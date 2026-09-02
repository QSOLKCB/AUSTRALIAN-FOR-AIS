"""
Validation module for Australian For AIs.

Validates benchmark examples, evaluation predictions, Phase 2 pilot items,
and independent human annotations against packaged JSON Schemas, then applies
project-level semantic invariants.
"""

from __future__ import annotations

import json
import math
import pathlib
from collections.abc import Iterator, Mapping, Sequence
from importlib import resources
from typing import Any, Callable

import jsonschema

_SCHEMA_PACKAGE_ROOT = resources.files("australian_for_ais").joinpath("schemas")
_EXAMPLE_SCHEMA_RESOURCE = _SCHEMA_PACKAGE_ROOT.joinpath("example.schema.json")
_EVALUATION_SCHEMA_RESOURCE = _SCHEMA_PACKAGE_ROOT.joinpath("evaluation.schema.json")
_PILOT_ITEM_SCHEMA_RESOURCE = _SCHEMA_PACKAGE_ROOT.joinpath("pilot-item.schema.json")
_ANNOTATION_SCHEMA_RESOURCE = _SCHEMA_PACKAGE_ROOT.joinpath("annotation.schema.json")
_INSUFFICIENT_CONTEXT = "insufficient_context"
_MAX_SAFE_INTEGER_BITS = 12_000


class ValidationError(Exception):
    """Raised when a record fails schema or semantic validation."""


def _load_schema(resource) -> dict:
    """Load and return a packaged JSON Schema resource."""
    return json.loads(resource.read_text(encoding="utf-8"))


def _get_example_schema() -> dict:
    return _load_schema(_EXAMPLE_SCHEMA_RESOURCE)


def _get_evaluation_schema() -> dict:
    return _load_schema(_EVALUATION_SCHEMA_RESOURCE)


def _get_pilot_item_schema() -> dict:
    return _load_schema(_PILOT_ITEM_SCHEMA_RESOURCE)


def _get_annotation_schema() -> dict:
    return _load_schema(_ANNOTATION_SCHEMA_RESOURCE)


def _normalise_text(value: str) -> str:
    """Case-fold text and collapse all whitespace runs for semantic comparison."""
    return " ".join(value.split()).casefold()


def _normalise_observed_utterance(value: str) -> str:
    """Collapse whitespace while preserving lexical case in observed utterances."""
    return " ".join(value.split())


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


def _require_unit_interval_number(
    record: Mapping[str, Any], field_name: str
) -> None:
    """Fail closed on bounded numeric fields without formatting hostile values."""
    if field_name not in record:
        return
    value = record.get(field_name)
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not (0.0 <= value <= 1.0)
    ):
        raise ValidationError(
            f"'{field_name}' must be a number between 0.0 and 1.0."
        )


