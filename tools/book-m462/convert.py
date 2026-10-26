#!/usr/bin/env python3
"""第 462 号《傲慢发生学——碰撞之前的结算》：把 /home/claude/aoman 下的定稿（chapters/ 前言、编首、三十章、结语；extra/ 十分钟、导读、附录、书目、后记）
转成 220/302 版式工具链（照第 520 号）的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = Path(M.SRC)
X = S.parent / 'extra'
CN = '零一二三四五六七八九'
PART_CH = {1: range(1, 7), 2: range(7, 13), 3: range(13, 17), 4: range(17, 22), 5: range(22, 27), 6: range(27, 31)}


def ends(text):
    """章末：**带走的话**／**小账**／**想一想** → 220 版式的三个引用框。"""
    L = text.split('\n'); out = []; i = 0

    def skip_blank():
        nonlocal i
        while i < len(L) and not L[i].strip():
            i += 1

    def clean(s):
        s = s.strip().lstrip('>').strip()
        s = re.sub(r'^(- |\d+[.、]\s*)', '', s).strip()
        s = re.sub(r'^第[一二]行[：:]\s*', '', s)
        return s

    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^\*\*带走的话\*\*[：:]?\s*(.*)$', s)
        if m:
            i += 1; x = m[1].strip()
            if not x:
                skip_blank(); x = []
                while i < len(L) and L[i].strip() and not L[i].strip().startswith('**'):
                    x.append(clean(L[i])); i += 1
                x = ''.join(x)
            x = re.sub(r'^\*\*(.*)\*\*$', r'\1', x)
            out += ['> **带走的话**', '> ' + x, '']
            continue
        m = re.match(r'^\*\*小账\*\*[：:]?\s*(.*)$', s)
        if m:
            i += 1; q = [m[1].strip()] if m[1].strip() else []
            skip_blank()
            while i < len(L) and L[i].strip() and not L[i].strip().startswith(('**', '#')):
                c = clean(L[i])
                if c: q.append(c)
                i += 1
            out += ['> **小账**'] + ['> ' + c for c in q] + ['']
            continue
        m = re.match(r'^\*\*想一想\*\*[：:]?\s*(.*)$', s)
        if m:
            i += 1; q = [m[1].strip()] if m[1].strip() else []
            skip_blank()
            while i < len(L) and not L[i].startswith('#') and L[i].strip() != '---':
                st = L[i].strip()
                if st.startswith('**') and not st.startswith('**想'):
                    break
                if st: q.append(clean(st))
                i += 1
            out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, x) for k, x in enumerate(q)] + ['']
            continue
        if s == '---':
            i += 1; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def chap(n):
    t = (S / ('ch%02d.md' % n)).read_text()
    t = re.sub(r'^## 第 ?(\d+) ?章　', lambda m: '## 第%s章　' % m[1], t, count=1, flags=re.M)
    return ends(t)


def main():
    (HERE / 'front').mkdir(exist_ok=True); (HERE / 'parts').mkdir(exist_ok=True); (HERE / 'back').mkdir(exist_ok=True)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、口述承重命题与裁定，Claude 执笔与统稿（十五路并行执笔）'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 25 万字'), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    cp += ['', 'AI 协作声明：本书的判断、口径与承重命题由王德生（口述）给出；文字在其指令下由 AI（Claude）协作成稿，并经其审定。', '',
           '书中所引古今中外各家的话，一律转述大意，不作逐字引文，出处以书名、篇名与年份标注。出处的核验结果标在原处：〔核〕为已查对出处，〔核：大意〕为出处已查对、引文取大意，〔待核〕为尚待查对，〔待验〕为本书推出、尚待验证的局面；汇总见附录三「引文核验总表」。', '',
           '书中陪读人物林国栋、林晓、周恺、豆豆、林家奶奶及各章日常场景、配角均为虚构，不承担证据。关于身体的章节讲理解、习惯与相处，不构成医学建议；身体或心里的难处真的大了，请找医生或心理咨询师。本书的承重命题由王德生于 2026 年 10 月 26 日口述，登记见附录一。', '',
           '全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录；六编三十章；结语、附录五件、参考书目、后记。', '',
           '版权所有　侵权必究', '']
    au = ['## 作者介绍', '',
          '王德生，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人、首席执行官。', '',
          '生长于中国农村，1990 年进入湘潭大学。后获中国科学院计算数学博士学位，并在中国科学院完成博士后研究，研究方向包括 Voronoi 图、Delaunay 剖分、质心 Voronoi 剖分与有限元方法。曾任教于英国斯旺西大学与新加坡南洋理工大学，2005 年起定居新加坡。', '',
          '他的思想走过四站：三视角·知识的结构和体系（2015 年 7 月至 2021 年初）；321 智慧系统（2021 年 7 月至 2025 年 7 月）；SIO 本体论（2025 年 7 月至 2026 年 1 月）；SDE 本体论（2026 年 1 月至今）。', '',
          '在德麦国际出版社出版多部专著，包括「普通人都能懂」系列的各卷哲学家解构与主题卷。', '',
          '本书是这一系列里写「傲慢」的一卷：一个人人都会拿来说别人、却很少有人拿来问自己的词。', '']
    pre = (S / '00-preface.md').read_text()
    pre = re.sub(r'^# 前言', '## 前言', pre, count=1, flags=re.M)
    front = '\n'.join(cp + au) + '\n' + (X / 'ten-min.md').read_text().strip() + '\n\n' + pre.strip() + '\n\n' + (X / 'daodu.md').read_text().strip() + '\n'
    (HERE / 'front/00-前置.md').write_text(front)
    for p, rng in PART_CH.items():
        head = (S / ('part-%d.md' % p)).read_text().strip()
        body = '\n\n'.join(chap(n).strip() for n in rng)
        (HERE / ('parts/%02d-第%s编.md' % (p, CN[p]))).write_text(head + '\n\n' + body + '\n')
    (HERE / 'back/11-结语.md').write_text((S / '99-conclusion.md').read_text().strip() + '\n')
    back = (X / 'appendix.md').read_text().strip() + '\n\n' + (X / 'biblio.md').read_text().strip() + '\n\n' + (X / 'houji.md').read_text().strip() + '\n'
    (HERE / 'back/12-后置.md').write_text(back)
    files = ['front/00-前置.md'] + ['parts/%02d-第%s编.md' % (p, CN[p]) for p in PART_CH] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n\n'.join((HERE / f).read_text().strip() for f in files) + '\n')
    print('ok', len(re.findall(r'[一-鿿]', (HERE / 'book.md').read_text())))


if __name__ == '__main__':
    main()
