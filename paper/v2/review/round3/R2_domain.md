## Domain Review Report (Peer Reviewer 2), Round 3

Manuscript: `paper/v2/cove_paper.tex` (commit ef69690). Simplified run: no sprint contract, no Phase 1 / Phase 2 split. I did not read any other round-3 report; I read only `00_reviewer_cards.md`.

### Reviewer Identity
Face-clustering and constrained-clustering researcher. Focus: whether the new Sec. II paragraph describes C-DBSCAN, C-DenStream, Lasek & Gryz, Grinch, ConPaC and Wu et al. correctly; whether "what we add is the order-invariance guarantee" survives that literature; whether the proof sketch matches `stable_cluster.py`; what is still missing on noisy constraints; whether the baseline names are right.

### Overall Recommendation
**Minor Revision.** The related-work paragraph is mostly accurate and the round-2 gaps (uncited near neighbours, ordering by face id) are genuinely closed. The domain problems left are mainly about how the contribution is worded against prior art, a few unstated assumptions in the proof, and one code behaviour that contradicts a sentence in Sec. III. All are fixable in text, plus one decision about the attach step.

### Confidence Score
4. Core expertise in clustering evaluation. I checked the code by reading it and by one executed test case. I could not read the full text of C-DBSCAN, C-DenStream or Lasek & Gryz, so statements about their internals are limited to abstracts and search snippets.

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

### Criterion-Bound Judgements
| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Literature coverage | Reviewer-2 remit, domain agent Step 1 | PARTLY_MEETS | absence: Sec. II — expected noisy-constraint, coherence and active/interactive face-clustering work; checked cove_paper.tex, references.bib | Constraint-based clustering is covered well; noisy-oracle and constraint-coherence work, which the paper's own negative result needs, is absent | Authors' scan lists items they did not cite | yes: the "wrong corrections are sticky" result is the paper's most novel finding and has no literature around it |
| Accuracy of descriptions of cited work | Reviewer-2 remit, domain agent Step 3a | MEETS | text: Sec. II "pairwise constraints have been used in clustering by Shi et al." | Each of the six is described correctly at abstract level; two need sharper wording (Grinch, ConPaC) | Abstract-level only for C-DBSCAN, C-DenStream, Lasek & Gryz | no |
| Contribution positioning | Reviewer-2 remit, domain agent Step 4c | PARTLY_MEETS | text: Sec. II "what we add is the guarantee that the result, with corrections, does not" | Order independence has prior art in the incremental setting; the real gap is order-free hard constraints with a user in the loop | The author scan already says this | yes |
| Proof sketch soundness | Reviewer-2 remit, domain agent Step 3b | PARTLY_MEETS | text: Proof "Only exactly equal real-valued similarities, where the face-id tie-break could matter, remain; we did not observe them." | Structure holds against the code; assumptions (tie handling, floating point, corrections as faces not ids) are not stated | One executed test, not a full audit | partly |
| Baseline naming | Reviewer-2 remit, domain agent Step 3c | MEETS (with a wording change) | text: Sec. IV "constrained average linkage~\cite{davidson2005agglomerative}" | Implementation is a faithful instance of the D&R scheme but is not D&R's exact algorithm | | no |

### Summary Assessment
The paper presents an incremental face clusterer whose result does not depend on photo import order, accepts must-link and cannot-link corrections, and keeps them when new photos arrive. After round 2 it also reports fair baselines: constrained average linkage, re-apply, and an Immich-style frozen rule. The new related-work paragraph is competent. I found no misdescription of any of the six newly cited works at abstract level, and the bibliographic details I checked are right. The weakness is the sentence that states the contribution. Order independence for incremental clustering has been claimed and proved before (Grinch; Bandyopadhyay and Murty), and batch constrained methods are order-free by construction, so the guarantee is not what is new. What is new is the combination: hard user constraints, in an order-free incremental clusterer, with an empirical look at what happens to them over time and what happens when they are wrong. The proof sketch matches the code in outline, but it leaves out assumptions that matter for real photo libraries (duplicates, floating point, corrections addressed by face id). One code path (non-core faces joined by a must-link) contradicts a sentence in Sec. III. The literature on noisy constraints and constraint coherence, which bears directly on the "sticky wrong corrections" result, is missing. I recommend Minor Revision.

