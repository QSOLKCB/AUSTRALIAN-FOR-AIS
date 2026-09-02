# Benchmark Design

## Design Philosophy

The benchmark is designed to test pragmatic interpretation rather than lexical recall. A benchmark that can be solved by a fixed phrase lookup has failed its purpose.

The project therefore keeps observation, literal interpretation, pragmatic annotation, uncertainty, and model prediction as separate fields.

---

## Example Record Structure

Each benchmark example contains:

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

## Phase 2 Pilot Items

Phase 2 separates the material shown to annotators from the annotations they produce.

`schemas/pilot-item.schema.json` contains only the observation-side fields needed for annotation:

- `id`
- `locale`
- `utterance`
- `context`
- `speaker_relationship`
- `source_type`
- `provenance`
- `license`
- optional `tags`
- optional `context_swap_group`

A pilot item deliberately contains **no gold pragmatic interpretation, mechanism label, social valence, hostility label, confidence, or ambiguity label**. Those are outputs of the human pilot rather than hints supplied to the annotator.

Each `speaker_relationship` describes the relationship in that individual item. It must not contain a disjunction that merely summarizes both members of a context pair, because relationship itself may be part of the pragmatic evidence being tested.

`data/pilot/items.jsonl` currently contains 60 independently authored synthetic pilot items arranged as 30 same-utterance context contrasts. These are pilot prompts, not a validated benchmark release.

---

## Phase 2 Human Annotation Records

`schemas/annotation.schema.json` stores one independent human annotation per record. The Phase 2 browser generates a local pseudonymous `annotator_id` in the exact form `annotator-<12 lowercase hexadecimal characters>` and does not accept names, email addresses, account handles, or other direct identifiers as annotation IDs.

The annotation schema preserves the uncertainty contract while making retained human readings explicit:

- the primary pragmatic interpretation must be retained among the annotator's plausible readings unless it is exactly `insufficient_context`;
- retaining two or more pragmatic interpretations requires `ambiguity: true`;
- `ambiguity: true` requires at least two distinct normalized retained readings;
- `insufficient_context` requires at least two distinct retained readings, `ambiguity: true`, and confidence at or below `0.4`;
- `insufficient_context` is not an ordinary pragmatic reading;
- `unknown` is a fallback mechanism and is mutually exclusive with every specific mechanism label;
- hostility may be `true`, `false`, or `uncertain`;
- social valence may be `friendly`, `hostile`, `neutral`, `ambiguous`, or `unknown`.

The optional `australian_english_exposure` field is a coarse, non-identifying self-report (`low`, `medium`, `high`, `unspecified`). It is not a nationality or demographic label.

One annotator may submit only one annotation for a given pilot item within an annotation file. Duplicate `(example_id, annotator_id)` assignments fail validation rather than being allowed to inflate annotation coverage.

When a browser profile is shared by more than one human annotator, the interface requires an explicit switch to a newly generated local pseudonym. That switch changes the storage namespace and reloads annotator-specific state so one person's visible form contents cannot silently become another person's independent record.

---

## Context-Swap Test Design

A benchmark context-swap group contains the same utterance under two or more different contexts.

Before scoring, a benchmark group is valid only when:

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

Phase 2 pilot context contrasts are weaker experimental objects because they are intentionally unannotated. Their validation requires only that the group has at least two items, preserves the exact observed utterance, and changes context. Human annotation may later show that a proposed contrast is ambiguous or unsuitable. The pilot must not manufacture a directional target merely to preserve the design hypothesis.

During human annotation, stable pilot IDs, tags, and `context_swap_group` metadata are hidden. Pair presentation order is derived deterministically from the locally generated pseudonym, with independently shuffled first- and later-pass group orders and a pseudonym-specific choice of which member appears first. A shared fixed counterpart offset such as `+30` is therefore not part of the annotation protocol.

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

## Phase 1 Component Metrics

Phase 1 reports independent components only:

1. **prediction_coverage_rate**: fraction of benchmark examples with a matching prediction record
2. **literal_accuracy**: correct literal predictions / all examples
3. **pragmatic_match_rate**: accepted pragmatic predictions / all examples
4. **ambiguity_recognition_rate**: ambiguous examples correctly marked ambiguous / all ambiguous examples
5. **hostility_accuracy**: correct hostility predictions / examples with resolved boolean hostility annotations
6. **hostility_uncertain_examples**: count of examples excluded from hostility accuracy because the annotation is `uncertain`
7. **social_valence_accuracy**: correct social-valence predictions / examples with resolved social-valence annotations
8. **social_valence_unknown_examples**: count of examples excluded from social-valence accuracy because the annotation is `unknown`
9. **confidence_brier_score**: mean Brier score for confidence in submitted pragmatic predictions; lower is better
10. **context_swap_sensitivity_rate**: context-swap pairs that are both directionally correct and different / all valid context-swap pairs

An annotated hostility value of `uncertain` is not converted into categorical ground truth. Those examples are counted in `hostility_uncertain_examples` and excluded from the `hostility_accuracy` denominator.

An annotated social valence of `unknown` is likewise unresolved rather than categorical ground truth. Those examples are counted in `social_valence_unknown_examples` and excluded from the `social_valence_accuracy` denominator.

Confidence calibration is reported only over submitted, schema-valid predictions because an absent record contains no confidence value. Coverage is reported separately, and missing records already count as failures in the dataset-proportion metrics.

No component is combined into a single "Australian understanding" score.

---

## Phase 2 Agreement Reporting

Phase 2 agreement analysis is descriptive evidence about the annotation process, not a replacement gold label.

The deterministic report includes:

- annotation coverage per pilot item;
- within-item pairwise agreement rates for categorical fields;
- Cohen's kappa for each annotator pair on shared examples;
- exact-set agreement and Jaccard overlap for multi-label mechanism selections;
- descriptive pairwise confidence differences.

Free-text pragmatic interpretations are deliberately **not** scored by exact-string agreement. Exact wording is not semantic equivalence, and Phase 2 does not introduce an unvalidated model judge to conceal that limitation. Free-text readings remain available for qualitative comparison and later adjudication design.

At least two independent human annotations per pilot item are required for Phase 2 graduation, but the software does not pretend that this human work has happened merely because the tooling exists.

---

## Exact-Match Limitation

The Phase 1 pragmatic evaluator uses case-folded exact string matching with collapsed whitespace against accepted interpretations. This is deliberately transparent and deterministic, but it is not semantic equivalence.

The one explicit sentinel rule is `insufficient_context`: it is accepted only in exact canonical spelling and only when the example itself declares that sentinel as its primary pragmatic interpretation.

A later phase may introduce a separately validated semantic scoring protocol.

---

## Schema Versioning

The review-facing schemas carry two machine-readable version markers:

- a versioned `$id`, currently containing `/v0.1.0/`;
- `x-project-schema-version: "0.1.0"`.

The JSON Schema `$schema` URI identifies the JSON Schema dialect only. It is **not** the project schema version.

The Phase 2 pilot-item and annotation schemas extend the unreleased research substrate without changing the semantics of the Phase 1 example or evaluation schemas.

After a public schema contract is released, a backward-incompatible schema change must:

1. increment the relevant project schema version in root schemas and packaged copies;
2. update affected records and Python models;
3. update tests and documentation; and
4. document the change in `CHANGELOG.md`.

The root `schemas/` files are the review-facing contracts. Equivalent copies are packaged under `src/australian_for_ais/schemas/` so installed wheels can validate offline.
