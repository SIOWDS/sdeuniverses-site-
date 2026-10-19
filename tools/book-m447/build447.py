#!/usr/bin/env python3
"""第 447 号排版：在系列 build_book.py 之上，逐节收紧，把章末、目录末、书目末的短页并回上一页。
不改正文，只按节微调行距、段距、盒子间距，最多四档。"""
import importlib.util, io, json, re, sys
from pathlib import Path
import pypdf

S = '/mnt/skills/plugins/sde-popular-philosophy-style/scripts/build_book.py'
spec = importlib.util.spec_from_file_location('bb', S); bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
from weasyprint import CSS, HTML

D = Path('/home/claude/book447')
SRC = D / '国家发生学导论_排版稿.md'
P = dict(bb.PRESETS['current'])
md = SRC.read_text(encoding='utf-8')
meta, doc = bb.build_html(md, P, str(D / 'cover-front.jpg'), str(D / 'cover-back.jpg'))
RUN = meta.get('title')
SKIP = re.compile(r'^(国家发生学导论|第 \d+ 章.*|导论|导读|目录|作者介绍|结语.*|参考书目|后记|\d+|[ivxlc]+)$')


def levels(ed):
    lh = bb.READER['lh'] if ed == 'reader' else P['lh']
    gap = P['gap']
    return [
        '',
        f'p{{line-height:{lh*0.975:.3f};margin-bottom:{gap*0.85:.2f}em}} li{{line-height:{lh*0.975:.3f}}}',
        f'p{{line-height:{lh*0.95:.3f};margin-bottom:{gap*0.7:.2f}em}} li{{line-height:{lh*0.95:.3f}}} h3.sec{{margin-top:.9em!important}} .takeaway{{margin:1em 0 .6em!important}} .ledger{{margin-bottom:.6em!important}}',
        f'p{{line-height:{lh*0.93:.3f};margin-bottom:{gap*0.6:.2f}em;letter-spacing:-0.01em}} li{{line-height:{lh*0.93:.3f}}} h3.sec{{margin-top:.75em!important}} .takeaway{{margin:.8em 0 .5em!important}} .ledger{{margin-bottom:.5em!important}}',
        f'p{{line-height:{lh*0.91:.3f};margin-bottom:{gap*0.5:.2f}em;letter-spacing:-0.02em}} li{{line-height:{lh*0.91:.3f}}} h3.sec{{margin-top:.6em!important}} .takeaway{{margin:.7em 0 .4em!important}} .ledger{{margin-bottom:.4em!important}}',
    ]


def scope(rules, sid):
    if sid == 'toc':
        n = len(re.findall(r'line-height', rules)) and rules.count('!important')
        if not rules: return ''
        lvl = 1 + rules.count('!important') // 3
        return (f'section.toc li{{margin:{max(.04, .14 - .03*lvl):.2f}em 0!important;line-height:{1.5 - .04*lvl:.2f}!important}}'
                f' section.toc li.part{{margin-top:{max(.35,.7-.1*lvl):.2f}em!important}}')
    if sid == 'f1' and rules:
        rules += ' table{font-size:.9em!important} td,th{padding-top:.12em!important;padding-bottom:.12em!important} p{margin-bottom:.3em}'
    return re.sub(r'(^|\}\s*)([^{}]+)\{', lambda m: m.group(1) + ', '.join(f'#{sid} {s.strip()}' for s in m.group(2).split(',')) + '{', rules)


def analyse(pdf_bytes, d, order):
    r = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    han = []
    for p in r.pages:
        t = p.extract_text() or ''
        body = [l for l in t.split('\n') if l.strip() and not SKIP.match(l.strip().replace('　', ' '))]
        han.append(len(re.findall(r'[一-鿿]', ''.join(body))))
    pos = bb.anchors(d)
    starts = sorted((pos[s], s) for s in order if s in pos)
    last = {}
    for k, (pg, sid) in enumerate(starts):
        end = (starts[k + 1][0] if k + 1 < len(starts) else len(han) - 1) - 1
        if end > pg:
            last[sid] = (end, han[end])
    return han, last


def main(ed):
    css = bb.build_css(P, ed, RUN)
    css += '\nsection.toc li{margin:.07em 0} section.toc li.part{margin-top:.5em}'
    if ed == 'reader':
        css += '\nsection.toc li{margin:0!important;line-height:1.38!important} section.toc li.part{margin-top:.3em!important}'
        css += '\n#f1 h3.sec:nth-of-type(3){break-before:page}'
    order = re.findall(r'<section class="(?:chapter[^"]*|fsec[^"]*|part[^"]*)" id="([a-z]+\d*)"', doc)
    parts = set(re.findall(r'<section class="part[^"]*" id="([a-z]+\d*)"', doc))
    med = None
    lv = {}
    L = levels(ed)
    for it in range(6):
        extra = '\n'.join(scope(L[v], s) for s, v in lv.items())
        d = HTML(string=bb.PH.sub('000', doc), base_url=str(D)).render(stylesheets=[CSS(string=css + '\n' + extra)])
        han, last = analyse(d.write_pdf(), d, order)
        if med is None:
            hs = sorted(h for h in han if h > 0); med = hs[len(hs) // 2]
        thr = med * 0.45
        runts = {s: v for s, v in last.items() if v[1] < thr and s not in parts and s != 'toc'}
        print(ed, 'pass', it, 'pages', len(d.pages), 'median', med, 'runts', len(runts), sorted(runts.items(), key=lambda x: x[1][0])[:40])
        todo = [s for s in runts if lv.get(s, 0) < len(L) - 1]
        if not todo:
            break
        for s in todo:
            lv[s] = lv.get(s, 0) + 1
    extra = '\n'.join(scope(L[v], s) for s, v in lv.items())
    (D / f'tighten-{ed}.json').write_text(json.dumps(lv, ensure_ascii=False, indent=1))
    out = D / f'国家发生学导论_第447号-{ed}.pdf'
    n, pos, fol = bb.render(doc, css + '\n' + extra, str(out), P, str(D))
    print(ed, 'final pages', n, 'tightened', lv)


if __name__ == '__main__':
    for ed in sys.argv[1:] or ['print', 'reader']:
        main(ed)
