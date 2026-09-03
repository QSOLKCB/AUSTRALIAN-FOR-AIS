# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — Post-Phase-2 Research Programme

### Changed

- Expanded canonical RQ5 in `docs/METHODOLOGY.md` to match the Phase 6 moderation-fairness design: disparate false-positive and false-negative rates are studied against explicitly defined matched non-Australian or comparison-register counterparts, while benign hostile-looking language versus genuine hostility is treated as a separate discrimination axis within the same study
- Temporarily constrained the advertised Python support range to CI-verified Python 3.11 and 3.12; Python 3.13/3.14 support remains a runtime-hardening target and must be established in CI before the upper bound is removed
- Expanded `ROADMAP.md` with post-Phase-2 research workstreams while preserving Phase 2 human-pilot graduation requirements and source/taxonomy governance gates
- Expanded `docs/RESEARCH-REFERENCE-CORPUS.md` with a formal source-registration contract and a first governed post-Phase-2 batch covering media and scholarship, including explicit source links, rights/provenance boundaries, epistemic status, project mappings, and safe benchmark-abstraction rules
- Added a regression that checks the governed research-reference batch retains its required rights, epistemic, consultation, and non-redistribution boundaries
- Synchronized `docs/METHODOLOGY.md` with the new trans-Tasman relational-pragmatics and slang/operational-intelligibility experiment families, including explicit relationship, reciprocity, mention/use, listener-background, slang-density, and task-criticality controls
- Replaced explicit nationality-stereotype wording in `ROADMAP.md` with abstract research placeholders and marked the New Zealand sexual sense of `root` as unestablished until an attributable New Zealand source is registered
- Pinned all newly adopted Workstream G/H registry entries in the governance regression and tightened source-link validation to reject localhost and other single-label HTTPS hosts
- Formally registered ASCFT under the governed research-source contract with explicit project-authored theoretical status, rights/provenance limits, source-specific mappings, and a safe-abstraction boundary rather than leaving Workstream F dependent on roadmap-only provenance
- Centralized ASCFT-derived authority-register, epistemic-coherence, demonstrated-competence, frame-stability, semantic-drift, contradiction-accumulation, and mode-transition experiment rules in `docs/METHODOLOGY.md`, preserving `FORMAL ANALOGY != PHYSICAL ONTOLOGY` and `MATHEMATICAL MODEL != EMPIRICALLY VALIDATED MECHANISM`
- Hardened research-reference validation to reject private, loopback, and other non-global IP-literal source destinations and to prevent all supported Markdown thematic-break forms from masquerading as substantive research or project mappings
- Centralized the ASCFT deadpan delivery-versus-intent construction rule with matched literal and nonliteral controls, and hardened mapping validation so bare blockquote markers and empty fenced-code containers cannot satisfy mandatory mapping content
- Strengthened delivery-versus-intent experiments to require the complete deadpan/non-deadpan × literal/nonliteral 2×2 crossing whenever a family claims to estimate delivery effects, and normalized registry validation around rendered Markdown semantics so commented-out entries, one-to-three-space-indented duplicate fields, nested empty block containers, and noncanonical numeric loopback host spellings fail closed
- Hardened governed-registry discovery and source contracts so fenced-code-wrapped entries or metadata, list-nested empty fences, reserved hostname suffixes, mutable community-governance downgrades, and arbitrary replacement of source-specific rights, epistemic, or safe-abstraction boundaries fail closed
- Reordered Markdown preprocessing so fenced comment literals cannot hide visible fields, preserved four-space-indented code semantics when identifying fences, and pinned every adopted source destination plus its source-type and pragmatic-relevance clause
- Hardened rendered-registry validation against comments opened inside indented code, links hidden in inline code, pinned clauses hidden in Markdown titles, empty rendered HTML mappings, hidden registration-contract sections, and nested fences that outlive their quote/list container
- Added source-gated Workstream I for Australian and United States policing-context transfer, requiring jurisdiction/date/source metadata, independently authored examples, explicit legal-review boundaries, and separation of institutional-script comparison from national moral ranking
- Centralized Workstream I policing-context methodology with jurisdiction/date metadata, source hierarchy, matched construction controls, observable-variable treatment of the proposed Australian `lighter touch` hypothesis, and legal-review gates; hardened rendered roadmap and registry validation for paragraph continuations, link-reference-only mappings, pinned DOI metadata, and image-only source links
- Hardened rendered-Markdown validators for recursively composed quote/list containers, tab-indented code, visible-only policing safeguards, multiline code-span/comment boundaries, non-rendering `script`/`style`/`template` content, and full-field integrity checks for governed rights, epistemic, and safe-use boundaries
- Extended the exact-head Markdown hardening to tab-expanded comment boundaries, list-aware continuation indentation, browser-hidden HTML (`hidden`, `aria-hidden`, `display:none`, and `visibility:hidden`), quote/list-contained source-field uniqueness, pinned DOI link destinations, registration-contract section scoping, complete governance-rationale and source-type integrity, full paragraph-continuation hashing, recursively composed mapping containers, and affirmative policing safeguards that reject negated source gates
- Canonicalized equivalent CommonMark strong-emphasis metadata labels before registry field counting so forms such as `__DOI:__` cannot bypass uniqueness checks, and restored the complete Phase 1 changelog history that had been accidentally truncated during review cleanup

