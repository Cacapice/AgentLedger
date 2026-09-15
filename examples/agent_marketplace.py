"""Two agents trade an item with atomic settlement and retry protection."""
from agent_ledger import Ledger

ledger = Ledger(balances={"buyer": 100, "seller": 0})

with ledger.transaction():
    ledger.transfer("buyer", "seller", 25, idempotency_key="trade-coffee-001")
    # Transfer the off-ledger item here. Any exception rolls the balance changes back.

print("buyer:", ledger.balance("buyer"))
print("seller:", ledger.balance("seller"))
print(ledger.get_history())  # install agent-ledger[analytics]
