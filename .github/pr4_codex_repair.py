from pathlib import Path
import hashlib
import pprint
import re
import runpy

ROOT = Path('.')
registry_path = ROOT / 'tests' / 'test_research_reference_registry.py'
h_path = ROOT / 'tests' / 'test_workstream_h_methodology.py'
regressions_path = ROOT / 'tests' / 'test_pr4_current_review_regressions.py'
roadmap_path = ROOT / 'ROADMAP.md'
methodology_path = ROOT / 'docs' / 'METHODOLOGY.md'

registry_ns = runpy.run_path(str(registry_path))
policing_ns = runpy.run_path(str(ROOT / 'tests' / 'test_policing_context_roadmap.py'))
h_ns = runpy.run_path(str(h_path))
corpus = (ROOT / 'docs' / 'RESEARCH-REFERENCE-CORPUS.md').read_text(encoding='utf-8')
methodology = methodology_path.read_text(encoding='utf-8')
roadmap = roadmap_path.read_text(encoding='utf-8')


def records_hash(source: str) -> str:
    records = policing_ns['_normalised_visible_workstream_records'](source)
    receipt = '\n'.join(f'{signature}\x1f{line}' for signature, line in records)
    return hashlib.sha256(receipt.encode('utf-8')).hexdigest()


# Derive immutable receipts from the canonical pre-repair tree.
research_record_hashes: dict[str, str] = {}
project_record_hashes: dict[str, str] = {}
entry_link_bindings: dict[str, tuple[tuple[str, str], ...]] = {}
sections = registry_ns['_registered_sections'](corpus)
for entry, section in sections.items():
    rendered, structure = registry_ns['_markdown_views'](section)
    research_headings = list(registry_ns['RESEARCH_MAPPING_HEADING_PATTERN'].finditer(structure))
    project_headings = list(registry_ns['PROJECT_MAPPING_HEADING_PATTERN'].finditer(structure))
    assert len(research_headings) == 1 and len(project_headings) == 1
    research_block = rendered[research_headings[0].end():project_headings[0].start()]
    safe_heading = re.search(
        rf'(?m)^ {{0,3}}{re.escape(registry_ns["SAFE_FIELD"])}',
        structure[project_headings[0].end():],
    )
    assert safe_heading
    project_start = project_headings[0].end()
    project_end = project_start + safe_heading.start()
    project_block = rendered[project_start:project_end]
    research_record_hashes[entry] = records_hash(research_block)
    project_record_hashes[entry] = records_hash(project_block)
    entry_link_bindings[entry] = tuple(
        registry_ns['_usable_https_source_bindings'](section, reference_scope=corpus)
    )

trans_raw = h_ns['_trans_tasman_raw'](methodology)
trans_source_hash = hashlib.sha256(trans_raw.encode('utf-8')).hexdigest()

g_heading = '### G. Trans-Tasman relational pragmatics and lexical context'
h_heading = '### H. Slang density, register compression, and operational intelligibility'
roadmap_structure = policing_ns['_rendered_structure'](roadmap)
g_start, _ = policing_ns['_visible_markdown_heading_span'](roadmap_structure, g_heading)
g_end, _ = policing_ns['_visible_markdown_heading_span'](roadmap_structure, h_heading)
assert g_start < g_end
g_raw = roadmap[g_start:g_end]
g_visible = ' '.join(policing_ns['_visible_text'](g_raw).split())
g_visible_hash = hashlib.sha256(g_visible.encode('utf-8')).hexdigest()
g_records_hash = records_hash(g_raw)

registry = registry_path.read_text(encoding='utf-8')

# 1) Apply every shared HTML-policy finding corpus-wide before slicing, while
# preserving the deliberately supported raw h3 entry-discovery path. Raw h3
# semantics are governed separately by _registered_sections()/ENTRY_CONTRACTS.
old = '    found = _SHARED_HTML_PREFLIGHT(text) & ACTIVE_DOCUMENT_HTML_KINDS\n'
new = '    found = set(_SHARED_HTML_PREFLIGHT(text)) - {"semantic-heading"}\n'
assert registry.count(old) == 1
registry = registry.replace(old, new, 1)

