from pathlib import Path
import re


test_path = Path("tests/test_research_reference_registry.py")
text = test_path.read_text(encoding="utf-8")

# 1. Treat visible HTML <strong>/<b> field labels like CommonMark strong labels.
strong_anchor = '''STRONG_METADATA_FIELD_PATTERN = re.compile(
    r"^(?P<marker>\\*\\*|__)(?P<label>[^:\\r\\n]+):(?P=marker)(?=$|[ \\t])"
)
'''
html_strong = strong_anchor + '''HTML_STRONG_METADATA_FIELD_PATTERN = re.compile(
    r"^<(?P<tag>strong|b)\\b(?P<attrs>[^>]*)>"
    r"(?P<label>[^<:\\r\\n]+):</(?P=tag)>(?=$|[ \\t])",
    flags=re.IGNORECASE,
)
'''
if "HTML_STRONG_METADATA_FIELD_PATTERN" not in text:
    assert strong_anchor in text
    text = text.replace(strong_anchor, html_strong, 1)

old_fence_state = '''@dataclass(frozen=True)
class FenceState:
    character: str
    minimum_length: int
    quote_depth: int
    list_indent: int | None
'''
new_fence_state = '''@dataclass(frozen=True)
class FenceState:
    character: str
    minimum_length: int
    containers: tuple[tuple[str, int], ...]
'''
if old_fence_state in text:
    text = text.replace(old_fence_state, new_fence_state, 1)

# 2. Parse arbitrary list/quote container order once and use it for fence ownership.
helper_anchor = "\ndef _line_opens_paragraph(line: str) -> bool:\n"
helpers = r'''
def _display_columns(value: str) -> int:
    columns = 0
    for character in value:
        if character == "\t":
            columns += 4 - (columns % 4)
        else:
            columns += 1
    return columns


def _parse_composed_container_prefixes(
    line: str,
) -> tuple[str, bool, tuple[tuple[str, int], ...]]:
    """Return logical text, code status, and ordered list/quote containers."""
    value = line.rstrip("\r\n")
    position = 0
    containers: list[tuple[str, int]] = []

    for _ in range(32):
        probe, columns = _indent_columns(value, position)
        if columns >= 4:
            return value[position:], True, tuple(containers)

        if probe < len(value) and value[probe] == ">":
            containers.append(("quote", 0))
            position = probe + 1
            if position < len(value) and value[position] in " \t":
                position += 1
            continue

        marker = LIST_CONTAINER_PREFIX_PATTERN.match(value, probe)
        if marker:
            content_indent = columns + _display_columns(marker.group(0))
            containers.append(("list", content_indent))
            position = marker.end()
            continue

        position = probe
        break

    return value[position:], False, tuple(containers)


def _consume_required_indent(
    value: str,
    start: int,
    required_columns: int,
) -> tuple[int, bool]:
    position = start
    columns = 0
    while position < len(value) and value[position] in " \t" and columns < required_columns:
        if value[position] == " ":
            columns += 1
        else:
            columns += 4 - (columns % 4)
        position += 1
    return position, columns >= required_columns


def _strip_expected_fence_containers(
    line: str,
    containers: tuple[tuple[str, int], ...],
) -> tuple[str, bool]:
    """Strip the continuation form of the containers that own an active fence."""
    value = line.rstrip("\r\n")
    position = 0

    for kind, amount in containers:
        if kind == "list":
            position, ok = _consume_required_indent(value, position, amount)
            if not ok:
                return value, False
            continue

        probe, columns = _indent_columns(value, position)
        if columns > 3 or probe >= len(value) or value[probe] != ">":
            return value, False
        position = probe + 1
        if position < len(value) and value[position] in " \t":
            position += 1

    return value[position:], True


def _line_opens_paragraph(line: str) -> bool:
'''
if "_parse_composed_container_prefixes" not in text:
    assert helper_anchor in text
    text = text.replace(helper_anchor, helpers, 1)

