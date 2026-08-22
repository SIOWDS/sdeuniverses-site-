#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkthreeviews_articles.py —— 把「三视角图册」扫码原文搬回站内。

产出：
  · public/three-views/read/<id>/index.html   每篇一页：PDF.js 分页阅读 ＋ 纯文字版 ＋ 下载
  · public/three-views/read/<id>/<id>.pdf     文章本体（位图已按 150dpi 重压，文字层未动）
  · public/three-views/articles/index.html    166 篇总目，按二十篇分组

底料：tools/threeviews_articles.py（ARTICLES / BY_IMG），正文文本读 tools/threeviews_text/<id>.txt。

⚠ 三条纪律：
 1. 阅读页与 /books 的 read.html 是同一套 PDF.js 画法，但**壳是本栏自己的**（浅色纸本），
    不许把首页导航背进来 —— 与 mkthreeviews.py 同一条基本原则（2026-08-22 王德生定）。
 2. 每页同目录既有 index.html 又有 PDF：站内检索按「同目录页面 URL」收 PDF 正文，
    所以阅读页里**必须同时内嵌纯文字版**，否则 --reuse-pdf 增量重建时这篇会落在索引外。
 3. PDF 文件名用 ASCII（<id>.pdf），中文标题走 <a download> 属性，避免 URL 编码坑。

用法：python3 tools/mkthreeviews_articles.py [--dry-run]
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from threeviews_articles import ARTICLES as _RAW, BY_IMG  # noqa: E402

# 文件里的顺序按编号（编号必须稳定，见 threeviews_articles.py 的说明），
# 但读者看到的顺序按图号——否则后补的几篇会全堆在末尾。
ARTICLES = sorted(_RAW, key=lambda a: (a['img'], a['title']))
from threeviews_data import SECTIONS, NAMES              # noqa: E402

OUT = os.path.join(PUB, 'three-views')
TEXTDIR = os.path.join(HERE, 'threeviews_text')
AC = '#2C7FA8'

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Playfair+Display:wght@400;600&family=Noto+Serif+SC:wght@300;400;500;600'
         '&display=swap" media="print" onload="this.media=\'all\';this.onload=null">')

