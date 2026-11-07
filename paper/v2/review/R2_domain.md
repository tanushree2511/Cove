# Peer Review Report

## Manuscript Information
- **Title**: Order-Stable Incremental Face Clustering for Local-First Personal Photo Libraries
- **Manuscript ID**: cove_paper.tex (v2)
- **Review Date**: 2026-11-06
- **Review Round**: Round 1 review

---

## Reviewer Information

### Reviewer Role
Peer Reviewer 2 (Domain)

### Reviewer Identity
Face-recognition researcher (ArcFace-family models, LFW/CALFW/CPLFW protocols). Checks clustering baselines (GCN clusterers, OGMC, DBSCAN/HDBSCAN as used in Immich), whether the recogniser comparison is fair, and licence issues.

### Review Focus
Whether the paper places itself correctly in the face-clustering and lightweight face-recognition literature, whether the baselines and benchmark protocols match what the field accepts, and whether the domain claims (the order-invariance novelty, where the pose and age failures come from, and the recogniser ranking) hold up against that literature and the released evaluation code.

---

## Overall Assessment

### Recommendation
- [ ] Accept
- [ ] Minor Revision
- [x] **Major Revision** — Substantial revisions needed, re-review required after revision
- [ ] Reject

### Confidence Score
4 — the paper's face-recognition and clustering content is within my expertise. I did not re-run experiments; I read the evaluation scripts and result JSONs only.

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

### Summary Assessment
The paper measures how much input order changes greedy leader face clustering on simulated LFW personal libraries. It proposes a core-face union-find clusterer with a looser attach threshold and a centroid merge, proves the clusterer is order-invariant, stress-tests it on degraded images, CALFW and CPLFW, and compares four lightweight recognisers on identical crops before adopting EdgeFace-S. The engineering is careful and the negative results are reported honestly. Several domain-level problems weaken the claims, though.

(1) With the selected m=1, the clusterer is essentially threshold-graph connected components (single linkage) plus nearest-core attachment. Order invariance therefore follows from classical results, and the paper does not position itself against them.

(2) The most relevant practical baseline is missing: the DBSCAN-derived incremental algorithm of Immich, which the paper itself names. DBSCAN/HDBSCAN and single linkage are also missing.

(3) The "CALFW" and "CPLFW" verification numbers do not use the official pair lists. The code samples random different-person pairs, which removes the benchmarks' hard negatives. This explains why EdgeFace-S scores 96.03 on CPLFW here against 92.48 in its official results, and it undermines the paper's claims about the published literature.

(4) Table II contradicts the claim that the pose failures lie in the embedding rather than the clustering: average-linkage clustering on the same embeddings scores 10 points higher on CPLFW.

(5) LFW-derived libraries are close to saturation for WebFace-trained models. Standard face-clustering benchmarks (IJB-B, real photo-album sets) are not used.

All of these can be fixed, so I recommend Major Revision.

---

## Strengths

### S1: The recogniser comparison is controlled and accounts for each model's similarity scale
All four recognisers embed the same detector/alignment crops. The paper reports paired differences with bootstrap CIs. It also notices that EdgeFace-S needs re-tuned thresholds because its cosine scale is shifted, and it re-tunes only on tuning data, reporting the untuned column as well (Table III, third column). This is better practice than most recogniser "swap" papers, which reuse thresholds or quote numbers from each model's own paper.
**Evidence Anchor**: `text: Sec. V-D "Thresholds cannot simply be reused: EdgeFace-S places all cosine similarities higher"`

### S2: Failure modes are reported openly, including a negative tuning result
Sec. V-C reports that pose/age-aware re-tuning and shared-neighbour linking both fail on held-out data. The paper does not hide this. That makes the paper more credible and more useful to practitioners.
**Evidence Anchor**: `text: Sec. V-C "on the held-out sets it lowered F1 on CALFW (0.934$\to$0.916), CPLFW (0.783$\to$0.778)"`

### S3: The metric and the evaluation split suit face clustering
B-Cubed F1 is the accepted metric for identity clustering, and it is the IJB-B clustering protocol's metric. CALFW and CPLFW are kept fully held out, while AgeDB-30 and CFP-FP are used only for tuning.
**Evidence Anchor**: `text: Sec. IV "CALFW ... and CPLFW ... are used only as held-out test sets, clustered whole."`

