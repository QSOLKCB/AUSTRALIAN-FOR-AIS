"""Regression checks for the proposed policing-context research workstream."""

from dataclasses import dataclass
from pathlib import Path
import hashlib
import html
from html.parser import HTMLParser
import re
import string

import pytest


ROADMAP = Path(__file__).parent.parent / "ROADMAP.md"
WORKSTREAM_HEADING = "### I. Australian and United States policing-context transfer"
WORKSTREAM_END = "\n---\n\n## Phase 3"
WORKSTREAM_END_HEADING = "## Phase 3 — Multi-Annotator Culturally Contextualised Dataset"
POLICING_WORKSTREAM_VISIBLE_SHA256 = "d43f7d255da2792106d69048e617d96d9f8933204bc3dd4623b2482e5a4600e8"


REQUIRED_CLAUSES = (
    WORKSTREAM_HEADING,
    "source-gated research proposal",
    "not legal advice",
    "Every implemented item must record, at minimum, the relevant country, jurisdiction, agency or institutional role, encounter type, source date or version, registered source identifiers or links supporting any legal or procedural condition supplied to the model, and claim type.",
    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",
    "POLICE TERMINOLOGY != CROSS-JURISDICTION EQUIVALENCE",
    "CASUAL ADDRESS != FRIENDSHIP OR CONSENT",
    "CALM TONE != ABSENCE OF COERCIVE AUTHORITY",
    "POLITE WORDING != VOLUNTARY CHOICE",
    "FICTIONAL POLICE TROPE != OPERATIONAL POLICY",
    "ONE AGENCY != A NATIONAL POLICING SYSTEM",
    "ONE ENCOUNTER != SYSTEM-WIDE GROUND TRUTH",
    "JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER",
    "LEGAL INFORMATION != LEGAL ADVICE",
    "register official and current sources for each Australian and United States jurisdictional claim",
    "before publishing any family involving coercion, consent, search, detention, "
    "questioning, force, emergency powers, or legal rights, verify the governing "
    "sources are current for the recorded jurisdiction and date and obtain appropriate "
    "review from relevant Australian and United States legal, policing, civil-liberties, "
    "and community expertise;",
)

AFFIRMATIVE_LINE_PREFIX_CLAUSES = (
    "Every implemented item must record, at minimum, the relevant country, jurisdiction, agency or institutional role, encounter type, source date or version, registered source identifiers or links supporting any legal or procedural condition supplied to the model, and claim type.",
    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",
    "POLICE TERMINOLOGY != CROSS-JURISDICTION EQUIVALENCE",
    "CASUAL ADDRESS != FRIENDSHIP OR CONSENT",
    "CALM TONE != ABSENCE OF COERCIVE AUTHORITY",
    "POLITE WORDING != VOLUNTARY CHOICE",
    "FICTIONAL POLICE TROPE != OPERATIONAL POLICY",
    "ONE AGENCY != A NATIONAL POLICING SYSTEM",
    "ONE ENCOUNTER != SYSTEM-WIDE GROUND TRUTH",
    "JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER",
    "LEGAL INFORMATION != LEGAL ADVICE",
    "register official and current sources for each Australian and United States jurisdictional claim",
    "before publishing any family involving coercion, consent, search, detention, "
    "questioning, force, emergency powers, or legal rights, verify the governing "
    "sources are current for the recorded jurisdiction and date and obtain appropriate "
    "review from relevant Australian and United States legal, policing, civil-liberties, "
    "and community expertise;",
)

AFFIRMATIVE_EXACT_LINE_OVERRIDES = {
    "register official and current sources for each Australian and United States jurisdictional claim": (
        "register official and current sources for each Australian and United States "
        "jurisdictional claim before adopting it as benchmark context;"
    ),
}

FENCE_PATTERN = re.compile(r"(?P<fence>`{3,}|~{3,})(?P<info>.*)")
LIST_MARKER_PATTERN = re.compile(r"(?:[-+*]|\d{1,9}[.)])(?:[ \t]+|$)")
THEMATIC_BREAK_PATTERN = re.compile(
    r"(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,}"
)
MARKDOWN_IMAGE_PATTERN = re.compile(
    r"!\[[^\]\r\n]*\]\([^\r\n)]*(?:\)[^\r\n)]*)?\)"
)
MARKDOWN_LINK_PATTERN = re.compile(
    r"(?<!!)\[(?P<label>[^\]\r\n]*)\]\("
    r"[ \t]*(?:<[^>\r\n]+>|[^\s)\r\n]+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?"
    r"[ \t]*\)"
)
AUTOLINK_PATTERN = re.compile(r"<(?P<url>https?://[^>\s]+)>")
LINK_REFERENCE_DEFINITION_PATTERN = re.compile(
    r"(?m)^ {0,3}\[(?P<label>[^\]\r\n]+)\]:[ \t]*"
    r"(?:\r?\n {1,3})?"
    r"(?P<destination><[^>\r\n]+>|[^\s\r\n]+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?[ \t]*$"
)
LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN = re.compile(
    r"\[(?P<label>[^\]\r\n]+)\]:[ \t]*"
    r"(?P<destination><[^>\r\n]+>|[^\s\r\n]+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?[ \t]*$"
)
HTML_TAG_PATTERN = re.compile(r"</?[A-Za-z][^>]*>|<![A-Za-z][^>]*>|<\?[\s\S]*?\?>")
NON_RENDERING_HTML_PATTERN = re.compile(
    r"<(script|style|template)\b[^>]*>.*?</\1\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)
SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})
CSS_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", flags=re.DOTALL)
RAW_HTML_BLOCK_TAGS = frozenset({"pre", "script", "style", "textarea"})
RAW_HTML_PROCESSING_INSTRUCTION = "__processing_instruction__"
RAW_HTML_DECLARATION = "__declaration__"
RAW_HTML_CDATA = "__cdata__"
PREFLIGHT_HTML_BLANK_LINE = "__blank_line__"
# CommonMark type-6 blocks end at a blank line, not at a closing HTML tag.
PREFLIGHT_HTML_BLOCK_TAGS = frozenset({
    "address", "article", "aside", "base", "basefont", "blockquote", "body",
    "caption", "center", "col", "colgroup", "dd", "details", "dialog", "dir",
    "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
    "frame", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head",
    "header", "hr", "html", "iframe", "legend", "li", "link", "main", "menu",
    "menuitem", "nav", "noframes", "ol", "optgroup", "option", "p", "param",
    "search", "section", "summary", "table", "tbody", "td", "tfoot", "th",
    "thead", "title", "tr", "track", "ul",
})
PREFLIGHT_HTML_TAG = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?=[ \t\r\n\f/>])"
    r"(?:[^>\"']|\"[^\"]*\"|'[^']*')*>", re.DOTALL,
)
INTERACTIVE_FORM_CONTROL_PATTERN = re.compile(
    r"<\s*(?:form|input|button|select|textarea|option|optgroup)\b",
    flags=re.IGNORECASE,
)


