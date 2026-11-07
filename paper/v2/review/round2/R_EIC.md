# Peer Review Report

## Manuscript Information
- **Title**: Face Grouping That Keeps the User's Corrections: Order-Invariant Incremental Clustering for Local-First Photo Libraries
- **Manuscript ID**: `paper/v2/cove_paper.tex` (commit ce1b15d, round-2 rewrite)
- **Review Date**: 2026-11-07
- **Review Round**: Round 2 (re-review after major revision)

---

## Reviewer Information

### Reviewer Role
Journal-Fit Reviewer (internal id EIC)

### Reviewer Identity
Programme-committee member of an IEEE India regional computing conference (applied-systems / image-processing track). Same identity as in round 1.

### Review Focus
- Does the paper fit the venue?
- Is the novelty the right size now that constrained clustering is cited as prior work?
- Does it fit the 6-page IEEE conference format?
- Is the AI-use disclosure acceptable?
- Are the round-1 issues (`EDITORIAL_DECISION.md`) really resolved, as `REVISION_LOG_round2.md` says?

I did not read any other round-2 seat report.

---

## Overall Assessment

### Recommendation
- [ ] Accept
- [x] **Minor Revision**
- [ ] Major Revision
- [ ] Reject

### Confidence Score
**4.** Applied clustering and face-recognition systems are within my remit. I re-derived several headline numbers from the released JSON files and read the constrained-labelling code. I did not re-run any experiment.

Confidence is an uncertainty/scope disclosure only; it never changes consensus counts, severity, decision bearing, or arbitration.

### Calibration Status
`NOT_CALIBRATED`

This is a simplified run: no sprint contract and no calibration scripts. A seat report cannot know the final panel topology.

### Summary Assessment
**What the paper does.** It describes the face clusterer of Cove, a local-first photo system:
- single-linkage core links, a looser attach threshold, and an average-linkage centroid merge;
- user must-link and cannot-link corrections, re-applied on every re-clustering;
- an argument that the output depends only on the set of faces and corrections, not on their order.

It is evaluated on identity-disjoint simulated LFW libraries, with equal tuning for all baselines and paired bootstrap intervals. Ten simulated corrections raise F1 from 0.984 to 0.994. After new photos arrive, 100% of corrections hold, against 27% under plain re-clustering.

**What improved since round 1.** The rewrite is a real improvement. The method is now honestly described as "an adaptation of known parts". The update-time claim is cut to the measured 1.3×. The paper reports where it loses: CPLFW, low-res and mixed photos. The protocol is well above the norm for this venue.

**What is still wrong.** The remaining problems are about sizing the headline claim and making the paper ready to submit:
1. The 100% figure holds by construction. The natural competitor is constrained re-clustering, for example constrained average linkage, which the paper cites. It is never run. So the paper does not yet show what its clusterer adds beyond cost.
2. Close prior art found by the authors' own novelty scans is not cited, including constrained/incremental DBSCAN and face clustering with pairwise constraints.
3. The title sells a feature that the shipped app does not have.
4. The AI-use statement understates how much of the work an AI assistant did.

**Recommendation.** Each issue can be fixed by a bounded amount of rewording, plus at most one extra baseline run. I recommend Minor Revision for this venue.

---

## Criterion-Bound Judgements

| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Venue fit (applied systems, IEEE India regional) | Reviewer card #1 | MEETS | `text: Sec. I "local-first managers such as Immich, PhotoPrism, FaceCluster and the Cove system described here"` | Deployed system plus empirical study on CPU hardware: the profile these tracks accept | none identified | no |
| Originality, sized correctly | Card #1; `references/quality_rubrics.md` | PARTLY_MEETS | W1, W2 | Sized well at the method level. Over-sized at the claim level: the 100% is by construction, and the nearest prior art is missing | Prior art known only from the authors' abstract-level scans | yes. Rewording, plus optionally one baseline |
| Methodological rigor (venue level) | rubrics | MEETS | S2 | Identity-disjoint split, equal grids, paired bootstrap | Detailed check is R1's remit | no |
| Evidence sufficiency for the headline | rubrics | PARTLY_MEETS | W1, W5 | Headline lacks a constrained baseline; the "share held" statistic is misdescribed | — | yes |
| Argument coherence (title → abstract → conclusion) | rubrics | PARTLY_MEETS | W3, W6 | Title and abstract describe a system property that limitation (vi) says the app lacks | — | yes |
| Writing quality | rubrics | MEETS | S5 | Plain, direct, honest about losses | — | no |
| Literature integration | rubrics | PARTLY_MEETS | W2, W11 | 32 refs, but the closest neighbours are absent and several entries are incomplete | — | yes (via W2) |
| Significance & impact | rubrics | MEETS | S1 | Practical, user-visible problem. Effect sizes are small in F1 (+0.7 pt later) but large in mistakes that come back | Simulated oracle user (limitation ii) | no |
| Page-limit fit (6 pp. IEEEtran) | Card #1 | MEETS | Detailed Comments § Journal Fit | About 3,200 body words, 3 tables (one full-width), 32 refs, no figures. My estimate is about 5–5.5 pages | Not compiled. My estimate only | no |
| AI-use disclosure | Card #1; IEEE author guidelines on AI-generated content | DOES_NOT_MEET | W4 | Understates the AI role, and is not in the Acknowledgment section that IEEE asks for | I have not checked the specific conference's own policy | yes. Wording only |
| Round-1 issue resolution | `EDITORIAL_DECISION.md` vs `REVISION_LOG_round2.md` | MEETS (mostly) | § Round-1 Resolution Audit | 11 of 13 editorial items are resolved and verified. Placeholders remain; the Immich/Chinese Whispers baselines were skipped without a stated reason | — | no |

I did not total these judgements or map them mechanically to the recommendation.

---

## Strengths

### S1: A real, user-visible problem, framed for practitioners
The two failure modes are concrete, and readers of an applied track will recognise them:
- order dependence: "two imports of the same photos can show different people";
- lost corrections: "the user must fix them again after every import".

The corrections framing matches documented behaviour in deployed tools. The authors' own scan cites Immich documentation that recommends resetting and re-clustering.

**Evidence Anchor**: `text: Sec. I "If the system re-clusters from scratch after an import, the user's earlier fixes are not part of its input, and the same mistakes come back."`

### S2: Evaluation protocol well above the regional-venue norm
- Tuning and test identities are disjoint, with zero overlap, verified in `exp14_disjoint_edgeface_s.json` `split.identity_overlap = 0`.
- Every method is tuned on the same libraries with the same rule.
- The recogniser is chosen by a rule declared before testing.
- Differences come with paired bootstrap intervals.

This directly fixes round-1 issues 1, 2 and 10.

**Evidence Anchor**: `text: Sec. IV "All rules below were fixed before any test number was computed."`

### S3: Novelty sized honestly at the method level
The paper now says plainly that, at m = 1, the core step is single linkage. It also says that constraints, incremental constraints and interactive face annotation are prior art. This is exactly the fix my round-1 W1 asked for.

**Evidence Anchor**: `text: Sec. III-B "We present it as an adaptation of known parts, and Sec. V-B measures each part."`

### S4: Losses and negative results reported plainly
- Table I bolds baselines where they win (JPEG, low-res, mixed, occluded, CPLFW).
- Sec. V-B says the method is "no longer clearly ahead".
- The CPLFW gap is now attributed to the clustering rule, not only to the embedding.
- Sec. V-D reports a pre-declared pose bonus that passed tuning but failed at test.

**Evidence Anchor**: `table: Table I — CPLFW row, Avg. linkage 0.909 bold vs Ours 0.841`

### S5: Claims match the released data
I recomputed the following and found they match:
- Table I (EdgeFace-S F1 and order-agreement row);
- Table II ("All", low-res, mixed, occluded and MBF rows, including the +0.010 [0.008, 0.011] gain);
- Sec. V-F timings: 3.53 / 4.72 / 16.69 s, and 0.145 s add vs 3.38 s read.

**Evidence Anchor**: `dataset: evaluation/results/exp15_corrections_edgeface_s.json and exp18_update_time_edgeface_s.json — table.ALL and rows[-1] match Table II and Sec. V-F`

