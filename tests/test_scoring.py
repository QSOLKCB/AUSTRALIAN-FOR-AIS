"""
Tests for the deterministic reference evaluator.
"""

import json
import pathlib

import pytest

from australian_for_ais.scoring import (
    ComponentScores,
    _context_swap_sensitive,
    _normalise,
    _pragmatic_matches,
    load_examples,
    load_predictions,
    score,
)
from australian_for_ais.models import BenchmarkExample, EvaluationRecord
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
        predicted_pragmatic="Pragmatic reading A",
        predicted_hostility=False,
        model_confidence=0.8,
    )
    defaults.update(kwargs)
    return EvaluationRecord(**defaults)


class TestHelpers:
    def test_normalise(self):
        assert _normalise("  Hello World  ") == "hello world"

    def test_pragmatic_matches_exact(self):
        assert _pragmatic_matches("Pragmatic reading A", ["Pragmatic reading A"])

    def test_pragmatic_matches_case_insensitive(self):
        assert _pragmatic_matches("PRAGMATIC READING A", ["Pragmatic reading A"])

    def test_pragmatic_matches_no_match(self):
        assert not _pragmatic_matches("Something else", ["Pragmatic reading A"])

    def test_pragmatic_matches_multiple(self):
        assert _pragmatic_matches("Reading B", ["Reading A", "Reading B"])

    def test_context_swap_sensitive_different(self):
        pred_a = _make_prediction(example_id="a", predicted_pragmatic="Sarcasm")
        pred_b = _make_prediction(example_id="b", predicted_pragmatic="Sincere praise")
        assert _context_swap_sensitive(pred_a, pred_b)

    def test_context_swap_not_sensitive_same(self):
        pred_a = _make_prediction(example_id="a", predicted_pragmatic="Sarcasm")
        pred_b = _make_prediction(example_id="b", predicted_pragmatic="sarcasm")
        assert not _context_swap_sensitive(pred_a, pred_b)


