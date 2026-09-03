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
policing = Path("tests/test_policing_context_roadmap.py")
workstream_h = Path("tests/test_workstream_h_methodology.py")

# ---------------------------------------------------------------------------
# 1. Registry: balanced Markdown link labels + nested HTML metadata labels.
# ---------------------------------------------------------------------------
replace_once(
    registry,
    '''HTML_STRONG_METADATA_FIELD_PATTERN = re.compile(\n    r"^<(?P<tag>strong|b)\\b(?P<attrs>[^>]*)>"\n    r"(?P<label>[^<:\\r\\n]+):</(?P=tag)>(?=$|[ \\t])",\n    flags=re.IGNORECASE,\n)\n''',
    '''HTML_STRONG_METADATA_FIELD_PATTERN = re.compile(\n    r"^<(?P<tag>strong|b)\\b(?P<attrs>[^>]*)>"\n    r"(?P<body>.*?)</(?P=tag)>(?=$|[ \\t])",\n    flags=re.IGNORECASE,\n)\n''',
)

replace_once(
    registry,
    '''    html_match = HTML_STRONG_METADATA_FIELD_PATTERN.match(line)\n    if html_match:\n        label = html_match.group("label")\n        rendered_label = _visible_html_text(html_match.group(0)).strip()\n        if rendered_label == f"{label}:":\n            canonical = f"**{label}:**"\n            return canonical + line[html_match.end():]\n    return line\n''',
    '''    html_match = HTML_STRONG_METADATA_FIELD_PATTERN.match(line)\n    if html_match:\n        rendered_label = _visible_html_text(html_match.group(0)).strip()\n        if rendered_label.endswith(":"):\n            label = rendered_label[:-1].strip()\n            if label and ":" not in label:\n                canonical = f"**{label}:**"\n                return canonical + line[html_match.end():]\n    return line\n''',
)

