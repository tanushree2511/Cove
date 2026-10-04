import logging
import os
import platform
import sys
import glob
import ctypes
from typing import Optional, Tuple, List
import psutil

from .envcompat import apply_legacy_env_aliases

apply_legacy_env_aliases()   # accept the pre-rename VISION_* variable names as aliases for COVE_*

# OpenMP threading for the libraries that use it (numpy/BLAS, faiss, opencv). Respect anything the user set.
# PASSIVE: waiting threads sleep instead of spinning - spinning shows as "high CPU use" but does no work, burns
# battery and heats laptop CPUs, which then clock down and run the real work slower.
try:
    import psutil as _psutil
    os.environ.setdefault("OMP_NUM_THREADS", str(_psutil.cpu_count(logical=False) or 4))
    os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
except Exception:
    pass

# Pre-load NVIDIA CUDA libraries if installed via pip (fixes ONNXRuntime CUDA 12 issues on Linux)
if platform.system() == "Linux":
    try:
        for path_dir in sys.path:
            if not os.path.isdir(path_dir):
                continue
            nvidia_lib_dirs = glob.glob(os.path.join(path_dir, "nvidia", "*", "lib"))
            for lib_dir in nvidia_lib_dirs:
                for so_file in glob.glob(os.path.join(lib_dir, "*.so.*")):
                    try:
                        ctypes.CDLL(so_file)
                    except Exception:
                        pass
    except Exception:
        pass

try:
    import onnxruntime
except ImportError:
    onnxruntime = None


def _parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_tuple(value: str, default: Tuple[int, int]) -> Tuple[int, int]:
    try:
        parts = [int(p.strip()) for p in value.split(",") if p.strip()]
        if len(parts) == 2:
            return parts[0], parts[1]
    except ValueError:
        pass
    return default


def get_user_data_dir(app_name: str = "Cove") -> str:
    system = platform.system()
    if system == "Windows":
        base = os.getenv("APPDATA")
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~/.config")

    path = os.path.join(base or os.getcwd(), app_name)
    os.makedirs(path, exist_ok=True)
    return path


# The data folder was called something else before the project was renamed. A library created back then must
# not disappear: the first time the new folder is used, the old one is moved into place.
_LEGACY_APP_DIR = "Vision" + "Archive"


def _resolve_user_data_dir(target: str) -> str:
    """`target` unless an old-name data folder sits next to it and the new one is still empty: then carry the old
    library over (rename = instant, nothing is copied). If the move is impossible (files in use, permissions) keep
    using the old folder instead of starting an empty library."""
    try:
        target = os.path.normpath(target)
        if os.path.basename(target) != "Cove":
            return target
        legacy = os.path.join(os.path.dirname(target), _LEGACY_APP_DIR)
        if not os.path.isdir(legacy):
            return target
        if os.path.isdir(target) and os.listdir(target):
            return target                      # the new folder already has data - never overwrite it
        try:
            if os.path.isdir(target):
                os.rmdir(target)
            os.rename(legacy, target)
        except OSError:
            return legacy
    except OSError:
        pass
    return target


def _has_required_assets(models_path: str) -> bool:
    if not os.path.isdir(models_path):
        return False
    clip_ok = any(os.path.isfile(os.path.join(models_path, f)) for f in ("clip_b16_image.onnx", "clip_image.onnx"))
    face_dir = os.path.join(models_path, "buffalo_s")
    return clip_ok and os.path.isdir(face_dir)


def _resolve_assets_dir(package_dir: str) -> str:
    targets = []
    override = os.getenv("COVE_MODEL_DIR")
    if override:
        targets.append(override)

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        targets.append(os.path.join(meipass, "models"))

    targets.extend([
        os.path.join(os.path.dirname(os.path.dirname(package_dir)), "models"),
        os.path.join(os.path.dirname(package_dir), "models"),
        os.path.join(package_dir, "models"),
        os.path.join(get_user_data_dir(), "models"),
        os.path.join(os.getcwd(), "models"),
    ])

    for candidate in targets:
        if candidate and os.path.isdir(candidate):
            has_clip = any(os.path.isfile(os.path.join(candidate, f)) for f in ("clip_b16_image.onnx", "clip_image.onnx"))
            face_dir = os.path.join(candidate, "buffalo_s")
            if has_clip or os.path.isdir(face_dir):
                return os.path.abspath(candidate)

    if meipass:
        return os.path.join(meipass, "models")
    return os.path.join(os.path.dirname(os.path.dirname(package_dir)), "models")


def _migrate_asset_file(source_dir: str, target: str, filename: str) -> None:
    src = os.path.join(source_dir, filename)
    if os.path.exists(src) and not os.path.exists(target):
        os.makedirs(os.path.dirname(target), exist_ok=True)
        try:
            from shutil import copy2

            copy2(src, target)
        except Exception:
            pass


