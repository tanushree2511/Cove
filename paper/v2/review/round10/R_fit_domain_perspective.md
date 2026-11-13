# Round 10 review (simulated): Journal-Fit, Domain, Perspective. HEAD 95e5089

Read-only. Not compiled (no TeX here). `verify_paper_numbers.py` was run: 209 ok, 0 mismatch. `paper/v2/` and `paper/overleaf_upload/` tex and bib are identical. 43 cited keys, all present in the bib; 10 bib entries uncited (harmless). All `\ref` labels resolve; no unbalanced braces seen; `figs/pipeline.pdf` is present in both folders. The Nov 10 PDF (6 pages) is stale and predates FIW.

## 0. Items carried over from rounds 8-9, status now
FIXED: tombstones defined (l.357); "real family photos" changed to "web family photos" (abstract, caption, Sec. IV, V-A); ArcFace and MobileFaceNets cited (l.115); Immich threshold now cites the docs (l.197); p=0.02 interval now printed (l.276); the sweep now covers all methods (l.277-280); Grinch moved to "incremental"; FIW library overlap quantified (344 slots over 247 of 490 families, l.260); embedding-privacy clause added (l.359-360); 15-run deletion test added (l.330); Discussion now says "On the LFW libraries" and "though we did not test one".
STILL OPEN: the abstract is not shorter (290 words by my count, was 298); the Mixed row and the "fairer tuning" detail are still there; look-alike has no number (l.246); the FIW bib entries are incomplete (see M8); the FIW intervals are still printed to 4 digits (see M6); the page budget (see C1).

## 1. Findings

### CRITICAL
**C1 - Page length: very likely over 6 pages (l.1-384).**
Evidence: I counted prose words with a script. The last commit whose PDF is 6 pages (cef2e0f, Nov 10) had abstract 245 words and body about 3,350 words, with three small tables. HEAD has abstract 290 and body about 4,130 (+780, +23%), with two tables, one figure and 3 more references (FIW x2, Immich docs). Net growth is roughly 0.7-0.9 column-page. Round 9 already estimated 6.1-6.5 pages and asked for 25-35 lines of cuts; since then about 130 more body words were added and only 8 abstract words removed. The 6-page fit is not credible without a compile.
Fix: compile on Overleaf first. If over, cut roughly 500-700 words: (a) "Fairer tuning" and people-bootstrap sentences l.240-247 (about 90 words); (b) l.329-340 the 15-run deletion sentence, the "twofold" sentence and the FAISS build sentence (about 80); (c) the two MBF-on-FIW sentences l.259-260 and l.286-287 (about 70); (d) abstract to 220 words or fewer (about 70); (e) l.344-352 "What the results show" restates the abstract and conclusion (about 80); (f) l.132-134 the 240/210-216/1,276 sentence (about 40); (g) Table I: drop the Mixed row and shorten the caption (about 60 words of space); (h) drop mazumdar2017noisy and the AUC sentence l.320-321 (about 40).

### MAJOR
**M1 - Placeholders and an unsupported "released" claim (l.17-28, 78, 376-378).**
Evidence: the authors' blocks are `[College name]`, `[City]`, `[email]`; the data line says "URL to be added"; "Author contributions: to be completed". Yet l.78 says "Code and per-run results are released."
Fix: fill the author fields and the URL before submission, or change l.78 to "will be released at the URL below" until the repository is public.

**M2 - Abstract is too long and its key sentences are hard to parse (l.33-47).**
Evidence: about 290 words against a typical IEEE conference limit of 150-250. The parenthetical "identical people on two devices (53\% and 31\% for a frozen-label rule of our design)" reads as if the frozen rule agrees on 53% and 31% of devices, i.e. it is easy to mistake for a success figure for the proposed method. The sentence "within about one point of average linkage, averaged over the library conditions (ahead ..., behind ... and, by 7 points, on profile ones)" mixes two different things: the library-condition average (about 0.0003 apart, i.e. a tie, so "one point" understates) and the whole-set CPLFW result (7 points).
Fix: cut to 220 words or fewer; write "identical people on two devices, where an edit-log baseline of our design agrees in only 53% and 31% of cases"; and say "tied on average over the library conditions; 7 points lower on the profile set CPLFW".

**M3 - "Corrections vs. gone by one wrong click in twenty" overstates against the body (l.45-46 vs l.277, 349-351).**
Evidence: at p=0.05 the gain is +0.0009 with an interval that includes zero; the body and Discussion say "small at five to ten". The abstract says "gone".
Fix: abstract: "no longer distinguishable from zero by about one wrong click in twenty".

