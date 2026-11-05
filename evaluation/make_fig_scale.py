"""Figure for Experiment 5: indexing time, incremental time and FAISS throughput against library size (measured: 1,000 and 5,000)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import FIGS, load_json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

runs = load_json("exp5_scale.json")["runs"]
ns = sorted(int(k) for k in runs)
init = [runs[str(n)]["initial_index_s"] / 60 for n in ns]
rate = init[-1] / ns[-1]                                           # minutes per item at the largest measured size
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
ax[0].plot(ns, init, "o-", color="#2c6fbb", label="initial indexing (measured)")
ax[0].plot([ns[-1], 10000], [init[-1], rate * 10000], "--", color="#2c6fbb", alpha=0.6, label="projection to 10,000 (not measured)")
for n, v in zip(ns, init): ax[0].annotate(f"{v:.0f} min", (n, v), textcoords="offset points", xytext=(6, -12), fontsize=8)
ax[0].set_xlabel("library size (photos)"); ax[0].set_ylabel("minutes"); ax[0].set_title("Initial indexing time", fontsize=10); ax[0].legend(fontsize=7); ax[0].grid(alpha=.3)
inc = [runs[str(n)]["incremental_100_s"] for n in ns]
ax[1].bar([str(n) for n in ns], inc, color="#c0392b", width=0.5)
for i, v in enumerate(inc): ax[1].text(i, v + 1, f"{v:.0f} s", ha="center", fontsize=9)
r1 = runs["1000"]
ax[1].bar(["1,000 + 100\nre-index all"], [r1["full_reindex_n_plus_100_s"]], color="#7f8c8d", width=0.5)
ax[1].text(2, r1["full_reindex_n_plus_100_s"] + 8, f"{r1['full_reindex_n_plus_100_s']:.0f} s", ha="center", fontsize=9)
ax[1].set_ylabel("seconds"); ax[1].set_title("Adding 100 photos: incremental vs full re-index", fontsize=10); ax[1].grid(alpha=.3, axis="y")
ax[1].set_xlabel("library size before adding")
qps = [runs[str(n)]["faiss"]["single_query_qps"] for n in ns]; bq = [runs[str(n)]["faiss"]["batch1024_qps"] for n in ns]
ax[2].plot(ns, qps, "o-", label="single query"); ax[2].plot(ns, bq, "s-", label="batch of 1,024")
ax[2].set_yscale("log"); ax[2].set_xlabel("vectors in the index"); ax[2].set_ylabel("FAISS queries per second (log)"); ax[2].set_title("FAISS exact search (512-D, top 10)", fontsize=10)
ax[2].legend(fontsize=8); ax[2].grid(alpha=.3, which="both")
plt.tight_layout(); plt.savefig(os.path.join(FIGS, "exp5_scalability.png"), dpi=160); print("saved")
