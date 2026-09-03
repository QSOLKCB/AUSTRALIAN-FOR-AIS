"""Regression checks for Workstream H listener-variable and source-governance design."""

from pathlib import Path
import html
from html.parser import HTMLParser
import re
import runpy


ROOT = Path(__file__).parent.parent
ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"
POLICING_TEST = Path(__file__).parent / "test_policing_context_roadmap.py"
WORKSTREAM_H_HEADING = "### H. Slang density, register compression, and operational intelligibility"
WORKSTREAM_I_HEADING = "### I. Australian and United States policing-context transfer"
TRANS_TASMAN_METHODOLOGY_HEADING = "## Trans-Tasman and Slang/Operational Experiment Design"
POLICING_METHODOLOGY_HEADING = "## Australian and United States Policing-Context Experiment Design"

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

HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})


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
        if values.get("aria-hidden", "").strip().lower() == "true":
            return True
        style = re.sub(
            r"/\*.*?\*/",
            "",
            values.get("style", "").lower(),
            flags=re.DOTALL,
        )
        style = re.sub(r"\s+", "", style)
        return "display:none" in style or "visibility:hidden" in style

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
        # Match browser tree construction: self-closing syntax does not close
        # non-void HTML elements such as <dialog />.
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


def _visible_markdown_text(markdown: str) -> str:
    """Return browser-visible safeguard text using the canonical policing reducer."""
    namespace = runpy.run_path(str(POLICING_TEST))
    return namespace["_visible_text"](markdown)


def _rendered_heading_span(text: str, heading: str) -> tuple[int, int]:
    """Locate one browser-visible heading using the hardened structural renderer."""
    namespace = runpy.run_path(str(POLICING_TEST))
    structure = namespace["_rendered_structure"](text)
    return namespace["_visible_markdown_heading_span"](structure, heading)


def _workstream_h(text: str) -> str:
    start, _ = _rendered_heading_span(text, WORKSTREAM_H_HEADING)
    end, _ = _rendered_heading_span(text, WORKSTREAM_I_HEADING)
    assert start < end, "rendered Workstream H boundary is invalid"
    return _visible_markdown_text(text[start:end])


def _trans_tasman_methodology(text: str) -> str:
    start, _ = _rendered_heading_span(text, TRANS_TASMAN_METHODOLOGY_HEADING)
    end, _ = _rendered_heading_span(text, POLICING_METHODOLOGY_HEADING)
    assert start < end, "rendered Trans-Tasman methodology boundary is invalid"
    return _visible_markdown_text(text[start:end])


def test_workstream_h_decouples_dialect_exposure_from_listener_identity():
    section = _workstream_h(ROADMAP.read_text(encoding="utf-8"))
    assert "self-reported or experimentally established Australian-English exposure" in section
    assert "independently of general English-language background or proficiency" in section
    assert "nationality and first-language identity must not define the comparison cohorts" in section
    assert "familiar Australian speakers, other English-speaking partners" not in section


def test_canonical_methodology_crosses_listener_variables_independently():
    section = _trans_tasman_methodology(
        METHODOLOGY.read_text(encoding="utf-8")
    )
    assert "Australian-English familiarity or exposure" in section
    assert "self-reported or experimentally established" in section
    assert "neither nationality nor first-language category acts as a proxy for comprehension" in section
    assert "higher versus lower Australian-English familiarity crossed or matched" in section


def test_workstream_h_keeps_community_attestation_bounded():
    section = _workstream_h(ROADMAP.read_text(encoding="utf-8"))
    assert "orientation/community-attestation sources with explicit non-representative status" in section
    assert "converting crowd-sourced examples directly into benchmark data" in section


def test_trans_tasman_methodology_never_allows_exact_group_stereotype_wording():
    section = _trans_tasman_methodology(
        METHODOLOGY.read_text(encoding="utf-8")
    )
    assert "An attributable source may document that a stereotype existed" in section
    assert "exact group-stereotyping wording must not be reproduced" in section
    assert "unless exact material has an attributable source" not in section


def test_workstream_h_and_methodology_safeguards_must_be_browser_visible():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    listener_clause = "nationality and first-language identity must not define the comparison cohorts"
    assert listener_clause in _workstream_h(roadmap)
    for hidden in (
        f"<!-- {listener_clause} -->",
        f"<span hidden>{listener_clause}</span>",
        f"<dialog>{listener_clause}</dialog>",
        f"<dialog />{listener_clause}</dialog>",
        f'<span style="display:/**/none">{listener_clause}</span>',
        f'[placeholder](# "{listener_clause}")',
        f'[placeholder](#\n"{listener_clause}")',
    ):
        mutated = roadmap.replace(listener_clause, hidden, 1)
        assert listener_clause not in _workstream_h(mutated)

    methodology = METHODOLOGY.read_text(encoding="utf-8")
    stereotype_clause = "exact group-stereotyping wording must not be reproduced"
    assert stereotype_clause in _trans_tasman_methodology(methodology)
    for hidden in (
        f"<!-- {stereotype_clause} -->",
        f"<span hidden>{stereotype_clause}</span>",
        f'[placeholder](# "{stereotype_clause}")',
        f'[placeholder [nested]](# "{stereotype_clause}")',
    ):
        mutated = methodology.replace(stereotype_clause, hidden, 1)
        assert stereotype_clause not in _trans_tasman_methodology(mutated)


def test_workstream_h_start_must_be_a_visible_heading():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_H_HEADING)
    end = roadmap.index(WORKSTREAM_I_HEADING, start)
    body = roadmap[start + len(WORKSTREAM_H_HEADING):end]
    mutated = (
        roadmap[:start]
        + f'[boundary](# "{WORKSTREAM_H_HEADING}")'
        + body
        + "\n"
        + WORKSTREAM_H_HEADING
        + "\n\n"
        + roadmap[end:]
    )
    section = _workstream_h(mutated)
    assert "nationality and first-language identity must not define the comparison cohorts" not in section
    assert "orientation/community-attestation sources with explicit non-representative status" not in section


def test_trans_tasman_methodology_start_must_be_a_visible_heading():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    start = methodology.index(TRANS_TASMAN_METHODOLOGY_HEADING)
    end = methodology.index(POLICING_METHODOLOGY_HEADING, start)
    body = methodology[start + len(TRANS_TASMAN_METHODOLOGY_HEADING):end]
    mutated = (
        methodology[:start]
        + f'[boundary](# "{TRANS_TASMAN_METHODOLOGY_HEADING}")'
        + body
        + "\n\n"
        + TRANS_TASMAN_METHODOLOGY_HEADING
        + "\n\n"
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


def test_workstream_h_visibility_ignores_reference_definition_titles():
    clause = "nationality and first-language identity must not define the comparison cohorts"
    for hidden in (
        f'[hidden]: # "{clause}"',
        f'> [hidden]: # "{clause}"',
        f'- > [hidden]: # "{clause}"',
    ):
        assert clause not in _visible_markdown_text(hidden)
