from dataclasses import dataclass
@dataclass(frozen=True)
class PolicyDecision:
    decision:str; reason:str; policy_id:str
class PolicyEngine:
    """Minimal deterministic action policy: deny > approval > allow."""
    def __init__(self, policy_id, *, deny_over=None, approval_over=None): self.policy_id=policy_id; self.deny_over=deny_over; self.approval_over=approval_over
    def evaluate(self, *, amount=None):
        if amount is not None and self.deny_over is not None and amount>self.deny_over:return PolicyDecision('DENY',f'amount exceeds {self.deny_over}',self.policy_id)
        if amount is not None and self.approval_over is not None and amount>self.approval_over:return PolicyDecision('REQUIRE_APPROVAL',f'amount exceeds {self.approval_over}',self.policy_id)
        return PolicyDecision('ALLOW','policy satisfied',self.policy_id)
