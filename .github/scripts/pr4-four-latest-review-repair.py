from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"{path}: replacement already present, skipping")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, sentinel: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel in text:
        print(f"{path}: regression already present, skipping")
        return
    path.write_text(text.rstrip() + "\n\n\n" + addition.strip() + "\n", encoding="utf-8")


path = Path("tests/test_research_reference_registry.py")

# 1. CommonMark backslash escapes are decoded before URL parsing.
replace_once(
    path,
    "import re\nfrom urllib.parse import urlparse\n",
    "import re\nimport string\nfrom urllib.parse import urlparse\n",
)
replace_once(
    path,
    '''def _normalise_https_destination(candidate: str) -> str | None:\n    value = html.unescape(candidate).strip().strip("<>").rstrip(".,;:!?")\n''',
    '''MARKDOWN_BACKSLASH_ESCAPE_PATTERN = re.compile(\n    rf"\\\\([{re.escape(string.punctuation)}])"\n)\n\n\ndef _normalise_https_destination(candidate: str) -> str | None:\n    value = html.unescape(candidate)\n    value = MARKDOWN_BACKSLASH_ESCAPE_PATTERN.sub(r"\\1", value)\n    value = value.strip().strip("<>").rstrip(".,;:!?")\n''',
)

# 2. Honor HTML5's implied paragraph end-tag behavior in both visibility parsers.
replace_once(
    path,
    '''NON_RENDERING_HTML_PATTERN = re.compile(\n    r"<(script|style|template)\\b[^>]*>.*?</\\1\\s*>",\n    flags=re.IGNORECASE | re.DOTALL,\n)\n\n\nclass _VisibleHTMLTextParser(HTMLParser):\n''',
    '''NON_RENDERING_HTML_PATTERN = re.compile(\n    r"<(script|style|template)\\b[^>]*>.*?</\\1\\s*>",\n    flags=re.IGNORECASE | re.DOTALL,\n)\n\nHTML_P_IMPLIED_END_START_TAGS = frozenset({\n    "address", "article", "aside", "blockquote", "div", "dl", "fieldset",\n    "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header",\n    "hgroup", "hr", "main", "menu", "nav", "ol", "p", "pre", "search",\n    "section", "table", "ul",\n})\n\n\nclass _VisibleHTMLTextParser(HTMLParser):\n''',
)
replace_once(
    path,
    '''    def __init__(self) -> None:\n        super().__init__(convert_charrefs=True)\n        self.parts: list[str] = []\n        self.hrefs: list[str] = []\n        self.stack: list[tuple[str, bool]] = []\n\n    @staticmethod\n''',
    '''    def __init__(self) -> None:\n        super().__init__(convert_charrefs=True)\n        self.parts: list[str] = []\n        self.hrefs: list[str] = []\n        self.stack: list[tuple[str, bool]] = []\n\n    def _apply_implied_paragraph_end(self, tag: str) -> None:\n        if tag not in HTML_P_IMPLIED_END_START_TAGS:\n            return\n        for index in range(len(self.stack) - 1, -1, -1):\n            if self.stack[index][0] == "p":\n                del self.stack[index:]\n                return\n\n    @staticmethod\n''',
)
replace_once(
    path,
    '''    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        inherited = self.stack[-1][1] if self.stack else False\n        hidden = inherited or self._is_hidden(tag, attrs)\n        if tag.lower() == "a" and not hidden:\n            for key, value in attrs:\n                if key.lower() == "href" and value:\n                    self.hrefs.append(value)\n                    break\n        self.stack.append((tag.lower(), hidden))\n''',
    '''    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        tag = tag.lower()\n        self._apply_implied_paragraph_end(tag)\n        inherited = self.stack[-1][1] if self.stack else False\n        hidden = inherited or self._is_hidden(tag, attrs)\n        if tag == "a" and not hidden:\n            for key, value in attrs:\n                if key.lower() == "href" and value:\n                    self.hrefs.append(value)\n                    break\n        self.stack.append((tag, hidden))\n''',
)
replace_once(
    path,
    '''    def _tag_end(self, start: int) -> int:\n        close = self.text.find(">", start)\n        return len(self.text) if close < 0 else close + 1\n\n    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        tag = tag.lower()\n        parent_hidden = self.stack[-1][1] if self.stack else False\n        own_hidden = _VisibleHTMLTextParser._is_hidden(tag, attrs)\n        hidden = parent_hidden or own_hidden\n        start = self._offset()\n''',
    '''    def _tag_end(self, start: int) -> int:\n        close = self.text.find(">", start)\n        return len(self.text) if close < 0 else close + 1\n\n    def _apply_implied_paragraph_end(self, tag: str, start: int) -> None:\n        if tag not in HTML_P_IMPLIED_END_START_TAGS:\n            return\n        for index in range(len(self.stack) - 1, -1, -1):\n            if self.stack[index][0] != "p":\n                continue\n            popped = self.stack[index:]\n            del self.stack[index:]\n            for _, _, root_start in popped:\n                if root_start is not None:\n                    self.spans.append((root_start, start))\n            return\n\n    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        tag = tag.lower()\n        start = self._offset()\n        self._apply_implied_paragraph_end(tag, start)\n        parent_hidden = self.stack[-1][1] if self.stack else False\n        own_hidden = _VisibleHTMLTextParser._is_hidden(tag, attrs)\n        hidden = parent_hidden or own_hidden\n''',
)

