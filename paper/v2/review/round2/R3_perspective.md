# Peer Review Report — Peer Reviewer 3 (Perspective), Round 2

## Manuscript Information
- **Title**: Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries
- **Manuscript ID**: `paper/v2/cove_paper.tex` (commit ce1b15d)
- **Review Date**: 2026-11-07
- **Review Round**: Round 2 (simulated panel, simplified run; sprint-contract and provenance scripts not executed)

---

## Reviewer Information

### Reviewer Role
Peer Reviewer 3 (Perspective)

### Reviewer Identity
Local-first / privacy software engineer. I build on-device media tools and I review whether claims about the product survive contact with the shipped code and with real family albums. I am not a face-recognition or clustering-evaluation specialist; statistical rigor is R1's remit and prior-art coverage is R2's.

### Review Focus
(1) Practical value of the corrections result for real family albums (simulated LFW libraries, oracle user). (2) The gap between the paper and the shipped Cove app, checked against `cove/api/server.py`, `cove/engines/stable_cluster.py`, `cove/engines/person_manager.py`, `cove/engines/face_recognizer.py`, `cove/pipeline/download_models.py`, `docker-compose.yml` and the frontend. (3) CPU/latency budget on the i5-8250U. (4) Privacy claims and the ethics of face grouping.

Blinding note: I read only `00_reviewer_cards.md` from the round-2 folder, plus the round-1 decision and the round-2 revision log.

---

## Overall Assessment

### Recommendation
- [ ] Accept
- [ ] Minor Revision
- [x] **Major Revision**
- [ ] Reject

### Confidence Score
**4** — the product, privacy and latency points are in my core area and I checked them against code and result files. I did not run the app, and I did not run the code-scaling concern in W4 (it comes from reading the code).

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

Seat reports always emit `NOT_CALIBRATED`: the final actual panel topology is not knowable until every seat has completed. A candidate profile never upgrades the seat report.

### Summary Assessment
The paper presents Cove's face clusterer: single linkage at m=1, plus attachment, plus a centroid merge. It accepts must-link and cannot-link corrections and gives the same output for any import order. Its headline is that corrections survive later re-clustering (100% hold, against 27% under plain re-clustering), at accuracy close to average linkage. The round-2 rewrite is much more honest than round 1. The clusterer code matches Sec. III line by line, the numbers I spot-checked match the JSONs, and the limitations name the app gap, the CORS issue and the largest-face restriction.

From a practitioner's view, four things still keep the paper from describing something a family could use:
- The headline numbers are mis-stated. "Ten corrections per library" is really a mean of 5.4. The 27% counts 33 libraries that received no corrections as 100% held; excluding them gives about 16%.
- The app exposes no way to make a correction at all, and it never uses the incremental path the title advertises.
- Corrections are keyed by integer face index, which the app renumbers when photos are deleted. The correction-aware merge also uses dense k×k matrices whose cost at real library sizes was never measured.
- The privacy sentence "neither photos nor embeddings leave the device" is not true of the recommended Docker deployment. That deployment publishes an unauthenticated API on all interfaces, and the API accepts any origin.

Most fixes are wording plus one re-computation and one timing run, so I recommend Major Revision rather than Reject.

---

## Strengths

### S1: Gaps and weak results are disclosed in plain words
The paper says the incremental gain is only 1.3× and "cheap but not constant-time". It states that the app does not persist corrections and overwrites names, that the API accepts any origin, that profile faces stay weak, and that the pose bonus failed. In my experience this level of candour is rare in system papers at this venue tier.
**Evidence Anchor**: `text: Sec. V-F "The update is therefore cheap but not constant-time."`

### S2: Order invariance matters in the real app, not only under artificial shuffles
In `server.py` `_run_face_detection_stage`, embeddings are collected through `concurrent.futures.as_completed` (lines ~642–669), so the face order in storage is non-deterministic even when the same folder is imported twice. The order-invariant clusterer is what makes the people view reproducible. The paper motivates this with import order. The thread-pool point is a stronger, concrete product argument that the authors could add in one sentence, and it also answers round-1's DA concern that invariance under arbitrary shuffles is unmeasured as a user need.
**Evidence Anchor**: `text: Sec. I "two imports of the same photos can show different people"`

