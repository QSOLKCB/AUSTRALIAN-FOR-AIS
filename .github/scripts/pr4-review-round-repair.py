from pathlib import Path

TEST = Path("tests/test_research_reference_registry.py")
CHANGELOG = Path("CHANGELOG.md")

text = TEST.read_text(encoding="utf-8")

old_patterns = '''LINK_REFERENCE_DEFINITION_PATTERN = re.compile(
    r"\\[[^\\]\\r\\n]+\\]:[ \\t]*(?:<[^>\\r\\n]+>|\\S+)"
    r"(?:[ \\t]+(?:\\\"[^\\\"\\r\\n]*\\\"|'[^'\\r\\n]*'|\\([^)]*\\)))?[ \\t]*"
)
'''
new_patterns = '''LINK_REFERENCE_DEFINITION_PATTERN = re.compile(
    r"(?m)^ {0,3}\\[(?P<label>[^\\]\\r\\n]+)\\]:[ \\t]*"
    r"(?P<destination><[^>\\r\\n]+>|[^\\s\\r\\n]+)"
    r"(?:[ \\t]+(?:\\\"[^\\\"\\r\\n]*\\\"|'[^'\\r\\n]*'|\\([^)]*\\)))?[ \\t]*$"
)
REFERENCE_LINK_PATTERN = re.compile(
    r"(?P<image>!?)\\[(?P<label>[^\\]\\r\\n]+)\\]"
    r"\\[(?P<reference>[^\\]\\r\\n]*)\\]"
)
SHORTCUT_REFERENCE_LINK_PATTERN = re.compile(
    r"(?P<image>!?)\\[(?P<label>[^\\]\\r\\n]+)\\]"
    r"(?![ \\t]*(?:\\(|\\[|:))"
)
'''
assert old_patterns in text, "reference-definition pattern anchor changed"
text = text.replace(old_patterns, new_patterns, 1)

visible_links_anchor = '''def _visible_html_links(text: str) -> tuple[str, ...]:
    """Return navigable href values from browser-visible raw HTML anchors."""
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ()
    return tuple(parser.hrefs)


'''
visibility_code = '''HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class _HiddenHTMLRegionParser(HTMLParser):
    """Locate browser-hidden HTML regions while preserving source offsets."""

    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=True)
        self.text = text
        self.stack: list[tuple[str, bool, int | None]] = []
        self.spans: list[tuple[int, int]] = []
        self.line_offsets = [0]
        for line in text.splitlines(keepends=True):
            self.line_offsets.append(self.line_offsets[-1] + len(line))

    def _offset(self) -> int:
        line, column = self.getpos()
        line_index = min(max(line - 1, 0), len(self.line_offsets) - 1)
        return min(self.line_offsets[line_index] + column, len(self.text))

    def _tag_end(self, start: int) -> int:
        close = self.text.find(">", start)
        return len(self.text) if close < 0 else close + 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        parent_hidden = self.stack[-1][1] if self.stack else False
        own_hidden = _VisibleHTMLTextParser._is_hidden(tag, attrs)
        hidden = parent_hidden or own_hidden
        start = self._offset()

        if tag in HTML_VOID_TAGS:
            if own_hidden and not parent_hidden:
                self.spans.append((start, self._tag_end(start)))
            return

        root_start = start if hidden and not parent_hidden else None
        self.stack.append((tag, hidden, root_start))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        parent_hidden = self.stack[-1][1] if self.stack else False
        if _VisibleHTMLTextParser._is_hidden(tag, attrs) and not parent_hidden:
            start = self._offset()
            self.spans.append((start, self._tag_end(start)))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] != tag:
                continue
            end = self._tag_end(self._offset())
            popped = self.stack[index:]
            del self.stack[index:]
            for _, _, root_start in popped:
                if root_start is not None:
                    self.spans.append((root_start, end))
            return

    def finish(self) -> None:
        for _, _, root_start in self.stack:
            if root_start is not None:
                self.spans.append((root_start, len(self.text)))
        self.stack.clear()


def _mask_hidden_html_regions(text: str) -> str:
    """Mask hidden HTML containers globally so visibility state survives slicing."""
    parser = _HiddenHTMLRegionParser(text)
    try:
        parser.feed(text)
        parser.close()
        parser.finish()
    except Exception:
        return _mask_non_newline(text)

    characters = list(text)
    for start, end in parser.spans:
        _mask_segment(characters, start, end)
    return "".join(characters)


'''
assert visible_links_anchor in text, "visible HTML link helper anchor changed"
text = text.replace(visible_links_anchor, visible_links_anchor + visibility_code, 1)