### S6: Update-time claim now sized to the evidence
The round-1 "faster than re-clustering" claim is replaced by "cheap but not constant-time". The paper gives a per-step breakdown showing that the read-time steps dominate.

**Evidence Anchor**: `text: Sec. V-F "The update is therefore cheap but not constant-time."`

---

## Weaknesses

### W1: The headline comparison is against a strawman; constrained re-clustering is cited but not run
**Problem**
- "100% of corrections still hold" is guaranteed by the design whenever the corrections are consistent: hard constraints are re-applied every time labels are computed (Sec. III-C).
- A method that discards the constraints will of course fail some of them. So the 100% is not a measured finding, yet the abstract and contribution 2 present it as one.
- The natural competitor is to store the corrections and re-run a constrained batch clusterer on the whole library. Constrained average linkage (Davidson & Ravi, cited as [davidson2005agglomerative]) is the obvious choice.
  - It would also keep 100%.
  - It is order-invariant.
  - Table I suggests it would be at least as accurate: average linkage ties or beats ours on four library conditions, and beats ours by 6.8 points on CPLFW.
- The only remaining difference is cost, which Sec. V-F shows once: 3.5 s vs 16.7 s at 8,290 faces, for *unconstrained* average linkage.

**Evidence Anchor**: `absence: Sec. V-C / Table II — expected a constrained re-clustering baseline (e.g., constrained average linkage) with F1 now/later, share held and update time; checked Sec. II, Sec. IV "Corrections", Sec. V-C, Table II, evaluation/exp15_corrections.py`

**Why it matters**
- A PC member who knows COP-KMeans will read "100% vs 27%" as true by construction. That undercuts the paper's headline.
- The paper's real differentiator (the same guarantee at lower update cost, plus incremental insertion) is never stated as the contribution.

**Suggestion**
- *Minimum:* in the abstract, contribution 2 and Sec. V-C, say that the 100% follows from treating corrections as hard constraints. Say that the measured quantity is how many corrections plain re-clustering loses. Add one sentence explaining why constrained batch re-clustering is not the answer: cost and O(n²) memory on large libraries.
- *Stronger:* add a "Constrained avg. linkage (re-run)" row to Table II, and its time at 8,290 faces to Sec. V-F. This is a single-file experiment; the libraries have at most about 1,400 faces.

**Severity**: Major
**Confidence**: 4. The by-construction point follows from Sec. III-C and `satisfied()` in `exp15_corrections.py`. Whether constrained average linkage would match on F1 is my inference from Table I.

### W2: Close prior art found by the authors' own novelty scans is not cited
**Problem**
- The round-1 scan explicitly flagged several works as prior art "for the idea behind our corrections feature" and for order independence. None of them is in Sec. II or `references.bib`:
  - face clustering with pairwise constraints: ConPaC, Shi, Otto & Jain 2017;
  - constrained and incremental-constrained DBSCAN: Lasek & Gryz 2019;
  - constraint streams: Halkidi et al. 2012;
  - order-independent incremental clustering: Monath et al. 2019 (Grinch); Bandyopadhyay & Murty 2016;
  - a mobile face album with user corrections: Xu et al. 2017;
  - constrained spectral face annotation: Han, Hu & Deng 2016.
- Constrained/incremental DBSCAN is the nearest algorithmic neighbour of "incremental DBSCAN core points plus must/cannot-link".
- The novelty sentence in Sec. II rests on a search the paper itself says read "abstracts only".

**Evidence Anchor**: `absence: Sec. II Related Work and references.bib — expected ConPaC (2017), constrained/incremental DBSCAN (Lasek & Gryz 2019), Grinch (2019), Bandyopadhyay & Murty (2016), Halkidi et al. (2012); checked Sec. II, all 33 bib entries, paper/v2/research/innovation_scan_2026-11-07.md §3 and innovation_scan_round3_2026-11-07.md C4/C6`

**Why it matters**
- If a reviewer knows ic-DBSCAN or ConPaC, the "we did not find" sentence and contribution 1 look uninformed.
- Leaving out prior art one's own search surfaced is the kind of gap that sinks a novelty claim.

