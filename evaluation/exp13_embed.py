"""Experiment 13a - embed the SAME aligned face crops (crop_faces.py) with every candidate recognition model, and
measure CPU speed.

Models (all ONNX, onnxruntime CPU):
  mbf          buffalo_s w600k_mbf (the app's current model)      models/buffalo_s/w600k_mbf.onnx
  edgeface_s   EdgeFace-S  (gamma 0.5, Idiap 2023)                models/face_candidates/edgeface_s_gamma_05.onnx
  edgeface_xs  EdgeFace-XS (gamma 0.6)                            models/face_candidates/edgeface_xs_gamma_06.onnx
  ghostface    GhostFaceNet W1.3 S1 ArcFace (Alansari 2023)       models/face_candidates/ghostfacenet_w1.3_s1.onnx
Output: cache/emb_<model>_<set>.npz (same format as hard_<set>.npz) and results/exp13_speed.json
Speed: ms per face, (a) batch 1 on ONE thread (a weak device / one worker) and (b) batch 32 using all cores.
"""
import os
import sys
import time

import numpy as np
import onnxruntime as ort

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, be_nice, save_json  # noqa: E402
be_nice()

ROOT = os.path.join(os.path.dirname(__file__), "..", "models")
MODELS = {
    "mbf": (os.path.join(ROOT, "buffalo_s", "w600k_mbf.onnx"), "nchw", 127.5, 127.5),
    "edgeface_s": (os.path.join(ROOT, "face_candidates", "edgeface_s_gamma_05.onnx"), "nchw", 127.5, 127.5),
    "edgeface_xs": (os.path.join(ROOT, "face_candidates", "edgeface_xs_gamma_06.onnx"), "nchw", 127.5, 127.5),
    "ghostface": (os.path.join(ROOT, "face_candidates", "ghostfacenet_w1.3_s1.onnx"), "nhwc", 127.5, 128.0),
}
SETS = [f"lfw_{k}" for k in ("clean", "lowres", "blur", "jpeg", "dark", "occlude")] + ["calfw", "cplfw", "tune_agedb", "tune_cfpfp"]


def session(path, threads):
    o = ort.SessionOptions()
    o.intra_op_num_threads = threads
    o.inter_op_num_threads = 1
    o.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(path, o, providers=["CPUExecutionProvider"])


def prep(crops_bgr, layout, mean, std):
    x = (crops_bgr[..., ::-1].astype(np.float32) - mean) / std        # BGR -> RGB, normalise
    return np.ascontiguousarray(x.transpose(0, 3, 1, 2) if layout == "nchw" else x)


def embed(sess, crops, spec, batch=64):
    name = sess.get_inputs()[0].name
    fixed = sess.get_inputs()[0].shape[0]
    bs = batch if not isinstance(fixed, int) else fixed
    out = []
    for s in range(0, len(crops), bs):
        out.append(sess.run(None, {name: prep(crops[s:s + bs], *spec[1:])})[0].reshape(-1, 512))
    return np.concatenate(out).astype(np.float32)


def speed(path, spec, crops):
    res = {}
    for label, threads, bs in (("1thread_batch1", 1, 1), ("allcores_batch32", os.cpu_count(), 32)):
        s = session(path, threads)
        fixed = s.get_inputs()[0].shape[0]
        bs = fixed if isinstance(fixed, int) else bs
        x = crops[:bs]
        embed(s, x, spec, bs)                                         # warm-up
        n, t0 = 0, time.perf_counter()
        while time.perf_counter() - t0 < 6.0:
            embed(s, x, spec, bs); n += len(x)
        res[label] = 1000 * (time.perf_counter() - t0) / n
    res["params_M"] = None
    try:
        import onnx
        res["params_M"] = sum(np.prod(t.dims) for t in onnx.load(path).graph.initializer) / 1e6
    except Exception:
        pass
    res["file_MB"] = os.path.getsize(path) / 1e6
    return res


def main():
    which = sys.argv[1:] or list(MODELS)
    speeds = {}
    sample = np.load(os.path.join(CACHE, "crops_lfw_clean.npz"))["crops"][:256]
    for m in which:
        spec = MODELS[m]
        if not os.path.exists(spec[0]):
            print(f"[{m}] model file missing, skipped", flush=True); continue
        speeds[m] = speed(spec[0], spec, sample)
        print(f"[{m}] speed {speeds[m]}", flush=True)
        sess = session(spec[0], os.cpu_count())
        for s in SETS:
            out = os.path.join(CACHE, f"emb_{m}_{s}.npz")
            src = os.path.join(CACHE, f"crops_{s}.npz")
            if os.path.exists(out) or not os.path.exists(src):
                continue
            d = np.load(src)
            t0 = time.time()
            E = embed(sess, d["crops"], spec)
            np.savez(out, paths=d["paths"], emb=E, det=np.ones(len(E), np.float32), missing=d["missing"])
            print(f"  [{m}] {s}: {len(E)} faces in {time.time() - t0:.0f}s", flush=True)
    old = {}
    p = os.path.join(os.path.dirname(__file__), "results", "exp13_speed.json")
    if os.path.exists(p):
        import json
        old = json.load(open(p))
    save_json("exp13_speed.json", {**old, **speeds})
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
