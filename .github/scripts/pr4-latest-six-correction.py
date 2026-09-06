from pathlib import Path

TARGET = Path("tests/test_research_reference_registry.py")
text = TARGET.read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return source.replace(old, new, 1)


old_underscore = r'''def _strip_emphasis_preserving_intraword_underscores(text: str) -> str:
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
'''
new_underscore = r'''OBFUSCATED_INTRAW_WORD_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z]_){2,}[A-Za-z]_?(?![A-Za-z0-9])"
)


def _strip_emphasis_preserving_intraword_underscores(text: str) -> str:
    """Preserve repeated single-letter intraword underscores used as visible obfuscation."""
    sentinel = "\uE000"
    assert sentinel not in text
    characters = list(text)
    for match in OBFUSCATED_INTRAW_WORD_PATTERN.finditer(text):
        for index in range(match.start(), match.end()):
            if characters[index] == "_":
                characters[index] = sentinel

    visible = "".join(characters)
    # Preserve the established canonical normalization for ordinary Markdown
    # emphasis and snake_case-like project identifiers. Only the reported
    # repeated single-letter obfuscation shape keeps literal underscores.
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return visible.replace(sentinel, "_")
'''
text = replace_once(
    text,
    old_underscore,
    new_underscore,
    "narrow intraword underscore preservation",
)

old_source_order = r'''    source_value = rendered[source_block.start(1):source_block.end(1)]
    assert _visible_inline_text(source_value), f"{entry} has an empty registered-source field"

    destinations = _usable_https_destinations(
        source_value,
        reference_scope=reference_scope,
    )
    assert destinations, f"{entry} has no usable HTTPS destination in its registered-source field"
'''
new_source_order = r'''    source_value = rendered[source_block.start(1):source_block.end(1)]
    destinations = _usable_https_destinations(
        source_value,
        reference_scope=reference_scope,
    )
    assert destinations, f"{entry} has no usable HTTPS destination in its registered-source field"
    assert _visible_inline_text(source_value), f"{entry} has an empty registered-source field"
'''
text = replace_once(
    text,
    old_source_order,
    new_source_order,
    "registered-source validation ordering",
)

# Keep the generated target compatible with git diff --check: exactly one
# trailing newline, never an extra blank line at EOF.
TARGET.write_text(text.rstrip("\r\n") + "\n", encoding="utf-8")
