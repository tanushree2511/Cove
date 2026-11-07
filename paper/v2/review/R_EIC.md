# Peer Review Report

## Manuscript Information
- **Title**: Order-Stable Incremental Face Clustering for Local-First Personal Photo Libraries
- **Manuscript ID**: paper/v2/cove_paper.tex (draft)
- **Review Date**: 2026-11-06
- **Review Round**: Round 1 review

---

## Reviewer Information

### Reviewer Role
Journal-Fit Reviewer (internal id EIC)

### Reviewer Identity
Programme-committee member of an IEEE regional conference in computing (e.g. an IEEE India Council conference). Reviews for fit to an applied-systems track, novelty relative to known clustering methods, and whether headline claims are sized to the evidence.

### Review Focus
Is this a coherent applied-systems contribution that fits an IEEE regional computing conference? Is the novelty claim honest relative to incremental DBSCAN / threshold-graph clustering? Do the abstract, contributions list and conclusion claim only what the experiments show, under the configuration actually shipped?

---

## Overall Assessment

### Recommendation
- [ ] Accept
- [ ] Minor Revision
- [x] **Major Revision**
- [ ] Reject

### Confidence Score
4. Applied clustering and face-recognition systems are within my area; I did not re-run the experiments, but I did check a few headline numbers against `evaluation/results/*.json`.

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

### Summary Assessment
The paper looks at a practical problem in local-first photo managers: greedy leader clustering of faces gives different "people" depending on the order photos are imported. The authors measure this on 30 simulated LFW libraries, propose an incremental clusterer (union-find over core faces, a looser attach threshold for weak faces, and an average-linkage merge of centroids), argue that its output depends only on the set of faces, and test it on degraded, look-alike, cross-age and cross-pose data. A second part compares four lightweight recognisers and adopts EdgeFace-S. The topic fits an IEEE regional applied-computing venue well. The writing is plain, the tuning/test split is disciplined, and the paper reports its own failures (pose, age, occlusion), which is rare and welcome. The problems are about sizing the claims, not about fit. (1) At the shipped setting m=1 the method reduces to threshold-graph (single-linkage) components plus nearest-core attachment plus a centroid merge, so the stated anti-chaining mechanism does nothing there, and the novelty over incremental DBSCAN is smaller than the contributions list says. (2) The "updates faster than re-clustering" claim rests on a superseded configuration, and the per-batch timings in the results file grow with library size almost exactly like the re-clustering baseline. (3) The obvious practical baseline, DBSCAN/HDBSCAN as used by the cited systems, is missing. All three can be fixed with reframing and one or two extra runs, so I recommend Major Revision.

---

## Strengths

### S1: Well-motivated, venue-appropriate practical problem
Order dependence in incremental face grouping is a real, user-visible defect (renamed people get reshuffled on re-import). It is framed in terms a practitioner audience will recognise, and it suits an applied-systems track.
**Evidence Anchor**: `text: Sec. I "Two users with the same photos can see different people, and re-importing a library can reshuffle people the user has already named."`

### S2: Clean tuning/test separation and held-out stress sets
Thresholds are chosen on seed-1 libraries and on AgeDB-30/CFP-FP pairs only, and CALFW/CPLFW are used purely as held-out tests. Many regional-conference submissions skip this discipline.
**Evidence Anchor**: `text: Sec. IV "Libraries with random seed~1 are used only for tuning, seed~0 libraries only for testing."`

### S3: Honest reporting of negative results and failure analysis
Sec. V-C reports two failed fixes and uses the similarity distribution (Fig. 2) to trace the pose failure to the embedding. That analysis then motivates the recogniser study, which gives the paper a coherent arc.
**Evidence Anchor**: `figure: Fig. 2 — hatched same-person CFP-FP pairs lying inside the different-person similarity range`

### S4: Controlled recogniser comparison on identical crops with CIs
Embedding the same aligned crops with all four models, with bootstrap CIs and CPU latency on stated hardware, is a fair and useful comparison for practitioners deploying on laptops.
**Evidence Anchor**: `table: Table II — paired differences to w600k_mbf with 95% CI markers and 1-thread / all-core latency`

### S5: Reproducibility and declarations
Code, grids and per-run JSON results are released, and the paper declares hardware, licences and AI-tool use. The JSON values I checked (the streaming timings at 13,233 faces, the blur and clean F1 rows of Table I) match the text.
**Evidence Anchor**: `dataset: evaluation/results/exp7_order_stability.json and exp9_hard.json — values match Sec. V-E and Table I`

---

## Weaknesses

