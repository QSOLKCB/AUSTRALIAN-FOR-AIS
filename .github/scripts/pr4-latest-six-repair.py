from pathlib import Path

TARGET = Path("tests/test_research_reference_registry.py")
text = TARGET.read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return source.replace(old, new, 1)


old_css = r'''def _css_hides_element(style: str) -> bool:
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
        important = re.search(r"\s*!important\s*$", raw_value) is not None
        value = re.sub(r"\s*!important\s*$", "", raw_value).strip()
        previous = winners.get(name)
        if previous is None or (important and not previous[0]) or important == previous[0]:
            winners[name] = (important, value)

    display = winners.get("display", (False, ""))[1]
    visibility = winners.get("visibility", (False, ""))[1]
    return display == "none" or visibility in {"hidden", "collapse"}
'''
new_css = r'''def _decode_css_escapes(value: str) -> str:
    """Decode CSS escapes without treating escaped punctuation as declaration syntax."""
    parts: list[str] = []
    position = 0
    while position < len(value):
        if value[position] != "\\":
            parts.append(value[position])
            position += 1
            continue

        if position + 1 >= len(value):
            parts.append("\\")
            position += 1
            continue

        next_character = value[position + 1]
        if next_character in "\r\n\f":
            if next_character == "\r" and position + 2 < len(value) and value[position + 2] == "\n":
                position += 3
            else:
                position += 2
            continue

        cursor = position + 1
        while (
            cursor < len(value)
            and cursor - (position + 1) < 6
            and value[cursor] in string.hexdigits
        ):
            cursor += 1
        if cursor > position + 1:
            codepoint = int(value[position + 1:cursor], 16)
            if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
                parts.append("\uFFFD")
            else:
                parts.append(chr(codepoint))
            if cursor < len(value) and value[cursor] in " \t\r\n\f":
                if value[cursor] == "\r" and cursor + 1 < len(value) and value[cursor + 1] == "\n":
                    cursor += 2
                else:
                    cursor += 1
            position = cursor
            continue

        parts.append(next_character)
        position += 2

    return "".join(parts)


def _css_hides_element(style: str) -> bool:
    """Apply inline CSS declaration order, escapes, and !important precedence."""
    cleaned = CSS_COMMENT_PATTERN.sub("", style)
    winners: dict[str, tuple[bool, str]] = {}
    for declaration in cleaned.split(";"):
        if ":" not in declaration:
            continue
        raw_name, raw_value = declaration.split(":", 1)
        name = _decode_css_escapes(raw_name.strip()).casefold()
        if name not in {"display", "visibility"}:
            continue
        decoded_value = _decode_css_escapes(raw_value.strip()).casefold()
        important = re.search(r"\s*!important\s*$", decoded_value) is not None
        value = re.sub(r"\s*!important\s*$", "", decoded_value).strip()
        previous = winners.get(name)
        if previous is None or (important and not previous[0]) or important == previous[0]:
            winners[name] = (important, value)

    display = winners.get("display", (False, ""))[1]
    visibility = winners.get("visibility", (False, ""))[1]
    return display == "none" or visibility in {"hidden", "collapse"}
'''
text = replace_once(text, old_css, new_css, "CSS escape/cascade repair")

text = replace_once(
    text,
    '        if tag in {"script", "style", "template"}:\n            return True\n',
    '        if tag in {"script", "style", "template", "title"}:\n            return True\n',
    "ordinary HTML title visibility",
)

text = replace_once(
    text,
    '        self.stack: list[tuple[str, bool]] = []\n',
    '        self.stack: list[tuple[str, bool, bool]] = []\n',
    "visible HTML stack shape",
)

old_starttag = r'''        inherited = self.stack[-1][1] if self.stack else False
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _ in self.stack)
        )
        hidden = inherited or svg_metadata_hidden or self._is_hidden(tag, attrs)
        if tag == "a" and not hidden:
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.hrefs.append(value)
                    break
        self.stack.append((tag, hidden))
'''
new_starttag = r'''        inherited_hidden = self.stack[-1][1] if self.stack else False
        inherited_inert = self.stack[-1][2] if self.stack else False
        values = {key.lower(): (value or "") for key, value in attrs}
        svg_metadata_hidden = (
            tag in SVG_NON_RENDERING_METADATA_TAGS
            and any(parent_tag == "svg" for parent_tag, _, _ in self.stack)
        )
        hidden = inherited_hidden or svg_metadata_hidden or self._is_hidden(tag, attrs)
        inert = inherited_inert or "inert" in values
        if tag == "a" and not hidden and not inert:
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.hrefs.append(value)
                    break
        self.stack.append((tag, hidden, inert))
'''
text = replace_once(text, old_starttag, new_starttag, "inert-anchor propagation")

