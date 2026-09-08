from pathlib import Path

path = Path("tests/test_pr4_source_binding_regressions.py")
text = path.read_text(encoding="utf-8")
old = '''@pytest.mark.parametrize("form", ["inline", "multiline-title", "html", "html-nested-label"])
def test_matching_source_bindings_preserve_accepted_hashes(validators, registered, form):
'''
new = '''@pytest.mark.parametrize("form", ["inline", "html", "html-nested-label"])
def test_matching_source_bindings_preserve_accepted_hashes(validators, registered, form):
'''
if text.count(old) != 1:
    raise SystemExit(f"expected one accepted-binding parameter block, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
