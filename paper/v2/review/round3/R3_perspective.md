# Perspective Review Report (Peer Reviewer 3), round 3

**Manuscript:** `paper/v2/cove_paper.tex` (commit ef69690), "Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries"
**Mode:** simplified run, one seat. I did not read any other round-3 report. I did not run the app or modify any file. I read the code and the JSON results.

### Reviewer Identity
Local-first and privacy software engineer. I have shipped self-hosted, on-device photo and sync software. I read the paper as someone who would have to wire this clusterer into a real app and support its users. I am an outsider to clustering theory. I do not judge the statistics (Reviewer 1) or the literature (Reviewer 2).

### Overall Recommendation
**Major Revision.** The experiments are now honest and well sized. What still fails is the gap between what the paper says Cove does and what Cove's code does, and the privacy statement is more favourable than the shipped Docker setup. Both gaps can be closed. If the title and abstract are re-sized, or the app is wired as described in W1, the remaining issues are minor and a conference reviewer could accept the paper.

### Confidence Score
4. Core expertise: local-first and self-hosted software, API exposure, UI consequences of constraint-based correction. I checked the code paths directly. Adjacent expertise: the legal framing (W5) and the clustering statistics.

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

### Criterion-Bound Judgements
| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Practical feasibility (paper vs app) | R3 card: "gap between the paper and the app" | DOES_NOT_MEET | `dataset: cove/api/server.py _run_clustering_stage`; `dataset: cove/engines/person_manager.py save_people(overwrite=True)` | The title and conclusion speak of Cove keeping corrections. The app has no correction endpoint, builds a fresh clusterer on every import, and wipes names. Limitation (vii) says so, but only in the last sentence of the limitations. | Frontend UI checked only by grep for correction/merge/split code. No UI was run. | yes: it decides whether the title is honest |
| Stakeholder and UI implications of sticky wrong corrections | R3 card | PARTLY_MEETS | `text: Sec. V-C "A system that keeps corrections must therefore show them and let the user remove one."` | The finding is real and reported candidly. The design advice is one sentence, and no experiment tests undo. | No user study exists, so UI claims cannot be checked either way. | yes |
| Privacy, consent and exposure | R3 card | PARTLY_MEETS | `dataset: docker-compose.yml ports`; `text: Privacy paragraph` | The paper is candid about the Docker LAN exposure but incomplete. It omits ports 8001 and 8080, the delete/upload endpoints, and the fact that the optional key cannot be used by the shipped UI. | I did not test any exploit or browser behaviour. | yes (for the "local-first" premise) |
| Real-user significance of F1 differences | R3 card | PARTLY_MEETS | `table: Table II "Later: F1" column` | Most differences are 0.001-0.004 F1. The user-relevant effect is hidden in the "held" column, and the text does not translate it. | Real users may behave differently from all three simulated users. | no (reframing only) |
| CPU budget | R3 card | MEETS (as measured), PARTLY_MEETS (for real libraries) | `dataset: exp18_update_time_edgeface_s.json`; `dataset: exp18b_constrained_time_edgeface_s.json` | Every timing number in Sec. V-F traces to the JSONs. Scale beyond 8,290 faces and the end-to-end import cost are not shown. | One laptop, one thread. | no |

Do not total, weight, average, or mechanically map these judgements to the recommendation.

### Summary Assessment
The paper has improved a lot since round 2. It now compares against fair baselines, includes a user who makes mistakes, times the constrained path, and says plainly that accuracy equals constrained average linkage and an Immich-style rule. My concern is that the title and conclusion tell a reader that Cove keeps the user's corrections. I read the code. The app has no way to create a correction, builds a new clusterer from the whole embedding store on every import, and calls `save_people(..., overwrite=True)`, which discards the only correction a user can make today, a rename. Limitation (vii) states this fairly, but only in its last sentence. The "survives the next import" result also silently assumes that a face's identity is stable, whereas the app keys faces by their position in a list that is renumbered when a photo is deleted. The finding that wrong corrections are sticky is the paper's most useful result for engineers, and the advice drawn from it is one sentence. The privacy paragraph is honest, but the shipped compose file exposes more than it says. The numbers I checked against the JSON files are accurate. Differences of 0.001-0.004 F1 are not noticeable to a person, but the count of fixes a user must redo is, and the paper already contains it. I recommend Major Revision.

