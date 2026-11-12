# Devil's Advocate re-review: round 6

Simulated reviewer, not a real peer review. Manuscript: `paper/v2/cove_paper.tex` (commit 000152d). I checked numbers against `evaluation/results/exp25`, `exp28`, `exp29`, `exp18` and `exp30`. LaTeX is not installed here, so I could not count pages. `paper/v2/Cove_paper.pdf` is dated 10 Nov and is stale against the 13 Nov tex.

## 1. Round-5 issues

| Issue | Status | Reason |
|---|---|---|
| M1 "beneficial up to 1 in 20" | FIXED | Abstract now says "gone by about one wrong click in twenty". Discussion says "clear up to about two in a hundred". Sweep values match exp25 (p=0.02: +0.0034 [0.0015, 0.0054]). The +0.0034 itself is still not printed in the text. |
| M2 "more accurate on clean, blur, dark" | FIXED (small gap) | Abstract now says "within about one point... ahead on clean, behind on low-res and profile, by up to 7 points". The 51-configuration result is reported. The Table I people-bootstrap is named. Blur [+0.0024,+0.0059] and dark [+0.0016,+0.0033] intervals exist in exp28 and exclude zero, but the text does not print them. |
| M3 by-construction consequences | PARTLY | The abstract now says "Recomputing the groups from the two sets gives" and "frozen-label rule of our design". Sec. V-C still says "what a plain edit log lacks" and "53% describes a plain edit log". A merged log replayed in a fixed (time, device) order is still not tested. |
| M4 sync with removals | FIXED | Scope paragraph now says tombstones are "not tested". |
| M5 "order of magnitude faster" | PARTLY | The text now says the lead narrows, gives 9 to 15 times, and discloses the 316 s index build and the synthetic copies. The abstract and Conclusion still say "order of magnitude", with no end-to-end figure. The ratio mixes baselines (see N1, N2). |
| m1 loose "matches" | FIXED | "Within 0.003 F1" holds: error-prone 0.9851 vs 0.9878 is 0.0027. |
| m2 conclusion F1 mix-up | FIXED | Now "0.9925 after the next import, against 0.985". |
| m3 look-alike row missing | NOT FIXED | Look-alike is still discussed with no numbers. exp28 gives +0.0037 with a lower bound of exactly 0.0. |
| m4 hidden limitations | PARTLY | Interval reuse (79 people) and the synthetic setup are stated. Still missing: the wrong-click rate is the authors' own assumption; cluster identity (names, cover photos) after a recompute; threshold transfer. |
| m5 "safe" review-and-undo | FIXED | Now "should accompany" and "advisable", and AUC 0.60 is disclosed. |
| m6 upgrade subset | NOT FIXED | Still "the 210 libraries whose faces are identical". The 30 excluded pairs are not named. "All 1,372 held" is true by construction. |
| m7 "local-first" label | PARTLY | "Simulated" and "application has no sync" are explicit. The title and Intro still call Immich and PhotoPrism local-first. The paper does not say the two devices are copies in one process with identical embeddings. |
| m8 proposition ties | PARTLY | "Up to exact ties" is in the statement. The abstract still says "a function of the set". Must-link ties use content, while edge ties use face id. |
| m9 deletion evidence | PARTLY | Unit test and one run are mentioned. The transitivity loss when a bridging face is deleted is not. |
| m10 housekeeping | PARTLY | The multiplicity note is added. College, city and email placeholders and "Author contributions: to be completed" remain. 79+1,844 vs 1,571 identities is unreconciled. |

## 2. New or remaining issues

**MAJOR**

**N1. The "0.15 s" figure is wrong or ambiguous.**
- Location: Sec. V-D, "Adding the faces and updating links took 0.15 s."
- exp18 shows 0.145 s is the final batch only (829 faces). The sum over the ten batches is 0.88 s.
- exp29 shows a single-batch build of the same 8,290 faces at 8.4 s. The text never reconciles incremental and one-batch cost.
- Fix: write "0.88 s in total (0.15 s for the last batch)". Say what the 8.4 s one-batch build includes.

