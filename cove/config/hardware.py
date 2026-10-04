"""Hardware detection and ONNX Runtime configuration candidates.

Goal: run well on whatever the machine has - any CPU, and NVIDIA / AMD / Intel / Apple / Qualcomm accelerators -
without the user configuring anything.

* `detect_hardware()` describes the machine: usable CPU cores (aware of containers: cgroup quotas and CPU
  affinity), memory, GPUs (vendor, VRAM, integrated or not) and which ONNX Runtime execution providers this
  install of onnxruntime can actually use.
* `candidate_configs()` turns that into an ordered list of `RuntimeConfig`s worth trying (accelerators first,
  then CPU with sensible thread counts). `autotune.py` benchmarks them on the real model and keeps the fastest,
  so a weak integrated GPU that is slower than the CPU is never chosen just because it exists.

Nothing here imports onnxruntime at module import time and every probe is wrapped, so detection can never stop
the app from starting.
"""
import glob
import math
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

try:
    import psutil
except ImportError:  # psutil is a requirement, but never fail hard on a probe
    psutil = None


# --------------------------------------------------------------------------------------------------------------------
# Data classes
# --------------------------------------------------------------------------------------------------------------------
@dataclass
class GPUInfo:
    name: str
    vendor: str = "other"          # nvidia | amd | intel | apple | qualcomm | other
    vram_mb: Optional[int] = None
    integrated: bool = False


@dataclass
class HardwareInfo:
    system: str = ""               # Windows | Linux | Darwin
    machine: str = ""              # x86_64 | arm64 | aarch64 ...
    cpu_name: str = ""
    physical_cores: int = 1
    logical_cores: int = 1
    usable_cores: int = 1          # logical cores this process may really use (affinity / cgroup quota)
    ram_gb: float = 0.0
    available_ram_gb: float = 0.0
    in_container: bool = False
    apple_silicon: bool = False
    gpus: List[GPUInfo] = field(default_factory=list)
    ort_providers: List[str] = field(default_factory=list)

    @property
    def usable_physical_cores(self) -> int:
        """Physical cores we can use. Matrix maths barely benefits from SMT/hyper-threads, so this is the
        thread count that normally gives the best single-session throughput."""
        if self.usable_cores >= self.logical_cores:      # whole machine available
            return max(1, self.physical_cores)
        # restricted by a container quota / CPU affinity: use what we were given (a quota of N CPUs is N
        # units of CPU time, not N hyper-threads), but never more than the physical core count
        return max(1, min(self.usable_cores, self.physical_cores))

    def signature(self) -> str:
        """Stable identity of this machine+runtime; a cached tuning result is only reused when it matches."""
        gpus = ",".join(sorted(g.name for g in self.gpus))
        return "|".join([self.system, self.machine, self.cpu_name, f"{self.physical_cores}/{self.logical_cores}/{self.usable_cores}",
                         gpus, ",".join(sorted(self.ort_providers))])

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RuntimeConfig:
    """One way of running an ONNX model: which providers, how many threads, how big a batch."""
    name: str
    providers: List[str]
    provider_options: List[Dict]
    intra_threads: int
    batch_size: int
    accelerator: bool = False                       # runs on a GPU/NPU rather than the CPU
    session_overrides: Dict[str, object] = field(default_factory=dict)   # e.g. DirectML wants mem-pattern off

    def to_dict(self) -> Dict:
        return asdict(self)


# --------------------------------------------------------------------------------------------------------------------
# Detection helpers
# --------------------------------------------------------------------------------------------------------------------
def _run(cmd, timeout=3) -> str:
    try:
        return subprocess.check_output(cmd, timeout=timeout, stderr=subprocess.DEVNULL).decode(errors="ignore")
    except Exception:
        return ""


def _read(path: str) -> Optional[str]:
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None


