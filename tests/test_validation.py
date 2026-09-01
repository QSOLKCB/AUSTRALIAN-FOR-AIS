"""
Tests for the validation module.
"""

import pathlib

import pytest

from australian_for_ais.validation import (
    ValidationError,
    validate_example_record,
    validate_evaluation_record,
    validate_jsonl_file,
)

REPO_ROOT = pathlib.Path(__file__).parent.parent
DATA_PATH = REPO_ROOT / "data" / "starter" / "examples.jsonl"


def _minimal_valid_example() -> dict:
    """Return a minimal valid example record."""
    return {
        "id": "test-001",
        "locale": "en-AU",
        "utterance": "She's not bad.",
        "context": "Person views a spectacular landscape.",
        "speaker_relationship": "Close friends",
        "literal_interpretation": "The subject is not of poor quality.",
        "pragmatic_interpretations": ["Understated praise"],
        "primary_pragmatic_interpretation": "Understated praise",
        "humour_mechanisms": ["understatement"],
        "social_valence": "friendly",
        "hostility": False,
        "confidence": 0.8,
        "ambiguity": False,
        "cultural_dependency": "high",
        "context_required": True,
        "source_type": "synthetic",
        "provenance": "Test fixture",
        "license": "Apache-2.0",
    }


def _minimal_valid_prediction() -> dict:
    return {
        "example_id": "test-001",
        "predicted_pragmatic": "Understated praise",
        "predicted_hostility": False,
        "model_confidence": 0.75,
    }


class TestExampleValidation:
    def test_valid_record_passes(self):
        validate_example_record(_minimal_valid_example())

    def test_missing_id_fails(self):
        rec = _minimal_valid_example()
        del rec["id"]
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_empty_id_fails(self):
        rec = _minimal_valid_example()
        rec["id"] = ""
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_missing_utterance_fails(self):
        rec = _minimal_valid_example()
        del rec["utterance"]
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_confidence_too_high_fails(self):
        rec = _minimal_valid_example()
        rec["confidence"] = 1.5
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_confidence_negative_fails(self):
        rec = _minimal_valid_example()
        rec["confidence"] = -0.1
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_empty_pragmatic_interpretations_fails(self):
        rec = _minimal_valid_example()
        rec["pragmatic_interpretations"] = []
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_invalid_humour_mechanism_fails(self):
        rec = _minimal_valid_example()
        rec["humour_mechanisms"] = ["not_a_real_mechanism"]
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_invalid_social_valence_fails(self):
        rec = _minimal_valid_example()
        rec["social_valence"] = "cheerful"
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_hostility_uncertain_string_passes(self):
        rec = _minimal_valid_example()
        rec["hostility"] = "uncertain"
        validate_example_record(rec)

    def test_hostility_invalid_string_fails(self):
        rec = _minimal_valid_example()
        rec["hostility"] = "maybe"
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_ambiguity_true_with_multiple_interpretations_passes(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["pragmatic_interpretations"] = ["Reading A", "Reading B"]
        validate_example_record(rec)

    def test_ambiguity_true_with_insufficient_context_passes(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["primary_pragmatic_interpretation"] = "insufficient_context"
        validate_example_record(rec)

    def test_ambiguity_true_single_interpretation_no_insufficient_fails(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["pragmatic_interpretations"] = ["Only one reading"]
        rec["primary_pragmatic_interpretation"] = "Only one reading"
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_unknown_field_fails(self):
        rec = _minimal_valid_example()
        rec["invented_field"] = "something"
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_invalid_source_type_fails(self):
        rec = _minimal_valid_example()
        rec["source_type"] = "made_up"
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_invalid_cultural_dependency_fails(self):
        rec = _minimal_valid_example()
        rec["cultural_dependency"] = "extreme"
        with pytest.raises(ValidationError):
            validate_example_record(rec)


class TestEvaluationValidation:
    def test_valid_prediction_passes(self):
        validate_evaluation_record(_minimal_valid_prediction())

    def test_missing_example_id_fails(self):
        rec = _minimal_valid_prediction()
        del rec["example_id"]
        with pytest.raises(ValidationError):
            validate_evaluation_record(rec)

    def test_model_confidence_out_of_range_fails(self):
        rec = _minimal_valid_prediction()
        rec["model_confidence"] = 1.1
        with pytest.raises(ValidationError):
            validate_evaluation_record(rec)

    def test_predicted_hostility_uncertain_passes(self):
        rec = _minimal_valid_prediction()
        rec["predicted_hostility"] = "uncertain"
        validate_evaluation_record(rec)

    def test_predicted_hostility_invalid_fails(self):
        rec = _minimal_valid_prediction()
        rec["predicted_hostility"] = "maybe"
        with pytest.raises(ValidationError):
            validate_evaluation_record(rec)

    def test_unknown_field_fails(self):
        rec = _minimal_valid_prediction()
        rec["extra_field"] = "oops"
        with pytest.raises(ValidationError):
            validate_evaluation_record(rec)


class TestJSONLValidation:
    def test_starter_data_validates(self):
        errors = validate_jsonl_file(DATA_PATH)
        assert errors == [], f"Starter data validation errors:\n" + "\n".join(errors)

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises((FileNotFoundError, OSError)):
            validate_jsonl_file(tmp_path / "nonexistent.jsonl")

    def test_malformed_json_caught(self, tmp_path):
        bad = tmp_path / "bad.jsonl"
        bad.write_text('{"id": "ok", malformed}\n', encoding="utf-8")
        errors = validate_jsonl_file(bad)
        assert len(errors) >= 1

    def test_blank_lines_skipped(self, tmp_path):
        import json as _json
        rec = _minimal_valid_example()
        good = tmp_path / "good.jsonl"
        good.write_text(
            "\n" + _json.dumps(rec) + "\n\n",
            encoding="utf-8"
        )
        errors = validate_jsonl_file(good)
        assert errors == []
