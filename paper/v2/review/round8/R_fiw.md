# Round 8 re-review: FIW outside-data test (simulated reviewer; Methodology, Devil's Advocate, Domain/ethics)

Checked: I re-read the JSON files. Ours 0.7855 vs average linkage 0.7849 (+0.0006), retuned -0.0024, correction numbers (0.787 to 0.801; held 1.00 vs 0.26; re-apply 0.86/0.40; error-prone 29 of 300 wrong) all match the paper. verify_paper_numbers.py reports 183 ok. The numbers are right; my concerns are about framing and protocol.

## Methodology
1. MAJOR - Dependent libraries. The 30 test libraries draw about 12 families each from only about 490 test families, so most families appear in several libraries. A bootstrap over libraries treats them as independent, and the intervals are too narrow. The paper does this honestly for LFW (people bootstrap) but not for FIW. Fix: bootstrap over families (resample family weights), or say in one clause that libraries overlap. This matters most for the "+0.011 over single linkage" claim.
2. MINOR - 6.7% (2,320 of 34,692) of crops were resized without detection or alignment. Their embeddings are probably worse. Fix: one sentence reporting F1 with these crops excluded, or say it was not checked.
3. MINOR - "Scores are far below LFW's because the faces are small and relatives look alike" is a cause nobody tested. Possible others: label noise, the same celebrity in two families, unaligned crops. Fix: "probably because".
4. MINOR - MBF embeddings for FIW exist in the cache (emb_mbf_fiw.npz) but the paper reports EdgeFace-S only. Fix: say "EdgeFace-S only" in the FIW paragraph, or report MBF.
5. MINOR - The Protocol intro lists the later additions (finer grids, bootstrap, ...) but FIW is not named. Add it.
6. The family-disjoint split and the two variants (LFW-tuned transfer, FIW-retuned) are sound. The retuned run is the fairer one. Libraries of 8-16 families with no singleton strangers differ from the LFW libraries. Say so briefly.

## Devil's Advocate
- "Beats the others" is mostly baseline miscalibration. With LFW settings, DBSCAN is 0.745 and HDBSCAN 0.729. Retuned, DBSCAN equals single linkage (0.774) and HDBSCAN is 0.769. Ours is then +0.011 and +0.016, not +0.040 and +0.057. The text quotes the transfer gaps as headline. MAJOR for proportionality. Fix: quote the retuned gaps next to them, or drop DBSCAN/HDBSCAN from the "above" list.
- The honest summary is that ours, average linkage, Two-stage (+0.003, interval includes 0) and no-attach (+0.002) are indistinguishable on FIW. The attach step, which was the stated source of the LFW gain, shows nothing here. The paper omits Two-stage and no-attach from the FIW paragraph. Add one clause.
- Bold "best" on 0.786 against 0.785 in Table I overstates. Fix: bold nothing in that row, or add "ties not distinguished".
- "Ties" means the interval is about +/-0.006, not equivalence. Say "within 0.006" once.
- Corrections: the +0.0089 gain is real but small (under one point), and it is seen against discarding them. The error-prone user's gain (+0.0004) supports the paper's own caution. These claims are proportionate. Ours also nominally beats constrained average linkage on FIW (+0.003 precise, +0.0036 casual), while the LFW text says it is worse on new photos; this is a tie.
- Discussion line 342: "All accuracy differences are small because most methods already score about 0.99" is now false for FIW (0.73-0.79; spread 0.057). MAJOR (a contradiction). Fix: "on LFW-based libraries".

## Domain and ethics
- Compliance looks fine. Images are git-ignored (*.npz, evaluation/cache/), only derived numbers are released, FIW is cited and the terms are stated. MINOR: datasets/fiw is excluded only in .git/info/exclude (local, not shared). Add datasets/ to .gitignore before releasing the repo. Also confirm that you registered or agreed to the licence on the FIW site.
- "Real family photos" is fair for the images but loose for the setting. FIW is a kinship benchmark of web face crops (often press or posed shots), not albums: no event structure, no singleton strangers, libraries built by sampling families. The text says "web images of public figures, not private albums" in the scope paragraph, which is good. MINOR: "public figures" overstates; the relatives and children in FIW may not be public. The Ethics line says "celebrity photos". Fix: "web-collected photos of celebrity families, including relatives who may not be public figures; no images shown or redistributed". Consider "web family photos (FIW)" in the abstract and Table row.
- Bib: both FIW entries use "and others". IEEE style will print "et al.", but the entries are incomplete. Fix: list all authors (Robinson, Shao, Wu, Liu, Gillis, Fu, as I recall; please verify) and add volume/pages for the TPAMI entry.

## Consistency checks
- "no retuning" (abstract, caption) is accurate, and the retuned variant is reported in the text. Fine.
- Last Table I row: First-Leader FIW order agreement is 0.64, above its 0.562 minimum, so the row is not affected. Fine.
- The abstract sentence is long. "ties" appears with "again", which is acceptable.

Recommendation: minor revision (accept after the fixes above). Confidence 4/5.
