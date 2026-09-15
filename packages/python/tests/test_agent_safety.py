from decimal import Decimal
import tempfile

import pytest

from agent_ledger import IdempotencyConflictError, InsufficientFundsError, Ledger, PolicyBlockedError
from agent_ledger.core import AuditLogger, JsonlSink


def make_ledger(tmp_path, **kwargs):
    return Ledger(logger=AuditLogger(sink=JsonlSink(tmp_path / 'audit.jsonl')), **kwargs)


def test_transaction_rolls_back(tmp_path):
    ledger = make_ledger(tmp_path, balances={'A': 50, 'B': 0})
    with pytest.raises(RuntimeError):
        with ledger.transaction():
            ledger.transfer('A', 'B', 20)
            raise RuntimeError('crash')
    assert ledger.balance('A') == Decimal('50')
    assert ledger.balance('B') == Decimal('0')


def test_strict_mode_blocks_overdraft(tmp_path):
    ledger = make_ledger(tmp_path, balances={'A': 5})
    with pytest.raises(InsufficientFundsError):
        ledger.debit('A', 10)
    assert ledger.balance('A') == Decimal('5')


def test_idempotency_prevents_double_debit(tmp_path):
    ledger = make_ledger(tmp_path, balances={'A': 20})
    first = ledger.debit('A', 5, idempotency_key='purchase_123')
    second = ledger.debit('A', 5, idempotency_key='purchase_123')
    assert first == second
    assert ledger.balance('A') == Decimal('15')
    with pytest.raises(IdempotencyConflictError):
        ledger.debit('A', 6, idempotency_key='purchase_123')


def test_transfer_and_dataframe_export(tmp_path):
    pd = pytest.importorskip('pandas')
    ledger = make_ledger(tmp_path, balances={'A': 100})
    ledger.transfer('A', 'B', 25, idempotency_key='t1')
    df = ledger.get_history()
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]['event'] == 'transfer'


def test_spending_decorator_rolls_back(tmp_path):
    ledger = make_ledger(tmp_path, balances={'bot_1': 20})

    @ledger.limit_spending(5)
    def task(agent):
        ledger.debit(agent, 6)

    with pytest.raises(PolicyBlockedError):
        task('bot_1')
    assert ledger.balance('bot_1') == Decimal('20')
