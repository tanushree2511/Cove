"""Runtime profile: which ONNX Runtime configuration this machine should use, found by measuring.

`get_runtime_profile()` detects the hardware, lists the configurations worth trying (see hardware.py), benchmarks
each on the real CLIP vision model, and keeps the fastest. The result is cached per machine, so the ~10-40 s
benchmark runs once (and again only if the hardware, onnxruntime version or model changes).

Each benchmark runs in a *separate process*: GPU drivers/providers that are misconfigured can hard-crash (or hang
while compiling kernels), and that must never take the application down - a failed or timed-out candidate is simply
skipped.

Environment overrides:
    COVE_FORCE_CPU=1 / COVE_USE_GPU=0   never use an accelerator
    COVE_AUTOTUNE=0                       skip benchmarking, use the heuristic choice
    COVE_ORT_THREADS=N                    force the intra-op thread count
    COVE_BATCH_SIZE=N                     force the CLIP batch size
    COVE_ENABLE_TRT=1                     also consider TensorRT (slow first start)
    COVE_USE_IGPU=1                       also benchmark integrated GPUs (off by default: they share the CPU's power budget and rarely win)
    COVE_BENCH_BUDGET_S=N                 wall-clock limit for the start-up benchmark (default 300)
    COVE_CPU_MODE=max                     only CPU layouts that load every logical core (default 'auto' = fastest measured)
    COVE_BENCH_ROUNDS=N                   interleaved benchmark rounds per candidate (default 2)

This file doubles as the benchmark worker: `python runtime.py --bench '<json>'`.
"""
import contextlib
import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

if __name__ == "__main__":   # run as a script by the benchmark subprocess
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hardware import HardwareInfo, RuntimeConfig, candidate_configs, detect_hardware, heuristic_choice  # noqa: E402
else:
    from .hardware import HardwareInfo, RuntimeConfig, candidate_configs, detect_hardware, heuristic_choice

try:
    import logging
    logger = logging.getLogger(__name__)
except Exception:  # pragma: no cover
    logger = None

CACHE_VERSION = 2
BENCH_TIMEOUT_S = 120        # a candidate that takes longer than this (compiling kernels, hung driver) is skipped
BENCH_SECONDS = 2.5          # steady-state measuring time per candidate


# --------------------------------------------------------------------------------------------------------------------
# Sessions
# --------------------------------------------------------------------------------------------------------------------
def make_session_options(cfg: RuntimeConfig, threads: Optional[int] = None):
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads = int(threads if threads is not None else cfg.intra_threads)
    so.inter_op_num_threads = 1
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    for key, value in cfg.session_overrides.items():
        if key == "execution_mode":
            so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL if value == "sequential" else ort.ExecutionMode.ORT_PARALLEL
        else:
            setattr(so, key, value)
    return so


def create_session(model_path: str, cfg: Optional[RuntimeConfig] = None, threads: Optional[int] = None):
    """InferenceSession for `cfg`. If the accelerator cannot be initialised the CPU is used instead (never raises
    just because a GPU provider is broken)."""
    import onnxruntime as ort
    cfg = cfg or get_runtime_profile().config
    try:
        sess = ort.InferenceSession(model_path, sess_options=make_session_options(cfg, threads),
                                    providers=cfg.providers, provider_options=cfg.provider_options)
        return sess
    except Exception as exc:
        if logger:
            logger.warning("Could not start %s (%s); falling back to the CPU", cfg.name, exc)
        so = ort.SessionOptions()
        so.intra_op_num_threads = int(threads if threads is not None else max(1, os.cpu_count() or 1))
        return ort.InferenceSession(model_path, sess_options=so, providers=["CPUExecutionProvider"])


