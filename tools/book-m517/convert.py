#!/usr/bin/env python3
"""把三审稿 src/ch*.md 与章式要件 src/form/ 转成成书用的分编稿 front/ parts/ back/（章式照第 302 号，版式照第 220 号）。
在 tools/book-m517 下运行。每章的依据已合成书后参考书目，这里去掉。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / 'src'
NO, ISBN, PRICE = 517, '978-1-970820-11-9', 'US$55.00'
PARTS = [('01-第一编', range(1, 5)), ('02-第二编', range(5, 9)), ('03-第三编', range(9, 13)), ('04-第四编', range(13, 16)),
         ('05-第五编', range(16, 20)), ('06-第六编', range(20, 24)), ('07-第七编', range(24, 29)), ('08-第八编', range(29, 36)), ('09-第九编', range(36, 39))]
CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十']
HANRE = re.compile(r'[一-鿿]')


def strip_yiju(t):
    m = re.search(r'(?m)^#{0,3}\s*本章依据\s*$', t)
    return t[:m.start()].rstrip() + '\n' if m else t


def body_of(text, extra=None):
    out, n = [], 0
    for ln in text.splitlines():
        ln = ln.rstrip()
        if ln.startswith('## '):
            n += 1
            out += ['', '### ◆ %s、%s' % (CN[n], ln[3:].strip()), '']
        elif ln.startswith('### '):
            out += ['', '**%s**' % ln[4:].strip(), '']
        elif ln.startswith('# '):
            pass
        else:
            out.append(ln)
    if extra:
        n += 1
        out += ['', '### ◆ %s、%s' % (CN[n], extra[0]), '', extra[1], '']
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def chap(n):
    t = strip_yiju((SRC / ('ch%02d.md' % n)).read_text(encoding='utf-8'))
    F = json.loads((SRC / 'form' / ('ch%02d.json' % n)).read_text(encoding='utf-8'))
    first = t.splitlines()[0]
    m = re.match(r'^# 第\s*(\d+)\s*章[　 ]+(.*)$', first)
    assert m and int(m[1]) == n, (n, first)
    assert F['n'] == n
    ex = F.get('wrongExisting', '').strip()
    extra = None
    if ex:
        assert ex == '全章' or ('## ' + ex) in t or ('### ' + ex) in t, ('wrongExisting 未找到', n, ex)
    else:
        assert F['wrong'].strip(), ('缺 wrong', n)
        extra = ('这一章怎样算错', F['wrong'].strip())
    body = body_of(t.split('\n', 1)[1], extra)
    head = '## 第 %d 章　%s\n\n> **这一章的问题**：%s\n\n' % (n, m[2].strip(), F['question'].strip())
    tail = '\n> **带走的话**\n> %s\n\n> **小账**\n> 靠什么写的？——%s\n> 还欠什么？——%s\n' % (F['takeaway'].strip(), F['read'].strip(), F['owe'].strip())
    return head + body + tail


def main():
    bodies = {n: chap(n) for _, r in PARTS for n in r}
    src_front = (ROOT / 'src_front.md').read_text(encoding='utf-8')
    qian = body_of((SRC / 'qianyan.md').read_text(encoding='utf-8'))
    dao = body_of((SRC / 'daodu.md').read_text(encoding='utf-8'))
    xiu = (SRC / 'xiuding.md').read_text(encoding='utf-8').strip()
    jie = (SRC / 'jieyu.md').read_text(encoding='utf-8')
    fulu = []
    for f in ['fulu_a', 'fulu_b', 'fulu_c', 'fulu_d', 'fulu_e', 'fulu_f', 'jinju', 'shuyu']:
        tx = (SRC / (f + '.md')).read_text(encoding='utf-8')
        out = []
        for ln in tx.splitlines():
            if ln.startswith('### '):
                out.append('**%s**' % ln[4:].strip())
            elif ln.startswith('## '):
                out.append('### ' + ln[3:].strip())
            elif ln.startswith('# '):
                out.append('## ' + ln[2:].strip())
            else:
                out.append(ln)
        fulu.append('\n'.join(out).strip())
    fulu_md = '# 附录\n\n下面几件是全书的配套：作者早年写下的五篇专论，这一版新增的“这本书怎样算错”，全书金句和术语表。\n\n' + '\n\n'.join(fulu) + '\n'
    cank = (SRC / 'cankao.md').read_text(encoding='utf-8').strip()
    jie_body = jie.splitlines()[0] + '\n\n' + body_of(jie.split('\n', 1)[1])
    han = sum(len(HANRE.findall(x)) for x in bodies.values()) + sum(len(HANRE.findall(x)) for x in (qian, dao, xiu, jie_body, fulu_md, cank, src_front))
    wan = '%.0f' % (han / 10000)
    front = src_front.replace('__XIUDING__', xiu).replace('__QIANYAN__', qian).replace('__DAODU__', dao).replace('__NO__', str(NO)).replace('__ISBN__', ISBN).replace('__PRICE__', PRICE).replace('__WAN__', wan)
    for d in ('front', 'parts', 'back'):
        (ROOT / d).mkdir(exist_ok=True)
    (ROOT / 'front/00-前置.md').write_text(front, encoding='utf-8')
    for i, (name, rng) in enumerate(PARTS, 1):
        intro = (SRC / ('bianxu_%d.md' % i)).read_text(encoding='utf-8').strip()
        (ROOT / 'parts' / (name + '.md')).write_text(intro + '\n\n' + '\n'.join(bodies[n] for n in rng), encoding='utf-8')
    (ROOT / 'back/09-结语.md').write_text(jie_body, encoding='utf-8')
    (ROOT / 'back/10-后置.md').write_text(cank + '\n\n' + fulu_md, encoding='utf-8')
    (ROOT / 'han.json').write_text(json.dumps({'body': han}) + '\n')
    (ROOT / 'book.md').write_text('\n\n'.join((ROOT / 'parts' / (n + '.md')).read_text(encoding='utf-8').strip() for n, _ in PARTS) + '\n', encoding='utf-8')
    print('ok 汉字', han, '约', wan, '万字')


if __name__ == '__main__':
    main()
