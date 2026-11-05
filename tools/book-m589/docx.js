// book.json → Word 版，版式向第 220、302 号靠：藏青标题、浅金章码、金色“第 N 章”、金短线、◆ 小节、米底金线答案卡。
const fs = require('fs');
const D = JSON.parse(fs.readFileSync('/home/claude/sde_ai_millennium/layout/book.json', 'utf8'));
const X = require('docx');
const { Document, Packer, Paragraph, TextRun, ImageRun, ShadingType, HeadingLevel, AlignmentType, Footer, Header, PageNumber, NumberFormat, TabStopType, LeaderType, Bookmark, InternalHyperlink, PageReference, Table, TableRow, TableCell, WidthType, BorderStyle, SectionType, VerticalAlign } = X;
const NAVY = '1F3A5F', GOLD = 'B08A3C', PALE = 'D9C39A', PAPER = 'FBF8F0', CARD = 'F6F1E4', INK = '2A2824', DIM = '8A8578';
const SONG = { ascii: 'Times New Roman', hAnsi: 'Times New Roman', eastAsia: '宋体', cs: '宋体' };
const HEI = { ascii: 'Arial', hAnsi: 'Arial', eastAsia: '黑体', cs: '黑体' };
const MM = 56.7;
const PAGE = { size: { width: Math.round(170 * MM), height: Math.round(240 * MM) }, margin: { top: Math.round(22 * MM), bottom: Math.round(20 * MM), left: Math.round(19 * MM), right: Math.round(17 * MM), header: Math.round(10 * MM), footer: Math.round(9 * MM) } };
const TW = PAGE.size.width - PAGE.margin.left - PAGE.margin.right;
const SZ = 21;
function runs(s, o = {}) {
  const size = o.size || SZ, out = [];
  for (const part of s.split(/(\*\*[^*]+\*\*|【设想与模拟[^】]*】)/).filter(Boolean)) {
    if (part.startsWith('**')) out.push(new TextRun({ text: part.slice(2, -2), font: o.dlg ? HEI : SONG, size, bold: true, color: NAVY }));
    else if (part.startsWith('【')) out.push(new TextRun({ text: part, font: HEI, size: size - 4, color: '8F7434' }));
    else out.push(new TextRun({ text: part, font: o.font || SONG, size, color: o.color || INK }));
  }
  return out;
}
const rule = (center) => new Paragraph({ spacing: { before: 60, after: 240 }, alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT,
  indent: center ? { left: Math.round(TW / 2 - 370), right: Math.round(TW / 2 - 370) } : { right: TW - 740 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 1 } }, children: [] });