replace_once(
    registry,
    '''def _normalise_reference_label(value: str) -> str:\n    """Apply CommonMark-style case-insensitive whitespace normalization."""\n    return " ".join(html.unescape(value).split()).casefold()\n\n\ndef _usable_https_destinations(\n''',
    '''def _normalise_reference_label(value: str) -> str:\n    """Apply CommonMark-style case-insensitive whitespace normalization."""\n    return " ".join(html.unescape(value).split()).casefold()\n\n\n@dataclass(frozen=True)\nclass MarkdownInlineLink:\n    start: int\n    end: int\n    label: str\n    destination: str\n    image: bool\n\n\ndef _is_escaped_markdown_character(text: str, index: int) -> bool:\n    backslashes = 0\n    cursor = index - 1\n    while cursor >= 0 and text[cursor] == "\\\\":\n        backslashes += 1\n        cursor -= 1\n    return backslashes % 2 == 1\n\n\ndef _balanced_markdown_label_end(text: str, start: int) -> int | None:\n    """Return the closing bracket for a balanced inline-link label."""\n    depth = 1\n    cursor = start + 1\n    while cursor < len(text):\n        character = text[cursor]\n        if character in "\\r\\n":\n            return None\n        if character == "\\\\" and cursor + 1 < len(text):\n            cursor += 2\n            continue\n        if character == "[":\n            depth += 1\n        elif character == "]":\n            depth -= 1\n            if depth == 0:\n                return cursor\n        cursor += 1\n    return None\n\n\ndef _inline_link_closing_paren(text: str, start: int) -> int | None:\n    """Return the closing parenthesis for an inline link destination/title."""\n    depth = 1\n    cursor = start + 1\n    quote: str | None = None\n    angle = False\n    top_level_space = False\n    while cursor < len(text):\n        character = text[cursor]\n        if character in "\\r\\n":\n            return None\n        if character == "\\\\" and cursor + 1 < len(text):\n            cursor += 2\n            continue\n        if quote is not None:\n            if character == quote:\n                quote = None\n            cursor += 1\n            continue\n        if angle:\n            if character == ">":\n                angle = False\n            cursor += 1\n            continue\n        if depth == 1 and character in " \\t":\n            top_level_space = True\n            cursor += 1\n            continue\n        if depth == 1 and top_level_space and character in {"\\\"", "'"}:\n            quote = character\n            cursor += 1\n            continue\n        if depth == 1 and not top_level_space and character == "<":\n            angle = True\n            cursor += 1\n            continue\n        if character == "(":\n            depth += 1\n        elif character == ")":\n            depth -= 1\n            if depth == 0:\n                return cursor\n        cursor += 1\n    return None\n\n\ndef _inline_link_destination(inner: str) -> str | None:\n    """Extract the destination while retaining the existing title contract."""\n    value = inner.lstrip(" \\t")\n    if not value:\n        return None\n\n    if value.startswith("<"):\n        close = value.find(">", 1)\n        if close < 0:\n            return None\n        destination = value[1:close]\n        remainder = value[close + 1:].strip()\n    else:\n        cursor = 0\n        depth = 0\n        while cursor < len(value):\n            character = value[cursor]\n            if character == "\\\\" and cursor + 1 < len(value):\n                cursor += 2\n                continue\n            if character == "(":\n                depth += 1\n            elif character == ")":\n                if depth == 0:\n                    return None\n                depth -= 1\n            elif character in " \\t" and depth == 0:\n                break\n            cursor += 1\n        if depth != 0:\n            return None\n        destination = value[:cursor]\n        remainder = value[cursor:].strip()\n\n    if not destination:\n        return None\n    if remainder:\n        quoted = (\n            len(remainder) >= 2\n            and remainder[0] in {"\\\"", "'"}\n            and remainder[-1] == remainder[0]\n        )\n        parenthesized = (\n            len(remainder) >= 2\n            and remainder[0] == "("\n            and remainder[-1] == ")"\n        )\n        if not (quoted or parenthesized):\n            return None\n    return destination\n\n\ndef _markdown_inline_links(text: str) -> tuple[MarkdownInlineLink, ...]:\n    """Parse inline links with balanced nested square-bracket labels."""\n    links: list[MarkdownInlineLink] = []\n    cursor = 0\n    while cursor < len(text):\n        bracket = text.find("[", cursor)\n        if bracket < 0:\n            break\n        if _is_escaped_markdown_character(text, bracket):\n            cursor = bracket + 1\n            continue\n\n        label_end = _balanced_markdown_label_end(text, bracket)\n        if label_end is None:\n            cursor = bracket + 1\n            continue\n        paren_start = label_end + 1\n        if paren_start >= len(text) or text[paren_start] != "(":\n            cursor = label_end + 1\n            continue\n        paren_end = _inline_link_closing_paren(text, paren_start)\n        if paren_end is None:\n            cursor = label_end + 1\n            continue\n        destination = _inline_link_destination(text[paren_start + 1:paren_end])\n        if destination is None:\n            cursor = paren_end + 1\n            continue\n\n        image = (\n            bracket > 0\n            and text[bracket - 1] == "!"\n            and not _is_escaped_markdown_character(text, bracket - 1)\n        )\n        start = bracket - 1 if image else bracket\n        links.append(\n            MarkdownInlineLink(\n                start=start,\n                end=paren_end + 1,\n                label=text[bracket + 1:label_end],\n                destination=destination,\n                image=image,\n            )\n        )\n        cursor = paren_end + 1\n    return tuple(links)\n\n\ndef _replace_inline_markdown_links_with_labels(text: str) -> str:\n    links = _markdown_inline_links(text)\n    if not links:\n        return text\n    parts: list[str] = []\n    cursor = 0\n    for link in links:\n        parts.append(text[cursor:link.start])\n        parts.append(link.label)\n        cursor = link.end\n    parts.append(text[cursor:])\n    return "".join(parts)\n\n\ndef _mask_inline_markdown_links(\n    text: str,\n    links: tuple[MarkdownInlineLink, ...],\n) -> str:\n    characters = list(text)\n    for link in links:\n        _mask_segment(characters, link.start, link.end)\n    return "".join(characters)\n\n\ndef _usable_https_destinations(\n''',
)

