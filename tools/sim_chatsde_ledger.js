#!/usr/bin/env node
/* 记分牌护栏（2026-08-23）
   抠 wds-mode.js 里 ledgerStrip / ledgerTake / ledgerAudit 的原文 eval 真跑（不复制代码），
   再对服务端那条规格与页面接线下静态断言。
   变异检验：M_JS=/tmp/wm.led.before.js node tools/sim_chatsde_ledger.js 应当变红。 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const M = fs.readFileSync(process.env.M_JS || path.join(ROOT, 'public/wds-mode.js'), 'utf8');
const W = fs.readFileSync(process.env.W_JS || path.join(ROOT, 'src/worker.js'), 'utf8');

let pass = 0, fail = 0;
const ok = (c, n, x) => { if (c) pass++; else { fail++; console.log('  ✗ ' + n + (x ? '  ← ' + x : '')); } };

// ---- 抠函数真跑 ----
let F = null;
try {
  const a = M.indexOf('var LEDGER_RE =');
  const b = M.indexOf('  function ledgerRender(cell, led, body)');
  F = new Function(M.slice(a, b) + '\n; return { strip: ledgerStrip, take: ledgerTake, audit: ledgerAudit, empty: ledgerEmpty };')();
} catch (e) { ok(false, '这一族函数能独立跑起来', e.message); }

const BODY = '拖延不是懒。心理学里有「意志力耗竭」的说法，行为经济学里有「双曲贴现」，'
  + '但两者讲的都是当下更划算。换到工程上的**备用传力路径**看：催促本身就是那条备用路径，'
  + '撤掉催促，这件事就换了性质。若观察到撤掉催促后拖延强度不变，本判断作废。';
const LINE = '〔交账〕已有说法：意志力耗竭；双曲贴现 ｜ 外领域：备用传力路径 ｜ 作废条件：若观察到撤掉催促后拖延强度不变，本判断作废 ｜ 新在：拖延不是懒，而是被催促这条备用路径养住的';

if (F) {
  console.log('\n【一】剥账（这一行绝不许进历史/成文稿/PDF）');
  const full = BODY + '\n\n' + LINE;
  ok(F.strip(full) === BODY, '剥干净且不动正文', JSON.stringify(F.strip(full).slice(-30)));
  ok(F.strip(BODY) === BODY, '没有账时原样返回');
  ok(F.strip(BODY + '\n【交账】已有说法：甲；乙') === BODY, '方头括号也认');
  ok(F.strip('').length === 0, '空文本不炸');
  // 流式中途只吐出半行账，也不许把半行留在正文里
  ok(F.strip(BODY + '\n〔交账〕已有说') === BODY, '半行账同样剥掉');

  console.log('【二】解析');
  const led = F.take(full);
  ok(!!led, '取得出账');
  ok(led.stock.length === 2 && led.stock[0] === '意志力耗竭', '已有说法按分号切开', JSON.stringify(led.stock));
  ok(led.field === '备用传力路径', '外领域', led.field);
  ok(/本判断作废$/.test(led.falsify), '作废条件吃到该字段末尾（不越过竖线）', led.falsify);
  ok(led.newness.indexOf('而是') > 0, '新在', led.newness);
  ok(led.body === BODY, 'body 是剥净的正文');
  ok(F.take(BODY) === null, '没交账回 null（分身档属正常）');

  console.log('【三】核对：只信自报＝让它自己发证书');
  const a1 = F.audit(led, BODY);
  ok(a1.stockOk && a1.stockN === 2, '两个说法都能在正文里找到', a1.stockN + '');
  ok(a1.fieldOk, '外领域在正文里真出现过');
  ok(a1.falOk, '作废条件是真条件句');
  ok(a1.newOk && !a1.newTold, '新在已填');
  // 交空账：账上有、正文里没有
  const fake = F.take(BODY + '\n〔交账〕已有说法：张三定律；李四效应 ｜ 外领域：量子力学 ｜ 作废条件：无 ｜ 新在：很有新意');
  const a2 = F.audit(fake, BODY);
  ok(a2.stockN === 0 && !a2.stockOk, '正文里找不到的说法按未做算', a2.stockN + '');
  ok(!a2.fieldOk, '正文里没出现的外领域按未做算');
  ok(!a2.falOk, '作废条件写「无」＝未做');
  // 只有一个说法
  const one = F.take(BODY + '\n〔交账〕已有说法：意志力耗竭 ｜ 外领域：无 ｜ 作废条件：无 ｜ 新在：无（只到复述）');
  const a3 = F.audit(one, BODY);
  ok(!a3.stockOk, '只摆一个说法不算过（至少两个）');
  ok(a3.newTold && !a3.newOk, '如实写「只到复述」＝申报，不是失败');
  // 假的作废条件：一句怎么都对的话
  const soft = F.take(BODY + '\n〔交账〕已有说法：意志力耗竭；双曲贴现 ｜ 外领域：备用传力路径 ｜ 作废条件：需要更多研究来验证 ｜ 新在：x');
  ok(!F.audit(soft, BODY).falOk, '「需要更多研究」不算作废条件');

  console.log('【四】不许自评分数漏进账里');
  ok(!/分数|打分|评分/.test(LINE), '示例账里没有分数字段');
}

console.log('【五】服务端那条规格');
ok(/const SDE_METHOD_LEDGER/.test(W), '规格常量在');
ok(/〔交账〕已有说法：/.test(W), '格式逐字给出');
ok(/已有说法至少两个/.test(W), '要求至少两个已有说法');
ok(/正文里也必须出现过/.test(W), '写明账上的东西正文里必须有');
ok(/不许在这一行里给自己打分/.test(W), '交账里禁止自评分数');
ok(/如实写「无」不丢人，编一个才丢人/.test(W), '留了如实申报的出路');
ok(/SDE_METHOD_SETTLE\s*\n\s*\+ SDE_METHOD_LEDGER;/.test(W), '标准档装了交账');
ok(/SDE_METHOD_SETTLE\s*\n\s*\+ SDE_METHOD_LEDGER\s*\n\s*\+ "\\n输出要求/.test(W), '深度档装了交账');

console.log('【六】页面接线');
ok(/var _led = ledgerTake\(answer\);/.test(M), 'finish 里先取账');
/* ⚠ 这条最初写成「indexOf(A) < indexOf(B)」，把剥账那一行整句删掉时 indexOf 回 -1，
   -1 小于任何下标 ⇒ 断言照样绿。**次序断言必须先断言「它在」**，否则删掉它反而更容易过。 */
{
  const iStrip = M.indexOf('if (_led) answer = _led.body;');
  const iHist = M.indexOf('history.push({ role: "wds", text: answer })');
  ok(iStrip > 0, '剥账那一行在');
  ok(iStrip > 0 && iHist > 0 && iStrip < iHist, '剥账排在入 history 之前（否则漏进成文稿与 PDF）');
}
ok(/if \(_led\) ledgerRender\(cell, _led, answer\);/.test(M), '摆记分牌');
ok(/mdRender\(ledgerStrip\(answer\)\)/.test(M), '流式渲染也剥（不让读者看它一个字一个字冒出来）');
ok(/cell\.turn\.appendChild\(box\); cell\.ledger = box;/.test(M), '记分牌挂在正文之外（不进导出稿）');
ok(/ledH: "这一答走了几步"/.test(M) && /ledH: "STEPS TAKEN"/.test(M), '中英文案都有');
ok(/\.wdsm-led \.lc\.no\{/.test(M), '未做那一格有单独样式');
ok(/\.wdsm-led \.lc\.nu\{/.test(M), '如实申报那一格是中性样式，不标红');

console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' PASS / ' + fail + ' FAIL\n');
process.exit(fail ? 1 : 0);
