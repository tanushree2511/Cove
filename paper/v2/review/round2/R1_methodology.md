# Methodology Review Report (Peer Reviewer 1), round 2

## Manuscript Information
- **Title**: Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries
- **Manuscript**: `paper/v2/cove_paper.tex` (commit ce1b15d)
- **Review date**: 2026-11-07
- **Review round**: Round 2 (re-review after Major Revision). Written blind to the other round-2 seats; only `00_reviewer_cards.md` was read.

### Reviewer Identity
Clustering-evaluation researcher (Peer Reviewer 1, Methodology). My remit covers the identity-disjoint split, how fair the tuning is, the bootstrap inference, the corrections protocol, the update-time measurement, test-data leakage, and whether the numbers match the artefacts.

### Overall Recommendation
**Major Revision**

### Confidence Score
4. Core expertise: clustering evaluation and resampling inference. I checked every number against the result JSONs and the code. The face-recognition domain is adjacent to my expertise.

Confidence describes uncertainty and scope only. It never changes consensus counts, severity, decision bearing or arbitration.

### Calibration Status
`NOT_CALIBRATED`

Seat reports always emit `NOT_CALIBRATED`, because the final panel topology is not known until every seat has finished.

### Verification performed (read-only)
- **Code read**:
  - `evaluation/exp14_disjoint.py`, `exp15_corrections.py`, `exp16_pose.py`, `exp17b_track_bridge_hard.py` (header), `exp18_update_time.py`, `exp13_screen.py` (bootstrap);
  - `cove/engines/stable_cluster.py`;
  - `exp7_order_stability.stable`.
- **Result files parsed**:
  - `exp14_disjoint_{edgeface_s,mbf}.json`, `exp14_tuned_{edgeface_s,mbf}.json`;
  - `exp15_corrections_{edgeface_s,mbf}.json`;
  - `exp16_pose_{edgeface_s,mbf}.json`;
  - `exp17b_track_bridge_hard_edgeface_s.json`;
  - `exp18_update_time_edgeface_s.json`;
  - `exp13_screen.json`, `exp13_speed.json`;
  - logs `cache/exp14_mbf*.log` and `cache/exp13_embed*.log`.
- **Small checks of my own** (scripts in the session scratchpad; no repo files changed):
  1. I recomputed the identity split and its coverage of CALFW and CPLFW.
  2. I counted identity overlap across the test libraries.
  3. I recomputed the per-correction hold rates in exp15.
  4. I ran a library-cluster bootstrap of the corrections gain.
  5. I timed one constrained and one unconstrained `labels()` call on the 8,290-face LFW set.

### Number-matching summary

| Claim / cell | Source | Result |
|---|---|---|
| Table I, all 80 F1 cells and the order-agreement row (EdgeFace-S) | exp14_disjoint_edgeface_s.json | **Match** (to 3 d.p.) |
| Bootstrap vs average linkage (±0.009; +0.002..+0.006; low-res −0.006 [−0.008,−0.004]; mixed −0.003 [−0.004,−0.001]; occluded −0.009 [−0.020,+0.001]) | bootstrap_ours_minus | **Match** |
| Tuned setting 0.65/1/0.50/0.55; tuning ARI 0.9822 vs 0.9826 | exp14_tuned_* | **Match**. The MBF grid rows are missing (see W9). |
| Grid sizes 11…360 | GRIDS in exp14 (11/77/11/11/44/20/70/360 = 604) | **Match** |
| CPLFW P/R 0.985/0.733 vs 0.912/0.906; MBF 0.787 vs 0.916 | whole_sets | **Match** |
| Table II, all cells | exp15 table | **Match** with the JSON. The "held" metric itself is mis-computed (W1). |
| "Ten corrections per library" | exp15 per_library | **MISMATCH**: mean 5.4, median 5; only 91/240 runs reached ten (W2) |
| "27% / 26% still hold" | exp15 per_library | **MISMATCH in meaning**: pooled per correction it is 20.3% / 16.9% (W1) |
| Gain +0.010 [+0.008,+0.011] | exp15 ALL | **Match** (0.0097 [0.0082, 0.0114]) |
| Pose: P 0.985→0.786, F1 0.841→0.800; MBF 0.787→0.796; occluded −2.7 | exp16 | **Match** |
| Update time 3.5 / 4.7 / 16.7 s; 0.15 s add; 3.4 s read; ARI ≥ 0.998 | exp18 | **Match** (single run) |
| Track bridge 0.585→0.784, 0.719, F1 0.854→0.860, 171 people | exp17b | **Match** |
| Table III accuracies and asterisks | exp13_screen.json | **Match** |
| Table III latency row (27.5/13.3/8.7/38.7; 19.7/11.8/8.4/43.5), "2.1×" | exp13_speed.json gives 33.4/14.8 and 22.7/14.0 ms (2.25×, 1.63×); no XS/GhostFaceNet entries | **MISMATCH / untraceable** (W9) |
| Abstract "order agreement as low as 0.52" | 0.515 is MBF; EdgeFace-S, the main recogniser, is 0.562 (as in Sec. V-A) | **Inconsistent** (minor) |
| "With MBF the pattern is the same, except HDBSCAN…" | MBF bootstrap | **MISMATCH in substance** (W8) |

