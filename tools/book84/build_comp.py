# -*- coding: utf-8 -*-
"""第 84 号配套读物生成器：explain.html / practice.html + 落地页与目录页的三读入口条。
内容源 /home/claude/b84/comp/{explain,practice}.txt，格式 TITLE:/SUB:/ABS: + '== 小节'。
幂等：入口条已存在则跳过。"""
import os, re, html as H

SITE = '/home/claude/site/public'
BASE = f'{SITE}/books/m/84'
SRC = '/home/claude/b84/comp'
NO, TITLE = '84', '越顺利，越没有你的位置'

ACC = {'explain': ('#D6AC60', '#B98F42', '#171207'), 'practice': ('#7FB2E0', '#5A8CBC', '#0C141F')}


def parse(kind):
    t = open(f'{SRC}/{kind}.txt', encoding='utf-8').read()
    meta = {}
    for k in ('TITLE', 'SUB', 'ABS'):
        m = re.search(r'^%s:\s*(.+)$' % k, t, re.M)
        meta[k] = m.group(1).strip() if m else ''
    body = re.sub(r'^(TITLE|SUB|ABS):.*$', '', t, flags=re.M)
    secs, cur = [], None
    for line in body.split('\n'):
        if line.startswith('== '):
            cur = (line[3:].strip(), []); secs.append(cur)
        elif cur is not None and line.strip():
            cur[1].append(line.strip())
    return meta, secs


def inline(s):
    s = H.escape(s)
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)


def build(kind):
    meta, secs = parse(kind)
    a, a2, tint = ACC[kind]
    other = 'practice' if kind == 'explain' else 'explain'
    otherlabel = '③ 实用文 · 方法流程' if kind == 'explain' else '② 诠释文 · 白话解释'
    selflabel = '② 诠释文 · 白话解释' if kind == 'explain' else '③ 实用文 · 方法流程'
    chars = sum(1 for c in ''.join(''.join(b) for _, b in secs) if '\u4e00' <= c <= '\u9fff')
    toc = ''.join('<a href="#s%d">%s</a>' % (i + 1, H.escape(t)) for i, (t, _) in enumerate(secs))
    body = []
    for i, (t, bs) in enumerate(secs):
        body.append('<h2 id="s%d">%s</h2>' % (i + 1, H.escape(t)))
        for b in bs:
            body.append('<p>%s</p>' % inline(b))
    css = f"""<style>
:root{{--bg:#0B0E14;--fg:#E6E8EE;--dim:#8A90A0;--acc:{a};--acc2:{a2};--line:#222836;--card:{tint}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);
font:16.5px/2.0 "Noto Serif CJK SC","Songti SC",Georgia,serif}}
a{{color:var(--acc);text-decoration:none}}a:hover{{text-decoration:underline}}
.bar{{position:sticky;top:0;background:rgba(11,14,20,.94);backdrop-filter:blur(8px);
border-bottom:1px solid var(--line);padding:11px 20px;display:flex;gap:16px;flex-wrap:wrap;
font-size:13.5px;align-items:center}}
.wrap{{max-width:760px;margin:0 auto;padding:30px 22px 70px}}
h1{{font-size:27px;line-height:1.45;margin:16px 0 8px;font-weight:700}}
.sub{{color:var(--dim);font-size:14.5px;margin-bottom:6px}}
.meta{{color:var(--dim);font-size:13px;margin-bottom:26px;font-family:"Noto Sans Mono CJK SC",monospace}}
.abs{{background:var(--card);border-left:3px solid var(--acc);padding:16px 18px;margin:0 0 30px;
color:#D8DCE6;font-size:15.5px;line-height:1.9}}
.abs p{{margin:0}}
.triad{{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 30px}}
.triad a{{flex:1;min-width:190px;border:1px solid var(--line);padding:11px 14px;font-size:13.5px;
color:var(--fg);line-height:1.5}}
.triad a.on{{border-color:var(--acc);color:var(--acc);background:var(--card)}}
.triad span{{display:block;color:var(--dim);font-size:12px;margin-top:3px}}
.toc{{border:1px solid var(--line);padding:14px 18px;margin:0 0 34px;
display:grid;grid-template-columns:1fr 1fr;gap:2px 18px}}
.toc a{{color:#C3C9D6;font-size:14px;padding:3px 0}}
h2{{font-size:19px;color:var(--acc);margin:38px 0 12px;font-weight:700;
border-top:1px solid var(--line);padding-top:18px;line-height:1.5}}
p{{margin:0 0 15px;text-align:justify}}
b{{color:#FFF;font-weight:700}}
.foot{{margin-top:54px;padding-top:18px;border-top:1px solid var(--line);
color:var(--dim);font-size:12.5px;line-height:1.9}}
@media(max-width:560px){{.toc{{grid-template-columns:1fr}}}}
</style>"""
    bar = (f'<div class="bar"><a href="/books/m/{NO}/">← 专著首页</a>'
           f'<a href="/books/m/{NO}/text/">网页版全书</a>'
           f'<a href="/books/m/{NO}/read.html">📄 在线 PDF</a>'
           f'<span style="color:var(--dim)">德麦国际专著第 {NO} 号 · 配套读物</span></div>')
    triad = (f'<div class="triad">'
             f'<a href="/books/m/{NO}/text/">① 理论正本<span>全书 343 页 · 26.2 万字</span></a>'
             f'<a class="on" href="#">{selflabel}<span>本页 · 约 {chars} 汉字</span></a>'
             f'<a href="/books/m/{NO}/{other}.html">{otherlabel}<span>姊妹篇</span></a></div>')
    html = (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{H.escape(meta["TITLE"])} · {TITLE} 配套读物 · 德麦国际专著第 {NO} 号</title>'
            f'<meta name="description" content="{H.escape(meta["ABS"][:150])}">{css}</head><body>'
            f'{bar}<div class="wrap"><h1>{H.escape(meta["TITLE"])}</h1>'
            f'<div class="sub">{H.escape(meta["SUB"])}</div>'
            f'<div class="meta">SDE Universes · 配套读物 · 2026年8月 · 约 {chars} 汉字</div>'
            f'{triad}<div class="abs"><p>{inline(meta["ABS"])}</p></div>'
            f'<div class="toc">{toc}</div>{"".join(body)}'
            f'<div class="foot">本页是《{TITLE}》（德麦国际专著第 {NO} 号）的配套读物，'
            f'不替代正本；书中的判据、数据口径与判错条件以正本为准。'
            f'<br>© 德麦国际出版社 · 新加坡 · SDE Universes</div></div></body></html>')
    open(f'{BASE}/{kind}.html', 'w', encoding='utf-8').write(html)
    return chars


