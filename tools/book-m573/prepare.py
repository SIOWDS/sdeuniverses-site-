#!/usr/bin/env python3
"""第 573 号《从聪明到智慧》（王德生　王涛 著）：把统稿三审后的定稿 src/source.md 转成 220/302 版式工具链认的合成稿 src/full.md。
只改格式（标题层级、列表、换行），不动正文文字。
结构：前置（专家推荐语、前言、怎样读这本书）→ 导读（原导论）→ 六编二十一章 → 结语 → 附录四件 → 后记。
「内容简介」进详情页，「作者简介」进前置模板的作者介绍，二者不进合成稿。
用法：python3 tools/book-m573/prepare.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = (HERE / 'src/source.md').read_text(encoding='utf-8')
TITLE = '从聪明到智慧'
APPX = {'附录A': '附录一', '附录B': '附录二', '附录C': '附录三'}


def tops(text):
    out, cur = [], None
    for l in text.split('\n'):
        if l.startswith('# '):
            cur = [l[2:].strip(), []]; out.append(cur)
        elif cur is not None:
            cur[1].append(l)
    return out


def norm_body(lines, shift):
    """shift：源里 ## 在目标里变成几级。返回目标行。"""
    res = []
    for raw in lines:
        l = raw.rstrip().replace('\\_', '_')
        m = re.match(r'^(#{2,5}) (.*)$', l)
        if m:
            lv = len(m[1]) + shift
            t = m[2].strip()
            if lv >= 5:
                res += ['', '**%s**' % t, '']
            else:
                if lv == 3 and re.match(r'^(\d+\.\d+ |[一二三四五六七八九十]+、|卡\d|走表示范|行动哲学自评量表|五张卡|本章收束|本编终点)', t):
                    t = '◆ ' + t
                res += ['', '#' * lv + ' ' + t, '']
            continue
        hard = l.endswith('\\')
        if hard:
            l = l[:-1]
        mq = re.match(r'^>\s?(.*)$', l)
        if mq:
            tx = mq[1].strip()
            if not tx:
                continue
            if len(tx.replace('**', '')) <= 90:
                res.append('- ' + tx)
            else:
                res += ['', tx, '']
            continue
        if re.match(r'^\s*[-*]\s+', l):
            res.append('- ' + re.sub(r'^\s*[-*]\s+', '', l))
            continue
        mn = re.match(r'^\s*(\d+)\.\s+(.*)$', l)
        if mn:
            res.append('%s. %s' % (mn[1], mn[2]))
            continue
        res.append(l.strip())
        if hard:
            res.append('')
    # 列表项之间的空行去掉；列表前后留空行
    out = []
    for i, l in enumerate(res):
        if l == '' and out and re.match(r'^(- |\d+\. )', out[-1]):
            j = i + 1
            while j < len(res) and res[j] == '':
                j += 1
            if j < len(res) and re.match(r'^(- |\d+\. )', res[j]) and (res[j].startswith('- ') == out[-1].startswith('- ')):
                continue
        if out and l and re.match(r'^(- |\d+\. )', l) and out[-1] and not re.match(r'^(- |\d+\. )', out[-1]):
            out.append('')
        if out and l and not re.match(r'^(- |\d+\. )', l) and out[-1] and re.match(r'^(- |\d+\. )', out[-1]):
            out.append('')
        out.append(l)
    txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip()
    return txt


def main():
    T = tops(SRC)
    names = [t[0] for t in T]
    get = lambda p: next(t for t in T if t[0].startswith(p))
    res = ['# ' + TITLE, '']
    res += ['# 专家推荐语　十二个行业的读法', '', norm_body(get('专家推荐语')[1], 0), '']
    xu = get('序言')
    res += ['# 前言　' + xu[0].split('：', 1)[1], '', norm_body(xu[1], 1), '']
    dd = get('问题驱动的导读建议')
    res += ['# 怎样读这本书　问题驱动的导读建议', '', norm_body(dd[1], 0), '']
    res += ['# 导读　行动哲学的地基与全书路线图', '', norm_body(get('导论')[1], 1), '']
    for t, body in T:
        if not re.match(r'^第.编　', t):
            continue
        # 编序小标题成为编序首段的粗体句
        b = list(body)
        k = next(i for i, l in enumerate(b) if l.startswith('## 编序'))
        lead = b[k][3:].strip().split('：', 1)[1]
        b[k] = '**%s**' % lead
        # 章：## 第N章　题 → ## 第 N 章　题；章内 ### → ### ◆
        res += ['# ' + t, '']
        chunk, chs = [], []
        cur = None
        for l in b:
            m = re.match(r'^## 第(\d+)章　(.*)$', l)
            if m:
                cur = [int(m[1]), m[2].strip(), []]; chs.append(cur); continue
            (cur[2] if cur else chunk).append(l)
        res += [norm_body(chunk, 0), '']
        for n, tt, cb in chs:
            res += ['## 第 %d 章　%s' % (n, tt), '', norm_body(cb, 0), '']
    jy = get('结语')
    res += ['# 结语　' + jy[0].split('：', 1)[1], '', norm_body(jy[1], 1), '']
    res += ['# 附录', '', '本书附录四件：前三件是正文主张的三处延伸——主体性的拥有感、圣经人物的三阶梯样本、科技创新的三合一纠缠；第四件把全书压成十条金句，便于随身带走、反复回读。', '']
    for k, v in APPX.items():
        a = get(k)
        sub = a[0].split('：', 1)[1]
        res += ['## %s　%s' % (v, sub), '', norm_body(a[1], 0), '']
    q = get('金句集锦')
    qb = []
    for l in q[1]:
        m = re.match(r'^### (\d+)．(.*)$', l)
        qb.append('### ◆ %s．%s' % (m[1], m[2]) if m else l)
    res += ['## 附录四　金句集锦', '', norm_body(qb, 0), '']
    hj = get('后记')
    res += ['# 后记　' + hj[0].split('：', 1)[1], '', norm_body(hj[1], 1), '']
    out = re.sub(r'\n{3,}', '\n\n', '\n'.join(res)).rstrip() + '\n'
    (HERE / 'src/full.md').write_text(out, encoding='utf-8')
    print('ok parts', len(re.findall(r'^# 第.编　', out, re.M)), 'chapters', len(re.findall(r'^## 第 \d+ 章　', out, re.M)),
          'han', len(re.findall(r'[一-鿿]', out)))


if __name__ == '__main__':
    main()
