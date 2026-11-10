# Novelty search, round 4: Phase 1 scoping (deep-research, full mode). Awaiting the author's confirmation.

Date: 2026-11-10.

**Context: rounds 1–3 already covered**
- G1: recogniser-agnostic thresholds. Not found in the searched sources; never tested.
- G2: user corrections that survive a recogniser upgrade. Not found in the searched sources; never tested.
- G3: thresholds learned from corrections. Prior art.
- G5: video tracks as pose bridges. Simulated; little F1 gain.
- G6: benchmark protocol.

**Review-form note:** already answered (skip) earlier in this project, so it is not shown again.

## Research Question Brief

### Topic Area
New, defensible novelty for Cove's face clusterer, building on what exp19 and the round-2 review found:
- in accuracy, corrections kept inside our clusterer equal constrained average linkage and an Immich-style frozen rule;
- they beat re-applying corrections when users click arbitrary faces;
- wrong corrections are sticky;
- with corrections, an update costs about as much as re-clustering.

### Primary Research Question
Which extensions of an order-invariant, incremental face clusterer that keeps user corrections would give a contribution that is **not found in prior work**, can be **built and tested on a laptop CPU within about a week** with the existing identity-disjoint protocol (exp14/15/19), and strengthen the paper's central claim about corrections and order? The search starts from the four candidate directions below, and is open to others found during it.

| Candidate | Idea | Link to a measured weakness or claim |
|---|---|---|
| **N1. Convergence across devices** | Because the output depends only on the *set* of faces and corrections, two devices that sync photos and corrections in any order converge to identical people, with no server and no coordination, even under conflicting corrections from different family members. The local-first and CRDT framing (strong eventual consistency) would give order invariance a concrete user need. Leader and Immich-style rules diverge. | Answers the round-1 and round-2 critique "why does order invariance matter?" |
| **N2. Wrong corrections that can be detected or undone** | Flag suspicious corrections, for example a "same person" whose faces are far below the merge evidence, or a pair of corrections that contradict each other. Corrections become retractable facts. | Our own negative result: 10% wrong merges erase the gain. |
| **N3. A truly incremental constrained update** | Maintain the constrained spanning forest as faces arrive, so the update cost with corrections no longer equals a re-cluster, while keeping the order-invariance proof. | Measured: 5.1 s with corrections vs 4.7 s re-cluster. |
| **G2 (carried over). Corrections that survive a recogniser upgrade** | Corrections are stored on faces, not embeddings, so switching from MBF to EdgeFace-S could keep every correction. Not found in round 1; never tested. | Model upgrades are real; the paper already uses two recognisers. |

### FINER Assessment
| Criterion | Score | Justification |
|---|---|---|
| Feasible | 4/5 | The search tools are available (SciSpace, Consensus, web; Scholar Gateway failed in round 1). Every candidate reuses existing code and data. A week is tight for N3. |
| Interesting | 4/5 | Each candidate answers a concrete criticism, or a negative result we measured ourselves. |
| Novel | 3/5 | Unknown until searched. N1 may turn out to be a "trivial corollary" of the proposition, and N2 overlaps with the noisy-constraint literature. Hence the counter-evidence searches. |
| Ethical | 5/5 | Public literature and public datasets only. The simulated users are not people. |
| Relevant | 5/5 | Directly decides what the next version of the paper claims. |
| **Average** | **4.2/5** | |

### Scope Boundaries
- **In scope:**
  - peer-reviewed papers and preprints, 1995–2026, on constrained, incremental, interactive or replicated clustering, and on face clustering;
  - CRDT and local-first software literature where it touches *derived* or computed state;
  - product documentation of Immich, Apple Photos, Google Photos, PhotoPrism and digiKam on multi-device people sync and on correcting or undoing people grouping;
  - methods that run on a CPU.
- **Out of scope:**
  - GPU-trained clusterers (GCN etc.; known since round 1);
  - new face recognisers;
  - studies with human participants (no time for ethics approval);
  - video datasets (G5 is done).
- **Domain:** computer vision (face clustering) × data mining (constrained/incremental clustering) × distributed systems (local-first/CRDT).
- **Timeframe:** 1995–2026.
- **Geography:** none (methods literature).
- **Population:** algorithms and systems for personal photo libraries.
- **Key assumptions:**
  1. "Novel" for this venue means "not found in the searched sources" (abstract-level), never "never tried".
  2. An extension is only worth adding if it tests a claim the paper makes, not as a bolt-on.
  3. The existing simulated libraries are acceptable evidence at this venue.

### Sub-questions
1. **SQ1 (N1).** Has convergence of a *derived clustering* across replicas been studied or shipped? Search terms include "CRDT/strong eventual consistency of computed views", "coordination-free clustering", "deterministic clustering across devices", and multi-device people sync in photo apps. Would a convergence experiment (devices receiving photos and corrections in different orders and batches, with conflicting corrections, synced at random times) show divergence for leader, Immich-style and DBSCAN rules, and none for ours?
2. **SQ2 (N2).** What is known about detecting or handling wrong pairwise constraints (noisy oracles, constraint coherence, retractable constraints) in constrained or interactive clustering, especially faces? Which detector fits an order-invariant clusterer without breaking the proof?
3. **SQ3 (N3 and G2).** Is incremental maintenance of a constrained spanning forest or constrained connectivity under insertions known, and at what cost? Has a re-check of round 1's G2 turned up new prior art since?
4. **SQ4 (open).** Are there other directions, found while searching SQ1–3, that fit the paper's thesis better? Examples: explaining to the user why two faces are grouped; deleting a person's data (machine unlearning for clustering).

