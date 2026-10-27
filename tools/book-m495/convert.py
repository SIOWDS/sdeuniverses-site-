#!/usr/bin/env python3
"""第 495 号《为何CPI失灵了？》：把 /home/claude/cpi-book/ 的各章统稿（ch00—ch24）转成 220/302 版式工具链的分卷稿。
只做格式转换，不动正文文字：
  · 「◆ 一、……」→「### ◆ 一、……」；「◆ 本章数据出处」→「### 本章数据出处」；
  · 「> **带走的话**：……」→ 引用框「带走的话」；「**想一想**」及其后各段 → 引用框「想一想」；
  · 前言里单独成段的加粗判词 → 引用块（排成判词框）；
  · 附录二（参考书目）提为全书参考书目；后记、附录入后置。本书无结语。
产物：front/00-前置.md、parts/NN-第X编.md、back/12-后置.md、book.md。
用法：python3 tools/book-m495/convert.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
SRC = Path(M.SRC)
CNB = ['', '一', '二', '三', '四', '五']
JUDG = 'CPI 没有算错，它平均的那个整体已经裂成了几层。差价不是成本的读数，是信心的读数；要修的不是总量，是经济的信望爱。'


def conv(text):
    L = text.split('\n'); out = []; i = 0
    while i < len(L):
        s = L[i].rstrip(); t = s.strip()
        if t in ('◆ 想一想', '### 想一想'):
            t = '**想一想**'
        if t.startswith('◆') and t != '**想一想**':
            out.append('### 本章数据出处' if '本章数据出处' in t else '### ' + t); i += 1; continue
        m = re.match(r'^>\s*\*\*带走的话\*\*[：:]\s*(.*)$', t)
        if m:
            out += ['> **带走的话**', '> ' + m[1]]; i += 1; continue
        if re.match(r'^\*\*想一想\*\*[：:]?\s*$', t):
            ps = []; i += 1
            while i < len(L):
                u = L[i].strip()
                if u.startswith(('#', '◆', '>', '|')):
                    break
                if u:
                    ps.append(u.lstrip('- ').strip())
                i += 1
            out.append('> **想一想**')
            out += ['> ' + p for p in ps]
            out.append('')
            continue
        if t == '**' + JUDG + '**':
            out.append('> **' + JUDG + '**'); i += 1; continue
        out.append(s.replace('  ', '') if s.endswith('  ') else s); i += 1
    return '\n'.join(out).strip() + '\n'


def rd(n):
    return (SRC / n).read_text(encoding='utf-8')


front = """## 出版信息
| 项 | 内容 |
|---|---|
| 书名 | 《为何CPI失灵了？——价格分层与经济信望爱的修复》 |
| 英文书名 | %s |
| 著者 | 王德生 |
| 执笔 | 复合主体：王德生立题、口述承重命题与裁定，Claude 执笔与统稿（十个写作智能体分章并行执笔） |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 %d 号 |
| ISBN | %s |
| 定价 | %s |
| 开本 | 170 mm × 240 mm |
| 字数 | 约 20 万字 |
| 版次 | %s |

AI 协作声明：本书的判断、口径与承重命题由王德生于 2026 年 10 月 27 日口述给出；文字在其指令下由 AI（Claude）协作成稿，并经其审定。

数据说明：书中具体数字取自国家统计局等官方发布与公开媒体报道，出处列于各章末「本章数据出处」；本书自行换算的比值逐处注明；查不到可靠数字的地方明写「没有查到」，或标〔待核〕。涉及 2024—2026 年的事实与数据，截至 2026 年 10 月。

引文说明：凡带引号的转述，请读作「大意如此」；直接引语每处不超过一句。

陪读人物钟守田、钟晓禾、周明远，以及书中各个算账的例子，均为虚构，不承担证据。本书讲经济的道理，不构成投资或理财建议。

版权所有　侵权必究

## 题词

【题词】差价不是成本的读数，是信心的读数。

## 作者介绍

王德生，SDE（显露·差异序列·特征纠缠）发生学本体论的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人、首席执行官。

生长于中国农村，父亲是农民。1990 年进入湘潭大学，后获中国科学院计算数学博士学位，并在中国科学院完成博士后研究。曾任教于英国斯旺西大学与新加坡南洋理工大学，2005 年起定居新加坡。

他在德麦国际出版社出版「普通人都能明白的」系列专著多部，把发生学的眼光放进哲学、经济、教育、身体与日常生活。本书是这个系列里的一本经济学主题卷：从一只苹果的两个价格出发，追问 CPI 为什么读不出今天的经济。

""" % (M.TITLE_EN, M.NO, M.ISBN, M.PRICE, M.EDITION)
front += conv(rd('ch00-preface.md')).replace('## 前言　', '## 前言　', 1)
(HERE / 'front').mkdir(exist_ok=True)
(HERE / 'front' / '00-前置.md').write_text(front, encoding='utf-8')

ranges = [(1, 4), (5, 9), (10, 13), (14, 17), (18, 22)]
(HERE / 'parts').mkdir(exist_ok=True)
parts = []
for k, (a, b) in enumerate(ranges, 1):
    txt = '\n\n'.join(conv(rd('ch%02d.md' % n)) for n in range(a, b + 1))
    assert txt.lstrip().startswith('# 第%s编' % CNB[k]), (k, txt[:40])
    (HERE / 'parts' / ('%02d-第%s编.md' % (k, CNB[k]))).write_text(txt, encoding='utf-8')
    parts.append(txt)

app = conv(rd('ch24-appendix.md'))
i1 = app.index('## 附录一'); i2 = app.index('## 附录二')
intro = app[:i1].replace('## 附录', '').strip()
intro = '附录一件：在自己的城市里，自己记一份价差，供做、供对、供回写。本书用到和参考的书与文献，见「参考书目」。'
a1 = app[i1:i2].strip()
bib = app[i2:].replace('## 附录二　参考书目', '# 参考书目', 1).strip()
post = conv(rd('ch23-postscript.md')).replace('## 后记', '# 后记', 1)
back = '# 附录\n\n%s\n\n%s\n\n%s\n\n%s\n' % (intro, a1, bib, post)
(HERE / 'back').mkdir(exist_ok=True)
(HERE / 'back' / '12-后置.md').write_text(back, encoding='utf-8')

book = front + '\n' + '\n\n'.join(parts) + '\n\n' + back
(HERE / 'book.md').write_text(book, encoding='utf-8')
print('han', len(re.findall(r'[一-鿿]', book)), 'chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)))
