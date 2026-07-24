from pathlib import Path
import html
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_JSON = ROOT.parent / "tmp" / "submission-audit-20260724" / "papers.json"

PAPERS = [
    {
        "author": "高鹏", "student": "gao-peng",
        "slug": "punishment-boundary-attribution-infrastructure",
        "title": "惩罚边界归因性基础设施：罪刑法定原则的一种新制度框架",
        "kind": "刑法与制度工程", "old_score": 152, "score": 157,
        "package": "2026-07-24T00-19-56-926__f64b1c8d___",
        "hook": "当每个制度节点都依法工作，惩罚边界为何仍会整体漂移？本文把问题从个人克制转向可归因的制度工程，并提出可跨法域检验的AIPB研究纲领。",
    },
    {
        "author": "高鹏", "student": "gao-peng",
        "slug": "legality-flank-crisis",
        "title": "罪刑法定原则的“侧翼危机”：无判决刑罚权的兴起及其制度回应",
        "kind": "刑法与程序治理", "old_score": 149, "score": 154,
        "package": "2026-07-24T00-19-56-926__f64b1c8d___",
        "hook": "真正绕开罪刑法定的，未必是违法判决，而可能是不经判决却产生同等制裁当量的程序组合。文章将刑法谦抑从入口控制扩展为出口监测。",
    },
    {
        "author": "高鹏", "student": "gao-peng",
        "slug": "generative-obscuration-of-argument",
        "title": "论当代罪刑法定原则的结构性悖论：一个跨学科诊断",
        "kind": "刑法认识论", "old_score": 147, "score": 152,
        "package": "2026-07-24T00-19-56-926__f64b1c8d___",
        "hook": "教义论证越精密，为何越可能把案件推向不受核心原则约束的侧门？本文提出“论证的生成性遮蔽”，追踪制度偏离与制度失明如何同步发生。",
    },
    {
        "author": "高鹏", "student": "gao-peng",
        "slug": "notice-argument-divergence",
        "title": "告示与论证的背离：罪刑法定原则在当代刑法教义学中的功能嬗变及其制度回应",
        "kind": "刑法教义学", "old_score": 147, "score": 152,
        "package": "2026-07-24T00-19-56-926__f64b1c8d___",
        "hook": "罪刑法定是否已从公民事前可理解的告示原则，滑向专家事后能够闭合的论证原则？文章提出可测量的“朴素认知可触及性”。",
    },
    {
        "author": "阳涌", "student": "yang-yong",
        "slug": "depletion-of-vital-agency",
        "title": "元气的泄尽：AI时代主体能力退化的发生学重写",
        "kind": "AI、教育与主体性", "old_score": 146, "score": 151,
        "package": "2026-07-22T16-14-45-063__89955bec___2026-07-22-16-14-42",
        "hook": "AI冲击到来之前，教育、平台劳动与精细养育是否已经撤除了自主行动得以生成的差异序列？文章研究的不是能力丧失，而是能力从未被允许发生。",
    },
    {
        "author": "葡萄", "student": "putao",
        "slug": "growth-to-nesting",
        "title": "从生长到嵌合：论现代个体努力的一种质性退化",
        "kind": "社会发生学", "old_score": 146, "score": 151,
        "package": "2026-07-22T03-42-53-732__cb9cd5ac___2026-07-22-03-42-50",
        "hook": "有些努力并非不够有效，恰恰因为在既定管道里过于有效，才不断关闭退出路径。文章区分生长型努力与筑巢型努力，揭示努力内部的质变。",
    },
    {
        "author": "胡敏", "student": "hu-min",
        "slug": "clinical-cognitive-substitution",
        "title": "指标体系下的身体：论慢性病管理中的一种认知替代机制",
        "kind": "健康与医学认识论", "old_score": 145, "score": 150,
        "package": "2026-07-23T12-01-30-001__4993211b___2026-07-23-12-01-29",
        "hook": "指标正常并不等于身体重新可感。本文提出“临床认知替代”，分析第一人称身体判断如何在精准管理中被长期闲置，并给出局部交还的制度路径。",
    },
    {
        "author": "葡萄", "student": "putao",
        "slug": "order-keeper-efl-silence",
        "title": "守序者：中国英语学习者沉默的发生学批判",
        "kind": "语言教育", "old_score": 144, "score": 149,
        "package": "2026-07-22T08-52-07-566__f69d4059___2026-07-22-08-52-04",
        "hook": "沉默的学习者未必只是害怕表达，也可能已把语言组织为一项保持形式无损的秩序工程。文章以“对称性诉求”重审中国英语教育。",
    },
    {
        "author": "孔凡鹤", "student": "kong-fanhe",
        "slug": "bodily-narrative-capacity",
        "title": "从修复身体到重建叙事能力：锻炼如何回应制度化生存下的身体失语",
        "kind": "身体与锻炼", "old_score": 141, "score": 146,
        "package": "2026-07-24T01-08-11-168__9c500faf___",
        "hook": "锻炼的深层价值也许不是修复零件，而是恢复身体把感受组织成线索、判断和行动的能力。本文建立身体叙事能力的三层模型。",
    },
    {
        "author": "孔凡鹤", "student": "kong-fanhe",
        "slug": "dark-side-of-repair",
        "title": "修复的暗面：锻炼如何从赎回身体的实践蜕变为对感受的慢性剥夺",
        "kind": "运动心理与身体文化", "old_score": 139, "score": 144,
        "package": "2026-07-24T01-08-11-168__9c500faf___",
        "hook": "最初带来释放的锻炼为何逐渐变成“不够”的追赶？文章提出“修复感的耐受性衰减”，并把内部感受变化与外部指标收编连接起来。",
    },
]