# 3. Locate registry boundaries only from actual visible Markdown heading lines.
replace_once(
    path,
    '''BATCH_HEADING = "## Registered post-Phase-2 expansion batch"\nBATCH_END = "## Priority A: adversarial pragmatics"\nCONTRACT_HEADING = "## Registration contract for new sources"\n''',
    '''STATUS_HEADING = "## Status"\nSOURCE_USE_HEADING = "## Source-use rules"\nREDISTRIBUTION_INVARIANT = "RESEARCH REFERENCE != REDISTRIBUTABLE DATA"\nBATCH_HEADING = "## Registered post-Phase-2 expansion batch"\nBATCH_END = "## Priority A: adversarial pragmatics"\nCONTRACT_HEADING = "## Registration contract for new sources"\n''',
)
replace_once(
    path,
    '''def _registered_batch(corpus: str) -> str:\n    rendered, structure = _markdown_views(corpus)\n    start = structure.index(BATCH_HEADING) + len(BATCH_HEADING)\n    end = structure.index(BATCH_END, start)\n    return rendered[start:end]\n''',
    '''def _visible_markdown_heading_span(structure: str, heading: str) -> tuple[int, int]:\n    """Return the unique browser-visible Markdown heading span with preserved offsets."""\n    visible_structure = _mask_hidden_html_regions(structure)\n    matches: list[tuple[int, int]] = []\n    offset = 0\n    for raw_line in visible_structure.splitlines(keepends=True):\n        line = raw_line.rstrip("\\r\\n")\n        logical, is_code = _strip_composed_container_prefixes(line)\n        if not is_code and logical.strip(" \\t") == heading:\n            matches.append((offset, offset + len(line)))\n        offset += len(raw_line)\n    assert len(matches) == 1, (\n        f"expected exactly one rendered heading {heading!r}, found {len(matches)}"\n    )\n    return matches[0]\n\n\ndef _registered_batch(corpus: str) -> str:\n    rendered, structure = _markdown_views(corpus)\n    _, start = _visible_markdown_heading_span(structure, BATCH_HEADING)\n    end, _ = _visible_markdown_heading_span(structure, BATCH_END)\n    assert start < end, "rendered governed batch boundaries are out of order"\n    return rendered[start:end]\n''',
)

