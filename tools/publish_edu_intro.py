#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布 /education/intro/ 频道「SDE教育学入门」及其第一讲。
用法: python3 tools/publish_edu_intro.py
做三件事: ① 生成频道页 ② 生成第一讲(三读骨架) ③ 把频道挂进 /education/ 的导航与区块
所有 HTML 改动前均 assert 锚点存在。
"""
import os, re, sys, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB  = os.path.join(ROOT, 'public')
EDU  = os.path.join(PUB, 'education')
CH   = os.path.join(EDU, 'intro')
TPL  = os.path.join(EDU, 'ai-era', 'adjudication-outsourcing', 'index.html')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _intro_lecture1 as L1

ACCENT = '#8C5A2B'      # 入门频道口音：赭陶（与 ai-era #146C94、栏目 #336699 区分）
CH_TITLE = 'SDE教育学入门'
CH_EN    = 'SDE Pedagogy · An Introduction'

LECTURES = [
 ('discovery-to-genesis', '第一讲', '教育：从发现到发生的革命',
  '传道模式的八环链，与它的八处裂缝。逐环写出它悄悄承诺了什么，再逐环去敲；末章交代它与「最小指导教学」的分界。', 'live'),
 ('what-is-a-concept', '第二讲', '一个概念是怎么发生的',
  '从数数到加法、到乘法、到幂与对数：七条概念发生链，两种完全不同的「不够用」。', 'soon'),
 ('the-container', '第三讲', '容器：一个从未被写下来的假设',
  '接受能力、打开思路、巩固练习、知识体系——四个日常说法，同一个未经辩护的预设。', 'soon'),
 ('time-for-telling', '第四讲', '讲授的时机',
  '不是要不要讲，是什么时候讲。有效失败、为未来学习作准备，与它们各自的边界条件。', 'soon'),
 ('three-conditions', '第五讲', '三种条件：E-条件 · D-条件 · S-条件',
  '一堂课的三种条件与它们不可颠倒的顺序，以及一份可以直接用的备课模板。', 'soon'),
 ('six-entries', '第六讲', '六种起手位',
  '同一个概念，六条进入路径；起手位选错，不只是慢，而会使一整类设计在原理上失效。', 'soon'),
 ('what-is-learned', '第七讲', '「学会了」到底是什么样子',
  '从「装在他身上」到「他的世界里多了一样能站住的东西」——检验方式随之全部改写。', 'soon'),
 ('subject-cases', '第八讲', '五个学科的现场',
  '加法、乘法、分数、面积、方程：先不要做什么、先做什么、崩掉的那一刻。', 'soon'),
 ('failure-that-works', '第九讲', '不是所有失败都是有效的',
  '三个必要条件与三条禁忌。缺任何一条，撞墙就只是挫败。', 'soon'),
 ('what-to-tell-directly', '第十讲', '哪些内容应当直接讲',
  '约定、安全、名字、脚手架——四类不必绕的内容，以及绕了为什么是浪费。', 'soon'),
 ('assessment', '第十一讲', '评价：如果学习是发生的，考什么',
  '当「装了多少」不再是目标，评价的对象要换成什么，以及这一换会遇到的现实阻力。', 'soon'),
 ('boundaries', '第十二讲', '这套东西不做什么',
  '本系列的适用边界、可证伪条件，与三条它明确不主张的推论。', 'soon'),
]

# ─────────────────────────── 工具 ───────────────────────────
def read(p):
    with open(p, encoding='utf-8') as f: return f.read()

def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f: f.write(s)
    print(f'  写入 {p.replace(ROOT+"/","")}  ({len(s)} 字节)')

def cjk(s):
    return len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'<[^>]+>', '', s)))

def tagcheck(h, where):
    for t in ('div', 'section', 'article', 'main', 'style', 'script', 'ol', 'p'):
        o = len(re.findall(rf'<{t}[\s>]', h)); c = len(re.findall(rf'</{t}>', h))
        if t in ('p',) and o != c:
            print(f'  ⚠ {where}: <{t}> {o} 开 / {c} 闭（p 允许省略闭合，仅提示）')
        elif t not in ('p',) and o != c:
            raise AssertionError(f'{where}: <{t}> 开 {o} 闭 {c} 不配对')
    print(f'  ✓ {where} 标签配对')

# ─────────────────────────── 取模板 CSS ───────────────────────────
tpl = read(TPL)
m = re.search(r'<style>(.*?)</style>', tpl, re.S)
assert m, '模板未找到 <style>'
CSS = m.group(1)
# 换口音色 + 补本频道自有样式
CSS = CSS.replace('#146C94', ACCENT).replace('#0f5b7d', ACCENT)
CSS += """
.fbox{margin:1.6rem 0;padding:1.15rem 1.4rem;background:#FBF3EA;border:1px solid #E4D3BF;border-radius:8px}
.fbox p{margin:0;font-size:1.06rem;line-height:1.95;color:#3A2F22}
.tag{margin:1.1rem 0;padding:.55rem .9rem;background:#F4F0E8;border-radius:6px;font-size:.93rem;color:#6B5D47}
.cases p{margin:.85rem 0;padding:.75rem 1rem;background:#FAF6EC;border-radius:6px;line-height:1.9}
sup.rf{color:#8C5A2B;font-size:.72em}
ol.ref{padding-left:1.4rem}
ol.ref li{margin:.55rem 0;line-height:1.8;font-size:.95rem;color:#4A4235}
"""

# 取三读骨架里的 pdf.js 脚本（原样复用，只换 PDF_URL）
scripts = re.findall(r'<script>(.*?)</script>', tpl, re.S)
PDFJS = next((s for s in scripts if 'getDocument' in s), None)
assert PDFJS, '模板未找到 pdf.js 阅读器脚本'

NAV = re.search(r'<nav>.*?</nav>', tpl, re.S).group(0)
NAV = NAV.replace('class="sib here"', 'class="sib"')

# ─────────────────────────── 第一讲页面 ───────────────────────────
def build_lecture():
    slug, no, title, blurb, _ = LECTURES[0]
    words = cjk(L1.BODY)
    toc = '\n'.join(f'<a href="#{i}">{t}</a>' for i, t in L1.TOC)
    kw  = '关键词：' + '；'.join(L1.KW)
    pdfurl = f'/education/intro/pdf/{slug}.pdf'
    h = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}——{L1.SUB} | SDE教育学入门 | SDE Universes</title>
<meta name="description" content="传道模式可以写成一条八环链：知识是客观世界的特征，被发现、被传播、被写进教材、被接受、消化、吸收、重组。本文逐环写出它承诺了什么，再逐环去敲，并交代它与「最小指导教学」的分界。">
<link rel="canonical" href="https://sdeuniverses.com/education/intro/{slug}/">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}——{L1.SUB}">
<meta property="og:description" content="八环链，八处裂缝，与一句从未被写在任何教参上的话。">
<meta property="og:url" content="https://sdeuniverses.com/education/intro/{slug}/">
<meta name="sde:column" content="education/intro">
<style>{CSS}</style>
</head>
<body>
{NAV}
<header class="hero">
  <div class="hero-bg"></div>
  <div class="eyebrow"><a href="/education/intro/">SDE教育学入门</a> · {no}</div>
  <h1 class="art-title">{title}</h1>
  <p class="art-sub">{L1.SUB}</p>
  <div class="art-meta">王德生 · 德麦国际 SDE 学派 · SDE教育学入门 · 2026年8月10日 · 约 {words:,} 字 · 8 条参考文献 · 三种阅读模式</div>
</header>

<div class="modes"><div class="mw">
  <button class="modebtn on" data-m="web"><span class="ic">📖</span>网页长文</button>
  <button class="modebtn" data-m="pdf"><span class="ic">📄</span>在线读 PDF</button>
  <button class="modebtn" data-m="dl"><span class="ic">⬇</span>下载 PDF</button>
</div></div>

<div id="web" class="panel on">
<main class="wrap">
<section class="body">
  <div class="abs"><div class="l">摘 要</div><p>{L1.ABS}</p></div>
  <div class="kw">{kw}</div>
  <div class="toc"><div class="l">目 录</div>{toc}</div>
  <article>
{L1.BODY}
  </article>
</section>
</main>
</div><!--/#web-->

<div id="pdf" class="panel"><div class="rdr">
  <div class="rdr-bar">
    <button class="rbtn" id="pv" disabled>‹ 上一页</button>
    <span class="pbox"><input id="pin" type="number" min="1" value="1"> / <span class="ptot" id="ptot">…</span></span>
    <button class="rbtn" id="nx" disabled>下一页 ›</button>
    <span class="zm"><button class="rbtn" id="zo" title="缩小">−</button><button class="rbtn" id="zi" title="放大">＋</button></span>
    <a class="rbtn dl" href="{pdfurl}" download>⬇ 下载</a>
  </div>
  <div class="rdr-stage">
    <div id="rload" class="rload"><div class="spin"></div>正在载入精排 PDF…</div>
    <div id="cwrap" style="display:none"><canvas id="pcv"></canvas></div>
    <div class="tapL" id="tL"></div><div class="tapR" id="tR"></div>
  </div>
  <div class="rhint">← → 方向键翻页 · 点击画面两侧翻页 · 可输入页码跳转 · ＋ − 缩放</div>
</div></div>

<div id="dl" class="panel"><div class="card">
  <h2>下载精排 PDF</h2>
  <p style="color:#4A4235;line-height:1.85">《{title}——{L1.SUB}》<br>SDE教育学入门 · {no} · 王德生 · 德麦国际 SDE 学派</p>
  <a class="dlbtn" href="{pdfurl}" download>⬇ 下载 PDF</a>
  <div class="sz">含题头、摘要、正文与页码的印刷级精排版。如需翻页在线阅读，切换到「在线读 PDF」；如需网页版，切换到「网页长文」。</div>
</div></div>

<footer>
  <div>© 德麦国际 Demai International · SDE教育学入门 · <a href="/education/intro/">返回频道</a> · <a href="/browse/">sdeuniverses.com</a></div>
</footer>

<script>
document.querySelectorAll('.modebtn').forEach(function(b){{
  b.addEventListener('click',function(){{
    document.querySelectorAll('.modebtn').forEach(function(x){{x.classList.remove('on')}});
    document.querySelectorAll('.panel').forEach(function(x){{x.classList.remove('on')}});
    b.classList.add('on');
    var el=document.getElementById(b.dataset.m); if(el) el.classList.add('on');
    window.scrollTo(0,0);
  }});
}});
</script>
<script>var PDF_URL="{pdfurl}";{PDFJS}</script>
<script>window.WDS_READ={{selector:"article"}};</script>
<script src="/taste/wds-companion/wds-read.js?v=20260817c" defer></script>
<script src="/wds-mode.js?v=20260818b" defer></script>
<script src="/assets/sde-talk.js?v=20260817c" data-pv="1" defer></script>
</body>
</html>"""
    return slug, h, words

# ─────────────────────────── 频道页 ───────────────────────────
def build_channel(words1):
    cards = []
    for slug, no, title, blurb, st in LECTURES:
        if st == 'live':
            cards.append(f"""<a class="lec live" href="/education/intro/{slug}/">
  <span class="no">{no}</span>
  <h3>{title}</h3>
  <p>{blurb}</p>
  <span class="rd">网页长文 · 在线PDF · 下载PDF →</span>
</a>""")
        else:
            cards.append(f"""<div class="lec">
  <span class="no">{no}</span>
  <h3>{title}</h3>
  <p>{blurb}</p>
  <span class="soon">即将上线</span>
</div>""")
    grid = '\n'.join(cards)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SDE教育学入门 | 教育发生学 | SDE Universes</title>
<meta name="description" content="十二讲，把「教」这件事的底层假设拆开看一遍。从传道模式的八环链，到「在 E 中，经 D，成 S」，再到五个学科的具体做法与它明确不主张的边界。面向一线教师。">
<link rel="canonical" href="https://sdeuniverses.com/education/intro/">
<meta property="og:type" content="website">
<meta property="og:title" content="SDE教育学入门 · 十二讲">
<meta property="og:description" content="教育：从发现到发生的革命。面向一线教师的入门系列。">
<meta property="og:url" content="https://sdeuniverses.com/education/intro/">
<style>{CSS}
.chhero{{padding:4.2rem 1.5rem 2.6rem;text-align:center;background:linear-gradient(180deg,#FBF5EC 0%,#F5EFE0 100%);border-bottom:1px solid #E4D3BF}}
.chhero .eb{{font-size:.74rem;letter-spacing:.3em;color:{ACCENT};text-transform:uppercase;margin-bottom:1rem}}
.chhero h1{{font-family:'Playfair Display','Noto Serif SC',serif;font-size:2.5rem;font-weight:700;color:#2A2315;margin:0 0 .8rem;letter-spacing:.02em}}
.chhero .sub{{font-size:1.06rem;color:#6B5D47;max-width:44rem;margin:0 auto;line-height:1.95}}
.chhero .meta{{margin-top:1.4rem;font-size:.86rem;color:#98886C}}
.lead2{{max-width:44rem;margin:2.6rem auto 0;padding:0 1.5rem;font-size:1.05rem;line-height:2.05;color:#3A3125}}
.lead2 p{{margin:1.1rem 0}}
.lead2 b{{color:{ACCENT}}}
.qbox{{margin:1.8rem 0;padding:1.2rem 1.5rem;background:#FBF3EA;border:1px solid #E4D3BF;border-radius:8px;font-size:1.1rem;line-height:1.9;color:#3A2F22;text-align:center}}
.lecs{{max-width:62rem;margin:3rem auto 4rem;padding:0 1.5rem;display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:1.1rem}}
.lec{{display:block;text-decoration:none;background:#FAF6EC;border:1px solid #E4D3BF;border-top:3px solid #D8C6AE;border-radius:7px;padding:1.15rem 1.25rem}}
.lec.live{{border-top-color:{ACCENT};box-shadow:0 4px 16px rgba(140,90,43,.07)}}
.lec.live:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(140,90,43,.13);transition:.18s}}
.lec .no{{display:block;font-size:.72rem;letter-spacing:.14em;color:{ACCENT};font-weight:600;margin-bottom:.45rem}}
.lec h3{{font-family:'Noto Serif SC',serif;font-size:1.08rem;font-weight:600;color:#2A2315;margin:0 0 .5rem;line-height:1.55}}
.lec p{{font-size:.9rem;color:#6B5D47;line-height:1.8;margin:0}}
.lec .rd{{display:inline-block;margin-top:.7rem;font-size:.8rem;color:{ACCENT};font-weight:600}}
.lec .soon{{display:inline-block;margin-top:.7rem;font-size:.76rem;color:#A89880;background:#F0E8D3;padding:.15rem .55rem;border-radius:3px}}
.backbar{{max-width:62rem;margin:0 auto 3rem;padding:0 1.5rem;text-align:center}}
.backbar a{{display:inline-block;margin:0 .4rem;padding:.5rem 1.1rem;border:1px solid #E4D3BF;border-radius:5px;color:#6B5D47;text-decoration:none;font-size:.9rem}}
.backbar a:hover{{border-color:{ACCENT};color:{ACCENT}}}
</style>
</head>
<body>
{NAV}
<header class="chhero">
  <div class="eb">{CH_EN}</div>
  <h1>SDE教育学入门</h1>
  <p class="sub">十二讲，把「教」这件事的底层假设拆开看一遍。面向一线教师，不需要任何预备知识。</p>
  <div class="meta">王德生 · 德麦国际 SDE 学派 · 教育发生学 · 频道开设于 2026 年 8 月</div>
</header>

<div class="lead2">
  <p>本频道只处理一个问题：<b>我们说「教」的时候，究竟默认了什么。</b></p>

  <div class="qbox">为什么「讲得最清楚」的那一节课，<br>学生未必学得最好？</div>

  <p>这个现象每一位教师都遇到过。它之所以令人困惑，是因为它与我们对教学的默认理解相冲突——而那套默认理解，可以被完整地写出来：知识是客观世界的特征，被发现，被传播，被写进教材，被学生接受、消化、吸收，最后与旧知识重组。八个环节，一环扣一环。</p>

  <p>这条链逻辑严整，<b>正因严整而极少被质疑</b>。本频道第一讲把它逐环写出来，标明每一环悄悄承诺了什么，再逐环去敲；此后各讲给出替代方案与它在课堂上的具体做法。</p>

  <p>需要预先说明两件事。<b>其一，本系列不主张「不许讲授」</b>——讲授是极其高效的手段，且有大量研究支持；本系列处理的从来不是「要不要讲」，而是「什么时候讲」。<b>其二，本系列提供的是设计语汇与诊断，不是新的实证结果</b>；凡说「这样上课更好」，读者都应读作一个可检验的设计假设，其证据来自各讲所引的文献，而不是来自本系列。</p>

  <p>这两条会在第一讲的第十六、十七、十八节被正面处理，也会在第十二讲被再讲一遍。它们不是免责声明，是本系列愿意被推翻的方式。</p>
</div>

<div class="lecs">
{grid}
</div>

<div class="backbar">
  <a href="/education/">← 教育发生学 · 栏目首页</a>
  <a href="/education/ai-era/">AI时代的教育</a>
  <a href="/education/sio-classics/">SIO教育学修订文库</a>
  <a href="/education/from-students/">频道 · 来自学员专栏</a>
</div>

<footer>
  <div>© 德麦国际 Demai International · SDE教育学入门 · <a href="/browse/">sdeuniverses.com</a></div>
</footer>
<script src="/wds-mode.js?v=20260818b" defer></script>
</body>
</html>"""

# ─────────────────────────── 挂进 /education/ ───────────────────────────
def wire_education():
    p = os.path.join(EDU, 'index.html')
    h = read(p)

    # ① nav-bar-sub 加锚点（插在 #edu-ai-era 链接之前）
    anchor_a = '<a href="#edu-ai-era"'
    assert anchor_a in h, 'nav-bar-sub 未找到 #edu-ai-era 锚点'
    new_a = '<a href="#edu-intro"><span class="zh-only">SDE教育学入门</span><span class="en-only">Intro</span></a>\n        '
    h = h.replace(anchor_a, new_a + anchor_a, 1)

    # ② 区块：插在 #edu-ai-era 区块之前
    blk_anchor = '<div class="block" id="edu-ai-era">'
    assert blk_anchor in h, '未找到 #edu-ai-era 区块'
    block = f"""<div class="block" id="edu-intro">
        <div class="block-head"><span class="block-num">新栏</span><h2 class="block-title"><span class="zh-only">SDE教育学入门 · 十二讲</span><span class="en-only">SDE Pedagogy · An Introduction</span></h2></div>
        <p class="block-desc zh-only">王德生 · 面向一线教师的入门频道 · 频道开设于 2026 年 8 月</p>
        <p class="block-desc en-only">Wang Desheng · An introductory channel for classroom teachers</p>
        <a class="art" href="/education/intro/">
          <span class="k">频道 · 十二讲</span>
          <b>教育：从发现到发生的革命</b>
          <span class="d">「师者，传道」——「传」这个字要求先有一样已经做好的东西，在别处，等着被搬过来。十二讲把这条八环链逐环拆开，标明每一环悄悄承诺了什么，再逐环去敲；并给出五个学科的具体做法与它明确不主张的边界。第一讲已上线，含三种阅读模式。</span>
          <span class="rd">进入频道 →</span>
        </a>
      </div>

      """
    h = h.replace(blk_anchor, block + blk_anchor, 1)
    tagcheck(h, '/education/index.html')
    write(p, h)

# ─────────────────────────── 主流程 ───────────────────────────
def main():
    print('① 第一讲')
    slug, page, words = build_lecture()
    tagcheck(page, f'intro/{slug}/index.html')
    assert '正在载入精排 PDF' in page and 'id="dl"' in page and 'id="web"' in page, '三读面板不全'
    write(os.path.join(CH, slug, 'index.html'), page)
    print(f'  正文 {words:,} 汉字')

    print('② 频道页')
    ch = build_channel(words)
    tagcheck(ch, 'intro/index.html')
    write(os.path.join(CH, 'index.html'), ch)

    print('③ 挂进 /education/')
    wire_education()

    print('\n完成。PDF 待生成：tools/build_pdf_from_page.py')

if __name__ == '__main__':
    main()
