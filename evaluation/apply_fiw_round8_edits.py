"""Round-8 edits: MobileFaceNet FIW results and the reviewer's wording fixes (library overlap, retuned gaps, FIW row)."""
p = r"D:\wincode\Major-Project\paper\v2\cove_paper.tex"
s = open(p, encoding="utf8").read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)


cut_i = s.index(r"\emph{Real family photos.} On FIW we changed nothing")
cut_j = s.index("\n\n", cut_i)
s = s[:cut_i] + r"""\emph{Real family photos.} On FIW we changed nothing (Table~\ref{tab:acc}). Ours scores 0.786, tied with average linkage (0.785;
difference $+0.0006$, $[-0.0046,+0.0061]$) and above single linkage ($+0.011$), DBSCAN ($+0.040$), HDBSCAN ($+0.057$) and
First-Leader ($+0.031$), whose order agreement is 0.64 against 1.000 for ours; the DBSCAN and HDBSCAN gaps are $+0.011$ and
$+0.016$ when every method is re-tuned on the tuning families, which also leaves ours tied with average linkage (0.785 against
0.788, $-0.0024$, $[-0.0082,+0.0036]$). MobileFaceNet gives the same picture (ours 0.783, average linkage 0.782, $+0.0014$,
$[-0.0020,+0.0048]$; re-tuned $-0.0042$, $[-0.0092,+0.0010]$). The 30 libraries share families, so the intervals are probably
too narrow. Scores are far below LFW's, probably because the faces are small (6.7\% were resized, not aligned) and relatives look alike.""" + s[cut_j:]

rep(r"the gain is $+0.0004$ ($[-0.0030,+0.0039]$).",
    r"the gain is $+0.0004$ ($[-0.0030,+0.0039]$). With MobileFaceNet the precise user's gain is $+0.0125$ ($[+0.0066,+0.0186]$); "
    r"ours keeps all corrections, plain re-clustering 21\%, and re-applying 87\% (precise) and 45\% (casual).")
rep(r"""All accuracy
differences are small because most methods already score about 0.99.""",
    r"""On the LFW libraries all accuracy
differences are small because most methods already score about 0.99; on FIW, at about 0.78, ours still only ties average linkage.""")
rep(r"""(finer grids, identity bootstrap,
error-rate sweep, scale and deletion tests)""", r"""(finer grids, identity bootstrap,
error-rate sweep, scale and deletion tests, FIW)""")
rep(r"(FIW's photos are web images of public figures, not private albums)", r"(FIW's photos are web images, mostly of public figures, not private albums)")
rep(r"FIW (family photos) & 0.755 & 0.782 & 0.774 & 0.745 & 0.729 & 0.785 & 0.783 & \textbf{0.786} \\",
    r"FIW (family photos) & 0.755 & 0.782 & 0.774 & 0.745 & 0.729 & 0.785 & 0.783 & 0.786 \\")
rep(r"with the LFW-tuned settings, no retuning).", r"with the LFW-tuned settings, no retuning; four methods are within 0.004).")
open(p, "w", encoding="utf8").write(s)

vp = r"D:\wincode\Major-Project\evaluation\verify_paper_numbers.py"
v = open(vp, encoding="utf8").read()
if "exp31 MBF" not in v:
    add = '''
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
'''
    v = v.replace('print(f"\\n{n_ok} ok, {bad} mismatch")', add + '\nprint(f"\\n{n_ok} ok, {bad} mismatch")')
    open(vp, "w", encoding="utf8").write(v)
gp = r"D:\wincode\Major-Project\.gitignore"
g = open(gp, encoding="utf8").read()
if "datasets/fiw" not in g:
    open(gp, "a", encoding="utf8").write("\n# FIW images: terms forbid redistribution\ndatasets/fiw/\n")
print("round-8 edits applied")
