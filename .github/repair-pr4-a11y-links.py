from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement target, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


policing = Path("tests/test_policing_context_roadmap.py")
replace_once(
    policing,
    '        if {"aria-label", "aria-labelledby"}.intersection(attribute_names):\n            self.violations.add("accessible-name")\n',
    '        if {"aria-label", "aria-labelledby", "aria-description", "aria-describedby"}.intersection(attribute_names):\n            self.violations.add("accessible-name")\n',
)
replace_once(
    policing,
    '''        values: dict[str, str] = {}\n        for key, value in attrs:\n            values.setdefault(key.lower(), value or "")\n        if tag == "meta" and values.get("http-equiv", "").strip().lower() == "refresh":\n''',
    '''        values: dict[str, str] = {}\n        for key, value in attrs:\n            values.setdefault(key.lower(), value or "")\n        # Negative tabindex removes an otherwise valid provenance anchor from\n        # sequential keyboard navigation. Keep focusability inside the governed\n        # link contract instead of sealing only label/href text.\n        if tag == "a" and "tabindex" in values:\n            try:\n                tabindex = int(values["tabindex"].strip())\n            except ValueError:\n                tabindex = 0\n            if tabindex < 0:\n                self.violations.add("keyboard-navigation")\n        if tag == "meta" and values.get("http-equiv", "").strip().lower() == "refresh":\n''',
)

registry = Path("tests/test_research_reference_registry.py")
replace_once(
    registry,
    '    "accessibility-hidden",\n    "nested-anchor",\n',
    '    "accessibility-hidden",\n    "keyboard-navigation",\n    "nested-anchor",\n',
)
replace_once(
    registry,
    '''    assert "accessibility-hidden" not in found, (\n        "aria-hidden accessibility suppression is not allowed in governed documents"\n    )\n    assert "nested-anchor" not in found, (\n''',
    '''    assert "accessibility-hidden" not in found, (\n        "aria-hidden accessibility suppression is not allowed in governed documents"\n    )\n    assert "keyboard-navigation" not in found, (\n        "negative tabindex keyboard-navigation suppression is not allowed in governed documents"\n    )\n    assert "nested-anchor" not in found, (\n''',
)
replace_once(
    registry,
    '''class MarkdownInlineLink:\n    start: int\n    end: int\n    label: str\n    destination: str\n    image: bool\n''',
    '''class MarkdownInlineLink:\n    start: int\n    end: int\n    label: str\n    destination: str\n    image: bool\n    title: str | None = None\n''',
)

text = registry.read_text(encoding="utf-8")
start = text.index("def _inline_link_destination(inner: str) -> str | None:\n")
end = text.index("\n\ndef _markdown_inline_links", start)
new_block = '''def _inline_link_destination_and_title(inner: str) -> tuple[str, str | None] | None:\n    """Extract a destination and optional CommonMark tooltip title."""\n    value = inner.lstrip(" \\t\\r\\n")\n    if not value:\n        return None\n\n    if value.startswith("<"):\n        close = value.find(">", 1)\n        if close < 0:\n            return None\n        destination = value[1:close]\n        remainder = value[close + 1:].strip()\n    else:\n        cursor = 0\n        depth = 0\n        while cursor < len(value):\n            character = value[cursor]\n            if character == "\\\\" and cursor + 1 < len(value):\n                cursor += 2\n                continue\n            if character == "(":\n                depth += 1\n            elif character == ")":\n                if depth == 0:\n                    return None\n                depth -= 1\n            elif character in " \\t\\r\\n" and depth == 0:\n                break\n            cursor += 1\n        if depth != 0:\n            return None\n        destination = value[:cursor]\n        remainder = value[cursor:].strip()\n\n    if not destination:\n        return None\n    title: str | None = None\n    if remainder:\n        quoted = (\n            len(remainder) >= 2\n            and remainder[0] in {"\\\"", "'"}\n            and remainder[-1] == remainder[0]\n        )\n        parenthesized = (\n            len(remainder) >= 2\n            and remainder[0] == "("\n            and remainder[-1] == ")"\n        )\n        if not (quoted or parenthesized):\n            return None\n        title = remainder[1:-1]\n    return destination, title\n\n\ndef _inline_link_destination(inner: str) -> str | None:\n    """Compatibility view retaining the existing destination-only helper."""\n    parsed = _inline_link_destination_and_title(inner)\n    return None if parsed is None else parsed[0]\n'''
registry.write_text(text[:start] + new_block + text[end:], encoding="utf-8")

