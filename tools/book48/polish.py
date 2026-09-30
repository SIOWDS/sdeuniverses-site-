#!/usr/bin/env python3
"""精选本打磨层：在 compile.py 抽出的 HTML 块上做排版级修复，文字论断不改。

1. 表格复原：原稿网页把表格压成了乱序文字；按内容与全本原版 PDF 中的表格匹配（orig_tables.json），
   换回真正的表格；清掉单元格里的字距空格，合并跨页续表，去掉重复表头，标题行改为表题。
2. 符号清理：表情符号标记删去；「📌 金句收束：」一类标签另起一段并加粗；✅❌⭕ 删去；
   1️⃣ → ①；⟹ → ⇒；下标数字改普通数字；⋅ → ·。
3. 编号句：被标成小标题的「1. ……。」编号句改为编号条目。
4. 个别修补：第 7 章的字符画示意图改为三栏小表。
"""
import json, re
from bs4 import BeautifulSoup
import tmatch

MARKS = '📌🔑✨📍👉🔶✳🔹◉✅❌⭕✦📎🌊🧭📚🧩📖🔰🌱'
LABEL_MARKS = '📌🔑✨'
KEYCAP = {'1': '①', '2': '②', '3': '③', '4': '④', '5': '⑤', '6': '⑥', '7': '⑦', '8': '⑧', '9': '⑨'}
SUBS = str.maketrans('₀₁₂₃₄₅₆₇₈₉', '0123456789')
CJK = r'[　-〿一-鿿＀-￯]'


def clean_text(s):
    s = re.sub(r'([1-9])️?⃣', lambda m: KEYCAP[m.group(1)], s)
    s = s.replace('️', '')
    s = re.sub('[' + MARKS + r']\s*', '', s)
    s = re.sub(r'_{3,}', '', s)
    s = s.replace('⟹', '⇒').replace('⋅', '·').translate(SUBS)
    return s


def cell(s):
    s = clean_text(s or '').strip()
    return re.sub(r'(?<=' + CJK + r')\s+(?=' + CJK + r')', '', s)


def table_html(rows, caption=None):
    rows = [[cell(c) for c in r] for r in rows]
    n = max(len(r) for r in rows)
    rows = [r + [''] * (n - len(r)) for r in rows]
    head = '<tr>' + ''.join(f'<th>{c}</th>' for c in rows[0]) + '</tr>'
    body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows[1:])
    cap = f'<p class="tcap"><b>{caption}</b></p>' if caption else ''
    return cap, f'<table><thead>{head}</thead><tbody>{body}</tbody></table>'


def restore_tables(blocks):
    ms = tmatch.find_matches(blocks)
    if not ms:
        return blocks
    # 合并相邻且表头相同的续表
    groups = []
    for i, j, ti, s in ms:
        rows = [r[:] for r in tmatch.T[ti]['rows']]
        if groups and groups[-1]['j'] == i and len(rows[0]) == len(groups[-1]['rows'][0]):
            g = groups[-1]
            hdr = [cell(c) for c in g['rows'][0]]
            if [cell(c) for c in rows[0]] == hdr:
                rows = rows[1:]
            g['rows'] += rows
            g['j'] = j
            continue
        groups.append({'i': i, 'j': j, 'rows': rows})
    out, k = [], 0
    for g in groups:
        out += blocks[k:g['i']]
        rows, cap = g['rows'], None
        first = [cell(c) for c in rows[0]]
        if sum(1 for c in first if c) == 1 and len(rows) > 2:
            cap, rows = first[0], rows[1:]
            # 标题行之后若紧跟两个表头相同的分表，去掉重复表头
        hdr = [cell(c) for c in rows[0]]
        rows = [rows[0]] + [r for r in rows[1:] if [cell(c) for c in r] != hdr]
        c, t = table_html(rows, cap)
        if c:
            out.append(c)
        out.append(t)
        k = g['j']
    out += blocks[k:]
    return out


def fix_text_nodes(html):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup.find_all(string=True):
        new = clean_text(str(node))
        if new != str(node):
            node.replace_with(new)
    return str(soup)


