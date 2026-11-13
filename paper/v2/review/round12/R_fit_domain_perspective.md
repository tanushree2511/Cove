# Round 12 review (simulated): Journal-Fit, Domain, Perspective. HEAD 49e33e2

Read-only. No TeX on this machine (pdflatex, latexmk, tectonic absent), so nothing was compiled and the page estimate is a model, not a measurement. I read the full .tex (l.1-358), exp32_immich_edgeface_s.json and exp32_immich.py, and the round-11 report. I did not re-run verify_paper_numbers.py. I re-derived by hand the Immich numbers, the Table I deltas quoted in the text, and all `\ref` targets (tab:acc, tab:corr, sec:method, sec:acc, sec:corr, sec:conseq, sec:time all resolve; no reference to Fig. 1 or any removed table remains; `sec:protocol` is unused, harmless; `\includegraphics` is no longer used, harmless).

## 1. Damage from the cuts

No broken sentence, no dangling Fig./Table reference. What was lost is mostly support and verifiability:

| Item | Where | Status |
|---|---|---|
| Abstract: "ties average linkage on average over the library conditions" | l.35-36 | The mean comparison is no longer stated anywhere in the body (see M1). |
| "14 to 69 times at 8,290 faces" | l.317 | The constrained-average-linkage times at 8,290 faces are no longer given (see M2). |
| "First-Leader" | Table I, l.171 | Never defined as a term (see m3). |
| Abstract's edit-log "53% and 31%" | l.41 | Still supported, l.295. |
| Abstract "within 0.003 F1 of constrained average linkage on all faces" | l.38-39 | Supported (0.9878 vs 0.9851 = 0.0027; others within 0.0011). |
| Conclusion: set-based claims, 0.9925 vs 0.985, "about half" for the upgrade, order of magnitude | l.337-341 | All supported in the body. |
| Proof sketch after cut | l.140-147 | Still complete and consistent with the Proposition (including "up to exact ties"). |
| Fair-tuning paragraph after cut | l.225-233 | Readable. Numbers consistent with the table. |
| Timing paragraph after cut | l.308-318 | Readable except M2 and m4. |
| FIW corrections paragraph | l.266-269 | Complete and readable. |

## 2. The Immich sentence (l.245) against exp32

What the file says: libraries 12, 6, 1 with 543, 585 and 642 photos; scored 396, 491, 565; no person assigned 147, 94, 77; Immich F1 0.9955, 1.000, 1.000 (mean 0.99849); ours on the same photos 1.000, 1.000, 1.000 (mean 1.000); ours on all photos 0.9994.

- "F1 0.998 on the photos it assigns to a person": correct (0.99849, rounds to 0.998).
- "against 1.000 for ours on the same photos": correct (mean_ours_same_photos_F1 = 1.0).
- "(543 to 642 photos)": correct.
- **"13--27% of the photos without a person": wrong at the low end.** 77/642 = 12.0%, 94/585 = 16.1%, 147/543 = 27.1%. It should read 12--27%. (The 12% is 11.99%, so "12" is right, not 13.)

Findings:

**M3 - Wrong percentage (l.245).** MAJOR only because it is a checkable number error in a sentence added late; fix in one character. Fix: "12--27%".

**M4 - The sentence sits in the FIW paragraph but describes LFW libraries (l.239-245).** The paragraph opens "Web family photos (FIW)" and the sentence says "three of the test libraries", which a reader will take as FIW libraries. The experiment is on clean LFW libraries (the JSON protocol says so). Fix: move it to the end of the previous paragraph (after l.237) and write "three of the LFW test libraries (the smallest, clean condition)".

