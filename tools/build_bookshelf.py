#!/usr/bin/env python3
"""Build all bookshelf entrances from public/books/catalog.json (stdlib only)."""
from pathlib import Path
import json,html,collections
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'public/books/catalog.json').read_text())
BOOKS=DATA['books'];CATS=DATA['categories'];VERSION='20260919-bookshelf-v2'
assert len({b['id'] for b in BOOKS})==len(BOOKS)
assert len({b['detailUrl'] for b in BOOKS})==len(BOOKS)
assert all(not b.get('flipUrl') or b['readUrl']==b['flipUrl'] for b in BOOKS), 'Keep flip readers as the primary reading action'
def esc(x):return html.escape(str(x or ''),quote=True)
def card(b):
 title=esc(b['title']);detail=esc(b['detailUrl']);author=' · '.join(b['authors']);cat=CATS[b['category']]
 reading=b['readMode'];state={'full':'全文可读','preview':'试读版','info':'书籍介绍'}[reading]
 data={'id':b['id'],'title':b['title'],'number':b['number'] or '', 'category':b['category'],'reading':reading,'authors':json.dumps(b['authors'],ensure_ascii=False),'search':' '.join([b['title'],author,cat,b.get('description',''),b.get('isbn') or '',str(b['number'] or '')])}
 data['flip']='true' if b.get('flipUrl') else 'false'
 attrs=' '.join('data-'+k+'="'+esc(v)+'"' for k,v in data.items())
 cover='<span class="no-cover">'+title+'</span>'
 if b.get('coverUrl'):cover='<img src="'+esc(b['coverUrl'])+'" alt="" width="92" height="134" loading="lazy" decoding="async"><span class="no-cover" hidden>'+title+'</span>'
 action='<a class="read-button'+(' secondary' if reading=='info' else '')+'" href="'+esc(b.get('readUrl') or b['detailUrl'])+'" aria-label="'+title+'：'+esc(b['readLabel'])+'">'+esc(b['readLabel'])+'</a>'
 if b.get('chapterUrl'):action+='<a class="detail-button chapter-link" href="'+esc(b['chapterUrl'])+'" aria-label="'+title+'：章节阅读">章节阅读</a>'
 if b.get('readUrl') and b['readUrl']!=b['detailUrl']:action+='<a class="detail-button" href="'+detail+'" aria-label="'+title+'：书籍详情">详情</a>'
 if b.get('pdfUrl') and b['pdfUrl']!=b.get('readUrl'):action+='<a class="pdf-link" href="'+esc(b['pdfUrl'])+'" aria-label="'+title+'：'+('试读版 PDF' if reading=='preview' else 'PDF')+'">PDF ↗</a>'
 return '<article class="book" '+attrs+'><div class="book-main"><a class="cover" href="'+detail+'" tabindex="-1" aria-hidden="true">'+cover+'</a><div class="book-copy"><p class="book-tag"><span>'+esc(cat)+'</span><span class="ordinal">'+('#'+str(b['number']) if b['number'] else '')+'</span></p><h3><a href="'+detail+'">'+title+'</a></h3><p class="byline">'+esc(author)+'</p><p class="description">'+esc(b.get('description'))+'</p></div></div><div class="book-meta"><span class="reading-state '+reading+'">'+state+'</span><span class="format">'+('PDF 全本' if b.get('pdfUrl') and b['pdfUrl']==b.get('readUrl') else '网页 / PDF' if b.get('pdfUrl') and reading=='full' else '在线阅读' if reading=='full' else '摘要与导读' if reading=='info' else '在线试读')+'</span></div><div class="book-actions">'+action+'</div></article>'
