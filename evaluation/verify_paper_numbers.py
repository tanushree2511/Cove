"""Targeted check of every NEW number the E1-E5 revision put in the paper against the results JSONs.
Each line: paper's value (as printed) vs value computed from the file. Prints MISMATCH when the printed value is not the
rounded file value."""
import json
import os

R = r"D:\wincode\Major-Project\evaluation\results"


def J(n):
    return json.load(open(os.path.join(R, n), encoding="utf8"))


bad = 0
n_ok = 0


def chk(name, paper, value, nd=None, scale=1.0):
    """paper: number as printed; value: from file; compared after rounding the file value to the printed precision."""
    global bad, n_ok
    v = value * scale
    if nd is None:
        nd = len(str(paper).split(".")[1]) if "." in str(paper) else 0
    ok = abs(round(v, nd) - float(paper)) < 10 ** -(nd + 3)
    if ok:
        n_ok += 1
    else:
        bad += 1
    print(("ok       " if ok else "MISMATCH ") + f"{name}: paper {paper} | file {v:.6f}")


# ---- E1 exactness and timing (exp20)
for m in ("edgeface_s", "mbf"):
    d = J(f"exp20_exact_{m}.json")
    chk(f"exp20 {m} identical plain", 240, d["identical_plain"], 0)
    chk(f"exp20 {m} identical corrected", 240, d["identical_corrected"], 0)
t = J("exp20_timing_edgeface_s.json")
chk("exp20 ref 0 corrections s", 4.9, t["ref_0_s"], 1)
chk("exp20 fast 0 corrections s", 0.5, t["fast_0_s"], 1)
chk("exp20 ref 10 corrections s", 4.5, t["ref_10_s"], 1)
chk("exp20 ref 50 corrections s", 5.1, t["ref_50_s"], 1)
chk("exp20 fast 10 corrections s", 1.9, t["fast_10_s"], 1)
chk("exp20 fast 50 corrections s", 2.2, t["fast_50_s"], 1)
chk("exp20 speed-up with corrections (2.3x)", 2.3, t["ref_50_s"] / t["fast_50_s"], 1)
chk("exp20 speed-up plain (~10x, 'about ten times')", 10, t["ref_0_s"] / t["fast_0_s"], 0)
# ---- E2 two devices (exp21)
for m, frozen_n, minari in (("edgeface_s", 127, 0.89), ("mbf", 74, 0.91)):
    d = J(f"exp21_replicas_{m}.json")["table"]
    chk(f"exp21 {m} ours identical", 240, d["ours"]["identical_count"], 0)
    chk(f"exp21 {m} c-avg identical", 240, d["c-avg"]["identical_count"], 0)
    chk(f"exp21 {m} frozen identical", frozen_n, d["frozen+log"]["identical_count"], 0)
    chk(f"exp21 {m} frozen min ARI", minari, d["frozen+log"]["min_ari_between"], 2)
d = J("exp21_replicas_edgeface_s.json")["table"]
chk("exp21 edgeface frozen share (abstract 53%)", 53, d["frozen+log"]["identical_share"], 0, 100)
chk("exp21 edgeface ours F1", 0.992, d["ours"]["F1"], 3)
chk("exp21 edgeface frozen F1", 0.987, d["frozen+log"]["F1"], 3)
chk("exp21 mbf frozen share (table 31%)", 31, J("exp21_replicas_mbf.json")["table"]["frozen+log"]["identical_share"], 0, 100)
# ---- E3 retraction (exp22)
for m, nlib, fi, ff_after, ff_never, ours_after, auc in (
        ("edgeface_s", 104, 5, 0.974, 0.980, 0.980, 0.60), ("mbf", 98, 9, 0.963, 0.969, 0.981, 0.63)):
    d = J(f"exp22_undo_{m}.json")["table"]
    chk(f"exp22 {m} libraries with wrong click", nlib, d["libraries_with_wrong_correction"], 0)
    chk(f"exp22 {m} ours identical share", 100, d["ours"]["identical_share"], 0, 100)
    chk(f"exp22 {m} frozen identical share", fi, d["frozen"]["identical_share"], 0, 100)
    chk(f"exp22 {m} frozen F1 after", ff_after, d["frozen"]["F1_after_retraction"], 3)
    chk(f"exp22 {m} frozen F1 never", ff_never, d["frozen"]["F1_never_made"], 3)
    chk(f"exp22 {m} ours F1 after", ours_after, d["ours"]["F1_after_retraction"], 3)
    chk(f"exp22 {m} AUC", auc, d["detector"]["auc_low_similarity_flags_wrong"], 2)
