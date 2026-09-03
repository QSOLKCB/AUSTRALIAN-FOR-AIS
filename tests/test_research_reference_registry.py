"""Regression checks for governed research-reference registration."""

from collections import Counter
import ipaddress
from pathlib import Path
import re
from urllib.parse import urlparse

import pytest


CORPUS = Path(__file__).parent.parent / "docs" / "RESEARCH-REFERENCE-CORPUS.md"

SOURCE_TYPE_FIELD = "**Source type:**"
RIGHTS_FIELD = "**Rights and provenance boundary:**"
EPISTEMIC_FIELD = "**Epistemic status:**"
SAFE_FIELD = "**Safe benchmark abstraction:**"
SCALAR_FIELDS = (
    SOURCE_TYPE_FIELD,
    RIGHTS_FIELD,
    EPISTEMIC_FIELD,
    SAFE_FIELD,
)
PINNED_SCALAR_FIELDS = SCALAR_FIELDS
SOURCES_KEY = "sources"


def _entry_contract(
    *,
    sources: tuple[str, ...],
    source_type: str,
    governance: str,
    rights: tuple[str, ...],
    epistemic: tuple[str, ...],
    safe: tuple[str, ...],
) -> dict[str, object]:
    """Build one explicit, immutable-in-practice governed-entry contract."""
    return {
        SOURCES_KEY: sources,
        SOURCE_TYPE_FIELD: (source_type,),
        "governance": governance,
        RIGHTS_FIELD: rights,
        EPISTEMIC_FIELD: epistemic,
        SAFE_FIELD: safe,
    }


