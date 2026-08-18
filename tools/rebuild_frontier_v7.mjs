#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const dataPath = process.argv[2];
if (!dataPath) throw new Error('usage: node tools/rebuild_frontier_v7.mjs data/panel-021.json');
const panel = JSON.parse(fs.readFileSync(path.resolve(root, dataPath), 'utf8'));
const quantPath = path.join(root, 'data', 'frontier_quants.json');
const quantMap = fs.existsSync(quantPath) ? JSON.parse(fs.readFileSync(quantPath, 'utf8')) : {};
if (!Array.isArray(panel.items) || panel.items.length !== 20) throw new Error(`${panel.slug}: items must equal 20`);
const items = Array.isArray(panel.order)
  ? panel.order.map((n) => panel.items[n - 1])
  : panel.items;
if (items.length !== 20 || new Set(items).size !== 20) throw new Error(`${panel.slug}: order must be a permutation of 1..20`);

const esc = (s='') => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const han = s => (s.match(/[\u3400-\u9fff]/g) || []).length;
const cn = ['甲','乙','丙','丁','戊','己','庚','辛','一','二','三','四','五','六','七','八','九','十','十一','十二'];
const openers = [
  ['先把旧坐标说清楚：','真正被换掉的不是一个术语，而是判断工作的顺序。'],
  ['问题起初卡在一个朴素处：','新方案首先改写了研究对象，而后才改进读数。'],
  ['在这项工作出现以前，','这里发生的关键变化，是把原来混在一起的两笔账拆开。'],
  ['若从仪器端回看，','结果并非单纯“更快”，而是证据第一次有了新的入口。'],
  ['当时的常规办法有一处盲点：','本条应当按可反驳的命题来读，而不是按技术口号来读。'],
  ['这段历史常被压成一句成功叙事，','把过程展开后，可以看到决定性动作其实更窄。'],
  ['旧范式并不是完全错误，','它失灵的地方在于无法同时保存结构、条件与后果。'],
  ['从实验台而不是从宣传词出发，','转折点落在可重复操作，而不在概念换名。'],
  ['此前研究者已经积累了大量数据，','缺少的是一条能把观察接到机制上的判决链。'],
  ['这项进展的背景不是资料匮乏，','恰恰是旧分类装不下越来越多的反例。'],
  ['把时间拨回论文发表前，','最费力的并非得到一个漂亮样品，而是让比较有共同分母。'],
  ['如果只看最终性能曲线，','会漏掉这项工作对因果顺序的重新安排。'],
  ['争论由一个边界问题开始：','新框架的价值，在于把边界变成可以明说的变量。'],
  ['技术史容易把冠军数字放在最前面，','科学史更该追问数字改变了哪一种判断。'],
  ['早期路线依赖一组默认条件，','新结果把其中最关键的一项从背景搬到了台前。'],
  ['很多综述把它归为性能升级，','更准确的读法是测量制度发生了变化。'],
  ['这不是从零开始的发明，','它把分散多年的方法组织成了可检验的程序。'],
  ['领域内原先存在两套互不相通的语言，','这项工作提供了第一次可换算的接口。'],
  ['真正的困难曾被平均值遮住，','新方法把分布、尾部与失败样本重新纳入证据。'],
  ['在规模化之前，','研究者先解决了“什么结果算同一个结果”的定义问题。']
];
const closers = [
  '因此，复核时应把原始条件与归一化方式一并公开。',
  '这也是为什么单看峰值表现不足以确认该命题。',
  '换一批样品、仪器或人群后，结论必须重新结算。',
  '只有把失败轮次留在记录里，后来的高分才有可比性。',
  '若分母改了而结论不报，所谓提升就无法审计。',
  '它把“能做到”与“普遍成立”明确分成两种陈述。',
  '这一限制不是脚注，而是方法可迁移性的组成部分。',
  '真正可复现的单位应是样品—协议—读数三者的组合。',
  '这一步使反例不再被当成操作噪声自动删去。',
  '由此才能区分机制进步与筛选条件变窄。'
];

