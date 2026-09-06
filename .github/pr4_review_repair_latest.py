from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


registry_path = Path("tests/test_research_reference_registry.py")
registry = registry_path.read_text(encoding="utf-8")

registry = replace_once(
    registry,
    '''GOVERNED_DELETION_HTML_PATTERN = re.compile(
    r"<(?:del|s|strike)\\b",
    flags=re.IGNORECASE,
)
''',
    '''GOVERNED_DELETION_HTML_PATTERN = re.compile(
    r"<(?:del|s|strike)\\b",
    flags=re.IGNORECASE,
)
GOVERNED_INLINE_STYLE_HTML_PATTERN = re.compile(
    r"<[A-Za-z][^>]*\\bstyle[ \\t]*=",
    flags=re.IGNORECASE,
)
GOVERNED_BIDI_HTML_PATTERN = re.compile(
    r"<bdo\\b|<[A-Za-z][^>]*\\bdir[ \\t]*=",
    flags=re.IGNORECASE,
)
RAW_HTML_TAG_TOKEN_PATTERN = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?=[ \\t\\r\\n/>])"
    r"(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*>",
    flags=re.DOTALL,
)
''',
    "registry forbidden HTML constants",
)

registry = replace_once(
    registry,
    '''        if name not in {"display", "visibility", "opacity"}:
            continue
''',
    '''        if name not in {"display", "visibility", "opacity", "content-visibility"}:
            continue
''',
    "registry supported CSS properties",
)
registry = replace_once(
    registry,
    '''    opacity = winners.get("opacity", (False, ""))[1]
    opacity_hidden = False
''',
    '''    opacity = winners.get("opacity", (False, ""))[1]
    content_visibility = winners.get("content-visibility", (False, ""))[1]
    opacity_hidden = False
''',
    "registry content visibility winner",
)
registry = replace_once(
    registry,
    '''        display == "none"
        or visibility in {"hidden", "collapse"}
        or opacity_hidden
''',
    '''        display == "none"
        or visibility in {"hidden", "collapse"}
        or content_visibility == "hidden"
        or opacity_hidden
''',
    "registry content visibility result",
)

registry = replace_once(
    registry,
    '''def _normalise_https_destination(
    candidate: str,
    *,
    strip_trailing_prose_punctuation: bool = False,
) -> str | None:
    value = COMMONMARK_CHARACTER_REFERENCE_PATTERN.sub(
        lambda match: html.unescape(match.group(0)),
        candidate,
    )
    value = MARKDOWN_BACKSLASH_ESCAPE_PATTERN.sub(r"\\1", value)
''',
    '''def _normalise_https_destination(
    candidate: str,
    *,
    strip_trailing_prose_punctuation: bool = False,
    decode_markdown_syntax: bool = True,
) -> str | None:
    value = candidate
    if decode_markdown_syntax:
        value = COMMONMARK_CHARACTER_REFERENCE_PATTERN.sub(
            lambda match: html.unescape(match.group(0)),
            value,
        )
        value = MARKDOWN_BACKSLASH_ESCAPE_PATTERN.sub(r"\\1", value)
''',
    "origin-aware destination normalization",
)

registry = replace_once(
    registry,
    '''def _require_rendered_https_destination(
    candidate: str,
    *,
    strip_trailing_prose_punctuation: bool = False,
) -> str:
    destination = _normalise_https_destination(
        candidate,
        strip_trailing_prose_punctuation=strip_trailing_prose_punctuation,
    )
''',
    '''def _require_rendered_https_destination(
    candidate: str,
    *,
    strip_trailing_prose_punctuation: bool = False,
    decode_markdown_syntax: bool = True,
) -> str:
    destination = _normalise_https_destination(
        candidate,
        strip_trailing_prose_punctuation=strip_trailing_prose_punctuation,
        decode_markdown_syntax=decode_markdown_syntax,
    )
''',
    "origin-aware required destination",
)

