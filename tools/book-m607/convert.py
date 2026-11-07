#!/usr/bin/env python3
"""第 607 号《SDE思想大全》：把源稿目录（总导论 intro_anchor.md、总合论 conclusion.md、115 章 chNNN.md，每件以 <!-- END_BODY --> 分隔正文与来源注）
转成统稿 book.md（# 作者介绍 / # 总导论　… / # 第N编　… / ## 第 N 章　… / ◆ 一、… / # 总合论　…）与 notes.json（各件来源注）、han.json、structure.json。
只改标题体例，不动正文文字：「## 一、」与「## 第一节 」统一成「◆ 一、」；章题「# 第N章 题」→「## 第 N 章　题」。
可重跑（源稿定稿后重跑即可）：
  python3 tools/book-m607/convert.py <源稿目录> [--toc tools/book-m607/toc.json]
"""
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
END = '<!-- END_BODY -->'
CN = '零一二三四五六七八九十'
HAN = re.compile(r'[㐀-䶿一-鿿]')


def cn(n):
    if n <= 10:
        return CN[n]
    if n < 20:
        return '十' + CN[n - 10]
    t, o = divmod(n, 10)
    return CN[t] + '十' + (CN[o] if o else '')


def cn2int(s):
    if '十' in s:
        a, _, b = s.partition('十')
        return (CN.index(a) if a else 1) * 10 + (CN.index(b) if b else 0)
    return CN.index(s)


def han_rule(body):
    """作者的 count_han 口径：仅正文段落汉字，不含标题、表格、代码、注释行。"""
    tot, fence = 0, False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith('```'):
            fence = not fence; continue
        if fence or not s or s.startswith(('#', '|', '<!--')):
            continue
        tot += len(HAN.findall(s))
    return tot


def split_notes(tail):
    """来源注：返回 {'title': 标题或空, 'paras': [...]}；标题形态不一（## 来源注／## 原典与说明／无标题）。"""
    title, paras = '', []
    for l in tail.split('\n'):
        if not l.strip():
            continue
        m = re.match(r'^## (.*)$', l)
        if m and not title and not paras:
            title = m[1].strip(); continue
        paras.append(l.rstrip())
    return {'title': title, 'paras': paras}


