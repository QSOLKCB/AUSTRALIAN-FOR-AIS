"""Tests for Phase 2 pilot items, independent annotations, and agreement analysis."""

import json
import pathlib
from importlib import resources

import jsonschema
import pytest

from australian_for_ais.annotation import (
    build_agreement_report,
    load_annotations,
    load_pilot_items,
)
from australian_for_ais.validation import ValidationError, validate_annotation_record

REPO_ROOT = pathlib.Path(__file__).parent.parent
PILOT_PATH = REPO_ROOT / "data" / "pilot" / "items.jsonl"
ANNOTATION_UI_PATH = REPO_ROOT / "annotation" / "index.html"
SCHEMAS_DIR = REPO_ROOT / "schemas"


def _annotation(**overrides):
    record = {
        "annotation_id": "ann-a-item-1",
        "example_id": "item-1",
        "annotator_id": "annotator-aaaaaaaaaaaa",
        "literal_interpretation": "Literal reading",
        "pragmatic_interpretations": ["Pragmatic reading"],
        "primary_pragmatic_interpretation": "Pragmatic reading",
        "humour_mechanisms": ["literal"],
        "social_valence": "neutral",
        "hostility": False,
        "confidence": 0.8,
        "ambiguity": False,
        "cultural_dependency": "low",
        "context_required": True,
        "australian_english_exposure": "medium",
    }
    record.update(overrides)
    return record


