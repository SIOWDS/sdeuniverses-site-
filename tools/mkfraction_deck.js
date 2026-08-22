// tools/mkfraction_deck.js —— 生成《分数是怎么发生的》21 页课件
// 用法（仓库根目录）：node tools/mkfraction_deck.js
//   → 写出 分数的发生学课件.pptx；再 soffice --convert-to pdf 得同名 PDF，
//     两个文件放进 public/banyu/prep/fraction-slides/（改名 fraction-genesis-slides.*），
//     并用 pymupdf 抽全文写到 tools/banyu_text/fraction-slides.txt。
//
// ⚠ 两条踩过的坑：
//  1. card() 的正文框高度一度写成 h-(ty-y)-0.72，在带 tag 的卡片上会算出 0.2" 甚至负数，
//     溢出的行被**叠着画在同一位置**——文件校验全绿、页面照常生成，只有渲染出来才看得见。
//     现在撑到卡片底边减 0.18；改文案后务必重渲染逐页看。
//  2. 纪律：全篇零学派术语（不出现 S/D/E、显露、纠缠、回写、光滑化）。
//     改完用 markitdown 数一遍。
const pptx = require('pptxgenjs');
const P = new pptx();
P.layout = 'LAYOUT_WIDE';                 // 13.3 x 7.5
P.author = '王德生';
P.title = '分数是怎么发生的';

const INK = '2B2622', CLAY = 'B85042', SAND = 'F1EBE0',
      SAGE = '5F7F68', PAPER = 'FFFFFF', GREY = '7A7068', LINE = 'D9CFC2';
const H = 'Cambria', B = 'Calibri';
const W = 13.33, HH = 7.5;

// ── 视觉母题：一个被分开的饼 ──────────────────────────
function pie(s, x, y, d, cut, color) {
  s.addShape(P.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: color || CLAY } });
  const cx = x + d / 2, cy = y + d / 2, r = d / 2;
  for (let i = 0; i < cut; i++) {
    const a = (Math.PI * 2 * i) / cut - Math.PI / 2;
    s.addShape(P.ShapeType.line, {
      x: cx, y: cy, w: r * Math.cos(a), h: r * Math.sin(a),
      line: { color: PAPER, width: 2 },
      flipH: Math.cos(a) < 0, flipV: Math.sin(a) < 0,
    });
  }
}

function foot(s, n) {
  s.addText('分数是怎么发生的　·　巴渝培训', {
    x: 0.55, y: 6.92, w: 6, h: 0.3, fontFace: B, fontSize: 10, color: GREY, margin: 0,
  });
  s.addText(String(n), {
    x: 12.2, y: 6.92, w: 0.6, h: 0.3, fontFace: B, fontSize: 10,
    color: GREY, align: 'right', margin: 0,
  });
}

function light(kicker, title, n) {
  const s = P.addSlide();
  s.background = { color: PAPER };
  if (kicker) s.addText(kicker, {
    x: 0.55, y: 0.42, w: 9, h: 0.32, fontFace: B, fontSize: 12,
    color: CLAY, bold: true, charSpacing: 2, margin: 0,
  });
  if (title) s.addText(title, {
    x: 0.55, y: 0.78, w: 12.2, h: 0.85, fontFace: H, fontSize: 32,
    color: INK, bold: true, margin: 0,
  });
  foot(s, n);
  return s;
}

function section(no, title, sub, n) {
  const s = P.addSlide();
  s.background = { color: INK };
  pie(s, 11.15, 0.75, 1.5, 3, CLAY);
  s.addText(no, {
    x: 0.9, y: 2.25, w: 2, h: 1, fontFace: H, fontSize: 62, color: CLAY, bold: true, margin: 0,
  });
  s.addText(title, {
    x: 0.9, y: 3.25, w: 10, h: 0.95, fontFace: H, fontSize: 40, color: PAPER, bold: true, margin: 0,
  });
  s.addText(sub, {
    x: 0.92, y: 4.3, w: 9.6, h: 1.2, fontFace: B, fontSize: 16,
    color: 'C9BEB0', lineSpacing: 26, margin: 0,
  });
  foot(s, n);
  return s;
}

