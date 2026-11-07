"""Experiment 15 - user corrections that survive re-clustering (must-link / cannot-link constraints).

Question: if a user fixes a few mistakes, (a) how much better does the library get, and (b) do the fixes survive
when new photos arrive and everything is clustered again? Today the app re-clusters from scratch, so (b) is "no".

Protocol (TEST libraries of exp14 only; identity-disjoint from tuning; nothing here is tuned):
  * method: ours with the exp14 tuned configuration of the recogniser (results/exp14_tuned_<model>.json).
  * each library is split once (fixed seed) into "now" (80% of photos) and "later" (20%, arriving afterwards).
  * a simulated user makes up to 10 corrections on the "now" clustering, one at a time. Each time they fix the
    single visible mistake that is biggest (most wrongly grouped face pairs):
      - a cluster mixing two people  -> "these are different people": cannot-link between the central face of the
        main person and the face of the other person that looks most like the main person;
      - a person split over two clusters -> "these are the same person": must-link between the two central faces.
  * after k corrections: B-Cubed F1 on "now".
  * then the "later" photos arrive and everything is re-clustered:
      kept  = clusterer keeps the corrections (this work);  lost = plain re-clustering (current app behaviour).
    We report F1 and the share of the user's corrections that still hold.
  * order check: all faces and all corrections inserted in 3 random orders -> agreement (ARI) with the original.
Run: COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp15_corrections.py   -> results/exp15_corrections_<model>.json
"""
import json
import os
import sys
import time
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cove"))
from adaptive import run_adaptive  # noqa: E402
from common import CACHE, be_nice, save_json, single_thread_worker  # noqa: E402
be_nice()
from engines.stable_cluster import StableIncrementalClusterer  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402

MODEL = os.environ.get("COVE_FACE_MODEL")
assert MODEL in ("mbf", "edgeface_s"), "set COVE_FACE_MODEL=mbf or edgeface_s"
SHARED = os.path.join(CACHE, f"exp14_shared_{MODEL}")
KS = (0, 1, 2, 3, 5, 10)
_D = {}


def _init():
    single_thread_worker()
    d = np.load(SHARED + ".npz")
    _D["X"] = np.load(SHARED + "_X.npy", mmap_mode="r")
    _D["N"], _D["y"], b = d["N"], d["y"], d["bounds"]
    _D["sl"] = {k: slice(b[i], b[i + 1]) for i, k in enumerate(d["keys"].tolist())}
    res = os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json")
    _D["cfg"] = json.load(open(res, encoding="utf8"))["tuned"]["Ours"]["params"]


def make(X, N, cons=(), order=None):
    p = _D["cfg"]
    c = StableIncrementalClusterer(link_threshold=p["link"], min_neighbors=p["m"], attach_threshold=p["attach"],
                                   merge_threshold=p["merge"], dim=X.shape[1])
    n = len(X)
    order = np.arange(n) if order is None else order
    inv = np.empty(n, dtype=int)
    inv[order] = np.arange(n)
    for s in range(0, n, 64):
        c.add(X[order[s:s + 64]], N[order[s:s + 64]])
    for kind, a, b in cons:
        (c.add_must_link if kind == "must" else c.add_cannot_link)(inv[a], inv[b])
    return c.labels()[inv]


def _central(X, idx):
    m = X[idx].mean(0)
    return int(idx[np.argmax(X[idx] @ m)])


def pick_correction(lab, y, X, done):
    """The single biggest visible mistake (most wrongly grouped pairs), as a constraint the user would give."""
    best = None
    for c in np.unique(lab):
        idx = np.where(lab == c)[0]
        cnt = Counter(y[idx]).most_common()
        if len(cnt) < 2:
            continue
        p = cnt[0][0]
        P = idx[y[idx] == p]
        a = _central(X, P)
        for q, nq in cnt[1:]:
            Q = idx[y[idx] == q]
            bq = int(Q[np.argmax(X[Q] @ X[P].mean(0))])
            key = ("cannot", min(a, bq), max(a, bq))
            if key not in done and (best is None or len(P) * nq > best[0]):
                best = (len(P) * nq, key)
    for person in np.unique(y):
        idx = np.where(y == person)[0]
        cnt = Counter(lab[idx]).most_common(2)
        if len(cnt) < 2:
            continue
        A = idx[lab[idx] == cnt[0][0]]
        B = idx[lab[idx] == cnt[1][0]]
        a, b = _central(X, A), _central(X, B)
        key = ("must", min(a, b), max(a, b))
        if key not in done and (best is None or len(A) * len(B) > best[0]):
            best = (len(A) * len(B), key)
    return None if best is None else best[1]