**M4 - Both "comparison to frozen rule" selling points rest on a baseline the authors designed, and the abstract still lists them as results (l.44, 203-204, 311-321, 346).**
Evidence: the frozen store replays edits "without timestamps, in received order"; this is acknowledged at l.314-315 and in the Discussion as "any such design shares them", which is honest. However Table II shows the frozen rule has the best "later" F1 for the precise user (0.9928 vs 0.9925 for ours) and 100% held, and its casual and error-prone cells are `--` with no explanation (l.303), so the reader cannot tell whether it was not run or failed.
Fix: add "(not run)" to the Table II caption for the `--` cells and give the reason in one clause; keep "of our design" next to the 53%/31% wherever they appear.

**M5 - Placeholders aside, FIW licence and ethics need one confirming sentence (l.175-176, 377).**
Evidence: "used under its terms (non-commercial research, images not redistributed)" is asserted. FIW relatives are not all public figures, and FIW includes minors. The paper shows no FIW image (good), and cites FIW (good), but the released "per-run results" may contain FIW file names or identity ids.
Fix: add "no FIW image is shown or shared; released files hold only scores and anonymous indices" (confirm this is true) and confirm the FIW agreement was accepted by the authors.

**M6 - FIW "better than" claims use narrow intervals the authors themselves doubt (l.255-261, 282-287).**
Evidence: l.260 says the intervals are "probably too narrow" (libraries share families), yet l.284-285 states "ours is better by +0.0045 ([+0.0016,+0.0077]) and +0.0094 ([+0.0061,+0.0130])" and l.256 lists "above single linkage (+0.011), DBSCAN (+0.040) ..." without any interval. The caveat sits in a different paragraph.
Fix: after the first FIW interval in Sec. V-B add "(intervals as in Sec. V-A, probably too narrow)", and round to one decimal in points ("about 0.5 and 0.9 points").