### S4: Model licences are disclosed
The declarations state the non-commercial terms of the InsightFace models. Many system papers skip this.
**Evidence Anchor**: `text: Declarations "Model licences: InsightFace models and EdgeFace weights are licensed for non-commercial research use."`

---

## Weaknesses

### W1: The novelty of order invariance is not placed against single linkage / threshold-graph components, to which the selected configuration reduces
**Problem**: With the tuned m=1, a face is core whenever it has at least one neighbour at or above τℓ. The core-face clusters are then exactly the connected components of the τℓ similarity graph, i.e. a single-linkage cut at τℓ. DBSCAN with minPts=2 produces the same components. Order invariance of connected components or single linkage computed incrementally with union-find is a classical property, not a new one. What the paper actually adds is (a) attaching isolated faces to their nearest core at a lower threshold τa and (b) an average-linkage merge of centroids. The text instead presents the whole construction as adapting incremental DBSCAN, with order invariance as a headline contribution. Also, at m=1 the safeguard against chaining ("a blurred photo cannot chain two people together") only covers faces with no neighbour at or above 0.50. Any face that does have such a neighbour can still chain clusters, as in single linkage.
**Evidence Anchor**: `text: Sec. IV "$\tau_\ell=0.50$, $m=1$, $\tau_a=0.35$, $\tau_g=0.45$"`
**Why it matters**: Reviewers in the clustering community will read contribution 2 as overclaimed. The invariance proof is correct, but it is close to trivial for the configuration actually shipped.
**Suggestion**: State the reduction for m=1 explicitly. Cite single-linkage and connected-components clustering as the order-invariant reference, and reframe the contribution as an order-invariant attach-and-merge layer on top of density/threshold-graph components. Add single linkage at τℓ (with and without the attach step) as a baseline, so readers can see how much the attach and merge steps add.
**Severity**: Major
**Confidence**: 5 — core expertise: graph-based face clustering

### W2: The directly relevant DBSCAN-family baselines are missing, including the algorithm used by Immich
**Problem**: Related Work names Immich as a density-based local-first system. Immich's documentation describes its algorithm as "derived from DBSCAN", with a minimum-recognised-faces core test and deferred handling of non-core faces. It also states that clusters from previous rounds are preserved, so the output depends on history. This is structurally the closest prior system to the proposed method, and it runs on the same InsightFace buffalo embeddings. The paper postpones the comparison, and it also leaves out plain DBSCAN/HDBSCAN on cosine distance and Chinese Whispers (dlib's widely used face clusterer). The only order-free batch reference is average-linkage agglomerative clustering, so the claim that "order-free batch methods are too slow" rests on a single method.
**Evidence Anchor**: `text: Sec. VI "nor with the density-based clustering of self-hosted managers; both are future work."`
**Why it matters**: The research gap is that no published work evaluates order sensitivity for such systems. It is best closed by measuring Immich's own rule. Without that, a reader cannot tell whether the gains over First-Leader would also hold over the method deployed in the most popular local-first manager. Field norm: face-clustering papers compare against DBSCAN/HDBSCAN and graph-component baselines (e.g. Otto et al. TPAMI 2018 and Yang et al. CVPR 2019, both already cited, report DBSCAN/HAC-family baselines).
**Suggestion**: Re-implement Immich's incremental rule (core test with minFaces, maxDistance, deferred non-core pass) on the same embeddings, and run it across the 20 shuffled orders and the Table II conditions. Add sklearn DBSCAN/HDBSCAN (batch, cosine) and single linkage. All of these are training-free and CPU-only, so the reason given for excluding GCN methods does not apply to them. GCN clusterers and OGMC can stay future work if the paper justifies this, e.g. by their need for labelled training clusters. The justification currently given for OGMC ("target GPU batch or very large settings") does not fit an online CPU method, so it should be restated.
**Severity**: Major
**Confidence**: 4 — core expertise; Immich behaviour checked against its public docs and server source, not run

