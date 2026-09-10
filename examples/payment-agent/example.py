from agent_ledger import Ledger
ledger=Ledger(agent="payment-agent",version="1.0")
@ledger.action("payment.send",policy="payments-v1",authority="operator")
def send_payment(amount): return {"accepted":True,"amount":amount}
print(send_payment(125))
