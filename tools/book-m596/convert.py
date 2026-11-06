#!/usr/bin/env python3
"""第 596 号《AI时代中华智慧的困境和出路》：把 chapters/chNN.md、notes/nNN.md、appendix.md 转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文文字。导论放在第一编之前（LUNS）；结语、资料与引用说明、附录、版本说明放后置；每编前的“编序”由 PART_INTRO 提供。
用法：python3 convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
CH, NT = HERE / 'chapters', HERE / 'notes'
sys.path.insert(0, str(HERE))
import meta as M  # noqa
han = lambda s: len(re.findall(r'[一-鿿]', s))
CN = '零一二三四五六七八九十'
PARTS = json.loads((HERE / 'parts.json').read_text(encoding='utf-8'))
PART_INTRO = {
 1: '这一编先回到起点：为什么一个“中”字，能把中原之行、中庸、时中日新与生生、以及中华智慧的多样性放进同一个文明问题。第 1 章交代问题怎样产生，第 2 章把中庸界定为守中守正的发展智慧，第 3 章讲时中、日新与生生提供的创造资源，第 4 章看智慧怎样变成习惯与制度，又怎样因此出现多样与竞争。本编不急于宣布传统失效，先把它最有力的一面说清楚。',
 2: '第二编看引进与发展战略。第 5 章讲引进为什么能成为发展的起点，第 6 章讲从引进到扩张需要哪些能力，第 7 章讲追赶窗口与投入回收之间的矛盾，第 8 章问发展在什么条件下转成新基底的发生。每一章都同时写成功的机制和失效的条件。',
 3: '第三编转向 AI。第 9 章讲既有答案的成本结构怎样改变，第 10 章讲当优化能力成为普遍可得的资源，什么还保有差异化价值，第 11 章把人和 AI 复合体作为创造的主体来分析，第 12 章以 DeepSeek 为开放的观察案例，说明怎样检验“持续突破”这样的说法。',
 4: '第四编提出发展型智慧遇到的四种深层困境：评价尺度（第 13 章）、知识同一性（第 14 章）、主体形成（第 15 章）、组织回写（第 16 章）。每一章先说这套安排曾经为什么有效，再说在 AI 条件下哪里开始失灵。',
 5: '第五编是全书的理论重建。第 17 章讲显露、差异序列与特征纠缠，第 18 章讲 0 到 1 与 1 到 N 怎样递归发生，第 19 章讲三界信息与能量中的基底重组，第 20 章给出发生智慧的工作程序与证伪要求。三方程在这里是联合解释的要求，不是数学定理。',
 6: '第六编是全书的主体编，把前面的概念带进三种生活：教育（第 21 至 24 章）、健康（第 25 至 28 章）、事业（第 29 至 32 章）。每个领域四章，次序相同：先重建旧路径的最强版本，再看 AI 带来的变化，然后提出共同发生的方案，最后写明怎样验证。三个领域的试点尚未实施，方案都按待检验的设想来读。',
 7: '第七编面向普通人：经验怎样成为知识母本（第 33 章），公共知识与同一性谱系知识有什么不同（第 34 章），书、知识库与智能体怎样共享基底（第 35 章），怎样形成一个可持续的知识发生循环（第 36 章）。',
 8: '第八编讲让新基底能够发生的公共条件：评价体系怎样容纳新问题（第 37 章），组织怎样保护探索并承接结果（第 38 章），平台怎样扩大知识发生的机会（第 39 章），创新治理怎样守住人的生活（第 40 章）。',
 9: '第九编回到文明责任：从守中开花到持续生成花种（第 41 章），中华智慧怎样参与跨文明创造（第 42 章），匹夫有责的具体责任结构（第 43 章），怎样检验中华智慧的新出路（第 44 章）。',
}


def cnum(n):
    return CN[n] if n <= 10 else None


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def read(p):
    return Path(p).read_text(encoding='utf-8')


def main():
    (HERE / 'parts').mkdir(exist_ok=True)
    total = 0
    md = read(CH / 'ch00.md')
    title = md.splitlines()[0][2:].strip()
    body = '\n'.join(md.splitlines()[1:]).strip() + '\n'
    total += body_han_of(body)
    (HERE / 'front/01-导论.md').write_text('# ' + title + '\n\n' + body, encoding='utf-8')
    nch = 0
    for k in range(1, 10):
        name, chs = PARTS[str(k)]
        chunks = ['# 第%s编　%s\n\n%s\n' % (cnum(k), name, PART_INTRO[k])]
        for n in chs:
            md = read(CH / ('ch%02d.md' % n))
            h = md.splitlines()[0]
            assert h.startswith('## 第 %d 章　' % n), h
            b = '\n'.join(md.splitlines()[1:]).strip() + '\n'
            total += body_han_of(b); nch += 1
            chunks.append('%s\n\n%s' % (h, b))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    assert nch == 44, nch
    back = []
    md = read(CH / 'ch99.md')
    t99 = md.splitlines()[0][2:].strip()
    b = '\n'.join(md.splitlines()[1:]).strip() + '\n'
    total += body_han_of(b)
    back.append('# %s\n\n%s' % (t99, b))
    # 资料与引用说明
    n0 = read(NT / 'n00.md').strip()
    parts = ['# 资料与引用说明\n\n' + n0 + '\n']
    for n in range(1, 45):
        t = read(NT / ('n%02d.md' % n)).strip()
        ttl = re.match(r'^## 第 %d 章　(.*)$' % n, read(CH / ('ch%02d.md' % n)).splitlines()[0])[1]
        parts.append('### 第 %d 章　资料说明\n\n%s\n' % (n, t))
    back.append('\n'.join(parts))
    # 附录
    app = read(HERE / 'appendix.md').splitlines()
    terms = [l.strip() for l in app[1:] if l.strip()]
    rows = ['| 术语 | 本书中的用法 |', '|---|---|']
    for l in terms:
        a, _, c = l.partition('  ')
        rows.append('| %s | %s |' % (a.strip(), c.strip()))
    extra = ''
    if (HERE / 'appendix_extra.md').exists():
        extra = '\n' + read(HERE / 'appendix_extra.md').strip() + '\n'
    back.append('# 附录\n\n本附录收录核心术语速查与全书论证地图，供读者查阅；它们都是对正文已有用法的压缩，不增加新的论断。\n\n## 附录一　核心术语速查\n\n' + '\n'.join(rows) + '\n' + extra)
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = read(HERE / 'front/00-前置.tpl.md')
    btpl = read(HERE / 'back/12-后置.tpl.md')
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_); btpl = btpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl, encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text('\n'.join(back) + '\n' + btpl, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d.md' % k for k in range(1, 10)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'body_han', total, 'all_han', han(b))


if __name__ == '__main__':
    main()