### W3: The "CALFW/CPLFW" verification numbers use a non-official protocol, and the paper then draws conclusions about the published literature from them
**Problem**: According to `evaluation/exp13_screen.py`, CALFW and CPLFW pairs are "sampled from identity labels (same = two photos of one person; different = two random people)". The official CALFW/CPLFW lists deliberately use hard negatives (e.g. same gender and race), and those negatives are what make the benchmarks hard. With random negatives the task gets much easier. That is consistent with Table III's EdgeFace-S CPLFW accuracy of 96.03%, against the 92.48% reported in the official EdgeFace release. The paper calls these numbers "CALFW" and "CPLFW" without qualification, and then says published comparisons "overstate the gap". That conclusion cannot be drawn from a protocol that differs from the published one. The paper's own crops and alignment (SCRFD-500M at 320 px) differ from the standard released aligned crops, and that differs again from published practice. Separately, Sec. IV says AgeDB-30/CFP-FP use "official labelled pairs", while the script subsamples 3,000+3,000 from them. That is a smaller inconsistency.
**Evidence Anchor**: `text: Sec. V-D "published comparisons against older MobileFaceNet checkpoints overstate the gap"`
**Why it matters**: Any face-recognition reader will compare Table III with published numbers and find them inflated by 3–4 points on CPLFW. That undermines the recogniser section, and the remark about the literature is unsupported. Field norm: the official 10-fold pair lists are the reporting standard for these sets (Zheng et al. CALFW arXiv:1708.08197; Zheng & Deng CPLFW TR 18-01; EdgeFace TBIOM 2024 and GhostFaceNets reporting, all cited).
**Suggestion**: Re-run the verification table on the official CALFW/CPLFW (and full AgeDB-30/CFP-FP) pair lists with their official folds. Keep the app-crop numbers as a second, clearly labelled column (e.g. "app pipeline, random negatives"). Either delete the sentence about published comparisons overstating the gap, or support it with a cited, like-for-like comparison.
**Severity**: Major
**Confidence**: 5 — core expertise: LFW-family verification protocols; confirmed in the released script

### W4: The paper attributes the pose and age failures to the embedding, but its own Table II contradicts this
**Problem**: The abstract, Sec. V-C and the Conclusion all say the remaining errors "come from the face embedding" and not from the clustering. In Table II, however, average-linkage agglomerative clustering on the same MBF embeddings reaches CPLFW F1 0.881 against 0.783 for the proposed method, and First-Leader reaches 0.857. On CALFW the gap is 0.955 against 0.934. Sec. V-B even explains the mechanism: agglomerative clustering "can therefore collect weak but numerous links". So a different clustering rule recovers much of the lost pose performance with the same embedding. The argument in Fig. 2 only shows that single pairs are not separable. It does not show that the cluster structure is unrecoverable.
**Evidence Anchor**: `table: Table II — CPLFW (pose) row, Agglom. 0.881 vs Ours 0.783 on identical embeddings`
**Why it matters**: This attribution is the motivation for the whole recogniser section (contribution 4). If part of the CPLFW gap comes from the clustering's link rule (single-pair threshold, with no aggregation over many weak links), then switching recogniser is only one remedy and may not be the main one.
**Suggestion**: Rephrase the claim. For example: under a single-pair link rule, CPLFW errors are limited by pair separability, while aggregate-linkage methods recover part of them at batch cost. Quantify how much of the gap the embedding explains by also running agglomerative clustering on EdgeFace-S embeddings. Discuss order-invariant ways to aggregate weak links (e.g. average linkage restricted to the centroid merge, which the method already has, with a looser τg on CPLFW-like tuning data).
**Severity**: Major
**Confidence**: 5 — follows directly from the manuscript's own table

