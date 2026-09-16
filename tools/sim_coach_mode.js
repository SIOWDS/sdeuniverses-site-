#!/usr/bin/env node
/* sim_coach_mode.js —— ChatSDE 陪练档 / 第四格 / 运动手环（2026-09-16 王德生令·理念艺术家原则）
 *
 * 钉五件事：
 *   ① 两块常量真能求值；母体版有七条硬句子；改姓版一个母体词都没有
 *   ② 服务端只认明确信号（缺省＝代劳档），且只在「非工序／非无SDE／非对撞」时挂，改姓档挂改姓版
 *   ③ 挂在 extras 上且 extras 排在工序之后、术语闸之前（后面的字压前面的字）
 *   ④ 前端：陪练钮三处齐（标记／文案／点击）、请求体带 coach、与无 SDE 互斥
 *   ⑤ 前端：第四格「我自己想问的」不发东西只聚焦；按钮问记 btn、打字问记 own、换新对话清零
 * 跑法：node tools/sim_coach_mode.js
 */
const fs = require('fs'), path = require('path');
const W = fs.readFileSync(path.join(__dirname, '..', 'src', 'worker.js'), 'utf8');
const F = fs.readFileSync(path.join(__dirname, '..', 'public', 'wds-mode.js'), 'utf8');
let bad = 0, n = 0;
const ok = (c, m) => { n++; console.log((c ? '  ok   ' : '  FAIL ') + m); if (!c) bad++; };
function evalConst(src, name) {
  const st = src.indexOf('const ' + name + ' =');
  if (st < 0) throw new Error(name + ' 没找到');
  const en = src.indexOf('";\n', st);
  return new Function(src.slice(st, en + 2) + '\nreturn ' + name + ';')();
}

console.log('— ① 常量 —');
let CO, CP;
try { CO = evalConst(W, 'SDE_COACH_BLOCK'); CP = evalConst(W, 'COACH_BLOCK_PLAIN'); }
catch (e) { ok(false, '求值抛错：' + e.message); process.exit(1); }
ok(CO.length > 600 && CO.length < 1600, '母体版长度合理：' + CO.length);
ok(CP.length > 300 && CP.length < 900, '改姓版长度合理：' + CP.length);
[
  ['成败看读者自己说出判断', '用自己的话说出一句他原来说不出的判断'],
  ['先让他亮卡', '先让他亮卡'],
  ['两张卡并排碰', '把你的卡摆在旁边'],
  ['承重句先由他写、不替他写定', '不要替他写定'],
  ['他要直接答就照办＋复述', '用自己的话复述一遍'],
  ['护住他自己的词', '护住他自己的词'],
  ['卡住只给最小提示', '只给最小的一个提示'],
  ['带回生活', '带回生活'],
  ['交账不把自己的判断记他名下', '不许把你自己的判断记在他名下'],
  ['压住解构卡出场顺序', '一律让位于本节'],
  ['不是苦行、可随时关', '随时可以关掉陪练档'],
].forEach(([m, k]) => ok(CO.indexOf(k) >= 0, '母体版·' + m));
['SDE', '解构卡', '承重句', '交账', 'S=', '三方程', '六路径'].forEach(w => ok(CP.indexOf(w) < 0, '改姓版不含母体词「' + w + '」'));
ok(CP.indexOf('不要替他写定') >= 0 && CP.indexOf('复述一遍') >= 0, '改姓版保住核心两条');

console.log('— ② 服务端开关 —');
ok(/const coach = \(b\.coach === 1 \|\| b\.coach === "1" \|\| b\.coach === true\);/.test(W), '只认明确信号，缺省＝代劳');
const inj = W.indexOf('if (coach && !tool && !noSde && !duel) {');
ok(inj > 0, '挂载条件＝非工序／非无SDE／非对撞');
const injBody = W.slice(inj, inj + 400);
ok(injBody.indexOf('(prof && prof.term) ? COACH_BLOCK_PLAIN : SDE_COACH_BLOCK') >= 0, '改姓档挂改姓版');
ok(injBody.indexOf('extras +=') >= 0, '挂在 extras 上');
const call = W.indexOf('const sys = WDS_CHAT_SYS(reflect, SDEM,');
ok(inj > 0 && call > inj && call - inj < 1200, '挂载发生在 WDS_CHAT_SYS 调用之前且紧邻');

