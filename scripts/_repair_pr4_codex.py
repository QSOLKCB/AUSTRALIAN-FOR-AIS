from __future__ import annotations

import hashlib
from pathlib import Path
import pprint
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"
POLICING = ROOT / "tests" / "test_policing_context_roadmap.py"
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(
        rf"(?ms)^def {re.escape(name)}\(.*?(?=^def |^@|\Z)"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"{name}: expected one function, found {len(matches)}")
    match = matches[0]
    return text[: match.start()] + replacement.rstrip() + "\n\n" + text[match.end() :]


def insert_once(text: str, anchor: str, insertion: str) -> str:
    if insertion.strip() in text:
        return text
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(f"anchor expected once, found {count}: {anchor[:80]!r}")
    return text.replace(anchor, insertion + anchor, 1)


# Freeze the current accepted governance rationales before changing parser semantics.
ns = runpy.run_path(str(REGISTRY))
corpus = CORPUS.read_text(encoding="utf-8")
sections = ns["_registered_sections"](corpus)
rationale_hashes: dict[str, str] = {}
for entry, section in sections.items():
    rendered, structure = ns["_markdown_views"](section)
    match = ns["GOVERNANCE_PATTERN"].search(structure)
    if not match:
        raise RuntimeError(f"missing canonical governance rationale for {entry}")
    raw = rendered[match.start("rationale") : match.end("rationale")]
    rationale = ns["_visible_inline_text"](raw)
    rationale_hashes[entry] = hashlib.sha256(rationale.encode("utf-8")).hexdigest()

registry = REGISTRY.read_text(encoding="utf-8")
registry = registry.replace("import html\n", "import html\nfrom html.parser import HTMLParser\n", 1)

if "GOVERNANCE_RATIONALE_HASHES =" not in registry:
    literal = pprint.pformat(rationale_hashes, width=100, sort_dicts=True)
    registry = registry.replace(
        "\n\nBATCH_HEADING =",
        f"\n\nGOVERNANCE_RATIONALE_HASHES = {literal}\n\nBATCH_HEADING =",
        1,
    )

html_helper = r'''

class _VisibleHTMLTextParser(HTMLParser):
    """Collect browser-visible HTML text while respecting hidden containers."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []

    @staticmethod
    def _is_hidden(tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        tag = tag.lower()
        if tag in {"script", "style", "template"}:
            return True
        values = {key.lower(): (value or "") for key, value in attrs}
        if "hidden" in values:
            return True
        if values.get("aria-hidden", "").strip().lower() == "true":
            return True
        style = re.sub(r"\s+", "", values.get("style", "").lower())
        return "display:none" in style or "visibility:hidden" in style

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        inherited = self.stack[-1][1] if self.stack else False
        self.stack.append((tag.lower(), inherited or self._is_hidden(tag, attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)


def _visible_html_text(text: str) -> str:
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    return " ".join(parser.parts)


def _indent_columns(value: str, start: int = 0) -> tuple[int, int]:
    """Return the first non-indent index and indentation in display columns."""
    index = start
    columns = 0
    while index < len(value) and value[index] in " \t":
        if value[index] == " ":
            columns += 1
        else:
            columns += 4 - (columns % 4)
        index += 1
    return index, columns
'''
registry = insert_once(registry, "\n\n@dataclass(frozen=True)\nclass LineContext:", html_helper)

