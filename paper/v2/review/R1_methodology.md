# Peer Review Report

## Manuscript Information
- **Title**: Order-Stable Incremental Face Clustering for Local-First Personal Photo Libraries
- **Manuscript ID**: paper/v2/cove_paper.tex
- **Review Date**: 2026-11-06
- **Review Round**: Round 1 review

---

## Reviewer Information

### Reviewer Role
Peer Reviewer 1 (Methodology)

### Reviewer Identity
Clustering-evaluation researcher. Focus: the tuning/test split, use of B-Cubed and ARI, number of orders and libraries, confidence intervals, and leakage between the seed-0 and seed-1 libraries.

### Review Focus
Can the experimental protocol support the paper's claims (order invariance, robustness on held-out degraded libraries, pose/age failures caused by the embedding, the EdgeFace-S gains)? I read the manuscript and checked its protocol and numbers against the released scripts (`evaluation/exp7_order_stability.py`, `exp8_personal_libraries.py`, `exp9_hard.py`, `exp10_tune_robust.py`, `exp11_tune_pose_age.py`, `exp13_screen.py`, `cove/engines/stable_cluster.py`) and result files (`evaluation/results/exp7*.json`, `exp8*.json`, `exp9_hard*.json`, `exp10_tuned_config.json`, `exp13_screen.json`). I also ran one short, read-only script that regenerates the seed-0 and seed-1 library index sets with `make_libraries` to measure how much they overlap. No experiments were re-run.

---

## Overall Assessment

### Recommendation
- [ ] Accept
- [ ] Minor Revision
- [x] **Major Revision**: substantial revisions needed, re-review required after revision
- [ ] Reject

### Confidence Score
4. Clustering evaluation protocol is my core area, and I verified the key numbers directly from the released code and JSON. I am less expert in face-recogniser benchmarking conventions.

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

### Summary Assessment
The paper measures how much greedy leader clustering depends on input order in 30 simulated LFW personal libraries. It proposes a core-link/attach/centroid-merge clusterer that is order-invariant by construction and evaluates it on degraded, look-alike, cross-age and cross-pose data. It then swaps the recogniser for EdgeFace-S. The order-sensitivity measurement is careful and reproducible: every headline number in Sec. V-A (0.756, 5.6, 2.5, 0.990) matches `exp8_personal_libraries.json`, and Tables I and III match `exp9_hard*.json`. The negative results are reported openly, which is to the paper's credit.

The robustness evaluation, however, is not the held-out evaluation the paper describes. The seed-1 "tuning" and seed-0 "test" libraries are drawn from the same 158 identities. 157 of the 158 test family identities, and 99.2% of the test family photos, also appear in the tuning libraries. The baselines were also tuned with a much smaller budget and on clean data only. On top of that, the held-out sets CALFW and CPLFW informed several selection decisions. No clustering comparison carries a confidence interval. The paper's own data also show that, on identical embeddings, other clusterers do 7–10 points better than ours on CPLFW, which contradicts the claim that the pose failures come from the embedding.

All of this is repairable with cheap re-analysis (identity-disjoint splits, equal-budget baseline tuning, paired bootstrap), so I recommend Major Revision rather than rejection.

---

## Strengths

### S1: Order sensitivity measured with a sound, reproducible design
Twenty shuffled orders per library × 30 libraries, plus batch-wise insertion, with order agreement defined as ARI between partitions from two orders. This metric targets the user-visible failure directly. All reported values match the released JSON (`agree_min` worst 0.7559, `F1_spread` max 0.0561 and mean 0.0248, Two-stage `agree_min` worst 0.9897).
**Evidence Anchor**: `text: Sec. V-A "the worst order agreement over 20 shuffled orders. The leader algorithm drops to 0.756"`

### S2: Selection rules fixed in advance and recorded in the code
The tuning scripts state their selection criterion before the search ("highest mean ARI averaged over the 7 conditions", `exp10_tune_robust.py`). The chosen configuration and the full grid are saved. This makes the selection auditable, and it is what let me run the checks below.
**Evidence Anchor**: `text: Sec. IV "Our thresholds were selected on the seed-1 tuning libraries under all seven conditions by the highest mean ARI (72-configuration grid)"`

