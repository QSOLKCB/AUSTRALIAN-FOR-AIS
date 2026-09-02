# Roadmap

This roadmap describes planned phases for the Australian For AIs project.

Phases are listed in order. No phase is marked complete until its graduation criteria are explicitly satisfied and documented. Future phases are not complete.

Planning reports, comedy/reference surveys, and external audits may inform this roadmap, but they are **research inputs rather than executable truth**. Recommendations are checked against the current repository before becoming project commitments, and stale status claims are not preserved merely because they appeared in an earlier report.

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

## Phase 2 — Pilot Human Annotation *(tooling merged in PR #2; human collection pending)*

**Goal:** Develop annotation tooling and conduct a small-scale pilot with real human annotators.

**Implementation status:** PR #2 merged a 60-item unannotated synthetic pilot pack, a self-contained offline annotation interface, strict per-annotator validation, locally generated pseudonymous annotation records, deterministic agreement analysis, a pilot protocol, and a mechanism-selection review. This does **not** claim that real human annotation or ethical review has already occurred.

**Deliverables:**
- [x] Offline annotation interface or workflow
- [x] Inter-annotator agreement analysis tools
- [x] 60-item unannotated synthetic pilot pack with 30 same-utterance context contrasts
- [ ] Pilot annotation of ~50–100 examples with multiple real annotators
- [ ] Revised annotation guide based on pilot experience
- [x] Mechanism-selection review informed by the Phase 1 research reference corpus

**Graduation Criteria:**
- [ ] Pilot annotation completed with at least 2 annotators per example
- [ ] Inter-annotator agreement measured and reported
- [ ] Annotation guide updated to reflect lessons learned from actual pilot use
- [ ] Ethical review of annotation process completed

---

## Cross-Phase Workstreams After PR #2

These workstreams may be implemented as focused PRs before or alongside Phase 3. They do not bypass Phase 2 graduation criteria.

### A. Research-corpus expansion and source governance

**Goal:** Broaden the reference corpus without turning copyrighted comedy, historical stereotypes, or cultural commentary into benchmark ground truth.

Planned work includes:
- expand the comedy/reference registry beyond the initial television set using candidate directions identified in post-Phase-2 research reports, but do not treat a named work as an adopted project reference until `docs/RESEARCH-REFERENCE-CORPUS.md` records its source links, provenance/rights boundary, epistemic status, and safe research use;
- prefer official, archival, creator, broadcaster, and peer-reviewed sources over orientation-only summaries where available;
- add academic work on cross-cultural humour, First Nations/Blak comedy, diversity in Australian comedy, and Australian humour as a sociolinguistic or social-regulatory phenomenon only when each source is formally registered;
- map each registered research source to candidate pragmatic mechanisms, relevant invariants, evidential status, and safe synthetic experiment families;
- retain the rule **RESEARCH REFERENCE != REDISTRIBUTABLE DATA**;
- treat performed comedy as mechanism-discovery material, not as a representative corpus of Australian speech.

First Nations, migrant, multicultural, regional, class-marked, or other community-specific material must not be converted into benchmark claims by outsiders alone. Where a future dataset family depends on community-specific pragmatic knowledge, appropriate consultation, permissions, provenance, and scope limitations are required. If those conditions cannot be met, the family should remain a research hypothesis rather than benchmark data.

### B. Mechanism qualification rather than taxonomy inflation

**Goal:** Use real pilot evidence to decide whether new mechanism labels are useful before modifying the benchmark contract.

The active Phase 2 taxonomy remains fixed during the human pilot. After pilot collection, review:
- frequency and distribution of `unknown` selections;
- mechanism-set overlap and recurring disagreement patterns;
- annotator notes describing missing concepts;
- confusion among neighbouring labels such as sarcasm, irony, inverse praise, affectionate insult, relational teasing, and tall-poppy humour;
- whether `self_deprecation`, `relational_teasing`, `tall_poppy_humour`, and `absurdist_escalation` are applied consistently enough to remain useful;
- whether any label encourages stereotypes, deterministic phrase rules, or over-generalisation.

Candidate future mechanism families include:
- `institutional_mimicry`
- `satirical_question_form`
- `performative_sincerity`
- `unreliable_authority`
- `performed_persona`
- `character_speaker_separation`
- `frame_switching`
- `implicature_failure`
- `larrikin_register`
- `cultural_cringe_inversion`
- carefully scoped class-marked register hypotheses

Pilot evidence may nominate a candidate, but **nomination is not schema promotion**. Before any candidate label is added to the active taxonomy, the project must define it provisionally and run an independent trial-coding or re-annotation round on suitable items. That trial must review whether annotators can apply the candidate consistently, whether it improves on existing labels or `unknown`, and whether its agreement/confusion pattern supports keeping it distinct. Only after that evidence is documented may a contract-changing PR update schemas, models, documentation, interface options, and tests together.

