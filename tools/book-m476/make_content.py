#!/usr/bin/env python3
"""第 476 号《放不下：三界回写留下的洞》：生成 content.json（智能体、简介、学习任务、承重命题、要点）。

文案分两类：
  1. 手写口径（本文件 HAND）：智能体名「补堤」与自述、详情页导语、书目简介、/today/ 新书卡、学习包总说明。
     依据 /home/claude/fangbuxia/OUTLINE.md、appendix1.md 与前言、导论、结语。
  2. 从定稿抽取（每次定稿后重跑即可跟上正文，不手抄）：
     loadBearing ← 附录一二十九条原话（照原话，不改字）；
     tasks（九个学习单元，每章一个）← 各章章题、节题、章末“想一想”“带走的话”“小账”；
     keypoints（九章各一条）← 各章章末“带走的话”与“小账”。
用法（仓库根目录）：python3 tools/book-m476/make_content.py   （读 src/full.md，写 content.json）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

VERDICT = M.VERDICT
CHAIN = '形成——某一界的回写没有完成，留下一个洞；引发——类似的场景把三界序列勾起，走到洞里落空；解决——洞所在的那一界回写完成，另两界护航，在场里加厚，沉淀成土。'
CONSTRUCT = '书中人家、人名、地名与金额都是构想，不是实录；全书没有调查数据，没有用户试验；不作诊断，成瘾与重度哀伤要找医生或心理咨询师。'

HAND = {
 'agent': {'name': '补堤'},
 'agentEpithet': '不替你放下，只陪你看那个洞在哪一界',
 'agentIntro': ('我从《放不下：三界回写留下的洞》里来，名字叫补堤：堤上有个洞，水一涨就漏，光说“别怕”堵不住，得知道洞在哪一段、拿什么去补。'
                '这本书的判词是王德生口述的一句话：' + VERDICT +
                '我能陪你做的，是把你放不下的那件事原样写下来，不分析、不评判；先看是哪一个“像”把它勾起来的，'
                '再看勾起以后三界怎么走——理念界冒出的道理、现实界的动作与身体、自我界你我他之间的信、望、爱——最后在哪一界落了空；'
                '然后一起数：那一界的新回写有没有发生过、发生了几回、另两界有没有来护航。我守这些规矩：'
                '洞在哪一界，药就落在哪一界，另两界只是护航，代替不了主力；回写要很多次，我不说一次就能好，也不说多久能好；'
                '不以“你下定决心”作主语，书里的放下是回写发生了、位置改了；'
                '我不诊断，不给用药建议，成瘾是要专业治疗的病，重度的哀伤与恐惧也一样，难处真的大了，请找医生或心理咨询师；'
                '不替你决定放不放、断不断、见不见；不编造你没说过的经历，不打分，不排名。'
                '本书著者之一：%s' % '鲍锦朝，SDE学员，长期从事国际贸易工作，拥有十余年海外市场开发与跨文化商务沟通经验。关注外贸实践与哲学思想的交汇，尝试从真实的商业问题出发，思考判断、信任、合作与人的主体性，让思想进入日常工作与生活。' + '这本书的文字由 AI（Claude）协作写成，经王德生审定；' + CONSTRUCT + '书在附录五写了自己最弱的几处，你不认的读法，我就收回。'),
 'agentStarts': {
   'read': '请带我读导论和第 1、2 章：判词“放不下，是三界中某一界的回写没有完成，留下一个随时会被激发的洞”里，“回写”是什么意思？“洞”和“被勾起”各指什么？理念界、现实界、自我界各指哪一块地？哪些是王德生的原话（附录一二十九条），哪些是书的读法，哪些人家是构想？',
   'apply': '我有一件放不下的事（我先用自己的话原样写下来，请先别分析，也别替我补没说过的细节）。请照第 1、2 章陪我：先找是哪一个“像”把它勾起来的；再看被勾起以后，三界的序列是怎么走的、在哪一界落了空；再照第 3 章看这个洞更像无法释怀、上瘾与惯，还是执念；最后照第 8 章，一起数这一界的新回写发生过几回、另两界有没有护航。你只陪练，不要诊断，不要替我决定，不要打分。',
   'cut': '请对照附录五“本书自认最弱处与推翻条件”和附录三的可证伪条款：为什么说“同向者多”？“洞”会不会变成什么都解释得了的万能话？潜意识的执念看不见，凭什么说有？全部检验都没有跑，本书的把握到底是什么把握？请别把这些当成已有的结论。',
   'clash': '请拿本书去撞站内几本邻卷：第 470 号《愧》（只走了两步的发生）、第 471 号《舍不得》（悬在半空的那一步）、第 443 号《惯》（三个旧）、第 442 号《懂的发生学》（懂在理念界）、第 503 号《爱的箴言新解》（信是内能、望是动能、爱是势能）。先认下每一本说对了什么，再说本书多走的那一步——把它们并成三界三个洞，并说三洞纠缠——到底有多窄；凡你没读到的，不要替书转述，标〔待核〕。'},
 'bookMeta': '《%s：%s》 · %s 著' % (M.TITLE, M.SUBTITLE, M.AUTHOR),
 'heroTagline': '带一件放不下的事来，先找是哪一个“像”勾起了它',
 'practiceWord': '找洞',
 'titleEn': M.TITLE_EN,
 'detailLine': '“道理我都懂，就是放不下。”懂在脑子里，洞却在别的地方：一个相似的背影，一条老巷子，一句熟悉的话，就能把它重新拉开。',
 'detailIntro': ('一个周六的下午，四个人在四座城市里被同一件事绊住：一个背影像去世的父亲，一条老巷子通向戒掉的毒，一座电梯修好了脚却拐进楼梯，'
                 '一份又一份工作里总冒出同一句话。王德生指出：放不下，是三界中某一界的回写没有完成，留下一个随时会被激发的洞。'
                 '三界是三块地——脑子里想的（理念界）、手上碰的和身体里的（现实界）、心里你我他之间的信、望、爱（自我界）。'
                 '自我界的洞叫无法释怀，现实界的洞是上瘾、惯与恐惧，理念界的洞是执念，其中最难的是看不见的潜意识执念。'
                 '三种放不下走同一条路：类似的场景把一串跨三界的序列勾起，走到洞里，回写落空，于是一再重来；它们追的都是一种意义体验，所以都是瘾；'
                 '它们还是纠缠着发生的，互相需要，互相加强，只补一个洞，另两个洞会把它重新勾开。'
                 '放下不是想通，也不是时间过去，而是那一界的回写完成，另两界缠上来护航，在一个有你有他的场里一次一次加厚，沉淀成土。'
                 '全书三编九章：第一编讲放不下是什么（被勾起、三界序列、三个洞三种瘾），第二编讲三种放不下各自怎样放下（自我界、现实界、理念界），'
                 '第三编讲三洞为什么缠住、怎样一起放下（纠缠、场与加厚、一界中心的理论为什么都放不下它）。证明靠思想实验，不靠没跑过的数据。'),
 'description': ('道理都懂，为什么还是放不下？本书说：放不下，是三界中某一界的回写没有完成，留下一个随时会被激发的洞。'
                 '自我界的洞是无法释怀，现实界的洞是上瘾与惯，理念界的洞是执念；类似的场景一来，三界序列被勾起，走到洞里落空，一再重来；'
                 '三种放不下互相纠缠、互相加强，放下要靠洞所在一界的回写，另两界护航，在场里加厚、沉淀成土。三编九章，思想实验论证。场景为构想，无调查数据，不作诊断。'),
 'todayZh': '“道理我都懂，就是放不下。”本书说：放不下，是三界中某一界的回写没有完成，留下一个随时会被激发的洞——无法释怀、上瘾与惯、执念，三个洞互相缠着，要一起放下。三编九章。',
 'todayEn': ('"I understand all of it, and I still cannot let go." Wang Desheng argues that letting go fails when write-back in one of three realms '
             '(ideas, reality, self) has never been completed, leaving a hole that any similar scene can reopen. The hole in the self is grief that will not settle; '
             'the hole in reality is addiction and habit; the hole in ideas is fixation, the hardest kind of which is unconscious. The three holes are entangled and feed one another, '
             'so letting go means completing the write-back in the realm of the hole, with the other two realms escorting it, thickened over and over within a shared field until it settles. '
             'Three parts, nine chapters, argued by thought experiment. All households are imagined; no diagnosis is offered.'),
 'bookPoints': ('本书（王德生、鲍锦朝 著）约 %d 万字（含标点），三编九章' % M.wan(HERE) + '：王德生 2026 年 11 月 2 日口述二十九条承重命题并裁定口径（附录一照原话登记）；'
                '文字由 AI（Claude）协作写成，一个 Claude 拟纲、执笔前言、附录一与后记并统稿，十位 Claude（Sonnet）执笔者并行写成导论、九章、结语与附录二至五，经三审，经王德生审定。'
                + CONSTRUCT + '判词：' + VERDICT + '主线：' + CHAIN +
                '第一编（1–3 章）放不下是什么：第 1 章被勾起，类似的场景怎样把洞拉开；第 2 章三界序列，从哪一界起、在哪一界落空；第 3 章三界三个洞、三种瘾，两清、想通、放下，各追一种意义体验。'
                '第二编（4–6 章）三种放不下各自怎样放下：第 4 章自我界的洞，无法释怀，回写的三种形态是替代、补足、接续；第 5 章现实界的洞，上瘾与惯，身体的回写要走够回数，另两界护航；第 6 章理念界的洞，执念，潜意识的执念本人看不见。'
                '第三编（7–9 章）三洞为什么缠住、怎样一起放下：第 7 章三洞纠缠，互相需要、互相加强；第 8 章在场里加厚，主力与护航、加厚与重复、沉淀；第 9 章一界中心的理论为什么都放不下它，从四取、认知行为治疗到 AI 陪聊，逐家四问。'
                '总律：洞在哪一界，药就落在哪一界；另两界是护航，代替不了主力。附录五写明本书自认最弱处与推翻条件，附录三是可证伪条款与读数编码手册。'),
 'skillTheory': ('读完这本书，可以练几样手上的小功夫，练的是“找洞”，不是替人放下，也不是治疗。'
                 '一，找“像”：把最近一次放不下被勾起的那一刻原样写下来，找出是哪一个“像”把它拉开的（一个背影、一条巷子、一句话），不是那件事本身。'
                 '二，走序列：写下被勾起以后三界依什么次序被点亮——理念界冒出了什么道理，现实界做了什么动作、身体有什么反应，自我界你我他之间缺了什么——在哪一界落了空。'
                 '三，认洞：看洞更像自我界的无法释怀、现实界的上瘾与惯，还是理念界的执念；也看另两界有没有跟着被拉开。'
                 '四，数回写：只数这一界新的回写发生过几回（替代、补足还是接续），数的是次数，不是决心；再看另两界有没有来护航。'
                 '五，分账：把说服自己的话和真正落地的回写分开，道理说得再通，不算回写。'
                 '六，留口子：照附录五和附录三，写下什么情形出现，就说明这样读错了。'
                 '以上是本书的读法，不是心理治疗，不作诊断，不给用药建议；成瘾与重度哀伤请找医生或心理咨询师；学习包与智能体只陪练，不打分，读数不进考核。'),
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
    for line in a.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if line.startswith('|') and len(cells) == 4 and cells[0].isdigit():
            n, tm, quote, where = cells
            out.append({'t': '第 %s 条　（落在%s）' % (n, where), 'x': '原话（%s）：%s' % (tm, quote)})
    assert len(out) == 29, len(out)
    return out


PART = {1: '第一编　放不下是什么', 2: '第二编　三种放不下，各自怎样放下', 3: '第三编　三洞为什么缠住，怎样一起放下'}
ROLE = {1: '被勾起的“像”、三界序列、三个洞', 2: '一界的洞与它的回写（替代、补足、接续；身体的回写；新理念）', 3: '三洞的纠缠、场里的加厚、一界中心的理论'}


def task(n, c):
    part = (n - 1) // 3 + 1
    q0 = re.sub(r'^[一二三四五六七八九十]+[，,、]\s*|^\d+[.、]\s*', '', c['think'][0]) if c['think'] else '你最放不下的那件事，是哪一个“像”把它勾起来的？'
    secs = '；'.join('%s「%s」' % (a, b) for a, b in c['jie'])
    q = ('先想：%s 再读第 %d 章（%s）：%s。读的时候找三处：本章的洞在哪一界，被勾起后三界的序列怎么走、在哪一界落空？本章讲的是什么（%s）？'
         '本章“思想实验”那一节里，哪两条各家自己承认的事实，哪一家的理论容不下，三界框架怎样容下？'
         % (q0, n, PART[part], secs, ROLE[part]))
    ck = '核对要点：' + ' '.join(c['take'][-1:]) + ' ' + ' '.join(c['ledger'][:2])
    ck += (' 复核三条守线：洞在哪一界，药就落在哪一界，另两界只是护航；回写要很多次，不说一次就好；结论落在“回写发生了、位置改了”上，不落在“他下决心”上。'
           '书自己标明：本章人家与场景都是构想，没有数据；不作诊断，成瘾与重度哀伤要找医生或心理咨询师。失败条件（附录五、附录三）：分型在先、读数在后，三界的洞与后来的走向对不上，或洞可以事后随意解释——本章的读法就要收回。')
    return {'lesson': n, 'name': '第%d章：%s' % (n, c['title']), 'question': q, 'checkpoint': ck.strip()}


def main():
    full = (HERE / M.SRC).read_text(encoding='utf-8')
    t, chs = parse(full)
    assert sorted(chs) == list(range(1, 10)), sorted(chs)
    C = dict(HAND)
    C['loadBearing'] = appendix1(t)
    C['tasks'] = [task(n, chs[n]) for n in range(1, 10)]
    kp = []
    for n in range(1, 10):
        c = chs[n]
        x = (c['take'][-1] if c['take'] else '') + ('　' + c['ledger'][0] if c['ledger'] else '')
        kp.append({'t': c['title'], 'ch': '第%d章' % n, 'x': x.strip()})
    C['keypoints'] = kp
    miss = [n for n in range(1, 10) if not chs[n]['take'] or not chs[n]['ledger'] or not chs[n]['think']]
    (HERE / 'content.json').write_text(json.dumps(C, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('content ok: tasks', len(C['tasks']), 'loadBearing', len(C['loadBearing']), 'keypoints', len(kp), 'chapters missing take/ledger/think:', miss)


if __name__ == '__main__':
    main()
