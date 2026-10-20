#!/usr/bin/env python3
"""生成第 482 号三位一体单元（学习包 + 问对页）。以 m/488 为模板。"""
import json, re, hashlib, shutil
from pathlib import Path
SITE=Path('/home/claude/site/public/books/m'); S=SITE/'488'; D=SITE/'482'
MS=Path('/home/claude/fengshui502'); V='20261020a'; REV='20261020-m482-unit-v1'
SLUG='fengshui-fashengxue'; AG='写土'
FILES=['ch00_daolun']+['ch%02d'%i for i in range(1,26)]+['ch26_jieyu']
ANCH=[3,5,6,7,8,10,11,12,14,15,16,18,19,20,22,23,24,26,27,28,30,31,32,34,35,36,37]
PARTS=['导论：风水是被发现的，还是被回写出来的？','定义：风水是 E 对方程运行的影响','回写：风水从哪里来','固化：风水怎样变成命运','E1 三界：土的三层','E2 信息三态：符号、逻辑与数学','E3 能量三状态：真、善、美','用这把尺子重读旧书','解冻与重写：从看风水到写风水','结语：从趋吉避凶，到解冻与重写']
PARTOF=[1]+[2]*4+[3]*3+[4]*3+[5]*3+[6]*3+[7]*3+[8]*3+[9]*3+[10]
SHORT=[]  # 短标题
tasks_in=[]
for f in ('batch1','batch2','batch3'): tasks_in+=json.load(open(MS/'tasks'/(f+'.json')))
tasks_in.sort(key=lambda x:x['lesson']); assert [t['lesson'] for t in tasks_in]==list(range(1,28))
# 全文网页里的短章题
html=open('/home/claude/bk482/text.html').read()
def htitle(sid):
    m=re.search(r'id="%s"[^>]*>(.*?)(?=id="s\d+"|$)'%sid,html,re.S); t=re.search(r'<h[12][^>]*>([^<]*)',m.group(1)); return t.group(1).strip()
(D/'unit'/'sources').mkdir(parents=True,exist_ok=True); (D/'agent').mkdir(exist_ok=True); (D/'downloads').mkdir(exist_ok=True)
tasks=[]
for i,(f,a,t) in enumerate(zip(FILES,ANCH,tasks_in),1):
    raw=(MS/(f+'.md')).read_text()
    lines=raw.strip().split('\n')
    head=lines[0].lstrip('# ').strip()
    secs=[l.lstrip('◆ ').strip() for l in lines if l.startswith('◆')]
    title=head if i not in (1,27) else head
    text=re.sub(r'\n{3,}','\n\n',raw.strip().replace('**','').replace('> ','')).strip()
    sha=hashlib.sha256(text.encode()).hexdigest()
    url='https://sdeuniverses.com/books/m/482/text/#s%d'%a
    src=dict(book='m-482',lesson=i,version='初版（2026-10-20）',title=title,url=url,sha256=sha,sections=[dict(title=s,url=url) for s in secs],text=text)
    json.dump(src,open(D/'unit'/'sources'/('chapter-%02d.json'%i),'w'),ensure_ascii=False,indent=2)
    short=htitle('s%d'%a)
    tasks.append(dict(lesson=i,problemId='M482-C%02d'%i,part=PARTOF[i-1],title=short,question=t['question'],checkpoint=t['checkpoint'],chapterTitle=title,sourceUrl=url,sourceData='/books/m/482/unit/sources/chapter-%02d.json'%i,sourceSha256=sha))
L=dict(schemaVersion='1.0',book='m-482',number=482,title='风水发生学——空间与人的共生智慧',authors=['邬燕琴'],advisor='王德生',sourceEdition='初版（2026-10-20）',taskVersion='20261020-m482-unit-v1',parts=PARTS,tasks=tasks,companionDesign=True,realModelTested=False,learningEffectTested=False)
json.dump(L,open(D/'unit'/'learning.json','w'),ensure_ascii=False,indent=2)
# ---- js / css / skill / agent pages
def common(s):
    s=s.replace('/books/m/488/','/books/m/482/').replace('m-488','m-482').replace('m488','m482').replace('第488卷','第482卷').replace('Book 488','Book 482')
    s=s.replace('content="488"','content="482"').replace('no:488','no:482').replace('20261019a',V).replace('20261019-m482','20261020-m482').replace('fei-fashengxue',SLUG)
    s=s.replace('n>31','n>27').replace('lesson>31','lesson>27').replace('e.lesson>31','e.lesson>27')
    s=s.replace('lesson>31','lesson>27').replace('三十一章','二十七个单元').replace('七编','十部')
    return s
