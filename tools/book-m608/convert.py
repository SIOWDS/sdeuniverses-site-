#!/usr/bin/env python3
"""第 608 号《彩超医生会被AI替代吗？——病症符号发生学》：把统稿各件 rev/*.md 转成 569/606 版式工具链（build.py）认的分卷稿。
只做格式转换（标题层级、章末三块转框、学员案例位改称作者案例位），不改正文文字，另加：出版信息、作者介绍、导读、三编编题、参考书目说明。
用法：python3 convert.py --src /home/claude/cdus-ai/rev
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
SRC = Path(sys.argv[sys.argv.index('--src') + 1])
han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = [('第一编　是什么：线索、三觉与定位', [1, 2, 3]), ('第二编　怎么做：下一刀、其他情况与分歧', [4, 5, 6]), ('第三编　为什么：单点的天花板、会发生的系统与责任', [7, 8, 9])]
BOXES = {'带走的话': '带走的话', '两行小账': '小账', '术语附注': '术语附注'}
CASE_FILLED = '''【作者亲历】这是作者进修时亲眼见到的一个病例，据作者提供的访谈整理，细节待本人核对。

一次车祸之后，几位伤者被送到医院。其中一位没有明显外伤，也没有流血，还站在旁边帮忙搬抬别的伤者。老师问他有没有不舒服，他说没事，让大家赶快去救别人。

老师没有因为这句“没事”就结束询问，而是接着问他受伤的经过。他这才说，电动车的车把曾经撞到过肚子。老师坚持让他做了急诊床旁超声。检查发现，他腹腔里有大量积血，随即被紧急送进手术室，保住了性命。

作者说，这个病例让她记到今天的，不只是超声能看到积血，而是那一句“没事”。外表平静，本人说没事，旁人也跟着放了心，这些都是“灯还没有亮”的样子。老师多问的那一句，才把一个看不出来的东西，放回了这个人的受伤经过里。

这一段不给任何判断标准，也不是说碰到这种情况就该怎样。它只是记下一件事：图上、身上都看不出来的时候，那一句追问，有时就是线索的开头。'''


def conv_body(text, level):
    """level=2：章（## 第 N 章）；前言/结语走各自的头"""
    lines = text.rstrip().split('\n')
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        hm = re.match(r'^(#{1,6}) (.*)$', l)
        if hm:
            lvl, t = len(hm[1]), hm[2].strip()
            if lvl == 2 and t in BOXES:
                j = i + 1
                body = []
                while j < len(lines) and not re.match(r'^#{1,2} ', lines[j]):
                    body.append(lines[j]); j += 1
                paras = [x.strip() for x in '\n'.join(body).strip().split('\n') if x.strip()]
                out += ['', '> **%s**' % BOXES[t], '>']
                for k, p in enumerate(paras):
                    out.append('> ' + p)
                    if k < len(paras) - 1:
                        out.append('>')
                out.append('')
                i = j
                continue
            if lvl == 2:
                out.append('### ◆ ' + t)
            elif lvl == 3:
                out.append('#### ' + t)
            else:
                out.append('**%s**' % t)
            i += 1
            continue
        if l.strip() in ('---', '***'):
            i += 1
            continue
        out.append(l.rstrip())
        i += 1
    return '\n'.join(out)


def fix_text(s):
    s = s.replace('【学员案例位：此处由学员补', '【作者案例位：此处由作者补')
    s = s.replace('学员案例位', '作者案例位')
    s = s.replace('欢迎学员把它写进手记', '欢迎作者把它写进手记').replace('凡该由学员补真实病例的', '凡该由作者补真实病例的').replace('请学员补上自己科室', '请作者补上自己科室')
    return s


