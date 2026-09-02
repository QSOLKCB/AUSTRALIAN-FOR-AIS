# Australian For AIs

**A Cultural-Pragmatics Benchmark for Ethical Language Understanding**

> "Australian English is an unusually effective place to discover whether your language model
> understands context or merely owns a very expensive dictionary."

---

## Research Question

> "What harms arise when an AI mistakes culturally normal pragmatic language for hostility,
> abuse, agreement, disagreement, consent, sentiment, or intent?"

---

## What Is Australian For AIs?

Australian For AIs is a cultural-pragmatics research project and benchmark for evaluating how artificial intelligence systems understand Australian English, particularly humour, irony, understatement, profanity, affectionate insults, social context, discourse markers, ambiguity, and intended meaning.

This project sits at the intersection of AI ethics, cultural bias, natural-language pragmatics, AI safety, moderation fairness, sentiment analysis, intent recognition, uncertainty calibration, sociolinguistics, cross-cultural NLP, and human-AI interaction.

The core research principle is:

> Language meaning is conditional on context, culture, relationship, discourse, and uncertainty.
> Surface lexical meaning alone is not sufficient evidence of intended social meaning.

Australian English is used as a benchmark environment because it makes extensive use of understatement, irony, sarcasm, deadpan humour, inverse praise, affectionate insults, profanity without hostility, social teasing, contextual ambiguity, and deliberately understated descriptions of extreme situations.

See [README4AI.md](README4AI.md) for a machine-oriented description of this repository.

---

## Why This Matters for AI Ethics

If an AI system incorrectly classifies ordinary pragmatic language as hostile, abusive, or violating, several ethically important failure modes are possible:

- Content moderation false positives may suppress legitimate speech
- Sentiment analysis may misrepresent community opinion
- Intent recognition systems may produce misleading signals
- Safety-tuned models may develop blind spots toward non-dominant dialects and registers
- Linguistic communities may experience unequal friction from systems calibrated to other norms

These are **researchable risks**, not assumed prevalence claims. Later phases are intended to test them empirically rather than assume the conclusion in advance.

---

## Research Reference Corpus

The project maintains a [research reference corpus](docs/RESEARCH-REFERENCE-CORPUS.md) for studying pragmatic mechanisms in Australian comedy and satire.

Initial references include *Fast Forward*, *Full Frontal*, *skitHOUSE*, *The Eric Bana Show Live*, *Russell Coight's All Aussie Adventures*, *Hey Dad..!*, Col'n Carpenter, and The Chaser, with The Chaser treated as a particularly valuable source of adversarial institutional pragmatics.

These works are **references, not benchmark data**. The project does not copy scripts, subtitles, or programme dialogue into the dataset merely because a work is useful to study. Instead, later benchmark items should use independently authored or appropriately licensed examples that isolate the relevant pragmatic mechanism.

A theoretical preprint is also registered as a hypothesis source. Its preprint status is preserved explicitly rather than treating it as settled evidence.

---

## What This Project Does NOT Claim

- Australian English is not homogeneous. Speaker variation is large and significant.
- This project does not claim to represent all Australian speakers or all regions.
- Individual example annotations do not represent universal Australian interpretation.
- A high benchmark score does not mean a model is culturally competent.
- This project does not claim the phenomena studied are unique to Australian English.
- Findings are not assumed to generalise automatically to other dialects.
- Comedy programmes are not treated as representative samples of Australian speakers.
- A research reference does not automatically grant permission to redistribute its dialogue.
- Phase 2 tooling does not imply that real human annotation has already occurred.

---

## Project Maturity

**Phase 1 — Research Substrate:** PR #1 established the contracts, schemas, synthetic starter fixtures, deterministic evaluator, provenance boundaries, and review-hardened validation substrate.

**Phase 2 — Pilot Human Annotation:** the Phase 2 implementation adds a 60-item unannotated synthetic pilot pack, offline annotation interface, independent annotation schema, agreement analysis, pilot protocol, and mechanism-selection review. Human collection and ethical review remain pending until actual participants complete the pilot.

See [ROADMAP.md](ROADMAP.md) for graduation criteria and future phases.

---

## Phase 2 Pilot

The pilot pack lives at:

```text
data/pilot/items.jsonl
```

It contains 60 independently authored synthetic prompts arranged as 30 same-utterance context contrasts. Pilot items contain no gold pragmatic labels.

Open the offline annotation tool directly in a browser:

```text
annotation/index.html
```

