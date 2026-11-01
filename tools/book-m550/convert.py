#!/usr/bin/env python3
"""第 550 号《听话论：真理的符合论》：把统稿 src/full.md（前言、六编十八章、结语、附录 A–E）
转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

章题「# 第N章　T」→「## 第N章　T」；节题「## N.M T」→「### ◆ N.M　T」；序的「## 0.M T」→「### ◆ 序M　T」；
三级标题→「#### T」；「这一章的问题」「带走的话」「两行小账」改写成 build.py 认的引用块。
产物：front/00-前置.md、front/01-导言.md、parts/NN.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录或仓库根目录都可）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))

INTRO = {
 '第一编': '第一章把符合论摆出来：它为什么在日常里看起来天经地义，它的家谱怎么传下来。第二章问它承诺了什么，再把它们逐条摆出来比较。第三章看反映论的视觉隐喻：镜子里没有碰，只有看，这个比喻把“触”和“做”都藏起来了。',
 '第二编': '符合论说“命题与事实相符”，可相符怎么做、谁来判，却说不出来。第四章借191号的成位，说物是一次成位的结果；第五章看康德那一柱和三处分手；第六章把八步论证摆出来，并写明它的强度；第七章看“实践检验”里其实藏着一次往返。',
 '第三编': '这一编讲本书自己的提法。第八章提出第五个候选：真的标准是被指定的；第九章讲命令，它是对差异序列和特征纠缠系统的统一性限定；第十章讲显露怎样回写、怎样沉进特征纠缠系统，成为很难改的统一；第十一章讲样板发生，和照着做时出现的符合感。',
 '第四编': '“发现”这个词，一边说真理在那里等着，一边把命令藏了起来。第十二章拆开“发现”的三件事；第十三章看科学里的固定流程：它为什么能让预期的显露高概率发生，仅此而已。',
 '第五编': '前人早有人看见了命令和知识的关系。第十四章读福柯：写已经说了的，也写还多出来的；第十五章读库恩、科学知识社会学、实用主义与反映论，看各家命名了什么真实的发生，又锁在哪一维。',
 '第六编': '真是发生的再来稳定性。第十六章讲知识的再发生；第十八章把九格逐格扫一遍，看母题在哪里发生，哪几格至今没有发生；第十八章回到一个最日常的问题：教，是怎样带人走到再来的。',
}


def conv_body(lines):
    """正文行转换：标题降级、章末块改引用块。"""
    out, i = [], 0
    n = len(lines)

    def next_para(j):
        # 跳过空行，取下一段（到空行为止）
        while j < n and not lines[j].strip():
            j += 1
        k = j
        while k < n and lines[k].strip():
            k += 1
        return lines[j:k], k

    while i < n:
        l = lines[i].rstrip()
        m = re.match(r'^## 0\.(\d+) (.+)$', l)
        if m:
            out.append('### ◆ 序%s　%s' % (m[1], m[2].strip())); i += 1; continue
        m = re.match(r'^## (\d+\.\d+) (.+)$', l)
        if m:
            out.append('### ◆ %s　%s' % (m[1], m[2].strip())); i += 1; continue
        if l == '## 带走的话' or l == '**带走的话**':
            para, i = next_para(i + 1)
            out += ['> **带走的话**', '>'] + ['> ' + x.strip() for x in para]
            continue
        m = re.match(r'^\*\*带走的话\*\*[：:](.+)$', l)
        if m:
            out += ['> **带走的话**', '>', '> ' + m[1].strip()]; i += 1; continue
        if re.match(r'^\*\*小账[一二]?\*\*', l) or l.strip() == '**小账**':
            items = []
            rest = re.sub(r'^\*\*小账[一二]?\*\*[：:　 ]*', '', l).strip()
            if rest: items.append(rest)
            j = i + 1
            pat = re.compile(r'^(- )?(第[一二]行[：:]|\*\*小账[一二]\*\*|\*\*本章命题的粗 F\*\*|\*\*本附录命题的粗 F\*\*)')
            while True:
                k = j
                while k < n and not lines[k].strip():
                    k += 1
                if k < n and pat.match(lines[k].strip()):
                    t = lines[k].strip()
                    t = re.sub(r'^- ', '', t)
                    t = re.sub(r'^第[一二]行[：:]\s*', '', t)
                    t = re.sub(r'^\*\*小账[一二]\*\*[：:　 ]*', '', t)
                    t = re.sub(r'^\*\*(本章|本附录)命题的粗 F\*\*[：:　 ]*', r'\1命题的粗 F：', t)
                    items.append(t); j = k + 1
                else:
                    break
            assert items, '小账无条目：第 %d 行附近' % i
            items = [x.replace('**', '') for x in items]
            out += ['> **小账**', '>']
            for q, it in enumerate(items):
                out.append('> ' + it)
                if q < len(items) - 1:
                    out.append('>')
            i = j; continue
        if l.startswith('- 小账'):
            j = i
            items = []
            while j < n and lines[j].startswith('- 小账'):
                items.append(re.sub(r'^小账[一二三]：', '', lines[j][2:].strip())); j += 1
            out += ['> **小账**', '>']
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            i = j; continue
        if re.match(r'^\*\*(两行)?小账\*\*[：:]?\s*$', l):
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            items = []
            while j < n and lines[j].startswith('- '):
                items.append(lines[j][2:].strip()); j += 1
            assert items, '小账无条目：第 %d 行附近' % i
            out += ['> **小账**', '>']
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            i = j; continue
        if l in ('**这一章的问题**', '## 这一章的问题'):
            para, i = next_para(i + 1)
            out.append('> **这一章的问题**：' + ''.join(x.strip() for x in para)); continue
        m = re.match(r'^\*\*这一章的问题\*\*[：:](.+)$', l)
        if m:
            out.append('> **这一章的问题**：' + m[1].strip()); i += 1; continue
        if l.startswith('### '):
            out.append('#### ' + l[4:].strip()); i += 1; continue
        if l.startswith('## '):
            out.append('### ◆ ' + l[3:].strip()); i += 1; continue
        out.append(l); i += 1
    # 去掉紧挨在章末的 ---（章与章之间不要分隔线）
    while out and out[-1].strip() in ('', '---'):
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def norm(l):
    """统一标题写法：编、章题用全角空格分隔。"""
    m = re.match(r'^# (第[一二三四五六]编)[ 　]+(.+)$', l)
    if m: return '# %s　%s' % (m[1], m[2])
    m = re.match(r'^## 第 ?(\d+) ?章[ 　]+(.+)$', l)
    if m: return '## 第%s章　%s' % (m[1], m[2])
    m = re.match(r'^# 附录 ?([A-E])[ 　]+(.+)$', l)
    if m: return '## 附录 %s　%s' % (m[1], m[2])   # 附录放在“# 附录”总页之下
    return l


def main():
    src = [norm(l) for l in (HERE / 'src/full.md').read_text(encoding='utf-8').splitlines()]
    tops, cur = [], None
    for l in src:
        if l.startswith('# '):
            cur = [l[2:].strip(), []]; tops.append(cur)
        elif l.startswith('## 附录 ') and cur is not None and not cur[0].startswith('第'):
            # 附录条目：并入同一个“附录”总页
            if not cur[0].startswith('附录'):
                cur = ['附录', []]; tops.append(cur)
            cur[1].append(l)
        elif cur is not None:
            cur[1].append(l)
    qian = next(t for t in tops if t[0].startswith('前言'))
    jie = next(t for t in tops if t[0].startswith('结语'))
    appx = next(t for t in tops if t[0] == '附录')
    parts, cp = [], None
    for t in tops:
        if re.match(r'^第.编　', t[0]):
            cp = [t[0], []]; parts.append(cp)
    # 章在各编之内（二级标题），切出来
    cur_part, chs = None, {}
    for t in tops:
        if re.match(r'^第.编　', t[0]):
            cur_part = t[0]; chs[cur_part] = []
            ch = None
            for l in t[1]:
                if l.startswith('## 第'):
                    ch = [l[3:].strip(), []]; chs[cur_part].append(ch)
                elif ch is not None:
                    ch[1].append(l)
    assert len(parts) == 6 and sum(len(v) for v in chs.values()) == 18, (len(parts), [len(v) for v in chs.values()])

    qian_md = conv_body(qian[1])
    (HERE / 'front/01-导言.md').write_text('# 前言　%s\n\n%s' % ('这本书想说什么', qian_md), encoding='utf-8')
    total = body_han_of(qian_md)
    for k, (pt, _) in enumerate(parts, 1):
        nm, title = pt.split('　', 1)
        chunks = ['# %s　%s\n\n%s\n' % (nm, title, INTRO[nm])]
        for ct, body in chs[pt]:
            md = conv_body(body)
            total += body_han_of(md)
            chunks.append('## %s\n\n%s' % (ct, md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    jie_md = conv_body(jie[1])
    total += body_han_of(jie_md)
    # 附录
    items, cur_i = [], None
    for l in appx[1]:
        if l.startswith('## 附录 '):
            cur_i = [l[3:].strip(), []]; items.append(cur_i)
        elif cur_i is not None:
            cur_i[1].append(l)
    appx_md = '附录 A–E 是方法、清单和数学形态的补充材料，不在正文字数之内：A 是发生档案模板，B 是对第 191 号相关条目的增订建议，C 是本书推演的推翻条件与文献核验表，D 是站内引书表，E 讲微分与积分。\n\n'
    appx_han = 0
    for t, bl in items:
        md = conv_body(bl)
        appx_han += body_han_of(md)
        appx_md += '## %s\n\n%s\n' % (t, md)
    wan = total / 10000

    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': appx_han}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan, '{AHAN}': format(appx_han, ',')}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl, encoding='utf-8')
    back = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a_, b_ in rep.items():
        back = back.replace(a_, b_)
    (HERE / 'back/12-后置.md').write_text('# 结语\n\n%s\n# 附录\n\n%s\n%s' % (jie_md, appx_md, back), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 7)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', total, 'appendix_han', appx_han, 'all_han', han(b))


if __name__ == '__main__':
    main()
