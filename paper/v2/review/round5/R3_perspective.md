# Round 5, Reviewer 3 (Perspective: local-first software engineer / privacy practitioner)

Manuscript: paper/v2/cove_paper.tex. Repo files checked: cove/engines/stable_cluster.py, cove/api/server.py (lines ~750-820, CORS at ~160), cove/engines/person_manager.py, frontend/src (PeopleView.jsx, lib/coveApi.js), README.md.

## Recommendation
Accept with minor revision (weak accept for a local IEEE conference). Confidence 4/5.
The positive tone is mostly honest, because the title says "A Simulation Study" and the abstract's last sentence says "simulated libraries and users". The remaining risk is a handful of sentences where the verbs ("handled", "keeps", "makes them safe", "natural companion", "worth in practice") are stronger than what was built or measured, plus one engineering gap (face identity across devices and across deletion) that an implementer would hit at once.

## Repo facts I rely on
- stable_cluster.py has add_must_link / add_cannot_link / remove, all addressed by integer face index. remove() compacts and renumbers ids (lines 145-172) and renumbers the corrections with them.
- server.py `_run_clustering_stage` calls `StableIncrementalClusterer(...).fit_predict(...)` on the whole library, never calls add_must_link / add_cannot_link, then `PersonManager().save_people(labels, face_paths, overwrite=True)`, which wipes the people DB. Person ids are `Person_{label}`; default names "Person N".
- The only people-editing endpoint is `POST /people/{id}/rename`; PeopleView.jsx only renames. Greps for undo, merge, split, tombstone, retract in server.py and the frontend found nothing relevant. There is no correction UI, no sync, no undo.
- Consequence: the shipped app does not use the corrections store, and a re-index wipes even user renames. "From the local-first system Cove" is true of the clusterer only. README line 149 ("order-stable incremental clusterer") is accurate only if "incremental" means the add() API, since the app re-clusters in batch.
- server.py allows CORS "*" with optional token auth (lines ~160-176). Fine on localhost, but relevant to issue 4.

## Issues

1. MAJOR. Location (abstract): "two simulated devices end with identical people ... a wrong correction can be retracted exactly, deleted photos are handled exactly".
   Problem: "exactly" for deletion and "devices" read as shipped features. "Devices" are one process exchanging two Python sets; there is no transport, no cross-device face identity, and no app path that calls remove() or the correction API.
   Fix: "two simulated devices (exchanging the two sets in-process)", and add to the scope paragraph: "In the Cove application only the clusterer is integrated today; corrections, undo and sync exist as library calls and in simulation."

2. MAJOR. Location (Scope and next steps): "The libraries and users are simulated from public benchmarks ... The natural next steps are a correction and undo interface in the application, device sync built on the two sets".
   Problem: honest about the simulation and about what comes next, but it never says the app currently has no correction UI and that its indexing job re-clusters from scratch with overwrite=True (even renames are lost). The Introduction ("the Cove system studied here") lets a reader think the lost-corrections problem was observed in, or solved in, the app. One factual sentence suffices; no limitations list is needed.
   Fix: "Cove today groups people with the order-stable clusterer but has no correction, undo or sync interface; the corrections, devices, retraction and upgrade results are simulations of those features."

3. MAJOR. Location (Method, "Corrections and deletion" and Fig. 1 caption): "Corrections are kept as a set of face pairs next to the face index ... deleting one pair, gives the same result as starting again".
   Problem: the central engineering gap. Corrections are stored by integer face index, and remove() renumbers. Across two devices indices differ, since each assigns ids in its own arrival order (the proof itself admits "face id ... depends on insertion order"). Exchanging "the two sets" silently assumes a stable cross-device face identity. The "ties by the faces' content, not their ids" rule in step (1) likewise presumes a content identity that is never defined. An app needs an id that survives re-import and is equal on every device (photo content hash plus detector box, or a UUID assigned once), with the integer index only a local cache, and corrections must name that id, not a photo (a photo can hold several faces).
   Fix (2-3 sentences, positive tone): "In an application each face needs an id that is the same on every device and survives re-import (we use the face index in the simulation; an application would use photo hash plus box). Corrections name that id; each retracted correction leaves a tombstone so a replica that missed the retraction does not re-add it; deleting a photo drops its faces and the corrections that name them."

