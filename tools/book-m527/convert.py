#!/usr/bin/env python3
"""第 527 号《子本打造法》：把统稿、审校、终审后的分章定稿（intro.md 导论、ch01–ch09 九章、outro.md 结语）与
matter/{parts.md 三编编序, front.md 题词与作者介绍, back_full.md 参考书目·附录·后记} 转成 220/302 版式工具链的分卷稿。
只做格式转换，不动正文文字。
章题「# 第X章　T」→「## 第N章　T」；节题「## 一、T」→「### ◆ 一、T」；小节「### （一）T」→ 加粗段；去掉分隔线。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m527/convert.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
CNB = ['', '一', '二', '三']
CNN = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
PARTS = {1: (1, 2, 3), 2: (4, 5, 6), 3: (7, 8, 9)}
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
    chap_files = ['intro.md'] + ['ch%02d.md' % i for i in range(1, 10)] + ['outro.md']
    allbody = ''.join(rd(f) for f in chap_files)
    wan = round(len(re.sub(r'\s', '', allbody)) / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        'AI 协作声明：本书的承重判断出自 WDS博士 2026 年 10 月 28 日的一次问对，原话登记于附录一；文字在其指令下由 AI（Claude）协作写成：Claude 拟定写作总纲，十路 Claude 分章并行执笔，四路审稿校稿，Claude 终审统稿，由王德生审定。同一底座的多位执笔者与编辑不能互作独立证据，书中的判断须由读者与真实做出的子本来检验。',
        '书中的阳老师是化名；他的九个具体判断、子本九问、问对回答与子本大纲，都是依据试验设计写下的构想示例，用来说明工序，不是调查结果，实测后将以实测材料替换。书中凡标「设想」「比如」的日常场景，均为说明道理而设。',
        '书中关于 Coral Hart 的数字，均为当事人自报或媒体转述。',
        '全书结构：导论；三编九章——子本是什么、子本怎样发生、子本怎样成书与生长；结语、参考书目、附录与后记。',
        '版权所有　侵权必究']
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + (SRC / 'matter/front.md').read_text().strip() + '\n')
    t, rest = split_head(rd('intro.md'))
    assert t.startswith('导论'), t
    (HERE / 'front/01-导论.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
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
    t, rest = split_head(rd('outro.md'))
    assert t.startswith('结语'), t
    (HERE / 'back/11-结语.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    (HERE / 'back/12-后置.md').write_text((SRC / 'matter/back_full.md').read_text().strip() + '\n')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CNB[k]) for k in range(1, 4)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', nch, len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan)


if __name__ == '__main__':
    main()
