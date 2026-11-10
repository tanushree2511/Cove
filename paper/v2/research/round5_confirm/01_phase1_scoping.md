# Confirmation research, round 5: Phase 1 scoping (deep-research, full mode). Awaiting the author's confirmation.

Date: 2026-11-10.

**Review-form note:** already answered (skip) earlier in this project, so it is not shown again.
**What this is:** a decision study, not a literature review. It asks whether the revised paper is correct, new enough, and ready,
or whether one more step is worth the time.

## Research Question Brief

### Primary Research Question
For the revised Cove paper (set semantics for face-grouping corrections, with E1–E5), is every claim **correct**, every reference
**real and correctly described**, and every novelty statement **still true in the searched sources**; and is there any addition
that would **materially raise the chance of acceptance** at an IEEE regional or national conference in India within about a week on
a laptop CPU, or should the paper be cut to 6 pages and submitted as it is?

### Sub-questions
1. **SQ1 Claim audit (done by me, deterministic).** Does every number in the abstract, text and tables match `evaluation/results/*.json`?
   Run a script over exp14–exp25 and list mismatches. Re-run the exactness test with the exp19 users' real corrections (item 1 of the
   editor's notes), because the random corrections in the first run rarely bind.
2. **SQ2 Reference audit (subagents).** For each of the 46 cited works: does it exist, are authors, year and venue right, and does the
   paper describe it correctly? Verdict per reference: VERIFIED / PARTLY (details wrong) / UNVERIFIED. Unverified means it is removed
   or flagged for the authors; it is never kept on trust.
3. **SQ3 Novelty re-check with the new framing (subagent, search tools).** For each component, with at least two phrasings and one
   counter-evidence query: (a) deterministic derived state that converges across replicas (CRDT, local-first) applied to clustering;
   (b) retracting or undoing a user constraint exactly in constrained clustering; (c) carrying pairwise constraints across a change of
   embedding model; (d) exact decomposition of average-linkage by threshold graph (this is textbook; the check is whether it is used
   for constrained agglomerative clustering); (e) multi-device "people" sync and correction handling in Apple Photos, Google Photos,
   Ente, Immich, PhotoPrism and digiKam documentation; (f) order-independent incremental clustering with must-link and cannot-link
   constraints. Verdicts: Known / Partly known / Not found in the searched sources.
4. **SQ4 Venue fit (subagent, web search).** Find 3–5 real IEEE-sponsored or IEEE-technically-co-sponsored conferences in India with
   submission deadlines after today, a 6-page limit, and an AI-use policy; record the call-for-papers page, deadline, page limit, indexing
   claim (IEEE Xplore), AI policy and registration fee if stated. The author must check each call himself or herself before submitting.
5. **SQ5 Decision.** Using SQ1–SQ4 and the round-4 review, rank: (A) submit as is after cuts; (B) add a second dataset for the
   libraries (feasibility of a public face dataset with identities beyond LFW, on this laptop); (C) wire corrections into the app so the
   paper can claim a working feature; (D) stop adding and spend the time on cuts, a proper check of the numbers and the bibliography.
   Give a recommendation with the main risk of each.

### FINER Assessment
| Criterion | Score | Justification |
|---|---|---|
| Feasible | 5/5 | Audits and searches only; no new large experiment is needed to answer the question |
| Interesting | 4/5 | It decides whether to submit |
| Novel | 3/5 | Not meant to be novel; it is a confirmation study |
| Ethical | 5/5 | Public sources only; no human subjects |
| Relevant | 5/5 | Directly decides the next step |
| **Average** | **4.4/5** | |

### Scope Boundaries
- **In scope:** the paper as committed (ab09dbe); its results files; its 46 references; literature 1995–2026 on the six components
  in SQ3; product documentation (to be read, not tested); conferences in India with a 6-page IEEE format.
- **Out of scope:** new face recognisers; studies with human participants (no time for ethics approval); real family photo albums;
  video datasets; GPU-trained methods.
- **Key assumptions:**
  1. "Novel" means "not found in the searched sources" (abstract level), never "never tried".
  2. A venue is a suggestion until the author reads its current call for papers.
  3. A source that cannot be verified to exist is excluded.

### Methodology Blueprint
- **Paradigm:** pragmatist; the product is a decision.
- **Method:** (1) deterministic audit of numbers; (2) per-reference verification using SciSpace, Consensus, Scholar Gateway and web
  search; (3) component-by-component prior-art scan, queries recorded verbatim; (4) venue search on publisher and conference pages;
  (5) a ranked decision with the risk of each option.
- **Validity:** every search query is recorded; every "not found" is bounded to the sources searched; the Devil's Advocate checks
  each of the three checkpoints below; no fabricated source is ever kept.
- **Limitations by design:** abstract-level reading for most sources; one reviewer per component; search-engine coverage; conference
  details can change after the search date.
- **Reporting:** a narrative report with per-reference, per-component and per-venue tables; AI disclosure included.

### Devil's Advocate Report, Checkpoint 1
**Verdict: PASS (with conditions).**
- *Critical:* none.
- *Major 1 — confirmation bias:* a study asked "confirm everything" tends to confirm. Mitigation: each component has a counter-evidence
  query, and the audit script reports mismatches rather than a pass.
- *Major 2 — "submit as is" is the comfortable answer:* the decision step must state what a reviewer would reject the paper for, and
  whether any of it can be fixed by wording alone.
- *Major 3 — venue lists go stale:* deadlines and policies must carry the date of the page read.
- *Strongest counter-argument:* "The paper's main results are properties of any method that recomputes from a set. A reader at a
  regional conference may find it obvious, and the one measured advantage (cost) is partly an implementation difference. The honest
  answer to 'is anything new here' may be: the measurements are new, the ideas are not."
- *Stress test:* if every novelty component came back "Known", the paper would still be an applied measurement paper; the framing
  would have to say so.

## Plan after you confirm (both gates at once)
- **Review:** five seats (Journal-Fit, Methodology, Domain, Perspective, Devil's Advocate) run in parallel on the current draft; then
  an Editorial Decision with a roadmap and a plain verdict on "publishable as is?".
- **Research:** my own audit (SQ1) plus three search subagents (SQ2 references, SQ3 novelty, SQ4 venues); then SQ5, the ranked decision.
- **Nothing in the paper changes** until both are done and you have read the combined report.
