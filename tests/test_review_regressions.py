"""Regression tests for review-discovered contract edge cases."""

import json
import pathlib

import pytest

from australian_for_ais.models import BenchmarkExample, EvaluationRecord
from australian_for_ais.scoring import load_examples, score
from australian_for_ais.validation import (
    ValidationError,
    validate_context_swap_groups,
    validate_evaluation_record,
    validate_example_record,
    validate_jsonl_file,
)

REPO_ROOT = pathlib.Path(__file__).parent.parent
DATA_PATH = REPO_ROOT / "data" / "starter" / "examples.jsonl"


def _example_record(**overrides) -> dict:
    record = {
        "id": "test-001",
        "locale": "en-AU",
        "utterance": "Good one, mate.",
        "context": "A successful task has just been completed.",
        "speaker_relationship": "Friends",
        "literal_interpretation": "Positive evaluation.",
        "pragmatic_interpretations": ["Sincere praise"],
        "primary_pragmatic_interpretation": "Sincere praise",
        "humour_mechanisms": ["literal"],
        "social_valence": "friendly",
        "hostility": False,
        "confidence": 0.8,
        "ambiguity": False,
        "cultural_dependency": "medium",
        "context_required": True,
        "source_type": "synthetic",
        "provenance": "Test fixture",
        "license": "Apache-2.0",
    }
    record.update(overrides)
    return record


def _example_model(**overrides) -> BenchmarkExample:
    return BenchmarkExample.from_dict(_example_record(**overrides))


def _prediction_model(**overrides) -> EvaluationRecord:
    record = {
        "example_id": "test-001",
        "predicted_literal": "Positive evaluation.",
        "predicted_pragmatic": "Sincere praise",
        "predicted_hostility": False,
        "predicted_social_valence": "friendly",
        "predicted_ambiguity": False,
        "model_confidence": 0.8,
    }
    record.update(overrides)
    return EvaluationRecord.from_dict(record)


def test_sentinel_cannot_be_an_ordinary_accepted_reading():
    record = _example_record(
        pragmatic_interpretations=["Sincere praise", "insufficient_context"],
        primary_pragmatic_interpretation="Sincere praise",
    )
    with pytest.raises(ValidationError, match="reserved"):
        validate_example_record(record)


def test_noncanonical_prediction_sentinel_is_rejected():
    record = {
        "example_id": "test-001",
        "predicted_literal": "Positive evaluation.",
        "predicted_pragmatic": " INSUFFICIENT_CONTEXT ",
        "predicted_hostility": False,
        "predicted_social_valence": "friendly",
        "predicted_ambiguity": True,
        "model_confidence": 0.3,
    }
    with pytest.raises(ValidationError, match="written exactly"):
        validate_evaluation_record(record)


def test_direct_scoring_rejects_reserved_sentinel_in_ordinary_example():
    example = _example_model(
        pragmatic_interpretations=["Sincere praise", "insufficient_context"],
        primary_pragmatic_interpretation="Sincere praise",
    )
    prediction = _prediction_model(predicted_pragmatic="insufficient_context")
    with pytest.raises(ValidationError, match="reserved"):
        score({"test-001": example}, {"test-001": prediction})


@pytest.mark.parametrize(
    "overrides, message",
    [
        (
            {
                "primary_pragmatic_interpretation": "insufficient_context",
                "pragmatic_interpretations": ["Sincere praise", "Sarcastic criticism"],
                "ambiguity": False,
                "confidence": 0.3,
            },
            "ambiguity",
        ),
        (
            {
                "primary_pragmatic_interpretation": "insufficient_context",
                "pragmatic_interpretations": ["Sincere praise", "Sarcastic criticism"],
                "ambiguity": True,
                "confidence": 0.9,
            },
            "at or below 0.4",
        ),
        (
            {
                "primary_pragmatic_interpretation": "insufficient_context",
                "pragmatic_interpretations": ["Sincere praise"],
                "ambiguity": True,
                "confidence": 0.3,
            },
            "at least two distinct",
        ),
    ],
)
def test_direct_scoring_validates_sentinel_primary_example_contract(overrides, message):
    example = _example_model(**overrides)
    prediction = _prediction_model(
        predicted_pragmatic="insufficient_context",
        predicted_ambiguity=True,
        model_confidence=0.3,
    )
    with pytest.raises(ValidationError, match=message):
        score({"test-001": example}, {"test-001": prediction})