**Suggestion**
- Read the full text of at least ConPaC, Lasek & Gryz, and Davidson et al. 2007.
- Add one sentence per group stating the difference. For example, if true: "ic-DBSCAN handles constraints but not order-invariant attachment or merge".
- Shrink the remaining novelty claim to the combination plus the persistence measurement.
- Verify every entry before citing. The scans worked from abstracts.

**Severity**: Major
**Confidence**: 4. The absence is directly checkable. How close each work is depends on full texts I have not read.

### W3: The title and abstract describe a system feature the shipped app does not have
**Problem**
- The abstract says "We describe the face clusterer of Cove … which addresses both", and the title promises grouping "That Keeps the User's Corrections".
- Limitation (vi) says the app does not persist corrections and overwrites user-assigned names. The code confirms this: `cove/api/server.py:773` calls `PersonManager().save_people(..., overwrite=True)`.
- Sec. IV describes plain re-clustering as "the behaviour of the current app".
- So the paper's own system currently shows the exact harm the introduction says it removes.

**Evidence Anchor**: `text: Sec. VI (vi) "the current app does not yet persist them through its re-clustering, which also overwrites user-assigned names"`

**Why it matters**
- At an applied-systems venue, the system is part of the contribution.
- A reader who installs Cove gets the opposite of the title. Any PC member who opens the repository will notice.

**Suggestion**
- *Preferred:* wire the clusterer's constraint API and name persistence into the app before submission. The clusterer side already exists. Then add two sentences on an end-to-end check.
- *Minimum:* reword the abstract to say that corrections are "implemented and evaluated in the clusterer; integration into the app is in progress". Keep the title only if the integration lands.

**Severity**: Major
**Confidence**: 5. Stated in the manuscript and visible in the code.

### W4: The AI-use statement understates the AI's role and is not where IEEE asks for it
**Problem**
- The Declarations say the AI assistant was used "to write parts of the code and experiment scripts, to search the literature and to edit the text".
- The repository record shows more than editing:
  - the round-2 revision log calls this version "a full rewrite" carried out by the assistant after the author approved it;
  - all five commits carry a Claude co-author line, including "Paper rewrite (round 2)" and the commit that introduced the evaluation suite;
  - the novelty scans, and the simulated pre-submission review that shaped the revision, were also AI-run.
- IEEE's guidance asks that AI-generated content be disclosed in the **Acknowledgment** section, naming the system and the sections affected and the extent of use.
- The IEEE conference template has no "Declarations" block. That block is a Springer convention.

**Evidence Anchor**: `text: Declarations "an AI assistant (Claude, Anthropic) was used to write parts of the code and experiment scripts, to search the literature and to edit the text"`

**Why it matters**
- Many Indian IEEE conferences and colleges now run similarity and AI-text detectors (iThenticate/Turnitin). An understated disclosure that is later contradicted by a detector, or by the public commit history, becomes an integrity problem. A plain disclosure is acceptable.

**Suggestion**
- Move the statement to an unnumbered `\section*{Acknowledgment}`.
- State the AI role accurately, for example: Claude drafted and revised the manuscript text (all sections) under the authors' direction; wrote most of the clustering and experiment code; ran the literature scans; produced a simulated pre-submission review. The authors designed the study goals, checked every number against the released scripts, and take responsibility.
- Then check the target conference's own policy. Some cap AI-generated text or need a separate form.

**Severity**: Major
**Confidence**: 4. Based on the repository record and IEEE's general author guidance. I have not seen the specific conference's call for papers.

### W5: The "share of corrections held" and "ten corrections" figures do not match their computation
**Problem**
- **"Ten corrections" is really "up to ten".** The abstract says "With ten simulated corrections per library". In `exp15_corrections_edgeface_s.json`, the 240 library-condition runs received 5.42 corrections on average: 33 received none, and only 91 received ten.
- **"27% hold" is a per-library average, not a share of corrections.** The figure averages over libraries, and the code's `satisfied()` returns 1.0 for a library with no corrections. Those 33 empty runs therefore count as "100% held" for plain re-clustering.
- **The true shares are lower:**
  - pooled over all corrections, plain re-clustering keeps 20.3% (MBF 16.9%);
  - averaged only over libraries that received corrections, it keeps 15.7%.

