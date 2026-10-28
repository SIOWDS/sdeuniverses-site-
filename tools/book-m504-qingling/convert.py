#!/usr/bin/env python3
"""第 504 号《被清零的不是博士》：把 meta.SRC 下的定稿（ch00 导论、ch01…ch13 十三章、ch14 结语）
转成 220/302 版式工具链的分卷稿。只做格式转换，不动正文文字：
  · 章题「# 第X章　题」→「## 第 N 章　题」；章内「## …」→「### ◆ …」；章内「### …」→ 加粗小标题段；
  · 四编编序为本脚本写定的一段；
  · 前置：出版信息、题词、写在前面；后置：后记（成书说明）。
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
CNUM = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三']
PARTS = [
    ('第一编', '困境：统一性的终结', range(1, 5),
     '这一编讲困境从哪里来。博士学位曾经值钱，是因为它在陌生人之间替人做了确认，而它靠的是三重统一：统一的训练、统一的尺度、统一的阶梯。大模型吃进全人类的公共知识，吐出公共知识的最优平均，它最先打穿的，正是价值寄存在统一性上的那些位置。于是旧范式开始给出自相矛盾的读数；而更深的伤口在后面：统一性训练在所有人的善意下，把一个人的来路磨平了。这一编最后留下一个问题，全书都要回答：来路已经被磨掉的人怎么办。'),
    ('第二编', '误诊：两条走不通的出路', range(5, 7),
     '面对地面在动，人最先想到的出路有两条，看起来方向相反，其实犯的是同一个错。一条是死守统一：多发论文、冲排名、早上车、追热点，在同一把尺子上挤得更紧，等于和一台不会累的机器赛跑。另一条是散成碎片：既然阶梯靠不住，那就做有意思的事、各走各的，结果散开以后没有任何东西能把一个人的工作接到别人那里。一个死守统一性，一个逃离统一性，都把它当作唯一的坐标，没有人把它换掉。'),
    ('第三编', '转移：从统一性到同一性谱系', range(7, 10),
     '这一编讲换掉的是什么。组织原则从"谁说了算"换成"谁和谁在哪一层相同"：统一性像发校服，同一性像一个家族的人长得有几分像，有人像得多、有人像得少。这是一次典范转移，靠的不是宣言，而是让人照着做的例题。落到一个博士身上，同一性有三层梯度：高同一性层是接口，变薄层正被机器接管，近零层是只属于你的来路。判断力就长在这最后一层，在统一性里它只是"能力"，在谱系里它才有了名分。'),
    ('第四编', '出路：谱系怎样长出来', range(10, 14),
     '最后一编讲出路，个人与制度各担一半。先正面回答门槛问题：来路不是天赋，也不是现成的"真我"，而是把经历重新接到问题上，它可以重新长出来，但需要时间与容许。再讲与 AI 的分工：机器接管统一性那一层，人负责来路与判断，并守住几条纪律。然后讲谱系的价值由谁来兑现：问题持有者、只看证据的同行、能接着用下去的作品。最后转向制度：导师、学位、评价与培养过程怎样重写，谁来帮来路已被磨平的人长出来。'),
]
han = lambda s: len(re.findall(r'[一-鿿]', s))


def curly(line):
    """直引号 " 成对换成中文引号 “ ”。"""
    if '"' not in line or line.lstrip().startswith('|'):
        return line
    out, op = [], True
    for ch in line:
        if ch == '"':
            out.append('“' if op else '”'); op = not op
        else:
            out.append(ch)
    return ''.join(out)


