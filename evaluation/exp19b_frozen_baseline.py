"""Experiment 19b - an Immich-style 'frozen' baseline for corrections (review round 2, R2 W1).

Immich's incremental face clustering keeps the people it has already found and gives each new face the person of
its most similar face (docs.immich.app/features/facial-recognition). Applied to our protocol:
  now    the user corrects OUR clustering of the "now" photos (exp15/exp19 oracle user, corrections inside ours);
  later  the corrected "now" people are frozen; each "later" face, in arrival order, joins the person of its most
         similar already-placed face if the similarity is >= 0.5 (Immich's default maximum distance 0.5), else
         starts a new person. Corrections therefore always hold; the question is F1 and order dependence.
Order check: the "later" faces arrive in 3 random orders; min ARI to the arrival order used.
Run: COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp19b_frozen_baseline.py
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import exp19_correction_baselines as E  # noqa: E402
from adaptive import run_adaptive  # noqa: E402
from common import save_json  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402

THR = 0.5


def frozen(lab_now, X, m, order):
    Xu = X / np.linalg.norm(X, axis=1, keepdims=True)
    lab = np.full(len(X), -1)
    lab[:m] = lab_now
    placed = list(range(m))
    nxt = lab_now.max() + 1
    for i in order:
        s = Xu[placed] @ Xu[i]
        j = int(np.argmax(s))
        if s[j] >= THR:
            lab[i] = lab[placed[j]]
        else:
            lab[i] = nxt
            nxt += 1
        placed.append(i)
    return lab


def _job(key):
    sl = E._D["sl"][key]
    X, N, y = np.asarray(E._D["X"][sl]), E._D["N"][sl], E._D["y"][sl]
    seed = int(key.split("|")[2])
    perm = np.random.RandomState(seed + 15000).permutation(len(X))
    X, N, y = X[perm], N[perm], y[perm]
    m = int(round(0.8 * len(X)))
    Xn, Nn, yn = X[:m], N[:m], y[:m]
    cons = []
    lab = E.ours(Xn, Nn, cons)
    for _ in range(E.MAXK):
        c = E.pick_correction(lab, yn, Xn, set(cons))
        if c is None:
            break
        cons.append(c)
        lab = E.ours(Xn, Nn, cons)
    later = frozen(lab, X, m, np.arange(m, len(X)))
    from sklearn.metrics import adjusted_rand_score
    agree = [adjusted_rand_score(later, frozen(lab, X, m, m + np.random.RandomState(700 + t).permutation(len(X) - m)))
             for t in range(3)]
    return key, {"n": len(cons), "later_F1": evaluate(later, y)["B3_F1"],
                 "later_new_F1": evaluate(later[m:], y[m:])["B3_F1"], "held": E.held(later, cons),
                 "order_agreement_min": float(min(agree))}


def main():
    t0 = time.time()
    keys = [k for k in np.load(E.SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    rows = dict(run_adaptive(_job, keys, initializer=E._init, name="FROZEN", per_step=4))
    by = {"ALL": list(rows.values())}
    for k, r in rows.items():
        by.setdefault(k.split("|")[1], []).append(r)
    table = {}
    for cond, rs in by.items():
        nc = sum(r["n"] for r in rs)
        table[cond] = {"later_F1": float(np.mean([r["later_F1"] for r in rs])),
                       "later_new_F1": float(np.mean([r["later_new_F1"] for r in rs])),
                       "held_share": sum(r["held"] for r in rs) / nc if nc else None,
                       "order_agreement_min": float(min(r["order_agreement_min"] for r in rs))}
        print(cond, {k: round(v, 4) if v is not None else None for k, v in table[cond].items()}, flush=True)
    save_json(f"exp19b_frozen_{E.MODEL}.json", {"model": E.MODEL, "protocol": __doc__, "threshold": THR,
                                                "table": table, "per_library": rows, "seconds": time.time() - t0})


if __name__ == "__main__":
    main()
