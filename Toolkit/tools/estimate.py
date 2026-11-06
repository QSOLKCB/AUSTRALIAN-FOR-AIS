"""Estimate matched-contrast directions from previously captured activations."""

import argparse
import hashlib
from pathlib import Path

from Toolkit.modules.contrast import estimate
from Toolkit.modules.receipts import (MAX_CAPTURE_BYTES, MAX_CAPTURE_LINE_BYTES,
                                      MAX_CAPTURE_RECORDS, canonical_json, iter_jsonl,
                                      sha256_file, write_new)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checkpoint-manifest", required=True,
                        help="SHA-256 checkpoint manifest recorded by capture.py")
    args = parser.parse_args(argv)
    if len(args.checkpoint_manifest) != 64 or any(c not in "0123456789abcdef" for c in args.checkpoint_manifest):
        parser.error("checkpoint-manifest must be a lowercase SHA-256 hex digest")
    try:
        def checked_pairs():
            for pair in iter_jsonl(args.input, max_bytes=MAX_CAPTURE_BYTES,
                                   max_records=MAX_CAPTURE_RECORDS,
                                   max_line_bytes=MAX_CAPTURE_LINE_BYTES):
                if not isinstance(pair, dict) or pair.get("checkpoint_manifest_sha256") != args.checkpoint_manifest:
                    raise ValueError("pair checkpoint fingerprints do not match the supplied manifest")
                yield pair

        directions = estimate(checked_pairs())
        result = {"schema": "au-steer-vector/1",
                  "checkpoint_manifest_sha256": args.checkpoint_manifest,
                  "input_sha256": sha256_file(args.input),
                  **directions}
        result["receipt_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
        write_new(args.output, canonical_json(result))
    except (ValueError, OSError, OverflowError) as exc:
        parser.exit(1, f"estimate: {exc}\n")
    print(f"wrote {args.output} ({result['pair_count']} training pairs, {len(result['layers'])} layers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
