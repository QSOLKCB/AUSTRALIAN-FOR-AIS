from __future__ import annotations

import hashlib
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
POLICING = ROOT / "tests" / "test_policing_context_roadmap.py"
PHASE2 = ROOT / "tests" / "test_phase2_review_followup.py"
REGRESSIONS = ROOT / "tests" / "test_pr4_current_review_regressions.py"
CHANGELOG = ROOT / "CHANGELOG.md"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one replacement in {path}: found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    POLICING,
    '''    descriptions = {\n        "replacement-content": "replacement-content HTML",\n        "raw-svg": "raw SVG HTML",\n''',
    '''    descriptions = {\n        "replacement-content": "replacement-content HTML",\n        "preformatted-content": "preformatted content HTML",\n        "semantic-role": "semantic role override HTML",\n        "raw-svg": "raw SVG HTML",\n''',
)

phase2_marker = "test_complete_phase2_changelog_section_is_pinned"
phase2_text = PHASE2.read_text(encoding="utf-8")
if phase2_marker in phase2_text:
    raise SystemExit("Phase 2 full-section receipt already present")
phase2_text += r'''


EXPECTED_VISIBLE_PHASE2_SECTION_SHA256 = "__PHASE2_SHA256__"


def _visible_phase2_section(changelog: str) -> str:
    """Return the complete browser-visible Phase 2 changelog section."""
    namespace = runpy.run_path(str(POLICING_TEST))
    structure = namespace["_rendered_structure"](changelog)
    phase2_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE2_HEADING
    )
    phase1_start, _ = namespace["_visible_markdown_heading_span"](
        structure, PHASE1_HEADING
    )
    assert phase2_start < phase1_start, "Phase 2 changelog boundaries are out of order"
    return namespace["_visible_text"](changelog[phase2_start:phase1_start])


def _phase2_section_sha256(changelog: str) -> str:
    import hashlib

    return hashlib.sha256(_visible_phase2_section(changelog).encode("utf-8")).hexdigest()


def test_complete_phase2_changelog_section_is_pinned():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert _phase2_section_sha256(changelog) == EXPECTED_VISIBLE_PHASE2_SECTION_SHA256


def test_phase2_section_seal_catches_sibling_empirical_claims():
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert _visible_phase2_notes(changelog) == EXPECTED_VISIBLE_PHASE2_NOTES
    claims = (
        "Three human annotators completed the Phase 2 pilot.",
        "The completed Phase 2 study received ethical-review approval.",
        "Three human annotators achieved 100% exact-string IAA.",
    )
    for claim in claims:
        sibling = (
            "### Fabricated Phase 2 results\n\n"
            f"- {claim}\n\n"
            + PHASE2_NOTES_HEADING
        )
        mutated = changelog.replace(PHASE2_NOTES_HEADING, sibling, 1)
        assert mutated != changelog
        # The existing Notes-only receipt remains unchanged, which is the gap
        # this complete-section seal is intended to close.
        assert _visible_phase2_notes(mutated) == EXPECTED_VISIBLE_PHASE2_NOTES
        assert _phase2_section_sha256(mutated) != EXPECTED_VISIBLE_PHASE2_SECTION_SHA256
'''
PHASE2.write_text(phase2_text, encoding="utf-8")

# Compute the immutable fixture from the canonical repository changelog using
# the same browser-visible reducer that the test will enforce.
phase2_namespace = runpy.run_path(str(PHASE2))
canonical = CHANGELOG.read_text(encoding="utf-8")
digest = hashlib.sha256(
    phase2_namespace["_visible_phase2_section"](canonical).encode("utf-8")
).hexdigest()
replace_once(PHASE2, "__PHASE2_SHA256__", digest)

regression_marker = "test_shared_methodology_rejects_preformatted_and_semantic_role_semantics"
regression_text = REGRESSIONS.read_text(encoding="utf-8")
if regression_marker in regression_text:
    raise SystemExit("shared-methodology regression already present")
regression_text += r'''


@pytest.mark.parametrize("kind", ("preformatted-content", "semantic-role"))
def test_shared_methodology_rejects_preformatted_and_semantic_role_semantics(
    kind: str,
) -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")

    workstream_i_phrase = "source-gated research proposal"
    if kind == "preformatted-content":
        workstream_i_payload = "<pre>source-gated     research proposal</pre>"
    else:
        workstream_i_payload = '<a role="button">source-gated research proposal</a>'
    mutated_i = roadmap.replace(workstream_i_phrase, workstream_i_payload, 1)
    assert mutated_i != roadmap
    assert kind in POLICING["_governed_surface_html_violations"](mutated_i)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated_i)

    workstream_h_phrase = (
        "nationality and first-language identity must not define the comparison cohorts"
    )
    if kind == "preformatted-content":
        workstream_h_payload = (
            "<pre>nationality and first-language identity must     not define the "
            "comparison cohorts</pre>"
        )
    else:
        workstream_h_payload = (
            '<a role="button">nationality and first-language identity must not define '
            "the comparison cohorts</a>"
        )
    mutated_h = roadmap.replace(workstream_h_phrase, workstream_h_payload, 1)
    assert mutated_h != roadmap
    assert kind in POLICING["_governed_surface_html_violations"](mutated_h)
    with pytest.raises(AssertionError):
        WORKSTREAM_H["_assert_workstream_h_integrity"](mutated_h)
'''
REGRESSIONS.write_text(regression_text, encoding="utf-8")

print(f"phase2_visible_sha256={digest}")
