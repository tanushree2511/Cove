# Round 5 - Journal-Fit Reviewer (R_EIC)

Recommendation: MINOR REVISION (accept after fixes), confidence 3/5.
The contribution is clear and honestly framed. The remaining problems are one over-claim repeated in three places, a few stale or imprecise statements, submission placeholders, and a likely overrun of the 6-page limit.

Verification note: I ran evaluation/verify_paper_numbers.py. Result: 129 ok, 2 mismatch. Both mismatches are labelled "abstract: ours minus c-avg" (0.0011 vs 0.00102; 0.0003 vs 0.00038). The abstract no longer contains these numbers, so the checks are stale. I also checked Table I against the text (ours minus average linkage per condition, ours minus single linkage range 0.2 to 14 points, attach-removal cost, 0.9854 overall), Table II against the prose, and Table III against the prose. They agree except where noted below.

## Issues

1. MAJOR - Over-claim. Locations: "Corrections stay beneficial up to about one wrong click in twenty" (abstract); "corrections stay useful up to about one wrong click in twenty" (Discussion); "Corrections remain beneficial up to about one wrong click in twenty, so pairing them with a visible, removable list makes them safe to use" (Conclusion).
   The evidence in Sec. 5.2 is +0.0009 at p=0.05 and +0.0010 at p=0.10, "intervals include zero", and -0.0057 at p=0.20. Only p=0 (+0.0065) is clearly beneficial. Table II's error-prone user (about 10% wrong, aimed at look-alikes) ends at 0.9851 vs 0.9854 for discarding, which is not beneficial. "Safe to use" is an extra step the paper never tests.
   Fix: write "do no measurable harm up to about one wrong click in twenty (gain indistinguishable from zero) and become harmful by one in five". Drop "safe to use"; write "so we recommend pairing them with a removable list". Make abstract, Discussion and Conclusion say the same thing.

2. MAJOR - Stale or inaccurate protocol claim: "All rules were fixed before any test number was computed" and "Nothing here is tuned".
   Sec. 5.1 reports a finer 0.01 baseline grid, a 51-point budget for ours, and a pose-aware bonus tried and rejected on CPLFW. All of these were run after test numbers existed (they respond to review). The pose bonus was judged on test data.
   Fix: "The main protocol was fixed before test numbers were computed; the finer-grid, small-budget and pose-bonus checks in Sec. V-A were added afterwards in response to review and are reported as such."

3. MAJOR (submission-blocking, not scientific) - Placeholders remain: "[College name]", "[City]", "[email]", and "Author contributions: to be completed". Fix: complete them before submission.

4. MAJOR - Length. Best estimate is 6.5 to 7.0 pages, so about 0.5 to 1 page over the hard limit.
   Basis: 4,200 words is about 4.3 pages of body text. Table I (table*, 11 rows) is about 0.3 page. Tables II and III are about 0.3 page together. The three figures are about 0.5 page. About 38 references at 8 pt is about 0.9 page. The proof, equations, and the Acknowledgment and Declarations headings add about 0.2 page.
   Cuts, in priority order:
   (a) Drop Fig. 2 (wrong-click sweep) and keep the four sweep numbers in text (saves about 0.2 page). Alternatively keep the figure and delete the sentence listing the numbers.
   (b) Cut Table I rows JPEG q8 and Mixed (near-ties already described in text).
   (c) Compress the Sec. IV "Corrections" paragraph and the Sec. V-D scale paragraph, especially the garbled c-avg sentence (issue 9). Saves about 0.15 page.
   (d) Merge Declarations into the Acknowledgment paragraph; trim Related Work "Incremental and constrained" by about 4 lines.
   (e) The .bib has about 48 entries; make sure only cited ones appear, and prune passing citations (for example ruiz2009cdenstream, lasek2019density, mazumdar2017noisy).
   Compile on Overleaf to confirm before submitting.

5. MINOR/MAJOR - Conclusion mixes metrics: "keeps corrections across imports (F1 0.984 to 0.994; 20% survive plain re-clustering)". The 0.984 to 0.994 figures are the "now" gain, before the new photos arrive. After import the figures are 0.9854 (discarded) vs 0.9925 (ours), per Table II. A reader will take this as the post-import gain.
   Fix: "(F1 0.985 to 0.993 after the next import; 20% of corrections survive plain re-clustering)".

6. MINOR - Abstract: "matches average linkage without corrections to about one point" sits beside the unreported CPLFW result (ours 6.8 points below on CPLFW, 0.841 vs 0.909) and the 0.9 point deficit on occluded photos. The abstract is scoped to "simulated libraries", but a reader of the abstract alone never learns of the pose weakness.
   Fix: add "(but about 7 points lower on a large-pose benchmark, CPLFW)". This is honest and still findings-led.

7. MINOR - Attach statement incomplete: "the gain is the attach threshold, whose removal costs up to 3.6 points". Table I shows removing attach helps on CPLFW (0.892 vs 0.841, +5.1 points) and costs 2.8 points on CALFW. So attach is not uniformly a gain.
   Fix: "removing it costs up to 3.6 points on degraded photos (2.8 on CALFW) but gains 5.1 on CPLFW, where attachment hurts recall".

