"""Experiment 25 (E5) - user effort, and how much user error the corrections can take.

Pre-declared protocol (round-4 plan; exp14 thresholds, exp14 test libraries, nothing tuned):
  The casual user of exp19 (random faces of the two people involved) works on the "now" 80% of a library with up to 10
  corrections, always aimed at the biggest remaining mistake. With probability p each correction is instead a WRONG
  "same person" between look-alike clusters (exp19's wrong_merge). p in {0, 0.02, 0.05, 0.10, 0.20}.
  Methods: ours, ours+reapply, c-avg (the same sessions as exp19).
Outcomes per method and p:
  - F1 of "now" after k = 0..10 corrections (mean over libraries), and the corrections needed to reach F1 >= 0.99 on "now"
    (libraries that start below 0.99; share reaching it, median corrections among those that do);
  - F1 after the "later" 20% arrive, against the same corrections thrown away ("lost"): gain = later - lost, with a 95% CI
    (bootstrap over libraries). The break-even error rate is the smallest p whose CI includes or falls below zero.
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp25_effort.py
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

RATES = (0.0, 0.02, 0.05, 0.10, 0.20)
SESS = ("ours", "ours+reapply", "c-avg")
TARGET = 0.99


def _job(key):
    sl = E._D["sl"][key]
    X, N, y = np.asarray(E._D["X"][sl]), E._D["N"][sl], E._D["y"][sl]
    seed = int(key.split("|")[2])
    perm = np.random.RandomState(seed + 15000).permutation(len(X))
    X, N, y = X[perm], N[perm], y[perm]
    m = int(round(0.8 * len(X)))
    Xn, Nn, yn = X[:m], N[:m], y[:m]
    out = {}
    for pi, p in enumerate(RATES):
        for s in SESS:
            rng = np.random.RandomState(seed * 100 + 50 + pi)
            cons = []
            lab = E.run(s, Xn, Nn, cons)
            curve = [evaluate(lab, yn)["B3_F1"]]
            for _ in range(E.MAXK):
                c = None
                if rng.rand() < p:
                    c = E.wrong_merge(lab, yn, Xn, set(cons), rng)
                if c is None:
                    c = E.biggest_mistake(lab, yn, Xn, set(cons), "casual", rng)
                if c is None:
                    break
                cons.append(c)
                lab = E.run(s, Xn, Nn, cons)
                curve.append(evaluate(lab, yn)["B3_F1"])
            curve += [curve[-1]] * (E.MAXK + 1 - len(curve))
            later = E.run(s, X, N, cons)
            base = E.ours(X, N) if s != "c-avg" else E.avg(X)
            out[f"{p}|{s}"] = {"curve": curve, "n": len(cons), "later_F1": evaluate(later, y)["B3_F1"],
                               "lost_F1": evaluate(base, y)["B3_F1"], "held": E.held(later, cons)}
    return key, out


def summarise(rows):
    rs = np.random.RandomState(0)
    table = {}
    for p in RATES:
        for s in SESS:
            v = [r[f"{p}|{s}"] for r in rows.values()]
            curves = np.array([x["curve"] for x in v])
            start = curves[:, 0] < TARGET
            reach = [int(np.argmax(c >= TARGET)) for c in curves[start] if (c >= TARGET).any()]
            gain = np.array([x["later_F1"] - x["lost_F1"] for x in v])
            bm = gain[rs.randint(0, len(gain), (10000, len(gain)))].mean(1)
            table[f"{p}|{s}"] = {
                "mean_curve": [float(a) for a in curves.mean(0)],
                "libs_below_target_at_start": int(start.sum()),
                "share_reaching_target": float(len(reach) / start.sum()) if start.sum() else None,
                "median_corrections_to_target": float(np.median(reach)) if reach else None,
                "later_F1": float(np.mean([x["later_F1"] for x in v])),
                "gain_over_discarding": float(gain.mean()),
                "gain_ci95": [float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))]}
    return table


def main():
    t0 = time.time()
    keys = [k for k in np.load(E.SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    if len(sys.argv) > 1:
        keys = keys[:int(sys.argv[1])]
    rows = dict(run_adaptive(_job, keys, initializer=E._init, name="EFFORT", per_step=4))
    table = summarise(rows)
    for k, e in table.items():
        print(k, "reach", e["share_reaching_target"] and round(e["share_reaching_target"], 3), "median",
              e["median_corrections_to_target"], "later", round(e["later_F1"], 4),
              "gain", round(e["gain_over_discarding"], 4), [round(a, 4) for a in e["gain_ci95"]], flush=True)
    if len(sys.argv) > 1:
        return
    save_json(f"exp25_effort_{E.MODEL}.json", {"model": E.MODEL, "protocol": __doc__, "table": table,
                                               "per_library": rows, "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
