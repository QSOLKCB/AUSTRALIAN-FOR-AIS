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

Australian For AIs is a cultural-pragmatics research project and benchmark for evaluating how
artificial intelligence systems understand Australian English — particularly humour, irony,
understatement, profanity, affectionate insults, social context, discourse markers, ambiguity,
and intended meaning.

This project sits at the intersection of AI ethics, cultural bias, natural-language pragmatics,
AI safety, moderation fairness, sentiment analysis, intent recognition, uncertainty calibration,
sociolinguistics, cross-cultural NLP, and human–AI interaction.

The core research principle is:

> Language meaning is conditional on context, culture, relationship, discourse, and uncertainty.
> Surface lexical meaning alone is not sufficient evidence of intended social meaning.

Australian English is used as a benchmark environment because it makes extensive use of
understatement, irony, sarcasm, deadpan humour, inverse praise, affectionate insults, profanity
without hostility, social teasing, contextual ambiguity, and deliberately understated descriptions
of extreme situations.

See [README4AI.md](README4AI.md) for a machine-oriented description of this repository.

---

## Why This Matters for AI Ethics

If an AI system incorrectly classifies ordinary pragmatic language as hostile, abusive, or
violating, several ethically important failure modes are possible:

- Content moderation false positives may suppress legitimate speech
- Sentiment analysis may misrepresent community opinion
- Intent recognition systems may produce misleading signals
- Safety-tuned models may develop blind spots toward non-dominant dialects and registers
- Linguistic communities may experience unequal friction from systems calibrated to other norms

Phase 1 treats these as **researchable risks**, not measured prevalence claims. Later phases are
intended to test them empirically rather than assume the conclusion in advance.

---

## Research Reference Corpus

The project maintains a [research reference corpus](docs/RESEARCH-REFERENCE-CORPUS.md) for
studying pragmatic mechanisms in Australian comedy and satire.

Initial references include *Fast Forward*, *Full Frontal*, *skitHOUSE*, *The Eric Bana Show Live*,
*Russell Coight's All Aussie Adventures*, *Hey Dad..!*, Col'n Carpenter, and The Chaser, with
The Chaser treated as a particularly valuable source of adversarial institutional pragmatics.

These works are **references, not benchmark data**. The project does not copy scripts, subtitles,
or programme dialogue into the dataset merely because a work is useful to study. Instead, later
benchmark items should use independently authored or appropriately licensed examples that isolate
the relevant pragmatic mechanism.

A theoretical preprint is also registered as a hypothesis source. Its preprint status is preserved
explicitly rather than treating it as settled evidence.

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

---

## Project Maturity

**Phase 1 — Research Substrate (current)**

This repository contains the research contracts, schemas, methodology documentation,
synthetic starter fixtures, reference evaluator, tests, provenance boundaries, and roadmap needed
for later dataset expansion. Phase 1 is not scientifically validated. It is a scaffold for future work.

See [ROADMAP.md](ROADMAP.md) for planned phases.

---

## Repository Architecture

```
README.md                  — This file (human-oriented)
README4AI.md               — Machine-oriented project description
AGENTS.md                  — Instructions for AI agents working in this repo
ROADMAP.md                 — Phased development plan
CHANGELOG.md               — Change history
CONTRIBUTING.md            — Contribution guidelines
CODE_OF_CONDUCT.md         — Community standards
CITATION.cff               — Citation metadata

docs/
  INVARIANTS.md            — Core research invariants (AU-HUMOUR-001 to AU-HUMOUR-010)
  METHODOLOGY.md           — Research methodology
  ETHICS.md                — Ethical considerations and risks
  ANNOTATION-GUIDE.md      — How future human annotation should work
  BENCHMARK-DESIGN.md      — Benchmark design rationale
  DATA-GOVERNANCE.md       — Data provenance and governance
  RESEARCH-REFERENCE-CORPUS.md — Reference works and source-use boundaries
  LIMITATIONS.md           — Known limitations
  GLOSSARY.md              — Terminology

schemas/
  example.schema.json      — JSON Schema for benchmark examples
  evaluation.schema.json   — JSON Schema for evaluation records

data/
  README.md                — Dataset description
  starter/
    examples.jsonl         — Synthetic starter fixtures (Phase 1)

src/australian_for_ais/
  __init__.py
  models.py                — Data models (dataclasses)
  validation.py            — Record validation
  scoring.py               — Deterministic reference evaluator
  cli.py                   — Command-line interface

tests/
  test_schema.py
  test_validation.py
  test_scoring.py
  fixtures/                — Test fixtures

scripts/
  validate_dataset.py      — Dataset validation script
  evaluate_predictions.py  — Prediction evaluation script

.github/workflows/
  ci.yml                   — Continuous integration

pyproject.toml             — Project metadata and dependencies
```

---

## Quickstart

### Install

```bash
pip install -e ".[dev]"
```

### Validate example records

```bash
python -m australian_for_ais.cli validate data/starter/examples.jsonl
```

### Evaluate predictions

```bash
python -m australian_for_ais.cli evaluate \
    data/starter/examples.jsonl \
    predictions.jsonl
```

### Run tests

```bash
pytest
```

### Validate via script

```bash
python scripts/validate_dataset.py data/starter/examples.jsonl
```

---

## Research Questions

See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for the full list. Selected examples:

- **RQ1**: Can language models distinguish lexical profanity from social aggression?
- **RQ5**: Do safety or moderation systems disproportionately classify ordinary Australian
  discourse as hostile or abusive?
- **RQ7**: Do context-swap examples expose reliance on lexical shortcuts?

---

## How Researchers Can Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

Short version:

1. Read [docs/INVARIANTS.md](docs/INVARIANTS.md) before touching data or evaluation code.
2. Read [docs/RESEARCH-REFERENCE-CORPUS.md](docs/RESEARCH-REFERENCE-CORPUS.md) before deriving examples from media references.
3. Do not fabricate citations or annotations.
4. Do not flatten ambiguity into false certainty.
5. Preserve stable example IDs.
6. Open an issue before making significant schema or methodology changes.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).
