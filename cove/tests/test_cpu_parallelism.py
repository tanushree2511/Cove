"""CPU utilisation: topology-driven multi-session candidates, the tie-break, the benchmark guards and the batch pipeline."""
import os
import sys
import threading
import time
import types

import numpy as np
import pytest

from config import hardware, runtime
from config.hardware import HardwareInfo, RuntimeConfig, candidate_configs, parallel_session_candidates


def make_hw(physical, logical, ram_gb=16.0, usable=None, machine="x86_64", system="Linux"):
    return HardwareInfo(system=system, machine=machine, cpu_name="test cpu", physical_cores=physical, logical_cores=logical,
                        usable_cores=usable or logical, ram_gb=ram_gb, available_ram_gb=ram_gb / 2,
                        ort_providers=["CPUExecutionProvider"])


# ------------------------------------------------------------------ candidates scale with the topology
@pytest.mark.parametrize("physical,logical", [(6, 12), (8, 16), (16, 32), (64, 128), (12, 12), (8, 8)])
def test_big_machines_get_replica_candidates_that_never_oversubscribe(physical, logical):
    hw = make_hw(physical, logical, ram_gb=64.0)
    cands = candidate_configs(hw)
    cpu = [c for c in cands if not c.accelerator]
    assert cpu[0].name == f"cpu-{physical}t" and cpu[0].sessions == 1       # the old default is still measured (and still the heuristic)
    assert len({c.name for c in cpu}) == len(cpu)
    for c in cpu:
        assert c.total_threads <= logical
        assert c.sessions >= 1 and c.intra_threads >= 1
    multi = [c for c in cpu if c.sessions > 1]
    assert 1 <= len(multi) <= hardware.MAX_MULTI_SESSION_CANDIDATES
    assert max(c.total_threads for c in multi) == logical                  # at least one split that uses every logical core


@pytest.mark.parametrize("physical,logical", [(1, 1), (1, 2), (2, 2), (2, 4), (4, 4), (4, 8)])
def test_small_machines_get_no_replicas_because_one_session_already_saturates_them(physical, logical):
    """Measured on a 4-core / 8-thread laptop CPU: replicas and 8 threads were slower than one 4-thread session."""
    assert parallel_session_candidates(make_hw(physical, logical)) == []
    names = [c.name for c in candidate_configs(make_hw(physical, logical)) if not c.accelerator]
    assert all("x" not in n for n in names)


def test_six_core_machine_splits():
    names = {c.name for c in parallel_session_candidates(make_hw(6, 12, ram_gb=32.0))}
    assert {"cpu-2x6t", "cpu-4x3t"} <= names


def test_container_quota_limits_the_split():
    hw = make_hw(16, 32, usable=2)                                        # only 2 CPUs of quota
    assert parallel_session_candidates(hw) == []


def test_low_memory_machines_get_fewer_replicas():
    small = {c.sessions for c in parallel_session_candidates(make_hw(8, 16, ram_gb=8.0))}
    big = {c.sessions for c in parallel_session_candidates(make_hw(8, 16, ram_gb=64.0))}
    assert max(small) < max(big)
    assert 4 in big


def test_arm_without_smt_splits_the_physical_cores():
    names = {c.name for c in parallel_session_candidates(make_hw(8, 8, ram_gb=32.0, machine="arm64"))}
    assert {"cpu-2x4t", "cpu-4x2t", "cpu-8x1t"} <= names


def test_eight_replicas_are_not_offered_when_memory_is_modest():
    names = {c.name for c in parallel_session_candidates(make_hw(8, 8, ram_gb=16.0, machine="arm64"))}
    assert "cpu-8x1t" not in names and {"cpu-2x4t", "cpu-4x2t"} <= names


def test_candidate_names_do_not_depend_on_free_memory():
    """The names are part of the tuning-cache key: a different amount of FREE RAM must not change them."""
    a, b = make_hw(8, 16), make_hw(8, 16)
    a.available_ram_gb, b.available_ram_gb = 0.5, 12.0
    assert [c.name for c in candidate_configs(a)] == [c.name for c in candidate_configs(b)]


def test_heuristic_choice_is_still_the_single_session_cpu():
    assert hardware.heuristic_choice(make_hw(4, 8)).name == "cpu-4t"
    big = hardware.heuristic_choice(make_hw(8, 16, ram_gb=64.0))
    assert big.name == "cpu-8t" and big.sessions == 1


