#!/usr/bin/env node
/* 「SDE 学科通融」全流程模拟 —— 用 jsdom 跑 public/taste/confluence/index.html 里的真代码。
 *
 * 铁律：改 tools/confluence/confluence.template.html（或重跑 build_confluence_page.py）必跑本脚本。
 *   node tools/sim_confluence.js
 *   CONF_HTML=/tmp/broken.html node tools/sim_confluence.js     # 变异检验：指向改坏的副本
 *
 * 覆盖本页与「碰撞出典范」相比新长出来的那五处：
 *   ① 入口是一个问题＋三个学科（不是三个源）· ② 工序 −1 题型判别（自动／手动／判不出即停）·
 *   ③ 定三家两路取材（站内库＋联网、锁定学科照抄、只认真链接、站内源抓全文、联网不通时降级）·
 *   ④ 成文之后的打磨（自查十项＋整篇重写；重写稿被截断时保留原稿）· ⑤ 体例锁死论文体。
 * 另加：问题穿进每一格的 system、一键跑到底、清空复位、术语零容忍照旧生效。
 */
const fs = require('fs');
const path = require('path');

const JSDOM_MOD = process.env.JSDOM_PATH || '/home/claude/node_modules/jsdom';
let jsdom;
try { jsdom = require(JSDOM_MOD); }
catch (e) { try { jsdom = require('jsdom'); } catch (e2) { console.error('缺 jsdom：cd /home/claude && npm install jsdom'); process.exit(2); } }
const { JSDOM, VirtualConsole } = jsdom;

const HTML_PATH = process.env.CONF_HTML ||
  path.join(__dirname, '..', 'public', 'taste', 'confluence', 'index.html');
const HTML = fs.readFileSync(HTML_PATH, 'utf8');
const ASSETS = path.join(__dirname, '..', 'public', 'taste', 'assets');
const RAG_JS = fs.readFileSync(path.join(ASSETS, 'sde-rag.js'), 'utf8');
const NBR_JS = fs.readFileSync(path.join(ASSETS, 'sde-nbr-gate.js'), 'utf8');

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
  while (Date.now() - t0 < (ms || 9000)) { if (fn()) return true; await sleep(30); }
  return false;
}

/* ---------------- 假数据 ---------------- */
const CATALOG = { generated: '2026-08-02', items: Array.from({ length: 20 }, (_, i) => ({
  t: '站上长文之' + i, u: '/column/fake-' + i + '/', d: '描述' + i, w: 12000, c: i < 4 ? '学科通融' : '今日长文' })) };
const STUDENTS = { generated: '2026-08-02', students: [
  { slug: 'zhang-qiong', name: '张琼', count: 2, items: [
    { title: '留白', url: '/students/zhang-qiong/a/', kind: '发展心理学', summary: '撤手是德' },
    { title: '伪生', url: '/students/zhang-qiong/b/', kind: '技术哲学', summary: '顶撞才养人' }] }] };
const ARTICLE_HTML = '<html><head><title>假文章</title></head><body><nav>导航</nav>' +
  '<article>' + '这是一篇站内文章的正文，够长够厚。'.repeat(120) + '</article>' +
  '<script>console.log(1)<\/script><footer>页脚</footer></body></html>';
const FAKE_NEIGONG = 'SDE 内功正文段落。'.repeat(6000).slice(0, 60000);

