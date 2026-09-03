"""Receipt regressions for the policing-context governance contract."""

from __future__ import annotations

import ast
from pathlib import Path


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
    for field in CANONICAL_METADATA_FIELDS:
        assert f"**{field}**" in methodology
