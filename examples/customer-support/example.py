from agent_ledger import Ledger
ledger=Ledger(agent="support-agent",version="1.0")
@ledger.action("refund.issue",policy="refund-v3",authority="support-service")
def refund(order_id,amount): return {"order":order_id,"amount":amount}
print(refund("order-123",50))