def test_runtime_config_roundtrip_and_old_dicts():
    cfg = hardware.cpu_config("cpu-2x4t", 4, 8, sessions=2)
    again = RuntimeConfig(**cfg.to_dict())
    assert again.sessions == 2 and again.total_threads == 8
    old = {k: v for k, v in cfg.to_dict().items() if k != "sessions"}      # a config written before replicas existed
    assert RuntimeConfig(**old).sessions == 1


# ------------------------------------------------------------------ autotune: interleaved rounds, noise, the 10% rule
BIG = dict(physical=8, logical=16, ram_gb=64.0)


def _tune(monkeypatch, speed, hw=None):
    """speed(name, call_index_for_that_name) -> ips (None = the candidate fails)"""
    hw = hw or make_hw(**BIG)
    cands = candidate_configs(hw)
    seen = {}

    def fake(cfg, model):
        k = seen.get(cfg.name, 0)
        seen[cfg.name] = k + 1
        v = speed(cfg.name, k)
        return {"ips": v} if v is not None else {"error": "skipped"}

    monkeypatch.setattr(runtime, "_bench_candidate", fake)
    return runtime._autotune(hw, cands, "model.onnx")


def test_candidates_are_measured_in_interleaved_rounds(monkeypatch):
    hw = make_hw(**BIG)
    order = []
    monkeypatch.setattr(runtime, "_bench_candidate", lambda cfg, m: order.append(cfg.name) or {"ips": 5.0})
    runtime._autotune(hw, candidate_configs(hw), "m")
    names = [c.name for c in candidate_configs(hw)]
    assert order == names + names                                          # A B C A B C, not A A B B C C


def test_thermal_drift_cannot_make_the_first_candidate_look_best(monkeypatch):
    """Every candidate is equally fast but the CPU throttles 40% between rounds: the baseline must stay."""
    p = _tune(monkeypatch, lambda name, k: 5.0 if k == 0 else 3.0)
    assert p.config.name == "cpu-8t" and p.config.sessions == 1


def test_a_clearly_faster_split_wins(monkeypatch):
    hw = make_hw(**BIG)
    multi = next(c.name for c in candidate_configs(hw) if c.sessions > 1)
    p = _tune(monkeypatch, lambda name, k: 7.0 if name == multi else 5.0)
    assert p.config.name == multi
    assert any(r["name"] == multi and r["runs"] == [7.0, 7.0] for r in p.results)


def test_a_small_win_is_not_worth_the_extra_memory(monkeypatch):
    hw = make_hw(**BIG)
    multi = next(c.name for c in candidate_configs(hw) if c.sessions > 1)
    p = _tune(monkeypatch, lambda name, k: 5.4 if name == multi else 5.0)     # +8%: above noise, below the 10% bar
    assert p.config.name == "cpu-8t"


def test_within_noise_the_simpler_config_wins(monkeypatch):
    p = _tune(monkeypatch, lambda name, k: 5.05 if "x" in name else (5.0 if name == "cpu-8t" else 4.95))
    assert p.config.name == "cpu-8t"


def test_results_record_every_run_and_failures(monkeypatch):
    hw = make_hw(**BIG)
    multi = next(c.name for c in candidate_configs(hw) if c.sessions > 1)
    p = _tune(monkeypatch, lambda name, k: None if name == multi else 5.0)
    entry = next(r for r in p.results if r["name"] == multi)
    assert "error" in entry and "ips" not in entry


def test_cpu_mode_max_only_offers_layouts_that_load_every_logical_core(monkeypatch, tmp_path):
    hw = make_hw(**BIG)
    hw.ort_providers = ["CPUExecutionProvider"]
    model = tmp_path / "m.onnx"
    model.write_bytes(b"x")
    benched = []
    monkeypatch.setattr(runtime, "detect_hardware", lambda *a, **k: hw)
    monkeypatch.setattr(runtime, "_cache_path", lambda: str(tmp_path / "p.json"))
    monkeypatch.setattr(runtime, "_system_is_calm", lambda *a, **k: True)
    monkeypatch.setattr(runtime, "_bench_candidate", lambda cfg, m: benched.append(cfg) or {"ips": 5.0})
    monkeypatch.setenv("COVE_CPU_MODE", "max")
    monkeypatch.setattr(runtime, "_profile", None)
    p = runtime.get_runtime_profile(model_path=str(model), refresh=True)
    assert benched and all(c.total_threads >= hw.logical_cores and not c.accelerator for c in benched)
    assert p.config.total_threads >= hw.logical_cores
    monkeypatch.setattr(runtime, "_profile", None)


