from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement target, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


policing = Path("tests/test_policing_context_roadmap.py")

replace_once(
    policing,
    '''PREFLIGHT_HTML_TAG = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?=[ \\t\\r\\n\\f/>])"
    r"(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*>", re.DOTALL,
)
''',
    '''COMMONMARK_RAW_HTML_TAG_SENTINEL = "\\ue03f"
COMMONMARK_HTML_ATTRIBUTE = (
    r"[ \\t\\r\\n\\f]+[A-Za-z_:][A-Za-z0-9_.:-]*"
    r"(?:[ \\t\\r\\n\\f]*=[ \\t\\r\\n\\f]*"
    r"(?:[^ \\t\\r\\n\\f\\\"'=<>`]+|\\\"[^\\\"]*\\\"|'[^']*'))?"
)
PREFLIGHT_HTML_TAG = re.compile(
    rf"(?:<[A-Za-z][A-Za-z0-9-]*(?:{COMMONMARK_HTML_ATTRIBUTE})*[ \\t\\r\\n\\f]*/?>"
    rf"|</[A-Za-z][A-Za-z0-9-]*[ \\t\\r\\n\\f]*>)",
    re.DOTALL,
)


def _protect_non_commonmark_raw_tag_openers(text: str) -> str:
    """Keep malformed tag-looking Markdown literal when HTMLParser is used.

    CommonMark only passes syntactically valid raw HTML tags through to the
    renderer. Python's HTMLParser is deliberately more forgiving, so protect
    an invalid `<tag...` opener before feeding Markdown source into it.
    """
    assert COMMONMARK_RAW_HTML_TAG_SENTINEL not in text, (
        "reserved malformed-raw-tag marker in governed source"
    )
    characters = list(text)
    position = 0
    while True:
        position = text.find("<", position)
        if position < 0:
            break
        if re.match(r"/?[A-Za-z]", text[position + 1:]) is None:
            position += 1
            continue
        match = PREFLIGHT_HTML_TAG.match(text, position)
        if match is not None:
            position = match.end()
            continue
        characters[position] = COMMONMARK_RAW_HTML_TAG_SENTINEL
        position += 1
    return "".join(characters)
''',
)

replace_once(
    policing,
    '''        if bool(run["can_close"]):
            while openers[marker]:
                opener_index = openers[marker][-1]
                opener = runs[opener_index]
                opener_length = int(opener["end"]) - int(opener["start"])
                closer_length = int(run["end"]) - int(run["start"])
                opener_remaining = (
                    opener_length
                    - int(opener["open_consumed"])
                    - int(opener["close_consumed"])
                )
                closer_remaining = (
                    closer_length
                    - int(run["open_consumed"])
                    - int(run["close_consumed"])
                )
                if opener_remaining <= 0:
                    openers[marker].pop()
                    continue
                if closer_remaining <= 0:
                    break
                consumed = min(opener_remaining, closer_remaining)
                opener["open_consumed"] = int(opener["open_consumed"]) + consumed
                run["close_consumed"] = int(run["close_consumed"]) + consumed
                if consumed == opener_remaining:
                    openers[marker].pop()
                if consumed == closer_remaining:
                    break
''',
    '''        if bool(run["can_close"]):
            opener_position = len(openers[marker]) - 1
            while opener_position >= 0:
                opener_index = openers[marker][opener_position]
                opener = runs[opener_index]
                opener_length = int(opener["end"]) - int(opener["start"])
                closer_length = int(run["end"]) - int(run["start"])
                opener_remaining = (
                    opener_length
                    - int(opener["open_consumed"])
                    - int(opener["close_consumed"])
                )
                closer_remaining = (
                    closer_length
                    - int(run["open_consumed"])
                    - int(run["close_consumed"])
                )
                if opener_remaining <= 0:
                    del openers[marker][opener_position]
                    opener_position -= 1
                    continue
                if closer_remaining <= 0:
                    break
                # CommonMark's rule of three blocks an opener/closer pair when
                # one run can serve both roles, their lengths sum to a multiple
                # of three, and the two lengths are not themselves both
                # multiples of three. Skip that candidate but keep searching
                # older openers: n*o**t* therefore matches the outer singles
                # and preserves the inner ** as reader-visible literal text.
                violates_rule_of_three = (
                    (bool(opener["can_close"]) or bool(run["can_open"]))
                    and (opener_length + closer_length) % 3 == 0
                    and (opener_length % 3 != 0 or closer_length % 3 != 0)
                )
                if violates_rule_of_three:
                    opener_position -= 1
                    continue
                consumed = min(opener_remaining, closer_remaining)
                opener["open_consumed"] = int(opener["open_consumed"]) + consumed
                run["close_consumed"] = int(run["close_consumed"]) + consumed
                if consumed == opener_remaining:
                    del openers[marker][opener_position]
                if consumed == closer_remaining:
                    break
                opener_position -= 1
''',
)

