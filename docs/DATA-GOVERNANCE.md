# Data Governance

## Principles

This project takes data provenance, consent, and licensing seriously.

Every record must have documented provenance. Records without provenance are not acceptable
in the dataset.

---

## Phase 1 — Synthetic Data

All Phase 1 examples are synthetic. They were generated as project fixtures to demonstrate
the schema and evaluation pipeline. They are not derived from real conversations.

Synthetic examples are labelled:
- `source_type: "synthetic"`
- `provenance: "Synthetic example created as a project fixture for Australian For AIs Phase 1"`
- `license: "CC0-1.0"` (or Apache-2.0 as specified in the record)

---

## Future Data Requirements

For any example added in Phase 2 or later:

### Provenance

Every record must include a `provenance` field that describes:
- Where the utterance originated
- Whether it was collected with consent
- Any transformations applied (e.g., paraphrasing for anonymisation)
- The date of collection

### Consent

Real utterances from identifiable speakers require documented consent from the speaker.

Do not include:
- Private conversations without explicit consent
- Social media content scraped without the platform's API or the user's consent
- Communications where the speaker had a reasonable expectation of privacy

### Licensing

Every record must specify a licence. Options include:
- `CC0-1.0` — Public domain dedication
- `CC-BY-4.0` — Attribution required
- `Apache-2.0` — Project default for synthetic content
- Documented fair use with justification

Copyrighted material must not be included without permission.

### Anonymisation

If a real utterance includes personally identifying information (names, locations, dates),
it must be paraphrased or anonymised before inclusion. The `provenance` field must note
that anonymisation was applied.

---

## Prohibited Data Sources

- Scraped social media without consent
- Private or direct messages without explicit consent
- Copyrighted corpora without licensing
- Fabricated citations or invented sources
- Data representing identifiable individuals who have not consented

---

## Data Integrity

- Example IDs (`id`) must be stable. Once assigned, an ID must not be changed.
- Records must validate against the current schema.
- Any modification to an existing example must be documented in `annotation_notes`.

---

## Dataset Metadata

When the dataset reaches a citable release, it must include:
- A dataset card describing content, scope, limitations, and known biases
- Licence for the full dataset
- Contact information for provenance questions
- DOI or persistent identifier (deferred to Phase 8)
