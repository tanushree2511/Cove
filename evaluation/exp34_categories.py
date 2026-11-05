"""Video retrieval and tagging by action type, with successes and failures - the same format as the photo evaluation (5.2).

Baseline = middle-frame embedding (the plain single-frame CLIP approach); ours = the app's filtered keyframes (all kept frames, and the
deployed adaptive-frame version). Categories = UCF101's five action types as grouped in the dataset paper (entered by hand below).
Examples are rendered with real video frames: green border = a video of the queried action, red = another action.
"""
import json
import os
import sys
import textwrap

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, FIGS, nrm, save_json  # noqa: E402
from exp34_analyze import build_configs, retrieval_metrics  # noqa: E402

from config.vision_config import CONFIG  # noqa: E402
from core.classifier import LABELS, LOGIT_SCALE, get_cached_text_features, softmax  # noqa: E402
from core.embedder import encode_query  # noqa: E402
from core.label_taxonomy import LABEL_DEFINITIONS  # noqa: E402

TYPES = {
    "Human-object interaction": "ApplyEyeMakeup ApplyLipstick BlowDryHair BrushingTeeth CuttingInKitchen Hammering HulaHoop JugglingBalls JumpRope Knitting "
                                "Mixing MoppingFloor Nunchucks PizzaTossing ShavingBeard SkateBoarding SoccerJuggling Typing WritingOnBoard YoYo",
    "Body motion only": "BabyCrawling BlowingCandles BodyWeightSquats HandstandPushups HandstandWalking JumpingJack Lunges PullUps PushUps RockClimbingIndoor "
                        "RopeClimbing Swing TaiChi TrampolineJumping WalkingWithDog WallPushups",
    "Human-human interaction": "BandMarching Haircut HeadMassage MilitaryParade SalsaSpin",
    "Playing musical instruments": "Drumming PlayingCello PlayingDaf PlayingDhol PlayingFlute PlayingGuitar PlayingPiano PlayingSitar PlayingTabla PlayingViolin",
}
VDIR = os.path.join(DS, "ucf101", "videos1k")
SHOW = {"Middle frame only (1)": "Middle frame (baseline)", "Uniform 14 frames": "Uniform 14 frames",
        "Ours: 14 pos + redundancy filter": "Ours: filtered keyframes", "Ours deployed (filter + adaptive CLIP frames)": "Ours deployed"}


def middle_frame(name):
    cap = cv2.VideoCapture(os.path.join(VDIR, name))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 60
    cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
    ok, fr = cap.read(); cap.release()
    return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok else np.zeros((120, 160, 3), dtype="uint8")


