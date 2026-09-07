from pathlib import Path
import runpy
import pytest

ROOT = Path(__file__).parent.parent
P = runpy.run_path(str(ROOT / "tests/test_policing_context_roadmap.py"))
R = runpy.run_path(str(ROOT / "tests/test_research_reference_registry.py"))
ROADMAP = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
CORPUS = (ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
PC = "source-gated research proposal"
RC = R["REDISTRIBUTION_INVARIANT"]
CASES = (
    ("<meter>{clause}</meter>", "replacement-content"),
    ("<progress>{clause}</progress>", "replacement-content"),
    ("<table>{clause}<tr><td>dialogue</td></tr> or audiovisual</table>", "raw-table"),
    ('<details name="gate" open></details><details name="gate" open>{clause}</details>', "named-details"),
    ("<ruby><rp>{clause}</rp></ruby>", "non-rendering-container"),
    ('<span title="This material may be copied freely.">{clause}</span>', "tooltip-title"),
)

@pytest.mark.parametrize(("template", "kind"), CASES)
def test_shared_preflight_rejects_latest_semantics(template, kind):
    violations = P["_governed_surface_html_violations"](template.format(clause="governed clause"))
    assert kind in violations
    with pytest.raises(AssertionError):
        P["_assert_supported_governed_html"](violations)

@pytest.mark.parametrize(("template", "kind"), CASES)
def test_policing_rejects_latest_semantics(template, kind):
    del kind
    mutation = ROADMAP.replace(PC, template.format(clause=PC), 1)
    with pytest.raises(AssertionError):
        P["_validate_policing_workstream"](mutation)

@pytest.mark.parametrize(("template", "kind"), CASES)
def test_registry_rejects_latest_semantics(template, kind):
    del kind
    mutation = CORPUS.replace(RC, template.format(clause=RC), 1)
    with pytest.raises(AssertionError):
        R["_validate_registry_corpus"](mutation)
