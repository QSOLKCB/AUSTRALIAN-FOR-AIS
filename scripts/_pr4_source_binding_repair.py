"""Apply four reviewed PR4 fixes only to the exact inspected validator blobs."""
from pathlib import Path
import subprocess

EXPECTED = {
    "tests/test_research_reference_registry.py": "0cc1cdd51c8edec25f82e95019fdfe5b9717b836",
    "tests/test_policing_context_roadmap.py": "905fafced8b5663437aa72a9930532a2661bcd30",
}


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Repair anchor count changed: {text.count(old)}: {old[:100]!r}")
    return text.replace(old, new, 1)


for name, expected in EXPECTED.items():
    actual = subprocess.check_output(["git", "hash-object", name], text=True).strip()
    if actual != expected:
        raise RuntimeError(f"Refusing changed source: {name}: {actual}")

path = Path("tests/test_research_reference_registry.py")
text = path.read_text(encoding="utf-8")
text = replace_once(text,
    '        SOURCES_KEY: sources,',
    '''        SOURCES_KEY: sources,
        # All adopted source fields currently display their URL as the label.
        # Keep each association, not just independent label/destination sets.
        "source_bindings": tuple((source, source) for source in sources),''')
text = replace_once(text,
    '        names = [key.lower() for key, _ in attrs]',
    '''        names = [key.lower() for key, _ in attrs]
        # Attribute parsing accepts every HTML whitespace form around '=' and
        # does not mistake strings inside another attribute for real styling.
        if "style" in names:
            self.found.add("inline-style")
        if "class" in names or tag in {"style", "link"}:
            self.found.add("styling")
        if tag == "img":
            self.found.add("replacement")''')
# Parsed attribute names replace the spelling-sensitive styling regex checks.
text = replace_once(text,
    '''        if GOVERNED_STYLING_HTML_PATTERN.search(logical):
            found.add("styling")
''', '')
text = replace_once(text,
    '''        if GOVERNED_INLINE_STYLE_HTML_PATTERN.search(logical):
            found.add("inline-style")
''', '')
text = replace_once(text,
    '        self.hrefs: list[str] = []',
    '        self.hrefs: list[str] = []\n        self.link_bindings: list[tuple[str, str]] = []')
text = replace_once(text,
    '''            linked_text = " ".join(self.parts[parts_start:]).strip()
            if linked_text:
                self.hrefs.append(href)''',
    '''            linked_text = "".join(self.parts[parts_start:]).strip()
            if linked_text:
                self.hrefs.append(href)
                self.link_bindings.append((linked_text, href))''')
text = replace_once(text,
    'class _VisuallyHiddenTableDetector(HTMLParser):',
    '''def _visible_html_link_bindings(text: str) -> tuple[tuple[str, str], ...]:
    """Keep linked character data attached to its already-decoded HTML href."""
    parser = _VisibleHTMLTextParser()
    parser.feed(text)
    parser.close()
    return tuple(parser.link_bindings)


class _VisuallyHiddenTableDetector(HTMLParser):''')
start = text.index('def _usable_https_destinations(')
end = text.index('\n\ndef _visible_markdown_heading_span', start)
text = text[:start] + '''def _usable_https_source_bindings(
    text: str,
    *,
    reference_scope: str | None = None,
) -> tuple[tuple[str, str], ...]:
    """Extract visible label/destination pairs through every supported link path."""
    structure = _mask_hidden_html_regions(_structural_registry_text(text))
    definition_source = text if reference_scope is None else reference_scope
    reference_structure = _mask_hidden_html_regions(
        _structural_registry_text(definition_source)
    )
    bindings: list[tuple[str, str]] = []

    def record(label: str, candidate: str, *, html_label: bool = False,
               strip_prose: bool = False) -> None:
        destination = _require_rendered_https_destination(
            candidate,
            strip_trailing_prose_punctuation=strip_prose,
            decode_markdown_syntax=not html_label,
        )
        # HTMLParser already decoded character references in linked text.
        # Escape that text before the existing canonical normalizer so it
        # cannot be decoded or interpreted as live HTML a second time.
        label_source = html.escape(label, quote=False) if html_label else label
        visible_label = _visible_inline_text(label_source)
        bindings.append((visible_label, destination))

    for label, candidate in _visible_html_link_bindings(structure):
        record(label, candidate, html_label=True)

    markdown_structure = _mask_raw_html_tags_for_markdown_link_discovery(structure)
    reference_markdown_structure = _mask_raw_html_tags_for_markdown_link_discovery(
        reference_structure
    )
    inline_links = _markdown_inline_links(markdown_structure)
    for link in inline_links:
        if not link.image:
            record(link.label, link.destination.strip("<>"))
    structure_without_inline_links = _mask_inline_markdown_links(
        markdown_structure, inline_links,
    )
    definitions = _reference_definitions(reference_markdown_structure)

    for match in REFERENCE_LINK_PATTERN.finditer(structure_without_inline_links):
        if match.group("image"):
            continue
        reference = match.group("reference") or match.group("label")
        candidate = definitions.get(_normalise_reference_label(reference))
        if candidate is not None:
            record(match.group("label"), candidate)

    without_reference_links = REFERENCE_LINK_PATTERN.sub("", structure_without_inline_links)
    for match in SHORTCUT_REFERENCE_LINK_PATTERN.finditer(without_reference_links):
        if match.group("image"):
            continue
        candidate = definitions.get(_normalise_reference_label(match.group("label")))
        if candidate is not None:
            record(match.group("label"), candidate)

    for match in AUTOLINK_PATTERN.finditer(without_reference_links):
        record(match.group("url"), match.group("url"))
    without_links = AUTOLINK_PATTERN.sub("", without_reference_links)
    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        candidate = match.group("url")
        record(candidate, candidate, strip_prose=True)
    return tuple(bindings)


def _usable_https_destinations(
    text: str,
    *,
    reference_scope: str | None = None,
) -> tuple[str, ...]:
    """Compatibility view of the same source-binding extraction pipeline."""
    return tuple(destination for _, destination in _usable_https_source_bindings(
        text, reference_scope=reference_scope,
    ))
''' + text[end:]
# Preserve existing helper contracts and their diagnostics; collect bindings
# alongside destinations only when complete entry validation requests them.
start = text.index('def _require_registered_source_link(')
end = text.index('\ndef _require_community_governance', start)
block = text[start:end]
block = replace_once(block,
    '    reference_scope: str | None = None,',
    '    reference_scope: str | None = None,\n    source_bindings: list[tuple[str, str]] | None = None,')
