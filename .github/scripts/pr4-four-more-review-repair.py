from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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


registry = ROOT / "tests" / "test_research_reference_registry.py"
workstream_h = ROOT / "tests" / "test_workstream_h_methodology.py"
policing = ROOT / "tests" / "test_policing_context_roadmap.py"
receipt = ROOT / "tests" / "test_policing_contract_receipt.py"

# 1. Registry metadata labels must be recognized through arbitrary ordinary
# HTML wrappers, not only the previously special-cased paragraph/anchor forms.
replace_once(
    registry,
    '''def _strip_composed_container_prefixes(line: str) -> tuple[str, bool]:
    """Strip recursively composed quote/list prefixes and detect code indentation."""
    logical, is_code, _ = _parse_composed_container_prefixes(line)
    return logical, is_code


def _canonicalise_metadata_marker(line: str) -> str:
''',
    '''def _strip_composed_container_prefixes(line: str) -> tuple[str, bool]:
    """Strip recursively composed quote/list prefixes and detect code indentation."""
    logical, is_code, _ = _parse_composed_container_prefixes(line)
    return logical, is_code


def _leading_wrapped_html_metadata_marker(text: str) -> tuple[str, int] | None:
    """Return a leading visible strong metadata label through ordinary HTML wrappers."""
    cursor = 0
    strong_pattern = re.compile(
        r"^<(?P<tag>strong|b)\\b[^>]*>(?P<body>.*?)</(?P=tag)>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    closing_wrapper = re.compile(r"^[ \\t]*</[A-Za-z][^>]*>", flags=re.IGNORECASE)

    while cursor < len(text):
        while cursor < len(text) and text[cursor] in " \\t":
            cursor += 1
        strong = strong_pattern.match(text[cursor:])
        if strong:
            rendered_label = _visible_html_text(strong.group(0)).strip()
            if not rendered_label.endswith(":"):
                return None
            label = rendered_label[:-1].strip()
            if not label or ":" in label:
                return None
            end = cursor + strong.end()
            # Consume only immediately closing wrapper tags. If a wrapper has
            # additional visible payload after the strong label, that payload
            # remains part of the field value instead of being discarded.
            while True:
                closing = closing_wrapper.match(text[end:])
                if closing is None:
                    break
                end += closing.end()
            return label, end

        tag = HTML_TAG_PATTERN.match(text, cursor)
        if tag is None:
            return None
        token = tag.group(0)
        if token.startswith("</") or token.startswith("<!") or token.startswith("<?"):
            return None
        cursor = tag.end()
    return None


def _canonicalise_metadata_marker(line: str) -> str:
''',
)

replace_once(
    registry,
    '''    inline_links = _markdown_inline_links(decoded)
    if inline_links:
        first_link = inline_links[0]
        if first_link.start == 0 and not first_link.image:
            decoded = first_link.label + decoded[first_link.end:]
    match = STRONG_METADATA_FIELD_PATTERN.match(decoded)
''',
    '''    inline_links = _markdown_inline_links(decoded)
    if inline_links:
        first_link = inline_links[0]
        if first_link.start == 0 and not first_link.image:
            decoded = first_link.label + decoded[first_link.end:]

    wrapped_html = _leading_wrapped_html_metadata_marker(decoded)
    if wrapped_html is not None:
        label, end = wrapped_html
        return f"**{label}:**" + decoded[end:]

    match = STRONG_METADATA_FIELD_PATTERN.match(decoded)
''',
)

append_once(
    registry,
    "def test_arbitrary_html_wrapper_metadata_label_is_counted():",
    '''\n\ndef test_arbitrary_html_wrapper_metadata_label_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    doi = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"
    mutated = corpus.replace(
        doi,
        doi
        + "\\n\\n<span><strong>DOI:</strong></span> "
        + "https://doi.org/10.0000/fabricated",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registry_corpus(mutated)
''',
)

