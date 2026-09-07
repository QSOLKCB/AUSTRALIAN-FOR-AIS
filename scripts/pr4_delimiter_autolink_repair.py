from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
POLICING = ROOT / "tests/test_policing_context_roadmap.py"
REGISTRY = ROOT / "tests/test_research_reference_registry.py"
ROADMAP = ROOT / "ROADMAP.md"
CORPUS = ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected exactly one match, found {count}"
    return text.replace(old, new, 1)


def reproduce_before_repair() -> None:
    policing = runpy.run_path(str(POLICING))
    registry = runpy.run_path(str(REGISTRY))
    roadmap = ROADMAP.read_text(encoding="utf-8")
    corpus = CORPUS.read_text(encoding="utf-8")

    # Fresh Codex evidence: the current validators incorrectly accept all three.
    surplus = roadmap.replace(
        "not legal advice",
        "***not legal advice**",
        1,
    )
    policing["_validate_policing_workstream"](surplus)

    unmatched = corpus.replace(
        "The article is registered as scholarship",
        "*The article is registered as scholarship",
        1,
    )
    registry["_validate_registry_corpus"](unmatched)

    email = "<current.sources.may.be.skipped@example.com>"
    email_roadmap = roadmap.replace(
        "not legal advice.",
        f"not legal advice. {email}",
        1,
    )
    policing["_validate_policing_workstream"](email_roadmap)
    email_corpus = corpus.replace(
        "The article is registered as scholarship",
        f"The article is registered as scholarship {email}",
        1,
    )
    registry["_validate_registry_corpus"](email_corpus)


COMMON_DELIMITER_FUNCTION = r'''def _protect_unmatched_markdown_emphasis_delimiters(text: str) -> str:
    """Protect literal emphasis characters, including surplus characters in matched runs."""
    assert UNMATCHED_MARKDOWN_ASTERISK not in text
    assert UNMATCHED_MARKDOWN_UNDERSCORE not in text

    runs: list[dict[str, object]] = []
    position = 0
    while position < len(text):
        marker = text[position]
        if marker not in {"*", "_"}:
            position += 1
            continue
        end = position + 1
        while end < len(text) and text[end] == marker:
            end += 1
        previous = text[position - 1] if position else None
        following = text[end] if end < len(text) else None
        previous_whitespace = previous is None or previous.isspace()
        following_whitespace = following is None or following.isspace()
        previous_punctuation = previous is not None and previous in string.punctuation
        following_punctuation = following is not None and following in string.punctuation
        left_flanking = (
            not following_whitespace
            and (not following_punctuation or previous_whitespace or previous_punctuation)
        )
        right_flanking = (
            not previous_whitespace
            and (not previous_punctuation or following_whitespace or following_punctuation)
        )
        if marker == "_":
            can_open = left_flanking and (not right_flanking or previous_punctuation)
            can_close = right_flanking and (not left_flanking or following_punctuation)
        else:
            can_open = left_flanking
            can_close = right_flanking
        runs.append({
            "start": position,
            "end": end,
            "marker": marker,
            "can_open": can_open,
            "can_close": can_close,
            "open_consumed": 0,
            "close_consumed": 0,
        })
        position = end

    openers: dict[str, list[int]] = {"*": [], "_": []}
    for index, run in enumerate(runs):
        marker = str(run["marker"])
        if bool(run["can_close"]):
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
        run_length = int(run["end"]) - int(run["start"])
        remaining = (
            run_length
            - int(run["open_consumed"])
            - int(run["close_consumed"])
        )
        if bool(run["can_open"]) and remaining > 0:
            openers[marker].append(index)

    if not runs:
        return text
    characters = list(text)
    for run in runs:
        start = int(run["start"]) + int(run["close_consumed"])
        end = int(run["end"]) - int(run["open_consumed"])
        if start >= end:
            continue
        # Preserve an unmatched candidate run, or the literal surplus left
        # after CommonMark consumes only part of a matched delimiter run.
        if not (
            bool(run["can_open"])
            or bool(run["can_close"])
            or int(run["open_consumed"])
            or int(run["close_consumed"])
        ):
            continue
        sentinel = (
            UNMATCHED_MARKDOWN_ASTERISK
            if run["marker"] == "*"
            else UNMATCHED_MARKDOWN_UNDERSCORE
        )
        for character_index in range(start, end):
            characters[character_index] = sentinel
    return "".join(characters)
'''