### W5: Test data is near saturation and identities may overlap with training data; standard face-clustering and photo-album benchmarks are not used
**Problem**: All personal libraries come from LFW. Modern WebFace-trained ArcFace models are near ceiling on LFW (clean F1 0.998 here; EdgeFace reports 99.78% LFW verification). LFW subjects are public figures, the same population that web-scraped training sets such as WebFace260M are built from. The paper does not discuss whether LFW identities overlap with the recognisers' training identities. All robustness differences therefore come from synthetic degradations of near-ceiling data. The field's accepted face-clustering benchmarks are IJB-B clustering (B-Cubed F, 512–1,845 subjects) and the MS1M/MS-Celeb splits used by GCN clusterers. Real personal-album datasets are PIPA (Flickr albums) and the Gallagher collection. None of these is used. For the "relatives" stand-in, look-alikes chosen by the same embedding's mean similarity are a self-referential proxy. Families In the Wild (FIW) offers real kin.
**Evidence Anchor**: `text: Sec. VI "Our libraries are simulations built from LFW celebrities"`
**Why it matters**: The headline robustness numbers (e.g. 0.972 vs 0.894 on mixed) cannot be compared with any face-clustering result in the literature, and they may overstate performance on real family albums. Field norm: IJB-B defines a clustering protocol with B-Cubed metrics (Whitelam et al., CVPRW 2017), and face-clustering work routinely reports on it (e.g. Shi, Otto & Jain, TIFS 2018).
**Suggestion**: Add at least one standard benchmark: the IJB-B clustering protocols, which are small enough for CPU and use the paper's own metric, or the face tracks of a real album set (PIPA). Add a sentence on possible identity overlap between LFW and WebFace600K/WebFace4M-12M, and check it if name lists are available. Consider FIW for the look-alike/relatives condition.
**Severity**: Major
**Confidence**: 4 — core expertise; I did not verify whether WebFace260M de-duplicates LFW identities, so the overlap point is posed as a question, not asserted

### W6: The licence statement is imprecise for a system that "ships" these models
**Problem**: The declaration groups InsightFace models and EdgeFace weights together as non-commercial. The EdgeFace repository is released under BSD-3-Clause. Any non-commercial restriction on its weights would come from training-data terms (WebFace), not from the repository, and the paper does not say which document it relies on. GhostFaceNet (HamadYA release, loaded through deepface) has no licence statement at all. The paper also says the evaluated configuration is what "Cove now ships". InsightFace's buffalo_s (SCRFD-500M + w600k_mbf) is explicitly restricted to non-commercial research. A distributed application that bundles it (the repository builds a Windows installer) needs a clear statement of its distribution terms.
**Evidence Anchor**: `text: Sec. V-D "This is the configuration Cove now ships"`
**Why it matters**: Readers and adopters cannot tell whether the recommended configuration can be legally redistributed. That bears directly on the practical contribution.
**Suggestion**: Give each component's licence with a source: SCRFD/buffalo_s (InsightFace model licence), EdgeFace code (BSD-3) and the terms of its weights/training data, GhostFaceNet weights, and the dataset licences (LFW, CALFW, CPLFW, AgeDB, CFP-FP). State that Cove is distributed for non-commercial use, or name a permissively licensed alternative.
**Severity**: Minor
**Confidence**: 4 — licence texts checked for EdgeFace (BSD-3); InsightFace terms from its public README; GhostFaceNet not checked

### W7: Related work omits key face-clustering and on-device prior work
**Problem**: Related Work cites rank-order (Otto 2018) and two 2019 GCN papers. It does not cite the original rank-order face-tagging work for personal albums (Zhu et al. CVPR 2011), which addresses the same personal-photo setting. It also misses ConPaC/IJB-B clustering (Shi et al. TIFS 2018), the later GCN-V/E (Yang et al. CVPR 2020), HDBSCAN (Campello et al. 2013), and Apple's published on-device people-recognition pipeline (2021), which is the closest industrial "local-first" analogue. The claim that the WebFace600K MobileFaceNet is trained on WebFace has no citation for WebFace260M (Zhu et al. CVPR 2021).
**Evidence Anchor**: `absence: Sec. II Related Work and references.bib — expected Zhu et al. 2011 rank-order face tagging, Shi et al. 2018, HDBSCAN, WebFace260M, Apple on-device people recognition; checked Sec. II, Sec. III-A, Sec. V-D, full bibliography`
**Why it matters**: The gap argument ("not aware of a published evaluation ... for such systems") and the positioning of the method both depend on covering this literature.
**Suggestion**: Add the references below and one sentence on each, saying how the present work differs (incremental, order-invariant, CPU, training-free).
**Severity**: Minor
**Confidence**: 5 — core expertise

---

## Detailed Comments