c1 = build('explain')
c2 = build('practice')
print('explain.html', c1, '汉字 · practice.html', c2, '汉字')

# ---- 落地页三读入口条（插在 hero 的 acts 之后，幂等）----
p = f'{BASE}/index.html'
h = open(p, encoding='utf-8').read()
MARK = '<!-- THREE-READS -->'
if MARK not in h:
    bar = (MARK + '<div class="note" style="margin-top:18px;border-top:1px solid var(--line);'
           'padding-top:16px"><b>三读</b>：'
           f'<a href="/books/m/{NO}/text/">① 理论正本</a> · '
           f'<a href="/books/m/{NO}/explain.html">② 诠释文《你按了铃，灯亮了，可是没人来》</a>（白话，零术语，约 5,600 字） · '
           f'<a href="/books/m/{NO}/practice.html">③ 实用文《取两个数，再留一处必须自己付款的地方》</a>（诊断与处置流程，约 5,300 字）</div>')
    anchor = '<div class="note">十一位作者互不相识'
    assert anchor in h
    h = h.replace(anchor, bar + anchor, 1)
    open(p, 'w', encoding='utf-8').write(h)
    print('landing: three-reads bar inserted')
else:
    print('landing: already has bar')

# ---- 网页版目录页也挂一条 ----
p2 = f'{BASE}/text/index.html'
h2 = open(p2, encoding='utf-8').read()
if MARK not in h2:
    bar2 = (MARK + '<div style="border:1px solid var(--line);padding:13px 16px;margin:0 0 22px;'
            'font-size:14px;line-height:1.9">三读：本页是 <b>① 理论正本</b> · '
            f'<a href="/books/m/{NO}/explain.html">② 诠释文（白话）</a> · '
            f'<a href="/books/m/{NO}/practice.html">③ 实用文（方法流程）</a></div>')
    anchor2 = '<div class="toc">'
    assert anchor2 in h2
    h2 = h2.replace(anchor2, bar2 + anchor2, 1)
    open(p2, 'w', encoding='utf-8').write(h2)
    print('text index: three-reads bar inserted')
else:
    print('text index: already has bar')
