"""Regression checks for Workstream H listener-variable and source-governance design."""

from pathlib import Path
import hashlib
import html
from html.parser import HTMLParser
import re
import runpy

import pytest


ROOT = Path(__file__).parent.parent
ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"
POLICING_TEST = Path(__file__).parent / "test_policing_context_roadmap.py"
WORKSTREAM_H_HEADING = "### H. Slang density, register compression, and operational intelligibility"
WORKSTREAM_I_HEADING = "### I. Australian and United States policing-context transfer"
TRANS_TASMAN_METHODOLOGY_HEADING = "## Trans-Tasman and Slang/Operational Experiment Design"
POLICING_METHODOLOGY_HEADING = "## Australian and United States Policing-Context Experiment Design"
WORKSTREAM_H_VISIBLE_SHA256 = "c38e4bc194d820c30ee714851ec279da7649fffc921da5a331d722d22d7c34b8"
WORKSTREAM_H_RECORDS_SHA256 = "456bd5d56197844d9f7bab8550bd341346fb30ef8695dbbf9031290b482eb09c"
WORKSTREAM_H_CITATION_LINKS = frozenset({
    ("Australian slang dictionary", "https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary"),
    ("Best Aussie slang", "https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/"),
    ("Communication key on combined exercise", "https://www.defence.gov.au/news-events/news/2022-09-08/communication-key-combined-exercise"),
    ("Partner nations rehearse for war", "https://www.defence.gov.au/news-events/news/2026-06-11/partner-nations-rehearse-war"),
    ("Welcome to Australia", "https://www.awm.gov.au/collection/LIB100000077"),
})
WORKSTREAM_H_CITATION_DESTINATIONS = frozenset(
    destination for _, destination in WORKSTREAM_H_CITATION_LINKS
)
TRANS_TASMAN_VISIBLE_SHA256 = "977cb0423a8e0690383f68ef9915ce049ed6f977feeff4f4ab28d21449db1c9b"
TRANS_TASMAN_SOURCE_STRUCTURE_SHA256 = "b7ddafd25cbc499dca28e3c5ffde094dc4f6115f4ad7995bc3752ab8240c12e2"

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
        if name not in {"display", "visibility", "opacity"}:
            continue
        raw_value = raw_value.strip()
        important = re.search(r"\s*!important\s*$", raw_value) is not None
        value = re.sub(r"\s*!important\s*$", "", raw_value).strip()
        previous = winners.get(name)
        if previous is None or (important and not previous[0]) or important == previous[0]:
            winners[name] = (important, value)

    display = winners.get("display", (False, ""))[1]
    visibility = winners.get("visibility", (False, ""))[1]
    opacity = winners.get("opacity", (False, ""))[1]
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
        or opacity_hidden
    )


class _VisibleHTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []

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
    return "".join(parser.parts)


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


def _inline_markdown_links(text: str) -> tuple[tuple[str, str], ...]:
    """Return rendered non-image inline-link label/destination pairs."""
    links: list[tuple[str, str]] = []
    cursor = 0
    while cursor < len(text):
        bracket = text.find("[", cursor)
        if bracket < 0:
            break
        if _is_escaped_markdown_character(text, bracket):
            cursor = bracket + 1
            continue
        label_end = _balanced_markdown_label_end(text, bracket)
        if label_end is None or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            cursor = bracket + 1
            continue
        paren_start = label_end + 1
        paren_end = _inline_link_closing_paren(text, paren_start)
        if paren_end is None:
            cursor = label_end + 1
            continue
        destination = _inline_link_destination(text[paren_start + 1:paren_end])
        if destination is None:
            cursor = paren_end + 1
            continue
        image = (
            bracket > 0
            and text[bracket - 1] == "!"
            and not _is_escaped_markdown_character(text, bracket - 1)
        )
        if not image:
            label = html.unescape(text[bracket + 1:label_end]).strip()
            links.append((label, html.unescape(destination.strip("<>"))))
        cursor = paren_end + 1
    return tuple(links)


def _inline_markdown_link_destinations(text: str) -> tuple[str, ...]:
    """Return non-image inline-link destinations from a rendered section source."""
    return tuple(destination for _, destination in _inline_markdown_links(text))


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
    namespace["_assert_supported_governed_html"](
        namespace["_governed_surface_html_violations"](text)
    )
    structure = namespace["_rendered_structure"](text)
    return namespace["_visible_markdown_heading_span"](structure, heading)


