# Round 5 novelty re-check (adversarial prior-art search)

Date: 2026-11-10. Goal: find prior work that makes each claimed component not new. Tools: SciSpace (SS), Consensus (CO), WebSearch standard (WS), WebFetch (WF), SciSpace record fetch. Scholar Gateway (SG) returned ACCESS_DENIED on both calls. No query contained author names, e-mail or the system name.
Reading-level tags: **[abs]** abstract only (search tool or SciSpace fetch); **[page]** page opened with WebFetch (the fetch tool summarises and caps quotes at about 125 characters); **[snip]** search-result summary only, not confirmed on the page.

## 0. Bottom line

| Comp | Round-5 verdict | Round 4 said |
|---|---|---|
| C1 convergent set-function clusterer | **Partly known.** Principle and design pattern are published and in 2026 were applied to other ML artefacts. Application to a clustering with user constraints: not found | Not found |
| C2 exact retraction; wrong-constraint detection | **Known** as a principle (exact unlearning, retroactive structures, ER rule evolution) and for detection. **Not found:** a constrained-clustering statement or a frozen-label comparison | Not found / Known |
| C3 constraints across a recogniser change | **Partly known** (PhotoPrism docs; multi-view constraint transfer). **Not found:** measured retention of the gain (47-48%) | Not found |
| C4 exact split at threshold-graph components | **Known.** Textbook for single linkage; stated and proved for all standard linkages in a 2026 preprint | "Not found as a named result" |
| C5 shipping apps | No official page I opened documents how diverging devices are reconciled; Ente maintainers acknowledge divergence in an issue thread | Apple wording unverified |
| C6 order-independent + hard constraints + incremental | **Partly known.** Each property is published; the conjunction as one stated result was not found | Pieces known |

## 1. Query log

SciSpace queries also carried a `limit:6` to `limit:8` token (omitted below); year tokens are kept. Hits are the closest three, abstract level.

