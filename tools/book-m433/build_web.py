#!/usr/bin/env python3
"""第 433 号《情绪价值发生学》：Markdown 全稿 → 全文网页 text.html，PDF 书签 → 翻页器目录 toc-reader.json。
用法：python3 tools/book-m433/build_web.py --ms book.md --reader reader.pdf --out OUTDIR
样式取自第 425 号全文网页（同一套类名）。
"""
import argparse, html, json, re
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / 'public'
NO, V, SLUG = 433, '20261019a', 'qingxu-jiazhi-fashengxue'
HAN = re.compile(r'[一-鿿]')


def inline(s):
    s = re.sub(r'(?<=[一-鿿　-〿＀-￯]) (?=[A-Za-z0-9$])|(?<=[A-Za-z0-9%$.)]) (?=[一-鿿　-〿＀-￯])', ' ', s)
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', s)
    return s


def table_html(rows):
    cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
    head, body = cells[0], cells[1:]
    cls = 'tb' + (' w5' if len(head) >= 5 else '')
    h = ['<div class="tw"><table class="%s"><thead><tr>' % cls] + ['<th>%s</th>' % inline(c) for c in head] + ['</tr></thead><tbody>']
    for r in body:
        h.append('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)


def render(lines, bib=False):
    out, i, ledger = [], 0, []
    L = [l.rstrip() for l in lines]
    while i < len(L):
        l = L[i]
        if not l.strip():
            i += 1; continue
        if l.startswith('|'):
            j = i
            while j < len(L) and L[j].startswith('|'): j += 1
            out.append(table_html(L[i:j])); i = j; continue
        if l.startswith('### '):
            t = l[4:].strip()
            if t.startswith('◆'):
                out.append('<h3 class="sec"><span class="dia">◆</span>%s</h3>' % inline(t.lstrip('◆ ').strip()))
            else:
                out.append('<h3 class="sec">%s</h3>' % inline(t))
            i += 1; continue
        if l.startswith('#### '):
            out.append('<h3 class="subhead">%s</h3>' % inline(l[5:])); i += 1; continue
        if l.startswith('【带走的话】'):
            out.append('<div class="takeaway"><span class="lab">带走的话</span><p>%s</p></div>' % inline(l[6:])); i += 1; continue
        if l.startswith('【小账】'):
            t = l[4:]
            parts = [p for p in re.split(r'(?<=[。？])(?=[二三四五六七八九十]，)', t) if p.strip()]
            out.append('<div class="ledger"><span class="lab">小　账</span>%s</div><div class="endmark">◆</div>' % ''.join('<p>%s</p>' % inline(p) for p in parts)); i += 1; continue
        if l.startswith('【想一想】'):
            out.append('<div class="wonder"><span class="lab">想一想</span><p>%s</p></div>' % inline(l[5:])); i += 1; continue
        if l.startswith('> '):
            j = i; q = []
            while j < len(L) and L[j].startswith('>'):
                q.append(L[j][1:].strip()); j += 1
            q = [x for x in q if x]
            if q and q[0].startswith('**判词**') or (len(q) == 1 and re.fullmatch(r'\*\*.+\*\*', q[0])):
                out.append('<blockquote class="verdict">%s</blockquote>' % ''.join('<p>%s</p>' % inline(x) for x in q))
            else:
                out.append('<blockquote class="verdict">%s</blockquote>' % ''.join('<p>%s</p>' % inline(x) for x in q))
            i = j; continue
        if re.fullmatch(r'〔[^〔〕]*〕', l.strip()):
            out.append('<p class="srcnote">%s</p>' % inline(l.strip())); i += 1; continue
        if bib and re.match(r'^\d+[.、]', l):
            out.append('<p class="bib">%s</p>' % inline(l)); i += 1; continue
        # 〔待核〕 on its own line right after a bibliography entry
        if l.startswith('- '):
            j = i; items = []
            while j < len(L) and L[j].startswith('- '):
                items.append(L[j][2:]); j += 1
            out.append('<ul class="ls">%s</ul>' % ''.join('<li>%s</li>' % inline(x) for x in items)); i = j; continue
        out.append('<p%s>%s</p>' % (' class="bib"' if bib else '', inline(l)))
        i += 1
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ms', type=Path, required=True); ap.add_argument('--reader', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    raw = a.ms.read_text(encoding='utf-8')
    fm_end = raw.index('\n---\n', 4)
    meta = {}
    stm = []
    for ln in raw[4:fm_end].splitlines():
        k, _, v = ln.partition(':')
        v = v.strip()
        if k == 'statement': stm.append(v)
        else: meta[k] = v
    body = raw[fm_end + 5:]
    han = len(HAN.findall(body))
    # split into top-level blocks
    blocks = re.split(r'\n(?=# )', '\n' + body)
    secs = []  # (kind, id, title, html)
    n = 0
    def nid():
        nonlocal n; n += 1; return 's%d' % n
    # 出版信息
    rows = [('书名', '《%s——%s》' % (meta['title'], meta['subtitle'])), ('著者', meta['author']), ('执笔', meta['executor']),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %s 号' % meta['series_no']),
            ('ISBN', meta['isbn']), ('定价', meta['price']), ('开本', '170 mm × 240 mm（16 开）'), ('字数', meta['words']), ('版次', meta['edition']), ('完稿', meta['finished'])]
    cp = '<div class="cp-title">出版信息</div><table class="cp">%s</table><div class="cp-notes">%s<p>%s</p></div>' % (
        ''.join('<tr><th>%s</th><td>%s</td></tr>' % (k, inline(v)) for k, v in rows), ''.join('<p>%s</p>' % inline(s) for s in stm), meta.get('copyright', ''))
    secs.append(('cp', nid(), '出版信息', cp))
    cur_part = None
    chap_no = 0
    for blk in blocks:
        blk = blk.strip('\n')
        if not blk: continue
        head, _, rest = blk.partition('\n')
        assert head.startswith('# '), head[:30]
        title = head[2:].strip()
        if re.match(r'第.{1,3}编　', title):
            lines = rest.split('\n')
            # 编序段 -> bianxu; 章 blocks are split by '## 第'
            chap_split = re.split(r'\n(?=## 第 ?\d+ ?章　)', '\n' + rest)
            intro = [l[4:] if l.startswith('【编序】') else l for l in chap_split[0].split('\n') if l.strip()]
            intro = [re.sub(r'^【编序】', '', l) for l in intro]
            m = re.match(r'(第.{1,3}编)　(.*)', title)
            lab = ' '.join(m.group(1))
            pid = nid()
            secs.append(('part', pid, title, '<div class="part-label">%s</div><h1 class="part-title">%s</h1><div class="rule"></div><div class="daoyu">导　语</div><div class="part-intro">%s</div>' % (
                lab, inline(m.group(2)), ''.join('<p class="bianxu">%s</p>' % inline(x) for x in intro))))
            for cb in chap_split[1:]:
                cb = cb.strip('\n')
                ch, _, cbody = cb.partition('\n')
                mm = re.match(r'## 第 ?(\d+) ?章　(.*)', ch)
                no = int(mm.group(1))
                inner = '<div class="chapnum">%02d</div><div class="chap-label">第 %d 章</div><h2 class="chap-title">%s</h2><div class="rule"></div>\n%s' % (no, no, inline(mm.group(2)), render(cbody.split('\n')))
                secs.append(('chapter', nid(), '第 %d 章　%s' % (no, mm.group(2)), inner))
                chap_no += 1
        elif title.startswith('附录'):
            sub = re.split(r'\n(?=## )', '\n' + rest)
            sid = nid()
            secs.append(('back', sid, '附录', '<h1 class="fs-title">附录</h1><div class="rule"></div>\n' + render(sub[0].split('\n'))))
            for sb in sub[1:]:
                sh, _, sbody = sb.strip('\n').partition('\n')
                secs.append(('back', nid(), sh[3:].strip(), '<h2 class="fs-title appx">%s</h2><div class="rule"></div>\n%s' % (inline(sh[3:].strip()), render(sbody.split('\n')))))
        else:
            kind = 'back' if title.startswith(('结语', '后记', '参考书目')) else 'front'
            name, _, sub = title.partition('　')
            h = '<h1 class="fs-title">%s</h1>' % inline(name) + ('<p class="fs-sub">%s</p>' % inline(sub) if sub else '') + '<div class="rule"></div>\n' + render(rest.split('\n'), bib=title.startswith('参考书目'))
            secs.append((kind, nid(), title, h))
    # css from 425
    src = (SITE / 'books/m/425/text/index.html').read_text(encoding='utf-8')
    style = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
    toc = []
    for kind, sid, title, _ in secs:
        if kind == 'cp': continue
        cls = {'part': 'p', 'chapter': 'c'}.get(kind, 'f')
        toc.append('<li class="%s"><a href="#%s">%s</a></li>' % (cls, sid, inline(title)))
    sec_html = []
    for kind, sid, title, h in secs:
        cls = {'part': 'part', 'chapter': 'chapter'}.get(kind, 'front-sec' if kind in ('front', 'cp') else 'backm')
        sec_html.append('<%s class="%s" id="%s">%s</%s>' % ('section', cls, sid, h, 'section'))
    T, SUB = meta['title'], meta['subtitle']
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全文网页阅读 · {T} · 德麦国际专著第 {NO} 号</title>
<meta name="description" content="《{T}——{SUB}》全文网页版。{meta['author']} 著，德麦国际专著第 {NO} 号，约 {han/10000:.0f} 万汉字。">
<meta name="tier" content="L0"><link rel="canonical" href="https://sdeuniverses.com/books/m/{NO}/text/">
<style>{style}</style></head><body><div id="prog"></div>
<div class="bar"><a href="/books/m/{NO}/">← 书籍详情</a><a href="/books/m/{NO}/read.html">在线翻页</a><a href="/books/m/{NO}/{SLUG}-print.pdf?v={V}" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>
<div class="wrap">
<div class="hero"><img src="/books/m/{NO}/cover.jpg?v={V}" alt="封面"><h1>{T}</h1><p>{SUB}</p>
<p style="color:var(--dim);margin-top:.5rem">{meta['author']} 著 · 德麦国际专著第 {NO} 号 · ISBN {meta['isbn']} · 约 {han/10000:.1f} 万汉字</p></div>
<details class="toc" open><summary>目录（出版信息 · 作者介绍 · 前言 · 导读 · 导论 · 第一编至第八编 · 结语 · 后记 · 参考书目 · 附录）</summary><ul>{''.join(toc)}</ul></details>
{chr(10).join(sec_html)}
<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{NO}/">书籍详情</a> · <a href="/books/m/{NO}/read.html">在线翻页</a></div>
</div>
<script>
(function(){{var p=document.getElementById('prog');addEventListener('scroll',function(){{var h=document.documentElement;p.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}},{{passive:true}});
var sizes=[16,17,18,20,22],k=2;try{{var s=localStorage.getItem('bk{NO}-fs');if(s)k=+s;var d=localStorage.getItem('bk{NO}-dark');if(d==='1')document.documentElement.classList.add('dark');}}catch(e){{}}
function ap(){{document.body.style.fontSize=sizes[k]+'px';}}ap();
document.getElementById('fs').onclick=function(){{k=(k+1)%sizes.length;ap();try{{localStorage.setItem('bk{NO}-fs',k)}}catch(e){{}}}};
document.getElementById('th').onclick=function(){{var on=document.documentElement.classList.toggle('dark');try{{localStorage.setItem('bk{NO}-dark',on?'1':'0')}}catch(e){{}}}};}})();
</script></body></html>"""
    (a.out / 'text.html').write_text(page, encoding='utf-8')
    # reader toc from PDF bookmarks
    import pymupdf
    d = pymupdf.open(str(a.reader))
    tocs = d.get_toc()
    skip = {'目录'}
    first = next(p for t, p in ((x[1], x[2]) for x in tocs) if t.startswith('前言'))
    flip = []
    for lvl, t, pg in tocs:
        if t in skip: continue
        printed = pg - first + 1
        flip.append({'t': t.replace('　', ' '), 'p': str(printed) if printed >= 1 else '', 'g': pg, 'l': 1 if (lvl == 1) else 2})
    # chapters are not bookmarked as level 2 in PDF? keep all entries as given
    (a.out / 'toc-reader.json').write_text(json.dumps({'toc': flip, 'offset': first}, ensure_ascii=False), encoding='utf-8')
    print('web ok', len(secs), 'sections; han', han, '; toc', len(flip), 'offset', first)
    print(json.dumps(meta['title']), chap_no, 'chapters')


if __name__ == '__main__':
    main()
