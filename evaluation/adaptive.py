"""Measure-before-you-run parallelism for this machine (any machine).

Instead of guessing a worker count, every heavy experiment stage goes through `run_adaptive`:

1. CALIBRATE on the real work. The first jobs of the stage are run with 1, 2, 4, ... workers. For each step it records
   how fast jobs finish (throughput) and the LOWEST free system RAM seen (sampled 4x per second, so short peaks count).
   Ramping stops as soon as
     * free RAM would fall below the safety floor (see below), or
     * more workers no longer make it meaningfully faster (< 10% gain: the CPU is saturated), or
     * the projected RAM of the next step would cross the floor.
   The calibration jobs are part of the stage, and their results are kept, so no work is wasted.
2. RUN the rest with the chosen worker count, with a LIVE GUARD: before each new job is handed out, free RAM is
   checked; if it is below the floor (another app grew, a heavy job is peaking) no new jobs are started until memory
   recovers, so the number of jobs in flight shrinks automatically instead of the machine running out of memory.

Safety floor = free RAM that must always remain for the user and the OS:
    max(1.5 GB, 15% of total RAM), override with COVE_RAM_FLOOR_GB.
COVE_MAX_WORKERS caps the count by hand if ever needed.

`python evaluation/adaptive.py` prints this machine's profile (cores, RAM, floor) and a CPU-scaling test that
shows how many parallel workers actually speed things up here; the result is saved to cache/hardware_profile.json.
"""
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait

import psutil

GB = 2 ** 30


def ram_floor_gb():
    env = os.environ.get("COVE_RAM_FLOOR_GB")
    if env:
        return float(env)
    return max(1.5, 0.15 * psutil.virtual_memory().total / GB)


def free_gb():
    return psutil.virtual_memory().available / GB


def cpu_budget():
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cove"))
        from config.hardware import detect_hardware
        n = detect_hardware(ort_providers=["CPUExecutionProvider"]).usable_cores
    except Exception:
        n = os.cpu_count() or 1
    n -= int(os.getenv("COVE_CPU_HEADROOM", "0") or 0)
    cap = os.environ.get("COVE_MAX_WORKERS")
    if cap:
        n = min(n, int(cap))
    return max(1, n)


def _log(msg, quiet):
    if not quiet:
        print(msg, flush=True)


def _run_batch(pool, fn, jobs, floor, in_flight, out, quiet=True, progress=None):
    """Run `jobs` on `pool` keeping at most `in_flight` running; never start a job while free RAM < floor.
    Appends results to `out`. Returns (seconds, lowest free GB seen)."""
    t0, low = time.perf_counter(), free_gb()
    it, running, paused = iter(jobs), set(), False
    exhausted = False
    while True:
        while not exhausted and len(running) < (in_flight[0] if isinstance(in_flight, list) else in_flight):
            f = free_gb()
            low = min(low, f)
            if f < floor and running:            # live guard: wait for memory instead of starting more work
                if not paused:
                    _log(f"   [guard] free RAM {f:.2f} GB < floor {floor:.2f} GB - holding new jobs", quiet)
                    paused = True
                break
            paused = False
            try:
                running.add(pool.submit(fn, next(it)))
            except StopIteration:
                exhausted = True
        if not running:
            break
        done, running = wait(running, timeout=0.25, return_when=FIRST_COMPLETED)
        low = min(low, free_gb())
        for d in done:
            out.append(d.result())
            if progress:
                progress(len(out))
    return time.perf_counter() - t0, low


def _timed_call(args):
    fn, job = args
    t = time.perf_counter()
    r = fn(job)
    return time.perf_counter() - t, r


