"""Experiment 17b - the track bridge in the HARD setting: the whole CPLFW test half (where ours scores F1 ~0.84).

Simulated ideal tracks, as exp17: for a fixed random half of the test-half CPLFW people that also have an LFW photo that is
NOT a copy of their CPLFW photos, a track = (their most frontal such LFW photo, their most profile CPLFW photo); that CPLFW
photo leaves the photo set. Same photos are scored in all runs:
  (a) photos only, (b) photos + track faces unlinked, (c) photos + track faces + must-link.
Scored on the remaining CPLFW photos: B-Cubed P/R/F1 overall, and same-person pair recall for video vs non-video people.
No tuning; exp14 tuned config. Order check on (c) with 2 random orders.
"""
import collections, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cove"))
import exp14_disjoint as E
from common import CACHE, save_json
from engines.stable_cluster import StableIncrementalClusterer
from exp1_cluster import evaluate
from exp17_track_bridge import pose
MODEL = E.MODEL
cfg = json.load(open(os.path.join(os.path.dirname(__file__), "results", f"exp14_tuned_{MODEL}.json")))["tuned"]["Ours"]["params"]


def cluster(X, N, links=(), order=None):
    c = StableIncrementalClusterer(link_threshold=cfg["link"], min_neighbors=cfg["m"], attach_threshold=cfg["attach"],
                                   merge_threshold=cfg["merge"], dim=X.shape[1])
    n = len(X); order = np.arange(n) if order is None else order
    inv = np.empty(n, dtype=int); inv[order] = np.arange(n)
    for s in range(0, n, 512):
        c.add(X[order[s:s + 512]], N[order[s:s + 512]])
    for a, b in links:
        c.add_must_link(inv[a], inv[b])
    return c.labels()[inv]


def pair_recall(lab, y, people):
    tot = hit = 0
    for n in people:
        idx = np.where(y == n)[0]
        for i in range(len(idx)):
            for j in range(i + 1, len(idx)):
                tot += 1; hit += int(lab[idx[i]] == lab[idx[j]])
    return hit / tot if tot else float("nan")


def main():
    t0 = time.time()
    lp, LX, LN = E.load_set("lfw_clean"); cp, CX, CN = E.load_set("cplfw")
    ly, cy = pose("lfw_clean"), pose("cplfw")
    by, half = E.split_identities(lp)
    test_ids = set(half["test"][0]) | set(half["test"][1])
    lidx = collections.defaultdict(list)
    for i, p in enumerate(lp): lidx[p.split("/")[0]].append(i)
    cidx = collections.defaultdict(list)
    for j, p in enumerate(cp):
        n = p.split("/")[-1].rsplit("_", 1)[0]
        if n in test_ids: cidx[n].append(j)
    eligible = {}
    for n, C in cidx.items():
        if len(C) < 3: continue
        L = [i for i in lidx.get(n, []) if (LX[i] @ CX[C].T).max() <= 0.90]     # LFW photos that are not CPLFW copies
        if L: eligible[n] = min(L, key=lambda i: ly.get(lp[i], 0.0))
    rng = np.random.RandomState(171)
    vid = set(rng.choice(sorted(eligible), len(eligible) // 2, replace=False))
    X, N, Y, links, track_rows = [], [], [], [], []
    for n in sorted(cidx):
        C = cidx[n]
        drop = max(C, key=lambda j: cy.get(cp[j], 0.0)) if n in vid else None
        for j in C:
            if j != drop:
                X.append(CX[j]); N.append(CN[j]); Y.append(n)
        if n in vid:
            X.append(LX[eligible[n]]); N.append(LN[eligible[n]]); Y.append(n)
            X.append(CX[drop]); N.append(CN[drop]); Y.append(n)
            links.append((len(X) - 2, len(X) - 1)); track_rows += [len(X) - 2, len(X) - 1]
    X, N, Y = np.array(X, dtype="float32"), np.array(N, dtype="float32"), np.array(Y)
    photo = np.ones(len(X), dtype=bool); photo[track_rows] = False
    print(f"{len(cidx)} test-half CPLFW people, {int(photo.sum())} photos, {len(vid)} people with a simulated track", flush=True)
    perm = np.random.RandomState(77).permutation(len(X))
    runs = {"a_photos": None, "b_tracks_unlinked": cluster(X, N, order=perm)[photo],
            "c_tracks_linked": cluster(X, N, links, order=perm)[photo]}
    pidx = np.where(photo)[0]
    runs["a_photos"] = cluster(X[pidx], N[pidx], order=np.random.RandomState(77).permutation(len(pidx)))
    yv = Y[photo]; vp = sorted(vid); nvp = sorted(set(cidx) - vid)
    out = {}
    for k, lab in runs.items():
        e = evaluate(lab, yv)
        out[k] = {"F1": e["B3_F1"], "P": e["B3_P"], "R": e["B3_R"], "pair_recall_video": pair_recall(lab, yv, vp),
                  "pair_recall_novideo": pair_recall(lab, yv, nvp)}
        t = out[k]
        print(f"== {k:18} F1 {t['F1']:.4f} (P {t['P']:.4f} R {t['R']:.4f}) | same-person pair recall: video people "
              f"{t['pair_recall_video']:.4f}, others {t['pair_recall_novideo']:.4f}", flush=True)
    from sklearn.metrics import adjusted_rand_score
    ref = cluster(X, N, links, order=perm)
    out["order_agreement_min"] = float(min(adjusted_rand_score(ref, cluster(X, N, links, order=np.random.RandomState(500 + t).permutation(len(X)))) for t in range(2)))
    print("order agreement min", out["order_agreement_min"], flush=True)
    save_json(f"exp17b_track_bridge_hard_{MODEL}.json", {"model": MODEL, "protocol": __doc__, "result": out,
              "people": len(cidx), "video_people": len(vid), "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
