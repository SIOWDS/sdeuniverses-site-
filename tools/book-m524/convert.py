#!/usr/bin/env python3
"""第 524 号《如何产生解决个性化问题的知识？》：把 meta.SRC 下的定稿分章稿（front.md 前言、ch00 序章、ch01–ch15 十五章、ch16 终章、
parts.py 五部部名与部序）转成 220/302 版式工具链的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md（序章）、parts/0N-第N部.md、back/11-结语.md（终章）、back/12-后置.md、book.md。
章标题「# 第X章　T」→「## 第N章　T」；节标题「## 一、T」→「### ◆ 一、T」；小节「### T」→ 加粗段。
"""
import re, sys, importlib.util
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
SRC = Path(M.SRC)
CNB = ['', '一', '二', '三', '四', '五']
CNN = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15}

spec = importlib.util.spec_from_file_location('parts', SRC / 'parts.py'); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)


def body_fix(t):
    t = re.sub(r'^## (.+)$', r'### ◆ \1', t, flags=re.M)
    t = re.sub(r'^### (?!◆)(.+)$', r'**\1**', t, flags=re.M)
    return re.sub(r'\n{3,}', '\n\n', t).strip() + '\n'


def chapter(f):
    t = (SRC / f).read_text()
    head, rest = t.split('\n', 1)
    m = re.match(r'^# 第(.+?)章　(.+)$', head.strip())
    assert m, head
    return '## 第%d章　%s\n\n%s' % (CNN[m[1]], m[2].strip(), body_fix(rest.lstrip('\n')))


def main():
    han = lambda s: len(re.findall(r'[一-鿿]', s))
    allsrc = ''.join((SRC / f).read_text() for f in ['front.md'] + ['ch%02d.md' % i for i in range(17)])
    wan = round(len(re.sub(r'\s', '', allsrc)) / 10000)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    notes = ['本书承重的判断出自 WDS博士 2026 年 10 月 28 日的一次问对，原话登记于附录；文字在 AI 协作下写成：由 Claude 统筹，十七路 Claude 分章执笔，经审稿、校稿、终审三审，Claude 统稿。',
             '书中人物（小周、林姐与乐乐、老陈、老蔡等）及其场景均为虚构，不承担证据；外部思想家只述大意。',
             '书中涉及身体与疾病的段落只谈知识怎样发生与成形，不构成诊疗意见；专业诊治请找医生。',
             '版权所有　侵权必究']
    epi = '## 题词\n\n【题词】知识不在库里，在问对里；问对的结果不是一段回答，而是一部作品。\n\n【题词署】——WDS博士口述，2026 年 10 月\n'
    pre = (SRC / 'front.md').read_text()
    pre = re.sub(r'^# 前言\s*$', '## 前言', pre, count=1, flags=re.M)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + epi + '\n' + pre.strip() + '\n')
    t = (SRC / 'ch00.md').read_text(); head, rest = t.split('\n', 1)
    assert head.startswith('# 序章　'), head
    (HERE / 'front/01-导论.md').write_text(head.strip() + '\n\n' + body_fix(rest.lstrip('\n')))
    (HERE / 'parts').mkdir(exist_ok=True)
    starts = {'ch01.md': 1, 'ch04.md': 2, 'ch08.md': 3, 'ch12.md': 4, 'ch15.md': 5}
    bounds = [(1, 3), (4, 7), (8, 11), (12, 14), (15, 15)]
    for k, (a, b) in enumerate(bounds, 1):
        title, intro = P.PARTS['ch%02d.md' % a]
        assert title.startswith('第%s部　' % CNB[k]), title
        txt = '# %s\n\n%s\n\n' % (title, intro) + '\n'.join(chapter('ch%02d.md' % i) for i in range(a, b + 1))
        (HERE / ('parts/0%d-第%s部.md' % (k, CNB[k]))).write_text(txt)
    t = (SRC / 'ch16.md').read_text(); head, rest = t.split('\n', 1)
    assert head.startswith('# 终章　'), head
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(head.strip() + '\n\n' + body_fix(rest.lstrip('\n')))
    (HERE / 'back/12-后置.md').write_text((HERE / 'back-matter.md').read_text())
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s部.md' % (k, CNB[k]) for k in range(1, 6)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    bk = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第\d+章　', bk, re.M)), 'hanzi', han(bk), 'wan', wan)


if __name__ == '__main__':
    main()
