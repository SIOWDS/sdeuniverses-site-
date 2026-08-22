#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkthreeviews.py —— 重建「三视角专栏」：总目页 public/three-views/index.html
   ＋ 21 个分篇页 public/three-views/<slug>/index.html。

底料：《三视角图册》（发明/王德生 制作/马锦涛，200 页）。
  · 正文 140 图（原册页 8–147）→ img/g001.webp … g140.webp，分属 20 篇
  · 补遗  47 图（原册页 154–200）→ img/x01.webp … x47.webp
    ⚠ 补遗那 47 页原带的二维码全部是同一枚**个人微信名片码**，导出时已用白块遮掉；
      重新导出务必沿用 tools/threeviews_data.py 旁的导出流程，别把原码放回来。
  · 每图的扫码文章链接由二维码解码得来，存于 threeviews_data.py 的 QR。

⚠ 页壳（head/nav/footer/scripts）从 **public/browse/index.html** 现取——
  站点首页现在是 /browse/，public/index.html 只是入口跳转页，别改回去。
  这里的四个壳函数是 tools/mkcolumnpages.py 的副本，**不要 import 那个模块**
  （它顶层就执行建页动作，跑起来会覆盖 /taste/ 并重建已删的 /agents/）。

改强调色要两处一起改：本文件的 AC 与 public/browse/index.html 的 .col-tv。

用法：python3 tools/mkthreeviews.py [--dry-run]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from threeviews_data import SECTIONS, NAMES, APPENDIX, QR, XQR_REMOVED  # noqa: E402

OUT = os.path.join(PUB, 'three-views')
AC = '#2C7FA8'                      # 本栏强调色（取自图册封面那枚三色环的蓝）
ZH, EN = '三视角专栏', 'Three Views'
DESC = ('三视角专栏：王德生《三视角图册》全册上站——对比·变化·分布三个视角，'
        '九宫格·27宫格·81宫格的层层展开，140 张主图分二十篇，另有补遗 47 张。'
        '全站唯一的图谱栏目，一图一判断。')


# ---------- 页壳（抄自 tools/mkcolumnpages.py，勿 import 那个模块） ----------

def head_of(t):
    # ⚠ 从 '<head' 起切会把 <!doctype> 与 <html> 开标签一起丢掉（HTMLParser 会报「多余
    #   </html>」），所以这里自己补回来，别照抄 mkcolumnpages 那一行。
    return '<!doctype html>\n<html lang="zh">\n' + t[t.index('<head'):t.index('</head>') + 7]


def nav_of(t):
    m = re.search(r'<(nav|div|header)[^>]*class="[^"]*nav-bar[^"]*"', t)
    i = t.index('<nav') if not m else t.rindex('<nav', 0, m.start()) if '<nav' in t[:m.start()] else m.start()
    tag = 'nav'
    depth = 0
    for mm in re.finditer(r'<nav\b|</nav>', t[i:]):
        depth += 1 if not mm.group(0).startswith('</') else -1
        if depth == 0:
            return t[i:i + mm.end()]
    raise SystemExit('顶栏没配上')


def inline_script_of(t):
    """browse 首页尾部那段中英切换 ＋ 顶栏让位脚本（没有它，fixed 顶栏会盖住正文）。"""
    m = re.search(r'<script>\s*\n// 中英切换.*?</script>', t, re.S)
    if not m:
        raise SystemExit('找不到首页尾部那段内联脚本')
    return m.group(0)


def scripts_of(t):
    tail = t[-4000:]
    return '\n'.join(m.group(0) for m in
                     re.finditer(r'<script[^>]*\bsrc="[^"]*"[^>]*></script>', tail))


def head_for(title, desc, canon):
    src = open(os.path.join(PUB, 'browse', 'index.html'), encoding='utf-8').read()
    h = head_of(src)
    h = re.sub(r'<title>.*?</title>', '<title>%s</title>' % esc(title), h, count=1, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + esc(desc) + m.group(2), h, count=1)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*(")',
               lambda m: m.group(1) + esc(title) + m.group(2), h, count=1)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*(")',
               lambda m: m.group(1) + esc(desc) + m.group(2), h, count=1)
    if '<link rel="canonical"' in h:
        h = re.sub(r'(<link rel="canonical" href=")[^"]*(")',
                   lambda m: m.group(1) + canon + m.group(2), h, count=1)
    else:
        h = h.replace('</head>', '<link rel="canonical" href="%s">\n</head>' % canon)
    h = h.replace('</head>', EXTRA_CSS + '\n</head>')
    return h


