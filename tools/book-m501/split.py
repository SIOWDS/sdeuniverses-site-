#!/usr/bin/env python3
"""第 501 号：从全稿.md 切出 build.py 要的分卷稿（gen/front、gen/parts、gen/back）和 gen/meta.json。每次 make.sh 都重做，不要手改 gen/。
全稿约定：YAML 元数据 + `# 作者介绍/前言/导读/导论一..四/第N编/结一..四/参考书目/附录/附录一..六/后记`，章用 `## 第 N 章　题`，
章末 【带走的话】【小账】，编首 【编序】。
用法：python3 split.py --src /home/claude/huibuqu/build/全稿.md --out gen
"""
import argparse, json, re, shutil
from pathlib import Path


def parse_meta(text):
    assert text.startswith('---'), '全稿缺 YAML 元数据'
    end = text.index('\n---', 3)
    meta = {'statement': []}
    for ln in text[3:end].splitlines():
        k, sep, v = ln.partition(':')
        if not sep:
            continue
        k, v = k.strip(), v.strip()
        if k == 'statement':
            meta['statement'].append(v)
        elif k:
            meta[k] = v
    return meta, text[end + 4:].lstrip('\n')


def split_items(s):
    """一行里挤在一起的「- a- b」或「1. a2. b」拆开。"""
    if re.match(r'^-\s', s):
        parts = re.split(r'(?<=[。！？」）；])\s*-\s+', s)
        return [re.sub(r'^-\s+', '', x).strip() for x in parts if x.strip()]
    if re.match(r'^\d+\.\s', s):
        parts = re.split(r'(?<=[。！？」）；])\s*(?=\d+\.\s)', s)
        return [x.strip() for x in parts if x.strip()]
    return [s]


def endboxes(t):
    """【带走的话】【小账】【编序】 → build.py 认得的引用块／段落。"""
    out, lines, i = [], t.split('\n'), 0
    while i < len(lines):
        L = lines[i]
        if L.startswith('【带走的话】'):
            out += ['> **带走的话**', '> ' + L[len('【带走的话】'):].strip(), '']
            i += 1
            continue
        if L.startswith('【编序】'):
            out += [L[len('【编序】'):].strip(), '']
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '【', '>', '|')):
                out += [lines[i].strip(), '']
                i += 1
            continue
        if L.startswith('【小账】'):
            ledger, wonder, cur = [], [], None
            while i < len(lines) and (lines[i].startswith('【小账】') or not lines[i].strip()):
                if lines[i].startswith('【小账】'):
                    s = lines[i][len('【小账】'):].strip()
                    if re.fullmatch(r'\**想一想\**[：:]?', s):
                        cur = wonder
                    else:
                        for x in split_items(s):
                            (cur if cur is not None else ledger).append(x)
                i += 1
            if ledger:
                out += ['> **小账**'] + ['> ' + x for x in ledger] + ['']
            if wonder:
                out += ['> **想一想**'] + ['> ' + x for x in wonder] + ['']
            continue
        out.append(L)
        i += 1
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    raw = a.src.read_text().replace('\r', '')
    meta, body = parse_meta(raw)
    if a.out.exists():
        shutil.rmtree(a.out)
    for d in ('front', 'parts', 'back'):
        (a.out / d).mkdir(parents=True)
    # 切 h1
    h1s, cur = [], None
    for ln in body.split('\n'):
        if re.match(r'^# (?!#)', ln):
            cur = [ln[2:].strip(), []]
            h1s.append(cur)
        elif cur is not None:
            cur[1].append(ln)
    items = [(t, endboxes('\n'.join(b)).strip('\n')) for t, b in h1s]
    han = len(re.findall(r'[一-鿿]', raw))
    wan = int(han / 10000)

    # 出版信息 + 前置
    info = [('书名', '《%s——%s》' % (meta['title'], meta['subtitle'])), ('著者', meta['author']),
            ('执笔', meta.get('executor', '')), ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
            ('编号', '德麦国际专著第 %s 号' % meta['series_no']), ('ISBN', meta['isbn']), ('定价', meta['price']),
            ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', meta.get('edition', '')),
            ('完稿', meta.get('finished', ''))]
    rows = [kv for kv in info if kv[1]]
    head = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + '\n'.join('| %s | %s |' % kv for kv in rows) + '\n\n'
    head += '\n\n'.join(meta['statement']) + '\n\n' + meta.get('copyright', '版权所有　侵权必究') + '\n'
    front_groups, lun, parts, jie, tail = [], [], [], [], []
    for t, b in items:
        if re.match(r'^(作者介绍|前言|导读)', t):
            front_groups.append('## %s\n\n%s\n' % (t, b))
        elif t.startswith('导论'):
            lun.append((t, b))
        elif re.match(r'^第.+编', t):
            parts.append((t, b))
        elif re.match(r'^结[一二三四五六七八九十]', t):
            jie.append((t, b))
        else:
            tail.append((t, b))
    assert len(parts) == 9 and len(lun) == 4 and len(jie) == 4, (len(parts), len(lun), len(jie))
    (a.out / 'front' / '00-前置.md').write_text(head + '\n' + '\n'.join(front_groups))
    for k, (t, b) in enumerate(lun, 1):
        (a.out / 'front' / ('1%d-导论.md' % k)).write_text('# %s\n\n%s\n' % (t, b))
    for k, (t, b) in enumerate(parts, 1):
        (a.out / 'parts' / ('%02d.md' % k)).write_text('# %s\n\n%s\n' % (t, b))
    (a.out / 'back' / '09-结卷.md').write_text('\n\n'.join('# %s\n\n%s\n' % x for x in jie))
    # 后置：参考书目、附录（附录一..六降为 ##）、后记
    tl = []
    for t, b in tail:
        if re.match(r'^附录[一二三四五六七八九十]', t):
            tl.append('## %s\n\n%s\n' % (t, b))
        else:
            tl.append('# %s\n\n%s\n' % (t, b))
    (a.out / 'back' / '10-后置.md').write_text('\n\n'.join(tl))
    nch = len(re.findall(r'^## 第 \d+ 章', '\n'.join(p.read_text() for p in (a.out / 'parts').glob('*.md')), re.M))
    assert nch == 81, nch
    meta.update(wan=wan, han=han, nch=nch)
    (a.out / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print('split ok: han', han, 'wan', wan, 'chapters', nch)


if __name__ == '__main__':
    main()
