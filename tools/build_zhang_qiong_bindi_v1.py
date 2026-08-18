#!/usr/bin/env python3
"""Rebuild Zhang Qiong's 20 representative companion pairs to v1.0.

The script deliberately treats the previously published companion pages as the
editorial draft layer: it preserves their article-specific reasoning, removes
old summary/action tails, redistributes the material into compliant sections,
adds the required boundary/falsification frames, and publishes canonical
directory-style pages plus plain-text sources.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "public" / "students" / "zhang-qiong"
TODAY = "2026年8月13日"

FORBIDDEN = {
    "SDE": "这套分析",
    "发生学": "形成过程分析",
    "本体论": "存在方式分析",
    "二阶碰撞": "双重对照",
    "学科通融": "跨领域互证",
    "差异序列": "变化次序",
    "纠缠": "交织",
    "显露": "呈现",
}


@dataclass(frozen=True)
class Item:
    slug: str
    score: float
    title: str
    explain_title: str
    practice_title: str
    analogy: str
    core: str
    neighbour: str
    divide: str
    observable: str
    falsifier: str
    stop: str
    risk: bool = False


ITEMS = [
    Item("recognitive-autophagy", 151.2, "识别性自噬", "手表已经说累了，身体还有机会开口吗？", "先感后看：把判断顺序留给自己", "睡眠手表", "外部标签若总在人的感受成形之前先给出答案，清晰度可能反过来削弱第一人称判断的练习机会", "普通技能退化", "普通退化丢的是熟练度，母文所说的风险丢的是产生判准的起点；前者复练即回升，后者会先出现无从比较的空档", "不看数据前能够独立说出的具体感受数、数据冲突时仍保留自身版本的次数，以及撤掉设备后形成暂时判断所需的时间", "延后查看数据并未改善独立判断，撤掉设备后也没有出现母文预测的空档", "出现急性症状、用药调整、慢病波动或专业人员要求连续监测时，应停止练习并以医疗安全为先", True),
    Item("reverse-cycle", 151, "命名那条分离线：理论生产的‘逆循环’与‘何以钝感’", "地图越印越精美，为什么路越走越绕？", "查一次绕路账：给旧地图安排实地复核", "旧城市地图", "一套工具赖以成立的现实条件已经变化时，使用者可能靠更精细的修补让它继续成功，从而把失配积成看不见的解释债务", "路径依赖", "路径依赖强调转换成本让人留在旧路上；这里的机制更反常，旧工具不是勉强维持，而是在新材料上显得更高产、更顺手", "反复绕路却被不同理由解释掉的次数、旧术语新增补丁的数量，以及脚注或例外区里累计的未解释材料", "现实条件改变后旧工具能够快速修正核心判准，没有出现高产与系统遗漏并存的阶段", "当旧工具承担飞行、医疗、工程安全等即时决策时，不做突然撤换，只能先建立平行记录和独立复核"),
    Item("calibrative-genesis", 150.5, "配准性生成", "安全网托得越稳，人为什么越不敢换地板？", "画出担保地图：训练离场后的独立决断", "安全网与地板", "长期成功的团体不仅帮助成员表达，也可能把判断赖以站立的担保条件悄悄写进成员，使能力在离场后难以迁移", "群体思维", "群体思维说成员为了一致而压低异议；母文描述的成员可能在团体里高度坦诚，问题是判断能力被特定的承接条件配准，换场后便失去落脚点", "同一判断在团体内外被主动提出的比例、离场后承担后果的完成度，以及没有熟悉回应时继续行动的次数", "成员离团后无需额外过渡就能等量迁移判断和行动，且担保条件强弱与迁移没有关系", "若团体涉及治疗、创伤披露或强权主持，不以迁移训练替代专业伦理、保密和转介制度", True),
    Item("positivist-attestation", 150, "社会学如何将存在感化约为不可说之物", "表格没有那一栏，那件事就不存在了吗？", "给表格开侧门：审查被字段抹掉的经验", "办事表格", "记录系统不只描述现实；当只有能进入字段的经验才获得承认时，登记方式也在决定什么有资格被当作存在", "承认理论", "承认理论关注一个人是否被他人尊重；这里更早一步，分析的是经验能否先取得可登记、可讨论的存在资格", "无法入栏却反复出现的案例数、自由叙述进入正式判断的比例，以及新增侧门是否真的改变后续处置", "开放非格式通道以后，被遗漏经验仍不能影响任何判断，字段结构与存在资格之间也没有稳定关系", "法定申报、医疗编码和安全清单不能随意取消；只能增加复核通道，不能用开放叙述替换必要字段"),
    Item("counter-body", 150, "逆身", "修得越来越好，为什么反而不知道自己怎么了？", "留下最后一票：保护当事人的裁决权", "不断返修的车辆", "连续修复可能把当事人从判断者变成被处理的对象；真正被拿走的不只是选择，而是对自身状态作出判断并承受后果的位置", "习得性无助", "习得性无助强调反复失败后不再行动；母文所说的人可能积极配合所有方案，失去的却是判断哪种结果算对、以及由谁认账的权利", "当事人能否先说出自己的目标、能否拒绝一项低风险建议、能否区分证据建议与最终裁决，以及决定后的责任归属是否清楚", "即使持续保留最后裁决权，当事人的判断能力仍按同样速度下降，代理程度与能力变化没有关联", "遇到急症、自伤风险、暴力控制、未成年人安全或必须遵医嘱的情形，立即停止低风险试验并转向专业处置", True),
    Item("ethical-idling", 149, "伦理空转项", "发动机一直轰鸣，车为什么没有前进一步？", "先看挂没挂挡：审计伦理语言的承重动作", "空挡轰鸣的发动机", "伦理话语可以非常真诚、完整并被制度奖励，却没有接上承担代价的行动支架，于是表达越丰富，现实越可能原地不动", "言行不一", "言行不一把问题落在说话者不诚实；伦理空转允许说话者完全真诚，缺口发生在话语与承重条件没有挂接", "一句伦理判断之后实际改变的资源、时间和责任，承担动作持续的周期，以及同场对比中有无支架时行动差异", "不论是否存在承重支架，同类伦理表达都稳定预测相同的行动，空转与挂挡无法经验区分", "涉及举报、创伤、家暴或身份暴露时，不要求当事人用行动证明真诚，先处理安全和权力风险"),
    Item("descriptive-intervention", 148, "描述性干预", "相机拍得越清楚，拍照的人为什么越碰不到现场？", "留一份火的记录：阻止描述把经验冻住", "事故现场的相机", "描述并非中性搬运；完美的整理可能同时把描述者从被现场改变的位置撤走，使方法成为对自身的保护层", "观察者效应", "观察者效应说观察改变对象；母文反向追问描述如何改变观察者，使其在分类完成后不再需要承受对象带来的冲击", "原始记录与成品之间被删去的迟疑数、描述者因此修改自身判断的次数，以及概念遭遇反例后是否真正改形", "保留原始冲击记录与只留整理成品的两组，在判断修正和后续观察上没有任何差异", "涉及真实受害者和隐私材料时，保留原始记录不得突破同意、匿名与保密边界"),
    Item("ethical-mending", 147, "伦续", "衣服每次都缝好了，关系为什么还是越来越薄？", "追一条缝补链：看见道德连接怎样续上", "随手缝衣的针线", "伦理连接往往不是靠宣言延续，而是在关系将断未断的瞬间，由来不及计算的小动作把下一步重新接上", "关怀伦理", "关怀伦理强调回应他人需要；母文更窄地识别断裂边缘的接续动作，并要求追踪它是否真的把下一次互动接出来", "一次缝补后下一次互动能否继续、接续动作是否形成链条，以及撤掉动作后断裂是否明显增加", "取消这些微小接续动作并不改变关系的连续性，或任何礼貌动作都产生相同效果", "不能用‘缝补关系’要求受伤者原谅、和解或继续留在不安全关系中", True),
    Item("unaccounted-begetting", 146, "不被算账的生育", "师傅没有讲出口的手艺，为什么最容易在考核中消失？", "留出不计件时间：保护共同做事中的传承", "师徒共同做活的工坊", "某些能力不是被讲授或计件生产出来，而是在不被即时结算的共同工作中互相长成；优化若剪掉这段空白，传承会先于产出消失", "默会知识", "默会知识说明有些知识说不清；母文进一步指出这种能力需要怎样的共同时间才能出生，以及结算制度怎样在出生前就把它剪掉", "无明确交付的共同工作时长、学徒在独立任务中的新判断数、意外传承发生的频率，以及两代人解决陌生问题的差异", "计件化与非计件化环境产生同等的独立判断和跨情境迁移，共同空白并不增加能力生成", "不得以传承为名制造无偿劳动、无限待命或权力依附；时间、责任和退出权必须公开"),
    Item("dwelling-in-unknowing", 145, "悬搁的日常化", "人人都说要容忍不知道，为什么问题还是立刻被填满？", "先搭条件再等答案：给未知留下可居住的位置", "憋气与可呼吸的房间", "长期停留在不知道之中不是意志品质，而需要时间、承接、保护和不立即交付成品的条件共同支撑", "模糊容忍", "模糊容忍被当作个人特质测量；母文把焦点移到环境是否允许问题保持未决，以及这种能力能否被日常条件托住", "问题在未被命名时持续的天数、被提前填答案的次数、未决材料最终产生新区分的比例，以及不同条件下的差异", "条件改善并不延长未决问题的寿命，也不增加新判断，个人特质完全解释所有变化", "在急救、法定时限和明确安全风险中不能为了保留未知而延误决策；先行动，再保留复盘空间"),
    Item("self-fueling-fire", 149, "自油火场", "灭火措施越来越多，为什么火反而烧得更旺？", "先分火和油：给改革做一次反向审计", "不断添油的灭火现场", "改革可能制造新的表格、角色和证明任务，这些产物又被当作问题仍在的证据，进而为下一轮改革提供燃料", "政策反馈", "政策反馈说明制度会形成自我强化利益；母文更具体地辨认‘解决措施的产物’怎样被误认成‘原问题的持续’，让改革靠自身副产品续命", "措施新增的证明任务数、目标达成后仍保留的岗位流程数、学习或工作本身获得的无任务时间，以及下一轮立项引用了哪些旧产物", "目标达成后改革装置能自然退出，新增任务不会成为后续立项理由，措施强度与问题表征没有正反馈", "涉及法定合规和安全制度时，不因反身审计擅自停掉保护措施；先证明副产品，再走正式退出程序"),
    Item("the-stand-in", 145, "替身", "样板课越来越漂亮，真正的学习去了哪里？", "拆掉一层样板：检验学习有没有真的发生", "精装修样板房", "评价系统会把可展示、可复制、可验收的学习外观做得越来越精致，最终让‘像学习的产物’占据学习本身的位置", "古德哈特定律", "古德哈特定律说指标成为目标后会失真；替身机制还解释谁持续生产逼真的外观，以及为什么生产者会真诚捍卫它就是学习", "离开提示后的迁移表现、学生提出新问题的数量、无人观摩时课堂行为是否保持，以及展示产物与陌生任务能力的相关性", "样板表现的提升始终同步带来陌生任务迁移和独立判断，撤掉展示要求反而使真实学习下降", "不能把检验变成新的公开课竞赛，也不能拿它要求教师或学生证明自己‘真实’；抽样应低风险且去绩效化"),
    Item("criterion-parasitism", 148, "判准寄生的双向吞噬环", "新招牌挂上以后，老手艺为什么连自己也说不清？", "暂时拿掉招牌：检查判断是否仍能站立", "老面馆换上平台招牌", "外来评价标准不只压制内部手艺；双方长期适配后，旧判准与新标准会互相吞噬，剩下一套谁也无法独立说明的混合判断", "制度同形", "制度同形关注组织变得相像；判准寄生追踪的是判断内核怎样在适配中被改写，以及拿掉外部标准后还有没有能站立的内部理由", "不看平台分数时仍能作出的整体判断数、内部理由能否推翻外部高分、拿掉标准后新人和老手判断的一致与分歧", "内部判准在适配全过程保持完整且能稳定否决外部标准，或拿掉标准后判断能力不受影响", "法定资质和安全标准不能用‘内部手艺’取代；拿掉检验只用于模拟或低风险复盘"),
    Item("epistemic-sclerosis", 141, "知识硬化", "石头磨得越来越光，为什么再也刻不出新纹路？", "给概念留一道毛边：恢复它碰到经验的能力", "被磨光的刻石", "概念为了流通、评审和统一使用而不断被磨平，可能同时失去被特殊经验卡住、变形并生成新区分的弹性", "物化", "物化指出人造关系被当作自然之物；知识硬化更关注概念经过哪些合规工序变得光滑，以及它为何因此失去受经验修改的能力", "例外是否进入正文、概念定义因案例而修改的次数、不同情境能否生成新分支，以及被删掉的毛刺有没有留下账目", "高度标准化的概念仍持续产生可检验的新区分，且对例外的吸收不会降低经验敏感度", "医疗诊断、工程规范等需要统一语言的场合，先保留标准词，再另开例外记录，不能直接拆除共识词表"),
    Item("mending-presence", 141, "从墙壁到缝匠", "墙上的洞全补好了，为什么声音还是传不过来？", "先别补平那条缝：把方法失败变成新感官", "墙壁上的裂缝", "方法碰壁不一定只意味着工具不足；若观察者承担接不上的那一段，裂缝可能被缝成一种此前没有的感知能力", "反身性", "反身性要求研究者交代自己的位置；母文还要求位置被具体失败改变，并让改变后的感知进入下一次判断，而不只写成方法声明", "被承认的接不上次数、它是否改变后续提问、由此产生的新区分能否被他人复现，以及失败是否只被换工具抹平", "承担方法失败与直接更换工具得到同样结果，所谓新感官不能提高任何后续辨认力", "涉及创伤叙事和临床现场时，研究者不能为了‘被改变’而追问当事人，安全与同意优先"),
    Item("singularity-inflation", 140, "独异性通胀", "人人都‘独一无二’，为什么彼此越来越像？", "查一次独特货币：减少标签的过量发行", "不断加印的奖状", "当独特成为人人必须取得的结算货币，标签会被系统性超发；名义上的差异增加，能够真正区分人的信息反而减少", "古德哈特定律", "古德哈特定律关心量化目标被操纵；独异性通胀解释即使没有作弊，结算节点也会主动增发新标签，使‘独特’自身失去稀缺与辨别力", "独特标签的新增速度、标签对后续行为的预测力、相同模板的复用率，以及不贴标签时能否描述具体差异", "标签数量上升的同时辨别力和预测力稳定提高，没有出现模板化与价值稀释", "不能以反通胀为名羞辱个体表达或取消少数身份的可见性；要减少空标签，而不是压低真实差异"),
    Item("constitutive-resonance", 142, "构成性共鸣", "越努力寻找意义，为什么越尝不出什么值得？", "留一件不打分的事：让意义从参与中长出来", "被手机评分打断的一餐", "意义未必由追求和选择直接生产；它可能在人被一件事叫住、长期参与并被关系反向构成时出现，过度结算会让这种能力闲置", "自我决定理论", "自我决定理论分析外部奖励怎样损害内在动机；母文区分动机强弱与意义判断能力，后者可能在没有明显奖励时也因长期代理而萎缩", "无评分活动的持续时间、参与中自发增加的责任、无人提醒时是否返回、以及活动结束后能否说出具体而非标签化的价值", "取消评价与目标以后仍不出现任何自发参与，代理程度也不影响意义判断，所有变化都可由动机解释", "不能拿‘让意义自己长’去取消必要教学支持、收入保障或心理帮助；无评分不等于无责任"),
    Item("gravity-or-death", 139, "关系的重力，抑或关系的死亡", "假花永远不会枯，为什么屋里反而没有生命？", "留一处不填满：重新感觉关系可能失去", "永不凋谢的假花", "关系若把所有裂缝都立即修平，可能逐渐失去‘它也可能终结’的真实感；稳定仍在，促使双方重新选择彼此的重力却消失", "依恋理论", "依恋理论关注安全联结怎样降低失去焦虑；母文区分安全与无死亡感，安全仍容许分离被想象，无死亡感则让关系像不会改变的背景", "双方主动选择共同活动的次数、未被立即填平的分歧是否产生新决定、谈及可能失去时能否出现具体而非威胁性的回应", "关系越缺少失去感越能持续产生主动选择与更新，保留未填缝隙只带来损害而无任何重力恢复", "存在暴力、胁迫、跟踪、严重创伤或分离风险时，不能制造不确定性；先求助、转介并保护安全", True),
    Item("intimate-presence", 138, "当亲密不再亲临", "恒温房越来越舒适，两个人为什么越来越不会问？", "把分析往后放：恢复亲密中的互相探问", "恒温房", "情感工具和固定解释若不断提前消除不透明，双方可能不再需要猜、问和等待，亲密中彼此到场的过程随之沉寂", "自我表露理论", "自我表露理论常把更多透明视为更亲密；母文关心透明由谁、以何种顺序产生，代理系统直接给答案并不等于两个人互相抵达", "未经工具提示而提出的问题数、双方能保留‘我还不知道’的时长、一次探问是否改变理解，以及停用代理后对话能否自行发生", "透明度提高始终带来更多自发探问和更新，代理深度与亲在沉寂没有稳定关系", "存在暴力、控制、跟踪、严重冲突或创伤触发时，不做不透明练习，先寻求专业安全支持", True),
    Item("conceptual-levitation", 139, "概念悬空", "相框越来越漂亮，为什么画还没有落地？", "让概念撞一次地面：从经验倒逼说法改形", "先买相框再找画", "概念若从与既有理论镜像对抗的方向先长出来，可能在碰到经验以前就获得完整外形，随后只挑能装进去的材料", "闭门造车", "闭门造车批评缺少现实材料；概念悬空即使拥有大量田野和数据也会发生，因为材料只被用来填充一个预先完成的对抗结构", "迫使核心概念改名或改边界的原始案例数、对不上清单是否进入正文、概念在跨场景时需要多少补丁", "先从理论对抗推出的概念与从经验摩擦长出的概念，在解释陌生材料和接受修正上同样有效", "涉及真实群体时，不能为让概念落地而把个案当试验材料；核验必须遵守同意、匿名与最小伤害"),
]


def han_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", text))


def clean(text: str, explanation: bool = False) -> str:
    text = html.unescape(text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(?:p|li|blockquote|div)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if explanation:
        for old, new in FORBIDDEN.items():
            text = text.replace(old, new)
    return text


def source_sections(item: Item, kind: str) -> list[tuple[str, str]]:
    old_html = BASE / item.slug / f"{kind}.html"
    nested_md = BASE / item.slug / ("interpretation" if kind == "explain" else "practice") / "source.md"
    sections: list[tuple[str, str]] = []
    if old_html.exists():
        raw = old_html.read_text(encoding="utf-8")
        article = re.search(r"<article\b[\s\S]*?</article>", raw, flags=re.I)
        if article is None:
            rel = old_html.relative_to(ROOT).as_posix()
            # 旧入口已经改为跳转页时，沿文件历史找到最近一版完整旧稿。
            # 不能只读 HEAD^：站点后续的自动索引提交会改变父提交位置。
            history = subprocess.run(
                ["git", "log", "--format=%H", "--", rel], cwd=ROOT, check=True,
                text=True, stdout=subprocess.PIPE, encoding="utf-8"
            ).stdout.splitlines()
            for commit in history:
                candidate = subprocess.run(
                    ["git", "show", f"{commit}:{rel}"], cwd=ROOT,
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding="utf-8"
                )
                if candidate.returncode:
                    continue
                found = re.search(r"<article\b[\s\S]*?</article>", candidate.stdout, flags=re.I)
                if found:
                    raw, article = candidate.stdout, found
                    break
        assert article, old_html
        body = article.group(0)
        matches = list(re.finditer(r"<h2[^>]*>([\s\S]*?)</h2>", body, flags=re.I))
        for idx, match in enumerate(matches):
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
            segment = body[match.end():end]
            if '<div class="endbox"' in segment:
                segment = segment.split('<div class="endbox"', 1)[0]
            heading = clean(match.group(1), kind == "explain")
            heading = re.sub(r"^\s*\d+\s*", "", heading).strip()
            text = clean(segment, kind == "explain")
            if text:
                sections.append((heading, text))
    else:
        raw = nested_md.read_text(encoding="utf-8")
        for match in re.finditer(r"^##\s+(.+?)\n([\s\S]*?)(?=^##\s+|\Z)", raw, flags=re.M):
            heading = clean(match.group(1), kind == "explain")
            text = clean(match.group(2), kind == "explain")
            if text:
                sections.append((heading, text))
    assert sections, (item.slug, kind)
    return sections


def sentence_units(sections: list[tuple[str, str]], kind: str) -> list[tuple[str, str, bool]]:
    explain_drop = re.compile(r"小动作|小练习|自查|那能怎么办|那还能做什么|那能做什么|怎么做")
    practice_drop = re.compile(r"一句话|收尾")
    units: list[tuple[str, str, bool]] = []

    def fine_parts(part: str) -> list[str]:
        tokens = re.split(r"(?<=[，：、])", part)
        out: list[str] = []
        buf = ""
        for token in tokens:
            if han_count(buf + token) <= 110:
                buf += token
                continue
            if buf:
                out.append(buf); buf = ""
            while han_count(token) > 110:
                seen = 0
                cut = 0
                for cut, char in enumerate(token, 1):
                    if re.match(r"[\u3400-\u9fff]", char):
                        seen += 1
                    if seen == 100:
                        break
                out.append(token[:cut])
                token = token[cut:]
            buf = token
        if buf:
            out.append(buf)
        return [x.strip() for x in out if han_count(x) >= 8]

    for heading, text in sections:
        if (kind == "explain" and explain_drop.search(heading)) or (kind == "practice" and practice_drop.search(heading)):
            continue
        parts = re.split(r"(?<=[。！？；])", text)
        for part in parts:
            part = part.strip(" ·\n")
            if not part or han_count(part) < 8:
                continue
            subparts = fine_parts(part)
            for sub in subparts:
                units.append((heading, sub, True))
    return units


def explain_special(item: Item) -> dict[int, str]:
    return {
        0: f"先把问题放进{item.analogy}这个普通场景。母文真正切开的不是‘要不要使用工具’或‘谁对谁错’，而是：{item.core}。这个类比既容得下它原本有用，也容得下后来发生反转，因此可以陪我们走完整篇。",
        8: f"现在回到{item.analogy}。前面已经看到的各层变化，到了这里要做一个新的分辨：不能因为它仍然有用，就推断它没有改变人的位置；也不能因为出现代价，就抹掉它原先解决过的真实困难。需要观察的是帮助与代替在哪一刻分开。",
        9: f"把{item.analogy}再推到更长的时间里，问题便不只属于一个人。学校、家庭、组织和平台会把某种方便写进流程，新人从第一天起就只见到完成后的答案，看不见答案原来怎样长出。久而久之，个人习惯会变成制度默认，制度默认又反过来证明这种习惯天然正确。",
        10: f"它和{item.neighbour}确实相邻，但不能混成一个说法。{item.divide}。可分离的判据不是两套话听起来像不像，而是把关键条件拿掉以后，两者给出的预测是否仍然相同。",
        13: f"这套判断不主张把{item.analogy}简单扔掉，也不主张只凭个人感受反对专业证据，更不能拿它去要求孩子、伴侣、下属或病人配合某种理想状态。它只要求把母文指出的那条分离线保留下来：看清帮助在什么条件下仍是帮助，在哪个时刻开始替代它原本想保护的能力。\n\n证伪条件必须写在这里：如果持续观察发现，{item.falsifier}，那么母文的核心判断就应当被削弱，不能用‘观察时间还不够’或‘当事人做得不标准’无限保护理论。",
    }


def practice_special(item: Item) -> dict[int, str]:
    boundary = (f"边界必须先于动作。{item.stop}。这套方法不替代诊断、治疗、法律援助、危机干预或法定程序，也不能拿去要求别人证明自己已经改变。"
                if item.risk else
                f"先定适用范围：只在低风险、可逆、能复原的场景里试。{item.stop}。这套方法不能越过专业责任、法定程序和他人的退出权。")
    return {
        0: f"这套方法处理的是一个窄问题：如何把‘{item.core}’变成可以观察和复盘的行动。它不负责证明母文永远正确，不承诺效果，也不把一次练习变成新绩效。最小动作只有一句话：先保留原来的做法，再增加一条能让关键差异被看见的低风险通道。",
        1: f"定位只看可见行为，不问‘我是不是已经理解’。先分辨卡点发生在感知、命名、比较、判断还是决定：有没有原始信号，能不能用自己的话说出，能否同时保留两个版本，谁拥有最后裁决，行动后由谁承担。卡点不同，动作不能通用。",
        2: boundary,
        12: f"读数采用三类：过程读数看动作有没有真实发生，结果读数看能力或关系有没有变化，反作用读数看方法是否制造新负担。本篇最关键的观察量是：{item.observable}。采集只做短周期抽样，用纸面或简短备忘记录，不做每日排名，不把它变成新的打卡项目。代价也要记：练习会降低速度、增加暂时不确定，并可能让旧流程显得不够整齐。",
        13: f"停手线是：动作引起持续焦虑、关系控制、风险上升、工作明显失序，或参与者开始为了交记录而表演。一旦出现，就恢复原流程，保留已经采到的材料，不靠加码挽救方法。安全边界以前文第三节为准；收尾不重新加码，只检查是否已经触线。\n\n理论也要接受撤回：如果足够长的低风险观察显示，{item.falsifier}，这套推论就没有得到支持。此时应收回机制判断，只保留确实有效的局部动作。",
    }


def extra_units(item: Item, kind: str) -> list[tuple[str, str, bool]]:
    if kind == "explain":
        texts = [
            f"个人层面最容易忽略的是顺序。{item.core}。同一件事若只是偶尔发生，通常不会形成稳定变化；只有当它反复发生、又被周围人当作理所当然时，母文所说的机制才逐渐闭合。",
            f"家庭与组织层面的难处在于，大家往往都能从旧安排中得到某种方便。检查{item.analogy}时，应同时记录谁因此省事、谁承担看不见的代价、谁有权说‘这次不一样’。这样才能避免把结构问题改写成个人性格。",
            f"时间是第三个判据。短期效果好，并不能回答长期能力是否仍在；短期不适也不能自动证明旧办法有害。需要把即时收益、延迟代价和撤走后的表现分开观察，才不会用某一个时点替整个过程下结论。",
            f"还可以做一个平行比较：找一件同样包含{item.analogy}结构、却不属于母文原领域的小事。若两边都出现相同的顺序变化，说明母文抓到的是可迁移结构；若只有原场景成立，就应缩小外推范围。",
            f"最后要给反例留位置。凡是使用同样安排却没有出现母文所说代价的人，都不能被一句‘他比较特殊’排除。记录他们保留了什么条件，往往比继续罗列受损案例更能校准判断。",
            f"代价也要单独看。{item.analogy}带来的方便往往立刻可见，损失却延后出现；若只比较当下满意度，结论会天然偏向现有安排。把速度、清晰度与长期判断力分开，才不会让一个指标替另一个指标发言。",
            f"还有一种重要情况：机制可能只在某个强度以上成立。低频、可退出、能被质疑的使用也许只是辅助；高频、默认、无法绕开的使用才形成替代。母文的边界因此应按剂量描述，不能把所有接触者放进同一格。",
            f"最后比较谁拥有改名权。现场出现新东西时，如果只有旧系统有权给它命名，新经验就只能成为例外；若当事人能够保留自己的暂时说法，两种证据才可能真正相遇。这条权利差异常比工具精度更早决定结果。",
        ]
    else:
        texts = [
            f"个人练习先选最近七天里重复出现的一次，不挑最严重事件。写下当时谁先开口、依据是什么、最后由谁决定，再安排一个只改顺序不改目标的小试验。完成后只比较两次现场，不给参与者贴标签。",
            f"家庭或团队使用时，由流程负责人先约定退出权。任何人都可以说暂停，不需要解释原因；记录只写行为和条件，不写‘不成熟’‘依赖’等人格判断。涉及别人的建议不能反过来成为要求对方配合的规章。",
            f"制度层面先做一处抽样，不全域推广。保留旧流程作为对照，明确试验何时结束、谁能宣布失败、失败后怎样恢复。只有观察到稳定变化，才讨论扩大范围；没有变化就停止，而不是增加培训次数。",
            f"复盘时必须放入一个阴性案例：找一位处在相似条件下却没有出现预期变化的人。比较他保留了什么动作、资源或关系，不把差异解释成人格优劣。阴性案例若持续增多，就缩小方法范围。",
            f"成本记录只写新增时间、沟通次数和中断影响，不写空泛感受。一次试验若为了收集证据占用了过多正常工作，就已经改变了被观察对象，应立即降频，并把这项干扰计入结果。",
            f"对照不必追求实验室式完美，只要保证目标相同而顺序不同。例如一次沿用原流程，另一次只延后关键提示；两次都记录现场条件。若同时改了人员、任务和奖励，结果就不能归到这套方法上。",
            f"负责人每轮只回答三个问题：原动作有没有发生，预期差异有没有出现，新负担有没有超过收益。三问中任何一问没有证据，就不扩大范围。用‘大家反映不错’代替观察量，等于让方法躲过检验。",
            f"结束时要把决定写清：继续、缩小、暂停或撤回，只选四者之一，并注明依据。不要用‘持续优化’拖延判断；那会把一次有终点的试验变成永久工程，也会使没有效果被误读成还需投入。",
        ]
    return [("补充观察", text, True) for text in texts]


def normalise_heading(text: str, explanation: bool) -> str:
    text = clean(text, explanation)
    text = re.sub(r"^[一二三四五六七八九十百]+[、.．]\s*", "", text)
    text = re.sub(r"^\d+[、.．：:]?\s*", "", text)
    text = text.replace("结尾：", "").replace("收尾：", "")
    return text[:38] or "再看一层"


def allocate(item: Item, kind: str) -> list[dict[str, str]]:
    originals = source_sections(item, kind)
    specials = explain_special(item) if kind == "explain" else practice_special(item)
    units = sentence_units(originals, kind)

    # 同一判断只保留一次：旧稿偶尔会重复句子，新增的边界段也可能与旧稿撞句。
    # 先建立固定段落的完整句集合，再对素材单元去重；短语不参与，避免误删必要承接。
    def unit_key(text: str) -> str:
        return re.sub(r"[\s，。！？；：、‘’“”（）《》〈〉—…·,.!?;:'\"()\[\]-]", "", text)

    special_keys = {
        unit_key(sentence)
        for special in specials.values()
        for sentence in re.split(r"(?<=[。！？；])", special)
        if han_count(sentence) >= 18
    }
    seen_keys: set[str] = set()
    unique_units: list[tuple[str, str, bool]] = []
    for unit in units:
        key = unit_key(unit[1])
        if han_count(unit[1]) >= 18 and (key in seen_keys or key in special_keys):
            continue
        if han_count(unit[1]) >= 18:
            seen_keys.add(key)
        unique_units.append(unit)
    units = unique_units

    fixed_counts = [han_count(specials.get(i, "")) for i in range(14)]
    needs = [max(0, 350 - fixed_counts[i]) for i in range(14)]
    caps = [500 - fixed_counts[i] for i in range(14)]
    fixed_total = sum(fixed_counts)
    additions = extra_units(item, kind)
    target_source = min(sum(caps), max(sum(needs) + 350, 5200 - fixed_total))
    while sum(han_count(t) for _, t, _ in units) < target_source and additions:
        heading, text, _ = additions.pop(0)
        for part in re.split(r"(?<=[。！？；])", text):
            if han_count(part) >= 8:
                part = part.strip()
                key = unit_key(part)
                if han_count(part) >= 18 and (key in seen_keys or key in special_keys):
                    continue
                if han_count(part) >= 18:
                    seen_keys.add(key)
                units.append((heading, part, True))
    source_total = sum(han_count(t) for _, t, _ in units)
    assert source_total >= sum(needs), (item.slug, kind, "insufficient source", source_total, sum(needs))

    max_source = sum(caps)
    while source_total > max_source and units:
        source_total -= han_count(units.pop()[1])
        while units and not units[-1][2]:
            source_total -= han_count(units.pop()[1])
    assert source_total >= sum(needs), (item.slug, kind, "trimmed too far", source_total, sum(needs))

    prefix = [0]
    for _, text, _ in units:
        prefix.append(prefix[-1] + han_count(text))

    @lru_cache(maxsize=None)
    def solve(slot: int, pos: int):
        if slot == 14:
            return () if pos == len(units) else None
        candidates = []
        ideal = 410 - fixed_counts[slot]
        for end in range(pos + 1, len(units) + 1):
            amount = prefix[end] - prefix[pos]
            if amount > caps[slot]:
                break
            if amount < needs[slot] or not units[end - 1][2]:
                continue
            remaining = prefix[-1] - prefix[end]
            if remaining < sum(needs[slot + 1:]) or remaining > sum(caps[slot + 1:]):
                continue
            candidates.append((abs(amount - ideal), end))
        for _, end in sorted(candidates):
            tail = solve(slot + 1, end)
            if tail is not None:
                return (end,) + tail
        return None

    boundaries = solve(0, 0)
    assert boundaries is not None, (item.slug, kind, "cannot partition", source_total, needs, caps)
    sections: list[dict[str, str]] = []
    start = 0
    for idx, end in enumerate(boundaries):
        group = units[start:end]
        text = "".join(part for _, part, _ in group).strip()
        if text.endswith(("，", "：", "、")):
            text = text[:-1] + "。"
        special = specials.get(idx, "")
        if special:
            text = text + "\n\n" + special
        sections.append({"heading": group[0][0], "text": text})
        start = end
    for idx, section in enumerate(sections):
        assert 350 <= han_count(section["text"]) <= 500, (item.slug, kind, idx, han_count(section["text"]))

    if kind == "explain":
        fixed_headings = {0: "从一个日常场景说起", 8: "回到这个日常场景", 9: "把类比再推一步", 10: f"它和{item.neighbour}相邻，但不是一回事", 13: "它不能被这样误用"}
    else:
        fixed_headings = {0: "这套方法做什么、不做什么", 1: "先定位：问题究竟卡在哪一环", 2: "边界先行：只在安全范围内行动", 12: "读数、采集办法与代价", 13: "什么时候应该停，什么时候说明理论可能不对"}
    used: set[str] = set()
    for idx, section in enumerate(sections):
        heading = fixed_headings.get(idx, normalise_heading(section["heading"], kind == "explain"))
        if heading in used:
            heading = heading + "，再往下一层"
        used.add(heading)
        section["heading"] = heading
    return sections


def source_text(item: Item, kind: str, sections: list[dict[str, str]]) -> str:
    title = item.explain_title if kind == "explain" else item.practice_title
    sub = (f"用{item.analogy}这一条主类比，讲清《{item.title}》切开的核心判断与适用边界"
           if kind == "explain" else
           f"把《{item.title}》落成低风险动作、可观察判据、读数与停手线")
    abstract = (f"这是一篇白话解释文，围绕{item.analogy}贯穿展开，让没有理论背景的读者理解：{item.core}。全文同时划清相邻理论、误用边界与证伪条件。"
                if kind == "explain" else
                f"这是一篇方法实践文，把《{item.title}》转成可上手的定位、动作、场景审计和记录办法。方法不承诺效果，并把安全边界、代价、停手线与证伪条件放进流程。")
    lines = [f"TITLE: {title}", f"SUB: {sub}", f"ABS: {abstract}", ""]
    for section in sections:
        text = section["text"]
        sentences = re.split(r"(?<=[。！？；])", text)
        total = han_count(text)
        acc = 0
        split_at = None
        for idx, sentence in enumerate(sentences):
            acc += han_count(sentence)
            if acc >= total // 2:
                split_at = idx + 1; break
        first = "".join(sentences[:split_at]).strip()
        second = "".join(sentences[split_at:]).strip()
        lines.extend([f"== {section['heading']}", first])
        if second:
            lines.extend(["", second])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


CSS = """
:root{--ink:#25231f;--muted:#716d63;--line:#d8d0bf;--paper:#fbf8f1;--green:#2f7147;--soft:#eaf3e5}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.95 "Noto Serif SC","Songti SC",serif}
a{color:var(--green);text-decoration:none}.wrap{max-width:790px;margin:auto;padding:0 24px}
nav{position:sticky;top:0;z-index:20;background:rgba(28,54,37,.96);color:white}nav .wrap{min-height:52px;display:flex;align-items:center;justify-content:space-between;gap:16px}nav a{color:white;font:14px/1.4 system-ui,"PingFang SC",sans-serif}
header{padding:54px 0 36px;background:linear-gradient(180deg,#eef6e9,#fbf8f1);border-bottom:1px solid var(--line)}
.eyebrow{font:700 12px/1.5 system-ui,"PingFang SC",sans-serif;letter-spacing:.2em;color:var(--green);margin-bottom:15px}
h1{font-size:clamp(28px,5vw,42px);line-height:1.35;margin:0 0 16px}.sub{font-size:17px;color:#4f584f}.meta{margin-top:15px;font:13px/1.6 system-ui,"PingFang SC",sans-serif;color:var(--muted)}
.triad{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:24px}.triad a{padding:12px;border:1px solid #b9cbb8;border-radius:10px;background:white;font:14px/1.5 system-ui,"PingFang SC",sans-serif}.triad a.active{background:var(--green);color:white}.triad small{display:block;opacity:.75;margin-top:3px}
article{padding:34px 24px 60px}.abs{padding:20px 22px;background:var(--soft);border-left:4px solid var(--green);border-radius:0 10px 10px 0;margin-bottom:30px}.toc{border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin-bottom:40px}.toc b{display:block;color:var(--green);letter-spacing:.18em;font:700 12px/1.5 system-ui,"PingFang SC",sans-serif}.toc ol{columns:2;margin:12px 0 0;padding-left:22px}.toc li{break-inside:avoid;margin:4px 0;font-size:14px}
article{counter-reset:section}h2{counter-increment:section;font-size:22px;line-height:1.55;margin:46px 0 18px;padding-top:10px;border-top:1px solid var(--line)}h2:before{content:counter(section,decimal-leading-zero) " ";color:var(--green);font:700 15px/1 system-ui,"PingFang SC",sans-serif;margin-right:8px}p{margin:0 0 18px;text-align:justify}.end{margin-top:48px;padding:22px;background:var(--soft);border-radius:10px}footer{padding:28px 0 44px;border-top:1px solid var(--line);color:var(--muted);font:13px/1.7 system-ui,"PingFang SC",sans-serif}
@media(max-width:680px){body{font-size:16px}.triad{grid-template-columns:1fr}.toc ol{columns:1}h2{font-size:20px}}
"""


def render(item: Item, kind: str, sections: list[dict[str, str]], source: str) -> str:
    title = item.explain_title if kind == "explain" else item.practice_title
    label = "白话解释文" if kind == "explain" else "方法实践文"
    route = "interpretation" if kind == "explain" else "practice"
    sibling_route = "practice" if kind == "explain" else "interpretation"
    sibling_title = item.practice_title if kind == "explain" else item.explain_title
    sub = re.search(r"^SUB:\s*(.+)$", source, flags=re.M).group(1)
    abstract = re.search(r"^ABS:\s*(.+)$", source, flags=re.M).group(1)
    toc = "".join(f'<li><a href="#s{i}">{html.escape(s["heading"])}</a></li>' for i, s in enumerate(sections, 1))
    body = []
    for idx, section in enumerate(sections, 1):
        paragraphs = [p.strip() for p in section["text"].split("\n\n") if p.strip()]
        body.append(f'<h2 id="s{idx}">{html.escape(section["heading"])}</h2>')
        body.extend(f'<p>{html.escape(p)}</p>' for p in paragraphs)
    total = sum(han_count(s["text"]) for s in sections)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · {label} | SDE Universes</title><meta name="description" content="{html.escape(abstract)}">
<link rel="canonical" href="https://sdeuniverses.com/students/zhang-qiong/{item.slug}/{route}/"><style>{CSS}</style></head>
<body><nav><div class="wrap"><a href="/browse/">SDE Universes</a><a href="/students/zhang-qiong/{item.slug}/">回母文《{html.escape(item.title)}》</a></div></nav>
<header><div class="wrap"><div class="eyebrow">并蒂文 · {label} · 母文《{html.escape(item.title)}》</div><h1>{html.escape(title)}</h1><div class="sub">{html.escape(sub)}</div><div class="meta">发表于{TODAY} · 正文 {total} 汉字 · 14节</div>
<div class="triad"><a href="/students/zhang-qiong/{item.slug}/">理论母文<small>张琼的理论判断 · {item.score:g}</small></a><a class="{'active' if kind == 'explain' else ''}" href="/students/zhang-qiong/{item.slug}/interpretation/">白话解释文<small>一条日常主类比</small></a><a class="{'active' if kind == 'practice' else ''}" href="/students/zhang-qiong/{item.slug}/practice/">方法实践文<small>动作、判据与停手线</small></a></div></div></header>
<article class="wrap"><div class="abs"><b>摘要</b>　{html.escape(abstract)}</div><div class="toc"><b>目录</b><ol>{toc}</ol></div>{''.join(body)}
<div class="end">继续阅读：<a href="/students/zhang-qiong/{item.slug}/">理论母文《{html.escape(item.title)}》</a> · <a href="/students/zhang-qiong/{item.slug}/{sibling_route}/">{html.escape(sibling_title)}</a></div></article>
<footer><div class="wrap">© 2026 SDE Universes · <a href="/students/zhang-qiong/works/">张琼 · 全部作品</a></div></footer><script src="/wds-mode.js?v=20260818b" defer></script></body></html>'''


TRIAD_STYLE = """<style>
.bindi-triad-wrap{max-width:900px;margin:0 auto;padding:18px 22px}.bindi-triad{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.bindi-triad a{display:block;padding:13px 15px;border:1px solid rgba(62,125,80,.35);border-radius:10px;background:rgba(255,255,255,.72);color:#2f593a;text-decoration:none;font:14px/1.5 system-ui,"PingFang SC",sans-serif}.bindi-triad a.active{background:#2f7147;color:#fff}.bindi-triad small{display:block;margin-top:4px;opacity:.76}@media(max-width:650px){.bindi-triad{grid-template-columns:1fr}}
</style>"""


def update_mother(item: Item) -> None:
    path = BASE / item.slug / "index.html"
    raw = path.read_text(encoding="utf-8")
    triad = f'''{TRIAD_STYLE}<section class="bindi-triad-wrap"><div class="bindi-triad"><a class="active" href="/students/zhang-qiong/{item.slug}/">理论母文<small>张琼的理论判断 · {item.score:g}</small></a><a href="/students/zhang-qiong/{item.slug}/interpretation/">白话解释文<small>{html.escape(item.explain_title)}</small></a><a href="/students/zhang-qiong/{item.slug}/practice/">方法实践文<small>{html.escape(item.practice_title)}</small></a></div></section>'''
    if '<section class="bindi-triad-wrap">' in raw:
        raw, count = re.subn(r'(?:<style>\s*\.bindi-triad-wrap[\s\S]*?</style>\s*)?<section class="bindi-triad-wrap">[\s\S]*?</section>', triad, raw, count=1)
        assert count == 1, item.slug
    elif '<!-- COMPANION-READS -->' in raw:
        raw, count = re.subn(r'<!-- COMPANION-READS -->[\s\S]*?<!-- /COMPANION-READS -->', triad, raw, count=1)
        assert count == 1, item.slug
    else:
        anchor = re.search(r'</header>', raw)
        assert anchor, item.slug
        raw = raw[:anchor.end()] + triad + raw[anchor.end():]
    path.write_text(raw, encoding="utf-8")


def redirect(path: Path, target: str) -> None:
    if not path.exists():
        return
    path.write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}"><link rel="canonical" href="https://sdeuniverses.com{target}"><title>并蒂文已升级</title></head><body><p>并蒂文已按新标准升级：<a href="{target}">进入新版</a></p></body></html>''', encoding="utf-8")


def update_manifest() -> None:
    data = {
        "updated": "2026-08-13",
        "project": "学员专栏并蒂文计划 v1.0",
        "student": {"name": "张琼", "slug": "zhang-qiong", "eligible_originals": 114},
        "selection": {
            "method": "典型性优先，兼顾创新智商、理论不可替代性与主题覆盖；统一按《并蒂文写作要求与流程 v1.0》重做，不沿用未达标旧稿",
            "score_scale": 160,
            "score_kind": "published-latest-review",
            "selected_originals": 20,
        },
        "derivatives": {
            "interpretations": 20,
            "practice_guides": 20,
            "minimum_han_each": 4800,
            "sections_each": 14,
            "credited_to": None,
            "count_in_student_roster": False,
            "count_in_innovation_ranking": False,
        },
        "items": [
            {
                "rank": rank,
                "iq": item.score,
                "title": item.title,
                "slug": item.slug,
                "original": f"/students/zhang-qiong/{item.slug}/",
                "interpretation": f"/students/zhang-qiong/{item.slug}/interpretation/",
                "practice": f"/students/zhang-qiong/{item.slug}/practice/",
            }
            for rank, item in enumerate(ITEMS, 1)
        ],
    }
    (BASE / "companion-manifest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_works() -> None:
    path = BASE / "works" / "index.html"
    raw = path.read_text(encoding="utf-8")
    rows = []
    for rank, item in enumerate(ITEMS, 1):
        rows.append(f'''<div class="bindi-row"><b>{rank:02d} · {html.escape(item.title)} · {item.score:g}</b><div class="bindi-links"><a href="/students/zhang-qiong/{item.slug}/">理论母文</a><a href="/students/zhang-qiong/{item.slug}/interpretation/">白话解释文</a><a href="/students/zhang-qiong/{item.slug}/practice/">方法实践文</a></div></div>''')
    block = f'''  <div class="work bindi-top"><span class="chip">并 蒂 文 计 划 · 张 琼 · V1.0 已 完 成</span><h2>20篇典型理论：一篇母文，三种读法</h2><p class="hook">从张琼114篇母文中，按理论不可替代性、创新智商与主题覆盖选出20篇，覆盖技术与身体、理论生产、团体、社会学方法、伦理、教育、亲密关系和独异性社会。每篇均重新制作一篇白话解释文与一篇方法实践文；每篇正文不少于4800个汉字、14节，包含固定框、边界、读数、停手线与证伪条件。旧式配套页不计入本批。</p><div class="bindi-list">{''.join(rows)}</div></div>
'''
    raw, count = re.subn(r'  <div class="work bindi-top">[\s\S]*?(?=\n  <div class="work")', block, raw, count=1)
    assert count == 1
    raw = raw.replace("创新智商最高5篇并蒂文", "20篇典型理论并蒂文")
    path.write_text(raw, encoding="utf-8")


def audit(built: dict[tuple[str, str], list[dict[str, str]]]) -> None:
    report = {"student": "张琼", "date": "2026-08-13", "pairs": 20, "pages": []}
    for item in ITEMS:
        for kind in ("explain", "practice"):
            sections = built[(item.slug, kind)]
            counts = [han_count(s["text"]) for s in sections]
            source_path = BASE / item.slug / ("interpretation" if kind == "explain" else "practice") / "source.txt"
            source = source_path.read_text(encoding="utf-8")
            assert len(sections) == 14
            assert sum(counts) >= 4800
            assert all(350 <= n <= 500 for n in counts)
            assert source.startswith("TITLE: ") and "\nSUB: " in source and "\nABS: " in source
            headings = re.findall(r"^==\s+(.+)$", source, flags=re.M)
            assert not any(re.match(r"^[一二三四五六七八九十百]+[、.．]|^\d+[、.．]", h) for h in headings)
            sentence_keys: set[str] = set()
            duplicate_sentences = 0
            for sentence in re.split(r"(?<=[。！？；])", "\n".join(s["text"] for s in sections)):
                key = re.sub(r"[\s，。！？；：、‘’“”（）《》〈〉—…·,.!?;:'\"()\[\]-]", "", sentence)
                if han_count(sentence) < 18:
                    continue
                if key in sentence_keys:
                    duplicate_sentences += 1
                sentence_keys.add(key)
            assert duplicate_sentences == 0, (item.slug, kind, "duplicate sentences", duplicate_sentences)
            if kind == "explain":
                assert all(word not in "\n".join(s["text"] for s in sections) for word in FORBIDDEN)
                for fixed in ("回到这个日常场景", "把类比再推一步", "它不能被这样误用"):
                    assert fixed in headings
            else:
                for fixed in ("先定位：问题究竟卡在哪一环", "读数、采集办法与代价", "什么时候应该停，什么时候说明理论可能不对"):
                    assert fixed in headings
            report["pages"].append({"slug": item.slug, "kind": kind, "han": sum(counts), "sections": 14, "min_section_han": min(counts), "max_section_han": max(counts), "duplicate_sentences": duplicate_sentences})
    (BASE / "companion-audit-v1.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    built: dict[tuple[str, str], list[dict[str, str]]] = {}
    for item in ITEMS:
        for kind, route in (("explain", "interpretation"), ("practice", "practice")):
            sections = allocate(item, kind)
            source = source_text(item, kind, sections)
            out_dir = BASE / item.slug / route
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "source.txt").write_text(source, encoding="utf-8")
            (out_dir / "index.html").write_text(render(item, kind, sections, source), encoding="utf-8")
            built[(item.slug, kind)] = sections
        update_mother(item)
        redirect(BASE / item.slug / "explain.html", f"/students/zhang-qiong/{item.slug}/interpretation/")
        redirect(BASE / item.slug / "practice.html", f"/students/zhang-qiong/{item.slug}/practice/")
    update_manifest()
    update_works()
    audit(built)
    totals = [(p["slug"], p["kind"], p["han"]) for p in json.loads((BASE / "companion-audit-v1.json").read_text(encoding="utf-8"))["pages"]]
    print(f"built {len(ITEMS)} pairs / {len(totals)} pages; Han range {min(x[2] for x in totals)}-{max(x[2] for x in totals)}")


if __name__ == "__main__":
    main()
