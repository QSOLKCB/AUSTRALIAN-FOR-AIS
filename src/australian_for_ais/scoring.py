"""
Deterministic reference evaluator for Australian For AIs.

IMPORTANT: Read docs/METHODOLOGY.md (Scoring Philosophy) before modifying this module.

Key constraints:
- No machine learning dependencies.
- No randomness. All functions must be deterministic.
- Metrics are reported as components, NOT aggregated into a single score.
- See AU-HUMOUR-010: benchmark score != cultural competence.
- See AU-HUMOUR-006: ambiguity must not be silently collapsed.

The evaluator measures observable correlates of pragmatic understanding against
annotated examples. It does not measure pragmatic understanding itself.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Iterator

from .models import BenchmarkExample, EvaluationRecord
from .validation import ValidationError, iter_jsonl, validate_example_record, validate_evaluation_record


# ---------------------------------------------------------------------------
# Scoring result
# ---------------------------------------------------------------------------

@dataclass
class ComponentScores:
    """
    Component scores for a single evaluation run.

    Each field is an independent metric. Do NOT sum or average these into a
    single composite score — they measure different dimensions.

    See docs/METHODOLOGY.md for metric definitions.
    """

    n_examples: int = 0
    n_predictions: int = 0

    # Literal interpretation accuracy
    literal_correct: int = 0
    literal_total: int = 0

    # Pragmatic interpretation match
    pragmatic_match: int = 0
    pragmatic_total: int = 0

    # Ambiguity recognition (ambiguous examples only)
    ambiguity_recognised: int = 0
    ambiguity_total: int = 0

    # Hostility classification
    hostility_correct: int = 0
    hostility_total: int = 0

    # Social valence classification
    social_valence_correct: int = 0
    social_valence_total: int = 0

    # Context-swap sensitivity
    context_swap_pairs_found: int = 0
    context_swap_sensitive: int = 0

    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        """Return a plain dictionary representation."""

        def safe_rate(num: int, denom: int) -> float | None:
            return round(num / denom, 4) if denom > 0 else None

        return {
            "n_examples": self.n_examples,
            "n_predictions": self.n_predictions,
            "literal_accuracy": safe_rate(self.literal_correct, self.literal_total),
            "pragmatic_match_rate": safe_rate(self.pragmatic_match, self.pragmatic_total),
            "ambiguity_recognition_rate": safe_rate(self.ambiguity_recognised, self.ambiguity_total),
            "hostility_accuracy": safe_rate(self.hostility_correct, self.hostility_total),
            "social_valence_accuracy": safe_rate(self.social_valence_correct, self.social_valence_total),
            "context_swap_pairs_found": self.context_swap_pairs_found,
            "context_swap_sensitivity_rate": safe_rate(
                self.context_swap_sensitive, self.context_swap_pairs_found
            ),
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def _normalise(s: str) -> str:
    """Normalise a string for case-insensitive comparison."""
    return s.strip().lower()


def _pragmatic_matches(
    predicted: str,
    annotated_interpretations: list[str],
) -> bool:
    """
    Return True if predicted matches any annotated pragmatic interpretation.

    Comparison is case-insensitive and strip-normalised.
    This is a string-level heuristic. Semantic equivalence is not measured.
    """
    pred_norm = _normalise(predicted)
    return any(_normalise(a) == pred_norm for a in annotated_interpretations)


def _hostility_matches(
    predicted: bool | str,
    annotated: bool | str,
) -> bool:
    """
    Return True if predicted hostility matches annotated hostility.

    Both values may be bool or "uncertain".
    """
    return predicted == annotated


def _social_valence_matches(
    predicted: str | None,
    annotated: str,
) -> bool:
    if predicted is None:
        return False
    return _normalise(predicted) == _normalise(annotated)


# ---------------------------------------------------------------------------
# Context-swap analysis
# ---------------------------------------------------------------------------

def _find_context_swap_pairs(
    examples: dict[str, BenchmarkExample],
    predictions: dict[str, EvaluationRecord],
) -> list[tuple[BenchmarkExample, BenchmarkExample]]:
    """
    Find pairs of examples that share a context_swap_group and both have predictions.

    Returns a list of (example_a, example_b) pairs.
    """
    groups: dict[str, list[str]] = {}
    for ex_id, ex in examples.items():
        if ex.context_swap_group and ex_id in predictions:
            groups.setdefault(ex.context_swap_group, []).append(ex_id)

    pairs = []
    for group_ids in groups.values():
        if len(group_ids) < 2:
            continue
        # Produce all unordered pairs
        for i in range(len(group_ids)):
            for j in range(i + 1, len(group_ids)):
                a = examples[group_ids[i]]
                b = examples[group_ids[j]]
                pairs.append((a, b))
    return pairs


def _context_swap_sensitive(
    pred_a: EvaluationRecord,
    pred_b: EvaluationRecord,
) -> bool:
    """
    Return True if the model produced different pragmatic predictions for a
    context-swap pair.

    Note: producing different outputs is a necessary but not sufficient
    condition for correct context use. See docs/BENCHMARK-DESIGN.md.
    """
    return _normalise(pred_a.predicted_pragmatic) != _normalise(pred_b.predicted_pragmatic)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_examples(path: pathlib.Path) -> dict[str, BenchmarkExample]:
    """
    Load and validate all benchmark examples from a JSONL file.

    Returns a dict mapping id -> BenchmarkExample.
    Raises ValidationError on invalid records.
    """
    examples: dict[str, BenchmarkExample] = {}
    for lineno, record in iter_jsonl(path):
        validate_example_record(record)
        ex = BenchmarkExample.from_dict(record)
        if ex.id in examples:
            raise ValidationError(
                f"Line {lineno}: duplicate example id '{ex.id}'."
            )
        examples[ex.id] = ex
    return examples


def load_predictions(path: pathlib.Path) -> dict[str, EvaluationRecord]:
    """
    Load and validate all prediction records from a JSONL file.

    Returns a dict mapping example_id -> EvaluationRecord.
    Raises ValidationError on invalid records.
    """
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
    """
    Score predictions against examples.

    Returns ComponentScores with per-dimension metrics.

    This function is deterministic: given the same inputs it always produces
    the same outputs. It has no side effects.
    """
    result = ComponentScores(
        n_examples=len(examples),
        n_predictions=len(predictions),
    )

    for ex_id, pred in predictions.items():
        if ex_id not in examples:
            result.errors.append(
                f"Prediction for unknown example_id '{ex_id}' — skipping."
            )
            continue

        ex = examples[ex_id]

        # Literal accuracy
        if pred.predicted_literal is not None:
            result.literal_total += 1
            if _normalise(pred.predicted_literal) == _normalise(ex.literal_interpretation):
                result.literal_correct += 1

        # Pragmatic match
        result.pragmatic_total += 1
        if _pragmatic_matches(pred.predicted_pragmatic, ex.pragmatic_interpretations):
            result.pragmatic_match += 1

        # Hostility accuracy
        result.hostility_total += 1
        if _hostility_matches(pred.predicted_hostility, ex.hostility):
            result.hostility_correct += 1

        # Social valence accuracy
        if pred.predicted_social_valence is not None:
            result.social_valence_total += 1
            if _social_valence_matches(pred.predicted_social_valence, ex.social_valence):
                result.social_valence_correct += 1

        # Ambiguity recognition (only for genuinely ambiguous examples)
        if ex.ambiguity:
            result.ambiguity_total += 1
            if pred.predicted_ambiguity is True:
                result.ambiguity_recognised += 1

    # Context-swap analysis
    pairs = _find_context_swap_pairs(examples, predictions)
    result.context_swap_pairs_found = len(pairs)
    for ex_a, ex_b in pairs:
        pred_a = predictions[ex_a.id]
        pred_b = predictions[ex_b.id]
        if _context_swap_sensitive(pred_a, pred_b):
            result.context_swap_sensitive += 1

    return result
