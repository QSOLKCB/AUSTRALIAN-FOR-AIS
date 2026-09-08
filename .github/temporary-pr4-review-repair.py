from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry_path = ROOT / "tests" / "test_research_reference_registry.py"
phase2_path = ROOT / "tests" / "test_phase2_review_followup.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


registry = registry_path.read_text(encoding="utf-8")
old_prefix_helper = '''def _normalised_registry_batch_prefix_value(corpus: str) -> str:
    """Return unowned reader-visible content before the first governed entry."""
    rendered, structure = _markdown_views(corpus)
    _, start = _visible_markdown_heading_span(structure, BATCH_HEADING)
    first_entry_start, _ = _visible_markdown_heading_span(
        structure, EXPECTED_GOVERNED_ENTRIES[0]
    )
    assert start <= first_entry_start, "rendered governed batch prefix boundaries are out of order"
    prefix = rendered[start:first_entry_start]
    # Preserve the established positive control that allows the governed batch
    # to be wrapped in an open disclosure labelled exactly "Governed references".
    # The wrapper label is presentation, not unowned source/governance prose.
    prefix = re.sub(
        r"<summary(?:\\s[^>]*)?>\\s*Governed references\\s*</summary>",
        "",
        prefix,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return _visible_inline_text(prefix)
'''
new_prefix_helper = '''def _registry_batch_prefix_bounds(corpus: str) -> tuple[int, int]:
    """Return source offsets for the gap between the batch heading and first entry."""
    _, structure = _markdown_views(corpus)
    _, start = _visible_markdown_heading_span(structure, BATCH_HEADING)
    first_entry_start, _ = _visible_markdown_heading_span(
        structure, EXPECTED_GOVERNED_ENTRIES[0]
    )
    assert start <= first_entry_start, "rendered governed batch prefix boundaries are out of order"
    return start, first_entry_start


def _registry_batch_prefix_source(corpus: str) -> str:
    """Return the raw source gap before the first governed registry entry."""
    start, end = _registry_batch_prefix_bounds(corpus)
    return corpus[start:end]


def _normalised_registry_batch_prefix_value(corpus: str) -> str:
    """Return unowned reader-visible content before the first governed entry."""
    rendered, _ = _markdown_views(corpus)
    start, first_entry_start = _registry_batch_prefix_bounds(corpus)
    prefix = rendered[start:first_entry_start]
    # Preserve the established positive control that allows the governed batch
    # to be wrapped in an open disclosure labelled exactly "Governed references".
    # The wrapper label is presentation, not unowned source/governance prose.
    prefix = re.sub(
        r"<summary(?:\\s[^>]*)?>\\s*Governed references\\s*</summary>",
        "",
        prefix,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return _visible_inline_text(prefix)
'''
registry = replace_once(registry, old_prefix_helper, new_prefix_helper, "registry prefix helper")

old_prefix_validation = '''    batch_prefix = _normalised_registry_batch_prefix_value(corpus)
    assert not batch_prefix, (
        "governed registry batch prefix must remain empty before the first registered entry; "
        f"got {batch_prefix!r}"
    )
'''
new_prefix_validation = '''    batch_prefix_source = _registry_batch_prefix_source(corpus)
    batch_prefix_violations = _SHARED_HTML_PREFLIGHT(batch_prefix_source)
    _SHARED_POLICING["_assert_supported_governed_html"](batch_prefix_violations)
    batch_prefix = _normalised_registry_batch_prefix_value(corpus)
    assert not batch_prefix, (
        "governed registry batch prefix must remain empty before the first registered entry; "
        f"got {batch_prefix!r}"
    )
'''
registry = replace_once(registry, old_prefix_validation, new_prefix_validation, "registry prefix validation")

prefix_test_anchor = '''def test_trailing_registry_visible_corpus_is_pinned():
'''
new_prefix_tests = '''@pytest.mark.parametrize(
    "injected",
    (
        '<a href="https://creativecommons.org/publicdomain/zero/1.0/" rel="license"></a>',
        '<meta itemprop="license" content="CC0">',
        '<hr>',
    ),
)
def test_governed_registry_batch_prefix_rejects_nontext_rendering_semantics(injected: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    mutated = corpus.replace(BATCH_HEADING, BATCH_HEADING + "\\n\\n" + injected, 1)
    assert mutated != corpus
    assert _normalised_registry_batch_prefix_value(mutated) == ""
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_trailing_registry_visible_corpus_is_pinned():
'''
registry = replace_once(registry, prefix_test_anchor, new_prefix_tests, "registry prefix regressions")
registry_path.write_text(registry, encoding="utf-8")

phase2 = phase2_path.read_text(encoding="utf-8")
namespace_anchor = '''    namespace["_assert_supported_governed_html"](violations - {"semantic-heading"})
    return namespace


def _visible_phase2_notes(changelog: str) -> str:
'''
namespace_replacement = '''    namespace["_assert_supported_governed_html"](violations - {"semantic-heading"})
    return namespace


def _assert_phase2_section_link_free(section: str, namespace: dict) -> None:
    """Keep Phase 2 changelog claims free of unsealed hyperlink destinations."""
    structure = namespace["_rendered_structure"](section)
    assert not tuple(namespace["_iter_inline_markdown_destinations"](structure)), (
        "unexpected Markdown hyperlink in governed Phase 2 changelog section"
    )
    assert namespace["AUTOLINK_PATTERN"].search(structure) is None, (
        "unexpected autolink in governed Phase 2 changelog section"
    )
    assert re.search(
        r"<\\s*a\\b(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*\\bhref(?:\\s*=|\\s|/?>)",
        structure,
        flags=re.IGNORECASE | re.DOTALL,
    ) is None, "unexpected raw HTML hyperlink in governed Phase 2 changelog section"
    assert re.search(
        r"(?<!!)\\[[^\\]\\r\\n]+\\]\\s*\\[[^\\]\\r\\n]*\\]",
        structure,
    ) is None, "unexpected reference-style hyperlink in governed Phase 2 changelog section"


def _visible_phase2_notes(changelog: str) -> str:
'''
phase2 = replace_once(phase2, namespace_anchor, namespace_replacement, "phase2 link helper")

notes_anchor = '''    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"

    phase2_structure = structure[phase2_start:phase1_start]
'''
notes_replacement = '''    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"

    phase2_source = changelog[phase2_start:phase1_start]
    _assert_phase2_section_link_free(phase2_source, namespace)
    phase2_structure = structure[phase2_start:phase1_start]
'''
phase2 = replace_once(phase2, notes_anchor, notes_replacement, "phase2 notes link gate")

raw_anchor = '''    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"
    return changelog[phase2_start:phase1_start]
'''
raw_replacement = '''    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"
    section = changelog[phase2_start:phase1_start]
    _assert_phase2_section_link_free(section, namespace)
    return section
'''
phase2 = replace_once(phase2, raw_anchor, raw_replacement, "phase2 raw section link gate")

phase2 += '''\n\ndef test_phase2_receipts_reject_unsealed_link_destinations():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    mutated = changelog.replace(
        "ethical approvals",
        "[ethical approvals](https://example.com/fake-approval)",
        1,
    )
    assert mutated != changelog
    for receipt in (
        _visible_phase2_notes,
        _phase2_section_sha256,
        _phase2_records_sha256,
    ):
        with pytest.raises(AssertionError, match="hyperlink"):
            receipt(mutated)
'''
phase2_path.write_text(phase2, encoding="utf-8")