### S3: Negative results and failure modes reported
Sec. V-C reports that pose/age re-tuning made the held-out results worse, and that a shared-neighbour linking rule did not help. Table I shows the method losing on Occluded, CALFW and CPLFW.
**Evidence Anchor**: `text: Sec. V-C "on the held-out sets it lowered F1 on CALFW (0.934→0.916), CPLFW (0.783→0.778) and occluded faces (0.949→0.885)"`

### S4: Controlled recogniser comparison with a threshold-transfer control
Every recogniser embeds identical crops, differences are paired against the current model, and Table III includes a column for EdgeFace-S run with MBF's thresholds. That column cleanly separates the effect of the recogniser from the effect of re-tuning.
**Evidence Anchor**: `table: Table III — column "EdgeFace-S, MBF thr." (e.g. Occluded 0.650)`

---

## Weaknesses

### W1: The seed-0 test libraries are not held out from the seed-1 tuning libraries
**Problem**: `make_libraries` draws "family" people from the same pool of 158 LFW identities with ≥10 photos for both seeds, and each person contributes up to 200 photos (often all of them). I regenerated both library sets with the released code. 157 of the 158 test family identities appear in the tuning libraries, 99.2% of the test family photos are themselves in the tuning libraries, and 76.2% of all test photos are. The degraded embeddings are computed once per photo (`hard_lfw_<cond>.npz`), so for five of the seven conditions the tuning and test libraries mostly contain the *same degraded embeddings*. Only the random assignment in "mixed" differs. Tuning-set F1 for the chosen configuration (`exp10_tuned_config.json`: clean 0.998, mixed 0.973, jpeg 0.986) is essentially identical to the "held-out" Table I (0.998, 0.972, 0.985). The script docstring calls the split "disjoint", and the abstract calls the test "held-out libraries". The Discussion admits that the libraries "can share people", but in practice they share almost all people and almost all photos.
**Evidence Anchor**: `text: Sec. IV "Libraries with random seed 1 are used only for tuning, seed 0 libraries only for testing."`
**Why it matters**: The robustness numbers in Table I and Table III are in effect tuning-set (in-sample) numbers for our method. A 72-point grid over four thresholds has low capacity, so the optimism is probably small, but it is unmeasured. The paper's main protocol claim ("tuning/test protocol", "held-out") is factually inaccurate.
**Suggestion**: Partition the identities before sampling. For example, split the 158 rich identities and the stranger pool 50/50 with a fixed seed, and draw tuning libraries only from one half and test libraries only from the other. Better, run k-fold cross-validation over identity folds and report the mean ± SD of test F1 across folds. Re-run exp10 and exp9 (minutes of CPU) and report the tuning-to-test gap. Correct the abstract, Sec. IV, and the Discussion accordingly.
**Severity**: Major
**Confidence**: 5 (core expertise: evaluation protocols; verified by regenerating the index sets with the released code)

### W2: The baselines get a much smaller tuning budget, on clean data only
**Problem**: Ours: 72 configurations, chosen on the degraded tuning libraries under seven conditions, by ARI. First-Leader and Agglomerative: one threshold each, tuned on the clean exp1 LFW split by B-Cubed F1. Two-stage: not tuned at all (fixed production values 0.45/0.40, even though `exp1_cluster.py` already contains a two-stage grid). The released results show how much this matters. "Ours v1" (the same algorithm family, tuned only on clean libraries, no attach threshold) is no better than Two-stage under degradation: mixed 0.894 vs 0.894, JPEG 0.880 vs 0.924, low-res 0.928 vs 0.941 (`exp9_hard.json`).
**Evidence Anchor**: `text: Sec. IV "First-Leader (threshold 0.325, the best of a threshold sweep on a separate LFW tuning split); Two-stage (leader at 0.45 plus centroid merge at 0.40, Cove's previous method)"`
**Why it matters**: The 4–8-point gains in Table I mix two causes: the algorithm, and the fact that only our method saw degraded tuning data. The claim that the method is "more robust to degraded photos than leader-based and batch agglomerative baselines" is therefore not isolated.
**Suggestion**: Tune every baseline on the same seed-1 degraded libraries, with the same ARI rule and a comparable grid. For example: a First-Leader threshold sweep, a two-stage (leader, merge) grid of about 72 points, and an agglomerative threshold sweep. Report these as the main baselines, and keep the clean-tuned versions as a secondary row.
**Severity**: Major
**Confidence**: 5 (core expertise; verified from the scripts and `exp9_hard.json`)