### W1: At the shipped setting (m=1) the anti-chaining mechanism does nothing, and the novelty is overstated
**Problem**: A face is core if |N_l(i)| >= m. At the selected m=1, every face with at least one neighbour above tau_l is core, and all such pairs are linked. So the clusters are just the connected components of the tau_l threshold graph (single linkage at 0.50, or 0.60 for EdgeFace-S). "Non-core" faces are only the faces with no tau_l neighbour, and those could never link anything anyway. The claim that "a blurred photo cannot chain two people together" therefore does not hold for the shipped configuration: a blurred face with one neighbour >= tau_l in each of two people is core and chains them. With m=1, the method is single-linkage components, plus attachment of isolated faces at tau_a, plus a centroid merge. Order invariance of threshold-graph components is a textbook property, and incremental DBSCAN already gives it for core points. Contribution 2 and the abstract's "order-invariant by construction" are true, but they present a known property as the main novelty.
**Evidence Anchor**: `text: Sec. III-B "Non-core faces never link two clusters, so a blurred photo cannot chain two people together"`
**Why it matters**: A PC member who knows DBSCAN will see this at once, and it undercuts both the novelty claim and the mechanism the paper gives for the robustness gains (Sec. V-B credits the attach threshold). As written, readers will infer a safeguard that the deployed system does not have.
**Suggestion**: (a) State plainly that with m=1 the link step is single linkage at tau_l. Present the contribution as a practical, verified adaptation of incremental core-point clustering (two thresholds plus a centroid merge, deployed in a real local-first app) rather than a new algorithm. (b) Reword the anti-chaining sentence so it applies only when m >= 2, or report results at m >= 2 too. (c) Shorten the proposition to a remark, or keep it with an explicit note that it follows from the connected-components definition.
**Severity**: Major
**Confidence**: 4 — core expertise in clustering; follows directly from the definitions in Sec. III-B and the m=1 selection in Sec. IV

### W2: The incremental-speed claim uses a superseded configuration and the timings barely show incremental behaviour
**Problem**: The abstract and conclusion say updates are "faster than re-clustering". Sec. V-E measures this with an early configuration (tau_l=0.40, m=3, tau_g=0.35) that is neither the order-experiment configuration nor the shipped one. The per-batch timings in `exp7_order_stability.json` grow almost linearly with total library size and match the Two-stage re-clustering baseline up to about 9k faces. Ours: 0.29, 0.86, 1.71, 2.78, 3.83, 5.24, 7.69, 8.02, 9.54, 11.25 s. Two-stage: 0.27, 0.86, 1.85, 3.46, 4.58, 5.98, 7.81, 9.84, 11.87, 15.67 s. That conflicts with "near-constant-time unions; full re-clustering is never needed": the cost of bringing the view up to date scales with library size, presumably because of the flat-index range search and the read-time attach/merge.
**Evidence Anchor**: `dataset: evaluation/results/exp7_order_stability.json streaming — "Ours (incremental)" update_s grows 0.29 to 11.25 s, tracking Two-stage 0.27 to 15.67 s`
**Why it matters**: Being incremental is half the paper's selling point ("order invariance can be had without giving up incremental updates"). As it stands, the evidence supports only a modest constant-factor gain at the largest size, measured on a different configuration.
**Suggestion**: Re-run the streaming experiment with the shipped thresholds (MBF and EdgeFace-S). Split the time into range search, union-find, and read-time attach/merge, and report the per-batch cost against batch size and library size. If the read-time step dominates, say so and soften the claim to something like "comparable to or modestly faster than re-clustering, while keeping partitions stable", or make the read step incremental as well.
**Severity**: Major
**Confidence**: 4 — numbers read directly from the released result file

### W3: The practical baseline the cited systems use (DBSCAN/HDBSCAN) is missing
**Problem**: Related Work says Immich and PhotoPrism "cluster faces with density-based methods", and the method is built on incremental DBSCAN. Yet DBSCAN/HDBSCAN on the same embeddings is not among the baselines, and Sec. VI defers it to future work. It is training-free, runs on a CPU, and is cheap to add on libraries of 389 to 1,421 faces.
**Evidence Anchor**: `absence: Sec. IV Methods and Table I — expected DBSCAN/HDBSCAN baseline on identical embeddings; checked Sec. II, Sec. IV, Table I, Table III, Sec. VI`
**Why it matters**: The paper's practical claim is about local-first managers. Without the clustering those managers actually run, readers cannot tell whether the gains over the leader baselines carry over to the systems the paper positions itself against. This is the first question a fit reviewer will ask.
**Suggestion**: Add DBSCAN (cosine, eps = 1 - tau, a small min_samples grid tuned on the seed-1 libraries) and, if feasible, HDBSCAN as columns in Table I, with order spread. Even one table column is enough.
**Severity**: Major
**Confidence**: 4 — venue-level expectation; scikit-learn implementations exist