// 卡片：标题 + 正文
function card(s, x, y, w, h, tag, title, body, tint, bar) {
  s.addShape(P.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06, fill: { color: tint || SAND },
  });
  let ty = y + 0.24;
  if (tag) {
    s.addText(tag, {
      x: x + 0.32, y: ty, w: w - 0.6, h: 0.28, fontFace: B, fontSize: 11,
      color: bar || CLAY, bold: true, charSpacing: 1.5, margin: 0,
    });
    ty += 0.34;
  }
  s.addText(title, {
    x: x + 0.32, y: ty, w: w - 0.64, h: 0.5, fontFace: H, fontSize: 17,
    color: INK, bold: true, margin: 0,
  });
  // 正文框一律撑到卡片底边减一点内边距。此前写成 h-(ty-y)-0.72，
  // 在有 tag 的卡片上常算出 0.2" 左右甚至负数，多出来的行被叠着画在同一位置。
  s.addText(body, {
    x: x + 0.32, y: ty + 0.52, w: w - 0.64, h: (y + h) - (ty + 0.52) - 0.18,
    fontFace: B, fontSize: 13.5, color: '4A423B', lineSpacing: 21, margin: 0, valign: 'top',
  });
}

let n = 0;

/* ══ 1 封面 ══ */
{
  const s = P.addSlide();
  s.background = { color: INK };
  pie(s, 10.4, 1.55, 2.3, 4, CLAY);
  s.addText('SDE · 数学发生学课件', {
    x: 0.9, y: 1.5, w: 8, h: 0.35, fontFace: B, fontSize: 13,
    color: CLAY, bold: true, charSpacing: 3, margin: 0,
  });
  s.addText('分数是怎么发生的', {
    x: 0.9, y: 2.05, w: 9.2, h: 1.15, fontFace: H, fontSize: 52,
    color: PAPER, bold: true, margin: 0,
  });
  s.addText('三个饼，分给四个人', {
    x: 0.92, y: 3.3, w: 9, h: 0.5, fontFace: H, fontSize: 24, color: 'D8C7B4', margin: 0,
  });
  s.addText('一节课的完整做法：怎么开头、怎么走、怎么当堂验收，以及四个最常踩的坑', {
    x: 0.92, y: 3.95, w: 9.2, h: 0.6, fontFace: B, fontSize: 15,
    color: '9C9187', lineSpacing: 24, margin: 0,
  });
  s.addShape(P.ShapeType.line, {
    x: 0.92, y: 4.85, w: 2.2, h: 0, line: { color: CLAY, width: 2 },
  });
  s.addText('小学中段 · 分数第一课　|　主讲：＿＿＿　|　巴渝培训预习材料', {
    x: 0.92, y: 5.15, w: 9.5, h: 0.4, fontFace: B, fontSize: 13, color: '8A8078', margin: 0,
  });
  s.addNotes('这一课件配合三天培训的第二天上午使用，也可以单独拿去上一节课。全篇不用任何专门名词。');
  foot(s, ++n);
}

/* ══ 2 现象 ══ */
{
  const s = light('先看一件真事', '当堂全对，一周后塌了', ++n);
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 2.0, w: 5.5, h: 3.4, rectRadius: 0.06, fill: { color: INK },
  });
  s.addText('近一半', {
    x: 0.9, y: 2.45, w: 4.8, h: 1.1, fontFace: H, fontSize: 60, color: CLAY, bold: true, margin: 0,
  });
  s.addText('三年级学完分数一周后，被问「1/2 和 1/3 谁大」，\n答「1/3 更大」的孩子占比', {
    x: 0.92, y: 3.6, w: 4.9, h: 1.2, fontFace: B, fontSize: 14,
    color: 'C9BEB0', lineSpacing: 22, margin: 0,
  });
  card(s, 6.35, 2.0, 6.4, 1.6, '当堂',
    '练习几乎全对',
    '通分、约分、比大小，一步不错。');
  card(s, 6.35, 3.8, 6.4, 1.6, '一周后',
    '换个问法就塌',
    '只问一句「谁大」，一半人答错。', 'F7EFEC');
  s.addText('这不是粗心。他心里那本账，从头到尾没被改过一个字。', {
    x: 0.55, y: 5.75, w: 12.2, h: 0.5, fontFace: H, fontSize: 21, color: CLAY, bold: true, margin: 0,
  });
  s.addNotes('先举手投票：你们班大概多少人会答错？让老师自己先押一个数，再给这个数字。');
}

