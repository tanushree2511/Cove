# Paper Configuration Record (academic-paper skill, Phase 0)

The author was unavailable ("I'm going to sleep, don't ask any questions, do whatever is best"), so every intake
decision below was made autonomously and is recorded here so it can be changed later.

| Field | Decision | Why |
|---|---|---|
| Mode | `revision` of the paper rejected at ICSSES 2026 (paper ID 251), executed as a full rewrite | The reviewers asked for new experiments and a sharper contribution, not wording fixes |
| Paper type | Empirical conference paper (IMRaD, IEEE conference layout) | Target venues are IEEE-indexed national/regional conferences in India |
| Discipline | Computer vision / multimedia systems | |
| Target venue | Generic IEEE conference (IEEEtran `conference` class, 6 pages + references) | No specific venue chosen yet; fits most IEEE conference page limits |
| Citation format | IEEE numeric | Required by IEEE conferences |
| Output format | LaTeX (`cove_paper.tex` + `references.bib` + `figs/`), compile on Overleaf | No LaTeX compiler could be installed on this machine |
| Language | English | |
| Abstract | English only (one abstract, about 200 words) | IEEE conferences require one English abstract; a zh-TW abstract (the skill default) would be out of place |
| Length | ~6 pages | Typical IEEE conference limit |
| Scope change | The paper is now about **order-stable incremental face clustering** inside Cove. The video-keyframe part is dropped | Reviewer 1's strongest criticisms were (a) limited novelty, (b) input-order sensitivity of First-Leader, (c) missing threshold analysis and controlled baselines. The clustering problem answers all three with real experiments; the video part would need new face-recall/retrieval experiments to be defensible and is left for a separate paper |
| Authors | Names must be filled in by the author (see `% AUTHORS` block). No template placeholders are left as fake names | Reviewer 1: "Remove unused author-template placeholders" |
| Literature | Narrative review of face clustering, incremental/online clustering, lightweight face recognition, local-first photo managers; every reference verified by web search (DOI / proceedings page) | Skill IRON RULE: no unverified citations |
| Style calibration | Skipped (no past papers by the author supplied) | |
| AI disclosure | Included (AI assistant used for code, experiments and drafting; all numbers come from the released scripts) | Skill mandatory inclusion; most IEEE conferences now ask for it |

## How each reviewer comment is answered

| Reviewer comment | Where answered |
|---|---|
| R1: limited novelty (combination of existing parts) | New algorithm: order-invariant incremental clusterer with a proof of order invariance (Sec. III), plus first measurement of order sensitivity in personal libraries (Sec. V-A) |
| R1: thresholds, selection procedure, checkpoints, processing order not reported | Sec. IV: every threshold, the tuning/test split, model files (buffalo_s `det_500m` + `w600k_mbf`, EdgeFace-S), shuffled orders, code paths |
| R1: input-order sensitivity of First-Leader; repeated-order experiments; identical embeddings | Sec. V-A: 20 shuffled orders x 30 libraries + full LFW, all methods on identical embeddings |
| R1/R4: threshold-sensitivity analysis | Sec. IV and V-C: 72- and 96-configuration grids on tuning data; Sec. V-D / Table III: same grid shifted for EdgeFace-S |
| R4: image quality, pose, lighting | Sec. V-B: low resolution, blur, JPEG, dark+noise, occlusion, mixed; Sec. V-C: CALFW (age), CPLFW (pose) |
| R4: compare with strong modern clustering baselines | Average-linkage agglomerative (batch, order-free reference), two-stage leader+merge, First-Leader; GCN methods discussed as supervised and not local-first-friendly (Sec. II) |
| R1: stage-level runtimes, repeated measurements | Sec. V-E: update time vs library size; recogniser latency (1 thread / all cores) |
| R1: comparison with existing local media systems | Sec. II (Immich, PhotoPrism) |
| R4: formal privacy analysis missing | Sec. VI: threat-model paragraph and limitation (no formal analysis claimed) |
| R1: video claims (frame reduction, end-to-end speed-up) | Removed from this paper; stated as future work |

## Decision log: EdgeFace-S adoption (2026-11-06, autonomous; author asleep and asked for no questions)

1. Screening (6,000 pairs per set, 10-fold): EdgeFace-S never significantly worse than w600k_mbf, about 2x faster. GhostFaceNet rejected (worse on pose and slower); EdgeFace-XS rejected (no accuracy gain).
2. Full clustering test with the original grid: EdgeFace-S worse on degraded photos (occluded F1 0.650). Cause: its cosine scale is ~0.10 higher (random-pair 99th percentile on AgeDB/CFP-FP *tuning* pairs 0.27-0.31 vs 0.19-0.21). Kept as `results/*_edgeface_s_noshift.json`.
3. Re-tuned on the same grid shifted by +0.10 (`COVE_GRID_SHIFT=0.10`, tuning data only), library-ARI rule: link 0.60, m 1, attach 0.50, merge 0.55.
4. Held-out: CPLFW 0.783 -> 0.854, CALFW 0.934 -> 0.949, all degraded conditions within +-0.4 points. Adopted as the default (`cove/config/face_clustering.py`).
5. The formal simulated peer review (academic-paper-reviewer) was NOT run, because its reviewer cards need the author's confirmation first. The cards are in `review_cards_pending.md`.
