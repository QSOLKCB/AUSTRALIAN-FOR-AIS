"""Regression checks for governed research-reference registration."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import html
from html.parser import HTMLParser
import ipaddress
from pathlib import Path
import re
from urllib.parse import urlparse

import pytest


CORPUS = Path(__file__).parent.parent / "docs" / "RESEARCH-REFERENCE-CORPUS.md"

SOURCE_TYPE_FIELD = "**Source type:**"
RIGHTS_FIELD = "**Rights and provenance boundary:**"
EPISTEMIC_FIELD = "**Epistemic status:**"
SAFE_FIELD = "**Safe benchmark abstraction:**"
DOI_FIELD = "**DOI:**"
SCALAR_FIELDS = (
    SOURCE_TYPE_FIELD,
    RIGHTS_FIELD,
    EPISTEMIC_FIELD,
    SAFE_FIELD,
)
BOUNDARY_FIELDS = (
    RIGHTS_FIELD,
    EPISTEMIC_FIELD,
    SAFE_FIELD,
)
SOURCES_KEY = "sources"


def _entry_contract(
    *,
    sources: tuple[str, ...],
    source_type: str,
    governance: str,
    rights: str,
    epistemic: str,
    safe: str,
    doi: str | None = None,
) -> dict[str, object]:
    """Build one explicit governed-entry contract."""
    contract: dict[str, object] = {
        SOURCES_KEY: sources,
        SOURCE_TYPE_FIELD: source_type,
        "governance": governance,
        RIGHTS_FIELD: rights,
        EPISTEMIC_FIELD: epistemic,
        SAFE_FIELD: safe,
    }
    if doi is not None:
        contract[DOI_FIELD] = doi
    return contract


ENTRY_CONTRACTS: dict[str, dict[str, object]] = {
    "### *Black Comedy* (ABC, 2014-2020)": _entry_contract(
        sources=("https://iview.abc.net.au/show/black-comedy",),
        source_type=(
            "Broadcaster programme record for an Australian First Nations "
            "sketch-comedy series."
        ),
        governance="required",
        rights=(
            "No programme dialogue, subtitles, scripts, episode transcripts, "
            "audiovisual material, character material, or other copyrighted "
            "expression is licensed to this repository by registration."
        ),
        epistemic=(
            "It is not a representative corpus of Aboriginal or Torres Strait "
            "Islander speech, and the programme alone cannot establish "
            "community-wide pragmatic rules."
        ),
        safe=(
            "Any later First Nations-specific benchmark family requires appropriate "
            "consultation, provenance, permissions, and scope limitations, plus a "
            "documented governance basis."
        ),
    ),
    "### *Kath & Kim*": _entry_contract(
        sources=("https://www.screenaustralia.gov.au/screen-guide/kath-and-kim-16295/",),
        source_type=(
            "Screen Australia catalogue record for an Australian television comedy "
            "series."
        ),
        governance="required",
        rights=(
            "Registration does not authorise copying dialogue, scripts, subtitles, "
            "character catchphrases, or audiovisual material into benchmark data."
        ),
        epistemic=(
            "It does not establish how suburban Australians, women, working-class "
            "speakers, or any other social category generally speak."
        ),
        safe=(
            "Any class-marked register family remains a hypothesis and requires "
            "appropriate consultation, provenance, permissions, and scope limitations "
            "before it can support community-specific benchmark claims."
        ),
    ),
    "### *The Castle* (1997)": _entry_contract(
        sources=(
            "https://www.acmi.net.au/works/86581--the-castle/",
            "https://www.nfsa.gov.au/collection/item/castle-fathers-day",
        ),
        source_type=(
            "Australian cultural-institution catalogue records for the 1997 feature "
            "film."
        ),
        governance="required",
        rights=(
            "This project must not copy screenplay text, dialogue, subtitles, clips, "
            "or distinctive character material into benchmark records."
        ),
        epistemic=(
            "It is not evidence that its characters or dialogue represent Australians "
            "generally."
        ),
        safe=(
            "Because the film's portrayal is class-marked, any later class-register or "
            "community-specific benchmark family derived from these hypotheses "
            "requires appropriate consultation, provenance, permissions, and scope "
            "limitations before it can support claims about a community."
        ),
    ),
    "### *Shaun Micallef's MAD AS HELL*": _entry_contract(
        sources=("https://iview.abc.net.au/show/shaun-micallef-s-mad-as-hell",),
        source_type=(
            "ABC broadcaster programme record for a satirical television comedy "
            "series."
        ),
        governance="not-required",
        rights=(
            "Programme dialogue, sketches, subtitles, transcripts, characters, and "
            "audiovisual material remain third-party copyrighted expression and must "
            "not be redistributed as benchmark data."
        ),
        epistemic=(
            "Political satire is analysed structurally; registration does not endorse "
            "the political position of any sketch or turn satire into factual evidence "
            "about its targets."
        ),
        safe="Do not reproduce programme jokes or political conclusions.",
    ),
    "### *Acropolis Now*": _entry_contract(
        sources=("https://www.screenaustralia.gov.au/screen-guide/acropolis-now-889/",),
        source_type=(
            "Screen Australia catalogue record for a historical Australian television "
            "comedy series."
        ),
        governance="required",
        rights=(
            "Registration does not permit copying scripts, dialogue, subtitles, "
            "accents-as-text, catchphrases, character material, or audiovisual content."
        ),
        epistemic=(
            "It must not be treated as representative evidence of Greek-Australian, "
            "migrant, or multicultural speech, and historical portrayals must not be "
            "projected onto contemporary communities."
        ),
        safe=(
            "Any community-specific benchmark family requires appropriate "
            "consultation, provenance, permissions, and scope limitations."
        ),
    ),
    (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    ): _entry_contract(
        sources=("https://europeanjournalofhumour.org/ejhr/article/view/560",),
        doi="https://doi.org/10.7592/EJHR2021.9.4.560",
        source_type="Peer-reviewed article in The European Journal of Humour Research.",
        governance="not-required",
        rights=(
            "Citation and analysis do not imply permission to redistribute the full "
            "article in this repository."
        ),
        epistemic=(
            "It does not provide a national-character lookup table or individual-level "
            "ground truth."
        ),
        safe="Do not convert its cultural comparisons into deterministic labels.",
    ),
    (
        "### Hurley (2025), *Laughter with purpose: how First Nations Australian "
        "comedians use humour to engage, educate, and empower audiences*"
    ): _entry_contract(
        sources=(
            "https://www.tandfonline.com/doi/full/10.1080/2040610X.2025.2538977",
        ),
        doi="https://doi.org/10.1080/2040610X.2025.2538977",
        source_type=(
            "Peer-reviewed article in Comedy Studies using a culturally grounded "
            "qualitative methodology centred on Aboriginal and Torres Strait Islander "
            "comedians, writers, and performers."
        ),
        governance="required",
        rights=(
            "Publisher access does not license this repository to reproduce the "
            "article, interview material, quoted performances, or community-specific "
            "language."
        ),
        epistemic=(
            "It is a stronger basis for understanding research-governance requirements "
            "than outsider summaries, but it still does not authorise this project to "
            "create First Nations benchmark ground truth without appropriate community "
            "involvement."
        ),
        safe=(
            "Any First Nations-specific annotation protocol or benchmark family "
            "requires appropriate consultation, provenance, permissions, and scope "
            "limitations and must preserve the paper's emphasis on cultural specificity "
            "and self-determination."
        ),
    ),
    "### Slade, *Australian Sketch Comedy Field Theory* (ASCFT)": _entry_contract(
        sources=("https://doi.org/10.5281/zenodo.17781653",),
        source_type=(
            "Project-authored formal-analysis paper supplied to the project by Trent "
            "Slade / QSOL-IMC."
        ),
        governance="not-required",
        rights=(
            "Registration does not place the full paper, its distinctive wording, "
            "equations, source-derived examples, transcripts, or referenced comedy "
            "material under the repository licence."
        ),
        epistemic=(
            "They do not by themselves establish literal physical ontology, "
            "empirically validated mechanisms, universal laws of Australian humour, or "
            "population-level cultural ground truth."
        ),
        safe=(
            "Do not copy source dialogue, transcript wording, distinctive jokes, "
            "equations as benchmark labels, or source-derived media expression."
        ),
    ),
    "### Trans-Tasman constitutional and federation context": _entry_contract(
        sources=(
            "https://peo.gov.au/understand-our-parliament/history-of-parliament/"
            "federation/federation",
            "https://peo.gov.au/understand-our-parliament/how-parliament-works/"
            "the-australian-constitution/introducing-the-australian-constitution",
            "https://peo.gov.au/understand-our-parliament/your-questions-on-notice/"
            "questions/new-zealand-is-mentioned-in-the-australian-constitution-does-"
            "that-mean-that-new-zealanders-have-the-right-to-vote-in-australia",
            "https://www.legislation.gov.au/C2004Q00685/asmade/1901-01-01/text/"
            "original/epub/OEBPS/document_1/document_1.html",
        ),
        source_type=(
            "Official Parliamentary Education Office explanatory material and "
            "Commonwealth legislation used to establish historical federation and "
            "constitutional context."
        ),
        governance="not-required",
        rights=(
            "Registration does not authorise wholesale republication of page text, "
            "educational material, or legislative presentation content in benchmark "
            "records; benchmark examples must remain independently authored."
        ),
        epistemic=(
            "They do not establish a shared modern national identity, prove a "
            "cousin-like relationship between individual Australians and New "
            "Zealanders, or determine the pragmatic meaning of contemporary "
            "trans-Tasman teasing."
        ),
        safe=(
            "Use the records only to document historical context around Australia and "
            "New Zealand; do not infer modern affinity, hostility, shared identity, or "
            "pragmatic licence from constitutional history alone."
        ),
    ),
    (
        "### ABC Language, *From rooting to bonking: a history of Australian sex "
        "terms*"
    ): _entry_contract(
        sources=(
            "https://www.abc.net.au/news/2018-03-01/from-rooting-to-bonking-a-history-"
            "of-australian-sex-terms/9492856",
        ),
        source_type=(
            "ABC language-history article used as a public linguistic reference for "
            "Australian sexual slang and lexical change."
        ),
        governance="not-required",
        rights=(
            "Registration does not permit reproducing substantial article text or "
            "turning its examples into redistributable benchmark records without "
            "independent provenance and rights analysis."
        ),
        epistemic=(
            "It does not establish how every Australian uses the term, does not by "
            "itself establish New Zealand usage, and does not make any single phrase a "
            "deterministic sexual reading outside context."
        ),
        safe=(
            "Build independently authored polysemy pairs that vary social, technical, "
            "botanical, or sports contexts; do not treat the article as proof that every "
            "Australian or New Zealander assigns the same sense to root."
        ),
    ),
    "### Victoria University, *Australian slang dictionary*": _entry_contract(
        sources=(
            "https://www.vu.edu.au/about-vu/news-events/vu-blog/"
            "australian-slang-dictionary",
        ),
        source_type=(
            "Public university educational glossary used for orientation to attested "
            "Australian slang terms and context-sensitive address forms."
        ),
        governance="not-required",
        rights=(
            "Registration does not permit copying the glossary wholesale into the "
            "benchmark, and its entries are not automatically benchmark labels or "
            "licensed dataset examples."
        ),
        epistemic=(
            "It is not a complete lexicon, a population survey, or evidence that every "
            "listed form is equally current across regions, generations, occupations, "
            "and communities."
        ),
        safe=(
            "Use the glossary to nominate independently authored lexical and "
            "context-swap tests, while requiring separate evidence for regional, "
            "generational, occupational, or community-specific claims."
        ),
    ),
    "### r/australia, *Best Aussie slang* community thread": _entry_contract(
        sources=("https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/",),
        source_type=(
            "Public user-generated community discussion retained as orientation and "
            "community-attestation material rather than lexicographic authority."
        ),
        governance="not-required",
        rights=(
            "Registration does not permit bulk copying, redistribution, or conversion "
            "of comments into benchmark examples; any exact quotation requires separate "
            "provenance and rights consideration."
        ),
        epistemic=(
            "Its participants are self-selected and the thread cannot establish "
            "prevalence, representativeness, national consensus, or authoritative "
            "etymology."
        ),
        safe=(
            "Use the thread only to generate research leads for independently authored "
            "examples and later source verification; do not use comment popularity or "
            "repetition as a proxy for population prevalence."
        ),
    ),
    (
        "### Australian Defence multinational communication reports (2022 and 2026)"
    ): _entry_contract(
        sources=(
            "https://www.defence.gov.au/news-events/news/2022-09-08/"
            "communication-key-combined-exercise",
            "https://www.defence.gov.au/news-events/news/2026-06-11/"
            "partner-nations-rehearse-war",
        ),
        source_type=(
            "Official Australian Defence news reports documenting communication "
            "challenges and adaptation during multinational military exercises."
        ),
        governance="not-required",
        rights=(
            "The repository may cite and summarise the reports but does not treat their "
            "prose, imagery, interviews, or exercise material as redistributable "
            "benchmark data."
        ),
        epistemic=(
            "These reports support communication-friction hypotheses, not claims that "
            "slang functioned as intentional encryption, defeated Allied codebreakers, "
            "or was formally prohibited in Australian-American exercises."
        ),
        safe=(
            "Create synthetic communication tasks that vary slang density, listener "
            "familiarity, and operational stakes without reproducing exercise dialogue "
            "or claiming that authentic Australian speech is inherently unsafe or "
            "unintelligible."
        ),
    ),
    "### WWII American-serviceman Australia language guides": _entry_contract(
        sources=(
            "https://www.awm.gov.au/collection/LIB100000077",
            "https://www.awm.gov.au/collection/LIB20571",
            "https://dictionaryofsydney.org/media/5562",
        ),
        source_type=(
            "Australian War Memorial catalogue records for wartime guides and an "
            "archived Dictionary of Sydney record identifying the Australian-slang "
            "section of a United States Army guide."
        ),
        governance="not-required",
        rights=(
            "Registration does not authorise republication of the full booklets, scans, "
            "illustrations, or glossary content as benchmark data."
        ),
        epistemic=(
            "They support a historical need for cultural and language orientation, but "
            "do not prove that actual joint operations failed because of slang or that "
            "Australian speech operated as an accidental cipher."
        ),
        safe=(
            "Use the archival records to motivate historically bounded comprehension "
            "experiments and source-governance questions, not to infer contemporary "
            "prevalence or fabricate claims of wartime codebreaking failure."
        ),
    ),
}
EXPECTED_GOVERNED_ENTRIES = tuple(ENTRY_CONTRACTS)

BOUNDARY_VALUE_HASHES = {'### *Black Comedy* (ABC, 2014-2020)': {'**Rights and provenance boundary:**': 'cae812038f7b4f0537bfe57f23795034eb4f37b1d9782ed392b3ebbeb8d86b03', '**Epistemic status:**': '48f19bace9450140e92d8675c5ac5172a8f1dbe11c2dafe152d553a150b4f6fa', '**Safe benchmark abstraction:**': '07c74efc929c4cb35e18926d72400a1a92362916d22d67d62f9ccac353d06ca7'}, '### *Kath & Kim*': {'**Rights and provenance boundary:**': 'c8e27a4fbfaf31fbbed5da7e397c16471a29025ad8eb2d3077d7375b6d6ceb31', '**Epistemic status:**': '51beb5076e007042b599da0328f428a4a99a5d8210a122a09d0d9fc01a09b556', '**Safe benchmark abstraction:**': '20b61a34b8c8de629ee47a7cb5dce1eb091f11397be74ace51199a8b236294a9'}, '### *The Castle* (1997)': {'**Rights and provenance boundary:**': '4aa5a0c3088117db674e03cf30c99584cf0c51a878412914624f5cc47d31af39', '**Epistemic status:**': 'ff5507a687f30834d310b3a5165ef98dd0e3ad9a21daa727c3bb40a8f2d17219', '**Safe benchmark abstraction:**': '51d8b85a50e05c6d280d16fe3faff3821ab67ee5ffdb4b6cf00e9964a433ac8f'}, "### *Shaun Micallef's MAD AS HELL*": {'**Rights and provenance boundary:**': '0ec09ac259c8f7a8e8ff287ace5ea1c9ad5324e67b88ec6617e8fe4c54cd2dd1', '**Epistemic status:**': '7fad0f6acb3abb59aaa5b233d7c464e1ab98b90ee6ad57d73a8933c2adbc92a0', '**Safe benchmark abstraction:**': '5fba923f66548ccb15ee60980f8e6a89930ddac715fb0a1ca396700013ae4c38'}, '### *Acropolis Now*': {'**Rights and provenance boundary:**': '107cf642f59261eb86c658c004bf043ea59fd26b6581f9f55262242fc8fdf6fd', '**Epistemic status:**': '90020a10667cc7135d9a885b087afa64da8085130fc455400dec67f87bb6c016', '**Safe benchmark abstraction:**': '2a2d654c2081079c1cd243a486816a442de0a57af09c3c2652c88827ad447de4'}, '### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*': {'**Rights and provenance boundary:**': '5f54028a15a648d3bae4476cd564dcb9e27145abbcf1a8e47ba2939763b4522b', '**Epistemic status:**': '82c6427f74df92609b6ea164beb549ac4201a1ecedcf07dbe1ea60ba5a572378', '**Safe benchmark abstraction:**': '6db0d1e84d1109f8d758f50046da1a20fdc567ddfd7cd23a17dd92ce8995e3a3'}, '### Hurley (2025), *Laughter with purpose: how First Nations Australian comedians use humour to engage, educate, and empower audiences*': {'**Rights and provenance boundary:**': '985fca98f9133d8396e2a5401ff7e6145cd0ea307daecedc9519679e15a04caa', '**Epistemic status:**': 'db57b3ea91c986e4ee3af928c963d3d77fd82b53a142f65a69286d7a1258254b', '**Safe benchmark abstraction:**': '917cfefad7ce793e50d670086bfff2c2c92dc45a7d4ff3514cddc5650de768cb'}, '### Slade, *Australian Sketch Comedy Field Theory* (ASCFT)': {'**Rights and provenance boundary:**': 'e087f4c10be9d21e4e3da819c72cbf1e21e29ca68f9943c036f3d7e98650639e', '**Epistemic status:**': '311b1185d79c54070556e1b09539ea9550fdd944e222d4098a11d32c8131b9c5', '**Safe benchmark abstraction:**': 'ef1386fb555baa20ec8ca365e41ee9560acf7648063128dedc6e217e8b1358cd'}, '### Trans-Tasman constitutional and federation context': {'**Rights and provenance boundary:**': '60583e2cef8c2f217fa3c4a4356dcc34df2552d32385eb60e69a2bcd14b89ab2', '**Epistemic status:**': '70c79aa45e75b53c16a0da6fc1466d6bbfc4df9af2a23df81bb43bf73c798571', '**Safe benchmark abstraction:**': '29382d7b25c2622f9441b64e33c5bdf7f65f6faa78473977ae907025695ec494'}, '### ABC Language, *From rooting to bonking: a history of Australian sex terms*': {'**Rights and provenance boundary:**': '7a66a4a08e09fb0818175f004f18b92be6e4fd71b64de69df6fdf8d100445200', '**Epistemic status:**': '1fd8c8521f13449262852fb6d3c8bd4dd4a2ea15f7b3195f7833e95f558ad8d1', '**Safe benchmark abstraction:**': '3845d5eb52196b674fa8f65178702ca0e5c563b6d20859f0b0dae7e02d9c86dc'}, '### Victoria University, *Australian slang dictionary*': {'**Rights and provenance boundary:**': '15aab72e357737551735419e0819c6785eba25f66e1c591ae45a508b1b16cb57', '**Epistemic status:**': 'd40108d2a8454dda753e5aecbf3d31fdca13a877927d7f27e5c8282cb4e3df43', '**Safe benchmark abstraction:**': 'abed3969653a372ce326c5a4de53b6528e56e5309657767e4ae04bda6f2ad413'}, '### r/australia, *Best Aussie slang* community thread': {'**Rights and provenance boundary:**': '43863b2aba252719bcf561f0425c7936dfbfc15bc3f1cc281884449a530f35bf', '**Epistemic status:**': 'f01416f2e8300843fb7487b81255897b73adc76e8422adcd73884aeabfa6076a', '**Safe benchmark abstraction:**': '35e3e647f8cdfc53cbdf3f0c1b9fd1ee713ba71a96657a93eed3e92765d21d24'}, '### Australian Defence multinational communication reports (2022 and 2026)': {'**Rights and provenance boundary:**': 'bb6985de4a9593ce589e19302cc0fa955e2c74663e7aa94bc5992fe278811909', '**Epistemic status:**': 'b54a4b0ada2b4870928b8aca1bcc0b78679d127ed0b0493c2196264b37b6afcf', '**Safe benchmark abstraction:**': '3cf19474e6d059b8303074d75ff086fb3c6655677c4d7bae7b34609ca1c8dcdf'}, '### WWII American-serviceman Australia language guides': {'**Rights and provenance boundary:**': '017ab0b941600f913cbb323b226546e76073e4a68dfb5a4709ee2b2331df1145', '**Epistemic status:**': '6210806120d333ba302d1ffb694b3b92cb3008ce0880142f5c40ab17b8fa89b1', '**Safe benchmark abstraction:**': 'f6b654c8a020fe3fd37c3f8de2f87c99e0b959e4ae6a8e9544cc79d2480404c2'}}

SOURCE_TYPE_VALUE_HASHES = {'### *Acropolis Now*': 'd5be93cc49571c5f83858008eb7b8101d9af8298dc7a7576183907c3ea4be15d',
 '### *Black Comedy* (ABC, 2014-2020)': 'ec715cef672b2fb61251f4cd2956258c77ba44eef5846f6ec870c290227bf6ff',
 '### *Kath & Kim*': '4d2b273563ff9fc830d5149ef8bb70cd0627cc0f7a7b64d8edf5f11fe849b630',
 "### *Shaun Micallef's MAD AS HELL*": 'a0c8ed618509fe8c7489b79352c25ec1e8553887e42ce09226f1434a2623209e',
 '### *The Castle* (1997)': '7718d0da544f10148203f67318e878df045607d18d9767fa4bb0237de0d42e0e',
 '### ABC Language, *From rooting to bonking: a history of Australian sex terms*': 'aade91743e5cba29b0e20a676884077697d5b98bb00ddd064ee21a13a96b7fbb',
 '### Australian Defence multinational communication reports (2022 and 2026)': '46a98638f5e147a78ed012c99a7c79851047490ddb179d2794b5ebb20d8f5743',
 '### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*': '1e4b6b3e408e64f78e64d9d1d7771e9c8994a72f72acebeccf427c7ea53ff8c4',
 '### Hurley (2025), *Laughter with purpose: how First Nations Australian comedians use humour to engage, educate, and empower audiences*': '35785d1fad7461854860f48411a3b14348f93f2f557af6c533756c4fcc3da5c0',
 '### Slade, *Australian Sketch Comedy Field Theory* (ASCFT)': '2961e8415bf496935457851a71c641643020102aaa532ed14a8c84d19d1d0f4b',
 '### Trans-Tasman constitutional and federation context': 'a0ca0e5699957f0709c6eef293384c48be940e79c9c3c34ebccc46b43687cf95',
 '### Victoria University, *Australian slang dictionary*': 'cf86b61c68efc97ce8ed33557ee420d42c3a2f03da257a2a2d2d0f171903e6fe',
 '### WWII American-serviceman Australia language guides': '093d2c21877cabdfd34d0d500f97a4a21477d30817fc282cf0376ec452446270',
 '### r/australia, *Best Aussie slang* community thread': '9344b351046982daa306153e2eb56f7c85a23607065aa454e142961af5ab10bc'}

GOVERNANCE_RATIONALE_HASHES = {'### *Acropolis Now*': '00d3590178d2cc6d9a4e4285dcd39403640b986f5389a0949af5ddd8adbdb169',
 '### *Black Comedy* (ABC, 2014-2020)': 'd038192bda9b712b9a68efce0a7e237b454f291949da1233f6eaceae62dd23d1',
 '### *Kath & Kim*': '24416824a1a6bfc1ce2e88dd76f0d9e9ec89af52782905f45e0ff5b1f5411a09',
 "### *Shaun Micallef's MAD AS HELL*": 'f2172dc029c4afa3829de4d49867978a375b6a2a28b8d4c75364124d8ab1f03b',
 '### *The Castle* (1997)': '8e510282ec3f6d2519137591b5d1cc4af412c80f11a7375e3916d2472ed7bd78',
 '### ABC Language, *From rooting to bonking: a history of Australian sex terms*': '250be6e926eaa3150e1588e6611a53cc84bcc556691cad9c96576743f89cadac',
 '### Australian Defence multinational communication reports (2022 and 2026)': 'e205cbce9f548406f83e882861d2d6c22eba896763b42611b791d04f7639377a',
 '### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*': '276c76cbdece677c0be3b919842ff596b4dfce1b1ecf42f230aecfde562eff4c',
 '### Hurley (2025), *Laughter with purpose: how First Nations Australian comedians use humour to engage, educate, and empower audiences*': 'baeec71dbcb9f7b10ff9666ad7bd232269bad98877f136c6b755039898237699',
 '### Slade, *Australian Sketch Comedy Field Theory* (ASCFT)': '94ef11805676a88e05433b69242c98b03c7f7b046e24d2e4a963caf10b624b38',
 '### Trans-Tasman constitutional and federation context': 'f136b9cba1be34be253f0040fc61901c9860ccbd9e91b1c26aa3d889a13db999',
 '### Victoria University, *Australian slang dictionary*': '1a6d7f9b920dd47b3b9444dbec12fe119768aeb5d176052b5c3b4ff5ef63b380',
 '### WWII American-serviceman Australia language guides': 'bacdff9bf663ddc2346b92570015b4d4e5aef4edc6024e6e60139cb4a902bec7',
 '### r/australia, *Best Aussie slang* community thread': 'c66e326bbe7271137fd04b1142fb324e24ce20da4bfc7d9add801e0dae5d5151'}

BATCH_HEADING = "## Registered post-Phase-2 expansion batch"
BATCH_END = "## Priority A: adversarial pragmatics"
CONTRACT_HEADING = "## Registration contract for new sources"
CONTRACT_SENTENCE = (
    "Every adopted post-Phase-2 registry entry must record all of the following fields"
)
REGISTRATION_CONTRACT_HASH = "1d171556a66c3cfc54a7bf14072d51bb68d17cb390fffa826a0f50329e2d51d6"
CONSULTATION_BOUNDARY = (
    "appropriate consultation, provenance, permissions, and scope limitations"
)

ENTRY_HEADING_PATTERN = re.compile(r"(?m)^ {0,3}(?P<heading>### .+?)[ \t]*$")
HTML_ENTRY_HEADING_PATTERN = re.compile(r"(?is)<h3\b[^>]*>.*?</h3\s*>")
GOVERNANCE_FIELD_PATTERN = re.compile(
    r"(?m)^[ \t]*\*\*Community-specific governance:\*\*"
)
GOVERNANCE_PATTERN = re.compile(
    r"(?m)^[ \t]*\*\*Community-specific governance:\*\*[ \t]*"
    r"(required|not-required):(?P<rationale>[^\r\n]*)$"
)
REGISTERED_SOURCE_FIELD_PATTERN = re.compile(
    r"(?m)^[ \t]*\*\*Registered sources?:\*\*"
)
RESEARCH_MAPPING_HEADING_PATTERN = re.compile(
    r"(?m)^ {0,3}(?:Candidate research mappings:|Research mappings:)[ \t]*$"
)
PROJECT_MAPPING_HEADING_PATTERN = re.compile(
    r"(?m)^ {0,3}Relevant project mappings:[ \t]*$"
)
MARKDOWN_LINK_PATTERN = re.compile(
    r"(?P<image>!?)\[(?P<label>[^\]\r\n]*)\]\("
    r"[ \t]*(?P<destination><[^>\r\n]+>|[^\s)\r\n]+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?"
    r"[ \t]*\)"
)
BARE_HTTPS_LINE_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:(?:[-+*]|\d{1,9}[.)])[ \t]+)?"
    r"(?P<url>https://\S+)[ \t]*$"
)
AUTOLINK_PATTERN = re.compile(r"<(?P<url>https://[^>\s]+)>")
LINK_REFERENCE_DEFINITION_PATTERN = re.compile(
    r"(?m)^ {0,3}\[(?P<label>[^\]\r\n]+)\]:[ \t]*"
    r"(?:\r?\n {1,3})?"
    r"(?P<destination><[^>\r\n]+>|[^\s\r\n]+)"
    r"(?:[ \t]+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^)]*\)))?[ \t]*$"
)
REFERENCE_LINK_PATTERN = re.compile(
    r"(?P<image>!?)\[(?P<label>[^\]\r\n]+)\]"
    r"\[(?P<reference>[^\]\r\n]*)\]"
)
SHORTCUT_REFERENCE_LINK_PATTERN = re.compile(
    r"(?P<image>!?)\[(?P<label>[^\]\r\n]+)\]"
    r"(?![ \t]*(?:\(|\[|:))"
)
HOST_LABEL_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?")
NUMERIC_HOST_LABEL_PATTERN = re.compile(r"(?:0[xX][0-9A-Fa-f]+|[0-9]+)")
SPECIAL_USE_HOST_SUFFIXES = (
    "localhost",
    "invalid",
    "test",
    "example",
    "local",
    "home.arpa",
)
THEMATIC_BREAK_PATTERN = re.compile(
    r"(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,}"
)
FENCE_PATTERN = re.compile(r"(?P<fence>`{3,}|~{3,})(?P<info>.*)")
LIST_CONTAINER_PREFIX_PATTERN = re.compile(r"(?:[-+*]|\d{1,9}[.)])[ \t]+")
STRONG_METADATA_FIELD_PATTERN = re.compile(
    r"^(?P<outer>\*\*|__|\*|_)(?P<inner>\*\*|__|\*|_)"
    r"(?P<label>[^:\r\n]+):(?P=inner)(?P=outer)(?=$|[ \t])"
)
HTML_STRONG_METADATA_FIELD_PATTERN = re.compile(
    r"^<(?P<tag>strong|b)\b(?P<attrs>[^>]*)>"
    r"(?P<body>.*?)</(?P=tag)>(?=$|[ \t])",
    flags=re.IGNORECASE,
)
HTML_TAG_PATTERN = re.compile(
    r"</?[A-Za-z][^>]*>|<![A-Za-z][^>]*>|<\?[\s\S]*?\?>"
)
NON_RENDERING_HTML_PATTERN = re.compile(
    r"<(script|style|template)\b[^>]*>.*?</\1\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)


class _VisibleHTMLTextParser(HTMLParser):
    """Collect browser-visible HTML text while respecting hidden containers."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hrefs: list[str] = []
        self.stack: list[tuple[str, bool]] = []

    @staticmethod
    def _is_hidden(tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        tag = tag.lower()
        if tag in {"script", "style", "template"}:
            return True
        values = {key.lower(): (value or "") for key, value in attrs}
        # A closed HTML disclosure renders its descendants collapsed until the
        # reader explicitly opens it. Governance text must be visible by default.
        if tag in {"details", "dialog"} and "open" not in values:
            return True
        if "hidden" in values:
            return True
        if values.get("aria-hidden", "").strip().lower() == "true":
            return True
        style = re.sub(r"\s+", "", values.get("style", "").lower())
        return "display:none" in style or "visibility:hidden" in style

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        inherited = self.stack[-1][1] if self.stack else False
        hidden = inherited or self._is_hidden(tag, attrs)
        if tag.lower() == "a" and not hidden:
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.hrefs.append(value)
                    break
        self.stack.append((tag.lower(), hidden))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in HTML_VOID_TAGS:
            return
        # HTML browsers ignore the self-closing flag on non-void elements.
        # Treat `<a ... />` as an opening anchor so its href remains navigable.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)


def _visible_html_text(text: str) -> str:
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ""
    return " ".join(parser.parts)


def _visible_html_links(text: str) -> tuple[str, ...]:
    """Return navigable href values from browser-visible raw HTML anchors."""
    parser = _VisibleHTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return ()
    return tuple(parser.hrefs)


HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class _HiddenHTMLRegionParser(HTMLParser):
    """Locate browser-hidden HTML regions while preserving source offsets."""

    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=True)
        self.text = text
        self.stack: list[tuple[str, bool, int | None]] = []
        self.spans: list[tuple[int, int]] = []
        self.line_offsets = [0]
        for line in text.splitlines(keepends=True):
            self.line_offsets.append(self.line_offsets[-1] + len(line))

    def _offset(self) -> int:
        line, column = self.getpos()
        line_index = min(max(line - 1, 0), len(self.line_offsets) - 1)
        return min(self.line_offsets[line_index] + column, len(self.text))

    def _tag_end(self, start: int) -> int:
        close = self.text.find(">", start)
        return len(self.text) if close < 0 else close + 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        parent_hidden = self.stack[-1][1] if self.stack else False
        own_hidden = _VisibleHTMLTextParser._is_hidden(tag, attrs)
        hidden = parent_hidden or own_hidden
        start = self._offset()

        if tag in HTML_VOID_TAGS:
            if own_hidden and not parent_hidden:
                self.spans.append((start, self._tag_end(start)))
            return

        root_start = start if hidden and not parent_hidden else None
        self.stack.append((tag, hidden, root_start))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in HTML_VOID_TAGS:
            # Match browser tree construction: the slash does not close a
            # non-void HTML element such as `<dialog />` or `<a />`.
            self.handle_starttag(tag, attrs)
            return
        parent_hidden = self.stack[-1][1] if self.stack else False
        if _VisibleHTMLTextParser._is_hidden(tag, attrs) and not parent_hidden:
            start = self._offset()
            self.spans.append((start, self._tag_end(start)))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] != tag:
                continue
            end = self._tag_end(self._offset())
            popped = self.stack[index:]
            del self.stack[index:]
            for _, _, root_start in popped:
                if root_start is not None:
                    self.spans.append((root_start, end))
            return

    def finish(self) -> None:
        for _, _, root_start in self.stack:
            if root_start is not None:
                self.spans.append((root_start, len(self.text)))
        self.stack.clear()


