/* 内功 sde-neigong.txt 的静态护栏
 *
 * 为什么要有这一份：内功是全站的底盘先验，九个页面共读同一个文件（金点子 / 中华智问 /
 * 经典解构 / 智慧讲解 / 提智对照 / 评分器 / 碰撞出典范 / 艺术绘画 / 会议助手），
 * 改一处九处都变——而它此前一个护栏都没有。两类事故最容易发生而且都是静默的：
 *   ① 改了内功却忘了 bump 各页的 ?v=，读者拿到的还是浏览器缓存里的旧文；
 *   ② 内功里某个承重段落被后来的编辑顺手删掉，谁也不会报错。
 *
 *   node tools/sim_neigong.js
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const NG = path.join(ROOT, "public/taste/assets/sde-neigong.txt");

let P = 0, F = 0;
function ok(cond, msg) { if (cond) { P++; console.log("  PASS " + msg); } else { F++; console.log("  FAIL " + msg); } }
function step(t, fn) { console.log(t); try { fn(); } catch (e) { F++; console.log("  FAIL 这一步自己抛了错：" + e.message); } }

const s = fs.readFileSync(NG, "utf8");

step("① 文件在位、体量合理", () => {
  ok(s.length > 40000, "内功不为空且不像被截断（" + s.length + " 字符 · JS 按码元数，汉字算 1）");
  ok(/# SDE-FT-Skill v(\d+\.\d+) 完/.test(s), "结尾有版本收口行");
});

step("② 版本号与各页的 ?v= 缓存戳一致（漏 bump 是静默事故）", () => {
  const m = s.match(/# SDE-FT-Skill v(\d+\.\d+) 完/);
  const ver = m ? m[1] : "";
  ok(!!ver, "取到内功版本号 v" + ver);
  const stamps = new Set();
  const files = [];
  (function walk(d) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) { if (e.name !== ".git") walk(p); }
      else if (/\.(html|js)$/.test(e.name)) files.push(p);
    }
  })(path.join(ROOT, "public"));
  let refs = 0;
  for (const f of files) {
    const t = fs.readFileSync(f, "utf8");
    const re = /sde-neigong\.txt\?v=([\d.]+)/g; let mm;
    while ((mm = re.exec(t))) { refs++; stamps.add(mm[1]); }
  }
  ok(refs > 0, "站内有 " + refs + " 处带 ?v= 的内功引用");
  ok(stamps.size === 1, "所有 ?v= 戳一致，实得：" + Array.from(stamps).join(" / "));
  ok(stamps.has(ver), "?v= 戳与内功版本号对得上（戳 " + Array.from(stamps).join(",") + " ／ 版本 " + ver + "）");
});

step("②之二 全文只许有一处「完」，且必须在最后（中缝出现假结束行，基底会当整份先验到此为止）", () => {
  const ends = s.match(/^# SDE-FT-Skill v[\d.]+ 完/gm) || [];
  ok(ends.length === 1, "「# SDE-FT-Skill vX 完」只出现一次，实得 " + ends.length + " 次");
  const last = s.lastIndexOf("# SDE-FT-Skill");
  ok(s.slice(last).length < 400, "那一行确实在文末（其后剩 " + s.slice(last).length + " 字符）");
  const vers = Array.from(new Set((s.match(/# SDE-FT-Skill v([\d.]+)/g) || [])));
  ok(vers.length === 1 || new Set(vers.map(v => v.match(/v([\d.]+)/)[1])).size === 1,
     "抬头与收口的版本号一致：" + vers.join(" / "));
  ok(!/全 Skill 的(总)?收口/.test(s), "没有小节自称「全 Skill 的收口」而后面还有内容");
});

step("③ 123 原理必须是三条，不是一条", () => {
  ok(/原理一\s+D\s*×\s*E\s*矛盾\s*→\s*S\s*改变/.test(s), "原理一 D×E→S 在");
  ok(/原理二\s+S\s*×\s*E\s*矛盾\s*→\s*D\s*改变/.test(s), "原理二 S×E→D 在");
  ok(/原理三\s+S\s*×\s*D\s*矛盾\s*→\s*E\s*改变/.test(s), "原理三 S×D→E 在");
  ok(s.indexOf("被驱动的那一样不是固定的") > 0, "写明被驱动项每一轮都在换（这是原文只画一条时的病根）");
});

step("④ 第七部分：两条撞法并存，且分岔写在最前", () => {
  const i72 = s.indexOf("### 7.2 先分清你手上有几个对立点");
  const i75 = s.indexOf("### 7.5 二阶碰撞六步");
  const i76 = s.indexOf("### 7.6 三种碰撞型");
  ok(i72 > 0, "7.2 分岔节在");
  ok(i75 > i72, "六步（一个对立点）排在分岔之后");
  ok(i76 > i75, "三种碰撞型（三个对立点）排在六步之后");
  ok(/7\.4[①③⑤⑥]/.test(s) === false, "旧的 7.4① 式回指已随小节顺移一并改净");
});

step("⑤ 三种碰撞型齐备，且各自的共有前提都写了", () => {
  ok(s.indexOf("三维度碰撞") > 0, "三维度型在");
  ok(s.indexOf("三路径碰撞") > 0, "三路径型在");
  ok(s.indexOf("三原理碰撞") > 0, "三原理型在");
  ok(s.indexOf("可由某一维单独读出") > 0, "三维度型的共有前提在");
  ok(s.indexOf("可由一个目标方向单独结算") > 0, "三路径型的共有前提在");
  ok(s.indexOf("驱动的方向是固定的") > 0, "三原理型的共有前提在");
  ok(/E 为目标[\s\S]{0,120}S 为目标[\s\S]{0,120}D 为目标/.test(s), "六路径按终点分成的三组写明");
});

step("⑥ 共有前提三步与它的两条硬纪律", () => {
  ok(s.indexOf("三家争的是") > 0, "第一步：把争论写成同一个句式");
  ok(s.indexOf("这还用说吗") > 0, "第二步的验收句（念给三家听三家都会说这还用说吗）");
  ok(s.indexOf("必须来自三家之一自己") > 0, "第三步：推翻材料必须来自三家之一自己");
  ok(s.indexOf("只是加入了争论") > 0, "写明外搬理由＝只是加入争论，没有取消争论");
  ok(s.indexOf("不是三家的综合") > 0, "收口：新典范不是三家的综合");
});

step("⑦ 三件验收（命题形状 / 零情态词 / 反向约束）", () => {
  ok(s.indexOf("也不是 Y₃") > 0, "三重否定命题形状（三个 Y）");
  ok(s.indexOf("零情态词判据") > 0, "零情态词判据在");
  ok(s.indexOf("五个答案必须互不相同") > 0, "零情态词判据的五场景验收");
  ok(s.indexOf("我原本会写下哪一句更强的话") > 0, "反向约束的验收问句");
  ok(s.indexOf("问题结构的影子") > 0, "三家为什么到不了：不写成缺陷");
});

step("⑧ 选源的两个陷阱都写了", () => {
  ok(s.indexOf("那是辩论,不是碰撞") > 0 || s.indexOf("那是辩论，不是碰撞") > 0, "同位置＝辩论不是碰撞");
  ok(s.indexOf("把应用场景当成一家") > 0, "场景冒充一家");
  ok(s.indexOf("静态断言冒充动力机制") > 0, "三原理型专属陷阱：静态断言冒充动力机制");
});

step("⑨ v3.7：三条原理各自都是三步（回写不能漏）", () => {
  ok(s.indexOf("某两个维度矛盾 → 第三个改变 → 这个改变回写前两个 → 下一轮由谁先动") > 0, "三步一般形式写全");
  ok(/原理二\s+S\s*×\s*E\s*矛盾\s*→\s*D\s*改变\s*→\s*新路径回写\s*S\s*与\s*E/.test(s), "原理二的回写在");
  ok(/原理三\s+S\s*×\s*D\s*矛盾\s*→\s*E\s*改变\s*→\s*新条件场回写\s*S\s*与\s*D/.test(s), "原理三的回写在");
  ok(s.indexOf("回写是\"下一轮谁先动\"的**唯一来源**") > 0, "写明回写是「下一轮谁先动」的唯一来源");
});

step("⑩ v3.7：题型三分 What/How/Why 在选源之前，且落位没写反", () => {
  const i760 = s.indexOf("#### 7.6.0 先定题型");
  const i761 = s.indexOf("#### 7.6.1 选源的唯一硬判据");
  ok(i760 > 0, "7.6.0 题型判别节在");
  ok(i761 > i760, "题型判别排在选源判据之前");
  ok(s.indexOf("判据不是疑问词,是答案的形状") > 0, "判据＝答案的形状，不是疑问词");
  ok(s.indexOf("产物**一律不落在**它三个对立点里的任何一个上") > 0, "写明产物不落在任何一个对立点上");
  ok(s.indexOf("不许说\"What 落在 S、How 落在 D、Why 落在 E\"") > 0, "错误落位被明写为禁止");
  ok(s.indexOf("配错型不会报错,只会悄悄降级") > 0, "配错型只降级不报错这条写了");
});

step("⑪ v3.7：三原理型的单因锁定三条", () => {
  ok(s.indexOf("单因锁定") > 0, "单因锁定在");
  ok(s.indexOf("三者共同作用") > 0 && s.indexOf("当场作废") > 0, "禁「其中一个因素／三者共同作用」，出现即作废");
  ok(s.indexOf("我这条驱动在什么情形下反而是被驱动的") > 0, "每家须自曝一处（＝推翻材料的接口）");
  ok(s.indexOf("不许写\"未找到\"") > 0, "本型第三步不许交白卷");
});

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