def _workstream_h_raw(text: str) -> str:
    start, _ = _rendered_heading_span(text, WORKSTREAM_H_HEADING)
    end, _ = _rendered_heading_span(text, WORKSTREAM_I_HEADING)
    assert start < end, "rendered Workstream H boundary is invalid"
    return text[start:end]


def _workstream_h(text: str) -> str:
    return _visible_markdown_text(_workstream_h_raw(text))


def _normalised_workstream_h_visible_value(text: str) -> str:
    return " ".join(_workstream_h(text).split())


class _RawAnchorDetector(HTMLParser):
    """Detect live raw-HTML anchors before Markdown-link masking."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def _record(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            for key, value in attrs:
                if key.lower() == "href":
                    self.hrefs.append(value or "")
                    break

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)


def _raw_html_anchor_hrefs(text: str) -> tuple[str, ...]:
    parser = _RawAnchorDetector()
    parser.feed(text)
    parser.close()
    return tuple(parser.hrefs)


def _rendered_inline_citation_links(
    text: str, *, reject_titles: bool = True
) -> tuple[tuple[str, str], ...]:
    """Use the registry's structural view, not hidden Markdown source text."""
    registry = runpy.run_path(str(POLICING_TEST.with_name("test_research_reference_registry.py")))
    assert not registry["_contains_markdown_structure_in_type6_raw_html"](text), (
        "Workstream H citations must not depend on Markdown made literal by a CommonMark type-6 raw HTML block"
    )
    structure = registry["_structural_registry_text"](text)
    structure = registry["_mask_hidden_html_regions"](structure)
    assert not registry["_contains_inert_html"](structure), (
        "Workstream H citations must not depend on inert, non-navigable HTML"
    )
    raw_anchor_hrefs = _raw_html_anchor_hrefs(structure)
    assert not raw_anchor_hrefs, (
        "Workstream H raw HTML anchors are not allowed; "
        f"got {raw_anchor_hrefs!r}"
    )
    structure = registry["_mask_raw_html_tags_for_markdown_link_discovery"](structure)
    titled_links = [
        link
        for link in registry["_markdown_inline_links"](structure)
        if not link.image and link.title is not None
    ]
    if reject_titles:
        assert not titled_links, (
            "Workstream H citation Markdown link titles are not allowed; "
            "tooltip provenance must remain inside the sealed citation contract"
        )
    return _inline_markdown_links(structure)


def _assert_workstream_h_integrity(text: str) -> str:
    raw_section = _workstream_h_raw(text)
    rendered_links = _rendered_inline_citation_links(raw_section)
    actual_links = set(rendered_links)
    assert len(rendered_links) == len(actual_links), "duplicate Workstream H citation binding"
    actual_destinations = {destination for _, destination in actual_links}
    assert actual_destinations == WORKSTREAM_H_CITATION_DESTINATIONS, (
        "Workstream H citation destinations changed: expected "
        f"{sorted(WORKSTREAM_H_CITATION_DESTINATIONS)!r}, got "
        f"{sorted(actual_destinations)!r}"
    )
    assert actual_links == WORKSTREAM_H_CITATION_LINKS, (
        "Workstream H citation label/destination bindings changed: expected "
        f"{sorted(WORKSTREAM_H_CITATION_LINKS)!r}, got {sorted(actual_links)!r}"
    )
    section = _visible_markdown_text(raw_section)
    policing = runpy.run_path(str(POLICING_TEST))
    visible_records = policing["_normalised_visible_workstream_records"](raw_section)
    unsupported_containers = [
        (signature, line)
        for signature, line in visible_records
        if signature not in {"root", "list:2"}
    ]
    assert not unsupported_containers, (
        "browser-visible Workstream H list/container hierarchy changed: "
        f"{unsupported_containers!r}"
    )
    value = " ".join(section.split())
    actual_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
    assert actual_hash == WORKSTREAM_H_VISIBLE_SHA256, (
        "browser-visible Workstream H changed: expected hash "
        f"{WORKSTREAM_H_VISIBLE_SHA256!r}, got {actual_hash!r}"
    )
    record_value = "\n".join(
        f"{signature}\x1f{line}" for signature, line in visible_records
    )
    actual_record_hash = hashlib.sha256(record_value.encode("utf-8")).hexdigest()
    assert actual_record_hash == WORKSTREAM_H_RECORDS_SHA256, (
        "browser-visible Workstream H record boundaries changed: expected hash "
        f"{WORKSTREAM_H_RECORDS_SHA256!r}, got {actual_record_hash!r}"
    )
    return section


