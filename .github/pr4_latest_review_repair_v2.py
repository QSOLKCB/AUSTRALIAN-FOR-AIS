from __future__ import annotations

from pathlib import Path


REGISTRY = Path("tests/test_research_reference_registry.py")
POLICING = Path("tests/test_policing_context_roadmap.py")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one match, found {count}"
    return text.replace(old, new, 1)


def patch_registry() -> None:
    text = REGISTRY.read_text(encoding="utf-8")
    original = text

    text = replace_once(
        text,
        'RAW_HTML_BLOCK_TAGS = frozenset({"pre", "script", "style", "textarea"})\n',
        '''RAW_HTML_BLOCK_TAGS = frozenset({"pre", "script", "style", "textarea"})
RAW_HTML_TYPE6_TAGS = frozenset({
    "address", "article", "aside", "base", "basefont", "blockquote", "body",
    "caption", "center", "col", "colgroup", "dd", "details", "dialog", "dir",
    "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
    "frame", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head",
    "header", "hr", "html", "iframe", "legend", "li", "link", "main", "menu",
    "menuitem", "nav", "noframes", "ol", "optgroup", "option", "p", "param",
    "search", "section", "summary", "table", "tbody", "td", "tfoot", "th",
    "thead", "title", "tr", "track", "ul",
})
''',
        label="type-6 raw HTML tag set",
    )

    text = replace_once(
        text,
        '''GOVERNED_REPLACEMENT_HTML_PATTERN = re.compile(
    r"<(?:object|embed|iframe|canvas)\\b",
    flags=re.IGNORECASE,
)
''',
        '''GOVERNED_REPLACEMENT_HTML_PATTERN = re.compile(
    r"<(?:object|embed|iframe|canvas)\\b",
    flags=re.IGNORECASE,
)
GOVERNED_DELETION_HTML_PATTERN = re.compile(
    r"<(?:del|s|strike)\\b",
    flags=re.IGNORECASE,
)
''',
        label="semantic deletion pattern",
    )

    text = replace_once(
        text,
        "        self.stack.append((tag, hidden, inert))\n",
        '''        if tag in HTML_VOID_TAGS:
            return
        self.stack.append((tag, hidden, inert))
''',
        label="void element visible-parser state",
    )

    visibility_helpers = '''def _winning_inline_visibility(style: str) -> str | None:
    """Return the winning inline visibility declaration after CSS normalization."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style)
    winner: tuple[bool, str] | None = None
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        raw_name, raw_value = declaration.split(":", 1)
        name = _decode_css_escapes(raw_name.strip()).casefold()
        if name != "visibility":
            continue
        decoded_value = _decode_css_escapes(raw_value.strip()).casefold()
        important = re.search(r"\\s*!important\\s*$", decoded_value) is not None
        value = re.sub(r"\\s*!important\\s*$", "", decoded_value).strip()
        if winner is None or (important and not winner[0]) or important == winner[0]:
            winner = (important, value)
    return winner[1] if winner is not None else None


class _VisibilityOverrideDetector(HTMLParser):
    """Detect inherited CSS visibility restored by a descendant."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.found = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        inherited_hidden = self.stack[-1][1] if self.stack else False
        values = _first_html_attribute_values(attrs)
        visibility = _winning_inline_visibility(values.get("style", ""))
        if inherited_hidden and visibility == "visible":
            self.found = True
        if visibility in {"hidden", "collapse"}:
            current_hidden = True
        elif visibility == "visible":
            current_hidden = False
        else:
            current_hidden = inherited_hidden
        if tag not in HTML_VOID_TAGS:
            self.stack.append((tag, current_hidden))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() not in HTML_VOID_TAGS:
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return


def _contains_descendant_visibility_override(text: str) -> bool:
    detector = _VisibilityOverrideDetector()
    try:
        detector.feed(text)
        detector.close()
    except Exception:
        return True
    return detector.found


'''
    text = replace_once(
        text,
        "HTML_VOID_TAGS = {\n",
        visibility_helpers + "HTML_VOID_TAGS = {\n",
        label="visibility override detector",
    )

    type6_helper = '''def _contains_markdown_structure_in_type6_raw_html(text: str) -> bool:
    """Detect Markdown headings made inert by a CommonMark type-6 raw HTML block.

    The registry intentionally supports visible raw HTML headings and containers, so
    we do not globally mask type-6 HTML. Instead, fail closed when such a block
    contains Markdown heading syntax before its terminating blank line. This is the
    ambiguity that can fabricate registry boundaries during heading discovery.
    """
    structure = _structural_registry_text(text)
    in_type6 = False
    for raw_line in structure.splitlines():
        logical, is_code = _strip_composed_container_prefixes(raw_line)
        candidate = logical.lstrip(" \\t")
        if is_code:
            continue
        if in_type6:
            if not candidate.strip():
                in_type6 = False
                continue
            if re.match(r"#{2,3}(?:[ \\t]+|$)", candidate):
                return True
            continue
        tag_match = re.match(
            r"</?(?P<tag>[A-Za-z][A-Za-z0-9-]*)(?=[ \\t/>]|$)",
            candidate,
        )
        if tag_match is not None and tag_match.group("tag").lower() in RAW_HTML_TYPE6_TAGS:
            in_type6 = True
    return False


'''
    text = replace_once(
        text,
        "def _matching_backtick_run_start(\n",
        type6_helper + "def _matching_backtick_run_start(\n",
        label="type-6 governance detector",
    )

    text = replace_once(
        text,
        '        parts.append(text[run_end:close].strip(" "))\n',
        '''        # Code-span contents are literal text. Escape them before the HTML
        # visibility pass so markup characters render as characters rather than
        # being reinterpreted as live HTML elements.
        parts.append(html.escape(text[run_end:close].strip(" "), quote=False))
''',
        label="literal code-span HTML",
    )

    text = replace_once(
        text,
        '''        if GOVERNED_REPLACEMENT_HTML_PATTERN.search(logical):
            found.add("replacement")
''',
        '''        if GOVERNED_REPLACEMENT_HTML_PATTERN.search(logical):
            found.add("replacement")
        if GOVERNED_DELETION_HTML_PATTERN.search(logical):
            found.add("deletion")
''',
        label="semantic deletion detection",
    )

    text = replace_once(
        text,
        '''    forbidden_html = _forbidden_governed_html_constructs(section)
    assert "replacement" not in forbidden_html, (
''',
        '''    forbidden_html = _forbidden_governed_html_constructs(section)
    assert "deletion" not in forbidden_html, (
        f"{entry} contains semantic deletion HTML (del/s/strike), which is not permitted "
        "in governed entries because deleted text cannot satisfy visible integrity"
    )
    assert "replacement" not in forbidden_html, (
''',
        label="semantic deletion integrity guard",
    )

    text = replace_once(
        text,
        '''def _validate_registry_corpus(corpus: str) -> None:
    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)
''',
        '''def _validate_registry_corpus(corpus: str) -> None:
    assert not _contains_markdown_structure_in_type6_raw_html(corpus), (
        "registry contains Markdown governance structure inside a CommonMark type-6 "
        "raw HTML block; this ambiguous structure is rejected fail closed"
    )
    structural_for_visibility = _structural_registry_text(corpus)
    assert not _contains_descendant_visibility_override(structural_for_visibility), (
        "registry contains a visibility:hidden/collapse ancestor with a descendant "
        "visibility:visible override; this ambiguous visual nesting is rejected fail closed"
    )
    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)
''',
        label="new corpus guards",
    )

    marker = "def test_latest_review_rendering_semantics_regressions():"
    assert marker not in text
    text += r'''


def test_latest_review_rendering_semantics_regressions():
    corpus = CORPUS.read_text(encoding="utf-8")

    mutated = corpus.replace(
        BATCH_HEADING,
        f"<div>\n{BATCH_HEADING}\n</div>",
        1,
    )
    with pytest.raises(AssertionError, match="type-6 raw HTML block"):
        _validate_registry_corpus(mutated)

    entry = next(
        heading for heading in EXPECTED_GOVERNED_ENTRIES if heading.startswith("### Chey")
    )
    section = _registered_sections(corpus)[entry]
    visibility_override = (
        '<span style="visibility:hidden">masked'
        '<span style="visibility:visible"><strong>DOI:</strong> '
        'https://doi.org/10.0000/fabricated</span></span>'
    )
    mutated = corpus.replace(section, section + "\n" + visibility_override + "\n", 1)
    with pytest.raises(AssertionError, match="visibility:hidden/collapse"):
        _validate_registry_corpus(mutated)

    assert _visible_html_text("<img hidden>visible remainder") == "visible remainder"


def test_semantic_deletion_markup_cannot_supply_pinned_governance():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    rights = str(ENTRY_CONTRACTS[entry][RIGHTS_FIELD])
    assert rights in section
    for tag in ("del", "s", "strike"):
        mutated_section = section.replace(rights, f"<{tag}>{rights}</{tag}>", 1)
        mutated = corpus.replace(section, mutated_section, 1)
        with pytest.raises(AssertionError, match="semantic deletion HTML"):
            _validate_registry_corpus(mutated)


def test_html_literals_inside_code_spans_remain_literal_integrity_text():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    rights = str(ENTRY_CONTRACTS[entry][RIGHTS_FIELD])
    assert "article" in rights
    assert rights in section
    corrupted = rights.replace("article", "`<span>article</span>`", 1)
    mutated_section = section.replace(rights, corrupted, 1)
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)
'''

    assert text != original
    REGISTRY.write_text(text, encoding="utf-8")


