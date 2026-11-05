#!/usr/bin/env python3
"""第 588 号《孩子没交给学校的那一半》（贝芳 著）：把三审稿 v0.3 的分章稿装成 convert.py 认的 src/。
只做版式转换，不动论证文字：
  章题「# 第N章　T」→「## 第 N 章　T」；节「## 一、T」「## T」→「### T」（去掉节序号，书里没有按节序号互指）；
  编题与编首语取 parts.json（七编），装在每编第一章之前；
  导论、结语的「## 」→「### 」；附录「# 附录」下「## 附录N　T」保留为二级。
另写 zuozhe.md（作者简介）与 cankao.md（参考文献，只列正文括注过、已核书目的文献与站内专著）。
用法：python3 tools/book-m588/mk_src.py /home/claude/bf2/book
"""
import json
import re
import sys
from pathlib import Path

B = Path(sys.argv[1])
HERE = Path(__file__).parent
OUT = HERE / 'src'
OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.md'):
    f.unlink()
PARTS = json.loads((HERE / 'parts.json').read_text(encoding='utf-8'))
first_of = {v[2][0]: v for v in PARTS.values()}
SECNUM = re.compile(r'^(?:[一二三四五六七八九十]+、|\d+[\.、．]\s*)')


def fix(t):
    t = t.replace('以 /home/claude/bf2/body/ 下的原文为准', '以作者公众号的原文为准')
    assert '/home/' not in t and 'bf2' not in t
    return t


def demote(body):
    out = []
    for l in body.splitlines():
        if l.startswith('## '):
            out.append('### ' + SECNUM.sub('', l[3:].strip()))
        elif l.startswith('### '):
            out.append('#### ' + l[4:].strip())
        else:
            out.append(l)
    return '\n'.join(out).strip() + '\n'


def rd(n):
    return fix((B / n).read_text(encoding='utf-8')).strip()


# 前言
t = rd('preface.md')
head, _, body = t.partition('\n')
assert head == '# 前言', head
(OUT / 'qianyan.md').write_text('# 前言\n\n' + demote(body), encoding='utf-8')
# 导论
t = rd('intro.md')
head, _, body = t.partition('\n')
assert head.startswith('# 导论　'), head
(OUT / 'daolun.md').write_text(head + '\n\n' + demote(body), encoding='utf-8')
# 十八章
for i in range(1, 19):
    t = rd('ch%02d.md' % i)
    head, _, body = t.partition('\n')
    m = re.match(r'^# 第(\d+)章　(.+)$', head)
    assert m and int(m[1]) == i, head
    pre = ''
    if i in first_of:
        no, name, _, intro = first_of[i]
        pre = '# %s　%s\n\n%s\n\n' % (no, name, intro.strip())
    (OUT / ('ch%02d.md' % i)).write_text(pre + '## 第 %d 章　%s\n\n' % (i, m[2].strip()) + demote(body), encoding='utf-8')
# 结语与附录
t = rd('closing.md')
k = t.index('\n# 附录')
jy, fl = t[:k].strip(), t[k:].strip()
head, _, body = jy.partition('\n')
assert head.startswith('# 结语　'), head
(OUT / 'jieyu.md').write_text(head + '\n\n' + demote(body), encoding='utf-8')
assert fl.startswith('# 附录\n')
(OUT / 'fulu.md').write_text(fl + '\n', encoding='utf-8')

(OUT / 'zuozhe.md').write_text('''# 作者简介

**贝芳**，资深人力资源从业者，一个读高中的女孩的母亲。2004 年参加工作，二十多年来一直在郑州的房地产企业做人事，2013 年起任一家房地产集团的人力资源总监，其间曾到集团下属物业公司任副总。招聘、薪酬、绩效、培训、员工关系、企业文化与组织建设，她都一手做过。自费考取二级企业人力资源管理师，系统学习过萨提亚模式心理咨询（一至三级）。运营个人公众号，写职场，也写做母亲；在公司之外提供简历优化、面试辅导等服务。

她的第一部专著《你没交给企业的那一半》（德麦国际专著第 586 号）讲成年人没交给企业的那一半。本书从她写给自己的一份育儿问题清单出发，讲孩子没交给学校的那一半：关系、赚钱、学习这三样，在 AI 时代的家里怎样留出混沌与介生的地方。本书是她在王德生老师指导下完成的专著。
''', encoding='utf-8')

