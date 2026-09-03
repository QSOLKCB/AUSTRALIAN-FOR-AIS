"""Regression checks for governed research-reference registration."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import html
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
DOI_FIELD = "**DOI:**"
SCALAR_FIELDS = (
    SOURCE_TYPE_FIELD,
    RIGHTS_FIELD,
    EPISTEMIC_FIELD,
    SAFE_FIELD,
)
SOURCES_KEY = "sources"


def _entry_contract(
    *,
    sources: tuple[str, ...],
    source_type: str,
    governance: str,
    rights: str,
    epistemic: str,
    safe: str,
    doi: str | None = None,
) -> dict[str, object]:
    """Build one explicit governed-entry contract."""
    contract: dict[str, object] = {
        SOURCES_KEY: sources,
        SOURCE_TYPE_FIELD: source_type,
        "governance": governance,
        RIGHTS_FIELD: rights,
        EPISTEMIC_FIELD: epistemic,
        SAFE_FIELD: safe,
    }
    if doi is not None:
        contract[DOI_FIELD] = doi
    return contract


ENTRY_CONTRACTS: dict[str, dict[str, object]] = {
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
            "expression is licensed to this repository by registration."
        ),
        epistemic=(
            "It is not a representative corpus of Aboriginal or Torres Strait "
            "Islander speech, and the programme alone cannot establish "
            "community-wide pragmatic rules."
        ),
        safe=(
            "Any later First Nations-specific benchmark family requires appropriate "
            "consultation, provenance, permissions, and scope limitations, plus a "
            "documented governance basis."
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
            "character catchphrases, or audiovisual material into benchmark data."
        ),
        epistemic=(
            "It does not establish how suburban Australians, women, working-class "
            "speakers, or any other social category generally speak."
        ),
        safe=(
            "Any class-marked register family remains a hypothesis and requires "
            "appropriate consultation, provenance, permissions, and scope limitations "
            "before it can support community-specific benchmark claims."
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
            "or distinctive character material into benchmark records."
        ),
        epistemic=(
            "It is not evidence that its characters or dialogue represent Australians "
            "generally."
        ),
        safe=(
            "Because the film's portrayal is class-marked, any later class-register or "
            "community-specific benchmark family derived from these hypotheses "
            "requires appropriate consultation, provenance, permissions, and scope "
            "limitations before it can support claims about a community."
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
            "not be redistributed as benchmark data."
        ),
        epistemic=(
            "Political satire is analysed structurally; registration does not endorse "
            "the political position of any sketch or turn satire into factual evidence "
            "about its targets."
        ),
        safe="Do not reproduce programme jokes or political conclusions.",
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
            "accents-as-text, catchphrases, character material, or audiovisual content."
        ),
        epistemic=(
            "It must not be treated as representative evidence of Greek-Australian, "
            "migrant, or multicultural speech, and historical portrayals must not be "
            "projected onto contemporary communities."
        ),
        safe=(
            "Any community-specific benchmark family requires appropriate "
            "consultation, provenance, permissions, and scope limitations."
        ),
    ),
    (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    ): _entry_contract(
        sources=("https://europeanjournalofhumour.org/ejhr/article/view/560",),
        source_type="Peer-reviewed article in The European Journal of Humour Research.",
        governance="not-required",
        rights=(
            "Citation and analysis do not imply permission to redistribute the full "
            "article in this repository."
        ),
        epistemic=(
            "It does not provide a national-character lookup table or individual-level "
            "ground truth."
        ),
        safe="Do not convert its cultural comparisons into deterministic labels.",
    ),
    (
        "### Hurley (2025), *Laughter with purpose: how First Nations Australian "
        "comedians use humour to engage, educate, and empower audiences*"
    ): _entry_contract(
        sources=(
            "https://www.tandfonline.com/doi/full/10.1080/2040610X.2025.2538977",
        ),
        source_type=(
            "Peer-reviewed article in Comedy Studies using a culturally grounded "
            "qualitative methodology centred on Aboriginal and Torres Strait Islander "
            "comedians, writers, and performers."
        ),
        governance="required",
        rights=(
            "Publisher access does not license this repository to reproduce the "
            "article, interview material, quoted performances, or community-specific "
            "language."
        ),
        epistemic=(
            "It is a stronger basis for understanding research-governance requirements "
            "than outsider summaries, but it still does not authorise this project to "
            "create First Nations benchmark ground truth without appropriate community "
            "involvement."
        ),
        safe=(
            "Any First Nations-specific annotation protocol or benchmark family "
            "requires appropriate consultation, provenance, permissions, and scope "
            "limitations and must preserve the paper's emphasis on cultural specificity "
            "and self-determination."
        ),
    ),
    "### Slade, *Australian Sketch Comedy Field Theory* (ASCFT)": _entry_contract(
        sources=("https://doi.org/10.5281/zenodo.17781653",),
        source_type=(
            "Project-authored formal-analysis paper supplied to the project by Trent "
            "Slade / QSOL-IMC."
        ),
        governance="not-required",
        rights=(
            "Registration does not place the full paper, its distinctive wording, "
            "equations, source-derived examples, transcripts, or referenced comedy "
            "material under the repository licence."
        ),
        epistemic=(
            "They do not by themselves establish literal physical ontology, "
            "empirically validated mechanisms, universal laws of Australian humour, or "
            "population-level cultural ground truth."
        ),
        safe=(
            "Do not copy source dialogue, transcript wording, distinctive jokes, "
            "equations as benchmark labels, or source-derived media expression."
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
            "records; benchmark examples must remain independently authored."
        ),
        epistemic=(
            "They do not establish a shared modern national identity, prove a "
            "cousin-like relationship between individual Australians and New "
            "Zealanders, or determine the pragmatic meaning of contemporary "
            "trans-Tasman teasing."
        ),
        safe=(
            "Use the records only to document historical context around Australia and "
            "New Zealand; do not infer modern affinity, hostility, shared identity, or "
            "pragmatic licence from constitutional history alone."
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
            "independent provenance and rights analysis."
        ),
        epistemic=(
            "It does not establish how every Australian uses the term, does not by "
            "itself establish New Zealand usage, and does not make any single phrase a "
            "deterministic sexual reading outside context."
        ),
        safe=(
            "Build independently authored polysemy pairs that vary social, technical, "
            "botanical, or sports contexts; do not treat the article as proof that every "
            "Australian or New Zealander assigns the same sense to root."
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
            "licensed dataset examples."
        ),
        epistemic=(
            "It is not a complete lexicon, a population survey, or evidence that every "
            "listed form is equally current across regions, generations, occupations, "
            "and communities."
        ),
        safe=(
            "Use the glossary to nominate independently authored lexical and "
            "context-swap tests, while requiring separate evidence for regional, "
            "generational, occupational, or community-specific claims."
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
            "provenance and rights consideration."
        ),
        epistemic=(
            "Its participants are self-selected and the thread cannot establish "
            "prevalence, representativeness, national consensus, or authoritative "
            "etymology."
        ),
        safe=(
            "Use the thread only to generate research leads for independently authored "
            "examples and later source verification; do not use comment popularity or "
            "repetition as a proxy for population prevalence."
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
            "benchmark data."
        ),
        epistemic=(
            "These reports support communication-friction hypotheses, not claims that "
            "slang functioned as intentional encryption, defeated Allied codebreakers, "
            "or was formally prohibited in Australian-American exercises."
        ),
        safe=(
            "Create synthetic communication tasks that vary slang density, listener "
            "familiarity, and operational stakes without reproducing exercise dialogue "
            "or claiming that authentic Australian speech is inherently unsafe or "
            "unintelligible."
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
            "illustrations, or glossary content as benchmark data."
        ),
        epistemic=(
            "They support a historical need for cultural and language orientation, but "
            "do not prove that actual joint operations failed because of slang or that "
            "Australian speech operated as an accidental cipher."
        ),
        safe=(
            "Use the archival records to motivate historically bounded comprehension "
            "experiments and source-governance questions, not to infer contemporary "
            "prevalence or fabricate claims of wartime codebreaking failure."
        ),
    ),
}
EXPECTED_GOVERNED_ENTRIES = tuple(ENTRY_CONTRACTS)

BATCH_HEADING = "## Registered post-Phase-2 expansion batch"
BATCH_END = "## Priority A: adversarial pragmatics"
CONTRACT_HEADING = "## Registration contract for new sources"
CONTRACT_SENTENCE = (
    "Every adopted post-Phase-2 registry entry must record all of the following fields"
)
CONSULTATION_BOUNDARY = (
    "appropriate consultation, provenance, permissions, and scope limitations"
)

ENTRY_HEADING_PATTERN = re.compile(r"(?m)^ {0,3}(?P<heading>### .+?)[ \t]*$")
GOVERNANCE_FIELD_PATTERN = re.compile(
    r"(?m)^[ \t]*\*\*Community-specific governance:\*\*"
)
GOVERNANCE_PATTERN = re.compile(
    r"(?m)^[ \t]*\*\*Community-specific governance:\*\*[ \t]*"
    r"(required|not-required):(?P<rationale>[^\r\n]*)$"
)
REGISTERED_SOURCE_FIELD_PATTERN = re.compile(
    r"(?m)^[ \t]*\*\*Registered sources?:\*\*"
)
RESEARCH_MAPPING_HEADING_PATTERN = re.compile(
    r"(?m)^ {0,3}(?:Candidate research mappings:|Research mappings:)[ \t]*$"
)
PROJECT_MAPPING_HEADING_PATTERN = re.compile(
    r"(?m)^ {0,3}Relevant project mappings:[ \t]*$"
)
MARKDOWN_LINK_PATTERN = re.compile(
    r"(?P<image>!?)\[(?P<label>[^\]\r\n]*)\]\("
    r"[ \t]*(?P<destination><[^>\r\n]+>|[^\s)\r\n]+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?"
    r"[ \t]*\)"
)
BARE_HTTPS_LINE_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:(?:[-+*]|\d{1,9}[.)])[ \t]+)?"
    r"(?P<url>https://\S+)[ \t]*$"
)
AUTOLINK_PATTERN = re.compile(r"<(?P<url>https://[^>\s]+)>")
LINK_REFERENCE_DEFINITION_PATTERN = re.compile(
    r"\[[^\]\r\n]+\]:[ \t]*(?:<[^>\r\n]+>|\S+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?[ \t]*"
)
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
LIST_CONTAINER_PREFIX_PATTERN = re.compile(r"(?:[-+*]|\d{1,9}[.)])[ \t]+")
HTML_TAG_PATTERN = re.compile(
    r"</?[A-Za-z][^>]*>|<![A-Za-z][^>]*>|<\?[\s\S]*?\?>"
)


@dataclass(frozen=True)
class LineContext:
    quote_depth: int
    after_quotes: str
    leading_spaces: int
    logical: str
    list_indent: int | None
    indented_code: bool


@dataclass(frozen=True)
class FenceState:
    character: str
    minimum_length: int
    quote_depth: int
    list_indent: int | None


def _mask_non_newline(text: str) -> str:
    """Replace visible characters with spaces while preserving line endings."""
    return "".join(character if character in "\r\n" else " " for character in text)


def _line_context(line: str) -> LineContext:
    """Describe CommonMark quote/list prefixes without erasing code indentation."""
    value = line.rstrip("\r\n")
    position = 0
    quote_depth = 0

    while True:
        probe = position
        spaces = 0
        while spaces < 3 and probe < len(value) and value[probe] == " ":
            probe += 1
            spaces += 1
        if probe >= len(value) or value[probe] != ">":
            break
        quote_depth += 1
        probe += 1
        if probe < len(value) and value[probe] in " \t":
            probe += 1
        position = probe

    after_quotes = value[position:]
    leading_spaces = len(after_quotes) - len(after_quotes.lstrip(" "))
    list_indent: int | None = None
    logical_start = min(leading_spaces, 3)

    if leading_spaces <= 3:
        marker = LIST_CONTAINER_PREFIX_PATTERN.match(after_quotes, leading_spaces)
        if marker:
            list_indent = marker.end()
            logical_start = marker.end()

    indented_code = list_indent is None and leading_spaces >= 4
    logical = after_quotes[logical_start:]
    return LineContext(
        quote_depth=quote_depth,
        after_quotes=after_quotes,
        leading_spaces=leading_spaces,
        logical=logical,
        list_indent=list_indent,
        indented_code=indented_code,
    )


def _line_opens_paragraph(line: str) -> bool:
    """Return whether a rendered line can keep a CommonMark paragraph open."""
    context = _line_context(line)
    logical = context.logical.strip()
    if not logical or context.indented_code:
        return False
    if re.fullmatch(r"#{1,6}(?:[ \t]+.*)?", logical):
        return False
    if THEMATIC_BREAK_PATTERN.fullmatch(logical):
        return False
    if LINK_REFERENCE_DEFINITION_PATTERN.fullmatch(logical):
        return False
    return True


def _fence_opener(line: str) -> FenceState | None:
    """Return a valid fence opener and its containing quote/list context."""
    context = _line_context(line)
    if context.indented_code:
        return None
    match = FENCE_PATTERN.fullmatch(context.logical.rstrip(" \t"))
    if not match:
        return None
    marker = match.group("fence")
    info = match.group("info")
    if marker[0] == "`" and "`" in info:
        return None
    return FenceState(
        character=marker[0],
        minimum_length=len(marker),
        quote_depth=context.quote_depth,
        list_indent=context.list_indent,
    )


def _fence_container_continues(line: str, state: FenceState) -> bool:
    """Return whether a nested quote/list fence still owns this source line."""
    if not line.strip():
        return True
    context = _line_context(line)
    if context.quote_depth < state.quote_depth:
        return False
    if state.list_indent is not None:
        if context.quote_depth != state.quote_depth:
            return False
        if context.list_indent is not None:
            return False
        return context.leading_spaces >= state.list_indent
    return True


def _fence_logical_line(line: str, state: FenceState) -> str:
    """Return content inside the active fence's container context."""
    context = _line_context(line)
    if state.list_indent is not None:
        return context.after_quotes[state.list_indent:]
    return context.logical


