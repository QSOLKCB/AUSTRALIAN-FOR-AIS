# Roadmap

This roadmap describes planned phases for the Australian For AIs project.

Phases are listed in order. No phase is marked complete until its graduation criteria are explicitly satisfied and documented. Future phases are not complete.

Planning reports, comedy/reference surveys, and external audits may inform this roadmap, but they are **research inputs rather than executable truth**. Recommendations are checked against the current repository before becoming project commitments, and stale status claims are not preserved merely because they appeared in an earlier report.

---

## Phase 1 — Research Substrate *(merged; external-researcher invariant review still pending)*

**Goal:** Establish the contracts, schemas, methodology, documentation, starter fixtures, reference evaluator, and tests needed for later dataset expansion.

**Deliverables:**
- Core invariants document (AU-HUMOUR-001 through AU-HUMOUR-010)
- JSON Schema for examples and evaluation records
- Synthetic starter dataset (~15 illustrative examples)
- Python data models and deterministic reference evaluator
- CLI for validation and evaluation
- Test suite (all offline)
- Ethics, methodology, annotation, and governance documentation
- Research reference corpus with explicit copyright, provenance, and epistemic-status boundaries
- Repository hygiene rules preventing generated local artefacts from entering the research record

**Graduation Criteria:**
- [x] All tests pass in CI
- [x] All starter examples validate against the schema
- [x] Research references are explicitly separated from redistributable benchmark data
- [x] No fabricated release/citation metadata remains in the Phase 1 branch
- [ ] Invariants reviewed by at least one researcher outside the initial author
- [x] PR reviewed and merged

Phase 1 code and documentation are merged, but the phase is not marked complete because the explicit external-researcher invariant review criterion remains open.

---

## Phase 2 — Pilot Human Annotation *(tooling merged in PR #2; human collection pending)*

**Goal:** Develop annotation tooling and conduct a small-scale pilot with real human annotators.

**Implementation status:** PR #2 merged a 60-item unannotated synthetic pilot pack, a self-contained offline annotation interface, strict per-annotator validation, locally generated pseudonymous annotation records, deterministic agreement analysis, a pilot protocol, and a mechanism-selection review. This does **not** claim that real human annotation or ethical review has already occurred.

**Deliverables:**
- [x] Offline annotation interface or workflow
- [x] Inter-annotator agreement analysis tools
- [x] 60-item unannotated synthetic pilot pack with 30 same-utterance context contrasts
- [ ] Pilot annotation of ~50–100 examples with multiple real annotators
- [ ] Revised annotation guide based on pilot experience
- [x] Mechanism-selection review informed by the Phase 1 research reference corpus

**Graduation Criteria:**
- [ ] Pilot annotation completed with at least 2 annotators per example
- [ ] Inter-annotator agreement measured and reported
- [ ] Annotation guide updated to reflect lessons learned from actual pilot use
- [ ] Ethical review of annotation process completed

---

## Cross-Phase Workstreams After PR #2

These workstreams may be implemented as focused PRs before or alongside Phase 3. They do not bypass Phase 2 graduation criteria.

### A. Research-corpus expansion and source governance

**Goal:** Broaden the reference corpus without turning copyrighted comedy, historical stereotypes, or cultural commentary into benchmark ground truth.

Planned work includes:
- expand the comedy/reference registry beyond the initial television set using candidate directions identified in post-Phase-2 research reports, but do not treat a named work as an adopted project reference until `docs/RESEARCH-REFERENCE-CORPUS.md` records its source links, provenance/rights boundary, epistemic status, and safe research use;
- prefer official, archival, creator, broadcaster, and peer-reviewed sources over orientation-only summaries where available;
- add academic work on cross-cultural humour, First Nations/Blak comedy, diversity in Australian comedy, and Australian humour as a sociolinguistic or social-regulatory phenomenon only when each source is formally registered;
- map each registered research source to candidate pragmatic mechanisms, relevant invariants, evidential status, and safe synthetic experiment families;
- retain the rule **RESEARCH REFERENCE != REDISTRIBUTABLE DATA**;
- treat performed comedy as mechanism-discovery material, not as a representative corpus of Australian speech.

First Nations, migrant, multicultural, regional, class-marked, or other community-specific material must not be converted into benchmark claims by outsiders alone. Where a future dataset family depends on community-specific pragmatic knowledge, appropriate consultation, permissions, provenance, and scope limitations are required. If those conditions cannot be met, the family should remain a research hypothesis rather than benchmark data.

### B. Mechanism qualification rather than taxonomy inflation

**Goal:** Use real pilot evidence to decide whether new mechanism labels are useful before modifying the benchmark contract.