### W3: "The attach threshold is the main reason" has no ablation
**Problem**: The causal explanation for the robustness gains is asserted, not tested. The released tuning grid already contains the ablation. The best configuration *without* an attach threshold, re-tuned on the degraded tuning libraries (link 0.50, m 1, merge 0.35), reaches mixed F1 0.937 and JPEG 0.938. The chosen configuration with attach reaches 0.973 and 0.986. Clean-tuned v1 reaches 0.899 and 0.883. On these tuning-set numbers, roughly half of the mixed-condition gain over v1 comes from re-tuning and half from the attach step.
**Evidence Anchor**: `text: Sec. V-B "The attach threshold is the main reason: degraded faces lose similarity to their own identity, fall below the link threshold"`
**Why it matters**: The attach/link separation is the paper's stated robustness mechanism (Discussion: "the attach/link separation makes clustering much more tolerant"). Without an ablation, readers cannot tell how much of the gain it delivers.
**Suggestion**: Add an ablation table on the (identity-disjoint) test libraries with these rows: (i) no attach, clean-tuned; (ii) no attach, degraded-tuned; (iii) attach, degraded-tuned; (iv) optionally, merge off. Report it per condition with CIs (see W5).
**Severity**: Major
**Confidence**: 4 (numbers taken from `exp10_tuned_config.json` grid rows; they are tuning-set values, not test values)

### W4: The held-out sets CALFW/CPLFW (and the test libraries) were used in selection decisions
**Problem**: Three decisions draw on test data. (a) The recogniser screen (`exp13_screen.py`) includes CALFW and CPLFW pairs, and its docstring states it is the gate for which model goes on to clustering. (b) The pose/age-tuned configuration (v3) was rejected on the basis of its *held-out* CALFW/CPLFW/occluded results (Sec. V-C). (c) For EdgeFace-S, both selection rules were run on the test sets (`exp9_hard_edgeface_s.json`: rule (a) pose+age+library vs rule (b) library-ARI), and only rule (b) is reported. Rule (a) is better on low-res (0.986 vs 0.977), mixed (0.982 vs 0.974) and JPEG. Rule (b) is better on Occluded, CALFW and CPLFW. Rule (b) is the original exp10 rule, so choosing it is defensible. But once the rule-(a) results had been seen on the test sets for both recognisers, those sets are no longer untouched.
**Evidence Anchor**: `text: Sec. V-D "We therefore re-tuned on the same 96-point grid shifted by +0.10, using only the tuning libraries and the library-ARI rule"`
**Why it matters**: The headline EdgeFace-S result (CPLFW 0.783→0.854, CALFW 0.934→0.949) and the claim "selected on tuning data only" both rely on CALFW/CPLFW being untouched.
**Suggestion**: Describe the actual sequence of analyses. Report the rule-(a) EdgeFace-S results alongside rule (b). Drop CALFW/CPLFW from the recogniser screen, or say they were used for it. Confirm the final configuration on a set never examined before, for example a held-back identity half of CPLFW/CALFW set aside now and evaluated once, or another cross-pose set.
**Severity**: Major
**Confidence**: 4 (core expertise; verified from the scripts and result files; the chronology is inferred from the file contents and the manuscript text)

### W5: No uncertainty estimates or paired tests for any clustering comparison
**Problem**: Tables I and III report only means over 30 libraries, or a single number for the whole CALFW/CPLFW sets. Claims such as "best or tied-best in seven of the ten conditions" (Clean 0.998 vs 0.996, Dark 0.995 vs 0.990) and "matches MBF on every degraded condition (within 0.4 points)" are made without CIs, a test, or an equivalence margin. The libraries give a natural paired design (same 30 libraries, every method), and the per-library values are already computed in `exp9_hard.py` but only the mean, worst and max-spread are saved.
**Evidence Anchor**: `table: Table I — caption "mean over 30 libraries; whole set for CALFW/CPLFW" with no SD or CI column`
**Why it matters**: Sub-point differences cannot be called "best" or "matches" without uncertainty. The CPLFW +7.1 and CALFW +1.5 come from a single clustering of one set, so their sampling variability is unknown.
**Suggestion**: Save the per-library F1/ARI. For each method pair, report the paired mean difference with a 95% bootstrap CI over libraries, and/or a Wilcoxon signed-rank test with Holm correction. For CALFW/CPLFW, use an identity-level (cluster) bootstrap. State an equivalence margin (e.g. ±0.5 points) for the "matches" claim and test it (TOST, or a CI inside the margin).
**Severity**: Major
**Confidence**: 5 (core expertise: statistical reporting for clustering benchmarks)

