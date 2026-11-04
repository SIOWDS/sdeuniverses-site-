#!/usr/bin/env python3
"""《腐败与癌症》修订版：把统稿后的 /home/claude/work/edit/ 下各件合成 220/302 版式工具链（build.py）认的分卷稿。
只改格式，不动正文一个字：
  · 前置：front/00-前置.tpl.md（出版信息、题词、作者介绍、修订版说明）＋「本书写给谁」＋前言；
  · 十一篇 → parts/01–11.md：「# 第X篇　篇名」＋编序（副题、篇首导读、三锚点）＋各章；
    章级标题「## 引言：T」这类改成「## 引言　T」（标签与题名之间用全角空格，build.py 靠它分开）；
  · 后置 → back/12-后置.md：结论、金句集锦、参考书目、附录（术语表）、版本说明。
末了逐字核对：去掉 Markdown 记号与空白后，各篇正文与统稿稿完全一致。
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

ED = Path(M.MS_DIR)
META = json.loads((HERE / 'src/parts-meta.json').read_text())
CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一']
LABELS = ('附录A', '附录B', '结语', '结论', '插入章', '引言', '导论', '导论（上）', '导论（下）', '后记')
han = lambda s: len(re.findall(r'[一-鿿]', s))


def norm(t):
    return re.sub(r'[\s#*>◆]', '', t)


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|') and not x.startswith('SUBTITLE'))
    return han(t.replace('**', ''))


def fix_h2(line):
    m = re.match(r'^## ([^　：]{1,6})：(.+)$', line)
    if m and m[1] in LABELS:
        return '## %s　%s' % (m[1], m[2])
    return line


def part_md(k):
    src = (ED / ('p%d.md' % k)).read_text(encoding='utf-8')
    sub = (re.search(r'^SUBTITLE:\s*(.+)$', src, re.M) or [None, None])[1]
    body = re.sub(r'^SUBTITLE:.*\n+', '', src, flags=re.M).strip()
    body = '\n'.join(fix_h2(l) for l in body.splitlines())
    m = META[str(k)]
    head = ['# 第%s篇　%s' % (CN[k], m['title']), '']
    if sub:
        head += [sub.strip(), '']
    head += ['**篇首导读**　' + m['guide'], '', '**三锚点**', '']
    head += ['- ' + a for a in m['anchors']] + ['']
    out = '\n'.join(head) + '\n' + body + '\n'
    # 核对：正文部分与统稿稿逐字一致
    ref = '\n'.join(fix_h2(l) for l in re.sub(r'^SUBTITLE:.*$', '', src, flags=re.M).splitlines())
    assert norm(body) == norm(ref), k
    return out, body


def strip_h(md, first):
    """去掉统稿稿里的一级题（## 前言 等），返回 (题, 正文)。"""
    lines = md.strip().splitlines()
    assert lines[0].startswith('## '), lines[0]
    return lines[0][3:].strip(), '\n'.join(lines[1:]).strip()


def main():
    total = 0
    # ── 前置 ──
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8').rstrip()
    rd_t, rd = strip_h((ED / 'front_readers.md').read_text(encoding='utf-8'), '本书写给谁')
    pf_t, pf = strip_h((ED / 'front_preface.md').read_text(encoding='utf-8'), '前言')
    psub = re.search(r'^SUBTITLE:\s*(.+)$', pf, re.M)[1].strip()
    pf = re.sub(r'^SUBTITLE:.*\n+', '', pf, flags=re.M).strip()
    rd = re.sub(r'^### ', '### ◆ ', rd, flags=re.M)
    total += body_han_of(rd) + body_han_of(pf)
    front_extra = '## 本书写给谁　十二类读者的入口\n\n%s\n\n## 前言　%s\n\n%s\n' % (rd, psub, pf)
    # ── 十一篇 ──
    parts = []
    for k in range(1, 12):
        md, body = part_md(k)
        total += body_han_of(body) + han(META[str(k)]['guide']) + sum(han(a) for a in META[str(k)]['anchors'])
        parts.append(md)
    # ── 后置 ──
    con = (ED / 'back_conclusion.md').read_text(encoding='utf-8')
    i = con.index('## 金句集锦')
    c1, c2 = con[:i].strip(), con[i:].strip()
    c1 = re.sub(r'^## 结论　', '# 结论　', c1)
    c2 = re.sub(r'^## 金句集锦', '# 金句集锦　十句话带走全书', c2)
    c2 = re.sub(r'^### (\d+)）', r'### ◆ \1　', c2, flags=re.M)
    total += body_han_of(c1)
    gl_t, gl = strip_h((ED / 'back_glossary.md').read_text(encoding='utf-8'), '术语表')
    back_tpl = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    back = '\n\n'.join([c1, c2, (HERE / 'back/参考书目.md').read_text(encoding='utf-8').strip(),
                        '# 附录\n\n本书附录一件：术语表。\n\n## 附录一　术语表\n\n' + gl])
    wan = total / 10000
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_); back_tpl = back_tpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl + '\n\n' + front_extra, encoding='utf-8')
    (HERE / 'parts').mkdir(exist_ok=True)
    for f in (HERE / 'parts').glob('*.md'):
        f.unlink()
    for k, md in enumerate(parts, 1):
        (HERE / ('parts/%02d.md' % k)).write_text(md, encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text(back.rstrip() + '\n\n' + back_tpl.strip() + '\n', encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total}), encoding='utf-8')
    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 12)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok parts 11, chapters', len(re.findall(r'^## ', ''.join(parts), re.M)), 'body_han', total, 'wan %.1f' % wan, 'all_han', han(b))


if __name__ == '__main__':
    main()
