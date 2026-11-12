# Round 5, Reviewer 2 (Domain: constrained / face clustering, distributed systems)

Manuscript: paper/v2/cove_paper.tex, with paper/v2/references.bib. Read-only review. I read the manuscript and the bib in full. For background I read the round-4 card and grepped paper/v2/research/round5_confirm. I ran one Consensus search, to check what the OGMC abstract says. Everything else comes from my own knowledge. Items I could not check are marked **unverified**.

## Recommendation

**Weak accept / minor-to-moderate revision. Confidence 4/5.**

The paper is honest about its limits and well bounded. Almost all of my points concern the wording of prior-work claims, a few places where the technical description is imprecise, and some missing neighbours in the literature. I found no fabricated or wrongly attributed result, but one citation (GRINCH) looks mis-described. The main residual risks are these:
- The distributed-systems framing claims a little more than a one-shot simulation supports.
- The "read step" is not incremental.
- The Proposition is closer to a bookkeeping lemma than to a property of this clusterer.

## Issues

### MAJOR

**M1. GRINCH is probably cited for something it does not do.**
Location: "Constraints have been added to density-based clustering ..., to incremental hierarchical clustering~\cite{monath2019grinch}".
- GRINCH (Monath et al., KDD 2019) is an incremental, non-greedy hierarchical clustering algorithm using rotations and grafts. Its abstract, as I recall it and as summarised in the round-5 recheck file, does not mention must-link or cannot-link constraints. The recheck file lists it as a counter-example for "incremental, order-independent", not for "constrained".
- The audit file marks the entry VERIFIED for "incremental hierarchical clustering can repair earlier merges", which is a different claim from the sentence the paper actually makes.
- Fix, either way:
  - Move GRINCH to a clause of its own: "incremental hierarchical clustering with rotations and grafts, whose order-independence guarantee needs a separability condition [monath2019grinch]".
  - Or replace it with a genuinely constrained incremental or streaming work that does what the sentence says. Halkidi et al. PAKDD 2012 and C-DenStream (already cited) fit, as does Kobren et al. AKBC 2019 (see the missing references).

**M2. "This split is classical; we use it for speed" overstates what the cited source supports.**
Location: Method, "Exact read step", and the Related Work sentence "Splitting a linkage clustering at the components of a threshold graph is classical for single linkage~\cite{gower1969mst}".
- Gower and Ross (1969) relate single linkage to the minimum spanning tree. The equivalence "single linkage cut at t = components of the threshold graph" goes back to Florek et al. 1951 and Johnson 1967. This is accurate for single linkage, and the Related Work sentence is correctly scoped to it.
- The Method paragraph, however, applies the split to **average** linkage (the step the paper itself calls "exact"). That is a different, though easy, argument: an average cannot exceed its largest term. "This split is classical" in that paragraph reads as covering average linkage, which Gower-Ross does not.
- The recheck file lists Maus and Borin 2026 and Dhulipala et al. 2021 for sparse-graph agglomerative clustering with component-wise independent subproblems, but the manuscript does not cite them.
- Fix: "For single linkage this decomposition is classical [gower1969mst]; for threshold-cut average linkage it is the usual sparse-graph decomposition [Maus&Borin, Dhulipala], and we use it for speed." Cite whichever of these the authors have actually read.

**M3. The "exact" argument depends on what "average linkage over centroids" means, and the text is ambiguous.**
Location: "Average linkage over centroids never joins two groups unless some cross pair has cosine $\ge\tau_g$ (an average cannot exceed its largest term)".
- If the merge is UPGMA over the centroid vectors, treated as items (Lance-Williams update), the argument is valid.
- If merged clusters get a recomputed, re-normalised centroid, the method is centroid (UPGMC-type) linkage. Then the similarity of a merged centroid to a third one is not an average of the earlier pairwise values, and the argument fails. Centroid linkage can also produce inversions.
- Terminology is blurred elsewhere too. The "Avg. linkage" baseline appears to be average linkage over faces, while ours merges centroids, and "constrained average linkage" is also over faces. This should be said once.
- The empirical check (240 pairs, identical partitions) is reassuring but is not a proof for the centroid-renormalising variant.
- Fix: state the exact merge definition. State that the baseline is on faces and ours on cluster centroids as items. Qualify "exact" as "identical to the original merge by the argument above, checked on 240 pairs and 8,290 faces".

