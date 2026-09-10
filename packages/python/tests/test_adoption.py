from agent_ledger.policy import PolicyEngine

def test_policy_precedence():
 p=PolicyEngine('pay-v1',approval_over=500,deny_over=5000)
 assert p.evaluate(amount=100).decision=='ALLOW'
 assert p.evaluate(amount=1000).decision=='REQUIRE_APPROVAL'
 assert p.evaluate(amount=6000).decision=='DENY'
