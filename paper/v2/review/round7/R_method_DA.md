# Round 7 - Methodology + Devil's Advocate verification (simulated reviewer)

Checked cove_paper.tex (commit 8c28a83) against exp14, 18, 20, 25, 29 JSON. verify_paper_numbers.py: 131 ok, 0 mismatch. No LaTeX here, so pages are uncounted; Cove_paper.pdf (10 Nov) is stale.

## A. Numbers I re-derived (all match)
- Abstract: re-apply 96/73%, plain re-cluster 20%; 7 points (CPLFW 0.909 - 0.841 = 6.85); 53% (127/240); 0.003 F1 (0.9878 vs 0.9851 = 0.0027).
- Timings: 0.44/1.25 s vs 30.4/19.6 s = 69x and 16x. At 49,740: 15.1x, 10.6x (constrained), 11.3x and 8.7x (SciPy) = "9 to 15". OK.
- 0.9 s total add = 0.877 s (sum of ten batches); last batch 0.145 s. OK.
- CPLFW attach: 0.8923 - 0.8406 = 5.2 points; occluded 3.6. OK.
- exp25 p=0.02: +0.0034 [0.0015, 0.0054]; p=0.05 +0.0009; 0.10 +0.0010 (CIs include 0); 0.20 -0.0057. OK.
- 3.4-4.9 s and 4.5/5.1 vs 1.9/2.2 s match exp18/exp20. Citation keys and labels: every \ref resolves; no reference to the removed scaling figure or consequences table.

## B. Round-6 issues
Methodology (R1)
1. Break-even: FIXED (Abstract, Results, Discussion agree with exp25).
2. "Matches" over-generalised: FIXED ("within about one point ... behind ... by 7 points").
3. Multiplicity/CIs: PARTLY. Note added; blur and dark still have no printed CI, no ALL interval.
4. "Fixed before any test number": FIXED (Sec. IV, first paragraph).
5. By-construction baseline: PARTLY. "frozen-label rule of our design" is in the abstract; no canonical-order frozen variant.
6. Timing hygiene: PARTLY. "0.9 s (0.15 s last batch)" and the 0.3-0.6 s spread added; "3.4-4.9 s" still mixes runs; no repeats.
7. Scaling: MOSTLY FIXED ("synthetic", "lead narrows"); NumPy-vs-SciPy mix not stated.
8. Exactness wording: FIXED.
9. Identity bootstrap details: NOT FIXED (minor).
10. Fairer tuning: PARTLY. The -0.0034 mixed fine-grid result is not reported.
11. Proposition vs code: MOSTLY FIXED (ties caveat in the statement). Deletion is still one run.
12. Interval unit: FIXED.
13. Verification: PARTLY. exp28_testruns_edgeface_s.json is still untracked (`git status` shows `??`).
14. Nits: PARTLY (sign of "-0.0003" is now clearer; "0.56" is not labelled worst case in the text).
A. "within 0.003 F1" on new faces: NOT FIXED in abstract/Conclusion (the body says "tied"). B. Abstract "exact" for deletion: NOT FIXED (no "by construction", no "one run"). D. Error-prone vs sweep: PARTLY (now "agrees with the sweep"; look-alike reason not stated). E: see 14.

Devil's Advocate
- M1 FIXED. M2 FIXED (blur/dark CIs unprinted). M3 PARTLY (Sec. V-C still frames 53% as "a plain edit log"; no merged-log-in-fixed-order test). M4 FIXED. M5 PARTLY (abstract now says "read step" and "synthetic"; index build and 316 s absent from abstract). m1, m2, m5 FIXED. m3 look-alike numbers: NOT FIXED. m4, m7, m9 PARTLY. m6 (30 excluded pairs unnamed): NOT FIXED. m8: PARTLY (abstract still says "a function of the set"). m10: NOT FIXED (placeholders).
- N1 (0.15 s): FIXED. N2 (mixed baselines): PARTLY (ranges and 316 s disclosed in body). N3 (strawman): PARTLY (re-apply 73-96% now in abstract, F1 gap 0.9914 vs 0.9925 not). N4 pages: NOT VERIFIABLE. N5: NOT FIXED. N6 placeholders: NOT FIXED. N7: NOT FIXED. N8: NOT FIXED. N9: NOT FIXED ("with EdgeFace-S" still missing in the Discussion's "frozen-label rule" claim; but Sec. V-B itself is correct). N10: NOT FIXED.

## C. New issues from the edits
1. MAJOR - Submission blockers remain: [College], [City], [email], "URL to be added", "Author contributions: to be completed". Fill them.
2. MAJOR - Page count never checked after cuts. Compile and confirm at most 6 pages (tex is ~4,250 words, one table*, three figures).
3. MINOR - "69 times" is not a stable figure. The same baseline is faster with ten corrections (19.6 s) than with none (30.4 s), and ours is 1.25 s here but 1.9 s in exp20. Single runs, no repeats. Fix: lead with "about 16 times" or "16 to 69 (single timings)".
4. MINOR - Text calls the 8-s build "adding to the flat FAISS index", but exp29 `build_s` times the whole clusterer add (batches of 64). The ten-batch add took 0.9 s for the same faces, a 9-fold gap explained only by "larger batches". Fix: say "building the clusterer" and give the batch size effect in one clause.
5. MINOR - Sec. V-B "on the new photos alone it is better for all three users (ours -0.0014 ...)": the subject is constrained average linkage; the sentence reads as if ours is better. Fix: "constrained average linkage is better on the new photos alone".
6. MINOR - "(eight conditions; no multiplicity correction)": Table I now shows 8 rows, but the bootstrap covered JPEG and look-alike, which are no longer in the table. Say "ten conditions" or list them.
7. MINOR - Abstract "(53% for a frozen-label rule of our design)" omits MBF's 31%, and the parenthesis can be read as the accuracy of the new method.
8. MINOR - figs/scaling.pdf, streaming and similarity_split files are now unused; harmless, but check they are not cited by anything else.

## D. Strongest remaining objection
What is new beyond known parts is the cheaper read step, measured on synthetic data against a baseline the authors wrote. Accuracy ties constrained average linkage. The other properties hold for any recompute-from-sets design, as the paper admits. The paper is honest now, but the claim size is "a careful engineering study".

## Recommendation
Minor revision (accept after housekeeping). Confidence 4/5. No CRITICAL issues. Do first: placeholders, compile page count, commit exp28 cache, soften "69 times", fix the V-B sentence.
