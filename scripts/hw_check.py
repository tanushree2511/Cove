"""One-command hardware check. Run on each machine you want to cover:

    python scripts/hw_check.py [--label my-laptop] [--skip-tests] [--skip-bench]

Writes evaluation/results/hw_<label>.json with: detected hardware, candidate backends and the heuristic pick,
onnxruntime providers, test-suite result and (optionally) the model benchmark exit status.
It only reports - it never changes any code.
"""
import argparse, json, os, platform, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "cove"))


def run(cmd, timeout):
    t = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {"cmd": " ".join(cmd), "returncode": p.returncode, "seconds": round(time.time() - t, 1),
                "tail": (p.stdout + p.stderr)[-1500:]}
    except Exception as e:  # timeout etc.
        return {"cmd": " ".join(cmd), "returncode": None, "error": repr(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default=platform.node() or "machine")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--skip-bench", action="store_true")
    a = ap.parse_args()

    out = {"label": a.label, "python": sys.version.split()[0], "date": time.strftime("%Y-%m-%d %H:%M")}

    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        out["onnxruntime"] = ort.__version__
    except Exception as e:
        providers = []
        out["onnxruntime_error"] = repr(e)

    try:
        from config import hardware as hw
        info = hw.detect_hardware(providers)
        cands = hw.candidate_configs(info)
        out["hardware"] = info.to_dict()
        out["candidates"] = [c.name for c in cands]
        out["heuristic_choice"] = hw.heuristic_choice(info, cands).name
    except Exception as e:
        out["detect_error"] = repr(e)

    if not a.skip_tests:
        out["tests"] = run([sys.executable, "-m", "pytest", "cove/tests", "-q", "-x", "--no-header"], 1800)
    if not a.skip_bench:
        out["benchmark"] = run([sys.executable, "benchmarks/run_model_benchmarks.py"], 3600)

    path = os.path.join(ROOT, "evaluation", "results", f"hw_{a.label}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out.get(k) for k in ("label", "onnxruntime", "candidates", "heuristic_choice")}, indent=2))
    print("tests rc:", out.get("tests", {}).get("returncode"), "| bench rc:", out.get("benchmark", {}).get("returncode"))
    print("saved ->", path)


if __name__ == "__main__":
    main()
