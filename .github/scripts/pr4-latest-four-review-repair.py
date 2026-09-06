from __future__ import annotations

import hashlib
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_TEST = ROOT / "tests" / "test_research_reference_registry.py"
WORKSTREAM_TEST = ROOT / "tests" / "test_workstream_h_methodology.py"
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"

SOURCE_USE_PLACEHOLDER = "__SOURCE_USE_SECTION_HASH__"
TRANS_TASMAN_PLACEHOLDER = "__TRANS_TASMAN_VISIBLE_SHA256__"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


registry = REGISTRY_TEST.read_text(encoding="utf-8")

registry = replace_once(
    registry,
    'REGISTRATION_CONTRACT_HASH = "1d171556a66c3cfc54a7bf14072d51bb68d17cb390fffa826a0f50329e2d51d6"\n',
    'REGISTRATION_CONTRACT_HASH = "1d171556a66c3cfc54a7bf14072d51bb68d17cb390fffa826a0f50329e2d51d6"\n'
    f'SOURCE_USE_SECTION_HASH = "{SOURCE_USE_PLACEHOLDER}"\n',
    "source-use hash constant",
)

registry = replace_once(
    registry,
    '''GOVERNED_INTERACTIVE_HTML_PATTERN = re.compile(
    r"<(?:form|input|button|select|textarea|option|optgroup)\\b",
    flags=re.IGNORECASE,
)
''',
    '''GOVERNED_INTERACTIVE_HTML_PATTERN = re.compile(
    r"<(?:form|input|button|select|textarea|option|optgroup)\\b",
    flags=re.IGNORECASE,
)
GOVERNED_STYLING_HTML_PATTERN = re.compile(
    r"<(?:style|link)\\b|<[A-Za-z][^>]*\\bclass[ \\t]*=",
    flags=re.IGNORECASE,
)
GOVERNED_REPLACEMENT_HTML_PATTERN = re.compile(
    r"<(?:object|embed|iframe)\\b",
    flags=re.IGNORECASE,
)
''',
    "governed HTML patterns",
)

registry = replace_once(
    registry,
    '''def _normalise_complete_entry_integrity(section: str) -> str:
    """Return the complete render-aware governed-entry body for integrity pinning."""
    return _visible_inline_text(section)


def _require_complete_entry_integrity(entry: str, section: str) -> None:
''',
    '''def _forbidden_governed_html_constructs(text: str) -> set[str]:
    """Detect live styling/replacement HTML while ignoring Markdown code containers."""
    rendered = _rendered_registry_text(text)
    scan = _mask_multiline_code_spans(rendered)
    fence: FenceState | None = None
    found: set[str] = set()

    for raw_line in scan.splitlines():
        while fence is not None and not _fence_container_continues(raw_line, fence):
            fence = None

        if fence is not None:
            if _is_fence_closer(raw_line, fence):
                fence = None
            continue

        opener = _fence_opener(raw_line)
        if opener is not None:
            fence = opener
            continue

        logical, is_code = _strip_composed_container_prefixes(raw_line)
        if is_code:
            continue
        logical = _mask_inline_code_spans(logical)
        if GOVERNED_STYLING_HTML_PATTERN.search(logical):
            found.add("styling")
        if GOVERNED_REPLACEMENT_HTML_PATTERN.search(logical):
            found.add("replacement")
    return found


def _normalise_complete_entry_integrity(section: str) -> str:
    """Return the complete render-aware governed-entry body for integrity pinning."""
    return _visible_inline_text(section)


def _require_complete_entry_integrity(entry: str, section: str) -> None:
''',
    "forbidden governed HTML helper",
)

registry = replace_once(
    registry,
    '''    rendered_section = _rendered_registry_text(section)
    structural_section = _structural_registry_text(section)
    assert not _contains_visually_hidden_table(structural_section), (
''',
    '''    rendered_section = _rendered_registry_text(section)
    structural_section = _structural_registry_text(section)
    forbidden_html = _forbidden_governed_html_constructs(section)
    assert "replacement" not in forbidden_html, (
        f"{entry} contains replacement-content HTML (object/embed/iframe), which is "
        "not permitted in governed entries because browser replacement semantics can "
        "hide pinned fallback provenance"
    )
    assert not _contains_visually_hidden_table(structural_section), (
''',
    "replacement-content fail-closed check",
)