### Strengths
1. **S1 Candid, verified limitation (vii).** Each part of the sentence matches the code: no correction endpoint, a full re-cluster on every import, names overwritten. Evidence Anchor: `text: Sec. VI "the current app has no interface for corrections yet, re-clusters from scratch on every import, and overwrites user-assigned names"`. I checked it against `server.py` (`_run_clustering_stage` calls `StableIncrementalClusterer(...).fit_predict` and then `save_people(labels, face_paths, overwrite=True)`). `add_must_link` and `add_cannot_link` are called only from `tests/` and `stable_cluster.py`.
2. **S2 Timing is traceable and honestly framed.** 3.8/4.3/5.1 s, 3.5/4.7/16.7 s and 0.15/3.4 s all match the JSONs. The paper says that with corrections an update costs about as much as re-clustering. Evidence Anchor: `dataset: exp18b_constrained_time_edgeface_s.json labels_seconds_by_corrections {0: 3.80, 1: 4.26, 10: 5.14, 50: 5.05}`.
3. **S3 The error-prone user is a real engineering contribution.** It shows that the lossy design (re-apply) tolerates mistakes better than the strict one. Evidence Anchor: `table: Table II, error-pr. column: ours 0.9851, re-apply (avg. link.) 0.9896`. The authors reported this against their own method.
4. **S4 The privacy paragraph states the Docker exposure instead of hiding it.** Evidence Anchor: `text: Sec. VI Privacy "in the Docker install it is reachable from the local network"`. It matches `docker-compose.yml`.

### Weaknesses

### W1: The title, abstract and conclusion describe a product behaviour that Cove does not have
**Problem:** The title says "Keeps the User's Corrections". The abstract opens "We describe the face clusterer of Cove, a local-first media system". The conclusion says "Cove's face clusterer ... keeps the user's corrections across later imports". All of these are in the present tense. The gap (no UI or endpoint, full re-cluster on every import, names wiped) appears only as the last sentence of limitation (vii). A reader of the abstract, which is what a conference programme shows, will believe the shipped app keeps corrections.
**What I checked in the code:**
- `server.py` has people endpoints only for `GET /people`, `GET /people/{id}/photos`, `POST /people/cleanup` and `POST /people/{id}/rename`.
- `_run_clustering_stage` builds a new `StableIncrementalClusterer` from the whole `storage.vector_matrix` and calls `PersonManager().save_people(labels, face_paths, overwrite=True)`. That sets `self.people = {}` before writing, so every rename is lost on the next import that adds faces.
- The incremental `add()` path that Sec. V-F times is never called by the app.
**Evidence Anchor:** `text: Title "Face Grouping That Keeps the User's Corrections"` and `dataset: cove/api/server.py _run_clustering_stage — fit_predict on all embeddings, then save_people(overwrite=True)`
**Why it matters:** The paper reports a method, and the method does what the paper says. The mismatch is about the word "Cove". Round 2 flagged this (issue 5), and the revision log says "the author must decide". It is still undecided in this draft.
**Suggestion (pick one):**
- (a) Retitle to a method title, for example "Order-Invariant Constrained Incremental Clustering for Local-First Face Grouping: Surviving the Next Import". Change the abstract's first sentence to "We describe a face clusterer, implemented in the clusterer module of Cove; its correction interface is not yet wired into the app". Move the current-state sentence from limitation (vii) into the Introduction's contribution list.
- (b) Wire it before submission. The minimum is:
  - (1) a `corrections.json` store of pairs of stable photo keys (see W2);
  - (2) `POST /people/merge` (one must-link between the representative faces of the two groups) and `POST /people/{id}/not-this-person` (cannot-link);
  - (3) in `_run_clustering_stage`, load the stored corrections, map keys to current face ids, drop stale ones, and call `add_must_link`/`add_cannot_link` before `labels()`;
  - (4) remove `overwrite=True`, or re-attach names by overlap (W6);
  - (5) a ledger endpoint (W3).
  Then the "Cove" claims are true, and Sec. V-F's 5.1 s becomes the number a user would see.
**Severity**: Major | **Evidence Anchor**: `text: Title "Face Grouping That Keeps the User's Corrections"` | **Confidence**: 5, I read both code paths