### Strengths
1. **S1 Related-work paragraph is accurate and honest about its own limits.** C-DBSCAN, C-DenStream and Lasek & Gryz are correctly placed as density-based clustering with instance constraints (stream version for C-DenStream); Wu et al. are correctly placed as track-derived constraints for face clustering in video. The paper also states the search was abstract-only. Evidence Anchor: text: Sec. II "In the sources we searched (SciSpace, Consensus and web search, abstracts only) we did not find an evaluation"
2. **S2 Round-2 contradictory-correction defect fixed and tested.** Must-links are now sorted by similarity then embedding bytes, not by face id, and the paper says so. Evidence Anchor: text: stable_cluster.py `_labels_constrained` "return (-float(np.dot(X[a], X[b])), ka, kb)"
3. **S3 Bibliographic details verified.** C-DBSCAN (RSFDGrC 2007, LNCS 4482), C-DenStream (DS 2009, LNCS 5808), Lasek & Gryz (ComSIS 16(2), 2019, pp. 469-489), Grinch (KDD 2019, DOI matches), Wu et al. (CVPR 2013, DOI 10.1109/CVPR.2013.450) all match web records. Evidence Anchor: dataset: references.bib entries ruiz2007cdbscan, ruiz2009cdenstream, lasek2019density, monath2019grinch, wu2013constrained
4. **S4 The negative result on wrong corrections is reported plainly.** Evidence Anchor: text: Sec. V-C "Wrong corrections are sticky."

### Weaknesses

### W1: "What we add is the order-invariance guarantee" is over-claimed against prior art the authors already found
**Problem**: In the incremental setting, order independence is a known target with a prior theorem and prior algorithm. Grinch (Monath et al. 2019) proves its tree contains the ground truth independent of arrival order (under a separability condition on the linkage). Bandyopadhyay and Murty (ICPR 2016, "Axioms to characterize efficient incremental clustering") define order independence and propose an order-independent incremental algorithm. The paper's own scan lists both (`innovation_scan_2026-11-07.md`), but Sec. II describes Grinch only as repairing earlier merges and does not cite Bandyopadhyay and Murty. Batch constrained methods (C-DBSCAN, Wu et al., constrained agglomerative) are functions of the whole set and so are not order-dependent in the first place, apart from DBSCAN border points. Order-invariance of this clusterer follows largely from its single-linkage / DBSCAN core structure, as the paper itself says in Sec. III ("single linkage at $\tau_\ell$").
**Evidence Anchor**: text: Sec. II "constrained step is closest to C-DBSCAN; what we add is the guarantee that the result, with corrections, does not"
**Why it matters**: A reviewer who knows Grinch will read the sentence as a priority claim and challenge it. The honest contribution is narrower and defensible.
**Suggestion**: Reword to: "order independence of incremental clustering is known (Grinch, Bandyopadhyay and Murty, OGMC); we keep it while enforcing hard must-link and cannot-link corrections, and we measure what happens to those corrections as photos arrive." Say in one clause what Grinch's guarantee needs (a separability condition) and that this paper's guarantee needs none but relies on the single-linkage structure. Add Bandyopadhyay and Murty.
**Severity**: Major
**Confidence**: 4. Core expertise; Grinch's theorem and Bandyopadhyay and Murty's claim both checked against search snippets of the abstracts.

### W2: "Closest to C-DBSCAN" is arguable; the nearer relative is constrained single linkage (Davidson and Ravi)
**Problem**: At the tuned setting $m=1$, the paper says the core step is single linkage. The constrained step in code is a Kruskal-style pass over edges in decreasing similarity that skips any union joining a cannot-linked pair. That is constrained agglomerative clustering with single linkage, which is the Davidson and Ravi scheme the paper already cites, plus a threshold, an attach step and a centroid merge. C-DBSCAN, as far as the abstract and snippets show, adds ML/CL to DBSCAN's neighbourhood expansion; I could not read its full text, so how it treats conflicts or order is unverified. Lasek and Gryz introduce "deferred points" to place points whose cannot-links would otherwise force an order-dependent choice. That addresses the same problem as the attach step here and deserves one clause.
**Evidence Anchor**: text: Sec. III "the core step is single linkage at $\tau_\ell$"
**Why it matters**: Positioning drives how novelty is read. It also tells the reader which known results (feasibility, dead-ends of constrained agglomeration) carry over.
**Suggestion**: Say "at $m=1$ our constrained step is Kruskal-style constrained single linkage; with $m>1$ it resembles C-DBSCAN/Lasek-Gryz density-based constraint handling." Add one clause on deferred points.
**Severity**: Minor
**Confidence**: 3. Could not read the C-DBSCAN or Lasek and Gryz full text.

