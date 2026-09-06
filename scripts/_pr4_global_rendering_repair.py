"""Apply exact-base fixes for PR4 global rendering semantics."""
from pathlib import Path
import ast
import subprocess

EXPECTED = {
    "tests/test_policing_context_roadmap.py": "68f3131775a035e8f2229f1583ca8c8b66a9a38f",
    "tests/test_workstream_h_methodology.py": "5019d619e44ce39dc017fc9a00e43bc7a594cd87",
    "tests/test_policing_contract_receipt.py": "ba4fb0f82025e4204382279b9bc4fac3b9f48e56",
}


def once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, f"Ambiguous or changed repair anchor: {old[:100]!r}"
    return text.replace(old, new, 1)


for filename, expected in EXPECTED.items():
    actual = subprocess.check_output(["git", "hash-object", filename], text=True).strip()
    assert actual == expected, f"Refusing changed source: {filename} {actual}"

path = Path("tests/test_policing_context_roadmap.py")
text = path.read_text(encoding="utf-8")
before = ast.parse(text)
text = once(text, 'RAW_HTML_CDATA = "__cdata__"', '''RAW_HTML_CDATA = "__cdata__"
PREFLIGHT_HTML_BLANK_LINE = "__blank_line__"
# CommonMark type-6 blocks end at a blank line, not at a closing HTML tag.
PREFLIGHT_HTML_BLOCK_TAGS = frozenset({
    "address", "article", "aside", "base", "basefont", "blockquote", "body",
    "caption", "center", "col", "colgroup", "dd", "details", "dialog", "dir",
    "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
    "frame", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head",
    "header", "hr", "html", "iframe", "legend", "li", "link", "main", "menu",
    "menuitem", "nav", "noframes", "ol", "optgroup", "option", "p", "param",
    "search", "section", "summary", "table", "tbody", "td", "tfoot", "th",
    "thead", "title", "tr", "track", "ul",
})
PREFLIGHT_HTML_TAG = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?=[ \\t\\r\\n\\f/>])"
    r"(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*>", re.DOTALL,
)''')
text = once(text,
    '    logical = _raw_html_block_logical_line(line, state)\n    if state.tag == RAW_HTML_PROCESSING_INSTRUCTION:',
    '''    logical = _raw_html_block_logical_line(line, state)
    if state.tag == PREFLIGHT_HTML_BLANK_LINE:
        return not logical.strip()
    if state.tag == RAW_HTML_PROCESSING_INSTRUCTION:''')
text = once(text,
    '''def _rendered_structure(markdown: str) -> str:
    """Mask code and comments while preserving rendered prose for inspection."""''',
    '''def _rendered_structure(
    markdown: str, *, html_spans: list[tuple[int, int]] | None = None,
) -> str:
    """Mask code/comments; optionally retain raw HTML for the policy preflight.

    The ordinary structural view is unchanged. The preflight view preserves
    raw HTML blocks and records their offsets so backticks within those blocks
    cannot be reinterpreted as Markdown code and conceal live HTML elements.
    """''')
start = text.index('def _rendered_structure(')
end = text.index('\ndef _is_escaped_markdown_character', start)
block = text[start:end]
block = once(block,
    '    for raw_line in markdown.splitlines(keepends=True):\n        line = raw_line.rstrip("\\r\\n")',
    '''    offset = 0
    for raw_line in markdown.splitlines(keepends=True):
        line_start = offset
        offset += len(raw_line)
        line = raw_line.rstrip("\\r\\n")''')
block = once(block,
    '''        if raw_html is not None:
            parts.append(_mask_non_newline(raw_line))''',
    '''        if raw_html is not None:
            if html_spans is not None:
                parts.append(raw_line)
                html_spans.append((line_start, offset))
            else:
                parts.append(_mask_non_newline(raw_line))''')
block = once(block,
    '''        raw_opener = _raw_html_block_opener(line)
        if raw_opener is not None:
            parts.append(_mask_non_newline(raw_line))''',
    '''        raw_opener = _raw_html_block_opener(line)
        if raw_opener is None and html_spans is not None:
            logical_html, is_code, containers = _parse_fence_container_prefixes(line)
            candidate = logical_html.strip(" \\t")
            tag_match = re.match(r"</?([A-Za-z][A-Za-z0-9-]*)(?=[ \\t\\r\\n\\f/>]|$)", candidate)
            if not is_code and tag_match is not None:
                type6 = tag_match.group(1).lower() in PREFLIGHT_HTML_BLOCK_TAGS
                type7 = not paragraph_open and PREFLIGHT_HTML_TAG.fullmatch(candidate) is not None
                if type6 or type7:
                    raw_opener = RawHTMLBlockState(PREFLIGHT_HTML_BLANK_LINE, containers)
        if raw_opener is not None:
            if html_spans is not None:
                parts.append(raw_line)
                html_spans.append((line_start, offset))
            else:
                parts.append(_mask_non_newline(raw_line))''')