### W2: "All corrections survive the next import" assumes a stable face identity that the app does not provide
**Problem:** The method section says corrections are "stored with the clusterer". The clusterer is an in-memory object. Constraints are pairs of integer face ids, which are positions in `storage.paths`. In the evaluation, faces are only added and never removed, so the ids are stable by construction. In the app they are not stable:
- `/images/delete` rebuilds the store with `_rebuild_storage_without`, which keeps the surviving rows in order and so renumbers every later face.
- `_reconcile_storage_with_disk` prunes "dead" paths in the same way.
- `/upload` writes `os.path.join(TEST_IMAGES_DIR, os.path.basename(f.filename))`, so a second photo with the same file name silently replaces the first.
So after one deletion a stored pair (10, 20) refers to two different faces. A silent must-link between two different people is worse than a lost correction. The paper's number (100 percent held) is about constraints and says nothing about this failure.
**Evidence Anchor:** `dataset: cove/api/server.py _rebuild_storage_without — survivor rows re-added in order, ids renumbered` (the paper side: `text: Sec. III-C "stored with the clusterer and applied every time labels are computed, including after new photos"`)
**Why it matters:** This is the difference between "the algorithm supports constraints" and "a user's fix survives". The paper's headline needs a statement on identity.
**Suggestion:**
- State the assumption in Sec. III-C: "a correction is a pair of persistent face keys; the key must survive deletion and re-indexing".
- Recommend the key. Use a content hash of the photo plus the face index within the photo. Because Cove clusters only the largest face (limitation iii), the hash alone is enough today. Do not use a path or position.
- Define what happens when one side of a pair disappears: drop the constraint and tell the user.
- One extra test in the released tests would show it: delete a photo, re-import, and check that corrections still apply to the same faces.
**Severity**: Major | **Evidence Anchor**: `dataset: cove/api/server.py _rebuild_storage_without — survivor rows re-added in order, ids renumbered` | **Confidence**: 4, verified in code; the effect on a user's data is inferred and untested

### W3: "Corrections must be visible and undoable" is a one-sentence conclusion with no design content and no test
**Problem:** The sticky-correction result is the most useful finding for anyone building the UI. Ours falls to the no-correction F1 (0.9851 vs 0.9854), constrained average linkage to 0.9878, and the forgetful re-apply method scores best (0.9896). The paper's advice is "must therefore show them and let the user remove one". That is true but not specific enough to implement. It also was not tested: no experiment simulates a user who notices and removes a wrong correction.
What the result implies for a UI, none of which the paper says:
1. **Must-links and cannot-links are not symmetric.** A wrong cannot-link only costs one extra split. A wrong must-link joins two people for good, including every future photo of both. A merge should therefore be harder to do than a split: it needs a confirmation that shows a sample of both groups, and it should be visible afterwards.
2. **Blast radius preview.** Before applying a merge, show how many photos change group. The code can compute this cheaply, because 4-5 s for the constrained read (V-F) is acceptable as a preview.
3. **A correction ledger.** List each correction with the two face thumbnails, the date and the groups it affected. Offer per-item "remove" and "remove all". The algorithm supports removal trivially (delete the pair from the sets), so the paper can state that the cost of undo is one re-read.
4. **Conflicts must be shown, not resolved silently.** The method says a cannot-link "wins" over a must-link, and contradictory must-links are resolved by similarity order. Both are deterministic, which is what the proposition needs. But the user who made the older correction never learns that it is now overridden. Surface this as a warning in the ledger.
5. **Soft constraints are an open option.** A constraint that must be re-confirmed after N imports, or one that only biases the clustering rather than forcing it, would keep much of the gain with much less stickiness. The re-apply result (0.9896 under noise) suggests the trade-off exists.
**Evidence Anchor:** `text: Sec. V-C "A system that keeps corrections must therefore show them and let the user remove one."`
**Why it matters:** The abstract and conclusion both finish on this advice, so it is the paper's takeaway. At present it is an inference from a single simulated error rate (10 percent) that nobody tested.
**Suggestion:**
- Cheapest: expand the V-C paragraph with items 1-4 above and call them design requirements, not results.
- Better, and fits the existing harness: add a "reviewing" user who inspects the cluster that each own must-link just merged and undoes it with probability q (for example 0.5). Report F1 for q = 0, 0.5, 1 at the 10 percent error rate. This shows how much undo is worth.
- Mention that a UI that offers only "merge" will make many more must-links than cannot-links. In exp15, 81 percent of the oracle's fixes were must-links (round-2 editorial decision), so the risky kind dominates.
**Severity**: Major | **Evidence Anchor**: `table: Table II, error-pr. column: ours 0.9851 vs re-apply (avg. link.) 0.9896` | **Confidence**: 3, adjacent expertise (HCI of interactive ML); the engineering consequences are mine, the experiment is a suggestion

