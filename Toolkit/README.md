# Toolkit — AUSTRALIAN-FOR-AIS

This directory owns **all new interpretability experiments**. It does not replace the
existing benchmark, annotation protocols, schemas, or research invariants.

**Status:** AU-STEER-001 Phase 0 prototype. The statistical contrast estimator,
vector-addition primitive, offline checkpoint capture adapter and receipt utilities
are implemented. Genuine Australian steering, an independently validated CLT,
audio-ASR adaptation, and any accuracy improvements are **not** established.

## Layout

- modules/contrast.py — matched, layer-wise activation contrasts and pure vector addition
- modules/receipts.py — strict JSONL ingestion, canonical receipts, SHA-256, no-overwrite writes
- modules/qwen_capture.py — optional local Qwen3 hidden-state extraction
- tools/capture.py — optional Qwen3 paired-prompt capture CLI
- tools/estimate.py — standalone activation-direction estimation CLI
- tests/ — deterministic offline standard-library tests
- docs/PLAN.md — sequenced work and scientific boundaries
- docs/AUDIOPOD.md — independent AudioPod and ASR integration plan

No root package metadata, benchmark schema, or existing fixture has been changed.

## Zero-dependency smoke test

Run from the repository root:

~~~sh
python -m unittest discover -s Toolkit/tests -v
~~~

## Phase 0: direction estimation

Input JSONL rows have these keys:

~~~json
{"pair_id":"synthetic-001","split":"train","checkpoint_manifest_sha256":"<64 hex digest from local capture>","positive":{"0":[2.0,3.0]},"negative":{"0":[1.0,3.0]}}
~~~

Numbers above are synthetic test examples, **not** cultural annotations or
evidence of a real model feature. Output consists of normalized layer-wise
paired mean-difference directions and magnitude measurements.

~~~sh
python -m Toolkit.tools.estimate --input ./pairs.jsonl --output ./direction.json --checkpoint-manifest YOUR_LOCAL_MANIFEST_SHA256
~~~

Estimation accepts training records only. All rows must have the same checkpoint
manifest, compatible widths, and distinct pair IDs. No model inference occurs here.

## Optional local model activation capture

Requires a **separately provisioned**, trusted local Qwen3 safetensors checkpoint
and locally installed compatible versions of PyTorch and Transformers.
Do not install these large dependencies into the benchmark or AudioPod package.
Use a separate uv environment, pinned dependencies, and offline execution
after intentional first-time provisioning.

~~~sh
python -m Toolkit.tools.capture --model-dir /models/Qwen3-0.6B \
  --input ./prompts-train.jsonl --output ./activations.jsonl --device cuda

python -m Toolkit.tools.estimate --input ./activations.jsonl \
  --output ./direction.json --checkpoint-manifest THE_REPORTED_MANIFEST_HASH
~~~

Capture input JSONL rows are:
~~~json
{"pair_id":"example-1","split":"train","positive_prompt":"An authored Australian example","negative_prompt":"A matched control example"}
~~~

The v2 capture site is the **last prompt token**, taken directly from each
Qwen3 decoder layer output **before** the final model RMS normalization
(embedding excluded), not an MLP output or an audio encoder. This avoids
mixing normalized final hidden states with unnormalized intermediate layers.
The capture producer and estimation consumer share a 1 GiB file bound,
32 MiB per-record bound and a 100-pair limit. Capture streams to a temporary
file and will not publish activations if the destination or receipt already
exists; it attempts to roll back an output if receipt publication fails.
A capture receipt includes exact hashes of local checkpoint files, input and output.
No dataset is automatically downloaded. No model weights are changed.

**Never** learn a direction using the held-out test split, the Phase 2 human
annotation records, or reference-only copyrighted source material. The current
CLI deliberately accepts training split only; dataset partitioning and reviewer
controls are the researcher's responsibility.

## Interpretation boundaries

A large activation contrast can indicate prompt-format, tokenisation, register
or vocabulary differences—not cultural understanding. Meaning-preserving matched
pairs, blinded held-out evaluation, random-direction controls, norm-matched
strength sweeps, general English controls, and causal patching are required
before claiming a transferable effect. A human-authored Scottish/accent result
is not an automatic Australian language feature.

A CLT is **not included yet**. Cross-layer transcoder reconstruction and
trained sparse features demand additional target-activation collection,
out-of-sample reconstruction tests, sparsity metrics and causal validation.
See docs/PLAN.md.

## Correctness hardening for AU-STEER-001

Qwen3's final `hidden_states` entry can be post-RMS-normalization, so the capture
adapter now attaches scoped hooks to every decoder layer output and removes
them in a finally block. The capture receipt uses method
`qwen3-final-prompt-token-decoder-pre-norm-v2` to distinguish this from the
original mixed-site prototype. Activation files should not be compared across
these method versions.

The capture producer and streaming estimator share a bounded 1 GiB output
contract, 32 MiB per JSONL record, and 100 records. The producer buffers only
one captured JSONL record at a time, while the estimator retains paired
differences in memory for deterministic ordering. Validate the checksum in
`out.jsonl.receipt.json` before using any artifact that may have been left
by process termination. Receipt publication failures trigger output rollback;
there is no general two-file atomic transaction across abrupt power loss.
