// SDE · Key 有效性检测（共享模块 + 四页接线）的模拟验证
// 一半是对共享模块跑真行为（jsdom 假 DOM + 假 fetch），一半是对四张真实页面下静态断言。
const fs = require('fs');
const { JSDOM } = require(process.env.JSDOM_PATH || 'jsdom');

const ROOT = require('path').join(__dirname, '..', 'public', 'taste') + '/';
const MOD = fs.readFileSync(ROOT + 'assets/sde-keyprobe.js', 'utf8');
let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  PASS ' + name); }
  else { fail++; console.log('  FAIL ' + name + (extra ? ' :: ' + extra : '')); }
}

// ── 装模块到一个假页面里 ──
function boot(html) {
  const dom = new JSDOM('<!doctype html><body>' + html + '</body>', { runScripts: 'outside-only' });
  const w = dom.window;
  w.eval(MOD);
  return w;
}
const W = boot('<div><input id="k1"><select id="s1"><option value="ds:pro">a</option><option value="gpt:pro">b</option><option value="off">c</option></select></div>');
const KP = W.SDEKeyProbe;

console.log('\n【一】判档：只有"这个 Key 本身不能用"才准报 ✗');
const V = (s, b) => KP.verdict(s, b);
ok('200 → ok', V(200, '{"choices":[]}').level === 'ok');
ok('401 → bad', V(401, '{"error":{"message":"Authentication Fails"}}').level === 'bad');
ok('403 → bad', V(403, 'forbidden').level === 'bad');
ok('402 余额不足 → warn 且写明 Key 有效', V(402, '').level === 'warn' && V(402, '').msg.indexOf('有效') > 0);
ok('insufficient balance 文案也认', V(400, '{"error":{"message":"Insufficient Balance"}}').level === 'warn');
ok('中文"余额不足"也认', V(400, '{"msg":"账户余额不足"}').level === 'warn');
ok('429 → warn', V(429, 'rate limit').level === 'warn');
ok('404 型号不可用 → warn', V(404, 'model not found').level === 'warn');
ok('model_not_found → warn', V(400, '{"error":{"code":"model_not_found"}}').level === 'warn');
ok('400 且提到 api key → bad', V(400, '{"error":{"message":"Invalid API-key provided"}}').level === 'bad');
ok('5xx → warn 且说明不是你的 Key', V(500, '').level === 'warn' && V(500, '').msg.indexOf('不是你的 Key') > 0);
ok('MiniMax 1004 裹在 200 里 → bad', V(200, '{"base_resp":{"status_code":1004}}').level === 'bad');
ok('MiniMax 1008 → warn', V(200, '{"base_resp":{"status_code":1008}}').level === 'warn');
ok('MiniMax 0 → ok', V(200, '{"base_resp":{"status_code":0}}').level === 'ok');
ok('Anthropic 200 里裹 error → 不误报 ok', V(200, '{"type":"error","error":{"message":"x"}}').level === 'warn');
ok('响应体不是 JSON 不炸', V(200, '<html>').level === 'ok');
ok('空/未定义响应体不炸', V(401, '').level === 'bad' && V(200, null).level === 'ok');
ok('未知状态带原文且截断', V(418, 'x'.repeat(5000)).level === 'warn' && V(418, 'teapot').msg.indexOf('teapot') > 0 && V(418, 'x'.repeat(5000)).msg.length < 200);