block = replace_once(block,
    '''    destinations = _usable_https_destinations(
        source_value,
        reference_scope=reference_scope,
    )''',
    '''    bindings = _usable_https_source_bindings(
        source_value,
        reference_scope=reference_scope,
    )
    destinations = tuple(destination for _, destination in bindings)''')
block = replace_once(block,
    '    return destinations',
    '''    if source_bindings is not None:
        source_bindings.extend(bindings)
    return destinations''')
text = text[:start] + block + text[end:]
start = text.index('def _validate_registered_entry(')
end = text.index('\ndef _normalised_status_value', start)
block = text[start:end]
block = replace_once(block,
    '''    destinations = _require_registered_source_link(
        entry,
        section,
        reference_scope=reference_scope,
    )''',
    '''    source_bindings: list[tuple[str, str]] = []
    destinations = _require_registered_source_link(
        entry,
        section,
        reference_scope=reference_scope,
        source_bindings=source_bindings,
    )''')
block = replace_once(block,
    '    _require_complete_entry_integrity(entry, section)',
    '''    expected_bindings = {
        (_visible_inline_text(label), destination)
        for label, destination in contract["source_bindings"]
    }
    assert set(source_bindings) == expected_bindings, (
        f"{entry} registered-source label/destination bindings changed: "
        f"expected {sorted(expected_bindings)!r}, got {sorted(source_bindings)!r}"
    )
    _require_complete_entry_integrity(entry, section)''')
text = text[:start] + block + text[end:]
text = replace_once(text,
    'contains replacement-content HTML (object/embed/iframe/canvas)',
    'contains replacement-content HTML (object/embed/iframe/canvas/img)')
# Check images before slicing can discard an enclosing tag or hidden region.
text = replace_once(text,
    '    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)',
    '''    corpus_forbidden_html = _forbidden_governed_html_constructs(corpus)
    assert "replacement" not in corpus_forbidden_html, (
        "registry contains replacement-content HTML, including raw images; "
        "rendered replacement content cannot be sealed as character data"
    )''')
compile(text, str(path), 'exec')
path.write_text(text, encoding="utf-8")

path = Path("tests/test_policing_context_roadmap.py")
text = path.read_text(encoding="utf-8")
text = replace_once(text,
    '''        if tag == "canvas":
            self.violations.add("canvas")''',
    '''        if tag == "canvas":
            self.violations.add("canvas")
        if tag == "img":
            self.violations.add("raw-image")''')
text = replace_once(text,
    '''    violations = _governed_surface_html_violations(markdown)
    assert "canvas" not in violations,''',
    '''    violations = _governed_surface_html_violations(markdown)
    assert "raw-image" not in violations, (
        "raw image HTML is not allowed on governed methodology surfaces"
    )
    assert "canvas" not in violations,''')
compile(text, str(path), 'exec')
path.write_text(text, encoding="utf-8")
print("Applied four review fixes; existing documents and integrity fixtures are unchanged.", flush=True)
