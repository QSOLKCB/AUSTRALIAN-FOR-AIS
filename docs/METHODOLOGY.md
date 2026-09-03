# Methodology

## Research Principle

Language meaning is conditional on context, culture, relationship, discourse, and uncertainty. Surface lexical meaning alone is not sufficient evidence of intended social meaning.

Australian English is used here as a deliberately difficult research environment because documented and observed Australian discourse provides rich cases of understatement, irony, affectionate insult, deadpan humour, discourse markers, and relationship-conditioned meaning. These are tendencies and research targets, not universal rules about Australian speakers.

---

## What This Project Studies

The project studies whether AI systems can:

1. recognise that surface and pragmatic meaning can differ;
2. use contextual information when interpreting an utterance;
3. represent genuine ambiguity rather than silently collapsing it;
4. calibrate confidence appropriately;
5. distinguish lexical profanity from social aggression; and
6. respond correctly when an identical utterance changes pragmatic meaning under a changed context.

---

## Research Questions

**RQ1:** Can language models distinguish lexical profanity from social aggression?

**RQ2:** Does providing relationship context materially improve pragmatic interpretation accuracy?

**RQ3:** Can models correctly recognise when an utterance is pragmatically ambiguous?

**RQ4:** Do models become overconfident when interpreting culturally dependent humour?

**RQ5:** Do safety or moderation systems show disparate false-positive or false-negative rates for Australian pragmatic language relative to explicitly defined, denotatively/pragmatically matched non-Australian or comparison-register counterparts, and, as a separate discrimination axis, can they distinguish benign hostile-looking language from genuine hostility?

**RQ6:** Can models distinguish sincere praise from inverse praise when lexical content is identical?

**RQ7:** Do context-swap examples expose reliance on lexical shortcuts rather than contextual reasoning?

**RQ8:** How much of performance on this benchmark transfers to other dialects or cultural settings?

These are questions under investigation, not assumed conclusions.

---

## Taxonomy of Pragmatic Mechanisms

The active Phase 1/2 taxonomy is intentionally small and extensible.

| Tag | Description |
|---|---|
| `understatement` | Deliberately diminished description of a significant situation |
| `sarcasm` | Surface-positive or otherwise literal wording used to convey criticism |
| `irony` | A contrast between expressed surface content and intended meaning |
| `deadpan` | Humorous or incongruous content delivered without overt expressive emphasis |
| `affectionate_insult` | Insulting language used within an affectionate or solidarity context |
| `inverse_praise` | Ostensible praise conveying negative evaluation |
| `profanity_non_hostile` | Profanity without hostile or aggressive intent |
| `discourse_marker` | Conversational marker whose function depends on discourse context |
| `self_deprecation` | Intentionally diminished self-representation |
| `absurdist_escalation` | Escalation to an absurd degree for comic or emphatic effect |
| `relational_teasing` | Humour directed at a person within a relationship context |
| `tall_poppy_humour` | Humorous deflation of success or status as an analytical hypothesis |
| `ambiguous_address` | Address term whose valence depends on relationship and context |
| `literal` | The utterance is intended and interpreted at face value |
| `unknown` | The active taxonomy does not justify a more specific mechanism |

Examples and annotations may carry multiple tags. Tags are analytical judgements, not established facts.

### Discourse markers such as “yeah nah”

The project explicitly rejects a fixed phrase-to-intent lookup table. A sequence such as `yeah nah` may have conventional directional tendencies in some Australian discourse, but an annotation must justify its interpretation from the supplied context, discourse position, relationship, and available delivery cues. The starter invitation fixture therefore treats refusal as the **best estimate for that context**, not as a universal lexical rule.

The same caution applies to `nah yeah`, `mate`, `old mate`, `righto`, profanity, and other socially loaded forms.

---

## Ambiguity and Insufficient Context

An ambiguous record must preserve at least two distinct normalized pragmatic readings. Duplicate strings, including case- or whitespace-only variants, do not constitute multiple interpretations.

