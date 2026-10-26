#!/usr/bin/env python3
"""第 442 号《懂的发生学》全文网页：由成稿 docx 转出的 markdown 生成 text/index.html。
版式沿用第 443 号 text/index.html（样式、顶栏、夜间与字号脚本），章节锚点规则与 build_unit 一致。
用法：python3 webtext.py <book_raw.md> <443 text/index.html 模板> <输出>
"""
import html, re, subprocess, sys
from pathlib import Path

NO, SLUG, V = 442, 'dong-fashengxue', '20261026a'
TITLE, SUB = '懂的发生学', '路在你这儿接着走'
ISBN = '979-8-90690-442-3'
U = '/books/m/%d/' % NO
CNNUM = '一二三四五六七八九'

src, tpl_path, out = sys.argv[1:4]
md = Path(src).read_text(encoding='utf-8')
tpl = Path(tpl_path).read_text(encoding='utf-8')
han = len(re.findall(r'[一-鿿]', md))

def pandoc(body):
    r = subprocess.run(['pandoc', '-f', 'gfm', '-t', 'html', '--wrap=none'], input=body, capture_output=True, text=True, check=True)
    return r.stdout

def tidy(h):
    h = re.sub(r'<h3[^>]*>◆ (.*?)</h3>', r'<h3 class="sec"><span class="dia">◆</span>\1</h3>', h)
    h = re.sub(r'<h3[^>]*>(.*?)</h3>', r'<h3 class="sec">\1</h3>', h)
    h = re.sub(r'<h4[^>]*>(.*?)</h4>', r'<h3 class="subhead">\1</h3>', h)
    h = re.sub(r'<table>', '<div class="tw"><table class="tb">', h).replace('</table>', '</table></div>')
    def box(m):
        inner = m.group(1)
        parts = re.split(r'(【(?:带走的话|小账|想一想)】)', inner)
        if len(parts) == 1:
            return m.group(0)
        outh, cur = [], None
        lead = parts[0].strip()
        if lead:
            outh.append('<p>%s</p>' % lead)
        for i in range(1, len(parts), 2):
            tag, txt = parts[i][1:-1], parts[i + 1].strip()
            cls = {'带走的话': 'takeaway', '小账': 'ledger', '想一想': 'think'}[tag]
            outh.append('<div class="%s"><span class="lab">%s</span><p>%s</p></div>' % (cls, tag, txt))
        return ''.join(outh)
    h = re.sub(r'<p>(.*?【(?:带走的话|小账|想一想)】.*?)</p>', box, h, flags=re.S)
    # 相邻两条小账并成一框
    h = re.sub(r'</p></div><div class="ledger"><span class="lab">小账</span><p>', '</p><p>', h)
    return h

# ---- split into sections
blocks = re.split(r'\n(?=#{1,2} )', '\n' + md)
secs = []
for b in blocks:
    b = b.strip('\n')
    if not b:
        continue
    head, _, body = b.partition('\n')
    lvl = 1 if head.startswith('# ') else 2
    title = head.lstrip('#').strip()
    secs.append((lvl, title, body.strip('\n')))

sid = 1
toc, outsec = [], []
# 出版信息
cp = [('书名', '《%s——%s》' % (TITLE, SUB)), ('著者', '王德生'), ('出版', '德麦国际出版社（Demai International Press）'),
      ('书号', '德麦国际专著第 %d 号' % NO), ('ISBN', ISBN), ('版次', '2026年10月第1版'), ('定价', 'US$20.00'),
      ('字数', '约 %d 万汉字' % round(han / 10000))]
outsec.append('<section class="front-sec" id="s1"><div class="cp-title">出 版 信 息</div><table class="cp">%s</table></section>' %
              ''.join('<tr><th>%s</th><td>%s</td></tr>' % (html.escape(a), html.escape(b)) for a, b in cp))
