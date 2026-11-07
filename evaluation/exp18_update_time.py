"""Re-measure update time with the SHIPPED EdgeFace-S thresholds (review issue 5).

Full LFW clean (EdgeFace-S embeddings), 10 batches, one fixed order. Per batch:
  incremental: c.add(batch) time + c.labels() time (separately)
  re-cluster ours: new clusterer on all faces so far (add all + labels)
  agglomerative avg (batch, sklearn, tuned thr) on all faces so far
Single-threaded BLAS for comparability; also reports the consistency ARI between successive partitions.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ["COVE_FACE_MODEL"] = "edgeface_s"
ROOT = r"D:\wincode\Major-Project"
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
sys.path.insert(0, os.path.join(ROOT, "cove"))
import numpy as np  # noqa: E402
import exp14_disjoint as E  # noqa: E402
from engines.stable_cluster import StableIncrementalClusterer  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402
from sklearn.cluster import AgglomerativeClustering  # noqa: E402
from sklearn.metrics import adjusted_rand_score  # noqa: E402

tuned = json.load(open(os.path.join(ROOT, "evaluation", "results", "exp14_tuned_edgeface_s.json"), encoding="utf8"))["tuned"]
p = tuned["Ours"]["params"]
agg_thr = tuned["Agglomerative (avg)"]["params"]["thr"]
paths, X, N = E.load_set("lfw_clean")
y = np.array([q.split("/")[0] for q in paths])
order = np.random.RandomState(7).permutation(len(X))
X, N, y = X[order], N[order], y[order]
n = len(X)
bounds = np.linspace(0, n, 11).astype(int)


def mk():
    return StableIncrementalClusterer(link_threshold=p["link"], min_neighbors=p["m"], attach_threshold=p["attach"],
                                      merge_threshold=p["merge"], dim=X.shape[1])


inc = mk()
rows, prev = [], None
for b in range(10):
    lo, hi = bounds[b], bounds[b + 1]
    t0 = time.perf_counter(); inc.add(X[lo:hi], N[lo:hi]); t_add = time.perf_counter() - t0
    t0 = time.perf_counter(); lab = inc.labels(); t_lab = time.perf_counter() - t0
    t0 = time.perf_counter(); c = mk(); c.add(X[:hi], N[:hi]); lab2 = c.labels(); t_re = time.perf_counter() - t0
    assert adjusted_rand_score(lab, lab2) == 1.0
    t0 = time.perf_counter()
    AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                            distance_threshold=1 - agg_thr).fit_predict(X[:hi])
    t_agg = time.perf_counter() - t0
    cons = None if prev is None else float(adjusted_rand_score(prev, lab[:len(prev)]))
    prev = lab
    r = dict(faces=int(hi), inc_add_s=t_add, inc_labels_s=t_lab, inc_total_s=t_add + t_lab, recluster_ours_s=t_re,
             agglomerative_s=t_agg, F1=float(evaluate(lab, y[:hi])["B3_F1"]), prev_partition_ARI=cons)
    rows.append(r)
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)
out = os.path.join(ROOT, "evaluation", "results", "exp18_update_time_edgeface_s.json")
json.dump({"protocol": __doc__, "config": p, "agglomerative_thr": agg_thr, "rows": rows}, open(out, "w"), indent=1)
print("saved", out)