def main():
    z = np.load(os.path.join(CACHE, "ucf_pool.npz"), allow_pickle=True)
    names = z["names"].tolist(); E, H = z["emb"].astype("float32"), z["hist"].astype("float32")
    dur = (z["total"] / np.maximum(z["fps"], 1e-6)).astype(float)
    meta = {m["video"]: m["label"] for m in json.load(open(os.path.join(DS, "ucf101", "ucf101_1000.json")))}
    classes = [l.split()[1] for l in open(os.path.join(DS, "ucf101", "splits", "ucfTrainTestlist", "classInd.txt")).read().split("\n") if l.strip()]
    types = {c: t for t, s in TYPES.items() for c in s.split()}
    for c in classes:
        types.setdefault(c, "Sports")                                         # every class not listed above is a sport
    assert set(types) == set(classes) and len(classes) == 101, (set(types) ^ set(classes))
    acts = [k for k, v in LABEL_DEFINITIONS.items() if v["group"] == "human_action"]
    y = np.array([classes.index(meta[n]) for n in names])
    cfgs, _, _ = build_configs(E, H, dur, CONFIG.runtime_profile)
    use = {k: cfgs[k][0] for k in SHOW}

    desc = [LABEL_DEFINITIONS[acts[c]]["prompts"][1] for c in range(101)]
    Q = np.stack([encode_query(q) for q in desc])
    rel = np.stack([y == c for c in range(101)])
    F = get_cached_text_features()
    truth = np.array([LABELS.index(acts[c]) for c in y])
    type_of_class = np.array([types[c] for c in classes]); type_of_video = type_of_class[y]
    order = list(TYPES) + ["Sports"]

    per_cfg = {}
    for k, V in use.items():
        per = retrieval_metrics(Q @ V.T, rel)
        top1 = np.argmax(softmax(LOGIT_SCALE * (V @ F.T)), axis=1) == truth
        per_cfg[k] = (per, top1)
    table = {}
    for t in order:
        qm = type_of_class == t; vm = type_of_video == t
        table[t] = {"queries": int(qm.sum()), "videos": int(vm.sum())}
        for k, (per, top1) in per_cfg.items():
            table[t][SHOW[k]] = {"mAP": float(per["mAP"][qm].mean()), "Hit@10": float(per["Hit@10"][qm].mean()),
                                  "Recall@10": float(per["Recall@10"][qm].mean()), "action_top1": float(top1[vm].mean())}
    overall = {SHOW[k]: {"mAP": float(per["mAP"].mean()), "Hit@10": float(per["Hit@10"].mean()), "Recall@10": float(per["Recall@10"].mean()),
                         "action_top1": float(top1.mean())} for k, (per, top1) in per_cfg.items()}

    # ---- examples: baseline = middle frame, ours = deployed
    Sb, So = Q @ use["Middle frame only (1)"].T, Q @ use["Ours deployed (filter + adaptive CLIP frames)"].T
    first_rank = lambda S: np.array([int(np.flatnonzero(rel[i][np.argsort(-S[i])])[0]) + 1 for i in range(101)])
    rb, ro = first_rank(Sb), first_rank(So)
    ap_o = per_cfg["Ours deployed (filter + adaptive CLIP frames)"][0]["mAP"]
    fixes = [int(i) for i in np.flatnonzero((ro == 1) & (rb > 1))]
    fails = [int(i) for i in np.flatnonzero(ro > 10)]
    rng = np.random.RandomState(0)
    pick = lambda ids, n: [int(i) for i in rng.permutation(ids)[:n]]
    chosen = [("success", i) for i in pick(fixes, 3)] + [("failure", i) for i in sorted(fails, key=lambda i: ap_o[i])[:3]]
    examples = []
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(chosen), 5, figsize=(13, 2.6 * len(chosen)))
    for r, (kind, qi) in enumerate(chosen):
        top = np.argsort(-So[qi])[:3]
        a_rel = int(np.flatnonzero(rel[qi])[0])
        ax = axes[r]
        ax[0].axis("off")
        ax[0].text(0, 0.95, ("SUCCESS" if kind == "success" else "FAILURE") + "\n" + "\n".join(textwrap.wrap(f'"{desc[qi]}"', 26)) +
                   f"\n\nclass: {classes[qi]}\nfirst relevant rank: ours {ro[qi]}, middle frame {rb[qi]}", va="top", fontsize=8,
                   color="#1a7f37" if kind == "success" else "#b42318")
        for j in range(3):
            v = int(top[j]); good = bool(rel[qi][v])
            ax[1 + j].imshow(middle_frame(names[v])); ax[1 + j].set_xticks([]); ax[1 + j].set_yticks([])
            for sp in ax[1 + j].spines.values():
                sp.set_edgecolor("#1a7f37" if good else "#b42318"); sp.set_linewidth(3)
            ax[1 + j].set_title(f"#{j + 1}: {classes[y[v]]}", fontsize=7)
        ax[4].imshow(middle_frame(names[a_rel])); ax[4].set_xticks([]); ax[4].set_yticks([]); ax[4].set_title("a relevant video", fontsize=7)
        for sp in ax[4].spines.values():
            sp.set_edgecolor("#1a7f37"); sp.set_linewidth(3)
        examples.append({"kind": kind, "query": desc[qi], "class": classes[qi], "rank_ours": int(ro[qi]), "rank_middle": int(rb[qi]),
                         "ours_top3": [{"video": names[int(v)], "class": classes[y[int(v)]], "relevant": bool(rel[qi][int(v)])} for v in top]})
    plt.tight_layout(); plt.savefig(os.path.join(FIGS, "exp4_video_examples.png"), dpi=140)
    counts = {"queries": 101, "ours_first_hit_at_1": int((ro == 1).sum()), "middle_first_hit_at_1": int((rb == 1).sum()),
              "ours_fixes_middle": len(fixes), "middle_beats_ours_at_1": int(((rb == 1) & (ro > 1)).sum()), "no_relevant_in_top10_ours": len(fails)}
    save_json("exp34_categories.json", {"overall": overall, "by_type": table, "examples": examples, "counts": counts})
    print(json.dumps({"overall": overall, "counts": counts}, indent=1))
    for t in order:
        print(t, table[t]["queries"], {k: round(v["mAP"], 3) for k, v in table[t].items() if isinstance(v, dict)}, {k: round(v["action_top1"], 3) for k, v in table[t].items() if isinstance(v, dict)})
    print("DONE")


if __name__ == "__main__":
    main()
