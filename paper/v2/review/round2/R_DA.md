# Devil's Advocate Review: round 2

**Manuscript:** `paper/v2/cove_paper.tex`, "Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries" (commit ce1b15d)
**Seat:** Devil's Advocate (fixed). This report was written without reading any other round-2 report; only `00_reviewer_cards.md` was read.
**Run mode:** standard-mode output format. No sprint contract was supplied, so there are no dimension scores.

### Calibration Status
`NOT_CALIBRATED`

### What was checked, and how
- **Code read:** `cove/engines/stable_cluster.py` (`_labels_constrained`) and `evaluation/exp15_corrections.py`, `exp14_disjoint.py`, `exp18`.
- **JSONs read:** exp14, exp15, exp18; prior-art scans; round-1 decision and revision log.
- **Read-only checks.** Every script lives in the scratchpad, and nothing in the repo was modified.
  1. **Post-hoc baseline (`posthoc.py`).** Re-ran the exp15 oracle on all 240 test libraries (EdgeFace-S, about 5 minutes). It reproduces the paper's "lost" F1 (0.9854) and "kept" F1 (0.9925) exactly. On top, it adds two trivial baselines that re-cluster and then re-apply the stored constraints post hoc:
     - **detach:** move the cannot-linked face out of its cluster, then merge the clusters of must-linked faces;
     - **split:** split a cluster that contains a cannot-linked pair by which of the two faces each member is nearer to, then do the must-link merges.

     A merge is skipped when it would join a cannot-linked pair. I wrote these baselines myself in about 20 lines. They have not been vetted, so the numbers are indicative only.
  2. **Contradictory corrections (`contra.py`).** A 9-face synthetic test of whether contradictory corrections are resolved in an order-free way.
  3. **Constrained-path cost (`ctime.py`).** Timed `labels()` with and without a constraint on all 8,290 LFW-clean faces.

**Genuine strengths (brief).**
- The paper is unusually candid: it reports where it is worse than average linkage, the failed pose bonus, and the app gaps.
- Table II matches the JSON.
- The order-invariance proposition holds empirically for non-contradictory corrections.

### Criterion-Bound Judgements
| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| 1. Core thesis | DA challenge dim. 1 | PARTLY_MEETS | text: Sec. V-C "the clusterer keeps every correction (100\% still hold)" | The thesis is true, but its headline evidence does not discriminate (C1) | Post-hoc baselines are my own | yes: headline |
| 2. Cherry-picking | DA dim. 2 | PARTLY_MEETS | dataset: `paper/v2/research/innovation_scan_2026-11-07.md` §4 G4 | The closest prior art flagged by the authors' own scan is omitted (M4) | Scan was abstract-level | yes |
| 3. Confirmation bias | DA dim. 3 | PARTLY_MEETS | text: Sec. IV "each time fixing the largest remaining mistake" | The oracle is designed for the mechanism (M2) | — | yes |
| 4. Logic chain | DA dim. 4 | PARTLY_MEETS | text: Sec. VI "The corrections result is the main difference to re-clustering" | 100% held is a design guarantee, not a finding | — | yes |
| 5. Overgeneralisation | DA dim. 5 | PARTLY_MEETS | text: abstract "With ten simulated corrections per library" | Only 91/240 libraries received 10 corrections (M1) | — | yes |
| 6. Alternative paths | DA dim. 6 | DOES_NOT_MEET | absence: Sec. V-C — expected a constrained or post-hoc re-clustering baseline; checked Table II, exp15 script, exp15 JSONs | Only a constraint-discarding comparator is given | — | yes |
| 7. Stakeholders | DA dim. 7 | PARTLY_MEETS | text: Sec. VI "real users fix fewer mistakes, in another order, and sometimes wrongly" | Acknowledged, but not measured | — | no |
| 8. So what? | DA dim. 8 | PARTLY_MEETS | text: Sec. V-F "The gain over re-running our own method is small (1.3$\times$)" | Order invariance is distinctive only against leader methods (M3) | Venue is an applied regional conference | yes |

### Strongest Counter-Argument
The paper's new headline, "100% of corrections hold vs 27% under plain re-clustering", is a property of the code, not a result.