The active Phase 2 taxonomy remains fixed during the human pilot. After pilot collection, review:
- frequency and distribution of `unknown` selections;
- mechanism-set overlap and recurring disagreement patterns;
- annotator notes describing missing concepts;
- confusion among neighbouring labels such as sarcasm, irony, inverse praise, affectionate insult, relational teasing, and tall-poppy humour;
- whether `self_deprecation`, `relational_teasing`, `tall_poppy_humour`, and `absurdist_escalation` are applied consistently enough to remain useful;
- whether any label encourages stereotypes, deterministic phrase rules, or over-generalisation.

Candidate future mechanism families include:
- `institutional_mimicry`
- `satirical_question_form`
- `performative_sincerity`
- `unreliable_authority`
- `performed_persona`
- `character_speaker_separation`
- `frame_switching`
- `implicature_failure`
- `larrikin_register`
- `cultural_cringe_inversion`
- carefully scoped class-marked register hypotheses

Pilot evidence may nominate a candidate, but **nomination is not schema promotion**. Before any candidate label is added to the active taxonomy, the project must define it provisionally and run an independent trial-coding or re-annotation round on suitable items. That trial must review whether annotators can apply the candidate consistently, whether it improves on existing labels or `unknown`, and whether its agreement/confusion pattern supports keeping it distinct. Only after that evidence is documented may a contract-changing PR update schemas, models, documentation, interface options, and tests together.

No candidate is promoted solely because it is culturally salient or appears frequently in comedy.

### C. Genuine-hostility and uncertainty controls

**Goal:** Ensure the benchmark can distinguish benign hostile-looking language from actual hostility instead of rewarding an always-benign classifier.

Planned work includes:
- introduce a small, ethically reviewed set of clearly hostile synthetic controls;
- include `hostility: "uncertain"` cases where the supplied evidence is genuinely underdetermined;
- build matched contrasts between affectionate insult/profanity/teasing and genuine aggression;
- use content warnings and annotator protections where appropriate;
- keep hostile controls proportionate and research-motivated rather than increasing offensive content for its own sake.

These controls are particularly important before Phase 6 moderation-fairness evaluation.

### D. Runtime and reproducibility hardening

**Goal:** Keep benchmark behaviour stable across supported Python versions and parser/runtime changes.

Current support contract:
- [x] Python 3.11 and 3.12 are the currently advertised and CI-tested package range.
- [x] Package metadata is temporarily constrained to `>=3.11,<3.13` so unverified newer runtimes are not silently advertised as supported.

Planned work includes:
- establish Python 3.13 and 3.14 compatibility in CI before removing the temporary `<3.13` package bound or describing those runtimes as supported;
- make excessive-JSON-nesting rejection an explicit project contract rather than relying on a particular Python parser raising `RecursionError`;
- preserve fail-closed handling for duplicate keys, pathological integers, non-finite values, cyclic in-memory structures, malformed JSON, Unicode decoding failures, and schema-diagnostic hazards;
- add useful test-coverage reporting without weakening deterministic test gates;
- keep clean-wheel/schema-resource smoke tests as release hygiene.

### E. Research-output and dataset infrastructure

**Goal:** Prepare the project for larger datasets and reproducible downstream analysis without prematurely freezing a leaderboard format.

Current capability:
- [x] Evaluation and agreement commands already emit machine-readable JSON.

Candidate work includes:
- define a versioned result/submission schema building on the existing JSON output before public leaderboard or cross-run aggregation work;
- directory-level validation for larger dataset collections;
- an explicit dataset-split contract before Phase 3/4 train/dev/test use becomes necessary;
- glossary expansion for culturally important research terms such as larrikin, Tall Poppy Syndrome, taking the piss, cultural cringe, and carefully scoped class-marked terminology.

### F. ASCFT-derived adversarial pragmatics

**Goal:** Operationalise Australian Sketch Comedy Field Theory (ASCFT) as a theory-derived source of adversarial pragmatic experiments without treating its qutrit, field, collapse, or attractor language as established physical ontology or as representative cultural ground truth.

ASCFT is now registered under the same governed source contract as other adopted post-Phase-2 research inputs. Workstream F may use it only within the provenance, rights, epistemic-status, community-governance, and safe-abstraction boundaries recorded in `docs/RESEARCH-REFERENCE-CORPUS.md`. Its useful starting structure is a three-state analytic basis:
- `|0>` Informal Larrikin Compression;
- `|1>` Bureaucratic Recursive Formalism;
- `|2>` Hyper-Formal Surreal Narration.

