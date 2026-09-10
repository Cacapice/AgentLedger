from __future__ import annotations
import re
import time
import urllib.error
import urllib.request
from html import unescape
from typing import Any, Mapping

from .core import AuditLogger

DEFAULT_SCUDERIA_URL = "https://www.scuderialifestyle.org/maxima/"


def _extract(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return unescape(match.group(1).strip()) if match else None


def observe_scuderia_indexability(
    url: str = DEFAULT_SCUDERIA_URL,
    *,
    logger: AuditLogger | None = None,
    timeout: float = 15.0,
    authority: str = "scuderia-operator",
) -> Mapping[str, Any]:
    """Run one real, read-only Scuderia SEO agent observation and ledger it.

    The observation performs a live HTTP GET against a Scuderia-owned page,
    checks indexability signals, and records the consequential agent action.
    It makes no mutation to the site or Search Console.
    """
    logger = logger or AuditLogger.from_env()
    started = time.perf_counter()
    status = "SUCCESS"
    error: BaseException | None = None
    result: dict[str, Any] = {}
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Scuderia-AgentLedger-Dogfood/1.0 (+read-only indexability observation)"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(750_000).decode("utf-8", errors="replace")
            http_status = int(getattr(response, "status", 200))
            final_url = response.geturl()
        canonical = _extract(r'<link[^>]+rel=["\\\']canonical["\\\'][^>]+href=["\\\']([^"\\\']+)', body)
        if canonical is None:
            canonical = _extract(r'<link[^>]+href=["\\\']([^"\\\']+)["\\\'][^>]+rel=["\\\']canonical["\\\']', body)
        robots = _extract(r'<meta[^>]+name=["\\\']robots["\\\'][^>]+content=["\\\']([^"\\\']+)', body) or ""
        title = _extract(r'<title[^>]*>(.*?)</title>', body)
        result = {
            "http_status": http_status,
            "final_url": final_url,
            "canonical": canonical,
            "title": title,
            "robots": robots,
            "indexable_http": 200 <= http_status < 300,
            "noindex_present": "noindex" in robots.lower(),
            "canonical_present": bool(canonical),
            "observation": "read-only",
        }
    except BaseException as exc:
        status = "FAILED"
        error = exc
        result = {"error_type": type(exc).__name__, "message": str(exc)[:500]}
    event = logger.log_event(
        agent_id="scuderia-indexability-agent",
        agent_version="1.0.0",
        user_principal_id=authority,
        principal_type="HUMAN_OPERATOR",
        tool_name="http.fetch",
        action_type="seo.indexability.observe",
        input_params={"url": url, "mode": "read-only"},
        output=result,
        duration_ms=(time.perf_counter() - started) * 1000,
        status=status,
        policy_context={
            "policy_id": "scuderia-public-observation-v1",
            "policy_version": "1",
            "decision": "ALLOWED",
            "mutation_allowed": False,
        },
        resource={"type": "web_page", "url": url, "owner": "Scuderia Lifestyle"},
    )
    return {"observation": result, "event": event, "hosted_receipt": event.get("hosted_receipt")}
