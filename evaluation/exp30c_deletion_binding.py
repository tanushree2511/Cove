"""Experiment 30c - deletion exactness over several random deletions, with BINDING corrections (round-10 review: the random corrections of 30b never changed a label).

On the 8,290 clean LFW faces (EdgeFace-S, shipped setting): for 5 seeds x deleted share {1%, 10%, 30%}, make up to 10 corrections that bind
(5 same-person pairs the unconstrained clusterer left in different clusters, 5 cannot-link pairs it put in one cluster; only pairs it got wrong), delete the random share, and compare the labels with a clusterer built
only from the remaining faces and only the corrections whose faces remain. Counts identical partitions.
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp30c_deletion_binding.py
"""
import os
import sys
import time

os.environ["COVE_FACE_MODEL"] = "edgeface_s"
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
import exp14_disjoint as D  # noqa: E402
import exp24_cavg_timing as T  # noqa: E402
from common import save_json  # noqa: E402
from exp20_exact_read import build, canon  # noqa: E402


def corrections(y, lab, rng, k=5):
    """Binding corrections: must-links between same-person faces in different clusters, cannot-links between
    different-person faces in the same cluster (both are mistakes of the unconstrained clustering)."""
    n = len(y)
    musts, cans = [], []
    for _ in range(200000):
        if len(musts) >= k and len(cans) >= k:
            break
        a, b = int(rng.randint(n)), int(rng.randint(n))
        if a == b:
            continue
        if y[a] == y[b] and lab[a] != lab[b] and len(musts) < k:
            musts.append(("must", a, b))
    by_cluster = {}
    for i, l in enumerate(lab.tolist()):
        by_cluster.setdefault(l, []).append(i)
    multi = [m for m in by_cluster.values() if len(set(y[m])) > 1]
    for mi in rng.permutation(len(multi)):
        m = multi[mi]
        if len(cans) >= k:
            break
        ids = {}
        for i in m:
            ids.setdefault(y[i], i)
        v = list(ids.values())
        pick = rng.choice(len(v), 2, replace=False)
        cans.append(("cannot", v[pick[0]], v[pick[1]]))
    return musts + cans


def main():
    paths, X, N = D.load_set("lfw_clean")
    y = np.array([p.split("/")[0] for p in paths])
    rows = []
    for share in (0.01, 0.10, 0.30):
        for seed in range(5):
            rng = np.random.RandomState(100 * seed + int(share * 100))
            c = build(X, N, T.P, True)
            lab0 = c.labels().copy()
            cons = corrections(y, lab0, rng)
            for kind, a, b in cons:
                (c.add_must_link if kind == "must" else c.add_cannot_link)(a, b)
            lab1 = c.labels()
            changed = not np.array_equal(canon(lab0), canon(lab1))
            gone = rng.choice(len(X), int(share * len(X)), replace=False)
            t = time.perf_counter()
            c.remove(gone)
            lab = c.labels()
            t_del = time.perf_counter() - t
            gs = set(gone.tolist())
            keep = [i for i in range(len(X)) if i not in gs]
            new_id = {old: j for j, old in enumerate(keep)}
            c2 = build(X[keep], N[keep], T.P, True)
            kept_cons = [(k, new_id[a], new_id[b]) for k, a, b in cons if a in new_id and b in new_id]
            for kind, a, b in kept_cons:
                (c2.add_must_link if kind == "must" else c2.add_cannot_link)(a, b)
            same = bool(np.array_equal(canon(lab), canon(c2.labels())))
            rows.append({"share": share, "seed": seed, "corrections_made": len(cons), "corrections_kept": len(kept_cons), "corrections_change_labels": changed, "identical": same, "seconds": t_del})
            print(rows[-1], flush=True)
    save_json("exp30c_deletion_binding_edgeface_s.json", {"protocol": __doc__, "rows": rows,
                                                         "identical_runs": int(sum(r["identical"] for r in rows)), "runs": len(rows), "binding_runs": int(sum(r["corrections_change_labels"] for r in rows))})
    print("identical", sum(r["identical"] for r in rows), "of", len(rows), "binding", sum(r["corrections_change_labels"] for r in rows))


if __name__ == "__main__":
    main()