def _mask_hidden_html_regions(text: str) -> str:
    """Mask hidden HTML containers globally so visibility state survives slicing."""
    parser = _HiddenHTMLRegionParser(text)
    try:
        parser.feed(text)
        parser.close()
        parser.finish()
    except Exception:
        return _mask_non_newline(text)

    characters = list(text)
    for start, end in parser.spans:
        _mask_segment(characters, start, end)
    return "".join(characters)


def _indent_columns(value: str, start: int = 0) -> tuple[int, int]:
    """Return the first non-indent index and indentation in display columns."""
    index = start
    columns = 0
    while index < len(value) and value[index] in " \t":
        if value[index] == " ":
            columns += 1
        else:
            columns += 4 - (columns % 4)
        index += 1
    return index, columns


@dataclass(frozen=True)
class LineContext:
    quote_depth: int
    after_quotes: str
    leading_spaces: int
    logical: str
    list_indent: int | None
    indented_code: bool


@dataclass(frozen=True)
class FenceState:
    character: str
    minimum_length: int
    containers: tuple[tuple[str, int], ...]


def _mask_non_newline(text: str) -> str:
    """Replace visible characters with spaces while preserving line endings."""
    return "".join(character if character in "\r\n" else " " for character in text)


def _line_context(line: str) -> LineContext:
    """Describe CommonMark quote/list prefixes without erasing code indentation."""
    value = line.rstrip("\r\n")
    position = 0
    quote_depth = 0

    while True:
        probe = position
        spaces = 0
        while spaces < 3 and probe < len(value) and value[probe] == " ":
            probe += 1
            spaces += 1
        if probe >= len(value) or value[probe] != ">":
            break
        quote_depth += 1
        probe += 1
        if probe < len(value) and value[probe] in " \t":
            probe += 1
        position = probe

    after_quotes = value[position:]
    leading_spaces = len(after_quotes) - len(after_quotes.lstrip(" "))
    list_indent: int | None = None
    logical_start = min(leading_spaces, 3)

    if leading_spaces <= 3:
        marker = LIST_CONTAINER_PREFIX_PATTERN.match(after_quotes, leading_spaces)
        if marker:
            list_indent = marker.end()
            logical_start = marker.end()

    indented_code = list_indent is None and leading_spaces >= 4
    logical = after_quotes[logical_start:]
    return LineContext(
        quote_depth=quote_depth,
        after_quotes=after_quotes,
        leading_spaces=leading_spaces,
        logical=logical,
        list_indent=list_indent,
        indented_code=indented_code,
    )