**M4. "Convergence across devices" is claimed in the Related Work, but no sync protocol exists, so what is shown is weaker.**
Location: "we did not find a measurement of whether face-grouping corrections ... converge across devices". Also the Proposition's Consequences (i): "devices that exchange both sets agree". Also the Conclusion: "Recomputing from sets gives devices that agree".
- What is shown is that two replicas holding equal sets compute equal partitions. Convergence in the CRDT sense (strong eventual consistency) additionally needs the following, none of which is built or simulated:
  - (a) a merge for the sets. Faces are grow-only, but corrections need removal (retraction) and face deletion, so you need tombstones or an observed-remove set. Concurrent add and remove, and a correction naming a face deleted on the other device, are not simulated.
  - (b) globally stable face ids (content-addressed, or per-device ids with a mapping).
  - (c) identical embeddings and similarities on all devices. Different CPUs or runtimes give different float32 values, which matters for threshold and tie decisions. Embeddings should be part of the replicated state, not recomputed per device.
- The simulation is one exchange between two devices with no concurrency during the exchange and no partial delivery.
- Fix: "devices holding the same two sets compute the same people; a sync protocol (set merge with tombstones, stable face ids, replicated embeddings) is future work". Replace "converge" by "agree" in Related Work. Add one sentence listing (a) to (c) under Scope and next steps. The Fig. 1 caption "exchanging the two sets between devices ... gives the same result as starting again" should carry the same qualifier.

**M5. The "frozen + edits" baseline makes the 53% figure look more informative than it is.**
Location: Abstract "(53\% for a frozen-label rule with replayed edits)"; Table 3.
- The paper does say the baseline is its own design. But "replayed in received order" with no timestamps or causal order is a deliberately non-convergent op log. A standard op-based approach (Lamport or hybrid-logical timestamps, last-writer-wins per face) would converge on labels. Such a baseline would still fail retraction and the revision of earlier groupings, which is the real argument.
- The text correctly says the property "is not unique to our clusterer; it is what a plain edit log lacks". The abstract number invites the opposite reading.
- Fix: in the abstract write "a naive edit log replayed in arrival order" and drop the bare 53%. Or add a timestamped-LWW frozen variant, so that the retraction and revision result stands alone.

**M6. The incremental-update description is only true without corrections, and the "read" step is not incremental.**
Location: "Core status and links only switch from false to true, so no earlier decision is undone; attachment and the merge are recomputed when labels are read." Also Corrections paragraph, steps (1)-(2).
- With cannot-links, union order matters. Steps (1) and (2) are a greedy Kruskal-style pass with a conflict test, so a new higher-similarity edge can pre-empt a previously accepted lower-similarity one. The timings (20 s with ten corrections at 50,000 faces; "edge sorting and attachment in Python now dominate") confirm that steps (1) and (2) are redone at read.
- So "no earlier decision is undone" holds for the correction-free union-find only. The method is incremental in neighbour lists and read-time recompute. The abstract's "must update the groups as photos arrive" and the "order of magnitude faster" claim should be read with that in mind. The comparator, constrained average linkage, is at least given the same component split.
- Fix: say explicitly that what is incremental is the neighbour structure and core flags, that reads are full recomputes (O(E log E) on the sparse threshold graph), and that deletion rebuilds the union-find.

### MINOR

**m1. The Proposition is mostly a bookkeeping statement and its name suggests more.**
- For a batch method such as average linkage, determinism in the sets is trivial. The non-trivial content is that the incremental neighbour-list and core-flag structure matches a from-scratch build. The proof sketch says exactly this. The "consequences" paragraph then correctly states that (i)-(iii) hold for any recompute-from-sets method, and that is the right scoping.
- The sentence "A clusterer ... does not depend on the order or batching of insertions or on deletions" in contribution 1 is less careful than the Consequences paragraph. Add "(as does any batch method)".
- The Proposition statement is fine for insertion and deletion. It says "up to exact ties between real-valued similarities". Float32 range-search results can differ in the last bit depending on batch size and BLAS or SIMD path, so a pair at the threshold may or may not be in the neighbour list. State that the proposition is in exact arithmetic.
- The proof says ties are broken "by face id" (insertion-dependent), but the Corrections paragraph says must-link ties are broken "by the faces' content, not their ids". Use content-based tie-breaking everywhere; then the tie caveat disappears for equal-content faces.

