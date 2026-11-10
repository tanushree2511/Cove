# Methodology Review Report (Peer Reviewer 1), round 3

**Manuscript:** `paper/v2/cove_paper.tex` (commit ef69690), "Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries"
**Mode:** simplified run of the full panel. This seat did not read any other round-3 report. Only `00_reviewer_cards.md` was read.
**Method:** read-only. I recomputed key numbers from the result JSONs. I also ran three small checks from the scratchpad, none of which modified a repo file: (a) c_avg against sklearn and on a conflict case; (b) c-avg with the conflict path repaired, on 51 small test libraries, with the stored results first reproduced exactly; (c) the order check for the error-prone user on 93 small libraries.

### Reviewer Identity
Clustering-evaluation researcher: checks experimental design, baseline fairness, the statistics, and whether each sentence in the paper equals the result file behind it.

### Overall Recommendation
**Minor Revision.** In round 2 this seat said Major Revision. The round-2 methodology defects are fixed in substance. What remains is claim-sizing and reporting accuracy plus one implementation bug with small effect. No Critical finding.

### Confidence Score
4. This is core expertise in clustering evaluation. I did not re-run the full 240-library experiment, and I checked the c-avg and order claims only on small libraries.

### Calibration Status
`NOT_CALIBRATED`

### Criterion-Bound Judgements
| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Baseline fairness (corrections) | Reviewer-card focus: own session per method, constrained-average-linkage fidelity | PARTLY_MEETS | `dataset: exp19_correction_baselines_edgeface_s.json table.ALL later_new_F1`; `text: Sec. V-C "matches constrained average linkage without its batch cost"` | Own-session design is sound and reproduces exp15 exactly. The F1 comparison is reported on all faces only. On the new faces, c-avg is significantly better. c_avg has a small bug in its conflict path. | Bug effect measured on 51 small libraries only. | yes (claim size) |
| User models | Reviewer-card focus: three users, error-prone definition | MEETS | `text: Sec. IV "each correction is, with probability 0.1, a wrong ``same person'' between random faces of the two most similar clusters"` | Definitions match `exp19_correction_baselines.py`. 162 of 1,528 wrong is 10.6%, as intended. | The error exposure differs across methods (see W7). Only "same person" errors are modelled. | no |
| Statistics (bootstrap, pooling) | Reviewer-card focus: independence, pooled rates | PARTLY_MEETS | `text: Sec. VI (iv) "treat the 30 libraries as independent"`; `dataset: exp19 boot() resamples 240 pairs` | Pooled hold rates are correctly pooled over corrections. The bootstrap unit is described wrongly for exp19. Identity-sharing is only disclosed. | My library-level resample gives similar intervals. No identity-level resample was run. | no |
| Text-to-JSON fidelity | Reviewer-card focus: every number matches | MEETS, with 2 small mismatches | See "Number audit" | About 60 numbers were checked. Mismatches: "up to 15%" timing spread; "5.4 on average" wording. | Table I was checked for the EdgeFace-S cells and the MBF values quoted in the text. | no |
| Reproducibility | Protocol | MEETS | `text: Sec. IV "All rules below were fixed before any test number was computed"` | Splits, seeds, grids and per-run JSONs are present. The paper has not been compiled. | Embedding cache is not shipped. | no |

### Summary Assessment
The paper compares four ways to keep user corrections when photos arrive, using three simulated users and two embedding models. Each method gets its own user session on its own "now" clustering. This is a real fix of the round-2 defect (the "kept vs thrown away" strawman). exp19's precise-user numbers reproduce exp15 exactly (later F1 0.9925, lost 0.9854, held 20.3%). The pooled hold rates, counts and CIs I recomputed match the text. The key honest findings are all reported: constrained average linkage and the frozen rule match the proposed method, re-apply is worse only for the casual user, and wrong corrections are sticky.