replace_once(
    registry,
    '    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)\n',
    '    visible = _replace_inline_markdown_links_with_labels(visible)\n',
)

replace_once(
    registry,
    '''    for match in MARKDOWN_LINK_PATTERN.finditer(structure):\n        if match.group("image"):\n            continue\n        destination = _normalise_https_destination(\n            match.group("destination").strip("<>")\n        )\n        if destination is not None:\n            destinations.append(destination)\n\n''',
    '''    inline_links = _markdown_inline_links(structure)\n    for link in inline_links:\n        if link.image:\n            continue\n        destination = _normalise_https_destination(link.destination.strip("<>"))\n        if destination is not None:\n            destinations.append(destination)\n    structure_without_inline_links = _mask_inline_markdown_links(\n        structure,\n        inline_links,\n    )\n\n''',
)
replace_once(
    registry,
    '    for match in REFERENCE_LINK_PATTERN.finditer(structure):\n',
    '    for match in REFERENCE_LINK_PATTERN.finditer(structure_without_inline_links):\n',
)
replace_once(
    registry,
    '    without_reference_links = REFERENCE_LINK_PATTERN.sub("", structure)\n',
    '    without_reference_links = REFERENCE_LINK_PATTERN.sub("", structure_without_inline_links)\n',
)
replace_once(
    registry,
    '    without_links = MARKDOWN_LINK_PATTERN.sub("", without_reference_links)\n',
    '    without_links = without_reference_links\n',
)

insert_before_once(
    registry,
    'def test_html_anchor_source_destination_is_included_in_pinned_set():\n',
    '''def test_balanced_nested_markdown_link_destination_is_included_in_pinned_set():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = EXPECTED_GOVERNED_ENTRIES[0]\n    section = _registered_sections(corpus)[entry]\n    mutated = section.replace(\n        SOURCE_TYPE_FIELD,\n        "[alternate [source]](https://www.wikipedia.org/)\\n\\n" + SOURCE_TYPE_FIELD,\n        1,\n    )\n    with pytest.raises(AssertionError, match="registered-source destinations changed"):\n        _validate_registered_entry(entry, mutated, reference_scope=corpus)\n\n\n''',
)

insert_before_once(
    registry,
    'def test_registration_contract_explicitly_bounds_community_attestation():\n',
    '''@pytest.mark.parametrize(\n    "markup",\n    (\n        "<strong><em>DOI:</em></strong>",\n        "<b><i>DOI:</i></b>",\n    ),\n)\ndef test_nested_html_strong_doi_field_is_counted(markup: str):\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*"\n    section = _registered_sections(corpus)[entry]\n    expected = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"\n    mutated = section.replace(\n        expected,\n        expected + f"\\n\\n{markup} https://doi.org/10.0000/fabricated",\n        1,\n    )\n    with pytest.raises(AssertionError, match="exactly one mandatory field"):\n        _validate_registered_entry(entry, mutated, reference_scope=corpus)\n\n\n''',
)

# ---------------------------------------------------------------------------
# 2. Policing renderer: give each active fence explicit container ownership.
# ---------------------------------------------------------------------------
replace_once(
    policing,
    'from pathlib import Path\nimport html\n',
    'from dataclasses import dataclass\nfrom pathlib import Path\nimport html\n',
)