replace_once(
    registry,
    '''        destination = _inline_link_destination(text[paren_start + 1:paren_end])\n        if destination is None:\n            cursor = paren_end + 1\n            continue\n\n        image = (\n''',
    '''        parsed_destination = _inline_link_destination_and_title(\n            text[paren_start + 1:paren_end]\n        )\n        if parsed_destination is None:\n            cursor = paren_end + 1\n            continue\n        destination, title = parsed_destination\n\n        image = (\n''',
)
replace_once(
    registry,
    '''                label=text[bracket + 1:label_end],\n                destination=destination,\n                image=image,\n            )\n''',
    '''                label=text[bracket + 1:label_end],\n                destination=destination,\n                image=image,\n                title=title,\n            )\n''',
)
replace_once(
    registry,
    '''def _require_registered_source_link(\n    entry: str,\n    section: str,\n    *,\n    reference_scope: str | None = None,\n    source_bindings: list[tuple[str, str]] | None = None,\n) -> tuple[str, ...]:\n''',
    '''def _require_registered_source_link(\n    entry: str,\n    section: str,\n    *,\n    reference_scope: str | None = None,\n    source_bindings: list[tuple[str, str]] | None = None,\n    source_titles: list[str] | None = None,\n) -> tuple[str, ...]:\n''',
)
replace_once(
    registry,
    '''    source_value = rendered[source_block.start(1):source_block.end(1)]\n    bindings = _usable_https_source_bindings(\n        source_value,\n        reference_scope=reference_scope,\n    )\n''',
    '''    source_value = rendered[source_block.start(1):source_block.end(1)]\n    if source_titles is not None:\n        title_structure = _mask_raw_html_tags_for_markdown_link_discovery(\n            _mask_hidden_html_regions(_structural_registry_text(source_value))\n        )\n        source_titles.extend(\n            link.title\n            for link in _markdown_inline_links(title_structure)\n            if not link.image and link.title is not None\n        )\n    bindings = _usable_https_source_bindings(\n        source_value,\n        reference_scope=reference_scope,\n    )\n''',
)
replace_once(
    registry,
    '''    _reject_non_commonmark_character_references(section)\n    source_bindings: list[tuple[str, str]] = []\n    destinations = _require_registered_source_link(\n        entry,\n        section,\n        reference_scope=reference_scope,\n        source_bindings=source_bindings,\n    )\n''',
    '''    _reject_non_commonmark_character_references(section)\n    source_bindings: list[tuple[str, str]] = []\n    source_titles: list[str] = []\n    destinations = _require_registered_source_link(\n        entry,\n        section,\n        reference_scope=reference_scope,\n        source_bindings=source_bindings,\n        source_titles=source_titles,\n    )\n''',
)
replace_once(
    registry,
    '''    assert set(source_bindings) == expected_bindings, (\n        f"{entry} registered-source label/destination bindings changed: "\n        f"expected {sorted(expected_bindings)!r}, got {sorted(source_bindings)!r}"\n    )\n    _require_complete_entry_integrity(entry, section)\n''',
    '''    assert set(source_bindings) == expected_bindings, (\n        f"{entry} registered-source label/destination bindings changed: "\n        f"expected {sorted(expected_bindings)!r}, got {sorted(source_bindings)!r}"\n    )\n    assert not source_titles, (\n        f"{entry} registered-source Markdown link titles are not allowed; "\n        "tooltip provenance must remain inside the sealed source contract"\n    )\n    _require_complete_entry_integrity(entry, section)\n''',
)

regressions = Path("tests/test_pr4_current_review_regressions.py")
text = regressions.read_text(encoding="utf-8")
marker = "\n\n# Human receipt: autolink/implied-end/type-6 repair passed 12 exact and 912 full-suite tests before self-cleanup.\n"
if text.count(marker) != 1:
    raise SystemExit("current-review human-receipt marker missing or duplicated")
additions = r'''


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
'''
regressions.write_text(text.replace(marker, additions + marker, 1), encoding="utf-8")
