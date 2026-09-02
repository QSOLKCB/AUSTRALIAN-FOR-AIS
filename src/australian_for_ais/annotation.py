"""Phase 2 pilot annotation loading and inter-annotator agreement utilities.

The module is deliberately offline and deterministic. Free-text pragmatic readings are
preserved as qualitative data and are not converted into a misleading exact-match IAA score.
"""

from __future__ import annotations

import itertools
import pathlib
from collections import Counter, defaultdict
from typing import Any

from .models import HumanAnnotation, PilotItem
from .validation import (
    ValidationError,
    iter_jsonl,
    validate_annotation_record,
    validate_pilot_item_record,
)


def _normalise_observed_utterance(value: str) -> str:
    return " ".join(value.split())


def _normalise_context(value: str) -> str:
    return " ".join(value.split()).casefold()


def _normalise_context_observation(item: PilotItem) -> tuple[str, str]:
    """Normalize the supplied context and relationship as one experimental observation."""
    return (
        _normalise_context(item.context),
        _normalise_context(item.speaker_relationship),
    )


def _pilot_group_line_suffix(
    members: list[PilotItem], source_lines: dict[str, int] | None
) -> str:
    if not source_lines:
        return ""
    lines = sorted({source_lines[item.id] for item in members if item.id in source_lines})
    if not lines:
        return ""
    label = "line" if len(lines) == 1 else "lines"
    return f" ({label} {', '.join(str(line) for line in lines)})"


def validate_pilot_context_swap_groups(
    items: list[PilotItem], source_lines: dict[str, int] | None = None
) -> None:
    """Validate only observation-level contracts for unannotated pilot swap groups."""
    groups: dict[str, list[PilotItem]] = defaultdict(list)
    for item in items:
        if item.context_swap_group:
            groups[item.context_swap_group].append(item)

    for group_name, members in groups.items():
        line_suffix = _pilot_group_line_suffix(members, source_lines)
        if len(members) < 2:
            raise ValidationError(
                f"Pilot context_swap_group '{group_name}'{line_suffix} must contain at least two items."
            )
        utterances = {_normalise_observed_utterance(item.utterance) for item in members}
        if len(utterances) != 1:
            raise ValidationError(
                f"Pilot context_swap_group '{group_name}'{line_suffix} must preserve the same utterance."
            )
        observations = {_normalise_context_observation(item) for item in members}
        if len(observations) != len(members):
            raise ValidationError(
                f"Pilot context_swap_group '{group_name}'{line_suffix} must use distinct context/relationship observations."
            )


def load_pilot_items(path: pathlib.Path) -> dict[str, PilotItem]:
    """Load a non-empty pilot item file and validate duplicate/group contracts."""
    items: dict[str, PilotItem] = {}
    source_lines: dict[str, int] = {}
    for lineno, record in iter_jsonl(path):
        try:
            validate_pilot_item_record(record)
        except ValidationError as exc:
            raise ValidationError(f"Line {lineno}: {exc}") from exc
        item = PilotItem.from_dict(record)
        if item.id in items:
            raise ValidationError(f"Line {lineno}: duplicate pilot item id '{item.id}'.")
        items[item.id] = item
        source_lines[item.id] = lineno

    if not items:
        raise ValidationError("Pilot item file must contain at least one item.")

    validate_pilot_context_swap_groups(list(items.values()), source_lines=source_lines)
    return items


def load_annotations(
    path: pathlib.Path,
    known_example_ids: set[str] | None = None,
) -> list[HumanAnnotation]:
    """Load a non-empty independent annotation file, rejecting duplicate assignments."""
    annotations: list[HumanAnnotation] = []
    annotation_ids: set[str] = set()
    assignments: set[tuple[str, str]] = set()

    for lineno, record in iter_jsonl(path):
        try:
            validate_annotation_record(record)
        except ValidationError as exc:
            raise ValidationError(f"Line {lineno}: {exc}") from exc
        annotation = HumanAnnotation.from_dict(record)

        if annotation.annotation_id in annotation_ids:
            raise ValidationError(
                f"Line {lineno}: duplicate annotation_id '{annotation.annotation_id}'."
            )
        annotation_ids.add(annotation.annotation_id)

        assignment = (annotation.example_id, annotation.annotator_id)
        if assignment in assignments:
            raise ValidationError(
                f"Line {lineno}: annotator '{annotation.annotator_id}' has more than one "
                f"annotation for example '{annotation.example_id}'."
            )
        assignments.add(assignment)

        if known_example_ids is not None and annotation.example_id not in known_example_ids:
            raise ValidationError(
                f"Line {lineno}: annotation references unknown example_id "
                f"'{annotation.example_id}'."
            )

        annotations.append(annotation)

    if not annotations:
        raise ValidationError("Annotation file must contain at least one annotation record.")

    return annotations


def _group_annotations(
    annotations: list[HumanAnnotation],
) -> dict[str, list[HumanAnnotation]]:
    grouped: dict[str, list[HumanAnnotation]] = defaultdict(list)
    for annotation in annotations:
        grouped[annotation.example_id].append(annotation)
    return grouped


def annotation_coverage(
    items: dict[str, PilotItem], annotations: list[HumanAnnotation]
) -> dict[str, Any]:
    grouped = _group_annotations(annotations)
    counts = {item_id: len(grouped.get(item_id, [])) for item_id in items}
    under_two = sorted(item_id for item_id, count in counts.items() if count < 2)
    return {
        "items_total": len(items),
        "annotations_total": len(annotations),
        "annotators_total": len({a.annotator_id for a in annotations}),
        "annotations_per_item": counts,
        "items_with_at_least_one_annotation": sum(count >= 1 for count in counts.values()),
        "items_with_at_least_two_annotations": sum(count >= 2 for count in counts.values()),
        "items_below_two_annotations": under_two,
        "minimum_annotations_per_item": min(counts.values()) if counts else 0,
        "maximum_annotations_per_item": max(counts.values()) if counts else 0,
    }


