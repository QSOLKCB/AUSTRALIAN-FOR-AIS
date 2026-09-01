# Benchmark Design

## Design Philosophy

The benchmark is designed to test pragmatic understanding, not lexical recall.

A benchmark that can be solved by lexical pattern-matching has failed its purpose. The design
choices described here are intended to make surface-level heuristics insufficient.

---

## Example Record Structure

Each example consists of:

- **id**: Stable unique identifier. Must not change after initial assignment.
- **locale**: Language variety (e.g., "en-AU").
- **utterance**: The linguistic form of what was said.
- **context**: Situational context required to interpret the utterance.
- **speaker_relationship**: The social relationship between speaker and addressee.
- **literal_interpretation**: The context-free denotative reading.
- **pragmatic_interpretations**: List of plausible socially intended readings (≥1 entry).
- **primary_pragmatic_interpretation**: The annotator's best-estimate reading.
- **humour_mechanisms**: Taxonomy tags for pragmatic devices in use.
- **social_valence**: The social register (friendly / hostile / neutral / ambiguous / unknown).
- **hostility**: Whether aggressive social intent is present (true / false / uncertain).
- **confidence**: Annotator certainty (0.0–1.0).
- **ambiguity**: Whether multiple substantially different interpretations are plausible.
- **cultural_dependency**: Whether interpretation requires specific cultural knowledge.
- **context_required**: Whether interpretation is substantially context-dependent.
- **alternative_interpretations**: Other plausible readings.
- **annotation_notes**: Free-text documentation of annotation reasoning.
- **source_type**: Origin category (synthetic / naturalistic / constructed).
- **provenance**: Description of origin, licensing, and consent status.
- **license**: Licence for this example.
- **tags**: Arbitrary searchable tags.
- **context_swap_group**: Optional — links examples that share an utterance but differ in context.

### Important Distinctions

| Field | Epistemic Status |
|---|---|
| `utterance` | Observation (what was said) |
| `literal_interpretation` | Inference (context-free) |
| `pragmatic_interpretations` | Annotator inference (context-dependent) |
| `primary_pragmatic_interpretation` | Annotator preference, not ground truth |
| `hostility` | Annotator inference, may be uncertain |
| `confidence` | Annotator self-report |

These distinctions must be preserved in all tooling.

---

## Context-Swap Test Design

A context-swap pair consists of:
- The same `utterance`
- Two or more different `context` values
- Different `primary_pragmatic_interpretation` values for each

Both records share a `context_swap_group` identifier.

**Evaluation rule:** A model passes a context-swap test if and only if its output differs
between the two context conditions in the expected direction. Producing the same output
for both contexts is a context-swap failure, regardless of whether either output is correct.

---

## Evaluation Records

Evaluation records (prediction files) must include:

- `example_id`: Must match an existing example `id`
- `predicted_literal`: Model's literal interpretation
- `predicted_pragmatic`: Model's pragmatic interpretation
- `predicted_hostility`: Model's hostility classification
- `predicted_social_valence`: Model's social valence classification
- `predicted_ambiguity`: Model's ambiguity judgement
- `model_confidence`: Model's reported confidence (0.0–1.0)

---

## Component Metrics

Phase 1 implements these metrics deterministically:

1. **literal_accuracy**: Proportion of examples where `predicted_literal` matches `literal_interpretation`
2. **pragmatic_match**: Proportion of examples where `predicted_pragmatic` matches any entry in `pragmatic_interpretations`
3. **ambiguity_recognition**: Proportion of ambiguous examples correctly identified as ambiguous
4. **hostility_accuracy**: Proportion of examples where `predicted_hostility` matches `hostility`
5. **social_valence_accuracy**: Proportion of examples where `predicted_social_valence` matches `social_valence`
6. **context_swap_sensitivity**: Proportion of context-swap pairs where model output differs between conditions

**These metrics are not aggregated into a single score.**

Aggregation would hide the differential performance across pragmatic mechanisms and create
false precision. Researchers should inspect component metrics separately.

---

## Schema Versioning

The schema version is recorded in `schemas/example.schema.json` via the `$schema` URI and
the `$id` field.

If the schema changes in a backward-incompatible way:
1. Increment the schema version in both schema files.
2. Update all existing records if required.
3. Document the change in CHANGELOG.md.
4. Update models.py to match.
