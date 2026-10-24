#!/usr/bin/env python3
"""第 512 号《班级之美：同一性谱系发生学》（工具链由第 421 号改来；原拟第 507 号，改号第 512 号）：把统稿全文（/home/claude/banji-zhimei/full.md）
转成 220 版式工具链（照第 421 号）的分卷稿。只做格式转换，不动正文文字。
用法：python3 tools/book-m512/convert.py /home/claude/banji-zhimei/full.md
产物：front/00-前置.md、front/01-导论.md、parts/01—08、back/09-结语.md、back/10-后置.md

格式约定（全书一致）：
- 节标题 `### 1.1　X`（导论 `## 0.1　X`、结语 `## 一、X`）一律转成 `### ◆ 1.1　X`，保留原编号，便于正文里「导论 0.3」「第 24.1 节」之类的互指；
- 「这一章的问题」各种写法统一成 `> **这一章的问题**：…`；
- 章末「带走的话」「小账」「明天可以试的一件小事」（### 标题式或 **粗体行** 式）统一转成引用块；
- 分隔线 `---` 去掉（分卷与分章已由版式承担）。
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/banji-zhimei/full.md')

CPMETA = [
    ('书名', '《班级之美：同一性谱系发生学》'),
    ('著者', '柴翱　刘华杰'),
    ('指导', '王德生'),
    ('执笔', '复合主体：柴翱、刘华杰著；王德生指导立题、口述承重命题与口径；文字由 AI（Claude）协作成稿，二十路分章执笔、七路独立质检、一路跨章统稿'),
    ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
    ('编号', '德麦国际专著第 512 号'),
    ('ISBN', '979-8-90690-512-3'),
    ('定价', 'US$23.00'),
    ('开本', '170 mm × 240 mm'),
    ('字数', '约 26 万字'),
    ('版次', '2026 年 10 月第 1 版'),
]
CPNOTES = [
    'AI 协作声明：本书的立题、判词与口述命题由指导老师王德生给出，著者柴翱、刘华杰署名；文字在其指令下由 AI（Claude）协作成稿，并经独立质检与统稿。书中所引各家理论只述大意，不替任何学者编原话。',
    '书中初二（3）班及陪读人物、课堂场景均为构想，不当证据。书中的读数只给班级自看，不进考核；本书不作心理或医学诊断，不对具体学校与现行政策表态。',
    '全书结构：出版信息、作者介绍、前置（十分钟读完这本书、前言、导读）、目录；导论；八编三十章；结语、参考书目、附录六件。',
    '版权所有　侵权必究',
]
AUTHOR_BIO = [
    '柴翱，本书作者之一，另著有德麦国际专著第 506 号《土·石·煤——作文的发生学》。',
    '刘华杰，北京师范大学教育学博士，华南师范大学教师教育学部硕士生导师。研究领域为教师伦理与师德建设、班主任专业成长、学校德育与班级管理、家庭教育。另著有德麦国际专著第 436 号《好老师为什么做不动——师德的精益求精》、第 452 号《谁在给善记账——学校制度的道德发生学》。',
    '王德生（指导），SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人、董事长，中国科学院计算数学博士。',
]

MARKERS = ('带走的话', '小账', '明天可以试的一件小事')
CN = '一二三四五六七八'


def marker_of(l):
    s = l.strip()
    m = re.fullmatch(r'(?:### |\*\*)(带走的话|小账|明天可以试的一件小事)(?:\*\*)?', s)
    return m[1] if m else None


def question(l):
    """「这一章的问题」五种写法 → `> **这一章的问题**：X`。"""
    s = l.strip()
    m = re.match(r'^(\*\*)?这一(章|编)的问题(\*\*)?[：:](\*\*)?\s*(.*)$', s)
    if not m:
        return None
    body = m[5]
    if m[1] and not m[3] and not m[4] and body.endswith('**'):
        body = body[:-2]
    return '> **这一%s的问题**：%s' % (m[2], body.strip())


def fmt(text, bib=False):
    out = []
    L = text.split('\n')
    i = 0
    while i < len(L):
        l = L[i]
        if l.strip() == '---':
            i += 1; continue
        mk = marker_of(l)
        if mk:
            out.append('> **%s**' % mk); i += 1
            while i < len(L):
                x = L[i]
                if x.startswith('#') or x.strip() == '---' or marker_of(x):
                    break
                if x.strip():
                    out.append('> ' + re.sub(r'^- ', '', x.strip()))
                i += 1
            out.append('')
            continue
        q = question(l)
        if q:
            out.append(q); i += 1; continue
        if not bib:
            m = re.match(r'^#{2,3} (\d+\.\d+|[一二三四五六七八九十]+、)(.*)$', l)
            if m:
                out.append('### ◆ ' + m[1] + m[2]); i += 1; continue
        out.append(l); i += 1
    s = '\n'.join(out)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip() + '\n'


BIB = """# 参考书目

