import sys

from config import runtime


def test_frozen_app_relaunches_itself_in_worker_mode(monkeypatch):
    """In a PyInstaller build sys.executable is the app, so the benchmark must be `<exe> --bench ...` - not a script
    path, which would start a second full backend (and every model again) for each candidate."""
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd

        class Done:
            stdout = '{"ips": 1.5}'
            stderr = ""
        return Done()

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    cfg = runtime.candidate_configs(runtime.detect_hardware())[0]

    assert runtime._bench_candidate(cfg, "model.onnx") == {"ips": 1.5}
    assert seen["cmd"][0] == sys.executable
    assert seen["cmd"][1] == "--bench"           # no script path in between


def test_unfrozen_run_still_uses_the_script(monkeypatch):
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd

        class Done:
            stdout = '{"ips": 2.0}'
            stderr = ""
        return Done()

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    monkeypatch.delattr(sys, "frozen", raising=False)
    cfg = runtime.candidate_configs(runtime.detect_hardware())[0]
    runtime._bench_candidate(cfg, "model.onnx")
    assert seen["cmd"][1].endswith("runtime.py") and seen["cmd"][2] == "--bench"


def test_run_benchmark_worker_only_claims_bench_invocations(monkeypatch):
    called = []
    monkeypatch.setattr(runtime, "_bench_main", lambda payload: called.append(payload))

    assert runtime.run_benchmark_worker(["app.exe"]) is False
    assert runtime.run_benchmark_worker(["app.exe", "--other", "x"]) is False
    assert called == []
    assert runtime.run_benchmark_worker(["app.exe", "--bench", "{}"]) is True
    assert called == ["{}"]
