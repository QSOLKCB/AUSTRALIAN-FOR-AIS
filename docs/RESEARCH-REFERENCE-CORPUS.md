# Research Reference Corpus

## Status

This document is a **research reference registry**, not a benchmark dataset and not a licence to redistribute source material.

The listed works are used to identify pragmatic mechanisms, construct research hypotheses, and design original synthetic or appropriately licensed benchmark items. Their inclusion does **not** imply that their dialogue, scripts, subtitles, transcripts, audiovisual material, characters, or other copyrighted expression may be copied into this repository.

The project must preserve the distinction:

> RESEARCH REFERENCE != REDISTRIBUTABLE DATA

and:

> COMEDIC DEPICTION != REPRESENTATIVE CULTURAL GROUND TRUTH

Australian comedy is used here as a rich source of adversarial pragmatic structures. It is not treated as a census of how Australians speak.

---

## Source-use rules

1. Use references to identify **mechanisms**, not to copy jokes or dialogue.
2. Prefer original synthetic examples, minimal pairs, and context swaps for benchmark data.
3. Record provenance and licence for every benchmark example independently of the reference that motivated it.
4. Do not infer that a fictional character, sketch, or satirical programme represents a demographic group.
5. Do not convert a comedy writer's premise into a universal linguistic rule.
6. Treat automatic transcripts as noisy observations until human-verified against an authorised source.
7. A reference may support a hypothesis without proving it.
8. Wikipedia and similar summaries are orientation sources, not substitutes for primary scholarship or rights information.
9. Political satire should be analysed for pragmatic structure, not used to encode a preferred political conclusion.
10. Historical material must be interpreted in the norms and media context of its period rather than silently projected onto contemporary Australian English.

---

## Priority A: adversarial pragmatics

### The Chaser / *The Chaser's War on Everything*

**Reference:**
- https://en.wikipedia.org/wiki/The_Chaser
- https://www.abc.net.au/tv/guide/abc2/200603/programs/LE0502H006D25032006T213000.htm

**Research priority:** Very high.

The Chaser is especially valuable because its comedy repeatedly places satirical intent inside real-world, institution-shaped interactions. ABC's programme description identifies confrontation and lampooning of politics, business, religion, media, and culture alongside news analysis, sketches, and field experiments.

Candidate pragmatic mechanisms for later formalisation:

- `institutional_mimicry`
- `adversarial_questioning`
- `satirical_question_form`
- `performative_sincerity`
- `literalised_absurdity`
- `authority_register_parody`
- `social_norm_violation`
- `frame_collision`

Key benchmark question:

> Can a model recognise satire when real people, real locations, formal language, and question-shaped utterances all superficially signal literal seriousness?

A future Chaser-inspired test family should use **newly written scenarios** that preserve these structures without reproducing programme dialogue.

---

### Russell Coight's *All Aussie Adventures*

**Reference:** https://en.wikipedia.org/wiki/All_Aussie_Adventures

The series is an Australian mockumentary parody of travel-adventure television. Its central structure is especially useful for testing conflicts between an authoritative register and demonstrated competence.

Candidate mechanisms:

- `deadpan`
- `unreliable_authority`
- `asserted_competence_conflict`
- `mockumentary_frame`
- `bush_mythology_parody`
- `expert_register_parody`

Key benchmark question:

> Does a model treat confident expert-style narration as evidence of competence even when the surrounding context contradicts it?

---

## Priority B: sketch, persona, and context switching

### *Fast Forward*

**Reference:** https://en.wikipedia.org/wiki/Fast_Forward_(Australian_TV_series)

The programme's media-focused sketch format and channel-changing device make it useful for studying abrupt frame changes, parody, impersonation, and the distinction between performed media register and sincere assertion.

Candidate mechanisms:

- `media_parody`
- `frame_switching`
- `performed_persona`
- `institutional_mimicry`
- `impersonation_context`

---

### *Full Frontal*

**Reference:** https://en.wikipedia.org/wiki/Full_Frontal_(Australian_TV_series)

The series continued the rapid sketch-to-sketch, channel-surfing grammar associated with *Fast Forward*. It is useful for persona separation, parody, character speech, and abrupt pragmatic reframing.

Candidate mechanisms:

- `performed_persona`
- `frame_switching`
- `parody_register`
- `character_speaker_separation`

A model must not infer performer belief directly from a character utterance.

---

### *The Eric Bana Show Live*

**Reference:** https://en.wikipedia.org/wiki/The_Eric_Bana_Show_Live

The programme combined celebrity guests, music, monologues, sketches, and characters carried over from earlier comedy work. This makes it useful for distinguishing host speech, performed persona, character speech, interview register, and sketch framing.

