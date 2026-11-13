# Round 11 review (simulated): Journal-Fit, Domain, Perspective. HEAD 75c87ec

Read-only. No TeX on this machine, so nothing was compiled. I read the full .tex (l.1-375), the bib entries for FIW, Immich, OGMC, and the results JSON behind the changed numbers. `evaluation/verify_paper_numbers.py` was run: 219 ok, 0 mismatch. I also re-checked by hand: MBF CALFW/CPLFW (0.937 vs 0.955; 0.787 vs 0.916, exp14_disjoint_mbf.json), the exp30c deletion test (15 of 15 identical, 7-10 corrections made, 2-10 kept, all flagged as changing the labels), the FIW json (per-library keys are integers; no file names or family ids), all `\ref` labels (resolve), all 43 cited keys (all in the bib).

## 0. Status of round-10 fixes (checked against the current text)

| Round-10 item | Status |
|---|---|
| Abstract shorter, "by construction", "no longer distinguishable from zero" | DONE, but still about 265 words (previous 290; see M3) |
| "ties ... on average over the library conditions (7 points lower on profile photos)" | DONE, numbers correct (0.9854 vs 0.9857; CPLFW 0.841 vs 0.909). The Table I rows behind "the library conditions" are partly missing (see M2) |
| MBF CPLFW/CALFW stated (l.244-245) | DONE, numbers match the file |
| Orders sentence (l.182) | DONE, clear |
| Constrained-average-linkage wording for error-prone user (l.266) | DONE, number correct (0.9878 vs 0.9851), but the sentence before it is now contradictory (see m3) |
| Table II caption ("--", correction sets differ) | DONE |
| Mean ARI (0.997/0.996) added | DONE, matches the file |
| FIW bib entries | DONE: MM 2016 pp. 242-246; TPAMI 40(11) 2624-2637 (both complete in references.bib l.496-512) |
| FIW ethics sentence | DONE; the json contains only scores and integer indices, so the sentence is true |
| Privacy wording, tombstones | DONE (l.350-351) |
| Binding-correction deletion test (exp30c) | DONE and honest: the file flags `corrections_change_labels: true` in 15 of 15 |
| Dropped "Mixed" row, look-alike sentence, AUC sentence, MBF-on-FIW interval sentences | Removed cleanly in the prose, but Mixed and Look-alike are now silent omissions from the table (M2) |
| "will be released (URL below)" (l.77) | DONE; the claim is now true to the facts, but the URL and author fields are still placeholders (M1) |

No new broken sentence or orphaned `\ref` was introduced. Grammar is acceptable throughout. The remaining defects are below.

## 1. Page-count estimate (candid)

Method. The last 6-page build (Cove_paper.pdf, 6 pages, made from cef2e0f) has page 6 holding only references [23]-[37]: 48 extracted lines against 122 on a full page (page 5). So that version used about 5.4 pages and had about 0.6 page (roughly 70 two-column lines) of slack.

Change since then, in two-column line equivalents (about 57 characters per line):
- Prose: my script counts 21,913 -> 26,015 characters (+4,100, +19%); your count of 21,800 -> 24,900 is +3,100 (+14%). That is +54 to +72 lines.
- References: 37 -> 43 cited, with the FIW entries now complete: about +16 to +20 lines.
- Floats: Table I lost 4 rows (13 -> 9) and Table III is gone: about -20 lines. The new pipeline figure (252x144 pt scaled to 0.92 column, plus a 4-line caption): about +16 lines. Net about -4.
- Total: about +66 to +88 lines against about 70 lines of slack.

Verdict: the paper sits right at the limit. My central estimate is 6.0 to 6.15 pages, so there is about a 50% chance it spills onto a 7th page by 1 to 15 lines. Float placement (a `table*` forced to the top of the next page, the figure `[t]` on page 2) can add whitespace that my estimate does not model, which tilts toward overflow. Compile on Overleaf before anything else. If it is over, cuts in ranked order (lines saved in brackets):

1. Abstract to 230 words or fewer, and delete the repeated parenthetical numbers [4].
2. Discussion "What the results show" (l.335-342): it repeats the abstract and conclusion; keep only the sweep sentence [6-7].
3. "Fairer tuning" detail and the people-bootstrap description (l.236-239, 184-185) down to one sentence each [5].
4. Timing paragraph: drop "single timings vary up to twofold", the 8,290-face comparison parenthesis and the FAISS sentence (l.330-331) [4].
5. Related Work: drop `mazumdar2017noisy`, `wu2013constrained` and one of `gower1969mst`/`sibson1973slink`; each also saves a reference line [4].
6. MBF sentences on FIW and CPLFW (l.244-245, 255, 282) [3].
7. The "(1,276 cases ...)" parenthetical (l.130-131) [2].
8. Pipeline figure width 0.92 -> 0.80 of the column [2-3].
9. The second Upgrade direction (l.318, "The other direction gives 48%") [1].

Items 1-4 together give about 20 lines, enough margin. Do not cut Table II or the deletion sentence.

