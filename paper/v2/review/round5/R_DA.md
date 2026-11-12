# Devil's Advocate Review: round 5

**Manuscript:** `paper/v2/cove_paper.tex` ("Order-Independent Face Grouping with Persistent User Corrections: A Simulation Study for Local-First Photo Libraries"). Simulated reviewer, not real peer review.
**Seat:** Devil's Advocate. Blind to the other round-5 seats (nothing in round5/ read). Read: the manuscript, round-4 `00_reviewer_cards.md`, round-4 `R_DA.md`.
**Scope of checking:** text-only audit this round (no code run, no result JSONs re-opened). Where I compare table cells with prose I did the arithmetic from the manuscript. Anything needing the JSONs is marked "verify".
**Calibration Status:** NOT_CALIBRATED. Abbreviations: "c-avg" is constrained average linkage; "avg link" is plain average linkage.

## Strongest counter-argument (about 270 words)

The rewrite converted a tie paper into a win paper by selecting the cells where the method is ahead. Of nine conditions in Table I, ours is ahead of average linkage on three (clean, blur, dark), by 0.002 to 0.006 F1, which is at most about one face per library. Ours is significantly behind on low-res and on CPLFW (6.8 points), and its largest point loss, occluded (-0.0089), is filed under "not distinguishable". The abstract's "the more accurate method on clean, blurred and dark photos" quotes an interval only for clean; for blur and dark none is given, and the text itself says the people-level bootstrap "widens the intervals". At the 51-configuration budget the authors themselves introduce, ours scores 0.9836 overall against 0.9849 to 0.9857 for average linkage, so under equal tuning freedom the "more accurate" claim reverses.

The "positive" results then fall into two groups. Group one (devices agree, retraction exact, deletion exact, corrections kept) is true for any recompute-from-sets design. The paper says so in Sec. III and then lists them as results in the abstract. The only opponent that fails them is a frozen-label store the authors designed, with edits replayed "in received order", i.e. the version that diverges by construction. Group two (the speed advantage) is measured against c-avg, a method nobody ships for photo libraries, and only the read step is timed. At 49,740 faces, building the index took 316 s, longer than the whole baseline (174 s).

Finally, "corrections remain beneficial up to one wrong click in twenty" is contradicted by the paper's own sweep: +0.0009 at p=0.05, interval includes zero. "Safe" rests on an undo view never tested, with a detector at AUC 0.60. Everything is measured on a benchmark at F1 0.985 before any correction.

## Issue list

Counts: CRITICAL 0, MAJOR 5, MINOR 10.

### CRITICAL
None. No single defect invalidates the work. The MAJOR items are over-claims that a reader can check against the paper's own numbers in minutes, so they should be fixed before submission.

### MAJOR

**M1. "Beneficial up to about one wrong click in twenty" contradicts the paper's own sweep.**
- Location: Abstract "Corrections stay beneficial up to about one wrong click in twenty"; Sec. V-B "$+0.0009$ at 0.05 and $+0.0010$ at 0.10 (intervals include zero)"; Discussion "corrections stay useful up to about one wrong click in twenty"; Conclusion "Corrections remain beneficial up to about one wrong click in twenty".
- Dimension: Overgeneralisation / logic chain.
- Problem: at p=0.05 the measured gain is statistically zero by the paper's own statement; at p=0.10 it is +0.0010 (also zero, and non-monotone, so the cut-off at 0.05 is arbitrary within noise). The error-prone user (p=0.1) ends at 0.985, "no better than discarding the corrections". Round 4 asked for the crossing point to be stated; the authors chose the generous end (1 in 20) over the last point with a positive interval, which the text never shows (the earlier p=0.02 value was dropped from this draft).
- Fix: replace with "clearly beneficial up to about one wrong click in fifty (p=0.02, +0.0034 [verify interval]), indistinguishable from none between one in twenty and one in ten, harmful at one in five". Report p=0.02 in the text and Fig. 2 caption.

