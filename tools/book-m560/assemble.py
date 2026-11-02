#!/usr/bin/env python3
"""第 560 号：把 /home/claude/wenxue-puxi/chapters/ 下三审稿合成 src/full.md（convert.py 认的格式）。
- 章题「# 第X章　T」→「## 第 N 章　T」；前言、结语「# X　T」→「## X　T」；插入三编编题。
- 节题「## ◆ …」→「### ◆ …」，「### T」→「#### T」。
- 章末装置统一：带走的话 → 「> **带走的话**」框；两行小账／小账一二 → 「> **小账**」框；想一想 → 「### ◆ 想一想」。
用法：python3 assemble.py [章稿目录]
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/wenxue-puxi/chapters')
CN = {c: i for i, c in enumerate('零一二三四五六七八九十')}
PARTS = {
    1: ('# 第一编　病：后现代的误读', '后现代拆掉统一性，拆得对；病在它把「统一性碎了」读成了「意义没了」。这一编先看统一性文学是怎么来的，再看后现代只做了一半，最后找到误读的根。'),
    4: ('# 第二编　谱系：七位作家，一次搬家', '从卡夫卡到残雪，七位作家排开，正好是意义搬家的全程：从统一性还在却够不着，到同一性只在一个自我、一场梦里新发生。'),
    11: ('# 第三编　救赎：同一性谱系的文学', '把七站画成一张图，把读者也放进谱系，再看 AI 把统一性变成水电之后，文学剩下什么：一个人、一个部落的字，怎样发生。'),
}


def cnnum(s):
    if s == '十':
        return 10
    if s.startswith('十'):
        return 10 + CN[s[1]]
    if len(s) == 2 and s[1] == '十':
        return CN[s[0]] * 10
    if '十' in s:
        a, b = s.split('十')
        return CN[a] * 10 + CN[b]
    return CN[s]


def plain(s):
    s = re.sub(r'^\s*>\s?', '', s)
    s = re.sub(r'^\s*[-*]\s+', '', s)
    return s.replace('**', '').strip()


MARK_TAKE = re.compile(r'^(?:#+\s*◆?\s*[一二三四五六七八九十]*、?\s*)?带走的话\s*[：:　]?\s*(.*)$')
MARK_LEDGER = re.compile(r'^(?:两行)?小账(?:[一二])?\s*[：:　]?\s*(.*)$')
MARK_THINK = re.compile(r'^(?:#+\s*◆?\s*[一二三四五六七八九十]*、?\s*)?想一想\s*[：:]?\s*$')


def end_zone(lines):
    """把章末（带走的话起）解析成三段。"""
    take, ledger, think, cur, tail = [], [], [], None, []
    for k, raw in enumerate(lines):
        if cur == 'think' and raw.startswith('#') and not MARK_THINK.match(re.sub(r'^#+\s*', '', raw.strip())):
            tail = lines[k:]
            break
        if raw.strip() in ('>', ''):
            if cur == 'think':
                think.append('')
            continue
        p = plain(raw)
        hd = re.sub(r'^#+\s*', '', raw.strip())
        m = MARK_TAKE.match(p) if '带走的话' in p and len(p) < 200 and (raw.lstrip().startswith(('#', '>', '**')) or p.startswith('带走的话')) else None
        if m and cur != 'think':
            cur = 'take'
            if m.group(1):
                take.append(m.group(1))
            continue
        m = MARK_LEDGER.match(p) if cur in ('take', 'ledger') else None
        if m:
            cur = 'ledger'
            rest = m.group(1)
            if rest:
                if '第二行' in rest:
                    a, b = rest.split('第二行', 1)
                    ledger += [a.strip(), '第二行' + b.strip()]
                else:
                    ledger.append(p if p.startswith('小账一') or p.startswith('小账二') else rest)
            continue
        if MARK_THINK.match(p) or MARK_THINK.match(hd):
            cur = 'think'
            continue
        if cur == 'take':
            take.append(p)
        elif cur == 'ledger':
            ledger.append(p)
        elif cur == 'think':
            q = re.sub(r'^\s*>\s?', '', raw).rstrip()
            q = re.sub(r'^(\d)[.．、]\s*', lambda m: '一二三四五六七八九'[int(m.group(1)) - 1] + '、', q)
            q = re.sub(r'^([一二三四五六七八九])[，,]\s*', r'\1、', q)
            think.append(q)
        else:
            raise SystemExit('unparsed end-zone line: ' + raw)
    out = []
    if take:
        out += ['> **带走的话**', '>', '> ' + ''.join(take).replace('**', '')]
    if ledger:
        out += ['', '> **小账**']
        for it in ledger:
            out += ['>', '> ' + it]
    if think:
        while think and not think[-1].strip():
            think.pop()
        while think and not think[0].strip():
            think.pop(0)
        out += ['', '### ◆ 想一想', ''] + think
    for l in tail:
        if l.startswith('### '):
            l = '#### ' + l[4:]
        elif l.startswith('## '):
            l = '### ' + l[3:]
        elif l.strip() == '---':
            continue
        out.append(l)
    return out, len(take), len(ledger), len([x for x in think if x.strip()])


def convert_chapter(text, kind):
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    h = lines[0]
    m = re.match(r'^#\s*第([一二三四五六七八九十]+)章[\s　]*(.*)$', h)
    if m:
        head = '## 第 %d 章　%s' % (cnnum(m.group(1)), m.group(2).strip())
        no = cnnum(m.group(1))
    else:
        m = re.match(r'^#\s*(前言|结语)[\s　]*(.*)$', h)
        assert m, h
        head = '## %s　%s' % (m.group(1), m.group(2).strip())
        no = None
    body = lines[1:]
    # 章末：从最后一个「带走的话」标记起（只认标题、粗体或引用块里的标记）
    zi = None
    for i, l in enumerate(body):
        p = re.sub(r'^#+\s*', '', plain(l))
        if '带走的话' in p and (l.lstrip().startswith(('#', '>', '**'))) and len(p) < 200 and (p.startswith('带走的话') or re.match(r'^◆?\s*[一二三四五六七八九十]*、?\s*带走的话', p)):
            zi = i
    assert zi is not None, 'no 带走的话 in ' + head
    pre, zone = body[:zi], body[zi:]
    z, nt, nl, nk = end_zone(zone)
    out = []
    for l in pre:
        if l.startswith('### '):
            l = '#### ' + l[4:]
        elif l.startswith('## '):
            l = '### ' + l[3:]
        elif l.strip() == '---':
            continue
        out.append(l)
    while out and not out[-1].strip():
        out.pop()
    return no, head, out + [''] + z, (nt, nl, nk)


def main():
    files = sorted(SRC.glob('*.md'))
    res = ['# 文学的同一性谱系', '']
    for f in files:
        no, head, body, stats = convert_chapter(f.read_text(encoding='utf-8'), f.name)
        if no in PARTS:
            res += [PARTS[no][0], '', PARTS[no][1], '']
        res += [head, ''] + body + ['']
        print('%-16s %-40s take=%d ledger=%d think=%d' % (f.name, head[:40], *stats))
    (HERE / 'src').mkdir(exist_ok=True)
    (HERE / 'src/full.md').write_text('\n'.join(res).rstrip() + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
