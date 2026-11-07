#!/usr/bin/env python3
"""第 607 号《SDE思想大全》：由统稿 book.md ＋ notes.json（来源注）出全书 Word（pandoc），中文用 Noto Serif CJK SC，标题藏青。
用法（仓库根目录）：python3 tools/book-m607/make_docx.py --out <dir>
产物：<dir>/sde-compendium.docx
"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402


def reference_docx(tmp):
    """取 pandoc 默认参考文档，改字体与标题颜色。"""
    import docx
    from docx.shared import RGBColor, Pt
    from docx.oxml.ns import qn
    ref = tmp / 'ref.docx'
    with open(ref, 'wb') as f:
        f.write(subprocess.run(['pandoc', '--print-default-data-file', 'reference.docx'], capture_output=True, check=True).stdout)
    d = docx.Document(str(ref))
    for st in d.styles:
        try:
            f = st.font
        except Exception:
            continue
        if f is None:
            continue
        f.name = 'Noto Serif CJK SC'
        rpr = st.element.get_or_add_rPr()
        rf = rpr.find(qn('w:rFonts'))
        if rf is None:
            rf = rpr.makeelement(qn('w:rFonts'), {}); rpr.append(rf)
        for k in ('w:eastAsia', 'w:ascii', 'w:hAnsi'):
            rf.set(qn(k), 'Noto Serif CJK SC')
        if st.name.startswith('Heading') or st.name == 'Title':
            f.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    d.styles['Normal'].font.size = Pt(10.5)
    d.save(str(ref))
    return ref


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    md = (HERE / 'book.md').read_text()
    import json
    notes = json.loads((HERE / 'notes.json').read_text(encoding='utf-8'))

    def note_md(stem):
        n = notes.get(stem)
        if not n or not n['paras']:
            return ''
        out = ['', '**%s**' % (n['title'] or '来源注'), '']
        for p in n['paras']:
            out += [re.sub(r'^- ', '', p), '']
        return '\n'.join(out)
    outl, cur = [], None
    for l in md.split('\n'):
        m = re.match(r'^## 第 (\d+) 章', l)
        if l.startswith('# ') or m:
            if cur:
                outl.append(note_md(cur)); cur = None
            if m:
                cur = 'ch%03d' % int(m[1])
            elif l.startswith('# 总导论'):
                cur = 'intro_anchor'
            elif l.startswith('# 总合论'):
                cur = 'conclusion'
        outl.append(l)
    if cur:
        outl.append(note_md(cur))
    md = '\n'.join(outl)
    md = re.sub(r'^◆ ', '### ', md, flags=re.M)
    md = re.sub(r'^\\\[\n(.*?)\n\\\]$', lambda m: '$$' + m[1].replace('\\qquad', '\\quad') + '$$', md, flags=re.M | re.S)
    md = re.sub(r'^\*\*编序\*\*$', '*编序*\n', md, flags=re.M)
    head = ('---\ntitle: "%s"\nsubtitle: "%s"\nauthor: "%s 著"\ndate: "德麦国际专著第 %d 号 · ISBN %s · %s · %s"\nlang: zh-CN\n---\n\n'
            % (M.TITLE, M.SUBTITLE, M.AUTHOR, M.NO, M.ISBN, M.PRICE, M.EDITION_SP))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / 'book.md'
        src.write_text(head + md)
        out = a.out / ('%s.docx' % M.SLUG)
        subprocess.run(['pandoc', str(src), '-f', 'markdown-auto_identifiers', '-o', str(out), '--toc', '--toc-depth=2',
                        '--reference-doc', str(reference_docx(td)), '--metadata', 'toc-title=目录'], check=True)
    print('docx ok', out, out.stat().st_size)


if __name__ == '__main__':
    main()
