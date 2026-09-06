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
    '''GOVERNED_BIDI_HTML_PATTERN = re.compile(
    r"<bdo\\b|<[A-Za-z][^>]*\\bdir[ \\t]*=",
    flags=re.IGNORECASE,
)
RAW_HTML_TAG_TOKEN_PATTERN = re.compile(
''',
    '''GOVERNED_BIDI_HTML_PATTERN = re.compile(
    r"<bdo\\b|<[A-Za-z][^>]*\\bdir[ \\t]*=",
    flags=re.IGNORECASE,
)
GOVERNED_CONDITIONAL_RAW_TEXT_TAGS = frozenset({
    "noscript", "plaintext", "xmp", "listing", "noframes", "noembed",
})
RAW_HTML_TAG_TOKEN_PATTERN = re.compile(
''',
    "governed raw-text constants",
)

registry = replace_once(
    registry,
    '''def _first_html_attribute_values(
    attrs: list[tuple[str, str | None]],
) -> dict[str, str]:
    """Match browser parsing by preserving the first duplicate attribute value."""
    values: dict[str, str] = {}
    for key, value in attrs:
        values.setdefault(key.lower(), value or "")
    return values


def _css_hides_element(style: str) -> bool:
''',
    '''def _first_html_attribute_values(
    attrs: list[tuple[str, str | None]],
) -> dict[str, str]:
    """Match browser parsing by preserving the first duplicate attribute value."""
    values: dict[str, str] = {}
    for key, value in attrs:
        values.setdefault(key.lower(), value or "")
    return values


class _GovernedHTMLSemanticsDetector(HTMLParser):
    """Fail closed on browser semantics the integrity reducer does not model."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.found: set[str] = set()

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()
        names = [key.lower() for key, _ in attrs]
        if tag == "details" and "open" not in names:
            # A closed disclosure still renders its summary. The lightweight
            # hidden-region masker intentionally does not try to model that
            # split subtree, so closed disclosures are rejected in governed
            # entries instead of letting visible summary contradictions escape
            # the complete-entry seal.
            self.found.add("closed-details")
        if any(name.startswith("on") for name in names):
            self.found.add("event-handler")
        if tag in GOVERNED_CONDITIONAL_RAW_TEXT_TAGS:
            self.found.add("conditional-raw-text")

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)


def _css_hides_element(style: str) -> bool:
''',
    "governed HTML semantics detector",
)

registry = replace_once(
    registry,
    '''def _visible_html_text(text: str) -> str:
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    return " ".join(parser.parts)


def _visible_html_links(text: str) -> tuple[str, ...]:
''',
    '''def _visible_html_text(text: str) -> str:
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    # HTML inline elements do not manufacture whitespace between adjacent text
    # nodes. Preserve the source/browser adjacency here; the final visible-text
    # normalizer collapses whitespace that was actually rendered by the source.
    return "".join(parser.parts)


def _visible_html_links(text: str) -> tuple[str, ...]:
''',
    "inline HTML adjacency",
)

registry = replace_once(
    registry,
    '''def _visible_inline_text(text: str) -> str:
    """Reduce Markdown/HTML metadata to browser-visible text only."""
    rendered = _rendered_registry_text(text)
    visible = _mask_link_reference_definitions_for_visibility(rendered)
    visible = _render_inline_code_spans(visible)
    visible = _replace_inline_markdown_links_with_labels(visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    # HTMLParser(convert_charrefs=True) performs the browser's one character-
    # reference decoding pass. Do not decode the resulting text a second time.
    visible = _visible_html_text(visible)
    visible = _strip_emphasis_preserving_intraword_underscores(visible)
    return " ".join(visible.split())
''',
    '''ENTITY_LITERAL_ASTERISK = "\\uE001"
ENTITY_LITERAL_UNDERSCORE = "\\uE002"


def _protect_entity_decoded_emphasis_punctuation(text: str) -> str:
    """Protect entity-derived punctuation from the later Markdown delimiter pass."""
    assert ENTITY_LITERAL_ASTERISK not in text
    assert ENTITY_LITERAL_UNDERSCORE not in text

    def replace(match: re.Match[str]) -> str:
        decoded = html.unescape(match.group(0))
        if decoded == "*":
            return ENTITY_LITERAL_ASTERISK
        if decoded == "_":
            return ENTITY_LITERAL_UNDERSCORE
        return match.group(0)

    return COMMONMARK_CHARACTER_REFERENCE_PATTERN.sub(replace, text)


def _restore_entity_decoded_emphasis_punctuation(text: str) -> str:
    return text.replace(ENTITY_LITERAL_ASTERISK, "*").replace(
        ENTITY_LITERAL_UNDERSCORE,
        "_",
    )


def _visible_inline_text(text: str) -> str:
    """Reduce Markdown/HTML metadata to browser-visible text only."""
    rendered = _rendered_registry_text(text)
    visible = _mask_link_reference_definitions_for_visibility(rendered)
    visible = _render_inline_code_spans(visible)
    visible = _replace_inline_markdown_links_with_labels(visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    # CommonMark decides emphasis delimiters before character references become
    # literal rendered punctuation. Protect entity-derived '*'/'_' so they are
    # not later mistaken for source Markdown delimiters.
    visible = _protect_entity_decoded_emphasis_punctuation(visible)
    # HTMLParser(convert_charrefs=True) performs the browser's one character-
    # reference decoding pass. Do not decode the resulting text a second time.
    visible = _visible_html_text(visible)
    visible = _strip_emphasis_preserving_intraword_underscores(visible)
    visible = _restore_entity_decoded_emphasis_punctuation(visible)
    return " ".join(visible.split())
''',
    "entity-derived literal punctuation",
)

