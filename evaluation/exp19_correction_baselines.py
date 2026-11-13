"""Experiment 19 - fair baselines for user corrections, and less-than-perfect users (review round 2).

Round-2 review: exp15 compared "corrections inside our clusterer" only with "corrections thrown away", and
with a perfect simulated user. Here every method that KEEPS corrections is compared, each with its own user
session on its own "now" clustering (the user fixes what that method shows them):
  ours          corrections inside our clusterer (must-/cannot-link constraints; this work)
  ours+reapply  our clusterer WITHOUT constraints, then the stored corrections re-applied afterwards:
                a cannot-linked pair in one cluster -> split that cluster by which of the two faces each member is
                more similar to; a must-linked pair in two clusters -> merge them unless that joins a cannot-linked
                pair (the reviewer's trivial baseline, as specified in round-2 R_DA.md)
  avg+reapply   average linkage (exp14-tuned threshold), then the same re-apply step
  c-avg         constrained average linkage (Davidson & Ravi 2005): must-link groups first, then average-linkage
                merges that never join a cannot-linked pair; same exp14-tuned threshold
  and, as references, ours-lost / avg-lost: corrections made "now" but thrown away when the library re-clusters.
Nothing is tuned here: thresholds are exp14's (tuning half), libraries are exp14's TEST libraries.

Users (each makes up to 10 corrections on "now", always aimed at the biggest remaining mistake):
  oracle  exp15's user: central face of the main person, intruder face most like them (best case for cuts)
  casual  the same mistake, but the two faces clicked are random faces of the two people involved
  noisy   casual, and each correction is, with probability 0.1, a WRONG "same person" between random faces of the
          two most similar clusters that hold different people (a look-alike merge)
Per library and method: F1 on "now" after the corrections, F1 after the "later" 20% arrive (all faces and the new
faces only), and how many of the user's corrections still hold (counted per correction, so libraries without
corrections add nothing). Order check (oracle user): photos inserted in 3 random orders, min ARI to the original.
Run: COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp19_correction_baselines.py
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
from exp15_corrections import pick_correction  # noqa: E402

MODEL = os.environ.get("COVE_FACE_MODEL")
assert MODEL in ("mbf", "edgeface_s"), "set COVE_FACE_MODEL=mbf or edgeface_s"
TAG = os.environ.get("COVE_TAG", "")                     # "" = the paper's LFW run; "_fiw" = exp31 outside-data run
SHARED = os.path.join(CACHE, f"exp14_shared_{MODEL}{TAG}")
TUNED = os.environ.get("COVE_TUNED") or os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json")
MAXK = 10
USERS = ("oracle", "casual", "noisy")
SESSIONS = ("ours", "ours+reapply", "avg+reapply", "c-avg")
_D = {}


def _init():
    single_thread_worker()
    d = np.load(SHARED + ".npz")
    _D["X"] = np.load(SHARED + "_X.npy", mmap_mode="r")
    _D["N"], _D["y"], b = d["N"], d["y"], d["bounds"]
    _D["sl"] = {k: slice(b[i], b[i + 1]) for i, k in enumerate(d["keys"].tolist())}
    t = json.load(open(TUNED, encoding="utf8"))["tuned"]
    _D["cfg"], _D["avg_thr"] = t["Ours"]["params"], t["Agglomerative (avg)"]["params"]["thr"]


# ----------------------------------------------------------------------------------------------- methods
def ours(X, N, cons=(), order=None):
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


def c_avg(X, cons=(), order=None):
    """Average linkage on cosine similarity (stop below the tuned threshold) with must-/cannot-link constraints.
    Without constraints this equals sklearn AgglomerativeClustering(linkage='average', metric='cosine')."""
    n = len(X)
    order = np.arange(n) if order is None else order
    inv = np.empty(n, dtype=int)
    inv[order] = np.arange(n)
    Xo = np.asarray(X[order], dtype=np.float64)
    Xo /= np.linalg.norm(Xo, axis=1, keepdims=True)
    cs = [(k, inv[a], inv[b]) for k, a, b in cons]
    par = list(range(n))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    cannot = [(a, b) for k, a, b in cs if k == "cannot"]
    musts = sorted(((a, b) for k, a, b in cs if k == "must"), key=lambda p: -float(Xo[p[0]] @ Xo[p[1]]))
    for a, b in musts:                                    # must-link groups; a cannot-link always wins
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
    grp = np.arange(k)
    thr = _D["avg_thr"]
    while True:
        f = int(np.argmax(S))
        a, b = divmod(f, k)
        if S[a, b] < thr:
            break
        a, b = min(a, b), max(a, b)                       # b joins a
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
        grp[grp == b] = a
    out = np.unique(grp[lab], return_inverse=True)[1]
    return out[inv]


def avg(X, order=None):
    return c_avg(X, (), order)


def reapply(lab, cons, X):
    """Re-apply stored corrections to a clustering that ignored them (round-2 DA's 'split' baseline)."""
    lab = lab.copy()
    nxt = lab.max() + 1
    Xu = X / np.linalg.norm(X, axis=1, keepdims=True)
    for k, a, b in cons:
        if k == "cannot" and lab[a] == lab[b]:
            idx = np.where(lab == lab[a])[0]
            side_b = idx[(Xu[idx] @ Xu[b]) > (Xu[idx] @ Xu[a])]
            lab[side_b] = nxt
            nxt += 1
    for k, a, b in cons:
        if k == "must" and lab[a] != lab[b]:
            trial = lab.copy()
            trial[trial == lab[b]] = lab[a]
            if all(trial[x] != trial[y] for kk, x, y in cons if kk == "cannot"):
                lab = trial
    return np.unique(lab, return_inverse=True)[1]


def run(session, X, N, cons, order=None):
    if session == "ours":
        return ours(X, N, cons, order)
    if session == "ours+reapply":
        return reapply(ours(X, N, (), order), cons, X)
    if session == "avg+reapply":
        return reapply(avg(X, order), cons, X)
    if session == "c-avg":
        return c_avg(X, cons, order)
    raise ValueError(session)


# ----------------------------------------------------------------------------------------------- users
def biggest_mistake(lab, y, X, done, user, rng):
    """Same choice of mistake as exp15 (most wrongly grouped pairs); the faces clicked depend on the user."""
    if user == "oracle":
        return pick_correction(lab, y, X, done)           # exactly exp15's user
    best = None
    for c in np.unique(lab):
        idx = np.where(lab == c)[0]
        cnt = Counter(y[idx]).most_common()
        if len(cnt) < 2:
            continue
        P = idx[y[idx] == cnt[0][0]]
        for q, nq in cnt[1:]:
            Q = idx[y[idx] == q]
            if best is None or len(P) * nq > best[0]:
                best = (len(P) * nq, "cannot", P, Q)
    for person in np.unique(y):
        idx = np.where(y == person)[0]
        cnt = Counter(lab[idx]).most_common(2)
        if len(cnt) < 2:
            continue
        A, B = idx[lab[idx] == cnt[0][0]], idx[lab[idx] == cnt[1][0]]
        if best is None or len(A) * len(B) > best[0]:
            best = (len(A) * len(B), "must", A, B)
    if best is None:
        return None
    _, kind, P, Q = best
    for _ in range(20):
        a, b = int(rng.choice(P)), int(rng.choice(Q))
        key = (kind, min(a, b), max(a, b))
        if key not in done:
            return key
    return None


def wrong_merge(lab, y, X, done, rng):
    """A look-alike mistake: 'same person' between random faces of the two most similar clusters whose main
    people differ."""
    ids = [c for c in np.unique(lab) if (lab == c).sum() >= 2]
    if len(ids) < 2:
        return None
    major = {c: Counter(y[lab == c]).most_common(1)[0][0] for c in ids}
    C = np.stack([X[lab == c].mean(0) for c in ids])
    C /= np.linalg.norm(C, axis=1, keepdims=True)
    S = C @ C.T
    np.fill_diagonal(S, -np.inf)
    for f in np.argsort(-S, axis=None)[:50]:
        i, j = divmod(int(f), len(ids))
        if major[ids[i]] == major[ids[j]]:
            continue
        a = int(rng.choice(np.where(lab == ids[i])[0]))
        b = int(rng.choice(np.where(lab == ids[j])[0]))
        key = ("must", min(a, b), max(a, b))
        if key not in done:
            return key
    return None


def held(lab, cons):
    return int(sum((lab[a] == lab[b]) == (k == "must") for k, a, b in cons))


# ----------------------------------------------------------------------------------------------- job
def _job(key):
    sl = _D["sl"][key]
    X, N, y = np.asarray(_D["X"][sl]), _D["N"][sl], _D["y"][sl]
    seed = int(key.split("|")[2])
    perm = np.random.RandomState(seed + 15000).permutation(len(X))   # exp15's now/later split
    X, N, y = X[perm], N[perm], y[perm]
    m = int(round(0.8 * len(X)))
    Xn, Nn, yn = X[:m], N[:m], y[:m]
    out = {"faces_now": m, "faces_total": len(X)}
    t0 = time.perf_counter()
    for ui, user in enumerate(USERS):
        for session in SESSIONS:
            rng = np.random.RandomState(seed * 100 + ui)          # same clicks for every method's user
            cons = []
            lab = run(session, Xn, Nn, cons)
            f0 = evaluate(lab, yn)["B3_F1"]
            for _ in range(MAXK):
                c = None
                if user == "noisy" and rng.rand() < 0.1:
                    c = wrong_merge(lab, yn, Xn, set(cons), rng)
                if c is None:
                    c = biggest_mistake(lab, yn, Xn, set(cons), user, rng)
                if c is None:
                    break
                cons.append(c)
                lab = run(session, Xn, Nn, cons)
            r = {"n": len(cons), "now_k0": f0, "now_k": evaluate(lab, yn)["B3_F1"],
                 "n_wrong": int(sum(yn[a] != yn[b] for k, a, b in cons if k == "must")
                                + sum(yn[a] == yn[b] for k, a, b in cons if k == "cannot"))}
            later = run(session, X, N, cons)
            r["later_F1"] = evaluate(later, y)["B3_F1"]
            r["later_new_F1"] = evaluate(later[m:], y[m:])["B3_F1"]
            r["held"] = held(later, cons)
            base = ours(X, N) if session in ("ours", "ours+reapply") else avg(X)
            r["lost_F1"] = evaluate(base, y)["B3_F1"]                  # same corrections, thrown away
            r["lost_new_F1"] = evaluate(base[m:], y[m:])["B3_F1"]
            r["lost_held"] = held(base, cons)
            if user == "oracle":
                from sklearn.metrics import adjusted_rand_score
                r["order_agreement_min"] = float(min(
                    adjusted_rand_score(later, run(session, X, N, cons, np.random.RandomState(700 + t)
                                                   .permutation(len(X)))) for t in range(3)))
            out[f"{user}|{session}"] = r
    out["seconds"] = time.perf_counter() - t0
    return key, out


def boot(a, b, n=10000, seed=0):
    d = np.asarray(a) - np.asarray(b)
    r = np.random.RandomState(seed)
    mm = d[r.randint(0, len(d), (n, len(d)))].mean(1)
    return {"diff": float(d.mean()), "ci95": [float(np.percentile(mm, 2.5)), float(np.percentile(mm, 97.5))]}


def summarise(rows):
    by = {}
    for k, r in rows.items():
        by.setdefault(k.split("|")[1], []).append(r)
    table = {}
    for cond, rs in [("ALL", list(rows.values()))] + sorted(by.items()):
        t = {}
        for user in USERS:
            for s in SESSIONS:
                v = [r[f"{user}|{s}"] for r in rs]
                nc = sum(x["n"] for x in v)
                e = {"corrections": nc, "mean_corrections": float(np.mean([x["n"] for x in v])),
                     "libs_with_corrections": int(sum(x["n"] > 0 for x in v)),
                     "wrong_corrections": int(sum(x["n_wrong"] for x in v)),
                     "now_k0": float(np.mean([x["now_k0"] for x in v])), "now_k": float(np.mean([x["now_k"] for x in v])),
                     "later_F1": float(np.mean([x["later_F1"] for x in v])),
                     "later_new_F1": float(np.mean([x["later_new_F1"] for x in v])),
                     "lost_F1": float(np.mean([x["lost_F1"] for x in v])),
                     "lost_new_F1": float(np.mean([x["lost_new_F1"] for x in v])),
                     "held_share": sum(x["held"] for x in v) / nc if nc else None,
                     "lost_held_share": sum(x["lost_held"] for x in v) / nc if nc else None}
                if user == "oracle":
                    e["order_agreement_min"] = float(min(x["order_agreement_min"] for x in v))
                if s != "ours":
                    e["ours_minus_this_later_F1"] = boot([r[f"{user}|ours"]["later_F1"] for r in rs],
                                                         [x["later_F1"] for x in v])
                t[f"{user}|{s}"] = e
        table[cond] = t
    return table


def main():
    t0 = time.time()
    keys = [k for k in np.load(SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    if len(sys.argv) > 1:                                   # quick check: first N libraries
        keys = keys[:int(sys.argv[1])]
    rows = dict(run_adaptive(_job, keys, initializer=_init, name="CORR-BASELINES", per_step=4))
    table = summarise(rows)
    for user in USERS:
        for s in SESSIONS:
            e = table["ALL"][f"{user}|{s}"]
            print(f"{user:6} {s:13} corr {e['mean_corrections']:.1f} wrong {e['wrong_corrections']:3d} | now "
                  f"{e['now_k0']:.4f}->{e['now_k']:.4f} | later {e['later_F1']:.4f} (lost {e['lost_F1']:.4f}) new "
                  f"{e['later_new_F1']:.4f} | held {e['held_share']:.3f} (lost {e['lost_held_share']:.3f})"
                  + (f" | order {e['order_agreement_min']:.4f}" if "order_agreement_min" in e else ""), flush=True)
    if len(sys.argv) > 1:
        return
    save_json(f"exp19_correction_baselines_{MODEL}{TAG}.json", {
        "model": MODEL, "protocol": __doc__, "config": {"ours": _cfg(), "avg_thr": _thr()},
        "table": table, "per_library": rows, "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


def _cfg():
    return json.load(open(TUNED, encoding="utf8"))["tuned"]["Ours"]["params"]


def _thr():
    return json.load(open(TUNED, encoding="utf8"))["tuned"]["Agglomerative (avg)"]["params"]["thr"]


if __name__ == "__main__":
    main()