def page(reading_house=False):
 counts=collections.Counter(b['category'] for b in BOOKS);authors=collections.Counter(a for b in BOOKS for a in b['authors']);modes=collections.Counter(b['readMode'] for b in BOOKS)
 chips='<button class="category" type="button" data-category-filter="all" data-label="全部图书" aria-pressed="true">全部<span>'+str(len(BOOKS))+'</span></button>'
 for k,label in CATS.items():chips+='<button class="category" type="button" data-category-filter="'+k+'" data-label="'+label+'" aria-pressed="false">'+label+'<span>'+str(counts[k])+'</span></button>'
 options='<option value="">全部作者</option>'+''.join('<option value="'+esc(a)+'">'+esc(a)+'</option>' for a,n in authors.most_common())
 nav='<a href="https://sdeuniverses.com/browse/">首页</a><a href="https://read.sdeuniverses.com/">读书馆</a><a class="current" href="https://sdeuniverses.com/books/" aria-current="page">专著书架</a>'
 if reading_house:nav='<a href="https://read.sdeuniverses.com/">读书馆</a><a href="https://read.sdeuniverses.com/club/">读书会</a><a class="current" href="https://sdeuniverses.com/books/">专著书架</a>'
 return '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>专著书架 · 德麦国际出版社 | SDE Universes</title><meta name="description" content="SDE专著与图书统一书架：按主题、作者、书名选择，直接阅读全文、试读版或查看书籍介绍。"><meta name="bookshelf-version" content="'''+VERSION+'''"><link rel="canonical" href="https://sdeuniverses.com/books/"><meta property="og:title" content="专著书架 · SDE Universes"><meta property="og:description" content="按主题与作者选书，找到想读的那一本。"><meta property="og:type" content="website"><meta property="og:url" content="https://sdeuniverses.com/books/"><link rel="stylesheet" href="https://sdeuniverses.com/books/bookshelf.css?v='''+VERSION+'''"><script src="https://sdeuniverses.com/books/bookshelf.js?v='''+VERSION+'''" defer></script></head>
<body><a class="skip" href="#book-grid">跳到图书</a><header class="topbar"><div class="wrap"><a class="brand" href="https://sdeuniverses.com/browse/">SDE Universes<small>德麦国际出版社</small></a><nav class="toplinks" aria-label="主导航">'''+nav+'''</nav></div></header>
<main class="wrap"><div class="heading"><div><div class="eyebrow">DEMAI INTERNATIONAL PRESS</div><h1>专著书架</h1><p>从一个问题出发，找到想读的那一本。</p></div><div class="shelf-total"><strong>'''+str(len(BOOKS))+'''</strong>部图书</div></div>
<section class="tools js-tools" aria-label="查找图书" hidden><div class="search-row"><div class="searchbox"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.8"/><path d="m16 16 4.5 4.5"/></svg><input type="search" id="book-search" aria-label="搜索书名、作者、关键词或ISBN" placeholder="搜索书名、作者、关键词或 ISBN" autocomplete="off"><button class="clear-search" type="button" id="clear-search" aria-label="清空搜索" hidden>×</button></div><label class="control" for="author-filter"><span>作者</span><select id="author-filter">'''+options+'''</select></label><label class="control" for="reading-filter"><span>阅读</span><select id="reading-filter"><option value="">全部图书</option><option value="flip">在线翻页（'''+str(sum(bool(b.get('flipUrl')) for b in BOOKS))+'''）</option><option value="full">全文可读（'''+str(modes['full'])+'''）</option><option value="preview">试读版（'''+str(modes['preview'])+'''）</option><option value="info">书籍介绍（'''+str(modes['info'])+'''）</option></select></label></div><div class="categories" role="group" aria-label="按主题筛选">'''+chips+'''</div></section>
<noscript><p class="no-js">下方列出全部图书，可直接点击阅读。启用 JavaScript 后可按主题与作者筛选。</p></noscript>
<div class="results-bar"><div class="result-left"><h2 id="result-title">全部图书</h2><span id="result-count" class="result-count" role="status" aria-live="polite">'''+str(len(BOOKS))+''' 部</span><button type="button" id="reset-filters" class="reset" hidden>清除筛选</button></div><div class="result-tools js-tools" hidden><label class="sort control" for="sort-books"><span>排序</span><select id="sort-books"><option value="latest">最新编号在前</option><option value="number">编号从小到大</option><option value="title">按书名排序</option></select></label><div class="view-toggle" role="group" aria-label="显示方式"><button type="button" data-view="grid" aria-pressed="true">书架</button><button type="button" data-view="list" aria-pressed="false">目录</button></div></div></div>
<div id="book-grid" class="book-grid">'''+''.join(card(b) for b in BOOKS)+'''</div>
<div id="empty-state" class="empty" hidden><h3>暂时没有符合条件的图书</h3><p>试试较短的关键词，或清除主题与作者筛选。</p><button id="empty-reset" type="button">查看全部图书</button></div><div class="load-area js-tools" hidden><button id="load-more" type="button" class="load-more">查看更多图书</button><div id="load-progress" class="load-progress"></div></div></main>
<footer><div class="wrap"><span>德麦国际出版社 · Demai International Press · Singapore</span><span>含专著与文学作品 · <a href="https://sdeuniverses.com/browse/">返回首页</a> · <a href="#">回到顶部</a></span></div></footer></body></html>'''
for name,reading_house in [('public/books/index.html',False),('public/monographs/index.html',False),('public/sites/read/library/index.html',True)]:
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(page(reading_house))
print('Built 3 bookshelf entrances,',len(BOOKS),'unique books.')
