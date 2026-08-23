#!/usr/bin/env node
/* 「每一答的使命＝用三件工具做出创新」护栏（2026-08-23）
   抠 worker.js 里那三个常量原文 eval 真跑（不复制一份代码）。
   变异检验：W_JS=/tmp/w.mission.before.js node tools/sim_chatsde_mission.js 应当变红。 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const W = process.env.W_JS || path.join(ROOT, 'src/worker.js');
const S = fs.readFileSync(W, 'utf8');

let pass = 0, fail = 0;
const ok = (c, n, x) => { if (c) pass++; else { fail++; console.log('  ✗ ' + n + (x ? '  ← ' + x : '')); } };

// ---- 抠出四个常量真跑 ----
let B = null;
try {
  const a = S.indexOf('const SDE_METHOD_MISSION');
  const b = S.indexOf('\n\n\n/* ═══════════ 三类问题', a);
  B = new Function(S.slice(a, b) + '\n; return { MISSION: SDE_METHOD_MISSION, SETTLE: SDE_METHOD_SETTLE, STOCK: SDE_METHOD_STOCK, DEEP: SDE_METHOD_BLOCK, LITE: SDE_METHOD_LITE };')();
} catch (e) { ok(false, '这一族常量能独立跑起来', e.message); }

if (B) {
  console.log('\n【一】使命：不是走工序，是长出新分辨');
  [B.DEEP, B.LITE].forEach((blk, i) => {
    const w = i ? '标准档' : '深度档';
    ok(/长出这一问之前不存在的一条分辨/.test(blk), w + '·写明使命是长出新分辨');
    ok(/解释清楚只是及格线/.test(blk), w + '·把「讲清楚」降为及格线');
    ok(/不是要展示的知识/.test(blk), w + '·工具是手段不是展品');
  });

  console.log('【二】三件工具都在，且三原理是三条不是一条');
  [['DEEP', '深度档'], ['LITE', '标准档']].forEach(([k, w]) => {
    const blk = B[k];
    ok(/S=F\(D,E\)/.test(blk) && /D=G\(S,E\)/.test(blk) && /E=H\(S,D\)/.test(blk), w + '·三大方程三条齐');
    ok(/六路径/.test(blk), w + '·六路径在');
    ok(/原理一 D×E/.test(blk) && /原理二 S×E/.test(blk) && /原理三 S×D/.test(blk), w + '·三原理三条齐');
    ok(/回写/.test(blk), w + '·回写被点名');
  });
  ok(/三缸机当单缸开/.test(B.DEEP), '深度档保留「只会用原理一＝三缸机当单缸开」这条警告');

  console.log('【三】结算是硬要求，且允许诚实申报');
  ok(/这一答新在哪/.test(B.SETTLE), '答完先自问「这一答新在哪」');
  ok(/X 不是 Y，而是 Z/.test(B.SETTLE), '给出最锋利的形状');
  ok(/还没撞出新东西/.test(B.SETTLE), '撞不出来准许如实说');
  ok(/不许临时造一个漂亮名字充数/.test(B.SETTLE), '禁止伪发生充数');
  ok(B.DEEP.indexOf(B.SETTLE) >= 0 && B.LITE.indexOf(B.SETTLE) >= 0, '两档共用同一份结算条款（单一定义处）');

  console.log('【四】三条禁令');
  ok(/这属于 E 维」不是回答/.test(B.SETTLE), '禁止拿工具名当答案');
  ok(/不许把矛盾抹平/.test(B.SETTLE), '禁止抹平矛盾');
  ok(/不许漏掉回写/.test(B.SETTLE), '禁止漏回写');

  console.log('【五】精简版真的短（每轮都要付的固定成本）');
  ok(B.LITE.length < B.DEEP.length, '精简版短于全量版', B.LITE.length + ' vs ' + B.DEEP.length);
  // 2026-08-23 抬到 1300：精简版又装进了「先清家底」那一步（+504 字）。
  // 抬这个数要有理由——它是每轮都付的固定成本，不是随手放宽的。
  ok(B.LITE.length < 1300, '精简版控制在 1300 字以内', B.LITE.length + ' 字');
  ok(B.DEEP.indexOf('意义三律') >= 0 && B.LITE.indexOf('意义三律') < 0, '意义三律等只留深度档');
}

console.log('【六】先清家底（穷尽基底的家底与记忆库）');
if (B) {
  ok(/先清家底，再谈新/.test(B.STOCK), '有这一步');
  ok(/这一步不许跳过/.test(B.STOCK), '写成硬要求，不是建议');
  ok(/站内资料/.test(B.STOCK) && /你自己的记忆库/.test(B.STOCK) && /本场已经说过的/.test(B.STOCK),
    '三样家底齐（站内资料／基底记忆／本场已说）');
  ok(/两三个已有的说法/.test(B.STOCK), '至少摆出两三个已有说法');
  ok(/跨至少两个不同学科/.test(B.STOCK), '要求跨学科（同一学科三个说法常是同一个）');
  ok(/从哪一处开始分岔/.test(B.STOCK), '逐个说清分离线');
  ok(/想不起来只说明你没想起来，不等于没人说过/.test(B.STOCK), '想不起来≠没人说过');
  ok(/绝不编造出处、年份、书名/.test(B.STOCK), '宁缺勿造（这一步是造假入口）');
  ok(/已经有人说过，叫 X/.test(B.STOCK), '发现已被说过时准许直说，且算好答案');
  ok(B.DEEP.indexOf(B.STOCK) >= 0 && B.LITE.indexOf(B.STOCK) >= 0, '两档都装了清家底（单一定义处）');
  ok(B.DEEP.indexOf(B.STOCK) < B.DEEP.indexOf('S=F(D,E)'), '清家底排在三件工具之前');
  ok(/相对家底里的哪几个说法而新/.test(B.SETTLE), '结算要说清相对谁而新');
}

console.log('【七】装配：非分身档每一轮都注入');
ok(/\(\(prof && prof\.term\) \? "" : \(deep \? SDE_METHOD_BLOCK : SDE_METHOD_LITE\)\)/.test(S),
  '深度走全量、标准走精简、分身不注入');
ok(!/\(deep && !\(prof && prof\.term\)\) \? SDE_METHOD_BLOCK : ""/.test(S), '旧的「只有深度档才有」已清');
ok(/LANG_TRIAD_BLOCK : SDE_TRIAD_BLOCK/.test(S), '判类工序块的分身分流没被动过');

console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' PASS / ' + fail + ' FAIL\n');
process.exit(fail ? 1 : 0);