### Literature Review / Theoretical Framework
- **Coverage**: See W7. Coverage of lightweight recognisers is adequate. The clustering literature stops at 2019, and there is nothing on personal-album face clustering or on-device industrial systems.
- **Integration quality**: The literature is synthesised rather than listed, but the reasons for excluding learned clusterers are bundled (labels, GPU, re-clustering) and are applied to OGMC, where they do not fit (W2).
- **Research gap argument**: Plausible, but it would be convincing only if Immich's actual rule were measured (W2).
- **Framework**: Placing the method in the incremental DBSCAN line is appropriate. With m=1 the density element disappears, though, and the right reference is single linkage (W1).

### Academic Argument Quality
- **Factual accuracy**: The CALFW/CPLFW naming is wrong for a non-official protocol (W3). The sentence about published comparisons overstating the gap is unsupported (W3). The attribution of failures to the embedding conflicts with Table II (W4). The EdgeFace parameter counts (3.65M / 1.77M) and γ values match the EdgeFace paper.
- **Terminology**: "Core face" is used consistently. "Order agreement" is a clear name for ARI between partitions.

### Contribution to the Field
- **Incremental contribution**: An order-invariant attach-and-merge layer over threshold-graph components, evaluated for degraded consumer photos, plus a practical, controlled recogniser swap. This is a useful systems contribution for local-first photo management. The algorithmic novelty is modest (W1).
- **Overclaiming risk**: Contribution 2 (W1), the conclusions about the literature in Sec. V-D (W3), and "traces them to the face embedding" (W4).