EXTRA_CSS = """<style>
[id]{scroll-margin-top:190px}
@media(max-width:900px){[id]{scroll-margin-top:210px}}
.tv-wrap{max-width:1180px;margin:0 auto;padding:0 1.6rem}
.tv-hd{padding:2.6rem 0 1.2rem;border-bottom:1px solid var(--border2,rgba(138,104,23,.16))}
.tv-eyebrow{font-size:.82rem;letter-spacing:.22em;color:%(AC)s;font-weight:700;text-transform:uppercase}
.tv-hd h1{font-size:2.3rem;line-height:1.28;margin:.5rem 0 .2rem}
.tv-sub{color:var(--muted,#7a6a52);font-size:.98rem}
.tv-lead{margin:1.9rem 0 0;font-size:1.04rem;line-height:1.95}
.tv-lead p{margin:0 0 1rem}
.tv-note{margin:1.6rem 0 0;padding:1rem 1.2rem;border-left:3px solid %(AC)s;background:rgba(44,127,168,.055);font-size:.94rem;line-height:1.8}
.tv-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:1.5rem 1.3rem;margin:2.2rem 0 1rem}
.tv-card{display:block;text-decoration:none;color:inherit;border:1px solid var(--border2,rgba(138,104,23,.18));border-radius:10px;overflow:hidden;background:#fff;transition:transform .18s,box-shadow .18s}
.tv-card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(0,0,0,.09)}
.tv-card img{display:block;width:100%%;aspect-ratio:4/3;object-fit:contain;background:#fbfaf6}
.tv-cb{padding:.7rem .85rem .9rem}
.tv-cb b{display:block;font-size:1.06rem;letter-spacing:.03em}
.tv-cb span{display:block;margin-top:.25rem;font-size:.83rem;color:var(--muted,#7a6a52)}
.tv-fig{margin:0 0 3.2rem;padding-bottom:2.4rem;border-bottom:1px dashed var(--border2,rgba(138,104,23,.2))}
.tv-fig:last-child{border-bottom:0}
.tv-no{display:inline-block;min-width:2.9em;font-family:'Playfair Display',Georgia,serif;font-size:.9rem;letter-spacing:.12em;color:%(AC)s;font-weight:700}
.tv-fig h3{display:inline;font-size:1.42rem;letter-spacing:.02em}
.tv-fig figure{margin:1rem 0 0}
.tv-fig img{display:block;width:100%%;max-width:1000px;height:auto;border:1px solid var(--border2,rgba(138,104,23,.16));border-radius:8px;background:#fff}
.tv-links{margin:1rem 0 0;font-size:.94rem;line-height:1.9}
.tv-links .tvl-h{color:var(--muted,#7a6a52);font-size:.84rem;letter-spacing:.1em}
.tv-links ol{margin:.3rem 0 0;padding-left:1.4rem}
.tv-links a{color:%(AC)s}
.tv-none{margin:.8rem 0 0;font-size:.88rem;color:var(--muted,#7a6a52)}
.tv-navrow{display:flex;flex-wrap:wrap;gap:.6rem 1.1rem;margin:2rem 0 .4rem;font-size:.92rem}
.tv-navrow a{color:%(AC)s;text-decoration:none}
.tv-navrow a:hover{text-decoration:underline;text-underline-offset:4px}
@media(max-width:640px){.tv-hd h1{font-size:1.7rem}.tv-wrap{padding:0 1rem}}
</style>""" % {'AC': AC}


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


# ---------- 组装 ----------

def sections_all():
    """20 篇 ＋ 补遗，统一成 (中文名, slug, [图键…]) 三元组。"""
    out = []
    for zh, slug, a, b in SECTIONS:
        out.append((zh, slug, ['g%03d' % i for i in range(a, b + 1)], a))
    out.append(('补遗', 'addenda', ['x%02d' % j for j in range(1, 48)], 0))
    return out