old_closer = '''def _is_fence_closer(line: str, state: FenceState) -> bool:
    """Return whether line closes the active fence."""
    logical = _fence_logical_line(line, state).rstrip(" \\t")
    return bool(
        re.fullmatch(
            rf"{re.escape(state.character)}{{{state.minimum_length},}}[ \\t]*",
            logical,
        )
    )
'''
new_closer = '''def _is_fence_closer(line: str, state: FenceState) -> bool:
    """Return whether line closes the active fence."""
    logical = _fence_logical_line(line, state)
    marker_index, indent_columns = _indent_columns(logical)
    if indent_columns > 3:
        return False
    candidate = logical[marker_index:].rstrip(" \\t")
    return bool(
        re.fullmatch(
            rf"{re.escape(state.character)}{{{state.minimum_length},}}[ \\t]*",
            candidate,
        )
    )
'''
assert old_closer in text, "fence closer anchor changed"
text = text.replace(old_closer, new_closer, 1)

old_destinations = '''def _usable_https_destinations(text: str) -> tuple[str, ...]:
    """Extract usable rendered links while excluding code and link titles."""
    structure = _structural_registry_text(text)
    destinations: list[str] = []

    for candidate in _visible_html_links(structure):
        destination = _normalise_https_destination(candidate)
        if destination is not None:
            destinations.append(destination)

    for match in MARKDOWN_LINK_PATTERN.finditer(structure):
        if match.group("image"):
            continue
        destination = _normalise_https_destination(
            match.group("destination").strip("<>")
        )
        if destination is not None:
            destinations.append(destination)

    without_links = MARKDOWN_LINK_PATTERN.sub("", structure)
    for match in AUTOLINK_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)

    without_links = AUTOLINK_PATTERN.sub("", without_links)
    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)

    return tuple(destinations)
'''
new_destinations = '''def _normalise_reference_label(value: str) -> str:
    """Apply CommonMark-style case-insensitive whitespace normalization."""
    return " ".join(html.unescape(value).split()).casefold()


def _usable_https_destinations(text: str) -> tuple[str, ...]:
    """Extract usable rendered links while excluding code and link titles."""
    structure = _mask_hidden_html_regions(_structural_registry_text(text))
    destinations: list[str] = []

    for candidate in _visible_html_links(structure):
        destination = _normalise_https_destination(candidate)
        if destination is not None:
            destinations.append(destination)

    for match in MARKDOWN_LINK_PATTERN.finditer(structure):
        if match.group("image"):
            continue
        destination = _normalise_https_destination(
            match.group("destination").strip("<>")
        )
        if destination is not None:
            destinations.append(destination)

    definitions: dict[str, str] = {}
    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(structure):
        destination = _normalise_https_destination(
            match.group("destination").strip("<>")
        )
        if destination is None:
            continue
        definitions.setdefault(
            _normalise_reference_label(match.group("label")),
            destination,
        )

    for match in REFERENCE_LINK_PATTERN.finditer(structure):
        if match.group("image"):
            continue
        reference = match.group("reference") or match.group("label")
        destination = definitions.get(_normalise_reference_label(reference))
        if destination is not None:
            destinations.append(destination)

    without_reference_links = REFERENCE_LINK_PATTERN.sub("", structure)
    for match in SHORTCUT_REFERENCE_LINK_PATTERN.finditer(without_reference_links):
        if match.group("image"):
            continue
        destination = definitions.get(
            _normalise_reference_label(match.group("label"))
        )
        if destination is not None:
            destinations.append(destination)

    without_links = MARKDOWN_LINK_PATTERN.sub("", without_reference_links)
    for match in AUTOLINK_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)

    without_links = AUTOLINK_PATTERN.sub("", without_links)
    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)

    return tuple(destinations)
'''
assert old_destinations in text, "usable-destination helper anchor changed"
text = text.replace(old_destinations, new_destinations, 1)

