# Round 13 review (simulated): Journal-Fit, Domain, Perspective. HEAD 9e879fc

Read-only. No TeX is installed here (no pdflatex, latexmk or tectonic), so nothing was compiled; the page estimate is a model, not a measurement. I read the full .tex (l.1-356) and compared it with the round-12 report. I checked citations by script: 40 distinct keys are cited and none is missing from references.bib (13 bib entries are uncited and do not print). I recomputed the Immich numbers from exp32_immich_edgeface_s.json: 147/543 = 27.1%, 94/585 = 16.1%, 77/642 = 12.0% unassigned; 302 of 318 unassigned photos (95%) belong to one-photo identities; version 3.4.1 is recorded. I recomputed the Table I deltas quoted in the text. I did not re-open the bib entries or re-run verify_paper_numbers.py.

## 0. Round-12 items now resolved (not repeated)
- Immich percentage (12-27%), version and "default settings", and placement in its own paragraph are done.
- The mean over the eight conditions (0.9854 / 0.9857) is now in the Table I caption (l.199), so the abstract's "ties on average" can be rebuilt.
- First-Leader and Two-stage now have definitions, but only in the Table I caption (see m1).
- The c-avg paragraph, FIW-corrections paragraph and Discussion were shortened. Every `\ref` target resolves (tab:acc, tab:corr, sec:method, sec:acc, sec:corr, sec:conseq, sec:time). No Fig. 1 reference remains.

## 1. Findings

### CRITICAL
None.

### MAJOR

**M1 - Blank line inside `\author{...}` may stop the build (l.18-25, blank line at l.24).**
Evidence: l.23 ends the last row without `\\`, then l.24 is an empty line before `\end{tabular}`. A blank line is a `\par` token in the argument of `\author`. If IEEEtran keeps the standard non-`\long` definition of `\author`, LaTeX stops with "Paragraph ended before \author was complete". I cannot confirm IEEEtran's exact definition without a compile.
Fix: delete l.24 (zero cost) and compile once.

**M2 - Real author data will break the 0.19\textwidth columns and the page budget (l.18-23).**
Evidence: the header compiles only because the placeholders are short. Each column is 0.19 x 516 pt = 98 pt (about 22 characters at `\small`). A realistic address such as `firstname.lastname2022@collegename.edu.in` (about 40 unbreakable characters) will give an overfull box of 30 pt or more, and a college name will wrap to 2-3 lines. Each extra header line is a full-width line, which is worth about 2 column lines.
Fix: put emails in `\scriptsize\texttt{}` with `\allowbreak` after dots or `@`, or merge Dept. and College into one row; then re-measure with the real names.

**M3 - Page fit is unproven and near 50/50 (see Section 3).**
Evidence: the same size model that called commit 49e33e2 "5.9 to 6.05 pages" was followed by the author-block commits and a further "cuts for six pages" commit (a42b352), so a real compile apparently still overflowed. The current text is about 510 characters smaller than 49e33e2 by my count.
Fix: compile on Overleaf; if the last page is more than 3 lines over, apply the cut list in Section 3.

**M4 - The "9 to 15 / 14 to 69 times faster" sentence is unchanged since round 12 (l.313-315; carried).**
Evidence: the constrained-average-linkage time at 8,290 faces is not in the paper, so "14 to 69 times at 8,290" cannot be checked. At 49,740 faces the stated times give 234/15 = 15.6, 212/20 = 10.6, 174/15 = 11.6 and 174/20 = 8.7, so the range is "9 to 16". The abstract's "about an order of magnitude" is supported only at the lower bound, where one baseline is a compiled SciPy lower bound, not constrained average linkage.
Fix: write "9 to 16 times at 49,740 faces" and either give the two 8,290-face times or delete the 14-to-69 clause.

### MINOR

**m1 - First-Leader and Two-stage are used before they are defined (l.168, l.192; definition only in the Table I caption l.199).** The intro says "leader pass" but never names First-Leader. Fix: at l.168 write "First-Leader (a greedy leader pass in arrival order) and Two-stage (that pass plus the centroid merge)".

**m2 - "original merge" is undefined (l.116, l.307).** "It gave identical partitions to the original merge" does not say that "it" is the component split, and "original merge" means the plain centroid average linkage over all centroids. Fix: "The split gave identical partitions to the unsplit centroid merge".