| # | Comp | Tool | Query (verbatim) | Hits that matter |
|---|---|---|---|---|
| 1 | C1 | SS | Can a clustering algorithm be designed as a conflict-free replicated data type, or be strongly eventually consistent, so that replicas that exchange data points converge to identical clusters regardless of order? | Shapiro 2011; Gillespie 2026; Almeida 2024 (none on clustering) |
| 2 | C1 | SS | Order-independent deterministic clustering whose result is a pure function of the set of items, so that distributed copies of a dataset converge to the same clustering without coordination | Bandyopadhyay & Murty 2016; Carlsson & Memoli 2008; Katselis 2014 |
| 3 | C1 counter | SS | Have conflict-free replicated data types or local-first techniques been applied to derived machine learning state such as vector indexes, embeddings, classifiers or clusters? year:2020-2026 | Gillespie 2026; Baquero & Brito 2026; OrderlessFL 2022 |
| 4 | C1 | CO | convergent clustering replicas conflict-free replicated data type eventual consistency clustering | Shapiro 2011; Almeida 2023; Gomes 2017 |
| 5 | C1 | WS | CRDT clustering algorithm replicas converge identical clusters eventual consistency "clustering" local-first | none on clustering |
| 6 | C1 | SS | How are user corrections to face groups merged and synchronised across several devices of one user in a personal photo collection? | Apple patent 2017; Chen 2018-19 patents; Wen 2007 patent |
| 7 | C1 counter | SS | Is clustering a monotone computation that can be run coordination-free under the CALM theorem or as a mergeable summary, so that partial results from replicas can be merged? | Hellerstein & Alvaro 2019; Laddad 2022; Ketsman 2023 |
| 8 | C1 | CO | mergeable clustering summaries commutative associative merge of clusterings from different replicas | Hore 2009; Bechchi 2007 (no CRDT) |
| 9 | C1 counter | WS | "CRDT" "k-means" OR "DBSCAN" OR "hierarchical clustering" convergent replicated clustering state merge arXiv | none |
| 10 | C1 | SS | Mergeable summaries: data summaries whose merge operation is commutative and associative so that distributed or streaming copies give the same result | Agarwal, Cormode, Huang 2012/13 |
| 11 | C1/C6 counter | SS | Generic entity resolution with match and merge functions that are idempotent, commutative and associative so that the result does not depend on the order in which records are processed | Benjelloun et al. 2009; Punter 2010; D-Swoosh 2007 |
| 12-13 | C1, C6 | SG | two natural-language versions of C1 and C6 | ACCESS_DENIED |
| 14 | C2 | SS | How can a user's must-link or cannot-link constraint be retracted or undone in interactive constrained clustering so the result equals the clustering obtained without it? | Randel 2021; Beauchamp 2025; Davidson 2007 |
| 15 | C2 | SS | Constrained clustering with constraint deletion: dynamic sets of pairwise constraints where constraints can be added and removed over time | Davidson 2007; CE-Stream 2013; Yi 2015 |
| 16 | C2 counter | SS | Machine unlearning for clustering: exact deletion of data points so that the result is identical to re-running k-means or hierarchical clustering without them | Kaplan 2026; Ginart 2019; Gupta 2025 |
| 17 | C2 | CO | undo or revoke earlier user feedback in interactive clustering, pairwise constraints removed after being given | Bae 2020 survey; Cohn 2003; Balcan & Blum 2008 |
| 18 | C2 | SS | Retroactive data structures that allow inserting or deleting an operation in the past so the present state is as if it had never been performed | Demaine 2007; Henzinger & Wu 2021 |
| 19 | C2 counter | SS | Detecting and removing erroneous or contradictory pairwise constraints given by non-expert users in interactive constrained clustering year:2020-2026 | Soenen 2020; Randel 2021; Yang & Pasquier 2024 |
| 20 | C2 | SS | Entity resolution with evolving rules: incrementally updating the resolution result when match rules are added, removed or changed so that it equals re-running from scratch | Whang & Garcia-Molina 2010, 2014; Saeedi 2020 |
| 21 | C2 | SS | Entity resolution with negative rules or cannot-link constraints and user feedback, including unmerging a wrongly merged entity | Whang 2009; Wang 2015; Kobren 2019 |
| 22 | C3 | SS | Reusing human feedback labels or pairwise constraints after the embedding model or feature extractor is upgraded, without re-annotating | BCT 2020; CoReS 2023 (embeddings only) |
| 23 | C3 | SS | Transferring must-link and cannot-link constraints between different feature representations or views of the same objects in multi-view constrained clustering | Eaton 2010/2014; Lu & Peng; Qian 2013 |
| 24 | C3 | CO | face recognition model upgrade: preserving existing identity clusters and user labels when embeddings change, backward-compatible face embeddings | BCT 2020; UniBCT 2022; FCT 2021 |
| 25 | C3 counter | WS | patent face recognition model version update migrate existing face clusters and user-confirmed labels to new embeddings re-cluster preserve user assignments | US12189738 (authentication) [snip]; US11423694 [snip]; none keeps labels |
| 26 | C4 | SS | Does average-linkage hierarchical clustering cut at a similarity threshold decompose exactly into the connected components of the threshold graph, so each component can be clustered independently? | Cohen-Addad 2018; Dhulipala 2021 (no direct statement) |
| 27 | C4 | SS | Hierarchical agglomerative clustering of a sparse similarity graph with missing edges treated as zero weight, exact speed-up by processing connected components separately | **Maus & Borin 2026**; Dhulipala 2021; Sumengen 2021 |
| 28 | C4 counter | SS | Single-linkage clusters at a threshold are the connected components of the threshold graph and can be read off the minimum spanning tree | Gower & Ross 1969; Lehert 1992; Lumley 2010 |
| 29 | C4 | WS | exact hierarchical agglomerative clustering average linkage distance threshold only pairs within threshold needed connected components of threshold graph independent subproblems | Dhulipala 2021; scikit-learn docs; none states it |
| 30 | C4 | CO | average linkage agglomerative clustering with distance threshold never merges clusters in different connected components of the threshold graph; sparse neighbor graph exact result | Maus & Borin 2026; Dhulipala 2021; Sieranoja 2025 |
| 31 | C6 | SS | Order-independent incremental clustering algorithm that enforces hard must-link and cannot-link constraints and gives the same result for any insertion order | Bandyopadhyay & Murty 2016; Rutayisire 2011; Davidson 2007 |
| 32 | C6 | SS | Incremental density-based clustering with instance-level must-link and cannot-link constraints on data streams, equivalence to batch result | Lasek & Gryz 2019; Halkidi 2012; C-DBSCAN |
| 33 | C6 | CO | order independent incremental constrained clustering insertion order invariance instance-level constraints | Beauchamp 2023; Davidson 2009; Wagstaff 2000 |
| 34 | C6 counter | SS | Incremental hierarchical clustering with user-specified must-link and cannot-link constraints, result independent of insertion order year:2019-2026 | Monath 2019 (Grinch); CCE-Stream 2023 |
| 35 | D1 | SS | Local-first machine learning on personal devices: synchronising learned or derived state such as embeddings, clusters or indexes between a user's devices without a server year:2024-2026 | Zerhoudi 2026; Alpasan 2026 (no clustering) |
| 36 | D1 | SS | Incremental face clustering with user feedback (merge, split, must-link, cannot-link) for personal photo collections year:2024-2026 | Filonenko 2025; Beauchamp 2025; Blase 2026 |
| 37 | D1 | CO | people album face grouping synchronisation across devices personal photo library user corrections consistency (year_min 2023) | nothing relevant |
| 38 | D1 | WS | arXiv 2026 incremental face clustering personal photo library on-device user corrections merge split order-independent | patents only [snip]; FaceCluster |
| 39 | D1/C6 | SS | Interactive or semi-supervised face clustering with pairwise constraints from user feedback in personal photo albums, corrections kept when new photos are added year:2018-2023 | Singh & Hang 2021; Hu 2018; Shi 2018 |
| 40 | D1/C6 | CO | face clustering human feedback must-link cannot-link constraints persist after re-clustering new photos incremental (year_min 2018) | Somandepalli 2019; Baumann 2022; Shi 2018 |