def _within_item_pairs(
    annotations: list[HumanAnnotation],
) -> list[tuple[HumanAnnotation, HumanAnnotation]]:
    pairs: list[tuple[HumanAnnotation, HumanAnnotation]] = []
    for members in _group_annotations(annotations).values():
        pairs.extend(itertools.combinations(members, 2))
    return pairs


def pairwise_nominal_agreement(
    annotations: list[HumanAnnotation], field_name: str
) -> dict[str, Any]:
    """Return descriptive pairwise agreement for one categorical annotation field."""
    pairs = _within_item_pairs(annotations)
    agreements = sum(
        getattr(left, field_name) == getattr(right, field_name) for left, right in pairs
    )
    return {
        "field": field_name,
        "agreeing_pairs": agreements,
        "comparable_pairs": len(pairs),
        "agreement_rate": round(agreements / len(pairs), 4) if pairs else None,
    }


def cohen_kappa_for_pair(
    annotations: list[HumanAnnotation],
    field_name: str,
    annotator_a: str,
    annotator_b: str,
) -> dict[str, Any]:
    """Compute Cohen's kappa on examples shared by two named pseudonymous annotators."""
    by_annotator: dict[str, dict[str, HumanAnnotation]] = defaultdict(dict)
    for annotation in annotations:
        by_annotator[annotation.annotator_id][annotation.example_id] = annotation

    shared_ids = sorted(
        set(by_annotator.get(annotator_a, {})) & set(by_annotator.get(annotator_b, {}))
    )
    if not shared_ids:
        return {
            "annotators": [annotator_a, annotator_b],
            "field": field_name,
            "shared_examples": 0,
            "kappa": None,
        }

    ratings_a = [getattr(by_annotator[annotator_a][item_id], field_name) for item_id in shared_ids]
    ratings_b = [getattr(by_annotator[annotator_b][item_id], field_name) for item_id in shared_ids]
    observed = sum(a == b for a, b in zip(ratings_a, ratings_b)) / len(shared_ids)

    counts_a = Counter(ratings_a)
    counts_b = Counter(ratings_b)
    categories = set(counts_a) | set(counts_b)
    expected = sum(
        (counts_a[category] / len(shared_ids)) * (counts_b[category] / len(shared_ids))
        for category in categories
    )
    kappa = None if expected == 1.0 else (observed - expected) / (1.0 - expected)

    return {
        "annotators": [annotator_a, annotator_b],
        "field": field_name,
        "shared_examples": len(shared_ids),
        "observed_agreement": round(observed, 4),
        "expected_agreement": round(expected, 4),
        "kappa": round(kappa, 4) if kappa is not None else None,
    }


def all_pairwise_cohen_kappas(
    annotations: list[HumanAnnotation], field_name: str
) -> list[dict[str, Any]]:
    annotators = sorted({annotation.annotator_id for annotation in annotations})
    return [
        cohen_kappa_for_pair(annotations, field_name, left, right)
        for left, right in itertools.combinations(annotators, 2)
    ]


def mechanism_agreement(annotations: list[HumanAnnotation]) -> dict[str, Any]:
    """Report exact-set agreement and mean Jaccard overlap for mechanism tags."""
    pairs = _within_item_pairs(annotations)
    if not pairs:
        return {
            "comparable_pairs": 0,
            "exact_set_agreement_rate": None,
            "mean_jaccard": None,
        }

    exact = 0
    jaccard_total = 0.0
    for left, right in pairs:
        left_set = set(left.humour_mechanisms)
        right_set = set(right.humour_mechanisms)
        if left_set == right_set:
            exact += 1
        union = left_set | right_set
        jaccard_total += 1.0 if not union else len(left_set & right_set) / len(union)

    return {
        "comparable_pairs": len(pairs),
        "exact_set_agreement_rate": round(exact / len(pairs), 4),
        "mean_jaccard": round(jaccard_total / len(pairs), 4),
    }


def confidence_difference(annotations: list[HumanAnnotation]) -> dict[str, Any]:
    """Report descriptive pairwise confidence difference; this is not an IAA coefficient."""
    pairs = _within_item_pairs(annotations)
    if not pairs:
        return {"comparable_pairs": 0, "mean_absolute_difference": None}
    difference = sum(abs(left.confidence - right.confidence) for left, right in pairs)
    return {
        "comparable_pairs": len(pairs),
        "mean_absolute_difference": round(difference / len(pairs), 4),
    }


def build_agreement_report(
    items: dict[str, PilotItem], annotations: list[HumanAnnotation]
) -> dict[str, Any]:
    """Build the deterministic Phase 2 pilot agreement report."""
    categorical_fields = (
        "hostility",
        "social_valence",
        "ambiguity",
        "cultural_dependency",
        "context_required",
    )
    return {
        "coverage": annotation_coverage(items, annotations),
        "categorical_pairwise_agreement": {
            field: pairwise_nominal_agreement(annotations, field)
            for field in categorical_fields
        },
        "cohen_kappa_by_annotator_pair": {
            field: all_pairwise_cohen_kappas(annotations, field)
            for field in categorical_fields
        },
        "mechanism_agreement": mechanism_agreement(annotations),
        "confidence_difference": confidence_difference(annotations),
        "pragmatic_free_text_iaa": None,
        "pragmatic_free_text_note": (
            "Free-text pragmatic interpretations are retained for qualitative/adjudication "
            "analysis and are not scored by exact-string agreement."
        ),
    }