def sections(body_lines, numbered=True):
    """## 一、x ／ ## 第一节 x → ◆ 一、x；无编号的小节（总导论）→ ◆ x。"""
    out, seq = [], []
    for l in body_lines:
        m = re.match(r'^## (.*)$', l)
        if not m:
            out.append(l); continue
        t = m[1].strip()
        m1 = re.match(r'^([一二三四五六七八九十]+)、\s*(.*)$', t)
        m2 = re.match(r'^第([一二三四五六七八九十]+)节\s*(.*)$', t)
        if m1:
            out.append('◆ %s、%s' % (m1[1], m1[2])); seq.append(m1[1])
        elif m2:
            out.append('◆ %s、%s' % (m2[1], m2[2])); seq.append(m2[1])
        else:
            out.append('◆ ' + t)
    return out, seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', type=Path)
    ap.add_argument('--toc', type=Path, default=HERE / 'toc.json')
    a = ap.parse_args()
    toc = json.loads(a.toc.read_text(encoding='utf-8'))
    ents = toc['entries']
    parts = [e for e in ents if e['kind'] == 'part']
    chap_part = {}
    for p in parts:
        for c in p['chapters']:
            chap_part[c] = p
    notes, han_rule_tot, han_all_tot, warnings = {}, 0, 0, []
    chapters_found = 0

    def load(stem):
        t = (a.src / (stem + '.md')).read_text(encoding='utf-8')
        assert END in t, stem + ' 缺 END_BODY'
        body, _, tail = t.partition(END)
        return body.strip('\n'), tail

    def count(body):
        nonlocal han_rule_tot, han_all_tot
        han_rule_tot += han_rule(body)
        han_all_tot += len(HAN.findall(body))

    out = [(HERE / 'author_intro.md').read_text(encoding='utf-8').rstrip('\n'), '']
    # ── 总导论 ──
    body, tail = load('intro_anchor')
    count(body)
    ls = body.split('\n')
    m = re.match(r'^# (总导论)[ 　]+(.*)$', ls[0]); assert m, ls[0]
    sec, _ = sections(ls[1:])
    out += ['# %s　%s' % (m[1], m[2].strip())] + sec + ['']
    notes['intro_anchor'] = split_notes(tail)
    # ── 各编各章 ──
    gi = json.loads((HERE / 'part_intro.json').read_text(encoding='utf-8')) if (HERE / 'part_intro.json').exists() else {}
    dom_idx = {}
    last_part = None
    for n in range(1, 116):
        p = chap_part[n]
        if p is not last_part:
            last_part = p
            tt = p['title'].replace(' ', '　', 1)
            pn = p['part']
            dom_idx.setdefault(p['domain'], []).append(pn)
            chs = p['chapters']
            intro = gi.get(str(pn)) or ('本编属本书「%s」部分，共 %d 章，自第 %d 章至第 %d 章。' % (p['domain'], len(chs), chs[0], chs[-1]))
            out += ['# ' + tt, '**编序**', intro, '']
        stem = 'ch%03d' % n
        body, tail = load(stem)
        count(body)
        ls = body.split('\n')
        m = re.match(r'^# 第(\d+)章[ 　]+(.*)$', ls[0]); assert m and int(m[1]) == n, (stem, ls[0])
        te = [e for e in ents if e.get('chapter') == n][0]
        norm = lambda x: re.sub(r'[\s、，,：:；;]+', '', x)   # toc.json 标题里标点已被空格替代
        if norm('第%d章%s' % (n, m[2])) != norm(te['title']):
            warnings.append('%s 章题与 toc 不一致：%s | %s' % (stem, ls[0], te['title']))
        sec, seq = sections(ls[1:])
        exp = [CN[i + 1] for i in range(len(seq))]
        if seq != exp:
            warnings.append('%s 小节序号不连续：%s' % (stem, seq))
        while sec and not sec[-1].strip():
            sec.pop()
        out += ['## 第 %d 章　%s' % (n, m[2].strip()), ''] + sec + ['']
        notes[stem] = split_notes(tail)
        chapters_found += 1
    # ── 总合论 ──
    body, tail = load('conclusion')
    count(body)
    ls = body.split('\n')
    m = re.match(r'^# (总合论)[ 　]+(.*)$', ls[0]); assert m, ls[0]
    sec, _ = sections(ls[1:])
    out += ['# %s　%s' % (m[1], m[2].strip())] + sec + ['']
    notes['conclusion'] = split_notes(tail)
    book = '\n'.join(out)
    book = re.sub(r'\n{3,}', '\n\n', book).rstrip('\n') + '\n'
    (HERE / 'book.md').write_text(book, encoding='utf-8')
    (HERE / 'notes.json').write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
    groups = [{'name': d, 'parts': ps} for d, ps in dom_idx.items()]
    struct = {'groups': groups, 'parts': [{'n': p['part'], 'title': p['title'], 'domain': p['domain'], 'chapters': p['chapters']} for p in parts]}
    (HERE / 'structure.json').write_text(json.dumps(struct, ensure_ascii=False, indent=1), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': han_rule_tot, 'body_all_before_end_body': han_all_tot, 'chapters': chapters_found,
                                               'rule': 'body＝作者 count_han 口径（END_BODY 之前、不含标题与表格）；body_all＝END_BODY 之前全部汉字'}, ensure_ascii=False))
    print('chapters', chapters_found, 'parts', len(parts), 'han(rule)', han_rule_tot, 'han(all before END)', han_all_tot)
    for w in warnings:
        print('WARN', w)


if __name__ == '__main__':
    main()