def _write_jsonl(path: pathlib.Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


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


def test_phase2_schemas_are_valid_and_packaged():
    package_dir = resources.files("australian_for_ais").joinpath("schemas")
    for name in ("pilot-item.schema.json", "annotation.schema.json"):
        root_schema = json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))
        packaged_schema = json.loads(
            package_dir.joinpath(name).read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator.check_schema(root_schema)
        assert packaged_schema == root_schema
        assert root_schema["x-project-schema-version"] == "0.1.0"


def test_annotation_requires_at_least_one_unique_mechanism():
    with pytest.raises(ValidationError, match="should be non-empty"):
        validate_annotation_record(_annotation(humour_mechanisms=[]))

    with pytest.raises(ValidationError, match="non-unique elements"):
        validate_annotation_record(
            _annotation(humour_mechanisms=["understatement", "understatement"])
        )


def test_unknown_mechanism_is_mutually_exclusive():
    with pytest.raises(ValidationError, match="should not be valid"):
        validate_annotation_record(
            _annotation(humour_mechanisms=["unknown", "sarcasm"])
        )


def test_multiple_retained_readings_require_ambiguity():
    with pytest.raises(ValidationError, match="True was expected"):
        validate_annotation_record(
            _annotation(
                pragmatic_interpretations=["Reading A", "Reading B"],
                primary_pragmatic_interpretation="Reading A",
                ambiguity=False,
            )
        )


def test_duplicate_or_equivalent_retained_readings_are_rejected():
    with pytest.raises(ValidationError):
        validate_annotation_record(
            _annotation(
                pragmatic_interpretations=["Reading A", "Reading A"],
                primary_pragmatic_interpretation="Reading A",
                ambiguity=True,
            )
        )

    with pytest.raises(ValidationError, match="at least two distinct normalized readings"):
        validate_annotation_record(
            _annotation(
                pragmatic_interpretations=["Reading A", " reading   a "],
                primary_pragmatic_interpretation="Reading A",
                ambiguity=True,
            )
        )


def test_annotation_insufficient_context_contract_is_enforced():
    record = _annotation(
        pragmatic_interpretations=["Reading A", "Reading B"],
        primary_pragmatic_interpretation="insufficient_context",
        ambiguity=True,
        confidence=0.3,
    )
    validate_annotation_record(record)

    bad = dict(record, confidence=0.8)
    with pytest.raises(ValidationError, match="at or below 0.4"):
        validate_annotation_record(bad)


def test_annotation_primary_must_be_retained_as_a_reading():
    record = _annotation(primary_pragmatic_interpretation="Different reading")
    with pytest.raises(ValidationError, match="must be present"):
        validate_annotation_record(record)


def test_annotation_id_must_be_generated_pseudonym_format():
    with pytest.raises(ValidationError, match="does not match"):
        validate_annotation_record(_annotation(annotator_id="person@example.com"))


def test_empty_annotation_file_is_rejected(tmp_path):
    path = tmp_path / "annotations.jsonl"
    path.write_text("\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="at least one annotation"):
        load_annotations(path, {"item-1"})


def test_duplicate_annotator_assignment_is_rejected(tmp_path):
    path = tmp_path / "annotations.jsonl"
    _write_jsonl(
        path,
        [
            _annotation(annotation_id="ann-1"),
            _annotation(annotation_id="ann-2"),
        ],
    )
    with pytest.raises(ValidationError, match="more than one annotation"):
        load_annotations(path, {"item-1"})


def test_unknown_annotation_example_is_rejected(tmp_path):
    path = tmp_path / "annotations.jsonl"
    _write_jsonl(path, [_annotation(example_id="missing")])
    with pytest.raises(ValidationError, match="unknown example_id"):
        load_annotations(path, {"item-1"})


def test_agreement_report_preserves_free_text_as_qualitative(tmp_path):
    items_path = tmp_path / "items.jsonl"
    _write_jsonl(items_path, [_pilot_item("item-1")])
    annotations_path = tmp_path / "annotations.jsonl"
    _write_jsonl(
        annotations_path,
        [
            _annotation(
                annotation_id="ann-a",
                annotator_id="annotator-aaaaaaaaaaaa",
            ),
            _annotation(
                annotation_id="ann-b",
                annotator_id="annotator-bbbbbbbbbbbb",
                primary_pragmatic_interpretation="Positive approval",
                pragmatic_interpretations=["Positive approval"],
            ),
        ],
    )

    items = load_pilot_items(items_path)
    annotations = load_annotations(annotations_path, set(items))
    report = build_agreement_report(items, annotations)

    assert report["coverage"]["items_with_at_least_two_annotations"] == 1
    assert report["coverage"]["annotations_per_item"] == {"item-1": 2}
    assert report["categorical_pairwise_agreement"]["hostility"]["agreement_rate"] == 1.0
    assert report["pragmatic_free_text_iaa"] is None
    assert "not scored" in report["pragmatic_free_text_note"]


def test_coverage_report_includes_zero_and_one_annotation_counts(tmp_path):
    items_path = tmp_path / "items.jsonl"
    _write_jsonl(items_path, [_pilot_item("item-1"), _pilot_item("item-2")])
    annotations_path = tmp_path / "annotations.jsonl"
    _write_jsonl(annotations_path, [_annotation()])

    items = load_pilot_items(items_path)
    annotations = load_annotations(annotations_path, set(items))
    report = build_agreement_report(items, annotations)

    assert report["coverage"]["annotations_per_item"] == {
        "item-1": 1,
        "item-2": 0,
    }
    assert report["coverage"]["items_below_two_annotations"] == ["item-1", "item-2"]


def test_committed_pilot_pack_has_60_unannotated_items_and_30_pairs():
    items = load_pilot_items(PILOT_PATH)
    assert len(items) == 60
    groups: dict[str, list[str]] = {}
    for item in items.values():
        assert item.source_type == "synthetic"
        assert "not copied" in item.provenance
        assert " or " not in item.speaker_relationship.casefold()
        if item.context_swap_group:
            groups.setdefault(item.context_swap_group, []).append(item.id)
    assert len(groups) == 30
    assert all(len(member_ids) == 2 for member_ids in groups.values())

    assert items["pilot-005a"].speaker_relationship == "long-term friends"
    assert items["pilot-005b"].speaker_relationship == "strangers"
    assert items["pilot-026a"].speaker_relationship == "mechanic and customer"
    assert items["pilot-026b"].speaker_relationship == "gardeners"


def test_annotation_ui_enforces_privacy_and_independence_contracts():
    html = ANNOTATION_UI_PATH.read_text(encoding="utf-8")
    assert 'id="annotatorId" type="text" readonly' in html
    assert "crypto.getRandomValues" in html
    assert "PSEUDONYM_PATTERN" in html
    assert "orderPilotItems" in html
    assert ":first-pass`" in html
    assert ":later-pass`" in html
    assert 'id="newPseudonym"' in html
    assert "Multiple retained pragmatic readings require ambiguity=true" in html
    assert "Duplicate or equivalent pragmatic readings are not allowed" in html
    assert "Select at least one pragmatic mechanism, or select unknown explicitly" in html
    assert "unknown mechanism cannot be combined" in html
    assert '$("exposure").value = a.australian_english_exposure || "unspecified"' in html
    assert 'humour_mechanisms: selected,' in html
