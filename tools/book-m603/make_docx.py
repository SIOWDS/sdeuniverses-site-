#!/usr/bin/env python3
"""第 603 号：由统稿 src/manuscript.md 出全书 Word（pandoc）。出版信息页用 book.json 的字段重排，其余照稿；中文用 Noto Serif CJK SC，标题藏青。
用法（仓库根目录）：python3 tools/book-m603/make_docx.py --out <构建目录>
产物：<out>/enterprise-ontology-paradigm.docx
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402


def reference_docx(tmp):
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
    md = (HERE / 'src/manuscript.md').read_text()
    cfg = json.loads((HERE / 'book.json').read_text())
    md = re.sub(r'^◆ (.*)$', r'### \1', md, flags=re.M)
    md = re.sub(r'^#### ', '##### ', md, flags=re.M)
    md = re.sub(r'^【(.*)】$', r'#### \1', md, flags=re.M)
    # 出版信息页按 book.json 重排
    s = md.index('# 出版信息'); e = md.index('# 作者介绍')
    rows = ''.join('**%s：** %s\n\n' % (k, v) for k, v in cfg['pub_rows']) + ''.join(n + '\n\n' for n in cfg.get('pub_notes', []))
    md = md[:s] + '# 出版信息\n\n' + rows + md[e:]
    head = ('---\ntitle: "%s"\nsubtitle: "%s"\nauthor: "%s 著"\ndate: "德麦国际专著第 %d 号 · ISBN %s · %s · %s"\nlang: zh-CN\n---\n\n'
            % (M.TITLE, M.SUBTITLE + '——' + M.SUBTITLE2, M.AUTHOR, M.NO, M.ISBN, M.PRICE, M.EDITION))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / 'book.md'
        src.write_text(head + md)
        out = a.out / ('%s.docx' % M.SLUG)
        subprocess.run(['pandoc', str(src), '-f', 'markdown-auto_identifiers-smart', '-o', str(out), '--toc', '--toc-depth=2',
                        '--reference-doc', str(reference_docx(td)), '--metadata', 'toc-title=目录'], check=True)
    print('docx ok', out, out.stat().st_size)


if __name__ == '__main__':
    main()
