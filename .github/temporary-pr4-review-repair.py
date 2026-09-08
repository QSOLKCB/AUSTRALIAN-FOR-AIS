from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match in {path}: {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


registry = Path("tests/test_research_reference_registry.py")
replace_once(
    registry,
    '''        if tag == "a" and not hidden and not inert:\n            for key, value in attrs:\n                if key.lower() == "href" and value:\n                    self.open_anchors.append((len(self.stack), value, len(self.parts)))\n                    break\n''',
    '''        if tag == "a" and not hidden and not inert:\n            for key, value in attrs:\n                if key.lower() == "href":\n                    # Presence is semantic even when the parsed value is empty:\n                    # href="" / bare href still creates a current-document link.\n                    self.open_anchors.append(\n                        (len(self.stack), "" if value is None else value, len(self.parts))\n                    )\n                    break\n''',
)
registry_text = registry.read_text(encoding="utf-8")
registry_test = '''\n\ndef test_source_use_rules_reject_empty_raw_html_href():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    phrase = "Record provenance and licence"\n    assert phrase in corpus\n    mutated = corpus.replace(\n        phrase,\n        f'<a href="" download>{phrase}</a>',\n        1,\n    )\n    assert _normalised_source_use_rules_value(mutated) == _normalised_source_use_rules_value(corpus)\n    assert _source_use_rules_record_receipt(mutated) == _source_use_rules_record_receipt(corpus)\n    with pytest.raises(AssertionError, match="no usable HTTPS destination"):\n        _source_use_rules_link_bindings(mutated)\n    with pytest.raises(AssertionError):\n        _validate_registry_corpus(mutated)\n'''
if "def test_source_use_rules_reject_empty_raw_html_href():" not in registry_text:
    registry.write_text(
        registry_text.rstrip() + registry_test.rstrip() + "\n",
        encoding="utf-8",
    )


ascft = Path("tests/test_ascft_methodology_integrity.py")
replace_once(
    ascft,
    '''def _assert_ascft_integrity(text: str) -> str:\n    _assert_ascft_has_no_links(text)\n''',
    '''def _assert_ascft_boundary_markup(text: str) -> None:\n    """Require the canonical full-boundary emphasis, not only visible words."""\n    namespace = _namespace()\n    raw_section = _raw_ascft_section(text)\n    structure = namespace["_mask_hidden_html_regions"](\n        namespace["_rendered_structure"](raw_section)\n    )\n    lines = [line.strip() for line in structure.splitlines()]\n    for boundary in MANDATORY_EPISTEMIC_BOUNDARIES:\n        marker = f"- **{boundary}**"\n        count = sum(line == marker for line in lines)\n        assert count == 1, (\n            "mandatory ASCFT epistemic boundary must retain canonical full-boundary "\n            f"emphasis: {boundary}; found {count} canonical records"\n        )\n\n\ndef _assert_ascft_integrity(text: str) -> str:\n    _assert_ascft_has_no_links(text)\n''',
)
replace_once(
    ascft,
    '''    assert actual_records_hash == ASCFT_RECORDS_SHA256, (\n        "ASCFT methodology record hierarchy changed: "\n        f"expected {ASCFT_RECORDS_SHA256!r}, got {actual_records_hash!r}"\n    )\n    for boundary in MANDATORY_EPISTEMIC_BOUNDARIES:\n''',
    '''    assert actual_records_hash == ASCFT_RECORDS_SHA256, (\n        "ASCFT methodology record hierarchy changed: "\n        f"expected {ASCFT_RECORDS_SHA256!r}, got {actual_records_hash!r}"\n    )\n    # Preserve established prose/hierarchy diagnostics for deletions/reversals;\n    # emphasis-only mutations reach this structural inline-markup gate.\n    _assert_ascft_boundary_markup(text)\n    for boundary in MANDATORY_EPISTEMIC_BOUNDARIES:\n''',
)
ascft_text = ascft.read_text(encoding="utf-8")
ascft_test = '''\n\n@pytest.mark.parametrize("boundary", MANDATORY_EPISTEMIC_BOUNDARIES)\ndef test_ascft_mandatory_boundaries_preserve_canonical_emphasis(boundary: str):\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    marker = f"- **{boundary}**"\n    assert marker in methodology\n    left, right = boundary.split(" != ", 1)\n    shifted = methodology.replace(\n        marker,\n        f"- {left} != **{right}**",\n        1,\n    )\n    assert _normalised_ascft_visible_value(shifted) == _normalised_ascft_visible_value(methodology)\n    assert _ascft_record_receipt(shifted) == _ascft_record_receipt(methodology)\n    with pytest.raises(AssertionError, match="canonical full-boundary emphasis"):\n        _assert_ascft_integrity(shifted)\n'''
if "def test_ascft_mandatory_boundaries_preserve_canonical_emphasis" not in ascft_text:
    ascft.write_text(
        ascft_text.rstrip() + ascft_test.rstrip() + "\n",
        encoding="utf-8",
    )


phase2 = Path("tests/test_phase2_review_followup.py")
phase2_text = phase2.read_text(encoding="utf-8")
helper_anchor = '''def _visible_phase2_notes(changelog: str) -> str:\n    namespace = runpy.run_path(str(POLICING_TEST))\n'''
helper_replacement = '''def _phase2_namespace(changelog: str) -> dict:\n    """Preflight the original changelog before any rendered slicing/masking."""\n    namespace = runpy.run_path(str(POLICING_TEST))\n    namespace["_assert_supported_governed_html"](\n        namespace["_governed_surface_html_violations"](changelog)\n    )\n    return namespace\n\n\ndef _visible_phase2_notes(changelog: str) -> str:\n    namespace = _phase2_namespace(changelog)\n'''
if helper_anchor not in phase2_text:
    raise RuntimeError("Phase 2 visible-notes anchor not found")
phase2_text = phase2_text.replace(helper_anchor, helper_replacement, 1)
raw_anchor = '''def _raw_phase2_section(changelog: str) -> str:\n    """Return the source slice for the complete rendered Phase 2 section."""\n    namespace = runpy.run_path(str(POLICING_TEST))\n'''
raw_replacement = '''def _raw_phase2_section(changelog: str) -> str:\n    """Return the source slice for the complete rendered Phase 2 section."""\n    namespace = _phase2_namespace(changelog)\n'''
if raw_anchor not in phase2_text:
    raise RuntimeError("Phase 2 raw-section anchor not found")
phase2_text = phase2_text.replace(raw_anchor, raw_replacement, 1)
phase2_test = '''\n\ndef test_phase2_receipts_reject_document_wide_styles_before_slicing():\n    changelog = CHANGELOG.read_text(encoding="utf-8")\n    mutated = "<style>body { display:none }</style>\\n\\n" + changelog\n    for receipt in (\n        _visible_phase2_notes,\n        _phase2_section_sha256,\n        _phase2_records_sha256,\n    ):\n        with pytest.raises(AssertionError):\n            receipt(mutated)\n'''
if "def test_phase2_receipts_reject_document_wide_styles_before_slicing" not in phase2_text:
    phase2_text = phase2_text.rstrip() + phase2_test.rstrip() + "\n"
phase2.write_text(phase2_text, encoding="utf-8")
