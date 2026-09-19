#!/usr/bin/env python3
"""Build missing page-turning readers from the checked-in bookshelf source map.
Existing handwritten readers are preserved: only books with a `reader` map are built.
"""
from pathlib import Path
from urllib.parse import urlsplit
import json,html
ROOT=Path(__file__).resolve().parents[1]
VERSION='20260919-reader-v1'
DATA=json.loads((ROOT/'public/books/catalog.json').read_text())
def esc(value):return html.escape(str(value),quote=True)
def build(book):
 cfg={'id':book['id'],'title':book['title'],**book['reader']}
 assert cfg['format'] in ('pdf','html') and cfg['sources']
 assert book['flipUrl']==book['readUrl']
 options=''.join('<option value="'+str(i)+'">'+esc(s['title'])+'</option>' for i,s in enumerate(cfg['sources']))
 fallback=''.join('<li><a href="'+esc(s['url'])+'">'+esc(s['title'])+'</a></li>' for s in cfg['sources'])
 pdfscript='<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js" defer></script>' if cfg['format']=='pdf' else ''
 alternate='<a class="secondary-nav" href="'+esc(book['chapterUrl'])+'">章节阅读</a>' if book.get('chapterUrl') else ''
 config=json.dumps(cfg,ensure_ascii=False).replace('<','\\u003c')
 out='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>在线翻页阅读 · '''+esc(book['title'])+''' | SDE Universes</title><meta name="description" content="'''+esc(book['title'])+'''：在线翻页阅读，支持页码跳转与目录选择。"><meta name="reader-version" content="'''+VERSION+'''"><link rel="canonical" href="'''+esc(book['flipUrl'])+'''"><link rel="stylesheet" href="/books/reader/reader.css?v='''+VERSION+'''">'''+pdfscript+'''<script src="/books/reader/reader.js?v='''+VERSION+'''" defer></script></head><body>
<header class="reader-header"><div><h1>'''+esc(book['title'])+'''</h1><p>'''+esc(' · '.join(book['authors']))+''' · 德麦国际出版社 · 在线翻页阅读</p></div><nav aria-label="阅读导航"><a href="/books/">返回书架</a>'''+alternate+'''<a class="secondary-nav" href="'''+esc(book['detailUrl'])+'''">书籍详情</a></nav></header>
<div class="toolbar" aria-label="翻页控制"><button id="prev" type="button" disabled>‹ 上一页</button><label class="page-number">第 <input id="pageInput" aria-label="页码" type="number" min="1" value="1" disabled> / <span id="totalPages">…</span> 页</label><button id="next" type="button" disabled>下一页 ›</button><label class="source-picker">'''+('分册' if cfg['format']=='pdf' else '目录')+'''<select id="chapter" aria-label="选择章节或分册" disabled>'''+options+'''</select></label><button id="smaller" type="button" aria-label="缩小" disabled>A−</button><button id="larger" type="button" aria-label="放大" disabled>A＋</button></div>
<main><div id="reader-error" class="reader-error" role="alert" hidden><p id="error-message"></p><button id="retry" type="button">重新载入</button> <a id="error-source" href="'''+esc(cfg['sources'][0]['url'])+'''">打开原文</a></div><div id="stage" class="stage"><div id="html-paper" class="html-paper" hidden><div id="text-viewport" class="text-viewport"><article id="text-flow" class="text-flow"></article></div></div><div id="pdf-paper" class="pdf-paper" hidden><canvas id="pdfCanvas" aria-label="当前书页"></canvas><div id="textLayer" class="textLayer"></div></div></div><div id="reader-status" class="reader-status" role="status" aria-live="polite">正在载入书页…</div><div class="reader-hint">上一页 / 下一页 · 输入页码跳转 · ← → 方向键翻页 · 自动记住阅读位置　<a id="source-link" class="source-link" href="'''+esc(cfg['sources'][0]['url'])+'''">原文</a></div><noscript><section class="source-fallback"><p>启用 JavaScript 即可翻页阅读，也可直接打开原文：</p><ol>'''+fallback+'''</ol></section></noscript></main>
<script type="application/json" id="reader-config">'''+config+'''</script></body></html>'''
 path=ROOT/('public'+urlsplit(book['flipUrl']).path)
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(out)
 return str(path.relative_to(ROOT))
if __name__=='__main__':
 paths=[build(b) for b in DATA['books'] if b.get('reader')]
 print('Built',len(paths),'complete-book readers.')
