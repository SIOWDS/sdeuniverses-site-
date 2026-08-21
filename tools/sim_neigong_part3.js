/* sim_neigong_part3.js —— 内功第三部分「二阶碰撞生典范」装载与心得纪律
   为什么要这个 sim：第三部分是并进 NEIGONG 本体的，所有装内功的调用都会带上它。
   一旦 loadNeigong 的降级分支写错，全站会静默退回只有第一部分——读起来一切正常，没有任何报错。 */
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
let P = 0, F = 0;
function ok(n, c) { if (c) { P++; console.log('  PASS ' + n); } else { F++; console.log('  FAIL ' + n); } }
function sec(t) { console.log('\n[' + t + ']'); }

const src = fs.readFileSync(path.join(ROOT, 'src/worker.js'), 'utf8');
const P3PATH = path.join(ROOT, 'public/taste/assets/sde-collide-paradigm.txt');

sec('一 · 第三部分文件本身');
ok('文件存在', fs.existsSync(P3PATH));
const p3 = fs.existsSync(P3PATH) ? fs.readFileSync(P3PATH, 'utf8') : '';
const han = (p3.match(/[\u4e00-\u9fff]/g) || []).length;
ok('汉字数 >4000（当前 ' + han + '）', han > 4000);
ok('长度过得了 loadNeigong 的 >3000 字节闸', Buffer.byteLength(p3) > 3000);
[
  ['一阶二阶分界', '若能从其中任一个源直接推导出来'],
  ['十四道工序骨架', '共有前提'],
  ['选源四闸含门类三分', '门类三分'],
  ['候选近邻闸三条纪律', '检索未命中 ≠ 未被占位'],
  ['先找同向占位者', '先找同向占位者'],
  ['三重否定命题形状', '也不是 Y₃'],
  ['靶格三签名', '失效不产生信号'],
  ['零情态词判据', '零情态词'],
  ['反向约束至少两处', '至少两个学科必须反过来'],
  ['划界三栏', '同批·同栏'],
  ['成文硬门', '缺则成文作废'],
  ['去母体化拦截词含创新智商', '创新智商／五维／综合分'],
  ['评审铁律一', '不为自己参与的文本发认证分'],
  ['真实读数锚点 139–142', '139–142'],
  ['至今没破 150 的原因', '做的是操作化，不是发生'],
].forEach(function (x) { ok('含「' + x[0] + '」', p3.indexOf(x[1]) >= 0); });

sec('二 · loadNeigong 真跑（抠出函数 + 打桩 ASSETS）');
/* ⚠ 2026-08-21：原来的正则把**整串签名** `loadNeigong(env, url)` 与紧邻的 `let NEIGONG = null;`
   一起钉死。领域档案给它加了第三个参数 path、又在中间插了 NEIGONG_BY_PATH 那个分档缓存，
   正则当场配不上 ⇒ m 为 null ⇒ **整份 sim 崩掉**（不是红，是崩：看起来像环境问题）。
   💡 本仓两条心法在这里同时应验：**钉字面的旧断言**（第六次）＋**会崩的护栏比会红的坏得多**。
   ⇒ 改成按用意抠：从 `let NEIGONG = null;` 起，到 loadNeigong 函数体结束为止，
     只认函数名，不认形参表；中间夹着什么声明都照收。 */
