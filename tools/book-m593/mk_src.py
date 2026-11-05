#!/usr/bin/env python3
"""把定稿目录 final/（b00 导论、b01–b60 各章、b61 结语）装成 convert.py 认的 src/，并生成书末参考文献。
正文一字不动。只动各章末尾的“参考：”块：标题改成“### 本章参考文献”，每条统一为一行一条、去掉行首“- ”、年份写法统一成 (年份)。
书末参考文献：汇总各章条目，去重，按作者排序；分西文、中文、站内专著三组。站内专著的著者与书名以 catalog 为准，对不上的写入 refs_report.json。
用法：python3 mk_src.py <定稿目录>"""
import json, re, sys, unicodedata
from pathlib import Path
HERE = Path(__file__).parent
B = Path(sys.argv[1]); OUT = HERE / 'src'
OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.md'):
    f.unlink()
NCH = 60
REPO = HERE.resolve().parents[1]
CAT = {x['number']: x for x in json.loads((REPO / 'public/books/catalog.json').read_text())['books'] if isinstance(x.get('number'), int)}
SITE_RE = re.compile(r'第\s*(\d+)\s*[号卷]\s*(?:（[^）]*著）)?\s*《([^》]+)》')


def norm_line(x):
    x = x.strip()
    x = re.sub(r'^- +', '', x)
    # “Author. 2000. Title.” → “Author (2000). Title.”（只动西文条目）
    if re.match(r'^[A-Za-z]', x) and not re.search(r'\(\d{4}', x):
        m = re.match(r'^(.+?)\.? ((?:19|20)\d{2}[a-z]?)\. (.+)$', x)
        if m:
            x = '%s. (%s). %s' % (m[1].rstrip('.'), m[2], m[3])
    if re.match(r'^[A-Za-z]', x) and x.endswith('。') and not re.search(r'[\u4e00-\u9fff]', x):
        x = x[:-1] + '.'
    return x


def split_refs(text):
    m = list(re.finditer(r'^参考[：:]\s*$', text, re.M))
    if not m:
        return text.strip(), []
    assert len(m) == 1
    return text[:m[0].start()].strip(), [norm_line(l) for l in text[m[0].end():].strip().split('\n') if l.strip()]


def key_of(x):
    """去重键：首作者姓＋年份＋题名前若干字母。"""
    t = unicodedata.normalize('NFKD', x).lower()
    y = re.search(r'\((\d{4}[a-z]?)', t) or re.search(r'\b((?:19|20)\d{2}[a-z]?)\b', t)
    y = y[1] if y else ''
    head = re.match(r'[^,.(]+', t)
    a = re.sub(r'[^a-z一-鿿]', '', head[0]) if head else ''
    after = t[t.index(y) + len(y):] if y and y in t else t
    ttl = re.sub(r'[^a-z一-鿿]', '', after)[:18]
    if 'uw professors' in t:   # 同一篇网页的两种写法
        return ('uw', '', 'turnover')
    return (a, y, ttl)


def bib_sort(x):
    return re.sub(r'[^a-z ]', '', unicodedata.normalize('NFKD', x).lower().replace('*', '')).strip()


def main():
    allrefs, site, odd = [], {}, []
    for i in range(0, 62):
        src = (B / ('b%02d.md' % i)).read_text(encoding='utf-8')
        body, refs = split_refs(src)
        name = {0: 'daolun.md', 61: 'jieyu.md'}.get(i, 'ch%02d.md' % i)
        if refs:
            body += '\n\n### 本章参考文献\n\n' + '\n'.join('- ' + r for r in refs)
        (OUT / name).write_text(body + '\n', encoding='utf-8')
        for r in refs:
            hits = SITE_RE.findall(r)
            if hits:
                for n, t in hits:
                    site.setdefault(int(n), set()).add(t.strip())
                continue
            if re.match(r'^(王德生|站内|胡敏|孔凡鹤)', r):
                odd.append(r); continue
            allrefs.append(r)
    (OUT / 'zuozhe.md').write_text((HERE / 'src_fixed/zuozhe.md').read_text(encoding='utf-8'), encoding='utf-8')
    (OUT / 'qianyan.md').write_text((HERE / 'src_fixed/qianyan.md').read_text(encoding='utf-8'), encoding='utf-8')
    # 去重：同键取最长（通常带刊物斜体与卷期的那条）
    best = {}
    for r in allrefs:
        k = key_of(r)
        if k not in best or len(r) > len(best[k]):
            best[k] = r
    xi = sorted((r for r in best.values() if re.match(r'^[*"“A-Za-z0-9]', r)), key=bib_sort)
    zh = sorted(r for r in best.values() if not re.match(r'^[*"“A-Za-z0-9]', r))
    rows, mismatch = [], []
    for n in sorted(site):
        e = CAT.get(n)
        if not e:
            mismatch.append({'no': n, 'titles': sorted(site[n]), 'issue': 'catalog 无此号'}); continue
        tt = e['title']
        for t in site[n]:
            if t != tt and not tt.startswith(t) and not t.startswith(tt):
                mismatch.append({'no': n, 'text': t, 'catalog': tt})
        rows.append('%s：第 %d 号《%s》，德麦国际专著。' % ('、'.join(e.get('authors') or []), n, tt))
    md = ['# 参考文献', '',
          '本书引到的外部文献与站内专著，按章汇总，去掉重复。西文按第一作者姓氏排序，中文与法规在后，站内专著按书号排列；站内专著的著者与书名以德麦国际书目为准。各章末尾另列该章用到的条目。', '',
          '### 西文文献', ''] + ['- ' + r for r in xi]
    if zh:
        md += ['', '### 中文文献与法规', ''] + ['- ' + r for r in zh]
    md += ['', '### 德麦国际专著（站内）', ''] + ['- ' + r for r in rows]
    (OUT / 'cankao.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    (HERE / 'refs_report.json').write_text(json.dumps({'raw': len(allrefs), 'dedup': len(best), 'site': len(rows), 'unparsedSiteLines': odd, 'siteMismatch': mismatch}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('src ok; refs raw', len(allrefs), 'dedup', len(best), 'site', len(rows), 'odd', len(odd), 'mismatch', len(mismatch))


if __name__ == '__main__':
    main()
