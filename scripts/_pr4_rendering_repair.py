"""Apply the reviewed, exact-blob PR4 repair and verify its regression evidence."""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

EXPECTED = {
    "tests/test_research_reference_registry.py": "b9b95a0ad1e52d89505958cb0a9f57ac9abc4623",
    "tests/test_policing_context_roadmap.py": "be483fc755cab25525777adaef600fa13c7afee9",
    "tests/test_workstream_h_methodology.py": "6c2b24388c992ca33c78655eda3b80dd9c080dfa",
    "tests/test_phase2_review_followup.py": "e7449d848b1d94987a53823c03b469dcd52bb702",
}


def replace_once(text, old, new):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one repair anchor, got {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


for name, expected in EXPECTED.items():
    actual = subprocess.check_output(["git", "hash-object", name], text=True).strip()
    if actual != expected:
        raise RuntimeError(f"Refusing to overwrite changed source: {name} {actual}")

# First prove the reviewed mutations fail against the unmodified validators.
red = subprocess.run([
    sys.executable, "-m", "pytest", "-q", "tests/test_governance_review_regressions.py",
    "--junitxml=/tmp/pr4-before.xml",
], check=False)
root = ET.parse("/tmp/pr4-before.xml").getroot()
failures = [case for case in root.iter("testcase") if case.find("failure") is not None]
errors = list(root.iter("error"))
if red.returncode != 1 or errors or len(failures) < 7:
    raise RuntimeError(f"Unexpected baseline: exit={red.returncode}, failures={len(failures)}, errors={len(errors)}")
print(f"BEFORE_REPAIR: {len(failures)} failing adversarial regressions; no collection errors", flush=True)

registry_path = Path("tests/test_research_reference_registry.py")
registry = registry_path.read_text(encoding="utf-8")
start = registry.index("class _GovernedHTMLSemanticsDetector(HTMLParser):")
end = registry.index("\n\ndef _css_hides_element", start)
block = registry[start:end]
block = replace_once(block, "        self.found: set[str] = set()", "        self.found: set[str] = set()\n        self.tags: list[str] = []")
block = replace_once(block, '        names = [key.lower() for key, _ in attrs]', '''        names = [key.lower() for key, _ in attrs]
        if "shadowrootmode" in names or "shadowroot" in names:
            self.found.add("shadow-root")
        table_descendants = {"caption", "colgroup", "thead", "tbody", "tfoot", "tr", "td", "th"}
        if tag in table_descendants and {"hidden", "popover"}.intersection(names):
            self.found.add("hidden-table-descendant")
        if tag == "a" and "a" in self.tags:
            self.found.add("nested-anchor")
        if tag not in HTML_VOID_TAGS:
            self.tags.append(tag)''')
block += '''
    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.tags) - 1, -1, -1):
            if self.tags[index] == tag:
                del self.tags[index:]
                return
'''
registry = registry[:start] + block + registry[end:]
registry = replace_once(registry,
    '    forbidden_html = _forbidden_governed_html_constructs(section)',
    '''    forbidden_html = _forbidden_governed_html_constructs(section)
    unsupported = forbidden_html & {"shadow-root", "hidden-table-descendant", "nested-anchor"}
    assert not unsupported, (
        f"{entry} contains unsupported governed HTML: {sorted(unsupported)}; "
        "shadow rendering, table insertion modes, and nested anchors must not bypass integrity"
    )''')
registry = replace_once(registry,
    '    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)',
    '''    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)
    unsupported = corpus_forbidden_html & {"shadow-root", "hidden-table-descendant", "nested-anchor"}
    assert not unsupported, (
        f"registry contains unsupported governed HTML: {sorted(unsupported)}; "
        "validate browser-sensitive constructs before masking or section slicing"
    )''')
registry_path.write_text(registry, encoding="utf-8")

policing_path = Path("tests/test_policing_context_roadmap.py")
policing = policing_path.read_text(encoding="utf-8")
policing = replace_once(policing, 'class _VisibleHTMLTextParser(HTMLParser):\n    def __init__(self) -> None:', '''RAW_HTML_LITERAL_PUNCTUATION = {"*": "\\uE110", "_": "\\uE111"}


class _VisibleHTMLTextParser(HTMLParser):
    def __init__(self, *, protect_raw_punctuation: bool = False) -> None:''')
policing = replace_once(policing,
    '        self.parts: list[str] = []\n        self.stack: list[tuple[str, bool]] = []',
    '''        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []
        self.protect_raw_punctuation = protect_raw_punctuation''')
policing = replace_once(policing, '        if "hidden" in values:\n            return True',
    '        if "hidden" in values or "popover" in values:\n            return True')
policing = replace_once(policing,
    '''    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)''',
    '''    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            if self.protect_raw_punctuation and self.stack:
                # Never promote punctuation emitted by raw HTML into Markdown
                # emphasis after parsing. Retain it in the integrity value.
                for literal, marker in RAW_HTML_LITERAL_PUNCTUATION.items():
                    data = data.replace(literal, marker)
            self.parts.append(data)''')
policing = replace_once(policing,
    '''def _visible_html_text(text: str) -> str:
    parser = _VisibleHTMLTextParser()''',
    '''def _visible_html_text(text: str, *, protect_raw_punctuation: bool = False) -> str:
    parser = _VisibleHTMLTextParser(protect_raw_punctuation=protect_raw_punctuation)''')
policing = replace_once(policing,
    '''    visible = _visible_html_text(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")''',
    '''    assert not any(marker in visible for marker in RAW_HTML_LITERAL_PUNCTUATION.values()), (
        "reserved literal-punctuation marker in governed source"
    )
    visible = _visible_html_text(visible, protect_raw_punctuation=True)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    for literal, marker in RAW_HTML_LITERAL_PUNCTUATION.items():
        visible = visible.replace(marker, literal)''')
policing_path.write_text(policing, encoding="utf-8")

h_path = Path("tests/test_workstream_h_methodology.py")
h = h_path.read_text(encoding="utf-8")
h = replace_once(h, 'def _assert_workstream_h_integrity(text: str) -> str:', '''def _rendered_inline_citation_links(text: str) -> tuple[tuple[str, str], ...]:
    """Use the registry's structural view, not hidden Markdown source text."""
    registry = runpy.run_path(str(POLICING_TEST.with_name("test_research_reference_registry.py")))
    structure = registry["_structural_registry_text"](text)
    structure = registry["_mask_hidden_html_regions"](structure)
    assert not registry["_contains_inert_html"](structure), (
        "Workstream H citations must not depend on inert, non-navigable HTML"
    )
    structure = registry["_mask_raw_html_tags_for_markdown_link_discovery"](structure)
    return _inline_markdown_links(structure)


def _assert_workstream_h_integrity(text: str) -> str:''')
h = replace_once(h, '    actual_links = set(_inline_markdown_links(raw_section))',
    '''    rendered_links = _rendered_inline_citation_links(raw_section)
    actual_links = set(rendered_links)
    assert len(rendered_links) == len(actual_links), "duplicate Workstream H citation binding"''')
h_path.write_text(h, encoding="utf-8")

notes_path = Path("tests/test_phase2_review_followup.py")
notes = notes_path.read_text(encoding="utf-8")
notes = replace_once(notes, 'def _visible_phase2_notes(changelog: str) -> str:', '''def _next_notes_peer_heading(structure: str, namespace: dict) -> int:
    """Find a visible ATX, Setext, or HTML peer heading without crossing code."""
    offset = 0
    paragraph_start = None
    paragraph_container = None
    for raw_line in structure.splitlines(keepends=True):
        logical, is_code, container = namespace["_parse_fence_container_prefixes"](
            raw_line.rstrip("\\r\\n")
        )
        stripped = logical.strip(" \\t")
        if is_code or not stripped:
            paragraph_start = None
            paragraph_container = None
        elif re.match(r"^#{1,3}(?:[ \\t]+|$)", stripped) or re.match(
            r"<h[1-3](?:[ \\t>])", stripped, re.IGNORECASE
        ):
            return offset
        elif re.fullmatch(r"(?:=+|-+)[ \\t]*", stripped):
            # A Setext underline belongs to the preceding paragraph in the
            # same container; a standalone thematic break is not a heading.
            if paragraph_start is not None and paragraph_container == container:
                return paragraph_start
            paragraph_start = None
            paragraph_container = None
        elif (namespace["THEMATIC_BREAK_PATTERN"].fullmatch(stripped)
              or re.match(r"^(?:#{4,6}(?:[ \\t]+|$)|`{3,}|~{3,}|<)", stripped)):
            paragraph_start = None
            paragraph_container = None
        else:
            if paragraph_start is None or paragraph_container != container:
                paragraph_start = offset
            paragraph_container = container
        offset += len(raw_line)
    return len(structure)


def _visible_phase2_notes(changelog: str) -> str:''')
old = '''    notes_end = len(phase2_structure)
    relative_offset = 0
    tail = visible_phase2_structure[notes_heading_end:]
    for raw_line in tail.splitlines(keepends=True):
        line = raw_line.rstrip("\\r\\n")
        logical, is_code, _ = namespace["_parse_fence_container_prefixes"](line)
        if not is_code:
            stripped = logical.strip(" \\t")
            if re.match(r"^#{1,3}(?:[ \\t]+|$)", stripped):
                notes_end = notes_heading_end + relative_offset
                break
        relative_offset += len(raw_line)'''
notes = replace_once(notes, old, '''    tail = visible_phase2_structure[notes_heading_end:]
    notes_end = notes_heading_end + _next_notes_peer_heading(tail, namespace)''')
notes_path.write_text(notes, encoding="utf-8")

for name in EXPECTED:
    compile(Path(name).read_text(encoding="utf-8"), name, "exec")
print("All exact-blob repairs applied; existing integrity fixtures are unchanged.", flush=True)