### W4: The privacy paragraph is incomplete about what the shipped Docker setup exposes
**Problem:** The paper says the API "has no access key and accepts requests from any origin" and is "reachable from the local network" in Docker. I verified three parts, and found four more things the paper omits.
Verified:
- `allow_origins=["*"]` with `allow_credentials=True` in `server.py`.
- `docker-compose.yml` publishes `"8000:8000"`, and uvicorn runs on `0.0.0.0`. A short-form port mapping binds all host interfaces.
- No access key in the shipped configuration.
Omitted:
1. `video-api` is also published (`"8001:8001"`, host `0.0.0.0`). It holds face data from videos and is not mentioned.
2. The `frontend` service publishes `"8080:80"`, and `nginx.conf` proxies `/api/cove/` and `/api/video/` to the two backends. So closing 8000 and 8001 does not close the API: it stays reachable through 8080. The web UI does not need 8000 or 8001 to be published at all, because nginx talks to them on the compose network.
3. The unauthenticated API is not read-only. `POST /images/delete` removes photo files from disk, `POST /upload` writes files, `POST /people/cleanup` deletes records, and `/media/test_images` serves every photo. A person on the same hostel, college or public Wi-Fi network can read and delete the library.
4. "No access key" is slightly wrong. `COVE_API_KEY` exists server-side (`vision_config.py`, `docs/API.md`) but is off by default, the compose file does not set it, and the frontend never sends `x-api-key` (grep of `frontend/src` finds no use). Turning it on would make the shipped UI return 401. So the paper's remedy, "Restricting the API to the app", needs client work too.
Native install: `backend_main.py` and `docs/ARCHITECTURE.md` bind `127.0.0.1` by default, so the native exposure is much smaller. A page in the user's own browser can still call `http://127.0.0.1:8000` while CORS is `*`. I did not test whether the browser's private-network protection blocks this, so I call it a risk and not a finding.
**Evidence Anchor:** `dataset: docker-compose.yml — services cove-api "8000:8000", video-api "8001:8001", frontend "8080:80"; nginx.conf location /api/cove/ proxy_pass cove-api:8000`
**Why it matters:** "Local-first" is the premise of the title. The paper releases this compose file with the code. The mitigation costs minutes.
**Suggestion:**
- In `docker-compose.yml`: remove the `ports:` for `cove-api` and `video-api`, and publish the frontend as `"127.0.0.1:8080:80"`.
- If LAN use is wanted, add HTTP Basic auth or a token in nginx and make the frontend send it.
- Replace `allow_origins=["*"]` with the known frontend origins, or with an `allow_origin_regex` for `localhost` and `tauri://`.
- Reword the paragraph: "an optional API key exists but is off by default and unsupported by the shipped UI; in the Docker setup the API, including delete and upload, is reachable from the local network on ports 8000, 8001 and 8080". Then the sentence "nothing leaves the device" is still true for the cloud, and not misleading for the LAN.
**Severity**: Major | **Evidence Anchor**: `dataset: docker-compose.yml — services cove-api "8000:8000", video-api "8001:8001", frontend "8080:80"; nginx.conf location /api/cove/ proxy_pass cove-api:8000` | **Confidence**: 4, config read directly; exploitability on a given network not tested

