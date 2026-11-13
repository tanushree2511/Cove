"""Experiment 31b - outside-data test on FIW (Families in the Wild) family photos (answers "real album data").

FIW terms: non-commercial research and education only; images are NOT redistributed (they stay in datasets/fiw/, git-ignored);
FIW is cited in the paper. Only derived embeddings and numbers are produced here.

What FIW is: face crops of real family photos (980 families, 34,692 faces, 5,773 people); relatives look alike, faces are small
and uncontrolled. It is NOT a private album and its people are public figures; the paper says so.

Protocol (fixed before any FIW number was computed):
  * Families are split once (seed 2026) into a TUNE half and a TEST half (no family, hence no relatives, in both).
  * A library = 8-16 random families of its half, every member's faces (<=200 per person): 20 tune and 30 test libraries.
  * A: TRANSFER - every method uses the parameters it was tuned to on LFW (exp14, tuning half); nothing is tuned on FIW.
  * B: RE-TUNED - every method is tuned on the 20 FIW tune libraries (same grids and rule as exp14), tested on the 30 test libraries.
  * Test as exp14: order-dependent methods 5 orders, others 3; paired bootstrap (10,000) over libraries for ours minus each.
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp31b_fiw_transfer.py
"""
import json
import os
import sys
import time

os.environ["COVE_TAG"] = "_fiw"
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import exp14_disjoint as E  # noqa: E402  (reads COVE_FACE_MODEL and COVE_TAG)
from adaptive import run_adaptive  # noqa: E402
from common import CACHE, save_json  # noqa: E402

MODEL = E.MODEL
N_TUNE, N_TEST, SEED = 20, 30, 2026


def load():
    d = np.load(os.path.join(CACHE, f"emb_{MODEL}_fiw.npz"), allow_pickle=True)
    paths = [p.replace("\\", "/") for p in d["paths"].tolist()]
    Eb = d["emb"].astype("float32")
    n = np.linalg.norm(Eb, axis=1)
    return paths, Eb / n[:, None], n, d["fallback"]


def build():
    paths, X, N, fb = load()
    fam = np.array([p.split("/")[0] for p in paths])
    ident = np.array([p.rsplit("/", 1)[0] for p in paths])
    fams = sorted(set(fam))
    rng = np.random.RandomState(SEED)
    perm = rng.permutation(len(fams))
    half = {"tune": [fams[i] for i in perm[: len(fams) // 2]], "test": [fams[i] for i in perm[len(fams) // 2:]]}
    by_fam = {}
    for i, f in enumerate(fam):
        by_fam.setdefault(f, []).append(i)
    Xs, Ns, ys, keys, bounds = [], [], [], [], [0]
    info = {"fallback_resized": int(np.sum(fb)), "faces": len(paths), "families": len(fams), "people": len(set(ident))}
    for split, n_lib, seed in (("tune", N_TUNE, 1), ("test", N_TEST, 0)):
        r = np.random.RandomState(seed)
        sizes = []
        for li in range(n_lib):
            chosen = r.choice(half[split], r.randint(8, 17), replace=False)
            idx = []
            for f in chosen:
                ii = np.array(by_fam[f])
                for pid in sorted(set(ident[ii])):
                    pi = ii[ident[ii] == pid]
                    idx += list(r.choice(pi, min(len(pi), 200), replace=False))
            idx = np.array(sorted(idx))
            Xs.append(X[idx]); Ns.append(N[idx]); ys.extend(ident[idx].tolist())
            keys.append(f"{split}|fiw|{li}"); bounds.append(bounds[-1] + len(idx)); sizes.append(len(idx))
        info[f"{split}_library_faces_min_med_max"] = [int(min(sizes)), int(np.median(sizes)), int(max(sizes))]
    np.save(E.SHARED + "_X.npy", np.concatenate(Xs).astype("float32"))
    np.savez(E.SHARED + ".npz", N=np.concatenate(Ns), y=np.array(ys), keys=np.array(keys), bounds=np.array(bounds))
    info["family_overlap_tune_test"] = len(set(half["tune"]) & set(half["test"]))
    return info


def summarise(per):
    table, boot = {}, {}
    for m, rs in per.items():
        table[m] = {k: float(np.mean([v[k] for v in rs.values()])) for k in rs[0]}
        table[m]["F1_worst"] = float(min(v["B3_F1"] for v in rs.values()))
        table[m]["order_agreement_min"] = float(min(v["order_agreement_min"] for v in rs.values()))
    ours = [per["Ours"][i]["B3_F1"] for i in sorted(per["Ours"])]
    for m in per:
        if m != "Ours":
            boot[m] = E.paired_bootstrap(ours, [per[m][i]["B3_F1"] for i in sorted(per[m])])
    return table, boot


def test(params, tag):
    keys = [k for k in np.load(E.SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    jobs = [(m, params[m], k) for m in E.GRIDS for k in keys]
    per = {}
    for m, k, r in run_adaptive(E._test, jobs, initializer=E._init, name=f"TEST-{tag}"):
        per.setdefault(m, {})[int(k.split("|")[2])] = r
    table, boot = summarise(per)
    print(f"\n== FIW {tag}", flush=True)
    for m, v in table.items():
        b = boot.get(m)
        print(f"   {m:<22} F1 {v['B3_F1']:.4f} (P {v['B3_P']:.3f} R {v['B3_R']:.3f}) ARI {v['ARI']:.4f} order {v['order_agreement_min']:.4f}"
              + (f"  ours-minus {b['diff']:+.4f} [{b['ci95'][0]:+.4f},{b['ci95'][1]:+.4f}]" if b else ""), flush=True)
    return {"table": table, "bootstrap_ours_minus": boot, "per_library": {m: {str(i): r for i, r in rs.items()} for m, rs in per.items()}}


def main():
    t0 = time.time()
    info = build()
    print("FIW libraries:", info, flush=True)
    assert info["family_overlap_tune_test"] == 0
    lfw = json.load(open(os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json"), encoding="utf8"))["tuned"]
    out = {"model": MODEL, "protocol": __doc__, "libraries": info}
    out["A_transfer_LFW_tuned"] = test({m: lfw[m]["params"] for m in E.GRIDS}, "transfer")
    # B: tune on FIW tune libraries
    jobs = [(m, p) for m, g in E.GRIDS.items() for p in g]
    print(f"TUNING on FIW: {len(jobs)} configurations", flush=True)
    tuned = {}
    for m, p, by, mean in run_adaptive(E._tune, jobs, initializer=E._init, name="TUNING-FIW"):
        if m not in tuned or mean > tuned[m][1]:
            tuned[m] = (p, mean)
    for m, (p, s) in tuned.items():
        print(f"CHOSEN {m:<22} {p} tuning ARI {s:.4f}", flush=True)
    out["B_tuned_on_FIW"] = test({m: tuned[m][0] for m in E.GRIDS}, "retuned")
    out["B_tuned_on_FIW"]["tuned"] = {m: {"params": p, "tuning_ARI_mean": s} for m, (p, s) in tuned.items()}
    out["LFW_tuned_params"] = {m: lfw[m]["params"] for m in E.GRIDS}
    out["seconds"] = time.time() - t0
    save_json(f"exp31_fiw_transfer_{MODEL}.json", out)
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