def _display_columns(value: str) -> int:
    columns = 0
    for character in value:
        if character == "\t":
            columns += 4 - (columns % 4)
        else:
            columns += 1
    return columns


def _parse_composed_container_prefixes(
    line: str,
) -> tuple[str, bool, tuple[tuple[str, int], ...]]:
    """Return logical text, code status, and ordered list/quote containers."""
    value = line.rstrip("\r\n")
    position = 0
    containers: list[tuple[str, int]] = []

    for _ in range(32):
        probe, columns = _indent_columns(value, position)
        if columns >= 4:
            return value[position:], True, tuple(containers)

        if probe < len(value) and value[probe] == ">":
            containers.append(("quote", 0))
            position = probe + 1
            if position < len(value) and value[position] in " \t":
                position += 1
            continue

        marker = LIST_CONTAINER_PREFIX_PATTERN.match(value, probe)
        if marker:
            content_indent = columns + _display_columns(marker.group(0))
            containers.append(("list", content_indent))
            position = marker.end()
            continue

        position = probe
        break

    return value[position:], False, tuple(containers)


def _consume_required_indent(
    value: str,
    start: int,
    required_columns: int,
) -> tuple[int, bool]:
    position = start
    columns = 0
    while position < len(value) and value[position] in " \t" and columns < required_columns:
        if value[position] == " ":
            columns += 1
        else:
            columns += 4 - (columns % 4)
        position += 1
    return position, columns >= required_columns


