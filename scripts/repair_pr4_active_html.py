from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def append_once(text: str, marker: str, addition: str) -> str:
    if marker in text:
        return text
    if not text.endswith("\n"):
        text += "\n"
    return text + "\n" + addition.lstrip("\n")


root = Path(__file__).resolve().parents[1]
policing_path = root / "tests" / "test_policing_context_roadmap.py"
registry_path = root / "tests" / "test_research_reference_registry.py"

policing = policing_path.read_text(encoding="utf-8")
policing = replace_once(
    policing,
    '''        attribute_names = {key.lower() for key, _ in attrs}\n        if {"shadowrootmode", "shadowroot"}.intersection(attribute_names):\n            self.violations.add("shadow-root")\n''',
    '''        attribute_names = {key.lower() for key, _ in attrs}\n        if any(name.startswith("on") for name in attribute_names):\n            self.violations.add("event-handler")\n        # Raw Markdown is embedded into an existing HTML document. A live\n        # duplicate root tag can merge attributes onto that document root, so\n        # reject html/body rather than approximating tree-builder semantics.\n        if tag in {"html", "body"}:\n            self.violations.add("document-root")\n        if {"shadowrootmode", "shadowroot"}.intersection(attribute_names):\n            self.violations.add("shadow-root")\n''',
    label="shared HTML event/root policy",
)
policing = replace_once(
    policing,
    '''        "executable-url": "executable URL HTML",\n        "non-rendering-container": "non-rendering datalist HTML",\n''',
    '''        "executable-url": "executable URL HTML",\n        "event-handler": "inline event-handler HTML",\n        "document-root": "document-root HTML",\n        "non-rendering-container": "non-rendering datalist HTML",\n''',
    label="shared HTML assertion descriptions",
)
policing = append_once(
    policing,
    "def test_latest_active_html_policy_rejects_event_handlers_and_document_roots():",
    r'''
def test_latest_active_html_policy_rejects_event_handlers_and_document_roots():
    handler = _governed_surface_html_violations(
        '<span onclick="document.body.textContent=\'weakened\'">canonical text</span>'
    )
    assert "event-handler" in handler
    with pytest.raises(AssertionError, match="event-handler"):
        _assert_supported_governed_html(handler)

    for tag in ("html", "body"):
        root_tag = _governed_surface_html_violations(f"<{tag} hidden></{tag}>")
        assert "document-root" in root_tag
        with pytest.raises(AssertionError, match="document-root"):
            _assert_supported_governed_html(root_tag)


def test_policing_workstream_rejects_event_handlers_before_section_slicing():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    clause = "source-gated research proposal"
    mutated = roadmap.replace(
        clause,
        '<span onclick="document.body.textContent=\'weakened\'">'
        + clause
        + "</span>",
        1,
    )
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)


@pytest.mark.parametrize("tag", ("html", "body"))
def test_policing_workstream_rejects_duplicate_document_root_tags(tag: str):
    roadmap = ROADMAP.read_text(encoding="utf-8")
    mutated = roadmap + f"\n<{tag} hidden></{tag}>\n"
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)
''',
)
policing_path.write_text(policing, encoding="utf-8")

registry = registry_path.read_text(encoding="utf-8")
registry = replace_once(
    registry,
    '''    "executable-url",\n    "non-rendering-container",\n})\n''',
    '''    "executable-url",\n    "event-handler",\n    "document-root",\n    "non-rendering-container",\n})\n''',
    label="registry active-document kinds",
)
registry = replace_once(
    registry,
    '''        if any(name.startswith("on") for name in names):\n            self.found.add("event-handler")\n        if tag in GOVERNED_CONDITIONAL_RAW_TEXT_TAGS:\n''',
    '''        if any(name.startswith("on") for name in names):\n            self.found.add("event-handler")\n        if tag in {"html", "body"}:\n            self.found.add("document-root")\n        if tag in GOVERNED_CONDITIONAL_RAW_TEXT_TAGS:\n''',
    label="registry semantic detector root tags",
)
registry = replace_once(
    registry,
    '''    assert "executable-url" not in found, (\n        "executable URL HTML is not allowed in governed documents"\n    )\n    assert "non-rendering-container" not in found, (\n''',
    '''    assert "executable-url" not in found, (\n        "executable URL HTML is not allowed in governed documents"\n    )\n    assert "event-handler" not in found, (\n        "inline event-handler HTML is not allowed in governed documents"\n    )\n    assert "document-root" not in found, (\n        "document-root HTML is not allowed in governed documents"\n    )\n    assert "non-rendering-container" not in found, (\n''',
    label="registry global active-document assertions",
)
registry = append_once(
    registry,
    "def test_latest_registry_active_html_policy_is_corpus_wide():",
    r'''
def test_latest_registry_active_html_policy_is_corpus_wide():
    handler = _forbidden_governed_html_constructs(
        '<span onclick="document.body.textContent=\'weakened\'">canonical text</span>'
    )
    assert "event-handler" in handler
    with pytest.raises(AssertionError, match="event-handler"):
        _assert_no_active_document_html(handler)

    for tag in ("html", "body"):
        root_tag = _forbidden_governed_html_constructs(f"<{tag} hidden></{tag}>")
        assert "document-root" in root_tag
        with pytest.raises(AssertionError, match="document-root"):
            _assert_no_active_document_html(root_tag)


def test_registry_rejects_event_handler_outside_registered_entries():
    corpus = CORPUS.read_text(encoding="utf-8")
    invariant = "RESEARCH REFERENCE != REDISTRIBUTABLE DATA"
    mutated = corpus.replace(
        invariant,
        '<span onclick="document.body.textContent=\'weakened\'">'
        + invariant
        + "</span>",
        1,
    )
    with pytest.raises(AssertionError, match="event-handler"):
        _validate_registry_corpus(mutated)


@pytest.mark.parametrize("tag", ("html", "body"))
def test_registry_rejects_duplicate_document_root_tags_before_slicing(tag: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    mutated = corpus + f"\n<{tag} hidden></{tag}>\n"
    with pytest.raises(AssertionError, match="document-root"):
        _validate_registry_corpus(mutated)
''',
)
registry_path.write_text(registry, encoding="utf-8")
