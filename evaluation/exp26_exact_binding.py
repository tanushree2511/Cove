"""Experiment 26 - a stronger exactness check of the fast read step, with corrections that really bind (round-5 audit, SQ1).

exp20 compared the fast and the reference read step with random corrections. Counting them showed that, per library, they were
on average 2.2 correct 'same person', 4.0 'different people' between random faces (which rarely change anything) and 2.0 wrong
'same person' - not 'twelve corrections'. Here the corrections are the ones the exp19 users make on the clusterer's own result:
  oracle  exp15's user (central face of the main person, intruder most like them)
  casual  random faces of the two people involved
  noisy   casual, and each correction is a WRONG look-alike 'same person' with probability 0.1
Each user makes up to 10 corrections, one at a time, aimed at the biggest remaining mistake, on the whole library (fast path
used to choose the next one). After 5 and after the last correction the labels of the fast path and of the reference path
(fast_merge=False, the original centroid merge) must be the same partition. Also recorded: whether the corrections changed the
partition at all (so the check is not vacuous). Pre-declared pass: zero differences. Nothing is tuned (exp14 thresholds).
Run: COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp26_exact_binding.py
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import exp19_correction_baselines as E  # noqa: E402
from adaptive import run_adaptive  # noqa: E402
from common import save_json  # noqa: E402
from exp20_exact_read import build, canon  # noqa: E402

USERS = ("oracle", "casual", "noisy")


def _job(key):
    sl = E._D["sl"][key]
    X, N, y = np.asarray(E._D["X"][sl]), E._D["N"][sl], E._D["y"][sl]
    p = E._D["cfg"]
    seed = int(key.split("|")[2])
    out = {"faces": len(X)}
    for ui, user in enumerate(USERS):
        rng = np.random.RandomState(seed * 100 + ui)
        c = build(X, N, p, True)
        lab0 = c.labels()
        base = canon(lab0)
        lab = lab0
        cons, snap = [], {}
        for step in range(1, E.MAXK + 1):
            k = None
            if user == "noisy" and rng.rand() < 0.1:
                k = E.wrong_merge(lab, y, X, set(cons), rng)
            if k is None:
                k = E.pick_correction(lab, y, X, set(cons)) if user == "oracle" else \
                    E.biggest_mistake(lab, y, X, set(cons), user, rng)
            if k is None:
                break
            cons.append(k)
            (c.add_must_link if k[0] == "must" else c.add_cannot_link)(k[1], k[2])
            lab = c.labels()
            if step == 5:
                snap[5] = (len(cons), lab.copy())
        snap["last"] = (len(cons), lab.copy())
        res = {"n": len(cons), "n_wrong": int(sum((y[a] != y[b]) if kd == "must" else (y[a] == y[b])
                                                  for kd, a, b in cons)),
               "changed_partition": bool(not np.array_equal(base, canon(lab)))}
        if cons:
            c.fast_merge = False                              # the reference read step on the SAME stored state
            ref_last = c.labels()
            res["identical_last"] = bool(np.array_equal(canon(ref_last), canon(lab)))
            if 5 in snap and snap[5][0] == len(cons):
                res["identical_5"] = res["identical_last"]
            elif 5 in snap:
                keep = (set(c.must), set(c.cannot))
                c.must = {(min(a, b), max(a, b)) for kd, a, b in cons[:snap[5][0]] if kd == "must"}
                c.cannot = {(min(a, b), max(a, b)) for kd, a, b in cons[:snap[5][0]] if kd == "cannot"}
                res["identical_5"] = bool(np.array_equal(canon(c.labels()), canon(snap[5][1])))
                c.must, c.cannot = keep
            c.fast_merge = True
        out[user] = res
    return key, out


def main():
    t0 = time.time()
    keys = [k for k in np.load(E.SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    if len(sys.argv) > 1:
        keys = keys[:int(sys.argv[1])]
    rows = dict(run_adaptive(_job, keys, initializer=E._init, name="EXACT-BINDING", per_step=4))
    table = {}
    for u in USERS:
        v = [r[u] for r in rows.values()]
        w = [x for x in v if x["n"] > 0]
        table[u] = {"libraries": len(v), "libraries_with_corrections": len(w),
                    "mean_corrections": float(np.mean([x["n"] for x in v])),
                    "libraries_where_corrections_changed_partition": int(sum(x["changed_partition"] for x in w)),
                    "identical_last": int(sum(x.get("identical_last", True) for x in w)),
                    "identical_5": int(sum(x.get("identical_5", True) for x in w)),
                    "differences": [k for k, r in rows.items() if r[u]["n"] > 0 and not (
                        r[u].get("identical_last", True) and r[u].get("identical_5", True))][:10]}
        print(u, table[u], flush=True)
    if len(sys.argv) > 1:
        return
    save_json(f"exp26_exact_binding_{E.MODEL}.json", {"model": E.MODEL, "protocol": __doc__, "table": table,
                                                      "per_library": rows, "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
