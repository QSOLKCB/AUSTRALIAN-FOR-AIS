"""Regression for Phase 2 annotation-guide pseudonym instructions."""

import pathlib


GUIDE = pathlib.Path(__file__).parent.parent / "docs" / "ANNOTATION-GUIDE.md"


def test_annotation_guide_uses_generated_read_only_pseudonym():
    guide = GUIDE.read_text(encoding="utf-8")

    assert "read-only pseudonymous annotator ID generated locally by the browser" in guide
    assert "Enter a pseudonymous annotator ID." not in guide
