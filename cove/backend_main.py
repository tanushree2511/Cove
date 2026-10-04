"""Entry point of the packaged photo backend (the `cove-backend` sidecar the desktop app starts).

PyInstaller freezes this file; the desktop shell sets COVE_PORT, COVE_USER_DATA and COVE_MODEL_DIR. Running it
directly (`python backend_main.py`) works too. The video backend has the same shape in videoModules/video_main.py.
"""
import multiprocessing
import os
import sys


def main() -> None:
    multiprocessing.freeze_support()   # required for frozen Windows builds that spawn worker processes
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)

    # The hardware benchmark re-launches this exe as a short-lived worker; it must not start a second server.
    from config.runtime import run_benchmark_worker
    if run_benchmark_worker(sys.argv):
        return

    import uvicorn
    from api.server import app          # a static import so PyInstaller sees the whole application

    uvicorn.run(
        app,
        host=os.getenv("COVE_HOST", "127.0.0.1"),
        port=int(os.getenv("COVE_PORT", "8000")),
        workers=1,
        # a windowless frozen app has no stdout to colour-detect on, which would crash uvicorn's default log setup
        log_config=None if sys.stdout is None else uvicorn.config.LOGGING_CONFIG,
    )


if __name__ == "__main__":
    main()
