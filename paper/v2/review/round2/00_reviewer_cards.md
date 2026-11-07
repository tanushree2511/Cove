# Simulated peer review, round 2: reviewer cards (awaiting confirmation)

- **Manuscript:** `paper/v2/cove_paper.tex`, the rewrite from commit ce1b15d. Title: "Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries".
- **Mode:** full review, with five role-separated seats and an editorial synthesis.
- **Target:** an IEEE regional or national computing conference in India.

The cards keep the round-1 identities, so the same yardstick is applied. The focus of each card is updated to the new headline claim: user corrections that persist, plus order invariance.

| Seat | Identity and focus |
|---|---|
| Journal-Fit Reviewer | Programme-committee member of an IEEE India regional computing conference. Checks that the paper fits the venue, that the novelty is stated at the right size now that constrained clustering is cited as prior work, that it fits the page limit, and that the AI-use disclosure is acceptable. |
| Reviewer 1 (Methodology) | Clustering-evaluation researcher. Checks the identity-disjoint split, the equal tuning grids, and the paired bootstrap. Checks the corrections protocol (80/20 "now/later", up to 10 simulated fixes taken from the biggest mistakes), including whether a simulated oracle user overstates the gains. Checks the update-time measurement and whether any test data leak into decisions. |
| Reviewer 2 (Domain) | Face-recognition and constrained-clustering researcher (COP-KMeans, constrained agglomerative clustering, interactive photo-album systems such as EasyAlbum). Checks whether the must-link/cannot-link method is distinct from prior work, whether the baselines are adequate (Immich-style DBSCAN, Chinese Whispers, a constrained re-clustering baseline), and whether the recogniser protocol is fair. |
| Reviewer 3 (Perspective) | Local-first and privacy software engineer. Checks the practical value for real family albums. Checks the gap between the paper and the app: corrections are not yet persisted, names are overwritten, and CORS accepts any origin. Checks the CPU and latency budget and whether the paper's statements about the product are honest. |
| Devil's Advocate (fixed) | Challenges the new headline. The "100% vs 27% of fixes kept" result may hold by construction: hard constraints are always satisfied, so a baseline that throws them away is a strawman. Also challenges whether the paper, now that the accuracy advantage is gone, still makes a contribution worth publishing. |
