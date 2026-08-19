#!/usr/bin/env python3
"""生成 text/bh/ 附录·白话术语表，并在目次页与落地页挂入口。幂等。"""
import json,re,sys,os
ROOT='/home/claude/site/public/books/m'
def build(cfg):
    d=json.load(open(cfg,encoding='utf-8')); b=d['book']; bt=d['title']
    tpl=open(f'{ROOT}/{b}/text/{d.get("tpl","ap3")}/index.html',encoding='utf-8').read()
    head=tpl[:tpl.find('<div class="wrap">')]
    head=re.sub(r'<title>.*?</title>',f'<title>附录 · 白话术语表 · {bt} · 德麦国际专著第 {b} 号</title>',head,flags=re.S)
    foot=tpl[tpl.rfind('<div class="foot">'):]
    rows=[]
    for slug,(title,items) in d['chapters'].items():
        rows.append(f'<h2 style="font-size:17px;margin:1.8em 0 .4em">{title}</h2>')
        for t,x in items:
            rows.append(f'<p style="margin:.5em 0"><b>{t}</b>　{x}</p>')
    body=(f'<div class="wrap"><h1>附录 · 白话术语表</h1>'
          f'<p>本书每一章都命名了一样此前没有名字的东西。下面按章列出，每条先用一句话说它是什么，再给一个日常例子，'
          f'最后指出它最容易被误当成的那个旧词。<b>这一层只帮助理解，不构成本书的论证与证据</b>——'
          f'真正的定义、判据与检验，仍以各章正文为准。</p>'
          + ''.join(rows) +
          f'<div class="nav2"><a href="/books/m/{b}/text/">‹ 返回目次</a></div>')
    os.makedirs(f'{ROOT}/{b}/text/bh',exist_ok=True)
    open(f'{ROOT}/{b}/text/bh/index.html','w',encoding='utf-8').write(head+body+foot)
    n=sum(len(i[1]) for i in d['chapters'].values())
    print(f'book {b}: glossary page with {n} terms')
    return n
if __name__=='__main__': build(sys.argv[1])
