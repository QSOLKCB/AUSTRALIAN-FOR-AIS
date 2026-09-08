from pathlib import Path
import hashlib
import runpy

ROOT = Path(__file__).resolve().parents[1]
POLICING = ROOT / "tests" / "test_policing_context_roadmap.py"
REGISTRY = ROOT / "tests" / "test_research_reference_registry.py"
REGRESSIONS = ROOT / "tests" / "test_pr4_current_review_regressions.py"
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


policing = POLICING.read_text(encoding="utf-8")
policing = replace_once(
    policing,
    '''        for key, value in attrs:\n            values.setdefault(key.lower(), value or "")\n        # Negative tabindex removes an otherwise valid provenance anchor from\n''',
    '''        for key, value in attrs:\n            values.setdefault(key.lower(), value or "")\n        # An ARIA-disabled provenance anchor can retain its canonical label and\n        # href while assistive technology exposes it as unavailable. Keep that\n        # interaction state inside the governed source-link contract.\n        if (\n            tag == "a"\n            and values.get("aria-disabled", "").strip().casefold() == "true"\n        ):\n            self.violations.add("accessibility-disabled")\n        # Negative tabindex removes an otherwise valid provenance anchor from\n''',
    "shared aria-disabled policy",
)
policing = replace_once(
    policing,
    '''        "accessibility-hidden": "aria-hidden accessibility suppression HTML",\n        "nested-anchor": "nested anchor HTML",\n''',
    '''        "accessibility-hidden": "aria-hidden accessibility suppression HTML",\n        "accessibility-disabled": "aria-disabled source-link suppression HTML",\n        "nested-anchor": "nested anchor HTML",\n''',
    "shared accessibility-disabled diagnostic",
)
POLICING.write_text(policing, encoding="utf-8")

registry = REGISTRY.read_text(encoding="utf-8")
registry = replace_once(
    registry,
    '''    "accessibility-hidden",\n    "keyboard-navigation",\n''',
    '''    "accessibility-hidden",\n    "accessibility-disabled",\n    "keyboard-navigation",\n''',
    "registry active accessibility-disabled kind",
)
registry = replace_once(
    registry,
    '''        if not (\n            bool(run["can_open"])\n            or bool(run["can_close"])\n            or int(run["open_consumed"])\n            or int(run["close_consumed"])\n        ):\n            continue\n        sentinel = (\n''',
    '''        # Any unconsumed delimiter character is reader-visible literal text,\n        # including a run surrounded by whitespace that can neither open nor\n        # close emphasis. Preserve it before generic delimiter stripping.\n        sentinel = (\n''',
    "registry whitespace-delimited emphasis preservation",
)
registry = replace_once(
    registry,
    '''        if tag == "img":\n            self.found.add("replacement")\n        if "shadowrootmode" in names or "shadowroot" in names:\n''',
    '''        if tag == "img":\n            self.found.add("replacement")\n        if tag == "hr":\n            self.found.add("thematic-break")\n        if "shadowrootmode" in names or "shadowroot" in names:\n''',
    "registry raw thematic break detection",
)
registry = replace_once(
    registry,
    '''    assert "accessibility-hidden" not in found, (\n        "aria-hidden accessibility suppression is not allowed in governed documents"\n    )\n    assert "keyboard-navigation" not in found, (\n''',
    '''    assert "accessibility-hidden" not in found, (\n        "aria-hidden accessibility suppression is not allowed in governed documents"\n    )\n    assert "accessibility-disabled" not in found, (\n        "aria-disabled source-link suppression is not allowed in governed documents"\n    )\n    assert "keyboard-navigation" not in found, (\n''',
    "registry accessibility-disabled diagnostic",
)
registry = replace_once(
    registry,
    '''    assert "executable-url" not in forbidden_html, (\n        f"{entry} contains an executable URL attribute; governed HTML must not "\n        "carry javascript:/vbscript: navigation"\n    )\n    assert "non-rendering-container" not in forbidden_html, (\n''',
    '''    assert "executable-url" not in forbidden_html, (\n        f"{entry} contains an executable URL attribute; governed HTML must not "\n        "carry javascript:/vbscript: navigation"\n    )\n    assert "thematic-break" not in forbidden_html, (\n        f"{entry} contains a raw HTML thematic break; governed entry receipts "\n        "must preserve the visual association between provenance and its boundary"\n    )\n    assert "non-rendering-container" not in forbidden_html, (\n''',
    "registry raw thematic break rejection",
)
REGISTRY.write_text(registry, encoding="utf-8")

# The delimiter correction changes the rendered normalization of existing
# snake_case-like identifiers because CommonMark renders those intraword
# underscores literally. Rebaseline only parser-sensitive fixtures against the
# unchanged canonical corpus; the guarded base SHA ensures no document bytes
# have moved under this migration.
ns = runpy.run_path(str(REGISTRY))
corpus = CORPUS.read_text(encoding="utf-8")
sections = ns["_registered_sections"](corpus)
fixture_source = REGISTRY.read_text(encoding="utf-8")
changed_fixtures: list[tuple[str, str, str]] = []
for entry, section in sections.items():
    research_value, project_value = ns["_require_mapping_block"](entry, section)
    complete_value = ns["_normalise_complete_entry_integrity"](section)
    values = (
        ("RESEARCH_MAPPING_VALUE_HASHES", research_value),
        ("PROJECT_MAPPING_VALUE_HASHES", project_value),
        ("ENTRY_RENDERED_VALUE_HASHES", complete_value),
    )
    for mapping_name, value in values:
        old_hash = ns[mapping_name][entry]
        new_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
        if old_hash == new_hash:
            continue
        count = fixture_source.count(old_hash)
        if count != 1:
            raise SystemExit(
                f"{mapping_name} {entry}: expected unique old hash {old_hash}, found {count}"
            )
        fixture_source = fixture_source.replace(old_hash, new_hash, 1)
        changed_fixtures.append((mapping_name, entry, new_hash))
REGISTRY.write_text(fixture_source, encoding="utf-8")
for mapping_name, entry, new_hash in changed_fixtures:
    print(f"rebaselined {mapping_name} {entry}: {new_hash}")

regressions = REGRESSIONS.read_text(encoding="utf-8")
marker = "\n\n# Human receipt: autolink/implied-end/type-6 repair passed 12 exact and 912 full-suite tests before self-cleanup.\n"
addition = r'''

def test_registry_whitespace_delimited_emphasis_marker_remains_visible() -> None:
    sample = "registered * as scholarship"
    assert REGISTRY["_visible_inline_text"](sample) == sample

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    mutated = corpus.replace(live, "The article is a * scholarly research reference.", 1)
    assert mutated != corpus
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_aria_disabled_true_is_rejected_for_registered_source_anchor() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    disabled = f'**Registered source:** <a href="{url}" aria-disabled="true">{url}</a>'
    assert live in corpus
    mutated = corpus.replace(live, disabled, 1)
    with pytest.raises(AssertionError, match="aria-disabled source-link suppression"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_raw_html_thematic_break_cannot_split_pinned_rights_clause() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    split = "The article is a scholarly <hr> research reference."
    assert live in corpus
    mutated = corpus.replace(live, split, 1)
    with pytest.raises(AssertionError, match="raw HTML thematic break"):
        REGISTRY["_validate_registry_corpus"](mutated)
'''
if marker not in regressions:
    raise SystemExit("regression receipt marker not found")
regressions = regressions.replace(marker, addition + marker, 1)
REGRESSIONS.write_text(regressions, encoding="utf-8")