ENTRY_CONTRACTS = {
    "### *Black Comedy* (ABC, 2014-2020)": _entry_contract(
        sources=("https://iview.abc.net.au/show/black-comedy",),
        source_type=(
            "Broadcaster programme record for an Australian First Nations "
            "sketch-comedy series."
        ),
        governance="required",
        rights=(
            "No programme dialogue, subtitles, scripts, episode transcripts, "
            "audiovisual material, character material, or other copyrighted "
            "expression is licensed to this repository by registration.",
        ),
        epistemic=(
            "It is **not** a representative corpus of Aboriginal or Torres Strait "
            "Islander speech, and the programme alone cannot establish "
            "community-wide pragmatic rules.",
        ),
        safe=(
            "Any later First Nations-specific benchmark family requires appropriate "
            "consultation, provenance, permissions, and scope limitations, plus a "
            "documented governance basis.",
        ),
    ),
    "### *Kath & Kim*": _entry_contract(
        sources=("https://www.screenaustralia.gov.au/screen-guide/kath-and-kim-16295/",),
        source_type=(
            "Screen Australia catalogue record for an Australian television comedy "
            "series."
        ),
        governance="required",
        rights=(
            "Registration does not authorise copying dialogue, scripts, subtitles, "
            "character catchphrases, or audiovisual material into benchmark data.",
        ),
        epistemic=(
            "It does not establish how suburban Australians, women, working-class "
            "speakers, or any other social category generally speak.",
        ),
        safe=(
            "Any class-marked register family remains a hypothesis and requires "
            "appropriate consultation, provenance, permissions, and scope limitations "
            "before it can support community-specific benchmark claims.",
        ),
    ),
    "### *The Castle* (1997)": _entry_contract(
        sources=(
            "https://www.acmi.net.au/works/86581--the-castle/",
            "https://www.nfsa.gov.au/collection/item/castle-fathers-day",
        ),
        source_type=(
            "Australian cultural-institution catalogue records for the 1997 feature "
            "film."
        ),
        governance="required",
        rights=(
            "This project must not copy screenplay text, dialogue, subtitles, clips, "
            "or distinctive character material into benchmark records.",
        ),
        epistemic=(
            "It is not evidence that its characters or dialogue represent Australians "
            "generally.",
        ),
        safe=(
            "Because the film's portrayal is class-marked, any later class-register or "
            "community-specific benchmark family derived from these hypotheses "
            "requires appropriate consultation, provenance, permissions, and scope "
            "limitations before it can support claims about a community.",
        ),
    ),
    "### *Shaun Micallef's MAD AS HELL*": _entry_contract(
        sources=("https://iview.abc.net.au/show/shaun-micallef-s-mad-as-hell",),
        source_type=(
            "ABC broadcaster programme record for a satirical television comedy "
            "series."
        ),
        governance="not-required",
        rights=(
            "Programme dialogue, sketches, subtitles, transcripts, characters, and "
            "audiovisual material remain third-party copyrighted expression and must "
            "not be redistributed as benchmark data.",
        ),
        epistemic=(
            "Political satire is analysed structurally; registration does not endorse "
            "the political position of any sketch or turn satire into factual evidence "
            "about its targets.",
        ),
        safe=("Do not reproduce programme jokes or political conclusions.",),
    ),
    "### *Acropolis Now*": _entry_contract(
        sources=("https://www.screenaustralia.gov.au/screen-guide/acropolis-now-889/",),
        source_type=(
            "Screen Australia catalogue record for a historical Australian television "
            "comedy series."
        ),
        governance="required",
        rights=(
            "Registration does not permit copying scripts, dialogue, subtitles, "
            "accents-as-text, catchphrases, character material, or audiovisual content.",
        ),
        epistemic=(
            "It must not be treated as representative evidence of Greek-Australian, "
            "migrant, or multicultural speech, and historical portrayals must not be "
            "projected onto contemporary communities.",
        ),
        safe=(
            "Any community-specific benchmark family requires appropriate "
            "consultation, provenance, permissions, and scope limitations.",
        ),
    ),
    (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    ): _entry_contract(
        sources=("https://europeanjournalofhumour.org/ejhr/article/view/560",),
        source_type=(
            "Peer-reviewed article in *The European Journal of Humour Research*."
        ),
        governance="not-required",
        rights=(
            "Citation and analysis do not imply permission to redistribute the full "
            "article in this repository.",
        ),
        epistemic=(
            "It does not provide a national-character lookup table or individual-level "
            "ground truth.",
        ),
        safe=("Do not convert its cultural comparisons into deterministic labels.",),
    ),
    (
        "### Hurley (2025), *Laughter with purpose: how First Nations Australian "
        "comedians use humour to engage, educate, and empower audiences*"
    ): _entry_contract(
        sources=(
            "https://www.tandfonline.com/doi/full/10.1080/2040610X.2025.2538977",
        ),
        source_type=(
            "Peer-reviewed article in *Comedy Studies* using a culturally grounded "
            "qualitative methodology centred on Aboriginal and Torres Strait Islander "
            "comedians, writers, and performers."
        ),
        governance="required",
        rights=(
            "Publisher access does not license this repository to reproduce the "
            "article, interview material, quoted performances, or community-specific "
            "language.",
        ),
        epistemic=(
            "It is a stronger basis for understanding research-governance requirements "
            "than outsider summaries, but it still does not authorise this project to "
            "create First Nations benchmark ground truth without appropriate community "
            "involvement.",
        ),
        safe=(
            "Any First Nations-specific annotation protocol or benchmark family "
            "requires appropriate consultation, provenance, permissions, and scope "
            "limitations and must preserve the paper's emphasis on cultural specificity "
            "and self-determination.",
        ),
    ),
    "### Slade, *Australian Sketch Comedy Field Theory* (ASCFT)": _entry_contract(
        sources=("https://doi.org/10.5281/zenodo.17781653",),
        source_type=(
            "Project-authored formal-analysis paper supplied to the project by Trent "
            "Slade / QSOL-IMC. The supplied paper is titled *Australian Sketch Comedy "
            "Field Theory: A Formal Analysis of Epistemic Deformation, Ternary Logic, "
            "and Cultural Signal Dynamics* and defines ASCFT's ternary analytic basis, "
            "perturbation/collapse framing, and later field-theoretic extensions."
        ),
        governance="not-required",
        rights=(
            "Registration does not place the full paper, its distinctive wording, "
            "equations, source-derived examples, transcripts, or referenced comedy "
            "material under the repository licence.",
        ),
        epistemic=(
            "They do not by themselves establish literal physical ontology, "
            "empirically validated mechanisms, universal laws of Australian humour, or "
            "population-level cultural ground truth.",
        ),
        safe=(
            "Do not copy source dialogue, transcript wording, distinctive jokes, "
            "equations as benchmark labels, or source-derived media expression.",
        ),
    ),
    "### Trans-Tasman constitutional and federation context": _entry_contract(
        sources=(
            "https://peo.gov.au/understand-our-parliament/history-of-parliament/"
            "federation/federation",
            "https://peo.gov.au/understand-our-parliament/how-parliament-works/"
            "the-australian-constitution/introducing-the-australian-constitution",
            "https://peo.gov.au/understand-our-parliament/your-questions-on-notice/"
            "questions/new-zealand-is-mentioned-in-the-australian-constitution-does-"
            "that-mean-that-new-zealanders-have-the-right-to-vote-in-australia",
            "https://www.legislation.gov.au/C2004Q00685/asmade/1901-01-01/text/"
            "original/epub/OEBPS/document_1/document_1.html",
        ),
        source_type=(
            "Official Parliamentary Education Office explanatory material and "
            "Commonwealth legislation used to establish historical federation and "
            "constitutional context."
        ),
        governance="not-required",
        rights=(
            "Registration does not authorise wholesale republication of page text, "
            "educational material, or legislative presentation content in benchmark "
            "records; benchmark examples must remain independently authored.",
        ),
        epistemic=(
            "They do not establish a shared modern national identity, prove a "
            "cousin-like relationship between individual Australians and New "
            "Zealanders, or determine the pragmatic meaning of contemporary "
            "trans-Tasman teasing.",
        ),
        safe=(
            "Use the records only to document historical context around Australia and "
            "New Zealand; do not infer modern affinity, hostility, shared identity, or "
            "pragmatic licence from constitutional history alone.",
        ),
    ),
    (
        "### ABC Language, *From rooting to bonking: a history of Australian sex "
        "terms*"
    ): _entry_contract(
        sources=(
            "https://www.abc.net.au/news/2018-03-01/from-rooting-to-bonking-a-history-"
            "of-australian-sex-terms/9492856",
        ),
        source_type=(
            "ABC language-history article used as a public linguistic reference for "
            "Australian sexual slang and lexical change."
        ),
        governance="not-required",
        rights=(
            "Registration does not permit reproducing substantial article text or "
            "turning its examples into redistributable benchmark records without "
            "independent provenance and rights analysis.",
        ),
        epistemic=(
            "It does not establish how every Australian uses the term, does not by "
            "itself establish New Zealand usage, and does not make any single phrase a "
            "deterministic sexual reading outside context.",
        ),
        safe=(
            "Build independently authored polysemy pairs that vary social, technical, "
            "botanical, or sports contexts; do not treat the article as proof that every "
            "Australian or New Zealander assigns the same sense to `root`.",
        ),
    ),
    "### Victoria University, *Australian slang dictionary*": _entry_contract(
        sources=(
            "https://www.vu.edu.au/about-vu/news-events/vu-blog/"
            "australian-slang-dictionary",
        ),
        source_type=(
            "Public university educational glossary used for orientation to attested "
            "Australian slang terms and context-sensitive address forms."
        ),
        governance="not-required",
        rights=(
            "Registration does not permit copying the glossary wholesale into the "
            "benchmark, and its entries are not automatically benchmark labels or "
            "licensed dataset examples.",
        ),
        epistemic=(
            "It is not a complete lexicon, a population survey, or evidence that every "
            "listed form is equally current across regions, generations, occupations, "
            "and communities.",
        ),
        safe=(
            "Use the glossary to nominate independently authored lexical and "
            "context-swap tests, while requiring separate evidence for regional, "
            "generational, occupational, or community-specific claims.",
        ),
    ),
    "### r/australia, *Best Aussie slang* community thread": _entry_contract(
        sources=("https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/",),
        source_type=(
            "Public user-generated community discussion retained as orientation and "
            "community-attestation material rather than lexicographic authority."
        ),
        governance="not-required",
        rights=(
            "Registration does not permit bulk copying, redistribution, or conversion "
            "of comments into benchmark examples; any exact quotation requires separate "
            "provenance and rights consideration.",
        ),
        epistemic=(
            "Its participants are self-selected and the thread cannot establish "
            "prevalence, representativeness, national consensus, or authoritative "
            "etymology.",
        ),
        safe=(
            "Use the thread only to generate research leads for independently authored "
            "examples and later source verification; do not use comment popularity or "
            "repetition as a proxy for population prevalence.",
        ),
    ),
    (
        "### Australian Defence multinational communication reports (2022 and 2026)"
    ): _entry_contract(
        sources=(
            "https://www.defence.gov.au/news-events/news/2022-09-08/"
            "communication-key-combined-exercise",
            "https://www.defence.gov.au/news-events/news/2026-06-11/"
            "partner-nations-rehearse-war",
        ),
        source_type=(
            "Official Australian Defence news reports documenting communication "
            "challenges and adaptation during multinational military exercises."
        ),
        governance="not-required",
        rights=(
            "The repository may cite and summarise the reports but does not treat their "
            "prose, imagery, interviews, or exercise material as redistributable "
            "benchmark data.",
        ),
        epistemic=(
            "These reports support communication-friction hypotheses, not claims that "
            "slang functioned as intentional encryption, defeated Allied codebreakers, "
            "or was formally prohibited in Australian-American exercises.",
        ),
        safe=(
            "Create synthetic communication tasks that vary slang density, listener "
            "familiarity, and operational stakes without reproducing exercise dialogue "
            "or claiming that authentic Australian speech is inherently unsafe or "
            "unintelligible.",
        ),
    ),
    "### WWII American-serviceman Australia language guides": _entry_contract(
        sources=(
            "https://www.awm.gov.au/collection/LIB100000077",
            "https://www.awm.gov.au/collection/LIB20571",
            "https://dictionaryofsydney.org/media/5562",
        ),
        source_type=(
            "Australian War Memorial catalogue records for wartime guides and an "
            "archived Dictionary of Sydney record identifying the Australian-slang "
            "section of a United States Army guide."
        ),
        governance="not-required",
        rights=(
            "Registration does not authorise republication of the full booklets, scans, "
            "illustrations, or glossary content as benchmark data.",
        ),
        epistemic=(
            "They support a historical need for cultural and language orientation, but "
            "do not prove that actual joint operations failed because of slang or that "
            "Australian speech operated as an accidental cipher.",
        ),
        safe=(
            "Use the archival records to motivate historically bounded comprehension "
            "experiments and source-governance questions, not to infer contemporary "
            "prevalence or fabricate claims of wartime codebreaking failure.",
        ),
    ),
}
EXPECTED_GOVERNED_ENTRIES = tuple(ENTRY_CONTRACTS)