def _strip_expected_fence_containers(
    line: str,
    containers: tuple[tuple[str, int], ...],
) -> tuple[str, bool]:
    """Strip the continuation form of the containers that own an active fence."""
    value = line.rstrip("\r\n")
    position = 0

    for kind, amount in containers:
        if kind == "list":
            position, ok = _consume_required_indent(value, position, amount)
            if not ok:
                return value, False
            continue

        probe, columns = _indent_columns(value, position)
        if columns > 3 or probe >= len(value) or value[probe] != ">":
            return value, False
        position = probe + 1
        if position < len(value) and value[position] in " \t":
            position += 1

    return value[position:], True


def _line_opens_paragraph(line: str) -> bool:
    """Return whether a rendered line can keep a CommonMark paragraph open."""
    context = _line_context(line)
    logical = context.logical.strip()
    if not logical or context.indented_code:
        return False
    if re.fullmatch(r"#{1,6}(?:[ \t]+.*)?", logical):
        return False
    if THEMATIC_BREAK_PATTERN.fullmatch(logical):
        return False
    if LINK_REFERENCE_DEFINITION_PATTERN.fullmatch(logical):
        return False
    return True


def _fence_opener(line: str) -> FenceState | None:
    """Return a valid fence opener and its ordered container ownership."""
    logical, indented_code, containers = _parse_composed_container_prefixes(line)
    if indented_code:
        return None
    match = FENCE_PATTERN.fullmatch(logical.rstrip(" \t"))
    if not match:
        return None
    marker = match.group("fence")
    info = match.group("info")
    if marker[0] == "`" and "`" in info:
        return None
    return FenceState(
        character=marker[0],
        minimum_length=len(marker),
        containers=containers,
    )


def _fence_container_continues(line: str, state: FenceState) -> bool:
    """Return whether the active fence's complete container chain continues."""
    if not line.strip():
        return True
    if not state.containers:
        return True
    _, ok = _strip_expected_fence_containers(line, state.containers)
    return ok


def _fence_logical_line(line: str, state: FenceState) -> str:
    """Return content inside the active fence's ordered container context."""
    if not state.containers:
        return line.rstrip("\r\n")
    logical, ok = _strip_expected_fence_containers(line, state.containers)
    return logical if ok else line.rstrip("\r\n")


def _is_fence_closer(line: str, state: FenceState) -> bool:
    """Return whether line closes the active fence."""
    logical = _fence_logical_line(line, state)
    marker_index, indent_columns = _indent_columns(logical)
    if indent_columns > 3:
        return False
    candidate = logical[marker_index:].rstrip(" \t")
    return bool(
        re.fullmatch(
            rf"{re.escape(state.character)}{{{state.minimum_length},}}[ \t]*",
            candidate,
        )
    )


def _mask_multiline_code_spans(text: str) -> str:
    """Mask closed Markdown code spans, including spans crossing line breaks."""
    characters = list(text)
    position = 0
    while position < len(text):
        if text[position] != "`":
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        marker = text[position:run_end]
        close = text.find(marker, run_end)
        if close < 0:
            position = run_end
            continue
        for index in range(position, close + len(marker)):
            if characters[index] not in "\r\n":
                characters[index] = " "
        position = close + len(marker)
    return "".join(characters)


def _mask_inline_code_spans(text: str) -> str:
    """Mask same-line Markdown code spans while preserving offsets."""
    characters = list(text)
    position = 0
    while position < len(text):
        if text[position] != "`":
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        marker = text[position:run_end]
        close = text.find(marker, run_end)
        if close < 0:
            position = run_end
            continue
        for index in range(position, close + len(marker)):
            if characters[index] not in "\r\n":
                characters[index] = " "
        position = close + len(marker)
    return "".join(characters)


