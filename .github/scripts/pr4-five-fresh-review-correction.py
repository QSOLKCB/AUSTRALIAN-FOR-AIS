from pathlib import Path

path = Path(__file__).with_name("pr4-five-fresh-review-repair.py")
text = path.read_text(encoding="utf-8")
old = '''workstream_h = replace_once(
    workstream_h,
    '    section = _workstream_h(ROADMAP.read_text(encoding="utf-8"))\\n',
    '    section = _assert_workstream_h_integrity(ROADMAP.read_text(encoding="utf-8"))\\n',
    label="Workstream H primary receipt integrity call",
)
'''
new = '''workstream_h = replace_once(
    workstream_h,
    ''' + "'''" + '''def test_workstream_h_decouples_dialect_exposure_from_listener_identity():
    section = _workstream_h(ROADMAP.read_text(encoding=\"utf-8\"))
''' + "'''" + ''',
    ''' + "'''" + '''def test_workstream_h_decouples_dialect_exposure_from_listener_identity():
    section = _assert_workstream_h_integrity(ROADMAP.read_text(encoding=\"utf-8\"))
''' + "'''" + ''',
    label="Workstream H primary receipt integrity call",
)
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"correction anchor: expected 1, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Narrowed Workstream H primary receipt mutation")
