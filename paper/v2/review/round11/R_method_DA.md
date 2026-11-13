# Round 11 - Methodology Reviewer + Devil's Advocate (simulated seats, read-only)

Manuscript: cove_paper.tex at commit 75c87ec; line numbers refer to it. verify_paper_numbers.py re-run: 219 ok / 0 mismatch. No project file was edited. My checks that needed the 8,290-face embeddings ran from scripts in the session scratchpad (they import evaluation code but call no save_json). LaTeX page fit not checked.

## 0. exp30c_deletion_binding.py - independent audit (the test the paper's deletion sentence now rests on)
- Do the corrections bind before deletion? YES. corrections() takes only mistakes of the unconstrained clustering (same-person pairs in different clusters; different-person pairs in one cluster). Compared with canonical labels, `corrections_change_labels` is True in 15 of 15 rows of the JSON.
- Do the SURVIVING corrections still bind in the rebuild? YES (not stored in the JSON; I re-ran all 15 with the same RNG stream). For each run I built the remaining-faces clusterer, then added only the surviving corrections: the partition changed in 15 of 15. So the "2-10 that survive" are not dead weight. The survivors are a mix: in 4 of the 15 runs no must-link survives (only cannot-links), in one (30%, seed 2) no cannot-link survives.
- Is the comparison what the paper says? YES. Corrections are remapped through new_id; ids stay in the same relative order, so id tie-breaking is identical on both sides; must-link ties are by face content. The original also has a different batch split (64 at a time over all faces vs over the kept faces), so insertion batching is exercised too. It does NOT permute the order, so the "up to exact ties" caveat is untouched by this test (m2).
- Numbers in the deletion sentence (L324): 15 runs = 5 seeds x {1,10,30}%: correct. "7-10 corrections made": rows give 7,8,10,8,9 / 7,9,8,7,10 / 9,9,10,7,8, min 7 max 10: correct (my re-run: 2-5 must-links + 5 cannot-links). "2-10 survive": min 2 (30%, seed 1), max 10: correct. "identical in all 15": JSON identical_runs = 15, binding_runs = 15: correct. "random corrections, which did not change the labels, also gave 15 of 15": TRUE - I re-ran the exp30b correction sets (5 must + 5 cannot, random) on the 8,290 faces and the partition was unchanged in 15 of 15; exp30b identical_runs = 15. But see m1: this clause is in no stored file.
- Code oddities (harmless): the first loop in corrections() can never reach its break (it needs len(cans)>=k, which is filled only afterwards), so it always burns 200,000 draws; the docstring says "5 same-person pairs" but random-pair sampling finds only 2-5 (concentrated on a few many-photo people). The paper's "7-10" is the honest count.

## 1. Findings (no CRITICAL, no MAJOR)

### MINOR
**m1 (L324): the clause "random corrections, which did not change the labels, also gave 15 of 15" is true but unbacked by any stored result.** Evidence: exp30b_deletion_seeds_edgeface_s.json has `corrections_kept`, `identical`, `seconds` only; verify_paper_numbers.py checks only the 15/15. The no-change fact lives only in scratchpad re-runs (round 10 and mine). Fix: add `corrections_change_labels` to exp30b's rows (one rerun) and a verify line, or drop the clause.

**m2 (abstract L43-44, proposition L146-157, L324): "exact deletion" is empirically tested only with consistent (true-label) corrections, on one library, one recogniser, and without permuting order.** Evidence: exp30b/30c draw corrections from true labels; the conflict rule (L138-139: drop the less similar must-link) and the error-prone user's wrong corrections are never combined with a deletion; the proof sketch's "up to exact ties" matters precisely when cannot-links meet equal similarities (duplicate photos), which neither test creates. The abstract carries "By construction", so this is a scope nit, not an overclaim. Fix: in L324 add "(true corrections only; one library)", or run one 30c variant with the error-prone user.

**m3 (L266): "so the two are tied for the precise and casual users" does not follow from the clause before it.** Evidence: that clause says c-avg is better on the new photos for all three users (ours minus c-avg -0.0014 [-0.0026,-0.0002] precise, interval excludes zero; -0.0017 casual; -0.0057 error-prone). The "tied" rests only on the all-faces gap (+0.0010 [-0.0001,+0.0021]); the two metrics point in opposite directions and the sentence reads as if the second supported the first. Fix: "ours is ahead by a not significant +0.001 on all faces and behind by 0.0014-0.0017 on the new photos alone for the precise and casual users".