### Sub-Question Bindings (#547)
1. Inherits domain, timeframe, population and assumptions unchanged; adds product documentation (already in scope). No deviations.
2. Inherits all axes. No deviations.
3. Inherits all axes. No deviations.
4. Inherits all axes, and is limited to directions that touch corrections, order or local-first use. No deviations.

### Candidate Questions Considered
| # | Candidate | FINER avg | Why not selected |
|---|---|---|---|
| 1 | The umbrella RQ above (N1–N3, G2, open) | 4.2 | **Selected.** It matches the author's request ("find what innovation we can do") and still pins each idea to a test. |
| 2 | N1 only (convergence) | 4.0 | Too narrow before the prior-art check: if N1 turns out to be prior art, the round is wasted. |
| 3 | N2 only (robust corrections) | 3.8 | Strong motivation, but likely to overlap heavily with noisy-constraint work. |
| 4 | Closing the profile-face recall gap while staying incremental | 3.2 | Largely covered in round 1 (pose/occlusion) and by the negative exp16/exp17 results. |

## Methodology Blueprint

### Research Paradigm
- **Selected:** pragmatist.
- **Justification:** the goal is a decision (what to build and claim), so the evidence needed is "does prior work already do this" plus "can we test it".

### Method
- **Type:** qualitative literature scan plus feasibility analysis.
- **Specific method:**
  - an integrative scan, one reviewer, abstract-level, with a per-component prior-art table, the same format as round 3;
  - for every candidate that survives, a pre-declared experiment design (not run in this research round).
- **Justification:** this is the same method as rounds 1–3, so verdicts are comparable. It is a scan, not a systematic review.

### Data Strategy
- **Data type:** secondary.
- **Sources:**
  - SciSpace and Consensus (papers);
  - Scholar Gateway (retried);
  - web search for product documentation and the CRDT/local-first literature (e.g., Kleppmann et al., Shapiro et al.).
- **Queries:** recorded verbatim. Each component is searched with at least two phrasings, plus one **counter-evidence query** worded to find work that would make the idea *not* new.
- **Inclusion:** the abstract addresses the component.
- **Exclusion:** no abstract available; or the source cannot be verified to exist (Iron Rule: if it cannot be verified, it is out).

### Analytical Framework
1. Split each candidate into components (C1…Cn), as in round 3.
2. Give each component a verdict: Known / Partly known / Not found in the searched sources.
3. Rank the candidates by novelty × value to the paper × effort (in days).
4. Draft a pre-declared test for the top 1–2 candidates, using test libraries only, nothing tuned on test, and a stated success criterion.

### Validity Criteria
| Criterion | Strategy |
|---|---|
| No fabricated sources | Every source found through a search tool; DOI or publisher page checked for every source that will be cited in the paper |
| Avoid confirmation bias | Counter-evidence query per component; Devil's Advocate checkpoint 2 |
| Bounded novelty claims | "Not found in the searched sources", with the queries listed |
| Read-scope honesty | Abstract-level only; no method weaknesses claimed for papers not read in full |

### Limitations (By Design)
- **Abstracts only, one reviewer, search-engine coverage.** A "not found" verdict can be overturned by a paper we did not see.
- **Product behaviour is from documentation.** It is not tested.

### Ethical Considerations
None beyond accurate attribution and AI disclosure. No human subjects are involved.

### Reporting Standard
None formal; this is a narrative or integrative scan. Not preregistered (decision support only).

## Devil's Advocate Report, Checkpoint 1

### Verdict: PASS (with conditions)

### Critical Issues
No critical issues identified.

### Major Issues
1. **Novelty-hunting bias.**
   - *Problem:* searching for "something new to add" can bolt an unrelated feature onto the paper.
   - *Recommendation:* a candidate counts only if it tests the paper's own thesis, which is that corrections and order behave well in a local-first library. This is assumption 2.
2. **Anchoring on the pre-listed candidates N1–N3.**
   - *Problem:* the search may only confirm ideas we already like.
   - *Recommendation:* run SQ4 as a real open query, and run a counter-evidence query for each candidate.
3. **N1 may be a trivial corollary.**
   - *Problem:* "a deterministic function of a set converges" is textbook CRDT reasoning.
   - *Recommendation:* N1 is valuable only if (a) shipped or published systems diverge in measurable ways, and (b) the conflict and removal semantics (contradictory corrections from two devices; a retracted correction; a deleted photo) need real design. The research must check both.

### Minor Issues
- **N3 may not fit in a week.**
  - Flag its effort honestly.
  - Do not rank it on novelty alone.

### Strongest Counter-Argument
"You are looking for novelty because the method lost its accuracy advantage. A reviewer will see an extra feature attached to a method that is equal to its baselines, and will ask why the paper is not simply an evaluation note."

### Stress Test Results
| Test | Result |
|---|---|
| Remove the strongest candidate (N1): is the round still useful? | Yes (N2 and G2 remain) |
| Flip the question: could the honest answer be "no novelty within a week"? | Yes. The report must allow that answer. |
| Does it generalise beyond this paper? | Partly (local-first apps with derived ML state) |
| "So what?" | Yes: it decides the next paper version |
