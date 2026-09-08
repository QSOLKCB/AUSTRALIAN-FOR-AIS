"""Section-scoped integrity checks for ASCFT-derived methodology."""

from pathlib import Path
import hashlib
import runpy
import re

import pytest


ROOT = Path(__file__).parent.parent
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"
POLICING_TEST = Path(__file__).parent / "test_policing_context_roadmap.py"
ASCFT_HEADING = "## ASCFT-Derived Experiment Design"
NEXT_HEADING = "## Trans-Tasman and Slang/Operational Experiment Design"
ASCFT_VISIBLE_SHA256 = "2eaae57359c818aeb946266d467b571a1dd7a5a3276c386b244b371d4adb07a8"
ASCFT_RECORDS_SHA256 = "80df8104e2c0b3b8f4a05efd45941f32ebce8910dd51665490694d0664d1affa"
MANDATORY_EPISTEMIC_BOUNDARIES = (
    "FORMAL ANALOGY != PHYSICAL ONTOLOGY",
    "MATHEMATICAL MODEL != EMPIRICALLY VALIDATED MECHANISM",
)


def _namespace() -> dict[str, object]:
    return runpy.run_path(str(POLICING_TEST))


def _raw_ascft_section(text: str) -> str:
    namespace = _namespace()
    namespace["_assert_supported_governed_html"](
        namespace["_governed_surface_html_violations"](text)
    )
    structure = namespace["_rendered_structure"](text)
    start, _ = namespace["_visible_markdown_heading_span"](structure, ASCFT_HEADING)
    end, _ = namespace["_visible_markdown_heading_span"](structure, NEXT_HEADING)
    assert start < end, "rendered ASCFT methodology boundary is invalid"
    return text[start:end]


def _normalised_ascft_visible_value(text: str) -> str:
    namespace = _namespace()
    return " ".join(namespace["_visible_text"](_raw_ascft_section(text)).split())


def _ascft_record_receipt(text: str) -> str:
    namespace = _namespace()
    records = namespace["_normalised_visible_workstream_records"](_raw_ascft_section(text))
    return "\n".join(
        f"{signature}\x1f{line}" for signature, line in records
    )



def _assert_ascft_has_no_links(text: str) -> None:
    """Reject live hyperlinks because ASCFT has no approved link contract."""
    namespace = _namespace()
    raw_section = _raw_ascft_section(text)
    rendered = namespace["_mask_hidden_html_regions"](
        namespace["_rendered_structure"](raw_section)
    )
    assert not tuple(namespace["_iter_inline_markdown_destinations"](rendered)), (
        "unexpected Markdown hyperlink in governed ASCFT methodology"
    )
    assert namespace["AUTOLINK_PATTERN"].search(rendered) is None, (
        "unexpected URI autolink in governed ASCFT methodology"
    )
    assert namespace["EMAIL_AUTOLINK_PATTERN"].search(rendered) is None, (
        "unexpected email autolink in governed ASCFT methodology"
    )
    assert re.search(
        r"<\s*a\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*\bhref\s*=",
        rendered,
        flags=re.IGNORECASE,
    ) is None, "unexpected raw HTML hyperlink in governed ASCFT methodology"
    assert re.search(
        r"(?<!!)\[[^\]\r\n]+\]\s*\[[^\]\r\n]*\]",
        rendered,
    ) is None, "unexpected reference-style hyperlink in governed ASCFT methodology"

def _assert_ascft_integrity(text: str) -> str:
    _assert_ascft_has_no_links(text)
    value = _normalised_ascft_visible_value(text)
    actual_visible_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
    assert actual_visible_hash == ASCFT_VISIBLE_SHA256, (
        "browser-visible ASCFT methodology changed or was weakened: "
        f"expected {ASCFT_VISIBLE_SHA256!r}, got {actual_visible_hash!r}"
    )
    records = _ascft_record_receipt(text)
    actual_records_hash = hashlib.sha256(records.encode("utf-8")).hexdigest()
    assert actual_records_hash == ASCFT_RECORDS_SHA256, (
        "ASCFT methodology record hierarchy changed: "
        f"expected {ASCFT_RECORDS_SHA256!r}, got {actual_records_hash!r}"
    )
    for boundary in MANDATORY_EPISTEMIC_BOUNDARIES:
        assert boundary in value, f"mandatory ASCFT epistemic boundary missing: {boundary}"
    return value


def test_ascft_methodology_section_is_pinned():
    _assert_ascft_integrity(METHODOLOGY.read_text(encoding="utf-8"))


@pytest.mark.parametrize("boundary", MANDATORY_EPISTEMIC_BOUNDARIES)
def test_ascft_mandatory_epistemic_boundaries_cannot_be_removed_or_reversed(boundary: str):
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    marker = f"- **{boundary}**"
    assert marker in methodology

    deleted = methodology.replace(marker, "", 1)
    with pytest.raises(AssertionError, match="ASCFT methodology changed or was weakened"):
        _assert_ascft_integrity(deleted)

    reversed_text = methodology.replace(
        marker,
        f"- **REVERSED: {boundary}**",
        1,
    )
    with pytest.raises(AssertionError, match="ASCFT methodology changed or was weakened"):
        _assert_ascft_integrity(reversed_text)

def test_ascft_methodology_rejects_unregistered_hyperlinks():
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    phrase = "The epistemic boundary is mandatory:"
    assert phrase in methodology
    mutated = methodology.replace(
        phrase,
        f"[{phrase}](https://example.com/unregistered)",
        1,
    )
    assert _normalised_ascft_visible_value(mutated) == _normalised_ascft_visible_value(methodology)
    assert _ascft_record_receipt(mutated) == _ascft_record_receipt(methodology)
    with pytest.raises(AssertionError, match="unexpected Markdown hyperlink"):
        _assert_ascft_integrity(mutated)
