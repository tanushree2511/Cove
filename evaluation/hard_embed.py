"""Embed the CHALLENGING test sets with the app's own face pipeline (buffalo_s: SCRFD-500M + ArcFace MobileFaceNet,
largest face per image), in parallel worker processes.

Sets
  calfw            CALFW  - cross-age LFW (same people photographed years/decades apart)      datasets/calfw/raw/images
  cplfw            CPLFW  - cross-pose LFW (profile and three-quarter views)                  datasets/cplfw/train/images
  lfw_<degr>       LFW images used by the exp8 personal libraries, degraded on the fly:
                     clean | lowres (face ~16 px) | blur (Gaussian sigma 3) | jpeg (quality 8)
                     | dark (gamma 3 + sensor noise) | occlude (black band over the eyes, like sunglasses)
Output: evaluation/cache/hard_<set>.npz  (paths, emb (raw, un-normalised), det, missing). Resumable.
Run:    python evaluation/hard_embed.py <set> [<set> ...]
"""
import glob
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, be_nice, plan_parallelism  # noqa: E402
be_nice()

WORKERS, THREADS_PER_WORKER = plan_parallelism(mem_per_worker_gb=0.6)  # ONNX inference: CPU budget split over workers
LFW = os.path.join(DS, "lfw", "lfw_funneled")
DEGRADATIONS = ("clean", "lowres", "blur", "jpeg", "dark", "occlude")


def degrade(img, kind, key):
    rng = np.random.RandomState(abs(hash(key)) % (2 ** 31))
    h, w = img.shape[:2]
    if kind == "clean":
        return img
    if kind == "lowres":                                   # LFW face ~100 px -> ~16 px, then back up (what a phone thumbnail / far-away face gives)
        small = cv2.resize(img, (w * 16 // 100, h * 16 // 100), interpolation=cv2.INTER_AREA)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    if kind == "blur":
        return cv2.GaussianBlur(img, (0, 0), 3.0)
    if kind == "jpeg":
        return cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 8])[1], cv2.IMREAD_COLOR)
    if kind == "dark":
        x = (img.astype(np.float32) / 255.0) ** 3.0 * 255.0
        x += rng.normal(0, 6, x.shape)
        return np.clip(x, 0, 255).astype(np.uint8)
    if kind == "occlude":                                  # funneled LFW: eyes sit at ~y 0.44-0.54 of the image
        out = img.copy()
        out[int(h * 0.40):int(h * 0.56), int(w * 0.26):int(w * 0.74)] = 0
        return out
    raise ValueError(kind)


def lfw_library_files():
    """Every LFW image used by the exp8 test (seed 0) and tuning (seed 1) libraries - the personal-library stress tests reuse them."""
    from exp7_order_stability import load_raw
    from exp8_personal_libraries import make_libraries
    paths, _, _, ident = load_raw()
    idx = sorted(set(np.concatenate(make_libraries(ident, seed=0) + make_libraries(ident, seed=1)).tolist()))  # test + tuning libraries
    return [paths[i].replace("\\", "/") for i in idx]


def files_for(set_name):
    if set_name == "calfw":
        root = os.path.join(DS, "calfw", "raw", "images")
        return root, sorted(os.path.relpath(f, root).replace("\\", "/") for f in glob.glob(os.path.join(root, "*", "*.jpg")))
    if set_name == "cplfw":
        root = os.path.join(DS, "cplfw", "train", "images")
        return root, sorted(os.path.relpath(f, root).replace("\\", "/") for f in glob.glob(os.path.join(root, "*", "*.jpg")))
    if set_name in ("tune_agedb", "tune_cfpfp"):                       # pose / age TUNING sets (never used for testing)
        root = os.path.join(DS, "hardtune", {"tune_agedb": "agedb_30", "tune_cfpfp": "cfp_fp"}[set_name], "images")
        return root, sorted(os.path.relpath(f, root).replace("\\", "/") for f in glob.glob(os.path.join(root, "*", "*.jpg")))
    if set_name.startswith("lfw_") and set_name[4:] in DEGRADATIONS:
        return LFW, lfw_library_files()
    raise ValueError(set_name)


_E = {}


def _init():
    os.environ["OMP_NUM_THREADS"] = str(THREADS_PER_WORKER)
    from engines.ai_engine import AIEngine
    from config.hardware import cpu_config
    from config.runtime import create_session
    eng = AIEngine(0)
    cfg = cpu_config("bench-face", THREADS_PER_WORKER, 1)
    for model in eng.app.models.values():           # pin each worker to its own small thread budget
        if getattr(model, "model_file", None) and hasattr(model, "session"):
            model.session = create_session(model.model_file, cfg)
    _E["eng"] = eng


def _embed(args):
    root, rel, kind = args
    img = cv2.imread(os.path.join(root, rel))
    if img is None:
        return rel, None, 0.0
    if kind:
        img = degrade(img, kind, rel)
    faces = _E["eng"].get_faces(img)
    if not faces:
        return rel, None, 0.0
    f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
    return rel, np.asarray(f.embedding, dtype=np.float32), float(f.det_score)


def run(set_name, pool):
    out = os.path.join(CACHE, f"hard_{set_name}.npz")
    root, files = files_for(set_name)
    kind = set_name[4:] if set_name.startswith("lfw_") else None
    done, det, miss = {}, {}, set()
    if os.path.exists(out):
        d = np.load(out, allow_pickle=True)
        done = dict(zip(d["paths"].tolist(), d["emb"]))
        det = dict(zip(d["paths"].tolist(), d["det"].tolist()))
        miss = set(d["missing"].tolist())
    todo = [f for f in files if f not in done and f not in miss]
    print(f"[{set_name}] {len(files)} images, {len(todo)} to embed, {WORKERS} workers x {THREADS_PER_WORKER} threads", flush=True)
    t0 = time.time()

    def save():
        p = list(done)
        np.savez(out, paths=np.array(p), emb=np.stack([done[k] for k in p]) if p else np.zeros((0, 512), np.float32),
                 det=np.array([det[k] for k in p]), missing=np.array(sorted(miss)))

    for i, (rel, emb, sc) in enumerate(pool.map(_embed, [(root, f, kind) for f in todo], chunksize=16)):
        if emb is None:
            miss.add(rel)
        else:
            done[rel], det[rel] = emb, sc
        if (i + 1) % 1000 == 0:
            save()
            r = (i + 1) / (time.time() - t0)
            print(f"  {i + 1}/{len(todo)} {r:.1f} img/s eta {(len(todo) - i - 1) / r / 60:.1f} min", flush=True)
    save()
    print(f"[{set_name}] DONE faces={len(done)} no-face={len(miss)} ({100 * len(miss) / max(1, len(files)):.1f}%)", flush=True)


if __name__ == "__main__":
    sets = sys.argv[1:] or [f"lfw_{k}" for k in DEGRADATIONS] + ["calfw", "cplfw"]
    with ProcessPoolExecutor(WORKERS, initializer=_init) as pool:
        for s in sets:
            run(s, pool)
    print("ALL DONE", flush=True)
