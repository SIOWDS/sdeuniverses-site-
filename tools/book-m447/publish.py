#!/usr/bin/env python3
"""第 447 号《国家发生学导论》上站：PDF、封面、全文网页、翻页器、详情页、书目、站点地图、/today/ 新书卡。
用法：python3 tools/book-m447/publish.py --src /home/claude/book447
"""
import argparse, datetime, html, json, re, shutil, subprocess
from pathlib import Path
import pypdf

SITE = Path(__file__).resolve().parents[2] / 'public'
NO = 447; V = '20261019b'; SLUG = 'guojia-fashengxue'
T = '国家发生学导论'
SUB = '法律、政治、经济三种属性怎样纠缠出一个「我们」'
ISBN = '979-8-90690-959-6'
LINE = '国家不是被发现的领土，也不是签下的约；它是法律、政治、经济三股线拧出来的一个「我们」。'
DESC = '两千多年的国家学说，几乎都在找国家「本来是什么」，于是每家都抓住一种属性当成国家本身。本书改问国家怎样发生：法律是国家的主体属性，是国家的「我」，一个集体的「我们」；政治是客体属性，经济是互动属性。三属性轮流侧重，分布、场、美九格织出一个国家的样子；固化、顶替、侧重卡死是三种病，跃迁、内卷、轮回、耗散是四种结局。导论、六编、结语，约 28 万汉字。'


def pages_of(pdf):
    return len(pypdf.PdfReader(str(pdf)).pages)


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return s


def render_text(md, han):
    style = re.search(r'<style>(.*?)</style>',
                      (SITE / 'books/m/302/text/index.html').read_text(encoding='utf-8'), re.S).group(1)
    style += '\ntable.tb{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.88rem}table.tb th,table.tb td{border:1px solid var(--line);padding:.35rem .5rem;text-align:left}table.tb th{background:var(--soft);color:var(--navy)}\n.bianxu{color:var(--dim)}\n'
    lines = md.split('\n')
    i = 0
    if lines[0].strip() == '---':
        i = 1
        while lines[i].strip() != '---':
            i += 1
        i += 1
    out, toc, opened = [], [], None
    n = 0
    def close():
        nonlocal opened
        if opened:
            out.append('</section>'); opened = None
    tbl = []
    def flush_tbl():
        nonlocal tbl
        if not tbl: return
        rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in tbl if not re.match(r'^\|?\s*:?-{2,}', r.strip())]
        h = '<table class="tb">'
        for k, r in enumerate(rows):
            tag = 'th' if k == 0 else 'td'
            h += '<tr>' + ''.join('<%s>%s</%s>' % (tag, inline(c), tag) for c in r) + '</tr>'
        out.append(h + '</table>'); tbl = []
    for raw in lines[i:]:
        t = raw.strip()
        if t.startswith('|'):
            tbl.append(t); continue
        flush_tbl()
        if not t: continue
        m = re.match(r'^# (.*)$', t)
        if m:
            close(); n += 1; sid = 's%d' % n; title = m.group(1)
            mp = re.match(r'^(第[一二三四五六七八九十]+编)[\s　]+(.*)$', title)
            if mp:
                toc.append(('p', sid, title))
                out.append('<section class="part" id="%s"><div class="part-label">%s</div><div class="part-title">%s</div><div class="rule"></div><div class="part-intro">' % (sid, mp.group(1), html.escape(mp.group(2))))
                opened = 'part-open'
            else:
                toc.append(('f', sid, title))
                out.append('<section class="front-sec" id="%s"><div class="fs-title">%s</div><div class="rule"></div>' % (sid, html.escape(title)))
                opened = 'f'
            continue
        if opened == 'part-open' and not t.startswith('【编序】') and not t.startswith('#'):
            pass
        m = re.match(r'^## (第 \d+ 章)[\s　]+(.*)$', t)
        if m:
            if opened == 'part-open': out.append('</div>'); 
            close(); n += 1; sid = 's%d' % n
            toc.append(('c', sid, m.group(1) + '　' + m.group(2)))
            out.append('<section class="chapter" id="%s"><div class="chap-label">%s</div><h2>%s</h2><div class="rule"></div>' % (sid, m.group(1), html.escape(m.group(2))))
            opened = 'c'; continue
        m = re.match(r'^##+ (.*)$', t)
        if m:
            out.append('<h3>%s</h3>' % inline(m.group(1))); continue
        m = re.match(r'^### ◆ (.*)$', t)
        if m:
            out.append('<h3><span class="dia">◆</span> %s</h3>' % inline(m.group(1))); continue
        if t.startswith('【编序】'):
            out.append('<p class="bianxu">%s</p>' % inline(t[4:])); continue
        if t.startswith('>'):
            out.append('<blockquote><p>%s</p></blockquote>' % inline(t.lstrip('> ').strip())); continue
        if re.match(r'^[-*]\s+', t):
            out.append('<p>%s</p>' % inline(re.sub(r'^[-*]\s+', '', t))); continue
        if opened == 'part-open':
            out.append('</div>'); opened = 'part'
        out.append('<p>%s</p>' % inline(t))
    flush_tbl(); 
    if opened == 'part-open': out.append('</div>')
    close()
    tocs = ''.join('<li class="%s"><a href="#%s">%s</a></li>' % (c, s, html.escape(x)) for c, s, x in toc)
    body = '\n'.join(out)
    # 编序后的 part-intro 须在下一个 # 前闭合：简化——part-intro div 已在遇到章或下一块时闭合
    head = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全文网页阅读 · {T} · 德麦国际专著第 {NO} 号</title>
