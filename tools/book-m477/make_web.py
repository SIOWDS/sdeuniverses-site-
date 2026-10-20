#!/usr/bin/env python3
"""第 475 号：由 build_book 的 HTML 和阅读版 PDF 书签，生成 text.html 与 toc-reader.json。"""
import json, re, sys, fitz
from pathlib import Path
H, PDF, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
T, SUB, NO, V = '发现的发生学', '发现是怎样被发生出来的', 477, '20261020b'
SLUG = 'faxian-de-fasheng'
ISBN = '979-8-90690-168-2'
h = H.read_text()
body = h[h.index('<body>') + 6:h.rindex('</body>')]
# 去掉扉页与目录页，目录改成网页目录
body = re.sub(r'<section class="titlepage">.*?</section>', '', body, flags=re.S)
m = re.search(r'<section class="fsec toc".*?</section>', body, re.S)
tocsec = m.group(0); body = body.replace(tocsec, '')
items = re.findall(r'<li class="(\w+)"><span class="t">(.*?)</span><span class="d"></span><span class="n">⟦a:(\w+)⟧</span></li>', tocsec)
for _, _, i in items:
    assert 'id="%s"' % i in body, i
li = ''.join('<li class="%s"><a href="#%s">%s</a></li>' % ({'part': 'p', 'chap': 'c'}.get(k, 'f'), i, t) for k, t, i in items)
body = re.sub(r'<section class="chapter label"', '<section class="chapter"', body)
han = len(re.findall(r'[一-鿿]', body))
css = """:root{--paper:#fbf8f0;--ink:#2d2d2d;--navy:#1f3a5f;--gold:#b08a3c;--dim:#8a8578;--line:#e4dccb;--soft:#f3eee1}
html.dark{--paper:#121518;--ink:#e3dfd6;--navy:#9fc0e6;--gold:#d9b45c;--dim:#8e949a;--line:#2a3036;--soft:#1a1f24}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:18px/2 "Noto Serif CJK SC","Songti SC",serif}
#prog{position:fixed;top:0;left:0;height:3px;background:var(--gold);z-index:9}
.bar{position:sticky;top:0;display:flex;gap:1rem;align-items:center;padding:.6rem 1rem;background:var(--paper);border-bottom:1px solid var(--line);font:14px sans-serif;z-index:5}
.bar a{color:var(--navy);text-decoration:none}.bar .sp{flex:1}.bar button{background:none;border:1px solid var(--line);color:var(--navy);border-radius:4px;padding:.2rem .6rem;cursor:pointer}
.wrap{max-width:46rem;margin:0 auto;padding:1rem 1.2rem 4rem}
.hero{text-align:center;padding:2rem 0}.hero img{width:200px;max-width:60%;box-shadow:0 4px 18px rgba(0,0,0,.25)}.hero h1{color:var(--navy);margin:1rem 0 .2rem}.hero p{margin:.2rem 0;color:var(--dim)}
details.toc{border:1px solid var(--line);border-radius:6px;padding:.6rem 1rem;margin:1rem 0;font:15px/1.9 sans-serif}details.toc summary{cursor:pointer;color:var(--navy)}
details.toc ul{list-style:none;padding:0}details.toc li.p{font-weight:700;margin-top:.6rem}details.toc li.c{padding-left:1.2rem}details.toc a{color:var(--ink);text-decoration:none}
section{margin:3rem 0}p{margin:0 0 .9em;text-indent:2em;text-align:justify}
h1.fs-title,h1.part-title,h2.chap-title{color:var(--navy);line-height:1.5}h2.chap-title{font-size:1.5rem;margin:.2rem 0}
.chap-label,.part-label{color:var(--gold);font:700 .85rem sans-serif;letter-spacing:.3em}.fs-sub{color:var(--gold)}
.rule{width:3rem;height:2px;background:var(--gold);margin:.8rem 0 1.5rem}
h3.sec{color:var(--navy);font-size:1.12rem;margin:2rem 0 .6rem}h3.sec .dia{color:var(--gold);margin-right:.4em}h3.subhead{color:var(--navy)}
.ledger,.takeaway,.think,.verdict{background:var(--soft);border-left:3px solid var(--gold);padding:.6rem 1rem;margin:1.2rem 0}
.ledger .lab,.takeaway .lab,.think .lab{display:block;font:700 .75rem sans-serif;color:var(--gold);letter-spacing:.3em}
.ledger p,.takeaway p,.think p,.verdict p{text-indent:0;margin:.2rem 0}.takeaway p{color:var(--navy);font-weight:700}.verdict p{color:var(--navy)}
table{border-collapse:collapse;width:100%;font:15px/1.7 sans-serif;margin:1rem 0}th{background:var(--navy);color:#fff;padding:.4rem .6rem;text-align:left}td{border-bottom:1px solid var(--line);padding:.4rem .6rem;vertical-align:top}
table.cp th{background:none;color:var(--dim);font-weight:400;width:5rem}.cp-title{text-align:center;letter-spacing:.6em;color:var(--navy);font-weight:700}.cp-notes p{text-indent:0;font-size:.85rem;color:var(--dim)}
p.bib{text-indent:-2em;padding-left:2em;font-size:.9rem;line-height:1.8}p.item{text-indent:0}.ls{line-height:1.9}
.foot{text-align:center;color:var(--dim);font:14px sans-serif;margin-top:4rem}.foot a{color:var(--navy)}
@media(max-width:600px){body{font-size:17px}}"""
page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全文网页阅读 · {T} · 德麦国际专著第 {NO} 号</title>
<meta name="description" content="《{T}——{SUB}》全文网页版。王德生 著，德麦国际专著第 {NO} 号，约 {han/10000:.0f} 万汉字。">
<meta name="tier" content="L0"><link rel="canonical" href="https://sdeuniverses.com/books/m/{NO}/text/">
<style>{css}</style></head><body><div id="prog"></div>
<div class="bar"><a href="/books/m/{NO}/">← 书籍详情</a><a href="/books/m/{NO}/read.html">在线翻页</a><a href="/books/m/{NO}/{SLUG}-print.pdf?v={V}" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>
<div class="wrap"><div class="hero"><img src="/books/m/{NO}/cover.jpg?v={V}" alt="封面"><h1>{T}</h1><p>{SUB}</p>
<p>王德生 著 · 德麦国际专著第 {NO} 号 · ISBN {ISBN} · 约 {han/10000:.0f} 万汉字</p></div>
<details class="toc" open><summary>目录</summary><ul>{li}</ul></details>
{body}
<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{NO}/">书籍详情</a> · <a href="/books/m/{NO}/read.html">在线翻页</a></div></div>
<script>(function(){{var p=document.getElementById('prog');addEventListener('scroll',function(){{var h=document.documentElement;p.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}},{{passive:true}});
var sizes=[16,17,18,20,22],k=2;try{{var s=localStorage.getItem('bk{NO}-fs');if(s)k=+s;if(localStorage.getItem('bk{NO}-dark')==='1')document.documentElement.classList.add('dark');}}catch(e){{}}
function ap(){{document.body.style.fontSize=sizes[k]+'px';}}ap();
document.getElementById('fs').onclick=function(){{k=(k+1)%sizes.length;ap();try{{localStorage.setItem('bk{NO}-fs',k)}}catch(e){{}}}};
document.getElementById('th').onclick=function(){{var on=document.documentElement.classList.toggle('dark');try{{localStorage.setItem('bk{NO}-dark',on?'1':'0')}}catch(e){{}}}};}})();</script></body></html>"""
(OUT / 'text.html').write_text(page)
# 翻页目录
d = fitz.open(str(PDF)); outline = d.get_toc()
main = next(pg for l, t, pg in outline if t.startswith('导论'))
toc = [{'t': '出版信息', 'p': '', 'g': 4, 'l': 1}]
for l, t, pg in outline:
    if t == '目录': continue
    toc.append({'t': t.replace('　', ' '), 'p': str(pg - main + 1) if pg >= main else '', 'g': pg, 'l': l})
(OUT / 'toc-reader.json').write_text(json.dumps({'toc': toc, 'offset': main}, ensure_ascii=False))
print('web ok han', han, 'main', main, 'toc', len(toc))