def _decode_css_escapes(value: str) -> str:
    """Decode CSS escapes before declaration-name/value comparison."""
    parts: list[str] = []
    position = 0
    while position < len(value):
        if value[position] != "\\":
            parts.append(value[position])
            position += 1
            continue
        if position + 1 >= len(value):
            parts.append("\\")
            position += 1
            continue
        next_character = value[position + 1]
        if next_character in "\r\n\f":
            if next_character == "\r" and position + 2 < len(value) and value[position + 2] == "\n":
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
                parts.append("\uFFFD")
            else:
                parts.append(chr(codepoint))
            if cursor < len(value) and value[cursor] in " \t\r\n\f":
                if value[cursor] == "\r" and cursor + 1 < len(value) and value[cursor + 1] == "\n":
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
    winners: dict[str, tuple[bool, str]] = {}
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        raw_name, raw_value = declaration.split(":", 1)
        name = _decode_css_escapes(raw_name.strip()).casefold()
        if name not in {"display", "visibility", "opacity", "content-visibility"}:
            continue
        decoded_value = _decode_css_escapes(raw_value.strip()).casefold()
        important = re.search(r"\s*!important\s*$", decoded_value) is not None
        value = re.sub(r"\s*!important\s*$", "", decoded_value).strip()
        previous = winners.get(name)
        if previous is None or (important and not previous[0]) or important == previous[0]:
            winners[name] = (important, value)

    display = winners.get("display", (False, ""))[1]
    visibility = winners.get("visibility", (False, ""))[1]
    opacity = winners.get("opacity", (False, ""))[1]
    content_visibility = winners.get("content-visibility", (False, ""))[1]
    opacity_hidden = False
    if opacity:
        numeric_opacity = opacity[:-1].strip() if opacity.endswith("%") else opacity
        try:
            opacity_hidden = float(numeric_opacity) <= 0.0
        except ValueError:
            opacity_hidden = False
    return (
        display == "none"
        or visibility in {"hidden", "collapse"}
        or content_visibility == "hidden"
        or opacity_hidden
    )


RAW_HTML_LITERAL_PUNCTUATION = {"*": "\uE110", "_": "\uE111"}


class _VisibleHTMLTextParser(HTMLParser):
    def __init__(self, *, protect_raw_punctuation: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []
        self.protect_raw_punctuation = protect_raw_punctuation

    @staticmethod
    def _is_hidden(tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        tag = tag.lower()
        if tag in {"script", "style", "template", "title"}:
            return True
        values: dict[str, str] = {}
        for key, value in attrs:
            values.setdefault(key.lower(), value or "")
        if tag in {"details", "dialog"} and "open" not in values:
            return True
        if "hidden" in values or "popover" in values:
            return True
        return _css_hides_element(values.get("style", ""))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        inherited = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _ in self.stack)
        )
        if tag in HTML_VOID_TAGS:
            return
        self.stack.append(
            (tag, inherited or svg_metadata_hidden or self._is_hidden(tag, attrs))
        )

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in HTML_VOID_TAGS:
            return
        # HTML browsers ignore the self-closing flag on non-void elements.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            if self.protect_raw_punctuation and self.stack:
                # Never promote punctuation emitted by raw HTML into Markdown
                # emphasis after parsing. Retain it in the integrity value.
                for literal, marker in RAW_HTML_LITERAL_PUNCTUATION.items():
                    data = data.replace(literal, marker)
            self.parts.append(data)


def _visible_html_text(text: str, *, protect_raw_punctuation: bool = False) -> str:
    parser = _VisibleHTMLTextParser(protect_raw_punctuation=protect_raw_punctuation)
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    return "".join(parser.parts)


HTML_VOID_TAGS = {
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

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        parent_hidden = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _, _ in self.stack)
        )
        own_hidden = svg_metadata_hidden or _VisibleHTMLTextParser._is_hidden(tag, attrs)
        hidden = parent_hidden or own_hidden
        start = self._offset()

        if tag in HTML_VOID_TAGS:
            if own_hidden and not parent_hidden:
                self.spans.append((start, self._tag_end(start)))
            return

        root_start = start if hidden and not parent_hidden else None
        self.stack.append((tag, hidden, root_start))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in HTML_VOID_TAGS:
            # Match browser tree construction: the slash does not close a
            # non-void HTML element such as `<dialog />` or `<a />`.
            self.handle_starttag(tag, attrs)
            return
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
    """Mask hidden containers globally so visibility state survives slicing."""
    parser = _HiddenHTMLRegionParser(text)
    try:
        parser.feed(text)
        parser.close()
        parser.finish()
    except Exception:
        return _mask_non_newline(text)

    characters = list(text)
    for start, end in parser.spans:
        for index in range(start, end):
            if characters[index] not in "\r\n":
                characters[index] = " "
    return "".join(characters)


def _mask_non_newline(text: str) -> str:
    return "".join(character if character in "\r\n" else " " for character in text)


