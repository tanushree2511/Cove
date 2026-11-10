# Methodology Review Report (Peer Reviewer 1), round 4

**Manuscript:** `paper/v2/cove_paper.tex` (after E1-E5, not compiled). Simulated reviewer; from round 4 I read only the cards file, no other seat's report.
**Checks (scratchpad, read-only, one core):** numbers and intervals recomputed from the JSONs (pair- and library-level bootstrap); leave-one-out binding test and fast-vs-reference check (14 libraries); order and batch-split invariance (30); `c_avg` on 300 tiny instances; scaling exponents. Untracked `exp26_*` files exist; the manuscript does not cite them and I did not audit them.

### Reviewer Identity
Clustering-evaluation researcher: audits numbers against the result files and asks what each experiment can actually show.

### Overall Recommendation
**Minor Revision** (round 3: Minor). No Critical finding. The new experiments are pre-planned and candid and nearly every new number matches its file. What remains is claim sizing and evidence descriptions that are weaker than they sound.

### Confidence Score
4. Core expertise; I re-ran samples (14 to 30 libraries), not the 240-library experiments.

### Calibration Status
`NOT_CALIBRATED`

### Criterion-Bound Judgements
| Dimension | Source | Judgement | Anchor | Rationale | Limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Text-to-file fidelity | Card 1 | MEETS | `dataset: exp19-exp25 JSONs` | About 70 values recomputed; 6 wording or scope mismatches | exp26 not audited | no |
| Exactness evidence | Card 1, 9 | PARTLY_MEETS | `text: Sec. VI-F "with and without twelve corrections each"` | Sound argument; test mostly non-binding | 14-library sample | yes |
| Consequence baselines | Card 2, 3 | PARTLY_MEETS | `text: Sec. IV "replayed in the order received"` | Ours = c-avg = 100% by construction; opponents authored | none | yes |
| Cost comparison | Card 5 | PARTLY_MEETS | `dataset: exp24 rows.8290` | Own cubic NumPy code, mixed conditions | one laptop | yes |

### Summary Assessment
The round-4 additions follow a plan committed before the runs, report their misses (2.3x against a 5x target; constrained average linkage better on new faces; wrong corrections sticky) and replaced one strawman (frozen-undo v1, F1 0.820). The round-3 number fixes are real. The weaknesses are about what the experiments can show. For ours, the two-device and retraction tests repeat the order-invariance test; the opponents are authored. The cost gap rests on the authors' O(n^3) NumPy code. The exactness test with corrections mostly uses corrections that change nothing. Some summary sentences exceed the tables. All are fixable by rewording plus two cheap re-runs.

### Strengths
**S1 Pre-declared plan, honest misses.** Plan with pass criteria committed 10:21 on 2026-11-10; first result file 10:31. `dataset: paper/v2/research/novelty_round4/02_research_report.md lines 101-106; exp22 *_v1_orphan_artifact.json`
**S2 Traceability.** Table I (80 cells and order row), Tables II-III and every E1-E5 value, including all intervals in Sec. VI-C/D, match the JSONs. `dataset: exp14, exp19, exp19b, exp21-exp25 JSONs`
**S3 The fast read step is exact by argument.** An average cannot cross a component of the cos >= tau_g graph; the 1e-4 margin only enlarges components. I found 0 differences after every oracle correction in 14 libraries. `equation: Sec. III "Exact read-time step"`
**S4 Intervals do not depend on the bootstrap unit.** A library-level cluster bootstrap reproduces the E4 intervals. `dataset: exp23 per_library`
**S5 Shared properties admitted.** `text: Sec. VI-D "The property is therefore not unique to our clusterer"`

### Weaknesses

