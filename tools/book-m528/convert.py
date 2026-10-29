#!/usr/bin/env python3
"""第 528 号《未来大学的课堂模式典范革命——九问模式》（由第 527 号 convert.py 改来）：
把三审定稿（intro.md 导论、ch01–ch26 二十六章、outro.md 结语、appx1.md／appx2.md 两件附录）与
matter/{parts.md 七编编序, front.md 题词与作者介绍, back_full.md 参考书目·附录总说明·后记}
转成 220/302 版式工具链的分卷稿。只做格式转换，不动正文文字。
章题「# 第N章　T」→「## 第N章　T」；节题「## T」→「### ◆ T」；小节「### T」→ 加粗段；去掉分隔线。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m528/convert.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
CNB = ['', '一', '二', '三', '四', '五', '六', '七']
PARTS = {1: (1, 2, 3, 4), 2: (5, 6, 7), 3: (8, 9, 10, 11), 4: (12, 13, 14), 5: (15, 16, 17, 18), 6: (19, 20, 21, 22, 23), 7: (24, 25, 26)}
han = lambda s: len(re.findall(r'[一-鿿]', s))


def body_of(text):
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
    rd = lambda n: (SRC / n).read_text()
    chap_files = ['intro.md'] + ['ch%02d.md' % i for i in range(1, 27)] + ['outro.md']
    allbody = ''.join(rd(f) for f in chap_files)
    wan = round(han(allbody) / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        'AI 协作声明：本书的承重判断出自 WDS博士 2026 年 10 月 29 日的一次问对；文字在其指令下由 AI（Claude）协作写成：Claude 拟定提纲，十路 Claude 分章并行执笔，两路换手评审，十路修订，四路审稿、四路校稿、一路终审，由王德生审定。同一底座的多位执笔者、评审者与编辑不能互作独立证据，书中的判断须由真实课堂来检验。',
        '书中的许宁、沈澄、周川、林晓、韩正、方舟、高远、苏文、叶青、吴静等人物与他们的课堂，都是为说明工序而写下的构造案例，不是调查结果。医学案例一律去标识化，学生不作临床决策；化学案例不涉及危险操作细节。',
        '附录二报告的小样本试跑由同一家族的模型作答与评判，只作先验，不作独立证据；它推翻了本书初稿第 8 章的一个判断，正文已据此改写。',
        '全书结构：导论；七编二十六章——母本与九问、改题与问对、ChatSDE 与通用大模型、打造子本与落壤、学业评估、学科九问样板、回写与大学的领地；结语、参考书目、附录两件与后记。',
        '版权所有　侵权必究']
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + (SRC / 'matter/front.md').read_text().strip() + '\n')
    t, rest = split_head(rd('intro.md'))
    assert t.startswith('导论'), t
    (HERE / 'front/01-导论.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    ptxt = (SRC / 'matter/parts.md').read_text()
    pblocks = [b for b in re.split(r'\n(?=# )', '\n' + ptxt) if b.strip()]
    assert len(pblocks) == 7, len(pblocks)
    nch = 0
    for k, rng in PARTS.items():
        pt, pbody = split_head(pblocks[k - 1])
        assert pt.startswith('第%s编' % CNB[k]), pt
        pbody = '\n\n'.join(x.strip() for x in pbody.strip().split('\n') if x.strip())
        chunks = ['# %s\n\n%s\n' % (pt, pbody)]
        for c in rng:
            ct, cbody = split_head(rd('ch%02d.md' % c))
            m = re.match(r'第\s*(\d+)\s*章[\s　]*(.*)$', ct)
            assert m and int(m[1]) == c, ct
            chunks.append('## 第%d章　%s\n\n%s' % (c, m[2].strip('　 '), body_of(cbody)))
            nch += 1
        (HERE / ('parts/0%d-第%s编.md' % (k, CNB[k]))).write_text('\n'.join(chunks))
    t, rest = split_head(rd('outro.md'))
    assert t.startswith('结语'), t
    (HERE / 'back/11-结语.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    # 后置：参考书目 + 附录总说明 + 两件附录 + 后记
    bf = (SRC / 'matter/back_full.md').read_text().strip()
    # 参考书目以三审定稿的 refs.md（即 30_参考文献.md）为准，替换 back_full.md 里的旧抄本
    refs = rd('refs.md').strip().split('\n', 1)[1].strip()
    r0 = bf.index('\n## 外文文献'); r1 = bf.index('\n# 附录')
    bf = bf[:r0] + '\n' + refs + '\n' + bf[r1:]
    i = bf.index('\n# 后记')
    appx = []
    for f in ('appx1.md', 'appx2.md'):
        at, abody = split_head(rd(f))
        appx.append('## %s\n\n%s' % (at, body_of(abody)))
    back = bf[:i].rstrip() + '\n\n' + '\n'.join(appx) + '\n' + bf[i:] + '\n'
    (HERE / 'back/12-后置.md').write_text(back)
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CNB[k]) for k in range(1, 8)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', nch, len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan)


if __name__ == '__main__':
    main()
