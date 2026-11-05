"""Experiment 8 - order stability on simulated PERSONAL libraries (few people, many photos each).

LFW as a whole is mostly one-photo identities, where insertion order cannot matter. A personal library is the opposite:
a few people (family, friends) with many photos each, plus some strangers. We simulate N_LIB such libraries from LFW:
  * 15-40 "known" people drawn from the identities with >= 10 photos, all their photos (capped at 200 per person)
  * 50-150 "strangers": one photo each from other identities
Every method clusters every library in N_ORDERS shuffled orders. Per library we record the mean F1, the spread
(max - min F1 over orders) and the order agreement (pairwise ARI between orders). Same embeddings and thresholds as exp7.
Run:  python evaluation/exp8_personal_libraries.py [quick]
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, os.path.dirname(__file__))
from common import load_json, save_json, be_nice, plan_parallelism  # noqa: E402
be_nice()
from exp1_cluster import agglomerative, evaluate  # noqa: E402
from exp7_order_stability import load_raw, run_method, stable  # noqa: E402

QUICK = len(sys.argv) > 1 and sys.argv[1] == "quick"
N_LIB = 4 if QUICK else 30
N_ORDERS = 5 if QUICK else 20
WORKERS, _ = plan_parallelism(mem_per_worker_gb=0.7, threads_per_worker=1)  # single-threaded clustering workers
METHODS = {"First-Leader (single pass)": "first_leader",
           "Two-stage (current Cove, 0.45/0.40)": "two_stage",
           "Ours: order-stable incremental": "stable"}


def _tune_one(args):
    c, tune = args
    X, N, ident = _W["X"], _W["N"], _W["ident"]
    r = [evaluate(stable(X[i], N[i], c), ident[i]) for i in tune]
    return {"link": c["link"], "m": c["m"], "merge": c["merge"], "ARI_mean": float(np.mean([e["ARI"] for e in r])),
            "F1_mean": float(np.mean([e["B3_F1"] for e in r])), "ARI_min": float(min(e["ARI"] for e in r))}


def tune_on_libraries(ident, base, pool):
    """Pick our method's parameters on SEPARATE tuning libraries (seed 1, disjoint from the test libraries, seed 0).
    Criterion fixed in advance: highest mean ARI (ARI punishes wrongly merged people). Our method is order-invariant,
    so one order per library is exact. Settings are evaluated in parallel."""
    tune = make_libraries(ident, seed=1)
    grid = [dict(base, link=l, m=m, merge=g) for l in (0.40, 0.45, 0.50, 0.55) for m in (2, 3, 4) for g in (0.35, 0.40, 0.45)]
    rows = list(pool.map(_tune_one, [(c, tune) for c in grid]))
    best = max(rows, key=lambda r: r["ARI_mean"])
    return dict(base, link=best["link"], m=best["m"], merge=best["merge"]), rows


def make_libraries(ident, seed=0):
    rng = np.random.RandomState(seed)
    by_id = {}
    for i, n in enumerate(ident):
        by_id.setdefault(n, []).append(i)
    rich = sorted(n for n, v in by_id.items() if len(v) >= 10)
    others = sorted(n for n, v in by_id.items() if len(v) < 10)
    libs = []
    for _ in range(N_LIB):
        people = rng.choice(rich, rng.randint(15, 41), replace=False)
        idx = []
        for p in people:
            v = by_id[p]
            idx += list(rng.choice(v, min(len(v), 200), replace=False))
        strangers = rng.choice(others, rng.randint(50, 151), replace=False)
        idx += [by_id[s][rng.randint(len(by_id[s]))] for s in strangers]
        libs.append(np.array(sorted(idx)))
    return libs


_W = {}


def _init():
    from common import single_thread_worker
    single_thread_worker()
    _, X, N, ident = load_raw()
    _W.update(X=X, N=N, ident=ident)


def _library(args):
    li, idx, cfg, fl_thr, ag_thr = args
    X, N, y = _W["X"][idx], _W["N"][idx], _W["ident"][idx]
    res = {"library": li, "faces": int(len(idx)), "people": int(len(np.unique(y)))}
    for name, m in METHODS.items():
        f1, ari, preds = [], [], []
        for sd in range(N_ORDERS):
            perm = np.random.RandomState(5000 + 97 * li + sd).permutation(len(idx))
            lab = run_method(m, X[perm], N[perm], cfg, fl_thr)
            back = np.empty(len(idx), dtype=int); back[perm] = lab
            e = evaluate(back, y); f1.append(e["B3_F1"]); ari.append(e["ARI"]); preds.append(back)
        agree = [adjusted_rand_score(preds[i], preds[j]) for i in range(len(preds)) for j in range(i + 1, len(preds))]
        res[name] = {"F1_mean": float(np.mean(f1)), "F1_min": float(np.min(f1)), "F1_spread": float(np.max(f1) - np.min(f1)),
                     "ARI_mean": float(np.mean(ari)), "ARI_min": float(np.min(ari)), "ARI_spread": float(np.max(ari) - np.min(ari)),
                     "agree_mean": float(np.mean(agree)), "agree_min": float(np.min(agree))}
    e = evaluate(agglomerative(X, 1.0 - ag_thr), y)
    res["Agglomerative (batch reference)"] = {"F1_mean": e["B3_F1"], "ARI_mean": e["ARI"]}
    return res


def main():
    _, X, N, ident = load_raw()
    e7 = load_json("exp7_order_stability.json")
    fl_thr, ag_thr = e7["thresholds"]["first_leader"], e7["thresholds"]["agglomerative"]
    libs = make_libraries(ident)
    with ProcessPoolExecutor(WORKERS, initializer=_init) as pool:
        cfg, tuning = tune_on_libraries(ident, e7["config"], pool)
    print("[tune on seed-1 libraries] chosen:", {k: cfg[k] for k in ("link", "m", "merge")}, flush=True)
    print(f"{len(libs)} libraries, faces {min(map(len, libs))}-{max(map(len, libs))}, {N_ORDERS} orders, {WORKERS} workers", flush=True)
    rows = []
    with ProcessPoolExecutor(WORKERS, initializer=_init) as pool:
        for r in pool.map(_library, [(i, l, cfg, fl_thr, ag_thr) for i, l in enumerate(libs)]):
            rows.append(r)
            print(f"  lib {r['library']:>2} faces={r['faces']:>4} people={r['people']:>3} | " + " | ".join(
                f"{k.split(' ')[0]} F1 {v['F1_mean']:.3f} spread {v.get('F1_spread', 0):.3f} agree {v.get('agree_min', 1):.3f}"
                for k, v in r.items() if isinstance(v, dict)), flush=True)
    summary = {}
    for name in list(METHODS) + ["Agglomerative (batch reference)"]:
        keys = rows[0][name].keys()
        summary[name] = {k: {"mean": float(np.mean([r[name][k] for r in rows])), "worst": float(
            np.max([r[name][k] for r in rows]) if "spread" in k else np.min([r[name][k] for r in rows]))} for k in keys}
        s = summary[name]
        print(f"{name:<38} F1 {s['F1_mean']['mean']:.4f} (worst lib {s['F1_mean']['worst']:.4f})"
              + (f"  F1 spread mean {s['F1_spread']['mean']:.4f} max {s['F1_spread']['worst']:.4f}"
                 f"  ARI spread max {s['ARI_spread']['worst']:.4f}  agree min {s['agree_min']['worst']:.4f}" if "F1_spread" in s else ""),
              flush=True)
    save_json("exp8_personal_libraries_quick.json" if QUICK else "exp8_personal_libraries.json",
              {"n_libraries": N_LIB, "n_orders": N_ORDERS, "config": cfg, "config_selected_on": "seed-1 tuning libraries, max mean ARI", "tuning_grid": tuning, "summary": summary, "libraries": rows})
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
