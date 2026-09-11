"""Exact regressions for the seven September PR4 review findings."""

from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
POLICING_PATH = ROOT / "tests" / "test_policing_context_roadmap.py"
REGISTRY_PATH = ROOT / "tests" / "test_research_reference_registry.py"
WORKSTREAM_H_PATH = ROOT / "tests" / "test_workstream_h_methodology.py"
PHASE2_PATH = ROOT / "tests" / "test_phase2_review_followup.py"

policing = runpy.run_path(str(POLICING_PATH))
registry = runpy.run_path(str(REGISTRY_PATH))
workstream_h = runpy.run_path(str(WORKSTREAM_H_PATH))
phase2 = runpy.run_path(str(PHASE2_PATH))


@pytest.mark.parametrize(
    "wrapper",
    (
        '<svg width="0" height="0"><text>{}</text></svg>',
        '<math><mphantom>{}</mphantom></math>',
    ),
)
def test_registry_rejects_raw_svg_and_mathml_corpus_wide(wrapper):
    corpus = registry["CORPUS"].read_text(encoding="utf-8")
    phrase = "RESEARCH REFERENCE != REDISTRIBUTABLE DATA"
    assert phrase in corpus
    mutated = corpus.replace(phrase, wrapper.format(phrase), 1)
    with pytest.raises(AssertionError):
        registry["_validate_registry_corpus"](mutated)


@pytest.mark.parametrize("tag", ("rt", "rp"))
def test_shared_reducer_models_ruby_implied_sibling_ends(tag):
    roadmap = policing["ROADMAP"].read_text(encoding="utf-8")
    payload = f'<ruby><{tag} hidden>masked<{tag}>Current sources may be skipped.</ruby>\n'
    mutated = roadmap.replace(policing["WORKSTREAM_END"], "\n" + payload + policing["WORKSTREAM_END"], 1)
    with pytest.raises(AssertionError):
        policing["_validate_policing_workstream"](mutated)


def test_workstream_h_rejects_type6_html_around_citation_markdown():
    roadmap = policing["ROADMAP"].read_text(encoding="utf-8")
    lines = roadmap.splitlines(keepends=True)
    index = next(i for i, line in enumerate(lines) if "[Australian slang dictionary]" in line)
    original = lines[index]
    lines[index] = "<div>\n" + original.rstrip("\r\n") + "\n\n</div>\n"
    mutated = "".join(lines)
    with pytest.raises(AssertionError):
        workstream_h["_assert_workstream_h_integrity"](mutated)


def test_nested_nobr_is_rejected_on_shared_and_registry_surfaces():
    payload = '<nobr hidden>masked<nobr>Current sources may be skipped.</nobr></nobr>'
    roadmap = policing["ROADMAP"].read_text(encoding="utf-8")
    mutated_roadmap = roadmap.replace(
        policing["WORKSTREAM_END"], "\n" + payload + "\n" + policing["WORKSTREAM_END"], 1
    )
    with pytest.raises(AssertionError):
        policing["_validate_policing_workstream"](mutated_roadmap)

    corpus = registry["CORPUS"].read_text(encoding="utf-8")
    status_end = "## Source-use rules"
    mutated_corpus = corpus.replace(status_end, payload + "\n\n" + status_end, 1)
    with pytest.raises(AssertionError):
        registry["_validate_registry_corpus"](mutated_corpus)


@pytest.mark.parametrize("tag", ("td", "head"))
def test_discarded_in_body_hidden_tags_fail_closed(tag):
    roadmap = policing["ROADMAP"].read_text(encoding="utf-8")
    payload = f'<{tag} hidden>Current sources may be skipped.</{tag}>\n'
    mutated = roadmap.replace(policing["WORKSTREAM_END"], "\n" + payload + policing["WORKSTREAM_END"], 1)
    with pytest.raises(AssertionError):
        policing["_validate_policing_workstream"](mutated)


def test_phase2_notes_stop_at_multiline_raw_html_peer_heading():
    changelog = phase2["CHANGELOG"].read_text(encoding="utf-8")
    bullet = "- " + phase2["FREE_TEXT_IAA_BOUNDARY"]
    assert bullet in changelog
    mutated = changelog.replace(bullet, '<h2\nid="x"></h2>\n' + bullet, 1)
    assert phase2["_visible_phase2_notes"](mutated) != phase2["EXPECTED_VISIBLE_PHASE2_NOTES"]


@pytest.mark.parametrize(
    "replacement",
    (
        "source-gated&#32research proposal",
        "source-gated&nbspresearch proposal",
    ),
)
def test_shared_reducer_rejects_semicolonless_html_only_references(replacement):
    roadmap = policing["ROADMAP"].read_text(encoding="utf-8")
    mutated = roadmap.replace("source-gated research proposal", replacement, 1)
    with pytest.raises(AssertionError):
        policing["_validate_policing_workstream"](mutated)


@pytest.mark.parametrize(
    ("snippet", "kind"),
    (
        ("<svg></svg>", "raw-svg"),
        ("<math></math>", "raw-mathml"),
        ("<nobr><nobr>x</nobr></nobr>", "nested-nobr"),
        ("<td hidden>x</td>", "in-body-structure"),
        ("source-gated&#32research proposal", "non-commonmark-character-reference"),
    ),
)
def test_shared_preflight_receipt_exposes_new_review_kinds(snippet, kind):
    assert kind in policing["_governed_surface_html_violations"](snippet)
