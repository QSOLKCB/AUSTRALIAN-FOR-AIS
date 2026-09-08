from __future__ import annotations

import argparse
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
POLICING_PATH = ROOT / "tests" / "test_policing_context_roadmap.py"
REGISTRY_PATH = ROOT / "tests" / "test_research_reference_registry.py"
REGRESSION_PATH = ROOT / "tests" / "test_pr4_current_review_regressions.py"
CORPUS_PATH = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one replacement in {path}: found {count}\nOLD={old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _load() -> tuple[dict[str, object], dict[str, object]]:
    policing = runpy.run_path(str(POLICING_PATH))
    registry = runpy.run_path(str(REGISTRY_PATH))
    return policing, registry


def reproduce() -> None:
    policing, registry = _load()
    corpus = CORPUS_PATH.read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    if live not in corpus:
        raise SystemExit("canonical registry sentence missing")

    # 1. Raw heading semantics currently disappear into character-data integrity.
    headed = corpus.replace(live, f"<h1>{live}</h1>", 1)
    registry["_validate_registry_corpus"](headed)

    # 2. NBSP currently collapses back to ordinary spaces via str.split().
    nbsp = corpus.replace(live, live.replace(" ", "&nbsp;"), 1)
    registry["_validate_registry_corpus"](nbsp)

    # 3. Microdata/body metadata currently remains outside the sealed text value.
    metadata = corpus.replace(
        live,
        f'<span itemscope><meta itemprop="license" content="CC0">{live}</span>',
        1,
    )
    registry["_validate_registry_corpus"](metadata)

    # Also demonstrate the equivalent ARIA heading form is presently accepted.
    role_heading = corpus.replace(live, f'<span role="heading">{live}</span>', 1)
    registry["_validate_registry_corpus"](role_heading)

    print("reproduced=raw-heading,nbsp,machine-metadata,role-heading")


def apply() -> None:
    _replace_once(
        POLICING_PATH,
        '        if tag in {"q", "blockquote"}:\n            self.violations.add("generated-quotation")\n',
        '        if tag in {"q", "blockquote"}:\n            self.violations.add("generated-quotation")\n'
        '        # Heading elements reframe governed prose structurally even when\n'
        '        # their character data is unchanged. Keep that semantic boundary\n'
        '        # inside the governed receipt rather than flattening it to text.\n'
        '        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:\n'
        '            self.violations.add("semantic-heading")\n',
    )

    _replace_once(
        POLICING_PATH,
        '        attribute_names = {key.lower() for key, _ in attrs}\n'
        '        # `hidden=until-found` is conditionally revealed by find-in-page or\n',
        '        attribute_names = {key.lower() for key, _ in attrs}\n'
        '        # ARIA can also manufacture heading semantics without using an h1-h6\n'
        '        # element. Reject that equivalent reframing on every governed surface.\n'
        '        if any(\n'
        '            key.lower() == "role"\n'
        '            and "heading" in {(value or "").strip().casefold().split()}\n'
        '            for key, value in attrs\n'
        '        ):\n'
        '            self.violations.add("semantic-heading")\n'
        '        # Microdata/RDFa and body metadata can publish machine-readable\n'
        '        # provenance or licence semantics that are absent from the sealed\n'
        '        # human-readable text. Fail closed rather than maintaining a second\n'
        '        # semantic contract for indexers and assistive consumers.\n'
        '        machine_metadata_attributes = {\n'
        '            "itemscope", "itemprop", "itemtype", "itemid", "itemref",\n'
        '            "about", "content", "datatype", "inlist", "prefix",\n'
        '            "property", "rel", "resource", "rev", "typeof", "vocab",\n'
        '        }\n'
        '        if tag == "meta" or machine_metadata_attributes.intersection(attribute_names):\n'
        '            self.violations.add("machine-metadata")\n'
        '        # `hidden=until-found` is conditionally revealed by find-in-page or\n',
    )

    # Fix a small set-construction typo in the generated role check above while keeping
    # the patch anchored to the exact reviewed text.
    _replace_once(
        POLICING_PATH,
        '            and "heading" in {(value or "").strip().casefold().split()}\n',
        '            and "heading" in (value or "").strip().casefold().split()\n',
    )

    _replace_once(
        POLICING_PATH,
        '        "semantic-role": "semantic role override HTML",\n'
        '        "raw-svg": "raw SVG HTML",\n',
        '        "semantic-role": "semantic role override HTML",\n'
        '        "semantic-heading": "raw/ARIA heading semantics HTML",\n'
        '        "machine-metadata": "machine-readable metadata HTML",\n'
        '        "raw-svg": "raw SVG HTML",\n',
    )

    _replace_once(
        REGISTRY_PATH,
        '    "semantic-role",\n'
        '    "preformatted-content",\n',
        '    "semantic-role",\n'
        '    "semantic-heading",\n'
        '    "machine-metadata",\n'
        '    "preformatted-content",\n',
    )

    _replace_once(
        REGISTRY_PATH,
        '    visible = visible.replace(RAW_HTML_LITERAL_ASTERISK, "*")\n'
        '    return " ".join(visible.split())\n',
        '    visible = visible.replace(RAW_HTML_LITERAL_ASTERISK, "*")\n'
        '    # HTML collapses only ASCII space, tab, LF, FF, and CR in ordinary\n'
        '    # flow. Preserve NBSP and every other Unicode separator so layout-\n'
        '    # significant/non-wrapping spacing changes the sealed receipt.\n'
        '    return re.sub(r"[ \\t\\n\\f\\r]+", " ", visible).strip(" ")\n',
    )

    _replace_once(
        REGISTRY_PATH,
        '    assert "semantic-role" not in found, (\n'
        '        "semantic role overrides on governed source anchors are not allowed in governed documents"\n'
        '    )\n'
        '    assert "preformatted-content" not in found, (\n',
        '    assert "semantic-role" not in found, (\n'
        '        "semantic role overrides on governed source anchors are not allowed in governed documents"\n'
        '    )\n'
        '    assert "semantic-heading" not in found, (\n'
        '        "raw or ARIA heading semantics are not allowed in governed documents"\n'
        '    )\n'
        '    assert "machine-metadata" not in found, (\n'
        '        "machine-readable Microdata/RDFa/body metadata is not allowed in governed documents"\n'
        '    )\n'
        '    assert "preformatted-content" not in found, (\n',
    )

    addition = r'''

# PR4 raw-heading / non-collapsible-spacing / machine-metadata regressions

@pytest.mark.parametrize(
    "wrapper",
    (
        "<h1>{}</h1>",
        "<h6>{}</h6>",
        '<span role="heading" aria-level="2">{}</span>',
    ),
)
def test_raw_or_aria_heading_semantics_cannot_reframe_governed_registry_text(
    wrapper: str,
) -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    assert live in corpus
    mutated = corpus.replace(live, wrapper.format(live), 1)
    assert "semantic-heading" in POLICING["_governed_surface_html_violations"](mutated)
    with pytest.raises(AssertionError, match="heading semantics"):
        REGISTRY["_validate_registry_corpus"](mutated)


@pytest.mark.parametrize("separator", ("\u00a0", "\u2007", "\u202f"))
def test_noncollapsible_unicode_separators_remain_in_registry_integrity_text(
    separator: str,
) -> None:
    sample = f"The{separator}article"
    assert REGISTRY["_visible_inline_text"](sample) == sample


def test_nbsp_entity_cannot_collapse_back_to_canonical_registry_receipt() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    encoded = live.replace(" ", "&nbsp;")
    assert live in corpus
    assert REGISTRY["_visible_inline_text"](encoded) == live.replace(" ", "\u00a0")
    mutated = corpus.replace(live, encoded, 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)


@pytest.mark.parametrize(
    "wrapper",
    (
        '<span itemscope><meta itemprop="license" content="CC0">{}</span>',
        '<span property="license" content="CC0">{}</span>',
        '<meta name="license" content="CC0">{}',
    ),
)
def test_machine_readable_rights_metadata_is_rejected_from_governed_registry(
    wrapper: str,
) -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "The article is a scholarly research reference."
    assert live in corpus
    mutated = corpus.replace(live, wrapper.format(live), 1)
    assert "machine-metadata" in POLICING["_governed_surface_html_violations"](mutated)
    with pytest.raises(AssertionError, match="machine-readable Microdata/RDFa/body metadata"):
        REGISTRY["_validate_registry_corpus"](mutated)
'''
    current = REGRESSION_PATH.read_text(encoding="utf-8")
    marker = "# PR4 raw-heading / non-collapsible-spacing / machine-metadata regressions"
    if marker in current:
        raise SystemExit("regression block already present")
    if not current.endswith("\n"):
        current += "\n"
    REGRESSION_PATH.write_text(current + addition.lstrip("\n"), encoding="utf-8")

    print("patched=policing,registry,current-review-regressions")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("reproduce", "apply"))
    args = parser.parse_args()
    if args.mode == "reproduce":
        reproduce()
    else:
        apply()


if __name__ == "__main__":
    main()
