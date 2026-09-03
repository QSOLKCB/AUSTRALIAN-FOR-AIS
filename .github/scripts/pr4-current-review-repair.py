from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before_once(path: Path, anchor: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one insertion anchor, found {count}")
    path.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8")


registry = Path("tests/test_research_reference_registry.py")
workstream_h = Path("tests/test_workstream_h_methodology.py")
policing = Path("tests/test_policing_context_roadmap.py")

# ---------------------------------------------------------------------------
# 1. Registry: multiline reference definitions + headings in containers.
# ---------------------------------------------------------------------------
replace_once(
    registry,
    '''LINK_REFERENCE_DEFINITION_PATTERN = re.compile(\n    r"(?m)^ {0,3}\\[(?P<label>[^\\]\\r\\n]+)\\]:[ \\t]*"\n    r"(?P<destination><[^>\\r\\n]+>|[^\\s\\r\\n]+)"\n    r"(?:[ \\t]+(?:\\\"[^\\\"\\r\\n]*\\\"|'[^'\\r\\n]*'|\\([^)]*\\)))?[ \\t]*$"\n)\n''',
    '''LINK_REFERENCE_DEFINITION_PATTERN = re.compile(\n    r"(?m)^ {0,3}\\[(?P<label>[^\\]\\r\\n]+)\\]:[ \\t]*"\n    r"(?:\\r?\\n {1,3})?"\n    r"(?P<destination><[^>\\r\\n]+>|[^\\s\\r\\n]+)"\n    r"(?:[ \\t]+(?:\\\"[^\\\"\\r\\n]*\\\"|'[^'\\r\\n]*'|\\([^)]*\\)))?[ \\t]*$"\n)\n''',
)

replace_once(
    registry,
    '''    matches: list[tuple[int, int, str]] = [\n        (match.start(), match.end(), match.group("heading"))\n        for match in ENTRY_HEADING_PATTERN.finditer(visible_structure)\n    ]\n''',
    '''    matches: list[tuple[int, int, str]] = []\n    offset = 0\n    for raw_line in visible_structure.splitlines(keepends=True):\n        line = raw_line.rstrip("\\r\\n")\n        logical, is_code = _strip_composed_container_prefixes(line)\n        if not is_code:\n            heading_match = re.fullmatch(\n                r" {0,3}(?P<heading>### .+?)[ \\t]*",\n                logical,\n            )\n            if heading_match:\n                matches.append(\n                    (\n                        offset,\n                        offset + len(line),\n                        heading_match.group("heading"),\n                    )\n                )\n        offset += len(raw_line)\n''',
)

insert_before_once(
    registry,
    '@pytest.mark.parametrize("wrapper", ("comment", "fence"))\ndef test_registration_contract_must_remain_rendered(wrapper: str):\n',
    '''def test_registered_source_resolves_multiline_document_reference_definition():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = EXPECTED_GOVERNED_ENTRIES[0]\n    section = _registered_sections(corpus)[entry]\n    marker = (\n        "**Registered source:**"\n        if "**Registered source:**" in section\n        else "**Registered sources:**"\n    )\n    mutated_section = section.replace(\n        marker,\n        f"{marker} [alternate][multiline-provenance]\\n",\n        1,\n    )\n    mutated = (\n        corpus.replace(section, mutated_section, 1)\n        + "\\n[multiline-provenance]:\\n  https://www.wikipedia.org/\\n"\n    )\n\n    with pytest.raises(AssertionError, match="registered-source destinations changed"):\n        _validate_registry_corpus(mutated)\n\n\n@pytest.mark.parametrize("prefix", ("> ", "- "))\ndef test_registry_discovers_entry_heading_inside_markdown_container(prefix: str):\n    corpus = CORPUS.read_text(encoding="utf-8")\n    fabricated = (\n        f"{prefix}### Fabricated ungoverned reference\\n"\n        f"{prefix}placeholder provenance prose\\n\\n"\n    )\n    mutated = corpus.replace(BATCH_END, fabricated + BATCH_END, 1)\n    assert "### Fabricated ungoverned reference" in _registered_sections(mutated)\n    with pytest.raises(\n        AssertionError,\n        match="every rendered governed entry must have an explicit pinned source contract",\n    ):\n        _validate_registry_corpus(mutated)\n\n\n''',
)

# ---------------------------------------------------------------------------
# 2. Workstream H: balanced inline-link labels in browser-visible text.
# ---------------------------------------------------------------------------
insert_before_once(
    workstream_h,
    'def _visible_markdown_text(markdown: str) -> str:\n',
    '''def _is_escaped_markdown_character(text: str, index: int) -> bool:\n    backslashes = 0\n    cursor = index - 1\n    while cursor >= 0 and text[cursor] == "\\\\":\n        backslashes += 1\n        cursor -= 1\n    return backslashes % 2 == 1\n\n\ndef _balanced_markdown_label_end(text: str, start: int) -> int | None:\n    depth = 1\n    cursor = start + 1\n    while cursor < len(text):\n        character = text[cursor]\n        if character in "\\r\\n":\n            return None\n        if character == "\\\\" and cursor + 1 < len(text):\n            cursor += 2\n            continue\n        if character == "[":\n            depth += 1\n        elif character == "]":\n            depth -= 1\n            if depth == 0:\n                return cursor\n        cursor += 1\n    return None\n\n\ndef _inline_link_closing_paren(text: str, start: int) -> int | None:\n    depth = 1\n    cursor = start + 1\n    quote: str | None = None\n    angle = False\n    while cursor < len(text):\n        character = text[cursor]\n        if character in "\\r\\n":\n            return None\n        if character == "\\\\" and cursor + 1 < len(text):\n            cursor += 2\n            continue\n        if quote is not None:\n            if character == quote:\n                quote = None\n            cursor += 1\n            continue\n        if angle:\n            if character == ">":\n                angle = False\n            cursor += 1\n            continue\n        if character in {"\\\"", "'"}:\n            quote = character\n            cursor += 1\n            continue\n        if character == "<":\n            angle = True\n            cursor += 1\n            continue\n        if character == "(":\n            depth += 1\n        elif character == ")":\n            depth -= 1\n            if depth == 0:\n                return cursor\n        cursor += 1\n    return None\n\n\ndef _replace_inline_markdown_links_for_visibility(text: str) -> str:\n    parts: list[str] = []\n    cursor = 0\n    while cursor < len(text):\n        bracket = text.find("[", cursor)\n        if bracket < 0:\n            parts.append(text[cursor:])\n            break\n        if _is_escaped_markdown_character(text, bracket):\n            parts.append(text[cursor:bracket + 1])\n            cursor = bracket + 1\n            continue\n        label_end = _balanced_markdown_label_end(text, bracket)\n        if label_end is None or label_end + 1 >= len(text) or text[label_end + 1] != "(":\n            parts.append(text[cursor:bracket + 1])\n            cursor = bracket + 1\n            continue\n        paren_end = _inline_link_closing_paren(text, label_end + 1)\n        if paren_end is None:\n            parts.append(text[cursor:bracket + 1])\n            cursor = bracket + 1\n            continue\n        image = (\n            bracket > 0\n            and text[bracket - 1] == "!"\n            and not _is_escaped_markdown_character(text, bracket - 1)\n        )\n        start = bracket - 1 if image else bracket\n        parts.append(text[cursor:start])\n        parts.append(" " if image else text[bracket + 1:label_end])\n        cursor = paren_end + 1\n    return "".join(parts)\n\n\n''',
)
replace_once(
    workstream_h,
    '''    visible = MARKDOWN_IMAGE_PATTERN.sub(" ", markdown)\n    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)\n''',
    '''    visible = _replace_inline_markdown_links_for_visibility(markdown)\n''',
)
replace_once(
    workstream_h,
    '''    for hidden in (\n        f"<!-- {stereotype_clause} -->",\n        f"<span hidden>{stereotype_clause}</span>",\n        f'[placeholder](# "{stereotype_clause}")',\n    ):\n''',
    '''    for hidden in (\n        f"<!-- {stereotype_clause} -->",\n        f"<span hidden>{stereotype_clause}</span>",\n        f'[placeholder](# "{stereotype_clause}")',\n        f'[placeholder [nested]](# "{stereotype_clause}")',\n    ):\n''',
)

# ---------------------------------------------------------------------------
# 3. Policing: closed disclosures + balanced link-label visibility.
# ---------------------------------------------------------------------------
replace_once(
    policing,
    '''        values = {key.lower(): (value or "") for key, value in attrs}\n        if "hidden" in values:\n''',
    '''        values = {key.lower(): (value or "") for key, value in attrs}\n        if tag == "details" and "open" not in values:\n            return True\n        if "hidden" in values:\n''',
)

insert_before_once(
    policing,
    'def _visible_text(markdown: str) -> str:\n',
    '''def _is_escaped_markdown_character(text: str, index: int) -> bool:\n    backslashes = 0\n    cursor = index - 1\n    while cursor >= 0 and text[cursor] == "\\\\":\n        backslashes += 1\n        cursor -= 1\n    return backslashes % 2 == 1\n\n\ndef _balanced_markdown_label_end(text: str, start: int) -> int | None:\n    depth = 1\n    cursor = start + 1\n    while cursor < len(text):\n        character = text[cursor]\n        if character in "\\r\\n":\n            return None\n        if character == "\\\\" and cursor + 1 < len(text):\n            cursor += 2\n            continue\n        if character == "[":\n            depth += 1\n        elif character == "]":\n            depth -= 1\n            if depth == 0:\n                return cursor\n        cursor += 1\n    return None\n\n\ndef _inline_link_closing_paren(text: str, start: int) -> int | None:\n    depth = 1\n    cursor = start + 1\n    quote: str | None = None\n    angle = False\n    while cursor < len(text):\n        character = text[cursor]\n        if character in "\\r\\n":\n            return None\n        if character == "\\\\" and cursor + 1 < len(text):\n            cursor += 2\n            continue\n        if quote is not None:\n            if character == quote:\n                quote = None\n            cursor += 1\n            continue\n        if angle:\n            if character == ">":\n                angle = False\n            cursor += 1\n            continue\n        if character in {"\\\"", "'"}:\n            quote = character\n            cursor += 1\n            continue\n        if character == "<":\n            angle = True\n            cursor += 1\n            continue\n        if character == "(":\n            depth += 1\n        elif character == ")":\n            depth -= 1\n            if depth == 0:\n                return cursor\n        cursor += 1\n    return None\n\n\ndef _replace_inline_markdown_links_for_visibility(text: str) -> str:\n    parts: list[str] = []\n    cursor = 0\n    while cursor < len(text):\n        bracket = text.find("[", cursor)\n        if bracket < 0:\n            parts.append(text[cursor:])\n            break\n        if _is_escaped_markdown_character(text, bracket):\n            parts.append(text[cursor:bracket + 1])\n            cursor = bracket + 1\n            continue\n        label_end = _balanced_markdown_label_end(text, bracket)\n        if label_end is None or label_end + 1 >= len(text) or text[label_end + 1] != "(":\n            parts.append(text[cursor:bracket + 1])\n            cursor = bracket + 1\n            continue\n        paren_end = _inline_link_closing_paren(text, label_end + 1)\n        if paren_end is None:\n            parts.append(text[cursor:bracket + 1])\n            cursor = bracket + 1\n            continue\n        image = (\n            bracket > 0\n            and text[bracket - 1] == "!"\n            and not _is_escaped_markdown_character(text, bracket - 1)\n        )\n        start = bracket - 1 if image else bracket\n        parts.append(text[cursor:start])\n        parts.append(" " if image else text[bracket + 1:label_end])\n        cursor = paren_end + 1\n    return "".join(parts)\n\n\n''',
)
replace_once(
    policing,
    '''    visible = MARKDOWN_IMAGE_PATTERN.sub(" ", markdown)\n    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)\n''',
    '''    visible = _replace_inline_markdown_links_for_visibility(markdown)\n''',
)

insert_before_once(
    policing,
    'def test_policing_fence_container_ownership_hides_top_level_code_payload():\n',
    '''def test_policing_context_workstream_cannot_hide_in_closed_details():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    start = roadmap.index(WORKSTREAM_HEADING)\n    end = roadmap.index(WORKSTREAM_END, start)\n    section = roadmap[start:end]\n    hidden = f"<details>\\n{section}\\n</details>\\n"\n    mutated = roadmap[:start] + hidden + roadmap[end:]\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n\n\n''',
)
replace_once(
    policing,
    '''def test_policing_safeguard_cannot_hide_in_link_title():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    clause = "register official and current sources for each Australian and United States jurisdictional claim"\n    replacement = f'[sources required](# "{clause}")'\n    mutated = roadmap.replace(clause, replacement, 1)\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n''',
    '''@pytest.mark.parametrize("label", ("sources required", "sources [required]"))\ndef test_policing_safeguard_cannot_hide_in_link_title(label: str):\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    clause = "register official and current sources for each Australian and United States jurisdictional claim"\n    replacement = f'[{label}](# "{clause}")'\n    mutated = roadmap.replace(clause, replacement, 1)\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n''',
)

print("Applied four current Codex review repairs.")
