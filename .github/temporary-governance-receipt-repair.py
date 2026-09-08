from pathlib import Path
import hashlib
import re
import runpy


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one occurrence, found {count}"
    return text.replace(old, new, 1)


# 1. ASCFT: no canonical links exist in this governed section, so reject
# live hyperlink surfaces rather than inventing a new approved-link contract.
ascft_path = Path("tests/test_ascft_methodology_integrity.py")
ascft = ascft_path.read_text(encoding="utf-8")
ascft = replace_once(ascft, "import runpy\n", "import runpy\nimport re\n", "ASCFT import")
ascft_helper = r'''
def _assert_ascft_has_no_links(text: str) -> None:
    """Reject live hyperlinks because ASCFT has no approved link contract."""
    namespace = _namespace()
    raw_section = _raw_ascft_section(text)
    rendered = namespace["_mask_hidden_html_regions"](
        namespace["_rendered_structure"](raw_section)
    )
    assert not tuple(namespace["_iter_inline_markdown_destinations"](rendered)), (
        "unexpected Markdown hyperlink in governed ASCFT methodology"
    )
    assert namespace["AUTOLINK_PATTERN"].search(rendered) is None, (
        "unexpected URI autolink in governed ASCFT methodology"
    )
    assert namespace["EMAIL_AUTOLINK_PATTERN"].search(rendered) is None, (
        "unexpected email autolink in governed ASCFT methodology"
    )
    assert re.search(
        r"<\s*a\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*\bhref\s*=",
        rendered,
        flags=re.IGNORECASE,
    ) is None, "unexpected raw HTML hyperlink in governed ASCFT methodology"
    assert re.search(
        r"(?<!!)\[[^\]\r\n]+\]\s*\[[^\]\r\n]*\]",
        rendered,
    ) is None, "unexpected reference-style hyperlink in governed ASCFT methodology"

'''
ascft = replace_once(
    ascft,
    "\ndef _assert_ascft_integrity(text: str) -> str:\n",
    "\n" + ascft_helper + "def _assert_ascft_integrity(text: str) -> str:\n",
    "ASCFT helper insertion",
)
ascft = replace_once(
    ascft,
    "def _assert_ascft_integrity(text: str) -> str:\n    value = _normalised_ascft_visible_value(text)\n",
    "def _assert_ascft_integrity(text: str) -> str:\n    _assert_ascft_has_no_links(text)\n    value = _normalised_ascft_visible_value(text)\n",
    "ASCFT assertion call",
)
ascft_test = r'''

def test_ascft_methodology_rejects_unregistered_hyperlinks():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    phrase = "The epistemic boundary is mandatory:"
    assert phrase in methodology
    mutated = methodology.replace(
        phrase,
        f"[{phrase}](https://example.com/unregistered)",
        1,
    )
    assert _normalised_ascft_visible_value(mutated) == _normalised_ascft_visible_value(methodology)
    assert _ascft_record_receipt(mutated) == _ascft_record_receipt(methodology)
    with pytest.raises(AssertionError, match="unexpected Markdown hyperlink"):
        _assert_ascft_integrity(mutated)
'''
ascft = ascft.rstrip() + ascft_test.rstrip() + "\n"
ascft_path.write_text(ascft, encoding="utf-8")


# 2 + 4. Registry source-use link closure and trailing structural receipt.
registry_path = Path("tests/test_research_reference_registry.py")
registry = registry_path.read_text(encoding="utf-8")
const_match = re.search(
    r'^(REGISTRY_TRAILING_LINK_BINDINGS_SHA256\s*=\s*["\'][0-9a-f]{64}["\'])$',
    registry,
    flags=re.MULTILINE,
)
assert const_match, "trailing link binding constant not found"
registry = (
    registry[: const_match.end()]
    + '\nREGISTRY_TRAILING_RECORDS_SHA256 = "__TRAILING_RECORDS_SHA256__"'
    + registry[const_match.end() :]
)

