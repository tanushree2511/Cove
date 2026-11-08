# Revision log, after the round-2 review (2026-11-08)

Responds to `review/round2/EDITORIAL_DECISION.md`. Every number below was checked against the result JSONs. The paper
has not been compiled, because there is no LaTeX on this machine.

## New experiments and code
- **exp19** (`evaluation/exp19_correction_baselines.py`, results in `exp19_correction_baselines_{edgeface_s,mbf}.json`)
  - Compares four ways of keeping corrections: ours, re-apply after our clusterer, re-apply after average linkage, and
    constrained average linkage. Each method gets its own user session.
  - Uses three simulated users: precise (exp15's oracle), casual (random faces), and error-prone (casual plus 10%
    wrong look-alike "same person").
  - Pools the hold rate over corrections and reports F1 on new faces only.
  - Our method with the precise user reproduces exp15 exactly: later F1 0.9925, lost 0.9854, held 20.3%.
- **exp19b** (`exp19b_frozen_baseline.py`): an Immich-style frozen rule, with the threshold at Immich's default of 0.5.
- **exp18b** (`exp18b_constrained_time.py`): reading the groups on 8,290 faces takes 3.8 s with 0 corrections, 4.3 s
  with 1, 5.1 s with 10, and 5.05 s with 50.
- **Recogniser speed** (`exp13_speed_all4.json`):
  - all four models re-timed, two runs each;
  - the old Table III numbers could not be traced to any file;
  - EdgeFace-S is 1.97× faster than MBF with one thread and 1.96× with all cores.
- **Clusterer fix** (`cove/engines/stable_cluster.py`):
  - must-links are now applied in order of decreasing similarity, not face id, so contradictory corrections are
    resolved independently of insertion order (DA m1);
  - a new test fails on the old code and passes on the new;
  - all 13 clusterer tests pass;
  - this has no effect on the exp15 results, because the oracle user never contradicts itself.

## Consensus issues
| # | Issue | Status |
|---|---|---|
| 1 | No fair baseline (C1) | **Fixed.** Constrained average linkage, two re-apply variants and the frozen rule are added (Table II rewritten). The text says that 100% holds by construction. Result: constrained average linkage and frozen match our F1. Re-apply loses with the casual user. |
| 2 | Hold-rate and count statistics | **Fixed.** 20% pooled (MBF 17%); "up to ten (5.4 on average)"; 207/240 libraries received corrections. |
| 3 | Perfect oracle user | **Fixed.** Casual and error-prone users added. New negative result: wrong corrections are sticky, and ours falls to the no-correction F1. |
| 4 | Missing prior art | **Fixed.** C-DBSCAN, C-DenStream, Lasek & Gryz 2019, Grinch (KDD 2019), ConPaC (Shi et al. 2018) and Wu et al. 2013 added and contrasted. Bibliographic details were web-verified; ConPaC's volume and pages are omitted because they were not confirmed. |
| 5 | Title vs app | **Text only.** Limitation (vii) now states exactly what the app lacks (no correction UI, re-clusters from scratch, overwrites names). The title is unchanged; **the author must decide** whether to retitle or to wire the feature into the app. |
| 6 | Corrections path not timed | **Fixed.** exp18b, Sec. V-F. With corrections, an update costs about as much as re-clustering from scratch, and the paper says so. |
| 7 | Number problems | **Fixed.** Table III re-measured; abstract 0.56; MBF occluded result stated (−0.026 vs average linkage). |

## Single-seat items
- **R1, CIs too narrow:** added as limitation (iv). No identity-level bootstrap was run.
- **DA m1, contradictions:** fixed in the code, and the proof sketch is updated.
- **R3:**
  - Privacy paragraph now states no API key, any origin, and that the Docker port is reachable on the LAN (verified: `"8000:8000"`).
  - Consent sentence added.
  - The product bugs are reported and not fixed.
- **R2:**
  - EdgeFace licence corrected to CC BY-NC-SA 4.0;
  - "up to border points" added for incremental DBSCAN.
- **EIC:** the AI statement is moved to an Acknowledgment section, per IEEE policy, and rewritten to describe the AI's
  role accurately.

## Still for the authors
1. Names, college, emails, guide, and the Author Contributions line.
2. **Actually check the numbers.** The Acknowledgment now states that the authors did.
3. Decide on the title vs the app (issue 5).
4. Compile on Overleaf and check the page count. The paper grew, so it may be over 6 pages.
5. Plagiarism check, and the conference's own AI policy.
