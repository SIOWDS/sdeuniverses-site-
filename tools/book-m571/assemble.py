#!/usr/bin/env python3
"""第 571 号《医患复合体状态发生学》：把 /home/claude/yihuan/ 下十个分卷稿（01-前言导读导论 … 10-结语附录后记）按顺序合成
src/full.md（convert.py 认的格式）。只改格式，不动正文一个字；书稿目录只读。

书稿原样已是「# 前言／# 导读／# 导论」「# 第X编　T」＋编序、「## 第 N 章　T」「### ◆ 一、T」「#### T」「# 结语　T」
「# 参考书目」「# 附录」（### 附录一…）「# 后记」，这里只做：
  · 章末装置统一成 build.py 认的引用块：
      「> **带走的话**：X」                       → 「> **带走的话**」框；
      「**小账**」「**两行小账**」＋下面的段落，或「> **小账**」＋「> 行」 → 「> **小账**」框，一行一条；
      「**想一想**」＋下面的段落（到下一个标题为止），或「> **想一想**」＋「> 行」 → 「> **想一想**」框，一问一条；
  · 两行正文紧挨着（中间没有空行，又不是列表、表格、引用、标题）时补一个空行，让它们各成一段——
    Markdown 会把紧挨的两行并成一段，这里照稿面的分行排（如「第一行：…／第二行：…」）；
  · 去掉 ---。
末了逐字核对：去掉 Markdown 记号、空白与「带走的话／小账／两行小账／想一想」标签后，合成稿与原稿正文完全一致，否则报错。
用法：python3 tools/book-m571/assemble.py [书稿目录]
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else M.MS_DIR)
STRUCT = re.compile(r'^(\||\d+\. |- |\* |#|>|```)')
LAB_TAKE = re.compile(r'^>\s*\*\*带走的话\*\*\s*[：:]\s*(.*)$')
LAB_LEDGER = re.compile(r'^(?:>\s*)?\*\*(?:两行)?小账\*\*\s*$')
LAB_THINK = re.compile(r'^(?:>\s*)?\*\*想一想\*\*\s*$')


def split_soft(lines):
    out = []
    for i, l in enumerate(lines):
        out.append(l)
        if i + 1 < len(lines):
            n = lines[i + 1]
            if l.strip() and n.strip() and not STRUCT.match(l.strip()) and not STRUCT.match(n.strip()):
                out.append('')
    return out


def grab(lines, i):
    """从 i 起收一个装置的条目：引用块（> 行）或普通段落，到下一个装置标签、标题或非引用块为止。返回 (条目, 新下标)。"""
    items, n = [], len(lines)
    quoted = None
    while i < n:
        l = lines[i].rstrip()
        s = l.strip()
        if not s:
            if quoted:            # 引用块之后的空行：看下一非空行是否还是引用
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and lines[j].lstrip().startswith('>') and not (LAB_LEDGER.match(lines[j].strip()) or LAB_THINK.match(lines[j].strip()) or LAB_TAKE.match(lines[j].strip())):
                    i = j; continue
                return items, i
            i += 1; continue
        if s.startswith('#') or LAB_LEDGER.match(s) or LAB_THINK.match(s) or LAB_TAKE.match(s):
            return items, i
        if s.startswith('>'):
            if quoted is False:
                return items, i
            quoted = True
            t = re.sub(r'^>\s?', '', s).strip()
            if t:
                items.append(t)
        else:
            if quoted:
                return items, i
            quoted = False
            items.append(s)
        i += 1
    return items, i


def convert(text):
    lines = text.splitlines()
    out, i, n = [], 0, len(lines)
    stats = {'take': 0, 'ledger': 0, 'think': 0}
    while i < n:
        l = lines[i].rstrip()
        s = l.strip()
        m = LAB_TAKE.match(s)
        if m:
            out += ['> **带走的话**', '>', '> ' + m.group(1).strip(), '']
            stats['take'] += 1; i += 1; continue
        if LAB_LEDGER.match(s) or LAB_THINK.match(s):
            kind = '小账' if LAB_LEDGER.match(s) else '想一想'
            items, i = grab(lines, i + 1)
            assert items, 'empty %s near line %d' % (kind, i)
            out.append('> **%s**' % kind)
            for it in items:
                out += ['>', '> ' + it]
            out.append('')
            stats['ledger' if kind == '小账' else 'think'] += 1
            continue
        if s == '---':
            i += 1; continue
        out.append(l); i += 1
    return out, stats


def norm(text):
    """逐字核对用：去掉 Markdown 记号、空白与章末标签。"""
    keep = []
    for l in text.splitlines():
        s = re.sub(r'^[>\s]*', '', l).strip()
        if re.fullmatch(r'(\*\*)?(两行)?小账(\*\*)?|(\*\*)?想一想(\*\*)?|(\*\*)?带走的话(\*\*)?|---', s):
            continue
        s = re.sub(r'^\*\*带走的话\*\*\s*[：:]', '', s)
        keep.append(s)
    t = ''.join(keep)
    return re.sub(r'[\s#*>]', '', t)


def main():
    res = ['# ' + M.TITLE, '']
    src_all = []
    for name in M.MS_FILES:
        f = SRC / name
        txt = f.read_text(encoding='utf-8')
        src_all.append(txt)
        body, st = convert(txt)
        body = split_soft(body)
        while body and not body[-1].strip():
            body.pop()
        res += body + ['']
        heads = [x for x in body if re.match(r'^#{1,2} ', x)]
        print('%-18s %-34s take=%d ledger=%d think=%d' % (name, (heads[0] if heads else '')[:34], st['take'], st['ledger'], st['think']))
    out = '\n'.join(res).rstrip() + '\n'
    out = re.sub(r'\n{3,}', '\n\n', out)
    (HERE / 'src').mkdir(exist_ok=True)
    (HERE / 'src/full.md').write_text(out, encoding='utf-8')
    a, b = norm('\n'.join(src_all)), norm(out.split('\n', 2)[2])
    if a != b:
        k = next(k for k in range(min(len(a), len(b))) if a[k] != b[k])
        raise SystemExit('正文核对不一致，位置 %d：\n原稿 %s\n合成 %s' % (k, a[max(0, k - 40):k + 40], b[max(0, k - 40):k + 40]))
    full = out
    print('ok full.md: chapters', len(re.findall(r'^## 第 \d+ 章　', full, re.M)), 'parts', len(re.findall(r'^# 第.编　', full, re.M)),
          'takeaway', full.count('> **带走的话**'), 'ledger', full.count('> **小账**'), 'think', full.count('> **想一想**'),
          '｜正文逐字核对一致（%d 字符）' % len(a))


if __name__ == '__main__':
    main()
