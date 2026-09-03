from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one repair anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, sentinel: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel in text:
        return
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + addition, encoding="utf-8")


registry = ROOT / "tests" / "test_research_reference_registry.py"
workstream_h = ROOT / "tests" / "test_workstream_h_methodology.py"
policing = ROOT / "tests" / "test_policing_context_roadmap.py"
receipt = ROOT / "tests" / "test_policing_contract_receipt.py"

# 1. SVG metadata such as <svg><title>...</title></svg> is accessibility/
# metadata content, not graphically rendered governance prose. Preserve the
# distinction in every visibility reducer that can satisfy a governance test.
replace_once(
    registry,
    '''    "section", "table", "ul",
})


class _VisibleHTMLTextParser(HTMLParser):
''',
    '''    "section", "table", "ul",
})

SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})


class _VisibleHTMLTextParser(HTMLParser):
''',
)
replace_once(
    registry,
    '''        inherited = self.stack[-1][1] if self.stack else False
        hidden = inherited or self._is_hidden(tag, attrs)
        if tag == "a" and not hidden:
''',
    '''        inherited = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _ in self.stack)
        )
        hidden = inherited or svg_metadata_hidden or self._is_hidden(tag, attrs)
        if tag == "a" and not hidden:
''',
)
replace_once(
    registry,
    '''        parent_hidden = self.stack[-1][1] if self.stack else False
        own_hidden = _VisibleHTMLTextParser._is_hidden(tag, attrs)
        hidden = parent_hidden or own_hidden

        if tag in HTML_VOID_TAGS:
''',
    '''        parent_hidden = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _, _ in self.stack)
        )
        own_hidden = svg_metadata_hidden or _VisibleHTMLTextParser._is_hidden(tag, attrs)
        hidden = parent_hidden or own_hidden

        if tag in HTML_VOID_TAGS:
''',
)

replace_once(
    workstream_h,
    '''HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class _VisibleHTMLTextParser(HTMLParser):
''',
    '''HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})


class _VisibleHTMLTextParser(HTMLParser):
''',
)
replace_once(
    workstream_h,
    '''    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        inherited = self.stack[-1][1] if self.stack else False
        self.stack.append((tag.lower(), inherited or self._is_hidden(tag, attrs)))
''',
    '''    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        inherited = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _ in self.stack)
        )
        self.stack.append(
            (tag, inherited or svg_metadata_hidden or self._is_hidden(tag, attrs))
        )
''',
)

replace_once(
    policing,
    '''NON_RENDERING_HTML_PATTERN = re.compile(
    r"<(script|style|template)\\b[^>]*>.*?</\\1\\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)


class _VisibleHTMLTextParser(HTMLParser):
''',
    '''NON_RENDERING_HTML_PATTERN = re.compile(
    r"<(script|style|template)\\b[^>]*>.*?</\\1\\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)
SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})


class _VisibleHTMLTextParser(HTMLParser):
''',
)
replace_once(
    policing,
    '''    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        inherited = self.stack[-1][1] if self.stack else False
        self.stack.append((tag.lower(), inherited or self._is_hidden(tag, attrs)))
''',
    '''    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        inherited = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _ in self.stack)
        )
        self.stack.append(
            (tag, inherited or svg_metadata_hidden or self._is_hidden(tag, attrs))
        )
''',
)
replace_once(
    policing,
    '''        tag = tag.lower()
        parent_hidden = self.stack[-1][1] if self.stack else False
        own_hidden = _VisibleHTMLTextParser._is_hidden(tag, attrs)
        hidden = parent_hidden or own_hidden
        start = self._offset()
''',
    '''        tag = tag.lower()
        parent_hidden = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _, _ in self.stack)
        )
        own_hidden = svg_metadata_hidden or _VisibleHTMLTextParser._is_hidden(tag, attrs)
        hidden = parent_hidden or own_hidden
        start = self._offset()
''',
)

# 2. Trans-Tasman methodology must use rendered heading boundaries, just as
# Workstream H and Workstream I already do.
replace_once(
    workstream_h,
    '''WORKSTREAM_H_HEADING = "### H. Slang density, register compression, and operational intelligibility"
WORKSTREAM_I_HEADING = "### I. Australian and United States policing-context transfer"
''',
    '''WORKSTREAM_H_HEADING = "### H. Slang density, register compression, and operational intelligibility"
WORKSTREAM_I_HEADING = "### I. Australian and United States policing-context transfer"
TRANS_TASMAN_METHODOLOGY_HEADING = "## Trans-Tasman and Slang/Operational Experiment Design"
POLICING_METHODOLOGY_HEADING = "## Australian and United States Policing-Context Experiment Design"
''',
)
replace_once(
    workstream_h,
    '''def _trans_tasman_methodology(text: str) -> str:
    start = text.index("## Trans-Tasman and Slang/Operational Experiment Design")
    end = text.index("## Australian and United States Policing-Context Experiment Design", start)
    return _visible_markdown_text(text[start:end])
''',
    '''def _trans_tasman_methodology(text: str) -> str:
    start, _ = _rendered_heading_span(text, TRANS_TASMAN_METHODOLOGY_HEADING)
    end, _ = _rendered_heading_span(text, POLICING_METHODOLOGY_HEADING)
    assert start < end, "rendered Trans-Tasman methodology boundary is invalid"
    return _visible_markdown_text(text[start:end])
''',
)