<meta name="description" content="《{T}——{SUB}》全文网页版。王德生 著，德麦国际专著第 {NO} 号，约 {han/10000:.0f} 万汉字。">
<meta name="tier" content="L0"><link rel="canonical" href="https://sdeuniverses.com/books/m/{NO}/text/">
<style>{style}</style></head><body><div id="prog"></div>
<div class="bar"><a href="/books/m/{NO}/">← 书籍详情</a><a href="/books/m/{NO}/read.html">在线翻页</a><a href="/books/m/{NO}/{SLUG}-print.pdf?v={V}" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>
<div class="wrap">
<div class="hero"><img src="/books/m/{NO}/cover.jpg?v={V}" alt="封面"><h1>{T}</h1><p>{SUB}</p>
<p style="color:var(--dim);margin-top:.5rem">王德生 著 · 德麦国际专著第 {NO} 号 · ISBN {ISBN} · 约 {han/10000:.0f} 万汉字</p></div>
<details class="toc" open><summary>目录（作者介绍 · 导读 · 导论 · 六编五十章 · 结语 · 参考书目 · 后记）</summary><ul>{tocs}</ul></details>
"""
    tail = f"""<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{NO}/">书籍详情</a> · <a href="/books/m/220/">《我的三个宝贝》（第 220 号）</a></div>
