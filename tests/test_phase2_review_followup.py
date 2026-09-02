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


def test_literal_required_check_uses_shared_phase2_normalizer():
    html = ANNOTATION_UI.read_text(encoding="utf-8")

    assert 'const literal = $("literal").value;' in html
    assert 'if (!normaliseReading(literal)) throw new Error("Literal interpretation is required.");' in html
    assert 'if (!$("literal").value.trim())' not in html


def test_pilot_validation_error_reports_jsonl_line(tmp_path):
    records = [_pilot_item("item-1"), _pilot_item("item-2")]
    records[1].pop("utterance")
    path = tmp_path / "pilot.jsonl"
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match=r"^Line 2:"):
        load_pilot_items(path)
