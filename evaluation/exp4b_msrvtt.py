"""Experiment 4 (literature comparison): text->video retrieval on MSR-VTT 1k-A (1,000 test videos, 1 caption each), the protocol of
CLIP4Clip / Frozen in Time, measured with OUR video embeddings so the published numbers can be put next to ours.

Frames come from a 15-frame pool per video (exp34_embed.py msrvtt):  middle frame = pool[7];  uniform-12 mean = CLIP4Clip's
frame count (zero-shot CLIP, mean pooling, NO fine-tuning);  ours = 14 positions + histogram filter;  ours deployed = + adaptive CLIP frames.
Text: the app's video-search encoding (caption blended with 'a photo of <caption>') and, as the plain CLIP baseline, the raw caption.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, nrm, save_json  # noqa: E402

USERDATA = os.path.join(CACHE, "userdata")
os.makedirs(USERDATA, exist_ok=True)
os.environ["COVE_USER_DATA"] = USERDATA

from core.video_processor import pick_evenly  # noqa: E402
from exp34_analyze import redundancy_filter  # noqa: E402

N_POOL, MID = 15, 7


def main():
    z = np.load(os.path.join(CACHE, "msrvtt_pool.npz"), allow_pickle=True)
    names = z["names"].tolist()
    E, H = z["emb"].astype("float32"), z["hist"].astype("float32")
    dur = (z["total"] / np.maximum(z["fps"], 1e-6)).astype(float)
    meta = {m["video"]: m for m in json.load(open(os.path.join(DS, "msrvtt", "msrvtt_test_1k.json"), encoding="utf8"))}
    caps = [meta[n]["caption"] for n in names]
    N = len(names)
    print(f"MSR-VTT videos with embeddings: {N}", flush=True)

    from config.vision_config import CONFIG
    profile = CONFIG.runtime_profile
    idx = lambda n, c: pick_evenly(list(range(n)), c)
    sel = {"Middle frame only (1)": [[MID]] * N, "Uniform 12 frames (CLIP4Clip frame count)": [idx(N_POOL, 12)] * N,
           "Uniform 15 frames (dense reference)": [list(range(N_POOL))] * N}
    kept, dep = [], []
    for i in range(N):
        k = [j for j in redundancy_filter(H[i])]
        kept.append(k)
        n_clip = profile.frames_for_video(dur[i]) if profile else len(k)
        dep.append([k[j] for j in idx(len(k), min(n_clip, len(k)))])
    sel["Ours: 14 pos + redundancy filter"] = kept
    sel["Ours deployed (filter + adaptive CLIP frames)"] = dep

    from core.embedder import encode_query, _get_engine
    eng = _get_engine()
    T = {"app video-search text (caption + 'a photo of')": np.stack([encode_query(c) for c in caps]),
         "plain CLIP text (raw caption)": nrm(np.stack([eng._encode_single_text(c) for c in caps]))}

    out = {"videos": N, "queries": N, "frames_note": "15-frame pool per video", "results": {}}
    for sname, sels in sel.items():
        V = np.stack([nrm(E[i][s].mean(0)) for i, s in enumerate(sels)])
        for tname, Q in T.items():
            S = Q @ V.T
            gt = S[np.arange(N), np.arange(N)]
            ranks = (S > gt[:, None]).sum(1) + 1
            out["results"][f"{sname} | {tname}"] = {"R@1": float((ranks <= 1).mean()), "R@5": float((ranks <= 5).mean()), "R@10": float((ranks <= 10).mean()),
                                                     "MdR": float(np.median(ranks)), "MnR": float(ranks.mean()), "MRR": float((1 / ranks).mean()),
                                                     "frames_mean": float(np.mean([len(s) for s in sels]))}
            r = out["results"][f"{sname} | {tname}"]
            print(f"{sname:<48} | {tname[:28]:<28} R@1={r['R@1']:.3f} R@5={r['R@5']:.3f} R@10={r['R@10']:.3f} MdR={r['MdR']:.0f}", flush=True)
    save_json("exp4b_msrvtt.json", out)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
