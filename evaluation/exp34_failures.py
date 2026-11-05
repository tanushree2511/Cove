"""Failure analysis for the video experiments: hardest queries and the most common action-tagging confusions (deployed configuration)."""
import json, os, sys, collections
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, load_json, nrm, save_json
os.environ["COVE_USER_DATA"] = os.path.join(CACHE, "userdata")
from core.label_taxonomy import LABEL_DEFINITIONS
from core.classifier import get_cached_text_features, LABELS, LOGIT_SCALE, softmax
from exp34_analyze import redundancy_filter, pick_idx, N_POOL

z = np.load(os.path.join(CACHE, "ucf_pool.npz"), allow_pickle=True)
names = z["names"].tolist(); E, H = z["emb"].astype("float32"), z["hist"].astype("float32")
dur = (z["total"] / np.maximum(z["fps"], 1e-6)).astype(float)
meta = {m["video"]: m["label"] for m in json.load(open(os.path.join(DS, "ucf101", "ucf101_1000.json")))}
classes = [l.split()[1] for l in open(os.path.join(DS, "ucf101", "splits", "ucfTrainTestlist", "classInd.txt")).read().split("\n") if l.strip()]
acts = [k for k, v in LABEL_DEFINITIONS.items() if v["group"] == "human_action"]
y = np.array([classes.index(meta[n]) for n in names])
F = get_cached_text_features()
truth = np.array([LABELS.index(acts[c]) for c in y])

# deployed configuration: 14 positions -> filter -> adaptive number of CLIP frames (4 for these clips, see 5.3)
u14 = pick_idx(N_POOL, 14); V = []
for i in range(len(names)):
    keep = [u14[j] for j in redundancy_filter(H[i][u14])]
    sel = [keep[j] for j in pick_idx(len(keep), min(4, len(keep)))]
    V.append(nrm(E[i][sel].mean(0)))
V = np.stack(V)
pred = np.argmax(softmax(LOGIT_SCALE * (V @ F.T)), axis=1)
conf = collections.Counter((acts[t], LABELS[p]) for t, p in zip(truth, pred) if t != p)
per_class = {c: float(np.mean(pred[y == i] == truth[y == i])) for i, c in enumerate(classes)}
worst = sorted(per_class.items(), key=lambda kv: kv[1])[:10]
q = load_json("exp34_video_quality.json")["configs"]["Ours deployed (filter + adaptive CLIP frames)"]["_per_query"]
ap = np.array(q["mAP"]); hit = np.array(q["Hit@10"])
worst_q = [(classes[i], float(ap[i])) for i in np.argsort(ap)[:8]]
miss = [classes[i] for i in np.flatnonzero(hit == 0)]
best_q = [(classes[i], float(ap[i])) for i in np.argsort(-ap)[:5]]
out = {"top_confusions": [(a, b, n) for (a, b), n in conf.most_common(12)], "lowest_accuracy_classes": worst,
       "lowest_ap_queries": worst_q, "queries_with_no_hit_in_top10": miss, "highest_ap_queries": best_q,
       "classes_perfect_top1": int(sum(v == 1.0 for v in per_class.values())), "classes": len(classes)}
save_json("exp34_failures.json", out)
print(json.dumps(out, indent=1))