### W6: The pose/age failures are attributed to the embedding, but same-embedding baselines do 7–10 points better
**Problem**: The abstract says "our analysis traces them to the face embedding rather than to the clustering". Yet Table I shows that on the *same MBF embeddings*, Agglomerative reaches CPLFW 0.881 and First-Leader 0.857, against 0.783 for ours, and Agglomerative reaches CALFW 0.955 against 0.934. At least 7–10 CPLFW points are therefore recoverable by a different clustering rule on the identical embedding. The Fig. 2 argument is also incomplete. "59% [of split same-person pairs] have a cosine similarity below 0.25, while the 99th percentile of different-person pairs is 0.17" leaves open how many split pairs fall between 0.17 and 0.25, which is a region where pairs are still above 99% of impostors. And the analysis uses CFP-FP pairs, not the CPLFW clustering itself.
**Evidence Anchor**: `table: Table I — CPLFW row, Agglom. 0.881 and First-Leader 0.857 vs Ours 0.783`
**Why it matters**: This causal attribution motivates the entire recogniser section (Sec. V-D) and the Conclusion ("Its remaining errors on profile and aged faces come from the face embedding").
**Suggestion**: Report the fraction of split same-person pairs below the impostor 99th percentile (0.17), not below 0.25. Add an oracle analysis on CPLFW, such as the best B-Cubed F1 that any single threshold, or agglomerative clustering, reaches on these embeddings, to separate embedding-limited error from algorithm-limited error. Rephrase the claim to "partly embedding-limited; the core-link rule also forgoes weak-but-numerous links that average linkage exploits".
**Severity**: Major
**Confidence**: 4 (core expertise; numbers from Table I and `exp9_hard.json`)

### W7: "Max order spread = 0" for ours is not measured, and the shipped configurations were not order-tested on libraries
**Problem**: In `exp9_hard.py` our method runs in exactly one order (`range(N_ORD if not m.startswith("stable") else 1)`), so its zero spread in Table I is true by construction, not an observation. The 20-order and batch-insertion test (Sec. V-A, exp8) used an earlier configuration (m=2, no attach threshold). The shipped configurations (MBF v2 with τ_a=0.35; EdgeFace-S v5) were checked only on whole LFW, in 3 orders (`exp7b_full_lfw_v2.json`). The attach step is a separate code path with its own tie-breaking (see W12).
**Evidence Anchor**: `table: Table I — row "Max order spread", Ours 0`
**Why it matters**: The Conclusion claims "a proof and an experimental check". The proof sketch is sound, but the experimental check does not cover the evaluated or shipped configurations under the library protocol.
**Suggestion**: Re-run exp8 (20 orders plus batch-of-100 insertion) with the v2 and EdgeFace-S v5 configurations, on clean and mixed libraries. In Table I, either report measured spreads or mark the cell as "0 by Prop. 1 (not measured)".
**Severity**: Minor
**Confidence**: 5 (verified in the script)

### W8: CALFW/CPLFW described as "fully separate", but they share identities with LFW
**Problem**: Of the CALFW identities, 4,018 of 4,025 are LFW identities, and so are 3,918 of 3,928 CPLFW identities (checked against the cached path lists). These sets were constructed from LFW identities, although the images are different. The First-Leader/Agglomerative tuning split ("separate LFW tuning split") also draws from LFW identities that appear in the test libraries.
**Evidence Anchor**: `text: Sec. VI "tuning and test libraries are drawn with different seeds from the same pool, so they can share people (CALFW and CPLFW are fully separate)"`
**Why it matters**: The overlap is at the identity level only, and tuning is threshold-level, so the risk is low. But the statement is inaccurate.
**Suggestion**: Change to "image-disjoint but identity-overlapping with LFW", and note the low-capacity tuning as the reason the risk is small.
**Severity**: Minor
**Confidence**: 5 (verified by identity-name intersection)

