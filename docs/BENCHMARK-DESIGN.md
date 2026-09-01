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
- **pragmatic_interpretations**: accepted plausible readings; ambiguous records require at least two distinct normalized readings
- **primary_pragmatic_interpretation**: annotator's best estimate, not objective ground truth
- **humour_mechanisms**: active taxonomy tags
- **social_valence**: friendly / hostile / neutral / ambiguous / unknown
- **hostility**: true / false / uncertain
- **confidence**: annotator certainty from 0.0 to 1.0
- **ambiguity**: whether substantially different readings remain plausible
- **cultural_dependency**: low / medium / high / unknown
- **context_required**: whether the supplied context materially affects interpretation
- **alternative_interpretations**: additional considered readings
- **annotation_notes**: reasoning and caveats
- **source_type**: synthetic / naturalistic / constructed
- **provenance**: origin and rights/consent information
- **license**: licence for the example
- **tags**: searchable non-normative tags
- **context_swap_group**: optional link between same-utterance context variants

Required textual fields and scorable interpretation strings must contain at least one non-whitespace character. A benchmark dataset must contain at least one valid example record; blank or empty datasets fail validation.

### Important Distinctions

| Field | Epistemic Status |
|---|---|
| `utterance` | Observation |
| `literal_interpretation` | Context-free inference |
| `pragmatic_interpretations` | Annotator inference |
| `primary_pragmatic_interpretation` | Annotator preference, not ground truth |
| `hostility` | Annotator inference, may be uncertain |
| `confidence` | Annotator self-report |

The primary pragmatic interpretation must be one of the accepted pragmatic interpretations unless it is exactly `insufficient_context`. An `insufficient_context` record must still preserve at least two distinct plausible readings, set `ambiguity: true`, and keep annotator confidence at or below 0.4.

`insufficient_context` is a reserved control value, not an ordinary accepted reading. It must not appear in `pragmatic_interpretations`. The evaluator injects it as an accepted answer only when the example's exact primary field is `insufficient_context`, and prediction files must use that exact canonical spelling.

A reading described as genuinely plausible in the fixture should be represented in `pragmatic_interpretations` if the evaluator is expected to accept it. `alternative_interpretations` must not become a hidden list of answers that the scorer treats as wrong.

---

## Context-Swap Test Design

A context-swap group contains the same utterance under two or more different contexts.

Before scoring, a group is valid only when:

1. it contains at least two records;
2. every member has the same observed utterance;
3. every member supplies a distinct context;
4. every member has a distinct primary pragmatic direction; and
5. accepted pragmatic direction sets are disjoint between members.

The disjointness rule is necessary because overlapping accepted sets can allow swapped answers to receive credit even when the model selects the wrong context-specific direction. Context-swap items are therefore stricter than ordinary ambiguous items.

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

Required textual prediction fields must contain non-whitespace content.

When an example explicitly declares `primary_pragmatic_interpretation: "insufficient_context"`, the model may submit `predicted_pragmatic: "insufficient_context"`. That sentinel is treated as an accepted pragmatic answer for that example rather than forcing a choice between unresolved readings.

A prediction file may contain fewer records than the dataset, but missing records are counted as incorrect for dataset-proportion metrics and are reported as evaluation errors. Unknown IDs are also errors. Both the module CLI and `scripts/evaluate_predictions.py` return a non-zero exit code when evaluation errors are present.

The public `score()` API also validates dictionary integrity before computing metrics. Mapping keys must match the `id` or `example_id` stored inside their records, and an empty benchmark mapping is rejected.

All advertised JSONL inputs must be regular files. Directory paths and unreadable inputs are converted into validation failures rather than uncaught filesystem tracebacks.

---

## Component Metrics

Phase 1 reports independent components only:

1. **prediction_coverage_rate**: fraction of benchmark examples with a matching prediction record
2. **literal_accuracy**: correct literal predictions / all examples
3. **pragmatic_match_rate**: accepted pragmatic predictions / all examples
4. **ambiguity_recognition_rate**: ambiguous examples correctly marked ambiguous / all ambiguous examples
5. **hostility_accuracy**: correct hostility predictions / examples with resolved boolean hostility annotations
6. **hostility_uncertain_examples**: count of examples excluded from hostility accuracy because the annotation is `uncertain`
7. **social_valence_accuracy**: correct social-valence predictions / all examples
8. **confidence_brier_score**: mean Brier score for confidence in submitted pragmatic predictions; lower is better
9. **context_swap_sensitivity_rate**: context-swap pairs that are both directionally correct and different / all valid context-swap pairs

An annotated hostility value of `uncertain` is not converted into categorical ground truth. Those examples are counted separately and excluded from the hostility-accuracy denominator.

Confidence calibration is reported only over submitted, schema-valid predictions because an absent record contains no confidence value. Coverage is reported separately, and missing records already count as failures in the dataset-proportion metrics.

No component is combined into a single "Australian understanding" score.

---

## Exact-Match Limitation

The Phase 1 pragmatic evaluator uses case-folded exact string matching with collapsed whitespace against accepted interpretations. This is deliberately transparent and deterministic, but it is not semantic equivalence.

The one explicit sentinel rule is `insufficient_context`: it is accepted only in exact canonical spelling and only when the example itself declares that sentinel as its primary pragmatic interpretation.

A later phase may introduce a separately validated semantic scoring protocol.

---

## Schema Versioning

Both schemas carry two machine-readable version markers:

- a versioned `$id`, currently containing `/v0.1.0/`;
- `x-project-schema-version: "0.1.0"`.

The JSON Schema `$schema` URI identifies the JSON Schema dialect only. It is **not** the project schema version.

The `0.1.0` schema remains the draft Phase 1 contract until this bootstrap PR is merged. Tightening that unreleased draft during review does not create a released compatibility promise.

After the initial contract is released, a backward-incompatible schema change must:

1. increment the project schema version in both root schemas and packaged copies;
2. update affected records and Python models;
3. update tests and documentation; and
4. document the change in `CHANGELOG.md`.

The root `schemas/` files are the review-facing contracts. Equivalent copies are packaged under `src/australian_for_ais/schemas/` so installed wheels can validate offline.