def create_sessions(model_path: str, cfg: Optional[RuntimeConfig] = None) -> list:
    """`cfg.sessions` independent InferenceSessions of the same model (data-parallel replicas; one for GPUs / single-session CPU)."""
    cfg = cfg or get_runtime_profile().config
    wanted = max(1, int(getattr(cfg, "sessions", 1) or 1))
    sessions = [create_session(model_path, cfg)]                  # the first one must exist (create_session already falls back to the CPU)
    for _ in range(wanted - 1):
        try:
            sessions.append(create_session(model_path, cfg))
        except Exception as exc:                                  # out of memory, a driver hiccup...: run with the replicas we have
            if logger:
                logger.warning("Could only create %d of %d model replicas (%s); continuing with fewer", len(sessions), wanted, exc)
            break
    return sessions


def limit_face_model_threads(face_app, profile: Optional["RuntimeProfile"] = None) -> None:
    """InsightFace creates its ONNX sessions with default threading, i.e. one thread per core *per model*. With
    several engines running at once that oversubscribes the CPU (threads fight over the same cores, which is
    slower than using fewer). Re-create each CPU session with the profile's per-engine thread budget."""
    try:
        profile = profile or get_runtime_profile()
        if profile is None or profile.accelerated:
            return
        from .hardware import cpu_config
        cfg = cpu_config("cpu-face", profile.face_threads, 1)
        for model in face_app.models.values():
            model_file = getattr(model, "model_file", None)
            if model_file and hasattr(model, "session"):
                model.session = create_session(model_file, cfg)
    except Exception as exc:
        if logger:
            logger.warning("Could not apply face-model thread limits: %s", exc)


