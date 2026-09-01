"""Tests for the deterministic reference evaluator."""

import json
import pathlib

import pytest

from australian_for_ais.models import BenchmarkExample, EvaluationRecord
from australian_for_ais.scoring import (
    _context_swap_sensitive,
    _normalise,
    _pragmatic_matches,
    load_examples,
    load_predictions,
    score,
)
from australian_for_ais.validation import ValidationError

REPO_ROOT = pathlib.Path(__file__).parent.parent
DATA_PATH = REPO_ROOT / "data" / "starter" / "examples.jsonl"


def _make_example(**kwargs) -> BenchmarkExample:
    defaults = dict(
        id="t-001",
        locale="en-AU",
        utterance="Test utterance",
        context="Test context",
        speaker_relationship="Friends",
        literal_interpretation="Literal reading",
        pragmatic_interpretations=["Pragmatic reading A"],
        primary_pragmatic_interpretation="Pragmatic reading A",
        humour_mechanisms=["literal"],
        social_valence="neutral",
        hostility=False,
        confidence=0.8,
        ambiguity=False,
        cultural_dependency="low",
        context_required=False,
        source_type="synthetic",
        provenance="test",
        license="Apache-2.0",
    )
    defaults.update(kwargs)
    return BenchmarkExample(**defaults)


def _make_prediction(**kwargs) -> EvaluationRecord:
    defaults = dict(
        example_id="t-001",
        predicted_literal="Literal reading",
        predicted_pragmatic="Pragmatic reading A",
        predicted_hostility=False,
        predicted_social_valence="neutral",
        predicted_ambiguity=False,
        model_confidence=0.8,
    )
    defaults.update(kwargs)
    return EvaluationRecord(**defaults)


class TestHelpers:
    def test_normalise(self):
        assert _normalise("  Hello World  ") == "hello world"

    def test_pragmatic_matches_multiple(self):
        assert _pragmatic_matches("READING B", ["Reading A", "Reading B"])

    def test_context_swap_requires_correct_direction(self):
        ex_a = _make_example(
            id="a",
            context="Successful event",
            pragmatic_interpretations=["Sincere praise"],
            primary_pragmatic_interpretation="Sincere praise",
        )
        ex_b = _make_example(
            id="b",
            context="Failed event",
            pragmatic_interpretations=["Sarcastic criticism"],
            primary_pragmatic_interpretation="Sarcastic criticism",
        )
        pred_a = _make_prediction(
            example_id="a", predicted_pragmatic="Sincere praise"
        )
        pred_b = _make_prediction(
            example_id="b", predicted_pragmatic="Sarcastic criticism"
        )
        assert _context_swap_sensitive(ex_a, ex_b, pred_a, pred_b)

        swapped_a = _make_prediction(
            example_id="a", predicted_pragmatic="Sarcastic criticism"
        )
        swapped_b = _make_prediction(
            example_id="b", predicted_pragmatic="Sincere praise"
        )
        assert not _context_swap_sensitive(ex_a, ex_b, swapped_a, swapped_b)