4. MAJOR. Location (removed Privacy paragraph vs. Intro "group faces on hardware the user controls", abstract "local-first").
   Problem: the paper makes and measures no privacy claim, so removal loses little. But the property it sells (device agreement) depends on exchanging "faces and corrections", and the faces are embeddings, i.e. biometric templates. That is a different exposure from exchanging labels. The stated next step (real albums, real users) also brings consent and data-protection obligations. The Declarations say "public benchmark data only" but are silent on this.
   Fix (one sentence, not a section) in Scope: "Exchanging the face set means exchanging embeddings, which are biometric data; a sync layer would need device-to-device encryption, and a study on real albums would need consent." Keep "local-first" in the abstract only alongside a clause that no sync is implemented.

5. MAJOR. Location (abstract and Conclusion): "Corrections stay beneficial up to about one wrong click in twenty, so a review-and-undo view is the natural companion" / "pairing them with a visible, removable list makes them safe to use."
   Problem: the data do not show that a review-and-undo view makes corrections safe. The sweep gains are +0.0065 at p=0, +0.0009 at 0.05 and +0.0010 at 0.10 with intervals including zero, and -0.0057 at 0.20. "Beneficial up to one in twenty" is really "not distinguishable from zero". Spotting the wrong click is hard (AUC 0.60), and whether a person reviewing a list finds it was not measured. "Safe" is a claim about user behaviour in an unbuilt interface.
   Fix: abstract: "Gains are clear for accurate users, not distinguishable from zero at one wrong click in twenty, and negative at one in five; exact retraction makes a review-and-undo view cheap to build." Conclusion: replace "makes them safe to use" with "is the design we recommend and will test with users."

6. MAJOR. Location (abstract "53\% for a frozen-label rule with replayed edits"; Table 1 and 2 rows "Frozen (Immich-style)", "Frozen + edits"; Discussion).
   Problem: the headline 53% (and 5% for retraction) is against a baseline the authors designed. The protocol says so ("our own design, not any product's sync") and the scope paragraph says "we designed", but the abstract does not, and "Immich-style" lets a skimmer attribute the number to Immich. The low figure is also largely by construction: replaying edits in received order on a label store with no reconciliation; even a simple add/remove-pair log plus recompute converges.
   Fix: abstract "(53% for a frozen-label baseline we designed, with replayed edits)"; rename rows to "Frozen-label (our baseline)"; drop "Immich-style" unless Immich's behaviour is cited. The Discussion's line that any recompute design gets the property is good; repeat it in the abstract.

7. MAJOR. Location (Discussion): "the measurements show how much they are worth in practice".
   Problem: practical value for a photo-library user. F1 gains are +0.010 (0.984 to 0.994) on the "now" photos, about +0.007 after new photos versus discarding (0.9854 to 0.9925), +0.0036 for the recogniser upgrade, and method differences of 0.001-0.006, on libraries where the baseline is already 0.985. A user would barely notice that. The value is in the guarantees and in the user-visible effect that 80% of fixes vanish on the next import under plain re-clustering; "worth in practice" implies the F1 numbers matter.
   Fix: lead with survival: "Without a corrections store 80% of a user's fixes disappear at the next import; with it none do. In F1 terms the gain is about one point on libraries that are already 98.5% accurate." Replace "in practice" with "on these simulated libraries".