class TestScoring:
    def _examples(self) -> dict[str, BenchmarkExample]:
        return {"t-001": _make_example()}

    def _predictions(self) -> dict[str, EvaluationRecord]:
        return {"t-001": _make_prediction()}

    def test_perfect_pragmatic_score(self):
        examples = self._examples()
        predictions = self._predictions()
        result = score(examples, predictions)
        assert result.pragmatic_match == 1
        assert result.pragmatic_total == 1

    def test_wrong_pragmatic(self):
        examples = self._examples()
        predictions = {"t-001": _make_prediction(predicted_pragmatic="Wrong")}
        result = score(examples, predictions)
        assert result.pragmatic_match == 0

    def test_hostility_correct(self):
        result = score(self._examples(), self._predictions())
        assert result.hostility_correct == 1

    def test_hostility_wrong(self):
        examples = self._examples()
        predictions = {"t-001": _make_prediction(predicted_hostility=True)}
        result = score(examples, predictions)
        assert result.hostility_correct == 0

    def test_ambiguity_recognition_for_ambiguous_example(self):
        ex = _make_example(
            ambiguity=True,
            pragmatic_interpretations=["Reading A", "Reading B"],
            primary_pragmatic_interpretation="Reading A",
        )
        examples = {"t-001": ex}
        predictions = {"t-001": _make_prediction(predicted_ambiguity=True)}
        result = score(examples, predictions)
        assert result.ambiguity_total == 1
        assert result.ambiguity_recognised == 1

    def test_ambiguity_not_recognised(self):
        ex = _make_example(
            ambiguity=True,
            pragmatic_interpretations=["Reading A", "Reading B"],
            primary_pragmatic_interpretation="Reading A",
        )
        examples = {"t-001": ex}
        predictions = {"t-001": _make_prediction(predicted_ambiguity=False)}
        result = score(examples, predictions)
        assert result.ambiguity_recognised == 0

    def test_non_ambiguous_example_not_counted(self):
        examples = self._examples()  # ambiguity=False
        result = score(examples, self._predictions())
        assert result.ambiguity_total == 0

    def test_social_valence_correct(self):
        examples = self._examples()
        predictions = {"t-001": _make_prediction(predicted_social_valence="neutral")}
        result = score(examples, predictions)
        assert result.social_valence_correct == 1

    def test_social_valence_wrong(self):
        examples = self._examples()
        predictions = {"t-001": _make_prediction(predicted_social_valence="hostile")}
        result = score(examples, predictions)
        assert result.social_valence_correct == 0

    def test_literal_accuracy(self):
        examples = self._examples()
        predictions = {"t-001": _make_prediction(predicted_literal="Literal reading")}
        result = score(examples, predictions)
        assert result.literal_correct == 1
        assert result.literal_total == 1

    def test_literal_wrong(self):
        examples = self._examples()
        predictions = {"t-001": _make_prediction(predicted_literal="Wrong literal")}
        result = score(examples, predictions)
        assert result.literal_correct == 0

    def test_unknown_example_id_generates_error(self):
        examples = self._examples()
        predictions = {"no-such-id": _make_prediction(example_id="no-such-id")}
        result = score(examples, predictions)
        assert len(result.errors) == 1

    def test_context_swap_sensitivity(self):
        ex_a = _make_example(id="cs-a", context_swap_group="csw-1")
        ex_b = _make_example(id="cs-b", context_swap_group="csw-1")
        examples = {"cs-a": ex_a, "cs-b": ex_b}
        pred_a = _make_prediction(example_id="cs-a", predicted_pragmatic="Sincere praise")
        pred_b = _make_prediction(example_id="cs-b", predicted_pragmatic="Sarcasm")
        predictions = {"cs-a": pred_a, "cs-b": pred_b}
        result = score(examples, predictions)
        assert result.context_swap_pairs_found == 1
        assert result.context_swap_sensitive == 1

    def test_context_swap_not_sensitive(self):
        ex_a = _make_example(id="cs-a", context_swap_group="csw-1")
        ex_b = _make_example(id="cs-b", context_swap_group="csw-1")
        examples = {"cs-a": ex_a, "cs-b": ex_b}
        pred_a = _make_prediction(example_id="cs-a", predicted_pragmatic="Same output")
        pred_b = _make_prediction(example_id="cs-b", predicted_pragmatic="Same output")
        predictions = {"cs-a": pred_a, "cs-b": pred_b}
        result = score(examples, predictions)
        assert result.context_swap_pairs_found == 1
        assert result.context_swap_sensitive == 0

    def test_scoring_is_deterministic(self):
        examples = self._examples()
        predictions = self._predictions()
        result_1 = score(examples, predictions)
        result_2 = score(examples, predictions)
        assert result_1.as_dict() == result_2.as_dict()

    def test_component_scores_as_dict_structure(self):
        result = score(self._examples(), self._predictions())
        d = result.as_dict()
        assert "pragmatic_match_rate" in d
        assert "hostility_accuracy" in d
        assert "ambiguity_recognition_rate" in d
        assert "context_swap_sensitivity_rate" in d
        assert "errors" in d


class TestLoadExamples:
    def test_load_starter_examples(self):
        examples = load_examples(DATA_PATH)
        assert len(examples) > 0

    def test_load_malformed_fails(self, tmp_path):
        bad = tmp_path / "bad.jsonl"
        bad.write_text('{"id": "x", malformed}\n', encoding="utf-8")
        with pytest.raises(ValidationError):
            load_examples(bad)

    def test_load_duplicate_id_fails(self, tmp_path):
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
        dup = tmp_path / "dup.jsonl"
        dup.write_text(
            json.dumps(rec) + "\n" + json.dumps(rec) + "\n",
            encoding="utf-8"
        )
        with pytest.raises(ValidationError, match="duplicate"):
            load_examples(dup)