**Evidence Anchor**: `dataset: evaluation/results/exp15_corrections_edgeface_s.json per_library — mean corrections_made 5.42; 33/240 zero; later_lost_satisfied pooled 0.203 vs reported 0.273`

**Why it matters**
- The error runs in the paper's favour: the real result is stronger. But it is the headline statistic, and its definition in the text ("share of the corrections") is not what was computed.

**Suggestion**
- Report the pooled share (about 20% / 17%).
- Say "up to ten (mean 5.4)" in the abstract, Sec. IV, the Table II caption and the conclusion.
- Optionally, give the more user-facing number: mistakes that came back per library.

**Severity**: Minor
**Confidence**: 5. Recomputed from the released JSON.

### W6: The abstract mixes recognisers in the order-agreement figure
**Problem**
- The abstract's "as low as 0.52" is the MBF minimum (First-Leader, mixed, 0.515).
- Table I and Sec. V-A, which are EdgeFace-S results, report 0.562.

**Evidence Anchor**: `text: Abstract "leader-based methods reach an order agreement as low as 0.52"`

**Suggestion**: Use 0.56, or write "0.56 (0.52 with MBF)".

**Severity**: Minor
**Confidence**: 5. Checked against `exp14_disjoint_{edgeface_s,mbf}.json`.

### W7: "Provably independent of order" does not hold for contradictory corrections
**Problem**
- Contribution 1 says the output, including corrections, is "provably independent of the order".
- In `_labels_constrained`, both the must-link processing order (`sorted(self.must)`) and the edge tie-break use internal face indices, and those are insertion positions.
- When must-links conflict with cannot-links, which must-link gets dropped can therefore depend on insertion order.
- The proof sketch waves this away ("neither do contradictory corrections"). But limitation (ii) says real users "sometimes" correct wrongly, which is exactly when contradictions arise.
- The empirical check (3 orders) used an oracle user who never contradicts.

**Evidence Anchor**: `text: Sec. III proof sketch "neither do contradictory corrections, which are resolved in a fixed order"`

**Suggestion**
- Resolve conflicts by a key that does not depend on insertion, such as a photo-content hash plus the face box, or the timestamp of the correction.
- Alternatively, state the exception inside Proposition 1 and drop "provably" from contribution 1.

**Severity**: Minor
**Confidence**: 4. Read from `cove/engines/stable_cluster.py`. I did not construct a counter-example run.

### W8: Baselines and their grids are never defined
**Problem**
- The Protocol never defines First-Leader, Two-stage, single/average linkage, DBSCAN or HDBSCAN, or their parameter grids. Sec. II only lists them.
- "Every method gets a grid over the same similarity range" cannot apply to HDBSCAN. Its tuned parameters are min-cluster-size 4 and min-samples 5 (`exp14 tuned.HDBSCAN`), not similarity thresholds.
- "Seven baselines" (contribution 3) counts the "Ours, no attach" ablation.

**Evidence Anchor**: `absence: Sec. IV Protocol — expected one-line definitions and grids for each baseline; checked Sec. II, Sec. IV, Sec. V-A, Table I caption`

**Suggestion**
- Add 3–4 lines or a footnote defining each baseline and its grid, including HDBSCAN's integer grid.
- Write "six baselines and one ablation".

**Severity**: Minor
**Confidence**: 5

### W9: The front matter is still not ready (round-1 W7 not resolved)
**Problem**
- The author blocks still contain "[College name]", "[City]" and "[email]".
- The Author contributions line says "to be completed by the authors".
- IEEE PDF eXpress and PC format checks at Indian regional conferences routinely desk-reject on this.

**Evidence Anchor**: `text: author block "\textit{[College name]}\\"`

**Suggestion**
- Fill in the author details and add the guide if the college requires it.
- Replace the Declarations block with IEEE-style Acknowledgment text (see W4). The data-availability and licence sentences can go there, or in a footnote.

**Severity**: Minor
**Confidence**: 5

