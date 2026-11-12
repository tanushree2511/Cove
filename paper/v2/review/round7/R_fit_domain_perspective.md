# Round 7 re-review (simulated): Journal-Fit, Domain, Perspective. Commit 8c28a83

Not compiled; page count is estimated from content. Bib check: 38 cited keys, none missing, 12 uncited (BibTeX drops them). All \ref labels resolve; both figure PDFs exist.

## Round-6 issues
**Journal-Fit**
- Placeholders: not counted as defects.
- Length (fig/table/Declarations): PARTLY. Fig count is 3 to 2, JPEG row gone, Declarations merged. Mixed row, Related Work and the Discussion repeats stay.
- Undefined First-Leader/Two-stage/no attach: FIXED (Table I caption). Caption is now long.
- Sweep vs error-prone user: PARTLY. "This agrees with the sweep" is there, but the look-alike targeting is not given as the reason.
- c-avg timing sentence: PARTLY. Still one long parenthetical. The abstract lacks "our implementation".
- 1,571 identities: FIXED ("distinct identities in the test libraries").
- Frozen sign: FIXED ("within 0.0003", plus 0.009 below with MBF).
- Disclosure: PARTLY. It says numbers were script-checked but not that references and code were checked.
- Plain-language note on small differences: NOT FIXED. Nowhere says +0.01 F1 is near the ceiling.
- N1 (abstract "within one point ... by 7"): FIXED.
- N2 (c-avg new-photo sentence): NOT FIXED. "it is better" is unclear, and "tied" fits badly with an interval that excludes zero.
- N3 ("gains 5.2" on CPLFW): NOT FIXED. Table I gives 0.892 - 0.841 = 5.1.
- N4 (210-216, 1,276): PARTLY. "Separate run" added; "cases" still undefined.
- N5 (16-69x): FIXED. 30.4/0.44 = 69 and 19.6/1.25 = 16.
- N6 (p=0.02): PARTLY. The value (+0.0034) is printed but its interval is not, yet the Discussion says "clear".
- N7 (frozen "within 0.003"): FIXED.
- N9 (look-alike number): NOT FIXED.
- N10 (abstract dense, ~235 words): NOT FIXED.

**Domain**
- M1, M2, M5, M6: FIXED. "Recomputes steps (1)-(4) from scratch" is now stated.
- M3 (Avg-linkage baseline is over faces, ours over centroids): NOT FIXED.
- M4 ("converge"): FIXED. It now says "agree". Float32 differences across CPUs are still unmentioned: PARTLY.
- m1 (tie rule): PARTLY. Steps (1) and (2) now use different tie rules, so the proof and text agree. "Content" is undefined, and Contribution 1 lacks "up to exact ties".
- m3, m6, m8, m9, m11: NOT FIXED. Uncited: ArcFace and MobileFaceNets, so MBF is uncredited.
- m10 (SLINK): PARTLY.
- N1 (Incremental DBSCAN deletion): FIXED.
- N2 (bandyopadhyay2016axioms): NOT FIXED. The bib title is "Axioms to Characterize Efficient Incremental Clustering" but the text says "order-independent". Reword.
- N3 ("single linkage" in Related Work): FIXED.
- N4 (Kobren): NOT FIXED.
- N5 (Immich 0.5 threshold): NOT FIXED. The entry is a repo link and does not support the number.

**Perspective**
- Issues 1-10, 12: FIXED or MOSTLY FIXED.
- Issue 11 ("up to exact ties" in bullet and abstract): NOT FIXED.
- N1 (one wording for the error-rate result): PARTLY. Abstract says "one in twenty"; Discussion says "five to ten".
- N2 ("should accompany", "natural companion", Conclusion "should come with"): NOT FIXED.
- N3: FIXED.
- N4: PARTLY (see m1).
- N5 (ethics sentence): NOT FIXED. It still reads "public benchmark data only".
- N6 (embedding exchange privacy): PARTLY. Consent is stated; no encrypted-exchange note.
- N8 ("Cove system studied here group faces"): NOT FIXED.

## New issues from the edits
- MAJOR (verify): Table I Two-stage equals Avg. linkage to 3 decimals in Low-res, Mixed and Occluded (0.986, 0.981, 0.952), yet Two-stage order agreement is 0.758 and linkage is 1.000. Check against the per-run results for a copy error.
- MINOR: the proof says "3-5 orders"; the protocol says 5.
- MINOR: ours with ten corrections at 8,290 faces is 1.9 s in one place and 1.25 s in another. The "factor of two" note does not cover this gap. Without corrections it is 0.5 s vs 0.44 s.
- MINOR: "9 to 15 times" at 49,740 faces. 234/15 = 15.6, 174/20 = 8.7, so "9 to 16".
- MINOR: Table I caption is about 4 lines, and the order-agreement line is mixed into it. Move the definitions into the text.
- MINOR: "210 pairs" appears twice for different things (corrections run, upgrade libraries).
- MINOR: Table I has 8 condition rows plus the order-agreement row, not 7.
- MINOR: Immich and PhotoPrism are described as "local-first". They are self-hosted.

## Page estimate
About 4,300 prose words at 850-950 words per page is 4.5-5.0 pages. Add about 0.2 for the title block, 0.35 for two figures, 0.25 for Table I, 0.1 for Table II, 0.15 for headings and the Proposition, and 0.7-0.8 for 38 references. Total is about 6.3-6.9, most likely 6.6. Six pages is not plausible as it stands. Need to cut about 0.6 page.

Cuts, ranked by saving:
1. Drop Fig. 2 (sweep). Every p value is already in the text. Saves about 0.13 page (about 14 lines).
2. Halve the Sec. V-D scale paragraph and the "Exact read step" validation sentence. Saves about 150 words (about 17 lines).
3. Delete the Method "Consequences" paragraph (repeated in V-C and Discussion). Saves 75 words (about 9 lines).
4. Cut the Discussion "What the results show" to two sentences. Saves about 100 words (about 11 lines).
5. Trim the fairer-tuning and bootstrap detail in V-A. Saves about 80 words.
6. Cut the Mixed row and the Table I caption definitions (move to text). Saves about 4 lines.
7. Remove mazumdar2017noisy and trim Related Work. Saves about 3 lines.
8. Trim abstract by 30 words. Saves about 4 lines.
Items 1-4 alone are about 50 lines, or about 0.5 page. Items 5-8 give another 0.1 page. Confirm on Overleaf.

## Recommendation
- Journal-Fit: minor revision, mainly for length. Confidence 3/5.
- Domain: weak accept (minor revision). Confidence 4/5.
- Perspective: weak accept (minor revision). Confidence 4/5.
No CRITICAL issues. One MAJOR: verify the Two-stage table cells. The page limit is also a MAJOR in practice.
