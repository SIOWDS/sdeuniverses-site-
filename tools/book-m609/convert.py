#!/usr/bin/env python3
"""第 609 号《抉择需要等待——让半成判断自己去长》：把母本 v0.3 的分章稿（ms/*.md）转成 569/608 版式工具链（build.py）认的分卷稿。
只做格式转换（标题层级、章末「带走的话」「小账」转框、编题、前置件、〔待核〕清单），不改正文文字。
用法：python3 convert.py --src /home/claude/jueze-wait/sanshen/ms
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
SRC = Path(sys.argv[sys.argv.index('--src') + 1])
han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = [('第一编　是什么', [1, 2, 3]), ('第二编　怎么判，怎么让它长', [4, 5, 6]),
         ('第三编　同一件事，在不同的行当里', [7, 8, 9, 10]), ('第四编　为什么', [11, 12, 13])]
CN = '零一二三四五六七八九十'


def box(label, paras):
    out = ['', '> **%s**' % label, '>']
    for k, p in enumerate(paras):
        out.append('> ' + p)
        if k < len(paras) - 1:
            out.append('>')
    out.append('')
    return out


def conv_body(text, h2='### ◆ ', h3='#### '):
    """章内：## → ### ◆；### → ####；#### → 粗体行。「**带走的话**：…」转框；「## 带走的话」「## 两行小账」转框。"""
    lines = text.rstrip().split('\n')
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^\*\*带走的话\*\*[：:]\s*(.*)$', l)
        if m:
            paras = [m[1]] if m[1].strip() else []
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].startswith(('>', '#')):
                paras.append(lines[j].strip()); j += 1
            out += box('带走的话', paras)
            i = j
            continue
        hm = re.match(r'^(#{1,6}) (.*)$', l)
        if hm:
            lvl, t = len(hm[1]), hm[2].strip()
            if lvl == 2 and t in ('带走的话', '两行小账', '小账'):
                j = i + 1; body = []
                while j < len(lines) and not re.match(r'^#{1,2} ', lines[j]):
                    body.append(lines[j]); j += 1
                paras = [x.strip() for x in '\n'.join(body).strip().split('\n') if x.strip()]
                out += box('小账' if '账' in t else '带走的话', paras)
                i = j
                continue
            if lvl == 2:
                out.append(h2 + t)
            elif lvl == 3:
                out.append(h3 + t)
            else:
                out.append('**%s**' % t)
            i += 1
            continue
        if l.strip() in ('---', '***'):
            i += 1
            continue
        if re.match(r'^◆ ', l):      # 正文里独占一行的 ◆ 小节名
            out.append('#### ' + l[2:].strip()); i += 1; continue
        out.append(l.rstrip())
        i += 1
    s = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', s)


def conv_chapter(text):
    lines = text.strip().split('\n')
    m = re.match(r'^# 第(\d+)章　(.*)$', lines[0])
    assert m, lines[0]
    return int(m[1]), '## 第 %s 章　%s\n\n%s\n' % (m[1], m[2].strip(), conv_body('\n'.join(lines[1:])))


def split_h2(text, key):
    """取以「## key…」开头、到下一个「## 」之前的一段，返回（标题行, 正文行列表）。"""
    ls = text.split('\n')
    s = next(i for i, l in enumerate(ls) if l.startswith('## ' + key))
    e = next((i for i in range(s + 1, len(ls)) if ls[i].startswith('## ')), len(ls))
    return ls[s], ls[s + 1:e]


