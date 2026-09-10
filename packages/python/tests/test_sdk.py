import json
import tempfile
import unittest
from pathlib import Path
from agent_ledger import AuditLogger, JsonlSink, PolicyBlockedError, audit_tool, verify_chain


class AgentLedgerTests(unittest.TestCase):
    def test_chain_redaction_and_verify(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "audit.jsonl"
            logger = AuditLogger(sink=JsonlSink(path), chain_id="test")
            logger.log_event(agent_id="a", tool_name="x", input_params={"token": "abc", "q": 1})
            logger.log_event(agent_id="a", tool_name="y", input_params={"q": 2})
            self.assertTrue(verify_chain(path)["valid"])
            first = json.loads(path.read_text().splitlines()[0])
            self.assertEqual(first["input_parameters"]["token"], "[REDACTED]")

    def test_decorator_binds_positional_args(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "audit.jsonl"
            logger = AuditLogger(sink=JsonlSink(path), chain_id="test")
            @audit_tool("a", logger=logger)
            def f(recipient_account, amount=1):
                return amount
            self.assertEqual(f("ACC-1", 2), 2)
            event = json.loads(path.read_text().splitlines()[0])
            self.assertEqual(event["input_parameters"]["recipient_account"], "[REDACTED]")

    def test_policy_block(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "audit.jsonl"
            logger = AuditLogger(sink=JsonlSink(path), chain_id="test")
            @audit_tool("a", logger=logger)
            def f():
                raise PolicyBlockedError("no")
            with self.assertRaises(PolicyBlockedError):
                f()
            event = json.loads(path.read_text().splitlines()[0])
            self.assertEqual(event["execution_status"], "BLOCKED_BY_POLICY")


if __name__ == "__main__":
    unittest.main()