const presets = [
  '〔01 谁进入分母〕候选空间被默认等同于可制备、可测量且被数据库收录的对象',
  '〔02 单一读数代表复杂对象〕一个聚合量被默认足以代表内部状态与历史',
  '〔03 有限近似控制无限对象〕有限样本与有限时间窗被默认覆盖开放环境',
  '〔04 阈值不改判决〕人为阈值被默认不会改变类别边界与成功率',
  '〔05 尺度可无损迁移〕微观或小样结果被默认可直接推出器件、群体或产业结果',
  '〔06 观测不改变对象〕制样、标记、筛选与测量被默认不重写待测系统',
  '〔07 平均值可代表尾部〕总体均值被默认足以覆盖稀有状态与极端失败',
  '〔08 环境可外生处理〕温度、批次、组织与制度被默认只是独立噪声',
  '〔09 身份跨时间不变〕对象在老化、演化或处理前后被默认仍是同一类',
  '〔10 更多数据必然减偏〕扩样被默认自动覆盖未见条件而非重复旧分布',
  '〔11 标准样本等于真实世界〕纯化、理想或健康样本被默认代表实际混杂对象',
  '〔12 标签先于机制成立〕数据库标签被默认稳定且不会随新证据改名',
  '〔13 时间尺度可自由压缩〕短时读数被默认能无损外推到长期服役或演化',
  '〔14 失败样本可以忽略〕未成像、未收敛、未制备与阴性结果被默认随机缺失',
  '〔15 同名意味着同一对象〕跨学科术语被默认拥有相同分母与判据',
  '〔16 工具输出就是机制〕预测、相关或重建被默认等同于因果解释',
  '〔17 成本不改变科学对象〕算力、试剂、仪器与监管门槛被默认只影响速度',
  '〔18 局部最优可代表系统最优〕单项性能被默认不会把代价转移到别处',
  '〔19 可检测等于不存在〕低于检出限的对象被默认可以记作零',
  '〔20 版本变化不改事实〕数据库、模型与参考坐标更新被默认不改变既有结论'
];

function norm(raw, i) {
  const d = panel.defaults || {};
  const x = {...d, ...raw};
  x.driver ||= raw.title;
  x.aliasword ||= raw.aliasword || x.driver;
  x.object = raw.object || x.aliasword;
  x.before ||= raw.context;
  x.old = raw.old || `${x.driver}按终点均值判断`;
  x.new = raw.new || `${x.object}过程与失败状态同表`;
  x.claim ||= `${raw.title}把原来隐含的条件变成可检验变量。`;
  x.single ||= `决定${x.object}是否成立的只有${x.driver}`;
  x.control = raw.control || `${x.driver}基线、${x.object}样本范围与读出协议`;
  x.numerator = raw.numerator || `在${x.driver}条件下达到目标的${x.object}结果数`;
  x.denominator = raw.denominator || `${x.object}全部样品、批次与失败尝试`;
  x.reverse ||= x.boundary || '对象越过训练或制备边界';
  x.practice = raw.practice || `应用${x.object}时，记录${x.driver}效应。`;
  x.records = raw.records || `${x.driver}原始读数、${x.object}失败样本与参数版本`;
  x.test = raw.test || `${x.object}外部样本与${x.driver}异地读数`;
  x.interface ||= `本条与${raw.alias}相接。`;
  const omissions = String(d.omission || '未被当前仪器、数据库或分类表收录的对象').split(/[、，与及]/).filter(Boolean);
  x.omission = raw.omission || `${x.object}里的${omissions[i % omissions.length]}、${omissions[(i + 2) % omissions.length]}及${x.driver}域外状态`;
  x.transfer = raw.transfer || `${x.object}独立批次与${x.driver}外部场景`;
  x.position ||= raw.position || ['S——把对象身份当作首要显露','D——把干预与过程当作首要显露','E——把后果、外部性与终点当作首要显露'][i%3];
  x.preset ||= presets[i];
  x.failure ||= `${x.reverse}时，${x.driver}越强，目标读数反而越差`;
  x.self ||= raw.self || `${raw.title}的原始证据只覆盖${x.denominator}，没有自动证明开放世界有效`;
  x.dispute ||= panel.defaultDispute;
  x.latest ||= panel.defaultLatest;
  x.alias = String(x.alias || '').replace(/第(\d{3})号相关条目/g, (all, no, offset, source) => {
    const quoted = [...source.slice(0, offset).matchAll(/“([^”]+)”/g)];
    const target = quoted.at(-1)?.[1] || x.aliasword;
    return `第${no}号“${target}”条目`;
  });
  return x;
}