只收正文实际提到、且书名与出版信息经核对的著作。正文只述其大意，不引原话。出版年份或出版社拿不准的，只写作者与书名。

### 站内专著

- 王德生．AI时代教育的新典范：从因材施教到我材发生——为我的土壤专门创造一粒种子．新加坡：德麦国际出版社，2026．（德麦国际专著第 400 号）
- 王德生．技术的“我”——AI时代职业教育的典范转移．新加坡：德麦国际出版社，2026．（德麦国际专著第 329 号）
- 王德生．可以出错的工位——德国职业教育为什么成功．新加坡：德麦国际出版社，2026．（德麦国际专著第 335 号）
- 王德生．知识的谱系发生——从“我们的知识”到“我的知识”．新加坡：德麦国际出版社，2026．（德麦国际专著第 337 号）
- 王德生．新文明诞生——同一性谱系化．新加坡：德麦国际出版社，2026．（德麦国际专著第 402 号）
- 王德生．教育的产品是结晶——AI 时代，为什么学了却没学会．新加坡：德麦国际出版社，2026．（德麦国际专著第 409 号）
- 刘华杰．好老师为什么做不动——师德的精益求精．新加坡：德麦国际出版社，2026．（德麦国际专著第 436 号）
- 刘华杰．谁在给善记账——学校制度的道德发生学．新加坡：德麦国际出版社，2026．（德麦国际专著第 452 号）
- 王德生．爱在创造中成全——把忍耐变成创造，把统一性升维为同一性谱系．新加坡：德麦国际出版社，2026．（德麦国际专著第 453 号）
- 王德生．SDE平台：慧店的诞生——让天下没有难发生的知识．新加坡：德麦国际出版社，2026．（德麦国际专著第 491 号）
- 王德生．化冲突——谱系社会的新知识发生器．新加坡：德麦国际出版社，2026．（德麦国际专著第 496 号）
- 王德生．知识分子向何处去？——从公共知识的转译者到谱系知识的立谱者．新加坡：德麦国际出版社，2026．（德麦国际专著第 505 号）

### 中文文献

- 佐藤学．静悄悄的革命——课堂改变，学校就会改变．李季湄，译．长春：长春出版社，2003．

### 外文文献

**教育学与学习科学**

- Comenius J A．Didactica Magna（《大教学论》）．Amsterdam，1657．
- Vygotsky L S．Mind in Society: The Development of Higher Psychological Processes（《社会中的心智》）．Cambridge, MA: Harvard University Press，1978．
- Piaget J．L'équilibration des structures cognitives: problème central du développement（《认知结构的平衡化》）．Paris: Presses Universitaires de France，1975．
- Whitehead A N．The Aims of Education and Other Essays（《教育的目的》）．New York: Macmillan，1929．
- Freudenthal H．Mathematics as an Educational Task（《作为教育任务的数学》）．Dordrecht: Reidel，1973．
- Doise W, Mugny G．The Social Development of the Intellect（《智力的社会发展》）．Oxford: Pergamon Press，1984．
- Engeström Y．Learning by Expanding: An Activity-Theoretical Approach to Developmental Research（《拓展性学习》）．Helsinki: Orienta-Konsultit，1987．
- Lave J, Wenger E．Situated Learning: Legitimate Peripheral Participation（《情境学习：合法的边缘性参与》）．Cambridge: Cambridge University Press，1991．
- Moll L C, Amanti C, Neff D, González N．Funds of knowledge for teaching: Using a qualitative approach to connect homes and classrooms（《为教学所用的知识储备》）．Theory Into Practice，1992，31(2)：132–141．
- Ball D L．With an eye on the mathematical horizon: Dilemmas of teaching elementary school mathematics（《着眼于数学的地平线：小学数学教学的两难》）．The Elementary School Journal，1993，93(4)：373–397．
- Lampert M．Teaching Problems and the Problems of Teaching（《教学问题与教学中的问题》）．New Haven: Yale University Press，2001．
- Engle R A, Conant F R．Guiding principles for fostering productive disciplinary engagement: Explaining an emergent argument in a community of learners classroom（《促进有成效的学科投入的指导原则》）．Cognition and Instruction，2002，20(4)：399–483．
- Scardamalia M, Bereiter C．Knowledge building: Theory, pedagogy, and technology（《知识建构：理论、教学法与技术》）// Sawyer R K．The Cambridge Handbook of the Learning Sciences．New York: Cambridge University Press，2006：97–115．
- Davis B, Sumara D．Complexity and Education: Inquiries into Learning, Teaching, and Research（《复杂性与教育》）．Mahwah, NJ: Lawrence Erlbaum，2006．
- Kapur M．Productive failure（《有成效的失败》）．Cognition and Instruction，2008，26(3)：379–424．

