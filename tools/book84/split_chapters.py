# -*- coding: utf-8 -*-
"""第 84 号：给网页版每一章做三读（① 网页长文 ② 在线翻页 ③ 下载本章 PDF）。

章级 PDF **从该章自己的 text 页重新渲染**，不是从全书 PDF 切页：
切页会把全书的完整字体嵌进每一个分册（实测 13 章共 18MB），
重渲染只嵌入该章用到的字形（约 5MB），且与网页长文同源，
任何一次正文订正都会同时落到网页与 PDF 两份上。
全书页码仍标在页面上，供与正本对照。
幂等：章页入口条已存在则跳过；PDF 与 read 页每次重出。
"""
import json, os, re, html as H
from weasyprint import HTML
from pypdf import PdfReader

SITE = '/home/claude/site/public'
BASE = f'{SITE}/books/m/84'
BOOK = '越顺利，越没有你的位置'
NO = '84'
PMAP = json.load(open('/home/claude/b84/pagemap.json', encoding='utf-8'))

PRINT_CSS = """@page{size:A4;margin:22mm 20mm 20mm 20mm;
 @bottom-center{content:counter(page);font-family:"Noto Serif CJK SC";font-size:9pt;color:#8A8272}}
@page :first{@bottom-center{content:none}}
body{font-family:"Noto Serif CJK SC",serif;font-size:10.6pt;line-height:1.75;color:#23201A}
.series{font-size:8.5pt;letter-spacing:.24em;color:#6B7A8C;margin:0 0 9pt}
h1{font-size:19pt;margin:0 0 6pt;line-height:1.35;color:#16202C}
.src{font-size:9pt;color:#8A8272;border-top:1px solid #D8D2C4;border-bottom:1px solid #D8D2C4;
 padding:6pt 0;margin:0 0 15pt}
h2{font-size:13.4pt;color:#2B3B50;margin:17pt 0 7pt;border-bottom:1px solid #E0DAD0;
 padding-bottom:4pt;page-break-after:avoid}
h3{font-size:11.4pt;color:#3A4A60;margin:12pt 0 5pt;page-break-after:avoid}
p{margin:0 0 8.5pt;text-align:justify;text-indent:2em}
blockquote{margin:10pt 0;padding:8pt 12pt;border-left:3px solid #C8A45C;background:#F6F3EC}
blockquote p{text-indent:0;margin:0}
table{width:100%;border-collapse:collapse;margin:0 0 10pt;font-size:9pt}
th,td{border:1px solid #D8D2C4;padding:5pt 6pt;text-align:left;vertical-align:top}
th{background:#F2EFE8}
.tail{margin-top:16pt;padding-top:8pt;border-top:1px solid #D8D2C4;font-size:8.6pt;
 color:#8A8272;line-height:1.7;text-indent:0}"""

ORDER = [
    ('pub', '出版信息'), ('au', '作者介绍'), ('qy', '前言'), ('dd', '导读'),
    ('dl', '导论为什么读数一切正常，而人不对劲'),
    ('b1', '第一编主语位被移走'),
    ('c01', '第一章主语不再是个人'), ('c02', '第二章一次成功由谁承载'),
    ('c03', '第三章自我可以被完美绕过'),
    ('sn', '枢纽章信到了，人不在收件的位置上'),
    ('b2', '第二编阻力被拿走'),
    ('c04', '第四章被工艺除去的那道阻力'), ('c05', '第五章善失去了自己的语法'),
    ('c06', '第六章熄灭它的不是暴力，是拥抱'),
    ('b3', '第三编评估从两侧同时收窄'),
    ('c07', '第七章带着全部信念盖下的那个章'), ('c08', '第八章越审越不能改'),
    ('c09', '第九章裁判席本身就是干扰'),
    ('hz', '合章同一个动作的两端'),
    ('b4', '第四编还剩下的那一注'),
    ('c10', '第十章押进去就拿不回来的那一部分'), ('c11', '第十一章蚀先于生'),
    ('jy', '结语把地址写回来'), ('ref', '参考书目'),
    ('ap1', '附录一选目协议全文与十一章清单'), ('ap2', '附录二十一章读数速查表'),
    ('ap3', '附录三判错清单'), ('fd', '封底'),
]
SPLIT = {'c01', 'c02', 'c03', 'sn', 'c04', 'c05', 'c06', 'c07', 'c08', 'c09', 'hz', 'c10', 'c11'}

