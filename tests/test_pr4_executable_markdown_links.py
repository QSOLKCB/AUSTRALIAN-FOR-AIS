"""Regression coverage for executable Markdown destinations on governed surfaces."""

from pathlib import Path
import runpy

import pytest


HERE = Path(__file__).parent
POLICING = runpy.run_path(str(HERE / "test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(HERE / "test_research_reference_registry.py"))


@pytest.mark.parametrize(
    "destination",
    (
        "javascript:document.body.textContent=%27weakened%27",
        "JAVASCRIPT:document.body.textContent=%27weakened%27",
        "javascript&#58;document.body.textContent=%27weakened%27",
        r"javascript\:document.body.textContent=%27weakened%27",
        "vbscript:msgbox%28%27weakened%27%29",
    ),
)
def test_shared_preflight_rejects_executable_inline_markdown_destinations(destination: str) -> None:
    markdown = f"[source-gated research proposal]({destination})"
    violations = POLICING["_governed_surface_html_violations"](markdown)
    assert "executable-url" in violations


@pytest.mark.parametrize(
    "markdown",
    (
        "`[example](javascript:alert(1))`",
        "<!-- [example](javascript:alert(1)) -->",
        "```markdown\n[example](javascript:alert(1))\n```",
        "![image](javascript:alert(1))",
    ),
)
def test_inert_or_non_anchor_markdown_does_not_trigger_executable_link_policy(markdown: str) -> None:
    violations = POLICING["_governed_surface_html_violations"](markdown)
    assert "executable-url" not in violations


def test_policing_validator_rejects_executable_markdown_link_on_required_clause() -> None:
    roadmap = POLICING["ROADMAP"].read_text()
    mutated = roadmap.replace(
        "source-gated research proposal",
        "[source-gated research proposal](javascript:document.body.textContent=%27weakened%27)",
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_registry_validator_rejects_executable_markdown_link_on_status_invariant() -> None:
    corpus = REGISTRY["CORPUS"].read_text()
    invariant = REGISTRY["REDISTRIBUTION_INVARIANT"]
    mutated = corpus.replace(
        invariant,
        f"[{invariant}](javascript:document.body.textContent=%27weakened%27)",
        1,
    )
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated)
