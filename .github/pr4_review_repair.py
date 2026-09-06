from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


PATH = Path("tests/test_research_reference_registry.py")


def load_registry_module(path: Path):
    spec = importlib.util.spec_from_file_location("_pr4_registry_before_repair", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_status_hash(module) -> str:
    corpus = module.CORPUS.read_text(encoding="utf-8")
    rendered, structure = module._markdown_views(corpus)
    status_start, _ = module._visible_markdown_heading_span(
        structure, module.STATUS_HEADING
    )
    status_end, _ = module._visible_markdown_heading_span(
        structure, module.SOURCE_USE_HEADING
    )
    assert status_start < status_end
    visible_status = module._visible_inline_text(rendered[status_start:status_end])
    return hashlib.sha256(visible_status.encode("utf-8")).hexdigest()


def main() -> None:
    original = PATH.read_text(encoding="utf-8")
    module = load_registry_module(PATH)
    status_hash = canonical_status_hash(module)
    text = original

    def replace_once(old: str, new: str, *, label: str) -> None:
        nonlocal text
        count = text.count(old)
        assert count == 1, f"{label}: expected one match, found {count}"
        text = text.replace(old, new, 1)

    replace_once(
        'SOURCE_USE_SECTION_HASH = "ffd50e6c62ec28f45dc18e372c0feb4d04f044671e1fc8cfb30293175935f1bb"\n',
        'SOURCE_USE_SECTION_HASH = "ffd50e6c62ec28f45dc18e372c0feb4d04f044671e1fc8cfb30293175935f1bb"\n'
        f'STATUS_SECTION_HASH = "{status_hash}"\n',
        label="Status hash fixture",
    )

    replace_once(
        'SVG_NON_RENDERING_METADATA_TAGS = frozenset({"title", "desc"})',
        'SVG_NON_RENDERING_METADATA_TAGS = frozenset('
        '{"title", "desc", "defs", "symbol", "metadata"}'
        ')',
        label="SVG non-rendering containers",
    )

    attribute_helper = '''def _first_html_attribute_values(
    attrs: list[tuple[str, str | None]],
) -> dict[str, str]:
    """Match browser parsing by preserving the first duplicate attribute value."""
    values: dict[str, str] = {}
    for key, value in attrs:
        values.setdefault(key.lower(), value or "")
    return values


'''
    css_marker = 'def _css_hides_element(style: str) -> bool:\n'
    assert attribute_helper not in text
    assert text.count(css_marker) == 1
    text = text.replace(css_marker, attribute_helper + css_marker, 1)

    duplicate_attr_expr = 'values = {key.lower(): (value or "") for key, value in attrs}'
    duplicate_attr_count = text.count(duplicate_attr_expr)
    assert duplicate_attr_count == 2, (
        f"duplicate attribute reducer: expected two matches, found {duplicate_attr_count}"
    )
    text = text.replace(
        duplicate_attr_expr,
        'values = _first_html_attribute_values(attrs)',
    )

    replace_once(
        'def _normalise_https_destination(candidate: str) -> str | None:\n',
        'def _normalise_https_destination(\n'
        '    candidate: str,\n'
        '    *,\n'
        '    strip_trailing_prose_punctuation: bool = False,\n'
        ') -> str | None:\n',
        label="HTTPS normalizer signature",
    )
    replace_once(
        '    value = value.strip().strip("<>").rstrip(".,;:!?")\n',
        '    value = value.strip().strip("<>")\n'
        '    if strip_trailing_prose_punctuation:\n'
        '        value = value.rstrip(".,;:!?")\n',
        label="HTTPS punctuation policy",
    )

    replace_once(
        'def _require_rendered_https_destination(candidate: str) -> str:\n'
        '    destination = _normalise_https_destination(candidate)\n',
        'def _require_rendered_https_destination(\n'
        '    candidate: str,\n'
        '    *,\n'
        '    strip_trailing_prose_punctuation: bool = False,\n'
        ') -> str:\n'
        '    destination = _normalise_https_destination(\n'
        '        candidate,\n'
        '        strip_trailing_prose_punctuation=strip_trailing_prose_punctuation,\n'
        '    )\n',
        label="rendered HTTPS destination wrapper",
    )

    bare_loop = '''    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destinations.append(
            _require_rendered_https_destination(match.group("url"))
        )
'''
    bare_loop_replacement = '''    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destinations.append(
            _require_rendered_https_destination(
                match.group("url"),
                strip_trailing_prose_punctuation=True,
            )
        )
'''
    replace_once(
        bare_loop,
        bare_loop_replacement,
        label="bare URL punctuation policy",
    )

    status_helper = '''def _normalised_status_value(corpus: str) -> str:
    """Return the complete browser-visible Status section."""
    rendered, structure = _markdown_views(corpus)
    start, _ = _visible_markdown_heading_span(structure, STATUS_HEADING)
    end, _ = _visible_markdown_heading_span(structure, SOURCE_USE_HEADING)
    assert start < end, "rendered Status/source-use boundaries are out of order"
    return _visible_inline_text(rendered[start:end])


'''
    source_use_marker = 'def _normalised_source_use_rules_value(corpus: str) -> str:\n'
    assert status_helper not in text
    assert text.count(source_use_marker) == 1
    text = text.replace(source_use_marker, status_helper + source_use_marker, 1)

    old_status_validation = '''    status_start, _ = _visible_markdown_heading_span(structure, STATUS_HEADING)
    status_end, _ = _visible_markdown_heading_span(structure, SOURCE_USE_HEADING)
    assert status_start < status_end, "rendered Status/source-use boundaries are out of order"
    visible_status = _visible_inline_text(rendered[status_start:status_end])
    assert REDISTRIBUTION_INVARIANT in visible_status, (
        "redistribution invariant must remain browser-visible inside the Status section"
    )

'''
    new_status_validation = '''    visible_status = _normalised_status_value(corpus)
    assert REDISTRIBUTION_INVARIANT in visible_status, (
        "redistribution invariant must remain browser-visible inside the Status section"
    )
    actual_status_hash = hashlib.sha256(visible_status.encode("utf-8")).hexdigest()
    assert actual_status_hash == STATUS_SECTION_HASH, (
        "browser-visible Status section changed or was weakened: "
        f"expected hash {STATUS_SECTION_HASH!r}, got {actual_status_hash!r}"
    )

'''
    replace_once(
        old_status_validation,
        new_status_validation,
        label="Status section validation",
    )

    regression_marker = "test_latest_review_status_and_browser_semantics_regressions"
    assert regression_marker not in text
    regressions = r'''


def test_latest_review_status_and_browser_semantics_regressions():
    corpus = CORPUS.read_text(encoding="utf-8")
    original_status = (
        "Australian comedy is used here as a rich source of adversarial pragmatic "
        "structures. It is not treated as a census of how Australians speak."
    )
    assert original_status in corpus
    mutated = corpus.replace(
        original_status,
        "Australian comedy is representative evidence of how all Australians speak.",
        1,
    )
    with pytest.raises(AssertionError, match="Status section changed or was weakened"):
        _validate_registry_corpus(mutated)

    # HTML tree builders preserve the first duplicate attribute. A later style
    # attribute must not resurrect text hidden by the first one.
    assert _visible_html_text(
        '<span style="display:none" style="display:inline">hidden governance</span>'
    ) == ""

    for container in ("defs", "symbol", "metadata"):
        assert _visible_html_text(
            f"<svg><{container}><text>hidden governance</text></{container}></svg>"
        ) == ""


def test_explicit_link_destinations_preserve_punctuation_but_bare_prose_trims_it():
    expected = "https://www.wikipedia.org/wiki/Australia;"
    assert _usable_https_destinations(
        f'<a href="{expected}">source</a>'
    ) == (expected,)
    assert _usable_https_destinations(f"[source]({expected})") == (expected,)
    assert _usable_https_destinations(f"<{expected}>") == (expected,)
    assert _usable_https_destinations(expected) == (expected.rstrip(";"),)
'''
    text += regressions

    assert text != original
    PATH.write_text(text, encoding="utf-8")
    print(f"Pinned browser-visible Status SHA-256: {status_hash}")


if __name__ == "__main__":
    main()
