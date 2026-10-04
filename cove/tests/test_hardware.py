"""Hardware detection, candidate selection, autotune and the CPU fallback - simulated for every vendor, because CI
(and most dev machines) only have one kind of hardware."""
import json
import os

import numpy as np
import pytest

from config import hardware as hw_mod
from config import runtime as rt
from config.hardware import (CPU, GPUInfo, HardwareInfo, candidate_configs, classify_gpu, cpu_config, heuristic_choice)


def machine(gpus=(), providers=(CPU,), system="Linux", arch="x86_64", physical=4, logical=8, usable=None, apple=False):
    return HardwareInfo(system=system, machine=arch, cpu_name="test cpu", physical_cores=physical, logical_cores=logical,
                        usable_cores=usable or logical, ram_gb=16, available_ram_gb=8, apple_silicon=apple,
                        gpus=[classify_gpu(g) if isinstance(g, str) else g for g in gpus], ort_providers=list(providers))


def names(cands):
    return [c.name for c in cands]


# ------------------------------------------------------------------ GPU classification
@pytest.mark.parametrize("name,vendor,integrated", [
    ("NVIDIA GeForce RTX 3060", "nvidia", False),
    ("NVIDIA A100-SXM4-40GB", "nvidia", False),
    ("AMD Radeon RX 6800 XT", "amd", False),
    ("AMD Radeon(TM) Graphics", "amd", True),
    ("Intel(R) UHD Graphics 620", "intel", True),
    ("Intel(R) Iris(R) Xe Graphics", "intel", True),
    ("Intel(R) Arc(TM) A770 Graphics", "intel", False),
    ("Apple M2 Pro", "apple", True),
    ("Qualcomm(R) Adreno(TM) GPU", "qualcomm", False),
])
def test_classify_gpu(name, vendor, integrated):
    g = classify_gpu(name)
    assert (g.vendor, g.integrated) == (vendor, integrated)


# ------------------------------------------------------------------ cores
def test_usable_physical_cores():
    assert machine(physical=4, logical=8).usable_physical_cores == 4                  # whole laptop: use physical cores
    assert machine(physical=4, logical=8, usable=2).usable_physical_cores == 2        # container limited to 2 CPUs
    assert machine(physical=8, logical=8, arch="arm64").usable_physical_cores == 8    # no SMT
    assert machine(physical=1, logical=1).usable_physical_cores == 1


def test_cgroup_cpu_quota(monkeypatch):
    monkeypatch.setattr(hw_mod, "_read", lambda p: "200000 100000" if p.endswith("cpu.max") else None)
    assert hw_mod._cgroup_cpu_limit() == 2.0
    monkeypatch.setattr(hw_mod, "_read", lambda p: "max 100000" if p.endswith("cpu.max") else None)
    assert hw_mod._cgroup_cpu_limit() is None


def test_detect_hardware_runs_here():
    hw = detect_here = hw_mod.detect_hardware()
    assert hw.logical_cores >= hw.physical_cores >= 1 and 1 <= hw.usable_cores <= hw.logical_cores
    assert CPU in hw.ort_providers


# ------------------------------------------------------------------ candidates per vendor
def test_cpu_only_machine():
    c = candidate_configs(machine())
    assert names(c) == ["cpu-4t", "cpu-8t"]                     # physical cores and all hyper-threads are both tried
    assert not any(x.accelerator for x in c)