replace_once(
    policing,
    '''def _fence_marker(line: str) -> tuple[str, int] | None:\n    logical, indentation = _strip_container_prefixes(line)\n    if indentation >= 4:\n        return None\n    match = FENCE_PATTERN.fullmatch(logical.rstrip(" \\t"))\n    if not match:\n        return None\n    marker = match.group("fence")\n    info = match.group("info")\n    if marker[0] == "`" and "`" in info:\n        return None\n    return marker[0], len(marker)\n\n\ndef _is_fence_closer(line: str, character: str, minimum_length: int) -> bool:\n    logical, _ = _strip_container_prefixes(line)\n    return bool(\n        re.fullmatch(\n            rf"{re.escape(character)}{{{minimum_length},}}[ \\t]*",\n            logical.rstrip(" \\t"),\n        )\n    )\n\n\n''',
    '''def _display_columns(value: str) -> int:\n    columns = 0\n    for character in value:\n        if character == "\\t":\n            columns += 4 - (columns % 4)\n        else:\n            columns += 1\n    return columns\n\n\n@dataclass(frozen=True)\nclass FenceState:\n    character: str\n    minimum_length: int\n    containers: tuple[tuple[str, int], ...]\n\n\ndef _parse_fence_container_prefixes(\n    line: str,\n) -> tuple[str, bool, tuple[tuple[str, int], ...]]:\n    """Return logical text, code status, and ordered list/quote containers."""\n    value = line.rstrip("\\r\\n")\n    position = 0\n    containers: list[tuple[str, int]] = []\n\n    for _ in range(32):\n        probe, columns = _indent_columns(value, position)\n        if columns >= 4:\n            return value[position:], True, tuple(containers)\n\n        if probe < len(value) and value[probe] == ">":\n            containers.append(("quote", 0))\n            position = probe + 1\n            if position < len(value) and value[position] in " \\t":\n                position += 1\n            continue\n\n        marker = LIST_MARKER_PATTERN.match(value, probe)\n        if marker:\n            content_indent = columns + _display_columns(marker.group(0))\n            containers.append(("list", content_indent))\n            position = marker.end()\n            continue\n\n        position = probe\n        break\n\n    return value[position:], False, tuple(containers)\n\n\ndef _consume_required_indent(\n    value: str,\n    start: int,\n    required_columns: int,\n) -> tuple[int, bool]:\n    position = start\n    columns = 0\n    while position < len(value) and value[position] in " \\t" and columns < required_columns:\n        if value[position] == " ":\n            columns += 1\n        else:\n            columns += 4 - (columns % 4)\n        position += 1\n    return position, columns >= required_columns\n\n\ndef _strip_expected_fence_containers(\n    line: str,\n    containers: tuple[tuple[str, int], ...],\n) -> tuple[str, bool]:\n    """Strip the continuation form of the containers that own an active fence."""\n    value = line.rstrip("\\r\\n")\n    position = 0\n\n    for kind, amount in containers:\n        if kind == "list":\n            position, ok = _consume_required_indent(value, position, amount)\n            if not ok:\n                return value, False\n            continue\n\n        probe, columns = _indent_columns(value, position)\n        if columns > 3 or probe >= len(value) or value[probe] != ">":\n            return value, False\n        position = probe + 1\n        if position < len(value) and value[position] in " \\t":\n            position += 1\n\n    return value[position:], True\n\n\ndef _fence_opener(line: str) -> FenceState | None:\n    logical, indented_code, containers = _parse_fence_container_prefixes(line)\n    if indented_code:\n        return None\n    match = FENCE_PATTERN.fullmatch(logical.rstrip(" \\t"))\n    if not match:\n        return None\n    marker = match.group("fence")\n    info = match.group("info")\n    if marker[0] == "`" and "`" in info:\n        return None\n    return FenceState(\n        character=marker[0],\n        minimum_length=len(marker),\n        containers=containers,\n    )\n\n\ndef _fence_container_continues(line: str, state: FenceState) -> bool:\n    if not line.strip():\n        return True\n    if not state.containers:\n        return True\n    _, ok = _strip_expected_fence_containers(line, state.containers)\n    return ok\n\n\ndef _fence_logical_line(line: str, state: FenceState) -> str:\n    if not state.containers:\n        return line.rstrip("\\r\\n")\n    logical, ok = _strip_expected_fence_containers(line, state.containers)\n    return logical if ok else line.rstrip("\\r\\n")\n\n\ndef _is_fence_closer(line: str, state: FenceState) -> bool:\n    logical = _fence_logical_line(line, state)\n    marker_index, indent_columns = _indent_columns(logical)\n    if indent_columns > 3:\n        return False\n    candidate = logical[marker_index:].rstrip(" \\t")\n    return bool(\n        re.fullmatch(\n            rf"{re.escape(state.character)}{{{state.minimum_length},}}[ \\t]*",\n            candidate,\n        )\n    )\n\n\n''',
)

