#!/usr/bin/env python3
"""第 300 号《圣经中女子智慧的缝隙和补缺》：分章 Markdown 稿（--src 目录：a1/a2/a3、ch01–ch41、z1/z2）→ 本目录 front/ parts/ back/ 分卷稿。只调格式，不改正文。"""
import argparse, re
from pathlib import Path
HERE = Path(__file__).parent
VOL = {1: ('卷一', '尺子：全丰满是什么，怎样量，怎样补', '这一卷四章，不逐位量女子，只磨尺子。第 1 章讲那个没有缝的人为什么能当尺子；第 2 章讲三种亏损；第 3 章讲量她们时的分寸；第 4 章讲他怎样补。四章共用一家三代女人做的一床被面。'),
       5: ('卷二', '缺一角：手里有一样，另一样没有到场', '这一卷六章，绕着九个角落看。夏娃、利亚与拉结、拿俄米与路得、底波拉与雅亿，各有一角没有到场；才德的妇人是一幅近乎满格的画像；歌篾一章，尺子放下，写“不可判”。'),
       11: ('卷三', '偏一路：起步在哪里，路走到哪里', '这一卷七章，看起步和步数。夏甲有来处没有去处；利百加总是先动手；她玛的路是被人截的，不是她走偏的；收生婆只记下一步；岸边三个女子接力走完一条路。喇合与以斯帖是对照：一位一夜之间换了起步，一位从听命走到发令。'),
       18: ('卷四', '断一火：攒劲，变样，留下', '这一卷六章，数三拍。撒拉等不及；哈拿三拍走全；亚比该替别人把火泄掉；撒勒法的寡妇无柴可攒；书念妇人一路无人托底。最后一章不判，也不补：那两位女子身上的火不是她们的。'),
       24: ('卷五', '他当面补缺：她带来的，他接上的，他没有动的', '这一卷九章，都在福音书里。每章问三件事：她带来的是哪一样，他接上的是哪一样，他没有动的是什么。第 30 章是边界：那一回他没有当面补她。第 31 章补在第三天。'),
       33: ('卷六', '降生与教会：补缺之前，补缺之后', '这一卷五章。前四章在他出来传道之前：家谱里的女子、以利沙伯、马利亚、亚拿。末一章在五旬节之后：吕底亚、百基拉、非比，脚下第一次有了地。'),
       38: ('卷七', '结算与读你自己', '这一卷四章。第 38 章把三十三章摆成一张总表；第 39 章逐条验收五条判决，站住的、收窄的、推翻的，照实写；第 40 章看后人给她们添的缝；第 41 章把尺子交到你手里。')}
FRONT = '''## 出版信息

| 字段 | 内容 |
|---|---|
| 书名 | 圣经中女子智慧的缝隙和补缺——用耶稣的全丰满智慧照亮她们 |
| 著者 | 李佳城 |
| 指导 | 王德生（定题、定口径） |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 300 号 |
| ISBN | 979-8-90690-620-5 |
| 定价 | US$23.00 |
| 开本 | 170 mm × 240 mm（16 开） |
| 字数 | 约 __WAN__ 万汉字 |
| 版次 | 2026 年 10 月第 1 版（初稿） |
| 完稿 | 2026 年 10 月 6 日 |

AI 协作声明：本书由王德生定题、定口径，文字在其指令下由 AI（Claude）协作成稿，著者负责通读、整理与改稿。本版为第 1 版初稿，归类与读数都是初判，可被推翻。

引文说明：经文引自和合本。凡带引号并注出处者为逐字引文；凡不带引号而注出处者为转述。转述处与待核处汇于附录四，引用前请对经文。

人物说明：书中“针线一家”“周姨”等日常人物都是设想的，不是真实个案。

处境说明：书中涉及家庭、身心处境的建议不能代替专业帮助；身处暴力或危机中的人，请先寻求实际保护。

来源说明：尺子出自德麦国际第 301 号专著《我是道路、真理、生命》；经文细读多承旧稿《圣经中的女子发生学智慧》与既有的释经研究，见附录五。

全书结构：出版信息、前言、导读、目录；导论与七卷四十一章；结语、附录六件。

版权所有　侵权必究

---

'''

def end_fix(t):
    """章尾：留下的痕迹提前，带走的话与小账改成本版式的两个框，放在章末。"""
    m = re.search(r'\*\*带走的话\*\*　(.+?)\n\n((?:> .*\n?)+)', t)
    if not m:
        return t
    take, ledger = m.group(1).strip(), m.group(2).strip().split('\n')
    rest = (t[:m.start()] + t[m.end():]).rstrip()
    led = '> **小账**\n>\n' + '\n'.join(l for l in ledger[1:])
    return rest + '\n\n> 【带走的话】\n>\n> ' + take + '\n\n' + led + '\n'

def chapter(t):
    L = t.strip().split('\n')
    # 题辞：第三行那句经文，排成引语块
    if L[2].startswith('“'):
        L[2] = '> ' + L[2]
    return end_fix('\n'.join(L)) + '\n'

def front_piece(t):
    L = t.strip().split('\n')
    name, sub = L[0][2:].strip(), L[2].strip()
    body = '\n'.join(L[3:]).replace('\n## ◆', '\n### ◆')
    b = body.strip().split('\n')
    if b[0].startswith('“'):
        b[0] = '> ' + b[0]
    return '## %s　%s\n\n%s\n\n' % (name, sub, '\n'.join(b))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True)
    S = ap.parse_args().src
    R = lambda f: (S / f).read_text()
    fix = lambda s: re.sub(r'(?<=\d)–(?=\d)', '—', s)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    (HERE / 'front' / '00-前置.md').write_text(fix(FRONT + front_piece(R('a1_qianyan.md')) + '---\n\n' + front_piece(R('a2_daodu.md')) + '---\n\n' + front_piece(R('a3_daolun.md'))))
    starts = sorted(VOL)
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else 42
        lab, name, intro = VOL[s]
        txt = '# %s　%s\n\n%s\n\n' % (lab, name, intro) + '\n'.join(chapter(R('ch%02d.md' % n)) for n in range(s, e))
        (HERE / 'parts' / ('%02d-%s.md' % (i + 1, lab))).write_text(fix(txt))
    z = R('z1_jieyu.md').strip().split('\n')
    body = '\n'.join(z[3:]).replace('\n## ◆', '\n### ◆').strip().split('\n')
    if body[0].startswith('“'):
        body[0] = '> ' + body[0]
    (HERE / 'back' / '09-结语.md').write_text(fix('# 结语　%s\n\n%s\n' % (z[2].strip(), '\n'.join(body))))
    a = R('z2_fulu.md').strip()
    a = a.replace('# 附录\n', '# 附录\n\n附录六件，供查、供对、供核：判词与五条判决速查卡，白话与术语对照，本书自己的读法登记，引文与转述说明，与旧稿和第 301 号的关系，查经小组用法。\n', 1)
    (HERE / 'back' / '10-后置.md').write_text(fix(a + '\n'))
    tot = sum(len(re.findall(r'[一-鿿]', f.read_text())) for f in HERE.glob('*/*.md'))
    p = HERE / 'front' / '00-前置.md'; p.write_text(p.read_text().replace('__WAN__', '%.1f' % (tot / 10000)))
    print('han', tot)

if __name__ == '__main__':
    main()