def patch_policing() -> None:
    text = POLICING.read_text(encoding="utf-8")
    original = text

    text = replace_once(
        text,
        '''        self.stack.append(
            (tag, inherited or svg_metadata_hidden or self._is_hidden(tag, attrs))
        )
''',
        '''        if tag in HTML_VOID_TAGS:
            return
        self.stack.append(
            (tag, inherited or svg_metadata_hidden or self._is_hidden(tag, attrs))
        )
''',
        label="policing void element state",
    )

    text = replace_once(
        text,
        '''    visible = _visible_html_text(visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
''',
        '''    # HTMLParser(convert_charrefs=True) already performs the browser's one
    # character-reference decoding pass. A second html.unescape() would turn
    # literal entity-looking text into content the browser never displays.
    visible = _visible_html_text(visible)
    visible = visible.replace("**", "").replace("__", "")
''',
        label="single entity decode in policing visibility",
    )

    marker = "def test_policing_visibility_decodes_character_references_once():"
    assert marker not in text
    text += r'''


def test_policing_visibility_decodes_character_references_once():
    assert _visible_text("&amp;#69;very implemented item must record") == (
        "&#69;very implemented item must record"
    )

    roadmap = ROADMAP.read_text(encoding="utf-8")
    sentence = REQUIRED_CLAUSES[3]
    assert "Every implemented item must record" in sentence
    encoded = sentence.replace("Every", "&amp;#69;very", 1)
    assert sentence in roadmap
    mutated = roadmap.replace(sentence, encoded, 1)
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)


def test_policing_visible_html_void_elements_do_not_hide_following_text():
    assert _visible_html_text("<img hidden>visible safeguard") == "visible safeguard"
'''

    assert text != original
    POLICING.write_text(text, encoding="utf-8")


def main() -> None:
    patch_registry()
    patch_policing()


if __name__ == "__main__":
    main()
