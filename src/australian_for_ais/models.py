"""
Data models for Australian For AIs benchmark examples and evaluation records.

These models mirror the JSON Schemas in schemas/. Changes to either must be
reflected in the other. See docs/BENCHMARK-DESIGN.md.

Note on epistemic status:
- BenchmarkExample fields represent annotations, not objective ground truth.
- See docs/INVARIANTS.md, particularly AU-HUMOUR-009.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


HUMOUR_MECHANISMS = frozenset({
    "understatement",
    "sarcasm",
    "irony",
    "deadpan",
    "affectionate_insult",
    "inverse_praise",
    "profanity_non_hostile",
    "discourse_marker",
    "self_deprecation",
    "absurdist_escalation",
    "relational_teasing",
    "tall_poppy_humour",
    "ambiguous_address",
    "literal",
    "unknown",
})

SOCIAL_VALENCE_VALUES = frozenset({
    "friendly", "hostile", "neutral", "ambiguous", "unknown"
})

CULTURAL_DEPENDENCY_VALUES = frozenset({"low", "medium", "high", "unknown"})
SOURCE_TYPE_VALUES = frozenset({"synthetic", "naturalistic", "constructed"})

HostilityValue = bool | Literal["uncertain"]
SocialValence = Literal["friendly", "hostile", "neutral", "ambiguous", "unknown"]


@dataclass
class BenchmarkExample:
    """A single benchmark example with observation and annotation fields kept distinct."""

    id: str
    locale: str
    utterance: str
    context: str
    speaker_relationship: str
    literal_interpretation: str
    pragmatic_interpretations: list[str]
    primary_pragmatic_interpretation: str
    humour_mechanisms: list[str]
    social_valence: SocialValence
    hostility: HostilityValue
    confidence: float
    ambiguity: bool
    cultural_dependency: str
    context_required: bool
    source_type: str
    provenance: str
    license: str
    alternative_interpretations: list[str] = field(default_factory=list)
    annotation_notes: str = ""
    tags: list[str] = field(default_factory=list)
    context_swap_group: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "BenchmarkExample":
        return cls(
            id=data["id"],
            locale=data["locale"],
            utterance=data["utterance"],
            context=data["context"],
            speaker_relationship=data["speaker_relationship"],
            literal_interpretation=data["literal_interpretation"],
            pragmatic_interpretations=data["pragmatic_interpretations"],
            primary_pragmatic_interpretation=data["primary_pragmatic_interpretation"],
            humour_mechanisms=data["humour_mechanisms"],
            social_valence=data["social_valence"],
            hostility=data["hostility"],
            confidence=data["confidence"],
            ambiguity=data["ambiguity"],
            cultural_dependency=data["cultural_dependency"],
            context_required=data["context_required"],
            source_type=data["source_type"],
            provenance=data["provenance"],
            license=data["license"],
            alternative_interpretations=data.get("alternative_interpretations", []),
            annotation_notes=data.get("annotation_notes", ""),
            tags=data.get("tags", []),
            context_swap_group=data.get("context_swap_group"),
        )

    def to_dict(self) -> dict:
        d: dict = {
            "id": self.id,
            "locale": self.locale,
            "utterance": self.utterance,
            "context": self.context,
            "speaker_relationship": self.speaker_relationship,
            "literal_interpretation": self.literal_interpretation,
            "pragmatic_interpretations": self.pragmatic_interpretations,
            "primary_pragmatic_interpretation": self.primary_pragmatic_interpretation,
            "humour_mechanisms": self.humour_mechanisms,
            "social_valence": self.social_valence,
            "hostility": self.hostility,
            "confidence": self.confidence,
            "ambiguity": self.ambiguity,
            "cultural_dependency": self.cultural_dependency,
            "context_required": self.context_required,
            "source_type": self.source_type,
            "provenance": self.provenance,
            "license": self.license,
        }
        if self.alternative_interpretations:
            d["alternative_interpretations"] = self.alternative_interpretations
        if self.annotation_notes:
            d["annotation_notes"] = self.annotation_notes
        if self.tags:
            d["tags"] = self.tags
        if self.context_swap_group is not None:
            d["context_swap_group"] = self.context_swap_group
        return d


@dataclass
class EvaluationRecord:
    """A complete model prediction record used in Phase 1 evaluation."""

    example_id: str
    predicted_literal: str
    predicted_pragmatic: str
    predicted_hostility: HostilityValue
    predicted_social_valence: SocialValence
    predicted_ambiguity: bool
    model_confidence: float
    model_id: str | None = None
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationRecord":
        return cls(
            example_id=data["example_id"],
            predicted_literal=data["predicted_literal"],
            predicted_pragmatic=data["predicted_pragmatic"],
            predicted_hostility=data["predicted_hostility"],
            predicted_social_valence=data["predicted_social_valence"],
            predicted_ambiguity=data["predicted_ambiguity"],
            model_confidence=data["model_confidence"],
            model_id=data.get("model_id"),
            notes=data.get("notes"),
        )
