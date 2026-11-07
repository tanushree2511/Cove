# Revision log, round 2 (2026-11-07)

**Paper:** `paper/v2/cove_paper.tex`, rewritten. The round-1 version is kept as `paper/v2/cove_paper_v2_round1.tex`.

**New title:** "Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries".

**Process note (honest):**
- This is a full rewrite approved by the author ("yes start the rewrite"). The headline changed to the corrections result, which the author agreed to.
- The academic-paper skill's revision-mode patch scripts (anchorize, patch, apply) were **not** run, because they target Markdown drafts.
- Every number in the paper was checked by hand against the result JSONs listed below.
- The paper could not be compiled here, because there is no LaTeX on this machine. Compile it on Overleaf and check the page count.

## Responses to the round-1 editorial roadmap (`EDITORIAL_DECISION.md`)

| # | Issue | Status | Where / how |
|---|---|---|---|
| C1 | "Pose/age failures come from the embedding" contradicted Table I | **Fixed** | The claim is removed. Sec. V-B now says the CPLFW gap "lies in the clustering rule as well as in the embedding", with numbers: ours P 0.985 / R 0.733 vs average linkage P 0.912 / R 0.906. The similarity-split figure is dropped. |
| 1 | Tuning and test libraries shared identities | **Fixed** | exp14: an identity-disjoint split (seed 2026, 79 family + 1,844 strangers per half, overlap 0). CALFW/CPLFW and look-alike libraries are restricted to test-half people. |
| 2 | Baselines tuned on unequal terms | **Fixed** | exp14: every method gets a grid over the same range (0.20–0.70), the same tuning libraries and the same rule. Grid sizes are stated. The "Ours, no attach" ablation is in Table I. |
| 3 | Novelty overstated at m = 1 | **Fixed** | Sec. III states that at m = 1 the method is single linkage + attach + centroid merge, "an adaptation of known parts". Single linkage is now a baseline. |
| 4 | Embedding-blame claim | **Fixed** | See C1. Average linkage is reported on EdgeFace-S (Table I). |
| 5 | Update-time claim weak | **Fixed** | exp18: re-measured with the shipped EdgeFace-S thresholds and a per-step breakdown. The result is 3.5 s vs 4.7 s for re-running our own clusterer, only 1.3×, stated plainly as "cheap but not constant-time". The paper also says the app does not yet persist corrections. |
| 6 | Missing baselines | **Mostly fixed** | DBSCAN, HDBSCAN and single linkage are added. An Immich re-implementation and Chinese Whispers are **not** added. |
| 7 | Recogniser comparison not on official protocols | **Fixed (renamed)** | Sec. V-E says the pairs are drawn at random, not the official lists. The "published comparisons overstate" sentence is deleted. |
| 8 | Mislabelled control in Table III | **Fixed (table removed)** | The old Table III is replaced by exp14, which tunes both recognisers on equal terms. |
| 9 | "2× faster" holds single-threaded only | **Fixed** | "2.1× faster with one thread; 1.67× with all cores". |
| 10 | Test sets used for decisions | **Fixed** | The recogniser is chosen by a pre-declared tuning rule (ARI 0.9822 vs 0.9826). Pose decisions use tuning data and CFP-FP only. |

**Single-seat findings:**
- **R3, name overwrite and splitting wrong merges:**
  - the clusterer now supports cannot-link, so a wrong merge can be split;
  - the app wiring is still missing, and the paper says so (limitation vi);
  - the product bug is reported only, not fixed.
- **R3, CORS:** reported in the Privacy paragraph ("currently accepts any origin"). Not fixed.
- **R3, largest face only:** stated as limitation (iii).
- **R1:**
  - confidence intervals: added, as paired bootstrap;
  - order spread: ours is now run in 3 orders on the test data;
  - B-Cubed P/R: given for CALFW/CPLFW in the text;
  - CALFW/CPLFW described as LFW identities restricted to the test half.
- **R2:**
  - licence wording kept;
  - IJB-B, PIPA and FIW are not added (the limitation names real family albums as untested).
- **EIC:**
  - the "reviewer of that version" wording is removed;
  - the method history is consistent;
  - the author placeholders **remain** and must be filled in by the authors.
- **DA:**
  - look-alike is re-run with EdgeFace-S (exp14);
  - temporal stability is re-measured (exp18, ARI ≥ 0.998).

## New content

| Section | Content | Source |
|---|---|---|
| III-C, Prop. 1 | User corrections (must-link / cannot-link) and an order-invariance argument that includes them | `cove/engines/stable_cluster.py` (`_labels_constrained`) |
| V-C, Table II | Corrections: F1 0.984 → 0.994; 100% vs 27% of corrections still hold | `evaluation/results/exp15_corrections_{edgeface_s,mbf}.json` |
| V-D | Negative result: pose-aware similarity | `exp16_pose_{edgeface_s,mbf}.json` |
| V-F | Update time | `exp18_update_time_edgeface_s.json`, `evaluation/exp18_update_time.py` |
| VI, future work | Simulated video-track bridge | `exp17b_track_bridge_hard_edgeface_s.json` |
| II | Prior art from the novelty scans (Wagstaff 2001, Davidson & Ravi 2005, Davidson et al. 2007, Daniels 2006, Van Craenendonck 2017, Tian 2007, EasyAlbum 2007, Song & Leung 2006, FaceCluster 2025, HDBSCAN 2013) | `paper/v2/research/innovation_scan_*.md` |

## Still for the authors before submission
1. Fill in the author names, college, city and emails. Add your guide if your college requires it.
2. Add DOIs to the new references from the publisher pages. They were left out where they could not be confirmed.
3. Compile on Overleaf, check the page limit of the chosen conference, and check that Table I (two columns wide) sits well.
4. Complete the Author Contributions line. Run the college plagiarism check.
5. Check the conference's own AI-use policy and adjust the Declarations wording if needed.
