// 命题账本（ledger）的护栏。跑法：node tools/sim_ledger.mjs
//
// 账本的第一件事是给候选卡补 pid / kin / g / src，把它升格成"三个维度都能指着说话"的对象。
// 这里测三样，都是行为实测不是读源码：
//   ① ppGrams 与 public/assets/sde-nbr.js 的 grams() **逐字同义**——一端算的指纹另一端要能直接比。
//      近邻库那条线已经栽过一次（两端给出两个召回数字，根因是口径差了三处），所以这条断言最要紧。
//   ② ppUp 惰性升格：老卡读到才补、改过才写、天然幂等。
//   ③ schema 里**没有任何可排序成等级的字段**（赞/分/粉丝/排名）——这不是约定，是结构约束。
import fs from "node:fs";
import path from "node:path";
const R = (p) => fs.readFileSync(path.join(process.cwd(), p), "utf8");
const W = R("src/worker.js");
const NBR = R("public/assets/sde-nbr.js");
const CAND = R("public/taste/assets/sde-cand.js");

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  ← " + JSON.stringify(extra) : "")); }
};
const group = (n) => console.log("\n【" + n + "】");

/* ── 抠出 worker 里的账本工具真跑 ── */
function grab(re, label) {
  const m = W.match(re);
  if (!m) throw new Error("抠不出 " + label + "——worker 结构变了，先改这个 sim");
  return m[0];
}
const SRC = [
  grab(/const PP_PUNCT = [\s\S]*?\n      const ppGrams = \(s\) => \{[\s\S]*?\n      \};/, "ppGrams"),
  grab(/const PP_ID_RE = [\s\S]*?\n      const ppKin = [^\n]*\n/, "ppId/ppSys/ppKin"),
  grab(/const ppUp = \(c\) => \{[\s\S]*?\n      \};/, "ppUp"),
].join("\n");
const box = {};
new Function("box", SRC + "\nbox.ppGrams=ppGrams;box.ppId=ppId;box.ppSys=ppSys;box.ppKin=ppKin;box.ppUp=ppUp;box.RE=PP_ID_RE;")(box);

/* ── 抠出近邻库模块的 grams 真跑（它是 (function(w){…})(window) 形） ── */
const nw = {};
new Function("window", NBR)(nw);
const nbrGrams = (s) => Object.keys(nw.SDENbr._grams(s));

group("一、两端文法逐字同义（改任一端不同步就当场红）");
const CASES = [
  "任何划界者都无法在自己划出的界内安置自己的划界动作",
  "ego depletion 与自我损耗其实是同一块地",
  "S 就是被看到这件事本身，不是结构",
  "Weick's enactment：环境是被行动划出来的",
  "",
  "。、；：？！——…",
  "abc de fghij 中文混排 test123",
];
let same = 0;
for (const c of CASES) {
  const a = box.ppGrams(c).slice().sort();
  const b = nbrGrams(c).slice().sort();
  if (JSON.stringify(a) === JSON.stringify(b)) same++;
  else console.log("    差异：" + JSON.stringify(c) + "\n      worker: " + JSON.stringify(a) + "\n      nbr   : " + JSON.stringify(b));
}
ok("七组输入两端产出同一组文法", same === CASES.length, same + "/" + CASES.length);
ok("★ 拉丁词整词保留（先换空格再抽，不能粘成一个词）",
  box.ppGrams("ego depletion").indexOf("ego") >= 0 && box.ppGrams("ego depletion").indexOf("depletion") >= 0
  && box.ppGrams("ego depletion").indexOf("egodepletion") < 0);
ok("汉字按二元组切", box.ppGrams("划界者").join(",") === "划界,界者");
ok("两字以下的拉丁不收（噪音）", box.ppGrams("a bc def").join(",") === "def");
ok("空输入不炸", box.ppGrams("").length === 0 && box.ppGrams(null).length === 0);

group("二、命题号");
const id1 = box.ppId(Date.now()), id2 = box.ppId(Date.now());
ok("形状对得上 PP_ID_RE", box.RE.test(id1) && box.RE.test(id2));
ok("同一毫秒也不重号（尾部有随机）", id1 !== id2);
ok("按时间可排序（36 进制时间补齐到 8 位，短的补零否则字典序会骗人）",
  box.ppId(1000) < box.ppId(2000) && box.ppId(1700000000000) < box.ppId(1800000000000));
ok("认不出的号一律拒收", !box.RE.test("p_xxx") && !box.RE.test("cd:123") && !box.RE.test(""));