registry = replace_function(
    registry,
    "_markdown_views",
    r'''
def _markdown_views(text: str) -> tuple[str, str]:
    """Return rendered and structural views with exact offsets preserved."""
    rendered_parts: list[str] = []
    structural_parts: list[str] = []
    in_comment = False
    fence: FenceState | None = None
    paragraph_open = False
    active_list_indent: int | None = None
    raw_lines = text.splitlines(keepends=True)
    scan_lines = _mask_multiline_code_spans(text).splitlines(keepends=True)
    assert len(raw_lines) == len(scan_lines)

    for raw_line, scan_line in zip(raw_lines, scan_lines):
        line = raw_line.rstrip("\r\n")
        indent_index, indent_columns = _indent_columns(line)
        explicit_list = (
            LIST_CONTAINER_PREFIX_PATTERN.match(line, indent_index)
            if indent_columns <= 3
            else None
        )
        if explicit_list is not None:
            active_list_indent = indent_columns + len(
                explicit_list.group(0).expandtabs(4)
            )
        elif line.strip() and active_list_indent is not None:
            if indent_columns < active_list_indent:
                active_list_indent = None

        if not line.strip():
            paragraph_open = False

        while fence is not None and not _fence_container_continues(line, fence):
            fence = None

        if fence is not None:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            if _is_fence_closer(line, fence):
                fence = None
            continue

        if in_comment:
            rendered_line, in_comment = _mask_html_comments_on_line(
                raw_line,
                in_comment=True,
                scan_line=scan_line,
            )
            rendered_parts.append(rendered_line)
            structural_parts.append(_mask_inline_code_spans(rendered_line))
            if not in_comment:
                paragraph_open = _line_opens_paragraph(
                    rendered_line.rstrip("\r\n")
                )
            continue

        context = _line_context(line)
        _, composed_indented_code = _strip_composed_container_prefixes(line)
        indented_code = context.indented_code or composed_indented_code
        if active_list_indent is not None and indent_columns >= active_list_indent:
            indented_code = (indent_columns - active_list_indent) >= 4

        if indented_code and not paragraph_open:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            continue

        if indented_code and paragraph_open:
            rendered_line, in_comment = _mask_html_comments_on_line(
                raw_line,
                in_comment=False,
                scan_line=scan_line,
            )
            rendered_parts.append(rendered_line)
            structural_parts.append(_mask_inline_code_spans(rendered_line))
            paragraph_open = True
            continue

        opener = _fence_opener(line)
        if opener is not None:
            fence = opener
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            continue

        rendered_line, in_comment = _mask_html_comments_on_line(
            raw_line,
            in_comment=False,
            scan_line=scan_line,
        )
        rendered_parts.append(rendered_line)
        structural_parts.append(_mask_inline_code_spans(rendered_line))
        paragraph_open = _line_opens_paragraph(
            rendered_line.rstrip("\r\n")
        )

    return "".join(rendered_parts), "".join(structural_parts)
''',
)

registry = replace_function(
    registry,
    "_visible_inline_text",
    r'''
def _visible_inline_text(text: str) -> str:
    """Reduce Markdown/HTML metadata to browser-visible text only."""
    rendered = _rendered_registry_text(text)
    visible = _render_inline_code_spans(rendered)
    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = _visible_html_text(visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return " ".join(visible.split())
''',
)