replace_once(
    policing,
    '''    fence_character: str | None = None\n    fence_length = 0\n''',
    '''    fence: FenceState | None = None\n''',
)
replace_once(
    policing,
    '''        if fence_character is not None:\n            parts.append(_mask_non_newline(raw_line))\n            if _is_fence_closer(line, fence_character, fence_length):\n                fence_character = None\n                fence_length = 0\n            paragraph_open = False\n            continue\n''',
    '''        while fence is not None and not _fence_container_continues(line, fence):\n            fence = None\n\n        if fence is not None:\n            parts.append(_mask_non_newline(raw_line))\n            if _is_fence_closer(line, fence):\n                fence = None\n            paragraph_open = False\n            continue\n''',
)
replace_once(
    policing,
    '''        opener = _fence_marker(line)\n        if opener is not None:\n            fence_character, fence_length = opener\n            parts.append(_mask_non_newline(raw_line))\n            paragraph_open = False\n            continue\n''',
    '''        opener = _fence_opener(line)\n        if opener is not None:\n            fence = opener\n            parts.append(_mask_non_newline(raw_line))\n            paragraph_open = False\n            continue\n''',
)

insert_before_once(
    policing,
    'def test_policing_safeguard_cannot_hide_in_link_title():\n',
    '''def test_policing_fence_container_ownership_hides_top_level_code_payload():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    clause = "register official and current sources for each Australian and United States jurisdictional claim"\n    original = f"- {clause};"\n    replacement = (\n        "- > ```\\n"\n        "```\\n"\n        f"{clause};\\n"\n        "```\\n"\n        "> ```"\n    )\n    assert original in roadmap\n    mutated = roadmap.replace(original, replacement, 1)\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n\n\n''',
)

# ---------------------------------------------------------------------------
# 3. Workstream H: validate browser-visible safeguards rather than raw Markdown.
# ---------------------------------------------------------------------------
replace_once(
    workstream_h,
    'from pathlib import Path\n',
    'from pathlib import Path\nimport html\nfrom html.parser import HTMLParser\nimport re\n',
)

