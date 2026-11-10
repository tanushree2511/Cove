## Journal-Fit Review Report (round 4)

### Reviewer Identity
Programme-committee member, IEEE India regional computing conference (6 pages); simulated seat `eic`. Read: the round-4 card file, the round-3 decision and my round-3 report; no other round-4 report. Manuscript at ab09dbe, uncompiled. Read-only checks: word counts; exp14 and exp19-exp25 JSONs against the text.

### Short answer: publishable after a cut to 6 pages?
Not by cutting alone; after an edit, yes, with no new experiment. The science is sound and candid, but the cut must follow one story (about 30% of the text goes), the abstract must carry only numbers that match the body (W5), and the blockers must clear (W3, W4).
I would reject it for: (a) desk-reject items if sent today (over length, placeholders, an untrue integrity sentence); (b) a cut that keeps the abstract's mismatched numbers; (c) on merit, only if the committee finds "recompute from the set" too thin: a one-line corollary, two of three consequences true by construction, simulated users, no correction interface or sync in the app, a cost edge measured against the authors' own NumPy code. At a regional venue I would not reject on (c).

### Criterion-Bound Judgements
| Dimension | Judgement | Anchor and reason | Decision bearing |
|---|---|---|---|
| Journal fit | MEETS | text: Sec. I "People most often search a personal photo collection by person"; applied, CPU-only, code release claimed | No |
| Originality | PARTLY_MEETS | text: Corollary "Any method that recomputes from the sets has (i) and (ii)"; parts known, measurement new | Yes |
| Significance | PARTLY_MEETS | table: Table II; accuracy ties, value lies in the properties | Yes |
| Length/format | DOES_NOT_MEET today | absence: see W2 | Yes |
| Disclosure | PARTLY_MEETS | text: Acknowledgment; see W3 | Yes |

### Summary Assessment
The paper makes face grouping a pure function of the set of faces and corrections, and measures the consequences: corrections survive imports (100% against 20%), devices that swap sets agree (100% against 53% for frozen labels), a wrong correction is retracted exactly, and about half the gain survives a recogniser change. Accuracy ties constrained average linkage and an Immich-style rule, as the body says. The round-4 experiments answered the round-3 roadmap. What remains is framing, length (about two pages over), six abstract and conclusion mismatches, and open integrity items.

### Round-3 items
- Fixed: cost against constrained average linkage now measured (exp24 matches); Table II rows; "ties" wording (frozen rule still run for the precise user only).
- Open: "provably" and the title; page fit (worse: body grew from about 4,100 to 5,130 words); the "checked the numbers" sentence and placeholders; "seven baselines", "abstracts only", "significantly".

### Strengths
1. **S1 Candid sizing in the body**: ties are called ties, losses reported (CPLFW -6.8 points). Evidence Anchor: text: Sec. V-C "so we call the two tied, not ours ahead"
2. **S2 One real organising idea**, with three measured consequences. Evidence Anchor: text: Sec. III-C "labels are a function of the set of faces"
3. **S3 Numbers hold**: Tables II-III and the text match exp19 and exp21-exp25 on every item checked. Evidence Anchor: table: Tables II-III against the JSONs
4. **S4 The most useful finding is a limit.** Evidence Anchor: text: Sec. VI "beyond roughly one wrong correction in twenty the gain is gone"

### Weaknesses
1. **W1 One idea, presented as a list.** The idea sits only in the Corollary and the first Discussion paragraph. The abstract gives eight results in eight sentences; the Introduction has four equal bullets, the first still selling "provably" and "ten times faster", the last the seven-baseline study and pose result from before the corrections story; Sec. V has seven equal subsections, four (A, B, E, F) not about corrections. Fix: open the abstract and Introduction with one sentence (corrections persist, devices that swap sets agree, a wrong one is removed exactly; accuracy ties constrained average linkage, which updates far slower); make the other bullets its evidence; keep V-C and V-D as the spine.
   - **Severity**: Major | **Evidence Anchor**: text: Sec. I "a clusterer that combines them so that both problems are solved at once" | **Confidence**: 4 (core: contribution sizing)