### W3: Proof sketch leaves out assumptions that real photo libraries break
**Problem**: Checked against `_labels_constrained` and `add`:
 (a) Ties. Core edges are sorted by `(-e[0], e[1], e[2])` and attachment by `(-a[0], a[1])`, i.e. by face id, and the final merge picks `np.argmax` over cluster indices derived from the minimum face id. Without cannot-links, tie order does not change the components. With cannot-links it can (which of two tied edges is blocked first). The proof says ties are "exactly equal real-valued similarities … we did not observe them". In a personal library, burst shots, duplicate imports and exported copies give pairs with similarity at or near 1.0, and exactly identical embeddings. For identical embeddings, `must_key` falls back to equal keys, so the order is set-iteration order, which contradicts "never by face ids" in Sec. III.
 (b) Floating point. Similarities come from a float32 FAISS `range_search`. Within one batch each new-new pair is computed in both directions and stored separately in `adj[i]` and `adj[j]`; old-new pairs are stored once. Batched matrix products need not return bit-identical values for the same pair across batch shapes, so a pair within one ulp of a threshold can flip with the batch split. The proposition assumes $s(i,j)$ is a pure function of the pair.
 (c) Corrections are addressed by face id (`add_must_link(i, j)`), which is the insertion index. "For fixed corrections" is only well defined if corrections are stated on faces and re-expressed under each order. The experiment (`inv[a]` in exp19) does this; the proposition does not say it.
**Evidence Anchor**: text: Proof "Only exactly equal real-valued similarities, where the face-id tie-break could matter, remain; we did not observe them."
**Why it matters**: The headline is "order-invariant ... provably". The sentence is nearly true, but a reviewer who tries a library with duplicates can falsify it.
**Suggestion**: State three assumptions in the proposition: distinct embeddings (or a content-based tie-break), pair similarities computed identically whatever the batch split, and corrections given as pairs of faces. Either compute similarities once per unordered pair, or quantise them (e.g. round to 1e-5) before thresholding and sorting, and say so. Add a test with duplicated photos.
**Severity**: Minor
**Confidence**: 4. Read the code; the floating-point point is a standard property of BLAS-backed search, not tested here.

### W4: Constrained path lets a single must-link between two non-core faces merge two whole clusters, contradicting Sec. III
**Problem**: Sec. III states "Non-core faces never link two clusters". In the constrained path, `has_core` is computed before any attachment, and the attachment loop then tries every non-core face whose component is not yet in `has_core`. A must-link between two non-core faces makes them one component. The first attaches to cluster X; the second then attaches to cluster Y, and `try_union` merges X and Y (no cannot-link blocks it). I confirmed this with a small executed case (3 faces around one direction, 3 around another, two peripheral faces at cosine about 0.6 to each cluster, `link_threshold=0.65`, `min_neighbors=1`, `attach_threshold=0.5`): without the must-link the result is two clusters; with one must-link between the two peripheral faces, all 8 faces form one cluster in all 20 random orders. So the behaviour is order-invariant but not what Sec. III describes. It matters because the faces a user picks to fix a split person are often fragment singletons, and singletons are non-core.
**Evidence Anchor**: text: stable_cluster.py L252 "if self.core[i] or find(i) in has_core:" together with Sec. III "Non-core faces never link two clusters"
**Why it matters**: The user's "same person" for two weak faces becomes "same person" for two clusters joined on attach evidence ($\tau_a=0.50$, looser than the link threshold 0.65). Table II results (exp19) may include such merges; the paper does not report how often.
**Suggestion**: Decide the intended semantics. Either re-evaluate `find(i) in has_core` inside the loop, so a component attaches to at most one core cluster, or keep the behaviour and say so in Sec. III. Count how often it happens in exp19 and report it.
**Severity**: Major
**Confidence**: 4. One executed minimal case plus code reading; frequency in exp19 not measured.

