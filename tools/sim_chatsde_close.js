/* sim_chatsde_close.js —— 「成文面板关不掉」的护栏
 *
 * .wdsm-dist 是 inset:0 / z-index 100003 的**全屏遮罩**，关不掉就等于整个站被锁住，
 * 读者只能刷新页面才出得去。原来出口只有顶栏那一颗 ✕，而顶栏恰恰是今天反复画不出来的那根横条。
 * 本文件把四条出口逐条真跑一遍：顶栏 ✕ / 角落逃生钮 / Esc / 点遮罩空白处。
 * 跑法：node tools/sim_chatsde_close.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };
const FSRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

/* ═══ 一、把那段关闭逻辑抠出来真跑 ═══ */
const a = FSRC.indexOf("    function distClose() {");
/* 终点锚：distClose 那一段之后紧接的是 cpBtn 那一行（svBtn.textContent 那句在它更后面，
   而且是 `svBtn.textContent = t("dSave")` 那一处——同名前缀不止一个，别用它当锚）。 */
const b = FSRC.indexOf("    cpBtn.onclick =", a);
const SRC = (a > 0 && b > a) ? FSRC.slice(a, b) : "";
ok("抠得到 distClose / distEsc / wrap 上的委托", SRC.indexOf("distEsc") > 0 && SRC.indexOf("wrap.addEventListener") > 0);

/* 手搓一副够用的 DOM：closest 真实现，事件按注册顺序派发 */
function mkNode(cls) {
  const n = {
    className: cls || "", parentNode: null, _kids: [], _listeners: {},
    closest(sel) {
      const want = sel.replace(/^\./, "");
      let cur = this;
      while (cur) { if ((" " + (cur.className || "") + " ").indexOf(" " + want + " ") >= 0) return cur; cur = cur.parentNode; }
      return null;
    },
    addEventListener(k, fn) { (this._listeners[k] = this._listeners[k] || []).push(fn); },
    removeChild(c) { this._kids = this._kids.filter((x) => x !== c); c.parentNode = null; },
    appendChild(c) { this._kids.push(c); c.parentNode = this; return c; },
    fire(k, ev) { (this._listeners[k] || []).forEach((fn) => fn(ev)); },
  };
  return n;
}
function harness(opts) {
  opts = opts || {};
  const box = { saved: 0, cancelled: 0, cleared: 0, notes: [], removed: false, docListeners: [], docRemoved: 0 };
  const body = mkNode("body");
  const wrap = mkNode("wdsm-dist"); body.appendChild(wrap);
  const src =
    /* ⚠ kind 必须给：distClose 里是 distSave(kindT(kind), …)，mock 里少一个 kind 就是 ReferenceError，
       而那一行外面裹着 try{}catch{}——错误被静静吞掉，读数看起来就成了"没存稿"。 */
    "var kind='paper';" +
    "var dStopped=" + (opts.stopped ? "true" : "false") + ", dr=__b.dr, text=__b.text, existing=" + (opts.existing ? "true" : "false") + ";" +
    "var beatT=1, pTrace={ ok:" + (opts.ok ? "true" : "false") + " }, wrap=__b.wrap;" +
    "function kindT(){return '论文';} function distSave(l,t,cb){ __b.saved++; cb&&cb(true); }" +
    "function clearInterval(){ __b.cleared++; }" +
    "function dNote(v){ __b.notes.push(String(v)); } function t(k){ return k; }" +
    "var document={ addEventListener:function(k,f){ __b.docListeners.push(f); }," +
    "               removeEventListener:function(){ __b.docRemoved++; } };\n" +
    SRC +
    "\n__b.esc = __b.docListeners[0];";
  box.wrap = wrap;
  box.text = opts.text === undefined ? "x".repeat(9000) : opts.text;
  box.dr = { cancel() { box.cancelled++; } };
  new Function("__b", src)(box);
  return { box, wrap, body };
}

/* ═══ 二、四条出口 ═══ */
console.log("── 四条出口 ──");
// ① 顶栏 ✕（class dx，点它冒泡到 wrap 的委托）
let h = harness({ ok: true });
let x = mkNode("wdsm-tbtn dx"); h.wrap.appendChild(x);
h.wrap.fire("click", { target: x });
ok("① 顶栏 ✕ 关得掉", h.wrap.parentNode === null);
ok("① 关之前先存了稿", h.box.saved === 1);
ok("① 关之前取消了流", h.box.cancelled === 1);
ok("① 停掉了心跳（不留后台定时器）", h.box.cleared === 1);

// ② 角落逃生钮：它也带 dx，且**挂在遮罩上**而不是盒子里
h = harness({ ok: true });
const esc = mkNode("wdsm-dist-esc dx"); h.wrap.appendChild(esc);
h.wrap.fire("click", { target: esc });
ok("② 角落逃生钮关得掉", h.wrap.parentNode === null);
ok("② 逃生钮确实挂在遮罩上（盒子内部崩了它还在）",
  /<div class='wdsm-dist-c'>[\s\S]{0,120}<\/div>"\s*\+\s*"<button class='wdsm-dist-esc dx'/.test(FSRC));

