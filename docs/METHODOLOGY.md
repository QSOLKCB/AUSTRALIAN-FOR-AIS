# Methodology

## Research Principle

Language meaning is conditional on context, culture, relationship, discourse, and uncertainty.
Surface lexical meaning alone is not sufficient evidence of intended social meaning.

This principle motivates using Australian English as a benchmark environment. Australian English
makes systematic use of pragmatic mechanisms — understatement, irony, affectionate insult,
deadpan humour — that create a substantial gap between surface and intended meaning.

---

## What This Project Studies

The project studies whether AI systems can:

1. Recognise that surface and pragmatic meaning differ
2. Use contextual information to inform pragmatic interpretation
3. Represent genuine ambiguity rather than collapsing it
4. Calibrate confidence appropriately for culturally dependent language
5. Distinguish lexical profanity from social aggression
6. Detect when "the same utterance means different things" given different contexts

---

## Research Questions

**RQ1:** Can language models distinguish lexical profanity from social aggression?

**RQ2:** Does providing relationship context materially improve pragmatic interpretation
accuracy?

**RQ3:** Can models correctly recognise when an utterance is pragmatically ambiguous?

**RQ4:** Do models become overconfident when interpreting culturally dependent humour?

**RQ5:** Do safety or moderation systems disproportionately classify ordinary Australian
discourse as hostile or abusive?

**RQ6:** Can models distinguish sincere praise from inverse praise when lexical content is
identical?

**RQ7:** Do context-swap examples expose reliance on lexical shortcuts rather than genuine
contextual reasoning?

**RQ8:** How much of performance on this benchmark transfers to other dialects or cultural
settings?

These are questions under investigation, not assumed conclusions.

---

## Taxonomy of Pragmatic Mechanisms

The following mechanisms appear in the starter dataset and are used as tags in example records.
The taxonomy is extensible and not claimed to be exhaustive.

| Tag | Description |
|---|---|
| `understatement` | Deliberately diminished description of a significant situation |
| `sarcasm` | Use of praise language to express criticism or contempt |
| `irony` | Stating the opposite of what is meant |
| `deadpan` | Presenting absurd or humorous content without tonal cues |
| `affectionate_insult` | Insulting language used to express affection or solidarity |
| `inverse_praise` | Ostensible positive framing expressing negative evaluation |
| `profanity_non_hostile` | Profanity without hostile or aggressive intent |
| `discourse_marker` | Conversational markers such as "yeah nah" that carry pragmatic meaning |
| `self_deprecation` | Intentionally diminished self-representation |
| `absurdist_escalation` | Escalation to an absurd degree for comic or emphatic effect |
| `relational_teasing` | Humour directed at a specific person within an established relationship |
| `tall_poppy_humour` | Deflation of success or status (related to tall poppy cultural pattern) |
| `ambiguous_address` | Address terms whose social valence depends on relationship and context |
| `literal` | The utterance is intended and interpreted at face value |
| `unknown` | The mechanism cannot be determined from available information |

Examples may carry multiple tags. Tags represent analytical hypotheses, not established facts.

---

## Context-Swap Design

A context-swap pair consists of:

- The same utterance
- Two or more different contexts
- Different expected pragmatic interpretations for each context

Context-swap tests are designed to measure whether a model's interpretation is actually
influenced by context, or whether it relies solely on lexical content.

A model that produces the same interpretation for both contexts of a context-swap pair has
failed to use context information — even if that interpretation happens to be correct for
one of the contexts.

---

## Minimal Pairs

Future phases will use minimal pairs: example variants that differ in exactly one feature
(speaker relationship, preceding event, tone description, or social setting) while keeping
lexical content constant.

Minimal pairs allow measurement of whether changing one contextual dimension changes model output.

---

## Scoring Philosophy

The following distinctions must be maintained:

- **DEFINED ≠ VALIDATED**: A metric that has been defined is not automatically validated.
- **BENCHMARK SCORE ≠ CULTURAL COMPETENCE**: See AU-HUMOUR-010.
- **CORRELATION ≠ PRAGMATIC UNDERSTANDING**: Statistical correlation between model output
  and labels does not imply the model understands pragmatic meaning.
- **ONE ANNOTATOR ≠ CULTURAL CONSENSUS**: Single-annotator labels are not culturally
  representative. See AU-HUMOUR-009.
- **LEXICAL MATCH ≠ INTENT RECOGNITION**: Matching an expected output string does not
  demonstrate the model recognised communicative intent.
- **MODEL EXPLANATION ≠ EVIDENCE OF INTERNAL REASONING**: A model's verbal explanation of
  its interpretation is not evidence about its actual internal process.

These distinctions are enforced in the reference evaluator and documented in invariants.

---

## Phase 1 Scope

Phase 1 implements component metrics that can be defined rigorously against synthetic fixtures:

- **Literal interpretation accuracy**: Does the model correctly identify the literal meaning?
- **Pragmatic interpretation match**: Does the predicted pragmatic interpretation match any
  of the annotated plausible interpretations?
- **Ambiguity recognition**: Does the model correctly identify ambiguous examples as ambiguous?
- **Hostility classification**: Does the model correctly classify `hostility` (true/false/uncertain)?
- **Social-valence classification**: Does the model correctly classify social valence?
- **Uncertainty calibration**: Is the model's reported confidence appropriate?
- **Context sensitivity**: Does model output change between context-swap examples?

Phase 1 metrics are deliberately modest. They do not constitute a validated scientific instrument.
