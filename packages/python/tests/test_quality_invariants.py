
import random, copy
import pytest
from agent_ledger.jcs import canonicalize_bytes
from agent_ledger.manifest import merkle_proof, verify_merkle_proof, merkle_root, build_run_manifest, sign_manifest, verify_manifest
from agent_ledger.signing import generate_keypair
from agent_ledger.disclosure import disclose, verify_disclosure

def test_canonicalization_deterministic_for_nested_objects():
    rng=random.Random(7)
    for _ in range(250):
        pairs=[("k"+str(i), rng.randint(-100000,100000)) for i in range(rng.randint(1,12))]
        a=dict(pairs); b=dict(reversed(pairs))
        assert canonicalize_bytes(a)==canonicalize_bytes(b)

@pytest.mark.parametrize("bad",[float("nan"),float("inf"),float("-inf")])
def test_canonicalization_rejects_nonfinite(bad):
    with pytest.raises((ValueError,TypeError)): canonicalize_bytes({"x":bad})

def test_merkle_proofs_all_positions_and_tamper():
    for n in range(1,33):
        vals=[{"i":i,"v":f"x{i}"} for i in range(n)]
        root=merkle_root(vals)
        for i,v in enumerate(vals):
            p=merkle_proof(vals,i)
            assert p["root"]==root and verify_merkle_proof(v,p)
            assert not verify_merkle_proof({**v,"v":"tampered"},p)

def test_signature_and_disclosure_bind_manifest():
    priv,pub=generate_keypair(); vals=[{"i":0},{"i":1}]
    m=sign_manifest(build_run_manifest(run_id="r",events=vals,effects=[]),priv)
    assert verify_manifest(m,pub)
    packet=disclose(vals,0,kind="event",signed_manifest=m)
    assert verify_disclosure(packet,public_key=pub)
    broken=copy.deepcopy(packet); broken["manifest"]["run_id"]="other"
    assert not verify_disclosure(broken,public_key=pub)