source_use_record_anchor = '''def _source_use_rules_record_receipt(corpus: str) -> str:
    """Seal browser-visible source-use rule records with their container hierarchy."""
    _, structure = _markdown_views(corpus)
    start, _ = _visible_markdown_heading_span(structure, SOURCE_USE_HEADING)
    end, _ = _visible_markdown_heading_span(structure, CONTRACT_HEADING)
    assert start < end, "rendered source-use/registration-contract boundaries are out of order"
    records = _SHARED_POLICING["_normalised_visible_workstream_records"](corpus[start:end])
    return "\\n".join(
        f"{signature}\\x1f{line}" for signature, line in records
    )
'''
assert source_use_record_anchor in registry, "source-use record helper anchor not found"
registry = registry.replace(
    source_use_record_anchor,
    source_use_record_anchor
    + '''

def _source_use_rules_link_bindings(corpus: str) -> tuple[tuple[str, str], ...]:
    """Return every live HTTPS link binding inside Source-use rules."""
    rendered, structure = _markdown_views(corpus)
    start, _ = _visible_markdown_heading_span(structure, SOURCE_USE_HEADING)
    end, _ = _visible_markdown_heading_span(structure, CONTRACT_HEADING)
    assert start < end, "rendered source-use/registration-contract boundaries are out of order"
    return tuple(
        _usable_https_source_bindings(
            rendered[start:end],
            reference_scope=corpus,
        )
    )
''',
    1,
)

trailing_value_anchor = '''def _normalised_registry_trailing_value(corpus: str) -> str:
    """Return browser-visible registry content from the post-batch boundary to EOF."""
    rendered, structure = _markdown_views(corpus)
    start, _ = _visible_markdown_heading_span(structure, BATCH_END)
    return _visible_inline_text(rendered[start:])
'''
assert trailing_value_anchor in registry, "trailing visible helper anchor not found"
registry = registry.replace(
    trailing_value_anchor,
    trailing_value_anchor
    + '''

def _registry_trailing_record_receipt(corpus: str) -> str:
    """Seal trailing browser-visible records with their CommonMark hierarchy."""
    _, structure = _markdown_views(corpus)
    start, _ = _visible_markdown_heading_span(structure, BATCH_END)
    records = _SHARED_POLICING["_normalised_visible_workstream_records"](corpus[start:])
    return "\\n".join(
        f"{signature}\\x1f{line}" for signature, line in records
    )
''',
    1,
)

source_use_validation_anchor = '''    assert actual_source_use_records_hash == SOURCE_USE_RECORDS_SHA256, (
        "source-use rule record hierarchy changed: "
        f"expected hash {SOURCE_USE_RECORDS_SHA256!r}, "
        f"got {actual_source_use_records_hash!r}"
    )
'''
assert source_use_validation_anchor in registry, "source-use validation anchor not found"
registry = registry.replace(
    source_use_validation_anchor,
    source_use_validation_anchor
    + '''    source_use_links = _source_use_rules_link_bindings(corpus)
    assert not source_use_links, (
        "source-use rules must not contain hyperlinks unless an explicit link contract is added; "
        f"got {source_use_links!r}"
    )
''',
    1,
)

trailing_validation_anchor = '''    assert actual_trailing_hash == REGISTRY_TRAILING_VISIBLE_SHA256, (
        "browser-visible trailing registry content changed outside the governed receipts: "
        f"expected hash {REGISTRY_TRAILING_VISIBLE_SHA256!r}, got {actual_trailing_hash!r}"
    )
'''
assert trailing_validation_anchor in registry, "trailing validation anchor not found"
registry = registry.replace(
    trailing_validation_anchor,
    trailing_validation_anchor
    + '''
    trailing_records = _registry_trailing_record_receipt(corpus)
    actual_trailing_records_hash = hashlib.sha256(
        trailing_records.encode("utf-8")
    ).hexdigest()
    assert actual_trailing_records_hash == REGISTRY_TRAILING_RECORDS_SHA256, (
        "trailing registry record hierarchy changed: "
        f"expected hash {REGISTRY_TRAILING_RECORDS_SHA256!r}, "
        f"got {actual_trailing_records_hash!r}"
    )
''',
    1,
)

