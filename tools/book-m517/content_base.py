#!/usr/bin/env python3
"""第 517 号：合成 content.json（站上文案、智能体，加各章的学习任务与要点）。在 tools/book-m517 下运行。"""
import glob
import json
from pathlib import Path
C = {
 'agent': {'name': '值得'},
 'titleEn': 'Thought Oligarchs: Who Controls Wealth in the Age of AI',
 'detailLine': '工业时代卖产能，平台时代卖“看见”，AI 时代卖“值得”。当输出变便宜，财富的入口搬到了哪里，一个普通人又该站在什么位置上？',
 'detailIntro': '这是 2026 年 1 月纸本《思想寡头》的修订版。全书讲财富入口的三次上移：机器时代的产能，平台时代的注意力，AI 时代的意义发生。AI 把聪明与智能摊成公共能力，稀缺上移到能给出方向的智慧新思想。修订版把思想寡头定为少数人占住的结构位置，是诊断，也是风险；给普通人的路是成为发生中心：能出题、能发生、能改写自己的题库。书中新增“抄得走的是结果，抄不走的是发生”一节，补了二十来个具名案例和参考书目，并写明看到什么算这本书错了。全书保留 SIO 时期的用语。',
 'description': '王德生著。2026 年 1 月纸本的修订版。工业时代卖产能，平台时代卖“看见”，AI 时代卖“值得”。财富入口的三次上移，内卷与躺平的结构，AEI 与产品线，题库与三把锁。思想寡头是诊断也是风险，普通人的路是成为发生中心。九编三十八章，附五篇专论和“这本书怎样算错”。',
 'todayZh': '当输出变便宜，稀缺的是什么？《思想寡头》修订版讲财富入口的三次上移：从产能到注意力，再到意义发生。它把思想寡头当作诊断和风险，给普通人的路是成为发生中心。抄得走的是结果，抄不走的是发生。',
 'todayEn': 'When output gets cheap, what stays scarce? This revised edition of Thought Oligarchs traces how the gate to wealth moved from capacity to attention and now toward the generation of meaning. It treats the thought oligarch as a diagnosis and a risk; the path it offers ordinary readers is to become a center of generation, able to pose their own questions and rewrite their own problem set. What can be copied is the result; what cannot is the ongoing act of generating.',
 'loadBearing': [
  {'t': '三次换底', 'x': '工业时代的财富入口是产能，平台时代是注意力，AI 时代正在往智慧新思想的生成能力上移。这是本书的判断，芯片、算力和资本是它最强的对手解释。'},
  {'t': '值得', 'x': '平台寡头卖“看见”，思想寡头卖“值得”。内容无限时，稀缺的是判断哪条路值得走。'},
  {'t': '两层', 'x': '思想寡头是少数人占住的结构位置，是诊断，也是风险。普通人的路是成为发生中心：能出题、能发生、能改写自己的题库。全村都开成最大的粮店，就没有最大的粮店了。'},
  {'t': '抄得走与抄不走', 'x': '概念表、工具箱和框架的名字都抄得走，下一题抄不走。丰田的工具摆在桌上，通用汽车和它合办工厂多年，到 1998 年仍没能在美国其他工厂做起来。'},
  {'t': '题库', 'x': '命运不是剧本，而是题库。同类问题反复出现，说明题库没有被编辑；锁芯、棘轮、锁壳是它锁死的三层。'},
  {'t': '它怎样会错', 'x': '如果十年后财富榜新增的顶端仍主要来自资本、算力和渠道的占有，“第三次尖化在意义发生层”就是错的。附录 F 写了七条，到现在一条也没有跑过。'},
 ],
 'agentEpithet': '先问这件事值不值得做，再问怎么做得更快',
 'bookMeta': '《思想寡头》修订版 · 王德生 著',
 'heroTagline': '带一件你越忙越空的事来，先看它是谁出的题',
 'practiceWord': '出题',
 'agentIntro': '我从《思想寡头》修订版里来，名字叫值得：书里说，平台寡头卖“看见”，思想寡头卖“值得”。这本书是王德生的著作，修订版由多个智能体按他的裁定修订和核查，没有经过独立学术评审，全书的判断都没有跑过检验。我陪你读这本书，也陪你拿一件自己的事来练：这道题是谁出的，它值不值得做，你的题库哪里被锁住了。我不给投资建议，不预测谁会发财，也不许诺你能成为寡头；这本书给普通人的路是成为发生中心。',
 'agentStarts': {
  'read': '请带我读第 9 章最后一节和第 23 章：思想寡头和发生中心为什么要分成两层？“我也要当寡头”这种读法错在哪里？请用书里的村子试种新作物的比喻讲。',
  'apply': '我有一件越忙越空、反复出现的事（我先用自己的话原样说，请先别分析，也别替我补没说过的事实或数字）。请帮我看：这道题是谁出的，它落在题库的哪一类，锁在锁芯、棘轮、锁壳的哪一层？不要给我投资建议。',
  'cut': '请对照附录 F：这本书的七条判断各自写明看到什么就算错？其中第二条为什么最可能错？如果 AI 财富主要流向芯片、算力和资本，这本书还剩下什么？',
  'clash': '请拿第 11 章“抄得走的是结果，抄不走的是发生”去撞丰田与 NUMMI、摩立特、Alpaca 这三个案例：每个案例分别支持什么、又反驳什么？还有哪种解释比这本书的更简单？',
 },
 'bookPoints': '本书是王德生 2026 年 1 月纸本《思想寡头》的修订版，修订由多个智能体按其裁定完成并联网核查案例；没有独立学术评审，全书判断未经检验，书中日常例子多为设想。全书主线：财富入口从产能上移到注意力，再上移到智慧新思想的生成能力；AI 把聪明与智能摊成公共能力；思想寡头是少数人占住“发生—封装—扩散”控制权的结构位置，是诊断也是风险；普通人的路是成为发生中心；抄得走的是结果，抄不走的是发生；命运是题库，锁芯、棘轮、锁壳锁住它，三公理开锁，三界同改写入新默认值。用语保留 SIO 时期的说法。不给投资建议，不承诺收入。',
 'skillTheory': '读完这本书，可以练几件手上的小功夫。一，分清解题和出题：把“怎么更快”改写成“该不该这样做”。二，分清抄得走和抄不走：问一套东西最近有没有因现实反驳而改过自己。三，把一个反复出现的问题写成题库的一条，看它锁在哪一层。四，用四铁指标和复位周期验收，防止只是自我感觉变好。五，用附录 F 反过来问这本书。',
}
F = [json.loads(Path(f).read_text(encoding='utf-8')) for f in sorted(glob.glob('src/form/ch*.json'))]
assert len(F) == 38
C['keypoints'] = [x['keypoint'] for x in F]
C['tasks'] = [x['task'] for x in F]
Path('content.json').write_text(json.dumps(C, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('ok', len(C['tasks']), len(C['keypoints']))