BATCH_HEADING = "## Registered post-Phase-2 expansion batch"
BATCH_END = "## Priority A: adversarial pragmatics"
CONSULTATION_BOUNDARY = (
    "appropriate consultation, provenance, permissions, and scope limitations"
)

ENTRY_HEADING_PATTERN = re.compile(
    r"(?m)^ {0,3}(?P<heading>### .+?)[ \t]*$"
)
GOVERNANCE_FIELD_PATTERN = re.compile(
    r"(?m)^ {0,3}\*\*Community-specific governance:\*\*"
)
GOVERNANCE_PATTERN = re.compile(
    r"(?m)^ {0,3}\*\*Community-specific governance:\*\*[ \t]*"
    r"(required|not-required):[ \t]*([^\r\n]*\S[^\r\n]*)[ \t]*$"
)
REGISTERED_SOURCE_FIELD_PATTERN = re.compile(
    r"(?m)^ {0,3}\*\*Registered sources?:\*\*"
)
RESEARCH_MAPPING_HEADING_PATTERN = re.compile(
    r"(?m)^ {0,3}(?:Candidate research mappings:|Research mappings:)[ \t]*$"
)
PROJECT_MAPPING_HEADING_PATTERN = re.compile(
    r"(?m)^ {0,3}Relevant project mappings:[ \t]*$"
)
MARKDOWN_LINK_PATTERN = re.compile(
    r"\[[^\]\r\n]*\]\("
    r"[ \t]*(?P<destination><[^>\r\n]+>|[^\s)\r\n]+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?"
    r"[ \t]*\)"
)
BARE_HTTPS_LINE_PATTERN = re.compile(
    r"(?m)^ {0,3}(?:(?:[-+*]|\d{1,9}[.)])[ \t]+)?"
    r"(?P<url>https://\S+)[ \t]*$"
)
AUTOLINK_PATTERN = re.compile(r"<(?P<url>https://[^>\s]+)>")
HOST_LABEL_PATTERN = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
)
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
LIST_CONTAINER_PREFIX_PATTERN = re.compile(
    r"(?:[-+*]|\d{1,9}[.)])[ \t]+"
)


