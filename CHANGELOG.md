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

### Changed

- Clarified that potential moderation, sentiment, and intent-classification harms are researchable risks rather than measured Phase 1 prevalence claims
- Expanded human and AI documentation with a strict `research reference != redistributable data` boundary
- Added provenance rules for media-inspired benchmark design and noisy automatic transcripts
- Removed an invented `date-released` value from `CITATION.cff`; unreleased metadata now remains explicitly pre-release
- Added candidate future mechanism families for institutional satire, performed persona, unreliable authority, and frame switching without silently expanding the active schema

### Removed

- Generated `__pycache__`, `.pyc`, and `*.egg-info` artefacts accidentally committed by the bootstrap environment

### Notes

Phase 1 is a research substrate, not a scientifically validated release.
No benchmark scores should be reported based on Phase 1 alone.