# 3. The policing methodology receipt must also locate its canonical section
# through unique rendered headings instead of raw source substrings.
replace_once(
    receipt,
    '''POLICING_METHODOLOGY_HEADING = (
    "## Australian and United States Policing-Context Experiment Design"
)
POLICING_METADATA_INTRO = (
''',
    '''POLICING_METHODOLOGY_HEADING = (
    "## Australian and United States Policing-Context Experiment Design"
)
POLICING_METHODOLOGY_END_HEADING = "## Scoring Philosophy"
POLICING_METADATA_INTRO = (
''',
)
replace_once(
    receipt,
    '''def _policing_methodology_section(methodology: str) -> str:
    assert POLICING_METHODOLOGY_HEADING in methodology
    start = methodology.index(POLICING_METHODOLOGY_HEADING)
    end = methodology.index("\\n---\\n", start)
    return methodology[start:end]
''',
    '''def _policing_methodology_section(methodology: str) -> str:
    policing_namespace = runpy.run_path(str(POLICING_TEST))
    structure = policing_namespace["_rendered_structure"](methodology)
    heading_span = policing_namespace["_visible_markdown_heading_span"]
    start, _ = heading_span(structure, POLICING_METHODOLOGY_HEADING)
    end, _ = heading_span(structure, POLICING_METHODOLOGY_END_HEADING)
    assert start < end, "rendered policing methodology boundary is invalid"
    return methodology[start:end]
''',
)

# 4. A rendered link inside a registered-source field is part of provenance.
# Do not silently filter non-HTTPS/unusable rendered links out of the exact set.
replace_once(
    registry,
    '''BARE_HTTPS_LINE_PATTERN = re.compile(
    r"(?m)^[ \\t]*(?:(?:[-+*]|\\d{1,9}[.)])[ \\t]+)?"
    r"(?P<url>https://\\S+)[ \\t]*$"
)
AUTOLINK_PATTERN = re.compile(r"<(?P<url>https://[^>\\s]+)>")
''',
    '''BARE_HTTPS_LINE_PATTERN = re.compile(
    r"(?m)^[ \\t]*(?:(?:[-+*]|\\d{1,9}[.)])[ \\t]+)?"
    r"(?P<url>https?://\\S+)[ \\t]*$"
)
AUTOLINK_PATTERN = re.compile(r"<(?P<url>https?://[^>\\s]+)>")
''',
)
replace_once(
    registry,
    '''def _usable_https_destinations(
    text: str,
    *,
    reference_scope: str | None = None,
) -> tuple[str, ...]:
''',
    '''def _require_rendered_https_destination(candidate: str) -> str:
    destination = _normalise_https_destination(candidate)
    assert destination is not None, (
        f"registered-source rendered link must be usable HTTPS: {candidate!r}"
    )
    return destination


def _usable_https_destinations(
    text: str,
    *,
    reference_scope: str | None = None,
) -> tuple[str, ...]:
''',
)
replace_once(
    registry,
    '''    for candidate in _visible_html_links(structure):
        destination = _normalise_https_destination(candidate)
        if destination is not None:
            destinations.append(destination)
''',
    '''    for candidate in _visible_html_links(structure):
        destinations.append(_require_rendered_https_destination(candidate))
''',
)
replace_once(
    registry,
    '''        destination = _normalise_https_destination(link.destination.strip("<>"))
        if destination is not None:
            destinations.append(destination)
''',
    '''        destinations.append(
            _require_rendered_https_destination(link.destination.strip("<>"))
        )
''',
)
replace_once(
    registry,
    '''    definitions: dict[str, str] = {}
    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(reference_structure):
        destination = _normalise_https_destination(
            match.group("destination").strip("<>")
        )
        if destination is None:
            continue
        definitions.setdefault(
            _normalise_reference_label(match.group("label")),
            destination,
        )
''',
    '''    definitions: dict[str, str] = {}
    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(reference_structure):
        definitions.setdefault(
            _normalise_reference_label(match.group("label")),
            match.group("destination").strip("<>"),
        )
''',
)
replace_once(
    registry,
    '''        destination = definitions.get(_normalise_reference_label(reference))
        if destination is not None:
            destinations.append(destination)
''',
    '''        candidate = definitions.get(_normalise_reference_label(reference))
        if candidate is not None:
            destinations.append(_require_rendered_https_destination(candidate))
''',
)
replace_once(
    registry,
    '''        destination = definitions.get(
            _normalise_reference_label(match.group("label"))
        )
        if destination is not None:
            destinations.append(destination)
''',
    '''        candidate = definitions.get(
            _normalise_reference_label(match.group("label"))
        )
        if candidate is not None:
            destinations.append(_require_rendered_https_destination(candidate))
''',
)
replace_once(
    registry,
    '''    for match in AUTOLINK_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)
''',
    '''    for match in AUTOLINK_PATTERN.finditer(without_links):
        destinations.append(
            _require_rendered_https_destination(match.group("url"))
        )
''',
)
replace_once(
    registry,
    '''    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)
''',
    '''    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destinations.append(
            _require_rendered_https_destination(match.group("url"))
        )
''',
)

