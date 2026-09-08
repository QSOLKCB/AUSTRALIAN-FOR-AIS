"""Focused regressions for the latest Phase 2 review findings."""

import hashlib
import json
import pathlib
import runpy
import re

import pytest

from australian_for_ais.annotation import load_pilot_items
from australian_for_ais.validation import ValidationError

REPO_ROOT = pathlib.Path(__file__).parent.parent
ANNOTATION_UI = REPO_ROOT / "annotation" / "index.html"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
POLICING_TEST = REPO_ROOT / "tests" / "test_policing_context_roadmap.py"
PHASE2_HEADING = "## [Unreleased] — Phase 2 Pilot Human Annotation"
PHASE1_HEADING = "## [Unreleased] — Phase 1 Research Substrate"
PHASE2_NOTES_HEADING = "### Notes"
FREE_TEXT_IAA_BOUNDARY = (
    "Free-text pragmatic interpretations remain qualitative evidence and are not "
    "assigned a misleading exact-string IAA score."
)
EXPECTED_VISIBLE_PHASE2_NOTES = (
    "### Notes - The Phase 2 pilot is an unannotated research fixture. "
    "No human annotation results, ethical approvals, or empirical agreement statistics "
    "are claimed until real pilot collection occurs. - "
    "Free-text pragmatic interpretations remain qualitative evidence and are not "
    "assigned a misleading exact-string IAA score. ---"
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


def _next_notes_peer_heading(structure: str, namespace: dict) -> int:
    """Find a visible ATX, Setext, or HTML peer heading without crossing code."""
    html_heading_starts = [
        match.start()
        for match in re.finditer(
            r"^[ \t]{0,3}<h[1-3](?=[ \t\r\n\f/>])(?:[^>\"']|\"[^\"]*\"|'[^']*')*>",
            structure,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
    ]
    offset = 0
    paragraph_start = None
    paragraph_container = None
    for raw_line in structure.splitlines(keepends=True):
        if html_heading_starts and offset <= html_heading_starts[0] < offset + len(raw_line):
            return html_heading_starts[0]
        if paragraph_start is not None:
            # Setext syntax takes precedence over interpreting a lone hyphen
            # as an empty list item. Retain the preceding paragraph's owning
            # containers when looking for its underline.
            candidate, continues = namespace["_strip_expected_fence_containers"](
                raw_line, paragraph_container
            )
            probe, columns = namespace["_indent_columns"](candidate)
            if (continues and columns <= 3
                    and re.fullmatch(r"(?:=+|-+)[ \t]*", candidate[probe:])):
                return paragraph_start
        logical, is_code, container = namespace["_parse_fence_container_prefixes"](
            raw_line.rstrip("\r\n")
        )
        stripped = logical.strip(" \t")
        if is_code or not stripped:
            paragraph_start = None
            paragraph_container = None
        elif re.match(r"^#{1,3}(?:[ \t]+|$)", stripped) or re.match(
            r"<h[1-3](?:[ \t>])", stripped, re.IGNORECASE
        ):
            return offset
        elif re.fullmatch(r"(?:=+|-+)[ \t]*", stripped):
            # A Setext underline belongs to the preceding paragraph in the
            # same container; a standalone thematic break is not a heading.
            if paragraph_start is not None and paragraph_container == container:
                return paragraph_start
            paragraph_start = None
            paragraph_container = None
        elif (namespace["THEMATIC_BREAK_PATTERN"].fullmatch(stripped)
              or re.match(r"^(?:#{4,6}(?:[ \t]+|$)|`{3,}|~{3,}|<)", stripped)):
            paragraph_start = None
            paragraph_container = None
        else:
            if paragraph_start is None or paragraph_container != container:
                paragraph_start = offset
            paragraph_container = container
        offset += len(raw_line)
    return len(structure)


def _visible_phase2_notes(changelog: str) -> str:
    namespace = runpy.run_path(str(POLICING_TEST))
    structure = namespace["_rendered_structure"](changelog)
    phase2_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE2_HEADING
    )
    phase1_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE1_HEADING
    )
    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"

    phase2_structure = structure[phase2_start:phase1_start]
    notes_start, notes_heading_end = namespace["_visible_markdown_heading_span"](
        phase2_structure, PHASE2_NOTES_HEADING
    )
    visible_phase2_structure = namespace["_mask_hidden_html_regions"](phase2_structure)

    tail = visible_phase2_structure[notes_heading_end:]
    notes_end = notes_heading_end + _next_notes_peer_heading(tail, namespace)

    absolute_notes_start = phase2_start + notes_start
    absolute_notes_end = phase2_start + notes_end
    return namespace["_visible_text"](
        changelog[absolute_notes_start:absolute_notes_end]
    )

def test_phase2_changelog_keeps_free_text_iaa_boundary():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert _visible_phase2_notes(changelog) == EXPECTED_VISIBLE_PHASE2_NOTES


def test_phase2_changelog_rejects_contradictory_iaa_continuation():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    bullet = f"- {FREE_TEXT_IAA_BOUNDARY}\n"
    contradictory = changelog.replace(
        bullet,
        f"- {FREE_TEXT_IAA_BOUNDARY} However, these interpretations are assigned "
        "an exact-string IAA score after all.\n",
        1,
    )
    assert _visible_phase2_notes(contradictory) != EXPECTED_VISIBLE_PHASE2_NOTES


