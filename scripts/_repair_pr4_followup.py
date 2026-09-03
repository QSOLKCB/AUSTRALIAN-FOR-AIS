from __future__ import annotations

import hashlib
from pathlib import Path
import pprint
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(rf"(?ms)^def {re.escape(name)}\(.*?(?=^def |^@|\Z)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"{name}: expected one function, found {len(matches)}")
    match = matches[0]
    return text[:match.start()] + replacement.rstrip() + "\n\n" + text[match.end():]


# The first repair script has already produced the stricter parser at this point.
ns = runpy.run_path(str(REGISTRY))
corpus = CORPUS.read_text(encoding="utf-8")
sections = ns["_registered_sections"](corpus)
source_type_hashes = {
    entry: hashlib.sha256(
        ns["_scalar_value"](entry, section, ns["SOURCE_TYPE_FIELD"]).encode("utf-8")
    ).hexdigest()
    for entry, section in sections.items()
}

text = REGISTRY.read_text(encoding="utf-8")
if "SOURCE_TYPE_VALUE_HASHES =" not in text:
    literal = pprint.pformat(source_type_hashes, width=100, sort_dicts=True)
    text = text.replace(
        "\n\nGOVERNANCE_RATIONALE_HASHES =",
        f"\n\nSOURCE_TYPE_VALUE_HASHES = {literal}\n\nGOVERNANCE_RATIONALE_HASHES =",
        1,
    )

# `_markdown_views()` has already masked true code/fences/comments in the structural
# view. Therefore any nonblank structural line is rendered structure, even where a
# raw four-space indent is a paragraph/list continuation. Do not reclassify it as
# code a second time here.
text = text.replace(
    "(logical.lstrip(\" \\t\"), rendered_logical.lstrip(\" \\t\"), is_code or rendered_is_code)",
    "(logical.lstrip(\" \\t\"), rendered_logical.lstrip(\" \\t\"), False)",
    1,
)

text = replace_function(
    text,
    "_require_community_governance",
    r'''
def _require_community_governance(entry: str, section: str) -> str:
    field_count = _metadata_field_count(section, ("**Community-specific governance:**",))
    assert field_count == 1, f"{entry} must contain exactly one community-specific governance field"

    rendered, structure = _markdown_views(section)
    classification = GOVERNANCE_PATTERN.search(structure)
    assert classification, f"{entry} has an invalid community-specific governance classification or rationale"
    raw_rationale = rendered[classification.start("rationale"):classification.end("rationale")]
    rationale = _visible_inline_text(raw_rationale)
    assert rationale, f"{entry} has an invalid community-specific governance classification or rationale"

    expected_hash = GOVERNANCE_RATIONALE_HASHES.get(entry)
    if expected_hash is not None:
        actual_hash = hashlib.sha256(rationale.encode("utf-8")).hexdigest()
        assert actual_hash == expected_hash, (
            f"{entry} changed pinned community-governance rationale: "
            f"expected hash {expected_hash!r}, got {actual_hash!r}"
        )

    value = classification.group(1)
    if value == "required":
        safe_use = _scalar_value(entry, section, SAFE_FIELD)
        assert CONSULTATION_BOUNDARY in safe_use, (
            f"{entry} is missing its community-specific consultation boundary "
            "from the safe benchmark abstraction field"
        )
    return value
''',
)

text = replace_function(
    text,
    "_require_pinned_entry_contract",
    r'''
def _require_pinned_entry_contract(
    entry: str,
    *,
    classification: str,
    scalar_values: dict[str, str],
    destinations: tuple[str, ...],
) -> None:
    contract = ENTRY_CONTRACTS.get(entry)
    assert contract is not None, f"{entry} has no pinned source-governance contract"
    expected_classification = contract["governance"]
    assert classification == expected_classification, f"{entry} must remain classified as {expected_classification}"

    expected_destinations = set(contract[SOURCES_KEY])
    actual_destinations = set(destinations)
    assert actual_destinations == expected_destinations, (
        f"{entry} registered-source destinations changed: "
        f"expected {sorted(expected_destinations)!r}, got {sorted(actual_destinations)!r}"
    )

    for field in SCALAR_FIELDS:
        expected_clause = _visible_inline_text(str(contract[field]))
        actual_value = scalar_values[field]
        assert expected_clause in actual_value, (
            f"{entry} is missing a pinned {field} clause or changed its accepted value: "
            f"{expected_clause!r}"
        )
        if field == SOURCE_TYPE_FIELD:
            actual_hash = hashlib.sha256(actual_value.encode("utf-8")).hexdigest()
            expected_hash = SOURCE_TYPE_VALUE_HASHES[entry]
            assert actual_hash == expected_hash, (
                f"{entry} changed pinned {field}: expected hash "
                f"{expected_hash!r}, got {actual_hash!r}"
            )
        elif field in BOUNDARY_FIELDS:
            actual_hash = hashlib.sha256(actual_value.encode("utf-8")).hexdigest()
            expected_hash = BOUNDARY_VALUE_HASHES[entry][field]
            assert actual_hash == expected_hash, (
                f"{entry} changed pinned {field}: expected hash "
                f"{expected_hash!r}, got {actual_hash!r}"
            )
''',
)

REGISTRY.write_text(text, encoding="utf-8")

# Remove the final temporary patch helper. The first-stage script already removes
# itself and its workflow from the working tree before this helper runs.
Path(__file__).unlink()