def split_labels(html):
    """「……。📌 金句结尾：……」拆成两段；段首的短标签「金句收束：」加粗。"""
    t0 = next(iter(BeautifulSoup(html, 'html.parser').children))
    if t0.name != 'p' or t0.get('class'):
        return [html]
    text = t0.decode_contents()
    parts = re.split('(?=[' + LABEL_MARKS + '])', text)
    parts = [p for p in parts if p.strip()]
    out = []
    for p in parts:
        had = p[:1] in LABEL_MARKS
        p = clean_text(p).strip()
        if not p:
            continue
        if had:
            m = re.match(r'^([^：:<>]{2,10})[：:]\s*(.*)$', p, re.S)
            if m:
                p = f'<b>{m.group(1)}：</b>{m.group(2)}'
            elif len(p) <= 12:
                p = f'<b>{p}</b>'
        out.append(f'<p>{p}</p>')
    return out or [html]


NUMSENT = re.compile(r'^\s*\d+[.．、]\s*\S')


def numbered_heads(html):
    t = next(iter(BeautifulSoup(html, 'html.parser').children))
    if t.name == 'h4':
        s = t.get_text().strip()
        if NUMSENT.match(s) and (re.search(r'[。；;！？]$', s) or len(s) > 26):
            return f'<p class="num">{s}</p>'
    return html


DIAGRAM_START = 'ΔSIO激活点'
DIAGRAM_END = '张力 → 主客结构化'


def fix_diagram(blocks):
    txt = [BeautifulSoup(b, 'html.parser').get_text() for b in blocks]
    try:
        i = next(k for k, t in enumerate(txt) if t.strip().startswith(DIAGRAM_START) or ('ΔSIO激活点' in t and '╱' in t))
        j = next(k for k in range(i, min(i + 12, len(txt))) if DIAGRAM_END in txt[k])
    except StopIteration:
        return blocks
    _, t = table_html([['第一性', '第二性（ΔSIO激活点）', '第三性'],
                       ['沉浸感', '张力 → 主客结构化', '结构化']])
    return blocks[:i] + [t] + blocks[j + 1:]


def polish(blocks, no=None):
    blocks = fix_diagram(blocks)
    blocks = restore_tables(blocks)
    blocks = pseudo_heads(blocks)
    blocks = key_labels(blocks)
    blocks = list_heads(blocks)
    blocks = join_into_list(blocks)
    blocks = short_heads(blocks)
    out = []
    for b in blocks:
        for x in split_labels(b):
            x = numbered_heads(x)
            out.append(fix_text_nodes(x))
    out = [re.sub(r'^<p>(金句[一二三四五六七八九十]+：.*)</p>$', r'<h4>\1</h4>', b, flags=re.S) for b in out]
    out = [re.sub(r'^<p>(\d+[.．、]\s*\S)', r'<p class="num">\1', b) if len(b) < 400 else b for b in out]
    out = after_select(out, no)
    # 去掉清理后变空的段落
    return [b for b in out if BeautifulSoup(b, 'html.parser').get_text().strip() or '<table' in b]


# ---------------------------------------------------------------- 章内伪标题
NUM = '一二三四五六七八九十'
RE_PART = re.compile(r'^第([' + NUM + r'\d]+)(编|部分)[\s　:：·、]*(.*?)[：:]?$')
RE_SEC = re.compile(r'^第([' + NUM + r'\d]+)节[\s　:：]*(.*?)[：:]?$')
RE_LEAD = re.compile(r'^(引言|导论|前言|结语|后记|摘要|补章|附录[一二三四五]?|导论补缺)([：:]\s*(.*))?$')
RE_LABEL = re.compile(r'^(第[' + NUM + r'\d]+章|总结|总结句|总结一句话|对照结论)[：:](.*)$')


def _p(t):
    return t.name == 'p' and not t.get('class')