insert_before_normalise = '''def _normalise_https_destination(
'''
mask_helper = '''def _mask_raw_html_tags_for_markdown_link_discovery(text: str) -> str:
    """Mask raw HTML tag tokens before interpreting Markdown link syntax."""
    characters = list(text)
    for match in RAW_HTML_TAG_TOKEN_PATTERN.finditer(text):
        _mask_segment(characters, match.start(), match.end())
    return "".join(characters)


'''
if mask_helper not in registry:
    if registry.count(insert_before_normalise) != 1:
        raise SystemExit("registry HTML tag masking insertion point drifted")
    registry = registry.replace(insert_before_normalise, mask_helper + insert_before_normalise, 1)

registry = replace_once(
    registry,
    '''    for candidate in _visible_html_links(structure):
        destinations.append(_require_rendered_https_destination(candidate))

    inline_links = _markdown_inline_links(structure)
''',
    '''    for candidate in _visible_html_links(structure):
        destinations.append(
            _require_rendered_https_destination(
                candidate,
                decode_markdown_syntax=False,
            )
        )

    markdown_structure = _mask_raw_html_tags_for_markdown_link_discovery(structure)
    reference_markdown_structure = _mask_raw_html_tags_for_markdown_link_discovery(
        reference_structure
    )
    inline_links = _markdown_inline_links(markdown_structure)
''',
    "raw HTML href and Markdown source separation",
)
registry = replace_once(
    registry,
    '''    structure_without_inline_links = _mask_inline_markdown_links(
        structure,
        inline_links,
    )

    definitions = _reference_definitions(reference_structure)
''',
    '''    structure_without_inline_links = _mask_inline_markdown_links(
        markdown_structure,
        inline_links,
    )

    definitions = _reference_definitions(reference_markdown_structure)
''',
    "masked Markdown/reference link discovery",
)

registry = replace_once(
    registry,
    '''        if GOVERNED_DELETION_HTML_PATTERN.search(logical):
            found.add("deletion")
''',
    '''        if GOVERNED_DELETION_HTML_PATTERN.search(logical):
            found.add("deletion")
        if GOVERNED_INLINE_STYLE_HTML_PATTERN.search(logical):
            found.add("inline-style")
        if GOVERNED_BIDI_HTML_PATTERN.search(logical):
            found.add("bidi")
''',
    "registry inline-style and bidi detection",
)
registry = replace_once(
    registry,
    '''    assert "replacement" not in forbidden_html, (
        f"{entry} contains replacement-content HTML (object/embed/iframe/canvas), which is "
        "not permitted in governed entries because browser replacement semantics can "
        "hide pinned fallback provenance"
    )
''',
    '''    assert "replacement" not in forbidden_html, (
        f"{entry} contains replacement-content HTML (object/embed/iframe/canvas), which is "
        "not permitted in governed entries because browser replacement semantics can "
        "hide pinned fallback provenance"
    )
    assert "inline-style" not in forbidden_html, (
        f"{entry} contains live inline style HTML; governed entries reject inline CSS "
        "rather than claiming complete browser visibility semantics"
    )
    assert "bidi" not in forbidden_html, (
        f"{entry} contains bidirectional/direction-changing HTML; governed clauses must "
        "retain their canonical visual reading order"
    )
''',
    "registry per-entry fail-closed HTML assertions",
)
registry = replace_once(
    registry,
    '''    assert "styling" not in corpus_forbidden_html, (
        "registry contains stylesheet/class-driven HTML styling; governed source "
        "visibility must not depend on embedded stylesheet selectors"
    )
''',
    '''    assert "styling" not in corpus_forbidden_html, (
        "registry contains stylesheet/class-driven HTML styling; governed source "
        "visibility must not depend on embedded stylesheet selectors"
    )
    assert "inline-style" not in corpus_forbidden_html, (
        "registry contains live inline style HTML; governed source visibility must not "
        "depend on CSS properties outside the validator's complete browser model"
    )
    assert "bidi" not in corpus_forbidden_html, (
        "registry contains bidirectional/direction-changing HTML; governed clauses must "
        "retain their canonical visual reading order"
    )
''',
    "registry corpus fail-closed HTML assertions",
)