**m1 - Fairness framing needs two qualifiers (l.245).** (a) The 12-27% without a person is probably by design rather than a recall failure: those photos are largely the one-photo "strangers" (50-150 per library), and, to my knowledge, Immich's default only names groups of at least three faces. The result file does not record the Immich version or the setting, and "no_person_assigned" also includes photos where no face was detected, so the cause is not separated. As worded, the sentence reads like a deficit. (b) Immich's F1 is computed only on the photos it assigns, so it is a precision-leaning subset score; ours on the same photos is a clean like-for-like subset (good), but it is also a whole-system comparison (Immich's own detector, recogniser and clustering vs SCRFD/EdgeFace/ours). Fix: "...scores F1 0.998 on the photos it assigns to a person (Immich version X, default settings; whole system, not the clusterer alone), against 1.000 for ours on the same photos; it assigns no person to 12-27% of the photos, mostly one-photo strangers, which we do not count as errors."

**m2 - Weak evidence base is not stated (l.245).** n = 3 libraries chosen as the smallest, no interval, and the whole gap (0.998 vs 1.000) comes from one library (library 12: 20 Immich people vs 19 true, a single split). The comparison is honest as worded (it does not claim a win), but "the three smallest" and "one library accounts for the difference" should be said, or the sentence will be read as a ranking. It is also not listed among the "additions" at l.150-151.

Verdict on fairness: the construction (same photos, nothing tuned, Immich defaults, centre-face heuristic, misses reported not penalised) is fair and conservative toward Immich; the wording is mostly correct once the percentage and placement are fixed.

## 3. Findings

### CRITICAL
None.

### MAJOR

**M1 - "ties on average over the library conditions" has lost its numbers (abstract l.35-36; body l.225-233).** Evidence: the body states ours' mean (0.9854, l.226) and per-condition deltas, but never the average-linkage mean (0.9857 in round 11), and Table I omits three of the eight conditions, so the average cannot be rebuilt from the paper. Fix: add "(mean over the eight conditions 0.9854 for ours, 0.9857 for average linkage)" at l.226-227.

**M2 - Unverifiable speed-up at 8,290 faces (l.316-317).** Evidence: "14 to 69 times faster at 8,290 faces" depends on constrained-average-linkage times at 8,290 faces that were cut; only ours (0.44 s) appears. Also 234/15 = 15.6 and 174/20 = 8.7, so "9 to 15" at 49,740 should be "9 to 16". Fix: add the two 8,290-face times (about 6 and 30 s) or drop the 8,290-face ratio and say "9 to 16 times at 49,740 faces".

**M3, M4** above (Immich).

### MINOR

**m3 - "First-Leader" is never defined (Table I, l.171, 195, 241).** The intro says "leader pass"; a reader meets a capitalised method name. Fix: l.171 "First-Leader (the greedy leader pass of Sec. I, in the order photos arrive)".

**m4 - FAISS build (l.318).** "Building the flat FAISS index took 316 s at 49,740 faces" is odd: adding vectors to a flat index is near-instant, and 8,290 faces add in 0.9 s (l.309). Presumably the 316 s is index plus neighbour-list (range-search) construction. Fix: "Building the neighbour lists took 316 s" (check the experiment file first).

**m5 - Timing sentence ambiguity (l.310).** "with 10 and 50 corrections 4.5 and 5.1 s against 1.9 and 2.2 s" does not say which is original and which is exact. Fix: "(original merge 4.5 and 5.1 s, exact read 1.9 and 2.2 s)".

**m6 - c-avg paragraph is a run-on with a non-sequitur "so" (l.253-255).** "...better for all three users ... so on all faces the two are within 0.001..." The "so" does not follow, "-0.000" is an odd interval bound, and the error-prone clause repeats l.258-259. Fix: "On the new photos alone constrained average linkage is ahead for all three users (by 0.0014, [0.0002,0.0026] for the precise user; 0.0057 for the error-prone user); on all faces the two are within 0.001 for the precise and casual users."

**m7 - Local-first parenthesis (l.55).** Fine now and unchanged; ignore. (Listed to confirm it is resolved.)

**m8 - Placeholders and URL (l.17-28, 77, 350-352).** Author block, "URL to be added", "Author contributions: to be completed" remain. Submission checklist, not content.

**m9 - Abstract length.** About 235 words by my count (down from 265), still dense with numbers; acceptable but the first thing to trim if lines are needed.

## 4. Page estimate (candid)

Base facts: the user's compile of 75c87ec gave 7 pages. Round-11 model predicted 6.0-6.15 for that commit, so the model was slightly optimistic (the spill is at least 1 line; probably a handful to 20). Since then: figure and caption removed (about -16 to -18 lines), prose cut by about 800 characters net after adding the Immich sentence (about -15 lines on the user's count, 24,900 to 24,400), references 43 to 42 (about -2 lines). Net about -33 lines relative to the 7-page build.

