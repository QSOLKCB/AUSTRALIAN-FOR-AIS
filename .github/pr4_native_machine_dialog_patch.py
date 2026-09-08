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
    'r"</?(?:address|article|aside|div|dl|fieldset|figcaption|figure|footer|header|main|nav|p|section|summary)\\b[^>]*>",',
    'r"</?(?:address|article|aside|dialog|div|dl|fieldset|figcaption|figure|footer|header|main|nav|p|section|summary)\\b[^>]*>",',
)

replace_once(
    POLICING,
    '''        "rendered-break": "rendered break HTML",\n        "preformatted-content": "preformatted content HTML",\n''',
    '''        "rendered-break": "rendered break HTML",\n        "raw-block": "raw block-container HTML",\n        "preformatted-content": "preformatted content HTML",\n''',
)

replace_once(
    REGISTRY,
    '''    assert "machine-metadata" not in found, (\n        "machine-readable Microdata/RDFa metadata is not allowed in governed documents"\n    )\n    assert "preformatted-content" not in found, (\n''',
    '''    assert "machine-metadata" not in found, (\n        "machine-readable metadata is not allowed in governed documents"\n    )\n    assert "raw-block" not in found, (\n        "raw block-container HTML carrying governed prose is not allowed in governed documents"\n    )\n    assert "preformatted-content" not in found, (\n''',
)

REGRESSION.write_text('''"""Regressions for native machine values and dialog prose containers."""\n\nfrom pathlib import Path\nimport runpy\nimport pytest\n\nROOT = Path(__file__).parent.parent\nPOLICING = runpy.run_path(str(ROOT / "tests" / "test_policing_context_roadmap.py"))\nREGISTRY = runpy.run_path(str(ROOT / "tests" / "test_research_reference_registry.py"))\nCORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"\n\n\ndef test_native_data_value_is_machine_metadata() -> None:\n    fragment = '<data value="CC0">The film remains copyrighted.</data>'\n    assert "machine-metadata" in POLICING["_governed_surface_html_violations"](fragment)\n    corpus = CORPUS.read_text(encoding="utf-8")\n    mutated = corpus.replace("The film remains copyrighted.", fragment, 1)\n    with pytest.raises(AssertionError, match="machine-readable metadata"):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_open_dialog_inside_governed_prose_is_rejected() -> None:\n    fragment = "Availability through ABC iview is <dialog open>not</dialog> permission to redistribute content."\n    assert "raw-block" in POLICING["_governed_surface_html_violations"](fragment)\n    corpus = CORPUS.read_text(encoding="utf-8")\n    original = "Availability through ABC iview is not permission to redistribute content."\n    mutated = corpus.replace(original, fragment, 1)\n    with pytest.raises(AssertionError, match="raw block-container HTML"):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_whole_section_open_dialog_wrapper_remains_supported() -> None:\n    fragment = "<dialog open>\\nCanonical governed prose.\\n</dialog>\\n"\n    assert "raw-block" not in POLICING["_governed_surface_html_violations"](fragment)\n''', encoding="utf-8")
