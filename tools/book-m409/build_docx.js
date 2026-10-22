// 《教育的产品是结晶》Word 版：与 PDF 同源（front/ parts/ back/），供改字用。
const fs = require('fs');
const path = require('path');
const D = require('docx');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, LevelFormat, Footer, Header, PageNumber,
        PageBreak, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType } = D;
const ROOT = __dirname;
const NAVY = '1F3A5F', GOLD = 'B08A3C', CYAN = '58A9B5', DIM = '8A8578', INK = '2A2824';
const SERIF = '宋体', SANS = '黑体', KAI = '楷体';
const W = 9638 - 2 * 1080; // 170×240 mm 开本内容宽
const rd = f => fs.readFileSync(path.join(ROOT, f), 'utf8');

function runs(t, base = {}) {
  const o = [];
  t.split(/(\*\*[^*]+\*\*)/).forEach(s => {
    if (!s) return;
    if (s.startsWith('**') && s.endsWith('**')) o.push(new TextRun({ text: s.slice(2, -2), bold: true, color: NAVY, ...base }));
    else o.push(new TextRun({ text: s, ...base }));
  });
  return o;
}
const body = { font: SERIF, size: 22, color: INK };
const P = (t, o = {}) => new Paragraph({ spacing: { after: 140, line: 380 }, indent: { firstLine: 440 }, alignment: AlignmentType.JUSTIFIED, children: runs(t, body), ...o });
const box = (label, lines, color, fill, opt = {}) => {
  const ps = [new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: label, font: SANS, size: 16, bold: true, color, characterSpacing: 60 })] })];
  lines.forEach(l => ps.push(new Paragraph({ spacing: { after: 60, line: 340 }, children: runs(l, { font: SERIF, size: opt.size || 20, color: opt.color || INK, bold: !!opt.bold }) })));
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W],
    borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
               left: { style: BorderStyle.SINGLE, size: 18, color }, insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
    rows: [new TableRow({ children: [new TableCell({ width: { size: W, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill },
      margins: { top: 120, bottom: 120, left: 200, right: 200 }, children: ps })] })] });
};
const gap = () => new Paragraph({ spacing: { after: 120 }, children: [] });

function blocks(text) {
  // 与 build.py 的 blocks_of 同理：段落、标题、引用块、列表、表格
  const out = []; let buf = [], kind = null;
  const flush = () => { if (buf.length) out.push([kind, buf]); buf = []; kind = null; };
  for (const raw of text.split('\n')) {
    const l = raw.trimEnd();
    if (!l.trim()) { flush(); continue; }
    if (l.startsWith('>')) { if (kind !== 'q') { flush(); kind = 'q'; } buf.push(l.replace(/^>\s?/, '')); continue; }
    if (l.startsWith('|')) { if (kind !== 't') { flush(); kind = 't'; } buf.push(l); continue; }
    const m = l.match(/^(#{1,3}) (.*)$/);
    if (m) { flush(); out.push(['h' + m[1].length, [m[2]]]); continue; }
    if (l.startsWith('- ')) { if (kind !== 'ul') { flush(); kind = 'ul'; } buf.push(l.slice(2)); continue; }
    if (/^\d+\. /.test(l)) { if (kind !== 'ol') { flush(); kind = 'ol'; } buf.push(l); continue; }
    if (['ul', 'ol', 'q', 't'].includes(kind)) flush();
    kind = kind || 'p'; buf.push(l.trim());
  }
  flush();
  return out.map(([k, b]) => k === 'p' ? ['p', [b.join('')]] : [k, b]);
}

function render(bl, K) {
  for (const [k, b] of bl) {
    if (k === 'p') {
      const t = b[0];
      if (/^〔[^〔〕]*〕$/.test(t)) K.push(new Paragraph({ spacing: { after: 160, line: 320 }, children: [new TextRun({ text: t, font: SANS, size: 17, color: DIM })] }));
      else if (t.startsWith('【场景】')) K.push(new Paragraph({ spacing: { before: 120, after: 160 }, children: [
        new TextRun({ text: '场　景　', font: SANS, size: 16, bold: true, color: GOLD }), ...runs(t.slice(4), { font: SERIF, size: 22, bold: true, color: NAVY })] }));
      else K.push(P(t));
    } else if (k === 'h3') {
      const t = b[0].replace(/^◆\s*/, '');
      K.push(new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, spacing: { before: 320, after: 160 }, children: [
        new TextRun({ text: '◆  ', color: GOLD, size: 18 }), new TextRun({ text: t, font: SANS, size: 23, bold: true, color: NAVY })] }));
    } else if (k === 'q') {
      const first = b[0].trim(), rest = b.slice(1).filter(x => x.trim());
      const mq = first.match(/^\*\*这一章的问题\*\*：(.*)$/);
      if (mq) { K.push(box('这一章的问题', [mq[1]], CYAN, 'F7F3E8', { size: 21 })); K.push(gap()); }
      else if (first === '**带走的话**') { K.push(gap()); K.push(box('带走的话', rest, GOLD, 'F6F1E4', { bold: true, color: NAVY, size: 21 })); }
      else if (first === '**想一想**') { K.push(box('想一想', rest, CYAN, 'F7F3E8', { size: 19, color: '4A463D' })); }
      else if (first === '**小账**') { K.push(gap()); K.push(box('小　账', rest, 'D8CFBB', 'F4EFE3', { size: 18, color: '5A554A' })); }
      else { const ls = b.filter(x => x.trim()); const allb = ls.every(x => /^\*\*.+\*\*$/.test(x.trim())); K.push(box('', ls, GOLD, allb ? 'F6F1E4' : 'FBF8F0', allb ? { bold: true, color: NAVY } : { size: 20, color: '4A463D' })); K.push(gap()); }
    } else if (k === 'ul') {
      b.forEach(x => K.push(new Paragraph({ numbering: { reference: 'b', level: 0 }, spacing: { after: 80, line: 360 }, children: runs(x, body) })));
    } else if (k === 'ol') {
      b.forEach(x => { const m = x.match(/^(\d+)\. (.*)$/); K.push(new Paragraph({ spacing: { after: 80, line: 360 }, indent: { left: 440, hanging: 440 }, children: [new TextRun({ text: m[1] + '. ', ...body }), ...runs(m[2], body)] })); });
    } else if (k === 't') {
      const rows = b.map(r => r.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim())).filter(r => !r.every(c => /^:?-{2,}:?$/.test(c)));
      const n = rows[0].length, cw = Math.floor(W / n);
      K.push(new Table({ width: { size: cw * n, type: WidthType.DXA }, columnWidths: Array(n).fill(cw), rows: rows.map((r, i) => new TableRow({ children: r.map(c => new TableCell({
        width: { size: cw, type: WidthType.DXA }, shading: i === 0 ? { type: ShadingType.CLEAR, fill: NAVY } : undefined, margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ children: runs(c, { font: i === 0 ? SANS : SERIF, size: 18, color: i === 0 ? 'FBF8F0' : INK, bold: i === 0 }) })] })) })) }));
      K.push(gap());
    }
  }
}
const brk = () => new Paragraph({ children: [new PageBreak()] });
const center = (t, o) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: o.sp || { after: 200 }, ...(o.h ? { heading: o.h } : {}), children: [new TextRun({ text: t, ...o.r })] });