### W1: The cost advantage over constrained average linkage is sized with the authors' own slow code, in mixed conditions
**Problem.** The abstract pairs 261 s (c-avg, zero corrections) with 1.3 s (ours, ten corrections); like for like it is 293.0 vs 1.277 s (229x). The c-avg is a NumPy loop scanning a k x k matrix per merge: time grows with exponent 3.2 to 3.4 (1.29, 11.7, 261 s at 1,658, 3,316, 8,290 faces). Compiled plain average linkage (exp18: 0.52, 2.36, 16.7 s; exponent 2.1) is a lower bound for any average-linkage c-avg. Against it the ratio is 4.5x, 8.6x, 13x (ten corrections) and 53x at 8,290 faces with none. So "but the gap is two orders of magnitude" (VI-C) is contradicted by its own 16.7 s, and the Conclusion repeats "two orders" without the caveat.
**Evidence Anchor**: `dataset: exp24_cavg_timing_edgeface_s.json rows.8290 cavg_decomposed_0_s 260.89, cavg_decomposed_10_s 292.99, ours_10_s 1.277; exp18 agglomerative_s 16.69`
**Severity**: Major
**Confidence**: 5, core expertise: benchmarking
**Fix.** Say "13x to 230x" in matching conditions; time a compiled constrained average linkage (SciPy `linkage` per component, cannot-links as +inf, must-links by contraction) beside ours.

### W2: Two-device and retraction results re-test the proposition against authored opponents
**Problem.** For ours, exp21 gives both devices the same faces and corrections in two random orders, and exp22 compares "set minus one" with "same set, other order". Both repeat the order-invariance test of exp14/exp19, and c-avg scores 100% too. "Identical on all 240" is a regression test, not a head-to-head; the informative numbers are the opponents' failures. (a) frozen+log applies a device's own faces and edits first and the other's second, so the same non-commuting edits run in different orders; a canonical total order would converge. The plan (`02_research_report.md` lines 93, 102) named last-writer-wins on labels and First-Leader; the run uses neither and the paper does not say so. (b) The frozen undo splits by the nearer of the two clicked faces (version 1 scored F1 0.820 and was replaced); a journal that restores labels and replays later arrivals is exact by construction. (c) "a session in which it was never made" overstates: exp22 recomputes the same remaining corrections.
**Evidence Anchor**: `text: Sec. IV "the other device's edits replayed in the order received"`
**Severity**: Major
**Confidence**: 4, core expertise: baseline design
**Fix.** Say set semantics gives (i) and (ii) without an ordering protocol or log; an event log with canonical order also does, at the cost of storing and replaying it. Add that row or one sentence, report the frozen+log held share (96%, 98%), reword (c). Two sentences suffice after the cuts.

### W3: The exactness test with corrections is weaker than "twelve corrections each"
**Problem.** `make_cons` gives a mean of 8.20 corrections per library (6 to 12): 2.20 correct same-person, 4.00 different-people, 2.00 wrong same-person. Leave-one-out on 14 libraries (112 corrections) changed the partition for 28/28 wrong same-person links, 0/28 correct same-person links (already one cluster) and 0/56 cannot-links. Part A therefore tests about two merges per library; cannot-links are exercised only by Part B (8,290 faces). With oracle corrections (14 libraries, after each of up to 10), 68/68 must-links and 5/8 cannot-links bind and fast equals reference throughout, so the claim is probably true.
**Evidence Anchor**: `text: Sec. VI-F "with and without twelve corrections each"`
**Severity**: Major
**Confidence**: 5, recomputed
**Fix.** Re-run Part A with the exp19 users' corrections on all 480 sets; report the binding count; replace "twelve".