No candidate is promoted solely because it is culturally salient or appears frequently in comedy.

### C. Genuine-hostility and uncertainty controls

**Goal:** Ensure the benchmark can distinguish benign hostile-looking language from actual hostility instead of rewarding an always-benign classifier.

Planned work includes:
- introduce a small, ethically reviewed set of clearly hostile synthetic controls;
- include `hostility: "uncertain"` cases where the supplied evidence is genuinely underdetermined;
- build matched contrasts between affectionate insult/profanity/teasing and genuine aggression;
- use content warnings and annotator protections where appropriate;
- keep hostile controls proportionate and research-motivated rather than increasing offensive content for its own sake.

These controls are particularly important before Phase 6 moderation-fairness evaluation.

### D. Runtime and reproducibility hardening

**Goal:** Keep benchmark behaviour stable across supported Python versions and parser/runtime changes.

Current support contract:
- [x] Python 3.11 and 3.12 are the currently advertised and CI-tested package range.
- [x] Package metadata is temporarily constrained to `>=3.11,<3.13` so unverified newer runtimes are not silently advertised as supported.

Planned work includes:
- establish Python 3.13 and 3.14 compatibility in CI before removing the temporary `<3.13` package bound or describing those runtimes as supported;
- make excessive-JSON-nesting rejection an explicit project contract rather than relying on a particular Python parser raising `RecursionError`;
- preserve fail-closed handling for duplicate keys, pathological integers, non-finite values, cyclic in-memory structures, malformed JSON, Unicode decoding failures, and schema-diagnostic hazards;
- add useful test-coverage reporting without weakening deterministic test gates;
- keep clean-wheel/schema-resource smoke tests as release hygiene.

### E. Research-output and dataset infrastructure

**Goal:** Prepare the project for larger datasets and reproducible downstream analysis without prematurely freezing a leaderboard format.

Current capability:
- [x] Evaluation and agreement commands already emit machine-readable JSON.

Candidate work includes:
- define a versioned result/submission schema building on the existing JSON output before public leaderboard or cross-run aggregation work;
- directory-level validation for larger dataset collections;
- an explicit dataset-split contract before Phase 3/4 train/dev/test use becomes necessary;
- glossary expansion for culturally important research terms such as larrikin, Tall Poppy Syndrome, taking the piss, cultural cringe, and carefully scoped class-marked terminology.

### F. ASCFT-derived adversarial pragmatics

**Goal:** Operationalise Australian Sketch Comedy Field Theory (ASCFT) as a theory-derived source of adversarial pragmatic experiments without treating its qutrit, field, collapse, or attractor language as established physical ontology or as representative cultural ground truth.

ASCFT is a candidate theoretical source and must pass the same source-registration contract as other post-Phase-2 research inputs before a benchmark family depends on it. Its useful starting structure is a three-state analytic basis:
- `|0>` Informal Larrikin Compression;
- `|1>` Bureaucratic Recursive Formalism;
- `|2>` Hyper-Formal Surreal Narration.

The project should treat these states as operational representations for experiment design. They may motivate controlled variables such as frame stability, authority register, semantic drift, recursive contradiction, category instability, demonstrated competence, abrupt pragmatic reframing, and collapse/termination structure. They do not by themselves establish that humour is governed by quantum mechanics, physical field dynamics, or a literal cultural vacuum state.

Candidate adversarial experiment families include:
- authority-register pairs holding confident formal delivery constant while varying whether the speaker is a competent expert, a recursively incoherent bureaucrat, or a deadpan surreal narrator;
- formal-coherence versus epistemic-coherence pairs where syntax and register remain polished while factual or inferential coherence changes;
- claimed-versus-demonstrated-competence pairs that separate authoritative performance from evidence of successful reasoning or action;
- frame-stability versus semantic-stability pairs in which a scene preserves its institutional or documentary frame while meaning progressively destabilises;
- deadpan literal-intent pairs separating delivery style from sincere assertion;
- semantic-drift and contradiction-accumulation sequences that test whether a model notices degradation across turns rather than scoring each utterance in isolation;
- mode-transition families that move between informal compression, bureaucratic recursion, and hyper-formal narration while holding topic or surface vocabulary as constant as practical;
- source-specific attractor motifs, including ASCFT's proposed "goat attractor", as hypotheses to test against documented source material rather than universal Australian-comedy rules.

