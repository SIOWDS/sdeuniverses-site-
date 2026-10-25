import re, json
def chapter_md(files, n):
    for f in files:
        s = open(f).read()
        m = re.search(r'^## 第 %d 章　.*?(?=^## |\Z)' % n, s, re.M | re.S)
        if m: return m.group(0)
def to_plain(md):
    lines = md.strip().split('\n')
    title = re.sub(r'^## 第 (\d+) 章', r'第\1章', lines[0])
    out = [title]
    body = '\n'.join(lines[1:])
    blocks = [b for b in re.split(r'\n\s*\n', body) if b.strip()]
    res = []
    for bl in blocks:
        bl = bl.strip()
        if bl.startswith('### '):
            res.append(bl[4:]); continue
        if bl.startswith('>'):
            ls = [re.sub(r'^> ?', '', x) for x in bl.split('\n')]
            ls = [x for x in ls if x.strip()]
            head = ls[0]
            if head == '**带走的话**':
                res.append('带走的话： ' + ' '.join(ls[1:]).replace('**', ''))
            elif head in ('**两行小账**', '**小账**'):
                res.append(head.strip('*') + '：\n' + '\n'.join('- ' + x for x in ls[1:]))
            elif head == '**想一想**':
                res.append('想一想：\n' + '\n'.join('%d. %s' % (i + 1, x) for i, x in enumerate(ls[1:])))
            elif head.startswith('**这一章的问题**'):
                pass
            else:
                res.append('\n'.join(ls))
            continue
        res.append(bl)
    txt = '\n\n'.join(out + res)
    txt = txt.replace('**', '').replace('“', '"').replace('”', '"')
    return txt