def patch_policing(text: str) -> str:
    old_autolink = '''AUTOLINK_PATTERN = re.compile(\n    r"<(?P<url>[A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\\x00-\\x20]*)>"\n)\n'''
    new_autolink = old_autolink + '''EMAIL_AUTOLINK_PATTERN = re.compile(\n    r"<(?P<email>[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"\n    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\\.)+"\n    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)>"\n)\n'''
    text = replace_once(text, old_autolink, new_autolink, "shared email autolink pattern")

    start = text.index("def _protect_unmatched_markdown_emphasis_delimiters(text: str) -> str:\n")
    end = text.index("\ndef _restore_unmatched_markdown_emphasis_delimiters", start)
    text = text[:start] + COMMON_DELIMITER_FUNCTION + text[end:]

    old_visible = '''    visible = _replace_inline_markdown_links_for_visibility(visible)\n    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)\n    # HTMLParser(convert_charrefs=True) already performs the browser's one\n'''
    new_visible = '''    visible = _replace_inline_markdown_links_for_visibility(visible)\n    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)\n    visible = EMAIL_AUTOLINK_PATTERN.sub(lambda match: match.group("email"), visible)\n    # HTMLParser(convert_charrefs=True) already performs the browser's one\n'''
    return replace_once(text, old_visible, new_visible, "shared visible email autolink reduction")


REGISTRY_DELIMITER_HELPER = r'''UNMATCHED_MARKDOWN_ASTERISK = "\uE003"
UNMATCHED_MARKDOWN_UNDERSCORE = "\uE004"


def _protect_unmatched_markdown_emphasis_delimiters(text: str) -> str:
    """Protect literal emphasis characters, including surplus characters in matched runs."""
    assert UNMATCHED_MARKDOWN_ASTERISK not in text
    assert UNMATCHED_MARKDOWN_UNDERSCORE not in text

    runs: list[dict[str, object]] = []
    position = 0
    while position < len(text):
        marker = text[position]
        if marker not in {"*", "_"}:
            position += 1
            continue
        end = position + 1
        while end < len(text) and text[end] == marker:
            end += 1
        previous = text[position - 1] if position else None
        following = text[end] if end < len(text) else None
        previous_whitespace = previous is None or previous.isspace()
        following_whitespace = following is None or following.isspace()
        previous_punctuation = previous is not None and previous in string.punctuation
        following_punctuation = following is not None and following in string.punctuation
        left_flanking = (
            not following_whitespace
            and (not following_punctuation or previous_whitespace or previous_punctuation)
        )
        right_flanking = (
            not previous_whitespace
            and (not previous_punctuation or following_whitespace or following_punctuation)
        )
        if marker == "_":
            can_open = left_flanking and (not right_flanking or previous_punctuation)
            can_close = right_flanking and (not left_flanking or following_punctuation)
        else:
            can_open = left_flanking
            can_close = right_flanking
        runs.append({
            "start": position,
            "end": end,
            "marker": marker,
            "can_open": can_open,
            "can_close": can_close,
            "open_consumed": 0,
            "close_consumed": 0,
        })
        position = end

    openers: dict[str, list[int]] = {"*": [], "_": []}
    for index, run in enumerate(runs):
        marker = str(run["marker"])
        if bool(run["can_close"]):
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
        run_length = int(run["end"]) - int(run["start"])
        remaining = (
            run_length
            - int(run["open_consumed"])
            - int(run["close_consumed"])
        )
        if bool(run["can_open"]) and remaining > 0:
            openers[marker].append(index)

    if not runs:
        return text
    characters = list(text)
    for run in runs:
        start = int(run["start"]) + int(run["close_consumed"])
        end = int(run["end"]) - int(run["open_consumed"])
        if start >= end:
            continue
        if not (
            bool(run["can_open"])
            or bool(run["can_close"])
            or int(run["open_consumed"])
            or int(run["close_consumed"])
        ):
            continue
        sentinel = (
            UNMATCHED_MARKDOWN_ASTERISK
            if run["marker"] == "*"
            else UNMATCHED_MARKDOWN_UNDERSCORE
        )
        for character_index in range(start, end):
            characters[character_index] = sentinel
    return "".join(characters)


def _restore_unmatched_markdown_emphasis_delimiters(text: str) -> str:
    return text.replace(UNMATCHED_MARKDOWN_ASTERISK, "*").replace(
        UNMATCHED_MARKDOWN_UNDERSCORE, "_"
    )


'''


