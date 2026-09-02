# README4AI — Machine-Oriented Repository Description

This file is addressed to AI agents, language models, and automated tools working within this
repository. Read it before modifying any file.

---

## Epistemic Boundaries

You are operating within a research project. Epistemic precision is required.

- **Observation** and **inference** are distinct. Do not collapse them.
- **Annotator interpretation** is not the same as **objective ground truth**.
- **Benchmark performance** is not the same as **cultural competence**.
- **Model confidence** must not substitute for evidence about cultural context.
- **Ambiguity must be preserved**. Do not silently resolve uncertain cases into certainty.
- **Research reference** is not the same as **redistributable benchmark data**.
- **Comedic depiction** is not the same as **representative cultural ground truth**.

---

## Terminology

| Term | Definition |
|---|---|
| `utterance` | The observed linguistic form of a statement |
| `literal_interpretation` | The denotative, context-independent semantic reading |
| `pragmatic_interpretation` | The socially intended meaning given context, relationship, and culture |
| `context` | Situational information available at the time of utterance |
| `speaker_relationship` | The social relationship between speaker and addressee |
| `social_valence` | The social register of an utterance (e.g. friendly, hostile, neutral) |
| `hostility` | Whether aggressive social intent is present — a ternary: `true`, `false`, `uncertain` |
| `confidence` | Annotator's subjective certainty about a pragmatic interpretation, 0.0–1.0 |
| `ambiguity` | Whether multiple substantially different interpretations are plausible |
| `humour_mechanisms` | Taxonomy labels for the pragmatic device being used |
| `context_swap_group` | ID linking utterances that are identical but have different contexts |
| `research_reference` | External work used to identify mechanisms or hypotheses; not benchmark data by default |

---

## File Layout

```
schemas/example.schema.json          — Normative schema for every example record
schemas/evaluation.schema.json       — Schema for evaluation prediction records
data/starter/examples.jsonl          — Phase 1 synthetic fixtures (one JSON object per line)
src/australian_for_ais/models.py     — Python data models
src/australian_for_ais/validation.py — Validation logic
src/australian_for_ais/scoring.py    — Deterministic reference evaluator
src/australian_for_ais/cli.py        — CLI entry point
tests/                               — pytest test suite
docs/INVARIANTS.md                   — Core invariants. Read before modifying data.
docs/RESEARCH-REFERENCE-CORPUS.md    — External references and source-use boundaries.
```

---

## Schemas

Two schemas are normative:

1. `schemas/example.schema.json` — every record in `data/` must validate against this.
2. `schemas/evaluation.schema.json` — every prediction record must validate against this.

If you modify a schema, you must:
- Update all records that reference it.
- Update `src/australian_for_ais/models.py` accordingly.
- Update `docs/BENCHMARK-DESIGN.md` to document the change.
- Re-run the full test suite.

Candidate mechanism labels listed in `docs/RESEARCH-REFERENCE-CORPUS.md` are **not active schema
values**. Do not insert them into dataset records unless the schema contract is deliberately revised.

---

## Invariants

The invariants in `docs/INVARIANTS.md` are non-negotiable research contracts.

Critical examples:

- **AU-HUMOUR-001**: Lexical profanity ≠ social aggression.
- **AU-HUMOUR-002**: Surface sentiment ≠ pragmatic sentiment.
- **AU-HUMOUR-003**: "mate" must not be assigned a fixed social valence.
- **AU-HUMOUR-006**: Ambiguity must not be silently collapsed into certainty.
- **AU-HUMOUR-009**: Annotator interpretation ≠ objective ground truth.

You must not introduce logic that violates these invariants.

---

## What Agents May Modify

- `src/` — Python source code (with tests, and without breaking invariants)
- `tests/` — Test files (must not delete existing tests or reduce coverage)
- `docs/` — Documentation (preserve precision; do not overstate scientific validity)
- `data/starter/examples.jsonl` — Adding examples is acceptable; modifying stable IDs is not
- `scripts/` — Utility scripts

---

## What Agents Must Not Do

- Fabricate citations, author names, DOIs, ORCID identifiers, dates, release metadata, or institutional affiliations.
- Convert uncertain or ambiguous annotations into categorical ground truth.
- Assign a fixed social meaning to "mate", profanity, or context-dependent language.
- Invent cultural rules and present them as established facts.
- Claim a model "understands" culture based on benchmark score alone.
- Infer that a speaker is Australian (or any nationality) from language use.
- Infer ethnicity, nationality, or identity from language.
- Remove the `ambiguity` field or suppress uncertainty representation.
- Change an example's `id` once it has been committed to the dataset.
- Mark future roadmap phases as complete.
- Introduce network dependencies into the test suite.
- Copy television scripts, subtitles, episode transcripts, or bulk dialogue into the benchmark without an independently established licence and documented justification.
- Treat a web-accessible source as automatically redistributable.
- Commit generated Python bytecode, cache directories, local packaging metadata, virtual environments, or editor artefacts.

---

## Research Reference Handling

`docs/RESEARCH-REFERENCE-CORPUS.md` contains works used for research design, including Australian
sketch comedy, sitcom, mockumentary, satire, and a theoretical preprint.

When using those references:

1. Extract the **pragmatic structure** or research hypothesis.
2. Write a new synthetic example or use independently licensed material.
3. Record the new example's own provenance and licence.
4. Do not copy a joke merely to preserve the mechanism.
5. Preserve source status. A preprint remains a preprint; a secondary summary remains secondary.
6. Treat ASR transcripts as noisy research aids until human-verified.
7. Do not infer that fictional or satirical depictions represent Australians generally.

---

## How to Validate Examples

```bash
python -m australian_for_ais.cli validate data/starter/examples.jsonl
```

Each line of a `.jsonl` file must independently validate against `schemas/example.schema.json`.

Validation checks:
- JSON well-formedness
- Required fields are present
- Field types match the schema
- `confidence` is between 0.0 and 1.0
- `id` is a non-empty string
- `pragmatic_interpretations` contains at least one entry

---

## Literal vs Pragmatic Meaning

The schema strictly separates:

| Field | Represents |
|---|---|
| `literal_interpretation` | Denotative semantic reading, context-free |
| `pragmatic_interpretations` | List of plausible socially intended meanings |
| `primary_pragmatic_interpretation` | The annotator's best-estimate reading (not ground truth) |

Do not conflate these. An utterance like "Yeah, nah." has a clear literal form and a pragmatic
reading that requires discourse context.

---

## Preserving Ambiguity

If an example is genuinely ambiguous, `ambiguity` must be `true` and
`pragmatic_interpretations` must contain at least two entries.

You must not resolve ambiguity by:
- Removing entries from `pragmatic_interpretations`
- Hardcoding the single interpretation a model produced
- Changing `ambiguity` to `false` without documented justification

---

## Uncertainty

The `confidence` field is a float between 0.0 and 1.0 representing annotator certainty.

- A value of 1.0 means the annotator is certain.
- A value below 0.5 indicates substantial uncertainty.
- `"insufficient_context"` is a valid value for `primary_pragmatic_interpretation` when
  context is genuinely insufficient to determine pragmatic meaning.

---

## Prohibition Against Inventing Cultural Rules

You must not introduce statements such as:

> "Australians always mean X when they say Y."
> "In Australian culture, Z is always interpreted as W."

Such statements are false and harmful. Individual speakers vary. Context varies.

Document cultural tendencies only when they are:
1. Attributed to appropriate research literature, OR
2. Hedged explicitly as hypotheses under investigation.

A source appearing in the research reference corpus does not by itself establish a universal cultural tendency.
