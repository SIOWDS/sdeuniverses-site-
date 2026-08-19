#!/usr/bin/env python3
"""在目次页与落地页挂「附录 · 白话术语表」入口。幂等。"""
import json,sys,re
ROOT='/home/claude/site/public/books/m'
def run(cfg):
    d=json.load(open(cfg,encoding='utf-8')); b=d['book']
    href=f'/books/m/{b}/text/bh/'
    # 目次页：插在「封底」条之前，没有封底就插在目录 div 末尾
    p=f'{ROOT}/{b}/text/index.html'; s=open(p,encoding='utf-8').read()
    if href not in s:
        item=f'<a class="" href="{href}">附录 · 白话术语表</a>'
        m=re.search(r'<a class="[^"]*" href="[^"]*/fd/">[^<]*</a>',s)
        if m: s=s[:m.start()]+item+s[m.start():]
        else:
            i=s.rfind('</div><div class="foot">'); s=s[:i]+item+s[i:]
        open(p,'w',encoding='utf-8').write(s); print('  toc linked')
    # 落地页：加一条独立入口条
    p=f'{ROOT}/{b}/index.html'; s=open(p,encoding='utf-8').read()
    if '<!-- BAIHUA-ENTRY -->' not in s:
        bar=(f'<!-- BAIHUA-ENTRY --><div style="border:1px solid rgba(214,172,96,.5);border-left:3px solid #D6AC60;'
             f'padding:13px 16px;margin:26px 0 0;font-size:14px;line-height:1.85">'
             f'<b>白话层</b>　本书新造的每一个概念都配了一段白话解释：各章正文开头有「白话释义」小节，'
             f'全书汇总见 <a href="{href}">附录 · 白话术语表</a>。</div>')
        m=re.search(r'<section',s)
        i=m.start() if m else s.find('</h1>')+5
        s=s[:i]+bar+s[i:]
        open(p,'w',encoding='utf-8').write(s); print('  landing linked')
if __name__=='__main__': run(sys.argv[1])
