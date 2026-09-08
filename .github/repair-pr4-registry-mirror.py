from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement target, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


registry = Path("tests/test_research_reference_registry.py")
replace_once(
    registry,
    '''_SHARED_HTML_PREFLIGHT = _SHARED_POLICING["_governed_surface_html_violations"]
''',
    '''_SHARED_HTML_PREFLIGHT = _SHARED_POLICING["_governed_surface_html_violations"]
_SHARED_PROTECT_NON_COMMONMARK_RAW_TAG_OPENERS = _SHARED_POLICING[
    "_protect_non_commonmark_raw_tag_openers"
]
_SHARED_RAW_TAG_SENTINEL = _SHARED_POLICING["COMMONMARK_RAW_HTML_TAG_SENTINEL"]
''',
)

rule3_old = '''        if bool(run["can_close"]):
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
'''
rule3_new = '''        if bool(run["can_close"]):
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
'''
replace_once(registry, rule3_old, rule3_new)

replace_once(
    registry,
    '''def _visible_html_text(
    text: str,
    *,
    protect_raw_html_literal_asterisks: bool = False,
) -> str:
    parser = _VisibleHTMLTextParser(
        protect_raw_html_literal_asterisks=protect_raw_html_literal_asterisks,
    )
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    # HTML inline elements do not manufacture whitespace between adjacent text
    # nodes. Preserve the source/browser adjacency here; the final visible-text
    # normalizer collapses whitespace that was actually rendered by the source.
    return "".join(parser.parts)
''',
    '''def _visible_html_text(
    text: str,
    *,
    protect_raw_html_literal_asterisks: bool = False,
) -> str:
    protected = _SHARED_PROTECT_NON_COMMONMARK_RAW_TAG_OPENERS(text)
    parser = _VisibleHTMLTextParser(
        protect_raw_html_literal_asterisks=protect_raw_html_literal_asterisks,
    )
    try:
        parser.feed(protected)
        parser.close()
    except Exception:
        return ""
    # HTML inline elements do not manufacture whitespace between adjacent text
    # nodes. Preserve the source/browser adjacency here; the final visible-text
    # normalizer collapses whitespace that was actually rendered by the source.
    return "".join(parser.parts).replace(_SHARED_RAW_TAG_SENTINEL, "<")
''',
)
replace_once(
    registry,
    '''def _visible_html_links(text: str) -> tuple[str, ...]:
    """Return navigable href values from browser-visible raw HTML anchors."""
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ()
    return tuple(parser.hrefs)
''',
    '''def _visible_html_links(text: str) -> tuple[str, ...]:
    """Return navigable href values from browser-visible raw HTML anchors."""
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(_SHARED_PROTECT_NON_COMMONMARK_RAW_TAG_OPENERS(text))
        parser.close()
    except Exception:
        return ()
    return tuple(parser.hrefs)
''',
)
replace_once(
    registry,
    '''def _visible_html_link_bindings(text: str) -> tuple[tuple[str, str], ...]:
    """Keep linked character data attached to its already-decoded HTML href."""
    parser = _VisibleHTMLTextParser()
    parser.feed(text)
    parser.close()
    return tuple(parser.link_bindings)
''',
    '''def _visible_html_link_bindings(text: str) -> tuple[tuple[str, str], ...]:
    """Keep linked character data attached to its already-decoded HTML href."""
    parser = _VisibleHTMLTextParser()
    parser.feed(_SHARED_PROTECT_NON_COMMONMARK_RAW_TAG_OPENERS(text))
    parser.close()
    return tuple(parser.link_bindings)
''',
)
replace_once(
    registry,
    '''def _mask_hidden_html_regions(text: str) -> str:
    """Mask hidden HTML containers globally so visibility state survives slicing."""
    parser = _HiddenHTMLRegionParser(text)
    try:
        parser.feed(text)
        parser.close()
        parser.finish()
''',
    '''def _mask_hidden_html_regions(text: str) -> str:
    """Mask hidden HTML containers globally so visibility state survives slicing."""
    protected = _SHARED_PROTECT_NON_COMMONMARK_RAW_TAG_OPENERS(text)
    parser = _HiddenHTMLRegionParser(protected)
    try:
        parser.feed(protected)
        parser.close()
        parser.finish()
''',
)
