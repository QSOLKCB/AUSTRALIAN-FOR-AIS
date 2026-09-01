# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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

### Removed

- Generated `__pycache__`, `.pyc`, and `*.egg-info` artefacts accidentally committed by the bootstrap environment

### Notes

Phase 1 is a research substrate, not a scientifically validated release.
No benchmark scores should be reported based on Phase 1 alone.