const _a = src.indexOf('let NEIGONG = null;');
const _f = src.indexOf('async function loadNeigong(', _a);
const _e = src.indexOf('\n}', _f);
const m = (_a >= 0 && _f > _a && _e > _f) ? [src.slice(_a, _e + 2)] : null;
ok('抠得到 loadNeigong', !!m);
ok('抠出来的括号是平的', !!m && m[0].split('{').length === m[0].split('}').length);
function mkLoader() {
  // 每次重新 eval，拿到干净的模块级缓存
  return eval('(function(){' + m[0].replace(/^let /gm, 'var ').replace(/^const NEIGONG_BY_PATH/gm, 'var NEIGONG_BY_PATH') + '\nreturn loadNeigong;})()');
}
function mkEnv(map) {
  return { ASSETS: { fetch: function (req) {
    const u = new URL(req.url).pathname;
    if (map[u] === undefined) return Promise.resolve({ text: function () { return Promise.resolve(''); } });
    return Promise.resolve({ text: function () { return Promise.resolve(map[u]); } });
  } } };
}
const BASE = 'https://x/', A = 'A'.repeat(6000), C = 'C'.repeat(4000);
(async function () {
  let f = mkLoader();
  let r = await f(mkEnv({ '/taste/assets/sde-neigong.txt': A, '/taste/assets/sde-collide-paradigm.txt': C }), BASE);
  ok('两份都在：返回 = 第一部分 + 第三部分', r === A + '\n\n' + C);
  ok('第三部分确实在里面', r.indexOf(C) > 0);

  f = mkLoader();
  r = await f(mkEnv({ '/taste/assets/sde-neigong.txt': A }), BASE);
  ok('第三部分读不到：退化为只有第一部分，不阻断开工', r === A);

  /* ── 一档一份缓存（领域档案带自己的内功时）──
     ⭐ 这是最容易静默串台的一处：NEIGONG 原来是**一个**模块级变量，
        分档之后若还共用它，谁先冷启动谁那一份就被所有人复用，
        表现是「ChatJohn 有时讲 SDE 黑话、有时不讲」——随冷启动飘，最难查。 */
  const LITE = 'L'.repeat(7000);
  f = mkLoader();
  const envBoth = mkEnv({ '/taste/assets/sde-neigong.txt': A,
                          '/taste/assets/sde-neigong-lite.txt': LITE,
                          '/taste/assets/sde-collide-paradigm.txt': C });
  const rFull = await f(envBoth, BASE);
  const rLite = await f(envBoth, BASE, '/taste/assets/sde-neigong-lite.txt');
  ok('同一个 isolate 里两档互不串台', rFull.indexOf(A) === 0 && rLite.indexOf(LITE) === 0);
  ok('轻功档那一份不含满血那一份', rLite.indexOf(A) < 0);
  ok('先取轻功档也不会污染满血那一档',
    (await f(envBoth, BASE)).indexOf(A) === 0);
  ok('两档都带上第三部分（碰撞法）', rFull.indexOf(C) > 0 && rLite.indexOf(C) > 0);
  f = mkLoader();
  const rBad = await f(envBoth, BASE, '/etc/passwd');
  ok('路径不在白名单里就退回默认那一份（不许拿任意路径去取文件）', rBad.indexOf(A) === 0);
  /* ⚠ 这条第一版用的是**全新 loader**：默认那一份根本没装过，返回空串是必然的，
     于是「读不到就冒充默认那一份」这个变异照样绿。
     💡 验「A 会不会被 B 冒充」，必须先让 B 真的在场——空着的缓存证明不了任何事。 */
  f = mkLoader();
  await f(mkEnv({ '/taste/assets/sde-neigong.txt': A }), BASE);          // 先把默认那一份装进缓存
  const rMiss = await f(mkEnv({ '/taste/assets/sde-neigong.txt': A }), BASE, '/taste/assets/sde-neigong-lite.txt');
  ok('这一档读不到就回空串，不拿默认那份冒充（由调用方出声）', rMiss === '', 'got ' + rMiss.slice(0, 12));

  f = mkLoader();
  r = await f(mkEnv({ '/taste/assets/sde-neigong.txt': 'x', '/taste/assets/sde-collide-paradigm.txt': C }), BASE);
  ok('第一部分过短（<5000）：整体返回空，不拿第三部分冒充内功', r === '');

  f = mkLoader();
  r = await f(mkEnv({ '/taste/assets/sde-neigong.txt': A, '/taste/assets/sde-collide-paradigm.txt': 'tiny' }), BASE);
  ok('第三部分过短（<3000）：不拼进去', r === A);

  f = mkLoader();
  const env1 = mkEnv({ '/taste/assets/sde-neigong.txt': A, '/taste/assets/sde-collide-paradigm.txt': C });
  let n = 0; const raw = env1.ASSETS.fetch;
  env1.ASSETS.fetch = function (q) { n++; return raw(q); };
  await f(env1, BASE); const first = n; await f(env1, BASE);
  ok('模块级缓存生效：第二次零往返（' + first + ' → ' + n + '）', n === first);

  f = mkLoader();
  r = await f({ ASSETS: { fetch: function () { throw new Error('boom'); } } }, BASE);
  ok('取件抛异常：返回空字符串而不是崩掉', r === '');

  sec('三 · 心得纪律：写心得时必须内化二阶碰撞');
  const rp = src.match(/const REFLECT_PROMPT = "([\s\S]*?)";\n/);
  ok('抠得到 REFLECT_PROMPT', !!rp);
  const R = rp ? rp[1] : '';
  [['三份互相冲突的材料', '互相冲突的材料'],
   ['共有前提这一步', '三家共同假定了什么'],
   ['推翻材料须来自三家之一', '必须来自三家之一自己'],
   ['三重否定的命题形状', '也不是丙说的那样'],
   ['第二根轴与四格', '第二根轴'],
   ['靶格三签名', '不产生任何信号'],
   ['不可还原自检', '单独推出来'],
   ['反向约束自检', '只会附和你的例子不算数'],
   ['仍守平实汉语纪律', '不要术语标签']
  ].forEach(function (x) { ok('心得提示含「' + x[0] + '」', R.indexOf(x[1]) >= 0); });
  ok('原有的近邻/分离线/证伪三件没被挤掉', R.indexOf('分界线') >= 0 && R.indexOf('是错的') >= 0);

  sec('四 · SDE 对谈开工仪式：第十节');
  const dp = src.match(/const DIALOGUE_REFLECT_PROMPT = "([\s\S]*?)";\n/);
  ok('抠得到 DIALOGUE_REFLECT_PROMPT', !!dp);
  const D = dp ? dp[1] : '';
  ok('节数已从八改十', D.indexOf('分十节写') >= 0 && D.indexOf('分八节写') < 0);
  ok('第十节存在且是二阶碰撞', /十、二阶碰撞生典范/.test(D));
  ok('第九节（创新智商）没被顶掉', D.indexOf('九、创新智商这把尺') >= 0);
  ok('十四道工序骨架在场', D.indexOf('候选近邻闸') >= 0 && D.indexOf('共有前提') >= 0);
  ok('字数目标已上调', D.indexOf('6500') >= 0 && D.indexOf('5500 字看齐') < 0);

  sec('五 · 唯一的例外没有被破坏');
  ok('mode=iq 仍然刻意不装内功（盲评者裸机）', /盲评刻意不装内功|评分者一旦被 SDE 内功装载/.test(src));
  ok('第三部分自己也要求评审不装心法', p3.indexOf('评审这一趟不装心法') >= 0);

  console.log('\n===== ' + P + ' PASS / ' + F + ' FAIL =====');
  process.exit(F ? 1 : 0);
})();
