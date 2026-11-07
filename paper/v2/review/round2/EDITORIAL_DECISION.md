# Editorial Decision: simulated review, round 2

**Manuscript:** "Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries" (`paper/v2/cove_paper.tex`, commit ce1b15d)

**Decision: MAJOR REVISION.**
- Four seats recommend Major Revision: R1, R2, R3 and the DA. The Journal-Fit Reviewer recommends Minor Revision for this venue.
- Every seat gave confidence 4/5.
- The Devil's Advocate CRITICAL issue C1 is validated by the editor (see below), so the paper cannot be accepted as written.

**Panel provenance:**
- Five role-separated seats ran as separate subagents of one model family (Claude Opus 5.5). No seat saw another round-2 report before committing its own.
- Because all seats share one model family, their agreement is not evidence of independent errors.
- This was a simplified run of the full mode: the sprint-contract, provenance and attachment scripts were not run.
- All seats are `NOT_CALIBRATED`.

**Reports:**
- `R_EIC.md`: Journal-Fit Reviewer
- `R1_methodology.md`: methodology
- `R2_domain.md`: domain
- `R3_perspective.md`: perspective
- `R_DA.md`: Devil's Advocate

## Round-1 issues
- **Accepted as resolved:** the identity-disjoint split, equal-range tuning, the new baselines, the CIs, the reworded embedding claim and the honest update-time figure.
  - R1 recomputed the split overlap as 0.
  - R1 matched every Table I cell and every bootstrap CI to the JSONs.
  - The EIC verified 11 of the 13 items.
- **Still open from round 1:** the Immich-style and Chinese Whispers baselines (now with no stated reason) and the author placeholders.

## Devil's Advocate CRITICAL issue: adjudication
**C1. "100% of corrections kept vs 27%" holds by construction, and the only comparator is a strawman.**
- **Why it holds by construction:** the clusterer refuses any union or merge that would break a correction, so "kept" cannot be below 100%. The comparator is the same clusterer with the corrections thrown away.
- **Corroborated by:** R1 (issue 1), R2 (W1, W2) and the EIC (issue 1).

**Editor's verification:**
- I read `exp15_corrections.py` and the DA's scratch script `posthoc.py` and its output, which re-runs the exp15 oracle on all 240 test libraries.
- The script reproduces the paper's "lost" and "kept" F1 exactly.
- It then adds a trivial baseline: re-cluster from scratch, then re-apply the stored corrections afterwards (the "split" variant). Over the 207 libraries that received at least one correction:

| Approach | Corrections still holding | F1 after new photos |
|---|---|---|
| Re-cluster, corrections lost (paper's comparator) | 15.7% (mean over libraries) | 0.983 |
| Re-cluster, then re-apply corrections (DA baseline, ~20 lines) | 98.5% | 0.989 |
| Ours, corrections inside the clusterer | 100% | 0.991 |

- Ours minus the re-apply baseline: mean +0.002 F1, range −0.005 to +0.053. The DA reports the clearest edge on occluded photos.
- **Verdict: validated.**
  - Most of the headline gain comes from simply storing the corrections. Building them into the clusterer adds a small, real extra gain.
  - The DA's baseline was written by a reviewer and has not been vetted, so its numbers are indicative only.
- **Repairable**, by adding this baseline (and constrained average linkage) and re-sizing the claim. This blocks acceptance until done.

## Consensus issues (raised by 2 or more seats), ordered by severity

| # | Issue | Seats | Verified by editor | Required change |
|---|---|---|---|---|
| 1 | **C1 above:** no fair baseline for corrections. | all 5 | Yes | Add re-cluster-then-re-apply and constrained average linkage (cited but never run; Davidson & Ravi 2005). Report hold rate, later F1 and order agreement for all of them. State that 100% is guaranteed by the hard constraints. |
| 2 | **The hold-rate and correction-count statistics are mis-described.** "27%" averages per-library rates and counts the 33/240 libraries with no corrections as 100% held, because `satisfied()` returns 1.0 for an empty list. Pooled over corrections the figure is 20.3% (MBF 16.9%); the mean over libraries with at least one fix is 15.7% (MBF 13.5%). "Ten corrections per library" is a cap: the mean is 5.4 (MBF 5.8), and only 91/240 libraries reached ten. | all 5 | **Yes, recomputed** | Report pooled rates over libraries with at least one fix. Say "up to ten (mean 5.4)" in the abstract, Sec. V-C and the conclusion (line 368). |
| 3 | **The simulated user is a perfect oracle.** It always fixes the biggest mistake, picks the faces where a cut works best, is never wrong, and 81% of its fixes are must-links. | R1, R3, DA | Yes (`pick_correction`) | Add a noisier user: a random face of the intruder, about 10% wrong fixes, fewer fixes. Report how much of the gain survives. |
| 4 | **Close prior work from the authors' own novelty scans is not cited:** C-DBSCAN, C-DenStream, Lasek & Gryz (incremental constrained DBSCAN), ConPaC, Wu et al. 2013, Grinch. | EIC, R2, DA | Yes (named in `research/innovation_scan_*.md`) | Cite and contrast them in Sec. II. Verify each before citing. |
| 5 | **The title and the app do not match.** The app has no correction endpoint or UI at all, re-clusters from scratch on every import (so the incremental path is unused), and overwrites names. "Does not yet persist corrections" understates the gap. | EIC, R3 | Yes (round-1 finding, unchanged) | Either connect corrections to the app, or retitle the paper as a clustering method with an evaluation and describe the app's state exactly. |
| 6 | **The corrections path is not timed.** With corrections present, `labels()` takes the constrained batch path (dense k×k merge), and its cost at real library sizes is unreported. | R2, R3, DA | Partly (the DA timed it on 8,290 faces; see R_DA.md) | Add the constrained-path time to Sec. V-F. |
| 7 | **Smaller number problems:** (a) the Table III latency rows (27.5/13.3 ms) do not match the released `exp13_speed.json` (33.4/14.8 ms; ratio 2.25×, not 2.1×); (b) the abstract's "as low as 0.52" is the MBF figure, while the EdgeFace-S text says 0.56; (c) "the MBF pattern is the same" hides that average linkage beats ours by 2.6 points on occluded photos with MBF. | R1 (+ EIC) | (a) and (b) yes | Re-measure or trace Table III, and label 0.52 as MBF. State the MBF occluded result. |

## Single-seat findings (Minor unless noted)
- **R1 (Major):** the bootstrap treats 30 libraries as independent, but they share 79 family identities (about 11 libraries each) and come from one split. Use an identity-level (cluster) bootstrap, or state the limitation.
- **DA m1, reproduced:**
  - contradictory corrections are resolved by `sorted(self.must)`, that is, by face ids, which depend on insertion order. A 9-face test gave two different partitions over 12 orders.
  - Use an order-free rule, such as dropping the weakest must-link, or qualify "provably independent".
- **R3:**
  - corrections are keyed by face position, which deleting photos renumbers;
  - "nothing leaves the device" is not true for the recommended Docker install: there is no API key, CORS accepts any origin, and the API is reachable from the local network;
  - largest face only, no model hash check, consent and ethics of grouping people's faces.
- **R2:**
  - the EdgeFace licence is CC BY-NC-SA 4.0, and the paper omits the ShareAlike term;
  - the recogniser-protocol details;
  - no real-album or IJB-B data.
- **EIC:** the AI-use statement says the AI "edited the text" while the record shows a full AI-assisted rewrite, and IEEE expects the disclosure in the Acknowledgment section. The author placeholders also remain.
- **Page length:** the EIC estimates 5–5.5 pages against a 6-page limit. The paper has not been compiled.

## What the panel agrees is sound
- The clusterer code matches Sec. III, and the order-invariance proposition holds for non-contradictory corrections (DA, R3).
- The identity-disjoint evaluation is real, and the Table I and CI numbers match the JSONs (R1).
- The negative results and limitations are reported candidly (all seats).
- The topic fits an applied IEEE India venue (EIC).

## Revision roadmap (suggested order)
1. **Fix the statistics (issue 2).** This is text only and quick.
2. **Run the fair baselines (issues 1 and 6):**
   - re-cluster-then-re-apply (the DA's script is a starting point);
   - constrained average linkage;
   - time the constrained path.
3. **Run the noisy-user sensitivity test (issue 3).** Fix the order dependence for contradictory corrections (DA m1).
4. **Re-size the headline** from the results of steps 2–3. The likely honest claim is: storing corrections is what keeps them; building them into an order-invariant incremental clusterer adds a small further gain and keeps the result independent of photo order.
5. **Decide on the app (issue 5):** connect corrections to the app, or retitle.
6. **Text items:** prior work (issue 4), Table III latency, MBF occluded result, cluster bootstrap or limitation, licence, AI statement, placeholders, compile.

These are the panel's issues, in the reviewers' own terms. Which ones to address is the author's decision.