def _is_fence_closer(line: str, state: FenceState) -> bool:
    """Return whether line closes the active fence."""
    logical = _fence_logical_line(line, state).rstrip(" \t")
    return bool(
        re.fullmatch(
            rf"{re.escape(state.character)}{{{state.minimum_length},}}[ \t]*",
            logical,
        )
    )


def _mask_inline_code_spans(text: str) -> str:
    """Mask same-line Markdown code spans while preserving offsets."""
    characters = list(text)
    position = 0
    while position < len(text):
        if text[position] != "`":
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        marker = text[position:run_end]
        close = text.find(marker, run_end)
        if close < 0:
            position = run_end
            continue
        for index in range(position, close + len(marker)):
            if characters[index] not in "\r\n":
                characters[index] = " "
        position = close + len(marker)
    return "".join(characters)


def _mask_segment(characters: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if characters[index] not in "\r\n":
            characters[index] = " "


def _mask_html_comments_on_line(
    raw_line: str,
    *,
    in_comment: bool,
) -> tuple[str, bool]:
    """Mask HTML comments using an inline-code-masked scan view."""
    scan = _mask_inline_code_spans(raw_line)
    characters = list(raw_line)
    position = 0

    while position < len(raw_line):
        if in_comment:
            canonical = scan.find("-->", position)
            alternate = scan.find("--!>", position)
            candidates = [index for index in (canonical, alternate) if index >= 0]
            if not candidates:
                _mask_segment(characters, position, len(raw_line))
                return "".join(characters), True
            close_start = min(candidates)
            close_length = 4 if scan.startswith("--!>", close_start) else 3
            close_end = close_start + close_length
            _mask_segment(characters, position, close_end)
            position = close_end
            in_comment = False
            continue

        opener = scan.find("<!--", position)
        if opener < 0:
            break
        in_comment = True
        position = opener

    return "".join(characters), in_comment


def _markdown_views(text: str) -> tuple[str, str]:
    """Return rendered and structural views with exact offsets preserved."""
    rendered_parts: list[str] = []
    structural_parts: list[str] = []
    in_comment = False
    fence: FenceState | None = None
    paragraph_open = False

    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            paragraph_open = False

        while fence is not None and not _fence_container_continues(line, fence):
            fence = None

        if fence is not None:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            if _is_fence_closer(line, fence):
                fence = None
            continue

        if in_comment:
            rendered_line, in_comment = _mask_html_comments_on_line(
                raw_line,
                in_comment=True,
            )
            rendered_parts.append(rendered_line)
            structural_parts.append(_mask_inline_code_spans(rendered_line))
            continue

        context = _line_context(line)
        if context.indented_code:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            continue

        opener = _fence_opener(line)
        if opener is not None:
            fence = opener
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            continue

        rendered_line, in_comment = _mask_html_comments_on_line(
            raw_line,
            in_comment=False,
        )
        rendered_parts.append(rendered_line)
        structural_parts.append(_mask_inline_code_spans(rendered_line))

    return "".join(rendered_parts), "".join(structural_parts)


def _rendered_registry_text(text: str) -> str:
    rendered, _ = _markdown_views(text)
    return rendered


def _structural_registry_text(text: str) -> str:
    _, structural = _markdown_views(text)
    return structural


def _render_inline_code_spans(text: str) -> str:
    """Replace same-line code spans with the text they visibly render."""
    parts: list[str] = []
    position = 0
    while position < len(text):
        if text[position] != "`":
            parts.append(text[position])
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        marker = text[position:run_end]
        close = text.find(marker, run_end)
        if close < 0:
            parts.append(marker)
            position = run_end
            continue
        parts.append(text[run_end:close].strip(" "))
        position = close + len(marker)
    return "".join(parts)


def _visible_inline_text(text: str) -> str:
    """Reduce Markdown/HTML metadata to its rendered visible text."""
    rendered = _rendered_registry_text(text)
    visible = _render_inline_code_spans(rendered)
    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = HTML_TAG_PATTERN.sub(" ", visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return " ".join(visible.split())
def _normalise_https_destination(candidate: str) -> str | None:
    value = candidate.strip().strip("<>").rstrip(".,;:!?")
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return None

    parsed_hostname = parsed.hostname
    if (
        parsed.scheme != "https"
        or not parsed_hostname
        or parsed.username is not None
        or parsed.password is not None
        or port is not None and port <= 0
    ):
        return None

    hostname = parsed_hostname.rstrip(".").lower()
    if not hostname or not any(character.isalnum() for character in hostname):
        return None

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        if not address.is_global:
            return None
    else:
        if any(
            hostname == suffix or hostname.endswith(f".{suffix}")
            for suffix in SPECIAL_USE_HOST_SUFFIXES
        ):
            return None
        labels = hostname.split(".")
        if all(NUMERIC_HOST_LABEL_PATTERN.fullmatch(label) for label in labels):
            return None
        if len(labels) < 2:
            return None
        if not all(label and HOST_LABEL_PATTERN.fullmatch(label) for label in labels):
            return None

    return value


def _usable_https_destinations(text: str) -> tuple[str, ...]:
    """Extract usable rendered links while excluding code and link titles."""
    structure = _structural_registry_text(text)
    destinations: list[str] = []

    for match in MARKDOWN_LINK_PATTERN.finditer(structure):
        if match.group("image"):
            continue
        destination = _normalise_https_destination(
            match.group("destination").strip("<>")
        )
        if destination is not None:
            destinations.append(destination)

    without_links = MARKDOWN_LINK_PATTERN.sub("", structure)
    for match in AUTOLINK_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)

    without_links = AUTOLINK_PATTERN.sub("", without_links)
    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)

    return tuple(destinations)


