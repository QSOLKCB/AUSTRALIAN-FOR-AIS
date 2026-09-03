"""Receipt regression for the complete policing-context invariant gate."""

from __future__ import annotations

import ast
from pathlib import Path


POLICING_TEST = Path(__file__).parent / "test_policing_context_roadmap.py"

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


def _literal_tuple(name: str) -> tuple[str, ...]:
    tree = ast.parse(POLICING_TEST.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        assert isinstance(value, tuple)
        assert all(isinstance(item, str) for item in value)
        return value
    raise AssertionError(f"missing policing contract tuple: {name}")


def test_all_policing_invariants_are_required_and_affirmative():
    required = set(_literal_tuple("REQUIRED_CLAUSES"))
    affirmative = set(_literal_tuple("AFFIRMATIVE_LINE_PREFIX_CLAUSES"))

    assert EXPECTED_POLICING_INVARIANTS <= required
    assert EXPECTED_POLICING_INVARIANTS <= affirmative