Candidate mechanisms:

- `performed_persona`
- `character_speaker_separation`
- `register_transition`
- `interview_vs_sketch_frame`

---

### *skitHOUSE*

**Reference:** https://en.wikipedia.org/wiki/Skithouse

The short-form sketch structure is useful for compressed absurdity, conversational reversal, social awkwardness, puns, and rapidly changing premises.

Candidate mechanisms:

- `absurdist_escalation`
- `context_reversal`
- `social_script_violation`
- `misunderstanding`
- `deadpan`

Any machine-generated transcript used during research must remain a non-authoritative aid until verified. No transcript should become gold benchmark text merely because an ASR system produced it.

---

## Priority C: relational and implicature-heavy comedy

### *Hey Dad..!*

**Reference:** https://en.wikipedia.org/wiki/Hey_Dad..!

As a long-running domestic sitcom, this source is potentially useful for studying family-role context, generational interaction, relational teasing, and utterances whose pragmatic interpretation depends on recurring relationships.

Candidate mechanisms:

- `relationship_conditioned_meaning`
- `domestic_banter`
- `generational_register`
- `relational_teasing`

Historical sitcom dialogue should not be treated as representative of contemporary Australian English without additional evidence.

---

### Col'n Carpenter

**Reference:** https://www.screenaustralia.gov.au/screen-guide/coln-carpenter-2636/

Screen Australia records *Col'n Carpenter* as a comedy series centred on the title character's misadventures. The character lineage is useful for research into naïveté, misunderstanding, failed implicature, and confidence that exceeds comprehension.

Candidate mechanisms:

- `implicature_failure`
- `naivete`
- `misunderstanding`
- `confident_misinterpretation`
- `social_script_misalignment`

---

## Theoretical reference

### Slade, Trent. *The Antipodean Jester: Australian Humor as Informal Governance in a Comparative Sociological Framework*

**DOI:** https://doi.org/10.22541/au.176780580.02987307/v1

**Status:** Preprint, posted 7 January 2026. The source explicitly states that it has not been peer reviewed and that data may be preliminary. It is distributed as CC BY 4.0.

The paper proposes that Australian humour can function as informal social regulation and discusses ridicule, irony, understatement, deadpan delivery, "taking the piss", Tall Poppy dynamics, the larrikin archetype, ambiguity, in-group signalling, exclusion, and cross-cultural misunderstanding.

For this repository, these claims are **hypotheses and conceptual prompts**, not established benchmark ground truth.

Candidate research mappings include:

- ambiguity tolerance
- hostile-play versus hostile-intent separation
- teasing as bonding versus exclusion
- anti-authority pragmatics
- understatement
- deadpan delivery
- tall-poppy / anti-pretension mechanisms
- high-context interpretation

---

## Candidate future taxonomy extensions

The Phase 1 schema intentionally keeps its active taxonomy small. The following labels are therefore **research candidates only** and MUST NOT be inserted into `humour_mechanisms` until the JSON Schema, data model, documentation, and tests are deliberately updated together:

- `institutional_mimicry`
- `adversarial_questioning`
- `satirical_question_form`
- `performative_sincerity`
- `unreliable_authority`
- `performed_persona`
- `character_speaker_separation`
- `frame_switching`
- `context_reversal`
- `implicature_failure`
- `relationship_conditioned_meaning`

This separation prevents the research notebook from silently mutating the benchmark contract.

---

## Research design derived from the corpus

The corpus suggests several high-value experimental constructions for later phases:

### 1. Context swaps

Hold the utterance constant while changing relationship, preceding event, or social setting.

### 2. Authority inversions

Hold an expert-like register constant while varying whether surrounding evidence supports or contradicts the speaker's competence.

### 3. Question-intent swaps

Use the same grammatical question form for genuine information seeking, sarcasm, accusation, satire, and performative bait.

### 4. Persona swaps

Hold wording constant while changing whether it is delivered as the speaker, a fictional character, a parody presenter, or a quoted third party.

### 5. Institutional-frame swaps

Use similar language inside genuine news, fake news parody, corporate PR, political satire, and ordinary conversation.

These constructions are preferable to copying source dialogue because they provide controlled variables, clean provenance, and clearer inference about model behaviour.

---

## Copyright and provenance boundary

Unless a source is separately established as permissively licensed for the intended use:

- do not copy scripts or subtitles;
- do not commit episode transcripts;
- do not bulk-extract dialogue;
- do not treat availability on the web as permission to redistribute;
- do not assume quotation rights imply dataset redistribution rights.

References may be cited for criticism, research design, and provenance. Benchmark examples should be independently authored or otherwise licensed and documented.