registry_tests = r'''


def test_latest_review_inline_css_href_autolink_and_bidi_regressions():
    assert _css_hides_element("content-visibility:hidden")

    mutated = _mutate_chey_phrase(
        '<span style="content-visibility:hidden">The article</span>'
    )
    with pytest.raises(AssertionError, match="inline style HTML"):
        _validate_registry_corpus(mutated)

    # HTMLParser has already decoded raw-HTML attributes exactly once. Do not
    # apply CommonMark character-reference decoding to href values a second time.
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _usable_https_destinations(
            '<a href="https&amp;#58;//example.org/path">source</a>'
        )

    # Markdown autolink syntax that exists only in a raw HTML attribute is not
    # rendered as a navigable Markdown link.
    assert _usable_https_destinations(
        '<span title="<https://example.org/path>">plain provenance</span>'
    ) == ()

    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(
        heading for heading in EXPECTED_GOVERNED_ENTRIES
        if heading.startswith("### Chey (2021)")
    )
    section = _registered_sections(corpus)[entry]
    rights = str(ENTRY_CONTRACTS[entry][RIGHTS_FIELD])
    mutated_section = section.replace(
        rights,
        f'<bdo dir="rtl">{rights}</bdo>',
        1,
    )
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="bidirectional/direction-changing HTML"):
        _validate_registry_corpus(mutated)
'''
if "def test_latest_review_inline_css_href_autolink_and_bidi_regressions():" not in registry:
    registry = registry.rstrip() + registry_tests + "\n"

registry_path.write_text(registry, encoding="utf-8")


policing_path = Path("tests/test_policing_context_roadmap.py")
policing = policing_path.read_text(encoding="utf-8")

policing = replace_once(
    policing,
    '''import re

import pytest
''',
    '''import re
import string

import pytest
''',
    "policing string import",
)

policing = replace_once(
    policing,
    '''CSS_COMMENT_PATTERN = re.compile(r"/\\*.*?\\*/", flags=re.DOTALL)


def _css_hides_element(style: str) -> bool:
    """Apply inline CSS declaration order and !important precedence."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())
''',
    '''CSS_COMMENT_PATTERN = re.compile(r"/\\*.*?\\*/", flags=re.DOTALL)
RAW_HTML_BLOCK_TAGS = frozenset({"pre", "script", "style", "textarea"})
RAW_HTML_PROCESSING_INSTRUCTION = "__processing_instruction__"
RAW_HTML_DECLARATION = "__declaration__"
RAW_HTML_CDATA = "__cdata__"


def _decode_css_escapes(value: str) -> str:
    """Decode CSS escapes before declaration-name/value comparison."""
    parts: list[str] = []
    position = 0
    while position < len(value):
        if value[position] != "\\\\":
            parts.append(value[position])
            position += 1
            continue
        if position + 1 >= len(value):
            parts.append("\\\\")
            position += 1
            continue
        next_character = value[position + 1]
        if next_character in "\\r\\n\\f":
            if next_character == "\\r" and position + 2 < len(value) and value[position + 2] == "\\n":
                position += 3
            else:
                position += 2
            continue
        cursor = position + 1
        while (
            cursor < len(value)
            and cursor - (position + 1) < 6
            and value[cursor] in string.hexdigits
        ):
            cursor += 1
        if cursor > position + 1:
            codepoint = int(value[position + 1:cursor], 16)
            if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
                parts.append("\\uFFFD")
            else:
                parts.append(chr(codepoint))
            if cursor < len(value) and value[cursor] in " \\t\\r\\n\\f":
                if value[cursor] == "\\r" and cursor + 1 < len(value) and value[cursor + 1] == "\\n":
                    cursor += 2
                else:
                    cursor += 1
            position = cursor
            continue
        parts.append(next_character)
        position += 2
    return "".join(parts)


def _css_hides_element(style: str) -> bool:
    """Apply CSS escapes, declaration order, and !important precedence."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style)
''',
    "policing CSS escape decoder",
)
policing = replace_once(
    policing,
    '''        name, raw_value = declaration.split(":", 1)
        name = name.strip()
        if name not in {"display", "visibility", "opacity"}:
            continue
        raw_value = raw_value.strip()
        important = re.search(r"\\s*!important\\s*$", raw_value) is not None
        value = re.sub(r"\\s*!important\\s*$", "", raw_value).strip()
''',
    '''        raw_name, raw_value = declaration.split(":", 1)
        name = _decode_css_escapes(raw_name.strip()).casefold()
        if name not in {"display", "visibility", "opacity", "content-visibility"}:
            continue
        decoded_value = _decode_css_escapes(raw_value.strip()).casefold()
        important = re.search(r"\\s*!important\\s*$", decoded_value) is not None
        value = re.sub(r"\\s*!important\\s*$", "", decoded_value).strip()
''',
    "policing decoded CSS declarations",
)
policing = replace_once(
    policing,
    '''    opacity = winners.get("opacity", (False, ""))[1]
    opacity_hidden = False
''',
    '''    opacity = winners.get("opacity", (False, ""))[1]
    content_visibility = winners.get("content-visibility", (False, ""))[1]
    opacity_hidden = False
''',
    "policing content visibility winner",
)
policing = replace_once(
    policing,
    '''        display == "none"
        or visibility in {"hidden", "collapse"}
        or opacity_hidden
''',
    '''        display == "none"
        or visibility in {"hidden", "collapse"}
        or content_visibility == "hidden"
        or opacity_hidden
''',
    "policing content visibility result",
)