/* ══ 3 那本账 ══ */
{
  const s = light('为什么会这样', '他心里那本账，写的是「3 比 2 大」', ++n);
  s.addText('孩子不是没听。他是拿一本旧账去读这个新东西——'
    + '而这本账，从来没有因为分数被改过。', {
    x: 0.55, y: 1.85, w: 12.2, h: 0.6, fontFace: B, fontSize: 16,
    color: '4A423B', lineSpacing: 26, margin: 0,
  });
  const rows = [
    ['旧账上写着', '数越大，那个东西就越大。3 比 2 大，所以 3 在哪儿都该更大。'],
    ['他看到 1/3', '看见的是「3」。分母那个位置对他来说，只是又一个数字。'],
    ['所以他答 1/3 大', '在他的账本里，这个答案完全讲得通——错的不是逻辑，是那本账。'],
  ];
  let y = 2.7;
  rows.forEach((r, i) => {
    s.addShape(P.ShapeType.ellipse, {
      x: 0.6, y: y + 0.1, w: 0.42, h: 0.42, fill: { color: i === 2 ? CLAY : LINE },
    });
    s.addText(String(i + 1), {
      x: 0.6, y: y + 0.14, w: 0.42, h: 0.34, fontFace: B, fontSize: 13,
      color: i === 2 ? PAPER : INK, bold: true, align: 'center', margin: 0,
    });
    s.addText(r[0], {
      x: 1.25, y: y + 0.08, w: 2.9, h: 0.4, fontFace: H, fontSize: 17,
      color: INK, bold: true, margin: 0,
    });
    s.addText(r[1], {
      x: 4.25, y: y + 0.05, w: 8.5, h: 0.6, fontFace: B, fontSize: 14,
      color: '4A423B', lineSpacing: 22, margin: 0,
    });
    y += 0.95;
  });
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 5.7, w: 12.2, h: 0.85, rectRadius: 0.06, fill: { color: SAND },
  });
  s.addText('所以这一课要做的不是「讲清楚」，是让这本账当场被改掉一次。', {
    x: 0.9, y: 5.9, w: 11.5, h: 0.45, fontFace: H, fontSize: 19, color: CLAY, bold: true, margin: 0,
  });
}

/* ══ 4 老办法 ══ */
{
  const s = light('老办法在哪一步失手', '讲第二遍，为什么还是不行', ++n);
  card(s, 0.55, 1.9, 3.9, 3.7, '老办法',
    '从定义起步',
    '「分数就是几分之几」——先给定义，再教通分约分，再做练习。\n\n'
    + '这套顺序本身没错：它是给已经懂了的人整理用的。\n\n'
    + '毛病在于，孩子还没有一个位置可以把它挂上去。');
  card(s, 4.65, 1.9, 3.9, 3.7, '于是',
    '他把形式记住了',
    '他记住了写法，也记住了操作步骤，考试当然对。\n\n'
    + '但他从来没有遇到过一个「非要分数不可」的时刻。\n\n'
    + '没遇到过，旧账就没有理由被改。', 'F7EFEC');
  card(s, 8.75, 1.9, 4.0, 3.7, '再讲一遍',
    '还是不行',
    '很多老师的反应是：那就再讲一遍，再多练几道。\n\n'
    + '可第二遍讲的还是同一个定义，还是从终点递过去的。\n\n'
    + '账不会因为听了两遍就改。', 'F7EFEC');
  s.addText('补课之所以常常没用，不是讲得不够清楚，是这一步压根不缺讲解。', {
    x: 0.55, y: 5.85, w: 12.2, h: 0.5, fontFace: H, fontSize: 20, color: INK, bold: true, margin: 0,
  });
  s.addNotes('这里可以停一下，问老师：你上一次给一个孩子讲第三遍同一个概念，是什么时候？');
}

/* ══ 5 上了锁 ══ */
{
  const s = light('还有一种更难的', '有些孩子，已经上了锁', ++n);
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 1.9, w: 6.1, h: 2.6, rectRadius: 0.06, fill: { color: INK },
  });
  s.addText('「数学就是这么规定的，不用想。」', {
    x: 0.9, y: 2.35, w: 5.4, h: 0.9, fontFace: H, fontSize: 24, color: PAPER, bold: true, margin: 0,
  });
  s.addText('这句话一旦写进心里，它管的就不是分数这一课了——'
    + '它管的是「以后所有的数学都不用想」。', {
    x: 0.92, y: 3.3, w: 5.4, h: 0.9, fontFace: B, fontSize: 14,
    color: 'C9BEB0', lineSpacing: 22, margin: 0,
  });
  card(s, 6.85, 1.9, 5.9, 1.35, '', '锁着的时候，把当年那条路还给他也没用',
    '他会照做，但不会跟着想——因为他已经认定这件事不需要想。');
  card(s, 6.85, 3.4, 5.9, 1.35, '', '所以次序是硬的：先开锁，再讲课',
    '开锁只需要一句话，难的是老师要当着全班说出这句话。', 'F7EFEC');
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 4.85, w: 12.2, h: 1.55, rectRadius: 0.06, fill: { color: SAND },
  });
  s.addText('开锁的那一句：', {
    x: 0.9, y: 5.05, w: 3, h: 0.4, fontFace: B, fontSize: 13,
    color: CLAY, bold: true, charSpacing: 1.5, margin: 0,
  });
  s.addText('「这个写法，其实当年也可以不这么定。你们信不信？」', {
    x: 0.9, y: 5.42, w: 11.5, h: 0.5, fontFace: H, fontSize: 23, color: INK, bold: true, margin: 0,
  });
  s.addText('说完不解释，等他们反应。有人抬头，锁就松了一道缝。', {
    x: 0.92, y: 5.95, w: 11.5, h: 0.35, fontFace: B, fontSize: 13.5, color: GREY, margin: 0,
  });
}