### W9: The recogniser CIs come from a pair-level bootstrap that ignores dependence, and CALFW/CPLFW use non-official pairs
**Problem**: `exp13_screen.py` resamples individual pairs. Pairs share images and identities, so the resampling units are not independent and the CIs are likely too narrow. CALFW/CPLFW pairs are sampled by the authors from identity labels, not taken from the official 6,000-pair protocol, so the "10-fold verification accuracy" values in Table II are not comparable to published numbers. Twelve comparisons are flagged without multiplicity control.
**Evidence Anchor**: `text: Sec. V-D "with the difference to w600k_mbf and a 95% bootstrap confidence interval"`
**Why it matters**: The asterisks in Table II are probably over-confident. The AgeDB +0.77 for EdgeFace-S (CI [+0.33, +1.18]) would likely survive, but GhostFaceNet's CPLFW −0.45 (upper bound −0.02) may not.
**Suggestion**: Use an identity-level block bootstrap (or McNemar on the official pair lists where they exist), apply Holm correction across the 12 comparisons, and state that the CALFW/CPLFW pairs are self-sampled.
**Severity**: Minor
**Confidence**: 4 (adjacent area: verification benchmarking)

### W10: Update-time evidence: one run, a non-shipped configuration, and a framing that does not fit the measurements
**Problem**: Fig. 3 uses an early configuration (τ_ℓ=0.40, m=3, τ_g=0.35) and a single run. At 13,233 faces, ours takes 11.25 s per update against 15.67 s for full Two-stage re-clustering, only about 1.4× faster, and its cost grows with library size. That growth is consistent with labels(), attachment and the centroid merge being recomputed over all faces at read time. In the same run Two-stage has the higher F1 (0.992 vs 0.987, `exp7_order_stability.json`).
**Evidence Anchor**: `text: Sec. III "The cost of an update is one range search for the new faces plus near-constant-time unions; full re-clustering is never needed."`
**Why it matters**: "Updates are faster than re-clustering" is in the abstract. The measured margin is small, the configuration is not the evaluated one, and there is no variance estimate.
**Suggestion**: Re-time with the shipped configurations over ≥5 repeats and report median and IQR. Time `add()` separately from `labels()`. Qualify the complexity statement (the read-time cost is linear in the number of faces and in the number of adjacency pairs).
**Severity**: Minor
**Confidence**: 5 (verified in the script and JSON)

### W11: The whole-LFW comparison is selective
**Problem**: Sec. V-A compares ours (F1 0.989, ARI 0.991) only with First-Leader's F1. In the released results, Two-stage F1 is 0.992, Agglomerative F1/ARI is 0.991/0.998, and First-Leader's ARI is 0.994, all at or above ours (`exp7_order_stability.json` full_lfw; `exp7b_full_lfw_v2.json`).
**Evidence Anchor**: `text: Sec. V-A "ours scores F1 0.989 and ARI 0.991 with identical output in all orders, against 0.982--0.984 F1 for First-Leader"`
**Why it matters**: Reporting only the comparison that favours the method gives a biased impression on clean data.
**Suggestion**: Report all methods' F1 and ARI on whole LFW, in a table row or a sentence.
**Severity**: Minor
**Confidence**: 5 (verified in the JSON)

### W12: The tie-break uses insertion index, so the proposition is not exact as implemented
**Problem**: Ties are broken "by the smaller face id", but in `cove/engines/stable_cluster.py` (line 141) the face id is the insertion index. An exact tie therefore resolves differently under different orders. The proof sketch dismisses ties as not arising in practice. That holds for real-valued embeddings, but it does not hold for duplicate photos, which are common in personal libraries (re-imports, copies). Duplicates give s=1.0 ties with identical neighbour sets.
**Evidence Anchor**: `text: Sec. III "ties broken by the smaller face id"`
**Why it matters**: This matters only for exact duplicates, but those are exactly the re-import case the Introduction uses as motivation.
**Suggestion**: Break ties with a content-derived key (e.g. a photo hash plus face index), and state this in the proposition.
**Severity**: Minor
**Confidence**: 4 (verified in code; the practical frequency of duplicates is not measured)

### W13: Merge/split claims made without B-Cubed precision and recall
**Problem**: "the only method with no merged people (F1 1.000)" is a claim about precision, but exp9 stores only F1 and ARI. The mean F1 is 0.9996 and the worst look-alike library has F1 0.987, so some errors occur. Elsewhere the text attributes failures to "chain[ing] different people", which is also a precision claim. `evaluate()` already computes B3_P and B3_R.
**Evidence Anchor**: `text: Sec. V-B "On look-alike libraries it is the only method with no merged people (F1 1.000)."`
**Why it matters**: F1 cannot distinguish merges from splits, yet the paper's explanations depend on that distinction.
**Suggestion**: Report B-Cubed precision and recall (or at least precision for look-alike) in Tables I and III, and quote the precision when claiming "no merged people".
**Severity**: Minor
**Confidence**: 5 (verified in the script and JSON)