# 2. Workstream H must be bounded by rendered headings, not raw substrings in
# Markdown metadata. Reuse the already-hardened policing structural renderer.
replace_once(
    workstream_h,
    '''from pathlib import Path
import html
from html.parser import HTMLParser
import re
''',
    '''from pathlib import Path
import html
from html.parser import HTMLParser
import re
import runpy
''',
)
replace_once(
    workstream_h,
    '''ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"
''',
    '''ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"
POLICING_TEST = Path(__file__).parent / "test_policing_context_roadmap.py"
WORKSTREAM_H_HEADING = "### H. Slang density, register compression, and operational intelligibility"
WORKSTREAM_I_HEADING = "### I. Australian and United States policing-context transfer"
''',
)
replace_once(
    workstream_h,
    '''def _workstream_h(text: str) -> str:
    start = text.index("### H. Slang density")
    end = text.index("### I. Australian and United States policing-context transfer", start)
    return _visible_markdown_text(text[start:end])
''',
    '''def _rendered_heading_span(text: str, heading: str) -> tuple[int, int]:
    """Locate one browser-visible heading using the hardened structural renderer."""
    namespace = runpy.run_path(str(POLICING_TEST))
    structure = namespace["_rendered_structure"](text)
    return namespace["_visible_markdown_heading_span"](structure, heading)


def _workstream_h(text: str) -> str:
    start, _ = _rendered_heading_span(text, WORKSTREAM_H_HEADING)
    end, _ = _rendered_heading_span(text, WORKSTREAM_I_HEADING)
    assert start < end, "rendered Workstream H boundary is invalid"
    return _visible_markdown_text(text[start:end])
''',
)
append_once(
    workstream_h,
    "def test_workstream_h_start_must_be_a_visible_heading():",
    '''\n\ndef test_workstream_h_start_must_be_a_visible_heading():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    start = roadmap.index(WORKSTREAM_H_HEADING)
    end = roadmap.index(WORKSTREAM_I_HEADING, start)
    body = roadmap[start + len(WORKSTREAM_H_HEADING):end]
    mutated = (
        roadmap[:start]
        + f'[boundary](# "{WORKSTREAM_H_HEADING}")'
        + body
        + "\\n"
        + WORKSTREAM_H_HEADING
        + roadmap[end:]
    )
    section = _workstream_h(mutated)
    assert "nationality and first-language identity must not define the comparison cohorts" not in section
    assert "orientation/community-attestation sources with explicit non-representative status" not in section
''',
)

# 3. Policing visible-text link parsing must accept CommonMark's newline between
# destination and title while still excluding title metadata from visible text.
replace_once(
    policing,
    '''def _inline_link_closing_paren(text: str, start: int) -> int | None:
    depth = 1
    cursor = start + 1
    quote: str | None = None
    angle = False
    while cursor < len(text):
        character = text[cursor]
        if character in "\\r\\n":
            return None
        if character == "\\\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if quote is not None:
            if character == quote:
                quote = None
            cursor += 1
            continue
        if angle:
            if character == ">":
                angle = False
            cursor += 1
            continue
        if character in {"\\\"", "'"}:
            quote = character
            cursor += 1
            continue
        if character == "<":
            angle = True
            cursor += 1
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _replace_inline_markdown_links_for_visibility(text: str) -> str:
''',
    '''def _inline_link_closing_paren(text: str, start: int) -> int | None:
    depth = 1
    cursor = start + 1
    quote: str | None = None
    angle = False
    top_level_space = False
    while cursor < len(text):
        character = text[cursor]
        if character == "\\\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if quote is not None:
            if character == quote:
                quote = None
            cursor += 1
            continue
        if angle:
            if character in "\\r\\n":
                return None
            if character == ">":
                angle = False
            cursor += 1
            continue
        if depth == 1 and character in " \\t\\r\\n":
            top_level_space = True
            cursor += 1
            continue
        if character in "\\r\\n":
            return None
        if depth == 1 and top_level_space and character in {"\\\"", "'"}:
            quote = character
            cursor += 1
            continue
        if depth == 1 and not top_level_space and character == "<":
            angle = True
            cursor += 1
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _inline_link_destination(inner: str) -> str | None:
    """Validate the destination/title split using CommonMark inline-link rules."""
    value = inner.lstrip(" \\t\\r\\n")
    if not value:
        return None
    if value.startswith("<"):
        close = value.find(">", 1)
        if close < 0:
            return None
        destination = value[1:close]
        remainder = value[close + 1:].strip()
    else:
        cursor = 0
        depth = 0
        while cursor < len(value):
            character = value[cursor]
            if character == "\\\\" and cursor + 1 < len(value):
                cursor += 2
                continue
            if character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    return None
                depth -= 1
            elif character in " \\t\\r\\n" and depth == 0:
                break
            cursor += 1
        if depth != 0:
            return None
        destination = value[:cursor]
        remainder = value[cursor:].strip()
    if not destination:
        return None
    if remainder:
        quoted = (
            len(remainder) >= 2
            and remainder[0] in {"\\\"", "'"}
            and remainder[-1] == remainder[0]
        )
        parenthesized = (
            len(remainder) >= 2
            and remainder[0] == "("
            and remainder[-1] == ")"
        )
        if not (quoted or parenthesized):
            return None
    return destination


def _replace_inline_markdown_links_for_visibility(text: str) -> str:
''',
)
replace_once(
    policing,
    '''        paren_end = _inline_link_closing_paren(text, label_end + 1)
        if paren_end is None:
            parts.append(text[cursor:bracket + 1])
            cursor = bracket + 1
            continue
''',
    '''        paren_start = label_end + 1
        paren_end = _inline_link_closing_paren(text, paren_start)
        if (
            paren_end is None
            or _inline_link_destination(text[paren_start + 1:paren_end]) is None
        ):
            parts.append(text[cursor:bracket + 1])
            cursor = bracket + 1
            continue
''',
)
append_once(
    policing,
    "def test_policing_source_gate_cannot_hide_in_multiline_link_title():",
    '''\n\ndef test_policing_source_gate_cannot_hide_in_multiline_link_title():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "source-gated research proposal"
    mutated = roadmap.replace(
        clause,
        f'[placeholder](#\\n "{clause}")',
        1,
    )
    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):
        _validate_policing_workstream(mutated)
''',
)