policing = replace_once(
    policing,
    '''@dataclass(frozen=True)
class FenceState:
    character: str
    minimum_length: int
    containers: tuple[tuple[str, int], ...]


def _parse_fence_container_prefixes(
''',
    '''@dataclass(frozen=True)
class FenceState:
    character: str
    minimum_length: int
    containers: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class RawHTMLBlockState:
    tag: str
    containers: tuple[tuple[str, int], ...]


def _parse_fence_container_prefixes(
''',
    "policing raw HTML block state",
)

raw_helpers_marker = '''def _line_opens_paragraph(line: str) -> bool:
'''
raw_helpers = r'''def _raw_html_block_opener(line: str) -> RawHTMLBlockState | None:
    """Return a CommonMark raw HTML block opener with its terminator family."""
    logical, indented_code, containers = _parse_fence_container_prefixes(line)
    if indented_code:
        return None
    candidate = logical.lstrip(" \t")
    if candidate.startswith("<?"):
        return RawHTMLBlockState(RAW_HTML_PROCESSING_INSTRUCTION, containers)
    if candidate.startswith("<![CDATA["):
        return RawHTMLBlockState(RAW_HTML_CDATA, containers)
    if re.match(r"<![A-Z]", candidate):
        return RawHTMLBlockState(RAW_HTML_DECLARATION, containers)
    match = re.match(
        r"<(?P<tag>pre|script|style|textarea)(?:[ \t]|>|$)",
        candidate,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    return RawHTMLBlockState(match.group("tag").lower(), containers)


def _raw_html_block_container_continues(line: str, state: RawHTMLBlockState) -> bool:
    if not line.strip() or not state.containers:
        return True
    _, ok = _strip_expected_fence_containers(line, state.containers)
    return ok


def _raw_html_block_logical_line(line: str, state: RawHTMLBlockState) -> str:
    if not state.containers:
        return line.rstrip("\r\n")
    logical, ok = _strip_expected_fence_containers(line, state.containers)
    return logical if ok else line.rstrip("\r\n")


def _raw_html_block_closes(line: str, state: RawHTMLBlockState) -> bool:
    logical = _raw_html_block_logical_line(line, state)
    if state.tag == RAW_HTML_PROCESSING_INSTRUCTION:
        return "?>" in logical
    if state.tag == RAW_HTML_CDATA:
        return "]]>" in logical
    if state.tag == RAW_HTML_DECLARATION:
        return ">" in logical
    return bool(
        re.search(
            rf"</{re.escape(state.tag)}[ \t]*>",
            logical,
            flags=re.IGNORECASE,
        )
    )


'''
if raw_helpers not in policing:
    if policing.count(raw_helpers_marker) != 1:
        raise SystemExit("policing raw HTML helper insertion point drifted")
    policing = policing.replace(raw_helpers_marker, raw_helpers + raw_helpers_marker, 1)