`insufficient_context` is a special primary annotation used only when the supplied context does not justify choosing among those retained readings. It therefore does **not** erase the candidate interpretations. A model may explicitly predict `insufficient_context` for a benchmark example annotated this way, and a human annotator may use the same sentinel in Phase 2.

The sentinel requires `ambiguity: true`, at least two distinct retained pragmatic readings, and confidence at or below `0.4`.

This avoids rewarding a model or annotator workflow for confidently collapsing unresolved ambiguity into one arbitrarily chosen reading.

---

## Context-Swap Design

A benchmark context-swap group holds the utterance constant while changing context. Dataset validation requires at least two members, the same observed utterance with lexical case preserved, distinct contexts, distinct primary pragmatic directions, and pairwise-disjoint accepted pragmatic direction sets. Whitespace runs may be normalised for comparison, but case differences such as `US` versus `us` are treated as a changed linguistic observation rather than a valid context-only swap.

The disjointness requirement is deliberately stronger than merely requiring different primaries. Without it, two ambiguous members could both accept readings `A` and `B`, allowing a model to swap `A` and `B` between contexts and still receive context-sensitivity credit. A valid benchmark context-swap group must therefore give each context a non-overlapping set of accepted directions.

The explicit `insufficient_context` sentinel is part of a sentinel-primary member's accepted direction set for this check. Consequently, two members whose primary interpretation is `insufficient_context` cannot belong to the same benchmark context-swap group because their accepted direction sets would overlap on the sentinel.

Success requires the prediction for each context to match an accepted interpretation for that context and the paired predictions to differ. Different-but-wrong outputs do not pass.

Phase 2 pilot pairs are intentionally weaker: before annotation they only preserve the same observed utterance and vary context. Human annotation is allowed to show that a proposed pair does not produce a clean directional contrast.

---

## Phase 2 Pilot Human Annotation

Phase 2 is a pilot of the **annotation process**, not a claim that human consensus exists.

The repository supplies 60 unannotated synthetic pilot items, arranged as 30 same-utterance context contrasts. The item records contain observation-side information only. They do not contain hidden gold interpretations, mechanism labels, valence, hostility, confidence, or ambiguity labels.

Each item should receive at least two independent human annotations. Annotators use pseudonymous IDs and work from the supplied utterance, context, and relationship only. They should not discuss an item with other annotators before submitting their own interpretation.

The optional `australian_english_exposure` field is a coarse self-report of familiarity (`low`, `medium`, `high`, or `unspecified`). It is not used to infer nationality, ethnicity, or identity.

The Phase 2 annotation record captures:

- literal interpretation;
- one or more pragmatic interpretations;
- primary interpretation or `insufficient_context`;
- mechanism labels;
- social valence and hostility;
- confidence and ambiguity;
- cultural dependency and context dependence;
- optional alternatives and notes.

The project stores independent annotations rather than overwriting them with a consensus label. Any later adjudication protocol must preserve the original records.

See `PHASE2-PILOT-PROTOCOL.md` for operational and ethical details.

---

## Phase 2 Agreement Analysis

Agreement metrics are evidence about the usability and stability of the annotation scheme. They are not evidence that an agreed label is objective cultural truth.

Phase 2 reports:

- coverage, including whether every item has at least two annotations;
- descriptive within-item pairwise agreement for categorical fields;
- Cohen's kappa for each pair of annotators on their shared examples;
- exact-set agreement and Jaccard overlap for multi-label mechanism selections;
- descriptive pairwise confidence differences.

Free-text pragmatic interpretations are **not** assigned an exact-string IAA score. Different wording can express similar meanings, and no validated semantic equivalence judge exists in Phase 2. The text is retained for qualitative review and for designing any later adjudication protocol.

A low agreement result is not automatically a failed item. It may indicate genuine ambiguity, unclear context, an unstable taxonomy label, or an annotation-guide problem. Those possibilities must be inspected rather than silently normalised away.