def _mask_segment(characters: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if characters[index] not in "\r\n":
            characters[index] = " "


def _mask_html_comments_on_line(
    raw_line: str,
    *,
    in_comment: bool,
    scan_line: str | None = None,
) -> tuple[str, bool]:
    """Mask HTML comments using a code-span-masked scan view."""
    scan = _mask_inline_code_spans(scan_line if scan_line is not None else raw_line)
    characters = list(raw_line)
    position = 0

    while position < len(raw_line):
        if in_comment:
            canonical = scan.find("-->", position)
            alternate = scan.find("--!>", position)
            candidates = [index for index in (canonical, alternate) if index >= 0]
            if not candidates:
                _mask_segment(characters, position, len(raw_line))
                return "".join(characters), True
            close_start = min(candidates)
            close_length = 4 if scan.startswith("--!>", close_start) else 3
            close_end = close_start + close_length
            _mask_segment(characters, position, close_end)
            position = close_end
            in_comment = False
            continue

        opener = scan.find("<!--", position)
        if opener < 0:
            break
        in_comment = True
        position = opener

    return "".join(characters), in_comment



def _markdown_views(text: str) -> tuple[str, str]:
    """Return rendered and structural views with exact offsets preserved."""
    rendered_parts: list[str] = []
    structural_parts: list[str] = []
    in_comment = False
    fence: FenceState | None = None
    paragraph_open = False
    active_list_indent: int | None = None
    raw_lines = text.splitlines(keepends=True)
    scan_lines = _mask_multiline_code_spans(text).splitlines(keepends=True)
    assert len(raw_lines) == len(scan_lines)

    for raw_line, scan_line in zip(raw_lines, scan_lines):
        line = raw_line.rstrip("\r\n")
        indent_index, indent_columns = _indent_columns(line)
        explicit_list = (
            LIST_CONTAINER_PREFIX_PATTERN.match(line, indent_index)
            if indent_columns <= 3
            else None
        )
        if explicit_list is not None:
            active_list_indent = indent_columns + len(
                explicit_list.group(0).expandtabs(4)
            )
        elif line.strip() and active_list_indent is not None:
            if indent_columns < active_list_indent:
                active_list_indent = None

        if not line.strip():
            paragraph_open = False

        while fence is not None and not _fence_container_continues(line, fence):
            fence = None

        if fence is not None:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            if _is_fence_closer(line, fence):
                fence = None
            continue

        if in_comment:
            rendered_line, in_comment = _mask_html_comments_on_line(
                raw_line,
                in_comment=True,
                scan_line=scan_line,
            )
            rendered_parts.append(rendered_line)
            structural_parts.append(_mask_inline_code_spans(rendered_line))
            if not in_comment:
                paragraph_open = _line_opens_paragraph(
                    rendered_line.rstrip("\r\n")
                )
            continue

        context = _line_context(line)
        _, composed_indented_code = _strip_composed_container_prefixes(line)
        indented_code = context.indented_code or composed_indented_code
        if active_list_indent is not None and indent_columns >= active_list_indent:
            indented_code = (indent_columns - active_list_indent) >= 4

        if indented_code and not paragraph_open:
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            continue

        if indented_code and paragraph_open:
            rendered_line, in_comment = _mask_html_comments_on_line(
                raw_line,
                in_comment=False,
                scan_line=scan_line,
            )
            rendered_parts.append(rendered_line)
            structural_parts.append(_mask_inline_code_spans(rendered_line))
            paragraph_open = True
            continue

        opener = _fence_opener(line)
        if opener is not None:
            fence = opener
            rendered_parts.append(raw_line)
            structural_parts.append(_mask_non_newline(raw_line))
            paragraph_open = False
            continue

        rendered_line, in_comment = _mask_html_comments_on_line(
            raw_line,
            in_comment=False,
            scan_line=scan_line,
        )
        rendered_parts.append(rendered_line)
        structural_parts.append(_mask_inline_code_spans(rendered_line))
        paragraph_open = _line_opens_paragraph(
            rendered_line.rstrip("\r\n")
        )

    return "".join(rendered_parts), "".join(structural_parts)

def _rendered_registry_text(text: str) -> str:
    rendered, _ = _markdown_views(text)
    return rendered


def _structural_registry_text(text: str) -> str:
    _, structural = _markdown_views(text)
    return structural


def _render_inline_code_spans(text: str) -> str:
    """Replace same-line code spans with the text they visibly render."""
    parts: list[str] = []
    position = 0
    while position < len(text):
        if text[position] != "`":
            parts.append(text[position])
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        marker = text[position:run_end]
        close = text.find(marker, run_end)
        if close < 0:
            parts.append(marker)
            position = run_end
            continue
        parts.append(text[run_end:close].strip(" "))
        position = close + len(marker)
    return "".join(parts)



def _visible_inline_text(text: str) -> str:
    """Reduce Markdown/HTML metadata to browser-visible text only."""
    rendered = _rendered_registry_text(text)
    visible = _render_inline_code_spans(rendered)
    visible = _replace_inline_markdown_links_with_labels(visible)
    visible = AUTOLINK_PATTERN.sub(lambda match: match.group("url"), visible)
    visible = _visible_html_text(visible)
    visible = html.unescape(visible)
    visible = visible.replace("**", "").replace("__", "")
    visible = visible.replace("*", "").replace("_", "")
    return " ".join(visible.split())

def _normalise_https_destination(candidate: str) -> str | None:
    value = candidate.strip().strip("<>").rstrip(".,;:!?")
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return None

    parsed_hostname = parsed.hostname
    if (
        parsed.scheme != "https"
        or not parsed_hostname
        or parsed.username is not None
        or parsed.password is not None
        or port is not None and port <= 0
    ):
        return None

    hostname = parsed_hostname.rstrip(".").lower()
    if not hostname or not any(character.isalnum() for character in hostname):
        return None

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        if not address.is_global:
            return None
    else:
        if any(
            hostname == suffix or hostname.endswith(f".{suffix}")
            for suffix in SPECIAL_USE_HOST_SUFFIXES
        ):
            return None
        labels = hostname.split(".")
        if all(NUMERIC_HOST_LABEL_PATTERN.fullmatch(label) for label in labels):
            return None
        if len(labels) < 2:
            return None
        if not all(label and HOST_LABEL_PATTERN.fullmatch(label) for label in labels):
            return None

    return value


def _normalise_reference_label(value: str) -> str:
    """Apply CommonMark-style case-insensitive whitespace normalization."""
    return " ".join(html.unescape(value).split()).casefold()


@dataclass(frozen=True)
class MarkdownInlineLink:
    start: int
    end: int
    label: str
    destination: str
    image: bool


def _is_escaped_markdown_character(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _balanced_markdown_label_end(text: str, start: int) -> int | None:
    """Return the closing bracket for a balanced inline-link label."""
    depth = 1
    cursor = start + 1
    while cursor < len(text):
        character = text[cursor]
        if character in "\r\n":
            return None
        if character == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _inline_link_closing_paren(text: str, start: int) -> int | None:
    """Return the closing parenthesis for an inline link destination/title."""
    depth = 1
    cursor = start + 1
    quote: str | None = None
    angle = False
    top_level_space = False
    while cursor < len(text):
        character = text[cursor]
        if character in "\r\n":
            return None
        if character == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if quote is not None:
            if character == quote:
                quote = None
            cursor += 1
            continue
        if angle:
            if character == ">":
                angle = False
            cursor += 1
            continue
        if depth == 1 and character in " \t":
            top_level_space = True
            cursor += 1
            continue
        if depth == 1 and top_level_space and character in {"\"", "'"}:
            quote = character
            cursor += 1
            continue
        if depth == 1 and not top_level_space and character == "<":
            angle = True
            cursor += 1
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _inline_link_destination(inner: str) -> str | None:
    """Extract the destination while retaining the existing title contract."""
    value = inner.lstrip(" \t")
    if not value:
        return None

    if value.startswith("<"):
        close = value.find(">", 1)
        if close < 0:
            return None
        destination = value[1:close]
        remainder = value[close + 1:].strip()
    else:
        cursor = 0
        depth = 0
        while cursor < len(value):
            character = value[cursor]
            if character == "\\" and cursor + 1 < len(value):
                cursor += 2
                continue
            if character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    return None
                depth -= 1
            elif character in " \t" and depth == 0:
                break
            cursor += 1
        if depth != 0:
            return None
        destination = value[:cursor]
        remainder = value[cursor:].strip()

    if not destination:
        return None
    if remainder:
        quoted = (
            len(remainder) >= 2
            and remainder[0] in {"\"", "'"}
            and remainder[-1] == remainder[0]
        )
        parenthesized = (
            len(remainder) >= 2
            and remainder[0] == "("
            and remainder[-1] == ")"
        )
        if not (quoted or parenthesized):
            return None
    return destination


def _markdown_inline_links(text: str) -> tuple[MarkdownInlineLink, ...]:
    """Parse inline links with balanced nested square-bracket labels."""
    links: list[MarkdownInlineLink] = []
    cursor = 0
    while cursor < len(text):
        bracket = text.find("[", cursor)
        if bracket < 0:
            break
        if _is_escaped_markdown_character(text, bracket):
            cursor = bracket + 1
            continue

        label_end = _balanced_markdown_label_end(text, bracket)
        if label_end is None:
            cursor = bracket + 1
            continue
        paren_start = label_end + 1
        if paren_start >= len(text) or text[paren_start] != "(":
            cursor = label_end + 1
            continue
        paren_end = _inline_link_closing_paren(text, paren_start)
        if paren_end is None:
            cursor = label_end + 1
            continue
        destination = _inline_link_destination(text[paren_start + 1:paren_end])
        if destination is None:
            cursor = paren_end + 1
            continue

        image = (
            bracket > 0
            and text[bracket - 1] == "!"
            and not _is_escaped_markdown_character(text, bracket - 1)
        )
        start = bracket - 1 if image else bracket
        links.append(
            MarkdownInlineLink(
                start=start,
                end=paren_end + 1,
                label=text[bracket + 1:label_end],
                destination=destination,
                image=image,
            )
        )
        cursor = paren_end + 1
    return tuple(links)


def _replace_inline_markdown_links_with_labels(text: str) -> str:
    links = _markdown_inline_links(text)
    if not links:
        return text
    parts: list[str] = []
    cursor = 0
    for link in links:
        parts.append(text[cursor:link.start])
        parts.append(link.label)
        cursor = link.end
    parts.append(text[cursor:])
    return "".join(parts)


def _mask_inline_markdown_links(
    text: str,
    links: tuple[MarkdownInlineLink, ...],
) -> str:
    characters = list(text)
    for link in links:
        _mask_segment(characters, link.start, link.end)
    return "".join(characters)


def _usable_https_destinations(
    text: str,
    *,
    reference_scope: str | None = None,
) -> tuple[str, ...]:
    """Extract rendered links, resolving reference definitions at document scope."""
    structure = _mask_hidden_html_regions(_structural_registry_text(text))
    definition_source = text if reference_scope is None else reference_scope
    reference_structure = _mask_hidden_html_regions(
        _structural_registry_text(definition_source)
    )
    destinations: list[str] = []

    for candidate in _visible_html_links(structure):
        destination = _normalise_https_destination(candidate)
        if destination is not None:
            destinations.append(destination)

    inline_links = _markdown_inline_links(structure)
    for link in inline_links:
        if link.image:
            continue
        destination = _normalise_https_destination(link.destination.strip("<>"))
        if destination is not None:
            destinations.append(destination)
    structure_without_inline_links = _mask_inline_markdown_links(
        structure,
        inline_links,
    )

    definitions: dict[str, str] = {}
    for match in LINK_REFERENCE_DEFINITION_PATTERN.finditer(reference_structure):
        destination = _normalise_https_destination(
            match.group("destination").strip("<>")
        )
        if destination is None:
            continue
        definitions.setdefault(
            _normalise_reference_label(match.group("label")),
            destination,
        )

    for match in REFERENCE_LINK_PATTERN.finditer(structure_without_inline_links):
        if match.group("image"):
            continue
        reference = match.group("reference") or match.group("label")
        destination = definitions.get(_normalise_reference_label(reference))
        if destination is not None:
            destinations.append(destination)

    without_reference_links = REFERENCE_LINK_PATTERN.sub("", structure_without_inline_links)
    for match in SHORTCUT_REFERENCE_LINK_PATTERN.finditer(without_reference_links):
        if match.group("image"):
            continue
        destination = definitions.get(
            _normalise_reference_label(match.group("label"))
        )
        if destination is not None:
            destinations.append(destination)

    without_links = without_reference_links
    for match in AUTOLINK_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)

    without_links = AUTOLINK_PATTERN.sub("", without_links)
    for match in BARE_HTTPS_LINE_PATTERN.finditer(without_links):
        destination = _normalise_https_destination(match.group("url"))
        if destination is not None:
            destinations.append(destination)

    return tuple(destinations)


def _registered_batch(corpus: str) -> str:
    rendered, structure = _markdown_views(corpus)
    start = structure.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = structure.index(BATCH_END, start)
    return rendered[start:end]


def _registered_sections(corpus: str) -> dict[str, str]:
    batch = _registered_batch(corpus)
    rendered, structure = _markdown_views(batch)
    visible_rendered = _mask_hidden_html_regions(rendered)
    visible_structure = _mask_hidden_html_regions(structure)
    matches: list[tuple[int, int, str]] = []
    offset = 0
    for raw_line in visible_structure.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        logical, is_code = _strip_composed_container_prefixes(line)
        if not is_code:
            heading_match = re.fullmatch(
                r" {0,3}(?P<heading>### .+?)[ \t]*",
                logical,
            )
            if heading_match:
                matches.append(
                    (
                        offset,
                        offset + len(line),
                        heading_match.group("heading"),
                    )
                )
        offset += len(raw_line)
    for match in HTML_ENTRY_HEADING_PATTERN.finditer(visible_structure):
        visible_heading = _visible_inline_text(
            visible_rendered[match.start():match.end()]
        )
        if visible_heading:
            matches.append((match.start(), match.end(), f"### {visible_heading}"))
    matches.sort(key=lambda item: item[0])
    assert matches, "registered post-Phase-2 batch contains no entries"

    headings = [heading for _, _, heading in matches]
    duplicates = sorted(
        heading for heading, count in Counter(headings).items() if count > 1
    )
    assert not duplicates, f"duplicate registered-entry headings: {duplicates}"

    sections: dict[str, str] = {}
    for index, (start, _heading_end, heading) in enumerate(matches):
        end = matches[index + 1][0] if index + 1 < len(matches) else len(batch)
        sections[heading] = rendered[start:end]
    return sections


def _strip_composed_container_prefixes(line: str) -> tuple[str, bool]:
    """Strip recursively composed quote/list prefixes and detect code indentation."""
    logical, is_code, _ = _parse_composed_container_prefixes(line)
    return logical, is_code


def _canonicalise_metadata_marker(line: str) -> str:
    """Canonicalise equivalent browser-rendered metadata labels."""
    # CommonMark resolves character references before rendering inline text.
    # Decode the candidate line before matching so `DOI&#58;` is the same
    # visible label as `DOI:` for uniqueness and scalar extraction.
    decoded = html.unescape(line)
    match = STRONG_METADATA_FIELD_PATTERN.match(decoded)
    if match:
        canonical = f"**{match.group('label')}:**"
        return canonical + decoded[match.end():]

    html_match = HTML_STRONG_METADATA_FIELD_PATTERN.match(decoded)
    if html_match:
        rendered_label = _visible_html_text(html_match.group(0)).strip()
        if rendered_label.endswith(":"):
            label = rendered_label[:-1].strip()
            if label and ":" not in label:
                canonical = f"**{label}:**"
                return canonical + decoded[html_match.end():]
    return line


def _normalised_rendered_lines(section: str) -> list[tuple[str, str, bool]]:
    """Return structural/rendered logical lines with list continuations preserved."""
    rendered, structure = _markdown_views(section)
    rendered_lines = rendered.splitlines()
    structure_lines = structure.splitlines()
    assert len(rendered_lines) == len(structure_lines)

    records: list[tuple[str, str, bool]] = []
    active_list_indent: int | None = None
    for rendered_line, structure_line in zip(rendered_lines, structure_lines):
        if not structure_line.strip():
            records.append(("", "", False))
            continue

        index, columns = _indent_columns(structure_line)
        marker = (
            LIST_CONTAINER_PREFIX_PATTERN.match(structure_line, index)
            if columns <= 3
            else None
        )
        if marker is not None:
            active_list_indent = columns + len(marker.group(0).expandtabs(4))
        elif active_list_indent is not None and columns < active_list_indent:
            active_list_indent = None

        logical, is_code = _strip_composed_container_prefixes(structure_line)
        rendered_logical, rendered_is_code = _strip_composed_container_prefixes(
            rendered_line
        )
        if (
            is_code
            and active_list_indent is not None
            and columns >= active_list_indent
            and columns - active_list_indent < 4
        ):
            logical = structure_line[index:]
            rendered_index, _ = _indent_columns(rendered_line)
            rendered_logical = rendered_line[rendered_index:]
            is_code = False
            rendered_is_code = False

        logical = _canonicalise_metadata_marker(logical.lstrip(" \t"))
        rendered_logical = _canonicalise_metadata_marker(
            rendered_logical.lstrip(" \t")
        )
        records.append((logical, rendered_logical, False))
    return records


def _metadata_field_count(section: str, fields: tuple[str, ...]) -> int:
    count = 0
    for logical, _, is_code in _normalised_rendered_lines(section):
        if is_code:
            continue
        for field in fields:
            if logical.startswith(field):
                suffix = logical[len(field):]
                if not suffix or suffix[0] in " \t":
                    count += 1
                    break
    return count


def _scalar_field_records(section: str, field: str) -> list[tuple[str, str]]:
    records = _normalised_rendered_lines(section)
    values: list[tuple[str, str]] = []
    for index, (logical, rendered_logical, is_code) in enumerate(records):
        if is_code or not logical.startswith(field):
            continue
        suffix = logical[len(field):]
        if suffix and suffix[0] not in " \t":
            continue
        if not rendered_logical.startswith(field):
            continue

        raw_parts = [rendered_logical[len(field):].strip()]
        cursor = index + 1
        while cursor < len(records):
            next_logical, next_rendered, next_is_code = records[cursor]
            stripped = next_logical.strip()
            if not stripped or next_is_code:
                break
            if re.match(r"\*\*[^*]+:\*\*", stripped):
                break
            if re.match(r"#{1,6}(?:[ \t]+|$)", stripped):
                break
            if stripped in {
                "Candidate research mappings:",
                "Research mappings:",
                "Relevant project mappings:",
            }:
                break
            if THEMATIC_BREAK_PATTERN.fullmatch(stripped):
                break
            raw_parts.append(next_rendered.strip())
            cursor += 1

        raw_value = " ".join(part for part in raw_parts if part)
        values.append((_visible_inline_text(raw_value), raw_value))
    return values


def _visible_scalar_values(section: str, field: str) -> list[str]:
    return [visible for visible, _ in _scalar_field_records(section, field)]


def _scalar_markdown_value(entry: str, section: str, field: str) -> str:
    records = _scalar_field_records(section, field)
    assert len(records) == 1, f"{entry} must contain exactly one mandatory field {field}"
    visible, raw = records[0]
    assert visible, f"{entry} has an empty mandatory field {field}"
    return raw

def _scalar_value(entry: str, section: str, field: str) -> str:
    values = _visible_scalar_values(section, field)
    assert len(values) == 1, (
        f"{entry} must contain exactly one mandatory field {field}"
    )
    value = values[0]
    assert value, f"{entry} has an empty mandatory field {field}"
    return value

def _require_scalar_value(entry: str, section: str, field: str) -> None:
    _scalar_value(entry, section, field)



def _has_non_heading_content(block: str) -> bool:
    rendered = _rendered_registry_text(block)
    fence: FenceState | None = None

    for raw_line in rendered.splitlines():
        while fence is not None and not _fence_container_continues(raw_line, fence):
            fence = None

        if fence is not None:
            if _is_fence_closer(raw_line, fence):
                fence = None
                continue
            if _visible_inline_text(_fence_logical_line(raw_line, fence).strip()):
                return True
            continue

        opener = _fence_opener(raw_line)
        if opener is not None:
            fence = opener
            continue

        logical, is_code = _strip_composed_container_prefixes(raw_line)
        line = logical.strip()
        if not line:
            continue
        if THEMATIC_BREAK_PATTERN.fullmatch(line):
            continue
        if re.fullmatch(r"(?:Candidate research mappings:|Research mappings:)", line):
            continue
        if line == "Relevant project mappings:":
            continue
        if re.fullmatch(r"#{1,6}[ \t]+.+", line):
            continue
        if re.fullmatch(r"(?:[-+*]|\d{1,9}[.)])", line):
            continue
        if re.fullmatch(r"\*\*[^*]+:\*\*(?:[ \t].*)?", line):
            continue
        if LINK_REFERENCE_DEFINITION_PATTERN.fullmatch(line):
            continue
        if _visible_inline_text(line):
            return True

    return False


def _require_mapping_block(entry: str, section: str) -> None:
    normalised = _normalised_rendered_lines(section)
    research_count = sum(
        1
        for logical, _, is_code in normalised
        if not is_code and logical.strip() in {"Candidate research mappings:", "Research mappings:"}
    )
    project_count = sum(
        1
        for logical, _, is_code in normalised
        if not is_code and logical.strip() == "Relevant project mappings:"
    )
    assert research_count == 1, f"{entry} must contain exactly one research mappings heading"
    assert project_count == 1, f"{entry} must contain exactly one relevant project mappings heading"

    rendered, structure = _markdown_views(section)
    research_headings = list(RESEARCH_MAPPING_HEADING_PATTERN.finditer(structure))
    project_headings = list(PROJECT_MAPPING_HEADING_PATTERN.finditer(structure))
    assert len(research_headings) == 1 and len(project_headings) == 1

    research_start = research_headings[0].end()
    project_start = project_headings[0].start()
    assert research_start < project_start, f"{entry} has research/project mapping headings in the wrong order"
    assert _has_non_heading_content(rendered[research_start:project_start]), f"{entry} has empty research mappings"

    safe_heading = re.search(
        rf"(?m)^ {{0,3}}{re.escape(SAFE_FIELD)}",
        structure[project_headings[0].end():],
    )
    assert safe_heading, f"{entry} is missing the safe benchmark abstraction field"
    project_value_start = project_headings[0].end()
    project_end = project_value_start + safe_heading.start()
    assert _has_non_heading_content(rendered[project_value_start:project_end]), f"{entry} has empty project mappings"


def _require_registered_source_link(
    entry: str,
    section: str,
    *,
    reference_scope: str | None = None,
) -> tuple[str, ...]:
    source_count = _metadata_field_count(
        section,
        ("**Registered source:**", "**Registered sources:**"),
    )
    assert source_count == 1, f"{entry} must contain exactly one registered-source field"

    rendered, structure = _markdown_views(section)
    source_block = re.search(
        r"(?ms)^[ \t]*\*\*Registered sources?:\*\*(.*?)"
        r"(?=^[ \t]*\*\*[^*\n]+:\*\*|\Z)",
        structure,
    )
    assert source_block, f"{entry} has an empty registered-source field"
    source_value = rendered[source_block.start(1):source_block.end(1)]
    assert _visible_inline_text(source_value), f"{entry} has an empty registered-source field"

    destinations = _usable_https_destinations(
        source_value,
        reference_scope=reference_scope,
    )
    assert destinations, f"{entry} has no usable HTTPS destination in its registered-source field"
    assert len(destinations) == len(set(destinations)), f"{entry} contains duplicate registered-source destinations"
    return destinations



def _require_community_governance(entry: str, section: str) -> str:
    field_count = _metadata_field_count(section, ("**Community-specific governance:**",))
    assert field_count == 1, f"{entry} must contain exactly one community-specific governance field"

    rendered, structure = _markdown_views(section)
    classification = GOVERNANCE_PATTERN.search(structure)
    assert classification, f"{entry} has an invalid community-specific governance classification or rationale"
    raw_rationale = rendered[classification.start("rationale"):classification.end("rationale")]
    rationale = _visible_inline_text(raw_rationale)
    assert rationale, f"{entry} has an invalid community-specific governance classification or rationale"

    expected_hash = GOVERNANCE_RATIONALE_HASHES.get(entry)
    if expected_hash is not None:
        actual_hash = hashlib.sha256(rationale.encode("utf-8")).hexdigest()
        assert actual_hash == expected_hash, (
            f"{entry} changed pinned community-governance rationale: "
            f"expected hash {expected_hash!r}, got {actual_hash!r}"
        )

    value = classification.group(1)
    if value == "required":
        safe_use = _scalar_value(entry, section, SAFE_FIELD)
        assert CONSULTATION_BOUNDARY in safe_use, (
            f"{entry} is missing its community-specific consultation boundary "
            "from the safe benchmark abstraction field"
        )
    return value


def _require_pinned_entry_contract(
    entry: str,
    *,
    classification: str,
    scalar_values: dict[str, str],
    destinations: tuple[str, ...],
) -> None:
    contract = ENTRY_CONTRACTS.get(entry)
    assert contract is not None, f"{entry} has no pinned source-governance contract"
    expected_classification = contract["governance"]
    assert classification == expected_classification, f"{entry} must remain classified as {expected_classification}"

    expected_destinations = set(contract[SOURCES_KEY])
    actual_destinations = set(destinations)
    assert actual_destinations == expected_destinations, (
        f"{entry} registered-source destinations changed: "
        f"expected {sorted(expected_destinations)!r}, got {sorted(actual_destinations)!r}"
    )

    for field in SCALAR_FIELDS:
        expected_clause = _visible_inline_text(str(contract[field]))
        actual_value = scalar_values[field]
        assert expected_clause in actual_value, (
            f"{entry} is missing a pinned {field} clause or changed its accepted value: "
            f"{expected_clause!r}"
        )
        if field == SOURCE_TYPE_FIELD:
            actual_hash = hashlib.sha256(actual_value.encode("utf-8")).hexdigest()
            expected_hash = SOURCE_TYPE_VALUE_HASHES[entry]
            assert actual_hash == expected_hash, (
                f"{entry} changed pinned {field}: expected hash "
                f"{expected_hash!r}, got {actual_hash!r}"
            )
        elif field in BOUNDARY_FIELDS:
            actual_hash = hashlib.sha256(actual_value.encode("utf-8")).hexdigest()
            expected_hash = BOUNDARY_VALUE_HASHES[entry][field]
            assert actual_hash == expected_hash, (
                f"{entry} changed pinned {field}: expected hash "
                f"{expected_hash!r}, got {actual_hash!r}"
            )

def _validate_registered_entry(
    entry: str,
    section: str,
    *,
    reference_scope: str | None = None,
) -> None:
    destinations = _require_registered_source_link(
        entry,
        section,
        reference_scope=reference_scope,
    )
    scalar_values = {field: _scalar_value(entry, section, field) for field in SCALAR_FIELDS}
    contract = ENTRY_CONTRACTS.get(entry)
    assert contract is not None, f"{entry} has no pinned source-governance contract"
    if DOI_FIELD in contract:
        expected_doi = str(contract[DOI_FIELD])
        doi_value = _scalar_value(entry, section, DOI_FIELD)
        assert doi_value == expected_doi, (
            f"{entry} DOI metadata changed: expected {expected_doi!r}, got {doi_value!r}"
        )
        raw_doi = _scalar_markdown_value(entry, section, DOI_FIELD)
        doi_destinations = _usable_https_destinations(raw_doi)
        assert doi_destinations == (expected_doi,), (
            f"{entry} DOI hyperlink destination changed: expected {(expected_doi,)!r}, "
            f"got {doi_destinations!r}"
        )
    else:
        assert not _visible_scalar_values(section, DOI_FIELD), f"{entry} has unpinned DOI metadata"
    classification = _require_community_governance(entry, section)
    _require_pinned_entry_contract(
        entry,
        classification=classification,
        scalar_values=scalar_values,
        destinations=destinations,
    )
    _require_mapping_block(entry, section)


def _validate_registry_corpus(corpus: str) -> None:
    rendered, structure = _markdown_views(corpus)
    assert CONTRACT_HEADING in structure, "rendered registration contract is missing"
    contract_start = structure.index(CONTRACT_HEADING)
    assert BATCH_HEADING in structure[contract_start:], "rendered governed batch heading is missing"
    contract_end = structure.index(BATCH_HEADING, contract_start)
    contract_section = structure[contract_start:contract_end]
    assert CONTRACT_SENTENCE in contract_section, "rendered registration contract is incomplete"
    visible_contract = _visible_inline_text(rendered[contract_start:contract_end])
    actual_contract_hash = hashlib.sha256(visible_contract.encode("utf-8")).hexdigest()
    assert actual_contract_hash == REGISTRATION_CONTRACT_HASH, (
        "rendered registration contract changed or was weakened: "
        f"expected hash {REGISTRATION_CONTRACT_HASH!r}, got {actual_contract_hash!r}"
    )
    assert "RESEARCH REFERENCE != REDISTRIBUTABLE DATA" in structure

    sections = _registered_sections(corpus)
    assert set(sections) == set(ENTRY_CONTRACTS), (
        "every rendered governed entry must have an explicit pinned source contract"
    )
    for entry, section in sections.items():
        _validate_registered_entry(
            entry,
            section,
            reference_scope=corpus,
        )

def test_post_phase2_registry_batch_preserves_governance_contract():
    _validate_registry_corpus(CORPUS.read_text(encoding="utf-8"))


def test_registered_source_resolves_document_scoped_reference_definition():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    marker = (
        "**Registered source:**"
        if "**Registered source:**" in section
        else "**Registered sources:**"
    )
    mutated_section = section.replace(
        marker,
        f"{marker} [alternate][external-provenance]\n",
        1,
    )
    mutated = (
        corpus.replace(section, mutated_section, 1)
        + "\n[external-provenance]: https://www.wikipedia.org/\n"
    )

    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registry_corpus(mutated)


def test_registered_source_resolves_multiline_document_reference_definition():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    marker = (
        "**Registered source:**"
        if "**Registered source:**" in section
        else "**Registered sources:**"
    )
    mutated_section = section.replace(
        marker,
        f"{marker} [alternate][multiline-provenance]\n",
        1,
    )
    mutated = (
        corpus.replace(section, mutated_section, 1)
        + "\n[multiline-provenance]:\n  https://www.wikipedia.org/\n"
    )

    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registry_corpus(mutated)


@pytest.mark.parametrize("prefix", ("> ", "- "))
def test_registry_discovers_entry_heading_inside_markdown_container(prefix: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    fabricated = (
        f"{prefix}### Fabricated ungoverned reference\n"
        f"{prefix}placeholder provenance prose\n\n"
    )
    mutated = corpus.replace(BATCH_END, fabricated + BATCH_END, 1)
    assert "### Fabricated ungoverned reference" in _registered_sections(mutated)
    with pytest.raises(
        AssertionError,
        match="every rendered governed entry must have an explicit pinned source contract",
    ):
        _validate_registry_corpus(mutated)


@pytest.mark.parametrize("wrapper", ("comment", "fence"))
def test_registration_contract_must_remain_rendered(wrapper: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(CONTRACT_HEADING)
    end = corpus.index(BATCH_HEADING, start)
    contract = corpus[start:end]
    if wrapper == "comment":
        hidden = f"<!--\n{contract}\n-->\n"
    else:
        hidden = f"````\n{contract}\n````\n"
    mutated = corpus[:start] + hidden + corpus[end:]
    with pytest.raises(AssertionError, match="rendered registration contract"):
        _validate_registry_corpus(mutated)


@pytest.mark.parametrize("wrapper", ("comment", "fence"))
def test_registry_discovery_ignores_hidden_complete_entry(wrapper: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    heading = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[heading]
    hidden = (
        f"<!--\n{section}\n-->\n"
        if wrapper == "comment"
        else f"````\n{section}\n````\n"
    )
    mutated = corpus.replace(section, hidden, 1)
    assert heading not in _registered_sections(mutated)


def test_registry_fields_ignore_fenced_and_inline_code_metadata():
    fenced = (
        "### Example\n\n```\n"
        "**Registered source:** https://example.com/source\n"
        "```\n\n**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", fenced)

    inline = (
        "### Example\n\n"
        "**Registered source:** `[source](https://example.com/source)`\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _require_registered_source_link("### Example", inline)


def test_indented_code_comment_opener_does_not_hide_visible_duplicate():
    section = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "    <!--\n"
        "**Registered source:** https://example.com/other\n"
        "    -->\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


def test_fenced_comment_literals_do_not_hide_visible_duplicate():
    section = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "```text\n<!--\n```\n\n"
        "**Registered source:** https://example.com/other\n\n"
        "```text\n-->\n```\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


@pytest.mark.parametrize(
    "opener, closer",
    (("- ```", "  ```"), ("> ```", "> ```")),
)
def test_nested_fence_ends_when_its_container_ends(opener: str, closer: str):
    section = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        f"{opener}\n"
        "**Registered source:** https://example.com/other\n"
        f"{closer}\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


@pytest.mark.parametrize(
    ("section", "field", "message"),
    (
        (
            "### Example\n\n**Source type:**\n\n"
            "**Rights and provenance boundary:** value\n",
            SOURCE_TYPE_FIELD,
            "empty mandatory field",
        ),
        (
            "### Example\n\n"
            "**Rights and provenance boundary:** restrictive value\n\n"
            "**Rights and provenance boundary:** replacement\n",
            RIGHTS_FIELD,
            "exactly one mandatory field",
        ),
        (
            "### Example\n\n"
            "**Rights and provenance boundary:** <!-- omitted -->\n",
            RIGHTS_FIELD,
            "empty mandatory field",
        ),
        (
            "### Example\n\n"
            "**Rights and provenance boundary:** <!-- hidden value -->\n",
            RIGHTS_FIELD,
            "empty mandatory field",
        ),
    ),
)
def test_scalar_field_fail_closed(section: str, field: str, message: str):
    with pytest.raises(AssertionError, match=message):
        _require_scalar_value("### Example", section, field)


@pytest.mark.parametrize(
    "section",
    (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "**Registered sources:** https://example.com/other\n\n"
        "**Source type:** example\n",
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n\n"
        "   **Registered source:** https://example.com/other\n\n"
        "**Source type:** example\n",
    ),
)
def test_registered_source_rejects_duplicate_fields(section: str):
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", section)


@pytest.mark.parametrize(
    "destination",
    (
        "[source](# \"https://example.com\")",
        "https://.",
        "https://localhost",
        "https://example",
        "https://127.0.0.1",
        "https://10.0.0.1",
        "https://192.168.1.1",
        "https://[::1]",
        "https://127.1",
        "https://127.0.0.01",
        "https://0x7f.0.0.1",
        "https://source.invalid",
        "https://source.test",
        "https://source.example",
        "https://router.local",
        "https://host.home.arpa",
        "![source](https://example.com/source)",
    ),
)
def test_registered_source_rejects_unusable_destinations(destination: str):
    section = (
        "### Example\n\n"
        f"**Registered source:** {destination}\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _require_registered_source_link("### Example", section)


@pytest.mark.parametrize(
    "container",
    (
        "-",
        "***",
        "___",
        "* * *",
        "_ _ _",
        "---",
        "- - -",
        ">",
        "> >",
        "```\n```",
        "```text\n```",
        "~~~\n~~~",
        "> ```\n> ```",
        "- ```\n  ```",
        "1. ~~~\n   ~~~",
        "> - ```\n>   ```",
        "<br>",
        "<div></div>",
        "&nbsp;",
        "<span> &nbsp; </span>",
        "- <!-- placeholder -->",
        "<!--\n- placeholder\n-->",
        "[placeholder]: https://example.com",
    ),
)
def test_mapping_blocks_reject_empty_rendered_content(container: str):
    section = (
        "### Example\n\n"
        f"Research mappings:\n{container}\n\n"
        f"Relevant project mappings:\n{container}\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="empty research mappings"):
        _require_mapping_block("### Example", section)


def test_mapping_blocks_accept_real_nested_fence_and_html_content():
    section = (
        "### Example\n\n"
        "Research mappings:\n"
        "- ```text\n"
        "  substantive mapping\n"
        "  ```\n\n"
        "Relevant project mappings:\n"
        "> <div>project mapping</div>\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    _require_mapping_block("### Example", section)


def test_required_entry_cannot_downgrade_community_governance():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Community-specific governance:** required:",
        "**Community-specific governance:** not-required:",
        1,
    ).replace(CONSULTATION_BOUNDARY, "documented scope review", 1)
    with pytest.raises(AssertionError, match="must remain classified as required"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        (RIGHTS_FIELD, "No restrictions; copy all dialogue."),
        (EPISTEMIC_FIELD, "Objective cultural ground truth."),
        (SAFE_FIELD, "Reproduce programme jokes verbatim."),
    ),
)
def test_source_specific_boundary_clauses_are_pinned(
    field: str,
    replacement: str,
):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Shaun Micallef's MAD AS HELL*"
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^ {{0,3}}{re.escape(field)}[^\r\n]*$",
        f"{field} {replacement}",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="missing a pinned"):
        _validate_registered_entry(entry, mutated)


def test_pinned_clause_cannot_hide_in_markdown_link_title():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    expected = str(ENTRY_CONTRACTS[entry][SOURCE_TYPE_FIELD])
    mutated = re.sub(
        rf"(?m)^ {{0,3}}{re.escape(SOURCE_TYPE_FIELD)}[^\r\n]*$",
        f'{SOURCE_TYPE_FIELD} [unknown](# "{expected}")',
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="missing a pinned"):
        _validate_registered_entry(entry, mutated)


def test_registered_source_destination_set_is_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "https://iview.abc.net.au/show/black-comedy",
        "https://www.wikipedia.org/",
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_multisource_entry_cannot_drop_an_adopted_destination():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *The Castle* (1997)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "- https://www.nfsa.gov.au/collection/item/castle-fathers-day\n",
        "",
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_community_governance_requires_visible_same_line_rationale():
    missing = (
        "### Example\n\n"
        "**Community-specific governance:** not-required:\n\n"
        "Candidate research mappings:\n- example\n"
    )
    with pytest.raises(AssertionError, match="invalid community-specific governance"):
        _require_community_governance("### Example", missing)

    hidden = (
        "### Example\n\n"
        "**Community-specific governance:** not-required: <!-- hidden -->\n"
    )
    with pytest.raises(AssertionError, match="invalid community-specific governance"):
        _require_community_governance("### Example", hidden)

def test_inline_code_remains_visible_field_text_but_not_a_link():
    scalar = (
        "### Example\n\n"
        "**Rights and provenance boundary:** `visible value`\n"
    )
    assert _scalar_value("### Example", scalar, RIGHTS_FIELD) == "visible value"

    governance = (
        "### Example\n\n"
        "**Community-specific governance:** not-required: `visible rationale`\n"
    )
    assert _require_community_governance("### Example", governance) == "not-required"

    source = (
        "### Example\n\n"
        "**Registered source:** `[source](https://example.com/source)`\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="no usable HTTPS destination"):
        _require_registered_source_link("### Example", source)

def test_paragraph_continuation_cannot_hide_indented_metadata():
    duplicate_source = (
        "### Example\n\n"
        "**Registered source:** https://example.com/source\n"
        "    **Registered source:** https://example.com/other\n\n"
        "**Source type:** example\n"
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _require_registered_source_link("### Example", duplicate_source)

    duplicate_scalar = (
        "### Example\n\n"
        "**Rights and provenance boundary:** restrictive value\n"
        "    **Rights and provenance boundary:** contradictory value\n"
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _scalar_value("### Example", duplicate_scalar, RIGHTS_FIELD)


def test_published_doi_metadata_is_pinned_and_unique():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    fake = section.replace(
        "https://doi.org/10.7592/EJHR2021.9.4.560",
        "https://doi.org/10.0000/invented",
        1,
    )
    with pytest.raises(AssertionError, match="DOI metadata changed"):
        _validate_registered_entry(entry, fake)

    duplicate = section.replace(
        "**Source type:**",
        "**DOI:** https://doi.org/10.0000/conflict\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, duplicate)


@pytest.mark.parametrize(
    "duplicate",
    (
        "> **DOI:** https://doi.org/10.0000/conflict",
        "- **DOI:** https://doi.org/10.0000/conflict",
    ),
)
def test_published_doi_rejects_rendered_container_duplicates(duplicate: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        f"{duplicate}\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)



def test_compound_container_duplicate_doi_is_rejected():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        "- > **DOI:** https://doi.org/10.0000/conflict\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_multiline_code_span_comment_literal_cannot_hide_visible_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    injected = (
        "prefix `\n"
        "<!--\n"
        "code`\n"
        "**DOI:** https://doi.org/10.0000/conflict\n"
        "-->\n\n"
        "**Source type:**"
    )
    mutated = section.replace("**Source type:**", injected, 1)
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize(
    "container",
    (
        "<script>placeholder</script>",
        "<style>.placeholder { display: none; }</style>",
        "<template>placeholder</template>",
    ),
)
def test_mapping_blocks_reject_nonrendering_html_contents(container: str):
    section = (
        "### Example\n\n"
        f"Research mappings:\n{container}\n\n"
        f"Relevant project mappings:\n{container}\n\n"
        "**Safe benchmark abstraction:** example\n"
    )
    with pytest.raises(AssertionError, match="empty research mappings"):
        _require_mapping_block("### Example", section)


def test_pinned_boundary_rejects_contradictory_addition():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Shaun Micallef's MAD AS HELL*"
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^ {{0,3}}{re.escape(RIGHTS_FIELD)}(?P<value>[^\r\n]*)$",
        lambda match: match.group(0)
        + " Contradictory override: programme dialogue may be copied into benchmark data.",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="changed pinned"):
        _validate_registered_entry(entry, mutated)



def test_tab_indented_comment_cannot_hide_duplicate_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))
    section = _registered_sections(corpus)[entry]
    doi = str(ENTRY_CONTRACTS[entry][DOI_FIELD])
    mutated = section.replace(
        f"{DOI_FIELD} {doi}",
        f"{DOI_FIELD} {doi}\n\n\t<!--\n{DOI_FIELD} https://doi.org/10.0000/conflict\n\t-->",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_list_continuation_indent_cannot_hide_duplicate_doi():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))
    section = _registered_sections(corpus)[entry]
    doi = str(ENTRY_CONTRACTS[entry][DOI_FIELD])
    mutated = section.replace(
        f"{DOI_FIELD} {doi}",
        f"{DOI_FIELD} {doi}\n\n- container\n\n    {DOI_FIELD} https://doi.org/10.0000/conflict",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_hidden_html_cannot_supply_registry_values_or_mappings():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^({re.escape(RIGHTS_FIELD)}[ \t]*)(.+)$",
        lambda match: match.group(1) + "<span hidden>" + match.group(2) + "</span>",
        section,
        count=1,
    )
    with pytest.raises(AssertionError):
        _validate_registered_entry(entry, mutated)
    assert not _has_non_heading_content('<div hidden>placeholder</div>')


def test_registered_source_duplicate_in_container_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        r"(?m)^(\*\*Registered source:\*\*[^\n]*)$",
        r"\1\n> **Registered source:** https://www.wikipedia.org/",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="exactly one registered-source field"):
        _validate_registered_entry(entry, mutated)


def test_doi_link_destination_is_pinned_as_well_as_visible_label():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))
    section = _registered_sections(corpus)[entry]
    doi = str(ENTRY_CONTRACTS[entry][DOI_FIELD])
    mutated = section.replace(
        f"{DOI_FIELD} {doi}",
        f"{DOI_FIELD} [{doi}](https://doi.org/10.0000/fabricated)",
        1,
    )
    with pytest.raises(AssertionError, match="DOI hyperlink destination changed"):
        _validate_registered_entry(entry, mutated)


def test_registration_contract_clauses_are_section_scoped():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(CONTRACT_HEADING)
    end = corpus.index(BATCH_HEADING, start)
    contract = corpus[start:end]
    mutated_contract = contract.replace(CONTRACT_SENTENCE, "mandatory fields are listed below", 1)
    mutated = corpus[:start] + mutated_contract + corpus[end:] + "\n" + CONTRACT_SENTENCE + "\n"
    with pytest.raises(AssertionError, match="registration contract is incomplete"):
        _validate_registry_corpus(mutated)


def test_governance_rationale_is_fully_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        r"(?m)^(\*\*Community-specific governance:\*\* required:[^\n]*)$",
        r"\1 Contradictory override: no consultation, provenance, permissions, or scope limitations are required.",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="governance rationale"):
        _validate_registered_entry(entry, mutated)


def test_source_type_complete_value_is_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^({re.escape(SOURCE_TYPE_FIELD)}[^\n]*)$",
        r"\1 Contradictory override: unverified anonymous post with no pragmatic relevance.",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="changed pinned"):
        _validate_registered_entry(entry, mutated)


