from pathlib import Path

POLICING = Path("tests/test_policing_context_roadmap.py")
REGRESSIONS = Path("tests/test_pr4_native_machine_dialog_regressions.py")

text = POLICING.read_text(encoding="utf-8")

old_dialog_tag = '''    dialog_tag = re.compile(r"</?dialog\\b[^>]*>", flags=re.IGNORECASE)\n'''
assert old_dialog_tag in text, "dialog_tag declaration not found"
text = text.replace(old_dialog_tag, "", 1)

old_opener = '''    open_dialog_tag = re.compile(\n        r"<dialog\\b(?=[^>]*(?:\\sopen(?:\\s*=|\\s|/?>)))[^>]*>",\n        flags=re.IGNORECASE,\n    )\n    for raw_line in live_markup.splitlines():\n'''
new_opener = '''    open_dialog_tag = re.compile(\n        r"<dialog\\b(?=[^>]*(?:\\sopen(?:\\s*=|\\s|/?>)))[^>]*>",\n        flags=re.IGNORECASE | re.DOTALL,\n    )\n    # Inspect complete opening-tag spans before source-line splitting. HTML\n    # attributes may legally cross line boundaries, so a line-local regex can\n    # miss `<dialog\\n open>`. An open dialog is an inline/reframing violation\n    # when its opener shares its source line with governed prose on either\n    # side. A clean whole-section wrapper remains supported even when the\n    # opener itself is formatted across multiple lines.\n    for open_dialog_match in open_dialog_tag.finditer(live_markup):\n        line_start = live_markup.rfind("\\n", 0, open_dialog_match.start()) + 1\n        line_end = live_markup.find("\\n", open_dialog_match.end())\n        if line_end < 0:\n            line_end = len(live_markup)\n        prefix = live_markup[line_start:open_dialog_match.start()]\n        suffix = live_markup[open_dialog_match.end():line_end]\n        if prefix.strip() or suffix.strip():\n            parser.violations.add("dialog-inline-block")\n            break\n\n    for raw_line in live_markup.splitlines():\n'''
assert old_opener in text, "open dialog block not found"
text = text.replace(old_opener, new_opener, 1)

old_line_local = '''        if open_dialog_tag.search(raw_line) is not None:\n            residual = dialog_tag.sub("", raw_line)\n            if residual.strip():\n                parser.violations.add("dialog-inline-block")\n                break\n'''
assert old_line_local in text, "line-local dialog check not found"
text = text.replace(old_line_local, "", 1)
POLICING.write_text(text, encoding="utf-8")

regressions = REGRESSIONS.read_text(encoding="utf-8")
assert "test_multiline_open_dialog_inside_governed_prose_is_rejected" not in regressions
regressions += '''\n\ndef test_multiline_open_dialog_inside_governed_prose_is_rejected() -> None:\n    fragment = (\n        "Availability through ABC iview is <dialog\\n"\n        " open>not</dialog> permission to redistribute content."\n    )\n    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)\n    corpus = CORPUS.read_text(encoding="utf-8")\n    original = "Availability through ABC iview is not permission to redistribute content."\n    mutated = corpus.replace(original, fragment, 1)\n    with pytest.raises(AssertionError, match="dialog block-container HTML"):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_multiline_whole_section_open_dialog_wrapper_remains_supported() -> None:\n    fragment = "<dialog\\n open>\\nCanonical governed prose.\\n</dialog>\\n"\n    violations = POLICING["_governed_surface_html_violations"](fragment)\n    assert "dialog-inline-block" not in violations\n'''
REGRESSIONS.write_text(regressions, encoding="utf-8")
