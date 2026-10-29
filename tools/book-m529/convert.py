#!/usr/bin/env python3
"""第 529 号《胡敏谈SDE本体论》：把三审定稿（final/ch00_导言.md、ch01–ch09 九章、ch10_结语.md、ch11_附录.md）与
matter/{parts.md 三编编前语, front.md 题词·作者介绍·前言} 转成 220/302 版式工具链的分卷稿（工具链承自第 527 号）。
只做格式转换，不动正文文字。
章题「# 第X章　T」→「## 第N章　T」；节题「## 一、T」→「### ◆ 一、T」；小节「### T」→ 加粗段；
「## 本章参考文献」→「### 本章参考文献」（不加菱形，build.py 据此切到书目体例）。
产物：front/00-前置.md、front/01-导言.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m529/convert.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
FIN = SRC / 'final'
CNB = ['', '一', '二', '三']
CNN = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
PARTS = {1: (1, 2, 3), 2: (4, 5, 6), 3: (7, 8, 9)}
han = lambda s: len(re.findall(r'[一-鿿]', s))


def body_of(text):
    out = []
    for line in text.split('\n'):
        if re.match(r'^## .*参考文献\s*$', line):
            out.append('### ' + line[3:].strip())
        elif re.match(r'^## ', line):
            out.append('### ◆ ' + line[3:].strip())
        elif re.match(r'^### ', line):
            out.append('**' + line[4:].strip() + '**')
        elif line.strip() == '---':
            continue
        else:
            out.append(line.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def wide_tables_to_blocks(text):
    """五栏以上的宽表（附录二总表）在 170 mm 开本里排不下：逐行改成「**首栏**」＋各栏一段，文字不动。"""
    out, rows = [], []

    def flush():
        if not rows:
            return
        cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
        cells = [r for r in cells if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
        if len(cells[0]) < 5:
            out.extend(rows)
        else:
            head = cells[0]
            for r in cells[1:]:
                out.append('### %s' % r[0]); out.append('')
                for h, c in zip(head[1:], r[1:]):
                    out.append('**%s**：%s' % (h, c)); out.append('')
        rows.clear()
    for line in text.split('\n'):
        if line.startswith('|'):
            rows.append(line); continue
        flush(); out.append(line)
    flush()
    return '\n'.join(out)


def split_head(text):
    head, _, rest = text.strip().partition('\n')
    return head.lstrip('# ').strip(), rest


def main():
    rd = lambda n: (FIN / n).read_text()
    chap_files = ['ch00_导言.md'] + ['ch%02d.md' % i for i in range(1, 10)] + ['ch10_结语.md', 'ch11_附录.md']
    allbody = ''.join(rd(f) for f in chap_files)
    wan = round(han(allbody) / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('母本', '王德生《SDE思想体系入门》（德麦国际专著第 395 号）'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        'AI 协作声明：本书的九个问题由胡敏提出，她就九问与 ChatSDE 的问对是本书的材料。文字在其问题与问对的基础上由 AI（Claude）协作写成：Claude 拟定写作总则与详细大纲，十路 Claude 分章并行执笔，十二路一审核实事实与引注，十二路二审校对文字，Claude 三审统稿。同一底座的多位执笔者与编辑不能互作独立证据，书中的判断须由读者的生活与今后的研究来检验。',
        '书中人物均为说明道理而构造的例子，首次出现处已标明，不是病例报告，也不是调查结果。本书讨论怎样看健康、怎样提问，不提供诊疗建议；红旗症状请立即就医，用药请遵医嘱。',
        '全书结构：前言；导言；三编九章——显露与纠缠、起手与序列、矛盾与回写；结语与四件附录。',
        '版权所有　侵权必究']
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + (SRC / 'matter/front.md').read_text().strip() + '\n')
    t, rest = split_head(rd('ch00_导言.md'))
    assert t.startswith('导言'), t
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    ptxt = (SRC / 'matter/parts.md').read_text()
    pblocks = [b for b in re.split(r'\n(?=# )', '\n' + ptxt) if b.strip()]
    assert len(pblocks) == 3
    nch = 0
    for k, rng in PARTS.items():
        pt, pbody = split_head(pblocks[k - 1])
        assert pt.startswith('第%s编' % CNB[k]), pt
        pbody = '\n\n'.join(x.strip() for x in pbody.strip().split('\n') if x.strip())
        chunks = ['# %s\n\n%s\n' % (pt, pbody)]
        for c in rng:
            ct, cbody = split_head(rd('ch%02d.md' % c))
            m = re.match(r'第([一二三四五六七八九])章[\s　]*(.*)$', ct)
            assert m and CNN[m[1]] == c, ct
            chunks.append('## 第%d章　%s\n\n%s' % (c, m[2].strip('　 '), body_of(cbody)))
            nch += 1
        (HERE / ('parts/0%d-第%s编.md' % (k, CNB[k]))).write_text('\n'.join(chunks))
    t, rest = split_head(rd('ch10_结语.md'))
    assert t.startswith('结语'), t
    (HERE / 'back/11-结语.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    # 附录：「# 附录」总页 +「## 附录一　…」各件；件内「### 」小节保留为小标题
    (HERE / 'back/12-后置.md').write_text(wide_tables_to_blocks(rd('ch11_附录.md')).strip() + '\n')
    files = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/0%d-第%s编.md' % (k, CNB[k]) for k in range(1, 4)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', nch, len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan)


if __name__ == '__main__':
    main()
