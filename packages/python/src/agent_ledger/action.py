from __future__ import annotations

import contextvars
import functools
import json
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterator, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .core import AuditLogger, PolicyBlockedError, utc_now


class LedgerError(RuntimeError):
    """Base error for balance-ledger operations."""


class InsufficientFundsError(LedgerError):
    """Raised when strict mode would allow an account to go below zero."""


class IdempotencyConflictError(LedgerError):
    """Raised when an idempotency key is reused for a different operation."""


class TransactionRecord(BaseModel):
    """Validated, IDE-friendly representation of a balance mutation."""

    model_config = ConfigDict(frozen=True)
    event: str
    account: str | None = None
    from_agent: str | None = None
    to_agent: str | None = None
    amount: Decimal = Field(gt=0)
    idempotency_key: str | None = None
    timestamp: str

    @field_validator("account", "from_agent", "to_agent")
    @classmethod
    def non_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("account identifiers must not be blank")
        return value


@dataclass
class _TransactionState:
    balances: dict[str, Decimal]
    history_len: int
    idempotency: dict[str, tuple[Any, ...]]


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = getattr(record, "ledger_event", {"event": "log", "message": record.getMessage()})
        return json.dumps(payload, default=str, sort_keys=True, separators=(",", ":"))


class Ledger:
    """Agent audit helper plus a small, safe in-memory balance ledger.

    Balance operations are validated with Pydantic, support idempotency, strict
    non-negative balances, atomic ``with ledger.transaction():`` blocks,
    structured JSON logging, and Pandas/CSV-friendly history export.
    """

    def __init__(self, logger=None, agent="agent", version=None, *, strict: bool = True, balances: Mapping[str, int | float | Decimal] | None = None):
        self.logger = logger or AuditLogger.from_env()
        self.agent = agent
        self.version = version
        self.strict = strict
        self._balances = {str(k): self._money(v) for k, v in (balances or {}).items()}
        self._history: list[TransactionRecord] = []
        self._idempotency: dict[str, tuple[Any, ...]] = {}
        self._tx_state: contextvars.ContextVar[_TransactionState | None] = contextvars.ContextVar("agent_ledger_transaction", default=None)
        self._structured_logger = logging.getLogger("agent_ledger.transactions")
        if not self._structured_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(_JsonFormatter())
            self._structured_logger.addHandler(handler)
            self._structured_logger.propagate = False
        self._structured_logger.setLevel(logging.INFO)

    @staticmethod
    def _money(value: int | float | Decimal) -> Decimal:
        amount = Decimal(str(value))
        if not amount.is_finite():
            raise ValueError("amount must be finite")
        return amount

    def balance(self, agent: str) -> Decimal:
        return self._balances.get(agent, Decimal("0"))

    def set_balance(self, agent: str, amount: int | float | Decimal) -> Decimal:
        value = self._money(amount)
        if self.strict and value < 0:
            raise InsufficientFundsError(f"negative balance is not allowed for {agent!r}")
        self._balances[agent] = value
        return value

    def _fingerprint(self, *parts: Any) -> tuple[Any, ...]:
        return tuple(str(p) if isinstance(p, Decimal) else p for p in parts)

    def _check_idempotency(self, key: str | None, fingerprint: tuple[Any, ...]) -> bool:
        if not key:
            return False
        prior = self._idempotency.get(key)
        if prior is None:
            self._idempotency[key] = fingerprint
            return False
        if prior != fingerprint:
            raise IdempotencyConflictError(f"idempotency key {key!r} was already used for a different operation")
        return True

    def _record(self, record: TransactionRecord) -> TransactionRecord:
        self._history.append(record)
        payload = record.model_dump(mode="json")
        self._structured_logger.info(record.event, extra={"ledger_event": payload})
        self.logger.log_event(
            agent_id=self.agent,
            agent_version=self.version,
            tool_name=f"ledger.{record.event}",
            action_type="LEDGER_TRANSACTION",
            input_params=payload,
            output={"recorded": True},
        )
        return record

    def credit(self, agent: str, amount: int | float | Decimal, *, idempotency_key: str | None = None) -> TransactionRecord:
        value = self._money(amount)
        if value <= 0:
            raise ValueError("amount must be greater than zero")
        fp = self._fingerprint("credit", agent, value)
        if self._check_idempotency(idempotency_key, fp):
            return next(r for r in reversed(self._history) if r.idempotency_key == idempotency_key)
        self._balances[agent] = self.balance(agent) + value
        return self._record(TransactionRecord(event="credit", account=agent, amount=value, idempotency_key=idempotency_key, timestamp=utc_now()))

    def debit(self, agent: str, amount: int | float | Decimal, *, allow_negative: bool | None = None, idempotency_key: str | None = None) -> TransactionRecord:
        value = self._money(amount)
        if value <= 0:
            raise ValueError("amount must be greater than zero")
        fp = self._fingerprint("debit", agent, value, allow_negative)
        if self._check_idempotency(idempotency_key, fp):
            return next(r for r in reversed(self._history) if r.idempotency_key == idempotency_key)
        enforce = self.strict if allow_negative is None else not allow_negative
        new_balance = self.balance(agent) - value
        if enforce and new_balance < 0:
            if idempotency_key:
                self._idempotency.pop(idempotency_key, None)
            raise InsufficientFundsError(f"debit of {value} would overdraw {agent!r}")
        self._balances[agent] = new_balance
        return self._record(TransactionRecord(event="debit", account=agent, amount=value, idempotency_key=idempotency_key, timestamp=utc_now()))

    def transfer(self, from_agent: str, to_agent: str, amount: int | float | Decimal, *, allow_negative: bool = False, idempotency_key: str | None = None) -> TransactionRecord:
        value = self._money(amount)
        if value <= 0:
            raise ValueError("amount must be greater than zero")
        fp = self._fingerprint("transfer", from_agent, to_agent, value, allow_negative)
        if self._check_idempotency(idempotency_key, fp):
            return next(r for r in reversed(self._history) if r.idempotency_key == idempotency_key)
        new_from = self.balance(from_agent) - value
        if not allow_negative and new_from < 0:
            if idempotency_key:
                self._idempotency.pop(idempotency_key, None)
            raise InsufficientFundsError(f"transfer of {value} would overdraw {from_agent!r}")
        self._balances[from_agent] = new_from
        self._balances[to_agent] = self.balance(to_agent) + value
        return self._record(TransactionRecord(event="transfer", from_agent=from_agent, to_agent=to_agent, amount=value, idempotency_key=idempotency_key, timestamp=utc_now()))

    @contextmanager
    def transaction(self) -> Iterator["Ledger"]:
        """Make a group of balance operations atomic; rollback on any exception."""
        if self._tx_state.get() is not None:
            yield self
            return
        state = _TransactionState(dict(self._balances), len(self._history), dict(self._idempotency))
        token = self._tx_state.set(state)
        try:
            yield self
        except Exception:
            self._balances = state.balances
            del self._history[state.history_len:]
            self._idempotency = state.idempotency
            raise
        finally:
            self._tx_state.reset(token)

    def get_history(self):
        """Return transaction history as a Pandas DataFrame.

        Pandas is an optional analytics dependency: install ``agent-ledger[analytics]``.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError("get_history() requires pandas; install agent-ledger[analytics]") from exc
        return pd.DataFrame([r.model_dump(mode="json") for r in self._history])

    def export_csv(self, path: str) -> str:
        self.get_history().to_csv(path, index=False)
        return path

    def limit_spending(self, max_cost: int | float | Decimal, *, account_arg: str = "agent"):
        """Rollback a decorated function when its selected agent spends over a cap."""
        cap = self._money(max_cost)
        if cap < 0:
            raise ValueError("max_cost must be non-negative")

        def decorator(fn):
            signature = __import__("inspect").signature(fn)

            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                bound = signature.bind_partial(*args, **kwargs)
                account = bound.arguments.get(account_arg)
                if account is None:
                    raise ValueError(f"decorated function must provide {account_arg!r}")
                account_id = getattr(account, "id", None) or getattr(account, "agent_id", None) or str(account)
                before = self.balance(account_id)
                with self.transaction():
                    result = fn(*args, **kwargs)
                    spent = before - self.balance(account_id)
                    if spent > cap:
                        raise PolicyBlockedError(f"spending limit exceeded: {spent} > {cap}", code="SPENDING_LIMIT")
                    return result

            return wrapped
        return decorator

    def action(self, name, *, policy=None, authority="system", tool=None):
        def deco(fn):
            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                start = time.perf_counter()
                try:
                    out = fn(*args, **kwargs); status = "SUCCESS"; err = None; return out
                except Exception as e:
                    out = None; status = "FAILED"; err = e; raise
                finally:
                    self.logger.log_event(agent_id=self.agent, agent_version=self.version, user_principal_id=authority, tool_name=tool or name, action_type=name, input_params={"args": args, "kwargs": kwargs}, output=out, duration_ms=(time.perf_counter()-start)*1000, status=status, error=err, policy_context={"policy_id": policy, "decision": "ALLOWED"} if policy else None)
            return wrapped
        return deco


ledger = Ledger()
