"""Experiment 9 - clustering under CHALLENGING conditions.

A. Degraded personal libraries: the 30 exp8 test libraries, re-embedded from degraded images
   (lowres ~16 px faces, blur, jpeg q8, dark+noise, eye occlusion) and a MIXED condition where every photo
   independently gets one of {clean, lowres, blur, jpeg, dark, occlude} - like a real phone library.
   Photos in which the detector finds no face are reported as detection failures and left out of clustering.
B. Look-alike libraries: each library is built from people whose faces are most similar to each other
   (nearest identity centroids) - a stand-in for siblings / relatives in a family album.
C. CALFW (cross-age, 4k people) and CPLFW (cross-pose) as whole sets.
Methods and thresholds exactly as exp8 (ours: config chosen on the seed-1 tuning libraries). One order per run for
the order-free methods; First-Leader / two-stage use 5 orders (mean, and spread).
Run: python evaluation/exp9_hard.py
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, load_json, save_json, be_nice, measure_worker_gb, plan_parallelism, single_thread_worker  # noqa: E402
be_nice()
from exp1_cluster import agglomerative, evaluate  # noqa: E402
from exp7_order_stability import load_raw, run_method  # noqa: E402
from exp8_personal_libraries import make_libraries  # noqa: E402

DEGR = ("clean", "lowres", "blur", "jpeg", "dark", "occlude")
N_ORD = 5
METHODS = {"First-Leader": "first_leader", "Two-stage (current)": "two_stage", "Ours v1 (exp8 config)": "stable",
           "Ours v2 (robust, exp10 config)": "stable_v2", "Ours v3 (pose+age tuned, exp11 config)": "stable_v3"}


FACE_MODEL = os.environ.get("COVE_FACE_MODEL")          # None = the original buffalo_s embeddings (hard_<set>.npz)
SUFFIX = f"_{FACE_MODEL}" if FACE_MODEL else ""
TAG = os.environ.get("COVE_RUN_TAG", "")             # result-file tag for alternative tuning grids (e.g. "_wide")
if FACE_MODEL:     # face-model comparison (exp13): only our method, tuned for that model. Module level so that
    METHODS = {"Ours (a: pose+age+library rule)": "stable_v4",   # spawned worker processes see the same list.
               "Ours (b: library-ARI rule)": "stable_v5"}


def load_set(name):
    p = os.path.join(CACHE, f"emb_{FACE_MODEL}_{name}.npz" if FACE_MODEL else f"hard_{name}.npz")
    if not os.path.exists(p):
        return None
    d = np.load(p, allow_pickle=True)
    E = d["emb"].astype("float32")
    n = np.linalg.norm(E, axis=1)
    return {"paths": [x.replace("\\", "/") for x in d["paths"].tolist()], "X": E / n[:, None], "N": n,
            "det": d["det"], "missing": d["missing"].tolist()}


def score(X, N, y, cfg, fl, ag, only=None):
    out = {}
    for name, m in METHODS.items():
        if only is not None and name != only:
            continue
        f1, ari = [], []
        for sd in range(N_ORD if not m.startswith("stable") else 1):
            perm = np.random.RandomState(77 + sd).permutation(len(X))
            c = cfg.get(m[-2:], cfg) if m.startswith("stable_v") else cfg
            lab = run_method("stable" if m.startswith("stable") else m, X[perm], N[perm], c, fl)
            back = np.empty(len(X), dtype=int); back[perm] = lab
            e = evaluate(back, y); f1.append(e["B3_F1"]); ari.append(e["ARI"])
        out[name] = {"F1": float(np.mean(f1)), "F1_spread": float(np.max(f1) - np.min(f1)), "ARI": float(np.mean(ari))}
    if FACE_MODEL or only not in (None, "Agglomerative (batch)"):    # agglomerative's threshold was tuned for buffalo_s only
        return out
    e = evaluate(agglomerative(X, 1.0 - ag), y)
    out["Agglomerative (batch)"] = {"F1": e["B3_F1"], "F1_spread": 0.0, "ARI": e["ARI"]}
    return out


def _job(a):
    os.environ["OMP_NUM_THREADS"] = "1"
    import faiss
    faiss.omp_set_num_threads(1)
    tag, X, N, y, cfg, fl, ag = a[:7]
    return tag, score(X, N, y, cfg, fl, ag, only=a[7] if len(a) > 7 else None)


def summarise(results):
    """results: list of per-library dicts -> mean F1/ARI, worst F1, mean spread per method."""
    s = {}
    for m in results[0]:
        s[m] = {"F1": float(np.mean([r[m]["F1"] for r in results])), "F1_worst": float(np.min([r[m]["F1"] for r in results])),
                "ARI": float(np.mean([r[m]["ARI"] for r in results])), "ARI_worst": float(np.min([r[m]["ARI"] for r in results])),
                "F1_spread_max": float(np.max([r[m]["F1_spread"] for r in results]))}
    return s


def lookalike_libraries(X, ident, n_lib=30, seed=3):
    """Libraries of mutually similar-looking people: seed person + its nearest identities by centroid."""
    rng = np.random.RandomState(seed)
    ids = {}
    for i, n in enumerate(ident):
        ids.setdefault(n, []).append(i)
    rich = sorted(n for n, v in ids.items() if len(v) >= 5)
    C = np.stack([X[ids[n]].mean(0) for n in rich]); C /= np.linalg.norm(C, axis=1, keepdims=True)
    S = C @ C.T
    libs = []
    for _ in range(n_lib):
        a = rng.randint(len(rich))
        group = np.argsort(-S[a])[:rng.randint(8, 16)]            # the most similar-looking people to a seed person
        idx = []
        for g in group:
            v = ids[rich[g]]
            idx += list(rng.choice(v, min(len(v), 60), replace=False))
        libs.append(np.array(sorted(idx)))
    return libs, float(np.mean([S[a][np.argsort(-S[a])[1:8]].mean() for a in range(len(rich))]))


def main():
    e8 = load_json("exp8_personal_libraries.json")
    e7 = load_json("exp7_order_stability.json")
    cfg, fl, ag = dict(e8["config"]), e7["thresholds"]["first_leader"], e7["thresholds"]["agglomerative"]
    if FACE_MODEL:                                                     # face-model comparison (exp13): ours, tuned per model
        g = load_json(f"exp11_tuned_config{SUFFIX}{TAG}.json")
        cfg["v4"] = g["config"]                                        # rule (a): mean of library ARI, AgeDB, CFP-FP pair acc
        b = max(g["grid"], key=lambda r: r["lfw_ARI"])                 # rule (b): library ARI only (the exp10 / v2 rule)
        cfg["v5"] = {k: b[k] for k in ("link", "m", "attach", "merge", "qpct", "qmin")}
        ag = load_json(f"exp11_tuned_config{SUFFIX}{TAG}.json").get("agglomerative", ag)
    cfg["v2"] = load_json("exp10_tuned_config.json")["config"]          # chosen on tuning data only (exp10)
    if not FACE_MODEL and os.path.exists(os.path.join(os.path.dirname(__file__), "results", "exp11_tuned_config.json")):
        cfg["v3"] = load_json("exp11_tuned_config.json")["config"]      # + pose/age tuning data (exp11)
    else:
        METHODS.pop("Ours v3 (pose+age tuned, exp11 config)", None)
    paths, _, _, ident = load_raw()
    libs = make_libraries(ident, seed=0)
    lib_files = [[paths[i].replace("\\", "/") for i in l] for l in libs]
    out = {"config": cfg}
    jobs = []

    # ---- A. degraded libraries (+ mixed)
    sets = {k: load_set(f"lfw_{k}") for k in DEGR}
    det_rates = {}
    for k, s in sets.items():
        if s is None:
            continue
        pos = {p: i for i, p in enumerate(s["paths"])}
        allf = sorted(set(f for lf in lib_files for f in lf))
        det_rates[k] = 1.0 - sum(f not in pos for f in allf) / len(allf)
        for li, lf in enumerate(lib_files):
            keep = [pos[f] for f in lf if f in pos]
            y = np.array([f.split("/")[0] for f in lf if f in pos])
            jobs.append((f"A|{k}|{li}", s["X"][keep], s["N"][keep], y, cfg, fl, ag))
    if all(sets[k] is not None for k in DEGR):
        pos = {k: {p: i for i, p in enumerate(sets[k]["paths"])} for k in DEGR}
        for li, lf in enumerate(lib_files):
            rng = np.random.RandomState(900 + li)
            Xs, Ns, ys = [], [], []
            for f in lf:
                k = DEGR[rng.randint(len(DEGR))]
                if f in pos[k]:
                    j = pos[k][f]; Xs.append(sets[k]["X"][j]); Ns.append(sets[k]["N"][j]); ys.append(f.split("/")[0])
            jobs.append((f"A|mixed|{li}", np.array(Xs), np.array(Ns), np.array(ys), cfg, fl, ag))
    out["detection_rate"] = det_rates

    # ---- B. look-alike libraries (clean LFW embeddings)
    _, Xc, Nc, _ = load_raw()
    la, sim = lookalike_libraries(Xc, ident)
    out["lookalike_mean_centroid_sim_top7"] = sim
    for li, l in enumerate([] if FACE_MODEL else la):
        jobs.append((f"B|lookalike|{li}", Xc[l], Nc[l], ident[l], cfg, fl, ag))

    # ---- C. CALFW / CPLFW whole sets
    for name in ("calfw", "cplfw"):
        s = load_set(name)
        if s is None:
            continue
        # CALFW: <identity>/<file>.jpg ; CPLFW: <shard>/<Identity_Name>_<n>.jpg
        y = np.array([p.split("/")[0] if name == "calfw" else p.split("/")[-1].rsplit("_", 1)[0] for p in s["paths"]])
        out[f"{name}_detection_rate"] = len(s["paths"]) / (len(s["paths"]) + len(s["missing"]))
        jobs.append((f"C|{name}|0", s["X"], s["N"], y, cfg, fl, ag))

    # library-sized jobs run in parallel; the two whole-set jobs (12k faces, O(n^2) agglomerative) run alone afterwards
    small = [j for j in jobs if not j[0].startswith("C|")]
    big = [j for j in jobs if j[0].startswith("C|")]
    probe = max(small, key=lambda j: len(j[1]))
    gb = measure_worker_gb(_job, probe, initializer=single_thread_worker)
    workers, _ = plan_parallelism(gb, threads_per_worker=1)
    print(f"{len(small)} library jobs: measured {gb:.2f} GB/worker -> {workers} workers; then {len(big)} whole-set job(s)", flush=True)
    res = {}
    with ProcessPoolExecutor(workers, initializer=single_thread_worker) as pool:
        for tag, r in pool.map(_job, small):
            res.setdefault(tuple(tag.split("|")[:2]), []).append(r)
    # whole-set jobs: one task per method, run in parallel (memory measured on the heaviest one, agglomerative)
    parts = [j + (m,) for j in big for m in list(METHODS) + ([] if FACE_MODEL else ["Agglomerative (batch)"])]
    if parts:
        gb_big = measure_worker_gb(_job, max(parts, key=lambda p: (p[7] == "Agglomerative (batch)", len(p[1]))),
                                   initializer=single_thread_worker)
        wb, _ = plan_parallelism(gb_big, threads_per_worker=1)
        print(f"{len(parts)} whole-set tasks: measured {gb_big:.2f} GB/worker -> {wb} workers", flush=True)
        merged = {}
        with ProcessPoolExecutor(wb, initializer=single_thread_worker) as pool:
            for tag, r in pool.map(_job, parts):
                merged.setdefault(tag, {}).update(r)
        for tag, r in merged.items():
            res.setdefault(tuple(tag.split("|")[:2]), []).append(r)
    table = {}
    for (part, cond), rs in sorted(res.items()):
        table[f"{part}:{cond}"] = summarise(rs)
        print(f"\n== {part}:{cond}  ({len(rs)} run{'s' if len(rs) > 1 else ''})"
              + (f"  detection {100 * det_rates[cond]:.1f}%" if cond in det_rates else ""), flush=True)
        for m, v in table[f"{part}:{cond}"].items():
            print(f"   {m:<24} F1 {v['F1']:.4f} (worst {v['F1_worst']:.4f})  ARI {v['ARI']:.4f} (worst {v['ARI_worst']:.4f})"
                  f"  order-spread max {v['F1_spread_max']:.4f}", flush=True)
    out["table"] = table
    save_json(f"exp9_hard{SUFFIX}{TAG}.json", out)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