# ------------------------------------------------------------------ stable hardware identity
def test_windows_cpu_name_comes_from_the_registry(monkeypatch):
    fake = types.ModuleType("winreg")
    fake.HKEY_LOCAL_MACHINE = object()

    class Key:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    fake.OpenKey = lambda *a, **k: Key()
    fake.QueryValueEx = lambda key, name: ("  Intel(R) Core(TM)  i5-8250U CPU @ 1.60GHz ", 1)
    monkeypatch.setitem(sys.modules, "winreg", fake)
    monkeypatch.setattr(hardware.platform, "system", lambda: "Windows")
    monkeypatch.setattr(hardware, "_run", lambda *a, **k: pytest.fail("must not spawn PowerShell when the registry answers"))
    assert hardware._cpu_name() == "Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz"


# ------------------------------------------------------------------ benchmark guards
def test_benchmark_lock_is_exclusive_and_releases(tmp_path):
    cache = str(tmp_path / "hardware_profile.json")
    order = []

    def second():
        with runtime._benchmark_lock(cache, wait_s=5) as held:
            order.append(("second", held))

    with runtime._benchmark_lock(cache) as held:
        assert held
        t = threading.Thread(target=second); t.start()
        time.sleep(1.5)
        assert order == []                                               # still waiting while the first holds it
    t.join(5)
    assert order == [("second", True)]
    assert not os.path.exists(cache + ".lock")


def test_a_stale_lock_does_not_block_forever(tmp_path):
    cache = str(tmp_path / "hardware_profile.json")
    with open(cache + ".lock", "w") as f:
        f.write("123")
    old = time.time() - 4000
    os.utime(cache + ".lock", (old, old))
    with runtime._benchmark_lock(cache, wait_s=3, stale_s=100) as held:
        assert held


def test_busy_cpu_skips_the_benchmark_and_caches_nothing(monkeypatch, tmp_path):
    cache = tmp_path / "hardware_profile.json"
    model = tmp_path / "m.onnx"; model.write_bytes(b"x")
    hw = make_hw(4, 8, system="Windows")
    hw.ort_providers = ["CPUExecutionProvider", "DmlExecutionProvider"]
    hw.gpus = [hardware.GPUInfo("Intel UHD", "intel", None, True)]
    monkeypatch.setattr(runtime, "detect_hardware", lambda *a, **k: hw)
    monkeypatch.setattr(runtime, "_cache_path", lambda: str(cache))
    monkeypatch.setattr(runtime, "_system_is_calm", lambda *a, **k: False)
    monkeypatch.setattr(runtime, "_autotune", lambda *a, **k: pytest.fail("benchmarked while the CPU was busy"))
    monkeypatch.setattr(runtime, "_profile", None)
    p = runtime.get_runtime_profile(model_path=str(model), refresh=True)
    assert p.source == "heuristic-busy" and not p.config.accelerator
    assert not cache.exists()
    monkeypatch.setattr(runtime, "_profile", None)


def test_system_is_calm_waits_for_a_short_burst(monkeypatch):
    loads = iter([80.0, 70.0, 10.0])
    fake = types.SimpleNamespace(cpu_percent=lambda interval=None: next(loads))
    monkeypatch.setitem(sys.modules, "psutil", fake)
    assert runtime._system_is_calm(limit_percent=35, wait_s=10) is True
    monkeypatch.setitem(sys.modules, "psutil", types.SimpleNamespace(cpu_percent=lambda interval=None: 95.0))
    assert runtime._system_is_calm(limit_percent=35, wait_s=1.5) is False


