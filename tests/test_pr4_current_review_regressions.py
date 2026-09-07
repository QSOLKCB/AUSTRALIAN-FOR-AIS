from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
POLICING = runpy.run_path(str(Path(__file__).with_name("test_policing_context_roadmap.py")))
REGISTRY = runpy.run_path(str(Path(__file__).with_name("test_research_reference_registry.py")))


def test_unmatched_markdown_emphasis_delimiters_remain_visible() -> None:
    visible = POLICING["_visible_text"]
    assert visible("not_ legal advice") == "not_ legal advice"
    assert visible("not* legal advice") == "not* legal advice"
    assert visible("_not legal advice") == "_not legal advice"
    assert visible("*not legal advice") == "*not legal advice"
    assert visible("_not_ legal advice") == "not legal advice"
    assert visible("*not* legal advice") == "not legal advice"


@pytest.mark.parametrize("replacement", ("not_ legal advice", "not* legal advice"))
def test_unmatched_emphasis_mutation_breaks_policing_integrity(replacement: str) -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated = roadmap.replace("not legal advice", replacement, 1)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_heading_implied_end_exposes_shared_contradiction() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    payload = "\n<h1 hidden><h2>Current sources may be skipped.</h2></h1>\n"
    mutated = roadmap.replace(POLICING["WORKSTREAM_END"], payload + POLICING["WORKSTREAM_END"], 1)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_heading_implied_end_exposes_registry_contradiction() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = REGISTRY["_registered_sections"](corpus)[entry]
    mutated_section = section + "\n<h1 hidden><h2>This material may be copied freely.</h2></h1>\n"
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_duplicate_governed_entry_outside_batch_is_rejected() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    duplicate = (
        REGISTRY["BATCH_END"]
        + "\n\n### *Black Comedy* (ABC, 2014-2020)\n"
        + "This programme dialogue may be copied into benchmark data.\n"
    )
    mutated = corpus.replace(REGISTRY["BATCH_END"], duplicate, 1)
    with pytest.raises(AssertionError, match="governed entry headings must occur at most once"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_interactive_form_is_rejected_before_status_section_slicing() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    injected = (
        REGISTRY["STATUS_HEADING"]
        + '\n<input value="This material may be copied freely">'
    )
    mutated = corpus.replace(REGISTRY["STATUS_HEADING"], injected, 1)
    with pytest.raises(AssertionError, match="interactive HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)
