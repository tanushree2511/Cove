"""Experiment 1 - facial identity clustering on LFW (+ LFW verification as the ArcFace-embedding sanity check).

Same L2-normalised 512-D embeddings (buffalo_s ArcFace-trained recogniser) for every method:
  * First-Leader        the original greedy single-pass method (compare to the first member of each cluster)
  * Ours (two-stage)    what the app runs today: First-Leader pass + average-linkage merge of cluster centroids
                        (cove/engines/cluster_engine.py ClusterEngine, min_cluster_size=1 as used by the indexing job)
  * DBSCAN              cosine metric (min_samples 2; noise points become singletons)
  * Agglomerative       average linkage, cosine
Splits are fixed (seed 0) and DISJOINT: thresholds are tuned on the tuning split only and reported on the test split.
"""
import contextlib
import io
import os
import sys
import time

import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, FIGS, nrm, save_json  # noqa: E402

from engines.cluster_engine import ClusterEngine  # noqa: E402

SEED = 0
N_SHUFFLES = 5
LFW = os.path.join(DS, "lfw", "lfw_funneled")


# ------------------------------------------------------------------ data / splits
def load_embeddings():
    d = np.load(os.path.join(CACHE, "lfw_faces.npz"), allow_pickle=True)
    paths = d["paths"].tolist()
    return paths, nrm(d["emb"]), d["missing"].tolist()


def make_splits(paths):
    ident = np.array([p.replace("\\", "/").split("/")[0] for p in paths])
    by_id = {}
    for i, n in enumerate(ident):
        by_id.setdefault(n, []).append(i)
    multi = sorted(n for n, v in by_id.items() if len(v) >= 2)
    single = sorted(n for n, v in by_id.items() if len(v) == 1)
    rng = np.random.RandomState(SEED)
    multi = [multi[i] for i in rng.permutation(len(multi))]
    single = [single[i] for i in rng.permutation(len(single))]

    def take(ids, singles):
        idx = []
        for n in ids:
            idx += sorted(by_id[n])[:5]                      # up to 5 images per identity
        for n in singles:
            idx += by_id[n]
        return np.array(idx), ident[np.array(idx)]

    tune = take(multi[:200], single[:300])
    test = take(multi[200:800], single[300:1300])
    return {"tune": tune, "test": test}, {"identities_multi": len(multi), "identities_single": len(single)}


# ------------------------------------------------------------------ metrics
def contingency(pred, truth):
    p = np.unique(pred, return_inverse=True)[1]
    t = np.unique(truth, return_inverse=True)[1]
    M = np.zeros((p.max() + 1, t.max() + 1), dtype=np.int64)
    np.add.at(M, (p, t), 1)
    return M, p, t


def bcubed(pred, truth):
    M, p, t = contingency(pred, truth)
    csize, lsize = M.sum(1), M.sum(0)
    inter = M[p, t].astype(float)
    prec = (inter / csize[p]).mean()
    rec = (inter / lsize[t]).mean()
    f1 = 2 * prec * rec / max(prec + rec, 1e-12)
    return float(prec), float(rec), float(f1)


def evaluate(pred, truth):
    pr, rc, f1 = bcubed(pred, truth)
    return {"B3_P": pr, "B3_R": rc, "B3_F1": f1,
            "ARI": float(adjusted_rand_score(truth, pred)),
            "NMI": float(normalized_mutual_info_score(truth, pred)),
            "clusters": int(len(np.unique(pred)))}


# ------------------------------------------------------------------ methods (all take unit vectors X, return labels)
def first_leader(X, thr):
    import faiss
    eng = ClusterEngine(min_cluster_size=1, threshold=thr, merge_threshold=None)
    with contextlib.redirect_stdout(io.StringIO()):
        return eng._greedy_leader(X.copy())


def ours_two_stage(X, thr=0.45, merge=0.40):
    eng = ClusterEngine(min_cluster_size=1, threshold=thr, merge_threshold=merge)
    with contextlib.redirect_stdout(io.StringIO()):
        return eng.fit_predict(X.copy())


def dbscan(X, eps, min_samples=2):
    lab = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine", n_jobs=1).fit_predict(X)
    noise = lab == -1
    lab = lab.copy()
    lab[noise] = lab.max() + 1 + np.arange(noise.sum())      # every noise point is its own cluster
    return lab


def agglomerative(X, dist_thr, linkage="average"):
    return AgglomerativeClustering(n_clusters=None, metric="cosine", linkage=linkage, distance_threshold=dist_thr).fit_predict(X)


