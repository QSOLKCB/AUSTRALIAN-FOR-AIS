"""Receipt regressions for the policing-context governance contract."""

from __future__ import annotations

import ast
from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
POLICING_TEST = Path(__file__).parent / "test_policing_context_roadmap.py"
ROADMAP = ROOT / "ROADMAP.md"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"

EXPECTED_POLICING_INVARIANTS = {
    "US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE",
    "POLICE TERMINOLOGY != CROSS-JURISDICTION EQUIVALENCE",
    "CASUAL ADDRESS != FRIENDSHIP OR CONSENT",
    "CALM TONE != ABSENCE OF COERCIVE AUTHORITY",
    "POLITE WORDING != VOLUNTARY CHOICE",
    "FICTIONAL POLICE TROPE != OPERATIONAL POLICY",
    "ONE AGENCY != A NATIONAL POLICING SYSTEM",
    "ONE ENCOUNTER != SYSTEM-WIDE GROUND TRUTH",
    "JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER",
    "LEGAL INFORMATION != LEGAL ADVICE",
}

MANDATORY_ITEM_METADATA_SENTENCE = (
    "Every implemented item must record, at minimum, the relevant country, "
    "jurisdiction, agency or institutional role, encounter type, source date or "
    "version, registered source identifiers or links supporting any legal or "
    "procedural condition supplied to the model, and claim type."
)

CANONICAL_METADATA_FIELDS = (
    "country",
    "jurisdiction",
    "agency or institutional role",
    "encounter type",
    "source date or version",
    "registered source identifiers or links",
    "claim type",
)

POLICING_METHODOLOGY_HEADING = (
    "## Australian and United States Policing-Context Experiment Design"
)
POLICING_METADATA_INTRO = (
    "Every implemented policing-context item must record, at minimum:"
)
HIGH_STAKES_REVIEW_SENTENCE = (
    "before publishing any family involving coercion, consent, search, detention, "
    "questioning, force, emergency powers, or legal rights, verify the governing sources "
    "are current for the recorded jurisdiction and date and obtain appropriate review from "
    "relevant Australian and United States legal, policing, civil-liberties, and community expertise;"
)
CANONICAL_HIGH_STAKES_REVIEW_SENTENCE = (
    "Before publication of a family involving coercion, consent, search, detention, questioning, "
    "force, emergency powers, or legal rights, the project must verify the governing sources are "
    "current for the recorded jurisdiction and date and obtain appropriate review from relevant "
    "Australian and United States legal, policing, civil-liberties, and community expertise."
)


def _string_constants_in_tuple(name: str) -> tuple[str, ...]:
    tree = ast.parse(POLICING_TEST.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        assert isinstance(node.value, ast.Tuple)
        return tuple(
            item.value
            for item in node.value.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
    raise AssertionError(f"missing policing contract tuple: {name}")


def _policing_methodology_section(methodology: str) -> str:
    assert POLICING_METHODOLOGY_HEADING in methodology
    start = methodology.index(POLICING_METHODOLOGY_HEADING)
    end = methodology.index("\n---\n", start)
    return methodology[start:end]


def _visible_policing_methodology(methodology: str) -> str:
    policing_namespace = runpy.run_path(str(POLICING_TEST))
    visible_text = policing_namespace["_visible_text"]
    return visible_text(_policing_methodology_section(methodology))


def _assert_canonical_policing_metadata(methodology: str) -> None:
    rendered = _visible_policing_methodology(methodology)
    assert POLICING_METADATA_INTRO in rendered
    for field in CANONICAL_METADATA_FIELDS:
        assert field in rendered


def _assert_canonical_high_stakes_gate(methodology: str) -> None:
    rendered = _visible_policing_methodology(methodology)
    assert CANONICAL_HIGH_STAKES_REVIEW_SENTENCE in rendered
    assert (
        "obtain appropriate review from relevant Australian and United States legal, policing, "
        "civil-liberties, and community expertise"
    ) in rendered


def test_all_policing_invariants_are_required_and_affirmative():
    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))
    affirmative = set(_string_constants_in_tuple("AFFIRMATIVE_LINE_PREFIX_CLAUSES"))

    assert EXPECTED_POLICING_INVARIANTS <= required
    assert EXPECTED_POLICING_INVARIANTS <= affirmative


def test_roadmap_policing_metadata_matches_canonical_minimum():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))
    affirmative = set(_string_constants_in_tuple("AFFIRMATIVE_LINE_PREFIX_CLAUSES"))

    assert "Every implemented item should record" not in roadmap
    assert MANDATORY_ITEM_METADATA_SENTENCE in roadmap
    assert MANDATORY_ITEM_METADATA_SENTENCE in required
    assert MANDATORY_ITEM_METADATA_SENTENCE in affirmative
    _assert_canonical_policing_metadata(methodology)


def test_policing_metadata_cannot_be_satisfied_outside_canonical_section():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    section = _policing_methodology_section(methodology)
    stripped_lines = [
        line
        for line in section.splitlines()
        if not any(f"**{field}**" in line for field in CANONICAL_METADATA_FIELDS)
    ]
    stripped_section = "\n".join(stripped_lines)
    external_decoys = "\n".join(
        f"Unrelated methodology prose mentioning **{field}**."
        for field in CANONICAL_METADATA_FIELDS
    )
    mutated = methodology.replace(section, stripped_section, 1) + "\n" + external_decoys

    with pytest.raises(AssertionError):
        _assert_canonical_policing_metadata(mutated)


def test_high_stakes_family_review_gate_matches_canonical_methodology():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    required = set(_string_constants_in_tuple("REQUIRED_CLAUSES"))
    affirmative = set(_string_constants_in_tuple("AFFIRMATIVE_LINE_PREFIX_CLAUSES"))

    assert "before publishing high-stakes conclusions" not in roadmap
    assert HIGH_STAKES_REVIEW_SENTENCE in roadmap
    assert HIGH_STAKES_REVIEW_SENTENCE in required
    assert HIGH_STAKES_REVIEW_SENTENCE in affirmative
    _assert_canonical_high_stakes_gate(methodology)


def test_policing_metadata_fields_must_be_browser_visible():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    section = _policing_methodology_section(methodology)
    hidden_lines: list[str] = []
    for line in section.splitlines():
        if any(f"**{field}**" in line for field in CANONICAL_METADATA_FIELDS):
            hidden_lines.append(f"<!-- {line} -->")
        else:
            hidden_lines.append(line)
    mutated_section = "\n".join(hidden_lines)
    mutated = methodology.replace(section, mutated_section, 1)

    with pytest.raises(AssertionError):
        _assert_canonical_policing_metadata(mutated)


def test_high_stakes_methodology_gate_must_be_browser_visible():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    assert CANONICAL_HIGH_STAKES_REVIEW_SENTENCE in methodology
    mutated = methodology.replace(
        CANONICAL_HIGH_STAKES_REVIEW_SENTENCE,
        f"<!-- {CANONICAL_HIGH_STAKES_REVIEW_SENTENCE} -->",
        1,
    )
    with pytest.raises(AssertionError):
        _assert_canonical_high_stakes_gate(mutated)
