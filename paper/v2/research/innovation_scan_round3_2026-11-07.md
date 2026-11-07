# Innovation scan, round 3 — G3 "corrections that teach the whole library" (deep-research, full mode, integrative scan)

Date: 2026-11-07. Same method and limits as rounds 1-2: SciSpace + Consensus + web, **abstracts only**, one reviewer,
"not found" is bounded to the queries listed. The author confirmed the RQ ("proceed"). Review-form note: already answered
(skip) earlier in this project, not shown again.

## RQ (confirmed)
Has prior work used a user's must-link / cannot-link corrections to **re-estimate the clustering thresholds for that user's
own library**, so that faces the user never corrected are grouped better — in particular in an incremental, order-invariant
face clusterer? Which components are known and which are not found?

## Queries (9)
1. must-link / cannot-link constraints to learn the metric or similarity threshold (SciSpace)
2. interactive face clustering where user feedback improves the remaining faces (SciSpace)
3. user corrections in personal-album face clustering adapting the threshold or model (SciSpace)
4. selecting the HAC threshold / number of clusters from a few pairwise constraints (SciSpace)
5. adapting a face-verification threshold to a new gallery/user from a few labelled pairs (SciSpace)
6. incremental / online constrained clustering that updates parameters as constraints arrive (SciSpace)
7. face clustering threshold adapted from user feedback in personal photo collections (Consensus)
8. recent (2019-2026) face clustering using human feedback to adjust the linking threshold (SciSpace)
9. patents: face clustering threshold adjusted from user merge/split corrections (web)

## Findings by component

| # | Component of G3 | Prior art found (abstract level) | Verdict |
|---|---|---|---|
| C1 | Learn the similarity from must-link / cannot-link | Wang, Chen & Zhang 2008 (CIKM); Soleymani Baghshah & Bagheri Shouraki 2009 (IJCAI); Conroy et al. 2010 (boosting a similarity from constraints); Davidson 2009/2018 survey ("constraints used to learn a distance function") | **Known** |
| C2 | Use constraints / a few labels to **choose the threshold or hyper-parameters** of an unsupervised clusterer | **Daniels & Giraud-Carrier 2006** ("Learning the threshold in hierarchical agglomerative clustering" from a small labelled subset, F-measure); **Van Craenendonck & Blockeel 2016/2017** (constraints used to select the clustering method *and tune its hyper-parameters*; beats semi-supervised methods) | **Known — this is the core of G3** |
| C3 | Personal photo albums: user merge/split edits → constraints → learned metric → re-cluster | **Ji, Wang & Tian 2010** (VCIP, semi-automatic photo clustering with distance metric learning); Wang et al. "Intelligent photo clustering with user interaction and distance metric learning" (Move/Split/Merge edits → metric; year per search listing 2011); Saboorian et al. 2010 (user feedback sets number of clusters and feature weights); Hu et al. 2018 (per-user model learned online from feedback, growing collections) | **Known** (general photos; face-specific listed below) |
| C4 | Face clustering with a human in the loop | Tian et al. 2007 (CVPR, partial clustering + interactive labelling); Cui et al. 2007 (EasyAlbum, CHI); Song & Leung 2006 (constrained spectral clustering with user feedback); Barr et al. 2014 (active face clustering, TIFS); Zhang, Kalashnikov & Mehrotra 2014 (human-in-the-loop; learns adaptive merge rules); Han, Hu & Deng 2016 (constrained spectral clustering in a face annotation system); Xu et al. 2017 (Face Album, mobile, user corrections); FaceCluster 2025 | **Known** (constraints/feedback used; none of these abstracts state a per-library threshold re-estimated from corrections) |
| C5 | Per-user / per-gallery threshold adaptation in face verification | Poh & Bengio 2005 (client-dependent threshold normalisation, F-Norm); Chou et al. 2018 (data-specific adaptive threshold for face recognition); Li et al. 2013 (CVPR, locally adaptive decision functions) | **Known** (verification, not clustering) |
| C6 | Incremental clustering with constraints added over time | Davidson, Ravi & Ester 2007 (KDD, incremental constrained clustering from user critique); Yi et al. 2015 (sequential constraints); Lafabregue et al. 2022 (I-SAMARAH); Beauchamp 2025 (thesis, incremental and active user feedback) | **Known** |
| C7 | **Combination:** per-library threshold re-estimation from corrections, inside an *order-invariant incremental* face clusterer whose corrections persist across new photos, scored on the *uncorrected* faces under an identity-disjoint protocol | — | **Not found in the searched sources** — but it is an application of C2 to Cove's clusterer, not a new mechanism |

