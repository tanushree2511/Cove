# Editorial Decision — simulated review, round 1

**Manuscript:** "Order-Stable Incremental Face Clustering for Local-First Personal Photo Libraries" (`paper/v2/cove_paper.tex`, 2026-11-06)
**Decision: MAJOR REVISION**. All five seats independently recommended Major Revision, each with confidence 4/5.

**Panel provenance:**
- Five role-separated seats ran as separate subagents of the same model family (Claude Opus 5.5). None saw another seat's report before committing its own.
- Same-family seats can share blind spots, so the agreement below is not evidence of independent errors.
- The skill's sprint-contract scripts, provenance scripts and attachment scripts were **not** run. This is a simplified run of the full mode.

Reports:
- `R_EIC.md`: Journal-Fit Reviewer
- `R1_methodology.md`: Reviewer 1, methodology
- `R2_domain.md`: Reviewer 2, domain
- `R3_perspective.md`: Reviewer 3, perspective
- `R_DA.md`: Devil's Advocate

## What the panel agrees is sound
- The order-invariance property and its proof sketch. R3 checked them against the code, and R1 and the DA checked them against the results.
- The reported numbers match the released result JSON files (R1, DA).
- The failure modes and negative results are reported openly (EIC, DA).
- The topic fits an applied IEEE regional venue (EIC).

## Devil's Advocate CRITICAL issue: adjudication
**C1. "The pose and age failures come from the embedding" contradicts Table I.**
- On the same MBF embeddings, agglomerative clustering scores CPLFW 0.881 and First-Leader 0.857, against 0.783 for ours.
- R1 and R2 raised the same point.
- **Validated.** The similarity analysis (Fig. 2) shows that the faces our method splits are weakly similar. It does not show that no clustering method could recover them: average linkage over all pairs does.
- The EdgeFace-S gain shows the embedding is *part* of the cause, not all of it.
- Blocks acceptance until the claim is reworded, both in the abstract and in contribution 4.

## Consensus issues (raised by 2 or more seats), ordered by severity

| # | Issue | Seats | Verified by editor | Required change |
|---|---|---|---|---|
| 1 | **Tuning and test libraries share identities.** Both seeds sample "family" people from the same 158 LFW identities: 157/158 test people and about 76% of test photos also appear in the tuning libraries. "Held-out" is therefore not true for Tables I and III. | R1 (measured), DA M4; the paper itself admits partial overlap | **Yes.** `make_libraries` samples both seeds from the same `rich` pool, and the docstring saying "disjoint" is wrong. | Split identities before sampling: tuning people and test people disjoint, strangers disjoint too. Re-tune and re-test every method. |
| 2 | **Baselines tuned on unequal terms.** Ours searched 72–330 configurations on degraded tuning data, while the baselines got one threshold tuned on clean data, or none. MBF got no shifted or wide grid while EdgeFace did. | R1, DA M1/M3 | Yes, for the EdgeFace/MBF asymmetry; a wide grid for both models is now running. | Give every method the same tuning budget on the same tuning data. Report an ablation separating "re-tuning" from "attach threshold". |
| 3 | **Novelty overstated at the shipped m=1.** Every face with any neighbour is core, so the method reduces to single-linkage components plus attachment plus a centroid merge, and the "non-core faces cannot chain people" safeguard is mostly empty. | EIC W1, R2, DA M6 | Yes (m=1 in every shipped config). | Present the method as a verified adaptation of known parts. Add single linkage as a baseline. Report m≥2 results or explain why m=1 wins. |
| 4 | **Embedding-blame claim** (C1 above) | R1, R2, DA | Yes | Reword, and add agglomerative clustering on EdgeFace-S. |
| 5 | **Update-time claim weak.** Measured with an old configuration; incremental time grows with library size and only wins at 13k faces. The shipped app calls `fit_predict` on all faces on every pass, so it is not incremental in practice. | EIC W2, R3 W1/W3, DA M5 | Yes (`server.py` `_run_clustering_stage`) | Re-measure with the shipped thresholds and a per-step breakdown, and soften the claim. Either persist the clusterer state in the app or say plainly that the app re-runs the (order-invariant) clustering. |
| 6 | **Missing baselines.** DBSCAN/HDBSCAN, Immich's DBSCAN-derived incremental method, Chinese Whispers, and the reason given for skipping OGMC. | EIC W3, R2 | n/a | Add DBSCAN/HDBSCAN (and an Immich-style re-implementation if feasible) to Table I on identical embeddings. |
| 7 | **Recogniser comparison not on official protocols.** CALFW/CPLFW pairs are built from random identities rather than the official hard-negative pair lists; "published comparisons overstate the gap" is unsupported. | R2 | Yes (`exp13_screen.py`) | Use the official pair lists, or rename the protocol and delete that sentence. |
| 8 | **Mislabelled control in Table III.** The third column is EdgeFace-S tuned on the unshifted grid (attach 0.40), not "MBF's thresholds" (attach 0.35). | DA M2 | Yes | Relabel the column, or run the true MBF-threshold control. |
| 9 | **"2× faster" holds single-threaded only**: 1.67× with all cores. | EIC, DA m2 | Yes | State both numbers. |
| 10 | **Test sets used for decisions.** CALFW/CPLFW informed the recogniser screen, the rejection of rule (a), and the choice of rule (b). | R1 | Yes | Make every decision on tuning data and pre-declare the selection rule. |

