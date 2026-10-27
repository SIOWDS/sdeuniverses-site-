"""从阅读版 PDF 的书签生成翻页器目录：python3 make_toc.py reader.pdf out.json [offset]"""
import json, sys, pymupdf
pdf, out = sys.argv[1], sys.argv[2]
off = int(sys.argv[3]) if len(sys.argv) > 3 else 6
toc = []
for lv, t, g in pymupdf.open(pdf).get_toc():
    if t in ('目录',):
        continue
    t = t.replace('　', ' ')
    toc.append({'t': t, 'p': str(g - off + 1) if g >= off else '', 'g': g, 'l': 1 if lv == 1 else 2})
json.dump({'toc': toc, 'offset': off}, open(out, 'w'), ensure_ascii=False)
print(len(toc), toc[:3], toc[-1])
