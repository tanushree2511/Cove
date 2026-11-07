"""Experiment 17 - do "video tracks" bridge a person's frontal and profile PHOTO clusters?  (simulated, oracle tracks)

Idea (gap G5, research/innovation_scan_round2): faces of one video track are the same person by construction, and a track
often sweeps from frontal to profile. Fed to the clusterer as must-links, a track could join that person's frontal photo
cluster and profile photo cluster. Real data with the same people in photos AND videos (YouTube Faces) needs a request
form, so this is a SIMULATION that measures the mechanism with ideal tracks:

  * People: TEST-half identities of exp14 (identity-disjoint from all tuning) with 3 CPLFW (pose-varied) photos and >= 3
    LFW photos. CPLFW photos that are near-copies of an LFW photo (cos > 0.90) replace that LFW photo (no duplicates).
  * 30 libraries (seed 17): 15-40 such people with all their photos (LFW capped at 60) + 50-150 test-half strangers.
  * Half of the people (fixed seed) "appear in a video". Their simulated track = 1 frontal photo (lowest |yaw| LFW) and the
    most profile CPLFW photo (highest |yaw|), taken OUT of the photo set and added as track faces.
  * Three runs per library: (a) photos only; (b) photos + track faces, no links; (c) photos + track faces + must-links.
  * Scored on PHOTOS only (track faces excluded): B-Cubed P/R/F1, and "frontal-profile recall" = share of same-person
    (LFW photo, CPLFW photo) pairs placed together, separately for video people and non-video people.
  * No parameter is tuned: clusterer config = exp14 tuned config of the recogniser. Paired bootstrap over libraries.
  * Order check: run (c) in 3 random face orders.
Limits: tracks are ideal (two real photos, perfectly linked); real video frames are lower quality and may never reach a
full profile. A positive result shows the mechanism works; it does not show the size of the gain on real videos.
Run: COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp17_track_bridge.py -> results/exp17_track_bridge_<model>.json
"""
import collections
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cove"))
import exp14_disjoint as E  # noqa: E402
from adaptive import run_adaptive  # noqa: E402
from common import CACHE, save_json, single_thread_worker  # noqa: E402
from engines.stable_cluster import StableIncrementalClusterer  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402

MODEL = E.MODEL
N_LIB = 30
_D = {}


def pose(name):
    d = np.load(os.path.join(CACHE, f"pose_{name}.npz"))
    return dict(zip([p.replace("\\", "/") for p in d["paths"].tolist()], np.abs(d["yaw"]).tolist()))


