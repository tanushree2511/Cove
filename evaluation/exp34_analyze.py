"""Experiments 3 + 4, step 2: quality of every frame-sampling strategy on the 1,000-video UCF101 subset.

Video embedding = mean of the selected frames' CLIP embeddings (L2-normalised) for every strategy except 'middle frame'.
  dense reference            all 25 pool frames (~3.5 frames/s on a 7 s clip)
  uniform 4 / 8 / 14 / 20    N evenly spaced pool frames
  middle frame               the exact middle frame (Exp. 4 baseline)
  ours: 14-pos + filter      14 uniform positions, then the app's histogram redundancy filter (corr < 0.95, keep >= 4); mean of ALL kept frames
  ours deployed              as above, then CLIP only on `frames_for_video()` of the kept frames (the hardware-adaptive count the app uses)
Retrieval: 101 action-description queries (the app's natural-language prompt for each UCF101 class) against the 1,000 videos; a video is
relevant when its UCF101 class matches.   Action accuracy: the app's zero-shot tagger (180-label taxonomy) vs the UCF101 ground truth.
"""
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, ROOT, nrm, save_json  # noqa: E402

# isolate the app's DB / label cache from the user's real library, but keep the measured hardware profile
USERDATA = os.path.join(CACHE, "userdata")
os.makedirs(USERDATA, exist_ok=True)
os.environ["COVE_USER_DATA"] = USERDATA
_hp = os.path.join(os.environ.get("APPDATA", ""), "Cove", "hardware_profile.json")
if os.path.exists(_hp):
    import shutil
    shutil.copy2(_hp, USERDATA)          # always the CURRENT measured profile (a stale copy once carried a load-skewed choice)

from core.video_processor import pick_evenly  # noqa: E402
from core.label_taxonomy import LABEL_DEFINITIONS  # noqa: E402

N_POOL = 25
MID = 12


def redundancy_filter(hists, thr=0.95, min_keep=4):
    """Exactly the filter in videoModules/core/video_processor.py::extract_frames (fast_mode)."""
    n = len(hists)
    if n <= min_keep:
        return list(range(n))
    sel = [0]
    for i in range(1, n):
        if cv2.compareHist(hists[i], hists[sel[-1]], cv2.HISTCMP_CORREL) < thr:
            sel.append(i)
    if len(sel) < min_keep:
        remaining = [x for x in range(n) if x not in sel]
        remaining.sort(key=lambda x: min(cv2.compareHist(hists[x], hists[s], cv2.HISTCMP_CORREL) for s in sel))
        while len(sel) < min_keep and remaining:
            sel.append(remaining.pop(0))
    return sorted(sel)


def pick_idx(n_pool, count):
    """indices chosen by the app's pick_evenly()"""
    return pick_evenly(list(range(n_pool)), count)


def build_configs(E, H, durations, profile):
    """Return {config: (video_embeddings [N,512], frames_per_video [N])}."""
    N = len(E)
    cfg = {}

    def mean_of(sel_per_video):
        V = np.stack([nrm(E[i][sel].mean(0)) for i, sel in enumerate(sel_per_video)])
        return V, np.array([len(s) for s in sel_per_video], dtype=float)

    cfg["Dense reference (25 frames)"] = mean_of([list(range(N_POOL))] * N)
    for n in (4, 8, 14, 20):
        cfg[f"Uniform {n} frames"] = mean_of([pick_idx(N_POOL, n)] * N)
    cfg["Middle frame only (1)"] = mean_of([[MID]] * N)
    u14 = pick_idx(N_POOL, 14)
    kept_all, deployed = [], []
    for i in range(N):
        keep = [u14[j] for j in redundancy_filter(H[i][u14])]
        kept_all.append(keep)
        n_clip = profile.frames_for_video(durations[i]) if profile is not None else len(keep)
        deployed.append([keep[j] for j in pick_idx(len(keep), min(n_clip, len(keep)))])
    cfg["Ours: 14 pos + redundancy filter"] = mean_of(kept_all)
    cfg["Ours deployed (filter + adaptive CLIP frames)"] = mean_of(deployed)
    return cfg, kept_all, deployed


