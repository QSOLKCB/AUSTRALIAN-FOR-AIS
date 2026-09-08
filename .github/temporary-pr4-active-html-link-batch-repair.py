from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement target, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


phase2 = ROOT / "tests" / "test_phase2_review_followup.py"
replace_once(
    phase2,
    '''def _phase2_namespace(changelog: str) -> dict:\n    """Reject document-wide stylesheet effects before rendered Phase 2 slicing."""\n    namespace = runpy.run_path(str(POLICING_TEST))\n    violations = namespace["_governed_surface_html_violations"](changelog)\n    namespace["_assert_supported_governed_html"](violations & {"stylesheet"})\n    return namespace\n''',
    '''def _phase2_namespace(changelog: str) -> dict:\n    """Reject document-wide active/rendering HTML before rendered Phase 2 slicing."""\n    namespace = runpy.run_path(str(POLICING_TEST))\n    violations = namespace["_governed_surface_html_violations"](changelog)\n    # Raw h1-h3 elements are intentionally supported as peer heading boundaries\n    # by the Notes slicer. Reject every other active/rendering violation on the\n    # original changelog before any structural masking can erase its effect.\n    namespace["_assert_supported_governed_html"](violations - {"semantic-heading"})\n    return namespace\n''',
)
replace_once(
    phase2,
    '''def test_phase2_receipts_reject_document_wide_styles_before_slicing():\n    changelog = CHANGELOG.read_text(encoding="utf-8")\n    mutated = "<style>body { display:none }</style>\\n\\n" + changelog\n    for receipt in (\n        _visible_phase2_notes,\n        _phase2_section_sha256,\n        _phase2_records_sha256,\n    ):\n        with pytest.raises(AssertionError):\n            receipt(mutated)\n''',
    '''@pytest.mark.parametrize(\n    "prefix",\n    (\n        "<style>body { display:none }</style>",\n        "<script>document.body.replaceChildren()</script>",\n    ),\n)\ndef test_phase2_receipts_reject_document_wide_active_html_before_slicing(prefix: str):\n    changelog = CHANGELOG.read_text(encoding="utf-8")\n    mutated = prefix + "\\n\\n" + changelog\n    for receipt in (\n        _visible_phase2_notes,\n        _phase2_section_sha256,\n        _phase2_records_sha256,\n    ):\n        with pytest.raises(AssertionError):\n            receipt(mutated)\n''',
)

policing = ROOT / "tests" / "test_policing_contract_receipt.py"
replace_once(
    policing,
    '''import hashlib\nfrom pathlib import Path\nimport runpy\n''',
    '''import hashlib\nfrom pathlib import Path\nimport re\nimport runpy\n''',
)
replace_once(
    policing,
    '''def _normalised_visible_policing_methodology(methodology: str) -> str:\n    return " ".join(_visible_policing_methodology(methodology).split())\n\n\ndef _assert_canonical_policing_integrity(methodology: str) -> None:\n    value = _normalised_visible_policing_methodology(methodology)\n''',
    '''def _normalised_visible_policing_methodology(methodology: str) -> str:\n    return " ".join(_visible_policing_methodology(methodology).split())\n\n\ndef _assert_policing_methodology_link_free(methodology: str) -> None:\n    """Keep the canonical policing methodology link-free until links are governed."""\n    namespace = runpy.run_path(str(POLICING_TEST))\n    section = _policing_methodology_section(methodology)\n    structure = namespace["_rendered_structure"](section)\n    assert not tuple(namespace["_iter_inline_markdown_destinations"](structure)), (\n        "unexpected Markdown hyperlink in canonical policing methodology"\n    )\n    assert namespace["AUTOLINK_PATTERN"].search(structure) is None, (\n        "unexpected autolink in canonical policing methodology"\n    )\n    assert re.search(r"<\\s*a\\b", structure, flags=re.IGNORECASE) is None, (\n        "unexpected raw HTML hyperlink in canonical policing methodology"\n    )\n    assert re.search(\n        r"(?<!!)\\[[^\\]\\r\\n]+\\]\\s*\\[[^\\]\\r\\n]*\\]",\n        structure,\n    ) is None, "unexpected reference-style hyperlink in canonical policing methodology"\n\n\ndef _assert_canonical_policing_integrity(methodology: str) -> None:\n    _assert_policing_methodology_link_free(methodology)\n    value = _normalised_visible_policing_methodology(methodology)\n''',
)
replace_once(
    policing,
    '''def test_canonical_policing_methodology_rejects_companion_high_stakes_reversal():\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    section = _policing_methodology_section(methodology)\n    mutated_section = (\n        section.rstrip()\n        + "\\n\\nExpert review may be skipped even for coercion and legal-rights families.\\n\\n"\n    )\n    mutated = methodology.replace(section, mutated_section, 1)\n    with pytest.raises(AssertionError, match="browser-visible canonical policing methodology changed"):\n        _assert_canonical_high_stakes_gate(mutated)\n''',
    '''def test_canonical_policing_methodology_rejects_companion_high_stakes_reversal():\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    section = _policing_methodology_section(methodology)\n    mutated_section = (\n        section.rstrip()\n        + "\\n\\nExpert review may be skipped even for coercion and legal-rights families.\\n\\n"\n    )\n    mutated = methodology.replace(section, mutated_section, 1)\n    with pytest.raises(AssertionError, match="browser-visible canonical policing methodology changed"):\n        _assert_canonical_high_stakes_gate(mutated)\n\n\n@pytest.mark.parametrize(\n    "phrase",\n    (\n        "Legal and procedural review is mandatory for high-stakes use.",\n        "Current official legislation",\n    ),\n)\ndef test_canonical_policing_methodology_rejects_unregistered_links(phrase: str):\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    section = _policing_methodology_section(methodology)\n    assert phrase in section\n    mutated = methodology.replace(\n        phrase,\n        f"[{phrase}](https://example.com/unregistered)",\n        1,\n    )\n    with pytest.raises(AssertionError, match="unexpected Markdown hyperlink"):\n        _assert_canonical_policing_integrity(mutated)\n''',
)

