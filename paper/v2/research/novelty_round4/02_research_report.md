# Novelty search, round 4: research report (deep-research, full mode, integrative scan)

Date: 2026-11-10. Same method and limits as rounds 1–3: SciSpace, Consensus and web search; **abstracts only**; one reviewer;
"not found" is bounded to the queries listed below. Scholar Gateway returned ACCESS_DENIED again; Consensus rate-limited
one query. The author confirmed the RQ and method ("accept both"). The review-form note was answered earlier (skip).

## RQ (confirmed)
Which extensions of an order-invariant, incremental face clusterer that keeps user corrections are **not found in prior work**,
can be built and tested on a laptop CPU in about a week with the existing identity-disjoint protocol (exp14/15/19), and strengthen
the paper's thesis about corrections and order?

## Queries (22; all logged)
SciSpace: (1) convergence of a derived clustering across replicas; (2) CRDT / coordination-free distributed clustering;
(3) noisy or contradictory must-link / cannot-link constraints; (4) detecting wrong constraints, coherence, utility;
(5) incremental / dynamic single-linkage or MST under insertions with constraints; (6) keeping annotations when the embedding model is
upgraded; (7) syncing face clusters across devices with user edits; (8) explaining or suggesting wrong merges in personal photo
albums; (9) federated / decentralised face clustering across devices; (10) retracting or undoing user constraints;
(11) threshold-cut linkage decomposes into connected components; (12) local-first derived state converging across devices;
(13) exact distributed DBSCAN / single-linkage merging; (14) revoking feedback in interactive photo clustering.
Consensus: (15) reusing constraints after the embedding changes; (16) corrections persisting across re-clustering (rate-limited, not re-run).
Web: (17) Apple Photos People sync; (18) Immich merge/undo/recluster; (19) Ente face recognition docs (fetched in full);
(20) Apple support page (the fetched URL was the wrong page, so Apple's own wording is **unverified**). Counter-evidence queries:
(2), (3), (4), (5), (10), (13) were worded to find work that would make an idea *not* new.

## Findings by candidate and component

### N1. Convergence across devices (same set of photos and corrections, any order → same people)
| # | Component | Prior art found (abstract level) | Verdict |
|---|---|---|---|
| a | A replicated object is a deterministic function of the *set* of updates, so replicas converge without coordination | Shapiro et al. 2011 (CRDTs: "any two replicas that received the same set of updates reach the same state"); Kleppmann et al. 2019 (local-first software) | **Known principle** |
| b | A *computed* result (not just stored data) as such a function | Navalho, Duarte & Preguiça 2015 ("CRDTs that do computations"); Laddad et al. 2022 (CALM/CRDT queries); Gillespie 2026 (OR-Set wrapper makes model merging convergent) | **Known pattern** |
| c | Clustering that gives the same result as the centralised run when data is split across sites | Tran & Sattler 2013; Jin et al. 2015 (incremental distributed single linkage); distributed DBSCAN merges (RP-DBSCAN 2018 and others) | **Known** (for data, not for user corrections) |
| d | Syncing face groups across a user's devices | Patents (Apple 2017 "Face syncing", via a server; OPPO/Xiaomi-type mobile-server cluster comparison 2018–19). **Ente docs:** "All corrections sync across devices"; "Unnamed groupings don't sync", and each device "works them out on its own" | **Known as a product feature**; no convergence guarantee is stated |
| e | An *order-invariant face clusterer with user corrections* shown to converge across devices, compared with leader/frozen rules | — | **Not found in the searched sources.** It follows directly from our Proposition 1, so it is an implication, not a new mechanism |

### N2. Wrong corrections: detection and undo
| # | Component | Prior art found | Verdict |
|---|---|---|---|
| a | Hard constraints are fragile when some are wrong | Yoshida 2012 ("treating pairwise constraints as hard constraints is vulnerable to erroneous ones"); Ares et al. 2012; Yang & Pasquier 2024/2026 | **Known — our "wrong corrections are sticky" result is an instance of this** |
| b | Handling noisy constraints | Zhu, Loy & Gong 2016 ("imperfect oracles"); Soenen et al. 2020 (identify and correct noisy constraints); Gribel et al. 2021; Freund et al. 2008 | **Known** |
| c | Scoring individual constraints as likely wrong | Randel, Aloise & Blanchard 2019/2021; Davidson, Wagstaff & Basu 2006; Wagstaff et al. 2006 (coherence) | **Known** (a detector would not be new) |
| d | Interactive split/merge feedback, with local changes to limit "churn" | Balcan & Blum 2008; Awasthi, Balcan & Voevodski 2017; Coden et al. 2017; Wen et al. 2007 (merge/split of face groups, patent) | **Known** |
| e | Undo of a merge in a shipped app | **Ente** docs: "If incorrectly grouped faces were merged, you can undo the merge"; rejected suggestions are not shown again | **Known as a feature** |
| f | *Exact* undo as a property of a set-valued clusterer (remove the correction from the set; result is identical to never having made it, even after new photos) | Constraint retraction in CLP(FD) (1999) is the closest abstract found; nothing for clustering | **Not found in the searched sources** (a corollary of set semantics) |

### N3. A truly incremental read-time step
| # | Component | Prior art found | Verdict |
|---|---|---|---|
| a | Dynamic / incremental single-linkage via maintained MST | Eppstein 1995; Tseng, Dhulipala & Shun 2022 (batch-dynamic MSF); De Man et al. (arXiv, fully dynamic single linkage); Kontogianni et al. 2016 (incremental single link in image collections); Jin et al. 2015 | **Known** |
| b | Dynamic average linkage | Yu, Dhulipala & Łącki 2025 (DynHAC, approximate); Monath 2019 (Grinch) | **Known (approximate)** |
| c | Incremental constrained clustering | Davidson, Ravi & Ester 2007 (NP-hard in general; sufficient conditions); Halkidi et al. 2012; Lafabregue et al. 2022 | **Known** |
| d | Splitting a threshold-cut agglomeration into independent parts (connected components of the threshold graph) | Textbook for single linkage (Hubert 1974; Hartigan 1981 on single-link and connected components). **No abstract found that states it for the average-linkage centroid merge** | Elementary; **not found as a named result for this use** |

### G2 (carried over). Corrections surviving a recogniser upgrade
| Component | Prior art found | Verdict |
|---|---|---|
| Avoid re-embedding after a model upgrade | BCT (Shen et al. 2020), UniBCT 2022, LCE 2021, CoReS 2021/23, FastFill 2023, Wang et al. 2020 (cross-model compatibility for face identification) | **Known — about embeddings, not user corrections** |
| Keep the user's constraints when the embedding changes | Consensus query (15) returned only general constrained-clustering work | **Not found in the searched sources** |
| Ente | No statement about people or merges after a model update (docs do not say) | Unknown |

### SQ4 (open): other directions
Explaining groupings to the user: Lad & Parikh 2014 (attribute-based explanations for interactive clustering, including faces).
Automatic cannot-links from "two faces in one photo are different people": Lo Presti 2012, Zhang et al. 2013/14, Song & Leung 2006
(round 1). Active query selection: Xiong et al. 2013, COBRAS 2018, Beauchamp 2025. All **known**; none changes the ranking.

## Feasibility probes (read-only, run this session on the 8,290-face LFW library, EdgeFace-S, shipped thresholds, one thread)
1. **Where does the read time go?** With the merge disabled, `labels()` took 0.02 s; the centroid merge alone took 9.20 s
   (full read 10.59 s; the machine was busy with five reviewer agents, so absolute times are about 3× the unloaded 3.4 s of exp18;
   **the share is what matters: the merge is essentially all of it**).
2. **How big is the merge problem?** 3,856 clusters before the merge. At the merge threshold, the centroid-similarity graph has
   **3,822 connected components, the largest of size 2, and 3,788 singletons**. Running the same average-linkage step per
   component took **0.17 s** (plus 0.44 s for the dense similarity product), and gave an **identical partition (ARI 1.000000)**.
   So an *exact* decomposition of the read-time step looks roughly 15× faster here, to be re-measured unloaded.
3. **Can corrections be moved between recognisers?** The 420 non-look-alike library-conditions are face-aligned across the MBF and
   EdgeFace-S files (identical keys, boundaries and identity labels; 354,541 faces). Only the 30 look-alike libraries differ, because
   they are built from model-specific embeddings. So the experiment needs no new data.
4. **A bug found by the review, fixed:** Table II rows ended in `\` instead of `\\` and would not have compiled. Fixed in the paper file.
5. **Behaviour found by the review and reproduced here:** in the constrained path, a must-link between two *non-core* faces whose best
   attach targets lie in different clusters merges those two whole clusters (2 clusters without the must-link, 1 with it, in all 20 random
   orders). It is order-invariant but contradicts "non-core faces never link two clusters"; the paper now says so. How often it happens in exp19
   has not been counted.
6. **User effort, from the existing exp19 results (descriptive, not tested):** with the precise user, our session needs fewer corrections than
   the average-linkage-based ones (EdgeFace-S: 5.4 vs 6.6 on average; 207 vs 224 libraries needing at least one; MBF: 5.8 vs 6.8), at about the same final F1
   (0.9939 vs 0.9945). This is the "effort" outcome the devil's advocate asked for.

## Devil's-advocate checkpoint 2 (synthesis): PASS with conditions
1. **Cherry-picking check.** The counter-evidence searches did find prior art for the principles behind every candidate (CRDTs, noisy-constraint
   handling, dynamic clustering, backward-compatible embeddings) and for two *product features* (Ente: synced corrections, undo of merges).
   What was not found is the combination in a clusterer for personal photos, with the consequences measured. Claim exactly that.
2. **Is this just an obvious corollary?** For N1 and N3(d) and N2(f): yes, in the sense that each follows from one proposition. That is acceptable
   for a regional conference *if* the paper says so and the measurements are what is new. It would not satisfy a top-tier venue.
3. **Risk of no effect.** E4 may show that only part of the gain transfers across recognisers; report it either way. E2's alternatives
   have no standard merge rule, so the comparison must use a stated, fair rule (last-writer-wins on labels).
4. **Risk of harm.** Faster read must not change a single label; the exactness test is a gate, not a nice-to-have.
5. **Scope risk.** The paper is already about 6.5 pages and the author wants 6. Every addition must be paid for by cuts (pose negative
   result, Table III, future work, parts of related work).

## Ranked shortlist (value to the paper × novelty × effort; all CPU-only, all pre-declared)
| Rank | Experiment | What it adds | Novelty (honest) | Effort | Pre-declared test and success criterion |
|---|---|---|---|---|---|
| **1** | **E1. Exact, local read-time step** (decompose the centroid merge into threshold-graph components; blocked similarity so memory stays small; remove the 20,000-cluster guard) | Makes "incremental" true: read time 15× lower in the probe, on top of 0.15 s inserts. Also gives the missing **constrained-average-linkage timing** | Low (elementary); **exactness proof + measurement** | 1–1.5 days | Identical labels on all 480 libraries and the 8,290-face run; unconstrained **and** constrained path; read time on 8,290 and 13,000 faces; constrained average linkage timed on the same data. **Pass:** zero label differences, at least 5× faster |
| **2** | **E2. Replica convergence** (2–3 devices, different arrival orders and batches, corrections made on each device, random syncs) | Gives order invariance a concrete user need (family devices), answering the repeated review question "why does order matter?" | Application; **not found in the searched sources** for faces | 1–1.5 days | Share of runs in which all replicas end with identical people, minimum ARI, F1 spread, and share of both devices' corrections kept, for: ours (set semantics), First-Leader, Immich-style frozen (labels shipped last-writer-wins), constrained average linkage. **Pass:** ours 100% identical; at least one alternative measurably diverges; otherwise report that no gap was found |
| **3** | **E3. Exact undo, and recovering from wrong corrections** | Turns the negative result ("wrong corrections are sticky") into a constructive one: retraction restores the never-made result exactly, even after new photos; frozen rules cannot | Low–moderate; corollary | 0.5–1 day | (a) property test on all libraries: retract a wrong correction after new photos → ARI 1.0 against the never-made run; same test for frozen (expected < 1). (b) optional: AUC of a similarity-based "suspicious correction" score, reported even if poor (it may be below 0.5, because look-alike merges are the most similar pairs) |
| **4** | **E4. Corrections across a recogniser upgrade** (MBF→EdgeFace-S and back, on the 210 aligned test libraries) | "Your fixes survive a model change"; a real product concern | Moderate; **not found in the searched sources** | 0.5 day (about 20 min of compute) | Retention = (transferred gain) / (native gain), with bootstrap CI, held share, and a no-harm check. **Pass:** no loss against no corrections; retention reported whatever it is |

| 5 (optional) | **E5. User effort instead of "held"** | Corrections needed to reach a target F1 (e.g. 0.99), per method and user, from the F1-after-each-fix curve; plus an error-rate sweep (0, 2, 5, 10% wrong) with a break-even rate | Low (a better outcome measure) | 0.5 day + about 1.5 h compute | Report median fixes-to-target with bootstrap CI; break-even error rate at which fixes stop paying off for each method |

**Also from the round-3 review (not novelty, but needed before submission):** time constrained average linkage directly (the devil's advocate measured the repo's pure-NumPy
version at about 32 s for 3,316 faces, so the 16.7 s used in the paper is plain average linkage, not the method compared); decide whether a must-link between non-core faces
may bridge clusters; key corrections by photo and face box, not by position.

**Not recommended now:** G1 (calibrated thresholds across recognisers; large effort, uncertain gain), G3 (core step is prior art), G5 (video bridges; marginal F1 gain),
a fully dynamic constrained MSF (heavy; dynamic-clustering prior art; E1 captures the practical benefit).

## What this does to the paper
- **One theme:** *set semantics*. Proposition 1 gets a **Corollary** listing what follows when the output is a pure function of the set of faces and
  corrections: (i) replicas converge, (ii) a retracted correction leaves no trace, (iii) corrections do not depend on the recogniser,
  (iv) the read-time step can be computed exactly and locally. Each is then *measured* (E1–E4).
- **Honest framing:** "an application of CRDT-style design to face clustering, with measured consequences; not found in the searched sources". Not "a new algorithm".
- **Title direction (for discussion):** from "Order-Invariant Incremental Clustering" toward a title that names corrections that are convergent and undoable.
- **Space:** needs about 0.6 pages. Pay with: pose negative result (to 3 lines), Table III (to a sentence), Future work, and a shorter Sec. II.
- **Product honesty remains:** the app still has no correction UI; E2–E4 would be simulations of what the app would do.

## Limitations of this scan
Abstract-level reading; one reviewer; search-engine coverage; Apple's own wording unverified (the fetched URL was wrong); Ente documentation read but not tested;
two of the fourteen SciSpace result lists were dominated by distributed-systems material unrelated to clustering. A "not found" can be overturned by a paper we did not see.

## Sources (found through the search tools; abstract level; titles verified to exist)
- Shapiro, Preguiça, Baquero, Zawirski. Conflict-free replicated data types. SSS 2011. https://scispace.com/papers/conflict-free-replicated-data-types-3qqitklmux
- Navalho, Duarte, Preguiça. A study of CRDTs that do computations. EuroSys 2015 workshop. https://scispace.com/papers/a-study-of-crdts-that-do-computations-10p54mj25v
- Laddad, Power, Milano. Keep CALM and CRDT on. PVLDB 2022. https://scispace.com/papers/keep-calm-and-crdt-on-3k1c8426
- Kleppmann, Wiggins, van Hardenberg. Local-first software. Onward! 2019. https://scispace.com/papers/local-first-software-you-own-your-data-in-spite-of-the-cloud-30qpsjzci7
- Gillespie. CRDTs for neural network model merging (2026, venue not confirmed). https://scispace.com/papers/conflict-free-replicated-data-types-for-neural-network-model-xxo7e4qfau8w
- Tran & Sattler. Communication-efficient exact clustering of distributed streaming data. ICCSA 2013. https://scispace.com/papers/communication-efficient-exact-clustering-of-distributed-3ns6dc1ll5
- Jin, Chen, Hendrix. Incremental, distributed single-linkage hierarchical clustering using MapReduce. HPCC 2015. https://scispace.com/papers/incremental-distributed-single-linkage-hierarchical-381sgerkxo
- Song & Lee. RP-DBSCAN. SIGMOD 2018. https://scispace.com/papers/rp-dbscan-a-superfast-parallel-dbscan-algorithm-based-on-4n58ub26k7
- Thomson, Circlaeys, Bombach. Face syncing in distributed computing environment (patent, 2017). https://scispace.com/papers/face-syncing-in-distributed-computing-environment-4anrg7r2lt
- Ente help: face recognition (fetched 2026-11-10). https://ente.com/help/photos/features/search-and-discovery/face-recognition
- Immich docs: facial recognition. https://docs.immich.app/features/facial-recognition ; feature request #24119. https://github.com/immich-app/immich/discussions/24119
- Zhu, Loy, Gong. Constrained clustering with imperfect oracles. IEEE TNNLS 2016. https://scispace.com/papers/constrained-clustering-with-imperfect-oracles-222fum1izy
- Soenen, Dumancic, Van Craenendonck. Tackling noise in active semi-supervised clustering. ECML-PKDD 2020. https://scispace.com/papers/tackling-noise-in-active-semi-supervised-clustering-3go1r4mmtf
- Randel, Aloise, Blanchard. A Lagrangian-based score for assessing the quality of pairwise constraints. DMKD 2021. https://scispace.com/papers/a-lagrangian-based-score-for-assessing-the-quality-of-dbvf7crghk
- Ares, Parapar, Barreiro. Constrained clustering with erroneous constraints. IP&M 2012. https://scispace.com/papers/an-experimental-study-of-constrained-clustering-4e89a0ek32
- Yoshida. Influence of erroneous pairwise constraints in semi-supervised clustering. AMT 2012. https://scispace.com/papers/influence-of-erroneous-pairwise-constraints-in-semi-51r73u40v2
- Davidson, Wagstaff, Basu. Measuring constraint-set utility. PKDD 2006. https://scispace.com/papers/measuring-constraint-set-utility-for-partitional-clustering-29djulz3iu
- Wagstaff, Basu, Davidson. When is constrained clustering beneficial, and why? AAAI 2006. https://scispace.com/papers/when-is-constrained-clustering-beneficial-and-why-5edn9m5aab
- Balcan & Blum. Clustering with interactive feedback. ALT 2008. https://scispace.com/papers/clustering-with-interactive-feedback-hwr4ddz32d
- Awasthi, Balcan, Voevodski. Local algorithms for interactive clustering. JMLR 2017. https://scispace.com/papers/local-algorithms-for-interactive-clustering-3mnncx71lb
- Wen, Xiao, Yang. Interactive photo annotation based on face clustering (patent, 2007). https://scispace.com/papers/interactive-photo-annotation-based-on-face-clustering-1zk879m6zl
- Tseng, Dhulipala, Shun. Parallel batch-dynamic minimum spanning forest and dynamic agglomerative graph clustering. SPAA 2022. https://scispace.com/papers/parallel-batch-dynamic-minimum-spanning-forest-and-the-299ty8um
- Yu, Dhulipala, Łącki. DynHAC (2025). https://scispace.com/papers/dynhac-fully-dynamic-approximate-hierarchical-agglomerative-1gjujty3tu7a
- Kontogianni, Mathias, Leibe. Incremental object discovery in time-varying image collections. CVPR 2016. https://scispace.com/papers/incremental-object-discovery-in-time-varying-image-2n1tqlve39
- Eppstein. Dynamic Euclidean minimum spanning trees and extrema of binary functions. DCG 1995. https://scispace.com/papers/dynamic-euclidean-minimum-spanning-trees-and-extrema-of-583u571srv
- Shen, Xiong, Xia, Soatto. Towards backward-compatible representation learning. CVPR 2020. https://scispace.com/papers/towards-backward-compatible-representation-learning-1qx8493tbq
- Wang et al. Unified representation learning for cross model compatibility (arXiv 2020). https://scispace.com/papers/unified-representation-learning-for-cross-model-3ljjarl6qj
- Lad & Parikh. Interactively guiding semi-supervised clustering via attribute-based explanations. ECCV 2014. https://scispace.com/papers/interactively-guiding-semi-supervised-clustering-via-3jgne08o22

**AI disclosure:** AI-assisted search, screening and synthesis (Claude, academic-research-skills deep-research). Abstract-level reading only.
The author should verify every source (and add DOIs) before citing it in the paper.