CSS = """<style>
:root{--bg:#F5EFE0;--card:#FAF6EC;--text:#2A2315;--text2:#6B5D47;--muted:#98886C;
 --border:rgba(138,104,23,.22);--border2:rgba(138,104,23,.12);--ac:%(AC)s}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);line-height:1.75;
 font-family:'Noto Serif SC',Georgia,serif;-webkit-text-size-adjust:100%%}
a{color:var(--ac)}
.tv-top{position:sticky;top:0;z-index:60;display:flex;align-items:center;
 justify-content:space-between;gap:.8rem;padding:.55rem 1.2rem;flex-wrap:wrap;
 background:rgba(245,239,224,.95);backdrop-filter:blur(10px);
 border-bottom:1px solid var(--border2)}
.tv-brand{display:flex;flex-direction:column;line-height:1.15;text-decoration:none;color:var(--ac)}
.tv-brand b{font-size:1rem;letter-spacing:.06em;font-weight:700}
.tv-brand span{font-family:'Playfair Display',Georgia,serif;font-size:.68rem;
 letter-spacing:.2em;color:var(--muted);text-transform:uppercase}
.tv-top nav{display:flex;align-items:center;gap:.3rem .9rem;flex-wrap:wrap;font-size:.88rem}
.tv-top nav a{color:var(--text2);text-decoration:none;white-space:nowrap}
.tv-top nav a:hover{color:var(--ac);text-decoration:underline;text-underline-offset:4px}
.tv-top nav a.cur{color:var(--ac);font-weight:700}
.tv-wrap{max-width:1180px;margin:0 auto;padding:0 1.6rem}
.tv-hd{padding:2.1rem 0 1.1rem;border-bottom:1px solid var(--border2)}
.tv-eyebrow{font-size:.78rem;letter-spacing:.22em;color:var(--ac);font-weight:700;
 text-transform:uppercase}
.tv-hd h1{font-size:1.95rem;line-height:1.3;margin:.5rem 0 .2rem;letter-spacing:.02em}
.tv-sub{color:var(--muted);font-size:.92rem;margin:0}
.tv-note{margin:1.6rem 0 0;padding:1rem 1.2rem;border-left:3px solid var(--ac);
 background:rgba(15,110,140,.05);font-size:.93rem;line-height:1.82}
.tv-foot{margin-top:3rem;padding:2rem 1.6rem 2.6rem;border-top:1px solid var(--border2);
 text-align:center;color:var(--muted);font-size:.85rem;line-height:1.9}
/* ── 阅读器 ── */
.bar{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;margin:1.4rem 0 .2rem}
.btn{background:var(--card);border:1px solid var(--border);color:var(--text2);
 padding:.42rem .85rem;border-radius:4px;font-size:.9rem;cursor:pointer;
 font-family:inherit;text-decoration:none;line-height:1.5}
.btn:hover:not(:disabled){border-color:var(--ac);color:var(--ac)}
.btn:disabled{opacity:.35;cursor:not-allowed}
.btn.dl{border-color:var(--ac);color:var(--ac)}
.pagebox{display:flex;align-items:center;gap:.35rem;font-size:.9rem;color:var(--text2)}
.pagebox input{width:3.6rem;background:#fff;border:1px solid var(--border);color:var(--text);
 padding:.36rem .3rem;border-radius:4px;text-align:center;font-family:inherit;font-size:.9rem}
.stage{display:flex;justify-content:center;padding:1rem 0 .5rem;min-height:50vh}
#page-wrap{position:relative;display:inline-block;line-height:0;background:#fff;
 border:1px solid var(--border2);border-radius:4px;overflow:hidden;
 box-shadow:0 12px 34px rgba(0,0,0,.10)}
canvas{display:block}
.textLayer{position:absolute;left:0;top:0;overflow:hidden;line-height:1;z-index:3;text-align:initial}
.textLayer span{color:transparent;position:absolute;white-space:pre;cursor:text;transform-origin:0 0}
.textLayer ::selection{background:rgba(44,127,168,.32)}
.loading{text-align:center;color:var(--muted);padding:4rem 1rem;font-size:1rem}
.spinner{width:34px;height:34px;border:3px solid rgba(44,127,168,.25);border-top-color:var(--ac);
 border-radius:50%%;margin:0 auto 1rem;animation:spin .9s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.err{text-align:center;color:#9B4A3A;padding:3rem 1rem;line-height:1.9}
.hint{text-align:center;color:var(--muted);font-size:.8rem;margin:.2rem 0 0}
details.plain{margin:2rem 0 0;border:1px solid var(--border2);border-radius:8px;
 background:var(--card);padding:.85rem 1.1rem}
details.plain summary{cursor:pointer;color:var(--ac);font-size:.95rem;font-weight:600}
details.plain .body{margin-top:1rem;white-space:pre-wrap;font-size:1rem;line-height:1.95;
 border-top:1px solid var(--border2);padding-top:1rem}
.tv-pager{display:flex;justify-content:space-between;gap:1rem;margin:2.2rem 0 0;font-size:.94rem}
.tv-pager a{text-decoration:none}
.tv-pager a:hover{text-decoration:underline;text-underline-offset:4px}
/* ── 总目 ── */
.grp{margin:2.4rem 0 0}
.grp h2{font-size:1.18rem;margin:0 0 .1rem;letter-spacing:.03em}
.grp .gs{color:var(--muted);font-size:.83rem}
.alist{margin:.9rem 0 0;padding:0;list-style:none;
 display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:.5rem .9rem}
.alist li{border:1px solid var(--border2);border-radius:7px;background:var(--card);
 padding:.55rem .8rem;font-size:.96rem}
.alist li a{text-decoration:none}
.alist li a:hover{text-decoration:underline;text-underline-offset:3px}
.alist li em{display:block;font-style:normal;color:var(--muted);font-size:.78rem;margin-top:.15rem}
@media(max-width:640px){.tv-wrap{padding:0 1rem}.tv-hd h1{font-size:1.5rem}
 .alist{grid-template-columns:1fr}}
</style>""" % {'AC': AC}

FOOT = """<footer class="tv-foot">
<p>《三视角图册》　发明 王德生　·　制作 马锦涛　|　扫码原文由王德生历年撰写</p>
<p>© 德麦国际　·　<a href="/three-views/">三视角专栏</a>　·　<a href="/browse/">爱思乐园 SDE Universes</a></p>
</footer>"""

FIT = ('<script src="/wds-mode.js?v=%s" defer></script>'
       % re.search(r'^stamp=(\S+)',
                   open(os.path.join(HERE, 'wds-mode.stamp'), encoding='utf-8').read(),
                   re.M).group(1))


def esc(s):
    return html.escape(s, quote=True)


def sec_of(img):
    for zh, slug, a, b in SECTIONS:
        if a <= img <= b:
            return zh, slug
    return '补遗', 'addenda'