# ------------------------------------------------------------------ the batch pipeline
class FakeSession:
    """Stands in for an onnxruntime session; embedding = the value every pixel of an image carries."""
    active = 0
    peak = 0
    lock = threading.Lock()

    def __init__(self, fail_on_batches=False, delay=0.05):
        self.fail_on_batches, self.delay, self.calls = fail_on_batches, delay, 0

    def run(self, _outputs, feed):
        x = next(iter(feed.values()))
        if self.fail_on_batches and len(x) > 1:
            raise RuntimeError("batch size must be 1")
        with FakeSession.lock:
            FakeSession.active += 1
            FakeSession.peak = max(FakeSession.peak, FakeSession.active)
        time.sleep(self.delay)
        with FakeSession.lock:
            FakeSession.active -= 1
        self.calls += 1
        v = x.reshape(len(x), -1)[:, 0]
        out = np.zeros((len(x), 4), dtype="float32"); out[:, 0] = v + 1.0; out[:, 1] = 1.0
        return [out]


def make_engine(sessions, batch_size=4, bad=()):
    from engines.search_engine import SearchEngine
    eng = SearchEngine.__new__(SearchEngine)
    eng.config = types.SimpleNamespace(effective_workers=4, runtime_profile=None)
    eng.batch_size, eng._batching_ok, eng._img_input_name = batch_size, True, "pixel_values"
    eng.img_sessions = sessions
    eng.img_session = sessions[0]

    def pre(item):
        if item in bad:
            raise IOError("unreadable")
        return np.full((3, 2, 2), float(item), dtype="float32")

    eng._preprocess = pre
    return eng


def expected(i):
    v = np.array([i + 1.0, 1.0, 0.0, 0.0], dtype="float32")
    return v / (np.linalg.norm(v) + 1e-6)


def test_results_keep_input_order_with_several_replicas():
    FakeSession.active = FakeSession.peak = 0
    sessions = [FakeSession() for _ in range(3)]
    eng = make_engine(sessions, batch_size=4)
    out = eng.get_image_embeddings(list(range(30)))
    assert len(out) == 30
    for i, e in enumerate(out):
        np.testing.assert_allclose(e, expected(i), atol=1e-5)
    assert all(s.calls > 0 for s in sessions)                              # every replica did work
    assert FakeSession.peak >= 2                                           # and they really ran at the same time


def test_unreadable_images_come_back_as_none_and_do_not_shift_the_rest():
    eng = make_engine([FakeSession(), FakeSession()], batch_size=4, bad={3, 7})
    out = eng.get_image_embeddings(list(range(12)))
    assert out[3] is None and out[7] is None
    for i in (0, 1, 2, 4, 5, 6, 8, 9, 10, 11):
        np.testing.assert_allclose(out[i], expected(i), atol=1e-5)


def test_single_image_and_empty_inputs():
    eng = make_engine([FakeSession()])
    assert eng.get_image_embeddings([]) == []
    np.testing.assert_allclose(eng.get_image_embeddings([5])[0], expected(5), atol=1e-5)
    assert eng.get_image_embeddings([5], batch_size=8)[0] is not None


def test_model_that_only_accepts_batch_one_degrades_gracefully():
    eng = make_engine([FakeSession(fail_on_batches=True)], batch_size=4)
    out = eng.get_image_embeddings(list(range(10)))
    assert eng._batching_ok is False
    for i, e in enumerate(out):
        np.testing.assert_allclose(e, expected(i), atol=1e-5)


def test_pipeline_overlaps_work_so_replicas_beat_one_session():
    items = list(range(24))
    one = make_engine([FakeSession(delay=0.1)], batch_size=4)
    t = time.perf_counter(); one.get_image_embeddings(items); t_one = time.perf_counter() - t
    three = make_engine([FakeSession(delay=0.1) for _ in range(3)], batch_size=4)
    t = time.perf_counter(); three.get_image_embeddings(items); t_three = time.perf_counter() - t
    assert t_three < 0.7 * t_one


# ------------------------------------------------------------------ integrated GPUs are opt-in (this laptop = CPU only)
def gpu_machine(gpu_names, providers, system="Windows", machine="AMD64", physical=4, logical=8):
    hw = make_hw(physical, logical, system=system, machine=machine)
    hw.gpus = [hardware.classify_gpu(n) for n in gpu_names]
    hw.ort_providers = providers
    return hw


def names_of(hw):
    return [c.name for c in candidate_configs(hw)]