### W4: Different experiments use three different threshold configurations
**Problem**: The order-sensitivity experiment uses (0.50, m=2, 0.45, no attach), the robustness table uses (0.50, m=1, 0.35, 0.45), the streaming experiment uses (0.40, m=3, 0.35), and EdgeFace-S uses (0.60, 1, 0.50, 0.55). The order-invariance result does not depend on thresholds, but the F1 values quoted beside it (LFW F1 0.989) and the update-time/ARI >= 0.994 results do.
**Evidence Anchor**: `text: Sec. V-E "thresholds of an early tuning round, $\tau_\ell=0.40$, $m=3$, $\tau_g=0.35$"`
**Why it matters**: A reader cannot tell which numbers describe the system as shipped. The paper looks pieced together from rounds of development.
**Suggestion**: Re-run Sec. V-A and V-E with the final configuration, or add a small table listing which configuration each experiment uses and why. The order and streaming scripts already exist, so a rerun is cheap.
**Severity**: Minor
**Confidence**: 5 — stated in the manuscript

### W5: The recogniser study takes up a large share of a clustering paper
**Problem**: The title and contributions 1 to 3 are about clustering, but about a third of the abstract and two of the three tables cover the recogniser swap. EdgeFace's accuracy and speed are already published. What is new here is the threshold re-tuning and the pose/age clustering effect.
**Evidence Anchor**: `text: Abstract "A controlled comparison of four lightweight recognisers on identical face crops then shows that EdgeFace-S is about twice as fast"`
**Why it matters**: It blurs the paper's identity. In a 5 to 6 page IEEE format, the space would serve W1 to W3 better.
**Suggestion**: Keep Table III (clustering with EdgeFace-S), shrink Table II to the key rows or move it to supplementary material, and cut the abstract's recogniser part to one sentence about the clustering effect.
**Severity**: Minor
**Confidence**: 4 — editorial judgement for the venue format

### W6: Some speed and robustness wording goes beyond the tables
**Problem**: (a) "halves the embedding time" (Sec. V-D, Conclusion) holds single-threaded (27.5 vs 13.3 ms), but Table III, which describes the shipped pipeline, uses all-core times of 19.7 vs 11.8 ms, a 1.67x speed-up. (b) "best or tied-best in seven of the ten conditions" counts margins of 0.002 to 0.003 (Clean, Look-alike) with no variability shown. (c) Contribution 1 calls simulated LFW-celebrity libraries "realistic personal libraries", even though Sec. VI says real albums differ.
**Evidence Anchor**: `table: Table III — Embedding time row 19.7 vs 11.8 ms/face (1.67x, not 2x)`
**Why it matters**: These are small individually, but PC members notice inflated wording, and it costs credibility that the honest limitations section earns.
**Suggestion**: Say "about 40% less embedding time with all cores (2x single-threaded)". Report the across-library spread or a paired test for the Table I differences and drop the "best" claims where the gap is below the noise. Replace "realistic" with "simulated".
**Severity**: Minor
**Confidence**: 4 — arithmetic on reported values

### W7: The submission is not ready: placeholder affiliations and a reference to an earlier review
**Problem**: The author blocks contain "[College name]", "[City]" and "[email]", and the declarations say "to be completed". The introduction cites "A reviewer of that version", which means nothing to readers of this paper.
**Evidence Anchor**: `text: author block "\textit{[College name]}\\"`
**Why it matters**: Incomplete front matter can lead to a desk rejection at IEEE conferences, independent of the content.
**Suggestion**: Fill in affiliations and author contributions. Replace the reviewer sentence with a neutral one, e.g. "A known weakness of this rule is ...".
**Severity**: Minor
**Confidence**: 5 — directly visible

### W8: The account of Cove's earlier method is inconsistent
**Problem**: Sec. I says the first version of Cove used First-Leader. Sec. IV calls Two-stage "Cove's previous method", and the results JSON labels it "Two-stage (current Cove)".
**Evidence Anchor**: `text: Sec. IV "leader at 0.45 plus centroid merge at 0.40, Cove's previous method"`
**Why it matters**: Readers cannot tell which baseline the shipped system actually replaces.
**Suggestion**: State the history once: v1 used First-Leader, v2 used Two-stage, and this paper's method is v3.
**Severity**: Minor
**Confidence**: 5 — internal text comparison

---

## Detailed Comments

