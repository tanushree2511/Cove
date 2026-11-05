"""Figures for the paper (IEEE single column, 3.5 in). Colors: validated categorical slots 1-3 (blue, orange, aqua),
each series ALSO has its own marker / line style so the figures survive grayscale printing; series are direct-labeled.
Output: paper/v2/figs/*.pdf
"""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(__file__)
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "..", "paper", "v2", "figs")
os.makedirs(OUT, exist_ok=True)
C = {"fl": "#2a78d6", "ts": "#eb6834", "ours": "#1baf7a"}
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.6, "pdf.fonttype": 42})


def load(name):
    return json.load(open(os.path.join(RES, name)))


def fig_order_agreement():
    libs = load("exp8_personal_libraries.json")["libraries"]
    rows = [("First-Leader", "First-Leader (single pass)", C["fl"], "o"),
            ("Two-stage", "Two-stage (current Cove, 0.45/0.40)", C["ts"], "s"),
            ("Ours", "Ours: order-stable incremental", C["ours"], "D")]
    fig, ax = plt.subplots(figsize=(3.5, 1.55))
    rng = np.random.RandomState(0)
    for y, (lab, key, col, mk) in enumerate(rows):
        v = np.array([l[key]["agree_min"] for l in libs])
        ax.scatter(v, y + rng.uniform(-0.18, 0.18, len(v)), s=12, color=col, marker=mk, linewidths=0.4,
                   edgecolors="white", zorder=3)
        rows[y] = (lab + "\nworst " + f"{v.min():.3f}",) + rows[y][1:]
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_xlim(0.74, 1.005)
    ax.set_xlabel("worst ARI between two input orders")
    ax.grid(axis="x", color=GRID, linewidth=0.5); ax.set_axisbelow(True)
    ax.invert_yaxis()
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(OUT, "order_agreement.pdf")); fig.savefig(os.path.join(OUT, "order_agreement.png"), dpi=200)


def fig_streaming():
    s = load("exp7_order_stability.json")["streaming"]
    rows = [("Ours (incremental update)", "Ours (incremental)", C["ours"], "D", "-"),
            ("Two-stage (re-cluster)", "Two-stage (re-cluster each batch)", C["ts"], "s", "--"),
            ("Agglomerative (re-cluster)", "Agglomerative (re-cluster each batch)", C["fl"], "o", ":")]
    fig, ax = plt.subplots(figsize=(3.5, 1.9))
    for lab, key, col, mk, ls in rows:
        x = [r["faces"] / 1000 for r in s[key]]; y = [r["update_s"] for r in s[key]]
        ax.plot(x, y, ls, color=col, linewidth=1.6, marker=mk, markersize=4, markeredgecolor="white", markeredgewidth=0.4)
        ax.text(x[-1] + 0.3, y[-1], lab.split(" (")[0], ha="left", va="center", color=INK, fontsize=7)
    ax.set_xlabel("faces in library (thousands)"); ax.set_ylabel("time to update (s)")
    ax.grid(color=GRID, linewidth=0.5); ax.set_axisbelow(True)
    ax.set_ylim(0, 46); ax.set_xlim(0, 17.5)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(OUT, "streaming.pdf")); fig.savefig(os.path.join(OUT, "streaming.png"), dpi=200)


def fig_similarity():
    """CFP-FP (tuning set, frontal-profile): cosine similarity of same-person pairs that our clustering SPLIT,
    against all different-person pairs. Current recogniser (w600k_mbf)."""
    import sys
    sys.path.insert(0, HERE)
    from common import DS
    from exp7_order_stability import stable
    cfg = load("exp10_tuned_config.json")["config"]
    d = np.load(os.path.join(HERE, "cache", "emb_mbf_tune_cfpfp.npz"))
    E = d["emb"] / np.linalg.norm(d["emb"], axis=1, keepdims=True)
    pos = {p: i for i, p in enumerate(d["paths"].tolist())}
    R = [r for r in csv.DictReader(open(os.path.join(DS, "hardtune", "cfp_fp", "pairs.csv"))) if r["a"] in pos and r["b"] in pos]
    lab = stable(E, np.linalg.norm(d["emb"], axis=1), cfg)
    sim = np.array([E[pos[r["a"]]] @ E[pos[r["b"]]] for r in R]); same = np.array([r["same"] == "1" for r in R])
    split = np.array([lab[pos[r["a"]]] != lab[pos[r["b"]]] for r in R])
    bins = np.linspace(-0.2, 0.9, 45)
    fig, ax = plt.subplots(figsize=(3.5, 1.8))
    ax.hist(sim[~same], bins, color=C["fl"], alpha=0.85, label="different person", edgecolor="white", linewidth=0.3)
    ax.hist(sim[same & ~split], bins, color=C["ours"], alpha=0.85, label="same, grouped", edgecolor="white", linewidth=0.3)
    ax.hist(sim[same & split], bins, color=C["ts"], label="same, split", edgecolor="white", linewidth=0.3,
            hatch="////")
    for t, name in ((cfg["attach"], "attach"), (cfg["link"], "link")):
        ax.axvline(t, color=INK, linewidth=0.7, linestyle="--")
        ax.text(t + 0.01, 610, name, fontsize=6.5, color=INK)
    ax.set_xlabel("cosine similarity of the pair"); ax.set_ylabel("pairs")
    ax.set_ylim(0, 660)
    ax.legend(frameon=False, fontsize=6.5, loc="upper left", bbox_to_anchor=(0.58, 0.9))
    ax.grid(axis="y", color=GRID, linewidth=0.5); ax.set_axisbelow(True)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(OUT, "similarity_split.pdf"))
    fig.savefig(os.path.join(OUT, "similarity_split.png"), dpi=200)
    return {"split_same": int((same & split).sum()), "same": int(same.sum()),
            "split_below_0.25": float((sim[same & split] < 0.25).mean()),
            "diff_p99": float(np.percentile(sim[~same], 99))}


if __name__ == "__main__":
    fig_order_agreement()
    fig_streaming()
    print(fig_similarity())
    for f in ("order_agreement", "streaming"):
        plt.figure()
    print("figures ->", os.path.abspath(OUT))
