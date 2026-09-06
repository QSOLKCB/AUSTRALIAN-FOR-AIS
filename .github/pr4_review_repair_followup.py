from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


path = Path("tests/test_research_reference_registry.py")
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    '''RAW_HTML_TAG_TOKEN_PATTERN = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?=[ \\t\\r\\n/>])"
    r"(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*>",
    flags=re.DOTALL,
)
''',
    '''RAW_HTML_TAG_TOKEN_PATTERN = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?=[ \\t\\r\\n/>])"
    r"(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*>",
    flags=re.DOTALL,
)
RAW_HTML_ANCHOR_ELEMENT_PATTERN = re.compile(
    r"<a\\b(?:[^>\\\"']|\\\"[^\\\"]*\\\"|'[^']*')*>.*?</a[ \\t\\r\\n]*>",
    flags=re.IGNORECASE | re.DOTALL,
)
''',
    "raw HTML anchor pattern",
)

text = replace_once(
    text,
    '''def _mask_raw_html_tags_for_markdown_link_discovery(text: str) -> str:
    """Mask raw HTML tag tokens before interpreting Markdown link syntax."""
    characters = list(text)
    for match in RAW_HTML_TAG_TOKEN_PATTERN.finditer(text):
        _mask_segment(characters, match.start(), match.end())
    return "".join(characters)
''',
    '''def _mask_raw_html_tags_for_markdown_link_discovery(text: str) -> str:
    """Mask raw HTML anchors/tags before interpreting Markdown link syntax."""
    characters = list(text)
    # The HTML parser has already recorded each visible anchor href. Mask the
    # whole anchor for the later Markdown/autolink/bare-URL passes so a URL
    # used as visible anchor text is not counted a second time as bare prose.
    for match in RAW_HTML_ANCHOR_ELEMENT_PATTERN.finditer(text):
        _mask_segment(characters, match.start(), match.end())
    for match in RAW_HTML_TAG_TOKEN_PATTERN.finditer(text):
        _mask_segment(characters, match.start(), match.end())
    return "".join(characters)
''',
    "anchor-aware Markdown link masking",
)

if "def test_raw_html_anchor_url_label_is_not_double_counted():" not in text:
    text = text.rstrip() + '''\n\n\ndef test_raw_html_anchor_url_label_is_not_double_counted():\n    destination = "https://example.org/path"\n    assert _usable_https_destinations(\n        f'<a href="{destination}">{destination}</a>'\n    ) == (destination,)\n''' + "\n"

path.write_text(text, encoding="utf-8")
print("Applied anchor-origin de-duplication follow-up.")