### Criterion-Bound Judgements

| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Methodological Rigor: separating tuning from test | Round-1 consensus issue 1; standard held-out protocol | MEETS | `dataset: exp14 split — identity_overlap 0, 79+1,844 per half` | Verified in code and by my own recomputation. | Single split seed. Earlier rounds saw the current test identities (W11). | yes: was blocking in round 1, now resolved |
| Methodological Rigor: fairness of baselines | Round-1 issue 2 | PARTLY_MEETS | `text: Sec. IV "Every method gets a grid over the same similarity range"` | Same data and same rule are given. Budgets, resolution and HDBSCAN's parameter space are not equal (W6). | The paper no longer claims superiority, which limits the impact. | no: the parity claim survives |
| Statistical inference | Resampling standards (unit = independent sampling unit) | PARTLY_MEETS | `dataset: exp14 test libraries — 79 family identities, each in ~11 of 30 libraries` | The bootstrap unit is the library, but libraries share identities (W5). | The direction is known: the CIs are too narrow. | yes, for the "significantly better/worse" statements |
| Validity of the corrections experiment (headline) | Construct validity; adequacy of the control condition | DOES_NOT_MEET | `table: Table II "Fixes held" 27% / 100%` | "Kept" is 100% by construction. "Lost" is mis-computed (W1). The only comparator is a deletion control (W3). The oracle user has no sensitivity test (W4). | Repairable without new methods. | yes: this is the headline claim |
| Evidence sufficiency (corrections) | Claims vs measured quantities | PARTLY_MEETS | `text: Abstract "With ten simulated corrections per library"` | The F1 gain is real and robust to the bootstrap unit. The "ten corrections" wording is wrong (W2). Propagation to new faces is not isolated. | — | yes |
| Results integrity / matching numbers | Artefact check | PARTLY_MEETS | Number-matching summary above | Most cells match. Three mismatches remain (held %, ten corrections, latency row), plus one misdescription (MBF pattern). | — | yes (headline %) |
| Reproducibility | Released scripts and results | PARTLY_MEETS | `dataset: exp14_tuned_mbf.json — "grid": {}, recovered from log` | Scripts are clear and deterministic. The MBF tuning grid and the latency source are missing. | — | no |
| Update-time measurement | Timing practice (repeats, matching workload) | PARTLY_MEETS | `dataset: exp18 — one run, one order, unconstrained path` | Honestly framed (1.3×). Single run; the workload with corrections is not timed (W10). | My spot check suggests the constrained path costs about the same. | no |
| Originality / Literature / Significance | — | NOT_ASSESSED | — | Outside the methodology remit (R2, R3, EIC). | — | — |

These judgements are not totalled or weighted. The recommendation follows from the corrections-validity row and the inference row. Both can be repaired with re-analysis of existing outputs and two or three bounded new runs.

### Summary Assessment
The paper presents an order-invariant incremental face clusterer (single-linkage core, a looser attach threshold, and a centroid merge) that accepts must-link and cannot-link corrections. It evaluates the clusterer on 30 + 30 identity-disjoint LFW-derived libraries under eight conditions, against seven baselines tuned by one rule.

Methodologically, round 2 is a real improvement:
- The identity overlap is gone (I verified this).
- Every method is tuned on the same tuning data by the same rule.
- A re-tuned no-attach ablation exists.
- Paired bootstraps are reported.
- Almost every Table I number matches the JSON.

The new headline experiment, however, does not yet measure what it claims:
- "100% of corrections hold" follows from the hard constraints, not from an experiment.
- The 27% baseline counts 33 of 240 library-conditions with no corrections as "100% held". Per correction, the hold rate is 20% (EdgeFace-S) and 17% (MBF).
- "Ten corrections per library" is really a mean of 5.4.
- The only comparator is the same clusterer with the corrections deleted.
- The simulated user is a perfect oracle, with no sensitivity analysis and no test of wrong corrections.