C5 web searches (WS), verbatim: (41) Apple Photos People album iCloud Photos "across your devices" merge people sync support.apple.com; (42) Google Photos support face groups merge people "face group" label sync across devices support.google.com photos; (43) PhotoPrism docs faces people recognition user guide merge faces clusters "People" docs.photoprism.app; (44) digiKam documentation face management people tags confirm unconfirmed faces recognition training rebuild docs.digikam.org; (45) Synology Photos People face recognition merge people remove face help kb.synology.com Synology Photos "People"; (46) Synology Photos "Merge people" "cannot be undone" People album help article; (47) Ente Photos face recognition "unnamed" groupings sync across devices corrections merge undo help.
Total: 45 successful searches (SS 25, CO 8, WS 12), 2 refused (SG); about 23 page fetches and 7 SciSpace record fetches.

## 2. Per-component findings: closest works and what differs

**C1. Partly known.**
1. Baquero & Brito, *Cache Merging as a Convergent Replicated State for Multi-Agent Latent Reasoning*, arXiv 2607.01308, 1 Jul 2026. https://scispace.com/papers/cache-merging-as-a-convergent-replicated-state-for-multi-dadfwjqm2cr4 [abs, full]. "the durable object is a set of content-addressed latent fragments merged by set union, a state-based CvRDT, and CanonicalMerge is its deterministic render"; output "byte-identical under any input permutation". Same pattern (state = a set, output = deterministic function of the set); different artefact (LLM caches).
2. Gillespie, *CRDTs for Neural Network Model Merging*, 2026 (arXiv 2605.19373). https://scispace.com/papers/conflict-free-replicated-data-types-for-neural-network-model-xxo7e4qfau8w [abs]. OR-Set layer plus deterministic merge for ML state (known from round 4; now two 2026 instances).
3. Saeedi, Peukert, Rahm, *Incremental Multi-source Entity Resolution for Knowledge Graph Completion*, ESWC 2020. https://scispace.com/papers/incremental-multi-source-entity-resolution-for-knowledge-ep92qe2yog [abs]. Reports results "independent from the order in which new entities are added" (empirical). No user corrections, no replicas.
Also: Bandyopadhyay & Murty, ICPR 2016 (order-independent incremental clustering) https://scispace.com/papers/axioms-to-characterize-efficient-incremental-clustering-260du0ugdt [abs]; Laddad et al. PVLDB 2022 ("Keep CALM and CRDT On": CRDT guarantees cover updates, not observations of state; a deterministic query over a replicated set is the textbook fit).
Industry route: patents reconcile diverging face groups by mapping or by sending results to a server (Apple 2017; Chen 2018-19) [snip]; Ente maintainers plan to "sync the information on the indexed images" (see C5).
**Differs:** none of these is a clustering of items under user constraints evaluated across replicas. The paper itself says any recompute-from-sets method has the property; claim the application and the measurement only.