def test_intel_laptop_with_only_an_integrated_gpu_is_cpu_only(monkeypatch):
    monkeypatch.delenv("COVE_USE_IGPU", raising=False)
    hw = gpu_machine(["Intel(R) UHD Graphics 620"], ["CPUExecutionProvider", "DmlExecutionProvider"])
    assert names_of(hw) == ["cpu-4t", "cpu-8t"]
    assert hardware.heuristic_choice(hw).name == "cpu-4t"


def test_the_integrated_gpu_can_be_switched_back_on(monkeypatch):
    monkeypatch.setenv("COVE_USE_IGPU", "1")
    hw = gpu_machine(["Intel(R) UHD Graphics 620"], ["CPUExecutionProvider", "DmlExecutionProvider"])
    assert "directml" in names_of(hw)


@pytest.mark.parametrize("gpu", ["AMD Radeon(TM) Graphics", "Intel(R) Iris(R) Xe Graphics", "Radeon Vega 8 Graphics"])
def test_apu_and_xe_graphics_are_not_benchmarked_by_default(monkeypatch, gpu):
    monkeypatch.delenv("COVE_USE_IGPU", raising=False)
    hw = gpu_machine([gpu], ["CPUExecutionProvider", "DmlExecutionProvider", "OpenVINOExecutionProvider", "ROCMExecutionProvider"])
    assert not any(c.accelerator for c in candidate_configs(hw))


def test_integrated_intel_gpu_still_gets_the_openvino_cpu_candidate(monkeypatch):
    monkeypatch.delenv("COVE_USE_IGPU", raising=False)
    hw = gpu_machine(["Intel(R) UHD Graphics 620"], ["CPUExecutionProvider", "OpenVINOExecutionProvider"], system="Linux")
    n = names_of(hw)
    assert "intel-openvino-cpu" in n and "intel-openvino-gpu" not in n and "intel-openvino-auto" not in n


def test_discrete_gpus_are_unaffected(monkeypatch):
    monkeypatch.delenv("COVE_USE_IGPU", raising=False)
    arc = gpu_machine(["Intel(R) Arc(TM) A770 Graphics"], ["CPUExecutionProvider", "OpenVINOExecutionProvider", "DmlExecutionProvider"])
    assert {"intel-openvino-gpu", "directml"} <= set(names_of(arc))
    both = gpu_machine(["Intel(R) UHD Graphics 630", "NVIDIA GeForce RTX 3060"], ["CPUExecutionProvider", "CUDAExecutionProvider", "DmlExecutionProvider"])
    assert {"nvidia-cuda", "directml"} <= set(names_of(both))
    assert hardware.heuristic_choice(both).name == "nvidia-cuda"


def test_apple_silicon_keeps_core_ml():
    hw = gpu_machine(["Apple M2"], ["CPUExecutionProvider", "CoreMLExecutionProvider"], system="Darwin", machine="arm64", physical=8, logical=8)
    hw.apple_silicon = True
    assert "apple-coreml" in names_of(hw)


def test_unknown_gpu_situation_still_offers_directml(monkeypatch):
    """Detection can fail (no GPU list): then let the benchmark decide rather than silently dropping the accelerator."""
    monkeypatch.delenv("COVE_USE_IGPU", raising=False)
    hw = gpu_machine([], ["CPUExecutionProvider", "DmlExecutionProvider"])
    assert "directml" in names_of(hw)


def test_windows_gpus_come_from_the_registry_without_spawning_anything(monkeypatch):
    fake = types.ModuleType("winreg")
    fake.HKEY_LOCAL_MACHINE = object()
    adapters = {"0000": {"DriverDesc": "Intel(R) UHD Graphics 620"}, "0001": {"DriverDesc": "Microsoft Basic Display Adapter"},
                "0002": {"DriverDesc": "NVIDIA GeForce RTX 3050", "HardwareInformation.qwMemorySize": 4 * 1024 ** 3},
                "Configuration": {}, "Properties": {}}

    class Key:
        def __init__(self, name=None):
            self.name = name

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    fake.OpenKey = lambda parent, sub: Key(sub if isinstance(sub, str) and sub in adapters else None)

    def enum_key(key, i):
        keys = list(adapters)
        if i >= len(keys):
            raise OSError("no more")
        return keys[i]

    def query(key, value):
        try:
            return (adapters[key.name][value], 1)
        except KeyError:
            raise OSError(value)

    fake.EnumKey = enum_key
    fake.QueryValueEx = query
    monkeypatch.setitem(sys.modules, "winreg", fake)
    gpus = hardware._windows_gpus_from_registry()
    assert [g.name for g in gpus] == ["Intel(R) UHD Graphics 620", "NVIDIA GeForce RTX 3050"]
    assert gpus[0].integrated and not gpus[1].integrated and gpus[1].vram_mb == 4096