/* ══ 6 段落一 ══ */
section('一', '这一课该从哪里起', '不从「分数是什么」起。从一个分不出来的东西起。', ++n);

/* ══ 7 起点 ══ */
{
  const s = light('换一个起点', '三个饼，分给四个人', ++n);
  pie(s, 0.75, 2.1, 1.3, 4, CLAY);
  pie(s, 2.25, 2.1, 1.3, 4, CLAY);
  pie(s, 3.75, 2.1, 1.3, 4, CLAY);
  s.addText('÷', {
    x: 5.25, y: 2.3, w: 0.7, h: 0.9, fontFace: H, fontSize: 40,
    color: GREY, align: 'center', margin: 0,
  });
  ['', '', '', ''].forEach((_, i) => {
    s.addShape(P.ShapeType.ellipse, {
      x: 6.15 + i * 0.85, y: 2.3, w: 0.62, h: 0.62, fill: { color: SAGE },
    });
  });
  s.addText('每人分到多少？', {
    x: 9.9, y: 2.32, w: 3, h: 0.6, fontFace: H, fontSize: 24, color: INK, bold: true, margin: 0,
  });
  s.addText('孩子手里只有整数。他答不出来——而且他知道自己答不出来。', {
    x: 0.55, y: 3.7, w: 12.2, h: 0.5, fontFace: B, fontSize: 16,
    color: '4A423B', margin: 0,
  });
  card(s, 0.55, 4.35, 3.9, 2.3, '为什么是 3 和 4', '不能整除',
    '4 个饼分 4 人，一人一个，用不上新东西。\n必须让整数在这里真的走不通。');
  card(s, 4.65, 4.35, 3.9, 2.3, '为什么是饼', '能真的分开',
    '手上能分、能看见、能拿走。\n换成纸条、绳子、蛋糕都行，不能换成投影。');
  card(s, 8.75, 4.35, 4.0, 2.3, '为什么不先说名字', '名字最后才给',
    '先分，分完再问「这一份该叫什么」。\n名字是他们命名的，不是你递的。', 'F7EFEC');
  s.addNotes('现场可以真的拿三张圆纸片来分。手上分过的，和看老师分的，差别很大。');
}

/* ══ 8 五步 ══ */
{
  const s = light('这一课的五步', '顺序不能换', ++n);
  const steps = [
    ['1', '开缺口', '抛出三个饼分四人。让他自己发现整数不够用。'],
    ['2', '给方向', '「看来我们需要一个比 1 小的东西。」——只给方向，不给答案。'],
    ['3', '亲手分', '真的动手分，分完给那一份命名，再把它写下来。'],
    ['4', '换个情境', '量绳、切蛋糕、分钱——同一个东西，让它再出现一次。'],
    ['5', '开新缺口', '「那 1/2 和 1/3，谁大？」——当堂就撞，别留到一周后。'],
  ];
  let x = 0.55;
  steps.forEach((st, i) => {
    const wgt = i === 4 ? CLAY : INK;
    s.addShape(P.ShapeType.roundRect, {
      x, y: 1.95, w: 2.32, h: 3.2, rectRadius: 0.06,
      fill: { color: i === 4 ? 'F7EFEC' : SAND },
    });
    s.addShape(P.ShapeType.ellipse, {
      x: x + 0.28, y: 2.2, w: 0.5, h: 0.5, fill: { color: wgt },
    });
    s.addText(st[0], {
      x: x + 0.28, y: 2.26, w: 0.5, h: 0.38, fontFace: B, fontSize: 14,
      color: PAPER, bold: true, align: 'center', margin: 0,
    });
    s.addText(st[1], {
      x: x + 0.28, y: 2.85, w: 1.9, h: 0.4, fontFace: H, fontSize: 18,
      color: INK, bold: true, margin: 0,
    });
    s.addText(st[2], {
      x: x + 0.28, y: 3.32, w: 1.85, h: 1.7, fontFace: B, fontSize: 12.5,
      color: '4A423B', lineSpacing: 19, margin: 0, valign: 'top',
    });
    if (i < 4) s.addText('›', {
      x: x + 2.35, y: 3.2, w: 0.3, h: 0.5, fontFace: H, fontSize: 22,
      color: GREY, align: 'center', margin: 0,
    });
    x += 2.5;
  });
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 5.5, w: 12.2, h: 0.95, rectRadius: 0.06, fill: { color: INK },
  });
  s.addText('最要紧的是第 1 步在第 2 步之前。反过来，就又变回老办法了。', {
    x: 0.9, y: 5.75, w: 11.5, h: 0.5, fontFace: H, fontSize: 20, color: PAPER, bold: true, margin: 0,
  });
}