### S3: The clusterer described is the clusterer shipped
`StableIncrementalClusterer._labels_constrained` implements exactly the four steps of Sec. III-C: sorted must-links first, core edges sorted by (−s, i, j) with cannot-link checks, best-first attachment, and a constrained average-linkage merge. `config/face_clustering.py` ships exactly the tuned setting (0.65 / 1 / 0.50 / 0.55).
**Evidence Anchor**: `text: Sec. IV "Tuned EdgeFace-S setting"`

### S4: The hardware target fits the stated audience
A 2017-era i5 laptop with 12 GB RAM, CPU only, and a recogniser chosen partly for speed (13.3 vs 27.5 ms/face single-thread) is a fair proxy for the machines students and families in India actually own.
**Evidence Anchor**: `text: Sec. IV Hardware "CPU only"`

### S5: Reported numbers match the released files
- `exp15_corrections_edgeface_s.json` ALL row: 0.9842 / 0.9939 / 0.9854 / 0.9925, lost-satisfied 0.273.
- `exp18_update_time_edgeface_s.json` last row: 3.53 s / 4.72 s / 16.69 s, add 0.145 s.
- `exp17b_track_bridge_hard_edgeface_s.json`: 0.585 / 0.784 / 0.719, F1 0.854 → 0.860, 171 video people.

All agree with the text. (W1 explains why one of these numbers is nevertheless mis-described.)
**Evidence Anchor**: `table: Table II — "All (8 cond.)" row matches exp15 ALL entries`

---

## Weaknesses

### W1: "Ten corrections per library" and "27% still hold" mis-describe the experiment
**Problem**:
- The abstract, Sec. V-C and the conclusion say ten corrections were made per library. In `exp15_corrections_edgeface_s.json` `per_library`, `corrections_made` has mean **5.4**: only 91 of 240 library×condition runs reached 10, and 33 runs had 0.
- The simulated user ran out of mistakes. The mean is 0.8 corrections on look-alike, 1.5 on clean, 2.1 on dark and 2.7 on blur, against 9.7 on low-res, occluded and mixed.
- `satisfied()` in `evaluation/exp15_corrections.py` (lines 105–108) returns 1.0 when there are no corrections, so the 33 empty runs count as "100% still hold" under plain re-clustering.
- Excluding them, the mean share held under plain re-clustering is **15.7%** (pooled per correction: 20.3%), not 27%. For MBF it is 13.5% (pooled 16.9%), not 26%.

**Evidence Anchor**: `text: Abstract "With ten simulated corrections per library"`

**Why it matters**:
- These are the paper's headline numbers.
- The error happens to understate the paper's own effect, but a reader cannot reproduce "ten per library".
- For a user, the more important fact is hidden: on reasonably good photos a ~1,000-face library had only one to three correctable mistakes. So the corrections feature pays off mainly on degraded photos. That is useful practical guidance and should be stated.

**Suggestion**:
- Write "up to ten (mean 5.4)" everywhere.
- Report the share held only over libraries with at least one correction, or pooled per correction, and say which.
- Add a column to Table II with the mean number of corrections made per condition.
- Re-state the abstract and conclusion figures.

**Severity**: Major
**Confidence**: 5 — recomputed directly from the released per-library JSON and the scoring function

### W2: The app has no way to make a correction; the limitation understates this
**Problem**:
- Limitation (vi) says the app "does not yet persist" corrections through re-clustering, which reads as if the app accepts corrections and then loses them.
- In fact the API has no merge, split, must-link or cannot-link endpoint. The routes are `/health`, `/hardware`, `/search/text`, `/index/image`, `/images`, `/people`, `/people/{id}/photos`, `/people/cleanup`, `/people/{id}/rename`, `/images/delete`, `/upload` and `/index/start|status`.
- `frontend/src/components/features/PeopleView.jsx` offers only rename. `add_must_link` / `add_cannot_link` are called only from tests and evaluation scripts.

The title ("Face Grouping That Keeps the User's Corrections") and the abstract ("We describe the face clusterer of Cove, a local-first media system") lead a reader to expect a shipped feature.

**Evidence Anchor**: `text: Sec. VI (vi) "the current app does not yet persist them through its re-clustering"`

**Why it matters**: The "100% kept" result describes a library feature evaluated on a simulated oracle. No Cove user can benefit from it today. In my experience, venue reviewers who try the released system will treat a mismatch like this as an honesty problem.

