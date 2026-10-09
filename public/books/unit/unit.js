/* 三位一体出版单元 · 共用内核（阅读 · 学习包 · 智能问对）
 * 以「有历史的问题节点」(unitId + nodeId) 为最小连接单位。
 * 纯逻辑、无 DOM：浏览器里挂 window.WDSUnit，Node 里 require() 即可测试。
 * 不做的事：不联网、不碰密钥、不替读者确认任何东西、不静默裁剪历史。 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.WDSUnit = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var TASKS = {
    ask:       { label: "自由问对",   needs: [],                  hint: "不限定任务，围绕本题自由追问。" },
    hint:      { label: "只给提示",   needs: [],                  hint: "只给一个关键提示或追问，不先给完整答案。" },
    diagnose:  { label: "比较理解",   needs: ["a1", "a2"],        hint: "对照你的初答与复答，说清哪里变了、哪里没变。" },
    critique:  { label: "检验异议",   needs: ["objection"],       hint: "先复述你的异议，再区分误读、有据反对、证据不足。" },
    transfer:  { label: "迁移设计",   needs: [],                  hint: "指定情境、行动、约束、观察与停止条件；计划不等于实施。" },
    review:    { label: "观察回看",   needs: ["observation"],     hint: "对照你的行动与结果：支持、反例、未知分开。" },
    summarize: { label: "本题小结",   needs: [],                  hint: "原文、建议、你的选择与未决事项分开列。" }
  };
  var STATUS = ["complete", "interrupted", "cancelled", "error"];
  var MATERIAL_KINDS = { a1: "初答", a2: "复答", t: "迁移记录", objection: "异议", observation: "实际观察", selection: "读者选句", prior: "旧答复" };
  var MAX_LEDGER_CHARS = 3000000;   // 超出即拒绝并提示导出，绝不静默删旧记录
  var MAX_MATERIAL_CHARS = 6000;    // 单份材料上限：超出让读者自己删减，不替他截断

  /* cyrb53：只做「同一负载」指纹，不是安全哈希 */
  function hash53(str) {
    var h1 = 0xdeadbeef, h2 = 0x41c6ce57;
    for (var i = 0; i < str.length; i++) {
      var ch = str.charCodeAt(i);
      h1 = Math.imul(h1 ^ ch, 2654435761); h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(16);
  }
  function canon(v) {          // 键序固定的 JSON，指纹才可复现
    if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
    if (v && typeof v === "object") return "{" + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ":" + canon(v[k]); }).join(",") + "}";
    return JSON.stringify(v === undefined ? null : v);
  }
  var _seq = 0;
  function newId(prefix) {
    _seq = (_seq + 1) % 1679616;
    return prefix + "_" + Date.now().toString(36) + _seq.toString(36) + Math.random().toString(36).slice(2, 6);
  }

  /* ---------- 账本：追加式事件 ---------- */
  function Ledger(storage, no) {
    if (!(no > 0)) throw new Error("ledger: bad book number");
    this.s = storage; this.no = no; this.key = "wds_unit_" + no;
  }
  Ledger.prototype._load = function () {
    var raw = null; try { raw = this.s.getItem(this.key); } catch (e) {}
    if (!raw) return { v: 1, unitId: "m" + this.no, no: this.no, events: [] };
    var d = JSON.parse(raw);                       // 损坏就抛出：绝不当作空账本覆盖
    if (!d || d.no !== this.no || !Array.isArray(d.events)) throw new Error("ledger: corrupt or foreign data");
    return d;
  };
  Ledger.prototype._save = function (d) {
    var raw = JSON.stringify(d);
    if (raw.length > MAX_LEDGER_CHARS) { var e = new Error("本书学习记录已达上限，请先导出备份后再继续"); e.code = "quota"; throw e; }
    try { this.s.setItem(this.key, raw); }
    catch (x) { var e2 = new Error("浏览器存储写入失败（可能已满或被禁用）；请先导出记录"); e2.code = "quota"; throw e2; }
  };
  Ledger.prototype.all = function () { return this._load().events.slice(); };
  Ledger.prototype.forNode = function (nodeId) { return this.all().filter(function (e) { return e.node === nodeId; }); };
  Ledger.prototype.byId = function (id) { return this.all().filter(function (e) { return e.id === id; })[0] || null; };
  Ledger.prototype.append = function (ev) {
    if (!ev || !ev.type || !ev.node) throw new Error("ledger: event needs type and node");
    var d = this._load();
    var e = {}; Object.keys(ev).forEach(function (k) { e[k] = ev[k]; });
    e.id = e.id || newId("e"); e.ts = e.ts || new Date().toISOString(); e.unitId = d.unitId;
    if (d.events.some(function (x) { return x.id === e.id; })) throw new Error("ledger: duplicate id " + e.id);
    // 规则：初答每个节点只封存一次（同内容幂等，不同内容拒绝）
    if (e.type === "seal") {
      e.hash = e.hash || hash53(String(e.text || ""));
      var old = d.events.filter(function (x) { return x.type === "seal" && x.node === e.node; })[0];
      if (old) { if (old.hash === e.hash) return old; throw new Error("ledger: first answer already sealed for " + e.node); }
    }
    // 规则：回执必须绑定一次已发送的请求，且同一请求只接受一份回执
    if (e.type === "receipt") {
      if (STATUS.indexOf(e.status) < 0) throw new Error("ledger: bad receipt status");
      var sent = d.events.filter(function (x) { return x.type === "sent" && x.requestId === e.requestId; })[0];
      if (!sent) throw new Error("ledger: receipt without sent request");
      var dup = d.events.filter(function (x) { return x.type === "receipt" && x.requestId === e.requestId; })[0];
      if (dup) { if (dup.status === e.status && dup.text === e.text) return dup; throw new Error("ledger: conflicting receipt for " + e.requestId); }
    }
    // 规则：sent 必须绑定已准备的请求，指纹一致；同一请求只发一次
    if (e.type === "sent") {
      var prep = d.events.filter(function (x) { return x.type === "prepared" && x.requestId === e.requestId; })[0];
      if (!prep || prep.hash !== e.hash) throw new Error("ledger: sent does not match prepared payload");
      if (d.events.some(function (x) { return x.type === "sent" && x.requestId === e.requestId; })) throw new Error("ledger: request already sent");
    }
    // 规则：采纳只能针对「完整」回执；其余状态只能作草稿或独立修订
    if (e.type === "revision") {
      if (["adopt", "modify", "object", "defer", "independent"].indexOf(e.stance) < 0) throw new Error("ledger: bad revision stance");
      if (e.stance !== "independent" && e.stance !== "defer") {
        var rc = d.events.filter(function (x) { return x.type === "receipt" && x.id === e.basisReceipt; })[0];
        if (!rc) throw new Error("ledger: revision needs a basis receipt");
        if (rc.status !== "complete" && (e.stance === "adopt" || e.stance === "modify")) throw new Error("ledger: incomplete answer cannot be adopted");
      }
      if (e.stance !== "defer" && (!e.text || !String(e.text).trim())) throw new Error("ledger: revision needs the reader's own words");
      e.confirmedBy = "reader";                   // 只有读者本人操作才会走到这里
    }
    d.events.push(e); this._save(d); return e;
  };
  /* 导出 / 导入 */
  Ledger.prototype.export = function () { return JSON.stringify(this._load(), null, 1); };
  Ledger.prototype.import = function (jsonText) {
    var inc; try { inc = JSON.parse(jsonText); } catch (e) { throw new Error("导入失败：不是有效的 JSON"); }
    if (!inc || inc.no !== this.no || !Array.isArray(inc.events)) throw new Error("导入失败：这不是本书的学习记录（书号不符）");
    var d = this._load(), backup = JSON.stringify(d), byId = {};
    d.events.forEach(function (x) { byId[x.id] = x; });
    var add = [];
    for (var i = 0; i < inc.events.length; i++) {
      var x = inc.events[i];
      if (!x || !x.id || !x.type || !x.node) throw new Error("导入失败：记录格式不完整（第 " + (i + 1) + " 条）");
      if (byId[x.id]) { if (canon(byId[x.id]) !== canon(x)) throw new Error("导入失败：记录 " + x.id + " 与本机同号记录内容不同，已整批拒绝"); }
      else add.push(x);
    }
    // 不同初答冲突：同一节点已封存的初答不允许被另一份取代
    var seal = {}; d.events.concat(add).forEach(function (x) { if (x.type === "seal") { if (seal[x.node] && seal[x.node] !== x.hash) throw new Error("导入失败：节点 " + x.node + " 存在两份不同的初答"); seal[x.node] = x.hash; } });
    d.events = d.events.concat(add); this._save(d);
    return { added: add.length, backup: backup };
  };

  /* ---------- 请求：准备 → 预览 → 确认 → 发送 ---------- */
  /* opts: {no,node:{id,q,why},task,materials:[{kind,text,include}],bookTitle}
   * materials 里 include!==true 的一律不进负载；单份过长直接拒绝，让读者自己删减。 */
  function prepare(opts) {
    var t = TASKS[opts.task] ? opts.task : "ask";
    var miss = TASKS[t].needs.filter(function (k) {
      return !(opts.materials || []).some(function (m) { return m.kind === k && m.include === true && String(m.text || "").trim(); });
    });
    var mats = [];
    for (var i = 0; i < (opts.materials || []).length; i++) {
      var m = opts.materials[i];
      if (m.include !== true || !String(m.text || "").trim()) continue;
      if (!MATERIAL_KINDS[m.kind]) throw new Error("未知材料类型：" + m.kind);
      if (String(m.text).length > MAX_MATERIAL_CHARS) { var e = new Error("「" + MATERIAL_KINDS[m.kind] + "」超过 " + MAX_MATERIAL_CHARS + " 字，请自己删减后再发送（系统不会替你截断）"); e.code = "too_long"; throw e; }
      mats.push({ kind: m.kind, text: String(m.text) });
    }
    var payload = { unitId: "m" + opts.no, node: { id: opts.node.id, q: opts.node.q }, task: t, materials: mats };
    return { requestId: newId("r"), task: t, payload: payload, hash: hash53(canon(payload)), missing: miss };
  }
  /* 预览文本：读者在确认前看到的就是将要发出的全部个人材料 */
  function previewLines(req) {
    var out = ["本题：" + req.payload.node.q, "任务：" + TASKS[req.task].label];
    if (!req.payload.materials.length) out.push("不附带任何个人文字（只发本题公共问题与原文依据）。");
    req.payload.materials.forEach(function (m) { out.push("【" + MATERIAL_KINDS[m.kind] + "】" + m.text); });
    return out;
  }
  /* 回执状态：流有文字不等于完成 */
  function receiptStatus(o) {
    if (o.cancelled) return "cancelled";
    if (o.error || o.httpError) return "error";
    if (!o.text || !String(o.text).trim()) return "error";
    if (!o.ended) return "interrupted";
    if (o.truncated) return "interrupted";
    return "complete";
  }
  /* 把账本里本题的历史整理成视图（供学习页/问对页展示，不改动账本） */
  function nodeView(events) {
    var v = { requests: [], revisions: [], observations: [], objections: [] };
    var rec = {};
    events.forEach(function (e) { if (e.type === "receipt") rec[e.requestId] = e; });
    events.forEach(function (e) {
      if (e.type === "sent") v.requests.push({ sent: e, receipt: rec[e.requestId] || null });
      else if (e.type === "revision") v.revisions.push(e);
      else if (e.type === "observation") v.observations.push(e);
      else if (e.type === "objection") v.objections.push(e);
    });
    return v;
  }

  return { TASKS: TASKS, STATUS: STATUS, MATERIAL_KINDS: MATERIAL_KINDS, MAX_LEDGER_CHARS: MAX_LEDGER_CHARS, MAX_MATERIAL_CHARS: MAX_MATERIAL_CHARS,
           hash53: hash53, canon: canon, newId: newId, Ledger: Ledger, prepare: prepare, previewLines: previewLines, receiptStatus: receiptStatus, nodeView: nodeView };
});