text = replace_once(
    text,
    '        parts.append(link.label)\n',
    '        parts.append("" if link.image else link.label)\n',
    "Markdown image alt visibility",
)

old_visible_inline = r'''def _visible_inline_text(text: str) -> str:
    """Reduce Markdown/HTML metadata to browser-visible text only."""
    rendered = _rendered_registry_text(text)
    visible = _mask_link_reference_definitions_for_visibility(rendered)
    visible = _render_inline_code_spans(visible)
    visible = _replace_inline_markdown_links_with_labels(visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = _visible_html_text(visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return " ".join(visible.split())
'''
new_visible_inline = r'''def _strip_emphasis_preserving_intraword_underscores(text: str) -> str:
    """Keep underscore runs that CommonMark renders literally inside words."""
    sentinel = "\uE000"
    assert sentinel not in text
    characters = list(text)
    position = 0
    while position < len(characters):
        if characters[position] != "_":
            position += 1
            continue
        end = position
        while end < len(characters) and characters[end] == "_":
            end += 1
        if (
            position > 0
            and end < len(characters)
            and characters[position - 1].isalnum()
            and characters[end].isalnum()
        ):
            for index in range(position, end):
                characters[index] = sentinel
        position = end

    visible = "".join(characters)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return visible.replace(sentinel, "_")


def _visible_inline_text(text: str) -> str:
    """Reduce Markdown/HTML metadata to browser-visible text only."""
    rendered = _rendered_registry_text(text)
    visible = _mask_link_reference_definitions_for_visibility(rendered)
    visible = _render_inline_code_spans(visible)
    visible = _replace_inline_markdown_links_with_labels(visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    # HTMLParser(convert_charrefs=True) performs the browser's one character-
    # reference decoding pass. Do not decode the resulting text a second time.
    visible = _visible_html_text(visible)
    visible = _strip_emphasis_preserving_intraword_underscores(visible)
    return " ".join(visible.split())
'''
text = replace_once(
    text,
    old_visible_inline,
    new_visible_inline,
    "rendered text one-pass entity / underscore repair",
)

new_tests = r'''

def _chey_section_for_rendering_mutation(corpus: str) -> tuple[str, str]:
    entry = next(
        heading for heading in EXPECTED_GOVERNED_ENTRIES if heading.startswith("### Chey (2021)")
    )
    return entry, _registered_sections(corpus)[entry]


def _mutate_chey_phrase(replacement: str) -> str:
    corpus = CORPUS.read_text(encoding="utf-8")
    _, section = _chey_section_for_rendering_mutation(corpus)
    assert "The article" in section
    mutated_section = section.replace("The article", replacement, 1)
    return corpus.replace(section, mutated_section, 1)


def test_ordinary_html_title_cannot_supply_pinned_visible_clause():
    mutated = _mutate_chey_phrase("<title>The article</title>")
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_css_escape_cannot_hide_pinned_visible_clause():
    mutated = _mutate_chey_phrase(
        '<span style="display:n\\6f ne">The article</span>'
    )
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_inert_registered_anchor_is_not_usable_provenance():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(
        heading for heading in EXPECTED_GOVERNED_ENTRIES if heading.startswith("### Hurley (2025)")
    )
    section = _registered_sections(corpus)[entry]
    source = str(ENTRY_CONTRACTS[entry][SOURCES_KEY][0])
    original = f"**Registered source:** {source}"
    replacement = (
        f'**Registered source:** <span inert><a href="{source}">{source}</a></span>'
    )
    assert original in section
    mutated_section = section.replace(original, replacement, 1)
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _validate_registry_corpus(mutated)


def test_markdown_image_alt_text_cannot_supply_pinned_visible_clause():
    mutated = _mutate_chey_phrase(
        "![The article](https://example.com/rendered-rights.png)"
    )
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_intraword_underscores_remain_literal_in_integrity_text():
    mutated = _mutate_chey_phrase("T_h_e_ a_r_t_i_c_l_e_")
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)


def test_character_references_are_decoded_once_for_integrity():
    mutated = _mutate_chey_phrase("&amp;#84;he article")
    with pytest.raises(AssertionError):
        _validate_registry_corpus(mutated)
'''

if "test_ordinary_html_title_cannot_supply_pinned_visible_clause" in text:
    raise SystemExit("six-gremlin regressions already present")
text = text.rstrip() + new_tests + "\n"
TARGET.write_text(text, encoding="utf-8")
