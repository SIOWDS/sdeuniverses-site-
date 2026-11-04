#!/usr/bin/env python3
"""把 chapters/ 的统稿稿转成成书用的分编稿 front/ parts/ back/（章式照第 302 号，版式照第 220 号）。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / 'src'
NO, ISBN, PRICE = 487, '979-8-90690-977-0', 'US$20.00'
PARTS = [('01-第一编', range(1, 12)), ('02-第二编', range(12, 16)), ('03-第三编', range(16, 27)),
         ('04-第四编', range(27, 34)), ('05-第五编', range(34, 38))]
CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二']
LABELS = ('> **这一章的问题**', '> **带走的话**', '> **小账**')
FLOOR = re.compile(r'^[一二三四五六七八九十]+、\s*')


def body_of(text, last_rename=None):
    out, n = [], 0
    for ln in text.splitlines():
        ln = ln.rstrip()
        if ln.startswith(LABELS):
            out += ['', ln]
        elif ln.startswith('## '):
            n += 1
            t = FLOOR.sub('', ln[3:].strip())
            if last_rename and t == '这一章怎样算错':
                t = last_rename
            out += ['', '### ◆ %s、%s' % (CN[n], t), '']
        elif ln.startswith('# '):
            pass
        else:
            out.append(ln)
    s = re.sub(r'\n{3,}', '\n\n', '\n'.join(out))
    return s.strip() + '\n'


def chap(n):
    t = (SRC / ('ch%02d.md' % n)).read_text(encoding='utf-8')
    first = t.splitlines()[0]
    m = re.match(r'^# 第\s*(\d+)\s*章[　 ]+(.*)$', first)
    assert m and int(m[1]) == n, (n, first)
    body = body_of(t.split('\n', 1)[1])
    assert '这一章的问题' in body and '**带走的话**' in body and '**小账**' in body, ('缺章式要件', n)
    return '## 第 %d 章　%s\n\n%s' % (n, m[2].strip(), body)


def main():
    han = sum(len(re.findall(r'[一-鿿]', p.read_text(encoding='utf-8'))) for p in SRC.glob('*.md'))
    src_front = (ROOT / 'src_front.md').read_text(encoding='utf-8')
    han_front = len(re.findall(r'[一-鿿]', src_front)) + len(re.findall(r'[一-鿿]', (ROOT / 'src_parts.md').read_text(encoding='utf-8')))
    wan = '%.0f' % ((han + han_front) / 10000)
    qian = body_of((SRC / 'qianyan.md').read_text(encoding='utf-8'))
    front = src_front.replace('__QIANYAN__', qian).replace('__NO__', str(NO)).replace('__ISBN__', ISBN)\
        .replace('__PRICE__', PRICE).replace('__WAN__', wan)
    (ROOT / 'front').mkdir(exist_ok=True); (ROOT / 'parts').mkdir(exist_ok=True); (ROOT / 'back').mkdir(exist_ok=True)
    (ROOT / 'front/00-前置.md').write_text(front, encoding='utf-8')
    d = (SRC / 'daolun.md').read_text(encoding='utf-8')
    (ROOT / 'front/01-导论.md').write_text(d.splitlines()[0] + '\n\n' + body_of(d.split('\n', 1)[1], '这一篇怎样算错'), encoding='utf-8')
    intros = re.split(r'(?m)^# ', (ROOT / 'src_parts.md').read_text(encoding='utf-8'))[1:]
    assert len(intros) == len(PARTS)
    for (name, rng), intro in zip(PARTS, intros):
        (ROOT / 'parts' / (name + '.md')).write_text('# ' + intro.strip() + '\n\n' + '\n'.join(chap(n) for n in rng), encoding='utf-8')
    j = (SRC / 'jieyu.md').read_text(encoding='utf-8')
    (ROOT / 'back/09-结语.md').write_text(j.splitlines()[0] + '\n\n' + body_of(j.split('\n', 1)[1]), encoding='utf-8')
    bib = (SRC / 'cankao.md').read_text(encoding='utf-8').strip() if (SRC / 'cankao.md').exists() else '# 参考书目\n\n（待补）'
    ful = (SRC / 'fulu.md').read_text(encoding='utf-8').strip()
    wu = (ROOT / 'src_fulu_wu.md')
    (ROOT / 'back/10-后置.md').write_text(bib + '\n\n' + ful + ('\n\n' + wu.read_text(encoding='utf-8').strip() if wu.exists() else '') + '\n', encoding='utf-8')
    (ROOT / 'han.json').write_text(json.dumps({'body': han + han_front}) + '\n')
    (ROOT / 'book.md').write_text('\n\n'.join((ROOT / 'parts' / (n + '.md')).read_text(encoding='utf-8').strip() for n, _ in PARTS) + '\n', encoding='utf-8')
    print('ok 汉字', han + han_front, '约', wan, '万字')


if __name__ == '__main__':
    main()
