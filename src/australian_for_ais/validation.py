"""
Validation module for Australian For AIs.

Validates benchmark example records and evaluation prediction records against
packaged JSON Schemas, then applies project-level semantic invariants.
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Iterator, Mapping, Sequence
from importlib import resources
from typing import Any, Callable

import jsonschema

_SCHEMA_PACKAGE_ROOT = resources.files("australian_for_ais").joinpath("schemas")
_EXAMPLE_SCHEMA_RESOURCE = _SCHEMA_PACKAGE_ROOT.joinpath("example.schema.json")
_EVALUATION_SCHEMA_RESOURCE = _SCHEMA_PACKAGE_ROOT.joinpath("evaluation.schema.json")
_INSUFFICIENT_CONTEXT = "insufficient_context"


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
    """Case-fold text and collapse all whitespace runs for semantic comparison."""
    return " ".join(value.split()).casefold()


def _require_non_whitespace_text(record: Mapping[str, Any], field_name: str) -> None:
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"'{field_name}' must contain non-whitespace text.")


def _require_non_whitespace_items(values: Any, field_name: str) -> None:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"'{field_name}[{index}]' must contain non-whitespace text."
            )


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
    for field_name in (
        "id",
        "locale",
        "utterance",
        "context",
        "speaker_relationship",
        "literal_interpretation",
        "primary_pragmatic_interpretation",
        "provenance",
        "license",
    ):
        _require_non_whitespace_text(record, field_name)

    _require_non_whitespace_items(
        record.get("pragmatic_interpretations"), "pragmatic_interpretations"
    )
    _require_non_whitespace_items(
        record.get("alternative_interpretations", []), "alternative_interpretations"
    )

    confidence = record.get("confidence")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not (0.0 <= confidence <= 1.0)
    ):
        raise ValidationError(
            f"'confidence' must be a number between 0.0 and 1.0, got {confidence!r}."
        )

    interps = record.get("pragmatic_interpretations", [])
    if not isinstance(interps, list) or len(interps) < 1:
        raise ValidationError(
            "'pragmatic_interpretations' must contain at least one entry."
        )

    primary = record.get("primary_pragmatic_interpretation", "")
    primary_normalised = _normalise_text(primary)
    if primary_normalised == _INSUFFICIENT_CONTEXT and primary != _INSUFFICIENT_CONTEXT:
        raise ValidationError(
            "The insufficient-context sentinel must be written exactly as "
            "'insufficient_context'."
        )

    # The sentinel is a control value, not an ordinary accepted reading. It is
    # admitted only through the exact primary field and is injected by scoring
    # only for that case.
    for interpretation in interps:
        if isinstance(interpretation, str) and _normalise_text(interpretation) == _INSUFFICIENT_CONTEXT:
            raise ValidationError(
                "'insufficient_context' is reserved for "
                "'primary_pragmatic_interpretation' and must not appear in "
                "'pragmatic_interpretations'."
            )

    accepted = {_normalise_text(v) for v in interps if isinstance(v, str)}
    if primary != _INSUFFICIENT_CONTEXT and primary_normalised not in accepted:
        raise ValidationError(
            "'primary_pragmatic_interpretation' must be present in "
            "'pragmatic_interpretations', unless it is 'insufficient_context'."
        )

    if record.get("ambiguity") is True and len(accepted) < 2:
        raise ValidationError(
            "If 'ambiguity' is true, 'pragmatic_interpretations' must contain "
            "at least two distinct normalized readings."
        )

    if primary == _INSUFFICIENT_CONTEXT:
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

    context_swap_group = record.get("context_swap_group")
    if context_swap_group is not None and (
        not isinstance(context_swap_group, str) or not context_swap_group.strip()
    ):
        raise ValidationError(
            "'context_swap_group' must contain non-whitespace text when present."
        )


def _accepted_direction_set(record: Mapping[str, Any]) -> set[str]:
    """Return normalized accepted directions used to validate context swaps."""
    accepted = {
        _normalise_text(value)
        for value in record.get("pragmatic_interpretations", [])
        if isinstance(value, str)
    }
    if record.get("primary_pragmatic_interpretation") == _INSUFFICIENT_CONTEXT:
        accepted.add(_INSUFFICIENT_CONTEXT)
    return accepted


def validate_context_swap_groups(records: Sequence[Mapping[str, Any]]) -> None:
    """
    Validate dataset-level context-swap contracts.

    Every group must contain at least two records, preserve the same observed
    utterance, use distinct contexts, encode distinct primary pragmatic
    directions, and keep accepted direction sets disjoint between members.
    """
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        group = record.get("context_swap_group")
        if isinstance(group, str) and group.strip():
            groups.setdefault(group, []).append(record)

    for group_name, members in groups.items():
        if len(members) < 2:
            raise ValidationError(
                f"context_swap_group '{group_name}' must contain at least two records."
            )

        utterances = {_normalise_text(str(member["utterance"])) for member in members}
        if len(utterances) != 1:
            raise ValidationError(
                f"context_swap_group '{group_name}' must use the same utterance "
                "for every member."
            )

        contexts = {_normalise_text(str(member["context"])) for member in members}
        if len(contexts) != len(members):
            raise ValidationError(
                f"context_swap_group '{group_name}' must contain a distinct context "
                "for every member."
            )

        primaries = {
            _normalise_text(str(member["primary_pragmatic_interpretation"]))
            for member in members
        }
        if len(primaries) != len(members):
            raise ValidationError(
                f"context_swap_group '{group_name}' must contain a distinct primary "
                "pragmatic interpretation for every member."
            )

        direction_sets = [_accepted_direction_set(member) for member in members]
        for i in range(len(direction_sets)):
            for j in range(i + 1, len(direction_sets)):
                overlap = direction_sets[i] & direction_sets[j]
                if overlap:
                    overlap_text = ", ".join(sorted(overlap))
                    raise ValidationError(
                        f"context_swap_group '{group_name}' must use disjoint accepted "
                        f"pragmatic directions between members; overlap: {overlap_text}."
                    )


def validate_evaluation_record(record: Any) -> None:
    """Validate a single complete evaluation prediction record."""
    if not isinstance(record, Mapping):
        raise ValidationError("Evaluation record must be a JSON object.")

    try:
        jsonschema.validate(record, _get_evaluation_schema())
    except jsonschema.ValidationError as exc:
        raise ValidationError(f"Schema validation failed: {exc.message}") from exc

    for field_name in ("example_id", "predicted_literal", "predicted_pragmatic"):
        _require_non_whitespace_text(record, field_name)

    predicted_pragmatic = record.get("predicted_pragmatic")
    if (
        isinstance(predicted_pragmatic, str)
        and _normalise_text(predicted_pragmatic) == _INSUFFICIENT_CONTEXT
        and predicted_pragmatic != _INSUFFICIENT_CONTEXT
    ):
        raise ValidationError(
            "The insufficient-context prediction sentinel must be written exactly as "
            "'insufficient_context'."
        )

    model_id = record.get("model_id")
    if model_id is not None and (
        not isinstance(model_id, str) or not model_id.strip()
    ):
        raise ValidationError("'model_id' must contain non-whitespace text when present.")

    mc = record.get("model_confidence")
    if (
        not isinstance(mc, (int, float))
        or isinstance(mc, bool)
        or not (0.0 <= mc <= 1.0)
    ):
        raise ValidationError(
            f"'model_confidence' must be a number between 0.0 and 1.0, got {mc!r}."
        )

    ph = record.get("predicted_hostility")
    if not isinstance(ph, bool) and ph != "uncertain":
        raise ValidationError(
            f"'predicted_hostility' must be true, false, or 'uncertain', got {ph!r}."
        )


def iter_jsonl(path: pathlib.Path) -> Iterator[tuple[int, Any]]:
    """Iterate over a regular JSONL file, yielding ``(line_number, value)`` tuples."""
    if not path.is_file():
        raise ValidationError(f"JSONL input is not a regular file: {path}")

    try:
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
    except ValidationError:
        raise
    except OSError as exc:
        detail = exc.strerror or str(exc)
        raise ValidationError(f"Could not read JSONL input '{path}': {detail}") from exc


def validate_jsonl_file(
    path: pathlib.Path,
    record_validator: Callable[[Any], None] | None = None,
) -> list[str]:
    """
    Validate all records in a JSONL file, including dataset-level invariants.

    Duplicate ``id`` or ``example_id`` values are rejected so the validation gate
    cannot approve a file that the corresponding loader later refuses to use.
    Example datasets must contain at least one valid record.
    """
    if record_validator is None:
        record_validator = validate_example_record

    is_example_dataset = record_validator is validate_example_record
    errors: list[str] = []
    seen: dict[tuple[str, str], int] = {}
    valid_example_records: list[Mapping[str, Any]] = []

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

            if is_example_dataset and isinstance(record, Mapping):
                valid_example_records.append(record)

            if isinstance(record, Mapping):
                key_name = (
                    "id"
                    if "id" in record
                    else "example_id"
                    if "example_id" in record
                    else None
                )
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

    if is_example_dataset and not errors:
        if not valid_example_records:
            errors.append("Benchmark dataset must contain at least one example record.")
        else:
            try:
                validate_context_swap_groups(valid_example_records)
            except ValidationError as exc:
                errors.append(str(exc))

    return errors
