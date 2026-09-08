from __future__ import annotations

from pathlib import Path
import hashlib
import runpy

ROOT = Path(__file__).resolve().parents[1]
POLICING_PATH = ROOT / "tests" / "test_policing_context_roadmap.py"
REGISTRY_PATH = ROOT / "tests" / "test_research_reference_registry.py"
WORKSTREAM_G_PATH = ROOT / "tests" / "test_workstream_g_integrity.py"
REGRESSION_PATH = ROOT / "tests" / "test_pr4_latest_review_regressions.py"
CORPUS_PATH = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one replacement anchor, found {count}")
    return text.replace(old, new, 1)


# Derive the new structural fixture from the canonical pre-repair tree, then
# commit the resulting literal. Do not compute it dynamically in the validator.
registry_ns = runpy.run_path(str(REGISTRY_PATH))
corpus = CORPUS_PATH.read_text(encoding="utf-8")
_, structure = registry_ns["_markdown_views"](corpus)
contract_start, _ = registry_ns["_visible_markdown_heading_span"](
    structure, registry_ns["CONTRACT_HEADING"]
)
contract_end, _ = registry_ns["_visible_markdown_heading_span"](
    structure, registry_ns["BATCH_HEADING"]
)
contract_records = registry_ns["_SHARED_POLICING"][
    "_normalised_visible_workstream_records"
](corpus[contract_start:contract_end])
contract_receipt = "\n".join(
    f"{signature}\x1f{line}" for signature, line in contract_records
)
contract_records_hash = hashlib.sha256(contract_receipt.encode("utf-8")).hexdigest()

# 1) Shared HTML policy: every rel attribute on a governed HTML element is
# uncontracted machine-readable semantics, and add a reusable link-free gate.
policing = POLICING_PATH.read_text(encoding="utf-8")
policing = replace_once(
    policing,
    '''            or ("rel" in attribute_names and tag not in {"a", "area", "link"})\n            or "license" in rel_tokens\n''',
    '''            or "rel" in attribute_names\n''',
    "semantic rel policy",
)
link_free_helper = r'''

def _assert_link_free_governed_section(markdown: str, *, context: str) -> None:
    """Require a governed section to contain no rendered hyperlinks."""
    html_spans: list[tuple[int, int]] = []
    structure = _rendered_structure(markdown, html_spans=html_spans)
    markdown_characters = list(structure)
    raw_html_parts: list[str] = []
    for start, end in html_spans:
        raw_html_parts.append(structure[start:end])
        markdown_characters[start:end] = " " * (end - start)

    markdown_only = "".join(markdown_characters)
    remaining_tags = list(PREFLIGHT_HTML_TAG.finditer(markdown_only))
    for match in reversed(remaining_tags):
        raw_html_parts.append(match.group(0))
        markdown_characters[match.start():match.end()] = " " * (
            match.end() - match.start()
        )
    markdown_only = "".join(markdown_characters)

    assert not tuple(_iter_inline_markdown_destinations(markdown_only)), (
        f"{context} must remain link-free: unexpected Markdown hyperlink"
    )
    assert AUTOLINK_PATTERN.search(markdown_only) is None, (
        f"{context} must remain link-free: unexpected URI autolink"
    )
    assert EMAIL_AUTOLINK_PATTERN.search(markdown_only) is None, (
        f"{context} must remain link-free: unexpected email autolink"
    )
    assert LINK_REFERENCE_DEFINITION_PATTERN.search(markdown_only) is None, (
        f"{context} must remain link-free: unexpected link-reference definition"
    )
    assert re.search(
        r"(?<!!)\[[^\]\r\n]+\]\s*\[[^\]\r\n]*\]",
        markdown_only,
    ) is None, f"{context} must remain link-free: unexpected reference-style hyperlink"

    raw_html = "\n".join(raw_html_parts)
    assert re.search(
        r"<\s*(?:a|area)\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*\bhref\s*=",
        raw_html,
        flags=re.IGNORECASE,
    ) is None, f"{context} must remain link-free: unexpected raw HTML hyperlink"
'''
policing = replace_once(
    policing,
    '\n\ndef _visible_text(markdown: str) -> str:\n',
    link_free_helper + '\n\ndef _visible_text(markdown: str) -> str:\n',
    "shared link-free helper insertion",
)
POLICING_PATH.write_text(policing, encoding="utf-8")

