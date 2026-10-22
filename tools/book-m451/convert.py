#!/usr/bin/env python3
"""第 451 号《发生的时差》：把统稿稿 book/*.md 转成 220 系列流水线的分卷 Markdown：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/09-结语.md、back/10-后置.md"""
import re
from pathlib import Path
S = Path('/tmp/claude-0/-home-claude/80312848-3eed-5825-9fb1-571a70adbd7e/scratchpad')
B, T = S / 'book', Path(__file__).resolve().parent
for d in ('front', 'parts', 'back'): (T / d).mkdir(parents=True, exist_ok=True)

PARTS = [
 (1, 5, '第一编　换档是什么', [
  '这一编五章，先把全书要用的几个词立起来。第 1 章从三大方程那句「谁也不先于谁」讲起：几样东西互相写，却没有说写得一样快。第 2 章把「快」字拆开，缓劲、先手、当家是三件事。第 3 章画出六种档位，讲换档靠什么推动。第 4 章讲卡档的两副样子。第 5 章把前人一家一家请出来，看他们走到了哪一步。',
  '**不怕慢，怕卡档。快慢不同是常事，快慢的次序换不过来，才是病。**']),
 (6, 10, '第二编　身体的档位', [
  '这一编五章，把换档放回身体里。血压不是一个数，一口气里有快手也有慢手，修复开工容易收工难，器官的一项功能常有两条路，三家医学各自守着一个「本来」。五章说的是同一件事：健康不是每只钟都准，是几只钟的快慢次序还能随着日子换。',
  '**身体的事请找医生。这一编只帮你看清：哪一只钟慢了，哪一个次序卡住了。**']),
 (11, 14, '第三编　家里的档位', [
  '这一编四章，回到卢家那套 2004 年买的三居室。房子跟不上日子，备用钱来得比冲击慢，安慰来得比难处快，现实换了版、人还在用旧版。家里没有谁做错事，毛病多半出在几样东西缓劲的次序上。',
  '**一个家僵住，常常不是谁不好，是慢的那一样一直没被等到。**']),
 (15, 19, '第四编　国家与规矩的档位', [
  '这一编五章，把同一个问题放到国家和规矩里去问。法律、政治、经济三副脚步缓劲不同；当家可以轮换，档位却未必跟着换；国家认不认旧话；家里的手和国家的手谁跑得快；一个国家怎样病，又怎样再来一次。',
  '**换了当家的人，不等于换了档。换了人没换档，就是轮回。**']),
 (20, 23, '第五编　老书里的档位', [
  '这一编四章，读几部老书：庄子、道德经、哥林多前书，以及佛家说的无常。本书不评判信仰本身，只借这些书里已有的读法，多问一句：快慢的次序还换不换得过来。',
  '**凿一半，放一晚；回去的路，是另一条路。**']),
 (24, 27, '第六编　知识自己的档位', [
  '这一编四章，把镜头转向知识本身：发现为什么总是晚到两步，词义怎样被封口词焊死，一门学问怎样从旧学问里撞出来。最后一章把本书参考的二十本书、连同本书自己，当作标本放上桌面。',
  '**框沉得比来料快，新的就被读成旧的；统稿赶不上执笔，书里就留下缝。**']),
 (28, 30, '第七编　用得上', [
  '这一编三章，只讲怎么用：教室里、身体与照护里、单位与生意里，怎样看出卡档，怎样帮它换档。每一章都给五个看得见的信号、五个明天就能试的小办法。',
  '**换档不必推倒重来，有时只要给慢的那一样留出几个夜晚。**']),
]
TAIL = ['放回日子里', '本章怎样会错', '带走的话', '小账', '想一想', '给想深究的人']


def split_tail(text):
    """把章末各小节切出来，按版式要求重排：…放回日子里 → 给想深究的人(框) → 本章怎样会错(框) → 带走的话 → 小账 → 想一想"""
    parts = re.split(r'^### (放回日子里|本章怎样会错|带走的话|小账|想一想|给想深究的人)\s*$', text, flags=re.M)
    head, rest = parts[0], parts[1:]
    tails = {rest[i]: rest[i + 1].strip() for i in range(0, len(rest), 2)}
    def box(lab, body):
        lines = [l for l in body.split('\n') if l.strip()]
        lines = [re.sub(r'^- ', '', l) for l in lines]
        return '> **%s**\n' % lab + '\n'.join('> ' + l for l in lines)
    out = head.rstrip() + '\n\n'
    for lab in ('放回日子里', '本章怎样会错'):
        if lab in tails: out += f'### {lab}\n\n' + tails[lab] + '\n\n'
    if '给想深究的人' in tails: out += box('给想深究的人', tails['给想深究的人']) + '\n\n'
    if '带走的话' in tails: out += box('带走的话', tails['带走的话']) + '\n\n'
    if '小账' in tails:
        ls = []
        for l in [re.sub(r'^- ', '', x) for x in tails['小账'].split('\n') if x.strip()]:
            if '——' not in l[:32] and '？' in l[:32]:
                q, _, a = l.partition('？'); l = q + '？——' + a
            ls.append(l)
        out += box('小账', '\n'.join(ls)) + '\n\n'
    if '想一想' in tails: out += box('想一想', tails['想一想']) + '\n\n'
    return out