def test_registry_failure_returns_an_empty_list_not_an_exception(monkeypatch):
    monkeypatch.setitem(sys.modules, "winreg", None)           # import raises
    assert hardware._windows_gpus_from_registry() == []


# ------------------------------------------------------------------ never crash: bounded benchmark, replicas, small machines
def test_cpu_candidates_are_benchmarked_before_accelerators(monkeypatch):
    hw = gpu_machine(["NVIDIA GeForce RTX 4070"], ["CPUExecutionProvider", "CUDAExecutionProvider"], system="Linux", machine="x86_64")
    order = []
    monkeypatch.setattr(runtime, "_bench_candidate", lambda cfg, m: order.append(cfg.name) or {"ips": 5.0})
    runtime._autotune(hw, candidate_configs(hw), "m")
    assert order.index("cpu-4t") < order.index("nvidia-cuda")


def test_the_benchmark_has_a_wall_clock_budget(monkeypatch):
    hw = make_hw(8, 16, ram_gb=64.0)
    calls = []
    monkeypatch.setenv("COVE_BENCH_BUDGET_S", "0")
    monkeypatch.setattr(runtime, "_bench_candidate", lambda cfg, m: calls.append(cfg.name) or {"ips": 5.0})
    p = runtime._autotune(hw, candidate_configs(hw), "m")
    assert calls == ["cpu-8t"]                                             # the first candidate is always measured, then the budget stops it
    assert p.config.name == "cpu-8t"


def test_failed_extra_replicas_leave_the_ones_that_worked(monkeypatch):
    made = []

    def fake_create(model, cfg, threads=None):
        if len(made) >= 2:
            raise MemoryError("no memory for another replica")
        made.append(object())
        return made[-1]

    monkeypatch.setattr(runtime, "create_session", fake_create)
    assert len(runtime.create_sessions("m.onnx", hardware.cpu_config("cpu-4x2t", 2, 8, sessions=4))) == 2


def test_a_failing_first_session_is_still_an_error(monkeypatch):
    def broken(*a, **k):
        raise RuntimeError("model missing")

    monkeypatch.setattr(runtime, "create_session", broken)
    with pytest.raises(RuntimeError):
        runtime.create_sessions("m.onnx", hardware.cpu_config("cpu-4t", 4, 8))


@pytest.mark.parametrize("ram,expected_max", [(2.0, 1), (3.9, 1), (4.0, 2), (5.5, 2), (8.0, 4), (64.0, 4)])
def test_face_replicas_shrink_on_low_memory_machines(ram, expected_max):
    hw = make_hw(8, 16, ram_gb=ram)
    prof = runtime.RuntimeProfile(hardware.cpu_config("cpu-8t", 8, 8), hw, "benchmark")
    assert 1 <= prof.face_pool_size <= expected_max
    if ram >= 8:
        assert prof.face_pool_size == 4


def test_calm_check_never_raises(monkeypatch):
    def boom(interval=None):
        raise OSError("counters unavailable")

    monkeypatch.setitem(sys.modules, "psutil", types.SimpleNamespace(cpu_percent=boom))
    assert runtime._system_is_calm(wait_s=1) is True


def test_a_batch_that_fails_unexpectedly_does_not_abort_the_rest():
    class Flaky(FakeSession):
        def run(self, outputs, feed):
            x = next(iter(feed.values()))
            if float(x.reshape(len(x), -1)[0, 0]) in (4.0, 5.0, 6.0, 7.0):      # the whole second batch (batch size 4)
                raise RuntimeError("driver reset")
            return super().run(outputs, feed)

    eng = make_engine([Flaky(delay=0.0)], batch_size=4)
    out = eng.get_image_embeddings(list(range(12)))
    assert all(out[i] is None for i in (4, 5, 6, 7))
    for i in (0, 1, 2, 3, 8, 9, 10, 11):
        np.testing.assert_allclose(out[i], expected(i), atol=1e-5)
