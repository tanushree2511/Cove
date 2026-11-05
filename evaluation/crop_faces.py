"""Detect + align faces ONCE (the app's SCRFD detector from buffalo_s, largest face, standard 5-point ArcFace
alignment to 112x112) and store the crops, so every candidate recognition model is compared on IDENTICAL faces.
Same sets / degradations / image lists as hard_embed.py.
Output: evaluation/cache/crops_<set>.npz  (paths, crops uint8 (n,112,112,3) BGR, missing)
Run:    python evaluation/crop_faces.py <set> [<set> ...]
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import hard_embed as H  # noqa: E402  (sets, degradations, worker sizing)
from common import CACHE  # noqa: E402

_D = {}


def _init():
    os.environ["OMP_NUM_THREADS"] = str(H.THREADS_PER_WORKER)
    from engines.ai_engine import AIEngine          # exactly the app's detector and detector settings
    det = AIEngine(0).app.det_model
    _D["det"] = det


def _crop(args):
    from insightface.utils import face_align
    root, rel, kind = args
    img = cv2.imread(os.path.join(root, rel))
    if img is None:
        return rel, None
    if kind:
        img = H.degrade(img, kind, rel)
    boxes, kps = _D["det"].detect(img, max_num=0, metric="default")
    if boxes is None or len(boxes) == 0:
        return rel, None
    k = int(np.argmax((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])))
    return rel, face_align.norm_crop(img, landmark=kps[k], image_size=112)


def run(set_name, pool):
    out = os.path.join(CACHE, f"crops_{set_name}.npz")
    if os.path.exists(out):
        print(f"[{set_name}] exists, skip", flush=True)
        return
    root, files = H.files_for(set_name)
    kind = set_name[4:] if set_name.startswith("lfw_") else None
    t0, paths, crops, miss = time.time(), [], [], []
    for i, (rel, c) in enumerate(pool.map(_crop, [(root, f, kind) for f in files], chunksize=16)):
        if c is None:
            miss.append(rel)
        else:
            paths.append(rel); crops.append(c)
        if (i + 1) % 2000 == 0:
            r = (i + 1) / (time.time() - t0)
            print(f"  [{set_name}] {i + 1}/{len(files)} {r:.0f} img/s eta {(len(files) - i - 1) / r / 60:.1f} min", flush=True)
    np.savez(out, paths=np.array(paths), crops=np.stack(crops), missing=np.array(miss))
    print(f"[{set_name}] DONE faces={len(paths)} no-face={len(miss)}", flush=True)


if __name__ == "__main__":
    sets = sys.argv[1:] or [f"lfw_{k}" for k in H.DEGRADATIONS] + ["calfw", "cplfw", "tune_agedb", "tune_cfpfp"]
    with ProcessPoolExecutor(H.WORKERS, initializer=_init) as pool:
        for s in sets:
            run(s, pool)
    print("ALL DONE", flush=True)