registry = replace_once(
    registry,
    '''def _validate_registry_corpus(corpus: str) -> None:
    rendered, structure = _markdown_views(corpus)
''',
    '''def _normalised_source_use_rules_value(corpus: str) -> str:
    """Return the complete browser-visible Source-use rules section."""
    rendered, structure = _markdown_views(corpus)
    start, _ = _visible_markdown_heading_span(structure, SOURCE_USE_HEADING)
    end, _ = _visible_markdown_heading_span(structure, CONTRACT_HEADING)
    assert start < end, "rendered source-use/registration-contract boundaries are out of order"
    return _visible_inline_text(rendered[start:end])


def _validate_registry_corpus(corpus: str) -> None:
    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)
    assert "styling" not in corpus_forbidden_html, (
        "registry contains stylesheet/class-driven HTML styling; governed source "
        "visibility must not depend on embedded stylesheet selectors"
    )
    rendered, structure = _markdown_views(corpus)
''',
    "source-use helper and global stylesheet guard",
)

registry = replace_once(
    registry,
    '''    assert REDISTRIBUTION_INVARIANT in visible_status, (
        "redistribution invariant must remain browser-visible inside the Status section"
    )

    sections = _registered_sections(corpus)
''',
    '''    assert REDISTRIBUTION_INVARIANT in visible_status, (
        "redistribution invariant must remain browser-visible inside the Status section"
    )

    visible_source_use = _normalised_source_use_rules_value(corpus)
    actual_source_use_hash = hashlib.sha256(visible_source_use.encode("utf-8")).hexdigest()
    assert actual_source_use_hash == SOURCE_USE_SECTION_HASH, (
        "browser-visible source-use rules changed or were weakened: "
        f"expected hash {SOURCE_USE_SECTION_HASH!r}, got {actual_source_use_hash!r}"
    )

    sections = _registered_sections(corpus)
''',
    "source-use seal enforcement",
)

registry = replace_once(
    registry,
    '''def test_post_phase2_registry_batch_preserves_governance_contract():
    _validate_registry_corpus(CORPUS.read_text(encoding="utf-8"))


def test_registered_source_resolves_document_scoped_reference_definition():
''',
    '''def test_post_phase2_registry_batch_preserves_governance_contract():
    _validate_registry_corpus(CORPUS.read_text(encoding="utf-8"))


def test_source_use_rules_are_complete_and_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(SOURCE_USE_HEADING) + len(SOURCE_USE_HEADING)
    end = corpus.index(CONTRACT_HEADING, start)
    mutated = (
        corpus[:start]
        + "\\n\\nAll source-use rules are optional.\\n\\n---\\n\\n"
        + corpus[end:]
    )
    with pytest.raises(AssertionError, match="source-use rules changed or were weakened"):
        _validate_registry_corpus(mutated)


def test_stylesheet_driven_hiding_is_rejected_fail_closed():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    rights = str(ENTRY_CONTRACTS[entry][RIGHTS_FIELD])
    assert rights in section
    replacement = (
        f'<span class="conceal">{rights}</span>'
        "\\n\\n<style>.conceal { display:none }</style>"
    )
    mutated_section = section.replace(rights, replacement, 1)
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="stylesheet/class-driven HTML styling"):
        _validate_registry_corpus(mutated)


def test_embedded_replacement_content_is_rejected_fail_closed():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(
        heading for heading in EXPECTED_GOVERNED_ENTRIES if heading.startswith("### Hurley (2025)")
    )
    section = _registered_sections(corpus)[entry]
    source = str(ENTRY_CONTRACTS[entry][SOURCES_KEY][0])
    original = f"**Registered source:** {source}"
    replacement = (
        f'**Registered source:** <object data="data:text/html,No attributable source">'
        f'<a href="{source}">{source}</a></object>'
    )
    assert original in section
    mutated_section = section.replace(original, replacement, 1)
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="replacement-content HTML"):
        _validate_registry_corpus(mutated)


def test_registered_source_resolves_document_scoped_reference_definition():
''',
    "latest registry regressions",
)

REGISTRY_TEST.write_text(registry.rstrip("\n") + "\n", encoding="utf-8")

