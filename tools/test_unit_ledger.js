// 三位一体出版单元内核测试（合成数据、无网络）。node tools/test_unit_ledger.js
const U = require("../public/books/unit/unit.js");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL:", m); } }
function throws(f, re, m) { try { f(); fail++; console.log("FAIL(no throw):", m); } catch (e) { if (re && !re.test(e.message + (e.code || ""))) { fail++; console.log("FAIL(wrong err):", m, e.message); } else pass++; } }
function mem(limit) { const o = {}; return { getItem: k => (k in o ? o[k] : null), setItem: (k, v) => { if (limit && v.length > limit) throw new Error("QuotaExceeded"); o[k] = v; }, _o: o }; }

const node = { id: "P1", q: "为什么目标越清楚人越没劲？" };
function flow(L, no, mats, task) {
  const r = U.prepare({ no, node, task: task || "ask", materials: mats || [] });
  L.append({ type: "prepared", node: "P1", requestId: r.requestId, hash: r.hash, task: r.task });
  L.append({ type: "sent", node: "P1", requestId: r.requestId, hash: r.hash });
  return r;
}

// 1 基本流程：准备→发送→回执→采纳/独立修订
{ const L = new U.Ledger(mem(), 3); const r = flow(L, 3, []);
  const rc = L.append({ type: "receipt", node: "P1", requestId: r.requestId, status: "complete", text: "建议……" });
  ok(rc.id && rc.status === "complete", "receipt stored");
  const rv = L.append({ type: "revision", node: "P1", stance: "adopt", basisReceipt: rc.id, text: "我同意把名词目标改成动词目标" });
  ok(rv.confirmedBy === "reader", "revision by reader");
  ok(U.nodeView(L.forNode("P1")).revisions.length === 1, "view");
}
// 2 回执规则
{ const L = new U.Ledger(mem(), 3);
  throws(() => L.append({ type: "receipt", node: "P1", requestId: "nope", status: "complete", text: "x" }), /without sent/, "receipt needs sent");
  const r = flow(L, 3, []);
  throws(() => L.append({ type: "sent", node: "P1", requestId: r.requestId, hash: r.hash }), /already sent/, "no double send");
  L.append({ type: "receipt", node: "P1", requestId: r.requestId, status: "interrupted", text: "半截" });
  const again = L.append({ type: "receipt", node: "P1", requestId: r.requestId, status: "interrupted", text: "半截" });
  ok(again.status === "interrupted", "idempotent receipt");
  throws(() => L.append({ type: "receipt", node: "P1", requestId: r.requestId, status: "complete", text: "不同" }), /conflicting/, "conflict receipt");
  const rc = L.all().filter(e => e.type === "receipt")[0];
  throws(() => L.append({ type: "revision", node: "P1", stance: "adopt", basisReceipt: rc.id, text: "采纳" }), /incomplete/, "cannot adopt interrupted");
  ok(L.append({ type: "revision", node: "P1", stance: "independent", text: "我自己的理由" }).stance === "independent", "independent allowed");
  throws(() => L.append({ type: "revision", node: "P1", stance: "independent", text: "  " }), /own words/, "empty revision");
  ok(L.append({ type: "revision", node: "P1", stance: "defer" }).stance === "defer", "defer needs no text");
  throws(() => L.append({ type: "sent", node: "P1", requestId: "ghost", hash: "1" }), /does not match/, "sent needs prepared");
  throws(() => L.append({ type: "sent", node: "P1", requestId: r.requestId, hash: "bad" }), /does not match|already/, "hash mismatch");
}
// 3 负载：只含勾选材料；缺材料提示；超长拒绝而不截断
{ const mats = [{ kind: "a1", text: "初答甲", include: true }, { kind: "a2", text: "复答乙", include: false }, { kind: "t", text: "迁移丙", include: true }];
  const r = U.prepare({ no: 3, node, task: "diagnose", materials: mats });
  ok(r.payload.materials.length === 2 && !JSON.stringify(r.payload).includes("复答乙"), "unchecked material not in payload");
  ok(r.missing.indexOf("a2") >= 0 && r.missing.indexOf("a1") < 0, "diagnose missing a2");
  const r2 = U.prepare({ no: 3, node, task: "diagnose", materials: mats });
  ok(r.hash === r2.hash, "same payload same hash");
  mats[0].text = "变了"; ok(U.prepare({ no: 3, node, task: "diagnose", materials: mats }).hash !== r.hash, "edit changes hash (old confirm invalid)");
  throws(() => U.prepare({ no: 3, node, task: "ask", materials: [{ kind: "a1", text: "字".repeat(U.MAX_MATERIAL_CHARS + 1), include: true }] }), /too_long/, "too long refused");
  throws(() => U.prepare({ no: 3, node, task: "ask", materials: [{ kind: "zzz", text: "x", include: true }] }), /未知材料/, "unknown kind");
  ok(U.prepare({ no: 3, node, task: "bogus", materials: [] }).task === "ask", "unknown task -> ask");
  ok(/不附带任何个人文字/.test(U.previewLines(U.prepare({ no: 3, node, task: "ask", materials: [] })).join("\n")), "preview says nothing attached");
}
// 4 回执状态
{ ok(U.receiptStatus({ text: "ok", ended: true }) === "complete", "complete");
  ok(U.receiptStatus({ text: "ok", ended: false }) === "interrupted", "no end marker");
  ok(U.receiptStatus({ text: "", ended: true }) === "error", "empty");
  ok(U.receiptStatus({ text: "ok", ended: true, httpError: 500 }) === "error", "http error");
  ok(U.receiptStatus({ text: "ok", ended: true, cancelled: true }) === "cancelled", "cancelled");
  ok(U.receiptStatus({ text: "ok", ended: true, truncated: true }) === "interrupted", "truncated");
}
// 5 历史不被裁剪：201 条以上、长答复、未知字段
{ const L = new U.Ledger(mem(), 3);
  for (let i = 0; i < 260; i++) L.append({ type: "observation", node: "P" + (i % 10), text: "观察" + i, ext: { unknown: i } });
  ok(L.all().length === 260, "260 events kept");
  const r = flow(L, 3, []); const long = "长".repeat(21000);
  L.append({ type: "receipt", node: "P1", requestId: r.requestId, status: "complete", text: long });
  ok(L.all().filter(e => e.type === "receipt")[0].text.length === 21000, "21000-char answer kept whole");
  ok(L.all()[5].ext.unknown === 5, "unknown fields preserved");
}
// 6 配额：拒绝并报 quota，不静默丢旧记录
{ const L = new U.Ledger(mem(2000), 3); let n = 0, err = null;
  try { for (; n < 100; n++) L.append({ type: "observation", node: "P1", text: "字".repeat(100) }); } catch (e) { err = e; }
  ok(err && err.code === "quota", "quota error");
  ok(L.all().length === n && n > 0, "old records intact after quota failure");
}
// 7 初答只封存一次
{ const L = new U.Ledger(mem(), 3);
  L.append({ type: "seal", node: "P1", text: "我最初这样想" });
  ok(L.append({ type: "seal", node: "P1", text: "我最初这样想" }).hash, "same seal idempotent");
  throws(() => L.append({ type: "seal", node: "P1", text: "改写的初答" }), /already sealed/, "second different seal refused");
  ok(L.all().filter(e => e.type === "seal").length === 1, "one seal");
}
// 8 导入导出：幂等合并、冲突整批拒绝、跨书拒绝、不同初答冲突
{ const A = new U.Ledger(mem(), 3); A.append({ type: "seal", node: "P1", text: "甲" }); A.append({ type: "observation", node: "P1", text: "观察" });
  const dump = A.export();
  const B = new U.Ledger(mem(), 3);
  ok(B.import(dump).added === 2, "import into empty"); ok(B.import(dump).added === 0, "re-import idempotent");
  throws(() => new U.Ledger(mem(), 4).import(dump), /书号不符/, "cross-book import refused");
  const bad = JSON.parse(dump); bad.events[1].text = "被改过"; 
  throws(() => B.import(JSON.stringify(bad)), /内容不同/, "same id different content refused");
  ok(B.all().length === 2, "ledger untouched after refused import");
  const C = new U.Ledger(mem(), 3); C.append({ type: "seal", node: "P1", text: "乙" });
  throws(() => C.import(dump), /两份不同的初答/, "two different first answers refused");
  throws(() => B.import("{not json"), /JSON/, "invalid json");
  const noid = JSON.stringify({ no: 3, events: [{ type: "x", node: "P1" }] }); throws(() => B.import(noid), /格式不完整/, "missing id");
}
// 9 不同书同名节点不串档；损坏数据不被覆盖
{ const s = mem(); const a = new U.Ledger(s, 3), b = new U.Ledger(s, 152);
  a.append({ type: "observation", node: "P1", text: "三号" }); b.append({ type: "observation", node: "P1", text: "152号" });
  ok(a.forNode("P1").length === 1 && b.forNode("P1")[0].text === "152号", "same node id, separate books");
  s.setItem("wds_unit_9", "{broken"); throws(() => new U.Ledger(s, 9).append({ type: "observation", node: "P1", text: "x" }), null, "corrupt not overwritten");
  ok(s.getItem("wds_unit_9") === "{broken", "corrupt data left in place");
}
// 10 并发：两个页面同时追加，各自重读，不覆盖对方
{ const s = mem(); const p1 = new U.Ledger(s, 3), p2 = new U.Ledger(s, 3);
  p1.append({ type: "observation", node: "P1", text: "页面1" }); p2.append({ type: "observation", node: "P1", text: "页面2" });
  ok(p1.all().length === 2, "both pages' records survive");
}
console.log(pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
