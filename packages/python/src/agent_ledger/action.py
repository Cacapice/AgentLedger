from __future__ import annotations
import functools, time
from contextlib import contextmanager
from .core import AuditLogger

class Ledger:
    def __init__(self, logger=None, agent="agent", version=None):
        self.logger=logger or AuditLogger.from_env(); self.agent=agent; self.version=version
    def action(self, name, *, policy=None, authority="system", tool=None):
        def deco(fn):
            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                start=time.perf_counter()
                try:
                    out=fn(*args, **kwargs); status="SUCCESS"; err=None; return out
                except Exception as e:
                    out=None; status="FAILED"; err=e; raise
                finally:
                    self.logger.log_event(agent_id=self.agent,agent_version=self.version,user_principal_id=authority,tool_name=tool or name,action_type=name,input_params={"args":args,"kwargs":kwargs},output=out,duration_ms=(time.perf_counter()-start)*1000,status=status,error=err,policy_context={"policy_id":policy,"decision":"ALLOWED"} if policy else None)
            return wrapped
        return deco

ledger=Ledger()
