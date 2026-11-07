# Peer Review Report: Domain Review (Peer Reviewer 2), Round 2

## Manuscript Information
- **Title**: Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries
- **Manuscript ID**: `paper/v2/cove_paper.tex` (commit ce1b15d)
- **Review Date**: 2026-11-07
- **Review Round**: Round 2 (simplified full-mode run; no sprint-contract, provenance or attachment scripts run)

---

## Reviewer Information

### Reviewer Role
Peer Reviewer 2 (Domain)

### Reviewer Identity
I work on face recognition and constrained clustering: COP-KMeans, constrained agglomerative clustering (Davidson & Ravi), incremental constrained clustering, interactive photo-album systems such as EasyAlbum, and face-clustering methods (rank-order, GCN clusterers, FaceCluster).

### Review Focus
Is the must-link/cannot-link method distinct from prior work, and is the paper honest about it? Are the baselines adequate for the new headline (corrections that persist)? In particular, is the "100% vs 27%" comparison fair? I also check related-work coverage, the correctness of the references, the fairness of the recogniser comparison, and the licence statements.

I committed this report blind to the other round-2 seats. I read only `00_reviewer_cards.md` in `round2/`, and I read the round-1 materials (`EDITORIAL_DECISION.md`, `REVISION_LOG_round2.md`, and my own round-1 `R2_domain.md`) for continuity.

---

## Overall Assessment

### Recommendation
- [x] **Major Revision**

### Confidence Score
4. Constrained and face clustering are my core expertise. The checks on product behaviour (Immich) and on licences rely on public documentation that I fetched during this review.

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

Seat reports always emit `NOT_CALIBRATED`. The final panel topology is not knowable until every seat has completed, and a candidate profile never upgrades the seat report.

### Summary Assessment
The paper presents Cove's face clusterer. It is single linkage at a strict threshold, plus attachment at a looser threshold, plus an average-linkage centroid merge. User corrections are stored as must-link and cannot-link constraints and re-applied on every read. The paper proves that the output does not depend on insertion order. On identity-disjoint simulated LFW libraries, ten simulated corrections raise B-Cubed F1 from 0.984 to 0.994. After new photos arrive, 100% of the corrections hold, against 27% under plain re-clustering.

From a domain point of view the revision is much more honest than round 1. It says outright that constrained clustering and interactive face annotation are prior work, and it presents the method as "an adaptation of known parts".

