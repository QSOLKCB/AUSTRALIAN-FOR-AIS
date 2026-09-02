#!/usr/bin/env python3
"""Print deterministic Phase 2 annotation coverage and agreement as JSON."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

# Allow running from a source checkout without installing the package.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from australian_for_ais.annotation import (
    build_agreement_report,
    load_annotations,
    load_pilot_items,
)
from australian_for_ais.validation import ValidationError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("items", type=pathlib.Path, help="Phase 2 pilot items JSONL")
    parser.add_argument("annotations", type=pathlib.Path, help="Human annotations JSONL")
    parser.add_argument(
        "--require-two",
        action="store_true",
        help="Return non-zero unless every pilot item has at least two annotations.",
    )
    args = parser.parse_args()

    try:
        items = load_pilot_items(args.items)
        annotations = load_annotations(args.annotations, set(items))
    except ValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    report = build_agreement_report(items, annotations)
    print(json.dumps(report, indent=2, sort_keys=True))

    if args.require_two and report["coverage"]["items_below_two_annotations"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
