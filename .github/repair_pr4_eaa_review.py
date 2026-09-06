from pathlib import Path


path = Path("tests/test_research_reference_registry.py")
text = path.read_text(encoding="utf-8")

hidden_old = '''        if "hidden" in values:
            return True
        return _css_hides_element(values.get("style", ""))
'''
hidden_new = '''        if "hidden" in values:
            return True
        # HTML popovers are not rendered in their resting state. Governance
        # text must be visible without a user activation step.
        if "popover" in values:
            return True
        return _css_hides_element(values.get("style", ""))
'''
if text.count(hidden_old) != 1:
    raise SystemExit("could not uniquely patch popover visibility")
text = text.replace(hidden_old, hidden_new, 1)

class_marker = "\n\nclass _VisibleHTMLTextParser(HTMLParser):\n"
if text.count(class_marker) != 1:
    raise SystemExit("could not uniquely locate visible HTML parser")
raw_html_helper = r'''
RAW_HTML_LITERAL_ASTERISK = "\uE003"


def _protect_unpaired_raw_html_asterisks(data: str) -> str:
    """Protect literal raw-HTML asterisks that are not paired emphasis runs."""
    assert RAW_HTML_LITERAL_ASTERISK not in data
    runs: list[tuple[int, int]] = []
    position = 0
    while position < len(data):
        if data[position] != "*":
            position += 1
            continue
        end = position + 1
        while end < len(data) and data[end] == "*":
            end += 1
        runs.append((position, end))
        position = end

    paired_indexes: set[int] = set()
    pending_by_length: dict[int, list[tuple[int, int]]] = {}
    for start, end in runs:
        length = end - start
        pending = pending_by_length.setdefault(length, [])
        if pending:
            open_start, open_end = pending.pop()
            paired_indexes.update(range(open_start, open_end))
            paired_indexes.update(range(start, end))
        else:
            pending.append((start, end))

    if not runs:
        return data
    characters = list(data)
    for index, character in enumerate(characters):
        if character == "*" and index not in paired_indexes:
            characters[index] = RAW_HTML_LITERAL_ASTERISK
    return "".join(characters)
'''
text = text.replace(class_marker, "\n\n" + raw_html_helper + class_marker.lstrip("\n"), 1)

init_old = '''    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hrefs: list[str] = []
        self.stack: list[tuple[str, bool, bool]] = []
        self.open_anchors: list[tuple[int, str, int]] = []
'''
init_new = '''    def __init__(
        self,
        *,
        protect_raw_html_literal_asterisks: bool = False,
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hrefs: list[str] = []
        self.stack: list[tuple[str, bool, bool]] = []
        self.open_anchors: list[tuple[int, str, int]] = []
        self.protect_raw_html_literal_asterisks = protect_raw_html_literal_asterisks
'''
if text.count(init_old) != 1:
    raise SystemExit("could not uniquely patch visible HTML parser init")
text = text.replace(init_old, init_new, 1)

data_old = '''    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)
'''
data_new = '''    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            if self.protect_raw_html_literal_asterisks and self.stack:
                data = _protect_unpaired_raw_html_asterisks(data)
            self.parts.append(data)
'''
if text.count(data_old) != 1:
    raise SystemExit("could not uniquely patch raw HTML data handling")
text = text.replace(data_old, data_new, 1)

visible_html_old = '''def _visible_html_text(text: str) -> str:
    parser = _VisibleHTMLTextParser()
'''
visible_html_new = '''def _visible_html_text(
    text: str,
    *,
    protect_raw_html_literal_asterisks: bool = False,
) -> str:
    parser = _VisibleHTMLTextParser(
        protect_raw_html_literal_asterisks=protect_raw_html_literal_asterisks,
    )
'''
if text.count(visible_html_old) != 1:
    raise SystemExit("could not uniquely patch visible HTML text wrapper")
text = text.replace(visible_html_old, visible_html_new, 1)

inline_old = '''    visible = _visible_html_text(visible)
    visible = _strip_emphasis_preserving_intraword_underscores(visible)
    visible = _restore_entity_decoded_emphasis_punctuation(visible)
    return " ".join(visible.split())
'''
inline_new = '''    visible = _visible_html_text(
        visible,
        protect_raw_html_literal_asterisks=True,
    )
    visible = _strip_emphasis_preserving_intraword_underscores(visible)
    visible = _restore_entity_decoded_emphasis_punctuation(visible)
    visible = visible.replace(RAW_HTML_LITERAL_ASTERISK, "*")
    return " ".join(visible.split())
'''
if text.count(inline_old) != 1:
    raise SystemExit("could not uniquely patch inline integrity reducer")
text = text.replace(inline_old, inline_new, 1)

test_name = "def test_eaa_review_raw_html_literal_asterisk_and_popover_visibility():"
if test_name in text:
    raise SystemExit("latest eaa review regression unexpectedly already present")
new_test = r'''


def test_eaa_review_raw_html_literal_asterisk_and_popover_visibility():
    # A literal asterisk emitted by a raw-HTML text node is not a Markdown
    # emphasis delimiter and must remain reader-visible integrity text.
    assert _visible_inline_text("The art<span>*</span>icle") == "The art*icle"

    # Popover content is hidden until explicit activation, so it cannot supply a
    # governance clause that is required to be visible by default.
    assert _visible_inline_text("<span popover>The article</span>") == ""

    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(
        heading
        for heading in EXPECTED_GOVERNED_ENTRIES
        if heading.startswith("### Chey (2021)")
    )
    section = _registered_sections(corpus)[entry]
    rights = str(ENTRY_CONTRACTS[entry][RIGHTS_FIELD])
    assert "article" in rights
    assert rights in section

    raw_html_corruption = rights.replace("article", "art<span>*</span>icle", 1)
    mutated_section = section.replace(rights, raw_html_corruption, 1)
    with pytest.raises(AssertionError):
        _validate_registry_corpus(corpus.replace(section, mutated_section, 1))

    popover_hidden = rights.replace("article", "<span popover>article</span>", 1)
    mutated_section = section.replace(rights, popover_hidden, 1)
    with pytest.raises(AssertionError):
        _validate_registry_corpus(corpus.replace(section, mutated_section, 1))
'''
text = text.rstrip() + new_test + "\n"
path.write_text(text, encoding="utf-8")
