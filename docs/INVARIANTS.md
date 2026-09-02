# Core Research Invariants

These invariants are non-negotiable research contracts for this project.

Any code, data, annotation, or evaluation logic that would violate an invariant is incorrect
and must be corrected before merging. If you believe an invariant should be revised, open
an issue and discuss before making changes.

---

## AU-HUMOUR-001

**LEXICAL PROFANITY ≠ SOCIAL AGGRESSION**

The presence of profanity in an utterance is not sufficient evidence that the utterance
expresses social aggression, hostility, or abusive intent.

Formally:
```
profanity(u) = true  ⟹̸  hostile(u) = true
```

An utterance may contain profanity that is:
- Purely emphatic ("bloody brilliant")
- Affectionate ("you absolute bastard, I missed you")
- Self-directed ("I'm such an idiot")
- Conventional filler with no emotional valence

Evaluation systems must not use lexical profanity as a proxy for hostile intent.

---

## AU-HUMOUR-002

**SURFACE SENTIMENT ≠ PRAGMATIC SENTIMENT**

The sentiment inferred from lexical content alone (surface sentiment) is not equivalent to
the socially intended sentiment of an utterance.

Formally:
```
surface_sentiment(u) ≠ pragmatic_sentiment(u, context, relationship)
```

Positive lexical forms may express sarcasm, irony, or contempt.
Negative lexical forms may express affection, humour, or understatement.

Sentiment analysis that ignores context, relationship, and pragmatic register is methodologically
insufficient for language that makes systematic use of these mechanisms.

---

## AU-HUMOUR-003

**"MATE" SHALL NOT BE ASSIGNED A FIXED SOCIAL VALENCE**

The word "mate" is context-dependent and relationship-dependent. No fixed social valence
(e.g., "friendly", "hostile", "neutral") may be assigned to it unconditionally.

Formally: ∄ valence v such that ∀u: contains(u, "mate") ⟹ social_valence(u) = v

"Mate" may be:
- A term of genuine friendship
- A term of mild hostility or sarcasm
- A form of address to a stranger carrying no relational claim
- Part of a sarcastic phrase ("good one, mate")
- Absent entirely from friendly interactions

Any system that assigns a fixed meaning to "mate" has implemented an incorrect heuristic.

---

## AU-HUMOUR-004

**CULTURAL DIFFERENCE ≠ HARMFUL INTENT**

An utterance that departs from language norms of a dominant or reference culture must not
be interpreted as evidence of harmful intent purely on the basis of that cultural difference.

Formally:
```
culturally_marked(u) = true  ⟹̸  harmful_intent(u) = true
```

Flagging or classifying utterances as harmful based on cultural unfamiliarity rather than
actual evidence of harm is a form of cultural discrimination that this project explicitly
aims to study and mitigate.

---

## AU-HUMOUR-005

**MODEL CONFIDENCE SHALL NOT SUBSTITUTE FOR CULTURAL CONTEXT**

A model's high-confidence prediction about pragmatic meaning does not constitute evidence
that the prediction is correct.

Formally:
```
P(model_prediction = x) = high  ⟹̸  correct_interpretation = x
```

Model confidence must be reported separately from cultural evidence.
High confidence in an incorrect pragmatic interpretation is a calibration failure, not a
correct result.

---

## AU-HUMOUR-006

**AMBIGUITY MUST NOT BE SILENTLY COLLAPSED INTO CERTAINTY**

When an utterance has multiple plausible pragmatic interpretations and context is insufficient
to determine which applies, the ambiguity must be represented explicitly.

Formally:
```
|plausible_interpretations(u, context)| > 1  ⟹  ambiguity(u) = true
```

A system that:
- Selects one interpretation without acknowledging alternatives
- Reports a single label without a confidence or uncertainty indicator
- Treats the highest-probability interpretation as the only interpretation

...has collapsed ambiguity in a methodologically unsound manner.

The data model supports `ambiguity: true` and multiple `pragmatic_interpretations` for this reason.

---

## AU-HUMOUR-007

**A CULTURAL HEURISTIC MUST NOT BE TREATED AS A UNIVERSAL RULE**

A heuristic derived from observation of Australian pragmatic language is valid only as a
defeasible tendency, not as a universal rule.

Formally:
```
heuristic H derived from Australian English observations
⟹̸  ∀u ∈ Language: H(u) = correct_interpretation(u)
```

Heuristics must be:
- Documented as hypotheses under investigation
- Marked with confidence levels and scope limitations
- Defeasible by counter-evidence

Any heuristic applied as though it were a universal law is an instance of over-generalisation.

---

## AU-HUMOUR-008

**THE SAME UTTERANCE MAY HAVE DIFFERENT PRAGMATIC MEANINGS UNDER DIFFERENT RELATIONSHIP CONTEXTS**

Formally:
```
∃u, c₁, c₂: c₁ ≠ c₂ ∧ pragmatic_meaning(u, c₁) ≠ pragmatic_meaning(u, c₂)
```

This is the foundational motivation for the context-swap test design.

Example: The utterance "Good one, mate." may express sincere praise in one relational context
and sarcastic criticism in another. Context and relationship must be available to any system
that claims to interpret it.

A model that produces the same output for both contexts has failed to use context information.

---

## AU-HUMOUR-009

**ANNOTATOR INTERPRETATION ≠ OBJECTIVE GROUND TRUTH**

The pragmatic interpretation provided by an annotator is that annotator's interpretation,
not an objective fact about the utterance.

Formally:
```
annotator_label(u) ≠ ground_truth(u)    [in general]
```

Annotation error, annotator cultural background, and inter-annotator disagreement are expected
and must be documented.

Treating single-annotator labels as ground truth:
- Suppresses legitimate interpretive variation
- Bakes annotator bias into the benchmark
- Misrepresents the epistemic status of the data

This is why the schema supports multiple pragmatic interpretations and explicit confidence values.

---

## AU-HUMOUR-010

**BENCHMARK PERFORMANCE ≠ GENERAL CULTURAL UNDERSTANDING**

A model's score on this benchmark does not imply that the model generally understands
Australian culture, or any other culture.

Formally:
```
score(model, benchmark) = high  ⟹̸  culturally_competent(model) = true
```

Benchmark performance:
- Measures only what the benchmark measures
- Is subject to distributional shift between benchmark and real-world language
- May be inflated by lexical pattern-matching rather than genuine pragmatic reasoning
- Is bounded by the quality and representativeness of the dataset

Claims of "cultural understanding" based on benchmark scores alone overstate the evidence.