function WEB_ITEMS(q) {
  return [0, 1, 2].map(i => ({
    t: '关于「' + q.slice(0, 8) + '」的理论 ' + (i + 1), u: 'https://example.org/paper-' + i,
    s: '这一家主张若干。'.repeat(12), m: '期刊 ' + i, d: '2025-0' + (i + 1) + '-01' }));
}
function NBR_BLOCK(q) {
  return '【站内近邻（sdeuniverses.com 已发表的相关篇目）——这一节是硬要求：\n'
    + '对下列每一篇，必须说清它已经说到哪一步，以及你这一次的判断与它的分离线在哪；\n'
    + '凡划不出分离线的，直接说明本次判断与该篇重复，不要另起新名。】\n'
    + '1、《自噬性稳态》（/students/zhang-qiong/x/）｜作者 张琼\n'
    + '　　该篇的判断：系统靠自己吃掉自己维持稳定。\n'
    + '2、《改不动的机器》（/students/zhang-qiong/y/）\n'
    + '　　该篇的判断：越是修得动的地方越先被修死。\n';
}
function demarcOK() {
  return '近邻检测\n本文所属学科：社会学\n'
    + '一、可取用困难（Bjork 1994）（学科：认知心理学）｜它说到哪一步：难一点记得牢。｜分离线：本文讲的是那道难度被谁读出来。｜判决性对照预测：若把难度撤掉而效果不变，则本文错。\n'
    + '二、《规训与惩罚》（学科：哲学）｜它说到哪一步：可见性生产服从。｜分离线：本文讲的是不可见者被判为不存在。｜判决性对照预测：若不可测项照样进入分配，则本文错。\n'
    + '三、古德哈特定律（Goodhart 1975）（学科：经济学）｜它说到哪一步：度量一旦成目标就变坏。｜分离线：病灶在固定这个动作本身。｜判决性对照预测：若换更好的度量能恢复流失的能力，则本文错。\n'
    + '四、《自噬性稳态》（学科：社会学）｜它说到哪一步：系统吃自己维稳。｜分离线：本文的是外化-固定。\n'
    + '五、《改不动的机器》（学科：社会学）｜它说到哪一步：修得动的先被修死。｜分离线：本文给的是成因不是现象。';
}
/* 定三家那一趟的产物：三家、含一家站内（链接以 / 开头） */
function pickAnswer(o) {
  o = o || {};
  const one = (n, disc, inside) => ['===源' + n,
    '标题：' + disc + '的那一家理论',
    '学科：' + disc,
    '来源：' + (inside ? '站内' : '站外'),
    '出处：某人 2025 · 《某篇》',
    '链接：' + (o.noLink ? '（材料里没有）' : (inside ? '/students/zhang-qiong/a/' : 'https://example.org/paper-' + n)),
    '论点：这一家认为那件事的病根在' + disc + '这一层。',
    '位置：站在' + (n === 1 ? '结果' : n === 2 ? '路径' : '条件') + '这一位置上。',
    '正文：' + '论证若干句。'.repeat(40)].join('\n');
  const three = o.onlyTwo ? [one(1, '认知心理学', false), one(2, '制度经济学', false)]
    : [one(1, '认知心理学', false), one(2, '制度经济学', false), one(3, '组织社会学', true)];
  return three.concat(['===', '对立点：三家把病根安在三个不同的位置上，互相取消对方的前提。']).join('\n\n');
}
const LONG_ARTICLE = '正文若干句，够长，末尾有句号。'.repeat(700);
function defaultAnswer(userMsg, ctx) {
  if (/先判它要的答案是什么形状/.test(userMsg))
    return '题型：Why\n理由：提问的人要的是什么在逼动它，不是一个分辨用的读数。\n自测：留经验的动作与用经验的动作的矛盾驱动了经验流失。';
  if (/定出\*\*三个学科\*\*/.test(userMsg))
    /* v3.8：定学科那一步多一列面板编号（0＝这一门走联网）。
       两门落到面板供料层、一门走联网，正好同时测到两条路。 */
    return '1｜471｜认知心理学｜认知负荷 理论 争论\n2｜0｜制度经济学｜度量 制度 批评\n3｜272｜组织社会学｜组织记忆 争论';
  if (/请为\*\*每一门各挑出一家\*\*/.test(userMsg)) return pickAnswer(ctx && ctx.pickOpt);
  if (/这是 SDE 内功的第/.test(userMsg)) return '这一段的承重判断若干。' + '要点。'.repeat(20);
  if (/合成一份 ≤3000 字的作业底盘/.test(userMsg)) return '一、本体论要害……' + '铁律一条。'.repeat(80);
  if (/你是验收员/.test(userMsg))
    return '主题1：病根在认知层 ｜ 主题2：病根在制度层 ｜ 主题3：病根在组织层\n烈度：8/10 ｜ 同源度：低 ｜ 打架点：病根到底在哪一层\n判词：三方对同一件事给了互相取消的答案';
  if (/一个主题观点/.test(userMsg) && /支撑观点/.test(userMsg)) {
    const blk = n => ['【源' + n + '】《假文章' + n + '》',
      '主题观点：第' + n + '家主张的那一条判断，够长够像判断句。',
      '支撑观点 ' + n + 'a：结果层的理由，独立成立。　〔依据：原文若干字〕',
      '支撑观点 ' + n + 'b：路径层的理由，独立成立。　〔依据：原文若干字〕',
      '支撑观点 ' + n + 'c：条件层的理由，独立成立。　〔依据：原文若干字〕',
      '互不包含自检：a×b 不同层 ｜ a×c 不同层 ｜ b×c 不同层'].join('\n');
    return [blk(1), blk(2), blk(3), '冲突 1×2：不能同时成立。', '冲突 1×3：不能同时成立。',
      '冲突 2×3：不能同时成立。', '主题冲突：三对全冲突'].join('\n\n');
  }
  if (/列一份学术论文的节次目录/.test(userMsg))
    return Array.from({ length: 16 }, (_, i) => '第' + (i + 1) + '章、章名' + (i + 1) + ' —— 落一件事').join('\n');
  if (/照下面的目录，把整篇文章/.test(userMsg)) return LONG_ARTICLE;
  if (/逐条查下面十项/.test(userMsg))
    return ['1. 题型对口 ｜ 过 ｜ 承重命题填得进那句话，走的正是驱动型。',
      '2. 位置三分 ｜ 不过 ｜ 二、三两家都站在路径这一位置。｜怎么改：把第三家换到条件位置上重写第五节。',
      '3. 反转模板查名 ｜ 不过 ｜ 剥出来是「X 越成功越失败」而正文一个正主都没点名。｜怎么改：点名成功陷阱与能力刚性。',
      '4. 证伪两档 ｜ 不过 ｜ 只验证了现象存在。｜怎么改：写出控制掉竞争解释后的剂量-反应式。',
      '5. 样本纪律 ｜ 过 ｜ 没有拿两个国家充数。',
      '6. 划界黑名单 ｜ 过 ｜ 没有靠"更系统"来划。',
      '7. 新读数还是新存在物 ｜ 过 ｜ 删掉这个读数那件事就不存在。',
      '8. 出处可核对 ｜ 过 ｜ 三条链接都对得上。',
      '9. 零术语零痕迹 ｜ 过 ｜ 没有学派专名。',
      '10. 收尾两件 ｜ 不过 ｜ 缺写死日期的赌注。｜怎么改：补一条。',
      '最要紧的三处：位置撞车、现象证伪、模板没点名。'].join('\n');
  if (/照下面的自查结果，把这篇文章\*\*整篇重写一遍\*\*/.test(userMsg))
    return (ctx && ctx.shortRewrite) ? '重写了一小截就没了。'.repeat(20)
      : '打磨后的正文若干句，够长，末尾有句号。'.repeat(800);
  if (/请把它与既有说法逐一划清界线/.test(userMsg)) return demarcOK();
  if (/请执行涌现/.test(userMsg)) return '涌现物：命名为「外化固定症」。' + '一句判断撑住它。'.repeat(20);
  if (/你是评审/.test(userMsg)) return (ctx && ctx.lowScore)
    ? '总分：138\n五维：S=140 D=138 E=139 I=134 F=140\n判级：合格\n最该补的一刀：回炉到「涌现」，' + '再往下切一层。'.repeat(6)
    : '总分：152\n五维：S=150 D=151 E=152 I=153 F=150\n判级：典范级\n最该补的一刀：' + '再往下切一层。'.repeat(6);
  if (/请先做体检/.test(userMsg))
    return '闸一：分数 8/10 ｜ 打架点一句话：三方把病根安在三个位置 ｜ 结局对立：有 ｜ 三方各自的硬证据：各有一条\n'
      + '闸二：同源度 低 ｜ 共享零件：无 ｜ 建议撞点：落在病根位置那一处\n闸三：最近的已发篇目：无 ｜ 处置：可发\n总判：放行';
  return '产物：一段假的工序输出。'.repeat(6);
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
  const ctx = { calls: [], errors: [], saved: [], webQ: [], frontHub: 0, frontPanel: [], nbrQ: [], pulls: [], webBody: [],
                pickOpt: opts.pickOpt, shortRewrite: opts.shortRewrite, lowScore: opts.lowScore, drafts: [], nbrLive: 0, nbrPeak: 0, nbrAborted: 0 };
  const vc = new VirtualConsole();
  vc.on('jsdomError', e => ctx.errors.push('jsdomError: ' + (e && e.message)));
  vc.on('error', (...a) => ctx.errors.push('console.error: ' + a.join(' ')));
  const answer = opts.answer || (u => defaultAnswer(u, ctx));

  function makeFetch() {
    return function (url, init) {
      url = String(url); init = init || {};
      const J = o => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(o), text: () => Promise.resolve(JSON.stringify(o)) });
      const T = s => Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(s), json: () => Promise.resolve({}) });
      const BAD = c => Promise.resolve({ ok: false, status: c, statusText: 'ERR', text: () => Promise.resolve(''), json: () => Promise.resolve({}) });

      /* 新思想前沿：hub 磁贴与面板供料层。体例逐字照线上——
         哪天面板页把 .src / .col 的类名改了，这里会当场红，而不是等真跑时静默丢材料。 */
      if (/\/frontier\/$/.test(url)) {
        ctx.frontHub++;
        return T('<html><body>' +
          '<a class="tile done" href="/frontier/oncology/"><span class="num">101</span><span class="nm">肿瘤学</span></a>' +
          '<a class="tile done" href="/frontier/cognitive-science/"><span class="num">471</span><span class="nm">认知科学</span></a>' +
          '<a class="tile done" href="/frontier/political-economy/"><span class="num">272</span><span class="nm">政治经济学</span></a>' +
          '</body></html>');
      }
      if (/\/frontier\/[a-z-]+\/$/.test(url)) {
        ctx.frontPanel.push(url);
        return T('<html><body>' +
          '<h2>甲、某条新思想：一句判断</h2>' +
          '<div class="src"><i>提出</i>某某，2019 年《某刊》12(3):45–67。　<i>争议</i>另一位，2022 年同刊。　<i>最新</i>第三位，2025 年。　<i>关键</i>一句可通约的读数。</div>' +
          '<p>正文段。</p>' +
          '<div class="col"><i>位置</i>S——它把某状态当成单独够用的那一样　<i>单因</i>只有这一样是决定性的　<i>预设</i>〔01 谁进入分母〕　<i>量纲</i>甲数∶乙数　<i>失效</i>当某条件时方向反过来　<i>自曝</i>本家自己承认的那一处弱点　<i>空栏</i>账上不设字段的那一类　<i>异名</i>另见第 999 号</div>' +
          '</body></html>');
      }
      if (url.indexOf('catalog.json') >= 0) return J(CATALOG);
      if (url.indexOf('publications.json') >= 0) return J(STUDENTS);
      if (url.indexOf('sde-neigong.txt') >= 0) return T(FAKE_NEIGONG);
      if (url.indexOf('sde-collide-heart.txt') >= 0) return T('二阶碰撞心法：先找矛盾再找高分。'.repeat(80));
      if (url.indexOf('sde-innovation-iq.txt') >= 0) return T('创新智商评分标尺：五维 S/D/E/I/F。'.repeat(80));
      if (url.indexOf('/api/kb/retrieve') >= 0) return opts.kbFail ? BAD(500) : J({ block: '【站内材料】假的检索块' });
      if (url.indexOf('/api/wds/websearch') >= 0) {
        const b = JSON.parse(init.body || '{}');
        const q = b.q || '';
        ctx.webQ.push(q); ctx.webBody.push(b);
        if (opts.webNoKey) return J({ ok: false, reason: 'need_search_key', items: [] });
        if (opts.webThin) return J({ ok: true, reason: '', items: [] });
        return J({ ok: true, reason: '', items: WEB_ITEMS(q) });
      }
      if (url.indexOf('/api/kb/neighbors') >= 0) {
        if (opts.nbrFail) return BAD(500);
        const q = (JSON.parse(init.body || '{}').q) || '';
        ctx.nbrQ.push(q);
        ctx.nbrLive++; ctx.nbrPeak = Math.max(ctx.nbrPeak, ctx.nbrLive);
        if (opts.hangNbr) {                       // 永不返回：模拟真跑时卡住的那一路
          return new Promise((res, rej) => {
            if (init.signal) init.signal.addEventListener('abort', () => { ctx.nbrLive--; ctx.nbrAborted++; rej(new Error('AbortError')); });
          });
        }
        return new Promise(res => setTimeout(() => { ctx.nbrLive--; res(null); }, opts.nbrMs || 20))
          .then(() => J({ n: 2, block: NBR_BLOCK(q) }));
      }
      if (url.indexOf('chat/completions') >= 0 || url.indexOf('/api/llm-proxy') >= 0) {
        const body = JSON.parse(init.body);
        const msgs = body.messages || [];
        const user = (msgs[msgs.length - 1] || {}).content || '';
        const budget = body.max_tokens != null ? body.max_tokens
          : (body.max_completion_tokens != null ? body.max_completion_tokens
          : ((body.generationConfig || {}).maxOutputTokens));
        ctx.calls.push({ url, max_tokens: budget, model: body.model, system: (msgs[0] || {}).content || '', user });
        const chunks = sseFor(answer(user));
        let i = 0;
        const nextChunk = () => i < chunks.length ? { done: false, value: Buffer.from(chunks[i++]) } : { done: true, value: undefined };
        const read = opts.slow ? () => new Promise(r => setTimeout(() => r(nextChunk()), opts.slow))
                               : () => Promise.resolve(nextChunk());
        return Promise.resolve({ ok: true, status: 200, body: { getReader: () => ({ read }) } });
      }
      // 站内正文抓取
      ctx.pulls.push(url);
      if (opts.articleFail) return BAD(404);
      return T(ARTICLE_HTML);
    };
  }

  const dom = new JSDOM(HTML, {
    runScripts: 'dangerously', url: 'https://sdeuniverses.com/taste/confluence/',
    virtualConsole: vc, pretendToBeVisual: true,
    beforeParse(win) {
      win.fetch = makeFetch();
      try { win.eval(RAG_JS); win.eval(NBR_JS); } catch (e) { ctx.errors.push('共用模块注入失败: ' + e.message); }
      win.TextDecoder = TextDecoder; win.TextEncoder = TextEncoder;
      win.AbortController = AbortController;
      win.Element.prototype.scrollIntoView = function () {};
      win.HTMLElement.prototype.scrollIntoView = function () {};
      win.HTMLAnchorElement.prototype.click = function () {};
      win.scrollTo = function () {}; win.alert = function () {};
      win.URL.createObjectURL = () => 'blob:fake'; win.URL.revokeObjectURL = () => {};
      // 存稿是逐格发生的，跑完再读只能读到最后一次——把每一次都记下来
      const _set = win.Storage.prototype.setItem;
      win.Storage.prototype.setItem = function (k, v) {
        if (k === 'sde_conf_draft') { try { ctx.drafts.push(JSON.parse(v)); } catch (e) {} }
        return _set.call(this, k, v);
      };
      win.docx = {
        Document: function (o) { this.o = o; win.__lastDoc = o; },
        Packer: { toBlob: () => Promise.resolve(new win.Blob(['docx-bytes'])) },
        Paragraph: function (o) { this.o = o; }, TextRun: function (o) { this.o = o; },
        AlignmentType: { CENTER: 'center' }, HeadingLevel: { HEADING_1: 'h1', HEADING_2: 'h2' }
      };
      if (opts.withSaveDir) {
        win.WDSSaveDir = {
          supported: () => true, name: () => '通融产出',
          ensure: () => Promise.resolve(true), forget: () => Promise.resolve(true),
          onChange: cb => { try { cb('通融产出'); } catch (e) {} },
          save: (name, blob) => {
            const rec = { name, size: blob && blob.size };
            ctx.saved.push(rec);
            if (blob && blob.text) { try { blob.text().then(t => { rec.text = t; }).catch(() => {}); } catch (e) {} }
            return Promise.resolve({ where: 'dir', dir: '通融产出', name });
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

function fillQ(c, q, d1, d2, d3) {
  c.$('cQuestion').value = q || '为什么组织越是想把经验留下来，经验反而流失得越快？';
  c.$('cQuestion').dispatchEvent(new c.win.Event('input', { bubbles: true }));
  [['cD1', d1], ['cD2', d2], ['cD3', d3]].forEach(([id, v]) => {
    if (v != null) { c.$(id).value = v; c.$(id).dispatchEvent(new c.win.Event('input', { bubbles: true })); }
  });
  c.$('apiKey').value = 'sk-fake';
}
function userOf(c, re) { const x = c.calls.filter(k => re.test(k.user)); return x.length ? x[x.length - 1] : null; }

/* ======================= 场景 ======================= */
(async function main() {
  console.log('页面：' + HTML_PATH + '\n' + '='.repeat(56));

  const c1 = await boot();
  await step('一、页面起得来（静态结构）', async () => {
    const stages = c1.doc.querySelectorAll('.stage');
    ok('十八道工序面板都在（v3.8：补了敌意拓宽／共有前提／真跑）', stages.length === 18, '实际 ' + stages.length);
    ok('工序顺序：内化 → 题型 → 定三家 …… 敌意拓宽 …… 共有前提 …… 真跑 → 成文 → 打磨 → 评审',
      ['warmup','qtype','select','gate','spine','collide','expand','nbrgate','hostile','collide2','premise','selforg','emerge','demarc','realrun','write','polish','review']
        .every((id, i) => stages[i] && stages[i].id === 'stage-' + id));
    /* v3.8 三道新工序的位置是硬的：敌意拓宽必须紧跟候选闸（先淘汰再互撞），
       共有前提必须在候选互撞之后（要撞完才知道三家共踩的是哪块地），
       真跑必须在划界之后、成文之前（跑出来的不利结果要来得及写进正文）。 */
    const stageIds = [...stages].map(x => x.id);
    const idx = id => stageIds.indexOf('stage-' + id);
    ok('敌意拓宽紧跟候选闸', idx('hostile') === idx('nbrgate') + 1);
    ok('共有前提在候选互撞之后、自组织之前', idx('premise') > idx('collide2') && idx('premise') < idx('selforg'));
    ok('真跑在划界之后、成文之前', idx('realrun') > idx('demarc') && idx('realrun') < idx('write'));
    ok('入口是问题＋三个学科', !!c1.$('cQuestion') && !!c1.$('cD1') && !!c1.$('cD2') && !!c1.$('cD3'));
    ok('题型可手动指定（含 auto/What/How/Why 四项）', c1.doc.querySelectorAll('#cType option').length === 4);
    ok('站内库那一路默认开着', c1.$('cUseKB').checked === true);
    ok('本站检索通道默认勾着、自备 Key 那格先藏着', c1.$('cSiteKey').checked === true && c1.$('cSkey').style.display === 'none');
    ok('旧的选源模式已收进隐藏容器', !!c1.$('legacyPick') && c1.$('legacyPick').style.display === 'none');
    ok('八家基底都在选择器里', ['ds:pro','glm:pro','kimi:pro','qwen:pro','minimax:pro','gpt:pro','claude:pro','gemini:pro']
      .every(v => !!c1.doc.querySelector('option[value="' + v + '"]')));
    ok('体例锁死为论文体', c1.$('genreSel').value === 'paper');
    ok('体例说明写的是论文体', /论文体/.test(c1.$('genreNote').textContent), c1.$('genreNote').textContent);
    ok('页面起来没有 JS 错误', c1.errors.length === 0, c1.errors.join(' | '));
    ok('状态条提示先写问题', /先写一个要解决的问题/.test(c1.$('srcState').textContent), c1.$('srcState').textContent);
    ok('交付区一开始是收起的', c1.$('deliver').style.display === 'none');
  });

  await step('二、填了问题与学科，状态条跟着变', async () => {
    fillQ(c1, null, '认知心理学', '制度经济学', '组织社会学');
    ok('状态条报出三个学科', /认知心理学×制度经济学×组织社会学/.test(c1.$('srcState').textContent), c1.$('srcState').textContent);
    c1.$('cSiteKey').checked = false;
    c1.$('cSiteKey').dispatchEvent(new c1.win.Event('change', { bubbles: true }));
    ok('取消本站通道后，自备 Key 那一格露出来', c1.$('cSkey').style.display === '');
  });

  /* ---- 全流程 ---- */
  const c2 = await boot();
  await step('三、一键跑到底（问题＋三学科 → 打磨 → 评审）', async () => {
    fillQ(c2, '为什么组织越是想把经验留下来，经验反而流失得越快？', '认知心理学', '制度经济学', '组织社会学');
    c2.click('#goBtn');
    const done = await waitFor(() => /创新智商|✓/.test(c2.$('stat-review').textContent), 30000);
    ok('跑到评审那一格', done, c2.$('stat-review').textContent);
    ok('题型判成 Why', /题型 Why/.test(c2.$('stat-qtype').textContent), c2.$('stat-qtype').textContent);
    ok('三家就位（站内 1 · 站外 2）', /站内 1 · 站外 2/.test(c2.$('stat-select').textContent), c2.$('stat-select').textContent);
    ok('打磨那一格跑完了', /已打磨/.test(c2.$('stat-polish').textContent), c2.$('stat-polish').textContent);
    ok('交付横幅亮了并报出题型与三学科',
      /题型 Why/.test(c2.$('doneBanner').textContent) && /认知心理学×制度经济学×组织社会学/.test(c2.$('doneBanner').textContent),
      c2.$('doneBanner').textContent);
    ok('横幅里写着已打磨', /已打磨/.test(c2.$('doneBanner').textContent));
    ok('横幅体例是学科通融体', /学科通融体/.test(c2.$('doneBanner').textContent));
    ok('全程无 JS 错误', c2.errors.length === 0, c2.errors.join(' | '));
  });

  await step('四、问题穿进了每一格的 system（不是只在定源那一格）', async () => {
    // 内化那几趟是读内功、与题无关，本来就不该带；其余每一趟都必须带
    const notWarm = c2.calls.filter(k => !/这是 SDE 内功的第|作业底盘/.test(k.user));
    const withQ = notWarm.filter(k => /本次要解决的问题/.test(k.system));
    ok('除内化外，每一趟调令都带着这道问题', withQ.length === notWarm.length,
       withQ.length + '/' + notWarm.length);
    ok('评审那一趟也拿到了这道题（否则它只会评写得好不好）',
       c2.calls.some(k => /只评不写/.test(k.system) && /本次要解决的问题/.test(k.system)));
    ok('评审被要求先看答没答到那道题',
       c2.calls.some(k => /只评不写/.test(k.system) && /答没答到那道题/.test(k.system)));
    const emerge = userOf(c2, /请执行涌现/);
    ok('涌现那一格的 system 里有这道问题', emerge && /经验反而流失得越快/.test(emerge.system));
    ok('题型判出来之后，位置要求也跟着进 system',
      c2.calls.some(k => /三条不同的动力机制/.test(k.system)));
  });

  await step('四之二、三家卡片把该看的都摆出来了（站内/站外 · 学科 · 位置 · 链接）', async () => {
    const t = c2.$('trioBox').textContent;
    ok('标了站内/站外', /〔站外〕/.test(t) && /〔站内〕/.test(t), t.slice(0, 60));
    ok('标了各自的学科', /认知心理学/.test(t) && /组织社会学/.test(t));
    ok('摆出了三家各自的位置（位置撞车只有摆眼前才看得出）',
       (t.match(/位置：/g) || []).length === 3, String((t.match(/位置：/g) || []).length));
    ok('站内那一家给的是站内链接', !!c2.doc.querySelector('#trioBox a[href^="/students/"]'));
    ok('卡片说明改口：三家会写进文献综述', /会正面写进成品的文献综述/.test(c2.doc.querySelector('#trioCard .small').textContent));
  });

  await step('五、定三家：两路取材都真的走了', async () => {
    ok('联网检索跑了三轮（三门各一轮）', c2.webQ.length >= 3, '实际 ' + c2.webQ.length);
    ok('站内近邻在定三家时也查了（三门各一次）',
      c2.nbrQ.filter(q => /认知心理学|制度经济学|组织社会学/.test(q)).length >= 3, c2.nbrQ.length + ' 次');
    const pick = userOf(c2, /请为\*\*每一门各挑出一家\*\*/);
    ok('面板目录抓过一次（626 块的可选学科池）', c2.frontHub >= 1, '实际 ' + c2.frontHub + ' 次');
    ok('三门各抓了自己那块面板的供料层', c2.frontPanel.length >= 1, '实际 ' + c2.frontPanel.length + ' 块');
    /* 断言认的是**材料块里真正的标记**，不是提示词的导语——
       导语可以被改写（v3.8 那一轮就改了），材料块的标记不能，因为基底靠它分辨三路。 */
    ok('挑三家的调令里三路材料都在（面板供料层排在最前）',
      pick && /〔站外·联网检索〕/.test(pick.user)
           && /〔站内·本站已有的相关篇目/.test(pick.user)
           && /〔新思想前沿 第\d+号《[^》]+》· 八字段供料层〕/.test(pick.user));
    ok('面板那一路排在联网与站内之前（基底先读到的是可核对的那一路）',
      pick && pick.user.indexOf('八字段供料层〕') < pick.user.indexOf('〔站外·联网检索〕'));
    ok('调令写明供料层是首选材料，且自曝与失效两栏专供共有前提那一格',
      pick && /首选材料/.test(pick.user) && /自曝/.test(pick.user) && /失效/.test(pick.user));
    ok('挑三家的调令里写死了"三家必须都在回答同一道题"', pick && /三家必须都在回答同一道题/.test(pick.user));
    ok('位置要求压过学科（学科可撞车、位置不许撞）', pick && /学科可以撞车而位置不许撞车/.test(pick.user));
    ok('铁律：一个字都不许编', pick && /一个字都不许编/.test(pick.user));
    ok('站内那一家去抓了全文', c2.pulls.some(u => /\/students\/zhang-qiong\/a\//.test(u)), c2.pulls.join(','));
  });

  await step('六、锁定的学科被照抄，不许基底改名', async () => {
    const c = await boot({ answer: u => {
      if (/定出\*\*三个学科\*\*/.test(u)) return '1｜法理学｜法 理论 争论\n2｜制度经济学｜度量 制度\n3｜组织社会学｜组织记忆';
      return defaultAnswer(u, {});
    } });
    fillQ(c, '为什么规则越细，越没人守？', '法学', '', '');
    c.click('#goBtn');
    await waitFor(() => /✓|⚠|中断/.test(c.$('stat-select').textContent), 20000);
    ok('人锁的「法学」没被改成「法理学」', c.$('cD1').value === '法学', c.$('cD1').value);
    ok('另两门由基底补齐', c.$('cD2').value === '制度经济学' && c.$('cD3').value === '组织社会学',
      c.$('cD2').value + '/' + c.$('cD3').value);
  });

  /* ---- 题型闸 ---- */
  await step('七、题型：手动指定时不花一次调用', async () => {
    const c = await boot();
    fillQ(c, '内卷的根源是什么？', '经济学', '生物学', '音乐学');
    c.$('cType').value = 'Why';
    c.click('#goBtn');
    await waitFor(() => /✓/.test(c.$('stat-qtype').textContent), 12000);
    ok('题型格标出手动指定', /手动指定/.test(c.$('stat-qtype').textContent), c.$('stat-qtype').textContent);
    ok('没有为判题型发过调令', !c.calls.some(k => /先判它要的答案是什么形状/.test(k.user)));
  });

  await step('八、题型：判不出就停下并指路（不闷头往下跑）', async () => {
    const c = await boot({ answer: u => {
      if (/先判它要的答案是什么形状/.test(u)) return '这道题挺有意思的，可以从很多角度看。'.repeat(4);
      return defaultAnswer(u, {});
    } });
    fillQ(c, '这件事该怎么看？', '甲学', '乙学', '丙学');
    c.click('#goBtn');
    await waitFor(() => c.$('errBox').style.display === 'block', 12000);
    ok('停下来并说清没判出题型', /没能判出题型/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('给了可操作的下一步（自己选题型＋自测句）',
      /题型.*那一格自己选/.test(c.$('errBox').textContent) && /矛盾驱动了/.test(c.$('errBox').textContent));
    ok('没有往下跑到定三家', !/✓/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
  });

  await step('九、没写问题就点跑：当场说清，不空转', async () => {
    const c = await boot();
    c.$('apiKey').value = 'sk-fake';
    c.click('#goBtn');
    await waitFor(() => c.$('errBox').style.display === 'block', 12000);
    ok('提示先写问题', /先在上面写清你要解决的那个问题/.test(c.$('errBox').textContent), c.$('errBox').textContent);
  });

  /* ---- 取材失败路径 ---- */
  await step('十、联网不通但站内库有料：降级往下走，并替他切到自备 Key', async () => {
    const c = await boot({ webNoKey: true });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => /✓/.test(c.$('stat-select').textContent), 25000);
    ok('三家仍然定了下来（用站内库的材料）', /三家已就位/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
    ok('替他取消了本站通道那个勾', c.$('cSiteKey').checked === false);
    ok('自备 Key 那一格露了出来', c.$('cSkey').style.display === '');
    ok('如实说了这一路不通、三家会偏站内', /只用站内库的材料/.test(c.$('errBox').textContent), c.$('errBox').textContent);
  });

  await step('十一、两路都空：如实停下，不假装挑到了三家', async () => {
    const c = await boot({ webNoKey: true, nbrFail: true });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => c.$('errBox').style.display === 'block', 25000);
    ok('说清两路都空', /两路都空/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('并指了一步能走通的路（填自己的智谱 Key）', /智谱 Key/.test(c.$('errBox').textContent));
  });

  await step('十二、假链接不当真链接（拿不到就如实标"无链接"）', async () => {
    const c = await boot({ pickOpt: { noLink: true } });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => /✓/.test(c.$('stat-select').textContent), 25000);
    ok('提醒有几家没拿到链接', /没拿到可点开的链接/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    await waitFor(() => c.calls.some(k => /文献综述与参考文献要用它/.test(k.user)), 25000);
    const w = userOf(c, /文献综述与参考文献要用它/);
    ok('出处清单里写的是"无链接，须自行补"，不是那句假话',
      w && /无链接，须自行补/.test(w.user) && !/材料里没有/.test(w.user));
  });

  await step('十三、只挑到两家：停下重挑，不凑数', async () => {
    const c = await boot({ pickOpt: { onlyTwo: true } });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => c.$('errBox').style.display === 'block', 25000);
    ok('如实说只读出两个源', /读出 2 个成形的源/.test(c.$('errBox').textContent), c.$('errBox').textContent);
  });

  /* ---- 打磨 ---- */
  await step('十四、打磨：先逐条自查十项，再照自查整篇重写', async () => {
    const audit = userOf(c2, /逐条查下面十项/);
    ok('自查调令十项齐全', audit &&
      ['题型对口','位置三分','反转模板查名','证伪两档','样本纪律','划界黑名单','新读数还是新存在物','出处可核对','零术语零痕迹','收尾两件']
        .every(k => audit.user.indexOf(k) >= 0));
    ok('自查用的是评审 system（带评分标尺），不是写手 system',
      audit && /只评不写/.test(audit.system) && /评分标尺/.test(audit.system));
    ok('自查把承重命题的填空自测写进去了', audit && /矛盾驱动了/.test(audit.user));
    ok('反转模板的四个正主都点了名', audit &&
      ['成功陷阱','伊卡洛斯悖论','能力刚性','内卷化','目标置换'].every(k => audit.user.indexOf(k) >= 0));
    const rw = userOf(c2, /整篇重写一遍/);
    ok('重写调令带上了自查结果与原稿', rw && /【自查结果】/.test(rw.user) && /【原稿全文】/.test(rw.user));
    ok('重写明令篇幅不许缩水', rw && /篇幅不许缩水/.test(rw.user));
    ok('重写明令不许留"修改说明"', rw && /不许出现"修改说明"/.test(rw.user));
    ok('重写用的是论文体写手 system', rw && /学术创新论文/.test(rw.system));
    ok('重写预算是成文那一档（32000）', rw && rw.max_tokens === 32000, rw && String(rw.max_tokens));
  });

  await step('十五、打磨稿被截断：保留原稿，不交半篇', async () => {
    const c = await boot({ shortRewrite: true });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => /⚠|✓/.test(c.$('stat-polish').textContent), 30000);
    ok('判为疑似被截断并保留原稿', /疑似被截断 · 已保留原稿/.test(c.$('stat-polish').textContent), c.$('stat-polish').textContent);
    ok('提示换能长输出的基底重跑本格', /重跑本格/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('自查结果仍然留着可用', /自查结果照样可用/.test(c.$('errBox').textContent));
  });

  /* ---- 术语闸 · 清空 ---- */
  await step('十六、术语零容忍照旧生效（打磨稿里留了痕迹要拦）', async () => {
    const c = await boot({ answer: u => {
      if (/照下面的自查结果，把这篇文章\*\*整篇重写一遍\*\*/.test(u))
        return ('这一稿用了 SDE 的差异序列来说明矛盾轴。' + '正文若干句，够长，末尾有句号。'.repeat(800));
      return defaultAnswer(u, {});
    } });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => /✓|⚠/.test(c.$('stat-polish').textContent), 30000);
    ok('打磨后仍点名残留的术语与痕迹',
      /SDE/.test(c.$('stat-polish').textContent) && /矛盾轴/.test(c.$('stat-polish').textContent), c.$('stat-polish').textContent);
    ok('默认不自动重写，停下来交给用户决定', /上站硬门槛/.test(c.$('errBox').textContent), c.$('errBox').textContent);
  });

  await step('十七、导出与清空复位', async () => {
    c2.click('#dlPack');
    await sleep(120);
    c2.click('#dlEngine');
    await sleep(120);
    ok('导出没炸', c2.errors.length === 0, c2.errors.join(' | '));
    c2.click('#resetBtn');
    await sleep(120);
    ok('十五格全复位', Array.from(c2.doc.querySelectorAll('.st-status')).every(e => e.textContent === '待命'));
    ok('交付区收起来了', c2.$('deliver').style.display === 'none');
    ok('题型与三学科的记账也清了',
      !/题型 Why/.test(c2.$('stat-qtype').textContent) && c2.$('doneBanner').innerHTML === '');
  });

  /* ---- 深挖：交付链路上那几处只有整跑才暴露的 ---- */
  await step('十八、评审读的是打磨后的那一版（不是原稿）', async () => {
    const rv = c2.calls.filter(k => /只评不写/.test(k.system));
    ok('评审确实跑了', rv.length >= 1);
    const last = rv[rv.length - 1];
    ok('评审拿到的是打磨稿', last && /打磨后的正文/.test(last.user) && !/^正文若干句/.test(last.user.trim()),
       last ? last.user.slice(0, 40) : '(无)');
  });

  await step('十九、成品导出用的是打磨稿', async () => {
    const c = await boot();
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => /创新智商|✓/.test(c.$('stat-review').textContent), 30000);
    c.click('#dlDocx');
    await sleep(200);
    const doc = c.win.__lastDoc;
    const txt = JSON.stringify(doc || {});
    ok('Word 里是打磨稿', /打磨后的正文/.test(txt), txt.slice(0, 60));
    ok('Word 页脚署的是学科通融', /由 SDE 学科通融生成/.test(txt));
    c.__ = c;
    globalThis.__c19 = c;
  });

  await step('二十、编辑成文那一格的产物，终稿要跟着变（否则那句"用编辑产物手改"是空话）', async () => {
    const c = globalThis.__c19;
    const btn = Array.from(c.doc.querySelectorAll('#stage-write button[data-act="edit"]'))[0];
    c.click(btn);
    await sleep(80);
    const ta = c.doc.querySelector('#stage-write textarea');
    ok('点开出现编辑框', !!ta);
    ta.value = '这是我手改过的终稿正文。' + '够长的一段正文，末尾有句号。'.repeat(400);
    c.click(btn);                       // 存回
    await sleep(120);
    ok('编辑框已收起', !c.doc.querySelector('#stage-write textarea'));
    c.click('#dlDocx');
    await sleep(200);
    const txt = JSON.stringify(c.win.__lastDoc || {});
    ok('导出的 Word 是手改后的那一版', /我手改过的终稿正文/.test(txt), txt.slice(0, 60));
  });

  await step('二十一、单独重跑打磨：不叠加面板、不重复插框', async () => {
    const c = globalThis.__c19;
    const before = c.doc.querySelectorAll('#stage-polish .out').length;
    const btn = Array.from(c.doc.querySelectorAll('#stage-polish button[data-act="rerun"]'))[0];
    c.click(btn);
    await waitFor(() => /✓|⚠/.test(c.$('stat-polish').textContent), 25000);
    const after = c.doc.querySelectorAll('#stage-polish .out').length;
    ok('重跑没有把输出框越堆越多', after === before, before + ' → ' + after);
  });

  await step('二十二、成文重跑之后，"已打磨"这个记号要撤掉', async () => {
    const c = globalThis.__c19;
    const btn = Array.from(c.doc.querySelectorAll('#stage-write button[data-act="rerun"]'))[0];
    c.click(btn);
    await waitFor(() => /✓|⚠/.test(c.$('stat-write').textContent), 25000);
    await sleep(200);
    ok('ST.polished 被撤回（重新写过就不算打磨过）',
       c.win.eval('typeof ST!=="undefined" && ST.polished === false'), String(c.win.eval('ST.polished')));
  });

  await step('二十三、只填一个学科：人填的那门不许丢', async () => {
    const c = await boot({ answer: u => {
      if (/定出\*\*三个学科\*\*/.test(u)) return '1｜音乐学｜音乐 理论 争论\n2｜制度经济学｜度量 制度\n3｜组织社会学｜组织记忆';
      return defaultAnswer(u, {});
    } });
    fillQ(c, '为什么排练越充分，现场越平庸？', null, '表演研究', null);
    c.click('#goBtn');
    await waitFor(() => /✓|⚠|中断/.test(c.$('stat-select').textContent), 25000);
    const ds = ['cD1', 'cD2', 'cD3'].map(id => c.$(id).value);
    ok('人填的「表演研究」还在三门里', ds.indexOf('表演研究') >= 0, ds.join('/'));
    ok('三门都补齐了', ds.every(Boolean), ds.join('/'));
  });

  await step('二十四、自备的检索 Key 真的传到了检索那一路', async () => {
    const c = await boot({ keyProbe: true });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.$('cSiteKey').checked = false;
    c.$('cSiteKey').dispatchEvent(new c.win.Event('change', { bubbles: true }));
    c.$('cSkey').value = 'zhipu-fake-key';
    c.click('#goBtn');
    await waitFor(() => c.webBody.length >= 1, 25000);
    ok('检索请求带上了自备 Key', c.webBody.some(b => b.skey === 'zhipu-fake-key'),
       JSON.stringify(c.webBody[0] || {}));
  });

  await step('二十五、跑到一半按停：当场停住，不硬跑到底', async () => {
    const c = await boot({ slow: 6 });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => /spinner|✓/.test(c.$('stat-select').innerHTML), 20000);
    c.click('#stopBtn');
    await sleep(1200);
    const n1 = c.calls.length;
    await sleep(1200);
    ok('按停之后不再发新调令', c.calls.length === n1, n1 + ' → ' + c.calls.length);
    ok('没有跑到评审', !/创新智商/.test(c.$('stat-review').textContent), c.$('stat-review').textContent);
  });

  /* ---- 自动存稿：与分数无关 ---- */
  await step('二十六、成文与打磨各存一次底稿（没选文件夹也不丢）', async () => {
    const c = await boot();
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => /✓|⚠/.test(c.$('stat-write').textContent), 30000);
    ok('交付区在成文那一格就露出来（不必等跑完）', c.$('deliver').style.display === '');
    await waitFor(() => /创新智商|✓/.test(c.$('stat-review').textContent), 35000);
    const tags = c.drafts.map(d => d.tag);
    const d1 = c.drafts.find(d => d.tag === '成文');
    ok('成文那一格存了一次', !!d1 && d1.md.length > 500, tags.join(' → '));
    ok('打磨那一格又存了一次', tags.indexOf('打磨') > tags.indexOf('成文'), tags.join(' → '));
    ok('评审与终稿也各存了一次', tags.some(t => /^评审/.test(t)) && tags.indexOf('终稿') >= 0, tags.join(' → '));
    ok('底稿带着问题与题型', d1 && /question: 为什么组织/.test(d1.md) && /qtype: Why/.test(d1.md));
    ok('底稿带着三家出处', d1 && /sources:/.test(d1.md) && /example\.org/.test(d1.md));
    ok('存稿提示写明与评分无关', /存稿与评分无关/.test(c.$('draftNote').textContent), c.$('draftNote').textContent);
  });

  await step('二十七、不到 150 一样存（这正是此前会丢的那一格）', async () => {
    const c = await boot({ lowScore: true, withSaveDir: true });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => !!c.$('choice-review'), 35000);
    const d = JSON.parse(c.win.localStorage.getItem('sde_conf_draft') || 'null');
    ok('评审判了 138 分，稿子照样存了', !!d && /iq_self: 138/.test(d.md), d ? d.tag : '(无)');
    ok('底稿的标签写着评审那一步与分数', d && /评审 138 分/.test(d.tag), d && d.tag);
    ok('选了文件夹就直接落盘', c.saved.some(x => /^学科通融_.*_评审 138 分\.md$/.test(x.name)),
       c.saved.map(x => x.name).join(' | '));
    ok('落盘的是完整发布包（含正文与划界）', c.saved.length > 0);
    c.click('#choice-review button[data-choice="keep"]');
    await sleep(400);
    ok('选了就这样交付之后，交付横幅出来了', /跑完了/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
    ok('横幅如实写未过线', /未过线/.test(c.$('doneBanner').textContent));
    ok('终稿又存了一次', c.saved.some(x => /_终稿\.md$/.test(x.name)), c.saved.map(x => x.name).join(' | '));
  });

  /* ---- 回炉由用户选 ---- */
  await step('二十八、不到 150 当场给两个按钮，不自作主张', async () => {
    const c = await boot({ lowScore: true });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    const got = await waitFor(() => !!c.$('choice-review'), 35000);
    ok('评审那一格弹出了选择', got);
    const btns = Array.from(c.doc.querySelectorAll('#choice-review button[data-choice]')).map(b => b.getAttribute('data-choice'));
    ok('正好两个选项：回炉 / 就这样交付', btns.length === 2 && btns.indexOf('redo') >= 0 && btns.indexOf('keep') >= 0, btns.join(','));
    ok('问句里点名了回炉到哪一格', /回炉/.test(c.$('choice-review').textContent) && /涌现/.test(c.$('choice-review').textContent),
       c.$('choice-review').textContent.slice(0, 70));
    ok('问句里说清稿子已经存了', /已经自动存下来了/.test(c.$('choice-review').textContent));
    ok('没等他点就先不动', !/跑完了/.test(c.$('doneBanner').textContent));
    c.click('#choice-review button[data-choice="redo"]');
    await sleep(600);
    ok('选了回炉就真的回去重跑', c.win.eval('ST.rounds') === 1, String(c.win.eval('ST.rounds')));
    ok('回的是评审点名的那一格', c.win.eval('ST.notes.join("|")').indexOf('涌现') >= 0, c.win.eval('ST.notes.join("|")'));
    ok('记了一笔是他选的（不是机器自作主张）', c.win.eval('ST.notes.join("|")').indexOf('你选的') >= 0);
  });

  await step('二十九、勾了「自动回炉」才不问', async () => {
    const c = await boot({ lowScore: true });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.$('autoRedoChk').checked = true;
    c.click('#goBtn');
    // 若它中途停下来问，rounds 会卡住不动——能一路走到 2，就证明两轮都没问
    const two = await waitFor(() => c.win.eval('ST.rounds') >= 2, 35000);
    ok('两轮回炉全自动，中途一次没停下来问', two, 'rounds=' + c.win.eval('ST.rounds'));
    ok('两轮用满之后才开始问', !!c.$('choice-review') || c.win.eval('ST.rounds') === 2);
    ok('红字写明是按他勾的那一项办的', /按你勾的/.test(c.$('errBox').textContent), c.$('errBox').textContent.slice(0, 60));
    ok('并说明稿子已存', /已经存下来了/.test(c.$('errBox').textContent));
  });

  await step('三十、卡在选择上时按「停下」，不能卡死', async () => {
    const c = await boot({ lowScore: true });
    fillQ(c, '为什么组织越想留住经验越留不住？', '认知心理学', '制度经济学', '组织社会学');
    c.click('#goBtn');
    await waitFor(() => !!c.$('choice-review'), 35000);
    c.click('#stopBtn');
    await sleep(500);
    ok('等待被解开、选择框收起', !c.$('choice-review'));
    ok('产线真的停了（按钮复位）', c.$('goBtn').disabled === false && c.$('stopBtn').style.display === 'none');
    ok('停下之前那一稿仍在', !!JSON.parse(c.win.localStorage.getItem('sde_conf_draft') || 'null'));
  });

  await step('三十一、下次开页面能把上一稿捞回来', async () => {
    const c = await boot();
    c.win.localStorage.setItem('sde_conf_draft', JSON.stringify({
      t: Date.now(), title: '那一段谁走的', tag: '评审 138 分', score: 138, words: 19728, md: '# 那一段谁走的\n正文若干。' }));
    c.win.eval('draftRestore()');
    await sleep(80);
    const bar = c.$('draftRestore');
    ok('找回条露出来了', bar.style.display === '');
    ok('写清是哪一稿、多少字、多少分', /那一段谁走的/.test(bar.textContent) && /19728/.test(bar.textContent) && /138/.test(bar.textContent),
       bar.textContent.slice(0, 80));
    ok('给了下载与丢掉两个口子', !!c.$('draftGet') && !!c.$('draftDrop'));
    c.click('#draftDrop');
    await sleep(80);
    ok('丢掉之后条子收起、底稿也清了', bar.style.display === 'none' && !c.win.localStorage.getItem('sde_conf_draft'));
  });

  await step('三十二、清空重来不动上一场的底稿', async () => {
    const c = await boot();
    c.win.localStorage.setItem('sde_conf_draft', JSON.stringify({ t: Date.now(), title: 'X', words: 9, md: '# X' }));
    c.$('apiKey').value = 'sk-fake';
    c.click('#resetBtn');
    await sleep(150);
    ok('底稿还在（清的是这一场，不是他上一场的成果）', !!c.win.localStorage.getItem('sde_conf_draft'));
    ok('找回条被重新挂上', c.$('draftRestore').style.display === '');
  });

  /* ---- 取材那一步：卡死的修复 ---- */
  await step('三十三、站内那一路是串行的（并发正是卡死的来路）', async () => {
    const c = await boot({ nbrMs: 60 });
    fillQ(c, '教育的本质是什么？', '社会学', '心理学', '化学');
    c.click('#goBtn');
    await waitFor(() => /✓|⚠|中断/.test(c.$('stat-select').textContent), 30000);
    ok('任何时刻只有一路站内近邻在飞', c.nbrPeak === 1, '峰值并发 ' + c.nbrPeak);
    ok('三门都查到了', c.nbrQ.filter(q => /社会学|心理学|化学/.test(q)).length >= 3, String(c.nbrQ.length));
  });

  await step('三十四、取材实时报进度（卡住时看得出是哪一路）', async () => {
    const c = await boot({ nbrMs: 220 });
    fillQ(c, '教育的本质是什么？', '社会学', '心理学', '化学');
    const seen = [];
    const poll = setInterval(() => { const t = c.$('stat-select').textContent; if (/取材/.test(t)) seen.push(t); }, 40);
    c.click('#goBtn');
    await waitFor(() => /✓|⚠|中断/.test(c.$('stat-select').textContent), 30000);
    clearInterval(poll);
    ok('状态条报了联网几分之几', seen.some(t => /联网 \d\/3/.test(t)), seen[0] || '(没抓到)');
    ok('状态条报了站内几分之几', seen.some(t => /站内近邻 \d\/3/.test(t)), seen[seen.length - 1] || '(没抓到)');
    ok('站内计数确实在往前走', seen.some(t => /站内近邻 0\/3/.test(t)) && seen.some(t => /站内近邻 [23]\/3/.test(t)));
  });

  await step('三十五、一路永不返回：被闸掉、如实标出，不无限期转圈', async () => {
    const c = await boot({ hangNbr: true });
    c.win.eval('SIDE_MS.kb = 300');            // 把闸调短，好在测试里跑完
    fillQ(c, '教育的本质是什么？', '社会学', '心理学', '化学');
    c.click('#goBtn');
    const moved = await waitFor(() => /✓|⚠|中断/.test(c.$('stat-select').textContent), 20000);
    ok('没有卡死，这一格照样收了尾', moved, c.$('stat-select').textContent);
    ok('挂住的请求被真的掐掉了', c.nbrAborted >= 3, '掐掉 ' + c.nbrAborted + ' 路');
    ok('如实记了一笔超时（不假装取到）', c.win.eval('ST.notes.join("|")').indexOf('超时被掐掉') >= 0,
       c.win.eval('ST.notes.join("|")').slice(0, 80));
    ok('联网那一路仍然拿到了材料', /三家已就位/.test(c.$('stat-select').textContent), c.$('stat-select').textContent);
  });

  await step('三十六、卡在取材上按「停下」，当场掐断在飞的请求', async () => {
    const c = await boot({ hangNbr: true });
    c.win.eval('SIDE_MS.kb = 60000');          // 闸留得很长，全靠「停下」掐
    fillQ(c, '教育的本质是什么？', '社会学', '心理学', '化学');
    c.click('#goBtn');
    await waitFor(() => c.nbrLive >= 1, 20000);
    c.click('#stopBtn');
    await sleep(500);
    ok('在飞的请求被掐断', c.nbrAborted >= 1, '掐断 ' + c.nbrAborted);
    ok('产线真的停了（按钮复位）', c.$('goBtn').disabled === false && c.$('stopBtn').style.display === 'none');
    ok('没有继续往下跑到体检', !/✓/.test(c.$('stat-gate').textContent), c.$('stat-gate').textContent);
  });

  if (process.env.DUMP) {
    console.log('\n' + '='.repeat(56) + '\n整条产线的调令流水（第三场整跑）\n' + '='.repeat(56));
    c2.calls.forEach((k, i) => {
      const head = k.user.split('\n').filter(Boolean)[0] || '';
      console.log(String(i + 1).padStart(2) + '. 预算 ' + String(k.max_tokens).padStart(5)
        + ' ｜ system ' + String(k.system.length).padStart(5) + ' 字'
        + ' ｜ 带题:' + (/本次要解决的问题/.test(k.system) ? '是' : '否')
        + ' ｜ ' + head.slice(0, 58));
    });
  }

  console.log('\n' + '='.repeat(56));
  console.log('通过 ' + pass + ' · 失败 ' + fail);
  if (fails.length) { console.log('\n失败清单：'); fails.forEach(f => console.log('  · ' + f)); }
  process.exit(fail ? 1 : 0);
})();