8. MINOR. Location (Sec. Update time): "Larger libraries are synthetic: the 8,290 embeddings are copied up to six times, each copy under its own random rotation" and abstract "roughly an order of magnitude faster up to 50,000 faces".
   Problem: the body is clear that this tests cost, not accuracy. The abstract has no qualifier. Rotated copies produce six unrelated sub-libraries, so there is no cross-copy structure; component sizes and the centroid-merge workload that dominates average-linkage cost are those of small libraries. Real 50k libraries have large components, where the baseline may be costlier (or ours slower). Also the app today re-clusters the whole library after every import, and the flat index build took 316 s at 49,740 faces, so end-to-end cost there is dominated by something not addressed.
   Fix: abstract "up to 50,000 synthetic faces (read step)"; add "End-to-end at 49,740 faces is dominated by the flat index build (316 s), which an approximate index would replace."

9. MINOR. Location (Method): "Deleting photos removes the faces ... with no new similarity search"; Update-time: "Deleting a random 10% of the faces took 0.59 s ... against 7.0 s".
   Problem: the code confirms the semantics, but remove() also resets and re-adds all vectors to the FAISS index (O(n) work), and the test deletes random faces, not photos with several faces or a whole person. In the app, `_reconcile_storage_with_disk` triggers a full re-cluster; remove() is not on that path.
   Fix: one sentence: "Deletion is simulated on faces; in the application it currently triggers a full re-cluster and remove() is the planned path."

10. MINOR. Location (Sec. Consequences, Table 2 "Retraction = never made", frozen 5 / 9).
   Problem: for implementers, the concurrency case is missing: two replicas, one retracts a correction while the other re-adds or still holds it. Exchange of full sets is a union-only merge and cannot express removal; a retraction needs a tombstone (observed-remove set of pairs). Only a single-device retraction after merge was tested. The frozen store's "inverse split edit" is also a weak foil: a store that kept the pre-edit state would also undo exactly.
   Fix: add to Next steps: "set exchange with removals needs tombstones (an observed-remove set of face pairs); concurrent retract and re-add was not tested."

11. MINOR. Location (Intro contribution bullet): "does not depend on the order or batching of insertions or on deletions".
   Problem: the Proposition qualifies "up to exact ties" (tie-breaking by face id depends on insertion order) but the bullet and abstract do not.
   Fix: add "up to exact ties" in the bullet.

12. MINOR. Location (Acknowledgment). The AI-use disclosure is frank and good; keep verify_paper_numbers.py in the release so reproducibility is checkable. No change required.

## Answers to the specific questions
- Honest tone: yes after issues 1, 2, 5, 6; about five short edits, none restoring a limitations list. The abstract is where a reader is most likely to be misled.
- Engineer needs: a stable cross-device face id (content hash plus box, or UUID), corrections as unordered face-id pairs typed same/different, recompute on read, cascade on deletion, tombstones for retraction, and a note that the app must stop wiping state (overwrite=True) on re-index. Only the pair-set idea is in the paper now.
- Face-index vs photo/box: addressing by face is right; addressing by position index is not enough for sync or deletion (issue 3).
- Privacy paragraph: removal is acceptable if one sentence on embeddings being biometric is kept (issue 4).
- Review-and-undo: sensible design advice, weakly supported empirically (issue 5).
- Scaling: adequately labelled in the body, under-labelled in the abstract (issue 8).

## Strengths
- Title and abstract disclose "Simulation Study" and simulated users.
- The frozen baseline is flagged as the authors' own in the protocol; the paper reports where it loses (CPLFW, low-res, occluded), that constrained average linkage ties it, and that the properties are not unique to its clusterer.
- Honest treatment of wrong clicks (sticky, negative at p=0.2) and a hard-constraint warning.
- Corrections keyed to faces, not embeddings, give a practically relevant recogniser-upgrade finding (about half the gain survives).
- Exact read step validated against the original merge; deletion unit test; code, splits and per-run results released; frank AI-use disclosure.
- Recompute-from-sets is the right local-first design and is credited to the CRDT and local-first literature.
