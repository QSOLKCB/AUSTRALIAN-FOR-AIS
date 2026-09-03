from __future__ import annotations

from pathlib import Path
import hashlib
import pprint
import runpy


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"
POLICING = ROOT / "tests" / "test_policing_context_roadmap.py"
WORKSTREAM_H = ROOT / "tests" / "test_workstream_h_methodology.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one repair anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, sentinel: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel in text:
        return
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + addition, encoding="utf-8")


# ---------------------------------------------------------------------------
# Registry: reference definitions inside containers, raw HTML blocks, and a
# complete render-aware entry integrity receipt.
# ---------------------------------------------------------------------------
replace_once(
    REGISTRY,
    'STATUS_HEADING = "## Status"\n',
    'ENTRY_RENDERED_VALUE_HASHES: dict[str, str] = {}\n\nSTATUS_HEADING = "## Status"\n',
)

replace_once(
    REGISTRY,
    'REFERENCE_LINK_PATTERN = re.compile(\n',
    '''LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN = re.compile(\n    r"\\[(?P<label>[^\\]\\r\\n]+)\\]:[ \\t]*"\n    r"(?P<destination><[^>\\r\\n]+>|[^\\s\\r\\n]+)"\n    r"(?:[ \\t]+(?:\\\"[^\\\"\\r\\n]*\\\"|'[^'\\r\\n]*'|\\([^)]*\\)))?[ \\t]*$"\n)\n\nREFERENCE_LINK_PATTERN = re.compile(\n''',
)

replace_once(
    REGISTRY,
    'SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})\n',
    '''SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})\nRAW_HTML_BLOCK_TAGS = frozenset({"pre", "script", "style", "textarea"})\n''',
)

replace_once(
    REGISTRY,
    '''@dataclass(frozen=True)\nclass FenceState:\n    character: str\n    minimum_length: int\n    containers: tuple[tuple[str, int], ...]\n\n\ndef _mask_non_newline(text: str) -> str:\n''',
    '''@dataclass(frozen=True)\nclass FenceState:\n    character: str\n    minimum_length: int\n    containers: tuple[tuple[str, int], ...]\n\n\n@dataclass(frozen=True)\nclass RawHTMLBlockState:\n    tag: str\n    containers: tuple[tuple[str, int], ...]\n\n\ndef _mask_non_newline(text: str) -> str:\n''',
)

replace_once(
    REGISTRY,
    'def _matching_backtick_run_start(\n',
    '''def _raw_html_block_opener(line: str) -> RawHTMLBlockState | None:\n    """Return a CommonMark type-1 raw HTML block opener."""\n    logical, indented_code, containers = _parse_composed_container_prefixes(line)\n    if indented_code:\n        return None\n    candidate = logical.lstrip(" \\t")\n    match = re.match(\n        r"<(?P<tag>pre|script|style|textarea)(?:[ \\t]|>|$)",\n        candidate,\n        flags=re.IGNORECASE,\n    )\n    if match is None:\n        return None\n    return RawHTMLBlockState(\n        tag=match.group("tag").lower(),\n        containers=containers,\n    )\n\n\ndef _raw_html_block_container_continues(\n    line: str,\n    state: RawHTMLBlockState,\n) -> bool:\n    if not line.strip() or not state.containers:\n        return True\n    _, ok = _strip_expected_fence_containers(line, state.containers)\n    return ok\n\n\ndef _raw_html_block_logical_line(line: str, state: RawHTMLBlockState) -> str:\n    if not state.containers:\n        return line.rstrip("\\r\\n")\n    logical, ok = _strip_expected_fence_containers(line, state.containers)\n    return logical if ok else line.rstrip("\\r\\n")\n\n\ndef _raw_html_block_closes(line: str, state: RawHTMLBlockState) -> bool:\n    logical = _raw_html_block_logical_line(line, state)\n    return bool(\n        re.search(\n            rf"</{re.escape(state.tag)}[ \\t]*>",\n            logical,\n            flags=re.IGNORECASE,\n        )\n    )\n\n\ndef _matching_backtick_run_start(\n''',
)

