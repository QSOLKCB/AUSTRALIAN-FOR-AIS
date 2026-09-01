"""
Command-line interface for Australian For AIs.

Usage:
    python -m australian_for_ais.cli validate <examples.jsonl>
    python -m australian_for_ais.cli evaluate <examples.jsonl> <predictions.jsonl>

All operations are offline-capable. No network access is required or performed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .scoring import load_examples, load_predictions, score
from .validation import ValidationError, validate_jsonl_file, validate_evaluation_record


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a JSONL dataset file against the example schema."""
    path = pathlib.Path(args.file)

    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    print(f"Validating {path} …")
    errors = validate_jsonl_file(path)

    if errors:
        print(f"\n{len(errors)} validation error(s) found:\n", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    # Count valid records
    with path.open(encoding="utf-8") as fh:
        count = sum(1 for line in fh if line.strip())
    print(f"OK — {count} record(s) valid.")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Evaluate predictions against benchmark examples."""
    examples_path = pathlib.Path(args.examples)
    predictions_path = pathlib.Path(args.predictions)

    if not examples_path.exists():
        print(f"Error: examples file not found: {examples_path}", file=sys.stderr)
        return 2

    if not predictions_path.exists():
        print(f"Error: predictions file not found: {predictions_path}", file=sys.stderr)
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
    scores = result.as_dict()

    print(json.dumps(scores, indent=2))

    if result.errors:
        print(f"\nWarnings ({len(result.errors)}):", file=sys.stderr)
        for err in result.errors:
            print(f"  {err}", file=sys.stderr)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="australian_for_ais",
        description=(
            "Australian For AIs — Cultural-Pragmatics Benchmark Tools\n\n"
            "All operations are offline-capable."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate
    val_parser = subparsers.add_parser(
        "validate",
        help="Validate a JSONL dataset file against the example schema.",
    )
    val_parser.add_argument("file", help="Path to the JSONL file to validate.")

    # evaluate
    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate model predictions against benchmark examples.",
    )
    eval_parser.add_argument("examples", help="Path to the benchmark examples JSONL file.")
    eval_parser.add_argument("predictions", help="Path to the predictions JSONL file.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "evaluate":
        return cmd_evaluate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
