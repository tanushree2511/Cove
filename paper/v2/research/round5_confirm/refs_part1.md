# Reference audit, round 5, part 1 (23 keys)

Date of audit: 2026-11-10. Read-only audit; no existing file was edited.
Scope: `references.bib` entries listed below, checked against `cove_paper.tex`.

## Method and limits (read first)

- Bibliographic metadata was taken from the Crossref REST API (publisher-deposited records, `api.crossref.org/works?...` and `/works/<doi>`), the CVF Open Access pages, arXiv, GitHub (web page, REST API and raw README), Consensus and SciSpace search results, and the vldb.org mirror of the dblp record.
- dblp.org itself, the ACM Digital Library and Springer link pages could not be opened (bot challenge, HTTP 403, or redirect to a login flow). I did not try to get around this. Where dblp content is cited it came from a search-result summary or the vldb.org dblp mirror, and I say so.
- Description checks are mostly ABSTRACT-ONLY (full texts are paywalled or scanned images). Every description verdict below is abstract-level unless it says otherwise.
- Verdict scheme (strict):
  - VERIFIED = work exists, every field present in the .bib is correct, the paper's sentence is not misleading. Missing DOI/publisher only is listed as an optional addition and does not change the verdict.
  - PARTLY = work exists, but at least one of: a present field is wrong; volume/issue/pages/article number is missing (IEEE style prints them); the paper's sentence needs rewording.
  - UNVERIFIED = could not confirm the work exists. None in this batch.

## Summary table

