# Round 3 Editorial Decision (simulated review)

All five seats reported: EIC, R1 Methodology, R2 Domain, R3 Perspective, Devil's Advocate.
These are simulated reviewers (model output), not real peer review.

## Decision: Minor Revision (borderline Major on claim sizing)

| Seat | Recommendation | Confidence |
|---|---|---|
| EIC | Minor, borderline Major | 4 |
| R1 Methodology | Minor | 4 |
| R2 Domain | Minor | 4 |
| R3 Perspective | Major | 4 |
| Devil's Advocate | No Critical, 7 Major | - |

## Consensus issues (raised by 3 or more seats)

1. **Claim size.** Accuracy ties constrained average linkage and the Immich-style frozen rule.
   - R1: on new faces only, constrained average linkage beats us for all three users and both recognisers (EdgeFace-S precise 0.9920 vs 0.9906). The paper reports only all-face F1.
   - DA: against the error-prone user, ours is 0.0042 below re-apply and 0.0027 below constrained average linkage (CIs exclude zero).
   - Fix: say "ties" and show the new-face numbers. Do not say "matches" without them.
2. **Cost claim is unmeasured.** The 5.1 s vs 16.7 s comparison is against plain average linkage, not constrained average linkage (EIC, DA, R1 partly). This is the main place the method could genuinely win, so it must be measured (novelty plan E1).
3. **Order invariance** is a free property of any deterministic batch method. It is distinctive only against the authors' own leader code (DA, R2).
4. **App gap.** Corrections are not wired into the app, are keyed by face index, and the Docker ports and API are open (R3; verified by me earlier).

## Editor-verified items
- Table II row endings (`\` vs `\\`): real, fixed in 5abb6fd.
- Non-core must-link merging two clusters: reproduced (1 vs 2 clusters over 20 orders). Now disclosed in the Method.
- Docker ports 8000/8001/8080 published; CORS `*`; API key optional and unused by the front end. Paper text corrected.
- Cost gap: confirmed by reading exp18/18b/19. Constrained average linkage is never timed.

## Reviewer-reported, not yet verified by me
- R1: `c_avg` undoes a rejected must-link incorrectly (union-find path compression survives the revert). Effect reported as small (held rate 97.75% to 98.88%, F1 barely moved).
- R1: bootstrap resamples 240 library-condition pairs, but the text says libraries.
- R1 number mismatches: run-to-run spread is 20%, not "up to 15%"; "5.4 corrections" is a mean over 240 pairs and is 6.3 among the 207 pairs that needed any; look-alike CI lower bound is exactly 0.
- DA: the one result that favours us (5.4 vs 6.6 fixes per library) is never reported in the paper's headline claims. (Note the mean-over-pairs caveat above applies to both.)

## Revision roadmap
Must do before submission:
1. Add new-face-only F1 to Table III and reword "matches" to "ties on all-face F1; slightly lower on new faces".
2. Time constrained average linkage directly (E1), or drop the speed claim.
3. Fix the three number mismatches; state the bootstrap unit correctly.
4. Verify or fix the `c_avg` revert, re-run exp19 if numbers move.
5. Report fixes-per-library with the correct denominator.
6. Fill author details; check DOIs; compile on Overleaf; check page count; plagiarism and AI-policy check.

Should do (novelty): E1 exact fast read step, E2 convergence across devices, E3 undo and wrong-correction recovery, E4 corrections across a recogniser upgrade. See `../../research/novelty_round4/02_research_report.md`.

Not to do: add more reviewers' wishlists beyond the 6-page budget.
