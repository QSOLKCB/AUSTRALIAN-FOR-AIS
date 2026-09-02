"""Focused regressions for the latest Phase 2 review findings."""

import json
import pathlib

import pytest

from australian_for_ais.annotation import load_pilot_items
from australian_for_ais.validation import ValidationError

REPO_ROOT = pathlib.Path(__file__).parent.parent
ANNOTATION_UI = REPO_ROOT / "annotation" / "index.html"


def _pilot_item(item_id: str) -> dict:
    return {
        "id": item_id,
        "locale": "en-AU",
        "utterance": "Good one.",
        "context": f"Synthetic context for {item_id}.",
        "speaker_relationship": "colleagues",
        "source_type": "synthetic",
        "provenance": "Test fixture",
        "license": "Apache-2.0",
    }


def _write_jsonl(path: pathlib.Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_literal_required_check_and_serialization_share_one_contract():
    html = ANNOTATION_UI.read_text(encoding="utf-8")

    assert 'const literal = $("literal").value;' in html
    assert 'if (!normaliseReading(literal)) throw new Error("Literal interpretation is required.");' in html
    assert "literal_interpretation: literal," in html
    assert "literal_interpretation: literal.trim()" not in html
    assert 'if (!$("literal").value.trim())' not in html


def test_pilot_validation_error_reports_jsonl_line(tmp_path):
    records = [_pilot_item("item-1"), _pilot_item("item-2")]
    records[1].pop("utterance")
    path = tmp_path / "pilot.jsonl"
    _write_jsonl(path, records)

    with pytest.raises(ValidationError, match=r"^Line 2:"):
        load_pilot_items(path)


def test_pilot_group_validation_reports_participating_lines(tmp_path):
    records = [_pilot_item("item-1"), _pilot_item("item-2")]
    records[0]["context_swap_group"] = "pair-x"
    records[1]["context_swap_group"] = "pair-x"
    records[1]["utterance"] = "Different utterance."
    path = tmp_path / "pilot-group.jsonl"
    _write_jsonl(path, records)

    with pytest.raises(
        ValidationError,
        match=r"context_swap_group 'pair-x' \(lines 1, 2\) must preserve the same utterance",
    ):
        load_pilot_items(path)


def test_relationship_only_context_swap_is_valid(tmp_path):
    records = [_pilot_item("item-1"), _pilot_item("item-2")]
    for record in records:
        record["context"] = "The speaker says this after the same small mistake."
        record["context_swap_group"] = "relationship-only"
    records[0]["speaker_relationship"] = "long-term friends"
    records[1]["speaker_relationship"] = "strangers"
    path = tmp_path / "relationship-only.jsonl"
    _write_jsonl(path, records)

    items = load_pilot_items(path)
    assert set(items) == {"item-1", "item-2"}


def test_browser_saved_annotations_are_bound_to_item_content():
    html = ANNOTATION_UI.read_text(encoding="utf-8")

    assert "function itemObservationKey(item)" in html
    assert "saved.item_observation_key !== itemObservationKey(item)" in html
    assert "saved.annotation.example_id !== item.id" in html
    assert "const saved = {item_observation_key: itemObservationKey(item), annotation};" in html
    assert "const annotation = unpackStoredAnnotation(item, raw);" in html
    assert "if (annotation) records.push(annotation);" in html