def _mask_non_newline(text: str) -> str:
    """Replace visible characters with spaces while preserving line endings."""
    return "".join(character if character in "\r\n" else " " for character in text)


def _logical_block_line(line: str) -> str:
    """Remove valid quote/list prefixes and at most three block-indent spaces."""
    value = line.rstrip(" \t")
    position = 0

    while position < len(value):
        probe = position
        spaces = 0
        while spaces < 3 and probe < len(value) and value[probe] == " ":
            probe += 1
            spaces += 1

        if probe < len(value) and value[probe] == ">":
            probe += 1
            if probe < len(value) and value[probe] in " \t":
                probe += 1
            position = probe
            continue

        list_prefix = LIST_CONTAINER_PREFIX_PATTERN.match(value, probe)
        if list_prefix:
            position = list_prefix.end()
            continue

        position = probe
        break

    return value[position:]


def _fence_opener(line: str) -> tuple[str, int] | None:
    """Return a valid CommonMark-style fence marker outside indented code."""
    logical = _logical_block_line(line)
    match = FENCE_PATTERN.fullmatch(logical)
    if not match:
        return None

    marker = match.group("fence")
    info = match.group("info")
    if marker[0] == "`" and "`" in info:
        return None
    return marker[0], len(marker)


def _is_fence_closer(line: str, character: str, minimum_length: int) -> bool:
    """Return whether line closes the active fence."""
    logical = _logical_block_line(line)
    return bool(
        re.fullmatch(
            rf"{re.escape(character)}{{{minimum_length},}}[ \t]*",
            logical,
        )
    )