**m3 - Abstract uses "re-applying" and "constrained average linkage" before defining them (l.39-40).** A reader of the abstract alone cannot tell what the comparison methods are. Fix: "re-applying corrections after clustering".

**m4 - Abstract "(an edit-log baseline of ours: 53% and 31%)" does not say 53% of what (l.37-38).** It means the share of 240 library-condition pairs on which two devices agree, for the two recognisers. Fix: "(a plain edit log agrees on 53% and 31% of 240 cases)".

**m5 - Garbled clause in the Immich paragraph (l.243).** "12-27% of the photos without a person, 95% of them people with a single photo" reads as if 95% of the people are single-photo. The data say 95% of the unassigned photos belong to one-photo identities. Fix: "95% of those photos are of people who appear once".

**m6 - The Immich paragraph does not say it compares whole systems (l.243).** Immich uses its own detector, recogniser and clustering, against SCRFD/EdgeFace plus ours. It also rests on three libraries, and the whole gap comes from one split (library 12, 20 Immich people vs 19). The text is honest ("say nothing about corrections, order or scale"), and it is not listed among the "additions" at l.147-148. Fix: add "whole system, not the clusterer alone" and "Immich" to the additions list.

**m7 - Rounding in the c-avg sentence (l.251, Table II).** "Within 0.001 F1 for the precise and casual users" - the precise gap is 0.9925 vs 0.9914 = 0.0011 in the table. Fix: "within 0.0011".

**m8 - Discussion wording "stay positive to ten" is ambiguous (l.322-323).** It mixes "in a hundred", "in twenty" and "ten" without a unit; re-applying is positive to 0.20, not 0.10. Fix: "stay positive up to 10% (c-avg) and 20% (re-applying) wrong clicks".

**m9 - Table I width is tight (l.206).** My estimate of the header widths at `\small` with tabcolsep 5 pt is about 520 pt against a 516 pt text width, so an overfull warning of a few points is possible. Fix: `\setlength{\tabcolsep}{4pt}`.

**m10 - FAISS build (l.316; carried).** "Building the flat FAISS index took 316 s" sits beside "8,290 faces added in 0.9 s". It is probably the neighbour-list construction. Fix: check the experiment file and name what was timed.

**m11 - "Against single linkage ours is better on every condition by 0.2 to 14 points" (l.227).** Three of the eight conditions (JPEG, mixed, look-alike) are not in Table I for single linkage, so "every" cannot be checked from the paper. Fix: "on every condition shown".

**m12 - Submission blockers, not content (l.17-23, 349-350).** Placeholders for authors 3-5, "URL to be added" and "Author contributions: to be completed".

## 2. Domain, journal-fit and perspective checks

**Claims against evidence.** Abstract, body and conclusion agree on: tie with average linkage (mean 0.9854 vs 0.9857, 7 points lower on CPLFW), FIW tie (0.786 vs 0.785), correction retention (100% vs 20%), within 0.003 of c-avg (0.0027 at most), the 0.05 error-rate crossover, and device agreement (240/240 vs 53%/31%). The declarations match the body on FIW terms and AI use. The proposition and its proof sketch still match each other, including "up to exact ties".

**Terms.**
- Standard or defined at first use: ARI (expanded l.162, cited), B-Cubed (cited, standard), core and attach (l.103-105), frozen (l.179), tombstones (l.329), order agreement (l.169), must-link and cannot-link (standard, restated l.125).
- Defined late or loosely: First-Leader and Two-stage (m1), "original merge" (m2).

**Cuts.** I found no broken or ungrammatical sentence except the Immich clause (m5). The Discussion is not gone (l.319-332), it is two short paragraphs.

**Ethics and privacy.** FIW terms (non-commercial, no redistribution, no image shown) are stated at l.159 and l.349, and the embedding-as-biometric statement and tombstone deletion are at l.331-332. The model licences are stated (l.350-351). One duplication: FIW terms appear at l.159, l.348 and l.349. Nothing to add; if a line is needed, merge them.

**Perspective (practitioner).** The paper is candid that the users are simulated, the frozen baseline is its own design, and "review and undo" is untested. The Immich result helps a self-hosting reader but is deliberately not framed as a win. A reader who does not know Cove still gets what they need, since only the clusterer is in scope.

