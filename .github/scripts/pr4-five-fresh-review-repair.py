from __future__ import annotations

import hashlib
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"
POLICING = ROOT / "tests" / "test_policing_context_roadmap.py"
WORKSTREAM_H = ROOT / "tests" / "test_workstream_h_methodology.py"
POLICING_RECEIPT = ROOT / "tests" / "test_policing_contract_receipt.py"
ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


CASCADE_OLD = '''def _css_hides_element(style: str) -> bool:
    """Interpret actual display/visibility declarations, not substrings in values."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        name = name.strip()
        value = re.sub(r"\\s*!important\\s*$", "", value.strip())
        if name == "display" and value == "none":
            return True
        if name == "visibility" and value in {"hidden", "collapse"}:
            return True
    return False
'''

CASCADE_NEW = '''def _css_hides_element(style: str) -> bool:
    """Apply inline CSS declaration order and !important precedence."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())
    winners: dict[str, tuple[bool, str]] = {}
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        name, raw_value = declaration.split(":", 1)
        name = name.strip()
        if name not in {"display", "visibility"}:
            continue
        raw_value = raw_value.strip()
        important = re.search(r"\\s*!important\\s*$", raw_value) is not None
        value = re.sub(r"\\s*!important\\s*$", "", raw_value).strip()
        previous = winners.get(name)
        if previous is None or (important and not previous[0]) or important == previous[0]:
            winners[name] = (important, value)

    display = winners.get("display", (False, ""))[1]
    visibility = winners.get("visibility", (False, ""))[1]
    return display == "none" or visibility in {"hidden", "collapse"}
'''

ARIA_HIDDEN = '''        if values.get("aria-hidden", "").strip().lower() == "true":
            return True
'''


# Registry parser: CSS cascade, visual ARIA semantics, and fail-closed hidden tables.
registry = REGISTRY.read_text(encoding="utf-8")
registry = replace_once(registry, CASCADE_OLD, CASCADE_NEW, label="registry CSS cascade")
registry = replace_once(registry, ARIA_HIDDEN, "", label="registry aria-hidden visual semantics")

registry_table_anchor = '''def _visible_html_links(text: str) -> tuple[str, ...]:
    """Return navigable href values from browser-visible raw HTML anchors."""
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ()
    return tuple(parser.hrefs)


HTML_VOID_TAGS = {
'''
registry_table_replacement = '''def _visible_html_links(text: str) -> tuple[str, ...]:
    """Return navigable href values from browser-visible raw HTML anchors."""
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ()
    return tuple(parser.hrefs)


class _VisuallyHiddenTableDetector(HTMLParser):
    """Detect hidden raw tables whose HTML5 foster-parenting semantics are ambiguous here."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.found = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "table" and _VisibleHTMLTextParser._is_hidden(tag, attrs):
            self.found = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _contains_visually_hidden_table(text: str) -> bool:
    detector = _VisuallyHiddenTableDetector()
    try:
        detector.feed(text)
        detector.close()
    except Exception:
        return True
    return detector.found


HTML_VOID_TAGS = {
'''
registry = replace_once(
    registry,
    registry_table_anchor,
    registry_table_replacement,
    label="registry hidden-table detector",
)

registry_integrity_anchor = '''    rendered_section = _rendered_registry_text(section)
    assert GOVERNED_INTERACTIVE_HTML_PATTERN.search(rendered_section) is None, (
        f"{entry} contains interactive HTML that is not permitted in governed entries"
    )
'''
registry_integrity_replacement = '''    rendered_section = _rendered_registry_text(section)
    structural_section = _structural_registry_text(section)
    assert not _contains_visually_hidden_table(structural_section), (
        f"{entry} contains a visually hidden raw HTML table; governed entries reject "
        "this construct because HTML5 foster parenting can render descendants outside "
        "the table's visual-hiding boundary"
    )
    assert GOVERNED_INTERACTIVE_HTML_PATTERN.search(rendered_section) is None, (
        f"{entry} contains interactive HTML that is not permitted in governed entries"
    )
'''
registry = replace_once(
    registry,
    registry_integrity_anchor,
    registry_integrity_replacement,
    label="registry hidden-table integrity guard",
)

