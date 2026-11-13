"""Experiment 30b - deletion exactness over several random deletions, with corrections present (round-9 review: 'exact' rested on one run).

On the 8,290 clean LFW faces (EdgeFace-S, shipped setting): for 5 seeds x deleted share {1%, 10%, 30%}, make 10 random corrections
(5 same-person from true labels, 5 cannot-link from true labels), delete the random share, and compare the labels with a clusterer built
only from the remaining faces and only the corrections whose faces remain. Counts identical partitions.
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp30b_deletion_seeds.py
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


def corrections(y, rng, k=5):
    cons, tries = [], 0
    n = len(y)
    same = diff = 0
    while (same < k or diff < k) and tries < 100000:
        tries += 1
        a, b = int(rng.randint(n)), int(rng.randint(n))
        if a == b:
            continue
        if y[a] == y[b] and same < k:
            cons.append(("must", a, b)); same += 1
        elif y[a] != y[b] and diff < k:
            cons.append(("cannot", a, b)); diff += 1
    return cons


def main():
    paths, X, N = D.load_set("lfw_clean")
    y = np.array([p.split("/")[0] for p in paths])
    rows = []
    for share in (0.01, 0.10, 0.30):
        for seed in range(5):
            rng = np.random.RandomState(100 * seed + int(share * 100))
            cons = corrections(y, rng)
            c = build(X, N, T.P, True)
            for kind, a, b in cons:
                (c.add_must_link if kind == "must" else c.add_cannot_link)(a, b)
            c.labels()
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
            rows.append({"share": share, "seed": seed, "corrections_kept": len(kept_cons), "identical": same, "seconds": t_del})
            print(rows[-1], flush=True)
    save_json("exp30b_deletion_seeds_edgeface_s.json", {"protocol": __doc__, "rows": rows,
                                                         "identical_runs": int(sum(r["identical"] for r in rows)), "runs": len(rows)})
    print("identical", sum(r["identical"] for r in rows), "of", len(rows))


if __name__ == "__main__":
    main()
