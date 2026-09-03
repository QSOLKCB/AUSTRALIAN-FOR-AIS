from __future__ import annotations

from pathlib import Path


PATH = Path("tests/test_research_reference_registry.py")
text = PATH.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    text = text.replace(old, new, 1)


def replace_block(start_marker: str, end_marker: str, replacement: str, label: str) -> None:
    global text
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"{label}: start marker missing")
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"{label}: end marker missing")
    text = text[:start] + replacement + text[end:]


if "NON_RENDERING_HTML_PATTERN = re.compile(" not in text:
    replace_once(
        '''HTML_TAG_PATTERN = re.compile(
    r"</?[A-Za-z][^>]*>|<![A-Za-z][^>]*>|<\\?[\\s\\S]*?\\?>"
)
''',
        '''HTML_TAG_PATTERN = re.compile(
    r"</?[A-Za-z][^>]*>|<![A-Za-z][^>]*>|<\\?[\\s\\S]*?\\?>"
)
NON_RENDERING_HTML_PATTERN = re.compile(
    r"<(script|style|template)\\b[^>]*>.*?</\\1\\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)
''',
        "non-rendering HTML constant",
    )

if "def _mask_multiline_code_spans" not in text:
    replace_once(
        '''def _mask_inline_code_spans(text: str) -> str:
''',
        '''def _mask_multiline_code_spans(text: str) -> str:
    """Mask closed Markdown code spans, including spans crossing line breaks."""
    characters = list(text)
    position = 0
    while position < len(text):
        if text[position] != "`":
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        marker = text[position:run_end]
        close = text.find(marker, run_end)
        if close < 0:
            position = run_end
            continue
        for index in range(position, close + len(marker)):
            if characters[index] not in "\\r\\n":
                characters[index] = " "
        position = close + len(marker)
    return "".join(characters)


def _mask_inline_code_spans(text: str) -> str:
''',
        "multiline code-span helper",
    )

replace_block(
    "def _mask_html_comments_on_line(\n",
    "def _markdown_views(text: str) -> tuple[str, str]:\n",
    '''def _mask_html_comments_on_line(
    raw_line: str,
    *,
    in_comment: bool,
    scan_line: str | None = None,
) -> tuple[str, bool]:
    """Mask HTML comments using a code-span-masked scan view."""
    scan = _mask_inline_code_spans(scan_line if scan_line is not None else raw_line)
    characters = list(raw_line)
    position = 0

    while position < len(raw_line):
        if in_comment:
            canonical = scan.find("-->", position)
            alternate = scan.find("--!>", position)
            candidates = [index for index in (canonical, alternate) if index >= 0]
            if not candidates:
                _mask_segment(characters, position, len(raw_line))
                return "".join(characters), True
            close_start = min(candidates)
            close_length = 4 if scan.startswith("--!>", close_start) else 3
            close_end = close_start + close_length
            _mask_segment(characters, position, close_end)
            position = close_end
            in_comment = False
            continue

        opener = scan.find("<!--", position)
        if opener < 0:
            break
        in_comment = True
        position = opener

    return "".join(characters), in_comment


''',
    "comment scanner",
)

replace_block(
    "def _markdown_views(text: str) -> tuple[str, str]:\n",
    "def _rendered_registry_text(text: str) -> str:\n",
    '''def _markdown_views(text: str) -> tuple[str, str]:
    """Return rendered and structural views with exact offsets preserved."""
    rendered_parts: list[str] = []
    structural_parts: list[str] = []
    in_comment = False
    fence: FenceState | None = None
    paragraph_open = False
    raw_lines = text.splitlines(keepends=True)
    scan_lines = _mask_multiline_code_spans(text).splitlines(keepends=True)
    assert len(raw_lines) == len(scan_lines)

    for raw_line, scan_line in zip(raw_lines, scan_lines):
        line = raw_line.rstrip("\\r\\n")
        if not line.strip():
            paragraph_open = False

        while fence is not None and not _fence_container_continues(line, fence):
            fence = None

        if fence is not None:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            if _is_fence_closer(line, fence):
                fence = None
            continue

        if in_comment:
            rendered_line, in_comment = _mask_html_comments_on_line(
                raw_line,
                in_comment=True,
                scan_line=scan_line,
            )
            rendered_parts.append(rendered_line)
            structural_parts.append(_mask_inline_code_spans(rendered_line))
            if not in_comment:
                paragraph_open = _line_opens_paragraph(
                    rendered_line.rstrip("\\r\\n")
                )
            continue

        context = _line_context(line)
        if context.indented_code and not paragraph_open:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            continue

        if context.indented_code and paragraph_open:
            rendered_line, in_comment = _mask_html_comments_on_line(
                raw_line,
                in_comment=False,
                scan_line=scan_line,
            )
            rendered_parts.append(rendered_line)
            structural_parts.append(_mask_inline_code_spans(rendered_line))
            paragraph_open = True
            continue

        opener = _fence_opener(line)
        if opener is not None:
            fence = opener
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            continue

        rendered_line, in_comment = _mask_html_comments_on_line(
            raw_line,
            in_comment=False,
            scan_line=scan_line,
        )
        rendered_parts.append(rendered_line)
        structural_parts.append(_mask_inline_code_spans(rendered_line))
        paragraph_open = _line_opens_paragraph(
            rendered_line.rstrip("\\r\\n")
        )

    return "".join(rendered_parts), "".join(structural_parts)

''',
    "multiline-aware Markdown views",
)