registry_tests = r'''


def test_css_cascade_uses_winning_visual_declaration():
    assert not _css_hides_element("display:none; display:inline")
    assert _css_hides_element("display:none !important; display:inline")
    assert not _css_hides_element("display:none; display:inline !important")
    assert not _css_hides_element("visibility:hidden; visibility:visible")

    corpus = CORPUS.read_text(encoding="utf-8")
    heading = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    payload = (
        '<span style="display:none; display:inline"><strong>DOI:</strong> '
        'https://doi.org/10.0000/fabricated</span>'
    )
    mutated = corpus.replace(heading, heading + "\n\n" + payload, 1)
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_aria_hidden_does_not_hide_visually_rendered_duplicate_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    payload = (
        '<span aria-hidden="true"><strong>DOI:</strong> '
        'https://doi.org/10.0000/fabricated</span>'
    )
    mutated = corpus.replace(heading, heading + "\n\n" + payload, 1)
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_hidden_table_foster_parenting_is_rejected_fail_closed():
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    payload = (
        '<table hidden><p><strong>DOI:</strong> '
        'https://doi.org/10.0000/fabricated</p></table>'
    )
    mutated = corpus.replace(heading, heading + "\n\n" + payload, 1)
    with pytest.raises(AssertionError, match="visually hidden raw HTML table"):
        _validate_registry_corpus(mutated)
'''
if "def test_css_cascade_uses_winning_visual_declaration" in registry:
    raise SystemExit("registry fresh-review regressions already present")
registry = registry.rstrip() + registry_tests + "\n"
REGISTRY.write_text(registry, encoding="utf-8")


# Canonical policing reducer: keep CSS/ARIA visual semantics aligned with registry.
policing = POLICING.read_text(encoding="utf-8")
policing = replace_once(policing, CASCADE_OLD, CASCADE_NEW, label="policing CSS cascade")
policing = replace_once(policing, ARIA_HIDDEN, "", label="policing aria-hidden visual semantics")
POLICING.write_text(policing, encoding="utf-8")


# Workstream H: align local visual parser and add a complete visible-section seal.
workstream_h = WORKSTREAM_H.read_text(encoding="utf-8")
workstream_h = replace_once(
    workstream_h,
    "from pathlib import Path\n",
    "from pathlib import Path\nimport hashlib\n",
    label="Workstream H hashlib import",
)
workstream_h = replace_once(
    workstream_h,
    'POLICING_METHODOLOGY_HEADING = "## Australian and United States Policing-Context Experiment Design"\n',
    'POLICING_METHODOLOGY_HEADING = "## Australian and United States Policing-Context Experiment Design"\nWORKSTREAM_H_VISIBLE_SHA256 = "__WORKSTREAM_H_VISIBLE_SHA256__"\n',
    label="Workstream H integrity constant",
)
workstream_h = replace_once(
    workstream_h,
    'SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})\n\n\nclass _VisibleHTMLTextParser',
    'SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})\nCSS_COMMENT_PATTERN = re.compile(r"/\\*.*?\\*/", flags=re.DOTALL)\n\n\ndef _css_hides_element(style: str) -> bool:\n    """Apply inline CSS declaration order and !important precedence."""\n    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())\n    winners: dict[str, tuple[bool, str]] = {}\n    for declaration in cleaned.split(";"):\n        if ":" not in declaration:\n            continue\n        name, raw_value = declaration.split(":", 1)\n        name = name.strip()\n        if name not in {"display", "visibility"}:\n            continue\n        raw_value = raw_value.strip()\n        important = re.search(r"\\s*!important\\s*$", raw_value) is not None\n        value = re.sub(r"\\s*!important\\s*$", "", raw_value).strip()\n        previous = winners.get(name)\n        if previous is None or (important and not previous[0]) or important == previous[0]:\n            winners[name] = (important, value)\n    display = winners.get("display", (False, ""))[1]\n    visibility = winners.get("visibility", (False, ""))[1]\n    return display == "none" or visibility in {"hidden", "collapse"}\n\n\nclass _VisibleHTMLTextParser',
    label="Workstream H CSS helper",
)
workstream_h = replace_once(
    workstream_h,
    ARIA_HIDDEN,
    "",
    label="Workstream H aria-hidden visual semantics",
)
old_h_style = '''        style = re.sub(
            r"/\\*.*?\\*/",
            "",
            values.get("style", "").lower(),
            flags=re.DOTALL,
        )
        style = re.sub(r"\\s+", "", style)
        return "display:none" in style or "visibility:hidden" in style
'''
workstream_h = replace_once(
    workstream_h,
    old_h_style,
    '        return _css_hides_element(values.get("style", ""))\n',
    label="Workstream H CSS use",
)