### W4: Summary sentences exceed the tables (four items)
**Problem.** (a) Abstract "within 0.002 F1": ours +0.0010 and +0.0004 (all faces), -0.0014 and -0.0017 (new faces) for the precise and casual users; -0.0027 and -0.0057 for the error-prone user. (b) Conclusion "past about one in twenty they cost more than they gain": the file gives +0.0009 (5%) and +0.0010 (10%), CIs include zero; negative only at 20% (-0.0057, [-0.0085, -0.0030]). "No longer distinguishable from zero" is supported. (c) The Conclusion counts "devices that agree, exact retraction" as advantages next to c-avg, which shares both; the upgrade result has no comparator. (d) The abstract has "30 simulated libraries" and "all 240 libraries" (30 x 8 conditions).
**Evidence Anchor**: `text: Conclusion "past about one in twenty they cost more than they gain"`
**Severity**: Minor
**Confidence**: 5, recomputed
**Fix.** Reword; use "library-condition pairs".

### W5: Round-3 must-dos only partly closed
**Problem.** (i) New-face F1 is in the text only against c-avg; Table II has no column. On new faces ours is also below avg+reapply (-0.0015, -0.0017, -0.0057) and frozen (-0.0006); only ours+reapply is lower, and only for the correct users. Define it (B-cubed on new faces alone, blind to new-to-old errors). (ii) The `c_avg` conflict path is unchanged since ef69690: 4 of 300 random tiny instances return a cannot-linked pair in one cluster; exp19, 21, 24, 25 use it; undisclosed (round-3 effect +0.0001 F1). (iii) Look-alike CI [0.0000, +0.0084] is still "not significantly different". (iv) Table II does not explain "--" (frozen: precise user only, untuned).
**Evidence Anchor**: `dataset: exp19_correction_baselines_edgeface_s.json oracle|ours later_new_F1 0.9906 vs oracle|avg+reapply 0.9922, oracle|c-avg 0.9920; exp19b later_new_F1 0.9912`
**Severity**: Minor
**Confidence**: 5, recomputed and reproduced
**Fix.** Add a new-face column; repair or disclose `c_avg`; call look-alike borderline.

### W6: Timing: same quantity, different values, no explanation
**Problem.** Reference merge 3.4 s (exp18) vs 4.9 s (exp20); fast read 0.5 vs 0.3 s; ten-correction read 1.9 vs 1.3 s: up to 60% spread, against the "up to 20%" cited elsewhere. The scripts run at below-normal priority on a shared laptop (`be_nice`), which the Hardware paragraph omits. Ratios survive; the abstract uses the faster run.
**Evidence Anchor**: `dataset: exp20_timing_edgeface_s.json fast_0_s 0.5086, fast_10_s 1.856 vs exp24 ours_0_s 0.3153, ours_10_s 1.277`
**Severity**: Minor
**Confidence**: 4, core expertise: benchmarking
**Fix.** One quiet run at normal priority, median and range of five, one timing table.

### W7: Recogniser-upgrade retention is valid but small and uneven
**Problem.** The interval is valid (library-level [0.381, 0.567] and [0.387, 0.570]) and the gain real (transferred above none in 178 of 210 pairs, below in 10). But +0.0036 is small, and "about half" averages unequal cases: retention 0.34 and 0.39 on occluded (gain +0.0087, +0.0143), 0.91 and 0.94 on clean. "All held" is true by construction; no comparator.
**Evidence Anchor**: `dataset: exp23_recogniser_upgrade.json per_library mbf->edgeface_s F1 none/native/transferred by condition`
**Severity**: Minor
**Confidence**: 4, recomputed
**Fix.** Report per-condition gains; drop "held" as evidence.

### W8: Error-rate sweep: conditional median, noise
**Problem.** Denominators (100, 103) are close, and a paired check on the 86 libraries below target for both agrees (c-avg reaches 0.99 in 49%, ours 27%; 22 vs 3 discordant). But "median 3 against 4" is over successes only. Random streams are not nested across rates (+0.0009 at 5%, +0.0010 at 10%); at p = 0.02 the library-level CI is [+0.0003, +0.0062] (pair-level [+0.0015, +0.0053]); realised wrong-click counts are missing.
**Evidence Anchor**: `dataset: exp25_effort_edgeface_s.json table 0.0|ours reach 0.340 (100 start below), 0.0|c-avg 0.573 (103); 0.02|ours gain_ci95 [0.0015, 0.0054]`
**Severity**: Minor
**Confidence**: 4, recomputed
**Fix.** Common random numbers, library-level intervals, report wrong-click counts.

