import test from 'node:test';
import assert from 'node:assert/strict';
import { redact } from '../dist/index.js';

test('redacts secrets recursively', () => {
  const result = redact({ token: 'abc', nested: { api_key: 'def', q: 1 } });
  assert.equal(result.value.token, '[REDACTED]');
  assert.equal(result.value.nested.api_key, '[REDACTED]');
  assert.equal(result.value.nested.q, 1);
  assert.deepEqual(result.fields, ['$.nested.api_key', '$.token']);
});
