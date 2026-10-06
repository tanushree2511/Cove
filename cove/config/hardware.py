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
    """One way of running an ONNX model: which providers, how many threads, how big a batch, how many parallel sessions."""
    name: str
    providers: List[str]
    provider_options: List[Dict]
    intra_threads: int                              # threads PER session
    batch_size: int
    accelerator: bool = False                       # runs on a GPU/NPU rather than the CPU
    session_overrides: Dict[str, object] = field(default_factory=dict)   # e.g. DirectML wants mem-pattern off
    sessions: int = 1                               # model replicas run side by side (data parallelism): keeps every core fed

    @property
    def total_threads(self) -> int:
        return max(1, self.sessions) * max(1, self.intra_threads)

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
            # The registry answers instantly and always the same way. (A PowerShell/WMI query can time out on a busy PC, and the
            # fallback name differs - which changed the tuning-cache key and triggered a surprise re-benchmark under load.)
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                    name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                    if name and name.strip():
                        return " ".join(name.split())
            except Exception:
                pass
            out = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name"], timeout=10).strip()
            if out:
                return " ".join(out.split())
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


_VIRTUAL_ADAPTERS = ("microsoft basic", "remote display", "hyper-v", "virtual", "parsec", "citrix", "vmware svga")


def _windows_gpus_from_registry() -> List[GPUInfo]:
    """Display adapters from the registry display-class key: no process spawn, so no timeout under load and the same answer
    every time (the PowerShell/WMI query this replaces could come back empty on a busy PC and change the tuning-cache key)."""
    gpus: List[GPUInfo] = []
    try:
        import winreg
        base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as key:
            index = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(key, index)
                except OSError:
                    break
                index += 1
                if not sub_name.isdigit():
                    continue
                try:
                    with winreg.OpenKey(key, sub_name) as sk:
                        name = str(winreg.QueryValueEx(sk, "DriverDesc")[0]).strip()
                        mem = None
                        try:
                            raw = winreg.QueryValueEx(sk, "HardwareInformation.qwMemorySize")[0]
                            mem = int.from_bytes(raw, "little") if isinstance(raw, (bytes, bytearray)) else int(raw)
                        except Exception:
                            pass
                except OSError:
                    continue
                if not name or any(v in name.lower() for v in _VIRTUAL_ADAPTERS):
                    continue
                g = classify_gpu(name)
                if mem and mem > 0:
                    g.vram_mb = int(mem // (1024 * 1024))
                gpus.append(g)
    except Exception:
        return []
    return gpus


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
        names.extend(_windows_gpus_from_registry())
        for line in ([] if names else _run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name + '|' + $_.AdapterRAM }"], timeout=15).splitlines()):
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


def cpu_config(name: str, threads: int, batch: int, sessions: int = 1) -> RuntimeConfig:
    return RuntimeConfig(name=name, providers=[CPU], provider_options=[{}], intra_threads=max(1, threads),
                         batch_size=batch, accelerator=False, sessions=max(1, sessions))


_cpu_config = cpu_config

SESSION_RAM_GB = 0.6          # approx. extra memory per additional CLIP image-encoder replica (weights + activations)
MAX_PARALLEL_SESSIONS = 8
MIN_PHYSICAL_CORES_FOR_REPLICAS = 6     # below this a single session already saturates the physical cores
MAX_MULTI_SESSION_CANDIDATES = 4   # keeps the one-time start-up benchmark short on machines with many cores


def parallel_session_candidates(hw: HardwareInfo) -> List[RuntimeConfig]:
    """CPU configurations that run several model replicas side by side.

    One session with N threads leaves cores idle: small matrix products stop scaling long before 8-16 threads, the
    sessions' pre/post-processing is serial, and hyper-threads share their core's units. Several smaller sessions
    working on different batches keep every core busy, at the price of one model copy of memory each. Which split is
    fastest depends on the CPU (cache sizes, memory bandwidth, SMT), so these are only *candidates* - the start-up
    benchmark measures them next to the single-session ones and keeps the fastest.

    Generated from the topology, never hard-coded for one chip: for the physical and the logical core count it tries
    2, 4 (and 8 on big machines) sessions of `cores // sessions` threads, within the machine's free memory."""
    phys, logical = hw.usable_physical_cores, max(hw.usable_cores, 1)
    if phys < MIN_PHYSICAL_CORES_FOR_REPLICAS or logical < 4:
        # Measured on a 4-core / 8-thread laptop CPU: one 4-thread session already keeps every PHYSICAL core busy (Task Manager
        # shows ~60% because the 4 hyper-thread siblings sit idle - they add nothing to AVX matrix maths), and 8 threads or
        # 2-4 replicas were slower (-7%) or no faster. Replicas only pay off where one session's thread pool stops scaling.
        return []
    counts = [s for s in (2, 4, 8) if s <= min(phys, MAX_PARALLEL_SESSIONS)]
    if phys >= 32:
        counts.append(16)
    avail = hw.ram_gb          # TOTAL (container-limited) RAM, not what happens to be free right now: the candidate list
    cands, seen = [], set()    # is part of the tuning-cache key and must not change from one start-up to the next
    for total in sorted({logical, phys}, reverse=True):                     # use-every-core splits first
        for s in counts:
            threads = max(1, total // s)
            if s * threads < 2 or (s, threads) in seen:
                continue
            if avail and (s - 1) * SESSION_RAM_GB > 0.25 * avail:         # the extra replicas must not starve the rest of the app
                continue
            seen.add((s, threads))
            cands.append(cpu_config(f"cpu-{s}x{threads}t", threads, 8, sessions=s))
    return cands[:MAX_MULTI_SESSION_CANDIDATES]


def candidate_configs(hw: HardwareInfo) -> List[RuntimeConfig]:
    """Ordered list of configurations worth benchmarking on this machine. Accelerators the installed
    onnxruntime cannot drive are simply not offered (the CPU config is always last and always works)."""
    avail = set(hw.ort_providers)
    vendors = {g.vendor for g in hw.gpus}
    discrete = [g for g in hw.gpus if not g.integrated]
    # An INTEGRATED GPU (Intel UHD/Iris, AMD APU graphics) shares the CPU's power and thermal budget and its memory bandwidth, so
    # it rarely beats the CPU it sits next to. Measured on a 15 W laptop (i5-8250U + UHD 620), same CLIP model, cool run:
    #   CPU 4 threads 4.76 img/s | iGPU (DirectML) 2.35 | CPU + iGPU together 3.68 - and after a minute of heat 2.78 | 1.12 | 0.29.
    # So integrated GPUs are not benchmarked by default (saves start-up time and keeps a flaky iGPU driver out of the picture);
    # COVE_USE_IGPU=1 puts them back. Discrete GPUs, Apple Silicon and NPUs are unaffected.
    use_igpu = os.getenv("COVE_USE_IGPU", "0").strip().lower() in ("1", "true", "yes", "on")

    def gpu_ok(vendor: str) -> bool:
        """A GPU of this vendor worth benchmarking: a discrete one, or an integrated one when asked for."""
        return any(g.vendor == vendor and (not g.integrated or use_igpu) for g in hw.gpus)
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
    if gpu_ok("amd") or not hw.gpus:
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
        if gpu_ok("intel") or not hw.gpus:
            accel("intel-openvino-gpu", ["OpenVINOExecutionProvider"], [{"device_type": "GPU"}], batch=8)
        if gpu_ok("intel") or not hw.gpus:
            accel("intel-openvino-auto", ["OpenVINOExecutionProvider"], [{"device_type": "AUTO"}], batch=8)
        cands.append(RuntimeConfig(name="intel-openvino-cpu", providers=["OpenVINOExecutionProvider"] + fallback,
                                   provider_options=[{"device_type": "CPU"}] + fallback_opts,
                                   intra_threads=hw.usable_physical_cores, batch_size=8))

    # --- DirectML: any DirectX 12 GPU on Windows (AMD, Intel, NVIDIA). Prefer a discrete adapter if there is one ---
    if "DmlExecutionProvider" in avail and hw.system == "Windows" and (not hw.gpus or discrete or use_igpu):
        # DirectML requires memory-pattern optimisation off and sequential execution
        accel("directml", ["DmlExecutionProvider"], [{"device_id": 0}], batch=8,
              overrides={"enable_mem_pattern": False, "execution_mode": "sequential"})

    # --- CPU: a couple of thread counts, so hyper-threading is only used if it actually helps ---
    phys = hw.usable_physical_cores
    cpu_threads = sorted({phys, hw.usable_cores}) if hw.usable_cores != phys else [phys]
    for t in cpu_threads:
        cands.append(_cpu_config(f"cpu-{t}t", t, 8))
    cands.extend(parallel_session_candidates(hw))           # data-parallel splits: measured, kept only if they win
    return cands


def heuristic_choice(hw: HardwareInfo, candidates: Optional[List[RuntimeConfig]] = None) -> RuntimeConfig:
    """What to use when benchmarking is disabled or fails: a strong GPU if there is one, otherwise the CPU."""
    candidates = candidates if candidates is not None else candidate_configs(hw)
    strong = [g for g in hw.gpus if not g.integrated] or [g for g in hw.gpus if g.vendor == "apple"]
    for c in candidates:
        if c.accelerator and (strong or not hw.gpus):
            return c
    return next(c for c in candidates if not c.accelerator and c.name.startswith("cpu-"))
