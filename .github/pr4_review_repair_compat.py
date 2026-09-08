from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one match, found {count}"
    return text.replace(old, new, 1)


policing_path = Path("tests/test_policing_context_roadmap.py")
policing = policing_path.read_text(encoding="utf-8")
policing = replace_once(
    policing,
    '''        # Raw block-level containers can likewise terminate or reframe the
        # surrounding paragraph while a text-only receipt reconstructs the
        # canonical characters. Do not approximate those layout semantics on
        # governed prose.
        if tag in {
            "address", "article", "aside", "div", "dl", "fieldset",
            "figcaption", "figure", "footer", "header", "main", "nav",
            "p", "section", "summary",
        }:
            self.violations.add("raw-block")
''',
    '',
    "remove blanket raw-block parser classification",
)
policing = replace_once(
    policing,
    '        "raw-block": "raw block-container HTML",\n',
    '',
    "keep raw-block out of shared global rejection precedence",
)
policing = replace_once(
    policing,
    '''    live_markup = "".join(characters)

    # Markdown links become anchors only after Markdown rendering, so the raw-HTML
''',
    '''    live_markup = "".join(characters)

    # Block containers are dangerous specifically when they carry/reframe
    # governed prose on the same rendered source line. Do not classify a bare
    # flow-HTML opener/closer as a violation here: CommonMark can legitimately
    # terminate that block at a blank line and resume Markdown afterwards.
    raw_block_tag = re.compile(
        r"</?(?:address|article|aside|div|dl|fieldset|figcaption|figure|footer|header|main|nav|p|section|summary)\\b[^>]*>",
        flags=re.IGNORECASE,
    )
    for raw_line in live_markup.splitlines():
        if raw_block_tag.search(raw_line) is None:
            continue
        residual = raw_block_tag.sub("", raw_line)
        if residual.strip():
            parser.violations.add("raw-block")
            break

    # Markdown links become anchors only after Markdown rendering, so the raw-HTML
''',
    "classify prose-bearing raw block containers",
)
policing_path.write_text(policing, encoding="utf-8")

registry_path = Path("tests/test_research_reference_registry.py")
registry = registry_path.read_text(encoding="utf-8")
registry = replace_once(
    registry,
    '    "raw-block",\n',
    '',
    "keep raw-block out of corpus-wide active kinds",
)
registry = replace_once(
    registry,
    '''    assert "raw-block" not in found, (
        "raw block-container HTML is not allowed in governed documents because block "
        "elements can terminate or reframe sealed scalar prose"
    )
''',
    '',
    "remove corpus-wide raw-block precedence",
)
registry = replace_once(
    registry,
    '''def _assert_registry_document_prefix(corpus: str) -> None:
    """Require the registry prefix to contain only the canonical level-one title."""
    _, structure = _markdown_views(corpus)
    title_start, _ = _visible_markdown_heading_span(structure, REGISTRY_TITLE_HEADING)
    status_start, _ = _visible_markdown_heading_span(structure, STATUS_HEADING)
    assert title_start == 0, (
        "registry must begin with the canonical level-one title; "
        "reader-visible content before the title is not governed"
    )
    assert title_start < status_start, "rendered registry title/Status boundaries are out of order"
    expected_prefix = REGISTRY_TITLE_HEADING + "\\n\\n"
    actual_prefix = corpus[:status_start]
    assert actual_prefix == expected_prefix, (
        "registry content before Status must contain only the canonical title: "
        f"expected {expected_prefix!r}, got {actual_prefix!r}"
    )
''',
    '''def _assert_registry_document_prefix(corpus: str) -> None:
    """Require no reader-visible registry-wide prose outside the title before Status."""
    rendered, structure = _markdown_views(corpus)
    title_start, title_end = _visible_markdown_heading_span(structure, REGISTRY_TITLE_HEADING)
    status_start, _ = _visible_markdown_heading_span(structure, STATUS_HEADING)
    assert title_start < status_start, "rendered registry title/Status boundaries are out of order"
    before_title = _visible_inline_text(rendered[:title_start]).strip()
    between_title_and_status = _visible_inline_text(rendered[title_end:status_start]).strip()
    assert not before_title, (
        "reader-visible registry content before the canonical title is not governed: "
        f"{before_title!r}"
    )
    assert not between_title_and_status, (
        "reader-visible registry content between the canonical title and Status is not governed: "
        f"{between_title_and_status!r}"
    )
''',
    "make registry prefix seal visibility-aware",
)
registry = replace_once(
    registry,
    '''    assert GOVERNED_INTERACTIVE_HTML_PATTERN.search(rendered_section) is None, (
        f"{entry} contains interactive HTML that is not permitted in governed entries"
    )
    value = _normalise_complete_entry_integrity(section)
''',
    '''    assert GOVERNED_INTERACTIVE_HTML_PATTERN.search(rendered_section) is None, (
        f"{entry} contains interactive HTML that is not permitted in governed entries"
    )
    # Keep this late in entry validation so established, more-specific diagnostics
    # retain precedence. Prose-bearing raw block containers can otherwise alter
    # browser paragraph structure while flattening back to the same receipt text.
    raw_block_html = _SHARED_HTML_PREFLIGHT(section) & {"raw-block"}
    assert not raw_block_html, (
        f"{entry} contains raw block-container HTML around governed prose; scalar "
        "content must not be structurally detached or reframed by browser block elements"
    )
    value = _normalise_complete_entry_integrity(section)
''',
    "add late entry-level raw-block rejection",
)
registry_path.write_text(registry, encoding="utf-8")
