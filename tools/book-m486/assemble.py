#!/usr/bin/env python3
"""第 486 号：把 /home/claude/zz486/ch 下的分章稿装成 build.py 要的分卷稿（front/parts/back），并出一份全稿 md。
用法：python3 assemble.py --src /home/claude/zz486/ch --full /home/claude/b486-full.md
"""
import argparse, json, re
from pathlib import Path

HERE = Path(__file__).parent


def endboxes(t):
    """【带走的话】【小账】**想一想** → build.py 认得的引用块。"""
    out, lines, i = [], t.split('\n'), 0
    while i < len(lines):
        L = lines[i]
        if L.startswith('【带走的话】'):
            out += ['> **带走的话**', '> ' + L[len('【带走的话】'):].strip(), '']
            i += 1; continue
        if L.startswith('【小账】'):
            items = []
            while i < len(lines) and (lines[i].startswith('【小账】') or not lines[i].strip()):
                if lines[i].startswith('【小账】'):
                    s = lines[i][len('【小账】'):].strip()
                    m = re.match(r'^([^：]{2,28})：(.*)$', s)
                    items.append('%s？——%s' % (m[1].rstrip('？'), m[2]) if m else s)
                i += 1
            out += ['> **小账**'] + ['> ' + x for x in items] + ['']
            continue
        m = re.match(r'^\*\*想一想\*\*[：:]?\s*(.*)$', L)
        if m:
            items = [m[1]] if m[1].strip() else []
            i += 1
            while i < len(lines) and not lines[i].startswith('#'):
                if lines[i].strip():
                    items.append(lines[i].strip())
                i += 1
            out += ['> **想一想**'] + ['> ' + x for x in items] + ['']
            continue
        out.append(L); i += 1
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True); ap.add_argument('--full', type=Path, required=True)
    a = ap.parse_args(); S = a.src
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob('*.md'):
            f.unlink()
    head = (HERE / 'front_head.md').read_text()
    fr = (S / 'front.md').read_text()
    fr = re.sub(r'^# ', '## ', fr, flags=re.M)
    (HERE / 'front' / '00-前置.md').write_text(head.rstrip() + '\n\n' + endboxes(fr).strip() + '\n')
    (HERE / 'front' / '01-导论.md').write_text(endboxes((S / 'daolun.md').read_text()).strip() + '\n')
    parts = json.loads((HERE / 'parts.json').read_text())
    intros = json.loads((HERE / 'intros.json').read_text())
    chs = {}
    for n in range(1, 45):
        t = (S / ('ch%02d.md' % n)).read_text().strip()
        assert t.startswith('## 第 %d 章　' % n), (n, t[:30])
        chs[n] = endboxes(t)
    for idx, (p, title, rng) in enumerate(parts, 1):
        body = '\n\n'.join(chs[n] for n in rng)
        (HERE / 'parts' / ('%02d-%s.md' % (idx, p))).write_text('# %s　%s\n\n' % (p, title) + '\n\n'.join(intros[idx - 1]) + '\n\n' + body + '\n')
    bk = (S / 'back.md').read_text()
    k = bk.index('\n# 后记')
    (HERE / 'back' / '09-结语.md').write_text(endboxes(bk[:k]).strip() + '\n')
    houji = bk[k + 1:].strip()
    hz = (S / 'houzhi.md').read_text()
    hz = hz[:hz.index('\n# 后记')].strip()
    yz = (S / 'yinwen.md').read_text().strip() if (S / 'yinwen.md').exists() else '（统稿后由脚本生成）'
    hz = hz.replace('（统稿后由脚本生成）', yz)
    (HERE / 'back' / '10-后置.md').write_text(hz + '\n\n' + houji + '\n')
    full = '\n\n'.join(p.read_text() for p in [HERE / 'front' / '00-前置.md', HERE / 'front' / '01-导论.md']
                       + sorted((HERE / 'parts').glob('*.md')) + [HERE / 'back' / '09-结语.md', HERE / 'back' / '10-后置.md'])
    wan = round(len(''.join(full.split())) / 10000)
    f0 = HERE / 'front' / '00-前置.md'
    f0.write_text(f0.read_text().replace('__WAN__', str(wan)))
    full = full.replace('__WAN__', str(wan))
    a.full.write_text(full)
    han = len(re.findall(r'[一-鿿]', full))
    print('ok', 'han', han, 'chars', len(''.join(full.split())))


if __name__ == '__main__':
    main()
