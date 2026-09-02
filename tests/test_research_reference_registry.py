"""Regression checks for governed research-reference registration."""

from collections import Counter
from pathlib import Path
import re
from urllib.parse import urlparse

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
HTML_COMMENT_PATTERN = re.compile(
    r"<!--.*?(?:-->|--!>|$)",
    re.S,
)
GOVERNANCE_FIELD_PATTERN = re.compile(
    r"(?m)^\*\*Community-specific governance:\*\*"
)
GOVERNANCE_PATTERN = re.compile(
    r"(?m)^\*\*Community-specific governance:\*\*[ \t]*"
    r"(required|not-required):[ \t]*([^\r\n]*\S[^\r\n]*)[ \t]*$"
)
REGISTERED_SOURCE_FIELD_PATTERN = re.compile(
    r"(?m)^\*\*Registered sources?:\*\*"
)
RESEARCH_MAPPING_HEADING_PATTERN = re.compile(
    r"(?m)^(?:Candidate research mappings:|Research mappings:)[ \t]*$"
)
PROJECT_MAPPING_HEADING_PATTERN = re.compile(
    r"(?m)^Relevant project mappings:[ \t]*$"
)
MARKDOWN_LINK_PATTERN = re.compile(
    r"\[[^\]\r\n]*\]\("
    r"[ \t]*(?P<destination><[^>\r\n]+>|[^\s)\r\n]+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?"
    r"[ \t]*\)"
)
BARE_HTTPS_LINE_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:[-+*][ \t]+)?(?P<url>https://\S+)[ \t]*$"
)
AUTOLINK_PATTERN = re.compile(r"<(?P<url>https://[^>\s]+)>")
HOST_LABEL_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?")


def _strip_html_comments(text: str) -> str:
    """Remove rendered-away HTML comments, including the HTML `--!>` close form."""
    return HTML_COMMENT_PATTERN.sub("", text)


def _is_usable_https_destination(candidate: str) -> bool:
    """Return whether candidate is a usable public-style HTTPS destination."""
    value = candidate.strip().strip("<>").rstrip(".,;:!?")
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return False

    hostname = parsed.hostname
    if parsed.scheme != "https" or not hostname or port is not None and port <= 0:
        return False
    if not any(character.isalnum() for character in hostname):
        return False

    labels = hostname.split(".")
    return all(label and HOST_LABEL_PATTERN.fullmatch(label) for label in labels)


def _usable_https_destinations(text: str) -> list[str]:
    """Extract usable rendered HTTPS destinations, excluding link titles."""
    rendered = _strip_html_comments(text)
    destinations: list[str] = []

    for match in MARKDOWN_LINK_PATTERN.finditer(rendered):
        destination = match.group("destination").strip("<>")
        if _is_usable_https_destination(destination):
            destinations.append(destination)

    without_links = MARKDOWN_LINK_PATTERN.sub("", rendered)
    for match in AUTOLINK_PATTERN.finditer(without_links):
        destination = match.group("url")
        if _is_usable_https_destination(destination):
            destinations.append(destination)

    without_links = AUTOLINK_PATTERN.sub("", without_links)
    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destination = match.group("url")
        if _is_usable_https_destination(destination):
            destinations.append(destination)

    return destinations


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
    """Return the unique rendered non-whitespace value for a mandatory field."""
    occurrences = list(re.finditer(rf"(?m)^{re.escape(field)}", section))
    assert len(occurrences) == 1, (
        f"{entry} must contain exactly one mandatory field {field}"
    )

    match = re.search(
        rf"(?m)^{re.escape(field)}[ \t]*([^\r\n]*\S[^\r\n]*)[ \t]*$",
        section,
    )
    assert match, f"{entry} has an empty mandatory field {field}"
    value = _strip_html_comments(match.group(1)).strip()
    assert value, f"{entry} has an empty mandatory field {field}"
    return value


def _require_scalar_value(entry: str, section: str, field: str) -> None:
    """Require exactly one rendered non-whitespace mandatory field."""
    _scalar_value(entry, section, field)


def _has_non_heading_content(block: str) -> bool:
    """Return whether a mapping block contains substantive rendered content."""
    rendered_block = _strip_html_comments(block)
    for raw_line in rendered_block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if RESEARCH_MAPPING_HEADING_PATTERN.fullmatch(line):
            continue
        if PROJECT_MAPPING_HEADING_PATTERN.fullmatch(line):
            continue
        if re.fullmatch(r"#{1,6}[ \t]+.+", line):
            continue
        if re.fullmatch(r"-{3,}", line):
            continue
        if re.fullmatch(r"(?:[-+*]|\d+[.)])", line):
            continue
        if re.fullmatch(r"\*\*[^*]+:\*\*(?:[ \t].*)?", line):
            continue
        return True
    return False