def _indent_columns(value: str, start: int = 0) -> tuple[int, int]:
    """Return source index and CommonMark-style indentation columns."""
    index = start
    columns = 0
    while index < len(value) and value[index] in " \t":
        if value[index] == " ":
            columns += 1
        else:
            columns += 4 - (columns % 4)
        index += 1
    return index, columns


def _strip_container_prefixes(line: str) -> tuple[str, int]:
    """Strip arbitrarily composed list/quote prefixes and report residual indent."""
    value = line.rstrip("\r\n")
    position = 0

    for _ in range(32):
        before = position
        probe, columns = _indent_columns(value, position)
        if columns >= 4:
            return value[position:], columns

        if probe < len(value) and value[probe] == ">":
            position = probe + 1
            if position < len(value) and value[position] in " \t":
                position += 1
            continue

        marker = LIST_MARKER_PATTERN.match(value, probe)
        if marker:
            position = marker.end()
            continue

        position = before
        break

    probe, columns = _indent_columns(value, position)
    return value[probe:], columns


def _mask_link_reference_definitions_for_visibility(markdown: str) -> str:
    """Mask CommonMark reference definitions, including container-scoped forms."""
    characters = list(markdown)
    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(markdown):
        for index in range(match.start(), match.end()):
            if characters[index] not in "\r\n":
                characters[index] = " "

    partially_masked = "".join(characters)
    offset = 0
    for raw_line in partially_masked.splitlines(keepends=True):
        logical, indentation = _strip_container_prefixes(raw_line)
        if (
            indentation < 4
            and LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN.fullmatch(
                logical.rstrip("\r\n \t")
            )
        ):
            for index in range(offset, offset + len(raw_line)):
                if characters[index] not in "\r\n":
                    characters[index] = " "
        offset += len(raw_line)
    return "".join(characters)


def _display_columns(value: str) -> int:
    columns = 0
    for character in value:
        if character == "\t":
            columns += 4 - (columns % 4)
        else:
            columns += 1
    return columns


@dataclass(frozen=True)
class FenceState:
    character: str
    minimum_length: int
    containers: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class RawHTMLBlockState:
    tag: str
    containers: tuple[tuple[str, int], ...]


def _parse_fence_container_prefixes(
    line: str,
) -> tuple[str, bool, tuple[tuple[str, int], ...]]:
    """Return logical text, code status, and ordered list/quote containers."""
    value = line.rstrip("\r\n")
    position = 0
    containers: list[tuple[str, int]] = []

    for _ in range(32):
        probe, columns = _indent_columns(value, position)
        if columns >= 4:
            return value[position:], True, tuple(containers)

        if probe < len(value) and value[probe] == ">":
            containers.append(("quote", 0))
            position = probe + 1
            if position < len(value) and value[position] in " \t":
                position += 1
            continue

        marker = LIST_MARKER_PATTERN.match(value, probe)
        if marker:
            content_indent = columns + _display_columns(marker.group(0))
            containers.append(("list", content_indent))
            position = marker.end()
            continue

        position = probe
        break

    return value[position:], False, tuple(containers)


def _consume_required_indent(
    value: str,
    start: int,
    required_columns: int,
) -> tuple[int, bool]:
    position = start
    columns = 0
    while position < len(value) and value[position] in " \t" and columns < required_columns:
        if value[position] == " ":
            columns += 1
        else:
            columns += 4 - (columns % 4)
        position += 1
    return position, columns >= required_columns


def _strip_expected_fence_containers(
    line: str,
    containers: tuple[tuple[str, int], ...],
) -> tuple[str, bool]:
    """Strip the continuation form of the containers that own an active fence."""
    value = line.rstrip("\r\n")
    position = 0

    for kind, amount in containers:
        if kind == "list":
            position, ok = _consume_required_indent(value, position, amount)
            if not ok:
                return value, False
            continue

        probe, columns = _indent_columns(value, position)
        if columns > 3 or probe >= len(value) or value[probe] != ">":
            return value, False
        position = probe + 1
        if position < len(value) and value[position] in " \t":
            position += 1

    return value[position:], True


def _fence_opener(line: str) -> FenceState | None:
    logical, indented_code, containers = _parse_fence_container_prefixes(line)
    if indented_code:
        return None
    match = FENCE_PATTERN.fullmatch(logical.rstrip(" \t"))
    if not match:
        return None
    marker = match.group("fence")
    info = match.group("info")
    if marker[0] == "`" and "`" in info:
        return None
    return FenceState(
        character=marker[0],
        minimum_length=len(marker),
        containers=containers,
    )


def _fence_container_continues(line: str, state: FenceState) -> bool:
    if not line.strip():
        return True
    if not state.containers:
        return True
    _, ok = _strip_expected_fence_containers(line, state.containers)
    return ok


def _fence_logical_line(line: str, state: FenceState) -> str:
    if not state.containers:
        return line.rstrip("\r\n")
    logical, ok = _strip_expected_fence_containers(line, state.containers)
    return logical if ok else line.rstrip("\r\n")


def _is_fence_closer(line: str, state: FenceState) -> bool:
    logical = _fence_logical_line(line, state)
    marker_index, indent_columns = _indent_columns(logical)
    if indent_columns > 3:
        return False
    candidate = logical[marker_index:].rstrip(" \t")
    return bool(
        re.fullmatch(
            rf"{re.escape(state.character)}{{{state.minimum_length},}}[ \t]*",
            candidate,
        )
    )


def _raw_html_block_opener(line: str) -> RawHTMLBlockState | None:
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
    if state.tag == PREFLIGHT_HTML_BLANK_LINE:
        return not logical.strip()
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


def _line_opens_paragraph(line: str) -> bool:
    logical, indentation = _strip_container_prefixes(line)
    stripped = logical.strip()
    if not stripped or indentation >= 4:
        return False
    if re.fullmatch(r"#{1,6}(?:[ \t]+.*)?", stripped):
        return False
    if THEMATIC_BREAK_PATTERN.fullmatch(stripped):
        return False
    if LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN.fullmatch(stripped):
        return False
    return True


