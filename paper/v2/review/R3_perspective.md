# Peer Review Report

## Manuscript Information
- **Title**: Order-Stable Incremental Face Clustering for Local-First Personal Photo Libraries
- **Manuscript ID**: cove_paper.tex (v2)
- **Review Date**: 2026-11-06
- **Review Round**: Round 1

---

## Reviewer Information

### Reviewer Role
Peer Reviewer 3 (Perspective)

### Reviewer Identity
Local-first / privacy software engineer. I look at practical value for real family albums, update latency, CPU budget, and on-device privacy claims. I also checked the released implementation (`cove/engines/stable_cluster.py`, `cove/api/server.py`, `cove/engines/person_manager.py`, `cove/config/face_clustering.py`, `evaluation/exp7_order_stability.py`, `evaluation/results/exp7_order_stability.json`) against what the paper says.

### Review Focus
Does the shipped system get the practical benefit the paper claims (stable, named people that survive library growth; cheap updates on a laptop CPU; nothing leaves the device)? And do the simulated libraries look like the albums real users have?

---

## Overall Assessment

### Recommendation
- [x] **Major Revision**

### Confidence Score
4. I know local-first and desktop-sidecar engineering well. I know face recognition as an adjacent field.

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

### Summary Assessment
The paper finds that greedy leader clustering depends on input order. It proposes a core-face union-find clusterer whose partition depends only on the set of faces, then evaluates it on LFW-derived libraries with degradations and compares four lightweight recognisers. From a practitioner's view the problem is real and well motivated, the algorithm is simple enough to ship, and the limitations section is unusually honest. The order-invariance result itself holds up: the proposition matches the code (core and link state only grows, and attachment is resolved at read time from the final lists).

The practical claims are a different story. The deployed system does not run the incremental path the paper evaluates. Each indexing pass re-clusters every face from scratch and rewrites the people database with `overwrite=True`. Partition invariance holds "up to renaming of cluster ids", so it does not protect the thing users care about, which is the names they gave people. The update-latency evidence is thin. At small sizes the "incremental" update costs the same as re-clustering, its cost grows roughly linearly with library size, and it was only measured up to 13k faces. The privacy paragraph is architecturally true, but the local API allows cross-origin requests from any website and needs no key by default. Finally, the libraries contain no children, no group photos and little demographic diversity, so the robustness numbers may not carry over to real family albums. None of this breaks the order-invariance result. Each point still needs rewriting, a new measurement, or narrower claims, so I recommend Major Revision.

---

## Strengths

### S1: The problem comes from real users and is measured, not assumed
The paper turns a concrete product complaint (re-importing reshuffles people) into a measurement: order agreement as low as 0.756 across 20 orders. Practitioners will recognise this failure.
**Evidence Anchor**: `text: §I "Two users with the same photos can see different people, and re-importing a library can reshuffle people the user has already named."`

### S2: The invariance claim matches the code
In `StableIncrementalClusterer.add`, core status and links only ever change from false to true. Attachment and the merge step are recomputed from the final adjacency lists in `labels()`. This is what the proof sketch describes. A claim that is exact and checkable is valuable in a consumer product.
**Evidence Anchor**: `text: §III-B "Core status and links only ever switch from false to true when faces are added, so no earlier decision needs to be undone."`

### S3: The privacy and limitations statements are honest
The paper says embeddings are as sensitive as photos, states plainly that it makes no formal privacy claim, and lists its failure modes (pose, age, occlusion, largest face only, a shared LFW pool).
**Evidence Anchor**: `text: §VI "face embeddings stored on disk are as sensitive as the photos and should be protected by the device's own encryption"`

### S4: The recogniser is chosen within a real CPU budget
The paper compares recognisers on identical crops, reports 1-thread and all-core latency on a mid-range 2017 laptop CPU, and re-tunes thresholds for the new similarity scale instead of reusing the old ones (Table III, third column). This is how a deployment decision should be made.
**Evidence Anchor**: `table: Table III — "EdgeFace-S, MBF thr." column, Occluded 0.650`