registry = replace_function(
    registry,
    "_visible_scalar_values",
    r'''
def _normalised_rendered_lines(section: str) -> list[tuple[str, str, bool]]:
    """Return structural/rendered logical lines with list continuations preserved."""
    rendered, structure = _markdown_views(section)
    rendered_lines = rendered.splitlines()
    structure_lines = structure.splitlines()
    assert len(rendered_lines) == len(structure_lines)

    records: list[tuple[str, str, bool]] = []
    active_list_indent: int | None = None
    for rendered_line, structure_line in zip(rendered_lines, structure_lines):
        if not structure_line.strip():
            records.append(("", "", False))
            continue

        index, columns = _indent_columns(structure_line)
        marker = (
            LIST_CONTAINER_PREFIX_PATTERN.match(structure_line, index)
            if columns <= 3
            else None
        )
        if marker is not None:
            active_list_indent = columns + len(marker.group(0).expandtabs(4))
        elif active_list_indent is not None and columns < active_list_indent:
            active_list_indent = None

        logical, is_code = _strip_composed_container_prefixes(structure_line)
        rendered_logical, rendered_is_code = _strip_composed_container_prefixes(
            rendered_line
        )
        if (
            is_code
            and active_list_indent is not None
            and columns >= active_list_indent
            and columns - active_list_indent < 4
        ):
            logical = structure_line[index:]
            rendered_index, _ = _indent_columns(rendered_line)
            rendered_logical = rendered_line[rendered_index:]
            is_code = False
            rendered_is_code = False

        records.append(
            (logical.lstrip(" \t"), rendered_logical.lstrip(" \t"), is_code or rendered_is_code)
        )
    return records


def _metadata_field_count(section: str, fields: tuple[str, ...]) -> int:
    count = 0
    for logical, _, is_code in _normalised_rendered_lines(section):
        if is_code:
            continue
        for field in fields:
            if logical.startswith(field):
                suffix = logical[len(field):]
                if not suffix or suffix[0] in " \t":
                    count += 1
                    break
    return count


def _scalar_field_records(section: str, field: str) -> list[tuple[str, str]]:
    records = _normalised_rendered_lines(section)
    values: list[tuple[str, str]] = []
    for index, (logical, rendered_logical, is_code) in enumerate(records):
        if is_code or not logical.startswith(field):
            continue
        suffix = logical[len(field):]
        if suffix and suffix[0] not in " \t":
            continue
        if not rendered_logical.startswith(field):
            continue

        raw_parts = [rendered_logical[len(field):].strip()]
        cursor = index + 1
        while cursor < len(records):
            next_logical, next_rendered, next_is_code = records[cursor]
            stripped = next_logical.strip()
            if not stripped or next_is_code:
                break
            if re.match(r"\*\*[^*]+:\*\*", stripped):
                break
            if re.match(r"#{1,6}(?:[ \t]+|$)", stripped):
                break
            if stripped in {
                "Candidate research mappings:",
                "Research mappings:",
                "Relevant project mappings:",
            }:
                break
            if THEMATIC_BREAK_PATTERN.fullmatch(stripped):
                break
            raw_parts.append(next_rendered.strip())
            cursor += 1

        raw_value = " ".join(part for part in raw_parts if part)
        values.append((_visible_inline_text(raw_value), raw_value))
    return values


def _visible_scalar_values(section: str, field: str) -> list[str]:
    return [visible for visible, _ in _scalar_field_records(section, field)]


def _scalar_markdown_value(entry: str, section: str, field: str) -> str:
    records = _scalar_field_records(section, field)
    assert len(records) == 1, f"{entry} must contain exactly one mandatory field {field}"
    visible, raw = records[0]
    assert visible, f"{entry} has an empty mandatory field {field}"
    return raw
''',
)

registry = replace_function(
    registry,
    "_has_non_heading_content",
    r'''
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
            if _visible_inline_text(_fence_logical_line(raw_line, fence).strip()):
                return True
            continue

        opener = _fence_opener(raw_line)
        if opener is not None:
            fence = opener
            continue

        logical, is_code = _strip_composed_container_prefixes(raw_line)
        line = logical.strip()
        if not line:
            continue
        if THEMATIC_BREAK_PATTERN.fullmatch(line):
            continue
        if re.fullmatch(r"(?:Candidate research mappings:|Research mappings:)", line):
            continue
        if line == "Relevant project mappings:":
            continue
        if re.fullmatch(r"#{1,6}[ \t]+.+", line):
            continue
        if re.fullmatch(r"(?:[-+*]|\d{1,9}[.)])", line):
            continue
        if re.fullmatch(r"\*\*[^*]+:\*\*(?:[ \t].*)?", line):
            continue
        if LINK_REFERENCE_DEFINITION_PATTERN.fullmatch(line):
            continue
        if _visible_inline_text(line):
            return True

    return False
''',
)