starts = [(s, PMAP[k]) for s, k in ORDER]
TOTAL = 343
spans = {}
for i, (s, p0) in enumerate(starts):
    p1 = starts[i + 1][1] - 1 if i + 1 < len(starts) else TOTAL
    spans[s] = (p0, p1)

MARK = '<!-- CHAPTER-READS -->'
done = []
for slug in [s for s, _ in ORDER if s in SPLIT]:
    p0, p1 = spans[slug]
    page = f'{BASE}/text/{slug}/index.html'
    h = open(page, encoding='utf-8').read()
    title = re.search(r'<h1>(.*?)</h1>', h, re.S).group(1)
    inner = h[h.index('</h1>') + 5:]
    inner = inner[:inner.index('<div class="nav2">')]
    inner = re.sub(r'<!-- CHAPTER-READS -->.*?</div>', '', inner, flags=re.S)

    name = f'm84-{slug}.pdf'
    doc = (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
           f'<style>{PRINT_CSS}</style></head><body>'
           f'<div class="series">SDE UNIVERSES · 德麦国际专著第 {NO} 号 · 单章分册</div>'
           f'<h1>{title}</h1>'
           f'<div class="src">《{BOOK}》· 王德生 ＋ Claude 编 · '
           f'本章在全书中为第 {p0}–{p1} 页 · ISBN 979-8-90690-018-0</div>'
           f'{inner}'
           f'<p class="tail">本分册取自《{BOOK}》（德麦国际专著第 {NO} 号）。'
           f'全书 343 页，含前言、导读、导论、四编十一章、枢纽章、合章、结语、参考书目与三则附录；'
           f'本章的判据与划界须与枢纽章、合章一并读。'
           f'全书网页版：sdeuniverses.com/books/m/{NO}/text/</p>'
           f'</body></html>')
    HTML(string=doc).write_pdf(f'{BASE}/{name}')
    n = len(PdfReader(f'{BASE}/{name}').pages)

    rd = (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
          f'<meta name="viewport" content="width=device-width,initial-scale=1">'
          f'<title>{title} · 在线翻页 · {BOOK} · 德麦国际专著第 {NO} 号</title>'
          f'<style>html,body{{margin:0;height:100%;background:#0B0E14}}'
          f'header{{height:56px;background:#121722;display:flex;align-items:center;'
          f'justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;'
          f'font-size:14px;border-bottom:1px solid #222836;color:#E6E8EE;gap:12px;flex-wrap:wrap}}'
          f'header a{{color:#D6AC60;text-decoration:none}}'
          f'iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>'
          f'<body><header><a href="/books/m/{NO}/text/{slug}/">‹ 返回网页长文</a>'
          f'<span>分册 {n} 页 · 全书第 {p0}–{p1} 页</span>'
          f'<a href="/books/m/{NO}/{name}" download>⬇ 下载本章</a></header>'
          f'<iframe src="/books/m/{NO}/{name}#view=FitH"></iframe></body></html>')
    open(f'{BASE}/text/{slug}/read.html', 'w', encoding='utf-8').write(rd)

    if MARK not in h:
        bar = (MARK + '<div style="border:1px solid var(--line);padding:11px 14px;margin:0 0 22px;'
               'font-size:13.5px;line-height:1.85">本章三读：<b>① 网页长文</b>（本页） · '
               f'<a href="/books/m/{NO}/text/{slug}/read.html">② 在线翻页</a> · '
               f'<a href="/books/m/{NO}/{name}" download>③ 下载本章 PDF（{n} 页）</a>'
               f'　<span style="color:var(--dim)">全书第 {p0}–{p1} 页</span></div>')
        h = h.replace('</h1>', '</h1>' + bar, 1)
        open(page, 'w', encoding='utf-8').write(h)
    done.append((slug, n, os.path.getsize(f'{BASE}/{name}') // 1024))

for s, n, kb in done:
    print(f'{s}: {n} 页 · {kb} KB')
print('分册合计 %.1f MB' % (sum(kb for _, _, kb in done) / 1024))
