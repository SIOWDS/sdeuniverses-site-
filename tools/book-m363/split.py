#!/usr/bin/env python3
"""第 363 号：把统稿后的单文件全稿（系列 Markdown 约定：YAML 头、【带走的话】【小账】【想一想】【编序】行首标记）
切成 220 系列成书脚本 build.py 要的分卷稿：front/00-前置.md、front/01-导论.md、parts/0N-*.md、back/09-结语.md、back/10-后置.md。
用法：python3 split.py /path/全稿.md
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
PARTS = ['上篇', '中篇一', '中篇二', '下篇一', '下篇二', '尾篇']


def conv_marks(lines):
    """行首标记 → build.py 认的引语块。连续的两行【小账】并成一个小账块。"""
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('【带走的话】'):
            out += ['> **带走的话**', '> ' + l[len('【带走的话】'):].strip(), '']
        elif l.startswith('【小账】'):
            rows = []
            while i < len(lines) and (lines[i].startswith('【小账】') or (not lines[i].strip() and i + 1 < len(lines) and lines[i + 1].startswith('【小账】'))):
                if lines[i].startswith('【小账】'):
                    t = lines[i][len('【小账】'):].strip()
                    m = re.match(r'^(看见与漏看|改进还是出题|[^：]{2,10})：(.*)$', t)
                    if m:
                        lab = {'看见与漏看': '看见了什么，漏看了什么？', '改进还是出题': '是在改进，还是在出题？'}.get(m[1], m[1] + '？')
                        rows.append('> %s——%s' % (lab, m[2].strip()))
                    else:
                        rows.append('> ' + t)
                i += 1
            out += ['> **小账**'] + rows + ['']
            continue
        elif l.startswith('【想一想】'):
            out += ['> **想一想**', '> ' + l[len('【想一想】'):].strip(), '']
        elif l.startswith('【编序】') or l.startswith('【编首】'):
            out += [re.sub(r'^【编[序首]】', '', l).strip(), '']
        else:
            out.append(l)
        i += 1
    return out


def main():
    src = Path(sys.argv[1]).read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n', src, re.S)
    meta, body = {}, src[m.end():]
    stm = []
    for line in m.group(1).splitlines():
        k, _, v = line.partition(':')
        if k.strip() == 'statement':
            stm.append(v.strip())
        else:
            meta[k.strip()] = v.strip()
    L = conv_marks(body.split('\n'))
    # 顶层切分
    tops, cur = [], None
    for l in L:
        h = re.match(r'^# (.+)$', l)
        if h:
            cur = [h.group(1).strip(), []]; tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    def join(x): return re.sub(r'\n{3,}', '\n\n', '\n'.join(x)).strip() + '\n'
    # 前置
    cp = ['## 出版信息', '', '| 字段 | 内容 |', '|---|---|',
          '| 书名 | %s——%s |' % (meta['title'], meta['subtitle']),
          '| 著者 | %s |' % meta['author'],
          '| 执笔 | AI 协作（Claude，Anthropic），作者口述立论、承重命题与裁定，并审定 |',
          '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
          '| 编号 | 德麦国际专著第 %s 号 |' % meta['series_no'],
          '| ISBN | %s |' % meta['isbn'], '| 定价 | %s |' % meta['price'],
          '| 开本 | 170 mm × 240 mm（16 开） |', '| 字数 | %s |' % meta['words'],
          '| 版次 | %s |' % meta['edition'], '| 完稿 | %s |' % meta['finished'], '']
    for x in stm:
        cp += [x, '']
    cp += [meta.get('copyright', '版权所有　侵权必究'), '', '---', '']
    front, lun, parts, back_end, back_rest = [], None, {}, None, []
    seen_main = False
    for t, b in tops:
        if t.startswith('导论'):
            lun = ['# ' + t, ''] + b; seen_main = True; continue
        pm = re.match(r'^(上篇|中篇一|中篇二|下篇一|下篇二|尾篇)　', t)
        if pm:
            parts[pm[1]] = ['# ' + t] + b; continue
        if t.startswith('结语'):
            back_end = ['# ' + t, ''] + b; continue
        if not seen_main:
            front += ['## ' + t, ''] + b + ['', '---', '']
        else:
            if re.match(r'^附录[一二三四五六七八九十]+　', t):
                back_rest += ['## ' + t, ''] + b
            else:
                back_rest += ['# ' + t, ''] + b
    (HERE / 'front/00-前置.md').write_text(join(cp + front))
    (HERE / 'front/01-导论.md').write_text(join(lun))
    for i, p in enumerate(PARTS, 1):
        (HERE / ('parts/%02d-%s.md' % (i, p))).write_text(join(parts[p]))
    (HERE / 'back/09-结语.md').write_text(join(back_end))
    (HERE / 'back/10-后置.md').write_text(join(back_rest))
    print('split ok', len(parts), 'parts')


if __name__ == '__main__':
    main()