class TestScoring:
    def _examples(self) -> dict[str, BenchmarkExample]:
        return {"t-001": _make_example()}

    def _predictions(self) -> dict[str, EvaluationRecord]:
        return {"t-001": _make_prediction()}

    def test_perfect_component_scores(self):
        result = score(self._examples(), self._predictions())
        assert result.literal_correct == 1
        assert result.pragmatic_match == 1
        assert result.hostility_correct == 1
        assert result.social_valence_correct == 1
        assert result.n_matched_predictions == 1
        assert result.errors == []

    def test_missing_prediction_counts_in_denominators(self):
        examples = {
            "t-001": _make_example(id="t-001"),
            "t-002": _make_example(id="t-002"),
        }
        predictions = {"t-001": _make_prediction(example_id="t-001")}
        result = score(examples, predictions)
        assert result.pragmatic_total == 2
        assert result.hostility_total == 2
        assert result.literal_total == 2
        assert result.social_valence_total == 2
        assert result.pragmatic_match == 1
        assert result.as_dict()["pragmatic_match_rate"] == 0.5
        assert result.as_dict()["prediction_coverage_rate"] == 0.5
        assert any("Missing prediction" in err for err in result.errors)

    def test_missing_ambiguous_prediction_counts_as_missed(self):
        ex = _make_example(
            ambiguity=True,
            pragmatic_interpretations=["A", "B"],
            primary_pragmatic_interpretation="A",
        )
        result = score({"t-001": ex}, {})
        assert result.ambiguity_total == 1
        assert result.ambiguity_recognised == 0

    def test_insufficient_context_is_an_accepted_pragmatic_answer(self):
        ex = _make_example(
            ambiguity=True,
            confidence=0.3,
            pragmatic_interpretations=["Sincere approval", "Sarcastic dismissal"],
            primary_pragmatic_interpretation="insufficient_context",
        )
        pred = _make_prediction(
            predicted_pragmatic="insufficient_context",
            predicted_ambiguity=True,
            model_confidence=0.9,
        )
        result = score({"t-001": ex}, {"t-001": pred})
        assert result.pragmatic_match == 1
        assert result.ambiguity_recognised == 1
        assert result.as_dict()["confidence_brier_score"] == pytest.approx(0.01)

    def test_uncertain_hostility_annotation_is_excluded_from_accuracy(self):
        ex = _make_example(hostility="uncertain")
        pred = _make_prediction(predicted_hostility=True)
        result = score({"t-001": ex}, {"t-001": pred})
        assert result.hostility_total == 0
        assert result.hostility_correct == 0
        assert result.hostility_uncertain_examples == 1
        assert result.as_dict()["hostility_accuracy"] is None

    def test_confidence_changes_brier_score(self):
        examples = self._examples()
        good_conf = score(
            examples,
            {"t-001": _make_prediction(model_confidence=0.95)},
        ).as_dict()["confidence_brier_score"]
        low_conf = score(
            examples,
            {"t-001": _make_prediction(model_confidence=0.2)},
        ).as_dict()["confidence_brier_score"]
        assert good_conf < low_conf

    def test_wrong_high_confidence_is_penalised(self):
        result = score(
            self._examples(),
            {
                "t-001": _make_prediction(
                    predicted_pragmatic="Wrong", model_confidence=0.95
                )
            },
        )
        assert result.as_dict()["confidence_brier_score"] == pytest.approx(0.9025)

    def test_unknown_prediction_generates_error(self):
        predictions = {"unknown": _make_prediction(example_id="unknown")}
        result = score(self._examples(), predictions)
        assert any("unknown example_id" in err for err in result.errors)
        assert any("Missing prediction" in err for err in result.errors)

    def test_context_swap_requires_correct_answers(self):
        ex_a = _make_example(
            id="cs-a",
            context="Successful event",
            context_swap_group="csw-1",
            pragmatic_interpretations=["Sincere praise"],
            primary_pragmatic_interpretation="Sincere praise",
        )
        ex_b = _make_example(
            id="cs-b",
            context="Failed event",
            context_swap_group="csw-1",
            pragmatic_interpretations=["Sarcastic criticism"],
            primary_pragmatic_interpretation="Sarcastic criticism",
        )
        examples = {"cs-a": ex_a, "cs-b": ex_b}

        correct = {
            "cs-a": _make_prediction(
                example_id="cs-a", predicted_pragmatic="Sincere praise"
            ),
            "cs-b": _make_prediction(
                example_id="cs-b", predicted_pragmatic="Sarcastic criticism"
            ),
        }
        assert score(examples, correct).context_swap_sensitive == 1

        wrong_but_different = {
            "cs-a": _make_prediction(
                example_id="cs-a", predicted_pragmatic="Wrong A"
            ),
            "cs-b": _make_prediction(
                example_id="cs-b", predicted_pragmatic="Wrong B"
            ),
        }
        assert score(examples, wrong_but_different).context_swap_sensitive == 0

    def test_context_swap_missing_member_is_failure(self):
        ex_a = _make_example(
            id="cs-a",
            context="Context A",
            context_swap_group="csw-1",
            pragmatic_interpretations=["Reading A"],
            primary_pragmatic_interpretation="Reading A",
        )
        ex_b = _make_example(
            id="cs-b",
            context="Context B",
            context_swap_group="csw-1",
            pragmatic_interpretations=["Reading B"],
            primary_pragmatic_interpretation="Reading B",
        )
        result = score(
            {"cs-a": ex_a, "cs-b": ex_b},
            {"cs-a": _make_prediction(example_id="cs-a", predicted_pragmatic="Reading A")},
        )
        assert result.context_swap_pairs_found == 1
        assert result.context_swap_sensitive == 0

    def test_malformed_context_swap_is_rejected_before_pair_scoring(self):
        ex_a = _make_example(
            id="cs-a",
            context="Same context",
            context_swap_group="csw-1",
            pragmatic_interpretations=["Reading A"],
            primary_pragmatic_interpretation="Reading A",
        )
        ex_b = _make_example(
            id="cs-b",
            context=" same context ",
            context_swap_group="csw-1",
            pragmatic_interpretations=["Reading B"],
            primary_pragmatic_interpretation="Reading B",
        )
        with pytest.raises(ValidationError, match="distinct context"):
            score({"cs-a": ex_a, "cs-b": ex_b}, {})

    def test_scoring_is_deterministic(self):
        result_1 = score(self._examples(), self._predictions())
        result_2 = score(self._examples(), self._predictions())
        assert result_1.as_dict() == result_2.as_dict()