## 2. Findings

### CRITICAL
None that I can establish from the text alone. The page limit (above) is the gating risk, and it can only be settled by compiling.

### MAJOR

**M1 - Placeholders remain (l.17-28, 367-369).**
Evidence: `[College name]`, `[City]`, `[email]`; "URL to be added"; "Author contributions: to be completed". The text is now consistent with these (l.77 says "will be released"), so this is a submission checklist item, not a content error.
Fix: fill the author block, the repository URL and the contributions line before upload, and make sure `evaluation/results/exp28_testruns_edgeface_s.json` (61 MB, still untracked, shown as `??` in git status) is committed or its absence stated, because l.367-368 say per-run results are in the repository.

**M2 - Table I silently drops two of the eight conditions that the abstract and text average over (l.169-170, 213, 238-239; abstract l.37-38).**
Evidence: "library conditions" are eight (240 pairs = 30 libraries x 8; "the eight conditions", l.239). The table shows five, and the caption mentions only JPEG as omitted. Mixed and Look-alike are still defined in the protocol (l.167, 169) but appear nowhere in the results. From exp14_disjoint_edgeface_s.json: Mixed, ours 0.978 vs average linkage 0.981 (the old interval included zero); Look-alike, ours 0.998 vs average linkage 0.994. So "ties on average over the library conditions" cannot be rebuilt from the printed table, and one omitted row is slightly adverse to ours.
Fix: caption: "JPEG (q8), Mixed and Look-alike omitted (ours 0.993, 0.978, 0.998; average linkage 0.993, 0.981, 0.994)."

**M3 - Abstract is still about 265 words (l.32-47).**
Evidence: down from 290, but IEEE conference templates normally allow 150-250, and it holds 13 numbers. It is the most dense part of the paper.
Fix: cut to 230 or fewer by dropping "(plain re-clustering keeps 20%, re-applying 73-96%)" and the edit-log percentages (both are in Sec. V-C) and keeping one figure for the speed.

### MINOR

**m1 - "the gain is the attach threshold" is a misattribution (l.242-244).**
Evidence: against single linkage the occluded gain is 14.3 points (0.943 vs 0.800), but ours without attach already scores 0.907, so the centroid merge gives about 10.7 of those points and attach only 3.6. The attach step is what costs 0.5 points on CPLFW (no-attach 0.892 vs single 0.846), not what produces the gain.
Fix: "the CPLFW gap is the attach threshold (removing it costs up to 3.6 points on libraries but gains about 5 on CPLFW); most of the gain over single linkage comes from the centroid merge."

**m2 - "In the last three the alternative is a frozen-label store" is wrong for Upgrade (l.199-201).**
Evidence: the three are Two devices, Retraction and Upgrade; the Upgrade paragraph (l.316-318) reports no frozen baseline.
Fix: "In the first two".

**m3 - c-avg paragraph is self-contradictory (l.264-267).**
Evidence: "on the new photos alone it is better for all three users (ours -0.0014, [-0.0026,-0.0002] for the precise user ...), so the two are tied for the precise and casual users." "It" has no clear subject, and an interval that excludes zero for the precise user cannot be called tied.
Fix: "on the new photos alone constrained average linkage is ahead for all three users (by 0.0014, [0.0002,0.0026] for the precise user; 0.0057 for the error-prone user); on all faces the two are within 0.001 for the precise and casual users."

**m4 - Error-prone user and sweep at p=0.10 disagree without comment (l.266, 269-272).**
Evidence: Table II gives ours 0.9851 vs 0.9854 for discarding (-0.0003); the sweep gives +0.0010 at p=0.10. Both are inside noise, but the text says they "agree".
Fix: add "(different random draws; both intervals include zero)".

**m5 - "Fixed before any test number was computed" (l.161) sits beside the statement that CALFW, CPLFW and earlier library draws were used while developing the clusterer (l.177).**
Fix: "The library protocol was fixed before any test number was computed".

**m6 - Proposition says "the corrections that name them" (l.145-149), but a deleted-and-readded face loses its corrections (l.140-141).**
The method text now says so; the statement of the proposition does not. Fix: "the stored corrections that name them".

**m7 - Deletion sentence is hard to follow (l.324).**
"random corrections, which did not change the labels" refers to the earlier test, never introduced. Also only 2-3 corrections survive at 30% deletion, so "together change the labels" may refer to before deletion. Fix: state "(corrections that change the labels before deletion; 2-10 survive)" and cut the "random corrections" clause or give it its own clause: "an earlier test with random corrections, which changed nothing, also gave 15 of 15".

**m8 - "Local-first" (title, l.57) is defined after the title and before the term is used in the body.**
The parenthetical at l.57 has no antecedent in the text, and Kleppmann's sense (l.95) includes sync, which the application lacks. Fix: "(here 'local-first' in the title means only that processing stays on the user's device)" or use "on-device".

**m9 - Conclusion over-attributes (l.356-358).**
"Recomputing from the sets gives ... corrections that keep about half their value across a recogniser change" - the recogniser result is a property of the embeddings, not of recomputing from the sets. Fix: separate the clause: "...; corrections also keep about half their value across a recogniser change".

