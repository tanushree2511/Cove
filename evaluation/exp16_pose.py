"""Experiment 16 - pose-aware similarity (frontal vs profile pairs get a similarity bonus before thresholding).

Signal: yaw proxy from the detector's 5 landmarks (pose_kps.py), free at run time in the app.
Rule:   s' = s + bonus * min(1, | |yaw_i| - |yaw_j| | / scale)    (engines/stable_cluster.py, pose_bonus/pose_scale)

Protocol, fixed BEFORE any test number is computed:
  * Base method = ours with the exp14 tuned configuration of the recogniser; only bonus and scale are tuned.
  * Grid: bonus in {0, 0.025, 0.05, 0.075, 0.10, 0.15}, scale in {0.5, 1.0}.
  * TUNING data only: the 30 exp14 tuning libraries x 7 conditions (mean ARI) and CFP-FP frontal-vs-profile pairs
    (pair accuracy; a separate dataset never used for testing). Score = mean of the two.
  * Decision rule: keep the best (bonus, scale) only if its score beats bonus = 0 by >= 0.002; otherwise pose is
    reported as "no gain" and not shipped.
  * TEST (once): the exp14 test libraries (8 conditions, 3 orders) and the whole CALFW / CPLFW test identities;
    paired bootstrap of the F1 difference (pose minus no pose) over libraries.
Run: COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp16_pose.py   -> results/exp16_pose_<model>.json
"""
import csv
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cove"))
import exp14_disjoint as E  # noqa: E402  (same libraries, split, model selection)
from adaptive import run_adaptive  # noqa: E402
from common import CACHE, DS, save_json, single_thread_worker  # noqa: E402
from engines.stable_cluster import StableIncrementalClusterer  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402

MODEL = E.MODEL
PSHARED = os.path.join(CACHE, f"exp16_yaw_{MODEL}.npy")
GRID = [dict(bonus=b, scale=s) for b in (0.0, 0.025, 0.05, 0.075, 0.10, 0.15) for s in (0.5, 1.0) if b or s == 1.0]
_D = {}


def pose_of(set_name):
    d = np.load(os.path.join(CACHE, f"pose_{set_name}.npz"))
    return dict(zip([p.replace("\\", "/") for p in d["paths"].tolist()], d["yaw"].tolist()))


def build_yaw():
    """Yaw for every face of the exp14 shared arrays, in exactly the same order (rebuilt with exp14's own code)."""
    sets = {k: E.load_set(f"lfw_{k}") for k in E.DEGR}
    yaw = {k: pose_of(f"lfw_{k}") for k in E.DEGR}
    by, half = E.split_identities(sets["clean"][0])
    pos = {k: {p: i for i, p in enumerate(sets[k][0])} for k in E.DEGR}
    out, miss = [], 0

    def g(k, f):
        nonlocal miss
        if f not in yaw[k]:
            miss += 1
        return yaw[k].get(f, 0.0)
    for split, seed in (("tune", 1), ("test", 0)):
        libs = E.make_libs(by, *half[split], seed=seed)
        for k in E.DEGR:
            for lf in libs:
                out += [g(k, f) for f in lf if f in pos[k]]
        for li, lf in enumerate(libs):
            rng = np.random.RandomState((1900 if split == "tune" else 900) + li)
            out += [g(k, f) for f in lf for k in [E.DEGR[rng.randint(len(E.DEGR))]] if f in pos[k]]
    test_ids = set(half["test"][0]) | set(half["test"][1])
    for lf in E.lookalike_libs(by, test_ids, sets["clean"][1], pos["clean"]):
        out += [g("clean", f) for f in lf]
    out = np.array(out, dtype="float32")
    n = int(np.load(E.SHARED + ".npz")["bounds"][-1])
    assert len(out) == n, (len(out), n)
    np.save(PSHARED, out)
    tune_ids = set(half["tune"][0]) | set(half["tune"][1])
    return miss, tune_ids


def _init():
    single_thread_worker()
    E._init()
    _D.update(E._D)                                   # X, N, y, sl of the exp14 shared libraries
    _D["Y"] = np.load(PSHARED, mmap_mode="r")
    _D["cfg"] = json.load(open(os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json"),
                               encoding="utf8"))["tuned"]["Ours"]["params"]
    paths, X, N = E.load_set("tune_cfpfp")
    yw = pose_of("tune_cfpfp")
    pos = {p: i for i, p in enumerate(paths)}
    with open(os.path.join(DS, "hardtune", "cfp_fp", "pairs.csv")) as f:
        rows = list(csv.DictReader(f))
    a = np.array([pos.get(r["a"], -1) for r in rows]); b = np.array([pos.get(r["b"], -1) for r in rows])
    _D["cfp"] = (X, N, np.array([yw.get(p, 0.0) for p in paths]), a, b, np.array([int(r["same"]) for r in rows]))


def cluster(X, N, Y, pp, order=None):
    p = _D["cfg"]
    c = StableIncrementalClusterer(link_threshold=p["link"], min_neighbors=p["m"], attach_threshold=p["attach"],
                                   merge_threshold=p["merge"], dim=X.shape[1], pose_bonus=pp["bonus"],
                                   pose_scale=pp["scale"])
    n = len(X)
    order = np.arange(n) if order is None else order
    for s in range(0, n, 256):
        o = order[s:s + 256]
        c.add(X[o], N[o], Y[o])
    lab = np.empty(n, dtype=int)
    lab[order] = c.labels()
    return lab


