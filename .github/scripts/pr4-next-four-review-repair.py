from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: str, sentinel: str, block: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if sentinel in text:
        return
    target.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


REGISTRY = "tests/test_research_reference_registry.py"
POLICING = "tests/test_policing_context_roadmap.py"
WORKSTREAM_H = "tests/test_workstream_h_methodology.py"

# 1. CSS comments are whitespace to CSS parsing and cannot conceal display:none.
style_old = '''        if values.get("aria-hidden", "").strip().lower() == "true":
            return True
        style = re.sub(r"\\s+", "", values.get("style", "").lower())
        return "display:none" in style or "visibility:hidden" in style
'''
style_new = '''        if values.get("aria-hidden", "").strip().lower() == "true":
            return True
        style = re.sub(
            r"/\\*.*?\\*/",
            "",
            values.get("style", "").lower(),
            flags=re.DOTALL,
        )
        style = re.sub(r"\\s+", "", style)
        return "display:none" in style or "visibility:hidden" in style
'''
for path in (REGISTRY, POLICING, WORKSTREAM_H):
    replace_once(path, style_old, style_new, f"{path} CSS visibility")

# 2. A raw HTML anchor may wrap the rendered strong metadata marker.
html_pattern_old = '''HTML_STRONG_METADATA_FIELD_PATTERN = re.compile(
    r"^<(?P<tag>strong|b)\\b(?P<attrs>[^>]*)>"
    r"(?P<body>.*?)</(?P=tag)>(?=$|[ \\t])",
    flags=re.IGNORECASE,
)
HTML_TAG_PATTERN = re.compile(
'''
html_pattern_new = '''HTML_STRONG_METADATA_FIELD_PATTERN = re.compile(
    r"^<(?P<tag>strong|b)\\b(?P<attrs>[^>]*)>"
    r"(?P<body>.*?)</(?P=tag)>(?=$|[ \\t])",
    flags=re.IGNORECASE,
)
HTML_LEADING_ANCHOR_PATTERN = re.compile(
    r"^<a\\b[^>]*>(?P<body>.*?)</a>(?=$|[ \\t])",
    flags=re.IGNORECASE | re.DOTALL,
)
HTML_TAG_PATTERN = re.compile(
'''
replace_once(REGISTRY, html_pattern_old, html_pattern_new, "HTML anchor metadata pattern")

canonical_old = '''    paragraph_wrapper = re.match(r"<p\\b[^>]*>[ \\t]*", decoded, flags=re.IGNORECASE)
    if paragraph_wrapper:
        decoded = decoded[paragraph_wrapper.end():]
    inline_links = _markdown_inline_links(decoded)
'''
canonical_new = '''    paragraph_wrapper = re.match(r"<p\\b[^>]*>[ \\t]*", decoded, flags=re.IGNORECASE)
    if paragraph_wrapper:
        decoded = decoded[paragraph_wrapper.end():]
    html_anchor = HTML_LEADING_ANCHOR_PATTERN.match(decoded)
    if html_anchor:
        anchor_body = html_anchor.group("body").strip(" \\t")
        if HTML_STRONG_METADATA_FIELD_PATTERN.match(anchor_body):
            decoded = anchor_body + decoded[html_anchor.end():]
    inline_links = _markdown_inline_links(decoded)
'''
replace_once(REGISTRY, canonical_old, canonical_new, "raw HTML anchor metadata canonicalization")

# 3. Workstream I boundaries must be unique browser-visible headings.
workstream_constants_old = '''WORKSTREAM_HEADING = "### I. Australian and United States policing-context transfer"
WORKSTREAM_END = "\\n---\\n\\n## Phase 3"
'''
workstream_constants_new = '''WORKSTREAM_HEADING = "### I. Australian and United States policing-context transfer"
WORKSTREAM_END = "\\n---\\n\\n## Phase 3"
WORKSTREAM_END_HEADING = "## Phase 3"
'''
replace_once(POLICING, workstream_constants_old, workstream_constants_new, "policing end heading constant")

policing_renderer_old = '''def _rendered_policing_workstream(roadmap: str) -> str:
    structure = _rendered_structure(roadmap)
    assert WORKSTREAM_HEADING in structure, "rendered policing workstream is missing"
    start = structure.index(WORKSTREAM_HEADING)
    end = structure.index(WORKSTREAM_END, start)
    visible_structure = _mask_hidden_html_regions(structure)
    return visible_structure[start:end]
'''
policing_renderer_new = '''def _visible_markdown_heading_span(structure: str, heading: str) -> tuple[int, int]:
    """Return the unique browser-visible Markdown heading span with preserved offsets."""
    visible_structure = _mask_hidden_html_regions(structure)
    matches: list[tuple[int, int]] = []
    offset = 0
    for raw_line in visible_structure.splitlines(keepends=True):
        line = raw_line.rstrip("\\r\\n")
        logical, is_code, _ = _parse_fence_container_prefixes(line)
        if not is_code and logical.strip(" \\t") == heading:
            matches.append((offset, offset + len(raw_line)))
        offset += len(raw_line)
    assert len(matches) == 1, (
        f"expected exactly one rendered heading {heading!r}, found {len(matches)}"
    )
    return matches[0]


def _rendered_policing_workstream(roadmap: str) -> str:
    structure = _rendered_structure(roadmap)
    try:
        start, _ = _visible_markdown_heading_span(structure, WORKSTREAM_HEADING)
    except AssertionError as exc:
        raise AssertionError("rendered policing workstream is missing") from exc
    end, _ = _visible_markdown_heading_span(structure, WORKSTREAM_END_HEADING)
    assert start < end, "rendered policing workstream boundary is invalid"
    visible_structure = _mask_hidden_html_regions(structure)
    return visible_structure[start:end]
'''
replace_once(POLICING, policing_renderer_old, policing_renderer_new, "visible policing heading boundaries")

