"""Entry point of the packaged video backend (the `video-backend` sidecar the desktop app starts).

Same shape as cove/backend_main.py: PyInstaller freezes this file and the desktop shell sets COVE_PORT,
COVE_USER_DATA and COVE_MODEL_DIR.
"""
import multiprocessing
import os
import sys


def main() -> None:
    multiprocessing.freeze_support()
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)         # `api` must resolve to videoModules/api.py, not the photo backend's package

    cove_dir = os.path.join(os.path.dirname(here), "cove")
    if os.path.isdir(cove_dir) and cove_dir not in sys.path:
        sys.path.append(cove_dir)        # when run from source; the frozen build already contains `config`
    from config.runtime import run_benchmark_worker
    if run_benchmark_worker(sys.argv):   # the hardware benchmark re-launches this exe as a worker, not a server
        return

    import uvicorn
    from api import app                  # a static import so PyInstaller sees the whole application

    uvicorn.run(
        app,
        host=os.getenv("COVE_HOST", "127.0.0.1"),
        port=int(os.getenv("COVE_PORT", "8001")),
        workers=1,
        log_config=None if sys.stdout is None else uvicorn.config.LOGGING_CONFIG,
    )


if __name__ == "__main__":
    main()