def _require_mapping_block(entry: str, section: str) -> None:
    """Require unique, non-empty research and project mapping blocks."""
    research_headings = list(RESEARCH_MAPPING_HEADING_PATTERN.finditer(section))
    assert len(research_headings) == 1, (
        f"{entry} must contain exactly one research mappings heading"
    )
    project_headings = list(PROJECT_MAPPING_HEADING_PATTERN.finditer(section))
    assert len(project_headings) == 1, (
        f"{entry} must contain exactly one relevant project mappings heading"
    )

    research_start = research_headings[0].end()
    project_start = project_headings[0].start()
    assert research_start < project_start, (
        f"{entry} has research/project mapping headings in the wrong order"
    )
    research_block = section[research_start:project_start]
    assert _has_non_heading_content(research_block), (
        f"{entry} has empty research mappings"
    )

    safe_heading = re.search(
        r"(?m)^\*\*Safe benchmark abstraction:\*\*",
        section[project_headings[0].end():],
    )
    assert safe_heading, f"{entry} is missing the safe benchmark abstraction field"
    project_start_value = project_headings[0].end()
    project_end = project_start_value + safe_heading.start()
    project_block = section[project_start_value:project_end]
    assert _has_non_heading_content(project_block), (
        f"{entry} has empty project mappings"
    )


def _require_registered_source_link(entry: str, section: str) -> None:
    """Require exactly one registered-source field with a usable HTTPS destination."""
    source_fields = list(REGISTERED_SOURCE_FIELD_PATTERN.finditer(section))
    assert len(source_fields) == 1, (
        f"{entry} must contain exactly one registered-source field"
    )

    source_block = re.search(
        r"(?ms)^\*\*Registered sources?:\*\*[ \t]*(.*?)"
        r"(?=^\*\*[^*\n]+:\*\*)",
        section,
    )
    assert source_block, f"{entry} has an empty registered-source field"
    rendered_source = _strip_html_comments(source_block.group(1))
    assert rendered_source.strip(), f"{entry} has an empty registered-source field"
    destinations = _usable_https_destinations(source_block.group(1))
    assert destinations, f"{entry} has no usable HTTPS destination in its registered-source field"


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
    rationale = _strip_html_comments(classification.group(2)).strip()
    assert rationale, (
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


def test_scalar_field_rejects_comment_only_value():
    section = (
        "### Example\n\n"
        "**Rights and provenance boundary:** <!-- omitted -->\n"
    )
    with pytest.raises(AssertionError, match="empty mandatory field"):
        _require_scalar_value(
            "### Example", section, "**Rights and provenance boundary:**"
        )


def test_registered_source_rejects_duplicate_singular_plural_fields():
    section = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "**Registered sources:**\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


def test_registered_source_ignores_commented_out_url():
    section = (
        "### Example\n\n"
        "**Registered source:** <!-- https://example.com/source -->\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="empty registered-source field"):
        _require_registered_source_link("### Example", section)


def test_registered_source_ignores_alternate_comment_terminator():
    section = (
        "### Example\n\n"
        "**Registered source:** <!-- https://example.com/source --!>\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="empty registered-source field"):
        _require_registered_source_link("### Example", section)


def test_registered_source_rejects_https_in_markdown_title():
    section = (
        "### Example\n\n"
        "**Registered source:** [source](# \"https://example.com\")\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _require_registered_source_link("### Example", section)


def test_registered_source_rejects_malformed_https_host():
    section = (
        "### Example\n\n"
        "**Registered source:** https://.\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _require_registered_source_link("### Example", section)


def test_mapping_blocks_reject_duplicate_headings_without_content():
    section = (
        "### Example\n\n"
        "Research mappings:\n\n"
        "Research mappings:\n\n"
        "Relevant project mappings:\n\n"
        "Relevant project mappings:\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one research mappings heading"):
        _require_mapping_block("### Example", section)


def test_mapping_blocks_reject_empty_list_markers():
    section = (
        "### Example\n\n"
        "Research mappings:\n-\n\n"
        "Relevant project mappings:\n-\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="empty research mappings"):
        _require_mapping_block("### Example", section)


def test_mapping_blocks_reject_commented_empty_list_markers():
    section = (
        "### Example\n\n"
        "Research mappings:\n- <!-- placeholder -->\n\n"
        "Relevant project mappings:\n- <!-- placeholder -->\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="empty research mappings"):
        _require_mapping_block("### Example", section)


def test_mapping_blocks_reject_multiline_commented_content():
    section = (
        "### Example\n\n"
        "Research mappings:\n<!--\n- placeholder\n-->\n\n"
        "Relevant project mappings:\n<!--\n- placeholder\n-->\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="empty research mappings"):
        _require_mapping_block("### Example", section)


def test_community_governance_requires_same_line_rationale():
    section = (
        "### Example\n\n"
        "**Community-specific governance:** not-required:\n\n"
        "Candidate research mappings:\n- example\n"
    )
    with pytest.raises(AssertionError, match="invalid community-specific governance"):
        _require_community_governance("### Example", section)


def test_community_governance_rejects_comment_only_rationale():
    section = (
        "### Example\n\n"
        "**Community-specific governance:** not-required: <!-- omitted -->\n"
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