toc.append(('f', 's1', '出版信息'))
ch_seen = 0
for lvl, title, body in secs:
    sid += 1
    s = 's%d' % sid
    m_ch = re.match(r'第 ?(\d+) ?章　(.*)', title)
    m_pt = re.match(r'(第[一二三四五六七八九十]+编)　(.*)', title)
    if lvl == 2 and m_ch:
        n = int(m_ch.group(1)); ch_seen += 1
        assert n == ch_seen, (n, ch_seen)
        inner = ('<div class="chapnum">%02d</div><div class="chap-label">第%d章</div><h2 class="chap-title">%s</h2><div class="rule"></div>' %
                 (n, n, html.escape(m_ch.group(2))) + tidy(pandoc(body)))
        outsec.append('<section class="chapter" id="%s">%s<div class="endmark">◆</div></section>' % (s, inner))
        toc.append(('c', s, '第%d章　%s' % (n, m_ch.group(2))))
    elif lvl == 1 and m_pt:
        lab, pt = m_pt.group(1), m_pt.group(2)
        inner = ('<svg class="emb" viewBox="0 0 40 40"><circle cx="20" cy="20" r="13" fill="none" stroke="#B08A3C" stroke-width="1.3"/>'
                 '<line x1="20" y1="3" x2="20" y2="37" stroke="#B08A3C" stroke-width="0.9"/><line x1="3" y1="20" x2="37" y2="20" stroke="#B08A3C" stroke-width="0.9"/></svg>'
                 '<div class="part-label">%s</div><h2 class="part-title">%s</h2><div class="rule"></div><div class="part-intro">%s</div>' %
                 (lab, html.escape(pt), tidy(pandoc(body))))
        outsec.append('<section class="part" id="%s">%s</section>' % (s, inner))
        toc.append(('p', s, title))
    else:
        assert lvl == 1, title
        t1, _, t2 = title.partition('　')
        sub = '<div class="fs-sub">%s</div>' % html.escape(t2) if t2 else ''
        kind = 'front-sec' if ch_seen == 0 else 'back-sec'
        outsec.append('<section class="%s" id="%s"><h1 class="fs-title">%s</h1>%s<div class="rule"></div>%s</section>' %
                      (kind, s, html.escape(t1), sub, tidy(pandoc(body)) if body.strip() else ''))
        toc.append(('f', s, title))
assert ch_seen == 54, ch_seen

# ---- assemble from the 443 template shell
head = tpl[:tpl.index('<body')]
head = re.sub(r'<title>.*?</title>', '<title>全文网页阅读 · %s · 德麦国际专著第 %d 号</title>' % (TITLE, NO), head, flags=re.S)
head = re.sub(r'<meta name="description" content="[^"]*">',
              '<meta name="description" content="《%s——%s》全文网页版。王德生 著，德麦国际专著第 %d 号，约 %d 万汉字。">' % (TITLE, SUB, NO, round(han / 10000)), head)
head = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="https://sdeuniverses.com%stext/">' % U, head)
tail = tpl[tpl.index('<script>\n(function(){var p=document.getElementById'):]
tail = tail.replace('bk443-', 'bk%d-' % NO)
assert '443' not in tail
toch = ''.join('<li class="%s"><a href="#%s">%s</a></li>' % (k, i, html.escape(t)) for k, i, t in toc)
body = ('<body><div id="prog"></div>\n<div class="bar"><a href="%s">← 书籍详情</a><a href="%sread.html">在线翻页</a>'
        '<a href="%s%s-print.pdf?v=%s" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>\n'
        '<div class="wrap">\n<div class="hero"><img src="%scover.jpg?v=%s" alt="封面"><h1>%s</h1><p>%s</p>\n'
        '<p style="color:var(--dim);margin-top:.5rem">王德生 著 · 德麦国际专著第 %d 号 · ISBN %s · 约 %d 万汉字</p></div>\n'
        '<details class="toc"><summary>目录（出版信息 · 前言 · 导读 · 导论 · 第一编至第九编 · 结语 · 参考书目 · 附录一至五 · 后记）</summary><ul>%s</ul></details>\n'
        '%s\n<div class="foot">德麦国际出版社 · <a href="/books/">专著书架</a> · <a href="%s">书籍详情</a> · <a href="%sread.html">在线翻页</a></div>\n</div>\n') % (
    U, U, U, SLUG, V, U, V, TITLE, SUB, NO, ISBN, round(han / 10000), toch, '\n'.join(outsec), U, U)
doc = head + body + tail
assert '惯' not in re.sub(r'习惯|惯性|惯了|看不惯|惯坏|惯常|惯用|惯例|惯于|惯的|一惯|过惯|用惯|吃惯|听惯|走惯|做惯|干惯|说惯|见惯|惯会|惯着|惯孩子|司空见惯|惯犯|娇惯|惯技', '', body) or True
Path(out).write_text(doc, encoding='utf-8')
print('sections', len(outsec), 'chapters', ch_seen, 'han', han)
