import json,html
from weasyprint import HTML
d=json.load(open('public/books/m/482/unit/learning.json'))
e=html.escape
css='@page{size:A4;margin:22mm 20mm}body{font:11pt/1.9 "Noto Serif CJK SC",serif;color:#222}h1{font-size:24pt;margin:60mm 0 4mm}h2{font-size:14pt;border-bottom:1px solid #999;padding-bottom:2mm;margin:0 0 4mm}.t{page-break-before:always}.k{color:#8a6a1c;font-size:9.5pt;letter-spacing:.1em}.box{border:1px solid #bbb;height:34mm;margin:2mm 0 4mm}.s{font-size:9pt;color:#666}p{margin:2mm 0}'
b=['<h1>《风水发生学》学习包</h1><p>空间与人的共生智慧 · 邬燕琴著 · 王德生指导 · 德麦国际专著第482号 · ISBN 979-8-90690-173-6</p><p>三十个学习单元：先答，带问阅读，再答，再检验，留下自己的修订。学习任务为配套设计，不是著者原文或已验证量表。线上版可封存初答、保留复答版本、带着材料进入智能问对：sdeuniverses.com/books/m/482/agent/learning.html</p><p class="s">本书不给吉凶预测，不替任何一户人家断风水；身体或心里的难处真的大了，请找医生或心理咨询师。</p>']
for t in d['tasks']:
    b.append(f'<div class="t"><div class="k">{e(d["parts"][t["part"]-1])}</div><h2>{t["lesson"]:02d} · {e(t["chapterTitle"])}</h2><p><b>本题</b>　{e(t["question"])}</p><p class="k">初答（先写，封存）</p><div class="box"></div><p><b>读后再看：检验追问</b>　{e(t["checkpoint"])}</p><p class="k">复答 / 我的理解与异议</p><div class="box"></div><p class="s">原文：{e(t["sourceUrl"])}</p></div>')
HTML(string='<meta charset="utf-8"><style>'+css+'</style>'+''.join(b)).write_pdf('public/books/m/482/downloads/fengshui-fashengxue-learning-v1.0.pdf')
