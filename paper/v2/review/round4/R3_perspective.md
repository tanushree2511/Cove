# Perspective Review Report (Peer Reviewer 3), round 4

**Manuscript:** `paper/v2/cove_paper.tex` (draft after E1-E5, not compiled). Simulated reviewer, not real peer review.
**Read-only run.** I did not read other round-4 reports, did not run the app or any script, and changed no existing file. I read `cove/api/server.py`, `engines/stable_cluster.py`, `engines/person_manager.py`, `config/vision_config.py`, `docker-compose.yml`, `nginx.conf`, `start.sh`/`start.bat`, the frontend API client, `docs/ARCHITECTURE.md`, `README.md`, exp21-23 scripts and JSON. One generic web search was made on IEEE's AI-disclosure policy (no project names in the query).

### Reviewer Identity
Local-first software engineer and privacy practitioner. I read the paper as someone who would have to ship it and support its users. I do not judge the statistics or the literature.

### Overall Recommendation
**Major Revision** (close to Minor if the claim-sizing fixes in W1 are made; the rest is repairable in wording).

### Confidence Score
4. Core expertise: local-first/self-hosted software, API exposure, sync design. Adjacent: HCI of correction, IEEE policy (secondary sources only).

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

### Summary Assessment
The paper has become honest about accuracy: it says "tie", reports an error-prone user and a sweep, and lists app gaps. My remaining concern is the distance between what is measured and what Cove does. In the code there is no correction endpoint, no persisted correction, no sync, no undo, and every import that adds a face wipes names. So E2 (two devices), E3 (retraction) and E4 (recogniser upgrade) are in-process function calls on one array of faces. The text says this only in limitation (vii), and (vii) names only one of the four missing pieces. The abstract and conclusion state the consequences in the present tense. The simulations also build in things a real deployment must supply: global face ids, one code version, no deletions, one-shot exchange. The privacy paragraph is accurate on everything I checked, but incomplete in both directions. These are fixable by rewording and a few lines of config. The engineering needed to make the claims literally true is about a week of work.

### Strengths
- **S1 Candid limitation (vii), verified.** Anchor: `text: §VI "the current app has no interface for corrections yet, re-clusters from scratch on every import, and overwrites user-assigned names"`. `_run_clustering_stage` builds a new clusterer and calls `save_people(..., overwrite=True)`, which sets `self.people = {}`. The frontend has only `renamePerson`.
- **S2 Failure is reported against the author's own method.** Anchor: `table: Table II error-pr. column, ours 0.9851 vs no corrections 0.9854`, plus the sweep ("-0.0057 at 0.20"). It is the most useful result for anyone building a UI.
- **S3 The two-device test has a real opponent.** Anchor: `table: Table III, two devices identical, Frozen + edits 53 / 31 %`. Replaying edit logs without set semantics is what a practitioner would actually build, and it fails. The paper also says c-avg shares the property.
- **S4 Exposure is stated, not hidden.** Anchor: `text: §VI Privacy "published ... on all network interfaces"`. Checked against compose: ports 8000/8001/8080, CORS `*` with credentials, `COVE_API_KEY` unset, no `x-api-key` in `frontend/src`.
- Pre-declared protocols, equal tuning, and a negative result (pose) are credible practice.

### Weaknesses

### W1: Simulated consequences are written as system behaviour, and the gap list is incomplete
**Problem:** The abstract's consequences sentence and the conclusion are in the present tense. Neither says that the app has no correction store or UI, no sync, no undo, and that an upgrade means re-indexing. Limitation (vii) covers corrections/re-cluster/names only. Sync and undo are absent from it. "Simulated" is attached to libraries and corrections, not to devices, retraction and upgrade.
**Evidence Anchor:** text: abstract "two devices that exchange photos and corrections end with identical people in all 240 libraries"; conclusion "keeps the user's corrections across later"
**Why it matters:** A reader who opens the released repo can see the gap in minutes (README: "the people found depend only on which photos are in the library"). Title, abstract and conclusion should survive that check.
**Suggestion:** (a) Abstract: "in simulation, with two in-process replicas ..."; add one sentence, "The correction interface, sync and undo are not yet in the app." (b) Conclusion: "the clusterer keeps / would keep". (c) Extend (vii) to list all four gaps. (d) Consider a method-first title. Alternative: wire the app (see the last section).
**Severity**: Major | **Confidence**: 5, both code and text read directly