### W5: The consent sentence promises a capability that the code does not have
**Problem:** "users should be able to delete a person's face data" is stated as a norm, but no endpoint does this. The nearest operations are `POST /images/delete` (removes whole photos, so everyone else in the photo is lost too) and `POST /people/cleanup` (removes only people whose photos are already gone). Embeddings of minors and bystanders are kept as plain vectors, and the people database is plain JSON. The paper's device-encryption advice leaves this to the OS. The paper also gives no legal framing. For readers in India, the relevant question is whether a personal photo manager is covered by the personal-or-domestic-purpose exemption of the Digital Personal Data Protection Act 2023, and whether a face embedding counts as biometric data; GDPR has a similar household exemption and a special category for biometric data. I mention these as leads for the authors and make no legal claim [UNVERIFIED, from memory, not checked against the statutes this session].
**Evidence Anchor:** `text: Sec. VI Privacy "users should be able to delete a person's face data"`
**Why it matters:** It is a one-sentence promise a reviewer or user can test. Also the Ethics declaration covers only the benchmark data, while the paper's end use is family photos including children.
**Suggestion:** Either add `DELETE /people/{id}` that removes the person's embeddings and cluster membership (keeping the photos), or reword to "the current release cannot delete one person's face data without deleting the photos". Add one line on the lawful-use framing, flagged as the authors' view.
**Severity**: Minor | **Evidence Anchor**: `text: Sec. VI Privacy "users should be able to delete a person's face data"` | **Confidence**: 4 for the code fact, 2 for the legal framing

### W6: Name continuity under relabelling is undefined, and names are the correction users make first
**Problem:** The only correction Cove supports today is renaming. Person ids are `Person_{label}`, where `label` is the output of `np.unique(..., return_inverse=True)` over union-find roots, and then the merge step. These ids do not persist: they depend on which face is the smallest in a component, so a new photo can shift them. Even if `overwrite=True` were removed, a name would attach to whatever group takes that number next. The paper shows that partitions are stable (ARI at least 0.998 between successive partitions) but never discusses label continuity, or what name a merged or split group carries. These are the first things a user sees after an import.
**Evidence Anchor:** `dataset: cove/engines/person_manager.py save_people — person_id = "Person_{label}"; overwrite=True resets self.people = {}`
**Why it matters:** Corrections that survive in the clusterer but whose names do not will look like lost corrections to the user.
**Suggestion:** Add two sentences defining the contract: a name is anchored to the set of its member faces. After an import, each new group inherits the name of the previous group it overlaps most, if the overlap is above a stated share. On a merge of two named groups, the user is asked which name stays. On a split, the name stays with the larger half and the other half is flagged. This also handles Section III's order-free relabelling.
**Severity**: Minor | **Evidence Anchor**: `dataset: cove/engines/person_manager.py save_people — person_id = "Person_{label}"; overwrite=True resets self.people = {}` | **Confidence**: 4, code read directly

### W7: Differences of 0.001-0.004 F1 are reported as wins, while the effect users would feel is not translated
**Problem:** Table II bolds 0.9945, 0.9928 and 0.9920 as best in columns where methods differ by about 0.001-0.004. The text calls +0.002 to +0.006 over average linkage "significantly better". The libraries have roughly 1,000-3,000 faces, so 0.002 B-Cubed F1 is on the order of a handful of faces out of a library. No user can see that, and the paper's own caveat (iv) says the intervals are probably too narrow. The effect that a user does feel is already in the data but not stated:
- Casual user, re-apply (ours): 73 percent of corrections hold, and the user made about 5.7 corrections per library. That is roughly 1.5-1.8 fixes the user must redo after each import, against none for the constraint-based methods. Computed from `exp19_correction_baselines_edgeface_s.json`: `casual|ours+reapply` held_share 0.732 with 1,360 corrections over 207 libraries.
- The F1 gap between those methods is 0.002.
**Evidence Anchor:** `text: Sec. V-A "ours is significantly better on clean, blur and dark photos (+0.002 to +0.006)"`
**Why it matters:** The honest advantage of storing corrections as constraints is not accuracy but "the user does not have to repeat work". Presented as F1, it looks negligible, and the paper then appears to over-sell.
**Suggestion:** Add one sentence and one column. Report "expected fixes to redo per import" next to "held (%)" (for the casual user, about 1.5-1.8 for re-apply and 0 for constraints). Report accuracy gaps below 0.005 as "no practical difference" and stop bolding within-noise cells. A dedicated "effort to clean" measure (corrections needed to reach F1 0.99) would help but is optional.
**Severity**: Minor | **Evidence Anchor**: `text: Sec. V-A "ours is significantly better on clean, blur and dark photos (+0.002 to +0.006)"` | **Confidence**: 4

