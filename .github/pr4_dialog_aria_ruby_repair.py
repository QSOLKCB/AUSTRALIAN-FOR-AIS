from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICING = ROOT / "tests" / "test_policing_context_roadmap.py"
REGRESSIONS = ROOT / "tests" / "test_pr4_native_machine_dialog_regressions.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


text = POLICING.read_text(encoding="utf-8")

text = replace_once(
    text,
    '''    def __init__(self) -> None:\n        super().__init__(convert_charrefs=True)\n        self.violations: set[str] = set()\n        self._anchor_open = False\n        self._nobr_open = False\n\n    def handle_starttag(\n''',
    '''    def __init__(self, source: str = "") -> None:\n        super().__init__(convert_charrefs=True)\n        self.violations: set[str] = set()\n        self._anchor_open = False\n        self._nobr_open = False\n        self._source = source\n        self._line_starts = [0]\n        self._line_starts.extend(match.end() for match in re.finditer(r"\\n", source))\n\n    def _source_offset(self) -> int:\n        """Map HTMLParser's current start-tag position back into source text."""\n        line, column = self.getpos()\n        if 1 <= line <= len(self._line_starts):\n            return self._line_starts[line - 1] + column\n        return 0\n\n    def handle_starttag(\n''',
    "parser source tracking",
)

text = replace_once(
    text,
    '''        attribute_names = {key.lower() for key, _ in attrs}\n        # contenteditable changes committed governance prose into an\n''',
    '''        attribute_names = {key.lower() for key, _ in attrs}\n        # HTMLParser has already tokenized the complete start tag, including\n        # quoted `>` characters and attributes split across source lines. Use\n        # that parsed span to decide whether an open dialog carries governed\n        # prose on the same source line instead of re-tokenizing HTML by regex.\n        if tag == "dialog" and "open" in attribute_names and self._source:\n            start = self._source_offset()\n            start_tag = self.get_starttag_text() or ""\n            end = start + len(start_tag)\n            line_start = self._source.rfind("\\n", 0, start) + 1\n            line_end = self._source.find("\\n", end)\n            if line_end < 0:\n                line_end = len(self._source)\n            prefix = self._source[line_start:start]\n            suffix = self._source[end:line_end]\n            if prefix.strip() or suffix.strip():\n                self.violations.add("dialog-inline-block")\n        # contenteditable changes committed governance prose into an\n''',
    "parsed dialog span",
)

text = replace_once(
    text,
    '''        # An ARIA-disabled provenance anchor can retain its canonical label and\n        # href while assistive technology exposes it as unavailable. Keep that\n        # interaction state inside the governed source-link contract.\n        if (\n            tag == "a"\n            and values.get("aria-disabled", "").strip().casefold() == "true"\n        ):\n            self.violations.add("accessibility-disabled")\n''',
    '''        # aria-disabled propagates disabled semantics to focusable descendants,\n        # so an ancestor can make a generated or nested provenance link appear\n        # unavailable without changing its sealed label/destination. Fail closed\n        # on the true state anywhere on a governed surface.\n        if values.get("aria-disabled", "").strip().casefold() == "true":\n            self.violations.add("accessibility-disabled")\n''',
    "inherited aria-disabled",
)

text = replace_once(
    text,
    '''        if tag in {"datalist", "rp"}:\n            self.violations.add("non-rendering-container")\n''',
    '''        # Ruby changes the visual relationship between base text and annotation.\n        # Do not let a critical qualifier move above/beside its surrounding prose\n        # while flattened character data reconstructs the canonical receipt.\n        if tag in {"datalist", "rp", "ruby", "rt"}:\n            self.violations.add("non-rendering-container")\n''',
    "ruby semantic containers",
)

text = replace_once(
    text,
    '''    parser = _GovernedSurfaceHTMLParser()\n    html_spans: list[tuple[int, int]] = []\n''',
    '''    html_spans: list[tuple[int, int]] = []\n''',
    "delay parser construction",
)

text = replace_once(
    text,
    '''    live_markup = "".join(characters)\n\n    # Block containers are dangerous specifically when they carry/reframe\n''',
    '''    live_markup = "".join(characters)\n    parser = _GovernedSurfaceHTMLParser(live_markup)\n\n    # Block containers are dangerous specifically when they carry/reframe\n''',
    "construct parser with source",
)

text = replace_once(
    text,
    '''    open_dialog_tag = re.compile(\n        r"<dialog\\b(?=[^>]*(?:\\sopen(?:\\s*=|\\s|/?>)))[^>]*>",\n        flags=re.IGNORECASE | re.DOTALL,\n    )\n    # Inspect complete opening-tag spans before source-line splitting. HTML\n    # attributes may legally cross line boundaries, so a line-local regex can\n    # miss `<dialog\\n open>`. An open dialog is an inline/reframing violation\n    # when its opener shares its source line with governed prose on either\n    # side. A clean whole-section wrapper remains supported even when the\n    # opener itself is formatted across multiple lines.\n    for open_dialog_match in open_dialog_tag.finditer(live_markup):\n        line_start = live_markup.rfind("\\n", 0, open_dialog_match.start()) + 1\n        line_end = live_markup.find("\\n", open_dialog_match.end())\n        if line_end < 0:\n            line_end = len(live_markup)\n        prefix = live_markup[line_start:open_dialog_match.start()]\n        suffix = live_markup[open_dialog_match.end():line_end]\n        if prefix.strip() or suffix.strip():\n            parser.violations.add("dialog-inline-block")\n            break\n\n''',
    '''''',
    "remove dialog regex tokenizer",
)

POLICING.write_text(text, encoding="utf-8")

regressions = REGRESSIONS.read_text(encoding="utf-8")
addition = r'''


def test_multiline_open_dialog_with_quoted_gt_is_rejected() -> None:
    fragment = (
        'Availability through ABC iview is <dialog data-x="a>b"\n'
        ' open>not</dialog> permission to redistribute content.'
    )
    assert "dialog-inline-block" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    original = "Availability through ABC iview is not permission to redistribute content."
    mutated = corpus.replace(original, fragment, 1)
    with pytest.raises(AssertionError, match="dialog block-container HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_multiline_dialog_wrapper_with_quoted_gt_remains_supported() -> None:
    fragment = '<dialog data-x="a>b"\n open>\nCanonical governed prose.\n</dialog>\n'
    violations = POLICING["_governed_surface_html_violations"](fragment)
    assert "dialog-inline-block" not in violations


def test_aria_disabled_ancestor_is_rejected_on_governed_source() -> None:
    fragment = '<span aria-disabled="true">https://iview.abc.net.au/show/black-comedy</span>'
    assert "accessibility-disabled" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    mutated = corpus.replace(url, fragment, 1)
    with pytest.raises(AssertionError, match="aria-disabled"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_ruby_annotation_cannot_relocate_governed_qualifier() -> None:
    fragment = (
        "Availability through ABC iview is "
        "<ruby>not<rt> permission</rt></ruby> to redistribute content."
    )
    assert "non-rendering-container" in POLICING["_governed_surface_html_violations"](fragment)
    corpus = CORPUS.read_text(encoding="utf-8")
    original = "Availability through ABC iview is not permission to redistribute content."
    mutated = corpus.replace(original, fragment, 1)
    with pytest.raises(AssertionError, match="non-rendering"):
        REGISTRY["_validate_registry_corpus"](mutated)
'''
if "test_multiline_open_dialog_with_quoted_gt_is_rejected" in regressions:
    raise SystemExit("fresh regression block already exists")
REGRESSIONS.write_text(regressions.rstrip() + addition + "\n", encoding="utf-8")
