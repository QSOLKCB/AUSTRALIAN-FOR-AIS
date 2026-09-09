from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICING = ROOT / "tests" / "test_policing_context_roadmap.py"
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"
REGRESSION = ROOT / "tests" / "test_pr4_native_machine_dialog_regressions.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one target snippet in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    POLICING,
    '''        if (\n            machine_metadata_attributes.intersection(attribute_names)\n            or "rel" in attribute_names\n        ):\n            self.violations.add("machine-metadata")\n''',
    '''        if (\n            machine_metadata_attributes.intersection(attribute_names)\n            or "rel" in attribute_names\n            or (tag == "data" and "value" in attribute_names)\n        ):\n            self.violations.add("machine-metadata")\n''',
)

replace_once(
    POLICING,
    '''    raw_block_tag = re.compile(\n        r"</?(?:address|article|aside|div|dl|fieldset|figcaption|figure|footer|header|main|nav|p|section|summary)\\b[^>]*>",\n        flags=re.IGNORECASE,\n    )\n    for raw_line in live_markup.splitlines():\n        if raw_block_tag.search(raw_line) is None:\n            continue\n        residual = raw_block_tag.sub("", raw_line)\n        if residual.strip():\n            parser.violations.add("raw-block")\n            break\n''',
    '''    raw_block_tag = re.compile(\n        r"</?(?:address|article|aside|div|dl|fieldset|figcaption|figure|footer|header|main|nav|p|section|summary)\\b[^>]*>",\n        flags=re.IGNORECASE,\n    )\n    dialog_tag = re.compile(r"</?dialog\\b[^>]*>", flags=re.IGNORECASE)\n    open_dialog_tag = re.compile(\n        r"<dialog\\b(?=[^>]*(?:\\sopen(?:\\s*=|\\s|/?>)))[^>]*>",\n        flags=re.IGNORECASE,\n    )\n    for raw_line in live_markup.splitlines():\n        if raw_block_tag.search(raw_line) is not None:\n            residual = raw_block_tag.sub("", raw_line)\n            if residual.strip():\n                parser.violations.add("raw-block")\n                break\n        if open_dialog_tag.search(raw_line) is not None:\n            residual = dialog_tag.sub("", raw_line)\n            if residual.strip():\n                parser.violations.add("dialog-inline-block")\n                break\n''',
)

replace_once(
    POLICING,
    '''        "rendered-break": "rendered break HTML",\n        "preformatted-content": "preformatted content HTML",\n''',
    '''        "rendered-break": "rendered break HTML",\n        "dialog-inline-block": "dialog block-container HTML carrying governed prose",\n        "preformatted-content": "preformatted content HTML",\n''',
)

replace_once(
    REGISTRY,
    '''    assert "machine-metadata" not in found, (\n        "machine-readable Microdata/RDFa metadata is not allowed in governed documents"\n    )\n    assert "preformatted-content" not in found, (\n''',
    '''    assert "machine-metadata" not in found, (\n        "machine-readable Microdata/RDFa metadata is not allowed in governed documents"\n    )\n    assert "dialog-inline-block" not in found, (\n        "dialog block-container HTML carrying governed prose is not allowed in governed documents"\n    )\n    assert "preformatted-content" not in found, (\n''',
)

REGRESSION.write_text('''"""Regressions for native machine values and dialog prose containers."""\n\nfrom pathlib import Path\nimport runpy\nimport pytest\n\nROOT = Path(__file__).parent.parent\nPOLICING = runpy.run_path(str(ROOT / "tests" / "test_policing_context_roadmap.py"))\nREGISTRY = runpy.run_path(str(ROOT / "tests" / "test_research_reference_registry.py"))\nCORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"\n\n\ndef test_native_data_value_is_machine_metadata() -> None:\n    fragment = '<data value="CC0">The film remains copyrighted.</data>'\n    assert "machine-metadata" in POLICING["_governed_surface_html_violations"](fragment)\n    corpus = CORPUS.read_text(encoding="utf-8")\n    mutated = corpus.replace("The film remains copyrighted.", fragment, 1)\n    with pytest.raises(AssertionError, match="machine-readable Microdata/RDFa metadata"):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_open_dialog_inside_governed_prose_is_rejected() -> None:\n    fragment = "Availability through ABC iview is <dialog open>not</dialog> permission to redistribute content."\n    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)\n    corpus = CORPUS.read_text(encoding="utf-8")\n    original = "Availability through ABC iview is not permission to redistribute content."\n    mutated = corpus.replace(original, fragment, 1)\n    with pytest.raises(AssertionError, match="dialog block-container HTML"):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_closed_dialog_keeps_existing_hidden_semantics() -> None:\n    fragment = "<dialog>Canonical governed prose.</dialog>"\n    assert "dialog-inline-block" not in POLICING["_governed_surface_html_violations"](fragment)\n\n\ndef test_whole_section_open_dialog_wrapper_remains_supported() -> None:\n    fragment = "<dialog open>\\nCanonical governed prose.\\n</dialog>\\n"\n    violations = POLICING["_governed_surface_html_violations"](fragment)\n    assert "dialog-inline-block" not in violations\n''', encoding="utf-8")
