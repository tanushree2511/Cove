# Innovation scan for Cove face clustering — integrative literature scan (deep-research, full mode)

Date: 2026-11-07. Form of review: integrative/narrative scan (the author replied "proceed" to the review-form note, recorded as *skip*).
This is **not** a systematic review: one reviewer, abstract-level reading, no registered protocol.

## 1. Research question (confirmed by the author)
Which techniques published 2019-2026 (plus foundational work) could raise Cove's clustering accuracy on cross-pose and occluded
faces, or remove per-recogniser threshold tuning, while running on a laptop CPU, keeping the order-invariance property and the
user-correction feature — and which of them have **not** been found in prior work on incremental face clustering for personal
photo libraries?

Sub-questions: (1) recent methods for pose/occlusion in face clustering and their CPU cost; (2) prior use in incremental,
order-invariant or user-constrained settings (novelty check); (3) testability with the existing exp14-16 protocol.

## 2. Method
* Sources searched: SciSpace (280M papers), Consensus (Semantic Scholar/OpenAlex), web search for product documentation.
  Scholar Gateway was attempted and returned ACCESS_DENIED; two Consensus queries hit a rate limit and were re-run on SciSpace.
* Queries (natural language, verbatim intent): GCN linkage face clustering; incremental/online order-independent face clustering;
  calibrating face similarity to probabilities across models; context cues in personal albums (co-occurrence, clothing, time);
  quality-aware face clustering; incremental clustering keeping must-link/cannot-link with order independence; calibration for
  clustering threshold transfer / backward-compatible embeddings; foundation models (CLIP/DINOv2) for face/person clustering;
  active pairwise queries for face clustering; metric/threshold learning from pairwise constraints; Immich clustering behaviour.
* Inclusion: peer-reviewed or preprint papers whose abstract addresses face/person clustering, incremental/constrained
  clustering, or similarity calibration. Product documentation used only for the "what deployed apps do" question.
* **Read scope: abstracts only** for every paper below. Following the skill's rule, no method-level weaknesses are claimed for
  any paper, and every "not found" statement is bounded to the queries above.
* Novelty wording: "not found in the searched sources" — never "never tried".

## 3. Findings: what already exists (prior art found)

| Candidate idea | Prior art found (abstract level) | Verdict |
|---|---|---|
| Learned linkage with GCN / transformers on k-NN graphs | Wang et al. 2019 (L-GCN, CVPR); Yang et al. 2019, 2020 (GCN-D/S, GCN-V/E, CVPR); Ye et al. 2021 (Face Transformer); Zhang et al. 2022 (Ada-NETS, ICLR); Chen et al. 2022 (hard clusters); many 2022-2025 variants | Not novel; batch, GPU-trained on MS-Celeb |
| Asking the user the most useful question (active clustering) | Biswas & Jacobs 2012/2014 (faces); Barr et al. 2014 (active face clustering); Basu et al. 2004; COBRA 2018; A3S 2024; FALCON 2026 | Not novel |
| Face clustering with pairwise constraints | Shi, Otto & Jain 2017 (ConPaC) | Not novel as such |
| Incremental / streaming clustering with constraints | Halkidi et al. 2012 (constraint streams); He et al. 2019 (incremental constrained random walk); Beauchamp 2025 (thesis, incremental user constraints); Lasek & Gryz 2019 (constrained DBSCAN, ic-DBSCAN) | Prior art for the *idea* behind our corrections feature |
| Order-independent incremental clustering | Monath et al. 2019 (Grinch: order independence under a separability condition); Bandyopadhyay & Murty 2016 (order-independent incremental algorithm); Montero et al. 2021 (OGMC: reduces order dependence for faces) | Prior art for order independence; none found combining it with user constraints for faces |
| Context in personal albums: clothing, capture time, "two faces in one photo are different people" | Song & Leung 2006; Anguelov et al. 2007 (CVPR); Lo Presti et al. 2012 (mutual-exclusivity constraint); Zhang et al. 2013 (context-assisted clustering, high precision kept by iterative cluster merging); Li et al. 2016 (CVPR, multi-level context) | Not novel (but cheap and useful for the app) |
| Body / multimodal person clustering on device | Yoo et al. 2026 ("Beyond Faces", MPCA, on-device gallery clustering) | Not novel |
| Foundation models (CLIP, DINO) for face clustering | Shen et al. 2023 (CLIP-Cluster, pose/age attribute hallucination); Sony et al. 2025: domain-specific face models **outperform** zero-shot foundation models; fusion helps at low FMR | Not novel; counter-evidence for CPU gain |
| Quality-aware clustering | Pan et al. 2022 (FC-Q, quality score as input); Purohit et al. 2025 (FacePrism); MagFace 2021 (norm = quality) | Not novel (Cove already has a quality gate) |
| Rank-based similarity | Otto et al. 2016/2018 (approximate rank-order, TPAMI) | Not novel |
| Similarity → calibrated probability | Salvador et al. 2021/2022 (FairCal); Xu et al. 2022/2024 (angular scaling calibration); Neto et al. 2022 (PIC-score); Brown & Russell 2026 (Adaptive Calibration); Liu et al. 2022 (OneFace, one threshold across datasets, verification); Xie et al. 2023 (FAFF, aligning scores of several models) | Known for **verification**; see gap G1 |
| Compatible embeddings across models / upgrades | Shen et al. 2020 (BCT, CVPR); Meng et al. 2021 (LCE); McNeely-White et al. 2020/2021 (linear maps between face models); Rubab et al. 2026 | Known; see gap G2 |
| Learning the metric/threshold from must-link/cannot-link | Wang et al. 2008/2011; Baghshah & Shouraki 2009; Liu et al. 2019; Randel et al. 2021 | Known in general; see gap G3 |

