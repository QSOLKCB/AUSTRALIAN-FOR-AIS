"""Regression evidence for the shared roadmap/methodology HTML contract."""
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parent.parent


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


def assert_policing_mutation_rejected(validators, wrapper, clause="source-gated research proposal"):
    p = validators["policing"]
    roadmap = p["ROADMAP"].read_text(encoding="utf-8")
    assert clause in roadmap
    changed = roadmap.replace(clause, wrapper.format(clause=clause), 1)
    assert changed != roadmap
    with pytest.raises(AssertionError):
        p["_validate_policing_workstream"](changed)


@pytest.mark.parametrize("tag", ["iframe", "object"])
def test_reported_replacement_fallback(validators, tag):
    assert_policing_mutation_rejected(validators, f"<{tag}>{{clause}}</{tag}>")


@pytest.mark.parametrize("tag", ["defs", "symbol"])
def test_reported_svg_definition_subtree(validators, tag):
    assert_policing_mutation_rejected(validators, f"<svg><{tag}>{{clause}}</{tag}></svg>")


@pytest.mark.parametrize("style", ["font-size:0", "color:transparent"])
def test_reported_unsupported_inline_style(validators, style):
    assert_policing_mutation_rejected(validators, f'<span style="{style}">{{clause}}</span>')


@pytest.mark.parametrize("tag", ["del", "s", "strike"])
def test_reported_deleted_negation(validators, tag):
    assert_policing_mutation_rejected(validators, f"<{tag}>not</{tag}> legal advice", "not legal advice")


def surface_document(validators, surface):
    p, h, receipt = (validators[key] for key in ("policing", "workstream_h", "receipt"))
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
    return (h["METHODOLOGY"].read_text(encoding="utf-8"), h["POLICING_METHODOLOGY_HEADING"],
            receipt["POLICING_METHODOLOGY_END_HEADING"], receipt["_assert_canonical_high_stakes_gate"],
            "Before publication")


SURFACES = ["workstream_i", "workstream_h", "trans_tasman", "policing_methodology"]
WRAPPERS = [
    pytest.param("<iframe>{clause}</iframe>", id="iframe"),
    pytest.param("<object>{clause}</object>", id="object"),
    pytest.param('<embed src="data:text/html,Source%20review%20may%20be%20skipped.">{clause}', id="embed"),
    pytest.param("<audio>{clause}</audio>", id="audio"),
    pytest.param("<video>{clause}</video>", id="video"),
    pytest.param("<svg><defs>{clause}</defs></svg>", id="svg-defs"),
    pytest.param("<svg><symbol>{clause}</symbol></svg>", id="svg-symbol"),
    pytest.param('<span style="font-size:0">{clause}</span>', id="font-size"),
    pytest.param('<span style="color:transparent">{clause}</span>', id="transparent"),
    pytest.param("<del>{clause}</del>", id="del"),
    pytest.param("<s>{clause}</s>", id="s"),
    pytest.param("<strike>{clause}</strike>", id="strike"),
]


@pytest.mark.parametrize("surface", SURFACES)
def test_unchanged_sealed_surface_still_validates(validators, surface):
    original, _, _, validate, _ = surface_document(validators, surface)
    validate(original)


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("wrapper", WRAPPERS)
def test_all_shared_surfaces_reject_unsupported_html(validators, surface, wrapper):
    original, start_heading, end_heading, validate, clause = surface_document(validators, surface)
    start = original.index(start_heading)
    end = original.index(end_heading, start)
    section = original[start:end]
    assert clause in section
    changed = original[:start] + section.replace(clause, wrapper.format(clause=clause), 1) + original[end:]
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("wrapper", [
    '<span style="font-size:0">\n{section}\n</span>\n',
    '<svg><symbol>\n{section}\n</symbol></svg>\n',
    '<object>\n{section}\n</object>\n',
    '<del>\n{section}\n</del>\n',
])
def test_preflight_runs_before_heading_slicing(validators, surface, wrapper):
    original, start_heading, end_heading, validate, _ = surface_document(validators, surface)
    start = original.index(start_heading)
    end = original.index(end_heading, start)
    changed = original[:start] + wrapper.format(section=original[start:end]) + original[end:]
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("payload", [
    '<iframe srcdoc="Source review may be skipped."></iframe>',
    '<object data="data:text/html,Source%20review%20may%20be%20skipped."></object>',
    '<span hidden><iframe srcdoc="Source review may be skipped."></iframe></span>',
    '<span style="display:none; color:transparent"></span>',
])
def test_replacement_and_styling_cannot_disappear_before_preflight(validators, surface, payload):
    original, _, end_heading, validate, _ = surface_document(validators, surface)
    changed = original.replace(end_heading, payload + "\n\n" + end_heading, 1)
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("markup,kind", [
    ('<IFRAME />fallback</IFRAME>', 'replacement-content'),
    ('<OBJECT\ndata="example" />fallback</OBJECT>', 'replacement-content'),
    ('<embed src="example" />', 'replacement-content'),
    ('<SVG><DEFS>hidden</DEFS></SVG>', 'raw-svg'),
    ('<svg><metadata>hidden</metadata></svg>', 'raw-svg'),
    ('<svg><symbol />hidden</svg>', 'raw-svg'),
    ('<DEL>not</DEL> legal advice', 'semantic-deletion'),
    ('<strike />not legal advice', 'semantic-deletion'),
    ('<span style>text</span>', 'inline-style'),
    ('<span title=">" STYLE\n=\n"font-size:0">text</span>', 'inline-style'),
    ('<span data-style="unused" style="">text</span>', 'inline-style'),
    ('<span style="" style="font-size:0">text</span>', 'inline-style'),
    ('<span\n    title="example"\n    style="font-size:0">text</span>', 'inline-style'),
    ('<span title="`" style="font-size:0">text</span>`', 'inline-style'),
])
def test_preflight_parses_html_instead_of_attribute_spelling(validators, markup, kind):
    p = validators['policing']
    assert kind in p['_governed_surface_html_violations'](markup)
    with pytest.raises(AssertionError):
        p['_visible_text'](markup)


@pytest.mark.parametrize("whitespace", ['\n', '\r', '\r\n', '\f', '\n\t'])
def test_multiline_styles_cannot_supply_governed_text(validators, whitespace):
    wrapper = f'<span STYLE{whitespace}="font-size:0">{{clause}}</span>'
    assert_policing_mutation_rejected(validators, wrapper)


@pytest.mark.parametrize("payload", [
    '<iframe srcdoc="example"></iframe>',
    '<svg><symbol>example</symbol></svg>',
    '<span style="font-size:0">example</span>',
    '<del>example</del>',
])
@pytest.mark.parametrize("wrapper", [
    '`{payload}`',
    '```html\n{payload}\n```',
    '> ```html\n> {payload}\n> ```',
    '<!-- {payload} -->',
])
def test_literal_examples_do_not_become_live_html(validators, payload, wrapper):
    assert not validators['policing']['_governed_surface_html_violations'](wrapper.format(payload=payload))


@pytest.mark.parametrize("markup", [
    '<span title="style=font-size:0">text</span>',
    '<span data-style="font-size:0">text</span>',
    '<span title="<iframe srcdoc=example>">text</span>',
    '<span title="<svg><defs>example</defs></svg>">text</span>',
    '<span title="<del>not</del>">text</span>',
    '<strong>text</strong>',
])
def test_attributes_and_ordinary_markup_remain_supported(validators, markup):
    p = validators['policing']
    assert not p['_governed_surface_html_violations'](markup)
    assert p['_visible_text'](markup) == 'text'
