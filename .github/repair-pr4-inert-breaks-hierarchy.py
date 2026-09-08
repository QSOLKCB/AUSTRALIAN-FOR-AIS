from __future__ import annotations

from pathlib import Path
import hashlib
import runpy

ROOT = Path(__file__).resolve().parents[1]
POLICING_PATH = ROOT / "tests" / "test_policing_context_roadmap.py"
REGRESSIONS_PATH = ROOT / "tests" / "test_pr4_current_review_regressions.py"
ROADMAP_PATH = ROOT / "ROADMAP.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


policing = POLICING_PATH.read_text(encoding="utf-8")

policing = replace_once(
    policing,
    'POLICING_WORKSTREAM_VISIBLE_SHA256 = "d43f7d255da2792106d69048e617d96d9f8933204bc3dd4623b2482e5a4600e8"\n',
    'POLICING_WORKSTREAM_VISIBLE_SHA256 = "d43f7d255da2792106d69048e617d96d9f8933204bc3dd4623b2482e5a4600e8"\n'
    'POLICING_WORKSTREAM_STRUCTURE_SHA256 = "__PR4_STRUCTURE_SHA256__"\n',
    "structure hash constant",
)

policing = replace_once(
    policing,
    '        if tag in {\n'
    '            "iframe", "object", "embed", "audio", "video", "meter", "progress",\n'
    '            "marquee",\n'
    '        }:\n'
    '            self.violations.add("replacement-content")\n',
    '        if tag in {\n'
    '            "iframe", "object", "embed", "audio", "video", "meter", "progress",\n'
    '            "marquee",\n'
    '        }:\n'
    '            self.violations.add("replacement-content")\n'
    '        # Browser-rendered line/thematic breaks can visually separate a\n'
    '        # mandatory governance phrase while character-data normalization\n'
    '        # recreates the canonical text. Keep those boundaries inside the\n'
    '        # shared governed-surface contract.\n'
    '        if tag in {"br", "hr"}:\n'
    '            self.violations.add("rendered-break")\n',
    "rendered break detection",
)

policing = replace_once(
    policing,
    '        if "aria-hidden" in attribute_names:\n'
    '            self.violations.add("accessibility-hidden")\n',
    '        if "aria-hidden" in attribute_names:\n'
    '            self.violations.add("accessibility-hidden")\n'
    '        # Native inert suppresses descendant interaction and accessibility\n'
    '        # exposure even though the character data can remain visually\n'
    '        # present. Reuse the accessibility-suppression policy across every\n'
    '        # governed surface, not only source-link/citation special cases.\n'
    '        if "inert" in attribute_names:\n'
    '            self.violations.add("accessibility-hidden")\n',
    "inert accessibility suppression",
)

policing = replace_once(
    policing,
    '        "replacement-content": "replacement-content HTML",\n'
    '        "preformatted-content": "preformatted content HTML",\n',
    '        "replacement-content": "replacement-content HTML",\n'
    '        "rendered-break": "rendered break HTML",\n'
    '        "preformatted-content": "preformatted content HTML",\n',
    "rendered break rejection table",
)

old_normalizer = '''def _normalised_visible_workstream_lines(rendered: str) -> list[str]:
    """Return the canonical browser-visible line sequence used by Workstream I integrity."""
    visible_lines: list[str] = []
    for raw_line in rendered.splitlines():
        line = _visible_text(raw_line).strip()
        line = re.sub(r"^(?:[-+*]|\\d{1,9}[.)])\\s+", "", line)
        if line:
            visible_lines.append(line)
    return visible_lines
'''
new_normalizer = '''def _workstream_container_signature(raw_line: str) -> str:
    """Encode CommonMark quote/list ownership for one visible Workstream I line."""
    _, is_code, containers = _parse_fence_container_prefixes(raw_line)
    if is_code:
        return "code"
    if not containers:
        return "root"
    return "/".join(f"{kind}:{amount}" for kind, amount in containers)


def _normalised_visible_workstream_records(rendered: str) -> list[tuple[str, str]]:
    """Return structural signatures plus canonical browser-visible Workstream I text."""
    records: list[tuple[str, str]] = []
    for raw_line in rendered.splitlines():
        signature = _workstream_container_signature(raw_line)
        line = _visible_text(raw_line).strip()
        line = re.sub(r"^(?:[-+*]|\\d{1,9}[.)])\\s+", "", line)
        if line:
            records.append((signature, line))
    return records


def _normalised_visible_workstream_lines(rendered: str) -> list[str]:
    """Return canonical browser-visible text lines for clause-level checks."""
    return [line for _, line in _normalised_visible_workstream_records(rendered)]
'''
policing = replace_once(policing, old_normalizer, new_normalizer, "workstream structural normalizer")

policing = replace_once(
    policing,
    '    workstream = _visible_text(rendered)\n'
    '    visible_lines = _normalised_visible_workstream_lines(rendered)\n',
    '    workstream = _visible_text(rendered)\n'
    '    visible_records = _normalised_visible_workstream_records(rendered)\n'
    '    visible_lines = [line for _, line in visible_records]\n',
    "visible workstream records",
)

