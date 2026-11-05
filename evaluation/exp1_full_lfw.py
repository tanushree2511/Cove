"""Experiment 1 (stress test): cluster ALL 13,233 LFW faces (5,749 identities; 4,069 of them appear once) with every method.

The 2,914-image test split of exp1_cluster.py is nearly saturated (B-Cubed F1 ~0.99), which hides differences between methods; the
full set has many more near-duplicate identities to confuse, and it shows how each method's runtime scales with n.
Thresholds are the ones tuned on the TUNING split (no test-set tuning); the two-stage method also runs at its production defaults.
5 shuffled input orders per method (Agglomerative: 1 run - its result is order-independent and it is O(n^2) in memory/time).
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import load_json, save_json  # noqa: E402
from exp1_cluster import (METHODS, evaluate, load_embeddings, ours_two_stage, run_shuffled, summarise, timed)  # noqa: E402


def main():
    paths, X, _ = load_embeddings()
    ident = np.array([p.replace("\\", "/").split("/")[0] for p in paths])
    tuned = load_json("exp1_clustering.json")["tuning"]["tuned_threshold"]
    print(f"{len(X)} faces, {len(set(ident.tolist()))} identities", flush=True)
    rows = {}
    configs = {n: (METHODS[n], tuned[n]) for n in METHODS}
    configs["Ours (two-stage, production defaults 0.45/0.40)"] = (lambda X_, s: ours_two_stage(X_, 0.45, 0.40), None)
    for name, (fn, thr) in configs.items():
        if name.startswith("Agglomerative"):
            lab, sec = timed(fn, X, thr)
            m = evaluate(lab, ident); m["seconds"] = sec
            rows[name] = {"threshold": thr, "metrics": {k: {"mean": v, "std": 0.0} for k, v in m.items()}, "order_agreement_ARI": 1.0, "runs": 1}
        else:
            r, agree = run_shuffled(fn, X, ident, thr)
            rows[name] = {"threshold": thr, "metrics": summarise(r), "order_agreement_ARI": agree, "runs": len(r)}
        mm = rows[name]["metrics"]
        print(f"{name:<52} F1={mm['B3_F1']['mean']:.4f}±{mm['B3_F1']['std']:.4f} P={mm['B3_P']['mean']:.4f} R={mm['B3_R']['mean']:.4f} "
              f"ARI={mm['ARI']['mean']:.4f} NMI={mm['NMI']['mean']:.4f} clusters={mm['clusters']['mean']:.0f} t={mm['seconds']['mean']:.1f}s", flush=True)
    # runtime scaling with n (one run each, tuned thresholds, subsets of the full set)
    scaling = {}
    rng = np.random.RandomState(0)
    for n in (1000, 2000, 4000, 8000, len(X)):
        sub = rng.permutation(len(X))[:n]
        scaling[str(n)] = {}
        for name, (fn, thr) in configs.items():
            if name.startswith("Ours (two-stage, production"):
                continue
            _, sec = timed(fn, X[sub], thr)
            scaling[str(n)][name] = sec
        print("scaling", n, {k: round(v, 2) for k, v in scaling[str(n)].items()}, flush=True)
    save_json("exp1_full_lfw.json", {"faces": len(X), "identities": int(len(set(ident.tolist()))), "table": rows, "runtime_scaling_s": scaling})
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
