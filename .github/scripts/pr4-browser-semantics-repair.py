from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, sentinel: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel in text:
        raise SystemExit(f"{path}: sentinel already present: {sentinel}")
    path.write_text(text.rstrip() + "\n\n\n" + addition.strip() + "\n", encoding="utf-8")


registry = Path("tests/test_research_reference_registry.py")
policing = Path("tests/test_policing_context_roadmap.py")
receipt = Path("tests/test_policing_contract_receipt.py")

# ---------------------------------------------------------------------------
# 1. Browser visibility: closed dialog is hidden just like closed details.
# ---------------------------------------------------------------------------
for path in (registry, policing):
    replace_once(
        path,
        '        if tag == "details" and "open" not in values:\n            return True\n',
        '        if tag in {"details", "dialog"} and "open" not in values:\n            return True\n',
    )

# ---------------------------------------------------------------------------
# 2. Browser HTML parsing: non-void self-closing syntax is a start tag.
#    This matters for <a ... /> and hidden containers such as <dialog />.
# ---------------------------------------------------------------------------
replace_once(
    registry,
    '''    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        return\n''',
    '''    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        tag = tag.lower()\n        if tag in HTML_VOID_TAGS:\n            return\n        # HTML browsers ignore the self-closing flag on non-void elements.\n        # Treat `<a ... />` as an opening anchor so its href remains navigable.\n        self.handle_starttag(tag, attrs)\n''',
)
replace_once(
    policing,
    '''    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        return\n''',
    '''    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        tag = tag.lower()\n        if tag in HTML_VOID_TAGS:\n            return\n        # HTML browsers ignore the self-closing flag on non-void elements.\n        self.handle_starttag(tag, attrs)\n''',
)

hidden_old = '''    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        parent_hidden = self.stack[-1][1] if self.stack else False\n        if _VisibleHTMLTextParser._is_hidden(tag, attrs) and not parent_hidden:\n            start = self._offset()\n            self.spans.append((start, self._tag_end(start)))\n'''
hidden_new = '''    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        tag = tag.lower()\n        if tag not in HTML_VOID_TAGS:\n            # Match browser tree construction: the slash does not close a\n            # non-void HTML element such as `<dialog />` or `<a />`.\n            self.handle_starttag(tag, attrs)\n            return\n        parent_hidden = self.stack[-1][1] if self.stack else False\n        if _VisibleHTMLTextParser._is_hidden(tag, attrs) and not parent_hidden:\n            start = self._offset()\n            self.spans.append((start, self._tag_end(start)))\n'''
replace_once(registry, hidden_old, hidden_new)
replace_once(policing, hidden_old, hidden_new)

# ---------------------------------------------------------------------------
# 3. Metadata labels: decode character references before label matching.
# ---------------------------------------------------------------------------
replace_once(
    registry,
    '''def _canonicalise_metadata_marker(line: str) -> str:\n    """Canonicalise equivalent visible strong-emphasis metadata labels."""\n    match = STRONG_METADATA_FIELD_PATTERN.match(line)\n    if match:\n        canonical = f"**{match.group('label')}:**"\n        return canonical + line[match.end():]\n\n    html_match = HTML_STRONG_METADATA_FIELD_PATTERN.match(line)\n    if html_match:\n        rendered_label = _visible_html_text(html_match.group(0)).strip()\n        if rendered_label.endswith(":"):\n            label = rendered_label[:-1].strip()\n            if label and ":" not in label:\n                canonical = f"**{label}:**"\n                return canonical + line[html_match.end():]\n    return line\n''',
    '''def _canonicalise_metadata_marker(line: str) -> str:\n    """Canonicalise equivalent browser-rendered metadata labels."""\n    # CommonMark resolves character references before rendering inline text.\n    # Decode the candidate line before matching so `DOI&#58;` is the same\n    # visible label as `DOI:` for uniqueness and scalar extraction.\n    decoded = html.unescape(line)\n    match = STRONG_METADATA_FIELD_PATTERN.match(decoded)\n    if match:\n        canonical = f"**{match.group('label')}:**"\n        return canonical + decoded[match.end():]\n\n    html_match = HTML_STRONG_METADATA_FIELD_PATTERN.match(decoded)\n    if html_match:\n        rendered_label = _visible_html_text(html_match.group(0)).strip()\n        if rendered_label.endswith(":"):\n            label = rendered_label[:-1].strip()\n            if label and ":" not in label:\n                canonical = f"**{label}:**"\n                return canonical + decoded[html_match.end():]\n    return line\n''',
)