h_integrity_anchor = '''def _workstream_h(text: str) -> str:
    start, _ = _rendered_heading_span(text, WORKSTREAM_H_HEADING)
    end, _ = _rendered_heading_span(text, WORKSTREAM_I_HEADING)
    assert start < end, "rendered Workstream H boundary is invalid"
    return _visible_markdown_text(text[start:end])


'''
h_integrity_replacement = '''def _workstream_h(text: str) -> str:
    start, _ = _rendered_heading_span(text, WORKSTREAM_H_HEADING)
    end, _ = _rendered_heading_span(text, WORKSTREAM_I_HEADING)
    assert start < end, "rendered Workstream H boundary is invalid"
    return _visible_markdown_text(text[start:end])


def _normalised_workstream_h_visible_value(text: str) -> str:
    return " ".join(_workstream_h(text).split())


def _assert_workstream_h_integrity(text: str) -> str:
    section = _workstream_h(text)
    value = " ".join(section.split())
    actual_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
    assert actual_hash == WORKSTREAM_H_VISIBLE_SHA256, (
        "browser-visible Workstream H changed: expected hash "
        f"{WORKSTREAM_H_VISIBLE_SHA256!r}, got {actual_hash!r}"
    )
    return section


'''
workstream_h = replace_once(
    workstream_h,
    h_integrity_anchor,
    h_integrity_replacement,
    label="Workstream H complete-section integrity helper",
)
workstream_h = replace_once(
    workstream_h,
    '    section = _workstream_h(ROADMAP.read_text(encoding="utf-8"))\n',
    '    section = _assert_workstream_h_integrity(ROADMAP.read_text(encoding="utf-8"))\n',
    label="Workstream H primary receipt integrity call",
)

h_tests = r'''


def test_workstream_h_companion_identity_contradiction_changes_section_seal():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_H_HEADING)
    end = roadmap.index(WORKSTREAM_I_HEADING, start)
    insertion = "\n- Nationality and first-language identity should define the comparison cohorts.\n"
    mutated = roadmap[:end] + insertion + roadmap[end:]
    with pytest.raises(AssertionError, match="browser-visible Workstream H changed"):
        _assert_workstream_h_integrity(mutated)


def test_aria_hidden_remains_visually_visible_to_workstream_h_reducer():
    clause = "nationality and first-language identity must not define the comparison cohorts"
    rendered = _visible_markdown_text(f'<span aria-hidden="true">{clause}</span>')
    assert clause in rendered
'''
# pytest is not currently imported in this file; add it with the new mutation receipt.
workstream_h = replace_once(
    workstream_h,
    "import runpy\n\n\nROOT",
    "import runpy\n\nimport pytest\n\n\nROOT",
    label="Workstream H pytest import",
)
if "test_workstream_h_companion_identity_contradiction_changes_section_seal" in workstream_h:
    raise SystemExit("Workstream H fresh-review regressions already present")
workstream_h = workstream_h.rstrip() + h_tests + "\n"
WORKSTREAM_H.write_text(workstream_h, encoding="utf-8")


