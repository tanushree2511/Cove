# Round 10 - Methodology Reviewer + Devil's Advocate (simulated seats, read-only)

Manuscript: cove_paper.tex (commit e582d64 + working tree); line numbers refer to it. verify_paper_numbers.py: 209 ok / 0 mismatch (re-run). No LaTeX in this environment and Cove_paper.pdf is dated 10 Nov, so the 6-page fit is NOT VERIFIED. Extra scripts I ran live only in the session scratchpad; no project file was touched.

## 0. Independent spot-checks (numbers NOT covered by verify_paper_numbers.py) - all correct unless flagged
1. Table I order-agreement row: First-Leader 0.562, Two-stage 0.758, DBSCAN 0.9966, HDBSCAN 0.9834, ours/avg/single 1.000 (exp14_disjoint_edgeface_s.json) - ok.
2. L209 "F1 differs by up to 5.9 points between orders": First-Leader F1_spread max 0.0587 (occlude) - ok.
3. Abstract L37-40 "within about one point of average linkage, averaged over library conditions": mean over 8 conditions ours 0.9854 vs avg 0.9857 (-0.0003); per-condition diffs clean +.0059, blur +.0038, dark +.0022, lowres -.0061; CPLFW 0.841 vs 0.909 (7 points) - ok.
4. L246-248 "better than single linkage on every condition by 0.2 to 14 points except CPLFW": CALFW +0.002, occluded +0.143, CPLFW -0.005 - ok. "Removal of attach costs up to 3.6 on libraries (occluded -0.0359), gains ~5 on CPLFW (0.892 vs 0.841)" - ok.
5. L251-253 CPLFW precision/recall 0.985/0.733 vs 0.912/0.906 - ok. CALFW 8,212 and CPLFW 7,718 faces - ok.
6. L178-183 grid sizes: Ours 360, one-threshold baselines 11 (JSON `grid`); tuned (0.65, 1, 0.50, 0.55); 79/1,844 per half - ok.
7. L240-242 fine grid: baselines moved by -0.0008 (avg), +0.0020 (single), +0.0021 (DBSCAN, HDBSCAN), -0.0012 (First-Leader), 0 (Two-stage); max 0.0021 - ok (wording, see m6). Look-alike identity CI [0.0000, 0.0104] supports "not distinguishable".
8. L260 FIW "344 family slots over 247 of 490 test families": I re-created the draw (RandomState(2026) split, seed-0 library draw, same RNG consumption as exp31b build()): 344 slots, 247 distinct families, 490 in the half, max reuse 4 - ok. 6.7% = 2,320/34,692 = 6.69% - ok.
9. L133-134 "210-216 pairs per user ... changed the result in all but one of 1,276 cases": exp26 tables, both recognisers, 213/213/216 and 210/210/214 pairs with corrections; 1,275 of 1,276 changed - ok.
10. L265 now-gain 0.984 -> 0.994, +0.0097 [0.0082, 0.0114] (my bootstrap of exp19 per_library, seed 0) - ok.
11. L269-270 ours minus c-avg, all faces: precise +0.0010 [-0.0001, +0.0021], casual +0.0004 [-0.0007, +0.0014], error-prone -0.0027 [-0.0045, -0.0010] (see m2).
12. L271 frozen within 0.0003 (EdgeFace-S 0.9928 vs 0.9925) and 0.009 below with MBF (0.9834 vs 0.9925) - ok. L274 162 of 1,528 - ok. Table II every cell incl. held 20/23, 96/73, 100/100 - ok.
13. L278-279 c-avg sweep +0.0028, +0.0027 (CIs [0.0018, 0.0038], [0.0018, 0.0036], exclude zero), -0.0009 [-0.0020, +0.0002]; re-apply +0.0039/+0.0037/+0.0025 with intervals excluding zero - ok.
14. L327-329 add 0.877 s total, last batch 0.145 s, original merge 3.38 s (exp18) to 4.91 s (exp20); fast 0.51 s; 1.86/2.20 s - ok.
15. L334-339 exp29: 15.4/20.0 s, 233.5/212.3 s, SciPy 174.4 s, build 8.4 s (8,290) and 315.8 s; 8,290 row 0.44/1.25 vs 30.3/19.6 s; ratios 15, 9 (SciPy / ours with corrections = 8.7), 69, 16 - ok.
16. L330-331 exp30b: 15 rows, 5 seeds x {1, 10, 30}%, all identical (JSON and log) - ok as a count.
17. L322 "210 libraries whose faces are identical under both recognisers": exp23 protocol = 240 minus 30 look-alike libraries - ok.
18. L197 Immich: fetched docs.immich.app/features/facial-recognition: "strongly recommended not to go below 0.3 or above 0.7"; frozen threshold cosine >= 0.5 = distance <= 0.5, inside the range - ok.
19. L168-170 library sizes (15-40 / 50-150; look-alikes 7-14 = argsort top 8-15 including the seed person) and 10,000 / 1,000 resamples - ok.
Also: the proof sketch matches stable_cluster.remove() (adjacency kept, core flags and union-find rebuilt, corrections renumbered).