def links_block(n):
    urls = QR.get(n, [])
    titles = APPENDIX.get(n, [])
    bits = []
    if titles:
        bits.append('<div class="tvl-h">图册附录列出的原文</div><ol>'
                    + ''.join('<li>%s</li>' % esc(t) for t in titles) + '</ol>')
    if urls:
        bits.append('<div class="tvl-h" style="margin-top:.55rem">'
                    '扫码原文 · 微信公众号（%d）</div><ol>' % len(urls)
                    + ''.join('<li><a href="%s" target="_blank" rel="noopener nofollow">'
                              '打开第 %d 篇 →</a></li>' % (esc(u), k + 1)
                              for k, u in enumerate(urls)) + '</ol>')
    if not bits:
        return '<p class="tv-none">此图在原册中没有配二维码。</p>'
    return '<div class="tv-links">' + ''.join(bits) + '</div>'


def build_section_page(zh, slug, keys, start, src):
    is_add = slug == 'addenda'
    title = '%s · %s | 三视角专栏 | SDE Universes' % (zh, ZH)
    desc = ('三视角图册「%s」共 %d 张图%s。' %
            (zh, len(keys), '' if is_add else '（第 %d–%d 号）' % (start, start + len(keys) - 1)))
    body = [head_for(title, desc, 'https://sdeuniverses.com/three-views/%s/' % slug),
            '<body class="zh">', nav_of(src), '<main class="tv-wrap">',
            '<header class="tv-hd">',
            '<div class="tv-eyebrow">三视角图册 · Three Views Atlas</div>',
            '<h1>%s</h1>' % esc(zh),
            '<p class="tv-sub">共 %d 张图%s　·　发明 王德生　·　制作 马锦涛</p>' %
            (len(keys), '' if is_add else ' · 第 %d–%d 号' % (start, start + len(keys) - 1)),
            '</header>',
            '<div class="tv-navrow"><a href="/three-views/">← 三视角专栏总目</a></div>']
    if is_add:
        body.append('<div class="tv-note">这 47 张不在图册目录与附录之内，是全册末尾另一套'
                    '视觉风格的补充图，多为三视角在具体事业与教学上的落地图。'
                    '原页面左上角带的是一枚个人微信名片码，上站前已移除；'
                    '「发明人 王德生」印章按原样保留。</div>')
    for k, key in enumerate(keys):
        n = start + k
        if is_add:
            cap = '<span class="tv-no">补 %02d</span> <h3>三视角补遗图</h3>' % (k + 1)
            links = ''
        else:
            cap = ('<span class="tv-no">%03d</span> <h3>%s</h3>' % (n, esc(NAMES[n])))
            links = links_block(n)
        body.append(
            '<section class="tv-fig" id="%s">%s<figure>'
            '<a href="/three-views/img/%s.webp" target="_blank" rel="noopener">'
            '<img src="/three-views/img/%s.webp" loading="lazy" decoding="async" '
            'alt="%s"></a></figure>%s</section>'
            % (key, cap, key, key,
               esc('三视角图册补遗第 %d 图' % (k + 1) if is_add
                   else '三视角图册第 %03d 图 %s' % (n, NAMES[n])), links))
    body += ['<div class="tv-navrow"><a href="/three-views/">← 三视角专栏总目</a>'
             '<a href="/browse/">爱思乐园首页</a></div>',
             '<div class="dir-foot" style="padding:2.6rem 0 3rem;text-align:center;'
             'color:var(--muted);font-size:.86rem"><p>© 德麦国际 · '
             '<a href="/browse/">爱思乐园 SDE Universes</a></p></div>',
             '</main>', inline_script_of(src), scripts_of(src), '</body>', '</html>']
    return '\n'.join(body)