def _mask_comment_segment(characters: list[str], start: int, end: int) -> None:
    """Mask one comment segment in-place while preserving line endings."""
    for index in range(start, end):
        if characters[index] not in "\r\n":
            characters[index] = " "


def _mask_html_comments_on_line(
    raw_line: str,
    *,
    in_comment: bool,
) -> tuple[str, bool]:
    """Mask HTML comments on a non-fenced line and return the next comment state."""
    characters = list(raw_line)
    position = 0

    while position < len(raw_line):
        if in_comment:
            canonical = raw_line.find("-->", position)
            alternate = raw_line.find("--!>", position)
            candidates = [index for index in (canonical, alternate) if index >= 0]
            if not candidates:
                _mask_comment_segment(characters, position, len(raw_line))
                return "".join(characters), True

            close_start = min(candidates)
            close_length = 4 if raw_line.startswith("--!>", close_start) else 3
            close_end = close_start + close_length
            _mask_comment_segment(characters, position, close_end)
            position = close_end
            in_comment = False
            continue

        opener = raw_line.find("<!--", position)
        if opener < 0:
            break
        in_comment = True
        position = opener

    return "".join(characters), in_comment


def _markdown_views(text: str) -> tuple[str, str]:
    """Return rendered and structural views with exact character offsets preserved."""
    rendered_parts: list[str] = []
    structural_parts: list[str] = []
    in_comment = False
    fence_character: str | None = None
    fence_length = 0

    for raw_line in text.splitlines(keepends=True):
        line_without_ending = raw_line.rstrip("\r\n")

        if fence_character is not None:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            if _is_fence_closer(
                line_without_ending,
                fence_character,
                fence_length,
            ):
                fence_character = None
                fence_length = 0
            continue

        if not in_comment:
            opener = _fence_opener(line_without_ending)
            if opener is not None:
                fence_character, fence_length = opener
                rendered_parts.append(raw_line)
                structural_parts.append(_mask_non_newline(raw_line))
                continue

        rendered_line, in_comment = _mask_html_comments_on_line(
            raw_line,
            in_comment=in_comment,
        )
        rendered_parts.append(rendered_line)
        structural_parts.append(rendered_line)

    return "".join(rendered_parts), "".join(structural_parts)