registry = replace_once(
    registry,
    '''    found: set[str] = set()

    for raw_line in scan.splitlines():
''',
    '''    found: set[str] = set()
    live_markup_parts: list[str] = []

    for raw_line in scan.splitlines():
''',
    "collect live governed HTML",
)

registry = replace_once(
    registry,
    '''        logical = _mask_inline_code_spans(logical)
        if GOVERNED_STYLING_HTML_PATTERN.search(logical):
''',
    '''        logical = _mask_inline_code_spans(logical)
        live_markup_parts.append(logical)
        if GOVERNED_STYLING_HTML_PATTERN.search(logical):
''',
    "append live governed HTML",
)

registry = replace_once(
    registry,
    '''        if GOVERNED_BIDI_HTML_PATTERN.search(logical):
            found.add("bidi")
    return found
''',
    '''        if GOVERNED_BIDI_HTML_PATTERN.search(logical):
            found.add("bidi")

    semantics = _GovernedHTMLSemanticsDetector()
    try:
        semantics.feed("\\n".join(live_markup_parts))
        semantics.close()
    except Exception:
        # Malformed live HTML is already unsafe for a render-integrity contract.
        found.add("conditional-raw-text")
    found.update(semantics.found)
    return found
''',
    "fail-closed governed HTML semantics",
)

registry = replace_once(
    registry,
    '''    assert "bidi" not in forbidden_html, (
        f"{entry} contains bidirectional/direction-changing HTML; governed clauses must "
        "retain their canonical visual reading order"
    )
    assert not _contains_visually_hidden_table(structural_section), (
''',
    '''    assert "bidi" not in forbidden_html, (
        f"{entry} contains bidirectional/direction-changing HTML; governed clauses must "
        "retain their canonical visual reading order"
    )
    assert "closed-details" not in forbidden_html, (
        f"{entry} contains a closed details disclosure; governed entries reject closed "
        "disclosures because their summary remains browser-visible while the body is hidden"
    )
    assert "event-handler" not in forbidden_html, (
        f"{entry} contains an inline event-handler attribute; governed provenance anchors "
        "must not be able to cancel or rewrite navigation"
    )
    assert "conditional-raw-text" not in forbidden_html, (
        f"{entry} contains conditional/legacy raw-text HTML (noscript/plaintext/xmp/etc.); "
        "governed entries reject tokenizer- or scripting-dependent rendering"
    )
    assert not _contains_visually_hidden_table(structural_section), (
''',
    "complete-entry browser semantics assertions",
)

if "def test_latest_4fe_browser_semantics_regressions():" not in registry:
    registry = registry.rstrip() + '''\n\n\ndef test_latest_4fe_browser_semantics_regressions():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = "### *Black Comedy* (ABC, 2014-2020)"\n    section = _registered_sections(corpus)[entry]\n\n    # Closed details still renders summary text. Governed entries reject this\n    # split visibility surface rather than letting a visible contradiction fall\n    # outside the complete-entry integrity value.\n    disclosure = section.rstrip() + (\n        "\\n\\n<details><summary>This source may be freely copied.</summary></details>\\n"\n    )\n    with pytest.raises(AssertionError, match="closed details disclosure"):\n        _validate_registry_corpus(corpus.replace(section, disclosure, 1))\n\n    # A click-cancelling handler can make an otherwise correct href unusable.\n    source = "https://iview.abc.net.au/show/black-comedy"\n    event_anchor = f'<a href="{source}" onclick="return false">{source}</a>'\n    event_mutation = section.replace(source, event_anchor, 1)\n    with pytest.raises(AssertionError, match="event-handler"):\n        _validate_registry_corpus(corpus.replace(section, event_mutation, 1))\n\n    # Character references become literal punctuation after Markdown delimiter\n    # parsing, so they must not be erased as if they were source emphasis.\n    assert "Broadcaster programme record" in section\n    entity_mutation = section.replace(\n        "Broadcaster programme record",\n        "Broadcaster progr&#42;amme record",\n        1,\n    )\n    with pytest.raises(AssertionError, match="missing a pinned|changed pinned"):\n        _validate_registry_corpus(corpus.replace(section, entity_mutation, 1))\n\n    # Empty inline wrappers do not create a browser word boundary.\n    adjacency_mutation = section.replace(\n        "Broadcaster programme record",\n        "Broadcaster<span></span>programme record",\n        1,\n    )\n    with pytest.raises(AssertionError, match="missing a pinned|changed pinned"):\n        _validate_registry_corpus(corpus.replace(section, adjacency_mutation, 1))\n\n\n@pytest.mark.parametrize("tag", ("noscript", "xmp", "plaintext"))\ndef test_conditional_and_legacy_raw_text_cannot_supply_governed_clauses(tag: str):\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = "### *Black Comedy* (ABC, 2014-2020)"\n    section = _registered_sections(corpus)[entry]\n    expected = str(ENTRY_CONTRACTS[entry][SOURCE_TYPE_FIELD])\n    assert expected in section\n    mutated_section = section.replace(expected, f"<{tag}>{expected}</{tag}>", 1)\n    with pytest.raises(AssertionError, match="conditional/legacy raw-text HTML"):\n        _validate_registry_corpus(corpus.replace(section, mutated_section, 1))\n''' + "\n"

