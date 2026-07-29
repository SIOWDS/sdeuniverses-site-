#!/usr/bin/env node
/* 「SDE 碰撞出典范」页面模拟测试 —— 用 jsdom 跑 public/taste/paradigm-forge/index.html 里的真代码。
 *
 * 铁律：改这一页（或改 tools/forge/forge.template.html 后重跑构建器）必跑本脚本。
 *   node tools/sim_paradigm_forge.js
 *   FORGE_HTML=/tmp/broken.html node tools/sim_paradigm_forge.js     # 变异检验：指向改坏的副本
 *
 * 依赖 jsdom（装在 /home/claude/node_modules；缺了就 cd /home/claude && npm install jsdom）。
 * 三个已知坑，已在下面处理：
 *  ① 页面错误必须经 VirtualConsole 的 jsdomError/error 收集才拿得到——只留个空数组是假测试；
 *  ② jsdom 没有 scrollIntoView / TextDecoder(window)，要在 beforeParse 里补，否则会在无关处炸；
 *  ③ 每步包在 step() 里 try/catch——页面坏掉时要出完整报告，而不是甩一段堆栈。
 */
const fs = require('fs');
const path = require('path');

let JSDOM;
try { ({ JSDOM } = require(process.env.JSDOM_PATH || '/home/claude/node_modules/jsdom')); }
catch (e) {
  try { ({ JSDOM } = require('jsdom')); }
  catch (e2) { console.error('缺 jsdom：cd /home/claude && npm install jsdom'); process.exit(2); }
}

const HTML = process.env.FORGE_HTML ||
  path.join(__dirname, '..', 'public', 'taste', 'paradigm-forge', 'index.html');

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

/* ---------- 假数据 ---------- */
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
    { slug: 'zhang-qiong', name: '张琼', count: 3, items: [
      { title: '留白', url: '/students/zhang-qiong/a/', kind: 'x', summary: 's' },
      { title: '伪生', url: '/students/zhang-qiong/b/', kind: 'x', summary: 's' },
      { title: '撤土', url: '/students/zhang-qiong/c/', kind: 'x', summary: 's' }] },
    { slug: 'gao-peng', name: '高鹏', count: 2, items: [
      { title: '禁令的肉身', url: '/students/gao-peng/a/', kind: 'x', summary: 's' },
      { title: '公正的沉默塌缩', url: '/students/gao-peng/b/', kind: 'x', summary: 's' }] },
    { slug: 'hu-min', name: '胡敏', count: 2, items: [
      { title: '悬契', url: '/students/hu-min/a/', kind: 'x', summary: 's' },
      { title: '复现土', url: '/students/hu-min/b/', kind: 'x', summary: 's' }] }
  ]
};
const ARTICLE_HTML = '<html><head><title>假文章</title></head><body><nav>导航</nav>' +
  '<article>' + '这是一篇假的站内文章正文。'.repeat(120) + '</article>' +
  '<script>console.log(1)<\/script><footer>页脚</footer></body></html>';

/* 假 SSE：按调令内容回不同的产物，好让下游工序有东西可吃 */
function fakeAnswer(userMsg) {
  if (/列一份文章目录/.test(userMsg)) {
    return Array.from({ length: 16 }, (_, i) => '第' + (i + 1) + '章、章名' + (i + 1) + ' —— 落一件事').join('\n');
  }
  if (/继续写这篇文章的第/.test(userMsg)) return '章节正文。'.repeat(60);
  if (/你是评审/.test(userMsg)) return '总分：152\n五维：S=150 D=151 E=152 I=153 F=150\n判级：典范级';
  if (/请先做体检/.test(userMsg)) return '闸一：分数 8/10 ｜ 打架点一句话：三方对同一件事判了相反的处方\n闸二：同源度 低\n闸三：无近邻\n总判：放行';
  return '产物：一段假的工序输出。';
}
function sseFor(text) {
  const chunks = [];
  chunks.push('data: ' + JSON.stringify({ choices: [{ delta: { reasoning_content: '思考…' } }] }) + '\n\n');
  for (let i = 0; i < text.length; i += 400) {
    chunks.push('data: ' + JSON.stringify({ choices: [{ delta: { content: text.slice(i, i + 400) } }] }) + '\n\n');
  }
  chunks.push('data: ' + JSON.stringify({ choices: [{ delta: {}, finish_reason: 'stop' }] }) + '\n\n');
  chunks.push('data: [DONE]\n\n');
  return chunks;
}