text = text[:start] + block + text[end:]
text = once(text,
    '''        if tag == "svg":
            self.violations.add("raw-svg")''',
    '''        if tag == "svg":
            self.violations.add("raw-svg")
        if tag == "math":
            self.violations.add("raw-mathml")
        if tag in {"style", "link"}:
            self.violations.add("stylesheet")''')
text = once(text,
    '''        if "style" in attribute_names:
            self.violations.add("inline-style")''',
    '''        if "style" in attribute_names:
            self.violations.add("inline-style")
        if "class" in attribute_names:
            self.violations.add("stylesheet")
        if tag == "bdo" or "dir" in attribute_names:
            self.violations.add("bidirectional")''')
text = once(text,
    '''    parser = _GovernedSurfaceHTMLParser()
    structure = _rendered_structure(markdown)''',
    '''    parser = _GovernedSurfaceHTMLParser()
    html_spans: list[tuple[int, int]] = []
    structure = _rendered_structure(markdown, html_spans=html_spans)''')
text = once(text,
    '''    raw_tag = re.compile(
        r"</?[A-Za-z][A-Za-z0-9-]*(?=[ \\t\\r\\n\\f/>])"
        r"(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*>", re.DOTALL,
    )
    characters = list(structure)
    cursor = 0
    while cursor < len(structure):
        tag_match = raw_tag.match(structure, cursor)''',
    '''    characters = list(structure)
    cursor = 0
    span_index = 0
    while cursor < len(structure):
        while span_index < len(html_spans) and html_spans[span_index][1] <= cursor:
            span_index += 1
        if span_index < len(html_spans) and html_spans[span_index][0] <= cursor:
            cursor = html_spans[span_index][1]
            continue
        tag_match = PREFLIGHT_HTML_TAG.match(structure, cursor)''')
text = once(text,
    '''        "semantic-deletion": "semantic deletion HTML",
    }''',
    '''        "semantic-deletion": "semantic deletion HTML",
        "stylesheet": "stylesheet/class-driven HTML",
        "raw-mathml": "raw MathML HTML",
        "bidirectional": "bidirectional HTML",
    }''')
text = once(text,
    '''def _rendered_policing_workstream(roadmap: str) -> str:
    structure = _rendered_structure(roadmap)
    try:
        start, _ = _visible_markdown_heading_span(structure, WORKSTREAM_HEADING)''',
    '''def _rendered_policing_workstream(roadmap: str) -> str:
    try:
        # Global styles and ancestor direction can affect a section even when
        # their source lies outside its heading boundaries.
        _assert_supported_governed_html(_governed_surface_html_violations(roadmap))
        structure = _rendered_structure(roadmap)
        start, _ = _visible_markdown_heading_span(structure, WORKSTREAM_HEADING)''')
# No test bodies, receipts, or existing contract constants are changed.
after = ast.parse(text)
for node in before.body:
    if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
        replacement = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == node.name)
        assert ast.dump(node) == ast.dump(replacement), node.name
path.write_text(text, encoding="utf-8")

path = Path("tests/test_workstream_h_methodology.py")
text = path.read_text(encoding="utf-8")
text = once(text,
    '''    namespace = runpy.run_path(str(POLICING_TEST))
    structure = namespace["_rendered_structure"](text)''',
    '''    namespace = runpy.run_path(str(POLICING_TEST))
    namespace["_assert_supported_governed_html"](
        namespace["_governed_surface_html_violations"](text)
    )
    structure = namespace["_rendered_structure"](text)''')
path.write_text(text, encoding="utf-8")

path = Path("tests/test_policing_contract_receipt.py")
text = path.read_text(encoding="utf-8")
text = once(text,
    '''    policing_namespace = runpy.run_path(str(POLICING_TEST))
    structure = policing_namespace["_rendered_structure"](methodology)''',
    '''    policing_namespace = runpy.run_path(str(POLICING_TEST))
    policing_namespace["_assert_supported_governed_html"](
        policing_namespace["_governed_surface_html_violations"](methodology)
    )
    structure = policing_namespace["_rendered_structure"](methodology)''')
path.write_text(text, encoding="utf-8")
for filename in EXPECTED:
    compile(Path(filename).read_text(encoding="utf-8"), filename, "exec")
print("Applied global stylesheet, MathML and bidirectional preflight repairs; existing tests and integrity values unchanged.")
