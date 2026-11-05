"""Shared helpers for the evaluation suite (runs natively against the project's own engines)."""
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DS = os.path.join(ROOT, "datasets")
CACHE = os.path.join(ROOT, "evaluation", "cache")
RESULTS = os.path.join(ROOT, "evaluation", "results")
FIGS = os.path.join(ROOT, "evaluation", "figures")
for _d in (CACHE, RESULTS, FIGS):
    os.makedirs(_d, exist_ok=True)

os.environ.setdefault("COVE_MODEL_DIR", os.path.join(ROOT, "models"))
for p in (os.path.join(ROOT, "cove"), os.path.join(ROOT, "videoModules")):
    if p not in sys.path:
        sys.path.insert(0, p)


def nrm(x):
    x = np.asarray(x, dtype="float32")
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-9)


def save_json(name, obj):
    with open(os.path.join(RESULTS, name), "w", encoding="utf8") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


def load_json(name):
    with open(os.path.join(RESULTS, name), encoding="utf8") as f:
        return json.load(f)


def ranking_metrics(ranks, ks=(1, 5, 10)):
    """`ranks`: 1-based rank of the (single) relevant item for each query -> R@k, MRR, mAP (== MRR with one relevant item)."""
    r = np.asarray(ranks, dtype=float)
    out = {f"R@{k}": float((r <= k).mean()) for k in ks}
    out["MRR"] = float((1.0 / r).mean())
    out["mAP"] = out["MRR"]
    out["median_rank"] = float(np.median(r))
    out["n_queries"] = int(len(r))
    return out


class Timer:
    def __enter__(self):
        self.t = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.s = time.perf_counter() - self.t


def be_nice():
    """Run this process (and the workers it starts) at low OS priority so the computer stays responsive:
    the experiment still uses idle CPU, but anything the user is doing gets the CPU first."""
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)  # BELOW_NORMAL
        else:
            os.nice(10)
    except Exception:
        pass


def single_thread_worker():
    """Process-pool initializer: cap every maths library in this worker to ONE thread (NumPy/SciPy BLAS, OpenMP,
    FAISS). Without it each 'single-threaded' worker silently starts one thread per core and the planned headroom
    disappears."""
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[v] = "1"
    try:
        from threadpoolctl import threadpool_limits
        threadpool_limits(1)
    except Exception:
        pass
    try:
        import faiss
        faiss.omp_set_num_threads(1)
    except Exception:
        pass
    be_nice()


def _probe(fn, args):
    fn(args)
    import psutil
    # USS = memory used ONLY by this worker (excludes pages shared via memory-mapped files and libraries, and
    # address space that libraries reserve but never touch) - exactly what each extra worker adds.
    peak = psutil.Process().memory_full_info().uss
    if peak is None:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024   # Linux reports KB
    return peak


def measure_worker_gb(fn, args, initializer=None, initargs=()):
    """Run ONE representative job in a fresh worker process and return its measured peak memory in GB
    (+20% safety margin). Used instead of guessing how much RAM a worker of this workload needs."""
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(1, initializer=initializer, initargs=initargs) as p:
        return 1.2 * p.submit(_probe, fn, args).result() / 2 ** 30


def plan_parallelism(mem_per_worker_gb: float, threads_per_worker=None):
    """Decide how many worker processes (and threads each) to run, from the machine it is running on.

    Nothing is hard-coded per machine; everything is derived from what this process may use right now:
      * CPU  - usable logical cores (affinity / container quotas respected, via cove.config.hardware). All of them are
               used; the computer stays responsive because the work runs at below-normal OS priority.
      * RAM  - memory AVAILABLE now minus a reserve for the user (10% of total RAM, at least 1 GB), divided by what one
               worker of this job needs - ideally MEASURED with measure_worker_gb() rather than guessed.
      * threads_per_worker - None: split the CPU budget over the workers (multi-threaded ONNX inference);
               1: single-threaded workers, one per free logical core.
    Returns (workers, threads_per_worker)."""
    import psutil
    try:
        from config.hardware import detect_hardware
        hw = detect_hardware(ort_providers=["CPUExecutionProvider"])
        logical, physical = max(1, hw.usable_cores), max(1, hw.usable_physical_cores)
    except Exception:
        logical = max(1, os.cpu_count() or 1)
        physical = max(1, psutil.cpu_count(logical=False) or logical)
    # All usable cores by default: responsiveness comes from running BELOW-NORMAL priority (be_nice), so the OS hands
    # the CPU to the user's programs first and idle cycles to the experiment. Set COVE_CPU_HEADROOM=<n> to keep n
    # logical cores completely free instead (e.g. on a machine without priority scheduling).
    headroom = int(os.getenv("COVE_CPU_HEADROOM", "0") or 0)
    cpu_budget = max(1, logical - max(0, headroom))
    vm = psutil.virtual_memory()
    reserve = max(1.0 * 2 ** 30, 0.10 * vm.total)
    by_ram = int(max(0.0, vm.available - reserve) // (max(mem_per_worker_gb, 0.05) * 2 ** 30))
    if threads_per_worker == 1:
        by_cpu = cpu_budget
    else:
        by_cpu = max(1, min(physical, cpu_budget) // 2) if cpu_budget >= 4 else 1
    workers = max(1, min(by_cpu, by_ram))
    threads = threads_per_worker or max(1, cpu_budget // workers)
    return workers, threads