### W14: The order-sensitivity summary relies on an extreme statistic and on uniform random orders
**Problem**: 0.756 is the minimum over 30 libraries × 190 order pairs, an extreme value that grows more extreme with the number of orders. The typical figures (mean agreement 0.987, mean per-library minimum 0.939) are not given in the text. Uniform permutations are also not how photos are imported: real imports arrive in chronological, person-correlated bursts.
**Evidence Anchor**: `figure: Fig. 1 — per-library worst order agreement over 20 orders`
**Why it matters**: The size of the problem the paper motivates is stated through its worst case only.
**Suggestion**: Report the mean and quantiles of order agreement alongside the minimum. Add a "bursty" order model (e.g. photos grouped by person or by event, then shuffled at the group level) as a sensitivity analysis.
**Severity**: Minor
**Confidence**: 4 (core expertise)

### W15: The chosen MBF thresholds also lie on the edge of the grid
**Problem**: The exp10 grid spans link {0.40, 0.45, 0.50} and merge {0.35, 0.40, 0.45}. The chosen τ_ℓ=0.50 and τ_g=0.45 are both maxima, and the top six configurations all have link=0.50. The Discussion acknowledges the grid-edge issue only for EdgeFace-S.
**Evidence Anchor**: `dataset: results/exp10_tuned_config.json — grid maxima link 0.50, merge 0.45 equal the chosen values`
**Why it matters**: The optimum may lie outside the searched range, which weakens comparisons such as MBF vs EdgeFace-S, since each recogniser may be under-tuned by a different amount.
**Suggestion**: Extend the grid (link up to 0.60, merge up to 0.55) on the identity-disjoint tuning data, and acknowledge the edge in the text.
**Severity**: Minor
**Confidence**: 5 (verified in the JSON)

---

## Detailed Comments

### Title & Abstract
- "held-out libraries" and "thresholds chosen on separate tuning libraries" need correcting (W1). "Our analysis traces them to the face embedding rather than to the clustering" overstates the evidence (W6).

### Introduction
- The research questions are clear, and the contributions map onto sections. Contribution 3 ("stress-test it under a tuning/test protocol") rests on the flawed split (W1).

### Methodology / Research Design
- Design: a simulated benchmark built from LFW, with one dataset family for tuning and testing plus CALFW/CPLFW. That design is appropriate for an engineering paper, provided the splits are identity-disjoint (W1) and all methods get equal tuning effort (W2).
- Sample: 30 libraries of 389–1,421 faces and 77–165 people (matches `exp8_personal_libraries.json`). This is adequate for paired comparisons once per-library values are saved (W5). The number of orders (20 for Sec. V-A, 5 for Table I) is adequate for the leader baselines.
- Metrics: B-Cubed F1 and ARI are appropriate and complementary. Selecting on ARI and reporting B-Cubed F1 is fine, but precision and recall should also be reported (W13). With 50–150 stranger singletons per library, B-Cubed rewards keeping strangers apart. That is reasonable, but report the stranger fraction so readers can interpret F1 levels.
- The proposition's proof sketch is logically sound (adjacency, core status and links are monotone under insertion; the components of the final graph do not depend on order), apart from the tie-break detail (W12).

### Results / Findings
- I verified that Table I and Table III match `exp9_hard.json` (v2 configuration) and `exp9_hard_{mbf,edgeface_s,edgeface_s_noshift}.json`, including the third column of Table III, and that the detection-failure rates match (worst 0.48% occlude, CPLFW 1.09%).
- Selective-reporting risks: W4 (EdgeFace rule (a) results not reported) and W11 (whole-LFW comparison).

### Discussion
- The limitations paragraph is honest, but it understates the tuning/test overlap ("can share people": in fact 157/158 of the family identities and 99% of the family photos are shared) and states CALFW/CPLFW separation inaccurately (W8).

### Conclusion
- "more robust to degraded photos than leader-based and batch agglomerative baselines" needs the baselines tuned on equal terms (W2). "Its remaining errors on profile and aged faces come from the face embedding" conflicts with the paper's own Table I (W6).

