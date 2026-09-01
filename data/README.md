# Dataset

## Phase 1 — Synthetic Starter Fixtures

The `starter/examples.jsonl` file contains synthetic examples created as project fixtures.
They are **not** a representative sample of Australian English.

Purpose:
- Demonstrate the schema
- Exercise the validation and evaluation pipeline
- Provide context-swap examples showing how identical utterances can have different meanings

**These examples are illustrative, not scientifically validated.**

Do not draw conclusions about AI capability or Australian language patterns from this data.

## File Format

Each file in `data/` is JSONL — one JSON object per line, each validating against
`schemas/example.schema.json`.

## Provenance

All Phase 1 examples are synthetic. See `docs/DATA-GOVERNANCE.md` for provenance policy.

## Validation

```bash
python -m australian_for_ais.cli validate data/starter/examples.jsonl
```
