"""Regression evidence for source associations and unsealed HTML rendering."""
import base64
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parent.parent
SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="40">'
    '<text x="0" y="24">Source review may be skipped.</text></svg>'
)
IMAGE_URI = "data:image/svg+xml;base64," + base64.b64encode(SVG.encode()).decode()


@pytest.fixture(scope="module")
def validators():
    return {
        name: runpy.run_path(str(ROOT / "tests" / filename))
        for name, filename in {
            "registry": "test_research_reference_registry.py",
            "policing": "test_policing_context_roadmap.py",
            "workstream_h": "test_workstream_h_methodology.py",
            "receipt": "test_policing_contract_receipt.py",
        }.items()
    }


@pytest.fixture(scope="module")
def registered(validators):
    r = validators["registry"]
    corpus = r["CORPUS"].read_text(encoding="utf-8")
    entry = "### *The Castle* (1997)"
    section = r["_registered_sections"](corpus)[entry]
    assert section in corpus
    sources = tuple(r["ENTRY_CONTRACTS"][entry][r["SOURCES_KEY"]])
    assert len(sources) == 2
    return corpus, entry, section, sources


def replace_sources(section, sources, form, *, swapped):
    targets = sources[::-1] if swapped else sources
    changed = section
    markers = tuple(f"PR4_SOURCE_URL_{index}_PLACEHOLDER" for index in range(len(sources)))
    for label, marker in zip(sources, markers):
        assert marker not in changed and label in changed
        changed = changed.replace(label, marker, 1)
    for label, target, marker in zip(sources, targets, markers):
        if form == "inline":
            link = f"[{label}]({target})"
        elif form == "multiline-title":
            link = f'[{label}]({target}\n "source")'
        elif form == "html":
            link = f'<a href="{target}">{label}</a>'
        elif form == "html-nested-label":
            # An inline element must not manufacture a space within the URL.
            midpoint = len(label) // 2
            link = f'<a href="{target}">{label[:midpoint]}<span>{label[midpoint:]}</span></a>'
        else:
            raise ValueError(form)
        changed = changed.replace(marker, link, 1)
    return changed


@pytest.mark.parametrize("form", ["inline", "multiline-title", "html", "html-nested-label"])
def test_registry_rejects_swapped_url_labels(validators, registered, form):
    r = validators["registry"]
    corpus, _, section, sources = registered
    changed_section = replace_sources(section, sources, form, swapped=True)
    changed = corpus.replace(section, changed_section, 1)
    with pytest.raises(AssertionError):
        r["_validate_registry_corpus"](changed)


@pytest.mark.parametrize("form", ["inline", "multiline-title", "html", "html-nested-label"])
def test_matching_source_bindings_preserve_accepted_hashes(validators, registered, form):
    r = validators["registry"]
    corpus, _, section, sources = registered
    changed = corpus.replace(section, replace_sources(section, sources, form, swapped=False), 1)
    r["_validate_registry_corpus"](changed)


@pytest.mark.parametrize("whitespace", ["\n", "\r", "\r\n", "\f", "\n\t"])
def test_registry_rejects_multiline_style_attributes(validators, registered, whitespace):
    r = validators["registry"]
    corpus, entry, section, _ = registered
    rights = r["_scalar_markdown_value"](entry, section, r["RIGHTS_FIELD"])
    assert rights in section
    replacement = f'<span style{whitespace}="font-size:0">{rights}</span>'
    changed = corpus.replace(section, section.replace(rights, replacement, 1), 1)
    with pytest.raises(AssertionError):
        r["_validate_registry_corpus"](changed)


@pytest.mark.parametrize("markup", [
    '<span style\n="font-size:0">text</span>',
    '<span STYLE\r="font-size:0">text</span>',
    '<span style\f="font-size:0">text</span>',
    '<span title=">" style\n="font-size:0">text</span>',
    '<span style\n=\n"font-size:0" />text</span>',
    '<span style>text</span>',
])
def test_style_detection_uses_parsed_attribute_names(validators, markup):
    r = validators["registry"]
    assert "inline-style" in r["_forbidden_governed_html_constructs"](markup)