# 2) Registry: consume rendered-break corpus-wide, add a structural receipt for
# the registration contract, and keep the contract link-free.
registry = REGISTRY_PATH.read_text(encoding="utf-8")
registry = replace_once(
    registry,
    'REGISTRATION_CONTRACT_HASH = "1d171556a66c3cfc54a7bf14072d51bb68d17cb390fffa826a0f50329e2d51d6"\n',
    'REGISTRATION_CONTRACT_HASH = "1d171556a66c3cfc54a7bf14072d51bb68d17cb390fffa826a0f50329e2d51d6"\n'
    f'REGISTRATION_CONTRACT_RECORDS_SHA256 = "{contract_records_hash}"\n',
    "registration contract structural hash constant",
)
registry = replace_once(
    registry,
    '''    assert "replacement-content" not in found, (\n        "replacement-content HTML is not allowed in governed documents"\n    )\n''',
    '''    assert "replacement-content" not in found, (\n        "replacement-content HTML is not allowed in governed documents"\n    )\n    assert "rendered-break" not in found, (\n        "rendered break HTML is not allowed in governed documents"\n    )\n''',
    "corpus rendered-break rejection",
)
contract_hash_block = '''    assert actual_contract_hash == REGISTRATION_CONTRACT_HASH, (\n        "rendered registration contract changed or was weakened: "\n        f"expected hash {REGISTRATION_CONTRACT_HASH!r}, got {actual_contract_hash!r}"\n    )\n\n    visible_status = _normalised_status_value(corpus)\n'''
contract_hardened_block = '''    assert actual_contract_hash == REGISTRATION_CONTRACT_HASH, (\n        "rendered registration contract changed or was weakened: "\n        f"expected hash {REGISTRATION_CONTRACT_HASH!r}, got {actual_contract_hash!r}"\n    )\n    contract_raw = corpus[contract_start:contract_end]\n    _SHARED_POLICING["_assert_link_free_governed_section"](\n        contract_raw, context="registration contract"\n    )\n    contract_records = _SHARED_POLICING[\n        "_normalised_visible_workstream_records"\n    ](contract_raw)\n    contract_record_receipt = "\\n".join(\n        f"{signature}\\x1f{line}" for signature, line in contract_records\n    )\n    actual_contract_records_hash = hashlib.sha256(\n        contract_record_receipt.encode("utf-8")\n    ).hexdigest()\n    assert actual_contract_records_hash == REGISTRATION_CONTRACT_RECORDS_SHA256, (\n        "registration-contract record hierarchy changed: "\n        f"expected hash {REGISTRATION_CONTRACT_RECORDS_SHA256!r}, "\n        f"got {actual_contract_records_hash!r}"\n    )\n\n    visible_status = _normalised_status_value(corpus)\n'''
registry = replace_once(
    registry,
    contract_hash_block,
    contract_hardened_block,
    "registration contract link and hierarchy checks",
)
REGISTRY_PATH.write_text(registry, encoding="utf-8")