### W5: The literature on noisy constraints and constraint coherence is missing, although the paper's own finding sits in it
**Problem**: The paper finds that wrong corrections persist and proposes only "show them and let the user remove one". Constraint quality is a studied topic: Davidson, Wagstaff and Basu (PKDD 2006) show that a constraint set can lower accuracy and define informativeness and coherence measures; Zhu, Loy and Gong (IEEE TNNLS 2016) handle constraints from imperfect oracles by flagging unreliable ones; Mazumdar and Saha (NeurIPS 2017) analyse clustering from noisy same-cluster queries; correlation clustering (Bansal, Blum, Chawla 2004) is the standard treatment of contradictory pairwise labels. Active and interactive face clustering with simulated or real human answers (Biswas and Jacobs, IJCV 2014; Cohn, Caruana, McCallum on clustering with user feedback) is the established frame for the simulated users in Sec. IV. None is cited. The statement that no one evaluated whether corrections survive re-clustering may still hold, but it needs to be made against this background.
**Evidence Anchor**: absence: Sec. II and references.bib — expected noisy-constraint, constraint-coherence and active/interactive face-clustering citations; checked cove_paper.tex Sec. II, Sec. V-C, Sec. VI, references.bib
**Why it matters**: The error-prone user is the paper's most informative new result, and without this work a reader cannot tell whether it is known.
**Suggestion**: Add one sentence naming these works. A cheap use: Davidson et al.'s coherence is exactly "does this correction contradict existing ones?", which could drive a "show conflicts" view. Do not claim a detector the paper does not run.
**Severity**: Major
**Confidence**: 4. The cited works were each checked by web search (abstract level); relevance judgement is mine.

### W6: Immich-style baseline is a simplification of Immich and is cited to the repository, not to the documentation
**Problem**: The paper describes frozen as "each new face joins the person of its most similar face if the similarity is at least 0.5, Immich's default", and cites only the GitHub repository. Current Immich documentation (docs.immich.app/features/facial-recognition) describes a DBSCAN-derived procedure: a new face joins the person of its most similar face if one is within the Maximum Recognition Distance; otherwise it becomes a core point only if it has at least Minimum Recognized Faces similar faces (default 3 in the settings page, which the docs page itself does not state); non-core faces wait until the rest of the batch is processed and are treated as outliers if still unassigned; search uses a limited number of nearest matches. The docs also describe the distance threshold on a 0 to 2 cosine-distance scale. The paper's rule has no core-point requirement for creating a person and no deferral. I could confirm the structure from the docs; I could not confirm the numeric defaults 0.5 and 3 from the documentation text, so the "0.5, Immich's default" claim should be cited to the source's default configuration. Immich also runs on a larger recogniser than MBF or EdgeFace-S, so 0.5 is not calibrated for these models (the paper notes this for MBF).
**Evidence Anchor**: text: Sec. IV "earlier people are kept and each new face joins the person of its most similar face if the similarity is at least 0.5"
**Why it matters**: "Immich-style" invites a reader to treat the result as a statement about Immich. It is a statement about a simplified freeze rule.
**Suggestion**: Call it "freeze-and-assign (Immich-style)", cite the docs page and the config file for the 0.5 default, and state that core-point creation and batch deferral were omitted. Optionally add a variant with min-faces = 3 and deferral.
**Severity**: Minor
**Confidence**: 3. Doc structure verified by fetch; numeric defaults recalled but not found in the documentation text.

### W7: Baseline naming "constrained average linkage (Davidson & Ravi 2005)"
**Problem**: Davidson and Ravi (PKDD 2005) give a framework and complexity results for agglomerative clustering with must-link and cannot-link constraints, including that a naive merge can dead-end. The implemented baseline (`c_avg`) is a faithful instance: must-link groups first, then true average linkage over faces, never merging a cannot-linked pair, stopping at a tuned similarity threshold (not at $k$). The must-link closure also drops a must-link that would break a cannot-link, which is an addition. This is "in the manner of", not their algorithm, and the paper's own merge step uses an average over cluster centroids with unit weights, which is not the same quantity as the baseline's face-level average.
**Evidence Anchor**: text: Sec. IV "constrained average linkage~\cite{davidson2005agglomerative} (must-link groups first, then average-linkage merges that never join a cannot-linked pair)"
**Why it matters**: Low. A pedantic reviewer will check.
**Suggestion**: Write "constrained average linkage (after Davidson and Ravi)" and add "threshold-stopped" in the protocol sentence.
**Severity**: Minor
**Confidence**: 4. Compared `c_avg` to the description of the 2005 scheme from the abstract and my knowledge of it.