8. MINOR - Sweep vs error-prone user look inconsistent: Fig. 2 has +0.0010 at p=0.10 (casual user), while Table II's error-prone user (probability 0.1) ends at -0.0003 against discarding. The cause is that error-prone wrong clicks target look-alike clusters while the sweep's are random.
   Fix: one sentence saying so. Without it the 1-in-20 / 1-in-10 headline looks contradictory.

9. MINOR - Garbled sentence in Sec. V-D: "Constrained average linkage (split per component; a version that caches each row's best partner, identical labels to our first NumPy version at 1,658 and 3,316 faces, which needed 293 s at 8,290 faces) took 234 and 212 s...". The reader cannot tell which implementation is timed, and the baseline is the authors' own, which affects the "order of magnitude faster" headline.
   Fix: split into two sentences; state that this is an optimised in-house Python implementation; keep the SciPy unconstrained lower bound (9x) as the conservative figure. In the abstract say "roughly 9 to 15 times faster than our implementation of constrained average linkage".

10. MINOR - Undefined terms. "First-Leader", "Two-stage" and "Ours, no attach" (Table I columns) are never defined in the protocol; Two-stage is only glossed in Results. "MBF" is used without definition (first mention is "MobileFaceNet w600k_mbf"). "Cove" is named in the abstract and introduction but never described.
   Fix: one line in Sec. IV listing the baselines; "(MBF)" at first mention; one clause saying what Cove is.

11. MINOR - Baseline naming inconsistency: Table II row "Frozen (Immich-style)" and Sec. IV "Immich's default" vs Sec. V-C "This baseline is our own design, not any product's sync" and the Scope paragraph "a frozen-label store we designed".
   Fix: rename the row "Frozen labels (our baseline)" and say only that the 0.5 cosine threshold follows Immich's documented default (cite it), so the paper does not imply that Immich behaves this way.

12. MINOR - Sec. IV says 79 + 1,844 identities per half (1,923), but people-resampling uses "1,571 identities". State whether 1,571 are those actually sampled into the 30 test libraries.

13. MINOR - "The frozen rule matches our F1 with EdgeFace-S (-0.0003)": in Table II the frozen row has the higher precise-user F1 (0.9928 vs 0.9925), so the sign is confusing. Write "ours is 0.0003 lower".

14. MINOR - Proposition holds "up to exact ties", but centroid sums also depend on floating-point summation order. Say "up to exact ties and floating-point summation order" (order agreement 1.000 was observed).

15. MINOR - AI-disclosure paragraph. Substantively good (tool, role, responsibility, verification script, simulated reviews). Improve it by:
    (a) titling it "Acknowledgment and AI-use disclosure" so it is findable;
    (b) stating that the authors checked the reference list and the code (the literature search was AI-run and "mostly abstracts");
    (c) confirming the exact wording the target conference requires;
    (d) removing the two stale checks from the verification script (see note above), so the "checked against per-run results" claim is clean.

16. MINOR - Contribution clarity. Positioning is honest ("we claim none of them", "application-and-measurement study") and there is one core idea: labels are a function of the face set and the correction set, with measured consequences. But the three bullets read as three studies (clusterer, correction comparison, accuracy and scale). Consider leading with one sentence: "the contribution is a measured demonstration that recomputing from sets gives order independence, durable corrections, exact retraction and cross-device agreement at no accuracy cost". Also, "Order-Independent" is shared by single and average linkage (the paper admits this), so say explicitly in the introduction that the novelty is the incremental, correction-preserving combination.

17. MINOR - Venue readability. Sec. IV and V carry Poisson-weight and paired bootstraps and many sub-0.01 differences. Add one plain-language sentence at the start of Results ("differences below 0.01 F1 are small; intervals are given where it matters"). Moving the p-sweep numbers into the figure supports the length cut 4(a).

## Strengths
- A clear, falsifiable core property (labels are a function of the two sets) with a short proof sketch and its stated limits (exact ties).
- Unusually honest reporting: names where the method loses (CPLFW, low-res, occluded, wrong clicks at p=0.2, tie with constrained average linkage), uses identity-disjoint test data, equalised tuning and finer-grid re-tuning.
- A sensible baseline set (constrained average linkage, frozen-label store), and it says the set property is not unique to the method.
- Reproducibility: per-run JSON, a number-verification script (129 of 131 checks pass), a released-code statement, licence notes.
- Concrete engineering results (deletion 0.59 s vs 7 s, exact read step, scale test to 50,000 faces) suited to a systems-minded regional audience.
- Findings-led abstract and a short scope paragraph; limitations are stated briefly without apology.

## Hand-back summary
1. Recommendation: Minor revision, confidence 3/5; one clear contribution, honest tone.
2. Main over-claim: "beneficial up to one wrong click in twenty / safe to use" in abstract, Discussion and Conclusion; sweep intervals at p=0.05 and 0.10 include zero.
3. Stale or imprecise: "rules fixed before any test number" (post-hoc checks exist), the Conclusion's 0.984 to 0.994 (pre-import figure), attach-removal "costs up to 3.6" (ignores CPLFW +5.1), Immich-style vs own-design label.
4. Length about 6.5 to 7 pages: cut 0.5 to 1 page (drop or inline the sweep figure, trim Table I rows, compress Sec. IV/V-D, merge Declarations, prune refs); fill the author and contribution placeholders.
5. AI disclosure is adequate (add that authors checked refs and code; retitle); the verify script has 2 stale abstract checks to remove.