**m10 - Wording of the FAISS cost (l.331).**
"Adding all faces to the flat FAISS index ... (quadratic)" - adding vectors to a flat index is linear; the quadratic part is the range searches of the update. Fix: "indexing and neighbour search".

**m11 - Speed-up range (l.329, 337, abstract).**
234/15 = 15.6, so "9 to 15" is slightly low; "9 to 16" or "about 9 to 15" is accurate. The abstract's "about an order of magnitude" is safe.

**m12 - Unverifiable attribution (l.91-92).**
OGMC "reduces order dependence for face streams": the cited title is "Efficient Large-Scale Face Clustering Using an Online Mixture of Gaussians", which does not say order dependence. Fix: "online clustering for face streams" unless the paper's text supports the stronger claim.

**m13 - "1,275 of them changed by the corrections" (l.130-131) is unclear.**
It means the corrections altered the labels in 1,275 of 1,276 cases (so the identity check is not vacuous). Fix: "corrections altered the labels in 1,275 of the 1,276 cases".

**m14 - Grid lower bound missing (l.175, 179).**
"upper bound 0.70" with "(11)" grid points only works if the lower bound is 0.20; DBSCAN and HDBSCAN fixed parameters are not named. Fix: "(0.20-0.70, step 0.05)" and "DBSCAN and HDBSCAN: one threshold, other settings fixed".

## 3. Domain reviewer notes (literature and technical claims)
- The related-work claims are bounded and dated (l.98-100). Every cited claim I could judge fits its reference. Missing but cheap to add: FINCH (Sarfraz et al., CVPR 2019) is the best known training-free, parameter-free face-clustering baseline that fits "training-free methods a CPU application can run" (l.82-83); one clause saying why it is not compared would pre-empt a reviewer.
- The core technical argument (mean of cosines cannot exceed its largest term, so average linkage splits at the threshold graph) is correct, and the proposition carves out ties honestly.
- The speed claim compares against dense average linkage (own implementation and SciPy). Sparse or approximate average linkage from a kNN graph is not tested; l.326-331 should say "dense".
- Tie cases: the proof sketch correctly says order agreement was 1.000 in every tested order; that is evidence, not proof, and the text says so.

## 4. Perspective reviewer notes (practice, ethics, readers)
- The paper's honest position is now clear: accuracy ties the best baseline; the value is the set-based design (shared by constrained average linkage, as l.337-338 admit) and a faster read. An outside reader will ask what is left that is unique; the answer (an incremental clusterer with exact deletion that is cheaper than dense recomputation) is in the text but not in one sentence. The conclusion could say it plainly.
- Oracle-guided simulated users: stated as upper bounds at l.194 and "untested" at l.342; adequate. Wrong-click rates are not tied to human data; `biswas2014active` is in the bib but uncited (harmless).
- FIW: ethics sentence is complete and true (the json holds scores and integer indices). FIW is distributed on request, not public; l.367 lists LFW/CALFW/CPLFW as public and omits FIW. Fix: "FIW is obtained from its authors under its terms".
- Privacy and tombstone wording (l.350-351) is fair and proportionate.
- Local-conference readers: the paper is very dense for six pages (must-link, core, attach, centroid merge, B-Cubed, ARI, bootstrap in the first two pages). Cutting M3 and the cuts in section 1 would also help readability.

## 5. What is now fine
- Numbers: 219 of 219 script checks pass; the MBF CPLFW/CALFW, the Table I deltas, the FIW deltas, the sweep numbers and the Table II cells I recomputed all match.
- Honesty of claims: "ties" language for Table I and FIW; error-prone user shows c-avg ahead; wrong corrections "sticky"; CPLFW 7 points worse reported in the abstract and body; frozen baseline labelled "of our design" in the abstract, Sec. IV, Sec. V-C and the Discussion; the novelty note is dated and bounded.
- Deletion exactness is now supported by a test that binds (exp30c) rather than a vacuous one.
- Bib: FIW entries complete; no missing keys; 10 uncited bib entries are harmless with IEEEtran.
- Ethics, AI disclosure, licence note, simulation framing are consistent in abstract, body, Discussion and conclusion.
- LaTeX: all labels resolve, no unbalanced braces seen, `proof` under IEEEtran with amsthm is fine; unused `sec:protocol` label and `multirow`, `xcolor` are harmless.

## 6. Recommendations
- **Journal-Fit Reviewer: minor revision, conditional on a compiled 6-page build.** Becomes major revision if the Overleaf build exceeds 6 pages and the cuts in section 1 are not applied. Blocking items: page count, M1, M3. Confidence 3/5 (cannot compile).
- **Domain Reviewer: weak accept.** Fix M2, m1, m2, m3, m12. Confidence 4/5.
- **Perspective Reviewer: weak accept.** Fix the FIW access sentence and consider one sentence on what is unique to the clusterer. Confidence 3/5.

No new experiments are needed.
