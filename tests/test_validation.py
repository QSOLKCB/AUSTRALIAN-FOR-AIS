"""Tests for validation and dataset-level contracts."""

import json
import pathlib
from typing import get_args

import pytest

from australian_for_ais.models import SocialValence
from australian_for_ais.validation import (
    ValidationError,
    validate_context_swap_groups,
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


def _context_swap_pair() -> list[dict]:
    a = _minimal_valid_example()
    a.update(
        {
            "id": "swap-a",
            "utterance": "Good one, mate.",
            "context": "A successful task has just been completed.",
            "pragmatic_interpretations": ["Sincere praise"],
            "primary_pragmatic_interpretation": "Sincere praise",
            "context_swap_group": "swap-1",
        }
    )
    b = _minimal_valid_example()
    b.update(
        {
            "id": "swap-b",
            "utterance": "Good one, mate.",
            "context": "A careless mistake has just caused a problem.",
            "pragmatic_interpretations": ["Sarcastic criticism"],
            "primary_pragmatic_interpretation": "Sarcastic criticism",
            "context_swap_group": "swap-1",
        }
    )
    return [a, b]


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

    def test_ambiguous_requires_two_distinct_readings(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["pragmatic_interpretations"] = ["Reading A", "  reading a  "]
        rec["primary_pragmatic_interpretation"] = "Reading A"
        with pytest.raises(ValidationError, match="distinct normalized"):
            validate_example_record(rec)

    def test_ambiguous_internal_whitespace_does_not_create_distinct_reading(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["pragmatic_interpretations"] = ["Sincere approval", "Sincere   approval"]
        rec["primary_pragmatic_interpretation"] = "Sincere approval"
        with pytest.raises(ValidationError, match="distinct normalized"):
            validate_example_record(rec)

    def test_insufficient_context_still_requires_two_distinct_readings(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["primary_pragmatic_interpretation"] = "insufficient_context"
        rec["confidence"] = 0.3
        with pytest.raises(ValidationError, match="distinct normalized"):
            validate_example_record(rec)

    def test_insufficient_context_requires_low_confidence(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["pragmatic_interpretations"] = ["Understated praise", "Lukewarm response"]
        rec["primary_pragmatic_interpretation"] = "insufficient_context"
        rec["confidence"] = 0.41
        with pytest.raises(ValidationError, match="at or below 0.4"):
            validate_example_record(rec)

    def test_insufficient_context_at_ceiling_passes(self):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["pragmatic_interpretations"] = ["Understated praise", "Lukewarm response"]
        rec["primary_pragmatic_interpretation"] = "insufficient_context"
        rec["confidence"] = 0.4
        validate_example_record(rec)

    @pytest.mark.parametrize(
        "variant",
        ["INSUFFICIENT_CONTEXT", " insufficient_context ", "Insufficient_Context"],
    )
    def test_insufficient_context_sentinel_must_be_canonical(self, variant):
        rec = _minimal_valid_example()
        rec["ambiguity"] = True
        rec["pragmatic_interpretations"] = [variant, "Another reading"]
        rec["primary_pragmatic_interpretation"] = variant
        rec["confidence"] = 0.3
        with pytest.raises(ValidationError, match="must be written exactly"):
            validate_example_record(rec)

    @pytest.mark.parametrize(
        "field",
        [
            "id",
            "locale",
            "utterance",
            "context",
            "speaker_relationship",
            "literal_interpretation",
            "primary_pragmatic_interpretation",
            "provenance",
            "license",
        ],
    )
    def test_whitespace_required_text_fails(self, field):
        rec = _minimal_valid_example()
        rec[field] = "   "
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_whitespace_pragmatic_interpretation_fails(self):
        rec = _minimal_valid_example()
        rec["pragmatic_interpretations"] = ["   "]
        rec["primary_pragmatic_interpretation"] = "   "
        with pytest.raises(ValidationError):
            validate_example_record(rec)

    def test_whitespace_alternative_interpretation_fails(self):
        rec = _minimal_valid_example()
        rec["alternative_interpretations"] = ["   "]
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

    def test_social_valence_type_alias_matches_schema_enum(self):
        assert set(get_args(SocialValence)) == {
            "friendly",
            "hostile",
            "neutral",
            "ambiguous",
            "unknown",
        }


class TestContextSwapValidation:
    def test_valid_pair_passes(self):
        validate_context_swap_groups(_context_swap_pair())

    def test_group_requires_at_least_two_members(self):
        with pytest.raises(ValidationError, match="at least two"):
            validate_context_swap_groups([_context_swap_pair()[0]])

    def test_group_requires_same_utterance(self):
        records = _context_swap_pair()
        records[1]["utterance"] = "Different utterance."
        with pytest.raises(ValidationError, match="same utterance"):
            validate_context_swap_groups(records)

    def test_group_requires_distinct_contexts(self):
        records = _context_swap_pair()
        records[1]["context"] = records[0]["context"].upper()
        with pytest.raises(ValidationError, match="distinct context"):
            validate_context_swap_groups(records)

    def test_group_rejects_context_difference_that_is_only_internal_whitespace(self):
        records = _context_swap_pair()
        records[0]["context"] = "A successful task has just been completed."
        records[1]["context"] = "A successful   task has just been completed."
        with pytest.raises(ValidationError, match="distinct context"):
            validate_context_swap_groups(records)

    def test_group_requires_distinct_primary_directions(self):
        records = _context_swap_pair()
        records[1]["primary_pragmatic_interpretation"] = "Sincere praise"
        records[1]["pragmatic_interpretations"] = ["Sincere praise"]
        with pytest.raises(ValidationError, match="distinct primary"):
            validate_context_swap_groups(records)

    def test_group_rejects_primary_difference_that_is_only_internal_whitespace(self):
        records = _context_swap_pair()
        records[1]["primary_pragmatic_interpretation"] = "Sincere   praise"
        records[1]["pragmatic_interpretations"] = ["Sincere   praise"]
        with pytest.raises(ValidationError, match="distinct primary"):
            validate_context_swap_groups(records)


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

    @pytest.mark.parametrize(
        "field", ["example_id", "predicted_literal", "predicted_pragmatic"]
    )
    def test_whitespace_prediction_text_fails(self, field):
        rec = _minimal_valid_prediction()
        rec[field] = "   "
        with pytest.raises(ValidationError):
            validate_evaluation_record(rec)

    def test_blank_model_id_fails_when_present(self):
        rec = _minimal_valid_prediction()
        rec["model_id"] = "   "
        with pytest.raises(ValidationError):
            validate_evaluation_record(rec)

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
        dup.write_text(
            json.dumps(rec) + "\n" + json.dumps(rec) + "\n", encoding="utf-8"
        )
        errors = validate_jsonl_file(dup)
        assert any("duplicate" in err.lower() for err in errors)

    def test_malformed_context_swap_rejected_by_validation_gate(self, tmp_path):
        rec = _context_swap_pair()[0]
        path = tmp_path / "bad-swap.jsonl"
        path.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        errors = validate_jsonl_file(path)
        assert any("at least two" in err for err in errors)

    def test_blank_lines_skipped(self, tmp_path):
        rec = _minimal_valid_example()
        good = tmp_path / "good.jsonl"
        good.write_text("\n" + json.dumps(rec) + "\n\n", encoding="utf-8")
        assert validate_jsonl_file(good) == []
