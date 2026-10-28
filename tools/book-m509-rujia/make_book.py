#!/usr/bin/env python3
"""Typeset 《儒家思想体系的六路径大解构》 as reader / print PDFs (WeasyPrint),
in the style of site vols 220/302/497/502.  usage: make_book.py reader|print|html"""
import json, re, subprocess, html, os, sys, glob
ROOT = '/home/claude/rujia'
B = ROOT + '/build'
MODE = sys.argv[1] if len(sys.argv) > 1 else 'reader'
s = json.load(open(ROOT + '/structure_v03.json'))
META = json.load(open(B + '/meta.json'))

def keyline(n):
    p = f'{ROOT}/learn/lesson_{n:02d}.json'
    if os.path.exists(p):
        try: return json.load(open(p)).get('keyline', '')
        except Exception: return ''
    return ''

def curly(t):
    out = []
    for line in t.split('\n'):
        if '"' in line:
            r = []; o = True
            for ch in line:
                if ch == '"': r.append('“' if o else '”'); o = not o
                else: r.append(ch)
            line = ''.join(r)
        out.append(line)
    return '\n'.join(out)

def md2html(md):
    p = subprocess.run(['pandoc', '-f', 'markdown-smart-auto_identifiers+east_asian_line_breaks',
                        '-t', 'html', '--wrap=none'], input=md, capture_output=True, text=True)
    if p.returncode: raise SystemExit(p.stderr)
    h = p.stdout
    h = re.sub(r'〔([^〕]{1,30})〕', r'<span class="mk">〔\1〕</span>', h)
    return h