### Journal Fit
Good fit for an IEEE regional applied-computing conference (systems/applications or image processing track). The work combines a deployed system with an empirical study, which these venues value, and the length appears appropriate for the 6-page IEEEtran conference format. The references are suitable but thin on recent face clustering (2020 to 2024 GCN/transformer clusterers are discussed only through two 2019 papers). One or two recent citations would show awareness of current work, even if those methods are not compared.

### Originality
The source of originality is a new combination applied to a new setting: two-threshold core-point clustering plus a centroid merge, evaluated for order stability in local-first photo libraries. The measurement of order sensitivity (Fig. 1) and the degraded-photo study are useful empirical contributions. The algorithmic novelty is modest and should be presented that way (W1). The paper's own sentence "We are not aware of a published evaluation of order sensitivity ... for such systems" is the honest novelty claim and should lead the paper.

### Significance
Mainly practical, within the sub-field: practitioners building self-hosted photo tools will benefit. Significance would rise noticeably with a DBSCAN/HDBSCAN comparison (W3), because that directly speaks to the systems people actually use.

### Structural Coherence
The arc from problem to method, robustness, failure analysis and recogniser fix is coherent. Coherence weakens where configurations change between experiments (W4) and where the abstract promises an incremental-speed advantage that Sec. V-E shows only weakly (W2).

### Title & Abstract
The title is accurate. The abstract is long and spends a third on the recogniser study (W5). Its claim "keeps B-Cubed F1 between 0.972 and 1.000" correctly leaves out occlusion, which is reported in the next sentence, and that is fine.

### Conclusion
Mostly aligned with the results. "updates faster than re-clustering" and "halves embedding time" need the softening described in W2 and W6. The future-work statement (real consented albums, multi-face photos) is appropriate.

---

## Questions for Authors
1. At m=1, what fraction of faces are non-core in the test libraries, and what do Table I results look like at m=2 or 3, where the anti-chaining safeguard actually operates?
2. In the streaming experiment, how much of each update is range search, union-find, and read-time attach/merge? Does the per-batch time stay flat if batch size is fixed and the library grows?
3. How does scikit-learn DBSCAN/HDBSCAN on the same embeddings compare in F1 and order spread?
4. How many libraries are in the seed-1 tuning set, and how many identities overlap between the tuning and test libraries?

---

## Minor Issues

### Language / Grammar
- Abstract: the sentence beginning "We report its failure modes openly" is very long; split it.
- Sec. III-B proof sketch: the remark about ties not arising "in practice" appears twice; keep one.

### Citation Format
- `jung2025posetta` and `zheng2017calfw` are `@misc` (arXiv); add the arXiv IDs, or cite the venue versions if they exist.
- `immich` and `photoprism` should carry an access date.

### Figures and Tables
- Table I: add a per-condition spread or confidence interval across the 30 libraries.
- Fig. 3: say in the caption that the thresholds differ from the shipped configuration (or re-run, see W2).

### Layout
- Table II uses `tabcolsep` 2.6pt; check it does not overflow the column in the compiled PDF.

---

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | quality_rubrics.md; regional IEEE applied-systems expectations | PARTLY_MEETS | Sec. III-B; Sec. II | Useful new empirical question; the algorithm is close to known threshold-graph/incremental DBSCAN at m=1 | Depends on how the novelty is reframed | yes, reframing required (W1) |
| Methodological Rigor | quality_rubrics.md | NOT_ASSESSED | — | Left to the methodology seat | outside EIC remit | no |
| Evidence Sufficiency | quality_rubrics.md | PARTLY_MEETS | exp7 streaming JSON; Table I | Robustness evidence is strong; the speed claim and the comparison against the cited systems' clustering are weak | Not re-run by me | yes (W2, W3) |
| Argument Coherence | quality_rubrics.md | PARTLY_MEETS | Sec. V-A, V-E configurations | Clear arc, but mixed configurations and a mechanism that does not operate at m=1 | none identified | yes (W1, W4) |
| Writing Quality | quality_rubrics.md | MEETS | whole manuscript | Plain, readable, honest limitations | placeholders remain | no |
| Literature Integration | quality_rubrics.md | PARTLY_MEETS | Sec. II | Relevant but thin on post-2020 face clustering | domain seat to confirm | no |
| Significance & Impact | quality_rubrics.md | MEETS | Sec. I, Sec. VI | Practical value for local-first tools at venue scale | grows with W3 | no |

The recommendation rests on three unresolved but repairable decision-bearing items: novelty and mechanism framing at m=1 (W1), the incremental-speed evidence (W2), and the missing density-based baseline (W3). None is fatal. Each needs either reframing or one additional run with existing scripts.
