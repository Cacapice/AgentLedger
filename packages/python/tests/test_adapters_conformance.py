import json
from pathlib import Path
from agent_ledger.adapters import SQLiteStateStore,LocalBlobStore
from agent_ledger.effects import _ALLOWED

def test_sqlite_state_and_blob(tmp_path):
 s=SQLiteStateStore(tmp_path/'state.db'); assert s.put('run','1',{'status':'PENDING'})==1; assert s.get('run','1')['status']=='PENDING'; assert s.put('run','1',{'status':'RUNNING'},expected_revision=1)==2
 b=LocalBlobStore(tmp_path/'blobs'); ref=b.put(b'evidence'); assert b.get(ref)==b'evidence'
def test_shared_semantics():
 f=json.loads((Path(__file__).parents[3]/'contracts/conformance/runtime_semantics.v1.json').read_text())
 for c in f['cases']:
  ok=all(b in _ALLOWED.get(a,set()) for a,b in zip(c['transitions'],c['transitions'][1:])); assert ok is c['valid'],c['name']

def test_distributed_lease_fencing_and_heartbeat(tmp_path):
 from datetime import datetime,timezone,timedelta
 from agent_ledger.leases import DistributedLeaseManager,LeaseBusy,LeaseLost
 s=SQLiteStateStore(tmp_path/'lease.db'); m=DistributedLeaseManager(s,ttl_seconds=10); t=datetime(2026,1,1,tzinfo=timezone.utc)
 a=m.acquire('run:1','worker-a',now=t); assert a.fence==1
 try: m.acquire('run:1','worker-b',now=t+timedelta(seconds=1)); assert False
 except LeaseBusy: pass
 a2=m.heartbeat(a,now=t+timedelta(seconds=2)); assert a2.fence==1
 b=m.acquire('run:1','worker-b',now=t+timedelta(seconds=20)); assert b.fence==2
 try: m.heartbeat(a2,now=t+timedelta(seconds=21)); assert False
 except LeaseLost: pass

def test_adapter_certification_and_failure_injection(tmp_path):
 from agent_ledger.certification import certify_state_store,certify_blob_store,FaultInjectingStateStore,InjectedFailure
 sr=certify_state_store(lambda:SQLiteStateStore(tmp_path/'cert.db'),'sqlite'); assert sr.certified
 br=certify_blob_store(lambda:LocalBlobStore(tmp_path/'cert-blobs'),'local'); assert br.certified
 f=FaultInjectingStateStore(SQLiteStateStore(tmp_path/'fault.db'),fail_put_calls={1})
 try: f.put('n','k',{'x':1}); assert False
 except InjectedFailure: pass
 assert f.put('n','k',{'x':1})==1