**m4 (Table I L212-214 vs L236-243 and abstract L37-39): Mixed and Look-alike are neither in Table I nor in the text, yet the headline "ties on average over the library conditions" (0.9854 vs 0.9857) is a mean over all eight.** Evidence: exp14 test: mixed ours 0.978 vs avg 0.981 (identity bootstrap -0.0025 [-0.0060,+0.0002]); look-alike 0.998 vs 0.994 (+0.0037 [0.0000,+0.0104]). The five shown conditions average 0.983 (ours) vs 0.984 (avg), so a reader cannot reproduce the headline from the table; the caption mentions only JPEG as omitted. Mixed is the only omitted condition where ours is behind. Fix: caption "JPEG, mixed (0.978 vs 0.981 for avg) and look-alike (0.998 vs 0.994) omitted; the means in Sec. V-A use all eight conditions."

**m5 (L329-330): the speed-up ranges mix baselines.** Evidence: exp29 at 50k: c-avg/ours = 234/15.4 = 15.2 and 212/20.0 = 10.6; SciPy/ours = 11.3 and 8.7, so "9 to 15" includes SciPy. At 8,290: c-avg/ours = 69 and 15.7, so "16 to 69" excludes SciPy (17.4 s gives 40 and 14). Fix: "14 to 69" at 8,290.

**m6 (abstract L39-40, Discussion L335-336): "within 0.003 F1 of constrained average linkage" is the all-faces gap; on the new photos alone the error-prone gap is 0.0057 (L266).** Not contradictory, but the abstract does not say which. Fix: add "on all faces".

**m7 (L77 vs L365-368): release wording.** "Code and per-run results will be released (URL below)" but the declarations say "in the repository (URL to be added)" and the AI paragraph says numbers were checked against "the released per-run results". There is no URL, and the per-run file behind the fine-grid/bootstrap result (exp28_testruns_edgeface_s.json, 61 MB) is still untracked in git. Fix: one tense ("will be released at [URL]") and `git add` that file or say it is omitted for size.

**m8 (abstract L37-40, L251-253): "ties" has no declared margin.** "Ties" is used for a mean gap with no interval (-0.0003), FIW (+0.0006 [-0.0046,+0.0061]) and "within 0.003". With 8 correlated conditions from the same 30 libraries these are consistent with small losses; the text does say "probably too narrow" where it matters. Fix: define "tie" once in Sec. IV (e.g. interval inside +/-0.01).

## 2. Spot-checked numbers not covered by verify_paper_numbers.py (all correct)
1. MBF CALFW ours 0.9367 vs avg 0.9551 (exp14_disjoint_mbf, whole sets) - ok.
2. MBF CPLFW ours 0.7865 vs avg 0.9164, "13 points" (12.98) - ok.
3. MBF occluded ours 0.9281 vs avg 0.9542 - ok.
4. Table I: all rows and columns match exp14 (EdgeFace-S), CALFW/CPLFW whole sets and the FIW run to 3 decimals; bold cells correct (Occluded Two-stage 0.95198 vs avg 0.95199 is a tie at three decimals, both bold); order-agreement row 0.562/0.758/1.000/0.997/0.983/1.000/1.000/1.000 - ok. Caption "four methods within 0.004" on FIW: 0.7855, 0.7849, 0.7834, 0.7822, spread 0.0033 - ok.
5. Fine grid: First-Leader -0.0012, Two-stage 0, Single +0.0020, DBSCAN +0.0021, HDBSCAN +0.0021, avg -0.0008, so the range -0.0012..+0.0021 (L237) - ok; avg 0.9849 vs 0.9857, ours budget-51 0.9809-0.9857 vs 0.9854 - ok.
6. Frozen replicas: mean ARI 0.9971 / 0.9958, lowest 0.885 / 0.914 ("0.89 and 0.91"), identical 127 / 74 of 240 (53% / 31%), F1 gap 0.0011 / 0.0019 - ok.
7. "1,276 cases, 1,275 changed": exp26 summed over both recognisers and three users: 1,276 library-user cases with corrections, 1,275 changed the partition (one EdgeFace-S error-prone library did not), zero differences - ok. These are cases, not distinct corrections.
8. Table II every cell, 0.9878 vs 0.9851, Held 20/23, 96/73, 100/100 - ok; casual new-photo gap -0.0017 - ok.
9. 162 of 1,528 wrong corrections; 207 of 240 libraries with a correction - ok.
10. "Superlinear, 0.44 to 15 s for six times the faces": exp29 ours_0: 0.44 / 1.67 / 4.81 / 15.42 s at 8,290 / 16,580 / 33,160 / 49,740 faces (6.0x faces, 35x time) - ok.
11. Orders (L182): exp14_disjoint.py `range(5 if method in ORDER_DEP else 3)`, ORDER_DEP = {First-Leader, Two-stage}; exp31b docstring says the same for FIW - the sentence is now exactly right. Grid sizes 360 vs 11, upper bound 0.70, step 0.05 - ok (36 x 2 x 5 = 360).
12. FIW first-leader order agreement 0.64; 34,692 / 5,773 / 2,320 (6.7%) - ok.
13. Scaling at 50k: 15.4 / 20.0 s, 234 / 212 s, SciPy 174 s, build 316 s (8.4 s at 8,290) - ok.
14. Single-linkage comparison "0.2 to 14 points except CPLFW (-0.5)": CALFW +0.2 ... occluded +14.3 ... CPLFW -0.5; attach removal -3.6 (occluded) and +5.1 (CPLFW) - ok.

