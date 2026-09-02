# README4AI — Machine-Oriented Repository Description

This file is addressed to AI agents, language models, and automated tools working within this repository. Read it before modifying any file.

---

## Epistemic Boundaries

You are operating within a research project. Epistemic precision is required.

- **Observation** and **inference** are distinct. Do not collapse them.
- **Annotator interpretation** is not the same as **objective ground truth**.
- **Human pilot tooling** is not the same as **completed human annotation**.
- **Inter-annotator agreement** is not the same as **objective cultural truth**.
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
| `pragmatic_interpretation` | The socially intended meaning given supplied context and relationship |
| `context` | Situational information supplied with an utterance |
| `speaker_relationship` | The social relationship between speaker and addressee |
| `social_valence` | The social register of an utterance: friendly / hostile / neutral / ambiguous / unknown |
| `hostility` | Whether aggressive social intent is present: `true`, `false`, or `uncertain` |
| `confidence` | Annotator's subjective certainty about a pragmatic interpretation, 0.0–1.0 |
| `ambiguity` | Whether multiple substantially different interpretations are plausible |
| `humour_mechanisms` | Active taxonomy labels for the pragmatic device being annotated |
| `context_swap_group` | ID linking same-utterance items under different contexts |
| `pilot_item` | Unannotated observation-side Phase 2 prompt shown to human annotators |
| `human_annotation` | One independent pseudonymous annotator's interpretation of a pilot item |
| `research_reference` | External work used to identify mechanisms or hypotheses; not benchmark data by default |

---

## File Layout

```text
schemas/example.schema.json          — Phase 1 benchmark example schema
schemas/evaluation.schema.json       — Phase 1 prediction schema
schemas/pilot-item.schema.json       — Phase 2 unannotated pilot-item schema
schemas/annotation.schema.json       — Phase 2 independent human-annotation schema

data/starter/examples.jsonl          — Phase 1 synthetic fixtures
data/pilot/items.jsonl               — 60 unannotated Phase 2 synthetic pilot items
annotation/index.html                — Offline Phase 2 annotation interface

src/australian_for_ais/models.py     — Python data models
src/australian_for_ais/validation.py — Validation logic
src/australian_for_ais/scoring.py    — Deterministic Phase 1 evaluator
src/australian_for_ais/annotation.py — Phase 2 coverage/agreement analysis
src/australian_for_ais/cli.py        — Offline CLI

docs/INVARIANTS.md                   — Core invariants
docs/PHASE2-PILOT-PROTOCOL.md        — Human pilot procedure and ethics boundary
docs/PHASE2-MECHANISM-REVIEW.md      — Phase 2 taxonomy review
docs/RESEARCH-REFERENCE-CORPUS.md    — External references and source-use boundaries
```

---

## Schemas

Four review-facing schemas are normative for their respective record types:

1. `example.schema.json` — released benchmark-style example records.
2. `evaluation.schema.json` — model prediction records.
3. `pilot-item.schema.json` — unannotated Phase 2 prompts.
4. `annotation.schema.json` — one independent Phase 2 human annotation.

Equivalent copies are packaged under `src/australian_for_ais/schemas/` for offline installed-wheel validation.

If you modify a schema, you must:
- update the packaged copy;
- update affected Python models and validation logic;
- update affected data where required;
- update `docs/BENCHMARK-DESIGN.md`;
- update tests and `CHANGELOG.md`;
- run the relevant CLI validation command and full test suite.

Candidate mechanism labels listed in `docs/RESEARCH-REFERENCE-CORPUS.md` are **not active schema values**. Do not insert them into data unless the schema contract is deliberately revised.

---

## Phase 2 Human Annotation Boundary

The Phase 2 branch contains a pilot-ready research workflow, not human research results.

`data/pilot/items.jsonl` contains 60 independently authored synthetic prompts with observation-side context only. It contains no gold pragmatic labels.

AI agents must **not**:

- invent human annotators;
- fabricate annotation JSONL to satisfy roadmap graduation criteria;
- invent consent or ethical-review status;
- treat a fake multi-agent simulation as inter-annotator agreement;
- overwrite real annotator disagreement with an AI-generated consensus;
- infer nationality, ethnicity, identity, or other sensitive characteristics from annotation language.

The optional `australian_english_exposure` field is a coarse non-identifying self-report only.

Real human annotations are stored as independent records. Duplicate `(example_id, annotator_id)` assignments are rejected.