def test_workstream_h_list_hierarchy_is_pinned():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    _assert_workstream_h_integrity(roadmap)
    bullet = (
        "keep any military claims limited to what official or archival evidence "
        "actually demonstrates."
    )
    canonical = f"- {bullet}"
    assert canonical in roadmap
    mutated = roadmap.replace(canonical, f"  - {bullet}", 1)
    with pytest.raises(AssertionError, match="list/container hierarchy changed"):
        _assert_workstream_h_integrity(mutated)


def test_workstream_h_record_boundaries_are_pinned():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    _assert_workstream_h_integrity(roadmap)
    preceding = (
        "- connect suitable tests to Phase 5 adversarial context swaps and Phase 7 "
        "cross-dialect/cross-register comparison;"
    )
    boundary = (
        "- keep any military claims limited to what official or archival evidence "
        "actually demonstrates."
    )
    canonical = preceding + "\n" + boundary
    assert canonical in roadmap
    mutated = roadmap.replace(canonical, preceding + " " + boundary, 1)
    with pytest.raises(AssertionError, match="record boundaries changed"):
        _assert_workstream_h_integrity(mutated)


def test_workstream_h_rejects_raw_html_anchor_attribution():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    phrase = "local language, terminology, accent, and slang"
    assert phrase in roadmap
    mutated = roadmap.replace(
        phrase,
        f'<a href="https://example.com/unregistered">{phrase}</a>',
        1,
    )
    with pytest.raises(AssertionError, match="raw HTML anchors are not allowed"):
        _assert_workstream_h_integrity(mutated)


def _trans_tasman_raw(text: str) -> str:
    start, _ = _rendered_heading_span(text, TRANS_TASMAN_METHODOLOGY_HEADING)
    end, _ = _rendered_heading_span(text, POLICING_METHODOLOGY_HEADING)
    assert start < end, "rendered Trans-Tasman methodology boundary is invalid"
    return text[start:end]


def _trans_tasman_methodology(text: str) -> str:
    return _visible_markdown_text(_trans_tasman_raw(text))


def _normalised_trans_tasman_visible_value(text: str) -> str:
    return " ".join(_trans_tasman_methodology(text).split())


def _assert_trans_tasman_integrity(text: str) -> str:
    raw_section = _trans_tasman_raw(text)
    rendered_links = _rendered_inline_citation_links(
        raw_section, reject_titles=False
    )
    assert not rendered_links, (
        "Trans-Tasman methodology citation links are not allowed; "
        f"got {sorted(set(rendered_links))!r}"
    )
    section = _visible_markdown_text(raw_section)
    value = " ".join(section.split())
    actual_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
    assert actual_hash == TRANS_TASMAN_VISIBLE_SHA256, (
        "browser-visible Trans-Tasman methodology changed: expected hash "
        f"{TRANS_TASMAN_VISIBLE_SHA256!r}, got {actual_hash!r}"
    )
    namespace = runpy.run_path(str(POLICING_TEST))
    structural = namespace["_rendered_structure"](raw_section)
    source_lines = raw_section.splitlines()
    structural_lines = structural.splitlines()
    assert len(source_lines) == len(structural_lines)
    source_structure_value = "\n".join(
        original.rstrip()
        for original, live in zip(source_lines, structural_lines)
        if live.strip()
    )
    actual_structure_hash = hashlib.sha256(
        source_structure_value.encode("utf-8")
    ).hexdigest()
    assert actual_structure_hash == TRANS_TASMAN_SOURCE_STRUCTURE_SHA256, (
        "Trans-Tasman methodology record hierarchy changed: expected source-structure hash "
        f"{TRANS_TASMAN_SOURCE_STRUCTURE_SHA256!r}, got {actual_structure_hash!r}"
    )
    return section


def test_trans_tasman_methodology_rejects_companion_identity_reversal():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    _assert_trans_tasman_integrity(methodology)
    reversal = "Nationality and first-language identity should define the comparison cohorts."
    mutated = methodology.replace(
        POLICING_METHODOLOGY_HEADING,
        reversal + "\n\n" + POLICING_METHODOLOGY_HEADING,
        1,
    )
    with pytest.raises(AssertionError, match="browser-visible Trans-Tasman methodology changed"):
        _assert_trans_tasman_integrity(mutated)