def run_adaptive(fn, jobs, initializer=None, initargs=(), name="stage", per_step=None, min_gain=0.10, quiet=False,
                 shuffle=True, on_result=None, recheck_secs=180.0):
    """Run fn over jobs with a worker count MEASURED on this machine now (see module docstring).
    Returns the list of results (completion order; results should identify their own job).

    Calibration runs the SAME sample of jobs at every tested worker count n and times each job inside its worker.
    Jobs of a stage can differ a lot in cost, so comparing different jobs is noise; the same jobs are a fair test.
    If job time does not grow when more run at once, the CPU still has room: speedup(n) = n * t(1) / t(n).
    Only the first (1-worker) results of the sample are kept; the repeats cost a few seconds.
    per_step: sample size (default 2 x CPU budget); n is never tested above it.
    on_result: called with every result as soon as it arrives (e.g. to checkpoint).
    recheck_secs: during the run, every this many seconds the worker count is re-checked on the jobs that just
             finished: one worker is added (if RAM allows) and kept only if speedup rises by >= 5%, else removed.
    shuffle: mix the job order (fixed seed) so the sample is a fair mix of job kinds; keep False when the caller
             put the heaviest jobs first on purpose (so the memory peak is seen early)."""
    jobs = list(jobs)
    if not jobs:
        return []
    if shuffle:
        import random
        random.Random(0).shuffle(jobs)
    floor, budget = ram_floor_gb(), cpu_budget()
    base = free_gb()
    _log(f"[{name}] {len(jobs)} jobs | free RAM {base:.2f} GB, floor {floor:.2f} GB, CPU budget {budget} workers", quiet)
    if base < floor + 0.3:
        _log(f"[{name}] WARNING: almost no free RAM before starting; close other apps to go faster", quiet)
    sample = jobs[:min(len(jobs), per_step or 2 * budget)]
    steps = [n for n in (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64) if n <= min(budget, len(sample))] or [1]
    if min(budget, len(sample)) not in steps:
        steps.append(min(budget, len(sample)))
    out, pos, chosen, best_sp, per_worker, t1 = [], len(sample), 1, None, None, None
    with ProcessPoolExecutor(budget, initializer=initializer, initargs=initargs) as pool:
        for n in steps:
            # warm-up: make sure n worker processes exist (initializers done) so start-up cost is not counted;
            # the pool only starts processes on demand, so idle memory grows with n, never beyond what is tested
            for f in [pool.submit(time.sleep, 0.3) for _ in range(n)]:
                f.result()
            if n == steps[0]:
                base = free_gb()                  # free RAM with one idle worker
            if per_worker is not None and base - per_worker * n < floor:
                _log(f"[{name}] stop ramp: {n} workers would need ~{per_worker * n:.2f} GB, only {base - floor:.2f} GB above floor", quiet)
                break
            res = []
            wall, low = _run_batch(pool, _timed_call, [(fn, j) for j in sample], floor, n, res)
            tn = sum(d for d, _ in res) / len(res)
            if n == steps[0]:
                t1 = tn
                out.extend(r for _, r in res)     # keep the sample's results once
                if on_result:
                    for _, r in res:
                        on_result(r)
            sp = n * t1 / tn
            used = max(0.0, base - low)
            per_worker = max(per_worker or 0.0, used / n)
            _log(f"[{name}]   test {n:>2} workers: job time x{tn / t1:.2f} vs 1 worker -> speedup x{sp:.2f} "
                 f"(wall {wall:.1f}s), lowest free RAM {low:.2f} GB (~{used / n:.2f} GB/worker)", quiet)
            if low < floor:
                _log(f"[{name}] stop ramp: free RAM went below floor at {n} workers", quiet)
                break
            if best_sp is not None and sp < best_sp * (1 + min_gain):
                _log(f"[{name}] stop ramp: {n} workers not meaningfully faster than {chosen}", quiet)
                break
            chosen, best_sp = n, sp
        _log(f"[{name}] CHOSEN {chosen} workers (live RAM guard on); {len(jobs) - pos} jobs left", quiet)
        rest = jobs[pos:]
        if rest:
            t0, total, start = time.perf_counter(), len(rest), len(out)
            step = max(1, total // 20)
            k = [chosen]
            st = dict(win=[], since=time.perf_counter(), prev_sp=best_sp, trial=False, cooldown=0)
            res = []

            def progress(n_out):
                dur, r = res[-1]
                out.append(r)
                if on_result:
                    on_result(r)
                done = n_out
                st["win"].append(dur)
                if done % step == 0 or done == total:
                    el = time.perf_counter() - t0
                    _log(f"[{name}]   [{done}/{total}] {el:.0f}s, ~{el / done * (total - done):.0f}s left, "
                         f"{k[0]} workers, free RAM {free_gb():.2f} GB", quiet)
                # live re-check of the worker count on the jobs that just finished
                if (time.perf_counter() - st["since"] >= recheck_secs and len(st["win"]) >= 2 * k[0]
                        and t1 and done < total):
                    sp = k[0] * t1 / (sum(st["win"]) / len(st["win"]))
                    if st["trial"]:
                        if sp < st["prev_sp"] * 1.05:
                            k[0] -= 1
                            st["cooldown"] = 2
                            _log(f"[{name}] re-check: {k[0] + 1} workers x{sp:.2f} not faster than x{st['prev_sp']:.2f}"
                                 f" -> back to {k[0]}", quiet)
                        else:
                            _log(f"[{name}] re-check: {k[0]} workers x{sp:.2f} > x{st['prev_sp']:.2f} -> keeping {k[0]}", quiet)
                            st["prev_sp"] = sp
                        st["trial"] = False
                    else:
                        st["prev_sp"] = sp
                        if st["cooldown"] > 0:
                            st["cooldown"] -= 1
                        elif k[0] < budget and free_gb() - (per_worker or 0) > floor:
                            k[0] += 1
                            st["trial"] = True
                            _log(f"[{name}] re-check: x{sp:.2f} at {k[0] - 1} workers -> trying {k[0]}", quiet)
                    st["win"], st["since"] = [], time.perf_counter()
            _run_batch(pool, _timed_call, [(fn, j) for j in rest], floor, k, res, quiet=quiet, progress=progress)
    return out


# ---------------------------------------------------------------------------- standalone machine profile
def _burn(n):
    import numpy as np
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[v] = "1"
    try:
        from threadpoolctl import threadpool_limits
        threadpool_limits(1)
    except Exception:
        pass
    rng = np.random.default_rng(n)
    a = rng.standard_normal((400, 400), dtype=np.float32)
    for _ in range(40):
        a = np.tanh(a @ a.T / 400)
    return float(a.sum())


def main():
    import json
    vm = psutil.virtual_memory()
    prof = dict(logical_cores=psutil.cpu_count(), physical_cores=psutil.cpu_count(logical=False),
                cpu_budget=cpu_budget(), total_ram_gb=round(vm.total / GB, 2), free_ram_gb=round(vm.available / GB, 2),
                ram_floor_gb=round(ram_floor_gb(), 2))
    print("machine:", prof, flush=True)
    res = {}
    budget = cpu_budget()
    with ProcessPoolExecutor(budget) as pool:
        list(pool.map(_burn, range(budget)))           # warm-up
        for n in sorted({1, 2, 4, 6, 8, budget} & set(range(1, budget + 1))):
            out = []
            secs, low = _run_batch(pool, _burn, list(range(4 * n)), ram_floor_gb(), n, out)
            res[n] = round(4 * n / secs, 2)
            print(f"  {n:>2} workers: {res[n]:6.2f} jobs/s  (x{res[n] / res[1]:.2f} vs 1)  lowest free RAM {low:.2f} GB", flush=True)
    prof["cpu_scaling_jobs_per_s"] = res
    best = max(res, key=res.get)
    prof["fastest_worker_count"] = best
    print(f"fastest: {best} workers. Each experiment still measures its own memory per job before running.", flush=True)
    path = os.path.join(os.path.dirname(__file__), "cache", "hardware_profile.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({**prof, "measured_at": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=1)
    print("saved", path)


if __name__ == "__main__":
    main()
