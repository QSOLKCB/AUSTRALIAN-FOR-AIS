# Phase 2 Pilot Data

`items.jsonl` contains 60 independently authored synthetic items prepared for the Phase 2 human-annotation pilot.

Important status boundary:

- these are **pilot prompts**, not benchmark gold labels;
- no human annotations are committed here yet;
- the 60 items form 30 context-contrast pairs, but pair metadata should not be shown during an annotation decision;
- all items are synthetic and Apache-2.0 licensed;
- the pack is not claimed to represent Australian English or Australian culture broadly.

Validate the pack with:

```bash
python -m australian_for_ais.cli validate-pilot data/pilot/items.jsonl
```

Use `annotation/index.html` for offline annotation and see `docs/PHASE2-PILOT-PROTOCOL.md` for the human-study procedure.

Human annotation files should not be committed until their consent, privacy, storage, and release status has been reviewed. A local annotation export is not automatically redistributable research data.
