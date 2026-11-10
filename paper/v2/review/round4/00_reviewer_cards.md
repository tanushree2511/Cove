# Simulated peer review, round 4: field analysis and reviewer cards (awaiting confirmation)

**Manuscript:** `paper/v2/cove_paper.tex` (commit ab09dbe), "Face Grouping That Keeps the User's Corrections:
Order-Invariant Incremental Clustering for Local-First Photo Libraries" (title not yet changed).
**Mode:** full (simplified run, as in rounds 1–3). Five role-separated seats; simulated reviewers, not real peer review.
**What is reviewed:** the draft as it stands after adding experiments E1–E5. It is NOT yet cut to 6 pages and NOT compiled.
The review comes before the cuts on purpose, so that the cuts follow what the reviewers consider important.

## Field analysis

| Dimension | Result |
|---|---|
| Length | Abstract 242 words; about 5,300 words of text; 3 tables; 46 cited references; estimated 6.5–7 IEEE pages (not compiled) |
| Primary discipline | Computer vision / pattern recognition (face clustering) |
| Secondary disciplines | Data mining (constrained and incremental clustering); systems (local-first software, replicated state); HCI (interactive correction) |
| Paradigm / method | Empirical: an algorithm, a proof sketch and a corollary, and simulation-based evaluation on public face datasets |
| Target venue | IEEE regional or national computing conference in India (6-page limit) |
| Maturity | Fourth draft, before submission. Round 3 verdict was Minor Revision (borderline Major on claim sizing) |
| New since round 3 | Exact fast read step (E1); two-device agreement (E2); exact retraction of a wrong correction (E3); corrections across a recogniser upgrade (E4); error-rate sweep (E5); constrained average linkage timed directly; new-face F1; number fixes |

## Cards

| Seat | Identity and focus |
|---|---|
| Journal-Fit Reviewer | Programme-committee member of an IEEE India regional computing conference. Checks whether the paper now has one clear contribution (corrections that stay put, converge and can be undone) or reads as a list of experiments; whether the claims are sized correctly after the fair baselines (accuracy is a tie, not a win); whether the abstract and conclusion over-claim anywhere; whether effect sizes of 0.001–0.005 F1 on simulated libraries are enough for a regional-conference paper; whether the title still matches the content; the 6-page fit; the AI-disclosure paragraph. |
| Reviewer 1 (Methodology) | Clustering-evaluation researcher. Audits every new number against `evaluation/results/*.json` (exp20–exp25). Checks: the exactness test with corrections (what corrections did it really use, and do they bind?); the two-device design and whether the frozen-label-with-edits baseline is a fair opponent or a strawman; the retraction test (is it more than "remove from a set and recompute"?); the retention ratio and its bootstrap; the timing comparison (NumPy constrained average linkage against our code, machine load between runs); the error-rate sweep denominators and intervals; consistency between the abstract and Tables II–III; the round-3 number fixes. |
| Reviewer 2 (Domain) | Constrained-clustering and face-clustering researcher with a distributed-systems background. Checks the new related-work claims: CRDT and local-first software (Shapiro et al.; Kleppmann et al.), backward-compatible embeddings (Shen et al.), noisy-constraint and retractable-constraint literature. Checks whether the Corollary ("any method that recomputes from the sets has (i) and (ii)") is stated correctly, whether "applies CRDT to face clustering" is a fair description, whether the novelty sentence ("we did not find ...") is bounded properly, and which prior work is still missing. Verifies that the three new bibliography entries are real and correctly described. |
| Reviewer 3 (Perspective) | Local-first software engineer and privacy practitioner. Checks the gap between what is measured and what the app does: Cove has no correction interface, no sync between devices, and no undo, so the three consequences are simulated. Asks what the "two devices" result means without a sync protocol, how a user would find the wrong correction to retract (the AUC is 0.60), what a recogniser upgrade means for stored embeddings and storage, what 0.001–0.005 F1 means to a person, and whether the privacy and API-exposure text is still accurate. |
| Devil's Advocate (fixed) | Challenges the paper's reason to exist. Everything in Sec. VI-D follows from "recompute from the set of faces and corrections", which is a one-line corollary; constrained average linkage has the same properties; the one remaining advantage is cost, and part of that gap is an implementation difference (NumPy against a compiled library). Effect sizes are in the third decimal. The frozen-label baseline with replayed edits was designed by the authors. Simulated users stand in for people. Asks whether this is a paper or an evaluation note, and whether a reader learns anything that is not obvious. |

## Editor's pre-review notes (from my own audit after the round-3 fixes; for the seats to confirm or refute, not conclusions)

1. **Exactness test with corrections.** `exp20_exact_read.py` draws random corrections. Counting them for the 240 libraries gives, on
   average, 8.2 per library: 2.2 correct "same person", 4.0 "different people" between random faces (which rarely bind), and 2.0 wrong
   "same person". The paper text says "twelve corrections each". The text is inaccurate, and the test is weaker than it sounds.
   A stronger version (the exp19 users' real corrections) has not been run yet.
2. **Abstract.** "Constrained average linkage is within 0.002 F1 of it" is true for the precise user (ours +0.0011) and the casual user
   (+0.0003), but not for the error-prone user (ours −0.0027 on all faces, −0.0057 on new faces).
3. **Same quantity, two values.** Read time with the original merge is 3.4 s (exp18) and 4.9 s (exp20); our read step is 0.5 s (exp20)
   and 0.3 s (exp24). The machine load differed between runs.
4. **Not compiled.** Page count unknown. The three new bibliography entries have no volume, pages or DOI.
5. **E5, the 57% against 34%.** Checked: the denominators are similar (100 against 103 libraries below the target at the start), and
   constrained average linkage starts slightly higher on the "now" photos (0.9862 against 0.9842).