### Missing Key References
- Zhu, Wen & Sun, CVPR 2011: rank-order clustering for face tagging in personal albums, the closest setting to this paper.
- Whitelam et al., CVPRW 2017 (IJB-B): the standard face-clustering protocol with B-Cubed F.
- Shi, Otto & Jain, TIFS 2018: face-clustering baselines on IJB-B.
- Yang et al., CVPR 2020: GCN-V/E, the more recent learned clusterer.
- Campello, Moulavi & Sander, PAKDD 2013: HDBSCAN.
- Zhu et al., CVPR 2021: WebFace260M, the training-data source of w600k_mbf and EdgeFace.
- Zhang et al., CVPR 2015: PIPA, a real photo-album person dataset.
- Robinson et al., ACM MM 2016: Families In the Wild, real kin for the look-alike condition.
- Apple ML Research, 2021: on-device people recognition in Photos (blog; URL machinelearning.apple.com/research/recognizing-people-photos, existence checked only through secondary coverage) [UNVERIFIED as a citable primary source].
- Biemann, 2006: Chinese Whispers (dlib's face-clustering algorithm), as a baseline lead.

```yaml suggested-references
- title: "A Rank-Order Distance Based Clustering Algorithm for Face Tagging"
  authors: ["Zhu, C.", "Wen, F.", "Sun, J."]
  year: "2011"
  venue: "CVPR 2011"
  doi: "10.1109/CVPR.2011.5995680"
  arxiv_id: null
- title: "IARPA Janus Benchmark-B Face Dataset"
  authors: ["Whitelam, C.", "et al."]
  year: "2017"
  venue: "CVPR Workshops 2017"
  doi: "10.1109/CVPRW.2017.87"
  arxiv_id: null
- title: "Face Clustering: Representation and Pairwise Constraints"
  authors: ["Shi, Y.", "Otto, C.", "Jain, A. K."]
  year: "2018"
  venue: "IEEE Trans. Information Forensics and Security"
  doi: null
  arxiv_id: "1706.05067"
- title: "Learning to Cluster Faces via Confidence and Connectivity Estimation"
  authors: ["Yang, L.", "Chen, D.", "Zhan, X.", "Zhao, R.", "Loy, C. C.", "Lin, D."]
  year: "2020"
  venue: "CVPR 2020"
  doi: null
  arxiv_id: "2004.00445"
- title: "Density-Based Clustering Based on Hierarchical Density Estimates"
  authors: ["Campello, R. J. G. B.", "Moulavi, D.", "Sander, J."]
  year: "2013"
  venue: "PAKDD 2013, LNCS 7819"
  doi: "10.1007/978-3-642-37456-2_14"
  arxiv_id: null
- title: "WebFace260M: A Benchmark Unveiling the Power of Million-Scale Deep Face Recognition"
  authors: ["Zhu, Z.", "et al."]
  year: "2021"
  venue: "CVPR 2021"
  doi: null
  arxiv_id: "2103.04098"
- title: "Beyond Frontal Faces: Improving Person Recognition Using Multiple Cues"
  authors: ["Zhang, N.", "Paluri, M.", "Taigman, Y.", "Fergus, R.", "Bourdev, L."]
  year: "2015"
  venue: "CVPR 2015"
  doi: null
  arxiv_id: "1501.05703"
- title: "Families in the Wild (FIW): Large-Scale Kinship Image Database and Benchmarks"
  authors: ["Robinson, J. P.", "Shao, M.", "Wu, Y.", "Fu, Y."]
  year: "2016"
  venue: "ACM Multimedia 2016"
  doi: "10.1145/2964284.2967219"
  arxiv_id: null
- title: "Chinese Whispers: an Efficient Graph Clustering Algorithm and its Application to Natural Language Processing Problems"
  authors: ["Biemann, C."]
  year: "2006"
  venue: "TextGraphs Workshop, HLT-NAACL 2006"
  doi: null
  arxiv_id: null
```

---

## Questions for Authors
1. With m=1, is there any face for which the method's output differs from "single linkage at τℓ, then attach singletons at τa, then centroid merge"? If not, why does the paper frame the method as DBSCAN-based rather than single-linkage-based?
2. How does Immich's incremental rule, re-implemented on the same MBF embeddings, score on the 20-order agreement test and on the Table II conditions?
3. Can you report Table III on the official CALFW/CPLFW pair lists and folds? Which document supports the non-commercial licence of the EdgeFace weights?
4. Does agglomerative clustering on EdgeFace-S embeddings exceed 0.854 on CPLFW? If it does, how much of the remaining pose gap belongs to the link rule rather than the embedding?

---

## Minor Issues

### Citation Format
- The OGMC entry has no volume or pages.
- The Immich and PhotoPrism entries are software repositories. Cite the documentation page that describes their clustering algorithm, so the claim that they use "density-based methods" can be checked; for PhotoPrism I could not verify it.

### Figures and Tables
- Table III: the CFP-FP accuracy denominators differ from 6,000 (detection failures dropped, per `exp13_screen.json`). State how many pairs were actually used for each set.
- Table III: the GhostFaceNet CALFW CI has a lower bound of exactly 0.000. Note that this is borderline.
- Also report pairwise F alongside B-Cubed F, so the numbers can be compared with GCN-clustering papers.

### Layout
- The author block still contains template placeholders ([College name], [email]).

---

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | quality_rubrics (domain lens) | PARTLY_MEETS | W1 | Order invariance at m=1 is classical; the attach-and-merge layer and the degraded-photo study are new | none identified | yes — the framing must change |
| Methodological Rigor | quality_rubrics | NOT_ASSESSED | — | Reviewer 1's remit; domain protocol issues are raised in W3 | — | no |
| Evidence Sufficiency | quality_rubrics (domain lens) | PARTLY_MEETS | W2, W5 | Missing DBSCAN/Immich baselines; no standard or real-album benchmark | none identified | yes |
| Argument Coherence | quality_rubrics (domain lens) | PARTLY_MEETS | W4 | The attribution of failures to the embedding contradicts Table II | none identified | yes |
| Writing Quality | quality_rubrics | NOT_ASSESSED | — | Outside this remit | — | no |
| Literature Integration | quality_rubrics | PARTLY_MEETS | W7, W3 | Key clustering and album work missing; inaccurate remark about published recogniser comparisons | none identified | yes (repairable) |
| Significance & Impact | quality_rubrics (domain lens) | MEETS | S1, S2 | Practically useful for local-first photo managers; honest failure analysis | Depends on W2 outcome | no |

The decision-bearing items still open are W1–W5: novelty framing, missing DBSCAN/Immich baselines, the non-official verification protocol, the attribution claim, and benchmark realism. All can be repaired with re-framing and additional CPU-only experiments that use the existing pipeline.