def _rendered_registry_text(text: str) -> str:
    """Return comment-masked Markdown while preserving fenced-code payload."""
    rendered, _ = _markdown_views(text)
    return rendered


def _structural_registry_text(text: str) -> str:
    """Return Markdown with comments and fenced regions masked."""
    _, structural = _markdown_views(text)
    return structural


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
        return False
    if len(labels) < 2:
        return False
    return all(label and HOST_LABEL_PATTERN.fullmatch(label) for label in labels)


def _usable_https_destinations(text: str) -> tuple[str, ...]:
    """Extract usable structural HTTPS destinations, excluding titles and code."""
    structure = _structural_registry_text(text)
    destinations: list[str] = []

    for match in MARKDOWN_LINK_PATTERN.finditer(structure):
        destination = match.group("destination").strip("<>")
        if _is_usable_https_destination(destination):
            destinations.append(destination)

    without_links = MARKDOWN_LINK_PATTERN.sub("", structure)
    for match in AUTOLINK_PATTERN.finditer(without_links):
        destination = match.group("url")
        if _is_usable_https_destination(destination):
            destinations.append(destination)

    without_links = AUTOLINK_PATTERN.sub("", without_links)
    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destination = match.group("url").rstrip(".,;:!?")
        if _is_usable_https_destination(destination):
            destinations.append(destination)

    return tuple(destinations)


def _registered_batch(corpus: str) -> str:
    """Return the rendered governed batch, using structural boundaries."""
    rendered, structure = _markdown_views(corpus)
    start = structure.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = structure.index(BATCH_END, start)
    return rendered[start:end]


def _registered_sections(corpus: str) -> dict[str, str]:
    """Discover every structural registered entry and return rendered section text."""
    batch = _registered_batch(corpus)
    rendered, structure = _markdown_views(batch)
    matches = list(ENTRY_HEADING_PATTERN.finditer(structure))
    assert matches, "registered post-Phase-2 batch contains no entries"

    headings = [match.group("heading") for match in matches]
    duplicates = sorted(
        heading for heading, count in Counter(headings).items() if count > 1
    )
    assert not duplicates, f"duplicate registered-entry headings: {duplicates}"

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group("heading")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(batch)
        sections[heading] = rendered[match.start():end]
    return sections