# 2) Add immutable mapping-container receipts, but enforce them only after the
# existing content-value contract so historical diagnostics retain precedence.
marker = 'def _require_mapping_block(entry: str, section: str) -> tuple[str, str]:\n'
assert registry.count(marker) == 1
constants = (
    'RESEARCH_MAPPING_RECORD_HASHES: dict[str, str] = '
    + pprint.pformat(research_record_hashes, width=100, sort_dicts=True)
    + '\nPROJECT_MAPPING_RECORD_HASHES: dict[str, str] = '
    + pprint.pformat(project_record_hashes, width=100, sort_dicts=True)
    + '\nENTRY_WIDE_LINK_BINDINGS: dict[str, tuple[tuple[str, str], ...]] = '
    + pprint.pformat(entry_link_bindings, width=100, sort_dicts=True)
    + '\n\n\ndef _mapping_record_hashes(section: str) -> tuple[str, str]:\n'
    + '    rendered, structure = _markdown_views(section)\n'
    + '    research_headings = list(RESEARCH_MAPPING_HEADING_PATTERN.finditer(structure))\n'
    + '    project_headings = list(PROJECT_MAPPING_HEADING_PATTERN.finditer(structure))\n'
    + '    assert len(research_headings) == 1 and len(project_headings) == 1\n'
    + '    research_block = rendered[research_headings[0].end():project_headings[0].start()]\n'
    + '    safe_heading = re.search(\n'
    + '        rf"(?m)^ {{0,3}}{re.escape(SAFE_FIELD)}",\n'
    + '        structure[project_headings[0].end():],\n'
    + '    )\n'
    + '    assert safe_heading is not None\n'
    + '    project_start = project_headings[0].end()\n'
    + '    project_end = project_start + safe_heading.start()\n'
    + '    project_block = rendered[project_start:project_end]\n'
    + '    records_fn = _SHARED_POLICING["_normalised_visible_workstream_records"]\n'
    + '    def digest(block: str) -> str:\n'
    + '        records = records_fn(block)\n'
    + '        receipt = "\\n".join(f"{signature}\\x1f{line}" for signature, line in records)\n'
    + '        return hashlib.sha256(receipt.encode("utf-8")).hexdigest()\n'
    + '    return digest(research_block), digest(project_block)\n\n\n'
)
registry = registry.replace(marker, constants + marker, 1)

contract_anchor = (
    '    _require_pinned_entry_contract(\n'
    '        entry,\n'
    '        classification=classification,\n'
    '        scalar_values=scalar_values,\n'
    '        destinations=destinations,\n'
    '        research_mapping=research_mapping,\n'
    '        project_mapping=project_mapping,\n'
    '    )\n'
)
assert registry.count(contract_anchor) == 1
registry = registry.replace(
    contract_anchor,
    contract_anchor
    + '    actual_research_records_hash, actual_project_records_hash = _mapping_record_hashes(section)\n'
    + '    expected_research_records_hash = RESEARCH_MAPPING_RECORD_HASHES[entry]\n'
    + '    expected_project_records_hash = PROJECT_MAPPING_RECORD_HASHES[entry]\n'
    + '    assert actual_research_records_hash == expected_research_records_hash, (\n'
    + '        f"{entry} research mapping hierarchy changed: expected hash "\n'
    + '        f"{expected_research_records_hash!r}, got {actual_research_records_hash!r}"\n'
    + '    )\n'
    + '    assert actual_project_records_hash == expected_project_records_hash, (\n'
    + '        f"{entry} project mapping hierarchy changed: expected hash "\n'
    + '        f"{expected_project_records_hash!r}, got {actual_project_records_hash!r}"\n'
    + '    )\n',
    1,
)

# 3) Bind every explicit hyperlink in an entry. Run this after the pre-existing
# complete visible-entry seal so older content diagnostics remain stable; a link
# wrapped around unchanged prose reaches this new binding assertion.
complete_anchor = '    _require_complete_entry_integrity(entry, section)\n'
assert registry.count(complete_anchor) == 1
registry = registry.replace(
    complete_anchor,
    complete_anchor
    + '    whole_entry_bindings = tuple(\n'
    + '        _usable_https_source_bindings(section, reference_scope=reference_scope)\n'
    + '    )\n'
    + '    expected_entry_bindings = ENTRY_WIDE_LINK_BINDINGS[entry]\n'
    + '    assert whole_entry_bindings == expected_entry_bindings, (\n'
    + '        f"{entry} contains ungoverned or misbound hyperlinks outside its pinned "\n'
    + '        f"entry contract: expected {expected_entry_bindings!r}, "\n'
    + '        f"got {whole_entry_bindings!r}"\n'
    + '    )\n',
    1,
)
registry_path.write_text(registry, encoding='utf-8')