/* ══ 9 段落二 ══ */
section('二', '四十分钟，逐段怎么走', '每一段写了分钟数、老师说什么、以及这一段禁止做的事。', ++n);

/* ══ 10 时间表 ══ */
{
  const s = light('全课一览', '四十分钟的分配', ++n);
  s.addTable([
    [{ text: '时间', options: { bold: true } }, { text: '这一段做什么', options: { bold: true } },
     { text: '老师这一段不许做的事', options: { bold: true } }],
    ['0–3 分', '开锁那一句（只对已经放弃的班用）', '不许解释这句话'],
    ['3–11 分', '三个饼分四人，让他卡住', '不许提示「可以切开」'],
    ['11–16 分', '给方向：需要一个比 1 小的东西', '不许写出 1/4，不许说「四分之一」'],
    ['16–31 分', '亲手分、命名、写下来', '不许替任何一组动手'],
    ['31–38 分', '换情境再来一次：量绳／分钱', '不许只做一个情境'],
    ['38–40 分', '开新缺口：1/2 和 1/3 谁大', '不许当堂给答案'],
  ], {
    x: 0.55, y: 1.9, w: 12.2, colW: [1.7, 5.6, 4.9],
    fontFace: B, fontSize: 13.5, color: '3A332E', border: { pt: 0.5, color: LINE },
    fill: { color: PAPER }, rowH: 0.52, valign: 'middle',
  });
  s.addText('末一栏是这份课件里最有用的一栏。这一课的难处从来不是「要做什么」，是「忍住不做什么」。', {
    x: 0.55, y: 5.85, w: 12.2, h: 0.5, fontFace: H, fontSize: 18, color: CLAY, bold: true, margin: 0,
  });
}

/* ══ 11 第一二步 ══ */
{
  const s = light('逐段拆解（上）', '第 1、2 步：让他卡住，然后只给方向', ++n);
  card(s, 0.55, 1.9, 6.0, 2.75, '第 1 步 · 8 分钟', '把缺口摆出来',
    '桌上三张圆纸片，四个孩子一组。一句话：「分掉，谁也不能多，谁也不能少。」\n\n'
    + '接下来什么都不做。有人会先切、有人会先分整块——都随他。');
  card(s, 6.75, 1.9, 6.0, 2.75, '这一段的成败', '他有没有真的卡住',
    '卡住的记号不是安静，是争起来：还剩一个，那一个怎么办。\n\n'
    + '⚠ 三十秒就有人说「切成四份」，是缺口太浅——换成五个饼分四人。', 'F7EFEC');
  card(s, 0.55, 4.85, 6.0, 1.8, '第 2 步 · 5 分钟', '只给方向，不给答案',
    '一句：「看来我们需要一个比 1 小的东西。」然后闭嘴。');
  card(s, 6.75, 4.85, 6.0, 1.8, '这一句为什么这么短', '再多一个字就成了答案',
    '「切成四份」是答案，「四分之一」是答案。'
    + '「一个比 1 小的东西」不是——它只指了个方向。', 'F7EFEC');
  s.addNotes('培训现场可以让两位老师演一遍第 2 步：一个演老师、一个演学生，看老师能不能只说这一句。');
}