source_use_test_anchor = '''def test_source_use_rules_preserve_list_hierarchy():
    corpus = CORPUS.read_text(encoding="utf-8")
    rule = (
        "3. Record provenance and licence for every benchmark example independently "
        "of the reference that motivated it."
    )
    assert rule in corpus
    mutated = corpus.replace(rule, f"  {rule}", 1)
    assert _normalised_source_use_rules_value(mutated) == _normalised_source_use_rules_value(corpus)
    with pytest.raises(AssertionError, match="source-use rule record hierarchy changed"):
        _validate_registry_corpus(mutated)
'''
assert source_use_test_anchor in registry, "source-use hierarchy test anchor not found"
registry = registry.replace(
    source_use_test_anchor,
    source_use_test_anchor
    + '''

def test_source_use_rules_reject_unregistered_links():
    corpus = CORPUS.read_text(encoding="utf-8")
    phrase = "Record provenance and licence"
    assert phrase in corpus
    mutated = corpus.replace(
        phrase,
        f"[{phrase}](https://example.com/unregistered)",
        1,
    )
    assert _normalised_source_use_rules_value(mutated) == _normalised_source_use_rules_value(corpus)
    assert _source_use_rules_record_receipt(mutated) == _source_use_rules_record_receipt(corpus)
    with pytest.raises(AssertionError, match="source-use rules must not contain hyperlinks"):
        _validate_registry_corpus(mutated)
''',
    1,
)

title_test_anchor = '''def test_trailing_registry_link_titles_are_rejected():
    corpus = CORPUS.read_text(encoding="utf-8")
    source = "- https://en.wikipedia.org/wiki/The_Chaser"
    titled = (
        '- [https://en.wikipedia.org/wiki/The_Chaser]'
        '(https://en.wikipedia.org/wiki/The_Chaser "All content is CC0")'
    )
    mutated = corpus.replace(source, titled, 1)
    assert mutated != corpus
    assert _normalised_registry_trailing_value(mutated) == _normalised_registry_trailing_value(corpus)
    assert _registry_trailing_link_binding_receipt(mutated) == _registry_trailing_link_binding_receipt(corpus)
    with pytest.raises(AssertionError, match="trailing registry Markdown link titles"):
        _validate_registry_corpus(mutated)
'''
assert title_test_anchor in registry, "trailing title test anchor not found"
registry = registry.replace(
    title_test_anchor,
    title_test_anchor
    + '''

def test_trailing_registry_preserves_record_hierarchy():
    corpus = CORPUS.read_text(encoding="utf-8")
    rule = "- do not treat availability on the web as permission to redistribute;"
    assert rule in corpus
    mutated = corpus.replace(rule, f"  {rule}", 1)
    assert _normalised_registry_trailing_value(mutated) == _normalised_registry_trailing_value(corpus)
    assert _registry_trailing_link_binding_receipt(mutated) == _registry_trailing_link_binding_receipt(corpus)
    with pytest.raises(AssertionError, match="trailing registry record hierarchy changed"):
        _validate_registry_corpus(mutated)
''',
    1,
)
registry_path.write_text(registry, encoding="utf-8")


# 3. Phase 2 complete section: preserve CommonMark container hierarchy.
phase2_path = Path("tests/test_phase2_review_followup.py")
phase2 = phase2_path.read_text(encoding="utf-8")
phase_const = re.search(
    r'^(EXPECTED_VISIBLE_PHASE2_SECTION_SHA256\s*=\s*["\'][0-9a-f]{64}["\'])$',
    phase2,
    flags=re.MULTILINE,
)
assert phase_const, "Phase 2 visible hash constant not found"
phase2 = (
    phase2[: phase_const.end()]
    + '\nEXPECTED_PHASE2_RECORDS_SHA256 = "__PHASE2_RECORDS_SHA256__"'
    + phase2[phase_const.end() :]
)