The bootstrap treats 30 libraries as independent, yet they are resamples of only 79 family identities from a single split, so the ±0.002–0.006 "significant" differences are over-confident. Several mechanistic sentences contradict the paper's own table (attach attribution, the CPLFW "single-linkage core" explanation, the MBF pattern).

None of this is fatal, and most of it can be fixed from existing outputs. The headline needs a correct metric, an informative comparator and a robustness check before acceptance, so I recommend Major Revision.

### Strengths
1. **The identity-disjoint split is real and verified.**
   - `split_identities` splits family and stranger identities separately (seed 2026), and libraries draw only from their own half.
   - The script asserts `identity_overlap == 0`. I recomputed the split myself: 79/79 family, 1,844/1,844 strangers.
   - This resolves round-1 issue 1.
   - Evidence Anchor: `dataset: exp14_disjoint_edgeface_s.json split — identity_overlap 0`
2. **The recogniser choice is pre-declared and robust.**
   - The rule is EdgeFace-S unless it is more than 0.005 ARI below MBF on tuning data.
   - The observed margin is 0.0004, so the decision is far from the boundary and is not sensitive to the rounding in the recovered MBF log.
   - Evidence Anchor: `text: Sec. IV "it is 0.9822 vs. 0.9826, so EdgeFace-S is used"`
3. **The ablation is re-tuned on the same grid.** "Ours, no attach" is tuned over its own 70-point grid, rather than having one component removed from the tuned configuration. This is the correct way to ablate a tuned component.
   - Evidence Anchor: `dataset: exp14 GRIDS "Ours, no attach" — 70 configurations`
4. **Order invariance is checked on several axes.**
   - exp14 uses 3 orders on every test library.
   - exp15 uses 3 orders, 64-face batches and shuffled constraint order.
   - exp18 asserts ARI = 1.0 between the incremental and from-scratch labels after every batch.
   - All gave 1.000. Round-1 W7 is resolved.
   - Evidence Anchor: `table: Table I "Order agreement (min)" — Ours 1.000`
5. **Negative and unfavourable results are reported, and their numbers match the JSONs.** These include the CPLFW deficit with P/R, the failed pose bonus, the 1.3× update gain, and the grid-edge Two-stage threshold.
   - Evidence Anchor: `text: Sec. V-F "The gain over re-running our own method is small (1.3×)"`
6. **The paired bootstrap per condition is implemented correctly within its unit.** It is paired by library index, with the same five shuffled orders for every method and 10,000 resamples. All CIs quoted in Sec. V-B match the JSON.
   - Evidence Anchor: `dataset: exp14 bootstrap_ours_minus — occlude −0.0089 [−0.0196, +0.0006]`

### Weaknesses

### W1: The "27% still hold" baseline figure is mis-computed: libraries with no corrections count as 100% held
**Problem**:
- In `exp15_corrections.py`, `satisfied(lab, cons)` returns 1.0 when `cons` is empty.
- 33 of 240 EdgeFace-S library-conditions (35 of 240 for MBF) received no correction at all, because they were already perfect (F1 = 1.0 at k = 0). Each of them contributes `later_lost_satisfied = 1.0` to the per-library mean.
- The reported 27% is therefore a mean of per-library fractions that includes these empty 100%s.
- My recomputation from `per_library`:

| Recogniser | Pooled over corrections | Per-library mean, excluding empty libraries | Reported |
|---|---|---|---|
| EdgeFace-S | 20.3% (264 of 1,300) | 15.7% | 27% |
| MBF | 16.9% | 13.5% | 26% |

- The look-alike row is the extreme case: the per-library mean is 52%, but pooled it is 25%, from only 24 corrections.

**Evidence Anchor**: `table: Table II "All (8 cond.)" Fixes held "27%\,/\,100%"`
**Why it matters**: This is the paper's headline number. It appears in the abstract, contribution 2, Sec. V-C and the Conclusion. The error happens to make the baseline look better, but a headline metric must be computed correctly. "About three of every four fixed mistakes come back" should read about four in five.
**Suggestion**: Define the metric per correction: pooled over all corrections, with a library-cluster bootstrap CI. Exclude libraries with no corrections, or report them separately. Recompute Table II, the abstract, contribution 2 and the Conclusion. State how many corrections each row is based on.
**Severity**: Major
**Confidence**: 5. Core expertise; verified directly from the code and the JSON.

### W2: "Ten corrections per library" is wrong: the mean is 5.4, and 33 of 240 runs had none
**Problem**:
- `KS = (0,1,2,3,5,10)`, and the loop stops when `pick_correction` returns None, which means nothing is left to fix. For those runs, `now_k10` is filled in with the final F1.
- The distribution of corrections made (EdgeFace-S):

