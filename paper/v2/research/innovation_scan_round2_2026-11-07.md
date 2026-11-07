# Innovation scan, round 2 — other parts of Cove (deep-research, full mode, integrative scan)

Date: 2026-11-07. Same method and limits as round 1 (`innovation_scan_2026-11-07.md`): SciSpace + Consensus + web,
**abstracts only**, one reviewer, "not found" bounded to the queries listed. The author confirmed the RQ ("proceed").

## RQ (confirmed)
Beyond face clustering — photo search, video tagging, cross-media identity, on-device efficiency, evaluation methodology —
which ideas buildable and testable on a laptop CPU in ~1-3 days are **not found** in prior work, ranked by user value and
defensibility of the novelty?

## Queries
(A) training-free CLIP adaptation with a cache of labelled examples / hierarchical zero-shot labels;
(B) person identity + text-to-image search in personal photo collections;
(C) linking one person's identity across photos and videos;
(C') video face tracks as must-link supervision to link still-photo clusters across pose;
(D) thermal / battery / memory-aware background inference on laptops and phones;
(E) benchmark or protocol for personal-library face clustering with order stability and identity-disjoint splits.

## Findings by area

| Area | Prior art found (abstract level) | Verdict |
|---|---|---|
| A. Video tagger: frozen CLIP + exemplar memory from user corrections + category gating | Tip-Adapter (Zhang et al., ECCV 2022: training-free key-value cache of labelled CLIP features); Proto-Adapter 2024; SuS-X 2022/23; Dual Memory Networks 2024; cache-based test-time adaptation 2026; CHiLS (Novack et al. 2023, hierarchical label sets); Hierarchy-CLIP 2022 | **Not novel.** `TECHNICAL_REPORT.md` §6 calls this "genuinely original" — that statement must be corrected before any paper uses it. |
| B. "Person + scene" search | Faces in Places (Zhong, Arandjelović & Zisserman, BMVC 2016); Personalised CLIP / CLIP-PAD (Korbar & Zisserman); Id-CLIP / COCO-PFS (Messina et al. 2024); local gallery organizer with group-of-people search (Titov et al. 2026) | Not novel |
| C. One identity across photos and videos | Savchenko 2019 (PeerJ; photo *and video* albums); Han et al. 2018 integrated system; still-to-video face matching (Zhu et al. 2016) | Not novel as such |
| C'. Video tracks as free same-person links | Wu et al. 2013 (CVPR, ICCV), 2017; Zhou et al. 2014 (CS-VFC) and 2015; Cao et al. 2015; Somandepalli & Narayanan 2019, 2020; Tapaswi et al. 2019; Sharma et al. 2019/2020 — **all cluster faces within videos** | The use of tracks is known; using them to bridge **still-photo** clusters is a gap (G5) |
| D. Heat/battery-aware background inference | Play It Cool (Zhou et al. 2022); Phoenix 2026; ThermWear 2026; EnerInfer 2026; DualEngine 2026; Choi et al. 2024 | Not novel |
| E. Benchmark protocol | No personal-library face-clustering benchmark with order-stability and correction-survival metrics found. Related: "Goldilocks" test sets (Wu et al. 2024) show non-identity-disjoint train/test sets bias accuracy upward; FaceCluster (Filonenko, Makarov & Savchenko 2025) — local interactive photo organizer (must be cited); survey of face clustering metrics (Chen 2023); IJB-B clustering protocol (Whitelam et al. 2017) | Gap (G6), modest but cheap — the protocol already exists in our code |

## Gaps not found in the searched sources
* **G5 — Video tracks as pose bridges for photo clusters.** In a mixed personal library, a person's video track shows the same
  face turning frontal → profile; faces of one track are automatic must-links (true by construction of tracking). Feeding
  them into Cove's constrained, order-invariant clusterer could join that person's frontal and profile *photo* clusters — the
  measured weakness (CPLFW F1 0.84 vs 0.91). Every track-constraint paper found clusters faces **inside videos** only.
* **G6 — A personal-library clustering benchmark**: identity-disjoint tuning/test libraries, 7 image conditions, look-alike
  libraries, order-agreement metric, correction-survival metric (exp14/exp15). Not found as a released benchmark.

## Devil's-advocate checkpoint 2: PASS with conditions
1. G5 is a new *use* of a known signal; claim it as "not found in the searched sources".
2. G5 needs data with the same people in photos and videos. YouTube Faces (3,425 videos, 1,595 people, LFW-style names;
   aligned frames ~5.4 GB, Tel Aviv University page) is the natural source; identity overlap with LFW/CPLFW must be
   **verified from the data**, not assumed.
3. Risk: video frames are near-frontal low-quality frames; if YouTube Faces tracks rarely reach profile, the bridge effect is
   small. This must be measured (yaw spread per track from pose_kps), not hoped for.
4. Risk of chaining (the exp16 lesson): a single wrong track would merge people; track faces are reliable only if tracks are
   correct. Use only within-video, single-face tracks, and report precision separately.
5. G6 is a contribution of method, not of algorithm; frame it as such.

## Ranked shortlist
| Rank | Idea | User value | Novelty | Effort | Test (pre-declared, tuning data only for any choice) |
|---|---|---|---|---|---|
| 1 | **G5 video tracks bridge photo clusters** | Fixes the main accuracy weakness for people with videos | Not found; modest-to-good | 2-3 days (download + embed sampled frames) | Libraries of LFW + CPLFW photos plus YTF videos of the overlapping test-half identities; F1 / precision / recall with vs. without track must-links, by pose gap; tracks sampled at k = 5 frames per video; identity-disjoint as exp14 |
| 2 | **G6 release the benchmark** (scripts + splits + metrics) | Reproducibility; reviewers asked for it | Not found; modest | 0.5-1 day (packaging) | n/a (documentation + released config) |
| 3 | Round-1 G1/G2 (recogniser-agnostic thresholds; corrections survive model swap) | Removes per-model tuning | Not found; modest | ~1 day | as in round 1 |

## Correction required in the project documents
`TECHNICAL_REPORT.md` §6 and §10.4 claim the video classifier's hierarchical gating + exemplar memory is "genuinely original".
Prior art: Tip-Adapter (2022) for the training-free exemplar cache; CHiLS (2023) / Hierarchy-CLIP (2022) for hierarchical
zero-shot labels. Recommended wording: "an application of training-free cache-based CLIP adaptation (Tip-Adapter) with
hierarchical label gating (cf. CHiLS) to personal-video tagging".

## Phase 5 (inline)
Editor: minor revision (needs the data-feasibility check for G5 before committing). Ethics: CLEARED — public research
datasets only; YouTube Faces licence terms must be checked before use. DA checkpoint 3: strongest counter-argument —
"YTF frames are low quality, so bridges may add errors"; answer: measure precision separately and keep track-faces out of
the reported photo F1.

AI disclosure: AI-assisted search, screening and synthesis (Claude, academic-research-skills deep-research); the author
should verify sources.

## Sources (abstract level; verified to exist via the search tools)
- Cao, X., et al. (2015). Constrained multi-view video face clustering. IEEE TIP. https://consensus.app/papers/details/035b6ad9cc355545962b3f9a666c940e/
- Chen, J. (2023). Survey of evaluation methods and metrics for face clustering. https://scispace.com/papers/survey-of-evaluation-methods-and-metrics-for-face-clustering-4pcjzzhtao
- Choi, P., et al. (2024). Impact of joint heat and memory constraints of mobile device in edge-assisted on-device AI. https://scispace.com/papers/impact-of-joint-heat-and-memory-constraints-of-mobile-device-12phf19ofe
- Filonenko, A., Makarov, I., & Savchenko, A. V. (2025). FaceCluster: Interactive photo organization with enhanced face recognition. https://scispace.com/papers/facecluster-interactive-photo-organization-with-enhanced-h0wld6u3yfpf
- Korbar, B., & Zisserman, A. Personalised CLIP or: how to find your vacation videos. BMVC. https://scispace.com/papers/personalised-clip-or-how-to-find-your-vacation-videos-1da2z1l2
- Messina, N., et al. (2024). Towards identity-aware cross-modal retrieval: a dataset and a baseline. https://scispace.com/papers/towards-identity-aware-cross-modal-retrieval-a-dataset-and-a-2408ffmelgcm
- Novack, Z., et al. (2023). CHiLS: Zero-shot image classification with hierarchical label sets. https://scispace.com/papers/chils-zero-shot-image-classification-with-hierarchical-label-2avzsxqh
- Savchenko, A. V. (2019). Efficient facial representations for age, gender and identity recognition in organizing photo albums using multi-output ConvNet. PeerJ CS. https://scispace.com/papers/efficient-facial-representations-for-age-gender-and-identity-o649stlba0
- Sharma, V., et al. (2019). Self-supervised learning of face representations for video face clustering. FG. https://scispace.com/papers/self-supervised-learning-of-face-representations-for-video-2y5md4doft
- Somandepalli, K., & Narayanan, S. (2019). Reinforcing self-expressive representation with constraint propagation for face clustering in movies. ICASSP. https://scispace.com/papers/reinforcing-self-expressive-representation-with-constraint-tpwwe3jhmy
- Tapaswi, M., et al. (2019). Video face clustering with unknown number of clusters. ICCV. https://consensus.app/papers/details/b788cb408da3588e9a5474b945c39bf8/
- Whitelam, C., et al. (2017). IARPA Janus Benchmark-B face dataset. CVPRW. https://scispace.com/papers/iarpa-janus-benchmark-b-face-dataset-24tnrtzgig
- Wu, B., et al. (2013). Constrained clustering and its application to face clustering in videos. CVPR. https://scispace.com/papers/constrained-clustering-and-its-application-to-face-2ru7l7tgl3
- Wu, H., et al. (2024). What is a Goldilocks face verification test set? https://scispace.com/papers/what-is-a-goldilocks-face-verification-test-set-1oeufq0eew
- Zhang, R., et al. (2022). Tip-Adapter: Training-free adaption of CLIP for few-shot classification. ECCV. https://scispace.com/papers/tip-adapter-training-free-adaption-of-clip-for-few-shot-142sl0zg
- Zhong, Y., Arandjelović, R., & Zisserman, A. (2016). Faces in places: Compound query retrieval. BMVC. https://scispace.com/papers/faces-in-places-compound-query-retrieval-1n4elcp9wc
- Zhou, C., et al. (2014). Video face clustering via constrained sparse representation. ICME. https://scispace.com/papers/video-face-clustering-via-constrained-sparse-representation-465v74tg3y
- Zhou, Y., et al. (2022). Play it cool: Dynamic shifting prevents thermal throttling. https://scispace.com/papers/play-it-cool-dynamic-shifting-prevents-thermal-throttling-2zjpdyf6
- YouTube Faces DB project page. https://www.cs.tau.ac.il/~wolf/ytfaces/