/* ══ 12 第三四五步 ══ */
{
  const s = light('逐段拆解（下）', '第 3、4、5 步：亲手走、再来一次、再卡住', ++n);
  card(s, 0.55, 1.9, 4.0, 3.05, '第 3 步 · 15 分钟', '亲手分，然后命名',
    '真的分完。然后问：「你手上这一份，该叫什么？」\n\n'
    + '让他们自己起名字，写法最后才由你补上。');
  card(s, 4.75, 1.9, 4.0, 3.05, '第 4 步 · 7 分钟', '换个情境再来一次',
    '一根绳子分给三个人。八块钱分给五个人。\n\n'
    + '同一个东西在第二个场合又出现一次——这一次比第一次更重要。');
  card(s, 8.95, 1.9, 3.8, 3.05, '第 5 步 · 2 分钟', '当堂开新缺口',
    '「那 1/2 和 1/3，谁大？」\n\n'
    + '让他们吵。不给答案，下课。下一节课从这里接。', 'F7EFEC');
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 5.12, w: 12.2, h: 1.55, rectRadius: 0.06, fill: { color: INK },
  });
  s.addText('第 5 步为什么放在这一节课里，而不是等一周后再发现', {
    x: 0.9, y: 5.28, w: 11.5, h: 0.45, fontFace: H, fontSize: 21, color: PAPER, bold: true, margin: 0,
  });
  s.addText('那半个班答错，是在一周之后才被发现的。而这一撞，本来可以发生在这节课的最后两分钟。'
    + '早两分钟撞上，你还在场；晚一周撞上，你已经在讲下一单元了。', {
    x: 0.92, y: 5.78, w: 11.5, h: 0.8, fontFace: B, fontSize: 15,
    color: 'C9BEB0', lineSpacing: 24, margin: 0,
  });
}

/* ══ 13 段落三 ══ */
section('三', '当堂怎么知道成了没有', '不用等考试，也不用等一周。下课前两分钟就有答案。', ++n);

/* ══ 14 那一问 ══ */
{
  const s = light('下课前的那一问', '不问会不会做', ++n);
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 1.9, w: 12.2, h: 1.4, rectRadius: 0.06, fill: { color: SAND },
  });
  s.addText('「今天，你有没有哪个原来的想法被推翻了？是哪一个？」', {
    x: 0.9, y: 2.15, w: 11.5, h: 0.6, fontFace: H, fontSize: 27, color: CLAY, bold: true, margin: 0,
  });
  s.addText('答得上来的人数，就是这节课的成绩。', {
    x: 0.92, y: 2.8, w: 11.5, h: 0.4, fontFace: B, fontSize: 15, color: '4A423B', margin: 0,
  });
  card(s, 0.55, 3.35, 6.0, 2.05, '这一课答得好的样子', '「我以前以为数越大越大」',
    '或者：「我以前以为分不完就是分不了。」——旧想法被点名了。');
  card(s, 6.75, 3.35, 6.0, 2.05, '答不上来的样子', '「学会了分数」',
    '这不是答案，这是复述课题。它说明账没动。', 'F7EFEC');
  s.addText('三个当堂能记的数（不用问学生，自己就能记）', {
    x: 0.55, y: 5.52, w: 12.2, h: 0.4, fontFace: B, fontSize: 13,
    color: CLAY, bold: true, charSpacing: 1.5, margin: 0,
  });
  const three = [
    ['你改了几次下一句', '因为孩子说的话而临时改口。零次＝你在放录音。'],
    ['几个人押了说法', '主动说出自己想法的人数（错的也算）。'],
    ['全班一起悬着多久', '没人知道答案、全场在等的时间，加起来。'],
  ];
  let x2 = 0.55;
  three.forEach((t) => {
    s.addShape(P.ShapeType.roundRect, {
      x: x2, y: 5.82, w: 3.94, h: 0.95, rectRadius: 0.05, fill: { color: SAND },
    });
    s.addText(t[0], {
      x: x2 + 0.25, y: 5.93, w: 3.5, h: 0.32, fontFace: H, fontSize: 15,
      color: INK, bold: true, margin: 0,
    });
    s.addText(t[1], {
      x: x2 + 0.25, y: 6.25, w: 3.5, h: 0.45, fontFace: B, fontSize: 11.5,
      color: '5A524B', lineSpacing: 16, margin: 0,
    });
    x2 += 4.13;
  });
}

/* ══ 15 一周后 ══ */
{
  const s = light('真正的验收', '一周以后，再问一次', ++n);
  s.addText('当堂那一问只能说明「今天动了」。这一课有没有真的落下去，'
    + '要等一周后那句不带算式的问话。', {
    x: 0.55, y: 1.85, w: 12.2, h: 0.6, fontFace: B, fontSize: 16,
    color: '4A423B', lineSpacing: 26, margin: 0,
  });
  s.addTable([
    [{ text: '一周后这样问', options: { bold: true } },
     { text: '答对说明什么', options: { bold: true } },
     { text: '答错说明什么', options: { bold: true } }],
    ['1/2 和 1/3，谁大？（不许算）', '分母那个位置，他真的看懂了',
      '旧账还在：他仍然只看见「3 比 2 大」'],
    ['1/4 是不是比 1 小？为什么？', '他能说出「一份不到一整个」', '他只会背写法，没有分过'],
    ['你能不能自己造一个比 1/4 小的？', '他站到了定规矩那一边', '他还站在接规矩那一边'],
  ], {
    x: 0.55, y: 2.7, w: 12.2, colW: [4.2, 4.0, 4.0],
    fontFace: B, fontSize: 13.5, color: '3A332E', border: { pt: 0.5, color: LINE },
    fill: { color: PAPER }, rowH: 0.62, valign: 'middle',
  });
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 5.35, w: 12.2, h: 1.05, rectRadius: 0.06, fill: { color: SAND },
  });
  s.addText('第三问最狠：会用的人未必会造，会造的人一定会用。', {
    x: 0.9, y: 5.62, w: 11.5, h: 0.5, fontFace: H, fontSize: 20, color: CLAY, bold: true, margin: 0,
  });
}

