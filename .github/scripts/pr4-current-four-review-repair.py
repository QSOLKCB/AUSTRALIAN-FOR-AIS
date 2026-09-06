from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"
PHASE2 = ROOT / "tests" / "test_phase2_review_followup.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def normalize_eof(text: str) -> str:
    return text.rstrip("\n") + "\n"


registry = REGISTRY.read_text(encoding="utf-8")

registry = replace_once(
    registry,
    '''GOVERNED_REPLACEMENT_HTML_PATTERN = re.compile(\n    r"<(?:object|embed|iframe)\\b",\n    flags=re.IGNORECASE,\n)''',
    '''GOVERNED_REPLACEMENT_HTML_PATTERN = re.compile(\n    r"<(?:object|embed|iframe|canvas)\\b",\n    flags=re.IGNORECASE,\n)''',
    "replacement-content tag set",
)

registry = replace_once(
    registry,
    '''        if name not in {"display", "visibility"}:\n            continue''',
    '''        if name not in {"display", "visibility", "opacity"}:\n            continue''',
    "CSS visual property set",
)

registry = replace_once(
    registry,
    '''    display = winners.get("display", (False, ""))[1]\n    visibility = winners.get("visibility", (False, ""))[1]\n    return display == "none" or visibility in {"hidden", "collapse"}''',
    '''    display = winners.get("display", (False, ""))[1]\n    visibility = winners.get("visibility", (False, ""))[1]\n    opacity = winners.get("opacity", (False, ""))[1]\n    opacity_hidden = False\n    if opacity:\n        numeric_opacity = opacity[:-1].strip() if opacity.endswith("%") else opacity\n        try:\n            opacity_hidden = float(numeric_opacity) <= 0.0\n        except ValueError:\n            opacity_hidden = False\n    return (\n        display == "none"\n        or visibility in {"hidden", "collapse"}\n        or opacity_hidden\n    )''',
    "CSS visibility result",
)

registry = replace_once(
    registry,
    '''def _contains_visually_hidden_table(text: str) -> bool:\n    detector = _VisuallyHiddenTableDetector()\n    try:\n        detector.feed(text)\n        detector.close()\n    except Exception:\n        return True\n    return detector.found\n\n\nHTML_VOID_TAGS = {''',
    '''def _contains_visually_hidden_table(text: str) -> bool:\n    detector = _VisuallyHiddenTableDetector()\n    try:\n        detector.feed(text)\n        detector.close()\n    except Exception:\n        return True\n    return detector.found\n\n\nclass _InertHTMLDetector(HTMLParser):\n    """Detect inert HTML containers without treating their visible text as hidden."""\n\n    def __init__(self) -> None:\n        super().__init__(convert_charrefs=True)\n        self.found = False\n\n    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        if any(key.lower() == "inert" for key, _ in attrs):\n            self.found = True\n\n    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        self.handle_starttag(tag, attrs)\n\n\ndef _contains_inert_html(text: str) -> bool:\n    detector = _InertHTMLDetector()\n    try:\n        detector.feed(text)\n        detector.close()\n    except Exception:\n        return True\n    return detector.found\n\n\nHTML_VOID_TAGS = {''',
    "inert HTML detector",
)

registry = replace_once(
    registry,
    '''    assert destinations, f"{entry} has no usable HTTPS destination in its registered-source field"\n    assert _visible_inline_text(source_value), f"{entry} has an empty registered-source field"''',
    '''    assert destinations, f"{entry} has no usable HTTPS destination in its registered-source field"\n    assert not _contains_inert_html(_structural_registry_text(source_value)), (\n        f"{entry} registered-source field contains inert HTML; provenance links must "\n        "remain interactive"\n    )\n    assert _visible_inline_text(source_value), f"{entry} has an empty registered-source field"''',
    "registered-source inert guard",
)

registry = replace_once(
    registry,
    '''        f"{entry} contains replacement-content HTML (object/embed/iframe), which is "''',
    '''        f"{entry} contains replacement-content HTML (object/embed/iframe/canvas), which is "''',
    "replacement-content error text",
)

