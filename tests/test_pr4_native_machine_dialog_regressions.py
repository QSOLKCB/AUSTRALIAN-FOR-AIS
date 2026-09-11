"""Regressions for native machine values and dialog prose containers."""

from pathlib import Path
import runpy
import pytest

ROOT = Path(__file__).parent.parent
POLICING = runpy.run_path(str(ROOT / "tests" / "test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(ROOT / "tests" / "test_research_reference_registry.py"))
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"


def test_native_data_value_is_machine_metadata() -> None:
    fragment = '<data value="CC0">The film remains copyrighted.</data>'
    assert "machine-metadata" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    mutated = corpus.replace("The film remains copyrighted.", fragment, 1)
    with pytest.raises(AssertionError, match="machine-readable Microdata/RDFa metadata"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_open_dialog_inside_governed_prose_is_rejected() -> None:
    fragment = "Availability through ABC iview is <dialog open>not</dialog> permission to redistribute content."
    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    original = "Availability through ABC iview is not permission to redistribute content."
    mutated = corpus.replace(original, fragment, 1)
    with pytest.raises(AssertionError, match="dialog block-container HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_closed_dialog_keeps_existing_hidden_semantics() -> None:
    fragment = "<dialog>Canonical governed prose.</dialog>"
    assert "dialog-inline-block" not in POLICING["_governed_surface_html_violations"](fragment)


def test_whole_section_open_dialog_wrapper_remains_supported() -> None:
    fragment = "<dialog open>\nCanonical governed prose.\n</dialog>\n"
    violations = POLICING["_governed_surface_html_violations"](fragment)
    assert "dialog-inline-block" not in violations


def test_multiline_open_dialog_inside_governed_prose_is_rejected() -> None:
    fragment = (
        "Availability through ABC iview is <dialog\n"
        " open>not</dialog> permission to redistribute content."
    )
    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    original = "Availability through ABC iview is not permission to redistribute content."
    mutated = corpus.replace(original, fragment, 1)
    with pytest.raises(AssertionError, match="dialog block-container HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_multiline_whole_section_open_dialog_wrapper_remains_supported() -> None:
    fragment = "<dialog\n open>\nCanonical governed prose.\n</dialog>\n"
    violations = POLICING["_governed_surface_html_violations"](fragment)
    assert "dialog-inline-block" not in violations


def test_multiline_open_dialog_with_quoted_gt_is_rejected() -> None:
    fragment = (
        'Availability through ABC iview is <dialog data-x="a>b"\n'
        ' open>not</dialog> permission to redistribute content.'
    )
    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    original = "Availability through ABC iview is not permission to redistribute content."
    mutated = corpus.replace(original, fragment, 1)
    with pytest.raises(AssertionError, match="dialog block-container HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_multiline_dialog_wrapper_with_quoted_gt_remains_supported() -> None:
    fragment = '<dialog data-x="a>b"\n open>\nCanonical governed prose.\n</dialog>\n'
    violations = POLICING["_governed_surface_html_violations"](fragment)
    assert "dialog-inline-block" not in violations


def test_aria_disabled_ancestor_is_rejected_on_governed_source() -> None:
    fragment = '<span aria-disabled="true">https://iview.abc.net.au/show/black-comedy</span>'
    assert "accessibility-disabled" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    mutated = corpus.replace(url, fragment, 1)
    with pytest.raises(AssertionError, match="aria-disabled"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_ruby_annotation_cannot_relocate_governed_qualifier() -> None:
    fragment = (
        "Availability through ABC iview is "
        "<ruby>not<rt> permission</rt></ruby> to redistribute content."
    )
    assert "non-rendering-container" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    original = "Availability through ABC iview is not permission to redistribute content."
    mutated = corpus.replace(original, fragment, 1)
    with pytest.raises(AssertionError, match="non-rendering"):
        REGISTRY["_validate_registry_corpus"](mutated)
