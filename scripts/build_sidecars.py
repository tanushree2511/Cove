#!/usr/bin/env python3
"""
build_sidecars.py — Packages the Python backends into standalone executables
for Tauri bundling.

Run this before `tauri build`:
  python3 scripts/build_sidecars.py

Produces:
  frontend/src-tauri/bin/cove-backend-x86_64-unknown-linux-gnu
  frontend/src-tauri/bin/video-backend-x86_64-unknown-linux-gnu
  (Windows: *-x86_64-pc-windows-msvc.exe)
  (macOS:   *-x86_64-apple-darwin  or  *-aarch64-apple-darwin)
"""

import os
import platform
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = ROOT / "frontend" / "src-tauri" / "bin"
VENV = ROOT / ".venv"
PIP = VENV / ("Scripts" if platform.system() == "Windows" else "bin") / "pip"

# Tauri expects platform-specific suffixes on sidecar binaries
SYSTEM = platform.system()
MACHINE = platform.machine().lower()

def _tauri_target() -> str:
    if SYSTEM == "Linux":
        arch = "x86_64" if "x86_64" in MACHINE or "amd64" in MACHINE else "aarch64"
        return f"{arch}-unknown-linux-gnu"
    elif SYSTEM == "Darwin":
        arch = "aarch64" if "arm" in MACHINE or "aarch64" in MACHINE else "x86_64"
        return f"{arch}-apple-darwin"
    elif SYSTEM == "Windows":
        return "x86_64-pc-windows-msvc"
    else:
        raise RuntimeError(f"Unsupported platform: {SYSTEM}")

EXT = ".exe" if SYSTEM == "Windows" else ""
TARGET = _tauri_target()

SIDECARS = [
    {
        "name": "cove-backend",
        "entry": str(ROOT / "cove" / "api" / "server.py"),
        "extra_data": [
            (str(ROOT / "models"), "models"),
        ],
        "hidden_imports": [
            "uvicorn", "fastapi", "insightface", "onnxruntime", "cv2",
            "faiss", "numpy", "PIL", "tokenizers", "scipy", "sklearn",
        ],
        "paths": [str(ROOT / "cove")],
    },
    {
        "name": "video-backend",
        "entry": str(ROOT / "videoModules" / "api.py"),
        "extra_data": [
            (str(ROOT / "models"), "models"),
        ],
        "hidden_imports": [
            "uvicorn", "fastapi", "onnxruntime", "cv2",
            "numpy", "PIL", "tokenizers", "scipy", "sklearn",
            "scenedetect", "imageio_ffmpeg",
        ],
        "paths": [str(ROOT / "videoModules"), str(ROOT / "cove")],
    },
]


def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])


def build_sidecar(sidecar: dict):
    name = sidecar["name"]
    output_name = f"{name}-{TARGET}"
    print(f"\n{'='*60}")
    print(f"Building sidecar: {name} -> {output_name}{EXT}")
    print(f"{'='*60}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        f"--name={name}",
        f"--distpath={BIN_DIR}",
        f"--workpath={ROOT / 'build' / name}",
        f"--specpath={ROOT / 'build'}",
    ]

    for src, dst in sidecar.get("extra_data", []):
        if os.path.exists(src):
            sep = ";" if SYSTEM == "Windows" else ":"
            cmd.append(f"--add-data={src}{sep}{dst}")

    for imp in sidecar.get("hidden_imports", []):
        cmd.append(f"--hidden-import={imp}")

    for path in sidecar.get("paths", []):
        cmd.append(f"--paths={path}")

    cmd.append(sidecar["entry"])

    subprocess.check_call(cmd, cwd=str(ROOT))

    # Rename to include Tauri target suffix
    built = BIN_DIR / (name + EXT)
    renamed = BIN_DIR / (output_name + EXT)
    if built.exists():
        if renamed.exists():
            renamed.unlink()
        built.rename(renamed)
        print(f"✓ {renamed}")
    else:
        raise FileNotFoundError(f"Build produced no output at {built}")


def main():
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    ensure_pyinstaller()
    for sidecar in SIDECARS:
        build_sidecar(sidecar)
    print("\n✅ All sidecars built successfully!")
    print(f"   Output: {BIN_DIR}/")
    print(f"\nNext step: cd frontend && npx tauri build")


if __name__ == "__main__":
    main()