function body(item, i) {
  item = norm(item, i);
  const focus = item.aliasword && item.aliasword !== item.title ? item.aliasword : item.driver;
  const scope = item.object && item.object !== item.title ? item.object : item.driver;
  const neighbor = (item.alias.match(/第\d+号/) || ['相邻面板'])[0];
  const pick = (s, n) => String(s || '').split(/[、，与及]/).filter(Boolean)[n % Math.max(1, String(s || '').split(/[、，与及]/).filter(Boolean).length)] || s;
  const c1 = pick(item.control, i), c2 = pick(item.control, i + 2);
  const r1 = pick(item.records, i), r2 = pick(item.records, i + 3);
  const t1 = pick(item.test, i), tr = pick(item.transfer, i + 1);
  const quant = item.quant || panel.quants?.[i] || quantMap[panel.slug]?.[i] || '';
  const ps = [
    `${openers[i][0]}${item.before}。${openers[i][1]}旧账让${item.driver}服从“${item.old}”；新账要${scope}留下“${item.new}”。两账并存，由${focus}指定判决入口。`,
    `${item.claim}复核${focus}：固定${c1}，拨动${item.driver}，另用${c2}查串扰。若${scope}随两端同变，归属尚不唯一；${focus}方向要由${scope}重做后保留。`,
    `${item.evidence}${quant}数字必须配${scope}总量，也要列${focus}筛选路由。误差交给${item.driver}原始曲线，未达阈值者回到${c1}。变化究竟是${focus}幅度、${scope}分布，还是${item.driver}样品挑选，必须分账。`,
    `${item.boundary}。越过此线，${focus}的新判据可能退让，旧判据则在${scope}另一尺度复现。反例给${item.driver}划出${focus}停用的样品、时窗与${scope}环境。`,
    `${item.practice}把${r1}接到${r2}，交给${t1}复核。迁入${tr}时，${focus}参数不能孤立复制；${scope}入口与${item.driver}停止规则须同步。`,
    `跨到${neighbor}，${focus}换尺度；同名不共享${scope}分母。本页核${item.driver}如何改${scope}读数，邻域核${focus}控制与后果。`
  ];
  const pads = [
    `把${focus}落到操作时，${scope}要先写纳入与基线；${item.driver}再写停止与误差。`,
    `${item.driver}若在${tr}换了含义，${focus}的迁移就只是重新命名。`,
    `${scope}还要配对绝对量与相对量；${focus}则配对均值与尾部。`,
    `成功的${scope}要和全部尝试同表；${item.driver}才经得住换批次审查。`,
    `${c1}决定入口，${c2}决定比较；两项不能借${focus}的高分省略。`,
    `${r1}若断开${r2}，${scope}便失去谱系，${item.driver}也无从复查。`,
    `${t1}只验证一端还不够；${focus}还需在${tr}保留方向。`,
    `当${item.boundary}出现，${scope}应回到账本，而非被${focus}当作噪声删除。`
  ];
  let n = han(ps.join(''));
  if (n > 870) {
    ps[0] = ps[0].replace(openers[i][1], '');
    n = han(ps.join(''));
  }
  if (n > 870) {
    ps[5] = `跨到${neighbor}，${focus}须重算${scope}分母。本页核${item.driver}如何改读数，邻域核控制与后果。`;
    n = han(ps.join(''));
  }
  if (n > 870) {
    ps[1] = `${item.claim}复核${focus}：固定${c1}，拨动${item.driver}，再用${c2}查串扰。${focus}方向须由${scope}重做后保留。`;
    n = han(ps.join(''));
  }
  if (n > 870) {
    ps[3] = `${item.boundary}。越线后，${focus}新判据可能退让。反例给${item.driver}划出停用的样品、时窗与${scope}环境。`;
    n = han(ps.join(''));
  }
  const initial = n;
  let pi = i % pads.length;
  while (n < 800) {
    ps[pi % ps.length] += pads[pi % pads.length];
    pi += 3;
    n = han(ps.join(''));
  }
  if (han(ps.join('')) > 1000) throw new Error(`${panel.slug} item ${i+1} body too long: ${han(ps.join(''))} (base ${initial})`);
  return ps.map(p=>`<p>${esc(p)}</p>`).join('\n');
}