REFS = '''# 参考文献

本书只转述以下著作与论文公认的论点或已公开的研究发现，未引原文、未标页码，正文的转述不超出附录四所列要旨。中译名为本书行文所用。

### 站内专著

王德生．《SDE教育发生学导论》．德麦国际专著第 324 号．德麦国际出版社．

王德生．《SDE教育发生学导论》．德麦国际专著第 47 号．德麦国际出版社．

陈晓艳．《家庭教育的智慧》．德麦国际专著第 65 号．德麦国际出版社．

王德生．《AI 时代最需要学习的是什么？》．德麦国际专著第 192 号．德麦国际出版社．

阳涌，胡敏．《学习兴趣发生学导论》．王德生指导．德麦国际专著第 352 号．德麦国际出版社．

王德生．《AI时代教育的新典范：从因材施教到我材发生》．德麦国际专著第 400 号．德麦国际出版社．

王德生．《教育的产品是结晶》．德麦国际专著第 409 号．德麦国际出版社．

王德生．《点赞是借来的连接度：社交媒体时代，青少年的心为什么这么累》．德麦国际专著第 413 号．德麦国际出版社．

阳涌．《AI接管秩序之后》．王德生指导．德麦国际专著第 537 号．德麦国际出版社，2026．

贝芳．《你没交给企业的那一半》．王德生指导．德麦国际专著第 586 号．德麦国际出版社，2026．

### 站外文献

Barber, B. K. (1996). Parental psychological control: Revisiting a neglected construct. *Child Development*, 67(6), 3296–3319.（巴伯《父母心理控制：重访一个被忽视的概念》）

Baumrind, D. (1966). Effects of authoritative parental control on child behavior. *Child Development*, 37(4), 887–907.（鲍姆林德关于权威型教养的研究）

Buber, M. (1923). *Ich und Du*. Insel-Verlag.（布伯《我与你》）

Edmondson, A. (1999). Psychological safety and learning behavior in work teams. *Administrative Science Quarterly*, 44(2), 350–383.（埃德蒙森《工作团队中的心理安全与学习行为》）

Faber, A., & Mazlish, E. (1980). *How to Talk So Kids Will Listen & Listen So Kids Will Talk*. Rawson, Wade.（法伯、玛兹丽施《如何说孩子才会听，怎么听孩子才肯说》）

Ginott, H. G. (1965). *Between Parent and Child*. Macmillan.（吉诺特《孩子，把你的手给我》）

Gollwitzer, P. M. (1999). Implementation intentions: Strong effects of simple plans. *American Psychologist*, 54(7), 493–503.（戈尔维策《执行意图》）

Goodhart, C. A. E. (1975). Problems of monetary management: The U.K. experience. *Papers in Monetary Economics*, Vol. I. Reserve Bank of Australia.（古德哈特定律）

Gordon, T. (1970). *Parent Effectiveness Training*. Peter H. Wyden.（戈登《父母效能训练》）

Jackson, P. W. (1968). *Life in Classrooms*. Holt, Rinehart and Winston.（杰克逊《课堂生活》）

Kolb, D. A. (1984). *Experiential Learning: Experience as the Source of Learning and Development*. Prentice-Hall.（科尔布《经验学习》）

Koval, C. Z., vanDellen, M. R., Fitzsimons, G. M., & Ranby, K. W. (2015). The burden of responsibility: Interpersonal costs of high self-control. *Journal of Personality and Social Psychology*, 108(5), 750–766.（科瓦尔等《责任的负担》）

Livingstone, S., & Blum-Ross, A. (2020). *Parenting for a Digital Future: How Hopes and Fears about Technology Shape Children's Lives*. Oxford University Press.（利文斯通、布卢姆-罗斯《数字未来的养育》）

Michie, S., van Stralen, M. M., & West, R. (2011). The behaviour change wheel: A new method for characterising and designing behaviour change interventions. *Implementation Science*, 6, 42.（米奇等，行为改变轮与 COM-B 模型）

Piaget, J. (1985). *The Equilibration of Cognitive Structures: The Central Problem of Intellectual Development*. University of Chicago Press.（皮亚杰关于同化、顺应与平衡的学说；法文原著 1975）

Rozenblit, L., & Keil, F. (2002). The misunderstood limits of folk science: An illusion of explanatory depth. *Cognitive Science*, 26(5), 521–562.（罗森布利特、凯尔《解释深度错觉》）

Ryan, R. M., & Deci, E. L. (2000). Self-determination theory and the facilitation of intrinsic motivation, social development, and well-being. *American Psychologist*, 55(1), 68–78.（瑞安、德西，自我决定理论）

Strathern, M. (1997). 'Improving ratings': Audit in the British University system. *European Review*, 5(3), 305–321.（斯特拉森对古德哈特定律的通行表述）

Turkle, S. (2015). *Reclaiming Conversation: The Power of Talk in a Digital Age*. Penguin Press.（特克尔《重拾交谈》）

Valkenburg, P. M., Krcmar, M., Peeters, A. L., & Marseille, N. M. (1999). Developing a scale to assess three styles of television mediation: "Instructive mediation," "restrictive mediation," and "social coviewing." *Journal of Broadcasting & Electronic Media*, 43(1), 52–66.（Valkenburg 等《电视中介三种方式量表》）

Weinstein, N., & Ryan, R. M. (2010). When helping helps: Autonomous motivation for prosocial behavior and its influence on well-being for the helper and recipient. *Journal of Personality and Social Psychology*, 98(2), 222–244.（温斯坦、瑞安《当帮助真有帮助》）

Winnicott, D. W. (1958). The capacity to be alone. *International Journal of Psycho-Analysis*, 39, 416–420.（温尼科特《独处的能力》）

Zhang, S., Sullivan, D., Li, J., Cagiltay, B., Mutlu, B., Kirkorian, H., & Fawaz, K. (2025). Exploring families' use and mediation of generative AI: A multi-user perspective. arXiv:2504.09004.（作者只读过摘要）
'''
(OUT / 'cankao.md').write_text(REFS, encoding='utf-8')
print('src', sorted(p.name for p in OUT.glob('*.md')))