**Suggestion**:
- Minimum: state in the abstract or introduction and in (vi) that "the correction mechanism is implemented and evaluated in the clusterer library; the Cove app does not yet expose a correction interface."
- Stronger, and the author's choice: add the two endpoints and persist `must`/`cannot` beside the people DB before submission.

**Severity**: Major
**Confidence**: 5 — exhaustive route list and grep of backend and frontend

### W3: The shipped app never uses the incremental path, and the update-time result has little value to users
**Problem**:
- `_run_clustering_stage` (`server.py` ~L747–777) builds a new `StableIncrementalClusterer` on every indexing pass and calls `fit_predict` on all stored embeddings. The app therefore runs the "re-running our clusterer from scratch" path (4.7 s at 8,290 faces), not the 3.5 s incremental one.
- Round-1 issue 5 asked the authors to "say plainly that the app re-runs the (order-invariant) clustering". The revision log marks this Fixed by pointing to the corrections sentence, which is a different statement.
- Sec. V-F says "the shipped EdgeFace-S setting", meaning the shipped thresholds but not the shipped code path.
- The saving the user actually feels is small. Embedding the 829 new faces of one batch alone costs about 11 s single-thread (829 × 13.3 ms, Table III), before SCRFD and JPEG decoding, so the 1.2 s clustering saving is about 10% of one import. End-to-end CPU cost per import, requested in round 1, is still not reported.
- Read time grows faster than linearly in exp18: `inc_labels_s` goes from 0.107 s at 829 faces to 3.38 s at 8,290, roughly n^1.5. Naively extrapolated, that is tens of seconds at the 30k–100k faces of a decade of family phone photos, but the paper gives no figure beyond 8,290.

**Evidence Anchor**: `text: Sec. V-F "We added 8{,}290 clean LFW faces to a library in ten equal batches with the shipped EdgeFace-S setting, one thread."`

**Why it matters**: "Incremental" is in the title, yet the only measured benefit is not delivered by the product, and is marginal next to embedding cost.

**Suggestion**:
- Say plainly that the app currently re-runs the clusterer on all faces at each import, which is still order-invariant.
- Report end-to-end seconds per import: decode + detect + embed + cluster.
- Either measure `labels()` at 30k–50k faces (synthetic replication of LFW embeddings is acceptable if stated) or bound the claim to ≤8k faces.
- Consider dropping "Incremental" from the title if the app does not adopt the path.

**Severity**: Major
**Confidence**: 5 — code path read directly, timing taken from exp18 JSON

### W4: Cost of the corrections path at real library sizes is unmeasured and likely prohibitive
**Problem**:
- With any correction present, `labels()` switches to `_labels_constrained`. Its step 4 builds a dense k×k float64 similarity matrix over clusters, plus a k×k boolean matrix, and on every merge iteration allocates another k×k array via `np.where(bad, -np.inf, S)` (`stable_cluster.py` L262–293).
- Time is therefore O(k² × merges) and memory O(k²). At k = 20,000 clusters (singletons count; family libraries contain many one-off strangers) one such matrix is 3.2 GB, against the stated 12 GB RAM.
- The unconstrained path uses scikit-learn instead. Exp18 timed only that path, and exp15 used libraries of 146–1,348 faces (median 938).
- Both paths silently skip the merge when there are more than 20,000 clusters (L193, L260). That is an undisclosed behaviour cliff: accuracy changes abruptly above that size.

**Evidence Anchor**: `absence: Sec. V-F and Sec. V-C — expected time and memory of the corrections-enabled labels() at library scale; checked Sec. V-C, Sec. V-F, Table II, exp15 and exp18 JSON`

**Why it matters**:
- The headline feature is keeping corrections across re-clustering.
- If one correction turns a 4.7 s re-cluster into minutes, or an out-of-memory error, on a 10k–30k-face library, the feature is not usable on the stated hardware.
- I have not run this. The concern comes from reading the code, which is why confidence is 4.

**Suggestion**:
- Add one timing row: exp18's 8,290-face run with, say, 10 corrections, reporting peak RAM.
- If it is slow, restrict the constrained merge to the clusters that actually carry constraints. The unconstrained merge result is valid wherever no cannot-link is involved.
- Disclose the 20,000-cluster cut-off or remove it.

**Severity**: Major
**Confidence**: 4 — complexity derived from code reading; not executed

