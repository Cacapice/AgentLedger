import pytest

from agent_ledger import Evidence, EvidenceLedger


def test_evidence_confidence_is_bounded():
    with pytest.raises(ValueError):
        Evidence(agent_id="a", action="x", confidence=1.1)


def test_boundary_validation_and_beta_posterior():
    ledger = EvidenceLedger()
    ledger.define_boundary("nonnegative", lambda e: e.resulting_state["balance"] >= 0)
    ledger.record(Evidence("a", "spend", {"balance": 10}, {"balance": 5}, run_id="r1"))
    ledger.record(Evidence("a", "spend", {"balance": 5}, {"balance": -1}, run_id="r1"))
    result = ledger.validate("nonnegative", run_id="r1")
    assert result.transitions == 2
    assert result.violations == 1
    assert result.violation_rate == 0.5
    assert result.posterior_alpha == 2.0
    assert result.posterior_beta == 2.0
    assert result.evidence_completeness == 1.0


def test_compare_versions():
    ledger = EvidenceLedger()
    ledger.define_boundary("safe", lambda e: e.outcome != "violation")
    ledger.record(Evidence("a", "x", {}, {}, outcome="ok", agent_version="v1"))
    ledger.record(Evidence("a", "x", {}, {}, outcome="violation", agent_version="v2"))
    results = ledger.compare_versions("safe")
    assert results["v1"].violations == 0
    assert results["v2"].violations == 1


def test_ape_schema_and_posterior_exports():
    from agent_ledger import AgentProvenanceEvent
    event = AgentProvenanceEvent(agent_id="a", action="x", prior_state={}, resulting_state={}, agent_version="v1")
    assert event.schema_version == "ape/1.0"
    ledger = EvidenceLedger()
    ledger.define_safe_set("safe", lambda e: e.outcome != "bad")
    ledger.record(event)
    data = ledger.posterior_dataset(boundary="safe")
    assert data.to_pymc()["n"] == 1
    assert data.to_stan()["y"] == [0]


def test_strict_mode_blocks_boundary_violation():
    from agent_ledger import BoundaryViolationError
    ledger = EvidenceLedger(enforcement="strict")
    ledger.define_safe_set("nonnegative", lambda e: e.resulting_state["balance"] >= 0)
    with pytest.raises(BoundaryViolationError):
        ledger.record(Evidence(agent_id="a", action="spend", prior_state={"balance": 1}, resulting_state={"balance": -1}))
    assert ledger.evidence() == []