The project should treat these states as operational representations for experiment design. They may motivate controlled variables such as frame stability, authority register, semantic drift, recursive contradiction, category instability, demonstrated competence, abrupt pragmatic reframing, and collapse/termination structure. They do not by themselves establish that humour is governed by quantum mechanics, physical field dynamics, or a literal cultural vacuum state.

Candidate adversarial experiment families include:
- authority-register pairs holding confident formal delivery constant while varying whether the speaker is a competent expert, a recursively incoherent bureaucrat, or a deadpan surreal narrator;
- formal-coherence versus epistemic-coherence pairs where syntax and register remain polished while factual or inferential coherence changes;
- claimed-versus-demonstrated-competence pairs that separate authoritative performance from evidence of successful reasoning or action;
- frame-stability versus semantic-stability pairs in which a scene preserves its institutional or documentary frame while meaning progressively destabilises;
- deadpan literal-intent pairs separating delivery style from sincere assertion;
- semantic-drift and contradiction-accumulation sequences that test whether a model notices degradation across turns rather than scoring each utterance in isolation;
- mode-transition families that move between informal compression, bureaucratic recursion, and hyper-formal narration while holding topic or surface vocabulary as constant as practical;
- source-specific attractor motifs, including ASCFT's proposed "goat attractor", as hypotheses to test against documented source material rather than universal Australian-comedy rules.

Candidate invariants for review include:
- **AUTHORITATIVE REGISTER != SINCERE ASSERTION**
- **FORMAL COHERENCE != EPISTEMIC COHERENCE**
- **ASSERTED COMPETENCE != DEMONSTRATED COMPETENCE**
- **NARRATIVE STABILITY != SEMANTIC STABILITY**
- **DEADPAN DELIVERY != LITERAL INTENT**
- **FORMAL ANALOGY != PHYSICAL ONTOLOGY**
- **MATHEMATICAL MODEL != EMPIRICALLY VALIDATED MECHANISM**

These are candidate invariants, not additions to the canonical AU-HUMOUR set. Any promotion requires explicit invariant review and coordinated documentation changes.

A focused follow-up PR should:
- maintain the registered ASCFT provenance, rights, epistemic-status, community-governance, and safe-abstraction record, strengthening it if more authoritative source or explicit licence metadata becomes available;
- create an ASCFT operational crosswalk mapping source terminology to observable benchmark manipulations without claiming literal physical equivalence;
- define independently authored synthetic minimal pairs and context swaps for the strongest testable mechanisms;
- keep source dialogue, transcript wording, and distinctive copyrighted expression out of redistributable benchmark data;
- separate source-specific motifs from general claims about Australian humour;
- identify which candidate mechanisms can be expressed using the current taxonomy and which, if any, require later provisional trial coding under Workstream B;
- add deterministic regressions for any new machine-readable contract introduced by the crosswalk or synthetic-family format.

The epistemic boundary for this workstream is explicit: ASCFT may be used as a formal analytic framework and hypothesis generator. Stronger claims that its field equations, qutrit states, collapse operators, attractors, Lagrangian, or cultural-stress observables constitute empirically validated physical mechanisms require independent evidence and are not assumed by this benchmark.

### G. Trans-Tasman relational pragmatics and lexical context

**Goal:** Study how Australian and New Zealand speakers can use nationality-focused teasing, rivalry, profanity, stereotypes, and shared regional slang without assuming either that such language is inherently hostile or that trans-Tasman banter is automatically harmless.

The historical relationship provides useful context but not modern pragmatic ground truth. New Zealand participated in the 1890 Australasian Federation Conference and later withdrew from the federation process. Covering clause 6 of the Commonwealth of Australia Constitution Act explicitly includes New Zealand in the historical definition of colonies that could be parts of the Commonwealth as States. See the Parliamentary Education Office's [Federation timeline](https://peo.gov.au/understand-our-parliament/history-of-parliament/federation/federation), its [Constitution introduction](https://peo.gov.au/understand-our-parliament/how-parliament-works/the-australian-constitution/introducing-the-australian-constitution), and the [Commonwealth of Australia Constitution Act](https://www.legislation.gov.au/C2004Q00685/asmade/1901-01-01/text/original/epub/OEBPS/document_1/document_1.html). This history may help explain why "cousin-like" or sibling-rivalry metaphors arise in contemporary discussion, but **HISTORICAL FEDERATION CONNECTION != SHARED NATIONAL IDENTITY** and historical proximity does not prove that any individual speaker experiences the relationship that way.

