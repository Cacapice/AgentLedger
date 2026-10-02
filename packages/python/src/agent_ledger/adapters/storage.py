"""Durable storage adapter contracts and production-oriented implementations."""
from __future__ import annotations
import json, sqlite3
from pathlib import Path
from typing import Any, Protocol

class StateStore(Protocol):
    def get(self, namespace:str, key:str)->dict[str,Any]|None: ...
    def put(self, namespace:str, key:str, value:dict[str,Any], *, expected_revision:int|None=None)->int: ...
    def delete(self, namespace:str, key:str)->None: ...

class SQLiteStateStore:
    """SQLite WAL state adapter with transactional optimistic revision checks."""
    def __init__(self,path:str|Path):
        self.path=str(path); self.db=sqlite3.connect(self.path,timeout=30,isolation_level=None)
        self.db.execute('PRAGMA journal_mode=WAL'); self.db.execute('PRAGMA synchronous=NORMAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS agentledger_state(namespace TEXT NOT NULL,key TEXT NOT NULL,value TEXT NOT NULL,revision INTEGER NOT NULL,PRIMARY KEY(namespace,key))')
    def get(self,namespace,key):
        row=self.db.execute('SELECT value,revision FROM agentledger_state WHERE namespace=? AND key=?',(namespace,key)).fetchone()
        return None if not row else {**json.loads(row[0]),'_revision':row[1]}
    def put(self,namespace,key,value,*,expected_revision=None):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            cur=self.db.execute('SELECT revision FROM agentledger_state WHERE namespace=? AND key=?',(namespace,key)).fetchone(); rev=cur[0] if cur else 0
            if expected_revision is not None and rev!=expected_revision: raise RuntimeError(f'stale revision: expected {expected_revision}, found {rev}')
            nxt=rev+1; payload=json.dumps(value,separators=(',',':'),sort_keys=True)
            self.db.execute('INSERT INTO agentledger_state(namespace,key,value,revision) VALUES(?,?,?,?) ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value,revision=excluded.revision',(namespace,key,payload,nxt)); self.db.execute('COMMIT'); return nxt
        except Exception: self.db.execute('ROLLBACK'); raise
    def delete(self,namespace,key): self.db.execute('DELETE FROM agentledger_state WHERE namespace=? AND key=?',(namespace,key))
    def close(self): self.db.close()

class DBAPIStateStore:
    """Transactional DB-API StateStore for Postgres/MySQL-compatible drivers."""
    dialect='generic'
    def __init__(self,connect,*,placeholder='%s'): self.connect=connect; self.p=placeholder; self.db=connect()
    def initialize(self):
        c=self.db.cursor(); c.execute('CREATE TABLE IF NOT EXISTS agentledger_state(namespace VARCHAR(255) NOT NULL,key_name VARCHAR(512) NOT NULL,value_json TEXT NOT NULL,revision BIGINT NOT NULL,PRIMARY KEY(namespace,key_name))'); self.db.commit()
    def get(self,namespace,key):
        c=self.db.cursor(); c.execute(f'SELECT value_json,revision FROM agentledger_state WHERE namespace={self.p} AND key_name={self.p}',(namespace,key)); row=c.fetchone(); return None if not row else {**json.loads(row[0]),'_revision':int(row[1])}
    def put(self,namespace,key,value,*,expected_revision=None):
        c=self.db.cursor()
        try:
            c.execute(f'SELECT revision FROM agentledger_state WHERE namespace={self.p} AND key_name={self.p} FOR UPDATE',(namespace,key)); row=c.fetchone(); rev=int(row[0]) if row else 0
            if expected_revision is not None and rev!=expected_revision: raise RuntimeError(f'stale revision: expected {expected_revision}, found {rev}')
            nxt=rev+1; payload=json.dumps(value,separators=(',',':'),sort_keys=True)
            if row: c.execute(f'UPDATE agentledger_state SET value_json={self.p},revision={self.p} WHERE namespace={self.p} AND key_name={self.p}',(payload,nxt,namespace,key))
            else: c.execute(f'INSERT INTO agentledger_state(namespace,key_name,value_json,revision) VALUES({self.p},{self.p},{self.p},{self.p})',(namespace,key,payload,nxt))
            self.db.commit(); return nxt
        except Exception: self.db.rollback(); raise
    def delete(self,namespace,key):
        c=self.db.cursor(); c.execute(f'DELETE FROM agentledger_state WHERE namespace={self.p} AND key_name={self.p}',(namespace,key)); self.db.commit()
    def close(self): self.db.close()

class PostgresStateStore(DBAPIStateStore):
    dialect='postgres'
    @classmethod
    def from_dsn(cls,dsn):
        import psycopg  # type: ignore[import-not-found]
        return cls(lambda: psycopg.connect(dsn))

class MySQLStateStore(DBAPIStateStore):
    dialect='mysql'
    @classmethod
    def from_url(cls,url):
        from urllib.parse import urlparse
        import pymysql  # type: ignore[import-untyped]
        u=urlparse(url)
        return cls(lambda:pymysql.connect(host=u.hostname,port=u.port or 3306,user=u.username,password=u.password,database=u.path.lstrip('/'),autocommit=False))
