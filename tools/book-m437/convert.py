#!/usr/bin/env python3
"""第 437 号《被替代的从来不是人——论AI替代的虚幻》（由第 527 号 convert.py 改来）：
把三审后的分章定稿（ch00_导论.md、ch01–ch37、ch99_结语.md）与 matter/{parts.md 六编编序, front.md 题词与作者介绍,
back_full.md 参考书目·后记} 转成 220/302 版式工具链的分卷稿。只做格式转换，不动正文文字。
章题「# 第X章　T」→「## 第N章　T」；节题「## 一　T」→「### ◆ 一、T」；「## 本章接引」「## 本章史料」→「### ◆ 本章接引」。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m437/convert.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
CH = SRC / 'chapters'
CNB = ['', '一', '二', '三', '四', '五', '六']
PARTS = {1: range(1, 7), 2: range(7, 15), 3: range(15, 21), 4: range(21, 27), 5: range(27, 32), 6: range(32, 38)}
han = lambda s: len(re.findall(r'[一-鿿]', s))


def cn2int(s):
    d = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    if '十' in s:
        a, _, b = s.partition('十')
        return (d[a] if a else 1) * 10 + (d[b] if b else 0)
    return d[s]


def body_of(text):
    out = []
    for line in text.split('\n'):
        m = re.match(r'^## ([一二三四五六七八九十]+)[　\s]+(.*)$', line)
        if m:
            out.append('### ◆ %s、%s' % (m[1], m[2].strip()))
        elif re.match(r'^## ', line):
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
    rd = lambda n: (CH / n).read_text()
    chap_files = ['ch00_导论.md'] + ['ch%02d.md' % i for i in range(1, 38)] + ['ch99_结语.md']
    allbody = ''.join(rd(f).split('## 本章接引')[0] for f in chap_files)
    wan = round(han(allbody) / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        'AI 协作声明：本书的母题、核心判断与书名出自王德生 2026 年 10 月 28 日的几轮问对；资料整理、各编执笔、史料核实与三审由王德生与 AI（Claude）组成的复合体协作完成：Claude 拟定写作规范，多路 Claude 分编并行执笔，三审（审稿、校稿、终审）为 AI 辅助审校，由王德生审定。执笔与审校同属一个基底家族，不构成独立复核，书中的判断须由读者与第三十七章所列检验来检验。',
        '书中的阿哲、林岚、小许、周叔、外公等人物都是设想人物，用来说明道理，不是调查对象。书中凡标「设想」「比如」的场景，均为说明而设。',
        '全书结构：导论；六编三十七章——缺口、拆开“替代”、复合体、可消去性、约不掉的工具、替代论之后；结语、参考书目与后记。',
        '版权所有　侵权必究']
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + (SRC / 'matter/front.md').read_text().strip() + '\n')
    t, rest = split_head(rd('ch00_导论.md'))
    assert t.startswith('导论'), t
    (HERE / 'front/01-导论.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    ptxt = (SRC / 'matter/parts.md').read_text()
    pblocks = [b for b in re.split(r'\n(?=# )', '\n' + ptxt) if b.strip()]
    assert len(pblocks) == 6, len(pblocks)
    nch = 0
    for k, rng in PARTS.items():
        pt, pbody = split_head(pblocks[k - 1])
        assert pt.startswith('第%s编' % CNB[k]), pt
        pbody = '\n\n'.join(x.strip() for x in pbody.strip().split('\n') if x.strip())
        chunks = ['# %s\n\n%s\n' % (pt, pbody)]
        for c in rng:
            ct, cbody = split_head(rd('ch%02d.md' % c))
            m = re.match(r'第([一二三四五六七八九十]+)章[\s　]*(.*)$', ct)
            assert m and cn2int(m[1]) == c, ct
            chunks.append('## 第%d章　%s\n\n%s' % (c, m[2].strip('　 '), body_of(cbody)))
            nch += 1
        (HERE / ('parts/0%d-第%s编.md' % (k, CNB[k]))).write_text('\n'.join(chunks))
    t, rest = split_head(rd('ch99_结语.md'))
    assert t.startswith('结语'), t
    (HERE / 'back/11-结语.md').write_text('# %s\n\n%s' % (t, body_of(rest)))
    (HERE / 'back/12-后置.md').write_text((SRC / 'matter/back_full.md').read_text().strip() + '\n')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CNB[k]) for k in range(1, 7)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', nch, len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan)


if __name__ == '__main__':
    main()