def test_nvidia_cuda():
    c = candidate_configs(machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider"]))
    assert c[0].name == "nvidia-cuda" and c[0].providers == ["CUDAExecutionProvider", CPU]
    assert names(c)[-1].startswith("cpu-")                       # CPU is always the last resort
    assert heuristic_choice(machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider"])).name == "nvidia-cuda"


def test_tensorrt_is_opt_in(monkeypatch):
    hw = machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider", "TensorrtExecutionProvider"])
    assert "nvidia-tensorrt" not in names(candidate_configs(hw))
    monkeypatch.setenv("COVE_ENABLE_TRT", "1")
    assert "nvidia-tensorrt" in names(candidate_configs(hw))


def test_nvidia_gpu_but_cpu_only_onnxruntime():
    # a GPU is present but the installed onnxruntime cannot use it -> must not offer an unusable accelerator
    c = candidate_configs(machine(["NVIDIA GeForce RTX 4070"], [CPU]))
    assert not any(x.accelerator for x in c)


def test_amd_rocm_and_migraphx():
    c = candidate_configs(machine(["AMD Radeon RX 7900 XTX"], [CPU, "ROCMExecutionProvider", "MIGraphXExecutionProvider"]))
    assert {"amd-migraphx", "amd-rocm"} <= set(names(c))


def test_apple_silicon_coreml():
    hw = machine(["Apple M2"], [CPU, "CoreMLExecutionProvider"], system="Darwin", arch="arm64", physical=8, logical=8, apple=True)
    c = candidate_configs(hw)
    assert c[0].name == "apple-coreml" and c[0].provider_options[0]["MLComputeUnits"] == "ALL"
    assert heuristic_choice(hw).name == "apple-coreml"


def test_windows_directml_needs_sequential_no_mempattern():
    c = candidate_configs(machine(["AMD Radeon RX 6700"], [CPU, "DmlExecutionProvider"], system="Windows"))
    dml = next(x for x in c if x.name == "directml")
    assert dml.session_overrides == {"enable_mem_pattern": False, "execution_mode": "sequential"}
    assert dml.providers == ["DmlExecutionProvider", CPU]


def test_intel_openvino_variants():
    c = candidate_configs(machine(["Intel(R) UHD Graphics 620"], [CPU, "OpenVINOExecutionProvider"]))
    assert {"intel-openvino-gpu", "intel-openvino-auto", "intel-openvino-cpu"} <= set(names(c))


def test_qualcomm_npu():
    hw = machine(["Qualcomm Adreno"], [CPU, "QNNExecutionProvider"], system="Windows", arch="arm64", physical=8, logical=8)
    q = next(x for x in candidate_configs(hw) if x.name == "qualcomm-npu")
    assert q.provider_options[0]["backend_path"] == "QnnHtp.dll"


def test_weak_integrated_gpu_is_not_chosen_by_heuristic():
    # Intel UHD only: an accelerator exists but a weak iGPU should lose to the CPU unless a benchmark says otherwise
    hw = machine(["Intel(R) UHD Graphics 620"], [CPU, "OpenVINOExecutionProvider", "DmlExecutionProvider"], system="Windows")
    assert not heuristic_choice(hw).accelerator


def test_every_candidate_ends_with_a_cpu_fallback():
    hw = machine(["NVIDIA GeForce RTX 4070", "AMD Radeon RX 7900"],
                 [CPU, "CUDAExecutionProvider", "ROCMExecutionProvider", "OpenVINOExecutionProvider"])
    for c in candidate_configs(hw):
        assert c.providers[-1] == CPU or c.name.startswith("cpu-")
        assert len(c.providers) == len(c.provider_options)


# ------------------------------------------------------------------ autotune
def test_autotune_picks_the_fastest_and_skips_failures(monkeypatch):
    hw = machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider"])
    cands = candidate_configs(hw)
    speeds = {"nvidia-cuda": {"error": "driver crashed"}, "cpu-4t": {"ips": 4.0}, "cpu-8t": {"ips": 3.5}}
    monkeypatch.setattr(rt, "_bench_candidate", lambda cfg, path: speeds[cfg.name])
    p = rt._autotune(hw, cands, "model.onnx")
    assert p.config.name == "cpu-4t" and p.source == "benchmark"
    assert p.images_per_second == 4.0


def test_autotune_prefers_gpu_when_it_is_actually_faster(monkeypatch):
    hw = machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider"])
    speeds = {"nvidia-cuda": {"ips": 180.0}, "cpu-4t": {"ips": 4.0}, "cpu-8t": {"ips": 3.5}}
    monkeypatch.setattr(rt, "_bench_candidate", lambda cfg, path: speeds[cfg.name])
    assert rt._autotune(hw, candidate_configs(hw), "m").config.name == "nvidia-cuda"


def test_autotune_all_failed_falls_back_to_heuristic(monkeypatch):
    hw = machine()
    monkeypatch.setattr(rt, "_bench_candidate", lambda cfg, path: {"error": "boom"})
    p = rt._autotune(hw, candidate_configs(hw), "m")
    assert p.source == "heuristic" and not p.accelerated


def test_profile_is_cached_between_runs(monkeypatch, tmp_path):
    model = tmp_path / "clip_image.onnx"
    model.write_bytes(b"x" * 1000)
    calls = []
    monkeypatch.setattr(rt, "_cache_path", lambda: str(tmp_path / "hardware_profile.json"))
    monkeypatch.setattr(rt, "detect_hardware", lambda: machine())
    monkeypatch.setattr(rt, "_bench_candidate", lambda cfg, path: calls.append(cfg.name) or {"ips": 4.0 if cfg.name == "cpu-4t" else 3.0})
    for var in ("COVE_FORCE_CPU", "COVE_USE_GPU", "COVE_AUTOTUNE"):
        monkeypatch.delenv(var, raising=False)

    monkeypatch.setattr(rt, "_profile", None)
    first = rt.get_runtime_profile(model_path=str(model))
    assert first.source == "benchmark" and calls == ["cpu-4t", "cpu-8t"]

    monkeypatch.setattr(rt, "_profile", None)       # "restart the app"
    second = rt.get_runtime_profile(model_path=str(model))
    assert second.source == "cache" and second.config.name == "cpu-4t" and len(calls) == 2


def test_force_cpu_never_uses_an_accelerator(monkeypatch, tmp_path):
    model = tmp_path / "m.onnx"
    model.write_bytes(b"x")
    monkeypatch.setattr(rt, "detect_hardware", lambda: machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider"]))
    monkeypatch.setattr(rt, "_cache_path", lambda: str(tmp_path / "p.json"))
    monkeypatch.setattr(rt, "_bench_candidate", lambda cfg, path: {"ips": 100.0 if cfg.accelerator else 4.0})
    monkeypatch.setenv("COVE_FORCE_CPU", "1")
    monkeypatch.setattr(rt, "_profile", None)
    assert not rt.get_runtime_profile(model_path=str(model)).accelerated


def test_thread_override(monkeypatch, tmp_path):
    monkeypatch.setenv("COVE_ORT_THREADS", "3")
    monkeypatch.setenv("COVE_AUTOTUNE", "0")
    monkeypatch.setattr(rt, "detect_hardware", lambda: machine())
    monkeypatch.setattr(rt, "_profile", None)
    assert rt.get_runtime_profile(model_path="x").config.intra_threads == 3


# ------------------------------------------------------------------ sizing derived from the profile
def profile(hw, cfg, ips=None):
    return rt.RuntimeProfile(cfg, hw, "test", [{"name": cfg.name, "ips": ips}] if ips else [])


def test_frames_scale_with_hardware_and_video_length():
    slow = profile(machine(), cpu_config("cpu-4t", 4, 8), ips=4.0)       # this laptop
    fast = profile(machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider"]),
                   candidate_configs(machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider"]))[0], ips=200.0)
    assert slow.frames_for_video(10) == 5            # short clip: ~1 frame per 3 s
    assert slow.frames_for_video(600) == 8           # long video: capped by the 2 s CLIP budget
    assert fast.frames_for_video(10) == 5            # a short clip needs no more frames, even on a GPU...
    assert fast.frames_for_video(600) == 14          # ...but a long one gets the full set
    assert slow.frames_for_video(1) == 4             # never fewer than 4


def test_pool_sizes_respect_available_cores():
    p = profile(machine(usable=8), cpu_config("cpu-4t", 4, 8))
    assert p.face_pool_size == 4 and p.face_threads == 2
    small = profile(machine(physical=1, logical=2, usable=1), cpu_config("cpu-1t", 1, 8))
    assert small.face_pool_size == 1 and small.face_threads == 1


# ------------------------------------------------------------------ real onnxruntime: sessions must never fail because a GPU is broken
def _identity_model(path):
    onnx = pytest.importorskip("onnx")
    from onnx import TensorProto, helper
    node = helper.make_node("Identity", ["x"], ["y"])
    graph = helper.make_graph([node], "g", [helper.make_tensor_value_info("x", TensorProto.FLOAT, [None, 3])],
                              [helper.make_tensor_value_info("y", TensorProto.FLOAT, [None, 3])])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    model.ir_version = 8
    onnx.save(model, str(path))


def test_create_session_falls_back_to_cpu_when_the_accelerator_is_unusable(tmp_path):
    ort = pytest.importorskip("onnxruntime")
    path = tmp_path / "id.onnx"
    _identity_model(path)
    broken = hw_mod.RuntimeConfig(name="broken-gpu", providers=["CUDAExecutionProvider", CPU], provider_options=[{"device_id": 99}, {}],
                                  intra_threads=2, batch_size=4, accelerator=True)
    sess = rt.create_session(str(path), broken)
    out = sess.run(None, {"x": np.ones((2, 3), dtype="float32")})[0]
    assert out.shape == (2, 3) and sess.get_providers()[0] == CPU


def test_bench_worker_measures_a_real_model(tmp_path, capsys):
    pytest.importorskip("onnxruntime")
    path = tmp_path / "id.onnx"
    _identity_model(path)
    cfg = cpu_config("cpu-2t", 2, 4)
    rt._bench_main(json.dumps({"model": str(path), "cfg": cfg.to_dict(), "seconds": 0.2}))
    result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    # the identity model takes 3 inputs, not an image -> either a number or a clean error, never a crash
    assert "ips" in result or "error" in result


def test_autotune_breaks_near_ties_toward_fewer_threads_and_accelerators(monkeypatch):
    hw = machine()
    monkeypatch.setattr(rt, "_bench_candidate", lambda cfg, path: {"ips": 4.55 if cfg.name == "cpu-8t" else 4.51})
    assert rt._autotune(hw, candidate_configs(hw), "m").config.name == "cpu-4t"          # 1% faster is noise

    hw = machine(["NVIDIA GeForce RTX 4070"], [CPU, "CUDAExecutionProvider"])
    speeds = {"nvidia-cuda": {"ips": 4.4}, "cpu-4t": {"ips": 4.5}, "cpu-8t": {"ips": 4.3}}
    monkeypatch.setattr(rt, "_bench_candidate", lambda cfg, path: speeds[cfg.name])
    assert rt._autotune(hw, candidate_configs(hw), "m").config.name == "nvidia-cuda"     # tie -> keep the CPU free


def test_observed_throughput_overrides_a_pessimistic_start_up_benchmark():
    # benchmark ran while two services competed for the CPU and read 2.7 img/s; real work runs at ~4.5
    p = profile(machine(), cpu_config("cpu-4t", 4, 8), ips=2.7)
    assert p.images_per_second == 2.7 and p.frames_for_video(600) == 5
    for _ in range(2):
        p.observe_throughput(8, 8 / 4.5)
    assert p.images_per_second == 2.7                       # not enough samples yet
    for _ in range(10):
        p.observe_throughput(8, 8 / 4.5)
    assert 4.3 < p.images_per_second < 4.6 and p.frames_for_video(600) == 9      # 4.5 img/s x 2 s budget


def test_observed_throughput_adapts_when_the_machine_slows_down():
    p = profile(machine(), cpu_config("cpu-4t", 4, 8), ips=4.5)
    for _ in range(20):
        p.observe_throughput(8, 8 / 2.0)                    # thermal throttling
    assert p.images_per_second < 2.2 and p.frames_for_video(600) < 5 + 1
