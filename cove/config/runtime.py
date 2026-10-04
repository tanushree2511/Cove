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

This file doubles as the benchmark worker: `python runtime.py --bench '<json>'`.
"""
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
            return 2 if 0 < vram < 4096 else 4
        return max(1, min(4, hw.usable_cores // 2))

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
        return (f"hardware: {hw.cpu_name or hw.machine} | {hw.physical_cores}C/{hw.logical_cores}T "
                f"(usable {hw.usable_cores}) | {hw.ram_gb:.1f} GB RAM | GPU: {gpus} || runtime: {self.config.name} "
                f"[{self.source}] threads={self.config.intra_threads} batch={self.clip_batch_size}")


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


def _autotune(hw: HardwareInfo, cands: List[RuntimeConfig], model_path: str) -> RuntimeProfile:
    results, measured = [], []
    for cfg in cands:
        res = _bench_candidate(cfg, model_path)
        results.append({"name": cfg.name, **res})
        if logger:
            logger.info("autotune %-22s %s", cfg.name, f"{res['ips']:.2f} img/s" if "ips" in res else f"skipped ({res.get('error')})")
        if "ips" in res:
            measured.append((cfg, res["ips"]))
    if not measured:
        return RuntimeProfile(heuristic_choice(hw, cands), hw, "heuristic", results)

    # Anything within 5% of the fastest counts as a tie (benchmark noise). Break ties in favour of an accelerator
    # (it leaves the CPU free for decoding / face detection), then the configuration using the fewest threads.
    top = max(ips for _, ips in measured)
    ties = [cfg for cfg, ips in measured if ips >= 0.95 * top]
    best = sorted(ties, key=lambda c: (not c.accelerator, c.intra_threads))[0]
    return RuntimeProfile(best, hw, "benchmark", results)


def _model_path() -> Optional[str]:
    try:
        from engines.search_engine import resolve_clip_model
        from .vision_config import CONFIG
        _, image_path, _ = resolve_clip_model(CONFIG.model_dir)
        return image_path if os.path.isfile(image_path) else None
    except Exception:
        return None


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
        model_path = model_path or _model_path()

        if len(cands) == 1 or model_path is None or not _truthy("COVE_AUTOTUNE", True):
            _profile = RuntimeProfile(heuristic_choice(hw, cands), hw, "forced" if len(cands) == 1 else "heuristic")
        else:
            cache_file = _cache_path()
            key = {"v": CACHE_VERSION, "sig": hw.signature(), "model": os.path.basename(model_path),
                   "model_size": os.path.getsize(model_path), "cands": [c.name for c in cands]}
            cached = None
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                if data.get("key") == key:
                    cached = next((c for c in cands if c.name == data.get("chosen")), None)
                    if cached:
                        _profile = RuntimeProfile(cached, hw, "cache", data.get("results", []))
            except Exception:
                pass
            if _profile is None:
                _profile = _autotune(hw, cands, model_path)
                try:
                    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                    with open(cache_file, "w") as f:
                        json.dump({"key": key, "chosen": _profile.config.name, "results": _profile.results,
                                   "hardware": hw.to_dict()}, f, indent=1)
                except Exception:
                    pass

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
        sess.run(None, feed)                                  # warm-up (kernel compile / graph optimisation)
        n, t0 = 0, time.perf_counter()
        while True:
            sess.run(None, feed)
            n += 1
            elapsed = time.perf_counter() - t0
            if elapsed >= spec["seconds"] and n >= 2:
                break
        print(json.dumps({"ips": round(n * b / elapsed, 3), "providers": used}))
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