---

## Minimal Pairs

Later phases will formalise variants that differ in one controlled factor such as speaker relationship, preceding event, explicit delivery cue, or social setting while holding other features constant.

---

## ASCFT-Derived Experiment Design

Workstream F uses the registered Australian Sketch Comedy Field Theory (ASCFT) source as a formal analytic framework and hypothesis generator. ASCFT terminology is source-specific analytic machinery, not an addition to the active humour taxonomy and not evidence that Australian humour is literally governed by physical field dynamics.

The preferred design is to hold topic, lexical content, or overt register as constant as practical while manipulating one observable dimension at a time. Core controlled variables include:

- **authority register**, separating confident formal delivery from whether the surrounding evidence supports the speaker's claims;
- **epistemic coherence**, varying factual, inferential, or categorical consistency while keeping surface fluency and formatting stable;
- **demonstrated competence**, separating asserted expertise from successful reasoning, prediction, or action;
- **frame stability**, holding an institutional, documentary, or expert frame constant while pragmatic or semantic content destabilises;
- **semantic drift and contradiction accumulation**, using ordered multi-turn sequences so degradation can be measured across turns rather than inferred from one isolated sentence;
- **delivery versus intent**, manipulating explicit delivery cues such as deadpan versus overtly expressive delivery independently from whether the utterance is sincerely literal, ironic, sarcastic, absurd, or otherwise nonliteral; and
- **mode transition**, using ASCFT's source-specific `|0>`, `|1>`, and `|2>` coordinates only to label controlled transitions among informal compression, bureaucratic recursion, and hyper-formal surreal narration during experiment construction.

Experiment families should include matched controls where polished formal language remains factually coherent, informal language remains semantically precise, or confident speakers demonstrate genuine competence. Whenever a family is used to evaluate **delivery versus intent**, it must implement a crossed 2×2 design containing all four cells: deadpan delivery with sincere literal intent, deadpan delivery with a justified nonliteral intent, non-deadpan delivery with sincere literal intent, and non-deadpan delivery with a justified nonliteral intent. The lexical proposition, relationship, discourse frame, and other relevant variables should be held constant as far as the research question permits. If all four cells cannot be constructed without introducing an uncontrolled confound, the family is not eligible to estimate a delivery effect or delivery-by-intent interaction and must instead be reported as a narrower intent or delivery comparison. Delivery style is evidence available to interpretation, not a deterministic label, so deadpan delivery alone must never establish literal or nonliteral intent.

Source-specific motifs such as the proposed goat attractor may be studied only as motifs of the registered theory or its documented source material. They are not benchmark labels, universal properties of Australian comedy, or acceptable shortcuts for assigning a collapse outcome. Any source-inspired item must be independently authored or appropriately licensed and must not reproduce dialogue, transcript wording, distinctive jokes, or other copyrighted expression.

The epistemic boundary is mandatory:

- **FORMAL ANALOGY != PHYSICAL ONTOLOGY**
- **MATHEMATICAL MODEL != EMPIRICALLY VALIDATED MECHANISM**

Qutrit states, fields, collapse operators, attractors, Lagrangians, cultural-stress observables, and similar constructs may organize hypotheses and controlled manipulations. Their mathematical definition does not establish that they are empirically validated physical mechanisms, population-level cultural laws, or objective ground truth.

---

## Trans-Tasman and Slang/Operational Experiment Design

Workstreams G and H extend the general context-swap and minimal-pair methodology. They do not create fixed phrase rules or community ground truth.

For **trans-Tasman relational-pragmatics** experiments, the preferred design is to hold lexical or structural content as constant as practical while manipulating one or more of the following variables explicitly:

- speaker relationship and established relational licence;
- reciprocity versus one-sided targeting;
- private, public, workplace, classroom, broadcast, or platform setting;
- target reaction where that reaction is part of the supplied evidence;
- direct use versus abstract mention, quotation placeholder, moderation analysis, or historical discussion; and
- benign-teasing, genuine-hostility, and unresolved controls.