const K = [];
// 书名页
K.push(center('德麦国际专著 · ' + ('第 409 号'), { sp: { before: 2400, after: 300 }, r: { font: SERIF, size: 22, color: NAVY, characterSpacing: 80 } }));
K.push(center('教育的产品是结晶', { sp: { after: 300 }, r: { font: SERIF, size: 72, bold: true, color: NAVY, characterSpacing: 120 } }));
K.push(center('AI 时代，为什么学了却没学会', { sp: { after: 2600 }, r: { font: SERIF, size: 24, color: GOLD } }));
K.push(center('王德生　著', { sp: { after: 1800 }, r: { font: SERIF, size: 26, characterSpacing: 60 } }));
K.push(center('德麦国际出版社', { sp: { after: 60 }, r: { font: SANS, size: 20, bold: true, color: NAVY, characterSpacing: 100 } }));
K.push(center('Demai International Press · Singapore', { r: { font: SANS, size: 16, color: DIM } }));
// 前置
const front = blocks(rd('front/00-前置.md'));
let grp = null; const groups = [];
for (const [k, b] of front) { if (k === 'h2') { grp = [b[0], []]; groups.push(grp); } else if (grp) grp[1].push([k, b]); }
for (const [title, bl] of groups) {
  K.push(brk());
  if (title === '题词') {
    const ps = bl.filter(x => x[0] === 'p').map(x => x[1][0]);
    K.push(new Paragraph({ spacing: { before: 3600 }, children: [] }));
    ps.forEach(x => K.push(center(x.replace('【题词】', '').replace('【题词署】', ''), { r: { font: SERIF, size: x.startsWith('【题词署】') ? 18 : 28, color: x.startsWith('【题词署】') ? DIM : NAVY, characterSpacing: 60 } })));
    continue;
  }
  K.push(center(title === '出版信息' ? '出 版 信 息' : title, { h: HeadingLevel.HEADING_1, sp: { before: 400, after: 360 }, r: { font: SANS, size: 30, bold: true, color: NAVY } }));
  render(bl, K);
}
// 目录（静态）
K.push(brk());
K.push(center('目　录', { sp: { before: 300, after: 360 }, r: { font: SANS, size: 32, bold: true, color: NAVY } }));
const tocLine = (t, lvl) => K.push(new Paragraph({ spacing: { after: 60, before: lvl === 0 ? 160 : 0 }, indent: { left: lvl === 2 ? 480 : 0 }, children: [new TextRun({ text: t, font: lvl === 2 ? SERIF : SANS, size: lvl === 2 ? 20 : 21, bold: lvl !== 2, color: lvl === 2 ? INK : NAVY })] }));
const hasLun = fs.existsSync(path.join(ROOT, 'front/01-导论.md'));
if (hasLun) tocLine(rd('front/01-导论.md').split('\n')[0].slice(2), 1);
const partFiles = fs.readdirSync(path.join(ROOT, 'parts')).filter(f => f.endsWith('.md')).sort();
for (const f of partFiles) {
  const t = rd('parts/' + f);
  tocLine(t.split('\n')[0].slice(2), 0);
  t.split('\n').filter(l => l.startsWith('## ')).forEach(l => tocLine(l.slice(3), 2));
}
tocLine(rd('back/09-结语.md').split('\n')[0].slice(2), 0);
rd('back/10-后置.md').split('\n').filter(l => /^#{1,2} /.test(l)).forEach(l => tocLine(l.replace(/^#+ /, ''), l.startsWith('## ') ? 2 : 0));
// 引子
const chapHead = (lab, title) => {
  K.push(brk());
  if (lab) K.push(new Paragraph({ spacing: { before: 600, after: 80 }, children: [new TextRun({ text: lab, font: SANS, size: 18, bold: true, color: GOLD })] }));
  K.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: lab ? 0 : 600, after: 120 }, children: [new TextRun({ text: title, font: SERIF, size: 34, bold: true, color: NAVY })] }));
  K.push(new Paragraph({ spacing: { after: 360 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 1 } }, indent: { right: 6700 }, children: [] }));
};
if (hasLun) { const lun = rd('front/01-导论.md').split('\n'); const [ln, ls] = lun[0].slice(2).split('　'); chapHead(ln, ls); render(blocks(lun.slice(1).join('\n')), K); }
for (const f of partFiles) {
  const lines = rd('parts/' + f).split('\n');
  const [pl, pt] = lines[0].slice(2).split(/　(.*)/s);
  K.push(brk());
  K.push(center(pl.split('').join(' '), { h: HeadingLevel.HEADING_1, sp: { before: 2600, after: 240 }, r: { font: SANS, size: 22, bold: true, color: GOLD, characterSpacing: 200 } }));
  K.push(center(pt, { sp: { after: 360 }, r: { font: SERIF, size: 36, bold: true, color: NAVY } }));
  K.push(center('导　语', { sp: { after: 200 }, r: { font: SANS, size: 18, bold: true, color: GOLD } }));
  let i = 1; const intro = [];
  while (i < lines.length && !lines[i].startsWith('## ')) { if (lines[i].trim()) intro.push(lines[i].trim()); i++; }
  intro.forEach(t => K.push(P(t, { children: runs(t, { font: SERIF, size: 21, color: '4A463D' }) })));
  let cur = null;
  const flushCh = () => { if (cur) { const [lab, tt] = cur[0].split('　'); chapHead(lab, tt); render(blocks(cur[1].join('\n')), K); K.push(center('◆', { sp: { before: 200 }, r: { color: GOLD, size: 16 } })); } };
  for (; i < lines.length; i++) { if (lines[i].startsWith('## ')) { flushCh(); cur = [lines[i].slice(3), []]; } else if (cur) cur[1].push(lines[i]); }
  flushCh();
}
const jy = rd('back/09-结语.md').split('\n');
const [jn, js] = jy[0].slice(2).split('　');
chapHead(jn, js);
render(blocks(jy.slice(1).join('\n')), K);
// 后置
const back = rd('back/10-后置.md').split('\n');
let cur = null; const items = [];
for (const l of back) { if (/^#{1,2} /.test(l)) { cur = [l.replace(/^#+ /, ''), l.startsWith('## ') ? 2 : 1, []]; items.push(cur); } else if (cur) cur[2].push(l); }
for (const [t, lv, bl] of items) {
  const [a, b] = t.split('　');
  chapHead(b ? a : '', b || a);
  render(blocks(bl.join('\n')), K);
}

const doc = new Document({
  creator: '王德生', title: '教育的产品是结晶——AI 时代，为什么学了却没学会',
  styles: { default: { document: { run: { font: SERIF, size: 22 } } }, paragraphStyles: [
    { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: SANS, size: 32, bold: true }, paragraph: { outlineLevel: 0 } },
    { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: SERIF, size: 34, bold: true }, paragraph: { outlineLevel: 1 } },
    { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: SANS, size: 23, bold: true }, paragraph: { outlineLevel: 2 } }] },
  numbering: { config: [{ reference: 'b', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 9638, height: 13606 }, margin: { top: 1150, bottom: 1150, left: 1080, right: 1080 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '教育的产品是结晶', font: SANS, size: 15, color: DIM })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 16, color: DIM })] })] }) },
    children: K }] });
Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2] || path.join(ROOT, 'build/jiaoyu-de-chanpin.docx'), b); console.log('docx ok'); });