2. **W2 Page budget underestimated**: about 8 pages against 6 (see Page fit).
   - **Severity**: Major | **Evidence Anchor**: absence: whole manuscript — expected a compiled PDF with a page count; checked cove_paper.tex, the paper/v2 listing, no TeX binary | **Confidence**: 3 (estimate; a compile decides)
3. **W3 The AI-disclosure sentence is not yet true.** The paragraph is in the right place and names the tool, but round 3 flagged this sentence and mismatches remain (W5; the editor counts about 8.2 corrections per library, not "twelve", in Sec. V-G). It gives no model version or dates and does not say which sections were AI-drafted; as I recall, IEEE policy asks for both (check the current wording and the conference's AI and similarity rules). Fix: do the check, then keep the clause; add model, dates and "all sections drafted by AI, edited by the authors"; reword "simulated peer review" as "role-prompted AI self-review".
   - **Severity**: Major | **Evidence Anchor**: text: Acknowledgment "checked the reported numbers against the released per-run results" | **Confidence**: 4
4. **W4 Unfinished fields.** Placeholders in both author blocks; "Author contributions" open. "Released" code has no URL; l.257 cites an internal path. The three new bib entries and about ten older ones lack volume, pages or DOI; `jung2025posetta` is uncited. Fix: fill, compile on Overleaf, add a URL, complete the references.
   - **Severity**: Major (administrative) | **Evidence Anchor**: text: l.19 "[College name]"; l.502 "to be completed by the authors" | **Confidence**: 5
5. **W5 Headline sentences that do not match the body** (Minor each; rows 1-2 touch the one remaining edge over constrained average linkage).

   | # | Where | Says | Data say | Fix |
   |---|---|---|---|---|
   | 1 | Abstract l.41-42 | "261 s instead of 1.3 s" | 261 s is zero corrections, 1.3 s is ten (0.3 s with zero); Sec. V-G also gives 1.9 s for that step (exp20 and exp24 runs) | Matched pair, one run: 293 against 1.3 |
   | 2 | Sec. V-C; Conclusion l.485 | "two orders of magnitude" | NumPy 229x-827x; compiled unconstrained average linkage, 16.7 s (Sec. V-C), gives 13x-53x | "One to two orders"; give 16.7 s |
   | 3 | Abstract l.41 | "within 0.002 F1" | Error-prone user -0.0027 (new faces -0.0057) | "within 0.003" |
   | 4 | l.487 | "past about one in twenty they cost more than they gain" | exp25: +0.0009 (5%), +0.0010 (10%), intervals include 0; negative only at 20% | "gain gone at 5-10%; negative at 20%" |
   | 5 | Abstract l.43 | "all 240 libraries" | 30 libraries x 8 conditions | "240 library-condition pairs" |
   | 6 | Abstract l.39; Intro l.77, 85 | "within about one point"; "ten times faster"; "seven baselines" | CPLFW -6.8 (MBF occluded -2.6); 9.7x only without corrections, 2.3x with; six baselines plus one ablation | Qualify; fix counts |

   Also: re-applying beats ours from 5% wrong clicks (exp25: +0.0039 against +0.0009 at 5%; +0.0037 against +0.0010 at 10%), and constrained average linkage keeps +0.0028 and +0.0027. The sweep text gives these rivals only at 20%. Add them; that is the honest size of "corrections as constraints".
6. **W6 Title names the method, not the contribution.** Order invariance is shared by single, average and constrained average linkage; "Incremental" is the weakest word (reading labels dominates update cost, Sec. V-G). Suggest "Keeping, Reconciling and Retracting User Corrections in Local-First Face Grouping" ("syncing" would over-claim).
   - **Severity**: Minor | **Evidence Anchor**: text: Title "Order-Invariant Incremental Clustering" | **Confidence**: 4
7. **W7 Small effects, strong words.** Limitation (iv) admits the intervals are "likely too narrow", yet Sec. V-B says "significantly" at +0.002 and Tables I-II bold the best cell at the third or fourth decimal. Fix: "slightly higher"; add a tie rule (under 0.003) to the captions.
   - **Severity**: Minor | **Evidence Anchor**: text: Sec. V-B "ours is significantly better on clean" | **Confidence**: 4
8. **W8 Novelty claim rests on abstract-level search.** Say "to our knowledge"; read C-DBSCAN, Davidson 2007, Zhu 2016, Grinch and FaceCluster in full first.
   - **Severity**: Minor | **Evidence Anchor**: text: Sec. II "abstracts only" | **Confidence**: 4

### Page fit (estimate, not a compile)
Body 5,130 words, abstract 245, three tables, 46 references. The earlier six-page Cove PDF in `paper/` holds about 800 words per full text page (round 3 assumed 950). I estimate 7.3-8.7 pages with references (about 8), 6.4-7.6 without; the card's 6.5-7 is optimistic. For 6.0 with references inside, cut about 1,500 words and 8 references; with references outside, about 850 words. Cut in this order:
1. V-E and V-F (217 words) to one sentence each: -180.
2. Privacy paragraph: fix Docker ports and CORS in code, keep two sentences: -100.
3. Protocol "Corrections" paragraph, 474 to 250: -220.
4. Related Work, 432 to 260: -170.
5. Limitations, 246 to 140; delete "Video tracks": -135.
6. Table I to one column, 5 methods x 6 rows: -0.2 page.
7. Declarations into the Acknowledgment; abstract to 190: -100.
8. Introduction to 300; tighten V-B, V-C, V-G: -370.

Keep V-C, V-D, the error-rate sweep and the simulated-user and app-gap limits; a small plot of gain against wrong-click rate could replace the sweep numbers. Drop references used only by cut text (AgeDB, CFP, GhostFaceNets, Daniels, Van Craenendonck, Song).

### Detailed Comments
**Journal Fit.** Suits the audience. The text is dense (11 numbers in the abstract, about 18 intervals, no figure); lead with the single message.
**Originality and Significance.** Honest and modest. F1 effects of 0.001-0.005 are ties (a handful of faces per library) and cannot carry a paper. The discrete properties can (100% against 20%, 100% against 53%, exact against 5%, about half after an upgrade), enough for a regional venue. Two hold by construction, so lead with the measured parts: frozen-rule gaps, retention ratio, the break-even near 5% wrong clicks.
**Coherence, Title, Abstract, Conclusion.** Title, abstract and conclusion agree on the method but disagree with the body on cost and error tolerance (W5). Echo the first Discussion paragraph up front; aim for a 200-word abstract with at most 8 numbers.

### Questions for Authors
1. Do the six pages include references, and is a paid extra page possible?
2. In one sentence, what should a reader remember?
3. Have you checked the conference's AI-content and similarity rules, given this disclosure?

### Minor Issues
- Sec. IV "All rules below were fixed before any test number was computed": restrict to the tuning and recogniser rules; the corrections protocols came after earlier rounds on the same libraries.
- Table II caption: explain "--". Table III: move the n/r column to a sentence. "Can never revisit an earlier grouping" (Sec. V-C) is unmeasured.

### Recommendation
**Major Revision.** For framing, length and integrity; no new experiment is needed, and the content is publishable at a regional IEEE conference after the edit. Re-read the cut version to confirm the caveats survived.

**Confidence**: 4 (the page count is an estimate; the IEEE policy wording is from memory).

**Calibration status**: `NOT_CALIBRATED`

### Plain-language verdict for the student author
1. Your science is solid and unusually honest.
2. The draft is about 8 pages and the limit is 6: cut a quarter of the text, not a few lines.
3. Say your one idea at the top: the result depends only on the photos and corrections, so corrections stay, devices agree and mistakes can be undone.
4. Fix the abstract numbers (261 s against 1.3 s, "within 0.002", "one in twenty") and fill the blanks before keeping the "checked the numbers" sentence.
5. You need an honest edit and an Overleaf compile, not new experiments.

### Top 3 issues
1. Page budget (W2): about 8 pages against 6.
2. One idea and matching numbers (W1, W5, W6).
3. Integrity and housekeeping (W3, W4).
