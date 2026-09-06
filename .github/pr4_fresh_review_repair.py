from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: str, marker: str, addition: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if marker in text:
        raise SystemExit(f"{path}: regression marker already exists: {marker}")
    target.write_text(text.rstrip() + "\n\n" + addition.strip() + "\n", encoding="utf-8")


POLICING = "tests/test_policing_context_roadmap.py"
WORKSTREAM_H = "tests/test_workstream_h_methodology.py"

# Shared browser-visible reducer: ordinary HTML <title> is metadata, not body text.
replace_once(
    POLICING,
    '        if tag in {"script", "style", "template"}:\n            return True',
    '        if tag in {"script", "style", "template", "title"}:\n            return True',
)

# Match browser duplicate-attribute handling: the first attribute wins.
replace_once(
    POLICING,
    '        values = {key.lower(): (value or "") for key, value in attrs}\n',
    '        values: dict[str, str] = {}\n'
    '        for key, value in attrs:\n'
    '            values.setdefault(key.lower(), value or "")\n',
)

# HTMLParser callbacks are adjacent inline text nodes unless markup itself creates spacing.
replace_once(
    POLICING,
    '    return " ".join(parser.parts)\n',
    '    return "".join(parser.parts)\n',
)

# Fail closed on interactive form controls on sealed roadmap/methodology surfaces.
replace_once(
    POLICING,
    'RAW_HTML_CDATA = "__cdata__"\n',
    'RAW_HTML_CDATA = "__cdata__"\n'
    'INTERACTIVE_FORM_CONTROL_PATTERN = re.compile(\n'
    '    r"<\\s*(?:form|input|button|select|textarea|option|optgroup)\\b",\n'
    '    flags=re.IGNORECASE,\n'
    ')\n',
)
replace_once(
    POLICING,
    'def _visible_text(markdown: str) -> str:\n'
    '    """Return browser-visible text without hidden HTML or link metadata."""\n'
    '    visible = _mask_link_reference_definitions_for_visibility(markdown)\n',
    'def _visible_text(markdown: str) -> str:\n'
    '    """Return browser-visible text without hidden HTML or link metadata."""\n'
    '    assert INTERACTIVE_FORM_CONTROL_PATTERN.search(markdown) is None, (\n'
    '        "interactive form control HTML is not allowed on governed methodology surfaces"\n'
    '    )\n'
    '    visible = _mask_link_reference_definitions_for_visibility(markdown)\n',
)

# Keep Workstream H's local fallback parser aligned with the shared browser semantics.
replace_once(
    WORKSTREAM_H,
    '        if tag in {"script", "style", "template"}:\n            return True',
    '        if tag in {"script", "style", "template", "title"}:\n            return True',
)
replace_once(
    WORKSTREAM_H,
    '        values = {key.lower(): (value or "") for key, value in attrs}\n',
    '        values: dict[str, str] = {}\n'
    '        for key, value in attrs:\n'
    '            values.setdefault(key.lower(), value or "")\n',
)
replace_once(
    WORKSTREAM_H,
    '    return " ".join(parser.parts)\n',
    '    return "".join(parser.parts)\n',
)

# Pin Workstream H citations as rendered label/destination pairs, not independent sets.
replace_once(
    WORKSTREAM_H,
    'WORKSTREAM_H_CITATION_DESTINATIONS = frozenset({\n'
    '    "https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary",\n'
    '    "https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/",\n'
    '    "https://www.defence.gov.au/news-events/news/2022-09-08/communication-key-combined-exercise",\n'
    '    "https://www.defence.gov.au/news-events/news/2026-06-11/partner-nations-rehearse-war",\n'
    '    "https://www.awm.gov.au/collection/LIB100000077",\n'
    '})\n',
    'WORKSTREAM_H_CITATION_LINKS = frozenset({\n'
    '    ("Australian slang dictionary", "https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary"),\n'
    '    ("Best Aussie slang", "https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/"),\n'
    '    ("Communication key on combined exercise", "https://www.defence.gov.au/news-events/news/2022-09-08/communication-key-combined-exercise"),\n'
    '    ("Partner nations rehearse for war", "https://www.defence.gov.au/news-events/news/2026-06-11/partner-nations-rehearse-war"),\n'
    '    ("Welcome to Australia", "https://www.awm.gov.au/collection/LIB100000077"),\n'
    '})\n'
    'WORKSTREAM_H_CITATION_DESTINATIONS = frozenset(\n'
    '    destination for _, destination in WORKSTREAM_H_CITATION_LINKS\n'
    ')\n',
)

