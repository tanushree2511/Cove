## Domain Review Report (Peer Reviewer 2), Round 4

Manuscript: `paper/v2/cove_paper.tex` (commit ab09dbe, not compiled). Simulated reviewer, simplified run (no sprint contract). I read only the card, the manuscript, bibliography, round-3 editorial decision and my own round-3 report, the novelty report, `stable_cluster.py` and the `c_avg` baseline in `evaluation/exp19_correction_baselines.py`. I did not read other round-4 seats. I ran no evaluation scripts.

### Reviewer Identity
Constrained-clustering and face-clustering researcher with a distributed-systems background.

### Overall Recommendation
**Minor Revision.** The experiments are honest and the sizing is now right. The domain problems are in wording: one over-general Corollary, preconditions it hides, and a gap statement that omits shipped product features.

### Confidence Score
4. Strong on clustering and constraints, moderate on CRDT theory. Literature checks are abstract level. I could not run code.

### Calibration Status
`NOT_CALIBRATED`

### Criterion-Bound Judgements
| Dimension | Source | Judgement | Anchor | Rationale | Limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Corollary correctness | Reviewer-2 remit, Step 3b | PARTLY_MEETS | text: Sec. III Corollary | (i),(ii) hold for order-insensitive deterministic functions only; universal sentence is false | informal statement | yes |
| Novelty statement | Step 4c | PARTLY_MEETS | text: Sec. II gap sentence | hedged, but omits shipped features and the query log | abstract-level search | yes |
| Exact read step | Step 3a | MEETS | text: Sec. III "an average cannot exceed its largest term" | correct, elementary, not new | test power weak | no |
| Baseline naming | Step 3c | MEETS (rewording) | text: Sec. IV "our implementation, after" | faithful instance, not D&R itself | timing is implementation | partly |
| Literature | Step 1 | PARTLY_MEETS | absence: noisy-constraint detection, exact deletion | round-3 gaps mostly closed | | no |

### Summary Assessment
The paper adds a read-time step, three consequence experiments and an error-rate sweep to a clusterer whose output is a function of the set of faces and corrections. The new Related Work is accurate at abstract level and the three new bibliography entries are real. Framing as an application of replicated-set design to face grouping, with measured consequences, is honest. The Corollary is the weak point. It is trivially true for set-functions, not new, and over-stated: its second sentence is contradicted by the paper's own Table I. Preconditions for convergence (bit-identical embeddings, stable face keys, eventual consistency) are not stated, and the abstract says devices "exchange photos" while the experiment exchanges faces. The exact read step is correct but elementary, and the gap sentence omits that shipping apps already offer undo of merges. None of this touches the measured results. All fixes are text, plus one limitation paragraph.

### Strengths
**S1 Exact read step with a gate.** The argument is correct (see Detailed Comments) and the paper reports the cost honestly (2.3x with corrections, below target). Evidence Anchor: text: Sec. V-E "a smaller gain (2.3$\times$, below the 5$\times$ we had set as the target)"

**S2 The property is shown not to be unique.** Constrained average linkage also converges; the paper says so. Evidence Anchor: text: Sec. V-D "The property is therefore not unique to our clusterer; it is what a plain edit log lacks."

