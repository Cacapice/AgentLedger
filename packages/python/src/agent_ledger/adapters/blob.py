from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Protocol
class BlobStore(Protocol):
    def put(self,data:bytes)->str: ...
    def get(self,ref:str)->bytes: ...
class LocalBlobStore:
    def __init__(self,root): self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def put(self,data):
        h=hashlib.sha256(data).hexdigest(); p=self.root/h[:2]/h; p.parent.mkdir(exist_ok=True); p.write_bytes(data); return f'sha256:{h}'
    def get(self,ref): h=ref.removeprefix('sha256:'); return (self.root/h[:2]/h).read_bytes()
class S3BlobStore:
    """S3/MinIO adapter; accepts a boto3-compatible client to keep core dependency-free."""
    def __init__(self,client,bucket,prefix='agentledger/'): self.client=client; self.bucket=bucket; self.prefix=prefix
    def put(self,data):
        h=hashlib.sha256(data).hexdigest(); key=f'{self.prefix}{h}'; self.client.put_object(Bucket=self.bucket,Key=key,Body=data); return f's3://{self.bucket}/{key}#sha256={h}'
    def get(self,ref):
        path=ref.split('#',1)[0].removeprefix(f's3://{self.bucket}/'); return self.client.get_object(Bucket=self.bucket,Key=path)['Body'].read()