def test_context_swap_rejects_overlapping_accepted_directions():
    first = _example_record(
        id="swap-a",
        context="A successful task has just been completed.",
        pragmatic_interpretations=["Sincere praise", "Shared fallback"],
        primary_pragmatic_interpretation="Sincere praise",
        ambiguity=True,
        context_swap_group="swap-1",
    )
    second = _example_record(
        id="swap-b",
        context="A careless mistake has just caused a problem.",
        pragmatic_interpretations=["Sarcastic criticism", "Shared fallback"],
        primary_pragmatic_interpretation="Sarcastic criticism",
        ambiguity=True,
        context_swap_group="swap-1",
    )
    with pytest.raises(ValidationError, match="disjoint accepted"):
        validate_context_swap_groups([first, second])


def test_empty_benchmark_validation_fails(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("\n\n", encoding="utf-8")
    errors = validate_jsonl_file(path)
    assert any("at least one example" in error for error in errors)

    with pytest.raises(ValidationError, match="at least one example"):
        load_examples(path)


def test_score_rejects_empty_example_mapping():
    with pytest.raises(ValidationError, match="empty benchmark"):
        score({}, {})


def test_score_rejects_prediction_mapping_key_mismatch():
    example = _example_model()
    prediction = _prediction_model(example_id="other-id")
    with pytest.raises(ValidationError, match="mapping key"):
        score({"test-001": example}, {"test-001": prediction})


def test_score_rejects_example_mapping_key_mismatch():
    example = _example_model(id="other-id")
    with pytest.raises(ValidationError, match="mapping key"):
        score({"test-001": example}, {})


@pytest.mark.parametrize(
    "confidence",
    [
        pytest.param(2.0, id="above-range"),
        pytest.param(-0.1, id="below-range"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="positive-infinity"),
        pytest.param(float("-inf"), id="negative-infinity"),
        pytest.param(10**10000, id="huge-integer"),
    ],
)
def test_score_rejects_invalid_direct_confidence_without_overflow(confidence):
    example = _example_model()
    prediction = _prediction_model(model_confidence=confidence)
    with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
        score({"test-001": example}, {"test-001": prediction})


def test_directory_jsonl_input_is_reported_cleanly(tmp_path):
    directory = tmp_path / "dataset-dir"
    directory.mkdir()

    errors = validate_jsonl_file(directory)
    assert any("not a regular file" in error for error in errors)

    with pytest.raises(ValidationError, match="not a regular file"):
        load_examples(directory)


def test_invalid_utf8_jsonl_is_reported_cleanly(tmp_path):
    path = tmp_path / "invalid-utf8.jsonl"
    path.write_bytes(b'{"id":"broken"}\xff\n')

    errors = validate_jsonl_file(path)
    assert any("UTF-8" in error for error in errors)

    with pytest.raises(ValidationError, match="UTF-8"):
        load_examples(path)


def test_old_mate_fixture_explicitly_rules_out_acquaintance_in_this_context():
    example = load_examples(DATA_PATH)["au-008"]
    assert example.ambiguity is False
    assert "neither recognises or has met before" in example.context
    assert any(
        "actual acquaintance" in reading and "different context" in reading
        for reading in example.alternative_interpretations
    )


def test_file_loader_still_accepts_normal_record(tmp_path):
    path = tmp_path / "one.jsonl"
    path.write_text(json.dumps(_example_record()) + "\n", encoding="utf-8")
    examples = load_examples(path)
    assert list(examples) == ["test-001"]