replace_once(
    REGISTRY,
    '''    in_comment = False\n    fence: FenceState | None = None\n    paragraph_open = False\n''',
    '''    in_comment = False\n    fence: FenceState | None = None\n    raw_html_block: RawHTMLBlockState | None = None\n    paragraph_open = False\n''',
)

replace_once(
    REGISTRY,
    '''        while fence is not None and not _fence_container_continues(line, fence):\n            fence = None\n\n        if fence is not None:\n''',
    '''        while fence is not None and not _fence_container_continues(line, fence):\n            fence = None\n        while (\n            raw_html_block is not None\n            and not _raw_html_block_container_continues(line, raw_html_block)\n        ):\n            raw_html_block = None\n\n        if fence is not None:\n''',
)

replace_once(
    REGISTRY,
    '''        if fence is not None:\n            rendered_parts.append(raw_line)\n            structural_parts.append(_mask_non_newline(raw_line))\n            paragraph_open = False\n            if _is_fence_closer(line, fence):\n                fence = None\n            continue\n\n        if in_comment:\n''',
    '''        if fence is not None:\n            rendered_parts.append(raw_line)\n            structural_parts.append(_mask_non_newline(raw_line))\n            paragraph_open = False\n            if _is_fence_closer(line, fence):\n                fence = None\n            continue\n\n        if raw_html_block is not None:\n            rendered_parts.append(raw_line)\n            structural_parts.append(_mask_non_newline(raw_line))\n            paragraph_open = False\n            if _raw_html_block_closes(line, raw_html_block):\n                raw_html_block = None\n            continue\n\n        if in_comment:\n''',
)

replace_once(
    REGISTRY,
    '''        if indented_code and paragraph_open:\n            rendered_line, in_comment = _mask_html_comments_on_line(\n                raw_line,\n                in_comment=False,\n                scan_line=scan_line,\n            )\n            rendered_parts.append(rendered_line)\n            structural_parts.append(_mask_inline_code_spans(rendered_line))\n            paragraph_open = True\n            continue\n\n        opener = _fence_opener(line)\n''',
    '''        if indented_code and paragraph_open:\n            rendered_line, in_comment = _mask_html_comments_on_line(\n                raw_line,\n                in_comment=False,\n                scan_line=scan_line,\n            )\n            rendered_parts.append(rendered_line)\n            structural_parts.append(_mask_inline_code_spans(rendered_line))\n            paragraph_open = True\n            continue\n\n        raw_html_opener = _raw_html_block_opener(line)\n        if raw_html_opener is not None:\n            raw_html_block = raw_html_opener\n            rendered_parts.append(raw_line)\n            structural_parts.append(_mask_non_newline(raw_line))\n            paragraph_open = False\n            if _raw_html_block_closes(line, raw_html_block):\n                raw_html_block = None\n            continue\n\n        opener = _fence_opener(line)\n''',
)

replace_once(
    REGISTRY,
    '''def _visible_inline_text(text: str) -> str:\n    """Reduce Markdown/HTML metadata to browser-visible text only."""\n    rendered = _rendered_registry_text(text)\n    visible = _render_inline_code_spans(rendered)\n''',
    '''def _visible_inline_text(text: str) -> str:\n    """Reduce Markdown/HTML metadata to browser-visible text only."""\n    rendered = _rendered_registry_text(text)\n    visible = _mask_link_reference_definitions_for_visibility(rendered)\n    visible = _render_inline_code_spans(visible)\n''',
)

