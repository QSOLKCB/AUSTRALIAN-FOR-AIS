from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICING_PATH = ROOT / "tests" / "test_policing_context_roadmap.py"
REGISTRY_PATH = ROOT / "tests" / "test_research_reference_registry.py"
REGRESSIONS_PATH = ROOT / "tests" / "test_pr4_current_review_regressions.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


policing = POLICING_PATH.read_text(encoding="utf-8")
policing = replace_once(
    policing,
    '        if "inert" in attribute_names:\n'
    '            self.violations.add("accessibility-hidden")\n',
    '        if "inert" in attribute_names:\n'
    '            self.violations.add("accessibility-inert")\n',
    "separate native inert violation kind",
)
policing = replace_once(
    policing,
    '        "accessibility-hidden": "aria-hidden accessibility suppression HTML",\n',
    '        "accessibility-hidden": "aria-hidden accessibility suppression HTML",\n'
    '        "accessibility-inert": "native inert accessibility suppression HTML",\n',
    "shared inert rejection description",
)
POLICING_PATH.write_text(policing, encoding="utf-8")

regressions = REGRESSIONS_PATH.read_text(encoding="utf-8")
regressions = replace_once(
    regressions,
    '    assert "accessibility-hidden" in POLICING["_governed_surface_html_violations"](mutated_roadmap)\n',
    '    assert "accessibility-inert" in POLICING["_governed_surface_html_violations"](mutated_roadmap)\n',
    "exact inert violation receipt",
)
REGRESSIONS_PATH.write_text(regressions, encoding="utf-8")

registry = REGISTRY_PATH.read_text(encoding="utf-8")
old_tail = '''    for entry, section in sections.items():
        _validate_registered_entry(
            entry,
            section,
            reference_scope=corpus,
        )
'''
new_tail = '''    for entry, section in sections.items():
        _validate_registered_entry(
            entry,
            section,
            reference_scope=corpus,
        )

    # Keep the established source-link inert diagnostics above: an inert source
    # fails while its registered-source field is being validated. After every
    # entry has had that more specific check, reject native inert anywhere else
    # in the governed corpus so rights/provenance and global governance clauses
    # cannot disappear from the accessibility tree while retaining their text
    # receipts.
    assert "accessibility-inert" not in _SHARED_HTML_PREFLIGHT(corpus), (
        "native inert accessibility suppression is not allowed in governed documents"
    )
'''
registry = replace_once(registry, old_tail, new_tail, "deferred corpus-wide inert gate")
REGISTRY_PATH.write_text(registry, encoding="utf-8")
