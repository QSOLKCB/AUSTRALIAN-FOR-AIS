"""Regression evidence for PR 4's outstanding rendered-governance findings."""

from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def validators():
    return {
        name: runpy.run_path(str(ROOT / "tests" / filename))
        for name, filename in {
            "registry": "test_research_reference_registry.py",
            "policing": "test_policing_context_roadmap.py",
            "workstream_h": "test_workstream_h_methodology.py",
            "notes": "test_phase2_review_followup.py",
        }.items()
    }


@pytest.mark.parametrize("punctuation", ["_", "*", "__", "**"])
def test_shared_literal_html_punctuation_is_not_markup(validators, punctuation):
    p = validators["policing"]
    assert p["_visible_text"](f"research<span>{punctuation}</span> proposal") == (
        f"research{punctuation} proposal"
    )
    assert p["_visible_text"]("**research** _proposal_") == "research proposal"
    assert p["_visible_text"]("<strong>research</strong> proposal") == "research proposal"


def test_shared_punctuation_mutation_invalidates_workstream(validators):
    p = validators["policing"]
    roadmap = p["ROADMAP"].read_text(encoding="utf-8")
    original = "source-gated research proposal"
    assert original in roadmap
    changed = roadmap.replace(original, "source-gated research<span>_</span> proposal", 1)
    with pytest.raises(AssertionError):
        p["_validate_policing_workstream"](changed)


@pytest.mark.parametrize("attribute", ["popover", 'popover="auto"', 'popover="manual"', 'popover="hint"'])
def test_shared_popover_cannot_supply_visible_safeguards(validators, attribute):
    p = validators["policing"]
    roadmap = p["ROADMAP"].read_text(encoding="utf-8")
    clause = p["REQUIRED_CLAUSES"][3]
    assert clause in roadmap
    changed = roadmap.replace(clause, f"<span {attribute}>{clause}</span>", 1)
    with pytest.raises(AssertionError):
        p["_validate_policing_workstream"](changed)


@pytest.mark.parametrize("wrapper", [
    "<!-- {link} -->",
    "`{link}`",
    "\n\n```\n{link}\n```\n\n",
    '<span hidden>{link}</span>',
    '<span title="{link}"></span>',
    '<span inert>{link}</span>',
])
def test_workstream_h_citation_must_be_live(validators, wrapper):
    h = validators["workstream_h"]
    roadmap = h["ROADMAP"].read_text(encoding="utf-8")
    label, destination = next(
        pair for pair in h["WORKSTREAM_H_CITATION_LINKS"]
        if pair[0] == "Australian slang dictionary"
    )
    link = f"[{label}]({destination})"
    assert link in roadmap
    changed = roadmap.replace(link, label + wrapper.format(link=link), 1)
    with pytest.raises(AssertionError):
        h["_assert_workstream_h_integrity"](changed)


def test_workstream_h_keeps_real_citation_with_comment_decoy(validators):
    h = validators["workstream_h"]
    roadmap = h["ROADMAP"].read_text(encoding="utf-8")
    changed = roadmap.replace(
        h["WORKSTREAM_I_HEADING"],
        '<!-- [unadopted decoy](https://example.org/) -->\n\n' + h["WORKSTREAM_I_HEADING"],
        1,
    )
    h["_assert_workstream_h_integrity"](changed)


@pytest.mark.parametrize("heading", [
    "Additional Phase 2 subsection\n---",
    "Additional Phase 2 subsection\n===",
    "Additional\nPhase 2 subsection\n-",
    "   Additional Phase 2 subsection\n   ===  ",
    "<h2>Additional Phase 2 subsection</h2>",
])
def test_notes_stop_at_rendered_setext_or_html_heading(validators, heading):
    n = validators["notes"]
    changelog = n["CHANGELOG"].read_text(encoding="utf-8")
    bullet = f'- {n["FREE_TEXT_IAA_BOUNDARY"]}\n'
    assert bullet in changelog
    changed = changelog.replace(bullet, "", 1).replace(
        n["PHASE1_HEADING"],
        heading + "\n\n" + bullet + "\n" + n["PHASE1_HEADING"],
        1,
    )
    assert n["FREE_TEXT_IAA_BOUNDARY"] not in n["_visible_phase2_notes"](changed)


@pytest.mark.parametrize("decoy", [
    "```\nNot a heading\n---\n```",
    "<!-- Not a heading\n--- -->",
    "---",
])
def test_notes_ignore_inert_heading_decoys(validators, decoy):
    n = validators["notes"]
    changelog = n["CHANGELOG"].read_text(encoding="utf-8")
    bullet = f'- {n["FREE_TEXT_IAA_BOUNDARY"]}\n'
    changed = changelog.replace(bullet, "\n" + decoy + "\n\n" + bullet, 1)
    assert n["FREE_TEXT_IAA_BOUNDARY"] in n["_visible_phase2_notes"](changed)


@pytest.mark.parametrize("mode", ["open", "closed"])
def test_declarative_shadow_root_cannot_escape_entry_seal(validators, mode):
    r = validators["registry"]
    corpus = r["CORPUS"].read_text(encoding="utf-8")
    entry = next(iter(r["ENTRY_CONTRACTS"]))
    section = r["_registered_sections"](corpus)[entry]
    payload = f'<div><template shadowrootmode="{mode}">Source controls may be skipped.</template></div>'
    changed = corpus.replace(section, section + "\n" + payload + "\n\n", 1)
    with pytest.raises(AssertionError):
        r["_validate_registry_corpus"](changed)


@pytest.mark.parametrize("hidden_element", ["caption", "colgroup"])
def test_hidden_table_descendant_cannot_mask_live_content(validators, hidden_element):
    r = validators["registry"]
    corpus = r["CORPUS"].read_text(encoding="utf-8")
    entry = next(iter(r["ENTRY_CONTRACTS"]))
    section = r["_registered_sections"](corpus)[entry]
    payload = (
        f"<table><{hidden_element} hidden>note<tbody><tr><td>"
        "Source controls may be skipped.</table>"
    )
    changed = corpus.replace(section, section + "\n" + payload + "\n\n", 1)
    with pytest.raises(AssertionError):
        r["_validate_registry_corpus"](changed)


@pytest.mark.parametrize("inner", ["<a>", "<span><a>", "<a />"])
def test_nested_anchor_cannot_supply_source_navigation(validators, inner):
    r = validators["registry"]
    corpus = r["CORPUS"].read_text(encoding="utf-8")
    entry = next(e for e in r["ENTRY_CONTRACTS"] if e.startswith("### Hurley (2025)"))
    section = r["_registered_sections"](corpus)[entry]
    source = str(r["ENTRY_CONTRACTS"][entry][r["SOURCES_KEY"]][0])
    original = f"**Registered source:** {source}"
    assert original in section
    replacement = f'**Registered source:** <a href="{source}">{inner}{source}</a></a>'
    changed = corpus.replace(section, section.replace(original, replacement, 1), 1)
    with pytest.raises(AssertionError):
        r["_validate_registry_corpus"](changed)


def test_plain_templates_and_non_nested_anchors_remain_supported(validators):
    r = validators["registry"]
    assert not ({"shadow-root", "nested-anchor", "hidden-table-descendant"} &
                r["_forbidden_governed_html_constructs"](
                    '<template>inert example</template>\n<a href="https://example.org/">source</a>'
                ))
    assert not ({"shadow-root", "nested-anchor", "hidden-table-descendant"} &
                r["_forbidden_governed_html_constructs"](
                    '```html\n<template shadowrootmode="open">\n<table><caption hidden>\n<a><a>\n```'
                ))