---

## Weaknesses

### W1: The shipped system re-clusters from scratch every time, so the evaluated incremental path is not what users run
**Problem**: The paper presents "an incremental clusterer for the Cove local-first media system" and its update-time experiment calls `add()` batch by batch. In the shipped code, `_run_clustering_stage()` (`cove/api/server.py`, about lines 768-773) builds a new `StableIncrementalClusterer(...).fit_predict(all_embeddings)` on every indexing pass. No clusterer state (adjacency lists, union-find parents, core flags) is saved between passes. The deployed system is therefore a batch method that is order-invariant. It is not incremental.
**Evidence Anchor**: `text: Abstract "We present an incremental clusterer for the Cove local-first media system that is order-invariant by construction"`
**Why it matters**: The paper's case against batch re-clustering ("too slow to re-run on every import") is exactly how the product behaves. Readers will assume the measured update latency is what Cove users get.
**Suggestion**: Either save the clusterer state (adjacency, parent, core and eligibility arrays) in the user data directory and call `add()` on new faces only, then re-measure end-to-end update time in the real app. Or rewrite the system description to say the deployed version re-runs the order-invariant clusterer in batch, and that the incremental path is evaluated offline only.
**Severity**: Major
**Confidence**: 5 — I read the deployed code path directly

### W2: Order invariance does not keep user-assigned names, and the shipped system deletes them
**Problem**: The proposition guarantees the same partition "up to renaming of cluster ids". The motivating harm in §I, though, is reshuffling people "the user has already named". In the code, `PersonManager.save_people(labels, face_paths, overwrite=True)` clears the database before every re-cluster. Ids come from `np.unique` and agglomerative labels, so they get renumbered whenever faces are added. Names set through `/people/{id}/rename` are therefore lost on the next indexing pass. Even if they were kept, growth can merge clusters (new links) and the centroid merge can regroup clusters. The paper never discusses how names and user corrections should map onto the new clusters.
**Evidence Anchor**: `text: §III-B Proposition "the same for every insertion order and every split of F into batches (up to renaming of cluster ids)"`
**Why it matters**: For a family-album user, a stable name ("Grandma") is the visible product. A partition that is stable but gets renumbered, with names wiped, does not fix the problem the introduction describes. Also, union-find never undoes a link, so a wrong merge cannot be split by the user.
**Suggestion**: (a) Add a label-carry-over step: match new clusters to old named clusters by maximum face overlap (Hungarian matching, or majority vote by face id) and report a "named-person survival rate" across the ten streaming batches. (b) Support must-link and cannot-link corrections from the user (constrained clustering, e.g. Wagstaff et al. 2001) and explain how they work with the monotone link graph. (c) At minimum, change the Proposition's motivating sentence and the Discussion so they do not imply that names survive.
**Severity**: Major
**Confidence**: 5 — I traced rename, re-cluster and `save_people(overwrite=True)` in the code

### W3: The update-latency claim is weak and only measured on a small library
**Problem**: In `evaluation/results/exp7_order_stability.json` the "incremental" update costs 0.29 s against 0.27 s for a Two-stage re-cluster at 1,323 faces, and 7.69 s against 7.81 s at 9,263 faces. It only pulls ahead at 13,233 faces (11.25 s against 15.67 s). The cost grows roughly linearly with total library size, not with batch size. That is because `labels()` re-scans every face's attachment and re-runs average linkage over all centroids, singletons included, on every read. The experiment also used old thresholds (m=3, link 0.40), not the shipped configuration.
**Evidence Anchor**: `figure: Fig. 3 — per-batch update time; at 13,233 faces 11.3 s vs 15.7 s (Two-stage)`
**Why it matters**: A real phone library holds tens of thousands of faces, often more, and per-person counts are skewed (one child can appear in thousands of photos). "Faster than re-clustering" is the paper's practical reason for preferring incremental updates, and the data barely supports it. Two more risks go unmeasured. Memory is "linear in the number of similar pairs", but that number grows quadratically with photos per person, and `adj` is a Python list of tuples. `_merge` silently skips the merge step when there are more than 20,000 clusters, which changes the output for large libraries with many strangers.
**Suggestion**: Re-run Fig. 3 with the shipped thresholds and plot update time against batch size and against library size separately. Include a synthetic 50k-100k-face library with a heavy-tailed photos-per-person distribution. Report peak RAM. Either cache attachment and merge results for untouched components, or reword the claim to "comparable to or modestly faster than re-clustering at up to 13k faces". Document the 20,000-cluster cutoff.
**Severity**: Major
**Confidence**: 4 — I read the raw timings and the code; I did not re-run them