registry = replace_function(
    registry,
    "_require_mapping_block",
    r'''
def _require_mapping_block(entry: str, section: str) -> None:
    normalised = _normalised_rendered_lines(section)
    research_count = sum(
        1
        for logical, _, is_code in normalised
        if not is_code and logical.strip() in {"Candidate research mappings:", "Research mappings:"}
    )
    project_count = sum(
        1
        for logical, _, is_code in normalised
        if not is_code and logical.strip() == "Relevant project mappings:"
    )
    assert research_count == 1, f"{entry} must contain exactly one research mappings heading"
    assert project_count == 1, f"{entry} must contain exactly one relevant project mappings heading"

    rendered, structure = _markdown_views(section)
    research_headings = list(RESEARCH_MAPPING_HEADING_PATTERN.finditer(structure))
    project_headings = list(PROJECT_MAPPING_HEADING_PATTERN.finditer(structure))
    assert len(research_headings) == 1 and len(project_headings) == 1

    research_start = research_headings[0].end()
    project_start = project_headings[0].start()
    assert research_start < project_start, f"{entry} has research/project mapping headings in the wrong order"
    assert _has_non_heading_content(rendered[research_start:project_start]), f"{entry} has empty research mappings"

    safe_heading = re.search(
        rf"(?m)^ {{0,3}}{re.escape(SAFE_FIELD)}",
        structure[project_headings[0].end():],
    )
    assert safe_heading, f"{entry} is missing the safe benchmark abstraction field"
    project_value_start = project_headings[0].end()
    project_end = project_value_start + safe_heading.start()
    assert _has_non_heading_content(rendered[project_value_start:project_end]), f"{entry} has empty project mappings"
''',
)

registry = replace_function(
    registry,
    "_require_registered_source_link",
    r'''
def _require_registered_source_link(entry: str, section: str) -> tuple[str, ...]:
    source_count = _metadata_field_count(
        section,
        ("**Registered source:**", "**Registered sources:**"),
    )
    assert source_count == 1, f"{entry} must contain exactly one registered-source field"

    rendered, structure = _markdown_views(section)
    source_block = re.search(
        r"(?ms)^[ \t]*\*\*Registered sources?:\*\*(.*?)"
        r"(?=^[ \t]*\*\*[^*\n]+:\*\*|\Z)",
        structure,
    )
    assert source_block, f"{entry} has an empty registered-source field"
    source_value = rendered[source_block.start(1):source_block.end(1)]
    assert _visible_inline_text(source_value), f"{entry} has an empty registered-source field"

    destinations = _usable_https_destinations(source_value)
    assert destinations, f"{entry} has no usable HTTPS destination in its registered-source field"
    assert len(destinations) == len(set(destinations)), f"{entry} contains duplicate registered-source destinations"
    return destinations
''',
)

registry = replace_function(
    registry,
    "_require_community_governance",
    r'''
def _require_community_governance(entry: str, section: str) -> str:
    field_count = _metadata_field_count(section, ("**Community-specific governance:**",))
    assert field_count == 1, f"{entry} must contain exactly one community-specific governance field"

    rendered, structure = _markdown_views(section)
    classification = GOVERNANCE_PATTERN.search(structure)
    assert classification, f"{entry} has an invalid community-specific governance classification or rationale"
    raw_rationale = rendered[classification.start("rationale"):classification.end("rationale")]
    rationale = _visible_inline_text(raw_rationale)
    assert rationale, f"{entry} has an invalid community-specific governance classification or rationale"
    actual_hash = hashlib.sha256(rationale.encode("utf-8")).hexdigest()
    expected_hash = GOVERNANCE_RATIONALE_HASHES[entry]
    assert actual_hash == expected_hash, (
        f"{entry} changed pinned community-governance rationale: "
        f"expected hash {expected_hash!r}, got {actual_hash!r}"
    )

    value = classification.group(1)
    if value == "required":
        safe_use = _scalar_value(entry, section, SAFE_FIELD)
        assert CONSULTATION_BOUNDARY in safe_use, (
            f"{entry} is missing its community-specific consultation boundary "
            "from the safe benchmark abstraction field"
        )
    return value
''',
)

