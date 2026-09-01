# AGENTS.md — Machine-Oriented Repository Instructions

This file contains instructions for AI agents and automated tools operating in this repository.

---

## Required Checks Before Completing Any Change

1. **Run the test suite.**
   ```bash
   pytest
   ```
   All tests must pass. Do not submit a change that breaks existing tests.

2. **Validate JSONL data.**
   ```bash
   python -m australian_for_ais.cli validate data/starter/examples.jsonl
   ```
   Every record must pass schema validation.

3. **If you modified schemas**, run tests again and update documentation.

---

## Code Quality

- Preserve deterministic evaluation behaviour. Do not introduce randomness into scoring.
- Do not change benchmark example semantics merely to make tests pass.
- Do not remove or disable existing tests. If a test is wrong, fix it with evidence.
- Follow existing code style. No new linters or formatters without prior discussion.

---

## Data Integrity

- **Never fabricate citations.** If a source is unknown, say so explicitly.
- **Never convert uncertain annotations into categorical ground truth.** The `confidence`
  field and `ambiguity` flag must reflect genuine annotator uncertainty.
- **Preserve existing example IDs.** Once an ID is committed, it is stable. Do not change it.
- **Do not assume a fixed meaning for context-dependent language** such as "mate", profanity,
  or discourse markers.
- **Distinguish data from commentary.** Data fields must contain observed or inferred
  information. Commentary belongs in `annotation_notes` or documentation files.

---

## Stereotypes and Identity

- Do not introduce language that stereotypes any group, dialect, or culture.
- Do not infer speaker identity, nationality, ethnicity, or any personal characteristic from
  language use.
- This project evaluates language understanding, not personal identity.

---

## Schema Changes

If you change `schemas/example.schema.json` or `schemas/evaluation.schema.json`:

1. Update `src/australian_for_ais/models.py` to match.
2. Update `data/starter/examples.jsonl` if required by the schema change.
3. Update `docs/BENCHMARK-DESIGN.md` to document the rationale.
4. Run `pytest` to verify consistency.

---

## Documentation Changes

When you change methodology, add research questions, or revise the scoring approach:

1. Update `docs/METHODOLOGY.md`.
2. Update `CHANGELOG.md` with a brief summary.
3. Do not overstate scientific validity in documentation.

---

## Prohibited Actions

- Do not fabricate author names, ORCID values, DOIs, or institutional affiliations.
- Do not claim benchmark performance equals cultural competence.
- Do not claim model explanations constitute evidence of internal reasoning.
- Do not mark future ROADMAP phases as complete.
- Do not introduce network access into the test suite. Tests must run offline.
- Do not merge to the main branch without a pull request and review.

---

## Invariants

Before modifying any evaluation logic or data, read `docs/INVARIANTS.md`.

The invariants AU-HUMOUR-001 through AU-HUMOUR-010 are non-negotiable. They exist to prevent
specific, documented categories of research error. Any code or data change that would violate
an invariant must be explicitly flagged and discussed before proceeding.
