"""Regression checks for governed research-reference registration."""

from pathlib import Path


CORPUS = Path(__file__).parent.parent / "docs" / "RESEARCH-REFERENCE-CORPUS.md"


REGISTERED_ENTRIES = (
    "### *Black Comedy* (ABC, 2014-2020)",
    "### *Kath & Kim*",
    "### *The Castle* (1997)",
    "### *Shaun Micallef's MAD AS HELL*",
    "### *Acropolis Now*",
    "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*",
    "### Hurley (2025), *Laughter with purpose: how First Nations Australian comedians use humour to engage, educate, and empower audiences*",
)

COMMUNITY_SPECIFIC_ENTRIES = (
    "### *Black Comedy* (ABC, 2014-2020)",
    "### *Kath & Kim*",
    "### *Acropolis Now*",
    "### Hurley (2025), *Laughter with purpose: how First Nations Australian comedians use humour to engage, educate, and empower audiences*",
)

REQUIRED_ENTRY_FIELDS = (
    "**Source type:**",
    "**Rights and provenance boundary:**",
    "**Epistemic status:**",
    "Relevant project mappings:",
    "**Safe benchmark abstraction:**",
)


def _registered_section(corpus: str, heading: str) -> str:
    """Return one registered entry without leaking fields from its neighbours."""
    start = corpus.index(heading)
    next_entry = corpus.find("\n---\n\n### ", start + len(heading))
    batch_end = corpus.find("\n---\n\n## Priority A", start + len(heading))
    ends = [position for position in (next_entry, batch_end) if position != -1]
    assert ends, f"registered entry {heading!r} has no section boundary"
    return corpus[start : min(ends)]


def test_post_phase2_registry_batch_preserves_governance_contract():
    corpus = CORPUS.read_text(encoding="utf-8")

    assert "## Registration contract for new sources" in corpus
    assert "## Registered post-Phase-2 expansion batch" in corpus
    assert "Every adopted post-Phase-2 registry entry must record all of the following fields" in corpus
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in corpus

    sections = {entry: _registered_section(corpus, entry) for entry in REGISTERED_ENTRIES}

    for entry, section in sections.items():
        assert "**Registered source:**" in section or "**Registered sources:**" in section
        for field in REQUIRED_ENTRY_FIELDS:
            assert field in section, f"{entry} is missing required registry field {field}"
        assert "Candidate research mappings:" in section or "Research mappings:" in section

    consultation_boundary = (
        "appropriate consultation, provenance, permissions, and scope limitations"
    )
    for entry in COMMUNITY_SPECIFIC_ENTRIES:
        assert consultation_boundary in sections[entry], (
            f"{entry} is missing its community-specific consultation boundary"
        )
