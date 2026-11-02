#!/usr/bin/env python3
"""第 479 号：把统稿定稿（src/ 下 front_前言.md、front_作者导读.md、ch00_导言.md、ch01–23.md、ch24_结语.md、appendix.md）
转成 220/302 版式工具链（build.py）认的分卷稿：front/00-前置.md、front/01-导言.md、parts/01–05.md、back/12-后置.md、book.md、han.json。
只做格式转换，不动正文文字。用法（仓库根目录或本目录）：python3 tools/book-m479/convert479.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = HERE / 'src'
han = lambda s: len(re.findall(r'[一-鿿]', s))

PARTS = [
    (1, '第一编', '困局：读数当家的学校',
     '这一编（第 1—3 章）摆出缺口：生源退潮之后，学位分成了价格账与使用账；招生数怎样一步一步接管一所学校；家庭交的学费，到底买了一个什么样的捆绑包。生源减少改变的是土壤，学校惯用的应对却只拧读数。'),
    (4, '第二编', '原理：学校价值的三大发生机制',
     '这一编（第 4—9 章）是全书的底盘。第 4 章重新定义学校价值；第 5—7 章写效能、实践、意义三条方程，每章讲清关系、起手的路径、推动它的动力和它熄火的样子；第 8 章写实践再生的成熟形态——持史；第 9 章写三条方程怎样健康运行、互相纠缠、互相激发。学校的价值不是学校拥有的东西，是一次次发生出来、也会一次次断档的东西。'),
    (10, '第三编', '路径：价值再生的七个抓手',
     '这一编（第 10—16 章）落到学校每天的工作：价值定位、课程、个性化、家校信任、教师、财务、组织。每章先写已经做对的，再写站内专著提醒的盲点，最后给做法、读数与怎样算错。'),
    (17, '第四编', '账本：把三方程放进真实的学校',
     '这一编（第 17—20 章）把三条方程落成可检验的诊断工具：重排学校的账本；放回江城与巴渝两所学校复盘；写校长本人；最后写本书自己怎样算错。一本讲兑现的书，自己也要先把承诺写清楚。'),
    (21, '第五编', '未来：AI时代的民办小学',
     '这一编（第 21—23 章）打开新的缺口：AI 来了以后，学校这个捆绑包被拆走的是哪几格；小学阶段怎样让 AI 进校园；生源继续减少的十年里，民办小学可以走的三条路。'),
]


def body_lines(text, drop_h1=True):
    """标题降级与章末件转换。"""
    out, acc = [], []
    lines = text.strip('\n').split('\n')
    if drop_h1 and lines and lines[0].startswith('# '):
        lines = lines[1:]

    def flush_acc():
        if acc:
            out.extend(['> **小账**', '>'])
            for k, a in enumerate(acc):
                out.append('> ' + a)
                if k < len(acc) - 1:
                    out.append('>')
            out.append('')
            acc.clear()
    for l in lines:
        s = l.rstrip()
        m = re.match(r'^【带走的话】\s*(.+)$', s)
        if m:
            flush_acc(); out.extend(['> **带走的话**', '>', '> ' + m[1], '']); continue
        m = re.match(r'^【小账】\s*(.+)$', s)
        if m:
            acc.append(m[1]); continue
        if acc and s.strip() == '':
            continue
        flush_acc()
        m = re.match(r'^> \*\*这一章的问题[：:]\s*(.+?)\*\*\s*$', s)
        if m:
            out.append('> **这一章的问题**：' + m[1]); continue
        if s.startswith('### '):
            out.append('#### ' + s[4:].strip()); continue
        if s.startswith('## '):
            out.append('### ◆ ' + s[3:].strip()); continue
        if s.startswith('# '):
            out.append('### ◆ ' + s[2:].strip()); continue
        out.append(s)
    flush_acc()
    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out).strip() + '\n'


def count(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    total = 0
    # 前言、导读、作者介绍
    pre = (S / 'front_前言.md').read_text(encoding='utf-8')
    pre_title = pre.split('\n', 1)[0][2:].strip()
    pre_md = body_lines(pre); total += count(pre_md)
    ad = (S / 'front_作者导读.md').read_text(encoding='utf-8')
    author_txt, guide_txt = ad.split('# 导读', 1)
    author_md = body_lines(author_txt)
    guide_md = body_lines('# 导读' + guide_txt); total += count(guide_md)
    # 导言
    lun = (S / 'ch00_导言.md').read_text(encoding='utf-8')
    lun_title = lun.split('\n', 1)[0][2:].strip()
    lun_md = body_lines(lun); total += count(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lun_title, lun_md), encoding='utf-8')
    # 各编
    starts = [p[0] for p in PARTS] + [24]
    for k, (st, nm, tt, intro) in enumerate(PARTS, 1):
        chunks = ['# %s　%s\n\n%s\n' % (nm, tt, intro)]
        for n in range(st, starts[k]):
            t = (S / ('ch%02d.md' % n)).read_text(encoding='utf-8')
            h = t.split('\n', 1)[0]
            m = re.match(r'^# 第 ?(\d+) ?章[\s　]+(.+)$', h)
            assert m and int(m[1]) == n, h
            md = body_lines(t); total += count(md)
            chunks.append('## 第 %d 章　%s\n\n%s' % (n, m[2].strip(), md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    # 结语与附录
    jie = (S / 'ch24_结语.md').read_text(encoding='utf-8')
    jie_title = jie.split('\n', 1)[0][2:].strip()
    jie_md = body_lines(jie); total += count(jie_md)
    ap = (S / 'appendix.md').read_text(encoding='utf-8')
    items = re.split(r'\n(?=# 附录)', '\n' + ap.strip())
    app_md, app_han = [], 0
    for it in items:
        it = it.strip()
        if not it:
            continue
        h, _, b = it.partition('\n')
        md = body_lines(b, drop_h1=False)
        app_han += count(md)
        app_md.append('## %s\n\n%s' % (h[2:].strip(), md))
    total += app_han
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': app_han}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        tpl = tpl.replace(a, b)
    tpl = tpl.replace('{AUTHOR_INTRO}', author_md.strip())
    front = tpl.rstrip() + '\n\n## %s\n\n%s\n## 导读\n\n%s' % (pre_title, pre_md, guide_md)
    (HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
    back = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        back = back.replace(a, b)
    appx = ('# 附录\n\n附录八件，供查、供对、供用：A 是作者工作年表；B 按持史四条重读家校共育十二大课程；'
            'C 是精细化单字清单与复审四栏；D 是三方程诊断量表与使用规则；E 是预案卡模板；'
            'F 是命题登记册摘要；G 是站内邻书对账表；H 是材料代码与数据来源。\n\n' + '\n'.join(app_md))
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n%s\n%s' % (jie_title, jie_md, appx, back), encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 6)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b))


if __name__ == '__main__':
    main()
