# Roadmap

This roadmap describes planned phases for the Australian For AIs project.

Phases are listed in order. No phase is marked complete until its graduation criteria are explicitly satisfied and documented. Future phases are not complete.

---

## Phase 1 — Research Substrate *(merged; external-researcher invariant review still pending)*

**Goal:** Establish the contracts, schemas, methodology, documentation, starter fixtures, reference evaluator, and tests needed for later dataset expansion.

**Deliverables:**
- Core invariants document (AU-HUMOUR-001 through AU-HUMOUR-010)
- JSON Schema for examples and evaluation records
- Synthetic starter dataset (~15 illustrative examples)
- Python data models and deterministic reference evaluator
- CLI for validation and evaluation
- Test suite (all offline)
- Ethics, methodology, annotation, and governance documentation
- Research reference corpus with explicit copyright, provenance, and epistemic-status boundaries
- Repository hygiene rules preventing generated local artefacts from entering the research record

**Graduation Criteria:**
- [x] All tests pass in CI
- [x] All starter examples validate against the schema
- [x] Research references are explicitly separated from redistributable benchmark data
- [x] No fabricated release/citation metadata remains in the Phase 1 branch
- [ ] Invariants reviewed by at least one researcher outside the initial author
- [x] PR reviewed and merged

Phase 1 code and documentation are merged, but the phase is not marked complete because the explicit external-researcher invariant review criterion remains open.

---

## Phase 2 — Pilot Human Annotation *(tooling implementation in PR #2; human collection pending)*

**Goal:** Develop annotation tooling and conduct a small-scale pilot with real human annotators.

**Implementation status:** PR #2 provides a 60-item unannotated synthetic pilot pack, a self-contained offline annotation interface, strict per-annotator validation, pseudonymous annotation records, deterministic agreement analysis, a pilot protocol, and a mechanism-selection review. This does **not** claim that real human annotation or ethical review has already occurred.

**Deliverables:**
- Annotation interface or workflow
- Inter-annotator agreement analysis tools
- Pilot annotation of ~50–100 examples with multiple annotators
- Revised annotation guide based on pilot experience
- Mechanism-selection review informed by the Phase 1 research reference corpus

**Graduation Criteria:**
- [ ] Pilot annotation completed with at least 2 annotators per example
- [ ] Inter-annotator agreement measured and reported
- [ ] Annotation guide updated to reflect lessons learned from actual pilot use
- [ ] Ethical review of annotation process completed

---

## Phase 3 — Multi-Annotator Culturally Contextualised Dataset

**Goal:** Produce a dataset with genuine human annotations, multiple interpretations per example, explicit confidence ratings, and documented inter-annotator disagreement.

**Deliverables:**
- Dataset of 200–500 examples with multi-annotator labels
- Provenance and consent documentation for all examples
- Formal inter-annotator agreement analysis
- Dataset card following established NLP data documentation practice

**Graduation Criteria:**
- [ ] Dataset ethics review completed
- [ ] Provenance documented for all examples
- [ ] Inter-annotator agreement reported with appropriate metrics
- [ ] Data release reviewed against privacy and consent requirements

---

## Phase 4 — Baseline Evaluation

**Goal:** Evaluate a selection of publicly available language models against the Phase 3 dataset using the reference evaluator and extended metrics.

**Deliverables:**
- Evaluation pipeline for local and API-accessible models
- Baseline scores on component metrics (not a single aggregate "score")
- Analysis of model failure modes
- Initial answer to RQ1–RQ5

**Graduation Criteria:**
- [ ] At least 3 models evaluated
- [ ] Component metrics reported without overclaiming
- [ ] Analysis does not conflate benchmark performance with cultural competence
- [ ] Results reviewed before public release

---

## Phase 5 — Adversarial Context-Swap and Minimal-Pair Benchmark

**Goal:** Formalise and expand the context-swap and minimal-pair test concepts, including adversarial pragmatic structures identified during reference-corpus analysis.

**Deliverables:**
- Extended context-swap dataset (same utterance, different contexts)
- Minimal-pair examples differing in speaker relationship, preceding event, or social setting
- Authority-inversion, question-intent, persona, and institutional-frame swap families
- Tall-poppy/status-calibration families separating playful status deflation, scepticism toward unsupported self-promotion, and unfair suppression of demonstrated competence
- Analysis of whether context-swap failures correlate with lexical shortcuts
- Answers to RQ6 and RQ7

**Graduation Criteria:**
- [ ] Context-swap examples cover at least 10 distinct utterance types
- [ ] Results show whether models use context beyond lexical content
- [ ] Methodology is replicable without proprietary dependencies
- [ ] Media-inspired benchmark items are independently authored or appropriately licensed
- [ ] Tall-poppy/status items do not encode "Australians dislike success" as a universal cultural rule

---

## Phase 6 — Moderation-Fairness Evaluation

**Goal:** Investigate whether content moderation systems produce disparate false-positive rates for Australian pragmatic language compared to denotatively similar non-Australian language.

**Deliverables:**
- Moderation-fairness evaluation methodology
- Results on at least 2 publicly accessible moderation systems
- Analysis of false-positive and false-negative patterns
- Answer to RQ5

**Graduation Criteria:**
- [ ] Methodology reviewed for ethical soundness
- [ ] Results do not identify individuals
- [ ] Limitations of moderation system API access are documented

---

## Phase 7 — Cross-Dialect Comparison

**Goal:** Investigate whether methods and findings from Australian English generalise to other dialects or culturally dependent pragmatic registers, without assuming they do.

**Deliverables:**
- Comparative framework for at least one additional dialect
- Analysis of shared and divergent pragmatic mechanisms
- Answer to RQ8
- Explicit documentation of what does and does not generalise

**Graduation Criteria:**
- [ ] At least one additional dialect included with appropriate cultural consultation
- [ ] Results do not assume Australian conventions are universal
- [ ] Collaborators from relevant linguistic communities are involved

---

## Phase 8 — Research Paper and Archival Release

**Goal:** Produce a citable, peer-reviewed research publication and an archivally deposited benchmark release.

**Deliverables:**
- Research paper submitted to a peer-reviewed venue
- Archived dataset with DOI
- Updated CITATION.cff with real metadata
- Final benchmark package suitable for independent replication

**Graduation Criteria:**
- [ ] Paper accepted at peer-reviewed venue
- [ ] Dataset archived with persistent identifier
- [ ] Replication instructions verified by independent researcher
- [ ] All metadata in CITATION.cff is accurate and complete