def _cgroup_cpu_limit() -> Optional[float]:
    """CPUs granted by a container quota (e.g. `docker run --cpus=4`), or None when unlimited."""
    v2 = _read("/sys/fs/cgroup/cpu.max")
    if v2:
        quota, _, period = v2.partition(" ")
        if quota != "max" and period:
            try:
                return float(quota) / float(period)
            except ValueError:
                pass
    quota, period = _read("/sys/fs/cgroup/cpu/cpu.cfs_quota_us"), _read("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
    try:
        if quota and period and int(quota) > 0:
            return int(quota) / int(period)
    except ValueError:
        pass
    return None


def _cgroup_memory_limit_gb() -> Optional[float]:
    for p in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        v = _read(p)
        if v and v != "max":
            try:
                gb = int(v) / 1024 ** 3
                if gb < 4096:  # v1 reports a huge number when unlimited
                    return gb
            except ValueError:
                pass
    return None


def _cpu_name() -> str:
    system = platform.system()
    try:
        if system == "Linux":
            for line in (_read("/proc/cpuinfo") or "").splitlines():
                if line.lower().startswith(("model name", "hardware", "processor")) and ":" in line:
                    val = line.split(":", 1)[1].strip()
                    if val and not val.isdigit():
                        return val
        elif system == "Darwin":
            out = _run(["sysctl", "-n", "machdep.cpu.brand_string"]).strip()
            if out:
                return out
        elif system == "Windows":
            out = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name"]).strip()
            if out:
                return out
    except Exception:
        pass
    return platform.processor() or platform.machine()


def classify_gpu(name: str) -> GPUInfo:
    """Vendor / integrated-or-discrete from a device name."""
    n = name.lower()
    # Explicit vendor words first; only fall back to model-number patterns (NVIDIA datacenter "A100", "H100",
    # "L4"...) when no vendor is named - otherwise Intel "Arc A770" would look like an NVIDIA A-series card.
    if "intel" in n or re.search(r"\buhd\b|\biris\b|\bhd graphics\b|\barc\b|i915", n):
        vendor = "intel"
    elif re.search(r"amd|radeon|advanced micro|vega|\brx ?\d|amdgpu", n):
        vendor = "amd"
    elif re.search(r"apple|\bm\d( |$)|metal", n):
        vendor = "apple"
    elif re.search(r"qualcomm|adreno|snapdragon", n):
        vendor = "qualcomm"
    elif re.search(r"nvidia|geforce|rtx|gtx|quadro|tesla|titan|tegra|jetson|\b[ahlt]\d{1,3}[a-z]?\b", n):
        vendor = "nvidia"
    else:
        vendor = "other"

    integrated = False
    if vendor == "intel":
        integrated = not re.search(r"\barc\b", n)        # Intel Arc is discrete, UHD/Iris/HD are integrated
    elif vendor == "amd":
        # APU graphics: "Radeon Graphics", "Radeon Vega 8", "Radeon 680M/780M" - discrete cards have RX/Pro/numbers
        integrated = bool(re.search(r"vega \d|radeon\(tm\) graphics|radeon graphics|radeon \d{3}m|radeon r\d\b", n)) and "rx" not in n
    elif vendor == "apple":
        integrated = True                                  # unified memory, but fast: handled by Core ML
    return GPUInfo(name=name.strip(), vendor=vendor, integrated=integrated)


def detect_gpus() -> List[GPUInfo]:
    """All GPUs visible to this OS, with VRAM where it can be read cheaply."""
    gpus: List[GPUInfo] = []

    # NVIDIA: nvidia-smi gives exact names and memory (also works inside GPU containers)
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    for line in out.splitlines():
        name, _, mem = line.partition(",")
        if name.strip():
            g = classify_gpu(name)
            g.vendor = "nvidia"
            try:
                g.vram_mb = int(float(mem.strip()))
            except ValueError:
                pass
            gpus.append(g)

    system = platform.system()
    names: List[str] = []
    if system == "Linux":
        for line in _run(["lspci"]).splitlines():
            if any(k in line.lower() for k in ("vga compatible", "3d controller", "display controller")):
                names.append(line.split(":", 2)[-1].strip())
        if not names:
            for p in glob.glob("/sys/class/drm/card[0-9]*/device/uevent"):
                content = _read(p) or ""
                if "DRIVER=i915" in content or "PCI_ID=8086" in content:
                    names.append("Intel Integrated Graphics (i915)")
                elif "DRIVER=amdgpu" in content:
                    names.append("AMD Radeon Graphics (amdgpu)")
        if os.path.exists("/dev/dxg"):   # WSL2 GPU paravirtualisation is present
            names.append("WSL2 GPU (dxg)")
    elif system == "Windows":
        for line in _run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name + '|' + $_.AdapterRAM }"], timeout=5).splitlines():
            name, _, ram = line.partition("|")
            if name.strip():
                g = classify_gpu(name)
                try:
                    if int(ram) > 0:
                        g.vram_mb = int(ram) // (1024 * 1024)   # note: WMI caps at 4 GB for 32-bit fields
                except ValueError:
                    pass
                names.append(g)
    elif system == "Darwin":
        for line in _run(["system_profiler", "SPDisplaysDataType"], timeout=5).splitlines():
            if "Chipset Model:" in line:
                names.append(line.split("Chipset Model:")[-1].strip())

    known = {g.name.lower() for g in gpus}
    for item in names:
        g = item if isinstance(item, GPUInfo) else classify_gpu(item)
        if g.vendor == "nvidia" and any(x.vendor == "nvidia" for x in gpus):
            continue  # already reported (with VRAM) by nvidia-smi
        if g.name.lower() not in known:
            gpus.append(g)
            known.add(g.name.lower())

    if system == "Darwin" and platform.machine() == "arm64" and not any(g.vendor == "apple" for g in gpus):
        gpus.append(GPUInfo(name="Apple Silicon GPU", vendor="apple", integrated=True))
    return gpus


