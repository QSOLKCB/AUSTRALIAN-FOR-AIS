"""Exact regressions for the latest PR #4 governance review findings."""

from __future__ import annotations

from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"
REGISTRY_NS = runpy.run_path(str(Path(__file__).with_name("test_research_reference_registry.py")))
RECEIPT_NS = runpy.run_path(str(Path(__file__).with_name("test_policing_contract_receipt.py")))


@pytest.mark.parametrize("tag", ["div", "p", "section", "summary"])
def test_raw_block_container_cannot_detach_registry_qualifier(tag: str) -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    canonical = "Availability through ABC iview is not permission to redistribute content."
    mutated = (
        "Availability through ABC iview is "
        f"<{tag}>not</{tag}> permission to redistribute content."
    )
    assert canonical in corpus
    with pytest.raises(AssertionError):
        REGISTRY_NS["_validate_registry_corpus"](corpus.replace(canonical, mutated, 1))


@pytest.mark.parametrize("position", ["before-title", "after-title"])
def test_registry_prefix_allows_only_canonical_title(position: str) -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    claim = "All registered sources may be copied freely into benchmark data."
    if position == "before-title":
        mutated = claim + "\n\n" + corpus
    else:
        mutated = corpus.replace(
            "# Research Reference Corpus\n\n",
            "# Research Reference Corpus\n\n" + claim + "\n\n",
            1,
        )
    with pytest.raises(AssertionError):
        REGISTRY_NS["_validate_registry_corpus"](mutated)


def test_single_nobr_cannot_wrap_registry_rights_boundary() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    canonical = "Availability through ABC iview is not permission to redistribute content."
    assert canonical in corpus
    mutated = corpus.replace(canonical, f"<nobr>{canonical}</nobr>", 1)
    with pytest.raises(AssertionError):
        REGISTRY_NS["_validate_registry_corpus"](mutated)


def test_policing_methodology_receipt_preserves_root_paragraph_hierarchy() -> None:
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    canonical = "Legal and procedural review is mandatory for high-stakes use."
    assert "\n" + canonical in methodology
    mutated = methodology.replace("\n" + canonical, "\n  " + canonical, 1)
    with pytest.raises(AssertionError):
        RECEIPT_NS["_assert_canonical_policing_integrity"](mutated)