const LBORDER = { left: { style: BorderStyle.SINGLE, size: 12, color: GOLD, space: 8 } };
function blocks(bl) {
  const out = [];
  for (const b of bl) {
    if (b.k === 'p') out.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 90, line: 380 }, indent: { firstLine: SZ * 2 }, widowControl: true, children: runs(b.s) }));
    else if (b.k === 'dlg') out.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 100, line: 380 }, children: runs(b.s, { dlg: true }) }));
    else if (b.k === 'sec') out.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: '◆ ', color: GOLD, size: 17, font: HEI }), new TextRun({ text: b.s })] }));
    else if (b.k === 'sub') out.push(new Paragraph({ spacing: { before: 240, after: 110 }, keepNext: true, children: [new TextRun({ text: b.s, font: SONG, bold: true, size: 23, color: NAVY })] }));
    else if (b.k === 'sim') out.push(new Paragraph({ spacing: { before: 60, after: 140, line: 290 }, indent: { left: 120 }, border: { left: { style: BorderStyle.SINGLE, size: 8, color: PALE, space: 7 } }, children: [new TextRun({ text: b.s, font: HEI, size: 17, color: '8F7434' })] }));
    else if (b.k === 'bib') out.push(new Paragraph({ spacing: { after: 60, line: 320 }, indent: { left: 420, hanging: 420 }, children: runs(b.s, { size: 19 }) }));
    else if (b.k === 'card') {
      const sh = { type: ShadingType.CLEAR, fill: CARD, color: 'auto' };
      out.push(new Paragraph({ shading: sh, border: LBORDER, indent: { left: 160, right: 60 }, spacing: { before: 200, after: 0, line: 320 }, keepNext: true, keepLines: true, children: [new TextRun({ text: '答 案 卡', font: HEI, bold: true, size: 16, color: GOLD })] }));
      b.rows.forEach((r, i) => out.push(new Paragraph({ shading: sh, border: LBORDER, indent: { left: 160, right: 60 }, spacing: { after: i === b.rows.length - 1 ? 200 : 0, line: 320 }, keepNext: i < b.rows.length - 1, keepLines: true,
        children: [...(r[0] ? [new TextRun({ text: r[0] + '：', font: HEI, bold: true, size: 18, color: NAVY })] : []), ...runs(r[1], { size: 19 })] })));
    } else if (b.k === 'table') {
      const widths = b.w.map(w => Math.round(TW * w / 100)); widths[widths.length - 1] += TW - widths.reduce((a, c) => a + c, 0);
      const cell = (t, i, head, odd) => new TableCell({ width: { size: widths[i], type: WidthType.DXA }, shading: head ? { type: ShadingType.CLEAR, fill: NAVY, color: 'auto' } : (odd ? { type: ShadingType.CLEAR, fill: CARD, color: 'auto' } : undefined),
        margins: { top: 50, bottom: 50, left: 70, right: 70 }, verticalAlign: VerticalAlign.TOP, children: [new Paragraph({ spacing: { line: 280 }, children: head ? [new TextRun({ text: t, font: HEI, bold: true, size: 17, color: PAPER })] : runs(t, { size: 18 }) })] });
      const none = { style: BorderStyle.NONE, size: 0, color: 'auto' }, line = { style: BorderStyle.SINGLE, size: 4, color: 'E4DCCB' };
      out.push(new Table({ width: { size: TW, type: WidthType.DXA }, columnWidths: widths, borders: { top: none, bottom: line, left: none, right: none, insideHorizontal: line, insideVertical: none },
        rows: [new TableRow({ tableHeader: true, children: b.head.map((t, i) => cell(t, i, true)) }), ...b.rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((t, i) => cell(t, i, false, ri % 2)) }))] }));
    }
  }
  return out;
}
const center = (t, o) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: o.before || 0, after: o.after || 0 }, children: [new TextRun({ text: t, font: o.font || SONG, size: o.size, bold: o.bold, color: o.color || INK })] });
const secs = D.secs, mi = secs.findIndex(s => s.kind === 'part');
function secBody(s, i) {
  const id = 's' + i;
  if (s.kind === 'part') return [
    new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER, spacing: { before: 1500, after: 140 }, children: [new Bookmark({ id, children: [new TextRun({ text: s.label.split('').join(' ') , font: HEI, size: 20, color: GOLD, bold: true })] })] }),
    center(s.name, { font: SONG, size: 38, bold: true, color: NAVY, after: 60 }), rule(true),
    center('导　语', { font: HEI, size: 17, bold: true, color: GOLD, after: 200 }),
    ...s.intro.map(t => new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 90, line: 380 }, indent: { firstLine: 400 }, children: runs(t, { size: 20, color: '4A463D' }) })) ];
  if (s.kind === 'chapter') return [
    new Paragraph({ pageBreakBefore: true, spacing: { before: 120, after: 20 }, keepNext: true, children: [new TextRun({ text: String(s.num).padStart(2, '0'), font: SONG, size: 68, color: PALE })] }),
    new Paragraph({ spacing: { after: 30 }, keepNext: true, children: [new TextRun({ text: `第 ${s.num} 章`, font: HEI, bold: true, size: 17, color: GOLD })] }),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new Bookmark({ id, children: [new TextRun({ text: s.name })] })] }), rule(false), ...blocks(s.blocks),
    center('◆', { size: 16, color: GOLD, before: 200 }) ];
  const lvl = s.kind === 'appx' ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_1;
  return [ new Paragraph({ heading: lvl, pageBreakBefore: true, spacing: { before: 500, after: 40 }, children: [new Bookmark({ id, children: [new TextRun({ text: s.name, font: SONG, size: s.kind === 'appx' ? 30 : 36, bold: true, color: NAVY })] })] }),
    ...(s.sub ? [new Paragraph({ spacing: { after: 20 }, children: [new TextRun({ text: s.sub, font: SONG, size: 21, color: GOLD })] })] : []), rule(false), ...blocks(s.blocks), ...(s.end ? [center('◆', { size: 16, color: GOLD, before: 200 })] : []) ];
}
function tocLine(s, i) {
  const cls = s.kind === 'part' ? 'p' : (s.kind === 'chapter' || s.kind === 'appx') ? 'c' : 'f';
  return new Paragraph({ spacing: { before: cls === 'p' ? 130 : 0, after: 18, line: 300 }, indent: cls === 'c' ? { left: 380 } : undefined, tabStops: [{ type: TabStopType.RIGHT, position: TW, leader: LeaderType.DOT }],
    children: [new InternalHyperlink({ anchor: 's' + i, children: [new TextRun({ text: s.title, font: cls === 'p' ? HEI : SONG, bold: cls === 'p', size: 19, color: cls === 'c' ? INK : NAVY })] }), new TextRun({ text: '\t', size: 18 }), new PageReference('s' + i)] });
}
const imgS = (f, w, h) => new Paragraph({ spacing: { before: 0, after: 0 }, children: [new ImageRun({ type: 'jpg', data: fs.readFileSync(f), transformation: { width: w, height: h } })] });
const OUT = '/home/claude/sde_ai_millennium/layout/out/';
const fullPage = { size: PAGE.size, margin: { top: 0, bottom: 0, left: 0, right: 0, header: 0, footer: 0 } };
const fw = Math.round(170 / 25.4 * 96) - 2, fh = Math.round(240 / 25.4 * 96) - 8;
const cp = secs[0];
const cpT = (() => { const w = [Math.round(TW * .16), TW - Math.round(TW * .16)]; const none = { style: BorderStyle.NONE, size: 0, color: 'auto' };
  return new Table({ width: { size: TW, type: WidthType.DXA }, columnWidths: w, borders: { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none },
    rows: cp.rows.map((r, i) => new TableRow({ children: [0, 1].map(c => new TableCell({ width: { size: w[c], type: WidthType.DXA }, shading: i % 2 ? undefined : { type: ShadingType.CLEAR, fill: 'F4EFE3', color: 'auto' }, margins: { top: 40, bottom: 40, left: 70, right: 70 },
      children: [new Paragraph({ spacing: { line: 270 }, children: [new TextRun({ text: r[c], font: c ? SONG : HEI, size: c ? 17 : 15, color: c ? INK : DIM })] })] })) })) }); })();
