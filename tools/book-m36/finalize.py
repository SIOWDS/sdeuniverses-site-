#!/usr/bin/env python3
"""第 36 号：把逐章打磨过的 work/*.md 合回 parts/*.md，并做全书统稿层面的定点修订。

统稿修订只有三类，逐条 assert 命中：
1. 旧书名、旧结构的残留（初稿成于书名与篇目未定之时：《超级智能体诞生：理论和实践》、「商业篇」等），对齐成书的三编七篇；
2. 术语与事实的硬伤（主—互—物 → 主—互—客；「柏拉图式的物自身」→ 康德式）；
3. 记号统一（等号、乘号、加号、不换行空格）。
用法：python3 finalize.py
"""
import glob
import os
import re
from pathlib import Path

HERE = Path(__file__).parent
BOOK = '《人—GPT超级复合智能体》'

FIX = {
    '00-专家推荐与导论.1.md': [
        ('《健康的超级复合智能体》', '《健康的超级复合智能体入门》', 0),
    ],
    '70-下编序.1.md': [
        ('《健康的超级复合智能体》', '《健康的超级复合智能体入门》', 0),
    ],
    '25-第二篇.1.md': [
        ('“教育的超级智能体”“健康的超级智能体”“商业的超级智能体”提供共同的', '“教育的超级智能体”“健康的超级智能体”乃至“商业的超级智能体”提供共同的', 1),
        ('本篇作为《超级智能体诞生：理论和实践》的起手篇，', '本篇作为全书上编的第二篇，', 1),
        ('作为下一篇《人—GPT超级复合智能体的诞生》的桥梁', '作为通向中编《人—GPT超级复合智能体的诞生》的桥梁', 1),
    ],
    '25-第二篇.2.md': [
        ('成为教育、健康与商业超级智能体的认知中枢——这些，将是本书上半部分迈向实践篇的桥梁段落。',
         '成为教育、健康乃至商业超级智能体的认知中枢——这些，将是本书上编迈向下编实践各篇的桥梁段落。', 1),
    ],
    '25-第二篇.3.md': [
        ('为后续三大“超级智能体”——教育、健康、商业——提供了新的可能', '为后续的“超级智能体”——教育、健康乃至商业——提供了新的可能', 1),
        ('后面《何谓智能体》和《人—GPT超级复合智能体的诞生》诸篇', '后面《何谓智能体？》和《人—GPT超级复合智能体的诞生》诸篇', 1),
        ('专著后面的三大部分——《教育的超级智能体》《健康的超级智能体》《商业的超级智能体》——将各自从一个具体SIO场域出发',
         '本书下编的两篇——《教育的超级复合智能体》《健康的超级复合智能体入门》——以及留待后续著作展开的商业场域，将各自从一个具体SIO场域出发', 1),
        ('在商业篇，我们要问：能否设计', '在商业场域，我们要问：能否设计', 1),
        ('这三条路，共同构成《超级智能体诞生：理论和实践》的下半部，也构成了', '这三条路，共同构成本书的实践指向，也构成了', 1),
    ],
    '60-第五篇.2.md': [
        ('到《人—GPT超级复合智能体的诞生》本书的各个章节', '到本书%s的各个章节' % BOOK, 1),
    ],
    '60-第五篇.3.md': [
        ('那么这本《人—GPT超级复合智能体的诞生》，', '那么这本%s，' % BOOK, 1),
    ],
    '75-第六篇.1.md': [
        ('而在更大的专著结构里，教育这一篇只是第一个实践场域：在健康篇，我们会问同样的问题——健康系统如何在三律上运行；在商业篇，我们会问企业与经济SIO如何在三律上运行。它们共同构成了“超级复合智能体诞生”的下半部，',
         '而在全书的结构里，教育这一篇只是第一个实践场域：在健康篇，我们会问同样的问题——健康系统如何在三律上运行；在本书之外的商业场域，还要问企业与经济SIO如何在三律上运行。它们共同构成了“超级复合智能体诞生”的实践部分，', 1),
    ],
    '75-第六篇.2.md': [
        ('也是整部《超级复合智能体诞生》在教育篇中', '也是整部%s在教育篇中' % BOOK, 1),
        ('并不是整部《超级复合智能体诞生》的终点，而是起点', '并不是整部%s的终点，而是实践的起点' % BOOK, 1),
        ('在商业篇，我们将把组织—市场—家庭—GPT的SIO打开，重写“商业智能”的含义。',
         '至于商业，则有待在本书之外把组织—市场—家庭—GPT的SIO打开，重写“商业智能”的含义。', 1),
        ('帮我写一篇关于XXX的作文', '帮我写一篇关于某某的作文', 1),
    ],
    '80-第七篇.3.md': [
        ('当我们把视线从医疗室内稍微移开一点', '当我们把视线从诊室内稍微移开一点', 1),
    ],
    '80-第七篇.4.md': [
        ('它其实是整部《超级复合智能体诞生》中的一条主干河', '它其实是整部%s中的一条主干河' % BOOK, 1),
    ],
    '90-结论与后置.1.md': [   # 参考书目：核对著录；第 23 条查无此书，撤下
        ('4. Dreyfus, H. L. (1992). *What Computers Still Can\'t Do: A Critique of Artificial Reason* (Rev. ed.). MIT Press.',
         '4. Dreyfus, H. L. (1992). *What Computers Still Can\'t Do: A Critique of Artificial Reason*. MIT Press.', 1),
        ('5. Peirce, C. S. (1998). *The Essential Peirce: Selected Philosophical Writings, Vol. 2 (1893–1913)*. Indiana University Press.',
         '5. Peirce, C. S. (1998). *The Essential Peirce: Selected Philosophical Writings, Vol. 2 (1893–1913)* (Peirce Edition Project, Ed.). Indiana University Press.', 1),
        ('8. Wiener, N. (1965). *Cybernetics', '8. Wiener, N. (1961). *Cybernetics', 1),
        ('18. Illich, I. (1976). *Medical Nemesis: The Expropriation of Health*. Marion Boyars.',
         '18. Illich, I. (1976). *Limits to Medicine: Medical Nemesis, the Expropriation of Health*. Marion Boyars.', 1),
        ("\n\n23. Littman, M. L. (2021). *Agents and Devices: A Neuroscientist's Guide to AI*. MIT Press.", '', 1),
    ],
    '30-第三篇.1.md': [
        ('并不是柏拉图式的“物自身”', '并不是康德式的“物自身”', 1),
    ],
}
GLOBAL = [('主—互—物', '主—互—客'), ('主S、互I、物O', '主S、互I、客O'), (' ', ' ')]
CJK = r'一-鿿　-〿＀-￯“”‘’—…·'


