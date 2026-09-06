"""Keep Setext underlines ahead of list-marker recognition in PR4 repair."""
from pathlib import Path

path = Path("tests/test_phase2_review_followup.py")
text = path.read_text(encoding="utf-8")
old = '''    for raw_line in structure.splitlines(keepends=True):
        logical, is_code, container = namespace["_parse_fence_container_prefixes"]('''
new = '''    for raw_line in structure.splitlines(keepends=True):
        if paragraph_start is not None:
            # Setext syntax takes precedence over interpreting a lone hyphen
            # as an empty list item. Retain the preceding paragraph's owning
            # containers when looking for its underline.
            candidate, continues = namespace["_strip_expected_fence_containers"](
                raw_line, paragraph_container
            )
            probe, columns = namespace["_indent_columns"](candidate)
            if (continues and columns <= 3
                    and re.fullmatch(r"(?:=+|-+)[ \\t]*", candidate[probe:])):
                return paragraph_start
        logical, is_code, container = namespace["_parse_fence_container_prefixes"]('''
assert text.count(old) == 1, "Setext repair anchor changed"
text = text.replace(old, new, 1)
compile(text, str(path), "exec")
path.write_text(text, encoding="utf-8")
print("Setext underline precedence corrected without changing any tests or integrity hashes.")