# 4) Trans-Tasman: the existing visible hash is intentionally whitespace
# normalized. Add a second exact source-structure seal after it, so two-space
# paragraph continuation cannot narrow an independent evidence boundary.
h_text = h_path.read_text(encoding='utf-8')
visible_line = re.search(r'^TRANS_TASMAN_VISIBLE_SHA256 = .+$', h_text, flags=re.MULTILINE)
assert visible_line
h_text = (
    h_text[:visible_line.end()]
    + f'\nTRANS_TASMAN_SOURCE_STRUCTURE_SHA256 = "{trans_source_hash}"'
    + h_text[visible_line.end():]
)
return_anchor = (
    '    assert actual_hash == TRANS_TASMAN_VISIBLE_SHA256, (\n'
    '        "browser-visible Trans-Tasman methodology changed: expected hash "\n'
    '        f"{TRANS_TASMAN_VISIBLE_SHA256!r}, got {actual_hash!r}"\n'
    '    )\n'
    '    return section\n'
)
assert h_text.count(return_anchor) == 1
h_text = h_text.replace(
    return_anchor,
    '    assert actual_hash == TRANS_TASMAN_VISIBLE_SHA256, (\n'
    '        "browser-visible Trans-Tasman methodology changed: expected hash "\n'
    '        f"{TRANS_TASMAN_VISIBLE_SHA256!r}, got {actual_hash!r}"\n'
    '    )\n'
    '    actual_structure_hash = hashlib.sha256(raw_section.encode("utf-8")).hexdigest()\n'
    '    assert actual_structure_hash == TRANS_TASMAN_SOURCE_STRUCTURE_SHA256, (\n'
    '        "Trans-Tasman methodology record hierarchy changed: expected source-structure hash "\n'
    '        f"{TRANS_TASMAN_SOURCE_STRUCTURE_SHA256!r}, got {actual_structure_hash!r}"\n'
    '    )\n'
    '    return section\n',
    1,
)
h_path.write_text(h_text, encoding='utf-8')