append_registry_tests = r'''


def test_inert_markdown_registered_link_is_rejected_fail_closed():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(
        heading for heading in EXPECTED_GOVERNED_ENTRIES
        if heading.startswith("### Hurley (2025)")
    )
    section = _registered_sections(corpus)[entry]
    source = str(ENTRY_CONTRACTS[entry][SOURCES_KEY][0])
    original = f"**Registered source:** {source}"
    replacement = (
        f'**Registered source:** <span inert>[{source}]({source})</span>'
    )
    assert original in section
    mutated_section = section.replace(original, replacement, 1)
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="contains inert HTML"):
        _validate_registry_corpus(mutated)


def test_opacity_zero_cannot_hide_pinned_visible_clause():
    assert _css_hides_element("opacity:0")
    assert _css_hides_element("opacity:0%")
    assert not _css_hides_element("opacity:0; opacity:1")
    assert _css_hides_element("opacity:0 !important; opacity:1")

    mutated = _mutate_chey_phrase(
        '<span style="opacity:0">The article</span>'
    )
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_canvas_fallback_is_rejected_fail_closed():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(
        heading for heading in EXPECTED_GOVERNED_ENTRIES
        if heading.startswith("### Hurley (2025)")
    )
    section = _registered_sections(corpus)[entry]
    source = str(ENTRY_CONTRACTS[entry][SOURCES_KEY][0])
    original = f"**Registered source:** {source}"
    replacement = (
        f'**Registered source:** <canvas><a href="{source}">{source}</a></canvas>'
    )
    assert original in section
    mutated_section = section.replace(original, replacement, 1)
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="replacement-content HTML"):
        _validate_registry_corpus(mutated)
'''

if "def test_inert_markdown_registered_link_is_rejected_fail_closed():" in registry:
    raise RuntimeError("registry regression sentinel already exists")
registry = normalize_eof(registry) + append_registry_tests.lstrip("\n")
REGISTRY.write_text(normalize_eof(registry), encoding="utf-8")

phase2 = PHASE2.read_text(encoding="utf-8")
phase2 = replace_once(
    phase2,
    '''import json\nimport pathlib''',
    '''import json\nimport pathlib\nimport runpy''',
    "phase2 runpy import",
)

phase2 = replace_once(
    phase2,
    '''CHANGELOG = REPO_ROOT / "CHANGELOG.md"\n''',
    '''CHANGELOG = REPO_ROOT / "CHANGELOG.md"\nPOLICING_TEST = REPO_ROOT / "tests" / "test_policing_context_roadmap.py"\nPHASE2_HEADING = "## [Unreleased] — Phase 2 Pilot Human Annotation"\nPHASE1_HEADING = "## [Unreleased] — Phase 1 Research Substrate"\nPHASE2_NOTES_HEADING = "### Notes"\nFREE_TEXT_IAA_BOUNDARY = (\n    "Free-text pragmatic interpretations remain qualitative evidence and are not "\n    "assigned a misleading exact-string IAA score."\n)\n''',
    "phase2 changelog constants",
)

old_test = '''def test_phase2_changelog_keeps_free_text_iaa_boundary():\n    changelog = CHANGELOG.read_text(encoding="utf-8")\n    assert (\n        "Free-text pragmatic interpretations remain qualitative evidence and are not "\n        "assigned a misleading exact-string IAA score."\n    ) in changelog\n'''
new_test = '''def _visible_phase2_notes(changelog: str) -> str:\n    namespace = runpy.run_path(str(POLICING_TEST))\n    structure = namespace["_rendered_structure"](changelog)\n    phase2_start, _ = namespace["_visible_markdown_heading_span"](\n        structure, PHASE2_HEADING\n    )\n    phase1_start, _ = namespace["_visible_markdown_heading_span"](\n        structure, PHASE1_HEADING\n    )\n    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"\n\n    phase2_structure = structure[phase2_start:phase1_start]\n    notes_start, _ = namespace["_visible_markdown_heading_span"](\n        phase2_structure, PHASE2_NOTES_HEADING\n    )\n    absolute_notes_start = phase2_start + notes_start\n    return namespace["_visible_text"](\n        changelog[absolute_notes_start:phase1_start]\n    )\n\n\ndef test_phase2_changelog_keeps_free_text_iaa_boundary():\n    changelog = CHANGELOG.read_text(encoding="utf-8")\n    assert FREE_TEXT_IAA_BOUNDARY in _visible_phase2_notes(changelog)\n\n\ndef test_phase2_changelog_iaa_boundary_is_visible_and_section_scoped():\n    changelog = CHANGELOG.read_text(encoding="utf-8")\n    bullet = f"- {FREE_TEXT_IAA_BOUNDARY}\\n"\n    assert bullet in changelog\n\n    commented = changelog.replace(\n        bullet,\n        f"- <!-- {FREE_TEXT_IAA_BOUNDARY} -->\\n",\n        1,\n    )\n    assert FREE_TEXT_IAA_BOUNDARY not in _visible_phase2_notes(commented)\n\n    moved = changelog.replace(bullet, "", 1).replace(\n        PHASE1_HEADING,\n        PHASE1_HEADING + f"\\n\\n- {FREE_TEXT_IAA_BOUNDARY}",\n        1,\n    )\n    assert FREE_TEXT_IAA_BOUNDARY not in _visible_phase2_notes(moved)\n'''
phase2 = replace_once(phase2, old_test, new_test, "phase2 IAA receipt")
PHASE2.write_text(normalize_eof(phase2), encoding="utf-8")

print("patched:")
print(REGISTRY.relative_to(ROOT))
print(PHASE2.relative_to(ROOT))
