"""Read-only provider-specific reconciliation for ambiguous effects.

Reconcilers MUST NOT retry or mutate the original effect. They query authoritative
provider state and return COMMITTED, FAILED, or UNKNOWN plus evidence.
"""
from __future__ import annotations
from typing import Any, Callable
from .reconcile import ReconciliationResult, ReconcilerRegistry

def _status(value:str|None, committed:set[str], failed:set[str])->str:
    v=(value or "").lower()
    if v in committed: return "COMMITTED"
    if v in failed: return "FAILED"
    return "UNKNOWN"

class StripeReconciler:
    provider="stripe"
    def __init__(self, client): self.client=client
    def __call__(self,effect:dict[str,Any])->ReconciliationResult:
        ref=effect.get("provider_ref") or effect.get("payment_intent_id")
        if not ref: return ReconciliationResult("UNKNOWN",{"reason":"missing provider reference"},self.provider)
        obj=self.client.PaymentIntent.retrieve(ref)
        raw=getattr(obj,"status",None) or (obj.get("status") if hasattr(obj,"get") else None)
        status=_status(raw,{"succeeded"},{"canceled","requires_payment_method"})
        return ReconciliationResult(status,{"provider_ref":ref,"provider_status":raw},self.provider)

class GitHubReconciler:
    provider="github"
    def __init__(self, lookup:Callable[[dict[str,Any]],dict[str,Any]|None]): self.lookup=lookup
    def __call__(self,effect:dict[str,Any])->ReconciliationResult:
        obj=self.lookup(effect)
        if not obj: return ReconciliationResult("UNKNOWN",{"reason":"operation not found"},self.provider)
        raw=str(obj.get("status",""))
        status=_status(raw,{"completed","success","merged","created"},{"failed","failure","cancelled","canceled"})
        return ReconciliationResult(status,{"provider_status":raw,"provider_ref":obj.get("id") or obj.get("url")},self.provider)

class HTTPIdempotencyReconciler:
    """Provider adapter for APIs exposing a read-only idempotency lookup endpoint."""
    provider="http-idempotency"
    def __init__(self, lookup:Callable[[str,dict[str,Any]],dict[str,Any]|None]): self.lookup=lookup
    def __call__(self,effect:dict[str,Any])->ReconciliationResult:
        key=effect.get("idempotency_key")
        if not key: return ReconciliationResult("UNKNOWN",{"reason":"missing idempotency key"},self.provider)
        obj=self.lookup(key,effect)
        if not obj: return ReconciliationResult("UNKNOWN",{"idempotency_key":key,"reason":"not found"},self.provider)
        raw=str(obj.get("status",""))
        status=_status(raw,{"committed","completed","success","succeeded"},{"failed","failure","rejected"})
        return ReconciliationResult(status,{"idempotency_key":key,"provider_status":raw,"provider_ref":obj.get("id")},self.provider)

def register_builtin_reconcilers(registry:ReconcilerRegistry, *, stripe=None, github_lookup=None, http_lookup=None):
    if stripe is not None: registry.register("stripe",StripeReconciler(stripe))
    if github_lookup is not None: registry.register("github",GitHubReconciler(github_lookup))
    if http_lookup is not None: registry.register("http-idempotency",HTTPIdempotencyReconciler(http_lookup))
    return registry
