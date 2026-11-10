"""Experiment 22 (E3) - undoing a wrong correction, and how a frozen rule differs.

Pre-declared protocol (round-4 research plan, nothing tuned; exp14 thresholds, exp14 test libraries):
  The error-prone user of exp19 (casual clicks, 10% wrong "same person" between look-alike clusters) works on the
  "now" 80% of a library with ours. For every library where this user made at least one WRONG correction we take the
  first wrong one, let the "later" 20% arrive, and then the user RETRACTS that correction.
  never-made   the same session without the wrong correction (faces in a different arrival order)
  ours-undo    the stored corrections minus the wrong one, recomputed; compared with never-made (exact equality?)
  frozen-undo  Immich-style frozen labels (exp19b rule, cosine >= 0.5) built from the corrected "now" labels with the
               wrong correction in place; retraction is the inverse edit of the stored labels: the merged person is split
               again by which of the two clicked faces each member (including faces that arrived later) is closer to.
Outcome: share of libraries whose result after retraction is IDENTICAL to never-made; ARI to never-made; F1 with the
mistake in place, after retraction and never-made. Also (b): can a wrong "same person" click be flagged?  AUC of
(1 - cosine of the two clicked faces) for wrong vs correct "same person" clicks, pooled over all libraries and users
(reported even if poor; look-alike merges involve very similar faces, so it may be below 0.5).
Run: COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp22_undo.py
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import exp19_correction_baselines as E  # noqa: E402
import exp19b_frozen_baseline as F  # noqa: E402
from adaptive import run_adaptive  # noqa: E402
from common import save_json  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402
from exp21_replica_convergence import apply_op, canon  # noqa: E402
from sklearn.metrics import adjusted_rand_score, roc_auc_score  # noqa: E402


def _job(key):
    sl = E._D["sl"][key]
    X, N, y = np.asarray(E._D["X"][sl]), E._D["N"][sl], E._D["y"][sl]
    seed = int(key.split("|")[2])
    perm = np.random.RandomState(seed + 15000).permutation(len(X))
    X, N, y = X[perm], N[perm], y[perm]
    m = int(round(0.8 * len(X)))
    Xn, Nn, yn = X[:m], N[:m], y[:m]
    Xu = X / np.linalg.norm(X, axis=1, keepdims=True)
    rng = np.random.RandomState(seed * 100 + 2)               # the exp19 error-prone ("noisy") user
    cons = []
    lab = E.ours(Xn, Nn, cons)
    for _ in range(E.MAXK):
        c = None
        if rng.rand() < 0.1:
            c = E.wrong_merge(lab, yn, Xn, set(cons), rng)
        if c is None:
            c = E.biggest_mistake(lab, yn, Xn, set(cons), "casual", rng)
        if c is None:
            break
        cons.append(c)
        lab = E.ours(Xn, Nn, cons)
    out = {"clicks": [{"must": k == "must", "wrong": bool(y[a] != y[b]) if k == "must" else bool(y[a] == y[b]),
                       "cos": float(Xu[a] @ Xu[b])} for k, a, b in cons]}
    wrong = [c for c in cons if c[0] == "must" and yn[c[1]] != yn[c[2]]]
    if not wrong:
        return key, out
    bad = wrong[0]
    good = [c for c in cons if c != bad]
    order = np.random.RandomState(900 + seed).permutation(len(X))
    # --- ours --------------------------------------------------------------------------------------------
    with_bad = E.ours(X, N, cons)
    never = E.ours(X, N, good, order)                                    # never made, other arrival order
    undone = E.ours(X, N, good)                                          # made, then retracted (set minus one)
    out["ours"] = {"identical": bool(np.array_equal(canon(undone), canon(never))),
                   "ari": float(adjusted_rand_score(undone, never)),
                   "F1_with": evaluate(with_bad, y)["B3_F1"], "F1_after": evaluate(undone, y)["B3_F1"],
                   "F1_never": evaluate(never, y)["B3_F1"]}
    # --- frozen --------------------------------------------------------------------------------------------
    now_bad = E.ours(Xn, Nn, cons)
    now_good = E.ours(Xn, Nn, good)
    arrive = np.arange(m, len(X))
    f_bad = F.frozen(now_bad, X, m, arrive)
    f_never = F.frozen(now_good, X, m, arrive)
    f_undo = f_bad.copy()                                                # inverse edit on the stored labels:
    apply_op(f_undo, ("cannot", bad[1], bad[2]), Xu)                     # split the merged person again
    out["frozen"] = {"identical": bool(np.array_equal(canon(f_undo), canon(f_never))),
                     "ari": float(adjusted_rand_score(f_undo, f_never)),
                     "F1_with": evaluate(f_bad, y)["B3_F1"], "F1_after": evaluate(f_undo, y)["B3_F1"],
                     "F1_never": evaluate(f_never, y)["B3_F1"]}
    return key, out


def main():
    t0 = time.time()
    keys = [k for k in np.load(E.SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    if len(sys.argv) > 1:
        keys = keys[:int(sys.argv[1])]
    rows = dict(run_adaptive(_job, keys, initializer=E._init, name="UNDO", per_step=4))
    table = {"libraries": len(rows)}
    have = [r for r in rows.values() if "ours" in r]
    table["libraries_with_wrong_correction"] = len(have)
    for m in ("ours", "frozen"):
        v = [r[m] for r in have]
        if v:
            table[m] = {"identical_share": float(np.mean([x["identical"] for x in v])),
                        "min_ari": float(min(x["ari"] for x in v)), "mean_ari": float(np.mean([x["ari"] for x in v])),
                        "F1_with_mistake": float(np.mean([x["F1_with"] for x in v])),
                        "F1_after_retraction": float(np.mean([x["F1_after"] for x in v])),
                        "F1_never_made": float(np.mean([x["F1_never"] for x in v]))}
    cl = [c for r in rows.values() for c in r["clicks"] if c["must"]]
    yv = np.array([c["wrong"] for c in cl])
    if 0 < yv.sum() < len(yv):
        table["detector"] = {"must_links": len(cl), "wrong": int(yv.sum()),
                             "auc_low_similarity_flags_wrong": float(roc_auc_score(yv, [-c["cos"] for c in cl])),
                             "mean_cos_wrong": float(np.mean([c["cos"] for c in cl if c["wrong"]])),
                             "mean_cos_right": float(np.mean([c["cos"] for c in cl if not c["wrong"]]))}
    print(table, flush=True)
    if len(sys.argv) > 1:
        return
    save_json(f"exp22_undo_{E.MODEL}.json", {"model": E.MODEL, "protocol": __doc__, "table": table,
                                             "per_library": rows, "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
