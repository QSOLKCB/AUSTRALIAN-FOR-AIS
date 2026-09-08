from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{path}: expected exactly one replacement target, found {count}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


policing = Path("tests/test_policing_context_roadmap.py")

replace_once(
    policing,
    '''        # Preserve an unmatched candidate run, or the literal surplus left
        # after CommonMark consumes only part of a matched delimiter run.
        if not (
            bool(run["can_open"])
            or bool(run["can_close"])
            or int(run["open_consumed"])
            or int(run["close_consumed"])
        ):
            continue
        sentinel = (
''',
    '''        # Any unconsumed delimiter character is browser-visible literal text.
        # That includes a run surrounded by whitespace, which can neither open
        # nor close emphasis and therefore must not disappear from the receipt.
        sentinel = (
''',
)

replace_once(
    policing,
    '''        if tag in {"iframe", "object", "embed", "audio", "video", "meter", "progress"}:
            self.violations.add("replacement-content")
''',
    '''        if tag in {
            "iframe", "object", "embed", "audio", "video", "meter", "progress",
            "marquee",
        }:
            self.violations.add("replacement-content")
''',
)

replace_once(
    policing,
    '''        attribute_names = {key.lower() for key, _ in attrs}
        if any(name.startswith("on") for name in attribute_names):
''',
    '''        attribute_names = {key.lower() for key, _ in attrs}
        # Hyperlink auditing can send an additional network request that is not
        # represented by the sealed href binding. Fail closed on it.
        if tag == "a" and "ping" in attribute_names:
            self.violations.add("executable-url")
        if any(name.startswith("on") for name in attribute_names):
''',
)

replace_once(
    policing,
    '''        structure = _rendered_structure(roadmap)
        start, _ = _visible_markdown_heading_span(structure, WORKSTREAM_HEADING)
''',
    '''        # Heading discovery must ignore raw HTML block payloads so a
        # heading-looking line inside <pre> cannot become a section boundary.
        heading_structure = _rendered_structure(roadmap)
        start, _ = _visible_markdown_heading_span(
            heading_structure, WORKSTREAM_HEADING
        )
''',
)
replace_once(
    policing,
    '''    end, _ = _visible_markdown_heading_span(structure, WORKSTREAM_END_HEADING)
''',
    '''    end, _ = _visible_markdown_heading_span(
        heading_structure, WORKSTREAM_END_HEADING
    )
''',
)
replace_once(
    policing,
    '''    visible_structure = _mask_hidden_html_regions(structure)
    return visible_structure[start:end]
''',
    '''    # Integrity uses a distinct same-length view that preserves raw HTML
    # blocks. Visible <pre>/<textarea> character data therefore contributes to
    # the receipt even though those blocks remain inert for heading discovery.
    integrity_structure = _rendered_structure(roadmap, html_spans=[])
    assert len(integrity_structure) == len(heading_structure), (
        "heading and integrity rendering views lost source-offset alignment"
    )
    visible_structure = _mask_hidden_html_regions(integrity_structure)
    return visible_structure[start:end]
''',
)

replace_once(
    policing,
    '''

    integrity_value = "\\n".join(visible_lines)
''',
    '''

    # Workstream I currently has no approved hyperlinks. Keep destinations out
    # of the prose-only receipt only by rejecting link-bearing syntax entirely;
    # future links must be explicitly registered and added to this contract.
    assert not tuple(_iter_inline_markdown_destinations(rendered)), (
        "unexpected Markdown hyperlink in governed policing workstream"
    )
    assert AUTOLINK_PATTERN.search(rendered) is None, (
        "unexpected autolink in governed policing workstream"
    )
    assert re.search(
        r"<\\s*a\\b(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*\\bhref\\s*=",
        rendered,
        flags=re.IGNORECASE,
    ) is None, "unexpected raw HTML hyperlink in governed policing workstream"
    assert re.search(
        r"(?<!!)\\[[^\\]\\r\\n]+\\]\\s*\\[[^\\]\\r\\n]*\\]",
        rendered,
    ) is None, "unexpected reference-style hyperlink in governed policing workstream"

    integrity_value = "\\n".join(visible_lines)
''',
)

