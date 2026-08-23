#!/usr/bin/env node
/* 中华智问 · 第一刀护栏（2026-08-23）
   口径：能真跑的就真跑（从页面里抠函数原文 eval，不复制一份代码），
   只能静态钉的（提示词、script 标签）就逐条钉死。
   变异检验：ZW_HTML=<变异页> node tools/sim_zhiwen_fix1.js  应当变红。 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const ZW = process.env.ZW_HTML || path.join(ROOT, 'public/taste/zhiwen/index.html');
const H = fs.readFileSync(ZW, 'utf8');

let pass = 0, fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; }
  else { fail++; console.log('  ✗ ' + name + (extra ? '  ← ' + extra : '')); }
}
function has(s, name) { ok(H.indexOf(s) >= 0, name, '页面里找不到：' + s.slice(0, 48)); }
function hasNot(s, name) { ok(H.indexOf(s) < 0, name, '页面里还留着：' + s.slice(0, 48)); }
function grab(re, label) {
  const m = H.match(re);
  if (!m) { fail++; console.log('  ✗ 抠不出 ' + label); return null; }
  return m[0];
}

console.log('\n【一】C1 · docx 本地兜底（CDN 一断不许全哑）');
has('<script src="/taste/assets/docx-8.5.0.umd.js"></script>', 'C1 本地脚本已引');
ok(fs.existsSync(path.join(ROOT, 'public/taste/assets/docx-8.5.0.umd.js')), 'C1 本地副本在仓库里');
{
  const p = path.join(ROOT, 'public/taste/assets/docx-8.5.0.umd.js');
  if (fs.existsSync(p)) {
    const code = fs.readFileSync(p, 'utf8');
    ok(code.length > 300000, 'C1 本地副本不是空壳', code.length + ' 字节');
    const m = { exports: {} };
    try {
      new Function('exports', 'module', code)(m.exports, m);
      ok(typeof m.exports.Packer === 'function' && typeof m.exports.Document === 'function',
        'C1 本地副本真能 eval 出 Document/Packer');
    } catch (e) { ok(false, 'C1 本地副本可 eval', e.message); }
  }
}
ok(/if\(typeof docx==="undefined"\)\{document\.write/.test(H), 'C1 本地拿不到时才回落 CDN');
// 四页同一处缺陷一起修
['idea-generator', 'confluence', 'paradigm-forge'].forEach(n => {
  const p = path.join(ROOT, 'public/taste/' + n + '/index.html');
  const t = fs.readFileSync(p, 'utf8');
  ok(t.indexOf('/taste/assets/docx-8.5.0.umd.js') >= 0, 'C1 兄弟页也改了：' + n);
});

console.log('【二】C1b/C2 · 导出守卫与下载（真跑）');
has("if(typeof docx === 'undefined' || !docx.Packer)", 'C1b saveDocx 有守卫');
has('Word 组件未能加载', 'C1b 守卫如实报错');
has("saveText(filename.replace(/\\.docx$/,'') + '.md'", 'C1b 给 .md 退路');
hasNot("a.href=url; a.download=filename; a.click();\n  URL.revokeObjectURL(url);", 'C2 旧的「点完就撤」已清干净');
{
  const src = grab(/function _dl\(blob, filename\)\{[\s\S]*?\n\}/, '_dl');
  if (src) {
    const calls = [];
    const fakeA = { click() { calls.push('click'); }, remove() { calls.push('remove'); }, style: {} };
    const sandbox = {
      URL: { createObjectURL: () => { calls.push('create'); return 'blob:x'; },
             revokeObjectURL: () => { calls.push('revoke'); } },
      document: { createElement: () => fakeA, body: { appendChild: () => calls.push('append') } },
      setTimeout: (fn, ms) => { calls.push('timer:' + ms); },
    };
    const fn = new Function('URL', 'document', 'setTimeout', src + '; return _dl;')(
      sandbox.URL, sandbox.document, sandbox.setTimeout);
    fn({}, 'a.docx');
    ok(calls.indexOf('append') >= 0 && calls.indexOf('append') < calls.indexOf('click'),
      'C2 <a> 先入文档再 click', calls.join(','));
    ok(calls.indexOf('revoke') < 0, 'C2 click 同一帧不撤 objectURL', calls.join(','));
    ok(calls.some(c => /^timer:(\d+)$/.test(c) && +c.split(':')[1] >= 10000),
      'C2 撤销推迟到至少 10 秒后', calls.join(','));
  }
}

console.log('【三】D1 · 评分口径归一（触发计数只作区间参考）');
{
  // 页面里凡出现「148-152」这张分档表的地方，附近都必须有归一口径
  const idx = [];
  let i = -1;
  while ((i = H.indexOf('148-152', i + 1)) >= 0) idx.push(i);
  ok(idx.length >= 5, 'D1 分档表至少五处（确认没数漏）', '实为 ' + idx.length + ' 处');
  let bare = 0;
  idx.forEach(p => {
    const win = H.slice(Math.max(0, p - 900), p + 300);
    if (!/只定区间参考|只用来定区间参考|区间参考/.test(win)) bare++;
  });
  ok(bare === 0, 'D1 没有一处分档表还在当主要标尺', '裸表 ' + bare + ' 处');
  has('最终分必须由五维', 'D1 五维优先写明');
  hasNot(' 按【触发条件满足数】给分:', 'D1 旧口径「按满足数给分」已清');
  hasNot('**满足条件数 → 智商分**:', 'D1 旧口径「满足条件数→智商分」已清');
}

console.log('【四】A2 · 空响应分死法（真跑判据）');
has('「0 字」有三种死法', 'A2 注释在位');
{
  const seg = H.slice(H.indexOf('  if(!acc){'), H.indexOf('  if(!acc){') + 1400);
  ok(/thinkChars > 0/.test(seg), 'A2 先问有没有思考痕迹');
  ok(/思考把 token 预算吃光/.test(seg), 'A2 点名真凶是预算被思考吃光');
  ok(/这才轮到查 Key/.test(seg), 'A2 干净的空才归咎 Key');
  ok(seg.indexOf('可能是 Key 未开通该模型服务、额度不足或被安全策略拦截）</span>') < 0,
    'A2 旧的「一律赖 Key」文案已换掉');
}

console.log('【五】A1a · 关思考开关（真跑八家×两档）');
{
  const src = grab(/\/\/ plain=true[\s\S]*?\nfunction buildPayload\(sel, systemPrompt, userQ, maxTokens, plain\)\{[\s\S]*?\n\}\n/, 'buildPayload');
  if (src) {
    const pm = grab(/function parseModel\([\s\S]*?\n\}/, 'parseModel');
    const build = new Function(pm + '\n' + src + '\n; return buildPayload;')();
    const b = (sel, plain) => build(sel, 'sys', 'q', 60000, plain);
    // 默认（不传 plain）：行为必须与从前一字不差
    ok(b('ds:pro').thinking.type === 'enabled', 'A1a 默认档 ds:pro 仍开思考');
    ok(b('ds:pro').reasoning_effort === 'xhigh', 'A1a 默认档 ds:pro 仍 xhigh');
    ok(b('glm:pro').thinking.type === 'enabled', 'A1a 默认档 glm:pro 仍开思考');
    ok(b('qwen:pro').enable_thinking === true, 'A1a 默认档 qwen:pro 仍开思考');
    ok(b('gpt:pro').reasoning_effort === 'high', 'A1a 默认档 gpt:pro 仍 high');
    // plain=true：该关的关掉
    ok(b('ds:pro', true).thinking.type === 'disabled', 'A1a plain 关掉 ds 思考');
    ok(b('ds:pro', true).reasoning_effort === undefined, 'A1a plain 同时撤掉 reasoning_effort');
    ok(b('glm:pro', true).thinking.type === 'disabled', 'A1a plain 关掉 glm 思考');
    ok(b('qwen:pro', true).enable_thinking === false, 'A1a plain 关掉 qwen 思考');
    ok(b('gpt:pro', true).reasoning_effort === 'low', 'A1a plain 把 gpt 压到最低');
    // Kimi / MiniMax 无开关：什么都不许加
    const k = b('kimi:pro', true), mm = b('minimax:pro', true);
    ok(k.thinking === undefined && k.enable_thinking === undefined, 'A1a plain 不给 kimi 塞非法字段');
    ok(mm.thinking === undefined && mm.enable_thinking === undefined, 'A1a plain 不给 minimax 塞非法字段');
    // claude / gemini 走各自的 return，不受影响
    ok(b('claude:pro', true).system === 'sys', 'A1a claude 结构未被 plain 破坏');
    ok(b('gemini:pro', true).generationConfig !== undefined, 'A1a gemini 结构未被 plain 破坏');
    ok(b('qwen:pro', true).max_tokens === 8192, 'A1a 千问 8192 硬顶仍在');
  }
  has('async function streamChat(apiKey, model, systemPrompt, userQ, bodyEl, statusEl, metaEl, colEl, maxTokens, plain)',
    'A1a streamChat 收 plain');
  has('buildPayload(model, systemPrompt, userQ, maxTokens, plain)', 'A1a streamChat 把 plain 透传下去');
}

console.log('【六】D2 · 第〇步不许悄悄降级');
has('两次都没写出正文，碰撞已中止', 'D2 硬停在位');
has('s0.el, 16000, true)', 'D2 重试是「降到 16000 + 关思考」');
// 注意：只钉「活的状态文案」——那句记述历史的注释留着是对的，别误伤
hasNot("s0.st.textContent='⚠ 返回为空，退回无方向盘撞法'", 'D2 旧的「空了就降级」状态文案已清');
hasNot('退回原来的无方向盘撞法，不让一道新工序毁掉整条产线', 'D2 旧的「失败不阻断」口径注释已改');
{
  const seg = H.slice(H.indexOf('let step0 = ' + "''"), H.indexOf("const s1 = mkBlock(collisionPanel"));
  ok(/if\(!step0\)\{[\s\S]*?throw new Error/.test(seg), 'D2 空 step0 一定抛错，不往下走');
  ok(seg.indexOf('16000, true') < seg.indexOf('throw new Error'), 'D2 先救一次再停，不是上来就停');
}

console.log('【七】没有误伤');
has('const PAPER_TOKENS = 60000;', '未动论文预算（那是第二刀的事）');
has('const COLLIDE_TOKENS = 60000;', '未动碰撞预算');
has('function collideP0(q, A, B, C)', '第〇步本体还在');
has('第④步 · 最近邻攻击', '最近邻攻击未被挤掉');
has('第⑥步', '盲区涌现未被挤掉');

console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' PASS / ' + fail + ' FAIL\n');
process.exit(fail ? 1 : 0);
