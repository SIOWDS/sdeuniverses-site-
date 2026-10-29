#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「专著母题」栏目生成器（2026-10-29）

每部专著一张约 2000 字的母题卡，供 SDE 二阶碰撞与形式归纳快速出大纲。
  源稿：content/motifs/{号}.md（固定七节格式，见 content/motifs/README.md）
  产出：public/motifs/index.html        总表（号、书名、作者、题型、一句母题；可筛选）
        public/motifs/{号}/index.html   单书母题卡
        public/motifs/motifs.json       机读总表（研究智能体先读这个）
        public/motifs/all.md            全部母题卡合订（纯文本）
书目信息一律取自 public/books/catalog.json。新书上站后：写好 content/motifs/{号}.md，再跑本脚本。
用法：python3 tools/build_motifs.py
"""
import os, re, json, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
SRC = os.path.join(ROOT, 'content', 'motifs')
OUT = os.path.join(PUB, 'motifs')
E = html.escape

cat = json.load(open(os.path.join(PUB, 'books', 'catalog.json'), encoding='utf-8'))
CATS = cat['categories']
BOOKS = {b['number']: b for b in cat['books'] if b.get('number') is not None}

META_KEYS = {'副题': 'subtitle', '作者': 'author', '题域': 'domain', '题型': 'qtype', '母题': 'motif'}

def parse(path):
    lines = open(path, encoding='utf-8').read().strip().split('\n')
    card = {'sections': []}
    m = re.match(r'#\s*第\s*(\d+)\s*号《(.+?)》', lines[0])
    card['title'] = m.group(2) if m else ''
    sec = None
    for ln in lines[1:]:
        if sec is None:
            mm = re.match(r'^-\s*(副题|作者|题域|题型|母题)[:：]\s*(.*)$', ln)
            if mm:
                card[META_KEYS[mm.group(1)]] = mm.group(2).strip(); continue
        hm = re.match(r'^##\s+(.+)$', ln)
        if hm:
            sec = {'h': hm.group(1).strip(), 'lines': []}; card['sections'].append(sec); continue
        if sec is not None: sec['lines'].append(ln)
    q = card.get('qtype', '')
    card['q'] = 'What' if 'What' in q else 'How' if 'How' in q else 'Why' if 'Why' in q else ''
    return card

def inline(s):
    s = E(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'第\s?(\d{1,3})\s?号', lambda m: f'<a href="/motifs/{m.group(1)}/">第{m.group(1)}号</a>' if int(m.group(1)) in BOOKS else m.group(0), s)
    return s

def render_lines(lines):
    out, para, lst = [], [], []
    def flush_p():
        if para: out.append('<p>' + inline(''.join(para)) + '</p>'); para.clear()
    def flush_l():
        if lst:
            out.append('<ul>' + ''.join(lst) + '</ul>'); lst.clear()
    for ln in lines:
        s = ln.rstrip()
        if not s.strip():
            flush_p(); continue
        lm = re.match(r'^(\s*)[-*]\s+(.*)$', s)
        if lm:
            flush_p()
            cls = ' class="sub"' if len(lm.group(1)) >= 2 else ''
            lst.append(f'<li{cls}>' + inline(lm.group(2)) + '</li>'); continue
        flush_l(); para.append(s.strip())
    flush_p(); flush_l()
    return '\n'.join(out)

CSS = """*{box-sizing:border-box}
:root{--paper:#F4EEE1;--paper2:#EAE0C8;--ink:#272116;--muted:#73664F;--acc:#7A3E1D;--acc2:#5A2B12;--line:rgba(122,62,29,.22);--card:#FBF7EE}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:'Noto Serif SC','Songti SC',Georgia,serif;line-height:1.85}
.zh-only,.en-only{}body.zh .en-only,body.en .zh-only{display:none}
a{color:var(--acc)}
header{position:sticky;top:0;z-index:10;background:rgba(244,238,225,.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.nav{max-width:1160px;margin:auto;padding:.75rem 16px;display:flex;align-items:center;gap:1.1rem;flex-wrap:wrap}
.brand{margin-right:auto;color:var(--acc2);text-decoration:none;font-weight:600;letter-spacing:.08em}
.nav>a:not(.brand){color:var(--muted);text-decoration:none;font-size:.88rem}.nav>a:hover{color:var(--acc)}
.hero{padding:clamp(3rem,8vw,6rem) 16px clamp(2rem,5vw,3.5rem);border-bottom:1px solid var(--line);background:radial-gradient(circle at 85% 20%,rgba(122,62,29,.10),transparent 32%),linear-gradient(135deg,var(--paper),var(--paper2))}
.wrap{max-width:1060px;margin:auto}
.eyebrow{font-size:.72rem;letter-spacing:.32em;color:var(--acc);margin:0 0 .9rem}
h1{margin:0;font-size:clamp(2.4rem,7vw,4.6rem);font-weight:600;letter-spacing:.08em;line-height:1.15}
.lead{max-width:44em;color:var(--muted);font-size:clamp(.98rem,2.1vw,1.12rem);margin:1.2rem 0 0}
.stats{display:flex;flex-wrap:wrap;gap:.6rem;margin-top:1.4rem}
.stats span{border:1px solid var(--line);background:rgba(255,255,255,.4);padding:.2rem .7rem;border-radius:999px;font-size:.85rem;color:var(--muted)}
.tools{position:sticky;top:52px;z-index:5;background:var(--paper);border-bottom:1px solid var(--line);padding:.8rem 16px}
.tools .wrap{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center}
.tools input{flex:1 1 260px;min-width:0;padding:.55rem .8rem;border:1px solid var(--line);border-radius:4px;background:var(--card);font:inherit;color:var(--ink)}
.tools select{padding:.5rem .6rem;border:1px solid var(--line);border-radius:4px;background:var(--card);font:inherit;color:var(--ink);max-width:100%}
.count{font-size:.85rem;color:var(--muted)}
.list{padding:1.4rem 16px 4rem}
.row{display:grid;grid-template-columns:4.2rem 1fr;gap:.2rem 1rem;padding:1rem 0;border-bottom:1px solid var(--line);text-decoration:none;color:inherit}
.row:hover .t{color:var(--acc)}
.no{font-size:.82rem;color:var(--muted);padding-top:.25rem}
.t{font-weight:600;font-size:1.06rem}
.au{font-weight:400;font-size:.84rem;color:var(--muted);margin-left:.5rem}
.mo{grid-column:2;color:var(--ink);font-size:.95rem}
.tags{grid-column:2;display:flex;flex-wrap:wrap;gap:.35rem}
.tags i{font-style:normal;font-size:.74rem;color:var(--acc);border:1px solid var(--line);border-radius:3px;padding:0 .4rem}
.row.pending .mo{color:var(--muted)}
article{max-width:780px;margin:auto;padding:2.2rem 16px 4rem}
.meta{display:grid;grid-template-columns:auto 1fr;gap:.25rem 1rem;font-size:.92rem;margin:1.4rem 0;padding:1rem 1.2rem;background:var(--card);border:1px solid var(--line);border-radius:4px}
.meta dt{color:var(--muted)}.meta dd{margin:0}
.motif{font-size:clamp(1.12rem,2.6vw,1.32rem);font-weight:600;line-height:1.7;border-left:4px solid var(--acc);padding:.3rem 0 .3rem 1rem;margin:1.6rem 0}
article h2{font-size:1.18rem;margin:2.2rem 0 .6rem;color:var(--acc2)}
article p{margin:.6rem 0}
article ul{padding-left:1.2rem}article li{margin:.35rem 0}article li.sub{margin-left:1.2rem;list-style:circle}
.pager{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin-top:3rem;padding-top:1.2rem;border-top:1px solid var(--line);font-size:.92rem}
.links{display:flex;flex-wrap:wrap;gap:.8rem;font-size:.9rem;margin-top:.4rem}
footer{border-top:1px solid var(--line);padding:1.6rem 16px;text-align:center;color:var(--muted);font-size:.85rem}
footer a{color:var(--muted)}
@media (max-width:560px){.row{grid-template-columns:3.2rem 1fr}.tools{top:0;position:relative}}
"""

def page(title, desc, canon, body, extra_js=''):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{E(title)}</title>
<meta content="{E(desc)}" name="description"/>
<link href="https://sdeuniverses.com{canon}" rel="canonical"/>
<meta content="{E(title)}" property="og:title"/>
<meta content="{E(desc)}" property="og:description"/>
<style>
{CSS}</style>
</head>
<body class="zh">
<header>
<nav aria-label="主导航" class="nav">
<a class="brand" href="/browse/">SDE Universes · 爱思乐园</a>
<a href="/browse/">首页</a>
<a href="/motifs/">专著母题</a>
<a href="/books/">专著书架</a>
<a href="/directory/">栏目总目录</a>
<a href="/search/">搜索</a>
</nav>
</header>
<main>
{body}
</main>
<footer>© 德麦国际 · <a href="/browse/">SDE Universes</a> · 专著母题</footer>
{extra_js}<script defer="" src="/wds-mode.js?v=20261025a"></script>
</body>
</html>
"""

def main():
    cards = {}
    for fn in os.listdir(SRC):
        m = re.match(r'^(\d+)\.md$', fn)
        if m and int(m.group(1)) in BOOKS:
            cards[int(m.group(1))] = parse(os.path.join(SRC, fn))
    nums = sorted(BOOKS, reverse=True)
    os.makedirs(OUT, exist_ok=True)
    today = datetime.date.today().isoformat()

    # ---- machine-readable
    recs, allmd = [], []
    for n in sorted(BOOKS):
        b = BOOKS[n]; c = cards.get(n)
        r = {'no': n, 'title': b.get('title', ''), 'subtitle': b.get('subtitle') or '',
             'author': b.get('authorNote') or '、'.join(b.get('authors') or []),
             'category': CATS.get(b.get('category'), b.get('category') or ''),
             'detail': (b.get('detailUrl') or '').replace('https://sdeuniverses.com', ''),
             'card': f'/motifs/{n}/' if c else None}
        if c:
            r.update({'domain': c.get('domain', ''), 'qtype': c['q'], 'motif': c.get('motif', '')})
            src = open(os.path.join(SRC, f'{n}.md'), encoding='utf-8').read().strip()
            r['text'] = src; allmd.append(src)
        recs.append(r)
    json.dump({'updated': today, 'count': len(recs), 'cards': len(cards), 'books': recs},
              open(os.path.join(OUT, 'motifs.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    open(os.path.join(OUT, 'all.md'), 'w', encoding='utf-8').write(
        f'# 专著母题 · 全部母题卡（{len(cards)} 张，{today}）\n\n' + '\n\n---\n\n'.join(allmd) + '\n')

    # ---- index
    qn = {k: sum(1 for c in cards.values() if c['q'] == k) for k in ('What', 'How', 'Why')}
    cat_opts = ''.join(f'<option value="{E(v)}">{E(v)}</option>' for v in CATS.values())
    rows = []
    for n in nums:
        b = BOOKS[n]; c = cards.get(n)
        au = b.get('authorNote') or '、'.join(b.get('authors') or [])
        cv = CATS.get(b.get('category'), '')
        if c:
            tags = ''.join(f'<i>{E(x)}</i>' for x in [c['q'], c.get('domain', ''), cv] if x)
            rows.append(f'<a class="row" href="/motifs/{n}/" data-c="{E(cv)}" data-q="{c["q"]}">'
                        f'<span class="no">第{n}号</span><span class="t">《{E(b.get("title",""))}》<span class="au">{E(au)}</span></span>'
                        f'<span class="mo">{E(c.get("motif",""))}</span><span class="tags">{tags}</span></a>')
        else:
            rows.append(f'<div class="row pending" data-c="{E(cv)}" data-q=""><span class="no">第{n}号</span>'
                        f'<span class="t">《{E(b.get("title",""))}》<span class="au">{E(au)}</span></span>'
                        f'<span class="mo">母题卡待写</span></div>')
    body = f"""<section class="hero"><div class="wrap">
<p class="eyebrow">MONOGRAPH MOTIFS · SDE UNIVERSES</p>
<h1>专著母题</h1>
<p class="lead">德麦国际每一部专著，压成一张约两千字的母题卡：一句话母题、它推翻的默认看法、母题怎样立起来、核心构念、全书骨架、关键案例、碰撞接口、边界。做 SDE 二阶碰撞或形式逻辑归纳时，先在这里选书、抽命题，就能很快出大纲，不必先通读全书。</p>
<div class="stats"><span>母题卡 {len(cards)} 张</span><span>专著 {len(BOOKS)} 部</span><span>What {qn['What']}</span><span>How {qn['How']}</span><span>Why {qn['Why']}</span><span>更新 {today}</span></div>
<div class="links"><a href="/motifs/motifs.json">机读总表 motifs.json</a><a href="/motifs/all.md">全部母题卡合订 all.md</a></div>
</div></section>
<section class="tools"><div class="wrap">
<input id="q" type="search" placeholder="搜书名、作者、母题、构念…" aria-label="搜索母题"/>
<select id="fc" aria-label="分类"><option value="">全部分类</option>{cat_opts}</select>
<select id="fq" aria-label="题型"><option value="">全部题型</option><option>What</option><option>How</option><option>Why</option></select>
<span class="count" id="cnt"></span>
</div></section>
<section class="list"><div class="wrap" id="list">
{chr(10).join(rows)}
</div></section>"""
    js = """<script>
(function(){var q=document.getElementById('q'),fc=document.getElementById('fc'),fq=document.getElementById('fq'),cnt=document.getElementById('cnt');
var rows=[].slice.call(document.querySelectorAll('#list .row'));
function run(){var s=q.value.trim().toLowerCase(),c=fc.value,t=fq.value,k=0;
rows.forEach(function(r){var ok=(!s||r.textContent.toLowerCase().indexOf(s)>=0)&&(!c||r.getAttribute('data-c')===c)&&(!t||r.getAttribute('data-q')===t);r.style.display=ok?'':'none';if(ok)k++});
cnt.textContent=k+' 部';}
q.addEventListener('input',run);fc.addEventListener('change',run);fq.addEventListener('change',run);run();})();
</script>
"""
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(
        page('专著母题 · SDE Universes', '德麦国际全部专著的母题卡：一句话母题、核心构念、碰撞接口与边界，供 SDE 二阶碰撞与形式归纳快速出大纲。',
             '/motifs/', body, js))

    # ---- per-book pages
    have = sorted(cards, reverse=True)
    for i, n in enumerate(have):
        b = BOOKS[n]; c = cards[n]
        au = c.get('author') or b.get('authorNote') or '、'.join(b.get('authors') or [])
        det = (b.get('detailUrl') or '').replace('https://sdeuniverses.com', '')
        meta = ''.join(f'<dt>{k}</dt><dd>{E(v)}</dd>' for k, v in [
            ('副题', c.get('subtitle') or b.get('subtitle') or '无'), ('作者', au), ('分类', CATS.get(b.get('category'), '')),
            ('题域', c.get('domain', '')), ('题型', c.get('qtype', ''))] if v)
        secs = ''.join(f'<h2>{E(s["h"])}</h2>\n{render_lines(s["lines"])}\n' for s in c['sections'])
        prev_n = have[i - 1] if i > 0 else None
        next_n = have[i + 1] if i + 1 < len(have) else None
        pager = '<div class="pager">' + (f'<a href="/motifs/{prev_n}/">← 第{prev_n}号《{E(BOOKS[prev_n]["title"])}》</a>' if prev_n else '<span></span>') + \
                (f'<a href="/motifs/{next_n}/">第{next_n}号《{E(BOOKS[next_n]["title"])}》 →</a>' if next_n else '<span></span>') + '</div>'
        links = '<div class="links"><a href="/motifs/">← 返回专著母题总表</a>' + \
                (f'<a href="{E(det)}">读这本书</a>' if det else '') + '</div>'
        body = f"""<article>
{links}
<p class="eyebrow" style="margin-top:1.6rem">专著母题 · 德麦国际专著第 {n} 号</p>
<h1 style="font-size:clamp(1.8rem,5vw,2.6rem)">《{E(b.get('title',''))}》</h1>
<p class="motif">{E(c.get('motif',''))}</p>
<dl class="meta">{meta}</dl>
{secs}
{pager}
</article>"""
        d = os.path.join(OUT, str(n)); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
            page(f'《{b.get("title","")}》母题卡 · 专著母题', (c.get('motif') or '')[:120], f'/motifs/{n}/', body))
    print(f'motif cards: {len(cards)} / books: {len(BOOKS)}')

if __name__ == '__main__':
    main()