## Devil's-advocate checkpoint 2: REVISE the claim (not the experiment)
1. **Cherry-picking check:** the counter-evidence search found direct prior art for the core step (C2). G3 cannot be called a new
   method. The honest framing is "we apply constraint-based threshold selection (Daniels & Giraud-Carrier 2006; Van Craenendonck
   & Blockeel 2017) per library, online, in an order-invariant clusterer".
2. **What remains new is narrow:** the setting (incremental + order-invariant + persistent corrections) and the evaluation
   (gain on *uncorrected* faces, identity-disjoint). A reviewer could call it "obvious once you have constraints".
3. **Risk of no effect:** with 10 corrections per library, the threshold estimate rests on ~10 pairs; noise may cancel the gain.
   Exp14 tuning already found a good global threshold, so headroom may be small (as with exp17 in family-sized libraries).
4. **Risk of harm:** loosening the threshold from a few must-links can cause chaining (the exp16 lesson). Precision must be
   reported separately.

## Ranked conclusion
| Idea | Novelty | Value | Recommendation |
|---|---|---|---|
| G3 as a *novelty claim* | Low (core step is prior art) | — | Do **not** present as an innovation |
| G3 as an *engineering add-on* to the corrections feature | Application of known method | Possible accuracy gain on uncorrected faces | Optional half-day test; report either way, cite C2 papers |
| Main paper contribution (unchanged) | Corrections that persist + order-invariance (round-1 G4) | Measured, real data | Keep as headline |

## Phase 5 (inline)
Editor: minor revision — the report is decision-ready; the per-component table is the key output. Ethics: CLEARED — public
literature only, no data collected. DA checkpoint 3: strongest counter-argument to *running* G3 at all — "it adds a known
technique to a paper whose novelty is elsewhere"; answer: only worth it if the user wants the product gain; it must not be
listed as a contribution.

AI disclosure: AI-assisted search, screening and synthesis (Claude, academic-research-skills deep-research). Abstract-level
reading only; the author should verify sources before citing.