The new headline does not yet stand up to the constrained-clustering literature, for three reasons:
1. **The 100% is true by construction.** Any hard-constraint method, or simply re-applying the constraints after re-clustering, also gives 100%.
2. **The only comparison is a strawman.** The baseline (the authors' own app forgetting the corrections) does not represent deployed practice. Immich's documented incremental mode keeps the people it has already found.
3. **The closest prior work is missing.** This includes constrained DBSCAN (C-DBSCAN, Lasek & Gryz), constrained stream clustering, and pairwise-constrained face clustering (ConPaC), even though the authors' own novelty scan says these must be cited.

Two smaller problems:
- The "27%" counts libraries in which no correction was made as 100% kept. Among the libraries that did receive corrections, the true figure is about 16–20%.
- The licence statement for EdgeFace omits its ShareAlike term.

All of these can be repaired with new baselines, a reframing of the contribution, and citation work. None needs new data.

---

## Strengths

### S1: The novelty claim is now sized correctly and the prior parts are named
The introduction and method section disclaim the components and state what the shipped setting reduces to. This answers my round-1 W1 and the panel's issue 3 directly.
**Evidence Anchor**: `text: Sec. III-B "At the tuned setting m=1 ... the core step is single linkage at τℓ" and Sec. I "we do not claim these parts as new"`

### S2: The constraint integration is technically sound and verified against the code
- In `_labels_constrained`, must-links are applied first.
- Core edges are then unioned in decreasing similarity. A union is refused if a cannot-linked pair would end up in one component, and the merge step blocks cluster pairs that contain a cannot-link.
- So a cannot-link wins over a conflicting must-link, as the paper says.
- Constraints are also respected during attachment (`try_union`), which a naive post-processing step would miss.
- Order agreement with three random orders of faces *and* constraints is 1.000 in all 240 library runs (`exp15_corrections_edgeface_s.json`, `order_agreement_min`).

**Evidence Anchor**: `text: Sec. III-C "a union is skipped if it would put a cannot-linked pair into one cluster, which builds a constrained maximum-spanning forest"`

### S3: The baseline set for accuracy without corrections is now credible and reported unflatteringly
- DBSCAN, HDBSCAN and single linkage were added, all tuned with the same grid and rule, and the attach ablation is reported.
- The paper says where it loses: low-res, mixed, and CPLFW (−6.8 points against average linkage). It also explains the loss correctly by the clustering rule (weak but numerous links), not by the embedding. This fixes the round-1 critical issue C1.

**Evidence Anchor**: `table: Table I — CPLFW row, Ours 0.841 vs Avg. linkage 0.909; text: Sec. V-B "The gap therefore lies in the clustering rule as well as in the embedding"`

### S4: The recogniser comparison is controlled and its non-standard protocol is disclosed
- All models are run on identical crops and identical pairs, with paired bootstrap CIs.
- The recogniser was chosen by a rule declared before testing and applied on tuning data (ARI 0.9822 vs 0.9826).
- The random-pair caveat is stated, and the unsupported round-1 sentence about the literature was deleted.

**Evidence Anchor**: `text: Sec. V-E "these pairs are drawn at random from the images, not the official hard-negative pair lists, so the numbers are not comparable with published results"`

### S5: Correction survival is a useful evaluation idea for interactive face grouping
I know of no face-annotation paper (Tian 2007, EasyAlbum 2007, FaceCluster 2025) that measures whether user edits survive later re-clustering, and the authors' scans also found none. As an *evaluation protocol* (distinct from the algorithm), this is a modest but real contribution to interactive photo-album research.
**Evidence Anchor**: `text: Sec. II "we did not find an evaluation of whether such corrections survive later re-clustering"`

---

## Weaknesses

### W1: The "lost corrections" problem and its only baseline do not represent deployed practice; Immich-style incremental assignment keeps existing people
**Problem**: The abstract claims that photo managers "must re-cluster whenever new photos arrive", and that this "silently undoes" the user's fixes. The only comparison in Sec. V-C is "plain re-clustering (the behaviour of the current app)", meaning Cove's own app.

Immich, which the paper cites as the leading local-first manager, documents something different:
- Its incremental mode "preserves the clusters (people) generated from the previous round".
- It gives a new face "the person of the most similar face".
- Only a full re-run "does behave like DBSCAN".
- Its documentation also tells users to "manually assign a selection of unassigned faces and queue Missing" so that later runs use those assignments. (Source: docs.immich.app/features/facial-recognition, fetched 2026-11-07.)

So the deployed alternative is not forgetting. It is frozen assignment, which keeps old corrections but is order-dependent. The authors' own scan (`innovation_scan_2026-11-07.md` §3) records this, together with Immich's advice to reset and re-cluster.

**Evidence Anchor**: `text: Abstract "Photo managers ... must re-cluster whenever new photos arrive" and Sec. IV "or with plain re-clustering (the behaviour of the current app)"`

**Why it matters**: The paper's real distinguishing point is getting *both* order invariance and persistent corrections. Batch re-clustering gives invariance without persistence. Immich-style frozen assignment gives persistence without invariance. The paper measures neither competitor against the combination, so the 27% comparison mostly measures a defect of the authors' own app.

**Suggestion**:
- Re-frame the two problems as a trade-off between the two deployed strategies.
- Re-implement Immich's documented rule as a baseline (DBSCAN-like core test with min faces = 3; assign a new face to the person of its most similar already-assigned face; never reassign assigned faces) on the same embeddings.
- Report it in both the order-agreement row of Table I and in Table II (later F1, corrections held, and the F1 of new faces of corrected people).
- Soften the abstract to "re-clustering from scratch, as in Cove's current app, undoes ...".

**Severity**: Major
**Confidence**: 4 (core expertise; Immich behaviour taken from its documentation, not from running its code)

### W2: "100% of corrections hold" is true by construction; constraint-aware baselines are missing, so Table II cannot show a method advantage
**Problem**: The `satisfied()` metric in `exp15_corrections.py` checks whether each stored constraint holds in the final partition. For any clusterer that enforces hard constraints, this is 100% whenever the constraints are feasible. That holds for COP-style methods (Wagstaff et al. 2001), for constrained agglomerative clustering (Davidson & Ravi 2005), and for C-DBSCAN (Ruiz et al. 2007). Without a fixed k, ML/CL feasibility only fails on contradictory constraints.

Even the crudest fair baseline gets 100%: re-cluster with average linkage, then merge must-linked clusters and move cannot-linked faces out. So "100% vs 27%" compares a method that remembers the constraints with one that throws them away. It does not compare constraint-handling strategies.

The informative quantities are different:
- **Later F1.** Does a correction *generalise* to the new photos and to the uncorrected faces of the same person?
- **Order agreement** under each strategy.

Table II reports later F1 only for "kept" vs "lost".

**Evidence Anchor**: `table: Table II — "Fixes held" column 27% / 100%; no row for any constrained or re-applied baseline`

**Why it matters**: Average linkage is the strongest unconstrained method in Table I. It beats ours on low-res, mixed, occluded and CPLFW. A constrained average linkage might therefore match or beat ours on later F1 (ours: 0.992), which would remove the method claim behind the headline.

Field norm: constrained-clustering papers evaluate the *accuracy gain from constraints* on points the constraints do not directly cover, plotted against the number of constraints. They do not report constraint satisfaction, which is guaranteed. See Wagstaff et al. ICML 2001 (accuracy vs. number of constraints on held-out instances) and Davidson & Ravi PKDD 2005 (both already cited).

**Suggestion**: Add three baselines to Table II, all given the same simulated corrections:
- (a) re-cluster, then re-apply the constraints post hoc, on average linkage and on ours;
- (b) constrained average-linkage agglomerative clustering (Davidson & Ravi 2005: refuse merges that join a cannot-linked pair; must-link components pre-merged);
- (c) the Immich-style frozen-assignment rule from W1.

Then:
- report later F1, F1 restricted to the *new* faces, and order agreement for each;
- keep "held" only as a sanity column, labelled "by construction for (a)–(c) and ours";
- optionally add Chinese Whispers (dlib's face-clustering default) to Table I, as asked in round 1 and still absent according to `REVISION_LOG_round2.md` item 6.

**Severity**: Major
**Confidence**: 5 (core expertise: constrained clustering)

### W3: The closest prior art for constrained, density-based and incremental face clustering is not cited, although the authors' own scan says it must be
**Problem**:
- Related Work cites COP-KMeans, Davidson & Ravi 2005 and Davidson, Ravi & Ester 2007. For thresholds, it cites Daniels 2006 and Van Craenendonck 2017. For the album setting, it cites Tian 2007, EasyAlbum 2007, Song & Leung 2006 and FaceCluster 2025.
- It omits the works closest to *this* method, a density/core-point clusterer with ML/CL that is updated as data arrive:
  - C-DBSCAN (Ruiz, Spiliopoulou & Menasalvas, RSFDGrC 2007);
  - its streaming form C-DenStream (Ruiz et al., Discovery Science 2009);
  - constrained DBSCAN variants (Lasek & Gryz, ComSIS 2019);
  - semi-supervised incremental stream clustering with constraints (Halkidi et al., PAKDD 2012).
- On faces, it omits the following:
  - ConPaC, pairwise-constrained face clustering (Shi, Otto & Jain, TIFS 2018; also round-1 suggestion, still missing);
  - track-derived must-links for video face clustering (Wu et al., CVPR 2013), which is directly relevant to the future-work paragraph;
  - same-photo cannot-links in personal collections (Lo Presti et al., MTAP 2012).
- On order independence, it omits Grinch (Monath et al., KDD 2019). It also does not say that OGMC (already cited) explicitly targets order dependence for faces, which bears on the claim that no order-dependence evaluation was found.
- Round 1 also recommended the personal-album rank-order paper (Zhu, Wen & Sun, CVPR 2011), which is still missing.
- `innovation_scan_2026-11-07.md` §4 G4 states: "The paper must cite and differentiate Halkidi 2012, He 2019, Lasek & Gryz 2019, Beauchamp 2025, Monath 2019 and Shi 2017". None of these is in `references.bib`.

**Evidence Anchor**: `absence: Sec. II Related Work and references.bib — expected C-DBSCAN/Lasek & Gryz, Halkidi 2012, Shi et al. 2018 ConPaC, Wu et al. 2013, Monath 2019; checked Sec. I, Sec. II, Sec. III-C, Sec. VI, all 32 bib entries, innovation_scan_2026-11-07.md §4`

**Why it matters**: The gap statement and the "we combine known parts" framing are only checkable if the reader can see the nearest combination already published. C-DBSCAN and C-DenStream are already "density-based clustering + ML/CL", the latter for arriving data. The remaining difference (an order-invariance proof covering constraints, plus a persistence evaluation on faces) has to be stated against them.

**Suggestion**:
- Add these works with one sentence of differentiation each. For example: "C-DBSCAN and C-DenStream also combine density-based clustering with ML/CL constraints; they do not analyse insertion-order dependence, and were not evaluated on faces."
- Rewrite the gap sentence so that it is bounded to *face* clustering in personal libraries.
- Read the full texts of C-DBSCAN and C-DenStream before claiming that they do not analyse order. The scans were abstract-only.

**Severity**: Major
**Confidence**: 4 (core expertise; existence of C-DBSCAN, Lasek & Gryz, ConPaC and Wu 2013 verified by web search in this session; the others taken from the authors' scan; full texts not read)

### W4: The constrained step is Davidson–Ravi constrained single linkage, and "constrained maximum-spanning forest" overstates it
**Problem**: Adding core edges in decreasing similarity and skipping any union that joins a cannot-linked pair is greedy Kruskal with cannot-link checks. That is constrained single-linkage agglomerative clustering, as analysed by Davidson & Ravi (2005). Calling it a "constrained maximum-spanning forest" suggests an optimum. With several cannot-links, the greedy result is not in general the maximum-weight forest that separates every cannot-linked pair, which is a multiway-cut-type problem. The claim that a cannot-link "splits a wrong merge at its weakest links" is exact only for a single cannot-link pair.

**Evidence Anchor**: `text: Sec. III-C "which builds a constrained maximum-spanning forest" and "therefore splits a wrong merge at its weakest links"`

**Why it matters**: Clustering reviewers will recognise the algorithm and expect it to carry its standard name. They will also read "maximum-spanning forest" as an optimality claim the paper does not prove.

**Suggestion**:
- Write "a greedy (Kruskal-order) constrained single linkage, as in Davidson & Ravi [x], applied to the core-link graph".
- State that the split is exact for one cannot-link and heuristic for several.

**Severity**: Minor
**Confidence**: 5 (core expertise)

### W5: With corrections present, the clusterer is a batch recomputation at read time; the order-invariance proof leans on this, and the update time was measured without corrections
**Problem**: In `stable_cluster.py`, `labels()` switches to `_labels_constrained()` as soon as any constraint exists. That function ignores the incremental union-find state. It rebuilds a fresh union-find over *all* core edges sorted by similarity, and then re-runs a dense O(k²)-memory centroid merge. The proposition's "with corrections" case relies on exactly this. Under constraints, the method is therefore order-invariant because it is a deterministic batch algorithm over a cached neighbour graph, not because of an incremental property.

`exp18_update_time.py` contains no constraints, so the 3.5 s figure in Sec. V-F applies only to the uncorrected path. Since Cove's goal is a library that the user has corrected, the corrected path is the realistic one.

The fixed order used to resolve contradictory corrections is `sorted(self.must)` over face ids. Face ids follow insertion order, so for contradictory corrections and exact ties the result does depend on insertion order. The paper says this happens only in cases that "do not arise in practice". But limitation (ii) concedes that real users sometimes make wrong corrections, and wrong corrections are the most likely source of contradictions.

**Evidence Anchor**: `text: Proof sketch "With corrections, the components are built from the final lists in an order fixed by similarity"; Sec. V-F "We added 8,290 clean LFW faces ... with the shipped EdgeFace-S setting"`

**Why it matters**: Contribution 1 calls the method an *incremental* clusterer whose output "including the user's corrections" is invariant. The invariance is correct, but the incremental part does not apply to the corrected case, and that case is untimed. Davidson, Ravi & Ester (2007), which is cited, is specifically about *avoiding* full recomputation when constraints change.

**Suggestion**:
- State plainly that with corrections the labels are recomputed from the stored neighbour lists.
- Time `labels()` in exp18 with, say, 10 and 100 constraints.
- Key the conflict resolution on a stable face identifier (photo hash + box), not on the insertion id. Alternatively, detect contradictions through the must-link transitive closure and ask the user to resolve them.

**Severity**: Minor
**Confidence**: 5 (code read in full)

### W6: The headline "27%" counts libraries without corrections as fully kept, and "ten corrections" is the cap, not the number made
**Problem**: `satisfied()` returns 1.0 when a library has no constraints. In `exp15_corrections_edgeface_s.json`, 33 of the 240 library runs received no correction and so count as "100% held" in the lost condition, and the same happens for MBF (35 of 240). Over libraries that actually received corrections, the lost condition keeps 15.7% on average (20.3% pooled over corrections; MBF 13.5% / 16.9%), not 27%.

The mean number of corrections made is 5.4 (MBF 5.8). Only 91 of the 240 runs reached ten corrections. Yet the abstract says "With ten simulated corrections per library", and Sec. V-C says "Ten corrections per library raise F1".

**Evidence Anchor**: `table: Table II — "All (8 cond.)" row, Fixes held 27% / 100%; text: Abstract "With ten simulated corrections per library, B-Cubed F1 rises from 0.984 to 0.994"`

**Why it matters**: Both errors run in the conservative direction for the paper: the true loss is larger, and fewer corrections achieved the gain. But the headline numbers are computed incorrectly, and a reader who replicates them will notice.

**Suggestion**:
- Report "held" only over libraries with at least one correction, or pooled over corrections, and state which.
- Report the mean number of corrections made. Phrase the result as "up to ten (mean 5.4)".
- Optionally plot F1 against the number of corrections, which is the standard constrained-clustering learning curve (see W2).

**Severity**: Minor (core claim unaffected; numbers must be corrected)
**Confidence**: 5 (recomputed from the per-library JSON)

### W7: Recogniser-comparison details: the AgeDB/CFP-FP protocol is also non-official, CFP-FP's role is stated inconsistently, and training-identity overlap is unaddressed
**Problem**:
- `exp13_screen.py` subsamples 3,000 + 3,000 pairs from the *official* AgeDB-30 and CFP-FP lists and uses its own random 10-fold split. These numbers are therefore not on the official protocol either, but the text names only CALFW/CPLFW as non-standard.
- The resulting CFP-FP accuracy for EdgeFace-S (98.31%) is far above the 95.81% on Idiap's model card. That suggests the alignment or crops differ from the reference pipeline. Relative comparisons on identical crops remain valid, but readers will compare against the published numbers.
- Sec. V-D calls CFP-FP "a dataset not used for testing", yet Table III reports it as a test.
- Both recognisers are trained on WebFace-derived data, and the overlap between LFW and WebFace celebrities (round-1 R2 minor point) is still not discussed.

**Evidence Anchor**: `text: Sec. V-D "CFP-FP frontal–profile pairs (a dataset not used for testing)" vs Table III row "CFP-FP 98.18 / 98.31"`

**Why it matters**: These points are minor because the recogniser section is no longer the headline and the comparison is paired on identical inputs. Still, inconsistent statements about which data are test data weaken the paper's otherwise careful no-leakage story.

**Suggestion**:
- Say that all four sets use a 6,000-pair subsample with non-official folds.
- Call CFP-FP "a tuning set for the pose experiment, also reported in Table III".
- Add one sentence on possible LFW/WebFace identity overlap, which affects the absolute level of all clustering numbers, not their comparison.

**Severity**: Minor
**Confidence**: 4 (script read; published number from the Idiap model card, fetched this session)

### W8: The licence statement is still incomplete and misses EdgeFace's ShareAlike term
**Problem**: The declaration says "InsightFace models and EdgeFace weights are licensed for non-commercial research use."
- Idiap's EdgeFace model card states "EdgeFace is released under CC BY-NC-SA 4.0" (huggingface.co/Idiap/EdgeFace-Base, fetched 2026-11-07). That is non-commercial *and ShareAlike*. ShareAlike matters because Cove redistributes ONNX conversions of the weights, which are adaptations.
- GhostFaceNet's licence is not stated.
- The dataset terms (LFW, CALFW, CPLFW, AgeDB-30, CFP-FP; research-only for most) are not stated.

`REVISION_LOG_round2.md` records "licence wording kept", so my round-1 W6 was not addressed.

**Evidence Anchor**: `text: Declarations "InsightFace models and EdgeFace weights are licensed for non-commercial research use."`

**Why it matters**: Cove is a distributed application. Adopters need to know that the shipped recogniser is CC BY-NC-SA and that converted weights must carry the same licence.

**Suggestion**:
- List each component with its licence and source: SCRFD/`buffalo_s` (InsightFace, non-commercial research), EdgeFace (CC BY-NC-SA 4.0 per Idiap), GhostFaceNet (state its release terms), and the datasets (terms of use).
- State that Cove as shipped is for non-commercial use.

**Severity**: Minor
**Confidence**: 4 (EdgeFace and Immich pages fetched; InsightFace terms from its public README as checked in round 1; GhostFaceNet not checked)

### W9: Real personal-album and standard face-clustering benchmarks are still absent
**Problem**: The evaluation is LFW-derived only. IJB-B's clustering protocol (Whitelam et al., CVPRW 2017) and real album data (PIPA; FIW for relatives) were declined in revision, and the limitation is acknowledged.

**Evidence Anchor**: `text: Sec. VI "The libraries are simulations built from LFW celebrities"`

**Why it matters**: Now that the headline is corrections rather than accuracy, this matters less. But the correction gains (+0.010 F1 from a 0.984 baseline) sit near saturation, and real albums with children ageing and multi-face photos may behave differently.

**Suggestion**: This is acceptable for a regional venue if the limitation stays. If time allows, report Table II on IJB-B's clustering subsets.

**Severity**: Minor `[FIELD-NORM UNVERIFIED]`: I did not ground in a venue source the claim that an applied regional venue would require IJB-B.
**Confidence**: 3 (venue-norm uncertainty)

---

## Detailed Comments

### Literature Review
- **Coverage**: Better than round 1. HDBSCAN, COP-KMeans, Davidson & Ravi (2005, 2007), Tian 2007, EasyAlbum, Song & Leung and FaceCluster were added, and they are cited accurately. The nearest neighbours of the method are still missing (W3): constrained density-based clustering, constrained stream clustering, and pairwise-constrained face clustering.
- **Integration quality**: The related work is synthesised rather than listed. Daniels 2006 and Van Craenendonck 2017 (threshold selection from constraints) are accurate, but the paper never uses them, whereas ConPaC and C-DBSCAN, which bear directly on its method, are absent.
- **Research gap argument**: Bounded honestly ("in the sources we searched ... abstracts only"). It should be narrowed to faces in personal libraries and set against Immich's documented frozen-assignment behaviour (W1).

### Theoretical Framework
- **Appropriateness**: Positioning the method in the incremental-DBSCAN line is fine historically. At m = 1, single linkage is the honest frame, and the paper now says so.
- **Application depth**: Ester et al. (1998) show that incremental insertion matches re-running DBSCAN for core points and clusters. Border-point assignment can differ, which is exactly the DBSCAN 0.997 order agreement in Sec. V-A. "Gives the same result as re-running DBSCAN" should read "up to border points".
- **Alternative frameworks**: For constraints, the right frame is Davidson & Ravi's constrained agglomerative clustering (W4), with C-DBSCAN as the density-based analogue.

### Academic Argument Quality
- **Factual accuracy**:
  - The Immich characterisation is implicit and inaccurate (W1).
  - The 27% figure and "ten corrections" are misreported (W6).
  - The statement that CFP-FP was "not used for testing" contradicts Table III (W7).
  - The HDBSCAN order agreement of 0.983 deserves one sentence. HDBSCAN is order-free in principle, but ties in mutual-reachability distance make the MST order-dependent in practice.
- **Argument logic**: The "100% vs 27%" contrast is presented as evidence for the method. It is evidence for remembering constraints, which every constrained method does (W2).
- **Terminology**: "constrained maximum-spanning forest" (W4). "Order agreement" and "core face" are used consistently.

### Contribution to the Field
- **Incremental contribution**: The contribution has three parts:
  - (a) a correct, code-verified way of folding ML/CL constraints into a single-linkage + attach + merge clusterer while keeping exact order invariance;
  - (b) a correction-survival evaluation protocol for interactive face grouping;
  - (c) an honest equal-tuning comparison showing the method is on a par with average linkage, not better than it.

  Part (b) is the most novel to the album-annotation literature. Part (a) is a careful engineering combination.
- **Positioning**: The paper needs explicit contrast with C-DBSCAN/C-DenStream, with ConPaC, and with Immich-style frozen assignment.
- **Overclaiming risk**: The abstract's "all corrections still hold, against 27%" (by construction; W2, W6) and "photo managers must re-cluster" (W1).

### References (checked against publisher records and dblp in this session where marked)
- `davidson2005agglomerative`: pp. 59–70 is correct. The DOI 10.1007/11564126_11 is verified. The volume is LNAI 3721 in the LNCS series. Add the DOI.
- `davidson2007incremental`: title and pp. 240–249 are correct. The DOI 10.1145/1281192.1281221 is verified (researchr/dblp). Add it.
- `filonenko2025facecluster`: verified on dblp (ACM MM 2025, pp. 13546–13548). A hosted copy confirms the demo track.
- `cui2007easyalbum`: exists. A DOI 10.1145/1240624.1240684 appeared in search results; I did not open the ACM page, so verify before adding.
- `campello2013hdbscan`: add DOI 10.1007/978-3-642-37456-2_14 (from round 1, not re-checked this session).
- `montero2022ogmc`: no volume or pages. Add EAAI volume and article number from the publisher.
- `daniels2006threshold`, `vancraenendonck2017selection`, `tian2007face`, `song2006context`, `wagstaff2001copkmeans`: consistent with the authors' scan and my knowledge. I did not re-open them this session, and DOIs or pages are missing for several.
- `jung2025posetta` is in `references.bib` but never cited. It is harmless with BibTeX, but remove it or cite it in Sec. V-D, where pose-invariant recognition is relevant.
- `immich` and `photoprism` are GitHub links. For W1, cite the Immich documentation page on facial recognition, not just the repository.
- I found no reference that looks fabricated.

### Missing Key References
- Ruiz, Spiliopoulou & Menasalvas 2007, C-DBSCAN: density-based clustering with ML/CL. This is the closest prior method.
- Ruiz, Menasalvas & Spiliopoulou 2009, C-DenStream: constrained density-based clustering of streams (arriving data).
- Lasek & Gryz 2019, constrained DBSCAN variants (ComSIS).
- Halkidi et al. 2012, semi-supervised incremental clustering of streams with constraints (PAKDD).
- Shi, Otto & Jain 2018, ConPaC: pairwise-constrained face clustering (TIFS).
- Wu, Zhang, Hu & Ji 2013: video-track must-links for face clustering. Cite it in the future-work paragraph.
- Lo Presti et al. 2012: same-photo mutual exclusivity in personal collections (MTAP).
- Monath et al. 2019, Grinch: order-robust incremental hierarchical clustering (KDD).
- Zhu, Wen & Sun 2011: rank-order clustering for face tagging in personal albums (CVPR).
- Biemann 2006, Chinese Whispers: a baseline lead (dlib's face-clustering algorithm).
- Immich documentation, "Facial recognition" (web): primary source for the deployed frozen-assignment behaviour.

~~~yaml suggested-references
- title: "C-DBSCAN: Density-Based Clustering with Constraints"
  authors: ["Ruiz, C.", "Spiliopoulou, M.", "Menasalvas, E."]
  year: "2007"
  doi: "10.1007/978-3-540-72530-5_25"
  arxiv_id: null
  status: "verified (web search this session: RSFDGrC 2007, LNCS 4482, pp. 216-223)"
- title: "C-DenStream: Using Domain Knowledge on a Data Stream"
  authors: ["Ruiz, C.", "Menasalvas, E.", "Spiliopoulou, M."]
  year: "2009"
  doi: null
  arxiv_id: null
  status: "existence verified (publisher listing in search results); venue Discovery Science 2009 not opened"
- title: "Density-Based Clustering with Constraints"
  authors: ["Lasek, P.", "Gryz, J."]
  year: "2019"
  doi: "10.2298/CSIS180601007L"
  arxiv_id: null
  status: "verified (search result listing ComSIS 16(2) with this DOI)"
- title: "A Semi-Supervised Incremental Clustering Algorithm for Streaming Data"
  authors: ["Halkidi, M.", "et al."]
  year: "2012"
  doi: null
  arxiv_id: null
  status: "unverified this session (taken from the authors' innovation scan, abstract level); co-authors not checked"
- title: "Face Clustering: Representation and Pairwise Constraints"
  authors: ["Shi, Y.", "Otto, C.", "Jain, A. K."]
  year: "2018"
  doi: "10.1109/TIFS.2018.2796999"
  arxiv_id: "1706.05067"
  status: "verified (arXiv record and two indexes listing the DOI)"
- title: "Constrained Clustering and Its Application to Face Clustering in Videos"
  authors: ["Wu, B.", "Zhang, Y.", "Hu, B.-G.", "Ji, Q."]
  year: "2013"
  doi: "10.1109/CVPR.2013.450"
  arxiv_id: null
  status: "verified (dblp/CVF records via search: CVPR 2013, pp. 3507-3514)"
- title: "A Data Association Approach to Detect and Organize People in Personal Photo Collections"
  authors: ["Lo Presti, L.", "et al."]
  year: "2012"
  doi: null
  arxiv_id: null
  status: "unverified this session (authors' scan, abstract level)"
- title: "Scalable Hierarchical Clustering with Tree Grafting"
  authors: ["Monath, N.", "et al."]
  year: "2019"
  doi: null
  arxiv_id: null
  status: "unverified this session (authors' scan, abstract level; KDD 2019)"
- title: "A Rank-Order Distance Based Clustering Algorithm for Face Tagging"
  authors: ["Zhu, C.", "Wen, F.", "Sun, J."]
  year: "2011"
  doi: "10.1109/CVPR.2011.5995680"
  arxiv_id: null
  status: "unverified this session (DOI from round-1 report, not re-checked)"
- title: "Chinese Whispers: An Efficient Graph Clustering Algorithm and Its Application to Natural Language Processing Problems"
  authors: ["Biemann, C."]
  year: "2006"
  doi: null
  arxiv_id: null
  status: "unverified this session (TextGraphs workshop at HLT-NAACL 2006, from memory)"
- title: "Immich documentation: Facial Recognition"
  authors: ["Immich contributors"]
  year: "2026"
  doi: null
  arxiv_id: null
  status: "verified (docs.immich.app/features/facial-recognition fetched 2026-11-07)"
~~~

---

## Questions for Authors
1. On the same embeddings and simulated corrections, what later F1 and order agreement do (a) constrained average linkage and (b) an Immich-style frozen-assignment rule achieve? If constrained average linkage matches 0.992, what remains of the method claim beyond order invariance?
2. How do C-DBSCAN (Ruiz et al. 2007) and C-DenStream (2009) differ from your constrained core-point clusterer? Is either order-invariant, and did you read their full texts?
3. Over libraries that actually received corrections, what share of corrections survives plain re-clustering, and how many corrections were made on average?
4. How long does `labels()` take on the 8,290-face library with 10 and with 100 constraints? How are contradictory corrections resolved independently of insertion order?

---

## Minor Issues
- Sec. II: "gives the same result as re-running DBSCAN" should read "up to border-point assignment".
- Sec. III-C: name the step "constrained single linkage (Davidson & Ravi)".
- Sec. V-A: explain HDBSCAN's 0.983 order agreement (ties in mutual-reachability distance).
- Sec. V-D vs Table III: CFP-FP role wording (W7).
- `references.bib`: add the verified DOIs listed under References. Remove the uncited `jung2025posetta` or cite it. Complete `montero2022ogmc`.
- The header comment in `references.bib` says "Every entry verified (DOI, publisher page ...)", but the round-2 block says DOIs were omitted. Make the two consistent.

---

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | `references/quality_rubrics.md` Originality; reviewer card (distinctness of the ML/CL method from prior work) | PARTLY_MEETS | `text: Sec. I "we do not claim these parts as new"`; W3 absence anchor | Honest sizing. The evaluation protocol (correction survival) is new to face-album work. The algorithm is a combination of known parts, and its nearest density-based constrained relatives are not differentiated. | C-DBSCAN/C-DenStream full texts not read | Yes. Positioning must be fixed (W3) |
| Methodological Rigor | rubric; reviewer card (baseline adequacy) | PARTLY_MEETS | `table: Table II — no constrained or re-applied baseline` | Equal tuning for unconstrained methods is good. The headline comparison lacks constraint-aware baselines and uses a metric that is true by construction. | Detailed design is R1's remit | Yes (W2) |
| Evidence Sufficiency | rubric | PARTLY_MEETS | `table: Table II — "All (8 cond.)" 27% / 100%` | The corrections gain is real (CI excludes 0). Survival is unproven as a method advantage, and the headline numbers are miscomputed (W6). | — | Yes (W2, W6) |
| Argument Coherence | rubric | PARTLY_MEETS | `text: Abstract "Photo managers ... must re-cluster whenever new photos arrive"` | The problem framing conflicts with deployed incremental practice (Immich). Otherwise the logic is coherent, and the CPLFW explanation is now correct. | Immich behaviour taken from docs | Yes (W1) |
| Writing Quality | rubric | MEETS | `text: Sec. VI "What they do not support."` | Plain and precise. Limitations are explicit. | Domain view only | No |
| Literature Integration | rubric; reviewer card (related-work coverage, citation correctness) | PARTLY_MEETS | W3 absence anchor; References section | Citations present are accurate and verified where checked. Key constrained-density, stream and face-constraint works are missing despite the authors' own scan. | Abstract-level verification for some | Yes (W3) |
| Significance & Impact | rubric | MEETS | `text: Sec. II "we did not find an evaluation of whether such corrections survive later re-clustering"` | Persistent, order-invariant corrections address a real need in local-first albums. The significance would rise with a fair comparison. | Simulated users only (R1/R3 remit) | No |

**Recommendation rationale**: The unresolved decision-bearing criteria are Methodological Rigor and Evidence Sufficiency (W2 and W6: constraint-aware baselines are missing and the headline numbers are miscomputed), Argument Coherence (W1: the Immich framing) and Literature Integration (W3). Each can be repaired with existing data and code: three extra baselines in exp15, a recomputed survival figure, re-framing, and about ten citations. None is fatal. The strengths in honest positioning and code correctness do not offset the missing fair comparison behind the new headline. Major Revision.