/* ══ 16 段落四 ══ */
section('四', '四个坑，和两栏话', '看着像那么回事，其实还是老办法——这四种最常见。', ++n);

/* ══ 17 四个坑 ══ */
{
  const s = light('四个最常踩的坑', '看着像，其实不是', ++n);
  const pits = [
    ['①', '假缺口', '孩子早就会切一半了，你还假装这是个难题。缺口是假的，后面全是表演。',
      '验法：有没有人真的争起来。'],
    ['②', '替他跑了', '工具给了，路却是老师一路演示到底。孩子看了一遍，没走过一步。',
      '验法：每一组的纸片是不是他们自己撕的。'],
    ['③', '热闹代替发生', '撕了、摆了、笑了，最后没有命名、没有写下来、没有收回。',
      '验法：黑板上有没有留下他们说出来的那个名字。'],
    ['④', '忘了最后两分钟', '前面都做对了，下课铃一响就散了。那一问没问，这节课就没有读数。',
      '验法：你手上有没有那三个数。'],
  ];
  let px = 0.55, py = 1.85;
  pits.forEach((p, i) => {
    const x = px + (i % 2) * 6.2, y = py + Math.floor(i / 2) * 2.28;
    s.addShape(P.ShapeType.roundRect, {
      x, y, w: 6.0, h: 2.15, rectRadius: 0.06, fill: { color: i === 3 ? 'F7EFEC' : SAND },
    });
    s.addText(p[0], {
      x: x + 0.3, y: y + 0.22, w: 0.5, h: 0.4, fontFace: H, fontSize: 20,
      color: CLAY, bold: true, margin: 0,
    });
    s.addText(p[1], {
      x: x + 0.85, y: y + 0.22, w: 4.9, h: 0.4, fontFace: H, fontSize: 18,
      color: INK, bold: true, margin: 0,
    });
    s.addText(p[2], {
      x: x + 0.3, y: y + 0.72, w: 5.4, h: 0.85, fontFace: B, fontSize: 13,
      color: '4A423B', lineSpacing: 20, margin: 0,
    });
    s.addText(p[3], {
      x: x + 0.3, y: y + 1.6, w: 5.4, h: 0.35, fontFace: B, fontSize: 12.5,
      color: CLAY, bold: true, margin: 0,
    });
  });
  s.addText('四个坑有一个共同点：都能让课看起来很好看。所以只能靠验法，不能靠感觉。', {
    x: 0.55, y: 6.42, w: 12.2, h: 0.45, fontFace: H, fontSize: 17, color: INK, bold: true, margin: 0,
  });
}

/* ══ 18 不要说要说 ══ */
{
  const s = light('课堂用语', '这一课里，不要说 / 改成', ++n);
  s.addTable([
    [{ text: '不要说', options: { bold: true, color: CLAY } },
     { text: '改成', options: { bold: true, color: SAGE } }],
    ['「分数就是几分之几，记住。」', '「先别记。你现在打算怎么分？」'],
    ['「切成四份不就行了。」', '「你们那一块，为什么要那样切？」'],
    ['「对，就是四分之一。」', '「你管它叫什么？写给大家看看。」'],
    ['「错了，我再讲一遍。」', '「按你的分法往下走，走到哪儿走不动了？」'],
    ['「时间不够了，答案是……」', '「这个我们先不定下来，下节课接着卡。」'],
  ], {
    x: 0.55, y: 1.95, w: 12.2, colW: [6.1, 6.1],
    fontFace: B, fontSize: 15, color: '3A332E', border: { pt: 0.5, color: LINE },
    fill: { color: PAPER }, rowH: 0.68, valign: 'middle',
  });
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 5.9, w: 12.2, h: 0.85, rectRadius: 0.06, fill: { color: SAND },
  });
  s.addText('右边这五句的共同点：都不需要老师先知道答案，也都把话还给了孩子。', {
    x: 0.9, y: 6.1, w: 11.5, h: 0.45, fontFace: H, fontSize: 18, color: INK, bold: true, margin: 0,
  });
}

