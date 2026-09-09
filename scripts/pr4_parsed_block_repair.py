from pathlib import Path

policing_path = Path("tests/test_policing_context_roadmap.py")
text = policing_path.read_text(encoding="utf-8")

old = '    "head", "hr", "html", "iframe", "link", "noframes", "ol", "optgroup",\n'
new = '    "head", "hr", "html", "iframe", "li", "link", "noframes", "ol", "optgroup",\n'
assert text.count(old) == 1
text = text.replace(old, new, 1)

old = '        if tag in {"ol", "ul"}:\n            self.violations.add("raw-list")\n'
new = '        if tag in {"ol", "ul", "li"}:\n            self.violations.add("raw-list")\n'
assert text.count(old) == 1
text = text.replace(old, new, 1)


def insert_after_in_governed_parser(source: str, method_signature: str, needle: str, addition: str) -> str:
    class_start = source.index("class _GovernedSurfaceHTMLParser(HTMLParser):")
    class_end = source.index("\ndef _governed_surface_html_violations", class_start)
    method_start = source.index(method_signature, class_start, class_end)
    needle_start = source.index(needle, method_start, class_end)
    insert_at = needle_start + len(needle)
    return source[:insert_at] + addition + source[insert_at:]


parsed_start_policy = '''        # Generic CommonMark block containers are checked from HTMLParser's
        # complete parsed start-tag span. This is deliberately source-aware so
        # multiline attributes cannot evade the ownership boundary by being
        # split across physical source lines.
        if tag in GOVERNED_RAW_BLOCK_CONTAINER_TAGS and self._source:
            start = self._source_offset()
            raw_tag = self.get_starttag_text() or ""
            end = start + len(raw_tag)
            previous = _nearest_substantive_source_line(
                self._source, start, before=True
            )
            if (
                not raw_tag
                or not _source_tag_occupies_line(self._source, start, end)
                or (
                    previous is not None
                    and not _is_governed_structural_boundary(previous)
                )
            ):
                self.violations.add("raw-block")
            else:
                # CommonMark type-6 blocks consume source through the next
                # blank line. Do not let a following Markdown list, quote, or
                # ATX heading be re-invented later by line-based receipts.
                line_end = self._source.find("\\n", end)
                if line_end >= 0:
                    next_end = self._source.find("\\n", line_end + 1)
                    if next_end < 0:
                        next_end = len(self._source)
                    following = self._source[line_end + 1:next_end].lstrip(" \\t")
                    if (
                        LIST_MARKER_PATTERN.match(following) is not None
                        or following.startswith(">")
                        or re.match(r"#{1,6}(?:[ \\t]+|$)", following) is not None
                    ):
                        self.violations.add("raw-block")
'''
text = insert_after_in_governed_parser(
    text,
    "    def handle_starttag(\n",
    "        tag = tag.lower()\n",
    parsed_start_policy,
)

parsed_end_policy = '''        # Generic block closing tags use the parser's source position too,
        # so closing boundaries cannot fall back to line-local regex parsing.
        if tag in GOVERNED_RAW_BLOCK_CONTAINER_TAGS and self._source:
            start = self._source_offset()
            match = re.match(
                rf"</{re.escape(tag)}[ \\t\\r\\n\\f]*>",
                self._source[start:],
                flags=re.IGNORECASE,
            )
            if match is None:
                self.violations.add("raw-block")
            else:
                end = start + match.end()
                following = _nearest_substantive_source_line(
                    self._source, end, before=False
                )
                if (
                    not _source_tag_occupies_line(self._source, start, end)
                    or (
                        following is not None
                        and not _is_governed_structural_boundary(following)
                    )
                ):
                    self.violations.add("raw-block")
'''
text = insert_after_in_governed_parser(
    text,
    "    def handle_endtag(self, tag: str) -> None:\n",
    "        tag = tag.lower()\n",
    parsed_end_policy,
)

start_marker = '    # Raw block containers may be retained only as complete structural\n'
end_marker = '    # Markdown links become anchors only after Markdown rendering, so the raw-HTML\n'
start = text.index(start_marker)
end = text.index(end_marker, start)
replacement = (
    "    # Generic raw-block ownership is enforced by the parsed HTML start/end\n"
    "    # tag callbacks above, including multiline tags. Keep this function-level\n"
    "    # pass focused on Markdown-only semantics that HTMLParser cannot see.\n\n"
)
text = text[:start] + replacement + text[end:]
policing_path.write_text(text, encoding="utf-8")

regression_path = Path("tests/test_pr4_clean_head_audit_regressions.py")
regressions = regression_path.read_text(encoding="utf-8")
assert "test_multiline_generic_raw_block_opener_cannot_detach_rights_boundary" not in regressions
addition = r'''


def test_multiline_generic_raw_block_opener_cannot_detach_rights_boundary() -> None:
    corpus = CORPUS.read_text(encoding="utf-8")
    original = (
        "Availability through ABC iview is not permission "
        "to redistribute content."
    )
    fragment = (
        "Availability through ABC iview is "
        '<center data-x="a\nb">not permission to redistribute content.'
    )
    assert original in corpus
    violations = POLICING["_governed_surface_html_violations"](fragment)
    assert "raw-block" in violations
    with pytest.raises(AssertionError, match="raw block-container HTML"):
        REGISTRY["_validate_registry_corpus"](
            corpus.replace(original, fragment, 1)
        )


def test_list_item_cannot_wrap_complete_governed_entry() -> None:
    fragment = (
        "## Governed section\n\n"
        "<li>\n\nCanonical governed prose.\n\n</li>\n\n"
        "## Next section\n"
    )
    violations = POLICING["_governed_surface_html_violations"](fragment)
    assert "raw-list" in violations
    assert "li" in POLICING["GOVERNED_BLOCK_TAGS_WITH_DEDICATED_POLICY"]
    assert "li" not in POLICING["GOVERNED_RAW_BLOCK_CONTAINER_TAGS"]

    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index("### *Black Comedy* (ABC, 2014-2020)")
    end = corpus.index("\n### *Kath & Kim*", start)
    entry = corpus[start:end]
    mutated = corpus[:start] + "<li>\n\n" + entry + "\n</li>\n" + corpus[end:]
    with pytest.raises(AssertionError, match="raw list HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)
'''
regression_path.write_text(regressions.rstrip() + addition + "\n", encoding="utf-8")
