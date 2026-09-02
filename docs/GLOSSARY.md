# Glossary

Definitions used in this project. Where terms have established meanings in linguistics or
NLP, those meanings are followed. Project-specific terms are noted.

---

**Affectionate insult**
An utterance that uses insulting language (often profanity or derogatory terms) to express
affection, solidarity, or friendly mockery rather than genuine hostility.

**Ambiguity** (pragmatic)
The condition in which an utterance has two or more substantially different plausible pragmatic
interpretations and available context is insufficient to determine which applies with high confidence.

**Annotator confidence**
A numeric value (0.0–1.0) representing the annotator's self-reported certainty about their
pragmatic interpretation of an utterance.

**Australian English**
A variety of English spoken in Australia, characterised in part by extensive use of pragmatic
mechanisms including understatement, irony, and affectionate insult. Australian English is not
homogeneous; it encompasses regional, generational, socioeconomic, and individual variation.

**Benchmark**
A standardised test set and evaluation methodology used to compare AI system capabilities.
A benchmark score measures performance on the benchmark, not general capability.

**Context**
Situational information available at the time of an utterance that influences its interpretation.
Includes speaker relationship, setting, preceding conversation, and social norms.

**Context-swap**
A benchmark design element in which the same utterance appears with two different contexts
producing different expected pragmatic interpretations. Designed to test whether model
interpretations depend on context rather than lexical content alone.

**Cultural dependency**
The degree to which correct interpretation of an utterance requires specific cultural knowledge.

**Deadpan**
A manner of presenting humorous or absurd content without tonal cues indicating humour.
The utterance is delivered "straight", requiring the listener to recognise humour from context.

**Discourse marker**
A word or phrase that indicates the speaker's communicative stance or organises the structure
of discourse. In some Australian contexts, a sequence such as "yeah nah" can function as a
softened rejection, but its interpretation depends on discourse position, relationship, prosody,
and other contextual cues rather than a fixed phrase-to-intent rule.

**Hostility** (annotation field)
Whether an utterance expresses aggressive social intent toward the addressee. A ternary value:
true / false / uncertain. Not to be inferred from lexical content alone (see AU-HUMOUR-001).

**Inter-annotator agreement (IAA)**
A measure of consistency between multiple annotators labelling the same data. Disagreement
is informative rather than merely noise in this project.

**Inverse praise**
Ostensibly positive language used to express a negative evaluation, often sarcastically.
Example: "Brilliant work." said to someone who has just made a mistake.

**Irony**
Stating the opposite of what one means, typically to achieve humour or rhetorical effect.

**Literal interpretation**
The denotative, context-free semantic reading of an utterance. What the words say in isolation.

**Locale**
Language variety identifier. Phase 1 uses "en-AU" for Australian English.

**Minimal pair**
Two example variants that differ in exactly one feature (e.g., speaker relationship or
preceding event) while keeping lexical content constant. Used to measure context sensitivity.

**Pragmatic interpretation**
The socially intended meaning of an utterance given context, relationship, and cultural
knowledge. May differ substantially from literal interpretation.

**Pragmatics**
The branch of linguistics studying how context contributes to meaning. Concerned with the
use of language in social interaction.

**Profanity (non-hostile)**
Profanity used for emphasis, affection, or conventional expression without hostile or
aggressive intent. See AU-HUMOUR-001.

**Provenance**
Documentation of an example's origin, including source, consent status, and licence.

**Sarcasm**
Use of praise language to express criticism or contempt. A form of inverse praise.

**Self-deprecation**
Intentional minimisation of one's own abilities, status, or success, often for humorous
or social effect.

**Social valence**
The social register of an utterance: friendly / hostile / neutral / ambiguous / unknown.
Not to be inferred from lexical content alone for context-dependent utterances.

**Source type**
Category describing how an example originated:
- synthetic — created as a project fixture
- naturalistic — drawn from real speech/text
- constructed — deliberately constructed for the benchmark

**Speaker relationship**
The social relationship between the speaker and the addressee (e.g., close friends,
strangers, colleagues, adversaries). A critical contextual variable for pragmatic interpretation.

**Tall-poppy humour**
Deflation of exceptional success or status for comic or social effect. Related to the
"tall poppy" cultural tendency to cut down those who are seen as elevating themselves.

**Understatement**
Deliberate use of language that significantly diminishes a situation or achievement, often
for humorous or emphatic effect.

**Utterance**
The observed linguistic form of a statement. The actual words used.