**C2. Known as a principle; clustering-specific statement not found.**
1. Kaplan, Kohen, Mansour, *Machine Unlearning as Private Retroactive Algorithms*, 2026 (preprint). https://scispace.com/papers/machine-unlearning-as-private-retroactive-algorithms-7042idvq6dv5 [abs]. "the unlearning algorithm should produce an outcome that would have been obtained had the deleted point never been included"; constructions for clustering.
2. Ginart, Guan, Valiant, *Making AI Forget You*, NeurIPS 2019 https://scispace.com/papers/making-ai-forget-you-data-deletion-in-machine-learning-3u0l0yv2gq [abs]; Gupta et al. 2025 (exact k-means++ unlearning, ARCANE) https://scispace.com/papers/integrating-k-means-with-arcane-a-scalable-framework-for-l25yyx5tq1dg [abs]; Demaine, Iacono, Langerman, *Retroactive data structures*, ACM TALG 2007 https://scispace.com/papers/retroactive-data-structures-1edav83d7a [abs] (delete an operation from the past).
3. Whang & Garcia-Molina, *Entity resolution with evolving rules*, PVLDB 2010 https://scispace.com/papers/entity-resolution-with-evolving-rules-3mk1n0qzt1 [abs]; Wang, Gao, Christen 2016 (incrementally repairing wrong matches and non-matches with provenance) https://scispace.com/papers/a-clustering-based-framework-for-incrementally-repairing-3vqot4zu8r [abs]; Wang et al. 2015 (repairs driven by must-link and cannot-link constraints) [abs].
Detection: Randel 2021, Soenen 2020, Beauchamp 2025 (conflict management: relax the least adequate constraint) https://scispace.com/papers/clustering-sous-contraintes-integration-incrementale-et-fbq3vu4qtupd [abs].
**Differs:** these delete data points or change rules, not a user's pair constraint inside a face clusterer, and none compares with a frozen-label store. The "equals never having made it" criterion is the standard definition of exact unlearning. The PDFs of Whang & Garcia-Molina could not be read, so "equals re-run" is implied by the abstract, not confirmed.

**C3. Partly known; retention measurement not found.**
1. PhotoPrism user guide (`faces migrate`): "It re-embeds every face, keeps the people you have already identified, and records the new model as the one in use." https://docs.photoprism.app/user-guide/ai/face-recognition/ [page]. Also "a face that you assigned manually keeps its assignment". A shipped product keeping identity labels through a model change; no pairwise constraints, no measurement.
2. Eaton, desJardins, Jacob, *Multi-view constrained clustering with an incomplete mapping between views*, KAIS 2014 (CIKM 2010) https://scispace.com/papers/multi-view-constrained-clustering-with-an-incomplete-mapping-2iejgdyo0a [abs]. Propagates pairwise constraints "to those instances that can be mapped to the other views" and reports gains over other ways of "transferring constraints". Here the mapping is complete (same faces), which is the easy case.
3. Shen et al., BCT, CVPR 2020 and successors [abs]: embeddings, not user feedback.
**Differs:** nobody measured how much of a correction gain survives a recogniser change. Immich says only that a model change needs Face Detection re-run in All mode and nothing about existing people (fetch-tool paraphrase) [page].