def _registered_batch(corpus: str) -> str:
    rendered, structure = _markdown_views(corpus)
    start = structure.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = structure.index(BATCH_END, start)
    return rendered[start:end]


def _registered_sections(corpus: str) -> dict[str, str]:
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
    rendered, structure = _markdown_views(section)
    prefix = rf"(?m)^[ \t]*{re.escape(field)}"
    occurrences = list(re.finditer(prefix, structure))
    assert len(occurrences) == 1, (
        f"{entry} must contain exactly one mandatory field {field}"
    )
    match = re.search(
        rf"{prefix}(?P<value>[^\r\n]*)$",
        structure,
    )
    assert match, f"{entry} has an empty mandatory field {field}"
    raw_value = rendered[match.start("value"):match.end("value")]
    value = _visible_inline_text(raw_value)
    assert value, f"{entry} has an empty mandatory field {field}"
    return value
def _require_scalar_value(entry: str, section: str, field: str) -> None:
    _scalar_value(entry, section, field)


def _has_non_heading_content(block: str) -> bool:
    rendered = _rendered_registry_text(block)
    fence: FenceState | None = None

    for raw_line in rendered.splitlines():
        while fence is not None and not _fence_container_continues(raw_line, fence):
            fence = None

        if fence is not None:
            if _is_fence_closer(raw_line, fence):
                fence = None
                continue
            if _fence_logical_line(raw_line, fence).strip():
                return True
            continue

        opener = _fence_opener(raw_line)
        if opener is not None:
            fence = opener
            continue

        context = _line_context(raw_line)
        if THEMATIC_BREAK_PATTERN.fullmatch(context.after_quotes.strip()):
            continue
        line = context.logical.strip()
        if not line:
            continue
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
        if _visible_inline_text(line):
            return True

    return False