def _mask_comments_on_line(raw_line: str, in_comment: bool) -> tuple[str, bool]:
    characters = list(raw_line)
    position = 0

    while position < len(raw_line):
        if in_comment:
            canonical = raw_line.find("-->", position)
            alternate = raw_line.find("--!>", position)
            candidates = [index for index in (canonical, alternate) if index >= 0]
            if not candidates:
                for index in range(position, len(raw_line)):
                    if characters[index] not in "\r\n":
                        characters[index] = " "
                return "".join(characters), True
            close_start = min(candidates)
            close_length = 4 if raw_line.startswith("--!>", close_start) else 3
            close_end = close_start + close_length
            for index in range(position, close_end):
                if characters[index] not in "\r\n":
                    characters[index] = " "
            position = close_end
            in_comment = False
            continue

        opener = raw_line.find("<!--", position)
        if opener < 0:
            break
        in_comment = True
        position = opener

    return "".join(characters), in_comment


def _rendered_structure(
    markdown: str, *, html_spans: list[tuple[int, int]] | None = None,
) -> str:
    """Mask code/comments; optionally retain raw HTML for the policy preflight.

    The ordinary structural view is unchanged. The preflight view preserves
    raw HTML blocks and records their offsets so backticks within those blocks
    cannot be reinterpreted as Markdown code and conceal live HTML elements.
    """
    parts: list[str] = []
    in_comment = False
    fence: FenceState | None = None
    raw_html: RawHTMLBlockState | None = None
    paragraph_open = False

    offset = 0
    for raw_line in markdown.splitlines(keepends=True):
        line_start = offset
        offset += len(raw_line)
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            paragraph_open = False

        while fence is not None and not _fence_container_continues(line, fence):
            fence = None
        while raw_html is not None and not _raw_html_block_container_continues(line, raw_html):
            raw_html = None

        if fence is not None:
            parts.append(_mask_non_newline(raw_line))
            if _is_fence_closer(line, fence):
                fence = None
            paragraph_open = False
            continue

        if raw_html is not None:
            if html_spans is not None:
                parts.append(raw_line)
                html_spans.append((line_start, offset))
            else:
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
        if indentation >= 4 and not paragraph_open:
            parts.append(_mask_non_newline(raw_line))
            continue

        opener = _fence_opener(line)
        if opener is not None:
            fence = opener
            parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            continue

        raw_opener = _raw_html_block_opener(line)
        if raw_opener is None and html_spans is not None:
            logical_html, is_code, containers = _parse_fence_container_prefixes(line)
            candidate = logical_html.strip(" \t")
            tag_match = re.match(r"</?([A-Za-z][A-Za-z0-9-]*)(?=[ \t\r\n\f/>]|$)", candidate)
            if not is_code and tag_match is not None:
                type6 = tag_match.group(1).lower() in PREFLIGHT_HTML_BLOCK_TAGS
                type7 = not paragraph_open and PREFLIGHT_HTML_TAG.fullmatch(candidate) is not None
                if type6 or type7:
                    raw_opener = RawHTMLBlockState(PREFLIGHT_HTML_BLANK_LINE, containers)
        if raw_opener is not None:
            if html_spans is not None:
                parts.append(raw_line)
                html_spans.append((line_start, offset))
            else:
                parts.append(_mask_non_newline(raw_line))
            if not _raw_html_block_closes(line, raw_opener):
                raw_html = raw_opener
            paragraph_open = False
            continue

        rendered_line, in_comment = _mask_comments_on_line(raw_line, False)
        parts.append(rendered_line)
        # Indented continuation lines do not end an already-open paragraph.
        # Preserve successive HTML attribute lines for the parsed preflight.
        paragraph_open = (
            paragraph_open and indentation >= 4 and bool(rendered_line.strip())
        ) or _line_opens_paragraph(rendered_line)

    return "".join(parts)