replace_once(
    '''    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = HTML_TAG_PATTERN.sub(" ", visible)
''',
    '''    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = NON_RENDERING_HTML_PATTERN.sub(" ", visible)
    visible = HTML_TAG_PATTERN.sub(" ", visible)
''',
    "visible non-rendering HTML",
)

if "def _strip_composed_container_prefixes" not in text:
    replace_once(
        '''def _visible_scalar_values(section: str, field: str) -> list[str]:
''',
        '''def _strip_composed_container_prefixes(line: str) -> tuple[str, bool]:
    """Strip recursively composed quote/list prefixes and detect code indentation."""
    value = line.rstrip("\\r\\n")
    position = 0

    for _ in range(32):
        probe = position
        columns = 0
        while probe < len(value) and value[probe] in " \\t":
            if value[probe] == " ":
                columns += 1
            else:
                columns += 4 - (columns % 4)
            probe += 1
        if columns >= 4:
            return value[position:], True

        if probe < len(value) and value[probe] == ">":
            position = probe + 1
            if position < len(value) and value[position] in " \\t":
                position += 1
            continue

        marker = LIST_CONTAINER_PREFIX_PATTERN.match(value, probe)
        if marker:
            position = marker.end()
            continue

        position = probe
        break

    return value[position:], False


def _visible_scalar_values(section: str, field: str) -> list[str]:
''',
        "composed container helper",
    )

replace_block(
    "def _visible_scalar_values(section: str, field: str) -> list[str]:\n",
    "def _scalar_value(entry: str, section: str, field: str) -> str:\n",
    '''def _visible_scalar_values(section: str, field: str) -> list[str]:
    """Return visible scalar values after normalising composed Markdown containers."""
    rendered, structure = _markdown_views(section)
    rendered_lines = rendered.splitlines()
    structure_lines = structure.splitlines()
    assert len(rendered_lines) == len(structure_lines)

    values: list[str] = []
    for rendered_line, structure_line in zip(rendered_lines, structure_lines):
        logical, is_code = _strip_composed_container_prefixes(structure_line)
        if is_code:
            continue
        logical = logical.lstrip(" \\t")
        if not logical.startswith(field):
            continue
        suffix = logical[len(field):]
        if suffix and suffix[0] not in " \\t":
            continue

        rendered_logical, rendered_is_code = _strip_composed_container_prefixes(
            rendered_line
        )
        if rendered_is_code:
            continue
        rendered_logical = rendered_logical.lstrip(" \\t")
        if not rendered_logical.startswith(field):
            continue
        raw_value = rendered_logical[len(field):]
        values.append(_visible_inline_text(raw_value))
    return values


''',
    "composed scalar parsing",
)

replace_once(
    '''def _has_non_heading_content(block: str) -> bool:
    rendered = _rendered_registry_text(block)
    fence: FenceState | None = None
''',
    '''def _has_non_heading_content(block: str) -> bool:
    rendered = _rendered_registry_text(block)
    rendered = NON_RENDERING_HTML_PATTERN.sub(" ", rendered)
    fence: FenceState | None = None
''',
    "non-rendering mapping HTML",
)

replace_once(
    '''    for field in SCALAR_FIELDS:
        expected_clause = str(contract[field])
        assert expected_clause in scalar_values[field], (
            f"{entry} is missing a pinned {field} clause: {expected_clause!r}"
        )
''',
    '''    for field in SCALAR_FIELDS:
        expected_clause = _visible_inline_text(str(contract[field]))
        actual_value = scalar_values[field]
        assert actual_value == expected_clause or actual_value.endswith(
            " " + expected_clause
        ), (
            f"{entry} changed pinned {field}: expected terminal clause "
            f"{expected_clause!r}, got {actual_value!r}"
        )
''',
    "terminal pinned boundary clauses",
)

if "test_compound_container_duplicate_doi_is_rejected" not in text:
    text += '''


def test_compound_container_duplicate_doi_is_rejected():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        "- > **DOI:** https://doi.org/10.0000/conflict\\n\\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_multiline_code_span_comment_literal_cannot_hide_visible_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    injected = (
        "prefix `\\n"
        "<!--\\n"
        "code`\\n"
        "**DOI:** https://doi.org/10.0000/conflict\\n"
        "-->\\n\\n"
        "**Source type:**"
    )
    mutated = section.replace("**Source type:**", injected, 1)
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize(
    "container",
    (
        "<script>placeholder</script>",
        "<style>.placeholder { display: none; }</style>",
        "<template>placeholder</template>",
    ),
)
def test_mapping_blocks_reject_nonrendering_html_contents(container: str):
    section = (
        "### Example\\n\\n"
        f"Research mappings:\\n{container}\\n\\n"
        f"Relevant project mappings:\\n{container}\\n\\n"
        "**Safe benchmark abstraction:** example\\n"
    )
    with pytest.raises(AssertionError, match="empty research mappings"):
        _require_mapping_block("### Example", section)


def test_pinned_boundary_rejects_contradictory_addition():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Shaun Micallef's MAD AS HELL*"
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^ {{0,3}}{re.escape(RIGHTS_FIELD)}(?P<value>[^\\r\\n]*)$",
        lambda match: match.group(0)
        + " Contradictory override: programme dialogue may be copied into benchmark data.",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="changed pinned"):
        _validate_registered_entry(entry, mutated)
'''

PATH.write_text(text, encoding="utf-8")
