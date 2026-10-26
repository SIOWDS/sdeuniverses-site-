#!/usr/bin/env python3
"""第 457 号《AI对科研的冲击为何首先表现在数学上？》：把三审定稿（M.SRC 下 01-front … 10-back 十个文件）
转成 220/302 版式工具链（照第 520 号）的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md、parts/01-上篇.md … 04-尾篇.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m457/convert.py
"""
import re, sys, csv
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = Path(M.SRC)


def ends(text):
    """章末：> **带走的话**　…／> **小账**　…（可续行）／**想一想** 后各段 → 220 版式的三个引用框。"""
    L = text.split('\n'); out = []; i = 0
    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^>\s*\*\*带走的话\*\*[　\s:：]*(.*)$', s)
        if m:
            x = re.sub(r'^\*\*(.*)\*\*$', r'\1', m[1].strip())
            out += ['> **带走的话**', '> ' + x, '']; i += 1; continue
        m = re.match(r'^>\s*\*\*小账\*\*[　\s:：]*(.*)$', s)
        if m:
            q = [m[1].strip()] if m[1].strip() else []
            i += 1
            while i < len(L) and L[i].strip().startswith('>'):
                c = L[i].strip().lstrip('>').strip()
                if c: q.append(c)
                i += 1
            out += ['> **小账**'] + ['> ' + c for c in q] + ['']
            continue
        if re.fullmatch(r'(\*\*)?想一想(\*\*)?[：:]?', s):
            qs = []; i += 1
            while i < len(L) and not L[i].startswith('#') and L[i].strip() != '---':
                if L[i].strip(): qs.append(re.sub(r'^(\d+[.、]\s*|- )', '', L[i].strip()))
                i += 1
            out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, q) for k, q in enumerate(qs)] + ['']
            continue
        if s == '---': i += 1; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


AUTHOR = """## 作者介绍

王德生，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人、首席执行官。

生长于中国农村，1990 年进入湘潭大学。后获中国科学院计算数学博士学位，并在中国科学院完成博士后研究，研究方向包括 Voronoi 图、Delaunay 剖分、质心 Voronoi 剖分与有限元方法。曾任教于英国斯旺西大学与新加坡南洋理工大学，2005 年起定居新加坡。

他的思想走过四站：三视角·知识的结构和体系（2015 年 7 月至 2021 年初）；321 智慧系统（2021 年 7 月至 2025 年 7 月）；SIO 本体论（2025 年 7 月至 2026 年 1 月）；SDE 本体论（2026 年 1 月至今）。

在德麦国际出版社出版多部专著，包括「普通人都能懂」系列的各卷哲学家解构与主题卷。

本书是一位计算数学出身的人，写数学被机器先接管的那一天：统一性退成水电，同一性长成谱系。
"""


def tsv_table():
    rows = []
    for f in sorted((S / 'review').glob('*.tsv')):
        for r in csv.reader(f.open(encoding='utf-8'), delimiter='\t'):
            r = [c.strip().replace('|', '／') for c in r]
            if len(r) < 4 or not r[0] or r[0].startswith('章'):
                continue
            rows.append(r[:4])
    def key(r):
        m = re.search(r'\d+', r[0]); return int(m.group()) if m else (-1 if '前' in r[0] or '导' in r[0] or '十分钟' in r[0] else 999)
    rows.sort(key=key)
    head = ['## 附录五　引文核验总表', '',
            '下表登记三审时逐条核过的引文、出处与史实。结论的读法：核＝出处已查对；核：大意＝出处已查对，引文取大意；据研究文献＝依据研究综述或通行说法；待验＝本书推出、尚待验证的判断；已改、已删＝核不实，正文已改或已删。', '',
            '| 章 | 说法或引文 | 出处 | 结论 |', '|---|---|---|---|']
    return '\n'.join(head + ['| %s |' % ' | '.join(r) for r in rows]) + '\n'


def main():
    fr = (S / '01-front.md').read_text()
    lun_i = fr.index('# 导论')
    front, lun = fr[:lun_i], fr[lun_i:]
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、口述母题与承重命题并裁定，Claude 定纲、十路并行执笔、统稿与三审'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 20 万字'), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    notes = ['AI 协作声明：本书的母题、判断与承重命题由王德生（口述）给出；文字在其指令下由 AI（Claude）协作成稿，并经其审定。',
             '书中所引古今中外各家的话，一律转述大意，不作逐字引文，出处以书名、篇名、节号与年份标注。核验结果标在原处：〔核〕为已查对出处，〔核：大意〕为出处已查对、引文取大意，〔据研究文献〕为依据研究综述或通行说法，〔待验〕为本书推出、尚待验证的判断；汇总见附录五「引文核验总表」。',
             '书中程砚、邵禾、谭穗及各章出现的老师、学生、店主等人物与场景均为虚构，只让场景落地，不承担证据。涉及身体与心里的段落只谈理解，不构成医疗或心理建议；难处真的大了，请找医生或心理咨询师。本书的承重命题由王德生于 2026 年 10 月 26 日口述，登记见附录一。',
             '全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录；导论与上、中、下、尾四篇三十六章；结语、附录五件、参考书目、后记。',
             '版权所有　侵权必究']
    front = re.sub(r'^# ', '## ', front, flags=re.M)
    front = ends(front)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + AUTHOR + '\n' + front)
    (HERE / 'front/01-导论.md').write_text(ends(lun))
    (HERE / 'parts').mkdir(exist_ok=True)
    pairs = [('01-上篇', ['02-shang-a.md', '03-shang-b.md']), ('02-中篇', ['04-zhong-a.md', '05-zhong-b.md']),
             ('03-下篇', ['06-xia-a.md', '07-xia-b.md']), ('04-尾篇', ['08-wei-a.md', '09-wei-b.md'])]
    for name, fs in pairs:
        t = '\n\n'.join((S / f).read_text().strip() for f in fs)
        head = t.split('\n', 1)[0]
        assert head.startswith('# ' + name[3:]), head
        (HERE / ('parts/%s.md' % name)).write_text(ends(t))
    bk = (S / '10-back.md').read_text()
    ib, ia, ih = bk.index('\n# 参考书目'), bk.index('\n# 附录'), bk.index('\n# 后记')
    assert ib < ia < ih
    jie, bib, appx, hou = bk[:ib], bk[ib:ia], bk[ia:ih], bk[ih:]
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(ends(jie))
    appx = re.sub(r'\n---\n', '\n', appx).strip() + '\n\n' + tsv_table()
    appx = appx.replace('附录四件', '附录五件')
    (HERE / 'back/12-后置.md').write_text(ends(appx).strip() + '\n\n' + bib.strip() + '\n\n' + hou.strip() + '\n')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%s.md' % n for n, _ in pairs] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'hanzi', len(re.findall(r'[一-鿿]', b)))


if __name__ == '__main__':
    main()
