"""End-to-end regressions for the latest PR #4 merge blockers."""

from pathlib import Path
import runpy
import pytest

ROOT = Path(__file__).parent.parent
POLICING = runpy.run_path(str(ROOT / "tests" / "test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(ROOT / "tests" / "test_research_reference_registry.py"))
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"
ROADMAP = ROOT / "ROADMAP.md"


def test_raw_block_violation_is_consumed_end_to_end() -> None:
    mutated = ROADMAP.read_text(encoding="utf-8").replace(
        "source-gated research proposal", "source-gated <div>research</div> proposal", 1
    )
    assert "raw-block" in POLICING["_governed_surface_html_violations"](
        "source-gated <div>research</div> proposal"
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_raw_list_violation_is_consumed_end_to_end() -> None:
    mutated = ROADMAP.read_text(encoding="utf-8").replace(
        "source-gated research proposal", "source-gated <ul><li>research</li></ul> proposal", 1
    )
    assert "raw-list" in POLICING["_governed_surface_html_violations"](
        "source-gated <ul><li>research</li></ul> proposal"
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_open_dialog_closing_boundary_cannot_share_governed_prose() -> None:
    original = "Availability through ABC iview is not permission to redistribute content."
    fragment = (
        "Availability through ABC iview is\n"
        "<dialog open>\n"
        "not</dialog> permission to redistribute content."
    )
    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)
    mutated = CORPUS.read_text(encoding="utf-8").replace(original, fragment, 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_clean_multiline_open_dialog_wrapper_still_supported() -> None:
    fragment = "<dialog open>\nCanonical governed prose.\n</dialog>\n"
    assert "dialog-inline-block" not in POLICING["_governed_surface_html_violations"](fragment)


def test_aria_owns_reorders_no_governed_accessibility_tree() -> None:
    original = "Availability through ABC iview is not permission to redistribute content."
    fragment = (
        'Availability through ABC iview is <span id="negation">not</span> '
        'permission to redistribute content.<span aria-owns="negation"></span>'
    )
    assert "accessibility-ownership" in POLICING["_governed_surface_html_violations"](fragment)
    mutated = CORPUS.read_text(encoding="utf-8").replace(original, fragment, 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)
