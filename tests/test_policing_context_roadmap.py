"""Regression checks for the proposed policing-context research workstream."""

from dataclasses import dataclass
from pathlib import Path
import re

import pytest


ROADMAP = Path(__file__).parent.parent / "ROADMAP.md"
WORKSTREAM_HEADING = "### I. Australian and United States policing-context transfer"
WORKSTREAM_END = "\n---\n\n## Phase 3"


REQUIRED_CLAUSES = (
    WORKSTREAM_HEADING,
    "source-gated research proposal",
    "not legal advice",
    "Every implemented item should record the relevant country, jurisdiction, institutional role, encounter type, and source date.",
    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",
    "CASUAL ADDRESS != FRIENDSHIP OR CONSENT",
    "FICTIONAL POLICE TROPE != OPERATIONAL POLICY",
    "JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER",
    "LEGAL INFORMATION != LEGAL ADVICE",
    "register official and current sources for each Australian and United States jurisdictional claim",
)

LIST_CONTAINER_PREFIX_PATTERN = re.compile(r"(?:[-+*]|\d{1,9}[.)])[ \t]+")
FENCE_PATTERN = re.compile(r"(?P<fence>`{3,}|~{3,})(?P<info>.*)")
THEMATIC_BREAK_PATTERN = re.compile(
    r"(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,}"
)


@dataclass(frozen=True)
class LineContext:
    quote_depth: int
    after_quotes: str
    leading_spaces: int
    logical: str
    list_indent: int | None
    indented_code: bool


@dataclass(frozen=True)
class FenceState:
    character: str
    minimum_length: int
    quote_depth: int
    list_indent: int | None


def _mask_non_newline(text: str) -> str:
    return "".join(character if character in "\r\n" else " " for character in text)


def _line_context(line: str) -> LineContext:
    """Describe CommonMark quote/list prefixes without erasing code indentation."""
    value = line.rstrip("\r\n")
    position = 0
    quote_depth = 0

    while True:
        probe = position
        spaces = 0
        while spaces < 3 and probe < len(value) and value[probe] == " ":
            probe += 1
            spaces += 1
        if probe >= len(value) or value[probe] != ">":
            break
        quote_depth += 1
        probe += 1
        if probe < len(value) and value[probe] in " \t":
            probe += 1
        position = probe

    after_quotes = value[position:]
    leading_spaces = len(after_quotes) - len(after_quotes.lstrip(" "))
    list_indent: int | None = None
    logical_start = min(leading_spaces, 3)

    if leading_spaces <= 3:
        marker = LIST_CONTAINER_PREFIX_PATTERN.match(after_quotes, leading_spaces)
        if marker:
            list_indent = marker.end()
            logical_start = marker.end()

    indented_code = list_indent is None and leading_spaces >= 4
    return LineContext(
        quote_depth=quote_depth,
        after_quotes=after_quotes,
        leading_spaces=leading_spaces,
        logical=after_quotes[logical_start:],
        list_indent=list_indent,
        indented_code=indented_code,
    )


def _fence_opener(line: str) -> FenceState | None:
    context = _line_context(line)
    if context.indented_code:
        return None
    match = FENCE_PATTERN.fullmatch(context.logical.rstrip(" \t"))
    if not match:
        return None
    marker = match.group("fence")
    info = match.group("info")
    if marker[0] == "`" and "`" in info:
        return None
    return FenceState(
        character=marker[0],
        minimum_length=len(marker),
        quote_depth=context.quote_depth,
        list_indent=context.list_indent,
    )


def _fence_container_continues(line: str, state: FenceState) -> bool:
    if not line.strip():
        return True
    context = _line_context(line)
    if context.quote_depth < state.quote_depth:
        return False
    if state.list_indent is not None:
        if context.quote_depth != state.quote_depth:
            return False
        if context.list_indent is not None:
            return False
        return context.leading_spaces >= state.list_indent
    return True


def _fence_logical_line(line: str, state: FenceState) -> str:
    context = _line_context(line)
    if state.list_indent is not None:
        return context.after_quotes[state.list_indent:]
    return context.logical


def _is_fence_closer(line: str, state: FenceState) -> bool:
    logical = _fence_logical_line(line, state).rstrip(" \t")
    return bool(
        re.fullmatch(
            rf"{re.escape(state.character)}{{{state.minimum_length},}}[ \t]*",
            logical,
        )
    )


def _line_opens_paragraph(line: str) -> bool:
    context = _line_context(line)
    logical = context.logical.strip()
    if not logical or context.indented_code:
        return False
    if re.fullmatch(r"#{1,6}(?:[ \t]+.*)?", logical):
        return False
    if THEMATIC_BREAK_PATTERN.fullmatch(logical):
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
    """Mask non-rendered Markdown containers while preserving source offsets."""
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
            paragraph_open = False
            if _is_fence_closer(line, fence):
                fence = None
            continue

        if in_comment:
            rendered_line, in_comment = _mask_comments_on_line(raw_line, True)
            parts.append(rendered_line)
            if not in_comment:
                paragraph_open = _line_opens_paragraph(
                    rendered_line.rstrip("\r\n")
                )
            continue

        context = _line_context(line)
        if context.indented_code and not paragraph_open:
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
        paragraph_open = _line_opens_paragraph(rendered_line.rstrip("\r\n"))

    return "".join(parts)


def _rendered_policing_workstream(roadmap: str) -> str:
    structure = _rendered_structure(roadmap)
    assert WORKSTREAM_HEADING in structure, "rendered policing workstream is missing"
    start = structure.index(WORKSTREAM_HEADING)
    end = structure.index(WORKSTREAM_END, start)
    return structure[start:end]


def _validate_policing_workstream(roadmap: str) -> None:
    workstream = _rendered_policing_workstream(roadmap)
    for clause in REQUIRED_CLAUSES:
        assert clause in workstream, f"missing policing-workstream safeguard: {clause}"


def test_policing_context_workstream_remains_source_gated_and_noncomparative():
    _validate_policing_workstream(ROADMAP.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "wrapper",
    ("comment", "fence", "blockquote-fence", "list-fence", "indented-code"),
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
        quoted = "".join(f"> {line}" if line.strip() else ">\n" for line in section.splitlines(keepends=True))
        hidden = f"> ````\n{quoted}> ````\n"
    elif wrapper == "list-fence":
        nested = "".join(f"  {line}" if line.strip() else "  \n" for line in section.splitlines(keepends=True))
        hidden = f"- ````\n{nested}  ````\n"
    else:
        hidden = "".join(
            f"    {line}" if line.strip() else line
            for line in section.splitlines(keepends=True)
        )

    mutated = roadmap[:start] + hidden + roadmap[end:]
    with pytest.raises(AssertionError, match="rendered policing workstream"):
        _validate_policing_workstream(mutated)
