from __future__ import annotations

import hashlib
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "tests" / "test_research_reference_registry.py"
CORPUS = ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md"

source = TEST.read_text(encoding="utf-8")
original = source
module = runpy.run_path(str(TEST))
corpus = CORPUS.read_text(encoding="utf-8")

rendered, structure = module["_markdown_views"](corpus)
start, _ = module["_visible_markdown_heading_span"](structure, module["BATCH_END"])
bindings = module["_usable_https_source_bindings"](
    rendered[start:],
    reference_scope=corpus,
)
receipt = "\n".join(f"{label}\x1f{destination}" for label, destination in bindings)
binding_hash = hashlib.sha256(receipt.encode("utf-8")).hexdigest()

constant_pattern = re.compile(
    r'(?m)^(REGISTRY_TRAILING_VISIBLE_SHA256\s*=\s*["\'][0-9a-f]{64}["\']\s*)$'
)
match = constant_pattern.search(source)
if not match:
    raise SystemExit("REGISTRY_TRAILING_VISIBLE_SHA256 constant not found")
if "REGISTRY_TRAILING_LINK_BINDINGS_SHA256" not in source:
    source = source[: match.end()] + (
        f'\nREGISTRY_TRAILING_LINK_BINDINGS_SHA256 = "{binding_hash}"'
    ) + source[match.end():]

old_helper = '''def _normalised_registry_trailing_value(corpus: str) -> str:\n    """Return browser-visible registry content from the post-batch boundary to EOF."""\n    rendered, structure = _markdown_views(corpus)\n    start, _ = _visible_markdown_heading_span(structure, BATCH_END)\n    return _visible_inline_text(rendered[start:])\n'''
new_helper = old_helper + '''\n\ndef _registry_trailing_link_binding_receipt(corpus: str) -> str:\n    """Return a deterministic seal of trailing visible link label/destination bindings."""\n    rendered, structure = _markdown_views(corpus)\n    start, _ = _visible_markdown_heading_span(structure, BATCH_END)\n    bindings = _usable_https_source_bindings(\n        rendered[start:],\n        reference_scope=corpus,\n    )\n    return "\\n".join(\n        f"{label}\\x1f{destination}" for label, destination in bindings\n    )\n'''
if "def _registry_trailing_link_binding_receipt" not in source:
    if old_helper not in source:
        raise SystemExit("trailing helper block not found")
    source = source.replace(old_helper, new_helper, 1)

old_validator = '''    visible_trailing = _normalised_registry_trailing_value(corpus)\n    actual_trailing_hash = hashlib.sha256(visible_trailing.encode("utf-8")).hexdigest()\n    assert actual_trailing_hash == REGISTRY_TRAILING_VISIBLE_SHA256, (\n        "browser-visible trailing registry content changed outside the governed receipts: "\n        f"expected hash {REGISTRY_TRAILING_VISIBLE_SHA256!r}, got {actual_trailing_hash!r}"\n    )\n'''
new_validator = old_validator + '''\n    trailing_binding_receipt = _registry_trailing_link_binding_receipt(corpus)\n    actual_trailing_binding_hash = hashlib.sha256(\n        trailing_binding_receipt.encode("utf-8")\n    ).hexdigest()\n    assert actual_trailing_binding_hash == REGISTRY_TRAILING_LINK_BINDINGS_SHA256, (\n        "trailing registry link bindings changed outside the governed receipts: "\n        f"expected hash {REGISTRY_TRAILING_LINK_BINDINGS_SHA256!r}, "\n        f"got {actual_trailing_binding_hash!r}"\n    )\n'''
if "trailing_binding_receipt = _registry_trailing_link_binding_receipt" not in source:
    if old_validator not in source:
        raise SystemExit("trailing validator block not found")
    source = source.replace(old_validator, new_validator, 1)

needle = '''def test_trailing_registry_visible_corpus_is_pinned():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    _validate_registry_corpus(corpus)\n    mutated = (\n        corpus.rstrip()\n        + "\\n\\nAll registered sources may be copied freely into benchmark data.\\n"\n    )\n    with pytest.raises(AssertionError, match="browser-visible trailing registry content changed"):\n        _validate_registry_corpus(mutated)\n'''
regression = needle + '''\n\ndef test_trailing_registry_link_destinations_are_pinned():\n    corpus = CORPUS.read_text(encoding="utf-8")\n    mutated = corpus.replace(\n        "- https://en.wikipedia.org/wiki/The_Chaser",\n        "- [https://en.wikipedia.org/wiki/The_Chaser](https://example.com/unregistered)",\n        1,\n    )\n    assert mutated != corpus\n    assert _normalised_registry_trailing_value(mutated) == _normalised_registry_trailing_value(corpus)\n    with pytest.raises(AssertionError, match="trailing registry link bindings changed"):\n        _validate_registry_corpus(mutated)\n'''
if "def test_trailing_registry_link_destinations_are_pinned" not in source:
    if needle not in source:
        raise SystemExit("trailing visible regression block not found")
    source = source.replace(needle, regression, 1)

if source == original:
    raise SystemExit("repair made no changes")
TEST.write_text(source, encoding="utf-8")
print(f"Pinned trailing link-binding SHA-256: {binding_hash}")
print(f"Trailing bindings sealed: {len(bindings)}")
