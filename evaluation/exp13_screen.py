"""Experiment 13b - SCREENING of candidate face-recognition models on pose and age (fast, same faces for all).

For each of four pose/age sets a FIXED random sample of 3000 same-person + 3000 different-person pairs is drawn once
(seed 0) and used for every model:
  AgeDB-30, CFP-FP : sampled from the OFFICIAL pair lists
  CALFW, CPLFW     : sampled from identity labels (same = two photos of one person; different = two random people)
Only the face crops in those pairs are embedded (identical crops for every model, crop_faces.py).
Metric: 10-fold verification accuracy (threshold chosen on 9 folds, applied to the 10th - the standard LFW protocol),
plus the paired difference to the current model (mbf) with a 95% bootstrap CI over pairs.
A model goes on to the full clustering test (exp9/exp11) only if it beats mbf with a CI that excludes 0.
Output: results/exp13_screen.json
"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, be_nice, save_json  # noqa: E402
be_nice()
from exp13_embed import MODELS, embed, session  # noqa: E402

N_PAIRS = 3000
SETS = ("calfw", "cplfw", "tune_agedb", "tune_cfpfp")
OFFICIAL = {"tune_agedb": "agedb_30", "tune_cfpfp": "cfp_fp"}


def make_pairs(name, paths):
    rng = np.random.RandomState(0)
    pos = {p: i for i, p in enumerate(paths)}
    if name in OFFICIAL:
        with open(os.path.join(DS, "hardtune", OFFICIAL[name], "pairs.csv")) as f:
            rows = [r for r in csv.DictReader(f) if r["a"] in pos and r["b"] in pos]
        same = [(pos[r["a"]], pos[r["b"]]) for r in rows if r["same"] == "1"]
        diff = [(pos[r["a"]], pos[r["b"]]) for r in rows if r["same"] == "0"]
        same = [same[i] for i in rng.choice(len(same), min(N_PAIRS, len(same)), replace=False)]
        diff = [diff[i] for i in rng.choice(len(diff), min(N_PAIRS, len(diff)), replace=False)]
    else:
        ident = [p.split("/")[0] if name == "calfw" else p.split("/")[-1].rsplit("_", 1)[0] for p in paths]
        by = {}
        for i, n in enumerate(ident):
            by.setdefault(n, []).append(i)
        multi = sorted(n for n, v in by.items() if len(v) >= 2)
        names = sorted(by)
        same, diff, seen = [], [], set()
        while len(same) < N_PAIRS:
            a, b = rng.choice(by[multi[rng.randint(len(multi))]], 2, replace=False)
            if (min(a, b), max(a, b)) not in seen:
                seen.add((min(a, b), max(a, b))); same.append((a, b))
        while len(diff) < N_PAIRS:
            n1, n2 = rng.choice(len(names), 2, replace=False)
            diff.append((rng.choice(by[names[n1]]), rng.choice(by[names[n2]])))
    P = np.array(same + diff)
    y = np.r_[np.ones(len(same)), np.zeros(len(diff))].astype(bool)
    return P, y


def tenfold_correct(sim, y):
    """Per-pair correctness under 10-fold threshold selection (fixed fold split, seed 1)."""
    folds = np.random.RandomState(1).permutation(len(y)) % 10
    ok = np.zeros(len(y), bool)
    cand = np.linspace(-0.3, 0.9, 241)
    for k in range(10):
        tr, te = folds != k, folds == k
        t = cand[np.argmax([((sim[tr] >= c) == y[tr]).mean() for c in cand])]
        ok[te] = (sim[te] >= t) == y[te]
    return ok


def main():
    models = [m for m in (sys.argv[1:] or list(MODELS)) if os.path.exists(MODELS[m][0])]
    out = {"n_pairs_per_set": 2 * N_PAIRS, "sets": {}}
    correct = {}
    for s in SETS:
        d = np.load(os.path.join(CACHE, f"crops_{s}.npz"))
        P, y = make_pairs(s, d["paths"].tolist())
        need = np.unique(P)
        remap = {j: i for i, j in enumerate(need)}
        Pi = np.vectorize(remap.get)(P)
        crops = d["crops"][need]
        out["sets"][s] = {"faces_embedded": int(len(need))}
        for m in models:
            cf = os.path.join(CACHE, f"screen_{m}_{s}.npy")
            if os.path.exists(cf):
                E = np.load(cf)
            else:
                E = embed(session(MODELS[m][0], os.cpu_count()), crops, MODELS[m])
                np.save(cf, E)
            E = E / np.linalg.norm(E, axis=1, keepdims=True)
            sim = np.einsum("ij,ij->i", E[Pi[:, 0]], E[Pi[:, 1]])
            ok = tenfold_correct(sim, y)
            correct[(m, s)] = ok
            out["sets"][s][m] = {"acc": float(ok.mean())}
            print(f"  {s:11s} {m:12s} acc {100 * ok.mean():.2f}%", flush=True)
    rng = np.random.RandomState(2)
    for s in SETS:
        if ("mbf", s) not in correct:
            continue
        for m in models:
            if m == "mbf":
                continue
            d = correct[(m, s)].astype(float) - correct[("mbf", s)].astype(float)
            bs = [d[rng.randint(len(d), size=len(d))].mean() for _ in range(2000)]
            out["sets"][s][m]["diff_vs_mbf"] = float(d.mean())
            out["sets"][s][m]["ci95"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    print("\n== accuracy (10-fold), and difference vs current model (95% CI)")
    print(f"{'model':12s}" + "".join(f"{s:>26s}" for s in SETS))
    for m in models:
        row = f"{m:12s}"
        for s in SETS:
            v = out["sets"][s][m]
            row += f"{100 * v['acc']:9.2f}%" + (f" ({100 * v['diff_vs_mbf']:+.2f} [{100 * v['ci95'][0]:+.2f},{100 * v['ci95'][1]:+.2f}])" if "ci95" in v else " " * 16)
        print(row, flush=True)
    save_json("exp13_screen.json", out)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
