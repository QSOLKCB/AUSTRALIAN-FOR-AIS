from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
POLICING = runpy.run_path(str(Path(__file__).with_name("test_policing_context_roadmap.py")))
REGISTRY = runpy.run_path(str(Path(__file__).with_name("test_research_reference_registry.py")))
WORKSTREAM_H = runpy.run_path(str(Path(__file__).with_name("test_workstream_h_methodology.py")))


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


def test_executable_uri_autolink_is_rejected_on_shared_and_registry_surfaces() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    payload = "\n<javascript:alert(1)>\n"
    mutated_roadmap = roadmap.replace(
        POLICING["WORKSTREAM_END"], payload + POLICING["WORKSTREAM_END"], 1
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = REGISTRY["_registered_sections"](corpus)[entry]
    mutated_section = section + "\n<javascript:alert(1)>\n"
    mutated_corpus = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)

    assert POLICING["_visible_text"]("<https://example.com/path>") == "https://example.com/path"


@pytest.mark.parametrize(
    "payload",
    (
        "<ul><li hidden>masked<li>Current sources may be skipped.</ul>",
        "<dl><dt hidden>masked<dd>Current sources may be skipped.</dl>",
        "<dl><dd hidden>masked<dt>Current sources may be skipped.</dl>",
    ),
)
def test_implied_list_and_definition_item_ends_expose_shared_contradictions(
    payload: str,
) -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated = roadmap.replace(
        POLICING["WORKSTREAM_END"],
        "\n" + payload + "\n" + POLICING["WORKSTREAM_END"],
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_type6_raw_html_cannot_supply_registry_metadata_or_link() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    inert = f"<div>\n**Registered source:** [{url}]({url})\n</div>"
    assert live in corpus
    mutated = corpus.replace(live, inert, 1)
    assert REGISTRY["_contains_markdown_structure_in_type6_raw_html"](mutated)
    with pytest.raises(AssertionError, match="type-6"):
        REGISTRY["_validate_registry_corpus"](mutated)



def test_hidden_until_found_is_rejected_across_governed_paths() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    payload = '<span hidden="until-found">Current sources may be skipped.</span>'
    mutated_roadmap = roadmap.replace(
        POLICING["WORKSTREAM_END"],
        "\n" + payload + "\n" + POLICING["WORKSTREAM_END"],
        1,
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    injected = REGISTRY["STATUS_HEADING"] + "\n" + payload
    mutated_corpus = corpus.replace(REGISTRY["STATUS_HEADING"], injected, 1)
    with pytest.raises(AssertionError, match="conditional/legacy raw-text"):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)


def test_base_element_is_rejected_across_governed_paths() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    payload = '<base target="_top">'
    mutated_roadmap = roadmap.replace(
        POLICING["WORKSTREAM_END"],
        "\n" + payload + "\n" + POLICING["WORKSTREAM_END"],
        1,
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    injected = REGISTRY["STATUS_HEADING"] + "\n" + payload
    mutated_corpus = corpus.replace(REGISTRY["STATUS_HEADING"], injected, 1)
    with pytest.raises(AssertionError, match="document-root HTML"):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)



def test_commonmark_rule_of_three_preserves_inner_literal_delimiters() -> None:
    assert POLICING["_visible_text"]("n*o**t* legal advice") == "no**t legal advice"
    assert REGISTRY["_visible_inline_text"]("n*o**t* legal advice") == "no**t legal advice"

    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated = roadmap.replace("not legal advice", "n*o**t* legal advice", 1)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_anchor_target_is_rejected_for_registered_source() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    targeted = f'**Registered source:** <a href="{url}" target="_top">{url}</a>'
    assert live in corpus
    mutated = corpus.replace(live, targeted, 1)
    with pytest.raises(AssertionError, match="executable URL"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_malformed_raw_tag_remains_literal_across_governed_paths() -> None:
    payload = "<span hidden=>Current sources may be skipped.</span>"
    visible = POLICING["_visible_text"](payload)
    assert "<span hidden=>" in visible
    assert "Current sources may be skipped." in visible
    registry_visible = REGISTRY["_visible_inline_text"](payload)
    assert "<span hidden=>" in registry_visible
    assert "Current sources may be skipped." in registry_visible

    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated_roadmap = roadmap.replace(
        POLICING["WORKSTREAM_END"],
        "\n" + payload + "\n" + POLICING["WORKSTREAM_END"],
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    injected = REGISTRY["STATUS_HEADING"] + "\n" + payload
    mutated_corpus = corpus.replace(REGISTRY["STATUS_HEADING"], injected, 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)



def test_aria_descriptions_are_rejected_for_governed_source_links() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    assert live in corpus
    variants = (
        f'**Registered source:** <a href="{url}" aria-description="This material is freely reusable">{url}</a>',
        f'**Registered source:** <a href="{url}" aria-describedby="rights-note">{url}</a>'
        '<span id="rights-note" hidden>This material is freely reusable.</span>',
    )
    for variant in variants:
        mutated = corpus.replace(live, variant, 1)
        with pytest.raises(AssertionError, match="accessible-name overrides"):
            REGISTRY["_validate_registry_corpus"](mutated)


def test_markdown_link_title_is_rejected_for_registered_source() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    titled = f'**Registered source:** [{url}]({url} "This material is freely reusable")'
    assert live in corpus
    mutated = corpus.replace(live, titled, 1)
    with pytest.raises(AssertionError, match="Markdown link titles"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_negative_tabindex_is_rejected_for_registered_source_anchor() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    unfocusable = f'**Registered source:** <a href="{url}" tabindex="-1">{url}</a>'
    assert live in corpus
    mutated = corpus.replace(live, unfocusable, 1)
    with pytest.raises(AssertionError, match="keyboard-navigation suppression"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_registry_whitespace_delimited_emphasis_marker_remains_visible() -> None:
    sample = "registered * as scholarship"
    assert REGISTRY["_visible_inline_text"](sample) == sample

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    mutated = corpus.replace(live, "The article is a * scholarly research reference.", 1)
    assert mutated != corpus
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_aria_disabled_true_is_rejected_for_registered_source_anchor() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    disabled = f'**Registered source:** <a href="{url}" aria-disabled="true">{url}</a>'
    assert live in corpus
    mutated = corpus.replace(live, disabled, 1)
    with pytest.raises(AssertionError, match="aria-disabled source-link suppression"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_raw_html_thematic_break_cannot_split_pinned_rights_clause() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    split = "The article is a scholarly <hr> research reference."
    assert live in corpus
    mutated = corpus.replace(live, split, 1)
    with pytest.raises(AssertionError, match="raw HTML thematic break"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_workstream_h_citation_markdown_title_is_rejected() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    label, destination = sorted(WORKSTREAM_H["WORKSTREAM_H_CITATION_LINKS"])[0]
    live = f"[{label}]({destination})"
    titled = f'[{label}]({destination} "This source may be copied freely")'
    assert live in roadmap
    mutated = roadmap.replace(live, titled, 1)
    with pytest.raises(AssertionError, match="citation Markdown link titles"):
        WORKSTREAM_H["_assert_workstream_h_integrity"](mutated)


def test_registered_source_anchor_role_override_is_rejected() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    overridden = f'**Registered source:** <a href="{url}" role="button">{url}</a>'
    assert live in corpus
    mutated = corpus.replace(live, overridden, 1)
    with pytest.raises(AssertionError, match="semantic role overrides"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_preformatted_whitespace_cannot_bypass_registry_receipt() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    preformatted = "<pre>The article is a scholarly\n                    research reference.</pre>"
    assert live in corpus
    mutated = corpus.replace(live, preformatted, 1)
    assert "preformatted-content" in REGISTRY["_forbidden_governed_html_constructs"](mutated)
    with pytest.raises(AssertionError, match="preformatted HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)


# Human receipt: autolink/implied-end/type-6 repair passed 12 exact and 912 full-suite tests before self-cleanup.



@pytest.mark.parametrize("kind", ("preformatted-content", "semantic-role"))
def test_shared_methodology_rejects_preformatted_and_semantic_role_semantics(
    kind: str,
) -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")

    workstream_i_phrase = "source-gated research proposal"
    if kind == "preformatted-content":
        workstream_i_payload = "<pre>source-gated     research proposal</pre>"
    else:
        workstream_i_payload = '<a role="button">source-gated research proposal</a>'
    mutated_i = roadmap.replace(workstream_i_phrase, workstream_i_payload, 1)
    assert mutated_i != roadmap
    assert kind in POLICING["_governed_surface_html_violations"](mutated_i)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated_i)

    workstream_h_phrase = (
        "nationality and first-language identity must not define the comparison cohorts"
    )
    if kind == "preformatted-content":
        workstream_h_payload = (
            "<pre>nationality and first-language identity must     not define the "
            "comparison cohorts</pre>"
        )
    else:
        workstream_h_payload = (
            '<a role="button">nationality and first-language identity must not define '
            "the comparison cohorts</a>"
        )
    mutated_h = roadmap.replace(workstream_h_phrase, workstream_h_payload, 1)
    assert mutated_h != roadmap
    assert kind in POLICING["_governed_surface_html_violations"](mutated_h)
    with pytest.raises(AssertionError):
        WORKSTREAM_H["_assert_workstream_h_integrity"](mutated_h)
