"""Regression evidence for global styling, MathML and bidirectional markup."""
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parent.parent
SURFACES = ("workstream_i", "workstream_h", "trans_tasman", "policing_methodology")
STYLE = "<style>body { display: none }</style>"
LINK = '<link rel="stylesheet" href="data:text/css,body%7Bdisplay:none%7D">'


@pytest.fixture(scope="module")
def validators():
    return {
        name: runpy.run_path(str(ROOT / "tests" / filename))
        for name, filename in {
            "policing": "test_policing_context_roadmap.py",
            "workstream_h": "test_workstream_h_methodology.py",
            "receipt": "test_policing_contract_receipt.py",
        }.items()
    }


def surface_document(validators, surface):
    p, h, r = (validators[key] for key in ("policing", "workstream_h", "receipt"))
    if surface == "workstream_i":
        return (p["ROADMAP"].read_text(encoding="utf-8"), p["WORKSTREAM_HEADING"],
                p["WORKSTREAM_END_HEADING"], p["_validate_policing_workstream"],
                "source-gated research proposal")
    if surface == "workstream_h":
        return (h["ROADMAP"].read_text(encoding="utf-8"), h["WORKSTREAM_H_HEADING"],
                h["WORKSTREAM_I_HEADING"], h["_assert_workstream_h_integrity"],
                "nationality and first-language identity must not define the comparison cohorts")
    if surface == "trans_tasman":
        return (h["METHODOLOGY"].read_text(encoding="utf-8"), h["TRANS_TASMAN_METHODOLOGY_HEADING"],
                h["POLICING_METHODOLOGY_HEADING"], h["_assert_trans_tasman_integrity"],
                "exact group-stereotyping wording must not be reproduced")
    assert surface == "policing_methodology"
    return (r["METHODOLOGY"].read_text(encoding="utf-8"), r["POLICING_METHODOLOGY_HEADING"],
            r["POLICING_METHODOLOGY_END_HEADING"], r["_assert_canonical_high_stakes_gate"],
            r["CANONICAL_HIGH_STAKES_REVIEW_SENTENCE"])


@pytest.mark.parametrize("kind", ("stylesheet", "mathml", "bidirectional"))
def test_reported_rendering_bypass(validators, kind):
    original, _, end_heading, validate, clause = surface_document(validators, "workstream_i")
    if kind == "stylesheet":
        changed = original.replace(end_heading, STYLE + "\n\n" + end_heading, 1)
    elif kind == "mathml":
        changed = original.replace(clause, f"<math><mphantom>{clause}</mphantom></math>", 1)
    else:
        changed = original.replace(clause, f'<bdo dir="rtl">{clause}</bdo>', 1)
    assert changed != original
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("payload", (STYLE, LINK))
@pytest.mark.parametrize("location", ("before", "inside", "after"))
def test_stylesheets_are_rejected_document_wide(validators, surface, payload, location):
    original, start_heading, end_heading, validate, _ = surface_document(validators, surface)
    if location == "before":
        changed = payload + "\n\n" + original
    elif location == "after":
        changed = original + "\n\n" + payload
    else:
        changed = original.replace(end_heading, payload + "\n\n" + end_heading, 1)
    assert start_heading in changed
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("wrapper", (
    "<math><mphantom>{clause}</mphantom></math>",
    '<bdo dir="rtl">{clause}</bdo>',
    '<span DIR\n=\n"rtl">{clause}</span>',
))
def test_shared_safeguards_cannot_be_hidden_or_reordered(validators, surface, wrapper):
    original, start_heading, end_heading, validate, clause = surface_document(validators, surface)
    start = original.index(start_heading)
    end = original.index(end_heading, start)
    section = original[start:end]
    assert clause in section
    changed = original[:start] + section.replace(clause, wrapper.format(clause=clause), 1) + original[end:]
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("wrapper", (
    "<math><mphantom>\n{section}\n</mphantom></math>\n",
    '<bdo dir="rtl">\n{section}\n</bdo>\n',
))
def test_ancestor_markup_is_checked_before_heading_slicing(validators, surface, wrapper):
    original, start_heading, end_heading, validate, _ = surface_document(validators, surface)
    start = original.index(start_heading)
    end = original.index(end_heading, start)
    changed = original[:start] + wrapper.format(section=original[start:end]) + original[end:]
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("markup,kind", (
    (STYLE, "stylesheet"),
    ('<STYLE\nmedia="all">body { display:none }</STYLE>', "stylesheet"),
    (LINK, "stylesheet"),
    ('<LINK\nREL="alternate stylesheet"\nHREF="example.css" />', "stylesheet"),
    ('<span class="hidden">text</span>', "stylesheet"),
    ('<math><mphantom>text</mphantom></math>', "raw-mathml"),
    ('<MATH><MPHANTOM>text</MPHANTOM></MATH>', "raw-mathml"),
    ('<math />text', "raw-mathml"),
    ('<bdo>text</bdo>', "bidirectional"),
    ('<BDO DIR="rtl" />text', "bidirectional"),
    ('<span dir>text</span>', "bidirectional"),
    ('<span dir="">text</span>', "bidirectional"),
    ('<span dir="ltr" DIR="rtl">text</span>', "bidirectional"),
    ('<span title=">"\n    DIR\n    ="rtl">text</span>', "bidirectional"),
    ('<span dir\f="rtl">text</span>', "bidirectional"),
))
def test_policy_uses_parsed_tags_and_attribute_names(validators, markup, kind):
    p = validators["policing"]
    assert kind in p["_governed_surface_html_violations"](markup)
    with pytest.raises(AssertionError):
        p["_visible_text"](markup)


@pytest.mark.parametrize("tag", ("pre", "div", "span"))
@pytest.mark.parametrize("payload", (STYLE, '<math><mphantom>text</mphantom></math>', '<bdo dir="rtl">text</bdo>'))
def test_backticks_inside_raw_html_blocks_are_not_markdown_code(validators, tag, payload):
    markup = f"<{tag}>\n`{payload}`\n</{tag}>\n"
    assert validators["policing"]["_governed_surface_html_violations"](markup)


@pytest.mark.parametrize("payload", (STYLE, LINK, '<math><mphantom>text</mphantom></math>', '<bdo dir="rtl">text</bdo>'))
@pytest.mark.parametrize("wrapper", (
    '`{payload}`',
    '```html\n{payload}\n```',
    '> ```html\n> {payload}\n> ```',
    '<!-- {payload} -->',
    '    {payload}\n',
))
def test_literal_code_and_comment_examples_remain_inert(validators, payload, wrapper):
    assert not validators["policing"]["_governed_surface_html_violations"](wrapper.format(payload=payload))


@pytest.mark.parametrize("markup", (
    '<span data-class="hidden">text</span>',
    '<strong>text</strong>',
))
def test_attribute_decoys_and_plain_markup_remain_supported(validators, markup):
    p = validators["policing"]
    assert not p["_governed_surface_html_violations"](markup)
    assert p["_visible_text"](markup) == "text"


def test_blank_line_resumes_markdown_after_flow_html_block(validators):
    markup = "<div>\n\n```html\n" + STYLE + "\n```\n\n</div>\n"
    assert not validators["policing"]["_governed_surface_html_violations"](markup)


@pytest.mark.parametrize("surface", SURFACES)
def test_unchanged_contracts_and_commented_stylesheets_still_validate(validators, surface):
    original, _, end_heading, validate, _ = surface_document(validators, surface)
    validate(original)
    validate(original.replace(end_heading, "<!-- " + STYLE + " -->\n\n" + end_heading, 1))
