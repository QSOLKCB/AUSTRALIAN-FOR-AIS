"""Regression checks for the proposed policing-context research workstream."""

from pathlib import Path


ROADMAP = Path(__file__).parent.parent / "ROADMAP.md"


def test_policing_context_workstream_remains_source_gated_and_noncomparative():
    roadmap = ROADMAP.read_text(encoding="utf-8")

    required_clauses = (
        "### I. Australian and United States policing-context transfer",
        "source-gated research proposal",
        "not legal advice",
        "Every implemented item should record the relevant country, jurisdiction, institutional role, encounter type, and source date.",
        "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",
        "CASUAL ADDRESS != FRIENDSHIP OR CONSENT",
        "FICTIONAL POLICE TROPE != OPERATIONAL POLICY",
        "JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER",
        "LEGAL INFORMATION != LEGAL ADVICE",
        "register official and current sources for each Australian and United States jurisdictional claim",
    )

    for clause in required_clauses:
        assert clause in roadmap, f"missing policing-workstream safeguard: {clause}"
