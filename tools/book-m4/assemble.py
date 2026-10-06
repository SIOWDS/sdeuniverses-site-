#!/usr/bin/env python3
"""第 4 号《SDE发生学》组装：src/paras.json（从原 PDF 逐页取出的段落）→ parts/NN-第X篇.md、front/、back/ 的正文。
只动形式：去公众号残留与写作过程标记、统一编章层级与标点、中西文加空格；论点与论证次序不改。
用法：python3 assemble.py
"""
import json, re
from pathlib import Path
from skeleton import load, cls

ROOT = Path(__file__).parent
CN = '零一二三四五六七八九十'
P = load()

TITLES = {
 '1': ('SDE的来龙去脉', '从三视角知识论出发，走向发生学本体论的彻底革命'),
 '2': ('SDE：对「发现」的发生学彻底革命', ''),
 '3': ('SDE本体论入门', '最本质、最本能、最本源的存在三维度'),
 '4': ('SDE思想体系入门', '发生学＝底盘＋回写：从SIO结构到SDE动力学的统一框架'),
 '5': ('SDE动力学初探', ''),
 '6': ('基于SDE本体论的思想创新方法与实践导论', ''),
 '7': ('欲望发生学的SDE定理', '欲望作为特征纠缠潜能的建立、运行与沉积机制'),
 '8': ('抑郁症的SDE解构入门', '从「press down」到E动力学退化：技术文明与意义三律的失速机制'),
 '9': ('无为而无不为的SDE解构', '「遵循大道」的错觉、阈值附近的自运行与后台纠缠机制'),
 '10': ('互动医学的SDE解构入门', '以慢性病为对象的差异序列与特征纠缠动力学纲要'),
}
SRC = {  # 原载：公众号 · 日期
 '1': ('SIO教育学', '2026-01-24'), '2': ('三二一智慧', '2026-01-14'), '3': ('创造力321', '2026-01-14'),
 '4': ('创造力321', '2026-01-22'), '5': ('SIO教育学', '2026-01-13'), '6': ('创造力321', '2026-01-10'),
 '7': ('321互动吧', '2026-01-13'), '8': ('创造力321', '2026-01-15'), '9': ('互动学园', '2026-01-17'),
 '10': ('三二一智慧', '2026-01-13'),
}


def quotes(s):
    out, depth = [], 0
    for ch in s:
        if ch in '“':
            out.append('「' if depth == 0 else '『'); depth += 1
        elif ch == '”':
            depth = max(depth - 1, 0); out.append('」' if depth == 0 else '』')
        elif ch == '‘':
            out.append('『'); depth += 1
        elif ch == '’':
            depth = max(depth - 1, 0); out.append('』')
        else:
            out.append(ch)
    return ''.join(out)


CJK = r'[一-鿿]'
LAT = r'[A-Za-z0-9Δσεφ]'


def spacing(s):
    s = re.sub('(%s)(%s)' % (CJK, LAT), r'\1 \2', s)
    s = re.sub('(%s)(%s)' % (LAT, CJK), r'\1 \2', s)
    return s


def clean(s):
    s = quotes(s)
    s = s.replace('（续写）', '')
    s = spacing(s)
    return s.strip()


DROP_PREFIX = ('（后续将继续',)
ARTICLE_FIXES = [  # (篇, 旧, 新) —— 写作过程中对话口气的残留
    ('1', '可你已经指出，真正的发生学革命', '可真正的发生学革命'),
    ('3', '你提出的号位对应关系非常关键', '号位对应关系非常关键'),
    ('3', '引入你已经建立的三模态语法', '引入前文已经建立的三模态语法'),
    ('8', '自由在你的体系中并不等同', '自由在本书的体系中并不等同'),
    ('8', '幸福在你的体系中不是', '幸福在本书的体系中不是'),
]


