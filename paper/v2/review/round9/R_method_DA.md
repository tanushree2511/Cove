# Round 9 - Methodology + Devil's Advocate (simulated reviewer)

Checked cove_paper.tex (commit 05a693e) against the results JSON. verify_paper_numbers.py: 199 ok. No LaTeX here, so pages are uncounted (Cove_paper.pdf is dated 10 Nov, stale). Braces, `$`, begin/end and every \ref/\cite resolve; Table I (9 cols) and Table II (6 cols) align with their headers.

## 1. Status of open items
Round 8: Dependent FIW libraries - PARTLY (text says "probably too narrow"; no family bootstrap; "+0.011 over single linkage" stated bare). Resized crops - PARTLY (6.7% named, no F1 without them). "Far below LFW" cause - FIXED ("probably"). MBF on FIW - FIXED (exp31 mbf, 0.783/0.782). Protocol lists FIW - FIXED. Retuned DBSCAN/HDBSCAN gaps - FIXED (+0.011/+0.016 match JSON). Two-stage/no-attach - PARTLY (caption only; attach shows nothing on FIW, text silent). Bold on 0.786 - FIXED. Interval for "ties" - FIXED (printed). Discussion "most methods score 0.99" - FIXED ("On the LFW libraries"). datasets/fiw ignore - FIXED (.gitignore line 130). "Public figures" - PARTLY ("mostly"). Bib "and others" - NOT FIXED (lines 496-508).
Round 7: break-even, "matches", "69 times" (now "single timings, twofold"), V-B sentence, "eight conditions", 53%/31% in abstract, "adding to FAISS" - FIXED. exp28_testruns still untracked (`??`) - NOT FIXED. Deletion "exact" is still one run plus a unit test - NOT FIXED. 0.9 s (ten batches) vs 8 s (batches of 64) for the same faces - PARTLY. Page count - NOT VERIFIABLE.

## 2. New or remaining problems
**MAJOR 1 - the wrong-click sweep is worse for ours than the text says.** exp25: at p=0.05 ours +0.0009 (CI includes 0) but constrained average linkage +0.0028 [0.0018,0.0038] and re-apply +0.0039; at 0.10 +0.0010 vs +0.0027 and +0.0037; at 0.20 ours -0.0057, c-avg -0.0009 (CI includes 0), re-apply +0.0025. Gap to c-avg is 0.0020 to 0.0051, so the abstract and Conclusion "within 0.003 F1 of constrained average linkage" holds only for the three fixed users. Also "A system with hard constraints must therefore show corrections" is false for c-avg, which is also hard-constrained. Fix: say the fragility is specific to our merge rule, name c-avg in that paragraph, and write "within 0.003 for the three simulated users; 0.005 at p=0.2".

**MAJOR 2 - protocol misstatement.** Sec. IV: "Every method runs in 5 shuffled orders". exp14_disjoint.py (line 205) runs only order-dependent methods 5 times; ours and the others run 3 (same for FIW). The empirical invariance check for ours is 3 orders. Fix: "5 for First-Leader and Two-stage, 3 for the rest".

**MINOR 3 - "identical people (53%, 31%)".** exp21: frozen+log mean ARI 0.997 and F1 gap between replicas 0.001; only the worst case (0.89, 0.91) is printed. Add the mean so readers see the practical gap is small.

**MINOR 4 - FIW headline.** Add "(libraries overlap)" next to +0.011, +0.040, +0.057, or run a family bootstrap. Add one clause: no-attach 0.783, Two-stage 0.782, so the attach step, the LFW gain, shows nothing here. FIW libraries have no singleton strangers; say so.

**MINOR 5 - by-construction results as findings.** "Exact retraction/deletion" and "keeps every consistent correction" follow from a set-based design; the abstract lists them as results. Put "by construction" once in the abstract; keep "one run" for deletion.

**MINOR 6 - "natural companion" / "advisable".** No test of a review view; the paper's own AUC of 0.60 says wrong clicks are hard to find. Write "would be needed; untested".

**MINOR 7 - scaling.** Ours grows 35x for 6x faces (0.44 to 15.4 s), build 316 s exceeds the baseline's 234 s total at 49,740. The text says "lead narrows" and the build; add "our read is superlinear".

**MINOR 8 - Table II.** "--" for the frozen rule (casual, error-prone) is unexplained; its 0.9928 is bold and above ours (0.9925). Say "run for the precise user only".

**MINOR 9 - bib/housekeeping.** Complete both FIW author lists and TPAMI volume/pages; track exp28_testruns; 12 unused bib entries are harmless.

Checked and correct: Table I all 9 rows plus order row; Table II all cells; 53%/31% (127, 74 of 240); +0.0034 at p=0.02 [0.0015,0.0054]; 1.9/2.2 s; 3.4-4.9 s; 0.877 s add; 9-15x and 16-69x; 1,276 cases (1,275 changed); retraction 104/98, AUC 0.60/0.63; upgrade 47%/48%; all FIW correction numbers; 6.7%.

## 3. Strongest counter-argument
The only rival with the same properties, constrained average linkage, is as accurate, handles wrong clicks and pose better, and ties on FIW. Ours wins on read-step speed on synthetic copies, while its index build costs more than the baseline's whole run. The consequence claims are measured against a baseline the authors designed, with simulated users. This is a careful engineering study, not a better method.

## Recommendation
Minor revision, bordering on major for items 1-2 (both are one-sentence fixes). Confidence 4/5. No CRITICAL issues.
