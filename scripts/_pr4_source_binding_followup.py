"""Preserve HTML attribute continuations and literal inline-code examples."""
from pathlib import Path

path = Path("tests/test_research_reference_registry.py")
text = path.read_text(encoding="utf-8")
start = text.index("def _forbidden_governed_html_constructs(text: str) -> set[str]:")
end = text.index("\n\ndef _normalise_complete_entry_integrity", start)
text = text[:start] + '''def _forbidden_governed_html_constructs(text: str) -> set[str]:
    """Parse live HTML without reclassifying attribute continuations as code."""
    rendered = _rendered_registry_text(text)
    scan = _mask_multiline_code_spans(rendered)
    fence: FenceState | None = None
    found: set[str] = set()
    semantics = _GovernedHTMLSemanticsDetector()

    try:
        for raw_line in scan.splitlines():
            # HTMLParser buffers an unfinished start tag in rawdata. Once an
            # actual live tag is open, all subsequent attribute whitespace
            # belongs to that tag, including tabs and four-space indentation.
            # Do not discard those lines as standalone Markdown code.
            if re.match(r"<[A-Za-z]", semantics.rawdata):
                semantics.feed(raw_line + "\\n")
                continue

            while fence is not None and not _fence_container_continues(raw_line, fence):
                fence = None
            if fence is not None:
                if _is_fence_closer(raw_line, fence):
                    fence = None
                continue
            opener = _fence_opener(raw_line)
            if opener is not None:
                fence = opener
                continue

            logical, is_code = _strip_composed_container_prefixes(raw_line)
            if is_code:
                continue
            logical = _mask_inline_code_spans(logical)
            semantics.feed(logical + "\\n")
            if GOVERNED_REPLACEMENT_HTML_PATTERN.search(logical):
                found.add("replacement")
            if GOVERNED_DELETION_HTML_PATTERN.search(logical):
                found.add("deletion")
            if GOVERNED_BIDI_HTML_PATTERN.search(logical):
                found.add("bidi")
        semantics.close()
    except Exception:
        # Malformed live HTML is unsafe for a render-integrity contract.
        found.add("conditional-raw-text")
    found.update(semantics.found)
    return found
''' + text[end:]
compile(text, str(path), "exec")
path.write_text(text, encoding="utf-8")

path = Path("tests/test_policing_context_roadmap.py")
text = path.read_text(encoding="utf-8")
old = '''    parser = _GovernedSurfaceHTMLParser()
    parser.feed(_rendered_structure(markdown))'''
new = '''    parser = _GovernedSurfaceHTMLParser()
    structure = _rendered_structure(markdown)
    # Exclude definite same-line literal code examples before parsing HTML.
    # Delimiter runs inside a raw HTML attribute are not Markdown syntax.
    # Multiline code ambiguity remains fail-closed at this HTML preflight.
    raw_tag = re.compile(
        r"</?[A-Za-z][A-Za-z0-9-]*(?=[ \\t\\r\\n\\f/>])"
        r"(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*>", re.DOTALL,
    )
    characters = list(structure)
    cursor = 0
    while cursor < len(structure):
        tag_match = raw_tag.match(structure, cursor)
        if tag_match is not None:
            cursor = tag_match.end()
            continue
        if structure[cursor] != "`":
            cursor += 1
            continue
        run_end = cursor + 1
        while run_end < len(structure) and structure[run_end] == "`":
            run_end += 1
        backslashes = 0
        previous = cursor - 1
        while previous >= 0 and structure[previous] == "\\\\":
            backslashes += 1
            previous -= 1
        if backslashes % 2:
            cursor = run_end
            continue
        line_end = re.search(r"[\\r\\n]", structure[run_end:])
        limit = run_end + line_end.start() if line_end is not None else len(structure)
        closer = next((
            match for match in re.finditer(r"`+", structure[run_end:limit])
            if len(match.group()) == run_end - cursor
        ), None)
        if closer is None:
            cursor = run_end
            continue
        end = run_end + closer.end()
        characters[cursor:end] = " " * (end - cursor)
        cursor = end
    parser.feed("".join(characters))'''
assert text.count(old) == 1, "Shared HTML preflight changed"
text = text.replace(old, new, 1)
compile(text, str(path), "exec")
path.write_text(text, encoding="utf-8")
print("Corrected attribute continuation and literal code handling; no tests or hashes changed.", flush=True)