def conv_chapter(text):
    lines = text.strip().split('\n')
    m = re.match(r'^# 第(.+?)章　(.*)$', lines[0])
    assert m, lines[0]
    cn = '零一二三四五六七八九十'
    n = cn.index(m[1]) if m[1] in cn else None
    assert n, m[1]
    body = conv_body('\n'.join(lines[1:]), 2)
    return '## 第 %d 章　%s\n\n%s\n' % (n, m[2].strip(), body)


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    chap = {}
    for k in range(1, 10):
        t = fix_text((SRC / ('%02d-ch.md' % k)).read_text(encoding='utf-8'))
        if k == 7:
            pat = re.compile(r'【作者案例位：此处由作者补一例真实扫查/分歧病例，不超过 800 字。建议写：一次图上的“灯”并不等于结论.*?】')
            assert pat.search(t), 'ch7 灯 slot not found'
            t = pat.sub(lambda m: CASE_FILLED, t, count=1)
        chap[k] = conv_chapter(t)
    total = 0
    book = []
    for k, (title, rng) in enumerate(PARTS, 1):
        segs = ['# ' + title, '']
        for n in rng:
            c = chap[n]
            total += han('\n'.join(x for x in c.splitlines() if not x.startswith('#')))
            segs.append(c)
        md = '\n'.join(segs)
        (HERE / ('parts/%02d.md' % k)).write_text(md, encoding='utf-8')
        book.append(md)
    # 前言
    q = fix_text((SRC / '00-前言.md').read_text(encoding='utf-8'))
    ql = q.rstrip().split('\n')
    assert ql[0].startswith('# 前言'), ql[0]
    q = '## ' + ql[0][2:] + '\n\n' + conv_body('\n'.join(ql[1:]), 2)
    # 结语
    j = fix_text((SRC / '10-结语.md').read_text(encoding='utf-8'))
    jl = j.rstrip().split('\n')
    assert jl[0].startswith('# 结语'), jl[0]
    j = '# ' + jl[0][2:] + '\n\n' + conv_body('\n'.join(jl[1:]), 2)
    # 附录
    a = fix_text((SRC / '11-附录.md').read_text(encoding='utf-8'))
    a = re.sub(r'(?m)^## 附录 ([A-E])　', r'## 附录\1　', a)
    a = a.replace('附录 B　学员病例手记位与模板', '附录B　作者病例手记位与模板').replace('附录B　学员病例手记位与模板', '附录B　作者病例手记位与模板')
    fronthan = han(q)
    jiehan = han(j)
    apphan = han(a)
    allhan = total + fronthan + jiehan
    wan = (allhan + apphan) / 10000
    dao = open(HERE / 'daodu.md', encoding='utf-8').read().strip() if (HERE / 'daodu.md').exists() else ''
    bio = open(HERE / 'author.md', encoding='utf-8').read().strip()
    cp = f"""## 出版信息

| 项 | 内容 |
|---|---|
| 书名 | 《{M.TITLE}》 |
| 副题 | {M.SUBTITLE} |
| 英文书名 | {M.TITLE_EN} |
| 著者 | {M.AUTHOR} |
| 指导 | {M.ADVISOR} |
| 执笔 | 杨莉提出问题并署名，王德生指导并口述母题与口径，Claude 协作执笔与统稿 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 {M.NO} 号 |
| ISBN | {M.ISBN} |
| 定价 | {M.PRICE} |
| 开本 | 170 mm × 240 mm |
| 字数 | 约 {wan:.1f} 万字（前言、三编九章、结语与附录，其中前言、九章与结语正文 {allhan:,} 个汉字） |
| 版次 | {M.EDITION_SP} |
| 完稿 | 2026 年 11 月 7 日 |

AI 协作声明：本书的问题由杨莉（彩超医生）提出；母题、口径与“会被替代的不是彩超医生，而是只看图下结论的单点做法”由王德生指导并口述；正文在其指令下由 AI（Claude）协作撰写，经统稿与三审。本书未经独立学术评审，也未经医学顾问审定，书中凡标〔待核〕处汇总在附录 E。

陪读人物与场景：书中的陈医生、小周、老张、王阿姨、李先生等人物和场景都是为讲清道理而构想的，不是真人真事；唯一标明“作者亲历”的一段，据作者提供的访谈整理，待本人核对；其余留出“作者案例位”，等作者补上自己科室里的真病例。

医学声明：本书不作诊断，不给任何具体疾病的诊断标准、治疗建议或数据阈值，不替代医生判断；书中的做法和检验办法，测的是做法，不用于给医生或病人打分、排名或考核。

编号与 ISBN：本书为德麦国际专著第 {M.NO} 号，ISBN {M.ISBN}，按站内书目序列与校验位计算，已对站内书目与预留档核过，无重号。

全书结构：出版信息、作者介绍、前言、导读、目录；第一编是什么（第 1–3 章）；第二编怎么做（第 4–6 章）；第三编为什么（第 7–9 章）；结语；参考书目；附录 A–E。

版权所有　侵权必究

"""
    front = cp + '## 作者介绍\n\n' + bio + '\n\n' + q + '\n' + (('\n## 导读　' + dao.split('\n', 1)[0].lstrip('# ').replace('导读　', '') + '\n\n' + dao.split('\n', 1)[1].strip() + '\n') if dao else '')
    (HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
    bib = open(HERE / 'bib.md', encoding='utf-8').read().strip()
    back = j + '\n\n' + bib + '\n\n' + a.strip() + '\n'
    back = re.sub(r'(?m)^## ◆ ', '### ◆ ', back)
    (HERE / 'back/12-后置.md').write_text(back, encoding='utf-8')
    (HERE / 'book.md').write_text('\n\n'.join([front] + book + [back]), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': allhan, 'chapters': total}, ensure_ascii=False))
    print('ok chapters-han', total, 'body-han', allhan, 'appendix', apphan)


main()