**m2. The "keeps all corrections" claim holds only for consistent constraint sets.**
- The text states that in a conflict the less similar must-link is dropped. So with the error-prone user ("same person" wrong click plus an earlier cannot-link), a correction can be silently unmet. "Held 100%" should be conditioned on satisfiability. A one-clause caveat, plus how often it occurred in the 1,528 corrections, would suffice.

**m3. "Persistent corrections" and cluster identity.**
- The title promises persistence, but the most common real correction is naming a person and keeping that name attached to a group. The method yields partitions "up to renaming of clusters" (Proposition). How names or cluster ids map across recomputes is not discussed. Add one sentence or a limitation.

**m4. Unbounded accuracy wording in the abstract.**
- "it is the more accurate method on clean, blurred and dark photos". In the text only clean ($+0.0059$) has an interval, and it barely excludes zero. Blur ($+0.0038$) and dark ($+0.0022$) have none, and the paper says people-resampling widens intervals. Gaps of 0.002-0.006 on a metric near 0.99 are at the ceiling.
- Fix: "slightly ahead on clean photos (paired interval excludes zero); not distinguishable on most other conditions".

**m5. Metric choices.**
- The tuning objective is ARI, but results are reported as B-Cubed F1. B-Cubed is item-weighted, and the libraries hold 50-150 single-photo strangers whose singletons are easy, which compresses scores toward 1. The standard citation for B-Cubed properties is Amigó et al. (fine), but the original definition is Bagga and Baldwin 1998 (**unverified**).
- Face-clustering literature (Yang et al. 2019, Wang et al. 2019) reports pairwise F-score and B-Cubed on large sets. Report pairwise F or ARI alongside B-Cubed for comparability, or state why not.
- "Order agreement (lowest ARI between two orders)" is fine.

**m6. "Must-link and cannot-link constraints were brought to k-means [wagstaff2001copkmeans]".**
- Accurate (COP-KMeans, ICML 2001, pp. 577-584). Instance-level constraints were introduced by Wagstaff and Cardie, ICML 2000 (**unverified**), and the standard overview is Basu, Davidson and Wagstaff (eds.), *Constrained Clustering*, 2008 (**unverified**). Cite one of them for the origin.

**m7. "OGMC reduces order dependence for face streams [montero2022ogmc]" is accurate.**
- I checked the abstract via Consensus. It says "we reduce the dependency of the clustering process on the order and the size of the incoming data". No change needed. Consider saying "reduces, but does not remove, order dependence", since the paper's point is exact invariance.

**m8. The CRDT / local-first paragraph is accurate but compressed.**
- "Computing state from the set of inputs so that replicas that exchange inputs agree is the idea of CRDTs and local-first software." More precisely: the replicated state is the set (a G-Set or an observed-remove set), and the clustering is a deterministic query over it. Say "derived view of a replicated set".
- Kleppmann et al. 2019 is a vision/ideals paper, not a technique. That is fine as cited, but add the technique references (see missing list).
- Deletion-equals-retraining is a known framing in "machine unlearning" (Ginart et al. 2019, unverified), and the recheck file already planned to cite it.

**m9. "We did not find ... bounded to those sources".**
- Appropriately hedged. Two things to tighten:
  - It counts "mostly abstracts" as the depth. State that product behaviour (Immich, PhotoPrism, digiKam, Google Photos, Apple Photos) was read from documentation only, if that is the case.
  - Real products do persist confirmed identities (digiKam stores confirmed faces as tags; Immich keeps assigned people). The intro's "re-clustering from scratch does not take the user's earlier fixes as input" is true of the batch method, not of deployed products. The Immich-style frozen rule is exactly such a product behaviour, so the intro should say "a naive re-run".

**m10. Related-work dilution at the "incremental" end.**
- SLINK (Sibson 1973, **unverified**) is an exact, order-independent, incremental single-linkage algorithm. At the tuned $m=1$ the core step is single linkage, so SLINK is the closest classical ancestor. Dynamic-connectivity work for the deletion path (Holm, de Lichtenberg and Thorup 2001, **unverified**) would justify "rebuild union-find" as a simple choice rather than an oversight.
- Balcan and Blum 2008 and Awasthi et al. 2014/2017, on interactive split/merge feedback (**unverified**), are the closest theory for "users merge and split people by hand".

