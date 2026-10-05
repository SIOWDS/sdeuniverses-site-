#!/usr/bin/env python3
"""把 src/（书稿分文件）转成成书流水线格式：front/ parts/ back/。核验状态行汇入附录七。"""
import re
from pathlib import Path
ROOT = Path(__file__).parent
SRC = ROOT / 'src'
for d in ('front', 'parts', 'back'):
    (ROOT / d).mkdir(exist_ok=True)
rd = lambda n: (SRC / n).read_text().strip()
NUM = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一']
PARTS = [("打字机上那一页", 1, 3, "这一编三章，从一张打字机里没打完的纸写起，认识一个叫新来者的人，再把全书要问的事放到桌面上。第 3 章是本编结算，先立下「攒」这个字。"),
("新来者", 4, 7, "这一编四章，写她从出生到 1933 年的前半生。看她的第一块土，看她第一次被逼着开口。第 7 章结算：第一张桌，多半靠别人垫位。"),
("没有桌子的人", 8, 13, "这一编六章，写 1933 到 1951 年：被拘、出走、失去国籍、重新开口。每一次桌子被抽走，她都先开了口。第 13 章把这十八年摆成一张表。"),
("桌子：劳动、工作、行动", 14, 19, "这一编六章，讲她最有名的一套分法。用饭桌、书桌、圆桌的日子，讲清劳动、工作、行动和「世界」。第 19 章结算。"),
("开端：诞生性与「谁」", 20, 24, "这一编五章，讲她最看重的两个词：诞生性与「谁」。她看见了每个人都是新来者，本书在这里问第一个小问题。第 24 章结算。"),
("承诺与宽恕：她已经有的回写", 25, 30, "这一编六章，把她的回写写足：宽恕、承诺、立国、议事会。先说她对在哪儿，再看她停在哪儿。第 30 章结算。"),
("玻璃亭", 31, 35, "这一编五章，写耶路撒冷的审判与它引起的风暴。写法克制：只问这件事怎样把她引向「思考」，不判谁对谁错。第 35 章结算。"),
("思考与良知", 36, 38, "这一编三章，讲她说的思考，是一个人和自己同桌。这是回看最小的场子。第 38 章结算。"),
("没写完的判断", 39, 42, "这一编四章，是全书下刀最重的地方，也最小心：她没写完的那一页，问的正是回看落在哪里。第 42 章结算。"),
("攒：开端是一条链", 43, 48, "这一编六章，是本书自己的一步：开端是一条会攒的链。讲门槛、回写、次序，也讲怎样检验、怎样会错。第 48 章结算。"),
("AI 时代的新来者", 49, 53, "这一编五章，是推论，不是证据。人与 AI 一起写东西，开端会怎样。本编每章都写明：尚无数据。第 53 章结算。")]
verif = {}

def fix_chapter(n, t):
    out, skip = [], False
    lines = t.strip().splitlines()
    for ln in lines:
        s = ln.rstrip()
        if s.startswith('核验状态：') or s.startswith('核验状态:'):
            verif[n] = s.split('：', 1)[1].strip().replace('|', '／'); continue
        if re.match(r'^◆ ', s):
            out.append('### ' + s); continue
        m = re.match(r'^\*\*带走的话\*\*[：:](.+)$', s)
        if m:
            out += ['> **带走的话**', '>', '> ' + m[1].strip().strip('*')]; continue
        m = re.match(r'^\*\*带走的话[：:](.+?)\*\*$', s)
        if m:
            out += ['> **带走的话**', '>', '> ' + m[1].strip()]; continue
        m = re.match(r'^(开门还是关门)[：:](.+)$', s)
        if m:
            out += ['> **小账**  ', '> 开门还是关门：' + m[2].strip() + '  ']; continue
        m = re.match(r'^(攒下来没有)[：:](.+)$', s)
        if m:
            out += ['> 攒下来没有：' + m[2].strip()]; continue
        out.append(s)
    txt = '\n'.join(out)
    txt = re.sub(r'\n{3,}', '\n\n', txt)
    # 小账两行之间不能有空行
    txt = re.sub(r'(> 开门还是关门：[^\n]*)\n\n(> 攒下来没有：)', r'\1\n\2', txt)
    return txt.replace('第 54 章', '结语')

def front():
    info = rd('front_00_出版信息与作者介绍.md')
    info = info.replace('| 项目 | 内容 |', '| 字段 | 内容 |')
    au = ("## 作者介绍\n\n王德生，德麦国际创办人，SDE 学派的提出者。SDE 是「显露—差异—纠缠」三个词的缩写，是一套看事情怎样发生的方法：一样东西长成现在的样子，是在一片具体的地上，经过一步一步的路长出来的。\n\n"
          "他主持编写了「普通人都能懂」系列，用这套方法解读中外思想家。\n\n"
          "本书把这套方法用在阿伦特身上：看她怎样看见每个人都是世界的新来者，又怎样把「开头」写成一次次的奇迹；再问一个小问题：开头，怎样才能攒下来？\n")
    info = re.sub(r'## 作者介绍.*$', au, info, flags=re.S)
    head = "# 普通人都能明白的阿伦特\n\n一个人、打字机上的一页纸，与 SDE 的解构\n\n王德生　著\n\n德麦国际\n\n---\n\n"
    out = head + info + '\n\n---\n\n'
    for n in ('front_01_前言.md', 'front_02_导读.md', 'front_03_导论.md'):
        t = rd(n)
        t = re.sub(r'^◆ ', '### ◆ ', t, flags=re.M)
        out += t + '\n\n---\n\n'
    (ROOT / 'front/00-前置.md').write_text(out.rstrip() + '\n')

def parts():
    for i, (title, s, e, intro) in enumerate(PARTS):
        body = f'# 第{NUM[i]}编　{title}\n\n{intro}\n\n---\n\n'
        chs = []
        for n in range(s, e + 1):
            chs.append(fix_chapter(n, rd(f'ch_{n:02d}.md')))
        body += '\n\n---\n\n'.join(chs)
        (ROOT / 'parts' / f'{i+1:02d}-第{NUM[i]}编.md').write_text(body + '\n')

def back():
    # 结语 = 第 54 章
    t = fix_chapter(54, rd('ch_54.md'))
    t = re.sub(r'^## 第 54 章　', '# 结语　', t, count=1)
    (ROOT / 'back/09-结语.md').write_text(t + '\n')
    refs = rd('back_01_参考书目.md')
    refs = re.sub(r'^## ', '# ', refs, count=1)
    app = rd('back_02_附录.md')
    app = re.sub(r'^## 附录\n', '# 附录\n', app, count=1)
    rows = ['| 章 | 本章〔待核〕项与说明 |', '|---|---|'] + ['| %d | %s |' % (n, verif[n]) for n in sorted(verif)]
    tbl = '\n'.join(rows)
    app = re.sub(r'### 四、总表.*$', '### 四、各章核验状态汇总\n\n下表原样汇集各章末尾的核验状态，供成书核验时逐条对照。\n\n' + tbl + '\n', app, flags=re.S)
    post = rd('back_03_后记.md')
    post = re.sub(r'^## ', '# ', post, count=1)
    (ROOT / 'back/10-后置.md').write_text(refs + '\n\n---\n\n' + app + '\n\n---\n\n' + post + '\n')

front(); parts(); back()
print('ok', len(verif), 'verif rows')
