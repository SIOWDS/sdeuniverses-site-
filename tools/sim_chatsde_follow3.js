#!/usr/bin/env node
/* ChatSDE 追问建议「三件工具各出一问」护栏（2026-08-23）
   做法：从 src/worker.js 里**抠原文 eval**（不复制一份代码，复制的那份对了不算数）。
   变异检验：W_JS=/tmp/worker.before.js node tools/sim_chatsde_follow3.js  应当变红。 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const W = process.env.W_JS || path.join(ROOT, 'src/worker.js');
const M = process.env.M_JS || path.join(ROOT, 'public/wds-mode.js');
const src = fs.readFileSync(W, 'utf8');
const mjs = fs.readFileSync(M, 'utf8');

let pass = 0, fail = 0;
const ok = (c, n, x) => { if (c) pass++; else { fail++; console.log('  ✗ ' + n + (x ? '  ← ' + x : '')); } };

// ---- 抠出这一族的常量与两个函数，放进一个沙盒里真跑 ----
function cut(startMark, endMark, label) {
  const a = src.indexOf(startMark);
  const b = src.indexOf(endMark, a);
  if (a < 0 || b < 0) { fail++; console.log('  ✗ 抠不出 ' + label); return ''; }
  return src.slice(a, b);
}
const body = cut('const SDE_PATHS =', 'async function followUps', 'followSys/parseFollows 段')
           + cut('async function followUps', '\n\n// ===== 联网搜索', 'followUps 段');
let SB = null;
try {
  SB = new Function('llmText', 'WDS_FOLLOW_MS',
    body + '\n; return { followSys, parseFollows, SDE_PATHS, SDE_EQUATIONS, SDE_PRINCIPLES };')(
    async () => '', 12000);
} catch (e) { ok(false, '这一族代码能独立跑起来', e.message); }

if (SB) {
  const S = SB.followSys({});               // 主站档
  const SL = SB.followSys({ term: 1 });     // 分身档（语言/健康）

  console.log('\n【一】提示词：三件工具各一条、What/How/Why 各一');
  ok(/三条必须各用一件不同的工具/.test(S), '写明三条各用一件不同工具');
  ok(/What[^\n]*三大方程/.test(S), 'What 绑三大方程');
  ok(/How[^\n]*六路径/.test(S), 'How 绑六路径');
  ok(/Why[^\n]*三原理/.test(S), 'Why 绑三原理');
  ok(S.indexOf('S=F(D,E)') >= 0 && S.indexOf('D=G(S,E)') >= 0 && S.indexOf('E=H(S,D)') >= 0,
    '三大方程三条都在');
  ok(S.indexOf('原理一') >= 0 && S.indexOf('原理二') >= 0 && S.indexOf('原理三') >= 0, '三原理三条都在');
  ok((S.match(/S→D→E|S→E→D|D→S→E|D→E→S|E→S→D|E→D→S/g) || []).length >= 6, '六路径六条都在');
  ok(/第一行 What、第二行 How、第三行 Why，顺序不许换/.test(S), '钉死行序');
  ok(/万能句/.test(S), '仍禁万能句');

  console.log('【二】改姓纪律：分身档里一个内部术语都不许出现');
  ['S=F(D,E)', 'D=G(S,E)', 'E=H(S,D)', 'S→D→E', 'E→D→S', '三大方程', '六路径', '三原理', '纠缠', '显露态', '差异序列']
    .forEach((t) => ok(SL.indexOf(t) < 0, '分身档不出现「' + t + '」'));
  ok(/是什么/.test(SL) && /怎么做|从哪下手|怎么走/.test(SL) && /为什么/.test(SL), '分身档仍讲清三种问法');

  console.log('【三】解析（真跑）');
  const good = 'What·S=F(D,E)｜这个判断是经哪条路长出来的\n'
             + 'How·咨询与干预｜照这样排下去第一步该改什么\n'
             + 'Why·原理二｜是什么逼得原来那条路改了道';
  const r = SB.parseFollows(good, {});
  ok(r.length === 3, '三行都收下', JSON.stringify(r));
  ok(r[0].p === 'What' && r[1].p === 'How' && r[2].p === 'Why', '类型按行序落位');
  ok(r[0].q === '这个判断是经哪条路长出来的', '问句取到竖线右边');
  ok(r[0].w.indexOf('S=F(D,E)') === 0, '第一行认出方程名', r[0].w);
  ok(r[1].w === '咨询与干预', '第二行认出路径名', r[1].w);
  ok(r[2].w.indexOf('原理二') === 0, '第三行认出原理名', r[2].w);

  // 宽容：漏分隔符 / 带编号 / 类型写成中文 / 工具名瞎写
  const messy = '1. 这个说法最先动的是哪一样\n2）How｜这一步具体怎么落到课上\n三、Why·原理九｜为什么它一直卡在这儿';
  const r2 = SB.parseFollows(messy, {});
  ok(r2.length === 3, '格式脏也照样给三条', JSON.stringify(r2));
  ok(r2[0].p === 'What' && r2[2].p === 'Why', '缺类型时按行序补');
  ok(r2[0].w === '', '认不出工具名就留空，不许标错');
  ok(r2[2].w === '', '瞎写的「原理九」不许被认成真工具');

  // 边界：太短、太长、空
  ok(SB.parseFollows('', {}).length === 0, '空输入回空');
  ok(SB.parseFollows('What·x｜太短\nHow·y｜' + '长'.repeat(50), {}).length === 0, '太短太长都丢掉');
  const r3 = SB.parseFollows(good + '\nWhat·多余｜这一条不该被收下', {});
  ok(r3.length === 3, '最多只取三条');

  // 分身档的类型标签也必须改姓
  const r4 = SB.parseFollows(good, { term: 1 });
  ok(r4[0].p === '是什么' && r4[1].p === '怎么做' && r4[2].p === '为什么', '分身档标签是中文白话',
    r4.map((x) => x.p).join('/'));
}

console.log('【四】预算与前端接线');
ok(/460, WDS_FOLLOW_MS/.test(src), '预算抬到 460（三行各多带一个工具名）');
ok(/短截止（WDS_FOLLOW_MS）/.test(src), '短截止的理由注释还在');
ok(/const fs = await followUps\(fVC, KEY, q, outText, lang, prof\)/.test(src), '调用点没被动过');
ok(/tag\.title = w \|\| t\("pathTip"\)/.test(mjs), '前端把工具名挂进 tooltip');
ok(/String\(item\.w \|\| ""\)/.test(mjs), '前端读 w 字段');
ok(mjs.indexOf('兼容两种形状') >= 0, '前端「老形状也认」的兼容说明还在');

console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' PASS / ' + fail + ' FAIL\n');
process.exit(fail ? 1 : 0);