def retrieval_metrics(S, rel):
    """S [Q,N] similarities, rel [Q,N] bool.  Returns per-query arrays + the aggregate."""
    order = np.argsort(-S, axis=1)
    hits = np.take_along_axis(rel, order, axis=1)
    nrel = rel.sum(1)
    out = {}
    per = {}
    for k in (1, 5, 10):
        h = hits[:, :k]
        per[f"Hit@{k}"] = h.any(1).astype(float)                          # >= 1 relevant video in the top-k (standard text->video R@k)
        per[f"Recall@{k}"] = h.sum(1) / nrel                               # fraction of the relevant videos retrieved
    per["P@10"] = hits[:, :10].sum(1) / 10.0
    first = hits.argmax(1) + 1
    per["MRR"] = 1.0 / first
    cum = np.cumsum(hits, axis=1)
    ranks = np.arange(1, hits.shape[1] + 1)
    per["mAP"] = ((cum / ranks) * hits).sum(1) / nrel
    return per


def boot_ci(x, n=2000, seed=0):
    rng = np.random.RandomState(seed)
    idx = rng.randint(0, len(x), (n, len(x)))
    m = x[idx].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    import json
    z = np.load(os.path.join(CACHE, "ucf_pool.npz"), allow_pickle=True)
    names = z["names"].tolist()
    E, H = z["emb"].astype("float32"), z["hist"].astype("float32")
    dur = (z["total"] / np.maximum(z["fps"], 1e-6)).astype(float)
    meta = {m["video"]: m["label"] for m in json.load(open(os.path.join(DS, "ucf101", "ucf101_1000.json")))}
    classes = [l.split()[1] for l in open(os.path.join(DS, "ucf101", "splits", "ucfTrainTestlist", "classInd.txt")).read().split("\n") if l.strip()]
    acts = [k for k, v in LABEL_DEFINITIONS.items() if v["group"] == "human_action"]
    assert len(acts) == len(classes) == 101, (len(acts), len(classes))
    cls2label = dict(zip(classes, acts))
    y = np.array([classes.index(meta[n]) for n in names])
    print(f"videos: {len(names)} | classes present: {len(set(y.tolist()))} | mean duration {dur.mean():.2f}s", flush=True)

    from config.vision_config import CONFIG
    profile = CONFIG.runtime_profile
    print("runtime profile:", profile.describe() if profile else None, "| ips:", getattr(profile, "images_per_second", None), flush=True)
    cfgs, kept_all, deployed = build_configs(E, H, dur, profile)

    # queries: the app's natural-language description for every class, encoded exactly as the app's video search does
    from core.embedder import encode_query, _get_engine
    eng = _get_engine()
    desc = [LABEL_DEFINITIONS[cls2label[c]]["prompts"][1] for c in classes]       # e.g. "a person doing archery"
    short = [LABEL_DEFINITIONS[cls2label[c]]["prompts"][0] for c in classes]      # e.g. "archery"
    Q = {}
    lat = {}
    for tag, qs in (("description", desc), ("class name", short)):
        ts = []
        embs = []
        for q in qs:
            t = time.perf_counter(); embs.append(encode_query(q)); ts.append(time.perf_counter() - t)
        Q[tag] = np.stack(embs); lat[tag] = float(np.mean(ts) * 1000)
    present = sorted(set(y.tolist()))
    rel = np.stack([y == c for c in range(101)])                                    # [101, N]
    keep_q = np.array([rel[c].any() for c in range(101)])

    # search latency (text encode + 1,000-video inner-product search), measured with FAISS like the app
    import faiss
    sample_V = cfgs["Ours: 14 pos + redundancy filter"][0].copy()
    idx = faiss.IndexFlatIP(512); idx.add(sample_V)
    ts = []
    for q in Q["description"]:
        t = time.perf_counter(); idx.search(q[None, :], 10); ts.append(time.perf_counter() - t)
    search_ms = float(np.mean(ts) * 1000)

    # classification
    from core.classifier import get_cached_text_features, LABELS, LOGIT_SCALE, softmax, classify_video
    F = get_cached_text_features()
    truth = np.array([LABELS.index(cls2label[classes[c]]) for c in y])

    out = {"videos": len(names), "classes": len(present), "mean_duration_s": float(dur.mean()), "pool_frames": N_POOL,
           "runtime_profile": profile.describe() if profile else None, "configs": {},
           "query_latency_ms": {"text_encode_description": lat["description"], "faiss_search_1000_videos": search_ms}}
    for name, (V, nfr) in cfgs.items():
        row = {"frames_per_video_mean": float(nfr.mean()), "frame_reduction_vs_dense_pct": float(100 * (1 - nfr.mean() / N_POOL)),
               "frame_reduction_vs_uniform14_pct": float(100 * (1 - nfr.mean() / 14))}
        for qtag in ("description", "class name"):
            S = Q[qtag][keep_q] @ V.T
            per = retrieval_metrics(S, rel[keep_q])
            row[f"retrieval_{qtag}"] = {k: float(v.mean()) for k, v in per.items()}
            row[f"retrieval_{qtag}_ci95"] = {k: boot_ci(per[k]) for k in ("Hit@10", "Recall@10", "mAP", "MRR")}
            if qtag == "description":
                row["_per_query"] = {k: v.tolist() for k, v in per.items()}
        probs = softmax(LOGIT_SCALE * (V @ F.T))
        order = np.argsort(-probs, axis=1)
        row["action_top1"] = float((order[:, 0] == truth).mean())
        row["action_top3"] = float((order[:, :3] == truth[:, None]).any(1).mean())
        tags = [classify_video(v) for v in V]
        row["app_multilabel_contains_truth"] = float(np.mean([LABELS[t] in [s.strip() for s in tg.split(",")] for t, tg in zip(truth, tags)]))
        row["app_labels_per_video"] = float(np.mean([len(tg.split(",")) for tg in tags]))
        out["configs"][name] = row
        r = row["retrieval_description"]
        print(f"{name:<48} frames={nfr.mean():5.2f} Hit@10={r['Hit@10']:.3f} R@10={r['Recall@10']:.3f} MRR={r['MRR']:.3f} mAP={r['mAP']:.3f} "
              f"top1={row['action_top1']:.3f} top3={row['action_top3']:.3f}", flush=True)

    # paired bootstrap over queries: key comparisons for the retrieval claim
    def pq(name, k):
        return np.array(out["configs"][name]["_per_query"][k])
    comp = {}
    rng = np.random.RandomState(1)
    for a, b in (("Ours: 14 pos + redundancy filter", "Uniform 14 frames"), ("Ours: 14 pos + redundancy filter", "Middle frame only (1)"),
                 ("Ours: 14 pos + redundancy filter", "Dense reference (25 frames)"), ("Ours deployed (filter + adaptive CLIP frames)", "Dense reference (25 frames)"),
                 ("Uniform 14 frames", "Middle frame only (1)")):
        for k in ("Hit@10", "mAP"):
            d = pq(a, k) - pq(b, k)
            idx_ = rng.randint(0, len(d), (2000, len(d)))
            m = d[idx_].mean(1)
            comp[f"{a} vs {b} [{k}]"] = {"diff": float(d.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]}
    out["paired_bootstrap"] = comp
    out["kept_frames_distribution"] = {str(k): int(v) for k, v in zip(*np.unique([len(k) for k in kept_all], return_counts=True))}
    save_json("exp34_video_quality.json", out)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
