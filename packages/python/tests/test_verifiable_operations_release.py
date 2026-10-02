
import pytest
from agent_ledger.manifest import build_run_manifest, sign_manifest
from agent_ledger.signing import generate_keypair
from agent_ledger.disclosure import disclose, verify_disclosure
from agent_ledger.providers import StripeReconciler, GitHubReconciler, HTTPIdempotencyReconciler
from agent_ledger.slo import scorecard, grouped_scorecards

def test_signed_selective_disclosure_tamper():
    priv,pub=generate_keypair()
    events=[{"i":1,"secret":"a"},{"i":2,"secret":"b"}]
    m=sign_manifest(build_run_manifest(run_id="r",events=events,effects=[]),priv)
    p=disclose(events,1,kind="event",signed_manifest=m)
    assert verify_disclosure(p,public_key=pub)
    p["value"]={"i":2,"secret":"tampered"}
    assert not verify_disclosure(p,public_key=pub)

class PI:
    def __init__(self,status): self.status=status
class PaymentIntent:
    status="succeeded"
    @classmethod
    def retrieve(cls,ref): return PI(cls.status)
class Stripe:
    PaymentIntent=PaymentIntent

def test_stripe_reconciler_readonly_mapping():
    r=StripeReconciler(Stripe())({"status":"UNKNOWN","provider_ref":"pi_1"})
    assert r.status=="COMMITTED"
    Stripe.PaymentIntent.status="processing"
    assert StripeReconciler(Stripe())({"status":"UNKNOWN","provider_ref":"pi_1"}).status=="UNKNOWN"

def test_github_and_http_reconcilers():
    gh=GitHubReconciler(lambda e:{"status":"merged","id":7})
    assert gh({"status":"UNKNOWN"}).status=="COMMITTED"
    http=HTTPIdempotencyReconciler(lambda k,e:{"status":"failed","id":"x"})
    assert http({"status":"UNKNOWN","idempotency_key":"k"}).status=="FAILED"

def test_scorecard_and_grouping():
    effects=[{"status":"COMMITTED","agent_id":"a","agent_version":"1","provider":"stripe"},
             {"status":"UNKNOWN","agent_id":"a","agent_version":"1","provider":"stripe"}]
    s=scorecard(effects=effects,objectives={"committed_rate":.5,"unknown_rate":.5,"failed_rate":0})
    assert s["healthy"] and s["score"]==1
    g=grouped_scorecards(effects)
    assert len(g)==1 and g[0]["group"]["provider"]=="stripe"

def test_otel_propagation_when_installed():
    pytest.importorskip("opentelemetry")
    from agent_ledger.otel import inject, extract
    carrier={}
    inject(carrier)
    assert isinstance(carrier,dict)
    assert extract(carrier) is not None