def _require_mapping_block(entry: str, section: str) -> None:
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
    assert _has_non_heading_content(rendered[research_start:project_start]), (
        f"{entry} has empty research mappings"
    )

    safe_heading = re.search(
        rf"(?m)^ {{0,3}}{re.escape(SAFE_FIELD)}",
        structure[project_headings[0].end():],
    )
    assert safe_heading, f"{entry} is missing the safe benchmark abstraction field"
    project_value_start = project_headings[0].end()
    project_end = project_value_start + safe_heading.start()
    assert _has_non_heading_content(rendered[project_value_start:project_end]), (
        f"{entry} has empty project mappings"
    )


def _require_registered_source_link(entry: str, section: str) -> tuple[str, ...]:
    rendered, structure = _markdown_views(section)
    source_fields = list(REGISTERED_SOURCE_FIELD_PATTERN.finditer(structure))
    assert len(source_fields) == 1, (
        f"{entry} must contain exactly one registered-source field"
    )
    source_block = re.search(
        r"(?ms)^[ \t]*\*\*Registered sources?:\*\*(.*?)"
        r"(?=^[ \t]*\*\*[^*\n]+:\*\*|\Z)",
        structure,
    )
    assert source_block, f"{entry} has an empty registered-source field"
    source_value = rendered[source_block.start(1):source_block.end(1)]
    assert _visible_inline_text(source_value), (
        f"{entry} has an empty registered-source field"
    )

    destinations = _usable_https_destinations(source_value)
    assert destinations, (
        f"{entry} has no usable HTTPS destination in its registered-source field"
    )
    assert len(destinations) == len(set(destinations)), (
        f"{entry} contains duplicate registered-source destinations"
    )
    return destinations