Versus the last known 6-page build (cef2e0f, about 5.4 pages, about 70 lines of slack): prose +2,600 characters (+46 lines), references +5 to +6 entries (+14 to +18 lines), tables -20 lines (Table III gone, Table I shorter): net +40 to +44 lines, leaving about 25 to 30 lines (roughly 0.2 page) of slack.

Both routes point to a build at about 5.9 to 6.05 pages. I put the probability that it fits on exactly 6 pages at about 60%. The main risks that the models do not capture: `table*` placement (Table I is a `[t]` two-column float and can be pushed a page, leaving white space), and the page-6 bibliography breaking. If it is still on 7 pages the spill will be small (under 15 lines). Compile on Overleaf first; apply cuts only if needed, and add a margin of about 10 lines if the compile is close.

### Ranked further cuts (lines saved, lowest value first)

1. Discussion "What the results show" (l.322-325): repeats Sec. V-B and V-C; keep one sentence on the sweep (the first sentence repeats l.296) [4-5].
2. FIW corrections paragraph (l.266-269): shrink to "On FIW ours keeps all corrections (plain re-clustering 26%), gains +0.0089 over discarding them, re-applying holds 86%/40% and constrained average linkage ties" [3].
3. c-avg paragraph (l.253-255), as m6; also drop "ours is +0.001 F1 on all faces ([-0.000,+0.002])" [3].
4. Reference trims: `wu2013constrained`, `cui2007easyalbum`, one of `gower1969mst`/`sibson1973slink`, with their text clauses (l.86-87, 61-63, 94-95) [5-6]. Keep `tian2007face`; the text says "established, and we claim none of them".
5. MBF clauses in V-A (l.232-233 and l.243, "MobileFaceNet agrees ...") [3]; keep the CPLFW 13-point MBF gap if you want to keep the candour, drop the CALFW and occluded MBF numbers.
6. Deletion paragraph (l.310-311): collapse the 15-case sentence to "15 further deletions with 7-10 binding corrections gave labels identical to a rebuild in all 15" [2].
7. Ethics and declarations (l.350-352): merge the FIW sentence and the license line; drop "the released files hold only scores and anonymous indices" [2].
8. Abstract: drop the edit-log parenthesis (l.40-41, repeated in Sec. V-C) [2].
9. Recogniser upgrade: delete "The other direction gives 48%: ..." [1].
10. Table I caption: delete "Bold: best. Last row..." clause or the "four methods are within 0.004" clause [1-2].

Items 1-4 alone give about 15 lines; do not cut Table II, the proof sketch or the Immich result. If the compile is under budget by a few lines, apply only 1 and 3.

## 5. What is fine
- No dangling Fig. 1 reference; no orphaned or undefined `\ref`; all remaining sentences parse.
- The Immich numbers (0.998, 1.000, 543-642) match exp32; the experiment script does what the sentence claims (same photos, no tuning, centre-face rule, misses excluded and counted).
- Abstract, conclusion and body agree on the central numbers and on the limits (simulated users, our own frozen baseline, "untested" review-and-undo view).
- Table II is complete and consistent with the text (0.9925/0.9920/0.9851 vs 0.985; 0.9878; 20%/23% held).
- Fair-tuning, CPLFW (7 points lower), the sweep and the deletion test remain honest and bounded.
- The novelty note is dated and bounded; ethics, AI disclosure and licence statements are consistent.
- The Proposition and its sketch still match each other after the cut.

## 6. Recommendations
- **Journal-Fit Reviewer: minor revision, conditional on a compiled 6-page build.** Blockers: Overleaf page count, placeholders (m8), M3. Confidence 3/5 (no compile).
- **Domain Reviewer: weak accept.** Fix M1, M2, M3, M4, m1, m4. Confidence 4/5.
- **Perspective Reviewer: weak accept.** The Immich sentence improves practical relevance; add the version, say "whole system", and the 12-27% context (m1, m2). Confidence 3/5.

No new experiments needed, except recording the Immich version and min-faces setting from the server that produced exp32.
