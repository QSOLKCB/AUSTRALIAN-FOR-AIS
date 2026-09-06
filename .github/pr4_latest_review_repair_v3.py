from __future__ import annotations

from pathlib import Path
import runpy


REGISTRY = Path("tests/test_research_reference_registry.py")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one match, found {count}"
    return text.replace(old, new, 1)


def main() -> None:
    # Apply the guarded semantic repair first.
    runpy.run_path(".github/pr4_latest_review_repair_v2.py", run_name="__main__")

    text = REGISTRY.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '''        + "\\n<div hidden>\\n"
        + corpus[start:end]
        + "\\n</div>\\n"
        + corpus[end:]
''',
        '''        + "\\n<div hidden>\\n\\n"
        + corpus[start:end]
        + "\\n</div>\\n\\n"
        + corpus[end:]
''',
        label="hidden div wrapper fixture",
    )

    text = replace_once(
        text,
        '''        + "\\n<details>\\n<summary>Governed references</summary>\\n"
        + corpus[start:end]
        + "\\n</details>\\n"
        + corpus[end:]
''',
        '''        + "\\n<details>\\n<summary>Governed references</summary>\\n\\n"
        + corpus[start:end]
        + "\\n</details>\\n\\n"
        + corpus[end:]
''',
        label="closed details wrapper fixture",
    )

    text = replace_once(
        text,
        '''        + "\\n<details open>\\n<summary>Governed references</summary>\\n"
        + corpus[start:end]
        + "\\n</details>\\n"
        + corpus[end:]
''',
        '''        + "\\n<details open>\\n<summary>Governed references</summary>\\n\\n"
        + corpus[start:end]
        + "\\n</details>\\n\\n"
        + corpus[end:]
''',
        label="open details wrapper fixture",
    )

    text = replace_once(
        text,
        '    mutated = corpus.replace(batch, f"<dialog>\\n{batch}\\n</dialog>\\n", 1)\n',
        '    mutated = corpus.replace(batch, f"<dialog>\\n\\n{batch}\\n\\n</dialog>\\n\\n", 1)\n',
        label="closed dialog wrapper fixture",
    )

    text = replace_once(
        text,
        '    mutated = corpus.replace(batch, f"<dialog open>\\n{batch}\\n</dialog>\\n", 1)\n',
        '    mutated = corpus.replace(batch, f"<dialog open>\\n\\n{batch}\\n\\n</dialog>\\n\\n", 1)\n',
        label="open dialog wrapper fixture",
    )

    text = replace_once(
        text,
        '''        f'<div style="display:/**/none">\\n{batch}\\n</div>\\n',
''',
        '''        f'<div style="display:/**/none">\\n\\n{batch}\\n\\n</div>\\n\\n',
''',
        label="CSS-hidden div wrapper fixture",
    )

    REGISTRY.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