registry_path.write_text(registry, encoding="utf-8")


workstream_path = Path("tests/test_workstream_h_methodology.py")
workstream = workstream_path.read_text(encoding="utf-8")

workstream = replace_once(
    workstream,
    '''WORKSTREAM_H_VISIBLE_SHA256 = "c38e4bc194d820c30ee714851ec279da7649fffc921da5a331d722d22d7c34b8"
TRANS_TASMAN_VISIBLE_SHA256 = "977cb0423a8e0690383f68ef9915ce049ed6f977feeff4f4ab28d21449db1c9b"
''',
    '''WORKSTREAM_H_VISIBLE_SHA256 = "c38e4bc194d820c30ee714851ec279da7649fffc921da5a331d722d22d7c34b8"
WORKSTREAM_H_CITATION_DESTINATIONS = frozenset({
    "https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary",
    "https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/",
    "https://www.defence.gov.au/news-events/news/2022-09-08/communication-key-combined-exercise",
    "https://www.defence.gov.au/news-events/news/2026-06-11/partner-nations-rehearse-war",
    "https://www.awm.gov.au/collection/LIB100000077",
})
TRANS_TASMAN_VISIBLE_SHA256 = "977cb0423a8e0690383f68ef9915ce049ed6f977feeff4f4ab28d21449db1c9b"
''',
    "Workstream H citation contract",
)

workstream = replace_once(
    workstream,
    '''def _replace_inline_markdown_links_for_visibility(text: str) -> str:
''',
    '''def _inline_markdown_link_destinations(text: str) -> tuple[str, ...]:
    """Return non-image inline-link destinations from a rendered section source."""
    destinations: list[str] = []
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
            destinations.append(html.unescape(destination.strip("<>")))
        cursor = paren_end + 1
    return tuple(destinations)


def _replace_inline_markdown_links_for_visibility(text: str) -> str:
''',
    "Workstream H destination parser",
)

workstream = replace_once(
    workstream,
    '''def _workstream_h(text: str) -> str:
    start, _ = _rendered_heading_span(text, WORKSTREAM_H_HEADING)
    end, _ = _rendered_heading_span(text, WORKSTREAM_I_HEADING)
    assert start < end, "rendered Workstream H boundary is invalid"
    return _visible_markdown_text(text[start:end])
''',
    '''def _workstream_h_raw(text: str) -> str:
    start, _ = _rendered_heading_span(text, WORKSTREAM_H_HEADING)
    end, _ = _rendered_heading_span(text, WORKSTREAM_I_HEADING)
    assert start < end, "rendered Workstream H boundary is invalid"
    return text[start:end]


def _workstream_h(text: str) -> str:
    return _visible_markdown_text(_workstream_h_raw(text))
''',
    "Workstream H raw section helper",
)

workstream = replace_once(
    workstream,
    '''def _assert_workstream_h_integrity(text: str) -> str:
    section = _workstream_h(text)
    value = " ".join(section.split())
''',
    '''def _assert_workstream_h_integrity(text: str) -> str:
    raw_section = _workstream_h_raw(text)
    actual_destinations = set(_inline_markdown_link_destinations(raw_section))
    assert actual_destinations == WORKSTREAM_H_CITATION_DESTINATIONS, (
        "Workstream H citation destinations changed: expected "
        f"{sorted(WORKSTREAM_H_CITATION_DESTINATIONS)!r}, got "
        f"{sorted(actual_destinations)!r}"
    )
    section = _visible_markdown_text(raw_section)
    value = " ".join(section.split())
''',
    "Workstream H destination integrity",
)

if "def test_workstream_h_citation_destinations_are_pinned():" not in workstream:
    workstream = workstream.rstrip() + '''\n\n\ndef test_workstream_h_citation_destinations_are_pinned():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    _assert_workstream_h_integrity(roadmap)\n    expected = "https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary"\n    mutated = roadmap.replace(expected, "https://www.wikipedia.org/", 1)\n    with pytest.raises(AssertionError, match="Workstream H citation destinations changed"):\n        _assert_workstream_h_integrity(mutated)\n''' + "\n"

workstream_path.write_text(workstream, encoding="utf-8")
print("Applied seven-item 4fe review repair and regressions.")
