#!/usr/bin/env python3
"""第 592 号《耗在关系里的二十年，能不能变成收入？》（贝芳 著）：把三审定稿的分章稿装成 convert.py 认的 src/。
只做版式转换，不动论证文字。章题「# 第 N 章　T」→「## 第 N 章　T」；节「## T」→「### T」；编题与编首语取 parts.json。
用法：python3 tools/book-m592/mk_src.py /home/claude/hr/book
"""
import json, re, sys
from pathlib import Path
B = Path(sys.argv[1]); HERE = Path(__file__).parent; OUT = HERE / 'src'; OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.md'):
    f.unlink()
PARTS = json.loads((HERE / 'parts.json').read_text(encoding='utf-8'))
first_of = {v[2][0]: v for v in PARTS.values()}
SECNUM = re.compile(r'^[一二三四五六七八九十]+、')
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
    t = (B / n).read_text(encoding='utf-8').strip()
    assert '/home/' not in t and '待贝芳' not in t and '〔待核〕' not in t, n
    return t
t = rd('preface.md'); head, _, body = t.partition('\n'); assert head == '# 前言'
(OUT / 'qianyan.md').write_text('# 前言\n\n' + body.strip() + '\n', encoding='utf-8')
t = rd('intro.md'); head, _, body = t.partition('\n'); assert head.startswith('# 导论　'), head
(OUT / 'daolun.md').write_text(head + '\n\n' + demote(body), encoding='utf-8')
for i in range(1, 30):
    t = rd('ch%02d.md' % i); head, _, body = t.partition('\n')
    m = re.match(r'^# 第 (\d+) 章　(.+)$', head); assert m and int(m[1]) == i, head
    pre = ''
    if i in first_of:
        no, name, _, intro = first_of[i]
        pre = '# %s　%s\n\n%s\n\n' % (no, name, intro.strip())
    (OUT / ('ch%02d.md' % i)).write_text(pre + '## 第 %d 章　%s\n\n' % (i, m[2].strip()) + demote(body), encoding='utf-8')