**What deployed apps do.** Immich's documentation states that its clustering is DBSCAN-derived but evolves as assets arrive, so
results differ from a fresh run, and recommends resetting jobs to recluster; an open feature request (#24119) asks to recluster
without resetting other people's data (web sources, Section 8). This supports the *motivation* of Cove's corrections feature;
it is product documentation, not peer-reviewed evidence.

## 4. Gaps: combinations **not found** in the searched sources
* **G1 – Recogniser-agnostic clustering thresholds via calibration.** Calibration of face scores to probabilities exists for
  verification; we did not find it used to make one *clustering* configuration (link/attach/merge) transfer unchanged between
  face recognisers. Directly addresses a measured Cove weakness (EdgeFace-S needed a shifted grid).
* **G2 – User corrections that survive a recogniser upgrade.** Constraints in Cove are stored on faces (photo + box), not on
  embeddings, so a model swap could re-embed and keep every correction. Backward-compatible embedding work avoids re-embedding;
  we did not find work on keeping user clustering corrections across a model change.
* **G3 – Per-library threshold adaptation from the user's own corrections inside an order-invariant incremental clusterer.**
  Metric learning from constraints is classic; the specific combination was not found.
* **G4 – Our own corrections feature (exp15)** — order-invariance guarantee for both faces *and* constraints, persistence across
  re-clustering, CPU, personal libraries. The parts are prior art (Sec. 3); the combination with a proof and the persistence
  measurement was not found. The paper must cite and differentiate Halkidi 2012, He 2019, Lasek & Gryz 2019, Beauchamp 2025,
  Monath 2019 and Shi 2017, and should read them in full before the claim is final.

## 5. Devil's-advocate checkpoint 2 (synthesis): PASS with conditions
1. *Cherry-picking:* counter-evidence was searched and is reported (foundation models lose to face models; our own pose bonus
   failed in exp16). Condition: keep exp16 in the paper as a negative result.
2. *Novelty inflation:* every gap is a **combination of known parts**. They must be described as "an application not found in
   the searched sources", with expected novelty *modest*.
3. *Expected gain:* none of G1-G3 is expected to close the CPLFW gap (0.84 vs 0.91). G1/G2 remove tuning and protect user work;
   they are not accuracy improvements. The largest accuracy lever found so far remains user corrections (exp15).
4. *Read scope:* abstracts only; full texts of the G4 papers must be read before submission.

## 6. Ranked shortlist (expected gain × novelty × effort; all CPU-only, all testable with the exp14-16 protocol)

| Rank | Idea | What it fixes | Novelty | Effort | Test (tune on tuning data only, test once) |
|---|---|---|---|---|---|
| 1 | **G1 + G2 "recogniser-agnostic Cove"**: isotonic calibration of cosine → P(same person) per recogniser, fitted on AgeDB/CFP-FP *tuning* pairs; one clustering config in probability space; corrections carried across a model swap | Per-model tuning (measured weakness); losing user work on model upgrade | Modest; not found | ~1 day | Tune config on MBF only; apply unchanged to EdgeFace-S and EdgeFace-XS (cached) on the identity-disjoint test libraries + CALFW/CPLFW; report the gap to per-model tuning. Make 10 corrections with MBF, swap to EdgeFace-S, report constraints kept and F1. |
| 2 | **G3 self-tuning from corrections**: after each correction, choose this library's thresholds from a small grid by constraint satisfaction | Library-specific errors (e.g. one person often in profile) | Modest | ~1 day | exp15 protocol: F1 after k corrections, with vs. without self-tuning; overfitting check on held-back constraints |
| 3 | **Pose cue at cluster level only** (bonus applied to centroid merges between clusters with different pose profiles, never to face links) | The chaining that broke exp16 | Low-moderate; idea came *after* seeing test results — must be disclosed | ~0.5 day | Re-tune on tuning data only; CPLFW precision and recall |
| — | Same-photo cannot-link + indexing all faces per photo | Wrong merges of people photographed together | Not novel (Lo Presti 2012) | ~1 day app work | Engineering improvement; report as such |

## 7. Limitations
Abstract-level reading only; one reviewer; two scholarly indexes plus web; Scholar Gateway unavailable; product behaviour taken
from documentation, not tested. "Not found" means not found with the listed queries in these sources.

## Phase 5 review (inline)
* Editor: verdict *minor revision* — the report answers the RQ, is honest about novelty; needs full-text reading of G4 sources.
* Ethics / integrity: CLEARED. No new face data is collected; public datasets only. AI disclosure below.
* Devil's advocate checkpoint 3: strongest counter-argument — "combinations of known parts are engineering, not research".
  Answer: the paper's contribution should be framed as a *verified system property* (order invariance + persistent corrections +
  recogniser-agnostic thresholds) with measured user benefit, which is appropriate for an applied IEEE regional venue.