def _preflight_json_structure(value: Any) -> None:
    """Reject values that can make schema diagnostics recurse or stringify unsafely."""
    # Track only containers currently on the traversal path. A container may be
    # reused in a different, already-completed branch without being a cycle.
    stack: list[tuple[Any, bool]] = [(value, False)]
    active_container_ids: set[int] = set()

    while stack:
        current, exiting = stack.pop()
        is_mapping = isinstance(current, Mapping)
        is_sequence = isinstance(current, Sequence) and not isinstance(
            current, (str, bytes)
        )

        if exiting:
            active_container_ids.remove(id(current))
            continue

        if isinstance(current, bool) or current is None:
            continue
        if isinstance(current, int):
            if current.bit_length() > _MAX_SAFE_INTEGER_BITS:
                raise ValidationError(
                    "Record contains an integer too large to validate safely."
                )
            continue
        if isinstance(current, float):
            if not math.isfinite(current):
                raise ValidationError(
                    "Record contains a non-finite numeric value, which is not valid JSON data."
                )
            continue
        if isinstance(current, str):
            continue

        if is_mapping or is_sequence:
            container_id = id(current)
            if container_id in active_container_ids:
                raise ValidationError(
                    "Record contains a cyclic container reference and cannot be validated."
                )

            active_container_ids.add(container_id)
            stack.append((current, True))

            if is_mapping:
                for key, item in current.items():
                    if not isinstance(key, str):
                        raise ValidationError("JSON object keys must be strings.")
                    stack.append((item, False))
            else:
                for item in current:
                    stack.append((item, False))


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting parser-dependent duplicate keys."""
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise ValidationError(f"Duplicate JSON object key '{key}' is not allowed.")
        record[key] = value
    return record


def _validate_schema_safely(record: Mapping[str, Any], schema: dict) -> None:
    """Run jsonschema while translating input-induced diagnostic failures."""
    try:
        jsonschema.validate(record, schema)
    except jsonschema.ValidationError as exc:
        raise ValidationError(f"Schema validation failed: {exc.message}") from exc
    except (ValueError, OverflowError, RecursionError) as exc:
        raise ValidationError(
            "Schema validation could not safely inspect the supplied record."
        ) from exc


def _validate_interpretation_contract(record: Mapping[str, Any]) -> None:
    """Apply the shared ambiguity and insufficient-context annotation contract."""
    _require_non_whitespace_items(
        record.get("pragmatic_interpretations"), "pragmatic_interpretations"
    )
    _require_non_whitespace_items(
        record.get("alternative_interpretations", []), "alternative_interpretations"
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

    for interpretation in interps:
        if (
            isinstance(interpretation, str)
            and _normalise_text(interpretation) == _INSUFFICIENT_CONTEXT
        ):
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

    confidence = record.get("confidence")
    if primary == _INSUFFICIENT_CONTEXT:
        if record.get("ambiguity") is not True:
            raise ValidationError(
                "'insufficient_context' requires 'ambiguity' to be true."
            )
        if confidence > 0.4:
            raise ValidationError(
                "'insufficient_context' requires confidence at or below 0.4."
            )


def validate_example_record(record: Any) -> None:
    """Validate a single benchmark example record."""
    if not isinstance(record, Mapping):
        raise ValidationError("Example record must be a JSON object.")

    _require_unit_interval_number(record, "confidence")
    _preflight_json_structure(record)
    _validate_schema_safely(record, _get_example_schema())
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

    _require_unit_interval_number(record, "confidence")
    _validate_interpretation_contract(record)

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


def validate_pilot_item_record(record: Any) -> None:
    """Validate one unannotated Phase 2 pilot item."""
    if not isinstance(record, Mapping):
        raise ValidationError("Pilot item must be a JSON object.")

    _preflight_json_structure(record)
    _validate_schema_safely(record, _get_pilot_item_schema())

    for field_name in (
        "id",
        "locale",
        "utterance",
        "context",
        "speaker_relationship",
        "provenance",
        "license",
    ):
        _require_non_whitespace_text(record, field_name)

    _require_non_whitespace_items(record.get("tags", []), "tags")


def validate_annotation_record(record: Any) -> None:
    """Validate one independent Phase 2 human annotation."""
    if not isinstance(record, Mapping):
        raise ValidationError("Human annotation must be a JSON object.")

    _require_unit_interval_number(record, "confidence")
    _preflight_json_structure(record)
    _validate_schema_safely(record, _get_annotation_schema())

    for field_name in (
        "annotation_id",
        "example_id",
        "annotator_id",
        "literal_interpretation",
        "primary_pragmatic_interpretation",
    ):
        _require_non_whitespace_text(record, field_name)

    _validate_interpretation_contract(record)

    hostility = record.get("hostility")
    if not isinstance(hostility, bool) and hostility != "uncertain":
        raise ValidationError(
            f"'hostility' must be true, false, or 'uncertain', got {hostility!r}."
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
    utterance including lexical case, use distinct contexts, encode distinct
    primary pragmatic directions, and keep accepted direction sets disjoint
    between members.
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

        utterances = {
            _normalise_observed_utterance(str(member["utterance"]))
            for member in members
        }
        if len(utterances) != 1:
            raise ValidationError(
                f"context_swap_group '{group_name}' must use the same utterance "
                "for every member, preserving lexical case."
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

    _require_unit_interval_number(record, "model_confidence")
    _preflight_json_structure(record)
    _validate_schema_safely(record, _get_evaluation_schema())

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

    _require_unit_interval_number(record, "model_confidence")

    ph = record.get("predicted_hostility")
    if not isinstance(ph, bool) and ph != "uncertain":
        raise ValidationError(
            f"'predicted_hostility' must be true, false, or 'uncertain', got {ph!r}."
        )


def iter_jsonl(path: pathlib.Path) -> Iterator[tuple[int, Any]]:
    """Iterate over a regular UTF-8 JSONL file, yielding line-numbered values."""
    if not path.is_file():
        raise ValidationError(f"JSONL input is not a regular file: {path}")

    try:
        with path.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield lineno, json.loads(
                        line, object_pairs_hook=_reject_duplicate_object_keys
                    )
                except json.JSONDecodeError as exc:
                    raise ValidationError(
                        f"Line {lineno}: malformed JSON — {exc}"
                    ) from exc
                except ValidationError as exc:
                    raise ValidationError(f"Line {lineno}: {exc}") from exc
                except ValueError as exc:
                    raise ValidationError(
                        f"Line {lineno}: JSON value could not be parsed safely — {exc}"
                    ) from exc
                except RecursionError as exc:
                    raise ValidationError(
                        f"Line {lineno}: JSON nesting is too deep to parse safely."
                    ) from exc
    except ValidationError:
        raise
    except UnicodeError as exc:
        raise ValidationError(
            f"Could not decode JSONL input '{path}' as UTF-8: {exc}"
        ) from exc
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