### W4: Only the largest face per photo is clustered, which leaves out most people in family albums
**Problem**: The detection stage (`_detect` in `server.py`) sorts detected faces by area and keeps only `faces[0]`. The paper mentions this once in the limitations ("We clustered the largest face per photo only"). It does not say that the shipped product behaves the same way, or what that means in practice.
**Evidence Anchor**: `text: §VI "We clustered the largest face per photo only."`
**Why it matters**: Family albums are full of group photos: weddings, festivals, dinners. Grandparents and children in the background never appear under their person, so "all photos of grandma" is systematically incomplete. Small background faces are also the low-resolution case where the attach threshold should help most, so the robustness result is never tested on those faces in deployment. Multi-face photos also add cannot-link information for free (two faces in the same photo are different people), which this design ignores.
**Suggestion**: Index every detected face above a minimum size and report the face counts. Evaluate on a multi-face benchmark, or at least on synthetic group composites. Consider same-photo cannot-link constraints. If that is out of scope, say clearly in §III-A and the abstract that both the method and the product index one face per photo.
**Severity**: Major
**Confidence**: 5 — I read the code; the practical consequence follows directly

### W5: The local API is readable cross-origin, which undercuts "neither the photos nor the face embeddings leave the device"
**Problem**: `server.py` installs `CORSMiddleware(allow_origins=["*"], allow_credentials=True, allow_methods=["*"])`. The `x-api-key` check runs only when `COVE_API_KEY` is set, and it is unset by default. The server binds to 127.0.0.1, which blocks other machines but not browsers. Any web page the user visits can call `http://127.0.0.1:8000/people`, `/people/{id}/photos` and `/media/test_images/...` and read the people database and photos. It can also send `/people/{id}/rename` and `/images/delete`.
**Evidence Anchor**: `text: §I "so neither the photos nor the face embeddings leave the device"`
**Why it matters**: For a paper that sells local-first privacy, a localhost sidecar open to cross-origin reads is the usual way such data does leave the device. The paper's privacy paragraph covers the intended data flow, not this exposure. (I am reporting this, not fixing it, per project rules.)
**Suggestion**: In the system, limit CORS to the app's own origin (for example the Tauri or Electron scheme), and require a random per-install token that the UI shell passes in. In the paper, either describe that mitigation or weaken the privacy sentence to "processing is local; the local API surface was not security-audited".
**Severity**: Major
**Confidence**: 4 — I read the middleware configuration; I did not run a live cross-origin probe

### W6: The evaluation population does not resemble the target users' albums
**Problem**: The libraries are LFW celebrities: mostly adults, mostly well-lit press photos, with a known demographic skew. There are no children and no infants, and nothing tests skin-tone balance. The authors are based in India and Cove's users are personal-album owners, yet no demographic breakdown is reported for any of the four recognisers.
**Evidence Anchor**: `text: §VI "Our libraries are simulations built from LFW celebrities"`
**Why it matters**: Lightweight recognisers are known to vary in accuracy across demographic groups. Children change appearance quickly. Both affect the false-merge and false-split rates a family actually sees. Choosing EdgeFace-S on CALFW, CPLFW, AgeDB and CFP-FP alone cannot show it is the better choice for an Indian family album.
**Suggestion**: Report per-group verification accuracy for the four recognisers on RFW (Wang et al., ICCV 2019), which has an Indian subset, using the same crop pipeline. Add children-ageing as a named limitation. State plainly that the robustness numbers come from adult celebrities.
**Severity**: Major
**Confidence**: 3 — adjacent field (face-recognition fairness); applying general deployment standards

