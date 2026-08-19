# -*- coding: utf-8 -*-
"""把 prereg.md 发布为 /books/m/92/prereg/，并在落地页与 text/ 目录页各插一条入口。幂等。"""
import os, re, html as H

os.chdir('/home/claude/b90')
SITE = '/home/claude/site/public'
NO = '92'
TITLE = '谁来陪伴我？'
PDF = '谁来陪伴我.pdf'
import sys
SRC = sys.argv[1] if len(sys.argv)>1 else 'prereg.md'
SLUG = sys.argv[2] if len(sys.argv)>2 else 'prereg'
raw = open(SRC, encoding='utf-8').read()
raw = re.sub(r'\*\*(.+?)\*\*', r'§B§\1§/B§', raw)          # 先保护粗体
blocks = [b.strip() for b in raw.split('\n\n') if b.strip()]


def inline(t):
    t = H.escape(t)
    t = t.replace('§B§', '<b>').replace('§/B§', '</b>')
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t


def md_table(b):
    rows = []
    for line in b.split('\n'):
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if all(set(c) <= set('-: ') for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return ''
    out = ['<table>']
    for i, r in enumerate(rows):
        tag = 'th' if i == 0 else 'td'
        out.append('<tr>' + ''.join(f'<{tag}>{inline(c)}</{tag}>' for c in r) + '</tr>')
    out.append('</table>')
    return '\n'.join(out)


body, title_txt, sub = [], None, None
for b in blocks:
    if b.startswith('# '):
        title_txt = b[2:].strip(); continue
    if b.startswith('### '):
        body.append('<h3>%s</h3>' % inline(b[4:].strip())); continue
    if b.startswith('## '):
        if sub is None and not b[3:].strip().startswith(('〇', '一', '二')):
            sub = b[3:].strip(); continue
        body.append('<h2>%s</h2>' % inline(b[3:].strip())); continue
    if b.startswith('|'):
        body.append(md_table(b)); continue
    if b.startswith('> '):
        q = ' '.join(l.lstrip('> ').strip() for l in b.split('\n'))
        body.append('<blockquote><p>%s</p></blockquote>' % inline(q)); continue
    if b.startswith('---'):
        body.append('<hr>'); continue
    if b.startswith('- ') or re.match(r'^\d+\. ', b):
        items = ''.join('<li>%s</li>' % inline(re.sub(r'^(- |\d+\. )', '', l.strip()))
                        for l in b.split('\n') if l.strip())
        body.append('<ul>%s</ul>' % items); continue
    if b.startswith('*') and b.endswith('*'):
        body.append('<p class="note">%s</p>' % inline(b.strip('*'))); continue
    body.append('<p>%s</p>' % inline(b.replace('\n', '')))

CSS = """<style>
:root{--bg:#0A1220;--fg:#E6EDF4;--dim:#8CA0B4;--gold:#C9A227;--mint:#8CE8C8;--line:#1C2E42;--card:#111C2C}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.95 "Noto Serif CJK SC","Songti SC",Georgia,serif}
a{color:var(--gold);text-decoration:none}a:hover{text-decoration:underline}
.bar{position:sticky;top:0;background:rgba(10,18,32,.94);backdrop-filter:blur(8px);
border-bottom:1px solid var(--line);padding:11px 20px;display:flex;gap:16px;flex-wrap:wrap;
font-size:13.5px;align-items:center}
.wrap{max-width:800px;margin:0 auto;padding:30px 22px 80px}
h1{font-size:27px;line-height:1.45;margin:14px 0 6px;font-weight:700;color:var(--mint)}
.sub{color:var(--dim);font-size:16px;margin-bottom:8px}
.meta{color:var(--dim);font-size:13.5px;margin-bottom:26px;font-family:"Noto Sans CJK SC",sans-serif}
h2{font-size:18.5px;color:var(--gold);margin:38px 0 12px;font-weight:700;
border-top:1px solid var(--line);padding-top:18px}
h3{font-size:15.5px;color:#B5C6D6;margin:26px 0 9px;font-weight:700}
p{margin:0 0 15px;text-align:justify}
blockquote{margin:18px 0;padding:13px 17px;border-left:3px solid var(--gold);
background:var(--card);color:#E4DECE}
blockquote p{margin:0}
table{width:100%;border-collapse:collapse;margin:6px 0 22px;font-size:13.5px}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{color:var(--gold);background:var(--card)}
ul{padding-left:22px}li{margin:0 0 9px;text-align:justify}
hr{border:0;border-top:1px solid var(--line);margin:30px 0}
code{font-family:"Noto Sans Mono CJK SC",Menlo,monospace;font-size:13.5px;color:var(--mint)}
.note{color:var(--dim);font-size:14px}
.foot{margin-top:56px;color:var(--dim);font-size:12.5px;text-align:center}
</style>"""

BAR = (f'<div class="bar"><a href="/books/m/{NO}/">← 专著首页</a>'
       f'<a href="/books/m/{NO}/text/">目录</a>'
       f'<a href="/books/m/{NO}/text/ap4/">附录四 · 判错清单排序</a>'
       f'<a href="/books/m/{NO}/{PDF}">⬇ 下载全书 PDF</a>'
       f'<span style="color:var(--dim)">德麦国际专著第 {NO} 号</span></div>')

page = (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{H.escape(title_txt)} · 一份可执行的预注册 · {TITLE} 第 {NO} 号</title>'
        f'<meta name="description" content="《谁来陪伴我？》第九章核心命题的可执行预注册：同成品—同接受项—异删除分支。含四条并存假设、变量操作化、样本量与功效、盲法、六道可行性门、八种结果的路由表与伦理条款。本书希望这一条被执行。">'
        f'{CSS}</head><body>{BAR}<div class="wrap">'
        f'<h1>{H.escape(title_txt)}</h1>'
        f'<div class="sub">{H.escape(sub or "")}</div>'
        f'<div class="meta">《谁来陪伴我？》（德麦国际专著第 {NO} 号）第九章核心命题的检验设计 · '
        f'附录二第九条 · 状态：<b>未执行</b> · 可自由使用、修改与再发布</div>'
        + '\n'.join(body) +
        f'<div class="foot">© 德麦国际出版社 · 王德生 ＋ Claude《{TITLE}》· 专著第 {NO} 号</div>'
        f'</div></body></html>')
import hashlib
_sha = hashlib.sha256(open(SRC, 'rb').read()).hexdigest()
page = page.replace('<div class="foot">',
    '<!--PREREG-SHA--><hr><p class="note">本文定稿的 SHA-256（对源文 <code>'
    + H.escape(os.path.basename(SRC)) + '</code> 计算，不含本行）：<br>'
    '<code style="word-break:break-all">' + _sha + '</code><br>'
    '任何改动都会改变这个值。执行者若修改本文，请重新计算并连同旧值一并公布——'
    '按停止规则一节，旧版全文须保留。</p><div class="foot">', 1)

DST = os.path.join(SITE, 'books/m', NO, SLUG)
os.makedirs(DST, exist_ok=True)
open(os.path.join(DST, 'index.html'), 'w', encoding='utf-8').write(page)
print('预注册页', len(page), '字节')

# ---- 落地页与目录页入口（幂等） ----
MARK = '<!-- PREREG -->' if SLUG == 'prereg' else '<!-- PREREG2 -->'
LP = os.path.join(SITE, 'books/m', NO, 'index.html')
h = open(LP, encoding='utf-8').read()
if MARK not in h:
    anchor = '<h2>本书不给行动清单</h2>'
    assert anchor in h, '落地页锚点不在'
    if SLUG == 'prereg':
        ins = (MARK + '\n<h2>一份已经写好的预注册</h2>\n'
               '<p>附录二那二十四条里，第九条最值得先做——它不需要十年追踪，周期以周计，'
               '而它一旦失败，第九章须整章撤销、枢纽章主式里的 s 项随之删除。</p>\n'
               '<p>这一条的<b>完整预注册已经写好并公开</b>：四条并存假设、变量操作化、样本量与功效、'
               '盲法与停止规则、六道可行性门、<b>八种结果分别改写本书哪一节的路由表</b>，以及伦理条款。'
               '它由本书的编写者所写，因而把每一个自由度提前钉死——'
               '<b>任何被改紧的版本都优先于本版。</b></p>\n'
               f'<div class="btns"><a class="btn" href="/books/m/{NO}/prereg/">'
               '📋 同成品—同接受项—异删除分支 · 一份可执行的预注册</a></div>\n')
    else:
        ins = (MARK + '\n<h2>另外六条：一份语料、两次访谈、一份日志</h2>\n'
               '<p>附录四标为 ★ 的那六条不需要招募伴侣。按材料而不是按章号重排之后，'
               '会看见一件本书写的时候没注意到的事：<b>六条里有三条共用同一份历时语料</b>——'
               '"陪伴"的语义收窄（第三章）、有效道歉形式要件的抬升（第八章）、'
               '凝结窗的坍缩（第五章），一次取数可以同时判决。</p>\n'
               '<p>方案里改正了本书原来写错的一条：第六章那条判错方式原写作"按使用强度分组比较"，'
               '<b>而组间比较因选择效应无论结果如何都不能判决</b>，已改为个体内滞后设计，'
               '并把判决量落在<b>交互项</b>上——本书的机制不是"渠道减少开口"，'
               '是"渠道切断了积压与开口之间的联系"。</p>\n'
               f'<div class="btns"><a class="btn" href="/books/m/{NO}/prereg2/">'
               '📋 六条 ★ 级判错方式的可执行方案</a></div>\n')
    h = h.replace(anchor, ins + anchor, 1)
    open(LP, 'w', encoding='utf-8').write(h)
    print('落地页入口已插:', SLUG)
else:
    print('落地页入口已存在，跳过:', SLUG)

TP = os.path.join(SITE, 'books/m', NO, 'text', 'index.html')
t = open(TP, encoding='utf-8').read()
if ('/%s/' % SLUG) not in t:
    anchor = '<div class="foot">'
    assert anchor in t
    label = ('《同成品—同接受项—异删除分支》· 附录二第九条的可执行预注册'
             if SLUG == 'prereg' else
             '《一份语料、两次访谈、一份日志》· 六条 ★ 级判错方式的可执行方案')
    ins = (f'<p style="margin-top:14px;font-size:14px;color:#8CA0B4">附：'
           f'<a href="/books/m/{NO}/{SLUG}/">{label}</a></p>')
    t = t.replace(anchor, ins + anchor, 1)
    open(TP, 'w', encoding='utf-8').write(t)
    print('目录页入口已插:', SLUG)
else:
    print('目录页入口已存在，跳过:', SLUG)