d = J("exp22_undo_edgeface_s.json")["table"]
chk("exp22 edgeface ours F1 with mistake (0.970)", 0.970, d["ours"]["F1_with_mistake"], 3)
# ---- E4 recogniser upgrade (exp23)
t = J("exp23_recogniser_upgrade.json")["table"]
a, b = t["mbf->edgeface_s"], t["edgeface_s->mbf"]
chk("exp23 m->e F1 none", 0.9837, a["F1_none"], 4)
chk("exp23 m->e F1 transferred", 0.9873, a["F1_transferred"], 4)
chk("exp23 m->e F1 native", 0.9914, a["F1_native"], 4)
chk("exp23 m->e gain", 0.0036, a["gain_over_none"], 4)
chk("exp23 m->e gain CI lo", 0.0030, a["gain_over_none_ci95"][0], 4)
chk("exp23 m->e gain CI hi", 0.0043, a["gain_over_none_ci95"][1], 4)
chk("exp23 m->e retention %", 47, a["retention"], 0, 100)
chk("exp23 m->e retention CI lo %", 38, a["retention_ci95"][0], 0, 100)
chk("exp23 m->e retention CI hi %", 57, a["retention_ci95"][1], 0, 100)
chk("exp23 m->e corrections", 1372, a["transferred_corrections"], 0)
chk("exp23 m->e held share", 1.0, a["transferred_held_share"], 1)
chk("exp23 e->m retention %", 48, b["retention"], 0, 100)
chk("exp23 e->m retention CI lo %", 40, b["retention_ci95"][0], 0, 100)
chk("exp23 e->m retention CI hi %", 57, b["retention_ci95"][1], 0, 100)
chk("exp23 e->m gain", 0.0048, b["gain_over_none"], 4)
chk("exp23 e->m gain CI lo", 0.0039, b["gain_over_none_ci95"][0], 4)
chk("exp23 e->m gain CI hi", 0.0059, b["gain_over_none_ci95"][1], 4)
# ---- direct cost comparison (exp24)
r = J("exp24_cavg_timing_edgeface_s.json")["rows"]
chk("exp24 c-avg 8290 faces 0 corr s", 261, r["8290"]["cavg_decomposed_0_s"], 0)
chk("exp24 c-avg 8290 faces 10 corr s", 293, r["8290"]["cavg_decomposed_10_s"], 0)
chk("exp24 ours 8290 faces 0 corr s", 0.3, r["8290"]["ours_0_s"], 1)
chk("exp24 ours 8290 faces 10 corr s", 1.3, r["8290"]["ours_10_s"], 1)
chk("exp24 c-avg 1658 10 corr s", 1.1, r["1658"]["cavg_decomposed_10_s"], 1)
chk("exp24 c-avg 3316 10 corr s", 11, r["3316"]["cavg_decomposed_10_s"], 0)
chk("exp24 ours 1658 10 corr s", 0.1, r["1658"]["ours_10_s"], 1)
chk("exp24 ours 3316 10 corr s", 0.3, r["3316"]["ours_10_s"], 1)
chk("exp24 equal at 1658 (decomposed == pure)", 1, float(r["1658"]["cavg_equal_10"]), 0)
chk("exp24 equal at 3316 (decomposed == pure)", 1, float(r["3316"]["cavg_equal_10"]), 0)
# ---- E5 error-rate sweep (exp25)
t = J("exp25_effort_edgeface_s.json")["table"]
for p, want in (("0.0", 0.0065), ("0.02", 0.0034), ("0.05", 0.0009), ("0.1", 0.0010), ("0.2", -0.0057)):
    chk(f"exp25 ours gain p={p}", want, t[f"{p}|ours"]["gain_over_discarding"], 4)
