import pytest
from agent_ledger import canonicalize_jcs, JCSError, generate_keypair, build_run_manifest, sign_manifest, verify_manifest, compare_replay

def test_rfc8785_sample():
    v={'numbers':[333333333.33333329,1E30,4.50,2e-3,1e-27],'string':'€$\x0f\nA\'B"\\\\"/','literals':[None,True,False]}
    assert canonicalize_jcs(v)=='{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],"string":"€$\\u000f\\nA\'B\\"\\\\\\\\\\\"/"}'
def test_utf16_sort_and_rejections():
    v={'€':'Euro','\r':'CR','דּ':'Hebrew','1':'One','😀':'Emoji','\x80':'Control','ö':'Latin'}
    out=canonicalize_jcs(v); assert [out.index(x) for x in ['CR','One','Control','Latin','Euro','Emoji','Hebrew']]==sorted(out.index(x) for x in ['CR','One','Control','Latin','Euro','Emoji','Hebrew'])
    with pytest.raises(JCSError): canonicalize_jcs(float('nan'))
    with pytest.raises(JCSError): canonicalize_jcs('\ud800')
def test_signed_manifest_and_replay():
    private,public=generate_keypair(); m=build_run_manifest(run_id='r1',events=[{'a':1}],effects=[{'s':'COMMITTED'}]); signed=sign_manifest(m,private); assert verify_manifest(signed,public)
    signed['event_count']=2; assert not verify_manifest(signed,public)
    assert compare_replay([{'x':1}],[{'x':1}]).equivalent
    assert not compare_replay([{'x':1}],[{'x':2}]).equivalent
