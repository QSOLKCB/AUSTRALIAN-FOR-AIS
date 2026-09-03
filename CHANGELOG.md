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