### MINOR
**m1 - Cove is never described (l.58, 354).** A reader who has not seen the project does not learn what Cove is, whether it is open source, or its platform. Fix: one clause in the Introduction ("Cove, our open-source desktop photo manager") with a URL once available.
**m2 - "Local-first" is used loosely (l.1 title, 56-58, 110-112).** Kleppmann's local-first software implies multi-device sync; the application has no sync (stated l.111-112), and Immich and PhotoPrism are self-hosted client-server systems. Fix: "self-hosted" for Immich/PhotoPrism/FaceCluster; say once what "local-first" means here (processing stays on the user's device).
**m3 - Quantity in l.241-243 undefined.** "average linkage 0.9849 against 0.9857", "ours ... 0.9854" are never said to be the mean B-Cubed F1 over the library conditions. Fix: add "(mean F1 over the library conditions)".
**m4 - "because" asserted (l.252-253).** "because single-linkage cores split profile photos from frontal ones" is a mechanism not tested here (precision 0.985 and recall 0.733 are consistent with it, but do not show it). Fix: "probably because".
**m5 - Look-alike claim has no number (l.246).** "not distinguishable on ... look-alike libraries" cannot be checked; look-alike is not in Table I. Fix: give the difference and interval or drop it.
**m6 - Confusing parenthetical on recognisers (l.115).** "(MobileFaceNet with ArcFace loss, w600k_mbf, "MBF", is also evaluated)" can be misread as describing EdgeFace-S. Fix: "; MobileFaceNet~\cite{..} trained with ArcFace loss~\cite{..} (InsightFace w600k_mbf, "MBF") is also evaluated."
**m7 - Training-set overlap with the test identities not mentioned.** The recognisers are trained on web face collections of public figures; LFW and FIW are public-figure web images. "Identity-disjoint" refers only to tuning versus test. Comparisons between clusterers are unaffected, but absolute scores (about 0.99) may be optimistic. Fix: one clause ("the recognisers' training sets may overlap LFW/FIW identities; we did not check").
**m8 - FIW bib entries incomplete (bib l.496-508).** Both use "and others", the 2016 entry has no pages and the 2018 entry has no volume or pages. Fix (verify): Robinson, Shao, Wu, Fu, ACM MM 2016, pp. 242-246; Robinson, Shao, Wu, Liu, Gillis, Fu, IEEE TPAMI 40(11):2624-2637, 2018.
**m9 - Citations attributed from abstracts (l.93-94, 57).** "OGMC reduces order dependence for face streams" and the FaceCluster description rest on abstracts or a demo paper. Fix: soften OGMC to "online clustering for face streams" unless the order-robustness claim is confirmed in the text.
**m10 - Proposition vs. deletion rule (l.143-144, 148-152).** Deletion "drops corrections that name" the deleted faces, so deleting and re-adding a face loses its correction; the final correction set then depends on history, contradicting "not the deletion history" in the edge case. Fix: add "(a re-added face starts without its old corrections)" or state the proposition for the stored correction set.
**m11 - Baselines' extra parameters (l.181-183).** "One-threshold baselines one (11)" - DBSCAN needs min_samples and HDBSCAN min_cluster_size. Fix: state the fixed values in the caption or "plus fixed min_samples".
**m12 - Convoluted sentence (l.132-134).** "a separate run from Sec. V-B: 210-216 pairs per user received corrections, which changed the result in all but one of 1,276 cases" clashes with "207 of 240" at l.264 and leaves the reader unsure which run is which. Fix: shorten to "identical under corrections too (1,275 of 1,276 corrected cases changed the result, none differed between the exact and original merge)" or cut it.
**m13 - Speed-up range (l.337).** 234/15 = 15.6, so "9 to 15 times" (also l.346) should read "9 to 16" (or "about 9 to 16").
**m14 - Conclusion number lacks its user (l.364-365).** "F1 0.9925" is the precise user; the abstract and conclusion do not say so. Fix: "(precise user)".
**m15 - Simulated-user realism (Perspective, l.190-197, 280, 351).** The precise and casual users pick faces "aimed at the largest remaining mistake", which needs ground truth; real users find mistakes by looking at thumbnails. The wrong-click rates (0.02-0.2) are not tied to any human study (biswas2014active, already in the bib, studies human pairwise constraints and could anchor this). The Discussion is hedged ("though we did not test one"), but the gain figures are best-case. Fix: one clause "an oracle-guided user is an upper bound".
**m16 - Privacy wording (l.358-360).** "embeddings are themselves biometric data" is a legal-sounding claim stated flatly and repeats "biometric" in the same sentence. Add one clause on bystanders and on misuse (grouping faces of people who did not consent to being recognised). Retraction tombstones keyed by photo hash and face box also keep identifiers of removed items; mention that they should be deleted with the photo. Fix: "embeddings can identify people and should be treated as biometric data".
**m17 - Table I caption dense (l.215-217).** Seven pieces of information in 4 full-width lines; "Bold: best" but the FIW row has no bold even though ours (0.786) is highest (explained by "four methods within 0.004"). Fix: split into a shorter caption and one sentence in the text.

## 2. What is now fine
- Numbers: 209 of 209 checked values match the released results; Table I deltas quoted in the text (+0.0059, +0.0038, +0.0022, -0.0061, -0.0089, 0.2 to 14 points, 3.6 and about 5 points) match the table cells.
- Claims about ties are now honest: FIW "ties", c-avg "tied, not ours ahead" (l.269-271), wrong corrections "sticky" (l.274), CPLFW 7 points worse reported in the abstract.
- Novelty note (l.100-102) is bounded to the searched sources and dated.
- AI-use disclosure, licence note (InsightFace, EdgeFace CC BY-NC-SA 4.0), and "simulated" framing are consistent between abstract, body, Discussion and conclusion.
- Bib entries I checked from memory (ArcFace, SCRFD, MobileFaceNets, EdgeFace, FAISS, Gower-Ross, SLINK, Ester 1996/1998, Davidson 2005/2006/2007, Wagstaff 2001, CRDT, Local-first, BCT, Otto, L-GCN, Yang, Shi, Wu, Zhu) have plausible venues, volumes and pages. Every cited claim I could judge fits its reference.
- LaTeX: `proof` with amsthm under IEEEtran is fine; table* in [t] may float one page late (check on Overleaf); unused label `sec:protocol` and packages `multirow`, `xcolor` are harmless.
- Proposition and proof sketch are honest about ties and exact arithmetic; the 15-run deletion test closes the "unit test only" gap.

## 3. Recommendation
- **Journal-Fit: minor revision, conditional on a compiled 6 pages** (major if the Overleaf build is over 6). Confidence 3/5. Blocking items: C1, M1, M2.
- **Domain: weak accept.** Confidence 4/5. Fix M6, m7, m8, m9, m10, m11 (all text-level).
- **Perspective: weak accept.** Confidence 3/5. Fix M5, m15, m16; the study remains simulated, which the paper says plainly.

No new experiments are needed.