@pytest.mark.parametrize("markup", [
    '<span title="style=font-size:0">text</span>',
    '<span title="class=example">text</span>',
    '<span data-style="font-size:0">text</span>',
    '<span title="<img src=example>">text</span>',
])
def test_attribute_value_decoys_do_not_create_live_markup(validators, markup):
    r = validators["registry"]
    assert not ({"inline-style", "styling", "replacement"} &
                r["_forbidden_governed_html_constructs"](markup))
    assert "raw-image" not in validators["policing"]["_governed_surface_html_violations"](markup)


@pytest.mark.parametrize("image", [
    f'<img src="{IMAGE_URI}">',
    f'<img src="{IMAGE_URI}" />',
    f'<IMG\nSRC="{IMAGE_URI}">',
    f'<img hidden src="{IMAGE_URI}">',
])
def test_registry_rejects_raw_images(validators, registered, image):
    r = validators["registry"]
    corpus, _, section, _ = registered
    changed = corpus.replace(section, section + "\n" + image + "\n\n", 1)
    with pytest.raises(AssertionError):
        r["_validate_registry_corpus"](changed)


@pytest.mark.parametrize("surface", ["workstream_i", "workstream_h", "trans_tasman", "policing_methodology"])
@pytest.mark.parametrize("tag", ["img", "IMG"])
def test_shared_surfaces_reject_raw_images(validators, surface, tag):
    p, h, receipt = (validators[key] for key in ("policing", "workstream_h", "receipt"))
    image = f'<{tag}\nsrc="{IMAGE_URI}">\n\n'
    if surface == "workstream_i":
        original = p["ROADMAP"].read_text(encoding="utf-8")
        boundary = p["WORKSTREAM_END_HEADING"]
        validate = p["_validate_policing_workstream"]
    elif surface == "workstream_h":
        original = h["ROADMAP"].read_text(encoding="utf-8")
        boundary = h["WORKSTREAM_I_HEADING"]
        validate = h["_assert_workstream_h_integrity"]
    elif surface == "trans_tasman":
        original = h["METHODOLOGY"].read_text(encoding="utf-8")
        boundary = h["POLICING_METHODOLOGY_HEADING"]
        validate = h["_assert_trans_tasman_integrity"]
    else:
        original = h["METHODOLOGY"].read_text(encoding="utf-8")
        boundary = "## Scoring Philosophy"
        validate = receipt["_assert_canonical_high_stakes_gate"]
    assert boundary in original
    with pytest.raises(AssertionError):
        validate(original.replace(boundary, image + boundary, 1))


@pytest.mark.parametrize("wrapper", ["`{image}`", "```html\n{image}\n```", "> ```html\n> {image}\n> ```", "<!-- {image} -->"])
def test_image_examples_in_code_or_comments_stay_inert(validators, wrapper):
    image = f'<img src="{IMAGE_URI}">'
    example = wrapper.format(image=image)
    assert "replacement" not in validators["registry"]["_forbidden_governed_html_constructs"](example)
    assert "raw-image" not in validators["policing"]["_governed_surface_html_violations"](example)


@pytest.mark.parametrize("form", ["full", "collapsed", "shortcut"])
@pytest.mark.parametrize("swapped", [False, True])
def test_source_binding_extraction_resolves_document_references(validators, registered, form, swapped):
    r = validators["registry"]
    *_, sources = registered
    targets = sources[::-1] if swapped else sources
    links, definitions = [], []
    for index, (label, target) in enumerate(zip(sources, targets)):
        reference = f"source-{index}" if form == "full" else label
        if form == "full":
            links.append(f"[{label}][{reference}]")
        elif form == "collapsed":
            links.append(f"[{label}][]")
        else:
            links.append(f"[{label}]")
        definitions.append(f"[{reference}]:\n  {target}")
    field = "\n".join(links)
    scope = field + "\n\n" + "\n".join(definitions)
    expected = tuple(zip(sources, targets))
    assert r["_usable_https_source_bindings"](field, reference_scope=scope) == expected
    assert r["_usable_https_destinations"](field, reference_scope=scope) == targets


def test_html_binding_character_data_is_not_decoded_twice(validators):
    r = validators["registry"]
    destination = "https://example.org/source"
    markup = f'<a href="{destination}">&amp;#84;</a>'
    assert r["_usable_https_source_bindings"](markup) == (("&#84;", destination),)