### W7: CPU budget is reported for embedding only, not end to end
**Problem**: Table II gives ms per face for the recogniser. SCRFD detection, image decoding, and the CLIP semantic re-index that runs in the same pass are not reported. The paper also does not give per-photo throughput or the time to index a typical library from a cold start on the i5-8250U.
**Evidence Anchor**: `table: Table II — rows "1 thread" / "All cores" (recogniser latency only)`
**Why it matters**: Saving about 8 ms per face matters only in proportion to the full pipeline. A user cares about how long the first import of 20k photos takes and whether the laptop stays usable meanwhile.
**Suggestion**: Add one row or sentence with end-to-end photos per second (decode + detect + align + embed), plus total first-index time for a 10k-photo library, for MBF and EdgeFace-S.
**Severity**: Minor
**Confidence**: 4 — core expertise: desktop performance budgeting

### W8: Non-commercial weight licences and unverified downloads limit deployment
**Problem**: The paper notes that InsightFace and EdgeFace weights are non-commercial, but it presents EdgeFace-S as "the configuration Cove now ships", and the repository has a Windows installer. `pipeline/download_models.py` fetches the EdgeFace ONNX file from a third-party GitHub release (`yakhyo/edgeface-onnx`) and does not check a hash.
**Evidence Anchor**: `text: Declarations "InsightFace models and EdgeFace weights are licensed for non-commercial research use."`
**Why it matters**: A reader who wants to adopt the system needs to know that they cannot redistribute it commercially. An unpinned model download is a supply-chain weak point in a privacy-focused product.
**Suggestion**: State the redistribution restriction next to the "Cove now ships" sentence. Pin a SHA-256 for every downloaded model.
**Severity**: Minor
**Confidence**: 4 — core expertise: software distribution

---

## Detailed Comments

### Assumption Audit
- **Explicit assumptions**: Order invariance is the right stability target. That holds for the partition, but users experience stability through names (W2).
- **Implicit assumptions**: (1) The deployed system uses the incremental path (it does not; W1). (2) One face per photo is representative (W4). (3) "Update" means clustering only, excluding detection, embedding and label read-out (W3, W7). (4) Localhost means private (W5).
- **Paradigmatic assumptions**: Evaluation is purely offline against benchmark labels. In a local-first product the human is part of the loop (naming, merging, splitting), and none of the metrics include user corrections or the cost of fixing mistakes.

### Cross-Disciplinary Connections
- **Parallel research**: Local-first software (Kleppmann et al., 2019) frames "the user's data survives updates" as a core requirement, which is exactly the name-persistence gap in W2. Constrained clustering with must-link and cannot-link constraints (Wagstaff et al., 2001) is the standard way to fold in user corrections and same-photo exclusions.
- **Borrowing opportunities**: The paper could measure "label churn" between successive library states, as done for stable cluster ids in stream-processing systems, alongside ARI.
- **Methodological borrowing**: A small consented pilot (even 2-3 real family albums held by the authors, with only metrics published) would test the LFW simulation far more strongly than any further benchmark.

### Practical Impact
- **Real-world application**: The algorithm is useful and cheap enough to ship. Its practical value depends on W1 and W2 being fixed in the product.
- **Implementation feasibility**: Saving the clusterer state is easy (a few NumPy arrays plus JSON). Label carry-over is a small Hungarian-matching step. Neither needs new research.
- **Stakeholders**: People in the background of group photos (W4), children, and non-celebrity demographics (W6) are the groups the current evaluation leaves out.