/* ---------- 起页面 ---------- */
const errors = [];
let calls = [];

function makeFetch(win) {
  return function (url, opts) {
    url = String(url);
    if (url.indexOf('catalog.json') >= 0) return respJSON(CATALOG);
    if (url.indexOf('publications.json') >= 0) return respJSON(STUDENTS);
    if (url.indexOf('sde-neigong.txt') >= 0) return respText('SDE 内功正文。'.repeat(900)); // >5000 字
    if (url.indexOf('/api/kb/retrieve') >= 0) return respJSON({ block: '【站内材料】假的检索块' });
    if (url.indexOf('chat/completions') >= 0 || url.indexOf('/api/llm-proxy') >= 0) {
      const body = JSON.parse(opts.body);
      const msgs = body.messages || [];
      const userMsg = (msgs[msgs.length - 1] || {}).content || '';
      calls.push({ url, max_tokens: body.max_tokens, model: body.model, system: (msgs[0] || {}).content || '', user: userMsg });
      const chunks = sseFor(fakeAnswer(userMsg));
      let i = 0;
      return Promise.resolve({
        ok: true, status: 200,
        body: { getReader: () => ({ read: () => i < chunks.length
            ? Promise.resolve({ done: false, value: Buffer.from(chunks[i++]) })
            : Promise.resolve({ done: true, value: undefined }) }) }
      });
    }
    // 站内文章
    return respText(ARTICLE_HTML);

    function respJSON(o) { return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(o), text: () => Promise.resolve(JSON.stringify(o)) }); }
    function respText(s) { return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(s), json: () => Promise.resolve({}) }); }
  };
}

