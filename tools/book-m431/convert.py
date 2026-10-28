#!/usr/bin/env python3
"""第 431 号《大学的典范革命》：把统稿三审后的分章定稿（导论 ch00、第 1—47 章、结语 ch48、编导语 p1—p9，以及后置件 back.md）
转成 220/302 版式工具链的分卷稿。只做格式转换，不动正文文字。
章内「## 一、」→「### ◆ 一、」；章题「# 第N章　」→「## 第N章　」；编导语 → 编首「编序」段。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m431/convert.py --src /home/claude/univ/ch --back /home/claude/univ/back.md
"""
import argparse, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

CNB = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']
PARTS = {1: range(1, 6), 2: range(6, 10), 3: range(10, 16), 4: range(16, 22), 5: range(22, 28),
         6: range(28, 34), 7: range(34, 38), 8: range(38, 45), 9: range(45, 48)}
han = lambda s: len(re.findall(r'[一-鿿]', s))


def body_of(text):
    """章内节题加 ◆；三级题改加粗段；去掉分隔线。"""
    out = []
    for line in text.split('\n'):
        if re.match(r'^## ', line):
            out.append('### ◆ ' + line[3:].strip())
        elif re.match(r'^### ', line):
            out.append('**' + line[4:].strip() + '**')
        elif line.strip() == '---':
            continue
        else:
            out.append(line.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def split_head(text):
    head, _, rest = text.strip().partition('\n')
    return head.lstrip('# ').strip(), rest


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True); ap.add_argument('--back', type=Path, required=True)
    a = ap.parse_args(); S = a.src
    rd = lambda n: (S / n).read_text()
    allbody = ''.join(rd(f) for f in sorted(p.name for p in S.glob('*.md')))
    wan = round(han(allbody + a.back.read_text()) / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.FULL_TITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、口述承重命题与裁定，Claude 分编执笔、统稿与三审'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        'AI 协作声明：本书的母题、承重命题与三个领域的划分由王德生（口述）给出；文字在其指令下由 AI（Claude）分编协作成稿，经统稿与三审，并由其审定。同一底座的多位执笔者与编辑不能互作独立证据，书中的判断须由读者与现实来检验。',
        '书中所引学者原话，一律转述大意；直接引语每处不超过一句。书中的制度设想、检验条件与失败条件为本书自拟，不是任何研究的结果。',
        '书中的茶园、小区、课堂、诊所等场景凡标「设想」「比如」者，均为说明道理而设，不是调查报告。',
        '王德生 2026 年 10 月 28 日的口述命题，登记于附录一。',
        '全书结构：导论；九编四十七章——统一性大学的兴衰、统一性的去向、谱系发生、自然科学、社会科学、人文学科、交叉之地、重生的大学、典范革命的全景；结语、参考书目、附录与后记。',
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
        pt, pbody = split_head(rd('p%d.md' % k))
        assert pt.startswith('第%s编' % CNB[k]), pt
        pbody = '\n\n'.join(x.strip() for x in pbody.strip().split('\n') if x.strip())
        chunks = ['# %s\n\n%s\n' % (pt, pbody)]
        for c in rng:
            ct, cbody = split_head(rd('ch%02d.md' % c))
            m = re.match(r'第\s*(\d+)\s*章\s*(.*)$', ct)
            assert m and int(m[1]) == c, ct
            chunks.append('## 第%d章　%s\n\n%s' % (c, m[2].strip('　 '), body_of(cbody)))
            nch += 1
        (HERE / ('parts/0%d-第%s编.md' % (k, CNB[k]))).write_text('\n'.join(chunks))
    t, rest = split_head(rd('ch48.md'))
    (HERE / 'back/11-结语.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    (HERE / 'back/12-后置.md').write_text(a.back.read_text().strip() + '\n')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CNB[k]) for k in range(1, 10)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', nch, len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan)


if __name__ == '__main__':
    main()