### Reproducibility
- Strong: code, grids and per-run JSON are released, and I could check every number I looked for. One weakness: exp9 does not save per-library scores, which prevents the paired analyses requested above.

### Methodological Fallacies Detected
- Overfitting / no true holdout: W1.
- Confounding (algorithm vs tuning data): W2, W3.
- Confirmation-leaning reporting: W4, W11.
- Over-inference in the causal attribution: W6.

---

## Questions for Authors
1. After re-tuning on identity-disjoint libraries, and with the baselines tuned on the same degraded data, does our method's mixed-condition F1 still exceed the best baseline, and by how much, with a 95% CI?
2. Was the decision to report rule (b) for EdgeFace-S taken before or after seeing the CALFW/CPLFW results for rule (a)?
3. On CPLFW with MBF embeddings, what is the best B-Cubed F1 achievable with our method (e.g. a higher τ_g, or a lower τ_ℓ with m≥2) compared with agglomerative clustering? In other words, how much of the 10-point gap is due to the algorithm rather than the embedding?
4. How often do exact-duplicate faces occur in the target use case, and does the implementation produce the same partition under re-ordering when duplicates are present?

---

## Minor Issues
- Sec. IV: CALFW is stated as 12,174 photos, but the cached set has 12,173 embedded faces. Clarify whether this difference is the one detection failure.
- Sec. V-A: say explicitly that the order experiment's library F1 for ours (0.9946) is slightly below Two-stage (0.9952) and Agglomerative (0.9959) on clean libraries, so readers do not read order invariance as a quality gain.
- Table II: state the number of latency repetitions and the spread.
- Sec. V-C: "96 configurations" (exp11) vs "72-configuration grid" (exp10). Name which grid each result comes from.

---

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | quality_rubrics.md | NOT_ASSESSED | — | Outside the methodology remit | Reviewer 2/3 scope | no |
| Methodological Rigor | quality_rubrics.md; reviewer card (tuning/test split, leakage) | DOES_NOT_MEET | W1, W2, W4 | The test libraries mostly reuse tuning photos; baselines are tuned unequally; held-out sets informed selection | Overfitting capacity of a 4-threshold grid is low, so the effect sizes may survive the repair | yes: repairable with re-analysis |
| Evidence Sufficiency | quality_rubrics.md; reviewer card (CIs, number of libraries/orders) | PARTLY_MEETS | W3, W5, W7 | Number of libraries and orders is adequate; no CIs or paired tests; no ablation of the attach step | Per-library data exist, so the fix is cheap | yes: repairable |
| Argument Coherence | quality_rubrics.md | PARTLY_MEETS | W6, W11 | Embedding attribution contradicted by same-embedding baselines; selective whole-LFW comparison | Wording-level fix plus one oracle analysis | yes |
| Writing Quality | quality_rubrics.md | NOT_ASSESSED | — | Outside remit | — | no |
| Literature Integration | quality_rubrics.md | NOT_ASSESSED | — | Reviewer 2 scope | — | no |
| Significance & Impact | quality_rubrics.md | NOT_ASSESSED | — | Reviewer 3 scope | — | no |

Statistical-reporting judgement (APA/statistical_reporting_standards, Step 4a): effect sizes are reported as raw F1/ARI differences (MEETS). Confidence intervals: only for the recogniser screen, and those are pair-level (PARTLY_MEETS / DOES_NOT_MEET for clustering). Multiple comparisons: not controlled (DOES_NOT_MEET). Red flags: test-set reuse in selection (W4).

**Recommendation rationale**: The decision-bearing failures are W1 (no genuine holdout), W2 (unequal baseline tuning), W4 (test reuse) and W5 (no uncertainty). All four are repairable with modest compute and re-analysis on the existing infrastructure, and W3 and W6 need one ablation and one oracle analysis each. The core contribution, an order-invariant incremental clusterer with a sound proof sketch, is not in doubt. The robustness and recogniser claims need re-validation. Major Revision.

---

## Arithmetic Receipts

no_recomputable_statistics: The manuscript reports no t/z/F/chi-square statistics, p-values, df, or Likert-scale means/SDs. I checked Sec. V-A–E, Tables I–III and the abstract. The only inferential element is the bootstrap CIs in Table II, which none of the bounded procedures covers. Table values were instead cross-checked against the released JSON (consistent; see Results above).
