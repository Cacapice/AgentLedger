from __future__ import annotations
import base64, hashlib
from typing import Any, TYPE_CHECKING
from .jcs import canonicalize_bytes

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey as Ed25519PrivateKeyType
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey as Ed25519PublicKeyType

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError:
    serialization = None  # type: ignore[assignment]
    Ed25519PrivateKey = None  # type: ignore[assignment,misc]
    Ed25519PublicKey = None  # type: ignore[assignment,misc]

class SigningUnavailableError(RuntimeError): pass

def _require() -> None:
    if Ed25519PrivateKey is None or Ed25519PublicKey is None or serialization is None:
        raise SigningUnavailableError("install agent-ledger[crypto] to use Ed25519 signing")

def generate_keypair():
    _require()
    assert Ed25519PrivateKey is not None and serialization is not None
    private=Ed25519PrivateKey.generate(); public=private.public_key()
    return private.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()), public.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)

def key_fingerprint(public_key:bytes)->str: return hashlib.sha256(public_key).hexdigest()

def sign_evidence(value:Any,private_key:bytes)->dict[str,str]:
    _require()
    assert Ed25519PrivateKey is not None and serialization is not None
    key=Ed25519PrivateKey.from_private_bytes(private_key); payload=canonicalize_bytes(value); pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    return {'algorithm':'Ed25519','canonicalization':'RFC8785','key_fingerprint':key_fingerprint(pub),'signature':base64.b64encode(key.sign(payload)).decode()}

def verify_evidence(value:Any,signature:dict[str,str],public_key:bytes)->bool:
    _require()
    assert Ed25519PublicKey is not None
    if signature.get('key_fingerprint') != key_fingerprint(public_key): return False
    try: Ed25519PublicKey.from_public_bytes(public_key).verify(base64.b64decode(signature['signature']),canonicalize_bytes(value)); return True
    except Exception: return False
