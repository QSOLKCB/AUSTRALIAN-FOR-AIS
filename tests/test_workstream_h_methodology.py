"""Regression checks for Workstream H listener-variable and source-governance design."""

from pathlib import Path


ROOT = Path(__file__).parent.parent
ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"


def _workstream_h(text: str) -> str:
    start = text.index("### H. Slang density")
    end = text.index("### I. Australian and United States policing-context transfer", start)
    return text[start:end]


def test_workstream_h_decouples_dialect_exposure_from_listener_identity():
    section = _workstream_h(ROADMAP.read_text(encoding="utf-8"))
    assert "self-reported or experimentally established Australian-English exposure" in section
    assert "independently of general English-language background or proficiency" in section
    assert "nationality and first-language identity must not define the comparison cohorts" in section
    assert "familiar Australian speakers, other English-speaking partners" not in section


def test_canonical_methodology_crosses_listener_variables_independently():
    text = METHODOLOGY.read_text(encoding="utf-8")
    start = text.index("## Trans-Tasman and Slang/Operational Experiment Design")
    end = text.index("## Australian and United States Policing-Context Experiment Design", start)
    section = text[start:end]
    assert "Australian-English familiarity or exposure" in section
    assert "self-reported or experimentally established" in section
    assert "neither nationality nor first-language category acts as a proxy for comprehension" in section
    assert "higher versus lower Australian-English familiarity crossed or matched" in section


def test_workstream_h_keeps_community_attestation_bounded():
    section = _workstream_h(ROADMAP.read_text(encoding="utf-8"))
    assert "orientation/community-attestation sources with explicit non-representative status" in section
    assert "converting crowd-sourced examples directly into benchmark data" in section


def test_trans_tasman_methodology_never_allows_exact_group_stereotype_wording():
    text = METHODOLOGY.read_text(encoding="utf-8")
    start = text.index("## Trans-Tasman and Slang/Operational Experiment Design")
    end = text.index("## Australian and United States Policing-Context Experiment Design", start)
    section = text[start:end]
    assert "exact group-stereotyping wording must not be reproduced" in section
    assert "unless exact material has an attributable source" not in section
