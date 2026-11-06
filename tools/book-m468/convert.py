#!/usr/bin/env python3
"""第 468 号《一看就不读》：把合成全稿 src/full.md（前言、导读、八编三十六章、结语、附录一至四）
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
 '上编': '第一个条件：人与 AI 之间，意义三律有没有转起来。第一章分开串联与纠缠，拿掉任何一方都拆不回去，才算纠缠；第二章讲特征律，目标在碰撞里长出来；第三章讲自由律，不在 AI 给的五十个选项里挑，而是在约束里裁出一条原本没有的路；第四章讲幸福律与分寸，一整轮走通，先松后紧。',
 '中编': '第二个条件：复合体生成的东西，有没有真、善、美的显露。第五章从刀切菜讲起，美是发生的诊断，三大感觉的 SDE 也在这一章讲；第六章讲真是内能、善是动能；第七章讲先显露给复合体自己，靠创新智商评估与三审做内部验收；第八章讲再显露给读者，读者读出"一个人"，是主体那一路最后亮了。',
 '下编': '第三个条件：复合体和读者的特征纠缠，有没有因为信息的增加而丰富。第九章讲美而无新，被重复确认不是学到；第十章讲双向增量，只对一方增加都不算；第十一章讲四种落地：新专著、新思想、新方法、新结构。',
 '终编': '三个条件合起来是 S3·D1·E2，正是"读人"的定义。第十二章把九格判据图逐格摆出，连同至今没有发生的那一格；第十三章讲署名与承担：想法可以说不清是谁的，责任必须有人签字。',
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


def body_chars_of(md):
    """正文字数（含标点）：汉字＋中文标点＋西文词（一个词算一字）；去 Markdown 符号与网址。"""
    t = re.sub(r'\]\([^)]*\)', '', md); t = re.sub(r'https?://\S+', '', t); t = re.sub(r'[#*>|`]', '', t)
    return (len(re.findall(r'[\u4e00-\u9fff]', t)) + len(re.findall(r'[\u3000-\u303f\uff00-\uffef“”‘’—…·]', t))
            + len(re.findall(r'[A-Za-z0-9]+', t)))


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def norm_title(t):
    t = t.strip()
    m = re.match(r'^(第[一二三四五六七八九十]+编|上编|中编|下编|终编|第\d+章|前言|序章|结语|附录[一二三四五六七八九十])[\s\u3000]*(.*)$', t)
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
    qian, dao, jie = one('前言'), one('序章'), one('结语')
    apps = [t for t in tops if re.match(r'^附录[一二三四五六七八九十]', t[0])]
    parts, cp = [], None
    for t in tops:
        if re.match(r'^(第.+编|上编|中编|下编|终编)', t[0]):
            cp = [t[0], []]; parts.append(cp)
        elif re.match(r'^第\d+章', t[0]):
            cp[1].append(t)
    nums = [int(re.match(r'^第(\d+)章', c[0])[1]) for p in parts for c in p[1]]
    assert len(parts) == 4 and nums == list(range(1, 14)), (len(parts), nums)
    assert len(apps) == 3, [a[0] for a in apps]
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)

    qian_md, dao_md = conv_body(qian[1]), conv_body(dao[1])
    total = body_han_of(qian_md) + body_han_of(dao_md)
    chars = body_chars_of(qian_md) + body_chars_of(dao_md)
    for k, (pt, chs) in enumerate(parts, 1):
        nm, title = pt.split('\u3000', 1)
        assert nm in INTRO, nm
        chunks = ['# %s\u3000%s\n\n%s\n' % (nm, title, INTRO[nm])]
        for ct, body in chs:
            md = conv_body(body)
            total += body_han_of(md)
            chars += body_chars_of(md)
            chunks.append('## %s\n\n%s' % (ct, md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    jie_md = conv_body(jie[1])
    total += body_han_of(jie_md)
    chars += body_chars_of(jie_md)
    app_han, app_md = 0, []
    for at, body in apps:
        md = conv_body(body)
        app_han += body_han_of(md)
        chars += body_chars_of(md)
        app_md.append('## %s\n\n%s' % (at, md))
    total += app_han
    wan = chars / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': app_han, 'chars': chars}), encoding='utf-8')

    rep = {'{HAN}': format(total, ','), '{WAN}': '%.0f' % wan, '{CHARS}': format(chars, ',')}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        tpl = tpl.replace(a, b)
    front = tpl.rstrip() + '\n\n## %s\n\n%s\n## %s\n\n%s' % (qian[0], qian_md, dao[0], dao_md)
    (HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
    back = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        back = back.replace(a, b)
    appx = ('# 附录\n\n本书附录三件：' + '；'.join(a[0].replace('\u3000', ' ') for a in apps) + '。附录二的自检表供读者与复合体自用，不是认证标准。\n\n' + '\n'.join(app_md))
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n%s\n%s' % (jie[0], jie_md, appx, back), encoding='utf-8')

    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 5)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章\u3000', b, re.M)), 'parts', len(parts), 'appendices', len(apps), 'body_han', total, '(appendix %d)' % app_han, 'chars', chars, 'all_han', han(b))


if __name__ == '__main__':
    main()