### W8: CPU-budget claims hold at 8,290 faces; scale, silent limits and end-to-end import cost are missing
**Problem:** The measured numbers are correct, but three things matter to a person with a real library and are not stated:
1. **Scale.** Only 8,290 faces were timed, with clean LFW (mostly singleton people). The read-time steps grow with the library (the paper says so). `_merge` in `stable_cluster.py` returns the labels unchanged when there are more than 20,000 clusters (`len(ids) > 20000`), so on a large library of many distinct people the centroid-merge step, one of the three parts of the method, silently turns off. The accuracy tables were measured with it on. Also `AgglomerativeClustering` with average linkage builds a dense k-by-k matrix, which at k near 20,000 is a few gigabytes of float64. That is plausible on the authors' 12 GB laptop and unlikely on a typical student 8 GB laptop. I did not run this and give the figure as arithmetic, not as a measurement.
2. **What the user waits for.** The update time excludes detection and embedding. The paper reports embedding latency (9.8 ms per face with one thread) but no detector latency. For a 1,000-photo import, face detection and embedding probably take much longer than the 4-5 s clustering step the paper times. So the 1.3 times saving of "incremental" over re-running (3.5 s vs 4.7 s) is not what the user notices.
3. **Incremental in the title.** With corrections present, the paper says an update costs about as much as re-clustering from scratch. The shipped app re-clusters from scratch in about 4.7 s at 8,290 faces. By the paper's own numbers the incremental path is not needed at this scale.
**Evidence Anchor:** `text: Sec. V-F "The update is therefore cheap but not constant-time."` and `dataset: cove/engines/stable_cluster.py _merge — returns lab when len(ids) > 20000`
**Why it matters:** The performance case for "Incremental" in the title is weak, and the scale limit is not disclosed.
**Suggestion:** State the 20,000-cluster limit in Sec. V-F or limitation list. If possible, time one library of 20,000-30,000 faces (the clean LFW set could be tiled with distractors). Report end-to-end seconds for a 100-photo import, split into detection, embedding and clustering. Consider dropping "Incremental" from the title, or justify it by the batch-free update rather than speed.
**Severity**: Minor | **Evidence Anchor**: `dataset: cove/engines/stable_cluster.py _merge — returns lab when len(ids) > 20000` | **Confidence**: 4 for the code fact, 2 for how often real libraries hit it

### Detailed Comments

#### Assumption Audit
- **Explicit assumptions:** The three simulated users are stated as models (limitation ii). Good.
- **Implicit assumptions:**
  - A face has a persistent identity across imports (W2).
  - The user makes corrections by clicking two faces. A real UI decides which pairs a "merge these two people" action creates. One pair? Every pair? The representative faces? This choice decides how the "casual" results transfer. The casual user is the closest proxy to a merge button, and the paper does not say so.
  - A user notices wrong corrections (W3).
  - Libraries fit in memory with one thread and a flat index (W8).
- **Paradigmatic assumptions:** Accuracy is the measure of success. For a local-first product, trust, reversibility and effort are the measures (W3, W7).

#### Cross-Disciplinary Connections
- **Parallel research:** Interactive machine learning has studied how people correct a learner and how corrections should be explained and undone (Amershi et al., "Power to the People"; Kulesza et al., "Principles of Explanatory Debugging"). Both bear directly on W3.
- **Borrowing opportunities:** The local-first software literature (Kleppmann et al.) offers a model for durable user edits that survive re-derivation of the shown state. A correction ledger keyed by stable ids is the same pattern as a replicated operation log.
- **Methodological borrowing:** Event sourcing: store the user's corrections as an append-only log of operations and re-derive the people view from the log plus the faces. That is what the clusterer already does, and naming it makes the design reusable and the undo trivial.

#### Practical Impact
- **Real-world application:** The method is deployable. The code is small and the tests pass. What is missing is the app layer.
- **Implementation feasibility:** The wiring plan in W1 is about a day of work for someone who knows the code. The compose change in W4 is minutes.
- **Stakeholders:** The people in the photos (bystanders, children) are mentioned in one sentence. Users on shared networks (hostels, colleges) are the real risk for the Docker setup.

#### Broader Implications
- **Ethical dimensions:** Biometric templates of non-consenting people are stored in plain files (W5).
- **Social impact:** A wrong merge between two real people is an error with social meaning (two relatives or two friends shown as one). The "precise" setting favouring precision (V-B) is the right default, and the paper says why.
- **Future directions:** A user study of even five people with a clickable prototype would answer W3 and W7 better than any further simulation.