## Single-seat findings to address (Minor unless noted)
- **R3 (Major, product):** re-clustering overwrites user-assigned names (`PersonManager.save_people(overwrite=True)`), and there is no way to split a wrong merge. This is the harm the introduction claims to prevent.
- **R3 (Major, product/privacy):**
  - the local API allows any origin (`allow_origins=["*"]`) with no API key by default, which undercuts the "nothing leaves the device" claim;
  - only the largest face per photo is indexed, in the product as well as the experiments.
- **R1:**
  - no confidence intervals or paired tests for clustering;
  - the zero order spread in Table I is true by construction (one order);
  - the shipped thresholds never went through the 20-order test;
  - B-Cubed precision and recall not reported;
  - CALFW/CPLFW are LFW identities, so they are not "fully separate".
- **R2:**
  - possible identity overlap between LFW and the WebFace training data;
  - no IJB-B, PIPA or FIW data;
  - licence wording: the EdgeFace code is BSD-3 but its weights are non-commercial, and buffalo_s is non-commercial too;
  - 10 suggested references; check them before citing.
- **R3:**
  - CPU cost reported for embedding only, not end to end;
  - no hash check on the downloaded ONNX model;
  - 3 suggested references, written from memory and unverified.
- **EIC:** placeholders in the author blocks; "a reviewer of that version" wording in the intro; the method history is inconsistent between Sec. I and Sec. IV.
- **DA:** the look-alike test was not re-run with EdgeFace-S; temporal stability shown only with an old configuration; the user-need premise (stability as the library grows vs. invariance under arbitrary shuffles) is unmeasured.

## Revision roadmap (suggested order)
1. **Identity-disjoint tuning/test split.** Re-run tuning and testing for all methods (fixes issue 1, and with equal budgets issue 2). Every other number depends on this, so it comes first.
2. **Equal-budget baseline tuning, plus new baselines:** single linkage, DBSCAN/HDBSCAN (issues 2, 3, 6), and agglomerative on EdgeFace-S (issue 4).
3. **Re-measure update time** with the shipped thresholds (issue 5), and decide the app question: persist the clusterer state, or describe the app honestly.
4. **Official CALFW/CPLFW pair lists** for the recogniser table (issue 7). Relabel the Table III control and state 1.67× with all cores (issues 8, 9).
5. **Rewrite the claims:** novelty framing, embedding blame, "held-out" and "realistic" wording.
6. **Product fixes, reported here and not applied** (the author decides): name preservation across re-clustering, CORS/API key, model hash check.

These are the panel's issues, kept in the reviewers' own terms. Which ones to address is the author's decision.
