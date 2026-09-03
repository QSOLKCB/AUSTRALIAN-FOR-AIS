from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one correction anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_exact(
    REGISTRY,
    '''    assert destination is not None, (
        f"registered-source rendered link must be usable HTTPS: {candidate!r}"
    )
''',
    '''    assert destination is not None, (
        f"registered-source rendered link has no usable HTTPS destination: {candidate!r}"
    )
''',
)

replace_exact(
    REGISTRY,
    '''    rights_value = _scalar_value(section, RIGHTS_FIELD)
''',
    '''    rights_value = _scalar_value(heading, section, RIGHTS_FIELD)
''',
)

print("Applied hydra repair harness compatibility corrections.")
