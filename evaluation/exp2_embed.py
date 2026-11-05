"""Experiment 2, step 1: embeddings for semantic image retrieval on MS COCO val2017 (5,000 images).

  images   the project's SearchEngine (CLIP ViT-B/16, the exact preprocessing + ONNX session the app uses)
  queries  COCO captions; two text encodings of every query:
             baseline  single prompt  -> engine._encode_single_text(caption)         (plain CLIP: one text pass)
             ours      prompt ensemble -> engine.get_text_embedding(caption)           (what /search/text does)
Resumable (checkpoints every 250 images / 1000 queries).   usage: exp2_embed.py images | text [max_ensemble_queries]
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, nrm  # noqa: E402

from engines.search_engine import SearchEngine  # noqa: E402

IMG_DIR = os.path.join(DS, "coco", "images5k")
CAPS = os.path.join(DS, "coco", "annotations", "captions_val2017.json")


def load_coco():
    d = json.load(open(CAPS, encoding="utf8"))
    imgs = sorted(d["images"], key=lambda i: i["id"])
    by_img = {}
    for a in d["annotations"]:
        by_img.setdefault(a["image_id"], []).append(a)
    for v in by_img.values():
        v.sort(key=lambda a: a["id"])
    return imgs, by_img


def embed_images(eng):
    imgs, _ = load_coco()
    out = os.path.join(CACHE, "coco5k_images.npz")
    done = {}
    if os.path.exists(out):
        z = np.load(out, allow_pickle=True)
        done = dict(zip(z["files"].tolist(), z["emb"]))
    todo = [i["file_name"] for i in imgs if i["file_name"] not in done and os.path.exists(os.path.join(IMG_DIR, i["file_name"]))]
    print(f"images: {len(done)} cached, {len(todo)} to embed, {len(imgs)} total", flush=True)
    t0 = time.time()
    step = 50
    for s in range(0, len(todo), step):
        part = todo[s:s + step]
        embs = eng.get_image_embeddings([os.path.join(IMG_DIR, f) for f in part])
        for f, e in zip(part, embs):
            if e is not None:
                done[f] = e
        if (s // step) % 5 == 4 or s + step >= len(todo):
            files = sorted(done)
            np.savez(out, files=np.array(files), emb=np.stack([done[f] for f in files]))
            rate = (s + len(part)) / (time.time() - t0)
            print(f"  {s + len(part)}/{len(todo)}  {rate:.2f} img/s  eta {(len(todo) - s - len(part)) / rate / 60:.1f} min", flush=True)
    print("IMAGES DONE", len(done), flush=True)


def embed_text(eng, max_ensemble):
    imgs, by_img = load_coco()
    queries = []                                                    # (image file, caption id, caption)
    for im in imgs:
        for a in by_img[im["id"]]:
            queries.append((im["file_name"], a["id"], a["caption"].strip()))
    first = {}
    for q in queries:
        first.setdefault(q[0], q)
    primary = [first[i["file_name"]] for i in imgs]                 # one query per image: the 5,000-query primary set
    print(f"{len(queries)} captions, {len(primary)} primary queries", flush=True)

    def run(name, qs, fn, ckpt=500):
        out = os.path.join(CACHE, f"coco5k_text_{name}.npz")
        done = {}
        if os.path.exists(out):
            z = np.load(out, allow_pickle=True)
            done = dict(zip(z["cid"].tolist(), z["emb"]))
        todo = [q for q in qs if q[1] not in done]
        t0 = time.time()
        for k, q in enumerate(todo):
            done[q[1]] = fn(q[2])
            if (k + 1) % ckpt == 0 or k + 1 == len(todo):
                cids = sorted(done)
                np.savez(out, cid=np.array(cids), emb=np.stack([done[c] for c in cids]))
                rate = (k + 1) / (time.time() - t0)
                print(f"  [{name}] {k + 1}/{len(todo)}  {rate:.1f} q/s  eta {(len(todo) - k - 1) / rate / 60:.1f} min", flush=True)
        print(f"[{name}] DONE {len(done)}", flush=True)

    # baseline for ALL 25k captions (cheap: one text pass each); ensemble for the primary 5,000 first, then the rest
    run("single_primary", primary, eng._encode_single_text)
    run("ensemble_primary", primary, eng.get_text_embedding)
    rest = [q for q in queries if q[1] not in {p[1] for p in primary}]
    if max_ensemble > 0:
        rest = rest[:max_ensemble]
        run("single_rest", rest, eng._encode_single_text)
        run("ensemble_rest", rest, eng.get_text_embedding)


if __name__ == "__main__":
    eng = SearchEngine()
    print("model:", eng.model_id, "providers:", eng.img_session.get_providers(), "batch:", eng.batch_size, flush=True)
    what = sys.argv[1] if len(sys.argv) > 1 else "images"
    if what == "images":
        embed_images(eng)
    else:
        embed_text(eng, int(sys.argv[2]) if len(sys.argv) > 2 else 0)