- Closed the next review round by making registry fence ownership container-order-aware, canonicalizing visible HTML strong metadata labels, explicitly governing community-attestation sources, and decoupling Australian-English familiarity from nationality and general language background in Workstream H

---

## [Unreleased] — Phase 2 Pilot Human Annotation

### Added

- `schemas/pilot-item.schema.json` for unannotated Phase 2 pilot prompts
- `schemas/annotation.schema.json` for independent pseudonymous human annotations
- Packaged copies of both Phase 2 schemas for installed-wheel validation
- `PilotItem` and `HumanAnnotation` data models
- Phase 2 pilot/annotation semantic validation using the existing uncertainty contract
- `src/australian_for_ais/annotation.py` with pilot loading, annotation loading, coverage reporting, categorical pairwise agreement, pairwise Cohen's kappa, mechanism-set overlap, and confidence-difference summaries
- CLI commands: `validate-pilot`, `validate-annotations`, `agreement`
- `scripts/analyse_annotations.py` wrapper for deterministic annotation analysis
- Self-contained offline browser annotation interface at `annotation/index.html`
- 60 independently authored synthetic pilot items in `data/pilot/items.jsonl`, arranged as 30 same-utterance context contrasts and containing no gold pragmatic labels
- `docs/PHASE2-PILOT-PROTOCOL.md` with annotation procedure, independence requirements, privacy boundaries, validation commands, and ethical-review checklist
- `docs/PHASE2-MECHANISM-REVIEW.md` recording the active taxonomy review and tall-poppy/status-calibration hypothesis without promoting new labels
- Phase 2 schema, annotation, agreement, duplicate-assignment, and committed-pilot regression tests
- CI validation of the Phase 2 pilot pack and installed Phase 2 schema resources

### Changed

- Activated `docs/ANNOTATION-GUIDE.md` for Phase 2 while preserving the rule that annotations are interpretations rather than objective ground truth
- Extended `docs/BENCHMARK-DESIGN.md` with separate pilot-item and human-annotation contracts and transparent Phase 2 agreement reporting
- Extended `docs/METHODOLOGY.md` with the Phase 2 pilot procedure and IAA limitations
- Updated `README.md` with the offline pilot workflow and commands
- Updated `ROADMAP.md` to record Phase 2 tooling implementation while leaving real human annotation, ethical review, agreement reporting, and guide revision as incomplete graduation requirements
- Added tall-poppy/status-calibration context families to the future Phase 5 roadmap without encoding "Australians dislike success" as a universal rule
- Replaced editable annotator identifiers with locally generated read-only pseudonyms in the form `annotator-<12 lowercase hexadecimal characters>` so names, email addresses, and account handles are not exported as annotation identities
- Made Phase 2 ambiguity representation two-way: multiple retained pragmatic readings require `ambiguity: true`, while `ambiguity: true` continues to require at least two distinct normalized readings
- Made the `unknown` mechanism mutually exclusive with specific mechanism labels in both the annotation schema and browser interface
- Replaced pair-wide relationship disjunctions with the actual speaker relationship for each individual pilot item
- Replaced the fixed `+30` context-pair presentation pattern with pseudonym-specific deterministic first/later ordering and pseudonym-specific choice of which pair member appears first
- Made shared-browser pseudonym changes switch storage namespaces and reload annotator-specific state so one annotator's visible form cannot silently become another annotator's record
- Aligned Phase 2 retained-reading normalization between browser and Python validation using locale-independent lowercase plus collapsed whitespace while preserving Phase 1 case-folded scoring semantics
- Made `scripts/analyse_annotations.py` bootstrap the repository `src/` path so the documented command runs directly from a source checkout without an editable install

### Notes

- The Phase 2 pilot is an unannotated research fixture. No human annotation results, ethical approvals, or empirical agreement statistics are claimed until real pilot collection occurs.

---

## [Unreleased] — Phase 1 Research Substrate

### Added

