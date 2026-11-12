# Round 6, Reviewer 3 (Perspective: local-first / privacy / deployment)

Manuscript: paper/v2/cove_paper.tex (after commit 000152d). I read the tex only. I did not compile it, so the 6-page limit is unchecked.

## 1. Prior issues (round 5)

1. Abstract "devices" and "exactly" read as shipped features. FIXED. The abstract now says "in simulation" and ends with "Only the clusterer is part of the application; corrections, devices and users are simulated". Fig. 1 caption adds "the application has no sync".
2. The scope paragraph does not say the app has no correction UI and wipes state on re-index. PARTLY. "Only the clusterer is part of the application" plus "A deployment needs a correction and undo interface" covers the main point. The overwrite-on-re-index fact is still absent. It is optional.
3. Stable cross-device face identity. FIXED. Method and Scope now say corrections must be keyed by photo hash plus face box. Tombstones are named.
4. Biometric embeddings and consent. FIXED. Scope has one sentence: exchanging faces means exchanging biometric embeddings, and real albums need the owners' consent.
5. "Review-and-undo makes corrections safe." MOSTLY FIXED. "Safe" is gone. The abstract says "should accompany", and the Conclusion says "advisable". Two small leftovers are listed as N1 and N2 below.
6. Frozen baseline looked like Immich's behaviour. FIXED. The abstract says "frozen-label rule of our design". Table rows are renamed. The Results text says 53% describes a plain edit log, not a deployed sync.
7. "Worth in practice" and small F1 gains. PARTLY. The Discussion now says "the measurements show what they are worth". The abstract leads with survival of fixes (20% kept by plain re-clustering). Nowhere does it say plainly that the F1 gain is about one point on libraries already near 98.5%.
8. Scaling labelled in the abstract. FIXED. The abstract says "synthetic libraries". The 316 s index build is reported.
9. Deletion is simulated, not in the app. MOSTLY FIXED. Covered by "Only the clusterer is part of the application". The test deletes random faces, not whole photos or whole people, and the text does not say so.
10. Concurrent retract and re-add. FIXED. Scope says tombstones are needed and the case is "not tested".
11. "Up to exact ties" missing from the contribution bullet. NOT FIXED. Only the Proposition carries the qualifier. The first bullet and the abstract's "function of the set" do not.
12. AI-use disclosure. Fine. It is frank and names the verification script.

## 2. New or remaining issues

N1. MINOR. Discussion: "gain from corrections is clear up to about two wrong clicks in a hundred."
- The Results text reports gains only at p = 0, 0.05, 0.10 and 0.20. The 0.02 value is not stated, so the claim cannot be checked from the text.
- The abstract and Conclusion say "gone by about one in twenty", and the Discussion says "small at five to ten". These three phrasings differ.
- Fix: report the p = 0.02 gain with its interval in the sweep sentence, and use one wording everywhere.

N2. MINOR. Abstract, Discussion and Conclusion: "review-and-undo view should accompany them" and "natural companion".
- The data show that retraction is exact. They do not show that users can spot a wrong click (the cosine test has AUC 0.60, and no user was tested).
- Fix: "we recommend, and will test with users". The Conclusion's last sentence nearly says this already.

N3. MINOR. Discussion: "the measurements show what they are worth."
- Add "on these simulated libraries" and one number: about +0.01 F1, against 80% of fixes lost under plain re-clustering.

N4. MINOR. Method, step (1): "ties by the faces' content, not their ids". The proof says "Edge ties are broken by face id, which depends on insertion order".
- These two statements conflict.
- The content-based tie-break is also never defined. It is the same identity issue the paper elsewhere hands to a "photo hash and face box".
- Fix: say which tie-break is used in the code and in the proof. Add "up to exact ties" to the first contribution bullet (issue 11).

N5. MINOR. Declarations, "Ethics: public benchmark data only."
- LFW, CALFW and CPLFW are scraped web photos of public figures, and faces are biometric data. Datasets of this kind are ethically contested.
- Say that the data are existing public benchmarks, that no new images were collected, and that no per-demographic error analysis was done. Grouping errors may differ across groups, and the paper's "look-alike" and "wrong merge" cases are the risky ones.
- A local-first photo tool can also be turned into a tracking tool. One sentence is enough: the clusterer runs on the user's device and does not identify named individuals.

N6. MINOR. Sync privacy. Scope names the biometric risk, but there is no design note beyond consent. Add "device-to-device encrypted exchange" to the list of deployment needs, or exchange only face ids, hashes and pairs rather than embeddings (embeddings can be recomputed on each device).

N7. MINOR (submission blocker, not a content issue). The author block still has placeholders ([College name], [City], [email]), and "Author contributions: to be completed". Fill these in before submission.

N8. MINOR. Intro: "the Cove system studied here group faces on hardware the user controls." This is true of the clusterer only. It is fine given the sentence at the end of the Introduction, but "studied here" could be "whose clusterer we study".

## 3. Framing assessment

The paper now leads with findings and is honest about being simulation-only. The title says "A Simulation Study", the abstract's last sentence and the Introduction say only the clusterer is in the app, and the Scope paragraph lists the designed baseline, shared-people intervals and synthetic copies. The remaining overreach is small word choices, such as "exact", "worth" and "natural companion". The practical-impact claim is appropriately modest: the value is in the guarantees (agreement, retraction, deletion, kept corrections), not in F1.

## 4. Recommendation

Accept with minor revision. This is a weak accept for a local IEEE conference. Confidence 4/5.
No CRITICAL or MAJOR issues remain. The N1-N8 edits are about eight short sentences, and the main ones are N4 (tie-break conflict), N5 (ethics sentence) and issue 11.
