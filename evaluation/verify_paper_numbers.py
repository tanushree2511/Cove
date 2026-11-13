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
chk("abstract: ours minus c-avg, precise user (within 0.002)", 0.0010,
    t19["oracle|ours"]["later_F1"] - t19["oracle|c-avg"]["later_F1"], 4)
chk("abstract: ours minus c-avg, casual user", 0.0004, t19["casual|ours"]["later_F1"] - t19["casual|c-avg"]["later_F1"], 4)
chk("abstract: ours minus c-avg, error-prone user (NOT within 0.002)", -0.0027,
    t19["noisy|ours"]["later_F1"] - t19["noisy|c-avg"]["later_F1"], 4)
# ---- exp27 faster constrained average linkage (cost paragraph)
r27 = J("exp27_cavg_fast_timing_edgeface_s.json")["rows"]["8290"]
chk("exp27 c-avg fast 0 corr s", 32, r27["cavg_fast_0_s"], 0)
chk("exp27 c-avg fast 10 corr s", 31, r27["cavg_fast_10_s"], 0)
chk("exp27 ours 0 corr s", 0.6, r27["ours_0_s"], 1)
chk("exp27 ours 10 corr s", 2.0, r27["ours_10_s"], 1)
chk("exp27 ratio with corrections (16x)", 16, r27["cavg_fast_10_s"] / r27["ours_10_s"], 0)
chk("exp27 ratio without corrections (54x)", 54, r27["cavg_fast_0_s"] / r27["ours_0_s"], 0)
# ---- exp28 fairer tuning, identity bootstrap (Sec. V-A); exp29 scaling; exp30 deletion
e28 = J("exp28_fair_tuning_edgeface_s.json")
chk("exp28 avg linkage fine grid overall", 0.9849, e28["table_F1"]["ALL"]["Agglomerative (avg) [fine grid]"], 4)
chk("exp28 avg linkage coarse grid overall", 0.9857, e28["table_F1"]["ALL"]["Agglomerative (avg) [coarse grid]"], 4)
bud = [v for k, v in e28["table_F1"]["ALL"].items() if k.startswith("Ours (budget")]
chk("exp28 ours budget-51 min", 0.9809, min(bud), 4)
chk("exp28 ours budget-51 max", 0.9857, max(bud), 4)
chk("exp28 ours budget-51 mean", 0.9836, float(np.mean(bud)), 4)
chk("exp28 ours full grid overall", 0.9854, e28["table_F1"]["ALL"]["Ours"], 4)
ib = e28["bootstrap_identity_ours_minus"]["Ours"]
A = "Agglomerative (avg) [coarse grid]"
chk("exp28 ours-minus-avg clean", 0.0059, ib["clean"][A]["diff"], 4)
chk("exp28 clean CI lo", 0.0020, ib["clean"][A]["ci95_identity"][0], 4)
chk("exp28 clean CI hi", 0.0119, ib["clean"][A]["ci95_identity"][1], 4)
chk("exp28 ours-minus-avg lowres", -0.0061, ib["lowres"][A]["diff"], 4)
chk("exp28 lowres CI lo", -0.0139, ib["lowres"][A]["ci95_identity"][0], 4)
chk("exp28 lowres CI hi", -0.0008, ib["lowres"][A]["ci95_identity"][1], 4)
chk("exp28 mixed", -0.0025, ib["mixed"][A]["diff"], 4)
chk("exp28 mixed CI lo", -0.0060, ib["mixed"][A]["ci95_identity"][0], 4)
chk("exp28 mixed CI hi", 0.0002, ib["mixed"][A]["ci95_identity"][1], 4)
chk("exp28 occluded", -0.0089, ib["occlude"][A]["diff"], 4)
chk("exp28 occluded CI lo", -0.0219, ib["occlude"][A]["ci95_identity"][0], 4)
chk("exp28 occluded CI hi", 0.0072, ib["occlude"][A]["ci95_identity"][1], 4)
chk("exp28 identities", 1571, e28["n_identities"], 0)
s29 = J("exp29_scaling_edgeface_s.json")["rows"]
chk("exp29 49740 ours 0 corr s", 15, s29["49740"]["ours_0_s"], 0)
chk("exp29 49740 ours 10 corr s", 20, s29["49740"]["ours_10_s"], 0)
chk("exp29 49740 c-avg 0 corr s", 234, s29["49740"]["cavg_cached_0_s"], 0)
chk("exp29 49740 c-avg 10 corr s", 212, s29["49740"]["cavg_cached_10_s"], 0)
chk("exp29 49740 scipy avg s", 174, s29["49740"]["scipy_avg_0_s"], 0)
chk("exp29 49740 build s", 316, s29["49740"]["build_s"], 0)
chk("exp29 ratio c-avg/ours at 50k, 0 corr (15x)", 15, s29["49740"]["cavg_cached_0_s"] / s29["49740"]["ours_0_s"], 0)
chk("exp29 ratio scipy/ours with corr at 50k (9x)", 9, s29["49740"]["scipy_avg_0_s"] / s29["49740"]["ours_10_s"], 0)
chk("exp29 ratio c-avg/ours at 8290 with corr (16x)", 16, s29["8290"]["cavg_cached_10_s"] / s29["8290"]["ours_10_s"], 0)
chk("exp29 ratio c-avg/ours at 8290 no corr (69x)", 69, s29["8290"]["cavg_cached_0_s"] / s29["8290"]["ours_0_s"], 0)
e30 = J("exp30_deletion_edgeface_s.json")
chk("exp30 remove 10% s", 0.59, e30["remove_s"], 2)
chk("exp30 labels after s", 0.5, e30["labels_after_s"], 1)
chk("exp30 rebuild s", 7.0, e30["rebuild_s"], 1)
chk("exp30 identical", 1, float(e30["identical"]), 0)