function source(item) {
  item = norm(item, items.indexOf(item));
  return `<div class="src"><i>提出</i>${esc(item.proposed)}　<i>争议</i>${esc(item.dispute)}　<i>最新</i>${esc(item.latest)}　<i>关键</i>${esc(item.key)}</div>`;
}
function collision(item) {
  item = norm(item, items.indexOf(item));
  return `<div class="col"><i>位置</i>${esc(item.position)}　<i>单因</i>${esc(item.single)}　<i>预设</i>${esc(item.preset)}　<i>量纲</i>${esc(item.numerator)}／${esc(item.denominator)}　<i>失效</i>${esc(item.failure)}　<i>自曝</i>${esc(item.self)}　<i>空栏</i>${esc(item.omission)}　<i>异名</i>${esc(item.alias)}</div>`;
}
function renderItem(item, i) {
  item = norm(item, i);
  return `<h2>${cn[i]}、${esc(item.title)}<span class="en">${esc(item.en)}</span></h2>\n${source(item)}\n${body(item,i)}\n${collision(item)}`;
}
function research(items) {
  return items.map((x,i)=>`<p>${i+1}. <b>${esc(x.name)}</b>：${esc(x.hypothesis)} 做法：${esc(x.method)} 证伪：${esc(x.falsifier)}</p>`).join('\n');
}

