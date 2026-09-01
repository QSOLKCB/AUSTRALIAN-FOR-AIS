# Annotation Guide

This document describes how future human annotation should be conducted for this project.

Phase 1 uses synthetic examples only. This guide prepares the annotation framework for
Phase 2 onwards.

---

## Annotator Roles

Annotators provide pragmatic interpretations of utterances given context.

Annotators are **not**:
- Final arbiters of cultural meaning
- Representatives of "all Australians" or any other cultural group
- Producing objective ground truth

Annotators are:
- Providing documented, hedged interpretations from their own perspective
- Contributing to a distribution of possible interpretations
- Making their uncertainty and cultural context explicit

---

## What Annotators Must Distinguish

### OBSERVATION

What was literally said.

The linguistic form of the utterance. Context-free. Not an interpretation.

Example: The utterance "Yeah, nah." is observed as two words in a particular sequence.

### INTERPRETATION

What the annotator believes was intended.

An inference about communicative intent based on:
- The utterance
- The provided context
- The annotator's cultural knowledge and experience

The annotator must label this as an interpretation, not a fact.

### CONTEXT

What information influenced the interpretation.

Annotators must identify which contextual elements were necessary to arrive at their interpretation.

Example: "I only read this as sarcastic because the context said the parking was terrible."

### CONFIDENCE

How certain the annotator is about their interpretation.

Expressed as a number between 0.0 and 1.0.

- 1.0 = completely certain
- 0.8 = highly likely
- 0.5 = roughly equal chance of multiple interpretations
- 0.3 = uncertain, leaning toward one interpretation
- 0.0 = no basis for confidence

Annotators should report genuine uncertainty and not inflate confidence to appear more authoritative.

### ALTERNATIVES

Other plausible interpretations the annotator considered.

Annotators must list alternative interpretations they found plausible even if they ultimately
prefer one. This is especially important when:
- Context is ambiguous
- Multiple cultural readings are possible
- The annotator is uncertain about the speaker's intent

Alternatives are not "wrong answers" — they are evidence of genuine pragmatic ambiguity.

### CULTURAL DEPENDENCE

Whether specific cultural knowledge appears necessary for interpretation.

Annotators should indicate if they believe:
- A person unfamiliar with Australian English would interpret the utterance differently
- The interpretation relies on knowledge of specific social conventions
- Contextual cues would be opaque to an outsider

---

## Key Principles

### Do Not Invent Context

Annotators must work only with the context provided in the example record. They must not
invent additional context to resolve ambiguity. If context is insufficient, they must
record this explicitly.

### Inter-Annotator Disagreement is Data

When two annotators disagree about the pragmatic interpretation of an utterance, that
disagreement is valuable research data. It indicates genuine pragmatic ambiguity, cultural
variation, or context insufficiency.

Disagreement should not be "resolved" by overriding one annotator's interpretation. Both
interpretations should be retained in the dataset with their respective confidence values.

### Annotators Bring Their Own Perspective

Annotators should interpret utterances from their own genuine perspective, not attempt to
simulate a generic "Australian" speaker. Their cultural background and relationship to
Australian English should be documented as metadata.

### Do Not Flatten Ambiguity

If an utterance could mean two things and the annotator is genuinely uncertain, both
interpretations should be recorded. The annotator should not force a single answer.

---

## Annotation Workflow (Phase 2)

1. **Read the utterance and context carefully.**
2. **Record the literal interpretation** — what the words say in isolation.
3. **Record your pragmatic interpretation** — what you believe was intended.
4. **Identify the mechanism(s)** — what pragmatic device is in use (see taxonomy in METHODOLOGY.md).
5. **Rate your confidence** — how certain are you?
6. **List alternatives** — what other readings did you consider?
7. **Note cultural dependence** — does this require specific cultural knowledge?
8. **Note insufficient context** — if context is genuinely insufficient, say so.

---

## Recording Uncertainty

When context is insufficient to determine pragmatic meaning, annotators must use:

- `primary_pragmatic_interpretation: "insufficient_context"` in the record
- A `confidence` value at or below 0.4
- `ambiguity: true`

Do not guess when genuinely uncertain. Documented uncertainty is more valuable than a forced guess.

---

## Multiple Annotators

From Phase 2 onwards, each example should have at least two independent annotations.

The dataset should store all annotations, not just a "consensus" label.

Inter-annotator agreement will be measured using appropriate metrics and reported as part of
the dataset documentation. Agreement is informative but disagreement is equally informative.
