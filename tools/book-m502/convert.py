#!/usr/bin/env python3
"""第 502 号《个人知识发生平台的数据基因》：把 meta.SRC 下的定稿（fm-preface、fm-guide、intro、ch-01…32、conclusion、app-1…7）
转成 220/302 版式工具链的分卷稿。只做格式转换，不动正文文字：
  · 章题「# 第N章　题」→「## 第 N 章　题」；章首一句话问题 →「这一章的问题」框；
  · 章内「## 一、…」「## 规格卡　…」→「### ◆ …」；章内「### …」→ 加粗小标题段；
  · 「**带走的话**　…」「**小账**＋列表」→ 引用框；
  · 七编编序取自导读「二、七编路线」各编一段（去掉加粗编名）；
  · 附录各件降一级：「# 附录N　…」→「## 附录N　…」，件内「##」→「### ◆」，「###」→ 加粗小标题段。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第X编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
CN = '零一二三四五六七八九十'
PARTS = [('第一编', '总图', range(1, 5)), ('第二编', '基因的规格', range(5, 12)),
         ('第三编', '表达：三部分的实现', range(12, 19)), ('第四编', '生长：代际与回写', range(19, 24)),
         ('第五编', '流通：社区里的市场', range(24, 28)), ('第六编', '人与守护', range(28, 31)),
         ('第七编', '全程与边界', range(31, 33))]
han = lambda s: len(re.findall(r'[一-鿿]', s))


def curly(line):
    """直引号 " 成对换成中文引号 “ ”（稿中个别章用了直引号）。"""
    if '"' not in line:
        return line
    out, op = [], True
    for ch in line:
        if ch == '"':
            out.append('“' if op else '”'); op = not op
        else:
            out.append(ch)
    return ''.join(out)


def body_convert(text, sec_level='###', sub_bold=True, first_question=False):
    """把一个单元（章、导论、结语、前言……）的正文按上面的规则转换；不含首行标题。"""
    L = [curly(x) for x in text.replace('\r', '').split('\n')]
    out, i, asked = [], 0, False
    while i < len(L):
        ln = L[i]; s = ln.strip()
        if first_question and not asked and s.startswith('> '):
            q = s[2:].strip()
            out += ['> **这一章的问题**：' + q, '']
            asked = True; i += 1
            continue
        if s.startswith('> ') and not asked:
            asked = True
        m = re.match(r'^\*\*带走的话\*\*[：:　 ]*(.*)$', s)
        if m:
            body = [m[1].strip()] if m[1].strip() else []
            i += 1
            while i < len(L) and L[i].strip() and not L[i].startswith('#') and not L[i].strip().startswith('**小账**'):
                body.append(L[i].strip()); i += 1
            out += ['> **带走的话**'] + ['> ' + b for b in body] + ['']
            continue
        if re.match(r'^\*\*小\s*账\*\*\s*$', s):
            items = []
            i += 1
            while i < len(L) and (not L[i].strip() and not items or L[i].strip().startswith('- ') or (L[i].strip() and items and not L[i].startswith('#') and not L[i].strip().startswith('**'))):
                t = L[i].strip()
                if t.startswith('- '):
                    items.append(t[2:].strip())
                elif t and items:
                    items[-1] += t
                i += 1
            out += ['> **小账**'] + ['> ' + x for x in items] + ['']
            continue
        if s.startswith('#### '):
            out += ['**%s**' % s[5:].strip()]; i += 1; continue
        if s.startswith('### '):
            out += ['**%s**' % s[4:].strip()] if sub_bold else ['### ' + s[4:].strip()]
            i += 1; continue
        if s.startswith('## '):
            out += ['%s ◆ %s' % (sec_level, s[3:].strip())]; i += 1; continue
        out.append(ln.rstrip())
        i += 1
    txt = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', txt).strip() + '\n'


def split_head(path):
    t = (SRC / path).read_text().replace('\r', '')
    first, _, rest = t.partition('\n')
    assert first.startswith('# '), (path, first)
    return first[2:].strip(), rest


