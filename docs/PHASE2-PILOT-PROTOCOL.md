# Phase 2 Pilot Human Annotation Protocol

## Status

This document defines the Phase 2 pilot procedure. It does **not** claim that the human pilot has been completed. The repository supplies the annotation tooling, a 60-item pilot pack, validation contracts, and deterministic agreement analysis. Human collection remains a real-world research activity and must not be fabricated or simulated by an AI agent.

## Purpose

The pilot tests whether the Phase 1 annotation concepts are usable by independent human annotators before a larger culturally contextualised dataset is created.

The pilot is intended to reveal:

- confusing or underspecified annotation instructions;
- fields on which annotators systematically disagree;
- contexts that are insufficient to support a single reading;
- taxonomy labels that are difficult to apply consistently;
- whether the benchmark design accidentally encourages lexical shortcuts;
- practical issues that should be fixed before Phase 3.

Agreement is diagnostic evidence about the annotation process. It is not proof of objective cultural ground truth.

## Pilot pack

`data/pilot/items.jsonl` contains 60 independently authored synthetic items. They are deliberately **unannotated**: pilot records contain observations and supplied context, not hidden gold pragmatic labels.

The 60 items form 30 context-contrast pairs. Pair metadata is retained for later analysis but should not be shown to annotators during an annotation decision. The offline interface therefore presents only the utterance, supplied context, and speaker relationship.

The pair design is a pilot instrument, not a released benchmark. Phase 2 annotations may show that a proposed pair is ambiguous, poorly controlled, or unsuitable. Such a result is useful and must not be edited away merely to make a context-swap hypothesis succeed.

## Annotator independence

Each pilot item should receive at least two independent human annotations.

Annotators should:

1. work from the supplied item only;
2. avoid discussing an item with other annotators before submitting their own annotation;
3. avoid consulting a supposed answer key, because none is provided;
4. record genuine uncertainty rather than forcing agreement;
5. use a pseudonymous `annotator_id` rather than a name, email address, account handle, or other direct identifier.

The project does not require demographic inference from language. The optional `australian_english_exposure` field is a coarse, non-identifying self-report (`low`, `medium`, `high`, or `unspecified`) and must not be used to infer nationality, ethnicity, or other personal identity.

## Annotation interface

Open `annotation/index.html` directly in a browser. It is self-contained and makes no network requests.

1. Select `data/pilot/items.jsonl`.
2. Enter a pseudonymous annotator ID.
3. Annotate items from the supplied context only.
4. Save each item locally in the browser.
5. Export the saved records as JSONL.

The interface intentionally does not display pilot tags or `context_swap_group` metadata.

## Required annotation fields

Each independent record follows `schemas/annotation.schema.json` and records:

- literal interpretation;
- one or more plausible pragmatic interpretations;
- primary pragmatic interpretation, or the exact `insufficient_context` sentinel;
- pragmatic mechanism tags from the active taxonomy;
- social valence;
- hostility;
- confidence;
- ambiguity;
- cultural dependency;
- whether context materially affects interpretation;
- optional alternatives and notes;
- optional coarse Australian-English exposure.

The Phase 1 uncertainty contract remains active. `insufficient_context` requires `ambiguity: true`, at least two distinct retained pragmatic readings, and confidence at or below `0.4`.

## Validation

Validate the pilot pack:

```bash
python -m australian_for_ais.cli validate-pilot data/pilot/items.jsonl
```

Validate collected annotations against the pilot item IDs:

```bash
python -m australian_for_ais.cli validate-annotations \
  data/pilot/items.jsonl annotations.jsonl
```

To enforce the Phase 2 graduation requirement of at least two annotations per item:

```bash
python -m australian_for_ais.cli validate-annotations \
  data/pilot/items.jsonl annotations.jsonl --require-two
```

## Agreement analysis

Run:

```bash
python -m australian_for_ais.cli agreement \
  data/pilot/items.jsonl annotations.jsonl
```

or:

```bash
python scripts/analyse_annotations.py \
  data/pilot/items.jsonl annotations.jsonl
```

The report includes:

- annotation coverage;
- descriptive within-item pairwise agreement for categorical fields;
- Cohen's kappa for each annotator pair on shared items;
- exact-set and Jaccard overlap for mechanism tags;
- descriptive confidence differences.

Free-text pragmatic interpretations are **not** assigned an exact-string IAA score. Two people may express the same interpretation with different wording, and an unvalidated semantic judge would hide that uncertainty rather than solve it. Free-text readings remain qualitative evidence for review and adjudication.

## Ethical review checklist

Before recruiting pilot annotators, document:

- who is coordinating the pilot;
- what participants are being asked to do;
- what data will be retained;
- how pseudonymous IDs are assigned;
- whether compensation is offered;
- how participants can withdraw before publication;
- where annotation files are stored;
- whether any naturalistic data are added beyond the synthetic pilot pack.

Do not collect unnecessary personal data. Do not treat one annotator as a representative of all Australian speakers.

## Phase 2 exit condition

The software and pilot pack can be ready before Phase 2 is complete. Phase 2 graduates only after real human annotation has occurred, at least two independent annotations exist for each pilot item, agreement is measured and reported, the annotation guide is revised from observed pilot experience, and the annotation process has received an explicit ethical review.
