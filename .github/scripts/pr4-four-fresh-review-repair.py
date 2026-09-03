from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"{path}: replacement already present, skipping")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all_exact(path: Path, old: str, new: str, expected_count: int) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(new) == expected_count:
        print(f"{path}: repeated replacement already present, skipping")
        return
    count = text.count(old)
    if count != expected_count:
        raise SystemExit(
            f"{path}: expected {expected_count} anchors, found {count}: {old[:80]!r}"
        )
    path.write_text(text.replace(old, new), encoding="utf-8")


def replace_between(
    path: Path,
    start_marker: str,
    end_marker: str,
    replacement: str,
    *,
    already_marker: str,
) -> None:
    text = path.read_text(encoding="utf-8")
    if already_marker in text:
        print(f"{path}: block replacement already present, skipping")
        return
    if text.count(start_marker) != 1:
        raise SystemExit(
            f"{path}: expected one start marker, found {text.count(start_marker)}: {start_marker!r}"
        )
    start = text.index(start_marker)
    try:
        end = text.index(end_marker, start)
    except ValueError as exc:
        raise SystemExit(f"{path}: missing end marker {end_marker!r}") from exc
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def append_once(path: Path, sentinel: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel in text:
        print(f"{path}: regression already present, skipping")
        return
    path.write_text(text.rstrip() + "\n\n\n" + addition.strip() + "\n", encoding="utf-8")


registry = Path("tests/test_research_reference_registry.py")
workstream_h = Path("tests/test_workstream_h_methodology.py")
receipt = Path("tests/test_policing_contract_receipt.py")

# ---------------------------------------------------------------------------
# 1. Markdown code spans: a closer must be a complete backtick run whose
#    length exactly equals the opener, never a prefix of a longer run.
# ---------------------------------------------------------------------------
helper_anchor = '''def _mask_multiline_code_spans(text: str) -> str:\n'''
helper = '''def _matching_backtick_run_start(\n    text: str,\n    start: int,\n    marker_length: int,\n) -> int | None:\n    """Return the next complete backtick run with exactly marker_length ticks."""\n    cursor = start\n    while cursor < len(text):\n        candidate = text.find("`", cursor)\n        if candidate < 0:\n            return None\n        run_end = candidate\n        while run_end < len(text) and text[run_end] == "`":\n            run_end += 1\n        if run_end - candidate == marker_length:\n            return candidate\n        cursor = run_end\n    return None\n\n\n'''
replace_once(registry, helper_anchor, helper + helper_anchor)
replace_all_exact(
    registry,
    '        close = text.find(marker, run_end)\n',
    '        close = _matching_backtick_run_start(text, run_end, len(marker))\n',
    3,
)

# ---------------------------------------------------------------------------
# 2. Workstream H HTML visibility: browsers ignore the self-closing slash on
#    non-void elements, so <dialog /> must open a hidden dialog until </dialog>.
# ---------------------------------------------------------------------------
void_anchor = 'AUTOLINK_PATTERN = re.compile(r"<(?P<url>https?://[^>\\s]+)>")\n\n\nclass _VisibleHTMLTextParser(HTMLParser):\n'
void_replacement = '''AUTOLINK_PATTERN = re.compile(r"<(?P<url>https?://[^>\\s]+)>")\n\nHTML_VOID_TAGS = {\n    "area", "base", "br", "col", "embed", "hr", "img", "input",\n    "link", "meta", "param", "source", "track", "wbr",\n}\n\n\nclass _VisibleHTMLTextParser(HTMLParser):\n'''
replace_once(workstream_h, void_anchor, void_replacement)
replace_once(
    workstream_h,
    '''    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        return\n''',
    '''    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n        tag = tag.lower()\n        if tag in HTML_VOID_TAGS:\n            return\n        # Match browser tree construction: self-closing syntax does not close\n        # non-void HTML elements such as <dialog />.\n        self.handle_starttag(tag, attrs)\n''',
)
replace_once(
    workstream_h,
    '''        f"<dialog>{listener_clause}</dialog>",\n        f'[placeholder](# "{listener_clause}")',\n''',
    '''        f"<dialog>{listener_clause}</dialog>",\n        f"<dialog />{listener_clause}</dialog>",\n        f'[placeholder](# "{listener_clause}")',\n''',
)

# ---------------------------------------------------------------------------
# 3. Inline Markdown links: allow a line ending between a destination and its
#    quoted title, while still rejecting line endings inside the destination.
# ---------------------------------------------------------------------------
new_inline_closer = '''def _inline_link_closing_paren(text: str, start: int) -> int | None:\n    """Return the closing parenthesis for an inline link destination/title."""\n    depth = 1\n    cursor = start + 1\n    quote: str | None = None\n    angle = False\n    top_level_space = False\n    while cursor < len(text):\n        character = text[cursor]\n        if character == "\\\\" and cursor + 1 < len(text):\n            cursor += 2\n            continue\n        if quote is not None:\n            if character == quote:\n                quote = None\n            cursor += 1\n            continue\n        if angle:\n            if character in "\\r\\n":\n                return None\n            if character == ">":\n                angle = False\n            cursor += 1\n            continue\n        if depth == 1 and character in " \\t\\r\\n":\n            top_level_space = True\n            cursor += 1\n            continue\n        if character in "\\r\\n":\n            return None\n        if depth == 1 and top_level_space and character in {"\\\"", "'"}:\n            quote = character\n            cursor += 1\n            continue\n        if depth == 1 and not top_level_space and character == "<":\n            angle = True\n            cursor += 1\n            continue\n        if character == "(":\n            depth += 1\n        elif character == ")":\n            depth -= 1\n            if depth == 0:\n                return cursor\n        cursor += 1\n    return None\n\n\n'''
replace_between(
    registry,
    'def _inline_link_closing_paren(text: str, start: int) -> int | None:\n',
    'def _inline_link_destination(inner: str) -> str | None:\n',
    new_inline_closer,
    already_marker='        if depth == 1 and character in " \\t\\r\\n":\n',
)
replace_once(
    registry,
    '    value = inner.lstrip(" \\t")\n',
    '    value = inner.lstrip(" \\t\\r\\n")\n',
)
replace_once(
    registry,
    '            elif character in " \\t" and depth == 0:\n',
    '            elif character in " \\t\\r\\n" and depth == 0:\n',
)

# ---------------------------------------------------------------------------
# 4. Policing metadata receipt: inspect the browser-visible canonical section,
#    reusing the policing validator's own visible Markdown/HTML reducer.
# ---------------------------------------------------------------------------
replace_once(
    receipt,
    'import ast\nfrom pathlib import Path\n',
    'import ast\nfrom pathlib import Path\nimport runpy\n',
)
replace_once(
    receipt,
    '''def _assert_canonical_policing_metadata(methodology: str) -> None:\n    policing_methodology = _policing_methodology_section(methodology)\n    assert POLICING_METADATA_INTRO in policing_methodology\n    for field in CANONICAL_METADATA_FIELDS:\n        assert f"**{field}**" in policing_methodology\n''',
    '''def _assert_canonical_policing_metadata(methodology: str) -> None:\n    policing_methodology = _policing_methodology_section(methodology)\n    policing_namespace = runpy.run_path(str(POLICING_TEST))\n    visible_text = policing_namespace["_visible_text"]\n    rendered = visible_text(policing_methodology)\n    assert POLICING_METADATA_INTRO in rendered\n    for field in CANONICAL_METADATA_FIELDS:\n        assert field in rendered\n''',
)

# ---------------------------------------------------------------------------
# Focused regressions for all four Codex mutations.
# ---------------------------------------------------------------------------
append_once(
    registry,
    "def test_mismatched_backtick_runs_cannot_hide_duplicate_doi():",
    '''def test_mismatched_backtick_runs_cannot_hide_duplicate_doi():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))\n    section = _registered_sections(corpus)[entry]\n    injected = (\n        "`\\n"\n        "**DOI:** https://doi.org/10.0000/fabricated\\n"\n        "``\\n\\n"\n        "**Source type:**"\n    )\n    mutated = section.replace("**Source type:**", injected, 1)\n    with pytest.raises(AssertionError, match="exactly one mandatory field"):\n        _validate_registered_entry(entry, mutated)\n\n\ndef test_multiline_inline_link_title_destination_is_pinned():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    entry = "### *Black Comedy* (ABC, 2014-2020)"\n    section = _registered_sections(corpus)[entry]\n    source_line = next(\n        line for line in section.splitlines()\n        if line.startswith("**Registered source:**")\n    )\n    mutated = section.replace(\n        source_line,\n        source_line\n        + '\\n[alternate](https://www.wikipedia.org/\\n "title")',\n        1,\n    )\n    with pytest.raises(AssertionError, match="registered-source destinations changed"):\n        _validate_registered_entry(entry, mutated)\n''',
)

append_once(
    receipt,
    "def test_policing_metadata_fields_must_be_browser_visible():",
    '''def test_policing_metadata_fields_must_be_browser_visible():\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    section = _policing_methodology_section(methodology)\n    hidden_lines: list[str] = []\n    for line in section.splitlines():\n        if any(f"**{field}**" in line for field in CANONICAL_METADATA_FIELDS):\n            hidden_lines.append(f"<!-- {line} -->")\n        else:\n            hidden_lines.append(line)\n    mutated_section = "\\n".join(hidden_lines)\n    mutated = methodology.replace(section, mutated_section, 1)\n\n    with pytest.raises(AssertionError):\n        _assert_canonical_policing_metadata(mutated)\n''',
)

print("Applied four fresh PR4 review repairs.")
