#!/usr/bin/env python3
"""第 238 号《特征律：西方哲学解构的屠龙刀》组装：src/ 下十六段打磨稿 → parts/NN-第X篇.md、back/*.md。

打磨稿的标题记号：# [篇]、## [摘要|引言|编|章|结论|后记|附论|全书结论|全书结尾]。
组装做五件事：按次序拼接并修三处接缝；统一标点与中西文间距；给章编全书连续的号；
生成各篇篇序；汇出〔待核〕总表。输出的 Markdown 里 ## 标题只有这几种：
  摘要 ／ 引言　题 ／ 第 N 章　题 ／ 第X编　题 ／ 结论　题 ／ 后记　题 ／ 附论　题
用法：python3 assemble.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / 'src'
CJK = r'[一-鿿〇]'
LAT = r'[A-Za-z0-9Δεσφ]'
CN = '零一二三四五六七八九十'

ORDER = ['s01', 's02', 's03', 's04', 's04-b', 's05', 's06', 's06-b', 's07', 's08', 's09', 's10', 's10-extra',
         's11', 's11-b', 's12', 's13', 's13-b', 's14', 's15', 's16']

PIANXU = {
    1: '本篇是全书的总纲。它从「花是红的、糖是甜的」这类日常断言讲起，说明特征律的三个条件——差异存在、差异稳定、复杂性机制——怎样把「特征」从固有物改写成发生的结果；再借气象、物理、生命、社会四个案例讲混沌—自组织—涌现，借心理学、语言学与 AI 讲三大意识的生成，最后落到知识、艺术与教育。',
    2: '本篇以亚里士多德为靶：他的「形式＋质料」是西方哲学两千年的支柱。作者认为，形式与质料的区分是差异稳定性在不同阈值下的投影，西方的「形式即本质」来自视觉中心的文明偏置。篇末附论{N}件，谈语言的本质、文明的多模态解放，以及希腊三哲的生平。',
    3: '本篇以康德为靶。第一编拆时间、空间、因果，第二编拆十二范畴，第三编拆真善美三大批判，第四编给出替代框架：特征律、自由律与幸福律。康德把发生的必然性固定成先天形式，是这一篇的总判断。篇末附论{N}件。',
    4: '本篇以黑格尔与马克思主义的辩证法为靶，称其为「必然学」，认为它本质上是发现学。第一编拆正反合与绝对精神，第二编拆它在历史唯物主义中的继承，第三编讲集体发生学，第四编讲文明的发生学逻辑。',
    5: '本篇以尼采为中心，从视角问题进入。作者的判断是：尼采把「发生的方向」误当成「主体的随意」。第一编拆尼采，第二编拆萨特、加缪的存在主义，第三编拆德里达、利奥塔、鲍德里亚，第四编讲三律哲学的确立。',
    6: '本篇是全书的方法书：把特征律的四大革命——本体论、发生论、复杂性、意义——化成可操作的刀法，依次解剖二十位西方哲学家，再以维特根斯坦为例给出五步流程，并试用于海德格尔、胡塞尔、尼采、德里达与中华哲学。',
}
CN_NUM = ['', '一', '二', '三', '四', '五', '六']


def read(name):
    p = SRC / (name + '.md')
    return p.read_text(encoding='utf-8')


def split_units(text):
    """把一段稿拆成 [(level, kind, title, body_lines)]；level 1 = 篇，2 = 其余。"""
    out, cur = [], None
    for line in text.split('\n'):
        m = re.match(r'^(#{1,2}) \[([^\]]+)\]\s*(.*)$', line)
        if m:
            cur = [len(m[1]), m[2], m[3].strip(), []]
            out.append(cur)
        elif cur is not None:
            cur[3].append(line)
        elif line.strip():
            raise SystemExit('标题前有正文：' + line[:40])
    return out


def seam_fix(units_by_seg):
    """三处接缝 + 重复的编标题。"""
    flat = []
    for seg in ORDER:
        for u in units_by_seg[seg]:
            flat.append([seg] + u)
    res = []
    last_group = None
    for seg, lvl, kind, title, body in flat:
        if kind == '编':
            if title == last_group:
                continue                     # 相邻两段重复印出的编标题
            last_group = title
        elif kind == '篇':
            last_group = None
        # 接缝一：s14 末尾只剩标题的「操作手册」附论
        if seg == 's14' and kind == '附论' and '操作手册' in title:
            continue
        # 接缝二：s15 开头被误挂在「后记」名下的操作手册正文
        if seg == 's15' and kind == '后记' and '维特根斯坦' in title:
            kind, title = '附论', '屠龙刀操作手册：哲学家解构的步骤示范'
            body = ['', '副题：以维特根斯坦为例', ''] + body
        res.append([seg, lvl, kind, title, body])
    return res


def norm_inline(s):
    if s.startswith('$$') or re.match(r'^\|[\s:|-]+\|$', s):
        return s
    # 引号
    s = s.replace('“', '「').replace('”', '」').replace('‘', '『').replace('’', '』')
    s = s.replace('——', '——')
    # 汉字间多余空格（PDF 强调造成）
    for _ in range(2):
        s = re.sub(r'(?<=[一-鿿，。；：、！？」』）》])[ \t]+(?=[一-鿿「『（《])', '', s)
    s = re.sub(r'(?<=[，。；：、！？」』）》])[ \t]+(?=[A-Za-z0-9])', '', s)
    s = re.sub(r'(?<=[一-鿿])[ \t]+(?=[，。；：、！？」』）])', '', s)
    # 中西文间距
    s = re.sub(r'(%s)(%s)' % (CJK, LAT), r'\1 \2', s)
    s = re.sub(r'(%s)(%s)' % (LAT, CJK), r'\1 \2', s)
    s = re.sub(r'(?<=[ΔΣ])\s+(?=SIO)', '', s)
    s = re.sub(r'[ \t]{2,}', ' ', s)
    return s.rstrip()


def norm_body(lines):
    out, blank = [], 0
    for ln in lines:
        raw = ln.rstrip()
        if not raw.strip():
            blank += 1
            if blank == 1:
                out.append('')
            continue
        blank = 0
        m = re.match(r'^(#{3,4} (?:◆ )?|> |- |\d+\. |\| )?(.*)$', raw)
        prefix = m[1] or ''
        if raw.startswith('|'):
            cells = [norm_inline(c.strip()) for c in raw.strip().strip('|').split('|')]
            out.append('| ' + ' | '.join(cells) + ' |')
        else:
            out.append(prefix + norm_inline(m[2]))
    while out and out[0] == '':
        out.pop(0)
    while out and out[-1] == '':
        out.pop()
    return out


def title_clean(t):
    t = norm_inline(t.strip())
    t = re.sub(r'^(结论|结语|后记|结尾宣言)[：:]\s*', '', t)
    t = re.sub(r'（约?\d+字）', '', t)
    return t.strip()


def main():
    units = {seg: split_units(read(seg)) for seg in ORDER}
    flat = seam_fix(units)
    # 分篇
    parts, cur = [], None
    back = {'结论': None, '结尾': None}
    for seg, lvl, kind, title, body in flat:
        if kind == '篇':
            cur = {'title': title_clean(title), 'sub': '', 'units': []}
            parts.append(cur)
            for ln in body:
                m = re.match(r'^副题：(.*)$', ln.strip())
                if m:
                    cur['sub'] = norm_inline(m[1])
            continue
        if kind == '全书结论':
            back['结论'] = (title_clean(title), norm_body(body)); continue
        if kind == '全书结尾':
            back['结尾'] = (title_clean(title), norm_body(body)); continue
        cur['units'].append((kind, title_clean(title), norm_body(body)))
    assert len(parts) == 6, len(parts)
    (ROOT / 'parts').mkdir(exist_ok=True)
    (ROOT / 'back').mkdir(exist_ok=True)
    n = 0
    hedao = []   # 待核总表条目
    toc_log = []
    for pi, p in enumerate(parts, 1):
        L = ['# 第%s篇　%s' % (CN_NUM[pi], p['title']), '']
        if p['sub']:
            L += ['副题：' + p['sub'], '']
        nfu = sum(1 for k, _, _ in p['units'] if k == '附论')
        L += [PIANXU[pi].replace('{N}', '一二三四五六七八九十'[nfu - 1] if nfu else ''), '']
        for kind, title, body in p['units']:
            if kind == '章':
                n += 1
                head = '## 第 %d 章　%s' % (n, title)
            elif kind == '编':
                head = '## ' + title
            elif kind == '摘要':
                head = '## 摘要'
            else:
                head = '## %s　%s' % (kind, title) if title else '## ' + kind
            L += [head, ''] + body + ['']
            toc_log.append((pi, head[3:]))
            cur_title = head[3:]
            sub = ''
            for ln in body:
                mm = re.match(r'^#{3,4} (?:◆ )?(.*)$', ln)
                if mm:
                    sub = mm[1]
                for m in re.finditer(r'〔待核〕', ln):
                    before = ln[:m.start()]
                    sents = [x for x in re.split(r'(?<=[。！？；])', before) if x.strip()]
                    snip = sents[-1] if sents else before
                    if len(snip) < 10 and len(sents) > 1:
                        snip = sents[-2] + snip
                    snip = re.sub(r'^[\s|\-\d.、]+', '', snip)[-60:]
                    where = cur_title + (' · ' + sub if sub and kind != '摘要' else '')
                    hedao.append((pi, where, snip + '〔待核〕'))
        (ROOT / 'parts' / ('%02d-第%s篇.md' % (pi, CN_NUM[pi]))).write_text('\n'.join(L).rstrip() + '\n', encoding='utf-8')
    for key, fn, lab in (('结论', '01-全书结论.md', '结论'), ('结尾', '02-结尾宣言.md', '结尾宣言')):
        t, b = back[key]
        (ROOT / 'back' / fn).write_text('\n'.join(['# %s　%s' % (lab, t), ''] + b) + '\n', encoding='utf-8')
    # 待核总表
    rows = ['| 序 | 篇 | 位置 | 存疑处 |', '|---|---|---|---|']
    for i, (pi, where, snip) in enumerate(hedao, 1):
        snip = snip.replace('|', '／').strip()
        rows.append('| %d | 第%s篇 | %s | %s |' % (i, CN_NUM[pi], where.replace('|', '／'), snip))
    (ROOT / 'back' / 'hedao-table.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    han = sum(len(re.findall(CJK, f.read_text())) for f in list((ROOT / 'parts').glob('*.md')) + list((ROOT / 'back').glob('*.md')))
    print('chapters', n, 'hedao', len(hedao), 'han chars (parts+back)', han)
    for pi, t in toc_log:
        pass


if __name__ == '__main__':
    main()