# --------------------------------------------------------------------------------------------------------------------
# Profile
# --------------------------------------------------------------------------------------------------------------------
@dataclass
class RuntimeProfile:
    config: RuntimeConfig
    hardware: HardwareInfo
    source: str                                  # forced | benchmark | cache | heuristic
    results: List[Dict] = field(default_factory=list)   # benchmark table: name, img/s or error

    # ---- derived sizing used by the rest of the app ----
    @property
    def accelerated(self) -> bool:
        return self.config.accelerator

    @property
    def clip_batch_size(self) -> int:
        return max(1, int(os.getenv("COVE_BATCH_SIZE", self.config.batch_size)))

    @property
    def face_pool_size(self) -> int:
        """Number of face-model replicas. They are small and run in parallel threads; keep the total thread count
        near the core count instead of every replica spawning one thread per core."""
        hw = self.hardware
        if self.accelerated:
            vram = max([g.vram_mb or 0 for g in hw.gpus if not g.integrated] or [0])
            n = 2 if 0 < vram < 4096 else 4
        else:
            n = max(1, min(4, hw.usable_cores // 2))
        if hw.ram_gb:                                   # every replica holds its own copy of the face models: low-RAM machines get fewer
            n = 1 if hw.ram_gb < 4 else min(n, 2) if hw.ram_gb < 6 else n
        return max(1, n)

    @property
    def face_threads(self) -> int:
        """Intra-op threads per face-model replica."""
        if self.accelerated:
            return 1
        return max(1, min(2, self.hardware.usable_cores // self.face_pool_size))

    # Live throughput: an exponential moving average of how fast the model *actually* runs under real load.
    # The start-up benchmark can read low (both services benchmark at once and compete for the CPU) or go stale
    # (a laptop heats up and clocks down), so real measurements take over once there are a few of them.
    _observed_ips: Optional[float] = field(default=None, repr=False)
    _observed_n: int = field(default=0, repr=False)

    def observe_throughput(self, images: int, seconds: float) -> None:
        if images <= 0 or seconds <= 0:
            return
        ips = images / seconds
        with _lock_observe:
            self._observed_ips = ips if self._observed_ips is None else 0.7 * self._observed_ips + 0.3 * ips
            self._observed_n += 1

    @property
    def images_per_second(self) -> float:
        """CLIP throughput of the chosen configuration: observed under real load if we have it, else the start-up
        benchmark, else a conservative guess."""
        if self._observed_ips is not None and self._observed_n >= 3:
            return float(self._observed_ips)
        for r in self.results:
            if r.get("name") == self.config.name and "ips" in r:
                return float(r["ips"])
        return 20.0 if self.accelerated else 4.0

    def frames_for_video(self, duration_s: Optional[float] = None, max_frames: int = 14, min_frames: int = 4) -> int:
        """How many frames of a video to run through CLIP, scaled to the hardware.

        Measured on MSR-VTT/UCF101: search and tagging accuracy is flat from 16 frames down to ~4 (it only drops
        at 1-2), so we sample about one frame per 3 s and cap the CLIP work per video at a time budget
        (COVE_VIDEO_BUDGET_S, default 2 s): slow CPUs use fewer frames, fast GPUs use more."""
        budget_s = float(os.getenv("COVE_VIDEO_BUDGET_S", "2.0"))
        affordable = int(self.images_per_second * budget_s)
        wanted = max_frames if not duration_s else int(duration_s / 3.0) + 2
        return max(min_frames, min(max_frames, affordable, wanted))

    @property
    def workers(self) -> int:
        """I/O + pre-processing threads for batch jobs."""
        hw = self.hardware
        return min(32, hw.usable_cores * 2) if self.accelerated else max(2, hw.usable_cores)

    def describe(self) -> str:
        hw = self.hardware
        gpus = ", ".join(f"{g.name}{' (integrated)' if g.integrated else ''}" for g in hw.gpus) or "none"
        threads = (f"{self.config.sessions}x{self.config.intra_threads}" if self.config.sessions > 1
                   else str(self.config.intra_threads))
        return (f"hardware: {hw.cpu_name or hw.machine} | {hw.physical_cores}C/{hw.logical_cores}T "
                f"(usable {hw.usable_cores}) | {hw.ram_gb:.1f} GB RAM | GPU: {gpus} || runtime: {self.config.name} "
                f"[{self.source}] threads={threads} batch={self.clip_batch_size}")


_profile: Optional[RuntimeProfile] = None
_lock = threading.Lock()
_lock_observe = threading.Lock()


def _truthy(name: str, default: bool) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in ("1", "true", "yes", "on")


def _cache_path() -> str:
    try:
        from .vision_config import CONFIG
        base = CONFIG.user_data_dir
    except Exception:
        base = os.path.expanduser("~")
    return os.path.join(base, "hardware_profile.json")


def _apply_overrides(cands: List[RuntimeConfig]) -> List[RuntimeConfig]:
    forced_threads = os.getenv("COVE_ORT_THREADS")
    for c in cands:
        if forced_threads and forced_threads.isdigit() and int(forced_threads) > 0:
            c.intra_threads = int(forced_threads)
    return cands


def _bench_candidate(cfg: RuntimeConfig, model_path: str) -> Dict:
    """Benchmark one candidate in an isolated subprocess -> {"ips": float} or {"error": str}."""
    payload = json.dumps({"model": model_path, "cfg": cfg.to_dict(), "seconds": BENCH_SECONDS})
    # A frozen app has no interpreter: sys.executable *is* the app, so it must re-launch itself in worker mode
    # (the entry points call run_benchmark_worker first). Running it like a script would start a second full backend.
    cmd = ([sys.executable, "--bench", payload] if getattr(sys, "frozen", False)
           else [sys.executable, os.path.abspath(__file__), "--bench", payload])
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=BENCH_TIMEOUT_S, text=True)
        for line in reversed(proc.stdout.strip().splitlines()):
            if line.startswith("{"):
                return json.loads(line)
        return {"error": (proc.stderr or "no output").strip().splitlines()[-1][:200] if (proc.stderr or "").strip() else "no output"}
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {BENCH_TIMEOUT_S}s"}
    except Exception as exc:
        return {"error": str(exc)[:200]}


BENCH_ROUNDS = 2                  # candidates are measured in this many interleaved rounds (A B C, A B C ...)
BENCH_BUDGET_S = 300.0            # stop measuring after this long (only once at least one candidate has a result)
BASELINE_MARGIN = 1.10            # a non-default CPU layout must beat the default one by 10% to be worth switching to


def _autotune(hw: HardwareInfo, cands: List[RuntimeConfig], model_path: str) -> RuntimeProfile:
    """Measure every candidate and pick the fastest, robustly.

    A laptop CPU throttles within a minute of sustained load (measured here: -40% between a cool and a hot run), so timing
    candidates one after another favours whichever ran first. Interleaving the candidates over several rounds spreads that drift
    evenly across all of them, and the average is what gets compared."""
    rounds = max(1, int(os.getenv("COVE_BENCH_ROUNDS", BENCH_ROUNDS)))
    deadline = time.time() + float(os.getenv("COVE_BENCH_BUDGET_S", BENCH_BUDGET_S))
    samples: Dict[str, List[Dict]] = {c.name: [] for c in cands}
    errors: Dict[str, str] = {}
    ordered = sorted(cands, key=lambda c: c.accelerator)          # CPU layouts first: they always work, accelerators may hang
    over_budget = False
    for _ in range(rounds):
        for cfg in ordered:
            if cfg.name in errors:
                continue
            if time.time() >= deadline and any(samples.values()):
                over_budget = True
                break
            res = _bench_candidate(cfg, model_path)
            if "ips" in res:
                samples[cfg.name].append(res)
            else:
                errors[cfg.name] = res.get("error", "no result")
        if over_budget:
            if logger:
                logger.warning("Start-up benchmark hit its time budget; using the candidates measured so far")
            break
    results, measured = [], []
    for cfg in cands:
        runs = samples[cfg.name]
        if runs and cfg.name not in errors:
            ips = sum(r["ips"] for r in runs) / len(runs)
            util = [r["cpu_percent"] for r in runs if r.get("cpu_percent") is not None]
            entry = {"name": cfg.name, "ips": round(ips, 3), "runs": [r["ips"] for r in runs], "providers": runs[0].get("providers")}
            if util:
                entry["cpu_percent"] = round(sum(util) / len(util), 1)
            results.append(entry)
            measured.append((cfg, ips))
        else:
            results.append({"name": cfg.name, "error": errors.get(cfg.name, "no result")})
        if logger:
            logger.info("autotune %-22s %s", cfg.name, f"{results[-1]['ips']:.2f} img/s" if "ips" in results[-1] else f"skipped ({results[-1]['error']})")
    if not measured:
        return RuntimeProfile(heuristic_choice(hw, cands), hw, "heuristic", results)

    # Anything within 5% of the fastest counts as a tie (benchmark noise). Break ties in favour of an accelerator
    # (it leaves the CPU free for decoding / face detection), then the configuration using the fewest threads and
    # replicas in total (less memory, less heat) - so a multi-session split is only chosen when it is clearly faster.
    top = max(ips for _, ips in measured)
    ties = [cfg for cfg, ips in measured if ips >= 0.95 * top]
    best = sorted(ties, key=lambda c: (not c.accelerator, c.total_threads, c.sessions))[0]
    # Replicas cost memory and heat: leave the plain single-session default only for a clear (10%) win on the CPU.
    base = next((c for c, _ in measured if not c.accelerator and c.sessions == 1), None)
    if base is not None and not best.accelerator and best is not base:
        if dict((c.name, i) for c, i in measured)[best.name] < BASELINE_MARGIN * dict((c.name, i) for c, i in measured)[base.name]:
            best = base
    return RuntimeProfile(best, hw, "benchmark", results)


def _model_path() -> Optional[str]:
    try:
        from engines.search_engine import resolve_clip_model
        from .vision_config import CONFIG
        _, image_path, _ = resolve_clip_model(CONFIG.model_dir)
        return image_path if os.path.isfile(image_path) else None
    except Exception:
        return None


def _load_cached_profile(cache_file: str, key: Dict, cands: List[RuntimeConfig], hw: HardwareInfo) -> Optional[RuntimeProfile]:
    try:
        with open(cache_file) as f:
            data = json.load(f)
        if data.get("key") == key:
            chosen = next((c for c in cands if c.name == data.get("chosen")), None)
            if chosen:
                return RuntimeProfile(chosen, hw, "cache", data.get("results", []))
    except Exception:
        pass
    return None


def _store_profile(cache_file: str, key: Dict, profile: RuntimeProfile, hw: HardwareInfo) -> None:
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        tmp = cache_file + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"key": key, "chosen": profile.config.name, "results": profile.results, "hardware": hw.to_dict()}, f, indent=1)
        os.replace(tmp, cache_file)
    except Exception:
        pass


def _system_is_calm(limit_percent: float = 35.0, wait_s: float = 20.0) -> bool:
    """True once overall CPU use is low enough for a fair benchmark (waits up to `wait_s` for a short burst to pass)."""
    try:
        import psutil
    except Exception:
        return True
    deadline = time.time() + wait_s
    while True:
        try:
            if psutil.cpu_percent(interval=1.0) <= limit_percent:
                return True
        except Exception:
            return True                                              # cannot tell: do not block the benchmark
        if time.time() >= deadline:
            return False


@contextlib.contextmanager
def _benchmark_lock(cache_file: str, wait_s: float = 900.0, stale_s: float = 1200.0):
    """Cross-process mutex (an exclusively-created file). Yields True if we hold it; a stale or unobtainable lock never blocks forever."""
    lock = cache_file + ".lock"
    held = False
    t0 = time.time()
    try:
        os.makedirs(os.path.dirname(lock), exist_ok=True)
    except OSError:
        pass
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            held = True
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lock) > stale_s:
                    os.remove(lock)               # left behind by a crashed process
                    continue
            except OSError:
                pass
            if time.time() - t0 > wait_s:
                break
            time.sleep(1.0)
        except OSError:
            break
    try:
        yield held
    finally:
        if held:
            try:
                os.remove(lock)
            except OSError:
                pass


