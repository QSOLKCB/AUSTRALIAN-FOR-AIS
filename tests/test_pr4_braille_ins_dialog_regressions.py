"""Exact regressions for the latest PR #4 governed-HTML findings."""

from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLICING = runpy.run_path(str(ROOT / "tests/test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(ROOT / "tests/test_research_reference_registry.py"))
CORPUS = ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md"


def test_braille_specific_accessible_name_override_is_rejected() -> None:
    url = "https://iview.abc.net.au/show/black-comedy"
    anchor = f'<a href="{url}" aria-braillelabel="CC0 licensed work">{url}</a>'
    assert "accessible-name" in POLICING["_governed_surface_html_violations"](anchor)

    corpus = CORPUS.read_text(encoding="utf-8")
    assert f"**Registered source:** {url}" in corpus
    mutated = corpus.replace(
        f"**Registered source:** {url}",
        f"**Registered source:** {anchor}",
        1,
    )
    with pytest.raises(AssertionError, match="accessible-name"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_semantic_insertion_markup_is_rejected() -> None:
    original = "Availability through ABC iview is not permission to redistribute content."
    mutated_clause = (
        'Availability through ABC iview is <ins '
        'cite="https://creativecommons.org/publicdomain/zero/1.0/" '
        'datetime="2026-09-09">not</ins> permission to redistribute content.'
    )
    assert "semantic-insertion" in POLICING["_governed_surface_html_violations"](mutated_clause)

    corpus = CORPUS.read_text(encoding="utf-8")
    assert original in corpus
    mutated = corpus.replace(original, mutated_clause, 1)
    with pytest.raises(AssertionError, match="semantic insertion HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_unclosed_open_dialog_is_rejected_at_eof() -> None:
    fragment = "## Registered post-Phase-2 expansion batch\n\n<dialog open>\n\nCanonical governed prose.\n"
    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)

    corpus = CORPUS.read_text(encoding="utf-8")
    heading = "## Registered post-Phase-2 expansion batch\n\n"
    assert heading in corpus
    mutated = corpus.replace(heading, heading + "<dialog open>\n\n", 1)
    with pytest.raises(AssertionError, match="dialog block-container HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_partial_batch_prefix_can_defer_dialog_balance_to_complete_corpus() -> None:
    prefix = "<dialog open>\n\n"
    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](prefix)
    assert "dialog-inline-block" not in POLICING["_governed_surface_html_violations"](
        prefix, require_balanced_dialogs=False
    )