LEAD = """<div class="tv-lead">
<p>三视角，是王德生在 SDE 之前立起来的一套看法：任何一件事，都可以从<b>对比</b>、<b>变化</b>、<b>分布</b>三个视角去看。三个视角各自再分三层，就是九宫格；九宫格再分，就是 27 宫格、81 宫格，直到 19683。它不是一套结论，是一副把话说清楚之前先得摆好的架子。</p>
<p>《三视角图册》把这套架子画成了图。全册 140 张主图分二十篇，从智慧论、本体论一路走到神学、科学、国学、逻辑、教育、经济、生理健康与美学——同一副架子，在二十个领域里各摆一次。另有补遗 47 张，是它落到具体事业与教学上的样子。</p>
<p>这一栏与全站其余各栏不同：站上此前全是文字，这里是<b>图</b>。一张图就是一个判断，看得比读得快。它也是这个站上门槛最低的入口——不必先懂 SDE，先看图。</p>
</div>
<div class="tv-note">
<b>两处分界，先说在前面。</b><br>
<b>与 SDE 的分界：</b>三视角问的是「从哪几个角度看」，SDE（显露·差异·纠缠）问的是「它是怎么发生的」。前者是看法的分法，后者是发生的本体论。三视角是 SDE 的来路与母体，不是 SDE 的简化版；SDE 也不是三视角的续集。读这一栏，读的是那副架子本身。<br>
<b>与「三维九宫」的分界：</b><a href="/nine-doorways/">三维九宫</a>那一栏做的是 SDE 的九宫应用；这一栏放的是三视角九宫格的原件。同一个「九宫」两处出现，不是重复——一处是用它，一处是它本身。
</div>"""


def build_index(secs, src):
    title = '三视角专栏 | 王德生《三视角图册》全册 | SDE Universes'
    body = [head_for(title, DESC, 'https://sdeuniverses.com/three-views/'),
            '<body class="zh">', nav_of(src), '<main class="tv-wrap">',
            '<header class="tv-hd">',
            '<div class="tv-eyebrow">三视角图册 · Three Views Atlas</div>',
            '<h1>三视角专栏</h1>',
            '<p class="tv-sub">对比 · 变化 · 分布　|　187 张图 · 二十篇 ＋ 补遗　|　'
            '发明 王德生　·　制作 马锦涛</p>',
            '</header>', LEAD, '<div class="tv-grid">']
    for zh, slug, keys, start in secs:
        cover = keys[0]
        rng = ('补遗 · %d 张' % len(keys)) if slug == 'addenda' \
            else ('第 %d–%d 号 · %d 张' % (start, start + len(keys) - 1, len(keys)))
        body.append('<a class="tv-card" href="/three-views/%s/">'
                    '<img src="/three-views/img/%s-t.webp" loading="lazy" decoding="async" '
                    'alt="%s"><div class="tv-cb"><b>%s</b><span>%s</span></div></a>'
                    % (slug, cover, esc(zh + ' 代表图'), esc(zh), rng))
    body.append('</div>')
    body.append('<div class="tv-note" style="margin-top:2.4rem"><b>关于「扫码原文」。</b>'
                '图册每张主图旁原印着二维码，指向王德生历年写在微信公众号上的文章与视频。'
                '这些链接已全部解出，逐图列在各分篇页上，眼下直接外链公众号原文；'
                '它们会分批搬回本站首发，搬一篇、这里就换一篇为站内地址。'
                '140 张主图中 130 张有码，共 %d 条外链；另 10 张原册即无码。</div>'
                % sum(len(v) for v in QR.values()))
    body += ['<div class="tv-navrow"><a href="/browse/">← 爱思乐园首页</a>'
             '<a href="/nine-doorways/">三维九宫 →</a>'
             '<a href="/drwang/">王博士与 SDE →</a></div>',
             '<div class="dir-foot" style="padding:2.6rem 0 3rem;text-align:center;'
             'color:var(--muted);font-size:.86rem"><p>© 德麦国际 · '
             '<a href="/browse/">爱思乐园 SDE Universes</a></p></div>',
             '</main>', inline_script_of(src), scripts_of(src), '</body>', '</html>']
    return '\n'.join(body)


def main():
    dry = '--dry-run' in sys.argv
    src = open(os.path.join(PUB, 'browse', 'index.html'), encoding='utf-8').read()
    secs = sections_all()
    n_img = sum(len(k) for _, _, k, _ in secs)
    print('篇 %d（含补遗）· 图 %d · 外链 %d · 补遗遮掉的个人二维码 %d 枚'
          % (len(secs), n_img, sum(len(v) for v in QR.values()), XQR_REMOVED))
    if dry:
        return
    os.makedirs(OUT, exist_ok=True)
    for zh, slug, keys, start in secs:
        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
            build_section_page(zh, slug, keys, start, src))
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(build_index(secs, src))
    print('已写 %d 页 →' % (len(secs) + 1), OUT)


if __name__ == '__main__':
    main()