### W8: Descriptions of Grinch and ConPaC are slightly off in emphasis
**Problem**: (i) Grinch is described as repairing earlier merges only; its main theoretical claim is arrival-order independence under separability, which is the property this paper claims (see W1). (ii) ConPaC is "Conditional Pairwise Clustering": its core method estimates the adjacency of faces with a conditional random field and loopy belief propagation; must-link and cannot-link constraints are an optional semi-supervised extension, and are probabilistic rather than hard. "Pairwise constraints have been used in clustering by Shi et al." is true but suggests the paper is about user constraints. The TIFS record is vol. 13, no. 7, pp. 1626-1640, DOI as in the bib; the round-3 log says volume and pages were unconfirmed, and my search confirms them.
**Evidence Anchor**: text: Sec. II "incremental hierarchical clustering can repair earlier merges as points arrive"
**Why it matters**: Small, but each is a place a domain reviewer notices.
**Suggestion**: Grinch: "...with an arrival-order-independence guarantee under a separability condition". ConPaC: "a CRF-based face clusterer that can also take must-link and cannot-link constraints (as soft evidence)". Add volume, number and pages to the bib entry.
**Severity**: Minor
**Confidence**: 4. Abstract-level verification.

### Detailed Comments

#### Literature Review
- **Coverage**: Good on constrained density-based and hierarchical clustering. Missing: noisy-constraint and coherence work (W5), Bandyopadhyay and Murty (W1), active and interactive image or face clustering (Biswas and Jacobs; Cohn et al.). The authors' scan also lists Basu et al. 2004 and Barr et al. 2014; I did not verify those.
- **Integration quality**: The paragraph names works, then states one contrast. It does not say what each does with conflicting constraints, whether constraints are hard or soft, or whether each is incremental. A three-column mini-table (hard/soft, incremental, order-free) would carry more than the prose and fit a 6-page paper.
- **Research gap argument**: The final sentence of "Interactive face grouping" is careful and honest. The gap is real but narrow: corrections surviving re-clustering in a personal library.

#### Theoretical Framework
- **Appropriateness**: Constrained clustering (instance-level constraints) is the right frame.
- **Application depth**: The paper uses the constraint idea but not the feasibility and coherence results of that literature. Contradictory corrections are resolved by a rule (strongest must-link wins; cannot-link beats must-link) without saying that this is a repair of an inconsistent constraint set.
- **Alternative frameworks**: Correlation clustering treats contradictory pairwise labels in one objective; a soft-constraint formulation would also allow removing wrong corrections. Worth one sentence.

#### Academic Argument Quality
- **Factual accuracy**: No factual error in the six descriptions. "Incremental DBSCAN ... same result ... up to the assignment of border points" is a fair reading of Ester et al. 1998.
- **Argument logic**: "As the proposition predicts" (Sec. V-A) rests on three random orders; it is evidence, not confirmation of the proof (W3).
- **Terminology precision**: "Order-invariant" vs. "order independent": the literature uses "order independent"; say so once. "Corrections kept 100%" is acknowledged as by construction.

#### Contribution to the Field
- **Incremental contribution**: Practical and methodological, small. The new knowledge is that (1) with fair baselines, constraints inside the clusterer, constrained average linkage and freezing reach the same F1; (2) wrong corrections stick; (3) re-applying stored corrections is weaker when users click arbitrary faces.
- **Positioning**: See W1 and W2.
- **Overclaiming**: The Discussion and Conclusion are properly sized. The remaining overclaim is the Sec. II priority sentence.

#### Missing Key References
- Davidson, Wagstaff, Basu 2006, "Measuring constraint-set utility for partitional clustering algorithms" (PKDD; informativeness and coherence). Verified by search.
- Zhu, Loy, Gong 2016, "Constrained Clustering With Imperfect Oracles" (IEEE TNNLS 27(6):1345-1357). Verified by search.
- Mazumdar and Saha 2017, "Clustering with Noisy Queries" (NeurIPS). Verified by search.
- Bansal, Blum, Chawla 2004, "Correlation Clustering" (Machine Learning 56:89-113). Verified by search.
- Bandyopadhyay and Murty 2016, "Axioms to Characterize Efficient Incremental Clustering" (ICPR, pp. 450-455). Verified by search (abstract level).
- Biswas and Jacobs 2014, "Active Image Clustering with Pairwise Constraints from Humans" (IJCV 108(1-2):133-147). Verified by search.
- Cohn, Caruana, McCallum 2003, "Semi-supervised clustering with user feedback" (Cornell tech report TR2003-1892). The paper is real; the exact report number is not verified, so omit it. Existence verified by search.
- Pourrajabi et al. 2014, "Model selection for semi-supervised clustering" (EDBT, pp. 331-342). Verified by search. Low priority: it concerns choosing parameters using constraints, which the paper already touches through Daniels and Giraud-Carrier and Van Craenendonck. Cite only if space allows.
- [UNVERIFIED] Basu, Banerjee, Mooney 2004, "Active semi-supervision for pairwise constrained clustering" (SDM), and Barr et al. 2014 on active face clustering: both come from the authors' scan; I did not check them.