### Broader Implications
- **Ethical dimensions**: Face clustering of family members, including minors, who did not consent to biometric processing. The paper could suggest an opt-in toggle and a "forget this person" action that deletes the stored embeddings.
- **Social impact**: Locally stored embeddings make it easy to link the same person across devices if they are exfiltrated. This raises the stakes of W5.
- **Future directions**: Multi-face incremental clustering with same-photo cannot-link constraints; persistent identity ids under growth; a consented real-album study.

---

## Questions for Authors
1. Is the Fig. 3 latency meant to describe the shipped product? If so, when will `server.py` keep clusterer state and call `add()` on new faces only?
2. After a user renames "Person 3" to a real name, what happens to that name when 500 new photos are indexed? Can you report a named-person survival rate?
3. What are update time and peak RAM at 50k-100k faces with a realistic heavy-tailed photos-per-person distribution, and how often does the 20,000-cluster merge cutoff trigger?
4. Is the CORS-open, keyless localhost API intended? If not, which mitigation do you plan to describe in the paper?

---

## Minor Issues
- §V Update time / Fig. 3: state in the caption that the thresholds differ from the shipped configuration (the body already says this).
- §IV: "Photos in which no face is detected are reported and left out". Say what the product does with them (it caches them as faceless).

---

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | quality_rubrics.md | NOT_ASSESSED | — | R2's remit | — | no |
| Methodological Rigor | quality_rubrics.md | NOT_ASSESSED | — | R1's remit | — | no |
| Evidence Sufficiency | quality_rubrics.md | PARTLY_MEETS | W3, W6, W7 | Latency and population evidence do not support the practical claims at realistic scale | Timings not re-run | yes: latency claim needs new data or narrower wording |
| Argument Coherence | quality_rubrics.md | NOT_ASSESSED | — | DA's remit | — | no |
| Writing Quality | quality_rubrics.md | MEETS | S3 | Plain and honest | none identified | no |
| Literature Integration | quality_rubrics.md | NOT_ASSESSED | — | R2's remit | — | no |
| Significance & Impact | quality_rubrics.md | PARTLY_MEETS | W1, W2, W4, W5 | The real problem is solved at the partition level, but the shipped product does not deliver the user-visible benefit | Code inspected, not run | yes: repairable through system changes or narrower claims |

The decision-bearing items (W1-W5) can all be fixed: through engineering changes plus re-measurement, or by narrowing the claims. None of them touches the proposition.

---

### Cross-Disciplinary Reading Recommendations
- Kleppmann et al., "Local-first software: you own your data, in spite of the cloud" (Onward! 2019): sets out the user-data-ownership and persistence requirements behind W2 and W5.
- Wagstaff et al., "Constrained K-means Clustering with Background Knowledge" (ICML 2001): the standard must-link and cannot-link formulation, for user corrections and same-photo exclusions (W2, W4).
- Wang et al., "Racial Faces in the Wild: Reducing Racial Bias by Information Maximization Adaptation Network" (ICCV 2019): the RFW benchmark, with an Indian subset, for W6.

(Metadata comes from my own knowledge and was not checked against an index in this session; the dispatcher should run the suggested-reference check.)

```yaml suggested-references
- title: "Local-first software: you own your data, in spite of the cloud"
  authors: ["Kleppmann, M.", "Wiggins, A.", "van Hardenberg, P.", "McGranaghan, M."]
  year: "2019"
  doi: "10.1145/3359591.3359737"
  arxiv_id: null
- title: "Constrained K-means Clustering with Background Knowledge"
  authors: ["Wagstaff, K.", "Cardie, C.", "Rogers, S.", "Schroedl, S."]
  year: "2001"
  doi: null
  arxiv_id: null
- title: "Racial Faces in the Wild: Reducing Racial Bias by Information Maximization Adaptation Network"
  authors: ["Wang, M.", "Deng, W.", "Hu, J.", "Tao, X.", "Huang, Y."]
  year: "2019"
  doi: null
  arxiv_id: "1812.00194"
```
