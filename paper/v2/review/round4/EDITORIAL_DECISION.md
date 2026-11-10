# Round 4 Editorial Decision (simulated, not real peer review)

Manuscript: paper/v2/cove_paper.tex at commit ab09dbe (not cut to 6 pages, not compiled).
Reports: Journal-Fit, Methodology, Domain, Perspective, Devil's Advocate. The synthesis below was written by the session, from the five reports. It is model output, not an editor's decision.

## Votes
| Seat | Recommendation | Confidence |
|---|---|---|
| Journal-Fit | Major Revision | 4 |
| Methodology | Minor Revision | 4 |
| Domain | Minor Revision | 4 |
| Perspective | Major Revision (borderline Minor) | 4 |
| Devil's Advocate | 0 critical, 3 major, 8 minor | - |

Overall: **Minor-to-Major Revision. All five seats ask for wording, framing, length and one cheap check. None asks for a new study.**

## Consensus (4 or 5 seats)
1. **Length.** About 8 pages; 6 needs roughly 1,500 words cut.
2. **Claim size.** Accuracy ties constrained average linkage; the paper reads as if it wins. Reframe as "assembles known parts and measures what set semantics buys".
3. **Simulation presented as system behaviour.** The app has no correction UI, no device sync and no undo; say so in one plain sentence.
4. **Corollary over-claim** (any method that recomputes from the sets has the properties). State preconditions, and say the comparison is with a frozen-label baseline the authors designed.
5. **Cost claim.** The 261 s vs 1.3 s gap is mostly the authors' own NumPy loop. A compiled version is about 13x slower than ours (range 13-53x), and the Devil's Advocate's 40-line scipy version took about 5 s, i.e. 2-4x our read step. The words "two orders of magnitude" must go.
6. **Number slips:** "twelve corrections" (really 8.2 per library, about 2 binding), abstract "within 0.002" (false for the error-prone user), "one in twenty", "seven baselines", "all 240 libraries", the AUC explanation, the Acknowledgment line about checked numbers.
7. **Novelty wording:** bounded "not found in searched sources", with queries and the date; C4 is known (Gower and Ross 1969; Maus and Borin 2026).

## Disagreement
- Journal-Fit and Perspective: Major (framing). Methodology and Domain: Minor (evidence is sound). Resolution: the evidence is sound; the framing is the problem. Fixable by writing alone.
- Devil's Advocate wants one more timing run first. Methodology also suggested it. Cheap (under an hour), and it removes the single weakest sentence.

## Devil's Advocate critical issues
Zero CRITICAL. The strongest counter-argument (everything follows from recompute-from-a-set; the cost edge is partly implementation; from about 1 wrong click in 20 plain re-apply beats hard constraints) is accepted as a framing constraint, not a blocker.

## Roadmap
1. (Optional, recommended, under 1 h) Time a compiled constrained average linkage with the same corrections, plus one 16-32k-face point. Rewrite cost sentences in abstract, V-C, V-G, VI, VII with the result, whatever it is.
2. Retitle around corrections that stay put; cut to 6 pages.
3. Fix items 3-7 above and the 22 reference fixes (research/round5_confirm/refs_part*.md).
4. Authors: names, DOIs, compile on Overleaf, plagiarism check, read the CFP (IEEE number, AI policy).

## Verdict
Publishable at an Indian IEEE regional or national conference after wording fixes and cuts. Not publishable as it stands (too long, over-claimed).
