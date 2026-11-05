"""Figure for Experiment 3: processing time per video versus retrieval / action quality for every frame-sampling strategy."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import FIGS, load_json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

q = load_json("exp34_video_quality.json")["configs"]
t = {r["strategy"]: r for r in load_json("exp3_timing.json")["results"]}
order = ["Middle frame only (1)", "Uniform 4 frames", "Uniform 8 frames", "Uniform 14 frames", "Uniform 20 frames", "Dense reference (25 frames)",
         "Ours: 14 pos + redundancy filter", "Ours deployed (filter + adaptive CLIP frames)"]
short = {"Middle frame only (1)": "middle frame", "Uniform 4 frames": "uniform 4", "Uniform 8 frames": "uniform 8", "Uniform 14 frames": "uniform 14",
         "Uniform 20 frames": "uniform 20", "Dense reference (25 frames)": "dense 25", "Ours: 14 pos + redundancy filter": "ours: 14 pos + filter (all kept)",
         "Ours deployed (filter + adaptive CLIP frames)": "ours deployed (filter + adaptive)"}
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6))
for a, (key, label) in zip(ax, (("mAP", "Video retrieval mAP (101 action queries)"), ("action_top1", "Zero-shot action accuracy, top-1"))):
    for name in order:
        x = t[name]["total_s"]
        y = q[name]["retrieval_description"]["mAP"] if key == "mAP" else q[name]["action_top1"]
        ours = name.startswith("Ours")
        a.scatter(x, y, s=70 if ours else 45, marker="D" if ours else "o", color="#c0392b" if ours else "#2c6fbb", zorder=3)
        off = (5, 5)
        if "deployed" in name: off = (8, 6)
        if name == "Uniform 4 frames": off = (-8, -14)
        if name.startswith("Ours: 14"): off = (6, -12)
        a.annotate(short[name], (x, y), textcoords="offset points", xytext=off, fontsize=7)
    a.set_xlabel("processing time per video (s): frame extraction + CLIP + face detection, this CPU")
    a.set_ylabel(label); a.grid(alpha=0.3)
ax[0].set_title("Efficiency versus quality, 1,000 UCF101 videos (timing: 30 random videos per strategy)", fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(FIGS, "exp3_efficiency_vs_quality.png"), dpi=160)
print("saved")
