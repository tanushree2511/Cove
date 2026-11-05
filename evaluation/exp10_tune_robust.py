"""Experiment 10 - choose the robust configuration of our method on TUNING data only.

Tuning data: the 30 seed-1 personal libraries (exp8), under every image condition of hard_embed.py (clean, lowres, blur,
jpeg, dark, occlude) plus a 'mixed' library (each photo one random condition; different random draw than exp9's test).
CALFW and CPLFW are NEVER used here - they stay fully held-out for exp9.
Selection rule, fixed in advance: highest mean ARI averaged over the 7 conditions (ARI punishes wrong merges and splits).
Our method is order-invariant, so one order per library is exact.
Output: results/exp10_tuned_config.json
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import be_nice, plan_parallelism, save_json, single_thread_worker, measure_worker_gb, load_json  # noqa: E402
be_nice()
from exp1_cluster import evaluate  # noqa: E402
from exp7_order_stability import load_raw, stable  # noqa: E402
from exp8_personal_libraries import make_libraries  # noqa: E402
from exp9_hard import DEGR, SUFFIX, load_set  # noqa: E402

GRID = [dict(link=l, m=m, attach=a, merge=g, qpct=None, qmin=None)
        for l in (0.40, 0.45, 0.50) for m in (1, 2) for a in (None, 0.30, 0.35, 0.40) for g in (0.35, 0.40, 0.45)]
_D = {}
SHARED = os.path.join(os.path.dirname(__file__), "cache", f"exp10_shared{SUFFIX}.npz")


def build_shared():
    """Build every tuning library once, in the parent, and store it as ONE uncompressed file. Workers memory-map it,
    so all of them share a single copy through the OS page cache instead of each loading every image set."""
    paths, _, _, ident = load_raw()
    libs = make_libraries(ident, seed=1)
    files = [[paths[i].replace("\\", "/") for i in l] for l in libs]
    sets = {k: load_set(f"lfw_{k}") for k in DEGR}
    pos = {k: {p: i for i, p in enumerate(sets[k]["paths"])} for k in DEGR}
    Xs, Ns, ys, conds, bounds = [], [], [], [], [0]

    def add(cond, X, N, y):
        Xs.append(X); Ns.append(N); ys.extend(y); conds.append(cond); bounds.append(bounds[-1] + len(X))
    for k in DEGR:
        for lf in files:
            keep = [pos[k][f] for f in lf if f in pos[k]]
            add(k, sets[k]["X"][keep], sets[k]["N"][keep], [f.split("/")[0] for f in lf if f in pos[k]])
    for li, lf in enumerate(files):
        rng = np.random.RandomState(1900 + li)
        sel = []
        for f in lf:
            k = DEGR[rng.randint(len(DEGR))]
            if f in pos[k]:
                sel.append((k, pos[k][f], f.split("/")[0]))
        add("mixed", np.stack([sets[k]["X"][j] for k, j, _ in sel]), np.array([sets[k]["N"][j] for k, j, _ in sel]), [y for *_, y in sel])
    np.save(SHARED.replace(".npz", "_X.npy"), np.concatenate(Xs).astype("float32"))
    np.savez(SHARED, N=np.concatenate(Ns), y=np.array(ys), conds=np.array(conds), bounds=np.array(bounds))


def _init():
    single_thread_worker()
    d = np.load(SHARED)
    _D["X"] = np.load(SHARED.replace(".npz", "_X.npy"), mmap_mode="r")      # shared, read-only
    _D["N"], _D["y"], _D["conds"], _D["b"] = d["N"], d["y"], d["conds"].tolist(), d["bounds"]
    _D["data"] = [(c, slice(_D["b"][i], _D["b"][i + 1])) for i, c in enumerate(_D["conds"])]


def _eval(cfg):
    per = {}
    for cond, sl in _D["data"]:
        e = evaluate(stable(np.asarray(_D["X"][sl]), _D["N"][sl], cfg), _D["y"][sl])
        per.setdefault(cond, []).append((e["ARI"], e["B3_F1"]))
    by = {c: {"ARI": float(np.mean([a for a, _ in v])), "F1": float(np.mean([f for _, f in v]))} for c, v in per.items()}
    return {**cfg, "per_condition": by, "ARI_mean": float(np.mean([v["ARI"] for v in by.values()])),
            "F1_mean": float(np.mean([v["F1"] for v in by.values()]))}


def main():
    build_shared()
    gb = measure_worker_gb(_eval, GRID[0], initializer=_init)
    workers, _ = plan_parallelism(gb, threads_per_worker=1)
    print(f"{len(GRID)} configurations x 7 conditions x 30 tuning libraries; {gb:.2f} GB/worker -> {workers} workers", flush=True)
    rows = []
    with ProcessPoolExecutor(workers, initializer=_init) as pool:
        for r in pool.map(_eval, GRID):
            rows.append(r)
            print(f"  link {r['link']} m {r['m']} attach {r['attach']} merge {r['merge']}  "
                  f"ARI {r['ARI_mean']:.4f} F1 {r['F1_mean']:.4f}", flush=True)
    best = max(rows, key=lambda r: r["ARI_mean"])
    cfg = {k: best[k] for k in ("link", "m", "attach", "merge", "qpct", "qmin")}
    print("CHOSEN:", cfg, f"tuning ARI {best['ARI_mean']:.4f} F1 {best['F1_mean']:.4f}", flush=True)
    save_json("exp10_tuned_config.json", {"config": cfg, "selected_on": "seed-1 tuning libraries x 7 conditions, max mean ARI",
                                          "previous_config": load_json("exp8_personal_libraries.json")["config"], "grid": rows})
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
