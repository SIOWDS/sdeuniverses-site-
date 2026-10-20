#!/usr/bin/env python3
"""由 unit/learning.json 生成学习包 PDF（weasyprint）：每章一页，含封存初答、读后追问、复答与迁移记录栏。
用法（仓库根目录）：python3 tools/book-m446/learning_pdf.py"""
import html, json
from weasyprint import HTML
d = json.load(open('public/books/m/446/unit/learning.json'))
e = html.escape
css = ('@page{size:A4;margin:20mm 20mm 22mm;@bottom-center{content:"第446卷 · 配套学习设计，不是能力认证 · " counter(page);font:8.5pt "Noto Sans CJK SC",sans-serif;color:#777}}'
       'body{font:10.8pt/1.85 "Noto Serif CJK SC",serif;color:#222}h1{font-size:25pt;margin:38mm 0 3mm;color:#1f3a5f}'
       'h2{font-size:14pt;border-bottom:1px solid #b08a3c;padding-bottom:2mm;margin:0 0 3mm;color:#1f3a5f}.t{page-break-before:always}'
       '.k{color:#8a6a1c;font-size:9.2pt;letter-spacing:.1em;font-family:"Noto Sans CJK SC",sans-serif}.box{border:1px solid #bbb;height:30mm;margin:1.5mm 0 3mm}'
       '.s{font-size:8.8pt;color:#666}p{margin:1.6mm 0}img{width:46mm;margin:6mm 0}')
b = ['<h1>《法律是谁？》学习包</h1><p>普通人都能明白的法律 · 高鹏著 · 德麦国际专著第446号 · ISBN 979-8-90690-177-4</p>'
     '<img src="public/books/m/446/cover.jpg">'
     '<p>导论、五编、结语，三十八个学习单元：先答，带问阅读，再答，迁移到自己的日子里，留下自己的修订。学习任务为配套设计，不是著者原文，不是标准答案，也不是已验证的量表。</p>'
     '<p>线上版可封存初答、保留复答版本、带着材料进入智能体「认话」：sdeuniverses.com/books/m/446/agent/learning.html</p>'
     '<p class="s">本书与本学习包不提供法律意见；遇到真实纠纷，请找当地有资质的专业人士。书中人物与场景为写作构造，不是史料，也不是判例。</p>']
for t in d['tasks']:
    part = d['parts'][t['part'] - 1]
    lab = part if part in ('两种人', '法治信仰') else part
    q, c = t['question'], t['checkpoint']
    b.append(f'<div class="t"><div class="k">{e(("导论" if t["part"]==1 else "结语" if t["part"]==7 else "第%d编" % (t["part"]-1)))} · {e(lab)}</div>'
             f'<h2>{t["lesson"]:02d} · {e(t["title"])}</h2><p class="s">{e(t["chapterTitle"])}</p>'
             f'<p class="k">本题 · 先答（封存，不覆盖）</p><p>{e(q)}</p><div class="box"></div>'
             f'<p class="k">读后追问与复答</p><p>{e(c)}</p><div class="box"></div>'
             f'<p class="k">迁移记录：做了什么 · 观察到什么 · 没有改善也写下来</p><div class="box" style="height:20mm"></div>'
             f'<p class="s">原文：{e(t["sourceUrl"])}</p></div>')
import os
os.makedirs('public/books/m/446/downloads', exist_ok=True)
HTML(string='<meta charset="utf-8"><style>' + css + '</style>' + ''.join(b), base_url='.').write_pdf('public/books/m/446/downloads/falv-shi-shei-learning-v1.0.pdf')
print('ok')
