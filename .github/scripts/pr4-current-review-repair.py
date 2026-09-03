from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_exact(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return text.replace(old, new)


registry_path = Path("tests/test_research_reference_registry.py")
registry = registry_path.read_text(encoding="utf-8")

registry = replace_once(
    registry,
    'def _usable_https_destinations(text: str) -> tuple[str, ...]:\n    """Extract usable rendered links while excluding code and link titles."""\n    structure = _mask_hidden_html_regions(_structural_registry_text(text))\n    destinations: list[str] = []\n',
    'def _usable_https_destinations(\n    text: str,\n    *,\n    reference_scope: str | None = None,\n) -> tuple[str, ...]:\n    """Extract rendered links, resolving reference definitions at document scope."""\n    structure = _mask_hidden_html_regions(_structural_registry_text(text))\n    definition_source = text if reference_scope is None else reference_scope\n    reference_structure = _mask_hidden_html_regions(\n        _structural_registry_text(definition_source)\n    )\n    destinations: list[str] = []\n',
    "document-scoped reference setup",
)
registry = replace_once(
    registry,
    '    definitions: dict[str, str] = {}\n    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(structure):\n',
    '    definitions: dict[str, str] = {}\n    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(reference_structure):\n',
    "document-scoped reference definitions",
)
registry = replace_once(
    registry,
    'def _require_registered_source_link(entry: str, section: str) -> tuple[str, ...]:\n',
    'def _require_registered_source_link(\n    entry: str,\n    section: str,\n    *,\n    reference_scope: str | None = None,\n) -> tuple[str, ...]:\n',
    "registered-source signature",
)
registry = replace_once(
    registry,
    '    destinations = _usable_https_destinations(source_value)\n',
    '    destinations = _usable_https_destinations(\n        source_value,\n        reference_scope=reference_scope,\n    )\n',
    "registered-source document scope",
)
registry = replace_once(
    registry,
    'def _validate_registered_entry(entry: str, section: str) -> None:\n    destinations = _require_registered_source_link(entry, section)\n',
    'def _validate_registered_entry(\n    entry: str,\n    section: str,\n    *,\n    reference_scope: str | None = None,\n) -> None:\n    destinations = _require_registered_source_link(\n        entry,\n        section,\n        reference_scope=reference_scope,\n    )\n',
    "entry validation reference scope",
)
registry = replace_once(
    registry,
    '    for entry, section in sections.items():\n        _validate_registered_entry(entry, section)\n',
    '    for entry, section in sections.items():\n        _validate_registered_entry(\n            entry,\n            section,\n            reference_scope=corpus,\n        )\n',
    "corpus validation reference scope",
)
registry = replace_once(
    registry,
    'def test_post_phase2_registry_batch_preserves_governance_contract():\n    _validate_registry_corpus(CORPUS.read_text(encoding="utf-8"))\n\n\n',
    '''def test_post_phase2_registry_batch_preserves_governance_contract():\n    _validate_registry_corpus(CORPUS.read_text(encoding="utf-8"))\n\n\ndef test_registered_source_resolves_document_scoped_reference_definition():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = EXPECTED_GOVERNED_ENTRIES[0]\n    section = _registered_sections(corpus)[entry]\n    marker = (\n        "**Registered source:**"\n        if "**Registered source:**" in section\n        else "**Registered sources:**"\n    )\n    mutated_section = section.replace(\n        marker,\n        f"{marker} [alternate][external-provenance]\\n",\n        1,\n    )\n    mutated = (\n        corpus.replace(section, mutated_section, 1)\n        + "\\n[external-provenance]: https://www.wikipedia.org/\\n"\n    )\n\n    with pytest.raises(AssertionError, match="registered-source destinations changed"):\n        _validate_registry_corpus(mutated)\n\n\n''',
    "document-scoped reference regression",
)
registry_path.write_text(registry, encoding="utf-8")


policing_path = Path("tests/test_policing_context_roadmap.py")
policing = policing_path.read_text(encoding="utf-8")

old_invariants = (
    '    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",\n'
    '    "CASUAL ADDRESS != FRIENDSHIP OR CONSENT",\n'
    '    "FICTIONAL POLICE TROPE != OPERATIONAL POLICY",\n'
    '    "JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER",\n'
)
new_invariants = (
    '    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",\n'
    '    "POLICE TERMINOLOGY != CROSS-JURISDICTION EQUIVALENCE",\n'
    '    "CASUAL ADDRESS != FRIENDSHIP OR CONSENT",\n'
    '    "CALM TONE != ABSENCE OF COERCIVE AUTHORITY",\n'
    '    "POLITE WORDING != VOLUNTARY CHOICE",\n'
    '    "FICTIONAL POLICE TROPE != OPERATIONAL POLICY",\n'
    '    "ONE AGENCY != A NATIONAL POLICING SYSTEM",\n'
    '    "ONE ENCOUNTER != SYSTEM-WIDE GROUND TRUTH",\n'
    '    "JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER",\n'
)
policing = replace_exact(
    policing,
    old_invariants,
    new_invariants,
    2,
    "policing invariant tuples",
)
policing = replace_once(
    policing,
    'def test_policing_source_gate_cannot_be_negated():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    clause = "register official and current sources for each Australian and United States jurisdictional claim"\n    mutated = roadmap.replace(clause, "never " + clause, 1)\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n',
    '''def test_policing_source_gate_cannot_be_negated():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    clause = "register official and current sources for each Australian and United States jurisdictional claim"\n    mutated = roadmap.replace(clause, "never " + clause, 1)\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n\n\n@pytest.mark.parametrize(\n    "clause",\n    (\n        "POLICE TERMINOLOGY != CROSS-JURISDICTION EQUIVALENCE",\n        "CALM TONE != ABSENCE OF COERCIVE AUTHORITY",\n        "POLITE WORDING != VOLUNTARY CHOICE",\n        "ONE AGENCY != A NATIONAL POLICING SYSTEM",\n        "ONE ENCOUNTER != SYSTEM-WIDE GROUND TRUTH",\n    ),\n)\ndef test_policing_scope_boundaries_are_all_required(clause: str):\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    assert clause in roadmap\n    mutated = roadmap.replace(clause, "REMOVED POLICING BOUNDARY", 1)\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n''',
    "policing boundary regressions",
)
policing_path.write_text(policing, encoding="utf-8")