def norm_sec(text):
    return re.sub(r'^### ◆\s*', '### ◆ ', text, flags=re.M)


def chapter(n):
    t = (B / f'ch-{n:02d}.md').read_text()
    first, _, body = t.partition('\n')
    m = re.match(r'^## 第(\d+)章　(.*)$', first)
    return f'## 第 {m[1]} 章　{m[2]}\n' + norm_sec(split_tail(body))


# ── 编 ──
for i, (a, b, title, intro) in enumerate(PARTS, 1):
    md = f'# {title}\n\n' + '\n\n'.join(intro) + '\n\n' + '\n\n'.join(chapter(n) for n in range(a, b + 1))
    (T / 'parts' / f'0{i}-第{"一二三四五六七"[i-1]}编.md').write_text(md)

# ── 导论 ──
t = (B / 'ch-导论.md').read_text()
first, _, body = t.partition('\n')
(T / 'front/01-导论.md').write_text('# ' + first.lstrip('# ').strip() + '\n' + norm_sec(split_tail(body)))

# ── 前置 ──
front = (B / 'front.md').read_text()
chunks = re.split(r'^## ', front, flags=re.M)[1:]
fm = {c.split('\n', 1)[0].strip(): c.split('\n', 1)[1] for c in chunks}
OLD = '章末依次是：放回日子里、本章怎样会错、带走的话、小账、想一想、给想深究的人。最后一段写给想往下深究的读者'
NEW = '章末依次是：放回日子里、本章怎样会错、给想深究的人，再收进三个小框：带走的话、小账、想一想。「给想深究的人」那一框写给想往下深究的读者'
assert OLD in fm['导读'], 'tail sentence changed'
fm['导读'] = fm['导读'].replace(OLD, NEW)
CP = """## 出版信息
| 项 | 内容 |
|---|---|
| 书名 | 《发生的时差——普通人都能懂的快慢之学》 |
| 著者 | 王德生 |
| 立题与裁定 | WDS博士 |
| 执笔 | 复合主体：WDS博士从二十种德麦国际专著碰撞立题，并作母题收窄、开写与各项口径的裁定；十位 AI（Claude）写手分章执笔，Claude 统稿；三审由 AI 编辑分段、跨章、终审完成 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 451 号 |
| ISBN | 979-8-90690-451-5 |
| 定价 | US$23.00 |
| 开本 | 170 mm × 240 mm |
| 字数 | 约 24.6 万汉字 |
| 版次 | 2026 年 10 月第 1 版 |

AI 协作声明：本书的母题，是从德麦国际 2026 年 10 月 19—20 日上架的二十种专著里读出来的，经一位未参与写作的评审独立审读后收窄；全书按一份共用底稿，由十位 AI（Claude）写手分章执笔，Claude 统稿与核对；立题、开写与待裁口径由 WDS博士裁定。六路径读作六种档位、123 原理读作「两快顶一慢」，是本书提出的读法，不是 SDE 的定论，书中只当地图用。

书中陪读的卢建国、周玉芬、卢晓、宋磊、宋可可一家五口，以及各章场景中出现的配角，均为虚构，不承担证据；书中的日子也是虚构的，从 2026 年九月开学一直写到入冬，不与本书成稿和出版的日子对应。二十本源书里的陪读人物照原书用名，注明书号。书中涉及身体、法律、理财的内容只讲道理，不构成医学、法律或投资建议。

全书结构：出版信息、题词、十分钟读完这本书、前言、导读、目录；导论与七编三十章；结语、参考书目、附录四件、后记。

版权所有　侵权必究
"""
EPI = """## 题词

【题词】不怕慢，怕卡档。

【题词署】——卢建国，开了三十一年货车
"""
out = CP + '\n' + EPI + '\n'
out += '## 十分钟读完这本书\n' + norm_sec(fm['十分钟读完这本书']) + '\n'
out += '## 前言\n' + norm_sec(fm['前言']) + '\n'
out += '## 导读\n' + norm_sec(fm['导读']) + '\n'
(T / 'front/00-前置.md').write_text(out)

