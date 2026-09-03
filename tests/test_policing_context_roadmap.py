"""Regression checks for the proposed policing-context research workstream."""

from dataclasses import dataclass
from pathlib import Path
import hashlib
import html
from html.parser import HTMLParser
import re

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


def _css_hides_element(style: str) -> bool:
    """Apply inline CSS declaration order and !important precedence."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())
    winners: dict[str, tuple[bool, str]] = {}
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        name, raw_value = declaration.split(":", 1)
        name = name.strip()
        if name not in {"display", "visibility"}:
            continue
        raw_value = raw_value.strip()
        important = re.search(r"\s*!important\s*$", raw_value) is not None
        value = re.sub(r"\s*!important\s*$", "", raw_value).strip()
        previous = winners.get(name)
        if previous is None or (important and not previous[0]) or important == previous[0]:
            winners[name] = (important, value)

    display = winners.get("display", (False, ""))[1]
    visibility = winners.get("visibility", (False, ""))[1]
    return display == "none" or visibility in {"hidden", "collapse"}


class _VisibleHTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []

    @staticmethod
    def _is_hidden(tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        tag = tag.lower()
        if tag in {"script", "style", "template"}:
            return True
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag in {"details", "dialog"} and "open" not in values:
            return True
        if "hidden" in values:
            return True
        return _css_hides_element(values.get("style", ""))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        inherited = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _ in self.stack)
        )
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
            self.parts.append(data)


def _visible_html_text(text: str) -> str:
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    return " ".join(parser.parts)


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


def _rendered_structure(markdown: str) -> str:
    """Mask code and comments while preserving rendered prose for inspection."""
    parts: list[str] = []
    in_comment = False
    fence: FenceState | None = None
    paragraph_open = False

    for raw_line in markdown.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            paragraph_open = False

        while fence is not None and not _fence_container_continues(line, fence):
            fence = None

        if fence is not None:
            parts.append(_mask_non_newline(raw_line))
            if _is_fence_closer(line, fence):
                fence = None
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

        rendered_line, in_comment = _mask_comments_on_line(raw_line, False)
        parts.append(rendered_line)
        paragraph_open = _line_opens_paragraph(rendered_line)

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


def _visible_text(markdown: str) -> str:
    """Return browser-visible text without hidden HTML or link metadata."""
    visible = _mask_link_reference_definitions_for_visibility(markdown)
    visible = _replace_inline_markdown_links_for_visibility(visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = _visible_html_text(visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return " ".join(visible.split())

def _visible_markdown_heading_span(structure: str, heading: str) -> tuple[int, int]:
    """Return the unique browser-visible Markdown heading span with preserved offsets."""
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
    structure = _rendered_structure(roadmap)
    try:
        start, _ = _visible_markdown_heading_span(structure, WORKSTREAM_HEADING)
    except AssertionError as exc:
        raise AssertionError("rendered policing workstream is missing; missing policing-workstream safeguard") from exc
    end, _ = _visible_markdown_heading_span(structure, WORKSTREAM_END_HEADING)
    assert start < end, "rendered policing workstream boundary is invalid"
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
