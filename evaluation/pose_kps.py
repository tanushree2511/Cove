"""Head-pose signal for every face used in the evaluation: re-runs the app's SCRFD detector (same image, same
degradation, same largest-face rule as crop_faces.py) and stores the 5 landmarks of the chosen face plus a yaw proxy:
    yaw = (nose_x - eye_mid_x) / inter-eye distance      (~0 frontal, |yaw| large for profile)
The app gets these landmarks for free from the detector it already runs, so the signal costs nothing at run time.
Output: cache/pose_<set>.npz (paths, kps (n,5,2), yaw (n,))
Run: python evaluation/pose_kps.py [<set> ...]
"""
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import hard_embed as H  # noqa: E402
from adaptive import run_adaptive  # noqa: E402
from common import CACHE, be_nice  # noqa: E402
be_nice()

_D = {}


def _init():
    os.environ["OMP_NUM_THREADS"] = "1"
    from engines.ai_engine import AIEngine
    _D["det"] = AIEngine(0).app.det_model


def _job(args):
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
    return rel, kps[k].astype("float32")


def yaw_of(kps):
    le, re, nose = kps[:, 0], kps[:, 1], kps[:, 2]
    d = np.linalg.norm(re - le, axis=1) + 1e-6
    return (nose[:, 0] - (le[:, 0] + re[:, 0]) / 2) / d


def run(set_name):
    out = os.path.join(CACHE, f"pose_{set_name}.npz")
    if os.path.exists(out):
        print(f"[{set_name}] exists, skip", flush=True)
        return
    root, files = H.files_for(set_name)
    kind = set_name[4:] if set_name.startswith("lfw_") else None
    t0 = time.time()
    res = [r for r in run_adaptive(_job, [(root, f, kind) for f in files], initializer=_init, name=set_name)
           if r[1] is not None]
    res.sort()
    kps = np.stack([k for _, k in res])
    np.savez(out, paths=np.array([p for p, _ in res]), kps=kps, yaw=yaw_of(kps))
    print(f"[{set_name}] DONE faces={len(res)} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:] or ["lfw_clean", "tune_cfpfp", "cplfw", "calfw", "lfw_lowres", "lfw_blur", "lfw_jpeg",
                              "lfw_dark", "lfw_occlude"]:
        run(s)
    print("ALL DONE", flush=True)