### W10: Behaviour at realistic library sizes is not shown
**Problem**
- The largest timed library has 8,290 faces. Read-time cost grows faster than linearly: `inc_labels_s` goes from 0.11 s at 829 faces to 3.38 s at 8,290, roughly n^1.5.
- The clusterer silently skips the centroid merge when there are more than 20,000 clusters (`stable_cluster.py:193`). A family library with many singleton strangers could cross that limit, and its behaviour would then change without notice.

**Evidence Anchor**: `dataset: evaluation/results/exp18_update_time_edgeface_s.json rows — inc_labels_s 0.107 at 829 faces to 3.385 at 8,290`

**Suggestion**
- Add one sentence projecting cost at about 50k faces, or run once on synthetic duplicates.
- Disclose the 20,000-cluster cutoff, or remove it.

**Severity**: Minor
**Confidence**: 4

### W11: Several bibliography entries are incomplete
**Problem**
- The round-2 additions lack pages, volumes or DOIs: Daniels 2006, Van Craenendonck 2017, Tian 2007, Cui 2007, Song 2006.
- The bib comment says they were verified only "abstract level".

**Evidence Anchor**: `dataset: paper/v2/references.bib lines 207–286 — entries daniels2006threshold, vancraenendonck2017selection, tian2007face, cui2007easyalbum, song2006context without pages/DOI`

**Suggestion**: Complete each entry from the publisher's page. Indian IEEE conferences check reference formatting at camera-ready.

**Severity**: Minor
**Confidence**: 5

---

## Round-1 Resolution Audit (EIC check of `REVISION_LOG_round2.md`)

| Round-1 item | Log says | My verification | Verdict |
|---|---|---|---|
| C1 embedding-blame claim | Fixed | Sec. V-B now attributes the gap to "the clustering rule as well as … the embedding", with the P/R numbers | Resolved |
| 1 identity overlap | Fixed | `split.identity_overlap = 0`; CALFW/CPLFW restricted to the test half (Sec. IV) | Resolved |
| 2 unequal tuning | Fixed | Same libraries and rule for all methods. The "same similarity range" wording is inexact for HDBSCAN (W8) | Resolved (wording nit) |
| 3 novelty at m = 1 | Fixed | Sec. III-B, lines 131–133; single linkage is a baseline | Resolved |
| 4 average linkage on EdgeFace-S | Fixed | Table I | Resolved |
| 5 update time | Fixed | Sec. V-F matches exp18; the claim is softened; the app gap is admitted | Resolved |
| 6 missing baselines | Mostly | DBSCAN/HDBSCAN/single linkage added. No Immich-style or Chinese Whispers baseline, and **no sentence in the paper says why** | Partly. Add one sentence |
| 7 recogniser protocol | Renamed | Sec. V-E states random pairs; the overstatement sentence is gone | Resolved |
| 8 Table III control | Removed | Table removed | Resolved |
| 9 1.67× | Fixed | Sec. V-E | Resolved |
| 10 test sets in decisions | Fixed | Rule stated (Sec. IV). Whether it was really declared in advance is not verifiable from the paper | Resolved as stated |
| EIC W1–W6, W8 | Fixed | Checked in the text | Resolved |
| EIC W7 placeholders | Remain | Still present | **Unresolved** (W9) |
| R3 names overwritten, CORS | Reported, not fixed | Disclosed in (vi) and in Privacy | Disclosed. The title still conflicts (W3) |

The revision log is accurate. I found no item marked "Fixed" that was not.

---

## Detailed Comments

### Journal Fit
- **Fit.** Good fit for an IEEE India regional applied-computing track: a working local-first system, CPU-only measurements on a stated laptop, and a careful empirical study. It is closer to INDICON- or CONECCT-style systems papers than to a CV-theory paper, which suits it.
- **Length.** I estimate 5–5.5 IEEEtran pages:
  - about 3,200 body words;
  - one full-width and two single-column tables;
  - 32 references;
  - no figures.
  
  That is within 6 pages, with room for the W1 row and the W2 sentences. The abstract (231 words) is inside IEEE's 150–250 range.
- **Figure.** The paper has none. A small diagram of the correction workflow (correction → constraint → later import) would help a general PC audience, if space allows.

