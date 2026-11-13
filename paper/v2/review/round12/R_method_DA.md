# Round 12 - Methodology Reviewer and Devil's Advocate
Paper: paper/v2/cove_paper.tex @ 49e33e2. Read-only audit; nothing edited except this file.

## 1. Audit of exp32_immich.py and the Immich sentence (tex line 245)

### M1 (MAJOR) Central face is not what is scored when the centre face has no person
exp32_immich.py lines 132-143: the loop skips every face with no `person`, then picks the best-scoring of the REMAINING faces. If the labelled central face is unclustered but a background face was clustered, that background face's person is used and the photo counts as "assigned". The docstring (lines 6-7) claims "the face at the image centre"; the code does not do that. Effect: a wrong person would lower Immich F1 (so 0.998 is, if anything, pessimistic), but the count of unassigned photos is biased low, and the protocol is mis-described.
Fix: pick the central face among ALL faces first, count the photo as unassigned if that face has no person, and rerun (or describe the rule as coded).

### M2 (MAJOR) "leaves 12-27% without a person" is probably mostly one-photo people, which no clusterer should group
Libraries hold 50-150 one-photo strangers (Sec. IV). Immich forms a person only from several faces (default min faces is 3 per Immich defaults; not checked in the repo), so one-photo strangers are never assigned. 147/94/77 unassigned are the same order as stranger counts. The sentence reads as a deficiency, and the F1 comparison excludes exactly those photos (the hard part of a library) for BOTH systems. The script does not report how many unassigned photos are singleton identities, so the claim cannot be judged.
Fix: report how many unassigned photos belong to one-photo identities, and say scored photos exclude them for both systems; otherwise soften "but leaves ...".

### M3 (MINOR) Percentage range off at the low end (line 245: "13--27%")
147/543 = 27.1%, 94/585 = 16.1%, 77/642 = 12.0% (11.99%). Lowest is 12, not 13. verify_paper_numbers.py lines 316-317 check 12 and 27, so it passes while the TeX says 13.
Fix: change "13--27" to "12--27".

### M4 (MINOR) Same-photo subset flatters both and the reader is not told
Ours on the same photos is 1.000 in all three (verified), but ours on all photos is 0.9994 (lib 12: 0.9982). A paired comparison on the subset Immich chose is fair for the stated claim, yet the subset is the easy part.
Fix: add "(0.999 on all photos)" or a clause that unassigned photos are excluded for both.

### M5 (MINOR) Reproducibility and validity of the Immich run
- The final run used re-downloaded models and forced reprocessing, but the script only calls `PUT /jobs/faceDetection {force:false}` (line 114). The forced reprocess is outside the script and not in exp32.log. In the log, library 1 hit "job start skipped: HTTP 400" (a job already running). The wait loop (lines 120-127) can hit the gap between the faceDetection and facialRecognition queues; the extra 10 s sleep mitigates but does not guarantee.
- Immich version, models and clustering settings are not recorded in the paper or the JSON; "default settings" is unverifiable.
- The three libraries are "the smallest", clean condition only (docstring line 3). The paper says only "three of the test libraries". N=3 and only one library has any error.
Fix: say "three smallest clean libraries"; record Immich version and settings in the JSON and a footnote.

### M6 (MINOR) Ground-truth noise
Labels are folder names; LFW photos can hold several faces, so label correctness depends on the central-face rule (M1). Library 12's single imperfection (20 Immich people vs 19 true, recall 0.991) is not diagnosed (split vs wrong label). I found no evidence of wrong labels and do not claim any.

### Verified correct for the Immich sentence
Immich mean F1 0.99849 -> 0.998; ours on the same photos 1.000 (all three libs); 543/585/642 photos; max unassigned 27%; one user per library (separate clustering); ours clustered on all photos then scored on the Immich-scored subset (lines 157-158), matching "same photos"; nothing tuned.