def satisfied(lab, cons):
    if not cons:
        return 1.0
    return float(np.mean([(lab[a] == lab[b]) == (k == "must") for k, a, b in cons]))


def _job(key):
    sl = _D["sl"][key]
    X, N, y = np.asarray(_D["X"][sl]), _D["N"][sl], _D["y"][sl]
    rng = np.random.RandomState(int(key.split("|")[2]) + 15000)
    perm = rng.permutation(len(X))                       # "now" = first 80%, "later" = last 20%, in this new indexing
    X, N, y = X[perm], N[perm], y[perm]
    m = int(round(0.8 * len(X)))
    Xn, Nn, yn = X[:m], N[:m], y[:m]
    cons, out = [], {"faces_now": m, "faces_total": len(X)}
    lab = make(Xn, Nn)
    for k in range(max(KS) + 1):
        if k in KS:
            out[f"now_k{k}"] = evaluate(lab, yn)["B3_F1"]
        if k == max(KS):
            break
        c = pick_correction(lab, yn, Xn, set(cons))
        if c is None:                                     # nothing left to fix
            f = evaluate(lab, yn)["B3_F1"]
            for kk in KS:
                if kk > k:
                    out[f"now_k{kk}"] = f
            break
        cons.append(c)
        lab = make(Xn, Nn, cons)
    out["corrections_made"] = len(cons)
    lost = make(X, N)                                     # current app: re-cluster without the corrections
    out["later_lost_F1"] = evaluate(lost, y)["B3_F1"]
    for k in (0, 5, 10):
        kept = make(X, N, cons[:k])
        out[f"later_kept_k{k}_F1"] = evaluate(kept, y)["B3_F1"]
        out[f"later_kept_k{k}_satisfied"] = satisfied(kept, cons[:k])
    out["later_lost_satisfied"] = satisfied(lost, cons)
    ref = make(X, N, cons)
    from sklearn.metrics import adjusted_rand_score
    agree = []
    for t in range(3):
        o = np.random.RandomState(700 + t).permutation(len(X))
        cs = [cons[i] for i in np.random.RandomState(800 + t).permutation(len(cons))]
        agree.append(adjusted_rand_score(ref, make(X, N, cs, order=o)))
    out["order_agreement_min"] = float(min(agree))
    return key, out


def boot(a, b, n=10000, seed=0):
    d = np.asarray(a) - np.asarray(b)
    r = np.random.RandomState(seed)
    m = d[r.randint(0, len(d), (n, len(d)))].mean(1)
    return {"diff": float(d.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]}


def main():
    t0 = time.time()
    keys = [k for k in np.load(SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    rows = dict(run_adaptive(_job, keys, initializer=_init, name="CORRECTIONS"))
    by = {}
    for k, r in rows.items():
        by.setdefault(k.split("|")[1], []).append(r)
    allr = list(rows.values())
    table = {}
    for cond, rs in list(by.items()) + [("ALL", allr)]:
        t = {f: float(np.mean([r[f] for r in rs])) for f in rs[0] if isinstance(rs[0][f], float)}
        t["order_agreement_min"] = float(min(r["order_agreement_min"] for r in rs))
        t["gain_now_k10_vs_k0"] = boot([r["now_k10"] for r in rs], [r["now_k0"] for r in rs])
        t["later_kept10_vs_lost"] = boot([r["later_kept_k10_F1"] for r in rs], [r["later_lost_F1"] for r in rs])
        table[cond] = t
        print(f"== {cond:9} now F1 k0 {t['now_k0']:.4f} k1 {t['now_k1']:.4f} k3 {t['now_k3']:.4f} k5 {t['now_k5']:.4f} "
              f"k10 {t['now_k10']:.4f} | after new photos: kept {t['later_kept_k10_F1']:.4f} lost {t['later_lost_F1']:.4f} "
              f"| corrections still true: kept {t['later_kept_k10_satisfied']:.3f} lost {t['later_lost_satisfied']:.3f} "
              f"| order-agree {t['order_agreement_min']:.4f}", flush=True)
    save_json(f"exp15_corrections_{MODEL}.json", {"model": MODEL, "protocol": __doc__, "config": json.load(open(
        os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json")))["tuned"]["Ours"]["params"],
        "table": table, "per_library": rows, "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