## 1. Status of round-9 items
Sweep claims for all methods: FIXED (L275-280 name c-avg and re-apply). FIW no-attach and library overlap: FIXED (L259-261). "advisable / untested": FIXED (L351-352). By-construction wording: PARTLY ("as any such design would", L43). Orders (round-9 M2): PARTLY, see m1. Mean ARI for the frozen replicas: NOT FIXED (still only lowest ARI 0.89/0.91; the file has mean 0.997/0.996 and replica F1 gap 0.001/0.002). Table II "--": NOT FIXED (caption silent). "Superlinear read": NOT FIXED. exp28_testruns_edgeface_s.json (61 MB) still untracked while L378 says per-run results are in the repository. Bib "and others" for both FIW entries (references.bib L497, L504): NOT FIXED.

## 2. Findings

### MAJOR
**M1 (L330-331, abstract L44 "exact ... deletion"): the new 15-run deletion test never exercises corrections.** Evidence: exp30b_deletion_seeds.py draws 5 same-person and 5 cannot-link pairs at random from true labels. I re-ran exactly those 15 correction sets on the full 8,290 faces: in 15 of 15 the corrections leave the partition unchanged (labels identical to the no-correction clustering). exp26's own docstring says random corrections "rarely change anything", the pitfall that motivated exp26. So "with 10 random corrections present" reads as a stress test but is vacuous; the 15 runs test deletion of the unconstrained clusterer on one library, one recogniser, one setting. Deletion with binding corrections is covered only by the synthetic unit test (test_remove_gives_the_state_of_never_having_added_those_faces, 5 trials, random pairs on 10 Gaussian blobs, where they do bind). Both sides also use the same fast-merge code path and the same relative face order, so tie-breaking is not tested. Fix: write "(none of the random corrections changed the labels; corrections that do are covered only by a synthetic unit test)", or reuse the exp26 user model for the 15 runs.

**M2 (L248-249): "With MBF the pattern is similar" understates the MBF whole-set result.** exp14_disjoint_mbf.json: CPLFW ours 0.787 vs average linkage 0.916 (13 points, against 7 with EdgeFace-S) and CALFW ours 0.937 vs 0.955, so ours is behind on both whole sets, whereas the text says ours is "best on CALFW" and the CPLFW deficit is "about 7 points" (L251-253, EdgeFace-S only). Only the MBF occluded gap is mentioned. Fix: "With MBF ours is also behind on CALFW (0.937 vs 0.955), by 13 points on CPLFW (0.787 vs 0.916) and on occluded faces (0.928 vs 0.954)."

### MINOR
**m1 (L185): "On the LFW libraries every method runs in 5 shuffled orders" is not true of the run behind Table I.** exp14_disjoint.py `_test`: `range(5 if method in ORDER_DEP else 3)`, ORDER_DEP = {First-Leader, Two-stage}; the exp14 docstring says "ours 3 orders". Table I's order-agreement row (ours 1.000) rests on 3 orders for ours. exp28 does run all methods in 5 orders, but stores only mean metrics (no order agreement) and its result file is untracked. This is round-9 M2 in a new form. Fix: "order-dependent methods 5 orders, the others 3 (all methods 5 in the Sec. V-A re-run)".

**m2 (L269-271): "so the two are tied, not ours ahead" is not true for the error-prone user.** Ours minus c-avg = -0.0027 [-0.0045, -0.0010] on all faces (excludes zero) and -0.0057 on new photos; Table II 0.9851 vs 0.9878. The abstract's "within 0.003" is correct, but L271 hides that c-avg is significantly better for this user. Fix: "tied for the precise and casual users; constrained average linkage is ahead by 0.0027 [0.0010, 0.0045] for the error-prone user".

**m3 (Table II caption L290-292): "all rows differ only through the clusterer used" is inexact.** Each method's simulated user corrects that method's own clustering, so correction sets differ in size (precise user: ours 1,300, re-apply 1,338, c-avg 1,582) and "Now" F1 differs (0.9925, 0.9945). Fix: "each row has its own correction set" and explain "--" (frozen rule run for the precise user only).

**m4 (L313-315, abstract L43-44): the device-disagreement headline omits that it is small in practice.** exp21: frozen+log mean ARI between replicas 0.997 (EdgeFace-S) / 0.996 (MBF), replica F1 gap 0.0011 / 0.0019; the paper prints only the lowest ARI. Fix: add "mean ARI 0.997, F1 gap 0.001".

