"""Exact regressions for the latest Codex findings on PR #4."""

from __future__ import annotations

from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).resolve().parent.parent
REGISTRY = runpy.run_path(str(ROOT / "tests" / "test_research_reference_registry.py"))
CORPUS = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")

BLACK_COMEDY_RIGHTS = (
    "Availability through ABC iview is not permission to redistribute content."
)


def test_registry_receipt_rejects_space_markdown_hard_line_break() -> None:
    mutated = CORPUS.replace(
        BLACK_COMEDY_RIGHTS,
        "Availability through ABC iview is  \nnot permission to redistribute content.",
        1,
    )
    assert mutated != CORPUS
    with pytest.raises(AssertionError, match="hard line breaks"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_registry_backslash_hard_break_already_changes_receipt() -> None:
    mutated = CORPUS.replace(
        BLACK_COMEDY_RIGHTS,
        "Availability through ABC iview is\\\nnot permission to redistribute content.",
        1,
    )
    assert mutated != CORPUS
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_registry_rejects_nested_small_presentation() -> None:
    wrapped = "<small>" * 12 + BLACK_COMEDY_RIGHTS + "</small>" * 12
    mutated = CORPUS.replace(BLACK_COMEDY_RIGHTS, wrapped, 1)
    assert mutated != CORPUS
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


@pytest.mark.parametrize("attribute", ['lang="ja"', 'xml:lang="ja"'])
def test_registry_rejects_language_overrides(attribute: str) -> None:
    wrapped = f"<span {attribute}>{BLACK_COMEDY_RIGHTS}</span>"
    mutated = CORPUS.replace(BLACK_COMEDY_RIGHTS, wrapped, 1)
    assert mutated != CORPUS
    with pytest.raises(AssertionError, match="language overrides"):
        REGISTRY["_validate_registry_corpus"](mutated)
