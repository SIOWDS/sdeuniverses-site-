#!/usr/bin/env python3
"""第 443 号《惯》：把统稿（scratchpad/guan 下的 ch00_front、ch02–ch10、ch11_end、app1、app2_after、app3）
转成 220/302 版式工具链（照第 520 号）的分卷稿。只做格式转换与章号改排，不动正文判断。
章号改排：原第一章（总论）→ 导论；原第二至十章 → 第 1–9 章；原第十一章（终章）→ 结语。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = Path(M.SRC)
CNUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '十一': 11}
PROTECT = ['《心理学原理》第四章', '第 236 号第三章']


def renumber(t):
    for k, p in enumerate(PROTECT):
        t = t.replace(p, '\x00%d\x00' % k)
    t = t.replace('第一章总论', '导论').replace('第一章　总论', '导论')
    rng = {'第二至四章': '第 1–3 章', '第五至七章': '第 4–6 章', '第八至十章': '第 7–9 章'}
    for a, b in rng.items():
        t = t.replace(a, b)

    def f(m):
        n = CNUM[m.group(1)]
        if n == 1: return '导论'
        if n == 11: return '结语'
        return '第 %d 章' % (n - 1)
    t = re.sub(r'第(十一|[一二三四五六七八九十])章', f, t)
    for k, p in enumerate(PROTECT):
        t = t.replace('\x00%d\x00' % k, p)
    return t


def strip_mark(x):
    x = x.strip()
    x = re.sub(r'^(- |\d+[.、]\s*|[一二三四五六七八九十]+[，、,]\s*)', '', x)
    x = re.sub(r'^\*\*(.*)\*\*$', r'\1', x)
    return x.strip()


def endboxes(body):
    """章内：「带走的话」节 → 带走的话框（＋小账框）；「想一想」节或行 → 想一想框。"""
    L = body.split('\n')
    out, i = [], 0
    while i < len(L):
        s = L[i].strip()
        if re.match(r'^#{2,3} ◆?\s*([0-9.一二三四五六七八九十、]+\s*|[\d.]+　)?带走的话\s*$', s):
            i += 1
            take, ledger, wonder, mode = [], [], [], 'take'
            while i < len(L) and not re.match(r'^#{1,3} ', L[i].strip()):
                x = L[i].strip(); i += 1
                if not x or x == '---': continue
                if re.match(r'^\*\*(两行)?小账\*\*$', x): mode = 'ledger'; continue
                if re.match(r'^\*\*想一想\*\*$', x): mode = 'wonder'; continue
                {'take': take, 'ledger': ledger, 'wonder': wonder}[mode].append(strip_mark(x))
            out += ['> **带走的话**'] + ['> ' + x for x in take] + ['']
            if ledger: out += ['> **小账**'] + ['> ' + x for x in ledger] + ['']
            if wonder: out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, q) for k, q in enumerate(wonder)] + ['']
            continue
        if re.match(r'^#{2,3} ◆?\s*([0-9.一二三四五六七八九十、]+\s*|[\d.]+　)?想一想\s*$', s):
            i += 1; qs = []
            while i < len(L) and not re.match(r'^#{1,3} ', L[i].strip()):
                x = L[i].strip(); i += 1
                if x and x != '---': qs.append(strip_mark(x))
            out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, q) for k, q in enumerate(qs)] + ['']
            continue
        out.append(L[i]); i += 1
    return '\n'.join(out)


def chapter(path, newno):
    t = Path(path).read_text().strip()
    head, _, body = t.partition('\n')
    m = re.match(r'^# 第[一二三四五六七八九十]+章　(.*)$', head)
    assert m, head
    body = re.sub(r'^### (.*)$', r'**\1**', body, flags=re.M)
    k = int(re.search(r'ch(\d+)', str(path)).group(1))
    body = re.sub(r'(?<![\d.])%d\.(\d{1,2})(?!\d)' % k, lambda m: '%d.%s' % (newno, m.group(1)), body)
    body = re.sub(r'^## (?!◆)(.*)$', r'## ◆ \1', body, flags=re.M)
    body = endboxes(body)
    body = re.sub(r'^## ◆', '### ◆', body, flags=re.M)
    body = '\n'.join(x for x in body.split('\n') if x.strip() != '---')
    return '## 第%d章　%s\n\n%s' % (newno, renumber(m.group(1)), renumber(body).strip())


def tidy(t):
    return re.sub(r'\n{3,}', '\n\n', t).strip() + '\n'


def main():
    fr = (S / 'ch00_front.md').read_text()
    pre_i, lun_i = fr.index('# 前言'), fr.index('# 第一章')
    preface, lun = fr[pre_i:lun_i], fr[lun_i:]
    # 出版信息
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、定音（三个旧）与审定；九位 AI 执笔人各领一问并行解构，Claude 统稿'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 20 万字'), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    notes = ['AI 协作声明：本书的方法底盘（SDE：显露·差异序列·特征纠缠；三方程、六路径、三原理）归属王德生。成书取《九问成书：新增二十套专著问对（全球拓敌版）》第五十二套《惯》的九问，由九位 AI 执笔人各领一问、从「SDE 本体论、SDE 方法论、SDE 专著系列」三路阅读并行解构，各写一章，再由 Claude 统稿；全书定音「惯，是旧方程、旧路径、旧原理，替新发生做了主」由王德生于 2026 年 10 月 26 日口述，判断与最终文本经其审定。',
             '书中周伯、小雯、周敏与乐乐、邱姨、苏爱珍、孟启、小乔、老顾等陪读人物与情节，均为作者构想，凡标明「这是我构想的场景」者，不指向任何真人真事。书中九个判别局面是可检验的设计，并未实际施行；所有读数只用于检验本书的说法，不用于考核任何人。本书不作医学或心理诊断；成瘾、强迫一类的难处大了，请找医生或心理咨询师。标〔待核〕处为仍在逐条复核的引文、年份与出处。',
             '全书结构：出版信息、作者介绍、前言；导论；第一编（What·旧方程）、第二编（How·旧路径）、第三编（Why·旧原理）共九章；结语；附录三件；后记。',
             '版权所有　侵权必究']
    author = (HERE.parent / 'book-m520/front/00-前置.md').read_text()
    author = author[author.index('## 作者介绍'):author.index('## 十分钟读完这本书')]
    author = author.replace('本书是这一系列里写「欠」的一卷：一个人人天天在用、却很少有人停下来看一眼的字。',
                            '本书是这一系列里写「惯」的一卷：一个人人天天在用，却很少被当成正题的字。')
    assert '写「惯」的一卷' in author
    pre = renumber(preface)
    pre = re.sub(r'^# 前言', '## 前言', pre, flags=re.M)
    pre = re.sub(r'^◆ (.*)$', r'### ◆ \1', pre, flags=re.M)
    pre = '\n'.join(x for x in pre.split('\n') if x.strip() != '---')
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text(tidy('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + author + '\n' + pre))
    # 导论
    head, _, body = lun.partition('\n')
    lb = endboxes(re.sub(r'^## ◆', '### ◆', body, flags=re.M).replace('### ◆ 十　带走的话', '### ◆ 带走的话'))
    lb = re.sub(r'^## ◆', '### ◆', endboxes(body), flags=re.M)
    lb = '\n'.join(x for x in lb.split('\n') if x.strip() != '---')
    (HERE / 'front/01-导论.md').write_text(tidy('# 导论　三个旧，替新发生做了主\n\n' + renumber(lb)))
    # 三编
    intros = {1: ('第一编　What：惯是什么——旧方程', 2), 2: ('第二编　How：惯怎样发生——旧路径', 5), 3: ('第三编　Why：惯为什么被推出来——旧原理', 8)}
    full = (S / '惯-全稿.md').read_text()
    pin = {}
    for name in ['上编　What：惯是什么——旧方程', '中编　How：惯怎样发生——旧路径', '下编　Why：惯为什么被推出来——旧原理']:
        k = full.index('# ' + name)
        seg = full[k:].split('\n', 1)[1]
        seg = seg[:seg.index('\n---')]
        pin[name[:2]] = renumber(seg.strip())
    (HERE / 'parts').mkdir(exist_ok=True)
    for k, (title, first) in intros.items():
        intro = pin['上编中编下编'[2 * (k - 1):2 * k]]
        intro = intro.replace('上编三章', '这一编三章').replace('中编三章', '这一编三章').replace('下编三章', '这一编三章')
        chs = [chapter(S / ('ch%02d.md' % n), n - 1) for n in range(first, first + 3)]
        (HERE / ('parts/0%d-第%s编.md' % (k, '一二三'[k - 1]))).write_text(tidy('# %s\n\n%s\n\n%s' % (title, intro, '\n\n'.join(chs))))
    # 结语
    end = (S / 'ch11_end.md').read_text()
    head, _, body = end.partition('\n')
    body = re.sub(r'^## ◆', '### ◆', endboxes(body), flags=re.M)
    body = '\n'.join(x for x in body.split('\n') if x.strip() != '---')
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(tidy('# 结语　留口——把惯放回发生里\n\n' + renumber(body)))
    # 后置
    a1 = (S / 'app1.md').read_text(); a2, after = (S / 'app2_after.md').read_text().split('# 后记')
    a3 = (S / 'app3.md').read_text()
    hou = full[full.index('# 后记'):]
    appx = '# 附录\n\n本书附录三件：九问原题与九章判断一览、九个判别局面与证伪条件汇总、本书引及的德麦国际专著。\n\n'
    for x in (a1, a2, a3):
        x = re.sub(r'^# (附录.)　', r'## \1　', x.strip(), flags=re.M)
        x = '\n'.join(y for y in x.split('\n') if y.strip() != '---')
        appx += renumber(x) + '\n\n'
    (HERE / 'back/12-后置.md').write_text(tidy(appx + renumber(hou)))
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, '一二三'[k - 1]) for k in (1, 2, 3)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', len(re.findall(r'[一-鿿]', b)))
    left = re.findall(r'.{8}第(?:十一|[一二三四五六七八九十])章.{4}', b)
    print('chinese-numeral chapter refs left:', left)


if __name__ == '__main__':
    main()
