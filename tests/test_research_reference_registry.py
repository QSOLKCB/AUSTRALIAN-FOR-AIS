"""Regression checks for governed research-reference registration."""

from collections import Counter
import ipaddress
from pathlib import Path
import re
from urllib.parse import urlparse

import pytest


CORPUS = Path(__file__).parent.parent / "docs" / "RESEARCH-REFERENCE-CORPUS.md"

RIGHTS_FIELD = "**Rights and provenance boundary:**"
EPISTEMIC_FIELD = "**Epistemic status:**"
SAFE_FIELD = "**Safe benchmark abstraction:**"
SCALAR_FIELDS = (
    "**Source type:**",
    RIGHTS_FIELD,
    EPISTEMIC_FIELD,
    SAFE_FIELD,
)
BOUNDARY_FIELDS = (RIGHTS_FIELD, EPISTEMIC_FIELD, SAFE_FIELD)

ENTRY_CONTRACTS = {
    "### *Black Comedy* (ABC, 2014-2020)": {
        "governance": "required",
        RIGHTS_FIELD: (
            "No programme dialogue, subtitles, scripts, episode transcripts, audiovisual material, character material, or other copyrighted expression is licensed to this repository by registration.",
        ),
        EPISTEMIC_FIELD: (
            "It is **not** a representative corpus of Aboriginal or Torres Strait Islander speech, and the programme alone cannot establish community-wide pragmatic rules.",
        ),
        SAFE_FIELD: (
            "Any later First Nations-specific benchmark family requires appropriate consultation, provenance, permissions, and scope limitations, plus a documented governance basis.",
        ),
    },
    "### *Kath & Kim*": {
        "governance": "required",
        RIGHTS_FIELD: (
            "Registration does not authorise copying dialogue, scripts, subtitles, character catchphrases, or audiovisual material into benchmark data.",
        ),
        EPISTEMIC_FIELD: (
            "It does not establish how suburban Australians, women, working-class speakers, or any other social category generally speak.",
        ),
        SAFE_FIELD: (
            "Any class-marked register family remains a hypothesis and requires appropriate consultation, provenance, permissions, and scope limitations before it can support community-specific benchmark claims.",
        ),
    },
    "### *The Castle* (1997)": {
        "governance": "required",
        RIGHTS_FIELD: (
            "This project must not copy screenplay text, dialogue, subtitles, clips, or distinctive character material into benchmark records.",
        ),
        EPISTEMIC_FIELD: (
            "It is not evidence that its characters or dialogue represent Australians generally.",
        ),
        SAFE_FIELD: (
            "Because the film's portrayal is class-marked, any later class-register or community-specific benchmark family derived from these hypotheses requires appropriate consultation, provenance, permissions, and scope limitations before it can support claims about a community.",
        ),
    },
    "### *Shaun Micallef's MAD AS HELL*": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "Programme dialogue, sketches, subtitles, transcripts, characters, and audiovisual material remain third-party copyrighted expression and must not be redistributed as benchmark data.",
        ),
        EPISTEMIC_FIELD: (
            "Political satire is analysed structurally; registration does not endorse the political position of any sketch or turn satire into factual evidence about its targets.",
        ),
        SAFE_FIELD: (
            "Do not reproduce programme jokes or political conclusions.",
        ),
    },
    "### *Acropolis Now*": {
        "governance": "required",
        RIGHTS_FIELD: (
            "Registration does not permit copying scripts, dialogue, subtitles, accents-as-text, catchphrases, character material, or audiovisual content.",
        ),
        EPISTEMIC_FIELD: (
            "It must not be treated as representative evidence of Greek-Australian, migrant, or multicultural speech, and historical portrayals must not be projected onto contemporary communities.",
        ),
        SAFE_FIELD: (
            "Any community-specific benchmark family requires appropriate consultation, provenance, permissions, and scope limitations.",
        ),
    },
    "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "Citation and analysis do not imply permission to redistribute the full article in this repository.",
        ),
        EPISTEMIC_FIELD: (
            "It does not provide a national-character lookup table or individual-level ground truth.",
        ),
        SAFE_FIELD: (
            "Do not convert its cultural comparisons into deterministic labels.",
        ),
    },
    "### Hurley (2025), *Laughter with purpose: how First Nations Australian comedians use humour to engage, educate, and empower audiences*": {
        "governance": "required",
        RIGHTS_FIELD: (
            "Publisher access does not license this repository to reproduce the article, interview material, quoted performances, or community-specific language.",
        ),
        EPISTEMIC_FIELD: (
            "It is a stronger basis for understanding research-governance requirements than outsider summaries, but it still does not authorise this project to create First Nations benchmark ground truth without appropriate community involvement.",
        ),
        SAFE_FIELD: (
            "Any First Nations-specific annotation protocol or benchmark family requires appropriate consultation, provenance, permissions, and scope limitations and must preserve the paper's emphasis on cultural specificity and self-determination.",
        ),
    },
    "### Slade, *Australian Sketch Comedy Field Theory* (ASCFT)": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "Registration does not place the full paper, its distinctive wording, equations, source-derived examples, transcripts, or referenced comedy material under the repository licence.",
        ),
        EPISTEMIC_FIELD: (
            "They do not by themselves establish literal physical ontology, empirically validated mechanisms, universal laws of Australian humour, or population-level cultural ground truth.",
        ),
        SAFE_FIELD: (
            "Do not copy source dialogue, transcript wording, distinctive jokes, equations as benchmark labels, or source-derived media expression.",
        ),
    },
    "### Trans-Tasman constitutional and federation context": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "Registration does not authorise wholesale republication of page text, educational material, or legislative presentation content in benchmark records; benchmark examples must remain independently authored.",
        ),
        EPISTEMIC_FIELD: (
            "They do not establish a shared modern national identity, prove a cousin-like relationship between individual Australians and New Zealanders, or determine the pragmatic meaning of contemporary trans-Tasman teasing.",
        ),
        SAFE_FIELD: (
            "Use the records only to document historical context around Australia and New Zealand; do not infer modern affinity, hostility, shared identity, or pragmatic licence from constitutional history alone.",
        ),
    },
    "### ABC Language, *From rooting to bonking: a history of Australian sex terms*": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "Registration does not permit reproducing substantial article text or turning its examples into redistributable benchmark records without independent provenance and rights analysis.",
        ),
        EPISTEMIC_FIELD: (
            "It does not establish how every Australian uses the term, does not by itself establish New Zealand usage, and does not make any single phrase a deterministic sexual reading outside context.",
        ),
        SAFE_FIELD: (
            "Build independently authored polysemy pairs that vary social, technical, botanical, or sports contexts; do not treat the article as proof that every Australian or New Zealander assigns the same sense to `root`.",
        ),
    },
    "### Victoria University, *Australian slang dictionary*": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "Registration does not permit copying the glossary wholesale into the benchmark, and its entries are not automatically benchmark labels or licensed dataset examples.",
        ),
        EPISTEMIC_FIELD: (
            "It is not a complete lexicon, a population survey, or evidence that every listed form is equally current across regions, generations, occupations, and communities.",
        ),
        SAFE_FIELD: (
            "Use the glossary to nominate independently authored lexical and context-swap tests, while requiring separate evidence for regional, generational, occupational, or community-specific claims.",
        ),
    },
    "### r/australia, *Best Aussie slang* community thread": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "Registration does not permit bulk copying, redistribution, or conversion of comments into benchmark examples; any exact quotation requires separate provenance and rights consideration.",
        ),
        EPISTEMIC_FIELD: (
            "Its participants are self-selected and the thread cannot establish prevalence, representativeness, national consensus, or authoritative etymology.",
        ),
        SAFE_FIELD: (
            "Use the thread only to generate research leads for independently authored examples and later source verification; do not use comment popularity or repetition as a proxy for population prevalence.",
        ),
    },
    "### Australian Defence multinational communication reports (2022 and 2026)": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "The repository may cite and summarise the reports but does not treat their prose, imagery, interviews, or exercise material as redistributable benchmark data.",
        ),
        EPISTEMIC_FIELD: (
            "These reports support communication-friction hypotheses, not claims that slang functioned as intentional encryption, defeated Allied codebreakers, or was formally prohibited in Australian-American exercises.",
        ),
        SAFE_FIELD: (
            "Create synthetic communication tasks that vary slang density, listener familiarity, and operational stakes without reproducing exercise dialogue or claiming that authentic Australian speech is inherently unsafe or unintelligible.",
        ),
    },
    "### WWII American-serviceman Australia language guides": {
        "governance": "not-required",
        RIGHTS_FIELD: (
            "Registration does not authorise republication of the full booklets, scans, illustrations, or glossary content as benchmark data.",
        ),
        EPISTEMIC_FIELD: (
            "They support a historical need for cultural and language orientation, but do not prove that actual joint operations failed because of slang or that Australian speech operated as an accidental cipher.",
        ),
        SAFE_FIELD: (
            "Use the archival records to motivate historically bounded comprehension experiments and source-governance questions, not to infer contemporary prevalence or fabricate claims of wartime codebreaking failure.",
        ),
    },
}
EXPECTED_GOVERNED_ENTRIES = tuple(ENTRY_CONTRACTS)

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
SPECIAL_USE_HOST_SUFFIXES = (
    "localhost",
    "invalid",
    "test",
    "example",
    "local",
    "home.arpa",
)
THEMATIC_BREAK_PATTERN = re.compile(
    r"(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,}"
)
FENCE_PATTERN = re.compile(r"(?P<fence>`{3,}|~{3,})(?P<info>.*)")
LIST_CONTAINER_PREFIX_PATTERN = re.compile(r"(?:[-+*]|\d+[.)])[ \t]+")