def page_head(title, desc, canon):
    return ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="canonical" href="%s">\n'
            '<meta property="og:type" content="article">\n'
            '<meta property="og:title" content="%s">\n'
            '<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s">\n%s\n%s\n</head>'
            % (esc(title), esc(desc), canon, esc(title), esc(desc), canon, FONTS, CSS))


def topbar(links):
    return ('<header class="tv-top">\n<a class="tv-brand" href="/three-views/">'
            '<b>三视角图册</b><span>Three Views Atlas</span></a>\n<nav>%s</nav>\n</header>'
            % ''.join(links))


READER_JS = """<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
var PDF_URL="%(pdf)s", DOC_TITLE=%(title_js)s;
pdfjsLib.GlobalWorkerOptions.workerSrc="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
var pdfDoc=null,pageNum=1,rendering=false,pending=null,baseScale=1.3,curText="";
var canvas=document.getElementById('pdfCanvas'),ctx=canvas.getContext('2d');
var pageWrap=document.getElementById('page-wrap'),textLayer=document.getElementById('textLayer');
var $=function(i){return document.getElementById(i);};
function drawTextLayer(tc,vp){
  textLayer.innerHTML='';var frag=document.createDocumentFragment(),fix=[];
  tc.items.forEach(function(it){
    if(!it.str)return;
    var m=pdfjsLib.Util.transform(vp.transform,it.transform),fs=Math.hypot(m[2],m[3]);
    if(!fs)return;
    var ang=Math.atan2(m[1],m[0]),sp=document.createElement('span');
    sp.textContent=it.str;
    var css='left:'+m[4].toFixed(2)+'px;top:'+(m[5]-fs).toFixed(2)+'px;font-size:'+fs.toFixed(2)+'px;';
    if(Math.abs(ang)>0.01)css+='transform:rotate('+ang.toFixed(4)+'rad);';
    sp.style.cssText=css;frag.appendChild(sp);fix.push([sp,it.width*vp.scale,ang]);
  });
  textLayer.appendChild(frag);
  fix.forEach(function(w){
    var sp=w[0],target=w[1],ang=w[2];if(!target)return;
    var real=sp.getBoundingClientRect().width;
    if(real>1){var sx=target/real;if(sx>0.1&&sx<10){
      sp.style.transform=(Math.abs(ang)>0.01?('rotate('+ang.toFixed(4)+'rad) '):'')+'scaleX('+sx.toFixed(3)+')';}}
  });
}
function render(num){
  rendering=true;
  pdfDoc.getPage(num).then(function(page){
    var avail=($('stage').clientWidth||window.innerWidth)-24;
    var vp1=page.getViewport({scale:1}),s=baseScale;
    if(vp1.width*s>avail&&avail>120)s=avail/vp1.width;
    var vp=page.getViewport({scale:s}),ratio=Math.min(window.devicePixelRatio||1,2.5);
    canvas.width=Math.floor(vp.width*ratio);canvas.height=Math.floor(vp.height*ratio);
    canvas.style.width=vp.width+'px';canvas.style.height=vp.height+'px';
    pageWrap.style.width=vp.width+'px';pageWrap.style.height=vp.height+'px';
    ctx.setTransform(ratio,0,0,ratio,0,0);
    page.render({canvasContext:ctx,viewport:vp}).promise.then(function(){
      return page.getTextContent();
    }).then(function(tc){
      curText=tc.items.map(function(i){return i.str;}).join(' ').replace(/\\s+/g,' ').trim();
      drawTextLayer(tc,vp);rendering=false;
      if(pending!==null){var p=pending;pending=null;render(p);}
    });
    $('pageInput').value=num;$('prev').disabled=(num<=1);$('next').disabled=(num>=pdfDoc.numPages);
  });
}
// 载入失败后 pdfDoc 仍是 null：缩放键不走 go() 的守卫，这里必须自己挡住，
// 否则一按 ＋/− 就抛 TypeError，把错误提示旁边的按钮全变成哑弹。
function queue(n){if(!pdfDoc)return;if(rendering)pending=n;else render(n);}
function go(n){if(!pdfDoc)return;pageNum=Math.min(Math.max(1,n),pdfDoc.numPages);queue(pageNum);}
pdfjsLib.getDocument(PDF_URL).promise.then(function(pdf){
  pdfDoc=pdf;$('totalPages').textContent=pdf.numPages;$('pageInput').max=pdf.numPages;
  $('loading').style.display='none';$('page-wrap').style.display='inline-block';render(pageNum);
}).catch(function(err){
  $('loading').style.display='none';$('error').style.display='block';
  $('error').innerHTML='这一篇暂时无法在线分页显示。<br>你仍可 <a href="'+PDF_URL+'" target="_blank">直接打开或下载 PDF</a>，'
    +'或展开下方「纯文字版」阅读。<br><span style="font-size:12px">（'+err.message+'）</span>';
});
$('prev').onclick=function(){go(pageNum-1);};
$('next').onclick=function(){go(pageNum+1);};
$('pageInput').onchange=function(e){go(parseInt(e.target.value)||1);};
$('zoomIn').onclick=function(){baseScale=Math.min(baseScale+0.2,3);queue(pageNum);};
$('zoomOut').onclick=function(){baseScale=Math.max(baseScale-0.2,0.6);queue(pageNum);};
document.addEventListener('keydown',function(e){
  if(e.target&&(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'))return;
  if(e.key==='ArrowLeft')go(pageNum-1);
  if(e.key==='ArrowRight')go(pageNum+1);
});
window.addEventListener('resize',function(){clearTimeout(window._rz);
  window._rz=setTimeout(function(){queue(pageNum);},220);});
window.WDS_READ={title:DOC_TITLE,
  bodyEl:function(){return document.getElementById('page-wrap');},
  docTextFn:function(){return curText?('【'+DOC_TITLE+' · 第 '+pageNum+' 页 / 共 '
    +(pdfDoc?pdfDoc.numPages:'?')+' 页】\\n'+curText):'';}};
</script>
<script src="/taste/wds-companion/wds-read.js?v=20260817c" defer></script>"""


