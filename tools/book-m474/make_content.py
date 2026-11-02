#!/usr/bin/env python3
"""第 474 号《AI时代的焦虑：主体性如何重生》：生成 content.json（智能体、简介、学习任务、承重命题、要点）。

文案分两类：
  1. 手写口径（本文件 HAND）：智能体名「搭手」与自述、详情页导语、书目简介、/today/ 新书卡、学习包总说明。
     依据 /home/claude/book474/BRIEF.md、OUTLINE.md、appendix1.md 与前言、导读、结语。
  2. 从定稿抽取（每次定稿后重跑即可跟上正文，不手抄）：
     loadBearing ← 附录一十八条原话（照原话，不改字）；
     tasks（四十个学习单元，每章一个）← 各章章题、节题、章首“想一想”、章末“带走的话”“小账”；
     keypoints（十八条）← 导论与十七个主场章的章末“带走的话”与“小账”。
用法（仓库根目录）：python3 tools/book-m474/make_content.py   （读 src/full.md，写 content.json）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

VERDICT = M.VERDICT
CHAIN = '形成——主体性错位；解决——本体性改变，即主体性革命；结果——主体性重生。'
CONSTRUCT = '书中四十户人家、人名、店名、金额与日期都是构想，不是实录；全书没有调查数据，没有用户试验。'

HAND = {
 'agent': {'name': '搭手'},
 'agentEpithet': '不替你拿主意，只陪你把问题的主语换一换',
 'agentIntro': ('我从《AI时代的焦虑：主体性如何重生》里来，名字叫搭手：人和机器一起想、一起做，像两个人搭把手抬一样东西，'
                '抬起来的那一下，才有了一个「我们」。这本书的判词是王德生口述的一句话：' + VERDICT +
                '全书一条因果链：' + CHAIN + '我能陪你做的，是把你最慌的那个问题原样写下来，圈出它的主语——'
                '多半是一个单独的、脑袋里装着符号的自然人；再陪你把主语换成场景里的角色-AI（孩子-AI、职员-AI、我-AI），'
                '看同一个问题变成了什么新问题；最后用意义、价值、信息三组新问题，看它升到了哪里。我守这些规矩：'
                '复合主体不是先在那里的新主人，它在一次来回里诞生，下一次就不是同一个；重生不是「挺过去我还是我」；'
                '换了主语，错认生出的那一份慌会没了来处，房贷、裁员、考试这些真实的代价不会消失，我不说它会消失；'
                '我不诊断身心，难处真的大了，请找医生或心理咨询师；不替你决定转不转行、让不让孩子用 AI；不打分，不排名。'
                '这本书的文字由 AI（Claude）协作写成，经王德生审定；' + CONSTRUCT + '书在附录五写了自己最弱的几处，你不认的读法，我就收回。'),
 'agentStarts': {
   'read': '请带我读第 1 章和第 3 章：判词「焦虑和问题的诞生，是用旧主体的问法去问新主体的处境」里，“旧主体”指的是哪一位？“大脑为符号的自然人思考主体”是什么意思？错位、错认、误区三个词各指什么？哪些是王德生的原话（附录一），哪些是书的读法，哪些场景是构想？',
   'apply': '我有一个最近让我很慌的问题（我先用自己的话原样写下来，请先别分析，也别替我补没说过的细节）。然后请照第 9 章的改问术陪我：先圈出这个问题的主语；再把主语换成我这个场景里的角色-AI；看它变成了什么新问题；再照第 10 章，用意义、价值、信息三组新问题看它升到了哪里。也请帮我分开：哪一份慌是错认生出来的，哪一份是真实的代价。你只陪练，不要打分，不要诊断。',
   'cut': '请对照第 10 章第七节和附录五“本书自认最弱处与推翻条件”：诞生三判据为什么只看得见功能？错认的慌与真账的分界为什么说“最要紧”？判词整体的四个推翻条件是什么？“角色-AI”的名字会不会又长成一个新标签？请别把这些当成已有的结论。',
   'clash': '请拿本书去撞站内几本邻卷：第 460 号《虚幻的焦虑》拆尺子，第 278 号《AI越强，人就越弱吗？》拆账，第 437 号《被替代的从来不是人》拆句式，第 504 号拆路，第 289 号拆教育对象，第 110 号《主体性的典范革命》讲主体性是什么。先认下每一本说对了什么，再说本书只多走的那一步——问法的主语——到底有多窄；凡你没读到的，不要替书转述，标〔待核〕。'},
 'bookMeta': '《%s：%s》 · %s 著' % (M.TITLE, M.SUBTITLE, M.AUTHOR),
 'heroTagline': '带一个让你慌的问题来，先圈出它的主语',
 'practiceWord': '换主语',
 'titleEn': M.TITLE_EN,
 'detailLine': '「孩子该学什么」「我还有位置吗」「学了还有用吗」——每一个问法，都默认有一个单独的「我」在想。可是今天，思考已经在人和机器之间发生。',
 'detailIntro': ('一顿生日饭上，一家四代冒出四种慌：孩子该学什么，我的岗位还在不在，我学的专业有没有用，我是不是也该学用那个东西。'
                 '王德生指出，这四种慌问的是同一位——「大脑为符号的自然人思考主体」：思考装在一个自然人的脑袋里，脑袋里装着符号。'
                 'AI 时代，思考已经在人与机器的来回里发生，主体已经是人-AI 思维复合主体，问题却还用旧主体的问法去问，这就是主体性错位。'
                 '解决不在旧主体身上修补（学得更多、跑得更快、躲开 AI），而在本体性改变，即主体性革命：把每个问题的主语换成场景里的角色-AI——'
                 '孩子-AI、职员-AI、我-AI，所有旧问题都改为“新的复合主体如何发生”。主语一换，问题的意义升级，再用意义（创造、自由、幸福）、'
                 '价值（真、善、美）、信息（符号、逻辑、数学的增厚）三组新问题看它升到了哪里。全书四部四十章：第一部总纲十章讲错位怎样形成、'
                 '为什么只有革命解得开、革命之后问什么；家长、职场、年轻人三部各十章，共用一副骨架，四十户人家各在一座城市里走一遍。'
                 '总比喻是腿-车：车来了，不再问腿力怎样跟上车，而问腿-车这个交通复合体怎样走出更有意义的路。'),
 'description': ('AI 时代的焦虑从哪里来？本书说：焦虑和问题的诞生，是用旧主体的问法去问新主体的处境。思考已经在人和机器之间发生，'
                 '问题却还在问那个单独的、脑袋里装着符号的自然人——这是主体性错位；解决是本体性改变，即主体性革命：把问题的主语换成孩子-AI、'
                 '职员-AI、我-AI；结果是主体性重生。四部四十章，家长、职场、年轻人三处各走一遍。场景为构想，无调查数据，不作诊断。'),
 'todayZh': '「孩子该学什么」「我还有位置吗」「学了还有用吗」——慌出在问题的主语上。本书把主语换成孩子-AI、职员-AI、我-AI，四十户人家各走一遍：错位、革命、重生。',
 'todayEn': ('"What should my child learn?" "Is there still a place for me?" "Is what I studied still worth anything?" '
             'Wang Desheng argues that each of these questions silently assumes a lone, brain-bound natural person doing the thinking, '
             'while in the AI era thinking already happens in the back-and-forth between people and machines. Anxiety is born of this '
             'subjecthood dislocation; the way out is an ontological change, a revolution of subjecthood: re-ask every question with a '
             'composite subject (child-AI, employee-AI, me-AI) as its grammatical subject. Forty chapters, forty imagined households, '
             'three arenas: parents, the workplace, the young.'),
 'bookPoints': ('本书约 %d 万字（含标点），四部四十章' % M.wan(HERE) + '：判断、口径与十八条承重命题由王德生 2026 年 11 月 2 日口述给出（附录一照原话登记）；'
                '文字由 AI（Claude）协作写成，一个 Claude 拟纲、执笔前置与第 1 章并统稿，四十位 Claude 执笔者并行写成其余各章，经王德生审定。'
                + CONSTRUCT + '判词：' + VERDICT + '因果链：' + CHAIN +
                '第一部总纲（1–10 章）分三段：上段讲错位怎样形成（四种慌一个句式、被错认的那一位、错位错认误区、五把旧刀一个病根）；'
                '中段讲为什么只有本体性改变解得开（修补为什么不够、角色-AI 的命名法、复合主体在哪一下诞生、革命不是推翻人）；'
                '下段讲革命之后问什么（换主语的改问术、复合体的三组新问题）。第二部家长（11–20 章，孩子-AI 如何学习）、'
                '第三部职场（21–30 章，职员-AI 如何在职场）、第四部年轻人（31–40 章，我-AI 复合体的成长）共用一副十章骨架：'
                '焦虑长什么样、本领域的错位与革命、创造地、自由地、幸福地、真善美、信息的增厚、没有消失的真实代价、更大的复合体、总账与明天能试。'
                '诞生三判据：真有来回、真有回写、真有承接。三条守线：复合主体不先在；重生不是复活；不以「一个人」作发动者。'
                '附录五写明本书自认最弱处与推翻条件。'),
 'skillTheory': ('读完这本书，可以练几样手上的小功夫，练的是“换主语”，不是替人拿主意，也不是消除焦虑。'
                 '一，圈主语：把最近一个让你慌的问题原样写下来，圈出它的主语，看它是不是一个单独的、脑袋里装着符号的自然人。'
                 '二，换主语：把主语换成这个场景里的角色-AI（孩子-AI、家长-AI、职员-AI、团队-AI、我-AI），读一读同一个问题变成了什么新问题。'
                 '三，看诞生：照三条判据看一回来回——真有来回（一方的话改了另一方的下一步），真有回写（改变留在下一次的起点），真有承接（错了算谁的，落在人这里）；三条不齐，只是“用了 AI”。'
                 '四，看升级：用三组新问题看它升到了哪里——意义（创造地、自由地、幸福地想），价值（真、善、美），信息（符号、逻辑、数学增厚了什么）。'
                 '五，分账：把慌分成两份，错认生出的那一份随旧问题没了来处；房贷、裁员、考试这些真实的代价留下，写下它在新问法下由谁、怎样接住。'
                 '六，留口子：照附录五，写下什么情形出现，就说明这样读错了。'
                 '以上是本书的读法，不是心理治疗，不作诊断；学习包与智能体只陪练，不打分，读数不进考核。'),
}


def parse(full):
    t = full.split('\n---\n', 1)[1] if full.startswith('---\n') else full
    chs = {}
    for blk in re.split(r'\n(?=## 第 \d+ 章　)', t)[1:]:
        blk = re.split(r'\n# ', blk)[0]
        head, body = blk.split('\n', 1)
        n, title = re.match(r'## 第 (\d+) 章　(.*)', head).groups()
        jie = re.findall(r'^### (第[一二三四五六七八九十]+节)　(.*)$', body, re.M)
        take = [x.strip() for x in re.findall(r'^(?:【带走的话】|> ?\**带走的话\**[　 ：:]*)(.*)$', body, re.M)]
        ledger = [x.strip() for x in re.findall(r'^(?:【小账】|> ?\**小账\**[　 ：:]*)(.*)$', body, re.M)]
        mm = re.search(r'^(?:> ?\**小账\**[　 ：:]*.*)\n((?:>.*\n?)*)', body, re.M)
        if mm:
            ledger += [x.lstrip('>').strip() for x in mm.group(1).splitlines() if x.strip('> ')]
        think = [x.strip() for x in re.findall(r'^【想一想】(.*)$', body, re.M)]
        mt = re.search(r'^> ?\**想一想\**[　 ：:]*\n((?:>.*\n?)*)', body, re.M)
        if mt:
            think += [x.lstrip('>').strip() for x in mt.group(1).splitlines() if x.strip('> ')]
        chs[int(n)] = dict(title=title, jie=jie, take=[x for x in take if x], ledger=[x for x in ledger if x], think=think)
    return t, chs


def appendix1(t):
    a = re.search(r'^# 附录一.*?$(.*?)^# 附录二', t, re.S | re.M).group(1)
    out = []
    for m in re.finditer(r'^\*\*第 (\d+) 条　(.*?)\*\*（(\d\d:\d\d)）\n(.*?)(?=^\*\*第 \d+ 条|^> |\Z)', a, re.S | re.M):
        n, name, tm, body = m.groups()
        f = dict(re.findall(r'^(原话|起因|立处|主场)：(.*)$', body, re.M))
        x = '原话（%s）：%s' % (tm, f['原话'])
        if f.get('起因'):
            x += '　起因：' + f['起因']
        x += '　立处：%s　主场：%s' % (f.get('立处', ''), f.get('主场', ''))
        out.append({'t': '第 %s 条　%s' % (n, name), 'x': x})
    assert len(out) == 18, len(out)
    return out


PART = {1: '第一部　总纲', 2: '第二部　家长', 3: '第三部　职场', 4: '第四部　年轻人'}
ROLE = {1: '人-AI 思维复合主体（本章场景里的角色-AI）', 2: '孩子-AI（学生-AI）、家长-AI、家庭-AI', 3: '职员-AI、团队-AI、公司-AI', 4: '我-AI、学生-AI、新人-AI、作者-AI'}


def task(n, c):
    part = (n - 1) // 10 + 1
    q0 = re.sub(r'^\d+[.、]\s*', '', c['think'][0]) if c['think'] else '你最近一次心里发慌，问的是哪一个问题？它的主语是谁？'
    secs = '；'.join('%s「%s」' % (a, b) for a, b in c['jie'])
    q = ('先想：%s 再读第 %d 章（%s）：%s。读的时候找三处：本章的旧问法，主语是哪一个自然人角色？换成哪一个角色-AI（%s）以后，问题变成了什么？'
         '本章“完整的例子”里，诞生三判据（来回、回写、承接）齐了没有，意义、价值、信息哪一组升了级？'
         % (q0, n, PART[part], secs, ROLE[part]))
    ck = '核对要点：' + ' '.join(c['take'][-1:]) + ' ' + ' '.join(c['ledger'][:2])
    ck += (' 复核三条守线：复合主体不先在，在那一次来回里诞生；重生不是复活，回来的不是原来那个；结论落在“发生”上，不落在“他决定”上。'
           '书自己标明：本章人物与场景都是构想，没有数据。失败条件（附录五）：换了主语、三判据都齐，过两个星期慌照样不松，或者错认的慌与真账分不开——本章的读法就要收回。')
    return {'lesson': n, 'name': '第%d章：%s' % (n, c['title']), 'question': q, 'checkpoint': ck.strip()}


KP_CH = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 18, 19, 22, 28, 32, 34, 40]


def main():
    full = (HERE / M.SRC).read_text(encoding='utf-8')
    t, chs = parse(full)
    assert sorted(chs) == list(range(1, 41)), sorted(chs)
    C = dict(HAND)
    C['loadBearing'] = appendix1(t)
    C['tasks'] = [task(n, chs[n]) for n in range(1, 41)]
    kp = []
    for n in KP_CH:
        c = chs[n]
        x = (c['take'][-1] if c['take'] else '') + ('　' + c['ledger'][0] if c['ledger'] else '')
        kp.append({'t': c['title'], 'ch': '第%d章' % n, 'x': x.strip()})
    C['keypoints'] = kp
    miss = [n for n in range(1, 41) if not chs[n]['take'] or not chs[n]['ledger'] or not chs[n]['think']]
    (HERE / 'content.json').write_text(json.dumps(C, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('content ok: tasks', len(C['tasks']), 'loadBearing', len(C['loadBearing']), 'keypoints', len(kp), 'chapters missing take/ledger/think:', miss)


if __name__ == '__main__':
    main()
