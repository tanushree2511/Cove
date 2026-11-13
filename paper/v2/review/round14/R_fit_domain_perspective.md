# Round 14 review (simulated): Journal-Fit, Domain, Perspective. HEAD aea28f3

Read-only. No TeX is installed here, so nothing was compiled; the page estimate is a model. I read the full .tex (l.1-354), diffed 9e879fc..aea28f3, checked all 40 cited keys against references.bib by script (none missing; 13 bib entries are uncited and do not print), and re-derived numbers from evaluation/results (exp14_testruns, exp29_scaling, exp27, exp20, exp30c). I did not re-run verify_paper_numbers.py or re-open the Immich json.

## 0. Round-13 fixes: checked

| Fix | Verdict |
|---|---|
| Blank line in `\author` removed (l.23) | Correct. But see M1 (a different LaTeX problem in the same block). |
| "5.9 points ... on average in the worst condition (11.7 on one library)" l.190 | Numbers correct: mean F1 spread of First-Leader is 5.87 (occluded, the worst condition); the largest single library is 11.75. Grammar fine. |
| Dark moved to "not distinguishable" (+0.0022) l.224 | Correct under the stated rule (under 0.003). Table I (0.997 vs 0.995) agrees. |
| "large gains (occluded, low-res) come mostly from the centroid merge" l.226 | Supported by Table I (no-attach 0.907 vs single 0.800; 0.978 vs 0.963). |
| Immich "photos of people who appear once" l.241 | Fixed, reads correctly. |
| "(2--10 survive the deletion)" l.307 | Matches exp30c (kept 2 to 10, made 7 to 10). |
| "9 to 15 times at 49,740" l.313 | Correct. exp29: 233.5/15.4 = 15.1, 212.3/20.0 = 10.6, 174.4/15.4 = 11.3, 174.4/20.0 = 8.7. Round-13 M4's "9 to 16" came from rounded inputs; do not change it. |
| "14 to 69 times at 8,290 (30 and 20 s against 0.44 and 1.25 s)" | Partly wrong, see m3. |
| "Adding the faces to the flat FAISS index took 316 s" l.314 | Introduced a mislabel, see M2. |
| Abstract "mean ARI 0.997" l.36 | Number is EdgeFace-S only (MBF 0.996); see m1. |
| Discussion "given identical embeddings", "positive up to", "intervals probably too narrow" l.319-321 | Correct and consistent with Sec. VI-A (+0.0034 with CI above zero at p=0.02; interval includes zero at 0.05). |

## 1. Findings

### CRITICAL
None.

### MAJOR

**M1 - `\\` followed by a line that starts with `[` in the author tabular (l.21-23).**
Evidence: l.21 ends with `\\` and l.22 begins `[City], India`; l.22 ends `\\` and l.23 begins `[email]`. In a tabular `\\` looks ahead for an optional `[length]` and skips spaces and line ends, so `\\ [City]` is read as `\\[City]`: "Illegal unit of measure (pt inserted)", and the text "[City]" and "[email]" in the first column vanishes. This is the well-known `\\ [` gotcha. It affects only the placeholder rows and disappears once real data replace them, but the current PDF is not clean and an Overleaf run will show errors.
Fix: write `\\ \relax [City], India` or `{[City]}` (or just fill the real data), then recompile.

**M2 - The "316 s FAISS index" claim is mislabelled and contradicts the 0.9 s claim (l.304-306 vs l.314).**
Evidence: exp29_scaling.py `build_s` calls `build()` from exp20, which adds 64 faces at a time to the whole `StableIncrementalClusterer` (FAISS add, range search, neighbour lists, unions). It is not the index add. The same script gives 8.4 s at 8,290 faces, while l.305 says adding all 8,290 faces and updating links took 0.9 s (ten batches). A reader sees 0.9 s for 8,290 faces and 316 s for 49,740 faces (350 times for 6 times the faces) with no explanation, and the round-13 reword ("adding the faces to the flat FAISS index") made the label more specific and wrong.
Fix: "Adding the faces in batches of 64 (search and link update) took 8 s at 8,290 and 316 s at 49,740 faces, so there the build, which grows with the flat range search, dominates the read."

