#!/usr/bin/env python3
"""临时合成器：把 /home/claude/551-jishu-tongyixing-puxi/chapters/ 下各稿件合成 src/full.md，并把各稿末〔待核〕清单收集到 待核总表.md。
（王德生/统稿人另行合成时可不用本脚本；本脚本只为试跑 convert.py。）
合成格式（convert.py 认的）：
  # 前言　T / # 导读　T / # 第N编　T / # 第N章　T / # 结语　T / # 附录一　T …… 一级标题
  章内节：## N.M T；节内小标题 ### T。前言、导读、附录、结语里的“### 一、…”降为 “## 一、…”。
切尾规则：每个文件以首个匹配 ^(#+ ?|\\*\\*)?(〔待核〕清单|附：|待核) 的行为界（任务书定的规则）；
  另补几个同类尾标：^#+ ?稿末(附件|附录)、^\\*\\*(字数|自数字数|自查表|本稿新造|拿不准)、^(字数自数|自数字数|自数：|自数（)，取其中最早者。
用法：python3 synth_full.py [--src DIR]
"""
import argparse, re
from pathlib import Path
HERE = Path(__file__).parent
SRC = Path('/home/claude/551-jishu-tongyixing-puxi/chapters')
CUT = re.compile(r'^(#+ ?|\*\*)?(〔待核〕清单|附：|待核)')
CUT2 = re.compile(r'^(#+ ?稿末(附件|附录)|\*\*(字数|自数字数|自查表|本稿新造|拿不准|建议)|(字数自数|自数字数|自数：|自数（)|#+ ?(字数|自查表|本稿新造|拿不准|建议))')
TAILSTOP = re.compile(r'^(#+ ?|\*\*)?(本稿新造案例清单|新造案例清单|自数|拿不准|建议|字数|自查表|附：)')

PARTS = [
 ('第一编', '缺口：统一性技术与“次等”的账', 1, 4),
 ('第二编', '土壤：六路径的 E', 5, 9),
 ('第三编', '谱位：六路径的光谱、家谱、乐谱与互底', 10, 14),
 ('第四编', '谱生：由 E 谱生成路径谱与显露谱', 15, 19),
 ('第五编', '我-AI 复合体的技术谱系', 20, 23),
 ('第六编', '六路径各一章：十三个行业', 24, 29),
 ('第七编', '职教的整体重建', 30, 33),
 ('第八编', '风险、边界与可错预言', 34, 36),
]


def cut(lines):
    """返回 (正文行, 尾部行)。"""
    k = len(lines)
    for i, l in enumerate(lines):
        if CUT.match(l) or CUT2.match(l):
            k = i; break
    body, tail = lines[:k], lines[k:]
    while body and body[-1].strip() in ('', '---'):
        body.pop()
    return body, tail


def todo_of(tail):
    """尾部里〔待核〕清单那一段。"""
    out, on = [], False
    for l in tail:
        if re.match(r'^(#+ ?|\*\*)?〔待核〕清单', l):
            on = True; out.append(l); continue
        if on and TAILSTOP.match(l):
            break
        if on:
            out.append(l)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, default=SRC); a = ap.parse_args()
    files = sorted(a.src.glob('*.md'))
    todo, chunks = [], []   # chunks: (kind, key, title, lines)
    for f in files:
        body, tail = cut(f.read_text(encoding='utf-8').splitlines())
        t = todo_of(tail)
        todo.append((f.name, t, len(tail)))
        # 按 "## " 顶层切段
        cur = None
        for l in body:
            m = re.match(r'^## (.+)$', l)
            if m:
                cur = [m[1].strip(), []]; chunks.append(cur)
            elif cur is not None:
                cur[1].append(l)
    def norm(title):
        # "第1章 题" -> "第1章　题"；"前言　T"/"导读　T"/"结语 T"/"附录一 T"
        m = re.match(r'^(第\d+章|前言|导读|结语|附录[一二三四])[\s　]+(.*)$', title)
        return '%s　%s' % (m[1], m[2]) if m else title
    def demote(lines, chapter):
        out = []
        for l in lines:
            if chapter and re.match(r'^### \d+\.\d+ ', l):
                out.append('## ' + l[4:])
            elif re.match(r'^### ', l):
                out.append('## ' + l[4:]) if not chapter else out.append('### ' + l[4:])
            elif re.match(r'^#### ', l):
                out.append('### ' + l[5:])
            else:
                out.append(l)
        return out
    book = ['# %s' % '全稿合成稿（临时，供试跑）', '']
    part_at = {p[2]: p for p in PARTS}
    for title, lines in chunks:
        t = norm(title)
        chap = re.match(r'^第(\d+)章', t)
        if chap and int(chap[1]) in part_at:
            p = part_at[int(chap[1])]
            book += ['# %s　%s' % (p[0], p[1]), '']
        while lines and not lines[-1].strip(): lines.pop()
        book += ['# ' + t, ''] + demote(lines, bool(chap)) + ['']
    (HERE / 'src').mkdir(exist_ok=True)
    (HERE / 'src/full.md').write_text('\n'.join(book).replace('\n\n\n', '\n\n') + '\n', encoding='utf-8')
    # 待核总表
    n = 0
    L = ['# 第 551 号 待核总表', '', '各稿件末尾〔待核〕清单原样收集（合成时从正文切掉）。以稿件当时状态为准；质检后请重跑 synth_full.py 或手工更新。', '']
    for name, t, nt in todo:
        L += ['## ' + name, '']
        t2 = [x for x in t if not re.match(r'^(#+ ?|\*\*)?〔待核〕清单', x)]
        L += (t2 if t2 else ['（无）']) + ['']
    (HERE / '待核总表.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('full.md', sum(len(c[1]) for c in chunks), 'lines;', len(chunks), 'chunks; 待核总表 written')


if __name__ == '__main__':
    main()