**Why it is guaranteed by the code.**
- `_labels_constrained` applies must-links first.
- It refuses every union, and every centroid merge, that would join a cannot-linked pair.
- The metric `satisfied()` checks only the two clicked faces.
- So "kept = 100%" cannot fail. The only comparator is a pipeline that deletes the constraints.

**What a fair comparison shows.** Keep the constraints, but use the dumbest possible re-application: re-cluster, then post-hoc merge the clusters of must-linked faces and split clusters on cannot-linked faces.
- Constraints held: 98.5% (pooled over 1,300 corrections).
- F1: 0.9907, against 0.9925 for the paper's clusterer and 0.9854 when the constraints are lost.
- So about 75% of the paper's "kept vs lost" gain comes from simply *storing* the corrections.
- Outside occluded photos, the two differ by at most 0.0009 F1. This is because 81% of the oracle's corrections are must-links, which any merge rule satisfies.

**What remains of the contribution.**
- Order invariance does not separate the method from average linkage, single linkage, DBSCAN, or from re-running the paper's own clusterer from scratch, which takes 4.7 s against 3.5 s for the incremental update.
- On accuracy without corrections, the method is now level with average linkage, or worse on low-res, mixed and CPLFW.

**The parsimonious reading.** "Persist the user's must-link/cannot-link constraints and re-run any deterministic constrained clusterer" gives everything claimed. It is a one-line design decision that Davidson & Ravi (2005), cited by the paper, already make possible.

**What survives.** The constrained maximum-spanning forest does beat post-hoc splitting on cannot-link-heavy occluded libraries (0.969 vs 0.956, better in 26 of 30 libraries). That is narrow, but it is real, and it is the result the paper should lead with.

### Issue List

#### CRITICAL
| # | Dimension | Issue Description | Evidence Anchor | Confidence | Field-Norm Boundary | Evidence-Crossing Rationale |
|---|-----------|-------------------|-----------------|------------|---------------------|-----------------------------|
| C1 | Logic chain / alternative paths | **The headline "100% vs 26–27%" is guaranteed by construction, and its only comparator throws the constraints away, so it cannot show that the proposed clusterer is what keeps corrections.** In code, must-links are unioned first, every cannot-violating union or merge is refused, and `satisfied()` tests only the constrained pair, so the "kept" side cannot be below 100%. My read-only run used the same 240 libraries and the same oracle constraints, and reproduced lost 0.9854 / kept 0.9925. Trivial post-hoc re-application gives: **split** baseline 98.5% held, F1 0.9907; **detach** baseline 98.6% held, F1 0.9883. Per condition, kept minus split is ≤0.0009 F1 in 7 of 8 conditions; it is +0.013 on occluded (0.969 vs 0.956), where 58% of corrections are cannot-links. Contribution bullet 2, the Sec. VI sentence "The corrections result is the main difference to re-clustering", and the abstract all present a design guarantee as an empirical finding. **Repairable:** state 100% as a guarantee, not a result; add a post-hoc and/or constrained-average-linkage baseline to Table II; lead with the occluded/cannot-link result, which is where the mechanism actually matters. | text: Sec. I contributions "with the clusterer keeping them, 100\% hold; with plain re-clustering, 26--27\%" | 5 (code read; result reproduced; baselines are my own and unvetted, so exact values are indicative) | — (rests on logic, not a field norm) | — |

