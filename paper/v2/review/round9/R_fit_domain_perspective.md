# Round 9 review (simulated): Journal-Fit, Domain, Perspective. Commit 05a693e
Not compiled (no TeX here; the stale Cove_paper.pdf of 10 Nov is 6 pages, before FIW). Checked: 40 cited keys, all in the bib, 12 uncited. All \ref labels resolve. Table I/II cell counts match their headers. Only pipeline.pdf is included. Re-checked Two-stage vs Avg. linkage in exp14_testruns_edgeface_s.json: genuine, not a copy error (low-res 0.9862 vs 0.9859, mixed 0.9811 vs 0.9808, occluded 0.9520 both).

## 1. Open items
Round 7: Mixed row/Discussion repeats PARTLY (Consequences paragraph and 2 figures gone, Mixed row stays). Fig. 2 sweep dropped FIXED. Plain-language "small difference" note NOT FIXED. c-avg new-photo "tied" PARTLY (now "so the two are tied, not ours ahead"). CPLFW "5.2" FIXED ("about 5"). p=0.02 interval NOT FIXED (+0.0034 printed without interval, Discussion still says "clear"). Two-stage table cells FIXED (genuine). "Look-alike number" NOT FIXED ("not distinguishable on look-alike" has no figure). Abstract length NOT FIXED (about 270 words, one 5-clause sentence). ArcFace/MobileFaceNets uncited NOT FIXED (MBF named, no \cite). Immich 0.5 threshold cites a repo only NOT FIXED. "Local-first" for Immich/PhotoPrism NOT FIXED. Ethics "public benchmark data only" PARTLY (FIW terms added).
Round 8: Libraries share families PARTLY (caveat added, no family bootstrap). Retuned gaps quoted FIXED. Two-stage/no-attach tie PARTLY (only in the caption: "four methods within 0.004"). Bold on FIW row FIXED. Discussion "all differences small" FIXED ("On the LFW libraries"). MBF FIW FIXED. Protocol names FIW FIXED. "probably because" FIXED. Excluded-crop F1 NOT FIXED. "Mostly of public figures" PARTLY (relatives may not be public). No singleton strangers in FIW libraries NOT FIXED. FIW bib "and others" NOT FIXED, TPAMI has no volume/pages. datasets/fiw/ in .gitignore FIXED.

## 2. New or remaining problems
- MAJOR (Perspective): Abstract and Contribution 3 say "on real family photos". FIW is web crops of celebrity families, with no albums, events or strangers. The paper says so in Discussion, but the abstract and the Table I caption ("real family photos") carry the stronger claim. Fix: "web-collected family photos (FIW)".
- MAJOR (Domain): the FIW interval claims (+0.0089, +0.0045, +0.0094, "ties") use libraries that share families. The paper admits "probably too narrow" yet still writes "[+0.0049,+0.0133]" to four digits. Fix: report the FIW corrections gains as "about 0.7-0.9 points" and drop the precision, or bootstrap over families.
- MAJOR (Fit): the FIW result is "ties" everywhere, yet the abstract sentence is stacked into "again ties" while the contribution list calls it an "outside test". State once in the Discussion that the attach step, the claimed source of the LFW gain, shows nothing on FIW (ours 0.786 vs no-attach 0.783).
- MINOR (Domain): "Immich's default threshold" is a cosine distance of 0.5 in its settings. Cite the docs or write "similarity 0.5, our reading of Immich's default".
- MINOR (Domain): OGMC "reduces order dependence" and Grinch under "constraints" (Grinch is incremental, with no must/cannot-link) are plausible but attributed from abstracts. Say "online" and move Grinch to "incremental".
- MINOR (Fit): undefined or late-defined terms: "tombstones", "Two-stage" (only in the caption), "overall" (0.9849), "look-alike" (absent from Table I), "union-find".
- MINOR (Fit): the Related Work novelty note ("sources searched ... mostly abstracts") is bounded and good, but the date "2026-11-10" is odd for a paper in review. Keep.
- MINOR (Perspective): privacy. Exchanging embeddings is flagged only as a consent issue. Add "embeddings can identify people and are treated as biometric data" (one clause). FIW includes minors and non-public relatives; Ethics should say "no FIW image is shown or shared; only derived scores". Also confirm that you accepted the FIW licence.
- MINOR (LaTeX): no unbalanced braces found. The unused \sec:protocol label and unused packages (multirow, xcolor) are harmless. A full-width table* [t] in Sec. V-A may float to the next page. Check on Overleaf.
- Bib fix (verify before use): robinson2016fiw: Robinson, Shao, Wu, Fu, ACM MM 2016, pp. 242-246. robinson2018fiw: Robinson, Shao, Wu, Liu, Gillis, Fu, TPAMI 40(11):2624-2637, 2018.

## 3. Page estimate
Prose about 3,900 words plus abstract 270. At about 950 words per column-page (body) that is 4.1 pages. Add abstract/title 0.35, Table I full width with a 4-line caption and 11 rows 0.30, pipeline figure 0.10, Table II 0.12, headings and the Proposition 0.15, references (40, 8 pt) 0.85. Total about 6.1-6.5 pages. FIW added about 0.25 page to the 6-page PDF of 10 Nov. Six pages is plausible only after cuts of about 25-35 column lines (about 0.4 page).
Cuts, ranked by lines saved:
1. "Fairer tuning" detail and people-bootstrap sentence in V-A: about 9 lines.
2. Second half of V-D (the 8 s / 316 s index build) plus the "twofold" sentence: about 7 lines.
3. Table I: drop the Mixed row, shorten the caption (JPEG, bold, order row) to 2 lines: about 4 full-width lines = 8 column lines.
4. Cut the two MBF FIW sentences (V-A, V-B) to one clause: about 5 lines.
5. Trim the abstract by 60 words (drop the 53%/31% and the "order of magnitude" clauses): about 5 lines.
6. Conclusion to 6 lines: about 4 lines.
7. Remove mazumdar2017noisy and trim the Declarations licence sentence: about 3 lines.
Items 1-5 are about 34 lines.

## Recommendation
- Journal-Fit: minor revision (length, abstract). Confidence 3/5.
- Domain: weak accept; fix FIW interval precision and the bib. Confidence 4/5.
- Perspective: weak accept; soften "real family photos", add the embedding-privacy clause. Confidence 4/5.
No CRITICAL items. Three MAJOR (FIW framing, FIW interval precision, FIW null result placement) plus the page limit.
