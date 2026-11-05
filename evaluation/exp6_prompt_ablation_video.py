"""Ablation: prompt ensembling for the VIDEO features (retrieval queries and zero-shot tagging), on the cached UCF101 frame pool.

 retrieval  : app text = caption blended with 'a photo of <caption>' (2 text passes)   vs   the single raw caption (1 pass)
 tagging    : label embedding = mean of every prompt of the label + 'a video of <first prompt>' (the app)   vs   first prompt only
Video embedding = 'Ours: 14 pos + redundancy filter' mean (all kept frames), as in 5.3.
"""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, nrm, save_json
os.environ["COVE_USER_DATA"] = os.path.join(CACHE, "userdata")
from core.label_taxonomy import LABEL_DEFINITIONS
from core.classifier import LABELS, LOGIT_SCALE, softmax
from core.embedder import encode_query, _get_engine
from exp34_analyze import redundancy_filter, pick_idx, N_POOL, retrieval_metrics

z = np.load(os.path.join(CACHE, "ucf_pool.npz"), allow_pickle=True)
names = z["names"].tolist(); E, H = z["emb"].astype("float32"), z["hist"].astype("float32")
meta = {m["video"]: m["label"] for m in json.load(open(os.path.join(DS, "ucf101", "ucf101_1000.json")))}
classes = [l.split()[1] for l in open(os.path.join(DS, "ucf101", "splits", "ucfTrainTestlist", "classInd.txt")).read().split("\n") if l.strip()]
acts = [k for k, v in LABEL_DEFINITIONS.items() if v["group"] == "human_action"]
y = np.array([classes.index(meta[n]) for n in names])
u14 = pick_idx(N_POOL, 14)
V = np.stack([nrm(E[i][[u14[j] for j in redundancy_filter(H[i][u14])]].mean(0)) for i in range(len(names))])
eng = _get_engine()
rel = np.stack([y == c for c in range(101)])
desc = [LABEL_DEFINITIONS[acts[c]]["prompts"][1] for c in range(101)]

out = {"retrieval": {}, "tagging": {}}
for tag, enc, passes in (("app blend (caption + 'a photo of')", lambda q: encode_query(q), 2), ("single raw caption", lambda q: nrm(eng._encode_single_text(q)), 1)):
    t = time.perf_counter(); Q = np.stack([enc(q) for q in desc]); sec = (time.perf_counter() - t) / len(desc)
    per = retrieval_metrics(Q @ V.T, rel)
    out["retrieval"][tag] = {**{k: float(v.mean()) for k, v in per.items()}, "text_passes": passes, "encode_ms_per_query": sec * 1000}
    r = out["retrieval"][tag]; print(f"retrieval {tag:<38} Hit@10={r['Hit@10']:.3f} R@10={r['Recall@10']:.3f} MRR={r['MRR']:.3f} mAP={r['mAP']:.3f} {r['encode_ms_per_query']:.0f} ms", flush=True)

truth = np.array([LABELS.index(acts[c]) for c in y])
def label_feats(fn):
    return nrm(np.stack([nrm(np.mean([nrm(eng._encode_single_text(p)) for p in fn(LABEL_DEFINITIONS[l]["prompts"])], axis=0)) for l in LABELS]))
for tag, fn in (("app: all prompts + 'a video of ...'", lambda ps: ps + [f"a video of {ps[0]}"]), ("all prompts, no 'a video of'", lambda ps: ps), ("first prompt only (no ensemble)", lambda ps: ps[:1])):
    t = time.perf_counter(); Fm = label_feats(fn); sec = time.perf_counter() - t
    probs = softmax(LOGIT_SCALE * (V @ Fm.T)); order = np.argsort(-probs, axis=1)
    out["tagging"][tag] = {"top1": float((order[:, 0] == truth).mean()), "top3": float((order[:, :3] == truth[:, None]).any(1).mean()), "label_encoding_s": sec}
    r = out["tagging"][tag]; print(f"tagging   {tag:<38} top1={r['top1']:.3f} top3={r['top3']:.3f}  (one-time label encoding {sec:.0f}s)", flush=True)
save_json("exp6_prompt_ablation_video.json", out); print("DONE")
