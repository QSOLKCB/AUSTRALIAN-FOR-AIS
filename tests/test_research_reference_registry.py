"""Regression checks for governed research-reference registration."""

from pathlib import Path
import re


CORPUS = Path(__file__).parent.parent / "docs" / "RESEARCH-REFERENCE-CORPUS.md"


EXPECTED_INITIAL_ENTRIES = (
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
    "### *The Castle* (1997)",
    "### *Acropolis Now*",
    "### Hurley (2025), *Laughter with purpose: how First Nations Australian comedians use humour to engage, educate, and empower audiences*",
)

SCALAR_FIELDS = (
    "**Source type:**",
    "**Rights and provenance boundary:**",
    "**Epistemic status:**",
    "**Safe benchmark abstraction:**",
)

BATCH_HEADING = "## Registered post-Phase-2 expansion batch"
BATCH_END = "## Priority A: adversarial pragmatics"


def _registered_batch(corpus: str) -> str:
    """Return only the governed post-Phase-2 registration batch."""
    start = corpus.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = corpus.index(BATCH_END, start)
    return corpus[start:end]


def _registered_sections(corpus: str) -> dict[str, str]:
    """Discover every registered entry and return isolated section text."""
    batch = _registered_batch(corpus)
    matches = list(re.finditer(r"(?m)^### .+$", batch))
    assert matches, "registered post-Phase-2 batch contains no entries"

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(0)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(batch)
        sections[heading] = batch[match.start():end]
    return sections


def _require_scalar_value(entry: str, section: str, field: str) -> None:
    """Require non-whitespace content on a mandatory single-line field."""
    match = re.search(rf"(?m)^{re.escape(field)}\s*(.+?)\s*$", section)
    assert match and match.group(1).strip(), f"{entry} has an empty mandatory field {field}"


def _require_mapping_block(entry: str, section: str) -> None:
    """Require non-empty research and project mapping blocks."""
    research = re.search(
        r"(?ms)^(?:Candidate research mappings:|Research mappings:)\s*(.+?)"
        r"(?=^Relevant project mappings:)",
        section,
    )
    assert research and research.group(1).strip(), f"{entry} has empty research mappings"

    project = re.search(
        r"(?ms)^Relevant project mappings:\s*(.+?)"
        r"(?=^\*\*Safe benchmark abstraction:\*\*)",
        section,
    )
    assert project and project.group(1).strip(), f"{entry} has empty project mappings"


def _require_registered_source_link(entry: str, section: str) -> None:
    """Require at least one HTTPS link in the registered-source field."""
    source_block = re.search(
        r"(?ms)^\*\*Registered sources?:\*\*\s*(.+?)"
        r"(?=^\*\*Source type:\*\*)",
        section,
    )
    assert source_block and source_block.group(1).strip(), (
        f"{entry} has an empty registered-source field"
    )
    urls = re.findall(r"https://[^\s)]+", source_block.group(1))
    assert urls, f"{entry} has no HTTPS link in its registered-source field"


def test_post_phase2_registry_batch_preserves_governance_contract():
    corpus = CORPUS.read_text(encoding="utf-8")

    assert "## Registration contract for new sources" in corpus
    assert BATCH_HEADING in corpus
    assert "Every adopted post-Phase-2 registry entry must record all of the following fields" in corpus
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in corpus

    sections = _registered_sections(corpus)

    for expected in EXPECTED_INITIAL_ENTRIES:
        assert expected in sections, f"expected initial registration {expected!r} is missing"

    for entry, section in sections.items():
        _require_registered_source_link(entry, section)
        for field in SCALAR_FIELDS:
            _require_scalar_value(entry, section, field)
        _require_mapping_block(entry, section)

    consultation_boundary = (
        "appropriate consultation, provenance, permissions, and scope limitations"
    )
    for entry in COMMUNITY_SPECIFIC_ENTRIES:
        assert entry in sections, f"community-specific registration {entry!r} is missing"
        assert consultation_boundary in sections[entry], (
            f"{entry} is missing its community-specific consultation boundary"
        )