#### MAJOR
| # | Dimension | Issue Description | Evidence Anchor | Confidence | Field-Norm Boundary | Evidence-Crossing Rationale |
|---|-----------|-------------------|-----------------|------------|---------------------|-----------------------------|
| M1 | Overgeneralisation / data–conclusion | **The headline statistics are mis-described.** (a) "27%" is the mean of per-library rates, and the 33/240 libraries with zero corrections score a vacuous 1.0, because `satisfied()` returns 1.0 for an empty list. Pooled over the 1,300 corrections, 20.3% hold; the mean over libraries with at least one correction is 15.7%. The per-condition figures are inflated the same way: look-alike is 51.6% reported vs 25% pooled, and clean is 26.7% vs 6.5%. (b) "Ten corrections per library" in the abstract and Sec. V-C: only 91/240 libraries received 10. The mean is 5.4, and 14/30 look-alike libraries received none. The direction understates the gap, but the abstract's dose is wrong. Report pooled shares and the distribution of corrections, or say "up to ten". | dataset: `evaluation/results/exp15_corrections_edgeface_s.json` per_library.corrections_made, and `exp15_corrections.py` `satisfied()` | 5 (recomputed from JSON) | — | — |
| M2 | Confirmation bias / external validity | **The oracle user is built to suit the mechanism.** It uses ground truth to pick the biggest error. It places a cannot-link between the *central* face of the main person and the intruder face *most similar* to them, which are exactly the faces at which a constrained maximum-spanning forest cuts most effectively. It is never wrong and never contradicts itself, and 81% of its corrections are must-links. The "now" F1 gain is measured on the very faces whose labels the oracle consulted. There is no sensitivity test: no random wrong-face clicks, no wrong corrections, no fewer fixes. Limitation (ii) concedes the issue, but the abstract states 0.984→0.994 with only "simulated". Add one noisy-user variant (for example, a random face of the intruder and 10% wrong corrections). | text: Sec. IV "each time fixing the largest remaining mistake" | 4 | — | — |
| M3 | "So what?" / alternative paths | **Order invariance is distinctive only against leader clustering, the authors' own first version.** Average linkage, single linkage, DBSCAN (0.997) and a from-scratch re-run of the paper's own clusterer are all order-invariant. The incremental update saves 1.2 s (3.5 s vs 4.7 s at 8,290 faces). The user-relevant property is stability *between* imports. It is reported only for the paper's own method (ARI ≥0.998); there is no baseline, for example average linkage re-run per batch. The obvious rival is constrained average linkage re-run per import, which is cited (Davidson & Ravi 2005) but not run. It would be order-invariant, keep corrections by construction, and match or beat the method on low-res, mixed and CPLFW. The authors' possible defence, the O(n²) memory of average linkage on 50k+ face libraries, is never measured beyond 8,290 faces. Either measure scale, or frame the contribution as an engineering trade-off. | text: Sec. V-A "but these batch methods must be re-run on the whole library after each import" | 4 | — | — |
| M4 | Cherry-picking (prior art) | **The closest prior art, flagged by the authors' own novelty scan, is omitted, while the paper claims a gap.** The scan says the paper "must cite and differentiate" these works. None appears in `cove_paper.tex` or `references.bib`. The works and why they matter: <br>• Halkidi 2012: semi-supervised incremental clustering of streams. <br>• He 2019: incremental constrained random walk. <br>• Lasek & Gryz 2019: constrained DBSCAN; DBSCAN core points with constraints is close to this paper's design. <br>• Beauchamp 2025: incremental integration of user feedback, which is the paper's headline. <br>• Monath 2019 (Grinch) and Bandyopadhyay & Murty 2016: order-independent incremental clustering, which bears on the "provably independent" claim. <br>Meanwhile Sec. II states "we did not find an evaluation of whether such corrections survive later re-clustering". | absence: Sec. II Related Work and references.bib — expected Halkidi 2012, Lasek & Gryz 2019, Beauchamp 2025, Monath 2019, Bandyopadhyay & Murty 2016; checked cove_paper.tex, references.bib (grep), innovation_scan_2026-11-07.md §3–4 | 3 (scan is abstract-level; I did not read these papers) | The authors' own pre-declared condition (innovation_scan §4 G4: "must cite and differentiate … before the claim is final"), plus standard practice that a novelty claim is differentiated from the nearest prior work | The paper makes the novelty claim that the scan said was conditional on citing these works, without citing them |

