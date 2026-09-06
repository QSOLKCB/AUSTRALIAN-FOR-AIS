from __future__ import annotations

from pathlib import Path

script_path = Path(__file__).with_name("pr4-latest-review-repair.py")
source = script_path.read_text(encoding="utf-8")
old = '''replace_once(
    "tests/test_workstream_h_methodology.py",
    old_policing_css,
    new_policing_css,
    "Workstream H opacity semantics",
)
'''
new = '''old_workstream_css = old_policing_css.replace(
    '            winners[name] = (important, value)\\n\\n    display =',
    '            winners[name] = (important, value)\\n    display =',
)
replace_once(
    "tests/test_workstream_h_methodology.py",
    old_workstream_css,
    new_policing_css,
    "Workstream H opacity semantics",
)
'''
if source.count(old) != 1:
    raise SystemExit("repair-v2: expected exactly one Workstream H call anchor")
source = source.replace(old, new, 1)
namespace = {"__file__": str(script_path), "__name__": "__main__"}
exec(compile(source, str(script_path), "exec"), namespace)