### W2: "Two devices agree" rests on assumptions the simulation supplies and the app lacks
**Problem:** In exp21 both replicas address faces by the same global integer index into one array, run the same code on the same CPU, exchange once, and never delete or retract. A real exchange needs:
1. **Stable face keys.** The app keys by file path (`storage.paths`). `/upload` overwrites a same-named file, and a replaced photo keeps its old embedding (already indexed by path). IMG_0001.jpg from two phones collides. Use a content hash plus face box (or the single largest-face slot).
2. **Tombstones.** Retraction (Corollary ii) plus union-merge of sets (Corollary i) do not compose. A replica that still holds the retracted correction re-introduces it at the next union. Corrections need unique op ids with tombstones (OR-set style); the paper tests (i) and (ii) separately, never together.
3. **Deletion is non-monotone.** The proof and the incremental update rely on core status and links only switching false to true. Deleting a photo breaks that; the app rebuilds storage and re-clusters. Say that the speed claim is for additions only, and that corrections naming a deleted face must be dropped (also for erasure reasons: a correction is derived personal data).
4. **A version contract.** Labels depend on the recogniser, thresholds and code version. Devices must ship embeddings (about 2 KB per face), not recompute them. Otherwise last-bit differences in inner products across CPU kernels flip near-threshold pairs, which is the "exact tie" caveat in practice.
5. **Transport and key exchange** for biometric templates. The paper's own Docker users have thin clients on one server, which needs no convergence at all.
**Evidence Anchor:** dataset: `evaluation/exp21_replica_convergence.py` — faces are indices `perm[...]` of one shared array; `E.run(method, X, N, allcons, order=order)` for both replicas
**Why it matters:** The "100%" is partly by construction. The honest claim is "the design permits convergence if these pieces are added."
**Suggestion:** Add 3-4 sentences in §VI-D or the Discussion listing requirements 1-4, and soften "two devices that exchange" to "two simulated replicas". An export/import of faces+corrections as a JSON file between two data directories would give a real, cheap check.
**Severity**: Major | **Confidence**: 4, distributed-systems judgement; not tested

### W3: No credible path from "the click was wrong" to "retract that correction", and the stated reason for AUC 0.60 is not supported by the data
**Problem:** The paper says the wrong click is hard to flag "because look-alike merges join similar faces". In `exp22_undo_edgeface_s.json` the mean cosine is 0.277 for wrong and 0.316 for right must-links, so the wrong ones are slightly *less* similar. Right must-links are also low-similarity pairs, since the clusterer separated those faces (that is why the user clicked). Pairwise cosine is therefore the wrong detector, by construction. The user also does not see a correction, but a symptom (a stranger on a person page).
**Evidence Anchor:** text: §VI-D "because look-alike merges join similar faces"; dataset: exp22 `detector` mean_cos_wrong 0.277, mean_cos_right 0.316
**Why it matters:** "Corrections must be visible and removable" is the paper's take-away. Without a discovery mechanism, exact retraction is cheap but unused.
**Suggestion:** Fix the explanation. Add a short design note: (a) a ledger with two thumbnails, date and effect ("joined 'Person 3' (41 photos) and 'Person 9' (12)"); (b) sort by blast radius; (c) from a person page, list the corrections that shaped it (the constrained spanning forest gives the path); (d) one-click "undo last"; (e) harder confirmation for must-links than for cannot-links. A "reviewing user" simulation (undo with probability q) would test the value. With about 6 corrections per library a ledger is short; after years of use it is not.
**Severity**: Major | **Confidence**: 4, numbers read from JSON; UI advice is my judgement