# 4. The high-stakes cross-document receipt must inspect browser-visible
# methodology text, not raw Markdown that could preserve a commented-out gate.
replace_once(
    receipt,
    '''HIGH_STAKES_REVIEW_SENTENCE = (
    "before publishing any family involving coercion, consent, search, detention, "
    "questioning, force, emergency powers, or legal rights, verify the governing sources "
    "are current for the recorded jurisdiction and date and obtain appropriate review from "
    "relevant Australian and United States legal, policing, civil-liberties, and community expertise;"
)
''',
    '''HIGH_STAKES_REVIEW_SENTENCE = (
    "before publishing any family involving coercion, consent, search, detention, "
    "questioning, force, emergency powers, or legal rights, verify the governing sources "
    "are current for the recorded jurisdiction and date and obtain appropriate review from "
    "relevant Australian and United States legal, policing, civil-liberties, and community expertise;"
)
CANONICAL_HIGH_STAKES_REVIEW_SENTENCE = (
    "Before publication of a family involving coercion, consent, search, detention, questioning, "
    "force, emergency powers, or legal rights, the project must verify the governing sources are "
    "current for the recorded jurisdiction and date and obtain appropriate review from relevant "
    "Australian and United States legal, policing, civil-liberties, and community expertise."
)
''',
)
replace_once(
    receipt,
    '''def _assert_canonical_policing_metadata(methodology: str) -> None:
    policing_methodology = _policing_methodology_section(methodology)
    policing_namespace = runpy.run_path(str(POLICING_TEST))
    visible_text = policing_namespace["_visible_text"]
    rendered = visible_text(policing_methodology)
    assert POLICING_METADATA_INTRO in rendered
    for field in CANONICAL_METADATA_FIELDS:
        assert field in rendered
''',
    '''def _visible_policing_methodology(methodology: str) -> str:
    policing_namespace = runpy.run_path(str(POLICING_TEST))
    visible_text = policing_namespace["_visible_text"]
    return visible_text(_policing_methodology_section(methodology))


def _assert_canonical_policing_metadata(methodology: str) -> None:
    rendered = _visible_policing_methodology(methodology)
    assert POLICING_METADATA_INTRO in rendered
    for field in CANONICAL_METADATA_FIELDS:
        assert field in rendered


def _assert_canonical_high_stakes_gate(methodology: str) -> None:
    rendered = _visible_policing_methodology(methodology)
    assert CANONICAL_HIGH_STAKES_REVIEW_SENTENCE in rendered
    assert (
        "obtain appropriate review from relevant Australian and United States legal, policing, "
        "civil-liberties, and community expertise"
    ) in rendered
''',
)
replace_once(
    receipt,
    '''    methodology = _policing_methodology_section(
        METHODOLOGY.read_text(encoding="utf-8")
    )
    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))
''',
    '''    methodology = METHODOLOGY.read_text(encoding="utf-8")
    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))
''',
)
replace_once(
    receipt,
    '''    assert "Before publication of a family involving coercion, consent, search, detention, questioning, force, emergency powers, or legal rights" in methodology
    assert "obtain appropriate review from relevant Australian and United States legal, policing, civil-liberties, and community expertise" in methodology
''',
    '''    _assert_canonical_high_stakes_gate(methodology)
''',
)
append_once(
    receipt,
    "def test_high_stakes_methodology_gate_must_be_browser_visible():",
    '''\n\ndef test_high_stakes_methodology_gate_must_be_browser_visible():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    assert CANONICAL_HIGH_STAKES_REVIEW_SENTENCE in methodology
    mutated = methodology.replace(
        CANONICAL_HIGH_STAKES_REVIEW_SENTENCE,
        f"<!-- {CANONICAL_HIGH_STAKES_REVIEW_SENTENCE} -->",
        1,
    )
    with pytest.raises(AssertionError):
        _assert_canonical_high_stakes_gate(mutated)
''',
)

print("Applied four fresh PR #4 review repairs.")
