from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .evidence import AgentProvenanceEvent, OperationalBoundary


@dataclass(frozen=True)
class PosteriorDataset:
    """Analysis-ready observations. Inference remains the caller's responsibility."""
    rows: tuple[dict[str, Any], ...]

    def to_records(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]

    def to_pandas(self):
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError("Install agent-ledger[analytics] to use pandas export") from exc
        return pd.DataFrame(self.to_records())

    def to_csv(self, path: str | Path) -> Path:
        path = Path(path)
        fields = list(self.rows[0].keys()) if self.rows else ["timestamp", "agent_id", "agent_version", "run_id", "action", "violation", "confidence", "evidence_complete"]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.rows)
        return path

    def to_pymc(self) -> dict[str, Any]:
        """Plain arrays suitable for PyMC model construction; does not run inference."""
        return {
            "violations": [int(row["violation"]) for row in self.rows],
            "agent_version": [row["agent_version"] for row in self.rows],
            "n": len(self.rows),
        }

    def to_stan(self) -> dict[str, Any]:
        """Minimal Bernoulli data dictionary accepted by common Stan models."""
        return {"N": len(self.rows), "y": [int(row["violation"]) for row in self.rows]}


def build_posterior_dataset(events: Iterable[AgentProvenanceEvent], boundary: OperationalBoundary) -> PosteriorDataset:
    rows = []
    for event in events:
        complete = event.prior_state is not None and event.resulting_state is not None and bool(event.action)
        rows.append({
            "timestamp": event.timestamp.isoformat(),
            "agent_id": event.agent_id,
            "agent_version": event.agent_version or "unknown",
            "run_id": event.run_id,
            "action": event.action,
            "violation": not boundary.contains(event),
            "confidence": event.confidence,
            "evidence_complete": complete,
        })
    return PosteriorDataset(tuple(rows))
