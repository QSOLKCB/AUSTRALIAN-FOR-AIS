# Benchmark Design

## Design Philosophy

The benchmark is designed to test pragmatic interpretation rather than lexical recall. A benchmark that can be solved by a fixed phrase lookup has failed its purpose.

The project therefore keeps observation, literal interpretation, pragmatic annotation, uncertainty, and model prediction as separate fields.

---

## Example Record Structure

Each example contains:

- **id**: stable unique identifier
- **locale**: language variety, e.g. `en-AU`
- **utterance**: observed linguistic form
- **context**: supplied situational context
- **speaker_relationship**: relationship between speaker and addressee
- **literal_interpretation**: context-free denotative reading
- **pragmatic_interpretations**: one or more accepted plausible readings
- **primary_pragmatic_interpretation**: annotator's best estimate, not objective ground truth
- **humour_mechanisms**: active taxonomy tags
- **social_valence**: friendly / hostile / neutral / ambiguous / unknown
- **hostility**: true / false / uncertain
- **confidence**: annotator certainty from 0.0 to 1.0
- **ambiguity**: whether substantially different readings remain plausible
- **cultural_dependency**: low / medium / high / unknown
- **context_required**: whether the supplied context materially affects interpretation
- **alternative_interpretations**: additional plausible readings
- **annotation_notes**: reasoning and caveats
- **source_type**: synthetic / naturalistic / constructed
- **provenance**: origin and rights/consent information
- **license**: licence for the example
- **tags**: searchable non-normative tags
- **context_swap_group**: optional link between same-utterance context variants

### Important Distinctions

| Field | Epistemic Status |
|---|---|
| `utterance` | Observation |
| `literal_interpretation` | Context-free inference |
| `pragmatic_interpretations` | Annotator inference |
| `primary_pragmatic_interpretation` | Annotator preference, not ground truth |
| `hostility` | Annotator inference, may be uncertain |
| `confidence` | Annotator self-report |

The primary pragmatic interpretation must be one of the accepted pragmatic interpretations unless it is exactly `insufficient_context`. This keeps the declared best estimate and the evaluator's accepted answers aligned.

---

## Context-Swap Test Design

A context-swap group contains the same utterance under two or more different contexts.

A pair passes only when:

1. both prediction records are present;
2. each prediction matches an accepted pragmatic interpretation for its own context; and
3. the two pragmatic predictions differ.

Merely producing two different strings is not sufficient. Swapped answers or two different wrong answers are failures.

---

## Evaluation Records

Every Phase 1 evaluation record must include all advertised dimensions:

- `example_id`
- `predicted_literal`
- `predicted_pragmatic`
- `predicted_hostility`
- `predicted_social_valence`
- `predicted_ambiguity`
- `model_confidence`

A prediction file may contain fewer records than the dataset, but missing records are counted as incorrect for dataset-proportion metrics and are reported as evaluation errors. Unknown IDs are also errors. The CLI returns a non-zero exit code when such errors are present.

---

## Component Metrics

Phase 1 reports independent components only:

1. **prediction_coverage_rate**: fraction of benchmark examples with a matching prediction record
2. **literal_accuracy**: correct literal predictions / all examples
3. **pragmatic_match_rate**: accepted pragmatic predictions / all examples
4. **ambiguity_recognition_rate**: ambiguous examples correctly marked ambiguous / all ambiguous examples
5. **hostility_accuracy**: correct hostility predictions / all examples
6. **social_valence_accuracy**: correct social-valence predictions / all examples
7. **confidence_brier_score**: mean Brier score for confidence in the submitted pragmatic predictions; lower is better
8. **context_swap_sensitivity_rate**: context-swap pairs that are both directionally correct and different / all context-swap pairs

Confidence calibration is reported only over submitted, schema-valid predictions because an absent record contains no confidence value. Coverage is reported separately, and missing records already count as failures in the dataset-proportion metrics.

No component is combined into a single "Australian understanding" score.

---

## Exact-Match Limitation

The Phase 1 pragmatic evaluator uses case-folded exact string matching against the accepted interpretations. This is deliberately transparent and deterministic, but it is not semantic equivalence. A later phase may introduce a separately validated semantic scoring protocol.

---

## Schema Versioning

Both schemas carry two machine-readable version markers:

- a versioned `$id`, currently containing `/v0.1.0/`;
- `x-project-schema-version: "0.1.0"`.

The JSON Schema `$schema` URI identifies the JSON Schema dialect only. It is **not** the project schema version.

For a backward-incompatible schema change:

1. increment the project schema version in both root schemas and packaged copies;
2. update affected records and Python models;
3. update tests and documentation;
4. document the change in `CHANGELOG.md`.

The root `schemas/` files are the review-facing contracts. Equivalent copies are packaged under `src/australian_for_ais/schemas/` so installed wheels can validate offline.