# ---- exp31: FIW outside-data test
f31 = J("exp31_fiw_transfer_edgeface_s.json")
At, Bt = f31["A_transfer_LFW_tuned"], f31["B_tuned_on_FIW"]
chk("exp31 FIW ours F1 (transfer)", 0.786, At["table"]["Ours"]["B3_F1"], 3)
chk("exp31 FIW avg F1 (transfer)", 0.785, At["table"]["Agglomerative (avg)"]["B3_F1"], 3)
chk("exp31 FIW first-leader F1", 0.755, At["table"]["First-Leader"]["B3_F1"], 3)
chk("exp31 FIW two-stage F1", 0.782, At["table"]["Two-stage"]["B3_F1"], 3)
chk("exp31 FIW single F1", 0.774, At["table"]["Single linkage"]["B3_F1"], 3)
chk("exp31 FIW dbscan F1", 0.745, At["table"]["DBSCAN"]["B3_F1"], 3)
chk("exp31 FIW hdbscan F1", 0.729, At["table"]["HDBSCAN"]["B3_F1"], 3)
chk("exp31 FIW no-attach F1", 0.783, At["table"]["Ours, no attach"]["B3_F1"], 3)
chk("exp31 ours-minus avg (transfer)", 0.0006, At["bootstrap_ours_minus"]["Agglomerative (avg)"]["diff"], 4)
chk("exp31 ours-minus avg CI lo", -0.0046, At["bootstrap_ours_minus"]["Agglomerative (avg)"]["ci95"][0], 4)
chk("exp31 ours-minus avg CI hi", 0.0061, At["bootstrap_ours_minus"]["Agglomerative (avg)"]["ci95"][1], 4)
chk("exp31 ours-minus single", 0.011, At["bootstrap_ours_minus"]["Single linkage"]["diff"], 3)
chk("exp31 ours-minus dbscan", 0.040, At["bootstrap_ours_minus"]["DBSCAN"]["diff"], 3)
chk("exp31 ours-minus hdbscan", 0.057, At["bootstrap_ours_minus"]["HDBSCAN"]["diff"], 3)
chk("exp31 ours-minus first-leader", 0.031, At["bootstrap_ours_minus"]["First-Leader"]["diff"], 3)
chk("exp31 first-leader order agreement", 0.64, At["table"]["First-Leader"]["order_agreement_min"], 2)
chk("exp31 ours order agreement", 1.0, At["table"]["Ours"]["order_agreement_min"], 1)
chk("exp31 retuned ours F1", 0.785, Bt["table"]["Ours"]["B3_F1"], 3)
chk("exp31 retuned avg F1", 0.788, Bt["table"]["Agglomerative (avg)"]["B3_F1"], 3)
chk("exp31 retuned ours-minus avg", -0.0024, Bt["bootstrap_ours_minus"]["Agglomerative (avg)"]["diff"], 4)
chk("exp31 retuned ours-minus avg CI lo", -0.0082, Bt["bootstrap_ours_minus"]["Agglomerative (avg)"]["ci95"][0], 4)
chk("exp31 retuned ours-minus avg CI hi", 0.0036, Bt["bootstrap_ours_minus"]["Agglomerative (avg)"]["ci95"][1], 4)
chk("exp31 FIW faces", 34692, f31["libraries"]["faces"], 0)
chk("exp31 FIW people", 5773, f31["libraries"]["people"], 0)
chk("exp31 FIW fallback crops", 2320, f31["libraries"]["fallback_resized"], 0)
import numpy as np
c31 = J("exp19_correction_baselines_edgeface_s_fiw.json")
rows31 = c31["per_library"]
tb = c31["table"]["ALL"]