replace_once(
    REGISTRY,
    'def _leading_wrapped_html_metadata_marker(text: str) -> tuple[str, int] | None:\n',
    '''def _reference_definitions(reference_structure: str) -> dict[str, str]:\n    """Collect document-wide reference definitions, including Markdown containers."""\n    candidates: list[tuple[int, str, str]] = []\n    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(reference_structure):\n        candidates.append(\n            (\n                match.start(),\n                match.group("label"),\n                match.group("destination").strip("<>"),\n            )\n        )\n\n    offset = 0\n    for raw_line in reference_structure.splitlines(keepends=True):\n        line = raw_line.rstrip("\\r\\n")\n        logical, is_code, containers = _parse_composed_container_prefixes(line)\n        if containers and not is_code:\n            match = LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN.fullmatch(\n                logical.rstrip(" \\t")\n            )\n            if match is not None:\n                candidates.append(\n                    (\n                        offset,\n                        match.group("label"),\n                        match.group("destination").strip("<>"),\n                    )\n                )\n        offset += len(raw_line)\n\n    definitions: dict[str, str] = {}\n    for _, label, destination in sorted(candidates, key=lambda item: item[0]):\n        definitions.setdefault(_normalise_reference_label(label), destination)\n    return definitions\n\n\ndef _mask_link_reference_definitions_for_visibility(text: str) -> str:\n    """Mask non-rendering reference-definition blocks while preserving offsets."""\n    characters = list(text)\n    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(text):\n        _mask_segment(characters, match.start(), match.end())\n\n    partially_masked = "".join(characters)\n    offset = 0\n    for raw_line in partially_masked.splitlines(keepends=True):\n        line = raw_line.rstrip("\\r\\n")\n        logical, is_code, containers = _parse_composed_container_prefixes(line)\n        if containers and not is_code:\n            match = LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN.fullmatch(\n                logical.rstrip(" \\t")\n            )\n            if match is not None:\n                _mask_segment(characters, offset, offset + len(raw_line))\n        offset += len(raw_line)\n    return "".join(characters)\n\n\ndef _leading_wrapped_html_metadata_marker(text: str) -> tuple[str, int] | None:\n''',
)

replace_once(
    REGISTRY,
    '''    definitions: dict[str, str] = {}\n    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(reference_structure):\n        definitions.setdefault(\n            _normalise_reference_label(match.group("label")),\n            match.group("destination").strip("<>"),\n        )\n''',
    '''    definitions = _reference_definitions(reference_structure)\n''',
)

replace_once(
    REGISTRY,
    'def _validate_registered_entry(\n',
    '''def _normalise_complete_entry_integrity(section: str) -> str:\n    """Return the complete render-aware governed-entry body for integrity pinning."""\n    rendered = _rendered_registry_text(section)\n    rendered = _mask_hidden_html_regions(rendered)\n    rendered = _mask_link_reference_definitions_for_visibility(rendered)\n    return " ".join(rendered.split())\n\n\ndef _require_complete_entry_integrity(entry: str, section: str) -> None:\n    expected_hash = ENTRY_RENDERED_VALUE_HASHES.get(entry)\n    assert expected_hash is not None, f"{entry} has no complete rendered-entry integrity fixture"\n    value = _normalise_complete_entry_integrity(section)\n    actual_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()\n    assert actual_hash == expected_hash, (\n        f"{entry} complete rendered governed entry changed: expected hash "\n        f"{expected_hash!r}, got {actual_hash!r}"\n    )\n\n\ndef _validate_registered_entry(\n''',
)

replace_once(
    REGISTRY,
    '''    _require_pinned_entry_contract(\n        entry,\n        classification=classification,\n        scalar_values=scalar_values,\n        destinations=destinations,\n        research_mapping=research_mapping,\n        project_mapping=project_mapping,\n    )\n\n\ndef _validate_registry_corpus(corpus: str) -> None:\n''',
    '''    _require_pinned_entry_contract(\n        entry,\n        classification=classification,\n        scalar_values=scalar_values,\n        destinations=destinations,\n        research_mapping=research_mapping,\n        project_mapping=project_mapping,\n    )\n    _require_complete_entry_integrity(entry, section)\n\n\ndef _validate_registry_corpus(corpus: str) -> None:\n''',
)