console.log('\n【二】探测请求：又小、不思考、不流式');
const T = KP.PROBE_TOKENS;
function realPayload(vendor, tier) { // 仿四页 buildPayload 的形状
  const b = { stream: true, messages: [{ role: 'system', content: 's' }, { role: 'user', content: 'q' }], max_tokens: 60000 };
  if (vendor === 'ds') { b.model = 'deepseek-v4-pro'; b.thinking = { type: 'enabled' }; b.reasoning_effort = 'xhigh'; }
  if (vendor === 'glm') { b.model = 'glm-5'; b.thinking = { type: 'enabled' }; }
  if (vendor === 'qwen') { b.model = 'qwen3.7-max'; b.enable_thinking = true; b.max_tokens = 8192; }
  if (vendor === 'minimax') { b.model = 'MiniMax-M3'; b.reasoning_split = true; b.max_tokens = 131072; }
  if (vendor === 'gpt') { b.model = 'gpt-5.5'; b.max_completion_tokens = 60000; delete b.max_tokens; b.reasoning_effort = 'high'; }
  if (vendor === 'claude') return { model: 'claude-opus-4-8', max_tokens: 60000, stream: true, system: 's', messages: [{ role: 'user', content: 'q' }] };
  if (vendor === 'gemini') return { systemInstruction: { parts: [{ text: 's' }] }, contents: [{ role: 'user', parts: [{ text: 'q' }] }], generationConfig: { maxOutputTokens: 60000, temperature: 0.7 } };
  return b;
}
['ds', 'glm', 'kimi', 'qwen', 'minimax', 'gpt', 'claude', 'gemini'].forEach(v => {
  const p = KP.shrink(realPayload(v, 'pro'), v + ':pro');
  const cap = p.max_tokens != null ? p.max_tokens : (p.max_completion_tokens != null ? p.max_completion_tokens : p.generationConfig.maxOutputTokens);
  ok(v + ' 预算压到 ' + T, cap === T, 'cap=' + cap);
  const think = (p.thinking && p.thinking.type === 'enabled') || p.enable_thinking === true || ('reasoning_effort' in p) || ('reasoning_split' in p);
  ok(v + ' 思考/推理档已关', !think);
  ok(v + ' 不走流式', p.stream !== true);
});
ok('shrink 保住 claude 的 system 形状', !!KP.shrink(realPayload('claude'), 'claude:pro').system);
ok('shrink 保住 gemini 的 contents 形状', Array.isArray(KP.shrink(realPayload('gemini'), 'gemini:pro').contents));
ok('gemini 探测温度归零', KP.shrink(realPayload('gemini'), 'gemini:pro').generationConfig.temperature === 0);
ok('qwen 探测不受 8192 影响', KP.shrink(realPayload('qwen'), 'qwen:pro').max_tokens === T);
ok('shrink 不炸在 null 上', KP.shrink(null, 'ds:pro') === null);

console.log('\n【三】注入与接线（真 DOM）');
const hooks = {
  buildPayload: (sel) => realPayload(sel.split(':')[0]),
  chatHeaders: (sel, k) => ({ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + k }),
  apiUrl: () => 'https://example.com/v1',
  isOverseas: (sel) => sel.indexOf('gpt') === 0,
  proxyUrl: '/api/llm-proxy'
};
const n = KP.attach([{ key: 'k1', sel: 's1' }, { key: 'nope', sel: 's1' }, { key: 'k1', sel: 'zzz' }], hooks);
ok('只给存在的框装，缺元素静默跳过', n === 1);
const btn = W.document.getElementById('sdekp-btn-k1');
const msg = W.document.getElementById('sdekp-msg-k1');
ok('按钮已注入且紧跟输入框', !!btn && W.document.getElementById('k1').nextSibling === btn);
ok('结论位紧跟按钮', !!msg && btn.nextSibling === msg);
ok('样式只注入一次', W.document.querySelectorAll('#sdekp-css').length === 1);
ok('结论位在 flex 行里自己占一行', /\.sdekp-msg\{[^}]*flex-basis:100%/.test(MOD));
{ // at 选择器：挂到祖先容器末尾，不插进不换行的 flex 行里
  const W2 = boot('<div class="key-card"><div class="key-row"><input id="dk"><button class="key-toggle">显示</button></div><div class="key-hint">h</div></div>');
  W2.SDEKeyProbe.attach([{ key:'dk', model:'ds:pro', at:'.key-card' }], hooks);
  const b2 = W2.document.getElementById('sdekp-btn-dk');
  ok('at 落位：钮挂到 .key-card 末尾而不是挤进 key-row', !!b2 && b2.parentNode.className === 'key-card' && W2.document.querySelector('.key-row').children.length === 2);
}
ok('重复 attach 不重复装钮', KP.attach([{ key: 'k1', sel: 's1' }], hooks) === 0 && W.document.querySelectorAll('#sdekp-btn-k1').length === 1);

