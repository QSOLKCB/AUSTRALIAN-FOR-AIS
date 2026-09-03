from __future__ import annotations

import hashlib
from pathlib import Path
import re
import runpy

REGISTRY = Path("tests/test_research_reference_registry.py")
POLICING = Path("tests/test_policing_context_roadmap.py")


registry = REGISTRY.read_text(encoding="utf-8")

helper_marker = "NON_COMMONMARK_CHARACTER_REFERENCE_CANDIDATE = re.compile("
if helper_marker not in registry:
    insertion_point = registry.find("def _normalise_https_destination(candidate: str) -> str | None:\n")
    if insertion_point < 0:
        raise SystemExit("v3: registry destination-normalizer boundary not found")
    helper = '''NON_COMMONMARK_CHARACTER_REFERENCE_CANDIDATE = re.compile(
    r"&(?:#[xX][0-9A-Fa-f]+|#[0-9]+|[A-Za-z][A-Za-z0-9]*)"
)


def _reject_non_commonmark_character_references(text: str) -> None:
    """Reject semicolonless references that Python would decode but CommonMark would not."""
    visible = _mask_hidden_html_regions(_rendered_registry_text(text))
    for match in NON_COMMONMARK_CHARACTER_REFERENCE_CANDIDATE.finditer(visible):
        if match.end() < len(visible) and visible[match.end()] == ";":
            continue
        candidate = match.group(0)
        if html.unescape(candidate) != candidate:
            raise AssertionError(
                "non-CommonMark character reference is not permitted in a governed entry: "
                f"{candidate!r}"
            )


'''
    registry = registry[:insertion_point] + helper + registry[insertion_point:]

call_anchor = ''') -> None:
    destinations = _require_registered_source_link(
'''
call_replacement = ''') -> None:
    _reject_non_commonmark_character_references(section)
    destinations = _require_registered_source_link(
'''
if "_reject_non_commonmark_character_references(section)" not in registry:
    count = registry.count(call_anchor)
    if count != 1:
        raise SystemExit(f"v3: expected one registered-entry call anchor, found {count}")
    registry = registry.replace(call_anchor, call_replacement, 1)

REGISTRY.write_text(registry, encoding="utf-8")


policing = POLICING.read_text(encoding="utf-8")
helper_name = "def _normalised_visible_workstream_lines(rendered: str) -> list[str]:"
if helper_name not in policing:
    validate_boundary = "def _validate_policing_workstream(roadmap: str) -> None:\n"
    index = policing.find(validate_boundary)
    if index < 0:
        raise SystemExit("v3: policing validator boundary not found")
    helper = '''def _normalised_visible_workstream_lines(rendered: str) -> list[str]:
    """Return the canonical browser-visible line sequence used by Workstream I integrity."""
    visible_lines: list[str] = []
    for raw_line in rendered.splitlines():
        line = _visible_text(raw_line).strip()
        line = re.sub(r"^(?:[-+*]|\\d{1,9}[.)])\\s+", "", line)
        if line:
            visible_lines.append(line)
    return visible_lines


'''
    policing = policing[:index] + helper + policing[index:]

old_loop = '''    visible_lines: list[str] = []
    for raw_line in rendered.splitlines():
        line = _visible_text(raw_line).strip()
        line = re.sub(r"^(?:[-+*]|\\d{1,9}[.)])\\s+", "", line)
        if line:
            visible_lines.append(line)
'''
new_loop = "    visible_lines = _normalised_visible_workstream_lines(rendered)\n"
if old_loop in policing:
    if policing.count(old_loop) != 1:
        raise SystemExit("v3: policing visible-line loop is ambiguous")
    policing = policing.replace(old_loop, new_loop, 1)
elif new_loop not in policing:
    raise SystemExit("v3: policing visible-line loop not found")

POLICING.write_text(policing, encoding="utf-8")

# Seed the integrity fixture through the exact helper the validator now calls.
namespace = runpy.run_path(str(POLICING))
roadmap = Path("ROADMAP.md").read_text(encoding="utf-8")
rendered = namespace["_rendered_policing_workstream"](roadmap)
visible_lines = namespace["_normalised_visible_workstream_lines"](rendered)
fixture = hashlib.sha256("\n".join(visible_lines).encode("utf-8")).hexdigest()

policing = POLICING.read_text(encoding="utf-8")
pattern = re.compile(r'POLICING_WORKSTREAM_VISIBLE_SHA256 = "[0-9a-f]{64}"')
matches = pattern.findall(policing)
if len(matches) != 1:
    raise SystemExit(f"v3: expected one policing integrity fixture, found {len(matches)}")
policing = pattern.sub(
    f'POLICING_WORKSTREAM_VISIBLE_SHA256 = "{fixture}"',
    policing,
    count=1,
)
POLICING.write_text(policing, encoding="utf-8")

print("v3 corrections applied; policing fixture", fixture)