METHODS = {
    # name: (function(X, t), threshold axis expressed as cosine SIMILARITY)
    "First-Leader (original)": lambda X, s: first_leader(X, s),
    "Ours (two-stage, merge 0.40)": lambda X, s: ours_two_stage(X, s, 0.40),
    "DBSCAN (min_samples=2)": lambda X, s: dbscan(X, 1.0 - s, 2),
    "Agglomerative (average)": lambda X, s: agglomerative(X, 1.0 - s),
}
GRID = np.round(np.arange(0.20, 0.701, 0.025), 3)


def timed(fn, X, s):
    t = time.perf_counter()
    lab = fn(X, s)
    return lab, time.perf_counter() - t


def run_shuffled(fn, X, truth, s, seeds=range(N_SHUFFLES)):
    rows, preds = [], []
    n = len(X)
    for sd in seeds:
        perm = np.random.RandomState(100 + sd).permutation(n)
        lab, sec = timed(fn, X[perm], s)
        inv = np.empty(n, dtype=int); inv[perm] = np.arange(n)
        back = lab[inv]                                     # labels in the original order
        m = evaluate(back, truth); m["seconds"] = sec
        rows.append(m); preds.append(back)
    agree = [adjusted_rand_score(preds[i], preds[j]) for i in range(len(preds)) for j in range(i + 1, len(preds))]
    return rows, float(np.mean(agree)) if agree else 1.0


def summarise(rows):
    keys = rows[0].keys()
    return {k: {"mean": float(np.mean([r[k] for r in rows])), "std": float(np.std([r[k] for r in rows]))} for k in keys}


