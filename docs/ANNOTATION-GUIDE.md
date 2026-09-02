# Annotation Guide

This document describes how human annotation should be conducted for this project.

Phase 1 established the synthetic benchmark substrate. Phase 2 adds an unannotated 60-item pilot pack, an offline annotation interface, per-annotator records, and agreement-analysis tooling. The existence of those tools does **not** mean that the human pilot has already occurred.

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
- Making their uncertainty explicit

Use a pseudonymous `annotator_id`, not a real name, email address, account handle, or other direct identifier. The optional `australian_english_exposure` field records only coarse self-reported familiarity (`low`, `medium`, `high`, or `unspecified`). Do not infer nationality, ethnicity, or other personal identity from an annotation.

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
- The annotator's knowledge and experience

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

Annotators must list alternative interpretations they found plausible even if they ultimately prefer one. This is especially important when:
- Context is ambiguous
- Multiple cultural readings are possible
- The annotator is uncertain about the speaker's intent

Alternatives are not "wrong answers". They are evidence of genuine pragmatic ambiguity.

### CULTURAL DEPENDENCE

Whether specific cultural knowledge appears necessary for interpretation.

Annotators should indicate if they believe:
- A person unfamiliar with Australian English could interpret the utterance differently
- The interpretation relies on knowledge of specific social conventions
- Contextual cues could be opaque to an outsider

---

## Key Principles

### Do Not Invent Context

Annotators must work only with the context provided in the pilot item. They must not invent additional context to resolve ambiguity. If context is insufficient, they must record this explicitly.

### Inter-Annotator Disagreement is Data

When two annotators disagree about the pragmatic interpretation of an utterance, that disagreement is valuable research data. It may indicate genuine pragmatic ambiguity, variation, annotation error, or context insufficiency.

Disagreement should not be "resolved" by silently overriding one annotator's interpretation. Independent annotation records must be retained with their respective confidence values.

### Annotators Bring Their Own Perspective

Annotators should interpret utterances from their own genuine perspective, not attempt to simulate a generic "Australian" speaker. The project may record coarse self-reported familiarity with Australian English, but does not require demographic profiling.

### Do Not Flatten Ambiguity

If an utterance could mean two things and the annotator is genuinely uncertain, both interpretations should be recorded. The annotator should not force a single answer.

### Do Not Use Pair Metadata as an Answer Hint

Phase 2 pilot records may contain `context_swap_group` metadata for later analysis. The annotation interface intentionally hides that field and other pilot tags. Annotators should make each decision from the displayed utterance, context, and relationship rather than reasoning from experimental grouping metadata.

---

## Annotation Workflow (Phase 2)

1. Open `annotation/index.html` locally in a browser.
2. Load `data/pilot/items.jsonl`.
3. Verify and use the read-only pseudonymous annotator ID generated locally by the browser.
4. Read the utterance and supplied context carefully.
5. Record the literal interpretation.
6. Record one or more plausible pragmatic interpretations.
7. Select the primary pragmatic interpretation, or use `insufficient_context` when justified.
8. Identify mechanism(s) from the active taxonomy in `METHODOLOGY.md`.
9. Rate confidence honestly.
10. Record ambiguity, social valence, hostility, cultural dependence, and whether context was required.
11. List alternatives and note the contextual cues that affected the decision.
12. Save locally and export the resulting annotation JSONL.

The browser tool performs no network requests. Local browser storage is a convenience, not an archival or consent mechanism.

---

## Recording Uncertainty

When context is insufficient to determine pragmatic meaning, annotators must use:

- `primary_pragmatic_interpretation: "insufficient_context"`
- at least two distinct retained `pragmatic_interpretations`
- `confidence` at or below 0.4
- `ambiguity: true`

Do not guess when genuinely uncertain. Documented uncertainty is more valuable than a forced guess.

---

## Multiple Annotators

From Phase 2 onwards, each pilot item should have at least two independent human annotations.

The dataset should store all annotations, not just a "consensus" label. The Phase 2 loader rejects duplicate `(example_id, annotator_id)` assignments so a single annotator cannot accidentally count twice on one item.

Validate collected annotation files with:

```bash
python -m australian_for_ais.cli validate-annotations \
  data/pilot/items.jsonl annotations.jsonl
```

Use `--require-two` only when checking whether the pilot has reached the roadmap's minimum coverage criterion.

---

## Inter-Annotator Agreement

Run:

```bash
python -m australian_for_ais.cli agreement \
  data/pilot/items.jsonl annotations.jsonl
```

Phase 2 reports coverage, categorical pairwise agreement, Cohen's kappa for annotator pairs on shared examples, mechanism-set overlap, and descriptive confidence differences.

Free-text pragmatic interpretations are retained for qualitative review and are **not** assigned an exact-string agreement score. Exact wording is not a validated proxy for semantic equivalence, and the project will not hide that limitation behind an unvalidated semantic judge.

See `PHASE2-PILOT-PROTOCOL.md` for the complete pilot procedure and ethical-review checklist.