**M3 - Placeholders still block submission (l.18-23, 70, 347, 348).** Authors 3-5, college, city, email, "URL to be added" (while l.70 says "URL below"), and "Author contributions: to be completed". Known and flagged in the l.17 comment; listed so it is not forgotten. Fix: fill before submission, and check the real header height (Section 3).

### MINOR

**m1 - Abstract l.36: "(an edit-log baseline of ours: 53% and 31%, mean ARI 0.997)".** Still does not say 53% of what (agreement on 240 pairs, EdgeFace-S and MBF), and 0.997 is the EdgeFace-S value only (0.996 for MBF). Fix: "a plain edit log agrees on 53% and 31% of 240 cases for the two recognisers (mean ARI 0.997 and 0.996)", or drop the ARI to save space.

**m2 - "In the first two the alternative is a frozen-label store" (l.183-184) points at the wrong items.** The four italic items are Error rate, Two devices, Retraction, Upgrade; the frozen store is used in Two devices and Retraction (l.291, l.297), not in Error rate. Fix: "In Two devices and Retraction the alternative is...".

**m3 - 8,290-face ratio (l.313).** From exp29, c-avg is 30.3 s and 19.6 s against ours 0.44 s and 1.25 s: 69 and 16 times. The "14" comes from SciPy (17.4 s) against ours with corrections (1.25 s), which the parenthesis does not show. Fix: "16 to 69 times at 8,290 faces (30 and 20 s against 0.44 and 1.25 s)".

**m4 - Two timings of the same quantity differ without comment (l.306 vs l.313).** At 8,290 faces with 10 corrections the read takes 1.9 s (exp20) in one paragraph and 1.25 s (exp29) in the next. Fix: say "in a later run" or use one set of numbers.

**m5 - Table I caption calls CALFW/CPLFW "identity-disjoint test data" (l.196) while l.161 says they were also used when developing earlier versions.** The disclosure exists, but the caption overstates for those two rows. Fix: "identity-disjoint test data (CALFW/CPLFW: see Sec. IV)".

**m6 - Immich is not in the "additions" list (l.145-146; carried).** Also say it compares whole systems (their detector and recogniser too). Fix: add "Immich comparison" to the list and "whole system" to l.241.

**m7 - Terms at first use.** First-Leader and Two-stage appear at l.166 (Test) before the l.190 definition; "constrained average linkage" and "re-applying" are used in the abstract (l.33-38) before the l.175-178 definitions. Fix: "re-applying corrections after clustering" in the abstract; at l.166 "First-Leader (greedy leader pass) and Two-stage (that plus the centroid merge)".

**m8 - "better on every condition by 0.2 to 14 points" (l.225; carried).** JPEG, mixed and look-alike are not in Table I for single linkage. Fix: "on every condition shown".

**m9 - Blur "better" (+0.0038, l.223) has no interval, while the tie rule needs one.** Fix: add the interval or write "ahead by 0.004".

**m10 - Discussion "stay positive to ten" (l.321; carried).** Re-applying is positive to 0.20. Fix: "up to 10% (constrained average linkage) and 20% (re-applying) wrong clicks".

**m11 - Perspective: fairness is not mentioned.** LFW and FIW are celebrity-heavy and demographically skewed; accuracy on a real family album, especially for children and across skin tones, is unmeasured. The l.323-324 clause on public figures covers privacy, not bias. Fix: one clause in Scope ("demographic differences are also unmeasured").

## 2. Claim vs evidence, consistency, ethics

- **Abstract, body and conclusion agree** on: tie with average linkage (0.9854 vs 0.9857; 7 points lower on CPLFW: 0.841 vs 0.909 = 6.8), FIW tie (0.786/0.785), keeps every consistent correction (100% vs 20%), within 0.003 of c-avg (largest gap 0.0027), the 0.05 crossover, device agreement 240/240 vs 53%/31%, and about half the value across a recogniser change (47%/48%). The "order of magnitude" claim holds against constrained average linkage (10.6 to 15.1 at 49,740).
- **Table II vs text:** bold marks, the 0.0003 frozen gap, the 0.0011 precise gap and the 0.9851/0.9878/0.9893 error-prone numbers all agree.
- **Proof sketch** matches the Proposition, including "up to exact ties" and the exact-arithmetic caveat. Nothing broken in l.130-142.
- **Sentences:** no broken or ungrammatical sentence found in the current text. The abstract is long (about 215 words) but within the IEEE range.
- **Ethics and privacy:** FIW terms (l.156, l.346-347), no image shown, biometric warning and tombstone deletion (l.329-330), AI-use disclosure and model licences (l.342-349) are present and consistent. The FIW terms appear three times; one could be merged to save a line.
- **Citations:** 40 of 40 resolve. The bib comment at l.212-213 says some DOIs are unconfirmed; run a final bib check.
- **Related work:** the bounded-search statement (2026-11-10, abstracts only) is honest. No missing key reference I can name.