AI disclosure: this scan was carried out with an AI assistant (Claude) using the academic-research-skills deep-research workflow;
searches, screening and synthesis were AI-assisted and should be checked by the author.

## 8. Sources (all verified to exist via the search tools; abstract-level)
- Anguelov, D., et al. (2007). Contextual identity recognition in personal photo albums. CVPR. https://scispace.com/papers/contextual-identity-recognition-in-personal-photo-albums-5dm5rqtyo3
- Bandyopadhyay, S., & Murty, M. N. (2016). Axioms to characterize efficient incremental clustering. ICPR. https://scispace.com/papers/axioms-to-characterize-efficient-incremental-clustering-260du0ugdt
- Barr, J. R., et al. (2014). Framework for active clustering with ensembles. IEEE TIFS. https://consensus.app/papers/details/19a0d00192ef5177bb9f332cebc15b5b/
- Basu, S., et al. (2004). Active semi-supervision for pairwise constrained clustering. SDM. https://consensus.app/papers/details/4578446bcb855172a93077622b287f1e/
- Beauchamp, A. (2025). Clustering sous contraintes : intégration incrémentale et active des retours utilisateur (thesis). https://scispace.com/papers/clustering-sous-contraintes-integration-incrementale-et-fbq3vu4qtupd
- Biswas, A., & Jacobs, D. (2014). Active image clustering with pairwise constraints from humans. IJCV. https://consensus.app/papers/details/4f5dd0c430e35fc585077d4e3c165327/
- Brown, R., & Russell, C. (2026). Adaptive calibration for fair and performant facial recognition. arXiv. https://consensus.app/papers/details/fc4f9fa37dd85cbab67ce99e87450bb1/
- Chen, Y., et al. (2022). On mitigating hard clusters for face clustering. arXiv/ECCV. https://consensus.app/papers/details/b165ab1c74e9589e88c19ad16c40f38f/
- Halkidi, M., et al. (2012). A semi-supervised incremental clustering algorithm for streaming data. PAKDD. https://scispace.com/papers/a-semi-supervised-incremental-clustering-algorithm-for-4g3btc55g1
- He, P., et al. (2019). Incremental constrained random walk clustering. https://scispace.com/papers/incremental-constrained-random-walk-clustering-48vc7ee027
- Kulshreshtha, P., & Guha, T. (2018). An online algorithm for constrained face clustering in videos. ICIP. https://scispace.com/papers/an-online-algorithm-for-constrained-face-clustering-in-32v2zalfpn
- Lasek, P., & Gryz, J. (2019). Density-based clustering with constraints. ComSIS. https://scispace.com/papers/density-based-clustering-with-constraints-4g5gsfsq3c
- Li, H., et al. (2016). A multi-level contextual model for person recognition in photo albums. CVPR. https://scispace.com/papers/a-multi-level-contextual-model-for-person-recognition-in-2alczhk3jy
- Liu, J., et al. (2022). OneFace: One threshold for all. ECCV. https://scispace.com/papers/oneface-one-threshold-for-all-1pc979zd
- Lo Presti, L., et al. (2012). A data association approach to detect and organize people in personal photo collections. MTAP. https://scispace.com/papers/a-data-association-approach-to-detect-and-organize-people-in-5fslk0o72z
- McNeely-White, D. G., et al. (2021). Canonical face embeddings. arXiv. https://scispace.com/papers/canonical-face-embeddings-2irqbzl30b
- Meng, Q., et al. (2021). MagFace. CVPR. https://scispace.com/papers/magface-a-universal-representation-for-face-recognition-and-4x2lkvhayo
- Monath, N., et al. (2019). Scalable hierarchical clustering with tree grafting (Grinch). KDD. https://scispace.com/papers/scalable-hierarchical-clustering-with-tree-grafting-9xtvg1usy6
- Montero, D., et al. (2021). Efficient large-scale face clustering using an online mixture of Gaussians. arXiv. https://scispace.com/papers/efficient-large-scale-face-clustering-using-an-online-1z1z0ye0cr
- Otto, C., et al. (2016). Clustering millions of faces by identity. IEEE TPAMI. https://consensus.app/papers/details/1d2dd1dc408c52ca973b5e7cbfcf5c16/
- Pan, Z., et al. (2022). Learning to cluster faces with mixed face quality. LNCS. https://scispace.com/papers/learning-to-cluster-faces-with-mixed-face-quality-27cmg2h4
- Salvador, T., et al. (2021). FairCal: Fairness calibration for face verification. https://consensus.app/papers/details/57a9c120e17b5172ad93ec8cb553a13f/
- Shen, S., et al. (2023). CLIP-Cluster: CLIP-guided attribute hallucination for face clustering. https://scispace.com/papers/clip-cluster-clip-guided-attribute-hallucination-for-face-24f15yj4zf
- Shen, Y., et al. (2020). Towards backward-compatible representation learning. CVPR. https://scispace.com/papers/towards-backward-compatible-representation-learning-1qx8493tbq
- Shi, Y., Otto, C., & Jain, A. K. (2017). Face clustering: Representation and pairwise constraints. IEEE TIFS. https://consensus.app/papers/details/2b0d472671d55f0ab5c548a6a133b9cb/
- Song, Y., & Leung, T. (2006). Context-aided human recognition – clustering. ECCV. https://scispace.com/papers/context-aided-human-recognition-clustering-4xh8ybrogt
- Sony, R., et al. (2025). Foundation versus domain-specific models in face recognition. arXiv. https://scispace.com/papers/foundation-versus-domain-specific-models-performance-21wqlfs3p0we
- Wang, Z., et al. (2019). Linkage based face clustering via graph convolution network. CVPR. https://scispace.com/papers/linkage-based-face-clustering-via-graph-convolution-network-3zxoabwqma
- Xu, M., et al. (2024). Confidence-calibrated face and kinship verification. IEEE TIFS. https://scispace.com/papers/confidence-calibrated-face-and-kinship-verification-5eoolj8j34
- Yang, L., et al. (2020). Learning to cluster faces via confidence and connectivity estimation. CVPR. https://scispace.com/papers/learning-to-cluster-faces-via-confidence-and-connectivity-26dd1t0949
- Yoo, S.-M., et al. (2026). Beyond faces: A multimodal person clustering for unconstrained environments. https://scispace.com/papers/beyond-faces-a-multimodal-person-clustering-for-ww6wujrmwp9b
- Zhang, L., Kalashnikov, D. V., & Mehrotra, S. (2013). A unified framework for context assisted face clustering. ICMR. https://scispace.com/papers/a-unified-framework-for-context-assisted-face-clustering-43vyqsaepx
- Zhang, Y., et al. (2022). Ada-NETS. ICLR. https://scispace.com/papers/ada-nets-face-clustering-via-adaptive-neighbour-discovery-in-1ytoqyuc
- Immich documentation, Facial recognition. https://docs.immich.app/features/facial-recognition
- Immich discussion #24119, Allow reclustering of all faces of a specific person. https://github.com/immich-app/immich/discussions/24119
