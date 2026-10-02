from __future__ import annotations
import copy, functools, threading, time
from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Mapping
from .core import AuditLogger, PolicyBlockedError, sha256_hex

class InsufficientFundsError(RuntimeError): pass
class IdempotencyConflictError(RuntimeError): pass

class Ledger:
    """Small transactional action ledger retained for backwards compatibility.

    Balances are Decimal-backed, mutations are atomic under an RLock, and
    idempotency keys are bound to the operation payload so a key cannot be
    silently reused for a different effect.
    """
    def __init__(self, logger=None, agent="agent", version=None, balances: Mapping[str, Any] | None=None):
        self.logger=logger or AuditLogger.from_env(); self.agent=agent; self.version=version
        self._balances={str(k): Decimal(str(v)) for k,v in (balances or {}).items()}
        self._history=[]; self._idempotency={}; self._lock=threading.RLock()

    def balance(self, account): return self._balances.get(str(account), Decimal("0"))

    @contextmanager
    def transaction(self):
        with self._lock:
            snapshot=(copy.deepcopy(self._balances), copy.deepcopy(self._history), copy.deepcopy(self._idempotency))
            try: yield self
            except BaseException:
                self._balances,self._history,self._idempotency=snapshot
                raise

    def _once(self, key, payload, operation):
        if not key: return operation()
        digest=sha256_hex(payload)
        if key in self._idempotency:
            prior_digest, result=self._idempotency[key]
            if prior_digest != digest: raise IdempotencyConflictError(f"idempotency key {key!r} was already used for a different operation")
            return result
        result=operation(); self._idempotency[key]=(digest,result); return result

    def _record(self, event, **fields):
        row={"event":event,"timestamp":time.time(),**fields}; self._history.append(row); return row

    def debit(self, account, amount, *, idempotency_key=None):
        account=str(account); amount=Decimal(str(amount))
        if amount < 0: raise ValueError("amount must be nonnegative")
        payload={"op":"debit","account":account,"amount":str(amount)}
        with self._lock:
            def apply():
                before=self.balance(account)
                if before < amount: raise InsufficientFundsError(f"insufficient funds in {account}")
                self._balances[account]=before-amount
                return self._record("debit",account=account,amount=amount,balance=self._balances[account])
            return self._once(idempotency_key,payload,apply)

    def credit(self, account, amount, *, idempotency_key=None):
        account=str(account); amount=Decimal(str(amount))
        if amount < 0: raise ValueError("amount must be nonnegative")
        payload={"op":"credit","account":account,"amount":str(amount)}
        with self._lock:
            def apply():
                self._balances[account]=self.balance(account)+amount
                return self._record("credit",account=account,amount=amount,balance=self._balances[account])
            return self._once(idempotency_key,payload,apply)

    def transfer(self, source, destination, amount, *, idempotency_key=None):
        source,destination=str(source),str(destination); amount=Decimal(str(amount))
        if amount < 0: raise ValueError("amount must be nonnegative")
        payload={"op":"transfer","source":source,"destination":destination,"amount":str(amount)}
        with self._lock:
            def apply():
                before=self.balance(source)
                if before < amount: raise InsufficientFundsError(f"insufficient funds in {source}")
                self._balances[source]=before-amount; self._balances[destination]=self.balance(destination)+amount
                return self._record("transfer",source=source,destination=destination,amount=amount,source_balance=self._balances[source],destination_balance=self._balances[destination])
            return self._once(idempotency_key,payload,apply)

    def get_history(self):
        try:
            import pandas as pd
            return pd.DataFrame(self._history)
        except ImportError: return list(self._history)

    def limit_spending(self, maximum):
        maximum=Decimal(str(maximum))
        def deco(fn):
            @functools.wraps(fn)
            def wrapped(*args,**kwargs):
                before=sum(self._balances.values(),Decimal("0"))
                with self.transaction():
                    out=fn(*args,**kwargs)
                    spent=before-sum(self._balances.values(),Decimal("0"))
                    if spent > maximum: raise PolicyBlockedError(f"spending limit exceeded: {spent} > {maximum}","SPENDING_LIMIT")
                    return out
            return wrapped
        return deco

    def action(self, name, *, policy=None, authority="system", tool=None):
        def deco(fn):
            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                start=time.perf_counter(); out=None; status="SUCCESS"; err=None
                try: out=fn(*args, **kwargs); return out
                except PolicyBlockedError as e: status="BLOCKED_BY_POLICY"; err=e; raise
                except Exception as e: status="FAILED"; err=e; raise
                finally:
                    self.logger.log_event(agent_id=self.agent,agent_version=self.version,user_principal_id=authority,tool_name=tool or name,action_type=name,input_params={"args":args,"kwargs":kwargs},output=out,duration_ms=(time.perf_counter()-start)*1000,status=status,error=err,policy_context={"policy_id":policy,"decision":"ALLOWED"} if policy else None)
            return wrapped
        return deco
ledger=Ledger()
