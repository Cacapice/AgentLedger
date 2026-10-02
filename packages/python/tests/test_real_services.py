"""Opt-in real-service integration tests used by CI service containers."""
import os, pytest
from agent_ledger.certification import certify_state_store,certify_blob_store

def test_postgres_real():
 dsn=os.getenv('AGENTLEDGER_POSTGRES_DSN')
 if not dsn: pytest.skip('AGENTLEDGER_POSTGRES_DSN not set')
 pytest.importorskip('psycopg')
 from agent_ledger.adapters import PostgresStateStore
 s=PostgresStateStore.from_dsn(dsn); s.initialize(); assert certify_state_store(lambda:s,'postgres').certified

def test_mysql_real():
 url=os.getenv('AGENTLEDGER_MYSQL_URL')
 if not url: pytest.skip('AGENTLEDGER_MYSQL_URL not set')
 pytest.importorskip('pymysql')
 from agent_ledger.adapters import MySQLStateStore
 s=MySQLStateStore.from_url(url); s.initialize(); assert certify_state_store(lambda:s,'mysql').certified

def test_minio_real():
 endpoint=os.getenv('AGENTLEDGER_S3_ENDPOINT')
 if not endpoint: pytest.skip('AGENTLEDGER_S3_ENDPOINT not set')
 boto3=pytest.importorskip('boto3'); bucket=os.getenv('AGENTLEDGER_S3_BUCKET','agentledger-test')
 c=boto3.client('s3',endpoint_url=endpoint,aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID','minioadmin'),aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY','minioadmin'),region_name='us-east-1')
 try:c.create_bucket(Bucket=bucket)
 except Exception:pass
 from agent_ledger.adapters import S3BlobStore
 assert certify_blob_store(lambda:S3BlobStore(c,bucket,prefix='ci/'),'minio').certified