**S3 Round-3 literature gaps closed**, with accurate one-clause descriptions (Davidson 2006, Zhu 2016, Bandyopadhyay 2016, Grinch's separability condition). Evidence Anchor: text: Sec. II "Grinch's guarantee needs a separability condition"

**S4 Bounded negative search.** The gap sentence states tools and "abstracts only". Evidence Anchor: text: Sec. II "In the sources we searched (SciSpace, Consensus and web search, abstracts only)"

### Weaknesses

### W1: The Corollary's universal sentence is false as stated
**Problem**: "Any method that recomputes from the sets has (i) and (ii)" fails for methods that recompute from the whole set but are not functions of the unordered set. Counter-examples: (a) the paper's own DBSCAN (order agreement 0.997, border points) and HDBSCAN (0.983) in Table I; (b) seeded methods (k-means, Louvain); (c) index tie-breaks: `np.argmax` in `_cavg_merge` and in `c_avg` (exp19 line 120) pick the first maximum by index, and `c_avg` orders equal-similarity must-links by input order, i.e. device-local ids. For constrained average linkage, (i) with contradictory corrections is untested, because the precise user makes none (E2). Second half: "a method that stores labels and edits them does not" is too strong. An operation log replayed in a canonical order gives (i) and (ii) for the edits. What breaks the frozen store is the path-dependent assignment of new faces. The paper compares only against "replay in the order received", a third design (canonical-order log) is missing. (ii) is a tautology for any set-function; the meaningful content is that no other state depends on the correction (true in the code: constraints are read-time only).
**Evidence Anchor**: text: Sec. III "Any method that recomputes from the sets has (i) and (ii); a method that stores labels and edits them does not."
**Why it matters**: It is the paper's only general statement and a distributed-systems reader will test it in a minute.
**Suggestion**: "Any method whose output is a deterministic function of the unordered sets (permutation-invariant, no seeds, content-based tie-breaks) has (i) and (ii); a store whose state is updated by order-dependent operations does not." Say that retraction means "same remaining corrections", not the session the user would have had without the click. Optionally add a canonical-order edit-log baseline.
**Severity**: Major (rewrite, no new data) | **Confidence**: 4, core expertise.

### W2: Preconditions of (i) are hidden; the abstract claims more than E2 tested
**Problem**: (a) Agreement needs bit-identical embeddings and identical similarity arithmetic. The abstract says devices "exchange photos"; E2 exchanges faces (embeddings). If each device re-embeds photos (ONNX Runtime on different hardware) or runs float32 FAISS/BLAS paths, a pair within about 1e-6 of a threshold can flip, and exact agreement is no longer guaranteed. Remedy: ship the 2 KB embedding with the photo, or quantise to integers. (b) Faces need globally stable keys (photo hash plus box), not insertion indices; Sec. VI(vii) says so, the Corollary does not. (c) Output is not monotone in the inputs, so agreement holds only once both devices hold the same sets (eventual, not continuous). (d) Retraction across devices needs tombstones or observed-remove semantics; (i) and (ii) together are not tested.
**Evidence Anchor**: text: Abstract "two devices that exchange photos and corrections end with identical people in all 240 libraries"
**Why it matters**: "Identical people" is the headline consequence; as worded it describes a deployment not measured.
**Suggestion**: Reword to "exchange faces (embeddings) and corrections", add the four preconditions in one Limitations sentence.
**Severity**: Major | **Confidence**: 3, adjacent field (distributed systems; hardware effect reasoned, not measured).

### W3: The gap sentence is under-bounded and omits shipped features
**Problem**: It lists search tools but not queries, number or date, and conjoins four properties. The editor's scan found that Ente documents synced corrections and undoing a merge; my web search (query below) found Ente's FAQ describing de-merge through a history view, but nothing on guarantees. The paper cites Immich, PhotoPrism and FaceCluster but not Ente. "Corrections survive re-clustering" is trivial for hard constraints, so its absence from evaluations is unsurprising.
**Evidence Anchor**: text: Sec. II "we did not find an evaluation of whether face-grouping corrections survive later re-clustering, converge across devices"
**Why it matters**: A reviewer who knows one shipping product will read the sentence as unaware of it.
**Suggestion**: See the corrected wording below.
**Severity**: Major | **Confidence**: 4

### W4: Exact read step is correct but elementary; test power and presentation
**Problem**: Correct, including the constrained merge. By induction, every group lies inside one component of the graph with edges at cosine >= tau_g; cross-component pairs are all below tau_g, so their unweighted average is too. Blocked merges only remove merges, so splitting stays exact; the argmax ordering within a component equals the global one. The 1e-4 margin only enlarges components (float32 error is about 1e-7) and is harmless. Gaps: (a) it holds for UPGMA over original centroid points, not centroid linkage (UPGMC: a mean of spread points can be more similar to a third point than any member). The text says "centroid merge" and a reader may think the latter. (b) sklearn merges at s > tau, `_cavg_merge` at s >= tau; irrelevant to split-equivalence, relevant to "constrained path equals unconstrained path" at exact ties. (c) The probe in the novelty report had 3,822 components, largest size 2: the check barely exercises multi-step averaging (the proof carries it), and the 10x depends on a sparse threshold graph. (d) Not new: single-linkage components at a threshold are textbook (Gower and Ross 1969), and per-component clustering of scored pairs is described in record-linkage patent text I found; I could not find a paper that states it for average linkage.
**Evidence Anchor**: text: Sec. III "Average linkage over centroids never joins two groups of centroids unless some cross pair has cosine $\ge\tau_g$"
**Suggestion**: Add "unweighted average linkage over the centroids as points", the one-line induction, a component-size distribution, and call it an exactness-preserving optimisation in the Introduction bullet.
**Severity**: Minor | **Confidence**: 4

### W5: Baseline description and cost claim
**Problem**: "After Davidson and Ravi" is fair: ML closure, then constrained merges, threshold-stopped. But `c_avg` is face-level average linkage while ours merges unit-weighted centroids (different quantities; say so). The must-link revert (`par[ra] = ra`, lines 99-104) after `find` calls with path compression is still in the file; I did not run it. The 261 s comes from an `argmax`-over-full-matrix loop (about O(n^3)), while compiled plain average linkage took 16.7 s (so 8-13x, or 56x unconstrained). "The gap is two orders of magnitude" mixes the two.
**Evidence Anchor**: text: Sec. V-B "Part of this gap is implementation" ; "the gap is two orders of magnitude"
**Suggestion**: Abstract: "our NumPy implementation, 261 s; compiled unconstrained lower bound 16.7 s". Mention that generic agglomerative algorithms (Mullner 2011) accept arbitrary update rules; I did not verify they handle forbidden merges. Overlaps R1.
**Severity**: Major | **Confidence**: 3

### W6: CRDT description is loose; derived-view literature thin
**Problem**: CRDTs guarantee strong eventual consistency through a commutative, associative, idempotent merge. "Computing a result from the set of inputs ... is the idea behind" them is a special case (grow-only or observed-remove sets plus a pure derived view). The CALM view explains why a non-monotone derived output is still coordination-free for eventual consistency. "We apply it" is fair if said this way. The editor's report lists Navalho et al. 2015 and Laddad et al. 2022 on computation over CRDTs; I did not verify them.
**Evidence Anchor**: text: Sec. II "is the idea behind conflict-free replicated data types"
**Suggestion**: "Replicating faces and corrections as sets and deriving the grouping as a pure function of them gives strong eventual consistency [Shapiro] with no merge rule for clusters, the pattern local-first software relies on [Kleppmann]."
**Severity**: Minor | **Confidence**: 4

### W7: Noisy-constraint and retraction literature still thin; "flagging is hard" over-generalised
**Problem**: Retraction equals "exact deletion" in the unlearning literature (Ginart et al. 2019); constraint scoring exists (Davidson 2006 coherence; Randel et al. 2021 score identifies constraints to remove). The AUC 0.60 is for one naive score (cosine of the clicked pair).
**Evidence Anchor**: text: Sec. V-D "Flagging the wrong click is hard"
**Suggestion**: Cite both; write "a cosine-based score gives AUC 0.60".
**Severity**: Minor | **Confidence**: 4

### W8: Proposition: ties and float32
**Problem**: "We did not observe them" is unmeasured. Float32 offers only about 6 million values in [0.65, 1); with 10^4 to 10^5 edges per library, exact ties are expected (my estimate, not measured). They matter only when a cannot-link blocks one of two tied edges; core edges are sorted by face id. Also pair values are stored from the later face's row, so batch shape can change the last bit. Round-3 W3 is only partly addressed.
**Evidence Anchor**: text: Proof "we did not observe them"
**Suggestion**: Break ties by embedding bytes (as already done for must-links) or count ties and report none changed a partition.
**Severity**: Minor | **Confidence**: 3

### W9: Upgrade claim (iii)
**Problem**: Thresholds are recogniser-specific; the text does not say how the new recogniser's thresholds are set after an upgrade. BCT [Shen] avoids re-embedding; if a compatible model is used corrections survive trivially.
**Evidence Anchor**: text: Sec. III "so it can be applied to embeddings from another recogniser"
**Suggestion**: State thresholds were the new model's tuned ones; say BCT-style compatibility is complementary.
**Severity**: Minor | **Confidence**: 3

### Verification of the three new bibliography entries
All real and correctly described. Shapiro et al., SSS 2011, LNCS 6976, pp. 386-400 (confirmed on a bib record by Preguica). Kleppmann et al., Onward! 2019, pp. 154-178, DOI 10.1145/3359591.3359737 (search result agreed with the published record). Shen et al., CVPR 2020, pp. 6368-6377, DOI 10.1109/CVPR42600.2020.00640. The bib lacks these fields; add them. Shen's work is about comparing old and new embeddings without backfilling; "address a related upgrade problem" is accurate.

### Searches run (counter-example hunt; no author names or system name)
1. SciSpace: "Does a face clustering system for personal photo libraries keep user merge and split corrections when new photos are added and the groups are recomputed?" Nearest: Zhang et al. ACM MM 2009 (adding images, manual manipulation; abstract does not say corrections persist), Han et al. 2016 (constrained spectral clustering in a face annotation system, batch). No evaluation of the four properties.
2. SciSpace: model-upgrade query on preserving identity labels or constraints after re-embedding: only backward-compatible embedding papers.
3. Consensus: retracting a must-link or cannot-link constraint: found Randel 2021 (score constraints to remove), nothing on exact retraction.
4. SciSpace: exact data deletion in clustering: Ginart et al. 2019.
5. WebSearch: Ente face recognition, merge, undo, sync: undo of merges is a shipped feature; sync of corrections not confirmed by the docs I could see.
6. WebSearch and SciSpace on threshold-graph decomposition of hierarchical clustering: nothing found for average linkage; Gower and Ross for single linkage.
Result: no counter-example to the conjunction, one to "retraction" as a feature (Ente). The negative remains bounded.

### Answer: is the novelty statement defensible as worded?
Mostly, but not as worded. Corrected wording:
"Replicating inputs as sets and deriving the result as a pure function of them is the pattern behind CRDTs [Shapiro] and local-first software [Kleppmann]. Shipping photo managers already let users undo a merge (e.g., Ente), but we found no documented convergence guarantee and no evaluation of whether face-grouping corrections survive later re-clustering, converge across devices, can be retracted exactly, or survive a change of recogniser. This rests on N queries over SciSpace, Consensus and web search on 10 Nov 2026 (abstracts and product documentation only; list in the repository) and is not proof of absence."
Also soften "provably" in the first contribution bullet to "by construction, up to exact ties".

### Missing literature (verified by me this session unless marked)
Ginart et al. (exact deletion); Randel et al. (constraint scoring); Barr et al. (active face clustering with soft constraints); Han, Hu, Deng (face annotation system with constraints); Zhang et al. 2009 (closest face-album system); Gower and Ross (single-linkage components); Mullner 2011 (agglomerative algorithms); UniBCT or CoReS for compatibility. Soenen et al. 2020, Yoshida 2012, Navalho 2015, Laddad 2022 are in the editor's scan; I did not verify them.

~~~yaml suggested-references
- title: "Making AI Forget You: Data Deletion in Machine Learning"
  authors: ["Ginart, A.", "Guan, M. Y.", "Valiant, G."]
  year: "2019"
  doi: null
  arxiv_id: null
- title: "A Lagrangian-based score for assessing the quality of pairwise constraints in semi-supervised clustering"
  authors: ["Randel, R.", "Aloise, D.", "Hertz, A."]
  year: "2021"
  doi: null
  arxiv_id: null
- title: "Framework for Active Clustering With Ensembles"
  authors: ["Barr, J. R.", "Bowyer, K. W.", "Flynn, P. J."]
  year: "2014"
  doi: null
  arxiv_id: null
- title: "Constrained Spectral Clustering on Face Annotation System"
  authors: ["Han, J.", "Hu, J.", "Deng, W."]
  year: "2016"
  doi: null
  arxiv_id: null
- title: "Face based image navigation and search"
  authors: ["Zhang, T.", "Xiao, J.", "Wen, D.", "Ding, X."]
  year: "2009"
  doi: "10.1145/1631272.1631365"
  arxiv_id: null
- title: "Minimum spanning trees and single linkage cluster analysis"
  authors: ["Gower, J. C.", "Ross, G. J. S."]
  year: "1969"
  doi: "10.2307/2346439"
  arxiv_id: null
- title: "Modern hierarchical, agglomerative clustering algorithms"
  authors: ["Mullner, D."]
  year: "2011"
  doi: null
  arxiv_id: "1109.2378"
- title: "Towards Universal Backward-Compatible Representation Learning"
  authors: ["Zhang, B.", "Ge, Y.", "Shen, Y."]
  year: "2022"
  doi: null
  arxiv_id: null
~~~

### Questions for Authors
1. In E2, does any run include contradictory corrections for constrained average linkage? Which order breaks equal-similarity must-links there?
2. Do both devices share embeddings in E2? What happens with independently computed embeddings?
3. How many exact ties exist among edges at tau_l, and did any change a partition?
4. What is the distribution of centroid-component sizes in the 240 libraries?

### Minor Issues
- "480 test libraries" (Sec. III) means 240 pairs x 2 recognisers; say so.
- Intro "about ten times faster" holds for the unconstrained read only (2.3x with corrections).
- Sec. V-B says 1.3 s for ten corrections; Sec. V-E says 1.9 s for the same step.
- Use "order independent" once, as the literature does.

## Recommendation
Minor Revision. Confidence 4. Calibration status NOT_CALIBRATED.

## Plain-language verdict for the student author
1. Your experiments are honest and the paper no longer over-claims accuracy; that is the hard part done.
2. The sentence "any method that recomputes from the sets has (i) and (ii)" is wrong, your own DBSCAN row proves it; say "any method that gives the same answer whatever the order of the photos".
3. Say clearly that two phones only agree if they share the same embeddings and face IDs; your test shared them, and your abstract says "photos".
4. Mention that real apps (Ente) already let you undo a merge, and write down how many searches you ran and when.
5. The fast read step is correct but a known trick; call it an optimisation, not a contribution.

## Top 3 issues
1. W1: the Corollary's universal claim is false as stated (Major).
2. W2: hidden preconditions and the "exchange photos" wording in the abstract (Major).
3. W3: the gap sentence omits shipped features and is not reproducible (Major).