def prep(k, ps):
    out, skip = [], False
    for x in ps:
        if skip:
            if x.rstrip().endswith('）') or '崩塌路径' in x:
                skip = False
            continue
        if x.startswith(DROP_PREFIX):
            skip = True
            continue
        out.append(x)
    ps = out
    # 被折行拆开的括号尾巴并回上一条
    merged = []
    for x in ps:
        if merged and len(x) <= 14 and '）' in x and '（' not in x and cls(x) == 'p':
            merged[-1] += x
        else:
            merged.append(x)
    ps = merged
    # 一条里并了几项的编号清单
    res = []
    for x in ps:
        res += [z for z in re.split(r'(?<=[。；])(?=\d[）)])|(?<=如下：)(?=1\. )|(?<=[。；；])(?=\d\. [^\d])', x) if z]
    ps = res
    for kk, a, b in ARTICLE_FIXES:
        if kk == k:
            ps = [x.replace(a, b) for x in ps]
    return ps


BREAKERS = ('然而', '但是', '可是', '因此', '于是', '更关键的是', '更深一层', '换言之', '与此同时', '此外', '至此', '这意味着', '由此', '从发生学', '从这一', '这里的', '第二', '第三', '第四', '第五', '其二', '其三', '其四', '最后', '正因如此', '所以', '总之', '例如', '以', '同样地', '更严重的是', '尤其')


def split_long(x, limit=440, target=240):
    """过长的段落按句子断开：先凑到 target 字，遇到转折/承接词或超过 limit 就另起一段。只断段，不改字。"""
    if len(x) <= limit:
        return [x]
    sents = re.findall(r'.*?[。！？](?:[」』）])*|.+$', x, re.S)
    out, cur = [], ''
    for s in sents:
        if cur and ((len(cur) >= target and s.startswith(BREAKERS)) or len(cur) + len(s) > limit + 60 or len(cur) >= limit):
            out.append(cur); cur = ''
        cur += s
    if cur:
        if out and len(cur) < 60:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def cn_num(w):
    if len(w) == 1:
        return CN.index(w)
    if w[0] == '十':
        return 10 + CN.index(w[1])
    return CN.index(w[0]) * 10 + (CN.index(w[1]) if len(w) > 1 else 0)


TERMS = '。！？；：…'


def is_listy(x):
    return len(x) <= 46 and x[-1] not in TERMS and cls(x) == 'p' and not re.match(r'^[A-D]\. ', x)


