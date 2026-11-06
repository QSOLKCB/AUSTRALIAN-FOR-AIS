"""Capture Qwen3 residual activations for matched Australian-language prompts.

Run only with a local checkpoint and locally installed optional dependencies.
Input JSONL: {pair_id, split:'train', positive_prompt, negative_prompt}.
"""

import argparse
import os
from pathlib import Path
import tempfile

from Toolkit.modules.receipts import (MAX_CAPTURE_BYTES, MAX_CAPTURE_LINE_BYTES,
                                      MAX_CAPTURE_RECORDS, canonical_json, load_jsonl,
                                      sha256_file, write_new)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--max-tokens", type=int, default=128)
    args = parser.parse_args(argv)
    try:
        rows = load_jsonl(args.input, max_bytes=2 * 1024 * 1024,
                          max_records=MAX_CAPTURE_RECORDS)
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
        output_path = args.output
        receipt_path = Path(str(output_path) + ".receipt.json")
        if output_path.resolve() == args.input.resolve() or receipt_path.resolve() == args.input.resolve():
            raise ValueError("output paths must not overwrite input")
        # Refuse a stale receipt before loading the model or performing inference.
        # lexists also rejects dangling symlinks.
        if os.path.lexists(output_path) or os.path.lexists(receipt_path):
            raise FileExistsError("activation output or receipt already exists")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Import only after validating input and destination paths.
        from Toolkit.modules.qwen_capture import LocalQwenCapture
        engine = LocalQwenCapture(args.model_dir, args.device, args.max_tokens)
        stamp = engine.checkpoint["checkpoint_manifest_sha256"]
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=output_path.parent, prefix=".au-capture-",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                size = 0
                for row in rows:
                    captured = {"pair_id": row["pair_id"], "split": "train",
                                "checkpoint_manifest_sha256": stamp,
                                "positive": engine.capture(row["positive_prompt"]),
                                "negative": engine.capture(row["negative_prompt"])}
                    encoded = canonical_json(captured)
                    if len(encoded) > MAX_CAPTURE_LINE_BYTES:
                        raise ValueError("activation record exceeds the line byte limit")
                    size += len(encoded)
                    if size > MAX_CAPTURE_BYTES:
                        raise ValueError("activation output exceeds the byte limit")
                    stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())

            receipt = {"schema": "au-capture-receipt/1",
                       "source_sha256": sha256_file(args.input),
                       "output_sha256": sha256_file(temporary),
                       "capture_method": "qwen3-final-prompt-token-decoder-pre-norm-v2",
                       "checkpoint": engine.checkpoint, "device": args.device,
                       "max_tokens": args.max_tokens, "pairs": len(rows)}
            # os.link publishes only to a new path, never replaces a competing file.
            # If receipt publication fails, remove ONLY the output inode we linked.
            if os.path.lexists(receipt_path):
                raise FileExistsError("receipt appeared during capture")
            os.link(temporary, output_path)
            try:
                write_new(receipt_path, canonical_json(receipt))
            except BaseException:
                if (output_path.exists() and
                        output_path.stat().st_ino == temporary.stat().st_ino and
                        output_path.stat().st_dev == temporary.stat().st_dev):
                    output_path.unlink()
                raise
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    except (ValueError, OSError, RuntimeError, ImportError, TypeError) as exc:
        parser.exit(1, f"capture: {exc}\n")
    print(f"captured {len(rows)} pairs; checkpoint manifest {stamp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