def build():
    lp, LX, LN = E.load_set("lfw_clean")
    cp, CX, CN = E.load_set("cplfw")
    ly, cy = pose("lfw_clean"), pose("cplfw")
    by, half = E.split_identities(lp)
    test_rich, test_str = half["test"]
    lidx = collections.defaultdict(list)
    for i, p in enumerate(lp):
        lidx[p.split("/")[0]].append(i)
    cidx = collections.defaultdict(list)
    for j, p in enumerate(cp):
        cidx[p.split("/")[-1].rsplit("_", 1)[0]].append(j)
    test_ids = set(test_rich) | set(test_str)
    people = {}
    for n in sorted(test_ids):
        if len(cidx.get(n, [])) < 3 or len(lidx.get(n, [])) < 3:
            continue
        L = list(lidx[n])
        for j in cidx[n]:                                   # drop LFW copies of CPLFW photos
            s = LX[L] @ CX[j]
            if len(L) and s.max() > 0.90:
                L.pop(int(np.argmax(s)))
        if len(L) >= 2:
            people[n] = (L, list(cidx[n]))
    strangers = [n for n in sorted(test_str) if n not in people]
    rng = np.random.RandomState(17)
    libs = []
    names = sorted(people)
    for li in range(N_LIB):
        fam = list(rng.choice(names, min(len(names), rng.randint(15, 41)), replace=False))
        vid = set(rng.choice(fam, len(fam) // 2, replace=False))
        X, N, Y, kind, who, yaw = [], [], [], [], [], []    # kind: 'L' lfw photo, 'C' cplfw photo, 'T' track face
        tracks = []
        for n in fam:
            L, C = people[n]
            L = list(rng.permutation(L))[:60]
            Ls = sorted(L, key=lambda i: ly.get(lp[i], 0.0))
            Cs = sorted(C, key=lambda j: -cy.get(cp[j], 0.0))
            track = []
            if n in vid:
                track = [("L", Ls[0]), ("C", Cs[0])]
                L = [i for i in L if i != Ls[0]]
                C = [j for j in C if j != Cs[0]]
            for i in L:
                X.append(LX[i]); N.append(LN[i]); Y.append(n); kind.append("L"); who.append(n in vid)
            for j in C:
                X.append(CX[j]); N.append(CN[j]); Y.append(n); kind.append("C"); who.append(n in vid)
            ids = []
            for src, k in track:
                X.append(LX[k] if src == "L" else CX[k]); N.append(LN[k] if src == "L" else CN[k])
                Y.append(n); kind.append("T"); who.append(True); ids.append(len(X) - 1)
            if ids:
                tracks.append(ids)
        for s in rng.choice(strangers, rng.randint(50, 151), replace=False):
            i = lidx[s][rng.randint(len(lidx[s]))]
            X.append(LX[i]); N.append(LN[i]); Y.append(s); kind.append("L"); who.append(False)
        libs.append(dict(X=np.array(X, dtype="float32"), N=np.array(N, dtype="float32"), y=np.array(Y),
                         kind=np.array(kind), video=np.array(who), tracks=tracks))
    return libs, len(people)


def _init():
    single_thread_worker()
    _D["cfg"] = json.load(open(os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json"),
                               encoding="utf8"))["tuned"]["Ours"]["params"]
    _D["libs"] = np.load(os.path.join(CACHE, f"exp17_libs_{MODEL}.npy"), allow_pickle=True)


def cluster(X, N, links=(), order=None):
    p = _D["cfg"]
    c = StableIncrementalClusterer(link_threshold=p["link"], min_neighbors=p["m"], attach_threshold=p["attach"],
                                   merge_threshold=p["merge"], dim=X.shape[1])
    n = len(X)
    order = np.arange(n) if order is None else order
    inv = np.empty(n, dtype=int)
    inv[order] = np.arange(n)
    for s in range(0, n, 128):
        c.add(X[order[s:s + 128]], N[order[s:s + 128]])
    for a, b in links:
        c.add_must_link(inv[a], inv[b])
    return c.labels()[inv]


def fp_recall(lab, d, mask_people):
    """Share of same-person (LFW photo, CPLFW photo) pairs placed in one cluster, over the selected people."""
    tot = hit = 0
    for n in np.unique(d["y"][mask_people]):
        L = np.where((d["y"] == n) & (d["kind"] == "L"))[0]
        C = np.where((d["y"] == n) & (d["kind"] == "C"))[0]
        for c in C:
            tot += len(L)
            hit += int((lab[L] == lab[c]).sum())
    return hit / tot if tot else float("nan")


def _job(li):
    d = _D["libs"][li]
    photo = d["kind"] != "T"
    out = {}
    links = [(t[k], t[k + 1]) for t in d["tracks"] for k in range(len(t) - 1)]
    runs = {"a_photos": cluster(d["X"][photo], d["N"][photo]),
            "b_tracks_unlinked": cluster(d["X"], d["N"])[photo],
            "c_tracks_linked": cluster(d["X"], d["N"], links)[photo]}
    sub = {k: d[k][photo] for k in ("y", "kind", "video")}
    for name, lab in runs.items():
        e = evaluate(lab, sub["y"])
        out[name] = {"F1": e["B3_F1"], "P": e["B3_P"], "R": e["B3_R"],
                     "fp_recall_video": fp_recall(lab, sub, sub["video"]),
                     "fp_recall_novideo": fp_recall(lab, sub, ~sub["video"] & np.isin(sub["kind"], ["L", "C"]))}
    from sklearn.metrics import adjusted_rand_score
    ref = cluster(d["X"], d["N"], links)
    out["order_agreement_min"] = float(min(adjusted_rand_score(ref, cluster(d["X"], d["N"], links,
                                       order=np.random.RandomState(900 + t).permutation(len(d["X"])))) for t in range(3)))
    out["faces"], out["tracks"] = int(photo.sum()), len(d["tracks"])
    return li, out


def main():
    t0 = time.time()
    libs, n_people = build()
    np.save(os.path.join(CACHE, f"exp17_libs_{MODEL}.npy"), np.array(libs, dtype=object), allow_pickle=True)
    print(f"{n_people} eligible test-half people; {N_LIB} libraries", flush=True)
    rows = dict(run_adaptive(_job, list(range(N_LIB)), initializer=_init, name="TRACKS", shuffle=False))
    keys = ("a_photos", "b_tracks_unlinked", "c_tracks_linked")
    table = {k: {m: float(np.nanmean([rows[i][k][m] for i in rows])) for m in rows[0][k]} for k in keys}
    boot = {f"{k}_minus_a": E.paired_bootstrap([rows[i][k]["F1"] for i in sorted(rows)],
                                                [rows[i]["a_photos"]["F1"] for i in sorted(rows)]) for k in keys[1:]}
    boot["c_minus_b"] = E.paired_bootstrap([rows[i]["c_tracks_linked"]["F1"] for i in sorted(rows)],
                                           [rows[i]["b_tracks_unlinked"]["F1"] for i in sorted(rows)])
    for k in keys:
        t = table[k]
        print(f"== {k:18} F1 {t['F1']:.4f} (P {t['P']:.4f} R {t['R']:.4f}) | frontal-profile recall: video people "
              f"{t['fp_recall_video']:.4f}, others {t['fp_recall_novideo']:.4f}", flush=True)
    for k, b in boot.items():
        print(f"   {k}: {b['diff']:+.4f} [{b['ci95'][0]:+.4f},{b['ci95'][1]:+.4f}]", flush=True)
    print("order agreement min", min(r["order_agreement_min"] for r in rows.values()), flush=True)
    save_json(f"exp17_track_bridge_{MODEL}.json", {"model": MODEL, "protocol": __doc__, "eligible_people": n_people,
                                                   "table": table, "bootstrap": boot, "per_library": rows,
                                                   "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