registry = replace_function(
    registry,
    "_require_pinned_entry_contract",
    r'''
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
    assert classification == expected_classification, f"{entry} must remain classified as {expected_classification}"

    expected_destinations = set(contract[SOURCES_KEY])
    actual_destinations = set(destinations)
    assert actual_destinations == expected_destinations, (
        f"{entry} registered-source destinations changed: "
        f"expected {sorted(expected_destinations)!r}, got {sorted(actual_destinations)!r}"
    )

    for field in SCALAR_FIELDS:
        expected_value = _visible_inline_text(str(contract[field]))
        actual_value = scalar_values[field]
        if field == SOURCE_TYPE_FIELD:
            assert actual_value == expected_value, (
                f"{entry} changed pinned {field}: expected {expected_value!r}, got {actual_value!r}"
            )
            continue
        expected_clause = expected_value
        assert expected_clause in actual_value, f"{entry} is missing a pinned {field} clause: {expected_clause!r}"
        if field in BOUNDARY_FIELDS:
            actual_hash = hashlib.sha256(actual_value.encode("utf-8")).hexdigest()
            expected_hash = BOUNDARY_VALUE_HASHES[entry][field]
            assert actual_hash == expected_hash, (
                f"{entry} changed pinned {field}: expected hash {expected_hash!r}, got {actual_hash!r}"
            )
''',
)

registry = replace_function(
    registry,
    "_validate_registered_entry",
    r'''
def _validate_registered_entry(entry: str, section: str) -> None:
    destinations = _require_registered_source_link(entry, section)
    scalar_values = {field: _scalar_value(entry, section, field) for field in SCALAR_FIELDS}
    contract = ENTRY_CONTRACTS.get(entry)
    assert contract is not None, f"{entry} has no pinned source-governance contract"
    if DOI_FIELD in contract:
        expected_doi = str(contract[DOI_FIELD])
        doi_value = _scalar_value(entry, section, DOI_FIELD)
        assert doi_value == expected_doi, (
            f"{entry} DOI metadata changed: expected {expected_doi!r}, got {doi_value!r}"
        )
        raw_doi = _scalar_markdown_value(entry, section, DOI_FIELD)
        doi_destinations = _usable_https_destinations(raw_doi)
        assert doi_destinations == (expected_doi,), (
            f"{entry} DOI hyperlink destination changed: expected {(expected_doi,)!r}, "
            f"got {doi_destinations!r}"
        )
    else:
        assert not _visible_scalar_values(section, DOI_FIELD), f"{entry} has unpinned DOI metadata"
    classification = _require_community_governance(entry, section)
    _require_pinned_entry_contract(
        entry,
        classification=classification,
        scalar_values=scalar_values,
        destinations=destinations,
    )
    _require_mapping_block(entry, section)
''',
)

registry = replace_function(
    registry,
    "_validate_registry_corpus",
    r'''
def _validate_registry_corpus(corpus: str) -> None:
    structure = _structural_registry_text(corpus)
    assert CONTRACT_HEADING in structure, "rendered registration contract is missing"
    contract_start = structure.index(CONTRACT_HEADING)
    assert BATCH_HEADING in structure[contract_start:], "rendered governed batch heading is missing"
    contract_end = structure.index(BATCH_HEADING, contract_start)
    contract_section = structure[contract_start:contract_end]
    assert CONTRACT_SENTENCE in contract_section, "rendered registration contract is incomplete"
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in structure

    sections = _registered_sections(corpus)
    assert set(sections) == set(ENTRY_CONTRACTS), (
        "every rendered governed entry must have an explicit pinned source contract"
    )
    for entry, section in sections.items():
        _validate_registered_entry(entry, section)
''',
)

