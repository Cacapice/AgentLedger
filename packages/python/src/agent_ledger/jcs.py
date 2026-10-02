"""RFC 8785 JSON Canonicalization Scheme (JCS)."""
from __future__ import annotations
import math
from typing import Any

class JCSError(ValueError): pass

def _string(s:str)->str:
    # RFC 8785 forbids lone surrogates and does not normalize Unicode.
    for c in s:
        if 0xD800 <= ord(c) <= 0xDFFF: raise JCSError('lone surrogate is not valid I-JSON')
    out='"'
    esc={'"':'\\"','\\':'\\\\','\b':'\\b','\t':'\\t','\n':'\\n','\f':'\\f','\r':'\\r'}
    for c in s:
        o=ord(c)
        if c in esc: out+=esc[c]
        elif o <= 0x1f: out+=f'\\u{o:04x}'
        else: out+=c
    return out+'"'

def _utf16_key(s:str)->bytes:
    return s.encode('utf-16-be','strict')

def _number(x:int|float)->str:
    f=float(x)
    if not math.isfinite(f): raise JCSError('NaN and Infinity are not valid I-JSON')
    if f == 0: return '0'
    # Integers outside exact binary64 range cannot be represented losslessly as I-JSON numbers.
    if isinstance(x,int) and abs(x)>9007199254740991: raise JCSError('integer exceeds I-JSON exact binary64 range; encode as string')
    s=repr(f).lower()
    neg=s.startswith('-'); body=s[1:] if neg else s
    if 'e' in body:
        mant, exp_s=body.split('e'); exp=int(exp_s)
        digits=mant.replace('.','')
        decpos=(mant.find('.') if '.' in mant else len(mant))+exp
        if 1e-6 <= abs(f) < 1e21:
            if decpos <= 0: body='0.'+'0'*(-decpos)+digits
            elif decpos >= len(digits): body=digits+'0'*(decpos-len(digits))
            else: body=digits[:decpos]+'.'+digits[decpos:]
        else:
            mantissa=digits[0]+(('.'+digits[1:]) if len(digits)>1 else '')
            body=mantissa+'e'+('+' if exp>=0 else '-')+str(abs(exp))
    else:
        body=body[:-2] if body.endswith('.0') else body
        # Python uses fixed notation where ECMAScript switches at >=1e21.
        if abs(f)>=1e21:
            digits=body.replace('.','').lstrip('0'); exp=len(body.split('.')[0])-1
            body=digits[0]+(('.'+digits[1:].rstrip('0')) if digits[1:].rstrip('0') else '')+'e+'+str(exp)
    return ('-' if neg else '')+body

def canonicalize(value:Any)->str:
    if value is None: return 'null'
    if value is True: return 'true'
    if value is False: return 'false'
    if isinstance(value,str): return _string(value)
    if isinstance(value,(int,float)) and not isinstance(value,bool): return _number(value)
    if isinstance(value,list): return '['+','.join(canonicalize(v) for v in value)+']'
    if isinstance(value,dict):
        if not all(isinstance(k,str) for k in value): raise JCSError('JSON object keys must be strings')
        keys=sorted(value,key=_utf16_key)
        return '{'+','.join(_string(k)+':'+canonicalize(value[k]) for k in keys)+'}'
    raise JCSError(f'unsupported JSON type: {type(value).__name__}')

def canonicalize_bytes(value:Any)->bytes: return canonicalize(value).encode('utf-8')