# Generate the committed complete-entry fixtures from the current governed
# corpus after all render/structure semantics above have been installed.
namespace = runpy.run_path(str(REGISTRY))
corpus = namespace["CORPUS"].read_text(encoding="utf-8")
sections = namespace["_registered_sections"](corpus)
normalise_entry = namespace["_normalise_complete_entry_integrity"]
entry_hashes = {
    entry: hashlib.sha256(normalise_entry(section).encode("utf-8")).hexdigest()
    for entry, section in sections.items()
}
registry_text = REGISTRY.read_text(encoding="utf-8")
placeholder = "ENTRY_RENDERED_VALUE_HASHES: dict[str, str] = {}"
replacement = (
    "ENTRY_RENDERED_VALUE_HASHES: dict[str, str] = "
    + pprint.pformat(entry_hashes, sort_dicts=True, width=100)
)
if placeholder not in registry_text:
    raise SystemExit("registry complete-entry hash placeholder missing")
REGISTRY.write_text(registry_text.replace(placeholder, replacement, 1), encoding="utf-8")

append_once(
    REGISTRY,
    "def test_registered_source_resolves_reference_definition_inside_container():",
    '''\n\ndef test_registered_source_resolves_reference_definition_inside_container():\n    source_value = "[alternate][container-provenance]"\n    for definition in (\n        "> [container-provenance]: https://www.wikipedia.org/",\n        "- > [container-provenance]: https://www.wikipedia.org/",\n    ):\n        scope = f"{source_value}\\n{definition}\\n"\n        assert _usable_https_destinations(\n            source_value,\n            reference_scope=scope,\n        ) == ("https://www.wikipedia.org/",)\n\n\ndef test_complete_rendered_governed_entry_is_pinned():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = EXPECTED_GOVERNED_ENTRIES[0]\n    section = _registered_sections(corpus)[entry]\n    mutated = (\n        section.rstrip()\n        + "\\n\\nThis work proves universal facts about all Aboriginal speakers.\\n"\n        + "[unregistered source](https://www.wikipedia.org/)\\n"\n    )\n    with pytest.raises(AssertionError, match="complete rendered governed entry changed"):\n        _validate_registered_entry(\n            entry,\n            mutated,\n            reference_scope=corpus,\n        )\n\n\ndef test_raw_html_block_cannot_supply_governed_batch_structure():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    start = corpus.index(BATCH_HEADING)\n    end = corpus.index(BATCH_END, start)\n    mutated = (\n        corpus[:start]\n        + "<textarea>\\n"\n        + corpus[start:end]\n        + "</textarea>\\n"\n        + corpus[end:]\n    )\n    with pytest.raises(AssertionError):\n        _validate_registry_corpus(mutated)\n''',
)

# ---------------------------------------------------------------------------
# Policing visibility: reference-definition blocks render no prose. Strip them
# before visible-text assertions. Workstream H delegates to this single reducer.
# ---------------------------------------------------------------------------
replace_once(
    POLICING,
    'AUTOLINK_PATTERN = re.compile(r"<(?P<url>https?://[^>\\s]+)>")\n',
    '''AUTOLINK_PATTERN = re.compile(r"<(?P<url>https?://[^>\\s]+)>")\nLINK_REFERENCE_DEFINITION_PATTERN = re.compile(\n    r"(?m)^ {0,3}\\[(?P<label>[^\\]\\r\\n]+)\\]:[ \\t]*"\n    r"(?:\\r?\\n {1,3})?"\n    r"(?P<destination><[^>\\r\\n]+>|[^\\s\\r\\n]+)"\n    r"(?:[ \\t]+(?:\\\"[^\\\"\\r\\n]*\\\"|'[^'\\r\\n]*'|\\([^)]*\\)))?[ \\t]*$"\n)\nLINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN = re.compile(\n    r"\\[(?P<label>[^\\]\\r\\n]+)\\]:[ \\t]*"\n    r"(?P<destination><[^>\\r\\n]+>|[^\\s\\r\\n]+)"\n    r"(?:[ \\t]+(?:\\\"[^\\\"\\r\\n]*\\\"|'[^'\\r\\n]*'|\\([^)]*\\)))?[ \\t]*$"\n)\n''',
)