old_link_function = '''def _inline_markdown_link_destinations(text: str) -> tuple[str, ...]:
    """Return non-image inline-link destinations from a rendered section source."""
    destinations: list[str] = []
    cursor = 0
    while cursor < len(text):
        bracket = text.find("[", cursor)
        if bracket < 0:
            break
        if _is_escaped_markdown_character(text, bracket):
            cursor = bracket + 1
            continue
        label_end = _balanced_markdown_label_end(text, bracket)
        if label_end is None or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            cursor = bracket + 1
            continue
        paren_start = label_end + 1
        paren_end = _inline_link_closing_paren(text, paren_start)
        if paren_end is None:
            cursor = label_end + 1
            continue
        destination = _inline_link_destination(text[paren_start + 1:paren_end])
        if destination is None:
            cursor = paren_end + 1
            continue
        image = (
            bracket > 0
            and text[bracket - 1] == "!"
            and not _is_escaped_markdown_character(text, bracket - 1)
        )
        if not image:
            destinations.append(html.unescape(destination.strip("<>")))
        cursor = paren_end + 1
    return tuple(destinations)
'''
new_link_function = '''def _inline_markdown_links(text: str) -> tuple[tuple[str, str], ...]:
    """Return rendered non-image inline-link label/destination pairs."""
    links: list[tuple[str, str]] = []
    cursor = 0
    while cursor < len(text):
        bracket = text.find("[", cursor)
        if bracket < 0:
            break
        if _is_escaped_markdown_character(text, bracket):
            cursor = bracket + 1
            continue
        label_end = _balanced_markdown_label_end(text, bracket)
        if label_end is None or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            cursor = bracket + 1
            continue
        paren_start = label_end + 1
        paren_end = _inline_link_closing_paren(text, paren_start)
        if paren_end is None:
            cursor = label_end + 1
            continue
        destination = _inline_link_destination(text[paren_start + 1:paren_end])
        if destination is None:
            cursor = paren_end + 1
            continue
        image = (
            bracket > 0
            and text[bracket - 1] == "!"
            and not _is_escaped_markdown_character(text, bracket - 1)
        )
        if not image:
            label = html.unescape(text[bracket + 1:label_end]).strip()
            links.append((label, html.unescape(destination.strip("<>"))))
        cursor = paren_end + 1
    return tuple(links)


def _inline_markdown_link_destinations(text: str) -> tuple[str, ...]:
    """Return non-image inline-link destinations from a rendered section source."""
    return tuple(destination for _, destination in _inline_markdown_links(text))
'''
replace_once(WORKSTREAM_H, old_link_function, new_link_function)

replace_once(
    WORKSTREAM_H,
    '    raw_section = _workstream_h_raw(text)\n'
    '    actual_destinations = set(_inline_markdown_link_destinations(raw_section))\n'
    '    assert actual_destinations == WORKSTREAM_H_CITATION_DESTINATIONS, (\n'
    '        "Workstream H citation destinations changed: expected "\n'
    '        f"{sorted(WORKSTREAM_H_CITATION_DESTINATIONS)!r}, got "\n'
    '        f"{sorted(actual_destinations)!r}"\n'
    '    )\n',
    '    raw_section = _workstream_h_raw(text)\n'
    '    actual_links = set(_inline_markdown_links(raw_section))\n'
    '    actual_destinations = {destination for _, destination in actual_links}\n'
    '    assert actual_destinations == WORKSTREAM_H_CITATION_DESTINATIONS, (\n'
    '        "Workstream H citation destinations changed: expected "\n'
    '        f"{sorted(WORKSTREAM_H_CITATION_DESTINATIONS)!r}, got "\n'
    '        f"{sorted(actual_destinations)!r}"\n'
    '    )\n'
    '    assert actual_links == WORKSTREAM_H_CITATION_LINKS, (\n'
    '        "Workstream H citation label/destination bindings changed: expected "\n'
    '        f"{sorted(WORKSTREAM_H_CITATION_LINKS)!r}, got {sorted(actual_links)!r}"\n'
    '    )\n',
)

append_once(
    POLICING,
    "test_fresh_review_inline_html_adjacency_is_preserved",
    r'''
def test_fresh_review_inline_html_adjacency_is_preserved():
    assert _visible_text("Every<span></span>implemented") == "Everyimplemented"

    roadmap = ROADMAP.read_text(encoding="utf-8")
    sentence = REQUIRED_CLAUSES[3]
    assert sentence in roadmap
    mutated = roadmap.replace(
        sentence,
        sentence.replace("Every implemented", "Every<span></span>implemented", 1),
        1,
    )
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)


def test_fresh_review_duplicate_html_attribute_preserves_first_value():
    sentence = REQUIRED_CLAUSES[3]
    hidden = f'<span style="display:none" style="display:inline">{sentence}</span>'
    assert sentence not in _visible_text(hidden)

    roadmap = ROADMAP.read_text(encoding="utf-8")
    assert sentence in roadmap
    mutated = roadmap.replace(sentence, hidden, 1)
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)


def test_fresh_review_interactive_form_control_is_rejected():
    with pytest.raises(AssertionError, match="interactive form control HTML"):
        _visible_text('<input value="Current sources may be skipped.">')

    roadmap = ROADMAP.read_text(encoding="utf-8")
    end = roadmap.index(WORKSTREAM_END, roadmap.index(WORKSTREAM_HEADING))
    mutated = roadmap[:end] + '\n<input value="Current sources may be skipped.">\n' + roadmap[end:]
    with pytest.raises(AssertionError, match="interactive form control HTML"):
        _validate_policing_workstream(mutated)


def test_fresh_review_html_title_is_non_rendering():
    sentence = REQUIRED_CLAUSES[3]
    assert _visible_text(f"<title>{sentence}</title>") == ""

    roadmap = ROADMAP.read_text(encoding="utf-8")
    assert sentence in roadmap
    mutated = roadmap.replace(sentence, f"<title>{sentence}</title>", 1)
    with pytest.raises(AssertionError):
        _validate_policing_workstream(mutated)
''',
)

append_once(
    WORKSTREAM_H,
    "test_fresh_review_workstream_h_binds_citation_labels_to_destinations",
    r'''
def test_fresh_review_workstream_h_binds_citation_labels_to_destinations():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    vu_url = "https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary"
    reddit_url = "https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/"
    vu_link = f"[Australian slang dictionary]({vu_url})"
    reddit_link = f"[Best Aussie slang]({reddit_url})"
    assert vu_link in roadmap
    assert reddit_link in roadmap
    mutated = roadmap.replace(
        vu_link,
        f"[Australian slang dictionary]({reddit_url})",
        1,
    ).replace(
        reddit_link,
        f"[Best Aussie slang]({vu_url})",
        1,
    )
    with pytest.raises(AssertionError, match="citation label/destination bindings changed"):
        _assert_workstream_h_integrity(mutated)
''',
)