def test_workstream_h_decouples_dialect_exposure_from_listener_identity():
    section = _assert_workstream_h_integrity(ROADMAP.read_text(encoding="utf-8"))
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
        f'<span style="opacity:0">{listener_clause}</span>',
        f'[placeholder](# "{listener_clause}")',
        f'[placeholder](#\n"{listener_clause}")',
    ):
        mutated = roadmap.replace(listener_clause, hidden, 1)
        if "style=" in hidden:
            with pytest.raises(AssertionError, match="inline style HTML"):
                _workstream_h(mutated)
        else:
            assert listener_clause not in _workstream_h(mutated)

    methodology = METHODOLOGY.read_text(encoding="utf-8")
    stereotype_clause = "exact group-stereotyping wording must not be reproduced"
    assert stereotype_clause in _trans_tasman_methodology(methodology)
    for hidden in (
        f"<!-- {stereotype_clause} -->",
        f"<span hidden>{stereotype_clause}</span>",
        f'<span style="opacity:0">{stereotype_clause}</span>',
        f'[placeholder](# "{stereotype_clause}")',
        f'[placeholder [nested]](# "{stereotype_clause}")',
    ):
        mutated = methodology.replace(stereotype_clause, hidden, 1)
        if "style=" in hidden:
            with pytest.raises(AssertionError, match="inline style HTML"):
                _trans_tasman_methodology(mutated)
        else:
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
    with pytest.raises(AssertionError, match="raw SVG HTML"):
        _workstream_h(mutated_roadmap)

    methodology = METHODOLOGY.read_text(encoding="utf-8")
    stereotype_clause = "exact group-stereotyping wording must not be reproduced"
    mutated_methodology = methodology.replace(
        stereotype_clause,
        f"<svg><title>{stereotype_clause}</title></svg>",
        1,
    )
    with pytest.raises(AssertionError, match="raw SVG HTML"):
        _trans_tasman_methodology(mutated_methodology)


def test_workstream_h_visibility_ignores_reference_definition_titles():
    clause = "nationality and first-language identity must not define the comparison cohorts"
    for hidden in (
        f'[hidden]: # "{clause}"',
        f'> [hidden]: # "{clause}"',
        f'- > [hidden]: # "{clause}"',
    ):
        assert clause not in _visible_markdown_text(hidden)


def test_workstream_h_companion_identity_contradiction_changes_section_seal():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_H_HEADING)
    end = roadmap.index(WORKSTREAM_I_HEADING, start)
    insertion = "\n- Nationality and first-language identity should define the comparison cohorts.\n"
    mutated = roadmap[:end] + insertion + roadmap[end:]
    with pytest.raises(AssertionError, match="browser-visible Workstream H changed"):
        _assert_workstream_h_integrity(mutated)


def test_aria_hidden_is_rejected_on_workstream_h_governed_surface():
    clause = "nationality and first-language identity must not define the comparison cohorts"
    with pytest.raises(AssertionError, match="aria-hidden accessibility suppression HTML"):
        _visible_markdown_text(f'<span aria-hidden="true">{clause}</span>')


def test_workstream_h_citation_destinations_are_pinned():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    _assert_workstream_h_integrity(roadmap)
    expected = "https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary"
    mutated = roadmap.replace(expected, "https://www.wikipedia.org/", 1)
    with pytest.raises(AssertionError, match="Workstream H citation destinations changed"):
        _assert_workstream_h_integrity(mutated)

def test_fresh_review_workstream_h_binds_citation_labels_to_destinations():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    vu_url = "https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary"
    reddit_url = "https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/"
    vu_link = f"[Australian slang dictionary]({vu_url})"
    reddit_link = f"[Best Aussie slang]({reddit_url})"
    assert vu_link in roadmap
    assert reddit_link in roadmap
    mutated = roadmap.replace(
        vu_link,
        f"[Australian slang dictionary]({reddit_url})",
        1,
    ).replace(
        reddit_link,
        f"[Best Aussie slang]({vu_url})",
        1,
    )
    with pytest.raises(AssertionError, match="citation label/destination bindings changed"):
        _assert_workstream_h_integrity(mutated)



def test_trans_tasman_methodology_rejects_unregistered_link_binding():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    _assert_trans_tasman_integrity(methodology)
    raw_section = _trans_tasman_raw(methodology)
    assert "relational licence" in raw_section
    mutated_section = raw_section.replace(
        "relational licence",
        "[relational licence](https://example.com/unregistered)",
        1,
    )
    mutated = methodology.replace(raw_section, mutated_section, 1)
    with pytest.raises(
        AssertionError, match="Trans-Tasman methodology citation links are not allowed"
    ):
        _assert_trans_tasman_integrity(mutated)