def build_reader(k, arts):
    a = arts[k]
    zh, slug = sec_of(a['img'])
    fig = NAMES.get(a['img'], '')
    pdf = '/three-views/read/%s/%s.pdf' % (a['id'], a['id'])
    txt = open(os.path.join(TEXTDIR, a['id'] + '.txt'), encoding='utf-8').read()
    lead = re.sub(r'\s+', ' ', txt[:110]).strip()
    desc = ('%s——王德生《三视角图册》第 %03d 图「%s」（%s）的扫码原文，共 %d 页。%s'
            % (a['title'], a['img'], fig, zh, a['pages'], lead))[:190]
    prev_a = ('<a href="/three-views/read/%s/">← 上一篇</a>' % arts[k - 1]['id']) if k > 0 \
        else '<a href="/three-views/articles/">← 文章总目</a>'
    next_a = ('<a href="/three-views/read/%s/">下一篇 →</a>' % arts[k + 1]['id']) \
        if k + 1 < len(arts) else '<a href="/three-views/articles/">回文章总目 →</a>'
    body = [
        page_head('%s · 三视角图册第 %03d 图' % (a['title'], a['img']), desc,
                  'https://sdeuniverses.com/three-views/read/%s/' % a['id']),
        '<body>',
        topbar(['<a href="/three-views/atlas/">三视角图册</a>',
                '<a href="/three-views/library/">三视角文章</a>',
                '<a href="/three-views/articles/">扫码原文</a>',
                '<a href="/three-views/%s/#g%03d">%s · 第 %03d 图</a>'
                % (slug, a['img'], esc(zh), a['img'])]
               + ['<a href="/three-views/%s/#g%03d">%s · 第 %03d 图</a>'
                  % (sec_of(m)[1], m, esc(sec_of(m)[0]), m) for m in a['also']]),
        '<main class="tv-wrap">', '<header class="tv-hd">',
        '<div class="tv-eyebrow">三视角图册 · 扫码原文</div>',
        '<h1>%s</h1>' % esc(a['title']),
        '<p class="tv-sub">对应第 %03d 图「%s」·&nbsp;%s　|　共 %d 页 · 约 %s 字　|　王德生</p>'
        % (a['img'], esc(fig), esc(zh), a['pages'], format(a['chars'], ',')),
        ('<div class="tv-note">%s。</div>' % esc(a['note'])) if a['note'] else '',
        '</header>',
        '<div class="bar">',
        '<button class="btn" id="prev" disabled>‹ 上一页</button>',
        '<div class="pagebox"><input id="pageInput" type="number" min="1" value="1">'
        '<span>/ <span id="totalPages">…</span></span></div>',
        '<button class="btn" id="next" disabled>下一页 ›</button>',
        '<button class="btn" id="zoomOut">−</button>',
        '<button class="btn" id="zoomIn">＋</button>',
        '<a class="btn dl" href="%s" download="%s.pdf">⬇ 下载 PDF</a>' % (pdf, esc(a['title'])),
        '<a class="btn" href="/three-views/%s/#g%03d">回到这张图</a>' % (slug, a['img']),
        '</div>',
        '<div class="stage" id="stage">',
        '<div id="loading" class="loading"><div class="spinner"></div>正在载入本篇…</div>',
        '<div id="page-wrap" style="display:none"><canvas id="pdfCanvas"></canvas>'
        '<div class="textLayer" id="textLayer"></div></div>',
        '<div id="error" class="err" style="display:none"></div>',
        '</div>',
        '<p class="hint">← → 方向键翻页 · 选中正文任意一句可问 WDS</p>',
        '<details class="plain"><summary>纯文字版（全文 %s 字，便于手机阅读、复制与站内检索）</summary>'
        '<div class="body">%s</div></details>' % (format(a['chars'], ','), esc(txt)),
        '<div class="tv-pager">%s%s</div>' % (prev_a, next_a),
        '</main>', FOOT,
        READER_JS % {'pdf': pdf, 'title_js': '"%s"' % a['title'].replace('"', '\\"')},
        FIT, '</body>', '</html>']
    return '\n'.join(body)


