# Round 6 - Domain Reviewer (R2), simulated re-review of commit 000152d

Recommendation: MINOR REVISION (weak accept). Confidence 4/5.
Prior-art claims are now properly bounded and the two wrong ones from round 5 are corrected. What remains is wording around "convergence", the incremental/read distinction, and a few missing neighbours. I read the tex and the bib in full. I did not re-verify external records (no lookup tools); items I could not check are marked unverified.

## Prior issues
M1 GRINCH mis-described: FIXED. It is now cited only for "incremental hierarchical clustering can repair earlier merges", which is what it does.
M2 "Classical" split overreach: FIXED. The text says the split is classical for single linkage (Gower-Ross, SLINK) and, for this average linkage, follows from the "mean cannot exceed its largest term" argument, used for speed.
M3 Meaning of "average linkage over centroids": MOSTLY FIXED. The text now says each centroid is one item and the group similarity is the mean of pairwise centroid cosines. That is UPGMA on fixed items, and the argument is correct. Still unsaid: the "Avg. linkage" baseline is over faces, ours over centroids.
M4 "Converge across devices": PARTLY. The Fig. 1 caption says "simulated; no sync", and Scope lists tombstones as untested. Related Work still says "converge across devices". Stable ids and replicated embeddings (float32 differences between CPUs affect threshold decisions) are not listed as requirements.
M5 53% frozen baseline: FIXED in wording ("of our design", "plain edit log, not a deployed sync"). A timestamped last-writer-wins variant is still missing, but the limitation is disclosed.
M6 Incremental only without corrections: PARTLY. "Attachment and the merge are recomputed when labels are read" is stated. Not stated: with corrections, steps (1) and (2) are a greedy Kruskal pass redone at every read. "No earlier decision is undone" is true only for the correction-free union.
m1 Proposition scope: PARTLY. "Exact arithmetic" was added. The tie rule is still inconsistent: the proof says ties break by face id, the Corrections paragraph says by content. Contribution 1 still lacks "(as does any batch method)".
m2 "Keeps every correction": FIXED by "consistent". How often a must-link was dropped in the 1,528 corrections is still not reported.
m3 Cluster naming/identity under "persistent corrections": NOT FIXED.
m4 Abstract accuracy wording: FIXED. Now "ahead on clean, behind on low-res and profile".
m5 Metrics: PARTLY. Bagga and Baldwin is now cited. No pairwise F-score, and the B-Cubed ceiling effect from single-photo strangers is not discussed.
m6 Wagstaff and Cardie 2000 / Basu et al. 2008: NOT FIXED (low priority).
m7 OGMC wording: accurate, no change needed.
m8 CRDT wording: NOT FIXED. "Derived view of a replicated set" is not used. Machine unlearning and CALM are not cited.
m9 Products: PARTLY. The search is bounded and the frozen rule is called our design. Real products persist confirmed identities, and the Introduction's "the same mistakes return" is true only of a naive re-run.
m10 SLINK: PARTLY. It is cited but only as "classical". Add that SLINK is the exact incremental single-linkage ancestor. Interactive split/merge theory (Balcan-Blum, Awasthi et al.) is still absent.
m11 Unused bib entries: NOT FIXED. 10 are uncited (ArcFace, MobileFaceNets, GhostFaceNets, AgeDB, CFP, posetta, daniels, vancraenendonck, song, biswas). BibTeX drops them, but MBF (MobileFaceNet / w600k) and its loss are therefore uncredited.
m12 Placeholders: NOT FIXED.

## New issues
N1 MINOR - Related Work. "Incremental DBSCAN gives the result of re-running DBSCAN after each insertion". Ester et al. 1998 also handles deletions. This matters because "exact handling of deleted photos" is presented as a result. Fix: "after each insertion or deletion; ours recomputes after deletion instead".
N2 MINOR - Introduction. bandyopadhyay2016axioms is cited as "order-independent incremental clustering". I could not confirm that paper's claim at this level (unverified). Check the abstract. If it only characterises incremental algorithms by axioms, reword to "axioms for incremental clustering".
N3 MINOR - Method. "Splitting a linkage clustering at the components of a threshold graph" does not say that for average linkage this is the paper's own argument. The Method paragraph does say it. Make the Related Work sentence say "single linkage".
N4 MINOR - Related Work. Kobren et al. (AKBC 2019) on user feedback surviving re-resolution is the closest prior work on "corrections survive re-clustering" (unverified). It is still not cited, and the novelty sentence is bounded to a search that may have missed it. Cite it or say it was found and differs.
N5 MINOR - Protocol. The frozen rule's "cosine 0.5, Immich's default threshold" is uncited and unverified. Cite the Immich docs or drop the attribution.
N6 MINOR - Method, Exact read step. "Identical partitions under real corrections ... changed the result in all but one of 1,276 cases" is dense and the counts are unexplained. Move the count to a footnote-style clause.

## Citation accuracy
No wrong or fabricated attribution found. Reference-list nits: 40 cited entries, none missing. The Immich and PhotoPrism entries are repository links with an access date, which is acceptable. filonenko2025facecluster pages and DOI are still unverified by me.

## Novelty bounding
Good. "We claim none of them", "application-and-measurement study", and the search statement are all limited to the sources searched. Consequences (i) to (iii) correctly say the properties hold for any recompute-from-sets method. The novelty claim reduces to a measurement on one clusterer, which is honestly framed.

## Summary
Minor revision, confidence 4/5. No CRITICAL or MAJOR issues remain. The most useful remaining edits are N1, "converge" to "agree", the explicit read-step-is-full-recompute sentence, and a consistent tie rule.