def _is_escaped_markdown_character(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _balanced_markdown_label_end(text: str, start: int) -> int | None:
    depth = 1
    cursor = start + 1
    while cursor < len(text):
        character = text[cursor]
        if character in "\r\n":
            return None
        if character == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _inline_link_closing_paren(text: str, start: int) -> int | None:
    depth = 1
    cursor = start + 1
    quote: str | None = None
    angle = False
    top_level_space = False
    while cursor < len(text):
        character = text[cursor]
        if character == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if quote is not None:
            if character == quote:
                quote = None
            cursor += 1
            continue
        if angle:
            if character in "\r\n":
                return None
            if character == ">":
                angle = False
            cursor += 1
            continue
        if depth == 1 and character in " \t\r\n":
            top_level_space = True
            cursor += 1
            continue
        if character in "\r\n":
            return None
        if depth == 1 and top_level_space and character in {"\"", "'"}:
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
    value = inner.lstrip(" \t\r\n")
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
            if character == "\\" and cursor + 1 < len(value):
                cursor += 2
                continue
            if character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    return None
                depth -= 1
            elif character in " \t\r\n" and depth == 0:
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
            and remainder[0] in {"\"", "'"}
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


def _replace_inline_markdown_links_for_visibility(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    while cursor < len(text):
        bracket = text.find("[", cursor)
        if bracket < 0:
            parts.append(text[cursor:])
            break
        if _is_escaped_markdown_character(text, bracket):
            parts.append(text[cursor:bracket + 1])
            cursor = bracket + 1
            continue
        label_end = _balanced_markdown_label_end(text, bracket)
        if label_end is None or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            parts.append(text[cursor:bracket + 1])
            cursor = bracket + 1
            continue
        paren_start = label_end + 1
        paren_end = _inline_link_closing_paren(text, paren_start)
        if (
            paren_end is None
            or _inline_link_destination(text[paren_start + 1:paren_end]) is None
        ):
            parts.append(text[cursor:bracket + 1])
            cursor = bracket + 1
            continue
        image = (
            bracket > 0
            and text[bracket - 1] == "!"
            and not _is_escaped_markdown_character(text, bracket - 1)
        )
        start = bracket - 1 if image else bracket
        parts.append(text[cursor:start])
        parts.append(" " if image else text[bracket + 1:label_end])
        cursor = paren_end + 1
    return "".join(parts)



GOVERNED_CONDITIONAL_RAW_TEXT_TAGS = frozenset({
    "noscript", "plaintext", "xmp", "listing", "noframes", "noembed",
})


GOVERNED_EXECUTABLE_URL_ATTRIBUTES = frozenset({
    "href", "src", "action", "formaction", "xlink:href",
})
GOVERNED_EXECUTABLE_URL_SCHEMES = frozenset({"javascript", "vbscript"})


def _has_executable_url_scheme(value: str) -> bool:
    """Detect script-capable URL schemes after browser-style whitespace folding."""
    if ":" not in value:
        return False
    raw_scheme = value.split(":", 1)[0]
    # HTMLParser has already decoded character references. Fail closed
    # on ASCII whitespace/control characters embedded in a URL scheme.
    scheme = re.sub(r"[\x00-\x20\x7f]+", "", raw_scheme).casefold()
    return scheme in GOVERNED_EXECUTABLE_URL_SCHEMES


class _GovernedSurfaceHTMLParser(HTMLParser):
    """Detect live HTML whose browser semantics are unsafe to approximate."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.violations: set[str] = set()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        if tag == "canvas":
            self.violations.add("canvas")
        if tag == "img":
            self.violations.add("raw-image")
        if tag in {"iframe", "object", "embed", "audio", "video"}:
            self.violations.add("replacement-content")
        # SVG needs its own rendering tree, not HTML character-data callbacks.
        if tag == "svg":
            self.violations.add("raw-svg")
        if tag == "math":
            self.violations.add("raw-mathml")
        if tag in {"style", "link"}:
            self.violations.add("stylesheet")
        # Non-rendering character data does not make an element harmless:
        # scripts can rewrite the document, and conditional text can vanish.
        if tag == "script":
            self.violations.add("executable-script")
        if tag in GOVERNED_CONDITIONAL_RAW_TEXT_TAGS:
            self.violations.add("conditional-raw-text")
        if tag in {"del", "s", "strike"}:
            self.violations.add("semantic-deletion")
        # Parsed names cover duplicate, boolean, and multiline attributes.
        # The reducer cannot establish readability for arbitrary inline CSS.
        attribute_names = {key.lower() for key, _ in attrs}
        if any(name.startswith("on") for name in attribute_names):
            self.violations.add("event-handler")
        # Raw Markdown is embedded into an existing HTML document. A live
        # duplicate root tag can merge attributes onto that document root, so
        # reject html/body rather than approximating tree-builder semantics.
        if tag in {"html", "body"}:
            self.violations.add("document-root")
        if {"shadowrootmode", "shadowroot"}.intersection(attribute_names):
            self.violations.add("shadow-root")
        # HTMLParser decodes attribute references once. Preserve the first
        # duplicate attribute, matching the browser's effective directive.
        values: dict[str, str] = {}
        for key, value in attrs:
            values.setdefault(key.lower(), value or "")
        if tag == "meta" and values.get("http-equiv", "").strip().lower() == "refresh":
            self.violations.add("meta-refresh")
        if any(
            name in values and _has_executable_url_scheme(values[name])
            for name in GOVERNED_EXECUTABLE_URL_ATTRIBUTES
        ):
            self.violations.add("executable-url")
        if tag == "datalist":
            self.violations.add("non-rendering-container")
        if "style" in attribute_names:
            self.violations.add("inline-style")
        if "class" in attribute_names:
            self.violations.add("stylesheet")
        if tag == "bdo" or "dir" in attribute_names:
            self.violations.add("bidirectional")
        if tag == "details":
            if "open" not in attribute_names:
                self.violations.add("closed-details")

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        # Apply the same policy to ordinary and self-closing tag syntax.
        self.handle_starttag(tag, attrs)


def _governed_surface_html_violations(markdown: str) -> set[str]:
    """Inspect live rendered structure while leaving comments/code inert."""
    parser = _GovernedSurfaceHTMLParser()
    html_spans: list[tuple[int, int]] = []
    structure = _rendered_structure(markdown, html_spans=html_spans)
    # Exclude definite same-line literal code examples before parsing HTML.
    # Delimiter runs inside a raw HTML attribute are not Markdown syntax.
    # Multiline code ambiguity remains fail-closed at this HTML preflight.
    characters = list(structure)
    cursor = 0
    span_index = 0
    while cursor < len(structure):
        while span_index < len(html_spans) and html_spans[span_index][1] <= cursor:
            span_index += 1
        if span_index < len(html_spans) and html_spans[span_index][0] <= cursor:
            cursor = html_spans[span_index][1]
            continue
        tag_match = PREFLIGHT_HTML_TAG.match(structure, cursor)
        if tag_match is not None:
            cursor = tag_match.end()
            continue
        if structure[cursor] != "`":
            cursor += 1
            continue
        run_end = cursor + 1
        while run_end < len(structure) and structure[run_end] == "`":
            run_end += 1
        backslashes = 0
        previous = cursor - 1
        while previous >= 0 and structure[previous] == "\\":
            backslashes += 1
            previous -= 1
        if backslashes % 2:
            cursor = run_end
            continue
        line_end = re.search(r"[\r\n]", structure[run_end:])
        limit = run_end + line_end.start() if line_end is not None else len(structure)
        closer = next((
            match for match in re.finditer(r"`+", structure[run_end:limit])
            if len(match.group()) == run_end - cursor
        ), None)
        if closer is None:
            cursor = run_end
            continue
        end = run_end + closer.end()
        characters[cursor:end] = " " * (end - cursor)
        cursor = end
    parser.feed("".join(characters))
    parser.close()
    return parser.violations


def _assert_supported_governed_html(violations: set[str]) -> None:
    """Fail closed on rendering semantics outside the shared text contract."""
    descriptions = {
        "replacement-content": "replacement-content HTML",
        "raw-svg": "raw SVG HTML",
        "inline-style": "inline style HTML",
        "semantic-deletion": "semantic deletion HTML",
        "stylesheet": "stylesheet/class-driven HTML",
        "raw-mathml": "raw MathML HTML",
        "bidirectional": "bidirectional HTML",
        "conditional-raw-text": "conditional/legacy raw-text HTML",
        "shadow-root": "declarative shadow-root HTML",
        "meta-refresh": "meta-refresh HTML",
        "executable-script": "executable script HTML",
        "executable-url": "executable URL HTML",
        "event-handler": "inline event-handler HTML",
        "document-root": "document-root HTML",
        "non-rendering-container": "non-rendering datalist HTML",
    }
    for kind, description in descriptions.items():
        assert kind not in violations, (
            f"{description} is not allowed on governed methodology surfaces"
        )


def _visible_text(markdown: str) -> str:
    """Return browser-visible text without hidden HTML or link metadata."""
    violations = _governed_surface_html_violations(markdown)
    _assert_supported_governed_html(violations)
    assert "raw-image" not in violations, (
        "raw image HTML is not allowed on governed methodology surfaces"
    )
    assert "canvas" not in violations, (
        "canvas fallback HTML is not allowed on governed methodology surfaces"
    )
    assert "closed-details" not in violations, (
        "default-closed <details> is not allowed on governed methodology surfaces"
    )
    assert INTERACTIVE_FORM_CONTROL_PATTERN.search(markdown) is None, (
        "interactive form control HTML is not allowed on governed methodology surfaces"
    )
    visible = _mask_link_reference_definitions_for_visibility(markdown)
    visible = _replace_inline_markdown_links_for_visibility(visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    # HTMLParser(convert_charrefs=True) already performs the browser's one
    # character-reference decoding pass. A second html.unescape() would turn
    # literal entity-looking text into content the browser never displays.
    assert not any(marker in visible for marker in RAW_HTML_LITERAL_PUNCTUATION.values()), (
        "reserved literal-punctuation marker in governed source"
    )
    visible = _visible_html_text(visible, protect_raw_punctuation=True)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    for literal, marker in RAW_HTML_LITERAL_PUNCTUATION.items():
        visible = visible.replace(marker, literal)
    return " ".join(visible.split())

def _visible_markdown_heading_span(structure: str, heading: str) -> tuple[int, int]:
    """Return the unique browser-visible Markdown heading span with preserved offsets."""
    # Inspect before slicing or hidden-region masking can erase a wrapper
    # that starts before the heading or encloses otherwise canonical text.
    _assert_supported_governed_html(_governed_surface_html_violations(structure))
    visible_structure = _mask_hidden_html_regions(structure)
    matches: list[tuple[int, int]] = []
    offset = 0
    for raw_line in visible_structure.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        logical, is_code, _ = _parse_fence_container_prefixes(line)
        if not is_code and logical.strip(" \t") == heading:
            matches.append((offset, offset + len(raw_line)))
        offset += len(raw_line)
    assert len(matches) == 1, (
        f"expected exactly one rendered heading {heading!r}, found {len(matches)}"
    )
    return matches[0]


def _rendered_policing_workstream(roadmap: str) -> str:
    try:
        # Global styles and ancestor direction can affect a section even when
        # their source lies outside its heading boundaries.
        _assert_supported_governed_html(_governed_surface_html_violations(roadmap))
        structure = _rendered_structure(roadmap)
        start, _ = _visible_markdown_heading_span(structure, WORKSTREAM_HEADING)
    except AssertionError as exc:
        raise AssertionError("rendered policing workstream is missing; missing policing-workstream safeguard") from exc
    end, _ = _visible_markdown_heading_span(structure, WORKSTREAM_END_HEADING)
    assert start < end, "rendered policing workstream boundary is invalid"
    assert "closed-details" not in _governed_surface_html_violations(roadmap[start:end]), (
        "default-closed <details> is not allowed in the rendered policing workstream"
    )
    visible_structure = _mask_hidden_html_regions(structure)
    return visible_structure[start:end]



def _normalised_visible_workstream_lines(rendered: str) -> list[str]:
    """Return the canonical browser-visible line sequence used by Workstream I integrity."""
    visible_lines: list[str] = []
    for raw_line in rendered.splitlines():
        line = _visible_text(raw_line).strip()
        line = re.sub(r"^(?:[-+*]|\d{1,9}[.)])\s+", "", line)
        if line:
            visible_lines.append(line)
    return visible_lines


def _validate_policing_workstream(roadmap: str) -> None:
    rendered = _rendered_policing_workstream(roadmap)
    workstream = _visible_text(rendered)
    visible_lines = _normalised_visible_workstream_lines(rendered)

    for clause in REQUIRED_CLAUSES:
        visible_clause = _visible_text(clause)
        if clause in AFFIRMATIVE_LINE_PREFIX_CLAUSES:
            expected_line = _visible_text(
                AFFIRMATIVE_EXACT_LINE_OVERRIDES.get(clause, clause)
            )
            assert any(line == expected_line for line in visible_lines), (
                f"missing policing-workstream safeguard: {clause}"
            )
        else:
            assert visible_clause in workstream, f"missing policing-workstream safeguard: {clause}"


    integrity_value = "\n".join(visible_lines)
    integrity_hash = hashlib.sha256(integrity_value.encode("utf-8")).hexdigest()
    assert integrity_hash == POLICING_WORKSTREAM_VISIBLE_SHA256, (
        "browser-visible policing workstream changed: expected hash "
        f"{POLICING_WORKSTREAM_VISIBLE_SHA256!r}, got {integrity_hash!r}"
    )

def test_policing_context_workstream_remains_source_gated_and_noncomparative():
    _validate_policing_workstream(ROADMAP.read_text(encoding="utf-8"))


def test_policing_item_metadata_contract_is_mandatory_and_complete():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    rendered = _rendered_policing_workstream(roadmap)
    visible = _visible_text(rendered)
    assert "Every implemented item should record" not in visible
    assert (
        "Every implemented item must record, at minimum, the relevant country, "
        "jurisdiction, agency or institutional role, encounter type, source date or "
        "version, registered source identifiers or links supporting any legal or "
        "procedural condition supplied to the model, and claim type."
    ) in visible


@pytest.mark.parametrize(
    "wrapper",
    (
        "comment",
        "fence",
        "blockquote-fence",
        "list-fence",
        "compound-list-quote-fence",
        "indented-code",
        "tab-indented-code",
    ),
)
def test_policing_context_workstream_must_remain_rendered(wrapper: str):
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_HEADING)
    end = roadmap.index(WORKSTREAM_END, start)
    section = roadmap[start:end]

    if wrapper == "comment":
        hidden = f"<!--\n{section}\n-->"
    elif wrapper == "fence":
        hidden = f"````\n{section}\n````"
    elif wrapper == "blockquote-fence":
        quoted = "".join(
            f"> {line}" if line.strip() else ">\n"
            for line in section.splitlines(keepends=True)
        )
        hidden = f"> ````\n{quoted}> ````\n"
    elif wrapper == "list-fence":
        nested = "".join(
            f"  {line}" if line.strip() else "  \n"
            for line in section.splitlines(keepends=True)
        )
        hidden = f"- ````\n{nested}  ````\n"
    elif wrapper == "compound-list-quote-fence":
        nested = "".join(
            f"  > {line}" if line.strip() else "  >\n"
            for line in section.splitlines(keepends=True)
        )
        hidden = f"- > ````\n{nested}  > ````\n"
    elif wrapper == "tab-indented-code":
        hidden = "".join(
            f"\t{line}" if line.strip() else line
            for line in section.splitlines(keepends=True)
        )
    else:
        hidden = "".join(
            f"    {line}" if line.strip() else line
            for line in section.splitlines(keepends=True)
        )

    mutated = roadmap[:start] + hidden + roadmap[end:]
    with pytest.raises(AssertionError, match="rendered policing workstream"):
        _validate_policing_workstream(mutated)


@pytest.mark.parametrize("tag", ("details", "dialog"))
def test_policing_context_workstream_cannot_hide_in_closed_html_container(tag: str):
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_HEADING)
    end = roadmap.index(WORKSTREAM_END, start)
    section = roadmap[start:end]
    hidden = f"<{tag}>\n{section}\n</{tag}>\n"
    mutated = roadmap[:start] + hidden + roadmap[end:]
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


def test_shared_governance_reducer_rejects_canvas_fallback():
    with pytest.raises(AssertionError, match="canvas fallback HTML"):
        _visible_text("<canvas>Current sources may be skipped.</canvas>")


def test_closed_details_summary_cannot_escape_policing_integrity():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    contradiction = (
        "<details><summary>Current sources may be skipped.</summary></details>\n\n"
    )
    mutated = roadmap.replace(WORKSTREAM_END, contradiction + WORKSTREAM_END, 1)
    with pytest.raises(AssertionError, match="default-closed <details>"):
        _validate_policing_workstream(mutated)


def test_policing_fence_container_ownership_hides_top_level_code_payload():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "register official and current sources for each Australian and United States jurisdictional claim"
    original = f"- {clause} before adopting it as benchmark context;"
    replacement = (
        "- > ```\n"
        "```\n"
        f"{clause};\n"
        "```\n"
        "> ```"
    )
    assert original in roadmap
    mutated = roadmap.replace(original, replacement, 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


@pytest.mark.parametrize("label", ("sources required", "sources [required]"))
def test_policing_safeguard_cannot_hide_in_link_title(label: str):
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "register official and current sources for each Australian and United States jurisdictional claim"
    replacement = f'[{label}](# "{clause}")'
    mutated = roadmap.replace(clause, replacement, 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)



def test_policing_safeguard_cannot_hide_in_hidden_html():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "register official and current sources for each Australian and United States jurisdictional claim"
    mutated = roadmap.replace(clause, f"<span hidden>{clause}</span>", 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


def test_policing_safeguard_cannot_hide_with_zero_opacity():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "CASUAL ADDRESS != FRIENDSHIP OR CONSENT"
    assert clause in roadmap
    mutated = roadmap.replace(
        clause,
        f'<span style="opacity:0">{clause}</span>',
        1,
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


def test_policing_source_gate_cannot_be_negated():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "register official and current sources for each Australian and United States jurisdictional claim"
    mutated = roadmap.replace(clause, "never " + clause, 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


@pytest.mark.parametrize(
    "clause",
    (
        "POLICE TERMINOLOGY != CROSS-JURISDICTION EQUIVALENCE",
        "CALM TONE != ABSENCE OF COERCIVE AUTHORITY",
        "POLITE WORDING != VOLUNTARY CHOICE",
        "ONE AGENCY != A NATIONAL POLICING SYSTEM",
        "ONE ENCOUNTER != SYSTEM-WIDE GROUND TRUTH",
    ),
)
def test_policing_scope_boundaries_are_all_required(clause: str):
    roadmap = ROADMAP.read_text(encoding="utf-8")
    assert clause in roadmap
    mutated = roadmap.replace(clause, "REMOVED POLICING BOUNDARY", 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


def test_policing_source_gate_cannot_be_suffix_negated():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    original = (
        "register official and current sources for each Australian and United States "
        "jurisdictional claim before adopting it as benchmark context;"
    )
    contradictory = (
        "register official and current sources for each Australian and United States "
        "jurisdictional claim only when convenient; no source is actually mandatory"
    )
    assert original in roadmap
    mutated = roadmap.replace(original, contradictory, 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)

def test_policing_workstream_start_must_be_a_visible_heading():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_HEADING)
    end = roadmap.index(WORKSTREAM_END, start)
    body = roadmap[start + len(WORKSTREAM_HEADING):end]
    mutated = (
        roadmap[:start]
        + f'[boundary](# "{WORKSTREAM_HEADING}")'
        + body
        + "\n"
        + WORKSTREAM_HEADING
        + roadmap[end:]
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


def test_policing_source_gate_cannot_hide_in_multiline_link_title():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "source-gated research proposal"
    mutated = roadmap.replace(
        clause,
        f'[placeholder](#\n "{clause}")',
        1,
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


def test_policing_svg_title_does_not_supply_visible_source_gate():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "source-gated research proposal"
    mutated = roadmap.replace(
        clause,
        f"<svg><title>{clause}</title></svg>",
        1,
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


def test_policing_visibility_ignores_reference_definition_titles():
    clause = REQUIRED_CLAUSES[-1]
    for hidden in (
        f'[hidden]: # "{clause}"',
        f'> [hidden]: # "{clause}"',
        f'- > [hidden]: # "{clause}"',
    ):
        assert clause not in _visible_text(hidden)



def test_policing_companion_contradiction_changes_complete_visible_section():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    source_gate = AFFIRMATIVE_EXACT_LINE_OVERRIDES[
        "register official and current sources for each Australian and United States jurisdictional claim"
    ]
    mutated = roadmap.replace(
        source_gate,
        source_gate
        + "\n- Official and current sources are optional for every jurisdictional claim.",
        1,
    )
    with pytest.raises(AssertionError, match="browser-visible policing workstream changed"):
        _validate_policing_workstream(mutated)



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


def test_latest_review_shared_css_escape_and_raw_html_block_regressions():
    for markup in (
        '<span style="display:n\\6f ne">hidden governance</span>',
        '<span style="content-visibility:hidden">hidden governance</span>',
    ):
        assert _visible_html_text(markup) == ""
        with pytest.raises(AssertionError, match="inline style HTML"):
            _visible_text(markup)

    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_HEADING)
    end = roadmap.index(WORKSTREAM_END, start)
    section = roadmap[start:end]
    mutated = roadmap[:start] + f"<pre>\n{section}\n</pre>\n" + roadmap[end:]
    with pytest.raises(AssertionError, match="rendered policing workstream"):
        _validate_policing_workstream(mutated)

def test_fresh_review_inline_html_adjacency_is_preserved():
    assert _visible_text("Every<span></span>implemented") == "Everyimplemented"

    roadmap = ROADMAP.read_text(encoding="utf-8")
    sentence = REQUIRED_CLAUSES[3]
    assert sentence in roadmap
    mutated = roadmap.replace(
        sentence,
        sentence.replace("Every implemented", "Every<span></span>implemented", 1),
        1,
    )
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)


def test_fresh_review_duplicate_html_attribute_preserves_first_value():
    sentence = REQUIRED_CLAUSES[3]
    hidden = f'<span style="display:none" style="display:inline">{sentence}</span>'
    assert sentence not in _visible_html_text(hidden)
    with pytest.raises(AssertionError, match="inline style HTML"):
        _visible_text(hidden)

    roadmap = ROADMAP.read_text(encoding="utf-8")
    assert sentence in roadmap
    mutated = roadmap.replace(sentence, hidden, 1)
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)


def test_fresh_review_interactive_form_control_is_rejected():
    with pytest.raises(AssertionError, match="interactive form control HTML"):
        _visible_text('<input value="Current sources may be skipped.">')

    roadmap = ROADMAP.read_text(encoding="utf-8")
    end = roadmap.index(WORKSTREAM_END, roadmap.index(WORKSTREAM_HEADING))
    mutated = roadmap[:end] + '\n<input value="Current sources may be skipped.">\n' + roadmap[end:]
    with pytest.raises(AssertionError, match="interactive form control HTML"):
        _validate_policing_workstream(mutated)


def test_fresh_review_html_title_is_non_rendering():
    sentence = REQUIRED_CLAUSES[3]
    assert _visible_text(f"<title>{sentence}</title>") == ""

    roadmap = ROADMAP.read_text(encoding="utf-8")
    assert sentence in roadmap
    mutated = roadmap.replace(sentence, f"<title>{sentence}</title>", 1)
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)
@pytest.mark.parametrize(
    ("markup", "kind"),
    (
        ('<a href="javascript:alert(1)">governed clause</a>', "executable-url"),
        ('<a href="java&#x0A;script:alert(1)">governed clause</a>', "executable-url"),
        ('<form action="vbscript:msgbox(1)">governed clause</form>', "executable-url"),
        ('<datalist><option>governed clause</option></datalist>', "non-rendering-container"),
    ),
)
def test_governed_surface_preflight_rejects_executable_urls_and_datalist(
    markup: str,
    kind: str,
) -> None:
    violations = _governed_surface_html_violations(markup)
    assert kind in violations
    with pytest.raises(AssertionError):
        _assert_supported_governed_html(violations)

def test_latest_active_html_policy_rejects_event_handlers_and_document_roots():
    handler = _governed_surface_html_violations(
        '<span onclick="document.body.textContent=\'weakened\'">canonical text</span>'
    )
    assert "event-handler" in handler
    with pytest.raises(AssertionError, match="event-handler"):
        _assert_supported_governed_html(handler)

    for tag in ("html", "body"):
        root_tag = _governed_surface_html_violations(f"<{tag} hidden></{tag}>")
        assert "document-root" in root_tag
        with pytest.raises(AssertionError, match="document-root"):
            _assert_supported_governed_html(root_tag)


def test_policing_workstream_rejects_event_handlers_before_section_slicing():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "source-gated research proposal"
    mutated = roadmap.replace(
        clause,
        '<span onclick="document.body.textContent=\'weakened\'">'
        + clause
        + "</span>",
        1,
    )
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)


@pytest.mark.parametrize("tag", ("html", "body"))
def test_policing_workstream_rejects_duplicate_document_root_tags(tag: str):
    roadmap = ROADMAP.read_text(encoding="utf-8")
    mutated = roadmap + f"\n<{tag} hidden></{tag}>\n"
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)
