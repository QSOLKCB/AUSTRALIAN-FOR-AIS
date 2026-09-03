from pathlib import Path


def replace_exact(text: str, old: str, new: str, *, count: int = 1) -> str:
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"expected {count} occurrence(s), found {actual}: {old[:100]!r}")
    return text.replace(old, new, count)


registry_path = Path("tests/test_research_reference_registry.py")
registry = registry_path.read_text(encoding="utf-8")

registry = replace_exact(
    registry,
    '''STRONG_METADATA_FIELD_PATTERN = re.compile(\n    r"^(?P<marker>\\*\\*|__)(?P<label>[^:\\r\\n]+):(?P=marker)(?=$|[ \\t])"\n)''',
    '''STRONG_METADATA_FIELD_PATTERN = re.compile(\n    r"^(?P<outer>\\*\\*|__|\\*|_)(?P<inner>\\*\\*|__|\\*|_)"\n    r"(?P<label>[^:\\r\\n]+):(?P=inner)(?P=outer)(?=$|[ \\t])"\n)''',
)

registry = replace_exact(
    registry,
    '''        values = {key.lower(): (value or "") for key, value in attrs}\n        if "hidden" in values:\n            return True''',
    '''        values = {key.lower(): (value or "") for key, value in attrs}\n        # A closed HTML disclosure renders its descendants collapsed until the\n        # reader explicitly opens it. Governance text must be visible by default.\n        if tag == "details" and "open" not in values:\n            return True\n        if "hidden" in values:\n            return True''',
)

registry = replace_exact(
    registry,
    '''\n\ndef test_compound_container_fence_cannot_hide_scalar_metadata():''',
    '''\n\n@pytest.mark.parametrize(\n    ("opener", "closer"),\n    (\n        ("***", "***"),\n        ("___", "___"),\n        ("**_", "_**"),\n        ("__*", "*__"),\n        ("*__", "__*"),\n        ("_**", "**_"),\n    ),\n)\ndef test_nested_emphasis_doi_field_is_counted(opener: str, closer: str):\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*"\n    section = _registered_sections(corpus)[entry]\n    expected = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"\n    mutated = section.replace(\n        expected,\n        expected\n        + f"\\n\\n{opener}DOI:{closer} https://doi.org/10.0000/fabricated",\n        1,\n    )\n    with pytest.raises(AssertionError, match="exactly one mandatory field"):\n        _validate_registered_entry(entry, mutated)\n\n\ndef test_compound_container_fence_cannot_hide_scalar_metadata():''',
)

registry = replace_exact(
    registry,
    '''\n\ndef test_reference_style_source_destination_is_included_in_pinned_set():''',
    '''\n\ndef test_closed_details_cannot_hide_complete_governed_batch():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    start = corpus.index(BATCH_HEADING) + len(BATCH_HEADING)\n    end = corpus.index(BATCH_END, start)\n    mutated = (\n        corpus[:start]\n        + "\\n<details>\\n<summary>Governed references</summary>\\n"\n        + corpus[start:end]\n        + "\\n</details>\\n"\n        + corpus[end:]\n    )\n    with pytest.raises(AssertionError, match="registered post-Phase-2 batch contains no entries"):\n        _validate_registry_corpus(mutated)\n\n\ndef test_open_details_keep_governed_batch_visible():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    start = corpus.index(BATCH_HEADING) + len(BATCH_HEADING)\n    end = corpus.index(BATCH_END, start)\n    mutated = (\n        corpus[:start]\n        + "\\n<details open>\\n<summary>Governed references</summary>\\n"\n        + corpus[start:end]\n        + "\\n</details>\\n"\n        + corpus[end:]\n    )\n    _validate_registry_corpus(mutated)\n\n\ndef test_reference_style_source_destination_is_included_in_pinned_set():''',
)

registry_path.write_text(registry, encoding="utf-8")

roadmap_path = Path("ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
old_roadmap = (
    "This workstream is a **source-gated research proposal**, not an adopted description of either policing system and not legal advice. "
    "Before any benchmark family is implemented, the project must register current official Australian and United States sources covering the specific jurisdictions and topics being compared. "
    "Australian federal, state, and territory material must not be collapsed into one undifferentiated script; United States federal, state, county, municipal, sheriff, highway-patrol, and special-jurisdiction material must likewise not be treated as interchangeable. "
    "Every implemented item should record the relevant country, jurisdiction, institutional role, encounter type, and source date."
)
new_roadmap = (
    "This workstream is a **source-gated research proposal**, not an adopted description of either policing system and not legal advice. "
    "Before any benchmark family is implemented, the project must register current official Australian and United States sources covering the specific jurisdictions and topics being compared. "
    "Australian federal, state, and territory material must not be collapsed into one undifferentiated script; United States federal, state, county, municipal, sheriff, highway-patrol, and special-jurisdiction material must likewise not be treated as interchangeable.\n\n"
    "Every implemented item must record, at minimum, the relevant country, jurisdiction, agency or institutional role, encounter type, source date or version, registered source identifiers or links supporting any legal or procedural condition supplied to the model, and claim type."
)
roadmap = replace_exact(roadmap, old_roadmap, new_roadmap)
roadmap_path.write_text(roadmap, encoding="utf-8")

policing_path = Path("tests/test_policing_context_roadmap.py")
policing = policing_path.read_text(encoding="utf-8")
old_clause = (
    '    "Every implemented item should record the relevant country, jurisdiction, institutional role, encounter type, and source date.",'
)
new_clause = (
    '    "Every implemented item must record, at minimum, the relevant country, jurisdiction, agency or institutional role, encounter type, source date or version, registered source identifiers or links supporting any legal or procedural condition supplied to the model, and claim type.",'
)
policing = replace_exact(policing, old_clause, new_clause)

policing = replace_exact(
    policing,
    '''AFFIRMATIVE_LINE_PREFIX_CLAUSES = (\n    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",''',
    '''AFFIRMATIVE_LINE_PREFIX_CLAUSES = (\n    "Every implemented item must record, at minimum, the relevant country, jurisdiction, agency or institutional role, encounter type, source date or version, registered source identifiers or links supporting any legal or procedural condition supplied to the model, and claim type.",\n    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",''',
)

policing = replace_exact(
    policing,
    '''def test_policing_context_workstream_remains_source_gated_and_noncomparative():\n    _validate_policing_workstream(ROADMAP.read_text(encoding="utf-8"))\n''',
    '''def test_policing_context_workstream_remains_source_gated_and_noncomparative():\n    _validate_policing_workstream(ROADMAP.read_text(encoding="utf-8"))\n\n\ndef test_policing_item_metadata_contract_is_mandatory_and_complete():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    rendered = _rendered_policing_workstream(roadmap)\n    visible = _visible_text(rendered)\n    assert "Every implemented item should record" not in visible\n    assert (\n        "Every implemented item must record, at minimum, the relevant country, "\n        "jurisdiction, agency or institutional role, encounter type, source date or "\n        "version, registered source identifiers or links supporting any legal or "\n        "procedural condition supplied to the model, and claim type."\n    ) in visible\n''',
)

policing_path.write_text(policing, encoding="utf-8")
