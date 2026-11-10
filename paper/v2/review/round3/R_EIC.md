## Journal-Fit Review Report (round 3)

### Reviewer Identity
Programme-committee member of an IEEE India regional or national computing conference (6-page limit). Seat: Journal-Fit Reviewer (internal id EIC). Role-separated simulated seat; it read only `00_reviewer_cards.md` from the round-3 folder and no peer report. Manuscript: `paper/v2/cove_paper.tex` at commit ef69690; not compiled (no LaTeX on this machine).

### Overall Recommendation
**Minor Revision** (borderline Major). A publishable contribution remains at this venue, but only if the paper is re-sized as an honest evaluation study rather than as a new method. Several mechanical defects (one table that will not typeset, a disclosure sentence not yet true, unresolved placeholders, an unmeasured page budget) must be fixed before submission.

### Confidence Score
4. Core field is applied computing and venue fit. I checked numbers against the JSONs only where they bear on journal fit, and I did not re-run any code.

### Calibration Status
`NOT_CALIBRATED`

### Criterion-Bound Judgements
| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Journal fit (topic, readership) | Card: IEEE India regional computing conference | MEETS | text: Sec. I "People most often search a personal photo collection by person" | Applied, local-first, CPU-only face grouping with released code suits a regional applied-computing audience. | Conference's own call for papers not seen. | No |
| Originality | Eic_agent Step 2 | PARTLY_MEETS | text: Sec. III-B "the method is then single linkage, plus attachment at"; table: Table II | Parts are known and the paper says so. At the tuned setting the new guarantee is a connected-components property. Accuracy equals constrained average linkage and the frozen rule. What is new is the measurement of correction survival and the negative results. | Novelty scans not re-run. | Yes (claim sizing) |
| Significance | Eic_agent Step 3 | PARTLY_MEETS | table: Table II (differences of 0.001 to 0.003 F1); text: Sec. V-C | Useful to builders of local photo managers. Effect sizes are small and rest on simulated users. | Real-user value untested. | Yes |
| Structural coherence / over-promising | Eic_agent Step 4 | PARTLY_MEETS | text: Intro bullet 1 "is provably independent of the"; text: Sec. V-F "an update therefore costs about as much as re-clustering from scratch" | Title, abstract and conclusion lead with "order-invariant incremental", which Sec. V-F undercuts. | None | Yes |
| Length / format fit | Venue 6-page limit | PARTLY_MEETS | absence: whole manuscript — expected a compiled page count; checked .tex, revision log | Estimate 6.2 to 6.7 pages; Table II markup is broken. | Estimate only. | Yes |
| Disclosure / integrity | IEEE AI-content policy | PARTLY_MEETS | text: Acknowledgment "The authors directed the work, chose what to keep, and checked the reported numbers against" | Location and content are right. One claim is not yet true (see W5). | Conference's own AI policy unknown. | Yes |
| Round-2 issue resolution | `EDITORIAL_DECISION.md` against `REVISION_LOG_round3.md` and paper | MEETS (7 of 7 consensus items addressed; 2 only partly) | see "Round-2 verification" | Fair baselines, pooled statistics, noisy user, prior art, constrained-path timing and number fixes are real and match the JSONs. | I did not recompute every bootstrap CI. | No |

### Summary Assessment
The paper describes a face clusterer for local photo libraries that keeps the user's must-link and cannot-link corrections and gives the same people for any import order. After the round-2 fixes the evidence is clear and honestly reported. Without corrections it is within about one point of average linkage on degraded photos and 6.8 points worse on profile faces. With corrections it keeps all of them, but constrained average linkage and an Immich-style frozen rule match its accuracy. Plain re-clustering loses most corrections. A re-apply rule is clearly worse only for a user who clicks arbitrary faces. A user who sometimes makes a wrong "same person" correction wipes out the gain for every method that enforces corrections.

The part worth publishing is the evaluation: correction survival measured against fair baselines, three user models, two reported negative results, and an identity-disjoint protocol. That is a sound contribution for a regional applied conference, and the paper's candour is its best feature. The part that is oversized is the method framing. The title, abstract and conclusion still present an "order-invariant incremental clusterer" as the contribution. Yet Sec. V-F shows that, with corrections, an update costs about the same as a full re-cluster. The cost advantage over constrained average linkage was never measured. The invariance guarantee is, at the tuned setting, a property of connected components, and the frozen rule it is meant to beat already reaches 0.995 order agreement. Re-sizing the claim, fixing the Table II markup, confirming the page count, and making the disclosure sentence true would bring this to an acceptable state.