- Repository structure, documentation, schemas, synthetic starter fixtures
- Core invariants (AU-HUMOUR-001 through AU-HUMOUR-010)
- JSON Schema for benchmark examples (`schemas/example.schema.json`)
- JSON Schema for evaluation records (`schemas/evaluation.schema.json`)
- Synthetic starter dataset: 15 illustrative examples in `data/starter/examples.jsonl`
- Python data models (`src/australian_for_ais/models.py`)
- Validation module (`src/australian_for_ais/validation.py`)
- Deterministic reference evaluator (`src/australian_for_ais/scoring.py`)
- Command-line interface (`src/australian_for_ais/cli.py`)
- Test suite (`tests/`)
- Utility scripts (`scripts/`)
- GitHub Actions CI workflow
- Research methodology documentation (`docs/METHODOLOGY.md`)
- Ethics documentation (`docs/ETHICS.md`)
- Annotation guide (`docs/ANNOTATION-GUIDE.md`)
- Benchmark design rationale (`docs/BENCHMARK-DESIGN.md`)
- Data governance policy (`docs/DATA-GOVERNANCE.md`)
- Research reference corpus and copyright/provenance boundary (`docs/RESEARCH-REFERENCE-CORPUS.md`)
- Limitations statement (`docs/LIMITATIONS.md`)
- Glossary (`docs/GLOSSARY.md`)
- Roadmap (`ROADMAP.md`)
- Root `.gitignore` covering Python bytecode, packaging metadata, caches, virtual environments, and local evaluation output
- Packaged JSON Schema resources for non-editable wheel installations
- Prediction coverage and Brier confidence-calibration components
- CI wheel smoke test proving packaged schemas remain available after installation

### Changed

- Clarified that potential moderation, sentiment, and intent-classification harms are researchable risks rather than measured Phase 1 prevalence claims
- Expanded human and AI documentation with a strict `research reference != redistributable data` boundary
- Added provenance rules for media-inspired benchmark design and noisy automatic transcripts
- Removed an invented `date-released` value from `CITATION.cff`; unreleased metadata now remains explicitly pre-release
- Added candidate future mechanism families for institutional satire, performed persona, unreliable authority, and frame switching without silently expanding the active schema
- Required every advertised prediction dimension in evaluation records
- Made accuracy denominators cover the complete benchmark so omitted predictions cannot inflate rates
- Made context-swap success require correct context-specific answers, not merely different strings
- Aligned every starter primary interpretation with an accepted scorable interpretation, except explicit `insufficient_context`
- Enforced the annotation-guide confidence ceiling for `insufficient_context`
- Reworked `yeah nah`, `nah yeah`, `old mate`, and related fixture notes to describe context-specific best estimates rather than fixed Australian-English rules
- Replaced rural-context inference with an explicit delivery cue for the deadpan heat fixture
- Replaced contradictory `literal` mechanism labels where pragmatic function differs from literal form
- Added project schema version `0.1.0` to machine-readable schema metadata
- Hardened dataset validation for duplicate IDs, non-object JSON, and whitespace-only provenance/licence metadata
- Restricted the model hostility type to `bool | Literal["uncertain"]`
- Added dataset-level validation for malformed context-swap groups: orphan members, changed utterances, duplicate contexts, and duplicate primary directions now fail closed
- Required ambiguous annotations to retain at least two distinct normalized pragmatic readings, including `insufficient_context` cases
- Made explicit `insufficient_context` predictions scorable instead of rewarding forced certainty
- Excluded unresolved `hostility: "uncertain"` annotations from categorical hostility accuracy and report their count separately
- Moved the documented lukewarm reading for `au-006` into the accepted pragmatic interpretations
- Rejected whitespace-only benchmark and prediction text across required linguistic/scorable fields
- Made `scripts/evaluate_predictions.py` return non-zero on missing/unknown prediction errors, matching the module CLI
- Reserved `insufficient_context` for exact sentinel-primary examples and rejected it from ordinary accepted-reading lists
- Required pairwise-disjoint accepted pragmatic direction sets in context-swap groups so overlapping ambiguous answers cannot earn swapped-direction credit
- Made empty benchmark datasets, malformed direct mapping IDs, directory JSONL inputs, and unreadable JSONL inputs fail closed
- Added finite `[0, 1]` confidence validation to direct `score()` calls before Brier arithmetic
- Clarified `au-008` by explicitly establishing that the referenced supermarket person is unknown to both speakers, preserving the acquaintance reading only as a different-context possibility
- Synchronized `docs/METHODOLOGY.md` with the hardened context-swap contract, including the sentinel/disjointness interaction
- Hardened JSONL parsing against invalid UTF-8, oversized integer tokens, duplicate object keys, and excessive parser nesting
- Added structure-wide validation preflight so pathological in-memory values outside confidence fields cannot trigger schema-diagnostic tracebacks
- Excluded unresolved `social_valence: "unknown"` annotations from categorical social-valence accuracy and report their count separately
- Required context-swap groups to preserve lexical case in the observed utterance, preventing case changes from masquerading as context-only swaps

### Removed

- Generated `__pycache__`, `.pyc`, and `*.egg-info` artefacts accidentally committed by the bootstrap environment

### Notes

Phase 1 is a research substrate, not a scientifically validated release.
No benchmark scores should be reported based on Phase 1 alone.