class VisionConfig:
    def __init__(self):
        package_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = _resolve_assets_dir(package_dir)
        self.assets_base = os.path.dirname(self.assets_dir)
        self.model_dir = self.assets_dir
        self.user_data_dir = _resolve_user_data_dir(os.getenv("COVE_USER_DATA", get_user_data_dir()))
        os.makedirs(self.user_data_dir, exist_ok=True)

        self.log_level = os.getenv("COVE_LOG_LEVEL", "INFO").upper()
        self.log_dir = os.path.join(self.user_data_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, os.getenv("COVE_LOG_FILE", "cove.log"))
        self.api_key = os.getenv("COVE_API_KEY")
        self.det_size = _parse_tuple(os.getenv("COVE_DET_SIZE", "320,320"), (320, 320))
        self.skip_model_load = _parse_bool(os.getenv("COVE_SKIP_MODEL_LOAD", None), False)
        self.ai_workers = int(os.getenv("COVE_AI_WORKERS", "")) if os.getenv("COVE_AI_WORKERS") else None
        self.vector_path = os.path.join(self.user_data_dir, os.getenv("COVE_IMAGE_VECTOR_PATH", "image_vectors.npy"))
        self.faiss_index_path = os.path.join(self.user_data_dir, os.getenv("COVE_FAISS_INDEX", "faiss_index.bin"))
        self.search_index_path = os.path.join(self.user_data_dir, os.getenv("COVE_FAISS_SEARCH_INDEX", "faiss_search_index.bin"))
        self.people_db_path = os.path.join(self.user_data_dir, os.getenv("COVE_PEOPLE_DB_PATH", "people_db.json"))
        self.paths_file = os.path.join(self.user_data_dir, os.getenv("COVE_PATHS_FILE", "paths.json"))
        self.embeddings_file = os.path.join(self.user_data_dir, os.getenv("COVE_EMBEDDINGS_FILE", "embeddings.npy"))
        self.image_cache = os.path.join(self.user_data_dir, os.getenv("COVE_IMAGE_CACHE", "image_cache.json"))

        self._migrate_cache()

    def _migrate_cache(self) -> None:
        migrate_candidates = [
            ("image_vectors.npy", self.vector_path),
            ("embeddings.npy", self.embeddings_file),
            ("paths.json", self.paths_file),
            ("people_db.json", self.people_db_path),
        ]
        for filename, target in migrate_candidates:
            _migrate_asset_file(self.assets_dir, target, filename)

    # ---- hardware-dependent settings: all derived from the measured runtime profile (config/runtime.py) ----
    @property
    def runtime_profile(self):
        """Best ONNX Runtime configuration for this machine (detected + benchmarked once, then cached).
        None only if detection itself fails, in which case everything below degrades to plain CPU defaults."""
        if getattr(self, "_runtime_profile", None) is None:
            try:
                from .runtime import get_runtime_profile
                self._runtime_profile = get_runtime_profile()
            except Exception as exc:  # never let hardware probing stop the app
                logging.getLogger(__name__).warning("Hardware profiling failed (%s); using CPU defaults", exc)
                self._runtime_profile = False
        return self._runtime_profile or None

    @property
    def use_gpu(self) -> bool:
        profile = self.runtime_profile
        return bool(profile and profile.accelerated)

    @property
    def providers(self):
        profile = self.runtime_profile
        return list(profile.config.providers) if profile else ["CPUExecutionProvider"]

    @property
    def provider_options(self):
        profile = self.runtime_profile
        return [dict(o) for o in profile.config.provider_options] if profile else [{}]

    @property
    def ctx_id(self):
        return 0 if self.use_gpu else -1

    @property
    def effective_workers(self) -> int:
        """Threads for I/O + pre-processing in batch jobs."""
        if self.ai_workers is not None:
            return max(1, self.ai_workers)
        profile = self.runtime_profile
        return profile.workers if profile else max(2, os.cpu_count() or 2)

    @property
    def ai_engine_pool_size(self) -> int:
        """Number of face-model replicas to hold in memory."""
        profile = self.runtime_profile
        return profile.face_pool_size if profile else min(4, os.cpu_count() or 1)


CONFIG = VisionConfig()


def setup_logging():
    if logging.getLogger().handlers:
        return

    level = CONFIG.log_level
    os.makedirs(CONFIG.log_dir, exist_ok=True)
    handlers = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(CONFIG.log_file, encoding="utf-8"))
    except OSError:
        pass

    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, CONFIG.log_level, logging.INFO))
    return logger


