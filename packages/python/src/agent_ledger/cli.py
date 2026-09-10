from __future__ import annotations
import argparse, json, os, sys, urllib.error, urllib.request
from pathlib import Path
from .core import verify_chain
from .scuderia import DEFAULT_SCUDERIA_URL, observe_scuderia_indexability


def remote_get(base, key, path):
    req = urllib.request.Request(base.rstrip('/') + path, headers={'Authorization': f'Bearer {key}'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _load_dotenv(path='.env.agent-ledger'):
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())


def _receipt_summary(result):
    checks = result.get('checks') or {}
    action = result.get('action') or {}
    print(f"✓ Receipt {result.get('receipt_id')} VERIFIED")
    print(f"✓ Agent: {action.get('agent_id', 'present')}")
    print(f"✓ Action: {action.get('action_type', 'present')}")
    if checks.get('policy_attribution'):
        print('✓ Policy attribution')
    print('✓ Event hash')
    print('✓ Chain link')


def main(argv=None):
    p = argparse.ArgumentParser(prog='agent-ledger', description='Agent Ledger developer CLI')
    sub = p.add_subparsers(dest='command', required=True)
    i = sub.add_parser('init', help='Create local Agent Ledger configuration')
    i.add_argument('--url'); i.add_argument('--api-key')
    v = sub.add_parser('verify', help='Verify local chain or hosted receipt')
    v.add_argument('target'); v.add_argument('--json', action='store_true', dest='as_json')
    d = sub.add_parser('doctor', help='Check hosted connectivity or production agent health')
    d.add_argument('--production', action='store_true')
    d.add_argument('--days', type=int, default=7)
    d.add_argument('--json', action='store_true', dest='as_json')
    dog = sub.add_parser('dogfood-scuderia', help='Run the canonical real Scuderia read-only agent demonstration')
    dog.add_argument('--url', default=DEFAULT_SCUDERIA_URL)
    dog.add_argument('--authority', default='scuderia-operator')
    dog.add_argument('--json', action='store_true', dest='as_json')
    dog.add_argument('--no-verify', action='store_true')
    a = p.parse_args(argv)

    _load_dotenv()

    if a.command == 'init':
        url = a.url or os.getenv('AGENT_LEDGER_URL', 'https://YOUR-WORKER.workers.dev')
        key = a.api_key or os.getenv('AGENT_LEDGER_API_KEY', 'al_REPLACE_ME')
        Path('.env.agent-ledger').write_text(f'AGENT_LEDGER_URL={url}\nAGENT_LEDGER_API_KEY={key}\n', encoding='utf-8')
        print('✓ wrote .env.agent-ledger')
        print('Next: agent-ledger doctor')
        return 0

    if a.command == 'doctor':
        url = os.getenv('AGENT_LEDGER_URL'); key = os.getenv('AGENT_LEDGER_API_KEY')
        if not url or not key:
            print('✗ set AGENT_LEDGER_URL and AGENT_LEDGER_API_KEY (or run agent-ledger init)', file=sys.stderr); return 2
        try:
            data = remote_get(url, key, '/v1/usage')
            print('✓ API reachable')
            print(f"✓ tenant {data.get('tenant', {}).get('slug', 'unknown')}")
            if a.production:
                report=remote_get(url,key,f'/v1/operations/health?days={a.days}')
                if a.as_json: print(json.dumps(report,indent=2)); return 0
                fleet=report.get('fleet',{}); print(f"\nAGENT OPERATIONS · {a.days} DAYS")
                print(f"Fleet health {fleet.get('health')} · {fleet.get('agents')} agents · {fleet.get('success_rate',0)*100:.1f}% successful")
                for x in report.get('agents',[])[:5]: print(f"{x['status'].upper():9} {x['agent_id']} · health {x['health']} · {x['success_rate']*100:.1f}% success")
                for x in report.get('version_regressions',[])[:3]: print(f"REGRESSION {x['agent_id']} {x['from_version']} → {x['to_version']} ({x['delta']*100:.1f} pts)")
                for x in report.get('loops',[])[:3]: print(f"LOOP       {x['agent_id']} {x['tool_name']} ×{x['count']}")
                for x in report.get('failure_clusters',[])[:3]: print(f"FAILURE    {x['signature']} ×{x['count']}")
                for r in report.get('recommendations',[]): print(f"→ {r}")
            return 0
        except Exception as e:
            print(f'✗ {e}', file=sys.stderr); return 2

    if a.command == 'dogfood-scuderia':
        url = os.getenv('AGENT_LEDGER_URL'); key = os.getenv('AGENT_LEDGER_API_KEY')
        if not url or not key:
            print('✗ dogfood requires AGENT_LEDGER_URL and AGENT_LEDGER_API_KEY', file=sys.stderr); return 2
        try:
            run = observe_scuderia_indexability(a.url, authority=a.authority)
            receipt = run.get('hosted_receipt') or {}
            receipt_id = receipt.get('receipt_id')
            if a.as_json:
                output = dict(run)
                if receipt_id and not a.no_verify:
                    try: output['verification'] = remote_get(url, key, f'/v1/receipts/{receipt_id}')
                    except Exception as exc: output['verification_error'] = str(exc)
                print(json.dumps(output, indent=2, default=str))
            else:
                obs = run['observation']
                print(f"✓ Scuderia live observation: {a.url}")
                print(f"✓ HTTP {obs.get('http_status')} · canonical={'yes' if obs.get('canonical_present') else 'no'} · noindex={'yes' if obs.get('noindex_present') else 'no'}")
                if not receipt_id:
                    print('✗ hosted ingestion returned no receipt_id', file=sys.stderr); return 2
                print(f"✓ Hosted receipt: {receipt_id}")
                if not a.no_verify:
                    verified = remote_get(url, key, f'/v1/receipts/{receipt_id}')
                    _receipt_summary(verified)
                print(f"\nCanonical proof command:\nagent-ledger verify {receipt_id}")
            return 0
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            if exc.code == 401:
                print('✗ receipt verification is unauthorized. Create/use a key with events:write, usage:read, and audit:read scopes.', file=sys.stderr)
            else:
                print(f'✗ HTTP {exc.code}: {detail}', file=sys.stderr)
            return 2
        except Exception as exc:
            print(f'✗ {exc}', file=sys.stderr); return 2

    if a.target.startswith('alr_'):
        url = os.getenv('AGENT_LEDGER_URL'); key = os.getenv('AGENT_LEDGER_API_KEY')
        if not url or not key:
            print('✗ hosted receipt verification requires AGENT_LEDGER_URL and AGENT_LEDGER_API_KEY', file=sys.stderr); return 2
        result = remote_get(url, key, f'/v1/receipts/{a.target}')
    else:
        result = dict(verify_chain(a.target))
    if a.as_json:
        print(json.dumps(result, indent=2))
    elif result.get('verified'):
        _receipt_summary(result)
    elif result.get('valid'):
        print(f"✓ {result['events']} events verified\n✓ Hash chain intact\n✓ Chain: {result['chain_id']}\n✓ Head: {result['head_hash']}")
    else:
        print('✗ verification failed', file=sys.stderr)
    return 0 if result.get('verified') or result.get('valid') else 2


if __name__ == '__main__':
    raise SystemExit(main())