def pseudo_heads(blocks):
    soups = [next(iter(BeautifulSoup(b, 'html.parser').children)) for b in blocks]
    txt = [s.get_text().strip() if s.name else '' for s in soups]
    out, k = [], 0
    while k < len(blocks):
        t, s = soups[k], txt[k]
        nxt = txt[k + 1] if k + 1 < len(blocks) else ''
        if not (t.name == 'p' and not t.get('class')) or len(s) > 44 or re.search(r'[。！？；;，,]$', s) or '，' in s:
            out.append(blocks[k]); k += 1; continue
        s = re.sub(r'^◎\s*', '', s)
        # 被截断的标题行：接上后面的短行
        if k + 1 < len(blocks) and _p(soups[k + 1]) and len(nxt) <= 20 and not re.search(r'[。！；;：:]$', nxt) and \
                (s.endswith('——') or (s.startswith('——') and len(s) >= 10) or (width_ok(s) and RE_PART.match(s))):
            s = s + nxt
            k += 1
        m = RE_PART.match(s)
        if m and len(s) <= 44:
            title = m.group(3).strip()
            out.append(f'<h2>第{m.group(1)}部分' + (f'　{title}' if title else '') + '</h2>')
            k += 1; continue
        if re.match(r'^[（(]\d+[）)][^，。；：:]{2,24}$', s):
            out.append(f'<h4>{s}</h4>')
            k += 1; continue
        m = RE_SEC.match(s)
        if m:
            out.append(f'<h3>第{m.group(1)}节　{m.group(2).strip()}</h3>')
            k += 1; continue
        m = RE_LEAD.match(s)
        if m:
            rest = (m.group(3) or '').strip()
            out.append(f'<h3>{m.group(1)}' + (f'：{rest}' if rest else '') + '</h3>')
            k += 1; continue
        m = RE_LABEL.match(s)
        if m:
            out.append(f'<p><b>{m.group(1)}：</b>{m.group(2).strip()}</p>')
            k += 1; continue
        if s.startswith('——') and len(s) <= 44:
            out.append(f'<p class="dash">{s}</p>')
            k += 1; continue
        out.append(blocks[k]); k += 1
    return out


def width_ok(s):
    return sum(2 if ord(c) > 0x2e80 else 1 for c in s) / 2 >= 24


# ---------------------------------------------------------------- 选篇后的清理
DROP_EXACT = {
    # 下面没有正文的悬空标题（后文未选入）
    '后记：资本主义的救赎之路', '第五部分　本体论与认识论的深层批判', '第四部分　文明的三律外化',
    '第六部分　意识三律对教育、管理、健康的创新解码', '第三部分　心理疾病的三界与三律对应解构',
    '第四部分　结论与展望', '第四部分　想象力篇：张力与前意义',
    # 写作过程残留
    '第二十四章〈家庭中的三律人格发生〉（约5000字）完成。',
    # 指向未选入内容的预告
    '下一章预告：', '下一章我们将进入第六章：', '“因材施教”神话的本体性批判',
    '附录一', '从看见球，到碰到球：网球纠缠教学的发生学分析',
}
DROP_PREFIX = ('下一章将进一步展开三类学习', '既然三律教学智慧才是孔子教育思想的真实核心，那么“因材施教”在历史上为何',
               '下一章，将从“学习的发生性存在方式”全面展开')
# 选篇后分部编号已不连贯的章：去掉「第X部分」分部标题
NO_PARTS = {5, 15}


def after_select(blocks, no=None):
    out = []
    for b in blocks:
        t = next(iter(BeautifulSoup(b, 'html.parser').children))
        s = t.get_text().strip() if t.name else ''
        if s in DROP_EXACT or s.startswith(DROP_PREFIX):
            continue
        if t.name == 'h2' and re.match(r'^第[' + NUM + r']+部分　总结$', s):
            out.append('<h3>总结</h3>'); continue
        if no in NO_PARTS and t.name == 'h2' and re.match(r'^第[' + NUM + r']+部分', s):
            continue
        if t.name == 'p' and s.startswith('结语与') and len(s) <= 40 and not re.search(r'[。！？]$', s):
            out.append(f'<h2>{s}</h2>'); continue
        out.append(b)
    # 章末只剩标题或副题的，去掉
    while out and re.match(r'<(h[234]|p class="dash")', out[-1]):
        out.pop()
    return out