registry = Path("tests/test_research_reference_registry.py")
replace_once(
    registry,
    '''_SHARED_HTML_PREFLIGHT = runpy.run_path(
    str(Path(__file__).with_name("test_policing_context_roadmap.py"))
)["_governed_surface_html_violations"]
''',
    '''_SHARED_POLICING = runpy.run_path(
    str(Path(__file__).with_name("test_policing_context_roadmap.py"))
)
_SHARED_HTML_PREFLIGHT = _SHARED_POLICING["_governed_surface_html_violations"]
''',
)
replace_once(
    registry,
    '''HTML_P_IMPLIED_END_START_TAGS = frozenset({
    "address", "article", "aside", "blockquote", "div", "dl", "fieldset",
    "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header",
    "hgroup", "hr", "main", "menu", "nav", "ol", "p", "pre", "search",
    "section", "table", "ul",
})
''',
    '''# Keep paragraph-closing browser semantics identical to the shared
# governed-surface parser instead of maintaining a drifting registry copy.
HTML_P_IMPLIED_END_START_TAGS = _SHARED_POLICING[
    "HTML_P_IMPLIED_END_START_TAGS"
]
''',
)

regression = Path("tests/test_pr4_astra_review_regressions.py")
regression.write_text(
    '''"""Regressions for the September 8 Astra review of PR #4."""

from pathlib import Path
import runpy

import pytest


TESTS = Path(__file__).parent
ROOT = TESTS.parent
POLICING = runpy.run_path(str(TESTS / "test_policing_context_roadmap.py"))
REGISTRY = runpy.run_path(str(TESTS / "test_research_reference_registry.py"))


def test_visible_pre_content_changes_policing_integrity() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    validate = POLICING["_validate_policing_workstream"]
    validate(roadmap)

    boundary = POLICING["WORKSTREAM_END"]
    assert boundary in roadmap
    changed = roadmap.replace(
        boundary,
        "\\n<pre>\\nCurrent sources may be skipped.\\n</pre>\\n" + boundary,
        1,
    )
    with pytest.raises(AssertionError):
        validate(changed)


@pytest.mark.parametrize("marker", ["*", "_"])
def test_whitespace_delimited_literal_marker_changes_policing_integrity(
    marker: str,
) -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    changed = roadmap.replace(
        "not legal advice",
        f"not {marker} legal advice",
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](changed)


def test_zero_sized_marquee_cannot_satisfy_policing_safeguard() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    phrase = "source-gated research proposal"
    changed = roadmap.replace(
        phrase,
        f'<marquee width="0" height="0">{phrase}</marquee>',
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](changed)


def test_unregistered_https_link_cannot_wrap_policing_safeguard() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    phrase = "source-gated research proposal"
    changed = roadmap.replace(
        phrase,
        f'[{phrase}](https://example.com/not-legal-advice)',
        1,
    )
    with pytest.raises(AssertionError, match="hyperlink"):
        POLICING["_validate_policing_workstream"](changed)


def test_anchor_ping_is_rejected_on_registered_source() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(
        encoding="utf-8"
    )
    source = "https://iview.abc.net.au/show/black-comedy"
    changed = corpus.replace(
        source,
        f'<a href="{source}" ping="https://example.com/track">{source}</a>',
        1,
    )
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](changed)


def test_registry_uses_browser_paragraph_end_for_center() -> None:
    rendered = REGISTRY["_visible_html_text"](
        '<p hidden>masked<center>Current sources may be skipped.</center></p>'
    )
    assert rendered == "Current sources may be skipped."


def test_visible_center_after_hidden_paragraph_changes_entry_integrity() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(
        encoding="utf-8"
    )
    marker = "Candidate research mappings:"
    assert marker in corpus
    changed = corpus.replace(
        marker,
        '<p hidden>masked<center>Current sources may be skipped.</center></p>\\n\\n'
        + marker,
        1,
    )
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](changed)
''',
    encoding="utf-8",
)
