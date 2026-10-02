import pytest
from agent_ledger import DurableRunStore, EffectLedger, EffectConflictError, EffectTransitionError, StaleLeaseError, generate_keypair, sign_evidence, verify_evidence

def test_durable_run_fencing_and_checkpoint(tmp_path):
    store=DurableRunStore(tmp_path/'runs.json'); run=store.create('r1'); leased=store.acquire(run.run_id,'worker-a')
    state=store.checkpoint('r1',leased.lease_token,step='tool',checkpoint={'cursor':3}); assert state.checkpoint=={'cursor':3}
    newer=store.acquire('r1','worker-b')
    with pytest.raises(StaleLeaseError): store.checkpoint('r1',leased.lease_token,step='stale',checkpoint={})
    assert store.finish('r1',newer.lease_token).status=='SUCCEEDED'

def test_effect_unknown_and_reconciliation(tmp_path):
    ledger=EffectLedger(tmp_path/'effects.json'); e=ledger.propose(run_id='r',tool_name='payments',idempotency_key='k',request={'amount':5})
    ledger.transition(e.effect_id,'AUTHORIZED'); ledger.transition(e.effect_id,'ATTEMPTED'); unknown=ledger.transition(e.effect_id,'UNKNOWN')
    assert unknown.status=='UNKNOWN'; assert ledger.transition(e.effect_id,'COMMITTED',response={'id':'p1'}).status=='COMMITTED'
    with pytest.raises(EffectTransitionError): ledger.transition(e.effect_id,'FAILED')
    with pytest.raises(EffectConflictError): ledger.propose(run_id='r',tool_name='payments',idempotency_key='k',request={'amount':6})

def test_ed25519_evidence_signature():
    private,public=generate_keypair(); event={'event_id':'e1','value':3}; sig=sign_evidence(event,private)
    assert verify_evidence(event,sig,public); assert not verify_evidence({'event_id':'e1','value':4},sig,public)
