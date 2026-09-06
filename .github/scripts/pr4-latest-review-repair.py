from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1. Raw-HTML provenance anchors become usable only after they contain
# browser-visible linked text. This prevents an empty <a href=...></a> from
# donating a destination while unrelated visible URL text sits beside it.
replace_once(
    "tests/test_research_reference_registry.py",
    '''        self.parts: list[str] = []
        self.hrefs: list[str] = []
        self.stack: list[tuple[str, bool, bool]] = []
''',
    '''        self.parts: list[str] = []
        self.hrefs: list[str] = []
        self.stack: list[tuple[str, bool, bool]] = []
        self.open_anchors: list[tuple[int, str, int]] = []
''',
    "registry anchor state",
)
replace_once(
    "tests/test_research_reference_registry.py",
    '''        if tag == "a" and not hidden and not inert:
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.hrefs.append(value)
                    break
        self.stack.append((tag, hidden, inert))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
''',
    '''        if tag == "a" and not hidden and not inert:
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.open_anchors.append((len(self.stack), value, len(self.parts)))
                    break
        self.stack.append((tag, hidden, inert))

    def _close_anchors_from_depth(self, depth: int) -> None:
        remaining: list[tuple[int, str, int]] = []
        for anchor_depth, href, parts_start in self.open_anchors:
            if anchor_depth < depth:
                remaining.append((anchor_depth, href, parts_start))
                continue
            linked_text = " ".join(self.parts[parts_start:]).strip()
            if linked_text:
                self.hrefs.append(href)
        self.open_anchors = remaining

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
''',
    "registry deferred anchor href",
)
replace_once(
    "tests/test_research_reference_registry.py",
    '''    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
''',
    '''    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self._close_anchors_from_depth(index)
                del self.stack[index:]
                return

    def close(self) -> None:
        super().close()
        self._close_anchors_from_depth(0)

    def handle_data(self, data: str) -> None:
''',
    "registry anchor close",
)

# 2. The shared policing/methodology visibility reducer must treat fully
# transparent governed text as hidden, using the same cascade semantics as the
# registry reducer.
old_policing_css = '''def _css_hides_element(style: str) -> bool:
    """Apply inline CSS declaration order and !important precedence."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())
    winners: dict[str, tuple[bool, str]] = {}
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        name, raw_value = declaration.split(":", 1)
        name = name.strip()
        if name not in {"display", "visibility"}:
            continue
        raw_value = raw_value.strip()
        important = re.search(r"\\s*!important\\s*$", raw_value) is not None
        value = re.sub(r"\\s*!important\\s*$", "", raw_value).strip()
        previous = winners.get(name)
        if previous is None or (important and not previous[0]) or important == previous[0]:
            winners[name] = (important, value)

    display = winners.get("display", (False, ""))[1]
    visibility = winners.get("visibility", (False, ""))[1]
    return display == "none" or visibility in {"hidden", "collapse"}
'''
new_policing_css = '''def _css_hides_element(style: str) -> bool:
    """Apply inline CSS declaration order and !important precedence."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style.lower())
    winners: dict[str, tuple[bool, str]] = {}
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        name, raw_value = declaration.split(":", 1)
        name = name.strip()
        if name not in {"display", "visibility", "opacity"}:
            continue
        raw_value = raw_value.strip()
        important = re.search(r"\\s*!important\\s*$", raw_value) is not None
        value = re.sub(r"\\s*!important\\s*$", "", raw_value).strip()
        previous = winners.get(name)
        if previous is None or (important and not previous[0]) or important == previous[0]:
            winners[name] = (important, value)

    display = winners.get("display", (False, ""))[1]
    visibility = winners.get("visibility", (False, ""))[1]
    opacity = winners.get("opacity", (False, ""))[1]
    opacity_hidden = False
    if opacity:
        numeric_opacity = opacity[:-1].strip() if opacity.endswith("%") else opacity
        try:
            opacity_hidden = float(numeric_opacity) <= 0.0
        except ValueError:
            opacity_hidden = False
    return (
        display == "none"
        or visibility in {"hidden", "collapse"}
        or opacity_hidden
    )
'''
replace_once(
    "tests/test_policing_context_roadmap.py",
    old_policing_css,
    new_policing_css,
    "policing opacity semantics",
)
replace_once(
    "tests/test_workstream_h_methodology.py",
    old_policing_css,
    new_policing_css,
    "Workstream H opacity semantics",
)