**C4. Known.**
1. Maus & Borin, *Scalable Exact Hierarchical Agglomerative Clustering via Sparse Geographic Distance Graphs*, arXiv 2604.11656 (v1 13 Apr 2026, v2 3 Nov 2026; no venue). https://arxiv.org/abs/2604.11656 [page]. "Connected components of this graph define independent subproblems, and we prove that the resulting assignments are exact for all standard linkage methods at any cut height h <= h_max." The page does not name the linkages.
2. Gower & Ross, JRSS-C 1969 https://scispace.com/papers/minimum-spanning-trees-and-single-linkage-cluster-analysis-3su8vrd2u7 [abs]; Lehert 1992 (single linkage at a predetermined threshold gives connected components) https://scispace.com/papers/classification-en-composantes-connexes-cas-particulier-de-l-27fcvf6biy [abs].
3. Davidson & Ravi, DMKD 2009: constraints improve the efficiency of agglomerative clustering [abs].
**Differs:** their setting is spatial distance graphs; ours is centroid similarities with a cannot-link veto, which only forbids merges and cannot cross components. The paper's one-line proof ("an average cannot exceed its largest term") is the same argument. This is an elementary lemma with a citation, not a contribution.

**C6. Partly known.** Closest three:
1. C-DBSCAN (Ruiz, Spiliopoulou, Menasalvas) https://scispace.com/papers/c-dbscan-density-based-clustering-with-constraints-24zy4syuzd and ic-DBSCAN (Lasek & Gryz 2019) [abs]: must-link/cannot-link in density-based clustering; batch, no order-independence statement.
2. Halkidi, Spiliopoulou, Pavlou, PAKDD 2012 https://scispace.com/papers/a-semi-supervised-incremental-clustering-algorithm-for-4g3btc55g1 [abs]: incremental, a "constraint stream" used "as data items are forgotten or new items arrive", cost-based (soft) enforcement.
3. Bandyopadhyay & Murty 2016 (order-independent incremental, no constraints) and Monath, Kobren, Krishnamurthy, KDD 2019 (Grinch; "independent of data arrival order" under separability) https://scispace.com/papers/scalable-hierarchical-clustering-with-tree-grafting-9xtvg1usy6 [abs].
Neighbours: Kobren, Monath, McCallum, AKBC 2019 (user feedback that survives re-resolution as new data arrives, by treating feedback as input items) https://scispace.com/papers/integrating-user-feedback-under-identity-uncertainty-in-cnshcu3gj9 [abs, full]; Rutayisire et al. 2011 (must-link/cannot-link makes COP-KMeans "too much sensitive to assignment order") [abs]; CE-Stream 2013 (constraints with activation, fading, outdating) [abs]; Davidson, Ravi, Ester 2007 [abs].
**Differs:** no abstract states hard constraints, incremental insertion and provable order/batch independence together. Kobren et al. is the closest to the paper's Problem 2 ("lost corrections") and is not cited.

## 3. C5. What shipping apps document

