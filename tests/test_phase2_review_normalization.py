"""Regressions for Phase 2 browser/backend normalization and source-tree scripts."""

import pathlib

import pytest

from australian_for_ais.validation import ValidationError, validate_annotation_record

REPO_ROOT = pathlib.Path(__file__).parent.parent
ANNOTATION_UI = REPO_ROOT / "annotation" / "index.html"
ANALYSIS_SCRIPT = REPO_ROOT / "scripts" / "analyse_annotations.py"


def _annotation(**overrides):
    record = {
        "annotation_id": "ann-normalization-1",
        "example_id": "item-1",
        "annotator_id": "annotator-aaaaaaaaaaaa",
        "literal_interpretation": "Literal reading",
        "pragmatic_interpretations": ["Reading A"],
        "primary_pragmatic_interpretation": "Reading A",
        "humour_mechanisms": ["literal"],
        "social_valence": "neutral",
        "hostility": False,
        "confidence": 0.8,
        "ambiguity": False,
        "cultural_dependency": "low",
        "context_required": True,
    }
    record.update(overrides)
    return record


def test_phase2_normalization_matches_browser_lowercase_contract():
    # Locale-independent lowercasing keeps these two readings distinct. This is
    # intentionally different from Phase 1's broader Unicode case-fold matching.
    validate_annotation_record(
        _annotation(
            pragmatic_interpretations=["Straße", "STRASSE"],
            primary_pragmatic_interpretation="Straße",
            ambiguity=True,
        )
    )

    with pytest.raises(ValidationError, match="at least two distinct normalized readings"):
        validate_annotation_record(
            _annotation(
                pragmatic_interpretations=["I", " i "],
                primary_pragmatic_interpretation="I",
                ambiguity=True,
            )
        )

    html = ANNOTATION_UI.read_text(encoding="utf-8")
    assert "value.toLowerCase()" in html
    assert "toLocaleLowerCase" not in html


def test_analysis_script_bootstraps_repo_src_before_package_imports():
    script = ANALYSIS_SCRIPT.read_text(encoding="utf-8")
    path_bootstrap = 'sys.path.insert(0, str(REPO_ROOT / "src"))'
    package_import = "from australian_for_ais.annotation import"

    assert path_bootstrap in script
    assert package_import in script
    assert script.index(path_bootstrap) < script.index(package_import)
