#!/usr/bin/env python3
"""第 572 号《K线人生——跃迁无法设计，只能接住》：把 /home/claude/klife/book/ 下的定稿（序言、第1—27章、尾声、附录AC/B/D）
按顺序合成 src/full.md（convert.py 认的格式）。只改格式，不动正文一个字；书稿目录只读。

书稿原样：每章「# 第N章　T」，章内「## T」，个别「### T」，章末「## 本章出处」；序言「# 序言　T」，尾声「# 尾声　T」（末节「## 本篇出处」），
附录AC.md 里先「# 附录A　T」后「# 附录C　T」（中间一条 ---），附录B.md、附录D.md 各一件。这里只做：
  · 序言 → 「# 前言　T」（前置）；序言、尾声里的「## T」→「### ◆ T」，「## 本章出处／本篇出处」→「### 本章出处／本篇出处」（书目体例）；
  · 八编：在第 1、4、8、11、14、19、22、25 章之前插「# 第X编　T」＋编首语（编序），编名与编首语逐字取自
    /home/claude/klife/run/assemble.py 的 parts 与 INTROS（这里用 ast 读出，不另抄一份）；
  · 章：「# 第N章　T」→「## 第 N 章　T」，「## T」→「### ◆ T」，「### T」→「#### T」，「## 本章出处」→「### 本章出处」；
  · 第 26 章：在「本章出处」之前插「### ◆ 十张缠图」与十张图（![名](charts/<slug>.jpg)），图由 publish 前的 charts 步骤压成 jpg；
  · 尾声 → 「# 尾声　T」；附录 → 「# 附录」下「## 附录A／B／C／D　T」（按 A、B、C、D 排），附录内「## T」→「### ◆ T」；
  · 两行正文紧挨着（中间没有空行，又不是列表、表格、标题）时补一个空行，让它们各成一段；去掉 ---。
末了逐字核对：去掉 Markdown 记号、◆ 与空白后，合成稿（除去插入的编名、编首语、十张缠图）与原稿正文完全一致（序言标题「序言」记作「前言」，
附录按 A、B、C、D 排），编首语与 run/assemble.py 逐字一致，否则报错。
用法：python3 tools/book-m572/assemble.py [书稿目录]
"""
import ast
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else M.MS_DIR)
RUN_ASM = Path('/home/claude/klife/run/assemble.py')
STRUCT = re.compile(r'^(\||\d+\. |- |\* |#|>|```|!\[)')
CN = '零一二三四五六七八九十'


def run_consts():
    tree = ast.parse(RUN_ASM.read_text(encoding='utf-8'))
    got = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('parts', 'INTROS'):
            got[node.targets[0].id] = ast.literal_eval(node.value)
    return got['parts'], got['INTROS']


def split_soft(lines):
    out = []
    for i, l in enumerate(lines):
        out.append(l)
        if i + 1 < len(lines):
            n = lines[i + 1]
            if l.strip() and n.strip() and not STRUCT.match(l.strip()) and not STRUCT.match(n.strip()):
                out.append('')
    return out


def demote(text, chapter=False):
    """章／序言／尾声／附录内的小节降级；首行（# 标题）由调用方处理。"""
    out = []
    for l in text.splitlines():
        if l.strip() == '---':
            continue
        m = re.match(r'^(#{2,3}) (.*)$', l)
        if m:
            t = m[2].strip()
            if m[1] == '##':
                if re.fullmatch(r'本(章|篇)出处', t):
                    l = '### ' + t
                else:
                    l = '### ◆ ' + t
            else:
                l = '#### ' + t
        out.append(l.rstrip())
    return out


def tidy(lines):
    lines = split_soft(lines)
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def norm(text):
    """逐字核对用：去掉 Markdown 记号、◆、--- 与空白。"""
    t = '\n'.join(l for l in text.splitlines() if l.strip() != '---')
    return re.sub(r'[\s#*>◆]', '', t)