def md_for(k):
    ps = prep(k, list(P[k]))
    title, sub = TITLES[k]
    # 去公众号头：标题、原创/作者/日期行、副标题行
    i = 0
    while i < min(4, len(ps)):
        x = ps[i]
        if i == 0 or re.match(r'^(原创\s)?王德生', x) or x.startswith('::') or x.startswith('——') or x.startswith('副标题：'):
            i += 1
        else:
            break
    ps = ps[i:]
    n = len(ps)
    out = []          # (type, text)
    j = 0
    in_intro = False
    skip_stub = False
    while j < n:
        x = ps[j]
        c = cls(x)
        # ── 篇内特例 ──
        if k == '4' and x.startswith('结论') and '收束段' in x:
            j += 2
            continue
        if k == '6' and x == '关键词':
            out.append(('p', '关键词：' + clean(ps[j + 1]))); j += 2; continue
        if k == '5' and x.startswith('插入章'):
            t = re.sub(r'^插入章[：:　 ]*', '', x)
            out.append(('h3', '◆ 补　' + clean(t))); in_intro = False; j += 1; continue
        if k == '5' and in_intro and re.match(r'^\d\. ', x) and len(x) < 40:
            m = re.match(r'^(\d)\. (.*)$', x)
            out.append(('h3', '◆ %s、%s' % (CN[int(m[1])], clean(m[2])))); j += 1; continue
        if k == '6' and c == 'h3c':
            m = re.match(r'^([一二三四五六七八九十]+)、(.*)$', x)
            out.append(('h2', '%s　%s' % (m[1], clean(m[2])))); j += 1; continue
        if re.match(r'^[A-D]\. ', x) and len(x) < 40:
            m = re.match(r'^([A-D])\. (.*)$', x)
            out.append(('h4', '%s　%s' % (m[1], clean(m[2])))); j += 1; continue
        # ── 通用 ──
        if c == 'ch':
            if re.fullmatch(r'第[一二三四五六七八九十]+章', x):
                x = x + ' ' + ps[j + 1]; j += 1
            m = re.match(r'^第([一二三四五六七八九十]+)章[ ：（]*(.*)$', x)
            num = cn_num(m[1])
            t = re.sub(r'^上[）)]\s*', '', m[2].strip().lstrip('：').strip())
            if k == '2' and num == 1:
                out.append(('h2', '第一部分　发现学的结构性困境'))
            out.append(('h2', '第 %d 章　%s' % (num, clean(t)))); in_intro = False
        elif c == 'grp':
            m = re.match(r'^第([二三四五六七八九十])部分：(.*)$', x)
            out.append(('h2', '第%s部分　%s' % (m[1], clean(m[2]))))
        elif c == 'h3':
            m = re.match(r'^(\d+\.\d+)\s+(.*)$', x)
            out.append(('h3', '◆ %s　%s' % (m[1], clean(m[2]))))
        elif c == 'h4':
            m = re.match(r'^(\d+\.\d+\.\d+)\s+(.*)$', x)
            out.append(('h4', '%s　%s' % (m[1], clean(m[2]))))
        elif c == 'h3c':
            m = re.match(r'^([一二三四五六七八九十]+)、(.*)$', x)
            out.append(('h3', '◆ %s、%s' % (m[1], clean(m[2]))))
        elif c == 'unit':
            m = re.match(r'^(摘要|导论|关键词|结语|后记|附录|展望|结论|插入章)\s*[：:　 ]?\s*(.*)$', x)
            kind, t = m[1], m[2].strip()
            if kind == '关键词':
                out.append(('p', clean(x)))
            else:
                if kind in ('结语', '后记') and not t and j + 1 < n and len(ps[j + 1]) < 40 and ps[j + 1][-1] not in '。！？；':
                    t = ps[j + 1]; j += 1
                if kind == '附录' and t.startswith('式工具箱'):
                    t = '工具箱' + t[len('式工具箱'):]
                t = re.sub(r'[（(]进入结尾[）)]', '', t)
                t = re.sub(r'^[（(]正式版：(.*)[）)]$', r'\1', t)
                out.append(('h2', '%s%s' % (kind, '　' + clean(t) if t else '')))
                in_intro = kind == '导论'
        else:
            m = re.match(r'^(\d+)[）)]\s*(.*)$', x)
            if m:
                out.append(('ol', '%s. %s' % (m[1], clean(m[2]))))
            elif re.match(r'^\d+\. ', x) and len(x) < 90:
                out.append(('ol', clean(x)))
            else:
                out.append(('p', clean(x)))
        j += 1
    # ── 成文：短行成列表；长段断开 ──
    lines = []
    idx = 0
    while idx < len(out):
        t, x = out[idx]
        if t in ('h2', 'h3', 'h4'):
            lines += ['', '#' * {'h2': 2, 'h3': 3, 'h4': 4}[t] + ' ' + x, '']
        elif t == 'ol':
            lines += [x]
            if idx + 1 >= len(out) or out[idx + 1][0] != 'ol':
                lines += ['']
        elif t == 'p':
            run = []
            while idx < len(out) and out[idx][0] == 'p' and is_listy(out[idx][1]):
                run.append(out[idx][1]); idx += 1
            if len(run) >= 2:
                lines += [''] + ['- ' + r for r in run] + ['']
                continue
            elif len(run) == 1:
                lines += [run[0], '']
                continue
            for part in split_long(x):
                lines += [part, '']
        idx += 1
    body = '\n'.join(lines)
    body = re.sub(r'\n{3,}', '\n\n', body).strip() + '\n'
    return body


if __name__ == '__main__':
    for k in TITLES:
        b = md_for(k)
        (ROOT / 'src' / ('draft-%02d.md' % int(k))).write_text(b, encoding='utf-8')
        print(k, len(b), len(re.findall(r'[\u4e00-\u9fff]', b)))