def _scalar_value(entry: str, section: str, field: str) -> str:
    """Return the unique structural non-whitespace value for a mandatory field."""
    structure = _structural_registry_text(section)
    prefix = rf"(?m)^ {{0,3}}{re.escape(field)}"
    occurrences = list(re.finditer(prefix, structure))
    assert len(occurrences) == 1, (
        f"{entry} must contain exactly one mandatory field {field}"
    )

    match = re.search(
        rf"{prefix}[ \t]*([^\r\n]*\S[^\r\n]*)[ \t]*$",
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
    rendered = _rendered_registry_text(block)
    fence_character: str | None = None
    fence_length = 0

    for raw_line in rendered.splitlines():
        logical = _logical_block_line(raw_line)

        if fence_character is not None:
            if _is_fence_closer(raw_line, fence_character, fence_length):
                fence_character = None
                fence_length = 0
                continue
            if logical.strip():
                return True
            continue

        if not logical.strip():
            continue

        opener = _fence_opener(raw_line)
        if opener is not None:
            fence_character, fence_length = opener
            continue

        line = logical.strip()
        if re.fullmatch(r"(?:Candidate research mappings:|Research mappings:)", line):
            continue
        if line == "Relevant project mappings:":
            continue
        if re.fullmatch(r"#{1,6}[ \t]+.+", line):
            continue
        if THEMATIC_BREAK_PATTERN.fullmatch(line):
            continue
        if re.fullmatch(r"(?:[-+*]|\d{1,9}[.)])", line):
            continue
        if re.fullmatch(r"\*\*[^*]+:\*\*(?:[ \t].*)?", line):
            continue
        return True

    return False


def _require_mapping_block(entry: str, section: str) -> None:
    """Require unique, non-empty research and project mapping blocks."""
    rendered, structure = _markdown_views(section)
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
        rf"(?m)^ {{0,3}}{re.escape(SAFE_FIELD)}",
        structure[project_headings[0].end():],
    )
    assert safe_heading, f"{entry} is missing the safe benchmark abstraction field"
    project_start_value = project_headings[0].end()
    project_end = project_start_value + safe_heading.start()
    project_block = rendered[project_start_value:project_end]
    assert _has_non_heading_content(project_block), (
        f"{entry} has empty project mappings"
    )


def _require_registered_source_link(entry: str, section: str) -> tuple[str, ...]:
    """Require one structural source field and return its usable destinations."""
    structure = _structural_registry_text(section)
    source_fields = list(REGISTERED_SOURCE_FIELD_PATTERN.finditer(structure))
    assert len(source_fields) == 1, (
        f"{entry} must contain exactly one registered-source field"
    )

    source_block = re.search(
        r"(?ms)^ {0,3}\*\*Registered sources?:\*\*[ \t]*(.*?)"
        r"(?=^ {0,3}\*\*[^*\n]+:\*\*|\Z)",
        structure,
    )
    assert source_block, f"{entry} has an empty registered-source field"
    source_value = source_block.group(1)
    assert source_value.strip(), f"{entry} has an empty registered-source field"

    destinations = _usable_https_destinations(source_value)
    assert destinations, (
        f"{entry} has no usable HTTPS destination in its registered-source field"
    )
    assert len(destinations) == len(set(destinations)), (
        f"{entry} contains duplicate registered-source destinations"
    )
    return destinations


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
        safe_use = _scalar_value(entry, section, SAFE_FIELD)
        assert CONSULTATION_BOUNDARY in safe_use, (
            f"{entry} is missing its community-specific consultation boundary "
            "from the safe benchmark abstraction field"
        )
    return value


def _require_pinned_entry_contract(
    entry: str,
    *,
    classification: str,
    scalar_values: dict[str, str],
    destinations: tuple[str, ...],
) -> None:
    """Preserve each adopted entry's provenance and load-bearing contract clauses."""
    contract = ENTRY_CONTRACTS.get(entry)
    assert contract is not None, f"{entry} has no pinned source-governance contract"

    expected_classification = contract["governance"]
    assert classification == expected_classification, (
        f"{entry} must remain classified as {expected_classification}"
    )

    expected_destinations = set(contract[SOURCES_KEY])
    actual_destinations = set(destinations)
    assert actual_destinations == expected_destinations, (
        f"{entry} registered-source destinations changed: "
        f"expected {sorted(expected_destinations)!r}, got {sorted(actual_destinations)!r}"
    )

    for field in PINNED_SCALAR_FIELDS:
        expected_clauses = contract[field]
        value = scalar_values[field]
        for clause in expected_clauses:
            assert clause in value, (
                f"{entry} is missing a pinned {field} clause: {clause!r}"
            )


def _validate_registered_entry(entry: str, section: str) -> None:
    """Validate one adopted registry entry against structural and pinned contracts."""
    destinations = _require_registered_source_link(entry, section)
    scalar_values = {
        field: _scalar_value(entry, section, field)
        for field in SCALAR_FIELDS
    }
    classification = _require_community_governance(entry, section)
    _require_pinned_entry_contract(
        entry,
        classification=classification,
        scalar_values=scalar_values,
        destinations=destinations,
    )
    _require_mapping_block(entry, section)