| App | Documented (exact words; URL) | Not documented |
|---|---|---|
| Apple Photos | "When you use iCloud Photos, People & Pets is kept up to date on all your devices." and "If you find more than one group of photos that have the same person or pet, you can merge them." https://support.apple.com/en-is/guide/photos/phtad9d981ab [page]. Apple ML Research, 28 Jul 2021: "a novel agglomerative clustering algorithm that enables an efficient incremental update of existing clusters"; first pass "fairly conservative because when it joins two instances, they are permanently associated"; processing "entirely locally". https://machinelearning.apple.com/research/recognizing-people-photos [page] | Undo, reconciliation of differing devices, order dependence, model updates. Community thread (users only, no Apple staff, 22 Apr 2025): 5 named people on a Mac, 4 on iPhone/iPad; methods "not documented". https://discussions.apple.com/thread/256045157 [page] |
| Google Photos | "Once you merge face groups, this action can't be undone." "Face labels are private to each account and aren't shared across accounts." https://support.google.com/photos/answer/6128838?hl=en [page] | Cross-device sync, conflicts |
| Ente | "Once indexed on one device, the indexes sync to other devices"; "If incorrectly grouped faces were merged, you can undo the merge."; "Face grouping management (editing clusters, removing incorrect faces) must be done on the mobile app." https://ente.com/help/photos/features/search-and-discovery/face-recognition [page]. Issue thread (13 Oct 2023): a user got different people on Mac and Windows; collaborator: "once we release this (hopefully very soon) we will also sync the information on the indexed images to other devices." https://github.com/ente-io/ente/discussions/549 [page] | Conflict handling, model updates. **Round 4's quotes "All corrections sync across devices" and "Unnamed groupings don't sync" were not reproduced in 4 fetches of this page or its FAQ page; do not quote them until re-read in a browser.** |
| Immich | "Re-running facial recognition on all assets afterwards does behave like DBSCAN, however."; "since it preserves the clusters (people) generated from the previous round."; "the larger the set of faces in the queue, the better the results will be." https://docs.immich.app/features/facial-recognition [page]. Issue #24119 (23 Nov 2025): a user could not separate two merged children without resetting other data. https://github.com/immich-app/immich/discussions/24119 [page] | Undo of a merge, sync, effect of a model change on existing people |
| PhotoPrism | `faces migrate` sentence (C3). `faces conflicts`: "list face clusters that hold the same face but are assigned to different people." Undo only by restoring a backup. https://docs.photoprism.app/user-guide/ai/face-recognition/ [page] | Merge procedure, cross-device divergence (the "conflict" is inside one instance) |
| digiKam | "digiKam does not keep a record of rejected faces." https://docs.digikam.org/en/left_sidebar/people_view.html [page]. Bug 298160 "Add undo functionality to face tagging operations", opened 2012-04-15, still REPORTED, latest comment 2026-07-28. https://bugs.kde.org/show_bug.cgi?id=298160 [page] | Sync, conflicts |
| Nextcloud Recognize | README: "Recognizes faces and groups photos by faces that appear in them (GUI in the memories app)". https://github.com/nextcloud/recognize [page] | Algorithm, sync, undo, conflicts (wiki not read) |
| Synology Photos | Merge "cannot be undone" [snip only]. The page https://kb.synology.com/en-id/DSM/help/SynologyPhotos/managing_albums?version=7 returned navigation text only | Unverified |

Answer: no official page I could open documents what happens when two devices' groupings diverge. The only acknowledgement is Ente #549 (and anecdotal Apple posts); PhotoPrism's `faces conflicts` is a different, single-instance notion. The paper's "we did not find" stands for documentation. Immich's own admission of batch dependence ("the larger the set of faces in the queue...") is usable as evidence for Problem 1.

## 4. D1. 2025-2026 searches

- **CRDT + clustering:** nothing (Q1, 3, 4, 5, 9). Nearest 2026 items are not clustering: Gillespie (model merging), Baquero & Brito (KV cache), CodeCRDT 2025, "Composing CRDTs Convergent by Construction" (PACMPL 2026) [abs].
- **Local-first + ML:** Zerhoudi et al. 2026 (local-first IR: indexes and models on device); Alpasan 2026 (P2P sync with CRDT conflict resolution) [abs]. Neither concerns convergence of derived clusters.
- **Face clustering + user feedback + incremental:** FaceCluster (Filonenko 2025, already cited), Beauchamp thesis 2025, FALCON (Blase 2026), Geng et al. AAAI 2025, PAL-Bench 2026 [abs]. None keeps hard corrections order-independently.
- **Photo library + people + sync:** no scholarly paper after 2019; only patents [snip], product docs and issue threads (section 3).

## 5. D2. What the contribution honestly reduces to

