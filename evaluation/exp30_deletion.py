"""Experiment 30 - deleting photos (external review, 2026-11-12): cost and exactness of StableIncrementalClusterer.remove().

On the 8,290 clean LFW faces (EdgeFace-S, shipped setting, one thread) delete a random 10% of the faces and compare with building a
clusterer from the remaining faces only: labels must be the same partition; time remove() + labels() against a full rebuild.
Run: COVE_FACE_MODEL=edgeface_s python evaluation/exp30_deletion.py
"""
import json
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


def main():
    paths, X, N = D.load_set("lfw_clean")
    c = build(X, N, T.P, True)
    c.labels()
    gone = np.random.RandomState(3).choice(len(X), len(X) // 10, replace=False)
    t = time.perf_counter()
    c.remove(gone)
    t_remove = time.perf_counter() - t
    t = time.perf_counter()
    lab = c.labels()
    t_labels = time.perf_counter() - t
    gs = set(gone.tolist())
    keep = [i for i in range(len(X)) if i not in gs]
    t = time.perf_counter()
    c2 = build(X[keep], N[keep], T.P, True)
    t_rebuild = time.perf_counter() - t
    same = bool(np.array_equal(canon(lab), canon(c2.labels())))
    save_json("exp30_deletion_edgeface_s.json", {"protocol": __doc__, "faces": len(X), "deleted": len(gone),
                                                 "remove_s": t_remove, "labels_after_s": t_labels,
                                                 "rebuild_s": t_rebuild, "identical": same})
    print(t_remove, t_labels, t_rebuild, same)


if __name__ == "__main__":
    main()
