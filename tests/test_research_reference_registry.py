"""Regression checks for governed research-reference registration."""

from collections import Counter
import ipaddress
from pathlib import Path
import re
from urllib.parse import urlparse

import pytest


CORPUS = Path(__file__).parent.parent / "docs" / "RESEARCH-REFERENCE-CORPUS.md"

EXPECTED_GOVERNED_ENTRIES = (
    "### *Black Comedy* (ABC, 2014-2020)",
    "### *Kath & Kim*",
    "### *The Castle* (1997)",
    "### *Shaun Micallef's MAD AS HELL*",
    "### *Acropolis Now*",
    "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*",
    "### Hurley (2025), *Laughter with purpose: how First Nations Australian comedians use humour to engage, educate, and empower audiences*",
    "### Slade, *Australian Sketch Comedy Field Theory* (ASCFT)",
    "### Trans-Tasman constitutional and federation context",
    "### ABC Language, *From rooting to bonking: a history of Australian sex terms*",
    "### Victoria University, *Australian slang dictionary*",
    "### r/australia, *Best Aussie slang* community thread",
    "### Australian Defence multinational communication reports (2022 and 2026)",
    "### WWII American-serviceman Australia language guides",
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
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?(?:-->|--!>|$)", re.S)
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
NUMERIC_HOST_LABEL_PATTERN = re.compile(r"(?:0[xX][0-9A-Fa-f]+|[0-9]+)")
THEMATIC_BREAK_PATTERN = re.compile(
    r"(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,}"
)
FENCE_PATTERN = re.compile(r"(?P<fence>`{3,}|~{3,})(?P<info>.*)")


def _strip_html_comments(text: str) -> str:
    """Remove rendered-away HTML comments, including the HTML `--!>` close form."""
    return HTML_COMMENT_PATTERN.sub("", text)


def _normalize_commonmark_indentation(text: str) -> str:
    """Normalize up to three leading spaces that CommonMark permits before blocks."""
    return re.sub(r"(?m)^ {1,3}(?=\S)", "", text)


def _rendered_registry_text(text: str) -> str:
    """Return the registry text relevant to rendered structural validation."""
    return _normalize_commonmark_indentation(_strip_html_comments(text))


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

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        return address.is_global

    labels = hostname.split(".")
    if all(NUMERIC_HOST_LABEL_PATTERN.fullmatch(label) for label in labels):
        # Do not let resolver-specific legacy IPv4 spellings fall back to DNS labels.
        return False
    if hostname.lower() == "localhost" or len(labels) < 2:
        return False
    return all(label and HOST_LABEL_PATTERN.fullmatch(label) for label in labels)


def _usable_https_destinations(text: str) -> list[str]:
    """Extract usable rendered HTTPS destinations, excluding link titles."""
    rendered = _rendered_registry_text(text)
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
    """Return only the rendered governed post-Phase-2 registration batch."""
    rendered = _rendered_registry_text(corpus)
    start = rendered.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = rendered.index(BATCH_END, start)
    return rendered[start:end]


def _registered_sections(corpus: str) -> dict[str, str]:
    """Discover every rendered registered entry and return isolated section text."""
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
    rendered = _rendered_registry_text(section)
    occurrences = list(re.finditer(rf"(?m)^{re.escape(field)}", rendered))
    assert len(occurrences) == 1, (
        f"{entry} must contain exactly one mandatory field {field}"
    )

    match = re.search(
        rf"(?m)^{re.escape(field)}[ \t]*([^\r\n]*\S[^\r\n]*)[ \t]*$",
        rendered,
    )
    assert match, f"{entry} has an empty mandatory field {field}"
    value = match.group(1).strip()
    assert value, f"{entry} has an empty mandatory field {field}"
    return value


def _require_scalar_value(entry: str, section: str, field: str) -> None:
    """Require exactly one rendered non-whitespace mandatory field."""
    _scalar_value(entry, section, field)


def _strip_blockquote_prefixes(line: str) -> str:
    """Strip nested blockquote container prefixes while preserving their content."""
    value = line.strip()
    while value.startswith(">"):
        value = value[1:]
        if value.startswith((" ", "\t")):
            value = value[1:]
        value = value.lstrip()
    return value


def _has_non_heading_content(block: str) -> bool:
    """Return whether a mapping block contains substantive rendered content."""
    rendered_block = _rendered_registry_text(block)
    fence_char: str | None = None
    fence_length = 0

    for raw_line in rendered_block.splitlines():
        line = _strip_blockquote_prefixes(raw_line)

        if fence_char is not None:
            if re.fullmatch(
                rf"{re.escape(fence_char)}{{{fence_length},}}[ \t]*", line
            ):
                fence_char = None
                fence_length = 0
                continue
            if line:
                return True
            continue

        if not line:
            continue

        fence = FENCE_PATTERN.fullmatch(line)
        if fence:
            marker = fence.group("fence")
            fence_char = marker[0]
            fence_length = len(marker)
            continue

        if RESEARCH_MAPPING_HEADING_PATTERN.fullmatch(line):
            continue
        if PROJECT_MAPPING_HEADING_PATTERN.fullmatch(line):
            continue
        if re.fullmatch(r"#{1,6}[ \t]+.+", line):
            continue
        if THEMATIC_BREAK_PATTERN.fullmatch(line):
            continue
        if re.fullmatch(r"(?:[-+*]|\d+[.)])", line):
            continue
        if re.fullmatch(r"\*\*[^*]+:\*\*(?:[ \t].*)?", line):
            continue
        return True
    return False


def _require_mapping_block(entry: str, section: str) -> None:
    """Require unique, non-empty research and project mapping blocks."""
    rendered = _rendered_registry_text(section)
    research_headings = list(RESEARCH_MAPPING_HEADING_PATTERN.finditer(rendered))
    assert len(research_headings) == 1, (
        f"{entry} must contain exactly one research mappings heading"
    )
    project_headings = list(PROJECT_MAPPING_HEADING_PATTERN.finditer(rendered))
    assert len(project_headings) == 1, (
        f"{entry} must contain exactly one relevant project mappings heading"
    )

    research_start = research_headings[0].end()
    project_start = project_headings[0].start()
    assert research_start < project_start, (
        f"{entry} has research/project mapping headings in the wrong order"
    )
    research_block = rendered[research_start:project_start]
    assert _has_non_heading_content(research_block), (
        f"{entry} has empty research mappings"
    )

    safe_heading = re.search(
        r"(?m)^\*\*Safe benchmark abstraction:\*\*",
        rendered[project_headings[0].end():],
    )
    assert safe_heading, f"{entry} is missing the safe benchmark abstraction field"
    project_start_value = project_headings[0].end()
    project_end = project_start_value + safe_heading.start()
    project_block = rendered[project_start_value:project_end]
    assert _has_non_heading_content(project_block), (
        f"{entry} has empty project mappings"
    )


def _require_registered_source_link(entry: str, section: str) -> None:
    """Require exactly one rendered source field with a usable HTTPS destination."""
    rendered = _rendered_registry_text(section)
    source_fields = list(REGISTERED_SOURCE_FIELD_PATTERN.finditer(rendered))
    assert len(source_fields) == 1, (
        f"{entry} must contain exactly one registered-source field"
    )

    source_block = re.search(
        r"(?ms)^\*\*Registered sources?:\*\*[ \t]*(.*?)"
        r"(?=^\*\*[^*\n]+:\*\*)",
        rendered,
    )
    assert source_block, f"{entry} has an empty registered-source field"
    source_value = source_block.group(1)
    assert source_value.strip(), f"{entry} has an empty registered-source field"
    destinations = _usable_https_destinations(source_value)
    assert destinations, (
        f"{entry} has no usable HTTPS destination in its registered-source field"
    )


def _require_community_governance(entry: str, section: str) -> None:
    """Validate exactly one rendered community-governance field and gate."""
    rendered = _rendered_registry_text(section)
    fields = list(GOVERNANCE_FIELD_PATTERN.finditer(rendered))
    assert len(fields) == 1, (
        f"{entry} must contain exactly one community-specific governance field"
    )

    classification = GOVERNANCE_PATTERN.search(rendered)
    assert classification, (
        f"{entry} has an invalid community-specific governance classification or rationale"
    )
    rationale = classification.group(2).strip()
    assert rationale, (
        f"{entry} has an invalid community-specific governance classification or rationale"
    )

    if classification.group(1) == "required":
        safe_use = _scalar_value(entry, rendered, "**Safe benchmark abstraction:**")
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
    for expected in EXPECTED_GOVERNED_ENTRIES:
        assert expected in sections, f"expected governed registration {expected!r} is missing"

    for entry, section in sections.items():
        _require_registered_source_link(entry, section)
        for field in SCALAR_FIELDS:
            _require_scalar_value(entry, section, field)
        _require_community_governance(entry, section)
        _require_mapping_block(entry, section)


def test_registry_discovery_ignores_commented_out_complete_entry():
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[heading]
    mutated = corpus.replace(section, f"<!--\n{section}\n-->\n", 1)
    assert heading not in _registered_sections(mutated)


@pytest.mark.parametrize(
    ("section", "field", "message"),
    (
        (
            "### Example\n\n**Source type:**\n\n**Rights and provenance boundary:** value\n",
            "**Source type:**",
            "empty mandatory field",
        ),
        (
            "### Example\n\n**Rights and provenance boundary:** restrictive value\n\n"
            "**Rights and provenance boundary:** replacement\n",
            "**Rights and provenance boundary:**",
            "exactly one mandatory field",
        ),
        (
            "### Example\n\n**Rights and provenance boundary:** <!-- omitted -->\n",
            "**Rights and provenance boundary:**",
            "empty mandatory field",
        ),
    ),
)
def test_scalar_field_fail_closed(section: str, field: str, message: str):
    with pytest.raises(AssertionError, match=message):
        _require_scalar_value("### Example", section, field)


@pytest.mark.parametrize(
    "section",
    (
        "### Example\n\n**Registered source:** https://example.com/source\n\n"
        "**Registered sources:** https://example.com/other\n\n**Source type:** example\n",
        "### Example\n\n**Registered source:** https://example.com/source\n\n"
        "   **Registered source:** https://example.com/other\n\n**Source type:** example\n",
    ),
)
def test_registered_source_rejects_duplicate_fields(section: str):
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


@pytest.mark.parametrize(
    "section",
    (
        "### Example\n\n**Registered source:** <!-- https://example.com/source -->\n\n"
        "**Source type:** example\n",
        "### Example\n\n**Registered source:** <!-- https://example.com/source --!>\n\n"
        "**Source type:** example\n",
    ),
)
def test_registered_source_ignores_commented_urls(section: str):
    with pytest.raises(AssertionError, match="empty registered-source field"):
        _require_registered_source_link("### Example", section)


@pytest.mark.parametrize(
    "destination",
    (
        "[source](# \"https://example.com\")",
        "https://.",
        "https://localhost",
        "https://example",
        "https://127.0.0.1",
        "https://10.0.0.1",
        "https://192.168.1.1",
        "https://[::1]",
        "https://127.1",
        "https://127.0.0.01",
        "https://0x7f.0.0.1",
    ),
)
def test_registered_source_rejects_unusable_destinations(destination: str):
    section = (
        "### Example\n\n"
        f"**Registered source:** {destination}\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _require_registered_source_link("### Example", section)


def test_mapping_blocks_reject_duplicate_headings_without_content():
    section = (
        "### Example\n\nResearch mappings:\n\nResearch mappings:\n\n"
        "Relevant project mappings:\n\nRelevant project mappings:\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one research mappings heading"):
        _require_mapping_block("### Example", section)


@pytest.mark.parametrize(
    "container",
    (
        "-",
        "***",
        "___",
        "* * *",
        "_ _ _",
        "---",
        "- - -",
        ">",
        "> >",
        "```\n```",
        "```text\n```",
        "~~~\n~~~",
        "> ```\n> ```",
        "> ```text\n> ```",
        "> ~~~\n> ~~~",
    ),
)
def test_mapping_blocks_reject_empty_rendered_containers(container: str):
    section = (
        "### Example\n\n"
        f"Research mappings:\n{container}\n\n"
        f"Relevant project mappings:\n{container}\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="empty research mappings"):
        _require_mapping_block("### Example", section)


def test_mapping_blocks_accept_content_inside_nested_fence():
    section = (
        "### Example\n\n"
        "Research mappings:\n> ```text\n> substantive mapping\n> ```\n\n"
        "Relevant project mappings:\n> ```\n> project mapping\n> ```\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    _require_mapping_block("### Example", section)


@pytest.mark.parametrize(
    "container",
    (
        "- <!-- placeholder -->",
        "<!--\n- placeholder\n-->",
    ),
)
def test_mapping_blocks_reject_commented_empty_content(container: str):
    section = (
        "### Example\n\n"
        f"Research mappings:\n{container}\n\n"
        f"Relevant project mappings:\n{container}\n\n"
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


@pytest.mark.parametrize(
    "second_field",
    (
        "**Community-specific governance:** required: community-specific source.",
        "**Community-specific governance:** required:",
    ),
)
def test_community_governance_rejects_duplicate_fields(second_field: str):
    section = (
        "### Example\n\n"
        "**Community-specific governance:** not-required: structural research only.\n\n"
        f"{second_field}\n\n"
        "**Safe benchmark abstraction:** Use only structural research questions.\n"
    )
    with pytest.raises(AssertionError, match="exactly one community-specific governance field"):
        _require_community_governance("### Example", section)