fence_block_pattern = re.compile(
    r"def _fence_opener\(line: str\) -> FenceState \| None:\n.*?"
    r"(?=\ndef _is_fence_closer\(line: str, state: FenceState\) -> bool:)",
    flags=re.DOTALL,
)
new_fence_block = r'''def _fence_opener(line: str) -> FenceState | None:
    """Return a valid fence opener and its ordered container ownership."""
    logical, indented_code, containers = _parse_composed_container_prefixes(line)
    if indented_code:
        return None
    match = FENCE_PATTERN.fullmatch(logical.rstrip(" \t"))
    if not match:
        return None
    marker = match.group("fence")
    info = match.group("info")
    if marker[0] == "`" and "`" in info:
        return None
    return FenceState(
        character=marker[0],
        minimum_length=len(marker),
        containers=containers,
    )


def _fence_container_continues(line: str, state: FenceState) -> bool:
    """Return whether the active fence's complete container chain continues."""
    if not line.strip():
        return True
    if not state.containers:
        return True
    _, ok = _strip_expected_fence_containers(line, state.containers)
    return ok


def _fence_logical_line(line: str, state: FenceState) -> str:
    """Return content inside the active fence's ordered container context."""
    if not state.containers:
        return line.rstrip("\r\n")
    logical, ok = _strip_expected_fence_containers(line, state.containers)
    return logical if ok else line.rstrip("\r\n")

'''
text, count = fence_block_pattern.subn(new_fence_block, text, count=1)
assert count == 1

strip_pattern = re.compile(
    r"def _strip_composed_container_prefixes\(line: str\) -> tuple\[str, bool\]:\n.*?"
    r"(?=\n\ndef _canonicalise_metadata_marker)",
    flags=re.DOTALL,
)
new_strip = r'''def _strip_composed_container_prefixes(line: str) -> tuple[str, bool]:
    """Strip recursively composed quote/list prefixes and detect code indentation."""
    logical, is_code, _ = _parse_composed_container_prefixes(line)
    return logical, is_code
'''
text, count = strip_pattern.subn(new_strip, text, count=1)
assert count == 1

canonical_pattern = re.compile(
    r"def _canonicalise_metadata_marker\(line: str\) -> str:\n.*?"
    r"(?=\n\ndef _normalised_rendered_lines)",
    flags=re.DOTALL,
)
new_canonical = r'''def _canonicalise_metadata_marker(line: str) -> str:
    """Canonicalise equivalent visible strong-emphasis metadata labels."""
    match = STRONG_METADATA_FIELD_PATTERN.match(line)
    if match:
        canonical = f"**{match.group('label')}:**"
        return canonical + line[match.end():]

    html_match = HTML_STRONG_METADATA_FIELD_PATTERN.match(line)
    if html_match:
        label = html_match.group("label")
        rendered_label = _visible_html_text(html_match.group(0)).strip()
        if rendered_label == f"{label}:":
            canonical = f"**{label}:**"
            return canonical + line[html_match.end():]
    return line
'''
text, count = canonical_pattern.subn(new_canonical, text, count=1)
assert count == 1

if "def test_compound_container_fence_cannot_hide_scalar_metadata():" not in text:
    text = text.rstrip() + r'''


def test_compound_container_fence_cannot_hide_scalar_metadata():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    rights_line = next(
        line for line in section.splitlines()
        if line.startswith(RIGHTS_FIELD)
    )
    mutated = section.replace(
        rights_line,
        f"- > ```\n  > {rights_line}\n  > ```",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize("tag", ["strong", "b"])
def test_html_strong_doi_field_is_counted(tag: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*"
    section = _registered_sections(corpus)[entry]
    expected = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"
    mutated = section.replace(
        expected,
        expected + f"\n\n<{tag}>DOI:</{tag}> https://doi.org/10.0000/fabricated",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_registration_contract_explicitly_bounds_community_attestation():
    corpus = CORPUS.read_text(encoding="utf-8")
    structure = _structural_registry_text(corpus)
    start = structure.index(CONTRACT_HEADING)
    end = structure.index(BATCH_HEADING, start)
    contract = structure[start:end]
    assert "explicitly bounded community-attestation source links" in contract
    assert "user-generated, non-representative orientation or attestation material" in contract
    assert "cannot establish prevalence" in contract
'''

test_path.write_text(text, encoding="utf-8")

# 3. Reconcile community-attestation with the adopted-source contract.
corpus_path = Path("docs/RESEARCH-REFERENCE-CORPUS.md")
corpus = corpus_path.read_text(encoding="utf-8")
old_source_rule = (
    "- one or more official, archival, creator, broadcaster, publisher, or peer-reviewed source links;"
)
new_source_rule = (
    "- one or more official, archival, creator, broadcaster, publisher, peer-reviewed, "
    "or explicitly bounded community-attestation source links;"
)
assert old_source_rule in corpus
corpus = corpus.replace(old_source_rule, new_source_rule, 1)

