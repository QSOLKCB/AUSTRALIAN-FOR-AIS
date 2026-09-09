from pathlib import Path

POLICING = Path("tests/test_policing_context_roadmap.py")
REGRESSIONS = Path("tests/test_pr4_clean_head_audit_regressions.py")

text = POLICING.read_text(encoding="utf-8")

replacements = [
    (
        '            or (tag == "data" and "value" in attribute_names)\n',
        '            or (tag == "data" and "value" in attribute_names)\n'
        '            or (tag == "time" and "datetime" in attribute_names)\n',
    ),
    (
        '        if tag == "a" and {"download", "ping", "target"}.intersection(attribute_names):\n'
        '            self.violations.add("executable-url")\n',
        '        if tag == "a" and {"attributionsrc", "download", "ping", "target"}.intersection(attribute_names):\n'
        '            self.violations.add("executable-url")\n',
    ),
    (
        '        if {"lang", "xml:lang"}.intersection(attribute_names):\n'
        '            self.violations.add("language-override")\n',
        '        if {"lang", "xml:lang"}.intersection(attribute_names):\n'
        '            self.violations.add("language-override")\n'
        '        if any(\n'
        '            key.lower() == "translate"\n'
        '            and (value or "").strip().casefold() == "no"\n'
        '            for key, value in attrs\n'
        '        ):\n'
        '            self.violations.add("language-override")\n'
        '        # autofocus can move keyboard/assistive-technology focus into the\n'
        '        # middle of a sealed governed surface without changing its text.\n'
        '        if "autofocus" in attribute_names:\n'
        '            self.violations.add("keyboard-navigation")\n',
    ),
    (
        '        "accessibility-disabled": "aria-disabled source-link suppression HTML",\n',
        '        "accessibility-disabled": "aria-disabled source-link suppression HTML",\n'
        '        "keyboard-navigation": "autofocus/tabindex keyboard-navigation HTML",\n',
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one policing replacement target, found {count}: {old!r}")
    text = text.replace(old, new, 1)

POLICING.write_text(text, encoding="utf-8")

regressions = REGRESSIONS.read_text(encoding="utf-8")
marker = "def test_anchor_attribution_reporting_endpoint_is_rejected() -> None:"
if marker not in regressions:
    regressions = regressions.rstrip() + '''\n\n\ndef test_anchor_attribution_reporting_endpoint_is_rejected() -> None:\n    url = "https://iview.abc.net.au/show/black-comedy"\n    endpoint = "https://untrusted.example/register"\n    fragment = f'<a href="{url}" attributionsrc="{endpoint}">{url}</a>'\n    violations = POLICING["_governed_surface_html_violations"](fragment)\n    assert "executable-url" in violations\n\n    corpus = CORPUS.read_text(encoding="utf-8")\n    original = f"**Registered source:** {url}"\n    replacement = f"**Registered source:** {fragment}"\n    assert original in corpus\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](\n            corpus.replace(original, replacement, 1)\n        )\n\n\ndef test_machine_readable_time_value_is_rejected() -> None:\n    fragment = '<time datetime="2099-01-01">2022</time>'\n    violations = POLICING["_governed_surface_html_violations"](fragment)\n    assert "machine-metadata" in violations\n\n    corpus = CORPUS.read_text(encoding="utf-8")\n    original = "The 2022 report directly records that Australian accent and slang"\n    replacement = (\n        'The <time datetime="2099-01-01">2022</time> report directly records '\n        "that Australian accent and slang"\n    )\n    assert original in corpus\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](\n            corpus.replace(original, replacement, 1)\n        )\n\n\ndef test_autofocus_is_rejected_across_governed_content() -> None:\n    fragment = '<span tabindex="-1" autofocus>not</span>'\n    violations = POLICING["_governed_surface_html_violations"](fragment)\n    assert "keyboard-navigation" in violations\n\n    corpus = CORPUS.read_text(encoding="utf-8")\n    original = (\n        "Availability through ABC iview is not permission "\n        "to redistribute content."\n    )\n    replacement = (\n        'Availability through ABC iview is <span tabindex="-1" autofocus>not</span> '\n        "permission to redistribute content."\n    )\n    assert original in corpus\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](\n            corpus.replace(original, replacement, 1)\n        )\n\n\ndef test_translate_no_is_rejected_as_language_override() -> None:\n    fragment = '<span translate="no">not</span>'\n    violations = POLICING["_governed_surface_html_violations"](fragment)\n    assert "language-override" in violations\n\n    corpus = CORPUS.read_text(encoding="utf-8")\n    original = (\n        "Availability through ABC iview is not permission "\n        "to redistribute content."\n    )\n    replacement = (\n        'Availability through ABC iview is <span translate="no">not</span> '\n        "permission to redistribute content."\n    )\n    assert original in corpus\n    with pytest.raises(AssertionError):\n        REGISTRY["_validate_registry_corpus"](\n            corpus.replace(original, replacement, 1)\n        )\n''' + "\n"

REGRESSIONS.write_text(regressions, encoding="utf-8")
