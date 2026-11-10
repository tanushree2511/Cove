"""Experiment 23 (E4) - do corrections survive a change of face recogniser?

Pre-declared protocol (round-4 research plan; nothing tuned; each recogniser uses its own exp14 thresholds):
  The 210 test libraries whose faces are identical across MBF and EdgeFace-S (all but the 30 look-alike libraries).
  The oracle user (exp15) makes up to 10 corrections on the "now" 80% under the OLD recogniser; the app is then
  upgraded, every face is re-embedded with the NEW recogniser, the 20% "later" faces arrive, and the stored corrections
  (pairs of faces) are applied by our clusterer under the new recogniser.
  none         new recogniser, corrections discarded
  native       new recogniser, corrections made by the same user on what the NEW recogniser showed
  transferred  new recogniser, corrections made under the OLD recogniser
Outcome: later F1 for the three; retention = (transferred - none) / (native - none) with a bootstrap CI over libraries;
share of transferred corrections that hold; no-harm check (transferred minus none, CI). Both directions are reported.
Run: python evaluation/exp23_recogniser_upgrade.py
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cove"))
from adaptive import run_adaptive  # noqa: E402
from common import CACHE, be_nice, save_json, single_thread_worker  # noqa: E402
be_nice()
from engines.stable_cluster import StableIncrementalClusterer  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402
from exp15_corrections import pick_correction  # noqa: E402

MODELS = ("mbf", "edgeface_s")
MAXK = 10
_D = {}


def _init():
    single_thread_worker()
    for mdl in MODELS:
        base = os.path.join(CACHE, f"exp14_shared_{mdl}")
        d = np.load(base + ".npz")
        b = d["bounds"]
        keys = d["keys"].tolist()
        _D[mdl] = {"X": np.load(base + "_X.npy", mmap_mode="r"), "N": d["N"], "y": d["y"],
                   "sl": {k: slice(b[i], b[i + 1]) for i, k in enumerate(keys)},
                   "cfg": json.load(open(os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{mdl}.json"),
                                         encoding="utf8"))["tuned"]["Ours"]["params"]}


def cluster(mdl, X, N, cons=()):
    p = _D[mdl]["cfg"]
    c = StableIncrementalClusterer(link_threshold=p["link"], min_neighbors=p["m"], attach_threshold=p["attach"],
                                   merge_threshold=p["merge"], dim=X.shape[1])
    for s in range(0, len(X), 64):
        c.add(X[s:s + 64], N[s:s + 64])
    for kind, a, b in cons:
        (c.add_must_link if kind == "must" else c.add_cannot_link)(a, b)
    return c.labels()


def session(mdl, Xn, Nn, yn):
    cons = []
    lab = cluster(mdl, Xn, Nn)
    for _ in range(MAXK):
        c = pick_correction(lab, yn, Xn, set(cons))
        if c is None:
            break
        cons.append(c)
        lab = cluster(mdl, Xn, Nn, cons)
    return cons


def held(lab, cons):
    return int(sum((lab[a] == lab[b]) == (k == "must") for k, a, b in cons))


def _job(key):
    seed = int(key.split("|")[2])
    out = {}
    for old, new in (("mbf", "edgeface_s"), ("edgeface_s", "mbf")):
        so, sn = _D[old]["sl"][key], _D[new]["sl"][key]
        Xo, No, yo = np.asarray(_D[old]["X"][so]), _D[old]["N"][so], _D[old]["y"][so]
        Xw, Nw, yw = np.asarray(_D[new]["X"][sn]), _D[new]["N"][sn], _D[new]["y"][sn]
        assert len(yo) == len(yw) and (yo == yw).all()
        perm = np.random.RandomState(seed + 15000).permutation(len(yo))
        Xo, No, Xw, Nw, y = Xo[perm], No[perm], Xw[perm], Nw[perm], yo[perm]
        m = int(round(0.8 * len(y)))
        cons_old = session(old, Xo[:m], No[:m], y[:m])
        cons_new = session(new, Xw[:m], Nw[:m], y[:m])
        res = {}
        for name, cons in (("none", []), ("native", cons_new), ("transferred", cons_old)):
            lab = cluster(new, Xw, Nw, cons)
            res[name] = {"F1": evaluate(lab, y)["B3_F1"], "new_F1": evaluate(lab[m:], y[m:])["B3_F1"],
                         "n": len(cons), "held": held(lab, cons)}
        out[f"{old}->{new}"] = res
    return key, out


def main():
    t0 = time.time()
    d1, d2 = np.load(os.path.join(CACHE, "exp14_shared_mbf.npz")), np.load(os.path.join(CACHE, "exp14_shared_edgeface_s.npz"))
    keys = [k for k in d1["keys"].tolist() if k.startswith("test|") and k in set(d2["keys"].tolist())
            and not k.startswith("test|lookalike")]
    if len(sys.argv) > 1:
        keys = keys[:int(sys.argv[1])]
    rows = dict(run_adaptive(_job, keys, initializer=_init, name="UPGRADE", per_step=4))
    table = {}
    rs = np.random.RandomState(0)
    for dirn in ("mbf->edgeface_s", "edgeface_s->mbf"):
        v = [r[dirn] for r in rows.values()]
        f = {s: np.array([x[s]["F1"] for x in v]) for s in ("none", "native", "transferred")}
        idx = rs.randint(0, len(v), (10000, len(v)))
        ret = [(f["transferred"][i].mean() - f["none"][i].mean()) / (f["native"][i].mean() - f["none"][i].mean())
               for i in idx]
        harm = (f["transferred"][idx] - f["none"][idx]).mean(1)
        nc = sum(x["transferred"]["n"] for x in v)
        table[dirn] = {"libraries": len(v), "F1_none": float(f["none"].mean()), "F1_native": float(f["native"].mean()),
                       "F1_transferred": float(f["transferred"].mean()),
                       "new_F1_none": float(np.mean([x["none"]["new_F1"] for x in v])),
                       "new_F1_native": float(np.mean([x["native"]["new_F1"] for x in v])),
                       "new_F1_transferred": float(np.mean([x["transferred"]["new_F1"] for x in v])),
                       "retention": float((f["transferred"].mean() - f["none"].mean()) / (f["native"].mean() - f["none"].mean())),
                       "retention_ci95": [float(np.nanpercentile(ret, 2.5)), float(np.nanpercentile(ret, 97.5))],
                       "gain_over_none": float((f["transferred"] - f["none"]).mean()),
                       "gain_over_none_ci95": [float(np.percentile(harm, 2.5)), float(np.percentile(harm, 97.5))],
                       "transferred_corrections": nc,
                       "transferred_held_share": sum(x["transferred"]["held"] for x in v) / nc if nc else None}
        print(dirn, {k: (round(a, 4) if isinstance(a, float) else a) for k, a in table[dirn].items()}, flush=True)
    if len(sys.argv) > 1:
        return
    save_json("exp23_recogniser_upgrade.json", {"protocol": __doc__, "table": table, "per_library": rows,
                                               "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