**M2. "The more accurate method on clean, blurred and dark photos" is a selected-cell claim and does not survive the paper's own tuning check.**
- Location: Abstract "it is the more accurate method on clean, blurred and dark photos"; Sec. V-A "ours is better on clean ($+0.0059$, ...), blur ($+0.0038$) and dark photos ($+0.0022$)".
- Dimension: Cherry-picking / statistics.
- Problem: (a) only clean has an interval; blur and dark have none, and the sentence before says the people bootstrap "widens the intervals". Which bootstrap produced the quoted intervals (library or people) is not stated. (b) Against HDBSCAN on blur (0.995 vs 0.997) the margin is 0.002. (c) The same paragraph reports ours at 51 configurations scoring 0.9836 (range 0.9809 to 0.9857) against 0.9849 and 0.9857 for average linkage overall, so at equal tuning budget the average is lower, and per-condition numbers for that setting are not shown. (d) The abstract does not mention the significant losses (low-res -0.0061 [-0.0139,-0.0008]; CPLFW -0.068) while naming the three wins. (e) Effect sizes are below one face per library (round 4, m3, still unaddressed).
- Fix: abstract: "matches average linkage overall (0.985 vs 0.986), ahead on clean photos, behind on low-resolution photos and on pose-varying whole sets". Give intervals for blur and dark or drop the sentence. State which bootstrap each interval uses.

