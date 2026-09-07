"""Reject document-active HTML without promoting literal examples to markup."""
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parent.parent
SHARED_SURFACES = ("workstream_i", "workstream_h", "trans_tasman", "policing_methodology")
SURFACES = (*SHARED_SURFACES, "registry")
SCRIPT = '<script>document.body.textContent="Source review may be skipped.";</script>'
REFRESH = '<meta http-equiv="refresh" content="0; url=https://example.com/">'
SHADOW = '<div><template shadowrootmode="open">Source review may be skipped.</template></div>'


@pytest.fixture(scope="module")
def validators():
    namespaces = {
        name: runpy.run_path(str(ROOT / "tests" / filename))
        for name, filename in {
            "policing": "test_policing_context_roadmap.py",
            "registry": "test_research_reference_registry.py",
            "workstream_h": "test_workstream_h_methodology.py",
            "receipt": "test_policing_contract_receipt.py",
        }.items()
    }
    namespaces["surface_document"] = runpy.run_path(
        str(ROOT / "tests" / "test_pr4_shared_html_regressions.py")
    )["surface_document"]
    return namespaces


def surface_case(validators, surface):
    if surface == "registry":
        r = validators["registry"]
        text = r["CORPUS"].read_text(encoding="utf-8")
        entry = "### *Black Comedy* (ABC, 2014-2020)"
        section = r["_registered_sections"](text)[entry]
        start = text.index(section)
        return text, start, start + len(section), r["_validate_registry_corpus"], str(r["ENTRY_CONTRACTS"][entry][r["SOURCE_TYPE_FIELD"]])
    text, heading, boundary, validate, clause = validators["surface_document"](validators, surface)
    start = text.index(heading)
    return text, start, text.index(boundary, start), validate, clause


@pytest.mark.parametrize("finding,surface", [
    ("noscript", "workstream_i"),
    ("shadow-root", "workstream_i"),
    ("meta-refresh", "workstream_i"),
    ("meta-refresh", "registry"),
    ("script", "workstream_i"),
    ("script", "registry"),
])
def test_reported_active_html_bypass(validators, finding, surface):
    text, start, end, validate, clause = surface_case(validators, surface)
    validate(text)
    section = text[start:end]
    if finding == "noscript":
        assert clause in section
        section = section.replace(clause, f"<noscript>{clause}</noscript>", 1)
    else:
        payload = {"shadow-root": SHADOW, "meta-refresh": REFRESH, "script": SCRIPT}[finding]
        section = section.rstrip() + "\n\n" + payload + "\n\n"
    with pytest.raises(AssertionError):
        validate(text[:start] + section + text[end:])


@pytest.mark.parametrize("surface", SHARED_SURFACES)
@pytest.mark.parametrize("tag", ("noscript", "NOSCRIPT", "xmp", "plaintext", "listing", "noframes", "noembed"))
def test_conditional_raw_text_cannot_supply_any_shared_safeguard(validators, surface, tag):
    text, start, end, validate, clause = surface_case(validators, surface)
    section = text[start:end]
    assert clause in section
    changed = section.replace(clause, f"<{tag}>{clause}</{tag}>", 1)
    with pytest.raises(AssertionError):
        validate(text[:start] + changed + text[end:])


