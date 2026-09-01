"""
Deterministic reference evaluator for Australian For AIs.

Key constraints:
- No machine learning dependencies.
- No randomness.
- Metrics are reported as components, never aggregated into one score.
- Missing predictions count as failures for dataset-proportion metrics.
- Confidence calibration is reported separately from correctness.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

from .models import BenchmarkExample, EvaluationRecord
from .validation import (
    ValidationError,
    iter_jsonl,
    validate_context_swap_groups,
    validate_evaluation_record,
    validate_example_record,
)


@dataclass
class ComponentScores:
    """Independent component metrics for one deterministic evaluation run."""

    n_examples: int = 0
    n_predictions: int = 0
    n_matched_predictions: int = 0

    literal_correct: int = 0
    literal_total: int = 0

    pragmatic_match: int = 0
    pragmatic_total: int = 0

    ambiguity_recognised: int = 0
    ambiguity_total: int = 0

    hostility_correct: int = 0
    hostility_total: int = 0
    hostility_uncertain_examples: int = 0

    social_valence_correct: int = 0
    social_valence_total: int = 0

    context_swap_pairs_found: int = 0
    context_swap_sensitive: int = 0

    confidence_brier_sum: float = 0.0
    confidence_total: int = 0

    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        def safe_rate(num: int, denom: int) -> float | None:
            return round(num / denom, 4) if denom > 0 else None

        return {
            "n_examples": self.n_examples,
            "n_predictions": self.n_predictions,
            "n_matched_predictions": self.n_matched_predictions,
            "prediction_coverage_rate": safe_rate(
                self.n_matched_predictions, self.n_examples
            ),
            "literal_accuracy": safe_rate(self.literal_correct, self.literal_total),
            "pragmatic_match_rate": safe_rate(
                self.pragmatic_match, self.pragmatic_total
            ),
            "ambiguity_recognition_rate": safe_rate(
                self.ambiguity_recognised, self.ambiguity_total
            ),
            "hostility_accuracy": safe_rate(
                self.hostility_correct, self.hostility_total
            ),
            "hostility_uncertain_examples": self.hostility_uncertain_examples,
            "social_valence_accuracy": safe_rate(
                self.social_valence_correct, self.social_valence_total
            ),
            "confidence_brier_score": (
                round(self.confidence_brier_sum / self.confidence_total, 4)
                if self.confidence_total > 0
                else None
            ),
            "confidence_total": self.confidence_total,
            "context_swap_pairs_found": self.context_swap_pairs_found,
            "context_swap_sensitivity_rate": safe_rate(
                self.context_swap_sensitive, self.context_swap_pairs_found
            ),
            "errors": self.errors,
        }


def _normalise(s: str) -> str:
    """Normalise a string for case-insensitive exact comparison."""
    return s.strip().casefold()


def _pragmatic_matches(predicted: str, annotated_interpretations: list[str]) -> bool:
    """Return True when a prediction exactly matches one accepted interpretation."""
    pred_norm = _normalise(predicted)
    return any(_normalise(a) == pred_norm for a in annotated_interpretations)


def _accepted_pragmatic_interpretations(ex: BenchmarkExample) -> list[str]:
    """
    Return the accepted pragmatic answers for one example.

    ``insufficient_context`` is an explicit accepted answer only when it is the
    example's declared primary interpretation. This preserves uncertainty rather
    than rewarding a forced choice between unresolved readings.
    """
    accepted = list(ex.pragmatic_interpretations)
    if _normalise(ex.primary_pragmatic_interpretation) == "insufficient_context":
        accepted.append("insufficient_context")
    return accepted


def _hostility_matches(predicted: bool | str, annotated: bool) -> bool:
    return predicted == annotated


def _social_valence_matches(predicted: str, annotated: str) -> bool:
    return _normalise(predicted) == _normalise(annotated)


def _find_context_swap_pairs(
    examples: dict[str, BenchmarkExample],
) -> list[tuple[BenchmarkExample, BenchmarkExample]]:
    """Validate and return all unordered pairs sharing a context-swap group."""
    validate_context_swap_groups([ex.to_dict() for ex in examples.values()])

    groups: dict[str, list[str]] = {}
    for ex_id, ex in examples.items():
        if ex.context_swap_group:
            groups.setdefault(ex.context_swap_group, []).append(ex_id)

    pairs: list[tuple[BenchmarkExample, BenchmarkExample]] = []
    for group_ids in groups.values():
        for i in range(len(group_ids)):
            for j in range(i + 1, len(group_ids)):
                pairs.append((examples[group_ids[i]], examples[group_ids[j]]))
    return pairs


def _context_swap_sensitive(
    ex_a: BenchmarkExample,
    ex_b: BenchmarkExample,
    pred_a: EvaluationRecord,
    pred_b: EvaluationRecord,
) -> bool:
    """
    Return True only when both context-specific answers are accepted and differ.

    Merely producing two different strings is not sufficient: swapped or otherwise
    incorrect answers do not demonstrate successful context use.
    """
    outputs_differ = _normalise(pred_a.predicted_pragmatic) != _normalise(
        pred_b.predicted_pragmatic
    )
    return (
        outputs_differ
        and _pragmatic_matches(
            pred_a.predicted_pragmatic, _accepted_pragmatic_interpretations(ex_a)
        )
        and _pragmatic_matches(
            pred_b.predicted_pragmatic, _accepted_pragmatic_interpretations(ex_b)
        )
    )


def load_examples(path: pathlib.Path) -> dict[str, BenchmarkExample]:
    """Load and validate benchmark examples, rejecting dataset-level violations."""
    examples: dict[str, BenchmarkExample] = {}
    raw_records = []

    for lineno, record in iter_jsonl(path):
        validate_example_record(record)
        raw_records.append(record)
        ex = BenchmarkExample.from_dict(record)
        if ex.id in examples:
            raise ValidationError(f"Line {lineno}: duplicate example id '{ex.id}'.")
        examples[ex.id] = ex

    validate_context_swap_groups(raw_records)
    return examples


def load_predictions(path: pathlib.Path) -> dict[str, EvaluationRecord]:
    """Load and validate complete prediction records, rejecting duplicates."""
    predictions: dict[str, EvaluationRecord] = {}
    for lineno, record in iter_jsonl(path):
        validate_evaluation_record(record)
        pred = EvaluationRecord.from_dict(record)
        if pred.example_id in predictions:
            raise ValidationError(
                f"Line {lineno}: duplicate prediction for example_id '{pred.example_id}'."
            )
        predictions[pred.example_id] = pred
    return predictions


def score(
    examples: dict[str, BenchmarkExample],
    predictions: dict[str, EvaluationRecord],
) -> ComponentScores:
    """Score predictions deterministically against the complete example set."""
    result = ComponentScores(
        n_examples=len(examples),
        n_predictions=len(predictions),
    )

    for prediction_id in predictions:
        if prediction_id not in examples:
            result.errors.append(
                f"Prediction for unknown example_id '{prediction_id}' — ignored."
            )

    for ex_id, ex in examples.items():
        result.literal_total += 1
        result.pragmatic_total += 1
        result.social_valence_total += 1
        if ex.ambiguity:
            result.ambiguity_total += 1

        if ex.hostility == "uncertain":
            result.hostility_uncertain_examples += 1
        else:
            result.hostility_total += 1

        pred = predictions.get(ex_id)
        if pred is None:
            result.errors.append(
                f"Missing prediction for example_id '{ex_id}' — counted as incorrect."
            )
            continue

        result.n_matched_predictions += 1

        if _normalise(pred.predicted_literal) == _normalise(ex.literal_interpretation):
            result.literal_correct += 1

        pragmatic_correct = _pragmatic_matches(
            pred.predicted_pragmatic, _accepted_pragmatic_interpretations(ex)
        )
        if pragmatic_correct:
            result.pragmatic_match += 1

        if ex.hostility != "uncertain" and _hostility_matches(
            pred.predicted_hostility, ex.hostility
        ):
            result.hostility_correct += 1

        if _social_valence_matches(pred.predicted_social_valence, ex.social_valence):
            result.social_valence_correct += 1

        if ex.ambiguity and pred.predicted_ambiguity is True:
            result.ambiguity_recognised += 1

        target = 1.0 if pragmatic_correct else 0.0
        result.confidence_brier_sum += (pred.model_confidence - target) ** 2
        result.confidence_total += 1

    pairs = _find_context_swap_pairs(examples)
    result.context_swap_pairs_found = len(pairs)
    for ex_a, ex_b in pairs:
        pred_a = predictions.get(ex_a.id)
        pred_b = predictions.get(ex_b.id)
        if pred_a is None or pred_b is None:
            continue
        if _context_swap_sensitive(ex_a, ex_b, pred_a, pred_b):
            result.context_swap_sensitive += 1

    return result