def _boot(a, n=10000, seed=0):
    a = np.asarray(a)
    m = a[np.random.RandomState(seed).randint(0, len(a), (n, len(a)))].mean(1)
    return a.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


g = _boot([r["oracle|ours"]["later_F1"] - r["oracle|ours"]["lost_F1"] for r in rows31.values()])
chk("exp31 corr gain precise", 0.0089, g[0], 4)
chk("exp31 corr gain precise CI lo", 0.0049, g[1], 4)
chk("exp31 corr gain precise CI hi", 0.0133, g[2], 4)
g = _boot([r["casual|ours"]["later_F1"] - r["casual|ours"]["lost_F1"] for r in rows31.values()])
chk("exp31 corr gain casual", 0.0069, g[0], 4)
chk("exp31 corr gain casual CI lo", 0.0027, g[1], 4)
chk("exp31 corr gain casual CI hi", 0.0115, g[2], 4)
g = _boot([r["noisy|ours"]["later_F1"] - r["noisy|ours"]["lost_F1"] for r in rows31.values()])
chk("exp31 corr gain error-prone", 0.0004, g[0], 4)
chk("exp31 corr gain error-prone CI lo", -0.0030, g[1], 4)
chk("exp31 corr gain error-prone CI hi", 0.0039, g[2], 4)
chk("exp31 now F1 before", 0.787, tb["oracle|ours"]["now_k0"], 3)
chk("exp31 now F1 after", 0.801, tb["oracle|ours"]["now_k"], 3)
chk("exp31 ours later F1 precise", 0.794, tb["oracle|ours"]["later_F1"], 3)
chk("exp31 discarded later F1", 0.786, tb["oracle|ours"]["lost_F1"], 3)
chk("exp31 plain re-clustering holds (%)", 26, tb["oracle|ours"]["lost_held_share"], 0, 100)
chk("exp31 re-apply holds precise (%)", 86, tb["oracle|ours+reapply"]["held_share"], 0, 100)
chk("exp31 re-apply holds casual (%)", 40, tb["casual|ours+reapply"]["held_share"], 0, 100)
for u, nm, v_ in (("oracle", "precise reapply", 0.0045), ("casual", "casual reapply", 0.0094), ("oracle", "precise c-avg", 0.0030)):
    key = "ours+reapply" if "reapply" in nm else "c-avg"
    chk(f"exp31 ours minus {nm}", v_, tb[f"{u}|{key}"]["ours_minus_this_later_F1"]["diff"], 4)
chk("exp31 ours minus precise reapply CI lo", 0.0016, tb["oracle|ours+reapply"]["ours_minus_this_later_F1"]["ci95"][0], 4)
chk("exp31 ours minus precise reapply CI hi", 0.0077, tb["oracle|ours+reapply"]["ours_minus_this_later_F1"]["ci95"][1], 4)
chk("exp31 ours minus casual reapply CI lo", 0.0061, tb["casual|ours+reapply"]["ours_minus_this_later_F1"]["ci95"][0], 4)
chk("exp31 ours minus casual reapply CI hi", 0.0130, tb["casual|ours+reapply"]["ours_minus_this_later_F1"]["ci95"][1], 4)
chk("exp31 ours minus precise c-avg CI lo", -0.0025, tb["oracle|c-avg"]["ours_minus_this_later_F1"]["ci95"][0], 4)
chk("exp31 ours minus precise c-avg CI hi", 0.0084, tb["oracle|c-avg"]["ours_minus_this_later_F1"]["ci95"][1], 4)
chk("exp31 wrong corrections (error-prone)", 29, tb["noisy|ours"]["wrong_corrections"], 0)
chk("exp31 corrections (error-prone)", 300, tb["noisy|ours"]["corrections"], 0)


