from __future__ import annotations

import hashlib
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_TEST = ROOT / "tests" / "test_research_reference_registry.py"
WORKSTREAM_TEST = ROOT / "tests" / "test_workstream_h_methodology.py"
METHODOLOGY = ROOT / "docs" / "METHODOLOGY.md"


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_registry_test() -> None:
    text = REGISTRY_TEST.read_text(encoding="utf-8")

    text = replace_once(
        text,
        'ENTRY_HEADING_PATTERN = re.compile(r"(?m)^ {0,3}(?P<heading>### .+?)[ \\t]*$")\n',
        'ENTRY_HEADING_PATTERN = re.compile(r"(?m)^ {0,3}(?P<heading>### .+?)[ \\t]*$")\n'
        'HTML_ENTRY_HEADING_PATTERN = re.compile(r"(?is)<h3\\b[^>]*>.*?</h3\\s*>")\n',
        label="HTML h3 heading pattern",
    )

    text = replace_once(
        text,
        'CONTRACT_SENTENCE = (\n'
        '    "Every adopted post-Phase-2 registry entry must record all of the following fields"\n'
        ')\n',
        'CONTRACT_SENTENCE = (\n'
        '    "Every adopted post-Phase-2 registry entry must record all of the following fields"\n'
        ')\n'
        'REGISTRATION_CONTRACT_HASH = "__AUTO_REGISTRATION_CONTRACT_HASH__"\n',
        label="registration contract hash constant",
    )

    text = replace_once(
        text,
        '        self.parts: list[str] = []\n'
        '        self.stack: list[tuple[str, bool]] = []\n',
        '        self.parts: list[str] = []\n'
        '        self.hrefs: list[str] = []\n'
        '        self.stack: list[tuple[str, bool]] = []\n',
        label="visible HTML parser href storage",
    )

    text = replace_once(
        text,
        '    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n'
        '        inherited = self.stack[-1][1] if self.stack else False\n'
        '        self.stack.append((tag.lower(), inherited or self._is_hidden(tag, attrs)))\n',
        '    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n'
        '        inherited = self.stack[-1][1] if self.stack else False\n'
        '        hidden = inherited or self._is_hidden(tag, attrs)\n'
        '        if tag.lower() == "a" and not hidden:\n'
        '            for key, value in attrs:\n'
        '                if key.lower() == "href" and value:\n'
        '                    self.hrefs.append(value)\n'
        '                    break\n'
        '        self.stack.append((tag.lower(), hidden))\n',
        label="visible HTML parser anchor extraction",
    )

    text = replace_once(
        text,
        'def _visible_html_text(text: str) -> str:\n'
        '    parser = _VisibleHTMLTextParser()\n'
        '    try:\n'
        '        parser.feed(text)\n'
        '        parser.close()\n'
        '    except Exception:\n'
        '        return ""\n'
        '    return " ".join(parser.parts)\n',
        'def _visible_html_text(text: str) -> str:\n'
        '    parser = _VisibleHTMLTextParser()\n'
        '    try:\n'
        '        parser.feed(text)\n'
        '        parser.close()\n'
        '    except Exception:\n'
        '        return ""\n'
        '    return " ".join(parser.parts)\n'
        '\n'
        '\n'
        'def _visible_html_links(text: str) -> tuple[str, ...]:\n'
        '    """Return navigable href values from browser-visible raw HTML anchors."""\n'
        '    parser = _VisibleHTMLTextParser()\n'
        '    try:\n'
        '        parser.feed(text)\n'
        '        parser.close()\n'
        '    except Exception:\n'
        '        return ()\n'
        '    return tuple(parser.hrefs)\n',
        label="visible HTML link helper",
    )

    text = replace_once(
        text,
        'def _usable_https_destinations(text: str) -> tuple[str, ...]:\n'
        '    """Extract usable rendered links while excluding code and link titles."""\n'
        '    structure = _structural_registry_text(text)\n'
        '    destinations: list[str] = []\n'
        '\n'
        '    for match in MARKDOWN_LINK_PATTERN.finditer(structure):\n',
        'def _usable_https_destinations(text: str) -> tuple[str, ...]:\n'
        '    """Extract usable rendered links while excluding code and link titles."""\n'
        '    structure = _structural_registry_text(text)\n'
        '    destinations: list[str] = []\n'
        '\n'
        '    for candidate in _visible_html_links(structure):\n'
        '        destination = _normalise_https_destination(candidate)\n'
        '        if destination is not None:\n'
        '            destinations.append(destination)\n'
        '\n'
        '    for match in MARKDOWN_LINK_PATTERN.finditer(structure):\n',
        label="raw HTML anchor destination extraction",
    )

    old_sections = '''def _registered_sections(corpus: str) -> dict[str, str]:
    batch = _registered_batch(corpus)
    rendered, structure = _markdown_views(batch)
    matches = list(ENTRY_HEADING_PATTERN.finditer(structure))
    assert matches, "registered post-Phase-2 batch contains no entries"

    headings = [match.group("heading") for match in matches]
    duplicates = sorted(
        heading for heading, count in Counter(headings).items() if count > 1
    )
    assert not duplicates, f"duplicate registered-entry headings: {duplicates}"

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group("heading")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(batch)
        sections[heading] = rendered[match.start():end]
    return sections
'''
    new_sections = '''def _registered_sections(corpus: str) -> dict[str, str]:
    batch = _registered_batch(corpus)
    rendered, structure = _markdown_views(batch)
    matches: list[tuple[int, int, str]] = [
        (match.start(), match.end(), match.group("heading"))
        for match in ENTRY_HEADING_PATTERN.finditer(structure)
    ]
    for match in HTML_ENTRY_HEADING_PATTERN.finditer(structure):
        visible_heading = _visible_inline_text(rendered[match.start():match.end()])
        if visible_heading:
            matches.append((match.start(), match.end(), f"### {visible_heading}"))
    matches.sort(key=lambda item: item[0])
    assert matches, "registered post-Phase-2 batch contains no entries"

    headings = [heading for _, _, heading in matches]
    duplicates = sorted(
        heading for heading, count in Counter(headings).items() if count > 1
    )
    assert not duplicates, f"duplicate registered-entry headings: {duplicates}"

    sections: dict[str, str] = {}
    for index, (start, _heading_end, heading) in enumerate(matches):
        end = matches[index + 1][0] if index + 1 < len(matches) else len(batch)
        sections[heading] = rendered[start:end]
    return sections
'''
    text = replace_once(text, old_sections, new_sections, label="rendered HTML entry discovery")

    old_validation = '''def _validate_registry_corpus(corpus: str) -> None:
    structure = _structural_registry_text(corpus)
    assert CONTRACT_HEADING in structure, "rendered registration contract is missing"
    contract_start = structure.index(CONTRACT_HEADING)
    assert BATCH_HEADING in structure[contract_start:], "rendered governed batch heading is missing"
    contract_end = structure.index(BATCH_HEADING, contract_start)
    contract_section = structure[contract_start:contract_end]
    assert CONTRACT_SENTENCE in contract_section, "rendered registration contract is incomplete"
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in structure

    sections = _registered_sections(corpus)
'''
    new_validation = '''def _validate_registry_corpus(corpus: str) -> None:
    rendered, structure = _markdown_views(corpus)
    assert CONTRACT_HEADING in structure, "rendered registration contract is missing"
    contract_start = structure.index(CONTRACT_HEADING)
    assert BATCH_HEADING in structure[contract_start:], "rendered governed batch heading is missing"
    contract_end = structure.index(BATCH_HEADING, contract_start)
    contract_section = structure[contract_start:contract_end]
    assert CONTRACT_SENTENCE in contract_section, "rendered registration contract is incomplete"
    visible_contract = _visible_inline_text(rendered[contract_start:contract_end])
    actual_contract_hash = hashlib.sha256(visible_contract.encode("utf-8")).hexdigest()
    assert actual_contract_hash == REGISTRATION_CONTRACT_HASH, (
        "rendered registration contract changed or was weakened: "
        f"expected hash {REGISTRATION_CONTRACT_HASH!r}, got {actual_contract_hash!r}"
    )
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in structure

    sections = _registered_sections(corpus)
'''
    text = replace_once(text, old_validation, new_validation, label="complete contract pinning")

    appended_tests = r'''


def test_registry_discovery_detects_rendered_html_h3_entry():
    corpus = CORPUS.read_text(encoding="utf-8")
    injected = (
        BATCH_HEADING
        + "\n\n<h3>Fabricated ungoverned reference</h3>\n\n"
        + "Arbitrary provenance prose.\n\n"
    )
    mutated = corpus.replace(BATCH_HEADING, injected, 1)
    sections = _registered_sections(mutated)
    assert "### Fabricated ungoverned reference" in sections
    with pytest.raises(AssertionError, match="every rendered governed entry"):
        _validate_registry_corpus(mutated)


def test_complete_registration_contract_is_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(CONTRACT_HEADING)
    end = corpus.index(BATCH_HEADING, start)
    contract = corpus[start:end]
    keep = contract.index(CONTRACT_SENTENCE) + len(CONTRACT_SENTENCE)
    weakened = contract[:keep] + "\n\nAll other requirements are optional.\n\n"
    mutated = corpus[:start] + weakened + corpus[end:]
    with pytest.raises(AssertionError, match="registration contract changed or was weakened"):
        _validate_registry_corpus(mutated)


def test_html_anchor_source_destination_is_included_in_pinned_set():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        SOURCE_TYPE_FIELD,
        '<a href="https://wikipedia.org/">alternate source</a>\n\n' + SOURCE_TYPE_FIELD,
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)
'''
    if "def test_registry_discovery_detects_rendered_html_h3_entry():" in text:
        raise RuntimeError("new registry regressions already present")
    text += appended_tests

    REGISTRY_TEST.write_text(text, encoding="utf-8")

    namespace = runpy.run_path(str(REGISTRY_TEST))
    corpus = namespace["CORPUS"].read_text(encoding="utf-8")
    rendered, structure = namespace["_markdown_views"](corpus)
    contract_start = structure.index(namespace["CONTRACT_HEADING"])
    contract_end = structure.index(namespace["BATCH_HEADING"], contract_start)
    visible_contract = namespace["_visible_inline_text"](
        rendered[contract_start:contract_end]
    )
    digest = hashlib.sha256(visible_contract.encode("utf-8")).hexdigest()

    text = REGISTRY_TEST.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'REGISTRATION_CONTRACT_HASH = "__AUTO_REGISTRATION_CONTRACT_HASH__"',
        f'REGISTRATION_CONTRACT_HASH = "{digest}"',
        label="computed registration contract hash",
    )
    REGISTRY_TEST.write_text(text, encoding="utf-8")