def cn(n):
    d = '零一二三四五六七八九十'
    if n <= 10: return d[n]
    if n < 20: return '十' + (d[n - 10] if n > 10 else '')
    return d[n // 10] + '十' + (d[n % 10] if n % 10 else '')

def chapter(n):
    t = curly(open(f'{ROOT}/chapters/ch{n:02d}.md').read().strip())
    first, rest = t.split('\n', 1)
    title = re.sub(r'^#\s*', '', first).strip()
    if n == 0:
        label, name = '导言', title.split('　', 1)[1]
    else:
        m = re.match(r'第(\d+)章\s*(.*)', title)
        label, name = f'第 {n} 章', m.group(2)
    short = name.split('——')[0]
    # demote headings: ## -> h2 (section), ### -> h3
    k = [0]
    body = md2html(rest)
    def sid(m):
        k[0] += 1
        return f'<h2 id="s{n}-{k[0]}">'
    body = re.sub(r'<h2>', sid, body)
    num = '' if n == 0 else f'{n:02d}'
    kl = keyline(n)
    box = f'<div class="keybox"><div class="kl">本章要点</div><p>{html.escape(kl)}</p></div>' if kl else ''
    return (f'<section class="chapter" id="ch{n}">'
            f'<div class="bt1"></div><div class="runhead">{html.escape(short)}</div>'
            f'<div class="chnum">{num}</div><div class="chlabel">{label}</div>'
            f'<h1 class="chtitle" data-bm="{html.escape((label+"　" if n else "导言　")+name.split("——")[0])}">{html.escape(name)}</h1><div class="rule"></div>{box}'
            f'{body}</section>')

def toc():
    out = ['<section class="toc" id="toc"><h1 class="fronth">目　录</h1><ul>']
    def li(cls, href, text):
        out.append(f'<li class="{cls}"><a href="#{href}"><span class="tt">{text}</span></a></li>')
    li('t-front', 'preface', '出版说明')
    li('t-ch', 'ch0', '导言　为什么是路径，为什么还不够')
    for pi, p in enumerate(s['parts']):
        pt = re.sub(r'（约.*?）', '', p['t'])
        li('t-part', f'part{pi}', pt)
        for bi, b in enumerate(p['bians']):
            li('t-bian', f'bian{pi}-{bi}', b['t'])
            for c in b['chs']:
                n = int(re.match(r'第(\d+)章', c[0]).group(1))
                nm = c[0].split('　', 1)[1] if n != 66 else open(f'{ROOT}/chapters/ch66.md').readline().split('　', 1)[1].strip()
                nm = nm.split('——')[0]
                li('t-ch', f'ch{n}', f'<b>第 {n} 章</b>　{html.escape(nm)}')
    li('t-front', 'app1', '附录一　本书的口径、读法与核查记录')
    li('t-front', 'app2', '附录二　待核引文与判断清单')
    out.append('</ul></section>')
    return '\n'.join(out)

EMBLEM = '''<svg class="emblem" viewBox="0 0 100 100" width="26mm" height="26mm"><g fill="none" stroke="#b8913a" stroke-width="1.1">
<circle cx="50" cy="50" r="44" stroke-width=".6"/><polygon points="50,12 83,31 83,69 50,88 17,69 17,31"/>
<circle cx="50" cy="50" r="9"/></g><g fill="#b8913a"><circle cx="50" cy="12" r="2.6"/><circle cx="83" cy="31" r="2.6"/>
<circle cx="83" cy="69" r="2.6"/><circle cx="50" cy="88" r="2.6"/><circle cx="17" cy="69" r="2.6"/><circle cx="17" cy="31" r="2.6"/>
<circle cx="50" cy="50" r="3.4"/></g></svg>'''

def part_page(pi, p):
    m = re.match(r'(.)部　(.*?)（约', p['t'])
    return (f'<section class="divider part" id="part{pi}">{EMBLEM}<div class="dlabel">{m.group(1)}　部</div>'
            f'<h1 class="dtitle">{html.escape(m.group(2))}</h1><div class="drule"></div>'
            f'<p class="dlead">{html.escape(p["lead"])}</p></section>')

def bian_page(pi, bi, b):
    lab, name = b['t'].split('　', 1)
    lab = '　'.join(lab)
    items = []
    for c in b['chs']:
        n = int(re.match(r'第(\d+)章', c[0]).group(1))
        nm = c[0].split('　', 1)[1] if n != 66 else '结语：从开花到出新花'
        items.append(f'<li><span class="bn">第 {n} 章</span>{html.escape(nm.split("——")[0])}</li>')
    return (f'<section class="divider bian" id="bian{pi}-{bi}"><div class="dlabel">{lab}</div>'
            f'<h1 class="dtitle">{html.escape(name)}</h1><div class="drule"></div><ul class="blist">{"".join(items)}</ul></section>')

def daihe():
    out = ['<section class="appendix" id="app2"><div class="bt1"></div><div class="runhead">附录二　待核引文与判断清单</div>',
           '<div class="chlabel">附录二</div><h1 class="chtitle">待核引文与判断清单</h1><div class="rule"></div>',
           '<p>引文与事实核查之后仍未能对照原书核实的句子，按章列出，供读者与下一版补核。正文中这些地方都标有〔待核〕或其变体；〔本书读法，待检〕是本书自己的判断，怎样才算错，写在各章“可错条件”里，不列于此。</p>']
    total = 0
    for n in range(0, 67):
        t = curly(open(f'{ROOT}/chapters/ch{n:02d}.md').read())
        hits = []
        for para in t.split('\n'):
            for m in re.finditer(r'[^。！？\n]*〔[^〕]*待核[^〕]*〕', para):
                x = m.group(0).strip().lstrip('#').strip().replace('**', '')
                x = x.strip('|').replace(' | ', '；').replace('|', '；').strip()
                x = x.lstrip('-').strip().lstrip('”’，、：；）)').strip()
                if x and x[-120:] not in hits: hits.append(x[-120:])
        if hits:
            total += len(hits)
            tl = open(f'{ROOT}/chapters/ch{n:02d}.md').readline().lstrip('#').strip()
            tl = tl.split('——')[0]
            out.append(f'<h3>{html.escape(tl)}（{len(hits)}条）</h3><ol class="dh">')
            for h in hits:
                out.append('<li>' + re.sub(r'〔([^〕]{1,30})〕', r'<span class="mk">〔\1〕</span>', html.escape(h)) + '</li>')
            out.append('</ol>')
    out.append('</section>')
    META['daiheCount'] = total
    return '\n'.join(out)

def mdsec(path, sid, label, title, run):
    t = curly(open(path).read().strip())
    t = re.sub(r'^#\s+.*\n', '', t, 1)
    return (f'<section class="appendix" id="{sid}"><div class="bt1"></div><div class="runhead">{run}</div>'
            f'<div class="chlabel">{label}</div><h1 class="chtitle">{title}</h1><div class="rule"></div>{md2html(t)}</section>')

def front():
    M = META
    rows = [('书名', f'《{M["title"]}》'), ('副题', M['subtitle']), ('英文书名', M['titleEn']), ('著者', M['author']),
            ('出版', '德麦国际出版社（Demai International Press）'), ('编号', f'德麦国际专著第 {M["no"]} 号'),
            ('ISBN', M['isbn']), ('定价', M['price']), ('开本', M['format_' + MODE]), ('字数', M['words']),
            ('版次', M['edition'])]
    tr = ''.join(f'<tr><th>{a}</th><td>{html.escape(b)}</td></tr>' for a, b in rows)
    notes = ''.join(f'<p>{x}</p>' for x in M['imprintNotes'])
    pre = md2html(curly(open(B + '/preface.md').read()))
    return f'''
<section class="cover"><img src="{B}/cover.jpg"/></section>
<section class="blank"></section>
<section class="halftitle"><div class="ht-series">德麦国际专著 · 第 {M["no"]} 号</div>
<div class="ht-pre">儒家思想体系的</div><div class="ht-title">六路径大解构</div>
<div class="ht-sub">从1到N的发展之道<br/>到0到1的典范发生之道</div><div class="ht-rule"></div>
<div class="ht-author">WDS博士　著</div>
<div class="ht-pub"><b>德麦国际出版社</b><br/><span>Demai International Press</span></div></section>
<section class="imprint"><h2 class="imh">出　版　信　息</h2><table>{tr}</table><div class="imnotes">{notes}<p class="rights">版权所有　侵权必究</p></div></section>
<section class="epigraph"><p class="ep">物有本末，事有终始，<br/>知所先后，则近道矣。</p><p class="ep-src">——《大学》</p></section>
<section class="preface" id="preface"><div class="runhead">出版说明</div><h1 class="fronth">出版说明</h1><div class="rule"></div>{pre}</section>
'''

def build():
    parts = [front(), toc(), chapter(0)]
    for pi, p in enumerate(s['parts']):
        parts.append(part_page(pi, p))
        for bi, b in enumerate(p['bians']):
            parts.append(bian_page(pi, bi, b))
            for c in b['chs']:
                parts.append(chapter(int(re.match(r'第(\d+)章', c[0]).group(1))))
    parts.append(mdsec(B + '/appendix1.md', 'app1', '附录一', '本书的口径、读法与核查记录', '附录一　本书的口径、读法与核查记录'))
    parts.append(daihe())
    parts.append(f'<section class="cover back"><img src="{B}/backcover.jpg"/></section>')
    css = open(B + '/book.css').read() + '\n' + open(B + f'/{MODE}.css').read()
    doc = (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{META["title"]}</title>'
           f'<meta name="author" content="{META["author"]}"><style>{css}</style></head><body>' + '\n'.join(parts) + '</body></html>')
    open(f'{B}/book_{MODE}.html', 'w').write(doc)
    json.dump(META, open(B + '/meta_out.json', 'w'), ensure_ascii=False, indent=1)
    return doc

if __name__ == '__main__':
    doc = build()
    if MODE in ('reader', 'print'):
        from weasyprint import HTML
        out = f'{B}/{META["slug"]}-{MODE}.pdf'
        HTML(string=doc, base_url=B).write_pdf(out)
        print('wrote', out)