## 3. LaTeX and page estimate (candid)

**Author tabular.**
- `\usepackage{array}` is loaded (l.8), so `>{\centering\arraybackslash}p{...}` is valid. A tabular inside `\author` in IEEEtran conference mode is legal and common.
- `\small` and `\setlength{\tabcolsep}{2pt}` inside the argument are scoped to the title block.
- Width: 5 x 0.19 x 516 = 490 pt + 10 x 2 pt = 510 pt, under 516 pt, so five columns render side by side with about 6 pt to spare and no overfull with the placeholder text.
- Two risks: M1 (blank line) and M2 (real data).
- The `\IEEEoverridecommandlockouts` line is unrelated and harmless.

**Page estimate.**
- By my own count (prose characters, tables and author block excluded) the sizes are: cef2e0f (6 pages) 22,328; 75c87ec (7 pages) 26,107; 49e33e2 25,195; 872823e 25,564; a42b352/HEAD 24,685. The user's figures (21,800 / 24,900 / 24,400) give the same ranking at a lower baseline.
- Relative to cef2e0f: +2,357 characters (about +40 lines at about 58 characters per column line), 2 tables instead of 3 (Table III gone, about -15 to -20 lines), no figure in either, about 3 to 5 more references (+6 to +10 lines), and a five-author header that is probably 1-2 lines taller (+2 to +4 column lines).
- That leaves roughly 0 to +15 lines of slack against the old 6-page build, with an error of at least 10 lines either way.
- I put the probability of exactly six pages with placeholders at about 50%, and about 35% once real affiliations and emails are in. Remaining risk factors: `table*` is `[t]` and can be pushed to the next page, and the last bibliography page can break badly.

**Ranked cut list (lowest value first; lines are column lines).**
1. Discussion "What the results show" (l.320-323): repeats Sec. VI-B/C and the Conclusion; keep the one sentence about the sweep. About 4 lines.
2. MBF clauses (l.229-230 CALFW/occluded numbers; l.240 "MobileFaceNet agrees ..."); keep the 13-point CPLFW gap. About 3 lines.
3. Declarations (l.348-351): merge the three FIW-terms mentions and drop "the released files hold only scores and anonymous indices". About 2.5 lines.
4. Table I caption (l.198-200): drop "Bold: best. Last row ..." and "four methods are within 0.004". About 1 full-width line, which is 2 column lines.
5. FIW corrections paragraph (l.265-267): one sentence. About 2 lines.
6. Reference `gower1969mst` or `sibson1973slink` (keep one) with its clause (l.91-92). About 2 lines.
7. Author block: merge Dept. and College into one row ("Dept. of CSE, [College]"). About 1 full-width line, so about 2 column lines.
8. Abstract: drop "(an edit-log baseline of ours: 53% and 31%)" and "(untested)". About 1.5 lines.
9. Deletion sentence (l.309): "15 further deletions with 7-10 binding corrections gave labels identical to a rebuild in all 15". About 1 line.
10. Recogniser upgrade: "The other direction gives 48%." About 0.5 line.

Items 1-7 give about 17 lines. Do not cut Table II, the proof sketch, the Immich result or the sweep numbers.

## 4. What is fine
- All citations resolve; no `\ref` is dangling; no removed figure or table is still cited.
- Immich numbers, Table I deltas, and the abstract/conclusion headline numbers match the data and each other.
- The limits (simulation, own baseline, bounded novelty search dated 2026-11-10, shared-people intervals, synthetic scale) are all stated.
- The five-column author tabular is valid LaTeX once the blank line is removed.
- AI-use disclosure, FIW terms, biometric-data warning and licences are present and consistent.

## 5. Recommendations
- **Journal-Fit Reviewer: minor revision, conditional on a compiled 6-page build.** Blockers: M1 (compile), M2/M3 (page fit with real author data), placeholders. Confidence 3/5 (nothing compiled).
- **Domain Reviewer: weak accept.** Fix M4 and m1, m2, m10, m11. Confidence 4/5.
- **Perspective Reviewer: weak accept.** The scope statements and the Immich paragraph are useful; fix m5, m6, m8. Confidence 3/5.

No new experiments are needed. The only data check is the 316 s item (m10).