(async () => {
  const doc = W.document, input = doc.getElementById('k1'), sel = doc.getElementById('s1');
  let seen = null;
  W.fetch = async (url, opt) => { seen = { url, opt }; return { status: 200, text: async () => '{"choices":[]}' }; };
  W.AbortController = function () { this.signal = {}; this.abort = () => { }; };

  input.value = ''; btn.click(); await new Promise(r => setTimeout(r, 5));
  ok('空 Key 直接拦下、不发请求', msg.className.indexOf('bad') > 0 && seen === null);

  input.value = 'sk-x'; sel.value = 'ds:pro'; btn.click(); await new Promise(r => setTimeout(r, 20));
  ok('国内基底直连 apiUrl', seen && seen.url === 'https://example.com/v1');
  ok('带上 Bearer 头', seen.opt.headers.Authorization === 'Bearer sk-x');
  ok('发出去的是压小过的 payload', JSON.parse(seen.opt.body).max_tokens === T);
  ok('200 → 绿字', msg.className.indexOf('ok') > 0, msg.className + ' | ' + msg.textContent);
  ok('按钮已恢复可点', btn.disabled === false && btn.textContent.indexOf('检测') >= 0);

  sel.value = 'gpt:pro'; input.value = 'sk-y'; btn.click(); await new Promise(r => setTimeout(r, 20));
  ok('境外基底走中转', seen.url === '/api/llm-proxy');

  sel.value = 'off'; btn.click(); await new Promise(r => setTimeout(r, 5));
  ok('off/follow 席位给提示不发请求', msg.textContent.indexOf('主基底') > 0);

  seen = null;
  W.fetch = async () => { const e = new Error('boom'); throw e; };
  sel.value = 'ds:pro'; input.value = 'sk-z'; btn.click(); await new Promise(r => setTimeout(r, 20));
  ok('网络挂了不炸、报 warn', msg.className.indexOf('warn') > 0 && btn.disabled === false);

  W.fetch = async () => ({ status: 402, text: async () => 'Insufficient Balance' });
  btn.click(); await new Promise(r => setTimeout(r, 20));
  ok('402 显示为黄字而不是红字', msg.className.indexOf('warn') > 0 && msg.className.indexOf('bad') < 0);

  input.dispatchEvent(new W.Event('input'));
  ok('改 Key 即清掉旧结论', msg.textContent === '');
  msg.textContent = 'x'; sel.dispatchEvent(new W.Event('change'));
  ok('换基底即清掉旧结论', msg.textContent === '');

  console.log('\n【四】四张真实页面');
  const PAGES = {
    'zhiwen': { keys: ['apiKey', 'evalKey', 'evalKey2'], sels: ['modelSel', 'evalSel', 'evalSel2'], overseas: true },
    'idea-generator': { keys: ['apiKey', 'osKey', 'osRevAKey', 'osRevBKey', 'osbKey', 'osbRevAKey', 'osbRevBKey', 'fourRevAKey', 'fourRevBKey', 'reviewKeyInputA', 'reviewKeyInputB', 'writerKeyInput'], sels: ['modelSel', 'osModel', 'osRevA', 'osRevB', 'osbModel', 'osbRevA', 'osbRevB', 'fourRevA', 'fourRevB', 'reviewModelSelA', 'reviewModelSelB', 'writerModelSel'], overseas: true },
    'classics-deconstructor': { keys: ['apiKey', 'reviewKey1', 'reviewKey2', 'assessKey'], sels: ['modelSel', 'reviewModelSel1', 'reviewModelSel2', 'assessModelSel'], overseas: true },
    'iq-scorer': { keys: ['dsKey', 'glmKey'], sels: [], overseas: false, at: true }
  };
  for (const [page, spec] of Object.entries(PAGES)) {
    const h = fs.readFileSync(ROOT + page + '/index.html', 'utf8');
    console.log('  -- ' + page);
    ok(page + ' 引了共享模块', /<script src="\/taste\/assets\/sde-keyprobe\.js\?v=1"><\/script>/.test(h));
    ok(page + ' 模块在 attach 之前（同步、非 defer）', h.indexOf('sde-keyprobe.js') < h.indexOf('SDEKeyProbe.attach') && !/sde-keyprobe\.js[^>]*defer/.test(h));
    ok(page + ' 有 chatHeaders 且真跑也用它', /function chatHeaders\(/.test(h) && /headers:\s*chatHeaders\(|const headers = chatHeaders\(/.test(h));
    ok(page + ' 全页只有一份头构造', (h.match(/function chatHeaders\(/g) || []).length === 1);
    if (spec.overseas) ok(page + ' 中转目标只剩 chatHeaders 里那 4 处', (h.match(/x-target-url/g) || []).length === 4, '实际 ' + (h.match(/x-target-url/g) || []).length);
    // 名单里的 id 必须在页面里真的存在（打字错了这里当场抓）
    const listBlock = h.slice(h.indexOf('SDEKeyProbe.attach'), h.indexOf('SDEKeyProbe.attach') + 1400);
    const listedKeys = (listBlock.match(/key:'([A-Za-z0-9_]+)'/g) || []).map(s => s.slice(5, -1));
    const listedSels = (listBlock.match(/sel:'([A-Za-z0-9_]+)'/g) || []).map(s => s.slice(5, -1));
    ok(page + ' 名单条数对得上（' + spec.keys.length + '）', listedKeys.length === spec.keys.length, '实际 ' + listedKeys.length);
    ok(page + ' 名单里的 Key 框都真的存在', listedKeys.every(k => new RegExp('id="' + k + '"').test(h)), listedKeys.filter(k => !new RegExp('id="' + k + '"').test(h)).join(','));
    ok(page + ' 名单里的基底下拉都真的存在', listedSels.every(s => new RegExp('id="' + s + '"').test(h)), listedSels.filter(s => !new RegExp('id="' + s + '"').test(h)).join(','));
    ok(page + ' 一个 Key 框都没漏', spec.keys.every(k => listedKeys.indexOf(k) >= 0), spec.keys.filter(k => listedKeys.indexOf(k) < 0).join(','));
    ok(page + ' 装不上也不许影响跑批（try 包住）', /catch\(e\)\{ \/\* 检测是附加件/.test(h));
    if (spec.at) ok(page + ' 用 at 落位避开不换行的 flex 行', /at:'\.key-card'/.test(h));
  }
  // 中华智问的内联老实现必须清干净（否则两套逻辑并存、日后各改各的）
  const zw = fs.readFileSync(ROOT + 'zhiwen/index.html', 'utf8');
  ok('zhiwen 内联 probeVerdict 已清', zw.indexOf('function probeVerdict(') < 0);
  ok('zhiwen 内联 buildProbePayload 已清', zw.indexOf('buildProbePayload') < 0);
  ok('zhiwen 内联 runKeyProbe 已清', zw.indexOf('runKeyProbe') < 0);
  ok('zhiwen 旧按钮与旧样式已清', zw.indexOf('class="kbtn"') < 0 && zw.indexOf('.kmsg{') < 0);
  ok('模块里写了 ?v= 的 bump 提醒', /bump 各页/.test(MOD));

  console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
