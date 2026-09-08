"""Regressions for the September 8 Astra review of PR #4."""

from pathlib import Path
import runpy

import pytest


TESTS = Path(__file__).parent
ROOT = TESTS.parent
POLICING = runpy.run_path(str(TESTS / "test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(TESTS / "test_research_reference_registry.py"))


def test_visible_pre_content_changes_policing_integrity() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    validate = POLICING["_validate_policing_workstream"]
    validate(roadmap)

    boundary = POLICING["WORKSTREAM_END"]
    assert boundary in roadmap
    changed = roadmap.replace(
        boundary,
        "\n<pre>\nCurrent sources may be skipped.\n</pre>\n" + boundary,
        1,
    )
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("marker", ["*", "_"])
def test_whitespace_delimited_literal_marker_changes_policing_integrity(
    marker: str,
) -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    changed = roadmap.replace(
        "not legal advice",
        f"not {marker} legal advice",
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](changed)


def test_zero_sized_marquee_cannot_satisfy_policing_safeguard() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    phrase = "source-gated research proposal"
    changed = roadmap.replace(
        phrase,
        f'<marquee width="0" height="0">{phrase}</marquee>',
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](changed)


def test_unregistered_https_link_cannot_wrap_policing_safeguard() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    phrase = "source-gated research proposal"
    changed = roadmap.replace(
        phrase,
        f'[{phrase}](https://example.com/not-legal-advice)',
        1,
    )
    with pytest.raises(AssertionError, match="hyperlink"):
        POLICING["_validate_policing_workstream"](changed)


def test_anchor_ping_is_rejected_on_registered_source() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(
        encoding="utf-8"
    )
    source = "https://iview.abc.net.au/show/black-comedy"
    changed = corpus.replace(
        source,
        f'<a href="{source}" ping="https://example.com/track">{source}</a>',
        1,
    )
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](changed)


def test_registry_uses_browser_paragraph_end_for_center() -> None:
    rendered = REGISTRY["_visible_html_text"](
        '<p hidden>masked<center>Current sources may be skipped.</center></p>'
    )
    assert rendered == "Current sources may be skipped."


def test_visible_center_after_hidden_paragraph_changes_entry_integrity() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(
        encoding="utf-8"
    )
    marker = "Candidate research mappings:"
    assert marker in corpus
    changed = corpus.replace(
        marker,
        '<p hidden>masked<center>Current sources may be skipped.</center></p>\n\n'
        + marker,
        1,
    )
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](changed)