Candidate invariants for review include:
- **AUTHORITATIVE REGISTER != SINCERE ASSERTION**
- **FORMAL COHERENCE != EPISTEMIC COHERENCE**
- **ASSERTED COMPETENCE != DEMONSTRATED COMPETENCE**
- **NARRATIVE STABILITY != SEMANTIC STABILITY**
- **DEADPAN DELIVERY != LITERAL INTENT**
- **FORMAL ANALOGY != PHYSICAL ONTOLOGY**
- **MATHEMATICAL MODEL != EMPIRICALLY VALIDATED MECHANISM**

These are candidate invariants, not additions to the canonical AU-HUMOUR set. Any promotion requires explicit invariant review and coordinated documentation changes.

A focused follow-up PR should:
- formally register ASCFT with provenance, rights, epistemic status, community-governance classification, project mappings, and a safe abstraction path;
- create an ASCFT operational crosswalk mapping source terminology to observable benchmark manipulations without claiming literal physical equivalence;
- define independently authored synthetic minimal pairs and context swaps for the strongest testable mechanisms;
- keep source dialogue, transcript wording, and distinctive copyrighted expression out of redistributable benchmark data;
- separate source-specific motifs from general claims about Australian humour;
- identify which candidate mechanisms can be expressed using the current taxonomy and which, if any, require later provisional trial coding under Workstream B;
- add deterministic regressions for any new machine-readable contract introduced by the crosswalk or synthetic-family format.

The epistemic boundary for this workstream is explicit: ASCFT may be used as a formal analytic framework and hypothesis generator. Stronger claims that its field equations, qutrit states, collapse operators, attractors, Lagrangian, or cultural-stress observables constitute empirically validated physical mechanisms require independent evidence and are not assumed by this benchmark.

---

## Phase 3 — Multi-Annotator Culturally Contextualised Dataset

**Goal:** Produce a dataset with genuine human annotations, multiple interpretations per example, explicit confidence ratings, documented disagreement, and broader pragmatic coverage than the initial pilot.

**Deliverables:**
- Dataset of 200–500 examples with multi-annotator labels
- Provenance and consent documentation for all examples
- Formal inter-annotator agreement analysis
- Dataset card following established NLP data documentation practice
- Expanded controlled families for tall-poppy/status calibration, self-deprecation, relational teasing/taking-the-piss, absurdist escalation, understatement, discourse markers, affectionate insult, profanity, literal controls, and genuine-hostility controls
- Additional context-swap groups where relationship, preceding event, authority status, social setting, or discourse frame is the controlled manipulation
- Research-corpus-to-benchmark design notes showing how mechanisms were abstracted into original or appropriately licensed data

**Cultural-governance requirement:**

First Nations/Blak, migrant, multicultural, regional, class-marked, or other community-specific example families are **not automatic Phase 3 requirements**. They may be included only when the project has appropriate cultural consultation, provenance, permissions, and a defensible claim boundary. Absence is preferable to invented representation.

**Graduation Criteria:**
- [ ] Dataset ethics review completed
- [ ] Provenance documented for all examples
- [ ] Inter-annotator agreement reported with appropriate metrics
- [ ] Data release reviewed against privacy and consent requirements
- [ ] Every active mechanism intended for evaluation has meaningful human-annotated coverage or is explicitly retired/deferred
- [ ] Hostility controls are sufficient to detect degenerate always-benign predictions
- [ ] Community-specific material, if present, has documented consultation and scope limitations

---

## Phase 4 — Baseline Evaluation

**Goal:** Evaluate a selection of publicly available language models against the Phase 3 dataset using the reference evaluator and extended metrics.

**Deliverables:**
- Evaluation pipeline for local and API-accessible models
- Baseline scores on component metrics, not a single aggregate "Australian understanding score"
- Versioned machine-readable result records building on the existing JSON CLI output
- Calibration, coverage, ambiguity-recognition, hostility, social-valence, pragmatic, and context-sensitivity reporting
- Analysis of model failure modes
- Initial answer to RQ1–RQ5

**Graduation Criteria:**
- [ ] At least 3 models evaluated
- [ ] Component metrics reported without overclaiming
- [ ] Analysis does not conflate benchmark performance with cultural competence
- [ ] Missing predictions remain visible in dataset-level coverage and the applicable accuracy denominators rather than being silently dropped
- [ ] Unresolved categorical annotations such as `hostility: "uncertain"` and `social_valence: "unknown"` are excluded from their categorical accuracy denominators and reported separately, matching the reference evaluator contract
- [ ] Results reviewed before public release

---

## Phase 5 — Adversarial Context-Swap and Minimal-Pair Benchmark

**Goal:** Formalise and expand context-swap and minimal-pair tests, including adversarial pragmatic structures identified during reference-corpus analysis.