def detect_hardware(ort_providers: Optional[List[str]] = None) -> HardwareInfo:
    hw = HardwareInfo(system=platform.system(), machine=platform.machine(), cpu_name=_cpu_name())

    logical = os.cpu_count() or 1
    physical = None
    if psutil:
        try:
            physical = psutil.cpu_count(logical=False)
            logical = psutil.cpu_count(logical=True) or logical
        except Exception:
            pass
    if not physical:  # containers/VMs often hide the topology: assume SMT=2 on x86, none on ARM
        physical = logical if hw.machine.lower() in ("arm64", "aarch64") else max(1, logical // 2)
    hw.logical_cores, hw.physical_cores = logical, min(physical, logical)

    usable = logical
    try:
        usable = min(usable, len(os.sched_getaffinity(0)))
    except Exception:
        pass
    quota = _cgroup_cpu_limit()
    if quota:
        usable = min(usable, max(1, int(math.ceil(quota))))
        hw.in_container = True
    hw.usable_cores = max(1, usable)
    hw.in_container = hw.in_container or os.path.exists("/.dockerenv")

    if psutil:
        try:
            vm = psutil.virtual_memory()
            hw.ram_gb, hw.available_ram_gb = vm.total / 1024 ** 3, vm.available / 1024 ** 3
        except Exception:
            pass
    mem_limit = _cgroup_memory_limit_gb()
    if mem_limit:
        hw.ram_gb = min(hw.ram_gb or mem_limit, mem_limit)
        hw.available_ram_gb = min(hw.available_ram_gb or mem_limit, mem_limit)

    hw.apple_silicon = hw.system == "Darwin" and hw.machine == "arm64"
    try:
        hw.gpus = detect_gpus()
    except Exception:
        hw.gpus = []

    if ort_providers is None:
        try:
            import onnxruntime
            ort_providers = list(onnxruntime.get_available_providers())
        except Exception:
            ort_providers = ["CPUExecutionProvider"]
    hw.ort_providers = ort_providers
    return hw


# --------------------------------------------------------------------------------------------------------------------
# Candidate runtime configurations
# --------------------------------------------------------------------------------------------------------------------
CPU = "CPUExecutionProvider"


def cpu_config(name: str, threads: int, batch: int) -> RuntimeConfig:
    return RuntimeConfig(name=name, providers=[CPU], provider_options=[{}], intra_threads=max(1, threads),
                         batch_size=batch, accelerator=False)


_cpu_config = cpu_config


def candidate_configs(hw: HardwareInfo) -> List[RuntimeConfig]:
    """Ordered list of configurations worth benchmarking on this machine. Accelerators the installed
    onnxruntime cannot drive are simply not offered (the CPU config is always last and always works)."""
    avail = set(hw.ort_providers)
    vendors = {g.vendor for g in hw.gpus}
    discrete = [g for g in hw.gpus if not g.integrated]
    cands: List[RuntimeConfig] = []
    fallback = [CPU]
    fallback_opts = [{}]

    def accel(name, providers, options, batch=16, threads=2, overrides=None):
        cands.append(RuntimeConfig(name=name, providers=providers + fallback, provider_options=options + fallback_opts,
                                   intra_threads=threads, batch_size=batch, accelerator=True,
                                   session_overrides=overrides or {}))

    # --- NVIDIA: CUDA (TensorRT is opt-in: building its engines takes minutes) ---
    if "CUDAExecutionProvider" in avail and ("nvidia" in vendors or not hw.gpus):
        if os.getenv("COVE_ENABLE_TRT", "0") == "1" and "TensorrtExecutionProvider" in avail:
            accel("nvidia-tensorrt", ["TensorrtExecutionProvider", "CUDAExecutionProvider"],
                  [{"device_id": 0, "trt_engine_cache_enable": True, "trt_fp16_enable": True}, {"device_id": 0}], batch=32)
        accel("nvidia-cuda", ["CUDAExecutionProvider"], [{"device_id": 0}], batch=32)

    # --- AMD: ROCm / MIGraphX (Linux) ---
    if "amd" in vendors or not hw.gpus:
        if "MIGraphXExecutionProvider" in avail:
            accel("amd-migraphx", ["MIGraphXExecutionProvider"], [{"device_id": 0}], batch=16)
        if "ROCMExecutionProvider" in avail:
            accel("amd-rocm", ["ROCMExecutionProvider"], [{"device_id": 0}], batch=16)

    # --- Apple: Core ML schedules across the CPU, GPU and Neural Engine ---
    if "CoreMLExecutionProvider" in avail and (hw.apple_silicon or "apple" in vendors):
        accel("apple-coreml", ["CoreMLExecutionProvider"], [{"ModelFormat": "MLProgram", "MLComputeUnits": "ALL"}], batch=8)

    # --- Qualcomm Snapdragon NPU ---
    if "QNNExecutionProvider" in avail:
        backend = "QnnHtp.dll" if hw.system == "Windows" else "libQnnHtp.so"
        accel("qualcomm-npu", ["QNNExecutionProvider"], [{"backend_path": backend}], batch=1)

    # --- Intel: OpenVINO drives the iGPU, Arc and NPU - and is often faster than plain ORT on Intel CPUs ---
    if "OpenVINOExecutionProvider" in avail:
        if "intel" in vendors or not hw.gpus:
            accel("intel-openvino-gpu", ["OpenVINOExecutionProvider"], [{"device_type": "GPU"}], batch=8)
        accel("intel-openvino-auto", ["OpenVINOExecutionProvider"], [{"device_type": "AUTO"}], batch=8)
        cands.append(RuntimeConfig(name="intel-openvino-cpu", providers=["OpenVINOExecutionProvider"] + fallback,
                                   provider_options=[{"device_type": "CPU"}] + fallback_opts,
                                   intra_threads=hw.usable_physical_cores, batch_size=8))

    # --- DirectML: any DirectX 12 GPU on Windows (AMD, Intel, NVIDIA). Prefer a discrete adapter if there is one ---
    if "DmlExecutionProvider" in avail and hw.system == "Windows":
        # DirectML requires memory-pattern optimisation off and sequential execution
        accel("directml", ["DmlExecutionProvider"], [{"device_id": 0}], batch=8,
              overrides={"enable_mem_pattern": False, "execution_mode": "sequential"})

    # --- CPU: a couple of thread counts, so hyper-threading is only used if it actually helps ---
    phys = hw.usable_physical_cores
    cpu_threads = sorted({phys, hw.usable_cores}) if hw.usable_cores != phys else [phys]
    for t in cpu_threads:
        cands.append(_cpu_config(f"cpu-{t}t", t, 8))
    return cands


def heuristic_choice(hw: HardwareInfo, candidates: Optional[List[RuntimeConfig]] = None) -> RuntimeConfig:
    """What to use when benchmarking is disabled or fails: a strong GPU if there is one, otherwise the CPU."""
    candidates = candidates if candidates is not None else candidate_configs(hw)
    strong = [g for g in hw.gpus if not g.integrated] or [g for g in hw.gpus if g.vendor == "apple"]
    for c in candidates:
        if c.accelerator and (strong or not hw.gpus):
            return c
    return next(c for c in candidates if not c.accelerator and c.name.startswith("cpu-"))
