#!/usr/bin/env python3
"""全文网页 text.html（样式取第 259 号全文页，与站上一致），分节 id 与 PDF 相同。"""
import html, re, sys
from pathlib import Path
import pdf as P
REPO = Path(sys.argv[1])
M, D = P.META, P.D
src = (REPO / 'public/books/m/259/text/index.html').read_text()
style = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
style += """
.ledger{background:var(--soft);border-left:3px solid var(--gold);padding:.9rem 1.1rem;margin:1.4rem 0;border-radius:4px;display:block}
.ledger .lab{display:block;font:700 .75rem sans-serif;color:var(--gold);letter-spacing:.3em;margin-bottom:.4rem}
.ledger p{text-indent:0;margin:.2rem 0;font-size:.95em}.ledger .lk{color:var(--navy);font-weight:700}
.endmark{text-align:center;color:var(--gold);margin:2rem 0 0}
.chapnum{font-size:2.6rem;color:var(--gold);opacity:.45;line-height:1;margin-top:1rem}.chap-label{margin:.3rem 0 .2rem}
.emb{width:44px;height:44px;display:block;margin:0 auto 1rem}
p.dlg{text-indent:0}p.sim,.simi{font-family:sans-serif;color:#8F7434;font-size:.84rem}p.sim{text-indent:0;border-left:2px solid #D9C39A;padding-left:.7rem}
p.bib{text-indent:-2em;padding-left:2em;font-size:.9rem;line-height:1.8;overflow-wrap:anywhere}
.fs-title.appx{font-size:1.4rem}h3.sec .dia{margin-right:.4em}h3.subhead{color:var(--navy);margin:1.6rem 0 .5rem}
table.cp th{background:none;color:var(--dim);font-weight:400;width:5rem}table.cp tr:nth-child(odd){background:var(--soft)}
table.tb{width:100%;border-collapse:collapse;font-size:.9rem}table.tb th{background:var(--navy);color:#fff;padding:.4rem .5rem;text-align:left}table.tb td{border-bottom:1px solid var(--line,#ddd);padding:.4rem .5rem;vertical-align:top}
.cp-title{text-align:center;letter-spacing:.6em;color:var(--navy);font-weight:700;margin:2rem 0 1rem}.cp-notes p{text-indent:0;font-size:.85rem;color:var(--dim)}
.epi{text-align:center;margin:3rem 0}.epi p{text-indent:0;text-align:center;color:var(--navy)}.epi .by{color:var(--dim);font-size:.9rem}
.part{text-align:center}.part-label{color:var(--gold);letter-spacing:.5em;font-weight:700}.daoyu{color:var(--gold);letter-spacing:.5em;font-size:.85rem;margin-bottom:.6rem}.part .rule{margin-left:auto;margin-right:auto}
.part-intro{text-align:left}
"""
secs = D['secs']; no = M['no']; v = M['version']; wan = D['wan']
toc = []
for i, s in enumerate(secs):
    if s['kind'] == 'cp':
        continue
    cls = {'part': 'p', 'chapter': 'c'}.get(s['kind'], 'f')
    toc.append('<li class="%s"><a href="#s%d">%s</a></li>' % (cls, i, P.inline(s['title'])))
body = []
for i, s in enumerate(secs):
    body.append(P.sec_html(i, s))
    if s['kind'] == 'cp':
        body.append('<div class="epi"><p>%s</p><p class="by">%s</p></div>' % tuple(D['epigraph']))
head = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全文网页阅读 · {M['title']} · 德麦国际专著第 {no} 号</title>
<meta name="description" content="《{M['title']}——{M['subtitle']}》全文网页版。{M['author']} 著，德麦国际专著第 {no} 号，约 {wan:.0f} 万字。">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="book_no" content="{no}"><link rel="canonical" href="https://sdeuniverses.com/books/m/{no}/text/">
<style>{style}</style></head><body><div id="prog"></div>
<div class="bar"><a href="/books/m/{no}/">← 书籍详情</a><a href="/books/m/{no}/read.html">在线翻页</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>
<div class="wrap">
<div class="hero"><img src="/books/m/{no}/cover.jpg?v={v}" alt="封面"><h1>{M['title']}</h1><p>{M['subtitle']}</p>
<p style="color:var(--dim);margin-top:.5rem">{M['author']} 著 · 德麦国际专著第 {no} 号 · ISBN {M['isbn']} · 约 {wan:.0f} 万字</p></div>
<details class="toc" open><summary>目录（出版信息 · 作者介绍 · 前言 · 导读 · 八编六十一章 · 结语 · 参考书目 · 附录三件）</summary><ul>{''.join(toc)}</ul></details>
"""
tail = f"""<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{no}/">书籍详情</a> · <a href="/books/m/{no}/read.html">在线翻页</a></div>
</div>
<script>
(function(){{var p=document.getElementById('prog');addEventListener('scroll',function(){{var h=document.documentElement;p.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}},{{passive:true}});
var sizes=[16,17,18,20,22],k=2;try{{var s=localStorage.getItem('bk{no}-fs');if(s)k=+s;var d=localStorage.getItem('bk{no}-dark');if(d==='1')document.documentElement.classList.add('dark');}}catch(e){{}}
function ap(){{document.body.style.fontSize=sizes[k]+'px';}}ap();
document.getElementById('fs').onclick=function(){{k=(k+1)%sizes.length;ap();try{{localStorage.setItem('bk{no}-fs',k)}}catch(e){{}}}};
document.getElementById('th').onclick=function(){{var on=document.documentElement.classList.toggle('dark');try{{localStorage.setItem('bk{no}-dark',on?'1':'0')}}catch(e){{}}}};}})();
</script></body></html>"""
(P.OUT / 'text.html').write_text(head + '\n'.join(body) + tail, encoding='utf-8')
print('web ok', len(head) + sum(map(len, body)))
