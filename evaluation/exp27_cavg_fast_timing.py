"""Experiment 27 - constrained average linkage with a fast (row-maximum cache) implementation (round-4 review, DA M1).

exp24 timed constrained average linkage with the authors' dense NumPy loop (cubic: a full argmax over the k x k matrix at every
merge). Round-4 reviewers pointed out that part of the 261 s vs 1.3 s gap is that implementation. Here the same algorithm keeps
the best partner of every row, so one merge costs O(k) instead of O(k^2). Same tie-breaking, so the output must equal the slow
version; checked on the 1,658 and 3,316 subsets. Same data, thresholds, subsets and corrections as exp24; one thread.
Run: python evaluation/exp27_cavg_fast_timing.py
"""
import os
import sys
import time

os.environ["COVE_FACE_MODEL"] = "edgeface_s"
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
import exp24_cavg_timing as T  # noqa: E402
import exp19_correction_baselines as E  # noqa: E402
from common import save_json  # noqa: E402
from exp15_corrections import pick_correction  # noqa: E402
from exp20_exact_read import build, canon  # noqa: E402
import exp14_disjoint as D  # noqa: E402


def c_avg_fast(X, cons=()):
    n = len(X)
    Xo = np.asarray(X, dtype=np.float64)
    Xo = Xo / np.linalg.norm(Xo, axis=1, keepdims=True)
    par = list(range(n))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    cannot = [(a, b) for k, a, b in cons if k == "cannot"]
    musts = sorted(((a, b) for k, a, b in cons if k == "must"), key=lambda p: -float(Xo[p[0]] @ Xo[p[1]]))
    for a, b in musts:
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
            if any(find(x) == find(y) for x, y in cannot):
                par[ra] = ra
    roots = np.array([find(i) for i in range(n)])
    _, lab = np.unique(roots, return_inverse=True)
    k = lab.max() + 1
    A = np.zeros((k, Xo.shape[1]))
    np.add.at(A, lab, Xo)
    size = np.bincount(lab, minlength=k).astype(np.float64)
    S = (A @ A.T) / np.outer(size, size)
    bad = np.zeros((k, k), dtype=bool)
    for a, b in cannot:
        bad[lab[a], lab[b]] = bad[lab[b], lab[a]] = True
    np.fill_diagonal(bad, True)
    S[bad] = -np.inf
    rarg = S.argmax(1)
    rmax = S[np.arange(k), rarg]
    grp = np.arange(k)
    thr = E._D["avg_thr"]
    while True:
        a = int(np.argmax(rmax))
        if rmax[a] < thr:
            break
        b = int(rarg[a])
        a, b = min(a, b), max(a, b)
        A[a] += A[b]
        size[a] += size[b]
        bad[a] |= bad[b]
        bad[:, a] = bad[a]
        row = (A @ A[a]) / (size * size[a])
        row[bad[a]] = -np.inf
        S[a, :] = row
        S[:, a] = row
        S[b, :] = -np.inf
        S[:, b] = -np.inf
        bad[b, :] = True
        bad[:, b] = True
        rmax[b] = -np.inf
        rarg[b] = 0
        stale = np.nonzero((rarg == a) | (rarg == b))[0]
        stale = stale[rmax[stale] > -np.inf]
        for r in np.union1d(stale, [a]):
            rarg[r] = int(S[r].argmax())
            rmax[r] = S[r, rarg[r]]
        # a changed row can now beat other rows' best
        better = row > rmax
        better[b] = False
        better[a] = False
        idx = np.nonzero(better)[0]
        rarg[idx] = a
        rmax[idx] = row[idx]
        grp[grp == b] = a
    return np.unique(grp[lab], return_inverse=True)[1]


def decomposed(X, cons, fn):
    old = E.c_avg
    E.c_avg = fn
    try:
        return T.c_avg_decomposed(X, cons)
    finally:
        E.c_avg = old


def main():
    paths, X, N = D.load_set("lfw_clean")
    y = np.array([q.split("/")[0] for q in paths])
    out = {"rows": {}}
    for n in (1658, 3316, 8290):
        idx = np.sort(np.random.RandomState(24).permutation(len(X))[:n]) if n < len(X) else np.arange(len(X))
        Xs, Ns, ys = X[idx], N[idx], y[idx]
        c = build(Xs, Ns, T.P, True)
        lab = c.labels()
        cons = []
        while len(cons) < 10:
            k = pick_correction(lab, ys, Xs, set(cons))
            if k is None:
                break
            cons.append(k)
        row = {"faces": n}
        for kk in (0, 10):
            cs = cons[:kk]
            c.must, c.cannot = set(), set()
            for kind, a, b in cs:
                (c.add_must_link if kind == "must" else c.add_cannot_link)(a, b)
            _, row[f"ours_{kk}_s"] = T.timed(c.labels)
            fast, row[f"cavg_fast_{kk}_s"] = T.timed(lambda: decomposed(Xs, cs, c_avg_fast))
            if n <= 3316:
                slow = E.c_avg(Xs, cs)
                row[f"fast_equals_slow_{kk}"] = bool(np.array_equal(canon(slow), canon(fast)))
            print(n, kk, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in row.items()}, flush=True)
        out["rows"][str(n)] = row
    save_json("exp27_cavg_fast_timing_edgeface_s.json", {"protocol": __doc__, **out})


if __name__ == "__main__":
    main()