### Cross-Disciplinary Reading Recommendations
All three are recommended from memory. I did not look them up in any index this session, so treat them as **[UNVERIFIED]** until checked.
- Kleppmann, Wiggins, van Hardenberg and McGranaghan, "Local-first software: you own your data, in spite of the cloud", Onward! 2019. [UNVERIFIED] Gives the standard definition of local-first and the ideals ("no spinners", "the long now", "security and privacy by default"), which the paper's use of the term can be checked against.
- Amershi, Cakmak, Knox and Kulesza, "Power to the People: The Role of Humans in Interactive Machine Learning", AI Magazine, 2014. [UNVERIFIED] Covers user-driven correction of learners and the risks of giving users direct control. Relevant to W3.
- Kulesza, Burnett, Wong and Stumpf, "Principles of Explanatory Debugging to Personalize Interactive Machine Learning", IUI 2015. [UNVERIFIED] On making a system's reasoning visible so that users can correct it. Relevant to the ledger and blast-radius preview.
- Search leads only (not citations): the Digital Personal Data Protection Act 2023 (personal-or-domestic-purpose exemption); GDPR Art. 2(2)(c) and Art. 9 (household exemption, biometric data). [UNVERIFIED]

~~~yaml suggested-references
- title: "Local-first software: you own your data, in spite of the cloud"
  authors: ["Kleppmann, M.", "Wiggins, A.", "van Hardenberg, P.", "McGranaghan, M."]
  year: "2019"
  doi: null
  arxiv_id: null
- title: "Power to the People: The Role of Humans in Interactive Machine Learning"
  authors: ["Amershi, S.", "Cakmak, M.", "Knox, W. B.", "Kulesza, T."]
  year: "2014"
  doi: null
  arxiv_id: null
- title: "Principles of Explanatory Debugging to Personalize Interactive Machine Learning"
  authors: ["Kulesza, T.", "Burnett, M.", "Wong, W.-K.", "Stumpf, S."]
  year: "2015"
  doi: null
  arxiv_id: null
~~~

### Questions for Authors
1. If a user deletes a photo and then re-imports, what stops a stored correction from attaching to a different face? What is the persistent key? (W2)
2. In the intended UI, how many constraint pairs does one "merge these two people" action create, and which faces are used? Is that closer to your precise user or your casual user? (W3, assumptions)
3. Would you run the "reviewing user" simulation of W3, in which the user undoes a wrong merge with probability q? If undo recovers most of the loss, the advice is supported; if not, the sticky result needs a different remedy.
4. Will the compose file in the released code still publish ports 8000, 8001 and 8080 on all interfaces? (W4)
5. Do you want the title to say "Cove"? If the app will not have corrections before submission, which sentence in the abstract tells the reader so? (W1)

### Minor Issues
- Sec. VI Privacy: "no access key" should read "an optional access key, off by default and not used by the shipped UI" (W4).
- Table II: the Frozen row shows "--" for casual and error-prone users, with no reason given in the caption. Add "not run" so a reader does not assume the cells are zero.
- Sec. V-C: "162 of 1,528 corrections wrong" is 10.6 percent, higher than the stated 0.1 probability because the casual user also makes more corrections that fail. State that the realised rate is 10.6 percent, not 10.
- The Declarations say "Ethics: only public benchmark datasets were used". Add that the described end use (family photos including children) needs the consent text of Sec. VI.
- Page limit: not compiled, as the revision log says. The additions I suggest (W3, W4, W7) are about 150-200 words in total; check the 6-page limit.

### Revision-check against round 2 (my seat)
| Round-2 item (R3) | Status in this draft |
|---|---|
| Corrections keyed by face position | **Not addressed** in the paper or the code (W2) |
| "Nothing leaves the device" false for Docker | **Partly fixed**: paragraph added and accurate as far as it goes; incomplete (W4) |
| Title and app do not match | **Not fixed** (W1); limitation (vii) is accurate |
| Largest face only | Listed as limitation (iii) |
| Consent | Sentence added; promises an unimplemented deletion (W5) |
| Corrections path not timed | **Fixed**, and the numbers match the JSONs (S2) |
