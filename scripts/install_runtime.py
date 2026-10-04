"""Install the ONNX Runtime build that matches this machine (called by start.sh / start.bat after the venv is made).

onnxruntime ships as *mutually exclusive* packages - plain CPU, CUDA, DirectML, OpenVINO, QNN... - all providing the
same `onnxruntime` module, so exactly one must be installed. This picks it from the detected hardware:

    macOS (Apple Silicon / Intel)         onnxruntime            (Core ML / Neural Engine support is built in)
    NVIDIA GPU, Windows / Linux           onnxruntime-gpu        (CUDA; needs a CUDA 12 + cuDNN 9 runtime)
    Windows with any other DX12 GPU       onnxruntime-directml   (AMD, Intel Arc / Iris / UHD, ...)
    Windows on Snapdragon (ARM)           onnxruntime-qnn        (Qualcomm NPU)
    Linux with an Intel GPU               onnxruntime-openvino
    everything else                       onnxruntime            (CPU; AMD ROCm needs AMD's own wheel - see README)

Whatever is installed, the app benchmarks the providers it actually finds at start-up (config/runtime.py) and
uses the fastest, so installing a GPU build can never make things slower than the CPU - and if a GPU runtime cannot
start, sessions fall back to the CPU. If this script cannot improve on the CPU build it leaves it alone.

    python scripts/install_runtime.py             install the matching build
    python scripts/install_runtime.py --dry-run   only show what would be installed
    COVE_SKIP_RUNTIME_INSTALL=1                 skip entirely (you manage onnxruntime yourself)
    COVE_ORT_PACKAGE=onnxruntime-gpu            force a specific package
"""
import os
import subprocess
import sys
from importlib import metadata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cove"))

FLAVOURS = ("onnxruntime", "onnxruntime-gpu", "onnxruntime-directml", "onnxruntime-openvino", "onnxruntime-qnn",
            "onnxruntime-rocm", "onnxruntime-migraphx", "onnxruntime-training")


def choose_package(system: str, machine: str, vendors: set) -> str:
    """Pure decision function (unit-tested): which onnxruntime package suits this OS / CPU architecture / GPUs."""
    arm = machine.lower() in ("arm64", "aarch64")
    if system == "Darwin":
        return "onnxruntime"
    if "nvidia" in vendors and system in ("Windows", "Linux") and not arm:
        return "onnxruntime-gpu"
    if system == "Windows":
        if arm and "qualcomm" in vendors:
            return "onnxruntime-qnn"
        if vendors - {"other"}:
            return "onnxruntime-directml"
    if system == "Linux" and "intel" in vendors and not arm:
        return "onnxruntime-openvino"
    return "onnxruntime"


def installed_flavours() -> set:
    found = set()
    for name in FLAVOURS:
        try:
            metadata.version(name)
            found.add(name)
        except metadata.PackageNotFoundError:
            pass
    return found


def pip(*args) -> int:
    return subprocess.call([sys.executable, "-m", "pip", *args])


def main() -> int:
    from config.envcompat import apply_legacy_env_aliases
    apply_legacy_env_aliases()   # accept the pre-rename VISION_* names

    if os.getenv("COVE_SKIP_RUNTIME_INSTALL") == "1":
        print("[runtime] COVE_SKIP_RUNTIME_INSTALL=1 - leaving onnxruntime as it is")
        return 0

    from config.hardware import detect_gpus
    import platform
    gpus = detect_gpus()
    vendors = {g.vendor for g in gpus}
    wanted = os.getenv("COVE_ORT_PACKAGE") or choose_package(platform.system(), platform.machine(), vendors)
    have = installed_flavours()
    print(f"[runtime] {platform.system()} {platform.machine()} | GPUs: {', '.join(g.name for g in gpus) or 'none'}")
    print(f"[runtime] best onnxruntime build: {wanted}   (installed: {', '.join(sorted(have)) or 'none'})")

    if have == {wanted}:
        print("[runtime] already installed")
        return 0
    if "--dry-run" in sys.argv:
        return 0

    # exactly one flavour may be present, otherwise they overwrite each other's files
    if have:
        pip("uninstall", "-y", *sorted(have))
    if pip("install", wanted, "-q") != 0 or subprocess.call([sys.executable, "-c", "import onnxruntime"]) != 0:
        print(f"[runtime] {wanted} could not be installed/loaded - falling back to the CPU build")
        pip("uninstall", "-y", wanted)
        pip("install", "onnxruntime", "-q")
        return 0   # not an error: the CPU build always works
    print("[runtime] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