replace_once(
    POLICING,
    'def _display_columns(value: str) -> int:\n',
    '''def _mask_link_reference_definitions_for_visibility(markdown: str) -> str:\n    """Mask CommonMark reference definitions, including container-scoped forms."""\n    characters = list(markdown)\n    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(markdown):\n        for index in range(match.start(), match.end()):\n            if characters[index] not in "\\r\\n":\n                characters[index] = " "\n\n    partially_masked = "".join(characters)\n    offset = 0\n    for raw_line in partially_masked.splitlines(keepends=True):\n        logical, indentation = _strip_container_prefixes(raw_line)\n        if (\n            indentation < 4\n            and LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN.fullmatch(\n                logical.rstrip("\\r\\n \\t")\n            )\n        ):\n            for index in range(offset, offset + len(raw_line)):\n                if characters[index] not in "\\r\\n":\n                    characters[index] = " "\n        offset += len(raw_line)\n    return "".join(characters)\n\n\ndef _display_columns(value: str) -> int:\n''',
)

replace_once(
    POLICING,
    '''    if THEMATIC_BREAK_PATTERN.fullmatch(stripped):\n        return False\n    return True\n''',
    '''    if THEMATIC_BREAK_PATTERN.fullmatch(stripped):\n        return False\n    if LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN.fullmatch(stripped):\n        return False\n    return True\n''',
)

replace_once(
    POLICING,
    '''def _visible_text(markdown: str) -> str:\n    """Return browser-visible text without hidden HTML or link metadata."""\n    visible = _replace_inline_markdown_links_for_visibility(markdown)\n''',
    '''def _visible_text(markdown: str) -> str:\n    """Return browser-visible text without hidden HTML or link metadata."""\n    visible = _mask_link_reference_definitions_for_visibility(markdown)\n    visible = _replace_inline_markdown_links_for_visibility(visible)\n''',
)

append_once(
    POLICING,
    "def test_policing_visibility_ignores_reference_definition_titles():",
    '''\n\ndef test_policing_visibility_ignores_reference_definition_titles():\n    clause = REQUIRED_CLAUSES[-1]\n    for hidden in (\n        f'[hidden]: # "{clause}"',\n        f'> [hidden]: # "{clause}"',\n        f'- > [hidden]: # "{clause}"',\n    ):\n        assert clause not in _visible_text(hidden)\n''',
)

replace_once(
    WORKSTREAM_H,
    '''def _visible_markdown_text(markdown: str) -> str:\n    """Return browser-visible safeguard text, excluding Markdown metadata."""\n    visible = _replace_inline_markdown_links_for_visibility(markdown)\n    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)\n    visible = _visible_html_text(visible)\n    visible = html.unescape(visible)\n    visible = visible.replace("**", "").replace("__", "")\n    visible = visible.replace("*", "").replace("_", "")\n    return " ".join(visible.split())\n''',
    '''def _visible_markdown_text(markdown: str) -> str:\n    """Return browser-visible safeguard text using the canonical policing reducer."""\n    namespace = runpy.run_path(str(POLICING_TEST))\n    return namespace["_visible_text"](markdown)\n''',
)

append_once(
    WORKSTREAM_H,
    "def test_workstream_h_visibility_ignores_reference_definition_titles():",
    '''\n\ndef test_workstream_h_visibility_ignores_reference_definition_titles():\n    clause = "nationality and first-language identity must not define the comparison cohorts"\n    for hidden in (\n        f'[hidden]: # "{clause}"',\n        f'> [hidden]: # "{clause}"',\n        f'- > [hidden]: # "{clause}"',\n    ):\n        assert clause not in _visible_markdown_text(hidden)\n''',
)

print("Applied five-head PR #4 hydra repair.")
