#!/usr/bin/env python3
"""
Validate a dataset JSONL file against the Australian For AIs example schema.

Usage:
    python scripts/validate_dataset.py data/starter/examples.jsonl

Exits with status 0 if all records are valid, 1 if any are invalid, 2 if a
usage error occurs.
"""

from __future__ import annotations

import pathlib
import sys

# Allow running from repo root without installing the package
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from australian_for_ais.validation import validate_jsonl_file


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <examples.jsonl>", file=sys.stderr)
        return 2

    path = pathlib.Path(sys.argv[1])
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    print(f"Validating {path} …")
    errors = validate_jsonl_file(path)

    if errors:
        print(f"\n{len(errors)} error(s):\n", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    with path.open(encoding="utf-8") as fh:
        count = sum(1 for line in fh if line.strip())
    print(f"OK — {count} record(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
