"""Regression checks for Workstream H listener-variable and source-governance design."""

from pathlib import Path
import html
from html.parser import HTMLParser
import re


ROOT = Path(__file__).parent.parent
ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"

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
        if tag == "details" and "open" not in values:
            return True
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


def _visible_markdown_text(markdown: str) -> str:
    """Return browser-visible safeguard text, excluding Markdown metadata."""
    visible = MARKDOWN_IMAGE_PATTERN.sub(" ", markdown)
    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = _visible_html_text(visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return " ".join(visible.split())


def _workstream_h(text: str) -> str:
    start = text.index("### H. Slang density")
    end = text.index("### I. Australian and United States policing-context transfer", start)
    return _visible_markdown_text(text[start:end])


def _trans_tasman_methodology(text: str) -> str:
    start = text.index("## Trans-Tasman and Slang/Operational Experiment Design")
    end = text.index("## Australian and United States Policing-Context Experiment Design", start)
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
        f'[placeholder](# "{listener_clause}")',
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
    ):
        mutated = methodology.replace(stereotype_clause, hidden, 1)
        assert stereotype_clause not in _trans_tasman_methodology(mutated)