def route_paras():
    """导读「二、七编路线」：每编一段，返回 {编名: 段文}。"""
    t = (SRC / 'fm-guide.md').read_text()
    seg = t.split('## 二、七编路线', 1)[1].split('\n## ', 1)[0]
    res = {}
    for p in seg.split('\n\n'):
        m = re.match(r'^\*\*(第.编)　[^*]+\*\*\s*(.*)$', p.strip(), re.S)
        if m:
            res[m[1]] = m[2].strip()
    assert len(res) == 7, res.keys()
    return res


def front():
    meta_cp = [
        ('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
        ('出版', '%s（%s）' % (M.PUBLISHER, M.PUBLISHER_EN)), ('丛书', '「慧店」系列第三卷（技术卷）'),
        ('编号', '德麦国际专著第 %d 号' % M.NO), ('ISBN', M.ISBN), ('定价', M.PRICE),
        ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % round(HAN_TOTAL / 10000)), ('版次', '2026 年 10 月第 1 版'),
    ]
    notes = [
        '本书承重的判断出自 WDS博士 2026 年 10 月下旬的口述，原话登记于附录六；文字在 AI 协作下写成：由 Claude 统筹，十五路 Claude 分章执笔，Claude 统稿。',
        '书中人物（罗青禾、阿乐、周叔、林可、许怀谷、唐敏等）及其场景均为虚构，不承担证据；书中的规格、流程与阈值是本书的设计，尚未真跑，标〔待验〕处待检验；外部文献只述大意，标〔待核〕处待核。',
        '书中涉及身体与用药的场景只谈理解与相处，不构成诊疗意见；涉及传销认定的段落不构成法律意见。',
        '版权所有　侵权必究',
    ]
    out = ['## 出版信息', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % r for r in meta_cp] + ['']
    out += [x + '\n' for x in notes]
    out += ['## 题词', '', '【题词】子本是用来发生的。', '', '【题词署】——WDS博士口述，2026 年 10 月', '']
    for f in ('fm-preface.md', 'fm-guide.md'):
        title, rest = split_head(f)
        out += ['## ' + title, '', body_convert(rest)]
    return '\n'.join(out)


def main():
    global HAN_TOTAL
    files = ['fm-preface.md', 'fm-guide.md', 'intro.md'] + ['ch-%02d.md' % k for k in range(1, 33)] + ['conclusion.md'] + ['app-%d.md' % k for k in range(1, 8)]
    HAN_TOTAL = sum(han((SRC / f).read_text()) for f in files)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for old in (HERE / d).glob('*.md'):
            old.unlink()
    fr = front()
    (HERE / 'front/00-前置.md').write_text(fr)
    title, rest = split_head('intro.md')
    lun = '# %s\n\n%s' % (title, body_convert(rest))
    (HERE / 'front/01-导论.md').write_text(lun)
    rp = route_paras()
    parts_txt = []
    for k, (pn, pt, rng) in enumerate(PARTS, 1):
        o = ['# %s　%s' % (pn, pt), '', rp[pn], '']
        for c in rng:
            title, rest = split_head('ch-%02d.md' % c)
            m = re.match(r'^第(\d+)章　(.+)$', title)
            assert m and int(m[1]) == c, title
            o += ['## 第 %d 章　%s' % (c, m[2]), '', body_convert(rest, first_question=True)]
        txt = '\n'.join(o)
        (HERE / ('parts/%02d-%s.md' % (k, pn))).write_text(txt)
        parts_txt.append(txt)
    title, rest = split_head('conclusion.md')
    jy = '# %s\n\n%s' % (title, body_convert(rest))
    (HERE / 'back/11-结语.md').write_text(jy)
    o = ['# 附录', '', '七个附录分两类：附录一至四是工具，规格、对照、母本总目与成本，供查；附录五至七是凭据，白话词、口述原话与推翻条件，供核。正文里写“详见附录某”的地方，都在这里落地。', '']
    for k in range(1, 8):
        title, rest = split_head('app-%d.md' % k)
        o += ['## ' + title, '', body_convert(rest, sec_level='###')]
    hz = '\n'.join(o)
    (HERE / 'back/12-后置.md').write_text(hz)
    book = '\n\n'.join([fr, lun] + parts_txt + [jy, hz])
    (HERE / 'book.md').write_text(book)
    print('汉字（源）', HAN_TOTAL, '汉字（分卷稿）', han(book))


if __name__ == '__main__':
    main()