group("三、来处与血缘");
ok("sys 只认 S/D/E，别的落回 D", box.ppSys("S") === "S" && box.ppSys("e") === "E" && box.ppSys("X") === "D" && box.ppSys() === "D");
ok("kin 只收合法命题号", JSON.stringify(box.ppKin([id1, "垃圾", "", id2])) === JSON.stringify([id1, id2]));
ok("kin 封顶 8 条", box.ppKin(new Array(20).fill(id1)).length === 8);
ok("kin 不是数组也不炸", box.ppKin(null).length === 0 && box.ppKin("x").length === 0);

group("四、惰性升格：老卡读到才补、改过才写、幂等");
const old = { id: "0000000000000000:abcdef01", uid: "u1", prop: "任何划界者都无法安置自己的划界动作", face: "把甲与乙分开", crit: "若丙则失效", ts: 1700000000000, state: "open" };
ok("★ 老卡第一次被读到 → 补齐四件并报「改过」", box.ppUp(old) === true);
ok("补出了命题号", box.RE.test(old.pid));
ok("★ 文法从命题＋辨别面算出来（不含判据——判据是怎么判，不是它占哪块地）",
  old.g.length > 0 && old.g.indexOf("划界") >= 0 && old.g.indexOf("若丙") < 0);
ok("血缘补成空数组而不是 undefined", Array.isArray(old.kin) && old.kin.length === 0);
ok("★ 老卡的来处记 E（它本来就是在微信里立的），不冒充别的维度", old.src.sys === "E");
const snap = JSON.stringify(old);
ok("★★ 第二次读同一张卡 → 不再报「改过」（幂等，不会每读一次写一次库）", box.ppUp(old) === false);
ok("且内容一个字节都没变", JSON.stringify(old) === snap);
const half = { id: "x", pid: id1, prop: "甲乙丙丁", ts: 1 };
ok("只缺一件也补得上（缺什么补什么）", box.ppUp(half) === true && half.g.length > 0 && Array.isArray(half.kin));
ok("已有的命题号不被覆盖（否则三系统的指针全断）", half.pid === id1);
ok("空卡不炸", box.ppUp(null) === false);

group("五、落卡与读卡的接线");
ok("落卡就带四件", /pid: ppId\(now\)/.test(W) && /src: \{ sys: ppSys\(b\.sys\), at: cdClean\(b\.src, 80\) \}/.test(W)
  && /kin: ppKin\(b\.kin\)/.test(W) && /g: ppGrams\(cdClean\(b\.prop, 120\)/.test(W));
ok("落卡同时写 pid→键 的指针", /await ppLink\(this\.ctx\.storage, card\)/.test(W));
ok("★ feed 里结算与升格各判各的（不用 || 短路，否则第二件被吃掉）",
  /let dirty = cdSettle\(c, now\);\s*\n\s*if \(ppUp\(c\)\) \{ dirty = true;/.test(W));
ok("顶回与分离线两处也顺手升格", (W.match(/if \(ppUp\(c\)\) await ppLink/g) || []).length >= 2);
ok("有按 pid 取命题的入口", /if \(op === "ppget"\)/.test(W) && /pass = \["get"\]/.test(W));
ok("★ 老卡还没 pid 时如实说，不假装它不存在", /老卡要被读到一次才会补上命题号/.test(W));
ok("cd 路由把 sys/src/kin 转发下去（不转发等于永远收不到）", /sys: b\.sys, src: b\.src, kin: b\.kin/.test(W));
ok("前端模块也把 sys/kin 递上来", /sys: String\(\(c && c\.sys\) \|\| "D"\), kin: \(c && c\.kin\) \|\| \[\]/.test(CAND));

group("六、schema 里不许有可排序成等级的东西");
const CARD_SEG = (W.match(/const card = \{[\s\S]*?due: now \+ CD_WIN[^\n]*\n/) || [""])[0];
ok("抠得到落卡的 schema", CARD_SEG.length > 100);
ok("★★ 卡上没有赞／分／热度／排名／粉丝任何一个字段",
  !/\b(likes?|score|hot|rank|fans|votes?|stars?)\s*:/.test(CARD_SEG), CARD_SEG.slice(0, 200));
ok("注释里写明了为什么不给它位置", /任何可排序成等级的\s*\n?\s*\/?\/?\s*数字/.test(W) || /可排序成等级/.test(W));

console.log("\n" + "═".repeat(52));
console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
console.log("═".repeat(52));
process.exit(fail ? 1 : 0);