append_once(
    registry,
    "def test_svg_title_cannot_hide_pinned_rights_boundary():",
    '''\n\ndef test_svg_title_cannot_hide_pinned_rights_boundary():
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[heading]
    rights_value = _scalar_value(section, RIGHTS_FIELD)
    assert rights_value in section
    mutated_section = section.replace(
        rights_value,
        f"<svg><title>{rights_value}</title></svg>",
        1,
    )
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


@pytest.mark.parametrize(
    "alternate",
    (
        "[alternate](http://www.wikipedia.org/)",
        "<http://www.wikipedia.org/>",
        '<a href="http://www.wikipedia.org/">alternate</a>',
        "http://www.wikipedia.org/",
    ),
)
def test_registered_source_rejects_rendered_non_https_links(alternate: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    source = "**Registered source:** https://iview.abc.net.au/show/black-comedy"
    assert source in corpus
    mutated = corpus.replace(source, source + "\\n\\n" + alternate, 1)
    with pytest.raises(AssertionError, match="usable HTTPS"):
        _validate_registry_corpus(mutated)
''',
)

append_once(
    workstream_h,
    "def test_trans_tasman_methodology_start_must_be_a_visible_heading():",
    '''\n\ndef test_trans_tasman_methodology_start_must_be_a_visible_heading():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    start = methodology.index(TRANS_TASMAN_METHODOLOGY_HEADING)
    end = methodology.index(POLICING_METHODOLOGY_HEADING, start)
    body = methodology[start + len(TRANS_TASMAN_METHODOLOGY_HEADING):end]
    mutated = (
        methodology[:start]
        + f'[boundary](# "{TRANS_TASMAN_METHODOLOGY_HEADING}")'
        + body
        + "\\n\\n"
        + TRANS_TASMAN_METHODOLOGY_HEADING
        + "\\n\\n"
        + methodology[end:]
    )
    section = _trans_tasman_methodology(mutated)
    assert "neither nationality nor first-language category acts as a proxy for comprehension" not in section
    assert "exact group-stereotyping wording must not be reproduced" not in section


def test_workstream_h_svg_title_does_not_supply_visible_safeguards():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    listener_clause = "nationality and first-language identity must not define the comparison cohorts"
    mutated_roadmap = roadmap.replace(
        listener_clause,
        f"<svg><title>{listener_clause}</title></svg>",
        1,
    )
    assert listener_clause not in _workstream_h(mutated_roadmap)

    methodology = METHODOLOGY.read_text(encoding="utf-8")
    stereotype_clause = "exact group-stereotyping wording must not be reproduced"
    mutated_methodology = methodology.replace(
        stereotype_clause,
        f"<svg><title>{stereotype_clause}</title></svg>",
        1,
    )
    assert stereotype_clause not in _trans_tasman_methodology(mutated_methodology)
''',
)

append_once(
    policing,
    "def test_policing_svg_title_does_not_supply_visible_source_gate():",
    '''\n\ndef test_policing_svg_title_does_not_supply_visible_source_gate():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "source-gated research proposal"
    mutated = roadmap.replace(
        clause,
        f"<svg><title>{clause}</title></svg>",
        1,
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)
''',
)

append_once(
    receipt,
    "def test_policing_methodology_start_must_be_a_visible_heading():",
    '''\n\ndef test_policing_methodology_start_must_be_a_visible_heading():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    start = methodology.index(POLICING_METHODOLOGY_HEADING)
    end = methodology.index(POLICING_METHODOLOGY_END_HEADING, start)
    body = methodology[start + len(POLICING_METHODOLOGY_HEADING):end]
    mutated = (
        methodology[:start]
        + f'[boundary](# "{POLICING_METHODOLOGY_HEADING}")'
        + body
        + "\\n\\n"
        + POLICING_METHODOLOGY_HEADING
        + "\\n\\n"
        + methodology[end:]
    )

    with pytest.raises(AssertionError):
        _assert_canonical_policing_metadata(mutated)
    with pytest.raises(AssertionError):
        _assert_canonical_high_stakes_gate(mutated)
''',
)

print("Applied four-head PR #4 hydra repair.")