The remaining weaknesses are about how far the evidence goes. (1) The all-face F1 hides that on the new faces, which are the point of an update, constrained average linkage is significantly better than the proposed method. (2) The c_avg implementation has a bug in its conflict path. This does not change any headline, but it makes the "faithful Davidson and Ravi" baseline unfaithful for the error-prone user. (3) The CIs for exp19 resample 240 library-condition pairs, not 30 libraries, and the text says otherwise. (4) The "within about one point of average linkage" statement does not hold for MBF occluded faces or for CPLFW. None of these is fatal. All are cheap to fix with text or with a re-run of the noisy c-avg sessions.

### Strengths
1. **S1 Own-session design.** `evidence: text: exp19 docstring "each with its own user session on its own "now" clustering"` and `_job()` code. Each method is corrected where it shows mistakes. The precise-user result reproduces exp15 exactly, so the new harness is validated against the old one.
2. **S2 Pooling is right.** `evidence: table: exp19 JSON per_library, recomputed`. Held share is `sum(held)/sum(n)` over corrections. My recomputation gives 1.000, 0.9581, 0.9266, 1.000 (precise); 0.7316 and 0.679 (casual re-apply); 0.2031 and 0.2275 (lost); 1300 corrections, 207 of 240 libraries with at least one, 91 that hit the cap of ten.
3. **S3 Equal tuning is real.** `evidence: dataset: exp14_disjoint_edgeface_s.json split` (identity_overlap 0; 79/79 family, 1,844/1,844 strangers; grids 360 vs 11 to 77, same rule). I note that tuning ARI is 0.9822 for ours against 0.9851 for average linkage and 0.9853 for Two-stage. The proposed method does not win on the tuning data even with the largest grid. The paper does not say so.
4. **S4 Numbers are traceable.** Table I (EdgeFace-S), the CI sentences of Sec. V-B, Table III accuracy and latency (after the re-measure), the update-time sentences and the future-work figures all match their JSONs (see audit).
5. **S5 Candid negative results.** The pose-aware similarity and the sticky wrong corrections are reported against the authors' interest.

### Weaknesses

### W1: On new faces, constrained average linkage is significantly better than the proposed method, and the paper does not show it
**Problem.** Table II and the text compare "later F1" over all faces. `exp19` also stores `later_new_F1`, the F1 of only the faces that arrived. On that metric the order flips for both models and all three users:
- EdgeFace-S, precise: ours 0.9906, c-avg 0.9920, avg+reapply 0.9922. Ours minus c-avg is -0.0014, library-level 95% CI [-0.0024, -0.0004].
- Casual: -0.0017 [-0.0028, -0.0006].
- Error-prone: -0.0057 [-0.0078, -0.0038].
- MBF: -0.0016, -0.0018, -0.0051, all CIs exclude zero.

The all-face figure is dominated by the 80% old faces, where the proposed method keeps its earlier grouping. The text says the method "matches constrained average linkage without its batch cost" (Conclusion) and "ours is +0.001 F1" (Sec. V-C). For the update the user waits for, the new faces, that is not so. The revision log says the new-face F1 is reported, but the paper does not use it. The same pattern holds against average linkage plus re-apply.
**Evidence Anchor**: `dataset: evaluation/results/exp19_correction_baselines_edgeface_s.json table.ALL, keys oracle|ours, oracle|c-avg, field later_new_F1 (0.9906 vs 0.9920)`
**Why it matters.** It is selective reporting by metric choice. It also makes the cost argument (5.1 s against 16.7 s) the only remaining reason to prefer the method over constrained average linkage.
**Suggestion.** Add a "new faces" column to Table II, or one sentence with the numbers. Say that on new faces constrained average linkage and the re-apply baselines are better by 0.001 to 0.006, and that the proposed method's edge on all faces comes from the old faces. Re-size the Conclusion sentence to "similar overall accuracy".
**Severity**: Major
**Confidence**: 5, core expertise: clustering evaluation (recomputed from the JSON and with a library-level bootstrap)