### W4: Recogniser upgrade is simulated as re-embedding of identical crops; the app's upgrade is a full re-index
**Problem:** exp23 restricts to 210 libraries whose faces are identical under both models and keeps face indices. In the app each recogniser has its own index files (`faiss_index_edgeface_s.bin`, `embeddings_edgeface_s.npy`, README: "switching re-indexes faces once"). Consequences not in the paper: (1) everything is re-detected and re-embedded; from the paper's own 9.8 ms per face that is about 100 s per 10,000 faces for embedding alone, detection untimed (my arithmetic, not a measurement); (2) storage is about 2 KB per face, kept twice (index and `.npy`) per model; (3) the old model's files are never touched, so a deleted photo's old-model template remains on disk; (4) `people_db.json` is shared across models and overwritten; (5) each model needs tuned thresholds, and an unknown model silently gets `buffalo_s` thresholds (`clustering_config` falls back), although the cosine scale differs by about 0.10; (6) a changed detector changes the face set, so index keys no longer work.
**Evidence Anchor:** dataset: `cove/config/vision_config.py` `_face_sfx` per-model paths; `cove/config/face_clustering.py` fallback to `buffalo_s`
**Why it matters:** "Corrections survive an upgrade" holds for a fixed face set and a retuned model; an upgrade needs more than that.
**Suggestion:** State assumptions (same detector, key by photo+box, thresholds retuned per model) and the re-embedding cost; mention old-embedding cleanup in Privacy.
**Severity**: Minor | **Confidence**: 4, code read; costs are arithmetic

### W5: What 0.001-0.005 F1 means to a person is still not stated; Table II still bolds within-noise cells
**Problem:** Sampled exp21 libraries hold 289-1,298 faces (mean about 870 in the twelve I read). 0.002 B-Cubed F1 is on the order of two faces out of 870, spread over 20-40 person pages. Nobody sees that. What a person sees is the number of wrong person pages and how many fixes they must redo. The paper has that data (held share; corrections to reach 0.99) but states it only in passing, and still bolds 0.9945, 0.9928, 0.9920.
**Evidence Anchor:** table: Table II "Later: F1", differences of 0.0005-0.0045 between bolded and unbolded cells
**Suggestion:** Say once: "differences below 0.005 correspond to a handful of faces per library and are not visible to a user"; unbold cells within noise; add a "person pages needing a fix" count and "fixes to redo per import" (about 1.5-1.8 for re-apply, casual user; 0 for constraints, from the held share). One correction repairs about one split or merged person (+0.010 F1 for 6.3 corrections).
**Severity**: Minor | **Confidence**: 4

### W6: Privacy paragraph is accurate, but incomplete and slightly unfair to the desktop build
**Problem:** Verified: ports 8000/8001/8080 on all interfaces, CORS `*` + credentials, key optional and unused by the UI, upload/delete endpoints, no per-person delete. Not in the paper: (1) `start.sh`/`start.bat` also run uvicorn with `--host 0.0.0.0`, and Vite uses `host: "::"`; only the packaged desktop sidecar defaults to `127.0.0.1`, so the exposure is not "Docker only"; (2) `video-api` has no key mechanism at all and exposes `DELETE /videos/delete-all`, so "its optional access key" is true for the photo API only; (3) nginx proxies both APIs on 8080, so closing 8000/8001 alone does not help; (4) `docs/ARCHITECTURE.md` says "Nothing leaves the machine" and "Backends bind to 127.0.0.1 by default", which compose and the start scripts contradict.
**Evidence Anchor:** dataset: `docker-compose.yml` `ports: "8000:8000"`, `"8001:8001"`, `"8080:80"`; `start.bat` line 98 `--host 0.0.0.0`
**Why it matters:** The fix costs minutes and makes the strongest sentence in the Introduction true. Publishing `127.0.0.1:8080:80` and dropping the two API `ports:` entries is enough.
**Suggestion:** Make the compose change before submission and shorten the paragraph. Otherwise add points 1-3. "Local-first" is also applied loosely: Immich and PhotoPrism are self-hosted servers (the bib title says so), where phone photos do leave the phone, and Kleppmann's ideals include multi-device use.
**Severity**: Minor | **Confidence**: 4; browser-side exploitability untested

