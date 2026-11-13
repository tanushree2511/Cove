"""Put the FIW (outside-data) results into the paper and the number checker. Run once after exp31b/exp19 (FIW)."""
p = r"D:\wincode\Major-Project\paper\v2\cove_paper.tex"
s = open(p, encoding="utf8").read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)


# abstract
rep(r"by 7 points, on profile ones). With corrections", r"by 7 points, on profile ones), and on real family photos (FIW) with no retuning it again ties average linkage. With corrections")

# contributions
rep(r"and a scale test to 50{,}000 faces (Sec.~\ref{sec:time}).", r"an outside test on real family photos (FIW), and a scale test to 50{,}000 faces (Sec.~\ref{sec:time}).")

# protocol
rep(r"after degradation (low-res, blur, JPEG, dark, occluded, mixed).",
    r"""after degradation (low-res, blur, JPEG, dark, occluded, mixed).
\emph{Real family photos:} FIW~\cite{robinson2016fiw,robinson2018fiw} has 34{,}692 face crops of 5{,}773 people in 980 families. We split
the families into two halves (no relatives shared), build 20 tuning and 30 test libraries of 8--16 families, and use the same
detector (no face was found in 2{,}320 crops, which were resized instead of dropped), recogniser, methods and metrics. FIW is used
under its terms (non-commercial research, images not redistributed).""")

# Table I: row and caption
rep(r"CPLFW (pose) & 0.600 & 0.897 & 0.846 & 0.516 & 0.520 & \textbf{0.909} & 0.892 & 0.841 \\",
    "CPLFW (pose) & 0.600 & 0.897 & 0.846 & 0.516 & 0.520 & \\textbf{0.909} & 0.892 & 0.841 \\\\\n"
    "FIW (family photos) & 0.755 & 0.782 & 0.774 & 0.745 & 0.729 & 0.785 & 0.783 & \\textbf{0.786} \\\\")
rep(r"for CALFW/CPLFW).", r"for CALFW/CPLFW; FIW: 30 libraries of real family photos with the LFW-tuned settings, no retuning).")

# results: FIW grouping paragraph
rep("ones.\n", r"""ones.

\emph{Real family photos.} On FIW we changed nothing (Table~\ref{tab:acc}). Ours scores 0.786, tied with average linkage (0.785;
difference $+0.0006$, $[-0.0046,+0.0061]$) and above single linkage ($+0.011$), DBSCAN ($+0.040$), HDBSCAN ($+0.057$) and
First-Leader ($+0.031$), whose order agreement is 0.64 against 1.000 for ours. Re-tuning every method on the tuning families gives
the same picture (ours 0.785, average linkage 0.788, $-0.0024$, $[-0.0082,+0.0036]$). Scores are far below LFW's because the faces are
small and relatives look alike.
""")

# results: FIW corrections
rep(r"""\begin{table}[t]
\caption{Keeping corrections""", r"""\emph{Real family photos.} On the FIW libraries (LFW settings) the precise user's ten corrections raised F1 from 0.787 to 0.801.
After the later photos arrive, ours keeps all of them where plain re-clustering keeps 26\%, and scores 0.794 against 0.786 without
them ($+0.0089$, $[+0.0049,+0.0133]$; casual user $+0.0069$, $[+0.0027,+0.0115]$). Re-applying holds only 86\% (precise) and 40\%
(casual) of the corrections, and ours is better by $+0.0045$ ($[+0.0016,+0.0077]$) and $+0.0094$ ($[+0.0061,+0.0130]$);
constrained average linkage again ties ($+0.0030$, $[-0.0025,+0.0084]$). For the error-prone user (29 of 300 corrections wrong)
the gain is $+0.0004$ ($[-0.0030,+0.0039]$).

\begin{table}[t]
\caption{Keeping corrections""")

# scope
rep(r"simulated from public benchmarks; the three consequences",
    r"simulated from public benchmarks (FIW's photos are web images of public figures, not private albums); the three consequences")

# ethics
rep(r"(web-collected celebrity photos; no new data collected)", r"(web-collected celebrity photos; FIW used under its non-commercial, no-redistribution terms; no new data collected)")
open(p, "w", encoding="utf8").write(s)

# bib
bp = r"D:\wincode\Major-Project\paper\v2\references.bib"
b = open(bp, encoding="utf8").read()
if "robinson2016fiw" not in b:
    b += """

@inproceedings{robinson2016fiw,
  author    = {Robinson, Joseph P. and others},
  title     = {Families in the Wild ({FIW}): Large-Scale Kinship Image Database and Benchmarks},
  booktitle = {Proc. ACM Int. Conf. on Multimedia (MM)},
  year      = {2016}
}

@article{robinson2018fiw,
  author  = {Robinson, Joseph P. and others},
  title   = {Visual Kinship Recognition of Families in the Wild},
  journal = {IEEE Trans. Pattern Analysis and Machine Intelligence},
  year    = {2018}
}
"""
    open(bp, "w", encoding="utf8").write(b)

# number checker
vp = r"D:\wincode\Major-Project\evaluation\verify_paper_numbers.py"
v = open(vp, encoding="utf8").read()
if "exp31" not in v:
    add = '''
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
'''
    v = v.replace('print(f"\\n{n_ok} ok, {bad} mismatch")', add + '\nprint(f"\\n{n_ok} ok, {bad} mismatch")')
    open(vp, "w", encoding="utf8").write(v)
print("edits applied")