def _strip_html_comments(text: str) -> str:
    """Remove rendered-away HTML comments, including the HTML `--!>` close form."""
    return HTML_COMMENT_PATTERN.sub("", text)


def _normalize_commonmark_indentation(text: str) -> str:
    """Normalize up to three leading spaces that CommonMark permits before blocks."""
    return re.sub(r"(?m)^ {1,3}(?=\S)", "", text)


def _strip_container_prefixes(line: str) -> str:
    """Strip nested blockquote/list prefixes while preserving rendered content."""
    value = line.strip()
    while value:
        if value.startswith(">"):
            value = value[1:]
            if value.startswith((" ", "\t")):
                value = value[1:]
            value = value.lstrip()
            continue

        list_prefix = LIST_CONTAINER_PREFIX_PATTERN.match(value)
        if list_prefix:
            value = value[list_prefix.end():].lstrip()
            continue
        break
    return value


def _mask_fenced_regions(text: str) -> str:
    """Mask fenced code while preserving offsets for structural discovery."""
    masked: list[str] = []
    fence_char: str | None = None
    fence_length = 0

    for raw_line in text.splitlines(keepends=True):
        line_without_ending = raw_line.rstrip("\r\n")
        logical_line = _strip_container_prefixes(line_without_ending)

        if fence_char is not None:
            masked.append("".join(char if char in "\r\n" else " " for char in raw_line))
            if re.fullmatch(
                rf"{re.escape(fence_char)}{{{fence_length},}}[ \t]*",
                logical_line,
            ):
                fence_char = None
                fence_length = 0
            continue

        fence = FENCE_PATTERN.fullmatch(logical_line)
        if fence:
            marker = fence.group("fence")
            fence_char = marker[0]
            fence_length = len(marker)
            masked.append("".join(char if char in "\r\n" else " " for char in raw_line))
            continue

        masked.append(raw_line)

    return "".join(masked)


