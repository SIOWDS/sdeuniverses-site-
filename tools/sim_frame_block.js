#!/usr/bin/env node
/* sim_frame_block.js —— ChatSDE 1.1「解构卡与解构回写」注入模拟（2026-09-10）
 *
 * 查三件事：
 *   ① SDE_FRAME_BLOCK 定义得出来（真能求值成字符串，不是语法过了但拼错）
 *   ② ChatSDE 主对话路（prof 为 null / 无 term）拿得到它
 *   ③ 改姓分身档（prof.term 为真）**拿不到**它——卡与「格」是母体词，
 *      漏进去等于前脚改姓后脚灌回（LANG_TRIAD_BLOCK 那两块的原始理由）
 *
 * 跑法：node tools/sim_frame_block.js
 */
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'src', 'worker.js');
const src = fs.readFileSync(SRC, 'utf8');

let bad = 0;
const ok = (cond, msg) => {
  console.log((cond ? '  ok   ' : '  FAIL ') + msg);
  if (!cond) bad++;
};

// —— 抽一个 `const NAME = "..." + "..." ;` 形式的常量并求值 ——
function evalConst(name) {
  const start = src.indexOf('const ' + name + ' =');
  if (start < 0) throw new Error(name + ' 没找到');
  // 从定义处起，找到第一个位于行首缩进之外的 `";` —— 本文件里这类常量都以 `";` 收尾
  const end = src.indexOf('";\n', start);
  if (end < 0) throw new Error(name + ' 找不到结尾');
  const code = src.slice(start, end + 2);
  // eslint-disable-next-line no-new-func
  return new Function(code + '\nreturn ' + name + ';')();
}

console.log('— ① 常量求值 —');
let FRAME, TRIAD, LANG;
try {
  FRAME = evalConst('SDE_FRAME_BLOCK');
  TRIAD = evalConst('SDE_TRIAD_BLOCK');
  LANG = evalConst('LANG_TRIAD_BLOCK');
  ok(typeof FRAME === 'string' && FRAME.length > 400, 'SDE_FRAME_BLOCK 求值成字符串，长度 ' + FRAME.length);
  ok(typeof TRIAD === 'string' && TRIAD.length > 3000, 'SDE_TRIAD_BLOCK 未被改坏，长度 ' + TRIAD.length);
} catch (e) {
  ok(false, '常量求值抛错：' + e.message);
  process.exit(1);
}

console.log('— ② 三件功能的硬句子都在 —');
[
  ['解构卡', '解构卡'],
  ['开场亮一次（一场一张）', '一场亮一次'],
  ['读数结算这一行', '这个读数结算'],
  ['承重句编号', '本场第 N 条'],
  ['作废条件落到可查记录', '若观察到什么，本条作废'],
  ['写不出承重句要明说', '没有落下承重句'],
  ['改格判据＝落不出可结算读数', '落不出可结算的读数'],
  ['三轮无读数回头看卡', '连着三轮'],
  ['改格三件套·走死在哪', '原解构走死在哪一步'],
  ['改格三件套·新卡', '新的解构是什么'],
  ['改格三件套·搬承重句', '搬到新卡的哪个位置'],
  ['不许说你问错了', '「你这个问题问错了」不许说'],
  ['走死一条路也是产出', '本身就是这一场的产出'],
  ['反模板·别演', '别演'],
].forEach(([label, needle]) => ok(FRAME.indexOf(needle) >= 0, label));

console.log('— ③ 注入分流 —');
// 复刻 system 组装处那一行的表达式
const pick = (prof) => ((prof && prof.term) ? LANG : TRIAD) + ((prof && prof.term) ? '' : FRAME);

const sysChat = pick(null);                    // ChatSDE 本人
const sysChat2 = pick({ id: 'health' });       // 别的分身，但没 term（不改姓）
const sysLang = pick({ id: 'lang', term: true }); // 改姓档

ok(sysChat.indexOf('解构卡') >= 0, 'ChatSDE 主路拿到解构卡块');
ok(sysChat.indexOf('先判这一问属于哪一类') >= 0, 'ChatSDE 主路仍保有判类块');
ok(sysChat.indexOf('解构卡') > sysChat.indexOf('先判这一问属于哪一类'), '解构卡排在判类块之后（它是那一节的延伸）');
ok(sysChat2.indexOf('解构卡') >= 0, '无 term 的分身档也拿到（与判类块同待遇）');
ok(sysLang.indexOf('解构卡') < 0, '改姓档（term）未被污染');
ok(sysLang.indexOf('本场第 N 条') < 0, '改姓档拿不到承重句编号格式');

console.log('— ④ 源码里的注入点 —');
ok(/\+ \(\(prof && prof\.term\) \? "" : SDE_FRAME_BLOCK\)/.test(src), 'system 组装处已独立一行注入 FRAME');
ok(/\+ \(\(prof && prof\.term\) \? LANG_TRIAD_BLOCK : SDE_TRIAD_BLOCK\)/.test(src), '判类块那一行一字未动（sim_wds_triad 钉着它）');
ok((src.match(/SDE_FRAME_BLOCK/g) || []).length === 2, 'SDE_FRAME_BLOCK 恰好出现两次（定义 + 注入）');

console.log(bad === 0 ? '\nALL PASS' : '\n' + bad + ' FAILED');
process.exit(bad === 0 ? 0 : 1);