registry_tests = r'''


def test_tab_indented_comment_cannot_hide_duplicate_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))
    section = _registered_sections(corpus)[entry]
    doi = str(ENTRY_CONTRACTS[entry][DOI_FIELD])
    mutated = section.replace(
        f"{DOI_FIELD} {doi}",
        f"{DOI_FIELD} {doi}\n\n\t<!--\n{DOI_FIELD} https://doi.org/10.0000/conflict\n\t-->",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_list_continuation_indent_cannot_hide_duplicate_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))
    section = _registered_sections(corpus)[entry]
    doi = str(ENTRY_CONTRACTS[entry][DOI_FIELD])
    mutated = section.replace(
        f"{DOI_FIELD} {doi}",
        f"{DOI_FIELD} {doi}\n\n- container\n\n    {DOI_FIELD} https://doi.org/10.0000/conflict",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_hidden_html_cannot_supply_registry_values_or_mappings():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^({re.escape(RIGHTS_FIELD)}[ \t]*)(.+)$",
        lambda match: match.group(1) + "<span hidden>" + match.group(2) + "</span>",
        section,
        count=1,
    )
    with pytest.raises(AssertionError):
        _validate_registered_entry(entry, mutated)
    assert not _has_non_heading_content('<div hidden>placeholder</div>')


def test_registered_source_duplicate_in_container_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        r"(?m)^(\*\*Registered source:\*\*[^\n]*)$",
        r"\1\n> **Registered source:** https://www.wikipedia.org/",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _validate_registered_entry(entry, mutated)


def test_doi_link_destination_is_pinned_as_well_as_visible_label():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))
    section = _registered_sections(corpus)[entry]
    doi = str(ENTRY_CONTRACTS[entry][DOI_FIELD])
    mutated = section.replace(
        f"{DOI_FIELD} {doi}",
        f"{DOI_FIELD} [{doi}](https://doi.org/10.0000/fabricated)",
        1,
    )
    with pytest.raises(AssertionError, match="DOI hyperlink destination changed"):
        _validate_registered_entry(entry, mutated)


def test_registration_contract_clauses_are_section_scoped():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(CONTRACT_HEADING)
    end = corpus.index(BATCH_HEADING, start)
    contract = corpus[start:end]
    mutated_contract = contract.replace(CONTRACT_SENTENCE, "mandatory fields are listed below", 1)
    mutated = corpus[:start] + mutated_contract + corpus[end:] + "\n" + CONTRACT_SENTENCE + "\n"
    with pytest.raises(AssertionError, match="registration contract is incomplete"):
        _validate_registry_corpus(mutated)


def test_governance_rationale_is_fully_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        r"(?m)^(\*\*Community-specific governance:\*\* required:[^\n]*)$",
        r"\1 Contradictory override: no consultation, provenance, permissions, or scope limitations are required.",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="governance rationale"):
        _validate_registered_entry(entry, mutated)


def test_source_type_complete_value_is_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^({re.escape(SOURCE_TYPE_FIELD)}[^\n]*)$",
        r"\1 Contradictory override: unverified anonymous post with no pragmatic relevance.",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="changed pinned"):
        _validate_registered_entry(entry, mutated)


def test_boundary_hash_includes_paragraph_continuations():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Shaun Micallef's MAD AS HELL*"
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^({re.escape(RIGHTS_FIELD)}[^\n]*)$",
        r"\1\nContradictory continuation: programme dialogue may be freely copied into benchmark data.",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="changed pinned"):
        _validate_registered_entry(entry, mutated)


def test_mapping_content_normalises_compound_containers():
    assert not _has_non_heading_content("- > ---\n")
'''
if "test_tab_indented_comment_cannot_hide_duplicate_doi" not in registry:
    registry += registry_tests

REGISTRY.write_text(registry, encoding="utf-8")

