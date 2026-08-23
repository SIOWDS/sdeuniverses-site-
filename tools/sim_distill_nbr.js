#!/usr/bin/env node
/* 「成文前先做一次占位者实搜」护栏（2026-08-23）
   抠 distNbrUsage 原文 eval 真跑，再对 distill 里的接线下位置断言。
   变异检验：W_JS=/tmp/w.nbr.before.js node tools/sim_distill_nbr.js 应当变红。 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const W = fs.readFileSync(process.env.W_JS || path.join(ROOT, 'src/worker.js'), 'utf8');

let pass = 0, fail = 0;
const ok = (c, n, x) => { if (c) pass++; else { fail++; console.log('  ✗ ' + n + (x ? '  ← ' + x : '')); } };
const at = (s) => W.indexOf(s);

console.log('\n【一】用法块（真跑两种形态）');
{
  const src = (W.match(/function distNbrUsage\(hasList\) \{[\s\S]*?\n\}/) || [''])[0];
  ok(!!src, '抠得出 distNbrUsage');
  if (src) {
    const f = new Function(src + '; return distNbrUsage;')();
    const yes = f(true), no = f(false);
    ok(/至少三位要出自上面这份名单/.test(yes), '有名单时：至少三位出自名单');
    ok(/近三年正是你自己记忆最薄的那一段/.test(yes), '写明名单是来补最近三年那一段的');
    ok(/按〔未核验〕写/.test(no), '没名单时：按未核验写');
    ok(/不许拿记忆里的老经典充数/.test(no), '没名单时禁止用老经典充数');
    ok(/据我所知尚无人提出/.test(no), '禁止「据我所知尚无人提出」式自我发证');
    [yes, no].forEach((t, i) => {
      const w = i ? '无名单' : '有名单';
      ok(/只准从上面这份名单或站内资料里照抄/.test(t), w + '·网址只准照抄（治编造 URL）');
      ok(/一个字符都不许自己拼/.test(t), w + '·不许自己拼网址');
      ok(/共纳入 N 件材料/.test(t) && /要么把那份清单真的写出来/.test(t), w + '·不许声称一份没写出来的清单');
      ok(/一句可核验而为假的话/.test(t), w + '·点破这类错的性质');
    });
  }
}

console.log('【二】只在该跑的档上跑');
ok(/const DIST_NBR_KINDS = \{ essay: 1, paper: 1, paper1: 1, outline: 1, wechat: 1 \}/.test(W),
  '白名单＝提炼成文/两档论文/提纲/公众号');
['report', 'poem', 'notice', 'letter', 'deck'].forEach((k) => {
  const seg = (W.match(/const DIST_NBR_KINDS = \{[^}]*\}/) || [''])[0];
  ok(seg.indexOf(k + ':') < 0, '不在白名单里：' + k + '（那些档盘最近邻是噪声）');
});

console.log('【三】只跑一次 · 种子取读者第一问');
ok(/if \(_distNbrP\) return _distNbrP;/.test(W), '惰性且只跑一次（提纲与各节共用）');
ok(/turns\.find\(\(t\) => t && t\.role !== "wds"/.test(W), '种子取读者自己的第一问');
ok(/String\(_t0\.text \|\| b\.title \|\| ""\)/.test(W), '没有第一问时退回标题');
ok(/nbrChain\(env, _seed, \(rvendor === "glm" \? KEY : ""\), convo\.slice\(0, 20000\)\)/.test(W),
  '走既有专用链；glm 用读者自己的 Key，否则回落管理员 Key');
ok(/\.catch\(\(\) => null\)/.test(W), '搜索失败不炸（成文是正菜，这是配菜）');

console.log('【四】三处都真的接上了（算了不接＝白搜）');
ok(/const psys = BASE \+ NBRB \+/.test(W), '提纲那一趟接上了');
ok(/const ssys = BASE \+ NBRB \+/.test(W), '正文各趟接上了');
ok(/\+ await \(async \(\) => \{\s*\n\s*const nc = await distNbrGet\(\);/.test(W), '一趟出全篇那一路接上了');
ok(at('const NBRB = distNbrBlock(_nbrDist);') > 0 && at('const NBRB = distNbrBlock(_nbrDist);') < at('const psys = BASE + NBRB'),
  'NBRB 先算后用');

console.log('【五】失败必须可见');
ok((W.match(/已先做一次站外占位者检索：召回/g) || []).length === 2, '两条路都把召回条数报给读者');
ok(/覆盖不足：/.test(W), '覆盖不足要说清是哪一种');
ok(/多半是没有可用的搜索 Key/.test(W), '一条没召回时点出最可能的原因');
/* ⚠ 聊天那一路也有一处 `t:"web", v: nc.items`（9874 行），按正则数会数到 3 条。
   要数的是**成文这两处**，所以判据落在成文段内（从 distill 路由起到文件末尾）。 */
{
  const dseg = W.slice(W.indexOf('url.pathname === "/api/wds/distill"'));
  ok((dseg.match(/t: "web", v: (nc|_nbrDist)\.items/g) || []).length === 2,
    '成文两条路都把来源卡发给前端');
}

console.log('【六】没误伤既有的链');
ok(/const wantNbr = \(rs && rs\.forge && FORGE_NBR_STAGES\[rs\.i \| 0\]\) \|\| tool === "iq"/.test(W),
  '聊天/评分那一路的敌意最近邻判据没被动过');
ok(/function nbrChainBlock\(res\)/.test(W), 'nbrChainBlock 仍是唯一那一份（没复制第二份）');
ok(/④ \*\*上面没有的作者与年份一个都不许写\*\*/.test(W), '通用四条纪律还在（本刀只补成文特有的三条）');

console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' PASS / ' + fail + ' FAIL\n');
process.exit(fail ? 1 : 0);