old_integrity = '''    integrity_value = "\\n".join(visible_lines)
    integrity_hash = hashlib.sha256(integrity_value.encode("utf-8")).hexdigest()
    assert integrity_hash == POLICING_WORKSTREAM_VISIBLE_SHA256, (
        "browser-visible policing workstream changed: expected hash "
        f"{POLICING_WORKSTREAM_VISIBLE_SHA256!r}, got {integrity_hash!r}"
    )
'''
new_integrity = '''    integrity_value = "\\n".join(visible_lines)
    integrity_hash = hashlib.sha256(integrity_value.encode("utf-8")).hexdigest()
    assert integrity_hash == POLICING_WORKSTREAM_VISIBLE_SHA256, (
        "browser-visible policing workstream changed: expected hash "
        f"{POLICING_WORKSTREAM_VISIBLE_SHA256!r}, got {integrity_hash!r}"
    )

    structural_integrity_value = "\\n".join(
        f"{signature}\\t{line}" for signature, line in visible_records
    )
    structural_integrity_hash = hashlib.sha256(
        structural_integrity_value.encode("utf-8")
    ).hexdigest()
    assert structural_integrity_hash == POLICING_WORKSTREAM_STRUCTURE_SHA256, (
        "browser-visible policing workstream container hierarchy changed: expected hash "
        f"{POLICING_WORKSTREAM_STRUCTURE_SHA256!r}, got {structural_integrity_hash!r}"
    )
'''
policing = replace_once(policing, old_integrity, new_integrity, "structural integrity receipt")

POLICING_PATH.write_text(policing, encoding="utf-8")

# Compute the new structural fixture from the unchanged canonical ROADMAP after
# the parser semantics above are installed. This does not rebaseline prose.
namespace = runpy.run_path(str(POLICING_PATH))
roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
rendered = namespace["_rendered_policing_workstream"](roadmap)
records = namespace["_normalised_visible_workstream_records"](rendered)
structure_value = "\n".join(f"{signature}\t{line}" for signature, line in records)
structure_hash = hashlib.sha256(structure_value.encode("utf-8")).hexdigest()
policing = POLICING_PATH.read_text(encoding="utf-8")
policing = replace_once(
    policing,
    'POLICING_WORKSTREAM_STRUCTURE_SHA256 = "__PR4_STRUCTURE_SHA256__"',
    f'POLICING_WORKSTREAM_STRUCTURE_SHA256 = "{structure_hash}"',
    "computed structural fixture",
)
POLICING_PATH.write_text(policing, encoding="utf-8")
print(f"POLICING_WORKSTREAM_STRUCTURE_SHA256={structure_hash}")

regressions = REGRESSIONS_PATH.read_text(encoding="utf-8")
marker = "# PR4 inert/break/list-hierarchy review regressions\n"
if marker in regressions:
    raise RuntimeError("latest regression block already present")
regressions += '''\n\n# PR4 inert/break/list-hierarchy review regressions\n\ndef test_inert_is_rejected_across_shared_and_registry_governed_surfaces() -> None:\n    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")\n    phrase = "source-gated research proposal"\n    inert_phrase = f"<span inert>{phrase}</span>"\n    mutated_roadmap = roadmap.replace(phrase, inert_phrase, 1)\n    assert mutated_roadmap != roadmap\n    assert "accessibility-hidden" in POLICING["_governed_surface_html_violations"](mutated_roadmap)\n    with pytest.raises(AssertionError):\n        POLICING["_validate_policing_workstream"](mutated_roadmap)\n\n    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")\n    live = "The article is a scholarly research reference."\n    inert_rights = f"<span inert>{live}</span>"\n    mutated_corpus = corpus.replace(live, inert_rights, 1)\n    assert mutated_corpus != corpus\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](mutated_corpus)\n\n\n@pytest.mark.parametrize("tag", ("br", "hr"))\ndef test_rendered_breaks_cannot_split_shared_methodology_safeguards(tag: str) -> None:\n    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")\n\n    workstream_i_phrase = "source-gated research proposal"\n    mutated_i = roadmap.replace(\n        workstream_i_phrase,\n        f"source-gated <{tag}> research proposal",\n        1,\n    )\n    assert mutated_i != roadmap\n    assert "rendered-break" in POLICING["_governed_surface_html_violations"](mutated_i)\n    with pytest.raises(AssertionError):\n        POLICING["_validate_policing_workstream"](mutated_i)\n\n    workstream_h_phrase = (\n        "nationality and first-language identity must not define the comparison cohorts"\n    )\n    mutated_h = roadmap.replace(\n        workstream_h_phrase,\n        f"nationality and first-language identity must <{tag}> not define the comparison cohorts",\n        1,\n    )\n    assert mutated_h != roadmap\n    assert "rendered-break" in POLICING["_governed_surface_html_violations"](mutated_h)\n    with pytest.raises(AssertionError):\n        WORKSTREAM_H["_assert_workstream_h_integrity"](mutated_h)\n\n\ndef test_policing_workstream_receipt_preserves_list_hierarchy() -> None:\n    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")\n    review_line = (\n        "- before publishing any family involving coercion, consent, search, detention, "\n        "questioning, force, emergency powers, or legal rights, verify the governing "\n        "sources are current for the recorded jurisdiction and date and obtain appropriate "\n        "review from relevant Australian and United States legal, policing, civil-liberties, "\n        "and community expertise;"\n    )\n    assert review_line in roadmap\n    mutated = roadmap.replace(review_line, "  " + review_line, 1)\n\n    canonical_rendered = POLICING["_rendered_policing_workstream"](roadmap)\n    mutated_rendered = POLICING["_rendered_policing_workstream"](mutated)\n    canonical_records = POLICING["_normalised_visible_workstream_records"](canonical_rendered)\n    mutated_records = POLICING["_normalised_visible_workstream_records"](mutated_rendered)\n    review_text = review_line[2:]\n    canonical_signature = next(signature for signature, line in canonical_records if line == review_text)\n    mutated_signature = next(signature for signature, line in mutated_records if line == review_text)\n    assert canonical_signature != mutated_signature\n\n    with pytest.raises(AssertionError, match="container hierarchy changed"):\n        POLICING["_validate_policing_workstream"](mutated)\n'''
REGRESSIONS_PATH.write_text(regressions, encoding="utf-8")