def daifa_list():
    """〔待核〕清单：各章含〔待核〕的句子，按章汇总。"""
    items = []
    files = sorted(SRC.glob('ch*.md'))
    for f in files:
        t = f.read_text(encoding='utf-8')
        if 'ch17' in f.name or 'ch16' in f.name or 'ch15' in f.name:
            lab = {'ch15': '附录A', 'ch16': '附录B', 'ch17': '附录C'}[f.name[:4]]
        elif 'ch00' in f.name:
            lab = '前言与导读'
        elif 'ch14' in f.name:
            lab = '结语'
        else:
            lab = '第%d章' % int(re.search(r'ch(\d+)', f.name)[1])
        for l in t.split('\n'):
            if '〔待核' not in l:
                continue
            ss = re.split(r'(?<=[。！？；])', l.strip())
            for s in ss:
                if '〔待核' in s:
                    s = re.sub(r'[*>#|]', '', s).strip()
                    items.append((lab, s[:150] + ('……' if len(s) > 150 else '')))
    return items


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    chap, total = {}, 0
    for k in range(1, 14):
        f = SRC / ('ch%02d.md' % k)
        n, c = conv_chapter(f.read_text(encoding='utf-8'))
        assert n == k, (n, k)
        chap[k] = c
    book = []
    for k, (title, rng) in enumerate(PARTS, 1):
        segs = ['# ' + title, '']
        for n in rng:
            segs.append(chap[n])
            total += han('\n'.join(x for x in chap[n].splitlines() if not x.startswith('#')))
        md = '\n'.join(segs)
        (HERE / ('parts/%02d.md' % k)).write_text(md, encoding='utf-8')
        book.append(md)
    # 前言 / 导读
    t0 = (SRC / 'ch00_前言导读.md').read_text(encoding='utf-8')
    h, body = split_h2(t0, '前言')
    q = '## 前言　' + re.sub(r'^## 前言[：:]', '', h) + '\n\n' + conv_body('\n'.join(body).replace('\n### ', '\n## ').replace('\n#### ', '\n### '))
    h, body = split_h2(t0, '导读')
    d = '## 导读　' + re.sub(r'^## 导读[：:]', '', h) + '\n\n' + conv_body('\n'.join(body).replace('\n### ', '\n## ').replace('\n#### ', '\n### '))
    # 结语
    t14 = (SRC / 'ch14_结语.md').read_text(encoding='utf-8').strip().split('\n')
    m = re.match(r'^# 结语[：:](.*)$', t14[0]); assert m, t14[0]
    j = '# 结语　' + m[1].strip() + '\n\n' + conv_body('\n'.join(t14[1:]))
    # 附录
    apps = []
    for fn, lab in (('ch15_附录A.md', 'A'), ('ch16_附录B.md', 'B'), ('ch17_附录C.md', 'C')):
        tt = (SRC / fn).read_text(encoding='utf-8').strip().split('\n')
        mm = re.match(r'^# 附录 ?([A-D])　(.*)$', tt[0]); assert mm, tt[0]
        apps.append('## 附录%s　%s\n\n%s' % (mm[1], mm[2].strip(), conv_body('\n'.join(tt[1:]))))
    dl = daifa_list()
    dtxt = ['## 附录D　〔待核〕清单', '', '本书凡出处、年代、数字、制度细节一时核不到的地方，都原位标了〔待核〕。下面按章汇总，一条不漏，核到一条，改一条。', '']
    cur = None
    for lab, s in dl:
        if lab != cur:
            dtxt += ['**%s**' % lab, '']; cur = lab
        dtxt.append('- ' + s)
    dtxt.append('')
    apps.append('\n'.join(dtxt))
    fronthan, jiehan = han(q) + han(d), han(j)
    apphan = sum(han(a) for a in apps)
    allhan = total + han(q) + han(d) + jiehan
    wan = (allhan + apphan) / 10000
    bio = open(HERE / 'author.md', encoding='utf-8').read().strip()
    cp = f"""## 出版信息

| 项 | 内容 |
|---|---|
| 书名 | 《{M.TITLE}》 |
| 副题 | {M.SUBTITLE} |
| 英文书名 | {M.TITLE_EN} |
| 著者 | {M.AUTHOR} |
| 执笔 | 王德生立题并口述母题与口径，Claude 协作执笔（二十位写手分章）、统稿与三审 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 {M.NO} 号 |
| ISBN | {M.ISBN} |
| 定价 | {M.PRICE} |
| 开本 | 170 mm × 240 mm |
| 字数 | 约 {wan:.0f} 万字（前言、导读、四编十三章与结语正文 {allhan:,} 个汉字，附录另计） |
| 版次 | {M.EDITION_SP} |
| 完稿 | 2026 年 11 月 7 日 |

AI 协作声明：本书的母题（“半成判断”：准确认出此刻是半成判断，烦恼便少一层）由王德生口述；正文在其指令下由 AI（Claude）协作撰写，经统稿与三审（初审、复审、终审）。本书未经独立学术评审，也未经医学、教育、法律等专业人士审定；书中凡出处、年代、数字、制度一时核不到之处，均原位标〔待核〕，汇总在附录 D。“烦恼”一词的定义目前是暂用的读法，有待作者最后确认。

陪读人物与场景：书中的莫师傅、阿鹤、柯老师、宁姐等人物与场景，都是为讲清道理而构想的，不是真人真事，也不指任何一家单位；凡写“我构想的场景”处，即是构想。

专业边界声明：本书讲的是怎样认出“此刻是半成判断”，不是诊断，不给任何疾病的诊断标准、治疗建议或数值阈值，不给法律或财务建议，不替医生、老师、家长、老板做决定；书中的三问和检查表测的是做法，不用于给任何人打分、排名或考核。涉及医疗、教育、法律、财务的具体决定，请找相应的专业人士。

编号与 ISBN：本书为德麦国际专著第 {M.NO} 号，ISBN {M.ISBN}，按站内书目序列与校验位计算，已对站内书目与预留档核过，无重号。

全书结构：出版信息、作者介绍、前言、导读、目录；第一编是什么（第 1–3 章）；第二编怎么判、怎么让它长（第 4–6 章）；第三编同一件事，在不同的行当里（第 7–10 章，医生、老师、家长、老板）；第四编为什么（第 11–13 章）；结语；参考书目；附录 A–D。

版权所有　侵权必究

"""
    front = cp + '## 作者介绍\n\n' + bio + '\n\n' + q + '\n\n' + d + '\n'
    (HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
    bib = open(HERE / 'bib.md', encoding='utf-8').read().strip()
    back = j + '\n\n' + bib + '\n\n# 附录\n\n' + '\n\n'.join(apps) + '\n'
    back = re.sub(r'(?m)^## ◆ ', '### ◆ ', back)
    (HERE / 'back/12-后置.md').write_text(back, encoding='utf-8')
    (HERE / 'book.md').write_text('\n\n'.join([front] + book + [back]), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': allhan, 'chapters': total}, ensure_ascii=False))
    print('ok chapters-han', total, 'body-han', allhan, 'appendix', apphan, 'daihe', len(dl))


main()
