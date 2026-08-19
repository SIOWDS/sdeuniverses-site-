/* sim_placeholder_gate.js —— 近邻库（占位者库）与候选闸的护栏
 *
 * 这一关最怕的不是报错，是**静默地变成橡皮图章**：库照查、闸照过、
 * 而实际上什么也没拦住。所以这里的断言分两类：
 *   ① 召回真的靠别名工作（拿 50 字压缩去钩，钩得出人名之外的东西）
 *   ② 三条纪律的措辞一个字都不许掉（它们是这道闸唯一的防退化装置）
 *
 * 跑法：node tools/sim_placeholder_gate.js
 */
const fs = require('fs');
const path = require('path');
const ROOT = path.dirname(__dirname);

let pass = 0, fail = 0; const bad = [];
function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; bad.push(name + (extra ? ('  ← ' + extra) : '')); console.log('  ✗ ' + name + (extra ? ('  ← ' + extra) : '')); }
}

// —— 装载模块（纯浏览器模块，给它一个 window 与 fetch 桩）——
const libJson = JSON.parse(fs.readFileSync(path.join(ROOT, 'public/kb/placeholders.json'), 'utf8'));
const win = {};
global.fetch = (u) => Promise.resolve({ ok: /placeholders\.json/.test(u), json: () => Promise.resolve(libJson) });
const src = fs.readFileSync(path.join(ROOT, 'public/taste/assets/sde-placeholder-lib.js'), 'utf8');
new Function('window', src)(win);
const G = win.SDEPlaceholder;

(async function () {
  console.log('\n— 一、库本身');
  ok('库能装上且非空', Array.isArray(libJson.items) && libJson.items.length >= 20, '卡数 ' + libJson.items.length);
  ok('每张卡都有命题、别名、出处、占住什么', libJson.items.every(x => x.p && x.a && x.a.length && x.o && x.h));
  ok('别名不少于每卡三条（钩子太少就钩不出来）',
    libJson.items.every(x => x.a.length >= 3), '最少的一张 ' + Math.min(...libJson.items.map(x => x.a.length)) + ' 条');
  ok('主键是命题空间不是人名（id 里不出现作者姓）',
    libJson.items.every(x => !/holling|bainbridge|scott|taleb/i.test(x.id)));

  console.log('\n— 二、召回靠别名工作（拿 50 字压缩去钩）');
  const q1 = '管理接管了系统的停止决定，压缩了它的变异范围，系统因此丧失韧性，而初期看起来很成功';
  const r1 = await G.match(q1, 5);
  ok('「压缩变异导致韧性丧失」钩得出命令—控制那张卡',
    r1.some(x => x.it.id === 'control-variance-pathology'), r1.map(x => x.it.id).join(','));

  const q2 = '接管控制之后技能从未生成，而监测读数照常正常，掩盖了能力空缺';
  const r2 = await G.match(q2, 5);
  ok('「接管控制导致技能不生成」钩得出自动化之讽那张卡',
    r2.some(x => x.it.id === 'automation-deskill-mask'), r2.map(x => x.it.id).join(','));

  const q3 = '留白一旦被制度性地授予，就必须产出可显现的证明，从而不再是留白';
  const r3 = await G.match(q3, 5);
  ok('「被授予的自主自我取消」钩得出自发性悖论那张卡',
    r3.some(x => x.it.id === 'be-spontaneous-paradox'), r3.map(x => x.it.id).join(','));

  const r4 = await G.match('把地方性的默会做法写成可公开援引的条文', 5);
  ok('「写下来即切割」钩得出可读性那张卡',
    r4.some(x => x.it.id === 'legibility-destroys-metis'), r4.map(x => x.it.id).join(','));

  ok('毫不相干的问题不硬凑（返回空或低分）', (await G.match('今天午饭吃什么', 5)).length === 0
    || (await G.match('今天午饭吃什么', 5))[0].s <= 6);
  ok('空问题返回空', (await G.match('', 5)).length === 0);

  console.log('\n— 三、三条纪律的措辞（掉一条这道闸就退化成橡皮图章）');
  const miss = G.block([]);
  ok('未命中时明写「不等于未被占位」', /不等于未被占位/.test(miss));
  ok('未命中时明写「不得据此放行」', /不得据此放行/.test(miss));
  ok('未命中时仍要求自己点名 ≥3 位', /至少三位/.test(miss));
  const hit = G.block(r1);
  ok('命中时写死 1:1 替换测试', /1:1 替换测试/.test(hit));
  ok('命中时写死通过条件是「带着分离线活下来」', /带着一条\*\*可裁决分离线\*\*活下来|带着一条可裁决分离线活下来/.test(hit));
  ok('命中时写死「侧重不同」不算分离线', /不是「侧重不同」/.test(hit));
  ok('命中时写死只引自己人视同未检索', /视同未检索/.test(hit));
  ok('块里带出外文原题与年份', /Holling & Meffe/.test(hit) && /1996/.test(hit));
  ok('块里带出「已知未占」（免得闸门一刀切死）', /已知未占/.test(hit));

  console.log('\n— 四、命名空间是分开的（不许把站内文章索引混进来）');
  ok('模块只读 /kb/placeholders.json', (src.match(/fetch\(/g) || []).length === 1 && /kb\/placeholders\.json/.test(src));
  ok('模块不碰 search 索引与 kb/retrieve', !/search\/|kb\/retrieve|neighbors\.json/.test(src));

  console.log('\n— 五、页面接线');
  const page = fs.readFileSync(path.join(ROOT, 'public/taste/paradigm-forge/index.html'), 'utf8');
  ok('页面引了占位者库模块', /sde-placeholder-lib\.js/.test(page));
  ok('工序表里有候选闸且在扩候选之后', /\{id:'expand'[\s\S]{0,200}\{id:'nbrgate'/.test(page));
  ok('候选闸在候选互撞之前', page.indexOf("{id:'nbrgate'") < page.indexOf("{id:'collide2'"));
  ok('闸门调令要求先找同向占位者', /先找同向占位者/.test(page));
  ok('闸门调令要求外圈学科与外文原题', /本候选所属学科之外/.test(page) && /外文原题/.test(page));
  ok('闸门三路取料齐（站内近邻 / 占位者库 / 联网）',
    /window\.__NBRC/.test(page) && /window\.__PH/.test(page) && /window\.__WEB/.test(page));
  ok('联网失败时如实标〔未联网〕、不假装搜过', /未联网/.test(page));
  ok('全灭时回扩候选而不是硬往下走', /全部淘汰[\s\S]{0,400}expand/.test(page));
  ok('存活却零分离线要报警', /一条分离线都没给/.test(page));
  ok('候选互撞只吃幸存候选', /已被淘汰的候选不许再进来/.test(page) && /O\.nbrgate/.test(page));
  ok('回炉表认得候选闸', /\['候选闸','nbrgate'\]/.test(page));

  console.log('\n========================================================');
  console.log('通过 ' + pass + ' ｜ 失败 ' + fail);
  if (bad.length) { console.log('\n失败清单：'); bad.forEach(x => console.log('  · ' + x)); }
  console.log('========================================================');
  process.exit(fail ? 1 : 0);
})();
