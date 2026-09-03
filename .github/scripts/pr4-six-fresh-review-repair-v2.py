from pathlib import Path

path = Path('.github/scripts/pr4-six-fresh-review-repair.py')
text = path.read_text(encoding='utf-8')

old = '''policing = replace_once(
    policing,
    ''' + "'''" + '''        else:
            assert visible_clause in workstream, (
                f\"missing policing-workstream safeguard: {clause}\"
            )
''' + "'''" + ''',
    ''' + "'''" + '''        else:
            assert visible_clause in workstream, (
                f\"missing policing-workstream safeguard: {clause}\"
            )

    integrity_value = \"\\\\n\".join(visible_lines)
    integrity_hash = hashlib.sha256(integrity_value.encode(\"utf-8\")).hexdigest()
    assert integrity_hash == POLICING_WORKSTREAM_VISIBLE_SHA256, (
        \"browser-visible policing workstream changed: expected hash \"
        f\"{POLICING_WORKSTREAM_VISIBLE_SHA256!r}, got {integrity_hash!r}\"
    )
''' + "'''" + ''',
    \"policing complete visible section integrity\",
)
'''

new = '''if \"browser-visible policing workstream changed\" not in policing:
    boundary = \"\\ndef test_policing_context_workstream_remains_source_gated_and_noncomparative():\"
    if policing.count(boundary) != 1:
        raise SystemExit(
            \"policing complete visible section integrity: structural boundary count \"
            f\"was {policing.count(boundary)}\"
        )
    integrity = ''' + "'''" + '''

    integrity_value = \"\\\\n\".join(visible_lines)
    integrity_hash = hashlib.sha256(integrity_value.encode(\"utf-8\")).hexdigest()
    assert integrity_hash == POLICING_WORKSTREAM_VISIBLE_SHA256, (
        \"browser-visible policing workstream changed: expected hash \"
        f\"{POLICING_WORKSTREAM_VISIBLE_SHA256!r}, got {integrity_hash!r}\"
    )
''' + "'''" + '''
    policing = policing.replace(boundary, integrity + boundary, 1)
'''

count = text.count(old)
if count == 0 and new in text:
    print('v2 policing insertion already refined')
elif count != 1:
    raise SystemExit(f'expected one brittle policing insertion block, found {count}')
else:
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('refined policing integrity insertion to structural boundary')