# 5) Workstream G: section-scoped, browser-visible and container-aware receipt,
# plus explicit nonfactual and safe-abstraction boundary mutations.
g_test = f'''"""Integrity receipt for Roadmap Workstream G trans-Tasman safeguards."""

from pathlib import Path
import hashlib
import runpy

import pytest


ROOT = Path(__file__).parent.parent
ROADMAP = ROOT / "ROADMAP.md"
POLICING = runpy.run_path(str(Path(__file__).with_name("test_policing_context_roadmap.py")))
WORKSTREAM_G_HEADING = {g_heading!r}
WORKSTREAM_H_HEADING = {h_heading!r}
WORKSTREAM_G_VISIBLE_SHA256 = {g_visible_hash!r}
WORKSTREAM_G_RECORDS_SHA256 = {g_records_hash!r}
NONFACTUAL_BOUNDARY = (
    "The research lead is not a factual statement about New Zealanders and is not evidence "
    "that Australians generally hold the underlying belief."
)
SAFE_ABSTRACTION_BOUNDARY = (
    "Redistributable benchmark items should model the relational and mention-versus-use "
    "structure with abstract placeholders or non-identity-targeted synthetic content rather "
    "than manufacturing new nationality stereotypes."
)


def _workstream_g_raw(text: str) -> str:
    POLICING["_assert_supported_governed_html"](
        POLICING["_governed_surface_html_violations"](text)
    )
    structure = POLICING["_rendered_structure"](text)
    start, _ = POLICING["_visible_markdown_heading_span"](structure, WORKSTREAM_G_HEADING)
    end, _ = POLICING["_visible_markdown_heading_span"](structure, WORKSTREAM_H_HEADING)
    assert start < end, "rendered Workstream G boundary is invalid"
    return text[start:end]


def _assert_workstream_g_integrity(text: str) -> str:
    raw = _workstream_g_raw(text)
    visible = " ".join(POLICING["_visible_text"](raw).split())
    actual_visible_hash = hashlib.sha256(visible.encode("utf-8")).hexdigest()
    assert actual_visible_hash == WORKSTREAM_G_VISIBLE_SHA256, (
        "browser-visible Workstream G changed: expected hash "
        f"{WORKSTREAM_G_VISIBLE_SHA256!r}, got {actual_visible_hash!r}"
    )
    records = POLICING["_normalised_visible_workstream_records"](raw)
    receipt = "\n".join(f"{signature}\x1f{line}" for signature, line in records)
    actual_records_hash = hashlib.sha256(receipt.encode("utf-8")).hexdigest()
    assert actual_records_hash == WORKSTREAM_G_RECORDS_SHA256, (
        "Workstream G record hierarchy changed: expected hash "
        f"{WORKSTREAM_G_RECORDS_SHA256!r}, got {actual_records_hash!r}"
    )
    assert NONFACTUAL_BOUNDARY in visible
    assert SAFE_ABSTRACTION_BOUNDARY in visible
    return visible


def test_workstream_g_stereotype_boundary_is_pinned() -> None:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    _assert_workstream_g_integrity(roadmap)
    reversed_claim = (
        "The research lead is a factual statement about New Zealanders and is evidence "
        "that Australians generally hold the underlying belief."
    )
    mutated = roadmap.replace(NONFACTUAL_BOUNDARY, reversed_claim, 1)
    with pytest.raises(AssertionError):
        _assert_workstream_g_integrity(mutated)


def test_workstream_g_safe_abstraction_boundary_is_pinned() -> None:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    mutated = roadmap.replace(
        SAFE_ABSTRACTION_BOUNDARY,
        "Redistributable benchmark items may reproduce nationality stereotypes directly.",
        1,
    )
    with pytest.raises(AssertionError):
        _assert_workstream_g_integrity(mutated)
'''
(ROOT / 'tests' / 'test_workstream_g_integrity.py').write_text(g_test, encoding='utf-8')

extra = r'''


def test_full_registry_html_policy_rejects_machine_metadata_before_title() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    mutated = '<a href="https://creativecommons.org/publicdomain/zero/1.0/" rel="license"></a>\n' + corpus
    with pytest.raises(AssertionError, match="machine-readable"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_governed_entry_rejects_hyperlink_outside_source_contract() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    phrase = "This project must not copy screenplay text"
    assert phrase in corpus
    mutated = corpus.replace(
        phrase,
        f'[{phrase}](https://creativecommons.org/publicdomain/zero/1.0/)',
        1,
    )
    with pytest.raises(AssertionError, match="ungoverned or misbound hyperlinks"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_trans_tasman_methodology_preserves_record_hierarchy() -> None:
    methodology = (ROOT / "docs" / "METHODOLOGY.md").read_text(encoding="utf-8")
    paragraph = "Official or archival military sources may motivate **communication-friction** hypotheses"
    assert paragraph in methodology
    mutated = methodology.replace(paragraph, "  " + paragraph, 1)
    with pytest.raises(AssertionError, match="record hierarchy changed"):
        WORKSTREAM_H["_assert_trans_tasman_integrity"](mutated)


def test_registry_mapping_receipts_preserve_list_hierarchy() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = REGISTRY["_registered_sections"](corpus)[entry]
    lines = section.splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if "AU-HUMOUR-007" in line and line.startswith("- "):
            lines[index] = "  " + line
            changed = True
            break
    assert changed, "expected noninitial Black Comedy mapping bullet was not found"
    mutated_section = "".join(lines)
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="mapping hierarchy changed"):
        REGISTRY["_validate_registry_corpus"](mutated)
'''
regression_text = regressions_path.read_text(encoding='utf-8')
sentinel = 'test_full_registry_html_policy_rejects_machine_metadata_before_title'
assert sentinel not in regression_text
regressions_path.write_text(regression_text + extra, encoding='utf-8')
