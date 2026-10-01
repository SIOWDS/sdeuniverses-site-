import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../src/worker.js', import.meta.url), 'utf8');
const start = source.indexOf('export class IndexMemory {');
const end = source.indexOf('export class ConfigVault {', start);
let now = Date.parse('2026-10-01T15:20:00Z');
class Clock extends Date { static now() { return now; } }
const IndexMemory = vm.runInNewContext(
  source.slice(start, end).replace('export class IndexMemory', 'class IndexMemory') + '\nIndexMemory;',
  { Date: Clock, Response, Request },
);

function fixture(values = {}, docs = 7489) {
  const meta = new Map(Object.entries(values));
  const alarms = [];
  const sql = { exec(q, ...args) {
    if (q.startsWith('SELECT v FROM meta')) return meta.has(args[0]) ? [{ v: meta.get(args[0]) }] : [];
    if (q.startsWith('INSERT INTO meta')) { meta.set(args[0], args[1]); return []; }
    if (q.startsWith('SELECT count(*) AS n FROM docs')) return [{ n: docs }];
    throw new Error('Unexpected SQL: ' + q);
  } };
  const env = { PDFS: { head: async () => ({ etag: 'new' }) } };
  const item = new IndexMemory({ storage: { sql, setAlarm: async (at) => alarms.push(at) } }, env);
  item._ready = true;
  return { item, meta, alarms, env };
}

// A new deployment must respect a rebuild already completed earlier in the same Beijing day.
{
  const f = fixture({ built: '2026-10-01T06:21:58Z', stamp: 'old' });
  assert.equal((await f.item._ensure(false)).why, 'daily_limit');
  assert.equal(f.alarms.length, 0);
}
// The first rebuild queues once; another instance sharing persistent state cannot queue another.
{
  const f = fixture({ built: '2026-09-30T15:40:00Z', stamp: 'old' });
  assert.equal((await f.item._ensure(false)).why, 'queued');
  assert.equal(f.meta.get('queuedDay'), '2026-10-01');
  f.meta.set('pending', '');
  assert.equal((await f.item._ensure(false)).why, 'daily_limit');
  assert.equal(f.alarms.length, 1);
  now = Date.parse('2026-10-01T16:00:00Z'); // Beijing midnight, not UTC midnight.
  assert.equal((await f.item._ensure(false)).why, 'queued');
  assert.equal(f.alarms.length, 2);
}
now = Date.parse('2026-10-01T15:20:00Z');
// Two concurrent HEAD requests must still start a single rebuild.
{
  const f = fixture({ built: '2026-09-30T15:40:00Z', stamp: 'old' });
  let release;
  const head = new Promise(resolve => { release = resolve; });
  f.env.PDFS.head = () => head;
  const both = Promise.all([f.item._ensure(false), f.item._ensure(false)]);
  release({ etag: 'new' });
  const results = await both;
  assert.equal(results.filter(r => r.why === 'queued').length, 1);
  assert.equal(f.alarms.length, 1);
}
// Fresh data incurs no writes; authorized force retains the existing recovery route.
{
  const f = fixture({ built: '2026-10-01T06:21:58Z', stamp: 'new' });
  assert.equal((await f.item._ensure(false)).why, 'fresh');
  assert.equal(f.alarms.length, 0);
  assert.equal((await f.item._ensure(true)).why, 'queued');
}
// Ordinary queries never trigger a stale-index rebuild; empty-store bootstrap is bounded too.
{
  const f = fixture({ stamp: 'old' });
  f.item._query = () => ({ ok: true });
  await f.item.fetch(new Request('https://idx.internal/', { method: 'POST', body: '{"op":"query"}' }));
  assert.equal(f.alarms.length, 0);
  const empty = fixture({}, 0);
  assert.equal((await empty.item._ensure(false)).why, 'queued');
  empty.meta.set('pending', '');
  assert.equal((await empty.item._ensure(false)).why, 'daily_limit');
}
assert.ok(!source.includes('idxHeal('), 'Stale-index auto-healing must not return');
assert.ok(!source.includes('[idx-daily]'), 'The separate cron must not rebuild the index');
console.log('Daily index policy: completed-day, persistent guard, timezone, concurrent requests, fresh, force and query tests passed.');