registry = ROOT / "tests" / "test_research_reference_registry.py"
replace_once(
    registry,
    '''def _normalised_registry_trailing_value(corpus: str) -> str:\n    """Return browser-visible registry content from the post-batch boundary to EOF."""\n    rendered, structure = _markdown_views(corpus)\n    start, _ = _visible_markdown_heading_span(structure, BATCH_END)\n    return _visible_inline_text(rendered[start:])\n''',
    '''def _registry_batch_prefix_source(corpus: str) -> str:\n    """Return source between the governed batch heading and its first entry."""\n    _, structure = _markdown_views(corpus)\n    _, start = _visible_markdown_heading_span(structure, BATCH_HEADING)\n    first_entry_start, _ = _visible_markdown_heading_span(\n        structure, EXPECTED_GOVERNED_ENTRIES[0]\n    )\n    assert start <= first_entry_start, "rendered governed batch prefix boundaries are out of order"\n    return corpus[start:first_entry_start]\n\n\ndef _normalised_registry_trailing_value(corpus: str) -> str:\n    """Return browser-visible registry content from the post-batch boundary to EOF."""\n    rendered, structure = _markdown_views(corpus)\n    start, _ = _visible_markdown_heading_span(structure, BATCH_END)\n    return _visible_inline_text(rendered[start:])\n''',
)
replace_once(
    registry,
    '''    sections = _registered_sections(corpus)\n    assert set(sections) == set(ENTRY_CONTRACTS), (\n        "every rendered governed entry must have an explicit pinned source contract"\n    )\n''',
    '''    batch_prefix = _registry_batch_prefix_source(corpus)\n    assert not batch_prefix.strip(), (\n        "governed registry batch prefix must remain empty before the first registered entry; "\n        f"got {batch_prefix.strip()!r}"\n    )\n\n    sections = _registered_sections(corpus)\n    assert set(sections) == set(ENTRY_CONTRACTS), (\n        "every rendered governed entry must have an explicit pinned source contract"\n    )\n''',
)
replace_once(
    registry,
    '''def test_trailing_registry_visible_corpus_is_pinned():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    _validate_registry_corpus(corpus)\n    mutated = (\n        corpus.rstrip()\n        + "\\n\\nAll registered sources may be copied freely into benchmark data.\\n"\n    )\n    with pytest.raises(AssertionError, match="browser-visible trailing registry content changed"):\n        _validate_registry_corpus(mutated)\n''',
    '''def test_governed_registry_batch_prefix_must_remain_empty():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    mutated = corpus.replace(\n        BATCH_HEADING,\n        BATCH_HEADING\n        + "\\n\\nAll registered sources may be copied freely into benchmark data.",\n        1,\n    )\n    assert mutated != corpus\n    with pytest.raises(AssertionError, match="governed registry batch prefix must remain empty"):\n        _validate_registry_corpus(mutated)\n\n\ndef test_trailing_registry_visible_corpus_is_pinned():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    _validate_registry_corpus(corpus)\n    mutated = (\n        corpus.rstrip()\n        + "\\n\\nAll registered sources may be copied freely into benchmark data.\\n"\n    )\n    with pytest.raises(AssertionError, match="browser-visible trailing registry content changed"):\n        _validate_registry_corpus(mutated)\n''',
)

print("patched Phase 2 active-HTML preflight, policing-methodology link contract, and registry batch prefix")
