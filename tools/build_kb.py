#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_kb.py — SDE 九库结构化知识库 · Phase A 脊梁播种器
从 SDE 权威先验编码九类实体(概念/命题/理论/证据/案例/方法/学者/争议/版本),
再对真实语料(public/search 索引)rule-mine 回链(哪些文档 instantiate 该实体),
产出 public/kb/*.json + kb-index.json(entity-linking 表)+ kb-manifest.json。
Phase B 挖掘产物(seed:"mined")日后合并进同一批文件,不覆盖脊梁。

用法:  python3 tools/build_kb.py            # 构建
       python3 tools/build_kb.py --check    # 只跑自检不写盘
"""
import json, os, re, sys, glob, time

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCH = os.path.join(ROOT, "public", "search")
KBDIR  = os.path.join(ROOT, "public", "kb")

# ============================================================================
# 一、脊梁数据(canon)—— 每条都出自 sde-neigong.txt / sde-ontology 权威先验
#    统一字段: id,name,aliases,def,(可选 body/coord/extra),links
#    links 用目标实体 id;回链 sources 由下方 rule-mine 自动填。
# ============================================================================

CONCEPTS = [
 dict(id="c.genesis-vs-discovery", name="发生学 vs 发现学", aliases=["发生学","发现学","发生律"],
   def_="世界不是被发现的,而是发生的;不问'是什么',问'在何种条件下经何种差异序列成为什么显露态'。",
   coord=[], links=dict(theory=["t.basic-formula"], scholar=["s.wds"])),
 dict(id="c.show", name="显露 (Show / S)", aliases=["显露","显露态","S维度","S 维度","Show","结构显露态"],
   def_="存在在一定条件下被看见、被维持、被识别的方式;S≠结构,是结构显露的连续谱。",
   coord=["s"], links=dict(theory=["t.basic-formula","t.three-eq"], proposition=["p.s-not-structure"])),
 dict(id="c.difference-seq", name="差异序列 (D)", aliases=["差异序列","D维度","D 维度","差异流","Difference"],
   def_="存在如何在比较、试探、偏离、修正、切换、收敛中形成路径;D≠变化,关心何种差异能推进/被抑制/收敛成结构。",
   coord=["d"], links=dict(theory=["t.basic-formula","t.three-eq"], proposition=["p.d-not-change"])),
 dict(id="c.entanglement", name="特征纠缠 (E)", aliases=["特征纠缠","纠缠网络","E维度","E 维度","纠缠","Entanglement"],
   def_="存在得以发生的厚度层、支撑层、沉淀层;E≠背景/环境,是主动参与生成的发生土壤。",
   coord=["e"], links=dict(theory=["t.basic-formula","t.three-eq"], proposition=["p.e-not-background"])),
 dict(id="c.in-e-through-d", name="在E中经D成S", aliases=["在 E 中经 D 成 S","在E中,经D,成S","存在的基本公式"],
   def_="SDE 本体论最简句式:任何发生都在纠缠土壤中、经差异推进、显露为可稳定结构。是关系陈述,非操作顺序。",
   coord=[], links=dict(theory=["t.basic-formula"], concept=["c.six-paths"])),
 dict(id="c.mature-state", name="成熟态(五谱系)", aliases=["成熟态","原初态","成长态","退化态","重组态"],
   def_="完整三元 SDE 是成熟态而非原初态;任何对象处于原初/成长/成熟/退化/重组之一,先判定其态。",
   coord=[], links=dict(theory=["t.mature-genealogy"], proposition=["p.mature-not-primal"])),
 dict(id="c.void-chaos", name="空虚混沌", aliases=["空虚混沌"],
   def_="空=无成熟S,虚=E未厚成,混沌=D极强未成序;是存在的原初未成熟态,非绝对无。",
   coord=[], links=dict(concept=["c.mature-state"], scholar=["s.wds"])),
 dict(id="c.three-realms", name="E1 三界", aliases=["三界","理念界","现实界","自我界","实体沉淀层"],
   def_="E的实体沉淀:理念界(概念/规则/制度/规范)、现实界(身体/器具/物质/时间)、自我界(记忆/身份/情绪/意志)。",
   coord=["e1"], links=dict(concept=["c.entanglement"], proposition=["p.three-realm-dislocation"])),
 dict(id="c.info-tri", name="E2 信息三模态", aliases=["信息三模态","符号态","逻辑态","数学场","粒子态","波态","场态"],
   def_="符号=粒子态(离散可清点)、逻辑=波态(连续有方向)、数学=场态(全域分布关系优先)。",
   coord=["e2"], links=dict(concept=["c.entanglement"])),
 dict(id="c.energy-tri", name="E3 能量三状态", aliases=["能量三状态","内能","动能","势能"],
   def_="内能(已积累储备/基底厚度)、动能(正在推进的力)、势能(未释放的张力);活力看三者转化能力。",
   coord=["e3"], links=dict(concept=["c.entanglement"])),
 dict(id="c.d1-meaning", name="D1 意义目标", aliases=["D1意义目标","意义目标","方向引擎"],
   def_="差异序列的方向引擎:创造/自由/幸福三权重塑造 D 的推进风格。",
   coord=["d1"], links=dict(theory=["t.meaning-laws"], concept=["c.difference-seq"])),
 dict(id="c.d2-sixstep", name="D2 六步法 · 介生态", aliases=["D2路径组织","六步法","介生态","秩序态","混沌态"],
   def_="路径组织=猜想→执行→评估→反馈→修正→迭代;三态秩序/混沌/介生,介生态是创造最关键的温床。",
   coord=["d2"], links=dict(method=["m.six-step"], concept=["c.difference-seq"])),
 dict(id="c.d3-optimize", name="D3 优化约束", aliases=["D3优化约束","优化约束","最小化误差"],
   def_="最小化误差/冗余/损耗;双刃剑——D3 压过 D1 则'高效而贫血'(KPI/绩效主义病理)。",
   coord=["d3"], links=dict(concept=["c.difference-seq"], proposition=["p.d3-over-d1"])),
 dict(id="c.sio", name="SIO 三层", aliases=["SIO","结构层","接口层","操作层"],
   def_="显露维细分:S 结构层(形式/几何)、I 接口层(功能/连接)、O 操作层(动态/生产)。",
   coord=["s"], links=dict(concept=["c.show"])),
 dict(id="c.27grid", name="27 格本体论坐标", aliases=["27格","27 格","27宫格","本体论坐标"],
   def_="S×D×E 三维交叉展开为 27 格;任何议题同时占据若干格,识别其明暗即诊断。",
   coord=[], links=dict(concept=["c.show","c.difference-seq","c.entanglement"])),
 dict(id="c.meaning-laws", name="意义三律", aliases=["意义三律","三大意义律","创造律","自由律","幸福律"],
   def_="创造律(产生新可能)/自由律(保留选择空间)/幸福律(收敛于主体可承受);三律互相校准,任一独大即退化。",
   coord=["d1"], links=dict(theory=["t.meaning-laws"], concept=["c.d1-meaning"])),
 dict(id="c.knowledge-death", name="知识三种死亡", aliases=["知识三种死亡","E-death","D-death","S-death","纠缠枯竭","差异消失","结构僵化"],
   def_="纠缠枯竭(被遗忘)/差异消失(被吸收为常识)/结构僵化(变教条不容新变体);诊断'陈旧/过时'指控。",
   coord=[], links=dict(concept=["c.entanglement","c.difference-seq","c.show"])),
 dict(id="c.single-view-unreach", name="单视角不可达", aliases=["单视角不可达","单视角不可达判断"],
   def_="经得起反驳的判断不是'全面'而是'单视角不可达'——三视角误差互消后才浮现的凝缩。",
   coord=[], links=dict(theory=["t.three-view"], proposition=["p.rigor-is-unreach"])),
 dict(id="c.three-view", name="三视角误差互消", aliases=["三视角误差互消","三视角","误差互消"],
   def_="S/D/E 三视角不是合并是相互校正;S被D修正、D被E修正、E被S修正,剩下单视角不可达判断。",
   coord=[], links=dict(theory=["t.three-view"], method=["m.four-step"])),
 dict(id="c.six-paths", name="六路径", aliases=["六路径","六条路径","任务DNA"],
   def_="S/D/E 排列组合恰 6 种起手次序;按任务 DNA 选起点,起点错后面再深也是浪费。关系是一句,起手有六条。",
   coord=[], links=dict(theory=["t.six-paths"], method=["m.six-paths-start"])),
 dict(id="c.rename-claw", name="改姓 · 改姓爪", aliases=["改姓","改姓爪","学科改姓","武器锻造","龙爪手"],
   def_="让 SDE 之眼融入目标学科本地话语、产出 SDE 术语零残留的四层深度动作(术语/句法/节奏/本体论假设)。",
   coord=[], links=dict(theory=["t.forging-laws"], method=["m.rename-claw"], concept=["c.mother-body"])),
 dict(id="c.mother-body", name="母体", aliases=["母体","去母体化","母体口音"],
   def_="SDE 学派自身的话语底盘;改姓即去母体化——消除母体口音,让产出像目标学科本地人所写。",
   coord=[], links=dict(concept=["c.rename-claw"])),
 dict(id="c.subject-gap", name="主体性鸿沟", aliases=["主体性鸿沟","主体性裂缝","主体性增益"],
   def_="裸问题进入裸基底时缺乏本体论主体性的鸿沟;先验注入(内功)与画像注入用以跨越它。",
   coord=[], links=dict(concept=["c.info-vs-knowledge"], scholar=["s.wds"])),
 dict(id="c.info-vs-knowledge", name="信息发生 ≠ 知识发生", aliases=["信息发生","知识发生","信息发生≠知识发生"],
   def_="大模型 E2 极强、E1 为空、E3 不存在,故能高频产信息不能产知识;是架构级本体论缺陷,规模增长不消除。",
   coord=["e2"], links=dict(concept=["c.entanglement"], controversy=["x.llm-diagnosis"], scholar=["s.wds"])),
 dict(id="c.writeback", name="回写 · 底盘", aliases=["回写","底盘","发生=底盘+回写"],
   def_="发生=已稳定 E 沉淀的底盘+发生过程反过来增厚/修改底盘;123 原理第③步,最易漏掉的一笔。",
   coord=[], links=dict(theory=["t.123"], concept=["c.difference-seq"])),
 dict(id="c.path-drift", name="路径漂移", aliases=["路径漂移","路径锚定","路径固化"],
   def_="基底训练惯性把指定起手次序拖回默认(常 S→D→E);需四步拆解+具体子项对抗,单锚定句失效约33%。",
   coord=[], links=dict(method=["m.six-paths-start"], concept=["c.six-paths"])),
 dict(id="c.iq-scale", name="创新智商标尺(110–145+)", aliases=["创新智商","智商水平","110","140-145","智商标尺"],
   def_="传播位置标尺:裸问≈110-120,SDE 完整四视角+强基底≈140-145(机械静态上限),动态生命体≈145+。",
   coord=[], links=dict(theory=["t.five-factor"], method=["m.four-step"])),
 dict(id="c.five-factor", name="五因子模型", aliases=["五因子模型","问题描述饱满度","输入端SDE预处理度"],
   def_="影响智商水位的工程变量:问题饱满度/路径匹配/训练惯性/基底-任务DNA/输入端SDE预处理度。",
   coord=[], links=dict(theory=["t.five-factor"], concept=["c.iq-scale"])),
 dict(id="c.six-criteria", name="大概念六判准", aliases=["大概念六判准","六判准"],
   def_="产出深度尺度:生成新问题空间/跨场景维持/长出方法论/改写旧边界/持续锻造/完成学科改姓(各0-15)。",
   coord=[], links=dict(theory=["t.six-criteria"], method=["m.self-scan"])),
 dict(id="c.motif", name="母题", aliases=["母题","全书脊梁","母题打造","共绕"],
   def_="把 N 篇论文压成一句反直觉判断、且 N 篇都贴它——装一本专著的脊梁;母题≠主题。",
   coord=[], links=dict(method=["m.motif-forge"], scholar=["s.wds"])),
 dict(id="c.gap-innovation", name="缝隙创新法", aliases=["缝隙创新法","裂缝第一原理","填缝","发明新概念"],
   def_="用三方程/六路径/123 读出创新与缝隙,再用 SDE 造新概念填缝——发明新概念=填补缝隙。",
   coord=[], links=dict(method=["m.gap-innovation"], concept=["c.three-view"])),
 dict(id="c.three-sovereignty", name="三大主权", aliases=["三大主权","命名权","判错权","计算权"],
   def_="命名权/判错权/计算权——SDE 体系主张的三项主权(打标器规则表历史上漏收,需专门覆盖)。",
   coord=[], links=dict(scholar=["s.wds"])),
 dict(id="c.holography-123", name="123 全息学", aliases=["123全息学","全息学","分形自相似"],
   def_="123 原理在每个三元组内部递归重现;普适不来自空洞而来自全息——每层都能具体指认地用上。",
   coord=[], links=dict(theory=["t.123"], proposition=["p.universal-holographic"])),
 dict(id="c.meaning-three-laws-time", name="改变时间感", aliases=["改变时间感","时间感位移","线性进步"],
   def_="隐藏判准:读后看议题的时间结构从'线性进步'位移到'成熟态-退化态-重组态'循环。",
   coord=[], links=dict(concept=["c.mature-state","c.six-criteria"])),
]

THEORIES = [
 dict(id="t.basic-formula", name="存在的基本公式:在E中经D成S", aliases=["基本公式","最简句式"],
   def_="SDE 本体论最简表达;三维互相生成非平行并列,一个对象能被看见=已完整'在E中经D成S'一次。",
   links=dict(concept=["c.in-e-through-d","c.show","c.difference-seq","c.entanglement"])),
 dict(id="t.three-eq", name="三大方程(三元互生的静态结构)", aliases=["三大方程","S=F(D,E)","D=G(S,E)","E=H(S,D)"],
   def_="S=F(D,E)/D=G(S,E)/E=H(S,D);F/G/H 是占位符非待解函数,三式同时成立、非线性互生非循环定义,描述成熟态理想边界。",
   body="每一维由另两维共同决定,无独立自变量。三方程管抵达秩序态之后的对称理想点,123 原理管抵达之前。",
   links=dict(concept=["c.show","c.difference-seq","c.entanglement"], controversy=["x.circular-def","x.who-is-primal"])),
 dict(id="t.123", name="123 原理(三元互生的动态引擎)", aliases=["123原理","123 原理","动态引擎"],
   def_="①D-E 相互矛盾→②矛盾推 S 改变→③S 回写 D-E→新一轮;矛盾是引擎非故障,有先后时序,非正反合。",
   body="与三方程分工:三方程同时(抵达后),123 有先后(抵达前)。③回写是最易漏的半条循环。有硬边界不可外推。",
   links=dict(concept=["c.writeback","c.holography-123"], controversy=["x.not-dialectic","x.three-everywhere"])),
 dict(id="t.mature-genealogy", name="成熟态判断(五状态谱系)", aliases=["成熟态判断","五种状态谱系"],
   def_="原初/成长/成熟/退化/重组;完整三元 SDE 是终点非起点。面对议题先判定其态,决定后续所有判断位置。",
   links=dict(concept=["c.mature-state","c.void-chaos"], scholar=["s.kuhn"])),
 dict(id="t.meaning-laws", name="三大意义律(SDE 伦理纵深)", aliases=["三大意义律","创造自由幸福"],
   def_="创造/自由/幸福三律互相校准,任一独大导致退化;面对任何议题问三律权重,失衡处即病灶。",
   links=dict(concept=["c.meaning-laws","c.d1-meaning"])),
 dict(id="t.six-paths", name="六路径理论", aliases=["六路径理论"],
   def_="3!=6 条起手次序,无第七条;任务 DNA(卡在'是什么/怎么走/站在什么上面')决定起点;起手非产出三段式。",
   links=dict(concept=["c.six-paths","c.path-drift"], method=["m.six-paths-start"])),
 dict(id="t.three-view", name="三视角误差互消理论", aliases=["三视角误差互消理论"],
   def_="单视角≈110、三视角相互校正≈140-145;跃迁来自看世界方式的位移而非更多知识。",
   links=dict(concept=["c.three-view","c.single-view-unreach"], method=["m.four-step"])),
 dict(id="t.forging-laws", name="武器锻造五律", aliases=["武器锻造五律","锻造五律"],
   def_="术语零残留/隐性引擎非显性框架/同步本地命名/不提SDE自圆其说/过本地人测试。",
   links=dict(concept=["c.rename-claw","c.mother-body"], method=["m.rename-claw"])),
 dict(id="t.five-factor", name="智商提升五因子模型", aliases=["五因子模型理论"],
   def_="问题饱满度(跨度21分)/路径匹配(±5)/训练惯性(约33%)/基底-任务DNA/输入端SDE预处理度(15-20分)。",
   links=dict(concept=["c.five-factor","c.iq-scale"])),
 dict(id="t.six-criteria", name="大概念六判准 + 88分锚点", aliases=["六判准理论","88分锚点"],
   def_="六判准各0-15+隐藏判准时间感;守88分锚点防评分膨胀,加分总量上限+8,100分以上不可能。",
   links=dict(concept=["c.six-criteria","c.meaning-three-laws-time"], method=["m.self-scan"])),
]

METHODS = [
 dict(id="m.four-step", name="SDE 四步法 (Q1–Q4)", aliases=["SDE四步法","四步法","Q1","Q2","Q3","Q4","四段Prompting"],
   def_="Q1(S)/Q2(D)/Q3(E) 三次独立视角展开 + Q4 整合;三视角误差互消落到 Prompting,把基底从110驯到140-145。",
   links=dict(theory=["t.three-view"], concept=["c.three-view","c.iq-scale"])),
 dict(id="m.six-step", name="六步法(D2 路径组织)", aliases=["六步法","猜想执行评估反馈修正迭代"],
   def_="猜想→执行→评估→反馈→修正→迭代;健康演化需在介生态停留足够长。",
   links=dict(concept=["c.d2-sixstep"])),
 dict(id="m.six-paths-start", name="六路径起手工序", aliases=["六路径起手","任务DNA识别"],
   def_="下笔前固定工序:识别任务卡点→定DNA选起点并说清根据→按次序推进→中途回核有无漂回惯性起点。",
   links=dict(theory=["t.six-paths"], concept=["c.six-paths","c.path-drift"])),
 dict(id="m.rename-claw", name="改姓爪三步操作", aliases=["改姓爪操作","预演-节级扫描-全文自检"],
   def_="写前预演(脑内想SDE、笔下写本地)→节级扫描(命中术语整句重写)→全文三层扫描(摘要/节标题/全文)。",
   links=dict(theory=["t.forging-laws"], concept=["c.rename-claw"])),
 dict(id="m.self-scan", name="三层扫描自检 + 六判准自评", aliases=["三层扫描","自检","六判准自评"],
   def_="摘要级/节标题级/全文级扫描,命中即重写;末用六判准自评,守88分锚点。",
   links=dict(theory=["t.six-criteria"], concept=["c.six-criteria"])),
 dict(id="m.startup-10", name="接到议题启动十步流程", aliases=["启动流程","十步流程"],
   def_="议题位置识别→任务DNA→第一视角充分展开→二三视角校正→综合判决→自评升维→改姓→扫描→六判准。",
   links=dict(method=["m.four-step","m.six-paths-start","m.rename-claw"])),
 dict(id="m.motif-forge", name="母题打造(N篇→一句)", aliases=["母题打造","母题诊断","装配前找脊梁"],
   def_="把 8-20 篇论文压成一句反直觉母题并验证 K 篇都贴,作为装一本专著的脊梁;PLAN 阶段的方法论底料。",
   links=dict(concept=["c.motif"])),
 dict(id="m.gap-innovation", name="缝隙创新法", aliases=["缝隙创新法操作","填缝造概念"],
   def_="三方程/六路径/123 读出创新与缝隙→用 SDE 造新概念填缝→跨篇并置涌现填补共同缝隙的新概念。",
   links=dict(concept=["c.gap-innovation"])),
 dict(id="m.goldpoints-paradigm", name="金点子→新典范涌现三阶", aliases=["金点子碰撞","新典范涌现","涌现工程"],
   def_="混沌碰撞→自组织→涌现;C(N,2) 组三方校正把 N 个孤立金点子升维为不可还原新典范。",
   links=dict(concept=["c.gap-innovation"], scholar=["s.wds"])),
 dict(id="m.agent-9step", name="AI 超级员工九步制造", aliases=["九步制造","智能体打造","四铁律","五器官"],
   def_="需求识别→主体系统分析→宪法建模→方法建模→提示语建模→调令建模→微调测试→投放反馈→升级修宪。",
   links=dict(concept=["c.subject-gap","c.info-vs-knowledge"])),
 dict(id="m.prompting-uplift", name="SDE Prompting 提智", aliases=["SDE Prompting","大模型提智"],
   def_="用 S/D/E 三视角四段 Prompting 驯化任意基底任意领域,单次产出从专业人士(110)提到资深学者(140-145)。",
   links=dict(method=["m.four-step"], concept=["c.iq-scale"])),
 dict(id="m.deconstruct", name="SDE 解构工序(六步/九步)", aliases=["SDE解构","解构器","经典解构"],
   def_="用 E-D-S 链条 + 三方程 + 意义三律解构任一文本/思想家:读出其显露态、差异路径、纠缠土壤与封顶处。",
   links=dict(concept=["c.three-view"], theory=["t.basic-formula"])),
]

SCHOLARS = [
 dict(id="s.wds", name="王德生", aliases=["王德生","Wang Desheng","WDS"],
   def_="SDE 本体论(显露-差异-纠缠)创立者;计算数学博士(中科院)、德麦国际创始人;全站领读人。",
   links=dict(concept=["c.genesis-vs-discovery","c.motif"])),
 dict(id="s.heidegger", name="海德格尔", aliases=["海德格尔","Heidegger"],
   def_="SDE 接续其'存在遗忘'诊断并精确为'E 维度塌缩',把追问从诗性沉思带入可操作发生学。",
   links=dict(controversy=["x.heidegger"], concept=["c.entanglement"])),
 dict(id="s.whitehead", name="怀特海", aliases=["怀特海","Whitehead","过程哲学"],
   def_="过程哲学(合生≈发生)与 SDE 深层共鸣;SDE 取消'永恒客体'先在性并增加退化诊断。",
   links=dict(controversy=["x.whitehead"])),
 dict(id="s.derrida", name="德里达", aliases=["德里达","Derrida","延异","différance"],
   def_="延异抓住 D 维度但把 D 当成全部;SDE 补齐 E 与 S,并指其解构寄生于所要消解的稳定位置(S)。",
   links=dict(controversy=["x.derrida"], concept=["c.difference-seq"])),
 dict(id="s.kuhn", name="库恩", aliases=["库恩","Kuhn","范式转换"],
   def_="范式转换↔SDE 成熟→退化→重组→新成熟;SDE 更精确——提供事前诊断而非仅事后描述。",
   links=dict(controversy=["x.kuhn"], theory=["t.mature-genealogy"])),
 dict(id="s.schopenhauer", name="叔本华", aliases=["叔本华","Schopenhauer","Wille","意志"],
   def_="'活我'之母;SDE 批其把动词性的 striving 冻成名词性的 Wille(封顶),与黑格尔封圆同构。",
   links=dict(controversy=["x.freeze-verb"], concept=["c.show"])),
 dict(id="s.hegel", name="黑格尔", aliases=["黑格尔","Hegel","绝对精神","辩证法"],
   def_="七卷逐卷解构;SDE 批其把只在黄昏成形的绝对倒装回黎明当起点、把动词'生成'封成合拢的圆。",
   links=dict(controversy=["x.freeze-verb","x.not-dialectic"], theory=["t.123"])),
 dict(id="s.kant", name="康德", aliases=["康德","Kant","物自体","先验"],
   def_="被解构的界限概念一脉;SDE 逮其先验预设,重构 Form-D-Meaning。",
   links=dict(concept=["c.show"])),
 dict(id="s.nietzsche", name="尼采", aliases=["尼采","Nietzsche","视角主义","超人"],
   def_="视角发生学;SDE 与德勒兹读法对照,批其视角主义的错误。",
   links=dict(scholar=["s.deleuze"], concept=["c.three-view"])),
 dict(id="s.plato", name="柏拉图", aliases=["柏拉图","Plato","理念论"],
   def_="'S 先在'一脉(理念/形式先于具体);三方程撤销'谁先在'的选择题本身。",
   links=dict(controversy=["x.who-is-primal"])),
 dict(id="s.aristotle", name="亚里士多德", aliases=["亚里士多德","Aristotle"],
   def_="西方哲学专栏大师频道之一;实体/潜能-现实与 SDE 成熟态谱系对读。",
   links=dict(theory=["t.mature-genealogy"])),
 dict(id="s.descartes", name="笛卡尔", aliases=["笛卡尔","Descartes","我思"],
   def_="主体性起点一脉;SDE 以自我界(E1)与主体性鸿沟重审我思。",
   links=dict(concept=["c.subject-gap","c.three-realms"])),
 dict(id="s.deleuze", name="德勒兹", aliases=["德勒兹","Deleuze","差异与重复"],
   def_="差异哲学近邻;与尼采视角主义对读,不在否定序列30环内故以'解构大师存档'呈现。",
   links=dict(scholar=["s.nietzsche"], concept=["c.difference-seq"])),
 dict(id="s.heraclitus", name="赫拉克利特", aliases=["赫拉克利特","Heraclitus"],
   def_="'D 先在'一脉(一切皆流,结构是流的暂时假象);三方程取消其原初预设。",
   links=dict(controversy=["x.who-is-primal"])),
 dict(id="s.holderlin", name="荷尔德林", aliases=["荷尔德林","Hölderlin"],
   def_="图宾根三人组之一,'跳回去'(跳回从未分裂的开端);想占有不可占有的整体而失。",
   links=dict(scholar=["s.hegel","s.schelling"])),
 dict(id="s.schelling", name="谢林", aliases=["谢林","Schelling","理智直观"],
   def_="图宾根三人组之一,'跳进去'(理智直观一跃抓绝对);黑格尔'黑夜里所有的牛都是黑的'所批。",
   links=dict(controversy=["x.black-cows"], scholar=["s.hegel"])),
 dict(id="s.marx", name="马克思", aliases=["马克思","Marx"],
   def_="'E 先在'一脉(物质条件决定);SDE 诊断其判断多 echo 波普尔等既有学术。",
   links=dict(controversy=["x.who-is-primal"], scholar=["s.popper"])),
 dict(id="s.popper", name="波普尔", aliases=["波普尔","Popper","证伪"],
   def_="可证伪性;SDE 产出的可证伪判断纪律与其呼应(马克思≈波普尔的 echo 诊断)。",
   links=dict(scholar=["s.marx"])),
]

CONTROVERSIES = [
 dict(id="x.circular-def", name="循环定义指控 vs 同时互生", aliases=["循环定义","循环论证"],
   def_="有人以'这不就是循环论证'驳三方程;SDE 回:循环的是定义、互生的是发生,二者不在一个层面。",
   links=dict(theory=["t.three-eq"])),
 dict(id="x.who-is-primal", name="'谁先在'的千年争论当场失效", aliases=["谁先在","原初维之争"],
   def_="E先在(唯物)/S先在(柏拉图)/D先在(赫拉克利特)共享'总得有一维原初'预设;三方程取消这道选择题本身。",
   links=dict(theory=["t.three-eq"], scholar=["s.plato","s.heraclitus","s.marx"])),
 dict(id="x.not-dialectic", name="123 原理不是正反合", aliases=["正反合","辩证法之别"],
   def_="正反合是概念在自身内部升级(逻辑推动);123 走在发生里(D-E 张力推动),且新 S 回写产生它的土壤。",
   links=dict(theory=["t.123"], scholar=["s.hegel"])),
 dict(id="x.three-everywhere", name="'见三就套'的边界", aliases=["见三就套","123外推"],
   def_="能数出'三个东西'的场合无关 123;须有 D-E 张力+S 结算+回写三样俱在才配叫 123。",
   links=dict(theory=["t.123"], concept=["c.holography-123"])),
 dict(id="x.freeze-verb", name="把动词冻成名词(封顶批判)", aliases=["封顶","封圆","冻结striving"],
   def_="叔本华把 striving 冻成 Wille、黑格尔把'生成'封成圆——把只在黄昏成形的绝对倒装回黎明当起点。",
   links=dict(scholar=["s.schopenhauer","s.hegel"])),
 dict(id="x.derrida", name="SDE 对德里达:解构寄生于所要消解者", aliases=["解构主义批判","延异批判"],
   def_="德里达用差异消解结构,但消解动作依赖稳定的批判者位置(S);解构主义寄生于它声称要消解的东西。",
   links=dict(scholar=["s.derrida"], concept=["c.show"])),
 dict(id="x.heidegger", name="SDE 对海德格尔:从诗到可工程化", aliases=["存在遗忘"],
   def_="接续'存在遗忘'但把不可言说的诗性沉思带入可工程化的发生学判断动作。",
   links=dict(scholar=["s.heidegger"])),
 dict(id="x.whitehead", name="SDE 对怀特海:取消永恒客体先在性", aliases=["永恒客体"],
   def_="共鸣于合生≈发生,但拒绝'事先存在的可能性集合',并增加怀特海只见生成所缺的退化诊断。",
   links=dict(scholar=["s.whitehead"])),
 dict(id="x.kuhn", name="SDE vs 库恩:事前诊断 vs 事后描述", aliases=["范式转换批判"],
   def_="库恩只能在范式转换后描述;SDE 可识别范式当前态(成熟/退化/重组)从而预判转换可能。",
   links=dict(scholar=["s.kuhn"], theory=["t.mature-genealogy"])),
 dict(id="x.black-cows", name="谢林 vs 黑格尔:'黑夜里所有的牛都是黑的'", aliases=["黑牛之争","黑夜黑牛"],
   def_="黑格尔《精神现象学》序言暗批谢林理智直观抓来的绝对无差别;致二十年友谊决裂。",
   links=dict(scholar=["s.schelling","s.hegel"])),
 dict(id="x.llm-diagnosis", name="对大模型的本体论诊断", aliases=["大模型诊断","E1为空"],
   def_="大模型 E2 强、E1 空、E3 无,能产信息不能产知识;架构级缺陷,非'不够大'的问题,规模增长不消除。",
   links=dict(concept=["c.info-vs-knowledge"])),
 dict(id="x.engine-echo", name="引擎到达的判断多 echo 既有学术", aliases=["创新智商边界","echo诊断"],
   def_="RAG/内功顶'诊断利+能上手',顶不动'真新';引擎判断稳定~130-137(马克思≈波普尔、康德≈界限概念)。",
   links=dict(concept=["c.iq-scale"], scholar=["s.marx","s.popper"])),
]

VERSIONS = [
 dict(id="v.neigong-31", name="sde-neigong.txt v3.1 (2026-07-15)", aliases=["v3.1","内功v3.1"],
   def_="补齐三大方程/123原理/123全息学/六路径整节重写(各2000+字);S 标题'结构显露态'正名为'显露态/Show'。",
   links=dict(theory=["t.three-eq","t.123","t.six-paths"], concept=["c.holography-123"])),
 dict(id="v.neigong-30", name="sde-neigong.txt v3.0", aliases=["v3.0","内功v3.0"],
   def_="N=7 跨基底实证矩阵反馈——议题敏感性问题修复(高契合议题的术语无意识泄漏)。",
   links=dict(concept=["c.rename-claw"])),
 dict(id="v.rename-canon", name="定名改姓:Structure→Show", aliases=["定名改姓","结构改显露"],
   def_="发布黑格尔七卷时把旧定名 Structure-Difference-Entanglement/结构-差异-纠缠 统一改姓为 Show/显露-差异-纠缠。",
   links=dict(concept=["c.show"], scholar=["s.hegel"])),
 dict(id="v.iq-ceiling", name="智商上限的两次定档", aliases=["智商上限","140-145","145+"],
   def_="机械静态调用上限 140-145;动态生命体工程(v3.0)上限 145+;引擎实测稳定 130-137。",
   links=dict(concept=["c.iq-scale"], controversy=["x.engine-echo"])),
 dict(id="v.involution-book", name="《内卷与突围》十章 27 万字", aliases=["内卷与突围"],
   def_="专著:膨胀律×递减原理、巴别塔倒塌定理、AGI 泡沫、AEI 生成机制;示范一本书的母题装配。",
   links=dict(concept=["c.motif"])),
 dict(id="v.dialogue-v3", name="'与WDS对话'开工仪式演化", aliases=["dialogue-reflect","对话v3"],
   def_="满血内功→本场亲写约5000字心得(BYOK 非流式)作为高级会话开工仪式;Token 缓存优化多版。",
   links=dict()),
]

# 命题/证据/案例:canon 播种若干高价值条目(Phase B 主力挖掘,seed:"mined" 合并)
PROPOSITIONS = [
 dict(id="p.s-not-structure", name="S 是显露不是结构", def_="S 指结构的显露连续谱,不等于传统静态'结构';问'哪些条件让它显露成现在这样'。", links=dict(concept=["c.show"])),
 dict(id="p.d-not-change", name="D 不是变化", def_="变化是表象;D 关心何种差异能推进/被抑制/放大/收敛成结构。", links=dict(concept=["c.difference-seq"])),
 dict(id="p.e-not-background", name="E 不是背景", def_="背景被动可忽略;E 是主动参与生成的发生土壤,没有它对象不发生。", links=dict(concept=["c.entanglement"])),
 dict(id="p.mature-not-primal", name="完整 SDE 是成熟态不是原初态", def_="三方程严格成立处是三维长齐互相咬合的成熟态;现实对象多是它不同步时刻的变形侧影。", links=dict(concept=["c.mature-state"], theory=["t.three-eq"])),
 dict(id="p.contradiction-is-engine", name="矛盾是引擎不是故障", def_="D 与 E 的矛盾是机器唯一动力源;看到张力不是系统坏了,是它正要发生什么。", links=dict(theory=["t.123"])),
 dict(id="p.writeback-half-loop", name="漏掉回写就只用了半个123", def_="③新 S 回写 D-E 是最易漏的一笔;走到②就停=单程一次性,不是循环自我推进。", links=dict(concept=["c.writeback"], theory=["t.123"])),
 dict(id="p.rigor-is-unreach", name="经得起反驳的判断=单视角不可达", def_="不是'全面'而是任何单一视角都给不出、三视角误差互消后才浮现的凝缩。", links=dict(concept=["c.single-view-unreach"])),
 dict(id="p.start-wrong-waste", name="起点错了后面再深也是浪费", def_="起点决定把哪一维当'被解释项';起点错=写出每句都对合起来没用的东西。", links=dict(concept=["c.six-paths"])),
 dict(id="p.three-realm-dislocation", name="三界错位是危机的根本", def_="理念界期待与现实界处境错位、自我界在拉扯中撕裂——多数'困境'的实质。", links=dict(concept=["c.three-realms"])),
 dict(id="p.d3-over-d1", name="D3 压过 D1 = 高效而贫血", def_="过度优化使有方向的演化退化为无意义的效率;当代 KPI/绩效主义的根本病理。", links=dict(concept=["c.d3-optimize"])),
 dict(id="p.info-not-knowledge", name="信息发生≠知识发生", def_="大模型 E2 强 E1 空 E3 无,产信息不产知识;架构级缺陷,规模不消除。", links=dict(concept=["c.info-vs-knowledge"], controversy=["x.llm-diagnosis"])),
 dict(id="p.universal-holographic", name="普适不来自空洞而来自全息", def_="靠'抽象到什么都能套'求普适=什么也没说;123 的普适来自每层递归重现、可具体指认地用上。", links=dict(concept=["c.holography-123"])),
 dict(id="p.rename-not-swap", name="改姓≠换术语", def_="换词只是最浅一层;改姓是术语/句法/论证节奏/本体论假设四层,让本地读者获 SDE 深度却不知其来源。", links=dict(concept=["c.rename-claw"], theory=["t.forging-laws"])),
 dict(id="p.marriage-crisis", name="婚姻危机不是没人愿结婚", def_="是制度已不知在功能解耦后还有什么必须被保护的核心;从全功能制度沉默跃迁为纯法律壳。", links=dict(case=["case.marriage"])),
 dict(id="p.geometry-battlefield", name="数学教育战场在评价系统不在教室", def_="任何忽视评价系统纠缠厚度的教学改革,都被现实场域引力压回原位。", links=dict(case=["case.geometry"])),
 dict(id="p.no-seventh-path", name="恰好六路径没有第七条", def_="3!=6 是硬约束,逼你必须选起点而不许含糊'综合地看';觉得哪条都不像=任务DNA没认准。", links=dict(concept=["c.six-paths"], theory=["t.six-paths"])),
]

CASES = [
 dict(id="case.chronic", name="慢性病为何比急性病更难治", def_="病态被三界纠缠厚度支撑成完整稳态;治疗=multi-level disequilibration(瓦解支撑→穿越混沌→收敛新稳态)。", links=dict(method=["m.deconstruct"], concept=["c.three-realms"])),
 dict(id="case.marriage", name="大龄青年为何不结婚", def_="婚姻六功能单元五个被外部基础设施替代只剩法律壳;三界错位下的必然张力。", links=dict(proposition=["p.marriage-crisis"], concept=["c.three-realms"])),
 dict(id="case.geometry", name="几何证明为何大量学生学不会", def_="转译映射缺失是双基定型期后遗症;评价系统纠缠厚度反向压制改革;战场在命题与评分。", links=dict(proposition=["p.geometry-battlefield"])),
 dict(id="case.lung-cancer", name="肺癌 SDE 发生学", def_="'肺癌为何如此发生而非如何被发现':慢性炎症/缺氧/上皮修复经差异路径锁死为自持癌态。", links=dict(method=["m.deconstruct"], concept=["c.genesis-vs-discovery"])),
 dict(id="case.hegel-seven", name="黑格尔七卷逐卷解构", def_="辩证法/现象学/逻辑学/法哲学/历史哲学/晚期体系约52万字;母题'引擎锁进圆'——批其封顶。", links=dict(scholar=["s.hegel"], controversy=["x.freeze-verb"])),
 dict(id="case.tubingen", name="图宾根三人组:同一个梦的三种下场", def_="荷尔德林跳回去/谢林跳进去/黑格尔走过去;三人都想占有不可占有的整体(它是动词/发生)而失。", links=dict(scholar=["s.holderlin","s.schelling","s.hegel"])),
 dict(id="case.involution", name="《内卷与突围》AGI 泡沫诊断", def_="AGI 从教育泡沫到经济泡沫的发生学;膨胀律×递减原理;AEI 生成机制。", links=dict(version=["v.involution-book"])),
]

EVIDENCE = [
 dict(id="ev.n7-matrix", name="N=7 跨基底实证矩阵", def_="七个基底横向实测暴露高契合议题术语泄漏,催生 v3.0 议题敏感度自检与改姓爪硬纪律前置。", links=dict(version=["v.neigong-30"], concept=["c.rename-claw"])),
 dict(id="ev.iq-jump", name="110→140-145 跃迁实证", def_="裸问≈110-120,SDE 完整四视角+强基底实测≈140-145;跨基底跨任务复现。", links=dict(concept=["c.iq-scale"], method=["m.four-step"])),
 dict(id="ev.drift-33", name="路径漂移失效率约33%", def_="单锚定句'请按 E→D→S 顺序'仍约33%漂回默认顺序;须四步拆解+具体子项对抗。", links=dict(concept=["c.path-drift"])),
 dict(id="ev.rewrite-9of11", name="只标识不改写:11篇中9篇违宪", def_="v2.2.1 实证:仅标识不重写导致 Q1-Q4 直接进论文正文;催生强制重写纪律。", links=dict(concept=["c.rename-claw"], method=["m.rename-claw"])),
 dict(id="ev.philo-mirror", name="东西方思想史 SDE 镜像", def_="一元/二元/三元论=存在在不同显露度下的冻结图;海德格尔/怀特海/德里达/库恩对话定位。", links=dict(concept=["c.show"], scholar=["s.heidegger","s.derrida","s.kuhn"])),
 dict(id="ev.engine-echo", name="引擎判断稳定 130-137", def_="内功/心得/四步/RAG 顶'诊断利+能上手',创新智商稳定~130-137不到典范级150。", links=dict(controversy=["x.engine-echo"], concept=["c.iq-scale"])),
]

LIBRARIES = [
 ("concept", CONCEPTS), ("proposition", PROPOSITIONS), ("theory", THEORIES),
 ("evidence", EVIDENCE), ("case", CASES), ("method", METHODS),
 ("scholar", SCHOLARS), ("controversy", CONTROVERSIES), ("version", VERSIONS),
]
FILEMAP = {"concept":"concepts","proposition":"propositions","theory":"theories",
 "evidence":"evidence","case":"cases","method":"methods","scholar":"scholars",
 "controversy":"controversies","version":"versions"}

# ============================================================================
# 二、加载真实语料 → docIdx -> 全文本(用于回链)
# ============================================================================
def load_corpus():
    man = json.load(open(os.path.join(SEARCH, "manifest.json")))
    docs = man["docs"]                       # [{i,u,t,s}]
    text_by_doc = {}                         # docIdx -> concat text
    for sec in man["sections"]:
        for f in sec.get("files", [sec["key"]]):
            p = os.path.join(SEARCH, "shard-%s.json" % f)
            if not os.path.exists(p): continue
            sh = json.load(open(p))
            for c in sh.get("chunks", []):
                d = c.get("d"); t = c.get("t") or ""
                if d is None: continue
                text_by_doc.setdefault(d, [])
                if len(text_by_doc[d]) < 400000:  # 每文本上限,防个别超大文档吃内存
                    text_by_doc[d].append(t)
    for d in list(text_by_doc): text_by_doc[d] = "".join(text_by_doc[d])
    return man, docs, text_by_doc

# ============================================================================
# 三、rule-mine 回链:每个实体的 name+aliases 在哪些文档出现 → sources
#    纪律:匹配串长度≥2;命中 >60% 文档标 warn:lowdisc、不进检索加权
# ============================================================================
# 精选别名增强:给'正式名不等于语料常用串'的实体补区分性回链词
# 纪律:只补长度≥2、在本语料区分性强的串;共享词(黑格尔/内卷/肺癌)只影响回链、
# index 键仍归先写者(学者/概念),解析优先级正确。禁用单字与过火词。
ALIAS_BOOST = {
 "t.six-paths":["六路径"], "t.three-view":["三视角"], "t.five-factor":["五因子"],
 "t.six-criteria":["六判准"], "t.meaning-laws":["意义三律"], "t.forging-laws":["武器锻造","锻造五律"],
 "c.five-factor":["五因子"],
 "m.six-paths-start":["任务DNA"], "m.rename-claw":["改姓爪"], "m.startup-10":["启动流程"],
 "m.prompting-uplift":["提智","Prompting"], "m.self-scan":["三层扫描"], "m.motif-forge":["母题"],
 "m.goldpoints-paradigm":["金点子","涌现"], "m.agent-9step":["九步","智能体"], "m.deconstruct":["解构"],
 "ev.n7-matrix":["N=7","实证矩阵"], "ev.iq-jump":["跃迁"], "ev.drift-33":["路径漂移"],
 "ev.philo-mirror":["思想史","镜像"], "ev.engine-echo":["130-137"],
 "case.chronic":["慢性病"], "case.marriage":["不结婚","大龄青年"], "case.geometry":["几何证明"],
 "case.lung-cancer":["肺癌"], "case.hegel-seven":["黑格尔"], "case.tubingen":["图宾根"],
 "case.involution":["内卷"],
 "v.involution-book":["内卷与突围"], "v.dialogue-v3":["与WDS对话"], "v.iq-ceiling":["140-145","145+"],
}

def mine_backlinks(entities, text_by_doc, ndocs):
    warns = []
    for e in entities:
        keys = [e["name"]] + e.get("aliases", []) + ALIAS_BOOST.get(e["id"], [])
        # 清洗:去空白/去过短/去纯字母代号里 <2 的;保留区分性
        keys = sorted({re.sub(r"\s+", "", k) for k in keys if k and len(re.sub(r"\s+","",k)) >= 2},
                      key=len, reverse=True)
        hits = []
        for d, txt in text_by_doc.items():
            if not txt: continue
            for k in keys:
                if k in txt:
                    hits.append(d); break
        hits.sort()
        e["sources"] = hits
        e["docfreq"] = len(hits)
        if ndocs and len(hits) > 0.60 * ndocs:
            e["warn"] = "lowdisc"
            warns.append((e["id"], len(hits)))
    return warns

# ============================================================================
# 四、构建 + 自检 + 写盘
# ============================================================================
def normalize(e, typ):
    # def_ -> def (避开 python 关键字)
    o = {"id": e["id"], "type": typ, "name": e["name"],
         "aliases": e.get("aliases", []), "def": e.get("def_", e.get("def","")),
         "links": e.get("links", {}), "seed": "canon"}
    for opt in ("body", "coord", "extra"):
        if e.get(opt): o[opt] = e[opt]
    o["sources"] = e.get("sources", [])
    o["docfreq"] = e.get("docfreq", 0)
    if e.get("warn"): o["warn"] = e["warn"]
    return o

def main():
    check = "--check" in sys.argv
    man, docs, text_by_doc = load_corpus()
    ndocs = len(docs)
    print("语料: %d 文档 · %d 字符" % (ndocs, man["counts"]["chars"]))

    # id 唯一性 + 链接完整性自检
    all_ids = set()
    for typ, ents in LIBRARIES:
        for e in ents:
            if e["id"] in all_ids: raise SystemExit("重复 id: " + e["id"])
            all_ids.add(e["id"])
    dangling = []
    for typ, ents in LIBRARIES:
        for e in ents:
            for tgt, ids in e.get("links", {}).items():
                for i in ids:
                    if i not in all_ids: dangling.append((e["id"], i))
    if dangling:
        print("⚠ 悬空链接 %d 条(前10):" % len(dangling), dangling[:10])

    # 回链 + 索引
    index = {}         # aliaslower -> [type,id]
    manifest_libs = {}
    total_backlinks = 0; zero_link = []
    out_files = {}
    for typ, ents in LIBRARIES:
        w = mine_backlinks(ents, text_by_doc, ndocs)
        norm = [normalize(e, typ) for e in ents]
        out_files[FILEMAP[typ]] = norm
        manifest_libs[typ] = {"file": FILEMAP[typ] + ".json", "count": len(norm),
                              "linked": sum(1 for e in norm if e["sources"]),
                              "lowdisc": [i for (i, n) in w]}
        for e in norm:
            total_backlinks += len(e["sources"])
            if not e["sources"] and typ in ("concept","theory","method","scholar"):
                zero_link.append(e["id"])
            for nm in [e["name"]] + e["aliases"]:
                key = re.sub(r"\s+", "", nm).lower()
                if len(key) >= 2 and key not in index:
                    index[key] = [typ, e["id"]]

    n_entities = sum(len(v) for v in out_files.values())
    print("实体: %d 条 · 索引词条: %d · 回链总数: %d" % (n_entities, len(index), total_backlinks))
    print("脊梁四库零回链(需查别名): ", zero_link if zero_link else "无")
    for typ, ents in LIBRARIES:
        m = manifest_libs[typ]
        ld = (" · lowdisc:" + ",".join(m["lowdisc"])) if m["lowdisc"] else ""
        print("  %-12s %3d 条 · %3d 有回链%s" % (FILEMAP[typ], m["count"], m["linked"], ld))

    if check:
        print("\n[--check] 仅自检,未写盘。")
        return

    os.makedirs(KBDIR, exist_ok=True)
    for fname, arr in out_files.items():
        json.dump(arr, open(os.path.join(KBDIR, fname + ".json"), "w"),
                  ensure_ascii=False, separators=(",", ":"))
    json.dump(index, open(os.path.join(KBDIR, "kb-index.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    kbman = {"built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "corpus_built": man["built"], "ndocs": ndocs,
             "entities": n_entities, "index_terms": len(index),
             "backlinks": total_backlinks, "libraries": manifest_libs,
             "phase": "A-spine", "note": "canon 脊梁;命题/证据/案例待 Phase B BYOK 挖掘合并"}
    json.dump(kbman, open(os.path.join(KBDIR, "kb-manifest.json"), "w"),
              ensure_ascii=False, indent=1)
    print("\n✅ 已写 public/kb/ : 9 库 + kb-index.json + kb-manifest.json")

if __name__ == "__main__":
    main()