const frontKids = [
  new Paragraph({ spacing: { before: 900, after: 300 }, children: [new TextRun({ text: `德麦国际专著 · 第 ${D.meta.no} 号`, font: HEI, size: 17, color: DIM })] }),
  new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: '千年难题，', font: SONG, bold: true, size: 40, color: NAVY })] }),
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: '还要等下一个理论吗？', font: SONG, bold: true, size: 50, color: NAVY })] }),
  new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: D.meta.subtitle, font: SONG, size: 21, color: GOLD })] }), rule(false),
  new Paragraph({ spacing: { before: 1500, after: 1900 }, children: [new TextRun({ text: '王德生　　著', font: SONG, size: 23 })] }),
  new Paragraph({ spacing: { after: 20 }, children: [new TextRun({ text: '德麦国际出版社', font: HEI, bold: true, size: 17, color: NAVY })] }),
  new Paragraph({ children: [new TextRun({ text: 'Demai International Press', font: HEI, size: 14, color: DIM })] }),
  new Paragraph({ pageBreakBefore: true, alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: '出 版 信 息', font: HEI, bold: true, size: 22, color: NAVY })] }),
  cpT, new Paragraph({ spacing: { after: 100 }, children: [] }),
  ...cp.notes.map(t => new Paragraph({ spacing: { after: 44, line: 262 }, children: runs(t, { size: 15, color: '5A554A' }) })),
  new Paragraph({ pageBreakBefore: true, alignment: AlignmentType.CENTER, spacing: { before: 3000, after: 0, line: 500 }, children: [new TextRun({ text: '必须是以 SDE 为核心基底的人-AI 复合智能体来解决千年难题，', font: SONG, size: 22, color: NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200, line: 500 }, children: [new TextRun({ text: '不是一套理论系统的诞生，而是随时生成解决答案。', font: SONG, size: 22, color: NAVY })] }),
  center(D.epigraph[1], { size: 17, color: DIM }),
];
for (let i = 1; i < mi; i++) frontKids.push(...secBody(secs[i], i));
frontKids.push(new Paragraph({ pageBreakBefore: true, spacing: { before: 400, after: 60 }, children: [new TextRun({ text: '目　录', font: SONG, bold: true, size: 36, color: NAVY })] }), rule(false));
secs.forEach((s, i) => { if (s.kind !== 'cp') frontKids.push(tocLine(s, i)); });
const mainKids = [];
for (let i = mi; i < secs.length; i++) { const b = secBody(secs[i], i); mainKids.push(...b); }
const hdr = new Header({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: D.meta.title, font: HEI, size: 14, color: '9A917E' })] })] });
const ftr = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: SONG, size: 16, color: DIM })] })] });
const tiny = () => new Paragraph({ spacing: { before: 0, after: 0, line: 20, lineRule: 'exact' }, children: [new TextRun({ text: '', size: 2 })] });
const blankH = new Header({ children: [tiny()] }), blankF = new Footer({ children: [tiny()] });
const doc = new Document({ title: D.meta.title + '——' + D.meta.subtitle, creator: D.meta.author, description: '德麦国际专著第 ' + D.meta.no + ' 号 · ISBN ' + D.meta.isbn, background: { color: PAPER },
  styles: { default: { document: { run: { font: SONG, size: SZ, color: INK } },
    heading1: { run: { font: SONG, size: 36, bold: true, color: NAVY }, paragraph: { spacing: { before: 300, after: 100 }, keepNext: true, outlineLevel: 0 } },
    heading2: { run: { font: SONG, size: 31, bold: true, color: NAVY }, paragraph: { spacing: { before: 0, after: 60 }, keepNext: true, outlineLevel: 1 } },
    heading3: { run: { font: HEI, size: 22, bold: true, color: NAVY }, paragraph: { spacing: { before: 280, after: 110 }, keepNext: true, outlineLevel: 2 } } } },
  features: { updateFields: false },
  sections: [
    { properties: { page: fullPage }, children: [imgS(OUT + 'cover.jpg', fw, fh)] },
    { properties: { type: SectionType.NEXT_PAGE, page: { ...PAGE, pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } } }, footers: { default: ftr }, children: frontKids },
    { properties: { type: SectionType.NEXT_PAGE, page: { ...PAGE, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } }, headers: { default: hdr }, footers: { default: ftr }, children: mainKids },
    { properties: { type: SectionType.NEXT_PAGE, page: fullPage }, headers: { default: blankH }, footers: { default: blankF }, children: [imgS(OUT + 'backcover.jpg', fw, fh - 14)] },
  ] });
Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2], b); console.log('ok', b.length); });