| Corrections made | 10 | 0 | 1 | 2 | 3 | others |
|---|---|---|---|---|---|---|
| Library-conditions | 91 | 33 | 32 | 24 | 16 | rest |

- The mean is 5.4 and the median is 5 (MBF: mean 5.8).
- The occluded, mixed and low-res conditions use about 9.7 corrections on average. Clean, blur, dark and look-alike use far fewer.

**Evidence Anchor**: `text: Abstract "With ten simulated corrections per library, B-Cubed F1 rises from 0.984 to 0.994"`
**Why it matters**: The abstract and Sec. V-C describe the treatment wrongly. The "k = 10" column of Table II really means "up to 10". The "All" averages mix libraries at the ceiling with libraries that used every correction, so the "+0.010" gain is not the effect of ten corrections.
**Suggestion**:
- Write "up to ten (mean 5.4)" and report the distribution.
- In Table II, give the mean number of corrections per row.
- Better still, report gain per correction used, or a curve over libraries that still have mistakes left.
**Severity**: Major
**Confidence**: 5. Verified from `per_library.corrections_made`.

### W3: "100% hold" is a property of the construction, and the only comparator is a deletion control
**Problem**:
- In `_labels_constrained`, a cannot-link always blocks a union, a must-link is always applied (unless it conflicts with a cannot-link), and the merge cannot split clusters. So `later_kept_*_satisfied` is 1.0 by construction. It works as a unit test, not as a measured result.
- The "lost" arm is the same clusterer run with the constraints deleted (`make(X, N)`). Because the clusterer is deterministic, it re-creates almost every mistake. The 20% that "hold" do so only because the 20% new photos happen to change the clustering.
- The experiment therefore measures whether the feature exists, not how good it is compared with other ways of keeping corrections. Missing comparators include:
  - constrained average linkage (Davidson & Ravi), which is the strongest unconstrained baseline in Table I, run with the same constraints;
  - a "freeze-and-assign" re-clustering that keeps user-confirmed people and only assigns new faces, as photo apps commonly do.
- The informative quantity is not isolated either. Sec. III-C claims a correction applies "including all photos added to them later". But `later_kept_k10_F1` is computed over all faces (the 80% "now" plus the 20% "later"), so it is dominated by the very faces the oracle fixed directly.

**Evidence Anchor**: `text: Sec. IV "either with the corrections kept by the clusterer or with plain re-clustering (the behaviour of the current app)"`
**Why it matters**: The headline contrast of 100% vs 27% would hold for any method that stores hard constraints. It cannot support a contribution that is specific to this clusterer. The contribution then rests on the combination of order invariance, incrementality and constraints, and that combination is never compared against a constrained batch method on accuracy and time.
**Suggestion**:
- Present 100% as a correctness check.
- Add constrained average linkage, with F1 after corrections and re-run time at 8k faces.
- Report F1, and same-person pair recall, on the 20% "later" faces only, for kept vs lost. This measures propagation.
- Optionally, add a freeze-and-assign baseline.
**Severity**: Major
**Confidence**: 4. Core expertise in constrained-clustering evaluation; the code paths were read directly.

### W4: The simulated user is a perfect oracle, and the gains and harms are not tested for sensitivity
**Problem**: `pick_correction` uses ground truth in three ways:
1. It fixes the largest remaining mistake, measured by the count of wrongly grouped pairs.
2. It always picks the most informative pair: the central face of the main person, and the intruder face most similar to the main person. That pair is exactly the one that makes the maximum-spanning-forest cut most effective.
3. It is never wrong.

The paper names this as limitation (ii) but does not measure it. Wrong corrections are the flip side of "100% hold": a mistaken cannot-link or must-link persists through every later re-clustering, and its harm is never quantified.

**Evidence Anchor**: `text: Sec. IV "each time fixing the largest remaining mistake"`
**Why it matters**: The F1 rise from 0.984 to 0.994 is an upper bound. It is unknown how much of the gain survives a realistic user, and whether persistent wrong corrections cost more than forgotten right ones. The second question bears directly on the practical claim.
**Suggestion**: Add three cheap variants on the existing libraries:
- (a) fix a random visible mistake rather than the largest;
- (b) pick a random face pair inside the mistaken cluster, or the split person, rather than the optimal pair;
- (c) a 5–10% rate of wrong corrections. For (c), report the F1 loss and how far the error spreads after the "later" import.

Report k against F1 for each variant.
**Severity**: Major
**Confidence**: 4.

