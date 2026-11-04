#!/usr/bin/env python3
"""第 572 号《K线人生——跃迁无法设计，只能接住》：由分卷稿 book.md 出全书 Word（pandoc），中文用宋体／Noto Serif CJK SC，标题藏青。
第 26 章的十张缠图从 public/books/m/572/text/charts/ 取（--resource-path），嵌进 Word。
用法（仓库根目录）：python3 tools/book-m572/make_docx.py --out <b572>
产物：<out>/k-line-life.docx
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
    md = md.replace('【题词署】', '').replace('【题词】', '')
    md = re.sub(r'^### ◆ ', '### ', md, flags=re.M)
    md = '![](cover.jpg){width=5.8in}\n\n' + md + '\n\n![](backcover.jpg){width=5.8in}\n'
    head = ('---\ntitle: "%s"\nsubtitle: "%s"\nauthor: "%s 著"\ndate: "%s · ISBN %s · %s · %s"\nlang: zh-CN\n---\n\n'
            % (M.TITLE, M.SUBTITLE, M.AUTHOR, M.NOLABEL, M.ISBN, M.PRICE, M.EDITION_SP))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / 'book.md'
        src.write_text(head + md)
        out = a.out / ('%s.docx' % M.SLUG)
        md_dir = HERE.resolve().parents[1] / ('public/books/m/%d/text' % M.NO)
        src.write_text(head + re.sub(r'^(!\[[^\]]*\]\([^)]+\))$', r'\1{width=6.2in}', md, flags=re.M))
        subprocess.run(['pandoc', str(src), '-f', 'markdown-auto_identifiers', '-o', str(out), '--toc', '--toc-depth=2',
                        '--resource-path', str(a.out),
                        '--reference-doc', str(reference_docx(td)), '--metadata', 'toc-title=目录'], check=True)
    print('docx ok', out, out.stat().st_size)


if __name__ == '__main__':
    main()