# Canonical policing methodology: complete browser-visible section seal.
receipt = POLICING_RECEIPT.read_text(encoding="utf-8")
receipt = replace_once(
    receipt,
    "import ast\n",
    "import ast\nimport hashlib\n",
    label="policing receipt hashlib import",
)
receipt = replace_once(
    receipt,
    'POLICING_METHODOLOGY_END_HEADING = "## Scoring Philosophy"\n',
    'POLICING_METHODOLOGY_END_HEADING = "## Scoring Philosophy"\nPOLICING_METHODOLOGY_VISIBLE_SHA256 = "__POLICING_METHODOLOGY_VISIBLE_SHA256__"\n',
    label="policing methodology integrity constant",
)
receipt_integrity_anchor = '''def _visible_policing_methodology(methodology: str) -> str:
    policing_namespace = runpy.run_path(str(POLICING_TEST))
    visible_text = policing_namespace["_visible_text"]
    return visible_text(_policing_methodology_section(methodology))


'''
receipt_integrity_replacement = '''def _visible_policing_methodology(methodology: str) -> str:
    policing_namespace = runpy.run_path(str(POLICING_TEST))
    visible_text = policing_namespace["_visible_text"]
    return visible_text(_policing_methodology_section(methodology))


def _normalised_visible_policing_methodology(methodology: str) -> str:
    return " ".join(_visible_policing_methodology(methodology).split())


def _assert_canonical_policing_integrity(methodology: str) -> None:
    value = _normalised_visible_policing_methodology(methodology)
    actual_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
    assert actual_hash == POLICING_METHODOLOGY_VISIBLE_SHA256, (
        "browser-visible canonical policing methodology changed: expected hash "
        f"{POLICING_METHODOLOGY_VISIBLE_SHA256!r}, got {actual_hash!r}"
    )


'''
receipt = replace_once(
    receipt,
    receipt_integrity_anchor,
    receipt_integrity_replacement,
    label="policing methodology integrity helper",
)
receipt = replace_once(
    receipt,
    '''def _assert_canonical_policing_metadata(methodology: str) -> None:
    rendered = _visible_policing_methodology(methodology)
''',
    '''def _assert_canonical_policing_metadata(methodology: str) -> None:
    _assert_canonical_policing_integrity(methodology)
    rendered = _visible_policing_methodology(methodology)
''',
    label="policing metadata complete-section seal",
)
receipt = replace_once(
    receipt,
    '''def _assert_canonical_high_stakes_gate(methodology: str) -> None:
    rendered = _visible_policing_methodology(methodology)
''',
    '''def _assert_canonical_high_stakes_gate(methodology: str) -> None:
    _assert_canonical_policing_integrity(methodology)
    rendered = _visible_policing_methodology(methodology)
''',
    label="high-stakes complete-section seal",
)
receipt_tests = r'''


def test_canonical_policing_methodology_rejects_companion_high_stakes_reversal():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    section = _policing_methodology_section(methodology)
    mutated_section = (
        section.rstrip()
        + "\n\nExpert review may be skipped even for coercion and legal-rights families.\n\n"
    )
    mutated = methodology.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="browser-visible canonical policing methodology changed"):
        _assert_canonical_high_stakes_gate(mutated)
'''
if "test_canonical_policing_methodology_rejects_companion_high_stakes_reversal" in receipt:
    raise SystemExit("policing receipt fresh-review regression already present")
receipt = receipt.rstrip() + receipt_tests + "\n"
POLICING_RECEIPT.write_text(receipt, encoding="utf-8")


# Seed committed integrity constants from the canonical current documents using the same
# normalization helpers that runtime validation uses.
h_namespace = runpy.run_path(str(WORKSTREAM_H))
h_value = h_namespace["_normalised_workstream_h_visible_value"](
    ROADMAP.read_text(encoding="utf-8")
)
h_digest = hashlib.sha256(h_value.encode("utf-8")).hexdigest()
h_text = WORKSTREAM_H.read_text(encoding="utf-8")
h_text = replace_once(
    h_text,
    "__WORKSTREAM_H_VISIBLE_SHA256__",
    h_digest,
    label="seed Workstream H visible hash",
)
WORKSTREAM_H.write_text(h_text, encoding="utf-8")

receipt_namespace = runpy.run_path(str(POLICING_RECEIPT))
receipt_value = receipt_namespace["_normalised_visible_policing_methodology"](
    METHODOLOGY.read_text(encoding="utf-8")
)
receipt_digest = hashlib.sha256(receipt_value.encode("utf-8")).hexdigest()
receipt_text = POLICING_RECEIPT.read_text(encoding="utf-8")
receipt_text = replace_once(
    receipt_text,
    "__POLICING_METHODOLOGY_VISIBLE_SHA256__",
    receipt_digest,
    label="seed canonical policing methodology visible hash",
)
POLICING_RECEIPT.write_text(receipt_text, encoding="utf-8")

print("Applied five-fresh-review repair")
print(f"Workstream H visible SHA-256: {h_digest}")
print(f"Canonical policing methodology visible SHA-256: {receipt_digest}")