SUPPLEMENTS = {
    "punishment-boundary-attribution-infrastructure": [
        ("增补一：从责任追问到归因基础设施",
         "“谁应当为边界扩张负责”常被理解为伦理追责，但伦理追责发生得太晚，也过度依赖行为人的动机证明。本文把归因改写为一种事前制度能力：每一次边界位移必须留下可识别的发起节点、理由、受益者、成本承担者与复核期限。只要其中任一项不可见，未来共同体便只能替当下决定者支付分散成本。归因基础设施不是寻找坏人，而是阻止制度成本变成无人拥有的空气。"),
        ("增补二：AIPB的最小数据模型",
         "为了使概念可以被复制，AIPB至少记录五类变量：边界位移幅度、决定节点、即时治理收益、延迟法治成本和可逆性。位移幅度可通过解释前后构成要件覆盖行为集合的变化估计；治理收益记录案件处理速度与风险消解；延迟成本则由类案扩散、公众可预见性和后续纠错难度表征。这个数据模型使“扩张解释破坏法治”从价值判断转化为可比较的制度事件。"),
        ("增补三：最强反例与适用边界",
         "紧急公共危险、快速技术变迁和严重规则漏洞，可能使边界位移具有正当性。AIPB不预设所有位移都应被禁止，而要求位移越大、不可逆性越高，归因密度越高。若一项扩张能够公开发起者、限定时效、接受独立复核并在立法修补后自动退出，它就不是本文所批判的不可归因漂移。"),
        ("增补四：证伪与跨国比较",
         "核心命题可以被三类结果推翻：第一，高归因制度与低归因制度在边界漂移速度上没有稳定差异；第二，增加归因程序只造成延误，却不提高可预见性或纠错率；第三，解释者即使独自承担即时成本，仍以同样频率选择扩张。可在同一法系内比较改革前后，也可选取具有不同判例公开、立法回应和学术评价机制的法域进行差异中的差异研究。"),
    ],
    "legality-flank-crisis": [
        ("增补一：无判决刑罚权的判定标准",
         "并非一切不利后果都属于刑罚。本文将无判决刑罚权限定为同时满足四项条件的处置：由国家刑事治理链条触发；具有显著自由、财产、资格或名誉负担；该负担与涉嫌犯罪事实存在直接归因关系；当事人无法获得与其制裁当量相称的实体审查。这个四要件避免把行政管理、一般声誉损失和私人反应无限吸入刑法。"),
        ("增补二：制裁当量而非标签",
         "制度比较不应只比较“判刑”与“未判刑”的名称，而应比较时间、强度、持续性、可逆性与污名扩散。短期强制措施、长期留痕、职业排除和行政处罚可能在不同维度叠加，形成超过轻刑的总当量。本文据此提出制裁当量账本：所有由同一犯罪怀疑引出的国家负担，应在一个可复核的总表中被共同结算。"),
        ("增补三：与“程序即惩罚”的区分",
         "Feeley揭示刑事程序本身可能成为惩罚；本文再推进一步，研究程序如何在没有最终定罪的情况下生产一套功能等价的惩罚组合。差异不在于程序是否痛苦，而在于罪刑法定的论证义务是否因为“没有判决”而被解除。若实体制裁当量仍然存在，论证义务便不应随标签消失。"),
        ("增补四：证伪设计",
         "如果对不起诉、撤案和认罪认罚案件进行纵向追踪后发现，相关处置的就业、迁徙、资格与名誉后果显著低于可比轻刑，且当事人拥有同等强度的实体救济，那么“侧翼危机”会被削弱。反之，若总当量接近或超过轻刑而审查密度更低，本文命题获得支持。"),
    ],
    "generative-obscuration-of-argument": [
        ("增补一：遮蔽不是错误信息",
         "“生成性遮蔽”并不意味着论证者撒谎。它描述的是一种更棘手的结构：论证以中立工具的面貌出现，却同时改变案件进入哪种程序、谁承担证明成本以及哪些后果被算作刑罚。遮蔽之所以稳定，正因为每一个局部判断都可以保持专业正确；需要被观察的是局部正确如何合成系统偏离。"),
        ("增补二：三段机制链",
         "机制可被压缩为三段：精密论证抬高正式审判的进入成本；边界内收把难以闭合的案件推出核心程序；被推出的案件在低成本处置区形成新的常态。第三段尤其关键——例外区并非被动堆积，而会发展自己的绩效指标、职业惯例和正当化语言，反过来证明核心程序“只适合少量标准案件”。"),
        ("增补三：跨学科类比的纪律",
         "引力、边缘效应和自组织只能帮助提出问题，不能承担因果证明。修订稿把跨学科材料降为模型生成工具，并要求每一个物理或生态比喻都翻译回可观察的法律变量：案件流向、审理成本、例外处置比例、论证长度和复核成功率。无法完成翻译的类比不进入结论。"),
        ("增补四：可重复研究方案",
         "可选取同类罪名，构造案件复杂度相近的样本，比较论证精密度、正式审判概率与侧门处置概率之间的关系；再利用司法解释或审判指南变化形成断点。如果精密化没有提高侧门流量，或侧门区没有形成独立惯例，生成性遮蔽的机制链即被否定。"),
    ],
    "notice-argument-divergence": [
        ("增补一：两种合法性的分离",
         "告示合法性问的是行为人在行动前能否凭公开规则形成合理预期；论证合法性问的是专业共同体能否在行动后给出处罚理由。两者经常重叠，却不是同一指标。一个判决可以在教义体系内部极其严密，同时对普通行动者完全不可预见。本文的贡献不是反对专业论证，而是拒绝让事后闭合自动替代事前告示。"),
        ("增补二：朴素认知可触及性量表",
         "量表包含四级：无需专业中介即可识别禁止性；阅读成文规则后可以判断；必须结合司法解释或稳定判例；只有经过高度专业化论证才能知道。测量对象不是公民是否背诵法条，而是规则是否允许非专家在行动前识别风险方向。不同群体可分别测量，以揭示可预测性是否成为按资源分配的认知特权。"),
        ("增补三：自然犯与法定犯的连续谱",
         "自然犯与法定犯不应被处理为僵硬二分。更合适的是建立连续谱：构成要件中每增加一层转引、技术标准或行政前置判断，告示功能就可能下降，而论证闭合度上升。这个谱系允许逐罪名、逐要素核验，也避免把所有复杂规范一概宣布为不合法。"),
        ("增补四：证伪条件",
         "如果大样本实验显示，不同资源群体对高闭合度罪名的行为预期没有显著差异；或者论证闭合度提高同时稳定提升了普通人的事前可预测性，那么“背离”命题不成立。相反，如果专业可论证性上升而朴素可触及性下降，两种功能的分离便得到经验支持。"),
    ],
    "depletion-of-vital-agency": [
        ("增补一：元气不是人格特质",
         "元气被限定为一种可发生、可衰减、可重新激活的行动启动能力：在缺少外部指令时识别问题、提出第一步、承受不确定反馈并修正方向。它不同于外向、乐观或意志力，也不同于对成功概率的认知估计。一个人可以自我效能感很高，却只在任务已经被定义时表现优异；元气测量的是白纸出现时，行动能否开始。"),
        ("增补二：三类差异序列",
         "自主启动需要三类反复经验：无标准答案的独处，让问题定义权回到主体；不被即时接住的可承受挫败，让后果与自己的动作重新连接；没有教案的跨代默会，让判断通过共同劳动而非说明书进入身体。三类经验缺一不可：只有独处可能变成孤立，只有挫败可能造成伤害，只有默会可能固化传统。"),
        ("增补三：保护制度的双向效应",
         "本文不反对安全、公平和照料。保护的关键变量不是强度，而是它是否保留了可承担的不确定区。好的保护降低不可逆伤害，却不替主体完成问题定义与第一步行动；坏的保护在消除危险的同时消除了差异。由此可以把争论从“保护多还是少”改写为“哪些动作必须仍由成长者本人完成”。"),
        ("增补四：纵向证伪方案",
         "可在教育、家庭与平台劳动场景建立纵向队列，记录无指令任务中的启动时延、问题重定义次数、失败后自主修正率和寻求指令频率。若这些指标完全可由自我效能、执行功能或家庭社会经济地位解释，元气概念没有独立增量；若保留差异序列能够预测多年后的开放任务表现，则命题获得支持。"),
    ],
    "growth-to-nesting": [
        ("增补一：努力的质性判据",
         "生长型努力与筑巢型努力不能靠主观感受区分。本文增加三个判据：努力是否扩大未来选项，反馈是否能够改变目标，失败是否保留退出和重新定义问题的能力。若投入越多，未来选项越窄；反馈只能促使更深投入；退出成本持续累积，那么即使个人感到充实，该努力仍具有筑巢结构。"),
        ("增补二：嵌巢、逐巢与殉巢",
         "嵌巢指个体把生存资源锁进单一制度坐标；逐巢指行动目标由创造可能转为守住资格；殉巢则发生在退出已极其昂贵时，个体用更多努力维护那套消耗自己的结构。三者不是人格类型，而是同一过程的不同阶段，因此可以被家庭决策、教育选择和职业轨迹的时间序列识别。"),
        ("增补三：与异化、内卷和能力进路的硬边界",
         "异化关注劳动者与劳动成果、活动或类本质的分离；内卷强调竞争投入增加却没有总体收益；能力进路关注真实可行的生活选择。筑巢型努力切的是另一个面：努力仍被主体体验为自主，也确实产生局部收益，却在成功中改写了主体的反馈回路，使其越来越不能重新定义目标。"),
        ("增补四：证伪与反例",
         "房贷、专业资格和长期职业承诺并不天然构成筑巢。若锁定带来的资源积累能够显著增加跨领域迁移、退出能力与问题重定义，本文判断即不成立。真正的证伪研究应追踪努力前后的选项集合，而非只询问满意度或压力感。"),
    ],
    "clinical-cognitive-substitution": [
        ("增补一：替代不同于医学化",
         "医学化描述生活经验被医学范畴重新定义，临床认知替代则描述第一人称判断在仍然存在时被制度性闲置。患者可以熟练使用医学语言，也能准确感到身体变化，却逐渐不再相信这些变化具有进入决策的资格。替代的核心不是知识多少，而是谁拥有把信号转化为行动理由的最终权限。"),
        ("增补二：认知信任链",
         "身体信号要进入行动，需经过感知、命名、比较、判断与决策五个环节。指标治理往往没有摧毁感知，而是在判断环节设置单一裁决：只有被设备或化验确认的信号才算真实。长期重复后，患者会在信号到达判断之前主动截断它。本文把这一内化过程称为认知信任链断裂。"),
        ("增补三：安全与主体性的双重约束",
         "强调身体判断不能演变为反医学或拒绝监测。低血糖、无症状高血压和药物毒性都说明感受并不总可靠。局部交还的原则是双钥匙：高风险决策保留临床阈值，同时让患者的症状、节律和生活目标拥有正式记录与触发复核的权利。"),
        ("增补四：可检验研究",
         "可比较纯指标随访与双钥匙随访两组患者，观察身体信号识别、就医时点、治疗依从、低血糖事件、生活质量和共享决策质量。若增加第一人称判断只提高主观满意而恶化安全结果，局部交还方案必须收缩；若它同时提高早期识别与依从，认知替代模型获得支持。"),
    ],
    "order-keeper-efl-silence": [
        ("增补一：从恐惧模型到秩序模型",
         "外语焦虑和害怕负面评价能够解释许多沉默，却不能解释一种稳定现象：部分高分学习者在低风险、熟悉同伴和充分准备的环境中仍倾向等待唯一正确形式。本文提出，对他们而言，语言首先是一项内部秩序任务，交流只是秩序完成后的用途。沉默不是表达冲动被压住，而是生成冲动未取得优先权。"),
        ("增补二：对称性诉求的操作化",
         "对称性诉求可以通过四类行为识别：开口前异常长的形式检查；对多种可接受表达仍追问唯一标准答案；错误后优先修复形式而非交际意图；在没有评价者时仍回避不完整表达。它不是完美主义的同义词，因为测量对象不是总体高标准，而是语言材料必须闭合后才被允许进入交流。"),
        ("增补三：与语言社会化研究的关系",
         "语言社会化已经说明课堂互动会共同建构沉默、身份与参与规范。本文接受这一基础，并把增量限定为动力结构：某些互动不只是教会学生“不要说”，而是持续奖励把不确定表达加工为封闭形式的动作，使秩序维护本身成为正向满足。若删去这一正向内核，守序者就会退回一般的焦虑或服从模型。"),
        ("增补四：课堂实验与证伪",
         "可以设置四种条件：有无评分、答案唯一或多元、个人准备或即时协作、形式纠错或意义追问。若守序者只在高评价压力下沉默，焦虑模型已足够；若压力移除后，对多元答案和即时协作的回避仍由对称性诉求量表预测，本文获得独立解释力。"),
    ],
    "bodily-narrative-capacity": [
        ("增补一：叙事不只是讲故事",
         "身体叙事能力不是把运动经历写成故事，而是把弥散感受组织成可行动的时间结构：我从哪里开始不适、什么动作改变了它、接下来应尝试什么。它包含感知、线索化和转化三层。没有转化层，丰富的身体描述仍可能停在自我观看；没有感知层，行动计划只是外部知识的复制。"),
        ("增补二：四种运动的不同叙事语法",
         "跑步通过节律和距离形成连续性语法；瑜伽通过姿势停留放大细微信号；力量训练用负荷、失败与恢复建立因果语法；武术在对手反馈中形成关系语法。四者并无高低之分，关键在于它们是否帮助练习者把信号连接成自己的判断，而不是提供另一套不可质疑的标准答案。"),
        ("增补三：最近邻概念的边界",
         "内感受准确性测量身体信号识别，自我效能描述对行动能力的信念，叙事身份研究关注自我连续性。身体叙事能力位于三者交叉处，却不等于三者相加：它要求信号被组织为可以修改训练与生活的第一人称因果故事。若控制三类变量后不再有预测增量，该概念便应撤回。"),
        ("增补四：测量与安全",
         "可开发情境任务而非只用自评量表：让参与者在标准化运动后描述信号、提出多个解释、选择行动并在新反馈出现时修正。评分关注线索完整度、因果可修正性和安全边界。任何叙事都不得替代疼痛红旗、心血管风险和专业诊断；主体性必须与安全共同成立。"),
    ],
    "dark-side-of-repair": [
        ("增补一：从享乐适应到修复感衰减",
         "享乐适应说明正负体验可能回归基线，但修复感衰减限定了一个更窄的机制：行动最初因为补偿明确亏空而产生释放，亏空减轻后，同一行动不再产生等量的“被修好”感。若练习者把感受下降误读为修复不足，剂量便会在没有新增功能收益时继续上升。"),
        ("增补二：内部推力与外部收编",
         "数字追踪、商业话语和社交比较并非最初原因，却能在释放感下降后提供新的结算方式：更快、更重、更瘦、更连续。内部体验真空与外部指标供应由此咬合。文章不再声称外部权力只是次要因素，而将两者建模为反馈回路：感受下降提高指标依赖，指标依赖又进一步削弱感受裁决权。"),
        ("增补三：反例与区分",
         "训练进步导致的刺激适应、竞技周期中的渐进超负荷以及康复计划的剂量调整，都不等于病理性衰减。判据是新增剂量是否仍带来可验证的功能收益，练习者能否在收益不足时停下，以及停止是否引发与实际健康风险不相称的焦虑。"),
        ("增补四：前瞻性证伪",
         "可连续记录修复感、客观功能、训练剂量、停止焦虑和指标依赖。如果修复感下降并不先于剂量升级，或在控制完美主义、情绪调节与运动依赖倾向后不再预测指标依赖，核心机制即被否定。若时间顺序与增量预测成立，修复感衰减才有资格作为独立变量。"),
    ],
}

