from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one correction anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


workstream_h = ROOT / "tests" / "test_workstream_h_methodology.py"
receipt = ROOT / "tests" / "test_policing_contract_receipt.py"

replace_exact(
    workstream_h,
    '''        + WORKSTREAM_H_HEADING
        + roadmap[end:]
''',
    '''        + WORKSTREAM_H_HEADING
        + "\\n\\n"
        + roadmap[end:]
''',
)

replace_exact(
    receipt,
    '''def test_high_stakes_family_review_gate_matches_canonical_methodology():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    methodology = _policing_methodology_section(
        METHODOLOGY.read_text(encoding="utf-8")
    )
    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))
''',
    '''def test_high_stakes_family_review_gate_matches_canonical_methodology():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))
''',
)

print("Applied guard-harness corrections.")
