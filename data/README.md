# Data

## Phase 1 — Synthetic Starter Fixtures

`starter/examples.jsonl` contains synthetic examples created as project fixtures. They are **not** a representative sample of Australian English.

Purpose:
- Demonstrate the benchmark example schema
- Exercise the validation and evaluation pipeline
- Provide controlled context-swap examples showing how identical utterances can have different meanings

These examples are illustrative, not scientifically validated. Do not draw conclusions about AI capability or Australian language patterns from them.

Validate with:

```bash
python -m australian_for_ais.cli validate data/starter/examples.jsonl
```

## Phase 2 — Unannotated Pilot Prompts

`pilot/items.jsonl` contains 60 independently authored synthetic prompts prepared for pilot human annotation. They are observation-side research prompts, **not gold benchmark examples**.

The pilot items validate against `schemas/pilot-item.schema.json`, not the Phase 1 example schema. They deliberately omit pragmatic answers, mechanism labels, valence, hostility, ambiguity, and confidence so those fields can be supplied independently by real annotators.

Validate with:

```bash
python -m australian_for_ais.cli validate-pilot data/pilot/items.jsonl
```

See `pilot/README.md` and `docs/PHASE2-PILOT-PROTOCOL.md` before collecting annotations.

## Human Annotation Files

Human annotation exports validate against `schemas/annotation.schema.json`. They are not automatically suitable for committing or redistribution merely because they pass schema validation. Consent, privacy, storage, and release status must be reviewed first.

Validate a collected file against the known pilot IDs with:

```bash
python -m australian_for_ais.cli validate-annotations \
  data/pilot/items.jsonl annotations.jsonl
```

## File Format

All record collections use JSONL: one JSON object per non-empty line. The applicable schema depends on the record type. Do not assume every file under `data/` is a benchmark-example file.

## Provenance

The committed Phase 1 starter examples and Phase 2 pilot prompts are synthetic. See `docs/DATA-GOVERNANCE.md` for provenance, consent, and redistribution policy.