### W2: c_avg drops a rejected must-link wrongly, which breaks the constraints of the "faithful" baseline for the error-prone user
**Problem.** In `c_avg`, a must-link union is undone with `par[ra] = ra` after `find()` has already compressed the paths of nodes of `ra`'s tree to `rb`. The compressed nodes stay attached to `rb`. A rejected must-link therefore silently merges part of one group into another and can violate the cannot-link it was meant to protect.
- A 5-constraint test (must 0-1, 1-2, 4-3, cannot 3-0, must 3-2) returns labels `[0 0 1 0 1 ...]`: faces 0 and 3, which are cannot-linked, share a label, and face 2 is split from its must-linked group.
- With the repair (copy of `par` before the union, restore on conflict), 51 small test libraries, error-prone user: held share 97.75% rises to 98.88%. Mean later F1 changes by +0.0001, and 1 of 51 libraries changes. The stored results were reproduced exactly with the original code before this comparison.
- The path runs only when a must-link conflicts with a cannot-link. That needs a wrong correction, so the precise and casual rows are unaffected. Only error-prone c-avg is affected (held 98.95% in the JSON, against 99.87% for ours).
- Otherwise the implementation is a faithful constrained average linkage: unconstrained it equals sklearn average linkage (ARI 1.0 on a 180-point test); must-link groups are formed first; cannot-linked merges are never allowed; merge scores are exact UPGMA (sum of pairwise cosines over size product). It is not a defect that a conflicting must-link is dropped; "cannot wins" is the same rule as in ours.
**Evidence Anchor**: `text: evaluation/exp19_correction_baselines.py c_avg() lines 99-104 "if any(find(x) == find(y) for x, y in cannot): par[ra] = ra"`
**Why it matters.** The hold rate and the F1 of "constrained average linkage" in the error-prone column are slightly wrong. The effect on F1 is negligible, but the baseline is cited as Davidson and Ravi.
**Suggestion.** Restore `par` from a copy (or test the conflict before the union), re-run the error-prone c-avg sessions for both models, and refresh the 0.988 and the held share. Add a unit test with a conflicting must-link.
**Severity**: Minor
**Confidence**: 5, core expertise: reproduced

### W3: The bootstrap unit in exp19 is the library-condition pair, but the text and limitation (iv) say libraries
**Problem.** Sec. IV says "paired bootstrap over libraries". This is true for exp14 (30 libraries per condition). For exp19, `boot()` resamples the 240 library-condition pairs as if independent. These are 30 libraries times 8 degradation conditions, so each library appears 8 times. Limitation (iv) says the CIs "treat the 30 libraries as independent", which describes exp14 and not Table II or the Sec. V-C CIs. Identity-sharing (79 family people, about 11 libraries each) is disclosed but not analysed.
- My check: resampling the 30 libraries (average the 8 conditions per library first) gives intervals of similar width. For EdgeFace-S, ours minus re-apply (casual) is [+0.0015, +0.0027], against the paper's [+0.0012, +0.0030]. Ours minus c-avg (precise) is [+0.0002, +0.0018], against [-0.0001, +0.0021].
- Two verdicts sit at the edge in either method: ours minus c-avg (casual) always includes zero; for MBF, the error-prone contrasts with re-apply and c-avg include zero or touch it ([-0.005, 0.000] for avg+reapply).
- So the pseudo-replication across conditions is not what makes the CIs too narrow. The shared identities are, and they are not handled.
**Evidence Anchor**: `text: evaluation/exp19_correction_baselines.py boot() "r.randint(0, len(d), (n, len(d)))" over rows = 240 pairs`
**Why it matters.** A reader will assume 30 independent units. It is a description error, not a conclusion-changing error.
**Suggestion.** State the unit for each table. Prefer the library-level bootstrap (cheap, shown above). If possible, add an identity-level cluster bootstrap over the 79 family people, as round-2 R1 asked. Otherwise keep limitation (iv) and correct its wording to cover Sec. V-C.
**Severity**: Minor (it was Major in round 2; my check reduces the impact, but identity-level dependence is still open)
**Confidence**: 4, core expertise: resampling, recomputed from the per-library data

