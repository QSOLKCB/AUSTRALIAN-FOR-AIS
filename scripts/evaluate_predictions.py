#!/usr/bin/env python3
"""
Evaluate model predictions against Australian For AIs benchmark examples.

Usage:
    python scripts/evaluate_predictions.py examples.jsonl predictions.jsonl

Prints component scores as JSON.

Exits with status 0 on success, 1 on validation/evaluation errors, 2 on usage errors.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from australian_for_ais.scoring import load_examples, load_predictions, score
from australian_for_ais.validation import ValidationError


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <examples.jsonl> <predictions.jsonl>",
            file=sys.stderr,
        )
        return 2

    examples_path = pathlib.Path(sys.argv[1])
    predictions_path = pathlib.Path(sys.argv[2])

    for path in (examples_path, predictions_path):
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            return 2

    try:
        examples = load_examples(examples_path)
    except ValidationError as exc:
        print(f"Error loading examples: {exc}", file=sys.stderr)
        return 1

    try:
        predictions = load_predictions(predictions_path)
    except ValidationError as exc:
        print(f"Error loading predictions: {exc}", file=sys.stderr)
        return 1

    result = score(examples, predictions)
    print(json.dumps(result.as_dict(), indent=2))

    if result.errors:
        print(f"\nEvaluation error(s) ({len(result.errors)}):", file=sys.stderr)
        for err in result.errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
