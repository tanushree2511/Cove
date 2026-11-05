"""Experiment 7 - order stability of incremental face clustering.

Q1  How much does each method's result change when the SAME faces arrive in a different order?
    20 shuffled orders per method; we report quality (B-Cubed F1, ARI) mean +- std and the mean pairwise
    ARI between the partitions of different orders ("order agreement"; 1.0 = identical result for every order).
Q2  Incremental use: faces arrive in 10 batches (library growth). Per-batch update cost of the incremental methods
    vs. re-clustering from scratch, and final quality.

All methods use the same cached buffalo_s ArcFace embeddings as Experiment 1. Our method's hyper-parameters are tuned
on the TUNING split only; baselines use the thresholds already tuned in exp1_clustering.json.
Run:  python evaluation/exp7_order_stability.py [quick]
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, load_json, save_json, be_nice, plan_parallelism  # noqa: E402
be_nice()
from exp1_cluster import agglomerative, evaluate, first_leader, make_splits, ours_two_stage  # noqa: E402

from engines.stable_cluster import StableIncrementalClusterer  # noqa: E402

QUICK = len(sys.argv) > 1 and sys.argv[1] == "quick"
N_ORDERS = 5 if QUICK else 20
WORKERS, _ = plan_parallelism(mem_per_worker_gb=1.6, threads_per_worker=1)  # single-threaded clustering workers


def load_raw():
    d = np.load(os.path.join(CACHE, "lfw_faces.npz"), allow_pickle=True)
    E = d["emb"].astype("float32")
    norms = np.linalg.norm(E, axis=1)
    X = E / norms[:, None]
    paths = d["paths"].tolist()
    ident = np.array([p.replace("\\", "/").split("/")[0] for p in paths])
    return paths, X, norms, ident


def stable(X, norms, cfg, batch=None):
    c = StableIncrementalClusterer(link_threshold=cfg["link"], min_neighbors=cfg["m"],
                                   merge_threshold=cfg["merge"], quality_min=cfg["qmin"], dim=X.shape[1], attach_threshold=cfg.get("attach"),
                                   weak_threshold=cfg.get("weak"), support=cfg.get("support", 3))
    b = batch or len(X)
    for s in range(0, len(X), b):
        c.add(X[s:s + b], norms[s:s + b])
    return c.labels()


def tune_stable(X, norms, y):
    rows = []
    for link in (0.40, 0.45, 0.50, 0.55):
        for m in (1, 2, 3):
            for merge in (None, 0.30, 0.35, 0.40):
                for qpct in (None, 5, 10):
                    qmin = None if qpct is None else float(np.percentile(norms, qpct))
                    cfg = {"link": link, "m": m, "merge": merge, "qpct": qpct, "qmin": qmin}
                    r = evaluate(stable(X, norms, cfg), y)
                    rows.append({**cfg, **r})
    best = max(rows, key=lambda r: r["B3_F1"])
    return best, rows


def run_method(method, Xp, Np, cfg, fl_thr):
    if method == "first_leader":
        return first_leader(Xp, fl_thr)
    if method == "two_stage":
        return ours_two_stage(Xp, 0.45, 0.40)
    if method == "stable":
        return stable(Xp, Np, cfg)
    if method == "stable_b100":
        return stable(Xp, Np, cfg, batch=100)
    raise ValueError(method)


_W = {}


def _init_worker(idx):
    # one core per worker: the parallelism is across input orders, not inside a run
    from common import single_thread_worker
    single_thread_worker()
    _, X, norms, _ = load_raw()
    _W["X"], _W["N"] = X[idx], norms[idx]


def _one_order(args):
    method, sd, cfg, fl_thr = args
    X, N = _W["X"], _W["N"]
    perm = np.random.RandomState(1000 + sd).permutation(len(X))
    t = time.perf_counter()
    lab = run_method(method, X[perm], N[perm], cfg, fl_thr)
    sec = time.perf_counter() - t
    back = np.empty(len(X), dtype=int)
    back[perm] = lab
    return sd, back, sec


def shuffled(name, method, idx, y, n_orders, cfg, fl_thr, pool):
    rows, preds = [], []
    for sd, back, sec in sorted(pool.map(_one_order, [(method, sd, cfg, fl_thr) for sd in range(n_orders)])):
        m = evaluate(back, y)
        m["seconds"] = sec
        rows.append(m)
        preds.append(back)
    agree = [adjusted_rand_score(preds[i], preds[j]) for i in range(len(preds)) for j in range(i + 1, len(preds))]
    out = {k: {"mean": float(np.mean([r[k] for r in rows])), "std": float(np.std([r[k] for r in rows])),
               "min": float(np.min([r[k] for r in rows])), "max": float(np.max([r[k] for r in rows]))} for k in rows[0]}
    out["order_agreement_ARI"] = {"mean": float(np.mean(agree)), "min": float(np.min(agree))}
    print(f"  {name:<44} F1={out['B3_F1']['mean']:.4f}±{out['B3_F1']['std']:.4f} "
          f"ARI={out['ARI']['mean']:.4f}±{out['ARI']['std']:.4f} agree={out['order_agreement_ARI']['mean']:.4f} "
          f"(min {out['order_agreement_ARI']['min']:.4f}) t={out['seconds']['mean']:.1f}s", flush=True)
    return out


def streaming(X, norms, y, cfg, fl_thr, n_batches=10, seed=7):
    """Library growth: faces arrive in n_batches. Incremental methods update; 'recluster' baselines start over."""
    n = len(X)
    perm = np.random.RandomState(seed).permutation(n)
    Xp, Np, yp = X[perm], norms[perm], y[perm]
    edges = np.linspace(0, n, n_batches + 1).astype(int)
    res = {"Ours (incremental)": [], "Two-stage (re-cluster each batch)": [], "Agglomerative (re-cluster each batch)": []}
    c = StableIncrementalClusterer(link_threshold=cfg["link"], min_neighbors=cfg["m"],
                                   merge_threshold=cfg["merge"], quality_min=cfg["qmin"], dim=X.shape[1], attach_threshold=cfg.get("attach"),
                                   weak_threshold=cfg.get("weak"), support=cfg.get("support", 3))
    prev_ours = None
    for b in range(n_batches):
        lo, hi = edges[b], edges[b + 1]
        t = time.perf_counter(); c.add(Xp[lo:hi], Np[lo:hi]); lab = c.labels(); s1 = time.perf_counter() - t
        # how many previously co-clustered pairs survive the update (stability of what the user already saw)
        keep = None
        if prev_ours is not None:
            keep = float(adjusted_rand_score(prev_ours, lab[:len(prev_ours)]))
        prev_ours = lab
        res["Ours (incremental)"].append({"faces": int(hi), "update_s": s1, "B3_F1": evaluate(lab, yp[:hi])["B3_F1"],
                                          "prev_partition_ARI": keep})
        t = time.perf_counter(); lab2 = ours_two_stage(Xp[:hi], 0.45, 0.40); s2 = time.perf_counter() - t
        res["Two-stage (re-cluster each batch)"].append({"faces": int(hi), "update_s": s2, "B3_F1": evaluate(lab2, yp[:hi])["B3_F1"]})
        if hi <= 6000 or not QUICK:
            t = time.perf_counter(); lab3 = agglomerative(Xp[:hi], 1.0 - 0.325); s3 = time.perf_counter() - t
            res["Agglomerative (re-cluster each batch)"].append({"faces": int(hi), "update_s": s3, "B3_F1": evaluate(lab3, yp[:hi])["B3_F1"]})
        print(f"  batch {b + 1}/{n_batches} faces={hi} ours={s1:.2f}s two-stage={s2:.2f}s", flush=True)
    return res


def main():
    paths, X, norms, ident = load_raw()
    splits, _ = make_splits(paths)
    tuned = load_json("exp1_clustering.json")["tuning"]["tuned_threshold"]
    fl_thr = tuned["First-Leader (original)"]
    ag_thr = tuned["Agglomerative (average)"]

    ti, ty = splits["tune"]
    best, grid = tune_stable(X[ti], norms[ti], ty)
    print("[tune] best:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in best.items()}, flush=True)
    cfg = {k: best[k] for k in ("link", "m", "merge", "qpct")}
    cfg["qmin"] = None if cfg["qpct"] is None else float(np.percentile(norms[ti], cfg["qpct"]))

    methods = {
        "First-Leader (single pass)": "first_leader",
        "Two-stage (current Cove, 0.45/0.40)": "two_stage",
        "Ours: order-stable incremental": "stable",
        "Ours, added 1 batch of 100 at a time": "stable_b100",
    }
    out = {"config": cfg, "tuning_grid": grid, "n_orders": N_ORDERS, "workers": WORKERS,
           "timing_note": f"shuffled-order runs execute {WORKERS} in parallel (1 thread each); use the streaming section for timing",
           "thresholds": {"first_leader": fl_thr, "agglomerative": ag_thr}}
    for split_name, (idx, y) in (("test_split", splits["test"]), ("full_lfw", (np.arange(len(X)), ident))):
        if QUICK and split_name == "full_lfw":
            continue
        print(f"[{split_name}] {len(idx)} faces, {len(np.unique(y))} identities", flush=True)
        Xs = X[idx]
        with ProcessPoolExecutor(WORKERS, initializer=_init_worker, initargs=(np.asarray(idx),)) as pool:
            table = {name: shuffled(name, m, idx, y, N_ORDERS, cfg, fl_thr, pool) for name, m in methods.items()}
        t = time.perf_counter(); lab = agglomerative(Xs, 1.0 - ag_thr); sec = time.perf_counter() - t
        m = evaluate(lab, y); m["seconds"] = sec
        table["Agglomerative (batch reference, order-free)"] = {k: {"mean": v, "std": 0.0} for k, v in m.items()}
        print(f"  {'Agglomerative (batch reference)':<44} F1={m['B3_F1']:.4f} ARI={m['ARI']:.4f} t={sec:.1f}s", flush=True)
        out[split_name] = table

    print("[streaming] full LFW in 10 batches" if not QUICK else "[streaming] test split in 10 batches", flush=True)
    sidx, sy = (splits["test"] if QUICK else (np.arange(len(X)), ident))
    out["streaming"] = streaming(X[sidx], norms[sidx], sy, cfg, fl_thr)
    save_json("exp7_order_stability_quick.json" if QUICK else "exp7_order_stability.json", out)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