### Originality
- **Method level: sized correctly.** S3 and the introduction's "we do not claim these parts as new" are exactly right.
- **Claim level: still over-sized** in two places: the by-construction 100% (W1), and a "not found" statement made without the prior art the authors' own scans surfaced (W2).
- **The honest contribution** is a working, order-invariant combination of known parts that keeps corrections at lower cost than constrained batch re-clustering, plus a measurement of how much plain re-clustering loses (about 80% of corrections; see W5). That is enough for this venue if it is stated that way.

### Significance
- **Practical, sub-field-level significance.** In F1 the gains are small (+0.010 now, +0.007 later), on near-saturated LFW-derived libraries.
- **The user-facing effect is large.** Roughly four of every five fixed mistakes return without the feature.
- **Lead with the user-facing effect.** It is more meaningful than F1, and fixing W5 makes it stronger.

### Structural Coherence
- **Strong arc.** Problem → method → order → accuracy → corrections → negative result → time → limits. The limitations section is unusually candid.
- **The one break** is W3: the title and abstract say the system does what the discussion admits it does not yet do.

### Title & Abstract
- **Title.** Accurate for the clusterer, not for the app (W3).
- **Abstract.** Well structured and numerically honest, apart from the 0.52 figure (W6) and "ten corrections" (W5). It should name the price of the precise setting, the lower CPLFW recall. It does name the CPLFW gap, which is good.

### Conclusion
Matches the results. Once W1 and W5 are fixed, the "about a quarter" phrase should change to "about one in five".

---

## What a real IEEE India regional PC would likely do
- **Likely outcome.** Two or three reviewers, short reports, an accept/reject decision with camera-ready changes. This paper's rigour is clearly above the median submission, so acceptance is the likely outcome **if** it gets past the format and integrity checks. At most one reviewer would raise W1.
- **What actually threatens it at this venue:**
  1. desk rejection over the placeholders (W9);
  2. a similarity or AI-detection flag that contradicts the disclosure (W4);
  3. a reviewer who knows the constrained-clustering literature calling the 100% headline trivially true (W1).
- **Effort.** All three can be fixed in about a day of writing, plus at most one small experiment.

---

## Questions for Authors
1. Would constrained average linkage, re-run from scratch, also keep 100% of corrections at comparable F1? If so, is the contribution the lower update cost? Can you show that cost and memory at 8k and about 50k faces?
2. Have you read ConPaC and Lasek & Gryz (constrained/incremental DBSCAN) in full? How does your constraint handling differ from theirs?
3. Will the app integration of corrections and name persistence be finished before submission? If not, are you willing to retitle?
4. Which conference are you targeting? Does its call for papers have an AI-content policy beyond IEEE's general guidance?

---

## Minor Issues

### Language / Accuracy
- **Sec. V-B, "better by 0.4 to 14 points".** Against single linkage and DBSCAN this is true on the eight library conditions. On CPLFW, single linkage is higher (0.846 vs 0.841). Add "on the library conditions".
- **Sec. V-A, "every order and batch split".** Batch-split invariance was tested empirically only with a fixed batch size of 64. Exp15's "kept" path rebuilds from scratch rather than inserting the "later" faces after the corrections. Either say that it follows from the proposition, or add one run with varied batch sizes.
- **Sec. II, "(SciSpace, Consensus and web search, abstracts only)".** Keep this honesty, but do the full-text check from W2 so that the sentence can be strengthened.

### Citation Format
- The `jung2025posetta` bib entry is uncited. That is harmless, but remove it if unused.
- The Immich and PhotoPrism `@misc` entries need access dates in IEEE style. They are present; check that IEEEtran renders them correctly.

### Figures and Tables
- **Table I.** Bold marks the best mean even where the paired difference is not significant (JPEG, look-alike). Add "bold: best mean; see text for significance" to the caption.
- **Table II.** The "Fixes held" column mixes two numbers in one cell ("27% / 100%"). Split it into "lost" and "kept" sub-columns to match the F1 columns.

### Layout
- `graphicx` is loaded but no figure is included. That is fine either way.
- Compile on Overleaf to confirm that the full-width Table I sits at the top of page 3 or 4 and does not push the references onto page 7.