def patch_methodology() -> None:
    text = METHODOLOGY.read_text(encoding="utf-8")
    old = (
        "Where a research question depends on historical stereotype structure, use an abstract "
        "placeholder or non-identity-targeted synthetic analogue unless exact material has an "
        "attributable source, an appropriate rights basis, and a documented governance rationale."
    )
    new = (
        "Where a research question depends on historical stereotype structure, use an abstract "
        "placeholder or non-identity-targeted synthetic analogue. An attributable source may "
        "document that a stereotype existed, but exact group-stereotyping wording must not be "
        "reproduced in repository content or redistributable benchmark items."
    )
    text = replace_once(text, old, new, label="categorical stereotype wording prohibition")
    METHODOLOGY.write_text(text, encoding="utf-8")


def patch_workstream_test() -> None:
    text = WORKSTREAM_TEST.read_text(encoding="utf-8")
    addition = '''\n\ndef test_trans_tasman_methodology_never_allows_exact_group_stereotype_wording():\n    text = METHODOLOGY.read_text(encoding="utf-8")\n    start = text.index("## Trans-Tasman and Slang/Operational Experiment Design")\n    end = text.index("## Australian and United States Policing-Context Experiment Design", start)\n    section = text[start:end]\n    assert "exact group-stereotyping wording must not be reproduced" in section\n    assert "unless exact material has an attributable source" not in section\n'''
    if "def test_trans_tasman_methodology_never_allows_exact_group_stereotype_wording():" in text:
        raise RuntimeError("methodology stereotype regression already present")
    WORKSTREAM_TEST.write_text(text + addition, encoding="utf-8")


def main() -> None:
    patch_registry_test()
    patch_methodology()
    patch_workstream_test()


if __name__ == "__main__":
    main()
