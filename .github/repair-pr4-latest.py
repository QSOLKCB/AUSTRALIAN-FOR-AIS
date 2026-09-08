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
    '''        # Hyperlink auditing can send an additional network request that is not
        # represented by the sealed href binding. Fail closed on it.
        if tag == "a" and "ping" in attribute_names:
            self.violations.add("executable-url")
''',
    '''        # `hidden=until-found` is conditionally revealed by find-in-page or
        # fragment navigation. Treat it as active conditional content rather
        # than omitting text that can later become reader-visible. Reuse the
        # existing corpus-wide conditional-content policy kind so the registry
        # and shared methodology validators fail closed together.
        if any(
            key.lower() == "hidden"
            and (value or "").strip().casefold() == "until-found"
            for key, value in attrs
        ):
            self.violations.add("conditional-raw-text")
        # Hyperlink auditing can send an additional network request that is not
        # represented by the sealed href binding. Fail closed on it.
        if tag == "a" and "ping" in attribute_names:
            self.violations.add("executable-url")
''',
)
replace_once(
    policing,
    '''        # Raw Markdown is embedded into an existing HTML document. A live
        # duplicate root tag can merge attributes onto that document root, so
        # reject html/body rather than approximating tree-builder semantics.
        if tag in {"html", "body"}:
            self.violations.add("document-root")
''',
    '''        # Raw Markdown is embedded into an existing HTML document. Live
        # html/body tags can merge attributes onto the document root, while
        # <base> mutates document-wide URL/target behavior for otherwise sealed
        # links. Reject all three under the active document-global HTML policy
        # rather than approximating tree-builder/navigation semantics.
        if tag in {"html", "body", "base"}:
            self.violations.add("document-root")
''',
)

regressions = Path("tests/test_pr4_current_review_regressions.py")
text = regressions.read_text(encoding="utf-8")
marker = "\n\n# Human receipt: autolink/implied-end/type-6 repair passed 12 exact and 912 full-suite tests before self-cleanup.\n"
if text.count(marker) != 1:
    raise SystemExit("current-review human-receipt marker missing or duplicated")
additions = r'''


def test_hidden_until_found_is_rejected_across_governed_paths() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    payload = '<span hidden="until-found">Current sources may be skipped.</span>'
    mutated_roadmap = roadmap.replace(
        POLICING["WORKSTREAM_END"],
        "\n" + payload + "\n" + POLICING["WORKSTREAM_END"],
        1,
    )
    with pytest.raises(AssertionError, match="conditional/legacy raw-text"):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    injected = REGISTRY["STATUS_HEADING"] + "\n" + payload
    mutated_corpus = corpus.replace(REGISTRY["STATUS_HEADING"], injected, 1)
    with pytest.raises(AssertionError, match="conditional/legacy raw-text"):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)


def test_base_element_is_rejected_across_governed_paths() -> None:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    payload = '<base target="_top">'
    mutated_roadmap = roadmap.replace(
        POLICING["WORKSTREAM_END"],
        "\n" + payload + "\n" + POLICING["WORKSTREAM_END"],
        1,
    )
    with pytest.raises(AssertionError, match="document-root HTML"):
        POLICING["_validate_policing_workstream"](mutated_roadmap)

    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    injected = REGISTRY["STATUS_HEADING"] + "\n" + payload
    mutated_corpus = corpus.replace(REGISTRY["STATUS_HEADING"], injected, 1)
    with pytest.raises(AssertionError, match="document-root HTML"):
        REGISTRY["_validate_registry_corpus"](mutated_corpus)
'''
regressions.write_text(text.replace(marker, additions + marker, 1), encoding="utf-8")
