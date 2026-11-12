"""Experiment 29 - scaling beyond 8,290 faces and a compiled (SciPy) average-linkage baseline (external review, 2026-11-12).

The review asked for sizes of at least 50,000 faces and for an optimised baseline. We only have 8,290 clean LFW faces, so larger
libraries are SYNTHETIC: the 8,290 embeddings are copied k times, each copy multiplied by its own random orthogonal matrix.
A rotation keeps every cosine inside a copy and makes copies unrelated to each other (different 'people', no cross links at the
tuned thresholds), so the work per copy is the same as for the real faces and the people number grows with k. This tests cost,
not accuracy: real libraries of that size would have different component sizes.
Timed on one thread, shipped EdgeFace-S setting, 0 and 10 corrections (the oracle user's, on the first copy):
  ours                labels() after the faces were added (fast read step)
  c-avg (cached)      constrained average linkage with the best-partner cache of exp27, per component of the threshold graph
  avg (SciPy)         UNCONSTRAINED average linkage in compiled C (scipy.cluster.hierarchy.linkage), per component
                      of the threshold graph; it cannot take constraints, so it is a lower bound on any constrained version
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp29_scaling.py
"""
import os
import sys
import time

os.environ["COVE_FACE_MODEL"] = "edgeface_s"
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
import exp27_cavg_fast_timing as F  # noqa: E402
import exp24_cavg_timing as T  # noqa: E402
import exp14_disjoint as D  # noqa: E402
import exp19_correction_baselines as E  # noqa: E402
from common import save_json  # noqa: E402
from exp15_corrections import pick_correction  # noqa: E402
from exp20_exact_read import build  # noqa: E402
from scipy.cluster.hierarchy import fcluster, linkage  # noqa: E402
from scipy.spatial.distance import pdist  # noqa: E402


def scipy_avg(X, cons=()):
    if len(X) < 2:
        return np.zeros(len(X), dtype=int)
    Z = linkage(pdist(np.asarray(X, dtype=np.float64), "cosine"), "average")
    return fcluster(Z, t=1.0 - E._D["avg_thr"], criterion="distance") - 1


def main():
    paths, X, N = D.load_set("lfw_clean")
    y = np.array([q.split("/")[0] for q in paths])
    base_c = build(X, N, T.P, True)
    lab0 = base_c.labels()
    cons = []
    while len(cons) < 10:
        k = pick_correction(lab0, y, X, set(cons))
        if k is None:
            break
        cons.append(k)
    del base_c
    out = {"rows": {}}
    rng = np.random.RandomState(29)
    for copies in (1, 2, 4, 6):
        Xs = [X]
        for _ in range(copies - 1):
            Q, _ = np.linalg.qr(rng.randn(X.shape[1], X.shape[1]))
            Xs.append((X @ Q).astype("float32"))
        XX = np.concatenate(Xs)
        NN = np.concatenate([N] * copies)
        n = len(XX)
        row = {"faces": int(n)}
        t0 = time.perf_counter()
        c = build(XX, NN, T.P, True)
        row["build_s"] = time.perf_counter() - t0
        for kk in (0, 10):
            cs = cons[:kk]
            c.must, c.cannot = set(), set()
            for kind, a, b in cs:
                (c.add_must_link if kind == "must" else c.add_cannot_link)(a, b)
            _, row[f"ours_{kk}_s"] = T.timed(c.labels)
            _, row[f"cavg_cached_{kk}_s"] = T.timed(lambda: F.decomposed(XX, cs, F.c_avg_fast))
            if kk == 0:
                _, row["scipy_avg_0_s"] = T.timed(lambda: F.decomposed(XX, [], scipy_avg))
            print(n, kk, {a: (round(b, 2) if isinstance(b, float) else b) for a, b in row.items()}, flush=True)
        out["rows"][str(n)] = row
        del c, XX, NN, Xs
    save_json("exp29_scaling_edgeface_s.json", {"protocol": __doc__, **out})


if __name__ == "__main__":
    main()
