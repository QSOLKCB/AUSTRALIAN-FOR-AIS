"""Regression checks for the proposed policing-context research workstream."""

from dataclasses import dataclass
from pathlib import Path
import html
from html.parser import HTMLParser
import re

import pytest


ROADMAP = Path(__file__).parent.parent / "ROADMAP.md"
WORKSTREAM_HEADING = "### I. Australian and United States policing-context transfer"
WORKSTREAM_END = "\n---\n\n## Phase 3"


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
)

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
HTML_TAG_PATTERN = re.compile(r"</?[A-Za-z][^>]*>|<![A-Za-z][^>]*>|<\?[\s\S]*?\?>")
NON_RENDERING_HTML_PATTERN = re.compile(
    r"<(script|style|template)\b[^>]*>.*?</\1\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)


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
        if "hidden" in values:
            return True
        if values.get("aria-hidden", "").strip().lower() == "true":
            return True
        style = re.sub(r"\s+", "", values.get("style", "").lower())
        return "display:none" in style or "visibility:hidden" in style

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        inherited = self.stack[-1][1] if self.stack else False
        self.stack.append((tag.lower(), inherited or self._is_hidden(tag, attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

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



def _visible_text(markdown: str) -> str:
    """Return browser-visible text without hidden HTML or link metadata."""
    visible = MARKDOWN_IMAGE_PATTERN.sub(" ", markdown)
    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = _visible_html_text(visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return " ".join(visible.split())

def _rendered_policing_workstream(roadmap: str) -> str:
    structure = _rendered_structure(roadmap)
    assert WORKSTREAM_HEADING in structure, "rendered policing workstream is missing"
    start = structure.index(WORKSTREAM_HEADING)
    end = structure.index(WORKSTREAM_END, start)
    return structure[start:end]



def _validate_policing_workstream(roadmap: str) -> None:
    rendered = _rendered_policing_workstream(roadmap)
    workstream = _visible_text(rendered)
    visible_lines: list[str] = []
    for raw_line in rendered.splitlines():
        line = _visible_text(raw_line).strip()
        line = re.sub(r"^(?:[-+*]|\d{1,9}[.)])\s+", "", line)
        if line:
            visible_lines.append(line)

    for clause in REQUIRED_CLAUSES:
        visible_clause = _visible_text(clause)
        if clause in AFFIRMATIVE_LINE_PREFIX_CLAUSES:
            assert any(line.startswith(visible_clause) for line in visible_lines), (
                f"missing policing-workstream safeguard: {clause}"
            )
        else:
            assert visible_clause in workstream, f"missing policing-workstream safeguard: {clause}"

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


def test_policing_safeguard_cannot_hide_in_link_title():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "register official and current sources for each Australian and United States jurisdictional claim"
    replacement = f'[sources required](# "{clause}")'
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