### W5: The resampling unit is too small: 30 libraries are resamples of 79 identities from one split
**Problem**:
- Every test library draws 15–40 of the same 79 test-half family identities. By my count, each identity appears in about 11.2 of the 30 test libraries (at most 18). Large identities such as Tony Blair, with 144 faces in library 0, recur across libraries and dominate B-Cubed.
- The paired bootstrap resamples libraries as if they were independent. Identity-level variation is the main source of variance, and the single split (seed 2026) and single library-sampling seed are never varied.
- For corrections, the "All" CI resamples 240 library-conditions, but these are 30 libraries × 7 conditions plus 30 look-alike libraries. A cluster bootstrap over the 60 underlying libraries gives [+0.0084, +0.0109] against the reported [+0.0082, +0.0114]. So that particular gain is robust, but the reported unit is mislabelled ("over libraries").

**Evidence Anchor**: `text: Sec. IV "Differences are tested with a paired bootstrap over libraries (10{,}000 resamples, 95\% intervals)"`
**Why it matters**: Sec. V-B makes significance claims on differences of 0.002–0.006 F1 ("significantly better on clean, blur and dark", "significantly worse on low-res and mixed"). With 79 effective identities and one split, these intervals are too narrow, and the signs may not hold up under another split.
**Suggestion**:
- Repeat exp14 testing over 5 or more split seeds, which is cheap compared with tuning, or use a two-way bootstrap that resamples identities and then libraries.
- Report the spread across splits.
- Soften "significantly" to the level the corrected intervals support.
- Label the corrections bootstrap unit correctly.
**Severity**: Major
**Confidence**: 4. Core expertise; the overlap was measured from `exp14_shared_edgeface_s.npz`.

### W6: "Equal tuning" means the same data and rule, not the same budget, resolution or parameter space
**Problem**: The grids are not equal.
- **Grid size**: 360 configurations for ours, 77 for Two-stage, 44 for DBSCAN, 20 for HDBSCAN, and 11 for each one-threshold method.
- **HDBSCAN** is not on the similarity range at all. Its grid covers only `min_cluster_size` and `min_samples`, with no `cluster_selection_epsilon`. On the whole sets it collapses (CALFW: P 0.232, ARI 0.000, F1 0.358), which suggests a configuration that is degenerate at larger scale rather than a fair baseline.
- **Our link grid** starts at 0.40, not 0.20.
- **One-threshold methods** are tuned at a 0.05 step, although a 0.01 step would cost almost nothing.
- **Two-stage** is tuned at the grid edge (0.70), and its tuning ARI (0.9853) is higher than ours (0.9822), so extending its grid could improve it further at test.

Because the test set is identity-disjoint, a larger grid for ours is not leakage. It is still not "equal terms", and the caption's "same grid range" is inaccurate.

**Evidence Anchor**: `text: Sec. IV "Every method gets a grid over the same similarity range (0.20--0.70, step 0.05)"`
**Why it matters**: The paper claims small significant wins on clean, blur and dark. With a finer grid for one-threshold methods, or an epsilon for HDBSCAN, these could disappear. The parity conclusion would probably survive.
**Suggestion**:
- Use a 0.01 step for one-parameter methods.
- Extend the Two-stage threshold beyond 0.70.
- Add `cluster_selection_epsilon` (or the cosine metric) for HDBSCAN.
- State plainly that the grids differ in size and range.
- Optionally, report the tuning ARI of every method in a supplementary table.
**Severity**: Minor
**Confidence**: 4.

### W7: Two mechanistic explanations contradict Table I
**Problem**:
- **(a) The attach threshold.** Sec. V-B says the margin over single linkage and DBSCAN "is the effect of the attach threshold". On occluded faces, single linkage scores 0.800, "Ours, no attach" 0.907 and Ours 0.943. Removing attach accounts for 3.6 of the 14.3 points. The other 10.7 points come from the centroid merge and the different tuned link threshold (0.60–0.65 against 0.55).
- **(b) The CPLFW gap.** Sec. V-B says average linkage "collects these weak but numerous links; our single-linkage core does not". Yet "Ours, no attach" uses the same single-linkage core and the same merge, at link 0.60 and merge 0.40, and scores CPLFW 0.892: 5.1 points above Ours (0.841) and only 1.7 below average linkage (0.909). For MBF the figures are 0.833 against 0.787. The CPLFW deficit therefore comes mainly from the tuned thresholds (0.65/0.50/0.55), not from the single-linkage core.
- **(c) "The precise setting".** "This is why we kept the precise setting" suggests that precision was preferred on purpose. In fact the setting was chosen by the mean-ARI rule.

