"""Apply an exact-base repair; this runner is removed before publication."""
from pathlib import Path
import ast
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {
    'tests/test_policing_context_roadmap.py': 'b17c33628c563901acca4c84d1fe114094a9c3f3',
    'tests/test_workstream_h_methodology.py': '9871949b8aa7e6b1790ab1442f678a47c185fdd9',
}


def replace_once(text, old, new):
    assert text.count(old) == 1, ('ambiguous patch anchor', old, text.count(old))
    return text.replace(old, new, 1)


originals = {}
for name, expected in EXPECTED.items():
    path = ROOT / name
    actual = subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()
    assert actual == expected, (name, actual, expected)
    originals[name] = path.read_text(encoding='utf-8')

name = 'tests/test_policing_context_roadmap.py'
p = originals[name]
p = replace_once(p, '''        if tag == "details":
            attribute_names = {key.lower() for key, _ in attrs}
''', '''        if tag in {"iframe", "object", "embed", "audio", "video"}:
            self.violations.add("replacement-content")
        # SVG needs its own rendering tree, not HTML character-data callbacks.
        if tag == "svg":
            self.violations.add("raw-svg")
        if tag in {"del", "s", "strike"}:
            self.violations.add("semantic-deletion")
        # Parsed names cover duplicate, boolean, and multiline attributes.
        # The reducer cannot establish readability for arbitrary inline CSS.
        attribute_names = {key.lower() for key, _ in attrs}
        if "style" in attribute_names:
            self.violations.add("inline-style")
        if tag == "details":
''')
p = replace_once(p, '# Browsers ignore self-closing syntax on non-void canvas/details.', '# Apply the same policy to ordinary and self-closing tag syntax.')
p = replace_once(p, '''        rendered_line, in_comment = _mask_comments_on_line(raw_line, False)
        parts.append(rendered_line)
        paragraph_open = _line_opens_paragraph(rendered_line)
''', '''        rendered_line, in_comment = _mask_comments_on_line(raw_line, False)
        parts.append(rendered_line)
        # Indented continuation lines do not end an already-open paragraph.
        # Preserve successive HTML attribute lines for the parsed preflight.
        paragraph_open = (
            paragraph_open and indentation >= 4 and bool(rendered_line.strip())
        ) or _line_opens_paragraph(rendered_line)
''')
helper = '''

def _assert_supported_governed_html(violations: set[str]) -> None:
    """Fail closed on rendering semantics outside the shared text contract."""
    descriptions = {
        "replacement-content": "replacement-content HTML",
        "raw-svg": "raw SVG HTML",
        "inline-style": "inline style HTML",
        "semantic-deletion": "semantic deletion HTML",
    }
    for kind, description in descriptions.items():
        assert kind not in violations, (
            f"{description} is not allowed on governed methodology surfaces"
        )
'''
p = replace_once(p, '\ndef _visible_text(markdown: str) -> str:\n', helper + '\n\ndef _visible_text(markdown: str) -> str:\n')
p = replace_once(p, '''    violations = _governed_surface_html_violations(markdown)
    assert "raw-image" not in violations''', '''    violations = _governed_surface_html_violations(markdown)
    _assert_supported_governed_html(violations)
    assert "raw-image" not in violations''')
p = replace_once(p, '''    """Return the unique browser-visible Markdown heading span with preserved offsets."""
    visible_structure = _mask_hidden_html_regions(structure)
''', '''    """Return the unique browser-visible Markdown heading span with preserved offsets."""
    # Inspect before slicing or hidden-region masking can erase a wrapper
    # that starts before the heading or encloses otherwise canonical text.
    _assert_supported_governed_html(_governed_surface_html_violations(structure))
    visible_structure = _mask_hidden_html_regions(structure)
''')
# Keep testing the low-level CSS reducer, while separately testing the newly
# stricter public governance boundary. No existing case or hash is removed.
p = replace_once(p, '''def test_latest_review_shared_css_escape_and_raw_html_block_regressions():
    assert _visible_text(
        '<span style="display:n\\\\6f ne">hidden governance</span>'
    ) == ""
    assert _visible_text(
        '<span style="content-visibility:hidden">hidden governance</span>'
    ) == ""
''', '''def test_latest_review_shared_css_escape_and_raw_html_block_regressions():
    for markup in (
        '<span style="display:n\\\\6f ne">hidden governance</span>',
        '<span style="content-visibility:hidden">hidden governance</span>',
    ):
        assert _visible_html_text(markup) == ""
        with pytest.raises(AssertionError, match="inline style HTML"):
            _visible_text(markup)
''')
p = replace_once(p, '''    assert sentence not in _visible_text(hidden)

    roadmap = ROADMAP.read_text(encoding="utf-8")''', '''    assert sentence not in _visible_html_text(hidden)
    with pytest.raises(AssertionError, match="inline style HTML"):
        _visible_text(hidden)

    roadmap = ROADMAP.read_text(encoding="utf-8")''')

hname = 'tests/test_workstream_h_methodology.py'
h = originals[hname]
h = replace_once(h, '''        assert listener_clause not in _workstream_h(mutated)
''', '''        if "style=" in hidden:
            with pytest.raises(AssertionError, match="inline style HTML"):
                _workstream_h(mutated)
        else:
            assert listener_clause not in _workstream_h(mutated)
''')
h = replace_once(h, '''        assert stereotype_clause not in _trans_tasman_methodology(mutated)
''', '''        if "style=" in hidden:
            with pytest.raises(AssertionError, match="inline style HTML"):
                _trans_tasman_methodology(mutated)
        else:
            assert stereotype_clause not in _trans_tasman_methodology(mutated)
''')
h = replace_once(h, '''    assert listener_clause not in _workstream_h(mutated_roadmap)
''', '''    with pytest.raises(AssertionError, match="raw SVG HTML"):
        _workstream_h(mutated_roadmap)
''')
h = replace_once(h, '''    assert stereotype_clause not in _trans_tasman_methodology(mutated_methodology)
''', '''    with pytest.raises(AssertionError, match="raw SVG HTML"):
        _trans_tasman_methodology(mutated_methodology)
''')

for name, text in {'tests/test_policing_context_roadmap.py': p, hname: h}.items():
    ast.parse(text, filename=name)
    assert re.findall(r'[0-9a-f]{64}', text) == re.findall(r'[0-9a-f]{64}', originals[name]), 'Integrity fixtures changed'
    old_tests = {n.name for n in ast.parse(originals[name]).body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')}
    new_tests = {n.name for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')}
    assert old_tests == new_tests, 'Existing test removed or renamed'
    (ROOT / name).write_text(text, encoding='utf-8')
print('Applied four shared HTML fixes; existing integrity fixtures and test names preserved.')