/* ══ 19 任务单 ══ */
{
  const s = light('可复印 · 学生用', '分饼记录单', ++n);
  s.addText('印在一张纸上，四人一组一张。第 3 步用。'
    + '　最后一行是最重要的一行——它就是「那一问」的书面版。', {
    x: 0.55, y: 1.82, w: 12.2, h: 0.4, fontFace: B, fontSize: 14, color: GREY, margin: 0,
  });
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 2.3, w: 12.2, h: 4.4, rectRadius: 0.06,
    fill: { color: PAPER }, line: { color: LINE, width: 1 },
  });
  const items = [
    '一、三个饼，我们组是这样分的（画出来）：',
    '二、每个人分到的那一份，我们管它叫：＿＿＿＿＿＿＿＿＿＿',
    '三、为什么这样分，大家都不吃亏？',
    '四、如果是三个饼分给五个人呢？还能这样分吗？',
    '五、今天有一件事，跟我原来想的不一样，是：',
  ];
  let iy = 2.55;
  items.forEach((t, i) => {
    s.addText(t, {
      x: 0.9, y: iy, w: 11.5, h: 0.35, fontFace: H, fontSize: 15.5,
      color: INK, bold: true, margin: 0,
    });
    if (i > 0) {
      s.addShape(P.ShapeType.line, {
        x: 0.95, y: iy + 0.52, w: 11.35, h: 0, line: { color: LINE, width: 1 },
      });
    }
    iy += i === 0 ? 1.30 : 0.72;
  });
}

/* ══ 20 备课模板 ══ */
{
  const s = light('可复印 · 老师用', '把你自己的一节课填进去', ++n);
  s.addText('这一课件讲的是分数。同一张表，换成小数、负数、乘法、面积，一样能填。', {
    x: 0.55, y: 1.82, w: 12.2, h: 0.4, fontFace: B, fontSize: 14, color: GREY, margin: 0,
  });
  s.addTable([
    [{ text: '这一步', options: { bold: true } }, { text: '我这一课打算怎么做', options: { bold: true } }],
    ['① 我抛出的那个真实难题是', '＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿'],
    ['② 我只给的那个方向是（不是答案）', '＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿'],
    ['③ 孩子亲手做的那一步是', '＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿'],
    ['④ 我换的第二个情境是', '＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿'],
    ['⑤ 下课前我要开的新缺口是', '＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿'],
    ['⑥ 那一问我打算怎么问', '＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿'],
  ], {
    x: 0.55, y: 2.35, w: 12.2, colW: [4.6, 7.6],
    fontFace: B, fontSize: 13.5, color: '3A332E', border: { pt: 0.5, color: LINE },
    fill: { color: PAPER }, rowH: 0.5, valign: 'middle',
  });
  s.addShape(P.ShapeType.roundRect, {
    x: 0.55, y: 6.05, w: 12.2, h: 0.75, rectRadius: 0.06, fill: { color: SAND },
  });
  s.addText('六行填不满，就先别上这一课——填不满说明缺口还没找到。', {
    x: 0.9, y: 6.21, w: 11.5, h: 0.45, fontFace: H, fontSize: 18, color: CLAY, bold: true, margin: 0,
  });
}

/* ══ 21 收束 ══ */
{
  const s = P.addSlide();
  s.background = { color: INK };
  pie(s, 10.6, 4.15, 1.9, 4, CLAY);
  s.addText('分数不在课本里。', {
    x: 0.9, y: 2.0, w: 10, h: 0.85, fontFace: H, fontSize: 40, color: PAPER, bold: true, margin: 0,
  });
  s.addText('它在那三个饼被真的分开的那一刻。', {
    x: 0.9, y: 2.95, w: 10, h: 0.85, fontFace: H, fontSize: 40, color: CLAY, bold: true, margin: 0,
  });
  s.addShape(P.ShapeType.line, {
    x: 0.92, y: 4.2, w: 2.2, h: 0, line: { color: CLAY, width: 2 },
  });
  s.addText('留给你的一件事：明天挑一个你最熟的概念，只做一件事——'
    + '找到它「走不通」的那个地方。找到了，这一课就已经开始了。', {
    x: 0.92, y: 4.5, w: 9.2, h: 1.0, fontFace: B, fontSize: 16,
    color: '9C9187', lineSpacing: 26, margin: 0,
  });
  foot(s, ++n);
}

P.writeFile({ fileName: '/home/claude/fen/分数的发生学课件.pptx' })
  .then(() => console.log('已写出', n, '页'));
