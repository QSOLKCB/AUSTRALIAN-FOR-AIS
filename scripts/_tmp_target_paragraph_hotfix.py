from pathlib import Path

path = Path("tests/test_research_reference_registry.py")
text = path.read_text(encoding="utf-8")
start = text.index("def _visible_scalar_values(section: str, field: str) -> list[str]:")
end = text.index("\ndef _scalar_value(entry: str, section: str, field: str) -> str:", start)
replacement = '''def _visible_scalar_values(section: str, field: str) -> list[str]:
    """Return visible scalar values after normalising composed Markdown containers."""
    rendered, structure = _markdown_views(section)
    rendered_lines = rendered.splitlines()
    structure_lines = structure.splitlines()
    assert len(rendered_lines) == len(structure_lines)

    values: list[str] = []
    paragraph_open = False
    for rendered_line, structure_line in zip(rendered_lines, structure_lines):
        if not structure_line.strip():
            paragraph_open = False
            continue

        logical, is_code = _strip_composed_container_prefixes(structure_line)
        continuation = is_code and paragraph_open
        if is_code and not continuation:
            paragraph_open = False
            continue

        if continuation:
            logical = structure_line.lstrip(" \\t")
            rendered_logical = rendered_line.lstrip(" \\t")
            next_paragraph_open = True
        else:
            logical = logical.lstrip(" \\t")
            rendered_logical, rendered_is_code = _strip_composed_container_prefixes(
                rendered_line
            )
            if rendered_is_code:
                paragraph_open = False
                continue
            rendered_logical = rendered_logical.lstrip(" \\t")
            next_paragraph_open = _line_opens_paragraph(structure_line)

        if logical.startswith(field):
            suffix = logical[len(field):]
            if not suffix or suffix[0] in " \\t":
                if rendered_logical.startswith(field):
                    raw_value = rendered_logical[len(field):]
                    values.append(_visible_inline_text(raw_value))

        paragraph_open = next_paragraph_open
    return values

'''
path.write_text(text[:start] + replacement + text[end + 1 :], encoding="utf-8")