old_sections = '''def _registered_sections(corpus: str) -> dict[str, str]:
    batch = _registered_batch(corpus)
    rendered, structure = _markdown_views(batch)
    matches: list[tuple[int, int, str]] = [
        (match.start(), match.end(), match.group("heading"))
        for match in ENTRY_HEADING_PATTERN.finditer(structure)
    ]
    for match in HTML_ENTRY_HEADING_PATTERN.finditer(structure):
        visible_heading = _visible_inline_text(rendered[match.start():match.end()])
        if visible_heading:
            matches.append((match.start(), match.end(), f"### {visible_heading}"))
'''
new_sections = '''def _registered_sections(corpus: str) -> dict[str, str]:
    batch = _registered_batch(corpus)
    rendered, structure = _markdown_views(batch)
    visible_rendered = _mask_hidden_html_regions(rendered)
    visible_structure = _mask_hidden_html_regions(structure)
    matches: list[tuple[int, int, str]] = [
        (match.start(), match.end(), match.group("heading"))
        for match in ENTRY_HEADING_PATTERN.finditer(visible_structure)
    ]
    for match in HTML_ENTRY_HEADING_PATTERN.finditer(visible_structure):
        visible_heading = _visible_inline_text(
            visible_rendered[match.start():match.end()]
        )
        if visible_heading:
            matches.append((match.start(), match.end(), f"### {visible_heading}"))
'''
assert old_sections in text, "registered-sections anchor changed"
text = text.replace(old_sections, new_sections, 1)

append_tests = r'''


def test_hidden_html_container_cannot_hide_complete_governed_batch():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = corpus.index(BATCH_END, start)
    mutated = (
        corpus[:start]
        + "\n<div hidden>\n"
        + corpus[start:end]
        + "\n</div>\n"
        + corpus[end:]
    )
    with pytest.raises(AssertionError, match="registered post-Phase-2 batch contains no entries"):
        _validate_registry_corpus(mutated)


def test_reference_style_source_destination_is_included_in_pinned_set():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        "[alternate][extra]\n[extra]: https://www.wikipedia.org/\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize(
    "reference",
    ("[alternate][]", "[alternate]"),
)
def test_collapsed_and_shortcut_reference_sources_are_resolved(reference: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        f"{reference}\n[alternate]: https://www.wikipedia.org/\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_nested_fence_closer_allows_commonmark_indentation():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        "> ```\n> inert code\n>   ```\n"
        "> **DOI:** https://doi.org/10.0000/conflict\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)
'''
marker = "def test_trans_tasman_methodology_never_allows_exact_group_stereotype_wording"
# This marker lives in another test file; use an existing registry-tail test instead.
assert "def test_complete_registration_contract_is_pinned" in text, "registry tail anchor changed"
text = text.rstrip() + append_tests + "\n"

TEST.write_text(text, encoding="utf-8")

changelog = CHANGELOG.read_text(encoding="utf-8")
old_note = "- The Phase 2 pilot is an unannotated research fixture. No human annotation results, ethical approvals, or empirical agreement statistics are claimed until real pilot collection occurs."
new_note = old_note + "\n- Free-text pragmatic interpretations remain qualitative evidence and are not assigned a misleading exact-string IAA score."
assert old_note in changelog, "Phase 2 changelog note anchor changed"
assert "Free-text pragmatic interpretations remain qualitative evidence" not in changelog, "free-text changelog note already restored"
changelog = changelog.replace(old_note, new_note, 1)
CHANGELOG.write_text(changelog, encoding="utf-8")
