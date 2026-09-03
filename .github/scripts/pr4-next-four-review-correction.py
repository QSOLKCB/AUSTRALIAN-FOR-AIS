from pathlib import Path

path = Path("tests/test_policing_context_roadmap.py")
text = path.read_text(encoding="utf-8")

old_heading = 'WORKSTREAM_END_HEADING = "## Phase 3"'
new_heading = (
    'WORKSTREAM_END_HEADING = '
    '"## Phase 3 — Multi-Annotator Culturally Contextualised Dataset"'
)
if new_heading not in text:
    if text.count(old_heading) != 1:
        raise SystemExit(
            f"policing end heading correction: expected one anchor, found {text.count(old_heading)}"
        )
    text = text.replace(old_heading, new_heading, 1)

old_error = 'raise AssertionError("rendered policing workstream is missing") from exc'
new_error = (
    'raise AssertionError('
    '"rendered policing workstream is missing; missing policing-workstream safeguard"'
    ') from exc'
)
if new_error not in text:
    if text.count(old_error) != 1:
        raise SystemExit(
            f"policing hidden-workstream error correction: expected one anchor, found {text.count(old_error)}"
        )
    text = text.replace(old_error, new_error, 1)

path.write_text(text, encoding="utf-8")
print("Corrected PR4 policing rendered-heading boundary.")