# Policing renderer: apply the same browser-visible HTML semantics and require
# affirmative line context for invariants/source gates that must not be negated.
policing = POLICING.read_text(encoding="utf-8")
policing = policing.replace("import html\n", "import html\nfrom html.parser import HTMLParser\n", 1)

if "AFFIRMATIVE_LINE_PREFIX_CLAUSES" not in policing:
    policing = policing.replace(
        "\n\nFENCE_PATTERN =",
        '''\n\nAFFIRMATIVE_LINE_PREFIX_CLAUSES = (\n    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",\n    "CASUAL ADDRESS != FRIENDSHIP OR CONSENT",\n    "FICTIONAL POLICE TROPE != OPERATIONAL POLICY",\n    "JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER",\n    "LEGAL INFORMATION != LEGAL ADVICE",\n    "register official and current sources for each Australian and United States jurisdictional claim",\n)\n\nFENCE_PATTERN =''',
        1,
    )

policing_html_helper = r'''

class _VisibleHTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []

    @staticmethod
    def _is_hidden(tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        tag = tag.lower()
        if tag in {"script", "style", "template"}:
            return True
        values = {key.lower(): (value or "") for key, value in attrs}
        if "hidden" in values:
            return True
        if values.get("aria-hidden", "").strip().lower() == "true":
            return True
        style = re.sub(r"\s+", "", values.get("style", "").lower())
        return "display:none" in style or "visibility:hidden" in style

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        inherited = self.stack[-1][1] if self.stack else False
        self.stack.append((tag.lower(), inherited or self._is_hidden(tag, attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)


def _visible_html_text(text: str) -> str:
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    return " ".join(parser.parts)
'''
policing = insert_once(policing, "\n\ndef _mask_non_newline", policing_html_helper)

policing = replace_function(
    policing,
    "_visible_text",
    r'''
def _visible_text(markdown: str) -> str:
    """Return browser-visible text without hidden HTML or link metadata."""
    visible = MARKDOWN_IMAGE_PATTERN.sub(" ", markdown)
    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = _visible_html_text(visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return " ".join(visible.split())
''',
)

policing = replace_function(
    policing,
    "_validate_policing_workstream",
    r'''
def _validate_policing_workstream(roadmap: str) -> None:
    rendered = _rendered_policing_workstream(roadmap)
    workstream = _visible_text(rendered)
    visible_lines: list[str] = []
    for raw_line in rendered.splitlines():
        line = _visible_text(raw_line).strip()
        line = re.sub(r"^(?:[-+*]|\d{1,9}[.)])\s+", "", line)
        if line:
            visible_lines.append(line)

    for clause in REQUIRED_CLAUSES:
        visible_clause = _visible_text(clause)
        if clause in AFFIRMATIVE_LINE_PREFIX_CLAUSES:
            assert any(line.startswith(visible_clause) for line in visible_lines), (
                f"missing policing-workstream safeguard: {clause}"
            )
        else:
            assert visible_clause in workstream, f"missing policing-workstream safeguard: {clause}"
''',
)

policing_tests = r'''


def test_policing_safeguard_cannot_hide_in_hidden_html():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "register official and current sources for each Australian and United States jurisdictional claim"
    mutated = roadmap.replace(clause, f"<span hidden>{clause}</span>", 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)


def test_policing_source_gate_cannot_be_negated():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "register official and current sources for each Australian and United States jurisdictional claim"
    mutated = roadmap.replace(clause, "never " + clause, 1)
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)
'''
if "test_policing_safeguard_cannot_hide_in_hidden_html" not in policing:
    policing += policing_tests

POLICING.write_text(policing, encoding="utf-8")

# One-shot machinery removes itself from the resulting tree.
for temporary in (
    ROOT / ".github" / "workflows" / "pr4-review-repair.yml",
    ROOT / "scripts" / "_repair_pr4_codex.py",
):
    if temporary.exists():
        temporary.unlink()
