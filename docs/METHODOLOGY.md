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

**RQ5:** Do safety or moderation systems disproportionately classify ordinary Australian discourse as hostile or abusive?

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