The repository must not introduce group-stereotyping wording merely to instantiate these contrasts. Where a research question depends on historical stereotype structure, use an abstract placeholder or non-identity-targeted synthetic analogue. An attributable source may document that a stereotype existed, but exact group-stereotyping wording must not be reproduced in repository content or redistributable benchmark items. Claims about New Zealand lexical or pragmatic norms require attributable New Zealand evidence and, where the claim is community-specific, appropriate New Zealand cultural or linguistic consultation.

For **slang-density and operational-intelligibility** experiments, lexical recognition, compositional interpretation, pragmatic interpretation, and task-critical communication clarity are separate evaluation targets. A useful ladder holds the underlying proposition stable while progressively varying slang density, abbreviation, discourse markers, local idioms, or register compression. Australian-English familiarity or exposure, general English-language background or proficiency, and task criticality should be explicit independent variables rather than inferred from nationality or identity. Where listener effects are evaluated, Australian-English familiarity should be self-reported or experimentally established, and comparisons should cross or match dialect exposure against broader English-language background so neither nationality nor first-language category acts as a proxy for comprehension.

Relevant controlled comparisons include:

- glossary-known versus context-correct interpretation;
- low-density versus high-density colloquial phrasing;
- higher versus lower Australian-English familiarity crossed or matched across general English-language backgrounds;
- informal social or barracks-style exchange versus safety-critical or operational instruction; and
- ordinary misunderstanding versus successful repair through clarification, shared terminology, translation, or visual grounding.

Official or archival military sources may motivate **communication-friction** hypotheses, but they do not establish that Australian slang is a secret code, that ordinary conversation defeated codebreakers, or that operational failure followed from slang unless an attributable source establishes that stronger claim. Community discussions and slang glossaries can nominate candidate forms, but neither is treated as representative population evidence or sufficient pragmatic ground truth.

These families remain subject to the same ambiguity, context-swap, provenance, annotation, and scoring rules defined elsewhere in this document. A model succeeds only when it uses the supplied context correctly, not merely when it recognises a slang token or nationality reference.

---

## Australian and United States Policing-Context Experiment Design

Workstream I studies **institutional-script transfer** between Australian and United States policing contexts. It is a linguistic-pragmatic research design, not legal advice, a use-of-force benchmark, or a ranking of which country polices “better”. No policing behaviour, legal right, coercive condition, or procedural difference may be inferred from nationality alone.

Every implemented policing-context item must record, at minimum:

- **country**;
- **jurisdiction**, including the relevant Australian state/territory or United States federal/state/local level where applicable;
- **agency or institutional role** when it affects interpretation;
- **encounter type**, such as ordinary service, traffic, welfare, public-order, emergency, questioning, interview, detention, or another explicitly defined category;
- **source date or version**;
- **registered source identifiers or links** supporting any legal or procedural condition supplied to the model; and
- **claim type**, separating linguistic-pragmatic interpretation from legal/procedural correctness, policy description, empirical system comparison, or unresolved context.

The source hierarchy is explicit. Current official legislation, court material, police-service policy/guidance, and other authoritative jurisdiction-specific sources are preferred for legal or procedural propositions. Official institutional reports may support operational terminology or documented practice within their stated scope. Peer-reviewed legal, criminological, sociolinguistic, or related scholarship may motivate bounded descriptive hypotheses. News, television, film, viral clips, body-camera compilations, anecdotes, and community discussion may generate research questions but cannot substitute for a current official source when an item asserts legal authority, rights, compulsion, search power, detention status, caution requirements, or another jurisdiction-specific rule.