(async function main() {
  console.log('页面：' + HTML);
  const html = fs.readFileSync(HTML, 'utf8');
  const { VirtualConsole } = require(process.env.JSDOM_PATH || '/home/claude/node_modules/jsdom');
  const vc = new VirtualConsole();
  vc.on('jsdomError', e => errors.push('jsdomError: ' + (e && e.message)));
  vc.on('error', (...a) => errors.push('console.error: ' + a.join(' ')));

  const dom = new JSDOM(html, {
    runScripts: 'dangerously', url: 'https://sdeuniverses.com/taste/paradigm-forge/',
    virtualConsole: vc, pretendToBeVisual: true,
    beforeParse(win) {
      win.fetch = makeFetch(win);
      win.TextDecoder = TextDecoder;
      win.TextEncoder = TextEncoder;
      win.AbortController = AbortController;
      win.Element.prototype.scrollIntoView = function () {};
      win.HTMLElement.prototype.scrollIntoView = function () {};
      win.scrollTo = function () {};
      win.alert = function () {};
      win.URL.createObjectURL = () => 'blob:fake';
      win.HTMLAnchorElement.prototype.click = function () {};   // 否则 jsdom 会报"navigation to another Document"
      win.URL.revokeObjectURL = () => {};
      // 外部库替身
      win.docx = {
        Document: function (o) { this.o = o; },
        Packer: { toBlob: () => Promise.resolve(new win.Blob(['x'])) },
        Paragraph: function (o) { this.o = o; },
        TextRun: function (o) { this.o = o; },
        AlignmentType: { CENTER: 'center' },
        HeadingLevel: { HEADING_1: 'h1', HEADING_2: 'h2' }
      };
      // WDSSaveDir 故意不注入：验"不支持时如实降级"
    }
  });
  const win = dom.window, doc = win.document;
  await sleep(300);

  await step('一、页面起得来', async () => {
    ok('十道工序面板都在', doc.querySelectorAll('.stage').length === 10, '实际 ' + doc.querySelectorAll('.stage').length);
    ok('基底选择器有 DeepSeek Pro', !!doc.querySelector('option[value="ds:pro"]'));
    ok('Key 标签跟着基底走', /DeepSeek/.test(doc.getElementById('keyLabel').textContent));
    ok('选源目录已载入（模式 A 有学员）', doc.getElementById('stuSel').options.length === 3,
      '实际 ' + doc.getElementById('stuSel').options.length);
    ok('存储位置在无 API 时如实降级', /不支持选择文件夹/.test(doc.getElementById('saveDirNote').textContent));
  });

  await step('二、模式切换', async () => {
    const click = sel => { const el = doc.querySelector(sel); el.dispatchEvent(new win.MouseEvent('click', { bubbles: true })); };
    click('.mode[data-mode="C"]');
    await sleep(50);
    ok('模式 C 面板出现', !doc.getElementById('mC').classList.contains('hidden'));
    ok('模式 C 三个下拉都填上了候选', [0, 1, 2].every(i => doc.getElementById('cSel' + i).options.length > 0));
    // 关键词筛
    const q = doc.getElementById('cQ0'); q.value = '睡眠';
    q.dispatchEvent(new win.Event('input', { bubbles: true }));
    await sleep(30);
    const opts = Array.from(doc.getElementById('cSel0').options).map(o => o.textContent);
    ok('关键词能把候选筛窄', opts.length > 0 && opts.every(t => /睡眠/.test(t)), '共 ' + opts.length + ' 条');
    click('.mode[data-mode="A"]');
    await sleep(30);
    ok('切回模式 A', !doc.getElementById('mA').classList.contains('hidden'));
  });

  await step('三、选三个源 + 跑完十道工序', async () => {
    doc.getElementById('apiKey').value = 'sk-fake';
    const boxes = doc.querySelectorAll('#stuList input[type=checkbox]');
    ok('学员篇目列出来了', boxes.length === 3, '实际 ' + boxes.length);
    for (const b of boxes) { b.checked = true; b.dispatchEvent(new win.Event('change', { bubbles: true })); }
    ok('已选 3 个源', /已选 3 \/ 3/.test(doc.getElementById('srcState').textContent));
    calls = [];
    doc.getElementById('goBtn').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
    // 等流水线跑完（假 SSE 很快，但成文要分趟）
    for (let i = 0; i < 300 && !/^✓/.test(doc.getElementById('stat-review').textContent) &&
      !/创新智商/.test(doc.getElementById('stat-review').textContent); i++) await sleep(50);
    ok('体检格出了结果', /✓/.test(doc.getElementById('stat-gate').textContent), doc.getElementById('stat-gate').textContent);
    ok('抽脊格出了结果', /✓/.test(doc.getElementById('stat-spine').textContent));
    ok('涌现格出了结果', /✓/.test(doc.getElementById('stat-emerge').textContent));
    ok('成文格出了字数', /字/.test(doc.getElementById('stat-write').textContent), doc.getElementById('stat-write').textContent);
    ok('评审格读出了创新智商', /创新智商 152/.test(doc.getElementById('stat-review').textContent), doc.getElementById('stat-review').textContent);
    ok('交付区已亮出', doc.getElementById('deliver').style.display !== 'none');
  });

  await step('四、预算纪律（满功率档不许超 8000）', async () => {
    const over = calls.filter(c => c.max_tokens > 8000);
    ok('没有任何一趟超过 8000 tokens', over.length === 0, over.map(c => c.max_tokens).join(','));
    const writeCalls = calls.filter(c => /继续写这篇文章的第/.test(c.user));
    ok('成文是分趟写的（≥4 趟）', writeCalls.length >= 4, '实际 ' + writeCalls.length + ' 趟');
    ok('成文每趟不超过 4000', writeCalls.every(c => c.max_tokens <= 4000));
  });

  await step('五、命根子：三条工序纪律', async () => {
    const spine = calls.find(c => /各抽三条最承重的判断/.test(c.user));
    ok('抽脊调令要求三视角各一条', spine && /结果层[\s\S]*路径层[\s\S]*条件层/.test(spine.user));
    const collide = calls.find(c => /跨篇两两对撞/.test(c.user));
    ok('碰撞调令写死了"同篇内部作废"', collide && /同一篇内部的对[\s\S]*一律作废/.test(collide.user));
    ok('碰撞调令要求无焦点即作废', collide && /无焦点/.test(collide.user));
    const emerge = calls.find(c => /五重检验/.test(c.user));
    ok('涌现调令有五重检验且含自反', emerge && /自反/.test(emerge.user) && /反噬预言/.test(emerge.user));
    ok('涌现调令要求证伪条件与赌注', emerge && /证伪条件/.test(emerge.user) && /赌注/.test(emerge.user));
    const demarc = calls.find(c => /划清界线/.test(c.user));
    ok('划界调令要求 6–10 个近邻', demarc && /6–10 个/.test(demarc.user));
    ok('划界这一格把站内检索块垫了进去', demarc && /站内可参照的近邻材料/.test(demarc.user));
    const writeCall = calls.find(c => /继续写这篇文章的第/.test(c.user));
    ok('成文的 system 里写死了术语零容忍', writeCall && /不得出现任何学派术语/.test(writeCall.system));
    ok('成文调令要求直接写正文、不复述目录', writeCall && /不要复述目录/.test(writeCall.user));
    const spineCall = calls.find(c => /各抽三条最承重的判断/.test(c.user));
    ok('成文用的是另一套 system（改姓），与工序 system 不同', writeCall && spineCall && writeCall.system !== spineCall.system);
    const review = calls.find(c => /你是评审/.test(c.user));
    ok('评审是独立一趟、且 system 说明只评不写', review && /只评不写/.test(review.system));
    ok('评审有反膨胀封顶', review && /封顶/.test(review.user));
  });

  await step('六、术语零容忍闸', async () => {
    const w = win.termHits('这段话里有显露和特征纠缠，还有发生学。');
    ok('术语能被抓出来', w.length >= 3, JSON.stringify(w));
    ok('干净文本零命中', win.termHits('这段话很干净，讲的是账本记不下的那样东西。').length === 0);
  });

  await step('七、单格重跑与"从这里继续"', async () => {
    calls = [];
    const btn = doc.querySelector('#stage-emerge button[data-act="rerun"]');
    btn.dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
    for (let i = 0; i < 80 && calls.length === 0; i++) await sleep(30);
    await sleep(200);
    ok('重跑只打了这一格', calls.length === 1, '实际 ' + calls.length + ' 次调用');
    ok('重跑的是涌现这一格', calls[0] && /五重检验/.test(calls[0].user));
  });

  await step('八、编辑产物能存回', async () => {
    const b = doc.querySelector('#stage-spine button[data-act="edit"]');
    b.dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
    const ta = doc.querySelector('#stage-spine textarea');
    ok('点开出现编辑框', !!ta);
    if (ta) {
      ta.value = '我手改过的九条';
      b.dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
      ok('存回后产物变成手改的内容', /我手改过的九条/.test(doc.getElementById('out-spine').textContent));
    }
  });

  await step('九、导出通道不炸', async () => {
    doc.getElementById('dlDocx').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
    doc.getElementById('dlPack').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
    doc.getElementById('dlEngine').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
    await sleep(200);
    ok('三个导出按钮点下去没抛错', true);
  });

  await step('十、清空后能再来一次', async () => {
    doc.getElementById('resetBtn').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
    await sleep(50);
    ok('工序状态复位', doc.getElementById('stat-emerge').textContent === '待命');
    ok('交付区收起', doc.getElementById('deliver').style.display === 'none');
    ok('产物清空', /还没跑到这一格/.test(doc.getElementById('out-spine').textContent));
  });

  await step('十一、页面运行期零抛错', async () => {
    ok('无 jsdom 运行时错误', errors.length === 0, errors.slice(0, 3).join(' ｜ '));
  });

  console.log('\n' + '='.repeat(56));
  console.log('通过 ' + pass + ' ｜ 失败 ' + fail);
  if (fail) { console.log('\n失败清单：'); fails.forEach(f => console.log('  · ' + f)); }
  console.log('='.repeat(56));
  process.exit(fail ? 1 : 0);
})();