# ------------------------------------------------------------------ verification (sanity check of the embeddings)
def lfw_verification(paths, X):
    idx = {p.replace("\\", "/"): i for i, p in enumerate(paths)}
    lines = open(os.path.join(LFW, "pairs.txt")).read().split("\n")
    folds_n, per = map(int, lines[0].split())
    pairs, k = [], 1
    for f in range(folds_n):
        for same in (1, 0):
            for _ in range(per):
                t = lines[k].split(); k += 1
                if same:
                    a = f"{t[0]}/{t[0]}_{int(t[1]):04d}.jpg"; b = f"{t[0]}/{t[0]}_{int(t[2]):04d}.jpg"
                else:
                    a = f"{t[0]}/{t[0]}_{int(t[1]):04d}.jpg"; b = f"{t[2]}/{t[2]}_{int(t[3]):04d}.jpg"
                pairs.append((f, a, b, same))
    sims, lab, fold = [], [], []
    skipped = 0
    for f, a, b, s in pairs:
        if a in idx and b in idx:
            sims.append(float(X[idx[a]] @ X[idx[b]])); lab.append(s); fold.append(f)
        else:
            skipped += 1                                    # no face detected -> counted as an error below
    sims, lab, fold = np.array(sims), np.array(lab), np.array(fold)
    accs = []
    for f in range(folds_n):
        tr, te = fold != f, fold == f
        cand = np.unique(sims[tr])
        best = cand[np.argmax([((sims[tr] >= c) == lab[tr]).mean() for c in cand[:: max(1, len(cand) // 800)]])] if len(cand) else 0.3
        cand = cand[:: max(1, len(cand) // 800)]
        best = cand[np.argmax([((sims[tr] >= c) == lab[tr]).mean() for c in cand])]
        accs.append(((sims[te] >= best) == lab[te]).sum())
    total_per_fold = len(pairs) / folds_n
    acc = float(np.sum(accs) / len(pairs))                  # undetected pairs count as wrong
    return {"pairs": len(pairs), "evaluated": int(len(sims)), "no_face_pairs": int(skipped),
            "accuracy_10fold_all_pairs": acc,
            "accuracy_10fold_detected_only": float(np.sum(accs) / max(len(sims), 1))}


def plot_sensitivity(sens):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.4))
    for name, pts in sens.items():
        xs = [p["thr"] for p in pts]
        m = np.array([p["B3_F1"]["mean"] for p in pts]); sd = np.array([p["B3_F1"]["std"] for p in pts])
        ax[0].plot(xs, m, marker="o", ms=3, label=name); ax[0].fill_between(xs, m - sd, m + sd, alpha=0.2)
        a_ = np.array([p["ARI"]["mean"] for p in pts])
        ax[1].plot(xs, a_, marker="o", ms=3, label=name)
    for a_, t in zip(ax, ("B-Cubed F1", "Adjusted Rand Index")):
        a_.set_xlabel("cosine-similarity threshold (DBSCAN / Agglomerative: 1 - distance)"); a_.set_ylabel(t); a_.grid(alpha=0.3)
        a_.set_ylim(0.0, 1.01)
    ax[0].set_title("Threshold sensitivity, LFW test split (mean ± std over 5 input orders)", fontsize=9)
    ax[1].set_title("Same sweep, Adjusted Rand Index", fontsize=9)
    ax[0].legend(fontsize=7, loc="lower left")
    plt.tight_layout(); plt.savefig(os.path.join(FIGS, "exp1_threshold_sensitivity.png"), dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ main
def main():
    paths, X, missing = load_embeddings()
    print("embedded:", len(paths), "no face:", len(missing), flush=True)
    splits, info = make_splits(paths)
    out = {"embedding": "InsightFace buffalo_s (ArcFace-trained MobileFaceNet w600k_mbf, 512-D), largest face per image",
           "lfw_images": len(paths) + len(missing), "faces_embedded": len(paths), "images_without_face": len(missing),
           "splits": {k: {"images": int(len(v[0])), "identities": int(len(np.unique(v[1])))} for k, v in splits.items()},
           **info}
    out["verification"] = lfw_verification(paths, X)
    print("verification:", out["verification"], flush=True)

    Xt, yt = X[splits["tune"][0]], splits["tune"][1]
    Xs, ys = X[splits["test"][0]], splits["test"][1]

    # 1. tune thresholds on the TUNING split only (single input order)
    best = {}
    tuning = {}
    for name, fn in METHODS.items():
        rows = []
        for s in GRID:
            lab = fn(Xt, s)
            m = evaluate(lab, yt); m["thr"] = float(s); rows.append(m)
        tuning[name] = rows
        b = max(rows, key=lambda r: r["B3_F1"])
        best[name] = b["thr"]
        print(f"[tune] {name:<32} best thr={b['thr']:.3f}  B3-F1={b['B3_F1']:.4f}", flush=True)
    # the production default of the two-stage method (no tuning involved), plus a full leader x merge grid on tuning
    grid2 = []
    for t1 in (0.35, 0.40, 0.45, 0.50, 0.55):
        for t2 in (0.30, 0.35, 0.40, 0.45):
            m = evaluate(ours_two_stage(Xt, t1, t2), yt); m.update(leader=t1, merge=t2); grid2.append(m)
    bg = max(grid2, key=lambda r: r["B3_F1"])
    print("[tune] two-stage grid best:", {k: round(v, 4) if isinstance(v, float) else v for k, v in bg.items()}, flush=True)
    out["tuning"] = {"per_method": tuning, "tuned_threshold": best, "two_stage_grid": grid2, "two_stage_grid_best": bg}

    # 2. TEST split: main comparison table at the tuned thresholds (5 shuffled input orders)
    table = {}
    configs = {n: (METHODS[n], best[n]) for n in METHODS}
    configs["Ours (two-stage, production defaults 0.45/0.40)"] = (lambda X, s: ours_two_stage(X, 0.45, 0.40), None)
    configs[f"Ours (two-stage, tuned {bg['leader']}/{bg['merge']})"] = (lambda X, s, a=bg['leader'], b=bg['merge']: ours_two_stage(X, a, b), None)
    for name, (fn, s) in configs.items():
        rows, agree = run_shuffled(fn, Xs, ys, s)
        table[name] = {"threshold": s, "metrics": summarise(rows), "order_agreement_ARI": agree}
        mm = table[name]["metrics"]
        print(f"[test] {name:<52} F1={mm['B3_F1']['mean']:.4f}±{mm['B3_F1']['std']:.4f} ARI={mm['ARI']['mean']:.4f} NMI={mm['NMI']['mean']:.4f} "
              f"t={mm['seconds']['mean']:.2f}s agree={agree:.4f}", flush=True)
    out["test_table"] = table

    # 3. threshold sensitivity on the TEST split (5 shuffles per point) - drives the paper graph
    sens = {}
    for name, fn in METHODS.items():
        pts = []
        for s in GRID:
            rows, agree = run_shuffled(fn, Xs, ys, s)
            sm = summarise(rows)
            pts.append({"thr": float(s), **{k: sm[k] for k in ("B3_P", "B3_R", "B3_F1", "ARI", "NMI", "clusters", "seconds")}, "agree": agree})
        sens[name] = pts
        print(f"[sens] {name} done", flush=True)
    # second curve for the two-stage method: sweep the merge threshold at the production leader threshold (0.45)
    pts = []
    for s in GRID:
        rows, agree = run_shuffled(lambda X, m: ours_two_stage(X, 0.45, m), Xs, ys, s)
        sm = summarise(rows)
        pts.append({"thr": float(s), **{k: sm[k] for k in ("B3_P", "B3_R", "B3_F1", "ARI", "NMI", "clusters", "seconds")}, "agree": agree})
    sens["Ours (two-stage, sweep of merge thr @ leader 0.45)"] = pts
    out["sensitivity"] = sens
    save_json("exp1_clustering.json", out)

    plot_sensitivity(sens)
    print("DONE", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "plot":
        from common import load_json
        plot_sensitivity(load_json("exp1_clustering.json")["sensitivity"])
    else:
        main()
