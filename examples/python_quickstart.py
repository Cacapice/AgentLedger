from agent_ledger import AuditLogger, PolicyBlockedError, audit_tool

logger = AuditLogger.from_env()

@audit_tool(agent_id="payments-agent", action_type="DELEGATED_ACTION", logger=logger)
def create_payment(recipient_account: str, amount: float):
    if amount > 10_000:
        raise PolicyBlockedError("human approval required", code="APPROVAL_REQUIRED")
    return {"status": "QUEUED", "amount": amount}

print(create_payment("ACC-123", 250.0, _user_principal_id="usr_42", _session_id="sess_1"))