**Evidence Anchor**: `table: Table I Occluded row — Single link. 0.800, Ours no attach 0.907, Ours 0.943; CPLFW row — Ours no attach 0.892 vs Ours 0.841`
**Why it matters**: These sentences are the paper's own account of where its accuracy comes from and why it fails on profile faces. As written they are not supported, and they hide a practical finding: a less strict setting of the same method nearly closes the CPLFW gap.
**Suggestion**:
- Attribute the gains to the ablation steps that actually produce them, and add an "Ours, no merge" row if the merge's share should be shown.
- Rewrite the CPLFW explanation around the threshold trade-off, and report the precision/recall of "no attach" on CPLFW.
- Describe the shipped setting as the one the ARI rule selected.
**Severity**: Minor
**Confidence**: 5. Read directly from Table I and the JSON.

### W8: The MBF results are described as "the same pattern", but they are not
**Problem**: For MBF, the comparison of ours against average linkage gives:

| Condition | Difference (ours − avg. linkage) | 95% CI |
|---|---|---|
| Occluded | −0.026 | [−0.041, −0.014] |
| Low-res | +0.0025 | [+0.0012, +0.0039] |
| Mixed | +0.0033 | [+0.0005, +0.0059] |
| JPEG | −0.001 | significant |

- The occluded gap is significant and falls well outside the "±0.009" band claimed for EdgeFace-S.
- Low-res and mixed are significantly better, the opposite sign to EdgeFace-S.
- Against the best MBF baseline on occluded faces (HDBSCAN, 0.963), ours trails by 3.5 points.

**Evidence Anchor**: `text: Sec. V-B "With MBF embeddings the pattern is the same, except that HDBSCAN is best on occluded faces"`
**Why it matters**: The abstract's "within about one point of the best batch baselines on degraded photos" holds only for EdgeFace-S. With MBF, average linkage also beats ours on occluded faces by 2.6 points.
**Suggestion**: Report the MBF bootstrap results in one sentence, or in a supplementary column, and limit the "within about one point" claim to EdgeFace-S.
**Severity**: Minor
**Confidence**: 5.

### W9: Two artefacts are missing (the latency row and the MBF tuning grid); the recogniser CIs ignore dependence
**Problem**:
- **(a) Latency row.** The latency row of Table III (27.5/13.3/8.7/38.7 ms with one thread; 19.7/11.8/8.4/43.5 ms with all cores) and the text's "2.1×" cannot be traced to any released file.
  - `results/exp13_speed.json` gives MBF 33.4/22.7 ms and EdgeFace-S 14.8/14.0 ms (2.25× and 1.63×), and has no entries for EdgeFace-XS or GhostFaceNet.
  - `cache/exp13_embed_*.log` records other runs: EdgeFace-S 43.4 ms, EdgeFace-XS 22.9 ms, GhostFaceNet 167.8 ms.
- **(b) MBF tuning grid.** `exp14_tuned_mbf.json` has `"grid": {}` and the note "recovered from cache/exp14_mbf.log". The MBF tuning values exist only to 4 decimals. Per-configuration rows are lost, so the MBF tuning cannot be audited. The recogniser decision is unaffected, because the margin of 0.0004 is far from the 0.005 rule threshold.
- **(c) Recogniser CIs.** The asterisks in Table III still come from a bootstrap over pairs (`exp13_screen.py`, line 104). Pairs share images and identities, so the intervals are too narrow. This was round-1 W9, and the revision log does not address it.

**Evidence Anchor**: `table: Table III "1 thread & 27.5 & 13.3 & 8.7 & 38.7"`
**Why it matters**: The Declarations state "All numbers are produced by the released scripts", and for these items that cannot be checked. The latency logs also show large run-to-run variance (up to 3×) that the table does not reveal.
**Suggestion**:
- Re-run the speed benchmark for all four models on an idle machine, with repeats, and save the median and IQR to `exp13_speed.json`. Then update Table III and the "2.1×/1.67×" figures.
- Re-run the MBF tuning, or state that its grid rows were lost.
- Use an identity-level bootstrap, or the 10 folds, for the Table III CIs.
**Severity**: Minor
**Confidence**: 5 for (a) and (b); 4 for (c).

### W10: The update time comes from one run, without corrections
**Problem**:
- exp18 times one order and one run per batch size, and only the unconstrained `labels()` path. The constrained path, which is the paper's headline feature, is a separate pure-Python Kruskal pass plus a dense k×k merge loop, and it is not timed.
- My single read-only spot check on the same 8,290 faces gave:
  - unconstrained `labels()`: 7.6 s on the first call and 4.4 s on the second;
  - with two constraints: 4.6 s.
- So the constrained cost appears similar, which reassures. But the run-to-run noise (3.4–7.6 s for the same call) is as large as the 1.2 s difference the paper reports between incremental and from-scratch.