contract_anchor = (
    "A required field must not be omitted merely because no strong value is available. "
    "When a field genuinely has no applicable mapping or no stronger source can be identified, "
    "the entry must say so explicitly and explain the limitation. Singular and plural source-link "
    "headings may differ when an entry needs more than one source, but the source-link field itself "
    "is mandatory.\n"
)
attestation_paragraph = contract_anchor + (
    "\nCommunity-attestation links are eligible only when the entry explicitly identifies them as "
    "user-generated, non-representative orientation or attestation material. They may nominate "
    "candidate forms, disagreements, or research leads, but cannot establish prevalence, population "
    "consensus, authoritative etymology, subgroup ground truth, or substitute for official, archival, "
    "publisher, or peer-reviewed evidence where the claim requires those sources. Safe abstraction "
    "must use independently authored examples and later source verification rather than converting "
    "community posts into benchmark data.\n"
)
if "Community-attestation links are eligible only" not in corpus:
    assert contract_anchor in corpus
    corpus = corpus.replace(contract_anchor, attestation_paragraph, 1)
corpus_path.write_text(corpus, encoding="utf-8")

# 4. Decouple Australian-English familiarity from nationality/language identity.
roadmap_path = Path("ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
old_listener = (
    "- cross-national listener cases testing Australian slang with familiar Australian speakers, "
    "other English-speaking partners, and speakers using English as an additional language;"
)
new_listener = (
    "- crossed listener-familiarity cases varying self-reported or experimentally established "
    "Australian-English exposure independently of general English-language background or proficiency; "
    "nationality and first-language identity must not define the comparison cohorts or stand in as "
    "proxies for comprehension;"
)
assert old_listener in roadmap
roadmap = roadmap.replace(old_listener, new_listener, 1)
roadmap_path.write_text(roadmap, encoding="utf-8")

methodology_path = Path("docs/METHODOLOGY.md")
methodology = methodology_path.read_text(encoding="utf-8")
old_method_sentence = (
    "Listener background and task criticality should be explicit variables rather than inferred after the fact."
)
new_method_sentence = (
    "Australian-English familiarity or exposure, general English-language background or proficiency, "
    "and task criticality should be explicit independent variables rather than inferred from nationality "
    "or identity. Where listener effects are evaluated, Australian-English familiarity should be "
    "self-reported or experimentally established, and comparisons should cross or match dialect exposure "
    "against broader English-language background so neither nationality nor first-language category acts "
    "as a proxy for comprehension."
)
assert old_method_sentence in methodology
methodology = methodology.replace(old_method_sentence, new_method_sentence, 1)
old_control = "- familiar-listener versus unfamiliar-listener conditions;"
new_control = (
    "- higher versus lower Australian-English familiarity crossed or matched across general "
    "English-language backgrounds;"
)
assert old_control in methodology
methodology = methodology.replace(old_control, new_control, 1)
methodology_path.write_text(methodology, encoding="utf-8")

workstream_test = Path("tests/test_workstream_h_methodology.py")
workstream_test.write_text(r'''"""Regression checks for Workstream H listener-variable design."""

from pathlib import Path


ROOT = Path(__file__).parent.parent
ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"


def _workstream_h(text: str) -> str:
    start = text.index("### H. Slang density")
    end = text.index("### I. Australian and United States policing-context transfer", start)
    return text[start:end]


def test_workstream_h_decouples_dialect_exposure_from_listener_identity():
    section = _workstream_h(ROADMAP.read_text(encoding="utf-8"))
    assert "self-reported or experimentally established Australian-English exposure" in section
    assert "independently of general English-language background or proficiency" in section
    assert "nationality and first-language identity must not define the comparison cohorts" in section
    assert "familiar Australian speakers, other English-speaking partners" not in section


def test_canonical_methodology_crosses_listener_variables_independently():
    text = METHODOLOGY.read_text(encoding="utf-8")
    start = text.index("## Trans-Tasman and Slang/Operational Experiment Design")
    end = text.index("## Australian and United States Policing-Context Experiment Design", start)
    section = text[start:end]
    assert "Australian-English familiarity or exposure" in section
    assert "self-reported or experimentally established" in section
    assert "neither nationality nor first-language category acts as a proxy for comprehension" in section
    assert "higher versus lower Australian-English familiarity crossed or matched" in section
''', encoding="utf-8")

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog_line = (
    "- Closed the next review round by making registry fence ownership container-order-aware, "
    "canonicalizing visible HTML strong metadata labels, explicitly governing community-attestation "
    "sources, and decoupling Australian-English familiarity from nationality and general language "
    "background in Workstream H\n"
)
if changelog_line not in changelog:
    marker = "\n---\n\n## [Unreleased] — Phase 2 Pilot Human Annotation"
    assert marker in changelog
    changelog = changelog.replace(marker, "\n" + changelog_line + marker, 1)
    changelog_path.write_text(changelog, encoding="utf-8")