If every component is Known or Partly known, the paper is an **application-and-measurement paper**: (a) an engineering assembly (single-linkage core, attach step, centroid merge, constrained maximum-spanning forest) with a short order-independence argument; (b) a controlled, identity-disjoint, equal-tuning measurement of what set semantics buys a personal photo library, with counter-results (wrong corrections hurt beyond about one in twenty; profile faces; about half of a correction's value is tied to the recogniser); (c) fair baselines (constrained average linkage, frozen-label rule).

**Three sentences for the related-work or novelty statement:**
1. "Order-independent incremental clustering, convergent replicated state computed from a set of updates, deletion that equals retraining without the item, transfer of pairwise constraints between feature spaces, and splitting a threshold-cut agglomeration into connected components are each established [Bandyopadhyay & Murty; Shapiro et al.; Ginart et al.; Eaton et al.; Gower & Ross; Maus & Borin], and we claim none of them as new."
2. "In the sources we searched (SciSpace, Consensus, web search and vendor documentation, mostly at abstract or help-page level, up to 10 November 2026), we did not find a clusterer that is at once incremental, order-independent and bound by hard user must-link and cannot-link corrections, nor a measurement of whether such corrections converge across devices, can be retracted exactly after new photos arrive, or keep their value after the recogniser changes."
3. "Our contribution is therefore an assembly of these ideas for personal photo libraries and a protocol-controlled simulation that measures their consequences, including the regimes in which corrections hurt."

**One abstract sentence:** "We assemble known ideas into a face clusterer whose output is a function of the set of faces and corrections, and measure in simulation what that buys: devices that agree, corrections that survive new photos, exact retraction, and about half of a correction's value across a recogniser change."

**Claims to weaken (in order):**
1. Intro: "Our contribution is a clusterer that combines them so that both problems are solved at once" becomes "assembles known parts".
2. Intro bullet 1 and the "Exact read-time step" paragraph: present as an application of a known decomposition (cite Gower & Ross 1969, Maus & Borin 2026); keep the timings as engineering.
3. Abstract and bullet 3: the device-agreement and retraction results hold for any method that recomputes from the sets. The abstract contrasts only with the frozen rule; add "as does constrained average linkage (agreement 100%; retraction not run)".
4. Related Work, last sentence: widen the bounded statement to name the families found here: entity-resolution feedback and repair (Kobren 2019; Whang & Garcia-Molina 2010/2014; Wang 2016), exact unlearning (Ginart 2019), PhotoPrism's identity-preserving migration.
5. Intro first paragraph: "Cloud services cluster... on their servers" omits Apple Photos and Ente, which cluster on the device and sync People or indexes across devices. Name them so the local-first framing is not read as unaddressed in products.

## 6. Changes against round 4

- C4 overturned: the "not found as a named result" is now a found result (Maus & Borin 2026).
- C2: "not found" becomes "known principle" (unlearning, retroactive structures, ER rule evolution); clustering-specific statement still not found.
- C1: "not found" becomes "partly known" (Baquero & Brito 2026; ER order-independence; Ente #549).
- C3: PhotoPrism documents identity-preserving migration; retention measurement still not found.
- New family not in round 4: entity resolution (Kobren 2019, Whang & Garcia-Molina, Wang 2016, Saeedi 2020).
- Apple's own wording is now verified from an opened page; Ente's two round-4 sentences are not reproducible.

## 7. Limitations of this scan

Abstract-level for nearly all scholarly sources; no forward or backward citation chasing (the most likely way a hit was missed); SciSpace capped at 6-8 results and Consensus at 6 per query; no direct query of Google Scholar, ACM, IEEE or DBLP; Scholar Gateway unavailable. Fetched help pages pass through a summarising tool that may omit sentences (this is the likely reason for the Ente discrepancy). The Swoosh PDF refused the connection and the 2010 evolving-rules PDF was unreadable, so their order-independence and "equals re-run" content is not confirmed; Swoosh's abstract does not list its four properties. Patents and the Synology claim are search-snippet level. The two 2026 preprints (Maus & Borin, Baquero & Brito) are not known to be peer-reviewed. A "not found" can be overturned by a paper this scan did not reach.

## 8. AI disclosure

AI-assisted search, screening and synthesis (Claude, via Claude Code, using the academic-research-skills deep-research workflow). The author must verify every source and add DOIs before citing it.
