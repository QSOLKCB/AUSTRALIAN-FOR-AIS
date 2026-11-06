# AU-STEER-001 — Toolkit development plan

All new experimental software, fixtures and documents stay under Toolkit/.
Existing AU-HUMOUR-001 through AU-HUMOUR-010 remain normative; this plan
does not promote hypotheses to validated findings.

## Phase 0 — implemented in this draft PR

- Strict, deterministic matched-pair mean-difference estimator.
- Pure functional steering-vector addition primitive (no runtime hook).
- Local-only Qwen3 residual-stream capture with lazy optional ML imports.
- Checkpoint/input/output SHA-256 receipt recording and refusal to overwrite.
- Standard-library offline unit tests, without model downloads.

**Evidence limit:** no Qwen weights were run by this PR and no cultural effect
was measured. Adapter functionality requires local-model integration testing.

## Phase 1 — Qwen steering and independent controls (future)

- Exact pinned model/tokenizer revisions; exclude development/evaluation leakage.
- Compare checkpoint manifest at every step, not only a user-supplied digest.
- Frozen prompt templates and paired train/dev/test splits.
- Register one specific activation site before tuning strength.
- Implement a scoped forward hook, restore it even on exceptions, and test
  zero-strength parity; enforce the same layer/shape/dtype.
- Measure meaningful pragmatic accuracy, refusal/hostility controls, uncertainty,
  ordinary-language regression, output slang density, memory and latency.
- Run random-direction, sign-flipped and lexical-shortcut controls.
- Publish exact-head execution receipts and local A/B comparisons.

## Phase 2 — compact interpretable feature models (future)

- Obtain licensed model-intermediate targets for both input layers and future
  MLP outputs; identify the exact Qwen checkpoint and hook interfaces.
- First implement a small sparse one-layer autoencoder **as a baseline**, not
  call it a cross-layer transcoder.
- Implement a genuine multi-target cross-layer decoder with strictly causal
  layer ordering and explicit objective: reconstruction + sparsity penalty.
- Validate held-out explained variance, reconstruction error, feature stability,
  feature sparsity, cross-seed agreement and intervention fidelity.
- Compare compact learned features with published checkpoint-matched CLT features.
- Avoid claims that labelled neurons or features encode 'national identity'.

## Phase 3 — audio ASR research (future)

- Separate adapter for a locally provided ASR model and audio-encoder layers.
- Australian audio corpus with explicit rights, consent and region/register scope.
- Evaluate WER/CER and meaning-preservation independently, alongside demographic
  and acoustic confound checks. Hold out speakers, not just recordings.
- Import AudioPod-produced synthetic speech only into a labelled synthetic split.
- Keep Piper voice synthesis, ASR and pragmatic text-model analysis separate.

## Governance

- All downloads require explicit provisioning. CI and tests remain offline.
- No automatic speech-to-text claim about AudioPod.
- No human annotations, consent, performance results or feature semantics invented.
- Human validation remains necessary to interpret context and uncertainty.
- No merge without independent review and green checks.
