from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) Shared governed-HTML preflight: preserve anchor semantics and reject
# preformatted containers whose layout-sensitive whitespace is not represented
# by the registry's normalized text receipt.
replace_once(
    "tests/test_policing_context_roadmap.py",
    '''        if tag == "a" and {"ping", "target"}.intersection(attribute_names):\n            self.violations.add("executable-url")\n''',
    '''        if tag == "a" and {"ping", "target"}.intersection(attribute_names):\n            self.violations.add("executable-url")\n        # A role override can make an otherwise canonical provenance anchor\n        # cease to be exposed as a link to assistive technology. Keep the\n        # anchor's native semantic role inside the governed link contract.\n        if tag == "a" and "role" in attribute_names:\n            self.violations.add("semantic-role")\n''',
)
replace_once(
    "tests/test_policing_context_roadmap.py",
    '''        if tag in {"style", "link"}:\n            self.violations.add("stylesheet")\n''',
    '''        if tag in {"style", "link"}:\n            self.violations.add("stylesheet")\n        # The registry receipts normalize whitespace, so they cannot faithfully\n        # seal layout-significant whitespace inside raw preformatted HTML.\n        if tag == "pre":\n            self.violations.add("preformatted-content")\n''',
)

# 2) Registry consumes the new shared policy findings corpus-wide and emits
# explicit diagnostics instead of silently omitting them from the active gate.
replace_once(
    "tests/test_research_reference_registry.py",
    '''    "accessibility-disabled",\n    "keyboard-navigation",\n    "nested-anchor",\n''',
    '''    "accessibility-disabled",\n    "keyboard-navigation",\n    "semantic-role",\n    "preformatted-content",\n    "nested-anchor",\n''',
)
replace_once(
    "tests/test_research_reference_registry.py",
    '''    assert "keyboard-navigation" not in found, (\n        "negative tabindex keyboard-navigation suppression is not allowed in governed documents"\n    )\n    assert "nested-anchor" not in found, (\n''',
    '''    assert "keyboard-navigation" not in found, (\n        "negative tabindex keyboard-navigation suppression is not allowed in governed documents"\n    )\n    assert "semantic-role" not in found, (\n        "semantic role overrides on governed source anchors are not allowed in governed documents"\n    )\n    assert "preformatted-content" not in found, (\n        "preformatted HTML is not allowed in governed registry documents"\n    )\n    assert "nested-anchor" not in found, (\n''',
)

# 3) Workstream H citations: reuse the registry's title-aware CommonMark parser
# on the already-masked structural citation source. Titles are reader-visible
# tooltip provenance and therefore must not sit outside the sealed binding.
replace_once(
    "tests/test_workstream_h_methodology.py",
    '''    structure = registry["_mask_raw_html_tags_for_markdown_link_discovery"](structure)\n    return _inline_markdown_links(structure)\n''',
    '''    structure = registry["_mask_raw_html_tags_for_markdown_link_discovery"](structure)\n    titled_links = [\n        link\n        for link in registry["_markdown_inline_links"](structure)\n        if not link.image and link.title is not None\n    ]\n    assert not titled_links, (\n        "Workstream H citation Markdown link titles are not allowed; "\n        "tooltip provenance must remain inside the sealed citation contract"\n    )\n    return _inline_markdown_links(structure)\n''',
)

# 4) Exact regressions for all three fresh review findings.
replace_once(
    "tests/test_pr4_current_review_regressions.py",
    '''REGISTRY = runpy.run_path(str(Path(__file__).with_name("test_research_reference_registry.py")))\n''',
    '''REGISTRY = runpy.run_path(str(Path(__file__).with_name("test_research_reference_registry.py")))\nWORKSTREAM_H = runpy.run_path(str(Path(__file__).with_name("test_workstream_h_methodology.py")))\n''',
)
replace_once(
    "tests/test_pr4_current_review_regressions.py",
    '''# Human receipt: autolink/implied-end/type-6 repair passed 12 exact and 912 full-suite tests before self-cleanup.\n''',
    '''def test_workstream_h_citation_markdown_title_is_rejected() -> None:\n    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")\n    label, destination = sorted(WORKSTREAM_H["WORKSTREAM_H_CITATION_LINKS"])[0]\n    live = f"[{label}]({destination})"\n    titled = f'[{label}]({destination} "This source may be copied freely")'\n    assert live in roadmap\n    mutated = roadmap.replace(live, titled, 1)\n    with pytest.raises(AssertionError, match="citation Markdown link titles"):\n        WORKSTREAM_H["_assert_workstream_h_integrity"](mutated)\n\n\ndef test_registered_source_anchor_role_override_is_rejected() -> None:\n    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")\n    url = "https://iview.abc.net.au/show/black-comedy"\n    live = f"**Registered source:** {url}"\n    overridden = f'**Registered source:** <a href="{url}" role="button">{url}</a>'\n    assert live in corpus\n    mutated = corpus.replace(live, overridden, 1)\n    with pytest.raises(AssertionError, match="semantic role overrides"):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_preformatted_whitespace_cannot_bypass_registry_receipt() -> None:\n    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")\n    live = "The article is a scholarly research reference."\n    preformatted = "<pre>The article is a scholarly\\n                    research reference.</pre>"\n    assert live in corpus\n    mutated = corpus.replace(live, preformatted, 1)\n    assert "preformatted-content" in REGISTRY["_forbidden_governed_html_constructs"](mutated)\n    with pytest.raises(AssertionError, match="preformatted HTML"):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\n# Human receipt: autolink/implied-end/type-6 repair passed 12 exact and 912 full-suite tests before self-cleanup.\n''',
)
