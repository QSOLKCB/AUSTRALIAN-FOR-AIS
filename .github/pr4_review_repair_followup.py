from pathlib import Path


path = Path("tests/test_research_reference_registry.py")
text = path.read_text(encoding="utf-8")

old = '''    assert "raw-list" not in found, (
        "raw list HTML is not allowed in governed documents because list containers can "
        "detach sealed scalar prose during browser tree construction"
    )
    assert "named-details" not in found, (
'''
new = '''    assert "raw-list" not in found, (
        "raw list HTML is not allowed in governed documents because list containers can "
        "detach sealed scalar prose during browser tree construction"
    )
    assert "raw-block" not in found, (
        "raw block-container HTML is not allowed in governed documents because block "
        "elements can terminate or reframe sealed scalar prose"
    )
    assert "named-details" not in found, (
'''
assert text.count(old) == 1, "raw-block assertion insertion anchor changed"
text = text.replace(old, new, 1)

old = '''    assert "raw-mathml" not in found, (
        "raw MathML is not allowed in governed documents"
    )
    assert "nested-nobr" not in found, (
'''
new = '''    assert "raw-mathml" not in found, (
        "raw MathML is not allowed in governed documents"
    )
    assert "nobr" not in found, (
        "nobr presentation containers are not allowed in governed documents"
    )
    assert "nested-nobr" not in found, (
'''
assert text.count(old) == 1, "single-nobr assertion insertion anchor changed"
text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
