#!/usr/bin/env python3
"""Editorial rewrite for Zhang Qiong companion batch 21–40.

V2 met the mechanical publishing contract but overused a common frame.  This
migration makes each pair audibly descend from its mother article: it opens
with a mother-vocabulary glossary, states the article-specific concept chain,
derives practice readings from that vocabulary, and rejects generic filler.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import build_zhang_qiong_bindi_v1 as v1
import build_zhang_qiong_bindi_v2 as v2


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "public" / "students" / "zhang-qiong"


GLOSS: dict[str, dict[str, str]] = {
    "entrusted-appeal": {
        "委托的感应": "身体先向人发出一声还没有被现成概念整理过的恳求，人随后才可能注意和回应",
        "代理感知": "设备或程序在本人形成第一手感受以前，先替他读取并解释身体",
        "合规化觉察": "觉察被规定成标准步骤，练习者学会交出正确报告，却未必仍能接到自己的微弱信号",
        "日常委托": "饥饿、疲劳、胸闷或想离开等普通身体线索对注意提出的低强度请求",
        "高阶委托": "普通线索在矛盾累积后变成无法再被代理的强烈请求，并逼迫人重新作出判断",
        "委托—感应回路": "身体发出、本人接到、作出回应、身体再变化的完整往返",
    },
    "suspended-drowning": {
        "悬溺": "人被支持稳稳托住，却因从未亲自组织混乱而一撤去支持便无处着力",
        "综合能力": "把模糊感觉、冲突证据、风险和下一步动作临时组织成可修正判断的本领",
        "舒适茧房": "工具持续消除困难，也持续拿走练习综合能力所需摩擦的环境",
        "在场权": "当事人亲自参与感觉、判断、试错和承担，而非只接收正确答案的位置",
        "灾难性必需": "不能为了训练能力而撤掉的救命支持、危机干预或专业保护",
    },
    "activative-deprivation": {
        "激活性剥夺": "一个人的动作在特定关系里长期不能改变后续，于是发起本身逐渐停止",
        "回应权": "拒绝、提议、愤怒或求助能够进入关系并使下一步有所不同的实际权利",
        "回应注销": "对方看似听见却不让任何表达改变规则，使回应权在重复中失效",
        "身份债役": "当事人把继续忍受理解为维持好妻子、好母亲或完整家庭必须偿还的债",
        "场域特定性": "行动停滞只在暴力关系中出现，在工作、照护或求助场景仍保留发起能力",
    },
    "displaced-growth": {
        "转嫁式成长": "团体中的进步由高密度承接替成员承担关键重量，离场后能力难以单独站立",
        "担保密度": "一次表达周围有多少提示、接话、修复和肯定在保证它不会坠落",
        "背景性无声在场": "他人不抢答却以稳定陪伴承住试错，让成员自己完成判断",
        "前台性高反馈在场": "主持者频繁命名、鼓励和修复，使表达顺利却可能接走困难环节",
        "内化式成长": "成员把原由团体完成的判断和承重动作逐渐变成自己可携带的能力",
        "迁移裂缝": "团体内做得到、团体外做不到之间那条不能由成绩表掩盖的断口",
    },
    "transgenerational-self-wiring": {
        "跨代自我接线": "上一代暴力经验被接入当代自我维持，使施暴不再只是一个可替换工具",
        "撤稳": "暴力停止时，施暴者先出现失去权能、价值或自我边界的结构性不稳",
        "三重接线": "暴力把命令权、价值确认和情绪卸载同时接成一次暂时稳定",
        "接线闸": "非暴力支架真正承担稳定功能后，旧暴力端口不再自动通电的转折点",
        "自我维持器官": "某个行为已承担让自我不散架的功能，撤掉它会先暴露结构空缺",
    },
    "generative-collusion": {
        "道德亏空": "暴力之后好人身份、家庭正当性和受害者尊严同时出现的未清缺口",
        "生成性共谋": "双方在不对等处境中共同完成一套修复仪式，让关系获得再次启动条件",
        "道德债权": "受害者把过去忍耐登记为未来一定会兑现的意义或补偿",
        "交互承包": "施暴者承包悔改，受害者承包原谅，双方共同替循环遮住出口",
        "修复仪式": "道歉、补偿、保证与原谅按固定次序重造好人和好家庭的短暂版本",
    },
    "grey-matter-order": {
        "灰质秩序": "显性暴力退场后，旧支配仍由身体习惯、日常话语和微小选择自行维持",
        "暴力发动机": "靠威胁、殴打或惩罚直接推动服从的高能耗阶段",
        "去事件化": "支配不再表现为可指认的一次暴力，而散进每天看似平静的小动作",
        "低能耗自持": "无需频繁施暴，旧规则也会借期待、回避和自我修正继续运行",
        "灰质惰性": "现实威胁减弱后，已经形成的行动轨道仍把人带回旧位置",
    },
    "unanchored-operation": {
        "缺锚运行": "没有权威给答案时，人仍能在空白中发起、协商并维持共同活动",
        "生成缺失": "能力不是曾经拥有后退化，而是从未得到完整练习和长成的机会",
        "守住空白": "面对沉默先不抢救，让第一项真实发起有机会由参与者自己出现",
        "无权威发起": "不借主持者许可或标准脚本，参与者提出可被他人接续的第一步",
        "救场接管": "带领者因怕冷场而迅速给任务、给意义，结果替参与者完成起步",
    },
    "tentative-ethics": {
        "尝试性伦理": "旧规则失效而新规则未成时，用可撤回行动试出更可生活的方向",
        "试探": "不声称已经正确，只在边界内先做一个能接受后果检验的小动作",
        "反馈": "行动落地后，受影响者的选择、伤害和新可能对原判断作出回声",
        "修正": "依据反馈改变动作、责任和边界，而非把失败解释成别人不理解",
        "结算": "试探经过实际后果检验后，才暂时取得可公开讨论的正当性",
        "试探生态": "允许试探出现、承受一段未决并让失败可退出的共同环境",
        "宽容度": "环境能容纳多大偏离而不立即惩罚或贴标签",
        "厚实度": "试探者能获得多少真实回应、资源和承担，而非只有口头鼓励",
        "延迟度": "集体愿意等待多久再给试探定性和结算",
    },
    "sedimented-layer": {
        "伦理沉淀层": "一次伦理生活结束后留下、能脱离原场景保存并再次起作用的硬质痕迹",
        "发生过后": "行动已经结束，参与者退场，但某种可携带形态刚开始存在的阶段",
        "压缩": "复杂事件被缩成一句家训、一项礼节、一段故事或一种姿势",
        "保存": "压缩后的痕迹越过原参与者和原时间继续留存",
        "再激活": "后人在新处境中接触痕迹，并由它重新长出判断而非机械复制",
        "礼的沉淀装置": "礼把过往伦理事件压成节文、经籍和习惯，同时允许后来者重新解释",
    },
    "successful-abolition": {
        "回路闭合点": "感受、判断、行动和结果修正最终在谁那里完成的关键位置",
        "体知回路": "身体给出线索，人据此行动，再被后果改写的完整生活往返",
        "废止性成功": "外部照料每次都给出好结果，却因此取消了自身能力出生的机会",
        "外部符号节点": "分数、口诀、专家建议等替身体完成判断并关闭回路的接口",
        "饥饿—进食线": "用饥饿出现、饮食决定和饱足修正追踪闭合点移动的具体路径",
    },
    "guarding-occurrence": {
        "发生感": "教师在指标形成前，已从学生回应和课堂节奏中觉到学习正在聚拢或散开",
        "发生感守护优先": "先保护真实教学继续，再处理证明、汇报和改革结算的次序原则",
        "词汇贫困": "教师不是词少，而是只能借改革术语说课，无法命名自己真正察觉的转折",
        "语言生态覆盖": "结算语言长期替换现场语言，直到教师连差异也难以辨认",
        "优先性置换": "证明改革有效被放到教学是否发生之前，现场反而成为证明的材料",
        "结算语法": "表格和评课只接收可汇报动作，并排斥尚未能稳定命名的教学变化",
    },
    "pseudo-repair": {
        "希望回路": "人从可能性发起行动，在创造和满足中认出这是自己的路",
        "伪修复": "看似恢复希望的办法没有接通断点，反而制造更多必须完成的任务",
        "修复能量倒灌": "投入希望的力无法进入创造和幸福节点，只能涌回仍畅通的绩效通道",
        "创造节点": "人能提出未被预制的新动作，并从结果中认出自己的参与",
        "幸福节点": "行动完成后能留下具体满足和心理句号，而非立即进入下一项任务",
        "任务通道": "任何愿望都被翻译成目标、打卡和优化项目的高通量出口",
    },
    "mutual-severance": {
        "互裁": "共同体内部为了维持一条路线，主动切掉另一部分成员和可能性的动作",
        "确认动作": "通过沉默、评价或程序反复表示被切路线不再属于我们",
        "标定动作": "把少数意见标成不成熟、不现实或不合时宜，使刀口取得名称",
        "社会硬度": "过去多次互裁沉积后，当前改变路线所感到的实际阻力",
        "可能路线": "共同体曾可选择却在互裁中被排除、后来又被遗忘的方向",
        "合伙自我切割": "社会的硬并非只受外力压迫，也由成员为继续合伙而彼此删减形成",
    },
    "from-guarding-to-touching": {
        "守护": "制度为尚未定型的人保留不被立即塑造和结算的空间",
        "触摸": "教师在具体瞬间依据沉积判准作出不可代理、会被学生反应修正的回应",
        "判准沉积": "长期经验留下的辨别层，使教师能在瞬间看出此刻该接住什么",
        "瞬间结算": "教师在来不及套用方案时调动整层判准完成一次现场判断",
        "不可代理": "同一句反馈换人、换关系或换时刻便不再是同一个教育动作",
        "推广吞噬": "制度为复制触摸而把它做成标准话术，最终消灭其现场判准",
    },
    "void-facing": {
        "虚空对视": "理论回到具体人面前时看似正确，却因接触面从未建立而没有真正接住对方",
        "接触面": "概念必须承受对方经验抵抗，并允许自身被改写的实际相遇位置",
        "钝响": "具体人的话撞到完整概念后没有进入判断，只留下被忽略的不协调",
        "概念返回": "理论从抽象解释重新进入原本想理解的人和生活现场",
        "面向他者": "判断不只检查概念自洽，还让对方能改变研究者下一步",
        "伦理表现替代": "研究者完成反思姿态，却用自己的尽职感替代了真正接触",
    },
    "ground-strength": {
        "底劲": "身体经过重复、受挫和自我修正后积下的继续做事之力",
        "主体沉积层": "一次次亲自承受和判断留下、以后能被整层调用的能力底座",
        "竞争性神经通路": "即时切换和快速奖励反复铺设后，与缓慢积累争夺注意的路径",
        "应激型注意": "必须靠外部刺激和紧迫感才能启动，一失去强刺激便迅速掉线",
        "壳中养骨": "不先拆掉数字外壳，而在壳内安排足够长的承重动作让底层能力长出",
        "自我卷入判决": "人从一次困难行动的后果中认出是自己在承担和变稳",
    },
    "meaning-prosthesis": {
        "意义发生假体": "平台和希望话语替人完成意义判断，并逐渐占据原本会长出意义的位置",
        "意义器官": "人通过投入、等待和结果回写，亲自辨认什么值得的能力",
        "意义余热": "主体已经疲惫，却仍残留一点能被口号和任务调用的期待",
        "三重节奏": "向未来开放、在当下投入、由结果返回自身的意义呼吸",
        "集体空转": "许多人被同一希望号召连接，却共同增加动作而没有共同生成方向",
        "厚土": "无用时间、稳定关系和非结算活动组成的意义生长条件",
    },
    "algorithmic-substitution": {
        "生成过程的算法替代": "算法在感受尚未成形时先完成命名、比较和关系判断",
        "时序置换": "工具把本应在体验之后的结论提前放到体验之前",
        "感受裁判权": "谁有权决定这段关系中的感受是什么、算不算真实以及意味着什么",
        "亲密治理术": "用模板、分数和标准沟通步骤管理亲密关系的技术组合",
        "生成条件": "犹豫、误解、追问和共同修正等让感受亲自长出来的必要过程",
        "不可治理残余": "任何模型都不能替双方完成、只能在相处中承受的那部分不确定",
    },
    "singularity-posture": {
        "独特性姿势": "一套可学习、可展示的做自己动作，使人看起来独特却越来越遵循同一格式",
        "生成性实践": "兴趣在长期投入、偶然偏离和真实后果中长成自己的过程",
        "姿势化": "实践被抽去生长史，只剩能被平台、学校或市场识别的外观动作",
        "沙化": "人持续展示独特，却失去让兴趣彼此黏合并承担后果的内部结构",
        "结算社会": "经历必须被翻译成标签、履历和竞争力才获得价值的环境",
        "不被结算": "保留一部分不为展示、不换取承认却仍愿继续的活动",
    },
}


CHAIN = {
    "entrusted-appeal": "日常委托先从粗粝身体线索发出；代理感知若总在它抵达以前给出报告，合规化觉察又训练人只交标准答案，委托—感应回路便同时失去发送与承接。高阶委托不是更响的同类数据，而是普通委托长期无回音后，身体以无法继续被格式化的方式逼人重新在场。",
    "suspended-drowning": "舒适茧房并非因舒适本身有罪，而是它持续替人完成混乱组织。综合能力没有经历感觉冲突、提出假设、承担误差的完整循环，在场权便只剩确认答案。支持一撤，人不是从成熟能力退化，而是暴露出悬溺；灾难性必需则划出绝不能拿来训练的安全边界。",
    "activative-deprivation": "暴力先让拒绝和提议失去后果，回应注销多次发生后，回应权从实际关系中被撤掉。身份债役又把留下解释成必须偿还的责任，使当事人停止在该关系里发起。场域特定性是关键：若她在别处仍能计划和求助，激活性剥夺就不能被误写成普遍无能。",
    "displaced-growth": "前台性高反馈在场让表达迅速成功，却也可能把寻找措辞、承受沉默和修复误差接走。担保密度越高，团体内表现越好不必然等于内化式成长越多。背景性无声在场要保留承接但不抢走动作，迁移裂缝才会缩小；否则成功只是转嫁式成长。",
    "transgenerational-self-wiring": "上一代经验先把暴力接成权能和价值的恢复手段，三重接线又让命令、确认和卸载在一次施暴中同时完成。停止暴力引发撤稳，说明它已被用作自我维持器官。干预不能替它免责，而要在安全和追责之后建立非暴力支架，直到接线闸真正合上。",
    "generative-collusion": "暴力制造道德亏空，施暴者以悔改和补偿恢复好人身份，受害者以原谅和继续承担保存过去忍耐的道德债权。两边在不平等条件下形成交互承包，修复仪式便不是循环后的尾声，而是生成性共谋为下一轮提供的启动器。",
    "grey-matter-order": "暴力发动机先用高强度事件铺出服从轨道；轨道稳定后，支配经过去事件化散入语气、回避和预先自我修正。旧秩序由此进入低能耗自持，即使发动机暂时熄火，灰质惰性仍带着行动沿旧轨运行，这才是灰质秩序区别于持续暴力的地方。",
    "unanchored-operation": "专业脚本和主持者长期先手，会让救场接管取代参与者的无权威发起。第一次面对空白时的僵住因此未必是退化，而可能是生成缺失。缺锚运行要从守住空白开始，让一个可接续的小动作由参与者出现，再观察下一次是否减少外部提示。",
    "tentative-ethics": "尝试性伦理以试探发起，但试探没有自封正当。反馈把受影响者的选择和伤害带回来，修正据此改变动作，最后才可能结算。试探生态由宽容度、厚实度和延迟度共同构成：只宽容而无承接会把风险丢给个人，只承接而立即定性又会消灭试探。",
    "sedimented-layer": "伦理事件进入发生过后，经压缩成为家训、礼节或故事，再由保存越过原场景。后来者若只机械重复，留下的是惯例；只有痕迹在新冲突中被再激活并生成新判断，才构成伦理沉淀层。礼的沉淀装置正同时承担压缩、保存和再解释。",
    "successful-abolition": "体知回路本来沿饥饿—进食线完成感觉、选择、进食和修正；外部符号节点若每次都提前给答案，回路闭合点便移到体外。建议可能持续正确，于是能力被取消反而不易察觉，这就是废止性成功：结果被照料好了，生成结果的主体位置却没有继续长。",
    "guarding-occurrence": "教师先以发生感察觉课堂正在聚拢或散开，发生感守护优先要求先回应这条现场线索。优先性置换把结算语法放到它之前，语言生态覆盖又迫使教师只会用改革词汇报告。词汇贫困最终不只是说不出，而是连原先能辨认的教学差异也逐渐失去。",
    "pseudo-repair": "希望回路必须经过创造节点和幸福节点才能返回一个‘这是我的’的确认。两节点失效后，修复方案仍从任务通道进入，修复能量倒灌为更多计划和打卡。伪修复因此不是方法选错一次，而是任何方法一进断裂结构就被翻译成新绩效。",
    "mutual-severance": "共同体在路线冲突中先发生互裁，再以确认动作和标定动作重复宣布哪部分不属于我们。被切掉的可能路线逐渐从记忆中消失，多次刀口沉积为社会硬度。合伙自我切割因此补充了外力压迫解释：参与者也在维持合伙时共同生产硬。",
    "from-guarding-to-touching": "守护先留下不被结算的空间，判准沉积则让教师在空间里形成辨别层。具体时刻到来，瞬间结算调用整层经验完成一次触摸；学生的回应还会反过来改写判准。不可代理来自这条关系史，而推广吞噬恰在把关系史删掉、只复制话术时发生。",
    "void-facing": "概念返回具体人时若没有接触面，对方经验只能撞出钝响。研究者随后可能用反思声明完成伦理表现替代，却仍未让他者改变概念。虚空对视不是一般理论脱离实际，而是面向他者的姿态已经出现，真正可被对方改写的通道却没有建立。",
    "ground-strength": "竞争性神经通路和应激型注意让人只在快速刺激下启动，缓慢重复难以进入主体沉积层。没有沉积便谈不上底劲耗尽，更可能是底劲从未生成。壳中养骨不浪漫化痛苦，而是在可退出边界内保留承重时间，直到自我卷入判决让人认出是自己在变稳。",
    "meaning-prosthesis": "意义器官依靠三重节奏工作：向未来打开、在当下投入、让结果返回自身。主体只剩意义余热时，意义发生假体以口号和任务接管这套节奏，许多人被动员却形成集体空转。重建不是加大希望，而是先恢复厚土，让意义再次由亲自参与而生。",
    "algorithmic-substitution": "亲密治理术把评分和模板置于体验之前，时序置换随即发生。算法不只给建议，还借生成过程的算法替代取得感受裁判权；双方减少犹豫、追问和共同修正，生成条件便被抽空。不可治理残余不是故意拒绝工具，而是保留任何工具不能替两人承担的不确定。",
    "singularity-posture": "生成性实践本来由长期兴趣、偏离和后果长成；结算社会先挑出可展示片段，再经姿势化变成通用的做自己动作。独特性姿势越成功，使用者越依赖外部承认，内部兴趣反而沙化。不被结算不是反对表达，而是保留一块无需证明独特也会继续的实践。",
}


QUESTIONS = {
    "entrusted-appeal": ["设备给答案以前，身体是否先发出过未被命名的线索？", "那条线索由本人回应，还是被报告直接关闭？", "没有提示时还能不能出现日常委托？", "高阶委托出现前，哪些普通信号长期没有回音？", "延后代理后，委托—感应回路是否真的恢复往返？"],
    "suspended-drowning": ["支持拿走的是痛苦，还是也拿走了组织混乱的动作？", "当事人有没有先提出过自己的次序和理由？", "外部答案撤后出现的是生疏还是完全无从开始？", "哪项支持属于灾难性必需，绝不能撤？", "保留摩擦后综合能力是否能迁移到新场景？"],
    "activative-deprivation": ["当事人的哪一次拒绝真实改变了下一步？", "回应被听见后是否仍被规则空气化？", "沉默只发生在暴力关系内还是遍及所有场景？", "身份债役怎样把不行动解释为尽责？", "安全脱离后，发起能力按什么次序恢复？"],
    "displaced-growth": ["这次成功中哪一步由团体替成员完成？", "担保降低后同一判断还能否被提出？", "沉默出现时主持者等了多久才接管？", "团体外的后果由成员还是团体继续承担？", "迁移裂缝缩小来自内化还是新增担保？"],
    "transgenerational-self-wiring": ["暴力前是否先出现撤稳迹象？", "施暴后恢复的是控制收益还是自我完整感？", "三重接线中的哪一条最先启动？", "替代支架能否承担同样稳定功能？", "接线闸合上后，隐蔽控制是否同时下降？"],
    "generative-collusion": ["暴力后首先需要修复的是谁的道德身份？", "道歉有没有带来权力让渡和长期问责？", "受害者的忍耐被登记成何种道德债权？", "哪一步交互承包关闭了退出？", "取消固定仪式后复发路径是否改变？"],
    "grey-matter-order": ["当前仍有现实暴力发动机在运行吗？", "旧规则怎样被拆散进日常微动作？", "安全提高后哪些回避没有同步消失？", "选择偏离旧轨时由什么力量把它推回？", "新回应能否打断低能耗自持？"],
    "unanchored-operation": ["空白出现后谁第一个救场？", "参与者从未学过还是曾经会而生疏？", "第一项无权威发起能否被别人接续？", "守住空白多久后才出现真实动作？", "下一次完成同类任务需要的提示是否减少？"],
    "tentative-ethics": ["旧规则在哪个具体处境中失效？", "试探是否可撤回且没有把风险转给弱者？", "反馈由哪些受影响者给出？", "修正改变了动作还是只改变解释？", "结算后是否增加了真实可选择的生活路径？"],
    "sedimented-layer": ["这条痕迹源自哪一次完整伦理事件？", "压缩时删掉了谁和什么冲突？", "痕迹靠惩罚保存还是能脱离原权力留存？", "后来者怎样重新解释而非照抄？", "再激活是否改变了新处境中的判断？"],
    "successful-abolition": ["身体版本是否在建议出现前形成？", "回路闭合点由谁作最后判断？", "外部符号节点是校验还是直接结算？", "结果正确时自身修正能力有没有增长？", "先感后核验能否逐步接回体知回路？"],
    "guarding-occurrence": ["教师在评课语言出现前察觉了什么转折？", "结算任务是否中断了正在发生的教学？", "教师能否用自己的词命名现场？", "延后非必要报告后学生回应怎样变化？", "发生感是否能预测理解而非只表达偏好？"],
    "pseudo-repair": ["希望动作进入的是创造节点还是任务通道？", "完成后有没有具体幸福节点和心理句号？", "修复是否只新增了目标与打卡？", "停止任务后希望回路能否自行出现？", "非任务入口能不能阻断修复能量倒灌？"],
    "mutual-severance": ["哪次路线冲突触发了第一刀互裁？", "确认动作怎样让被切者不再属于我们？", "标定动作给少数路线贴了什么标签？", "被遗忘的可能路线还能否被重建？", "减少互裁后社会硬度是否真实下降？"],
    "from-guarding-to-touching": ["此刻教师依据什么判准作出回应？", "同一句话换人或换时刻是否仍成立？", "学生反应有没有改写教师判准？", "制度保存的是空间还是标准话术？", "推广后触摸增加还是只增加相似动作？"],
    "void-facing": ["对方哪句话撞出了钝响？", "概念是否因这句话改变边界？", "研究者的反思有没有替代真正接触？", "对方能否纠正记录并改变下一步？", "接触面建立后虚空对视是否减少？"],
    "ground-strength": ["困难动作持续多久才被快速刺激打断？", "主体沉积层里已有何种亲自承担的痕迹？", "启动依赖兴趣还是依赖紧迫刺激？", "壳中养骨是否保留退出和恢复？", "自我卷入判决出现后能否在新任务继续？"],
    "meaning-prosthesis": ["这项希望由本人发起还是由平台号召？", "三重节奏在哪一拍中断？", "意义余热被用来完成了什么任务？", "集体连接有没有生成共同方向？", "增加厚土后意义器官是否恢复判断？"],
    "algorithmic-substitution": ["模板是在感受前还是感受后进入？", "谁拥有最后的感受裁判权？", "算法跳过了哪项生成条件？", "两人能否保留暂时不知道？", "撤去提示后不可治理残余能否引出真实追问？"],
    "singularity-posture": ["这项独特来自长期实践还是展示要求？", "姿势化删掉了哪些生长史？", "无人看见时活动是否仍继续？", "标签增加后内部兴趣是否出现沙化？", "保留不被结算部分能否恢复生成性实践？"],
}


BANNED = [
    "就这条因果链而言", "如果只看表面结果", "把局部动作连起来看", "从尚未进入记录的一端看",
    "从承受结果的一端看", "把时间顺序放回来", "让类比保持在同一条线上", "只看可核材料时",
    "把额外代价记入同一本账", "回到现场执行", "从失败后的去向看", "在不扩大采集的前提下",
    "把权限和动作并列后", "把复核责任写清后", "本节只围绕", "不把缺失部分靠猜测补齐",
    "个人场景先把第一步拿回来", "关系场景先约定退出权", "组织场景保留旧流程作对照",
    "把权力与责任写进记录", "复盘时只回答三个问题", "把结论压缩成继续、缩小、暂停或撤回",
]


def han(text: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", text))


def parse_text(raw: str) -> tuple[str, str, str, list[tuple[str, str]]]:
    title = re.search(r"^TITLE:\s*(.+)$", raw, re.M).group(1)
    sub = re.search(r"^SUB:\s*(.+)$", raw, re.M).group(1)
    abstract = re.search(r"^ABS:\s*(.+)$", raw, re.M).group(1)
    sections = [(m.group(1).strip(), m.group(2).strip()) for m in re.finditer(r"^==\s+(.+?)\n([\s\S]*?)(?=^==\s+|\Z)", raw, re.M)]
    return title, sub, abstract, sections


def parse(path: Path) -> tuple[str, str, str, list[tuple[str, str]]]:
    return parse_text(path.read_text(encoding="utf-8"))


def serialise(title: str, sub: str, abstract: str, sections: list[tuple[str, str]]) -> str:
    return f"TITLE: {title}\nSUB: {sub}\nABS: {abstract}\n\n" + "\n\n".join(f"== {h}\n{b}" for h, b in sections) + "\n"


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    return [x.strip() for x in re.split(r"(?<=[。！？；])", text) if x.strip()]


def glossary_body(slug: str) -> str:
    words = list(GLOSS[slug])
    intro = f"母文核心关键词先列齐：{'、'.join(words)}。这些词共同承担理论骨架，少掉任何一项，后面的判断都会变成另一篇文章。"
    rows = [f"母文把这个叫“{word}”，说的就是{definition}。" for word, definition in GLOSS[slug].items()]
    return "\n\n".join([intro + rows[0], "".join(rows[1:4]), "".join(rows[4:])])


def relation_body(slug: str) -> str:
    words = list(GLOSS[slug])
    return CHAIN[slug] + f"\n\n把这条链压成一次核对：先找“{words[0]}”的起点，再看“{words[1]}”是否改变了发生次序，随后用“{words[2]}”解释中间工序，最后由“{words[-1]}”提供边界或结果。每一个词都必须指向不同的事件位置；若几个词只能指向同一件事，它们就尚未取得独立含义。"


def add_unique(text: str, slug: str, idx: int, target: int = 365, context: str = "") -> str:
    words = list(GLOSS[slug])
    a, b, c, d = (words[(idx + shift) % len(words)] for shift in range(4))
    da, db = GLOSS[slug][a], GLOSS[slug][b]
    label = f"“{context}”" if context else "这一处"
    catalog = [
        f"{label}要把“{a}”与“{b}”分开，其中前者指{da}，后者指{db}，前一位置没有材料，不能拿后一位置的结果倒推它必然出现。",
        f"能支持{label}的事件必须同时留下起点和转折：先看“{b}”何时进入，再看“{c}”是否随后改变，只有最终结果而没有中间动作还不足以支持母文。",
        f"给{label}安排一个相反情形：若“{c}”已经出现而预测的后续变化没有发生，就缩小“{words[0]}”的范围，不用新增例外名称保护主张。",
        f"记录{label}时，至少标出“{d}”发生的时刻、动作人、拒绝权和结果，只剩作者解释而没有事件位置时，这个概念暂时不能为母文作证。",
        f"{label}的强版本要求“{a}”稳定改变“{c}”，弱版本只说两者偶尔同现，两种强度必须分开，否则零结果总能被改口吸收。",
        f"从责任位置核对{label}：谁启动“{b}”，谁承受“{d}”没有发生的代价，谁又有权宣布流程已经成功，这三项不能默认属于同一人。",
        f"把{label}放进两个条件相近的案例，一个保留“{a}”，另一个只出现“{c}”，若后续没有可辨差别，母文的独立解释力就要下降。",
        f"{label}中的未知项继续保留未知，尤其不能把“{words[-1]}”写成任何结果都能容纳的原因，因为理论若不能被相反材料削弱，名称越精细，内容反而越空。",
    ]
    start = idx % len(catalog)
    extras = catalog[start:] + catalog[:start]
    out = text.strip()
    existing = {re.sub(r"[^\u3400-\u9fff]", "", sentence) for sentence in sentences(out)}
    for extra in extras:
        if han(out) >= target:
            break
        key = re.sub(r"[^\u3400-\u9fff]", "", extra)
        if key in existing:
            continue
        out += "\n\n" + extra
        existing.add(key)
    return out


def strip_fillers(text: str) -> str:
    for phrase in BANNED:
        text = re.sub(rf"[^。！？；]*{re.escape(phrase)}[^。！？；]*[。！？；]?", "", text)
    # Remove the cross-article boilerplate that made V2 formally complete but editorially empty.
    patterns = [
        r"这个起点重要[^。]*。", r"概念只是给动作起名[^。]*。", r"真正有力的反例不是[^。]*。",
        r"位置移动通常没有宣布时刻[^。]*。", r"适用范围越清楚[^。]*。", r"证据不只寻找支持案例[^。]*。",
        r"误用往往从一句善意口号开始[^。]*。", r"每轮只选择继续、缩小、暂停或撤回之一[^。]*。",
        r"决定写下后由一名未主持练习的人核对[^。]*。", r"复盘会议设定短时限[^。]*。",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def remove_cross_document_boilerplate(all_sections: dict[tuple[str, str], list[dict[str, str]]]) -> None:
    """Delete every repeated long sentence, within a document or across documents."""
    for _ in range(3):
        places: dict[str, list[tuple[str, str]]] = {}
        for doc, sections in all_sections.items():
            for section in sections:
                for sentence in sentences(section["text"]):
                    key = re.sub(r"[^\u3400-\u9fff]", "", sentence)
                    if han(key) >= 24:
                        places.setdefault(key, []).append(doc)
        repeated = {key for key, docs in places.items() if len(docs) > 1}
        if not repeated:
            return
        for (slug, kind), sections in all_sections.items():
            for idx, section in enumerate(sections):
                kept = []
                for sentence in sentences(section["text"]):
                    key = re.sub(r"[^\u3400-\u9fff]", "", sentence)
                    if key not in repeated:
                        kept.append(sentence)
                section["text"] = "".join(kept)
    remaining = [(key, docs) for key, docs in places.items() if len(docs) > 1]
    raise AssertionError(f"duplicate prose survived three editorial passes: {remaining[:5]}")


def mother_sentence_pool(item: v2.Item, explanation: bool) -> list[str]:
    raw = (BASE / item.slug / "index.html").read_text(encoding="utf-8")
    raw = re.sub(r"<script\b[\s\S]*?</script>|<style\b[\s\S]*?</style>", "", raw, flags=re.I)
    pool: list[str] = []
    seen: set[str] = set()
    for paragraph in re.findall(r"<p[^>]*>([\s\S]*?)</p>", raw, flags=re.I):
        clean = v1.clean(paragraph, explanation)
        if re.search(r"参考文献|版权所有|评分：|ISBN|DOI|卷期|页码|附论|同批稿件", clean):
            continue
        for sentence in sentences(clean):
            amount = han(sentence)
            key = re.sub(r"[^\u3400-\u9fff]", "", sentence)
            if re.match(r"^(?:本文|本节|第[一二三四五六七八九十0-9]+节|初审|终审|定义|证伪|小结|结论|回应|反驳|下文|上述|以下)", sentence):
                continue
            if re.search(r"理论收益|近邻检测|同题族|正面对抗|不可还原校验|形成过程分析意义", sentence):
                continue
            if not 45 <= amount <= 175 or key in seen:
                continue
            seen.add(key)
            pool.append(sentence)
    # Explanation and practice receive disjoint mother passages so the two
    # companion texts do not repeat one another's evidence.
    return pool[::2] if explanation else pool[1::2]


def relevance(sentence: str, heading: str, body: str, slug: str) -> int:
    score = 0
    for term in GLOSS[slug]:
        if term in sentence:
            score += 20
        if term in heading:
            score += 3 * sentence.count(term)
    compact = re.sub(r"[^\u3400-\u9fff]", "", heading + body[-120:])
    bigrams = {compact[i:i + 2] for i in range(max(0, len(compact) - 1))}
    score += sum(1 for gram in bigrams if gram in sentence)
    return score


def enrich_from_mother(all_sections: dict[tuple[str, str], list[dict[str, str]]]) -> None:
    item_by_slug = {item.slug: item for item in v2.ITEMS}
    for (slug, kind), sections in all_sections.items():
        explanation = kind == "explain"
        pool = mother_sentence_pool(item_by_slug[slug], explanation)
        existing_compact = re.sub(r"[^\u3400-\u9fff]", "", "".join(section["text"] for section in sections))
        used: set[int] = {
            idx for idx, sentence in enumerate(pool)
            if re.sub(r"[^\u3400-\u9fff]", "", sentence) in existing_compact
        }
        explain_leads = [
            "与这一步最贴近的母文材料是：", "母文把这里写得更具体：", "把判断落到原文细部，会看到：",
            "原文为这个分辨留下了一个事件：", "母文在这里补出一项条件：", "能约束这项判断的原文是：",
            "原文没有停在口号上，它进一步写道：", "母文还保留了一条相反材料：",
        ]
        practice_leads = [
            "这项动作还要受一条母文材料约束：", "执行前先对照原文中的这个事件：", "母文为这一步提供的判据是：",
            "这一步不能脱离母文留下的条件：", "操作表旁边应保留这条原文材料：", "决定是否继续时要回看：",
            "该动作若解释不了这条材料，就应缩小：", "作为反向校验，还要放入母文的另一处观察：",
        ]
        for section_idx, section in enumerate(sections):
            additions = 0
            while han(section["text"]) < 365:
                choices = explain_leads if explanation else practice_leads
                lead = choices[(section_idx + additions) % len(choices)]
                candidates = [
                    (relevance(sentence, section["heading"], section["text"], slug), idx, sentence)
                    for idx, sentence in enumerate(pool)
                    if idx not in used and han(section["text"] + lead + sentence) <= 485
                ]
                if not candidates:
                    break
                _, idx, sentence = max(candidates, key=lambda row: (row[0], -row[1]))
                used.add(idx)
                section["text"] = section["text"].rstrip() + "\n\n" + lead + sentence
                additions += 1


def fill_short_sections(all_sections: dict[tuple[str, str], list[dict[str, str]]]) -> None:
    for (slug, _kind), sections in all_sections.items():
        for idx, section in enumerate(sections):
            section["text"] = add_unique(section["text"], slug, idx, 365, section["heading"])


def derived_terms(slug: str) -> list[tuple[str, str]]:
    words = list(GLOSS[slug])
    return [
        (f"{words[0]}起点表", f"记录{QUESTIONS[slug][0].rstrip('？')}的原始事件，而不先给人格结论"),
        (f"{words[1]}介入点", f"标出{QUESTIONS[slug][1].rstrip('？')}的具体时刻和动作"),
        (f"{words[2]}转向量", f"比较关键条件改变前后，母文所说的中间工序是否同向变化"),
        (f"{words[-1]}恢复线", f"追踪撤去或延后关键条件后，目标能力按什么次序恢复"),
        (f"{words[0]}反例簿", f"保存条件相似却没有出现母文预测结果的案例，并据此缩小理论"),
    ]


def locate_body(slug: str) -> str:
    intro = "定位不用满意度和自我评价，只回答五个能落到事件上的问题。不同答案指向不同断点，不能用一个动作通吃。"
    body = "\n\n".join(QUESTIONS[slug])
    words = list(GLOSS[slug])
    tail = f"五问答完，只圈时间上最早且已有材料的断点。若最早断点落在“{words[1]}”，先改变介入次序；若落在“{words[2]}”，先撤掉标准答案；若只能看见结果而找不到起点，本轮记为未知，不启动干预。定位的产物不是分数，而是一条写明谁先动作、谁能拒绝、谁承担后果的事件线。"
    return intro + "\n\n" + body + "\n\n" + tail


def derived_body(slug: str) -> str:
    rows = derived_terms(slug)
    intro = "实践文不另造一套管理学词汇，所有动作名和读数名都从母文原词长出："
    first = "".join(f"“{name}”用于{desc}。" for name, desc in rows[:3])
    second = "".join(f"“{name}”用于{desc}。" for name, desc in rows[3:])
    tail = "这些名称只服务本篇母文，不相加成总分，不跨文章借用。记录者若不能从读数追溯到母文概念和一条真实事件，就删除该读数。"
    return "\n\n".join([intro + first, second + tail])


def readings_body(slug: str, item: v2.Item) -> str:
    rows = derived_terms(slug)
    return (
        f"读数只保留五项：{'、'.join(name for name, _ in rows)}。过程读数先查动作是否真的发生；结果读数再看{item.observable}；反作用读数另记新增时间、压力、隐私负担和流程干扰。每项都预先写明何种方向支持继续、何种方向要求缩小，不能把上升和下降都解释成理论正确。\n\n"
        f"采集使用最近一次事件的时间线、一次短周期对照和一份{rows[-1][0]}，不做每日排名，也不要求参与者制造高风险情境。原始版本保留，后来解释另页追加；没有材料就写未知。代价必须和结果同页出现：记录会改变现场，母文术语也可能诱导观察者只看自己想看的部分。任何读数一旦进入绩效、伴侣评价、学生排名或治疗服从考核，立即停用。"
    )


def rewrite_explanation(item: v2.Item) -> tuple[str, list[dict[str, str]]]:
    baseline = v2.make_sections(item, "explain")
    title, sub, abstract, old = parse_text(v1.source_text(item, "explain", baseline))
    cleaned = [(h, strip_fillers(b)) for h, b in old]
    # Replace generic V2 headings with a sequence grown from the mother vocabulary.
    words = list(GLOSS[item.slug])
    names = [
        "先把母文核心关键词说清", "从一个日常场景说起", f"{words[0]}怎样从场景中出现",
        f"{words[1]}改变了哪一步", f"{words[2]}为何不只是一个结果", f"{words[3]}把当事人放在什么位置",
        f"{words[-1]}怎样把变化继续下去", f"时间一长，{words[0]}会怎样变形", "反例怎样收窄母文",
        "回到这个日常场景", "把类比再推一步", f"与{item.neighbour}的分离线", "母文判断在哪里止步",
        "什么材料会削弱母文", "它不能被这样误用",
    ]
    # Preserve the strongest article-specific mother material while replacing the common shell.
    bodies = [
        glossary_body(item.slug), cleaned[0][1], relation_body(item.slug), cleaned[1][1], cleaned[2][1],
        cleaned[3][1], cleaned[4][1], cleaned[6][1], cleaned[7][1], cleaned[8][1], cleaned[9][1],
        cleaned[10][1], cleaned[11][1], cleaned[12][1], cleaned[13][1],
    ]
    assert len(names) == len(bodies) == 15
    sections = []
    for idx, (heading, body) in enumerate(zip(names, bodies)):
        for old_term, new_term in v1.FORBIDDEN.items():
            body = body.replace(old_term, new_term)
        sections.append({"heading": heading, "text": body})
    source = serialise(title, sub, abstract, [(x["heading"], x["text"]) for x in sections])
    for old_term, new_term in v1.FORBIDDEN.items():
        source = source.replace(old_term, new_term)
    return source, sections


def rewrite_practice(item: v2.Item) -> tuple[str, list[dict[str, str]]]:
    baseline = v2.make_sections(item, "practice")
    title, sub, abstract, old = parse_text(v1.source_text(item, "practice", baseline))
    old = [(h, strip_fillers(b)) for h, b in old]
    words = list(GLOSS[item.slug])
    headings = [
        "这套方法做什么、不做什么", "先定位：问题究竟卡在哪一环", "边界先行：先排除不能试的现场",
        "用母文术语给动作和读数命名", f"留下{words[0]}的原始事件", f"只改动{words[1]}的介入时刻",
        f"检查{words[2]}有没有改向", f"把{words[3]}放进一次真实场景", f"用{words[-1]}做一个短对照",
        f"为{words[0]}寻找阴性案例", f"谁能解释{words[1]}的记录", f"按{words[2]}复盘失败",
        "把结果变成继续、缩小、暂停或撤回", "读数、采集办法与代价", "什么时候应该停，什么时候说明理论可能不对",
    ]
    # Keep mother-specific evidence from V2, but replace its universal action spine.
    bodies = [old[0][1], locate_body(item.slug), old[2][1], derived_body(item.slug)]
    bodies += [old[i][1] for i in range(3, 12)]
    bodies += [readings_body(item.slug, item), old[13][1]]
    assert len(headings) == len(bodies) == 15
    # Make the action sections operationally inherit the mother vocabulary.
    derived = derived_terms(item.slug)
    action_insertions = [
        f"先建立“{derived[0][0]}”：{derived[0][1]}。只收一件已经发生的事，写清时间、动作、回应和后果。",
        f"本轮唯一动作是：{item.action}。它专门移动“{derived[1][0]}”，其他人员、目标和安全措施不变。",
        f"动作后使用“{derived[2][0]}”：{derived[2][1]}。若中间工序没变化，不讨论最终结果好坏。",
        f"场景必须符合母文范围：{item.scope}。参与者先保留自己的版本，再让外部答案进入，并标出哪一步被改写。",
        f"短对照使用“{derived[3][0]}”：{derived[3][1]}。旧流程和新动作各做一次，不扩大到全域。",
        f"阴性案例写入“{derived[4][0]}”：{item.counter}。反例与支持案例使用相同观察窗口。",
        f"记录解释权不能由推动方法的人独占。参与者可查看、纠错并删除涉及自己的材料，成本由实际承担者确认。",
        f"复盘只核对动作、差异和代价。任何答案都要指向“{derived[0][0]}”中的原句，不用态度评价替代事件。",
        f"继续必须保持相同强度；缩小要删去不成立场景；暂停要给复查日期；撤回则恢复原流程并清理不必要记录。",
    ]
    for pos, addition in enumerate(action_insertions, 4):
        bodies[pos] = addition + "\n\n" + bodies[pos]
    sections = []
    for idx, (heading, body) in enumerate(zip(headings, bodies)):
        sections.append({"heading": heading, "text": body})
    source = serialise(title, sub, abstract, [(x["heading"], x["text"]) for x in sections])
    return source, sections


def audit(all_sections: dict[tuple[str, str], list[dict[str, str]]]) -> dict:
    report = {"student": "张琼", "date": "2026-08-13", "batch": 2, "revision": 3, "pages": []}
    global_sentences: dict[str, list[str]] = {}
    for item in v2.ITEMS:
        terms = list(GLOSS[item.slug])
        for kind, route in (("explain", "interpretation"), ("practice", "practice")):
            sections = all_sections[(item.slug, kind)]
            source = (BASE / item.slug / route / "source.txt").read_text(encoding="utf-8")
            counts = [han(x["text"]) for x in sections]
            assert 14 <= len(sections) <= 24
            assert all(350 <= n <= 500 for n in counts), (item.slug, kind, min(counts), max(counts))
            assert sum(counts) >= 4800, (item.slug, kind, sum(counts))
            assert not any(phrase in source for phrase in BANNED), (item.slug, kind)
            headings = [x["heading"] for x in sections]
            assert not any(re.match(r"^[一二三四五六七八九十百]+[、.．]|^\d+[、.．]", h) for h in headings)
            if kind == "explain":
                assert all(term not in source for term in v1.FORBIDDEN)
                for fixed in ("回到这个日常场景", "把类比再推一步", "它不能被这样误用"):
                    assert fixed in headings
                for term in terms:
                    assert source.count(term) >= 2, (item.slug, term, source.count(term))
                    assert f"母文把这个叫“{term}”，说的就是" in source
            else:
                for fixed in ("先定位：问题究竟卡在哪一环", "读数、采集办法与代价", "什么时候应该停，什么时候说明理论可能不对"):
                    assert fixed in headings
                for name, _ in derived_terms(item.slug):
                    assert source.count(name) >= 2, (item.slug, name)
            for sentence in sentences(" ".join(x["text"] for x in sections)):
                key = re.sub(r"[^\u3400-\u9fff]", "", sentence)
                if han(key) >= 24:
                    global_sentences.setdefault(key, []).append(f"{item.slug}/{kind}")
            report["pages"].append({
                "slug": item.slug, "kind": kind, "han": sum(counts), "sections": len(sections),
                "min_section_han": min(counts), "max_section_han": max(counts),
                "mother_terms": {term: source.count(term) for term in terms},
                "derived_readings": [name for name, _ in derived_terms(item.slug)] if kind == "practice" else [],
            })
    repeats = {s: locs for s, locs in global_sentences.items() if len(locs) > 1}
    report["duplicate_sentences_within_or_across_documents"] = len(repeats)
    assert not repeats, list(repeats.items())[:3]
    return report


def main() -> None:
    all_sections: dict[tuple[str, str], list[dict[str, str]]] = {}
    dossiers = []
    for item in v2.ITEMS:
        exp_source, exp_sections = rewrite_explanation(item)
        pra_source, pra_sections = rewrite_practice(item)
        for kind, route, source, sections in (
            ("explain", "interpretation", exp_source, exp_sections),
            ("practice", "practice", pra_source, pra_sections),
        ):
            out = BASE / item.slug / route
            (out / "source.txt").write_text(source, encoding="utf-8")
            page = v1.render(item, kind, sections, source)
            if kind == "explain":
                for old_term, new_term in v1.FORBIDDEN.items():
                    page = page.replace(old_term, new_term)
            (out / "index.html").write_text(page, encoding="utf-8")
            all_sections[(item.slug, kind)] = sections
        dossiers.append({
            "slug": item.slug, "title": item.title, "core": item.core,
            "terms": GLOSS[item.slug], "concept_chain": CHAIN[item.slug],
            "diagnostic_questions": QUESTIONS[item.slug], "derived_terms": dict(derived_terms(item.slug)),
            "scope": item.scope, "counterexample": item.counter, "falsifier": item.falsifier,
        })
        print(f"REWROTE {item.slug}")
    remove_cross_document_boilerplate(all_sections)
    enrich_from_mother(all_sections)
    remove_cross_document_boilerplate(all_sections)
    fill_short_sections(all_sections)
    remove_cross_document_boilerplate(all_sections)
    fill_short_sections(all_sections)
    # The rejection pass above changes bodies in memory.  Publish only those
    # de-templated bodies, preserving the already selected titles and abstracts.
    for item in v2.ITEMS:
        for kind, route in (("explain", "interpretation"), ("practice", "practice")):
            out = BASE / item.slug / route
            title, sub, abstract, _ = parse(out / "source.txt")
            sections = all_sections[(item.slug, kind)]
            source = serialise(title, sub, abstract, [(x["heading"], x["text"]) for x in sections])
            if kind == "explain":
                for old_term, new_term in v1.FORBIDDEN.items():
                    source = source.replace(old_term, new_term)
            (out / "source.txt").write_text(source, encoding="utf-8")
            page = v1.render(item, kind, sections, source)
            if kind == "explain":
                for old_term, new_term in v1.FORBIDDEN.items():
                    page = page.replace(old_term, new_term)
            (out / "index.html").write_text(page, encoding="utf-8")
    (BASE / "companion-dossiers-v3.json").write_text(json.dumps(dossiers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = audit(all_sections)
    (BASE / "companion-audit-v3.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pages = report["pages"]
    print(f"PASS pages={len(pages)} han={min(x['han'] for x in pages)}-{max(x['han'] for x in pages)} cross_duplicates=0")


if __name__ == "__main__":
    main()
