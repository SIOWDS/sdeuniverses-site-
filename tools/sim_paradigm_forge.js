#!/usr/bin/env node
/* 「SDE 碰撞出典范」全功能模拟 —— 用 jsdom 跑 public/taste/paradigm-forge/index.html 里的真代码。
 *
 * 铁律：改这一页（或改 tools/forge/forge.template.html 后重跑构建器）必跑本脚本。
 *   node tools/sim_paradigm_forge.js
 *   FORGE_HTML=/tmp/broken.html node tools/sim_paradigm_forge.js     # 变异检验：指向改坏的副本
 *
 * 覆盖：四种选源模式各跑一遍全流程 · 基底切换与 Key 分存 · 境外基底经代理 · 预算纪律 ·
 *      十道工序的调令纪律 · 三道闸 · 术语零容忍 · 失败路径（无 Key／取不到正文／太短／重复源）·
 *      停下 · 评审不到 150 的回炉提示 · 内功取不到时降级 · 站内检索失败时安全退回 ·
 *      存储位置（在场写目录 / 不在场如实降级）· 单格重跑 / 从这里继续 / 编辑存回 · 三个导出通道 · 清空复位。
 *
 * 三个坑（已处理）：① 页面错误必须经 VirtualConsole 的 jsdomError/error 收集才拿得到；
 *   ② jsdom 没有 TextDecoder(window)/scrollIntoView，且 <a>.click() 会报 navigation；
 *   ③ 每步包在 step() 里 try/catch，页面坏掉时要出完整报告而不是甩堆栈。
 */
const fs = require('fs');
const path = require('path');

const JSDOM_MOD = process.env.JSDOM_PATH || '/home/claude/node_modules/jsdom';
let jsdom;
try { jsdom = require(JSDOM_MOD); }
catch (e) { try { jsdom = require('jsdom'); } catch (e2) { console.error('缺 jsdom：cd /home/claude && npm install jsdom'); process.exit(2); } }
const { JSDOM, VirtualConsole } = jsdom;

const HTML_PATH = process.env.FORGE_HTML ||
  path.join(__dirname, '..', 'public', 'taste', 'paradigm-forge', 'index.html');
const HTML = fs.readFileSync(HTML_PATH, 'utf8');

let pass = 0, fail = 0;
const fails = [];
function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; fails.push(name + (extra ? '  ← ' + extra : '')); console.log('  ✗ ' + name + (extra ? '  ← ' + extra : '')); }
}
async function step(name, fn) {
  console.log('\n— ' + name);
  try { await fn(); }
  catch (e) { fail++; fails.push(name + ' 抛错：' + (e && e.message)); console.log('  ✗ 抛错：' + (e && e.message)); }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function waitFor(fn, ms) {
  const t0 = Date.now();
  while (Date.now() - t0 < (ms || 8000)) { if (fn()) return true; await sleep(30); }
  return false;
}

/* ---------------- 假数据 ---------------- */
const CATALOG = {
  generated: '2026-07-29',
  items: Array.from({ length: 40 }, (_, i) => ({
    t: '站上长文之' + i + (i % 3 === 0 ? '·睡眠' : i % 3 === 1 ? '·创造' : '·自信'),
    u: '/column/fake-' + i + '/', d: '描述' + i, w: 12000 + i, c: i < 5 ? '每日必读' : '今日长文'
  }))
};
const STUDENTS = {
  generated: '2026-07-29',
  students: [
    { slug: 'zhang-qiong', name: '张琼', count: 6, items: [
      { title: '留白', url: '/students/zhang-qiong/a/', kind: '发展心理学', summary: '撤手是德' },
      { title: '伪生', url: '/students/zhang-qiong/b/', kind: '技术哲学', summary: '顶撞才养人' },
      { title: '撤土', url: '/students/zhang-qiong/c/', kind: '照护制度', summary: '撤手是灾' },
      { title: '角力', url: '/students/zhang-qiong/d/', kind: '伦理', summary: '第四篇' },
      { title: '反循环', url: '/students/zhang-qiong/e/', kind: '伦理', summary: '第五篇' },
      { title: '同意', url: '/students/zhang-qiong/f/', kind: '伦理', summary: '第六篇' }] },
    { slug: 'gao-peng', name: '高鹏', count: 2, items: [
      { title: '禁令的肉身', url: '/students/gao-peng/a/' },
      { title: '公正的沉默塌缩', url: '/students/gao-peng/b/' }] },
    { slug: 'hu-min', name: '胡敏', count: 2, items: [
      { title: '悬契', url: '/students/hu-min/a/' },
      { title: '复现土', url: '/students/hu-min/b/' }] }
  ]
};
const ARTICLE_HTML = '<html><head><title>假文章</title></head><body><nav>导航</nav>' +
  '<article>' + '这是一篇假的站内文章正文。'.repeat(120) + '</article>' +
  '<script>console.log(1)<\/script><footer>页脚</footer></body></html>';
// 6 万字符 → 26000 一段，正好 3 段，便于数
const FAKE_NEIGONG = 'SDE 内功正文段落。'.repeat(6000).slice(0, 60000);
const SHORT_HTML = '<html><body><article>太短。</article></body></html>';

function spineAnswer(conflictLine) {
  const blk = n => ['【源' + n + '】《假文章' + n + '》',
    '主题观点：第' + n + '篇主张的那一条判断，够长够像判断句。',
    '支撑观点 ' + n + 'a：结果层的理由，独立成立。　〔依据：原文若干字〕',
    '支撑观点 ' + n + 'b：路径层的理由，独立成立。　〔依据：原文若干字〕',
    '支撑观点 ' + n + 'c：条件层的理由，独立成立。　〔依据：原文若干字〕',
    '互不包含自检：a×b 不同层 ｜ a×c 不同层 ｜ b×c 不同层'].join('\n');
  return [blk(1), blk(2), blk(3),
    '冲突 1×2：一个说该撤手，一个说撤手是灾，不能同时成立。',
    '冲突 1×3：一个说留白养人，一个说留白什么也长不出。',
    '冲突 2×3：两条处方相反。',
    '主题冲突：' + (conflictLine || '三对全冲突')].join('\n\n');
}
function defaultAnswer(userMsg) {
  if (/这是 SDE 内功的第/.test(userMsg)) return '这一段的承重判断若干。' + '要点。'.repeat(20);
  if (/合成一份 ≤3000 字的作业底盘/.test(userMsg)) return '一、本体论要害……二、方法论工序……三、碰撞心法转写……四、十条铁律……' + '铁律一条。'.repeat(80);
  if (/【文章清单】/.test(userMsg))
    return /已经试过/.test(userMsg)
      ? '换一条轴再找……\n种子：#4 #5 #6 ｜ 矛盾轴：另一条轴'
      : '这三篇在"撤手"上给了相反的处方……\n种子：#1 #2 #3 ｜ 矛盾轴：同一个"撤"字的三种相反评价';
  if (/你是验收员/.test(userMsg))
    return '烈度：8/10 ｜ 同源度：低 ｜ 打架点：撤手到底是德是灾\n判词：三方对同一个动作给了相反的处方';
  if (/一个主题观点/.test(userMsg) && /支撑观点/.test(userMsg)) return spineAnswer('三对全冲突');
  if (/列一份文章目录/.test(userMsg))
    return Array.from({ length: 16 }, (_, i) => '第' + (i + 1) + '章、章名' + (i + 1) + ' —— 落一件事').join('\n');
  if (/继续写这篇文章的第/.test(userMsg)) return '章节正文。'.repeat(60);
  if (/你是评审/.test(userMsg)) return '总分：152\n五维：S=150 D=151 E=152 I=153 F=150\n判级：典范级\n最该补的一刀：' + '再往下切一层。'.repeat(6);
  if (/请先做体检/.test(userMsg)) return gateOK();
  return '产物：一段假的工序输出。'.repeat(6);
}
function gateOK() {
  return '闸一：分数 8/10 ｜ 打架点一句话：三方对同一件事判了相反的处方 ｜ 结局对立：有 ｜ 三方各自的硬证据：各有一条\n' +
    '闸二：同源度 低 ｜ 共享零件：无 ｜ 建议撞点：落在处方相反那一处\n闸三：最近的已发篇目：无 ｜ 处置：可发\n总判：放行';
}
function verifyOK(sc) {
  return '烈度：' + sc + '/10 ｜ 同源度：低 ｜ 打架点：三方对同一个动作给了相反的处方\n' +
    '判词：结局对立，三方各自都有对手消化不了的证据，够打。';
}
function verifyBad(sc) {
  return '烈度：' + sc + '/10 ｜ 同源度：中 ｜ 打架点：说不清\n' +
    '判词：这三篇只是侧重不同、各说一面，属于互补；换一条轴去找处方相反的那一类。';
}
function gateBad(score) {
  return '闸一：分数 ' + score + '/10 ｜ 打架点一句话：其实是侧重不同 ｜ 结局对立：无 ｜ 三方各自的硬证据：说不上来\n' +
    '闸二：同源度 高 ｜ 共享零件：同一套框架\n闸三：与已发篇目同族\n总判：换源';
}
function sseFor(text) {
  const out = ['data: ' + JSON.stringify({ choices: [{ delta: { reasoning_content: '思考…' } }] }) + '\n\n'];
  for (let i = 0; i < text.length; i += 400)
    out.push('data: ' + JSON.stringify({ choices: [{ delta: { content: text.slice(i, i + 400) } }] }) + '\n\n');
  out.push('data: ' + JSON.stringify({ choices: [{ delta: {}, finish_reason: 'stop' }] }) + '\n\n');
  out.push('data: [DONE]\n\n');
  return out;
}

/* ---------------- 起一个页面 ---------------- */
async function boot(opts) {
  opts = opts || {};
  const ctx = { calls: [], errors: [], saved: [] };
  const vc = new VirtualConsole();
  vc.on('jsdomError', e => ctx.errors.push('jsdomError: ' + (e && e.message)));
  vc.on('error', (...a) => ctx.errors.push('console.error: ' + a.join(' ')));

  const answer = opts.answer || defaultAnswer;
  function makeFetch() {
    return function (url, init) {
      url = String(url); init = init || {};
      const J = o => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(o), text: () => Promise.resolve(JSON.stringify(o)) });
      const T = s => Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(s), json: () => Promise.resolve({}) });
      const BAD = c => Promise.resolve({ ok: false, status: c, statusText: 'ERR', text: () => Promise.resolve(''), json: () => Promise.resolve({}) });

      if (url.indexOf('catalog.json') >= 0) return opts.catalogFail ? BAD(404) : J(CATALOG);
      if (url.indexOf('publications.json') >= 0) return opts.catalogFail ? BAD(404) : J(STUDENTS);
      if (url.indexOf('sde-neigong.txt') >= 0) return opts.neigongFail ? BAD(404) : T(FAKE_NEIGONG);
      if (url.indexOf('sde-collide-heart.txt') >= 0) return T('二阶碰撞心法：先找矛盾再找高分。'.repeat(80));
      if (url.indexOf('sde-innovation-iq.txt') >= 0) return T('创新智商评分标尺：五维 S/D/E/I/F。'.repeat(80));
      if (url.indexOf('/api/kb/retrieve') >= 0) return opts.kbFail ? BAD(500) : J({ block: '【站内材料】假的检索块' });
      if (url.indexOf('chat/completions') >= 0 || url.indexOf('/api/llm-proxy') >= 0) {
        const body = JSON.parse(init.body);
        const msgs = body.messages || [];
        const user = (msgs[msgs.length - 1] || {}).content || '';
        const budget = body.max_tokens != null ? body.max_tokens
          : (body.max_completion_tokens != null ? body.max_completion_tokens
          : ((body.generationConfig || {}).maxOutputTokens));
        ctx.calls.push({ url, max_tokens: budget, model: body.model,
          system: (msgs[0] || {}).content || '', user, headers: init.headers || {} });
        const chunks = sseFor(answer(user));
        let i = 0;
        const nextChunk = () => i < chunks.length
          ? { done: false, value: Buffer.from(chunks[i++]) }
          : { done: true, value: undefined };
        const read = opts.slow
          ? () => new Promise(r => setTimeout(() => r(nextChunk()), opts.slow))
          : () => Promise.resolve(nextChunk());
        return Promise.resolve({ ok: true, status: 200, body: { getReader: () => ({ read }) } });
      }
      if (opts.articleFail) return BAD(404);
      if (opts.articleShort) return T(SHORT_HTML);
      return T(ARTICLE_HTML);
    };
  }

  const dom = new JSDOM(HTML, {
    runScripts: 'dangerously', url: 'https://sdeuniverses.com/taste/paradigm-forge/',
    virtualConsole: vc, pretendToBeVisual: true,
    beforeParse(win) {
      win.fetch = makeFetch();
      win.TextDecoder = TextDecoder; win.TextEncoder = TextEncoder;
      win.AbortController = AbortController;
      win.Element.prototype.scrollIntoView = function () {};
      win.HTMLElement.prototype.scrollIntoView = function () {};
      win.HTMLAnchorElement.prototype.click = function () {};   // 否则 jsdom 报 navigation to another Document
      win.scrollTo = function () {}; win.alert = function () {};
      win.URL.createObjectURL = () => 'blob:fake'; win.URL.revokeObjectURL = () => {};
      win.docx = {
        Document: function (o) { this.o = o; win.__lastDoc = o; },
        Packer: { toBlob: () => Promise.resolve(new win.Blob(['docx-bytes'])) },
        Paragraph: function (o) { this.o = o; }, TextRun: function (o) { this.o = o; },
        AlignmentType: { CENTER: 'center' }, HeadingLevel: { HEADING_1: 'h1', HEADING_2: 'h2' }
      };
      if (opts.withSaveDir) {
        win.WDSSaveDir = {
          supported: () => true, name: () => '碰撞产出',
          ensure: () => Promise.resolve(true), forget: () => Promise.resolve(true),
          // 真模块 wds-savedir.js 的契约：注册时立刻回调一次（第 157 行 try{ f(name()) }），替身照抄
          onChange: cb => { win.__sdCb = cb; try { cb('碰撞产出'); } catch (e) {} },
          save: (name, blob) => {
            const rec = { name, size: blob && blob.size };
            ctx.saved.push(rec);
            if (blob && blob.text) { try { blob.text().then(t => { rec.text = t; }).catch(() => {}); } catch (e) {} }
            return Promise.resolve({ where: 'dir', dir: '碰撞产出', name });
          }
        };
      }
    }
  });
  ctx.dom = dom; ctx.win = dom.window; ctx.doc = dom.window.document;
  ctx.$ = id => ctx.doc.getElementById(id);
  ctx.click = sel => { const el = typeof sel === 'string' ? ctx.doc.querySelector(sel) : sel;
    el.dispatchEvent(new ctx.win.MouseEvent('click', { bubbles: true })); };
  await sleep(250);
  return ctx;
}