chk("exp25 ours gain CI lo p=0.2", -0.0085, t["0.2|ours"]["gain_ci95"][0], 4)
chk("exp25 ours gain CI hi p=0.2", -0.0030, t["0.2|ours"]["gain_ci95"][1], 4)
chk("exp25 c-avg gain p=0.2", -0.0009, t["0.2|c-avg"]["gain_over_discarding"], 4)
chk("exp25 c-avg gain CI lo p=0.2", -0.0020, t["0.2|c-avg"]["gain_ci95"][0], 4)
chk("exp25 c-avg gain CI hi p=0.2", 0.0002, t["0.2|c-avg"]["gain_ci95"][1], 4)
chk("exp25 reapply gain p=0.2", 0.0025, t["0.2|ours+reapply"]["gain_over_discarding"], 4)
chk("exp25 c-avg reach % p=0", 57, t["0.0|c-avg"]["share_reaching_target"], 0, 100)
chk("exp25 ours reach % p=0", 34, t["0.0|ours"]["share_reaching_target"], 0, 100)
chk("exp25 c-avg median p=0", 3, t["0.0|c-avg"]["median_corrections_to_target"], 0)
chk("exp25 ours median p=0", 4, t["0.0|ours"]["median_corrections_to_target"], 0)
# ---- exp19 numbers used in the revision (new-face F1, corrections per library)
d = J("exp19_correction_baselines_edgeface_s.json")["per_library"]
import numpy as np  # noqa: E402
n = [r["oracle|ours"]["n"] for r in d.values()]
chk("exp19 mean corrections all 240 (5.4)", 5.4, float(np.mean(n)), 1)
chk("exp19 mean corrections among those with >=1 (6.3)", 6.3, float(np.mean([x for x in n if x > 0])), 1)
chk("exp19 libraries with >=1 correction (207)", 207, sum(x > 0 for x in n), 0)
rs = np.random.RandomState(0)
for u, want in (("oracle", -0.0014), ("casual", -0.0017), ("noisy", -0.0057)):
    a = np.array([r[f"{u}|ours"]["later_new_F1"] for r in d.values()])
    c = np.array([r[f"{u}|c-avg"]["later_new_F1"] for r in d.values()])
    chk(f"exp19 new-face F1 ours-minus-c-avg ({u})", want, float((a - c).mean()), 4)
a = np.array([r["oracle|ours"]["later_new_F1"] for r in d.values()]) - np.array([r["oracle|c-avg"]["later_new_F1"] for r in d.values()])
bm = a[rs.randint(0, len(a), (10000, len(a)))].mean(1)
chk("exp19 new-face CI lo (oracle)", -0.0026, float(np.percentile(bm, 2.5)), 4)
chk("exp19 new-face CI hi (oracle)", -0.0002, float(np.percentile(bm, 97.5)), 4)
# ---- abstract claims
t19 = J("exp19_correction_baselines_edgeface_s.json")["table"]["ALL"]
chk("abstract: ours minus c-avg, precise user (within 0.002)", 0.0011,
    t19["oracle|ours"]["later_F1"] - t19["oracle|c-avg"]["later_F1"], 4)
chk("abstract: ours minus c-avg, casual user", 0.0003, t19["casual|ours"]["later_F1"] - t19["casual|c-avg"]["later_F1"], 4)
chk("abstract: ours minus c-avg, error-prone user (NOT within 0.002)", -0.0027,
    t19["noisy|ours"]["later_F1"] - t19["noisy|c-avg"]["later_F1"], 4)
print(f"\n{n_ok} ok, {bad} mismatch")