policing = replace_once(
    policing,
    '''    in_comment = False
    fence: FenceState | None = None
    paragraph_open = False

    for raw_line in markdown.splitlines(keepends=True):
''',
    '''    in_comment = False
    fence: FenceState | None = None
    raw_html: RawHTMLBlockState | None = None
    paragraph_open = False

    for raw_line in markdown.splitlines(keepends=True):
''',
    "policing raw HTML state variable",
)
policing = replace_once(
    policing,
    '''        while fence is not None and not _fence_container_continues(line, fence):
            fence = None

        if fence is not None:
''',
    '''        while fence is not None and not _fence_container_continues(line, fence):
            fence = None
        while raw_html is not None and not _raw_html_block_container_continues(line, raw_html):
            raw_html = None

        if fence is not None:
''',
    "policing raw HTML container continuation",
)
policing = replace_once(
    policing,
    '''        if in_comment:
            rendered_line, in_comment = _mask_comments_on_line(raw_line, True)
            parts.append(rendered_line)
            if not in_comment:
                paragraph_open = _line_opens_paragraph(rendered_line)
            continue

        logical, indentation = _strip_container_prefixes(line)
''',
    '''        if raw_html is not None:
            parts.append(_mask_non_newline(raw_line))
            if _raw_html_block_closes(line, raw_html):
                raw_html = None
            paragraph_open = False
            continue

        if in_comment:
            rendered_line, in_comment = _mask_comments_on_line(raw_line, True)
            parts.append(rendered_line)
            if not in_comment:
                paragraph_open = _line_opens_paragraph(rendered_line)
            continue

        logical, indentation = _strip_container_prefixes(line)
''',
    "policing active raw HTML masking",
)
policing = replace_once(
    policing,
    '''        opener = _fence_opener(line)
        if opener is not None:
            fence = opener
            parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            continue

        rendered_line, in_comment = _mask_comments_on_line(raw_line, False)
''',
    '''        opener = _fence_opener(line)
        if opener is not None:
            fence = opener
            parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            continue

        raw_opener = _raw_html_block_opener(line)
        if raw_opener is not None:
            parts.append(_mask_non_newline(raw_line))
            if not _raw_html_block_closes(line, raw_opener):
                raw_html = raw_opener
            paragraph_open = False
            continue

        rendered_line, in_comment = _mask_comments_on_line(raw_line, False)
''',
    "policing raw HTML opener masking",
)

policing_tests = r'''


def test_latest_review_shared_css_escape_and_raw_html_block_regressions():
    assert _visible_text(
        '<span style="display:n\\6f ne">hidden governance</span>'
    ) == ""
    assert _visible_text(
        '<span style="content-visibility:hidden">hidden governance</span>'
    ) == ""

    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_HEADING)
    end = roadmap.index(WORKSTREAM_END, start)
    section = roadmap[start:end]
    mutated = roadmap[:start] + f"<pre>\n{section}\n</pre>\n" + roadmap[end:]
    with pytest.raises(AssertionError, match="rendered policing workstream"):
        _validate_policing_workstream(mutated)
'''
if "def test_latest_review_shared_css_escape_and_raw_html_block_regressions():" not in policing:
    policing = policing.rstrip() + policing_tests + "\n"

policing_path.write_text(policing, encoding="utf-8")
print("Applied guarded PR #4 latest-review fixes for six P2 findings.")
