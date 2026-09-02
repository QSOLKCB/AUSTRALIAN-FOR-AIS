"""
Command-line interface for Australian For AIs.

Usage:
    python -m australian_for_ais.cli validate <examples.jsonl>
    python -m australian_for_ais.cli evaluate <examples.jsonl> <predictions.jsonl>
    python -m australian_for_ais.cli validate-pilot <items.jsonl>
    python -m australian_for_ais.cli validate-annotations <items.jsonl> <annotations.jsonl>
    python -m australian_for_ais.cli agreement <items.jsonl> <annotations.jsonl>

All operations are offline-capable. No network access is required or performed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .annotation import build_agreement_report, load_annotations, load_pilot_items
from .scoring import load_examples, load_predictions, score
from .validation import ValidationError, validate_jsonl_file, validate_pilot_item_record


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a JSONL dataset file against the example schema and dataset invariants."""
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

    with path.open(encoding="utf-8") as fh:
        count = sum(1 for line in fh if line.strip())
    print(f"OK — {count} record(s) valid.")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Evaluate a complete prediction file against benchmark examples."""
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
    print(json.dumps(result.as_dict(), indent=2))

    if result.errors:
        print(f"\nEvaluation error(s) ({len(result.errors)}):", file=sys.stderr)
        for err in result.errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    return 0


def cmd_validate_pilot(args: argparse.Namespace) -> int:
    """Validate an unannotated Phase 2 pilot item file."""
    path = pathlib.Path(args.file)
    try:
        items = load_pilot_items(path)
    except ValidationError as exc:
        print(f"Pilot validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"OK — {len(items)} pilot item(s) valid.")
    return 0


def _load_phase2_inputs(args: argparse.Namespace):
    items_path = pathlib.Path(args.items)
    annotations_path = pathlib.Path(args.annotations)
    items = load_pilot_items(items_path)
    annotations = load_annotations(annotations_path, set(items))
    return items, annotations


def cmd_validate_annotations(args: argparse.Namespace) -> int:
    """Validate Phase 2 annotations against known pilot item IDs."""
    try:
        items, annotations = _load_phase2_inputs(args)
    except ValidationError as exc:
        print(f"Annotation validation failed: {exc}", file=sys.stderr)
        return 1

    report = build_agreement_report(items, annotations)
    under_two = report["coverage"]["items_below_two_annotations"]
    print(
        f"OK — {len(annotations)} annotation(s) valid for {len(items)} pilot item(s)."
    )
    if under_two:
        print(
            f"Pilot not yet graduation-ready: {len(under_two)} item(s) have fewer than "
            "two independent annotations."
        )
        if args.require_two:
            return 1
    return 0


def cmd_agreement(args: argparse.Namespace) -> int:
    """Print a deterministic Phase 2 agreement/coverage report as JSON."""
    try:
        items, annotations = _load_phase2_inputs(args)
    except ValidationError as exc:
        print(f"Agreement analysis failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(build_agreement_report(items, annotations), indent=2, sort_keys=True))
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

    val_parser = subparsers.add_parser(
        "validate",
        help="Validate a JSONL dataset file against the example schema.",
    )
    val_parser.add_argument("file", help="Path to the JSONL file to validate.")

    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate model predictions against benchmark examples.",
    )
    eval_parser.add_argument("examples", help="Path to the benchmark examples JSONL file.")
    eval_parser.add_argument("predictions", help="Path to the predictions JSONL file.")

    pilot_parser = subparsers.add_parser(
        "validate-pilot",
        help="Validate Phase 2 unannotated pilot items.",
    )
    pilot_parser.add_argument("file", help="Path to the pilot items JSONL file.")

    annotations_parser = subparsers.add_parser(
        "validate-annotations",
        help="Validate Phase 2 human annotations against pilot items.",
    )
    annotations_parser.add_argument("items", help="Path to pilot items JSONL.")
    annotations_parser.add_argument("annotations", help="Path to annotations JSONL.")
    annotations_parser.add_argument(
        "--require-two",
        action="store_true",
        help="Return non-zero unless every item has at least two annotations.",
    )

    agreement_parser = subparsers.add_parser(
        "agreement",
        help="Report Phase 2 annotation coverage and agreement metrics.",
    )
    agreement_parser.add_argument("items", help="Path to pilot items JSONL.")
    agreement_parser.add_argument("annotations", help="Path to annotations JSONL.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "evaluate":
        return cmd_evaluate(args)
    if args.command == "validate-pilot":
        return cmd_validate_pilot(args)
    if args.command == "validate-annotations":
        return cmd_validate_annotations(args)
    if args.command == "agreement":
        return cmd_agreement(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