The central benchmark problem is relational licence. A nationality-targeted trans-Tasman stereotype may function as reciprocal teasing between close Australian and New Zealand friends who have an established history of such banter, while equivalent targeting from a stranger, workplace aggressor, or hostile online account may be harassment or genuine hostility. Abstractly describing the same stereotype inside linguistic, historical, or moderation analysis is a third pragmatic frame again. The benchmark must therefore model speaker relationship, reciprocity, setting, target reaction where available, and discourse purpose rather than classifying nationality-focused language from lexical content alone.

A historically circulated research lead supplied to the project concerns a crude nationality-targeted sexual stereotype about New Zealanders. Repository policy prohibits introducing group-stereotyping language, so the exact wording is not retained here. The research lead is not a factual statement about New Zealanders and is not evidence that Australians generally hold the underlying belief. Any future provenance-bearing study of an exact historical formulation requires an attributable source and a separate governance review. Redistributable benchmark items should model the relational and mention-versus-use structure with abstract placeholders or non-identity-targeted synthetic content rather than manufacturing new nationality stereotypes.

The word `root` is also a useful lexical-pragmatic stress case. The currently registered ABC Language source supports the bounded claim that Australian English uses `root` as vulgar slang for sexual intercourse. The project has not yet registered an attributable New Zealand source establishing a corresponding New Zealand sexual sense, so that New Zealand-specific claim remains unestablished here. The currently supported comparison is contextual polysemy across Australian English and other domains: Australian sexual slang, American expressions such as "root for the team", botanical senses, and computing uses of `root` for privileged access. ABC Language's [history of Australian slang terms for sex](https://www.abc.net.au/news/2018-03-01/from-rooting-to-bonking-a-history-of-australian-sex-terms/9492856) documents the Australian sexual sense. A prompt such as `Got root?` can therefore change pragmatic interpretation radically under an Australian social context, a Unix administration context, or a non-Australian sports-support context.

Candidate adversarial experiment families include:
- same-structure relationship swaps where an abstract nationality-targeted tease is addressed by a close friend with established reciprocal banter versus a stranger, coworker, adversarial account, or authority figure;
- sports-rivalry pairs separating playful pre/post-match needling from genuine national hostility;
- mention-versus-use pairs separating abstract description or quotation placeholders used for linguistic, historical, moderation, or research analysis from direct nationality-targeted use;
- reciprocity pairs distinguishing two-way teasing from one-sided repeated degradation;
- public/private setting swaps testing whether relational licence changes across a private friendship, group chat, workplace, classroom, broadcast, or public platform;
- target-reaction/context pairs where the same surface joke is welcomed, reciprocated, rejected, or explicitly experienced as harassment;
- `root` polysemy pairs spanning the sourced Australian sexual-slang sense, computing privilege, plant anatomy, and non-Australian sports-support senses;
- moderation controls checking whether systems over-classify close-friend national teasing as hate/abuse or under-classify genuinely hostile nationality-targeted speech merely because similar structures can occur in friendly banter.

Candidate invariants for review include:
- **TRANS-TASMAN TEASING != INTERGROUP HATRED**
- **RELATIONAL LICENCE != UNIVERSAL LICENCE**
- **STEREOTYPE JOKE != FACTUAL BELIEF**
- **MENTIONED STEREOTYPE != ENDORSED STEREOTYPE**
- **NATIONALITY REFERENCE != HOSTILE INTENT**
- **CLOSE-MATE BANTER != STRANGER OR WORKPLACE LICENCE**
- **DIALECT-SPECIFIC SENSE != GLOBAL ENGLISH SENSE**
- **HISTORICAL FEDERATION CONNECTION != SHARED NATIONAL IDENTITY**

These are candidate invariants and research hypotheses, not universal claims about Australians or New Zealanders. A friendly interpretation must never be inferred solely from nationality, and a hostile interpretation must never be inferred solely from the presence of a nationality reference. Any benchmark family making claims about New Zealand pragmatic norms should involve New Zealand cultural or linguistic consultation under the same governance principles used elsewhere in the project.

A focused follow-up PR should:
- maintain the now-registered historical and Australian linguistic sources for the trans-Tasman research family and add an attributable New Zealand linguistic source before making claims about New Zealand-specific lexical usage;
- document the distinction between Australian observations about trans-Tasman banter and claims about New Zealand speakers themselves;
- build independently authored minimal pairs spanning friendship, sports rivalry, workplace/public hostility, mention/analysis, and uncertain cases without introducing group-stereotyping wording into the repository;
- include genuine-hostility controls so relational-teasing recognition cannot reward an always-benign classifier;
- preserve `root` as a context-sensitive Australian lexical family rather than a deterministic phrase rule or an unsupported cross-dialect claim;
- map candidate items to the existing `relational_teasing`, `affectionate_insult`, `cultural_dependency`, `context_required`, ambiguity, social-valence, and hostility contracts before proposing any new mechanism label;
- connect suitable families to Phase 5 context-swap evaluation, Phase 6 moderation fairness, and Phase 7 cross-dialect comparison.

