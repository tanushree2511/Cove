# Simulated peer review, round 3: field analysis and reviewer cards (awaiting confirmation)

**Manuscript:** `paper/v2/cove_paper.tex` (commit ef69690), "Face Grouping That Keeps the User's Corrections:
Order-Invariant Incremental Clustering for Local-First Photo Libraries".
**Mode:** full (simplified run, as in rounds 1–2). There are five role-separated seats; each one also checks whether
the round-2 issues are really fixed (`review/round2/EDITORIAL_DECISION.md` against `REVISION_LOG_round3.md`).

## Field analysis

| Dimension | Result |
|---|---|
| Length | Abstract 248 words; about 4,200 words of text; 3 tables; 38 references; estimated about 6.5 IEEE pages (not compiled) |
| Primary discipline | Computer vision / pattern recognition (face clustering) |
| Secondary disciplines | Data mining (constrained and incremental clustering); HCI (interactive correction); systems (local-first software) |
| Paradigm / method | Empirical: an algorithm, a proof sketch, and a simulation-based evaluation on public face datasets |
| Target venue | IEEE regional or national computing conference in India (6-page limit) |
| Maturity | Third revised draft, before submission |

## Cards

| Seat | Identity and focus |
|---|---|
| Journal-Fit Reviewer | Programme-committee member of an IEEE India regional computing conference. Checks whether a contribution remains after the fair baselines: the method now equals constrained average linkage and an Immich-style rule in accuracy. Checks whether the claims are sized right, whether the paper fits 6 pages, and whether the Acknowledgment-section AI disclosure is acceptable. |
| Reviewer 1 (Methodology) | Clustering-evaluation researcher. Checks exp19: each method gets its own user session; the three simulated users, especially the definition of the error-prone user; pooled hold rates; bootstrap independence. Checks the constrained-average-linkage implementation, and whether the Immich-style threshold, untuned for MBF, is fair. Checks consistency between the 4-decimal table and the text, and that every number matches the JSONs. |
| Reviewer 2 (Domain) | Face-clustering and constrained-clustering researcher. Checks whether the new related work (C-DBSCAN, C-DenStream, Lasek & Gryz, Grinch, ConPaC, Wu et al.) is described correctly. Checks whether "what we add is the order-invariance guarantee" holds against that work. Looks for literature still missing on noisy or erroneous constraints. Checks the baseline naming ("Davidson & Ravi 2005"). |
| Reviewer 3 (Perspective) | Local-first and privacy software engineer. Checks the gap between the paper and the app (no correction UI, from-scratch re-clustering, names overwritten). Checks what "wrong corrections are sticky" means for the UI, whether F1 differences of 0.001 matter to users, the privacy and consent text, and the CPU budget. |
| Devil's Advocate (fixed) | Challenges the paper's reason to exist now. Accuracy equals constrained average linkage and Immich-style freezing. The cost advantage over constrained average linkage was never measured directly, only against plain average linkage. The win over "re-apply" depends on a simulated "casual" user. Order invariance matters little if freezing already reaches 0.995 agreement. Asks what a reader learns that is not obvious. |