def get_runtime_profile(model_path: Optional[str] = None, refresh: bool = False) -> RuntimeProfile:
    """The (cached) best runtime configuration for this machine."""
    global _profile
    with _lock:
        if _profile is not None and not refresh:
            return _profile

        hw = detect_hardware()
        cands = _apply_overrides(candidate_configs(hw))
        if _truthy("COVE_FORCE_CPU", False) or not _truthy("COVE_USE_GPU", True):
            cands = [c for c in cands if not c.accelerator]
        if os.getenv("COVE_CPU_MODE", "auto").strip().lower() == "max":
            # "Use every logical core": only CPU layouts that load all of them. Not the default - on SMT CPUs the extra
            # hyper-threads usually add heat, not speed (see config/hardware.py) - but it is what some users want.
            full = [c for c in cands if not c.accelerator and c.total_threads >= hw.usable_cores]
            if full:
                cands = full
        model_path = model_path or _model_path()

        if len(cands) == 1 or model_path is None or not _truthy("COVE_AUTOTUNE", True):
            _profile = RuntimeProfile(heuristic_choice(hw, cands), hw, "forced" if len(cands) == 1 else "heuristic")
        else:
            cache_file = _cache_path()
            key = {"v": CACHE_VERSION, "sig": hw.signature(), "model": os.path.basename(model_path),
                   "model_size": os.path.getsize(model_path), "cands": [c.name for c in cands]}
            _profile = _load_cached_profile(cache_file, key, cands, hw)
            if _profile is None:
                # Only ONE process benchmarks at a time (the photo and video services start together and would otherwise
                # time each other's candidates); the others wait here and then simply read the winner's cache.
                with _benchmark_lock(cache_file) as _owner:
                    _profile = _load_cached_profile(cache_file, key, cands, hw)
                    if _profile is None:
                        if _system_is_calm():
                            _profile = _autotune(hw, cands, model_path)
                            _store_profile(cache_file, key, _profile, hw)
                        else:
                            # Timings taken while other work hogs the CPU favour the GPU/iGPU unfairly and, once cached, would
                            # keep the app on a slower configuration for good. Use the safe heuristic and benchmark next time.
                            if logger:
                                logger.warning("CPU is busy - skipping the start-up benchmark (nothing is cached; it will run on a quieter start)")
                            _profile = RuntimeProfile(heuristic_choice(hw, cands), hw, "heuristic-busy")

        if logger:
            logger.info("Runtime profile - %s", _profile.describe())
        return _profile