Controlled construction should hold the utterance and encounter purpose as constant as practical while varying only the jurisdictional or institutional variable under study. A jurisdiction swap is valid only when the underlying conditions are actually comparable. If the Australian and United States conditions differ in law, role, procedure, or factual setting, the item must expose that difference explicitly rather than pretending it is a clean lexical minimal pair. Appropriate controls include:

- same wording with different supplied jurisdictions when the legal/pragmatic comparison is genuinely matched;
- same jurisdiction with different officer roles, encounter categories, or explicit authority conditions;
- polite wording versus explicit compulsion while holding the legal condition fixed;
- casual address, first-name use, humour, understatement, or `mate` versus a more formal register while holding authority constant;
- fictional or media-script wording versus the current official rule supplied in context; and
- unresolved cases where the evidence does not establish whether an utterance is a request, direction, warning, caution, consent inquiry, or compulsory instruction.

A proposed Australian “lighter touch” hypothesis must therefore be decomposed into observable, source-supported variables such as conversational register, casual address, explicitness, repair, de-escalatory language, or stated compulsion. `Australian` and `American` are never labels for benevolence, danger, coercion, restraint, lawfulness, legitimacy, or conversational style. If the evidence supports only a language/register difference, the benchmark must make only that linguistic claim.

Legal and procedural review is mandatory for high-stakes use. Before publication of a family involving coercion, consent, search, detention, questioning, force, emergency powers, or legal rights, the project must verify the governing sources are current for the recorded jurisdiction and date and obtain appropriate review from relevant Australian and United States legal, policing, civil-liberties, and community expertise. When sources conflict, are stale, or do not establish the requested condition, the item must remain unresolved or be excluded rather than forcing a gold label.

The following boundaries are mandatory:

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

---

## Scoring Philosophy

The following distinctions are mandatory:

- **DEFINED ≠ VALIDATED**
- **BENCHMARK SCORE ≠ CULTURAL COMPETENCE**
- **CORRELATION ≠ PRAGMATIC UNDERSTANDING**
- **ONE ANNOTATOR ≠ CULTURAL CONSENSUS**
- **LEXICAL MATCH ≠ INTENT RECOGNITION**
- **MODEL EXPLANATION ≠ EVIDENCE OF INTERNAL REASONING**

Phase 1 uses deterministic exact matching because it is inspectable. Phase 2 uses deterministic annotation validation and transparent agreement calculations for the same reason. Limitations are documented rather than hidden behind a semantic judge.

---

## Phase 1 Metrics

Phase 1 reports:

- prediction coverage;
- literal interpretation accuracy;
- pragmatic interpretation match;
- ambiguity recognition on annotated ambiguous items;
- hostility classification accuracy on examples with resolved boolean hostility annotations;
- a separate count of examples whose hostility annotation remains `uncertain`;
- social-valence classification accuracy on examples with resolved social-valence annotations;
- a separate count of examples whose social valence remains `unknown`;
- confidence calibration using the Brier score for confidence in pragmatic correctness; and
- directionally correct context-swap sensitivity.

An annotated hostility value of `uncertain` is not a categorical truth label. Such examples are excluded from the hostility-accuracy denominator rather than rewarding a model merely for echoing annotator uncertainty.

Likewise, `social_valence: "unknown"` marks an unresolved annotation rather than a categorical class target. Those examples are excluded from social-valence accuracy and reported separately.

For the Brier component, pragmatic correctness is encoded as `1` when the submitted pragmatic prediction matches an accepted interpretation, including the explicit `insufficient_context` sentinel when declared by the example, and `0` otherwise. The reported value is the mean squared difference between the model's confidence and that binary outcome. Lower is better.

Prediction confidence must be finite and within `[0, 1]`. This constraint is enforced both for JSONL-loaded predictions and for direct library calls to `score()`.

Missing prediction records have no confidence value, so calibration is computed over submitted valid predictions while coverage is reported independently. Missing predictions still count as incorrect in dataset-proportion accuracy metrics and produce evaluation errors.

Phase 1 metrics are deliberately modest and are not a validated scientific instrument.