## 3. LaTeX and page estimate (candid)

**LaTeX.** `array` is loaded, `*{5}{>{\centering\arraybackslash}p{0.19\textwidth}}` is valid, and `\small` plus `\tabcolsep` inside `\author` are scoped. Width: 5 x 0.19 x 516 = 490 pt plus 20 pt of padding = 510 pt, under 516 pt. The block is legal in IEEEtran conference mode apart from M1. `amsthm` with `proposition` and `proof[Proof sketch]` is fine. `table*` is `[t]` and may float to the next page. Real emails (about 40 characters) in 98 pt columns will overfull; use `\scriptsize` and `\allowbreak`.

**Page estimate.** I could not compile. Against cef2e0f (about 21,800 characters, 3 tables, 6 pages), the text is about 2,900 characters longer (about +50 column lines), Table III is gone (about -15 to -20 lines), there are about 3 to 5 more references (+6 to +10), and the five-author header is 1-2 lines taller (+2 to +4). Net about +25 to +40 lines over the last 6-page build. Against the 7-page build (24,900 chars with a figure) the text is only about 200 characters shorter and the figure is gone. I put the chance of exactly 6 pages with placeholders at 35-45%, lower with real affiliations. Treat it as likely over by 10 to 25 column lines.

**Ranked cut list (lowest value first; column lines saved).**
1. Two-devices detail l.291-293: drop "(mean ARI ... mean F1 gap about 0.001-0.002)" and the repeated "not a deployed sync" sentence; keep 127/74 of 240 and "not unique". About 3 lines.
2. Discussion "What the results show" l.317-321: keep one sentence about the sweep (Results and Conclusion repeat it). About 4 lines.
3. MBF clauses l.227-228 (CALFW/occluded numbers) and l.238 (MobileFaceNet agrees); keep the 13-point CPLFW gap. About 3 lines.
4. Declarations l.346-347: merge the three FIW-terms mentions; drop "the released files hold only scores and anonymous indices". About 2.5 lines.
5. Table I caption l.196-198: drop "Bold: best. Last row ..." and "four methods are within 0.004". About 2 lines.
6. FIW corrections paragraph l.263-265: one sentence. About 2 lines.
7. One of gower1969mst / sibson1973slink with its clause (l.89-90). About 2 lines plus a reference line.
8. Author block: merge Dept. and College into one row. About 2 column lines.
9. Abstract: delete "(untested)" and the ARI added in round 13. About 1.5 lines.
10. Deletion sentence tail l.307 and "The other direction gives 48%." l.301. About 1.5 lines.

Items 1-7 give about 18 lines; adding 8-10 gives about 23. Do not cut Table II, the proof sketch, the Immich result or the sweep numbers.

## 4. What is fine
- All round-13 content fixes except the two noted (M2, m1) are correct and introduced no number error; the First-Leader spread, deletion survival and 9-to-15 are verified against raw results.
- Every `\ref` resolves; no figure is cited; 40 of 40 cites resolve.
- Limits are stated: simulated users and devices, own frozen baseline, tie framing, 79 shared people, synthetic scale, bounded novelty search.
- Headline numbers in abstract, Table I/II, text and conclusion agree.

## 5. Recommendations
- **Journal-Fit Reviewer: minor revision, conditional on a compiled 6-page build with real author data** (M1, M3, page fit). Confidence 3/5 (nothing compiled).
- **Domain Reviewer: weak accept**; fix M2, m3, m4, m7, m8. Confidence 4/5.
- **Perspective Reviewer: weak accept**; the scope statements and the Immich paragraph help a practitioner; add m11 and fix m6, m10. Confidence 3/5.

No new experiments needed; M2 only needs the exp29 timing label read correctly.
