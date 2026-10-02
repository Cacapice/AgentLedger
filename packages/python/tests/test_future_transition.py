import tempfile
from pathlib import Path
import pytest
from agent_ledger.manifest import merkle_root,merkle_proof,verify_merkle_proof
from agent_ledger.bundle import export_bundle,verify_bundle
from agent_ledger.signing import generate_keypair
from agent_ledger.compat import capabilities,require_supported
from agent_ledger.reconcile import ReconcilerRegistry,ReconciliationResult
from agent_ledger.controls import Budget,CancellationToken
from agent_ledger.policy import PolicyEngine
from agent_ledger.policy_sim import simulate
from agent_ledger.slo import evidence_slo
from agent_ledger.causal import CausalContext

def test_merkle_inclusion_and_bundle():
    vals=[{'n':1},{'n':2},{'n':3}]; p=merkle_proof(vals,1)
    assert p['root']==merkle_root(vals) and verify_merkle_proof(vals[1],p)
    assert not verify_merkle_proof({'n':9},p)
    priv,pub=generate_keypair()
    with tempfile.TemporaryDirectory() as d:
        f=export_bundle(Path(d)/'run.alb',run_id='r1',events=vals,effects=[{'status':'COMMITTED'}],private_key=priv)
        assert verify_bundle(f,public_key=pub)['valid']

def test_transition_controls_and_simulation():
    assert 'evidence.portable-bundle' in capabilities()['features']
    with pytest.raises(ValueError): require_supported(bundle_version='future/99')
    reg=ReconcilerRegistry(); reg.register('mail',lambda e:ReconciliationResult('COMMITTED',{'message_id':'m1'},'mail'))
    assert reg.reconcile('mail',{'status':'UNKNOWN'}).status=='COMMITTED'
    b=Budget(max_cost=1,max_tokens=10); b.charge(cost=.2,tokens=3)
    with pytest.raises(RuntimeError): b.charge(cost=1)
    c=CancellationToken(); c.cancel('operator')
    with pytest.raises(RuntimeError): c.check()
    sim=simulate([{'amount':6,'policy_result':'ALLOW'}],PolicyEngine('p2',approval_over=5)); assert sim['changed']==1
    slo=evidence_slo(effects=[{'status':'COMMITTED'},{'status':'UNKNOWN'}],divergences=[1]); assert slo['unknown_rate']==.5
    assert CausalContext('r',trace_id='t').attributes()['agentledger.trace_id']=='t'