def patch_registry(text: str) -> str:
    old_autolink = 'AUTOLINK_PATTERN = re.compile(r"<(?P<url>https?://[^>\\s]+)>")\n'
    new_autolink = old_autolink + '''EMAIL_AUTOLINK_PATTERN = re.compile(\n    r"<(?P<email>[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"\n    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\\.)+"\n    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)>"\n)\n'''
    text = replace_once(text, old_autolink, new_autolink, "registry email autolink pattern")

    marker = "OBFUSCATED_INTRAW_WORD_PATTERN = re.compile(\n"
    assert "UNMATCHED_MARKDOWN_ASTERISK = \"\\uE003\"" not in text
    text = replace_once(text, marker, REGISTRY_DELIMITER_HELPER + marker, "registry delimiter helper")

    old_visible = '''    visible = _replace_inline_markdown_links_with_labels(visible)\n    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)\n    # CommonMark decides emphasis delimiters before character references become\n'''
    new_visible = '''    visible = _replace_inline_markdown_links_with_labels(visible)\n    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)\n    visible = EMAIL_AUTOLINK_PATTERN.sub(lambda match: match.group("email"), visible)\n    # CommonMark decides emphasis delimiters before character references become\n'''
    text = replace_once(text, old_visible, new_visible, "registry visible email autolink reduction")

    old_protect = '''    visible = _protect_entity_decoded_emphasis_punctuation(visible)\n    # HTMLParser(convert_charrefs=True) performs the browser's one character-\n'''
    new_protect = '''    visible = _protect_entity_decoded_emphasis_punctuation(visible)\n    visible = _protect_unmatched_markdown_emphasis_delimiters(visible)\n    # HTMLParser(convert_charrefs=True) performs the browser's one character-\n'''
    text = replace_once(text, old_protect, new_protect, "registry delimiter protection call")

    old_restore = '''    visible = _strip_emphasis_preserving_intraword_underscores(visible)\n    visible = _restore_entity_decoded_emphasis_punctuation(visible)\n    visible = visible.replace(RAW_HTML_LITERAL_ASTERISK, "*")\n'''
    new_restore = '''    visible = _strip_emphasis_preserving_intraword_underscores(visible)\n    visible = _restore_entity_decoded_emphasis_punctuation(visible)\n    visible = _restore_unmatched_markdown_emphasis_delimiters(visible)\n    visible = visible.replace(RAW_HTML_LITERAL_ASTERISK, "*")\n'''
    text = replace_once(text, old_restore, new_restore, "registry delimiter restoration call")

    old_source_start = '''    structure = _mask_hidden_html_regions(_structural_registry_text(text))\n    definition_source = text if reference_scope is None else reference_scope\n'''
    new_source_start = '''    structure = _mask_hidden_html_regions(_structural_registry_text(text))\n    email_autolinks = tuple(EMAIL_AUTOLINK_PATTERN.finditer(structure))\n    assert not email_autolinks, (\n        "registered-source email autolinks are not usable HTTPS provenance: "\n        + ", ".join(match.group("email") for match in email_autolinks)\n    )\n    definition_source = text if reference_scope is None else reference_scope\n'''
    return replace_once(text, old_source_start, new_source_start, "registry source email autolink rejection")


def write_regressions() -> None:
    test_path = ROOT / "tests/test_pr4_delimiter_autolink_regressions.py"
    assert not test_path.exists(), f"unexpected existing regression file: {test_path}"
    test_path.write_text(
        '''from pathlib import Path\nimport runpy\n\nimport pytest\n\nROOT = Path(__file__).resolve().parents[1]\nPOLICING = runpy.run_path(str(ROOT / "tests/test_policing_context_roadmap.py"))\nREGISTRY = runpy.run_path(str(ROOT / "tests/test_research_reference_registry.py"))\n\n\ndef test_shared_surplus_delimiter_characters_remain_visible():\n    assert POLICING["_visible_text"]("***not legal advice**") == "*not legal advice"\n    assert POLICING["_visible_text"]("**not legal advice***") == "not legal advice*"\n    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")\n    mutated = roadmap.replace("not legal advice", "***not legal advice**", 1)\n    with pytest.raises(AssertionError):\n        POLICING["_validate_policing_workstream"](mutated)\n\n\ndef test_registry_unmatched_delimiter_remains_visible_and_breaks_receipt():\n    phrase = "The article is registered as scholarship"\n    assert REGISTRY["_visible_inline_text"]("*" + phrase) == "*" + phrase\n    corpus = (ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")\n    mutated = corpus.replace(phrase, "*" + phrase, 1)\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](mutated)\n\n\ndef test_commonmark_email_autolinks_are_visible_governed_content():\n    email_markup = "<current.sources.may.be.skipped@example.com>"\n    visible_email = "current.sources.may.be.skipped@example.com"\n    assert POLICING["_visible_text"](email_markup) == visible_email\n    assert REGISTRY["_visible_inline_text"](email_markup) == visible_email\n\n    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")\n    mutated_roadmap = roadmap.replace(\n        "not legal advice.",\n        f"not legal advice. {email_markup}",\n        1,\n    )\n    with pytest.raises(AssertionError):\n        POLICING["_validate_policing_workstream"](mutated_roadmap)\n\n    corpus = (ROOT / "docs/RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")\n    mutated_corpus = corpus.replace(\n        "The article is registered as scholarship",\n        f"The article is registered as scholarship {email_markup}",\n        1,\n    )\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](mutated_corpus)\n\n\ndef test_registered_source_email_autolink_is_not_https_provenance():\n    with pytest.raises(AssertionError, match="email autolinks"):\n        REGISTRY["_usable_https_source_bindings"](\n            "**Registered source:** <source@example.com>"\n        )\n''',
        encoding="utf-8",
    )


def main() -> None:
    reproduce_before_repair()
    policing = POLICING.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")
    POLICING.write_text(patch_policing(policing), encoding="utf-8")
    REGISTRY.write_text(patch_registry(registry), encoding="utf-8")
    write_regressions()


if __name__ == "__main__":
    main()