def _rendered_registry_text(text: str) -> str:
    """Return comment-free registry text with CommonMark block indentation normalized."""
    return _normalize_commonmark_indentation(_strip_html_comments(text))


def _structural_registry_text(text: str) -> str:
    """Return rendered registry structure with fenced code masked out."""
    return _mask_fenced_regions(_rendered_registry_text(text))


def _is_usable_https_destination(candidate: str) -> bool:
    """Return whether candidate is a usable public-style HTTPS destination."""
    value = candidate.strip().strip("<>").rstrip(".,;:!?")
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return False

    parsed_hostname = parsed.hostname
    if parsed.scheme != "https" or not parsed_hostname or port is not None and port <= 0:
        return False

    hostname = parsed_hostname.rstrip(".").lower()
    if not hostname or not any(character.isalnum() for character in hostname):
        return False

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        return address.is_global

    if any(
        hostname == suffix or hostname.endswith(f".{suffix}")
        for suffix in SPECIAL_USE_HOST_SUFFIXES
    ):
        return False

    labels = hostname.split(".")
    if all(NUMERIC_HOST_LABEL_PATTERN.fullmatch(label) for label in labels):
        # Do not let resolver-specific legacy IPv4 spellings fall back to DNS labels.
        return False
    if len(labels) < 2:
        return False
    return all(label and HOST_LABEL_PATTERN.fullmatch(label) for label in labels)