@pytest.mark.parametrize("surface", SHARED_SURFACES)
@pytest.mark.parametrize("attribute", ('shadowrootmode="open"', 'shadowrootmode="closed"', 'SHADOWROOTMODE\n=\n"open"', 'shadowroot="open"'))
def test_shadow_content_cannot_escape_shared_section_integrity(validators, surface, attribute):
    text, _, end, validate, _ = surface_case(validators, surface)
    payload = f'<div><template {attribute}>Source review may be skipped.</template></div>'
    with pytest.raises(AssertionError):
        validate(text[:end] + payload + "\n\n" + text[end:])


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("position", ("before", "inside", "after"))
@pytest.mark.parametrize("payload", (SCRIPT, REFRESH))
def test_document_active_html_is_rejected_before_any_section_slicing(validators, surface, position, payload):
    text, _, end, validate, _ = surface_case(validators, surface)
    offset = {"before": 0, "inside": end, "after": len(text)}[position]
    changed = text[:offset] + "\n\n" + payload + "\n\n" + text[offset:]
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("markup,kind", [
    ('<script src="https://example.com/code.js"></script>', 'executable-script'),
    ('<SCRIPT\ntype="module">void 0</SCRIPT>', 'executable-script'),
    ('<script />void 0</script>', 'executable-script'),
    ('<script type="application/json">{}</script>', 'executable-script'),
    ('<meta HTTP-EQUIV="REFRESH" content="30">', 'meta-refresh'),
    ('<meta http-equiv\n=\n"refresh" content="0">', 'meta-refresh'),
    ('<meta http-equiv\f="refresh" content="0">', 'meta-refresh'),
    ('<meta http-equiv="re&#102;resh" content="0">', 'meta-refresh'),
    ('<meta http-equiv="refresh" http-equiv="content-type" content="0">', 'meta-refresh'),
    ('<meta title=">" http-equiv="refresh" content="0" />', 'meta-refresh'),
    ('<meta\n    title="example"\n    http-equiv="refresh"\n    content="0">', 'meta-refresh'),
])
def test_both_parsed_policies_recognise_active_elements(validators, markup, kind):
    assert kind in validators["policing"]["_governed_surface_html_violations"](markup)
    assert kind in validators["registry"]["_forbidden_governed_html_constructs"](markup)


@pytest.mark.parametrize("markup,kind", [
    ('<noscript />hidden safeguard</noscript>', 'conditional-raw-text'),
    ('<template shadowrootmode>example</template>', 'shadow-root'),
    ('<template shadowrootmode="">example</template>', 'shadow-root'),
    ('<template shadowrootmode="closed" shadowrootmode="open">example</template>', 'shadow-root'),
    ('<template title="`" shadowrootmode="open">example</template>`', 'shadow-root'),
])
def test_shared_policy_uses_parsed_tag_and_attribute_names(validators, markup, kind):
    assert kind in validators["policing"]["_governed_surface_html_violations"](markup)


@pytest.mark.parametrize("payload", (SCRIPT, REFRESH))
@pytest.mark.parametrize("wrapper", ("<div>\n`{payload}`\n</div>", "<pre>\n{payload}\n</pre>"))
def test_raw_html_backticks_and_pre_blocks_do_not_conceal_live_elements(validators, payload, wrapper):
    markup = wrapper.format(payload=payload)
    expected = "executable-script" if payload == SCRIPT else "meta-refresh"
    assert expected in validators["policing"]["_governed_surface_html_violations"](markup)
    assert expected in validators["registry"]["_forbidden_governed_html_constructs"](markup)


@pytest.mark.parametrize("payload", (SCRIPT, REFRESH, SHADOW, '<noscript>example</noscript>'))
@pytest.mark.parametrize("wrapper", ('`{payload}`', '```html\n{payload}\n```', '> ```html\n> {payload}\n> ```', '<!-- {payload} -->'))
def test_literal_examples_remain_inert_at_both_preflights(validators, payload, wrapper):
    example = wrapper.format(payload=payload)
    assert not validators["policing"]["_governed_surface_html_violations"](example)
    assert not validators["registry"]["_forbidden_governed_html_constructs"](example)


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("payload", (SCRIPT, REFRESH, SHADOW, '<noscript>example</noscript>'))
def test_commented_examples_do_not_invalidate_unchanged_documents(validators, surface, payload):
    text, _, _, validate, _ = surface_case(validators, surface)
    validate("<!-- " + payload + " -->\n\n" + text)


@pytest.mark.parametrize("markup", [
    '<meta charset="utf-8">',
    '<meta name="refresh" content="description">',
    '<meta data-http-equiv="refresh" content="0">',
    '<meta http-equiv="content-type" http-equiv="refresh" content="0">',
    '<meta http-equiv="&amp;#114;efresh" content="0">',
    '<span data-shadowrootmode="open">text</span>',
    '<template>ordinary inert text</template>',
])
def test_harmless_metadata_and_attribute_values_remain_supported(validators, markup):
    assert not validators["policing"]["_governed_surface_html_violations"](markup)
    assert not validators["registry"]["_forbidden_governed_html_constructs"](markup)
