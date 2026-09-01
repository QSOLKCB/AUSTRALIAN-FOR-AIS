"""
Validation module for Australian For AIs.

Validates benchmark example records and evaluation prediction records against
their respective JSON Schemas.

This module is intentionally dependency-light. It uses jsonschema for schema
validation and the Python standard library for everything else.
"""

from __future__ import annotations

import json
import pathlib
from typing import Iterator

import jsonschema

_PACKAGE_DIR = pathlib.Path(__file__).parent
_REPO_ROOT = _PACKAGE_DIR.parent.parent
_SCHEMAS_DIR = _REPO_ROOT / "schemas"

_EXAMPLE_SCHEMA_PATH = _SCHEMAS_DIR / "example.schema.json"
_EVALUATION_SCHEMA_PATH = _SCHEMAS_DIR / "evaluation.schema.json"


def _load_schema(path: pathlib.Path) -> dict:
    """Load and return a JSON Schema from a file."""
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _get_example_schema() -> dict:
    return _load_schema(_EXAMPLE_SCHEMA_PATH)


def _get_evaluation_schema() -> dict:
    return _load_schema(_EVALUATION_SCHEMA_PATH)


class ValidationError(Exception):
    """Raised when a record fails schema or semantic validation."""


def validate_example_record(record: dict) -> None:
    """
    Validate a single benchmark example record.

    Raises ValidationError if the record is invalid. This includes both
    JSON Schema violations and project-specific semantic rules.
    """
    schema = _get_example_schema()
    try:
        jsonschema.validate(record, schema)
    except jsonschema.ValidationError as exc:
        raise ValidationError(f"Schema validation failed: {exc.message}") from exc

    _semantic_validate_example(record)


def _semantic_validate_example(record: dict) -> None:
    """Project-specific semantic rules beyond JSON Schema."""

    # id must be non-empty (also enforced by schema but be explicit)
    if not record.get("id", "").strip():
        raise ValidationError("'id' must be a non-empty string.")

    # confidence must be in [0.0, 1.0]
    confidence = record.get("confidence")
    if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
        raise ValidationError(
            f"'confidence' must be a number between 0.0 and 1.0, got {confidence!r}."
        )

    # pragmatic_interpretations must have at least one entry
    interps = record.get("pragmatic_interpretations", [])
    if not isinstance(interps, list) or len(interps) < 1:
        raise ValidationError(
            "'pragmatic_interpretations' must contain at least one entry."
        )

    # if ambiguity is True, there should be at least two interpretations OR
    # primary is "insufficient_context"
    if record.get("ambiguity") is True:
        primary = record.get("primary_pragmatic_interpretation", "")
        if primary != "insufficient_context" and len(interps) < 2:
            raise ValidationError(
                "If 'ambiguity' is true and primary is not 'insufficient_context', "
                "'pragmatic_interpretations' must contain at least two entries."
            )

    # hostility must be bool or "uncertain"
    hostility = record.get("hostility")
    if not isinstance(hostility, bool) and hostility != "uncertain":
        raise ValidationError(
            f"'hostility' must be true, false, or 'uncertain', got {hostility!r}."
        )


def validate_evaluation_record(record: dict) -> None:
    """
    Validate a single evaluation prediction record.

    Raises ValidationError if the record is invalid.
    """
    schema = _get_evaluation_schema()
    try:
        jsonschema.validate(record, schema)
    except jsonschema.ValidationError as exc:
        raise ValidationError(f"Schema validation failed: {exc.message}") from exc

    # model_confidence in [0.0, 1.0]
    mc = record.get("model_confidence")
    if not isinstance(mc, (int, float)) or not (0.0 <= mc <= 1.0):
        raise ValidationError(
            f"'model_confidence' must be a number between 0.0 and 1.0, got {mc!r}."
        )

    # predicted_hostility must be bool or "uncertain"
    ph = record.get("predicted_hostility")
    if not isinstance(ph, bool) and ph != "uncertain":
        raise ValidationError(
            f"'predicted_hostility' must be true, false, or 'uncertain', got {ph!r}."
        )


def iter_jsonl(path: pathlib.Path) -> Iterator[tuple[int, dict]]:
    """
    Iterate over a JSONL file, yielding (line_number, record) tuples.

    Skips blank lines. Raises ValidationError on malformed JSON.
    """
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield lineno, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    f"Line {lineno}: malformed JSON — {exc}"
                ) from exc


def validate_jsonl_file(
    path: pathlib.Path,
    record_validator=None,
) -> list[str]:
    """
    Validate all records in a JSONL file.

    Returns a list of error strings. An empty list means all records are valid.

    record_validator defaults to validate_example_record.
    """
    if record_validator is None:
        record_validator = validate_example_record

    errors: list[str] = []
    try:
        for lineno, record in iter_jsonl(path):
            try:
                record_validator(record)
            except ValidationError as exc:
                errors.append(f"Line {lineno} (id={record.get('id', '?')}): {exc}")
    except ValidationError as exc:
        errors.append(str(exc))

    return errors