### W9: Proposition: ties are also float rounding
**Problem.** The same pair's similarity differs by up to 6e-7 between a one-shot FAISS batch and chunked insertion; in one library 9 of 387,640 pairs lie within 1e-4 of 0.65, none within 1e-6. In 30 libraries, one-shot, 64-chunk and shuffled one-by-one insertion gave identical partitions, with and without corrections, so it holds in practice. Duplicate files in real libraries can give exact ties.
**Evidence Anchor**: `text: Sec. III Proposition "up to renaming of clusters and exact similarity ties"`
**Severity**: Minor
**Confidence**: 4, core expertise: numerics
**Fix.** Say "ties and float rounding"; break ties by embedding bytes, as `must_key` does.

### Number audit
| Paper statement | Value in paper | Value in file | OK / MISMATCH |
|---|---|---|---|
| Order agreement; F1 before/after; held (Abs.) | 0.56; 0.984 to 0.994; 100%/20% | 0.562; 0.9842 to 0.9939; 1.000/0.2031 | OK |
| c-avg "within 0.002 F1" (Abs.) | 0.002 | all faces +0.0010/+0.0004/-0.0027; new faces -0.0014/-0.0017/-0.0057 (precise/casual/error-prone) | OK for correct users; MISMATCH for error-prone |
| "261 s instead of 1.3 s" (Abs.) | 261; 1.3 | 260.89 (0 corr); 1.277 (10 corr); like for like 292.99 vs 1.277 | MISMATCH (mixed conditions) |
| "30 libraries"; "all 240 libraries" (Abs.) | 30; 240 | 30 x 8 = 240 pairs | MISMATCH (unit) |
| Devices identical; frozen; min ARI; F1 (VI-D, T.III) | 240; 53/31%; 0.89/0.91; 0.987 vs 0.992 | 240/240; 127 (52.9%), 74 (30.8%); 0.8854/0.9136; 0.9872 vs 0.9919 | OK |
| Retraction (VI-D, T.III) | 104/98; ARI 1; 0.970 to 0.980; frozen 5%/9%, 0.974 vs 0.980, 0.963 vs 0.969; AUC 0.60/0.63 | 104/98; 1.0; 0.9697 to 0.9797; 4.8%/9.2%, 0.9741 vs 0.9799, 0.9626 vs 0.9693; 0.595/0.629 | OK |
| Upgrade and retention (VI-D) | 0.9837 to 0.9873; +0.0036 [+0.0030,+0.0043]; 1,372; 47% [38,57]; 48% [40,57]; +0.0048 [+0.0039,+0.0059] | 0.98366 to 0.98729; 0.00363 [0.00303,0.00429]; 1372; 0.4685 [0.381,0.570]; 0.4795 [0.396,0.569]; 0.00482 [0.00389,0.00594] | OK |
| "all 480 test libraries" (III) | 480 | 240 x 2, 0 differing | OK |
| "twelve corrections each" (VI-F) | 12 | mean 8.20 (6 to 12); about 2 bind | MISMATCH |
| Read times (III, VI-F) | 3.4; 0.5 (4.9 same run), "ten times"; 4.5, 5.1 / 1.9, 2.2, 2.3x; 4.7, 16.7, 0.15, 0.02 | 3.385; 0.509 (4.910, 9.65x); 4.514, 5.084 / 1.856, 2.195, 2.32x; 4.715, 16.686, 0.1455, 0.017 (my run) | OK |
| c-avg 1.1/11/293 s; ours 0.1/0.3/1.3 s (VI-F) | as stated | 1.070/11.20/292.99; 0.115/0.274/1.277 | OK |
| Ours 0.3/1.3 s (VI-C) vs 0.5/1.9 s (VI-F) | both | exp24 0.315/1.277; exp20 0.509/1.856 | OK, unreconciled |
| "the gap is two orders of magnitude" (VI-C, Concl.) | about 100x | 16.686/1.277 = 13x; 292.99/1.277 = 229x | MISMATCH (scope) |
| 207 of 240; 6.3 (5.4) (VI-C) | as stated | 207; 6.28; 5.42 | OK |
| New-face gap vs c-avg; frozen; MBF; agreement (VI-C) | -0.0014 [-0.0026,-0.0002], -0.0017, -0.0057; -0.0003 [-0.001,+0.000]; 0.009; 0.995 | same; -0.0003 [-0.0012,+0.0003]; 0.0091; 0.9946 | OK |
| Sweep gains and CIs; "57% against 34%", medians 3/4 | as stated | identical; 0.573 (of 103) vs 0.340 (of 100) | OK |
| "past one in twenty ... more than they gain" (Concl.) | claim | +0.0009 (5%), +0.0010 (10%), CIs include 0 | MISMATCH |
| Look-alike "not significantly different" (VI-B) | claim | +0.0037, [0.0000, +0.0084] | borderline (open since round 3) |
| Tables I, II, III cells | as printed | exp14; exp19/19b; exp21/22 | OK (0 mismatches) |

