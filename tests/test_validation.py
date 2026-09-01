"""Tests for validation and dataset-level contracts."""

import json
import pathlib

import pytest

from australian_for_ais.validation import (
    ValidationError,
    validate_evaluation_record,
    validate_example_record,
    validate_jsonl_file,
)

REPO_ROOT = pathlib.Path(__file__).parent.parent
DATA_PATH = REPO_ROOT / "data" / "starter" / "examples.jsonl"


def _minimal_valid_example() -> dict:
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
        "predicted_literal": "The subject is not of poor quality.",
        "predicted_pragmatic": "Understated praise",
        "predicted_hostility": False,
        "predicted_social_valence": "friendly",
        "predicted_ambiguity": False,
        "model_confidence": 0.75,
    }


class TestExampleValidation:
    def test_valid_record_passes(self):
        validate_example_record(_minimal_valid_example())

    @pytest.mark.parametrize("field", ["id", "utterance", "provenance", "license"])
    def test_missing_required_field_fails(self, field):
        rec = _minimal_valid_example()
        del rec[field]
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_non_object_fails_cleanly(self):
        with pytest.raises(ValidationError, match="JSON object"):
            validate_example_record([])

    @pytest.mark.parametrize("value", [-0.1, 1.1, True])
    def test_invalid_confidence_fails(self, value):
        rec = _minimal_valid_example()
        rec["confidence"] = value
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_primary_must_be_scorable(self):
        rec = _minimal_valid_example()
        rec["primary_pragmatic_interpretation"] = "Different wording"
        with pytest.raises(ValidationError, match="must be present"):
            validate_example_record(rec)

    def test_insufficient_context_requires_low_confidence(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["primary_pragmatic_interpretation"] = "insufficient_context"
        rec["confidence"] = 0.41
        with pytest.raises(ValidationError, match="at or below 0.4"):
            validate_example_record(rec)

    def test_insufficient_context_at_ceiling_passes(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["primary_pragmatic_interpretation"] = "insufficient_context"
        rec["confidence"] = 0.4
        validate_example_record(rec)

    @pytest.mark.parametrize("field", ["provenance", "license"])
    def test_whitespace_metadata_fails(self, field):
        rec = _minimal_valid_example()
        rec[field] = "   "
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_hostility_uncertain_passes(self):
        rec = _minimal_valid_example()
        rec["hostility"] = "uncertain"
        validate_example_record(rec)

    def test_invalid_hostility_fails(self):
        rec = _minimal_valid_example()
        rec["hostility"] = "maybe"
        with pytest.raises(ValidationError):
            validate_example_record(rec)


class TestEvaluationValidation:
    def test_valid_prediction_passes(self):
        validate_evaluation_record(_minimal_valid_prediction())

    @pytest.mark.parametrize(
        "field",
        [
            "example_id",
            "predicted_literal",
            "predicted_pragmatic",
            "predicted_hostility",
            "predicted_social_valence",
            "predicted_ambiguity",
            "model_confidence",
        ],
    )
    def test_every_advertised_dimension_is_required(self, field):
        rec = _minimal_valid_prediction()
        del rec[field]
        with pytest.raises(ValidationError):
            validate_evaluation_record(rec)

    def test_non_object_prediction_fails_cleanly(self):
        with pytest.raises(ValidationError, match="JSON object"):
            validate_evaluation_record(None)

    def test_predicted_hostility_invalid_fails(self):
        rec = _minimal_valid_prediction()
        rec["predicted_hostility"] = "maybe"
        with pytest.raises(ValidationError):
            validate_evaluation_record(rec)


class TestJSONLValidation:
    def test_starter_data_validates(self):
        errors = validate_jsonl_file(DATA_PATH)
        assert errors == [], "\n".join(errors)

    def test_malformed_json_caught(self, tmp_path):
        bad = tmp_path / "bad.jsonl"
        bad.write_text('{"id": "ok", malformed}\n', encoding="utf-8")
        assert validate_jsonl_file(bad)

    def test_non_object_json_is_reported_not_crashed(self, tmp_path):
        bad = tmp_path / "bad.jsonl"
        bad.write_text("null\n", encoding="utf-8")
        errors = validate_jsonl_file(bad)
        assert len(errors) == 1
        assert "JSON object" in errors[0]

    def test_duplicate_ids_rejected_by_validation_gate(self, tmp_path):
        rec = _minimal_valid_example()
        dup = tmp_path / "dup.jsonl"
        dup.write_text(json.dumps(rec) + "\n" + json.dumps(rec) + "\n", encoding="utf-8")
        errors = validate_jsonl_file(dup)
        assert any("duplicate" in err.lower() for err in errors)

    def test_blank_lines_skipped(self, tmp_path):
        rec = _minimal_valid_example()
        good = tmp_path / "good.jsonl"
        good.write_text("\n" + json.dumps(rec) + "\n\n", encoding="utf-8")
        assert validate_jsonl_file(good) == []
