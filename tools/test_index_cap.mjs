import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../src/worker.js', import.meta.url), 'utf8');
const start = source.indexOf('const IDX_CAP_AUTO');
const end = source.indexOf('export class ConfigVault {', start);
let now = Date.parse('2026-10-02T15:00:00Z');
class Clock extends Date { static now() { return now; } }
const IndexMemory = vm.runInNewContext(
  source.slice(start, end).replace('export class IndexMemory', 'class IndexMemory') + '\nIndexMemory;',
  { Date: Clock, Response, Request, _scanObjEntries() {}, _scanTopLevel() {} },
);

function cursor(rows, rowsWritten) { const c = [...rows]; c.rowsWritten = rowsWritten; return c; }
function fixture(values = {}, o = {}) {
  const meta = new Map(Object.entries(values));
  const alarms = [];
  const sql = { exec(q, ...args) {
    if (q.startsWith('SELECT v FROM meta')) return meta.has(args[0]) ? [{ v: meta.get(args[0]) }] : [];
    if (q.startsWith('INSERT INTO meta')) { meta.set(args[0], args[1]); return []; }
    if (q.startsWith('SELECT count(*) AS n FROM docs_new')) return [{ n: o.docsNew ?? 7000 }];
    if (q.startsWith('SELECT count(*) AS n FROM docs')) return [{ n: o.docs ?? 7000 }];
    if (q.startsWith('SELECT count(*) AS n FROM terms')) return [{ n: o.terms ?? 500000 }];
    if (q.startsWith('INSERT INTO terms_new') || q.startsWith('INSERT OR REPLACE INTO docs_new')) return cursor([], o.insertRows ?? 0);
    if (q.startsWith('CREATE INDEX')) return cursor([], o.indexRows ?? 0);
    if (q.startsWith('DROP TABLE') || q.startsWith('ALTER TABLE')) return cursor([], 0);
    throw new Error('Unexpected SQL: ' + q);
  } };
  const env = { PDFS: { head: async () => ({ etag: 'new' }), get: async () => ({ text: async () => '{}' }) } };
  const item = new IndexMemory({ storage: { sql, setAlarm: async (at) => alarms.push(at) } }, env);
  item._ready = true;
  return { item, meta, alarms };
}
const M = (n) => String(n * 1000000);

// 账期：每月 9 日（UTC）起算
for (const [iso, key] of [['2026-10-08T23:59:59Z', '2026-09'], ['2026-10-09T00:00:00Z', '2026-10'],
                          ['2026-01-05T00:00:00Z', '2025-12'], ['2026-09-09T00:00:00Z', '2026-09']]) {
  now = Date.parse(iso);
  assert.equal(fixture().item._cycleKey(), key, iso);
}

