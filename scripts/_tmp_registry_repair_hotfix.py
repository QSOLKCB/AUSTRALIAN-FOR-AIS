from pathlib import Path

path = Path("scripts/_tmp_registry_review_repair.py")
text = path.read_text(encoding="utf-8")

old = '''    values: list[str] = []
    for rendered_line, structure_line in zip(rendered_lines, structure_lines):
        logical, is_code = _strip_composed_container_prefixes(structure_line)
        if is_code:
            continue
        logical = logical.lstrip(" \\t")
        if not logical.startswith(field):
            continue
        suffix = logical[len(field):]
        if suffix and suffix[0] not in " \\t":
            continue

        rendered_logical, rendered_is_code = _strip_composed_container_prefixes(
            rendered_line
        )
        if rendered_is_code:
            continue
        rendered_logical = rendered_logical.lstrip(" \\t")
        if not rendered_logical.startswith(field):
            continue
        raw_value = rendered_logical[len(field):]
        values.append(_visible_inline_text(raw_value))
    return values
'''

new = '''    values: list[str] = []
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

count = text.count(old)
if count != 1:
    raise SystemExit(f"paragraph-aware scalar replacement: expected one match, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