**Deliverables:**
- Extended context-swap dataset holding utterance constant while varying context and/or relationship
- Minimal-pair examples differing in speaker relationship, preceding event, social setting, authority status, demonstrated competence, persona, or discourse frame
- Authority-inversion and claimed-vs-demonstrated-competence families
- Question-intent families separating information seeking, accusation, sarcasm, satire, rhetorical challenge, and performative bait
- Persona and character-speaker-separation families
- Institutional-mimicry and authority-register-parody families
- Larrikin/anti-authority pragmatics studied as a hypothesis rather than a universal Australian rule
- Tall-poppy/status-calibration families separating playful status deflation, scepticism toward unsupported self-promotion, ordinary congratulations with deflationary humour, and unfair suppression of demonstrated competence
- Self-deprecation families separating conventional humility, genuine low confidence, irony, and defensive status management
- Absurdist-escalation families separating literal improbability, deadpan delivery, understatement, and surreal frame shifts
- Analysis of whether context-swap failures correlate with lexical shortcuts or authority/prestige shortcuts
- Answers to RQ6 and RQ7

**Graduation Criteria:**
- [ ] Context-swap examples cover at least 10 distinct utterance types and multiple manipulation dimensions
- [ ] Results show whether models use context beyond lexical content
- [ ] Relationship-only minimal pairs are represented where scientifically useful
- [ ] Methodology is replicable without proprietary dependencies
- [ ] Media-inspired benchmark items are independently authored or appropriately licensed
- [ ] Tall-poppy/status items do not encode "Australians dislike success" as a universal cultural rule
- [ ] Larrikin, cultural-cringe, class-marked, or institutional-satire families remain explicitly scoped hypotheses rather than national-character claims

---

## Phase 6 — Moderation-Fairness Evaluation

**Goal:** Investigate whether content moderation systems produce disparate false-positive or false-negative rates for Australian pragmatic language relative to explicitly defined, denotatively/pragmatically matched non-Australian or comparison-register counterparts, while separately testing benign-versus-hostile discrimination.

**Deliverables:**
- Moderation-fairness evaluation methodology
- Matched Australian-versus-non-Australian (or otherwise explicitly defined comparison-register) counterpart families suitable for estimating disparate error rates
- Matched benign-versus-hostile control families suitable for detecting false positives, false negatives, and degenerate always-benign behaviour
- Results on at least 2 publicly accessible moderation systems
- Analysis of false-positive and false-negative patterns by comparison group and hostility status
- Separate treatment of affectionate insult, profanity-non-hostile, relational teasing, satire, genuine hostility, and unresolved hostility
- Answer to RQ5

**Graduation Criteria:**
- [ ] Methodology reviewed for ethical soundness
- [ ] The evaluation includes matched Australian/comparison-register counterparts sufficient to support any disparate-rate claim
- [ ] The evaluation includes enough genuine-hostility controls that an always-benign classifier cannot appear successful
- [ ] Results do not identify individuals
- [ ] Limitations of moderation system API access are documented
- [ ] Cultural difference is not treated as evidence of harmlessness or harmfulness by itself

---

## Phase 7 — Cross-Dialect and Cross-Cultural Comparison

**Goal:** Investigate whether methods and findings from Australian English generalise to other dialects or culturally dependent pragmatic registers, without assuming that they do.

**Deliverables:**
- Comparative framework for at least one additional dialect or culturally situated pragmatic register
- Analysis of shared and divergent pragmatic mechanisms
- Use of published cross-cultural humour research as hypothesis-generation material, not as a lookup table for national character
- Answer to RQ8
- Explicit documentation of what does and does not generalise

**Graduation Criteria:**
- [ ] At least one additional dialect/register included with appropriate cultural consultation
- [ ] Results do not assume Australian conventions are universal
- [ ] Collaborators from relevant linguistic communities are involved
- [ ] Broad cultural comparison tables are not treated as ground-truth labels for individuals

---

## Phase 8 — Research Paper and Archival Release

**Goal:** Produce a citable, peer-reviewed research publication and an archivally deposited benchmark release.

**Deliverables:**
- Research paper submitted to a peer-reviewed venue
- Archived dataset with DOI
- Updated CITATION.cff with real metadata
- Versioned dataset card, benchmark schemas, evaluation protocol, and machine-readable result format
- Final benchmark package suitable for independent replication

**Graduation Criteria:**
- [ ] Paper accepted at peer-reviewed venue
- [ ] Dataset archived with persistent identifier
- [ ] Replication instructions verified by independent researcher
- [ ] All metadata in CITATION.cff is accurate and complete
- [ ] Archived release states which cultural/mechanism families were validated, deferred, or excluded and why
