# Round 6 - Reviewer 1 (Methodology)

Checked against the current cove_paper.tex, exp25/26/28 JSON files, and a fresh run of verify_paper_numbers.py (131 ok, 0 mismatch). Cove_paper.pdf is 6 pages (may predate the last edit; recheck after final build).

## Round-5 issues

1. Break-even claim (MAJOR): **FIXED.** Abstract and Conclusion say "gone by about one wrong click in twenty"; Results and Discussion state +0.0009 / +0.0010 with intervals including zero, and "clear up to about two in a hundred". This matches exp25.
2. "Matches" over-generalised (MAJOR): **FIXED.** Abstract now says "within about one point of average linkage (ahead on clean, behind on low-res and profile, by up to 7 points)" and "within 0.003 F1".
3. Multiplicity and selective reporting (MAJOR): **PARTLY.** Low-res loss is now named in the abstract and "no multiplicity correction" is stated. Still missing are CIs for blur and dark (they exist in the JSON) and any overall (ALL) bootstrap interval for ours vs average linkage.
4. "Fixed before any test number" (MAJOR): **FIXED.** Sec. IV now says only the main protocol was fixed and lists the later checks as additions.
5. Consequence results by construction / strawman baseline: **PARTLY.** The abstract now says "frozen-label rule of our design". The text says the frozen store mixes insertion order with replay order and that 53% "describes a plain edit log". Still missing: a frozen variant with canonical face order, mean ARI / F1 gap next to 53%, and a sentence that the 100% rows follow from the Proposition.
6. Timing hygiene: **PARTLY.** The text now says single timings vary up to 2x and gives the 0.3-0.6 s range. Still open: "3.4-4.9 s" mixes two runs, "0.15 s" is one 829-face batch but reads as the whole load, and the 16-69x ratios come from exp29 while the printed 0.5 / 1.9 s come from exp20. No repeats.
7. Scaling trend and comparator: **MOSTLY FIXED.** "Synthetic" is in the abstract and "the lead narrows" is stated. Still not said: the comparison mixes the authors' NumPy constrained average linkage with SciPy, and the read step grows with exponent about 2.
8. Exactness wording: **FIXED.** "210-216 pairs per user received corrections ... all but one of 1,276 cases" matches exp26. The 8,290-face check using random corrections is not flagged as weakly binding.
9. Identity bootstrap details: **NOT FIXED.** Reweighting nature, order-0-only per-face scores, and the ALL row are still unaddressed. This is minor.
10. Fairer-tuning paragraph: **PARTLY.** "None moved by more than 0.0021" is now accurate. The fine-grid mixed result (-0.0034 [-0.0071,-0.0002]) and why the budget is 51 points are still not reported.
11. Proposition vs code: **MOSTLY FIXED.** "In exact arithmetic ... ties at a threshold" covers floating-point issues. Deletion is still backed by one seed (exp30) plus a unit test, while the abstract says "exact handling of deleted photos".
12. Interval unit: **FIXED.** Sec. IV and the Discussion both say library-condition pairs. No library-level robustness sentence, which is fine.
13. Verification script: **PARTLY.** The script now passes 131/131. exp28_testruns_edgeface_s.json is still untracked in git (`git status` shows `??`), yet the paper says per-run results are released.
14. Nits: **MOSTLY FIXED.** "About 7 points" replaces 6.8. The sentence "frozen rule matches our F1 (-0.0003)" still does not say which way the sign runs.

## New or remaining issues

**A. MINOR - abstract "within 0.003 F1" is not true on new faces.** Location: abstract, Conclusion, Discussion. Against constrained average linkage on the new photos alone, the error-prone user gives -0.0057 and the precise user -0.0014 with a CI excluding zero. The Discussion also lumps "a frozen-label rule" into the 0.003 statement, but ours is 0.009 higher with MBF. Fix: "within 0.003 F1 on all faces (lower on newly arrived faces)" and drop the frozen rule from that sentence.

**B. MINOR - "exact retraction" and "exact deletion" in the abstract are properties of the design, not findings.** The text admits this ("would match by construction"), but the abstract presents them as results beside empirical ones. Fix: "exact by construction" and add "(one deletion run)".

**C. MINOR - the order-independence claim covers only the tested orders.** "Ours gave identical partitions in every order" rests on 5 shuffles and the Proposition, which is only up to ties. That is adequate and is stated. No action beyond keeping the caveat.

**D. MINOR - error-prone user result is stated as "ours 0.985, no better than discarding" while the sweep says +0.001 at p=0.05 to 0.10.** Both are true (different error models: p=0.1 look-alike for error-prone vs sweep), but a reader may think they conflict. Fix: one clause noting that the error-prone user's wrong clicks are look-alike merges at p=0.1.

**E. MINOR - the Table I order-agreement row (0.562 etc.) is a minimum over conditions, but the text quotes "0.56" for First-Leader without saying it is the worst case.** The caption says "lowest"; fine, but state "worst-case" in the text.

No critical issues found. Numbers I rechecked (exp25 p=0 gain +0.0065, exp26 counts, 131-number script) match.

## Recommendation

**Minor revision**, confidence 4/5. Claims are now sized to evidence in the abstract, results, and conclusion. What remains is polish: blur/dark CIs and an ALL interval (issue 3), timing provenance (6), fine-grid mixed result (10), committing the exp28 cache (13), and tightening "within 0.003 F1" and "exact" in the abstract (A, B). None of this needs new experiments.
