#!/usr/bin/env python3
"""第 467 号《忍》：把 /home/claude/ren-book/chapters 下的统稿（front/ch01–09/back）
转成 220/302 版式工具链（照第 520 号）的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = Path(M.SRC)
CN = '零一二三四五六七八九十'
PARTS = {1: ('第一编　忍是什么', [1, 2, 3], '这一编三章，各问一个「是什么」。第一章说忍有两半：覆盖与承受。第二章把忍分成九种，看九个出口。第三章把忍和让、熬、憋、等、累放在一排，看它们各自走到了哪一步。'),
         2: ('第二编　忍怎样发生', [4, 5, 6], '这一编三章，看一次忍怎样走完它的一生。第四章看那个更重要的意义怎样盖下来，第五章看它退出主导以后忍怎样到期，第六章看悬着的忍怎样或爆或蚀。'),
         3: ('第三编　为什么会有忍', [7, 8, 9], '这一编三章，问忍为什么非如此不可。第七章说意义有轻重才有忍，第八章说忍与创造、自由、幸福的关系，第九章给出怎样忍得成的三问。')}


def ends(text):
    """章末：**带走的话** / **想一想** / **两行小账** → 引用框。"""
    L = text.split('\n'); out = []; i = 0

    def grab(i):
        q = []
        while i < len(L) and not L[i].startswith('#') and not re.match(r'^\*\*(带走的话|想一想|两行小账|小账)\*\*', L[i].strip()):
            s = L[i].strip()
            if s and s != '---':
                s = re.sub(r'^(- |\* |> )', '', s)
                q.append(s)
            i += 1
        return q, i
    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^\*\*(带走的话|想一想|两行小账|小账)\*\*[：:]?\s*(.*)$', s)
        if m:
            kind = '小账' if m[1] in ('两行小账', '小账') else m[1]
            q, i = grab(i + 1)
            if m[2].strip(): q.insert(0, m[2].strip())
            if kind == '带走的话':
                q = [re.sub(r'^\*\*(.*)\*\*$', r'\1', x) for x in q]
                out += ['> **带走的话**'] + ['> ' + x for x in q] + ['']
            elif kind == '想一想':
                q = [re.sub(r'^([一二三四五六七八九十]+[，、.]|\d+[.、)]\s*)', '', x).strip() for x in q]
                out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, x) for k, x in enumerate(q)] + ['']
            else:
                out += ['> **小账**'] + ['> ' + x for x in q] + ['']
            continue
        if s == '---': i += 1; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def chapter(k):
    t = (S / ('ch0%d.md' % k)).read_text()
    t = t.replace('“', '「').replace('”', '」')
    head, rest = t.split('\n', 1)
    m = re.match(r'^# 第(.)章　(.*)$', head.strip())
    assert m and CN.index(m[1]) == k, head
    rest = re.sub(r'^### ', '#### ', rest, flags=re.M)
    rest = re.sub(r'^## ', '### ', rest, flags=re.M)
    return '## 第%d章　%s\n\n' % (k, m[2]) + ends(rest)


def main():
    fr = (S / 'front.md').read_text()
    li = fr.index('# 导论')
    front, lun = fr[:li], fr[li:]
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、口述承重命题与裁定，Claude 解构、执笔与统稿（十个写作智能体并行执笔）'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 20 万字'), ('版次', M.EDITION)]:
        cp.append('| %s | %s |' % (a, b))
    notes = ['AI 协作声明：本书的母题、口径与十一句承重命题由王德生口述给出；文字在其指令下由 AI（Claude）解构、协作成稿与统稿，并经其审定。',
             '书中所引古今中外各家的话，一律转述大意，不作逐字引文；中国古典短句照引原文。年份、书名、章节尚未查对的，标〔待核〕；本书推出、尚待验证的局面，标〔待验〕。',
             '书中林晓一家及各章日常人物、场景均为虚构。写到身体的地方讲理解与相处，不构成医学建议；难处真的大了，请找医生或心理咨询师。国共合作一事只述史实与结构，不评价任何一方。本书的承重命题由王德生于 2026 年 10 月 26 日口述，登记见附录一。',
             '全书结构：出版信息、作者介绍、前言、导读、目录；导论与三编九章；结语、附录五件、后记。',
             '版权所有　侵权必究']
    author = (Path(M.TPL) / 'front/00-前置.md').read_text()
    a0 = author.index('## 作者介绍'); a1 = author.index('\n## ', a0 + 5)
    author = author[a0:a1].strip() + '\n'
    front = re.sub(r'^## ', '### ', front, flags=re.M)
    front = re.sub(r'^# ', '## ', front, flags=re.M)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + author + '\n' + ends(front))
    lun = re.sub(r'^## ', '### ', lun, flags=re.M)
    (HERE / 'front/01-导论.md').write_text(ends(lun.replace('“', '「').replace('”', '」')))
    (HERE / 'parts').mkdir(exist_ok=True)
    for p, (title, chs, intro) in PARTS.items():
        body = '# %s\n\n%s\n\n' % (title, intro) + '\n'.join(chapter(k) for k in chs)
        (HERE / ('parts/0%d-第%s编.md' % (p, CN[p]))).write_text(body)
    bk = (S / 'back.md').read_text()
    ai = bk.index('# 附录')
    jy, rest = bk[:ai], bk[ai:]
    jy = re.sub(r'^## ', '### ', jy, flags=re.M)
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(ends(jy))
    (HERE / 'back/12-后置.md').write_text(rest.strip() + '\n')
    for f in list((HERE / 'front').glob('*.md')) + list((HERE / 'parts').glob('*.md')) + list((HERE / 'back').glob('*.md')):
        s = f.read_text()
        for a, b in (('上编', '第一编'), ('中编', '第二编'), ('下编', '第三编')):
            s = s.replace(a, b)
        f.write_text(s)
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CN[k]) for k in (1, 2, 3)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', len(re.findall(r'[一-鿿]', b)))


if __name__ == '__main__':
    main()
