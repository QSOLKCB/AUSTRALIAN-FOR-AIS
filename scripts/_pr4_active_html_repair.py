"""Apply the exact-reviewed active-document HTML repair without changing fixtures."""
from pathlib import Path
import ast
import subprocess

BASE = "d3e9cf8943259bae5731d50a85fc7c99c14ab22a"
EXPECTED = {
    "tests/test_policing_context_roadmap.py": "60f60e5fd955e347188739c598ca0b50d36a7223",
    "tests/test_research_reference_registry.py": "758575bd4bcb7f3e20d050f50d82ea30dae2182c",
}


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Repair anchor count {count}, expected one: {old[:100]!r}")
    return text.replace(old, new, 1)


for filename, expected in EXPECTED.items():
    actual = subprocess.check_output(["git", "hash-object", filename], text=True).strip()
    if actual != expected:
        raise RuntimeError(f"Source changed; refusing stale repair: {filename} {actual}")

p = Path("tests/test_policing_context_roadmap.py")
text = p.read_text(encoding="utf-8")
text = replace_once(text, 'class _GovernedSurfaceHTMLParser(HTMLParser):', '''GOVERNED_CONDITIONAL_RAW_TEXT_TAGS = frozenset({
    "noscript", "plaintext", "xmp", "listing", "noframes", "noembed",
})


class _GovernedSurfaceHTMLParser(HTMLParser):''')
text = replace_once(text,
    '        if tag in {"style", "link"}:\n            self.violations.add("stylesheet")',
    '''        if tag in {"style", "link"}:
            self.violations.add("stylesheet")
        # Non-rendering character data does not make an element harmless:
        # scripts can rewrite the document, and conditional text can vanish.
        if tag == "script":
            self.violations.add("executable-script")
        if tag in GOVERNED_CONDITIONAL_RAW_TEXT_TAGS:
            self.violations.add("conditional-raw-text")''')
text = replace_once(text,
    '        attribute_names = {key.lower() for key, _ in attrs}',
    '''        attribute_names = {key.lower() for key, _ in attrs}
        if {"shadowrootmode", "shadowroot"}.intersection(attribute_names):
            self.violations.add("shadow-root")
        # HTMLParser decodes attribute references once. Preserve the first
        # duplicate attribute, matching the browser's effective directive.
        values: dict[str, str] = {}
        for key, value in attrs:
            values.setdefault(key.lower(), value or "")
        if tag == "meta" and values.get("http-equiv", "").strip().lower() == "refresh":
            self.violations.add("meta-refresh")''')
text = replace_once(text,
    '        "bidirectional": "bidirectional HTML",',
    '''        "bidirectional": "bidirectional HTML",
        "conditional-raw-text": "conditional/legacy raw-text HTML",
        "shadow-root": "declarative shadow-root HTML",
        "meta-refresh": "meta-refresh HTML",
        "executable-script": "executable script HTML",''')
p.write_text(text, encoding="utf-8")

r = Path("tests/test_research_reference_registry.py")
text = r.read_text(encoding="utf-8")
text = replace_once(text, 'import re\nimport string\n', 'import re\nimport runpy\nimport string\n')
text = replace_once(text, 'import pytest\n\n\nCORPUS =', '''import pytest


# Reuse the raw-HTML-preserving scanner for document-active elements. Unlike
# a structural Markdown view, it does not treat backticks inside raw HTML
# blocks as code or discard executable script blocks before inspection.
_SHARED_HTML_PREFLIGHT = runpy.run_path(
    str(Path(__file__).with_name("test_policing_context_roadmap.py"))
)["_governed_surface_html_violations"]
ACTIVE_DOCUMENT_HTML_KINDS = frozenset({"executable-script", "meta-refresh"})


CORPUS =''')
start = text.index('class _GovernedHTMLSemanticsDetector(HTMLParser):')
end = text.index('\n\ndef _css_hides_element', start)
block = text[start:end]
block = replace_once(block, '        names = [key.lower() for key, _ in attrs]', '''        names = [key.lower() for key, _ in attrs]
        if tag == "script":
            self.found.add("executable-script")
        values = _first_html_attribute_values(attrs)
        if tag == "meta" and values.get("http-equiv", "").strip().lower() == "refresh":
            self.found.add("meta-refresh")''')
text = text[:start] + block + text[end:]
start = text.index('def _forbidden_governed_html_constructs(text: str) -> set[str]:')
end = text.index('\n\ndef _normalise_complete_entry_integrity', start)
block = text[start:end]
block = replace_once(block, '    found: set[str] = set()', '''    found = _SHARED_HTML_PREFLIGHT(text) & ACTIVE_DOCUMENT_HTML_KINDS''')
text = text[:start] + block + text[end:]
text = replace_once(text, 'def _normalise_complete_entry_integrity(section: str) -> str:', '''def _assert_no_active_document_html(found: set[str]) -> None:
    """Reject actions that can replace the document without changing its text."""
    assert "executable-script" not in found, "executable script HTML is not allowed in governed documents"
    assert "meta-refresh" not in found, "meta-refresh HTML is not allowed in governed documents"


def _normalise_complete_entry_integrity(section: str) -> str:''')
text = replace_once(text,
    '    forbidden_html = _forbidden_governed_html_constructs(section)',
    '    forbidden_html = _forbidden_governed_html_constructs(section)\n    _assert_no_active_document_html(forbidden_html)')
text = replace_once(text,
    '    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)\n', '')
text = replace_once(text, 'def _validate_registry_corpus(corpus: str) -> None:', '''def _validate_registry_corpus(corpus: str) -> None:
    # Check the original document before any heading slicing or masking.
    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)
    _assert_no_active_document_html(corpus_forbidden_html)''')
r.write_text(text, encoding="utf-8")

for filename in EXPECTED:
    before = ast.parse(subprocess.check_output(["git", "show", BASE + ":" + filename], text=True))
    after = ast.parse(Path(filename).read_text(encoding="utf-8"))
    before_tests = {n.name: ast.dump(n) for n in before.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    after_tests = {n.name: ast.dump(n) for n in after.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    assert before_tests == after_tests, "Existing regression tests changed"
    def constants(tree):
        return {
            ast.dump(node.targets[0]): ast.dump(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and ("HASH" in target.id or "SHA256" in target.id or target.id == "ENTRY_CONTRACTS") for target in node.targets)
        }
    assert constants(before) == constants(after), "Existing integrity fixtures changed"
print("Applied four active-document HTML repairs; existing tests and integrity fixtures unchanged.", flush=True)