def test_phase2_changelog_iaa_boundary_is_visible_and_section_scoped():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    bullet = f"- {FREE_TEXT_IAA_BOUNDARY}\n"
    assert bullet in changelog

    commented = changelog.replace(
        bullet,
        f"- <!-- {FREE_TEXT_IAA_BOUNDARY} -->\n",
        1,
    )
    assert FREE_TEXT_IAA_BOUNDARY not in _visible_phase2_notes(commented)

    moved = changelog.replace(bullet, "", 1).replace(
        PHASE1_HEADING,
        PHASE1_HEADING + f"\n\n- {FREE_TEXT_IAA_BOUNDARY}",
        1,
    )
    assert FREE_TEXT_IAA_BOUNDARY not in _visible_phase2_notes(moved)

def test_phase2_notes_stop_at_next_visible_peer_heading():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    bullet = f"- {FREE_TEXT_IAA_BOUNDARY}\n"
    assert bullet in changelog
    moved = changelog.replace(bullet, "", 1).replace(
        PHASE1_HEADING,
        "### Additional Phase 2 subsection\n\n"
        f"- {FREE_TEXT_IAA_BOUNDARY}\n\n"
        + PHASE1_HEADING,
        1,
    )
    assert FREE_TEXT_IAA_BOUNDARY not in _visible_phase2_notes(moved)



EXPECTED_VISIBLE_PHASE2_SECTION_SHA256 = "87ab007dbc8c8bb27d812438d69e9708907da64c00d89394fdb7e399877978ac"
EXPECTED_PHASE2_RECORDS_SHA256 = "a5eb75600941b1599a25c7d2620c9d8a5bdfa591c9f6eed105b07a48215aff9c"


def _raw_phase2_section(changelog: str) -> str:
    """Return the source slice for the complete rendered Phase 2 section."""
    namespace = runpy.run_path(str(POLICING_TEST))
    structure = namespace["_rendered_structure"](changelog)
    phase2_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE2_HEADING
    )
    phase1_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE1_HEADING
    )
    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"
    return changelog[phase2_start:phase1_start]


def _visible_phase2_section(changelog: str) -> str:
    """Return the complete browser-visible Phase 2 changelog section."""
    namespace = runpy.run_path(str(POLICING_TEST))
    return namespace["_visible_text"](_raw_phase2_section(changelog))


def _phase2_record_receipt(changelog: str) -> str:
    """Seal Phase 2 browser-visible records with their CommonMark hierarchy."""
    namespace = runpy.run_path(str(POLICING_TEST))
    records = namespace["_normalised_visible_workstream_records"](
        _raw_phase2_section(changelog)
    )
    return "\n".join(
        f"{signature}\x1f{line}" for signature, line in records
    )


def _phase2_records_sha256(changelog: str) -> str:
    return hashlib.sha256(_phase2_record_receipt(changelog).encode("utf-8")).hexdigest()


def _phase2_section_sha256(changelog: str) -> str:
    import hashlib

    return hashlib.sha256(_visible_phase2_section(changelog).encode("utf-8")).hexdigest()


def test_complete_phase2_changelog_section_is_pinned():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert _phase2_section_sha256(changelog) == EXPECTED_VISIBLE_PHASE2_SECTION_SHA256
    assert _phase2_records_sha256(changelog) == EXPECTED_PHASE2_RECORDS_SHA256


def test_phase2_section_receipt_preserves_list_hierarchy():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    bullet = f"- {FREE_TEXT_IAA_BOUNDARY}\n"
    assert bullet in changelog
    mutated = changelog.replace(bullet, f"  {bullet}", 1)
    assert _visible_phase2_notes(mutated) == EXPECTED_VISIBLE_PHASE2_NOTES
    assert _phase2_section_sha256(mutated) == EXPECTED_VISIBLE_PHASE2_SECTION_SHA256
    assert _phase2_records_sha256(mutated) != EXPECTED_PHASE2_RECORDS_SHA256


def test_phase2_section_seal_catches_sibling_empirical_claims():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert _visible_phase2_notes(changelog) == EXPECTED_VISIBLE_PHASE2_NOTES
    claims = (
        "Three human annotators completed the Phase 2 pilot.",
        "The completed Phase 2 study received ethical-review approval.",
        "Three human annotators achieved 100% exact-string IAA.",
    )
    for claim in claims:
        sibling = (
            "### Fabricated Phase 2 results\n\n"
            f"- {claim}\n\n"
            + PHASE2_NOTES_HEADING
        )
        mutated = changelog.replace(PHASE2_NOTES_HEADING, sibling, 1)
        assert mutated != changelog
        # The existing Notes-only receipt remains unchanged, which is the gap
        # this complete-section seal is intended to close.
        assert _visible_phase2_notes(mutated) == EXPECTED_VISIBLE_PHASE2_NOTES
        assert _phase2_section_sha256(mutated) != EXPECTED_VISIBLE_PHASE2_SECTION_SHA256
