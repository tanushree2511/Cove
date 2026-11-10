# Round 5 decision (SQ5): submit as is, or add something?

Sources: audit of numbers (verify script: 90 ok, 2 own-rounding differences), exp26 exactness with real corrections (zero differences on both recognisers), reference audit (24 verified, 22 partly, 0 unverified of 46), novelty re-check, venue search, round-4 review. Searches are abstract-level and bounded to the sources searched.

## What is confirmed
- Every checked number matches the result files, except the wording slips listed in the editorial decision.
- The fast read step gives the same partition as the reference on 240 libraries x 2 recognisers x 3 simulated users (corrections that really change the result in a minority of libraries; the counts are in exp26 JSON).
- All 46 references exist. 22 need missing volume/pages/DOI, a few need reworded sentences, one author first name is wrong (Bandyopadhyay, Sambaran), EdgeFace uses CosFace not ArcFace.

## Novelty (not found in searched sources, never "nobody did it")
C1 partly known; C2 known as a principle; C3 partly known (retention measurement not found); C4 known; C6 partly known. Honest contribution = measurements plus the combination, not new algorithms.

## Options, ranked
| Rank | Option | Main risk |
|---|---|---|
| 1 | A+D: cut to 6 pages, fix wording, fix bibliography, run the one compiled-timing check | Reviewers may call it an evaluation note; mitigated by honest framing |
| 2 | C: wire corrections into the app (3-4 days) | Time; adds a "working feature" but the paper's claims stay simulation-level |
| 3 | B: second dataset | Time and no human ground truth beyond what we have; low acceptance gain for a regional venue |

Recommendation: **A+D. Do not add experiments beyond the compiled-timing check.**

## Venues (read 2026-11-10; the authors must re-read each call)
INDIACom-2027, Delhi, 7-9 Apr 2027: full paper 7 Dec 2026, 6 pages, IEEE Delhi Section "technically approved", Xplore only "applied for". ICMDRSE-2027, Pune: 10 Jan 2027, technically co-sponsored by IEEE, strictest AI-use rule. Details in 03_venues.md. IEEE's own database refused access, so IEEE sponsorship is unconfirmed.