# ---------------------------------------------------------------------------
# 4. Policing receipt: scope canonical metadata checks to the policing method.
# ---------------------------------------------------------------------------
replace_once(
    receipt,
    '''CANONICAL_METADATA_FIELDS = (\n    "country",\n    "jurisdiction",\n    "agency or institutional role",\n    "encounter type",\n    "source date or version",\n    "registered source identifiers or links",\n    "claim type",\n)\n''',
    '''CANONICAL_METADATA_FIELDS = (\n    "country",\n    "jurisdiction",\n    "agency or institutional role",\n    "encounter type",\n    "source date or version",\n    "registered source identifiers or links",\n    "claim type",\n)\n\nPOLICING_METHODOLOGY_HEADING = (\n    "## Australian and United States Policing-Context Experiment Design"\n)\nPOLICING_METADATA_INTRO = (\n    "Every implemented policing-context item must record, at minimum:"\n)\n''',
)
replace_once(
    receipt,
    '''def test_roadmap_policing_metadata_matches_canonical_minimum():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))\n    affirmative = set(_string_constants_in_tuple("AFFIRMATIVE_LINE_PREFIX_CLAUSES"))\n\n    assert "Every implemented item should record" not in roadmap\n    assert MANDATORY_ITEM_METADATA_SENTENCE in roadmap\n    assert MANDATORY_ITEM_METADATA_SENTENCE in required\n    assert MANDATORY_ITEM_METADATA_SENTENCE in affirmative\n    for field in CANONICAL_METADATA_FIELDS:\n        assert f"**{field}**" in methodology\n''',
    '''def test_roadmap_policing_metadata_matches_canonical_minimum():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))\n    affirmative = set(_string_constants_in_tuple("AFFIRMATIVE_LINE_PREFIX_CLAUSES"))\n\n    assert POLICING_METHODOLOGY_HEADING in methodology\n    start = methodology.index(POLICING_METHODOLOGY_HEADING)\n    end = methodology.index("\\n---\\n", start)\n    policing_methodology = methodology[start:end]\n\n    assert "Every implemented item should record" not in roadmap\n    assert MANDATORY_ITEM_METADATA_SENTENCE in roadmap\n    assert MANDATORY_ITEM_METADATA_SENTENCE in required\n    assert MANDATORY_ITEM_METADATA_SENTENCE in affirmative\n    assert POLICING_METADATA_INTRO in policing_methodology\n    for field in CANONICAL_METADATA_FIELDS:\n        assert f"**{field}**" in policing_methodology\n''',
)

# ---------------------------------------------------------------------------
# Focused regressions for all four review findings.
# ---------------------------------------------------------------------------
append_once(
    registry,
    "def test_entity_encoded_metadata_label_is_counted():",
    '''def test_entity_encoded_metadata_label_is_counted():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = (\n        "### Chey (2021), *Overcoming awkwardness: some interpretations of "\n        "Australian humour*"\n    )\n    section = _registered_sections(corpus)[entry]\n    mutated = section.replace(\n        "**Source type:**",\n        "**DOI&#58;** https://doi.org/10.0000/fabricated\\n\\n**Source type:**",\n        1,\n    )\n    with pytest.raises(AssertionError, match="exactly one mandatory field"):\n        _validate_registered_entry(entry, mutated)\n\n\ndef test_self_closing_anchor_source_destination_is_counted():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = "### *Black Comedy* (ABC, 2014-2020)"\n    section = _registered_sections(corpus)[entry]\n    pinned = "https://iview.abc.net.au/show/black-comedy"\n    mutated = section.replace(\n        pinned,\n        pinned + ' <a href="https://www.wikipedia.org/" />alternate</a>',\n        1,\n    )\n    with pytest.raises(AssertionError, match="registered-source destinations changed"):\n        _validate_registered_entry(entry, mutated)\n\n\ndef test_closed_dialog_cannot_hide_complete_governed_batch():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    batch = _registered_batch(corpus)\n    mutated = corpus.replace(batch, f"<dialog>\\n{batch}\\n</dialog>\\n", 1)\n    with pytest.raises(AssertionError, match="contains no entries"):\n        _validate_registry_corpus(mutated)\n\n\ndef test_open_dialog_keeps_governed_batch_visible():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    batch = _registered_batch(corpus)\n    mutated = corpus.replace(batch, f"<dialog open>\\n{batch}\\n</dialog>\\n", 1)\n    _validate_registry_corpus(mutated)\n''',
)

replace_once(
    policing,
    '''def test_policing_context_workstream_cannot_hide_in_closed_details():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    start = roadmap.index(WORKSTREAM_HEADING)\n    end = roadmap.index(WORKSTREAM_END, start)\n    section = roadmap[start:end]\n    hidden = f"<details>\\n{section}\\n</details>\\n"\n    mutated = roadmap[:start] + hidden + roadmap[end:]\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n''',
    '''@pytest.mark.parametrize("tag", ("details", "dialog"))\ndef test_policing_context_workstream_cannot_hide_in_closed_html_container(tag: str):\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    start = roadmap.index(WORKSTREAM_HEADING)\n    end = roadmap.index(WORKSTREAM_END, start)\n    section = roadmap[start:end]\n    hidden = f"<{tag}>\\n{section}\\n</{tag}>\\n"\n    mutated = roadmap[:start] + hidden + roadmap[end:]\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n''',
)

print("Applied browser-semantics and policing-scope repairs.")