### W4: "Within about one point of average linkage" is not true for all degraded conditions
**Problem.** The abstract says accuracy without corrections is "within about one point of average linkage", and the Conclusion says "within about one point of the best batch baselines on degraded photos". With EdgeFace-S the worst library condition is -0.009 (occluded), which fits. MBF occluded is -0.026 (0.928 vs 0.954; CI [-0.041, -0.014]), HDBSCAN is 0.963, and CPLFW is -0.068. The body states all three, but the two summary sentences do not. The Conclusion does mention profile faces separately, which covers CPLFW, but not MBF occluded, which is a degraded-photo condition.
**Evidence Anchor**: `text: Abstract "its accuracy without corrections is within about one point of average linkage"; dataset: exp14_disjoint_mbf.json bootstrap_ours_minus.occlude["Agglomerative (avg)"] diff -0.0261`
**Why it matters.** Summary sentences are what readers keep.
**Suggestion.** Write "within one point on EdgeFace-S library conditions (up to 2.6 points on MBF occluded)". Add the tuning-ARI sentence (S3).
**Severity**: Minor
**Confidence**: 5, core expertise: checked against the JSON

### W5: The "Immich-style" frozen baseline is untuned and partial
**Problem.** The threshold 0.5 sits between the EdgeFace-S attach (0.50) and link (0.65) values, so it is a fair setting there. For MBF, the tuned values are attach 0.35 and link 0.50, so 0.5 is as strict as the link threshold. New faces then often start new people: new-face F1 is 0.9536 against 0.9897 for ours, which is the real size of the MBF gap (the paper's 0.009 on all faces understates it). The paper does say the threshold is Immich's default and is "untuned", so this is disclosed. In addition:
- The frozen rule was run only for the precise user, on ours' "now" clustering (exp19b `_job`). Table II shows "--" for the casual and error-prone user without explaining why in the caption.
- The rule is simpler than Immich (no minimum-neighbour rule for creating a person).
- "Nothing in this experiment is tuned" (Sec. IV) is not true for this baseline in the sense the paper uses elsewhere, where "tuned on equal terms" is the standard.
**Evidence Anchor**: `dataset: exp19b_frozen_mbf.json table.ALL later_new_F1 0.9536 vs exp19_correction_baselines_mbf.json oracle|ours later_new_F1 0.9897`
**Why it matters.** Frozen is the strongest rival (best precise-user F1, 0.9928) and the round-1 "open item". If the threshold were tuned, frozen would probably match or beat ours on MBF too, which the paper's wording does not concede.
**Suggestion.** Add the threshold to the equal-tuning protocol (same 0.20-0.70 grid, same tuning libraries), or report a sweep of 0.35-0.65 for both models. Run frozen for the casual and error-prone users (cheap). Explain the "--" cells in the caption, and say "Immich-style" means nearest-face assignment only.
**Severity**: Minor
**Confidence**: 4, core expertise: baseline design

### W6: The re-apply baseline is a single pass, and its advantage concentrates in one condition
**Problem.** `reapply()` splits cannot-linked pairs once, then tries must-links once; it does not repeat until all corrections hold. The hold rate of 96% (precise) and 73% (casual) is therefore partly a property of this heuristic. A reader cannot tell how much of "re-apply loses" would remain with a fixed-point version. Also, for the casual user, ours minus re-apply is +0.0156 on occluded and between -0.0008 and +0.0021 on the other seven conditions. The overall +0.002 is therefore one condition (0.0156/8 = 0.0020).
**Evidence Anchor**: `dataset: exp19 JSON table.occlude["casual|ours+reapply"].ours_minus_this_later_F1.diff 0.0156 vs table.lowres 0.0010, table.mixed 0.0021, others <= 0`
**Why it matters.** The abstract's "only 73% for a user who clicks arbitrary faces" is the paper's strongest argument for building corrections into the clusterer.
**Suggestion.** Add a stronger re-apply (iterate to a fixed point, with must-link groups merged first), or state that the result is for a one-pass re-apply. Add the per-condition spread to the sentence "by 1.6 points on occluded photos" (the text already says this, so one more clause suffices).
**Severity**: Minor
**Confidence**: 4, core expertise: baseline design

### W7: The error-prone user's exposure differs across methods, and the "sticky" explanation and the undo advice are not tested
**Problem.**
- Each method's session has its own random stream, which diverges as soon as the clusterings differ. The number of wrong corrections therefore differs: 162 (ours), 158, 175, 177 (c-avg). Comparing F1 across methods then mixes the method effect with the amount of error it received.
- The explanation "the user's later attempt to separate them competes with it" is not supported by any measurement. For ours, 1,526 of 1,528 corrections hold (99.87%), so at most 2 corrections were overridden. The mechanism may be simply that a wrong merge joins two people and nothing removes it.
- "Corrections must be visible and undoable" is a design inference. No experiment simulates an undo, so the paper cannot say how much of the gain undo recovers.
- The proposition now covers contradictory corrections, but exp19 checks order invariance only for the precise user. My check covers this: error-prone user, ours, 93 small libraries, 3 random orders, worst ARI 1.0000. The claim is therefore supported, but the paper does not test it.
**Evidence Anchor**: `text: Sec. V-C "A wrong ``same person'' joins two people for good, and the user's later attempt to separate them competes with it."; dataset: exp19 JSON noisy|* wrong_corrections 162, 158, 175, 177`
**Suggestion.** Use a common error schedule (draw the error events from a stream independent of the clusterings, or fix which corrections are wrong). Add the order check for the error-prone user (the code already supports it). Weaken "competes with it" to "stays unless removed", or measure it. Add a simple undo simulation (remove each wrong correction with probability p after k corrections), or state that undo is untested.
**Severity**: Minor
**Confidence**: 4, core expertise: simulation design

### W8: Cost claims compare different things, and the cost of constrained average linkage is not measured
**Problem.** Sec. V-C says "average linkage alone took 16.7 s ... against 5.1 s for our clusterer with corrections". The 16.7 s is sklearn average linkage on 8,290 faces (exp18). The 5.1 s is one `labels()` call with 10 corrections (exp18b), which excludes the 0.15 s add. The constrained average linkage that the paper compares in accuracy is the custom dense implementation in exp19, which has never been timed. The claim that it "must re-run on the whole library" is correct by construction, but the cost ratio is for a different algorithm. The 0-correction read time is 3.80 s in exp18b and 3.38 s in exp18 (same data, 12% apart), so the "3.8 s, 4.3 s with one" increment is within run-to-run noise.
**Evidence Anchor**: `dataset: exp18_update_time_edgeface_s.json rows[-1].agglomerative_s 16.69, inc_labels_s 3.38; exp18b labels_seconds_by_corrections {"0": 3.80, "1": 4.26, "10": 5.14, "50": 5.05}`
**Suggestion.** Time `c_avg` on the same 8,290 faces with the same constraints, or write that the comparison is with unconstrained sklearn average linkage. Say the timings have about 10% noise.
**Severity**: Minor
**Confidence**: 4, core expertise: benchmarking

### W9: Whole-set results are single runs with transferred thresholds
**Problem.** CALFW and CPLFW (8,212 and 7,718 faces) use thresholds tuned on libraries of up to 1,348 faces. Several baselines fail in ways that look like threshold transfer, not method weakness: HDBSCAN on CALFW has precision 0.23 and ARI 0.0001; DBSCAN on CPLFW has recall 0.35. The "best on CALFW" result (0.947 vs 0.945 for single linkage) is a single run with no CI, yet it is set in bold in Table I.
**Evidence Anchor**: `dataset: exp14_disjoint_edgeface_s.json whole_sets_test_identities.calfw HDBSCAN B3_F1 0.358, ARI 0.0001; Ours 0.9475 vs Single linkage 0.9452`
**Suggestion.** Remove the bold for 0.947 or say the difference is not tested. Note that HDBSCAN's CALFW value reflects a threshold mismatch at a different scale, or tune it once on a whole-set-sized tuning set.
**Severity**: Minor
**Confidence**: 3, adjacent: depends on how the HDBSCAN parameters scale

### W10: Wording that does not match the data
**Problem.** (a) Sec. V-C: "207 of the 240 library-condition pairs needed at least one correction, and 5.4 were made on average". 5.4 is the mean over all 240 pairs (1,300/240). Among the 207 it is 6.3, and 91 pairs hit the cap of ten. A reader will read 5.4 as the mean among the 207. (b) Sec. V-B: "The mean of two runs, which differed by up to 15%" is wrong: EdgeFace-S all-core latency differed by 20.2% (7.10 vs 8.54 ms), EdgeFace-XS 17.0%, MBF 14.2%. (c) "Look-alike: not significantly different": the CI is [0.0000, +0.0084], on the edge. (d) Table II's caption does not say that the frozen rule exists only for the precise user.
**Evidence Anchor**: `dataset: exp13_speed_all4.json edgeface_s allcores_batch32 [7.104, 8.541]; exp19 JSON oracle|ours corrections 1300, libs_with_corrections 207`
**Suggestion.** Fix the four phrases.
**Severity**: Minor
**Confidence**: 5, core expertise: recomputed

### Round-2 fixes: verified or not
| Round-2 issue | Claimed | Verdict |
|---|---|---|
| C1 no fair baseline | exp19: four methods, own sessions | Real. Two reservations: W1 (new-face F1 omitted) and W6 (one-pass re-apply). |
| Hold-rate and counts | pooled 20%, "up to ten (5.4)", 207/240 | Real. Numbers recomputed: 0.2031 (MBF 0.1687); 1300/240 = 5.42; 207. Wording issue in W10(a). |
| Perfect user | casual, error-prone added | Real. W7 for design limits. |
| Missing prior art | six works added | Outside my remit; not checked. |
| Constrained path not timed | exp18b | Real. Values match (3.80, 4.26, 5.14, 5.05). Comparison caveat in W8. |
| Table III latency | re-measured | Real: all 8 latency cells and 4 parameter cells match `exp13_speed_all4.json` (means of two runs). "Up to 15%" is wrong (W10b). The 2.0x ratio is 1.97 (1 thread) and 1.96 (all cores). |
| "0.52" vs "0.56" | abstract says 0.56 | Real: First-Leader min order agreement 0.562 (EdgeFace-S); 0.515 for MBF. |
| MBF occluded stated | -0.026 | Real, in Sec. V-B. Not in the abstract or Conclusion (W4). |
| Bootstrap independence | limitation (iv) | Partly. The unit is described wrongly for exp19 (W3). No identity-level bootstrap. |
| Order-free contradiction rule | must-links by decreasing similarity | Real in `stable_cluster.py` (`must_key`, content tie-break). My check on the error-prone user: worst ARI 1.0000. Not tested in the paper (W7). |
| Frozen baseline | exp19b, threshold 0.5 | Real but untuned (W5). |

### Number audit (text against JSON)
Matched exactly, to the stated rounding:
- Table I (all 10 conditions, 8 methods, EdgeFace-S) and the order row (0.562, 0.758, 1.000, 0.997, 0.983).
- First-Leader F1 spread 5.9 points (0.0587).
- Sec. V-B CIs: occluded -0.009 [-0.020, +0.001]; low-res -0.006 [-0.008, -0.004]; mixed -0.003 [-0.004, -0.001]; clean, blur, dark +0.002 to +0.006; "0.4 to 14 points" against single linkage and DBSCAN; no-attach costs up to 3.6 points.
- MBF occluded 0.928 vs 0.954 (-0.026, [-0.041, -0.014]), HDBSCAN 0.963; CPLFW 0.841 vs 0.909 and MBF 0.787 vs 0.916; CPLFW precision 0.985, recall 0.733 vs 0.906 (0.9120 and 0.9063 for average linkage; the text says "precision 0.985 vs. 0.912", correct).
- Tuning rule: 0.9822 vs 0.9826.
- Sec. V-C: 0.984 to 0.994; gain +0.010 [+0.008, +0.011]; 0.946 to 0.977 and 0.975 to 0.989; 20% (17%); 0.985; c-avg +0.001 [-0.000, +0.002] (MBF [+0.001, +0.002]); frozen -0.0003 [-0.001, +0.000] and +0.009 for MBF; agreement 0.995; 96%, 73%, 68%; +0.001 and +0.002 [+0.001, +0.003]; MBF 0.004; 1.6 points on occluded; 162 of 1,528; 0.985, 0.988, 0.989, -0.004 [-0.006, -0.002].
- All Table II cells (EdgeFace-S), including the bold cells.
- Sec. V-F: 3.5, 4.7, 16.7, 0.15, 3.4, 1.3x, ARI >= 0.998, 3.8/4.3/5.1.
- Table III: all accuracy cells, asterisks (GhostFaceNet CALFW CI is [0.0000, +0.0045], correctly unmarked), latency, parameters.
- Future-work numbers: 171 people, 0.585 to 0.784, 0.719, 0.854 to 0.860.
- CPLFW pose: 0.985 to 0.786, 0.841 to 0.800, MBF 0.787 to 0.796, MBF occluded -2.7 points.

Mismatched or ambiguous: W10(a) "5.4 on average"; W10(b) "up to 15%"; W10(c) borderline look-alike CI. I did not check the MBF counterparts of every Table I cell.

### Detailed Comments

#### Research Questions & Hypotheses
The question "do corrections survive an import, and at what cost to accuracy?" is clear and answerable with the design. The claim has been re-sized correctly from "27% vs 100%" to the fair comparison.

#### Research Design
The simulation uses disjoint identities and an equal-tuning protocol. The own-session principle is the right design. The three users are described precisely, and the code matches the text.

#### Sampling Strategy
30 test libraries by 8 conditions. Look-alike libraries use a different construction under the same seeds. The users are models, as limitation (ii) says.

#### Data Collection
Not applicable, apart from the embedding cache. The identity split and seeds are fixed.

#### Analysis Methods
Pooled hold rates are valid. The paired bootstrap is valid in form, with the unit caveats in W3. F1 on all faces vs new faces: W1.

#### Results Presentation
Complete and candid, with the omissions in W1, W5 and W7.

#### Reproducibility
The code, grids, seeds and per-library results are present. I reproduced the stored c-avg numbers exactly from the code, which confirms determinism.

#### Methodological Fallacies Detected
- Metric choice that hides a reversal (W1).
- Pseudo-replication of a mild kind (W3).
- Weak-baseline risk (W5 frozen untuned, W6 one-pass re-apply).
- No ecological or survivorship problem found.

### Questions for Authors
1. Why is the new-face F1 left out of Table II, given that exp19 stores it?
2. What are the held share and the F1 of constrained average linkage in the error-prone sessions after the conflict-path fix?
3. Does frozen with a tuned threshold, and with casual and error-prone users, still match the proposed method?
4. What is the runtime of your constrained average linkage on the same 8,290 faces and constraints?
5. If the wrong corrections are removed after the next import (a simple undo), how much of the 0.985 to 0.992 gap is recovered?

### Minor Issues
- Table II caption should say what "--" means.
- Sec. IV says the hold rate is pooled "over all corrections"; also say it counts wrong corrections as held if they are satisfied.
- `_labels_constrained` skips the centroid merge when there are more than 20,000 clusters (`len(ids) > 20000`); the paper does not mention this limit.
- Exact-tie caveat in the proof: duplicate photos give exactly equal embeddings, which are not rare in real libraries. "We did not observe them" is for the simulated data only.
- The order-agreement figure is a minimum over libraries. A mean or a count of libraries with ARI below 1 would be more informative for the leader-based methods.