**N2. The speed ratios mix conditions and baselines.**
- Location: Sec. V-D "16 to 69 times at 8,290 faces", plus the Abstract and Conclusion.
- exp29 at 8,290 faces gives 69 times (cached constrained average linkage, 0 corrections), 40 times (SciPy), and 16 times (cached, 10 corrections).
- At 49,740 faces, ours plus index build (316 s) is slower end to end than every baseline.
- Fix: replace the abstract wording with "read step 9 to 15 times faster at 50,000 synthetic faces; index build, not timed against the baselines, takes 316 s". Add a small table giving n, ours, baseline name and build time.

**N3. The abstract's comparison for "keeps every correction" is a strawman.**
- Location: Abstract "where plain re-clustering keeps 20%"; Table II.
- Re-apply keeps 96% and gives later F1 0.9914. Ours gives 0.9925, a difference of 0.0011.
- The frozen rule gives 0.9928 for the precise user, which is higher than ours.
- The body states these figures. The abstract does not.
- Fix: add "re-applying keeps 96% at 0.001 lower F1".

**N4. Page limit unverified.**
- The body has a table*, 3 figures, the proof and about 4,300 words. The PDF is stale.
- Fix: compile and count before submitting. Cut the Related Work sentence on 2026-11-10 searches, or Table II columns, if over 6 pages.

**MINOR**

- **N5. Table I and the text disagree on look-alike.** Add a Table I row or a one-line number (m3).
- **N6. Placeholders.** The author block (college, city, email) and the Declarations ("to be completed") must be filled before submission.
- **N7. Confusing sentence.** Sec. V-B, "on the new photos alone it is better for all three users (ours -0.0014...)". The subject is constrained average linkage. Write "constrained average linkage is better on the new photos".
- **N8. Identity counts.** Define the 1,571 identities as those actually sampled in the 30 test libraries.
- **N9. Discussion wording.** "Within 0.003 F1 of ... a frozen-label rule" holds only for EdgeFace-S. With MBF the frozen rule is 0.009 lower. Add "with EdgeFace-S".
- **N10. Abstract and Proposition.** The abstract's "function of the set" should carry "up to ties", and the proof should break edge ties by content, as the must-link step does.

No CRITICAL issues.

## 3. Strongest remaining counter-argument

The properties that matter, namely devices agreeing, exact retraction and deletion, and kept corrections, hold for any design that recomputes from sets. The paper says so itself. Its only opponent is a frozen-label store the authors designed to diverge. The practical alternatives reach the same accuracy. Re-apply scores 0.9914 against 0.9925 for ours. Frozen scores 0.9928. Constrained average linkage ties on new photos. So what is new is the cheaper read step, and that is measured only on synthetic, disjoint rotated copies against a method nobody ships. The 316 s index build exceeds the baselines' entire runtime. The gain from corrections is under 0.01 F1 on a benchmark that already sits at 0.985, and it is gone at one wrong click in twenty. A real album or real user is never tested.

## 4. Summary

1. The round-5 MAJORs are mostly fixed. M1, M2 and M4 are FIXED. M3 and M5 are PARTLY fixed. m3 and m6 are NOT FIXED.
2. No CRITICAL issues. New MAJORs: N1, the "0.15 s" figure is really the last batch (total 0.88 s) and is unreconciled with the 8.4 s one-batch build in exp29. N2, speed ratios mix baselines and exclude the 316 s build.
3. N3: the abstract compares only against plain re-clustering (20%). Re-apply at 96% and frozen at 0.9928 are within 0.001 F1 of ours.
4. Page count unverified (no LaTeX here, PDF stale). Author-block and Declarations placeholders remain.
5. Sweep, bootstrap and scaling numbers match the JSONs. The remaining problems are wording and framing, not wrong results.
