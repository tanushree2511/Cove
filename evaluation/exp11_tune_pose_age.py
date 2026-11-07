"""Experiment 11 - re-tune our method with POSE and AGE tuning data added (still never touching the test sets).

Tuning data
  * the exp10 data: 30 seed-1 LFW personal libraries x 7 image conditions          -> mean ARI
  * AgeDB-30 (age gaps, 440 people)  and  CFP-FP (frontal vs profile, 500 people)  -> PAIR accuracy:
    every image of the set is clustered once; each of the official labelled pairs (3000 same / 3000-3500 different)
    is scored correct when "same person" pairs land in one cluster and "different person" pairs in different ones.
    The pairs are exact ground truth, so no identity labels have to be guessed. Pairs whose image had no detectable
    face count as "not together" (identical for every configuration).
Held-out TEST sets (CALFW, CPLFW, the seed-0 libraries, look-alike libraries) are not read here.
Selection rule fixed in advance: maximise the mean of (LFW-library ARI, AgeDB pair accuracy, CFP-FP pair accuracy).
Output: results/exp11_tuned_config.json
"""
import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import DS, be_nice, load_json, measure_worker_gb, plan_parallelism, save_json, single_thread_worker  # noqa: E402
be_nice()
import exp10_tune_robust as e10  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402
from exp7_order_stability import stable  # noqa: E402
from exp9_hard import SUFFIX, TAG, load_set  # noqa: E402

PAIRSETS = {"agedb": ("tune_agedb", "agedb_30"), "cfpfp": ("tune_cfpfp", "cfp_fp")}
# COVE_GRID_SHIFT moves every similarity threshold by a constant, for recognisers whose cosine scale differs from
# w600k_mbf (EdgeFace-S: random-pair 99th percentile on the AgeDB/CFP-FP *tuning* pairs is ~0.10 higher).
SHIFT = float(os.environ.get("COVE_GRID_SHIFT", "0"))
GRID = [dict(link=round(l + SHIFT, 3), m=m, attach=round(a + SHIFT, 3), merge=round(g + SHIFT, 3), qpct=None, qmin=None)
        for l in (0.40, 0.45, 0.50) for m in (1, 2) for a in (0.25, 0.30, 0.35, 0.40)
        for g in (0.30, 0.35, 0.40, 0.45)]
if os.environ.get("COVE_GRID") == "wide":            # one wide absolute grid, identical for every recogniser
    GRID = [dict(link=l, m=m, attach=a, merge=g, qpct=None, qmin=None)
            for l in (0.45, 0.50, 0.55, 0.60, 0.65, 0.70) for m in (1, 2)
            for a in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55) if a <= l
            for g in (0.40, 0.45, 0.50, 0.55, 0.60)]
_P = {}


def _init():
    e10._init()
    for k, (emb, folder) in PAIRSETS.items():
        s = load_set(emb)
        pos = {p: i for i, p in enumerate(s["paths"])}
        with open(os.path.join(DS, "hardtune", folder, "pairs.csv")) as f:
            rows = list(csv.DictReader(f))
        a = np.array([pos.get(r["a"], -1) for r in rows]); b = np.array([pos.get(r["b"], -1) for r in rows])
        _P[k] = (s["X"], s["N"], a, b, np.array([int(r["same"]) for r in rows]))


def pair_accuracy(lab, a, b, same):
    ok = (a >= 0) & (b >= 0)
    together = np.zeros(len(a), dtype=bool)
    together[ok] = lab[a[ok]] == lab[b[ok]]
    return float((together == (same == 1)).mean()), float(together[same == 1].mean()), float((~together[same == 0]).mean())


def _eval(cfg):
    r = e10._eval(cfg)
    out = {**cfg, "lfw_ARI": r["ARI_mean"], "lfw_F1": r["F1_mean"], "lfw_per_condition": r["per_condition"]}
    for k, (X, N, a, b, same) in _P.items():
        acc, tpr, tnr = pair_accuracy(stable(X, N, cfg), a, b, same)
        out[f"{k}_pair_acc"], out[f"{k}_same_kept"], out[f"{k}_diff_kept_apart"] = acc, tpr, tnr
    out["score"] = float(np.mean([out["lfw_ARI"], out["agedb_pair_acc"], out["cfpfp_pair_acc"]]))
    return out


def main():
    e10.build_shared()
    gb = measure_worker_gb(_eval, GRID[0], initializer=_init)
    workers, _ = plan_parallelism(gb, threads_per_worker=1)
    print(f"{len(GRID)} configurations; {gb:.2f} GB/worker -> {workers} workers", flush=True)
    rows = []
    with ProcessPoolExecutor(workers, initializer=_init) as pool:
        for r in pool.map(_eval, GRID):
            rows.append(r)
    rows.sort(key=lambda r: -r["score"])
    for r in rows[:8]:
        print(f"  link {r['link']} m {r['m']} attach {r['attach']} merge {r['merge']} | score {r['score']:.4f} "
              f"lfwARI {r['lfw_ARI']:.4f} agedb {r['agedb_pair_acc']:.4f} cfpfp {r['cfpfp_pair_acc']:.4f}", flush=True)
    prev = load_json("exp10_tuned_config.json")["config"] if not SUFFIX else {"link": -1, "m": -1, "attach": -1, "merge": -1}
    pr = next((r for r in rows if all(r[k] == prev[k] for k in ("link", "m", "attach", "merge"))), None)
    if pr:
        print(f"  (v2 config for comparison: score {pr['score']:.4f} lfwARI {pr['lfw_ARI']:.4f} "
              f"agedb {pr['agedb_pair_acc']:.4f} cfpfp {pr['cfpfp_pair_acc']:.4f})", flush=True)
    best = rows[0]
    cfg = {k: best[k] for k in ("link", "m", "attach", "merge", "qpct", "qmin")}
    print("CHOSEN:", cfg, flush=True)
    save_json(f"exp11_tuned_config{SUFFIX}{TAG}.json", {"config": cfg, "selected_on": "seed-1 LFW libraries x 7 conditions (ARI) + AgeDB-30 and CFP-FP pair accuracy",
                                          "grid": rows})
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
