"""Experiment 1, step 1: embed LFW with the app's own face pipeline (InsightFace buffalo_s: SCRFD-500M detector +
ArcFace-trained MobileFaceNet recogniser; the largest face per image, exactly as the indexing job does) and cache it.

Resumable: embeddings are checkpointed every 500 images.
"""
import glob
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, ROOT  # noqa: E402

from engines.ai_engine import AIEngine  # noqa: E402

LFW = os.path.join(DS, "lfw", "lfw_funneled")
OUT = os.path.join(CACHE, "lfw_faces.npz")


def main():
    files = sorted(glob.glob(os.path.join(LFW, "*", "*.jpg")))
    print("LFW images:", len(files), flush=True)
    done = {}
    if os.path.exists(OUT):
        d = np.load(OUT, allow_pickle=True)
        done = {p: e for p, e in zip(d["paths"].tolist(), d["emb"])}
        print("resuming with", len(done), flush=True)
    eng = AIEngine(0)
    miss = set(np.load(OUT, allow_pickle=True)["missing"].tolist()) if os.path.exists(OUT) else set()
    todo = [f for f in files if os.path.relpath(f, LFW) not in done and os.path.relpath(f, LFW) not in miss]
    t0 = time.time()
    for i, f in enumerate(todo):
        rel = os.path.relpath(f, LFW)
        img = cv2.imread(f)
        emb = None
        if img is not None:
            faces = eng.get_faces(img)
            if faces:
                faces.sort(key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)
                emb = np.asarray(faces[0].embedding, dtype=np.float32)
        if emb is None:
            miss.add(rel)
        else:
            done[rel] = emb
        if (i + 1) % 500 == 0 or i + 1 == len(todo):
            paths = list(done)
            np.savez(OUT, paths=np.array(paths), emb=np.stack([done[p] for p in paths]), missing=np.array(sorted(miss)))
            rate = (i + 1) / (time.time() - t0)
            print(f"{i + 1}/{len(todo)}  {rate:.1f} img/s  eta {(len(todo) - i - 1) / rate / 60:.1f} min", flush=True)
    print("DONE faces:", len(done), "no-face:", len(miss), flush=True)


if __name__ == "__main__":
    main()
