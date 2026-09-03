"""Regression checks for the proposed policing-context research workstream."""

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


def _mask_non_newline(text: str) -> str:
    return "".join(character if character in "\r\n" else " " for character in text)


def _rendered_structure(markdown: str) -> str:
    """Mask fenced code and HTML comments while preserving source offsets."""
    parts: list[str] = []
    in_comment = False
    fence_character: str | None = None
    fence_length = 0

    for raw_line in markdown.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        stripped = line.lstrip(" ")
        indentation = len(line) - len(stripped)

        if fence_character is not None:
            parts.append(_mask_non_newline(raw_line))
            if indentation <= 3 and re.fullmatch(
                rf"{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
                stripped,
            ):
                fence_character = None
                fence_length = 0
            continue

        if not in_comment and indentation <= 3:
            opener = re.fullmatch(r"(?P<fence>`{3,}|~{3,}).*", stripped)
            if opener:
                marker = opener.group("fence")
                fence_character = marker[0]
                fence_length = len(marker)
                parts.append(_mask_non_newline(raw_line))
                continue

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
                    position = len(raw_line)
                    break
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

        parts.append("".join(characters))

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


@pytest.mark.parametrize("wrapper", ("comment", "fence"))
def test_policing_context_workstream_must_remain_rendered(wrapper: str):
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_HEADING)
    end = roadmap.index(WORKSTREAM_END, start)
    section = roadmap[start:end]
    hidden = (
        f"<!--\n{section}\n-->"
        if wrapper == "comment"
        else f"````\n{section}\n````"
    )
    mutated = roadmap[:start] + hidden + roadmap[end:]
    with pytest.raises(AssertionError, match="rendered policing workstream"):
        _validate_policing_workstream(mutated)