~~~yaml suggested-references
- title: "Measuring Constraint-Set Utility for Partitional Clustering Algorithms"
  authors: ["Davidson, I.", "Wagstaff, K. L.", "Basu, S."]
  year: "2006"
  doi: "10.1007/11871637_15"
  arxiv_id: null
- title: "Constrained Clustering With Imperfect Oracles"
  authors: ["Zhu, X.", "Loy, C. C.", "Gong, S."]
  year: "2016"
  doi: "10.1109/TNNLS.2014.2387425"
  arxiv_id: null
- title: "Clustering with Noisy Queries"
  authors: ["Mazumdar, A.", "Saha, B."]
  year: "2017"
  doi: null
  arxiv_id: "1706.07510"
- title: "Correlation Clustering"
  authors: ["Bansal, N.", "Blum, A.", "Chawla, S."]
  year: "2004"
  doi: "10.1023/B:MACH.0000033116.57574.95"
  arxiv_id: null
- title: "Axioms to Characterize Efficient Incremental Clustering"
  authors: ["Bandyopadhyay, S.", "Murty, M. N."]
  year: "2016"
  doi: null
  arxiv_id: null
- title: "Active Image Clustering with Pairwise Constraints from Humans"
  authors: ["Biswas, A.", "Jacobs, D. W."]
  year: "2014"
  doi: "10.1007/s11263-013-0680-6"
  arxiv_id: null
- title: "Semi-supervised clustering with user feedback"
  authors: ["Cohn, D.", "Caruana, R.", "McCallum, A."]
  year: "2003"
  doi: null
  arxiv_id: null
- title: "Model selection for semi-supervised clustering"
  authors: ["Pourrajabi, M.", "Moulavi, D.", "Campello, R. J. G. B.", "Zimek, A.", "Sander, J.", "Goebel, R."]
  year: "2014"
  doi: "10.5441/002/edbt.2014.31"
  arxiv_id: null
- title: "Active semi-supervision for pairwise constrained clustering"
  authors: ["Basu, S.", "Banerjee, A.", "Mooney, R. J."]
  year: "2004"
  doi: null
  arxiv_id: null
~~~

Verification status: the first eight entries were located by web search in this session (title, authors, year, venue; DOIs shown are those the search results gave). The last entry (Basu et al. 2004) is UNVERIFIED: it is named in the authors' own scan only.

### Questions for Authors
1. In exp19, in how many corrections did the constrained path join two core clusters through a must-link between two non-core faces (W4)? Is that the intended semantics?
2. Does the order-invariance test (three random orders) include libraries with duplicated or near-duplicated photos, and are any exactly equal similarities present in the test libraries (W3)?
3. What do you claim that Grinch and Bandyopadhyay-Murty do not (W1)? A one-line answer would settle the Sec. II wording.
4. Would a conflict flag, using constraint coherence, be a cheap way to make wrong corrections visible, as the Discussion asks for?

### Minor Issues
- Sec. II is a long single paragraph; consider splitting it into "order independence" and "constraints".
- `references.bib`: ConPaC is missing `volume = {13}`, `number = {7}`, `pages = {1626--1640}`; Lasek and Gryz is missing `pages = {469--489}`.
- Immich entry cites the repository; add the documentation URL (`docs.immich.app/features/facial-recognition`) and a date.
- "Order-invariant" vs. "order independent": use the literature's term once, then keep yours.
- Sec. V-C: "as the proposition predicts" would read better as "consistent with".
- The C-DBSCAN reference lists no page numbers beyond 216-223; keep them (they match the record I found).