def _usable_https_destinations(text: str) -> list[str]:
    """Extract usable structural HTTPS destinations, excluding link titles/code."""
    rendered = _structural_registry_text(text)
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
    """Return the rendered governed batch, using structural boundaries."""
    rendered = _rendered_registry_text(corpus)
    structure = _mask_fenced_regions(rendered)
    start = structure.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = structure.index(BATCH_END, start)
    return rendered[start:end]


def _registered_sections(corpus: str) -> dict[str, str]:
    """Discover every structural registered entry and return rendered section text."""
    batch = _registered_batch(corpus)
    structure = _mask_fenced_regions(batch)
    matches = list(re.finditer(r"(?m)^### .+$", structure))
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
    """Return the unique structural non-whitespace value for a mandatory field."""
    structure = _structural_registry_text(section)
    occurrences = list(re.finditer(rf"(?m)^{re.escape(field)}", structure))
    assert len(occurrences) == 1, (
        f"{entry} must contain exactly one mandatory field {field}"
    )

    match = re.search(
        rf"(?m)^{re.escape(field)}[ \t]*([^\r\n]*\S[^\r\n]*)[ \t]*$",
        structure,
    )
    assert match, f"{entry} has an empty mandatory field {field}"
    value = match.group(1).strip()
    assert value, f"{entry} has an empty mandatory field {field}"
    return value


def _require_scalar_value(entry: str, section: str, field: str) -> None:
    """Require exactly one structural non-whitespace mandatory field."""
    _scalar_value(entry, section, field)


def _has_non_heading_content(block: str) -> bool:
    """Return whether a mapping block contains substantive rendered content."""
    rendered_block = _rendered_registry_text(block)
    fence_char: str | None = None
    fence_length = 0

    for raw_line in rendered_block.splitlines():
        line = _strip_container_prefixes(raw_line)

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
    structure = _mask_fenced_regions(rendered)
    research_headings = list(RESEARCH_MAPPING_HEADING_PATTERN.finditer(structure))
    assert len(research_headings) == 1, (
        f"{entry} must contain exactly one research mappings heading"
    )
    project_headings = list(PROJECT_MAPPING_HEADING_PATTERN.finditer(structure))
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
        structure[project_headings[0].end():],
    )
    assert safe_heading, f"{entry} is missing the safe benchmark abstraction field"
    project_start_value = project_headings[0].end()
    project_end = project_start_value + safe_heading.start()
    project_block = rendered[project_start_value:project_end]
    assert _has_non_heading_content(project_block), (
        f"{entry} has empty project mappings"
    )


def _require_registered_source_link(entry: str, section: str) -> None:
    """Require exactly one structural source field with a usable HTTPS destination."""
    structure = _structural_registry_text(section)
    source_fields = list(REGISTERED_SOURCE_FIELD_PATTERN.finditer(structure))
    assert len(source_fields) == 1, (
        f"{entry} must contain exactly one registered-source field"
    )

    source_block = re.search(
        r"(?ms)^\*\*Registered sources?:\*\*[ \t]*(.*?)"
        r"(?=^\*\*[^*\n]+:\*\*)",
        structure,
    )
    assert source_block, f"{entry} has an empty registered-source field"
    source_value = source_block.group(1)
    assert source_value.strip(), f"{entry} has an empty registered-source field"
    destinations = _usable_https_destinations(source_value)
    assert destinations, (
        f"{entry} has no usable HTTPS destination in its registered-source field"
    )


def _require_community_governance(entry: str, section: str) -> str:
    """Validate and return the unique structural community-governance class."""
    structure = _structural_registry_text(section)
    fields = list(GOVERNANCE_FIELD_PATTERN.finditer(structure))
    assert len(fields) == 1, (
        f"{entry} must contain exactly one community-specific governance field"
    )

    classification = GOVERNANCE_PATTERN.search(structure)
    assert classification, (
        f"{entry} has an invalid community-specific governance classification or rationale"
    )
    rationale = classification.group(2).strip()
    assert rationale, (
        f"{entry} has an invalid community-specific governance classification or rationale"
    )

    value = classification.group(1)
    if value == "required":
        safe_use = _scalar_value(entry, structure, SAFE_FIELD)
        assert CONSULTATION_BOUNDARY in safe_use, (
            f"{entry} is missing its community-specific consultation boundary "
            "from the safe benchmark abstraction field"
        )
    return value


