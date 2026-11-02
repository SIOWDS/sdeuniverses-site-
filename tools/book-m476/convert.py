#!/usr/bin/env python3
"""第 476 号《放不下：三界回写留下的洞》（由第 474 号 convert.py 改来）：把统稿合成稿 src/full.md 转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文文字。

src/full.md（统稿人合成，assemble.py 生成）的结构：
  --- 元数据块 ---
  # 作者介绍 / # 前言 / # 导论　题
  # 第一编　题（其下两段【编序】）……# 第三编　题；## 第 N 章　题（1–9）；章首「> 一句话」；### 第一节　节题；#### ◆ 一、小节题
  【带走的话】…（节末、章末）【小账】…（章末）【想一想】…（章末）
  # 结语　题 / # 参考书目 / # 附录一　题 … # 附录五　题 / # 后记
  无导读。

「编—章—节」三层的转换：
  编 →「# 第一编　题」原样（编首页、金色花饰、“编　序”）；【编序】两段写成编序段；
  章 →「## 第 N 章　题」原样；章首「> 一句话」→「> **章旨**」块；
  节 →「### 第一节　题」；◆ 小节 →「#### ◆ 一、题」；
  【带走的话】【小账】【想一想】→ 引用块盒子（连续同类行并成一盒）。
产物：front/00-前置.md（出版信息、题词、作者介绍、前言）、front/01-导言.md（导论）、parts/01–03.md、
      back/12-后置.md（结语、参考书目、附录总页＋附录一至五、后记）、book.md、han.json。
用法：python3 tools/book-m476/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
BOX_RE = re.compile(r'^【(带走的话|小账|想一想|编序)】\s*(.*)$')


def split_front_matter(text):
    meta, body = {'statement': []}, text
    if text.startswith('---\n'):
        end = text.index('\n---\n', 4)
        for l in text[4:end].splitlines():
            k, sep, v = l.partition(':')
            if not sep:
                continue
            k, v = k.strip(), v.strip()
            if k == 'statement':
                meta['statement'].append(v)
            elif k:
                meta[k] = v
        body = text[end + 5:]
    return meta, body


def conv_body(lines):
    out, plain_prev, i, n = [], False, 0, len(lines)
    while i < n:
        l = lines[i].rstrip()
        s = l.strip()
        if s == '---':
            out.append(''); plain_prev = False; i += 1; continue
        m = BOX_RE.match(s)
        if m:
            kind, items, j = m[1], [], i
            while j < n:
                mm = BOX_RE.match(lines[j].strip())
                if mm and mm[1] == kind:
                    items.append(mm[2]); j += 1; continue
                break
            if kind == '编序':
                for it in items:
                    out.extend(['', it, ''])
            else:
                out.extend(['', '> **%s**' % kind, '>'])
                for k, it in enumerate(items):
                    out.append('> ' + it)
                    if k < len(items) - 1:
                        out.append('>')
                out.append('')
            plain_prev = False
            i = j; continue
        mq = re.match(r'^> ?\**(带走的话|小账|想一想)\**[　 ：:]*(.*)$', s)
        if mq:   # 少数章把章末盒子写成引用块（「> 小账　……」「> 想一想」后接「> 1. ……」），一并改成标准盒子
            kind, items, j = mq[1], [mq[2]] if mq[2] else [], i + 1
            while j < n and lines[j].startswith('>') and lines[j].strip() != '>':
                items.append(lines[j].lstrip('>').strip()); j += 1
            out.extend(['', '> **%s**' % kind, '>'])
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            out.append('')
            plain_prev = False
            i = j; continue
        if re.match(r'^> 本章[一二三四五六七八九十]+节[：:]', s):
            out.extend(['', '> **章旨**', '>', '> ' + s[2:].strip(), ''])
            plain_prev = False; i += 1; continue
        if s.startswith('> ') and not s.startswith('> **'):   # 第 476 号：章首一句话引导（紧跟「## 第 N 章」）→ 章旨
            prev = next((x for x in reversed(out) if x.strip()), '')
            if re.match(r'^## 第 \d+ 章　', prev):
                out.extend(['', '> **章旨**', '>', s, ''])
                plain_prev = False; i += 1; continue
        is_plain = bool(s) and not re.match(r'^(#|>|\||- |\d+\. )', s)
        if is_plain and plain_prev:
            out.append('')
        out.append(l)
        plain_prev = is_plain
        i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def chars_of(md):
    """含标点的字数：去掉 Markdown 记号与空白后的字符数。"""
    t = []
    for x in md.splitlines():
        if re.fullmatch(r'\|?[\s:|-]+\|?', x.strip()) and '-' in x:
            continue
        x = re.sub(r'^#+ ', '', x)
        x = re.sub(r'^> ?', '', x)
        t.append(x.replace('**', '').replace('|', '').replace('◆', ''))
    return len(re.sub(r'\s', '', ''.join(t)))


def body_han_of(md):
    return han('\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|')).replace('**', ''))


def main():
    fm, body = split_front_matter((HERE / M.SRC).read_text(encoding='utf-8'))
    tops, cur = [], None
    for l in body.splitlines():
        if l.startswith('# '):
            cur = [l[2:].strip(), []]
            tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    key = lambda t: re.split(r'[\s　]', t[0], maxsplit=1)[0]
    get = lambda nm: next(t for t in tops if key(t) == nm)
    author, qian, lun, jie = get('作者介绍'), get('前言'), get('导论'), get('结语')
    bib, hou = get('参考书目'), get('后记')
    parts = [t for t in tops if re.match(r'^第[一二三]编', t[0])]
    apps = [t for t in tops if re.match(r'^附录[一二三四五六七八九十]', t[0])]
    assert len(parts) == 3, [key(t) for t in tops]
    assert len(apps) == 5, [a[0] for a in apps]
    norm = lambda t: re.sub(r'^(\S+?)[\s　]+', r'\1　', t, count=1)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)

    st = {'body': 0, 'chars': 0, 'appendix': 0}

    def acc(md, appx=False):
        h = body_han_of(md)
        st['body'] += h
        st['appendix'] += h if appx else 0
        return md

    author_md = conv_body(author[1])
    qian_md = acc(conv_body(qian[1]))
    lun_md = acc(conv_body(lun[1]))
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (norm(lun[0]), lun_md), encoding='utf-8')

    nums, parts_md = [], []
    for k, (pt, lines) in enumerate(parts, 1):
        md = acc(conv_body(lines))
        nums += [int(x) for x in re.findall(r'^## 第 (\d+) 章　', md, re.M)]
        parts_md.append(md)
        (HERE / ('parts/%02d.md' % k)).write_text('# %s\n\n%s' % (norm(pt), md), encoding='utf-8')
    assert nums == list(range(1, 10)), nums

    jie_md = acc(conv_body(jie[1]))
    app_md = ['## %s\n\n%s' % (norm(t), acc(conv_body(b), True)) for t, b in apps]
    back = ('# %s\n\n%s\n# 参考书目\n\n%s\n# 附录\n\n本书附录五件：%s。附录一照原话登记二十九条口述承重命题；附录五写明本书自认最弱处与推翻条件，读者可先看。\n\n%s\n'
            '# 后记\n\n%s'
            % (norm(jie[0]), jie_md, conv_body(bib[1]), '；'.join(a[0].replace('　', ' ') for a in apps), '\n'.join(app_md),
               conv_body(hou[1])))
    (HERE / 'back/12-后置.md').write_text(back, encoding='utf-8')

    st['chars'] = chars_of('\n'.join([author_md, qian_md, lun_md] + parts_md + [back]))
    mw = re.search(r'(\d+)\s*万字', fm.get('words', ''))
    st['wan'] = int(mw[1]) if mw else round(st['chars'] / 10000)   # 对外“约 N 万字”以统稿元数据 words 为准（统稿人按全稿含标点计）
    wan = st['wan']
    (HERE / 'han.json').write_text(json.dumps(st), encoding='utf-8')

    # 出版信息：书号、ISBN、定价取 meta（唯一来源）；执笔、声明取 full.md 元数据块
    rows = [('书名', '《%s：%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
            ('执笔', fm.get('executor', '')), ('出版', '%s（%s）· 新加坡' % (M.PUBLISHER, M.PUBLISHER_EN)),
            ('编号', '德麦国际专著第 %d 号' % M.NO), ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
            ('字数', '约 %d 万字（含标点）' % wan), ('版次', M.EDITION_SP)]
    front = ['## 出版信息', '', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % (a, b.replace('|', '／')) for a, b in rows if b]
    front += ['']
    for s in fm['statement']:
        front += [s, '']
    front += [fm.get('copyright', '版权所有　侵权必究'), '']
    front += ['## 题词', '', '【题词】' + M.EPIGRAPH, '', '【题词署】——王德生', '']
    front += ['## 作者介绍', '', author_md, '## 前言', '', qian_md]
    (HERE / 'front/00-前置.md').write_text('\n'.join(front), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 4)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'parts', len(parts), 'appendices', len(apps),
          'body_han', st['body'], '(appendix %d)' % st['appendix'], 'chars', st['chars'], '约%d万字' % wan,
          'jie', len(re.findall(r'^### 第[一二三四五六七八九十]+节　', b, re.M)), 'take', b.count('> **带走的话**'),
          'ledger', b.count('> **小账**'), 'think', b.count('> **想一想**'), 'lead', b.count('> **章旨**'))


if __name__ == '__main__':
    main()