def body_convert(text):
    out = []
    for ln in text.replace('\r', '').split('\n'):
        ln = curly(ln)
        s = ln.strip()
        if s.startswith('#### '):
            out.append('**%s**' % s[5:].strip()); continue
        if s.startswith('### '):
            out.append('**%s**' % s[4:].strip()); continue
        if s.startswith('## '):
            out.append('### ◆ %s' % s[3:].strip()); continue
        if re.fullmatch(r'-{3,}', s):
            continue
        out.append(ln.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def split_head(name):
    t = (SRC / name).read_text().replace('\r', '')
    first, _, rest = t.partition('\n')
    assert first.startswith('# '), (name, first)
    return curly(first[2:].strip()), rest


APP = {}
for _f in sorted(Path('/home/claude/apparatus').glob('part*.json')):
    APP.update(__import__('json').loads(_f.read_text()))


def apparatus(key, txt):
    """版面装置（第 504 号美化）：章首「这一章的问题」、章中金线引语（原文摘句）、章末「带走的话＋小账」。"""
    a = APP.get(key)
    if not a:
        return txt
    paras = txt.strip().split('\n\n')
    for s in a.get('pulls', []):
        s = curly(s.strip())
        idx = next((i for i, x in enumerate(paras) if s in x and not x.startswith(('#', '>'))), None)
        assert idx is not None, (key, s[:20])
        paras.insert(idx + 1, '> **%s**' % s)
    q = curly(a['question'].strip())
    head = ['> **这一章的问题**：' + q]
    tail = ['> **带走的话**\n> ' + curly(a['takeaway'].strip()),
            '> **小账**\n' + '\n'.join('> ' + curly(x.strip()) for x in a['ledger'])]
    return '\n\n'.join(head + paras + tail) + '\n'


PREFACE_RAW = [
    '本书写给正在读博、刚刚毕业，或者正在犹豫要不要读博的人。它从一条在国内短视频平台流传的视频说起，那条视频的标题是"Anthropic 科学家宣布：全球博士生职业生涯一夜清零"。标题是夸张的，演讲本身却提出了一个真问题。本书的回答是：被清零的不是博士，是那条人人都走的路；AI 冲击的不是某种职业，而是统一性；出路在于看清自己在同一性谱系的哪一层，并把自己的来路重新长出来。',
    '全书分四编。第一编讲困境从哪里来，第二编讲两种看起来相反、其实同病的误诊，第三编讲这次典范转移换掉的是什么，第四编讲出路，个人与制度各担一半。每个观点都配了一个读者一看就懂的场景，可以从任何一章读起；但第四章提出的门槛问题，最好和第十章、第十三章连着读。',
    '书中的林晓、周宁、陈哲、唐教授、苏敏、何川、宋可等人物均为综合虚构，他们的经历取材于许多博士生的处境，但不对应任何具体的个人，也不承担证据。书中提到的那场演讲及其内容，依据的是公开的演讲幻灯片与中文编译稿，只述大意。本书没有做任何统计调查，书中凡说到普遍现象，都是定性的描述。',
]
POSTSCRIPT_RAW = [
    '这本书的判断，来自 2026 年 10 月 28 日清晨的一次对话。WDS博士在手机上刷到那条"全球博士生职业生涯一夜清零"的短视频，读完演讲原貌之后，说了两句话："真正 AI 冲击的是统一性，救赎之路是同一性谱系"；"这是新文明的典范转移：从统一性到同一性谱系"。全书就是把这两句话，放到一个博士生的处境里，一层一层讲开。',
    '本书在站内前作上往前走了一步。《新文明诞生：同一性谱系化》（德麦国际专著第 402 号）讲的是新文明的总图；《知识分子向何处去？》讲的是知识分子的职业典范转移。本书把镜头推近，对准站在统一性最密集位置上的那一群人：还在读博、阶梯还没爬完就被抽了梯子的人。',
    '成书方式如实交代：书名、四编结构、读者对象、"出路两头并重并专门处理门槛问题"与二十万字的篇幅，经 WDS博士逐项裁定；导论、十三章与结语由十五路写作智能体（Claude）依同一份写作总纲并行执笔，再由 Claude 统稿，统一人物设定、术语与事实口径。署名王德生。',
]

PREFACE = [curly(x) for x in PREFACE_RAW]
POSTSCRIPT = [curly(x) for x in POSTSCRIPT_RAW]
PARTS = [(a, b, c, curly(d)) for a, b, c, d in PARTS]


def front(han_total):
    meta_cp = [
        ('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
        ('执笔', '复合主体：WDS博士定题与裁定，十五路写作智能体（Claude）分章执笔，Claude 统稿'),
        ('出版', '%s（%s）' % (M.PUBLISHER, M.PUBLISHER_EN)),
        ('编号', '德麦国际专著第 %d 号' % M.NO), ('ISBN', M.ISBN), ('定价', M.PRICE),
        ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % round(han_total / 10000)), ('版次', '2026 年 10 月第 1 版'),
    ]
    notes = [
        '书中人物（林晓、周宁、陈哲、唐教授、苏敏、何川、宋可等）及其场景均为综合虚构，不承担证据；书中提到的演讲依据公开幻灯片与中文编译稿转述大意；本书未做统计调查，凡说普遍现象均为定性描述。',
        '本书讨论读博、择业与学术制度，不构成任何个人的升学、就业或心理方面的专业建议。',
        '版权所有　侵权必究',
    ]
    out = ['## 出版信息', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % r for r in meta_cp] + ['']
    out += [x + '\n' for x in notes]
    out += ['## 题词', '', '【题词】被清零的不是博士，', '', '【题词】是那条人人都走的路。', '', '【题词署】——本书判词', '']
    out += ['## 写在前面', ''] + [p + '\n' for p in PREFACE]
    return '\n'.join(out)


def main():
    files = ['ch%02d.md' % k for k in range(0, 15)]
    han_total = sum(han((SRC / f).read_text()) for f in files)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for old in (HERE / d).glob('*.md'):
            old.unlink()
    fr = front(han_total)
    (HERE / 'front/00-前置.md').write_text(fr)
    title, rest = split_head('ch00.md')
    assert title.startswith('导论'), title
    lun = '# %s\n\n%s' % (title, apparatus('ch00', body_convert(rest)))
    (HERE / 'front/01-导论.md').write_text(lun)
    parts_txt = []
    for k, (pn, pt, rng, intro) in enumerate(PARTS, 1):
        o = ['# %s　%s' % (pn, pt), '', intro, '']
        for c in rng:
            title, rest = split_head('ch%02d.md' % c)
            m = re.match(r'^第(.+?)章　(.+)$', title)
            assert m and m[1] == CNUM[c], title
            o += ['## 第 %d 章　%s' % (c, m[2]), '', apparatus('ch%02d' % c, body_convert(rest))]
        txt = '\n'.join(o)
        (HERE / ('parts/%02d-%s.md' % (k, pn))).write_text(txt)
        parts_txt.append(txt)
    title, rest = split_head('ch14.md')
    assert title.startswith('结语'), title
    jy = '# %s\n\n%s' % (title, apparatus('ch14', body_convert(rest)))
    (HERE / 'back/11-结语.md').write_text(jy)
    hz = '# 后记　成书说明\n\n' + '\n\n'.join(POSTSCRIPT) + '\n'
    (HERE / 'back/12-后置.md').write_text(hz)
    book = '\n\n'.join([fr, lun] + parts_txt + [jy, hz])
    (HERE / 'book.md').write_text(book)
    print('汉字（源）', han_total, '汉字（分卷稿）', han(book))


if __name__ == '__main__':
    main()
