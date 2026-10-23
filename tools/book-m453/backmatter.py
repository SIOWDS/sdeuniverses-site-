#!/usr/bin/env python3
"""生成 back/10-后置.md：参考书目、附录（一、五为据稿件与核对总表生成，其余手写在 src/）、后记。
用法：python3 backmatter.py <draft目录> <经文核对总表.md>"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import scripture_index as SI

DRAFT = Path(sys.argv[1]); TABLE = sys.argv[2]


def rd(n):
    return (HERE / 'src' / n).read_text(encoding='utf-8').rstrip('\n')


def chap_files():
    fs = sorted(DRAFT.glob('[0-9][0-9]_*.md'))
    return fs


def sentences(para):
    """按 。！？ 切句，但引号、括号未闭合时不切。"""
    out, cur, depth = [], '', 0
    OPEN, CLOSE = '“‘（(「《', '”’）)」》'
    i = 0
    while i < len(para):
        c = para[i]; cur += c
        if c in OPEN: depth += 1
        elif c in CLOSE: depth = max(0, depth - 1)
        if c in '。！？' and depth == 0:
            while i + 1 < len(para) and para[i + 1] in CLOSE:
                i += 1; cur += para[i]; depth = max(0, depth - 1)
            out.append(cur); cur = ''
        i += 1
    if cur.strip(): out.append(cur)
    return out


def appx1():
    idx = SI.parse_table(TABLE)
    rows = SI.render(idx)
    intro = ('## 附录一　经文索引\n\n'
             '本索引据《经文核对总表》（逐章对照和合本核对）生成，按书卷次序排列。每一格是“章:节”，括号里是引用它的章（导论、结语，或第几章）；'
             '只列了章数的，是整章被提到。经文以手边的和合本为准。\n\n'
             '| 书卷 | 章:节（所在章） |\n|---|---|')
    return intro + '\n' + '\n'.join(rows)


def appx5():
    out = ['## 附录五　本书的读法登记与推翻条件', '']
    lun = (DRAFT / '00_导论.md').read_text(encoding='utf-8')
    i = lun.index('## 本书怎样算错'); j = lun.index('## 带走的话')
    paras = [p.strip() for p in lun[i:j].split('\n') if p.strip() and not p.startswith('#')]
    out += ['本书是一本说“凡……都”的书，所以必须自己先写下：什么情形出现，它就得认错。下面分两层：先是全书总的推翻条件，原文照导论“本书怎样算错”一节录出；再是逐章的登记：左栏是该章标了“（本书的读法，待验）”的地方，也就是本书推出来、经文没有明说的读法，右栏是小账里写的“怎样算错”。', '']
    out += [p + '\n' for p in paras]
    out += ['### 逐章登记', '', '| 章 | 本书的读法，待验 | 怎样算错 |', '|---|---|---|']
    for f in chap_files():
        if f.name.startswith('00'):
            lab = '导论'
        elif f.name.startswith('99'):
            lab = '结语'
        else:
            lab = '第 %d 章' % int(f.name[:2])
        txt = f.read_text(encoding='utf-8')
        main = txt.split('## SDE 小账')[0]
        tent = []
        for para in main.split('\n'):
            if para.startswith(('#', '>')) or '待验' not in para: continue
            ss = sentences(para)
            for k, s in enumerate(ss):
                if '待验' in s:
                    s = s.strip()
                    if k > 0 and (len(s) < 32 or s.startswith(('这', '那', '其', '它', '以上', '下面'))):
                        s = ss[k - 1].strip() + s
                    tent.append(s.replace('**', ''))
        if lab == '导论':          # 导论里的两处是对“待验”记号本身的说明，不是对经文的读法
            tent = []
        wrong = re.findall(r'怎样算错：([^\n]*)', txt)
        tcell = '　'.join('（%d）%s' % (k, s) for k, s in enumerate(tent, 1)) if len(tent) > 1 else (tent[0] if tent else ('——' if lab == '导论' else '（本章无标注）'))
        wcell = '　'.join(wrong) if wrong else ('——' if lab == '结语' else '（见本章小账）')
        out.append('| %s | %s | %s |' % (lab, tcell.replace('|', '｜'), wcell.replace('|', '｜')))
    return '\n'.join(out)


def main():
    parts = [rd('biblio.md'), '', rd('appx_intro.md'), '', appx1(), '', rd('appx_2.md'), '', rd('appx_3.md'), '', rd('appx_4.md'), '', appx5(), '', rd('appx_6.md'), '', rd('afterword.md')]
    (HERE / 'back/10-后置.md').write_text('\n'.join(parts) + '\n', encoding='utf-8')
    print('ok')


main()