# ── 结语、后置 ──
back = (B / 'back.md').read_text()
chunks = re.split(r'^## ', back, flags=re.M)[1:]
bm = {c.split('\n', 1)[0].strip(): c.split('\n', 1)[1] for c in chunks}
jy = bm['结语　留出那几个夜晚']
jy = re.sub(r'^\*\*带走的话\*\*：(.*)$', r'> **带走的话**\n> \1', jy, flags=re.M)
(T / 'back/09-结语.md').write_text('# 结语　留出那几个夜晚\n' + norm_sec(jy))

BIB = """# 参考书目

## 一、本书所读的二十种德麦国际专著

见附录四。

## 二、站内近邻

1. 王德生：《情商的本体论革命》，德麦国际专著第 282 号。
2. 王德生：《胜算》，德麦国际专著第 336 号。
3. 王德生：《属性纠缠论——实体属性发生学导论》，德麦国际专著第 396 号。
4. 王德生、Claude：《轮空》，sdeuniverses.com 学科通融长文，2026 年 8 月。
5. 胡志英：《初次对表》，sdeuniverses.com 学员专栏，2026 年 7 月。

## 三、外部文献

1. Ogburn, W. F. 1922. *Social Change with Respect to Culture and Original Nature*. New York: B. W. Huebsch.
2. Braudel, F. 1958. Histoire et sciences sociales : la longue durée. *Annales. Économies, Sociétés, Civilisations* 13(4).
3. Koselleck, R. 2000. *Zeitschichten: Studien zur Historik*. Frankfurt am Main: Suhrkamp.
4. Brand, S. 1999. *The Clock of the Long Now*. New York: Basic Books.
5. Gunderson, L. H. & Holling, C. S. (eds.) 2002. *Panarchy*. Washington, DC: Island Press.
6. Carpenter, S. R. & Brock, W. A. 2008. Adaptive capacity and traps. *Ecology and Society* 13(2).
7. Rosa, H. 2005. *Beschleunigung*. Frankfurt am Main: Suhrkamp.
8. Rosa, H. 2016. *Resonanz*. Berlin: Suhrkamp.
9. Gould, S. J. 1977. *Ontogeny and Phylogeny*. Cambridge, MA: Harvard University Press.
10. Hairston, N. G. Jr. et al. 2005. Rapid evolution and the convergence of ecological and evolutionary time. *Ecology Letters* 8.
11. Scheffer, M. et al. 2009. Early-warning signals for critical transitions. *Nature* 461: 53–59.
12. Ashwin, P. et al. 2012. Tipping points in open systems. *Phil. Trans. R. Soc. A* 370.
13. Lipsitz, L. A. & Goldberger, A. L. 1992. Loss of 'complexity' and aging. *JAMA* 267: 1806–1809.
14. Earn, D. J. D., Levin, S. A. & Rohani, P. 2000. Coherence and conservation. *Science* 290: 1360–1364.
15. Haldane, A. G. & May, R. M. 2011. Systemic risk in banking ecosystems. *Nature* 469: 351–355.
16. Ancona, D. & Chong, C.-L. 1996. Entrainment: Pace, cycle, and rhythm in organizational behavior. *Research in Organizational Behavior* 18.
17. Lupu, I. & Liu, S. 2025. The entrainment cycle: Understanding professionals' compliance with extreme work hours in professional service firms. *Accounting, Organizations and Society* 114: 101597.
18. Serhan, C. N. & Savill, J. 2005. Resolution of inflammation: the beginning programs the end. *Nature Immunology* 6: 1191–1197.
19. Wever, R. A. 1979. *The Circadian System of Man*. New York: Springer.
20. Lefebvre, H. 1992. *Éléments de rythmanalyse*. Paris: Syllepse.
21. Little, J. D. C. 1961. A proof for the queuing formula L = λW. *Operations Research* 9(3): 383–387.
"""
appx = '# 附录\n\n本书附录四件：白话小词典，怎样才算错与最便宜的跑法，前人与近邻一览，本书所读的二十本专著。\n\n'
for k in ['附录一　白话小词典', '附录二　怎样才算错，以及最便宜的跑法', '附录三　前人与近邻一览', '附录四　本书所读的二十本专著']:
    appx += '## ' + k + '\n' + re.sub(r'^### ', '### ', bm[k]) + '\n'
(T / 'back/10-后置.md').write_text(BIB + '\n' + appx + '\n# 后记\n' + bm['后记'])
print('ok')