### Answers to the editor's two questions
**Is the evidence enough after the cuts to 6 pages?** Yes for order invariance, corrections kept versus lost, accuracy ties (with the new-face caveat) and fragility to wrong corrections. Not as worded for "two orders of magnitude", the consequence experiments as advantages over c-avg, and an "exact" test with corrections. Keep the new-face numbers, one timing table, limitations (iv) and (vii), and one sentence on the plan change. Safe cuts: pose result, recogniser-choice detail, video tracks, Table III to two sentences.
**Single most important extra check:** time a properly implemented (compiled or heap-based) constrained average linkage beside our read step on the same 8,290 faces and ten corrections, in one quiet run at normal priority (median of five). It decides whether the remaining advantage over c-avg is about 10x or about 200x; every cost sentence depends on it.

### Questions for Authors
1. What does the exactness test show when every correction binds (exp19 users, all 480 sets)?
2. How long does a compiled constrained average linkage take on the same data?
3. Would a canonical-order log, or last-writer-wins, converge, and how many corrections would each keep? Why was the planned alternative replaced?
4. Is the `c_avg` conflict-path bug fixed, and do the error-prone rows change?

### Minor Issues
- "Library" means 30, 210, 240 or 480 in different places; say "library-condition pair".
- CALFW 0.947 is bold on one run with no interval.
- "-0.000" in VI-C; "the same exact split" in VI-F: the c-avg split uses the face graph, ours the centroid graph.

### Final verdict
**Recommendation:** Minor Revision. **Confidence:** 4. **Calibration status:** `NOT_CALIBRATED`.

**Plain-language verdict for the author:**
1. Your numbers are honest and almost all match your result files, which is rare and good.
2. The speed claim is the weak point: the program you compared with is slow code you wrote, so say "about 10 to 200 times faster" and test one properly fast version.
3. The two-device and undo tests show your idea works, but not that it beats others, because the others were set up to fail; say so plainly.
4. Fix three sentences: "twelve corrections" (it is 8, and only 2 matter), "one in twenty", "two orders of magnitude".
5. After that, this is a fair, small, honest conference paper.

**Top 3 issues:** (1) W1, the cost claim: own cubic-time code, mixed conditions, "two orders" contradicted by the compiled 16.7 s; (2) W2, device and retraction results re-test the proposition against authored opponents (planned last-writer-wins dropped); (3) W3, "twelve corrections" is 8.2 and only about 2 bind; re-run with binding corrections.
