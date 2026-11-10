"""Experiment 20 (E1) - is the fast read-time step exact, and how much faster is it?

Pre-declared gate (round-4 research plan): the fast centroid merge (threshold-graph decomposition + blocked
similarity) must give IDENTICAL partitions to the reference merge on every test library, with and without user
corrections. Pass = zero partition differences. Nothing is tuned: thresholds are exp14's tuning-half values.

Part A  exactness: all test libraries of the shared exp14 set, both recognisers' thresholds as shipped.
        unconstrained, and with 12 corrections (6 correct must, 4 correct cannot, 2 wrong must) from fixed seeds.
Part B  timing: 8,290 clean LFW faces (as exp18), one thread, labels() reference vs fast, unconstrained and with 10 and
        50 corrections; plus constrained average linkage (exp19's c_avg) timed once on the same data.
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp20_exact_read.py [A|B]
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cove"))
from common import CACHE, be_nice, save_json, single_thread_worker  # noqa: E402
be_nice()
from adaptive import run_adaptive  # noqa: E402
from engines.stable_cluster import StableIncrementalClusterer  # noqa: E402

MODEL = os.environ.get("COVE_FACE_MODEL", "edgeface_s")
SHARED = os.path.join(CACHE, f"exp14_shared_{MODEL}")
TUNED = os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json")
_D = {}


def _init():
    single_thread_worker()
    d = np.load(SHARED + ".npz")
    _D["X"] = np.load(SHARED + "_X.npy", mmap_mode="r")
    _D["N"], _D["y"], b = d["N"], d["y"], d["bounds"]
    _D["sl"] = {k: slice(b[i], b[i + 1]) for i, k in enumerate(d["keys"].tolist())}
    _D["cfg"] = json.load(open(TUNED, encoding="utf8"))["tuned"]["Ours"]["params"]


def canon(lab):
    """Partition in canonical form (label = order of first appearance) so equal partitions compare equal."""
    seen, out = {}, np.empty(len(lab), dtype=int)
    for i, v in enumerate(lab.tolist()):
        out[i] = seen.setdefault(v, len(seen))
    return out


def build(X, N, p, fast):
    c = StableIncrementalClusterer(link_threshold=p["link"], min_neighbors=p["m"], attach_threshold=p["attach"],
                                   merge_threshold=p["merge"], dim=X.shape[1], fast_merge=fast)
    for s in range(0, len(X), 64):
        c.add(X[s:s + 64], N[s:s + 64])
    return c


def make_cons(y, seed):
    r = np.random.RandomState(seed)
    n = len(y)
    cons = []
    for _ in range(40):
        a, b = int(r.randint(n)), int(r.randint(n))
        if a == b:
            continue
        kind = "must" if y[a] == y[b] else "cannot"
        if kind == "must" and sum(k == "must" and y[p] == y[q] for k, p, q in cons) >= 6:
            continue
        if kind == "cannot" and sum(k == "cannot" for k, p, q in cons) >= 4:
            continue
        cons.append((kind, a, b))
    wrong = 0
    while wrong < 2:                                     # two wrong "same person" clicks
        a, b = int(r.randint(n)), int(r.randint(n))
        if a != b and y[a] != y[b]:
            cons.append(("must", a, b))
            wrong += 1
    return cons


def _job(key):
    sl = _D["sl"][key]
    X, N, y = np.asarray(_D["X"][sl]), _D["N"][sl], _D["y"][sl]
    p = _D["cfg"]
    seed = int(key.split("|")[2])
    out = {"faces": len(X)}
    cons = make_cons(y, seed)
    for name, cs in (("plain", []), ("corrected", cons)):
        res = {}
        for fast in (False, True):
            c = build(X, N, p, fast)
            for k, a, b in cs:
                (c.add_must_link if k == "must" else c.add_cannot_link)(a, b)
            t0 = time.perf_counter()
            res[fast] = c.labels()
            out[f"{name}_{'fast' if fast else 'ref'}_s"] = time.perf_counter() - t0
        out[f"{name}_identical"] = bool(np.array_equal(canon(res[False]), canon(res[True])))
        out[f"{name}_clusters"] = int(res[True].max() + 1)
    return key, out


def part_a():
    t0 = time.time()
    keys = [k for k in np.load(SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    rows = dict(run_adaptive(_job, keys, initializer=_init, name="EXACT-READ", per_step=4))
    nplain = sum(r["plain_identical"] for r in rows.values())
    ncorr = sum(r["corrected_identical"] for r in rows.values())
    print(f"{MODEL}: libraries {len(rows)} | identical plain {nplain}/{len(rows)} | identical corrected {ncorr}/{len(rows)}",
          flush=True)
    bad = [k for k, r in rows.items() if not (r["plain_identical"] and r["corrected_identical"])]
    print("differing libraries:", bad[:10], flush=True)
    save_json(f"exp20_exact_{MODEL}.json", {"model": MODEL, "protocol": __doc__, "libraries": len(rows),
              "identical_plain": nplain, "identical_corrected": ncorr, "differing": bad, "per_library": rows,
              "seconds": time.time() - t0})


def part_b():
    single_thread_worker()
    import exp14_disjoint as E
    from exp15_corrections import pick_correction
    p = json.load(open(TUNED, encoding="utf8"))["tuned"]["Ours"]["params"]
    paths, X, N = E.load_set("lfw_clean")
    y = np.array([q.split("/")[0] for q in paths])
    out = {"faces": len(X), "config": p}
    cs = {}
    for fast in (False, True):
        c = build(X, N, p, fast)
        lab = c.labels()
        if fast is False:
            ref_lab = lab
            cons = []
            while len(cons) < 50:
                k = pick_correction(lab, y, X, set(cons))
                if k is None:
                    break
                cons.append(k)
        for kk in (0, 10, 50):
            c.must, c.cannot = set(), set()
            for kind, a, b in cons[:kk]:
                (c.add_must_link if kind == "must" else c.add_cannot_link)(a, b)
            ts = []
            for _ in range(3):
                t0 = time.perf_counter()
                l2 = c.labels()
                ts.append(time.perf_counter() - t0)
            out[f"{'fast' if fast else 'ref'}_{kk}_s"] = float(np.median(ts))
            cs[(fast, kk)] = canon(l2)
            print(f"{'fast' if fast else 'ref '} {kk:2d} corrections: {np.median(ts):.2f} s", flush=True)
    out["identical"] = {str(kk): bool(np.array_equal(cs[(False, kk)], cs[(True, kk)])) for kk in (0, 10, 50)}
    print("identical:", out["identical"], flush=True)
    save_json(f"exp20_timing_{MODEL}.json", out)


if __name__ == "__main__":
    {"A": part_a, "B": part_b}[sys.argv[1] if len(sys.argv) > 1 else "A"]()
