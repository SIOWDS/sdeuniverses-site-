#!/usr/bin/env python3
"""第 434 号：把 /home/claude/chapters/ch00–ch26.md 转成 220/302 版式工具链的分卷稿（front/parts/back/book.md）。只做格式转换，不动正文文字。"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
SRC = Path(M.SRC)
CNB = ['', '一', '二', '三', '四', '五']
PARTS = [  # (编号, 章号区间, 标题, 编序)
 (1, range(1, 5), '两本书：从 The Book 到 Our/My Book',
  'The Book 和 Our/My Book 各是什么符号？为什么一个冠词换成一个代词，就是教育从发现学到发生学的转换？本编立起全书的框架：先说清 The Book 是什么、来自哪里，再说清 Our Book 和 My Book 是什么，最后把谱系四层摆在一起，并老老实实回答一个问题：这和你已经在做的有什么不同。'),
 (2, range(5, 11), '发生：Our/My Book 怎样长出来',
  '两本书具体怎样发生？从母本出发，经过画像与九问，长出班级子本和学生子本，再在两者之间来回回写；老师、学生、AI 三方各做什么。本编是全书的机制部分，每一章都落到一个周五下午能做的最小动作。'),
 (3, range(11, 15), '学段：从小学到大学',
  '同样是 Our/My Book，在小学、中学、大学各长成什么样子？学段之间怎样不再每升一级清零一次？本编按人的成长来落地，并算清应试这笔账。'),
 (4, range(15, 22), '学科：每门课的两本书',
  '在每一门具体的课里，The Book 是什么，My Book 长什么样，Our Book 长什么样；每门课只写它最硬的一个学段拐点，只写它独有的失败。本编共用的三件事，写在第15章开头。'),
 (5, range(22, 26), '学校：制度、风险与检验',
  '一所学校要走到 Our/My Book，评价、风险、归属、落地四件事怎样处理？本书的主张在什么情况下算错？本编打开新的缺口，也把可以检验的条件摆出来。'),
]
def han(s): return len(re.findall(r'[一-鿿]', s))
def conv_chapter(t, as_chapter=True):
    out = []
    for line in t.replace('\r', '').split('\n'):
        s = line.rstrip()
        if re.match(r'^# ', s):
            h = s[2:].strip()
            h = re.sub(r'^第 ?(\d+) ?章', lambda m: '第%s章' % m[1], h)
            out.append('## ' + h); continue
        if re.match(r'^## ', s):
            out.append('### ◆ ' + s[3:].strip()); continue
        if re.match(r'^### ', s):
            out.append('### ' + s[4:].strip()); continue
        out.append(s)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'

def main():
    ch = {n: (SRC / ('ch%02d.md' % n)).read_text() for n in range(0, 27)}
    # 前置
    nchar = sum(han(v) for v in ch.values())
    wan = round(nchar / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    rows = [('书名', '《%s》' % M.FULL_TITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
            ('执笔', '复合主体：王德生立题、定母题与裁定，Claude 分编执笔、统稿与三审'),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
            ('ISBN', M.ISBN)]
    if M.PRICE: rows.append(('定价', M.PRICE))
    rows += [('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]
    for a, b in rows: cp.append('| %s | %s |' % (a, b))
    notes = [
     'AI 协作声明：本书的母题（从 The Book 到 Our/My Book）、The Book 与 Our/My Book 的定义和谱系四层，由王德生给出；文字在其指令下由 AI（Claude）分编协作成稿，经五路审读、返工、校稿与终审，并由其审定。同一底座的多位执笔者与审读者不能互作独立证据，书中的判断须由学校、教师、学生与现实来检验。',
     '书中的学校、班级、教师、学生与家长，除明说取自公开材料处外，均为说明道理而设的构造案例，不是调查报告；书中的时间账、人数与门槛数值是估算或建议值，须在具体学校用试点实际数据校正。',
     '书中提到的做法名（档案袋、项目式学习、知识建构共同体、形成性评价、先行组织者、前概念访谈等），只点名称，不转述具体文献。涉及学生数据、版权与法律的部分，是本书的原则与建议，不是法律意见，上线前请法务审读。',
     '全书结构：导言；五编二十五章——两本书、发生、学段、学科、学校；结语与后记。',
     '版权所有　侵权必究',
    ]
    author = (Path(HERE.parent / 'book-m431/front/00-前置.md').read_text().split('## 作者介绍', 1)[1].strip().split('\n## ')[0])
    preface = open(HERE / 'preface.md').read().strip()
    guide = open(HERE / 'guide.md').read().strip()
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n## 作者介绍\n' + author + '\n\n' + preface + '\n\n' + guide + '\n')
    (HERE / 'front/01-导论.md').write_text(conv_chapter(ch[0]).replace('# 导言　', '# 导言　', 1).replace('## 导言　', '# 导言　', 1))
    (HERE / 'parts').mkdir(exist_ok=True)
    for k, rng, title, intro in PARTS:
        txt = '# 第%s编　%s\n\n%s\n\n' % (CNB[k], title, intro) + '\n'.join(conv_chapter(ch[n]) for n in rng)
        (HERE / ('parts/0%d-第%s编.md' % (k, CNB[k]))).write_text(txt)
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(conv_chapter(ch[26]).replace('## 结语　', '# 结语　', 1))
    (HERE / 'back/12-后置.md').write_text(open(HERE / 'afterword.md').read().strip() + '\n')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CNB[k]) for k in range(1, 6)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan)
if __name__ == '__main__':
    main()
