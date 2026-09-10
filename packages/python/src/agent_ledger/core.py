from __future__ import annotations

import asyncio
import functools
import hashlib
import inspect
import json
import os
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional

SCHEMA_VERSION = "1.0.0"
META_KEYS = {
    "_user_principal_id", "_principal_type", "_session_id", "_trace_id",
    "_model_context", "_policy_context", "_resource"
}
DEFAULT_SENSITIVE_KEYS = {
    "authorization", "cookie", "set_cookie", "password", "passwd", "secret",
    "token", "api_key", "apikey", "private_key", "access_token", "refresh_token",
    "client_secret", "recipient_account", "account_number", "ssn", "social_security_number"
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    return repr(value)


def canonical_json(value: Any) -> str:
    return json.dumps(json_safe(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class PolicyBlockedError(RuntimeError):
    def __init__(self, message: str, code: str = "POLICY_BLOCK"):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RedactionResult:
    value: Any
    fields: tuple[str, ...]


class Redactor:
    def __init__(self, sensitive_keys: Optional[Iterable[str]] = None, max_string: int = 2000):
        self.sensitive_keys = {x.lower().replace("-", "_") for x in (sensitive_keys or DEFAULT_SENSITIVE_KEYS)}
        self.max_string = max_string

    def redact(self, value: Any, path: str = "$") -> RedactionResult:
        fields: list[str] = []

        def walk(v: Any, p: str, key: Optional[str] = None) -> Any:
            normalized = (key or "").lower().replace("-", "_")
            if key is not None and (
                normalized in self.sensitive_keys
                or any(tok in normalized for tok in ("password", "secret", "token", "private_key"))
            ):
                fields.append(p)
                return "[REDACTED]"
            if isinstance(v, Mapping):
                return {str(k): walk(val, f"{p}.{k}", str(k)) for k, val in v.items()}
            if isinstance(v, (list, tuple, set)):
                return [walk(val, f"{p}[{i}]") for i, val in enumerate(v)]
            if isinstance(v, str) and len(v) > self.max_string:
                fields.append(p)
                return v[: self.max_string] + "…[TRUNCATED]"
            return json_safe(v)

        return RedactionResult(walk(value, path), tuple(sorted(set(fields))))


class JsonlSink:
    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: Mapping[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(canonical_json(event) + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                # Some serverless/container filesystems do not expose durable fsync.
                pass


class IngestionClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> Optional["IngestionClient"]:
        url = os.getenv("AGENT_LEDGER_URL")
        key = os.getenv("AGENT_LEDGER_API_KEY")
        return cls(url, key) if url and key else None

    def send(self, event: Mapping[str, Any]) -> Mapping[str, Any]:
        body = canonical_json(event).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/events",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Agent Ledger ingestion failed ({exc.code}): {detail}") from exc


class AuditLogger:
    def __init__(
        self,
        sink: Optional[JsonlSink] = None,
        chain_id: Optional[str] = None,
        redactor: Optional[Redactor] = None,
        ingestion: Optional[IngestionClient] = None,
    ):
        self.sink = sink or JsonlSink(os.getenv("AGENT_LEDGER_LOG", "./audit_events.jsonl"))
        self.chain_id = chain_id or os.getenv("AGENT_LEDGER_CHAIN_ID") or str(uuid.uuid4())
        self.redactor = redactor or Redactor()
        self.ingestion = ingestion
        self._last_hash: Optional[str] = None
        self._sequence = 0
        self._lock = threading.RLock()

    @classmethod
    def from_env(cls) -> "AuditLogger":
        return cls(ingestion=IngestionClient.from_env())

    @staticmethod
    def _summary(output: Any) -> Mapping[str, Any]:
        safe = json_safe(output)
        if isinstance(safe, Mapping):
            return {"type": "object", "keys": sorted(map(str, safe.keys()))[:50], "result_preview": canonical_json(safe)[:1000]}
        if isinstance(safe, list):
            return {"type": "array", "length": len(safe), "result_preview": canonical_json(safe[:10])[:1000]}
        return {"type": type(output).__name__, "result_preview": str(safe)[:1000]}

    def log_event(self, *, agent_id: str, user_principal_id: str = "system", tool_name: str,
                  action_type: str = "TOOL_CALL", input_params: Mapping[str, Any] | None = None,
                  output: Any = None, duration_ms: float = 0, status: str = "SUCCESS",
                  error: Optional[BaseException] = None, session_id: Optional[str] = None,
                  trace_id: Optional[str] = None, principal_type: str = "SYSTEM",
                  agent_version: Optional[str] = None, model_info: Optional[Mapping[str, Any]] = None,
                  policy_context: Optional[Mapping[str, Any]] = None,
                  resource: Optional[Mapping[str, Any]] = None) -> Mapping[str, Any]:
        red_in = self.redactor.redact(input_params or {})
        red_out = self.redactor.redact(self._summary(output) if output is not None else {})
        timestamp = utc_now()
        payload_hash = sha256_hex({
            "input_parameters": red_in.value,
            "output_summary": red_out.value,
            "timestamp": timestamp,
            "execution_status": status,
        })
        with self._lock:
            self._sequence += 1
            event = {
                "schema_version": SCHEMA_VERSION,
                "event_id": str(uuid.uuid4()),
                "chain_id": self.chain_id,
                "sequence_number": self._sequence,
                "timestamp": timestamp,
                "agent_id": agent_id,
                "agent_version": agent_version,
                "actor": {"principal_id": user_principal_id, "principal_type": principal_type},
                "session_id": session_id,
                "trace_id": trace_id,
                "action_type": action_type,
                "tool_name": tool_name,
                "resource": json_safe(resource) if resource else None,
                "model_context": self.redactor.redact(model_info or {}).value if model_info else None,
                "policy_context": json_safe(policy_context) if policy_context else None,
                "input_parameters": red_in.value,
                "output_summary": red_out.value,
                "redaction": {"applied": bool(red_in.fields or red_out.fields), "fields": sorted(set(red_in.fields + red_out.fields))},
                "execution_duration_ms": round(max(0.0, duration_ms), 3),
                "execution_status": status,
                "error": None if error is None else {"type": type(error).__name__, "code": getattr(error, "code", None), "message": str(error)[:2000]},
                "payload_hash": payload_hash,
                "prev_event_hash": self._last_hash,
                "integrity": {"algorithm": "SHA-256", "canonicalization": "sorted-json-v1"},
            }
            event["event_hash"] = sha256_hex(event)
            self.sink.write(event)
            self._last_hash = event["event_hash"]
        if self.ingestion:
            # The persisted local event remains exactly the hashed event above.
            # Hosted acknowledgement/receipt metadata is attached only to the
            # in-memory return value so local chain verification is unaffected.
            event["hosted_receipt"] = self.ingestion.send(event)
        return event


def verify_chain(path: str | os.PathLike[str]) -> Mapping[str, Any]:
    previous: Optional[str] = None
    chain_id: Optional[str] = None
    count = 0
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            event = json.loads(line)
            count += 1
            chain_id = chain_id or event.get("chain_id")
            if event.get("chain_id") != chain_id:
                return {"valid": False, "line": line_number, "reason": "chain_id changed", "events": count}
            if event.get("sequence_number") != count:
                return {"valid": False, "line": line_number, "reason": "sequence_number mismatch", "events": count}
            if event.get("prev_event_hash") != previous:
                return {"valid": False, "line": line_number, "reason": "prev_event_hash mismatch", "events": count}
            expected = sha256_hex({k: v for k, v in event.items() if k != "event_hash"})
            if event.get("event_hash") != expected:
                return {"valid": False, "line": line_number, "reason": "event_hash mismatch", "events": count}
            previous = event["event_hash"]
    return {"valid": True, "events": count, "chain_id": chain_id, "head_hash": previous}


def audit_tool(agent_id: str, tool_name: Optional[str] = None, action_type: str = "TOOL_CALL", *,
               agent_version: Optional[str] = None, logger: Optional[AuditLogger] = None):
    def decorator(func: Callable):
        resolved = tool_name or func.__name__
        signature = inspect.signature(func)

        def split(kwargs: MutableMapping[str, Any]):
            meta = {key: kwargs.pop(key, None) for key in META_KEYS}
            return meta

        def params(args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> Mapping[str, Any]:
            bound = signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            return dict(bound.arguments)

        def emit(log: AuditLogger, meta: Mapping[str, Any], inputs: Mapping[str, Any], output: Any,
                 elapsed: float, status: str, error: Optional[BaseException] = None):
            return log.log_event(
                agent_id=agent_id, agent_version=agent_version,
                user_principal_id=meta.get("_user_principal_id") or "system",
                principal_type=meta.get("_principal_type") or "SYSTEM",
                session_id=meta.get("_session_id"), trace_id=meta.get("_trace_id"),
                model_info=meta.get("_model_context"), policy_context=meta.get("_policy_context"),
                resource=meta.get("_resource"), tool_name=resolved, action_type=action_type,
                input_params=inputs, output=output, duration_ms=elapsed, status=status, error=error,
            )

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                meta = split(kwargs)
                inputs = params(args, kwargs)
                log = logger or AuditLogger.from_env()
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    emit(log, meta, inputs, result, (time.perf_counter() - start) * 1000, "SUCCESS")
                    return result
                except PolicyBlockedError as exc:
                    emit(log, meta, inputs, None, (time.perf_counter() - start) * 1000, "BLOCKED_BY_POLICY", exc)
                    raise
                except asyncio.CancelledError as exc:
                    emit(log, meta, inputs, None, (time.perf_counter() - start) * 1000, "CANCELLED", exc)
                    raise
                except Exception as exc:
                    emit(log, meta, inputs, None, (time.perf_counter() - start) * 1000, "FAILED", exc)
                    raise
            return async_wrapper

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            meta = split(kwargs)
            inputs = params(args, kwargs)
            log = logger or AuditLogger.from_env()
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                emit(log, meta, inputs, result, (time.perf_counter() - start) * 1000, "SUCCESS")
                return result
            except PolicyBlockedError as exc:
                emit(log, meta, inputs, None, (time.perf_counter() - start) * 1000, "BLOCKED_BY_POLICY", exc)
                raise
            except Exception as exc:
                emit(log, meta, inputs, None, (time.perf_counter() - start) * 1000, "FAILED", exc)
                raise
        return wrapper
    return decorator
