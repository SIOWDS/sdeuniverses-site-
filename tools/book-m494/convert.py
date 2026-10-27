#!/usr/bin/env python3
"""第 494 号《矛盾在哪里结算》：把 /home/claude/book/ 的统稿（front.md + part01–10.md）转成 220/302 版式工具链的分卷稿。
只做格式转换，不动正文文字：
  · 编首语标记去掉，编首语成为编序；
  · 章末「本章结算」（行内、独立段或小节标题三种写法）→ 引用框「本章结算」；
  · 「本章涉及文献」（行内分号串或列表）→ 引用框「本章涉及文献」，并汇总去重成全书参考书目；
  · 第 35 章（结语）移为全书结语。
产物：front/00-前置.md、parts/NN-第X编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
SRC = Path(M.SRC)
CNB = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
han = lambda s: len(re.findall(r'[一-鿿]', s))
BIB = []


def split_refs(s):
    s = s.strip().lstrip('：:　 ').rstrip('。')
    return [x.strip().rstrip('。.') for x in re.split(r'[；;]\s*', s) if x.strip()]


def chapter_ends(text):
    """把「本章结算」「本章涉及文献」两类章末件转成引用框。"""
    L = text.split('\n'); out = []; i = 0
    stop = lambda ln: ln.startswith('#') or ln.strip() == '---' or ln.startswith('**本章涉及文献**') or ln.startswith('**本章结算**')
    while i < len(L):
        ln = L[i]; s = ln.strip()
        m = re.match(r'^###\s+(?:[一二三四五六七八九十]+、)?本章结算\s*$', s) or re.match(r'^\*\*本章结算\*\*[：:　 ]*(.*)$', s)
        if m:
            body = []
            if m.groups() and m.group(1).strip():
                body.append(m.group(1).strip())
            i += 1
            while i < len(L) and not stop(L[i]):
                if L[i].strip():
                    body.append(L[i].strip())
                i += 1
            out += ['> **本章结算**'] + ['> ' + b for b in body] + ['']
            continue
        m = re.match(r'^\*\*本章涉及文献\*\*[：:　 ]*(.*)$', s)
        if m:
            items = split_refs(m.group(1)) if m.group(1).strip() else []
            i += 1
            while i < len(L) and not stop(L[i]):
                t = L[i].strip()
                if t:
                    t = re.sub(r'^[-*]\s+', '', t)
                    t = re.sub(r'^\d+\.\s+', '', t)
                    items += split_refs(t) if not items and '；' in t else [t.rstrip('。.')]
                i += 1
            for x in items:
                if x not in BIB:
                    BIB.append(x)
            out += ['> **本章涉及文献**'] + ['> ' + x for x in items] + ['']
            continue
        if s == '---':
            i += 1; continue
        out.append(ln); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def part_file(k, t):
    t = t.replace('\r', '')
    t = re.sub(r'^####\s+', '### ', t, flags=re.M)
    t = re.sub(r'^\*\*编首语\*\*[　 ]*', '', t, flags=re.M)
    t = re.sub(r'^(## 第\d+章　.*?)\s*⚔\s*', r'\1　⚔ ', t, flags=re.M)
    head, rest = t.split('\n', 1)
    assert head.startswith('# 第%s编' % CNB[k]), head
    return head + '\n\n' + chapter_ends(rest.lstrip('\n'))


def main():
    fr = (SRC / 'front.md').read_text()
    pre = fr[fr.index('# 前言'):]
    pre = pre[:pre.index('# 目录')].rstrip().rstrip('-').rstrip()
    pre = pre.replace('# 前言', '## 前言', 1)
    parts = [(SRC / ('part%02d.md' % k)).read_text() for k in range(1, 11)]
    # 第 35 章移为全书结语
    p10 = parts[9]
    j = p10.index('## 第35章')
    jie = p10[j:]
    parts[9] = p10[:j].rstrip().rstrip('-').rstrip() + '\n'
    jie_head, jie_body = jie.split('\n', 1)
    sub = re.sub(r'^## 第35章　(结语：)?', '', jie_head).strip()
    body_all = ''.join(parts) + jie
    wan = round(han(pre + body_all) / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s》' % M.FULL_TITLE), ('副题', M.SUBTITLE2), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    notes = ['本书所述「国家三属性」「结算」「过分和谐」「介生路径」「危机路径」等，是本书提出的分析框架，不是学界定论；书中对各位经济学家的转述只述大意，引文以原著为准。',
             '涉及 2025—2026 年的事实与数据，截至 2026 年 10 月；此后的变化不在本书范围之内。', '版权所有　侵权必究']
    epi = ['## 题词', '【题词】没有矛盾，就没有轮换。', '【题词署】——本书母题']
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + '\n\n'.join(epi) + '\n\n' + pre + '\n')
    (HERE / 'parts').mkdir(exist_ok=True)
    files = ['front/00-前置.md']
    for k in range(1, 11):
        f = 'parts/%02d-第%s编.md' % (k, CNB[k])
        (HERE / f).write_text(part_file(k, parts[k - 1]))
        files.append(f)
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text('# 结语　' + sub + '\n\n' + chapter_ends(jie_body.lstrip('\n')))
    bib = ['# 参考书目', '', '以下为各章「本章涉及文献」的汇总，按首次出现的先后排列。', '']
    bib += ['%d. %s' % (n + 1, x) for n, x in enumerate(BIB)]
    (HERE / 'back/12-后置.md').write_text('\n'.join(bib) + '\n')
    files += ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan, 'bib', len(BIB),
          'jiesuan', b.count('> **本章结算**'), 'refs', b.count('> **本章涉及文献**'))


if __name__ == '__main__':
    main()