Free-text pragmatic interpretations are not assigned exact-string IAA scores. Phase 2 has no validated semantic-equivalence judge.

---

## Invariants

The invariants in `docs/INVARIANTS.md` are non-negotiable research contracts.

Critical examples:

- **AU-HUMOUR-001**: Lexical profanity ≠ social aggression.
- **AU-HUMOUR-002**: Surface sentiment ≠ pragmatic sentiment.
- **AU-HUMOUR-003**: "mate" must not be assigned a fixed social valence.
- **AU-HUMOUR-006**: Ambiguity must not be silently collapsed into certainty.
- **AU-HUMOUR-007**: A cultural heuristic must not be treated as a universal rule.
- **AU-HUMOUR-009**: Annotator interpretation ≠ objective ground truth.

You must not introduce logic or data that violates these invariants.

---

## What Agents May Modify

- `src/` — source code with tests and preserved invariants
- `tests/` — tests, without deleting existing coverage to make changes pass
- `docs/` — documentation with explicit epistemic status
- `data/starter/examples.jsonl` — benchmark fixtures, preserving stable IDs
- `data/pilot/items.jsonl` — clearly synthetic pilot prompts, preserving stable IDs and no hidden gold labels
- `annotation/` — offline annotation tooling
- `scripts/` — deterministic offline utilities

---

## What Agents Must Not Do

- Fabricate citations, authors, DOIs, ORCID identifiers, dates, release metadata, institutions, participants, annotations, consent, or research outcomes.
- Convert uncertain or ambiguous annotations into categorical ground truth.
- Assign a fixed social meaning to "mate", profanity, `yeah nah`, or other context-dependent language.
- Invent cultural rules and present them as established facts.
- Claim a model "understands" culture based on benchmark score alone.
- Infer speaker or annotator identity, nationality, ethnicity, or other personal characteristics from language.
- Change a committed example or pilot ID without explicit migration justification.
- Mark future roadmap phases complete without satisfying their graduation criteria.
- Introduce network dependencies into tests or annotation analysis.
- Copy television scripts, subtitles, episode transcripts, or bulk dialogue into benchmark/pilot data without an independently established licence and documented justification.
- Treat a web-accessible source as automatically redistributable.
- Commit generated caches, bytecode, packaging metadata, virtual environments, or editor artefacts.

---

## Research Reference Handling

`docs/RESEARCH-REFERENCE-CORPUS.md` contains works used for mechanism discovery and research design.

When using those references:

1. Extract the **pragmatic structure** or research hypothesis.
2. Write a new synthetic example or use independently licensed material.
3. Record the new item's own provenance and licence.
4. Do not copy a joke merely to preserve the mechanism.
5. Preserve source status. A preprint remains a preprint; a secondary summary remains secondary.
6. Treat ASR transcripts as noisy research aids until human-verified.
7. Do not infer that fictional or satirical depictions represent Australians generally.

The Phase 2 mechanism review treats tall-poppy/status deflation as a hypothesis to test, not a rule that Australians dislike success.

---

## Validation Commands

Phase 1 starter examples:

```bash
python -m australian_for_ais.cli validate data/starter/examples.jsonl
```

Phase 2 pilot pack:

```bash
python -m australian_for_ais.cli validate-pilot data/pilot/items.jsonl
```

Collected human annotations:

```bash
python -m australian_for_ais.cli validate-annotations \
  data/pilot/items.jsonl annotations.jsonl
```

Agreement report:

```bash
python -m australian_for_ais.cli agreement \
  data/pilot/items.jsonl annotations.jsonl
```

Graduation coverage check:

```bash
python -m australian_for_ais.cli validate-annotations \
  data/pilot/items.jsonl annotations.jsonl --require-two
```

---

## Preserving Ambiguity

If an annotation is genuinely ambiguous, `ambiguity` must be `true` and `pragmatic_interpretations` must contain at least two distinct readings.

`insufficient_context` is a reserved primary control value. It requires at least two retained readings, `ambiguity: true`, and confidence at or below `0.4`.

Do not resolve ambiguity by deleting alternatives, hardcoding one model output, or changing the label merely to improve agreement.

---

## Prohibition Against Inventing Cultural Rules

Do not introduce statements such as:

> "Australians always mean X when they say Y."
> "In Australian culture, Z is always interpreted as W."

Individual speakers vary and context varies. Cultural tendencies must be attributed to appropriate evidence or explicitly hedged as hypotheses under investigation.
