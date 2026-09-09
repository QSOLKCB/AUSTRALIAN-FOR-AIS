"""Regressions for the PR #4 clean-head audit blockers."""

from collections import Counter
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLICING = runpy.run_path(str(ROOT / "tests/test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(ROOT / "tests/test_research_reference_registry.py"))
CORPUS = ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md"


def test_clean_line_dialog_clause_fragment_is_rejected() -> None:
    fragment = (
        "Availability through ABC iview is\n"
        "<dialog open>\n"
        "not\n"
        "</dialog>\n"
        "permission to redistribute content."
    )
    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    original = "Availability through ABC iview is not permission to redistribute content."
    assert original in corpus
    mutated = corpus.replace(original, fragment, 1)
    with pytest.raises(AssertionError, match="dialog block-container HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_structural_section_dialog_wrapper_remains_supported() -> None:
    fragment = "## Governed section\n\n<dialog open>\nCanonical governed prose.\n</dialog>\n\n## Next section\n"
    assert "dialog-inline-block" not in POLICING["_governed_surface_html_violations"](fragment)


def test_single_source_accepts_equivalent_inline_link() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    original = f"**Registered source:** {url}"
    replacement = f"**Registered source:** [{url}]({url})"
    assert original in corpus
    REGISTRY["_validate_registry_corpus"](corpus.replace(original, replacement, 1))


def test_single_source_field_binding_is_format_invariant() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = REGISTRY["_registered_sections"](corpus)[entry]
    original_bindings: list[tuple[str, str]] = []
    REGISTRY["_require_registered_source_link"](
        entry, section, reference_scope=corpus, source_bindings=original_bindings
    )
    replacement = f"**Registered source:** [{url}]({url})"
    mutated = corpus.replace(f"**Registered source:** {url}", replacement, 1)
    linked_section = REGISTRY["_registered_sections"](mutated)[entry]
    linked_bindings: list[tuple[str, str]] = []
    REGISTRY["_require_registered_source_link"](
        entry, linked_section, reference_scope=mutated, source_bindings=linked_bindings
    )
    expected = Counter({(url, url): 1})
    assert Counter(original_bindings) == Counter(linked_bindings) == expected
