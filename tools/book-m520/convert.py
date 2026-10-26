#!/usr/bin/env python3
"""第 520 号《欠》：把 /home/claude/qian/parts 下的定稿（00前件、编01–09、97结语、98参考书目、99附录后记）
转成 220/302 版式工具链（照第 519 号）的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = Path(M.SRC)
CN = '零一二三四五六七八九'
PIAN = {1: '上篇　欠是什么', 4: '中篇　欠怎样发生', 7: '下篇　欠为什么被推出来'}
SHANG = ['上篇三编，各问一个「是什么」。第一编把欠和缺、借、负、亏分开，立起三种欠。第二编问：物里、身体里、心里的欠，是不是同一回事。第三编问：「两清」「谁也不欠谁」，遮住了什么。',
         '三编合起来，只做一件事：把欠从一本账里请出来，放回一件正在发生的事里。']

def ends(text):
    """章末：**带走的话**：…／> 小账 …／想一想 … → 220 版式的三个引用框。"""
    L = text.split('\n'); out = []; i = 0
    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^\*\*带走的话\*\*[：:]\s*(.*)$', s)
        if m:
            x = re.sub(r'^\*\*(.*)\*\*$', r'\1', m[1].strip())
            out += ['> **带走的话**', '> ' + x, '']; i += 1
            # 小账
            while i < len(L) and not L[i].strip(): i += 1
            q = []
            while i < len(L) and L[i].strip().startswith('>'):
                c = L[i].strip().lstrip('>').strip()
                if c and c not in ('小账', '**小账**'): q.append(c)
                i += 1
            if q:
                out += ['> **小账**'] + ['> ' + c for c in q] + ['']
            # 想一想
            while i < len(L) and not L[i].strip(): i += 1
            if i < len(L):
                mm = re.match(r'^(\*\*)?想一想(\*\*)?[：:]?\s*(.*)$', L[i].strip())
                if mm:
                    qs = [mm[3].strip()] if mm[3].strip() else []
                    i += 1
                    while i < len(L) and not L[i].startswith('#') and L[i].strip() != '---':
                        if L[i].strip(): qs.append(re.sub(r'^(\d+[.、]\s*|- )', '', L[i].strip()))
                        i += 1
                    out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, q) for k, q in enumerate(qs)] + ['']
            continue
        if s == '---': i += 1; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'

def main():
    fr = (S / '00前件.md').read_text()
    fr = fr[fr.index('# 作者介绍'):]
    lun_i = fr.index('# 导论')
    front, lun = fr[:lun_i], fr[lun_i:]
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、口述承重命题与裁定，Claude 执笔与统稿（九编并行执笔）'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 20 万字'), ('版次', '2026 年 10 月第 1 版第 1 次修订')]:
        cp.append('| %s | %s |' % (a, b))
    notes = ['AI 协作声明：本书的判断、口径与承重命题由王德生（口述）给出；文字在其指令下由 AI（Claude）协作成稿，并经其审定。',
             '书中所引古今中外各家的话，一律转述大意，不作逐字引文，出处以书名、篇名与年份标注。出处的核验结果标在原处：〔核〕为已查对出处，〔核：大意〕为出处已查对、引文取大意，〔据研究文献〕为依据研究综述，〔待验〕为本书推出、尚待验证的局面；汇总见附录四「引文核验总表」。',
             '书中陪读人物周桂芳、周磊、朵朵及各章日常场景、人物均为虚构。关于身体的章节讲理解、习惯与相处，不构成医学建议；关于借贷的章节讲理解，不构成理财建议。身体或心里的难处真的大了，请找医生或心理咨询师。本书的承重命题由王德生于 2026 年 10 月 26 日口述，登记见附录一。',
             '全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录；导论与上中下三篇九编五十四章；结语、附录六件、参考书目、后记。',
             '版权所有　侵权必究']
    front = re.sub(r'^# ', '## ', front, flags=re.M)
    front = ends(front)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + front)
    (HERE / 'front/01-导论.md').write_text(ends(lun))
    (HERE / 'parts').mkdir(exist_ok=True)
    for k in range(1, 10):
        t = (S / ('编0%d.md' % k)).read_text()
        pre = []
        if t.startswith('# ') and '篇' in t.split('\n', 1)[0]:
            head, rest = t.split('\n', 1)
            j = rest.index('\n# 第')
            pre = [p.strip() for p in rest[:j].split('\n') if p.strip()]
            t = rest[j + 1:]
        if k == 1: pre = SHANG
        if pre:
            pre = ['**%s**' % PIAN[k]] + pre
        head, rest = t.split('\n', 1)
        assert head.startswith('# 第%s编' % CN[k]), head
        rest = rest.lstrip('\n')
        body = head + '\n\n' + ('\n\n'.join(pre) + '\n\n' if pre else '') + rest
        body = re.sub(r'^## 第 (\d+) 章　', r'## 第\1章　', body, flags=re.M)
        (HERE / ('parts/0%d-第%s编.md' % (k, CN[k]))).write_text(ends(body))
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(ends((S / '97结语.md').read_text()))
    ap = (S / '99附录后记.md').read_text()
    ai = ap.index('# 后记')
    appx, hou = ap[:ai], ap[ai:]
    appx = re.sub(r'\n---\n', '\n', appx)
    bib = (S / '98参考书目.md').read_text()
    bib = re.sub(r'^【(.*)】$', r'### \1', bib, flags=re.M)
    (HERE / 'back/12-后置.md').write_text(appx.strip() + '\n\n' + bib.strip() + '\n\n' + hou.strip() + '\n')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CN[k]) for k in range(1, 10)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    han = lambda s: len(re.findall(r'[一-鿿]', s))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b))

if __name__ == '__main__':
    main()
