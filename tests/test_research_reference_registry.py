"""Regression checks for governed research-reference registration."""

from collections import Counter
from pathlib import Path
import re

import pytest


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

SCALAR_FIELDS = (
    "**Source type:**",
    "**Rights and provenance boundary:**",
    "**Epistemic status:**",
    "**Safe benchmark abstraction:**",
)

BATCH_HEADING = "## Registered post-Phase-2 expansion batch"
BATCH_END = "## Priority A: adversarial pragmatics"
CONSULTATION_BOUNDARY = (
    "appropriate consultation, provenance, permissions, and scope limitations"
)
GOVERNANCE_FIELD_PATTERN = re.compile(
    r"(?m)^\*\*Community-specific governance:\*\*"
)
GOVERNANCE_PATTERN = re.compile(
    r"(?m)^\*\*Community-specific governance:\*\*[ \t]*"
    r"(required|not-required):[ \t]*([^\r\n]*\S[^\r\n]*)[ \t]*$"
)


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

    headings = [match.group(0) for match in matches]
    duplicates = sorted(
        heading for heading, count in Counter(headings).items() if count > 1
    )
    assert not duplicates, f"duplicate registered-entry headings: {duplicates}"

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(0)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(batch)
        sections[heading] = batch[match.start():end]
    return sections


def _scalar_value(entry: str, section: str, field: str) -> str:
    """Return the unique non-whitespace value for a mandatory single-line field."""
    occurrences = list(re.finditer(rf"(?m)^{re.escape(field)}", section))
    assert len(occurrences) == 1, (
        f"{entry} must contain exactly one mandatory field {field}"
    )

    match = re.search(
        rf"(?m)^{re.escape(field)}[ \t]*([^\r\n]*\S[^\r\n]*)[ \t]*$",
        section,
    )
    assert match, f"{entry} has an empty mandatory field {field}"
    return match.group(1).strip()


def _require_scalar_value(entry: str, section: str, field: str) -> None:
    """Require exactly one non-whitespace mandatory single-line field."""
    _scalar_value(entry, section, field)


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
    """Require at least one HTTPS link in the registered-source field only."""
    source_block = re.search(
        r"(?ms)^\*\*Registered sources?:\*\*[ \t]*(.*?)"
        r"(?=^\*\*[^*\n]+:\*\*)",
        section,
    )
    assert source_block and source_block.group(1).strip(), (
        f"{entry} has an empty registered-source field"
    )
    urls = re.findall(r"https://[^\s)]+", source_block.group(1))
    assert urls, f"{entry} has no HTTPS link in its registered-source field"


def _require_community_governance(entry: str, section: str) -> None:
    """Validate exactly one per-entry community-governance field and gate."""
    fields = list(GOVERNANCE_FIELD_PATTERN.finditer(section))
    assert len(fields) == 1, (
        f"{entry} must contain exactly one community-specific governance field"
    )

    classification = GOVERNANCE_PATTERN.search(section)
    assert classification, (
        f"{entry} has an invalid community-specific governance classification or rationale"
    )

    if classification.group(1) == "required":
        safe_use = _scalar_value(entry, section, "**Safe benchmark abstraction:**")
        assert CONSULTATION_BOUNDARY in safe_use, (
            f"{entry} is missing its community-specific consultation boundary "
            "from the safe benchmark abstraction field"
        )


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
        _require_community_governance(entry, section)
        _require_mapping_block(entry, section)


def test_scalar_field_cannot_borrow_next_metadata_line():
    section = (
        "### Example\n\n"
        "**Source type:**\n\n"
        "**Rights and provenance boundary:** value\n"
    )
    with pytest.raises(AssertionError, match="empty mandatory field"):
        _require_scalar_value("### Example", section, "**Source type:**")


def test_scalar_field_rejects_duplicate_occurrences():
    section = (
        "### Example\n\n"
        "**Rights and provenance boundary:** restrictive value\n\n"
        "**Rights and provenance boundary:**\n"
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _require_scalar_value(
            "### Example", section, "**Rights and provenance boundary:**"
        )


def test_community_governance_requires_same_line_rationale():
    section = (
        "### Example\n\n"
        "**Community-specific governance:** not-required:\n\n"
        "Candidate research mappings:\n- example\n"
    )
    with pytest.raises(AssertionError, match="invalid community-specific governance"):
        _require_community_governance("### Example", section)


def test_required_consultation_boundary_must_be_in_safe_abstraction():
    section = (
        "### Example\n\n"
        "**Rights and provenance boundary:** "
        f"{CONSULTATION_BOUNDARY}.\n\n"
        "**Community-specific governance:** required: community-specific source.\n\n"
        "**Safe benchmark abstraction:** Use only structural research questions.\n"
    )
    with pytest.raises(AssertionError, match="safe benchmark abstraction field"):
        _require_community_governance("### Example", section)


def test_community_governance_rejects_duplicate_classifications():
    section = (
        "### Example\n\n"
        "**Community-specific governance:** not-required: structural research only.\n\n"
        "**Community-specific governance:** required: community-specific source.\n\n"
        "**Safe benchmark abstraction:** Use only structural research questions.\n"
    )
    with pytest.raises(AssertionError, match="exactly one community-specific governance field"):
        _require_community_governance("### Example", section)


def test_community_governance_counts_malformed_duplicate_field():
    section = (
        "### Example\n\n"
        "**Community-specific governance:** not-required: structural research only.\n\n"
        "**Community-specific governance:** required:\n\n"
        "**Safe benchmark abstraction:** Use only structural research questions.\n"
    )
    with pytest.raises(AssertionError, match="exactly one community-specific governance field"):
        _require_community_governance("### Example", section)