**m11. Unused bib entries, and one missing citation.**
- Entries never cited in the text: deng2019arcface, chen2018mobilefacenets, alansari2023ghostfacenets, moschoglou2017agedb, sengupta2016cfp, jung2025posetta, daniels2006threshold, vancraenendonck2017selection, song2006context, biswas2014active. IEEEtran/BibTeX will drop them, so this is harmless, but it means MobileFaceNets (evaluated as "MBF / w600k_mbf") and ArcFace (the training loss of that model) are not credited. Cite both where the second recogniser is introduced.
- biswas2014active (pairwise human constraints for image clustering, IJCV) belongs in the interactive-annotation sentence next to Tian and Cui.

**m12. Template placeholders.** The author block still has "[College name]", "[City]", "[email]", and "Author contributions: to be completed". Not my domain, but this must be resolved before submission.

## Bibliography spot-check (20 entries)

I compared fields with my own recollection of the records. No lookup tool was used except for OGMC.

| Entry | Result |
|---|---|
| deng2019arcface (CVPR 2019, pp. 4690-4699, DOI .00482) | consistent |
| guo2022scrfd (ICLR 2022) | consistent |
| chen2018mobilefacenets (CCBR 2018, LNCS 10996, pp. 428-438) | consistent |
| george2024edgeface (T-BIOM 6(2), pp. 158-168) | consistent |
| alansari2023ghostfacenets (IEEE Access 11, pp. 35429-35446) | consistent |
| ester1996dbscan (KDD, pp. 226-231) and ester1998incremental (VLDB, pp. 323-333) | consistent |
| campello2013hdbscan (PAKDD, LNCS 7819, pp. 160-172) | consistent |
| otto2018clustering (TPAMI 40(2), pp. 289-303) | consistent |
| wang2019linkage (pp. 1117-1125), yang2019affinity (pp. 2298-2306) | consistent |
| amigo2009bcubed (Inf. Retrieval 12(4), pp. 461-486) | consistent |
| hubert1985ari (J. Classification 2(1), pp. 193-218) | consistent |
| johnson2021faiss (IEEE Trans. Big Data 7(3), pp. 535-547) | consistent |
| shapiro2011crdt (SSS 2011, LNCS 6976, pp. 386-400) | consistent |
| kleppmann2019local (Onward! 2019, pp. 154-178) | consistent |
| gower1969mst (JRSS-C 18(1), pp. 54-64, DOI 10.2307/2346439) | consistent. The DOI is the JSTOR-style one. |
| davidson2005agglomerative (PKDD, LNCS 3721, pp. 59-70) | consistent |
| shi2018conpac (TIFS 13(7), pp. 1626-1640) | consistent |
| wagstaff2001copkmeans (ICML 2001, pp. 577-584) | consistent |
| monath2019grinch (KDD 2019, pp. 1438-1448) | fields consistent, **but see M1: the description of its content is the problem, not the record** |
| montero2022ogmc (EAAI 114, 105079) | abstract checked, matches the claim |

Flagged, **unverified**:
- filonenko2025facecluster: ACM MM 2025 demo pages 13546-13548 and DOI. A 2025 demo paper outside my knowledge. The audit marks it VERIFIED. Re-check the pages.
- jung2025posetta (unused).
- zheng2018cplfw (tech report number 18-01), zhu2016imperfect (the DOI year is 2014 while the volume is 2016, which is plausible for early access), mazumdar2017noisy (pages 5788-5799), lasek2019density (pages 469-489).

Format nits: the techreport/misc entries for LFW, CALFW and CPLFW are fine. The immich and photoprism `year = {2026}` with `note = Accessed Nov. 2026` is acceptable.

## Suggested missing references (all unverified unless stated)