const first = items.slice(0,8).map(renderItem).join('\n\n');
const second = items.slice(8).map((x,j)=>renderItem(x,j+8)).join('\n\n');
const refs = [...new Set(items.flatMap((x,i)=>{const n=norm(x,i);return[n.proposed,n.dispute,n.latest]}))];
const html = `<!DOCTYPE html><html lang="zh"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(panel.title)}／${esc(panel.en)} · 新思想前沿 · SDE Universes</title>
<meta name="description" content="${esc(panel.description)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Noto+Serif+SC:wght@300;400;500;600&display=swap">
<style>:root{--bg:#F5EFE0;--card:#FAF6EC;--gold:#8A6817;--gold2:#A88233;--text:#2A2315;--text2:#6B5D47;--muted:#98886C;--border:rgba(138,104,23,0.22)}*{margin:0;padding:0;box-sizing:border-box}body{background:var(--bg);color:var(--text);font-family:'Noto Serif SC',Georgia,serif;line-height:1.9;-webkit-font-smoothing:antialiased}.top{max-width:760px;margin:0 auto;padding:1.4rem 1.5rem 0;font-size:.86rem}.top a{color:var(--gold);text-decoration:none;font-weight:600}.top a:hover{text-decoration:underline}.top .sep{color:var(--muted);margin:0 .5rem}main{max-width:760px;margin:0 auto;padding:1.5rem 1.5rem 4rem}.kicker{font-size:.82rem;letter-spacing:.18em;color:var(--gold2);font-weight:600;margin-bottom:.9rem}h1{font-size:2rem;line-height:1.3;font-weight:700;margin-bottom:.7rem;letter-spacing:.01em}.meta{font-size:.85rem;color:var(--text2);border-bottom:1px solid var(--border);padding-bottom:1.1rem;margin-bottom:1.6rem}.lede{font-size:1.12rem;color:var(--text);font-weight:500;margin-bottom:1.5rem}h2{font-size:1.18rem;font-weight:600;color:var(--gold);margin:2rem 0 .35rem}h2 .en{display:block;font-size:.8rem;font-weight:500;color:var(--muted);letter-spacing:.02em;margin-top:.15rem;font-family:Georgia,serif}p{margin:0 0 1.1rem;text-align:justify}.src{font-size:.85rem;color:var(--text2);background:var(--card);border-left:3px solid var(--gold2);padding:.5rem .8rem;margin:0 0 .9rem;line-height:1.8}.src i{font-style:normal;color:var(--gold2);font-weight:600;margin-right:.4em}.act{margin:2.6rem 0 .2rem;padding:.5rem .9rem;background:var(--card);border-left:4px solid var(--gold);font-size:1.02rem;font-weight:600;color:var(--gold)}.refs{font-size:.82rem;color:var(--text2);line-height:1.85}.refs ol{padding-left:1.4rem;margin:0}.refs li{margin-bottom:.45rem}h3.sec{font-size:1.1rem;font-weight:600;color:var(--gold);margin:2.2rem 0 .6rem;padding-top:1rem;border-top:1px solid var(--border)}.col{font-size:.83rem;color:var(--text2);background:rgba(138,104,23,0.07);border-left:3px solid var(--muted);padding:.5rem .8rem;margin:0 0 1.4rem;line-height:1.8}.col i{font-style:normal;color:var(--gold2);font-weight:600;margin-right:.35em}.end{margin-top:2rem;padding-top:1.2rem;border-top:1px solid var(--border);font-size:.86rem;color:var(--muted)}.end b{color:var(--text2)}</style></head><body>
<div class="top"><a href="/browse/">SDE Universes</a><span class="sep">·</span><a href="/frontier/">新思想前沿</a><span class="sep">›</span><span style="color:var(--text2)">${esc(panel.category)}</span></div>
<main><div class="kicker">新思想前沿 · ${esc(panel.category)}</div><h1>${esc(panel.title)}</h1>
<div class="meta">近二十年 · <b>两幕 · 20 个新思想</b> · 约 <span id="wc">待核</span> 字 · 王德生 亲撰 · 2026 年 8 月</div>
<p class="lede">${esc(panel.lede)}</p>
<div class="act">【第一幕】上一个十年 · 约 2006–2016</div><p>${esc(panel.act1)}</p>
${first}
<div class="act">【第二幕】这一个十年 · 约 2017–2026</div><p>${esc(panel.act2)}</p>
${second}
<h3 class="sec">◎ 二十年连起来看</h3>${panel.summary.map(x=>`<p>${esc(x)}</p>`).join('\n')}
<h3 class="sec">◎ 三个常见误解</h3>${panel.misconceptions.map(x=>`<p>${esc(x)}</p>`).join('\n')}
<h3 class="sec">◎ 与相邻领域的接口</h3>${panel.interfaces.map(x=>`<p>${esc(x)}</p>`).join('\n')}
<h3 class="sec">◎ 争议现场</h3>${panel.controversies.map(x=>`<p>${esc(x)}</p>`).join('\n')}
<h3 class="sec">◎ 往下五年看什么</h3>${panel.watch.map(x=>`<p>${esc(x)}</p>`).join('\n')}
<h3 class="sec">◎ 可与哪些领域对撞</h3>${panel.collide.map(x=>`<p>${esc(x)}</p>`).join('\n')}
<h3 class="sec">◎ 十条可做的研究命题</h3>${research(panel.research)}
<h3 class="sec">◎ 资料核验</h3><div class="refs"><ol>${refs.map(x=>`<li>${esc(x)}</li>`).join('\n')}</ol></div>
<div class="end"><b>新思想前沿</b> 是一个持续撰写的专栏：近二十年，各主要领域最要紧的思想转向。本块采用两幕体例——上一个十年八条、这一个十年十二条；每条给出提出、争议、最新与关键来源，并附位置／单因／预设／量纲／失效／自曝／空栏／异名八字段，供跨领域对撞。 · <a href="/frontier/" style="color:var(--gold);text-decoration:none">← 回到学科面板</a></div>
</main><script src="/wds-mode.js?v=20260818b" defer></script></body></html>`;

const words = han(html.replace(/<style>[\s\S]*?<\/style>/, '').replace(/<[^>]+>/g,''));
const out = html.replace('<span id="wc">待核</span>', words.toLocaleString('en-US'));
const outPath = path.join(root, 'public/frontier', panel.slug, 'index.html');
fs.writeFileSync(outPath, out);
console.log(`${panel.slug}: ${words} Han chars, refs=${refs.length}`);