# 3) Workstream G already contains approved research citations. Seal their
# exact label/destination pairs instead of banning legitimate links.
g = WORKSTREAM_G_PATH.read_text(encoding="utf-8")
g = replace_once(
    g,
    'POLICING = runpy.run_path(str(Path(__file__).with_name("test_policing_context_roadmap.py")))\n',
    'POLICING = runpy.run_path(str(Path(__file__).with_name("test_policing_context_roadmap.py")))\n'
    'WORKSTREAM_H = runpy.run_path(str(Path(__file__).with_name("test_workstream_h_methodology.py")))\n',
    "Workstream G citation helper import",
)
g = replace_once(
    g,
    "WORKSTREAM_G_RECORDS_SHA256 = 'b1ef6be68642ac60b4ef92eef96e135cd9a0f7a197c0de1c6d865384c1edb11e'\n",
    "WORKSTREAM_G_RECORDS_SHA256 = 'b1ef6be68642ac60b4ef92eef96e135cd9a0f7a197c0de1c6d865384c1edb11e'\n"
    "WORKSTREAM_G_CITATION_LINKS = frozenset({\n"
    "    ('Federation timeline', 'https://peo.gov.au/understand-our-parliament/history-of-parliament/federation/federation'),\n"
    "    ('Constitution introduction', 'https://peo.gov.au/understand-our-parliament/how-parliament-works/the-australian-constitution/introducing-the-australian-constitution'),\n"
    "    ('Commonwealth of Australia Constitution Act', 'https://www.legislation.gov.au/C2004Q00685/asmade/1901-01-01/text/original/epub/OEBPS/document_1/document_1.html'),\n"
    "    ('history of Australian slang terms for sex', 'https://www.abc.net.au/news/2018-03-01/from-rooting-to-bonking-a-history-of-australian-sex-terms/9492856'),\n"
    "})\n",
    "Workstream G citation bindings constant",
)
g = replace_once(
    g,
    '''def _assert_workstream_g_integrity(text: str) -> str:\n    raw = _workstream_g_raw(text)\n    visible = " ".join(POLICING["_visible_text"](raw).split())\n''',
    '''def _assert_workstream_g_integrity(text: str) -> str:\n    raw = _workstream_g_raw(text)\n    rendered_links = WORKSTREAM_H["_rendered_inline_citation_links"](raw)\n    actual_links = set(rendered_links)\n    assert len(rendered_links) == len(actual_links), "duplicate Workstream G citation binding"\n    assert actual_links == WORKSTREAM_G_CITATION_LINKS, (\n        "Workstream G citation label/destination bindings changed: expected "\n        f"{sorted(WORKSTREAM_G_CITATION_LINKS)!r}, got {sorted(actual_links)!r}"\n    )\n    visible = " ".join(POLICING["_visible_text"](raw).split())\n''',
    "Workstream G link binding enforcement",
)
WORKSTREAM_G_PATH.write_text(g, encoding="utf-8")

# 4) Exact adversarial regressions for this Codex batch.
REGRESSION_PATH.write_text(r'''"""Exact regressions for the 2026-09-09 PR #4 Codex review batch."""

from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
REGISTRY = runpy.run_path(str(Path(__file__).with_name("test_research_reference_registry.py")))
WORKSTREAM_G = runpy.run_path(str(Path(__file__).with_name("test_workstream_g_integrity.py")))
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"
ROADMAP = ROOT / "ROADMAP.md"


def test_corpus_wide_gate_rejects_rendered_break_in_status() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    mutated = corpus.replace(
        "not a benchmark dataset",
        "not <hr>a benchmark dataset",
        1,
    )
    with pytest.raises(AssertionError, match="rendered break"):
        REGISTRY["_validate_registry_corpus"](mutated)


@pytest.mark.parametrize("kind", ("markdown", "html"))
def test_workstream_g_binds_anti_stereotype_disclaimer_links(kind: str) -> None:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = WORKSTREAM_G["NONFACTUAL_BOUNDARY"]
    destination = "https://example.com/factual-claim"
    if kind == "markdown":
        replacement = f"[{clause}]({destination})"
    else:
        replacement = f'<a href="{destination}">{clause}</a>'
    mutated = roadmap.replace(clause, replacement, 1)
    with pytest.raises(AssertionError):
        WORKSTREAM_G["_assert_workstream_g_integrity"](mutated)


def test_registration_contract_is_link_free() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    phrase = "the rights and provenance boundary for repository use"
    mutated = corpus.replace(
        phrase,
        f"[{phrase}](https://creativecommons.org/publicdomain/zero/1.0/)",
        1,
    )
    with pytest.raises(AssertionError, match="registration contract must remain link-free"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_registration_contract_preserves_list_hierarchy() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    bullet = "- the rights and provenance boundary for repository use;"
    assert bullet in corpus
    mutated = corpus.replace(bullet, "  " + bullet, 1)
    with pytest.raises(AssertionError, match="record hierarchy"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_governed_anchor_rel_semantics_are_rejected() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    source = f"**Registered source:** {url}"
    replacement = (
        f'**Registered source:** <a href="{url}" rel="author">{url}</a>'
    )
    mutated = corpus.replace(source, replacement, 1)
    with pytest.raises(AssertionError, match="machine-readable"):
        REGISTRY["_validate_registry_corpus"](mutated)
''', encoding="utf-8")

print(f"registration contract structural hash: {contract_records_hash}")
print("PR #4 latest review repair applied")