for n in ('core.js','unit.css'):
    shutil.copy(S/'unit'/n,D/'unit'/n)
    p=D/'unit'/n; p.write_text(common(p.read_text()))
core=(D/'unit'/'core.js').read_text(); assert '>31' not in core and '488' not in core, re.findall(r'.{20}(?:>31|488).{20}',core)
app=common((S/'unit'/'app.js').read_text())
POINTS=("这是第482卷配套学习任务，不是著者原文或已验证量表。只依据实际提供的本章；不得声称已通读全书。"
"全书判词：「风水不在地里，在日子一天天写进土里的痕迹里；所以风水不只能看，还能写。」"
"定义（王德生博士）：风水就是新的 E，如何与已有的 D、与目标的 S 形成一个和谐的方程，即三方程之一 E=H(S,D)。风水好，是三方程不走向不等式（S=F(D,E)、D=G(S,E)、E=H(S,D) 三条都还成立）；隐含两层：六路径通顺（六六大顺，即 E 高度促进六路径顺利运行，风水差是 E 拖住、卡住某几条）与三原理动力充足（S 与 D 顶撞则 E 变，D 与 E 顶撞则 S 变，S 与 E 顶撞则 D 变，三种转换都转得动）。焦点是 E：E1 三界（理念界、现实界、自我界）、E2 信息三态（符号态、逻辑态、数学态）、E3 能量三状态（内能真、动能善、势能美）。风水＝E1、E2、E3 对 SDE 方法论具体运行的影响；好是正面影响，差是负面影响。"
"发生机制：风水是 S 不断回写 E 形成的，不是地里本来就有的。固化：风水固化即 E 固化，E 固化会固化 D 和 S，整个 SDE 固化，形成所谓的「命运」；命运是 E 的长期稳定化；断语「准」的地方，往往是固化最深的地方；解冻是松开固化点，让方程重新可写。诊断法：先找固化点，再查方程、路径、原理，最后加回写一步连成循环（吸收邬燕琴的五阶段框架：识别问题、诊断环境、分析关系、制定方案、验证效果）。"
"主语纪律：写成这家的日子被某物排成了什么样，不以「一个人」做主语去看穿、决定或掌控风水与命运。"
"证据边界：书中引用的风水断语取自著者所附两本现代通俗风水书的照片页（附件书一书名未知；附件书二为《图解寻龙大侠赖布衣真传阴阳宅风水绝断》），单句短引并标页码，只作为旧书的说法来分析其发生机制，不当事实转述，不背书；〔待核〕是未核实的说法，只取大意，不得编造出处、年份与数据；杜明远、方晴、杜小禾、杜奶奶、老周均为虚构陪读人物，故事不是证据。"
"本书不给吉凶预测，不替任何一户人家断风水好坏，不给医疗、心理或法律建议；身体或心里的难处真的大了，请找医生或心理咨询师。不建议为化煞而花钱、搬家或拆改房屋。"
"书中最弱处：E=H(S,D) 的写法与回写、固化的因果链是本书在王德生博士定义上的展开读法，尚无实测检验；方程诊断表是配套设计，不是已验证量表。回答时区分作者原文、模型推论与读者判断；读者举出反例时，有据反对与证据不足须明说，不替书辩护。")
m=re.search(r"agentName:'换气',agentEpithet:'.*?',bookMeta:'.*?',docTitle",app,re.S); assert m
app=app.replace(m.group(0),"agentName:'%s',agentEpithet:'先问这块土是被谁写成的，再问哪条路被它卡住，最后问哪一处能重新写',bookMeta:'《风水发生学——空间与人的共生智慧》 · 邬燕琴著 · 王德生指导 · 第482卷 · ISBN 979-8-90690-173-6 · 初版',docTitle"%AG)
m=re.search(r"bookPoints:'.*?本轮模式：'",app,re.S); assert m
app=app.replace(m.group(0),"bookPoints:'%s本轮模式：'"%POINTS.replace("'","\\'"))
app=app.replace('只依据实际提供的本章','只依据实际提供的本章')
assert '488' not in app and '换气' not in app and '李秋金' not in app, re.findall(r'.{15}(?:488|换气|李秋金|肺).{15}',app)[:5]
(D/'unit'/'app.js').write_text(app)
sk=common((S/'unit'/'SKILL.md').read_text())
sk=re.sub(r'^# .*?\n',f'# {AG} · 第482卷学习问对规范 v1.0\n',sk,count=1)
sk=re.sub(r'书籍：.*?。当前正文',"书籍：《风水发生学——空间与人的共生智慧》，邬燕琴著，王德生指导，第482卷，ISBN 979-8-90690-173-6。当前正文",sk,count=1,flags=re.S)
sk=sk.replace('初版（2026-10-19）','初版（2026-10-20）').replace('lesson=1..31','lesson=1..27')
sk=re.sub(r'## 理论与证据\n.*?\n\n## 两次回写',"## 理论与证据\n本书是邬燕琴著、王德生指导的德麦国际第482号。底盘：风水就是新的 E 如何与已有的 D、目标的 S 形成和谐的方程 E=H(S,D)；风水好是三方程不走向不等式、E 高度促进六路径顺利运行；风水是 S 不断回写 E 形成的；E 固化连带固化 D 和 S，即所谓命运；解冻是松开固化点。焦点是 E1 三界、E2 信息三态、E3 能量三状态。陪读人物杜明远一家为虚构，故事不是证据。书中引用的风水断语来自两本现代通俗风水书的照片页，只作旧书的说法来分析，不当事实，不作吉凶预测，不替人断风水；身体或心里的难处真的大了，请找医生或心理咨询师。\n\n## 两次回写",sk,flags=re.S)
assert '肺' not in sk and '李秋金' not in sk and '488' not in sk, re.findall(r'.{10}(?:肺|李秋金|488).{10}',sk)
(D/'unit'/'SKILL.md').write_text(sk)
# agent pages
DESC="我从《风水发生学》里来。你带一间住了很久的屋子、一条总被绊住的走廊、一个舍不得动的老物件，或者一句「这房子风水好不好」来，我先陪你问三句：这块土是被哪些日子写成的；它和你们在走的路、想要的样子对不对得上；它冻在哪里，从哪处能松动。"
for n in ('dialogue.html','learning.html'):
    s=common((S/'agent'/n).read_text())
    s=s.replace('李秋金著','邬燕琴著 · 王德生指导').replace('李秋金','邬燕琴').replace('ISBN 979-8-90690-678-6','ISBN 979-8-90690-173-6')
    s=s.replace('一口气是怎样发生的','风水发生学').replace('三位一体单元20261019','三位一体单元20261020').replace('正文初版（2026-10-19）','正文初版（2026-10-20）')
    s=s.replace('肺把自己放在分母上：先问这口气交出了什么，再问它靠哪两条路，最后问账结在哪里。','风水不在地里，在日子写进土里的痕迹里：先问这块土是被谁写成的，再问哪条路被它卡住，最后问哪一处能重新写。')
    s=s.replace('换气',AG).replace('三十一章三问实践','二十七单元实践').replace('二十七个单元三问实践','二十七单元实践').replace('十部 · 二十七个单元','十部 · 二十七单元')
    s=s.replace('原有'+AG+'入口','原有'+AG+'入口')
    leftover=re.findall(r'.{12}(?:488|肺|氧|呼吸|气）|憋气).{12}',s)
    assert not leftover,(n,leftover)
    (D/'agent'/n).write_text(s)
pu=json.loads((S/'publication-unit.json').read_text())
pu.update(unitId='m-482',number=482,title='风水发生学——空间与人的共生智慧',authors=['邬燕琴'],advisor='王德生',isbn='979-8-90690-173-6',price='US$20',sourceEdition='初版（2026-10-20）',revision=REV,learningTasks=27,parts=10,agentName=AG,localStorage='IndexedDB / sde-publication-m482-v1; append-only events; no silent trimming')
for c in pu['components']:
    for k,v in list(c.items()):
        if isinstance(v,str): c[k]=common(v)
    if c['kind']=='dialogue': c['name']=AG
json.dump(pu,open(D/'publication-unit.json','w'),ensure_ascii=False,indent=2)
print('ok')