| key | exists + evidence | bib mismatches / missing fields (corrected values) | paper's description (quoted, <=25 words) and judgement | verdict |
|---|---|---|---|---|
| immich | Yes. GitHub repo `immich-app/immich`: https://github.com/immich-app/immich ; REST API (https://api.github.com/repos/immich-app/immich) shows created 2022-02-03, not archived, AGPL-3.0, description "High performance self-hosted photo and video management solution", latest release v3.3.6 published 2026-11-04. README feature table lists "Facial recognition and clustering". Docs (https://docs.immich.app/features/facial-recognition) describe an incremental DBSCAN-derived face grouping run by a separate machine-learning service. | Title is a paraphrase: official tagline has no "Immich:" prefix and reads "High performance ... management solution" (bib: "High-Performance ... Management"). No version given although releases exist (latest on audit date v3.3.6, 2026-11-04). URL, year 2026 and "Accessed Nov. 2026" are fine. | "local-first managers such as Immich, PhotoPrism, FaceCluster and the Cove system ... do it on the user's own hardware, so neither photos nor embeddings leave the device." OVERSTATED. Immich is a self-hosted server (phone app uploads to the user's server; ML runs in a separate service), not "local-first" in the device sense, and photos do leave the phone. "User's own hardware" is fine. | PARTLY |
| photoprism | Yes. GitHub repo `photoprism/photoprism`: https://github.com/photoprism/photoprism ; API shows created 2018-01-27, not archived, description "AI-Powered Photos App", latest release 261029-963b58c50 (2026-10-29). README: "AI-powered, privacy-first app ... whether self-hosted or in the cloud". Docs (https://docs.photoprism.app/user-guide/organize/people/) say faces are detected and grouped by similarity. | Bib title "AI-Powered Photos App for the Decentralized Web" is an older tagline (still seen on mirrors, e.g. gitea/SourceForge copies); the upstream repo description today is "AI-Powered Photos App" and the README H1 is "PhotoPrism: Browse Your Life in Pictures". No version. | Same sentence as above. OVERSTATED for the same reason; also PhotoPrism is offered "self-hosted or in the cloud", so "on the user's own hardware" holds only for the self-hosted mode. | PARTLY |
| filonenko2025facecluster | Yes. Crossref: https://api.crossref.org/works/10.1145/3746027.3754485 ("Proceedings of the 33rd ACM International Conference on Multimedia", pp. 13546-13548, issued 2025-10-27; authors Filonenko, Makarov, Savchenko). Also SciSpace record and a dblp record `conf/mm/FilonenkoMS25` (seen in search results, same pages). | Title, 3 authors, year, pages match. Missing (optional): DOI 10.1145/3746027.3754485. Booktitle should read "Proc. 33rd ACM Int. Conf. Multimedia (MM)". "Demo Track" label: abstract says "The demo showcases...", and 3 pages is consistent with a demo; I could not see the track name on a listing page. | "FaceCluster is a recent local, interactive photo organizer." CORRECT (abstract: "interactive photo management system ... operates entirely locally"). Abstract-only. | VERIFIED |
| hartigan1975clustering | Yes. Open Library record: Hartigan, John A., "Clustering algorithms", Wiley, 1975, ISBN 047135645X / 9780471356455 (https://openlibrary.org/search.json?q=title%3A%22Clustering+algorithms%22+author%3AHartigan). Crossref also holds a 1975 JSTOR review of the book (10.2307/2529577). | Matches (author, title, Wiley, New York, 1975). Optional: `isbn = {047135645X}`. Book not opened. | "cheapest update is a greedy leader pass: a new face joins the most similar cluster above a threshold or starts a new one." CORRECT per secondary sources (R package docs for Hartigan's leader algorithm, e.g. https://rdrr.io/pkg/leaderCluster/man/leaderCluster.html: one pass, new leader if not within radius r, else nearest leader; result depends on data order). Book text itself not read. | VERIFIED |
| wagstaff2001copkmeans | Yes. https://mlanthology.org/icml/2001/wagstaff2001icml-constrained/ (ICML 2001, pp. 577-584, Wagstaff, Cardie, Rogers, Schroedl); PDF at https://www.wkiri.com/research/papers/wagstaff-kmeans-01.pdf (seen in search results). | All fields match. | "Must-link and cannot-link constraints were introduced for k-means." OVERSTATED. The constraint types were introduced in Wagstaff and Cardie, "Clustering with Instance-Level Constraints", ICML 2000, pp. 1103-1110 (COP-COBWEB); the 2001 paper brings them to k-means (COP-KMeans). Source: search-result summaries of https://mlanthology.org/icml/2000/wagstaff2000icml-clustering/ and https://www.wkiri.com/research/papers/wagstaff-constraints-00.pdf (not opened; a same-titled AAAI-00 record at p. 1097 also exists). The 2001 abstract itself does not mention must-link/cannot-link. | PARTLY |
| davidson2005agglomerative | Yes. Crossref DOI 10.1007/11564126_11, LNCS "Knowledge Discovery in Databases: PKDD 2005", pp. 59-70, 2005. LNCS vol. 3721 confirmed via search results (Springer book 10.1007/11564126; ISBN 978-3-540-29244-9). SciSpace abstract: "We explore the use of instance and cluster-level constraints with agglomerative hierarchical clustering". | All fields match. Missing (optional): `doi = {10.1007/11564126_11}`. Note a journal extension exists: Data Min. Knowl. Discov. 18(2):257-282, 2009, DOI 10.1007/s10618-008-0103-4. | "studied for agglomerative clustering" and "constrained average linkage ... after [davidson2005]". CORRECT (abstract-only). | VERIFIED |
| davidson2007incremental | Yes. Crossref DOI 10.1145/1281192.1281221, Proc. 13th ACM SIGKDD, pp. 240-249, 2007-08-12; authors Davidson, Ravi, Ester. Abstract via Consensus. | All fields match. Optional: `doi = {10.1145/1281192.1281221}`. | "Davidson et al. update a clustering as a user adds constraints over time." CORRECT (abstract: "constraints are incrementally given ... efficiently updating a clustering ... rather than reclustering"). Intro "its incremental form" also CORRECT. | VERIFIED |
| tian2007face | Yes. Crossref DOI 10.1109/CVPR.2007.383282, "2007 IEEE Conference on Computer Vision and Pattern Recognition", pp. 1-8, 2007-06; authors Tian, Liu, Xiao, Wen, Tang. Abstract via Consensus. | Title, 5 authors, venue, year match. Missing: `pages = {1--8}`, `doi = {10.1109/CVPR.2007.383282}`. | "interactive face annotation [tian, cui]" and "let users label or correct face groups and propagate the labels". CORRECT (abstract: partial clustering for initial labeling, then interactive labeling to cut user operations). | PARTLY (pages missing) |
| cui2007easyalbum | Yes. Crossref DOI 10.1145/1240624.1240684, CHI 2007, pp. 367-376, 2007-04-29; authors Cui, Wen, Xiao, Tian, Tang. Abstract via Consensus. | Title, 5 authors, venue, year match. Missing: `pages = {367--376}`, `doi = {10.1145/1240624.1240684}`. | Same sentences as tian2007face. CORRECT (abstract: "cluster annotation ... ad hoc annotation ... learning propagation"). | PARTLY (pages missing) |
| otto2018clustering | Yes. Crossref DOI 10.1109/tpami.2017.2679100: IEEE TPAMI vol. 40, no. 2, pp. 289-303, Feb 2018; authors Otto, Wang, Jain. arXiv 1604.00989. | Exact match on all fields (authors, title, journal, volume 40, number 2, pages 289-303, year 2018, DOI). | "Large-scale face clustering uses approximate rank-order distances." CORRECT (abstract of the paper: approximate Rank-Order clustering using approximate nearest neighbours). | VERIFIED |
| wang2019linkage | Yes. CVF page https://openaccess.thecvf.com/content_CVPR_2019/html/Wang_Linkage_Based_Face_Clustering_via_Graph_Convolution_Network_CVPR_2019_paper.html : pp. 1117-1125, authors Wang, Zheng, Li, Wang. Crossref DOI 10.1109/CVPR.2019.00121 (pages 1117-1125). | All present fields match. Missing (optional): `doi = {10.1109/CVPR.2019.00121}`. | "graph networks that predict links on a k-nearest-neighbour graph ... need labelled training clusters and usually a GPU." Link-prediction part CORRECT (abstract: "formulate this task as a link prediction problem ... sub-graphs around each instance ... GCN"). "Labelled training" is implied (supervised GCN); "usually a GPU" is CANNOT-TELL from the abstract. | VERIFIED |
| yang2019affinity | Yes. CVF page https://openaccess.thecvf.com/content_CVPR_2019/html/Yang_Learning_to_Cluster_Faces_on_an_Affinity_Graph_CVPR_2019_paper.html (6 authors as in the bib; page meta citation_firstpage 2298, citation_lastpage 2306). Crossref DOI 10.1109/CVPR.2019.00240. | Bib pages 2298-2306 match the CVF page. Crossref / IEEE Xplore deposits 2293-2301 for the same DOI, so the two sources disagree; keep one convention (CVF's 2298-2306 is what the bib uses). Missing (optional): `doi = {10.1109/CVPR.2019.00240}`. | "graph networks that predict links on a k-nearest-neighbour graph" (cites wang and yang). OVERSTATED for Yang et al. Their abstract: "a framework based on graph convolutional network, which combines a detection and a segmentation module to pinpoint face clusters" (cluster proposals, not link prediction). | PARTLY (wording) |
| ester1996dbscan | Yes. AAAI page https://aaai.org/papers/kdd96-037-a-density-based-algorithm-for-discovering-clusters-in-large-spatial-databases-with-noise/ (KDD-96, 2nd Int. Conf. on Knowledge Discovery and Data Mining). BibBase record (https://bibbase.org/network/publication/ester-kriegel-sander-xu-adensitybasedalgorithmfordiscoveringclustersinlargespatialdatabaseswithnoise-1996): pp. 226-231, AAAI Press, Portland, Oregon, 1996. | All fields match. Optional: `publisher = {AAAI Press}`, `address = {Portland, OR}`. | Cited as the DBSCAN baseline. CORRECT. | VERIFIED |
| campello2013hdbscan | Yes. Crossref DOI 10.1007/978-3-642-37456-2_14, pp. 160-172, 2013; authors Campello, Moulavi, Sander; book is "Advances in Knowledge Discovery and Data Mining, PAKDD 2013, Part II" = LNCS 7819 (search results for Springer book 10.1007/978-3-642-37456-2). SciSpace abstract: hierarchical density-based method with cluster stability measure. | All fields match (booktitle PAKDD, LNCS 7819, pp. 160-172, 2013). Missing (optional): `doi = {10.1007/978-3-642-37456-2_14}`. | Cited as the HDBSCAN baseline. CORRECT. | VERIFIED |
| ester1998incremental | Yes. vldb.org dblp mirror https://vldb.org/dblp/db/conf/vldb/EsterKSWX98.html : 5 authors, VLDB 1998 (24th, New York), pp. 323-333. Abstract via search results: incremental DBSCAN "yields the same result as DBSCAN" (provable from the cluster definition). | All fields match. | "Incremental DBSCAN showed that inserting a point changes clusters only locally and gives the same result as re-running DBSCAN (up to the assignment of border points)." CORRECT for the main claim (abstract-only). The "up to border points" parenthetical could not be checked (the VLDB PDF is a scanned image); it is a conservative hedge, low risk. | VERIFIED |
| ruiz2007cdbscan | Yes. Crossref DOI 10.1007/978-3-540-72530-5_25, "Rough Sets, Fuzzy Sets, Data Mining and Granular Computing", pp. 216-223, 2007, Springer; authors Ruiz, Spiliopoulou, Menasalvas. LNCS 4482 from search-result summary of the Springer record. | All fields match. | "Constraints have also been added to density-based clustering (C-DBSCAN ...)". CORRECT (abstract: extends DBSCAN with must-link/cannot-link instance constraints). | VERIFIED |
| ruiz2009cdenstream | Yes. Crossref DOI 10.1007/978-3-642-04747-3_23, "Discovery Science", pp. 287-301, 2009; authors Ruiz, Menasalvas, Spiliopoulou. LNCS 5808 from search-result summary. | All fields match. | "its stream version C-DenStream". CORRECT (abstract: density-based stream clustering with domain-knowledge constraints). | VERIFIED |
| lasek2019density | Yes. Crossref DOI 10.2298/csis180601007l: Comput. Sci. Inf. Syst. vol. 16, no. 2, pp. 469-489, 2019; authors Lasek, Gryz. Page https://geodesic.mathdoc.fr/item/CSIS_2019_16_2_a7 (ic-NBC and ic-DBSCAN with must-link/cannot-link). | Authors, title, journal, vol 16, no 2, year, DOI match. Missing: `pages = {469--489}`. | "and later work [lasek]" on constraints in density-based clustering. CORRECT (abstract: ic-DBSCAN / ic-NBC with instance-level constraints). | PARTLY (pages missing) |
| monath2019grinch | Yes. Crossref DOI 10.1145/3292500.3330929, Proc. 25th ACM SIGKDD, pp. 1438-1448, 2019-07-25; 5 authors match. arXiv 2001.00076. | All fields match. | "incremental hierarchical clustering can repair earlier merges as points arrive" and "Grinch's guarantee needs a separability condition". CORRECT (abstract/search summary: rotations and global grafting; guarantee under a separability notion for linkage functions). | VERIFIED |
| shi2018conpac | Yes. Crossref DOI 10.1109/tifs.2018.2796999; arXiv 1706.05067 (journal-ref: IEEE TIFS vol. 13, issue 7, July 2018). | Authors, title, journal, year, DOI match. Missing: `volume = {13}`, `number = {7}`, `pages = {1626--1640}`. | "pairwise constraints have been used in clustering by Shi et al." CORRECT (abstract: ConPaC "can naturally incorporate pairwise constraints to obtain a semi-supervised version"). | PARTLY (vol/no/pages missing) |
| wu2013constrained | Yes. CVF page https://openaccess.thecvf.com/content_cvpr_2013/html/Wu_Constrained_Clustering_and_2013_CVPR_paper.html : pp. 3507-3514, authors Wu, Zhang, Hu, Ji. Crossref DOI 10.1109/cvpr.2013.450. | Exact match on all fields. | "and, from video tracks, by Wu et al." CORRECT (abstract: pairwise constraints "obtained from the temporal and spatial knowledge of the face tracks", HMRF clustering). | VERIFIED |
| bandyopadhyay2016axioms | Yes. Crossref DOI 10.1109/icpr.2016.7899675: ICPR 2016 (23rd), pp. 450-455, Dec 2016; authors Bandyopadhyay **Sambaran**, Murty M Narasimha. Abstract via Consensus. | **Wrong first name:** bib has "Bandyopadhyay, Sanghamitra"; correct is "Bandyopadhyay, Sambaran" (Crossref deposit; search summaries say IBM Research). Title, venue, year, pages match. Missing (optional): `doi = {10.1109/ICPR.2016.7899675}`. | "Order-independent incremental clustering is known without corrections." CORRECT (abstract: "an order independent incremental clustering algorithm which satisfies all of these axioms in some constrained manner"). | PARTLY (author name wrong) |
| montero2022ogmc | Yes. Crossref DOI 10.1016/j.engappai.2022.105079: Eng. Appl. Artif. Intell. vol. 114, article 105079, Sept 2022; 4 authors match. arXiv 2103.17272 (https://arxiv.org/abs/2103.17272). | Authors, title, journal, year, DOI match. Missing: `volume = {114}`, article number `pages = {105079}` (or `articleno`). | "OGMC clusters face streams online and reports reduced order dependence." CORRECT (abstract: "continuous stream of unknown faces ... we reduce the dependency of the clustering process on the order and the size of the incoming data"). | PARTLY (volume/article no. missing) |

## Counts

- VERIFIED: 13 (filonenko2025facecluster, hartigan1975clustering, davidson2005agglomerative, davidson2007incremental, otto2018clustering, wang2019linkage, ester1996dbscan, campello2013hdbscan, ester1998incremental, ruiz2007cdbscan, ruiz2009cdenstream, monath2019grinch, wu2013constrained)
- PARTLY: 10 (immich, photoprism, wagstaff2001copkmeans, tian2007face, cui2007easyalbum, yang2019affinity, lasek2019density, shi2018conpac, bandyopadhyay2016axioms, montero2022ogmc)
- UNVERIFIED: 0

No fabricated or non-existent reference was found in this batch. The one hard factual error in the .bib is the first name in bandyopadhyay2016axioms.

## Fix list for references.bib (exact corrected fields)

```bibtex
% hard error
@inproceedings{bandyopadhyay2016axioms,
  author    = {Bandyopadhyay, Sambaran and Murty, M. Narasimha},   % was: Sanghamitra
  doi       = {10.1109/ICPR.2016.7899675},                           % add
  ...unchanged...
}

% missing volume / issue / pages (journal articles)
@article{shi2018conpac,
  volume = {13},
  number = {7},
  pages  = {1626--1640},
  ...}
@article{montero2022ogmc,
  volume = {114},
  pages  = {105079},      % article number
  ...}
@article{lasek2019density,
  pages = {469--489},
  ...}

% missing pages (conference papers)
@inproceedings{tian2007face,
  pages = {1--8},
  doi   = {10.1109/CVPR.2007.383282},
  ...}
@inproceedings{cui2007easyalbum,
  pages = {367--376},
  doi   = {10.1145/1240624.1240684},
  ...}

% software entries: update title tagline and name a version
@misc{immich,
  title = {Immich: High Performance Self-Hosted Photo and Video Management Solution},
  note  = {Version v3.3.6 (released 2026-11-04); accessed Nov. 2026},   % use the version you actually ran
  ...}
@misc{photoprism,
  title = {{PhotoPrism}: {AI}-Powered Photos App},        % current upstream description; old "for the Decentralized Web" tagline is outdated
  note  = {Release 261029-963b58c50 (2026-10-29); accessed Nov. 2026},  % use the version you actually ran
  ...}

% DOI additions (optional, no field is wrong)
filonenko2025facecluster: doi = {10.1145/3746027.3754485};  booktitle = {Proc. 33rd ACM Int. Conf. Multimedia (MM)}
campello2013hdbscan:      doi = {10.1007/978-3-642-37456-2_14}
davidson2005agglomerative: doi = {10.1007/11564126_11}
davidson2007incremental:  doi = {10.1145/1281192.1281221}
wang2019linkage:          doi = {10.1109/CVPR.2019.00121}
yang2019affinity:         doi = {10.1109/CVPR.2019.00240}
                          % note: CVF lists pp. 2298-2306 (kept); IEEE Xplore/Crossref lists 2293-2301
ester1996dbscan:          publisher = {AAAI Press}, address = {Portland, OR}   (optional)
hartigan1975clustering:   isbn = {047135645X}                                  (optional)
```

If the authors choose to add the 2000 constraints paper (see rewording 2 below), the entry (verified only from search-result summaries, not from an opened page, so check the pages once more before submission):

```bibtex
@inproceedings{wagstaff2000constraints,
  author    = {Wagstaff, Kiri and Cardie, Claire},
  title     = {Clustering with Instance-Level Constraints},
  booktitle = {Proc. 17th Int. Conf. Machine Learning (ICML)},
  pages     = {1103--1110},
  year      = {2000}
}
```

## Descriptions to reword in the paper

1. Introduction, line 56-58 (immich, photoprism). Current: "local-first managers such as Immich~\cite{immich}, PhotoPrism~\cite{photoprism}, FaceCluster~\cite{filonenko2025facecluster} and the Cove system described here do it on the user's own hardware, so neither photos nor embeddings leave the device."
   Suggested: "self-hosted managers such as Immich, PhotoPrism and FaceCluster, and the Cove system described here, do it on hardware the user controls, so photos and embeddings are not sent to a third-party cloud."
   Reason: Immich and PhotoPrism are self-hosted server applications (Immich's phone app uploads to the user's own server; PhotoPrism is also offered "in the cloud"), and "local-first" has a narrower meaning (the paper cites Kleppmann et al. elsewhere). "Neither ... leave the device" is true for Cove (on-device) but not for a self-hosted server setup.

2. Related Work (wagstaff2001copkmeans). Current: "Must-link and cannot-link constraints were introduced for $k$-means~\cite{wagstaff2001copkmeans}".
   Suggested (no new reference): "Must-link and cannot-link constraints were popularised for $k$-means~\cite{wagstaff2001copkmeans}".
   Suggested (preferred, with the 2000 paper added above): "Must-link and cannot-link constraints were introduced by Wagstaff and Cardie~\cite{wagstaff2000constraints} and applied to $k$-means~\cite{wagstaff2001copkmeans}".

3. Related Work, first paragraph (yang2019affinity). Current: "or graph networks that predict links on a $k$-nearest-neighbour graph~\cite{wang2019linkage,yang2019affinity}".
   Suggested: "or graph convolutional networks on a $k$-nearest-neighbour graph that predict links between faces~\cite{wang2019linkage} or detect and segment cluster proposals~\cite{yang2019affinity}".
   Also soften "and usually a GPU" to "and typically a GPU for training" or drop it, since the abstracts do not state hardware needs.

Everything else in this batch is described correctly at abstract level. Items I could not check beyond the abstract: ester1998incremental "(up to the assignment of border points)" parenthetical; hartigan1975clustering (book text not read; description matches secondary sources); the GPU remark about wang2019linkage / yang2019affinity.

## Evidence sources actually opened or seen (index)

- Crossref: api.crossref.org works lookups for all journal/conference entries (titles, authors, pages, DOIs above).
- CVF Open Access: Wang 2019, Yang 2019, Wu 2013 pages (abstracts, page ranges).
- arXiv abstract pages: 1604.00989 (Otto), 1706.05067 (Shi), 2103.17272 (Montero); search result for 2001.00076 (Monath).
- GitHub: https://github.com/immich-app/immich , https://github.com/photoprism/photoprism , REST API repo and latest-release endpoints, raw READMEs; docs.immich.app facial-recognition page; docs.photoprism.app people page.
- vldb.org dblp mirror for Ester 1998; AAAI page and BibBase for Ester 1996; mlanthology for Wagstaff 2001; Open Library for Hartigan.
- Consensus and SciSpace result records for abstracts (Tian, Cui, Davidson 2007, Davidson 2005, Campello, Bandyopadhyay, FaceCluster).
