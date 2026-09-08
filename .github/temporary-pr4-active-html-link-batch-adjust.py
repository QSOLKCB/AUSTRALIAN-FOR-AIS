from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests" / "test_research_reference_registry.py"
text = path.read_text(encoding="utf-8")

old_helper = '''def _registry_batch_prefix_source(corpus: str) -> str:\n    """Return source between the governed batch heading and its first entry."""\n    _, structure = _markdown_views(corpus)\n    _, start = _visible_markdown_heading_span(structure, BATCH_HEADING)\n    first_entry_start, _ = _visible_markdown_heading_span(\n        structure, EXPECTED_GOVERNED_ENTRIES[0]\n    )\n    assert start <= first_entry_start, "rendered governed batch prefix boundaries are out of order"\n    return corpus[start:first_entry_start]\n'''
new_helper = '''def _normalised_registry_batch_prefix_value(corpus: str) -> str:\n    """Return unowned reader-visible content before the first governed entry."""\n    rendered, structure = _markdown_views(corpus)\n    _, start = _visible_markdown_heading_span(structure, BATCH_HEADING)\n    first_entry_start, _ = _visible_markdown_heading_span(\n        structure, EXPECTED_GOVERNED_ENTRIES[0]\n    )\n    assert start <= first_entry_start, "rendered governed batch prefix boundaries are out of order"\n    prefix = rendered[start:first_entry_start]\n    # Preserve the established positive control that allows the governed batch\n    # to be wrapped in an open disclosure labelled exactly "Governed references".\n    # The wrapper label is presentation, not unowned source/governance prose.\n    prefix = re.sub(\n        r"<summary(?:\\s[^>]*)?>\\s*Governed references\\s*</summary>",\n        "",\n        prefix,\n        flags=re.IGNORECASE | re.DOTALL,\n    )\n    return _visible_inline_text(prefix)\n'''
if text.count(old_helper) != 1:
    raise SystemExit("expected exactly one patched registry batch-prefix helper")
text = text.replace(old_helper, new_helper, 1)

old_validation = '''    batch_prefix = _registry_batch_prefix_source(corpus)\n    assert not batch_prefix.strip(), (\n        "governed registry batch prefix must remain empty before the first registered entry; "\n        f"got {batch_prefix.strip()!r}"\n    )\n\n    sections = _registered_sections(corpus)\n    assert set(sections) == set(ENTRY_CONTRACTS), (\n        "every rendered governed entry must have an explicit pinned source contract"\n    )\n'''
new_validation = '''    sections = _registered_sections(corpus)\n    assert set(sections) == set(ENTRY_CONTRACTS), (\n        "every rendered governed entry must have an explicit pinned source contract"\n    )\n\n    batch_prefix = _normalised_registry_batch_prefix_value(corpus)\n    assert not batch_prefix, (\n        "governed registry batch prefix must remain empty before the first registered entry; "\n        f"got {batch_prefix!r}"\n    )\n'''
if text.count(old_validation) != 1:
    raise SystemExit("expected exactly one patched registry batch-prefix validation block")
text = text.replace(old_validation, new_validation, 1)
path.write_text(text, encoding="utf-8")
print("adjusted registry batch-prefix guard for established wrapper/diagnostic compatibility")