def _lib(key):
    sl = _D["sl"][key]
    return np.asarray(_D["X"][sl]), _D["N"][sl], np.asarray(_D["Y"][sl]), _D["y"][sl]


def _tune(pp):
    from sklearn.metrics import adjusted_rand_score
    per = {}
    for key in _D["sl"]:
        split, cond, _ = key.split("|")
        if split == "tune":
            X, N, Y, y = _lib(key)
            per.setdefault(cond, []).append(adjusted_rand_score(y, cluster(X, N, Y, pp)))
    lfw = float(np.mean([np.mean(v) for v in per.values()]))
    X, N, Y, a, b, same = _D["cfp"]
    lab = cluster(X, N, Y, pp)
    ok = (a >= 0) & (b >= 0)
    together = np.zeros(len(a), dtype=bool)
    together[ok] = lab[a[ok]] == lab[b[ok]]
    acc = float((together == (same == 1)).mean())
    return pp, lfw, acc, (lfw + acc) / 2


def _test(args):
    pp, key = args
    X, N, Y, y = _lib(key)
    from sklearn.metrics import adjusted_rand_score
    labs = [cluster(X, N, Y, pp, order=np.random.RandomState(77 + s).permutation(len(X))) for s in range(3)]
    f1 = float(np.mean([evaluate(l, y)["B3_F1"] for l in labs]))
    return pp["bonus"], key, f1, float(min(adjusted_rand_score(labs[0], l) for l in labs[1:]))


def _whole(args):
    pp, name, tune_ids = args
    paths, X, N = E.load_set(name)
    yw = pose_of(name)
    ident = [p.split("/")[0] if name == "calfw" else p.split("/")[-1].rsplit("_", 1)[0] for p in paths]
    keep = [i for i, n in enumerate(ident) if n not in tune_ids]
    X, N = X[keep], N[keep]
    Y = np.array([yw.get(paths[i], 0.0) for i in keep])
    y = np.array([ident[i] for i in keep])
    lab = cluster(X, N, Y, pp, order=np.random.RandomState(77).permutation(len(X)))
    e = evaluate(lab, y)
    return pp["bonus"], name, {k: float(e[k]) for k in ("B3_P", "B3_R", "B3_F1", "ARI")}


def main():
    t0 = time.time()
    miss, tune_ids = build_yaw()
    print(f"yaw built for exp14 libraries ({miss} faces without landmarks -> yaw 0)", flush=True)
    rows = sorted(run_adaptive(_tune, GRID, initializer=_init, name="POSE-TUNE"), key=lambda r: -r[3])
    for pp, lfw, acc, sc in rows:
        print(f"  bonus {pp['bonus']:.3f} scale {pp['scale']}: score {sc:.4f} (LFW ARI {lfw:.4f}, CFP-FP pairs {acc:.4f})", flush=True)
    base = next(r for r in rows if r[0]["bonus"] == 0)
    best = rows[0]
    use = best[0] if best[3] - base[3] >= 0.002 else None
    print(f"DECISION: {'pose ' + str(use) if use else 'no gain on tuning data -> pose not used'} "
          f"(best {best[3]:.4f} vs no pose {base[3]:.4f})", flush=True)
    out = {"model": MODEL, "protocol": __doc__, "tuning": [dict(**r[0], lfw_ARI=r[1], cfpfp_pair_acc=r[2], score=r[3]) for r in rows],
           "decision": use}
    if use:
        zero = dict(bonus=0.0, scale=1.0)
        keys = [k for k in E._D_keys() if k.startswith("test|")]
        res = run_adaptive(_test, [(pp, k) for pp in (zero, use) for k in keys], initializer=_init, name="POSE-TEST")
        per = {}
        for b, k, f1, ag in res:
            per.setdefault(k.split("|")[1], {}).setdefault("pose" if b else "none", {})[int(k.split("|")[2])] = (f1, ag)
        table = {}
        for cond, d in per.items():
            ids = sorted(d["none"])
            a = [d["pose"][i][0] for i in ids]; b = [d["none"][i][0] for i in ids]
            table[cond] = {"F1_pose": float(np.mean(a)), "F1_none": float(np.mean(b)),
                           "order_agreement_min_pose": float(min(d["pose"][i][1] for i in ids)),
                           "pose_minus_none": E.paired_bootstrap(a, b)}
            t = table[cond]
            print(f"== {cond:9} pose {t['F1_pose']:.4f} none {t['F1_none']:.4f} diff {t['pose_minus_none']['diff']:+.4f} "
                  f"[{t['pose_minus_none']['ci95'][0]:+.4f},{t['pose_minus_none']['ci95'][1]:+.4f}] order {t['order_agreement_min_pose']:.4f}", flush=True)
        whole = {}
        for b, name, r in run_adaptive(_whole, [(pp, n, tune_ids) for pp in (zero, use) for n in ("calfw", "cplfw")],
                                       initializer=_init, name="POSE-WHOLE", per_step=2, shuffle=False):
            whole.setdefault(name, {})["pose" if b else "none"] = r
            print(f"   {name} {'pose' if b else 'none'} F1 {r['B3_F1']:.4f} ARI {r['ARI']:.4f}", flush=True)
        out.update(test=table, whole_sets_test_identities=whole)
    out["seconds"] = time.time() - t0
    save_json(f"exp16_pose_{MODEL}.json", out)
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