# 4. Workstream H must accept the valid newline between destination and title.
workstream_h_link_old = '''def _inline_link_closing_paren(text: str, start: int) -> int | None:
    depth = 1
    cursor = start + 1
    quote: str | None = None
    angle = False
    while cursor < len(text):
        character = text[cursor]
        if character in "\\r\\n":
            return None
        if character == "\\\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if quote is not None:
            if character == quote:
                quote = None
            cursor += 1
            continue
        if angle:
            if character == ">":
                angle = False
            cursor += 1
            continue
        if character in {"\\\"", "'"}:
            quote = character
            cursor += 1
            continue
        if character == "<":
            angle = True
            cursor += 1
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None
'''
workstream_h_link_new = '''def _inline_link_closing_paren(text: str, start: int) -> int | None:
    depth = 1
    cursor = start + 1
    quote: str | None = None
    angle = False
    top_level_space = False
    while cursor < len(text):
        character = text[cursor]
        if character == "\\\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if quote is not None:
            if character == quote:
                quote = None
            cursor += 1
            continue
        if angle:
            if character in "\\r\\n":
                return None
            if character == ">":
                angle = False
            cursor += 1
            continue
        if depth == 1 and character in " \\t\\r\\n":
            top_level_space = True
            cursor += 1
            continue
        if character in "\\r\\n":
            return None
        if depth == 1 and top_level_space and character in {"\\\"", "'"}:
            quote = character
            cursor += 1
            continue
        if depth == 1 and not top_level_space and character == "<":
            angle = True
            cursor += 1
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _inline_link_destination(inner: str) -> str | None:
    """Validate the destination/title split using CommonMark inline-link rules."""
    value = inner.lstrip(" \\t\\r\\n")
    if not value:
        return None
    if value.startswith("<"):
        close = value.find(">", 1)
        if close < 0:
            return None
        destination = value[1:close]
        remainder = value[close + 1:].strip()
    else:
        cursor = 0
        depth = 0
        while cursor < len(value):
            character = value[cursor]
            if character == "\\\\" and cursor + 1 < len(value):
                cursor += 2
                continue
            if character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    return None
                depth -= 1
            elif character in " \\t\\r\\n" and depth == 0:
                break
            cursor += 1
        if depth != 0:
            return None
        destination = value[:cursor]
        remainder = value[cursor:].strip()
    if not destination:
        return None
    if remainder:
        quoted = (
            len(remainder) >= 2
            and remainder[0] in {"\\\"", "'"}
            and remainder[-1] == remainder[0]
        )
        parenthesized = (
            len(remainder) >= 2
            and remainder[0] == "("
            and remainder[-1] == ")"
        )
        if not (quoted or parenthesized):
            return None
    return destination
'''
replace_once(WORKSTREAM_H, workstream_h_link_old, workstream_h_link_new, "Workstream H multiline inline-link parser")

workstream_h_replace_old = '''        paren_end = _inline_link_closing_paren(text, label_end + 1)
        if paren_end is None:
            parts.append(text[cursor:bracket + 1])
            cursor = bracket + 1
            continue
        image = (
'''
workstream_h_replace_new = '''        paren_start = label_end + 1
        paren_end = _inline_link_closing_paren(text, paren_start)
        if (
            paren_end is None
            or _inline_link_destination(text[paren_start + 1:paren_end]) is None
        ):
            parts.append(text[cursor:bracket + 1])
            cursor = bracket + 1
            continue
        image = (
'''
replace_once(WORKSTREAM_H, workstream_h_replace_old, workstream_h_replace_new, "Workstream H inline-link destination validation")

workstream_h_cases_old = '''        f"<dialog />{listener_clause}</dialog>",
        f'[placeholder](# "{listener_clause}")',
'''
workstream_h_cases_new = '''        f"<dialog />{listener_clause}</dialog>",
        f'<span style="display:/**/none">{listener_clause}</span>',
        f'[placeholder](# "{listener_clause}")',
        f'[placeholder](#\\n"{listener_clause}")',
'''
replace_once(WORKSTREAM_H, workstream_h_cases_old, workstream_h_cases_new, "Workstream H hidden safeguard mutations")

append_once(
    REGISTRY,
    "def test_css_comment_cannot_hide_complete_governed_batch",
    '''
def test_css_comment_cannot_hide_complete_governed_batch():
    corpus = CORPUS.read_text(encoding="utf-8")
    batch = _registered_batch(corpus)
    mutated = corpus.replace(
        batch,
        f'<div style="display:/**/none">\\n{batch}\\n</div>\\n',
        1,
    )
    with pytest.raises(AssertionError, match="contains no entries"):
        _validate_registry_corpus(mutated)


def test_html_anchor_wrapped_metadata_label_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    doi = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"
    mutated = corpus.replace(
        doi,
        doi
        + '\\n\\n<a href="#field"><strong>DOI:</strong></a> '
        + "https://doi.org/10.0000/fabricated",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registry_corpus(mutated)
''',
)

append_once(
    POLICING,
    "def test_policing_workstream_start_must_be_a_visible_heading",
    '''
def test_policing_workstream_start_must_be_a_visible_heading():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_HEADING)
    end = roadmap.index(WORKSTREAM_END, start)
    body = roadmap[start + len(WORKSTREAM_HEADING):end]
    mutated = (
        roadmap[:start]
        + f'[boundary](# "{WORKSTREAM_HEADING}")'
        + body
        + "\\n"
        + WORKSTREAM_HEADING
        + roadmap[end:]
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)
''',
)

print("Applied next four PR4 review repairs.")
