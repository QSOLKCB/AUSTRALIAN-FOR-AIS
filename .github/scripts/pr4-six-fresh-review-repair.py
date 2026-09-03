from __future__ import annotations

import hashlib
from pathlib import Path
import re
import runpy

REGISTRY = Path("tests/test_research_reference_registry.py")
POLICING = Path("tests/test_policing_context_roadmap.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0 and new in text:
        return text
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one old anchor, found {count}")
    return text.replace(old, new, 1)


def insert_after_block(text: str, start_marker: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        return text
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"{label}: start marker not found")
    close = text.find("})", start)
    if close < 0:
        raise SystemExit(f"{label}: closing marker not found")
    close += 2
    return text[:close] + insertion + text[close:]


registry = REGISTRY.read_text(encoding="utf-8")

registry = replace_once(
    registry,
    'SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})\nRAW_HTML_BLOCK_TAGS = frozenset({"pre", "script", "style", "textarea"})\n',
    '''SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})
RAW_HTML_BLOCK_TAGS = frozenset({"pre", "script", "style", "textarea"})
RAW_HTML_PROCESSING_INSTRUCTION = "__processing_instruction__"
RAW_HTML_DECLARATION = "__declaration__"
RAW_HTML_CDATA = "__cdata__"
CSS_COMMENT_PATTERN = re.compile(r"/\\*.*?\\*/", flags=re.DOTALL)
COMMONMARK_CHARACTER_REFERENCE_PATTERN = re.compile(
    r"&(?:#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});"
)
GOVERNED_INTERACTIVE_HTML_PATTERN = re.compile(
    r"<(?:form|input|button|select|textarea|option|optgroup)\\b",
    flags=re.IGNORECASE,
)


def _css_hides_element(style: str) -> bool:
    """Interpret actual display/visibility declarations, not substrings in values."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        name = name.strip()
        value = re.sub(r"\\s*!important\\s*$", "", value.strip())
        if name == "display" and value == "none":
            return True
        if name == "visibility" and value in {"hidden", "collapse"}:
            return True
    return False
''',
    "registry shared visibility constants",
)

registry = insert_after_block(
    registry,
    "HTML_P_IMPLIED_END_START_TAGS = frozenset({",
    '''

HTML_IMPLIED_END_TARGETS = {
    "li": frozenset({"li"}),
    "dt": frozenset({"dt", "dd"}),
    "dd": frozenset({"dt", "dd"}),
    "rt": frozenset({"rt", "rp"}),
    "rp": frozenset({"rt", "rp"}),
    "option": frozenset({"option"}),
    "optgroup": frozenset({"option", "optgroup"}),
    "thead": frozenset({"thead", "tbody", "tfoot"}),
    "tbody": frozenset({"thead", "tbody", "tfoot"}),
    "tfoot": frozenset({"thead", "tbody", "tfoot"}),
    "tr": frozenset({"tr"}),
    "td": frozenset({"td", "th"}),
    "th": frozenset({"td", "th"}),
}
''',
    "registry implied end targets",
)

old_style = '''        style = re.sub(
            r"/\\*.*?\\*/",
            "",
            values.get("style", "").lower(),
            flags=re.DOTALL,
        )
        style = re.sub(r"\\s+", "", style)
        return "display:none" in style or "visibility:hidden" in style
'''
registry = replace_once(
    registry,
    old_style,
    '        return _css_hides_element(values.get("style", ""))\n',
    "registry CSS declaration parsing",
)

old_visible_implied = '''    def _apply_implied_paragraph_end(self, tag: str) -> None:
        if tag not in HTML_P_IMPLIED_END_START_TAGS:
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == "p":
                del self.stack[index:]
                return
'''
new_visible_implied = '''    def _apply_implied_paragraph_end(self, tag: str) -> None:
        if tag in HTML_P_IMPLIED_END_START_TAGS:
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == "p":
                    del self.stack[index:]
                    return

        targets = HTML_IMPLIED_END_TARGETS.get(tag)
        if not targets:
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] in targets:
                del self.stack[index:]
                return
'''
registry = replace_once(
    registry,
    old_visible_implied,
    new_visible_implied,
    "registry visible implied end tags",
)

old_hidden_implied = '''    def _apply_implied_paragraph_end(self, tag: str, start: int) -> None:
        if tag not in HTML_P_IMPLIED_END_START_TAGS:
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] != "p":
                continue
            popped = self.stack[index:]
            del self.stack[index:]
            for _, _, root_start in popped:
                if root_start is not None:
                    self.spans.append((root_start, start))
            return
'''
new_hidden_implied = '''    def _apply_implied_paragraph_end(self, tag: str, start: int) -> None:
        targets: frozenset[str] | None = None
        if tag in HTML_P_IMPLIED_END_START_TAGS:
            targets = frozenset({"p"})
        else:
            targets = HTML_IMPLIED_END_TARGETS.get(tag)
        if not targets:
            return

        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] not in targets:
                continue
            popped = self.stack[index:]
            del self.stack[index:]
            for _, _, root_start in popped:
                if root_start is not None:
                    self.spans.append((root_start, start))
            return
'''
registry = replace_once(
    registry,
    old_hidden_implied,
    new_hidden_implied,
    "registry hidden-region implied end tags",
)

old_raw_opener = '''def _raw_html_block_opener(line: str) -> RawHTMLBlockState | None:
    """Return a CommonMark type-1 raw HTML block opener."""
    logical, indented_code, containers = _parse_composed_container_prefixes(line)
    if indented_code:
        return None
    candidate = logical.lstrip(" \\t")
    match = re.match(
        r"<(?P<tag>pre|script|style|textarea)(?:[ \\t]|>|$)",
        candidate,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    return RawHTMLBlockState(
        tag=match.group("tag").lower(),
        containers=containers,
    )
'''
new_raw_opener = '''def _raw_html_block_opener(line: str) -> RawHTMLBlockState | None:
    """Return a CommonMark raw HTML block opener with its terminator family."""
    logical, indented_code, containers = _parse_composed_container_prefixes(line)
    if indented_code:
        return None
    candidate = logical.lstrip(" \\t")

    if candidate.startswith("<?"):
        return RawHTMLBlockState(
            tag=RAW_HTML_PROCESSING_INSTRUCTION,
            containers=containers,
        )
    if candidate.startswith("<![CDATA["):
        return RawHTMLBlockState(tag=RAW_HTML_CDATA, containers=containers)
    if re.match(r"<![A-Z]", candidate):
        return RawHTMLBlockState(tag=RAW_HTML_DECLARATION, containers=containers)

    match = re.match(
        r"<(?P<tag>pre|script|style|textarea)(?:[ \\t]|>|$)",
        candidate,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    return RawHTMLBlockState(
        tag=match.group("tag").lower(),
        containers=containers,
    )
'''
registry = replace_once(
    registry,
    old_raw_opener,
    new_raw_opener,
    "registry CommonMark raw HTML block openers",
)

old_raw_close = '''def _raw_html_block_closes(line: str, state: RawHTMLBlockState) -> bool:
    logical = _raw_html_block_logical_line(line, state)
    return bool(
        re.search(
            rf"</{re.escape(state.tag)}[ \\t]*>",
            logical,
            flags=re.IGNORECASE,
        )
    )
'''
new_raw_close = '''def _raw_html_block_closes(line: str, state: RawHTMLBlockState) -> bool:
    logical = _raw_html_block_logical_line(line, state)
    if state.tag == RAW_HTML_PROCESSING_INSTRUCTION:
        return "?>" in logical
    if state.tag == RAW_HTML_CDATA:
        return "]]>" in logical
    if state.tag == RAW_HTML_DECLARATION:
        return ">" in logical
    return bool(
        re.search(
            rf"</{re.escape(state.tag)}[ \\t]*>",
            logical,
            flags=re.IGNORECASE,
        )
    )
'''
registry = replace_once(
    registry,
    old_raw_close,
    new_raw_close,
    "registry CommonMark raw HTML block closers",
)

registry = replace_once(
    registry,
    '''def _normalise_https_destination(candidate: str) -> str | None:
    value = html.unescape(candidate)
    value = MARKDOWN_BACKSLASH_ESCAPE_PATTERN.sub(r"\\1", value)
''',
    '''def _normalise_https_destination(candidate: str) -> str | None:
    value = COMMONMARK_CHARACTER_REFERENCE_PATTERN.sub(
        lambda match: html.unescape(match.group(0)),
        candidate,
    )
    value = MARKDOWN_BACKSLASH_ESCAPE_PATTERN.sub(r"\\1", value)
''',
    "registry strict CommonMark character references",
)

registry = replace_once(
    registry,
    '''def _require_complete_entry_integrity(entry: str, section: str) -> None:
    expected_hash = ENTRY_RENDERED_VALUE_HASHES.get(entry)
    assert expected_hash is not None, f"{entry} has no complete rendered-entry integrity fixture"
    value = _normalise_complete_entry_integrity(section)
''',
    '''def _require_complete_entry_integrity(entry: str, section: str) -> None:
    expected_hash = ENTRY_RENDERED_VALUE_HASHES.get(entry)
    assert expected_hash is not None, f"{entry} has no complete rendered-entry integrity fixture"
    rendered_section = _rendered_registry_text(section)
    assert GOVERNED_INTERACTIVE_HTML_PATTERN.search(rendered_section) is None, (
        f"{entry} contains interactive HTML that is not permitted in governed entries"
    )
    value = _normalise_complete_entry_integrity(section)
''',
    "registry interactive HTML fail-closed gate",
)

registry_tests = r'''


def test_css_custom_property_cannot_hide_visible_duplicate_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    mutated = corpus.replace(
        heading,
        heading
        + '\n\n<span style="--note:display:none"><strong>DOI:</strong> '
        + "https://doi.org/10.0000/fabricated</span>",
        1,
    )
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


@pytest.mark.parametrize(
    "payload",
    (
        "<ul><li hidden>masked<li><strong>DOI:</strong> "
        "https://doi.org/10.0000/fabricated</ul>",
        "<dl><dt hidden>masked<dd><strong>DOI:</strong> "
        "https://doi.org/10.0000/fabricated</dl>",
    ),
)
def test_html_implied_item_end_cannot_hide_duplicate_doi(payload):
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    mutated = corpus.replace(heading, heading + "\n\n" + payload, 1)
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


@pytest.mark.parametrize(
    ("open_marker", "close_marker"),
    (
        ("<?hidden", "?>"),
        ("<![CDATA[", "]]>")
    ),
)
def test_non_type1_raw_html_block_cannot_supply_governed_batch_structure(
    open_marker,
    close_marker,
):
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(BATCH_HEADING)
    end = corpus.index(BATCH_END, start) + len(BATCH_END)
    governed = corpus[start:end]
    mutated = corpus[:start] + open_marker + "\n" + governed + "\n" + close_marker + corpus[end:]
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_malformed_character_reference_does_not_create_https_doi_destination():
    corpus = CORPUS.read_text(encoding="utf-8")
    expected = "https://doi.org/10.7592/EJHR2021.9.4.560"
    replacement = (
        "[https://doi.org/10.7592/EJHR2021.9.4.560]"
        "(https&#58//doi.org/10.7592/EJHR2021.9.4.560)"
    )
    mutated = corpus.replace(f"**DOI:** {expected}", f"**DOI:** {replacement}", 1)
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_interactive_form_control_cannot_bypass_complete_entry_integrity():
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = "### *Black Comedy* (ABC, 2014-2020)"
    payload = (
        '<input value="This work proves universal facts about all Aboriginal speakers.">'
    )
    mutated = corpus.replace(heading, heading + "\n\n" + payload, 1)
    with pytest.raises(AssertionError, match="interactive HTML"):
        _validate_registry_corpus(mutated)
'''
if "test_css_custom_property_cannot_hide_visible_duplicate_doi" not in registry:
    registry += registry_tests

REGISTRY.write_text(registry, encoding="utf-8")

policing = POLICING.read_text(encoding="utf-8")
policing = replace_once(
    policing,
    'from dataclasses import dataclass\nfrom pathlib import Path\nimport html\n',
    'from dataclasses import dataclass\nfrom pathlib import Path\nimport hashlib\nimport html\n',
    "policing hashlib import",
)
policing = replace_once(
    policing,
    'WORKSTREAM_END_HEADING = "## Phase 3 — Multi-Annotator Culturally Contextualised Dataset"\n',
    'WORKSTREAM_END_HEADING = "## Phase 3 — Multi-Annotator Culturally Contextualised Dataset"\nPOLICING_WORKSTREAM_VISIBLE_SHA256 = "__SEED_POLICING_WORKSTREAM_HASH__"\n',
    "policing integrity constant",
)
policing = replace_once(
    policing,
    'SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})\n',
    '''SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})
CSS_COMMENT_PATTERN = re.compile(r"/\\*.*?\\*/", flags=re.DOTALL)


def _css_hides_element(style: str) -> bool:
    """Interpret actual display/visibility declarations, not substrings in values."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        name = name.strip()
        value = re.sub(r"\\s*!important\\s*$", "", value.strip())
        if name == "display" and value == "none":
            return True
        if name == "visibility" and value in {"hidden", "collapse"}:
            return True
    return False
''',
    "policing CSS declaration helper",
)
policing = replace_once(
    policing,
    old_style,
    '        return _css_hides_element(values.get("style", ""))\n',
    "policing CSS declaration parsing",
)

policing = replace_once(
    policing,
    '''        else:
            assert visible_clause in workstream, (
                f"missing policing-workstream safeguard: {clause}"
            )
''',
    '''        else:
            assert visible_clause in workstream, (
                f"missing policing-workstream safeguard: {clause}"
            )

    integrity_value = "\\n".join(visible_lines)
    integrity_hash = hashlib.sha256(integrity_value.encode("utf-8")).hexdigest()
    assert integrity_hash == POLICING_WORKSTREAM_VISIBLE_SHA256, (
        "browser-visible policing workstream changed: expected hash "
        f"{POLICING_WORKSTREAM_VISIBLE_SHA256!r}, got {integrity_hash!r}"
    )
''',
    "policing complete visible section integrity",
)

policing_test = r'''


def test_policing_companion_contradiction_changes_complete_visible_section():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    source_gate = AFFIRMATIVE_EXACT_LINE_OVERRIDES[
        "register official and current sources for each Australian and United States jurisdictional claim"
    ]
    mutated = roadmap.replace(
        source_gate,
        source_gate
        + "\n- Official and current sources are optional for every jurisdictional claim.",
        1,
    )
    with pytest.raises(AssertionError, match="browser-visible policing workstream changed"):
        _validate_policing_workstream(mutated)
'''
if "test_policing_companion_contradiction_changes_complete_visible_section" not in policing:
    policing += policing_test

POLICING.write_text(policing, encoding="utf-8")

# Seed the complete visible Workstream I fixture from the current checked-in roadmap.
namespace = runpy.run_path(str(POLICING))
roadmap = Path("ROADMAP.md").read_text(encoding="utf-8")
rendered = namespace["_rendered_policing_workstream"](roadmap)
visible_lines: list[str] = []
for raw_line in rendered.splitlines():
    line = namespace["_visible_text"](raw_line).strip()
    line = re.sub(r"^(?:[-+*]|\\d{1,9}[.)])\\s+", "", line)
    if line:
        visible_lines.append(line)
fixture = hashlib.sha256("\n".join(visible_lines).encode("utf-8")).hexdigest()
policing = POLICING.read_text(encoding="utf-8")
placeholder = 'POLICING_WORKSTREAM_VISIBLE_SHA256 = "__SEED_POLICING_WORKSTREAM_HASH__"'
if placeholder not in policing:
    if f'POLICING_WORKSTREAM_VISIBLE_SHA256 = "{fixture}"' not in policing:
        raise SystemExit("policing integrity placeholder missing")
else:
    policing = policing.replace(
        placeholder,
        f'POLICING_WORKSTREAM_VISIBLE_SHA256 = "{fixture}"',
        1,
    )
    POLICING.write_text(policing, encoding="utf-8")

print("six-fresh-review repair applied; policing fixture", fixture)
