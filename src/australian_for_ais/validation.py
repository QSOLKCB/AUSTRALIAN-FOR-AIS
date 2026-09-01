"""
Validation module for Australian For AIs.

Validates benchmark example records and evaluation prediction records against
packaged JSON Schemas, then applies project-level semantic invariants.
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Iterator, Mapping
from importlib import resources
from typing import Any, Callable

import jsonschema

_SCHEMA_PACKAGE_ROOT = resources.files("australian_for_ais").joinpath("schemas")
_EXAMPLE_SCHEMA_RESOURCE = _SCHEMA_PACKAGE_ROOT.joinpath("example.schema.json")
_EVALUATION_SCHEMA_RESOURCE = _SCHEMA_PACKAGE_ROOT.joinpath("evaluation.schema.json")


class ValidationError(Exception):
    """Raised when a record fails schema or semantic validation."""


def _load_schema(resource) -> dict:
    """Load and return a packaged JSON Schema resource."""
    return json.loads(resource.read_text(encoding="utf-8"))


def _get_example_schema() -> dict:
    return _load_schema(_EXAMPLE_SCHEMA_RESOURCE)


def _get_evaluation_schema() -> dict:
    return _load_schema(_EVALUATION_SCHEMA_RESOURCE)


def _normalise_text(value: str) -> str:
    return value.strip().casefold()


def validate_example_record(record: Any) -> None:
    """Validate a single benchmark example record."""
    if not isinstance(record, Mapping):
        raise ValidationError("Example record must be a JSON object.")

    try:
        jsonschema.validate(record, _get_example_schema())
    except jsonschema.ValidationError as exc:
        raise ValidationError(f"Schema validation failed: {exc.message}") from exc

    _semantic_validate_example(record)


def _semantic_validate_example(record: Mapping[str, Any]) -> None:
    if not str(record.get("id", "")).strip():
        raise ValidationError("'id' must be a non-empty string.")

    confidence = record.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not (0.0 <= confidence <= 1.0):
        raise ValidationError(
            f"'confidence' must be a number between 0.0 and 1.0, got {confidence!r}."
        )

    interps = record.get("pragmatic_interpretations", [])
    if not isinstance(interps, list) or len(interps) < 1:
        raise ValidationError("'pragmatic_interpretations' must contain at least one entry.")

    primary = record.get("primary_pragmatic_interpretation", "")
    if primary != "insufficient_context":
        accepted = {_normalise_text(v) for v in interps if isinstance(v, str)}
        if _normalise_text(primary) not in accepted:
            raise ValidationError(
                "'primary_pragmatic_interpretation' must be present in "
                "'pragmatic_interpretations', unless it is 'insufficient_context'."
            )

    if record.get("ambiguity") is True:
        if primary != "insufficient_context" and len(interps) < 2:
            raise ValidationError(
                "If 'ambiguity' is true and primary is not 'insufficient_context', "
                "'pragmatic_interpretations' must contain at least two entries."
            )

    if primary == "insufficient_context":
        if record.get("ambiguity") is not True:
            raise ValidationError(
                "'insufficient_context' requires 'ambiguity' to be true."
            )
        if confidence > 0.4:
            raise ValidationError(
                "'insufficient_context' requires confidence at or below 0.4."
            )

    hostility = record.get("hostility")
    if not isinstance(hostility, bool) and hostility != "uncertain":
        raise ValidationError(
            f"'hostility' must be true, false, or 'uncertain', got {hostility!r}."
        )

    for field_name in ("provenance", "license"):
        value = record.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"'{field_name}' must contain non-whitespace text.")


def validate_evaluation_record(record: Any) -> None:
    """Validate a single complete evaluation prediction record."""
    if not isinstance(record, Mapping):
        raise ValidationError("Evaluation record must be a JSON object.")

    try:
        jsonschema.validate(record, _get_evaluation_schema())
    except jsonschema.ValidationError as exc:
        raise ValidationError(f"Schema validation failed: {exc.message}") from exc

    mc = record.get("model_confidence")
    if not isinstance(mc, (int, float)) or isinstance(mc, bool) or not (0.0 <= mc <= 1.0):
        raise ValidationError(
            f"'model_confidence' must be a number between 0.0 and 1.0, got {mc!r}."
        )

    ph = record.get("predicted_hostility")
    if not isinstance(ph, bool) and ph != "uncertain":
        raise ValidationError(
            f"'predicted_hostility' must be true, false, or 'uncertain', got {ph!r}."
        )


def iter_jsonl(path: pathlib.Path) -> Iterator[tuple[int, Any]]:
    """Iterate over a JSONL file, yielding ``(line_number, parsed_value)`` tuples."""
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield lineno, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"Line {lineno}: malformed JSON — {exc}") from exc


def validate_jsonl_file(
    path: pathlib.Path,
    record_validator: Callable[[Any], None] | None = None,
) -> list[str]:
    """
    Validate all records in a JSONL file, including dataset-level uniqueness.

    Duplicate ``id`` or ``example_id`` values are rejected so the validation gate
    cannot approve a file that the corresponding loader later refuses to use.
    """
    if record_validator is None:
        record_validator = validate_example_record

    errors: list[str] = []
    seen: dict[tuple[str, str], int] = {}

    try:
        for lineno, record in iter_jsonl(path):
            display_id = "?"
            if isinstance(record, Mapping):
                if isinstance(record.get("id"), str):
                    display_id = record["id"]
                elif isinstance(record.get("example_id"), str):
                    display_id = record["example_id"]

            try:
                record_validator(record)
            except ValidationError as exc:
                errors.append(f"Line {lineno} (id={display_id}): {exc}")
                continue

            if isinstance(record, Mapping):
                key_name = "id" if "id" in record else "example_id" if "example_id" in record else None
                if key_name is not None:
                    key_value = record.get(key_name)
                    if isinstance(key_value, str):
                        key = (key_name, key_value)
                        if key in seen:
                            errors.append(
                                f"Line {lineno} ({key_name}={key_value}): duplicate value; "
                                f"first seen on line {seen[key]}."
                            )
                        else:
                            seen[key] = lineno
    except ValidationError as exc:
        errors.append(str(exc))

    return errors