1. Sibson 1973, SLINK, *The Computer Journal* 16(1): exact incremental single linkage. Unverified.
2. Johnson 1967, "Hierarchical clustering schemes", *Psychometrika*: single linkage and threshold-graph components. Unverified.
3. Wagstaff and Cardie 2000, "Clustering with instance-level constraints" (ICML/AAAI 2000), and Basu, Davidson and Wagstaff (eds.), *Constrained Clustering* (CRC, 2008). Unverified.
4. Balcan and Blum 2008, "Clustering with interactive feedback" (ALT); Awasthi, Balcan and Voevodski, "Local algorithms for interactive clustering" (ICML 2014; JMLR 2017). Unverified.
5. Kobren, Monath and McCallum 2019, "Integrating user feedback under identity uncertainty in knowledge base construction" (AKBC): the closest prior work on user feedback surviving re-resolution. Found in the round-5 recheck (abstract level only), not checked by me.
6. Maus and Borin 2026, arXiv 2604.11656 (exact HAC via connected components of a sparse graph); Dhulipala et al., ICML 2021 (sparse-graph HAC). Both found in the recheck file only.
7. Halkidi, Spiliopoulou and Pavlou, PAKDD 2012 (semi-supervised incremental clustering with a constraint stream). From the recheck file.
8. Ginart et al. 2019, "Making AI forget you: data deletion in machine learning" (NeurIPS); Cao and Yang 2015 (S&P). Deletion as "equal to retraining". Unverified.
9. Hellerstein and Alvaro 2020, "Keeping CALM: when distributed consistency is easy" (CACM). Explains why recompute-from-set is coordination-free and why removals need care. Unverified.
10. Almeida, Shoker and Baquero 2018, delta-state CRDTs (JPDC); Kleppmann and Beresford 2017, JSON CRDT (TPDS); Shapiro et al., INRIA RR-7506, 2011 (comprehensive CRDT study). Unverified.
11. Bagga and Baldwin 1998 (original B-Cubed, COLING-ACL). Unverified.
12. Holm, de Lichtenberg and Thorup 2001 (dynamic connectivity), for the deletion discussion. Unverified.
13. Recent face-clustering graph methods, if space allows: Yang et al. CVPR 2020 (confidence and connectivity); Guo et al. CVPR 2020 (density-aware embedding). Unverified.
14. Product evidence for "persisted identities" (digiKam, Apple's on-device people recognition write-up, 2021): check before citing. Unverified.

## Terminology and technical accuracy checklist

- "Exact split" and "exact read step": acceptable once M3 is fixed; say "identical partitions" rather than "exact" in the abstract-level statements.
- "Core face" with $m=1$ equals single linkage: correct, apart from isolated faces, which go to the attach step. The description is right.
- "Incremental DBSCAN ... up to border points": accurate.
- "Leader clustering [Hartigan 1975]": correct attribution.
- "Immich's default" at cosine $\ge0.5$: plausible (a cosine distance of 0.5); not verified here.
- B-Cubed and ARI usage: correct but see m5.
- "Average linkage" (faces) versus "average linkage over centroids" (ours): clarify (M3).
- "Order agreement (min)" for DBSCAN of 0.997: consistent with border-point dependence.

## Strengths

1. The prior-work posture is honest. The introduction says plainly that nothing in the parts is new, the Related Work sentence on novelty is bounded to the sources searched, and "Consequences" correctly states the result is not unique to this clusterer.
2. It reports where the method loses: CPLFW ($-6.8$ points to average linkage, with a stated precision/recall mechanism), low-res, MBF on occluded, wrong-click sensitivity at $p=0.2$, and the tie with constrained average linkage.
3. The fair-tuning and equal-tuning audit (finer baseline grids, a reduced-budget run for ours, people-level resampling) is better than most application papers in this area.
4. The experiments that distinguish the design are well chosen: retraction, deletion equal to rebuild, device agreement, and a recogniser-swap with a pre-registered subset (210 libraries).
5. The recompute-from-sets framing is a correct and useful engineering insight for local-first photo software. The paper does not oversell it as a protocol.
6. The bibliography is largely accurate, recently completed with volume, pages and DOI, and the added Gower-Ross entry is correct.

## Five-line summary (hand-back)
1. Weak accept, minor-to-moderate revision, confidence 4/5; prior-work claims are mostly accurate and well bounded (OGMC, Gower-Ross scoping and the bounded-search statement hold up).
2. MAJOR: GRINCH is cited as an example of constraints added to incremental hierarchical clustering, which it is not (M1); "this split is classical" overreaches for average linkage, and "average linkage over centroids" needs a precise definition for the exactness argument (M2, M3).
3. MAJOR: "converge across devices" and "devices that agree" claim more than a one-shot, no-protocol simulation supports (need set-merge with tombstones, stable face ids, replicated embeddings); the 53% frozen-baseline figure is a naive non-timestamped op log (M4, M5); incremental update holds only without corrections, and reads are full recomputes (M6).
4. MINOR: Proposition is bookkeeping equal to a batch method (state exact-arithmetic and content-based ties), "keeps all corrections" holds for consistent sets, accuracy wording at the 0.002 level, B-Cubed saturation, cluster naming not handled.
5. Missing references (all unverified by me except the OGMC check): SLINK, interactive split/merge feedback theory, Kobren et al. AKBC 2019, Maus and Borin / Dhulipala, machine unlearning, CALM and delta-CRDTs; about 20 bib entries spot-checked, none with an obviously wrong field.