// 本周期（9/9–10/8）已写 68.52M：自动与人手 force 都不许再写
now = Date.parse('2026-10-02T15:00:00Z');
{
  const f = fixture({ built: '2026-09-30T15:40:00Z', stamp: 'old' });
  const r = await f.item._ensure(false);
  assert.equal(r.why, 'monthly_cap'); assert.equal(f.alarms.length, 0);
  assert.equal(r.used, 68520000);
  const r2 = await f.item._ensure(true);
  assert.equal(r2.why, 'hard_cap'); assert.equal(r2.ok, false); assert.equal(f.alarms.length, 0);
}
// 新周期（10/9 起）计数归零，恢复正常排队
now = Date.parse('2026-10-09T15:20:00Z');
{
  const f = fixture({ built: '2026-10-08T15:40:00Z', stamp: 'old', capCycle: '2026-09', capRows: M(68) });
  assert.equal((await f.item._ensure(false)).why, 'queued');
  assert.equal(f.meta.get('capCycle'), '2026-10'); assert.equal(f.meta.get('capRows'), '0');
  assert.equal(f.meta.get('runRows'), '0'); assert.equal(f.alarms.length, 1);
}
// 临界：已用 ＋ 预计一趟 ＞ 4000 万 就不开工（预计取 lastSyncRows 与 160 万的较大者）
{
  const mk = (used, last) => fixture({ built: '2026-10-08T15:40:00Z', stamp: 'old', capCycle: '2026-10', capRows: String(used), lastSyncRows: String(last) });
  let f = mk(38000000, 1000000);          // 38.0 + 1.6 = 39.6 ≤ 40
  assert.equal((await f.item._ensure(false)).why, 'queued');
  f = mk(38500000, 1000000);              // 38.5 + 1.6 = 40.1 > 40
  assert.equal((await f.item._ensure(false)).why, 'monthly_cap');
  f = mk(36000000, 5000000);              // 预计取 lastSyncRows：36 + 5 = 41 > 40
  assert.equal((await f.item._ensure(false)).why, 'monthly_cap');
  // 人手 force：越过 4000 万可以，但到 4800 万为止
  f = mk(46000000, 1000000);              // 46.0 + 1.6 = 47.6 ≤ 48
  assert.equal((await f.item._ensure(true)).why, 'queued');
  f = mk(46500000, 1000000);              // 46.5 + 1.6 = 48.1 > 48
  const r = await f.item._ensure(true);
  assert.equal(r.why, 'hard_cap'); assert.equal(f.alarms.length, 0);
}
// 记账：_w 读 rowsWritten，_flushRows 落到 capRows 与 runRows；失败的任务也入账
{
  const f = fixture({ capCycle: '2026-10', capRows: '1000', runRows: '0' }, { insertRows: 90 });
  f.item._w('INSERT INTO terms_new(term,i,src) VALUES (?,?,?)', 'a', 1, 'k');
  f.item._w('INSERT INTO terms_new(term,i,src) VALUES (?,?,?)', 'b', 2, 'k');
  f.item._flushRows();
  assert.equal(f.meta.get('capRows'), '1180'); assert.equal(f.meta.get('runRows'), '180');
  f.item._flushRows(); assert.equal(f.meta.get('capRows'), '1180');   // 重复落账不重复计
}
// 同步结束的入账：取「实测」与「保守下限（文档 ＋ 词条×2）」的较大者，lastSyncRows 同步更新
{
  // 实测偏低（只读到建索引的 10 万行）→ 补到下限 7000 + 2×500000
  let f = fixture({ pending: JSON.stringify(['coords']), newstamp: 's1', capCycle: '2026-10', capRows: '0', runRows: '0' }, { indexRows: 100000 });
  await f.item.alarm();
  assert.equal(f.meta.get('capRows'), String(7000 + 2 * 500000));
  assert.equal(f.meta.get('lastSyncRows'), String(7000 + 2 * 500000));
  assert.equal(f.meta.get('stamp'), 's1');
  // 实测高于下限（比如删旧表也被计行）→ 以实测为准
  f = fixture({ pending: JSON.stringify(['coords']), newstamp: 's2', capCycle: '2026-10', capRows: '0', runRows: '0' }, { indexRows: 1900000 });
  await f.item.alarm();
  assert.equal(f.meta.get('capRows'), '1900000'); assert.equal(f.meta.get('lastSyncRows'), '1900000');
}
// 状态里带出闸的读数，工作流据此决定整趟是否开工
{
  const f = fixture({ capCycle: '2026-10', capRows: M(39) });
  const s = f.item._status === undefined ? null : null;
  f.item.sql.exec = ((orig) => (q, ...a) => q.startsWith('SELECT count(*) AS n FROM terms') ? [{ n: 1 }] : orig(q, ...a))(f.item.sql.exec);
  const st = f.item._status();
  assert.equal(st.cap.capped, true); assert.equal(st.cap.used, 39000000); assert.equal(st.cap.capAuto, 40000000);
}
console.log('Index monthly write cap: cycle, thresholds, hard ceiling, accounting and settlement tests passed.');