**Evidence Anchor**: `dataset: exp18_update_time_edgeface_s.json — rows[9] inc_total_s 3.53, recluster_ours_s 4.72, single run`
**Why it matters**: "1.3×" and "3.5 s vs 4.7 s" are not reliable at this level of noise, and the workload with corrections is not covered.
**Suggestion**:
- Report the median and IQR of at least 5 repeats, after a warm-up call.
- Add a row with 10 and with 100 corrections.
- State that the read path dominates and grows with library size. The text already does this well.
**Severity**: Minor
**Confidence**: 4. My spot check is a single run.

### W11: Some decisions are still informed by test data, while the paper says everything was fixed in advance
**Problem**:
- **(a) Pose rule.** The pre-declared pose rule passed on tuning data. The authors then rejected the bonus because of the test results on CPLFW and occluded faces. The decision to ship without it was therefore taken on test data. This is reported honestly, but it contradicts "All rules below were fixed before any test number was computed".
- **(b) Pose motivation.** The pose experiment was motivated by the CPLFW test weakness.
- **(c) Earlier development.** The method's structure and its grid ranges (link 0.40–0.70, attach 0.30–0.55, merge 0.40–0.60) were developed in round-1 experiments that used what are now test-half identities and the CALFW/CPLFW test sets.
- **(d) Pose tuning proxy.** The pose score averaged LFW ARI with CFP-FP pair co-clustering accuracy. That proxy rewarded the bonus (+2.4 points pair accuracy) even though LFW ARI fell (0.9822 → 0.9813), which explains why the rule passed and the test failed.

**Evidence Anchor**: `text: Sec. IV "All rules below were fixed before any test number was computed."`
**Why it matters**: The test half is not pristine with respect to the overall research process. The likely bias is small, because thresholds are re-tuned on disjoint data, but the claim should be stated as precisely as the paper states its other limitations.
**Suggestion**:
- Qualify the sentence: the thresholds and selection rules were fixed before testing, but the method design and the grid ranges came from earlier experiments on the same datasets.
- State that the pose decision overrode the pre-declared rule.
- Note that the pose proxy was flawed.
- If feasible, keep a small untouched set (for example, a further disjoint LFW split or a different dataset) as a final check.
**Severity**: Minor
**Confidence**: 4.

### W12: CALFW/CPLFW are described as "restricted to test-half identities", but they exclude tuning identities instead
**Problem**:
- `whole_set` keeps every identity that is not in `tune_ids`.
- The LFW cache that defines the split holds only 8,290 faces from 3,846 identities. Many CALFW/CPLFW identities are in neither half:

| Set | Total identities | Test half | Tuning half (removed) | Neither half (kept) |
|---|---|---|---|---|
| CALFW | 4,025 | 1,363 | 1,315 | 1,347 |
| CPLFW | 3,928 | 1,323 | 1,294 | 1,311 |

- There is no leakage, because the kept identities never appear in tuning. The description is still inaccurate, and the fact that the LFW subset is 8,290 of 13,233 images is not stated.

**Evidence Anchor**: `text: Sec. IV "restricted to test-half identities (8{,}212 and 7{,}718 faces)"`
**Why it matters**: Readers who try to reproduce the split will get different counts. It also matters for interpreting the 1,323 "people" in exp17b.
**Suggestion**: Write "excluding all tuning-half identities", and state the size of the LFW subset and how it was selected (for example, detection success).
**Severity**: Minor
**Confidence**: 5. Recomputed from `cache/emb_edgeface_s_*.npz`.

### W13: Whole-set comparisons are single runs, and the order-agreement statistic is narrow
**Problem**:
- **(a)** CALFW and CPLFW are each clustered once, in one order (seed 77), with no CI. Even so, the paper says ours has "the best F1 (0.947)" on CALFW, against 0.945 for single linkage, and the First-Leader whole-set numbers come from a single order.
- **(b)** "Order agreement" in the code is the lowest ARI against the first order, not the lowest over all pairs of orders. The orders are uniform shuffles, not realistic import sequences (round-1 W14 is unaddressed).
- **(c)** The exp14 test adds all faces in one batch. The "batch split" part of the invariance claim is supported by exp15 and exp18, not exp14, and the text should say so.

**Evidence Anchor**: `text: Sec. V-B "On CALFW it has the best F1 (0.947)"`
**Why it matters**: A difference of 0.002 from one run cannot support "best". The order statistic also understates how much leader methods vary.
**Suggestion**:
- Bootstrap the whole sets by identity, or call 0.947 vs 0.945 a tie.
- Define order agreement exactly as computed, or compute the minimum over all pairs.
- Cite exp15/exp18 for the batch-split invariance.
**Severity**: Minor
**Confidence**: 5.