# ---- exp31 MobileFaceNet and retuned gaps
m31 = J("exp31_fiw_transfer_mbf.json")
chk("exp31 MBF ours F1", 0.783, m31["A_transfer_LFW_tuned"]["table"]["Ours"]["B3_F1"], 3)
chk("exp31 MBF avg F1", 0.782, m31["A_transfer_LFW_tuned"]["table"]["Agglomerative (avg)"]["B3_F1"], 3)
b_ = m31["A_transfer_LFW_tuned"]["bootstrap_ours_minus"]["Agglomerative (avg)"]
chk("exp31 MBF ours-minus avg", 0.0014, b_["diff"], 4)
chk("exp31 MBF ours-minus avg CI lo", -0.0020, b_["ci95"][0], 4)
chk("exp31 MBF ours-minus avg CI hi", 0.0048, b_["ci95"][1], 4)
b_ = m31["B_tuned_on_FIW"]["bootstrap_ours_minus"]["Agglomerative (avg)"]
chk("exp31 MBF retuned ours-minus avg", -0.0042, b_["diff"], 4)
chk("exp31 MBF retuned CI lo", -0.0092, b_["ci95"][0], 4)
chk("exp31 MBF retuned CI hi", 0.0010, b_["ci95"][1], 4)
chk("exp31 retuned ours-minus dbscan", 0.011, Bt["bootstrap_ours_minus"]["DBSCAN"]["diff"], 3)
chk("exp31 retuned ours-minus hdbscan", 0.016, Bt["bootstrap_ours_minus"]["HDBSCAN"]["diff"], 3)
cm = J("exp19_correction_baselines_mbf_fiw.json")
rm = cm["per_library"]
g = _boot([r["oracle|ours"]["later_F1"] - r["oracle|ours"]["lost_F1"] for r in rm.values()])
chk("exp31 MBF corr gain precise", 0.0125, g[0], 4)
chk("exp31 MBF corr gain precise CI lo", 0.0066, g[1], 4)
chk("exp31 MBF corr gain precise CI hi", 0.0186, g[2], 4)
chk("exp31 MBF plain re-clustering holds (%)", 21, cm["table"]["ALL"]["oracle|ours"]["lost_held_share"], 0, 100)
chk("exp31 MBF re-apply holds precise (%)", 87, cm["table"]["ALL"]["oracle|ours+reapply"]["held_share"], 0, 100)
chk("exp31 MBF re-apply holds casual (%)", 45, cm["table"]["ALL"]["casual|ours+reapply"]["held_share"], 0, 100)


chk("exp25 ours gain CI lo p=0.02", 0.0015, t["0.02|ours"]["gain_ci95"][0], 4)
chk("exp25 ours gain CI hi p=0.02", 0.0054, t["0.02|ours"]["gain_ci95"][1], 4)
chk("exp25 reapply p=0.05", 0.0039, t["0.05|ours+reapply"]["gain_over_discarding"], 4)
chk("exp25 reapply p=0.1", 0.0037, t["0.1|ours+reapply"]["gain_over_discarding"], 4)
chk("exp25 reapply p=0.2", 0.0025, t["0.2|ours+reapply"]["gain_over_discarding"], 4)
chk("exp25 c-avg p=0.05", 0.0028, t["0.05|c-avg"]["gain_over_discarding"], 4)
chk("exp25 c-avg p=0.1", 0.0027, t["0.1|c-avg"]["gain_over_discarding"], 4)
chk("exp31 FIW ours no-attach F1", 0.783, At["table"]["Ours, no attach"]["B3_F1"], 3)

print(f"\n{n_ok} ok, {bad} mismatch")
