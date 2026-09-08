from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"
ROADMAP = ROOT / "tests" / "test_policing_context_roadmap.py"
REGRESSION = ROOT / "tests" / "test_pr4_latest_codex_regressions.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one replacement in {path}: found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) Reject reader-visible CommonMark two-space hard breaks before the ordinary
# whitespace fold can erase the distinction. The structural view already masks
# comments, fenced code, and inline code spans, so inert examples remain inert.
replace_once(
    REGISTRY,
    '''def _visible_inline_text(text: str) -> str:\n    """Reduce Markdown/HTML metadata to browser-visible text only."""\n    rendered = _rendered_registry_text(text)\n    visible = _mask_link_reference_definitions_for_visibility(rendered)\n''',
    '''def _visible_inline_text(text: str) -> str:\n    """Reduce Markdown/HTML metadata to browser-visible text only."""\n    structural = _structural_registry_text(text)\n    if re.search(r"(?<=\\S) {2,}(?:\\r\\n|\\r|\\n)", structural):\n        raise AssertionError(\n            "Markdown hard line breaks are not allowed in governed registry receipts"\n        )\n    rendered = _rendered_registry_text(text)\n    visible = _mask_link_reference_definitions_for_visibility(rendered)\n''',
)

# 2) Language metadata changes assistive pronunciation without changing the
# character-data seal. Make it a first-class shared violation and ensure the
# registry's corpus-wide gate consumes it.
replace_once(
    REGISTRY,
    '''    "accessible-name",\n    "accessibility-hidden",\n''',
    '''    "accessible-name",\n    "language-override",\n    "accessibility-hidden",\n''',
)

# 3) Nested/single <small> presentation can recursively shrink mandatory prose.
replace_once(
    ROADMAP,
    '''        if tag in {"font", "basefont"}:\n            self.violations.add("presentational-font")\n''',
    '''        if tag in {"font", "basefont", "small"}:\n            self.violations.add("presentational-font")\n''',
)

replace_once(
    ROADMAP,
    '''        if "title" in attribute_names:\n            self.violations.add("tooltip-title")\n        if {"aria-label", "aria-labelledby", "aria-description", "aria-describedby", "aria-details"}.intersection(attribute_names):\n''',
    '''        if "title" in attribute_names:\n            self.violations.add("tooltip-title")\n        if {"lang", "xml:lang"}.intersection(attribute_names):\n            self.violations.add("language-override")\n        if {"aria-label", "aria-labelledby", "aria-description", "aria-describedby", "aria-details"}.intersection(attribute_names):\n''',
)

replace_once(
    ROADMAP,
    '''        "presentational-font": "legacy presentational font HTML",\n        "accessible-name": "accessible-name override HTML",\n''',
    '''        "presentational-font": "presentational font-size HTML",\n        "language-override": "language override HTML",\n        "accessible-name": "accessible-name override HTML",\n''',
)

REGRESSION.write_text(
    '''"""Exact regressions for the latest Codex findings on PR #4."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nimport runpy\n\nimport pytest\n\n\nROOT = Path(__file__).resolve().parent.parent\nREGISTRY = runpy.run_path(str(ROOT / "tests" / "test_research_reference_registry.py"))\nCORPUS = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")\n\nBLACK_COMEDY_RIGHTS = (\n    "Availability through ABC iview is not permission to redistribute content."\n)\n\n\ndef test_registry_receipt_rejects_space_markdown_hard_line_break() -> None:\n    mutated = CORPUS.replace(\n        BLACK_COMEDY_RIGHTS,\n        "Availability through ABC iview is  \\nnot permission to redistribute content.",\n        1,\n    )\n    assert mutated != CORPUS\n    with pytest.raises(AssertionError, match="hard line breaks"):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_registry_backslash_hard_break_already_changes_receipt() -> None:\n    mutated = CORPUS.replace(\n        BLACK_COMEDY_RIGHTS,\n        "Availability through ABC iview is\\\\\\nnot permission to redistribute content.",\n        1,\n    )\n    assert mutated != CORPUS\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_registry_rejects_nested_small_presentation() -> None:\n    wrapped = "<small>" * 12 + BLACK_COMEDY_RIGHTS + "</small>" * 12\n    mutated = CORPUS.replace(BLACK_COMEDY_RIGHTS, wrapped, 1)\n    assert mutated != CORPUS\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\n@pytest.mark.parametrize("attribute", ['lang="ja"', 'xml:lang="ja"'])\ndef test_registry_rejects_language_overrides(attribute: str) -> None:\n    wrapped = f"<span {attribute}>{BLACK_COMEDY_RIGHTS}</span>"\n    mutated = CORPUS.replace(BLACK_COMEDY_RIGHTS, wrapped, 1)\n    assert mutated != CORPUS\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](mutated)\n''',
    encoding="utf-8",
)
