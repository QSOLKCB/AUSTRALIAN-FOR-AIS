"""Integrity receipt for Roadmap Workstream G trans-Tasman safeguards."""

from pathlib import Path
import hashlib
import runpy

import pytest


ROOT = Path(__file__).parent.parent
ROADMAP = ROOT / "ROADMAP.md"
POLICING = runpy.run_path(str(Path(__file__).with_name("test_policing_context_roadmap.py")))
WORKSTREAM_G_HEADING = '### G. Trans-Tasman relational pragmatics and lexical context'
WORKSTREAM_H_HEADING = '### H. Slang density, register compression, and operational intelligibility'
WORKSTREAM_G_VISIBLE_SHA256 = '3af2e5d1e987d550d492d5231f67a8c82538bd97ce94d01ef646ba747ee88135'
WORKSTREAM_G_RECORDS_SHA256 = 'b1ef6be68642ac60b4ef92eef96e135cd9a0f7a197c0de1c6d865384c1edb11e'
NONFACTUAL_BOUNDARY = (
    "The research lead is not a factual statement about New Zealanders and is not evidence "
    "that Australians generally hold the underlying belief."
)
SAFE_ABSTRACTION_BOUNDARY = (
    "Redistributable benchmark items should model the relational and mention-versus-use "
    "structure with abstract placeholders or non-identity-targeted synthetic content rather "
    "than manufacturing new nationality stereotypes."
)


def _workstream_g_raw(text: str) -> str:
    POLICING["_assert_supported_governed_html"](
        POLICING["_governed_surface_html_violations"](text)
    )
    structure = POLICING["_rendered_structure"](text)
    start, _ = POLICING["_visible_markdown_heading_span"](structure, WORKSTREAM_G_HEADING)
    end, _ = POLICING["_visible_markdown_heading_span"](structure, WORKSTREAM_H_HEADING)
    assert start < end, "rendered Workstream G boundary is invalid"
    return text[start:end]


def _assert_workstream_g_integrity(text: str) -> str:
    raw = _workstream_g_raw(text)
    visible = " ".join(POLICING["_visible_text"](raw).split())
    actual_visible_hash = hashlib.sha256(visible.encode("utf-8")).hexdigest()
    assert actual_visible_hash == WORKSTREAM_G_VISIBLE_SHA256, (
        "browser-visible Workstream G changed: expected hash "
        f"{WORKSTREAM_G_VISIBLE_SHA256!r}, got {actual_visible_hash!r}"
    )
    records = POLICING["_normalised_visible_workstream_records"](raw)
    receipt = "\n".join(f"{signature}\x1f{line}" for signature, line in records)
    actual_records_hash = hashlib.sha256(receipt.encode("utf-8")).hexdigest()
    assert actual_records_hash == WORKSTREAM_G_RECORDS_SHA256, (
        "Workstream G record hierarchy changed: expected hash "
        f"{WORKSTREAM_G_RECORDS_SHA256!r}, got {actual_records_hash!r}"
    )
    assert NONFACTUAL_BOUNDARY in visible
    assert SAFE_ABSTRACTION_BOUNDARY in visible
    return visible


def test_workstream_g_stereotype_boundary_is_pinned() -> None:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    _assert_workstream_g_integrity(roadmap)
    reversed_claim = (
        "The research lead is a factual statement about New Zealanders and is evidence "
        "that Australians generally hold the underlying belief."
    )
    mutated = roadmap.replace(NONFACTUAL_BOUNDARY, reversed_claim, 1)
    with pytest.raises(AssertionError):
        _assert_workstream_g_integrity(mutated)


def test_workstream_g_safe_abstraction_boundary_is_pinned() -> None:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    mutated = roadmap.replace(
        SAFE_ABSTRACTION_BOUNDARY,
        "Redistributable benchmark items may reproduce nationality stereotypes directly.",
        1,
    )
    with pytest.raises(AssertionError):
        _assert_workstream_g_integrity(mutated)