### Detailed Comments

#### Research Questions & Hypotheses
The paper asks two questions: (1) is the clusterer order-invariant, and (2) do corrections survive re-clustering? Question (1) is answered properly, by a proof sketch plus empirical checks. Question (2) is posed so that the answer is "yes" by construction (W3). The answerable question is a different one: how much do kept corrections improve the clustering of new photos, compared with other ways of keeping them, under realistic users? The paper does not yet ask it.

#### Research Design
- The identity-disjoint split is a clear improvement and is correctly implemented.
- The corrections design has a single 80/20 split per library, which is random and not temporal, and no new people arrive in the "later" batch. This tests re-clustering stability more than a real later import, where new people do appear. A variant in which "later" contains people unseen in "now" would be more realistic.
- The tuning protocol fixes the data and the rule but not the budget (W6).

#### Sampling Strategy
- There are 30 tuning and 30 test libraries, but only 79 family identities per half (W5). Look-alike libraries are formed from the test half only (verified).
- "Eight image conditions" in the abstract counts look-alike, which is not an image condition (Sec. IV lists seven, including clean).

#### Data Collection
The degradations are synthetic and are applied before re-embedding. Only the largest face per photo is used, which is stated in limitation (iii).

#### Analysis Methods
- B-Cubed P/R/F1 and ARI are appropriate metrics. B-Cubed is item-weighted, so large identities such as Tony Blair dominate. Consider also reporting identity-averaged recall.
- The bootstrap pairing is correct, but the unit is too small (W5). The 8 × 7 comparisons have no multiplicity correction; this is minor, given that the paper is conservative in wording.

#### Results Presentation
- The tables match the JSONs, except for the items in the number-matching summary.
- In Table I, bolding ours as best on JPEG (0.9926) when Two-stage and average linkage are both 0.9932 is a rounding artefact. Bold by unrounded value, or bold all ties within the CI.

#### Reproducibility
- The scripts are deterministic, seeded and checkpointed. This is good practice.
- Gaps: the MBF tuning grid and the latency source (W9). The 8,290-image LFW subset is not described (W12).

#### Methodological Fallacies Detected
- **Construct validity / tautological outcome**: "kept" is 100% by construction (W3).
- **Denominator error**: empty correction sets count as fully held (W1).
- **Pseudo-replication**: libraries that share identities are treated as independent (W5).
- **Post-hoc rationalisation**: "we kept the precise setting" (W7c).
- **Test-informed decisions**: the pose rejection (W11).
- **Not found**: no p-hacking or selective reporting. Unfavourable results are reported.

### Questions for Authors
1. On the 20% "later" faces alone, what are B-Cubed F1 and same-person pair recall for kept vs lost corrections? This is the quantity that shows corrections propagating to new photos.
2. With constrained average linkage given the same corrections, what are the "now" and "later" F1 and the re-run time at 8k faces? If it matches your F1, is the contribution then only incrementality and order invariance?
3. How much of the F1 gain remains when the simulated user (a) fixes random visible mistakes, (b) chooses random face pairs, or (c) makes 5–10% wrong corrections? What does one wrong cannot-link or must-link cost after the next import?
4. Across five or more identity-split seeds, do the signs of the clean, blur, dark, low-res and mixed differences against average linkage stay the same?

### Minor Issues
- Abstract: "order agreement as low as 0.52" is the MBF figure. Sec. V-A reports 0.56 for EdgeFace-S, the main recogniser. Use one recogniser, or say which.
- Abstract and Table I caption: "every baseline tuned on the same grid" / "same grid range". The grids differ (W6).
- Table II caption: "30 test libraries", but "All (8 cond.)" includes the 30 separate look-alike libraries.
- Sec. III proof sketch: exact similarity ties "do not arise in practice". Re-imported duplicate photos produce exactly that, and the introduction uses re-import as its motivation. The effect is benign, because duplicates link at s = 1 and land in the same cluster. Say this instead of "do not arise".
- Sec. III: contradictory corrections are "resolved in a fixed order". The order is `sorted(self.must)` by face id, and face ids depend on insertion order, so the proposition does not cover contradictory corrections. Scope it accordingly.
- Sec. VI future work: the baseline F1 of 0.854 differs from Table I's 0.841 because the photo set differs (one profile photo per track person is removed). Say so.
- Sec. V-B: "Against single linkage and DBSCAN, ours is better by 0.4 to 14 points" holds for the library conditions only. On CPLFW, single linkage is better (0.846 vs 0.841).
