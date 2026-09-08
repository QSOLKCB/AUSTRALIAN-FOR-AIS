from __future__ import annotations

from pathlib import Path
import subprocess
import sys

REVIEWED_HEAD = "76c6059faea160e00d0bc89bc836ec56ea77eeaa"
BRANCH = "research-corpus-governed-expansion"
SCRIPT = ".github/repair-pr4-aria-details-blockquote.py"
WORKFLOW = ".github/workflows/pr4-aria-details-blockquote-repair.yml"
POLICING = Path("tests/test_policing_context_roadmap.py")
REGRESSIONS = Path("tests/test_pr4_current_review_regressions.py")


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def output(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


# Refuse to repair any branch that has moved except for this guarded scaffold.
run("git", "merge-base", "--is-ancestor", REVIEWED_HEAD, "HEAD")
changed = set(filter(None, output("git", "diff", "--name-only", f"{REVIEWED_HEAD}..HEAD").splitlines()))
expected_scaffold = {SCRIPT, WORKFLOW}
if changed != expected_scaffold:
    raise SystemExit(
        f"guard failed: expected only repair scaffold after {REVIEWED_HEAD}, got {sorted(changed)!r}"
    )

policing = POLICING.read_text(encoding="utf-8")
old_aria = 'if {"aria-label", "aria-labelledby", "aria-description", "aria-describedby"}.intersection(attribute_names):'
new_aria = 'if {"aria-label", "aria-labelledby", "aria-description", "aria-describedby", "aria-details"}.intersection(attribute_names):'
if policing.count(old_aria) != 1:
    raise SystemExit(f"guard failed: expected one ARIA metadata policy site, found {policing.count(old_aria)}")
policing = policing.replace(old_aria, new_aria, 1)

old_quote = '        if tag == "q":\n            self.violations.add("generated-quotation")'
new_quote = '        if tag in {"q", "blockquote"}:\n            self.violations.add("generated-quotation")'
if policing.count(old_quote) != 1:
    raise SystemExit(f"guard failed: expected one quotation policy site, found {policing.count(old_quote)}")
policing = policing.replace(old_quote, new_quote, 1)
POLICING.write_text(policing, encoding="utf-8")

regressions = REGRESSIONS.read_text(encoding="utf-8")
marker = "# PR4 aria-details / blockquote review regressions"
if marker in regressions:
    raise SystemExit("guard failed: aria-details/block-quotation regressions already present")
regressions += r'''


# PR4 aria-details / blockquote review regressions

def test_aria_details_is_rejected_for_governed_source_link() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    detailed = f'**Registered source:** <a href="{url}" aria-details="rights-note">{url}</a>'
    assert live in corpus
    mutated = corpus.replace(live, detailed, 1)
    mutated = mutated.replace(
        REGISTRY["BATCH_END"],
        REGISTRY["BATCH_END"] + '\n\n<p id="rights-note">This material is freely reusable.</p>',
        1,
    )
    assert "accessible-name" in POLICING["_governed_surface_html_violations"](mutated)
    with pytest.raises(AssertionError, match="accessible-name overrides"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_blockquote_cannot_reframe_pinned_registry_rights_assertion() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    rights = (
        "**Rights and provenance boundary:** The ABC programme page establishes the work as a "
        "research reference. No programme dialogue, subtitles, scripts, episode transcripts, "
        "audiovisual material, character material, or other copyrighted expression is licensed "
        "to this repository by registration. Availability through ABC iview is not permission "
        "to redistribute content."
    )
    assert rights in corpus
    quoted = f"<blockquote>{rights}</blockquote>"
    mutated = corpus.replace(rights, quoted, 1)
    assert "generated-quotation" in POLICING["_governed_surface_html_violations"](mutated)
    with pytest.raises(AssertionError, match="generated quotation HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)
'''
REGRESSIONS.write_text(regressions, encoding="utf-8")

run("git", "diff", "--check")

# Exact review regressions first, then the core governance surfaces, datasets, and full suite.
run(sys.executable, "-m", "pytest", "-q", "tests/test_pr4_current_review_regressions.py")
run(
    sys.executable,
    "-m",
    "pytest",
    "-q",
    "tests/test_research_reference_registry.py",
    "tests/test_policing_context_roadmap.py",
    "tests/test_workstream_h_methodology.py",
    "tests/test_policing_contract_receipt.py",
    "tests/test_phase2_review_followup.py",
    "tests/test_pr4_current_review_regressions.py",
)
run(sys.executable, "-m", "australian_for_ais.cli", "validate", "data/starter/examples.jsonl")
run(sys.executable, "-m", "australian_for_ais.cli", "validate-pilot", "data/pilot/items.jsonl")
run(sys.executable, "-m", "pytest", "-q", "--disable-warnings", "--maxfail=1")

# Self-clean the privileged repair scaffold before creating the substantive commit.
Path(SCRIPT).unlink()
Path(WORKFLOW).unlink()
run("git", "diff", "--check")
run("git", "add", str(POLICING), str(REGRESSIONS), SCRIPT, WORKFLOW)

status = output("git", "status", "--porcelain")
allowed = {
    "M  tests/test_policing_context_roadmap.py",
    "M  tests/test_pr4_current_review_regressions.py",
    "D  .github/repair-pr4-aria-details-blockquote.py",
    "D  .github/workflows/pr4-aria-details-blockquote-repair.yml",
}
actual = set(filter(None, status.splitlines()))
if actual != allowed:
    raise SystemExit(f"guard failed: unexpected staged state {sorted(actual)!r}")

run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
run("git", "commit", "-m", "Reject ARIA details and quotation reframing")
run("git", "push", "origin", f"HEAD:{BRANCH}")
print("repair_commit=" + output("git", "rev-parse", "HEAD"))
print("repair_tree=" + output("git", "rev-parse", "HEAD^{tree}"))