### H. Slang density, register compression, and operational intelligibility

**Goal:** Study Australian slang as a context-sensitive, compositional register that can support efficient in-group communication while becoming difficult for unfamiliar listeners, especially when multiple colloquialisms, abbreviations, pragmatic inversions, and local references are packed into the same exchange.

This workstream must distinguish evidence levels. Victoria University's [Australian slang dictionary](https://www.vu.edu.au/about-vu/news-events/vu-blog/australian-slang-dictionary) is a public educational glossary and is useful for attested examples such as `arvo`, `heaps`, `mate`, `old mate`, `smoko`, and `cactus`, including the explicit observation that `mate` and `old mate` are not always friendly. The Reddit thread [Best Aussie slang](https://www.reddit.com/r/australia/comments/1g73mue/best_aussie_slang/) is community-attestation material only: it is useful for discovering candidate expressions, speaker judgements, disagreement about currency or origin, and naturally occurring metalinguistic commentary, but it is not lexicographic authority or representative population evidence.

Official Defence reporting provides a higher-stakes intelligibility case. During Exercise Predators Run in the Northern Territory, an Australian Army linguist stated that the Australian accent and use of slang can be particularly challenging for Filipino soldiers participating in the multinational exercise. See Defence, [Communication key on combined exercise](https://www.defence.gov.au/news-events/news/2022-09-08/communication-key-combined-exercise). A 2026 joint-training report also records terminology and language hurdles between partner forces and the use of visual models to build shared understanding. See Defence, [Partner nations rehearse for war](https://www.defence.gov.au/news-events/news/2026-06-11/partner-nations-rehearse-war). These sources support the narrower claim that local language, terminology, accent, and slang can create cross-force communication friction. They do **not** establish that Australian troops intentionally used slang as encryption or that Allied codebreakers were defeated by ordinary Australian conversation.

There is also historical evidence that visiting American servicemen were explicitly briefed on Australian language and culture. The Australian War Memorial catalogues the circa-1942 booklet [Welcome to Australia](https://www.awm.gov.au/collection/LIB100000077), designed for American troops in Australia, and a United States Army pocket guide to Australia included a dedicated Australian-slang section. This supports **HISTORICAL NEED FOR LANGUAGE BRIEFING != EVIDENCE OF INTENTIONAL OBFUSCATION**.

The project has not yet found reliable support for two stronger research leads supplied during planning: that Allied codebreakers trained on foreign ciphers could not parse Australian conversational slang, or that the ADF formally restricted slang specifically for Australian-American exercises in Darwin to prevent fatal misunderstandings. Those claims must remain unadopted unless attributable evidence is found.

Candidate adversarial experiment families include:
- slang-density ladders that preserve propositional content while progressively replacing standard phrasing with colloquialisms, abbreviations, discourse markers, and local idioms;
- compositional tests where each slang item is individually familiar but the combined utterance requires resolving several context-dependent meanings at once;
- `mate` and `old mate` social-valence swaps separating friendly address, neutral reference, distancing, criticism, and hostility;
- diachronic and regional uncertainty cases where speakers disagree about whether an expression is current, local, borrowed, dated, or widespread;
- glossary-versus-context tests where a model is given correct dictionary meanings but must still infer implicature, tone, relationship, and intended force;
- military or emergency-style clarity contrasts separating informal barracks banter from safety-critical instructions where conventional terminology and explicitness matter;
- cross-national listener cases testing Australian slang with familiar Australian speakers, other English-speaking partners, and speakers using English as an additional language;
- ASCFT `|0>` bridge tests treating Informal Larrikin Compression as a hypothesis about information compression rather than a licence to equate slang density with semantic degradation.

Candidate invariants for review include:
- **SLANG TOKEN != FIXED PRAGMATIC MEANING**
- **SLANG GLOSSARY != PRAGMATIC UNDERSTANDING**
- **COMMUNITY ATTESTATION != LEXICOGRAPHIC AUTHORITY**
- **IN-GROUP FLUENCY != CROSS-GROUP INTELLIGIBILITY**
- **DENSE COLLOQUIAL REGISTER != SECRET CODE**
- **INFORMAL COMPRESSION != INTENTIONAL ENCRYPTION**
- **FAMILIAR REGISTER != OPERATIONAL CLARITY**
- **HISTORICAL LANGUAGE BRIEFING != PROOF OF COMMUNICATION FAILURE**

A focused follow-up PR should:
- maintain the now-registered Victoria University, Defence, and wartime archival records and add stronger linguistic scholarship under the governed source contract;
- retain Reddit and similar community discussions as orientation/community-attestation sources with explicit non-representative status;
- build independently authored slang-density and context-swap items instead of converting crowd-sourced examples directly into benchmark data;
- distinguish lexical recognition, compositional interpretation, pragmatic interpretation, and safety-critical operational clarity as separate evaluation targets;
- document regional, generational, occupational, and temporal variation rather than treating an Australian slang dictionary as a timeless national lookup table;
- connect suitable tests to Phase 5 adversarial context swaps and Phase 7 cross-dialect/cross-register comparison;
- keep any military claims limited to what official or archival evidence actually demonstrates.

### I. Australian and United States policing-context transfer

**Goal:** Study whether AI systems import policing language, legal scripts, agency assumptions, emergency-routing conventions, and screen-fiction tropes from one jurisdiction into another, without treating either country, police service, officer, or encounter as monolithic.

This workstream is a **source-gated research proposal**, not an adopted description of either policing system and not legal advice. Before any benchmark family is implemented, the project must register current official Australian and United States sources covering the specific jurisdictions and topics being compared. Australian federal, state, and territory material must not be collapsed into one undifferentiated script; United States federal, state, county, municipal, sheriff, highway-patrol, and special-jurisdiction material must likewise not be treated as interchangeable. Every implemented item should record the relevant country, jurisdiction, institutional role, encounter type, and source date.

The core pragmatic problem is institutional-script transfer. A model trained heavily on United States media may insert a familiar American warning, agency title, emergency convention, courtroom role, or encounter expectation into an Australian scenario. The reverse error is also possible. Surface-equivalent terms may carry different legal force, institutional scope, or conversational expectations, while distinct terms may serve partly comparable functions. The benchmark should test whether the model asks for or uses jurisdictional context instead of completing the scene from the loudest television trope in its training data.

Candidate adversarial experiment families include:
- same-utterance jurisdiction swaps in which the country, state/territory, agency, or officer role changes while the wording remains constant;
- emergency-contact and agency-routing scenarios that test whether the model selects the convention supported by the supplied location rather than a globally assumed default;
- caution, interview, detention, search, consent, and right-to-silence scenarios that distinguish jurisdiction-specific legal language from imported catchphrases;
- role-title pairs involving terms such as `constable`, `sheriff`, `deputy`, `trooper`, `detective`, `prosecutor`, and other labels whose powers or institutional position cannot be inferred from the word alone;
- casual-address pairs testing whether an officer's use of `mate`, first names, humour, understatement, or a calm register is mistaken for friendship, consent, informality of legal consequence, or absence of coercive authority;
- direction-versus-request pairs separating politeness, conversational softening, lawful authority, voluntary cooperation, uncertainty, and explicit compulsion;
- ordinary service, traffic, welfare, public-order, emergency, questioning, and detention controls so the benchmark does not equate every police interaction with hostility or every calm interaction with harmlessness;
- media-trope controls separating fictional dialogue and imported procedural scripts from the official rule or practice actually supplied in context.

Candidate invariants for review include:
- **US POLICE SCRIPT != AUSTRALIAN LEGAL PROCEDURE**
- **POLICE TERMINOLOGY != CROSS-JURISDICTION EQUIVALENCE**
- **CASUAL ADDRESS != FRIENDSHIP OR CONSENT**
- **CALM TONE != ABSENCE OF COERCIVE AUTHORITY**
- **POLITE WORDING != VOLUNTARY CHOICE**
- **FICTIONAL POLICE TROPE != OPERATIONAL POLICY**
- **ONE AGENCY != A NATIONAL POLICING SYSTEM**
- **ONE ENCOUNTER != SYSTEM-WIDE GROUND TRUTH**
- **JURISDICTIONAL DIFFERENCE != NATIONAL MORAL CHARACTER**
- **LEGAL INFORMATION != LEGAL ADVICE**

These are candidate research invariants, not legal conclusions or evaluations of which country polices "better". The study must not infer danger, benevolence, lawfulness, racism, corruption, restraint, or legitimacy from nationality, uniform, accent, weapon visibility, casual language, or one anecdote. Where an experiment concerns coercion, consent, search, detention, questioning, force, or legal rights, the supplied context and registered jurisdiction-specific source must establish the relevant condition rather than asking annotators or models to guess it.

A focused follow-up PR should:
- register official and current sources for each Australian and United States jurisdictional claim before adopting it as benchmark context;
- add a canonical methodology section defining jurisdiction/date metadata, encounter categories, matched controls, source hierarchy, and legal-review requirements;
- construct independently authored context swaps rather than copying body-camera audio, police interviews, television dialogue, viral clips, or identifiable real-person encounters;
- separate linguistic-pragmatic evaluation from legal correctness, policy evaluation, use-of-force analysis, and moral comparison, reporting each only when the dataset and sources genuinely support it;
- include unresolved cases where the context does not establish whether a statement is a request, direction, warning, caution, consent inquiry, or compulsory instruction;
- involve appropriate Australian and United States legal, policing, civil-liberties, and community expertise before publishing high-stakes conclusions;
- connect suitable families to Phase 5 context swaps, Phase 6 moderation/safety analysis, and Phase 7 cross-register and cross-institution comparison.

---

## Phase 3 — Multi-Annotator Culturally Contextualised Dataset

**Goal:** Produce a dataset with genuine human annotations, multiple interpretations per example, explicit confidence ratings, documented disagreement, and broader pragmatic coverage than the initial pilot.

**Deliverables:**
- Dataset of 200–500 examples with multi-annotator labels
- Provenance and consent documentation for all examples
- Formal inter-annotator agreement analysis
- Dataset card following established NLP data documentation practice
- Expanded controlled families for tall-poppy/status calibration, self-deprecation, relational teasing/taking-the-piss, absurdist escalation, understatement, discourse markers, affectionate insult, profanity, literal controls, and genuine-hostility controls
- Additional context-swap groups where relationship, preceding event, authority status, social setting, or discourse frame is the controlled manipulation
- Research-corpus-to-benchmark design notes showing how mechanisms were abstracted into original or appropriately licensed data

**Cultural-governance requirement:**

First Nations/Blak, migrant, multicultural, regional, class-marked, or other community-specific example families are **not automatic Phase 3 requirements**. They may be included only when the project has appropriate cultural consultation, provenance, permissions, and a defensible claim boundary. Absence is preferable to invented representation.

**Graduation Criteria:**
- [ ] Dataset ethics review completed
- [ ] Provenance documented for all examples
- [ ] Inter-annotator agreement reported with appropriate metrics
- [ ] Data release reviewed against privacy and consent requirements
- [ ] Every active mechanism intended for evaluation has meaningful human-annotated coverage or is explicitly retired/deferred
- [ ] Hostility controls are sufficient to detect degenerate always-benign predictions
- [ ] Community-specific material, if present, has documented consultation and scope limitations

---

## Phase 4 — Baseline Evaluation

**Goal:** Evaluate a selection of publicly available language models against the Phase 3 dataset using the reference evaluator and extended metrics.

**Deliverables:**
- Evaluation pipeline for local and API-accessible models
- Baseline scores on component metrics, not a single aggregate "Australian understanding score"
- Versioned machine-readable result records building on the existing JSON CLI output
- Calibration, coverage, ambiguity-recognition, hostility, social-valence, pragmatic, and context-sensitivity reporting
- Analysis of model failure modes
- Initial answer to RQ1–RQ5

**Graduation Criteria:**
- [ ] At least 3 models evaluated
- [ ] Component metrics reported without overclaiming
- [ ] Analysis does not conflate benchmark performance with cultural competence
- [ ] Missing predictions remain visible in dataset-level coverage and the applicable accuracy denominators rather than being silently dropped
- [ ] Unresolved categorical annotations such as `hostility: "uncertain"` and `social_valence: "unknown"` are excluded from their categorical accuracy denominators and reported separately, matching the reference evaluator contract
- [ ] Results reviewed before public release

---

## Phase 5 — Adversarial Context-Swap and Minimal-Pair Benchmark

**Goal:** Formalise and expand context-swap and minimal-pair tests, including adversarial pragmatic structures identified during reference-corpus analysis.

**Deliverables:**
- Extended context-swap dataset holding utterance constant while varying context and/or relationship
- Minimal-pair examples differing in speaker relationship, preceding event, social setting, authority status, demonstrated competence, persona, or discourse frame
- Authority-inversion and claimed-vs-demonstrated-competence families
- Question-intent families separating information seeking, accusation, sarcasm, satire, rhetorical challenge, and performative bait
- Persona and character-speaker-separation families
- Institutional-mimicry and authority-register-parody families
- Larrikin/anti-authority pragmatics studied as a hypothesis rather than a universal Australian rule
- Tall-poppy/status-calibration families separating playful status deflation, scepticism toward unsupported self-promotion, ordinary congratulations with deflationary humour, and unfair suppression of demonstrated competence
- Self-deprecation families separating conventional humility, genuine low confidence, irony, and defensive status management
- Absurdist-escalation families separating literal improbability, deadpan delivery, understatement, and surreal frame shifts
- Trans-Tasman relationship-swap families separating reciprocal Australian/New Zealand banter from one-sided hostility, harassment, quotation/analysis, and uncertain cases
- Slang-density and compositional-register families separating lexical recognition from context-sensitive pragmatic interpretation
- Source-gated Australian/United States policing-context families separating jurisdictional evidence from imported institutional scripts or media tropes
- Analysis of whether context-swap failures correlate with lexical shortcuts or authority/prestige shortcuts
- Answers to RQ6 and RQ7

**Graduation Criteria:**
- [ ] Context-swap examples cover at least 10 distinct utterance types and multiple manipulation dimensions
- [ ] Results show whether models use context beyond lexical content
- [ ] Relationship-only minimal pairs are represented where scientifically useful
- [ ] Methodology is replicable without proprietary dependencies
- [ ] Media-inspired benchmark items are independently authored or appropriately licensed
- [ ] Tall-poppy/status items do not encode "Australians dislike success" as a universal cultural rule
- [ ] Larrikin, cultural-cringe, class-marked, or institutional-satire families remain explicitly scoped hypotheses rather than national-character claims

---

## Phase 6 — Moderation-Fairness Evaluation

**Goal:** Investigate whether content moderation systems produce disparate false-positive or false-negative rates for Australian pragmatic language relative to explicitly defined, denotatively/pragmatically matched non-Australian or comparison-register counterparts, while separately testing benign-versus-hostile discrimination.

**Deliverables:**
- Moderation-fairness evaluation methodology
- Matched Australian-versus-non-Australian (or otherwise explicitly defined comparison-register) counterpart families suitable for estimating disparate error rates
- Matched benign-versus-hostile control families suitable for detecting false positives, false negatives, and degenerate always-benign behaviour
- Results on at least 2 publicly accessible moderation systems
- Analysis of false-positive and false-negative patterns by comparison group and hostility status
- Separate treatment of affectionate insult, profanity-non-hostile, relational teasing, satire, genuine hostility, and unresolved hostility
- Answer to RQ5

**Graduation Criteria:**
- [ ] Methodology reviewed for ethical soundness
- [ ] The evaluation includes matched Australian/comparison-register counterparts sufficient to support any disparate-rate claim
- [ ] The evaluation includes enough genuine-hostility controls that an always-benign classifier cannot appear successful
- [ ] Results do not identify individuals
- [ ] Limitations of moderation system API access are documented
- [ ] Cultural difference is not treated as evidence of harmlessness or harmfulness by itself

---

## Phase 7 — Cross-Dialect and Cross-Cultural Comparison

**Goal:** Investigate whether methods and findings from Australian English generalise to other dialects or culturally dependent pragmatic registers, without assuming that they do.

**Deliverables:**
- Comparative framework for at least one additional dialect or culturally situated pragmatic register
- New Zealand English and trans-Tasman pragmatics as a candidate comparison family, contingent on appropriate New Zealand cultural/linguistic consultation and explicit separation of shared vocabulary from divergent pragmatic context
- Australian slang-density and operational-intelligibility comparisons as a candidate cross-register family, with listener background and task criticality treated as explicit variables
- Analysis of shared and divergent pragmatic mechanisms
- Use of published cross-cultural humour research as hypothesis-generation material, not as a lookup table for national character
- Answer to RQ8
- Explicit documentation of what does and does not generalise

**Graduation Criteria:**
- [ ] At least one additional dialect/register included with appropriate cultural consultation
- [ ] Results do not assume Australian conventions are universal
- [ ] Collaborators from relevant linguistic communities are involved
- [ ] Broad cultural comparison tables are not treated as ground-truth labels for individuals

---

## Phase 8 — Research Paper and Archival Release

**Goal:** Produce a citable, peer-reviewed research publication and an archivally deposited benchmark release.

**Deliverables:**
- Research paper submitted to a peer-reviewed venue
- Archived dataset with DOI
- Updated CITATION.cff with real metadata
- Versioned dataset card, benchmark schemas, evaluation protocol, and machine-readable result format
- Final benchmark package suitable for independent replication

**Graduation Criteria:**
- [ ] Paper accepted at peer-reviewed venue
- [ ] Dataset archived with persistent identifier
- [ ] Replication instructions verified by independent researcher
- [ ] All metadata in CITATION.cff is accurate and complete
- [ ] Archived release states which cultural/mechanism families were validated, deferred, or excluded and why
