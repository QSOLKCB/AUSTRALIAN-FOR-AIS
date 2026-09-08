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