## 3. Scope of "exact" / "identical"
- Abstract L41-44 ("By construction ... identical people on two devices ... exact retraction and deletion"): supported by construction plus 240/240 (devices, both recognisers), ARI 1 in 104/98 libraries (retraction) and 16 deletion runs; the abstract's last sentence says corrections, devices and users are simulated. OK (m2 for the one nit).
- Sec. III (L129-131) "identical partitions to the original merge": scope 240 library-condition pairs x 2 recognisers, 1,275/1,276 corrected cases and 8,290 faces - correct and stated.
- Sec. V-D (L324): scope now correct (binding corrections, 15 runs, 8,290 faces, EdgeFace-S). The "up to exact ties" caveat is carried by L147-157, Discussion L337-338 ("any such design shares them") and the Conclusion ("in simulation"). Not over-scoped anywhere.

## 4. Consistency after the trims
- Removed Mixed row: text no longer mentions it but the means still include it (m4).
- Intro "four ways to keep corrections" matches Table II (frozen is precise-only; caption explains "--").
- "will be released" vs "repository" (m7). Author-block placeholders and "Author contributions: to be completed" remain (known pre-submission items).
- No other contradictions: abstract 53%/31%, 20%, 73-96%, "about one wrong click in twenty" (+0.0009 at 0.05, interval includes zero), Discussion "clear up to about two in a hundred" (+0.0034 [+0.0015,+0.0054]) and the Conclusion all agree with the data.

## 5. Strongest remaining counter-argument
The paper's selling points are guarantees of the design (order independence, device agreement, retraction, deletion), which the paper itself says any recompute-from-sets clusterer shares, and constrained average linkage shares them while keeping corrections at least as well (significantly better for the error-prone user, more forgiving of wrong clicks). What distinguishes this clusterer is a faster read step, and that is not free: the speed comes from clustering cluster centroids after single-linkage cores, the same mechanism that loses 7 points (EdgeFace-S) to 13 points (MBF) on CPLFW. Accuracy parity is shown on LFW libraries where every method scores 0.98-0.99 and on FIW where everything is about 0.78; the speed ratio is shown on rotated copies of one library that fix component sizes, against a baseline the authors wrote (the independent SciPy floor narrows the lead to 9x), while the 316 s index build dominates at 50k anyway. So the evidence supports "a cheap, deterministic read step close to the standard method on easy data", not "a better clusterer". The paper words itself that way; the residual risk is a reader taking "ties" (m8) at face value.

## 6. Recommendations
- Methodology Reviewer: Accept with minor revision (m1, m3, m4 are worth fixing; the deletion-binding test now verifiably does what the paper says). Confidence 4/5.
- Devil's Advocate: Minor revision; no fatal flaw, and the counter-argument is largely stated by the paper itself. Confidence 4/5.
