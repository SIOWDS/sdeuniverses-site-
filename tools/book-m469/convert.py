#!/usr/bin/env python3
"""第 469 号《朋友发生学——没有朋友的存在，只有朋友的发生》：把 /home/claude/pengyou 下三审定稿
（00-前置、bianNN-00-xu 编序、bianNN-chMM 三十六章、bianNN-99-zhang 本编总账、99-jieyu 结语、99-fulu 附录、98-shimu 参考书目、98-houji 后记）
转成 220/302 版式工具链（照第 462、520 号）的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = Path(M.SRC)
CN = '零一二三四五六七八九'


def ends(text):
    """章末：**带走的话**／**两行小账**／**想一想** → 220 版式的三个引用框。"""
    L = text.split('\n'); out = []; i = 0

    def skip_blank():
        nonlocal i
        while i < len(L) and not L[i].strip():
            i += 1

    def clean(s):
        s = s.strip().lstrip('>').strip()
        s = re.sub(r'^(- |\d+[.、]\s*|[一二三][、.]\s*)', '', s).strip()
        return s

    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^\*\*带走的话\*\*\s*[：:]?\s*(.*)$', s) or re.match(r'^\*\*带走的话[：:]\s*\*\*\s*(.*)$', s)
        if m:
            i += 1; x = m[1].strip()
            if not x:
                skip_blank(); x = []
                while i < len(L) and L[i].strip() and not L[i].strip().startswith('**'):
                    x.append(clean(L[i])); i += 1
                x = ''.join(x)
            x = re.sub(r'^\*\*(.*)\*\*$', r'\1', x).strip('*')
            out += ['> **带走的话**', '> ' + x, '']
            continue
        m = re.match(r'^\*\*(?:两行)?小账\*\*\s*[：:]?\s*(.*)$', s)
        if m:
            i += 1; q = [m[1].strip()] if m[1].strip() else []
            skip_blank()
            while i < len(L) and L[i].strip() and not L[i].strip().startswith(('**', '#')):
                c = clean(L[i])
                if c: q.append(c)
                i += 1
            out += ['> **小账**'] + ['> ' + c for c in q] + ['']
            continue
        m = re.match(r'^\*\*想一想\*\*\s*[：:]?\s*(.*)$', s)
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


def rd(name):
    return (S / name).read_text().strip()


def chap(path):
    t = Path(path).read_text()
    t = re.sub(r'^## 第 ?(\d+) ?章　', lambda m: '## 第%s章　' % m[1], t, count=1, flags=re.M)
    return ends(t)


def zhang(path):
    t = Path(path).read_text().strip()
    t = re.sub(r'^## 本编总账\s*$', '## 本编总账　看见与收回', t, count=1, flags=re.M)
    assert t.startswith('## 本编总账'), path
    head, _, body = t.partition('\n')
    body = re.sub(r'^#{1,2} ', '### ', body, flags=re.M)
    return head + '\n' + body + '\n'


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、口述承重命题与裁定，Claude 执笔与统稿（十路并行执笔，三审）'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 25 万字'), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    cp += ['', 'AI 协作声明：本书的判断、口径与承重命题由王德生（口述）给出；文字在其指令下由 AI（Claude）协作成稿，并经其审定。', '',
           '书中所引古今中外各家的话，一律转述大意；凡带引号处，请读作「大意如此」。圣经引文据和合本。出处的核验结果标在原处：〔核〕为已查对，〔核：大意〕为出处已查对、引文取大意，〔待核〕为尚待查对，〔待验〕为本书推出、尚待验证的说法；汇总见附录三「引文核验总表」。', '',
           '书中陪读人物宋牧、杜衡、杜小苇及其亲友、同事、同学均为虚构，只承担画面，不承担证据。本书的十条承重命题由王德生于 2026 年 10 月 26 日口述，登记见附录四。', '',
           '全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录、导论；九编三十六章，每编末附本编总账；结语、附录六件、参考书目、后记。', '',
           '版权所有　侵权必究', '']
    au = ['## 作者介绍', '',
          '王德生，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人、首席执行官。', '',
          '生长于中国农村，1990 年进入湘潭大学。后获中国科学院计算数学博士学位，并在中国科学院完成博士后研究，研究方向包括 Voronoi 图、Delaunay 剖分、质心 Voronoi 剖分与有限元方法。曾任教于英国斯旺西大学与新加坡南洋理工大学，2005 年起定居新加坡。', '',
          '他的思想走过四站：三视角·知识的结构和体系（2015 年 7 月至 2021 年初）；321 智慧系统（2021 年 7 月至 2025 年 7 月）；SIO 本体论（2025 年 7 月至 2026 年 1 月）；SDE 本体论（2026 年 1 月至今）。', '',
          '在德麦国际出版社出版多部专著，包括「普通人都能明白」系列的各卷哲学家解构与主题卷。', '',
          '本书是这一系列里写「朋友」的一卷，与第 462 号《傲慢发生学》互为姊妹卷：那一卷写单向的回写，这一卷写双向的回写。', '']

    def h1to2(t):
        return re.sub(r'^# ', '## ', t, count=1, flags=re.M)
    ten = rd('00-shifenzhong.md') if (S / '00-shifenzhong.md').exists() else ''
    front = '\n'.join(cp + au) + '\n' + (ten + '\n\n' if ten else '') + h1to2(rd('00-qianyan.md')) + '\n\n' + h1to2(rd('00-daodu.md')) + '\n'
    (HERE / 'front/00-前置.md').write_text(front)
    (HERE / 'front/01-导论.md').write_text(rd('00-daolun.md') + '\n')
    pfiles = []
    for p in range(1, 10):
        head = rd('bian%02d-00-xu.md' % p)
        assert head.startswith('# 第%s编　' % CN[p]), head[:30]
        chs = sorted(S.glob('bian%02d-ch*.md' % p))
        assert len(chs) == 4, chs
        body = '\n\n'.join(chap(c).strip() for c in chs)
        z = zhang(S / ('bian%02d-99-zhang.md' % p))
        f = 'parts/%02d-第%s编.md' % (p, CN[p]); pfiles.append(f)
        (HERE / f).write_text(head + '\n\n' + body + '\n\n' + z)
    (HERE / 'back/11-结语.md').write_text(ends(rd('99-jieyu.md')))
    fu = rd('99-fulu.md')
    fu = re.sub(r'^## ', '### ', fu, flags=re.M)
    fu = re.sub(r'^# (附录[一二三四五六七八九十])', r'## \1', fu, flags=re.M)
    back = fu + '\n\n' + rd('98-shimu.md') + '\n\n' + rd('98-houji.md') + '\n'
    (HERE / 'back/12-后置.md').write_text(back)
    files = ['front/00-前置.md', 'front/01-导论.md'] + pfiles + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n\n'.join((HERE / f).read_text().strip() for f in files) + '\n')
    bk = (HERE / 'book.md').read_text()
    print('ok', len(re.findall(r'[一-鿿]', bk)), 'chapters', len(re.findall(r'^## 第\d+章　', bk, re.M)))


if __name__ == '__main__':
    main()