def norm(s):
    for a, b in GLOBAL:
        s = s.replace(a, b)
    out = []
    for line in s.split('\n'):
        if not line.startswith(('#', '%%')) or True:
            line = line.replace('＝', '=').replace('＋', '+')
            line = re.sub(r' *(?<![=<>!])=(?!=) *', ' = ', line)
            line = re.sub(r' *× *', ' × ', line)
            line = re.sub(r' *\+ *', '+', line) if re.search('[一-鿿] *\\+|\\+ *[一-鿿]', line) else line
            line = re.sub(r'(?<=[%s]) +(?=[A-Za-z0-9Δθ(])' % CJK, '', line)
            line = re.sub(r'(?<=[A-Za-z0-9Δθ)%%]) +(?=[%s])' % CJK, '', line)
            line = re.sub(r'(?<=[%s]) +(?=\*\*)|(?<=\*\*) +(?=[%s])' % (CJK, CJK), '', line)
            line = re.sub(r'(?<=[一-鿿])vs(?= )', ' vs', line)
            line = line.replace('......', '……').rstrip()
            line = re.sub(r'^%%(?=\S)', '%% ', line)
        out.append(line)
    return '\n'.join(out)


def main():
    groups = {}
    for f in sorted(glob.glob(str(HERE / 'work' / '*.md')), key=lambda x: (os.path.basename(x).rsplit('.', 2)[0], int(x.split('.')[-2]))):
        name = os.path.basename(f)
        t = open(f).read()
        for a, b, n in FIX.get(name, []):
            c = t.count(a)
            assert (c == n) if n else c >= 1, (name, a[:30], c)
            t = t.replace(a, b)
        groups.setdefault(name.rsplit('.', 2)[0], []).append(norm(t).strip('\n'))
    tot = 0
    for key, chunks in groups.items():
        txt = re.sub(r'\n{3,}', '\n\n', '\n\n'.join(chunks)) + '\n'
        if key.startswith('90-'):   # 金句：每条一张卡
            txt = re.sub(r'^\*\*\d+\. ?(.+?)\*\*$', r'### \1', txt, flags=re.M)
            assert len(re.findall(r'^### ', txt, re.M)) == 10
        if key.startswith('80-'):
            txt = txt.replace('## 第七篇　健康的超级复合智能体｜', '## 第七篇　健康的超级复合智能体入门｜')
        assert '\\' not in txt, [l[:80] for l in txt.splitlines() if '\\' in l][:3]
        for l in txt.splitlines():
            if not l.startswith(('|', '-', '#', '%')):
                assert l.count('**') % 2 == 0, l[:80]
                assert l.count('“') == l.count('”'), (key, l[:60], l.count('“'), l.count('”'))
        (HERE / 'parts' / (key + '.md')).write_text(txt)
        tot += len(re.findall(r'[一-鿿]', txt))
    print('parts', len(groups), 'han', tot)


if __name__ == '__main__':
    main()
