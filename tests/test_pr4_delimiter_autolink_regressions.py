from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLICING = runpy.run_path(str(ROOT / "tests/test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(ROOT / "tests/test_research_reference_registry.py"))


def test_shared_surplus_delimiter_characters_remain_visible():
    assert POLICING["_visible_text"]("***not legal advice**") == "*not legal advice"
    assert POLICING["_visible_text"]("**not legal advice***") == "not legal advice*"
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated = roadmap.replace("not legal advice", "***not legal advice**", 1)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_registry_unmatched_delimiter_remains_visible_and_breaks_receipt():
    phrase = "The article is registered as scholarship"
    assert REGISTRY["_visible_inline_text"]("*" + phrase) == "*" + phrase
    corpus = (ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    mutated = corpus.replace(phrase, "*" + phrase, 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_registry_surplus_delimiter_characters_remain_visible():
    phrase = "The article is registered as scholarship"
    assert REGISTRY["_visible_inline_text"]("***" + phrase + "**") == "*" + phrase
    assert REGISTRY["_visible_inline_text"]("**" + phrase + "***") == phrase + "*"
    corpus = (ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    mutated = corpus.replace(phrase, "***" + phrase + "**", 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_commonmark_email_autolinks_are_visible_governed_content():
    email_markup = "<current.sources.may.be.skipped@example.com>"
    visible_email = "current.sources.may.be.skipped@example.com"
    assert POLICING["_visible_text"](email_markup) == visible_email
    assert REGISTRY["_visible_inline_text"](email_markup) == visible_email

    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated_roadmap = roadmap.replace(
        "not legal advice.",
        f"not legal advice. {email_markup}",
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    mutated_corpus = corpus.replace(
        "The article is registered as scholarship",
        f"The article is registered as scholarship {email_markup}",
        1,
    )
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)


def test_registered_source_email_autolink_is_not_https_provenance():
    with pytest.raises(AssertionError, match="email autolinks"):
        REGISTRY["_usable_https_source_bindings"](
            "**Registered source:** <source@example.com>"
        )


def test_registry_raw_html_literal_asterisk_stays_literal():
    assert REGISTRY["_visible_inline_text"]("The art<span>*</span>icle") == "The art*icle"
