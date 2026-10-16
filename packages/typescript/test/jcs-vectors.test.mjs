import {test} from 'node:test';
import {strict as assert} from 'node:assert';
import {readFileSync} from 'node:fs';
import {canonicalizeJcs} from '../dist/index.js';
const vectors=JSON.parse(readFileSync(new URL('../../../tests/interop/jcs_vectors.json',import.meta.url),'utf8'));
test('Python/TypeScript shared RFC8785 fixtures',()=>{for(const v of vectors)assert.equal(canonicalizeJcs(v.input),v.canonical)});