registry_ns = runpy.run_path(str(REGISTRY_TEST))
source_use_value = registry_ns["_normalised_source_use_rules_value"](
    CORPUS.read_text(encoding="utf-8")
)
source_use_hash = hashlib.sha256(source_use_value.encode("utf-8")).hexdigest()
registry = REGISTRY_TEST.read_text(encoding="utf-8")
registry = replace_once(
    registry,
    f'SOURCE_USE_SECTION_HASH = "{SOURCE_USE_PLACEHOLDER}"',
    f'SOURCE_USE_SECTION_HASH = "{source_use_hash}"',
    "computed source-use hash",
)
REGISTRY_TEST.write_text(registry.rstrip("\n") + "\n", encoding="utf-8")

workstream = WORKSTREAM_TEST.read_text(encoding="utf-8")
workstream = replace_once(
    workstream,
    'WORKSTREAM_H_VISIBLE_SHA256 = "c38e4bc194d820c30ee714851ec279da7649fffc921da5a331d722d22d7c34b8"\n',
    'WORKSTREAM_H_VISIBLE_SHA256 = "c38e4bc194d820c30ee714851ec279da7649fffc921da5a331d722d22d7c34b8"\n'
    f'TRANS_TASMAN_VISIBLE_SHA256 = "{TRANS_TASMAN_PLACEHOLDER}"\n',
    "Trans-Tasman hash constant",
)

workstream = replace_once(
    workstream,
    '''def _trans_tasman_methodology(text: str) -> str:
    start, _ = _rendered_heading_span(text, TRANS_TASMAN_METHODOLOGY_HEADING)
    end, _ = _rendered_heading_span(text, POLICING_METHODOLOGY_HEADING)
    assert start < end, "rendered Trans-Tasman methodology boundary is invalid"
    return _visible_markdown_text(text[start:end])


def test_workstream_h_decouples_dialect_exposure_from_listener_identity():
''',
    '''def _trans_tasman_methodology(text: str) -> str:
    start, _ = _rendered_heading_span(text, TRANS_TASMAN_METHODOLOGY_HEADING)
    end, _ = _rendered_heading_span(text, POLICING_METHODOLOGY_HEADING)
    assert start < end, "rendered Trans-Tasman methodology boundary is invalid"
    return _visible_markdown_text(text[start:end])


def _normalised_trans_tasman_visible_value(text: str) -> str:
    return " ".join(_trans_tasman_methodology(text).split())


def _assert_trans_tasman_integrity(text: str) -> str:
    section = _trans_tasman_methodology(text)
    value = " ".join(section.split())
    actual_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
    assert actual_hash == TRANS_TASMAN_VISIBLE_SHA256, (
        "browser-visible Trans-Tasman methodology changed: expected hash "
        f"{TRANS_TASMAN_VISIBLE_SHA256!r}, got {actual_hash!r}"
    )
    return section


def test_trans_tasman_methodology_rejects_companion_identity_reversal():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    _assert_trans_tasman_integrity(methodology)
    reversal = "Nationality and first-language identity should define the comparison cohorts."
    mutated = methodology.replace(
        POLICING_METHODOLOGY_HEADING,
        reversal + "\\n\\n" + POLICING_METHODOLOGY_HEADING,
        1,
    )
    with pytest.raises(AssertionError, match="browser-visible Trans-Tasman methodology changed"):
        _assert_trans_tasman_integrity(mutated)


def test_workstream_h_decouples_dialect_exposure_from_listener_identity():
''',
    "Trans-Tasman section seal",
)

WORKSTREAM_TEST.write_text(workstream.rstrip("\n") + "\n", encoding="utf-8")

workstream_ns = runpy.run_path(str(WORKSTREAM_TEST))
trans_tasman_value = workstream_ns["_normalised_trans_tasman_visible_value"](
    METHODOLOGY.read_text(encoding="utf-8")
)
trans_tasman_hash = hashlib.sha256(trans_tasman_value.encode("utf-8")).hexdigest()
workstream = WORKSTREAM_TEST.read_text(encoding="utf-8")
workstream = replace_once(
    workstream,
    f'TRANS_TASMAN_VISIBLE_SHA256 = "{TRANS_TASMAN_PLACEHOLDER}"',
    f'TRANS_TASMAN_VISIBLE_SHA256 = "{trans_tasman_hash}"',
    "computed Trans-Tasman hash",
)
WORKSTREAM_TEST.write_text(workstream.rstrip("\n") + "\n", encoding="utf-8")

print(f"source-use section sha256: {source_use_hash}")
print(f"Trans-Tasman methodology sha256: {trans_tasman_hash}")
