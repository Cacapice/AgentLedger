import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_ledger.core import AuditLogger, IngestionClient, JsonlSink, verify_chain
from agent_ledger.scuderia import observe_scuderia_indexability


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'<html><head><title>Maxima</title><link rel="canonical" href="https://www.scuderialifestyle.org/maxima/"><meta name="robots" content="index,follow"></head><body>ok</body></html>'
        self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *args): pass


class StubIngestion:
    def send(self, event):
        return {'accepted': True, 'receipt_id': 'alr_0123456789abcdef0123456789abcdef', 'event_hash': event['event_hash']}


class DogfoodTests(unittest.TestCase):
    def test_real_http_observation_gets_hosted_receipt_without_mutating_local_chain(self):
        server = HTTPServer(('127.0.0.1', 0), Handler)
        t = threading.Thread(target=server.serve_forever, daemon=True); t.start()
        try:
            with TemporaryDirectory() as td:
                path = Path(td) / 'events.jsonl'
                logger = AuditLogger(sink=JsonlSink(path), ingestion=StubIngestion())
                run = observe_scuderia_indexability(f'http://127.0.0.1:{server.server_port}/maxima/', logger=logger)
                self.assertEqual(run['hosted_receipt']['receipt_id'], 'alr_0123456789abcdef0123456789abcdef')
                self.assertTrue(run['observation']['canonical_present'])
                self.assertFalse(run['observation']['noindex_present'])
                self.assertTrue(verify_chain(path)['valid'])
                persisted = json.loads(path.read_text().strip())
                self.assertNotIn('hosted_receipt', persisted)
        finally:
            server.shutdown(); server.server_close()
