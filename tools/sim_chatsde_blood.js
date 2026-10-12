/* sim_chatsde_blood —— 2026-10-12 王德生令「一个要满血，一个要无血」的验收（源码检视式；推上去后仍要真跑一次）。
 * 满血：ChatSDE 本体的 SDE 一路不看标准／深度、不看档位，一律装完整内功（含二阶碰撞）＋完整工序。
 * 无血：无 SDE 一路不收长期记忆、分层记忆、「关于我」、前情账本；历史只带本场无 SDE 档的那几轮。
 * 跑法：node tools/sim_chatsde_blood.js（在 site 根目录） */
const fs = require("fs");
const W = fs.readFileSync("src/worker.js", "utf8"), F = fs.readFileSync("public/wds-mode.js", "utf8");
let P = 0, X = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { X++; console.log("  FAIL " + m); } }
const hi = W.indexOf('if (url.pathname === "/api/wds/chat")');
const C = W.slice(hi, W.indexOf('if (url.pathname === "/api/wds/ping")', hi));
console.log("① 满血");
const i5 = C.indexOf('if (!prof && !noSde && !rs && !duel && tool !== "iq") {');
ok(i5 > 0, "完整内功的闸不再看 G.on／gK.ng（标准档、1–4 档也装）");
ok(C.indexOf("if (G.on && gK.ng") < 0, "旧的第 5 档专属闸已拆");
ok(i5 > 0 && C.slice(i5, i5 + 2600).indexOf('loadNeigong(env, url, "/taste/assets/sde-neigong.txt")') > 0, "装的是默认那份（loadNeigong 会接上二阶碰撞）");
ok(i5 > 0 && C.slice(i5, i5 + 2600).indexOf("resPriorFit(") > 0 && C.slice(i5, i5 + 2600).indexOf("neigongLite(_ng5)") > 0, "仍走预算闸，装不下退精简并当场说明");
ok(i5 > 0 && i5 < C.indexOf("WDS_CHAT_SYS(reflect, SDEM,"), "装在 system 拼装之前");
ok(/const mFull = \(!noSde && !prof && !duel\) \? true : /.test(C), "完整工序不再看档位");
ok(/满血：已装完整内功先验/.test(C), "屏幕上的说明改成「满血」");
console.log("② 无血 · 服务端兜底（老缓存客户端也拦得住）");
ok(/const _noBlood = b\.nosde === 1 \|\| b\.nosde === true;\n\s*let umem = _noBlood \? "" :/.test(C), "长期记忆 umem 清空（且排在 noSde 声明之前，不踩 TDZ）");
ok(/const umem3 = \(!_noBlood && /.test(C), "分层记忆 umem3 不收");
ok(/const about = noSde \? "" :/.test(C) && C.indexOf("const about = noSde") > C.indexOf("const noSde = b.nosde"), "「关于我」清空（noSde 已声明之后）");
ok(/const comp = noSde \? "" :/.test(C) && C.indexOf("const comp = noSde") > C.indexOf("const noSde = b.nosde"), "前情账本清空");
console.log("③ 无血 · 前端");
ok(/function histPack\(from, nsOnly\) \{[\s\S]{0,200}if \(nsOnly && !history\[i\]\.ns\) continue;/.test(F), "histPack 能只取无 SDE 档的轮次");
ok(/if \(_ns\) \{ payload\.history = histPack\(0, true\); payload\.umem = ""; delete payload\.umem3; payload\.about = ""; delete payload\.comp; \}/.test(F), "无 SDE 一发：历史只带 ns 轮、四样一起断");
ok(F.indexOf("var _ns = payload.nosde ? 1 : 0;") > F.indexOf("var payload = { q: q, history: histPack("), "_ns 在 payload 之后才定（读的是同一个 nosde 判据）");
ok(/history\.push\(_ns \? \{ role: "reader", text: q, ns: 1 \}/.test(F), "提问落盘时打上 ns 标记");
ok(/H\.push\(_ns \? \{ role: "wds", text: answer, ns: 1 \}/.test(F) && /history\.push\(_ns \? \{ role: "wds", text: answer, ns: 1 \}/.test(F), "两处答案落盘都打 ns（后台场与前台场）");
ok(/history\.push\(t\.ns \? \{ role: "reader", text: t\.text, ns: 1 \}/.test(F) && /history\.push\(t\.ns \? \{ role: "wds", text: t\.text, ns: 1 \}/.test(F), "重开旧场时 ns 标记不丢");
const S = fs.readFileSync("public/assets/wds-store.js", "utf8");
ok(/return t\.ns \? \{ role: t\.role, text: t\.text, ns: 1 \}/.test(S), "本机会话库落盘时保留 ns（否则一重开旧场标记就丢）");
// 行为：用一份假 history 跑 histPack 的过滤逻辑
const m = F.match(/function histPack\(from, nsOnly\) \{[\s\S]*?\n  \}\n/);
const fn = new Function("history", "HIST_PERMSG", "HIST_BUDGET", m[0] + "; return histPack;")(
  [{ role: "reader", text: "冰为什么滑" }, { role: "wds", text: "SDE：滑是相遇的产物" },
   { role: "reader", text: "冰为什么滑", ns: 1 }, { role: "wds", text: "无 SDE：预融层", ns: 1 }], 8000, 60000);
const a = fn(0, true), b = fn(0, false);
ok(a.length === 2 && a.every((x) => x.text.indexOf("SDE：") < 0 || x.text.indexOf("无 SDE") === 0), "行为：无血历史里看不到 SDE 那一答");
ok(b.length === 4, "行为：SDE 一路历史照旧完整");
console.log("===== " + P + " PASS / " + X + " FAIL =====");
process.exit(X ? 1 : 0);