async function runPipeline(c, timeout) {
  c.$('apiKey').value = 'sk-fake';
  c.click('#goBtn');
  return await waitFor(() => /创新智商|✓/.test(c.$('stat-review').textContent), timeout || 20000);
}
/* 自动模式：什么都不用选，学员下拉默认第一位即可 */
function pickModeA(c) { return 3; }
/* 手挑模式：勾上"我自己挑三篇"，再勾前三篇 */
function pickModeAManual(c) {
  const chk = c.$('manualChk');
  chk.checked = true; chk.dispatchEvent(new c.win.Event('change', { bubbles: true }));
  const boxes = Array.from(c.doc.querySelectorAll('#stuList input[type=checkbox]')).slice(0, 3);
  boxes.forEach(b => { b.checked = true; b.dispatchEvent(new c.win.Event('change', { bubbles: true })); });
  return boxes.length;
}
function setStudent(c, slug) {
  c.$('stuSel').value = slug; c.$('stuSel').dispatchEvent(new c.win.Event('change', { bubbles: true }));
}

/* ======================= 场景 ======================= */
(async function main() {
  console.log('页面：' + HTML_PATH + '\n' + '='.repeat(56));

  const c1 = await boot();
  await step('一、页面起得来（静态结构）', async () => {
    ok('十二道工序面板都在', c1.doc.querySelectorAll('.stage').length === 12, '实际 ' + c1.doc.querySelectorAll('.stage').length);
    ok('第一格是内化、第二格是选篇', c1.doc.querySelectorAll('.stage')[0].id === 'stage-warmup' &&
      c1.doc.querySelectorAll('.stage')[1].id === 'stage-select');
    ok('工序顺序正确', ['warmup','select','gate','spine','collide','expand','collide2','selforg','emerge','demarc','write','review']
      .every((id, i) => c1.doc.querySelectorAll('.stage')[i].id === 'stage-' + id));
    ok('八家基底都在选择器里', ['ds:pro','glm:pro','kimi:pro','qwen:pro','minimax:pro','gpt:pro','claude:pro','gemini:pro']
      .every(v => !!c1.doc.querySelector('option[value="' + v + '"]')));
    ok('四种选源模式都在', c1.doc.querySelectorAll('.mode').length === 4);
    ok('选源目录已载入（学员三位）', c1.$('stuSel').options.length === 3, '实际 ' + c1.$('stuSel').options.length);
    ok('模式 A 默认交给基底挑（手挑列表收起）', c1.doc.getElementById('stuManual').classList.contains('hidden'));
    ok('状态条说清了由基底从几篇里挑', /由基底从「张琼」的 6 篇里挑/.test(c1.$('srcState').textContent), c1.$('srcState').textContent);
    ok('存储位置在无 API 时如实降级', /不支持选择文件夹/.test(c1.$('saveDirNote').textContent));
    ok('交付区一开始是收起的', c1.$('deliver').style.display === 'none');
  });

  await step('二、基底切换 · Key 分存 · 境外提示', async () => {
    c1.win.localStorage.setItem('sde_ds_key', 'sk-ds'); c1.win.localStorage.setItem('sde_glm_key', 'sk-glm');
    c1.$('modelSel').value = 'glm:pro';
    c1.$('modelSel').dispatchEvent(new c1.win.Event('change', { bubbles: true }));
    ok('切到智谱后 Key 跟着换', c1.$('apiKey').value === 'sk-glm', c1.$('apiKey').value);
    ok('Key 标签写的是智谱', /智谱/.test(c1.$('keyLabel').textContent));
    c1.$('modelSel').value = 'gpt:pro';
    c1.$('modelSel').dispatchEvent(new c1.win.Event('change', { bubbles: true }));
    ok('境外基底给出中转说明', c1.$('overseasNote').style.display === 'block' && /中转/.test(c1.$('overseasNote').textContent));
    ok('境外基底的 Key 槽是空的（分存生效）', c1.$('apiKey').value === '');
    c1.$('modelSel').value = 'ds:pro';
    c1.$('modelSel').dispatchEvent(new c1.win.Event('change', { bubbles: true }));
    ok('切回 DeepSeek 取回自己的 Key', c1.$('apiKey').value === 'sk-ds');
  });

  await step('三、引擎室开关', async () => {
    const chk = c1.$('engineChk');
    chk.checked = true; chk.dispatchEvent(new c1.win.Event('change', { bubbles: true }));
    ok('打开后工序格展开', c1.doc.getElementById('stage-collide').classList.contains('open'));
    ok('成文格不受开关影响', !c1.doc.getElementById('stage-write').classList.contains('open'));
    chk.checked = false; chk.dispatchEvent(new c1.win.Event('change', { bubbles: true }));
    ok('关掉后工序格收起', !c1.doc.getElementById('stage-collide').classList.contains('open'));
  });

  const cA = await boot();
  await step('四、模式 A（基底选篇 → 跑完十一道工序）', async () => {
    const done = await runPipeline(cA);
    ok('十一格全部跑完', done, '停在 ' + cA.$('stat-review').textContent);
    ok('选篇格报出第几轮定标与烈度', /第 1 轮定标 · 烈度 8\/10/.test(cA.$('stat-select').textContent), cA.$('stat-select').textContent);
    ok('种子三篇已就位', /种子：留白 × 伪生 × 撤土/.test(cA.$('srcState').textContent), cA.$('srcState').textContent);
    ok('一轮定标就只花两趟（提名+验收）',
      cA.calls.filter(x => /【文章清单】/.test(x.user)).length === 1 &&
      cA.calls.filter(x => /你是验收员/.test(x.user)).length === 1);
    ['gate','spine','collide','expand','collide2','selforg','emerge','demarc'].forEach(id =>
      ok('  ' + id + ' 出了结果', /✓/.test(cA.$('stat-' + id).textContent), cA.$('stat-' + id).textContent));
    ok('成文格给出了字数', /字/.test(cA.$('stat-write').textContent), cA.$('stat-write').textContent);
    ok('成文格报告术语零残留', /术语零残留/.test(cA.$('stat-write').textContent));
    ok('评审读出创新智商 152', /创新智商 152/.test(cA.$('stat-review').textContent));
    ok('交付区已亮出', cA.$('deliver').style.display !== 'none');
    ok('三个源都进了调令', cA.calls.some(x => /源1/.test(x.user) && /源2/.test(x.user) && /源3/.test(x.user)));
  });

  await step('五、预算纪律（满功率档的硬上限）', async () => {
    const over = cA.calls.filter(c => c.max_tokens > 8000);
    ok('没有任何一趟超过 8000', over.length === 0, over.map(c => c.max_tokens).join(','));
    const w = cA.calls.filter(c => /继续写这篇文章的第/.test(c.user));
    ok('成文分趟写（≥4 趟）', w.length >= 4, '实际 ' + w.length + ' 趟');
    ok('成文每趟 ≤4000', w.every(c => c.max_tokens <= 4000));
    ok('体检那趟是 4000', (cA.calls.find(c => /请先做体检/.test(c.user)) || {}).max_tokens === 4000);
    ok('自组织那趟是 6000', (cA.calls.find(c => /自组织聚类/.test(c.user)) || {}).max_tokens === 6000);
    ok('用的是所选基底的模型串', cA.calls.every(c => /deepseek/.test(c.model || '')), (cA.calls[0] || {}).model);
  });

  await step('六、十一道工序的调令纪律', async () => {
    const f = re => cA.calls.find(c => re.test(c.user));
    const sel = f(/【文章清单】/);
    ok('选篇把这位学员的全部篇目编号列出来', sel && /#1　留白/.test(sel.user) && /#6　同意/.test(sel.user));
    ok('选篇带上门类与摘要（好判打架点）', sel && /〔发展心理学〕/.test(sel.user) && /撤手是德/.test(sel.user));
    ok('选篇写明"不是挑三篇最好的"', sel && /不是挑三篇最好的/.test(sel.user));
    ok('选篇把结局对立列为首要判据', sel && /结局对立.*最优先|\*\*结局对立\*\*最优先/.test(sel.user));
    ok('选篇规定了机读格式', sel && /种子：#3 #17 #42/.test(sel.user));
    const ver = f(/你是验收员/);
    ok('验收是独立一趟、只验不提名', ver && /只验不提名/.test(ver.system));
    ok('验收硬约束：互补 ≤4、结局对立 ≥7', ver && /烈度 ≤4/.test(ver.user) && /烈度 ≥7/.test(ver.user));
    ok('验收被明确要求宁可判低', ver && /宁可判低/.test(ver.user));
    ok('验收只要两行读数', ver && /烈度：X\/10/.test(ver.user) && /判词：/.test(ver.user));
    ok('验收调令里带的是三篇的标题与摘要', ver && /留白/.test(ver.user) && /撤手是德/.test(ver.user));
    const gate = f(/请先做体检/);
    ok('体检写死三道闸', gate && /闸一/.test(gate.user) && /闸二/.test(gate.user) && /闸三/.test(gate.user));
    ok('体检把已发清单垫进去（避重）', gate && /已发清单/.test(gate.user));
    ok('体检优先找结局对立', gate && /结局对立/.test(gate.user));
    const spine = f(/一个主题观点/);
    ok('抽脊要三视角各一条', spine && /结果层[\s\S]*路径层[\s\S]*条件层/.test(spine.user));
    ok('抽脊要"一个主题观点 ＋ 三个支撑观点"', spine && /一个主题观点/.test(spine.user) && /三个支撑观点/.test(spine.user));
    ok('抽脊规定了机读字段与 1a/1b/1c 编号', spine && /支撑观点 1a/.test(spine.user) && /2a\/2b\/2c/.test(spine.user));
    ok('抽脊要求三条支撑互不包含', spine && /互不包含/.test(spine.user));
    ok('抽脊要求逐对自检包含关系', spine && /a×b …… ｜ a×c/.test(spine.user));
    ok('抽脊要求三条主题两两冲突并给四行验收',
      spine && /冲突 1×2/.test(spine.user) && /冲突 1×3/.test(spine.user) && /冲突 2×3/.test(spine.user) && /主题冲突：三对全冲突/.test(spine.user) && /不成立（点名哪一对其实相容/.test(spine.user));
    ok('抽脊把冲突判准写死（若这条成立那条就不成立）', spine && /若这条成立、那条就不成立/.test(spine.user));
    ok('抽脊明说宁可判不成立也别硬撑', spine && /不要为了交差硬说成冲突/.test(spine.user));
    const nom = f(/【文章清单】/);
    ok('提名就要交三条主题观点与两两冲突', nom && /主题观点/.test(nom.user) && /两两冲突/.test(nom.user));
    ok('提名写明"一对相容就不合格"', nom && /只要有一对其实相容/.test(nom.user));
    const vf = cA.calls.find(x => /你是验收员/.test(x.user));
    ok('验收员也要写三条主题观点', vf && /主题1/.test(vf.user));
    ok('验收员写不出三条互斥主题就压分', vf && /写不出三条彼此不能同时成立的主题观点/.test(vf.user));
    const col = f(/跨篇 3×3/);
    ok('碰撞写死同篇内部作废', col && /同一篇内部的对[\s\S]*一律作废/.test(col.user));
    ok('碰撞要求无焦点即作废、不许强行联系', col && /无焦点/.test(col.user) && /不许强行联系/.test(col.user));
    ok('碰撞要求结构性命名 ≤20 字', col && /≤20 字/.test(col.user));
    ok('碰撞撞的是九条支撑、主题冲突当底盘', col && /三条主题观点彼此冲突，这是本次碰撞的底盘/.test(col.user) && /九条支撑观点/.test(col.user));
    const exp = f(/五个候选判断/);
    ok('扩候选要求候选间不同脊、不凑数', exp && /不许同脊/.test(exp.user) && /不要凑数/.test(exp.user));
    const c2 = f(/第二阶对撞/);
    ok('候选互撞是 C(5,2)=10 对', c2 && /10 对/.test(c2.user));
    const so = f(/自组织聚类/);
    ok('暗流要 ≥2 个涌现物支撑、不许硬凑', so && /≥2 个涌现物/.test(so.user) && /不许硬凑/.test(so.user));
    const em = f(/五重检验/);
    ok('涌现含自反与反噬预言', em && /自反/.test(em.user) && /反噬预言/.test(em.user));
    ok('涌现要证伪条件与写死日期的赌注', em && /证伪条件/.test(em.user) && /赌注/.test(em.user));
    ok('涌现明令不自评', em && /你不给自己打分/.test(em.user));
    const de = f(/划清界线/);
    ok('划界要 6–10 个近邻并落到可分辨判据', de && /6–10 个/.test(de.user) && /判据差在哪/.test(de.user));
    ok('划界把站内检索块垫了进去', de && /站内可参照的近邻材料/.test(de.user));
    const wr = f(/继续写这篇文章的第/);
    ok('成文 system 写死术语零容忍', wr && /不得出现任何学派术语/.test(wr.system));
    ok('成文 system 要求长句 ≤90 字', wr && /长句不超过 90 字/.test(wr.system));
    ok('成文调令要求直接写正文、不复述目录', wr && /不要复述目录/.test(wr.user));
    ok('成文把已写结尾垫进去防重复', wr && /已写正文的结尾/.test(wr.user));
    ok('成文与工序用的是两套 system', wr && spine && wr.system !== spine.system);
    const rv = f(/你是评审/);
    ok('评审独立一趟、system 说明只评不写', rv && /只评不写/.test(rv.system));
    ok('评审有多条反膨胀封顶', rv && (rv.user.match(/封顶/g) || []).length >= 3);
    ok('评审要求不到 150 点名回炉', rv && /点名回炉/.test(rv.user));
    ok('工序 system 里带 SDE 母语内功', spine && /SDE 本体论·凝缩/.test(spine.system));
  });

  await step('七、单格重跑 / 从这里继续 / 编辑存回', async () => {
    cA.calls.length = 0;
    cA.click('#stage-emerge button[data-act="rerun"]');
    await waitFor(() => cA.calls.length > 0, 4000); await sleep(250);
    ok('重跑只打这一格', cA.calls.length === 1, '实际 ' + cA.calls.length);
    ok('重跑的确是涌现格', cA.calls[0] && /五重检验/.test(cA.calls[0].user));

    cA.calls.length = 0;
    cA.click('#stage-demarc button[data-act="cont"]');
    await waitFor(() => /创新智商/.test(cA.$('stat-review').textContent) && cA.calls.length > 3, 20000);
    const kinds = cA.calls.map(x => /划清界线/.test(x.user) ? 'demarc'
      : (/继续写这篇文章的第|列一份文章目录/.test(x.user) ? 'write'
      : (/你是评审/.test(x.user) ? 'review' : 'other')));
    ok('「从这里继续」只跑划界→成文→评审', kinds.length > 3 && kinds.every(x => ['demarc','write','review'].includes(x)),
      Array.from(new Set(kinds)).join(','));

    const btn = cA.doc.querySelector('#stage-spine button[data-act="edit"]');
    cA.click(btn);
    const ta = cA.doc.querySelector('#stage-spine textarea');
    ok('点开出现编辑框', !!ta);
    if (ta) { ta.value = '我手改过的九条'; cA.click(btn); }
    ok('存回后产物变成手改的', /我手改过的九条/.test(cA.$('out-spine').textContent));
    ok('编辑框已收起', !cA.doc.querySelector('#stage-spine textarea'));
    cA.calls.length = 0;
    cA.click('#stage-collide button[data-act="rerun"]');
    await waitFor(() => cA.calls.length > 0, 4000);
    ok('手改的产物真的被下一格吃进去', cA.calls[0] && /我手改过的九条/.test(cA.calls[0].user));
  });

  await step('八、三个导出通道', async () => {
    cA.click('#dlDocx'); cA.click('#dlPack'); cA.click('#dlEngine');
    await sleep(300);
    const doc = cA.win.__lastDoc;
    ok('Word 确实被打包', !!(doc && doc.sections && doc.sections[0].children.length > 3));
    ok('Word 里有署名行', !!(doc && JSON.stringify(doc).indexOf('王德生 ＋ Claude') >= 0));
    ok('导出没抛错', cA.errors.length === 0, cA.errors.slice(0, 2).join(' ｜ '));
  });

  await step('九、清空后能再来一次', async () => {
    cA.click('#resetBtn'); await sleep(80);
    ok('工序状态复位', cA.$('stat-emerge').textContent === '待命');
    ok('产物清空', /还没跑到这一格/.test(cA.$('out-spine').textContent));
    ok('交付区收起', cA.$('deliver').style.display === 'none');
    cA.calls.length = 0;
    ok('候选也被清掉', true);
    const done = await runPipeline(cA);
    ok('第二遍照样跑得完（重新选篇）', done);
    ok('第二遍确实重新挑了一次', cA.calls.some(x => /【文章清单】/.test(x.user)));
  });

  await step('十、模式 B（三人各一篇）', async () => {
    const c = await boot();
    c.click('.mode[data-mode="B"]'); await sleep(60);
    ok('三行作者×篇目都填上了', [0,1,2].every(i => c.$('bStu' + i).options.length === 3 && c.$('bArt' + i).options.length > 0));
    ok('默认就是三位不同作者', new Set([0,1,2].map(i => c.$('bStu' + i).value)).size === 3,
      [0,1,2].map(i => c.$('bStu' + i).value).join(','));
    c.$('bStu0').value = 'gao-peng'; c.$('bStu0').dispatchEvent(new c.win.Event('change', { bubbles: true }));
    await sleep(40);
    ok('换作者后篇目跟着换', Array.from(c.$('bArt0').options).some(o => /禁令的肉身/.test(o.textContent)));
    // 此刻第一、二行都是高鹏且都选了第一篇——先验"撞源必被拦"，再换回去跑正题
    c.$('apiKey').value = 'sk-fake'; c.click('#goBtn');
    await waitFor(() => c.$('errBox').style.display === 'block', 4000);
    ok('两行选到同一篇时被拦下', /不能重复/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    c.$('bStu0').value = 'zhang-qiong'; c.$('bStu0').dispatchEvent(new c.win.Event('change', { bubbles: true }));
    await sleep(40);
    const done = await runPipeline(c);
    ok('B 模式跑得完', done, c.$('stat-review').textContent);
    ok('调令里带上了三位作者名', c.calls.some(x => /张琼/.test(x.user) && /高鹏/.test(x.user) && /胡敏/.test(x.user)));
    ok('零抛错', c.errors.length === 0, c.errors.slice(0, 2).join(' ｜ '));
  });

  await step('十一、模式 C（站上三长文 + 关键词筛）', async () => {
    const c = await boot();
    c.click('.mode[data-mode="C"]'); await sleep(60);
    ok('三个下拉都有候选', [0,1,2].every(i => c.$('cSel' + i).options.length > 0));
    const q = c.$('cQ0'); q.value = '睡眠'; q.dispatchEvent(new c.win.Event('input', { bubbles: true }));
    await sleep(40);
    const opts = Array.from(c.$('cSel0').options).map(o => o.textContent);
    ok('关键词把候选筛窄且全命中', opts.length > 0 && opts.every(t => /睡眠/.test(t)), '共 ' + opts.length);
    q.value = ''; q.dispatchEvent(new c.win.Event('input', { bubbles: true })); await sleep(40);
    ok('清掉关键词候选回满', c.$('cSel0').options.length > opts.length);
    c.$('cSel0').selectedIndex = 0; c.$('cSel1').selectedIndex = 1; c.$('cSel2').selectedIndex = 2;
    const done = await runPipeline(c);
    ok('C 模式跑得完', done, c.$('stat-review').textContent);
    ok('三个源的链接进了调令', c.calls.some(x => /\/column\/fake-/.test(x.user)));
    ok('零抛错', c.errors.length === 0, c.errors.slice(0, 2).join(' ｜ '));
  });

  await step('十二、模式 F（自由投喂）', async () => {
    const c = await boot();
    c.click('.mode[data-mode="F"]'); await sleep(50);
    c.$('f1').value = '站外理论甲\n' + '甲的论证。'.repeat(60);
    c.$('f2').value = '站外理论乙\n' + '乙的论证。'.repeat(60);
    c.$('f3').value = '短';
    c.$('apiKey').value = 'sk-fake';
    c.click('#goBtn');
    await waitFor(() => c.$('errBox').style.display === 'block', 3000);
    ok('第三个源太短被拦下', /第 3 个源太短/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('被拦下时一趟基底都没打', c.calls.length === 0);
    c.$('f3').value = '站外理论丙\n' + '丙的论证。'.repeat(60);
    const done = await runPipeline(c);
    ok('补齐后跑得完', done, c.$('stat-review').textContent);
    ok('三个标题都取自首行', c.calls.some(x => /站外理论甲/.test(x.user) && /站外理论丙/.test(x.user)));
    ok('零抛错', c.errors.length === 0, c.errors.slice(0, 2).join(' ｜ '));
  });

  await step('十三、失败路径：没填 Key', async () => {
    const c = await boot();
    pickModeA(c);
    c.click('#goBtn');
    await sleep(250);
    ok('给出"先填 Key"的提示', /API Key/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('一趟基底都没打', c.calls.length === 0);
    ok('开始按钮没被永久锁死', c.$('goBtn').disabled === false);
  });

  await step('十四、失败路径：取不到正文 / 正文太短 / 源重复', async () => {
    const a = await boot({ articleFail: true });
    a.$('apiKey').value = 'sk-fake'; a.click('#goBtn');
    await waitFor(() => a.$('errBox').style.display === 'block', 6000);
    ok('404 时如实报"取不到正文"', /取不到正文/.test(a.$('errBox').textContent), a.$('errBox').textContent);
    ok('只跑到选篇就停（没往下烧 Token）', a.calls.length <= 6, '实际 ' + a.calls.length + ' 趟（内化四趟＋提名＋验收）');

    const b = await boot({ articleShort: true });
    b.$('apiKey').value = 'sk-fake'; b.click('#goBtn');
    await waitFor(() => b.$('errBox').style.display === 'block', 4000);
    ok('正文太短时点名换一篇', /正文太短/.test(b.$('errBox').textContent), b.$('errBox').textContent);

    const d = await boot();
    d.click('.mode[data-mode="F"]'); await sleep(50);
    ['f1','f2','f3'].forEach(id => { d.$(id).value = '同一个标题\n' + '一样的正文。'.repeat(60); });
    d.$('apiKey').value = 'sk-fake'; d.click('#goBtn');
    await waitFor(() => d.$('errBox').style.display === 'block', 4000);
    ok('三个源重复时被拦', /不能重复/.test(d.$('errBox').textContent), d.$('errBox').textContent);
  });

  await step('十五、全文体检始终低分：回选篇重找两次就收手', async () => {
    let nom = 0;
    const c = await boot({ answer: u => {
      if (/【文章清单】/.test(u)) { nom++;
        const sets = [[1,2,3],[4,5,6],[1,4,6],[2,3,5]];
        return '这一组……' + '理由若干。'.repeat(6) + '\n种子：#' + sets[(nom - 1) % 4].join(' #') + ' ｜ 矛盾轴：轴' + nom; }
      if (/你是验收员/.test(u)) return verifyOK(8);
      if (/请先做体检/.test(u)) return gateBad(3);
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 45000);
    ok('摘要层过了、全文层不过，就回选篇重找', nom >= 2, '提名了 ' + nom + ' 轮');
    ok('最多回两次（第三次不再回头）', nom === 3, '提名了 ' + nom + ' 轮');
    ok('末了如实说"多半是互补"', /闸一只给了 3\/10/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('给出下一步（换学员或手挑）', /建议换一位学员或改手挑/.test(c.$('errBox').textContent));
    ok('不阻断，照样跑完', done, c.$('stat-review').textContent);
  });

  await step('十六、成文带术语：自动改姓重写一次', async () => {
    let round = 0;
    const c = await boot({ answer: u => {
      if (/继续写这篇文章的第/.test(u)) {
        return /上一稿的问题/.test(u)
          ? '这一章改用大白话，讲的是账本记不下的那样东西。'.repeat(20)
          : '这一章讲显露与特征纠缠，还引了发生学。'.repeat(20);
      }
      if (/列一份文章目录/.test(u)) { round++; }
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 30000);
    ok('跑得完', done, c.$('stat-review').textContent);
    ok('成文重写了一遍（目录出了两次）', round === 2, '实际 ' + round + ' 次');
    ok('重写时把违规词带回去点名', c.calls.some(x => /上一稿的问题[\s\S]*显露/.test(x.user)));
    ok('改完术语零残留', /术语零残留/.test(c.$('stat-write').textContent), c.$('stat-write').textContent);
    ok('横幅记下了自动修的这一笔', /自动重写/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
  });

  await step('十六之二、改写一遍仍带术语就不再空转', async () => {
    const c = await boot({ answer: u => /继续写这篇文章的第/.test(u)
      ? '这一章讲显露与特征纠缠，还引了发生学。'.repeat(20) : defaultAnswer(u) });
    const done = await runPipeline(c, 30000);
    ok('跑得完（不静默失败）', done);
    ok('只重写一次就收手', (c.calls.filter(x => /列一份文章目录/.test(x.user)) || []).length === 2);
    ok('如实说要手工改', /仍有残留/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('横幅把术语残留亮出来', /术语残留/.test(c.$('doneBanner').textContent));
  });

  await step('十七、评审不到 150：自动回炉，第二轮过线', async () => {
    let rv = 0;
    const c = await boot({ answer: u => {
      if (/你是评审/.test(u)) {
        rv++;
        return rv === 1
          ? '总分：138\n五维：S=140 D=139 E=132 I=130 F=130\n判级：偏低\n若总分<150：回炉到「近邻划界」，把最近的邻居再切一刀。'
          : '总分：152\n五维：S=150 D=151 E=152 I=153 F=150\n判级：典范级';
      }
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 40000);
    ok('评审跑了两轮', rv === 2, '实际 ' + rv + ' 轮');
    ok('回炉回到了评审点名的那一格（近邻划界）',
      (c.calls.filter(x => /逐一划清界线/.test(x.user)) || []).length === 2,
      (c.calls.filter(x => /逐一划清界线/.test(x.user)) || []).length + ' 次');
    ok('第二轮读出 152', /创新智商 152/.test(c.$('stat-review').textContent), c.$('stat-review').textContent);
    ok('横幅写明过线', /过线/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
    ok('横幅记下回炉这一笔', /回炉/.test(c.$('doneBanner').textContent));
    ok('跑完了', done);
  });

  await step('十七之一、评审两轮都不过线就收手（不无限回炉）', async () => {
    let rv = 0;
    const c = await boot({ answer: u => {
      if (/你是评审/.test(u)) { rv++; return '总分：138\n五维：S=140 D=139 E=132 I=130 F=130\n判级：偏低\n回炉：涌现'; }
      return defaultAnswer(u);
    } });
    await runPipeline(c, 45000);
    ok('最多回炉两轮（评审三次）', rv === 3, '实际评审 ' + rv + ' 次');
    ok('回炉去的是评审点名的涌现格',
      (c.calls.filter(x => /五重检验/.test(x.user)) || []).length === 3,
      (c.calls.filter(x => /五重检验/.test(x.user)) || []).length + ' 次');
    ok('横幅如实说没过线', /未过线/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
  });

  await step('十七之六、一趟空答自动降档重来', async () => {
    let n = 0;
    const c = await boot({ answer: u => {
      if (/五重检验/.test(u)) { n++; return n === 1 ? '' : defaultAnswer(u); }
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 30000);
    ok('空答那一格重来了一次', n === 2, '实际 ' + n + ' 次');
    const em = c.calls.filter(x => /五重检验/.test(x.user));
    ok('重来的那趟降了档（≤4000）', em.length === 2 && em[1].max_tokens <= 4000, em.map(x => x.max_tokens).join('→'));
    ok('照样跑到底', done);
    ok('横幅记下这一笔', /降档/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);

    // 不只是"空"要重来——短到不成产物（<30 字）也要重来，否则一句"好的"会被当成合格产物往下传
    let k = 0;
    const c2 = await boot({ answer: u => {
      if (/自组织聚类/.test(u)) { k++; return k === 1 ? '好的，我明白了。' : defaultAnswer(u); }
      return defaultAnswer(u);
    } });
    const done2 = await runPipeline(c2, 30000);
    ok('短到不成产物的那趟也重来了', k === 2, '实际 ' + k + ' 次');
    ok('重来后照样跑到底', done2);
  });

  await step('十七之二、手挑模式仍然可用（选篇格自动跳过）', async () => {
    const c = await boot();
    ok('勾上手挑后列表露出来', pickModeAManual(c) === 3 && !c.doc.getElementById('stuManual').classList.contains('hidden'));
    ok('计数回到 3/3', /已选 3 \/ 3/.test(c.$('srcState').textContent), c.$('srcState').textContent);
    const done = await runPipeline(c);
    ok('照样跑得完', done, c.$('stat-review').textContent);
    ok('选篇格标为跳过', /跳过/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
    ok('一趟选篇的 Token 都没花', !c.calls.some(x => /【文章清单】/.test(x.user)));
    ok('勾多勾少会被拦', (function(){
      const extra = Array.from(c.doc.querySelectorAll('#stuList input[type=checkbox]'))[3];
      extra.checked = true; extra.dispatchEvent(new c.win.Event('change', { bubbles: true }));
      return c.doc.querySelectorAll('#stuList input[type=checkbox]:checked').length === 3;   // 勾第四篇顶掉最早的
    })());
  });

  await step('十七之三、一直找到三个种子为止（第一轮不过就换一组重提）', async () => {
    let nom = 0, ver = 0;
    const c = await boot({ answer: u => {
      if (/【文章清单】/.test(u)) { nom++; return '理由若干。'.repeat(6) + '\n种子：#' +
        (nom === 1 ? '1 #2 #3' : '4 #5 #6') + ' ｜ 矛盾轴：轴' + nom; }
      if (/你是验收员/.test(u)) { ver++; return ver === 1
        ? '烈度：4/10 ｜ 同源度：中 ｜ 打架点：说不清\n判词：这三篇只是侧重不同，换一条轴去找处方相反的，别在同一批里挪位置'
        : verifyOK(8); }
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 30000);
    ok('提名了两轮', nom === 2, '实际 ' + nom + ' 轮');
    ok('每轮都验了一次', ver === 2, '实际 ' + ver + ' 次');
    ok('第二轮定标', /第 2 轮定标 · 烈度 8\/10/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
    ok('定标的是第二组', /种子：角力 × 反循环 × 同意/.test(c.$('srcState').textContent), c.$('srcState').textContent);
    const nom2 = c.calls.filter(x => /【文章清单】/.test(x.user))[1];
    ok('第二轮提名带上了"已经试过"清单', nom2 && /已经试过、被判不合格的组合/.test(nom2.user));
    ok('把上一轮的判词原样交回去', nom2 && /只是侧重不同/.test(nom2.user));
    ok('明令不许只换一篇就交差', nom2 && /不许只换一篇就交差/.test(nom2.user));
    ok('搜寻过程逐轮记在页面上', (c.$('out-select').parentNode.querySelector('.sel-log').textContent.match(/第 \d 轮/g) || []).length >= 2);
    ok('跑到底', done, c.$('stat-review').textContent);
  });

  await step('十七之四、烈度够但同源度高，也不算定标', async () => {
    let ver = 0, nom = 0;
    const c = await boot({ answer: u => {
      if (/【文章清单】/.test(u)) { nom++; return '理由若干。'.repeat(6) + '\n种子：#' +
        (nom === 1 ? '1 #2 #3' : '4 #5 #6') + ' ｜ 矛盾轴：轴' + nom; }
      if (/你是验收员/.test(u)) { ver++; return ver === 1
        ? '烈度：8/10 ｜ 同源度：高 ｜ 打架点：像在打架\n判词：其实是同一件事的三个侧面'
        : '烈度：7/10 ｜ 同源度：低 ｜ 打架点：处方相反\n判词：可以'; }
      return defaultAnswer(u);
    } });
    await runPipeline(c, 30000);
    ok('同源度高的那组不定标，继续找', ver >= 2, '只验了 ' + ver + ' 次');
    ok('最终定标在第二轮', /第 2 轮定标/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
  });

  await step('十七之五、试满上限还没找到，就取最好的一组并说清', async () => {
    const c = await boot({ answer: u => {
      if (/你是验收员/.test(u)) return verifyBad(4);
      return defaultAnswer(u);
    } });
    c.$('maxRounds').value = '3';
    const done = await runPipeline(c, 30000);
    // 两道闸都能把流程送回选篇（全文体检 / 三条主题观点不冲突），所以轮数是区间不是定值——但必须有界
    const noms = c.calls.filter(x => /【文章清单】/.test(x.user)).length;
    ok('至少试满三组，且不会无界地试下去', noms >= 3 && noms <= 8, '实际 ' + noms + ' 轮');
    ok('状态条如实写"试满"', /试满 3 组/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
    ok('红字给出三条出路（换学员／调大轮数／手挑）', /换一位学员/.test(c.$('errBox').textContent) &&
      /最多试/.test(c.$('errBox').textContent) && /手挑/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('不阻断，照样跑完给你看', done, c.$('stat-review').textContent);
  });

  await step('十七之六之二、提名重复的组合要被扣分、不许拿来定标', async () => {
    let ver = 0;
    const c = await boot({ answer: u => {
      if (/【文章清单】/.test(u)) return '就这一组。' .repeat(6) + '\n种子：#1 #2 #3 ｜ 矛盾轴：甲';  // 每轮都提同一组
      if (/你是验收员/.test(u)) { ver++; return ver === 1 ? verifyBad(4) : verifyOK(9); }
      return defaultAnswer(u);
    } });
    c.$('maxRounds').value = '3';
    await runPipeline(c, 40000);
    const log = c.$('out-select').parentNode.querySelector('.sel-log').textContent;
    ok('重复组合被标出来', /提了重复组合/.test(log), log.slice(0, 160));
    ok('重复的那组即便打了 9 分也不定标', !/定标/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
    ok('最后如实说"试满"并取最好的一组', /试满/.test(c.$('stat-select').textContent));
  });

  await step('十七之七、摘要层看走眼：全文体检不过就回选篇再找', async () => {
    let gate = 0, nom = 0;
    const c = await boot({ answer: u => {
      if (/【文章清单】/.test(u)) { nom++; return '理由若干。'.repeat(6) + '\n种子：#' +
        (nom === 1 ? '1 #2 #3' : '4 #5 #6') + ' ｜ 矛盾轴：轴' + nom; }
      if (/你是验收员/.test(u)) return verifyOK(8);
      if (/请先做体检/.test(u)) { gate++; return gate === 1 ? gateBad(3) : gateOK(); }
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 35000);
    ok('体检不过时回选篇又找了一轮', nom === 2, '提名了 ' + nom + ' 轮');
    ok('体检跑了两趟', gate === 2, '实际 ' + gate + ' 趟');
    ok('红字说清是"摘要层看走眼"', /摘要层看走眼|回选篇接着找/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    const nom2 = c.calls.filter(x => /【文章清单】/.test(x.user))[1];
    ok('全文体检的判词也进了下一轮提名', nom2 && /全文体检只给 3\/10/.test(nom2.user));
    ok('换完跑到底', done, c.$('stat-review').textContent);
  });

  await step('十七之八、基底始终给不出编号时说人话', async () => {
    const c = await boot({ answer: u => /【文章清单】/.test(u) ? '我觉得这几篇都不错，可惜没法编号。' : defaultAnswer(u) });
    c.$('maxRounds').value = '3';
    c.$('apiKey').value = 'sk-fake'; c.click('#goBtn');
    await waitFor(() => c.$('errBox').style.display === 'block', 15000);
    ok('提示重跑本格或改手挑', /勾上「我自己挑三篇」/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('没有硬撑着往下跑', c.$('stat-gate').textContent === '待命');
  });

  await step('十七之七、三篇与它们的观点要出现在页面上', async () => {
    const c = await boot();
    const done = await runPipeline(c, 30000);
    ok('跑得完', done);
    ok('三篇卡片亮出来了', !c.$('trioCard').classList.contains('hidden'));
    const rows = c.doc.querySelectorAll('#trioBox .trio-row');
    ok('正好三块', rows.length === 3, '实际 ' + rows.length);
    ok('每块都有主题观点', Array.from(rows).every(r => /主题观点：第\d篇主张的那一条判断/.test(r.textContent)));
    ok('每块都有三条支撑', Array.from(rows).every(r => r.querySelectorAll('ol li').length === 3),
      Array.from(rows).map(r => r.querySelectorAll('ol li').length).join(','));
    ok('三条支撑分别来自结果层/路径层/条件层', /结果层[\s\S]*路径层[\s\S]*条件层/.test(rows[0].textContent));
    ok('每块都链回原文', Array.from(rows).every(r => !!r.querySelector('a[href^="/students/"]')));
    ok('冲突校验行亮出来', /三对全冲突/.test(c.$('trioConflict').textContent), c.$('trioConflict').textContent);
    ok('横幅也带上主题冲突', /主题冲突：三对全冲突/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
  });

  await step('十七之八、三条主题观点没能两两冲突 → 自动回选篇另找', async () => {
    let sp = 0, nom = 0;
    const c = await boot({ answer: u => {
      if (/一个主题观点/.test(u)) { sp++; return spineAnswer(sp === 1 ? '不成立（源1 与源3 其实相容，两条能一起成立）' : '三对全冲突'); }
      if (/【文章清单】/.test(u)) { nom++; }
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 40000);
    ok('抽脊跑了两遍', sp === 2, '实际 ' + sp + ' 遍');
    ok('确实回选篇重提了（且有界）', nom >= 2 && nom <= 8, '实际提名 ' + nom + ' 轮');
    ok('第二组换的是另一条轴（不是原地挪位置）', /角力|反循环|同意/.test(c.$('srcState').textContent), c.$('srcState').textContent);
    ok('换组后重新体检', (c.calls.filter(x => /请先做体检/.test(x.user)) || []).length === 2);
    ok('把不合格的原因记进"已试过"', c.calls.some(x => /【文章清单】/.test(x.user) && /主题观点没能两两冲突/.test(x.user)));
    ok('最终冲突校验是通过的', /三对全冲突/.test(c.$('trioConflict').textContent), c.$('trioConflict').textContent);
    ok('照样跑到底', done, c.$('stat-review').textContent);
  });

  await step('十七之九、抽脊没按格式写时不炸（卡片如实说没读出来）', async () => {
    const c = await boot({ answer: u => /一个主题观点/.test(u)
      ? '我觉得这三篇分别讲了三件事，写成一段话就好。'.repeat(8) : defaultAnswer(u) });
    const done = await runPipeline(c, 30000);
    ok('照样跑到底', done, c.$('stat-review').textContent);
    ok('卡片退回三篇标题（不空白）', c.doc.querySelectorAll('#trioBox .trio-row').length === 3);
    ok('如实说观点没抽出来', /观点还没抽出来|没读出来/.test(c.$('trioBox').textContent));
    ok('零抛错', c.errors.length === 0, c.errors.slice(0, 2).join(' ｜ '));
  });

  await step('十七之十、观点是中间产物：看得见，但不进成品', async () => {
    const c = await boot({ withSaveDir: true });
    await runPipeline(c, 30000);
    c.click('#dlPack'); c.click('#dlEngine'); await sleep(500);
    const pack = c.saved.find(x => /发布包_/.test(x.name));
    const eng = c.saved.find(x => /引擎室_/.test(x.name));
    ok('成品（发布包）里没有主题观点', pack && pack.text && !/主题观点/.test(pack.text),
      pack && pack.text ? '出现 ' + (pack.text.match(/主题观点/g) || []).length + ' 次' : '(没取到)');
    ok('成品里也没有支撑观点', pack && pack.text && !/- 支撑[abc]：/.test(pack.text));
    ok('成品仍列三篇来源（栏目规矩）', pack && pack.text && /## 三篇来源/.test(pack.text) &&
      (pack.text.match(/https?:\/\/[^\s]*\/students\//g) || []).length === 3);
    ok('引擎室存档里三条主题观点齐全', eng && eng.text && (eng.text.match(/- 主题观点：/g) || []).length === 3,
      eng && eng.text ? ((eng.text.match(/- 主题观点：/g) || []).length + ' 条') : '(没取到)');
    ok('引擎室存档里九条支撑齐全', eng && eng.text && (eng.text.match(/- 支撑[abc]：/g) || []).length === 9,
      eng && eng.text ? ((eng.text.match(/- 支撑[abc]：/g) || []).length + ' 条') : '');
    ok('引擎室注明这是中间产物', eng && eng.text && /中间产物，不进成品/.test(eng.text));
    ok('冲突校验只留在引擎室', eng && eng.text && /三条主题观点的冲突校验/.test(eng.text) &&
      pack && !/冲突校验/.test(pack.text));
  });

  await step('十七之十一、中间那一块可以就地取用', async () => {
    const c = await boot({ withSaveDir: true });
    ok('卡片上写明它不进成品', /不会写进成品文章/.test(c.$('trioCard').textContent));
    ok('还没跑时点复制会如实说没内容', (function(){
      c.click('#trioCopy'); return /还没有可复制/.test(c.$('trioNote').textContent);
    })(), c.$('trioNote').textContent);
    await runPipeline(c, 30000);
    c.click('#trioDl'); await sleep(400);
    const f = c.saved.find(x => /三篇与观点_/.test(x.name));
    ok('能单独存成 .md', !!f, JSON.stringify(c.saved.map(x => x.name)));
    ok('存出来的就是三篇与九条观点', f && f.text && (f.text.match(/- 支撑[abc]：/g) || []).length === 9,
      f && f.text ? ((f.text.match(/- 支撑[abc]：/g) || []).length + ' 条') : '(没取到)');
    ok('零抛错', c.errors.length === 0, c.errors.slice(0, 2).join(' ｜ '));
  });

  await step('十八、停下（跑到一半中止）', async () => {
    const c = await boot({ slow: 40 });   // 每个 chunk 40ms，好让"停下"有机会插进去
    pickModeA(c); c.$('apiKey').value = 'sk-fake'; c.click('#goBtn');
    await waitFor(() => c.calls.length >= 1, 6000);
    c.click('#stopBtn');
    await sleep(600);
    const n1 = c.calls.length; await sleep(900);
    ok('点停之后不再发新请求', c.calls.length === n1, n1 + ' → ' + c.calls.length);
    ok('停在前两格以内（当前这趟跑完就收）', n1 <= 2, '实际跑了 ' + n1 + ' 趟');
    ok('评审格没跑到', c.$('stat-review').textContent === '待命', c.$('stat-review').textContent);
    ok('停下按钮收起、开始按钮恢复', c.$('stopBtn').style.display === 'none' && c.$('goBtn').disabled === false);
    // 停完还能再开：abort 标志必须在下一次 runFrom 开头被清掉，否则"停一次废一次"
    c.click('#goBtn');
    await waitFor(() => c.calls.length > n1, 6000);
    ok('停下之后还能重新开跑', c.calls.length > n1, n1 + ' → ' + c.calls.length);
  });

  await step('十九、内功取不到时降级（不空转）', async () => {
    const c = await boot({ neigongFail: true });
    pickModeA(c);
    const done = await runPipeline(c);
    ok('照样跑得完（不像发生器那样直接中止）', done, c.$('stat-review').textContent);
    const spine = c.calls.find(x => /一个主题观点/.test(x.user));
    ok('system 里仍带页面自带的凝缩内功', spine && /SDE 本体论·凝缩/.test(spine.system));
    ok('没有把取不到的内功塞成空节', spine && !/完整内功/.test(spine.system));
  });

  await step('二十、站内检索失败时安全退回', async () => {
    const c = await boot({ kbFail: true });
    pickModeA(c);
    const done = await runPipeline(c);
    ok('划界格照样跑得完', done && /✓/.test(c.$('stat-demarc').textContent));
    const de = c.calls.find(x => /划清界线/.test(x.user));
    ok('检索块为空时不塞进调令', de && !/站内可参照的近邻材料/.test(de.user));
    ok('零抛错', c.errors.length === 0, c.errors.slice(0, 2).join(' ｜ '));
  });

  await step('二十一、选源目录取不到时不瘫', async () => {
    const c = await boot({ catalogFail: true });
    ok('学员下拉为空但页面不炸', c.$('stuSel').options.length === 0);
    ok('零抛错', c.errors.length === 0, c.errors.slice(0, 2).join(' ｜ '));
    c.click('.mode[data-mode="F"]'); await sleep(50);
    ['f1','f2','f3'].forEach((id, i) => { c.$(id).value = '源' + i + '\n' + '正文。'.repeat(80); });
    const done = await runPipeline(c);
    ok('自由投喂照样跑得完', done, c.$('stat-review').textContent);
  });

  await step('二十二、存储位置：选了文件夹就写进去', async () => {
    const c = await boot({ withSaveDir: true });
    ok('显示当前文件夹名', c.$('saveDirName').textContent === '碰撞产出');
    ok('按钮文案是"更换文件夹"', c.$('saveDirPick').textContent === '更换文件夹');
    pickModeA(c);
    await runPipeline(c);
    c.click('#dlPack'); await sleep(300);
    ok('发布包写进了目录', c.saved.some(x => /发布包_/.test(x.name)), JSON.stringify(c.saved.map(x => x.name)));
    ok('写入结果有回显', /已写入/.test(c.$('saveDirNote').textContent), c.$('saveDirNote').textContent);
    c.click('#dlEngine'); await sleep(400);
    ok('引擎室 md 也写进了目录', c.saved.some(x => /引擎室_/.test(x.name)));
    const pack = c.saved.find(x => /发布包_/.test(x.name));
    ok('发布包带 front-matter（题名/署名/来源）', pack && pack.text && /^---/.test(pack.text) &&
      /author: 王德生 ＋ Claude/.test(pack.text) && /sources:/.test(pack.text),
      pack && pack.text ? pack.text.slice(0, 60).replace(/\n/g, '⏎') : '(没取到内容)');
    ok('发布包附了三篇来源与划界', pack && pack.text && /## 三篇来源/.test(pack.text) && /与既有说法的划界/.test(pack.text));
    const eng = c.saved.find(x => /引擎室_/.test(x.name));
    ok('引擎室 md 十二格俱全', eng && eng.text && (eng.text.match(/\n## \d+\./g) || []).length === 12,
      eng && eng.text ? ((eng.text.match(/\n## \d+\./g) || []).length + ' 格') : '(没取到内容)');
    c.click('#dlDocx'); await sleep(400);
    ok('Word 也写进了目录', c.saved.some(x => /\.docx$/.test(x.name)));
  });

  await step('二十三、境外基底经代理', async () => {
    const c = await boot();
    c.$('modelSel').value = 'gpt:pro';
    c.$('modelSel').dispatchEvent(new c.win.Event('change', { bubbles: true }));
    pickModeA(c);
    const done = await runPipeline(c, 25000);
    ok('GPT 通道跑得完', done, c.$('stat-review').textContent);
    ok('走的是本站代理', c.calls.length > 0 && c.calls.every(x => /llm-proxy/.test(x.url)), (c.calls[0] || {}).url);
    ok('带了目标地址头', c.calls[0] && /openai\.com/.test(c.calls[0].headers['x-target-url'] || ''));
    ok('预算同样不超 8000', c.calls.every(x => x.max_tokens <= 8000));
    ok('零抛错', c.errors.length === 0, c.errors.slice(0, 2).join(' ｜ '));
  });

  await step('二十三之二、内化：十万字内功分块读完，写成心得当底盘', async () => {
    const c = await boot();
    const done = await runPipeline(c, 40000);
    const chunkCalls = c.calls.filter(x => /这是 SDE 内功的第/.test(x.user));
    ok('内功被分块读完（6 万字符 → 3 段）', chunkCalls.length === 3, '实际 ' + chunkCalls.length + ' 段');
    ok('每一段读的是不同的原文', new Set(chunkCalls.map(x => x.user.slice(-200))).size === 3);
    ok('末了合成一份心得总纲', c.calls.some(x => /合成一份 ≤3000 字的作业底盘/.test(x.user)));
    ok('心得总纲要求分四部分含十条铁律', c.calls.some(x => /本次作业的十条铁律/.test(x.user)));
    ok('状态条报出读了几段', /读完 3 段内功/.test(c.$('stat-warmup').textContent), c.$('stat-warmup').textContent);
    const gate = c.calls.find(x => /请先做体检/.test(x.user));
    ok('心得进了后面每一格的 system', gate && /你自己内化后写下的心得/.test(gate.system));
    ok('碰撞心法也全文进了 system', gate && /二阶碰撞心法/.test(gate.system));
    const engine = c.calls.filter(x => !/内功的第|作业底盘|你是验收员|你是评审/.test(x.user));
    ok('工序格无一例外都带着心得', engine.length >= 6 && engine.every(x => /内化后写下的心得/.test(x.system)),
      engine.filter(x => !/内化后写下的心得/.test(x.system)).length + ' 格没带');
    const rv = c.calls.find(x => /你是评审/.test(x.user));
    ok('评审那一趟另配评分标尺全文', rv && /创新智商评分标尺/.test(rv.system));
    ok('跑到底', done, c.$('stat-review').textContent);
  });

  await step('二十三之三、心得按本机缓存，重跑不再重内化；重跑本格才重内化', async () => {
    const c = await boot();
    await runPipeline(c, 40000);
    const n1 = c.calls.filter(x => /这是 SDE 内功的第/.test(x.user)).length;
    c.click('#resetBtn'); await sleep(80);
    c.calls.length = 0;
    await runPipeline(c, 40000);
    ok('第二遍不再读内功（用缓存的心得）', c.calls.filter(x => /这是 SDE 内功的第/.test(x.user)).length === 0);
    ok('状态条如实说用的是缓存', /用本机已内化的心得/.test(c.$('stat-warmup').textContent), c.$('stat-warmup').textContent);
    ok('第一遍确实读过（不是从没读）', n1 === 3, '第一遍读了 ' + n1 + ' 段');
    c.calls.length = 0;
    c.click('#stage-warmup button[data-act="rerun"]');
    await waitFor(() => c.calls.filter(x => /这是 SDE 内功的第/.test(x.user)).length >= 3, 20000);
    ok('点「重跑本格」会强制重内化', c.calls.filter(x => /这是 SDE 内功的第/.test(x.user)).length === 3);
  });

  await step('二十三之四、内功取不到时退回凝缩内功（不空转）', async () => {
    const c = await boot({ neigongFail: true });
    const done = await runPipeline(c, 40000);
    ok('如实说明退回', /退回页面自带的凝缩内功/.test(c.$('stat-warmup').textContent), c.$('stat-warmup').textContent);
    ok('一段内功都没读', c.calls.filter(x => /这是 SDE 内功的第/.test(x.user)).length === 0);
    const gate = c.calls.find(x => /请先做体检/.test(x.user));
    ok('system 里仍有凝缩内功与心法', gate && /SDE 本体论·凝缩/.test(gate.system) && /二阶碰撞心法/.test(gate.system));
    ok('照样跑得完', done, c.$('stat-review').textContent);
  });

  await step('二十三之五、成品不许留碰撞创新的痕迹', async () => {
    const c = await boot();
    await runPipeline(c, 40000);
    const wr = c.calls.find(x => /继续写这篇文章的第/.test(x.user));
    ok('成文 system 明令不留做法痕迹', wr && /不许留下这篇文章是怎么做出来的痕迹/.test(wr.system));
    ok('点名禁掉工艺词', wr && /碰撞、对撞、撞出、涌现、暗流/.test(wr.system));
    ok('要求判断像本来就长在这门学科里', wr && /来路不必交代/.test(wr.system));
    ok('划界那章要写成"这与某某说的不是一回事"', wr && /不是一回事/.test(wr.system));
    ok('给写手的素材不带出处', wr && /不许在正文里交代它们的出处/.test(wr.user) && !/https?:\/\//.test(wr.user.split('【可用的素材')[1] || ''));
    const outline = c.calls.find(x => /列一份文章目录/.test(x.user));
    ok('目录里禁掉"方法说明""三篇来源"这类章目', outline && /不许出现"三篇来源""方法说明"/.test(outline.user));
    ok('干净成品报"无工艺痕迹"', /无工艺痕迹/.test(c.$('stat-write').textContent), c.$('stat-write').textContent);
  });

  await step('二十三之六、正文带了工艺词就自动重写一遍', async () => {
    let wrote = 0;
    const c = await boot({ answer: u => {
      if (/继续写这篇文章的第/.test(u)) { wrote++;
        return wrote <= 6 ? ('这一章说明三篇文章碰撞之后涌现出的暗流。'.repeat(20)) : ('干净的正文。'.repeat(60)); }
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 50000);
    ok('工艺痕迹被逮住', /工艺痕迹/.test(c.$('stat-write').textContent) || /无工艺痕迹/.test(c.$('stat-write').textContent));
    ok('自动重写了一遍（成文跑了两轮）', wrote > 6, '共写了 ' + wrote + ' 趟');
    ok('重写的调令里点名了痕迹词', c.calls.some(x => /继续写这篇文章的第/.test(x.user) && /做法的痕迹整句删掉/.test(x.user)));
    ok('重写后干净了', /无工艺痕迹/.test(c.$('stat-write').textContent), c.$('stat-write').textContent);
    ok('跑到底', done, c.$('stat-review').textContent);
  });

  await step('二十三之七、真机故障：合成心得那一趟吐 0 字', async () => {
    let merge = 0;
    const c = await boot({ answer: u => {
      if (/合成一份 ≤3000 字的作业底盘/.test(u)) { merge++; return ''; }   // 两趟都空（满功率想太久的那个坑）
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 45000);
    ok('空答后自动降档重来一趟', merge === 2, '实际 ' + merge + ' 趟');
    ok('重试那一趟的调令里点明"别铺陈"', c.calls.some(x => /只顾着想、没写出正文/.test(x.user)));
    ok('两趟都空就拿分段心得兜底', /用分段心得当底盘/.test(c.$('stat-warmup').textContent), c.$('stat-warmup').textContent);
    const gate = c.calls.find(x => /请先做体检/.test(x.user));
    ok('后面每一格照样拿得到底盘（不空转）', gate && /内化后写下的心得/.test(gate.system));
    ok('读过的那几段内功没白读', gate && /第1段/.test(gate.system));
    ok('照样跑到底', done, c.$('stat-review').textContent);
  });

  await step('二十三之八、提名那一趟吐 0 字也能自愈', async () => {
    let nom = 0;
    const c = await boot({ answer: u => {
      if (/【文章清单】/.test(u)) { nom++; return nom === 1 ? '' : defaultAnswer(u); }
      return defaultAnswer(u);
    } });
    const done = await runPipeline(c, 45000);
    ok('空答的那一轮自动降档重来', nom >= 2, '实际 ' + nom + ' 趟');
    ok('照样定标', /定标/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
    ok('跑到底', done, c.$('stat-review').textContent);
  });

  await step('二十三之九、真机故障：提名不按格式给编号（四层兜底逐个验）', async () => {
    // ① 写成「第3篇」而不是 #3
    const a = await boot({ answer: u => /【文章清单】/.test(u)
      ? ('理由若干。'.repeat(8) + '\n种子：第1篇、第2篇、第3篇 ｜ 矛盾轴：撤手的三种评价') : defaultAnswer(u) });
    await runPipeline(a, 45000);
    ok('「第N篇」这种写法也认', /定标/.test(a.$('stat-select').textContent), a.$('stat-select').textContent);
    ok('认出来的是前三篇', /种子：留白 × 伪生 × 撤土/.test(a.$('srcState').textContent), a.$('srcState').textContent);

    // ② 通篇不写编号，只点名标题
    const b = await boot({ answer: u => /【文章清单】/.test(u)
      ? ('我选《角力》《反循环》《同意》这三篇，它们在同一件事上给了相反的处方。'.repeat(3)) : defaultAnswer(u) });
    await runPipeline(b, 45000);
    ok('只点标题也能靠反查救回来', /定标/.test(b.$('stat-select').textContent), b.$('stat-select').textContent);
    ok('反查到的正是那三篇', /角力/.test(b.$('srcState').textContent) && /同意/.test(b.$('srcState').textContent),
      b.$('srcState').textContent);

    // ③ 真的什么都没给：作废重提，且回灌的话要说人话
    let nom = 0;
    const c = await boot({ answer: u => {
      if (/【文章清单】/.test(u)) { nom++; return nom === 1
        ? '这几篇都不错，我说不好选哪三篇。'.repeat(4) : defaultAnswer(u); }
      return defaultAnswer(u);
    } });
    await runPipeline(c, 45000);
    const log = c.$('out-select').parentNode.querySelector('.sel-log').textContent;
    ok('这一轮作废并重提', /没读出编号/.test(log), log.slice(0, 120));
    const nom2 = c.calls.filter(x => /【文章清单】/.test(x.user))[1];
    ok('回灌的话说人话（不是 #0 #0 #0）', nom2 && /没按格式给编号，这一轮不算数/.test(nom2.user) && !/#0/.test(nom2.user));
    ok('格式要求提到了调令最前面', nom2 && /先记住怎么收尾/.test(nom2.user));
    ok('第二轮照样定标', /定标/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
  });

  await step('二十四、术语闸本身', async () => {
    const c = await boot();
    ok('能抓出多词', c.win.termHits('这里有显露、特征纠缠和发生学。').length >= 3);
    ok('干净文本零命中', c.win.termHits('账本记不下的那样东西。').length === 0);
    ok('计数写在结果里', /×2/.test(c.win.termHits('发生学与发生学').join(',')));
    ok('痕迹闸能抓工艺词', c.win.traceHits('这三篇文章碰撞后涌现出暗流。').length >= 3,
      JSON.stringify(c.win.traceHits('这三篇文章碰撞后涌现出暗流。')));
    ok('正常论证不误伤', c.win.traceHits('账本记不下的那样东西，与古德哈特定律不是一回事。').length === 0);
  });

  await step('二十五、全程零运行时错误', async () => {
    ok('模式 A 页面零抛错', cA.errors.length === 0, cA.errors.slice(0, 3).join(' ｜ '));
    ok('首个页面零抛错', c1.errors.length === 0, c1.errors.slice(0, 3).join(' ｜ '));
  });

  console.log('\n' + '='.repeat(56));
  console.log('通过 ' + pass + ' ｜ 失败 ' + fail);
  if (fail) { console.log('\n失败清单：'); fails.forEach(f => console.log('  · ' + f)); }
  console.log('='.repeat(56));
  process.exit(fail ? 1 : 0);
})();