## Sources (abstract level; found via the search tools)
- Barr, J. R., Bowyer, K. W., & Flynn, P. J. (2014). Framework for active clustering with ensembles. IEEE TIFS. https://scispace.com/papers/framework-for-active-clustering-with-ensembles-4tgvv1i0o5
- Beauchamp, A. (2025). Clustering sous contraintes : intégration incrémentale et active des retours utilisateur (thesis). https://scispace.com/papers/clustering-sous-contraintes-integration-incrementale-et-fbq3vu4qtupd
- Chou, H.-R., Lee, J.-H., & Chan, Y.-M. (2018). Data-specific adaptive threshold for face recognition and authentication. arXiv. https://scispace.com/papers/data-specific-adaptive-threshold-for-face-recognition-and-23s8yl74sl
- Conroy, B., Xi, Y. T., & Ramadge, P. J. (2010). A supervisory approach to semi-supervised clustering. ICASSP. https://scispace.com/papers/a-supervisory-approach-to-semi-supervised-clustering-1s4ixwjnk1
- Cui, J., Wen, F., Xiao, R., et al. (2007). EasyAlbum: An interactive photo annotation system based on face clustering and re-ranking. CHI. https://scispace.com/papers/easyalbum-an-interactive-photo-annotation-system-based-on-2bhbm6rwmi
- Daniels, K., & Giraud-Carrier, C. (2006). Learning the threshold in hierarchical agglomerative clustering. ICMLA. https://scispace.com/papers/learning-the-threshold-in-hierarchical-agglomerative-xloj17fhyq
- Davidson, I. (2009/2018). Clustering with constraints. https://scispace.com/papers/clustering-with-constraints-2tp8924fg7
- Davidson, I., Ravi, S. S., & Ester, M. (2007). Efficient incremental constrained clustering. KDD. https://scispace.com/papers/efficient-incremental-constrained-clustering-3gvu2vtion
- Filonenko, A., Makarov, I., & Savchenko, A. V. (2025). FaceCluster: Interactive photo organization with enhanced face recognition. https://scispace.com/papers/facecluster-interactive-photo-organization-with-enhanced-h0wld6u3yfpf
- Han, J., Hu, J., & Deng, W. (2016). Constrained spectral clustering on face annotation system. CCPR. https://scispace.com/papers/constrained-spectral-clustering-on-face-annotation-system-2trycmji1f
- Hu, J., Sun, Z., Sun, Y., et al. (2018). Accumulative image categorization: A personal photo classification method for progressive collection. MTAP. https://scispace.com/papers/accumulative-image-categorization-a-personal-photo-35a8k69py4
- Ji, D., Wang, M., & Tian, Q. (2010). Semi-automatic photo clustering with distance metric learning. VCIP. https://scispace.com/papers/semi-automatic-photo-clustering-with-distance-metric-1cgfh6ij9p
- Lafabregue, B., Gançarski, P., Weber, J., et al. (2022). Incremental constrained clustering with application to remote sensing images time series. ICDMW. https://scispace.com/papers/incremental-constrained-clustering-with-application-to-3pwdpnn7
- Li, Z., Chang, S., Liang, F., et al. (2013). Learning locally-adaptive decision functions for person verification. CVPR. https://scispace.com/papers/learning-locally-adaptive-decision-functions-for-person-4fyunv59os
- Poh, N., & Bengio, S. (2005). F-ratio client dependent normalisation for biometric authentication tasks. ICASSP. https://scispace.com/papers/f-ratio-client-dependent-normalisation-for-biometric-2m636zdrzx
- Saboorian, M. M., Jamzad, M., & Rabiee, H. R. (2010). User adaptive clustering for large image databases. ICPR. https://scispace.com/papers/user-adaptive-clustering-for-large-image-databases-2707ff4ipy
- Soleymani Baghshah, M., & Bagheri Shouraki, S. (2009). Semi-supervised metric learning using pairwise constraints. IJCAI. https://scispace.com/papers/semi-supervised-metric-learning-using-pairwise-constraints-2hcoji2znq
- Song, Y., & Leung, T. (2006). Context-aided human recognition – clustering. https://consensus.app/papers/details/521c45f1b6fb5df89a165db2e653ac3e/
- Tian, Y., Liu, W., Xiao, R., et al. (2007). A face annotation framework with partial clustering and interactive labeling. CVPR. https://scispace.com/papers/a-face-annotation-framework-with-partial-clustering-and-4jhvxjnm4h
- Van Craenendonck, T., & Blockeel, H. (2017). Constraint-based clustering selection. Machine Learning. https://scispace.com/papers/constraint-based-clustering-selection-2amttxwgct
- Wang, F., Chen, S., & Zhang, C. (2008). Semi-supervised metric learning by maximizing constraint margin. CIKM. https://scispace.com/papers/semi-supervised-metric-learning-by-maximizing-constraint-3qm47ou9xt
- Wang, M., et al. Intelligent photo clustering with user interaction and distance metric learning (listed as 2011; bibliographic details to verify). https://www.bohrium.com/paper-details/intelligent-photo-clustering-with-user-interaction-and-distance-metric-learning/811679154947751937-2594
- Xu, Y., Peng, F., Yuan, Y., et al. (2017). Face Album: Towards automatic photo management based on person identity on mobile phones. ICASSP. https://scispace.com/papers/face-album-towards-automatic-photo-management-based-on-xfth79zudt
- Yi, J., Zhang, L., Yang, T., et al. (2015). An efficient semi-supervised clustering algorithm with sequential constraints. KDD. https://scispace.com/papers/an-efficient-semi-supervised-clustering-algorithm-with-bkaiy5m8ti
- Zhang, L., Kalashnikov, D. V., & Mehrotra, S. (2014). Context-assisted face clustering framework with human-in-the-loop. IJMIR. https://scispace.com/papers/context-assisted-face-clustering-framework-with-human-in-the-4m7akdetje