#### MINOR
| # | Dimension | Issue Description | Evidence Anchor | Confidence |
|---|-----------|-------------------|-----------------|------------|
| m1 | Logic (proposition scope) | **Contradictory corrections are resolved by `sorted(self.must)`, i.e. by face ids, which are insertion order.** My 9-face test used must(0,3), must(3,6) and cannot(0,6). Over 12 insertion orders it gave two different partitions: sometimes 0–3 stayed together, sometimes 3–6. The proof sketch dismisses contradictions as not arising "in practice", but limitation (ii) concedes that users are sometimes wrong. The fix is cheap: use an order-free rule, such as dropping the must-link with the lowest similarity. Otherwise qualify "provably independent". | text: proof sketch "neither do contradictory corrections, which are resolved in a fixed order" | 5 (reproduced) |
| m2 | Overgeneralisation | **The abstract mixes recognisers and over-generalises.** "Order agreement as low as 0.52" is the MBF value (0.515); the body and Table I give 0.56 for EdgeFace-S. "Within about one point of the best batch baselines" is not true with MBF on occluded faces: HDBSCAN scores 0.963 vs 0.928 for the method, a gap of 3.5 points. | text: abstract "leader-based methods reach an order agreement as low as 0.52" | 5 |
| m3 | Evidence gap | **The claim that a must-link carries over to "all photos added to them later" is not tested on the new faces themselves.** The "later" F1 pools old and new faces. Report kept vs lost vs post-hoc F1 on the 20% new faces only. | text: Sec. III-C "including all photos added to them later" | 4 |
| m4 | Unexamined metric | **"Held" counts only the two clicked faces, not whether the mistake stays fixed.** A cannot-link can be satisfied while most of the intruder's photos stay merged. F1 is the real measure, and "held" should be presented as secondary. | text: Table II caption "Fixes held" | 4 |
| m5 | Wording | **"Identical partitions in every order and batch split" (Sec. V-A) overstates what exp14 tested.** exp14 runs the method as one batch per order; batch splits are exercised only in exp15 (64-face batches) and exp18. | text: Sec. V-A "Our method gave identical partitions in every order and batch split" | 4 |
| m6 | Framing | **The "lost" comparator is the authors' own unfinished app** ("the behaviour of the current app"), not a deployed third-party system. Comparing a fixed version with one's own known bug flatters the result. | text: Sec. IV "or with plain re-clustering (the behaviour of the current app)" | 3 |

### Ignored Alternative Explanations/Paths
1. **Persist the corrections and re-apply them post hoc** (re-cluster, then merge and split). This gets about 98.5% held and about 75% of the F1 gain with trivial code (C1). The paper's mechanism adds value only where cannot-links dominate.
2. **Constrained average linkage re-run on every import** (Davidson & Ravi 2005). It is order-invariant, keeps corrections and is at least as accurate on low-res, mixed and CPLFW. The paper's only clear edge over it would be scale, which is unmeasured beyond 8,290 faces.
3. **Pinning:** freeze clusters the user has confirmed and attach only the new faces to them. This is a simple product pattern that keeps corrections without constrained clustering.
4. **Re-running the paper's own clusterer from scratch** gives the same order invariance for 1.2 s more. The "incremental" part is not needed for either headline property.

### Missing Stakeholder Perspectives
- Real users who make noisy, partial or contradictory corrections (no user study and no noisy-oracle test).
- Owners of large libraries (50k+ faces), for whom the scale argument against batch baselines would actually matter.
- Families with multi-face photos and ageing children (acknowledged; untested).

### Unexamined Premise
The paper treats "the two faces the user clicked are still apart (or together)" as equivalent to "the mistake the user fixed is still fixed". The "held" metric encodes this premise, and the 100% figure inherits it. Whether a correction *stays effective* is measured only indirectly, through F1, and there the advantage over trivial persistence is small except on occluded photos.

### Observations (Non-Defects)
- **The real mechanism-level result is on occluded photos.** Kept 0.969, post-hoc split 0.956, lost 0.943; the clusterer is better than post-hoc in 26/30 libraries. Face-level constrained re-clustering propagates cannot-links better than cluster-level surgery. This is the defensible, non-tautological evidence for the design.
- **I checked for a hidden cost on the constrained path and withdraw the suspicion.** On 8,290 faces with one constraint, `labels()` took 4.7 s against 7.9 s unconstrained (the machine was under load). I found no hidden latency cost.
- **The Table II numbers match the JSON** (ALL: 0.9842, 0.9939, 0.9854, 0.9925; 27.3%, computed per-library). The order agreement of 1.000 for exp15 is confirmed.
- **The honest accuracy section** ("no longer clearly ahead") and the negative pose result are strengths. They also mean the corrections claim has to carry the paper on its own, which is why C1 matters.
- **Scratch scripts and full output** are under `C:\Users\poppi\AppData\Local\Temp\claude\7744983e0baceb7b\6637e143-3146-4993-9397-536df44865f5\scratchpad\`: `posthoc.py`, `posthoc_full.txt`, `parse.py`, `contra.py` and `ctime.py`.