// ③ Esc
h = harness({ ok: false });
let prevented = 0, stopped = 0;
h.box.esc({ key: "Escape", preventDefault() { prevented++; }, stopPropagation() { stopped++; } });
ok("③ Esc 关得掉（哪怕还在写）", h.wrap.parentNode === null);
ok("③ Esc 在捕获阶段拦下（不让 hotkey 里的 doStop 吞掉）", stopped === 1 && prevented === 1);
ok("③ Esc 也先存了稿", h.box.saved === 1);
h = harness({ ok: true });
h.box.esc({ key: "a", preventDefault() {}, stopPropagation() {} });
ok("③ 别的键不误伤", h.wrap.parentNode !== null);
/* ⚠ 上面那条只验了"拦了没有"，验不出**在哪个阶段拦**。而捕获阶段正是这条修复的承重位：
   hotkey 也挂在 document 上，冒泡阶段注册就可能排在它后面、被 `if (doStop()) return;` 先吞掉。
   （反向验证过：把第三个参数 true 去掉，上面那几条照样全绿——所以必须单独查这一处。） */
ok("③ Esc 是**捕获阶段**注册的（第三个参数 true）",
  /document\.addEventListener\("keydown", distEsc, true\);/.test(FSRC));
ok("③ 面板摘掉时把这个全局监听也摘了（不留悬挂监听）",
  /removeEventListener\("keydown", distEsc, true\)/.test(FSRC));

// ④ 点遮罩空白处
h = harness({ ok: true });
h.wrap.fire("click", { target: h.wrap });
ok("④ 写完之后，点遮罩空白处关得掉", h.wrap.parentNode === null);
h = harness({ ok: false });
h.wrap.fire("click", { target: h.wrap });
ok("④ 写作途中点遮罩**不关**（误点一下丢两万字，代价太大）", h.wrap.parentNode !== null);
ok("④ 而且给了一句话说明该怎么关", h.box.notes.join("|").indexOf("dCloseBusy") >= 0);
h = harness({ ok: false, stopped: true });
h.wrap.fire("click", { target: h.wrap });
ok("④ 已按过停止 → 点遮罩就能关", h.wrap.parentNode === null);
h = harness({ ok: true });
const inner = mkNode("wdsm-dist-box"); h.wrap.appendChild(inner);
h.wrap.fire("click", { target: inner });
ok("④ 点盒子里面不算（只认点在遮罩本身）", h.wrap.parentNode !== null);

// 存稿的边界
h = harness({ ok: true, text: "太短" });
h.wrap.fire("click", { target: h.wrap });
ok("稿子太短就不必存（别在记录里塞空壳）", h.box.saved === 0 && h.wrap.parentNode === null);
h = harness({ ok: true, existing: true });
h.wrap.fire("click", { target: h.wrap });
ok("从「成文记录」摊开的那一份不重复存", h.box.saved === 0);

/* ═══ 三、源码级：全局 Esc 的次序与心跳重建 ═══ */
console.log("── 全局 Esc 与心跳重建 ──");
const hk = FSRC.slice(FSRC.indexOf('if (k === "Escape") {'), FSRC.indexOf('if (k === "Escape") {') + 1400);
/* ⚠ 比先后要拿**代码**的锚去比，不能拿 ".wdsm-dist" 这种在注释里也会出现的串——
   解释这条病的注释里正好先写了 doStop()，naive 的 indexOf 量到的是注释。 */
const iDist = hk.indexOf('querySelectorAll(".wdsm-dist")'), iStop = hk.indexOf("if (doStop()) return;");
ok("全局 Esc 里，成文面板排在 doStop() 之前（doStop 会吞掉按键）", iDist > 0 && iStop > 0 && iDist < iStop);
ok("关的是**最上面**那一个成文面板", /dps\[dps\.length - 1\]/.test(hk));
ok("优先走面板自己的 _close（会存稿），取不到才硬摘节点", /_close === "function"/.test(hk) && /removeChild\(topPanel\)/.test(hk));
ok("旧的 `.wdsm-help || .wdsm-dist` 串联已拆掉（help 层会把成文面板挡住）",
  !/querySelector\("\.wdsm-help"\) \|\| document\.querySelector\("\.wdsm-dist"\)/.test(FSRC));
const beat = FSRC.slice(FSRC.indexOf("beatT = setInterval(function () {"), FSRC.indexOf("}, 2000);"));
ok("心跳重建顶栏时那颗 ✕ 带了 dx（否则重建之后又关不掉）", /el\("button", "wdsm-tbtn dx", "\\u2715"\)/.test(beat));
ok("重建的 ✕ 不再自己绑 onclick（统一走 wrap 上的委托，才会先存稿）",
  beat.indexOf("x2.onclick") < 0);
ok("wrap 上挂了 _close，全局 Esc 才够得着这里的闭包", /wrap\._close = distClose;/.test(FSRC));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
