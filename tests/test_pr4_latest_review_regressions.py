"""Exact regressions for the 2026-09-09 PR #4 Codex review batch."""

from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
REGISTRY = runpy.run_path(str(Path(__file__).with_name("test_research_reference_registry.py")))
WORKSTREAM_G = runpy.run_path(str(Path(__file__).with_name("test_workstream_g_integrity.py")))
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"
ROADMAP = ROOT / "ROADMAP.md"


def test_corpus_wide_gate_rejects_rendered_break_in_status() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    mutated = corpus.replace(
        "not a benchmark dataset",
        "not <hr>a benchmark dataset",
        1,
    )
    with pytest.raises(AssertionError, match="raw HTML thematic break"):
        REGISTRY["_validate_registry_corpus"](mutated)


@pytest.mark.parametrize("kind", ("markdown", "html"))
def test_workstream_g_binds_anti_stereotype_disclaimer_links(kind: str) -> None:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = WORKSTREAM_G["NONFACTUAL_BOUNDARY"]
    destination = "https://example.com/factual-claim"
    if kind == "markdown":
        replacement = f"[{clause}]({destination})"
    else:
        replacement = f'<a href="{destination}">{clause}</a>'
    mutated = roadmap.replace(clause, replacement, 1)
    with pytest.raises(AssertionError):
        WORKSTREAM_G["_assert_workstream_g_integrity"](mutated)


def test_registration_contract_is_link_free() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    phrase = "the rights and provenance boundary for repository use"
    mutated = corpus.replace(
        phrase,
        f"[{phrase}](https://creativecommons.org/publicdomain/zero/1.0/)",
        1,
    )
    with pytest.raises(AssertionError, match="registration contract must remain link-free"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_registration_contract_preserves_list_hierarchy() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    bullet = "- the rights and provenance boundary for repository use;"
    assert bullet in corpus
    mutated = corpus.replace(bullet, "  " + bullet, 1)
    with pytest.raises(AssertionError, match="record hierarchy"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_governed_anchor_rel_semantics_are_rejected() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    source = f"**Registered source:** {url}"
    replacement = (
        f'**Registered source:** <a href="{url}" rel="author">{url}</a>'
    )
    mutated = corpus.replace(source, replacement, 1)
    with pytest.raises(AssertionError, match="machine-readable"):
        REGISTRY["_validate_registry_corpus"](mutated)