def main():
    parts, intros = run_consts()
    assert {k: v for k, v in parts.items()} == M.PARTS, '编名与 meta.PARTS 不一致'
    txt = {f: (SRC / f).read_text(encoding='utf-8') for f in M.MS_FILES}
    res = ['# ' + M.TITLE, '']
    # 前言（序言）
    pre = txt['00_序言.md'].strip().splitlines()
    m = re.match(r'^# 序言　(.*)$', pre[0])
    assert m, pre[0]
    res += ['# 前言　' + m[1], ''] + tidy(demote('\n'.join(pre[1:]))) + ['']
    src_parts = ['# 前言　' + m[1] + '\n' + '\n'.join(pre[1:])]
    ins = []   # 插入的版式文字（编名、编首语、十张缠图），核对时扣除
    for n in range(1, 28):
        f = '第%02d章.md' % n
        t = txt[f].strip().splitlines()
        cm = re.match(r'^# 第(\d+)章　(.*)$', t[0])
        assert cm and int(cm[1]) == n, t[0]
        if n in parts:
            pl = ['# ' + parts[n], '', intros[n], '']
            res += pl; ins.append(pl)
        body = tidy(demote('\n'.join(t[1:]), chapter=True))
        if n == 26:
            k = body.index('### 本章出处')
            fig = ['### ◆ 十张缠图', ''] + sum((['![%s](%s/%s.jpg)' % (nm, M.CHART_URL, sl), ''] for nm, sl in M.CHARTS), [])
            body = body[:k] + fig + body[k:]
            ins.append(fig)
        res += ['## 第 %d 章　%s' % (n, cm[2]), ''] + body + ['']
        src_parts.append(txt[f])
    # 尾声
    ep = txt['99_尾声.md'].strip().splitlines()
    assert ep[0].startswith('# 尾声　'), ep[0]
    res += [ep[0], ''] + tidy(demote('\n'.join(ep[1:]))) + ['']
    src_parts.append(txt['99_尾声.md'])
    # 附录：A、B、C、D
    ac = txt['附录AC.md']
    i = ac.index('# 附录C　')
    apx = {'A': ac[:i], 'B': txt['附录B.md'], 'C': ac[i:], 'D': txt['附录D.md']}
    res += ['# 附录', '']
    for k in 'ABCD':
        a = apx[k].strip().splitlines()
        assert a[0].startswith('# 附录%s　' % k), a[0]
        res += ['#' + a[0], ''] + tidy(demote('\n'.join(a[1:]))) + ['']
        src_parts.append(apx[k])
    ins.append(['# 附录'])
    out = '\n'.join(res).rstrip() + '\n'
    out = re.sub(r'\n{3,}', '\n\n', out)
    (HERE / 'src').mkdir(exist_ok=True)
    (HERE / 'src/full.md').write_text(out, encoding='utf-8')
    # 逐字核对：扣掉插入的版式文字（按整行块扣，每块必须在合成稿里原样出现）与书名行
    chk = out.split('\n', 2)[2]
    for blk in ins:
        s_ = '\n'.join(blk).strip('\n')
        assert s_ in chk, s_[:40]
        chk = chk.replace(s_, '', 1)
    chk_n = norm(chk)
    a, b = norm('\n'.join(src_parts)), chk_n
    if a != b:
        k = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        raise SystemExit('正文核对不一致，位置 %d：\n原稿 %s\n合成 %s' % (k, a[max(0, k - 40):k + 40], b[max(0, k - 40):k + 40]))
    print('ok full.md: chapters', len(re.findall(r'^## 第 \d+ 章　', out, re.M)), 'parts', len(re.findall(r'^# 第.编　', out, re.M)),
          'figures', len(re.findall(r'^!\[', out, re.M)), '｜正文逐字核对一致（%d 字符）' % len(a))


if __name__ == '__main__':
    main()