def _require_community_governance(entry: str, section: str) -> str:
    rendered, structure = _markdown_views(section)
    fields = list(GOVERNANCE_FIELD_PATTERN.finditer(structure))
    assert len(fields) == 1, (
        f"{entry} must contain exactly one community-specific governance field"
    )
    classification = GOVERNANCE_PATTERN.search(structure)
    assert classification, (
        f"{entry} has an invalid community-specific governance classification or rationale"
    )
    raw_rationale = rendered[
        classification.start("rationale"):classification.end("rationale")
    ]
    rationale = _visible_inline_text(raw_rationale)
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

    for field in SCALAR_FIELDS:
        expected_clause = str(contract[field])
        assert expected_clause in scalar_values[field], (
            f"{entry} is missing a pinned {field} clause: {expected_clause!r}"
        )


def _validate_registered_entry(entry: str, section: str) -> None:
    destinations = _require_registered_source_link(entry, section)
    scalar_values = {
        field: _scalar_value(entry, section, field)
        for field in SCALAR_FIELDS
    }
    contract = ENTRY_CONTRACTS.get(entry)
    assert contract is not None, f"{entry} has no pinned source-governance contract"
    if DOI_FIELD in contract:
        doi_value = _scalar_value(entry, section, DOI_FIELD)
        assert doi_value == contract[DOI_FIELD], (
            f"{entry} DOI metadata changed: expected {contract[DOI_FIELD]!r}, "
            f"got {doi_value!r}"
        )
    else:
        structure = _structural_registry_text(section)
        assert not re.search(
            rf"(?m)^[ \t]*{re.escape(DOI_FIELD)}",
            structure,
        ), f"{entry} has unpinned DOI metadata"
    classification = _require_community_governance(entry, section)
    _require_pinned_entry_contract(
        entry,
        classification=classification,
        scalar_values=scalar_values,
        destinations=destinations,
    )
    _require_mapping_block(entry, section)


