#!/usr/bin/env python3
"""第 587 号《一个人养不出的清明》（贝芳 著）：把三审定稿（/home/claude/qingming 下 chapters/*.md 与 front/ 的
导读、编首语、小账、参考书目、版本说明）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

转换：章题「# 第N章　T」→「## 第 N 章　T」；节「## T」→「### ◆ 一、T」（按章内次序编号）；「### T」→「#### T」；
第一、二编章末两个固定小块「今晚可以做的一件小事」「写给自己的一句话」→ 引文框；每章末尾加「小账」框（front/xiaozhang.json）。
总论（第1—2章）与三编各为一卷；前言、导读放前置；结语、参考书目、附录、版本说明放后置。
产物：front/00-前置.md、parts/01..04.md、back/12-后置.md、book.md、han.json。
用法：python3 tools/book-m587/conv587.py [定稿根目录，默认 meta.SRC]
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

B = Path(sys.argv[1] if len(sys.argv) > 1 else M.SRC)
CH, FR = B / 'chapters', B / 'front'
han = lambda s: len(re.findall(r'[一-鿿]', s))
CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五']
FIXED = ('今晚可以做的一件小事', '写给自己的一句话')
XZ = json.loads((FR / 'xiaozhang.json').read_text(encoding='utf-8'))
PARTS = json.loads((FR / 'parts.json').read_text(encoding='utf-8'))


def conv_body(text, xz_key=None):
    out, sec, i = [], 0, 0
    lines = text.splitlines()
    while i < len(lines):
        l = lines[i].rstrip()
        if l.startswith('## '):
            t = l[3:].strip()
            if t in FIXED:
                # 固定小块：收进引文框，直到下一个标题
                j, paras = i + 1, []
                while j < len(lines) and not lines[j].startswith('#'):
                    if lines[j].strip():
                        paras.append(lines[j].strip())
                    j += 1
                out += ['> **%s**' % t]
                for p in paras:
                    out += ['>', '> ' + p]
                out.append('')
                i = j
                continue
            sec += 1
            out.append('### ◆ %s、%s' % (CN[sec], t))
        elif l.startswith('### '):
            out.append('#### ' + l[4:].strip())
        else:
            out.append(l)
        i += 1
    if xz_key and XZ.get(xz_key):
        out += ['', '> **小账**', '>', '> ' + XZ[xz_key]]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', '').replace('今晚可以做的一件小事', '').replace('写给自己的一句话', '').replace('小账', ''))


def split_title(txt):
    head, _, body = txt.partition('\n')
    return head.lstrip('# ').strip(), body


def rd(p):
    return Path(p).read_text(encoding='utf-8').strip()


def main():
    total = 0
    # 前置：作者介绍（取自 fm_info.md 的作者简介段）、前言、导读
    info = rd(FR / 'fm_info.md')
    bio = info.split('# 作者简介', 1)[1].strip()
    fronts = ['## 作者介绍\n\n' + bio + '\n']
    t, b = split_title(rd(CH / 'ch00_序.md'))
    md = conv_body(b, '前言'); total += body_han_of(md)
    fronts.append('## %s\n\n%s' % (t, md))
    t, b = split_title(rd(FR / 'fm_daodu.md'))
    md = conv_body(b); total += body_han_of(md)
    fronts.append('## %s\n\n%s' % (t, md))
    # 总论与三编
    plan = [('总论', range(1, 3)), ('第一编', range(3, 9)), ('第二编', range(9, 17)), ('第三编', range(17, 22))]
    for k, (pk, rg) in enumerate(plan, 1):
        P = PARTS[pk]
        total += han(P['intro'])
        chunks = ['# %s　%s\n\n%s\n' % (P['label'], P['title'], P['intro'])]
        for n in rg:
            t, b = split_title(rd(CH / ('ch%02d.md' % n)))
            m = re.match(r'^第(\d+)章\s*(.*)$', t)
            assert m and int(m[1]) == n, (n, t)
            md = conv_body(b, 'ch%02d' % n); total += body_han_of(md)
            chunks.append('## 第 %d 章　%s\n\n%s' % (n, m[2].strip(), md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    # 后置：结语、参考书目、附录、版本说明
    t, b = split_title(rd(CH / 'ch22_结语.md'))
    jmd = conv_body(b, 'ch22_结语'); total += body_han_of(jmd)
    back = ['# %s\n\n%s' % (t, jmd)]
    t, b = split_title(rd(FR / 'bm_refs.md'))
    back.append('# 参考书目\n\n' + b.strip() + '\n')
    ap = rd(CH / 'ch99_附录.md')
    ap = re.sub(r'^# 附录\s*\n', '', ap)
    ap = re.sub(r'^### ', '#### ', ap, flags=re.M)
    appx = han(ap)
    back.append('# 附录\n\n本书附录五件：一周身体记录表、就诊前的那一页纸、和AI一起开始的三小步、资料来源、你的问题在书里的哪一章。\n\n' + ap.strip() + '\n')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % (total / 10000), '{ALL}': '%.0f' % (total / 10000), '{APPX}': format(appx, ',')}
    tail = (HERE / 'back/12-版本说明.tpl.md').read_text(encoding='utf-8')
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, c in rep.items():
        tail = tail.replace(a, c); tpl = tpl.replace(a, c)
    back.append(tail)
    (HERE / 'back/12-后置.md').write_text('\n'.join(back), encoding='utf-8')
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fronts), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': appx}), encoding='utf-8')
    for f in (HERE / 'parts').glob('0[5-9].md'):
        f.unlink()
    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 5)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    bk = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok parts', len(re.findall(r'^# (总论|第.编)　', bk, re.M)), 'chapters', len(re.findall(r'^## 第 \d+ 章　', bk, re.M)),
          'body_han', total, 'appendix_han', appx)


if __name__ == '__main__':
    main()
