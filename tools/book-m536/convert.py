#!/usr/bin/env python3
"""第 536 号《AI时代普通人的知识发生机会》：把三审定稿（meta.SRC 下 front.md、part01–16.md、ch001–096.md、back.md）
转成 220/302 版式工具链的分卷稿（工具链承自第 532 号）。只做格式转换，不动正文文字。

结构：前置（出版信息 · 题词 · 作者介绍 · 本版说明）→ 导论 → 第一至十六编（每编六章，共九十六章）→ 参考书目 → 版本说明。
本书无结语（第 96 章即收束）、无附录。
章题「## 第N章　T」不变；节题「### 一、T」→「### ◆ 一、T」；正文中的 **…** 不保留。
产物：front/00-前置.md、front/01-导言.md、parts/NN.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m536/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
han = lambda s: len(re.findall(r'[一-鿿]', s))
INTRO = json.loads((HERE / 'parts_intro.json').read_text(encoding='utf-8'))

AUTHOR_INTRO = [
    '**王德生**（Desheng Wang），博士，SIO 本体论与 SDE 发生学（显露·差异序列·特征纠缠）创立者，德麦国际（Demai International）创始人、董事长，主持 SDE Universes 平台与德麦国际专著出版体系。',
    '计算数学出身：湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后；曾任英国威尔士大学斯旺西分校高级研究员、新加坡南洋理工大学数学系助理教授（博导）与资深研究科学家，在计算数学与图形学国际期刊发表论文四十余篇。2015 年起回国推广三视角方法论，在各地高校讲学数百场；2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。',
    '本书的核心问题、SDE 框架与田间原生观察由王德生提出；正文由 AI（Claude）协作撰写、整理与三审统稿。',
]


def sec_heads(text):
    out = []
    for line in text.split('\n'):
        if line.startswith('### '):
            out.append('### ◆ ' + line[4:].strip())
        elif line.strip() == '---':
            continue
        else:
            out.append(line.rstrip())
    s = '\n'.join(out).replace('**', '')
    return re.sub(r'\n{3,}', '\n\n', s).strip() + '\n'


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for old in (HERE / d).glob('*.md'):
            old.unlink()
    chs = [(SRC / ('ch%03d.md' % i)).read_text(encoding='utf-8') for i in range(1, 97)]
    body_han = sum(han('\n'.join(l for l in c.split('\n') if not l.lstrip().startswith('#'))) for c in chs)
    wan = body_han / 10000
    fr = (SRC / 'front.md').read_text(encoding='utf-8')
    secs = {}
    for blk in re.split(r'\n(?=## )', fr):
        if blk.startswith('## '):
            h, _, b = blk.partition('\n')
            secs[h[3:].strip()] = b.strip()
    note = next(v for k, v in secs.items() if k.startswith('本版说明'))
    intro_key = next(k for k in secs if k.startswith('导论'))
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '正文约 %.1f 万字（九十六章正文 %s 个汉字）' % (wan, format(body_han, ','))),
                 ('版次', M.EDITION_SP)]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        '成书说明：本书由王德生提出核心问题、SDE 理论框架与田间原生观察；正文由 AI（Claude）协作撰写与整理，经十六路分编第一审（论证与 SDE 口径）、第二审（事实与来源核对）和统稿第三审。同一底座的多位执笔者与审稿者不能互作独立证据。',
        '书中“草长了一年、割过几次、又长起来，原本板结的土变得松软”是王德生本人的田间经验，也是全书唯一的真实亲历；其余人物、场景与数据均为构想，以〔构想案例〕等标出，不是田野调查、医学研究或平台用户试验。',
        '本书守三条边界：不以农业类比作医学诊断或停药、减药建议；不替儿童代笔，记录先征得同意；不保证收入或创业成功。',
        '全书结构：本版说明；导论；第一至十六编，九十六章；参考书目（R01–R47）与版本说明。',
        '版权所有　侵权必究']
    front = ['\n'.join(cp), '\n\n'.join(notes),
             '## 题词\n\n【题词】%s\n\n【题词署】——本书的田间原型' % M.EPIGRAPH,
             '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_INTRO),
             '## 本版说明\n\n' + note.replace('**', '')]
    (HERE / 'front/00-前置.md').write_text('\n\n'.join(front) + '\n', encoding='utf-8')
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s\n' % (intro_key.replace(' ', '　'), secs[intro_key].replace('**', '')), encoding='utf-8')
    order = json.loads((SRC / '_order.json').read_text())
    pn = 0
    for f in order:
        if not f.startswith('part'):
            continue
        pn += 1
        pt = (SRC / f).read_text(encoding='utf-8').split('\n')[0].lstrip('# ').strip()
        chunks = ['# %s\n\n%s\n' % (pt, '\n\n'.join(INTRO[str(pn)]))]
        for i in range((pn - 1) * 6 + 1, pn * 6 + 1):
            c = chs[i - 1]
            head, _, body = c.partition('\n')
            assert re.match(r'^## 第%d章　' % i, head), head
            chunks.append(head.strip() + '\n\n' + sec_heads(body))
        (HERE / ('parts/%02d.md' % pn)).write_text('\n'.join(chunks), encoding='utf-8')
    bk = (SRC / 'back.md').read_text(encoding='utf-8')
    refs, _, colo = bk.partition('# 本版字数')
    rh, _, rb = refs.partition('\n')
    blocks = [b.strip() for b in re.split(r'\n\s*\n', rb) if b.strip()]
    out, i = [], 0
    while i < len(blocks):
        b = blocks[i]
        if re.match(r'\[R\d+\]', b) and i + 1 < len(blocks) and blocks[i + 1].startswith('http'):
            out.append(b + ' ' + blocks[i + 1]); i += 2
        else:
            out.append(b); i += 1
    intro_p = out[0]
    entries = out[1:]
    back = ['# 参考书目　本书引用来源与核对边界', intro_p] + entries
    ch, _, cb = colo.partition('\n')
    back += ['# 版本说明　本版字数、版本与交付', cb.strip()]
    (HERE / 'back/12-后置.md').write_text('\n\n'.join(back).replace('**', '') + '\n', encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 17)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', body_han, 'all_han', han(b), 'refs', len(entries))


if __name__ == '__main__':
    main()