def test_post_phase2_registry_batch_preserves_governance_contract():
    corpus = CORPUS.read_text(encoding="utf-8")

    assert "## Registration contract for new sources" in corpus
    assert BATCH_HEADING in corpus
    assert (
        "Every adopted post-Phase-2 registry entry must record all of the following fields"
        in corpus
    )
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


def test_fenced_comment_literals_do_not_hide_visible_duplicate_source_field():
    section = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "```text\n<!--\n```\n\n"
        "**Registered source:** https://example.com/other\n\n"
        "```text\n-->\n```\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


def test_four_space_indented_fence_markers_do_not_mask_visible_metadata():
    section = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "    ```\n"
        "**Registered source:** https://example.com/other\n"
        "    ```\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


@pytest.mark.parametrize(
    ("section", "field", "message"),
    (
        (
            "### Example\n\n**Source type:**\n\n"
            "**Rights and provenance boundary:** value\n",
            SOURCE_TYPE_FIELD,
            "empty mandatory field",
        ),
        (
            "### Example\n\n"
            "**Rights and provenance boundary:** restrictive value\n\n"
            "**Rights and provenance boundary:** replacement\n",
            RIGHTS_FIELD,
            "exactly one mandatory field",
        ),
        (
            "### Example\n\n"
            "**Rights and provenance boundary:** <!-- omitted -->\n",
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
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "**Registered sources:** https://example.com/other\n\n"
        "**Source type:** example\n",
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "   **Registered source:** https://example.com/other\n\n"
        "**Source type:** example\n",
    ),
)
def test_registered_source_rejects_duplicate_fields(section: str):
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


@pytest.mark.parametrize(
    "section",
    (
        "### Example\n\n"
        "**Registered source:** <!-- https://example.com/source -->\n\n"
        "**Source type:** example\n",
        "### Example\n\n"
        "**Registered source:** <!-- https://example.com/source --!>\n\n"
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
        "### Example\n\n"
        "Research mappings:\n\n"
        "Research mappings:\n\n"
        "Relevant project mappings:\n\n"
        "Relevant project mappings:\n\n"
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
        "Research mappings:\n"
        "> ```text\n"
        "> substantive mapping\n"
        "> ```\n\n"
        "Relevant project mappings:\n"
        "> ```\n"
        "> project mapping\n"
        "> ```\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    _require_mapping_block("### Example", section)


def test_mapping_blocks_accept_content_inside_list_fence():
    section = (
        "### Example\n\n"
        "Research mappings:\n"
        "- ```text\n"
        "  substantive mapping\n"
        "  ```\n\n"
        "Relevant project mappings:\n"
        "1. ~~~\n"
        "   project mapping\n"
        "   ~~~\n\n"
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
        rf"(?m)^ {{0,3}}{re.escape(field)}[^\r\n]*$",
        f"{field} {replacement}",
        section,
        count=1,
    )

    with pytest.raises(AssertionError, match="missing a pinned"):
        _validate_registered_entry(entry, mutated)


def test_source_type_and_relevance_clause_is_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^ {{0,3}}{re.escape(SOURCE_TYPE_FIELD)}[^\r\n]*$",
        f"{SOURCE_TYPE_FIELD} unknown",
        section,
        count=1,
    )

    with pytest.raises(AssertionError, match="missing a pinned"):
        _validate_registered_entry(entry, mutated)


def test_registered_source_destination_set_is_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "https://iview.abc.net.au/show/black-comedy",
        "https://www.wikipedia.org/",
        1,
    )

    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_multisource_entry_cannot_drop_an_adopted_destination():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *The Castle* (1997)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "- https://www.nfsa.gov.au/collection/item/castle-fathers-day\n",
        "",
        1,
    )

    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_community_governance_requires_same_line_rationale():
    section = (
        "### Example\n\n"
        "**Community-specific governance:** not-required:\n\n"
        "Candidate research mappings:\n"
        "- example\n"
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
    with pytest.raises(
        AssertionError,
        match="exactly one community-specific governance field",
    ):
        _require_community_governance("### Example", section)