class TestLoaders:
    def test_load_starter_examples(self):
        examples = load_examples(DATA_PATH)
        assert len(examples) == 15

    def test_load_duplicate_example_id_fails(self, tmp_path):
        rec = {
            "id": "dup-001",
            "locale": "en-AU",
            "utterance": "Test",
            "context": "c",
            "speaker_relationship": "friends",
            "literal_interpretation": "lit",
            "pragmatic_interpretations": ["p"],
            "primary_pragmatic_interpretation": "p",
            "humour_mechanisms": ["literal"],
            "social_valence": "neutral",
            "hostility": False,
            "confidence": 0.8,
            "ambiguity": False,
            "cultural_dependency": "low",
            "context_required": False,
            "source_type": "synthetic",
            "provenance": "test",
            "license": "Apache-2.0",
        }
        path = tmp_path / "dup.jsonl"
        path.write_text(
            json.dumps(rec) + "\n" + json.dumps(rec) + "\n", encoding="utf-8"
        )
        with pytest.raises(ValidationError, match="duplicate"):
            load_examples(path)

    def test_load_malformed_context_swap_group_fails(self, tmp_path):
        rec = {
            "id": "swap-001",
            "locale": "en-AU",
            "utterance": "Good one, mate.",
            "context": "A success.",
            "speaker_relationship": "friends",
            "literal_interpretation": "praise",
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
            "provenance": "test",
            "license": "Apache-2.0",
            "context_swap_group": "orphan",
        }
        path = tmp_path / "bad-swap.jsonl"
        path.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        with pytest.raises(ValidationError, match="at least two"):
            load_examples(path)

    def test_load_prediction_requires_complete_record(self, tmp_path):
        path = tmp_path / "predictions.jsonl"
        path.write_text(
            json.dumps(
                {
                    "example_id": "t-001",
                    "predicted_pragmatic": "Pragmatic reading A",
                    "predicted_hostility": False,
                    "model_confidence": 0.8,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValidationError):
            load_predictions(path)