**哲学、语言与社会理论**

- Mauss M．Essai sur le don（《礼物》）．L'Année sociologique，1925．
- Husserl E．Die Frage nach dem Ursprung der Geometrie als intentional-historisches Problem（《几何学的起源》）．Revue internationale de philosophie，1939．
- Wittgenstein L．Philosophische Untersuchungen（《哲学研究》）．Oxford: Blackwell，1953．
- Kuhn T S．The Structure of Scientific Revolutions（《科学革命的结构》）．Chicago: University of Chicago Press，1962．
- Bakhtin M M．The Dialogic Imagination: Four Essays（《对话的想象》）．Austin: University of Texas Press，1981．
- Honneth A．Kampf um Anerkennung（《为承认而斗争》）．Frankfurt am Main: Suhrkamp，1992．
- Wertsch J V．Mind as Action（《行动中的心智》）．New York: Oxford University Press，1998．

**生态学与图论**

- Fiedler M．Algebraic connectivity of graphs（《图的代数连通度》）．Czechoslovak Mathematical Journal，1973，23(2)：298–305．
- Gunderson L H, Holling C S．Panarchy: Understanding Transformations in Human and Natural Systems（《扰沌：理解人类与自然系统中的转变》）．Washington, DC: Island Press，2002．
"""


def main():
    raw = SRC.read_text()
    raw = re.sub(r'<!--.*?-->', '', raw, flags=re.S)
    i_qz = raw.index('\n# 前置\n')
    i_dl = raw.index('\n# 导论　')
    i_p = [m.start() for m in re.finditer(r'\n# 第[一二三四五六七八]编　', raw)]
    i_jy = raw.index('\n# 结语　')
    i_fl = raw.index('\n# 附录\n')
    assert len(i_p) == 8 and i_qz < i_dl < i_p[0] < i_jy < i_fl

    qianzhi = raw[i_qz:i_dl].strip()
    daolun = raw[i_dl:i_p[0]].strip()
    parts = [raw[a:b].strip() for a, b in zip(i_p, i_p[1:] + [i_jy])]
    jieyu = raw[i_jy:i_fl].strip()
    fulu = raw[i_fl:].strip()

    # 前置：去掉「# 前置」一行；「前言·X」改成「前言　X」（版式按全角空格拆主副题）
    qz = qianzhi.split('\n', 1)[1]
    qz = re.sub(r'^## 前言·', '## 前言　', qz, flags=re.M)
    cp = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in CPMETA) + '\n' + '\n\n'.join(CPNOTES)
    au = '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_BIO)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text(cp + '\n\n' + au + '\n\n' + fmt(qz))
    (HERE / 'front/01-导论.md').write_text(fmt(daolun))
    (HERE / 'parts').mkdir(exist_ok=True)
    nums = []
    for k, p in enumerate(parts):
        f = fmt(p)
        (HERE / ('parts/%02d-第%s编.md' % (k + 1, CN[k]))).write_text(f)
        nums += [int(x) for x in re.findall(r'^## 第 (\d+) 章　', f, re.M)]
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/09-结语.md').write_text(fmt(jieyu))
    (HERE / 'back/10-后置.md').write_text(BIB.strip() + '\n\n' + fmt(fulu, bib=True))
    assert nums == list(range(1, 31)), nums
    print('ok: 8 parts, chapters', nums[0], '-', nums[-1])


if __name__ == '__main__':
    main()
