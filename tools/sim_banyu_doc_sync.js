#!/usr/bin/env node
/* 「成文 · PPT」说明页与 app 的对账（2026-08-23）
   缘起：app 里今天新加了剧本与应用文五档，说明页 /banyu/chatsde/ 还停在旧清单——
   功能加了、说明页没跟上，读者（明天是一百位小学老师）按说明页找不到那几档。
   这类漂移不会报错，只会让人以为「没有这个功能」。
   判据：app 的 KIND_DEF 与 DECK_TPL 是唯一事实源，说明页必须覆盖到它们。
   变异检验：改回旧清单应当变红。 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const CL = fs.readFileSync(process.env.M_JS || path.join(ROOT, 'public/wds-mode.js'), 'utf8');
const SV = fs.readFileSync(path.join(ROOT, 'src/worker.js'), 'utf8');
const DOC = fs.readFileSync(process.env.DOC_HTML || path.join(ROOT, 'public/banyu/chatsde/index.html'), 'utf8');

let pass = 0, fail = 0;
const ok = (c, n, x) => { if (c) pass++; else { fail++; console.log('  ✗ ' + n + (x ? '  ← ' + x : '')); } };

// ---- 事实源①：客户端档位表 ----
const kindSeg = CL.slice(CL.indexOf('var KIND_DEF'), CL.indexOf('\n  ];', CL.indexOf('var KIND_DEF')));
const kinds = [...kindSeg.matchAll(/k: *"([a-z0-9]+)"/g)].map((m) => m[1]);
// ---- 事实源②：两侧模板表必须一致 ----
const svSeg = SV.slice(SV.indexOf('const DECK_TPL = {'), SV.indexOf('\n};', SV.indexOf('const DECK_TPL = {')));
const svTpl = [...svSeg.matchAll(/\n  ([a-z0-9]+): *\{/g)].map((m) => m[1]);
const clSeg = CL.slice(CL.indexOf('var DECK_TPLS = ['), CL.indexOf('\n  ];', CL.indexOf('var DECK_TPLS = [')));
const clTpl = [...clSeg.matchAll(/id: *"([a-z0-9]+)"/g)].map((m) => m[1]);

console.log('\n【一】两侧模板表对账（改一边不改另一边＝选得到、写不出）');
ok(svTpl.length === 20, '服务端 20 套模板', svTpl.length + ' 套');
ok(clTpl.length === svTpl.length && svTpl.every((x) => clTpl.includes(x)),
  '客户端模板与服务端逐个对上', '服务端多出：' + svTpl.filter((x) => !clTpl.includes(x)).join(',')
  + ' / 客户端多出：' + clTpl.filter((x) => !svTpl.includes(x)).join(','));

console.log('【二】说明页覆盖到 app 的每一档');
// 档位 → 说明页上应当出现的词（用界面上的正式名，别自造）
const NAME = {
  report: '对话报告', essay: '提炼成文', paper1: '两万字论文', paper: '两万字论文',
  outline: '写作提纲', sumdoc: '总结你载入的那篇文章', deck: 'PPT',
  wechat: '公众号文章', prose: '散文', story: '短篇小说', script: '剧本', poem: '诗歌',
  notice: '通知公告', plan: '方案策划', summary: '总结述职', speech: '讲话致辞', letter: '函件邮件',
};
kinds.forEach((k) => {
  const n = NAME[k];
  ok(!!n, '档位 ' + k + ' 在对照表里有名字（新加档要同时补这里与说明页）');
  if (n) ok(DOC.indexOf(n) >= 0, '说明页写到了「' + n + '」（' + k + '）');
});

console.log('【三】说明页的课件四步还在');
['点顶栏 ✎ 成文 · PPT', '教学讲义', '培训课件', '家校沟通', '存为 .pptx'].forEach((s) => {
  ok(DOC.indexOf(s) >= 0, '说明页仍写着「' + s + '」');
});
ok(!/另外还有十几种/.test(DOC), '模板数不再写成含糊的「十几种」');

console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' PASS / ' + fail + ' FAIL\n');
process.exit(fail ? 1 : 0);