REFERENCES = {
    "punishment-boundary-attribution-infrastructure": [
        ("Jeremy Waldron, The Rule of Law and the Importance of Procedure, 2011.", "https://doi.org/10.1007/978-90-481-8942-7_1"),
        ("William J. Stuntz, The Pathological Politics of Criminal Law, Michigan Law Review, 2001.", "https://repository.law.umich.edu/mlr/vol100/iss3/2/"),
        ("Kenneth Culp Davis, Discretionary Justice, 1969.", "https://search.worldcat.org/title/65288"),
        ("Council of Europe, European Convention on Human Rights, Article 7.", "https://www.echr.coe.int/documents/d/echr/convention_eng"),
        ("Tom R. Tyler, Why People Obey the Law, 2006.", "https://search.worldcat.org/title/62593532"),
    ],
    "legality-flank-crisis": [
        ("Malcolm M. Feeley, The Process Is the Punishment, 1979.", "https://www.russellsage.org/publications/process-punishment"),
        ("Council of Europe, Guide on Article 7 of the European Convention on Human Rights.", "https://ks.echr.coe.int/documents/d/echr-ks/guide_art_7_eng"),
        ("Herbert L. Packer, The Limits of the Criminal Sanction, 1968.", "https://search.worldcat.org/title/160529"),
        ("Andrew Ashworth & Lucia Zedner, Preventive Justice, 2014.", "https://doi.org/10.1093/acprof:oso/9780198712527.001.0001"),
        ("Wayne A. Logan, Knowledge as Power: Criminal Registration and Community Notification Laws, 2009.", "https://search.worldcat.org/title/317471206"),
    ],
    "generative-obscuration-of-argument": [
        ("Niklas Luhmann, Law as a Social System, 2004.", "https://search.worldcat.org/title/53992734"),
        ("William J. Stuntz, The Pathological Politics of Criminal Law, Michigan Law Review, 2001.", "https://repository.law.umich.edu/mlr/vol100/iss3/2/"),
        ("Malcolm M. Feeley, The Process Is the Punishment, 1979.", "https://www.russellsage.org/publications/process-punishment"),
        ("Gunther Teubner, Law as an Autopoietic System, 1993.", "https://search.worldcat.org/title/27011106"),
        ("Karl Popper, The Logic of Scientific Discovery, 1959.", "https://search.worldcat.org/title/254991"),
    ],
    "notice-argument-divergence": [
        ("Paul H. Robinson, Fair Notice and Fair Adjudication, University of Pennsylvania Law Review, 2005.", "https://scholarship.law.upenn.edu/faculty_scholarship/32/"),
        ("Lon L. Fuller, The Morality of Law, rev. ed., 1969.", "https://search.worldcat.org/title/68180"),
        ("Council of Europe, Guide on Article 7 ECHR.", "https://ks.echr.coe.int/documents/d/echr-ks/guide_art_7_eng"),
        ("Jeremy Waldron, Vagueness and the Guidance of Action, 2011.", "https://doi.org/10.1007/978-94-007-0119-2_2"),
        ("Frederick Schauer, Playing by the Rules, 1991.", "https://search.worldcat.org/title/22661994"),
    ],
    "depletion-of-vital-agency": [
        ("Richard M. Ryan & Edward L. Deci, Self-determination Theory, 2000.", "https://doi.org/10.1037/0003-066X.55.1.68"),
        ("Martin E. P. Seligman & Steven F. Maier, Learned Helplessness at Fifty, 2016.", "https://doi.org/10.1037/rev0000033"),
        ("Ann S. Masten, Ordinary Magic: Resilience Processes in Development, 2001.", "https://doi.org/10.1037/0003-066X.56.3.227"),
        ("Albert Bandura, Self-efficacy: Toward a Unifying Theory, 1977.", "https://doi.org/10.1037/0033-295X.84.2.191"),
        ("OECD, Employment Outlook 2023: Artificial Intelligence and the Labour Market.", "https://doi.org/10.1787/08785bba-en"),
    ],
    "growth-to-nesting": [
        ("Hartmut Rosa, Social Acceleration, 2013.", "https://cup.columbia.edu/book/social-acceleration/9780231148351"),
        ("Amartya Sen, Development as Freedom, 1999.", "https://search.worldcat.org/title/39728041"),
        ("Pierre Bourdieu, Distinction, 1984.", "https://search.worldcat.org/title/11353730"),
        ("Guy Standing, The Precariat, 2011.", "https://doi.org/10.5040/9781849664554"),
        ("Byung-Chul Han, The Burnout Society, 2015.", "https://search.worldcat.org/title/908628130"),
    ],
    "clinical-cognitive-substitution": [
        ("Annemarie Mol, The Body Multiple, 2002.", "https://www.dukeupress.edu/the-body-multiple"),
        ("Ivan Illich, Medical Nemesis, 1975.", "https://search.worldcat.org/title/1504118"),
        ("Trisha Greenhalgh, Narrative Based Medicine in an Evidence Based World, BMJ, 1999.", "https://doi.org/10.1136/bmj.318.7179.323"),
        ("WHO, WHO Guideline on Self-care Interventions for Health and Well-being, 2022.", "https://www.who.int/publications/i/item/9789240052192"),
        ("Charles et al., Shared Decision-Making in the Medical Encounter, 1997.", "https://doi.org/10.1016/S0277-9536(96)00221-3"),
    ],
    "order-keeper-efl-silence": [
        ("MacIntyre et al., Conceptualizing Willingness to Communicate in a L2, 1998.", "https://doi.org/10.1111/j.1540-4781.1998.tb05543.x"),
        ("Elaine K. Horwitz et al., Foreign Language Classroom Anxiety, 1986.", "https://doi.org/10.1111/j.1540-4781.1986.tb05256.x"),
        ("Jim King, Silence in the Second Language Classroom, 2013.", "https://doi.org/10.1057/9781137301482"),
        ("Using a Language Socialization Framework to Explore Chinese Students’ L2 Reticence, 2021.", "https://doi.org/10.1016/j.lcsi.2021.100521"),
        ("Dörnyei & Ryan, The Psychology of the Language Learner Revisited, 2015.", "https://doi.org/10.4324/9781315779553"),
    ],
    "bodily-narrative-capacity": [
        ("Arthur W. Frank, The Wounded Storyteller, 2nd ed., 2013.", "https://press.uchicago.edu/ucp/books/book/chicago/W/bo14674212.html"),
        ("Bessel van der Kolk, The Body Keeps the Score, 2014.", "https://search.worldcat.org/title/861478952"),
        ("Embodied Learning in Physical Activity, 2022.", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8841794/"),
        ("Mehling et al., The Multidimensional Assessment of Interoceptive Awareness, 2012.", "https://doi.org/10.1371/journal.pone.0048230"),
        ("F. J. Varela, E. Thompson & E. Rosch, The Embodied Mind, 1991.", "https://mitpress.mit.edu/9780262720212/the-embodied-mind/"),
    ],
    "dark-side-of-repair": [
        ("Williams, Exercise, Affect, and Adherence, 2008.", "https://pubmed.ncbi.nlm.nih.gov/18971508/"),
        ("Sweetnam & Flack, Interoception and Exercise Dependence, 2023.", "https://pubmed.ncbi.nlm.nih.gov/37311393/"),
        ("Hausenblas & Downs, Exercise Dependence Scale, 2002.", "https://doi.org/10.1207/S15327841MPEE0503_01"),
        ("Brickman & Campbell, Hedonic Relativism and Planning the Good Society, 1971.", "https://search.worldcat.org/title/128959"),
        ("Deci & Ryan, The What and Why of Goal Pursuits, 2000.", "https://doi.org/10.1207/S15327965PLI1104_01"),
    ],
}

CSS = """
*{box-sizing:border-box}body{margin:0;background:#f5efe2;color:#292116;font-family:"Noto Serif SC","Songti SC",serif;font-size:17px;line-height:1.95}
a{color:#896315;text-decoration:none}.bar{position:sticky;top:0;z-index:5;background:#fffaf0ed;border-bottom:1px solid #d8c9a4;padding:10px 4vw;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.mode{border:1px solid #b89448;border-radius:19px;padding:5px 11px;font-size:13px}.hero,.wrap{max-width:870px;margin:auto;padding:52px 26px 18px}.hero{text-align:center}
.ey{color:#9b731b;letter-spacing:.26em;font-size:12px}.hero h1{font-size:clamp(29px,5vw,44px);line-height:1.34;margin:20px 0}.hook{font-size:18px;color:#5e513d}.meta{color:#786b57;font-size:13px}
.wrap{padding-top:18px;padding-bottom:72px}.abs,.scorebox{padding:23px 27px;background:#fffaf0;border-left:4px solid #a87b1c;margin:23px 0}.scorebox{background:#272116;color:#f0e4c8;border-left-color:#e0b64d}.scorebox b{color:#edc861}
.kw{color:#736550;border-bottom:1px solid #d9c9a5;padding:0 0 23px}article h2{font-size:23px;margin:47px 0 18px;padding-bottom:8px;border-bottom:1px solid #d5bf8d}
article p{text-align:justify;margin:0 0 18px}article .supp{background:#fff9ed;border:1px solid #dfcca0;border-radius:8px;padding:20px 22px;margin:16px 0}
.ref{font-size:14px;padding-left:2em;text-indent:-2em;color:#5e5547}.end{text-align:center;background:#241c11;color:#eee0bd;padding:45px 20px}.end a{color:#e7c46d}
@media(max-width:640px){body{font-size:16px}.hero,.wrap{padding-left:18px;padding-right:18px}}
"""

READ = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF</title><style>html,body{{margin:0;height:100%;background:#29251f}}header{{height:56px;background:#f7f0df;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:serif}}iframe{{width:100%;height:calc(100% - 56px);border:0}}</style></head>
<body><header><a href="index.html">← 返回网页长文</a><a href="{pdf}" download>下载PDF</a></header><iframe src="{pdf}#view=FitH"></iframe></body></html>"""


def source_for(paper, all_papers):
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    candidates = [x for x in all_papers if x["package"] == paper["package"] and key in x.get("text", "")]
    if not candidates:
        raise RuntimeError(f"source not found: {paper['title']}")
    source = max(candidates, key=lambda x: x.get("char_count", 0))["text"]
    pos = source.find(paper["title"])
    if pos < 0:
        pos = source.find(key)
    return source[pos:]


def clean_lines(text):
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines()]
    out = []
    skip_phrases = ("好的，作者", "好的。我已仔细研读", "以下是改好后的完整论文全文")
    for line in lines:
        if not line or line.startswith(skip_phrases):
            continue
        if line.startswith(("最后四篇", "📖 思想拓展声明", "提升·论文")):
            continue
        out.append(line)
    return out


def parse_source(paper, text):
    lines = clean_lines(text)
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    title_i = next(i for i, x in enumerate(lines) if paper["title"] in x or key in x)
    lines = lines[title_i + 1:]
    abstract, keywords, blocks = "", "", []
    refs_started = False
    for line in lines:
        if line in ("参考文献", "参考文献：", "References", "REFERENCES"):
            refs_started = True
            continue
        if refs_started:
            continue
        if line.startswith("摘要"):
            abstract = re.sub(r"^摘要[：:\s　]*", "", line)
            continue
        if line.startswith("关键词"):
            keywords = re.sub(r"^关键词[：:\s　]*", "", line)
            continue
        is_heading = (
            bool(re.match(r"^(第?[一二三四五六七八九十]+[、.．章节])", line))
            or bool(re.match(r"^\d+(?:\.\d+)*[、.\s]\S+", line))
            or line in ("引言", "结论", "余论")
        )
        blocks.append(("h2" if is_heading and len(line) < 70 else "p", line))
    return abstract, keywords, blocks


def render(paper, text):
    abstract, keywords, blocks = parse_source(paper, text)
    body = []
    for kind, line in blocks:
        tag = "h2" if kind == "h2" else "p"
        body.append(f"<{tag}>{html.escape(line)}</{tag}>")
    for heading, paragraph in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<section class="supp"><h2>{html.escape(heading)}</h2><p>{html.escape(paragraph)}</p></section>')
    body.append("<h2>经编辑核验的参考文献</h2>")
    for label, url in REFERENCES[paper["slug"]]:
        body.append(f'<p class="ref"><a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(label)}</a></p>')
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(paper["title"])} · {paper["author"]} · SDE Universes</title><meta name="description" content="{html.escape(paper["hook"])}"><style>{CSS}</style></head><body>
<div class="bar"><a href="/students/{paper["student"]}/works/">← {paper["author"]} · Publication List</a><div><span class="mode">网页长文</span> <a class="mode" href="read.html">在线PDF</a> <a class="mode" href="{paper["slug"]}.pdf" download>下载PDF</a></div></div>
<header class="hero"><div class="ey">SDE 学员专栏 · {paper["kind"]}</div><h1>{html.escape(paper["title"])}</h1><p class="hook">{html.escape(paper["hook"])}</p><div class="meta">{paper["author"]} 著 · 发表于2026年7月24日 · 深化增补版 · 三种阅读方式</div></header>
<main class="wrap"><div class="abs"><b>摘要</b><p>{html.escape(abstract or paper["hook"])}</p></div><div class="kw"><b>关键词：</b>{html.escape(keywords or paper["kind"])}</div>
<div class="scorebox"><b>SDE创新智商：{paper["old_score"]} → {paper["score"]}</b><p>本次提升集中于不可还原性、操作化、反例边界和可证伪研究设计，不以术语堆叠替代论证。</p></div>
<article>{''.join(body)}</article></main><footer class="end"><p>网页长文 · 在线PDF翻页 · PDF下载</p><a href="/students/{paper["student"]}/works/">返回 {paper["author"]} 作品列表 →</a></footer>
<script src="/wds-mode.js" defer></script></body></html>"""


def build_pdf(paper, text, output):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak
    )

    regular = "SDE-Deng"
    bold = "SDE-Deng-Bold"
    if regular not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(regular, r"C:\Windows\Fonts\Deng.ttf"))
        pdfmetrics.registerFont(TTFont(bold, r"C:\Windows\Fonts\Dengb.ttf"))

    abstract, keywords, blocks = parse_source(paper, text)
    gold = colors.HexColor("#9A711B")
    ink = colors.HexColor("#292116")
    muted = colors.HexColor("#716551")
    styles = {
        "ey": ParagraphStyle("ey", fontName=bold, fontSize=8.5, leading=12, textColor=gold, alignment=TA_CENTER, spaceAfter=9),
        "title": ParagraphStyle("title", fontName=bold, fontSize=21, leading=31, textColor=ink, alignment=TA_CENTER, spaceAfter=13),
        "meta": ParagraphStyle("meta", fontName=regular, fontSize=8.5, leading=13, textColor=muted, alignment=TA_CENTER, spaceAfter=18),
        "body": ParagraphStyle("body", fontName=regular, fontSize=10.2, leading=18, textColor=ink, alignment=TA_JUSTIFY, firstLineIndent=20, spaceAfter=8),
        "abstract": ParagraphStyle("abstract", fontName=regular, fontSize=9.4, leading=16, textColor=ink, alignment=TA_JUSTIFY, leftIndent=8*mm, rightIndent=8*mm, borderColor=gold, borderWidth=0, borderPadding=9, backColor=colors.HexColor("#FBF7EC"), spaceAfter=13),
        "h2": ParagraphStyle("h2", fontName=bold, fontSize=14, leading=21, textColor=ink, spaceBefore=17, spaceAfter=9, keepWithNext=True),
        "supp": ParagraphStyle("supp", fontName=regular, fontSize=9.8, leading=17, textColor=ink, alignment=TA_JUSTIFY, leftIndent=5*mm, rightIndent=5*mm, borderColor=colors.HexColor("#D9C28E"), borderWidth=0.6, borderPadding=9, backColor=colors.HexColor("#FFF9ED"), spaceAfter=10),
        "ref": ParagraphStyle("ref", fontName=regular, fontSize=8.4, leading=13, textColor=muted, leftIndent=7*mm, firstLineIndent=-7*mm, spaceAfter=5),
    }

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D7C49A"))
        canvas.line(22*mm, 14*mm, A4[0]-22*mm, 14*mm)
        canvas.setFont(regular, 7.5)
        canvas.setFillColor(muted)
        canvas.drawString(22*mm, 9.5*mm, f"SDE Universes · {paper['author']}")
        canvas.drawRightString(A4[0]-22*mm, 9.5*mm, str(doc.page))
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(output), pagesize=A4, rightMargin=22*mm, leftMargin=22*mm,
        topMargin=20*mm, bottomMargin=19*mm, title=paper["title"], author=paper["author"],
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(PageTemplate(id="article", frames=[frame], onPage=footer))
    story = [
        Paragraph("SDE 学员专栏 · 深化增补版", styles["ey"]),
        Paragraph(html.escape(paper["title"]), styles["title"]),
        Paragraph(f"{paper['author']} 著　·　SDE创新智商 {paper['old_score']} → {paper['score']}　·　2026年7月24日", styles["meta"]),
        Paragraph(f"<b>摘要</b>　{html.escape(abstract or paper['hook'])}", styles["abstract"]),
        Paragraph(f"<b>关键词：</b>{html.escape(keywords or paper['kind'])}", styles["meta"]),
        Spacer(1, 4*mm),
    ]
    for kind, line in blocks:
        story.append(Paragraph(html.escape(line), styles["h2" if kind == "h2" else "body"]))
    story.append(PageBreak())
    story.append(Paragraph("深化增补：不可还原性、边界与证伪", styles["h2"]))
    for heading, paragraph in SUPPLEMENTS[paper["slug"]]:
        story.append(Paragraph(html.escape(heading), styles["h2"]))
        story.append(Paragraph(html.escape(paragraph), styles["supp"]))
    story.append(Paragraph("经编辑核验的参考文献", styles["h2"]))
    for label, url in REFERENCES[paper["slug"]]:
        story.append(Paragraph(f'• <link href="{html.escape(url)}">{html.escape(label)}</link>', styles["ref"]))
    doc.build(story)


def update_publications():
    path = ROOT / "public" / "students" / "publications.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    students = {x["slug"]: x for x in data["students"]}
    for paper in PAPERS:
        student = students[paper["student"]]
        url = f'/students/{paper["student"]}/{paper["slug"]}/'
        if any(x["url"] == url for x in student["items"]):
            continue
        number = max([x.get("number", 0) for x in student["items"]] + [0]) + 1
        student["items"].insert(0, {
            "number": number, "title": paper["title"], "url": url,
            "kind": paper["kind"], "summary": paper["hook"],
        })
        student["count"] = len(student["items"])
    data["generated"] = "2026-07-24"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_works():
    for paper in PAPERS:
        path = ROOT / "public" / "students" / paper["student"] / "works" / "index.html"
        text = path.read_text(encoding="utf-8")
        if f'/{paper["slug"]}/' in text:
            continue
        card = f"""<div class="work"><span class="chip">新作 · {paper["kind"]} · 深化增补版</span><h2>{html.escape(paper["title"])}</h2>
<p class="hook">{html.escape(paper["hook"])}</p><div class="meta">SDE创新智商 {paper["old_score"]} → {paper["score"]} · 三种阅读方式 · 发表于2026年7月24日</div>
<div class="modes"><a class="m primary" href="/students/{paper["student"]}/{paper["slug"]}/">网页长文</a><a class="m ghost" href="/students/{paper["student"]}/{paper["slug"]}/read.html">在线 PDF</a><a class="m ghost" href="/students/{paper["student"]}/{paper["slug"]}/{paper["slug"]}.pdf" download>下载 PDF</a></div></div>"""
        marker = '<div class="back">'
        if marker in text:
            text = text.replace(marker, card + marker, 1)
        elif "</main>" in text:
            text = text.replace("</main>", card + "</main>", 1)
        else:
            text = text.replace('<div class="works">', '<div class="works">' + card, 1)
        path.write_text(text, encoding="utf-8")


def main():
    all_papers = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    for paper in PAPERS:
        source = source_for(paper, all_papers)
        out = ROOT / "public" / "students" / paper["student"] / paper["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(render(paper, source), encoding="utf-8")
        (out / "read.html").write_text(
            READ.format(title=html.escape(paper["title"]), pdf=f'{paper["slug"]}.pdf'),
            encoding="utf-8",
        )
        build_pdf(paper, source, out / f'{paper["slug"]}.pdf')
    update_publications()
    update_works()
    print(f"Generated {len(PAPERS)} polished papers")


if __name__ == "__main__":
    main()
