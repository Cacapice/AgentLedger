from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Literal, Mapping, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AgentProvenanceEvent(BaseModel):
    """APE 1.0: canonical, versioned evidence record for an agent transition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["ape/1.0"] = "ape/1.0"
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: str
    action: str
    agent_version: str | None = None
    run_id: str | None = None
    prior_state: Any = None
    resulting_state: Any = None
    observation: Any = None
    outcome: Any = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    policy_id: str | None = None
    provenance: Mapping[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None

    def __init__(self, agent_id: str | None = None, action: str | None = None, prior_state: Any = None, resulting_state: Any = None, **data: Any) -> None:
        # Preserve the original Evidence(agent_id, action, prior_state, resulting_state, ...) API.
        if agent_id is not None:
            data["agent_id"] = agent_id
        if action is not None:
            data["action"] = action
        if prior_state is not None:
            data["prior_state"] = prior_state
        if resulting_state is not None:
            data["resulting_state"] = resulting_state
        super().__init__(**data)

    @property
    def policy(self) -> str | None:  # backwards-compatible name
        return self.policy_id

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


# Backwards-compatible public name; APE is now the canonical representation.
Evidence = AgentProvenanceEvent


@dataclass(frozen=True)
class OperationalBoundary:
    """Named safe set over observed state/action/state transitions."""

    name: str
    predicate: Callable[[AgentProvenanceEvent], bool]
    description: str = ""

    def contains(self, evidence: AgentProvenanceEvent) -> bool:
        return bool(self.predicate(evidence))


@dataclass(frozen=True)
class EventValidation:
    event_id: str
    boundary: str
    valid: bool
    violation: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    boundary: str
    transitions: int
    inside_safe_set: int
    violations: int
    violation_rate: float
    posterior_alpha: float
    posterior_beta: float
    evidence_completeness: float
    violation_indices: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_evidence(
    evidence: Iterable[AgentProvenanceEvent],
    boundary: OperationalBoundary,
    *,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
) -> ValidationResult:
    """Return safe-set counts and a Beta posterior over violation probability."""
    if prior_alpha <= 0 or prior_beta <= 0:
        raise ValueError("Beta prior parameters must be positive")
    rows = list(evidence)
    violations: list[int] = []
    complete = 0
    for index, item in enumerate(rows):
        if item.prior_state is not None and item.resulting_state is not None and item.action:
            complete += 1
        if not boundary.contains(item):
            violations.append(index)
    n = len(rows)
    v = len(violations)
    return ValidationResult(
        boundary=boundary.name,
        transitions=n,
        inside_safe_set=n - v,
        violations=v,
        violation_rate=(v / n) if n else 0.0,
        posterior_alpha=prior_alpha + v,
        posterior_beta=prior_beta + (n - v),
        evidence_completeness=(complete / n) if n else 1.0,
        violation_indices=tuple(violations),
    )
