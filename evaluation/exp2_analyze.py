"""Experiment 2, step 2: text->image retrieval on MS COCO val2017 (5,000-image gallery).

  CLIP baseline  : one text prompt (the raw caption), cosine similarity against the 5,000 image embeddings
  Ours           : the app's prompt ensemble (SearchEngine.get_text_embedding), same image embeddings

Each query has exactly one relevant image (the one the caption describes), so mAP equals MRR (reported for both).
Queries are grouped (non-exclusively, by keyword rules) into objects / scenes / activities / people.
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, FIGS, nrm, ranking_metrics, save_json  # noqa: E402
from exp2_embed import load_coco, IMG_DIR  # noqa: E402

PEOPLE = set("man men woman women person people boy boys girl girls child children kid kids guy guys lady ladies player players baby babies "
             "couple family skier surfer skateboarder batter pitcher catcher umpire crowd group toddler gentleman".split())
NOT_VERBS = set("building buildings ceiling clothing evening morning king ring thing things something everything nothing wedding painting "
                "paintings bedding parking sibling spring string icing dining sing stuffing frosting topping toppings pudding".split())
SCENES = set("kitchen bathroom bedroom room street road beach field park city snow mountain mountains ocean sea lake river water forest "
             "restaurant airport station farm yard garden market court stadium harbor intersection sidewalk hill hills desert sky night "
             "outdoor outdoors indoor indoors office store shop zoo church bridge track runway lot pasture meadow trail".split())
OBJECTS = set(("bicycle bike car motorcycle motorbike airplane plane jet bus train truck boat ship traffic light hydrant sign meter bench bird cat dog horse "
               "sheep cow elephant bear zebra giraffe backpack umbrella handbag tie suitcase frisbee skis snowboard ball kite bat glove skateboard "
               "surfboard racket racquet bottle glass cup fork knife spoon bowl banana apple sandwich orange broccoli carrot hot dog pizza donut "
               "cake chair couch sofa plant bed table toilet tv television laptop mouse remote keyboard phone microwave oven toaster sink "
               "refrigerator fridge book clock vase scissors teddy toothbrush").split())


def stem(w):
    return w[:-1] if w.endswith("s") and len(w) > 3 else w


def categorise(caption):
    words = re.findall(r"[a-z]+", caption.lower())
    ws = set(words) | {stem(w) for w in words}
    cats = set()
    if ws & PEOPLE:
        cats.add("people")
    if any(w.endswith("ing") and len(w) > 4 and w not in NOT_VERBS for w in words):
        cats.add("activities")
    if ws & SCENES:
        cats.add("scenes")
    if ws & OBJECTS:
        cats.add("objects")
    return cats


def ranks_of(Q, I, gt, chunk=1000):
    out = np.empty(len(Q), dtype=int)
    for s in range(0, len(Q), chunk):
        S = Q[s:s + chunk] @ I.T
        g = S[np.arange(len(S)), gt[s:s + chunk]]
        out[s:s + chunk] = (S > g[:, None]).sum(1) + 1
    return out


def top_k(Q, I, k=5):
    S = Q @ I.T
    return np.argsort(-S, axis=1)[:, :k]


def bootstrap_diff(ra, rb, k, n=2000, seed=0):
    rng = np.random.RandomState(seed)
    a, b = (ra <= k).astype(float), (rb <= k).astype(float)
    idx = rng.randint(0, len(a), (n, len(a)))
    d = (a[idx].mean(1) - b[idx].mean(1))
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main():
    imgs, by_img = load_coco()
    z = np.load(os.path.join(CACHE, "coco5k_images.npz"), allow_pickle=True)
    files = z["files"].tolist()
    I = nrm(z["emb"])
    file_idx = {f: i for i, f in enumerate(files)}
    cap_of, img_of = {}, {}
    for im in imgs:
        for a in by_img[im["id"]]:
            cap_of[a["id"]] = a["caption"].strip(); img_of[a["id"]] = im["file_name"]

    def load_text(name):
        p = os.path.join(CACHE, f"coco5k_text_{name}.npz")
        if not os.path.exists(p):
            return {}
        t = np.load(p, allow_pickle=True)
        return dict(zip(t["cid"].tolist(), nrm(t["emb"])))

    base = load_text("single_primary"); ens = load_text("ensemble_primary")
    base.update(load_text("single_rest")); ens.update(load_text("ensemble_rest"))
    cids_primary = [a["id"] for im in imgs for a in by_img[im["id"]][:1] if im["file_name"] in file_idx]
    cids_primary = [c for c in cids_primary if c in base and c in ens]
    print(f"gallery: {len(files)} images | primary queries: {len(cids_primary)} | extra queries with both encodings: "
          f"{len([c for c in base if c in ens]) - len(cids_primary)}", flush=True)

    def evaluate_set(cids, tag):
        gt = np.array([file_idx[img_of[c]] for c in cids])
        Qb = np.stack([base[c] for c in cids]); Qe = np.stack([ens[c] for c in cids])
        rb, re_ = ranks_of(Qb, I, gt), ranks_of(Qe, I, gt)
        res = {"queries": len(cids), "gallery": len(files),
               "CLIP baseline (single prompt)": ranking_metrics(rb), "Ours (prompt ensemble)": ranking_metrics(re_),
               "paired_bootstrap_95CI_ours_minus_baseline": {f"R@{k}": bootstrap_diff(re_, rb, k) for k in (1, 5, 10)}}
        cats = {}
        qcats = [categorise(cap_of[c]) for c in cids]
        for cat in ("objects", "scenes", "activities", "people"):
            m = np.array([cat in q for q in qcats])
            if m.sum():
                cats[cat] = {"queries": int(m.sum()), "baseline": ranking_metrics(rb[m]), "ours": ranking_metrics(re_[m])}
        m = np.array([len(q) == 0 for q in qcats])
        if m.sum():
            cats["other (no keyword match)"] = {"queries": int(m.sum()), "baseline": ranking_metrics(rb[m]), "ours": ranking_metrics(re_[m])}
        res["by_category"] = cats
        return res, (cids, gt, rb, re_, Qb, Qe)

    primary, pack = evaluate_set(cids_primary, "primary")
    out = {"primary_5000_queries": primary}
    for k in ("CLIP baseline (single prompt)", "Ours (prompt ensemble)"):
        mm = primary[k]; print(f"{k:<32} R@1={mm['R@1']:.4f} R@5={mm['R@5']:.4f} R@10={mm['R@10']:.4f} MRR={mm['MRR']:.4f}", flush=True)
    all_c = [c for c in base if c in ens and c not in set(cids_primary) and img_of[c] in file_idx]
    if all_c:
        out["all_captions"], _ = evaluate_set(cids_primary + all_c, "all")
        print("all-captions run:", {k: out["all_captions"][k]["R@1"] for k in ("CLIP baseline (single prompt)", "Ours (prompt ensemble)")}, flush=True)

    # image -> text (needs every caption of an image encoded): only when the extra captions exist
    full = [im for im in imgs if im["file_name"] in file_idx and all(a["id"] in base and a["id"] in ens for a in by_img[im["id"]])]
    if len(full) >= 1000:
        for tag, T in (("CLIP baseline (single prompt)", base), ("Ours (prompt ensemble)", ens)):
            cap_ids = [a["id"] for im in full for a in by_img[im["id"]]]
            C = np.stack([T[c] for c in cap_ids]); owner = np.array([file_idx[img_of[c]] for c in cap_ids])
            Iq = I[[file_idx[im["file_name"]] for im in full]]
            S = Iq @ C.T
            first_rank, aps = [], []
            for r, im in enumerate(full):
                rel = owner == file_idx[im["file_name"]]
                order = np.argsort(-S[r]); hits = rel[order]
                pos = np.flatnonzero(hits)
                first_rank.append(pos[0] + 1)
                aps.append(float(np.mean((np.arange(len(pos)) + 1) / (pos + 1))))
            m = ranking_metrics(first_rank); m["mAP"] = float(np.mean(aps)); m["gallery_captions"] = len(cap_ids); m["queries"] = len(full)
            out.setdefault("image_to_text", {})[tag] = m

    # examples: where the ensemble fixes the baseline, where both fail, where the ensemble regresses
    cids, gt, rb, re_, Qb, Qe = pack
    rng = np.random.RandomState(0)
    pick = lambda mask, n: [int(i) for i in rng.permutation(np.flatnonzero(mask))[:n]]
    groups = {"ensemble_fixes_baseline": pick((re_ == 1) & (rb > 1), 4), "both_succeed": pick((re_ == 1) & (rb == 1), 2),
              "both_fail_top10": pick((re_ > 10) & (rb > 10), 4), "ensemble_regresses": pick((re_ > 1) & (rb == 1), 4)}
    tk = top_k(Qe, I, 3)
    ex = {}
    for g, ids in groups.items():
        ex[g] = [{"caption": cap_of[cids[i]], "relevant_image": files[gt[i]], "rank_baseline": int(rb[i]), "rank_ours": int(re_[i]),
                  "ours_top3": [files[j] for j in tk[i]]} for i in ids]
    out["examples"] = ex
    out["example_counts"] = {"ensemble_fixes_baseline(ours r1, baseline not)": int(((re_ == 1) & (rb > 1)).sum()),
                             "ensemble_regresses(baseline r1, ours not)": int(((re_ > 1) & (rb == 1)).sum()),
                             "both_fail_top10": int(((re_ > 10) & (rb > 10)).sum()), "both_r1": int(((re_ == 1) & (rb == 1)).sum())}
    save_json("exp2_image_retrieval.json", out)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    rows = [("Success: ensemble ranks it #1, baseline does not", ex["ensemble_fixes_baseline"][:3], True),
            ("Failure: relevant image not in our top-10", ex["both_fail_top10"][:3], False)]
    fig, axes = plt.subplots(2 * len(rows), 3, figsize=(11, 9.5))
    for r, (title, items, _) in enumerate(rows):
        for c in range(3):
            a1, a2 = axes[2 * r][c], axes[2 * r + 1][c]
            a1.axis("off"); a2.axis("off")
            if c >= len(items):
                continue
            it = items[c]
            a1.imshow(Image.open(os.path.join(IMG_DIR, it["relevant_image"])).convert("RGB"))
            import textwrap
            wrapped = "\n".join(textwrap.wrap('"' + it["caption"] + '"', 36))
            a1.set_title(wrapped + f'\nrelevant image (ours rank {it["rank_ours"]}, baseline {it["rank_baseline"]})', fontsize=7)
            a2.imshow(Image.open(os.path.join(IMG_DIR, it["ours_top3"][0])).convert("RGB"))
            a2.set_title("our top-1" + (" (= relevant)" if it["ours_top3"][0] == it["relevant_image"] else ""), fontsize=7)
        axes[2 * r][0].annotate(title, xy=(0, 1.35), xycoords="axes fraction", fontsize=10, fontweight="bold")
    plt.tight_layout(); plt.savefig(os.path.join(FIGS, "exp2_examples.png"), dpi=150)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