def build_index():
    n = len(ARTICLES)
    title = '三视角图册 · 扫码原文全部 %d 篇' % n
    desc = ('王德生《三视角图册》每张主图旁的扫码原文，%d 篇已全部搬回站内直读：'
            '可分页阅读、可下载 PDF、附纯文字版，不再跳转公众号。' % n)
    body = [page_head(title, desc, 'https://sdeuniverses.com/three-views/articles/'),
            '<body>',
            topbar(['<a href="/three-views/atlas/">三视角图册</a>',
                    '<a href="/three-views/library/">三视角文章</a>',
                    '<a class="cur">扫码原文</a>']),
            '<main class="tv-wrap">', '<header class="tv-hd">',
            '<div class="tv-eyebrow">Articles</div>',
            '<h1>扫码原文 · %d 篇</h1>' % n,
            '<p class="tv-sub">图册每张主图旁那枚二维码指向的文章，现已直接挂在站内　|　'
            '共 %d 篇 · 落在 %d 张图上 · 约 %s 万字</p>'
            % (n, len(BY_IMG), format(round(sum(a['chars'] for a in ARTICLES) / 10000))),
            '</header>',
            '<div class="tv-note">每一篇都能<b>在线分页翻阅</b>、<b>下载 PDF</b>，也附<b>纯文字版</b>。'
            '文章按它在图册里对应的那张图归位——先是图，再是那张图底下的话。</div>']
    for zh, slug, a, b in SECTIONS:
        rows = [x for x in ARTICLES
                if any(a <= m <= b for m in [x['img']] + x['also'])]
        if not rows:
            continue
        body.append('<div class="grp"><h2><a href="/three-views/%s/" '
                    'style="text-decoration:none">%s</a></h2>'
                    '<div class="gs">第 %d–%d 图 · %d 篇</div><ul class="alist">'
                    % (slug, esc(zh), a, b, len(rows)))
        for x in rows:
            n = next(m for m in [x['img']] + x['also'] if a <= m <= b)
            body.append('<li><a href="/three-views/read/%s/">%s</a>'
                        '<em>第 %03d 图 %s · %d 页%s</em></li>'
                        % (x['id'], esc(x['title']), n, esc(NAMES.get(n, '')),
                           x['pages'], '　·　' + esc(x['note']) if x['note'] else ''))
        body.append('</ul></div>')
    body += ['<div class="tv-pager"><a href="/three-views/library/">← 回三视角文章</a>'
             '<a href="/browse/">爱思乐园首页 →</a></div>',
             '</main>', FOOT, FIT, '</body>', '</html>']
    return '\n'.join(body)


def main():
    dry = '--dry-run' in sys.argv
    print('文章 %d 篇 · 落在 %d 张图 · PDF 合计 %.1f MB · 正文 %s 字'
          % (len(ARTICLES), len(BY_IMG), sum(a['bytes'] for a in ARTICLES) / 1e6,
             format(sum(a['chars'] for a in ARTICLES), ',')))
    if dry:
        return
    for k, a in enumerate(ARTICLES):
        d = os.path.join(OUT, 'read', a['id'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
            build_reader(k, ARTICLES))
    d = os.path.join(OUT, 'articles')
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(build_index())
    print('已写 %d 个阅读页 ＋ 1 个文章总目 →' % len(ARTICLES), OUT)


if __name__ == '__main__':
    main()
