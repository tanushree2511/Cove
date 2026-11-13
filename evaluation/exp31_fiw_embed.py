"""Experiment 31a - detect/align and embed the FIW face crops (Families in the Wild), for an outside-data test.

FIW (https://web.northeastern.edu/smilelab/fiw/) terms: non-commercial research and education only, do NOT distribute the
images, cite the FIW papers. The images stay in datasets/fiw/ (git-ignored); only embeddings and numbers are derived.

Each FIW file is a small face crop: datasets/fiw/all/FIDs/F####/MID#/P#####_face#.jpg. Identity = (family, member) = "F####/MID#".
Photo = (family, P#####): faces from the same photo are different people (a free cannot-link, not used here).
Same detector and alignment as the LFW experiments (SCRFD from the app, largest face, 5-point ArcFace alignment to 112x112).
If no face is found in a crop, the crop is resized to 112x112 and flagged (counted and reported), so no face is dropped.
Output: cache/fiw_crops.npz (paths, crops, fallback flag) and cache/emb_edgeface_s_fiw.npz / emb_mbf_fiw.npz
Run: python evaluation/exp31_fiw_embed.py [limit]      (limit = embed only the first N files, for a speed test)
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import hard_embed as H  # noqa: E402
from common import CACHE, be_nice  # noqa: E402
be_nice()

ROOT = os.path.join(os.path.dirname(__file__), "..", "datasets", "fiw", "all", "FIDs")
_D = {}


def _init():
    os.environ["OMP_NUM_THREADS"] = str(H.THREADS_PER_WORKER)
    from engines.ai_engine import AIEngine
    _D["det"] = AIEngine(0).app.det_model


def _crop(rel):
    from insightface.utils import face_align
    img = cv2.imread(os.path.join(ROOT, rel))
    if img is None:
        return rel, None, True
    boxes, kps = _D["det"].detect(img, max_num=0, metric="default")
    if boxes is None or len(boxes) == 0:
        return rel, cv2.resize(img, (112, 112), interpolation=cv2.INTER_LINEAR), True
    k = int(np.argmax((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])))
    return rel, face_align.norm_crop(img, landmark=kps[k], image_size=112), False


def list_files():
    out = []
    for f in sorted(os.listdir(ROOT)):
        fp = os.path.join(ROOT, f)
        if not os.path.isdir(fp):
            continue
        for m in sorted(os.listdir(fp)):
            mp = os.path.join(fp, m)
            if os.path.isdir(mp):
                out += [f"{f}/{m}/{x}" for x in sorted(os.listdir(mp)) if x.lower().endswith(".jpg")]
    return out


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    files = list_files()
    if limit:
        files = files[:limit]
    tag = "fiw" if not limit else f"fiw_test{limit}"
    print(f"{len(files)} FIW files, {H.WORKERS} workers x {H.THREADS_PER_WORKER} threads", flush=True)
    out = os.path.join(CACHE, f"crops_{tag}.npz")
    t0 = time.time()
    if not os.path.exists(out):
        paths, crops, fb = [], [], []
        with ProcessPoolExecutor(H.WORKERS, initializer=_init) as pool:
            for i, (rel, c, flag) in enumerate(pool.map(_crop, files, chunksize=16)):
                if c is None:
                    continue
                paths.append(rel); crops.append(c); fb.append(flag)
                if (i + 1) % 2000 == 0:
                    r = (i + 1) / (time.time() - t0)
                    print(f"  crop {i + 1}/{len(files)} {r:.0f}/s eta {(len(files) - i - 1) / r / 60:.1f} min", flush=True)
        np.savez(out, paths=np.array(paths), crops=np.stack(crops), missing=np.array([]), fallback=np.array(fb))
        print(f"crops done in {time.time() - t0:.0f}s; fallback (no face found, resized) = {int(np.sum(fb))}/{len(fb)}", flush=True)
    # embed with the two recognisers using the same code path as exp13
    import exp13_embed as E
    d = np.load(out)
    for m in ("edgeface_s", "mbf"):
        spec = E.MODELS[m]
        sess = E.session(spec[0], os.cpu_count())
        t1 = time.time()
        emb = E.embed(sess, d["crops"], spec)
        np.savez(os.path.join(CACHE, f"emb_{m}_{tag}.npz"), paths=d["paths"], emb=emb, det=np.ones(len(emb), np.float32),
                 missing=d["missing"], fallback=d["fallback"])
        print(f"[{m}] {len(emb)} faces embedded in {time.time() - t1:.0f}s", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