# 3. Regression for empty HTML anchors. The visible entity-encoded URL beside
# the empty anchor must not make the empty href into usable provenance.
replace_once(
    "tests/test_research_reference_registry.py",
    '''\n\n@pytest.mark.parametrize(\n    "container",\n    (\n        "-",\n        "***",\n''',
    '''\n\ndef test_empty_html_anchor_cannot_supply_registered_source_destination():\n    section = (\n        "### Example\\n\\n"\n        '**Registered source:** <a href="https://example.com/source"></a> '\n        "https&#58;//example.com/source\\n\\n"\n        "**Source type:** example\\n"\n    )\n    with pytest.raises(AssertionError, match="no usable HTTPS destination"):\n        _require_registered_source_link("### Example", section)\n\n\n@pytest.mark.parametrize(\n    "container",\n    (\n        "-",\n        "***",\n''',
    "empty HTML anchor regression",
)

# 4. Workstream I opacity regression.
replace_once(
    "tests/test_policing_context_roadmap.py",
    '''def test_policing_source_gate_cannot_be_negated():\n''',
    '''def test_policing_safeguard_cannot_hide_with_zero_opacity():\n    roadmap = ROADMAP.read_text(encoding="utf-8")\n    clause = "CASUAL ADDRESS != FRIENDSHIP OR CONSENT"\n    assert clause in roadmap\n    mutated = roadmap.replace(\n        clause,\n        f'<span style="opacity:0">{clause}</span>',\n        1,\n    )\n    with pytest.raises(AssertionError, match="missing policing-workstream safeguard"):\n        _validate_policing_workstream(mutated)\n\n\ndef test_policing_source_gate_cannot_be_negated():\n''',
    "policing opacity regression",
)

# 5. Workstream H and Trans-Tasman methodology both use their own copy of the
# browser-visible reducer, so exercise opacity in both hidden-clause loops.
replace_once(
    "tests/test_workstream_h_methodology.py",
    '''        f'<span style="display:/**/none">{listener_clause}</span>',\n        f'[placeholder](# "{listener_clause}")',\n''',
    '''        f'<span style="display:/**/none">{listener_clause}</span>',\n        f'<span style="opacity:0">{listener_clause}</span>',\n        f'[placeholder](# "{listener_clause}")',\n''',
    "Workstream H opacity regression",
)
replace_once(
    "tests/test_workstream_h_methodology.py",
    '''        f"<span hidden>{stereotype_clause}</span>",\n        f'[placeholder](# "{stereotype_clause}")',\n''',
    '''        f"<span hidden>{stereotype_clause}</span>",\n        f'<span style="opacity:0">{stereotype_clause}</span>',\n        f'[placeholder](# "{stereotype_clause}")',\n''',
    "Trans-Tasman opacity regression",
)

# 6. Canonical policing methodology receipt must also fail when the high-stakes
# review gate survives only as fully transparent text.
replace_once(
    "tests/test_policing_contract_receipt.py",
    '''\n\ndef test_policing_methodology_start_must_be_a_visible_heading():\n''',
    '''\n\ndef test_high_stakes_methodology_gate_cannot_hide_with_zero_opacity():\n    methodology = METHODOLOGY.read_text(encoding="utf-8")\n    assert CANONICAL_HIGH_STAKES_REVIEW_SENTENCE in methodology\n    mutated = methodology.replace(\n        CANONICAL_HIGH_STAKES_REVIEW_SENTENCE,\n        f'<span style="opacity:0">{CANONICAL_HIGH_STAKES_REVIEW_SENTENCE}</span>',\n        1,\n    )\n    with pytest.raises(AssertionError):\n        _assert_canonical_high_stakes_gate(mutated)\n\n\ndef test_policing_methodology_start_must_be_a_visible_heading():\n''',
    "canonical policing opacity regression",
)

print("latest PR4 review repair applied")