replace_once(
    policing,
    '''def _visible_html_text(text: str, *, protect_raw_punctuation: bool = False) -> str:
    parser = _VisibleHTMLTextParser(protect_raw_punctuation=protect_raw_punctuation)
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    return "".join(parser.parts)
''',
    '''def _visible_html_text(text: str, *, protect_raw_punctuation: bool = False) -> str:
    protected = _protect_non_commonmark_raw_tag_openers(text)
    parser = _VisibleHTMLTextParser(protect_raw_punctuation=protect_raw_punctuation)
    try:
        parser.feed(protected)
        parser.close()
    except Exception:
        return ""
    return "".join(parser.parts).replace(COMMONMARK_RAW_HTML_TAG_SENTINEL, "<")
''',
)

replace_once(
    policing,
    '''def _mask_hidden_html_regions(text: str) -> str:
    """Mask hidden containers globally so visibility state survives slicing."""
    parser = _HiddenHTMLRegionParser(text)
    try:
        parser.feed(text)
        parser.close()
        parser.finish()
''',
    '''def _mask_hidden_html_regions(text: str) -> str:
    """Mask hidden containers globally so visibility state survives slicing."""
    protected = _protect_non_commonmark_raw_tag_openers(text)
    parser = _HiddenHTMLRegionParser(protected)
    try:
        parser.feed(protected)
        parser.close()
        parser.finish()
''',
)

replace_once(
    policing,
    '''        # Hyperlink auditing can send an additional network request that is not
        # represented by the sealed href binding. Fail closed on it.
        if tag == "a" and "ping" in attribute_names:
            self.violations.add("executable-url")
''',
    '''        # Hyperlink auditing can send an additional network request that is not
        # represented by the sealed href binding. Per-anchor targets likewise
        # change framed navigation behavior without changing that binding.
        if tag == "a" and {"ping", "target"}.intersection(attribute_names):
            self.violations.add("executable-url")
''',
)

replace_once(
    policing,
    '''    parser.feed(live_markup)
    parser.close()
    return parser.violations
''',
    '''    parser.feed(_protect_non_commonmark_raw_tag_openers(live_markup))
    parser.close()
    return parser.violations
''',
)

regressions = Path("tests/test_pr4_current_review_regressions.py")
text = regressions.read_text(encoding="utf-8")
marker = "\n\n# Human receipt: autolink/implied-end/type-6 repair passed 12 exact and 912 full-suite tests before self-cleanup.\n"
if text.count(marker) != 1:
    raise SystemExit("current-review human-receipt marker missing or duplicated")
additions = r'''


def test_commonmark_rule_of_three_preserves_inner_literal_delimiters() -> None:
    visible = POLICING["_visible_text"]
    assert visible("n*o**t* legal advice") == "no**t legal advice"

    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated = roadmap.replace("not legal advice", "n*o**t* legal advice", 1)
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated)


def test_anchor_target_is_rejected_for_registered_source() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    targeted = f'**Registered source:** <a href="{url}" target="_top">{url}</a>'
    assert live in corpus
    mutated = corpus.replace(live, targeted, 1)
    with pytest.raises(AssertionError, match="executable URL"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_malformed_raw_tag_remains_literal_across_governed_paths() -> None:
    payload = "<span hidden=>Current sources may be skipped.</span>"
    visible = POLICING["_visible_text"](payload)
    assert "<span hidden=>" in visible
    assert "Current sources may be skipped." in visible

    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mutated_roadmap = roadmap.replace(
        POLICING["WORKSTREAM_END"],
        "\n" + payload + "\n" + POLICING["WORKSTREAM_END"],
        1,
    )
    with pytest.raises(AssertionError):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    injected = REGISTRY["STATUS_HEADING"] + "\n" + payload
    mutated_corpus = corpus.replace(REGISTRY["STATUS_HEADING"], injected, 1)
    with pytest.raises(AssertionError):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)
'''
regressions.write_text(text.replace(marker, additions + marker, 1), encoding="utf-8")