def key_labels(blocks):
    """只有「结论：」几个字的强调框：与下一段合并进框；下一段是列表时改为加粗标签。"""
    out, k = [], 0
    while k < len(blocks):
        b = blocks[k]
        t = next(iter(BeautifulSoup(b, 'html.parser').children))
        s = t.get_text().strip() if t.name else ''
        if t.name == 'p' and 'key' in (t.get('class') or []) and len(s) <= 8 and re.search(r'[：:]$', s):
            nxt = blocks[k + 1] if k + 1 < len(blocks) else ''
            n = next(iter(BeautifulSoup(nxt, 'html.parser').children)) if nxt else None
            if n is not None and n.name == 'p' and not n.get('class'):
                out.append(f'<p class="key"><b>{s}</b>{n.decode_contents()}</p>')
                k += 2; continue
            out.append(f'<p><b>{s}</b></p>')
            k += 1; continue
        out.append(b); k += 1
    return out


END_PUNCT = re.compile(r'[。！？!?；;：:，,、…”」』）)】]$')


def short_heads(blocks):
    """短行小标题：≤24 字、无句末标点、不含逗号的短段，连续不超过两行、其后接正文段/列表/表格，
    且前一块不是短行 → h4（三行以上的短行串视为列表，不动）。"""
    soups = [next(iter(BeautifulSoup(b, 'html.parser').children)) for b in blocks]
    txt = [s.get_text().strip() if s.name else '' for s in soups]

    def is_short(k):
        t = soups[k]
        return t.name == 'p' and not t.get('class') and 2 <= len(txt[k]) <= 24 and not END_PUNCT.search(txt[k]) \
            and '，' not in txt[k] and not re.match(r'^[-·•\d]', txt[k])
    out, k = [], 0
    while k < len(blocks):
        if is_short(k):
            e = k
            while e + 1 < len(blocks) and is_short(e + 1):
                e += 1
            run = e - k + 1
            prev_short = k > 0 and soups[k - 1].name == 'p' and len(txt[k - 1]) <= 24 and not END_PUNCT.search(txt[k - 1])
            nxt_ok = e + 1 < len(blocks) and ((soups[e + 1].name == 'p' and (len(txt[e + 1]) > 30 or re.search(r'[：:]$', txt[e + 1])))
                                              or soups[e + 1].name in ('ul', 'ol', 'table'))
            if run <= 2 and nxt_ok and not prev_short:
                out += [f'<h4>{txt[x]}</h4>' for x in range(k, e + 1)]
            else:
                out += blocks[k:e + 1]
            k = e + 1
            continue
        out.append(blocks[k]); k += 1
    return out


def join_into_list(blocks):
    """未完句的段落（行尾无标点）与紧随其后列表的首项接回。"""
    out = []
    for b in blocks:
        t = next(iter(BeautifulSoup(b, 'html.parser').children))
        if out and t.name == 'ul':
            p = next(iter(BeautifulSoup(out[-1], 'html.parser').children))
            ptxt = p.get_text().strip()
            lis = t.find_all('li', recursive=False)
            if p.name == 'p' and ptxt and not re.search(r'[。！？!?；;：:”」』）)】]$', ptxt) and len(ptxt) >= 16 and lis \
                    and len(lis[0].get_text().strip()) <= 30:
                first = lis[0]
                p.append(BeautifulSoup(first.decode_contents(), 'html.parser'))
                first.decompose()
                out[-1] = str(p)
                if t.find('li'):
                    out.append(str(t))
                continue
        out.append(b)
    return out


def list_heads(blocks):
    """被拆成一两个列表项的标题（首项以「——」结尾）合回一个小节标题。"""
    out = []
    for b in blocks:
        t = next(iter(BeautifulSoup(b, 'html.parser').children))
        if t.name == 'ul':
            lis = [li.get_text().strip() for li in t.find_all('li', recursive=False)]
            if 1 <= len(lis) <= 2 and lis[0].endswith('——') and len(''.join(lis)) <= 44:
                out.append('<h3>' + ''.join(lis) + '</h3>')
                continue
        out.append(b)
    return out