console.log('— ③ system 次序：工序 < extras < 术语闸 —');
const fn = W.slice(W.indexOf('function WDS_CHAT_SYS('), W.indexOf('const SDE_LEXICON ='));
const iTool = fn.indexOf('+ wdsToolSys(tool, prof, rung)');
const iExt = fn.indexOf('+ (extras || "")');
const iTerm = fn.lastIndexOf('+ (prof && prof.term ? prof.term : "")');
ok(iTool > 0 && iExt > 0 && iTerm > 0, '三个锚都在（先断言在，再比次序）');
ok(iTool < iExt && iExt < iTerm, 'extras 在工序之后、术语闸之前');

console.log('— ④ 前端陪练钮 —');
ok(F.indexOf("<button class='wdsm-mode' data-k='coach'></button>") >= 0, '标记在档位条里');
ok(/mCoach: "\\u270b 陪练"/.test(F) && /mCoach: "\\u270b Coach"/.test(F), '中英文案齐');
ok(F.indexOf('else if (k === "coach") {') >= 0, '点击分支在');
ok(/\(k === "coach"\) \? coachOn/.test(F), '点亮态跟 coachOn');
ok(F.indexOf('coach: coachOn ? 1 : undefined') >= 0, '主对话请求体带 coach（关时不发字段）');
ok(F.indexOf('if (coachOn && noSdeOn) { noSdeOn = false;') >= 0, '开陪练关无SDE');
ok(F.indexOf('if (noSdeOn && coachOn) { coachOn = false;') >= 0, '开无SDE关陪练');
ok(F.indexOf('coachOn = localStorage.getItem(LS_COACH) === "1";') >= 0, '默认代劳档');

console.log('— ⑤ 第四格与运动手环 —');
const rf = F.slice(F.indexOf('function renderFollows('), F.indexOf('// —— 朗读'));
ok(rf.indexOf('t("ownAsk")') >= 0, '第四格在追问框里');
const ownClick = rf.slice(rf.indexOf('own.onclick'), rf.indexOf('own.onclick') + 140);
ok(ownClick.indexOf('focus()') >= 0 && ownClick.indexOf('send(') < 0, '第四格只聚焦、不发东西');
ok((rf.match(/SEND_VIA = "btn"/g) || []).length === 2, '三条追问与「一起问」都记作按钮');
const sd = F.slice(F.indexOf('function send(forceQ)'), F.indexOf('function send(forceQ)') + 900);
ok(sd.indexOf('if (SEND_VIA === "btn") { askStats.btn++; askRun++; }') >= 0, '按钮问记 btn');
ok(sd.indexOf('else if (forceQ == null) { askStats.own++; askRun = 0; }') >= 0, '打字问记 own，并清连点计数');
ok(sd.indexOf('SEND_VIA = "";') > sd.indexOf('askStats.own++'), '记完即清来源标记（取 Key 回调不重记）');
ok((F.match(/history = \[\]; askReset\(\);/g) || []).length === 2, '两处新对话都清零');
ok(rf.indexOf('askRun >= 3') >= 0 && rf.indexOf('t("ownNudge")') >= 0, '连点三轮只提示');

// 行为小跑：把计数逻辑抠出来模拟一场
(function () {
  let askStats = { own: 0, btn: 0 }, askRun = 0, SEND_VIA = "";
  function count(forceQ) { if (SEND_VIA === "btn") { askStats.btn++; askRun++; } else if (forceQ == null) { askStats.own++; askRun = 0; } SEND_VIA = ""; }
  count(null); SEND_VIA = "btn"; count("q1"); SEND_VIA = "btn"; count("q2"); SEND_VIA = "btn"; count("q3");
  count("取Key后回调");
  ok(askStats.own === 1 && askStats.btn === 3 && askRun === 3, '模拟一场：own=1 btn=3 连点=3（回调未重记）');
  count(null);
  ok(askRun === 0 && askStats.own === 2, '自己打一问后连点清零');
})();

console.log('\n' + (n - bad) + ' passed, ' + bad + ' failed');
process.exit(bad ? 1 : 0);
