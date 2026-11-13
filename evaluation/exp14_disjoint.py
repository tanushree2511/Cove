"""Experiment 14 - identity-disjoint tuning/test protocol with equal tuning for every method (paper revision, round 1).

Answers the round-1 review: (1) tuning and test libraries shared identities; (2) baselines were tuned on unequal
terms; (3) test sets influenced decisions; (4) no confidence intervals; (5) no single-linkage / DBSCAN / HDBSCAN baselines.

Protocol, fixed BEFORE any test number is computed:
  * LFW identities are split once (seed 2026) into a TUNING half and a TEST half, separately for "family" identities
    (>= 10 photos) and "stranger" identities (< 10 photos). Libraries are drawn only from their own half, so no
    person in any test library appears in any tuning library.
  * Every method gets a threshold grid over the same similarity range on the same 30 tuning libraries x 7
    conditions (clean, lowres, blur, jpeg, dark, occlude, mixed). Selection rule for every method: highest mean ARI
    over the 7 conditions. Order-dependent methods are tuned on one fixed order per library.
  * Recogniser choice (MBF vs EdgeFace-S) is made on TUNING data: EdgeFace-S (faster) is chosen unless its tuning
    mean ARI for our method is lower than MBF's by more than 0.005.
  * Test: 30 test libraries x 7 conditions; order-dependent methods 5 orders, ours 3 orders (an empirical check of
    the invariance proof). CALFW / CPLFW and look-alike libraries are restricted to TEST-half identities.
  * Paired bootstrap (10,000 resamples over libraries) for the F1 difference between ours and each baseline.
Run once per recogniser:  COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp14_disjoint.py
Output: results/exp14_disjoint_<model>.json
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from adaptive import run_adaptive  # noqa: E402
from common import CACHE, be_nice, save_json, single_thread_worker  # noqa: E402
be_nice()
from exp1_cluster import agglomerative, dbscan, evaluate, first_leader, ours_two_stage  # noqa: E402
from exp7_order_stability import stable  # noqa: E402

MODEL = os.environ.get("COVE_FACE_MODEL")
assert MODEL in ("mbf", "edgeface_s"), "set COVE_FACE_MODEL=mbf or edgeface_s"
DEGR = ("clean", "lowres", "blur", "jpeg", "dark", "occlude")
CONDS = DEGR + ("mixed",)
N_LIB, SPLIT_SEED = 30, 2026
TAG = os.environ.get("COVE_TAG", "")                     # "" = the paper's LFW run; "_fiw" = exp31 outside-data run
SHARED = os.path.join(CACHE, f"exp14_shared_{MODEL}{TAG}")

T = [float(round(x, 2)) for x in np.arange(0.20, 0.701, 0.05)]                   # common similarity range for baselines
GRIDS = {
    "First-Leader": [dict(thr=t) for t in T],
    "Two-stage": [dict(thr=t, merge=g) for t in T for g in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60)],
    "Single linkage": [dict(thr=t) for t in T],
    "Agglomerative (avg)": [dict(thr=t) for t in T],
    "DBSCAN": [dict(thr=t, ms=k) for t in T for k in (2, 3, 4, 5)],
    "HDBSCAN": [dict(mcs=a, ms=b) for a in (2, 3, 4, 5, 8) for b in (1, 2, 3, 5)],
    "Ours, no attach": [dict(link=l, m=m, attach=None, merge=g) for l in (0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70)
                        for m in (1, 2) for g in (0.40, 0.45, 0.50, 0.55, 0.60)],
    "Ours": [dict(link=l, m=m, attach=a, merge=g) for l in (0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70) for m in (1, 2)
             for a in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55) if a <= l for g in (0.40, 0.45, 0.50, 0.55, 0.60)],
}
ORDER_DEP = {"First-Leader", "Two-stage"}


def hdbscan(X, mcs, ms):
    from sklearn.cluster import HDBSCAN
    lab = HDBSCAN(min_cluster_size=mcs, min_samples=ms, metric="euclidean").fit_predict(X)   # unit vectors: euclid ~ cosine
    noise = lab == -1
    lab = lab.copy()
    lab[noise] = lab.max() + 1 + np.arange(noise.sum())
    return lab


def run(method, X, N, p):
    if method == "First-Leader":
        return first_leader(X, p["thr"])
    if method == "Two-stage":
        return ours_two_stage(X, p["thr"], p["merge"])
    if method == "Single linkage":
        return agglomerative(X, 1.0 - p["thr"], linkage="single")
    if method == "Agglomerative (avg)":
        return agglomerative(X, 1.0 - p["thr"])
    if method == "DBSCAN":
        return dbscan(X, 1.0 - p["thr"], p["ms"])
    if method == "HDBSCAN":
        return hdbscan(X, p["mcs"], p["ms"])
    if method.startswith("Ours"):
        return stable(X, N, dict(link=p["link"], m=p["m"], attach=p["attach"], merge=p["merge"], qmin=None))
    raise ValueError(method)


# ------------------------------------------------------------------ data
def load_set(name):
    d = np.load(os.path.join(CACHE, f"emb_{MODEL}_{name}.npz"), allow_pickle=True)
    E = d["emb"].astype("float32")
    n = np.linalg.norm(E, axis=1)
    return [p.replace("\\", "/") for p in d["paths"].tolist()], E / n[:, None], n


def split_identities(paths):
    by = {}
    for p in paths:
        by.setdefault(p.split("/")[0], []).append(p)
    rng = np.random.RandomState(SPLIT_SEED)
    rich = sorted(n for n, v in by.items() if len(v) >= 10)
    others = sorted(n for n, v in by.items() if len(v) < 10)
    rp, op = rng.permutation(rich), rng.permutation(others)
    half = {"tune": (list(rp[: len(rp) // 2]), list(op[: len(op) // 2])),
            "test": (list(rp[len(rp) // 2:]), list(op[len(op) // 2:]))}
    return by, half


def make_libs(by, rich, others, seed):
    rng = np.random.RandomState(seed)
    libs = []
    for _ in range(N_LIB):
        people = rng.choice(rich, rng.randint(15, 41), replace=False)
        files = []
        for p in people:
            v = sorted(by[p])
            files += list(rng.choice(v, min(len(v), 200), replace=False))
        for s in rng.choice(others, rng.randint(50, 151), replace=False):
            v = sorted(by[s])
            files.append(v[rng.randint(len(v))])
        libs.append(sorted(files))
    return libs


def lookalike_libs(by, ids, X, pos, n_lib=30, seed=3):
    rich = sorted(n for n in ids if len(by[n]) >= 5)
    C = np.stack([X[[pos[f] for f in by[n] if f in pos]].mean(0) for n in rich])
    C /= np.linalg.norm(C, axis=1, keepdims=True)
    S = C @ C.T
    rng = np.random.RandomState(seed)
    libs = []
    for _ in range(n_lib):
        a = rng.randint(len(rich))
        files = []
        for g in np.argsort(-S[a])[: rng.randint(8, 16)]:
            v = sorted(by[rich[g]])
            files += list(rng.choice(v, min(len(v), 60), replace=False))
        libs.append(sorted(files))
    return libs


def build_shared():
    """All tuning/test library-conditions in one memory-mapped array, so every worker shares one copy."""
    sets = {k: load_set(f"lfw_{k}") for k in DEGR}
    by, half = split_identities(sets["clean"][0])
    pos = {k: {p: i for i, p in enumerate(sets[k][0])} for k in DEGR}
    Xs, Ns, ys, keys, bounds = [], [], [], [], [0]

    def add(key, X, N, y):
        Xs.append(X); Ns.append(N); ys.extend(y); keys.append(key); bounds.append(bounds[-1] + len(X))
    for split, seed in (("tune", 1), ("test", 0)):
        libs = make_libs(by, *half[split], seed=seed)
        for k in DEGR:
            for li, lf in enumerate(libs):
                keep = [f for f in lf if f in pos[k]]
                add(f"{split}|{k}|{li}", sets[k][1][[pos[k][f] for f in keep]], sets[k][2][[pos[k][f] for f in keep]],
                    [f.split("/")[0] for f in keep])
        for li, lf in enumerate(libs):
            rng = np.random.RandomState((1900 if split == "tune" else 900) + li)
            sel = [(k, f) for f in lf for k in [DEGR[rng.randint(len(DEGR))]] if f in pos[k]]
            add(f"{split}|mixed|{li}", np.stack([sets[k][1][pos[k][f]] for k, f in sel]),
                np.array([sets[k][2][pos[k][f]] for k, f in sel]), [f.split("/")[0] for _, f in sel])
    test_ids = set(half["test"][0]) | set(half["test"][1])
    for li, lf in enumerate(lookalike_libs(by, test_ids, sets["clean"][1], pos["clean"])):
        add(f"test|lookalike|{li}", sets["clean"][1][[pos["clean"][f] for f in lf]],
            sets["clean"][2][[pos["clean"][f] for f in lf]], [f.split("/")[0] for f in lf])
    np.save(SHARED + "_X.npy", np.concatenate(Xs).astype("float32"))
    np.savez(SHARED + ".npz", N=np.concatenate(Ns), y=np.array(ys), keys=np.array(keys), bounds=np.array(bounds))
    tune_ids = set(half["tune"][0]) | set(half["tune"][1])
    return {"tune_family": len(half["tune"][0]), "test_family": len(half["test"][0]),
            "tune_strangers": len(half["tune"][1]), "test_strangers": len(half["test"][1]),
            "identity_overlap": len(tune_ids & test_ids)}, tune_ids


_D = {}


def _init():
    single_thread_worker()
    d = np.load(SHARED + ".npz")
    _D["X"] = np.load(SHARED + "_X.npy", mmap_mode="r")
    _D["N"], _D["y"], b = d["N"], d["y"], d["bounds"]
    _D["sl"] = {k: slice(b[i], b[i + 1]) for i, k in enumerate(d["keys"].tolist())}


def _tune(args):
    method, p = args
    per = {}
    for key, sl in _D["sl"].items():
        split, cond, li = key.split("|")
        if split != "tune":
            continue
        X, N = np.asarray(_D["X"][sl]), _D["N"][sl]
        perm = np.random.RandomState(5000 + int(li)).permutation(len(X)) if method in ORDER_DEP else np.arange(len(X))
        lab = run(method, X[perm], N[perm], p)
        back = np.empty(len(X), dtype=int); back[perm] = lab
        per.setdefault(cond, []).append(evaluate(back, _D["y"][sl])["ARI"])
    by = {c: float(np.mean(v)) for c, v in per.items()}
    return method, p, by, float(np.mean(list(by.values())))


def _test(args):
    method, p, key = args
    sl = _D["sl"][key]
    X, N, y = np.asarray(_D["X"][sl]), _D["N"][sl], _D["y"][sl]
    rows, preds = [], []
    for sd in range(5 if method in ORDER_DEP else 3):
        perm = np.random.RandomState(77 + sd).permutation(len(X))
        lab = run(method, X[perm], N[perm], p)
        back = np.empty(len(X), dtype=int); back[perm] = lab
        rows.append(evaluate(back, y)); preds.append(back)
    from sklearn.metrics import adjusted_rand_score
    agree = min(adjusted_rand_score(preds[0], q) for q in preds[1:])
    m = {k: float(np.mean([r[k] for r in rows])) for k in ("B3_P", "B3_R", "B3_F1", "ARI")}
    m["F1_spread"] = float(max(r["B3_F1"] for r in rows) - min(r["B3_F1"] for r in rows))
    m["order_agreement_min"] = float(agree)
    return method, key, m


def paired_bootstrap(a, b, n=10000, seed=0):
    d = np.asarray(a) - np.asarray(b)
    rng = np.random.RandomState(seed)
    bs = d[rng.randint(0, len(d), (n, len(d)))].mean(1)
    return {"diff": float(d.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}


def whole_set(name, tune_ids):
    paths, X, N = load_set(name)
    ident = [p.split("/")[0] if name == "calfw" else p.split("/")[-1].rsplit("_", 1)[0] for p in paths]
    keep = [i for i, n in enumerate(ident) if n not in tune_ids]
    return X[keep], N[keep], np.array([ident[i] for i in keep])


def _whole(args):
    method, p, name, tune_ids = args
    X, N, y = whole_set(name, tune_ids)
    perm = np.random.RandomState(77).permutation(len(X))
    lab = run(method, X[perm], N[perm], p)
    back = np.empty(len(X), dtype=int); back[perm] = lab
    e = evaluate(back, y)
    return method, name, {k: float(e[k]) for k in ("B3_P", "B3_R", "B3_F1", "ARI")}, int(len(X))


def main():
    t0 = time.time()
    info, tune_ids = build_shared()
    print("identity split:", info, flush=True)
    assert info["identity_overlap"] == 0
    jobs = [(m, p) for m, g in GRIDS.items() for p in g]
    tuned, grid_rows = {}, {}
    ck_tune = os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json")
    if os.path.exists(ck_tune):                          # resume: tuning already finished and saved
        d = json.load(open(ck_tune, encoding="utf8"))
        tuned = {m: (v["params"], v["tuning_ARI_mean"]) for m, v in d["tuned"].items()}
        grid_rows = d.get("grid", {})
        jobs = []
        print(f"TUNING: resumed from {os.path.basename(ck_tune)}", flush=True)
    else:
        print(f"TUNING: {len(jobs)} configurations", flush=True)
    # partial checkpoint: one JSON line per finished configuration, so a stopped run resumes where it was
    part = os.path.join(CACHE, f"exp14_tune_partial_{MODEL}.jsonl")
    prior = []
    if jobs and os.path.exists(part):
        with open(part, encoding="utf8") as f:
            prior = [tuple(json.loads(line)) for line in f if line.strip()]
        done_keys = {json.dumps([r[0], r[1]], sort_keys=True) for r in prior}
        jobs = [j for j in jobs if json.dumps([j[0], j[1]], sort_keys=True) not in done_keys]
        print(f"TUNING: {len(prior)} configurations resumed from partial checkpoint, {len(jobs)} to run", flush=True)
    pf = open(part, "a", encoding="utf8") if jobs else None

    def _ck(r):
        pf.write(json.dumps(list(r)) + "\n")
        pf.flush()
    new_rows = run_adaptive(_tune, jobs, initializer=_init, name="TUNING", on_result=_ck if pf else None)
    if pf:
        pf.close()
    for m, p, by, mean in prior + new_rows:
        grid_rows.setdefault(m, []).append({**p, "per_condition_ARI": by, "ARI_mean": mean})
        if m not in tuned or mean > tuned[m][1]:
            tuned[m] = (p, mean)
    for m, (p, s) in tuned.items():
        print(f"CHOSEN {m:<22} {p}  tuning ARI {s:.4f}", flush=True)
    if jobs or prior:
        save_json(os.path.basename(ck_tune), {"tuned": {m: {"params": p, "tuning_ARI_mean": s} for m, (p, s) in tuned.items()},
                                              "grid": grid_rows})

    keys = [k for k in _D_keys() if k.startswith("test|")]
    tjobs = [(m, tuned[m][0], k) for m in GRIDS for k in keys]
    ck_test = os.path.join(os.path.dirname(__file__), "results", f"exp14_testruns_{MODEL}.json")
    per = {}
    if os.path.exists(ck_test):                          # resume: per-library test runs already saved
        raw = json.load(open(ck_test, encoding="utf8"))
        per = {c: {m: {int(i): r for i, r in rs.items()} for m, rs in ms.items()} for c, ms in raw.items()}
        print(f"TEST: resumed from {os.path.basename(ck_test)}", flush=True)
    else:
        print(f"TEST: {len(tjobs)} library runs", flush=True)
        for m, k, r in run_adaptive(_test, tjobs, initializer=_init, name="TEST"):
            per.setdefault(k.split("|")[1], {}).setdefault(m, {})[int(k.split("|")[2])] = r
        save_json(os.path.basename(ck_test), per)
    table, boot = {}, {}
    for cond, ms in per.items():
        table[cond] = {m: {k: float(np.mean([v[k] for v in rs.values()])) for k in rs[0]} for m, rs in ms.items()}
        for m in table[cond]:
            table[cond][m]["F1_worst"] = float(min(v["B3_F1"] for v in ms[m].values()))
            table[cond][m]["order_agreement_min"] = float(min(v["order_agreement_min"] for v in ms[m].values()))
        ours = [ms["Ours"][i]["B3_F1"] for i in sorted(ms["Ours"])]
        boot[cond] = {m: paired_bootstrap(ours, [ms[m][i]["B3_F1"] for i in sorted(ms[m])]) for m in ms if m != "Ours"}
        print(f"\n== {cond}", flush=True)
        for m, v in table[cond].items():
            b = boot[cond].get(m)
            print(f"   {m:<22} F1 {v['B3_F1']:.4f} (P {v['B3_P']:.3f} R {v['B3_R']:.3f})  ARI {v['ARI']:.4f}  "
                  f"order-agree {v['order_agreement_min']:.4f}"
                  + (f"  ours-minus {b['diff']:+.4f} [{b['ci95'][0]:+.4f},{b['ci95'][1]:+.4f}]" if b else ""), flush=True)

    # whole-set CALFW / CPLFW (test-half identities only); O(n^2) methods -> fewer workers, measured
    wjobs = [(m, tuned[m][0], n, tune_ids) for n in ("calfw", "cplfw") for m in GRIDS]
    # heaviest jobs first (agglomerative, then CALFW) so the calibration sees the memory peak before choosing
    wjobs.sort(key=lambda j: (j[0] != "Agglomerative (avg)", j[2] != "calfw"))
    print(f"\nWHOLE SETS: {len(wjobs)} runs", flush=True)
    whole = {}
    for m, n, r, size in run_adaptive(_whole, wjobs, initializer=single_thread_worker, name="WHOLE", per_step=3, shuffle=False):
        whole.setdefault(n, {"faces": size})[m] = r
        print(f"   {n} {m:<22} F1 {r['B3_F1']:.4f} ARI {r['ARI']:.4f}", flush=True)
    save_json(f"exp14_disjoint_{MODEL}.json", {
        "model": MODEL, "protocol": __doc__, "split": info,
        "tuned": {m: {"params": p, "tuning_ARI_mean": s} for m, (p, s) in tuned.items()},
        "test": table, "bootstrap_ours_minus": boot, "whole_sets_test_identities": whole, "grid": grid_rows,
        "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


def _D_keys():
    return np.load(SHARED + ".npz")["keys"].tolist()


if __name__ == "__main__":
    main()