old_phase_helper = '''def _visible_phase2_section(changelog: str) -> str:
    """Return the complete browser-visible Phase 2 changelog section."""
    namespace = runpy.run_path(str(POLICING_TEST))
    structure = namespace["_rendered_structure"](changelog)
    phase2_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE2_HEADING
    )
    phase1_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE1_HEADING
    )
    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"
    return namespace["_visible_text"](changelog[phase2_start:phase1_start])
'''
assert old_phase_helper in phase2, "Phase 2 helper anchor not found"
new_phase_helper = '''def _raw_phase2_section(changelog: str) -> str:
    """Return the source slice for the complete rendered Phase 2 section."""
    namespace = runpy.run_path(str(POLICING_TEST))
    structure = namespace["_rendered_structure"](changelog)
    phase2_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE2_HEADING
    )
    phase1_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE1_HEADING
    )
    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"
    return changelog[phase2_start:phase1_start]


def _visible_phase2_section(changelog: str) -> str:
    """Return the complete browser-visible Phase 2 changelog section."""
    namespace = runpy.run_path(str(POLICING_TEST))
    return namespace["_visible_text"](_raw_phase2_section(changelog))


def _phase2_record_receipt(changelog: str) -> str:
    """Seal Phase 2 browser-visible records with their CommonMark hierarchy."""
    namespace = runpy.run_path(str(POLICING_TEST))
    records = namespace["_normalised_visible_workstream_records"](
        _raw_phase2_section(changelog)
    )
    return "\\n".join(
        f"{signature}\\x1f{line}" for signature, line in records
    )


def _phase2_records_sha256(changelog: str) -> str:
    return hashlib.sha256(_phase2_record_receipt(changelog).encode("utf-8")).hexdigest()
'''
phase2 = phase2.replace(old_phase_helper, new_phase_helper, 1)
phase_test_anchor = '''def test_complete_phase2_changelog_section_is_pinned():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert _phase2_section_sha256(changelog) == EXPECTED_VISIBLE_PHASE2_SECTION_SHA256
'''
assert phase_test_anchor in phase2, "Phase 2 complete section test anchor not found"
phase2 = phase2.replace(
    phase_test_anchor,
    phase_test_anchor
    + '''    assert _phase2_records_sha256(changelog) == EXPECTED_PHASE2_RECORDS_SHA256


def test_phase2_section_receipt_preserves_list_hierarchy():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    bullet = f"- {FREE_TEXT_IAA_BOUNDARY}\\n"
    assert bullet in changelog
    mutated = changelog.replace(bullet, f"  {bullet}", 1)
    assert _visible_phase2_notes(mutated) == EXPECTED_VISIBLE_PHASE2_NOTES
    assert _phase2_section_sha256(mutated) == EXPECTED_VISIBLE_PHASE2_SECTION_SHA256
    assert _phase2_records_sha256(mutated) != EXPECTED_PHASE2_RECORDS_SHA256
''',
    1,
)
phase2_path.write_text(phase2, encoding="utf-8")


# Compute immutable structural receipts against canonical source text.
phase_ns = runpy.run_path(str(phase2_path))
phase_changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
phase_hash = hashlib.sha256(
    phase_ns["_phase2_record_receipt"](phase_changelog).encode("utf-8")
).hexdigest()
phase2_path.write_text(
    phase2_path.read_text(encoding="utf-8").replace(
        "__PHASE2_RECORDS_SHA256__", phase_hash
    ),
    encoding="utf-8",
)

registry_ns = runpy.run_path(str(registry_path))
corpus = Path("docs/RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
trailing_hash = hashlib.sha256(
    registry_ns["_registry_trailing_record_receipt"](corpus).encode("utf-8")
).hexdigest()
registry_path.write_text(
    registry_path.read_text(encoding="utf-8").replace(
        "__TRAILING_RECORDS_SHA256__", trailing_hash
    ),
    encoding="utf-8",
)

for path in (ascft_path, registry_path, phase2_path):
    text = path.read_text(encoding="utf-8")
    assert "__PHASE2_RECORDS_SHA256__" not in text
    assert "__TRAILING_RECORDS_SHA256__" not in text
    compile(text, str(path), "exec")

print(f"Phase 2 structural receipt: {phase_hash}")
print(f"Trailing registry structural receipt: {trailing_hash}")