### W5: Corrections are keyed by face insertion index; deletions and re-indexing break them silently
**Problem**:
- `add_must_link(i, j)` / `add_cannot_link(i, j)` store integer face ids, which are positions in insertion order, and the clusterer has no removal operation.
- The app renumbers faces whenever photos are deleted: `/images/delete` → `_rebuild_storage_without`, `server.py` ~L389–440. A stored correction would then point at a different face, or at nothing.
- Re-detection after a model change (EdgeFace-S ↔ buffalo_s fallback, `_resolve_face_model`) also rebuilds the index.
- Proposition 1 and the monotonicity argument ("core status and links only switch from false to true") hold only for append-only libraries. Real libraries delete photos routinely: duplicates, blurry shots, the de-dup pass in `server.py` itself.
- A user-assigned name is itself a correction. Today it is keyed by `Person_{label}`, which is renumbered by `np.unique` on every run, so names would drift even without `overwrite=True`.

**Evidence Anchor**: `text: Sec. III-C "The corrections are stored with the clusterer and applied every time labels are computed, including after new photos"`

**Why it matters**: "Keeps the user's corrections" fails silently under the second most common library operation after import. Persistence is precisely what local-first software has to get right.

**Suggestion**:
- Scope the claim to append-only libraries in Sec. III-C and limitation (vi).
- Add a short design note: key constraints by a stable face key, such as a photo content hash plus a quantised face box. Define what happens when an anchor face is deleted (re-anchor to the cluster's next-central face, or drop it with a notice). Represent a named person as a must-link group, with cannot-links between differently named people, so that naming and corrections share one mechanism and survive re-clustering.
- Optionally, add an exp15 variant that deletes 10% of photos between "now" and "later".

**Severity**: Major
**Confidence**: 4 — code paths read; the deletion scenario was not executed

### W6: The privacy claim is not true of the recommended deployment
**Problem**: The introduction states without qualification that neither photos nor embeddings leave the device. In the shipped configuration:
- `server.py` L159–165 sets `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.
- The API-key middleware is enabled only if `COVE_API_KEY` is set. It is unset by default (`vision_config.py` L189) and not set in `docker-compose.yml`.
- So any web page open in the user's browser can, subject to whatever private-network-access protection the browser has (this varies by browser and version), read `/people`, fetch photos from `/media/test_images/`, and call `/images/delete` or `/upload`.
- Docker is the README's "recommended" install. Its compose file runs uvicorn with `--host 0.0.0.0` and publishes `8000:8000`, `8001:8001` and `8080:80` on all host interfaces (`docker-compose.yml` L10–20, L40–48, L68–71). Anyone on the same Wi-Fi (hostel, college, café) can browse and delete the library without credentials.
- Native runs bind 127.0.0.1 (L879), which removes the LAN exposure but not the cross-origin one.
- The paper's Privacy paragraph mentions only "accepts any origin", not the consequence and not the LAN exposure.

**Evidence Anchor**: `text: Sec. I "so neither photos nor embeddings leave the device"`

**Why it matters**: Local processing is the paper's motivating premise. Processing locally is not the same as keeping data local; a reader, or a family, would take the sentence as a guarantee.

**Suggestion**:
- Rephrase to "processing never sends photos or embeddings to a remote service", and state the threat model: the local API is currently unauthenticated, accepts any origin, and in Docker is reachable from the local network.
- Product fix, reported only and the author's choice: publish `127.0.0.1:8000:8000` in compose, generate a per-install token, and restrict origins to the app's own.

**Severity**: Major
**Confidence**: 4 — configuration read directly; exploitation not attempted, and browser private-network-access behaviour varies

### W7: Largest-face-only undercuts the motivating use case, and the consequence is not stated
**Problem**: Both indexing paths (`server.py` L286–287 and L659–661) sort faces by box area and keep only `faces[0]`, and the people DB maps people to photos. A group photo (wedding, festival, family dinner) therefore appears under at most one person. The introduction's example, "all photos of grandma", would miss every photo in which grandma is not the largest face. Limitation (iii) states the restriction but not this consequence.
**Evidence Anchor**: `text: Sec. VI (iii) "Only the largest face per photo is clustered."`
**Why it matters**: In family albums, multi-face photos are common, by my practitioner estimate the majority at gatherings. This limits recall for the paper's own motivating use case, though not the clustering result itself.
**Suggestion**: Add one sentence on the consequence. If feasible, report the share of LFW test photos in which SCRFD finds more than one face, as a rough indicator. List all-faces indexing as the first engineering step alongside (vi).
**Severity**: Minor
**Confidence**: 5 — code read directly

### W8: Ethics covers only dataset provenance, not the people being grouped
**Problem**: The Ethics declaration says only that public benchmark datasets were used. The paper does not discuss:
- the people pictured in a user's library who never consented to being grouped (relatives, children, bystanders; the "strangers" of the simulation);
- misuse: the same CPU pipeline, plus must-link tooling, can organise any scraped photo set by identity;
- the documented consent problems of web-scraped face benchmarks such as LFW, and of the WebFace data behind the recognisers;
- demographic differences in recognition error, which matter for Indian family albums that differ greatly from LFW's public-figure population.

The local-first design has a real ethical argument in its favour that the paper also leaves out: India's DPDP Act 2023 exempts processing by an individual for personal or domestic purposes (Sec. 3(c)(i)), and on-device processing keeps the use within that scope.
**Evidence Anchor**: `absence: Sec. VI Privacy and Declarations (Ethics) — expected discussion of consent of pictured non-users, misuse and demographic differentials; checked Sec. I, Sec. VI, Declarations`
**Why it matters**: The paper's framing is about face grouping for ordinary users. At an Indian IEEE venue, a short paragraph on these points is increasingly expected and costs little.
**Suggestion**: Add 3–4 sentences to the Privacy paragraph covering the household-use framing, non-consenting data subjects (offer per-person "forget" and opt-out), the misuse caveat, and a note that error rates are untested on Indian or child faces. Cite NIST IR 8280 and Raji & Fried (2021).
**Severity**: Minor
**Confidence**: 4 — applied-ethics and regulatory reading, not legal expertise

### W9: Model provenance and integrity are unstated; the round-1 hash-check item was dropped
**Problem**:
- `face_recognizer.py` downloads the EdgeFace-S ONNX from a third-party mirror (`github.com/yakhyo/edgeface-onnx`), not from Idiap.
- `download_models.py` checks only the byte count, with no SHA-256.
- The paper states neither the source nor the equivalence check that the code comment cites (cosine 0.9999998 against the official checkpoint).
- The revision log does not respond to round-1's hash-check item.

**Evidence Anchor**: `absence: Sec. III-A and Declarations (Licences) — expected the EdgeFace-S weight source and an integrity check; checked Sec. III-A, Sec. V-E, Declarations, REVISION_LOG_round2.md`
**Why it matters**: The model is a supply-chain dependency of a privacy-motivated tool. Reproducibility also depends on knowing exactly which weights were used.
**Suggestion**: Give the source and the equivalence result in one sentence. Pin and verify a SHA-256 in `download_models.py` (product item, author's choice).
**Severity**: Minor
**Confidence**: 5 — code read directly

### W10: "Successive partitions stayed consistent" does not mean the user's people view stays stable
**Problem**: ARI ≥ 0.998 between successive partitions is a statement about the partition. In the app, cluster labels are renumbered on every run (`np.unique(..., return_inverse=True)`), and person ids and names are keyed by `Person_{label}` (`person_manager.py` L31–37). After the next import, "Person 3" may be a different person, even with a near-identical partition.
**Evidence Anchor**: `text: Sec. V-F "Successive partitions stayed consistent"`
**Why it matters**: Readers may take partition stability as stable people and names, which the current product does not provide.
**Suggestion**: Add "as partitions; the app would also need to match clusters across runs (e.g., by maximum photo overlap) to keep person identities and names", or fold this into the W5 design note.
**Severity**: Minor
**Confidence**: 5 — code read directly

### W11: The simulated user and the "later" photos are not shaped like a real household
**Problem**:
- The "later" set is a random 20% of the same people's photos. Real imports are temporally clustered: a new event, new people, children a year older.
- The oracle picks "the central face of the main person" and the most similar wrong face, using ground truth. A real user sees a grid of photo thumbnails and would tap a wrong photo, not choose a face pair.

Limitations (i) and (ii) acknowledge the oracle, but not the random "later" split or the mismatch with the interface.
**Evidence Anchor**: `text: Sec. IV Corrections "each time fixing the largest remaining mistake"`
**Why it matters**: The rate at which plain re-clustering loses fixes (16–27%) likely depends on how new the later photos are. The magnitude in a real household may differ in either direction.
**Suggestion**:
- Name both points in limitation (ii).
- Optionally, add a variant where "later" holds whole new identities or each person's latest-dated photos, and one where the corrected face is a random member of the wrong group rather than the most similar one.
- Specify the interface mapping: a cannot-link from a tapped photo to the person's central face.

**Severity**: Minor
**Confidence**: 4 — practitioner judgement on household photo behaviour

---

## Detailed Comments

### Assumption Audit
- **Explicit assumptions**: Corrections are hard constraints that are always right (limitation ii). For a family album that is mostly sound. Wrong user corrections do occur, though (twins, a parent and an adult child), and with hard constraints a wrong cannot-link is permanent and invisible. A "review my corrections" view is the practical counterpart.
- **Implicit assumptions**:
  - The library is append-only (W5).
  - One face per photo carries the meaning of the photo (W7).
  - Clustering time is the bottleneck of an import. It is not: embedding is (W3).
  - "On-device" implies "private" (W6).
- **Paradigmatic assumptions**: Accuracy is judged by B-Cubed F1 against celebrity identities. The user-facing quantity is effort: corrections needed, and corrections lost per import. W1's recomputation shows the two can diverge, so the paper would be stronger if the effort metric led.

### Cross-Disciplinary Connections
- **Parallel research**: Local-first software (Kleppmann et al., 2019) treats user edits as durable state that must merge with automatic updates. This is exactly the corrections-survive-re-clustering problem. Its framing of operations keyed by stable ids, never by positions, is the direct fix for W5.
- **Borrowing opportunities**: Treat names and corrections as one constraint log keyed by stable face keys and replayed on each clustering. That gives auditability and undo, and it suits the order-invariance proof, since the proof already depends only on the set of constraints.
- **Methodological borrowing**: HCI-style effort metrics (clicks or corrections per 1,000 photos) and a small diary study with 2–3 real family albums with owner consent. Even an informal one would answer the representativeness question better than more LFW conditions.

### Practical Impact
- **Real-world application**: The order-invariance property is product-relevant now (S2). The corrections mechanism is relevant once wired in, but only after W4 and W5 are solved.
- **Implementation feasibility**: The barriers are engineering ones: an endpoint and UI, stable keys, a scalable constrained merge, and all-faces indexing. None needs new research, and the paper should say so.
- **Stakeholders**: The people who are photographed but are not the user (W8). Also the family's less technical members, who will use whatever defaults the Docker install sets (W6).

### Broader Implications
- **Ethical dimensions**: See W8. The local-first design is the paper's best ethical argument, and it should be made explicitly together with its caveats.
- **Social impact**: The approach lowers the barrier to identity-organising photo sets on commodity laptops. That is benign for household use and dual-use otherwise; one sentence suffices.
- **Future directions**:
  - deletion-robust constraint persistence;
  - correction-aware merge restricted to constrained clusters;
  - multi-face indexing with in-photo cannot-links: two faces in one photo are different people by construction, which is a free constraint source analogous to the video-track must-links in Sec. VI;
  - evaluation on consented real family albums.

The in-photo cannot-link is, in my view, the most promising and cheapest follow-up. It needs no user effort and directly targets the merge errors that users find hard to notice.

---

## Cross-Disciplinary Reading Recommendations
- Kleppmann, Wiggins, van Hardenberg, McGranaghan (2019), "Local-first software: you own your data, in spite of the cloud", Onward! '19. Verified via web search (Cambridge repository and ACM records; DOI 10.1145/3359591.3359737). It frames durable user edits and data ownership in the paper's own vocabulary (W5, W6).
- Grother, Ngan, Hanaoka (2019), "Face Recognition Vendor Test (FRVT) Part 3: Demographic Effects", NISTIR 8280. Verified via web search (NIST publication page; DOI 10.6028/NIST.IR.8280). It shows demographic differences in error rates, including elevated false positives for children and the elderly, which is directly relevant to family albums (W8).
- Raji, Fried (2021), "About Face: A Survey of Facial Recognition Evaluation", arXiv:2102.00813. Verified via web search (arXiv). It documents consent and provenance problems of face benchmarks, including LFW-era web-scraped data (W8).
- India, Digital Personal Data Protection Act 2023, Sec. 3(c)(i), the personal/domestic-purpose exclusion. Text confirmed via web search on secondary legal sources. The commencement date of the section is reported inconsistently, so check the official gazette before citing (W8).

~~~yaml suggested-references
- title: "Local-first software: you own your data, in spite of the cloud"
  authors: ["Kleppmann, M.", "Wiggins, A.", "van Hardenberg, P.", "McGranaghan, M."]
  year: "2019"
  doi: "10.1145/3359591.3359737"
  arxiv_id: null
- title: "Face Recognition Vendor Test (FRVT) Part 3: Demographic Effects"
  authors: ["Grother, P.", "Ngan, M.", "Hanaoka, K."]
  year: "2019"
  doi: "10.6028/NIST.IR.8280"
  arxiv_id: null
- title: "About Face: A Survey of Facial Recognition Evaluation"
  authors: ["Raji, I. D.", "Fried, G."]
  year: "2021"
  doi: null
  arxiv_id: "2102.00813"
~~~

---

## Questions for Authors
1. With 10 corrections on the 8,290-face exp18 library, how long does `labels()` take and what is the peak RAM? Does it stay within the i5/12 GB budget?
2. What should happen to a must-link or cannot-link when one of its two faces is deleted? Will constraints be keyed by something other than the insertion index?
3. Will the submitted version describe the corrections as a library feature, or will the app gain a correction endpoint and UI before submission?
4. Is the Docker install intended for single-machine use only? If so, would you publish ports on 127.0.0.1 and generate an API token by default?

---

## Minor Issues

### Language / Grammar
- Sec. VI future work: the CPLFW F1 "0.854" (exp17b, with track photos removed) sits next to Table I's 0.841 on a different photo set. Add "(on the photos that remain)" so readers do not see a contradiction.

### Figures and Tables
- Table II: add a "mean fixes made" column (W1). The "Fixes held" header "27% / 100%" should say which denominator is used.

### Layout
- Author placeholders remain (also noted in the revision log).

---

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | quality_rubrics (R2/EIC remit) | NOT_ASSESSED | — | Outside R3 remit | — | no — other seats |
| Methodological Rigor | quality_rubrics (R1 remit) | NOT_ASSESSED | — | Outside R3 remit, except the corrections-metric point raised as W1 | — | no — other seats |
| Evidence Sufficiency (practical claims) | Reviewer card R3: practical value, CPU budget | PARTLY_MEETS | `text: Abstract "With ten simulated corrections per library"`; `absence: Sec. V-F — corrections-path timing` | Headline counts mis-described; corrections path untimed at scale; no end-to-end cost | W4 is from code reading | yes — W1, W4 need new numbers |
| Argument Coherence | quality_rubrics (DA remit) | NOT_ASSESSED | — | Outside R3 remit | — | no |
| Writing Quality | quality_rubrics | MEETS | `text: Sec. V-F "cheap but not constant-time"` | Plain, direct, and honest about weak results | — | no |
| Literature Integration | quality_rubrics (R2 remit) | NOT_ASSESSED | — | Outside R3 remit; cross-disciplinary leads given above | — | no |
| Significance & Impact | Reviewer card R3: real family albums | PARTLY_MEETS | `text: Sec. VI (iii) "Only the largest face per photo is clustered."` | Order invariance is product-relevant now; the corrections feature is not reachable by users and has untested persistence | Representativeness of LFW for Indian albums is judged, not measured | yes — W2, W5 |
| Honesty of product statements | Reviewer card R3: paper vs app gap | PARTLY_MEETS | `text: Sec. VI (vi) "the current app does not yet persist them through its re-clustering"` | Limitations exist but understate: no correction UI, app is non-incremental | none identified | yes — W2, W3 (wording fixes) |
| Privacy claims | Reviewer card R3: privacy | DOES_NOT_MEET | `text: Sec. I "so neither photos nor embeddings leave the device"` | Unqualified claim contradicted by the recommended deployment's unauthenticated LAN- and cross-origin-reachable API | Browser private-network-access protections vary | yes — W6 (wording fix suffices) |
| Ethics of face grouping | Reviewer card R3: consent, misuse | PARTLY_MEETS | `absence: Declarations (Ethics) — non-user consent` | Dataset ethics only | Not legal advice | no — Minor |

Recommendation rationale: Major Revision. The unresolved decision-bearing items are:
- W1 (recompute and re-state the headline numbers): repairable from existing JSONs.
- W2, W3 and W6 (wording about the app and privacy): repairable in text.
- W4 (time the corrections path at scale): one experiment.
- W5 (scope to append-only, plus a design note): text, with an optional experiment.

None is fatal. The strengths do not offset them, because these items concern what the paper tells users the system does.
