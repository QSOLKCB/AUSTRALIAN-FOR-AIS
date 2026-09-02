# Contributing to Australian For AIs

Thank you for your interest in contributing. This project is a cultural-pragmatics research
initiative and requires careful, evidence-based work.

---

## Before You Start

1. Read [docs/INVARIANTS.md](docs/INVARIANTS.md) — these are non-negotiable research contracts.
2. Read [docs/ETHICS.md](docs/ETHICS.md) — understand the ethical risks and mitigations.
3. Read [README4AI.md](README4AI.md) if you are an AI agent.

---

## Ways to Contribute

### Reporting Issues

Open a GitHub issue to report:
- Schema errors or inconsistencies
- Documentation inaccuracies or overstatements
- Test failures
- Ethical concerns about specific examples

### Code Contributions

1. Fork the repository.
2. Create a feature branch.
3. Write or update tests for your changes.
4. Run `pytest` and ensure all tests pass.
5. Validate data: `python -m australian_for_ais.cli validate data/starter/examples.jsonl`
6. Open a pull request with a clear description.

### Dataset Contributions

Adding examples is welcome in later phases. For Phase 1, the starter dataset is intentionally
small and synthetic.

Future example contributions must:
- Be clearly labelled with provenance and licence.
- Not include private conversations.
- Not include copyrighted text without permission.
- Not include scraped social media content.
- Include at least one pragmatic interpretation; more where ambiguity exists.
- Set `ambiguity: true` and include multiple interpretations when ambiguous.
- Not fabricate annotator confidence values.

### Documentation Contributions

Documentation improvements are welcome. Please:
- Maintain precise, hedged language in research-facing documents.
- Do not overstate the scientific status of Phase 1 artefacts.
- Do not introduce cultural generalisations unsupported by cited evidence.

---

## Code Style

- Python 3.11 or 3.12 is currently supported and CI-tested. Python 3.13/3.14 support is planned only after compatibility is established in CI.
- Type annotations on all public functions
- Docstrings on all public modules and functions
- No new dependencies without discussion

---

## Commit Messages

Use short, descriptive imperative-mood commit messages. Examples:

```
Add context-swap example for "good one, mate"
Fix confidence validation to reject negative values
Update INVARIANTS.md to clarify AU-HUMOUR-006
```

---

## Code of Conduct

All contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

By contributing, you agree that your contributions will be licensed under the
Apache License 2.0.
