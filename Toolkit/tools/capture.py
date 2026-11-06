"""Capture Qwen3 residual activations for matched Australian-language prompts.

Run only with a local checkpoint and locally installed optional dependencies.
Input JSONL: {pair_id, split:'train', positive_prompt, negative_prompt}.
"""

import argparse
import json
from pathlib import Path

from Toolkit.modules.receipts import canonical_json, load_jsonl, sha256_file, write_new


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--max-tokens", type=int, default=128)
    args = parser.parse_args(argv)
    try:
        rows = load_jsonl(args.input, max_bytes=2 * 1024 * 1024, max_records=100)
        ids = set()
        for row in rows:
            if not isinstance(row, dict) or row.get("split") != "train":
                raise ValueError("capture accepts explicit train records only")
            identifier = row.get("pair_id")
            if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
                raise ValueError("pair IDs must be distinct nonempty strings")
            ids.add(identifier)
            for key in ("positive_prompt", "negative_prompt"):
                if not isinstance(row.get(key), str) or not row[key].strip():
                    raise ValueError(f"{identifier}: missing {key}")
        # Import after validating the full input; heavyweight dependencies are optional.
        from Toolkit.modules.qwen_capture import LocalQwenCapture
        engine = LocalQwenCapture(args.model_dir, args.device, args.max_tokens)
        stamp = engine.checkpoint["checkpoint_manifest_sha256"]
        captured = []
        for row in rows:
            captured.append({"pair_id": row["pair_id"], "split": "train",
                             "checkpoint_manifest_sha256": stamp,
                             "positive": engine.capture(row["positive_prompt"]),
                             "negative": engine.capture(row["negative_prompt"])})
        content = b"".join(canonical_json(row) for row in captured)
        write_new(args.output, content)
        receipt = {"schema": "au-capture-receipt/1",
                   "source_sha256": sha256_file(args.input),
                   "output_sha256": sha256_file(args.output),
                   "capture_method": "qwen3-final-prompt-token-residual-v1",
                   "checkpoint": engine.checkpoint, "device": args.device,
                   "max_tokens": args.max_tokens, "pairs": len(captured)}
        write_new(str(args.output) + ".receipt.json", canonical_json(receipt))
    except (ValueError, OSError, RuntimeError, ImportError, TypeError) as exc:
        parser.exit(1, f"capture: {exc}\n")
    print(f"captured {len(captured)} pairs; checkpoint manifest {stamp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
