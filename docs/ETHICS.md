# Ethics

This document describes the ethical considerations, risks, and commitments of the Australian
For AIs project. It should be read by all contributors and researchers before working with
the project.

---

## Core Commitments

**This project must not be used to infer whether a person is Australian.**

**This project must not be used to infer ethnicity, nationality, or identity from language.**

**This project evaluates language understanding, not personal identity.**

These commitments are unconditional.

---

## Identified Risks

### Cultural Stereotyping

Risk: The benchmark may reify Australian English as a monolithic variety, implying all
Australians speak this way or that these pragmatic patterns are universal among Australian
speakers.

Mitigation:
- Documentation explicitly states Australian English is not homogeneous.
- Individual examples are not claimed to represent all Australian speakers.
- The taxonomy is presented as a set of observed mechanisms, not cultural rules.

### Dialect Discrimination

Risk: Systems trained or evaluated on this benchmark may perform poorly on Australian
English, but this could be misinterpreted as Australian English being in some way less
"standard" or less deserving of accurate processing.

Mitigation:
- The project frames poor performance as a model limitation, not a dialect deficiency.
- Documentation emphasises that dialectal variation is a normal feature of language.

### Moderation False Positives

Risk: An AI system that does not understand Australian pragmatic language may flag ordinary
Australian speech as hostile, abusive, or violating, suppressing legitimate communication.

This is one of the primary harms this project is designed to study. False positive moderation
rates for culturally marked language are a form of systemic discrimination.

### Moderation False Negatives

Risk: A system may fail to detect genuinely hostile language that happens to use pragmatic
forms similar to legitimate Australian speech.

Mitigation: The benchmark must include examples where profanity is genuinely hostile as
well as examples where it is not. Phase 1 defers hostile examples to protect annotator
wellbeing, but this must be addressed in future phases.

### Over-Generalisation

Risk: Findings from this benchmark may be applied too broadly to other dialects or languages
without evidence that they transfer.

Mitigation: See AU-HUMOUR-007. Explicit documentation in LIMITATIONS.md. Phase 7 of the
roadmap addresses cross-dialect comparison with appropriate care.

### Treating Cultural Membership as Predictable Behaviour

Risk: Someone might use this project to claim that knowing a person is Australian predicts
their pragmatic patterns. This conflates group membership with individual behaviour.

Mitigation: Documentation repeatedly states this project studies language mechanisms, not
people. Identity inference from language is explicitly prohibited.

### Mistaken Hostility Detection

Risk: A model may classify affectionate insults, friendly profanity, or sarcastic praise as
hostile, triggering downstream harms (moderation action, escalation, misclassification).

This is the direct subject of AU-HUMOUR-001.

### Mistaken Sentiment Detection

Risk: Positive-valence sarcasm or negative-form compliments may be miscategorised by
sentiment analysis systems, producing inaccurate representations of community opinion.

This is the direct subject of AU-HUMOUR-002.

### Mistaken Intent Inference

Risk: An AI system may infer hostile, aggressive, or non-consenting intent from language
that is pragmatically ordinary in its context.

This has implications for content moderation, legal reasoning systems, and human-AI interaction.

### Annotator Bias

Risk: Annotations from a narrow set of annotators may reflect their cultural background,
relationship to Australian English, or personal interpretive tendencies, rather than any
broader cultural consensus.

Mitigation: Multiple annotators, explicit uncertainty representation, and treatment of
inter-annotator disagreement as data rather than noise. See AU-HUMOUR-009.

### Privacy

Risk: Examples derived from real conversations may contain personally identifying information.

Mitigation: Phase 1 uses only synthetic examples. Future phases must document consent and
provenance for all real examples. Private conversations must not be included without explicit
consent.

### Dataset Consent

Risk: Including public language data (social media, forum posts) without consent from
speakers raises ethical and legal concerns.

Mitigation: Data governance policy (DATA-GOVERNANCE.md) prohibits scraping without consent.
All future examples must have documented provenance and licence.

### Provenance

Risk: Examples without clear provenance may be copyright material, private data, or
fabricated without documentation.

Mitigation: Every example must include a `provenance` field. Synthetic examples are explicitly
labelled. Real examples must document source and licence.

### Demographic Inference

Risk: This project could be used to build tools that infer a speaker's demographic background
from language use.

Such use is prohibited. This project evaluates language understanding, not speaker identity.

### Benchmark Gaming

Risk: A model optimised specifically against this benchmark may score highly without any
genuine improvement in pragmatic understanding.

Mitigation: Separation of development and test splits in future phases. Documentation that
benchmark score ≠ cultural competence (see AU-HUMOUR-010). Publication of methodology before
evaluation data.

### Cultural Flattening

Risk: The project may flatten the diversity within Australian English — regional variation,
socioeconomic variation, Indigenous varieties, migrant varieties — into a single homogeneous
"Australian" category.

Mitigation: Documentation of limitations. Future phases must seek to represent internal
diversity rather than treating "Australian English" as uniform.

---

## Ethical Review

Phases involving real human data (Phase 2 onwards) must be reviewed by an appropriate
institutional ethics board or equivalent process before data collection begins.

Phase 1 uses only synthetic examples and does not involve human participants beyond
researchers creating the scaffold. However, the ethics principles documented here apply from
the beginning.

---

## Reporting Ethical Concerns

Ethical concerns about project content, methodology, or use should be raised as GitHub issues
labelled "ethics". Serious concerns (privacy violations, discriminatory content) should be
reported to project maintainers directly.
