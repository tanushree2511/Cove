"""Which onnxruntime build gets installed on each kind of machine."""
import importlib.util
import os

import pytest

_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "install_runtime.py")
if not os.path.exists(_SCRIPT):
    pytest.skip("scripts/ not present (e.g. inside the runtime container image)", allow_module_level=True)

_spec = importlib.util.spec_from_file_location("install_runtime", _SCRIPT)
install_runtime = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(install_runtime)
choose = install_runtime.choose_package


@pytest.mark.parametrize("system,machine,vendors,expected", [
    ("Darwin", "arm64", {"apple"}, "onnxruntime"),                         # Core ML is built into the macOS wheel
    ("Darwin", "x86_64", {"intel", "amd"}, "onnxruntime"),
    ("Windows", "AMD64", {"nvidia"}, "onnxruntime-gpu"),
    ("Linux", "x86_64", {"nvidia"}, "onnxruntime-gpu"),
    ("Linux", "x86_64", {"nvidia", "intel"}, "onnxruntime-gpu"),           # discrete NVIDIA beats the iGPU
    ("Windows", "AMD64", {"amd"}, "onnxruntime-directml"),
    ("Windows", "AMD64", {"intel"}, "onnxruntime-directml"),               # e.g. UHD 620 / Iris / Arc
    ("Windows", "ARM64", {"qualcomm"}, "onnxruntime-qnn"),
    ("Linux", "x86_64", {"intel"}, "onnxruntime-openvino"),
    ("Linux", "x86_64", {"amd"}, "onnxruntime"),                           # ROCm wheels are not on PyPI
    ("Linux", "aarch64", set(), "onnxruntime"),                            # Raspberry Pi, Graviton, ...
    ("Linux", "x86_64", set(), "onnxruntime"),
    ("Windows", "AMD64", set(), "onnxruntime"),
    ("Linux", "aarch64", {"nvidia"}, "onnxruntime"),                       # Jetson needs NVIDIA's own wheel
])
def test_choose_package(system, machine, vendors, expected):
    assert choose(system, machine, vendors) == expected
