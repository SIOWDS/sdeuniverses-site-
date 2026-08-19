#!/usr/bin/env python3
# 给专著章页插入「白话释义」盒子 + 生成附录·白话术语表页 + 挂入口。幂等。
import json,re,sys,os,html

ROOT='/home/claude/site/public/books/m'
GUARD='<!-- BAIHUA -->'

def box(items, dim='--dim', line='--line', am='--gold'):
    ps=''.join(f'<p style="margin:.55em 0"><b>{t}</b>　{d}</p>' for t,d in items)
    return (f'{GUARD}<div style="border:1px solid var({line});border-left:3px solid var({am});'
            f'padding:14px 17px;margin:0 0 26px;font-size:14.5px;line-height:1.9;background:rgba(255,255,255,.02)">'
            f'<p style="margin:.2em 0 .8em"><b>白话释义 · 本章新造的概念</b>　'
            f'<span style="color:var({dim})">（白话层，只帮助理解，不构成本章的论证与证据）</span></p>'
            f'{ps}</div>')

def insert(path, blk):
    s=open(path,encoding='utf-8').read()
    if GUARD in s:                      # 幂等：先清旧块再插新块
        s=re.sub(re.escape(GUARD)+r'<div .*?</div></div>','',s,flags=re.S)
        s=re.sub(re.escape(GUARD)+r'<div [^>]*>(?:(?!</div>).)*?(?:<p[^>]*>.*?</p>)+</div>','',s,flags=re.S)
    m=re.search(r'<h2[ >]',s)
    if not m:
        m=re.search(r'<h3[ >]',s)
    if not m:
        print('  !! no heading anchor:',path); return False
    s=s[:m.start()]+blk+s[m.start():]
    open(path,'w',encoding='utf-8').write(s)
    return True

def main(cfg):
    d=json.load(open(cfg,encoding='utf-8'))
    b=d['book']; vars_=d.get('vars',{})
    ok=0
    for slug,(title,items) in d['chapters'].items():
        p=f'{ROOT}/{b}/text/{slug}/index.html'
        if not os.path.exists(p): print('  missing',p); continue
        if insert(p, box(items,**vars_)): ok+=1; print('  +',slug,len(items),'terms')
    print(f'book {b}: {ok} chapters patched')

if __name__=='__main__': main(sys.argv[1])
