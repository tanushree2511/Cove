"""Build the two backends the desktop app ships as sidecars, and stage everything Tauri bundles.

    python scripts/build_backends.py              fetch models (if missing), freeze both backends, stage them
    python scripts/build_backends.py --only cove  just the photo backend
    python scripts/build_backends.py --skip-models

Output (all git-ignored):
    frontend/src-tauri/bin/cove-backend-<target-triple>[.exe]     photo API   (port 8000, started by the app)
    frontend/src-tauri/bin/video-backend-<target-triple>[.exe]    video API   (port 8001, started by the app)
    models/                                                       CLIP + InsightFace models, bundled as a resource

Run it from an environment that has requirements.txt + pyinstaller installed. On Windows the CI job first installs the
DirectML onnxruntime (COVE_ORT_PACKAGE=onnxruntime-directml python scripts/install_runtime.py) so the packaged app
can use any DX12 GPU; the app still benchmarks and falls back to the CPU on its own.
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COVE = os.path.join(ROOT, "cove")
VIDEO = os.path.join(ROOT, "videoModules")
BIN_DIR = os.path.join(ROOT, "frontend", "src-tauri", "bin")
BUILD_DIR = os.path.join(ROOT, "build", "backends")
MODELS_DIR = os.path.join(ROOT, "models")

# Packages that carry native libraries / data files PyInstaller's static analysis does not see.
COLLECT_ALL = ["onnxruntime", "insightface", "faiss", "imageio_ffmpeg", "scenedetect", "tokenizers"]
HIDDEN_IMPORTS = [
    "uvicorn.logging", "uvicorn.loops.auto", "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on", "multipart", "multipart.multipart",
    # imported lazily inside functions, so analysis would miss them
    "config.runtime", "config.hardware", "config.envcompat", "sklearn.utils._typedefs", "sklearn.neighbors._partition_nodes",
]
EXCLUDES = ["matplotlib", "tkinter", "IPython", "pytest", "PyQt5", "PyQt6", "PySide2", "PySide6", "torch", "tensorflow"]

SERVICES = {
    "cove": {"name": "cove-backend", "entry": os.path.join(COVE, "backend_main.py"), "paths": [COVE]},
    # videoModules first: `api` must resolve to videoModules/api.py, not the photo backend's cove/api package
    "video": {"name": "video-backend", "entry": os.path.join(VIDEO, "video_main.py"), "paths": [VIDEO, COVE]},
}


def host_triple() -> str:
    try:
        out = subprocess.run(["rustc", "-vV"], capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            if line.startswith("host:"):
                return line.split(":", 1)[1].strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    arch = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}.get(platform.machine().lower(), platform.machine().lower())
    return {
        "Windows": f"{arch}-pc-windows-msvc",
        "Darwin": f"{arch}-apple-darwin",
    }.get(platform.system(), f"{arch}-unknown-linux-gnu")


def fetch_models() -> None:
    """CLIP (ONNX, from Hugging Face) + the InsightFace buffalo_s bundle, into <repo>/models (resumable, idempotent)."""
    env = dict(os.environ, COVE_MODEL_DIR=MODELS_DIR)
    os.makedirs(MODELS_DIR, exist_ok=True)
    subprocess.run([sys.executable, os.path.join(COVE, "pipeline", "download_models.py")], check=True, env=env)
    if not os.path.isdir(os.path.join(MODELS_DIR, "models", "buffalo_s")) and not os.path.isdir(os.path.join(MODELS_DIR, "buffalo_s")):
        code = (
            "from insightface.app import FaceAnalysis\n"
            f"app = FaceAnalysis(name='buffalo_s', root=r'{ROOT}', allowed_modules=['detection', 'recognition'], "
            "providers=['CPUExecutionProvider'])\n"
            "app.prepare(ctx_id=-1, det_size=(320, 320))\n"
        )
        subprocess.run([sys.executable, "-c", code], check=True)
    if not os.path.isdir(os.path.join(MODELS_DIR, "buffalo_s")):
        raise SystemExit(f"buffalo_s face model missing from {MODELS_DIR} after download")


def freeze(key: str, triple: str) -> str:
    spec = SERVICES[key]
    exe_suffix = ".exe" if platform.system() == "Windows" else ""
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--console",
           "--name", spec["name"],
           "--distpath", os.path.join(BUILD_DIR, "dist"),
           "--workpath", os.path.join(BUILD_DIR, "work", key),
           "--specpath", os.path.join(BUILD_DIR, "spec")]
    for p in spec["paths"]:
        cmd += ["--paths", p]
    for pkg in COLLECT_ALL:
        cmd += ["--collect-all", pkg]
    for mod in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", mod]
    for mod in EXCLUDES:
        cmd += ["--exclude-module", mod]
    cmd.append(spec["entry"])
    print(f"\n=== Freezing {spec['name']} ===", flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)

    built = os.path.join(BUILD_DIR, "dist", spec["name"] + exe_suffix)
    os.makedirs(BIN_DIR, exist_ok=True)
    staged = os.path.join(BIN_DIR, f"{spec['name']}-{triple}{exe_suffix}")
    shutil.copy2(built, staged)
    print(f"staged {staged} ({os.path.getsize(staged) / 1e6:.0f} MB)")
    return staged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", choices=sorted(SERVICES), help="build just one backend")
    parser.add_argument("--skip-models", action="store_true", help="do not fetch the models")
    args = parser.parse_args()

    triple = host_triple()
    print(f"target triple: {triple}")
    if not args.skip_models:
        fetch_models()
    for key in ([args.only] if args.only else list(SERVICES)):
        freeze(key, triple)
    print("\nDone. Next: cd frontend && npx tauri build")


if __name__ == "__main__":
    main()
