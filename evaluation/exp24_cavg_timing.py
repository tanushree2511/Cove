"""Experiment 24 - the missing cost comparison: constrained average linkage timed directly (review round 3, DA M1).

Round 3 found that the paper's 5.1 s vs 16.7 s compared our read step with PLAIN average linkage, never with the
constrained average linkage that exp19 uses as the strongest baseline. Here, on the clean LFW faces (EdgeFace-S, shipped
exp14 thresholds, ONE thread), with 0 and 10 corrections (exp15's oracle user on the uncorrected result):
  c-avg (as written)   exp19's c_avg, a dense NumPy implementation, on random subsets of 1,658 and 3,316 faces
                       (it did not finish at 8,290 faces within 10 minutes in the reviewer's run)
  c-avg (decomposed)  the same algorithm run per connected group of the threshold graph (exact for average linkage;
                       checked equal to the plain version on the 1,658-face subset), so it can be timed at 8,290 faces
  ours                labels() of the clusterer after the faces were added (fast read step, exp20)
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp24_cavg_timing.py
"""
import json
import os
import sys
import time

os.environ["COVE_FACE_MODEL"] = "edgeface_s"
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cove"))
from common import be_nice, save_json, single_thread_worker  # noqa: E402
single_thread_worker()
be_nice()
import exp14_disjoint as D  # noqa: E402
import exp19_correction_baselines as E  # noqa: E402
from exp15_corrections import pick_correction  # noqa: E402
from exp20_exact_read import build, canon  # noqa: E402
from scipy.sparse import coo_matrix  # noqa: E402
from scipy.sparse.csgraph import connected_components  # noqa: E402

tuned = json.load(open(os.path.join(os.path.dirname(__file__), "results", "exp14_tuned_edgeface_s.json"), encoding="utf8"))["tuned"]
P, THR = tuned["Ours"]["params"], tuned["Agglomerative (avg)"]["params"]["thr"]
E._D["avg_thr"] = THR


def c_avg_decomposed(X, cons):
    n = len(X)
    Xu = (X / np.linalg.norm(X, axis=1, keepdims=True)).astype("float32")
    rows, cols = [], []
    for s in range(0, n, 2048):
        r, c = np.nonzero(Xu[s:s + 2048] @ Xu.T >= THR - 1e-4)
        rows.append(r + s)
        cols.append(c)
    r, c = np.concatenate(rows), np.concatenate(cols)
    mr = [a for k, a, b in cons if k == "must"]
    mc = [b for k, a, b in cons if k == "must"]
    g = coo_matrix((np.ones(len(r) + len(mr), dtype=np.int8), (np.concatenate([r, mr]).astype(int),
                                                              np.concatenate([c, mc]).astype(int))), shape=(n, n))
    comp = connected_components(g, directed=False)[1]
    out = np.arange(n)
    nxt = n
    for cid in np.nonzero(np.bincount(comp) > 1)[0]:
        idx = np.nonzero(comp == cid)[0]
        pos = {int(v): t for t, v in enumerate(idx)}
        sub = [(k, pos[a], pos[b]) for k, a, b in cons if a in pos and b in pos]
        lab = E.c_avg(X[idx], sub)
        out[idx] = nxt + lab
        nxt += int(lab.max()) + 1
    return out


def timed(f):
    t0 = time.perf_counter()
    r = f()
    return r, time.perf_counter() - t0


def main():
    paths, X, N = D.load_set("lfw_clean")
    y = np.array([q.split("/")[0] for q in paths])
    out = {"config": P, "avg_thr": THR, "rows": {}}
    for n in (1658, 3316, 8290):
        idx = np.sort(np.random.RandomState(24).permutation(len(X))[:n]) if n < len(X) else np.arange(len(X))
        Xs, Ns, ys = X[idx], N[idx], y[idx]
        c = build(Xs, Ns, P, True)
        lab = c.labels()
        cons = []
        while len(cons) < 10:
            k = pick_correction(lab, ys, Xs, set(cons))
            if k is None:
                break
            cons.append(k)
        row = {"faces": len(Xs)}
        for kk in (0, 10):
            cs = cons[:kk]
            c.must, c.cannot = set(), set()
            for kind, a, b in cs:
                (c.add_must_link if kind == "must" else c.add_cannot_link)(a, b)
            _, row[f"ours_{kk}_s"] = timed(c.labels)
            dec, row[f"cavg_decomposed_{kk}_s"] = timed(lambda: c_avg_decomposed(Xs, cs))
            if n <= 3316:
                pure, row[f"cavg_pure_{kk}_s"] = timed(lambda: E.c_avg(Xs, cs))
                row[f"cavg_equal_{kk}"] = bool(np.array_equal(canon(pure), canon(dec)))
            print(n, kk, {a: (round(b, 2) if isinstance(b, float) else b) for a, b in row.items()}, flush=True)
        out["rows"][str(n)] = row
    save_json("exp24_cavg_timing_edgeface_s.json", {"protocol": __doc__, **out})


if __name__ == "__main__":
    main()
