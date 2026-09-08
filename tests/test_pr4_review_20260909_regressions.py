from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).parent.parent
REGISTRY = runpy.run_path(str(Path(__file__).with_name("test_research_reference_registry.py")))


def test_registered_source_anchor_rejects_download_activation() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    url = "https://iview.abc.net.au/show/black-comedy"
    live = f"**Registered source:** {url}"
    downloaded = f'**Registered source:** <a href="{url}" download>{url}</a>'
    assert live in corpus
    mutated = corpus.replace(live, downloaded, 1)
    with pytest.raises(AssertionError, match="executable URL"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_status_receipt_rejects_unregistered_link_binding() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    live = "**research reference registry**"
    linked = "**[research reference registry](https://creativecommons.org/publicdomain/zero/1.0/)**"
    assert live in corpus
    mutated = corpus.replace(live, linked, 1)
    assert REGISTRY["_normalised_status_value"](mutated) == REGISTRY["_normalised_status_value"](corpus)
    with pytest.raises(AssertionError, match="Status section must not contain hyperlinks"):
        REGISTRY["_validate_registry_corpus"](mutated)


def test_raw_html_list_cannot_detach_complete_entry_boundary() -> None:
    corpus = (ROOT / "docs" / "RESEARCH-REFERENCE-CORPUS.md").read_text(encoding="utf-8")
    heading = "### *Black Comedy* (ABC, 2014-2020)"
    section = REGISTRY["_registered_sections"](corpus)[heading]
    live = "is not permission to"
    split = "is <ul><li>not</li></ul> permission to"
    assert live in section
    mutated_section = section.replace(live, split, 1)
    assert REGISTRY["_normalise_complete_entry_integrity"](mutated_section) == REGISTRY["_normalise_complete_entry_integrity"](section)
    mutated = corpus.replace(section, mutated_section, 1)
    with pytest.raises(AssertionError, match="raw list HTML"):
        REGISTRY["_validate_registry_corpus"](mutated)
