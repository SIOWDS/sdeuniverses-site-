#!/usr/bin/env python3
"""第 551 号《AI时代的职业教育出路：技术的同一性谱系》：把合成全稿 src/full.md（前言、导读、八编三十六章、结语、附录一至四）
转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

full.md 格式：一级标题 = 前言／导读／第N编／第N章／结语／附录一…附录四（标题与题之间空格或全角空格均可）；
  章内节 = 二级标题 “## N.M 题”；节内小标题 = 三级标题；前言、导读、结语、附录内的 “## 一、…” 也是节。
转换：章题「# 第N章　T」→「## 第N章　T」；节题「## N.M T」→「### ◆ N.M　T」；其余二级标题→「### ◆ T」；三级标题→「#### T」；
「这一章的问题」「带走的话」「小账」的各种写法（加粗位置、冒号位置、小账一／小账二、第一行／第二行、列表、一二三、）统一改写成 build.py 认的引用块；围栏代码块原样保留。
前言、导读放进前置（罗马页码）；结语与附录一至四放进后置，附录在目录里各占一行。
产物：front/00-前置.md、parts/NN.md（八编）、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录或仓库根目录都可）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))

INTRO = {
 '第一编': '第一章先把话说公道：跳舞、打乒乓球那样的正规统一指导，有三份实实在在的功劳，它的出身是传递技术太贵时付出的成本。第二章说技术就是六路径，统一指导是把六路径压成了一条。第三章讲职教为什么被叫作二等：拿“点”的尺去量“路”。第四章看两个极端，一端是一条路，一端是各走各的、没有人签收。',
 '第二编': '这一编从土讲起。技术长在什么土里？第五章讲手上的东西，第六章讲耳朵里的东西，第七章讲眼睛的位置，每一种感觉都含完整的显露、差异序列和纠缠。第八章把土分类，第九章讲机器读不到的那一层：它恰恰最值钱。',
 '第三编': '土讲完了，这一编立谱本身。第十章讲六条路径怎样再按三维的分量具体化；第十一章讲这些位置像一张光谱，怎样报位置；第十二章讲一个人的路径从哪里分叉；第十三章讲几条路径在一个团队里怎样合奏；第十四章讲路径之间怎样互为留底。',
 '第四编': '这一编讲怎样给一个人生成他自己的路径，以及它的记录、折价与认证。第十五章讲选起手、选中心，第十六章讲生成之前先封一份对照，第十七章讲谱系条，第十八章讲转岗时的迁移折扣，第十九章讲认证怎样从认地板走向认谱位。',
 '第五编': 'AI 进来以后，谱会变成什么样？第二十章讲人和 AI 合在一起学一门手艺，路径由谁起手；第二十一章讲模拟买得到次数，买不到后果；第二十二章讲同一个底座生成的东西会长出同一种口音；第二十三章讲回写归谁。',
 '第六编': '六条路径，每条一章，十三个行业。第二十四章讲沉淀型，第二十五章讲倒逼型，第二十六章讲锚定型，第二十七章讲进入型，第二十八章讲原型型，第二十九章讲再创型。每章讲这条路径在日常里长什么样、典型的谱位、几个行业怎样走、哪里是一个字不能改的地板。行业与路径的对应是设想，待行业里的人验证。',
 '第七编': '谱要落到地上。第三十章讲学校，第三十一章讲企业与工位，第三十二章讲行业协会与评价，第三十三章讲政策：底线统一，谱来分工。这一编回答，次等的标签怎样消：换尺子，不靠升格。',
 '第八编': '最后一编对着这本书自己。第三十四章讲谱系化会在哪里变坏，第三十五章讲有余裕的人才有自己的谱，这份不平等怎样处理，第三十六章把十二条会被时间判错的预言摆出来，并写明这本书怎样算错。',
}


ACC_HEAD = re.compile(r'^(\*\*)?小账(\*\*)?[：:]?\s*$')
ACC_ANY = re.compile(r'^([-*]\s*)?\*{0,2}小账')


def clean_acc(l):
    """把各种写法的小账一行整理成“本章得失：……”这样的一条。"""
    l = l.strip()
    l = re.sub(r'^[-*]\s+', '', l)
    l = re.sub(r'^\d+\.\s+', '', l)
    l = re.sub(r'^[一二三]、', '', l)
    m = re.match(r'^\*?小账[一二三]?[\u3000 ]*(?:第[一二]行)?(?:（([^）]*)）)?[：:]\*?\s*(.*)$', l)
    if m:
        l = (m[1] + '：' + m[2]) if m[1] else m[2]
    else:
        m = re.match(r'^第[一二]行（([^）]*)）[：:]\s*(.*)$', l)
        if m:
            l = m[1] + '：' + m[2]
    return l.strip()


def conv_body(lines):
    """正文行转换：标题降级、章末块改引用块。围栏代码块原样保留。"""
    out, i = [], 0
    n = len(lines)

    def next_para(j):
        while j < n and not lines[j].strip():
            j += 1
        k = j
        while k < n and lines[k].strip():
            k += 1
        return lines[j:k], k

    def account(j):
        """从第 j 行起读小账块，返回 (条目, 下一行位置)；没有小账返回 ([], j)。"""
        k = j
        while k < n and not lines[k].strip():
            k += 1
        if k >= n or not (ACC_ANY.match(lines[k].strip()) or ACC_HEAD.match(lines[k].strip())):
            if not (k < n and re.match(r'^([-*]\s*)?(\d+\.\s*)?([一二]、)?(本章得|第一行（本章得失）)', lines[k].strip())):
                return [], j
        items, p = [], k
        while p < n:
            l = lines[p].strip()
            if not l:
                q = p
                while q < n and not lines[q].strip():
                    q += 1
                if q < n and ACC_ANY.match(lines[q].strip()):
                    p = q; continue
                break
            if l == '---' or l.startswith('#'):
                break
            if ACC_HEAD.match(l):
                p += 1; continue
            c = clean_acc(l)
            if c:
                items.append(c)
            p += 1
        return items, p

    def emit_acc(items):
        out.extend(['> **小账**', '>'])
        for k, it in enumerate(items):
            out.append('> ' + it)
            if k < len(items) - 1:
                out.append('>')

    def take(text):
        nonlocal i
        out.extend(['> **带走的话**', '>', '> ' + text.strip(), ''])
        items, i2 = account(i)
        if items:
            emit_acc(items); i = i2
        else:
            pass

    while i < n:
        l = lines[i].rstrip()
        if l.strip().startswith('```'):
            out.append(l); i += 1
            while i < n and not lines[i].strip().startswith('```'):
                out.append(lines[i].rstrip()); i += 1
            if i < n:
                out.append(lines[i].rstrip()); i += 1
            continue
        m = re.match(r'^## (\d+\.\d+) (.+)$', l)
        if m:
            out.append('### ◆ %s\u3000%s' % (m[1], m[2].strip())); i += 1; continue
        # 带走的话：四种写法
        if l in ('## 带走的话', '**带走的话**', '**带走的话：**', '**带走的话**：'):
            para, i = next_para(i + 1)
            take(''.join(x.strip() for x in para)); continue
        m = (re.match(r'^\*\*带走的话\*\*[：:]\s*(.+)$', l) or re.match(r'^\*\*带走的话[：:]\*\*\s*(.+)$', l)
             or re.match(r'^\*\*带走的话[：:](.+?)\*\*$', l))
        if m:
            i += 1; take(m[1]); continue
        # 小账（没有紧跟在带走的话后面时）
        if ACC_HEAD.match(l.strip()) or (ACC_ANY.match(l.strip()) and not out[-1:] == ['']):
            items, i2 = account(i)
            if items:
                emit_acc(items); i = i2; continue
        if re.fullmatch(r'(\*\*这一(章|附录)的问题\*\*[：:]?|## 这一(章|附录)的问题|\*\*这一(章|附录)的问题[：:]\*\*)', l):
            para, i = next_para(i + 1)
            out.append('> **这一章的问题**：' + ''.join(x.strip() for x in para)); continue
        m = (re.match(r'^\*\*这一(?:章|附录)的问题\*\*[：:]\s*(.+)$', l) or re.match(r'^\*\*这一(?:章|附录)的问题[：:]\*\*\s*(.+)$', l)
             or re.match(r'^\*\*这一(?:章|附录)的问题[：:](.+?)\*\*$', l))
        if m:
            out.append('> **这一章的问题**：' + m[1].strip()); i += 1; continue
        if l.startswith('### '):
            out.append('#### ' + l[4:].strip()); i += 1; continue
        if l.startswith('## '):
            out.append('### ◆ ' + l[3:].strip()); i += 1; continue
        out.append(l); i += 1
    while out and out[-1].strip() in ('', '---'):
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def norm_title(t):
    t = t.strip()
    m = re.match(r'^(第[一二三四五六七八九十]+编|第\d+章|前言|导读|结语|附录[一二三四五六七八九十])[\s\u3000]*(.*)$', t)
    return (m[1] + '\u3000' + m[2]).strip('\u3000') if m else t


def main():
    src = (HERE / 'src/full.md').read_text(encoding='utf-8').splitlines()
    tops, cur = [], None
    for l in src:
        if l.startswith('# '):
            cur = [norm_title(l[2:]), []]; tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    one = lambda pre: next(t for t in tops if t[0].startswith(pre))
    qian, dao, jie = one('前言'), one('导读'), one('结语')
    apps = [t for t in tops if re.match(r'^附录[一二三四五六七八九十]', t[0])]
    parts, cp = [], None
    for t in tops:
        if re.match(r'^第.+编', t[0]):
            cp = [t[0], []]; parts.append(cp)
        elif re.match(r'^第\d+章', t[0]):
            cp[1].append(t)
    nums = [int(re.match(r'^第(\d+)章', c[0])[1]) for p in parts for c in p[1]]
    assert len(parts) == 8 and nums == list(range(1, 37)), (len(parts), nums)
    assert len(apps) == 4, [a[0] for a in apps]
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)

    qian_md, dao_md = conv_body(qian[1]), conv_body(dao[1])
    total = body_han_of(qian_md) + body_han_of(dao_md)
    for k, (pt, chs) in enumerate(parts, 1):
        nm, title = pt.split('\u3000', 1)
        assert nm in INTRO, nm
        chunks = ['# %s\u3000%s\n\n%s\n' % (nm, title, INTRO[nm])]
        for ct, body in chs:
            md = conv_body(body)
            total += body_han_of(md)
            chunks.append('## %s\n\n%s' % (ct, md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    jie_md = conv_body(jie[1])
    total += body_han_of(jie_md)
    app_han, app_md = 0, []
    for at, body in apps:
        md = conv_body(body)
        app_han += body_han_of(md)
        app_md.append('## %s\n\n%s' % (at, md))
    total += app_han
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': app_han}), encoding='utf-8')

    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        tpl = tpl.replace(a, b)
    front = tpl.rstrip() + '\n\n## %s\n\n%s\n## %s\n\n%s' % (qian[0], qian_md, dao[0], dao_md)
    (HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
    back = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        back = back.replace(a, b)
    appx = ('# 附录\n\n本书附录四件：' + '；'.join(a[0].replace('\u3000', ' ') for a in apps) + '。附录三、附录四写的是设想中的格式与算法，没有已实现的系统，也没有实测数据。\n\n' + '\n'.join(app_md))
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n%s\n%s' % (jie[0], jie_md, appx, back), encoding='utf-8')

    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 9)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章\u3000', b, re.M)), 'parts', len(parts), 'appendices', len(apps), 'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b))


if __name__ == '__main__':
    main()
