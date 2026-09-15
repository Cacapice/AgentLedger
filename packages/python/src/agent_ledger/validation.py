from __future__ import annotations

from collections import defaultdict
from typing import Literal

from .evidence import AgentProvenanceEvent, EventValidation, OperationalBoundary, ValidationResult, validate_evidence
from .posterior import PosteriorDataset, build_posterior_dataset


class BoundaryViolationError(RuntimeError):
    def __init__(self, result: EventValidation):
        super().__init__(f"event {result.event_id} violates boundary {result.boundary}")
        self.result = result


class EvidenceLedger:
    """Small validation view: APE collection + safe-set enforcement + analysis export."""

    def __init__(self, *, enforcement: Literal["observe", "strict"] = "observe") -> None:
        if enforcement not in {"observe", "strict"}:
            raise ValueError("enforcement must be 'observe' or 'strict'")
        self.enforcement = enforcement
        self._evidence: list[AgentProvenanceEvent] = []
        self._boundaries: dict[str, OperationalBoundary] = {}

    def record(self, evidence: AgentProvenanceEvent) -> AgentProvenanceEvent:
        if self.enforcement == "strict":
            for boundary in self._boundaries.values():
                result = self.validate_event(evidence, boundary.name)
                if not result.valid:
                    raise BoundaryViolationError(result)
        self._evidence.append(evidence)
        return evidence

    def evidence(self, run_id: str | None = None) -> list[AgentProvenanceEvent]:
        if run_id is None:
            return list(self._evidence)
        return [item for item in self._evidence if item.run_id == run_id]

    def define_boundary(self, name: str, predicate, *, description: str = "") -> OperationalBoundary:
        boundary = OperationalBoundary(name=name, predicate=predicate, description=description)
        self._boundaries[name] = boundary
        return boundary

    define_safe_set = define_boundary

    def validate_event(self, event: AgentProvenanceEvent, boundary: str) -> EventValidation:
        try:
            rule = self._boundaries[boundary]
        except KeyError as exc:
            raise KeyError(f"unknown operational boundary: {boundary}") from exc
        valid = rule.contains(event)
        return EventValidation(str(event.event_id), boundary, valid, None if valid else "outside_safe_set")

    def validate(self, boundary: str, *, run_id: str | None = None,
                 prior_alpha: float = 1.0, prior_beta: float = 1.0) -> ValidationResult:
        try:
            rule = self._boundaries[boundary]
        except KeyError as exc:
            raise KeyError(f"unknown operational boundary: {boundary}") from exc
        return validate_evidence(self.evidence(run_id), rule, prior_alpha=prior_alpha, prior_beta=prior_beta)

    def compare_versions(self, boundary: str) -> dict[str, ValidationResult]:
        grouped: dict[str, list[AgentProvenanceEvent]] = defaultdict(list)
        for item in self._evidence:
            grouped[item.agent_version or "unknown"].append(item)
        rule = self._boundaries[boundary]
        return {version: validate_evidence(rows, rule) for version, rows in grouped.items()}

    def posterior_dataset(self, *, boundary: str, run_id: str | None = None) -> PosteriorDataset:
        try:
            rule = self._boundaries[boundary]
        except KeyError as exc:
            raise KeyError(f"unknown operational boundary: {boundary}") from exc
        return build_posterior_dataset(self.evidence(run_id), rule)
