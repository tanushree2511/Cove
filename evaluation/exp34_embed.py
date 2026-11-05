"""Experiments 3 + 4, step 1: decode a dense 25-frame pool for every video and embed it once.

Every sampling strategy under test is then derived from this pool (see exp34_analyze.py), so each video is decoded and
embedded only once:  uniform-N = N evenly spaced pool frames (temporal offset <= 1/48 of the clip), middle-frame = the exact
middle frame (index 12 of 25), dense reference = all 25.   Frames are read with the same cv2 seek logic as the app
(videoModules/core/video_processor.py) and embedded with the app's own engine (BGR->RGB, CLIP ViT-B/16).

usage: exp34_embed.py ucf | msrvtt          (resumable; checkpoints every 20 videos)
"""
import json
import os
import sys
import time

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS  # noqa: E402

from engines.search_engine import SearchEngine  # noqa: E402

POOL = {"ucf": 25, "msrvtt": 15}
SETS = {
    "ucf": (os.path.join(DS, "ucf101", "ucf101_1000.json"), os.path.join(DS, "ucf101", "videos1k")),
    "msrvtt": (os.path.join(DS, "msrvtt", "msrvtt_test_1k.json"), os.path.join(DS, "msrvtt", "videos1k")),
}


def read_pool(path, n):
    """n frames at linspace(0, T-1, n) positions (same seek-based reader as the app) + their gray histograms."""
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    if total <= 0:
        total = 60
    idx = np.linspace(0, total - 1, n).astype(int)
    frames, hists, ok_idx = [], [], []
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ret, fr = cap.read()
        if not ret:
            continue
        h, w = fr.shape[:2]
        if max(h, w) > 1280:
            s = 1280.0 / max(h, w)
            fr = cv2.resize(fr, (int(w * s), int(h * s)))
        frames.append(fr); ok_idx.append(int(i))
    if len(frames) < n // 2:                                  # bad index: fall back to a sequential read (like the app)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        seq = []
        while True:
            ret, fr = cap.read()
            if not ret:
                break
            seq.append(fr)
        if seq:
            sel = np.linspace(0, len(seq) - 1, n).astype(int)
            frames, ok_idx = [seq[j] for j in sel], [int(j) for j in sel]
    cap.release()
    for fr in frames:
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        hh = cv2.calcHist([g], [0], None, [256], [0, 256])
        hists.append(cv2.normalize(hh, hh).flatten())
    return frames, np.array(hists, dtype="float32"), ok_idx, total, fps


def to_pil(fr):
    return Image.fromarray(np.ascontiguousarray(fr[:, :, ::-1]))


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "ucf"
    meta_path, vdir = SETS[which]
    meta = json.load(open(meta_path, encoding="utf8"))
    limit = int(os.environ.get("EVAL_LIMIT", "0"))
    out = os.path.join(CACHE, f"{which}_pool{'_smoke' if limit else ''}.npz")
    state = {}
    if os.path.exists(out):
        z = np.load(out, allow_pickle=True)
        state = {n: (e, h, i, int(t), float(f)) for n, e, h, i, t, f in zip(z["names"], z["emb"], z["hist"], z["idx"], z["total"], z["fps"])}
    todo = [m["video"] for m in meta if m["video"] not in state and os.path.exists(os.path.join(vdir, m["video"]))]
    # seeded random order: any prefix of the run is a class-balanced sample, so the run can be stopped (and resumed) at any time
    todo = [todo[i] for i in np.random.RandomState(0).permutation(len(todo))]
    if limit:
        todo = todo[:limit]
    print(f"{which}: {len(state)} cached, {len(todo)} to do, {len(meta)} total", flush=True)
    eng = SearchEngine()
    print("model:", eng.model_id, flush=True)
    n_pool = POOL[which]
    t0 = time.time()

    def save():
        names = sorted(state)
        np.savez(out, names=np.array(names), emb=np.stack([state[n][0] for n in names]), hist=np.stack([state[n][1] for n in names]),
                 idx=np.stack([state[n][2] for n in names]), total=np.array([state[n][3] for n in names]),
                 fps=np.array([state[n][4] for n in names]))

    for k, name in enumerate(todo):
        frames, hists, idx, total, fps = read_pool(os.path.join(vdir, name), n_pool)
        if len(frames) < n_pool:                           # pad (rare: short/corrupt clip) by repeating the last frame
            while len(frames) < n_pool:
                frames.append(frames[-1]); hists = np.vstack([hists, hists[-1:]]); idx.append(idx[-1])
        embs = eng.get_image_embeddings([to_pil(f) for f in frames])
        if any(e is None for e in embs):
            print("skip (embed failed)", name, flush=True); continue
        state[name] = (np.stack(embs).astype("float32"), hists, np.array(idx[:n_pool]), total, fps)
        if (k + 1) % 20 == 0 or k + 1 == len(todo):
            save()
            rate = (k + 1) / (time.time() - t0)
            print(f"  {k + 1}/{len(todo)}  {rate * 60:.1f} videos/min  eta {(len(todo) - k - 1) / rate / 60:.1f} min", flush=True)
    save()
    print("DONE", len(state), flush=True)


if __name__ == "__main__":
    main()
