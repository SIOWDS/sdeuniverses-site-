#!/usr/bin/env python3
"""第 445 号：把打磨后的分章稿（pol/u00—u51）与前后件拼成全稿，统一体例，再切成 build.py 要的分卷稿。
用法：python3 assemble.py /home/claude/lichen
产物：<src>/full.md（全稿）；本目录 front/ parts/ back/
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1])
CN = '一二三四五六七八九十'
PUB = [
    ('书名', '《家庭保险管理发生学——从备用E到教育、健康与事业的价值保全》'),
    ('著者', '李辰'),
    ('执笔', '李辰著；文字在 AI 协作下成稿，统稿与排版由 Claude 执笔'),
    ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
    ('编号', '德麦国际专著第 445 号'),
    ('ISBN', '979-8-90690-676-2'),
    ('定价', 'US$24.00'),
    ('开本', '170 mm × 240 mm'),
    ('字数', '__WAN__'),
    ('版次', '2026 年 10 月第 1 版'),
]
NOTES = [
    'AI 协作声明：本书由李辰著，文字在 AI 协作下成稿，统稿与排版由 Claude 执笔。书中所用 SDE 方法（三方程、六路径、三原理）出自王德生博士的 SDE 本体论。',
    '构拟说明：家庭甲、乙、丙、丁四户及其情景均为本书构拟，用于说明逻辑上的可能与操作上的做法，不代表任何真实家庭，不计作经验证据；设定见附录一。书中的七个假说尚待检验，检验与反例的登记见第 47、48 章。',
    '使用说明：本书不评价任何具体的保险产品、机构或人工智能产品，不构成保险、投资、法律或医疗建议。保险合同以条款原文为准，社会保险与公共服务以所在地区现行规定为准；涉及健康的内容只谈保障与家庭安排，身体的难处请找医生。凡标〔待核〕处，出处或版本尚待核对。',
    '全书结构：出版信息、作者介绍、题词、目录；导论；十编五十章；结语；参考书目；附录二件（四户构拟家庭一览、五十章交付件一览）。',
    '版权所有　侵权必究',
]


def norm(t):
    t = t.replace('\\[', '[').replace('\\]', ']')
    t = t.replace('“', '「').replace('”', '」').replace('‘', '『').replace('’', '』')
    lines = []
    for l in t.split('\n'):
        if l.startswith('|') and re.fullmatch(r'\|[\s\-:|]+\|?', l.strip()):
            lines.append(l); continue
        l = re.sub(r'(?<=[一-鿿])(?=\d)', ' ', l)
        l = re.sub(r'(?<=\d)(?=[一-鿿])', ' ', l)
        lines.append(l)
    t = '\n'.join(lines)
    t = re.sub(r'^## 第 (\d+) 章　', lambda m: '## 第 %s 章　' % m[1], t, flags=re.M)
    t = t.replace('！', '。')
    return t


def main():
    bx = json.loads((SRC / 'bianxu.json').read_text())
    units = [(SRC / 'pol' / ('u%02d.md' % i)).read_text().strip() for i in range(52)]
    body = []
    for u in units:
        L = u.split('\n')
        m = re.match(r'^# (第(.)编)　', L[0])
        if m:
            L = [L[0], '', bx[m[1]], ''] + L[1:]
        body.append('\n'.join(L))
    front = (SRC / 'front.md').read_text().strip()
    back = '\n\n'.join([(SRC / 'bib.md').read_text().strip(),
                        '# 附录\n\n附录二件，供查、供对。附录一写明四户构拟家庭的设定，各章凡用到它们，以此为准；附录二按章列出五十章的交付件，供家庭、从业者与研究者查找。',
                        (SRC / 'appx1.md').read_text().strip(), (SRC / 'appx2.md').read_text().strip()])
    full = norm(front + '\n\n' + '\n\n'.join(body) + '\n\n' + back) + '\n'
    han = len(re.findall(r'[一-鿿]', full))
    wan = '约 %d 万字' % round(han / 10000)
    pub = '\n'.join(['| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % kv for kv in PUB]) + '\n\n' + '\n\n'.join(NOTES)
    full = full.replace('@@PUBINFO', pub).replace('__WAN__', wan)
    (SRC / 'full.md').write_text(full)
    # 切分
    tops, cur = [], ['__front__', []]
    tops.append(cur)
    for l in full.split('\n'):
        m = re.match(r'^# (.+)$', l)
        if m:
            cur = [m[1], []]; tops.append(cur)
        cur[1].append(l)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob('*.md'):
            f.unlink()
    (HERE / 'front/00-前置.md').write_text('\n'.join(tops[0][1]).strip() + '\n')
    lun = [t for t in tops if t[0].startswith('导论')]
    parts = [t for t in tops if re.match(r'^第.编', t[0])]
    jie = [t for t in tops if t[0].startswith('结语')]
    rest = [t for t in tops if t[0].startswith(('参考书目', '附录'))]
    assert len(lun) == 1 and len(parts) == 10 and len(jie) == 1 and len(rest) == 2, (len(lun), len(parts), len(jie), len(rest))
    (HERE / 'front/01-导论.md').write_text('\n'.join(lun[0][1]).strip() + '\n')
    for i, (t, ls) in enumerate(parts, 1):
        (HERE / ('parts/%02d-第%s编.md' % (i, CN[i - 1]))).write_text('\n'.join(ls).strip() + '\n')
    (HERE / 'back/09-结语.md').write_text('\n'.join(jie[0][1]).strip() + '\n')
    (HERE / 'back/10-后置.md').write_text('\n\n'.join('\n'.join(t[1]).strip() for t in rest) + '\n')
    print('assembled; han', han, wan)


if __name__ == '__main__':
    main()
