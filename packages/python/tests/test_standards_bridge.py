import pytest
from agent_ledger.standards_bridge import parse_traceparent, event_to_otel_attributes

def test_traceparent_valid():
    p = parse_traceparent('00-' + 'a'*32 + '-' + 'b'*16 + '-01')
    assert p['trace_flags'] == '01'

@pytest.mark.parametrize('value', ['00-'+'0'*32+'-'+'b'*16+'-01', '00-'+'a'*32+'-'+'0'*16+'-01', 'ff-'+'a'*32+'-'+'b'*16+'-01', 'invalid'])
def test_traceparent_invalid(value):
    with pytest.raises(ValueError): parse_traceparent(value)

def test_telemetry_redacts_content():
    attrs = event_to_otel_attributes({'event_id':'e1','agent_id':'a1','action':'execute_tool','observation':'SECRET','prior_state':{'token':'SECRET'}})
    assert 'SECRET' not in str(attrs)
    assert attrs['agentledger.action'] == 'execute_tool'