### Strengths
1. **S1 Candid reporting of where the method loses**: the paper states that it is not clearly ahead on degraded photos, is worse on profile faces, and loses its gain under wrong corrections. This is rare and valuable at this level.
   - **Evidence Anchor**: text: Sec. V-B "Under these terms our method is no longer clearly ahead on"
2. **S2 Round-2 fair-baseline fix is genuine**: constrained average linkage, two re-apply variants and the frozen rule were added. Each method gets its own user session. The hold rate is pooled over corrections. I checked `exp19_correction_baselines_edgeface_s.json` (ours 1,300 corrections over 207 libraries, mean 5.42, held 1.0, lost-held 0.203, later F1 0.99247) and `exp19b_frozen_edgeface_s.json` (later F1 0.9928, order agreement 0.9946). They match Table II and the text.
   - **Evidence Anchor**: table: Table II rows "Ours", "Constr. avg. link.", "Frozen (Immich-style)"
3. **S3 Identity-disjoint protocol, pre-declared tuning rules, released code**: these let a reader judge the claims. The negative pose result and the sticky-wrong-corrections result are genuinely informative.
   - **Evidence Anchor**: text: Sec. IV "All rules below were fixed before any test number was computed."
4. **S4 Disclosure is in the right place and specific about the AI's role**: it lists code, experiments, literature search and text.
   - **Evidence Anchor**: text: Acknowledgment "an AI assistant (Claude, Anthropic) was used throughout this work."
5. **S5 Prior art is now cited and contrasted**: 38 cited references, with no unused entry apart from `jung2025posetta`, which sits in the .bib file but is not cited.
   - **Evidence Anchor**: text: Sec. II "Our constrained step is closest to C-DBSCAN"

### Weaknesses

### W1: The headline contribution is still sized as a method, but the evidence supports an evaluation
**Problem**: The title, abstract, introduction bullet 1 and conclusion present the "order-invariant incremental clusterer" as the contribution. The paper's own results undercut each part of that:
- At the tuned setting m=1 the clustering is single linkage plus attachment plus a merge, so invariance is a connected-components property.
- Batch single and average linkage are also invariant (Table I, last row).
- The frozen rule reaches 0.995 order agreement and a marginally higher later F1 (0.9928 against 0.9925).
- Constrained average linkage ties on F1.
- Incremental update is 1.3 times faster than re-clustering, and with corrections it is about as costly as re-clustering.

The "provably" in the introduction describes a proof sketch of a near-trivial property. The title also says the face grouping "keeps the user's corrections", but the app has no correction interface (limitation vii).
**Evidence Anchor**: text: Intro "is provably independent of the"
**Why it matters**: A programme committee will read a "new clusterer" claim, see a tie with simple baselines, and downgrade the paper. The same facts framed as "what happens to corrections when photos arrive, measured fairly" are a stronger and truer contribution. This is the main acceptance risk.
**Suggestion**:
- Move the evaluation to the front of the contribution list and demote the clusterer to "the vehicle".
- Replace "provably" with "by construction (proof sketch)".
- Retitle, for example "Keeping User Corrections When New Photos Arrive: A Comparison of Constraint Handling in Face Clustering for Local Photo Libraries", or drop "Incremental" from the title.
- In the abstract, say that the method ties with constrained average linkage and the frozen rule, and that its distinct properties are exact order invariance and constraint-by-construction.
**Severity**: Major
**Confidence**: 4: core competence in conference-level contribution sizing.