def _validate_registry_corpus(corpus: str) -> None:
    structure = _structural_registry_text(corpus)
    assert CONTRACT_HEADING in structure, "rendered registration contract is missing"
    assert CONTRACT_SENTENCE in structure, "rendered registration contract is incomplete"
    assert BATCH_HEADING in structure, "rendered governed batch heading is missing"
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in structure

    sections = _registered_sections(corpus)
    assert set(sections) == set(ENTRY_CONTRACTS), (
        "every rendered governed entry must have an explicit pinned source contract"
    )
    for entry, section in sections.items():
        _validate_registered_entry(entry, section)


def test_post_phase2_registry_batch_preserves_governance_contract():
    _validate_registry_corpus(CORPUS.read_text(encoding="utf-8"))


@pytest.mark.parametrize("wrapper", ("comment", "fence"))
def test_registration_contract_must_remain_rendered(wrapper: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(CONTRACT_HEADING)
    end = corpus.index(BATCH_HEADING, start)
    contract = corpus[start:end]
    if wrapper == "comment":
        hidden = f"<!--\n{contract}\n-->\n"
    else:
        hidden = f"````\n{contract}\n````\n"
    mutated = corpus[:start] + hidden + corpus[end:]
    with pytest.raises(AssertionError, match="rendered registration contract"):
        _validate_registry_corpus(mutated)


@pytest.mark.parametrize("wrapper", ("comment", "fence"))
def test_registry_discovery_ignores_hidden_complete_entry(wrapper: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[heading]
    hidden = (
        f"<!--\n{section}\n-->\n"
        if wrapper == "comment"
        else f"````\n{section}\n````\n"
    )
    mutated = corpus.replace(section, hidden, 1)
    assert heading not in _registered_sections(mutated)


def test_registry_fields_ignore_fenced_and_inline_code_metadata():
    fenced = (
        "### Example\n\n```\n"
        "**Registered source:** https://example.com/source\n"
        "```\n\n**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", fenced)

    inline = (
        "### Example\n\n"
        "**Registered source:** `[source](https://example.com/source)`\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _require_registered_source_link("### Example", inline)


def test_indented_code_comment_opener_does_not_hide_visible_duplicate():
    section = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "    <!--\n"
        "**Registered source:** https://example.com/other\n"
        "    -->\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


def test_fenced_comment_literals_do_not_hide_visible_duplicate():
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


@pytest.mark.parametrize(
    "opener, closer",
    (("- ```", "  ```"), ("> ```", "> ```")),
)
def test_nested_fence_ends_when_its_container_ends(opener: str, closer: str):
    section = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        f"{opener}\n"
        "**Registered source:** https://example.com/other\n"
        f"{closer}\n\n"
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
        (
            "### Example\n\n"
            "**Rights and provenance boundary:** <!-- hidden value -->\n",
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
        "![source](https://example.com/source)",
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
        "- ```\n  ```",
        "1. ~~~\n   ~~~",
        "> - ```\n>   ```",
        "<br>",
        "<div></div>",
        "&nbsp;",
        "<span> &nbsp; </span>",
        "- <!-- placeholder -->",
        "<!--\n- placeholder\n-->",
        "[placeholder]: https://example.com",
    ),
)
def test_mapping_blocks_reject_empty_rendered_content(container: str):
    section = (
        "### Example\n\n"
        f"Research mappings:\n{container}\n\n"
        f"Relevant project mappings:\n{container}\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="empty research mappings"):
        _require_mapping_block("### Example", section)


def test_mapping_blocks_accept_real_nested_fence_and_html_content():
    section = (
        "### Example\n\n"
        "Research mappings:\n"
        "- ```text\n"
        "  substantive mapping\n"
        "  ```\n\n"
        "Relevant project mappings:\n"
        "> <div>project mapping</div>\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
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


def test_pinned_clause_cannot_hide_in_markdown_link_title():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    expected = str(ENTRY_CONTRACTS[entry][SOURCE_TYPE_FIELD])
    mutated = re.sub(
        rf"(?m)^ {{0,3}}{re.escape(SOURCE_TYPE_FIELD)}[^\r\n]*$",
        f'{SOURCE_TYPE_FIELD} [unknown](# "{expected}")',
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


def test_community_governance_requires_visible_same_line_rationale():
    missing = (
        "### Example\n\n"
        "**Community-specific governance:** not-required:\n\n"
        "Candidate research mappings:\n- example\n"
    )
    with pytest.raises(AssertionError, match="invalid community-specific governance"):
        _require_community_governance("### Example", missing)

    hidden = (
        "### Example\n\n"
        "**Community-specific governance:** not-required: <!-- hidden -->\n"
    )
    with pytest.raises(AssertionError, match="invalid community-specific governance"):
        _require_community_governance("### Example", hidden)

def test_inline_code_remains_visible_field_text_but_not_a_link():
    scalar = (
        "### Example\n\n"
        "**Rights and provenance boundary:** `visible value`\n"
    )
    assert _scalar_value("### Example", scalar, RIGHTS_FIELD) == "visible value"

    governance = (
        "### Example\n\n"
        "**Community-specific governance:** not-required: `visible rationale`\n"
    )
    assert _require_community_governance("### Example", governance) == "not-required"

    source = (
        "### Example\n\n"
        "**Registered source:** `[source](https://example.com/source)`\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _require_registered_source_link("### Example", source)

def test_paragraph_continuation_cannot_hide_indented_metadata():
    duplicate_source = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n"
        "    **Registered source:** https://example.com/other\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", duplicate_source)

    duplicate_scalar = (
        "### Example\n\n"
        "**Rights and provenance boundary:** restrictive value\n"
        "    **Rights and provenance boundary:** contradictory value\n"
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _scalar_value("### Example", duplicate_scalar, RIGHTS_FIELD)


def test_published_doi_metadata_is_pinned_and_unique():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    fake = section.replace(
        "https://doi.org/10.7592/EJHR2021.9.4.560",
        "https://doi.org/10.0000/invented",
        1,
    )
    with pytest.raises(AssertionError, match="DOI metadata changed"):
        _validate_registered_entry(entry, fake)

    duplicate = section.replace(
        "**Source type:**",
        "**DOI:** https://doi.org/10.0000/conflict\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, duplicate)

