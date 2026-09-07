from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).parent.parent
P = runpy.run_path(str(ROOT / "tests/test_policing_context_roadmap.py"))
R = runpy.run_path(str(ROOT / "tests/test_research_reference_registry.py"))
ROADMAP = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
CORPUS = (ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")

POLICING_CLAUSE = "source-gated research proposal"
RIGHTS_CLAUSE = R["REDISTRIBUTION_INVARIANT"]
BLACK_COMEDY_URL = "https://iview.abc.net.au/show/black-comedy"


@pytest.mark.parametrize(
    "markup",
    (
        '<font color="white">{clause}</font>',
        '<font color="transparent">{clause}</font>',
        '<basefont color="white">{clause}',
    ),
)
def test_shared_preflight_rejects_legacy_presentational_font(markup):
    violations = P["_governed_surface_html_violations"](
        markup.format(clause="governed clause")
    )
    assert "presentational-font" in violations
    with pytest.raises(AssertionError):
        P["_assert_supported_governed_html"](violations)


@pytest.mark.parametrize(
    "markup",
    (
        '<font color="white">{clause}</font>',
        '<font color="transparent">{clause}</font>',
    ),
)
def test_policing_and_registry_reject_presentational_font(markup):
    roadmap = ROADMAP.replace(
        POLICING_CLAUSE, markup.format(clause=POLICING_CLAUSE), 1
    )
    with pytest.raises(AssertionError):
        P["_validate_policing_workstream"](roadmap)

    corpus = CORPUS.replace(
        RIGHTS_CLAUSE, markup.format(clause=RIGHTS_CLAUSE), 1
    )
    with pytest.raises(AssertionError):
        R["_validate_registry_corpus"](corpus)


@pytest.mark.parametrize("attribute", ("aria-label", "aria-labelledby"))
def test_registry_rejects_accessible_name_override_on_registered_source(attribute):
    value = (
        "Unverified and reusable source"
        if attribute == "aria-label"
        else "contradictory-source-name"
    )
    anchor = (
        f'<a href="{BLACK_COMEDY_URL}" {attribute}="{value}">'
        f"{BLACK_COMEDY_URL}</a>"
    )
    mutation = CORPUS.replace(BLACK_COMEDY_URL, anchor, 1)
    violations = P["_governed_surface_html_violations"](anchor)
    assert "accessible-name" in violations
    with pytest.raises(AssertionError):
        R["_validate_registry_corpus"](mutation)