### W7: Two small code-claim imprecisions
"re-clusters from scratch on every import" should read "on every import that adds faces" (`faces_added or faces_changed or not _people_db_exists()`). "Corrections are stored with the clusterer" is in-process memory: the sets `must`/`cannot` are never serialised, and the app's single `fit_predict` call never uses multi-batch `add`.
**Evidence Anchor:** dataset: `server.py` `_run_clustering_stage`; `stable_cluster.py` `self.must = set()`
**Severity**: Minor | **Confidence**: 5

### W8: AI-use disclosure is honest but thinner than IEEE asks
IEEE's published wording (from secondary summaries and a search snippet; check the current Author Center page) asks to name the AI system, identify the specific sections, and explain the level of use, in the Acknowledgments. This paper names "Claude, Anthropic" with no model/version, says "used throughout this work" instead of listing sections, and states the level well. Author contributions are "to be completed"; the author block has placeholders. Suggest: add model name/dates, one line per area (code, experiments, text, literature search, simulated review), what the authors personally did and verified (e.g. each Table cell traced to a JSON), and check the CFP's own AI/plagiarism-detector rule.
**Evidence Anchor:** text: Acknowledgment "an AI assistant (Claude, Anthropic) was used throughout this work"
**Severity**: Minor | **Confidence**: 3, policy text not read at source

### Detailed Comments
- **Assumptions:** a face has a stable identity (W2); the user can find mistakes (W3); one library fits in one process; the user clicks like the simulated users, which the paper states.
- **Practical impact:** the algorithm is deployable; the app layer is missing. The Docker thin-client deployment has no replica problem, so the paper should say who needs convergence (two laptops importing separately).
- **Reading leads (unverified, from memory):** Kleppmann et al. 2019 (already cited); Kulesza et al., "Principles of Explanatory Debugging" (IUI 2015) for the ledger/explanation design. [UNVERIFIED]

### Questions for Authors
1. What is the persistent key of a face, and what happens to a correction when its photo is deleted or replaced by a same-named file?
2. If one device retracts a correction while another still holds it, what does the merge do?
3. Will the compose file in the release still publish 8000/8001 on all interfaces?
4. Which of the three consequences would you demonstrate through the real HTTP API?

### Minor Issues
- Frozen row "--" cells in Table II need "not run".
- Soften "as Immich does" to "Immich-style" throughout.
- Three new bib entries lack volume/pages/DOI.

### The one-week question
**Single addition: persistent, content-keyed corrections wired into the real import path.** Concretely: a corrections store keyed by photo content hash; `POST /people/merge` and `/people/{id}/not-this-person`; a ledger endpoint with remove; load corrections in `_run_clustering_stage` and drop `overwrite=True` (re-attach names by overlap); a two-button UI plus a list. Estimate 3-4 days for someone who knows the code. Add an export/import of faces+corrections between two data directories (half a day) to check convergence for real, and an integration test: import, correct, import more, restart, retract, compare with the never-made result.
**Is it worth it versus submitting now?** It buys honesty and a real demonstration, not acceptance: a regional conference will probably accept the simulated paper once claims are sized. The same honesty can be had in 30 minutes by rewording title, abstract and conclusion (W1). My advice: do the must-do list first (cut to 6 pages, W1 wording, compose hardening, compile, placeholders, AI disclosure). Spend the week on wiring only if the title keeps the word "Cove ... keeps corrections", and the deadline allows both. Otherwise submit now as a method paper and wire the app for the extended version.

---
**Recommendation:** Major Revision (borderline Minor).
**Confidence:** 4
**Calibration status:** NOT_CALIBRATED

**Plain-language verdict for the author:**
1. Your experiments are honest and well built; the simulated results are not the problem.
2. The problem is wording: the abstract and conclusion make simulated results sound like things Cove already does.
3. Cove today has no correction button, no sync and no undo, and it erases names whenever a new photo with a face arrives.
4. Either reword (30 minutes) or wire corrections into the app (3-4 days), and fix the Docker ports either way.
5. Add one sentence that tells a normal person what 0.002 F1 means, and fill in the disclosure details.

**Top 3 issues:** (1) W1 simulated consequences presented as system behaviour; (2) W2 two-device result depends on supplied identity, tombstone and version assumptions; (3) W3 no way to find the wrong correction, and the AUC explanation contradicts the paper's own JSON.