### W2: The cost advantage over constrained average linkage is asserted, contradicted internally, and never measured
**Problem**: The abstract says constrained average linkage "must re-run on the whole library". The conclusion says ours "matches constrained average linkage without its batch cost". Sec. V-F then reports that with corrections the labels come from the constrained batch path, and "an update therefore costs about as much as re-clustering from scratch". The only batch time given (16.7 s for average linkage against 5.1 s for ours) compares unconstrained scikit-learn average linkage with ours on the constrained read path. Constrained average linkage itself was never timed. `exp18b_constrained_time_edgeface_s.json` has no entry for it.
**Evidence Anchor**: text: Conclusion "and matches constrained average linkage without its batch cost."
**Why it matters**: This is the one remaining claimed edge over the strongest correction baseline. It is not backed by a measurement, and the paper's own timing paragraph says the edge may not exist.
**Suggestion**: Time constrained average linkage with 0, 10 and 50 corrections on the same 8,290 faces with a comparable implementation. It is a few lines, because the code exists in `exp19_correction_baselines.py`. Then either report the measured ratio or delete the "without its batch cost" phrase and the abstract's batch-cost sentence.
**Severity**: Major
**Confidence**: 4: arithmetic and text consistency are directly checkable.

### W3: Table II will not typeset
**Problem**: In the source, the six body rows of `\label{tab:corr}` end in a single backslash followed by a newline, not `\\`. I confirmed this with `cat -A` on lines 322 to 327, for example `20\,/\,23 \$`. Every other table in the file uses `\\`. LaTeX will merge the rows and stop with "Extra alignment tab" errors, or typeset the table as one garbled row. This is also the headline table of the paper.
**Evidence Anchor**: table: Table II (`tab:corr`), source lines 322 to 327, row terminators `\` instead of `\\`
**Why it matters**: The revision log admits the paper "has not been compiled". A paper that fails to build, or has a broken main table, cannot go to a programme committee. This probably came from an escape-stripping edit, so other edits from the same session deserve a compile check.
**Suggestion**: Restore `\\` on all six rows, then compile on Overleaf and read the log for other warnings. Check overfull boxes in Table I (`table*`, 9 columns) and Table II (6 columns at `\tabcolsep` 1.8 pt).
**Severity**: Major (a one-character fix, but it blocks any submission).
**Confidence**: 5: verified by byte inspection.

### W4: The 6-page fit is uncertain and probably over
**Problem**: I estimated from the .tex by stripping tables and comments: about 4,100 words of running text (including macro residue), 3 tables (one `table*`, 9 columns, 11 rows), 38 references and a 248-word abstract.
- Text at about 950 words per IEEEtran conference page is 4.3 pages.
- Title, authors and abstract take about 0.35 pages.
- Tables take about 0.8 pages in total (Table I about 0.25, Table II about 0.2, Table III about 0.25, and captions).
- References take about 0.7 to 0.8 pages (38 entries at about 3 lines each).
- Headings, the proposition and the proof, the Acknowledgment and the Declarations block take about 0.3 pages.

This gives 6.2 to 6.7 pages. The round-2 estimate was 5 to 5.5 pages before the added related work, the three-user Table II, and the new timing paragraph. The revision log itself flags this. The venue's limit and any paid over-length option are unknown to me.
**Evidence Anchor**: absence: Manuscript — expected a compiled PDF with a page count; checked cove_paper.tex, REVISION_LOG_round3.md, paper/v2 directory
**Why it matters**: Over-length submissions are often rejected without review.
**Suggestion**: Compile first. If over, cut in this order:
- (a) Table III and Sec. V-E, with one sentence and the numbers moved to the repository. This saves about 0.3 page and addresses a side topic.
- (b) Sec. V-D (the pose negative result) to three sentences.
- (c) The Declarations block merged into the Acknowledgment.
- (d) The 8-row MBF-versus-EdgeFace asides.
- (e) The prior-art paragraph trimmed to the six contrasts that matter.

Remove `jung2025posetta` from the .bib file.
**Severity**: Major
**Confidence**: 3: an estimate; the compile is decisive.

### W5: The AI disclosure is acceptable in form, but one sentence is not yet true and several fields are unfinished
**Problem**: The Acknowledgment placement and content match IEEE practice. The content is specific: the system is named, and code, experiments, literature search and text are listed. It states that "the authors ... checked the reported numbers against the released per-run results". The revision log says the opposite: "Actually check the numbers. The Acknowledgment now states that the authors did." A disclosure that asserts human verification which has not happened is a misstatement. In addition, the author blocks still hold `[College name]`, `[City]` and `[email]`, and "Author contributions" says "to be completed". A reviewer would also ask what "ran a simulated peer review" means. It could be misread as a claim of external review.
**Evidence Anchor**: text: Acknowledgment "The authors directed the work, chose what to keep, and checked the reported numbers against"
**Why it matters**: Integrity statements are weighed heavily, and this one would be false if submitted today. Placeholders are an automatic desk-reject at many venues.
**Suggestion**:
- Have the authors actually spot-check the numbers (Tables I to III, abstract, Sec. V) against the JSONs, and then keep the sentence.
- Add the model name and version and the period of use. Reword "simulated peer review" to "a self-review exercise with role-prompted AI reviewers, whose findings we addressed".
- Fill the placeholders and the contributions line.
- Check the conference's own AI policy. Some Indian conferences restrict AI-drafted text or run detectors, and a plagiarism and similarity check is still pending.
**Severity**: Major (it blocks submission, though the fix is administrative).
**Confidence**: 4: the contradiction between the paper and the revision log is directly visible.

### W6: Two correction comparisons are weaker than the text implies
**Problem**:
- (a) The frozen rule is run only for the precise user: Table II shows "--" for the casual and error-prone users. So the claim that the rule "matches our F1" is untested for the users where re-apply fails.
- (b) "It can never revisit an earlier grouping" is stated as a weakness of freezing but is not measured. The "later" photos are 20% of the same people, so there is little to revisit.
- (c) Under the error-prone user, ours is worse than constrained average linkage by 0.0027 (CI [-0.0045, -0.0010], from exp19) and worse than re-apply (reported). The text gives the c-avg level (0.988) but not the significant gap. The Conclusion then says ours "matches" constrained average linkage unqualified.
**Evidence Anchor**: text: Sec. V-C "is mildly order-dependent (agreement 0.995), and it can never revisit an earlier grouping"
**Why it matters**: Each omission leans slightly toward the proposed method in the summary sentences, in a paper whose strength is not doing that.
**Suggestion**: Run `exp19b` for the casual and error-prone users. Or label them "not run" in the caption. Add the c-avg gap with its CI to the sticky-corrections paragraph. Change "matches" in the Conclusion to "ties for a careful user and is slightly worse for an error-prone one".
**Severity**: Minor
**Confidence**: 4: read from the JSONs.

### W7: Round-1 items and counts still loose
**Problem**:
- (a) The round-1 item "Chinese Whispers" is silently absent, with no stated reason (open since round 1).
- (b) The introduction says "seven baselines", but Table I has six baselines plus the "Ours, no attach" ablation.
- (c) The identity-level bootstrap was not run. The confidence intervals are acknowledged as probably too narrow (limitation iv), yet differences of 0.002 to 0.006 are called significant in Sec. V-B.
- (d) The Related Work names the search tools used ("SciSpace, Consensus and web search, abstracts only"), which reads as process detail rather than scholarship.
**Evidence Anchor**: text: Intro "an identity-disjoint evaluation against seven baselines tuned on equal terms"
**Why it matters**: Each is small, but together they invite avoidable reviewer comments.
**Suggestion**:
- Say "six baselines and one ablation".
- Add one sentence on why graph-based or Chinese-Whispers clustering was omitted, or run it.
- Run a bootstrap over identities, or soften "significantly" for effects below 0.005.
- Rephrase the search statement as "to our knowledge".
**Severity**: Minor
**Confidence**: 4

### Round-2 verification (EDITORIAL_DECISION.md against REVISION_LOG_round3.md and the paper)
| Round-2 item | Log says | Paper / evidence | My verdict |
|---|---|---|---|
| 1 Fair baselines (C1) | Fixed | Table II has c-avg, two re-apply variants and frozen. JSONs match. Text says 100% holds by construction. | **Resolved.** Residual: W6 (frozen only for the precise user). |
| 2 Hold-rate statistics | Fixed | "20% pooled", "up to ten (5.4 on average)", 207 of 240. JSON: 0.203, 5.417, 207. | **Resolved.** |
| 3 Perfect oracle | Fixed | Casual and error-prone users added. JSON: 1,528 corrections with 162 wrong. | **Resolved.** Honest negative result. |
| 4 Missing prior art | Fixed | C-DBSCAN, C-DenStream, Lasek and Gryz, Grinch, ConPaC and Wu et al. are all cited and contrasted. | **Resolved** as to presence. Correctness belongs to Reviewer 2. |
| 5 Title against the app | Text only; author decides | Title unchanged. Limitation (vii) states the gap precisely. | **Not resolved.** Needs a decision (see W1). |
| 6 Constrained path timed | Fixed | Sec. V-F gives 3.8 to 5.1 s. Matches `exp18b`. | **Resolved**, but it removes the "no batch cost" argument (W2). |
| 7 Number problems | Fixed | Abstract uses 0.56. The MBF occluded gap (-0.026) is stated. Table III was re-measured. | **Resolved.** |
| Single-seat: bootstrap independence | Limitation (iv) only | No identity-level bootstrap. | **Partly resolved**; disclosed (W7c). |
| Single-seat: contradictory corrections | Code fixed | Proof sketch updated. | **Resolved** as stated; not re-run by me. |
| Single-seat: licence, privacy, consent | Fixed | CC BY-NC-SA 4.0 given; API-key and CORS text present. | **Resolved.** |
| EIC: AI statement and Acknowledgment | Moved and rewritten | Now in the Acknowledgment. | **Partly resolved**: location right, one sentence not yet true (W5). |
| EIC: author placeholders | Still for the authors | Placeholders remain. | **Open.** |
| EIC: page length | Needs Overleaf | Not compiled; my estimate is 6.2 to 6.7 pages. | **Open** (W4). |
| New in round 3 | n/a | Table II row terminators are `\` instead of `\\`. | **New defect** (W3). |

### Detailed Comments

#### Journal Fit
The topic and the CPU-only, local-first angle suit an IEEE India regional computing conference. The audience values reproducible, honest applied work. Length is the open risk (W4). The Declarations block is not usual in IEEE conference format and costs space.

#### Originality
Honest and modest. The paper states that the parts are known. What I credit as new is the measurement: no earlier work in the cited set evaluates whether corrections survive re-clustering, and the paper hedges that claim as "in the sources we searched". The invariance property is correct, but at m=1 it is largely inherited from single linkage. That makes the proposition a good robustness guarantee for the code, not a research contribution.

#### Significance
Real but local: it informs designers of local photo managers that storing corrections as constraints beats re-applying them for imprecise users. The effect sizes are 0.001 to 0.004 F1, on simulated users from LFW celebrities. The wrong-correction result (the advice to make corrections visible and undoable) is the most transferable lesson.

#### Structural Coherence
Abstract, Sec. V-C and the Conclusion are consistent on the numbers. They are not consistent on the cost claim (W2) or on how much the method itself matters (W1). The Discussion's "What the results support" paragraph is the best-sized statement in the paper and should be echoed in the abstract.

#### Title & Abstract
The abstract is 248 words, long for a 6-page IEEE paper, and carries 12 numbers. Trim to about 200 words. The title promises "Keeps the User's Corrections" and "Incremental", the two claims the evidence sizes down.

#### Conclusion
Accurate except for "without its batch cost" and the unqualified "matches constrained average linkage" (W2, W6).

### Questions for Authors
1. Is constrained average linkage actually slower than your constrained path at 8,290 faces? Give the measured time with 10 corrections.
2. If the frozen rule reaches 0.995 order agreement and the same F1, what scenario makes the exact invariance (1.000) and the revisable grouping matter to a user? Do you have one measured?
3. Will the title remain unchanged if the app has no correction interface at submission time?
4. What is the conference's page limit, and does it allow paid extra pages?

### Minor Issues
- Remove the uncited `jung2025posetta` entry from `references.bib`.
- Abstract: lead with the finding (corrections survive; ties with constrained average linkage) and shorten.
- Table I: ties are shown in bold for several cells (JPEG, ours 0.993 against Two-stage and average linkage 0.993). State the tie rule in the caption.
- Table II caption: explain "--" for the frozen row and why the casual and error-prone columns are missing.
- Sec. V-E: the latency row footnote "mean of two runs which differed by up to 15%" weakens the 2.0 times claim. Say "about 2 times".
- Several sentences use a semicolon where two sentences read better (Sec. V-B, V-C). Hyphenate "re-apply" and "re-cluster" consistently.
- Sec. IV hardware sentence: add that timing was on battery or mains if known (reproducibility).
- Declarations: "Author contributions: to be completed" must be completed or removed.