The interface asks annotators to load the pilot JSONL, use a pseudonymous annotator ID, make independent decisions from the supplied context, save locally, and export annotation JSONL. It makes no network requests.

Validate the pilot pack:

```bash
python -m australian_for_ais.cli validate-pilot data/pilot/items.jsonl
```

Validate collected annotations:

```bash
python -m australian_for_ais.cli validate-annotations \
    data/pilot/items.jsonl \
    annotations.jsonl
```

Generate agreement and coverage results:

```bash
python -m australian_for_ais.cli agreement \
    data/pilot/items.jsonl \
    annotations.jsonl
```

See [docs/PHASE2-PILOT-PROTOCOL.md](docs/PHASE2-PILOT-PROTOCOL.md) before recruiting or collecting human annotations.

---

## Repository Architecture

```text
README.md                  — This file (human-oriented)
README4AI.md               — Machine-oriented project description
AGENTS.md                  — Instructions for AI agents working in this repo
ROADMAP.md                 — Phased development plan
CHANGELOG.md               — Change history
CONTRIBUTING.md            — Contribution guidelines
CODE_OF_CONDUCT.md         — Community standards
CITATION.cff               — Citation metadata

annotation/
  index.html               — Self-contained offline Phase 2 annotation interface

docs/
  INVARIANTS.md            — Core research invariants (AU-HUMOUR-001 to AU-HUMOUR-010)
  METHODOLOGY.md           — Research methodology
  ETHICS.md                — Ethical considerations and risks
  ANNOTATION-GUIDE.md      — Human annotation guidance
  PHASE2-PILOT-PROTOCOL.md — Pilot procedure and ethical-review checklist
  PHASE2-MECHANISM-REVIEW.md — Pilot taxonomy review
  BENCHMARK-DESIGN.md      — Benchmark and annotation record contracts
  DATA-GOVERNANCE.md       — Data provenance and governance
  RESEARCH-REFERENCE-CORPUS.md — Reference works and source-use boundaries
  LIMITATIONS.md           — Known limitations
  GLOSSARY.md              — Terminology

schemas/
  example.schema.json      — JSON Schema for benchmark examples
  evaluation.schema.json   — JSON Schema for evaluation records
  pilot-item.schema.json   — Phase 2 unannotated pilot item schema
  annotation.schema.json   — Phase 2 independent human annotation schema

data/
  README.md                — Dataset description
  starter/examples.jsonl   — Synthetic Phase 1 fixtures
  pilot/items.jsonl        — 60-item unannotated Phase 2 pilot pack
  pilot/README.md          — Pilot-data status and use boundary

src/australian_for_ais/
  models.py                — Benchmark, pilot, annotation, and evaluation models
  validation.py            — Schema and semantic validation
  scoring.py               — Deterministic Phase 1 reference evaluator
  annotation.py            — Phase 2 loading, coverage, and agreement analysis
  cli.py                   — Offline command-line interface

scripts/
  validate_dataset.py      — Dataset validation script
  evaluate_predictions.py  — Prediction evaluation script
  analyse_annotations.py   — Phase 2 agreement report wrapper

.github/workflows/ci.yml   — Continuous integration
pyproject.toml             — Project metadata and dependencies
```

---

## Quickstart

### Install

```bash
pip install -e ".[dev]"
```

### Validate Phase 1 example records

```bash
python -m australian_for_ais.cli validate data/starter/examples.jsonl
```

### Evaluate predictions

```bash
python -m australian_for_ais.cli evaluate \
    data/starter/examples.jsonl \
    predictions.jsonl
```

### Validate the Phase 2 pilot pack

```bash
python -m australian_for_ais.cli validate-pilot data/pilot/items.jsonl
```

### Run tests

```bash
pytest
```

---

## Research Questions

See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for the full list. Selected examples:

- **RQ1**: Can language models distinguish lexical profanity from social aggression?
- **RQ5**: Do safety or moderation systems disproportionately classify ordinary Australian discourse as hostile or abusive?
- **RQ7**: Do context-swap examples expose reliance on lexical shortcuts?

---

## How Researchers Can Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

Short version:

1. Read [docs/INVARIANTS.md](docs/INVARIANTS.md) before touching data or evaluation code.
2. Read [docs/RESEARCH-REFERENCE-CORPUS.md](docs/RESEARCH-REFERENCE-CORPUS.md) before deriving examples from media references.
3. Do not fabricate citations, human annotators, or annotation results.
4. Do not flatten ambiguity into false certainty.
5. Preserve stable example IDs.
6. Open an issue before making significant schema or methodology changes.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).