**m5 (L164-165, L240-249): design history not disclosed.** "The main protocol was fixed before any test number was computed" is true for exp14, but earlier scripts (exp9, exp11, exp12) already evaluated earlier clusterer versions on CALFW/CPLFW and on seed-0 libraries ("held-out for exp9"; exp12 "Attempt B: algorithm change"). CALFW/CPLFW are therefore not unseen, and the attach step and quality-gate design may have been informed by those looks (I cannot tell from the repo; confidence 3). Fix: one clause saying CALFW/CPLFW and seed-0 libraries were also used in earlier development rounds.

**m6 (L240-241): "did not help them" is imprecise.** The fine grid raised single linkage, DBSCAN and HDBSCAN by +0.0020 / +0.0021 / +0.0021 and lowered average linkage and First-Leader. Fix: "moved them by -0.0012 to +0.0021".

**m7 (L178-183): "grid over the same similarity range (0.20-0.70)" does not hold for ours** (link 0.40-0.70, attach 0.30-0.55, merge 0.40-0.60) or for Two-stage merge (0.30-0.60). The freedom disclosure is honest; the range statement is loose. Fix: "same upper bound 0.70".

**m8 (L333-340): synthetic copies fix component size.** Six rotated copies give six independent 8,290-face components, so per-component methods (c-avg 30 s to 234 s, 7.7x) look cheaper than for one real 50,000-face library, while ours grows 35x (0.44 to 15.4 s). The 50k ratios are therefore not predictive in either direction. Fix: add "component sizes are fixed by construction; our read is superlinear".

**m9 (L170-171): "Look-alike libraries add the 7-14 test people..." is misleading;** a look-alike library consists only of those 8-15 people (up to 60 photos each, no strangers). Fix: "consist of".

**m10 (L330): the 7.0 s rebuild time excludes reading the labels** (exp30 times build only; labels are read after the timer) while ours includes 0.5 s of reading. Conservative toward the paper. Fix: "7.0 s plus 0.5 s".

**m11 housekeeping:** exp28_testruns_edgeface_s.json untracked (61 MB); FIW bib authors "and others".

No CRITICAL findings.

## 3. Verified correct (scope of "exact"/"identical")
- Fast read step equals the original merge: 240/240 plain and corrected (random corrections, exp20) and 1,275 of 1,276 binding user corrections (exp26) with zero differences, both recognisers; the argument for the component split is sound. Scope: 8,290 clean faces and the 240 libraries.
- Order invariance of ours: F1 spread 0 and agreement 1.000 in all 8 conditions over 3 orders; the tie-break caveat (L158-160) is honest.
- Two devices (240/240 for ours and c-avg) and retraction (ARI 1 in 104/98 libraries) hold by construction; the abstract says "as any such design would".
- FIW protocol, family split (0 overlap), no tuning on FIW in the transfer run, interval reporting and the "probably too narrow" wording are consistent with exp31b.
- Tuning vs test data: exp14 tunes on tune-half libraries only, the recogniser is chosen on tuning ARI, CALFW/CPLFW are filtered by tune_ids, identity overlap is asserted 0, correction experiments use test libraries with nothing tuned, FIW transfer uses LFW-tuned parameters. I found no direct leakage of test sets into tuning in the code (see m5 for development history only).

## 4. Strongest counter-argument
The paper's own numbers say the method is no better than the standard, simple alternative. Constrained average linkage ties it without corrections (LFW, FIW, both recognisers), is as accurate or better with corrections (significantly better for the error-prone user, more forgiving at every error rate above 2%), and wins on CPLFW by 7-13 points. It shares every "consequence" the abstract advertises (device agreement, retraction, deletion) because those follow from recomputing from sets. What remains is a read step 9-15x faster, measured on synthetic rotated copies against a baseline the authors wrote themselves (SciPy's 174 s is a floor, not a competitor), while the index build (316 s) dominates at 50k anyway. The other "gaps" are against baselines the authors designed (frozen-label store, re-apply) with simulated users and devices, on benchmarks where baselines already score 0.99 or differences sit inside the intervals. The 15-run deletion test is vacuous with respect to corrections, the "exact" results are guaranteed by construction, and no real album, user or sync was tested. Acceptable as a careful engineering and measurement note; weak as evidence that this clusterer is a better choice than constrained average linkage with a faster merge.

## 5. Recommendations
- Methodology Reviewer: Minor revision (borderline major only because M1 and M2 are overclaims; both are wording fixes). Confidence 4/5.
- Devil's Advocate: Minor revision; the counter-argument is not fatal because the paper states most of it itself. Confidence 4/5.
