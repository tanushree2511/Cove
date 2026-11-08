"""Experiment 18b - read time of the clusterer WITH user corrections (review round 2, R2 W5 / R3).

With any must-/cannot-link present, labels() runs the constrained batch path (_labels_constrained). Same data and
setting as exp18 (8,290 clean LFW faces, EdgeFace-S, shipped exp14 thresholds, one thread). We time labels() with
0, 1, 10 and 50 corrections (exp15's simulated user, picked on the uncorrected result), 3 repeats each, median.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ["COVE_FACE_MODEL"] = "edgeface_s"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
sys.path.insert(0, os.path.join(ROOT, "cove"))
import numpy as np  # noqa: E402
import exp14_disjoint as E  # noqa: E402
from engines.stable_cluster import StableIncrementalClusterer  # noqa: E402
from exp15_corrections import pick_correction  # noqa: E402

p = json.load(open(os.path.join(ROOT, "evaluation", "results", "exp14_tuned_edgeface_s.json"), encoding="utf8"))["tuned"]["Ours"]["params"]
paths, X, N = E.load_set("lfw_clean")
y = np.array([q.split("/")[0] for q in paths])
c = StableIncrementalClusterer(link_threshold=p["link"], min_neighbors=p["m"], attach_threshold=p["attach"],
                               merge_threshold=p["merge"], dim=X.shape[1])
c.add(X, N)
lab = c.labels()
cons = []
while len(cons) < 50:
    k = pick_correction(lab, y, X, set(cons))
    if k is None:
        break
    cons.append(k)
rows = {}
for k in (0, 1, 10, 50):
    c.must, c.cannot = set(), set()
    for kind, a, b in cons[:k]:
        (c.add_must_link if kind == "must" else c.add_cannot_link)(a, b)
    ts = []
    for _ in range(3):
        t0 = time.perf_counter(); c.labels(); ts.append(time.perf_counter() - t0)
    rows[k] = float(np.median(ts))
    print(f"{len(X)} faces, {k:2d} corrections: labels() {rows[k]:.2f} s", flush=True)
out = os.path.join(ROOT, "evaluation", "results", "exp18b_constrained_time_edgeface_s.json")
json.dump({"protocol": __doc__, "faces": len(X), "config": p, "labels_seconds_by_corrections": rows,
           "corrections_available": len(cons)}, open(out, "w"), indent=1)
print("saved", out)