replace_once(
    workstream_h,
    '''METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"\n\n\ndef _workstream_h(text: str) -> str:\n    start = text.index("### H. Slang density")\n    end = text.index("### I. Australian and United States policing-context transfer", start)\n    return text[start:end]\n\n\n''',
    '''METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"\n\nMARKDOWN_IMAGE_PATTERN = re.compile(\n    r"!\\[[^\\]\\r\\n]*\\]\\([^\\r\\n)]*(?:\\)[^\\r\\n)]*)?\\)"\n)\nMARKDOWN_LINK_PATTERN = re.compile(\n    r"(?<!!)\\[(?P<label>[^\\]\\r\\n]*)\\]\\("\n    r"[ \\t]*(?:<[^>\\r\\n]+>|[^\\s)\\r\\n]+)"\n    r"(?:[ \\t]+(?:\\\"[^\\\"\\r\\n]*\\\"|'[^'\\r\\n]*'|\\([^)]*\\)))?"\n    r"[ \\t]*\\)"\n)\nAUTOLINK_PATTERN = re.compile(r"<(?P<url>https?://[^>\\s]+)>")\n\n\nclass _VisibleHTMLTextParser(HTMLParser):\n    def __init__(self) -> None:\n        super().__init__(convert_charrefs=True)\n        self.parts: list[str] = []\n        self.stack: list[tuple[str, bool]] = []\n\n    @staticmethod\n    def _is_hidden(tag: str, attrs: list[tuple[str, str | None]]) -> bool:\n        tag = tag.lower()\n        if tag in {"script", "style", "template"}:\n            return True\n        values = {key.lower(): (value or "") for key, value in attrs}\n        if tag == "details" and "open" not in values:\n            return True\n        if "hidden" in values:\n            return True\n        if values.get("aria-hidden", "").strip().lower() == "true":\n            return True\n        style = re.sub(r"\\s+", "", values.get("style", "").lower())\n        return "display:none" in style or "visibility:hidden" in style\n\n    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        inherited = self.stack[-1][1] if self.stack else False\n        self.stack.append((tag.lower(), inherited or self._is_hidden(tag, attrs)))\n\n    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        return\n\n    def handle_endtag(self, tag: str) -> None:\n        tag = tag.lower()\n        for index in range(len(self.stack) - 1, -1, -1):\n            if self.stack[index][0] == tag:\n                del self.stack[index:]\n                return\n\n    def handle_data(self, data: str) -> None:\n        if not self.stack or not self.stack[-1][1]:\n            self.parts.append(data)\n\n\ndef _visible_html_text(text: str) -> str:\n    parser = _VisibleHTMLTextParser()\n    try:\n        parser.feed(text)\n        parser.close()\n    except Exception:\n        return ""\n    return " ".join(parser.parts)\n\n\ndef _visible_markdown_text(markdown: str) -> str:\n    """Return browser-visible safeguard text, excluding Markdown metadata."""\n    visible = MARKDOWN_IMAGE_PATTERN.sub(" ", markdown)\n    visible = MARKDOWN_LINK_PATTERN.sub(lambda match: match.group("label"), visible)\n    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)\n    visible = _visible_html_text(visible)\n    visible = html.unescape(visible)\n    visible = visible.replace("**", "").replace("__", "")\n    visible = visible.replace("*", "").replace("_", "")\n    return " ".join(visible.split())\n\n\ndef _workstream_h(text: str) -> str:\n    start = text.index("### H. Slang density")\n    end = text.index("### I. Australian and United States policing-context transfer", start)\n    return _visible_markdown_text(text[start:end])\n\n\ndef _trans_tasman_methodology(text: str) -> str:\n    start = text.index("## Trans-Tasman and Slang/Operational Experiment Design")\n    end = text.index("## Australian and United States Policing-Context Experiment Design", start)\n    return _visible_markdown_text(text[start:end])\n\n\n''',
)

old_method_slice = '''    text = METHODOLOGY.read_text(encoding="utf-8")\n    start = text.index("## Trans-Tasman and Slang/Operational Experiment Design")\n    end = text.index("## Australian and United States Policing-Context Experiment Design", start)\n    section = text[start:end]\n'''
new_method_slice = '''    section = _trans_tasman_methodology(\n        METHODOLOGY.read_text(encoding="utf-8")\n    )\n'''
text = workstream_h.read_text(encoding="utf-8")
if text.count(old_method_slice) != 2:
    raise SystemExit(
        f"{workstream_h}: expected two canonical methodology slice anchors, "
        f"found {text.count(old_method_slice)}"
    )
workstream_h.write_text(text.replace(old_method_slice, new_method_slice), encoding="utf-8")

workstream_h.write_text(
    workstream_h.read_text(encoding="utf-8")
    + '''\n\ndef test_workstream_h_and_methodology_safeguards_must_be_browser_visible():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    listener_clause = "nationality and first-language identity must not define the comparison cohorts"\n    assert listener_clause in _workstream_h(roadmap)\n    for hidden in (\n        f"<!-- {listener_clause} -->",\n        f"<span hidden>{listener_clause}</span>",\n        f'[placeholder](# "{listener_clause}")',\n    ):\n        mutated = roadmap.replace(listener_clause, hidden, 1)\n        assert listener_clause not in _workstream_h(mutated)\n\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    stereotype_clause = "exact group-stereotyping wording must not be reproduced"\n    assert stereotype_clause in _trans_tasman_methodology(methodology)\n    for hidden in (\n        f"<!-- {stereotype_clause} -->",\n        f"<span hidden>{stereotype_clause}</span>",\n        f'[placeholder](# "{stereotype_clause}")',\n    ):\n        mutated = methodology.replace(stereotype_clause, hidden, 1)\n        assert stereotype_clause not in _trans_tasman_methodology(mutated)\n''',
    encoding="utf-8",
)

print("Applied four current Codex review repairs.")
