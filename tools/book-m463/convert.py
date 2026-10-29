#!/usr/bin/env python3
"""第 463 号《AI会取代老师吗？——教学的典范转移三维度》：把三审后的分章定稿（导论 ch00、第 1—65 章、结语 ch66、附录 ch67）
转成 220/302 版式工具链的分卷稿（由第 431 号 convert.py 改来）。只做格式转换，不动正文文字。
章内「## 节题」→「### ◆ 节题」；「### 三级题」→ 加粗段；章题「# 第N章　」→「## 第N章　」；各编首章文件里的编题与编首语 → 编首「编序」段；
「待作者确认」标记不进成书。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m463/convert.py --src /home/claude/book/chapters
"""
import argparse, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

CNB = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']
PARTS = {1: range(1, 6), 2: range(6, 16), 3: range(16, 24), 4: range(24, 31), 5: range(31, 39),
         6: range(39, 44), 7: range(44, 58), 8: range(58, 66)}
han = lambda s: len(re.findall(r'[一-鿿]', s))


def clean(text):
    text = re.sub(r'\s*<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\*\*【待作者确认[^】]*】\*\*', '', text)
    text = re.sub(r'【待作者确认[^】]*】', '', text)
    return text


def body_of(text):
    out = []
    for line in clean(text).split('\n'):
        if re.match(r'^## ', line):
            out.append('### ◆ ' + line[3:].strip())
        elif re.match(r'^#{3,} ', line):
            out.append('**' + line.lstrip('#').strip() + '**')
        elif line.strip() == '---':
            continue
        else:
            out.append(line.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def split_head(text):
    head, _, rest = text.strip().partition('\n')
    return head.lstrip('# ').strip(), rest


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True)
    S = ap.parse_args().src
    rd = lambda n: (S / n).read_text(encoding='utf-8')
    allbody = ''.join(rd('ch%02d.md' % i) for i in range(0, 68))
    wan = round(han(allbody) / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.FULL_TITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、口述承重命题与裁定，Claude 分章执笔、统稿与三审'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        'AI 协作声明：本书的母题、三个维度的划分与承重命题由王德生（口述）给出；文字在其指令下由 AI（Claude）分章协作成稿，经统稿与三审，并由其审定。同一底座的多位执笔者与编辑不能互作独立证据，书中的判断须由读者与课堂来检验。',
        '书中所引学者与站内专著的原话，直接引语每处不超过一句，其余一律转述大意。书中的课例、制度设想、检验条件与失败条件为本书自拟，不是任何研究的结果；“每个人有自己的伞”是本书提出的新主张，尚待检验。',
        '书中的课堂、学校、教师、学生、家长与数字，凡未注明出处者，均为说明道理而构造的场景，不是调查报告。',
        '王德生 2026 年 10 月 29 日的口述命题五条，见导论与大纲；全书怎样算错，汇总于附录三。',
        '全书结构：导论；八编六十五章——下岗论的账本、统一性退位给同一性谱系、AI 时代自然科学和数学逻辑符号学的革命、发现退位给发生、真善美价值退位给意义获得、三条转移缺一不可、各科教学怎样转移、新老师；结语与附录。',
        '版权所有　侵权必究']
    author = ('## 作者介绍\n王德生，德麦国际（Demai International）创办人，SDE 本体论的提出者。SDE 三个字母，说的是世界怎样发生：显露、差异序列、特征纠缠。\n'
              '他在中国农村长大，1990 年考入湘潭大学，后在中国科学院获计算数学博士学位，并在那里做博士后研究；之后在斯旺西大学、南洋理工大学任职，2005 年起定居新加坡。\n'
              '他的思想走过四站：三视角、321 智慧系统、SIO 本体论，到今天的 SDE 本体论。他的书由德麦国际出版社出版，多数写给没受过哲学训练、却天天在过日子的人。\n')
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + author)
    t, rest = split_head(rd('ch00.md'))
    (HERE / 'front/01-导论.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    nch = 0
    for k, rng in PARTS.items():
        chunks = []
        for c in rng:
            text = rd('ch%02d.md' % c).strip()
            if c == rng[0]:
                pt, rest = split_head(text)
                assert pt.startswith('第%s编' % CNB[k]), (c, pt)
                m = re.search(r'^# 第\s*\d+\s*章', rest, re.M)
                intro, text = rest[:m.start()], rest[m.start():]
                intro = '\n\n'.join(x.strip() for x in clean(intro).strip().split('\n') if x.strip())
                chunks.append('# %s\n\n%s\n' % (pt, intro))
            ct, cbody = split_head(text)
            m = re.match(r'第\s*(\d+)\s*章\s*(.*)$', ct)
            assert m and int(m[1]) == c, ct
            chunks.append('## 第%d章　%s\n\n%s' % (c, m[2].strip('　 '), body_of(cbody)))
            nch += 1
        (HERE / ('parts/0%d-第%s编.md' % (k, CNB[k]))).write_text('\n'.join(chunks))
    t, rest = split_head(rd('ch66.md'))
    (HERE / 'back/11-结语.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    t, rest = split_head(rd('ch67.md'))
    appx = []
    for line in clean(rest).split('\n'):
        if re.match(r'^### ', line):
            appx.append('**' + line[4:].strip() + '**')
        else:
            appx.append(line.rstrip())
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n' % (t, re.sub(r'\n{3,}', '\n\n', '\n'.join(appx)).strip()))
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CNB[k]) for k in PARTS] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    assert '待作者确认' not in b
    print('ok chapters', nch, len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan)


if __name__ == '__main__':
    main()
