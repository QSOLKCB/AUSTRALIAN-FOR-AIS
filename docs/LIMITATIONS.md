# Limitations

This document describes known limitations of the Australian For AIs project.

---

## Phase 1 Limitations

### Synthetic Data

Phase 1 uses synthetic examples created as project fixtures. These examples demonstrate
the schema and evaluation pipeline but are not a representative sample of real Australian
speech. No conclusions about model performance should be drawn from Phase 1 evaluation results.

### Single Annotator

Phase 1 examples were created by the project authors, not independently annotated by multiple
human annotators. The pragmatic interpretations and confidence values represent the authors'
views, not a culturally representative sample.

### Small Dataset

Approximately 15 examples is far too small for meaningful statistical analysis. Phase 1 is
a scaffold, not a benchmark.

### No Adversarial Testing

Phase 1 does not include adversarial examples designed to probe specific model failure modes.
This is deferred to Phase 5.

### No Real-World Validation

The synthetic examples have not been validated against the judgements of real speakers of
Australian English. This is a significant limitation.

---

## Structural Limitations

### Australian English is Not Homogeneous

This project uses "Australian English" as a convenient label, but Australian English
encompasses significant regional, generational, socioeconomic, and individual variation.

The pragmatic mechanisms studied here may be more or less salient in different varieties
and for different speakers. Findings must not be generalised to all Australian speakers.

### Cultural Phenomena Are Not Uniquely Australian

The pragmatic mechanisms studied here — understatement, irony, affectionate insult,
deadpan humour — are not unique to Australian English. They appear in many varieties of
English and other languages.

Australian English is used as a benchmark environment because these mechanisms are particularly
prominent and well-documented here. This does not mean findings are inapplicable elsewhere,
or that they are universal.

### Annotator Cultural Background

Annotation quality depends on the annotator's familiarity with Australian pragmatic conventions.
Phase 2 must document annotator backgrounds and include annotators with diverse relationships
to Australian English.

### Benchmark Cannot Test All Pragmatic Mechanisms

The taxonomy in METHODOLOGY.md is not exhaustive. The benchmark cannot test mechanisms that
have not been identified and operationalised.

### Evaluation Metrics Are Approximate

The component metrics defined in Phase 1 are approximations. They measure observable
correlates of pragmatic understanding, not pragmatic understanding itself.

In particular:
- Pragmatic match is measured by string comparison against a finite list of annotations,
  not by semantic equivalence.
- Ambiguity recognition depends on whether the benchmark has correctly identified ambiguous
  examples.

---

## Research Limitations

### Benchmark Performance ≠ Cultural Competence

See AU-HUMOUR-010 and METHODOLOGY.md. A model that scores highly on this benchmark has not
been demonstrated to be culturally competent in any general sense.

### No Causal Claims

This project can document correlations between model outputs and pragmatic features, but
cannot make causal claims about why models perform as they do.

### Transfer to Other Dialects

Whether findings from this benchmark transfer to other dialects is an open research question
(RQ8). Do not assume transfer.

### Phase 1 is Not a Validated Scientific Instrument

Phase 1 establishes a research scaffold. It is not a validated psychometric instrument or
an accepted scientific benchmark. Researchers should not publish findings from Phase 1 alone
without clearly disclosing these limitations.