## 2. Did the cuts leave unsupported or contradicted claims?
- Abstract vs body vs conclusion: consistent. "7 points lower on profile photos" = 0.841 vs 0.909 (6.8). "within 0.003 F1 of constrained average linkage": largest gap error-prone 0.9851 vs 0.9878 = 0.0027. "one wrong click in twenty" matches +0.0009, CI includes zero. "53% and 31%" = 127/240, 74/240.
- Recogniser change: abstract no longer mentions it; Conclusion says corrections keep "about half their value", body gives 47% [38,57] and 48%. Supported. Related Work still lists "survive a change of recogniser" among unfound measurements; consistent.
- Cut FIW casual and error-prone numbers: no dangling references. Remaining FIW correction text (lines 266-269) cites casual 40% held and +0.0094, which are stated with their own figures. All \ref labels exist (sec:method, acc, corr, conseq, time, protocol; tab:acc, tab:corr); no reference to the removed figure.
- S1 (MINOR) Table I caption (line 202) says "the means in Sec. V-A use all eight conditions", but after the cuts Sec. V-A quotes no eight-condition mean difference, while the abstract claims a tie "on average over the library conditions". Fix: add one sentence with that mean difference or drop the caption clause.
- Discussion "re-applying and constrained average linkage stay positive to ten": re-applying is positive to 0.20, constrained average linkage to 0.10. True.

## 3. Spot checks (not in verify_paper_numbers.py)
1. 207 x 6.3 / 240 = 5.43 -> "5.4 over all". OK.
2. 127/240 = 52.9%, 74/240 = 30.8%. OK.
3. 30 libraries x 8 conditions = 240. OK.
4. exp29 at 49,740 faces: ours 15.4 / 20.0 s, c-avg 233.5 / 212.3, SciPy 174.4; ratios 15.2, 11.3, 10.6, 8.7 -> "9 to 15". OK. 
5. At 8,290: 30.3/0.44=69, 17.4/0.44=40, 19.6/1.25=16, 17.4/1.25=14 -> "14 to 69". OK. "0.44 to 15 s", build 316 s OK.
6. 8,290 x 6 = 49,740. OK.
7. FIW deltas from Table I: single +0.012 (text 0.011), DBSCAN +0.041 (0.040), HDBSCAN +0.057, First-Leader +0.031; differences are rounding of underlying values. OK.
8. Caption "four methods within 0.004" on FIW: ours 0.786, avg 0.785, no-attach 0.783, Two-stage 0.782. OK.
9. CPLFW: 0.841 vs 0.909 about 7 points; vs single 0.846 gap 0.5. OK.
10. Precise "now" gain 0.984 -> 0.994 = +0.010; Table II held values match text. OK.
11. Table II error-prone ours 0.9851 vs constrained avg 0.9878, as quoted. OK.
12. 980/2 = 490 test families. OK.
Items 10-12 and retraction counts (104/98, 5%/9%) are consistency checks against text and tables, not recomputed from raw runs; 1,571 identities, 360 grid points, 344 family slots not re-derived.

## 4. Strongest counter-argument (Devil's Advocate)
The Immich sentence is the weakest-evidence sentence in the paper and it sits beside the headline accuracy claim. Three smallest, clean, convenience-picked libraries; scored photos exclude everything Immich did not group (probably the one-off strangers, the hardest part of the library for any clusterer); the central-face rule is not implemented as described (M1); Immich settings and version are unrecorded; the final run needed forced reprocessing after failed runs, outside the script. The honest reading is "on easy clean photos both systems are near-perfect (0.998 vs 1.000)", which says nothing about order dependence, correction persistence or scale, the paper's actual claims. "Leaves 12-27% without a person" can be read as a rebuttal of Immich when it more likely reflects a minimum-cluster-size rule. More broadly, the accuracy story is a tie or loss to average linkage, and the set-semantics properties are ones the paper itself says any recompute-from-sets design shares (Sec. VI), measured against a frozen-label baseline of the authors' own design. The paper says this honestly, so it is a limitation, not a flaw.

## Recommendation
Methodology Reviewer: MINOR REVISION. Confidence 4/5. Numbers are clean; the issues are in the new Immich sentence and its script.
Devil's Advocate: MINOR REVISION; the sentence overreaches its evidence, the rest of the paper survives the cuts. Confidence 4/5.

Priority fixes: (1) "13--27" -> "12--27"; (2) count how many unassigned photos are singletons and say scored photos exclude them for both systems, else soften "but leaves ..."; (3) fix or disclose the central-face selection; (4) "three smallest clean libraries", record Immich version and settings; (5) resolve the Table I caption versus text mismatch on eight-condition means.
