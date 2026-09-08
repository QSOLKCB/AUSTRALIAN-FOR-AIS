from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one match, found {count}"
    return text.replace(old, new, 1)


policing_path = Path("tests/test_policing_context_roadmap.py")
policing = policing_path.read_text(encoding="utf-8")
policing = replace_once(
    policing,
    '        "raw-block": "raw block-container HTML",\n',
    '',
    "keep raw-block out of shared global rejection precedence",
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
    # (closed disclosures, duplicate metadata, type-6 structure, styling, etc.)
    # retain precedence. A raw block that otherwise flattens back to canonical
    # scalar prose still fails before the complete-entry hash is accepted.
    raw_block_html = _SHARED_HTML_PREFLIGHT(section) & {"raw-block"}
    assert not raw_block_html, (
        f"{entry} contains raw block-container HTML; governed scalar prose must not "
        "be structurally detached or reframed by browser block elements"
    )
    value = _normalise_complete_entry_integrity(section)
''',
    "add late entry-level raw-block rejection",
)
registry_path.write_text(registry, encoding="utf-8")
