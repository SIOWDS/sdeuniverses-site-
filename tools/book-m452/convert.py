#!/usr/bin/env python3
"""三审定稿（sanshen/r3 或指定目录）→ 第 409 号工具链方言（front/ parts/ back/）。
用法：python3 convert.py [源目录]   默认 ../sanshen/r3
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / 'sanshen/r3'
CN = '零一二三四五六七八九十'


def cnum(n):
    if n <= 10:
        return CN[n]
    if n < 20:
        return '十' + (CN[n - 10] if n > 10 else '')
    return CN[n // 10] + '十' + (CN[n % 10] if n % 10 else '')


def smart(s):
    """残留半角直引号 → 弯引号（逐行成对）。"""
    out = []
    for line in s.splitlines():
        if '"' in line:
            k = 0
            buf = []
            for ch in line:
                if ch == '"':
                    buf.append('“' if k % 2 == 0 else '”'); k += 1
                else:
                    buf.append(ch)
            line = ''.join(buf)
        out.append(line)
    return '\n'.join(out) + '\n'


def sections(text):
    """### N.M 题 / ### 第一节　题 → ### ◆ 一、题"""
    def rep(m):
        t = m[1].strip()
        m2 = re.match(r'^\d+\.(\d+)\s+(.*)$', t)
        if m2:
            return '### ◆ %s、%s' % (cnum(int(m2[1])), m2[2].strip())
        m3 = re.match(r'^第([一二三四五六七八九十]+)节[　 ]+(.*)$', t)
        if m3:
            return '### ◆ %s、%s' % (m3[1], m3[2].strip())
        return '### ◆ ' + t.lstrip('◆ ')
    return re.sub(r'^### (.+)$', rep, text, flags=re.M)


def chapter_ends(text):
    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        m = re.fullmatch(r'\*\*判词[：:](.+?)\*\*\s*', l.strip())
        if m:
            out += ['> **判词**', '> ' + m[1].strip()]
            i += 1; continue
        m = re.fullmatch(r'>\s*\*\*(?:本章)?随身三问\*\*[：:。]?\s*(.+)', l.strip())
        if not m:
            m = re.fullmatch(r'>?\s*(?:\*\*)?(?:本章)?随身三问[：:。](?:\*\*)?\s*(.+)', l.strip())
        if m and '随身三问' in l[:16]:
            out += ['> **随身三问**', '> ' + m[1].strip()]
            i += 1; continue
        if l.strip() in ('**一页账**', '> **一页账**', '**一页账：**'):
            paras, j = [], i + 1
            while j < len(lines) and not lines[j].startswith('#') and lines[j].strip() != '---':
                t = lines[j].strip()
                if t.startswith('> '):
                    t = t[2:]
                paras.append(t)
                j += 1
            body = [p for p in paras if p]
            out.append('> **一页账**')
            for k, p in enumerate(body):
                out.append('> ' + p)
                if k < len(body) - 1:
                    out.append('>')
            out.append('')
            i = j; continue
        out.append(l)
        i += 1
    return '\n'.join(out) + '\n'


def main():
    for d in ('front', 'parts', 'back'):
        (ROOT / d).mkdir(exist_ok=True)
    intros = json.loads((ROOT / 'part_intros.json').read_text())

    # 前言＋导论
    t = (SRC / '00-前言导论.md').read_text()
    k = t.index('\n# 导论')
    qian, dao = t[:k], t[k + 1:]
    qian = sections(qian).replace('# 前言', '## 前言', 1)
    fm = (ROOT / 'front_matter.md').read_text().rstrip() + '\n\n' + qian
    (ROOT / 'front/00-前置.md').write_text(smart(fm))
    (ROOT / 'front/01-导论.md').write_text(smart(chapter_ends(sections(dao))))

    # 各编
    for n in range(1, 8):
        f = next(SRC.glob('%02d-*.md' % n))
        t = chapter_ends(sections(f.read_text()))
        lines = t.splitlines()
        title = lines[0]
        name = re.match(r'^# (第.编)', title)[1]
        # 编首到第一章之间有没有导语段落
        first_ch = next(i for i, l in enumerate(lines) if l.startswith('## '))
        has_intro = any(l.strip() and not l.startswith('#') for l in lines[1:first_ch])
        if not has_intro and name in intros:
            lines = [title, ''] + sum([[p, ''] for p in intros[name]], []) + lines[first_ch:]
        (ROOT / 'parts' / f.name).write_text(smart('\n'.join(lines) + '\n'))

    # 结语、附录
    t = (SRC / '08-结语附录.md').read_text()
    k = t.index('\n# 附录')
    jie, fu = t[:k], t[k + 1:]
    (ROOT / 'back/09-结语.md').write_text(smart(chapter_ends(sections(jie))))
    back = (ROOT / 'bib.md').read_text().rstrip() + '\n\n' + fu.rstrip() + '\n\n' + (ROOT / 'houji.md').read_text()
    (ROOT / 'back/10-后置.md').write_text(smart(back))
    print('converted from', SRC)


if __name__ == '__main__':
    main()