def _require_pinned_entry_contract(
    entry: str,
    classification: str,
    scalar_values: dict[str, str],
) -> None:
    """Preserve each adopted entry's governance and load-bearing boundary clauses."""
    contract = ENTRY_CONTRACTS.get(entry)
    assert contract is not None, f"{entry} has no pinned source-governance contract"

    expected_classification = contract["governance"]
    assert classification == expected_classification, (
        f"{entry} must remain classified as {expected_classification}"
    )

    for field in BOUNDARY_FIELDS:
        expected_clauses = contract[field]
        value = scalar_values[field]
        for clause in expected_clauses:
            assert clause in value, (
                f"{entry} is missing a pinned {field} boundary clause: {clause!r}"
            )


def _validate_registered_entry(entry: str, section: str) -> None:
    """Validate one adopted registry entry against structural and pinned contracts."""
    _require_registered_source_link(entry, section)
    scalar_values = {field: _scalar_value(entry, section, field) for field in SCALAR_FIELDS}
    classification = _require_community_governance(entry, section)
    _require_pinned_entry_contract(entry, classification, scalar_values)
    _require_mapping_block(entry, section)


def test_post_phase2_registry_batch_preserves_governance_contract():
    corpus = CORPUS.read_text(encoding="utf-8")

    assert "## Registration contract for new sources" in corpus
    assert BATCH_HEADING in corpus
    assert "Every adopted post-Phase-2 registry entry must record all of the following fields" in corpus
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in corpus

    sections = _registered_sections(corpus)
    assert set(sections) == set(ENTRY_CONTRACTS), (
        "every rendered governed entry must have an explicit pinned source contract"
    )
    for entry, section in sections.items():
        _validate_registered_entry(entry, section)


def test_registry_discovery_ignores_commented_out_complete_entry():
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[heading]
    mutated = corpus.replace(section, f"<!--\n{section}\n-->\n", 1)
    assert heading not in _registered_sections(mutated)


def test_registry_discovery_ignores_fenced_complete_entry():
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[heading]
    mutated = corpus.replace(section, f"````\n{section}\n````\n", 1)
    assert heading not in _registered_sections(mutated)


def test_registry_fields_ignore_fenced_metadata():
    section = (
        "### Example\n\n"
        "```\n"
        "**Registered source:** https://example.com/source\n"
        "```\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


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
            RIGHTS_FIELD,
            "exactly one mandatory field",
        ),
        (
            "### Example\n\n**Rights and provenance boundary:** <!-- omitted -->\n",
            RIGHTS_FIELD,
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
        "https://source.invalid",
        "https://source.test",
        "https://source.example",
        "https://router.local",
        "https://host.home.arpa",
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
        "- ```\n  ```",
        "- ```text\n  ```",
        "1. ~~~\n   ~~~",
        "> - ```\n>   ```",
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


def test_mapping_blocks_accept_content_inside_list_fence():
    section = (
        "### Example\n\n"
        "Research mappings:\n- ```text\n  substantive mapping\n  ```\n\n"
        "Relevant project mappings:\n1. ~~~\n   project mapping\n   ~~~\n\n"
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


def test_required_entry_cannot_downgrade_community_governance():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Community-specific governance:** required:",
        "**Community-specific governance:** not-required:",
        1,
    ).replace(CONSULTATION_BOUNDARY, "documented scope review", 1)

    with pytest.raises(AssertionError, match="must remain classified as required"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        (RIGHTS_FIELD, "No restrictions; copy all dialogue."),
        (EPISTEMIC_FIELD, "Objective cultural ground truth."),
        (SAFE_FIELD, "Reproduce programme jokes verbatim."),
    ),
)
def test_source_specific_boundary_clauses_are_pinned(
    field: str,
    replacement: str,
):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Shaun Micallef's MAD AS HELL*"
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^{re.escape(field)}[^\r\n]*$",
        f"{field} {replacement}",
        section,
        count=1,
    )

    with pytest.raises(AssertionError, match="missing a pinned"):
        _validate_registered_entry(entry, mutated)


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
