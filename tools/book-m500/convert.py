#!/usr/bin/env python3
"""第 500 号《AI是加速你的落地》：把三审稿（src/ch/*.md 与 src/parts.json）转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文文字：标题改写、## 改成 ### ◆、直引号改弯引号、参考文献去掉斜体记号。
产物：front/00-前置.md、front/01-导论.md、parts/01—07、back/09-结语.md、back/10-后置.md、book.md、han.json。
用法：python3 tools/book-m500/convert.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / 'src' / 'ch'
PARTS = json.loads((HERE / 'src' / 'parts.json').read_text(encoding='utf-8'))
CN = '一二三四五六七'
han = lambda s: len(re.findall(r'[一-鿿]', s))


def quotes(s):
    out = []
    for line in s.split('\n'):
        o = True
        r = ''
        for c in line:
            if c == '"':
                r += '“' if o else '”'
                o = not o
            else:
                r += c
        assert o, '引号不成对：' + line[:60]
        out.append(r)
    return '\n'.join(out)


def body_of(name):
    t = quotes((SRC / name).read_text(encoding='utf-8')).strip()
    head, _, rest = t.partition('\n')
    assert head.startswith('# '), name
    rest = re.sub(r'^### ', '#### ', rest, flags=re.M)
    rest = re.sub(r'^## ', '### ◆ ', rest, flags=re.M)
    return head[2:].strip(), rest.strip()


def main():
    total = 0
    # 前言
    h, pre = body_of('00.md')
    m = re.match(r'^前言[：:　 ]*(.*)$', h)
    total += han(pre)
    front = (HERE / 'src' / 'front.tpl.md').read_text(encoding='utf-8').rstrip() + '\n\n## 前言　%s\n\n%s\n' % (m[1], pre)
    # 导论
    h, lun = body_of('00b.md')
    m = re.match(r'^导论[：:　 ]*(.*)$', h)
    total += han(lun)
    lun_md = '# 导论　%s\n\n%s\n' % (m[1], lun)
    # 七编
    parts = []
    starts = sorted(int(k) for k in PARTS)
    for i, st in enumerate(starts):
        en = starts[i + 1] - 1 if i + 1 < len(starts) else 36
        p = PARTS[str(st)]
        title = re.sub(r'^第.编[　 ]*', '', p['title'])
        total += han(p['intro'])
        chunk = ['# 第%s编　%s：%s' % (CN[i], title, p['sub']), '', quotes(p['intro']), '']
        for n in range(st, en + 1):
            h, b = body_of('%02d.md' % n)
            cm = re.match(r'^第(\d+)章[　 ]+(.*)$', h)
            assert cm and int(cm[1]) == n, h
            total += han(b)
            chunk += ['## 第 %d 章　%s' % (n, cm[2]), '', b, '']
        parts.append('\n'.join(chunk))
    # 结语
    h, end = body_of('37.md')
    m = re.match(r'^结语[：:　 ]*(.*)$', h)
    total += han(end)
    end_md = '# 结语　%s\n\n%s\n' % (m[1], end)
    # 附录、后记
    h1, a1 = body_of('39.md')
    h2, a2 = body_of('40.md')
    a2 = re.sub(r'(?<![*])\*([^*\n]+)\*(?![*])', r'\1', a2)
    h3, hou = body_of('38.md')
    total += han(a1) + han(hou)
    ta = lambda s: re.sub(r'^附录(.)[　 ]+', r'附录\1　', s)
    back = '# 附录\n\n## %s\n\n%s\n\n## %s\n\n%s\n\n# 后记\n\n%s\n' % (ta(h1), a1, ta(h2), a2, hou)
    wan = total / 10000
    front = front.replace('{WAN}', '%.0f' % wan).replace('{HAN}', format(total, ','))
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'parts').mkdir(exist_ok=True)
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
    (HERE / 'front/01-导论.md').write_text(lun_md, encoding='utf-8')
    for k, chunk in enumerate(parts, 1):
        (HERE / ('parts/%02d-第%s编.md' % (k, CN[k - 1]))).write_text(chunk + '\n', encoding='utf-8')
    (HERE / 'back/09-结语.md').write_text(end_md, encoding='utf-8')
    (HERE / 'back/10-后置.md').write_text(back, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d-第%s编.md' % (k, CN[k - 1]) for k in range(1, 8)] + ['back/09-结语.md', 'back/10-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'parts', len(parts), 'body_han', total)


if __name__ == '__main__':
    main()
