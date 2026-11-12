"""Experiment 28 - fairer tuning, equal shuffles and an identity-level bootstrap (answers the external review of 2026-11-12).

The review's objections to Table I: (a) ours has four tuned parameters (360 grid points) and the baselines one or two on a
coarse 0.05 grid ("equal terms" did not hold in freedom); (b) ours ran in 3 shuffled orders, order-dependent baselines in 5;
(c) the bootstrap resamples libraries, but the 30 test libraries share the same people, so the intervals are too narrow.
Here, on the same identity-disjoint libraries (EdgeFace-S, exp14 split; nothing about the test half is used for tuning):
  1. Every baseline is re-tuned on a much finer grid (step 0.01 for similarity thresholds, more values for the other
     parameters) with exp14's rule (highest mean ARI on the tuning libraries).
  2. Ours is also run with a SMALL budget: the best of 51 randomly chosen configurations of its own grid (51 = the number of
     grid points of a one-threshold baseline), for 5 random draws, chosen by tuning ARI only.
  3. Every method runs in 5 shuffled orders on the test libraries.
  4. Bootstrap over IDENTITIES: each person (family people and each single-photo stranger) gets a Poisson(1) weight per
     resample; a library's B-Cubed precision/recall are the weight-averaged per-face values; F1 is formed per library and
     averaged over the 30 libraries. This keeps the libraries' shared people shared across resamples.
Pre-declared reading: nothing is tuned on test data; every number is reported even if it favours a baseline.
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp28_fair_tuning_identity_bootstrap.py
Output: results/exp28_fair_tuning_edgeface_s.json (+ cache npz of per-face scores)
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import exp14_disjoint as D  # noqa: E402
from adaptive import run_adaptive  # noqa: E402
from common import CACHE, save_json, single_thread_worker  # noqa: E402
from exp1_cluster import contingency, evaluate  # noqa: E402

RES = os.path.join(os.path.dirname(__file__), "results")
T1 = [float(round(x, 2)) for x in np.arange(0.20, 0.701, 0.01)]
T2 = [float(round(x, 2)) for x in np.arange(0.20, 0.701, 0.02)]
FINE = {
    "First-Leader": [dict(thr=t) for t in T1],
    "Two-stage": [dict(thr=t, merge=g) for t in T2 for g in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60)],
    "Single linkage": [dict(thr=t) for t in T1],
    "Agglomerative (avg)": [dict(thr=t) for t in T1],
    "DBSCAN": [dict(thr=t, ms=k) for t in T1 for k in (2, 3, 4, 5)],
    "HDBSCAN": [dict(mcs=a, ms=b) for a in (2, 3, 4, 5, 6, 8, 10) for b in (1, 2, 3, 4, 5, 7)],
}
BUDGET, DRAWS = 51, 5


def _test2(args):
    method, p, key = args
    sl = D._D["sl"][key]
    X, N, y = np.asarray(D._D["X"][sl]), D._D["N"][sl], D._D["y"][sl]
    rows, perface = [], None
    for sd in range(5):
        perm = np.random.RandomState(77 + sd).permutation(len(X))
        lab = D.run(method.split("#")[0], X[perm], N[perm], p)
        back = np.empty(len(X), dtype=int)
        back[perm] = lab
        rows.append(evaluate(back, y))
        if sd == 0:
            M, pi, ti = contingency(back, y)
            inter = M[pi, ti].astype(float)
            perface = np.stack([inter / M.sum(1)[pi], inter / M.sum(0)[ti]]).astype("float32")
    m = {k: float(np.mean([r[k] for r in rows])) for k in ("B3_P", "B3_R", "B3_F1", "ARI")}
    return method, key, m, perface.tolist()


def main():
    t0 = time.time()
    info, tune_ids = D.build_shared()
    coarse = json.load(open(os.path.join(RES, "exp14_tuned_edgeface_s.json"), encoding="utf8"))
    # ---- 1. fine tuning of the baselines
    ck = os.path.join(RES, "exp28_tuned_fine_edgeface_s.json")
    if os.path.exists(ck):
        fine = json.load(open(ck, encoding="utf8"))
        print("fine tuning resumed from", ck, flush=True)
    else:
        jobs = [(m, p) for m, g in FINE.items() for p in g]
        print(f"FINE TUNING: {len(jobs)} configurations", flush=True)
        rows = run_adaptive(D._tune, jobs, initializer=D._init, name="FINE-TUNE")
        best = {}
        for m, p, by, mean in rows:
            if m not in best or mean > best[m][1]:
                best[m] = (p, mean)
        fine = {m: {"params": p, "tuning_ARI_mean": s} for m, (p, s) in best.items()}
        save_json(os.path.basename(ck), fine)
    for m, v in fine.items():
        print(f"  FINE   {m:<22} {v['params']}  tuning ARI {v['tuning_ARI_mean']:.4f}   "
              f"(coarse: {coarse['tuned'][m]['params']}  {coarse['tuned'][m]['tuning_ARI_mean']:.4f})", flush=True)
    # ---- 2. ours with a small random budget (tuning ARI only)
    ours_rows = coarse["grid"]["Ours"]
    budget = {}
    for s in range(DRAWS):
        idx = np.random.RandomState(100 + s).choice(len(ours_rows), BUDGET, replace=False)
        r = max((ours_rows[i] for i in idx), key=lambda r: r["ARI_mean"])
        budget[f"Ours (budget {BUDGET}, draw {s})"] = {k: r[k] for k in ("link", "m", "attach", "merge")} | \
            {"tuning_ARI_mean": r["ARI_mean"]}
    # ---- 3. test runs, 5 orders each
    methods = {}
    for m, v in coarse["tuned"].items():
        methods[m + " [coarse grid]" if m in FINE else m] = (m, v["params"])
    for m, v in fine.items():
        methods[m + " [fine grid]"] = (m, v["params"])
    for name, v in budget.items():
        methods[name] = ("Ours", {k: v[k] for k in ("link", "m", "attach", "merge")})
    keys = [k for k in D._D_keys() if k.startswith("test|")]
    cache = os.path.join(RES, "exp28_testruns_edgeface_s.json")
    if os.path.exists(cache):
        raw = json.load(open(cache, encoding="utf8"))
        print("test runs resumed", flush=True)
    else:
        jobs = [((name, base), p, k) for name, (base, p) in methods.items() for k in keys]
        print(f"TEST: {len(jobs)} library runs x 5 orders", flush=True)
        raw = {}
        res = run_adaptive(_test_wrap, jobs, initializer=D._init, name="TEST5")
        for name, key, m, pf in res:
            raw.setdefault(name, {})[key] = {"m": m, "pf": pf}
        json.dump(raw, open(cache, "w", encoding="utf8"))
    # ---- 4. summaries and identity bootstrap
    D._init()                                          # the summary reads labels in this (main) process
    ident = {}
    for k in keys:
        sl = D._D["sl"][k]
        ident[k] = np.asarray(D._D["y"][sl])
    all_ids = sorted({str(v) for a in ident.values() for v in a})
    pos = {v: i for i, v in enumerate(all_ids)}
    idx = {k: np.array([pos[str(v)] for v in a]) for k, a in ident.items()}
    B = 1000
    rng = np.random.RandomState(28)
    W = rng.poisson(1.0, (B, len(all_ids))).astype("float32")

    def boot_f1(name, cond):
        out = np.zeros(B)
        ks = [k for k in keys if k.split("|")[1] == cond]
        for k in ks:
            pf = np.asarray(raw[name][k]["pf"], dtype="float32")
            w = W[:, idx[k]]
            sw = np.maximum(w.sum(1), 1e-9)
            P, R = (w * pf[0]).sum(1) / sw, (w * pf[1]).sum(1) / sw
            out += 2 * P * R / np.maximum(P + R, 1e-12)
        return out / len(ks)

    table, boot = {}, {}
    conds = sorted({k.split("|")[1] for k in keys})
    for cond in conds + ["ALL"]:
        cs = conds if cond == "ALL" else [cond]
        table[cond] = {n: float(np.mean([raw[n][k]["m"]["B3_F1"] for k in keys if k.split("|")[1] in cs])) for n in raw}
    ref_names = ["Ours"] + [n for n in raw if n.startswith("Ours (budget")]
    for ref in ref_names:
        boot[ref] = {}
        for cond in conds:
            f_ref = boot_f1(ref, cond)
            boot[ref][cond] = {}
            for n in raw:
                if n == ref:
                    continue
                d = f_ref - boot_f1(n, cond)
                obs = table[cond][ref] - table[cond][n]
                boot[ref][cond][n] = {"diff": float(obs), "ci95_identity": [float(np.percentile(d, 2.5)),
                                                                             float(np.percentile(d, 97.5))]}
    order = {n: float(min(raw[n][k]["m"]["B3_F1"] for k in keys)) for n in raw}
    save_json("exp28_fair_tuning_edgeface_s.json", {
        "protocol": __doc__, "fine_tuned": fine, "budget_configs": budget, "table_F1": table,
        "bootstrap_identity_ours_minus": boot, "worst_library_F1": order, "seconds": time.time() - t0,
        "n_identities": len(all_ids), "bootstrap_resamples": B})
    for n in raw:
        print(f"{n:<42} ALL {table['ALL'][n]:.4f}", flush=True)
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


def _test_wrap(args):
    (name, base), p, key = args
    out = _test2((base, p, key))
    return name, out[1], out[2], out[3]


if __name__ == "__main__":
    main()
