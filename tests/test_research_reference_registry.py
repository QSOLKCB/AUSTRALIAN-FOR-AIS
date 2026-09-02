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


def test_post_phase2_registry_batch_preserves_governance_contract():
    corpus = CORPUS.read_text(encoding="utf-8")

    assert "## Registration contract for new sources" in corpus
    assert "## Registered post-Phase-2 expansion batch" in corpus

    for entry in REGISTERED_ENTRIES:
        assert entry in corpus

    assert "**Rights and provenance boundary:**" in corpus
    assert "**Epistemic status:**" in corpus
    assert "**Safe benchmark abstraction:**" in corpus
    assert "appropriate consultation, provenance, permissions, and scope limitations" in corpus
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in corpus
