"""Distributed lease/heartbeat primitives backed by any revisioned StateStore."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import secrets
from typing import Any

class LeaseBusy(RuntimeError): pass
class LeaseLost(RuntimeError): pass

def _now(): return datetime.now(timezone.utc)
def _iso(dt): return dt.isoformat().replace('+00:00','Z')
def _parse(s): return datetime.fromisoformat(s.replace('Z','+00:00'))

@dataclass(frozen=True)
class Lease:
    resource: str
    owner: str
    token: str
    fence: int
    expires_at: str
    revision: int

class DistributedLeaseManager:
    """TTL lease with monotonically increasing fencing tokens and heartbeats.

    Correctness relies on the StateStore's expected_revision compare-and-swap.
    Downstream resources should persist/check ``fence`` where stale writers matter.
    """
    def __init__(self, store:Any, *, namespace='leases', ttl_seconds=30):
        self.store=store; self.namespace=namespace; self.ttl_seconds=ttl_seconds
    def acquire(self, resource:str, owner:str, *, now=None)->Lease:
        now=now or _now(); row=self.store.get(self.namespace,resource)
        if row and _parse(row['expires_at']) > now and row['owner'] != owner:
            raise LeaseBusy(f'{resource} held by {row["owner"]}')
        rev=0 if row is None else row['_revision']; fence=1 if row is None else int(row.get('fence',0))+1
        token=secrets.token_hex(16); expires=_iso(now+timedelta(seconds=self.ttl_seconds))
        payload={'resource':resource,'owner':owner,'token':token,'fence':fence,'expires_at':expires}
        try: newrev=self.store.put(self.namespace,resource,payload,expected_revision=rev)
        except Exception as e: raise LeaseBusy(f'lease raced for {resource}') from e
        return Lease(resource,owner,token,fence,expires,newrev)
    def heartbeat(self, lease:Lease, *, now=None)->Lease:
        now=now or _now(); row=self.store.get(self.namespace,lease.resource)
        if not row or row.get('token')!=lease.token or row.get('owner')!=lease.owner or int(row.get('fence',0))!=lease.fence:
            raise LeaseLost(lease.resource)
        if _parse(row['expires_at']) <= now: raise LeaseLost(f'{lease.resource} expired')
        payload={k:row[k] for k in ('resource','owner','token','fence')}; payload['expires_at']=_iso(now+timedelta(seconds=self.ttl_seconds))
        try: rev=self.store.put(self.namespace,lease.resource,payload,expected_revision=row['_revision'])
        except Exception as e: raise LeaseLost(f'{lease.resource} heartbeat lost race') from e
        return Lease(lease.resource,lease.owner,lease.token,lease.fence,payload['expires_at'],rev)
    def release(self, lease:Lease):
        row=self.store.get(self.namespace,lease.resource)
        if not row or row.get('token')!=lease.token: raise LeaseLost(lease.resource)
        self.store.delete(self.namespace,lease.resource)
