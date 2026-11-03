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
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kafka-book/final')
CN = {c: i for i, c in enumerate('零一二三四五六七八九十')}
PARTS = {
    1: ('# 第一编　囚牢：统一性是什么', '这一编三章，先看那座牢。第 1 章写卡夫卡生活里的四座房子：法、父亲、保险局、店与工厂，它们说同一种话，给每个人派定一个对所有人都一样的位置。第 2 章写这些机构怎样还在运转，却已不再对任何一个具体的人说话。第 3 章站到出牢的岔路口：打破统一性之后，是剩下一族有来路的格子，还是什么都不剩。三章合起来是一句话：统一性先失语，后倒塌；出牢有两条路，只有一条通向自由。'),
    4: ('# 第二编　卡夫卡的自由：纠缠长出的谱系', '这一编六章，看卡夫卡走的那条路。第 4 章看「一天早晨」：转换不被叙述，只被发现。第 5、6 章细读《变形记》《审判》《城堡》，数出一格一格完整的同一性，看一人变、全家怎样跟着换格。第 7 章读《在法的门前》：门只为你一人而开，这自由是有形的。第 8、9 章讲他怎样写：保守的现实主义，忠实于正在开始发生的东西，不替它写结局。六章合起来是一句话：卡夫卡的自由，是纠缠打破统一性、长出同一性谱系的自由。'),
    10: ('# 第三编　卡夫卡为什么被看成荒诞', '这一编三章，问一个一百年的误会。第 10 章看小说里的人怎样追问罪名、任命、许可，现实怎样只用发生回答。第 11 章看小说外的读者：神学、精神分析、异化、存在主义、后现代，五把钥匙各开一处，没有一把开得了全部。第 12 章请加缪站到门前，给荒诞下一个新定义。三章合起来是一句话：卡夫卡并不荒诞，荒诞是用统一性去量同一性谱系时得到的读数。'),
    13: ('# 第四编　残雪的自由：真正的荒诞', '这一编五章，看另一条路。第 13、14 章读残雪的《灵魂的城堡》：她是离卡夫卡最近的读者，闻到了他的味道，却用「精神自由」给它命名，没有进入。第 15 章看她的小说怎样连一格一格的同一性也松开。第 16 章说明「打破一切」仍是统一性，只是站在反面。第 17 章下结论：卡夫卡的荒诞只是读数，残雪把荒诞写进了作品。五章合起来是一句话：连同一性都打破，不是自由，是乱来，是真正的荒诞。'),
    18: ('# 第五编　有形的自由', '这一编一章，把三条路并排摆开：统一性有秩序无自由，残雪与后现代有破碎无形，卡夫卡有纠缠、有谱系、有形。最后给出读卡夫卡的几个问题，带到结语。'),
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
        qs = [x for x in think if x.strip()]
        out += ['', '### ◆ 想一想', '']
        for q in qs:
            out += [q, '']
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
        m = re.match(r'^#\s*(序章|前言|结语)[\s　]*(.*)$', h)
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
    res = ['# 卡夫卡并不荒诞', '']
    for f in files:
        no, head, body, stats = convert_chapter(f.read_text(encoding='utf-8'), f.name)
        if no in PARTS:
            res += [PARTS[no][0], '', PARTS[no][1], '']
        res += [head, ''] + body + ['']
        print('%-16s %-40s take=%d ledger=%d think=%d' % (f.name, head[:40], *stats))
    extra = HERE / 'back_extra.md'
    if extra.exists():
        res += [''] + extra.read_text(encoding='utf-8').strip().splitlines()
    (HERE / 'src').mkdir(exist_ok=True)
    (HERE / 'src/full.md').write_text('\n'.join(res).rstrip() + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