# 4. Scope contract/status checks to visible rendered heading-delimited sections.
replace_once(
    path,
    '''def _validate_registry_corpus(corpus: str) -> None:\n    rendered, structure = _markdown_views(corpus)\n    assert CONTRACT_HEADING in structure, "rendered registration contract is missing"\n    contract_start = structure.index(CONTRACT_HEADING)\n    assert BATCH_HEADING in structure[contract_start:], "rendered governed batch heading is missing"\n    contract_end = structure.index(BATCH_HEADING, contract_start)\n    contract_section = structure[contract_start:contract_end]\n    assert CONTRACT_SENTENCE in contract_section, "rendered registration contract is incomplete"\n    visible_contract = _visible_inline_text(rendered[contract_start:contract_end])\n    actual_contract_hash = hashlib.sha256(visible_contract.encode("utf-8")).hexdigest()\n    assert actual_contract_hash == REGISTRATION_CONTRACT_HASH, (\n        "rendered registration contract changed or was weakened: "\n        f"expected hash {REGISTRATION_CONTRACT_HASH!r}, got {actual_contract_hash!r}"\n    )\n    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in structure\n\n    sections = _registered_sections(corpus)\n''',
    '''def _validate_registry_corpus(corpus: str) -> None:\n    rendered, structure = _markdown_views(corpus)\n    contract_start, _ = _visible_markdown_heading_span(structure, CONTRACT_HEADING)\n    contract_end, _ = _visible_markdown_heading_span(structure, BATCH_HEADING)\n    assert contract_start < contract_end, "rendered registration contract boundaries are out of order"\n    contract_section = structure[contract_start:contract_end]\n    assert CONTRACT_SENTENCE in contract_section, "rendered registration contract is incomplete"\n    visible_contract = _visible_inline_text(rendered[contract_start:contract_end])\n    actual_contract_hash = hashlib.sha256(visible_contract.encode("utf-8")).hexdigest()\n    assert actual_contract_hash == REGISTRATION_CONTRACT_HASH, (\n        "rendered registration contract changed or was weakened: "\n        f"expected hash {REGISTRATION_CONTRACT_HASH!r}, got {actual_contract_hash!r}"\n    )\n\n    status_start, _ = _visible_markdown_heading_span(structure, STATUS_HEADING)\n    status_end, _ = _visible_markdown_heading_span(structure, SOURCE_USE_HEADING)\n    assert status_start < status_end, "rendered Status/source-use boundaries are out of order"\n    visible_status = _visible_inline_text(rendered[status_start:status_end])\n    assert REDISTRIBUTION_INVARIANT in visible_status, (\n        "redistribution invariant must remain browser-visible inside the Status section"\n    )\n\n    sections = _registered_sections(corpus)\n''',
)

append_once(
    path,
    "def test_markdown_escaped_source_destination_is_pinned():",
    r'''def test_markdown_escaped_source_destination_is_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    source = "**Registered source:** https://iview.abc.net.au/show/black-comedy"
    mutated = corpus.replace(
        source,
        source + "\n[alternate](https\\://www.wikipedia.org/)",
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registry_corpus(mutated)


def test_implied_paragraph_end_cannot_hide_duplicate_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    doi = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"
    mutated = corpus.replace(
        doi,
        doi
        + "\n\n<p hidden>masked<p><strong>DOI:</strong> "
        + "https://doi.org/10.0000/fabricated</p></p>",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registry_corpus(mutated)


def test_registry_batch_end_must_be_a_visible_heading():
    corpus = CORPUS.read_text(encoding="utf-8")
    mutated = corpus.replace(
        BATCH_END,
        (
            f'[boundary](# "{BATCH_END}")\n\n'
            "### Fabricated ungoverned reference\n\n"
            "placeholder provenance text\n\n"
            f"{BATCH_END}"
        ),
        1,
    )
    with pytest.raises(AssertionError, match="explicit pinned source contract"):
        _validate_registry_corpus(mutated)


def test_redistribution_invariant_must_be_visible_in_status_section():
    corpus = CORPUS.read_text(encoding="utf-8")
    mutated = corpus.replace(
        "> RESEARCH REFERENCE != REDISTRIBUTABLE DATA",
        "> <span hidden>RESEARCH REFERENCE != REDISTRIBUTABLE DATA</span>",
        1,
    )
    with pytest.raises(AssertionError, match="redistribution invariant"):
        _validate_registry_corpus(mutated)
''',
)

print("Applied four latest PR4 review repairs.")