# --------------------------------------------------------------------------------------------------------------------
# Benchmark worker (runs in its own process)
# --------------------------------------------------------------------------------------------------------------------
def _bench_main(payload: str) -> None:
    import numpy as np
    spec = json.loads(payload)
    cfg = RuntimeConfig(**spec["cfg"])
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(spec["model"], sess_options=make_session_options(cfg),
                                    providers=cfg.providers, provider_options=cfg.provider_options)
        used = sess.get_providers()
        # ORT quietly drops a provider it cannot load: a "GPU" candidate that ended up on the CPU is not a GPU result
        if cfg.accelerator and used and used[0] == "CPUExecutionProvider":
            print(json.dumps({"error": f"{cfg.providers[0]} unavailable at runtime (fell back to CPU)"}))
            return
        inp = sess.get_inputs()[0]
        dims = [d if isinstance(d, int) else None for d in inp.shape]
        h = dims[2] if len(dims) > 2 and dims[2] else 224
        w = dims[3] if len(dims) > 3 and dims[3] else 224
        b = cfg.batch_size
        x = np.random.rand(b, 3, h, w).astype("float32")
        feed = {inp.name: x}
        # Data-parallel candidates run `cfg.sessions` replicas at the same time, exactly as the app does at run time.
        sessions = [sess] + [ort.InferenceSession(spec["model"], sess_options=make_session_options(cfg),
                                                  providers=cfg.providers, provider_options=cfg.provider_options)
                             for _ in range(max(1, int(getattr(cfg, "sessions", 1) or 1)) - 1)]
        for s_ in sessions:
            s_.run(None, feed)                                # warm-up (kernel compile / graph optimisation)
        counts = [0] * len(sessions)
        t0 = time.perf_counter()
        stop_at = t0 + spec["seconds"]

        def loop(i):
            while True:
                sessions[i].run(None, feed)
                counts[i] += 1
                if time.perf_counter() >= stop_at and counts[i] >= 2:
                    return

        try:                                                   # how busy the whole CPU really was while the candidate ran
            import psutil
            psutil.cpu_percent(interval=None)
        except Exception:
            psutil = None
        if len(sessions) == 1:
            loop(0)
        else:
            workers = [threading.Thread(target=loop, args=(i,)) for i in range(len(sessions))]
            for t_ in workers:
                t_.start()
            for t_ in workers:
                t_.join()
        elapsed = time.perf_counter() - t0
        util = psutil.cpu_percent(interval=None) if psutil else None
        print(json.dumps({"ips": round(sum(counts) * b / elapsed, 3), "providers": used,
                          "cpu_percent": round(util, 1) if util is not None else None}))
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"[:200]}))


def run_benchmark_worker(argv: List[str]) -> bool:
    """If `argv` is a benchmark-worker invocation (`<exe> --bench <payload>`), run it and return True."""
    if len(argv) >= 3 and argv[1] == "--bench":
        _bench_main(argv[2])
        return True
    return False


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--bench":
        _bench_main(sys.argv[2])
    else:
        import logging as _l
        _l.basicConfig(level=_l.INFO)
        logger = _l.getLogger("runtime")
        print(get_runtime_profile(refresh=True).describe())