**M3. The abstract presents consequences true by construction as results, against an opponent that diverges by design (carry-over of the external reviewer's "true by construction" and of round-4 M2).**
- Location: Abstract "two simulated devices end with identical people (53\% for a frozen-label rule with replayed edits), a wrong correction can be retracted exactly, deleted photos are handled exactly"; Sec. IV "second device replays the other's edits in received order. This baseline is our own design"; Sec. V-C "it is what a plain edit log lacks".
- Dimension: Logic chain / alternative paths.
- Problem: Sec. III concedes these hold for any recompute-from-sets method, and Table III marks the c-avg retraction "n/r (it would match by construction)", yet the abstract credits them to "the clusterer". The 53% opponent is one that never merges logs or labels. A merged event log replayed in a fixed (time, device) order converges 100% and supports exact undo by dropping the event. Round 4 reported this (Check B: 98.6% of corrections held, F1 0.9886 vs 0.9933) and the text still says "plain edit log". "Edit log" and "replayed in received order" are different designs.
- Fix: in the abstract say "by construction" and name the opponent as "a frozen-label store that replays edits in arrival order". Add one row (merged ordered log) to Table III or change the sentence in Sec. V-C to "a store that replays edits in arrival order".

**M4. Replication claims ignore retraction and deletion across devices (tombstones).**
- Location: Fig. 1 caption "exchanging the two sets between devices, or deleting one pair, gives the same result as starting again"; Abstract "two simulated devices end with identical people ..., a wrong correction can be retracted exactly, deleted photos are handled exactly"; Sec. V-C "Two devices" test.
- Dimension: Logic chain / overgeneralisation.
- Problem: the two-device test is a single exchange of grow-only sets. Retraction and deletion are tested on one device only. If device A retracts a pair or deletes a photo while device B still holds it, a set union brings it back; exact convergence then requires removal records, and the paper's design of the set exchange is not defined for them. The caption combines two operations that were never run together. Round 4 raised this as an observation and the authors have since added deletion, which makes the gap material. The condensed Scope paragraph no longer mentions it.
- Fix: either run the combined case (retract on A, add on B, exchange, with tombstones for removed pairs and faces) or add to Sec. V-C: "removals need a record of removed pairs; we did not test sync of removals".

**M5. "Roughly an order of magnitude faster up to 50,000 faces" is a read-step ratio against a baseline outside the practical frontier, on a synthetic scale test whose structure favours the method.**
- Location: Abstract "reads the groups roughly an order of magnitude faster up to 50{,}000 faces"; Sec. V-D "Larger libraries are synthetic ... each copy under its own random rotation, so copies are unrelated"; "Building the flat FAISS index in one batch took 316\,s at 49{,}740 faces"; Conclusion "at a read step roughly an order of magnitude faster than constrained average linkage".
- Dimension: Overgeneralisation / so-what.
- Problem: (a) Six rotated copies give six disjoint libraries of 8,290; the threshold graph never has one giant component, which the exact split exploits. Round 4 found a 97% component in real 8,290-face data; a real 50k library does not behave like six independent copies, so linear scaling is a property of the construction. (b) Only the read step is timed. Index build at 49,740 faces (316 s) exceeds the compiled baseline (174 s), so end-to-end ours is slower at the largest size. (c) Scaling inconsistency to explain: adding 8,290 faces in ten batches and updating links took 0.15 s, but one-batch flat index building at 49,740 faces took 316 s, a factor of about 2,000 for 6x the faces. "Quadratic" predicts about 36x (about 5 s). Either the 0.15 s excludes the range searches or the 316 s includes something else. (d) The 9 to 15x compares with the unconstrained SciPy lower bound and a caching Python version; the 16 to 69x at 8,290 faces mixes baselines and it is unclear which ratio belongs to which. Round 4 measured only 2 to 4x against a compiled c-avg at 8,290 faces (verify against the new code). (e) The practical alternative (the frozen store) has no read cost at all, so a speed comparison against c-avg answers a question few users ask. Also check memory: a 49,740-face condensed float64 matrix is about 9.9 GB on a 12 GB laptop, so the 174 s may include swapping.
- Fix: restate as "the read step stays below 20 s at 50k faces (synthetic, disjoint copies); the compiled unconstrained lower bound is 174 s; index build 316 s dominates". Give a table with n, ours, baseline name per cell, and the end-to-end total. Delete "order of magnitude" from the abstract or tie it to "read step, synthetic".

### MINOR

**m1. "Matches average linkage without corrections to about one point" is loose, and "matches constrained average linkage in accuracy" hides a loss.**
- Location: Abstract lines 37 and 39. Table II error-pr. column: ours 0.9851 vs c-avg 0.9878 (-0.0027); new-photo F1 of ours is lower for all three users (Sec. V-B, -0.0014 to -0.0057).
- Problem: "about one point" excludes the 6.8-point CPLFW loss; "matches" glosses the error-prone column and the new-face deficit, which the body calls "tied, not ours ahead".
- Fix: "within 0.3 points overall, and within 0.003 F1 on corrected libraries except when clicks are wrong".

**m2. Conclusion mixes the "now" F1 with the "later" F1.**
- Location: Conclusion "keeps corrections across imports (F1 0.984 to 0.994; 20\% survive plain re-clustering)".
- Problem: 0.984 to 0.994 is the gain on the "now" photos before any import. After the import the table shows 0.9854 to 0.9925 (+0.007). The sentence ties the 0.994 to "across imports".
- Fix: "(F1 0.985 to 0.9925 after the next import; 20% survive plain re-clustering)".

**m3. Look-alike condition is discussed but missing from Table I.**
- Location: Sec. V-A "not distinguishable on JPEG, mixed ..., occluded ... and look-alike libraries"; Table I has seven library rows and two whole-set rows, no look-alike row.
- Problem: look-alike libraries (the hard-negative case most relevant to wrong merges) cannot be checked, and "240 pairs" (30 x 8) assumes it exists.
- Fix: add the row or one sentence with the numbers and interval.

**m4. Removing the limitations list dropped items that matter, and "likely too narrow" became "resample libraries".**
- Location: Sec. VI "Scope and next steps" "intervals for corrections resample libraries".
- Dimension: Hidden limitations.
- What is now hidden or weakened: (1) the direction of the interval bias (round 4: "likely too narrow", 30 libraries sharing 79 family identities). The people bootstrap was added for Table I only; the correction intervals (Table II, Fig. 2, E4) still ignore the identity reuse. (2) The wrong-click rate, the one parameter that decides the result, is an assumption; one sentence says the users are simulated but not that p was chosen by the authors. (3) Cluster identity: "up to renaming of clusters" means names, cover photos and hidden people need matching after every recompute, which "Persistent User Corrections" in the title implies is solved. (4) Tuned thresholds are from one dataset; threshold transfer to other data and to MBF is not stated (are MBF thresholds re-tuned?). (5) Sorting by face id breaks ties by insertion order. (6) The frozen rule was run only for the precise user (Table II dashes). (7) Detection and face ids: corrections name faces, so a recogniser or detector change alters ids (see m6).
- Fix: restore a four-line list in Scope: interval reuse, assumed wrong-click rate, no cluster-identity handling, no real photos or users.

**m5. "Safe", "natural companion" for review-and-undo are untested.**
- Location: Abstract "so a review-and-undo view is the natural companion"; Conclusion "pairing them with a visible, removable list makes them safe to use"; Sec. V-C "Finding the wrong click is hard: ... AUC of only 0.60".
- Problem: the experiment retracts a click known to be wrong; no finder, interface or user is tested, and the only detector tried is near chance. "Safe" is an engineering conclusion with no evidence.
- Fix: "a review-and-undo view is needed; we did not test whether users can find wrong clicks".

**m6. Upgrade experiment is on a selected subset.**
- Location: Sec. IV "the 210 libraries whose faces are identical under both recognisers"; Abstract "corrections keep about half their gain under a different recogniser".
- Problem: 30 of 240 library-condition pairs are dropped because the face sets differ, likely the degraded conditions where detection varies. A real upgrade changes the face set and ids, which breaks the corrections that name faces. "All 1,372 held" is by construction. The 47% has no comparator (carry-over of round-4 m4).
- Fix: say which 30 pairs were excluded and why, and add a sentence on face identity across detector changes.

**m7. Over-reach of the "local-first" label and the "two devices".**
- Location: Title "for Local-First Photo Libraries"; Intro "Local-first managers such as Immich, PhotoPrism, FaceCluster"; Abstract "two simulated devices".
- Problem: Immich and PhotoPrism are self-hosted servers, not local-first in the Kleppmann sense (offline-capable replicas). Nothing measures offline operation, multiple physical devices, sync transport or bit-identical embeddings across hardware (different ONNX runtimes or CPUs can shift embeddings). "On-device" cost is a laptop read step; detection and embedding time are not reported.
- Fix: "self-hosted and on-device photo managers"; add one sentence that the devices are two copies in one process and embeddings are assumed bit-identical.

**m8. Proposition: wording stronger than the proof.**
- Location: Abstract "output is a function of the set of faces and the set of must-link and cannot-link corrections"; Proposition "up to exact ties"; proof "Edge ties are broken by face id, which depends on insertion order"; Sec. III "ties by the faces' content, not their ids".
- Problem: must-link ties use content, core-link ties use ids. The abstract states an unconditional function of the set. Float-level non-determinism of range search across batch shapes (BLAS kernel differences near a threshold) is not covered. Round-4 Check C (noise 1e-4, 30 of 30 identical) supports the claim but is not in the paper.
- Fix: break core-link ties by content too (one line), or put "up to ties" in the abstract, and cite the noise test.

**m9. Deletion evidence is one run.**
- Location: Sec. V-D "Deleting a random 10\% of the faces took 0.59\,s ... with identical labels"; Abstract "deleted photos are handled exactly".
- Problem: one library of 8,290 faces, one random 10%, one seed; the unit test is not described (sizes, with or without corrections). "Drops corrections that name them" removes a transitive link a-b, b-c when b is deleted, so the user's implied a-c is lost; "exactly" means "equal to never having added them", not "preserving user intent".
- Fix: say "equal to never having added them (unit test plus one 8,290-face run)"; note the transitivity loss.

**m10. Statistics and housekeeping.**
- Location: Sec. IV "1{,}571 identities" vs "(79 per half)" and "(1{,}844 per half)"; Sec. V-A throughout; author block; Declarations "to be completed".
- Problem: (a) 79 + 1,844 = 1,923 identities per half, but the bootstrap uses 1,571; the reader cannot reconcile them. (b) About 9 conditions x 7 baselines are compared with no multiplicity statement, and "not distinguishable" is used for intervals that are mostly negative (occluded -0.0089 [-0.0219,+0.0072]). (c) The author block still holds "[College name]", "[City]", "[email]" placeholders and "Author contributions: to be completed" (the source comment says do not submit them). (d) The 6-page fit cannot be confirmed from the manuscript alone (a 9-column table*, 3 figures, about 4,200 words; the PDF in `paper/v2/` may be stale), so compile and count before submitting.
- Fix: reconcile the counts, add "intervals are unadjusted", fill the placeholders, compile.

## "So what?" test

One sentence the paper can defend: "Storing corrections as face pairs and recomputing the groups from the two sets gives order-independent people that keep every correction, at no accuracy cost on a saturated benchmark and with an inexpensive read step; hard corrections stop helping at around one wrong click in fifty."
- A reader learns (1) leader clustering is order dependent (known), (2) a hard-constraint design is as accurate as c-avg (expected), (3) the error-rate crossing (new, useful), (4) the recogniser-change retention (new, no comparator).
- A reader does not learn that the method is better than what an application engineer would use (frozen labels plus an ordered log), or how it behaves on real albums.
- A regional conference will probably accept the paper as an application-and-measurement study if the abstract is sized to point (3). A program committee that read the abstract as written would see an unsupported "more accurate" and "beneficial up to 1 in 20" and score it down on over-claiming rather than on the method.

## Which external-reviewer points are still unaddressed

| External point | Status after the rewrite | Would a PC still reject on it? |
|---|---|---|
| No figures | Fixed (pipeline, sweep, scaling). No accuracy or correction-curve figure. | No |
| Not clearly better than c-avg | Conceded in body ("tied, not ours ahead"), but the abstract still says "more accurate" and "faster". The speed claim is M5. | Possibly, unless the abstract is resized |
| Consequences true by construction | Conceded in Sec. III and Table III "n/r"; abstract still lists them as results against a self-designed opponent (M3, M4). | Likely a concern |
| Corrections help little | Unaddressed: gain +0.007 F1 on a 0.985 baseline; zero at p=0.05 (M1). | Yes, as a "so what" weakness |
| Data too easy and artificial | Disclosed ("simulated"), not addressed: LFW celebrities, F1 0.985 to 0.998, no real albums or users. | Possibly; the most likely rejection reason at a stronger venue |
| Tuning not equal | Partly addressed (finer grids; 51-config run). The equal-budget result favours the baseline and is not carried into the abstract (M2). | No, if M2 is fixed |
| Weak statistics | Partly: people bootstrap for Table I only; correction intervals still library-level; no multiplicity; blur/dark intervals missing (M2, m10). | Possibly |
| Proposition only a sketch | Unchanged: still a sketch, tie handling inconsistent (m8). | Unlikely at this venue |
| Local-first / devices overclaimed | Partly: "simulated" is in the title; "local-first" labelling and the combined sync-plus-removal gap remain (m7, M4). | Unlikely if M4 is stated |
| Title overpromises | Fixed in form; "Persistent" still suggests more than recomputation of partitions up to renaming. | No |

## Observations (non-defects)

- The body is more honest than the abstract: "Our method is not clearly ahead on degraded photos", the CPLFW loss, "tied, not ours ahead", the "n/r" label and the disclosure that the frozen baseline is the authors' own design are all there. The problem is the abstract and conclusion not carrying them.
- The fairer-tuning paragraph (finer grid, 51-config budget) is a real improvement and is reported even though it does not favour the method.
- The Acknowledgment's AI disclosure and the number-verification script are good practice; keep through the cut.
- The Scope paragraph is accurate as far as it goes; the issue is omission (m4), not falsehood.
- Table II numbers are internally consistent with the prose I could check: "Now" column same for no-corrections and ours by design; frozen's 0.9928 is the best precise-user later F1 (the text says "matches", fine); Table I deltas against average linkage (+0.0059, +0.0038, +0.0022, -0.0061, -0.0025, -0.0089, -0.068) match the cell differences.
- Deletion support is a genuine addition, and the 7.0 s rebuild versus 0.59 s plus 0.5 s read is a reasonable local-first argument if m9 is worded carefully.
- Not my remit: page count and reference formatting (see m10(d) for a one-line pointer).

## Hand-back summary (5 lines)

1. Verdict: no CRITICAL, 5 MAJOR, 10 MINOR; the body is honest, the abstract and conclusion over-claim.
2. Biggest: "beneficial up to one wrong click in twenty" is contradicted by the paper's own sweep (+0.0009, interval includes zero); also "more accurate on clean, blurred and dark photos" is selected-cell, only clean has an interval, and ours loses at equal tuning budget (0.9836 vs 0.9849 to 0.9857).
3. The consequences (devices, retraction, deletion) are by construction and the 53% opponent diverges by design; the combined sync-plus-removal case (tombstones) is untested although Fig. 1 and the abstract imply it.
4. "Order of magnitude faster up to 50,000 faces" is a read-step ratio on six disjoint rotated copies, while index building (316 s) exceeds the baseline's entire run (174 s) and 0.15 s vs 316 s is an unexplained jump; the removed limitations list hid interval reuse, the assumed wrong-click rate and cluster-identity handling.
5. Still unaddressed from the external reviewer: easy and artificial data (F1 0.985), small corrections gain, and library-level intervals for the correction results; fixes are wording-level except for the sync-with-removal and the scaling clarification.
