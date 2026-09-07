"""Regressions for the final rendered-governance review round on PR #4."""

from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
POLICING = runpy.run_path(str(ROOT / "tests" / "test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(ROOT / "tests" / "test_research_reference_registry.py"))


def _mutate_workstream(old: str, new: str) -> str:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    start = roadmap.index(POLICING["WORKSTREAM_HEADING"])
    end = roadmap.index(POLICING["WORKSTREAM_END_HEADING"], start)
    section = roadmap[start:end]
    assert old in section
    section = section.replace(old, new, 1)
    return roadmap[:start] + section + roadmap[end:]


def test_entity_decoded_emphasis_punctuation_remains_literal() -> None:
    mutated = _mutate_workstream("not legal advice", "not&#95; legal advice")
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_generated_q_markup_is_rejected_on_shared_and_registry_surfaces() -> None:
    mutated_roadmap = _mutate_workstream(
        "not legal advice", "<q>not legal advice</q>"
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    invariant = "RESEARCH REFERENCE != REDISTRIBUTABLE DATA"
    assert invariant in corpus
    mutated_corpus = corpus.replace(invariant, f"<q>{invariant}</q>", 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)


def test_markdown_images_are_rejected_before_registry_integrity_reduction() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    boundary = REGISTRY["SOURCE_USE_HEADING"]
    index = corpus.index(boundary)
    image = "![Current sources may be skipped](https://example.com/x.png)\n\n"
    mutated = corpus[:index] + image + corpus[index:]
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


# Human receipt: the repair runner verified this regression set before self-cleanup.
