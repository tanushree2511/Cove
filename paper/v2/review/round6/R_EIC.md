# Round 6 - Journal-Fit Reviewer (R_EIC), simulated re-review of commit 000152d

Recommendation: MINOR REVISION. Confidence 3/5.
The science and tone are now sound and the over-claim is gone. Two things block submission: placeholders and the page limit. I could not compile (no LaTeX here; the PDF in paper/v2 is dated 10 Nov and stale), so the page count is an estimate from content.

## Page-limit estimate
About 4,400 body words (4,695 counting tables and captions), about 4.5 pages of running text. Add Table I (full width, 10 rows, about 0.3 page), Tables II and III (about 0.35), three figures (about 0.55), 40 cited references (about 0.9) and the title and abstract block. Total is about 6.7 to 7.3 pages. Six pages is not plausible without cuts of about 0.8 to 1.0 page:
(a) drop Fig. 2 and keep its numbers in text (0.2);
(b) drop Table I rows JPEG and Mixed (0.07);
(c) compress the Sec. IV Corrections paragraph, the Exact-read-step validation sentence and the Sec. V-D scale paragraph (0.3);
(d) merge Declarations into the Acknowledgment (0.1);
(e) cut Related Work by 4 lines (ruiz2009cdenstream, lasek2019density, mazumdar2017noisy) (0.1);
(f) shorten Discussion and Conclusion, which repeat the abstract (0.15).
Confirm on Overleaf.

## Prior issues (round 5)
1. Over-claim "beneficial up to 1 in 20": FIXED. Abstract, Discussion and Conclusion now say the gain is gone at about 1 in 20 and give the p=0.05 and p=0.10 numbers with "intervals include zero".
2. "Rules fixed before any test number": FIXED. Sec. IV now calls the later checks "additions".
3. Placeholders: NOT FIXED. [College name], [City], [email] and "Author contributions: to be completed" are still there.
4. Length: NOT FIXED. Fig. 2, all Table I rows and the separate Declarations are still there.
5. Conclusion mixed metrics: FIXED. It now says 0.9925 after the next import against 0.985.
6. Abstract hides CPLFW weakness: FIXED. It now says "behind on low-res and profile ones, by up to 7 points".
7. Attach statement: FIXED. It now gives the CPLFW gain. See N3 for a rounding nit.
8. Sweep vs error-prone user: PARTLY. The look-alike targeting is stated in Sec. IV, but no sentence says that is why the two results differ.
9. Garbled c-avg timing sentence: PARTLY. It is better but still one long parenthetical. The abstract still says "constrained average linkage" without "our implementation".
10. Undefined terms: NOT FIXED. First-Leader, Two-stage, Ours-no-attach, MBF and Cove are still undefined in Sec. IV.
11. Immich-style label: FIXED. It is now "frozen-label rule we designed". "Immich's default threshold" is uncited.
12. 1,571 identities vs 79 + 1,844: NOT FIXED.
13. Sign of the frozen difference ("-0.0003"): NOT FIXED. Table II shows frozen higher.
14. Floating-point caveat: FIXED. The Proposition now says "in exact arithmetic".
15. AI-disclosure: NOT FIXED. It is not retitled and does not say the authors checked references and code.
16. One-sentence contribution: PARTLY. "Known parts" is stated, but the three bullets still read as three studies.
17. Plain-language note on small differences: NOT FIXED.

## New issues
N1 MINOR - Abstract and Sec. V-A. "Within about one point of average linkage ... by up to 7 points" contradicts itself. Fix: "within one point on libraries, 7 points lower on CPLFW".
N2 MINOR - Sec. V-B. "it is better for all three users (ours -0.0014 ...)": "it" is unclear, and the interval excludes zero in favour of constrained average linkage. Fix: "constrained average linkage is better on the new photos alone (by 0.0014 for the precise user, 0.0057 error-prone)".
N3 MINOR - Sec. V-A. "gains 5.2 on CPLFW" but Table I gives 0.892 - 0.841 = 5.1. State 5.1, or add a digit.
N4 MINOR - Number consistency. Sec. III says 210-216 pairs per user got corrections; Sec. V-B says 207 of 240 for the precise user. Say which recogniser each number belongs to. Also "1,276 cases" is not explained.
N5 MINOR - Sec. V-D. "16 to 69 times at 8,290 faces" cannot be derived from the numbers printed (the 8,290-face constrained times are missing). Print them, or drop the claim.
N6 MINOR - Discussion. "Clear up to about two wrong clicks in a hundred": no p=0.02 value appears in the text. Add it.
N7 MINOR - Discussion. "within 0.003 of ... a frozen-label rule" is true for EdgeFace-S only. With MBF the frozen rule is 0.009 lower.
N8 MINOR - "Code and per-run results are released" gives no URL. Add one, or "anonymised link on request".
N9 MINOR - Look-alike libraries are discussed in text but have no row or number.
N10 MINOR - The abstract is dense (about 230 words, about 15 numbers). Cut one or two for a regional audience.

## Strengths
Honest losses are stated. A single core property is stated with a proof sketch. The baseline set is fair, with finer-grid re-tuning. Abstract, Conclusion and Discussion now agree with each other and with Tables II and III. I spot-checked 53%, 127 and 74 of 240, 5% and 9%, 104 and 98, 0.9925 against 0.985, and the single-linkage range 0.2 to 14. All agree.

## Summary
Minor revision, confidence 3/5. No CRITICAL issues. Blockers: placeholders (MAJOR) and length of about 7 pages against a 6-page limit (MAJOR). Fix the undefined terms, the 207/210 mismatch, and the sign and clarity of the c-avg comparison.