t = rd('end.md'); head, _, body = t.partition('\n'); assert head.startswith('# 结语　'), head
(OUT / 'jieyu.md').write_text(head + '\n\n' + demote(body), encoding='utf-8')
t = rd('appendix.md'); assert t.startswith('# 附录\n')
(OUT / 'fulu.md').write_text(t + '\n', encoding='utf-8')
(OUT / 'zuozhe.md').write_text('''# 作者简介

**贝芳**，资深人力资源从业者。2004 年参加工作，二十多年来一直在郑州的房地产企业做人事，历任人事主管、人事行政经理（兼管计划运营）、人力资源部经理，2013 年起任一家房地产集团的人力资源总监至今，其间曾到集团下属物业公司任副总。招聘、薪酬、绩效、培训、员工关系、企业文化与组织建设，她都一手做过。早年随公司赴清华大学参加过一周的人力资源课程，此后自费考取二级企业人力资源管理师，自费学习绩效改进等课程，并系统学习过萨提亚模式心理咨询（一至三级）。

她做事的信条是“管理没有小事”和“做正确的事”。近年开始写作，运营个人公众号，也开始在公司之外提供简历优化、面试辅导、职场沟通、新人成长指导与 DISC 解读等服务。著有《你没交给企业的那一半》（德麦国际专著第 586 号）、《一个人养不出的清明》（第 587 号）、《孩子没交给学校的那一半》（第 588 号）。本书在王德生老师指导下完成。
''', encoding='utf-8')
(OUT / 'cankao.md').write_text('''# 参考文献

本书只转述以下著作与论文公认的论点，未标页码。站内专著的短引与转述，以各书原文为准。

### 站内专著

SITE_REFS

### 站外文献

Becker, G. S. (1964). *Human Capital*. Columbia University Press.（贝克尔《人力资本》）

Bloom, B. S. (Ed.). (1956). *Taxonomy of Educational Objectives: Handbook I, Cognitive Domain*. David McKay.（布鲁姆等《教育目标分类》）

Burt, R. S. (1992). *Structural Holes: The Social Structure of Competition*. Harvard University Press.（伯特《结构洞》）

Clark, A., & Chalmers, D. (1998). The extended mind. *Analysis*, 58(1), 7–19.（克拉克、查默斯《延展心智》）

Cowan, N. (2001). The magical number 4 in short-term memory. *Behavioral and Brain Sciences*, 24(1), 87–114.（考恩关于工作记忆容量的研究）

Csikszentmihalyi, M. (1990). *Flow: The Psychology of Optimal Experience*. Harper & Row.（契克森米哈伊《心流》）

Fisher, R., & Ury, W. (1981). *Getting to Yes*. Houghton Mifflin.（费希尔、尤里《谈判力》）

Fitzpatrick, R. (2013). *The Mom Test*. CreateSpace.（菲茨帕特里克《妈妈测试》）

Frost, P. J. (2003). *Toxic Emotions at Work: How Compassionate Managers Handle Pain and Conflict*. Harvard Business School Press.（弗罗斯特《职场中的有毒情绪》）

Granovetter, M. S. (1973). The strength of weak ties. *American Journal of Sociology*, 78(6), 1360–1380.（格兰诺维特《弱关系的力量》）

Ibarra, H. (2003). *Working Identity: Unconventional Strategies for Reinventing Your Career*. Harvard Business School Press.（伊巴拉《转行》）

Jensen, M. C., & Meckling, W. H. (1976). Theory of the firm: Managerial behavior, agency costs and ownership structure. *Journal of Financial Economics*, 3(4), 305–360.（詹森、麦克林关于委托代理的研究）

Kahn, R. L., Wolfe, D. M., Quinn, R. P., Snoek, J. D., & Rosenthal, R. A. (1964). *Organizational Stress: Studies in Role Conflict and Ambiguity*. Wiley.（卡恩等《组织压力》）

Kano, N., Seraku, N., Takahashi, F., & Tsuji, S. (1984). Attractive quality and must-be quality. *Journal of the Japanese Society for Quality Control*, 14(2), 39–48.（狩野纪昭等关于魅力质量的研究）

Kiyosaki, R. T. (1998). *Cashflow Quadrant*. TechPress.（清崎《富爸爸现金流象限》）

Klein, G. (1998). *Sources of Power: How People Make Decisions*. MIT Press.（克莱因《权力的来源》）

Knight, F. H. (1921). *Risk, Uncertainty and Profit*. Houghton Mifflin.（奈特《风险、不确定性与利润》）

Leiter, M. P., & Maslach, C. (2004). Areas of worklife: A structured approach to organizational predictors of job burnout. In *Research in Occupational Stress and Well-being*, Vol. 3. Elsevier.（莱特、马斯拉奇关于工作生活六领域的研究）

Marston, W. M. (1928). *Emotions of Normal People*. Kegan Paul.（马斯顿《常人的情绪》，DISC 的来源）

Nissenbaum, H. (2010). *Privacy in Context: Technology, Policy, and the Integrity of Social Life*. Stanford University Press.（尼森鲍姆《情境中的隐私》）

Nonaka, I., & Takeuchi, H. (1995). *The Knowledge-Creating Company*. Oxford University Press.（野中郁次郎、竹内弘高《创造知识的企业》）

Parasuraman, R., & Manzey, D. H. (2010). Complacency and bias in human use of automation: An attentional integration. *Human Factors*, 52(3), 381–410.（帕拉休拉曼、曼泽关于自动化偏差的综述）

Polanyi, M. (1966). *The Tacit Dimension*. Doubleday.（波兰尼《默会的维度》）

Ries, E. (2011). *The Lean Startup*. Crown Business.（里斯《精益创业》）
'''.replace('SITE_REFS', (HERE / 'site_refs.md').read_text(encoding='utf-8').strip()), encoding='utf-8')
print('src', len(list(OUT.glob('*.md'))))
