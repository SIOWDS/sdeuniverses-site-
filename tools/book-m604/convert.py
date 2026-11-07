#!/usr/bin/env python3
"""把 book/ 母本分章稿转成 569 工具链（build.py）认的分编稿。只做格式转换，不动正文文字。
  # 第N章　题 → ## 第 N 章　题；## N.M　题 / 其他 ## → ### ◆；### → ####；
  ## 这一章的问题／带走的话／两行小账 → 引用块（版式排青框／金框／小账）。
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
BOOK = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'book'
sys.path.insert(0, str(HERE))
import meta as M  # noqa
han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = [
    ('第一编　一句话的两副面孔', range(1, 4)),
    ('第二编　三态纠缠发生：事实长什么样', range(4, 8)),
    ('第三编　为什么总以为事实会自己说话', range(8, 12)),
    ('第四编　九格审判', range(12, 15)),
    ('第五编　敌人与邻居', range(15, 18)),
    ('第六编　AI 时代：总结的极限', range(18, 20)),
    ('第七编　五个领域：教育、健康、事业、管理、法律', range(20, 25)),
    ('第八编　日常用法与可证伪', range(25, 27)),
]
BOX = {'这一章的问题': '这一章的问题', '带走的话': '带走的话', '两行小账': '小账'}


def conv_chapter(text):
    lines = text.rstrip().split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    m = re.match(r'^# 第\s*(\d+)\s*章\s*(.*)$', lines[0].strip())
    assert m, lines[0]
    out = ['## 第 %s 章　%s' % (m[1], m[2].strip())]
    i = 1
    while i < len(lines):
        l = lines[i]
        hm = re.match(r'^(#{2,6}) (.*)$', l)
        if hm:
            lvl, t = len(hm[1]), hm[2].strip()
            if lvl == 2 and t in BOX:
                j = i + 1
                body = []
                while j < len(lines) and not re.match(r'^#{1,2} ', lines[j]):
                    body.append(lines[j]); j += 1
                paras = [x.strip() for x in body if x.strip()]
                out += ['', '> **%s**' % BOX[t], '>']
                for k, p in enumerate(paras):
                    out.append('> ' + p)
                    if k < len(paras) - 1:
                        out.append('>')
                out.append('')
                i = j
                continue
            if lvl == 2:
                out.append('### ◆ ' + t)
            elif lvl == 3:
                out.append('#### ' + t)
            else:
                out.append('**%s**' % t)
            i += 1
            continue
        if l.strip() in ('---', '***'):
            i += 1
            continue
        out.append(l.rstrip())
        i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out).strip() + '\n')


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    total = 0
    book = []
    for k, (title, rng) in enumerate(PARTS, 1):
        segs = ['# ' + title, '']
        for n in rng:
            c = conv_chapter((BOOK / ('ch%02d.md' % n)).read_text(encoding='utf-8'))
            total += han('\n'.join(x for x in c.splitlines() if not x.startswith('#')))
            segs.append(c)
        md = '\n'.join(segs)
        (HERE / ('parts/%02d.md' % k)).write_text(md, encoding='utf-8')
        book.append(md)
    qian = (BOOK / '00-前言.md').read_text(encoding='utf-8').strip()
    qian = re.sub(r'(?m)^# 前言.*$', '## 前言', qian, count=1)
    qian = re.sub(r'(?m)^## (?!前言)(.*)$', r'### ◆ \1', qian)
    qian = re.sub(r'(?m)^### (?!◆)(.*)$', r'#### \1', qian)
    dao = (BOOK / '01-导读.md').read_text(encoding='utf-8').strip()
    dao = re.sub(r'(?m)^# 导读[：:　 ]*(.*)$', r'# 导读　\1', dao, count=1)
    jie = (BOOK / 'ch27-结语.md').read_text(encoding='utf-8').strip()
    jie = re.sub(r'(?m)^# 结语[：:　 ]*(.*)$', r'# 结语　\1', jie, count=1)
    app = (BOOK / 'ch28-附录.md').read_text(encoding='utf-8').strip()
    app = re.sub(r'(?m)^## (附录[一二三四五六七八九十]) +(.*)$', r'## \1　\2', app)
    ban = (HERE / 'banben.md').read_text(encoding='utf-8').strip()
    fronthan, daohan, jiehan, apphan = han(qian), han(dao), han(jie), han(app)
    allhan = total + fronthan + daohan + jiehan
    wan = allhan / 10000
    cp = (HERE / 'cp.md').read_text(encoding='utf-8').replace('@@WAN@@', '%.1f' % wan).replace('@@HAN@@', '{:,}'.format(allhan))
    (HERE / 'front/00-前置.md').write_text(cp + '\n' + qian + '\n', encoding='utf-8')
    (HERE / 'front/01-导言.md').write_text(dao + '\n', encoding='utf-8')
    back = '\n\n'.join([jie, app, ban])
    (HERE / 'back/12-后置.md').write_text(back + '\n', encoding='utf-8')
    (HERE / 'book.md').write_text('\n\n'.join([cp, qian, dao] + book + [back]), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': allhan, 'chapters': total}, ensure_ascii=False))
    print('ok chapters-han', total, 'front', fronthan, 'dao', daohan, 'jie', jiehan, 'app', apphan, 'all', allhan)


if __name__ == '__main__':
    main()
