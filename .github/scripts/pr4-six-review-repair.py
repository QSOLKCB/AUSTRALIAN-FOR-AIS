from __future__ import annotations

import hashlib
from pathlib import Path
import pprint
import runpy


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"{path}: replacement already applied, skipping")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all_exact(path: Path, old: str, new: str, expected_count: int) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(new) == expected_count:
        print(f"{path}: repeated replacement already applied, skipping")
        return
    count = text.count(old)
    if count != expected_count:
        raise SystemExit(
            f"{path}: expected {expected_count} repeated anchors, found {count}"
        )
    path.write_text(text.replace(old, new), encoding="utf-8")


def replace_between(
    path: Path,
    start_marker: str,
    end_marker: str,
    replacement: str,
    *,
    already_marker: str | None = None,
) -> None:
    text = path.read_text(encoding="utf-8")
    if already_marker is not None and already_marker in text:
        print(f"{path}: block replacement already applied, skipping")
        return
    if text.count(start_marker) != 1:
        raise SystemExit(
            f"{path}: expected one block start {start_marker!r}, found {text.count(start_marker)}"
        )
    start = text.index(start_marker)
    try:
        end = text.index(end_marker, start)
    except ValueError as exc:
        raise SystemExit(f"{path}: missing block end {end_marker!r}") from exc
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def append_once(path: Path, sentinel: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel in text:
        print(f"{path}: appended regression already present, skipping")
        return
    path.write_text(text.rstrip() + "\n\n\n" + addition.strip() + "\n", encoding="utf-8")


registry = Path("tests/test_research_reference_registry.py")
workstream_h = Path("tests/test_workstream_h_methodology.py")
policing = Path("tests/test_policing_context_roadmap.py")
receipt = Path("tests/test_policing_contract_receipt.py")
roadmap = Path("ROADMAP.md")

# ---------------------------------------------------------------------------
# Registry: reserve complete per-entry mapping integrity fixtures.
# ---------------------------------------------------------------------------
replace_once(
    registry,
    'SOURCES_KEY = "sources"\n',
    'SOURCES_KEY = "sources"\n'
    'RESEARCH_MAPPING_VALUE_HASHES: dict[str, str] = {}\n'
    'PROJECT_MAPPING_VALUE_HASHES: dict[str, str] = {}\n',
)

# Markdown character references are decoded before a browser navigates links.
replace_once(
    registry,
    '    value = candidate.strip().strip("<>").rstrip(".,;:!?")\n',
    '    value = html.unescape(candidate).strip().strip("<>").rstrip(".,;:!?")\n',
)

# Render a leading non-image inline link label before classifying metadata.
replace_once(
    registry,
    '    decoded = html.unescape(line)\n    match = STRONG_METADATA_FIELD_PATTERN.match(decoded)\n',
    '    decoded = html.unescape(line)\n'
    '    inline_links = _markdown_inline_links(decoded)\n'
    '    if inline_links:\n'
    '        first_link = inline_links[0]\n'
    '        if first_link.start == 0 and not first_link.image:\n'
    '            decoded = first_link.label + decoded[first_link.end:]\n'
    '    match = STRONG_METADATA_FIELD_PATTERN.match(decoded)\n',
)

# Return the complete normalized research/project mapping values after the
# existing structural/non-empty validation. These values are then hash-pinned.
new_mapping_function = '''def _require_mapping_block(entry: str, section: str) -> tuple[str, str]:
    normalised = _normalised_rendered_lines(section)
    research_count = sum(
        1
        for logical, _, is_code in normalised
        if not is_code and logical.strip() in {"Candidate research mappings:", "Research mappings:"}
    )
    project_count = sum(
        1
        for logical, _, is_code in normalised
        if not is_code and logical.strip() == "Relevant project mappings:"
    )
    assert research_count == 1, f"{entry} must contain exactly one research mappings heading"
    assert project_count == 1, f"{entry} must contain exactly one relevant project mappings heading"

    rendered, structure = _markdown_views(section)
    research_headings = list(RESEARCH_MAPPING_HEADING_PATTERN.finditer(structure))
    project_headings = list(PROJECT_MAPPING_HEADING_PATTERN.finditer(structure))
    assert len(research_headings) == 1 and len(project_headings) == 1

    research_start = research_headings[0].end()
    project_start = project_headings[0].start()
    assert research_start < project_start, f"{entry} has research/project mapping headings in the wrong order"
    research_block = rendered[research_start:project_start]
    assert _has_non_heading_content(research_block), f"{entry} has empty research mappings"
    research_value = _visible_inline_text(research_block)
    assert research_value, f"{entry} has empty research mappings"

    safe_heading = re.search(
        rf"(?m)^ {{0,3}}{re.escape(SAFE_FIELD)}",
        structure[project_headings[0].end():],
    )
    assert safe_heading, f"{entry} is missing the safe benchmark abstraction field"
    project_value_start = project_headings[0].end()
    project_end = project_value_start + safe_heading.start()
    project_block = rendered[project_value_start:project_end]
    assert _has_non_heading_content(project_block), f"{entry} has empty project mappings"
    project_value = _visible_inline_text(project_block)
    assert project_value, f"{entry} has empty project mappings"
    return research_value, project_value


'''
replace_between(
    registry,
    'def _require_mapping_block(entry: str, section: str) -> None:\n',
    'def _require_registered_source_link(',
    new_mapping_function,
    already_marker='def _require_mapping_block(entry: str, section: str) -> tuple[str, str]:',
)

replace_once(
    registry,
    '    destinations: tuple[str, ...],\n) -> None:\n',
    '    destinations: tuple[str, ...],\n'
    '    research_mapping: str,\n'
    '    project_mapping: str,\n'
    ') -> None:\n',
)

replace_once(
    registry,
    '''            assert actual_hash == expected_hash, (
                f"{entry} changed pinned {field}: expected hash "
                f"{expected_hash!r}, got {actual_hash!r}"
            )

def _validate_registered_entry(
''',
    '''            assert actual_hash == expected_hash, (
                f"{entry} changed pinned {field}: expected hash "
                f"{expected_hash!r}, got {actual_hash!r}"
            )

    actual_research_hash = hashlib.sha256(research_mapping.encode("utf-8")).hexdigest()
    expected_research_hash = RESEARCH_MAPPING_VALUE_HASHES[entry]
    assert actual_research_hash == expected_research_hash, (
        f"{entry} research mappings changed: expected hash "
        f"{expected_research_hash!r}, got {actual_research_hash!r}"
    )
    actual_project_hash = hashlib.sha256(project_mapping.encode("utf-8")).hexdigest()
    expected_project_hash = PROJECT_MAPPING_VALUE_HASHES[entry]
    assert actual_project_hash == expected_project_hash, (
        f"{entry} project mappings changed: expected hash "
        f"{expected_project_hash!r}, got {actual_project_hash!r}"
    )


def _validate_registered_entry(
''',
)

replace_once(
    registry,
    '''    classification = _require_community_governance(entry, section)
    _require_pinned_entry_contract(
        entry,
        classification=classification,
        scalar_values=scalar_values,
        destinations=destinations,
    )
    _require_mapping_block(entry, section)
''',
    '''    classification = _require_community_governance(entry, section)
    research_mapping, project_mapping = _require_mapping_block(entry, section)
    _require_pinned_entry_contract(
        entry,
        classification=classification,
        scalar_values=scalar_values,
        destinations=destinations,
        research_mapping=research_mapping,
        project_mapping=project_mapping,
    )
''',
)

# ---------------------------------------------------------------------------
# Workstream H: align closed-dialog semantics with registry and policing.
# ---------------------------------------------------------------------------
replace_once(
    workstream_h,
    '        if tag == "details" and "open" not in values:\n            return True\n',
    '        if tag in {"details", "dialog"} and "open" not in values:\n            return True\n',
)
replace_once(
    workstream_h,
    '''        f"<span hidden>{listener_clause}</span>",
        f'[placeholder](# "{listener_clause}")',
''',
    '''        f"<span hidden>{listener_clause}</span>",
        f"<dialog>{listener_clause}</dialog>",
        f'[placeholder](# "{listener_clause}")',
''',
)

# ---------------------------------------------------------------------------
# Policing: exact affirmative lines, suffix-negation rejection, and review gate.
# ---------------------------------------------------------------------------
source_gate = (
    '    "register official and current sources for each Australian and United States '
    'jurisdictional claim",\n'
)
high_stakes_clause = (
    '    "before publishing any family involving coercion, consent, search, detention, "\n'
    '    "questioning, force, emergency powers, or legal rights, verify the governing "\n'
    '    "sources are current for the recorded jurisdiction and date and obtain appropriate "\n'
    '    "review from relevant Australian and United States legal, policing, civil-liberties, "\n'
    '    "and community expertise;",\n'
)
replace_all_exact(policing, source_gate, source_gate + high_stakes_clause, 2)

replace_once(
    policing,
    '''    "register official and current sources for each Australian and United States jurisdictional claim",
    "before publishing any family involving coercion, consent, search, detention, "
    "questioning, force, emergency powers, or legal rights, verify the governing "
    "sources are current for the recorded jurisdiction and date and obtain appropriate "
    "review from relevant Australian and United States legal, policing, civil-liberties, "
    "and community expertise;",
)

FENCE_PATTERN''',
    '''    "register official and current sources for each Australian and United States jurisdictional claim",
    "before publishing any family involving coercion, consent, search, detention, "
    "questioning, force, emergency powers, or legal rights, verify the governing "
    "sources are current for the recorded jurisdiction and date and obtain appropriate "
    "review from relevant Australian and United States legal, policing, civil-liberties, "
    "and community expertise;",
)

AFFIRMATIVE_EXACT_LINE_OVERRIDES = {
    "register official and current sources for each Australian and United States jurisdictional claim": (
        "register official and current sources for each Australian and United States "
        "jurisdictional claim before adopting it as benchmark context;"
    ),
}

FENCE_PATTERN''',
)

replace_once(
    policing,
    '''        if clause in AFFIRMATIVE_LINE_PREFIX_CLAUSES:
            assert any(line.startswith(visible_clause) for line in visible_lines), (
                f"missing policing-workstream safeguard: {clause}"
            )
''',
    '''        if clause in AFFIRMATIVE_LINE_PREFIX_CLAUSES:
            expected_line = _visible_text(
                AFFIRMATIVE_EXACT_LINE_OVERRIDES.get(clause, clause)
            )
            assert any(line == expected_line for line in visible_lines), (
                f"missing policing-workstream safeguard: {clause}"
            )
''',
)

old_review = (
    '- involve appropriate Australian and United States legal, policing, civil-liberties, '
    'and community expertise before publishing high-stakes conclusions;'
)
new_review = (
    '- before publishing any family involving coercion, consent, search, detention, '
    'questioning, force, emergency powers, or legal rights, verify the governing sources '
    'are current for the recorded jurisdiction and date and obtain appropriate review from '
    'relevant Australian and United States legal, policing, civil-liberties, and community expertise;'
)
replace_once(roadmap, old_review, new_review)

# ---------------------------------------------------------------------------
# Receipt: independently pin the roadmap/canonical high-stakes publication gate.
# ---------------------------------------------------------------------------
replace_once(
    receipt,
    '''POLICING_METADATA_INTRO = (
    "Every implemented policing-context item must record, at minimum:"
)
''',
    '''POLICING_METADATA_INTRO = (
    "Every implemented policing-context item must record, at minimum:"
)
HIGH_STAKES_REVIEW_SENTENCE = (
    "before publishing any family involving coercion, consent, search, detention, "
    "questioning, force, emergency powers, or legal rights, verify the governing sources "
    "are current for the recorded jurisdiction and date and obtain appropriate review from "
    "relevant Australian and United States legal, policing, civil-liberties, and community expertise;"
)
''',
)

append_once(
    receipt,
    "def test_high_stakes_family_review_gate_matches_canonical_methodology():",
    '''def test_high_stakes_family_review_gate_matches_canonical_methodology():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    methodology = _policing_methodology_section(
        METHODOLOGY.read_text(encoding="utf-8")
    )
    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))
    affirmative = set(_string_constants_in_tuple("AFFIRMATIVE_LINE_PREFIX_CLAUSES"))

    assert "before publishing high-stakes conclusions" not in roadmap
    assert HIGH_STAKES_REVIEW_SENTENCE in roadmap
    assert HIGH_STAKES_REVIEW_SENTENCE in required
    assert HIGH_STAKES_REVIEW_SENTENCE in affirmative
    assert "Before publication of a family involving coercion, consent, search, detention, questioning, force, emergency powers, or legal rights" in methodology
    assert "obtain appropriate review from relevant Australian and United States legal, policing, civil-liberties, and community expertise" in methodology
''',
)

append_once(
    policing,
    "def test_policing_source_gate_cannot_be_suffix_negated():",
    '''def test_policing_source_gate_cannot_be_suffix_negated():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    original = (
        "register official and current sources for each Australian and United States "
        "jurisdictional claim before adopting it as benchmark context;"
    )
    contradictory = (
        "register official and current sources for each Australian and United States "
        "jurisdictional claim only when convenient; no source is actually mandatory"
    )
    assert original in roadmap
    mutated = roadmap.replace(original, contradictory, 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)
''',
)

# ---------------------------------------------------------------------------
# Registry focused mutations for the new browser-equivalence and mapping gaps.
# ---------------------------------------------------------------------------
append_once(
    registry,
    "def test_link_wrapped_metadata_label_is_counted():",
    '''def test_link_wrapped_metadata_label_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    mutated = section.rstrip() + "\\n\\n[**DOI:**](#field) https://doi.org/10.0000/fabricated\\n"
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_entity_encoded_markdown_link_destination_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    pinned = "https://iview.abc.net.au/show/black-comedy"
    mutated = section.replace(
        pinned,
        pinned + " [alternate](https&#58;//www.wikipedia.org/)",
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_complete_per_entry_mappings_are_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    research = RESEARCH_MAPPING_HEADING_PATTERN.search(section)
    project = PROJECT_MAPPING_HEADING_PATTERN.search(section)
    assert research is not None and project is not None
    safe_start = section.index(SAFE_FIELD, project.end())
    mutated = (
        section[:research.end()]
        + "\\n\\n- unrelated placeholder\\n\\n"
        + section[project.start():project.end()]
        + "\\n\\n- unrelated placeholder\\n\\n"
        + section[safe_start:]
    )
    with pytest.raises(AssertionError, match="research mappings changed|project mappings changed"):
        _validate_registered_entry(entry, mutated)
''',
)

# ---------------------------------------------------------------------------
# Populate static mapping hashes from the unmutated governed corpus after the
# helper changes above have been written. No tests execute under runpy.
# ---------------------------------------------------------------------------
namespace = runpy.run_path(str(registry))
corpus = namespace["CORPUS"].read_text(encoding="utf-8")
sections = namespace["_registered_sections"](corpus)
require_mapping = namespace["_require_mapping_block"]
research_hashes: dict[str, str] = {}
project_hashes: dict[str, str] = {}
for entry, section in sections.items():
    research_value, project_value = require_mapping(entry, section)
    research_hashes[entry] = hashlib.sha256(research_value.encode("utf-8")).hexdigest()
    project_hashes[entry] = hashlib.sha256(project_value.encode("utf-8")).hexdigest()

text = registry.read_text(encoding="utf-8")
research_old = "RESEARCH_MAPPING_VALUE_HASHES: dict[str, str] = {}"
project_old = "PROJECT_MAPPING_VALUE_HASHES: dict[str, str] = {}"
if research_old not in text or project_old not in text:
    raise SystemExit("registry mapping-hash placeholders were not available exactly once")
text = text.replace(
    research_old,
    "RESEARCH_MAPPING_VALUE_HASHES: dict[str, str] = "
    + pprint.pformat(research_hashes, sort_dicts=True, width=100),
    1,
)
text = text.replace(
    project_old,
    "PROJECT_MAPPING_VALUE_HASHES: dict[str, str] = "
    + pprint.pformat(project_hashes, sort_dicts=True, width=100),
    1,
)
registry.write_text(text, encoding="utf-8")

print("Applied six-review governed-validation repairs.")