</div>
<script>
(function(){{var p=document.getElementById('prog');addEventListener('scroll',function(){{var h=document.documentElement;p.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}},{{passive:true}});
var sizes=[16,17,18,20,22],k=2;try{{var s=localStorage.getItem('bk{NO}-fs');if(s)k=+s;var d=localStorage.getItem('bk{NO}-dark');if(d==='1')document.documentElement.classList.add('dark');}}catch(e){{}}
function ap(){{document.body.style.fontSize=sizes[k]+'px';}}ap();
document.getElementById('fs').onclick=function(){{k=(k+1)%sizes.length;ap();try{{localStorage.setItem('bk{NO}-fs',k)}}catch(e){{}}}};
document.getElementById('th').onclick=function(){{var on=document.documentElement.classList.toggle('dark');try{{localStorage.setItem('bk{NO}-dark',on?'1':'0')}}catch(e){{}}}};}})();
</script></body></html>"""
    return head + body + tail


def toc_json(pdf, offset):
    r = pypdf.PdfReader(str(pdf)); res = []
    def walk(o, l):
        for x in o:
            if isinstance(x, list): walk(x, l + 1)
            else:
                g = r.get_destination_page_number(x) + 1; pr = g - offset + 1
                res.append({'t': re.sub(r'[\s　]+', ' ', x.title, count=1), 'p': str(pr) if pr > 0 else '', 'g': g, 'l': 1 if l == 0 else 2})
    walk(r.outline, 0)
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True)
    A = ap.parse_args(); b = A.src
    d = SITE / 'books' / 'm' / str(NO)
    assert not (d / 'index.html').exists(), f'{NO} 号目录已存在'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    shutil.copy(b / '国家发生学导论_第447号-print.pdf', d / f'{SLUG}-print.pdf')
    shutil.copy(b / '国家发生学导论_第447号-reader.pdf', d / f'{SLUG}-reader.pdf')
    shutil.copy(b / 'cover-front.jpg', d / 'cover.jpg'); shutil.copy(b / 'cover-back.jpg', d / 'backcover.jpg')
    md = (b / '国家发生学导论_排版稿.md').read_text(encoding='utf-8')
    han = len(re.findall(r'[一-鿿]', md))
    (d / 'text' / 'index.html').write_text(render_text(md, han), encoding='utf-8')
    offset = 5
    toc = toc_json(d / f'{SLUG}-reader.pdf', offset)
    tpl = (SITE / 'books' / 'm' / '259' / 'read.html').read_text()
    rep = [('友好阅读 · 在线翻页 · 谈尼采视角主义的错误 | SDE Universes', f'友好阅读 · 在线翻页 · {T} | SDE Universes'),
           ('《谈尼采视角主义的错误》在线翻页阅读', f'《{T}》在线翻页阅读'),
           ('https://sdeuniverses.com/books/m/259/read.html', f'https://sdeuniverses.com/books/m/{NO}/read.html'),
           ('<span class="ttl">谈尼采视角主义的错误</span><span class="sub hideS">视角是选出来的，还是长出来的</span>', f'<span class="ttl">{T}</span><span class="sub hideS">{SUB}</span>'),
           ('<a href="/books/m/259/"', f'<a href="/books/m/{NO}/"'),
           ("title: '谈尼采视角主义的错误',", f"title: '{T}',"),
           ("msg('正在载入《谈尼采视角主义的错误》…');", f"msg('正在载入《{T}》…');")]
    for a, c in rep:
        assert a in tpl, a[:40]; tpl = tpl.replace(a, c)
    cfg = {'pdf': f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': offset}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>', lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>', lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc, ensure_ascii=False), tpl, flags=re.S)
    assert 'm/259' not in tpl and '尼采' not in tpl
    (d / 'read.html').write_text(tpl)
    pages = pages_of(d / f'{SLUG}-print.pdf')
    det = (Path(__file__).parent / 'detail.html').read_text()
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    cat_p = SITE / 'books' / 'catalog.json'; data = json.loads(cat_p.read_text()); books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books)
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='core', description=DESC,
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$25.00', priceUsd=25, currency='USD', priceLabel='US$25.00', edition='2026年10月第1版',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''))
    books.insert(0, entry); data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t)
    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    i = h.index('★ 新书 · 德麦国际专著第'); a0 = h.rindex('<a href="/books/m/', 0, i)
    card = ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · US$ 25.00</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$ 25.00</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">国家发生学导论：法律、政治、经济怎样纠缠出一个「我们」</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">An Introduction to the Genesis of the State</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">王德生著。不问国家是什么，问国家怎样发生：法律是国家的主体属性，是国家的「我」；政治是客体属性，经济是互动属性。拆八家旧答案，立九格，诊三种病与四种结局。</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">By Wang Desheng. Not what the state is, but how it happens: law as the subject attribute of the state, politics as its object attribute, economy as its interaction attribute.</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(han, ','), pages))
    tp.write_text(h[:a0] + card + h[a0:])
    print('published', d, 'pages', pages, 'han', han, 'toc', len(toc))


if __name__ == '__main__':
    main()
