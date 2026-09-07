"""Regressions for governed accessibility-tree and anchor semantics."""

from pathlib import Path
import runpy

import pytest

TESTS = Path(__file__).parent
ROOT = TESTS.parent
POLICING = runpy.run_path(str(TESTS / "test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(TESTS / "test_research_reference_registry.py"))

@pytest.mark.parametrize("markup", [
    '<span role="img" aria-hidden="true">source-gated research proposal</span>',
    '<a href="https://example.org/source" aria-hidden="true">https://example.org/source</a>',
])
def test_aria_hidden_is_rejected_by_shared_and_registry_preflights(markup: str) -> None:
    violations = POLICING["_governed_surface_html_violations"](markup)
    assert "accessibility-hidden" in violations
    with pytest.raises(AssertionError, match="aria-hidden"):
        POLICING["_assert_supported_governed_html"](violations)
    found = REGISTRY["_forbidden_governed_html_constructs"](markup)
    assert "accessibility-hidden" in found
    with pytest.raises(AssertionError, match="aria-hidden"):
        REGISTRY["_assert_no_active_document_html"](found)

def test_aria_hidden_cannot_hide_policing_safeguard() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated = roadmap.replace("source-gated research proposal", '<span aria-hidden="true">source-gated research proposal</span>', 1)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)

def test_aria_hidden_cannot_hide_registered_source() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    source = "https://iview.abc.net.au/show/black-comedy"
    mutated = corpus.replace(source, f'<a href="{source}" aria-hidden="true">{source}</a>', 1)
    with pytest.raises(AssertionError, match="aria-hidden"):
        REGISTRY["_validate_registry_corpus"](mutated)

@pytest.mark.parametrize("markup", [
    '<a hidden>masked<a>Current sources may be skipped.</a></a>',
    '<a hidden><span>masked</span><a>Current sources may be skipped.</a></a>',
])
def test_nested_anchors_are_rejected_by_shared_and_registry_preflights(markup: str) -> None:
    violations = POLICING["_governed_surface_html_violations"](markup)
    assert "nested-anchor" in violations
    with pytest.raises(AssertionError, match="nested anchor"):
        POLICING["_assert_supported_governed_html"](violations)
    found = REGISTRY["_forbidden_governed_html_constructs"](markup)
    assert "nested-anchor" in found
    with pytest.raises(AssertionError, match="nested anchor"):
        REGISTRY["_assert_no_active_document_html"](found)

def test_nested_anchor_cannot_escape_hidden_policing_ancestor() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    marker = "\n---\n\n## Phase 3"
    mutated = roadmap.replace(marker, '\n<a hidden>masked<a>Current sources may be skipped.</a></a>\n' + marker, 1)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)

def test_nested_anchor_cannot_escape_hidden_registry_ancestor() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    marker = "## Priority A: adversarial pragmatics"
    mutated = corpus.replace(marker, '<a hidden>masked<a>This source may be copied freely.</a></a>\n\n' + marker, 1)
    with pytest.raises(AssertionError, match="nested anchor"):
        REGISTRY["_validate_registry_corpus"](mutated)
