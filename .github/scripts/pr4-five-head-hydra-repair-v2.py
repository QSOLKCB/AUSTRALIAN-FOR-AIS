from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "pr4-five-head-hydra-repair.py"

text = SCRIPT.read_text(encoding="utf-8")

old = """    'REFERENCE_LINK_PATTERN = re.compile(\\n',\n    '''LINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN = re.compile(\\n"""
new = """    '\\nREFERENCE_LINK_PATTERN = re.compile(\\n',\n    '''\\nLINK_REFERENCE_DEFINITION_SINGLE_LINE_PATTERN = re.compile(\\n"""
if new not in text:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"reference-link anchor correction expected one source anchor, found {count}")
    text = text.replace(old, new, 1)

old = """    '''        while fence is not None and not _fence_container_continues(line, fence):\\n            fence = None\\n\\n        if fence is not None:\\n''',\n    '''        while fence is not None and not _fence_container_continues(line, fence):\\n            fence = None\\n        while (\\n"""
new = """    '''        if not line.strip():\\n            paragraph_open = False\\n\\n        while fence is not None and not _fence_container_continues(line, fence):\\n            fence = None\\n\\n        if fence is not None:\\n''',\n    '''        if not line.strip():\\n            paragraph_open = False\\n\\n        while fence is not None and not _fence_container_continues(line, fence):\\n            fence = None\\n        while (\\n"""
if new not in text:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"fence-loop anchor correction expected one source anchor, found {count}")
    text = text.replace(old, new, 1)

SCRIPT.write_text(text, encoding="utf-8")
print("Applied five-head repair anchor corrections.")