def test_boundary_hash_includes_paragraph_continuations():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Shaun Micallef's MAD AS HELL*"
    section = _registered_sections(corpus)[entry]
    mutated = re.sub(
        rf"(?m)^({re.escape(RIGHTS_FIELD)}[^\n]*)$",
        r"\1\nContradictory continuation: programme dialogue may be freely copied into benchmark data.",
        section,
        count=1,
    )
    with pytest.raises(AssertionError, match="changed pinned"):
        _validate_registered_entry(entry, mutated)


def test_mapping_content_normalises_compound_containers():
    assert not _has_non_heading_content("- > ---\n")


def test_equivalent_strong_emphasis_doi_field_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560",
        "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560\n\n"
        "__DOI:__ https://doi.org/10.0000/fabricated",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize(
    ("opener", "closer"),
    (
        ("***", "***"),
        ("___", "___"),
        ("**_", "_**"),
        ("__*", "*__"),
        ("*__", "__*"),
        ("_**", "**_"),
    ),
)
def test_nested_emphasis_doi_field_is_counted(opener: str, closer: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*"
    section = _registered_sections(corpus)[entry]
    expected = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"
    mutated = section.replace(
        expected,
        expected
        + f"\n\n{opener}DOI:{closer} https://doi.org/10.0000/fabricated",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_compound_container_fence_cannot_hide_scalar_metadata():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    rights_line = next(
        line for line in section.splitlines()
        if line.startswith(RIGHTS_FIELD)
    )
    mutated = section.replace(
        rights_line,
        f"- > ```\n  > {rights_line}\n  > ```",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize("tag", ["strong", "b"])
def test_html_strong_doi_field_is_counted(tag: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*"
    section = _registered_sections(corpus)[entry]
    expected = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"
    mutated = section.replace(
        expected,
        expected + f"\n\n<{tag}>DOI:</{tag}> https://doi.org/10.0000/fabricated",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize(
    "markup",
    (
        "<strong><em>DOI:</em></strong>",
        "<b><i>DOI:</i></b>",
    ),
)
def test_nested_html_strong_doi_field_is_counted(markup: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### Chey (2021), *Overcoming awkwardness: some interpretations of Australian humour*"
    section = _registered_sections(corpus)[entry]
    expected = "**DOI:** https://doi.org/10.7592/EJHR2021.9.4.560"
    mutated = section.replace(
        expected,
        expected + f"\n\n{markup} https://doi.org/10.0000/fabricated",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated, reference_scope=corpus)


def test_registration_contract_explicitly_bounds_community_attestation():
    corpus = CORPUS.read_text(encoding="utf-8")
    structure = _structural_registry_text(corpus)
    start = structure.index(CONTRACT_HEADING)
    end = structure.index(BATCH_HEADING, start)
    contract = structure[start:end]
    assert "explicitly bounded community-attestation source links" in contract
    assert "user-generated, non-representative orientation or attestation material" in contract
    assert "cannot establish prevalence" in contract



def test_registry_discovery_detects_rendered_html_h3_entry():
    corpus = CORPUS.read_text(encoding="utf-8")
    injected = (
        BATCH_HEADING
        + "\n\n<h3>Fabricated ungoverned reference</h3>\n\n"
        + "Arbitrary provenance prose.\n\n"
    )
    mutated = corpus.replace(BATCH_HEADING, injected, 1)
    sections = _registered_sections(mutated)
    assert "### Fabricated ungoverned reference" in sections
    with pytest.raises(AssertionError, match="every rendered governed entry"):
        _validate_registry_corpus(mutated)


def test_complete_registration_contract_is_pinned():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(CONTRACT_HEADING)
    end = corpus.index(BATCH_HEADING, start)
    contract = corpus[start:end]
    keep = contract.index(CONTRACT_SENTENCE) + len(CONTRACT_SENTENCE)
    weakened = contract[:keep] + "\n\nAll other requirements are optional.\n\n"
    mutated = corpus[:start] + weakened + corpus[end:]
    with pytest.raises(AssertionError, match="registration contract changed or was weakened"):
        _validate_registry_corpus(mutated)


def test_balanced_nested_markdown_link_destination_is_included_in_pinned_set():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        SOURCE_TYPE_FIELD,
        "[alternate [source]](https://www.wikipedia.org/)\n\n" + SOURCE_TYPE_FIELD,
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated, reference_scope=corpus)


def test_html_anchor_source_destination_is_included_in_pinned_set():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = EXPECTED_GOVERNED_ENTRIES[0]
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        SOURCE_TYPE_FIELD,
        '<a href="https://wikipedia.org/">alternate source</a>\n\n' + SOURCE_TYPE_FIELD,
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_hidden_html_container_cannot_hide_complete_governed_batch():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = corpus.index(BATCH_END, start)
    mutated = (
        corpus[:start]
        + "\n<div hidden>\n"
        + corpus[start:end]
        + "\n</div>\n"
        + corpus[end:]
    )
    with pytest.raises(AssertionError, match="registered post-Phase-2 batch contains no entries"):
        _validate_registry_corpus(mutated)


def test_closed_details_cannot_hide_complete_governed_batch():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = corpus.index(BATCH_END, start)
    mutated = (
        corpus[:start]
        + "\n<details>\n<summary>Governed references</summary>\n"
        + corpus[start:end]
        + "\n</details>\n"
        + corpus[end:]
    )
    with pytest.raises(AssertionError, match="registered post-Phase-2 batch contains no entries"):
        _validate_registry_corpus(mutated)


def test_open_details_keep_governed_batch_visible():
    corpus = CORPUS.read_text(encoding="utf-8")
    start = corpus.index(BATCH_HEADING) + len(BATCH_HEADING)
    end = corpus.index(BATCH_END, start)
    mutated = (
        corpus[:start]
        + "\n<details open>\n<summary>Governed references</summary>\n"
        + corpus[start:end]
        + "\n</details>\n"
        + corpus[end:]
    )
    _validate_registry_corpus(mutated)


def test_reference_style_source_destination_is_included_in_pinned_set():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        "[alternate][extra]\n[extra]: https://www.wikipedia.org/\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


@pytest.mark.parametrize(
    "reference",
    ("[alternate][]", "[alternate]"),
)
def test_collapsed_and_shortcut_reference_sources_are_resolved(reference: str):
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        f"{reference}\n[alternate]: https://www.wikipedia.org/\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_nested_fence_closer_allows_commonmark_indentation():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = next(name for name in ENTRY_CONTRACTS if name.startswith("### Chey"))
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        "> ```\n> inert code\n>   ```\n"
        "> **DOI:** https://doi.org/10.0000/conflict\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_entity_encoded_metadata_label_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = (
        "### Chey (2021), *Overcoming awkwardness: some interpretations of "
        "Australian humour*"
    )
    section = _registered_sections(corpus)[entry]
    mutated = section.replace(
        "**Source type:**",
        "**DOI&#58;** https://doi.org/10.0000/fabricated\n\n**Source type:**",
        1,
    )
    with pytest.raises(AssertionError, match="exactly one mandatory field"):
        _validate_registered_entry(entry, mutated)


def test_self_closing_anchor_source_destination_is_counted():
    corpus = CORPUS.read_text(encoding="utf-8")
    entry = "### *Black Comedy* (ABC, 2014-2020)"
    section = _registered_sections(corpus)[entry]
    pinned = "https://iview.abc.net.au/show/black-comedy"
    mutated = section.replace(
        pinned,
        pinned + ' <a href="https://www.wikipedia.org/" />alternate</a>',
        1,
    )
    with pytest.raises(AssertionError, match="registered-source destinations changed"):
        _validate_registered_entry(entry, mutated)


def test_closed_dialog_cannot_hide_complete_governed_batch():
    corpus = CORPUS.read_text(encoding="utf-8")
    batch = _registered_batch(corpus)
    mutated = corpus.replace(batch, f"<dialog>\n{batch}\n</dialog>\n", 1)
    with pytest.raises(AssertionError, match="contains no entries"):
        _validate_registry_corpus(mutated)


def test_open_dialog_keeps_governed_batch_visible():
    corpus = CORPUS.read_text(encoding="utf-8")
    batch = _registered_batch(corpus)
    mutated = corpus.replace(batch, f"<dialog open>\n{batch}\n</dialog>\n", 1)
    _validate_registry_corpus(mutated)
