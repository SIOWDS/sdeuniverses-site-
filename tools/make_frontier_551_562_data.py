#!/usr/bin/env python3
"""Create researched V7 dossiers for Frontier panels 551--562."""
from __future__ import annotations

import json
from pathlib import Path

from make_frontier_542_550_data import make_item, make_tail, records

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "frontier_551_562_data"
PANELS = []


def add(no, slug, title, group, description, lede, thesis, outlook, extra_refs, blob):
    PANELS.append(dict(
        no=no, slug=slug, title=title, group=group, description=description,
        lede=lede, thesis=thesis, outlook=outlook, extra_refs=extra_refs,
        items=records(blob),
    ))


add(
    551, "autonomous-systems-cyber-physical-systems", "自主系统与信息物理系统", "自主系统 · 安全工程",
    "从DARPA城市挑战、ROS与CPS框架到SOTIF、运行时保障和自动驾驶安全论证，审计自主闭环的二十年。",
    "自主系统并不是把控制员从画面里删掉，而是让感知、推断、动作、物理后果与人工接管在同一时钟上可追责。本面板以二十个节点追问：系统何时真的获得自治，何时只是把监控和失败转移到不显眼的位置。",
    "自主性的决定性机制是让感知—决策—执行闭环在不确定环境中仍受可验证安全约束，而不是无人运行时长增加",
    "未来五年要看安全论证能否覆盖分布外场景、网络攻击、组织接管与软件更新，并把每次越界、降级和险情回写到运行时保障证据",
    [
        "Lee, Cyber Physical Systems: Design Challenges, IEEE ISORC, 363–369 (2008).",
        "NIST SP 1500-201, Framework for Cyber-Physical Systems, Volume 1: Overview (2017).",
        "NIST SP 1900-202, Cyber-Physical Systems and Internet of Things (2019).",
        "Sheh et al., Autonomous Cybersecurity and AI Risk Management for Uncrewed Systems, NIST workshop paper (2023).",
    ],
    r"""
DARPA城市挑战|DARPA Urban Challenge|Urmson et al., Journal of Field Robotics 25, 425–466 (2008), doi:10.1002/rob.20255|封闭规则下完成城市道路是否等于开放交通自治|挑战赛成为自动驾驶系统集成的共同历史基线|把感知规划控制压进可运行整车闭环|Boss在约九十六公里城市赛道中完成与交通交互，证明多模块系统可在规则任务里长时闭环|赛道、地图与对手均受组织，开放道路的稀有行为和责任不能由完赛外推
信息物理系统设计挑战|Cyber-Physical Systems|Lee, IEEE ISORC, 363–369 (2008), doi:10.1109/ISORC.2008.25|通用计算抽象能否忽略时间与物理连续性|精确时间语义和混合系统继续构成CPS底层问题|把时间和物理动态提升为计算语义|Lee指出传统计算把时间视作非功能属性，难以保证与物理世界的确定交互，由此重写系统设计对象|若平台时延、时钟漂移和环境动力学未进入模型，软件正确性不能推出物理安全
ROS机器人中间件|Robot Operating System|Quigley et al., ICRA Workshop on Open Source Software 3, 5 (2009)|模块复用会不会同时扩散接口假设与不安全默认|ROS 2以DDS、实时性和安全通信修补早期局限|开放消息图让机器人能力可组合|ROS以节点、话题、服务和工具形成共享软件生态，使感知与控制模块可以快速替换重组|通信尽力而为、版本依赖与未经验证的软件包会把原型便利变成部署故障
协同自适应巡航|Cooperative Adaptive Cruise Control|Ploeg et al., IEEE Transactions on Intelligent Transportation Systems 15, 1437–1446 (2014), doi:10.1109/TITS.2014.2299551|车车通信收益能否抵抗丢包与异构制动|车路协同和编队控制继续进入网联自动驾驶试验|前车状态通信缩短稳定车距|CACC把无线前馈加入车载反馈，实车队列可在更短间距下抑制扰动放大|时延、丢包或恶意消息会令前馈反号，安全不能依赖通信永久可用
STPA系统事故模型|System-Theoretic Process Analysis|Leveson, Engineering a Safer World, MIT Press (2011)|事故是否主要来自部件失效而非错误交互|STPA已用于航空、汽车、医疗和软件密集系统|用不安全控制动作分析系统事故|STPA把事故看成约束失效，能捕捉每个部件正常却因时序、反馈或组织决策造成的危险|分析边界和控制结构由人划定，漏掉组织激励时图再完整也会遗漏风险
Kilobot千机器人群|Kilobot Swarm|Rubenstein, Cornejo & Nagpal, Science 345, 795–799 (2014), doi:10.1126/science.1254295|规模涌现是否足以保证任务稳定与个体可追责|群体机器人转向异构、故障恢复与现实环境|简单局部规则形成千机全局形状|一千零二十四台低成本机器人以局部通信和自组织规则完成形状汇聚，展示规模化群体行为|误差会随密度和通信遮挡累积，形成图案不等于在动态任务中安全有效
NIST信息物理框架|NIST CPS Framework|NIST SP 1500-201 and 1500-202 (2017), doi:10.6028/NIST.SP.1500-201|跨行业词汇能否成为工程验收而非概念清单|框架映射到IoT、智慧城市与人因分析|以功能、可信与生命周期视角对齐CPS|NIST工作组把系统、网络、数据、时间与可信属性放进统一分析框架，促进跨行业比较|框架本身不提供领域阈值，若没有场景测试和责任人，勾选属性不会产生安全
控制屏障函数|Control Barrier Functions|Ames et al., IEEE Transactions on Automatic Control 62, 3861–3876 (2017), doi:10.1109/TAC.2016.2638961|连续安全集能否覆盖感知误差与离散模式切换|屏障函数与学习控制结合为安全滤波主线|在线约束动作保持系统位于安全集|控制屏障函数把安全写成前向不变集条件，并可通过二次规划实时修正名义控制|安全集、动力学或状态估计若错误，数学上可行的滤波也会把系统带出真实边界
Reluplex神经网络验证|Reluplex Verification|Katz et al., CAV 2017, 97–117, doi:10.1007/978-3-319-63387-9_5|局部性质证明能否代表完整感知系统安全|神经网络验证扩展到分支定界、抽象解释与大模型|把ReLU网络性质化为可判定约束|Reluplex证明可对航空避碰网络查询特定输入域下的输出性质，打开学习部件形式验证路径|输入域和性质由人给定，未建模传感器、预处理与环境变化不在证明之内
Autoware开源自动驾驶栈|Autoware|Kato et al., IEEE/ACM CODES+ISSS, 1–6 (2018), doi:10.1109/CODESISSS.2018.00035|开放栈能否同时保持实时、硬件兼容与安全责任|Autoware持续形成Core与Universe分层生态|把自动驾驶模块和数据接口公开复用|Autoware把定位、感知、预测、规划和控制组合为可运行开源栈，降低整车研究门槛|配置差异、地图质量与未认证模块会使相同代码在不同车辆上给出不同风险
NIST CPS与物联网统一视角|CPS and IoT|NIST SP 1900-202 (2019), doi:10.6028/NIST.SP.1900-202|连接规模是否会模糊封闭控制与开放网络的差别|CPS与IoT架构继续在可信、互操作和生命周期上汇合|用共同概念分析计算物理网络|报告把智能系统定义为物理与计算部件的交互网络，并澄清CPS与IoT的重叠和差异|把所有联网设备统称CPS会淡化实时闭环、物理后果和安全等级的实质差异
Waymo安全方法|Waymo Safety Methodologies|Waymo, Safety Methodologies and Safety Readiness Determinations (2020)|企业自证材料能否构成可反驳的公众安全论证|案例、仿真、封闭场和道路证据开始组成安全论证|用多层证据决定系统何时可部署|Waymo公开硬件、行为与运行安全方法，强调从危险分析到安全准备度的证据链|指标、事故分母和内部阈值若不可独立审计，完整框架仍可能只证明自身标准
UL 4600自主产品安全标准|UL 4600|UL 4600, Standard for Evaluation of Autonomous Products, first edition (2020)|无驾驶员系统能否用传统合规测试覆盖|安全论证和证据管理成为无人系统认证补充|以结构化安全案例替代单一通过测试|UL 4600要求自主产品说明目标、危险、证据与论证关系，承认开放环境无法穷举测试|标准不保证每条论证真实；若证据选择性披露，形式完整会掩盖场景空洞
深度可达性分析|DeepReach|Bansal & Tomlin, IEEE ICRA, 1817–1824 (2021), doi:10.1109/ICRA48506.2021.9561949|神经近似能否保留Hamilton–Jacobi安全边界的保守性|神经偏微分方程扩大高维可达集估计|用神经隐式函数近似高维价值函数|DeepReach以无网格神经表示求解高维可达性问题，使在线安全分析覆盖更多状态维度|近似残差小不等于危险集保守，验证不足时速度增益会换来漏检风险
UNECE自动车道保持法规|UNECE R157 ALKS|UNECE Regulation No. 157, entered into force 2021 and amended thereafter|最低法规场景能否代表完整自动驾驶能力|速度与换道扩展仍保留运行设计域和驾驶接管边界|把限定自动驾驶功能写入型式批准|R157首次为自动车道保持系统设定运行、数据记录、驾驶可用性与最低风险动作要求|合规只覆盖规定运行设计域，不能被营销外推为所有道路和天气的自动驾驶
ISO预期功能安全|ISO 21448 SOTIF|ISO 21448:2022, Road vehicles—Safety of the intended functionality|无故障系统能否因感知和场景不足而危险|SOTIF与ISO 26262共同进入自动驾驶安全流程|把性能不足和未知场景纳入安全工程|SOTIF要求分析预期功能在合理可预见误用、触发条件和感知局限下的风险|未知场景的覆盖率无法直接证明，场景库若由历史数据封闭就会漏掉结构性新风险
运行时保障架构|Runtime Assurance|ASTM F3269-21, Standard Practice for Methods to Safely Bound Flight Behavior of Unmanned Aircraft Systems (2021)|安全切换是否能在故障前识别并保持可控|运行时监控与简化安全控制器用于高保证自治|复杂控制越界时切换到已验证安全控制|运行时保障把高性能但难验证的控制器与可验证备份及监视器组合，使实验自治有硬边界|监视器、切换逻辑或备份控制共享错误时，架构会在最需接管时同时失效
自动驾驶安全案例框架|Safety Case Framework|Waymo, A Blueprint for AV Safety, updated 2023|安全案例能否持续吸收软件更新和真实道路险情|自主驾驶发布转向多层论证而非里程总数|把系统、行为与运行证据汇成发布决策|蓝图用分层主张连接危险、要求、仿真、封闭测试与道路运营，说明为何某版本可在某区域运行|软件持续更新会使证据过期，若案例不随版本重算就成为历史装饰
无人系统网络与AI风险|Uncrewed Systems Risk|Sheh et al., NIST workshop paper on autonomous cybersecurity and AI risk management (2023)|连接与学习是否把网络攻击变成物理危险|NIST CSF 2.0与AI RMF开始共同用于无人系统|把网络、AI和实体后果纳入同一风险图|NIST论文梳理无人系统因连接、自动化和数据依赖产生的组合风险，并映射风险管理控制|分开完成网络和AI清单仍可能遗漏跨层攻击链，责任必须沿物理后果闭合
持续运行监测与安全绩效|In-Service Safety Monitoring|UNECE VMAD and NATM guidelines for automated driving systems, 2022–2024|上市前测试能否代表真实运行全生命周期|监管转向审核、仿真、场地、道路和运行监测组合|用持续证据替代一次型式批准|UNECE验证方法框架要求多支柱评估并关注在用监测，使软件定义车辆的更新可被继续审查|事故口径、暴露里程和险情报告若跨企业不可比，持续监测会退化为选择性绩效叙事
""",
)


add(
    552, "computational-precision-health", "计算精准健康", "精准医学 · 计算健康",
    "从PheWAS、iPOP与UK Biobank到多祖源全基因组、联邦学习和临床风险校准，重建精准健康证据链。",
    "精准健康不是给每个人多算一个分数，而是把基因、环境、生活轨迹和医疗决策接成能改善结局的可校准链条。本面板区分相关发现、个体预测与临床行动，尤其审计祖源偏差、缺失数据和行动阈值。",
    "精准化的决定性机制是让多源纵向信息在具体人群和临床动作上保持校准，而不是变量数量或模型复杂度增加",
    "未来五年要看多祖源数据、连续测量和真实世界试验能否共同证明净临床获益，并让风险阈值、模型漂移和不可行动发现进入知情同意",
    [
        "Collins & Varmus, A New Initiative on Precision Medicine, New England Journal of Medicine 372, 793–795 (2015).",
        "All of Us Research Program Genomics Investigators, Genomic data in the All of Us Research Program, Nature 627, 340–346 (2024).",
        "Sudlow et al., UK Biobank: An Open Access Resource, PLoS Medicine 12, e1001779 (2015).",
        "Martin et al., Clinical use of current polygenic risk scores may exacerbate health disparities, Nature Genetics 51, 584–591 (2019).",
    ],
    r"""
PheWAS电子病历表型扫描|Phenome-Wide Association Study|Denny et al., Bioinformatics 26, 1205–1210 (2010), doi:10.1093/bioinformatics/btq126|账单编码能否代表稳定临床表型|PheWAS与全基因组、实验室值和时间序列继续融合|从一个遗传变异横扫整套临床表型|PheWAS把电子病历代码聚合成表型并扫描遗传关联，使既有照护数据可反向发现多效性|编码受就医机会和报销影响，关联可能反映诊疗过程而非疾病机制
个体多组学画像|Integrated Personal Omics Profiling|Chen et al., Cell 148, 1293–1307 (2012), doi:10.1016/j.cell.2012.02.009|单人密集轨迹能否区分个体信号与偶然波动|纵向多组学队列扩展到更多参与者和可穿戴数据|在同一人身上对齐组学与临床时间|研究连续十四个月测量基因组、转录、蛋白、代谢与自身抗体，观察感染和糖代谢变化|单例的发现不能估计普遍效应，密集采样也会放大多重检验和回看解释
CPIC药物基因组指南|CPIC Guidelines|Relling & Klein, Clinical Pharmacology & Therapeutics 89, 464–467 (2011), doi:10.1038/clpt.2010.279|基因结果何时足以改变处方而非只提示风险|CPIC持续发布基因—药物对的可执行分级指南|把已有基因型转换成具体用药动作|CPIC明确指南回答如何使用已获得的药物基因结果，使发现与处方剂量或替代药物相连|等位基因功能、祖源频率和替代药可及性不同，指南不能机械跨人群应用
英国生物样本库|UK Biobank|Sudlow et al., PLoS Medicine 12, e1001779 (2015), doi:10.1371/journal.pmed.1001779|健康志愿者偏差会不会扭曲绝对风险|约五十万人数据持续链接影像、组学和医疗记录|大规模深表型与长期结局开放复用|UK Biobank把基因、生活方式、测量与后续健康记录纳入同一研究资源，改变风险模型规模|参与者比目标人群更健康且年龄受限，相对关联可稳不代表绝对风险可直接用于筛查
精准医学计划|Precision Medicine Initiative|Collins & Varmus, New England Journal of Medicine 372, 793–795 (2015), doi:10.1056/NEJMp1500523|个体差异数据能否转成可支付的健康收益|All of Us以多样性和纵向资料推进百万人队列|把治疗与预防从平均人转向个体差异|倡议把肿瘤分子分型和长期国民队列列为两条路径，推动基因、环境与生活方式联合研究|精准标签若没有可行动干预和公平可及，只会把分类做细而不改善结局
NCI-MATCH篮式试验|NCI-MATCH|Flaherty et al., Journal of Clinical Oncology 38, 3883–3894 (2020), doi:10.1200/JCO.19.03010|跨肿瘤靶点匹配能否克服低命中与耐药|分子篮式和伞式主方案已成为肿瘤试验基础设施|按分子异常而非器官匹配治疗|NCI-MATCH对多种难治肿瘤统一测序并分配靶向亚组，检验组织无关治疗逻辑|可匹配比例、变异功能和既往治疗限制会使基因可测不等于药物可用
多基因风险等同单基因风险|Polygenic Risk Scores|Khera et al., Nature Genetics 50, 1219–1224 (2018), doi:10.1038/s41588-018-0183-z|高分位风险能否在不同祖源和临床路径中保持|多祖源PRS与临床实施试验成为校准重点|聚合大量常见变异形成高风险分层|研究显示部分常见病PRS可识别与单基因变异相近风险的人群比例，推动群体筛查讨论|风险是相对且依赖训练祖源，未证明改变行为或治疗后仍有净获益
连续血糖个体反应|Personal Glucose Dynamics|Hall et al., PLoS Biology 16, e2005143 (2018), doi:10.1371/journal.pbio.2005143|短期血糖波动能否代表长期代谢风险|连续传感与个体化营养试验持续扩展|用连续轨迹揭示餐后反应异质性|连续血糖监测显示无糖尿病者也有不同葡萄糖型，并暴露平均门诊值遗漏的波动|传感误差、饮食记录和短期观察会夸大分类稳定性，不能直接贴病理标签
高性能医学|High-Performance Medicine|Topol, Nature Medicine 25, 44–56 (2019), doi:10.1038/s41591-018-0300-7|AI增效会不会以去技能化和自动化偏差为代价|人机协同评价从算法准确率转向临床工作流|机器计算与人类判断互补|Topol提出深度学习可处理影像、记录和连续数据，让临床人员把注意力返回解释与照护关系|若节省时间被更高产量吞掉，或模型错误无人敢否决，互补会变成责任稀释
PRS祖源不平等|PRS Ancestry Bias|Martin et al., Nature Genetics 51, 584–591 (2019), doi:10.1038/s41588-019-0379-x|欧洲训练的风险分数能否公平跨祖源使用|多祖源全基因组资源正改善但未消除可迁移差距|训练代表性决定风险分层误差|论文量化当前PRS在非欧洲人群性能下降，并警告临床应用可能扩大健康差异|把种族当生物代理或简单重标定不能替代多样本数据和社会环境建模
医疗联邦学习|Federated Learning in Medicine|Sheller et al., Scientific Reports 10, 12598 (2020), doi:10.1038/s41598-020-69250-1|参数不出院是否就等于隐私且无中心偏差|安全聚合、差分隐私和跨机构治理继续结合|跨医院训练而不集中原始影像|多机构脑肿瘤分割实验显示联邦模型可接近集中训练并优于单院模型|梯度仍可泄漏信息，机构样本异质和掉线会让平均聚合偏向大中心
英国生物样本库外显子组|UK Biobank Exomes|Szustakowski et al., Nature Genetics 53, 942–948 (2021), doi:10.1038/s41588-021-00885-0|大样本稀有变异关联能否直接给出药物靶点|外显子与全基因组分析扩展到更大样本|约二十万外显子连接深表型|研究系统分析蛋白编码变异与数千表型，为罕见功能变异和人类敲除提供规模证据|多重检验、表型噪声和参与偏差会令统计命中缺少机制与临床效应
Bridge2AI数据就绪计划|Bridge2AI|NIH Common Fund, Bridge2AI program launched 2022|大而多模态数据能否同时做到可复用、合乎伦理和面向AI|多个数据生成项目与技能中心推进AI就绪标准|把数据生成时的语义和伦理设计前置|Bridge2AI资助语音、细胞图谱、健康恢复力等数据并共建标准，试图避免事后清洗|共同数据规范若忽略社区语义和用途变化，会让技术互操作掩盖同意范围冲突
AlphaMissense变异效应|AlphaMissense|Cheng et al., Science 381, eadg7492 (2023), doi:10.1126/science.adg7492|模型致病分数能否替代家系和功能证据|预测覆盖大多数可能错义变异并进入研究资源|用进化与结构表征估计错义致病性|AlphaMissense为人类蛋白错义变异提供广覆盖评分，帮助排序罕见病候选|训练标签和基因约束会形成循环，临床分类仍需群体、家系、功能与表型证据
多祖源全基因组资源|All of Us Genomes|All of Us Research Program Genomics Investigators, Nature 627, 340–346 (2024), doi:10.1038/s41586-023-06957-x|扩大多样性是否足以修复医疗可及和随访差异|约二十四万五千个临床级全基因组已开放研究|让历史不足代表人群进入基因发现分母|项目报告约二十四万五千个基因组并发现逾十亿变异，约半数参与者来自非欧洲遗传祖源|研究参与多样不等于每个分析都公平，电子病历缺失与返回结果能力仍不均等
多祖源PRS临床实施|Multi-Ancestry PRS|Ding et al., Nature Medicine 29, 480–487 (2023), doi:10.1038/s41591-022-02104-x|校准改善能否在行动阈值上带来净收益|跨祖源方法和前瞻性实施试验并行推进|结合多群体效应提高风险可迁移性|多祖源建模通过共享与人群特异效应改善若干复杂病风险预测|统计提升可能很小且依赖人群标签，若不改变有效干预就没有临床效用
基因组罕见病诊断|Genomic Rare-Disease Diagnosis|Turro et al., Nature 583, 96–102 (2020), doi:10.1038/s41586-020-2434-2|统一基因组流程能否覆盖结构变异和非编码机制|全基因组进入医疗系统并与表型本体结合|在常规医疗中连接序列和精细表型|英国一项大规模罕见病研究展示标准化全基因组、家系和临床表型可发现新诊断|未诊断病例往往集中于重复区、嵌合、调控和未知基因，阴性结果需持续重分析
药物基因组嵌入病历|PGx Clinical Implementation|CPIC guideline updates and PharmGKB implementation resources, 2023–2025|指南存在是否意味着处方工作流会真正采用|预先基因分型和临床决策支持开始进入系统实施|把基因结果在处方时自动转成提示|嵌入式支持可在医师开药瞬间呈现基因—药物建议，减少结果被遗忘|警报疲劳、保险覆盖和不同实验室表型翻译会让可行动结果仍不被执行
计算患者数字孪生|Computational Patient Digital Twin|Venkatapurapu et al., npj Digital Medicine 7, review of healthcare digital twins (2024)|个体仿真能否在缺少反事实数据时验证|多尺度数字孪生从概念走向疾病特定原型|用动态模型比较个体干预轨迹|数字孪生把生理模型、临床记录和实时数据结合，试图先模拟再选择干预|同一患者只有一条真实轨迹，模型可辨识性和治疗反馈使个体反事实难以验证
AI医疗器械生命周期|AI-Enabled Medical Devices|US FDA, AI-Enabled Medical Device List and lifecycle policy materials, updated 2025|批准列表能否代表真实世界持续有效|监管转向预定变更控制、透明度与上市后监测|把会更新的模型纳入全生命周期监管|FDA持续公开AI器械并提出变更计划，使训练、验证和更新边界成为提交内容|列表并非完整市场清单且缺少统一性能分母，批准不能替代本地人群校准
""",
)


add(
    553, "biomedical-foundation-models-medical-ai", "生物医学基础模型与医学AI", "医学AI · 基础模型",
    "从皮肤影像深度学习、BioBERT与BEHRT到Med-PaLM、RETFound、多模态病理模型和LMM治理，审计医学AI。",
    "医学基础模型的价值不在参数规模，而在同一表征能否跨任务复用后仍保留疾病谱、工作流和人群差异。本面板把基准成绩、临床对话、影像迁移与监管边界分开，拒绝把考试正确率直接写成医疗能力。",
    "医学基础模型的决定性机制是可复用表征在跨机构迁移后仍保持临床校准与可追责性，而不是预训练数据或参数增加",
    "未来五年要看前瞻性临床试验、外部人群、数据泄漏审计和版本更新能否进入同一评价，并让模型知道何时拒答、升级给医生或撤回建议",
    [
        "Moor et al., Foundation models for generalist medical artificial intelligence, Nature 616, 259–265 (2023).",
        "Singhal et al., Large language models encode clinical knowledge, Nature 620, 172–180 (2023).",
        "Zhou et al., A foundation model for generalizable disease detection from retinal images, Nature 622, 156–163 (2023).",
        "WHO, Ethics and governance of artificial intelligence for health: guidance on large multi-modal models (2025).",
    ],
    r"""
皮肤癌深度学习|Dermatologist-Level Classification|Esteva et al., Nature 542, 115–118 (2017), doi:10.1038/nature21056|精选图像上的专家水平能否迁移到真实分诊|外部临床试验开始检验多肤色和手机图像|端到端卷积网络学习病变视觉表征|研究在图像数据上训练网络并与皮肤科医师比较，证明通用视觉表征可迁移到皮肤病分类|病例谱、图像质量和转诊阈值变化会令曲线下面积无法代表临床伤害
胸片深度学习基准|Chest Radiograph Deep Learning|Rajpurkar et al., arXiv:1711.05225, CheXNet (2017)|公开标签能否代表放射科最终诊断|大胸片模型转向报告生成和多机构外部验证|用弱标签海量胸片预训练疾病表征|CheXNet在ChestX-ray14上推动胸片深度学习基准，并暴露自然语言标签与病灶定位差距|报告抽取错误、设备标记和医院捷径会制造表面准确，不能从内部测试推临床优越
ClinicalBERT病历语言模型|ClinicalBERT|Alsentzer et al., Clinical Natural Language Processing Workshop, 72–78 (2019)|去标识病历文本能否跨医院保留语义|临床语言预训练进入编码、预测和摘要任务|在临床记录上继续预训练通用语言模型|ClinicalBERT展示领域语料可改善临床文本任务，令病历成为可复用表征来源|记录风格、模板和照护流程高度机构化，模型可能学习谁记录而非谁患病
BioBERT生物医学预训练|BioBERT|Lee et al., Bioinformatics 36, 1234–1240 (2020), doi:10.1093/bioinformatics/btz682|文献语言能力是否等于生物机制理解|生物医学编码器成为检索、实体和关系抽取底座|在论文语料上继续预训练获得领域表征|BioBERT在PubMed和全文语料上适配BERT，并改善实体识别、关系抽取与问答|文献偏倚和时间泄漏会进入模型，抽取关系不能自动成为因果知识
BEHRT电子病历Transformer|BEHRT|Li et al., Scientific Reports 10, 7155 (2020), doi:10.1038/s41598-020-62922-y|就诊序列能否像词序列一样建模而不丢时间和缺失机制|纵向病历基础模型扩展到代码、数值与文本多模态|用注意力学习疾病和就诊序列表征|BEHRT把诊断、年龄和位置编码成纵向序列，在多病预测上展示预训练迁移|病历事件由医疗利用产生，缺失不随机且同一代码在不同制度中含义不同
CONSORT-AI临床试验报告|CONSORT-AI|Liu et al., Nature Medicine 26, 1364–1374 (2020), doi:10.1038/s41591-020-1034-x|算法试验能否披露人机交互和错误处理|AI干预报告与SPIRIT-AI共同成为最低透明度要求|把算法版本、输入和失败写入试验报告|CONSORT-AI扩展清单要求说明模型如何整合进临床、输入质量、输出使用与错误案例|遵守报告清单不等于试验设计公平，选择性终点和对照仍可制造优势
WHO健康AI伦理原则|WHO AI for Health Ethics|WHO, Ethics and governance of artificial intelligence for health (2021)|六项伦理原则能否变成采购和问责条款|监管机构开始发布医疗AI全生命周期规则|把自主、福祉、透明、责任、公平与持续性并列|WHO把人权和伦理置于设计、部署与使用中心，反对技术性能独占治理|原则若没有数据访问、申诉、监测和制裁机制，会停留在价值声明
GatorTron临床大模型|GatorTron|Yang et al., npj Digital Medicine 5, 194 (2022), doi:10.1038/s41746-022-00742-2|扩大临床语言模型是否稳定改善复杂任务|临床大模型转向指令、检索和本地部署|九百亿词临床语料扩大语言表征|GatorTron比较不同规模模型，在临床实体、关系、相似度和问答上呈现规模收益|单一医疗系统语料与算力门槛限制复用，基准提升不说明床旁安全
Med-PaLM临床知识编码|Med-PaLM|Singhal et al., Nature 620, 172–180 (2023), doi:10.1038/s41586-023-06291-2|医学考试和专家评分能否代表患者照护|后续模型改进事实性但仍需真实临床验证|用医学指令微调和人类反馈改善问答|Med-PaLM在多项医学问答基准达到较高分数，并由临床医师评估长答案|考试题是封闭知识任务，幻觉、遗漏和群体偏差在真实对话中可能改变治疗
通用医学基础模型议程|Generalist Medical AI|Moor et al., Nature 616, 259–265 (2023), doi:10.1038/s41586-023-05881-4|一个模型能否安全覆盖多任务、多模态和多机构|通用模型研究转向适配成本、漂移与治理|以大规模自监督表征支持多种医学任务|论文提出医学基础模型可由影像、信号、文本和组学预训练后适配多任务，并列出机会与风险|通用性若靠模糊任务边界实现，会把每个专科的校准和责任降为平均性能
RETFound视网膜基础模型|RETFound|Zhou et al., Nature 622, 156–163 (2023), doi:10.1038/s41586-023-06555-x|视网膜自监督表征能否跨设备和人群泛化|外部评估开始检验域外和人口亚组|掩码自编码从大量眼底图像学通用表征|RETFound以自监督预训练改善眼病及部分系统病预测的数据效率和迁移|相机、筛查人群和疾病流行率变化会破坏校准，系统病关联容易受混杂
MedSAM医学图像分割|MedSAM|Ma et al., Nature Communications 15, 654 (2024), doi:10.1038/s41467-024-44824-z|统一提示分割能否覆盖三维、小病灶和专业协议|医学版通用分割模型继续扩展多模态与三维数据|以大规模掩码适配通用分割表征|MedSAM在多种医学图像与任务上适配Segment Anything，降低任务专用模型门槛|交互提示质量和数据分布决定结果，边界看似平滑可能漏掉临床关键微小结构
CONCH病理视觉语言模型|CONCH|Lu et al., Nature Medicine 30, 863–874 (2024), doi:10.1038/s41591-024-02856-4|图文对齐能否学习病理机制而非报告词汇捷径|病理基础模型进入零样本、检索和弱监督分类|对齐切片视觉与病理语言表征|CONCH用大规模病理图文预训练，在多种分类、分割和检索任务显示迁移能力|报告和切片配对含选择偏差，零样本标签与临床决策的误差成本不同
UNI通用病理编码器|UNI|Chen et al., Nature Medicine 30, 850–862 (2024), doi:10.1038/s41591-024-02857-3|十万级切片预训练能否跨器官与扫描仪保持|通用病理表征开始支持罕见癌和小样本任务|用自监督全切片数据训练通用编码器|UNI从大规模病理图块学习视觉表征，并在多种器官任务上减少标注需求|切片来源集中和扫描色彩差异会形成机构指纹，线性探针优越不等于临床流程优越
Med-Gemini多模态推理|Med-Gemini|Saab et al., arXiv:2404.18416 (2024)|长上下文和检索增强能否减少幻觉而不制造新错误|多模态医学模型加入影像、病历与网络检索|把通用多模态模型适配临床推理|Med-Gemini在问答、长病历和影像基准展示多任务能力，并探索不确定性引导检索|预印本基准和自选示例不构成临床证据，检索来源也可能错误或过时
TRIPOD+AI预测模型报告|TRIPOD+AI|Collins et al., BMJ 385, e078378 (2024), doi:10.1136/bmj-2023-078378|更完整报告能否阻止数据泄漏和过度拟合|AI预测模型报告标准更新替代旧TRIPOD|明确数据、评价、公平与开放要求|TRIPOD+AI扩展预测模型研究报告，使训练、验证、缺失、亚组与可用性更可审查|清单不能补救错误设计，作者完整披露后模型仍可能不适合临床用途
AMIE诊断对话系统|AMIE|Tu et al., Nature, Towards conversational diagnostic AI (2025)|模拟病人对话中的优越能否迁移到真实患者|对话AI开始接受前瞻性、真实语言与安全升级测试|用自我博弈和推理链训练诊断访谈|AMIE在结构化文字模拟会诊中与基层医师比较，显示病史采集和鉴别诊断潜力|模拟病人、纯文字和已知答案移除了体检、情绪、时间压力与责任，不可外推独立执业
WHO大型多模态模型指南|WHO LMM Guidance|WHO, Ethics and governance of AI for health: guidance on large multi-modal models (2025)|四十余项建议能否约束跨境商业模型|指南覆盖政府、开发者与医疗提供者责任|按用途和生命周期治理生成式医学AI|WHO针对诊疗、患者使用、文书、教育和研究提出透明、审计、人类监督等建议|自愿采纳和快速更新节奏可能留下监管空窗，弱卫生系统也缺乏独立评估资源
医疗AI良好机器学习实践|Good Machine Learning Practice|FDA, Health Canada & MHRA, Good Machine Learning Practice guiding principles, updated 2025|十项原则能否形成可执行提交证据|国际监管者把代表性、独立测试和人机团队纳入产品生命周期|用全生命周期质量替代一次模型验收|GMLP原则要求数据适配目标人群、训练测试独立、性能聚焦人机团队并监测部署后变化|原则不指定统一阈值，厂商若自选亚组和终点仍可合规地展示最好一面
临床自适应基础模型|Clinically Adaptive Foundation Models|Jiang et al., npj Digital Medicine, test-time clinically adaptive framework (2026)|测试时适配能否在无标签现场保持安全|域适配开始从离线重训转向部署时更新|利用现场未标注数据校正医学影像域偏移|临床自适应框架尝试让基础模型在新设备和机构上调整表征，以缓解域外下降|无监督适配可能追随患病率或采集伪影，更新后若无冻结对照就难以追责
""",
)


add(
    554, "spatial-omics-multimodal-cell-atlas", "空间组学与多模态细胞图谱", "空间组学 · 细胞图谱",
    "从成像质谱、MERFISH与空间转录组到HuBMAP三维参考图谱、空间多组学和人类胸腺地图，审计组织坐标。",
    "细胞图谱不是一张颜色更密的切片，而是要说明每个分子信号来自哪类细胞、位于什么组织关系、经历何种测量损失。本面板把分辨率、通量、分子覆盖和坐标配准放进同一证据账。",
    "空间图谱的决定性机制是让分子状态保留可复查的组织邻域与坐标关系，而不是细胞数、颜色数或基因数增加",
    "未来五年要看二维切片能否组成带不确定度的三维参考系，跨技术映射是否守住稀有生态位，并让疾病、年龄和祖源差异进入共同坐标而非被平均掉",
    [
        "Regev et al., The Human Cell Atlas, eLife 6, e27041 (2017).",
        "HuBMAP Consortium, The human body at cellular resolution, Nature 574, 187–192 (2019).",
        "Börner et al., Human BioMolecular Atlas Program: 3D Human Reference Atlas, Nature Methods (2025).",
        "Yayon et al., A spatial human thymus cell atlas, Nature 633, 902–910 (2024).",
    ],
    r"""
成像质谱细胞地图|Imaging Mass Cytometry|Giesen et al., Nature Methods 11, 417–422 (2014), doi:10.1038/nmeth.2869|金属标签多重成像能否保持抗体特异与组织形态|高维组织成像与单细胞分割继续融合|用同位素标签同时定位多种蛋白|成像质谱以激光烧蚀和质谱读取数十种抗体标签，使组织切片获得高维蛋白坐标|抗体交叉反应、离子串扰和分割错误会把技术通道误写成细胞状态
MIBI多离子束成像|MIBI|Angelo et al., Nature Medicine 20, 436–442 (2014), doi:10.1038/nm.3488|多重离子成像的定量能否跨批次比较|肿瘤免疫空间生态成为主要应用|离子束逐像素读取金属标记抗体|MIBI在固定组织中同时测量多种蛋白并保留亚细胞位置，突破荧光通道限制|像素强度受标签、切片厚度和仪器漂移影响，空间共现不等于细胞互作
MERFISH高通量原位RNA|MERFISH|Chen et al., Science 348, aaa6090 (2015), doi:10.1126/science.aaa6090|纠错编码能否在拥挤细胞中保持分子计数|MERFISH扩展到更大基因集和三维组织|组合条码与纠错原位识别RNA|MERFISH用多轮杂交的二进制条码和纠错设计，在单细胞原位测量大量RNA|探针效率、光学拥挤与轮次配准造成基因特异缺失，低表达分子尤其脆弱
空间转录组|Spatial Transcriptomics|Ståhl et al., Science 353, 78–82 (2016), doi:10.1126/science.aaf2403|捕获点混合多细胞时能否还原真实邻域|高密度阵列与单细胞解卷积不断提高空间解析|给转录本加位置条码再测序|空间转录组把切片置于带坐标条码的阵列，将全转录组读数映回组织形态|捕获直径、扩散和组织透化会混合邻细胞，算法拆分不能凭空恢复未测信息
CODEX循环蛋白成像|CODEX|Goltsev et al., Cell 174, 968–981.e15 (2018), doi:10.1016/j.cell.2018.07.010|多轮显影会不会累积漂白、位移与抗体干扰|空间免疫图谱扩展到大组织和临床队列|DNA条码抗体分轮显影数十蛋白|CODEX以条码和迭代成像在原位解析免疫细胞类型、邻域与组织结构|轮次配准和分割错误会系统影响细胞邻接，面板选择也限制可见生物学
高清空间转录组|HDST|Vickovic et al., Nature Methods 16, 987–990 (2019), doi:10.1038/s41592-019-0548-y|更小空间珠是否会因捕获量下降而失去灵敏度|分辨率与分子覆盖的折衷成为平台比较核心|用微米级条码珠阵列提高空间分辨|HDST把空间单元降到约两微米尺度，使组织结构可接近细胞甚至亚细胞定位|每个珠子转录本稀疏，空间精细不等于表达定量精确
Slide-seq组织RNA地图|Slide-seq|Rodriques et al., Science 363, 1463–1467 (2019), doi:10.1126/science.aaw1219|随机珠阵列解码能否稳定覆盖大组织|Slide-seqV2提高捕获效率并扩展脑图谱|把条码珠位置与切片转录本相连|Slide-seq在大面积组织以约十微米珠构建转录空间图，兼顾尺度与近细胞分辨率|珠位置、RNA扩散和低捕获率使稀有状态易被邻域平滑掩盖
人类细胞图谱计划|Human Cell Atlas|Regev et al., eLife 6, e27041 (2017), doi:10.7554/eLife.27041|参考图谱能否代表年龄、祖源、状态和采样部位差异|HCA进入器官网络、疾病比较与空间整合|用开放标准描绘人体细胞类型和状态|HCA提出跨组织、技术和地区建立人类细胞参考图谱，并重视数据门户与伦理|参考若由易取样健康组织主导，会把代表不足人群和动态状态标成偏离
HuBMAP人体分子图谱|HuBMAP|HuBMAP Consortium, Nature 574, 187–192 (2019), doi:10.1038/s41586-019-1629-x|多平台数据能否落进共同人体坐标|2023年以来肾、肠和胎盘空间图谱成套发布|构建健康成人身体的多尺度三维地图|HuBMAP组织组织获取、组学、成像、数据门户和共同坐标，目标是从器官到细胞统一参考|供体数、取材方向和组织变形会使共同坐标带有巨大不确定度
seqFISH+单细胞原位转录组|seqFISH+|Eng et al., Nature 568, 235–239 (2019), doi:10.1038/s41586-019-1049-y|一万基因原位读出能否控制误码与光学拥挤|原位转录组与组织结构建模继续结合|组合荧光编码扩展到转录组尺度|seqFISH+以多轮编码在单细胞中读取约一万种转录本，并保持亚细胞位置|复杂探针设计和成像轮次限制组织厚度，未检测不能直接解释为未表达
DBiT-seq微流控空间多组学|DBiT-seq|Liu et al., Cell 183, 1665–1681.e26 (2020), doi:10.1016/j.cell.2020.10.026|交叉流道像素能否保持组织边界和双模态定量|空间转录与蛋白共同测量成为平台主线|正交微流控在组织上写入二维条码|DBiT-seq把两组条码通道交叉，能在同一切片联合读取RNA与选定蛋白|像素仍含多细胞且蛋白面板受限，两个模态的动态范围和缺失机制不同
Tangram单细胞到空间映射|Tangram|Biancalani et al., Nature Methods 18, 1352–1362 (2021), doi:10.1038/s41592-021-01264-7|计算映射会不会把参考图谱先验强加给切片|跨模态映射开始报告不确定度与未匹配细胞|用共同基因把单细胞表征映回空间|Tangram优化单细胞表达与空间读数的匹配，可推断未直接测量基因的空间分布|参考缺少的细胞无法正确映射，平滑解会制造看似合理却不存在的生态位
seq-Scope亚细胞空间转录组|Seq-Scope|Cho et al., Cell 184, 3559–3572.e22 (2021), doi:10.1016/j.cell.2021.05.010|亚微米条码是否受RNA扩散和稀疏计数支配|超高分辨平台转向细胞器与组织大图兼顾|用高密度测序簇作空间条码阵列|Seq-Scope把测序流动槽簇转成亚微米坐标，展示组织和亚细胞转录结构|名义像素远小于有效分辨率，捕获效率与分子扩散决定真实可辨尺度
Stereo-seq厘米尺度纳米阵列|Stereo-seq|Chen et al., Cell 185, 1777–1792.e21 (2022), doi:10.1016/j.cell.2022.04.003|超大视野与高分辨能否同时保持一致捕获|时空胚胎和器官图谱采用DNA纳米球阵列|大面积高密度条码同时覆盖尺度与细节|Stereo-seq以DNA纳米球阵列描绘小鼠器官发生，连接厘米视野和近细胞空间读数|有效分辨率仍受RNA捕获与聚合影响，跨芯片归一化会改变发育梯度
cell2location空间解卷积|cell2location|Kleshchevnikov et al., Nature Biotechnology 40, 661–671 (2022), doi:10.1038/s41587-021-01139-4|贝叶斯解卷积能否区分相近细胞并避免参考偏差|空间细胞丰度估计广泛用于低分辨平台|用单细胞参考估计每个空间点的细胞组成|cell2location以层次模型分离平台差异和细胞型信号，输出位置中的细胞丰度|参考标注、基因选择和先验细胞数会决定结果，稀有或新状态可能被硬分给最近类型
Tabula Sapiens多器官细胞图谱|Tabula Sapiens|Tabula Sapiens Consortium, Science 376, eabl4896 (2022), doi:10.1126/science.abl4896|多器官统一流程能否抵消供体和取材偏差|大型跨器官单细胞参考用于空间映射|同一供体多组织连接细胞身份|图谱分析近五十万细胞、二十四种组织，并利用部分同供体取材比较器官共享细胞|非空间解离会丢失邻域并选择性损伤细胞，不能作为空间真值直接回填
CosMx空间分子成像|CosMx Spatial Molecular Imager|He et al., Nature Biotechnology 40, 1794–1806 (2022), doi:10.1038/s41587-022-01483-z|高面板单分子成像能否在临床固定组织中稳定|商业平台推动千基因与蛋白联合空间分析|在单细胞和亚细胞位置读取RNA与蛋白|CosMx展示固定组织中的高重数原位RNA及蛋白检测，并支持细胞级空间分型|面板、细胞边界和背景阈值影响计数，商业处理管线若不透明会削弱复现
HuBMAP肾脏空间多组学|HuBMAP Kidney Atlas|Lake et al., Nature 619, 585–594 (2023), doi:10.1038/s41586-023-05769-3|多模态整合能否区分损伤状态与取材应激|健康和损伤生态位进入人体参考图谱|把转录、染色质和空间位置连接到肾单位|研究识别五十一类细胞和二十八种损伤相关状态，并定位适应与退行生态位|病肾样本、治疗和冷缺血会影响状态，横断面地图不能直接给出演化方向
三维人体参考图谱|3D Human Reference Atlas|Börner et al., Nature Methods, HuBMAP HRA framework (2025)|不同供体二维切片能否可靠映射到统一三维器官|二十余联盟协作共同坐标、知识图谱和器官模型|用共同坐标连接器官结构、细胞和标志物|HRA把解剖结构、细胞类型和标志物映入三维器官参考，并开放数据与工具|器官形变、尺度和个体差异使坐标不是精确地址，映射置信度必须显式保留
空间人类胸腺图谱|Spatial Human Thymus Atlas|Yayon et al., Nature 633, 902–910 (2024), doi:10.1038/s41586-024-07944-6|发育连续轨迹能否由横断面空间数据推断|空间转录与单细胞多组学整合描绘胸腺发育|把胸腺细胞状态放回连续发育生态位|研究整合空间转录、单细胞与多组学，解析胸腺细胞发育和组织区域关系|年龄、供体和切片方向混杂可被算法误解为连续发育，仍需谱系和功能验证
""",
)


add(
    555, "protein-language-models-generative-biology", "蛋白质语言模型与生成生物学", "生成生物学 · 蛋白设计",
    "从UniRep、ESM与AlphaFold到ProteinMPNN、RFdiffusion、AlphaFold 3和开放生成式CRISPR，审计序列设计闭环。",
    "蛋白语言模型把进化留下的序列当作训练语料，但自然界会存在的蛋白不等于实验室能表达、更不等于满足指定功能。本面板把表征、结构预测、逆向折叠、从头生成与湿实验筛选逐层分开。",
    "生成生物学的决定性机制是让进化表征在明确物理与功能约束下产生可湿实验验证的新分子，而不是困惑度或结构置信度变好",
    "未来五年要看生成模型能否公开失败分母、跨实验室复现实验功能，并把免疫原性、可制造性、生物安全和序列新颖性同时纳入多目标设计",
    [
        "Rives et al., Biological structure and function emerge from scaling unsupervised learning, PNAS 118, e2016239118 (2021).",
        "Jumper et al., Highly accurate protein structure prediction with AlphaFold, Nature 596, 583–589 (2021).",
        "Watson et al., De novo design of protein structure and function with RFdiffusion, Nature 620, 1089–1100 (2023).",
        "Abramson et al., Accurate structure prediction of biomolecular interactions with AlphaFold 3, Nature 630, 493–500 (2024).",
    ],
    r"""
UniRep统一蛋白表征|UniRep|Alley et al., Nature Methods 16, 1315–1322 (2019), doi:10.1038/s41592-019-0598-1|无监督序列表征能否跨家族预测工程性质|蛋白语言模型规模化沿用其迁移学习逻辑|用进化序列预训练通用蛋白向量|UniRep在约两千四百万条序列上训练循环模型，以少量标注改善稳定性和功能预测|数据库同源泄漏与家族偏差会让随机划分过度乐观，嵌入不能替代实验因果
TAPE蛋白迁移基准|TAPE|Rao et al., NeurIPS 32 (2019), arXiv:1906.08230|统一基准会不会奖励数据划分捷径|远同源和结构感知划分成为蛋白模型评价底线|用多任务比较序列预训练迁移|TAPE汇集结构、接触、远同源和工程任务，检验不同预训练表征的通用性|基准规模小且任务代理化，排行榜进步不能直接代表新功能设计
ESM规模化蛋白语言模型|ESM|Rives et al., PNAS 118, e2016239118 (2021), doi:10.1073/pnas.2016239118|规模增长是否真的学到结构而非家族统计|ESM系列扩展到结构、功能与生成模型|大规模无监督学习涌现结构和功能信号|模型从二点五亿条序列学习表示，注意力与接触、二级结构及功能预测相关|进化数据库极不均衡，涌现相关不说明模型掌握折叠物理或可设计性
AlphaFold 2结构预测|AlphaFold 2|Jumper et al., Nature 596, 583–589 (2021), doi:10.1038/s41586-021-03819-2|静态结构置信度能否代表动态、配体与突变效应|AlphaFold数据库和后续多聚体模型扩大覆盖|联合序列进化与几何推理预测三维结构|AlphaFold 2在CASP14显著提升多数单链结构准确度，并给出逐残基置信度|无序区、构象集合、复合物和训练相似结构会限制解释，预测不是实验结构
RoseTTAFold三轨网络|RoseTTAFold|Baek et al., Science 373, 871–876 (2021), doi:10.1126/science.abj8754|序列距离坐标三轨通信能否跨新折叠泛化|三轨表征进入RFdiffusion设计架构|在一维二维三维表征间反复传递信息|RoseTTAFold以三轨网络快速预测蛋白结构与复合体，并展示方法可开放复用|预测精度仍依赖多序列比对与模板，低置信区域不能被顺滑模型外观掩盖
ProtTrans大规模序列预训练|ProtTrans|Elnaggar et al., IEEE Transactions on Pattern Analysis and Machine Intelligence 44, 7112–7127 (2022), doi:10.1109/TPAMI.2021.3095381|海量算力收益能否在低资源实验室复现|更高效蛋白模型开始压缩与开放嵌入|把Transformer迁移到数十亿蛋白序列|ProtTrans比较多种语言模型并展示单序列表征在结构和定位任务上的迁移能力|训练碳成本、数据库冗余和评测重叠会使规模优势难以公平换算
ProteinMPNN逆向折叠|ProteinMPNN|Dauparas et al., Science 378, 49–56 (2022), doi:10.1126/science.add2187|给定骨架的高概率序列能否稳定表达并折叠|ProteinMPNN成为生成骨架后的标准序列设计器|以结构条件生成兼容氨基酸序列|模型在蛋白结构图上生成序列，实验显示多种设计比传统方法有更高成功率|固定骨架忽略动力学和功能，序列概率高也可能聚集、降解或缺乏活性
ProGen可控蛋白生成|ProGen|Madani et al., Nature Biotechnology 41, 1099–1106 (2023), doi:10.1038/s41587-022-01618-2|自然语言式控制标签能否指定真实功能|条件蛋白生成进入酶类和家族定向设计|以家族与功能标签条件化自回归序列|ProGen生成与天然序列显著不同的溶菌酶，并有部分样品在实验中保持活性|测试家族和样本数有限，活性存在不等于性能、稳定性与安全性达到应用要求
ProtGPT2从头序列生成|ProtGPT2|Ferruz, Schmidt & Höcker, Nature Communications 13, 4348 (2022), doi:10.1038/s41467-022-32007-7|似蛋白序列统计能否保证可折叠与功能|无条件生成转向结构与功能约束|用自回归语言模型生成蛋白样序列|ProtGPT2生成覆盖自然蛋白空间附近且具预测结构特征的新序列，展示无条件探索能力|结构预测自洽可能与生成模型共享先验，缺少表达和功能实验就不是新生物学
ESMFold单序列结构预测|ESMFold|Lin et al., Science 379, 1123–1130 (2023), doi:10.1126/science.ade2574|语言表征能否替代多序列比对而保持置信|大规模宏基因组结构图谱采用快速单序列预测|直接从语言模型表征生成三维结构|ESMFold显著加快单序列预测，并用于构建数亿宏基因组蛋白结构图谱|速度与覆盖以部分精度为代价，陌生家族和低置信预测不可当作确定结构
AlphaFold蛋白结构数据库|AlphaFold DB|Varadi et al., Nucleic Acids Research 50, D439–D444 (2022), doi:10.1093/nar/gkab1061|海量预测结构会不会诱导忽略置信区间|数据库扩展到两亿余条预测并与注释资源连接|把结构预测从单次服务变成公共基础设施|AlphaFold DB开放大规模蛋白预测和逐残基置信度，使结构假设可被快速检索|数据库规模不等于实验覆盖，低置信区、异构体和复合状态需在下游分析传播
RFdiffusion从头蛋白设计|RFdiffusion|Watson et al., Nature 620, 1089–1100 (2023), doi:10.1038/s41586-023-06415-8|扩散生成的几何是否能兑现指定结合与功能|方法扩展到全原子、酶和抗体设计|从噪声迭代生成满足几何条件的骨架|RFdiffusion可按对称、基序和靶标条件生成多类结构，实验验证部分结合蛋白和功能设计|实验阳性来自筛选后的子集，设计总数、合成失败和亲和力分布必须进入分母
语言模型抗体设计|Language-Model Antibody Design|Shanehsazzadeh et al., Nature Biotechnology, generative antibody design studies (2023)|保持天然性分数能否同时提高亲和与特异|抗体生成结合结构、亲和成熟与可开发性筛选|以抗体序列分布提出少量突变候选|蛋白语言模型可在缺少靶标结构时排序抗体突变并发现保持结合的变体|天然样式不保证免疫原性低、聚集少或脱靶可控，候选仍需完整开发性实验
AlphaFold 3分子相互作用|AlphaFold 3|Abramson et al., Nature 630, 493–500 (2024), doi:10.1038/s41586-024-07487-w|联合结构预测能否替代结合自由能和动态实验|模型可预测蛋白、核酸、小分子、离子与修饰残基复合物|用扩散架构统一多类生物分子复合体|AlphaFold 3在多数相互作用类别超过专用方法，扩大结构假设空间|特定RNA、抗体、手性和构象变化仍有失败，结构准确不直接给出亲和、动力学或药效
Evo长基因组基础模型|Evo|Nguyen et al., Science, sequence modeling from molecular to genome scale (2024)|长上下文能否学到基因组因果调控而非共现|模型用于蛋白、非编码DNA与合成基因组元件设计|在单碱基分辨率跨越长基因组上下文|Evo以原核和噬菌体序列训练长上下文模型，展示从突变效应到多基因系统生成任务|训练范围不含真核复杂调控，生成序列的生物安全和功能验证远落后于计算规模
OpenCRISPR生成式编辑器|OpenCRISPR-1|Ruffolo et al., bioRxiv 2024, generative design of CRISPR-Cas proteins|生成Cas蛋白能否兼顾活性、特异和免疫风险|开放模型与实验验证推动可编程基因编辑器设计|用蛋白语言模型生成远离天然家族的Cas序列|研究公开生成模型并验证部分新Cas蛋白在细胞中的编辑活性，展示从序列到工具的闭环|预印本样本与靶位有限，脱靶、递送、免疫原性和长期安全尚不能由体外活性替代
ESM3多模态生成模型|ESM3|Hayes et al., Science, Simulating 500 million years of evolution with a language model (2025)|同时建模序列结构功能会不会造成互相验证的闭环|生成模型可按部分序列、结构与功能提示补全蛋白|在离散轨道中联合生成序列结构功能|ESM3展示多模态提示生成，并实验表达一个与已知荧光蛋白远缘的候选|单个醒目成功不能代表总体成功率，模型预测结构与功能标签也不是独立证据
全原子扩散设计|All-Atom Protein Design|Krishna et al., Science, Generalized biomolecular modeling and design with RoseTTAFold All-Atom (2024)|全原子模型能否准确处理小分子参数和溶剂效应|全原子生成开始面向配体结合与化学环境|在统一图中表示蛋白、核酸和小分子原子|RoseTTAFold All-Atom扩展结构建模到非蛋白组分，为配体条件设计提供统一表示|训练结构偏向稳定复合物，质子化、金属、溶剂和诱导契合会改变真实能量景观
生成酶催化位点|Generative Enzyme Design|Yeh et al., bioRxiv and Nature-era de novo enzyme design studies (2023–2025)|几何匹配能否转化为足够催化效率和选择性|扩散骨架与序列设计结合实验定向进化|围绕过渡态几何生成催化骨架|生成式方法可围绕功能基序提出大量新骨架，再由ProteinMPNN和实验筛选获得初始活性|初始活性常远低于天然酶，筛选和后续进化贡献若不拆开会夸大模型因果
湿实验生成闭环|Design-Build-Test-Learn for Proteins|National Academies and protein design benchmark initiatives, 2024–2026|计算命中率能否用一致分母跨实验室比较|社区开始要求公开全量设计、表达和功能失败|把生成、合成、表达、纯化和功能测定串成证据链|标准化闭环可区分序列生成、结构形成与真实功能各自成功率，使算法比较不再只报最佳分子|实验协议、检测下限和人工救援差异仍会改变命中率，公共盲测是必要边界
""",
)


add(
    556, "translational-medicine-biomedical-innovation", "转化医学与生物医学创新", "转化医学 · 生物创新",
    "从遗传靶点验证、类器官与主方案试验到真实世界证据、组织芯片和NCATS转化原则，审计从发现到健康收益。",
    "转化不是把论文沿一条管线向临床推，而是实验室、患者、监管、制造和支付不断相互否决又回写的循环。本面板把‘死亡之谷’拆成二十个可检查节点，特别保留失败、停项和反向转化。",
    "转化的决定性机制是让实验、临床、监管和实施之间形成可回写的证据闭环，而不是候选数量或开发速度单独增加",
    "未来五年要看平台试验、人体相关模型和真实世界数据能否提前淘汰无效路线，同时让制造、可及性和患者优先级在首次人体研究前进入设计",
    [
        "Zerhouni, Translational and Clinical Science—Time for a New Vision, New England Journal of Medicine 353, 1621–1623 (2005).",
        "Woodcock & LaVange, Master Protocols to Study Multiple Therapies, New England Journal of Medicine 377, 62–70 (2017).",
        "US FDA, Real-World Evidence Program Framework (2018).",
        "NCATS, Translational Science Principles, updated July 2025.",
    ],
    r"""
转化研究双向道路|Bench-to-Bedside and Back|Zerhouni, New England Journal of Medicine 353, 1621–1623 (2005), doi:10.1056/NEJMsb053912|转化是否被误画成基础发现单向流向临床|反向转化和团队科学成为体系原则|让患者观察回写基础问题|新愿景强调临床研究与基础科学双向连接，以共同基础设施跨越学科和机构边界|若只统计上市产品，失败和患者提出的新机制仍会被管线叙事抹去
患者来源类器官|Patient-Derived Organoids|Sato et al., Nature 459, 262–265 (2009), doi:10.1038/nature07935|体外三维上皮能否代表免疫、血管和药代环境|类器官进入癌症药敏、遗传病和再生研究|用干细胞自组织保留组织特征|肠隐窝干细胞可长期形成含多类上皮细胞的三维结构，为患者特异模型奠基|缺少基质、免疫、血管和系统暴露时，药物反应不能直接预测人体疗效
I-SPY 2适应性平台|I-SPY 2|Barker et al., Clinical Pharmacology & Therapeutics 86, 97–100 (2009), doi:10.1038/clpt.2009.68|贝叶斯适应是否因时变对照和亚组探索产生偏差|乳腺癌平台持续毕业或淘汰多种方案|在共同主方案内按生物标志物更新分配|I-SPY 2让多个新辅助治疗共享对照并动态学习生物标志物亚组，缩短进入确证试验路径|模型先验、终点替代性和入组时间变化会影响毕业概率，仍需独立确认
NIH NCATS转化科学中心|NCATS|US NIH, NCATS established under FY2012 appropriations|新机构能否解决分散在制度和激励中的瓶颈|NCATS以CTSA、组织芯片和药物再利用构建共同方案|把管线共性障碍本身作为科学对象|NCATS成立后把加速诊断、治疗与干预的科学和运营创新集中为任务|集中资源若按速度奖励，会把艰难但重要的可及性、阴性结果和社区需求排后
遗传学提高靶点成功率|Human Genetics and Drug Targets|Nelson et al., Nature Genetics 47, 856–860 (2015), doi:10.1038/ng.3314|遗传支持与药物获批的关联能否证明因果|人类敲除和生物样本库继续用于靶点去风险|用人类遗传证据验证靶点方向|分析显示具有遗传支持的靶点在开发管线中更可能取得成功，推动靶点选择前移|公开管线和已知靶点有选择偏差，遗传效应终身暴露也不等于药物短期干预
患者类器官药敏预测|Organoid Drug Response|Vlachogiannis et al., Science 359, 920–926 (2018), doi:10.1126/science.aao2774|晚期癌症类器官能否预测异质病灶和人体暴露|类器官药筛进入前瞻性共临床研究|比较患者治疗反应与体外类器官反应|研究建立胃肠癌类器官库并报告体外药物反应与患者结局的对应，显示个体模型潜力|取样病灶、培养选择和回顾性比较会抬高一致性，阴性培养也属于失败分母
二十一世纪治愈法与真实世界证据|21st Century Cures and RWE|US Congress, 21st Century Cures Act (2016); FDA RWE Framework (2018)|常规数据能否在混杂下支持监管因果|FDA发布数据适用性和研究设计指导|让电子病历与理赔补充传统试验|法律要求评估真实世界证据支持新适应证和上市后要求，促使监管方法系统化|数据可得不等于可用，治疗选择、缺失和编码漂移会制造无法校正的偏差
主方案试验|Master Protocols|Woodcock & LaVange, New England Journal of Medicine 377, 62–70 (2017), doi:10.1056/NEJMsr1611625|共享对照和多臂决策能否保持统计独立与治理清晰|篮式、伞式和平台试验在癌症与传染病扩张|一套基础设施连续比较多治疗或亚组|主方案减少重复启动成本并可按统一标准加入或退出治疗臂，使学习持续化|多重比较、时变对照和复杂沟通会增加解释债务，速度不能牺牲可审计性
首批CAR-T批准|CAR-T Translation|US FDA approvals of tisagenlecleucel and axicabtagene ciloleucel (2017)|高缓解率能否抵消细胞制造、毒性和可及性|细胞治疗扩展到早线、实体瘤与现货平台|把患者T细胞工程化为活药物|CAR-T把受体设计、个体制造、住院监测和长期随访合成一种新转化路径|细胞因子风暴、神经毒性、失败制造与高成本令试验疗效不能等同人群获益
FDA真实世界证据框架|FDA RWE Framework|US FDA, Framework for FDA's Real-World Evidence Program (2018)|观察数据是否可满足适用性、可靠性和因果设计要求|RWE指南细化数据标准与监管提交|按监管问题选择数据与分析而非先有库再找结论|框架区分数据是否适用、研究设计能否回答问题和执行是否合规，为RWE设定审查路径|未测混杂和数据生成过程若不可重建，再先进的加权也不能制造随机化
RECOVERY平台试验|RECOVERY Trial|RECOVERY Collaborative Group, New England Journal of Medicine 384, 693–704 (2021), doi:10.1056/NEJMoa2021436|简化大样本能否在紧急状态保持数据质量|平台快速确认地塞米松并淘汰多种无效疗法|用极简随机化在常规医疗快速学习|RECOVERY借英国医疗系统迅速入组并证明地塞米松降低需氧住院患者死亡，改变全球实践|集中系统和明确硬终点不可简单复制到慢病，未纳入人群和长期伤害仍需补证
组织芯片与动物替代|Tissue Chips|NCATS Tissue Chip for Drug Screening program, 2012–2025|微生理系统能否预测整个人体药代和免疫反应|FDA Modernization Act 2.0推动非动物方法进入监管讨论|在可控芯片上重建人类组织功能|器官芯片结合人细胞、流动和机械刺激，能针对特定毒性与疾病机制提供人体相关读数|每个芯片只覆盖有限器官和时间尺度，材料吸附、成熟度和跨器官耦合限制外推
FDA突破性疗法通道|Breakthrough Therapy Designation|US FDA, Food and Drug Administration Safety and Innovation Act (2012)|早期显著信号能否在小样本下可靠加速|加速通道伴随确证试验延期和撤回争议|让严重疾病高潜力疗法获得密集指导|突破性疗法指定通过滚动沟通和开发协同缩短路径，并不降低批准证据法定标准|单臂替代终点和选择性早期结果会夸大效应，上市后确证必须有可执行期限
mRNA疫苗转化平台|mRNA Vaccine Platform|Polack et al., New England Journal of Medicine 383, 2603–2615 (2020), doi:10.1056/NEJMoa2034577|疫情速度能否归因于新平台而非数十年基础与巨大资源|mRNA扩展到流感、肿瘤和个体化疫苗|可复用递送与制造平台快速更换编码序列|SARS-CoV-2疫苗把核苷修饰、脂质纳米颗粒、序列设计和大规模试验迅速接通|冷链、罕见不良事件、免疫持续性和全球产能说明平台成功仍受系统条件约束
去中心化临床试验|Decentralized Clinical Trials|US FDA, Decentralized Clinical Trials for Drugs, Biological Products, and Devices, final guidance (2024)|远程访问会不会引入数字排斥和测量异质|监管明确远程访视、本地人员与数字技术责任|把部分试验活动移到参与者生活环境|去中心化设计可减少旅行并扩大覆盖，同时用远程同意、传感和本地服务收集数据|设备、网络、家庭支持与本地执行差异会形成新选择偏差，便利不等于代表性
FDA现代化法2.0|FDA Modernization Act 2.0|US Congress, enacted December 2022|允许非动物证据是否意味着可直接取消动物研究|类器官、芯片和计算模型进入具体适用场景验证|把监管可接受方法从动物试验扩展到替代模型|法律修订允许在适当情况下使用细胞、器官芯片和计算等非临床方法支持开发|法律许可不是科学验证，每种方法仍须证明与具体毒性或药代问题相适配
转化科学七项原则|Translational Science Principles|NCATS, Translational Science Principles, updated July 2025|广义原则能否改变资助、晋升和停项决策|NCATS将未满足需求、通用方案、团队、效率、伙伴与严谨并列|把跨管线共性瓶颈转成可复用方法|七项原则强调未满足需求、可推广方案、跨学科团队、效率、跨界伙伴和严谨研究|如果考核仍只奖励论文、专利和速度，原则无法阻止不可复现路线继续占用资源
里程碑式停项决策|Milestone-Based Translation|NCATS project management and translational science case studies (2022–2025)|快速停项是否会错杀高风险长周期机制|转化管理开始预注册go或no-go与失败学习|用事先阈值把资源从低价值路线释放|里程碑管理要求在关键证据到来前写明继续、转向和停止条件，减少沉没成本驱动|阈值若只偏好短期可测成果，会系统淘汰慢变量、罕见病和基础机制
患者共同设计转化|Patient-Engaged Translation|PCORI and NCATS patient-focused therapy development resources (2018–2025)|参与是否拥有决策权而非只被咨询|患者进入终点、负担、风险和实施设计|把生活经验前置到研究问题和成功定义|患者与社区共同选择终点可暴露实验室忽略的功能、负担与可及性问题，提高方案相关性|代表由谁选、意见如何改变预算若不透明，参与会退化为象征性背书
转化生态系统责任链|Translational Ecosystem Accountability|NCATS Strategic Plan 2025–2030|单项目速度能否代表整个生态系统对健康的贡献|战略转向跨阶段指标、数据共享和公共健康影响|按从发现到实施的完整证据链评价创新|生态视角要求科研、运营、监管、制造、支付和社区共享里程碑与失败学习|宏观影响难归因，若用宽泛社会收益为每个项目辩护，就失去可反驳停项边界
""",
)


add(
    557, "learning-health-systems-implementation-science", "学习型医疗系统与实施科学", "实施科学 · 医疗系统",
    "从RE-AIM、CFIR与学习型医疗愿景到嵌入式试验、CFIR 2.0、去实施和算法漂移，审计数据到实践的闭环。",
    "医疗系统积累数据并不等于会学习；只有反馈改变工作流、结局被重新测量、伤害能迫使系统撤回时，循环才闭合。本面板把有效性、采用、实施、维持和公平分开记账。",
    "学习型医疗的决定性机制是把日常数据转成可检验改变，再把结果与失败持续回写实践，而不是电子病历或仪表板数量增加",
    "未来五年要看嵌入式随机试验、实施结果和算法监测能否共享基础设施，并让患者、基层团队和代表不足机构拥有改变规则的权力",
    [
        "Institute of Medicine, The Learning Healthcare System: Workshop Summary (2007).",
        "Damschroder et al., Fostering implementation through CFIR, Implementation Science 4, 50 (2009).",
        "Damschroder et al., The updated CFIR based on user feedback, Implementation Science 17, 75 (2022).",
        "Proctor et al., Outcomes for implementation research, Administration and Policy in Mental Health 38, 65–76 (2011).",
    ],
    r"""
RE-AIM实施评价|RE-AIM|Glasgow et al., American Journal of Public Health 89, 1322–1327 (1999)|平均有效性会不会掩盖覆盖、采用和维持失败|RE-AIM持续用于数字健康、政策和公平评价|把覆盖有效采用实施维持并列|RE-AIM要求同时报告谁被触达、效果、机构采用、执行一致和长期维持，改变只看试验疗效的习惯|五维可被任意加权，资料缺失时综合叙事仍可能选择性报喜
学习型医疗系统愿景|Learning Healthcare System|Institute of Medicine, The Learning Healthcare System workshop summary (2007)|常规照护数据能否快速产生可靠证据|数字基础设施扩展但组织学习仍是瓶颈|让每次照护同时贡献下一次改进|愿景把科学、信息学、激励和文化接成持续学习系统，使研究与实践不再完全分离|病历数据受选择和工作流影响，没有实验设计的快速循环可能快速传播错误
CFIR综合实施框架|CFIR|Damschroder et al., Implementation Science 4, 50 (2009), doi:10.1186/1748-5908-4-50|多构念框架能否生成可检验机制而非事后分类|2022年更新版重组领域并加入平等中心文化|用干预内外环境个体过程解释实施|CFIR整合多种理论，提供干预、外部、内部、个体和过程构念以系统诊断实施障碍|研究者可在结果出现后挑构念解释一切，必须事前指定机制和比较
常态化过程理论|Normalization Process Theory|May & Finch, Sociology 43, 535–554 (2009), doi:10.1177/0038038509103208|创新嵌入日常是否只取决于个人接受|NPT用于远程医疗、协作照护与数字工具|用意义参与行动监测解释工作如何常态化|NPT关注团队如何理解新实践、投入关系工作、执行并反思，使实施对象从态度转到集体劳动|理论可能低估权力、资源和政策冲击，稳定常态也可能固化低价值照护
实施结果分类|Implementation Outcomes|Proctor et al., Administration and Policy in Mental Health 38, 65–76 (2011), doi:10.1007/s10488-010-0319-7|可接受与可行是否能替代患者健康结局|接受、采用、适切、成本、忠实、渗透和维持已成共同语言|把实施成功与服务和临床结果区分|分类明确实施结果是创新进入系统的近端指标，帮助定位疗效为何没有兑现|实施顺利的无效干预仍是失败，近端指标不能被写成最终健康收益
ERIC实施策略目录|ERIC|Powell et al., Implementation Science 10, 21 (2015), doi:10.1186/s13012-015-0209-1|策略命名一致能否说明何时对谁有效|机制映射和情境匹配成为后续重点|用共识整理七十三种实施策略|ERIC把培训、审计反馈、促进、联盟和激励等策略形成标准词汇，便于比较研究|策略名称粒度不一，未报告剂量、执行者和机制时同名策略不可复制
PRECIS-2实用性试验轮|PRECIS-2|Loudon et al., BMJ 350, h2147 (2015), doi:10.1136/bmj.h2147|试验更贴近日常是否会牺牲内部因果识别|实用性与解释性被视为多维设计选择|用九个维度审查试验与常规实践距离|PRECIS-2让资格、招募、场所、组织、依从、随访、终点和分析的实用程度可视化|团队自评可能把方便设计误写成实用，代表性和数据质量仍需独立测量
阶梯楔形整群试验|Stepped-Wedge Trial|Hemming et al., BMJ 350, h391 (2015), doi:10.1136/bmj.h391|所有集群最终获得干预是否足以消除时间混杂|设计用于政策与系统分阶段实施但方法要求提高|利用分批上线估计系统干预效应|阶梯楔形让各集群按随机顺序从对照转干预，适合无法同步铺开的组织改变|时间趋势、学习扩散和集群数少会严重偏倚，伦理吸引力不能替代统计可识别
NIH医疗系统研究协作网|NIH Collaboratory|NIH Pragmatic Trials Collaboratory, launched 2012|嵌入试验能否在不打断照护时保持同意和数据质量|多项示范项目形成电子表型与监管知识|在医疗系统内运行大规模实用随机试验|Collaboratory把研究者与医疗系统连接，共享分布式数据、电子病历和整群随机经验|系统伙伴多为资源丰富机构，成功基础设施不代表小型和安全网医院可复制
PCORnet分布式研究网络|PCORnet|Fleurence et al., Journal of the American Medical Informatics Association 21, 578–582 (2014)|共同数据模型能否抹平机构语义和缺失差异|网络支持患者中心比较效果与快速查询|数据留在节点而用共同模型协作分析|PCORnet连接临床研究网络与患者网络，降低跨机构队列和试验启动成本|字段同名不等于生成过程相同，本地映射错误可在分布式分析中不可见
电子病历脓毒症预警试验|Sepsis Alert Trial|Adams et al., Nature Medicine 28, 1455–1460 (2022), doi:10.1038/s41591-022-01894-0|预警模型性能能否在临床采用后改善结局|真实部署评价显示实施响应决定模型效用|把算法警报与临床确认和治疗时间相连|多中心实施研究显示在医师及时评估警报的患者中结局较好，突出人机流程|响应不是随机，较易识别患者更可能被及时确认，不能把关联全归给模型
更新版CFIR 2.0|Updated CFIR|Damschroder et al., Implementation Science 17, 75 (2022), doi:10.1186/s13012-022-01245-0|用户反馈更新能否提高构念可操作性|新版调整术语、角色、过程并强化受众视角|让创新提供者接受者与情境关系更清楚|CFIR 2.0基于广泛用户反馈重构领域，加入关键事件、本地条件和角色细分|构念更多不自动提升预测，跨案例需一致编码并公开否定证据
CFIR结果附录|CFIR Outcomes Addendum|Damschroder et al., Implementation Science 17, 7 (2022), doi:10.1186/s13012-021-01181-5|决定因素框架能否与明确结果和机制对接|结果附录区分实施与创新结果及预期性|把情境因素与可测结果的方向相连|附录尝试避免只描述障碍，要求说明构念如何影响实施或创新结果|若分析仍是横断面访谈，机制方向与时间顺序无法仅靠框架确认
去实施低价值照护|De-Implementation|Norton & Chambers, Implementation Science 15, 2 (2020), doi:10.1186/s13012-019-0968-9|停止既有实践是否只是实施的镜像过程|低价值检测、药物和程序撤除成为独立研究线|识别并撤回无效有害或低价值实践|去实施研究强调习惯、专业身份、收入和患者预期使停止比采用更复杂|费用下降不等于伤害减少，若替代服务不可及，撤除会把负担转给患者
审计与反馈效果|Audit and Feedback|Ivers et al., Cochrane Database of Systematic Reviews, updated 2012–2024|绩效反馈何时改变行为而非制造报表|多层、可行动和可信比较者提高效果|把实际绩效与目标差距返回执行者|系统综述显示审计反馈通常有小到中等改进，基线差、重复和明确行动计划时更强|效果高度异质，指标博弈和记录负担会令报告改善而真实照护不变
实施公平框架|Health Equity Implementation|Woodward et al., Implementation Science 14, 83 (2019)|普遍实施会不会在资源不同机构扩大差距|公平开始嵌入实施决定、策略和结果|把谁受益谁承担负担作为实施变量|公平视角要求按人群和机构资源拆分覆盖、采用、忠实与结局，而非只在结尾做亚组|小样本和敏感身份数据缺失会让最受影响群体再次不可见
算法漂移监测|Clinical Algorithm Drift|Davis et al., Journal of the American Medical Informatics Association and related monitoring studies (2017–2024)|部署前外部验证能否代表流程变化后的未来|监测转向数据、性能、校准和行动四层漂移|持续比较模型输出与后续真实结局|漂移监测把患病率、输入编码、模型校准和医师响应分开，允许触发复评或停用|结局延迟和干预回写会改变标签，警报阈值过多又会制造监测疲劳
患者报告结局回写|Patient-Reported Outcomes in LHS|Basch et al., JAMA 318, 197–198 (2017) and follow-up trials|症状自报能否在工作流中被及时处理|电子患者报告结局进入肿瘤和慢病常规照护|让患者体验成为连续反馈而非末端问卷|随机研究显示系统收集症状并向团队报警可改善生活质量并减少急诊，证明反馈可改变照护|数字接入、语言和团队响应能力不均会使自报系统偏向资源充足患者
学习型系统成熟度|Learning Health System Maturity|AHRQ and Learning Health Systems journal frameworks, 2023–2025|成熟度自评能否对应实际学习速度与健康收益|组织开始评价数据、科学、文化、治理和公平能力|用可观察能力审查学习循环是否闭合|成熟度框架把数据基础设施与领导、患者参与、实验和实施并列，阻止把IT升级等同学习|组织可通过文件证明流程存在，却未必有撤回失败实践的权力和记录
实施机制的可迁移性|Mechanism-Focused Implementation|Lewis et al., Implementation Science agenda, 2018–2025|同一策略的机制能否跨情境保持方向|研究从策略清单转向作用机制和情境调节|说明策略通过何种近端变化影响结果|机制研究要求把策略、目标、近端决定因素和结果连成因果链，便于跨场景累积知识|复杂系统中多策略同时变化，若无时序和对照，机制图仍可能只是合理故事
""",
)


add(
    558, "digital-biomarkers-wearable-health", "数字生物标志物与可穿戴健康", "数字健康 · 可穿戴测量",
    "从手机数字表型、mPower与Apple Heart Study到V3验证、肤色偏差、Fitbit房颤和无袖带血压，审计连续健康数据。",
    "手腕和手机每天产生海量读数，但数字生物标志物必须先证明设备测得对、算法算得对、而且结果与目标临床状态有关。本面板把传感器流、测量指标、风险提示和临床终点逐层拆开。",
    "数字标志物的决定性机制是让连续传感读数经过验证、分析验证和临床验证后对应明确用途，而不是采样频率或用户规模增加",
    "未来五年要看无感测量能否跨肤色、年龄、设备版本和生活情境保持校准，并把缺戴、漂移、误报与临床响应成本纳入统一分母",
    [
        "Onnela & Rauch, Harnessing Smartphone-Based Digital Phenotyping, Neuropsychopharmacology 41, 1691–1696 (2016).",
        "Perez et al., Large-Scale Assessment of a Smartwatch to Identify Atrial Fibrillation, New England Journal of Medicine 381, 1909–1917 (2019).",
        "Goldsack et al., Verification, analytical validation, and clinical validation (V3), npj Digital Medicine 3, 55 (2020).",
        "US FDA, Digital Health Technologies for Remote Data Acquisition in Clinical Investigations, final guidance (2023).",
    ],
    r"""
mPower帕金森手机研究|mPower|Bot et al., Scientific Data 3, 160011 (2016), doi:10.1038/sdata.2016.11|自愿手机任务能否代表疾病严重度和广泛患者|开放数据推动步态语音和触屏数字指标研究|用手机任务与被动传感远程量化症状|mPower让参与者在家完成步行、平衡、语音和点击任务，快速形成大规模开放数据|智能手机拥有、坚持使用和自报诊断产生强选择偏差，任务表现也受环境影响
智能手机数字表型|Digital Phenotyping|Onnela & Rauch, Neuropsychopharmacology 41, 1691–1696 (2016), doi:10.1038/npp.2016.7|位置通信和活动代理能否合法推断心理状态|数字表型进入精神健康研究并引发隐私治理|以个人设备连续捕捉行为表型|概念把手机的主动问卷和被动传感结合，试图描述个体在自然环境的行为动态|同一轨迹可有多种社会含义，未经情境和同意的推断会把代理指标变成监控
可穿戴癫痫监测器|Wearable Seizure Monitor|US FDA clearance of Empatica Embrace2 (2018)|腕部电活动和运动能否覆盖非惊厥发作|穿戴报警用于特定强直阵挛发作而非所有癫痫|用多传感腕带识别可能的惊厥发作|监管许可展示可穿戴设备可针对明确发作类型提供照护者提示|适用范围窄且误报受运动影响，报警不是诊断也不能保证发现每次发作
连续血糖与个体糖型|Continuous Glucose Phenotypes|Hall et al., PLoS Biology 16, e2005143 (2018), doi:10.1371/journal.pbio.2005143|传感波动阈值能否稳定定义代谢亚型|消费级CGM快速扩张但临床用途仍分人群|把间歇采血变成全天餐后轨迹|研究用连续血糖揭示个体对食物反应和波动差异，推动个体化营养假设|组织液滞后、校准和短期行为改变会影响轨迹，未患糖尿病者的阈值临床意义有限
Apple Heart Study|Apple Heart Study|Perez et al., New England Journal of Medicine 381, 1909–1917 (2019), doi:10.1056/NEJMoa1901183|超大虚拟研究能否克服自选参与和验证回收偏差|约四十二万人研究成为消费穿戴临床评价范例|以光电容积脉搏不规则提示筛查房颤|研究远程招募四十一万九千余人，少数收到提示并以心电贴片确认，展示大规模无场地研究|只有提示者进入主要确认链且贴片回收有限，阳性预测值不能写成总体敏感度
可穿戴新冠前症状信号|Wearables for Presymptomatic COVID-19|Mishra et al., Nature Biomedical Engineering 4, 1208–1220 (2020), doi:10.1038/s41551-020-00640-6|静息心率偏离能否区分感染与压力睡眠等因素|可穿戴异常检测扩展到传染病与恢复监测|用个人基线而非群体阈值检测异常|研究在部分感染者症状前发现心率、活动和睡眠偏离，展示个体内连续基线价值|回顾性窗口和确诊时间不确定会夸大提前量，异常缺乏病原特异性
V3验证框架|V3 Framework|Goldsack et al., npj Digital Medicine 3, 55 (2020), doi:10.1038/s41746-020-0260-4|统一词汇能否阻止未经临床验证的传感指标上市|V3成为生物计量监测技术适用性基础|分开验证设备、算法和临床关系|框架区分验证传感器性能、分析验证算法输出、临床验证与健康状态关系，明确每层证据|三层通过仍需特定使用情境的可用性和净收益，不能把相关性当治疗效果
肤色与光学传感偏差|Optical Sensor Skin-Tone Bias|Bent et al., npj Digital Medicine 3, 117 (2020), doi:10.1038/s41746-020-00302-6|消费设备误差是否在人群平均中掩盖肤色差异|多肤色校准与公开亚组性能成为评价要求|按皮肤色素和设备拆分心率误差|研究比较多种穿戴设备，发现不同活动和肤色条件下误差差异，暴露光学测量公平问题|小样本和肤色量表粗糙限制结论，但不报告亚组会更系统地隐藏风险
无接触睡眠与呼吸监测|Contactless Sleep Sensing|Radar and ballistocardiography validation studies, 2017–2022|非接触便利能否替代多导睡眠金标准|毫米波与床旁传感进入家庭睡眠评估|从身体微动推断呼吸心率和睡眠阶段|非接触传感减少佩戴负担并能长周期记录夜间生理变化|同床者、床垫、体位和睡眠障碍类型改变信号，算法分期不能直接替代临床诊断
Fitbit房颤大规模研究|Fitbit Heart Study|Lubitz et al., Circulation 146, 1415–1424 (2022), doi:10.1161/CIRCULATIONAHA.122.060291|仅在静止时检测能否兼顾精度和覆盖|约四十五万五千人研究验证可扩展房颤提示|以连续多脉搏窗口提高不规则节律特异性|研究在大型消费设备人群中触发远程心电贴片确认，检验算法阳性预测|静止窗口排除运动信号也漏掉部分发作，拥有设备的人群不能代表筛查目标人群
可穿戴步态数字终点|Wearable Gait Endpoints|Mobilise-D and Critical Path Institute validation programs, 2019–2025|真实世界步行速度能否与疾病功能和治疗变化对应|监管资格审查推动帕金森、多发硬化等终点标准化|在生活环境连续量化步态表现|多中心项目统一设备、算法和临床验证，尝试把日常步态转成试验终点|设备佩戴位置、助行器和环境决定信号，日常活动减少可能源于社会因素而非疾病
声音数字生物标志物|Voice Biomarkers|Low et al., review and prospective voice studies in npj Digital Medicine (2020–2024)|语音特征能否跨语言设备和情绪保持疾病特异|开放语音队列用于帕金森、呼吸和心理健康|从声学与语言特征提取低负担指标|远程语音任务可捕捉发声、呼吸和语言变化，为频繁随访提供廉价信号|麦克风、方言、药物和情境强烈混杂，模型可能识别设备或社会群体
数字测量缺失机制|Wearable Missingness|Dunn et al., JAMIA and wearable adherence studies (2018–2023)|未佩戴是否可当作随机缺失|研究开始把依从本身作为行为与偏差变量|区分无活动与设备未戴和数据未传|穿戴研究显示缺失与年龄、症状、充电和生活规律相关，连续数据的空白本身需要解释|简单插补会把病重停戴或数字排斥者伪造成稳定，进而高估干预效果
数字终点监管指南|DHT Remote Data Guidance|US FDA, Digital Health Technologies for Remote Data Acquisition in Clinical Investigations, final guidance (2023)|设备适用性和版本变化能否在试验中持续控制|指南明确验证、可用性、风险与记录保留|按具体试验用途选择并管理数字技术|FDA要求申办者说明DHT适用性、验证、参与者培训、数据访问和风险，为远程终点设证据门槛|指南不能替每种算法设阈值，固件自动更新仍可能改变试验中途测量
远程患者监测|Remote Patient Monitoring|CMS reimbursement and randomized remote monitoring evidence, 2018–2025|更多家庭读数能否减少住院而不增加警报负担|慢病监测与支付扩张后转向净效益评价|把家庭生理数据接入临床响应流程|远程监测可在心衰、血压和糖尿病中提前发现变化，并减少部分就诊负担|没有分层阈值和响应团队时，数据洪流会增加误报、工作量与数字差距
无袖带血压设备|Cuffless Blood Pressure|European Society of Hypertension recommendations and IEEE 1708 validation work, 2022–2024|脉搏传导或光学模型能否跨姿势和血管状态保持|国际团体要求独立于校准袖带的动态验证|从连续波形估算血压而非间歇充气|无袖带方法有望提供夜间和活动中趋势，扩展传统门诊点测|个体校准会把回归均值误作准确，运动、温度和血管硬度改变映射，尚不能普遍替代袖带诊断
智能戒指睡眠与恢复|Smart Ring Biomarkers|de Zambotti et al., Behavioral Sleep Medicine and validation studies, 2019–2024|消费恢复分数能否对应可解释生理状态|戒指在睡眠、生育与感染研究中扩张|以指端光学温度与运动融合长期轨迹|指端设备佩戴负担较低，可连续估计睡眠、静息心率和温度偏离|私有综合分数随算法版本改变且缺乏可追溯量纲，用户行为会被不可审计评分引导
可穿戴妊娠生理轨迹|Wearables in Pregnancy|Li et al., npj Digital Medicine and prospective pregnancy wearable cohorts (2021–2024)|孕期正常变化能否与并发症早期信号区分|纵向研究开始建立个体孕周基线|用全天心率睡眠温度描述孕期动态|连续穿戴可观察妊娠和产后心率、睡眠与活动的系统变化，为风险预测提供时间坐标|设备用户通常更富裕健康，预警模型若不跨产科人群验证会扩大照护差距
联邦可穿戴分析|Federated Wearable Learning|Federated analytics studies for mobile health, 2020–2025|数据留在设备是否足以保护位置与健康隐私|端侧学习结合安全聚合与差分隐私|在不集中原始轨迹时更新群体模型|联邦方案可减少原始传感数据汇集，并让模型从大量设备迭代|梯度、更新频率和设备参与仍泄漏行为，电量网络差异会让聚合偏向常在线者
数字标志物适用性声明|Context of Use for Digital Measures|Digital Medicine Society and regulatory qualification resources, 2020–2025|同一指标能否在筛查监测和试验终点间自由迁移|数字测量开发转向预先锁定人群用途和决策|把测量对象、场景和行动阈值写成适用性声明|适用性声明迫使开发者说明测什么、为谁、何时、用来做什么以及误差后果|商业产品常用宽泛健康标签回避窄验证边界，跨用途外推会让既有证据失效
""",
)


add(
    559, "digital-mental-health-computational-psychiatry", "数字心理健康与计算精神医学", "心理健康 · 计算精神医学",
    "从RDoC、计算精神病学与手机表型到数字疗法、生成式对话、危机升级和真实世界停用，审计心理健康数字化。",
    "心理健康数字工具最容易把互动频率误写成治疗效果，也最容易在风险最高时暴露无人响应的边界。本面板把机制模型、数字表型、自动干预、临床疗效和危机责任分开。",
    "数字心理健康的决定性机制是把可解释的个体状态估计接到有证据的干预与人工升级，而不是下载量、对话轮次或预测准确率增加",
    "未来五年要看生成式系统能否在自杀、躁狂、精神病性症状和药物问题上可靠拒答并升级，同时以独立长期试验证明效果不随新奇感消失",
    [
        "Insel et al., Research Domain Criteria: Toward a New Classification Framework, American Journal of Psychiatry 167, 748–751 (2010).",
        "Montague et al., Computational psychiatry, Trends in Cognitive Sciences 16, 72–80 (2012).",
        "Huys, Maia & Frank, Computational psychiatry as a bridge, Nature Neuroscience 19, 404–413 (2016).",
        "WHO, Ethics and governance of artificial intelligence for health: guidance on large multi-modal models (2025).",
    ],
    r"""
RDoC研究领域标准|Research Domain Criteria|Insel et al., American Journal of Psychiatry 167, 748–751 (2010), doi:10.1176/appi.ajp.2010.09091379|跨诊断维度能否改善机制研究而不抹去临床叙事|RDoC矩阵扩展发展和环境维度|用行为神经回路和功能维度重组研究|RDoC把负性效价、认知、社会过程等维度跨传统诊断研究，推动机制和量化表型|研究框架不是诊断系统，量表与神经指标若脱离生活痛苦会产生新的还原主义
计算精神病学议程|Computational Psychiatry|Montague et al., Trends in Cognitive Sciences 16, 72–80 (2012), doi:10.1016/j.tics.2011.11.018|模型参数能否对应可重复的心理机制|生成模型和规范模型进入跨诊断研究|用形式模型连接行为计算与神经过程|议程提出以学习、决策和社会互动模型解释症状异质性，并为个体化干预提供参数|不同模型可同样拟合行为，参数可辨识和任务重测信度不足会让机制标签虚假精确
手机抑郁行为信号|Mobile Sensing for Depression|Saeb et al., Journal of Medical Internet Research 17, e175 (2015), doi:10.2196/jmir.4273|位置和手机使用能否区分抑郁与社会经济情境|数字表型研究转向预注册和跨队列验证|用被动手机传感关联症状严重度|小样本研究发现活动范围和地点规律等特征与抑郁量表相关，展示无负担测量可能|样本很小且相关受工作、住区和设备影响，不能从位置轨迹诊断个体
计算模型连接症状与回路|Models as a Bridge|Huys, Maia & Frank, Nature Neuroscience 19, 404–413 (2016), doi:10.1038/nn.4238|任务模型能否跨场景保留临床区分度|层次贝叶斯和纵向任务试图提高可靠性|用机制参数连接行为、神经和症状|综述把计算精神病学定义为规范、机制和数据驱动模型的桥梁，强调可检验预测|实验任务的短暂策略不一定代表日常功能，漂亮模型也可能缺乏治疗可行动性
Woebot认知行为聊天机器人|Woebot|Fitzpatrick et al., JMIR Mental Health 4, e19 (2017), doi:10.2196/mental.7785|两周自报改善能否代表持续临床疗效|心理聊天机器人数量增长并转向更严格比较|用自动对话递送认知行为技巧|一项小型随机试验比较Woebot与信息材料，报告短期抑郁症状改善和较高互动|样本年轻、自选、周期短且无盲法，互动新奇感和期待效应难分离
处方数字疗法reSET|reSET|US FDA authorization of reSET for substance use disorder (2017)|软件获批能否保证患者持续使用和支付可行|处方数字疗法经历扩张、报销困难与企业退出|把认知行为课程和临床管理结合|reSET成为较早获FDA许可的处方数字疗法，要求在临床管理框架中使用|许可基于特定试验和版本，真实世界依从、共病和服务可及性决定净效用
自动化虚拟现实精神病治疗|Automated VR Therapy|Freeman et al., Lancet Psychiatry 5, 625–632 (2018), doi:10.1016/S2215-0366(18)30155-8|虚拟场景内恐惧下降能否迁移到日常社会功能|自动VR扩展到恐高、焦虑和精神病性症状|用分级虚拟暴露和自动教练训练安全学习|随机试验显示自动VR可减少精神病患者对现实场景的回避与痛苦|头显可及、晕动、治疗师支持和现实风险不同，虚拟完成不等于长期社区参与
即时自适应干预|Just-in-Time Adaptive Interventions|Nahum-Shani et al., Annals of Behavioral Medicine 52, 446–462 (2018), doi:10.1007/s12160-016-9830-8|此刻预测的脆弱状态能否可靠决定推送时机|微随机试验用于估计不同情境的近端效应|按实时状态决定是否何时给何种支持|JITAI框架明确决策点、干预选项、脆弱和可接受状态及近端结果，使适应逻辑可检验|频繁提示会疲劳且状态估计出错，短期响应可能损害自主和长期习惯
数字CBT失眠长期试验|Digital CBT for Insomnia|Espie et al., Lancet Psychiatry 6, 281–289 (2019), doi:10.1016/S2215-0366(18)30472-6|睡眠改善能否进一步改善功能与心理健康|全自动CBT-I进入卫生系统与长期随访|以结构化数字课程递送失眠认知行为治疗|大型随机试验显示数字CBT-I改善失眠并带来部分心理健康和功能收益|高流失、自报终点和自选互联网样本会高估普遍效果，严重共病仍需临床评估
社交媒体自杀风险预测|Social-Media Suicide Prediction|Coppersmith et al., Biomedical Informatics Insights and later studies (2018–2021)|公开文本风险信号是否授权平台替用户判断和干预|伦理研究强调同意、误报和危机转介|从语言和行为变化估计自伤风险|计算研究显示社交媒体文本可与自杀意念或心理症状相关，为早期支持提出可能|标签来源、语境和基率使个体误报很高，秘密监测可能伤害信任并触发执法风险
数字疗法真实世界崩塌|Digital Therapeutics Market Failure|Pear Therapeutics bankruptcy filings and product discontinuity (2023)|临床证据能否脱离商业持续性和服务基础设施|行业转向支付证据、互操作与退出计划|把企业存续和数据迁移纳入治疗连续性|处方数字疗法先驱破产显示监管许可、临床试验和市场采用之间存在断裂|患者访问、数据与医生工作流随企业退出中断，疗效评价必须包含产品生命周期
在线危机干预升级|Crisis Escalation in Digital Care|988 Lifeline and digital mental health safety protocols, 2022–2025|自动风险分类能否在分钟级把人交给合适服务|平台开始公开危机检测、人工复核与地区资源边界|让高风险对话触发人工和紧急支持|结构化升级协议可把自杀意念、暴力和急性精神病性症状从自助工具移交专业人员|地理定位、语言、服务容量和误报决定实际响应，显示热线并不等于完成救助
LLM与医生回答比较|LLM Empathy Study|Ayers et al., JAMA Internal Medicine 183, 589–596 (2023), doi:10.1001/jamainternmed.2023.1838|盲评网络回答偏好能否代表临床安全和关系|生成式健康对话研究转向真实工作流与伤害审计|语言模型生成被评为更完整和富同理心的回答|研究让专业人员比较公开问答中的医生与聊天机器人回复，后者常获较高质量和同理评分|医生原回复受平台时间限制，评审看不到行动后果；好听回答仍可能事实错误
心理健康应用隐私执法|Mental-Health App Privacy|US FTC, BetterHelp prohibited from sharing health data for advertising (2023)|隐私声明能否约束广告和分析生态的数据流|监管开始把心理信息的二次使用视为伤害|以执法把敏感心理数据用途限制落地|FTC行动指控平台在承诺隐私后仍向广告商披露敏感信息，并要求赔偿与删除|一次和解不能消除第三方SDK和跨境处理，用户同意也常无法理解推断数据
生成式AI心理健康治理|Generative AI for Mental Health|WHO guidance on large multi-modal models, 2024–2025|通用模型能否在危机与妄想内容中可靠保持边界|WHO提出四十余项面向政府开发者和医疗方建议|按用途、风险和责任治理生成式对话|WHO指南要求透明、人类监督、审计和利益相关者参与，覆盖患者自用和临床应用|建议不是疗效证据，通用模型更新频繁且可能迎合用户，必须独立红队和停用
强化学习精神病学|Reinforcement-Learning Psychiatry|Mkrtchian et al., computational psychiatry studies of learning and mood (2017–2024)|奖励学习参数差异是否稳定映射诊断和治疗反应|跨任务层次模型与纵向采样尝试提高信度|把学习率预测误差和探索写成症状机制|强化学习模型可分解患者在奖励和惩罚学习中的行为差异，形成机制假设|参数高度依赖任务、先验和药物状态，同一诊断内异质性会超过组间差异
NICE数字健康证据标准|Digital Health Evidence Standards|NICE, Evidence Standards Framework for Digital Health Technologies, updated 2022|风险分层证据要求能否跟上自适应和生成式产品|框架按功能与风险匹配有效性和经济证据|让数字工具不再以同一低门槛进入采购|NICE框架区分系统服务、沟通、自我管理、治疗和诊断等层级并列出证据标准|厂商自报功能分类可能下调要求，算法更新后旧证据也会过期
数字表型可重复性|Digital Phenotyping Reproducibility|Onnela Lab and multi-cohort benchmark studies, 2020–2025|同名手机特征能否跨操作系统城市和生活阶段复现|研究转向原始数据标准、个体基线和开放代码|检验被动行为特征的跨队列稳定性|多队列比较显示活动、睡眠和社交代理可提供纵向信号，也揭示平台实现差异|位置熵、屏幕时间等同名指标的采样规则不同，跨研究合并前必须重算
WHO引导式心理聊天机器人试验|WHO Guided Chatbot|Bryant et al., randomized clinical trial of a guided chatbot intervention in Jordan (2026)|低资源环境短期改善能否跨语言危机和长期服务维持|结构化引导聊天被研究为可扩展心理支持|把循证练习与人工支持边界编码进对话|随机试验报告引导式聊天干预改善困扰、功能和福祉，显示非开放生成路线可扩展|受试者支持、文化适配和随访长度限定结论，不能外推为通用AI治疗师
真实世界停用与伤害登记|Digital Mental Health Post-Market Registry|Regulatory and health-system safety proposals, 2024–2026|试验后是否有人记录恶化、依赖和错误升级|研究倡议建立版本、停用原因与不良事件共同登记|把数字产品的退出和伤害作为临床结局|持续登记可连接版本、使用模式、症状变化、危机升级和停用原因，补足短试验|伤害定义和企业报告激励不一致，患者退出后往往最难随访却最重要
""",
)


add(
    560, "one-health", "同一健康One Health", "公共卫生 · 同一健康",
    "从曼哈顿原则、跨物种溢出与Tripartite合作到OHHLEP定义、H5N1奶牛传播和全球大流行协定，审计人—动物—环境接口。",
    "同一健康不是把三个部门放进同一会议，而是要求同一病原、抗性基因或生态扰动在人体、动物与环境之间共享监测和决策。本面板逐项检查接口是否真的闭合。",
    "One Health的决定性机制是跨人类、动物与生态系统共享因果模型、监测和联合行动，而不是参与部门或会议数量增加",
    "未来五年要看联合风险评估、环境维度和地方财政能否常态化，并让H5N1、AMR和溢出预防的早期信号在危机前触发共同措施",
    [
        "Wildlife Conservation Society, The Manhattan Principles on One World, One Health (2004).",
        "OHHLEP et al., One Health: A new definition for a sustainable and healthy future, PLoS Pathogens 18, e1010537 (2022).",
        "FAO, UNEP, WHO & WOAH, One Health Joint Plan of Action 2022–2026.",
        "WHO, One Health fact sheet, updated May 2026.",
    ],
    r"""
曼哈顿十二项原则|Manhattan Principles|Wildlife Conservation Society, One World One Health symposium (2004)|野生动物保护议程能否进入卫生和农业实际预算|柏林原则在2019年更新气候与公平维度|把人类动物生态健康视为同一系统|十二项原则在跨学科框架下连接生态完整性、传染病与社会健康，成为现代One Health标志|原则缺少执行权和稳定财政，危机后部门仍可能回到各自法定边界
尼帕病毒生态溢出|Nipah Virus Ecology|Epstein et al., Proceedings of the National Academy of Sciences 103, 7142–7147 (2006)|果蝠宿主发现能否直接指出可干预传播链|土地利用、养殖和食物接触研究细化溢出路径|联合宿主生态与人类接触解释暴发|研究确认孟加拉果蝠与尼帕暴露关系，后续工作连接椰枣汁和人际传播|只把蝙蝠视作危险会诱发扑杀并破坏生态，真正干预点在具体接触界面
Tripartite跨机构合作|FAO-OIE-WHO Tripartite|FAO, OIE and WHO, Tripartite Concept Note (2010)|全球机构合作能否穿透国家部门和地方执行|UNEP加入后形成Quadripartite|把动物卫生食品农业与人类卫生正式协同|概念说明三机构在流感、狂犬病和抗菌药耐药等接口共享责任与技术支持|国家预算、数据法和实验室体系仍分割，全球备忘录不等于地方联合响应
环境抗菌药耐药|Environmental AMR|Berendonk et al., Nature Reviews Microbiology 13, 310–317 (2015), doi:10.1038/nrmicro3439|环境耐药基因是否只是临床使用的下游污染|全球行动逐步纳入污水、制药和农业源|把环境作为耐药选择与传播库|研究综述显示废水、土壤和水体可承载抗生素、耐药菌与基因交换，扩展临床治理边界|环境检出基因不自动等于人体感染风险，需连接暴露剂量和传播链
病原溢出路径模型|Pathogen Spillover|Plowright et al., Nature Reviews Microbiology 15, 502–510 (2017), doi:10.1038/nrmicro.2017.45|发现野生宿主是否足以预测下一次大流行|研究转向宿主压力、病原释放、接触和受体易感的串联|把溢出拆成连续必要屏障|框架把宿主分布、感染、病原释放、环境存活、人类暴露和易感串成可干预路径|每段数据稀缺且相乘，热点地图若省略行为与卫生系统会产生虚假确定
IPBES大流行时代报告|IPBES Pandemics Workshop|IPBES, Workshop Report on Biodiversity and Pandemics (2020)|把土地利用归因溢出能否形成可执行预防政策|全球讨论从疫情响应转向上游预防|连接生物多样性丧失、贸易和病原出现|报告综合证据指出土地利用变化、农业扩张和野生动物利用提高人兽接触并驱动新发病|全球驱动到单次暴发因果链难量化，政策不能用抽象风险替代地方生计方案
柏林One Health原则|Berlin Principles|Gruetzmacher et al., Science of the Total Environment 764, 142919 (2021), doi:10.1016/j.scitotenv.2020.142919|更新原则能否把气候和社会不平等真正纳入|十项原则强调制度、投资、原住民知识与生态完整|把全球环境变化前置于疾病应对|柏林原则在曼哈顿框架上加入气候、生物多样性、消费与公平，要求跨尺度行动|范围扩大容易稀释优先级，若没有指标和权责，所有议题都重要等于无人负责
SARS-CoV-2水貂传播|Mink SARS-CoV-2|Hammer et al., Emerging Infectious Diseases 27, 547–551 (2021), doi:10.3201/eid2702.203794|养殖动物监测能否在大规模传播前触发行动|多国建立动物SARS-CoV-2监测和生物安全|识别人—水貂—人的双向传播|丹麦水貂暴发显示高密度养殖可形成病毒扩增和变异环境，并发生回传人类|大规模扑杀的福利、生计和证据阈值争议说明单一卫生目标不足
白尾鹿病毒库|SARS-CoV-2 in White-Tailed Deer|Hale et al., Nature 602, 481–486 (2022), doi:10.1038/s41586-021-04353-x|野生动物高血清阳性是否意味着持续反向威胁|基因组监测显示鹿群独立传播谱系|把大流行监测扩展到常见野生哺乳动物|研究在美国白尾鹿发现广泛感染证据，说明人类病原可建立新动物传播链|采样地区和狩猎样本有偏，动物感染不自动等于高概率回传或高致病
OHHLEP统一定义|OHHLEP One Health Definition|Adisasmito et al., PLoS Pathogens 18, e1010537 (2022), doi:10.1371/journal.ppat.1010537|统一定义能否改变环境长期被边缘化|定义被Quadripartite和多国框架采用|平衡优化人类动物植物和生态系统健康|专家组把One Health定义为综合统一方法，强调系统间紧密联系和可持续平衡|共识语言无法解决利益冲突，例如农业产量、生态保护与短期防疫的权衡
One Health联合行动计划|One Health Joint Plan of Action|FAO, UNEP, WHO & WOAH, One Health Joint Plan of Action 2022–2026|六条行动轨能否获得国家层面共同预算|实施指南和地区工作坊推进本地化|把能力、溢出、地方病、食品、AMR和环境列入一套计划|四机构列出六条行动轨和跨部门协作框架，为国家评估和实施提供共同路线|计划到2026年的成果受自愿采纳与数据能力限制，中央协调强不代表地方可执行
狂犬病Zero by 30|Zero by 30|WHO, FAO, WOAH and GARC, Global Strategic Plan to end human deaths from dog-mediated rabies by 2030 (2018)|人用暴露后预防能否替代犬群免疫和流浪犬治理|大规模犬疫苗与可及PEP仍是消除双支柱|以犬群源头控制联动人类救治|计划把犬接种、病例监测、人用疫苗和社区教育接成消除路径，体现One Health可操作性|犬群覆盖不足、疫苗断供和跨境流动会使单年活动无法维持传播阻断
GLASS抗菌药耐药监测|Global AMR Surveillance|WHO GLASS reports, expanded One Health modules 2015–2025|人类实验室数据能否代表动物、食品和环境耐药链|监测逐步连接抗菌药使用和多部门数据|用标准化病原药敏数据比较趋势|GLASS建立国家AMR和使用数据报告框架，提高跨国可见性并支持行动计划|检测能力和送检模式差异很大，报告比例不能直接排名国家风险
联合风险评估工具|Joint Risk Assessment Tool|FAO, WHO and WOAH, Joint Risk Assessment Operational Tool, updated 2025|多部门共同打分能否转成及时共同决策|工具被用于人兽界面事件和能力建设|围绕同一危害共享信息与不确定度|JRA工具规定问题、团队、证据、风险表征与管理选项，使部门不再各出一份结论|数据共享权、主持权和行动预算若未解决，联合评估会停在会议报告
废水病原监测|Wastewater Surveillance|WHO and national SARS-CoV-2 wastewater surveillance guidance, 2020–2024|环境信号能否公平代表无下水系统和流动人口|废水平台扩展到流感脊灰和AMR|用群体排泄信号提供无个体检测早期趋势|疫情中废水RNA可在病例报告前显示社区变化，并避免依赖个人就医|降雨、工业排放、采样点和污水接入率改变分母，浓度不能直接换算感染人数
H5N1奶牛传播|H5N1 in Dairy Cattle|USDA, CDC and genomic investigations of H5N1 dairy cattle outbreaks (2024)|禽源病毒进入奶牛后是否形成新的哺乳动物适应通道|跨州奶牛传播与散发人感染推动联合监测|用动物临床、牛奶、基因组和职业暴露拼接传播|2024年美国奶牛群暴发显示H5N1跨物种并随牛只流动扩散，原奶成为高信号样本|牧场进入、工人检测与野生动物样本不足，使传播起点和真实人群风险仍有空白
One Health经济论证|Economics of One Health|World Bank, People, Pathogens and Our Planet reports and pandemic prevention estimates|预防投资回报能否在部门间被谁支付谁受益所阻断|疫情后融资讨论强调上游预防和共同收益|把跨部门成本与避免损失放进同一账户|经济分析显示监测、兽医、卫生和环境协作相对大流行损失成本较低，为预防提供财政理由|避免的灾难不可见且收益跨部门，模型假设容易被用来高估单一项目回报
食品链One Health|Food Safety One Health|FAO and WHO food safety strategies, 2022–2030|从农场到餐桌标准能否覆盖非正规市场和小农|全基因组溯源连接人类病例食品与动物来源|沿食品链共享病原与耐药证据|整合监测可把沙门氏菌、弯曲杆菌和耐药株从患者追到食品和养殖环节|检测和贸易执法可能把成本不成比例转给小生产者，风险治理需公平支持
气候驱动媒介病|Climate-Sensitive Vector Disease|WHO, Global Vector Control Response 2017–2030 and climate-health assessments|气候适宜性模型能否预测实际暴发|媒介监测与气候服务开始联动|连接温度降雨生态与人群易感|One Health视角把蚊媒生态、动物宿主、城市积水和医疗能力共同纳入预警|气候相关不是单因，人口流动、免疫和控制措施可令模型方向反转
WHO大流行协定中的One Health|WHO Pandemic Agreement|World Health Assembly, WHO Pandemic Agreement adopted 2025|全球协定能否把溢出预防与主权、融资和公平落实|协定实施与病原获取惠益分享机制继续谈判|把预防准备响应和公平写入共同规则|协定把One Health等预防原则与卫生系统、研发和公平获取纳入全球框架|文本通过不等于执行，监测义务、资源转移和环境行动仍需可核验安排
""",
)


add(
    561, "planetary-health", "行星健康", "地球系统 · 行星健康",
    "从行星边界与人类世健康委员会到污染负担、六重边界越界、气候健康倒计时和年度行星体检，审计健康的地球系统底座。",
    "行星健康主张人的健康不是环境政策的附属受益，而是嵌在气候、生物多样性、土地、水和生物地球化学循环之中。本面板拒绝只列风险，要求每个地球系统变化都连接暴露、健康结局与社会分配。",
    "行星健康的决定性机制是把人类健康置于有阈值、有反馈的地球系统约束内核算，而不是环境指标或健康指标各自增加",
    "未来五年要看边界越界能否连接到区域健康决策、原住民治理和公平转型，并让健康收益成为能源、食物、城市与自然恢复的共同绩效",
    [
        "Whitmee et al., Safeguarding human health in the Anthropocene epoch, The Lancet 386, 1973–2028 (2015).",
        "Steffen et al., Planetary boundaries: Guiding human development, Science 347, 1259855 (2015).",
        "Richardson et al., Earth beyond six of nine planetary boundaries, Science Advances 9, eadh2458 (2023).",
        "The Lancet Countdown, annual report on health and climate change, 2024–2025.",
    ],
    r"""
行星边界更新|Planetary Boundaries 2015|Steffen et al., Science 347, 1259855 (2015), doi:10.1126/science.1259855|全球控制变量能否直接指导区域健康决策|2023年更新显示九项中六项越界|用安全运行空间表达地球系统阈值|框架更新气候、生物圈、土地和生物地球化学循环等边界，强调跨阈值的非线性风险|全球边界不是单个国家配额，控制变量与具体疾病间还需区域暴露链
人类世健康委员会|Planetary Health Commission|Whitmee et al., The Lancet 386, 1973–2028 (2015), doi:10.1016/S0140-6736(15)60901-1|人类健康进步是否靠透支未来生态系统取得|行星健康形成研究、教育和政策网络|把健康文明与自然系统状态放在同一命题|委员会指出过去健康收益伴随环境退化，定义行星健康为人类文明及其自然系统的健康|概念范围极广，若没有因果路径和责任主体会成为所有可持续议题的同义词
大加速|Great Acceleration|Steffen et al., Anthropocene Review 2, 81–98 (2015), doi:10.1177/2053019614564785|全球平均曲线会不会掩盖消费责任和健康不平等|社会经济与地球系统指标继续按地区和收入拆分|把二战后人类活动与地球变化同步呈现|大加速曲线显示能源、肥料、城市化等与温室气体、生态和水变化同期陡升|同期上升不证明每条因果，全球总量还会把高消费群体责任平均给所有人
行星健康教育框架|Planetary Health Education|Stone et al., Lancet Planetary Health and Planetary Health Alliance framework (2018–2021)|新课程能否改变临床和公共政策实践|教育框架加入相互联系、公平、系统思维和行动|让卫生专业理解生态决定因素与共同收益|行星健康教育把气候、食物、生物多样性和正义连接到临床与公共卫生能力|课程若只加讲座而不改采购、研究和临床路径，知识不会转成机构行为
医疗气候足迹|Health-Care Climate Footprint|Health Care Without Harm & Arup, Health Care's Climate Footprint (2019)|全球百分比估算能否指导具体医疗减排|范围一二三核算和国家路线图持续细化|把医疗系统自身排放纳入健康责任|报告估计医疗约占全球净排放百分之四点四，突出供应链、能源和交通来源|投入产出模型和国家数据有不确定，单一总占比不能替每家医院设公平目标
EAT-Lancet健康膳食|Planetary Health Diet|Willett et al., The Lancet 393, 447–492 (2019), doi:10.1016/S0140-6736(18)31788-4|全球参考膳食能否跨文化营养和生计适用|本地化可负担性与农业转型成为争议核心|把慢病预防与食物系统边界共同优化|委员会提出富植物参考膳食并建模健康和环境收益，连接营养与土地、气候和养分循环|许多地区负担不起或有营养缺口，全球配额不能忽略原住民饮食和小农生计
气候归因热死亡|Heat Mortality Attribution|Vicedo-Cabrera et al., Nature Climate Change 11, 492–500 (2021), doi:10.1038/s41558-021-01058-x|模型反事实能否把具体死亡归因人为变暖|多城市归因扩展到不平等与适应差异|比较有无人为变暖气候下温度死亡关系|多国城市研究估计暖季热相关死亡中相当部分可归因人为气候变化|死亡函数、城市覆盖和适应假设影响比例，未覆盖低收入地区并非风险更低
污染与健康负担|Pollution and Health|Fuller et al., Lancet Planetary Health 6, e535–e547 (2022), doi:10.1016/S2542-5196(22)00090-0|九百万死亡估计能否避免重复归因和数据空白|传统污染下降而空气与化学污染负担上升|用可比风险评估连接污染暴露与死亡|更新估计2019年污染相关过早死亡约九百万，突出低中收入国家和现代污染|多种暴露相关且监测稀缺，模型估计不能替代地方源解析和干预评估
生物多样性与健康|Biodiversity and Health|IPBES, Global Assessment Report (2019); WHO-CBD state of knowledge|生物多样性减少与健康关系能否超越笼统生态服务|研究连接药物、营养、微生物、病原调节与心理福祉|把物种基因和生态系统变化接到健康路径|评估显示生物多样性支持食物、水、药物、文化与疾病调节，也受人类健康行动影响|关系并非总是单向，某些病原随特定多样性变化增加，需避免简单稀释效应
野火烟雾跨境暴露|Wildfire Smoke Health|Burke et al., Nature and Lancet Planetary Health studies (2021–2024)|颗粒物浓度能否区分野火烟与城市源的不同毒性|卫星、化学传输和健康记录联合归因|把生态火灾变成远距离人口健康暴露|研究显示野火烟可跨越地区增加PM2.5并与呼吸心血管和妊娠风险相关|烟羽模型、室内防护和疏散行为决定个体剂量，地区平均会掩盖高风险职业
地球六项边界越界|Six of Nine Boundaries|Richardson et al., Science Advances 9, eadh2458 (2023), doi:10.1126/sciadv.adh2458|六项越界是否意味着全球系统已不可逆崩溃|更新提供控制变量区间而非末日倒计时|用最新证据量化九项边界状态|研究判断气候、生物圈、土地、淡水、生物地球化学流和新实体六项越界，显示系统远离安全空间|越界表示风险升高而非精确崩溃日期，各边界交互和区域阈值仍不确定
地球系统临界点|Climate Tipping Points|Armstrong McKay et al., Science 377, eabn7950 (2022), doi:10.1126/science.abn7950|临界温度估计能否转成健康预警而不制造宿命论|研究更新冰盖、冻土、环流和生态系统阈值|识别升温可能触发自我维持变化的系统|综合评估显示当前升温已进入部分临界要素风险区，强化尽快减排和适应必要|证据强度和时间尺度差异大，临界点并非越过即瞬间变化，也不能成为放弃行动理由
海洋变化与健康|Ocean Health|IPCC AR6 WGII ocean and human health assessments (2022)|海洋变暖酸化缺氧如何通过食物和生计影响健康|海洋热浪、藻华和渔业营养风险被联合评估|连接海洋系统、食物安全、病原和沿海保护|评估把海洋变暖、酸化、海平面和生态变化与渔业、灾害、弧菌和心理文化损失相连|全球鱼获和海平面均值不能代表岛屿与沿海原住民的不可替代损失
行星健康与抗菌药耐药|Planetary Health and AMR|UNEP, Bracing for Superbugs: environmental action in One Health response to AMR (2023)|环境行动能否改变临床耐药结局|联合国环境署把污染、气候、生物多样性与AMR连接|把制药农业污水和生态压力纳入耐药治理|报告说明环境释放和污染可促进抗菌剂与耐药基因传播，要求源头减排和污水管理|环境浓度到感染负担的量化链仍薄弱，不能以宏观联系替代监测
气候迁移与健康|Climate Mobility and Health|IPCC AR6 WGII and IOM health assessments (2022–2025)|气候是否可单独归因个人迁移决定|研究转向被迫不动、短期流离和城市接收能力|把环境冲击、迁移选择与健康服务连成路径|评估显示灾害、海平面、粮食和生计压力可驱动多种流动并影响伤病、心理和照护连续性|迁移多因且可能是适应，使用气候难民标签会抹去能动性和法律差异
原住民知识与治理|Indigenous Planetary Health|Redvers et al., Lancet Planetary Health and Indigenous determinants frameworks (2020–2023)|引用传统知识是否给予土地权和决策权|研究强调关系性健康、主权和共同治理|把土地文化语言与身心生态健康视为整体|原住民框架指出健康来自人与土地、祖先和未来世代的关系，挑战自然仅是资源的假设|抽取知识却不返还数据、土地和权力会重复殖民，参与不能替代主权
Lancet气候健康倒计时|Lancet Countdown|Romanello et al., The Lancet annual report 2024|年度全球指标能否推动国家政策而非只重复警报|报告追踪热、传染病、粮食、经济与行动|用持续指标把气候承诺和健康结果并列|倒计时年度更新多项健康与气候指标，显示热暴露、化石燃料和适应差距的趋势|全球年度汇总存在数据滞后，指标增加不等于政策执行或局地健康改善
WHO气候与健康决议|WHO Climate and Health|World Health Assembly resolution on climate change and health (2024)|卫生部门倡议能否影响能源交通农业等上游决策|WHO推动国家健康适应计划和低碳韧性系统|把气候行动确立为公共卫生职责|世卫大会与相关框架要求卫生系统评估风险、增强韧性并倡导减排共同收益|卫生部门若无跨部门预算与法规权，决议会停在宣传和项目化适应
年度行星健康体检|Planetary Health Check|Potsdam Institute and partners, Planetary Health Check (2024–2025)|年度仪表板能否表达边界交互和不确定度|报告尝试持续更新九项边界和地球韧性|把科学更新转成可重复年度状态检查|年度体检汇集边界数据和解释，帮助公众与决策者追踪地球系统状态变化|颜色分类会压缩方法差异和区域变化，不能把一次年度分级当作精确预测
健康共同收益政策|Health Co-Benefits of Decarbonization|Hamilton et al., Lancet Planetary Health 5, e74–e83 (2021), doi:10.1016/S2542-5196(20)30249-7|模型健康收益能否在能源食物交通现实政策中兑现|净零情景越来越报告空气、活动与膳食收益|让减排同时减少污染并改善行为风险|多国情景研究估计符合巴黎目标的能源、交通和饮食行动可避免大量过早死亡|收益依赖政策设计和基线，若成本转给低收入者，平均净收益仍可能扩大不平等
""",
)


add(
    562, "climate-health-sustainable-healthcare", "气候与健康、可持续医疗", "气候健康 · 可持续医疗",
    "从热行动计划、医疗气候足迹和净零卫生系统到WHO低碳韧性框架、绿色手术、供应链与公平转型，审计医疗自身的双重责任。",
    "医疗系统既承受热浪、洪水、烟霾和传染病冲击，也通过能源、药品、器械和供应链制造排放。可持续医疗不能以少用资源损害照护，必须让临床质量、韧性、碳和公平共同优化。",
    "可持续医疗的决定性机制是把气候韧性与全生命周期排放嵌入临床质量和资源配置，而不是单独报告医院碳总量",
    "未来五年要看范围三供应链、低碳临床路径和气候风险预算能否进入采购与质量考核，并保证低收入地区扩容基本照护时不被同一减排阈值惩罚",
    [
        "WHO, Operational framework for building climate resilient health systems (2015).",
        "Health Care Without Harm & Arup, Health Care's Climate Footprint (2019).",
        "NHS England, Delivering a Net Zero National Health Service (2020).",
        "WHO, Operational framework for building climate resilient and low carbon health systems (2023).",
    ],
    r"""
医疗气候韧性操作框架|Climate-Resilient Health Systems|WHO, Operational framework for building climate resilient health systems (2015)|十个组成部分能否进入常规卫生规划和预算|2023年框架加入低碳目标形成双重责任|从领导、劳动力、信息、基础设施到项目系统化适应|WHO 2015框架把气候风险纳入卫生系统核心职能，避免适应只是一项环境项目|国家卫生能力差异巨大，清单完成不能代表医院在真实灾害中维持服务
艾哈迈达巴德热行动计划|Ahmedabad Heat Action Plan|Ahmedabad Municipal Corporation and NRDC, launched 2013; evaluation studies 2018|预警与公众沟通能否减少热死亡而非只改变记录|印度多城市复制并本地化热健康行动|用阈值预警、部门协调和脆弱人群措施应对热浪|行动计划连接气象预警、卫生培训、公众传播和降温措施，评估显示极端热期死亡下降|前后比较受年份和死亡登记影响，空调不可及与户外劳动仍需结构性保护
麻醉气体生命周期|Anesthetic Gas Footprint|Sherman et al., Anesthesia & Analgesia 114, 1086–1090 (2012), doi:10.1213/ANE.0b013e31824f694d|降低高温室效应麻醉剂能否保持患者安全和选择|地氟烷退出、低流量麻醉和气体捕集成为医院行动|按临床等效剂量比较挥发性麻醉气候影响|生命周期研究显示不同麻醉气体全球增温潜势差异巨大，使药物选择成为可行动减排点|患者适应证和总新鲜气流决定实际排放，禁用单药不能替代围术期整体质量
气候敏感卫生设施|Climate-Resilient Health Facilities|WHO, Safe and climate-resilient health care facilities guidance (2020)|设施改造能否同时保证能源、水、感染控制和可及|WHO清单扩展到环境可持续设施|按灾害风险强化关键服务和基础设施|指南要求评估卫生人员、供水卫生、能源、基础设施和废物，使设施在气候冲击中继续安全服务|资源有限机构若只得到评估表而无资本投入，暴露风险会被再次记录而非解决
医疗全球气候足迹|Health Care Climate Footprint|Health Care Without Harm & Arup (2019)|约百分之四点四估算能否分配机构与国家责任|各国建立范围一二三核算和路线图|量化医疗能源、运营和供应链排放|报告估计医疗约占全球净排放百分之四点四，并显示供应链是主要来源|投入产出估算不等于医院采购明细，低收入系统扩容与高收入过度医疗不能承担同样路径
吸入器碳差异|Inhaler Carbon Footprint|Wilkinson et al., BMJ 2019 and NHS inhaler guidance|从定量吸入器改干粉能否兼顾吸气能力和依从|共享决策与良好疾病控制被列为先决条件|在临床等效时减少高增温推进剂|研究与指南指出某些定量吸入器推进剂足迹远高于干粉装置，提供处方减排机会|儿童、老年和急性发作未必能有效使用干粉，换药导致控制变差会令方向反号
NHS净零路线|NHS Net Zero|NHS England, Delivering a Net Zero National Health Service (2020)|全球首个国家卫生净零承诺能否覆盖药品和供应链|NHS设直接控制2040和影响范围2045目标|用分范围路线把净零嵌入国家卫生系统|路线量化药物、建筑、旅行、供应链和临床服务，并设中期行动与采购要求|目标依赖供应商和电网脱碳，若等候、质量和健康不平等恶化就不是可持续医疗
COP26健康倡议|COP26 Health Programme|WHO and UK COP26 Presidency, climate-resilient and low-carbon health commitments (2021)|国家承诺能否转成有资金的卫生适应计划|七十五国以上加入ATACH并获得技术资源|把卫生系统韧性和低碳承诺带入气候谈判|COP26首次形成正式健康计划，邀请国家承诺气候韧性和低碳可持续卫生系统|承诺口径和基线不同且多为自愿，签署数量不能替代排放和服务连续性结果
绿色手术|Green Surgery|UK Green Surgery Report (2023) and surgical sustainability studies|减少一次性耗材与器械是否影响感染和周转|围术期路线转向麻醉、采购、器械、废物和路径整体|按临床过程做手术生命周期评估|绿色手术框架识别高影响耗材、能源、麻醉和不必要流程，鼓励可复用器械与适当日间手术|单项碳估算跨医院差异大，感染控制和再处理能力不足时可复用不一定更优
WHO低碳韧性框架|Low-Carbon Resilient Health Systems|WHO, Operational framework for building climate resilient and low carbon health systems (2023), ISBN 9789240081888|减排与适应能否避免在资源分配上相互竞争|十个组成部分为不同收入和排放水平提供路径|把安全优质照护、韧性和低碳共同设计|框架目标是在不稳定气候中保护社区，同时优化资源并降低温室气体，明确双重责任|高排放系统和能源贫困系统不能套同一优先级，转型必须以全民健康覆盖为边界
医院洪水与停电韧性|Hospital Climate Resilience|PAHO Smart Hospitals and WHO facility assessments, 2017–2024|加固建筑能否覆盖供应链、人员和信息系统连续性|智慧医院把安全、绿色和运营连续性结合|用多灾种评估保护关键诊疗能力|项目通过风险评估、备用能源、水、结构和运营方案降低飓风洪水后的服务中断|备用柴油若长期高碳且燃料链脆弱，会把短期韧性与长期减排对立
极端热与孕产健康|Heat and Maternal Health|Chersich et al., BMJ and Nature Medicine reviews and cohorts (2020–2024)|温度暴露与早产死胎关联能否排除污染和社会混杂|热健康计划开始识别孕产妇和新生儿|把高温纳入产前风险、劳动保护和设施降温|多地区研究关联高温与早产、死胎及孕产压力，提示妇幼服务需气候适应|暴露按室外站点估计会误分个人温度，空调、工作和住房条件决定风险不平等
气候灾害与心理健康|Climate Disaster Mental Health|WHO mental health and climate change policy brief (2022)|灾后焦虑悲伤是否会被过度医学化而忽略住房和生计|心理急救和长期社区重建纳入气候适应|连接急性灾害、慢性焦虑与社会决定因素|WHO指出洪水、火灾、热和流离可增加心理困扰并冲击服务，需要把支持纳入气候行动|症状量表不能代替恢复住房、生计和社会网络，临床化会转移结构责任
远程医疗生命周期|Telemedicine Footprint|Purohit et al., Journal of Climate Change and Health lifecycle studies (2021–2024)|少出行是否会被设备、数据中心和重复就诊排放抵消|研究按地区、距离、模态和临床效果细分|比较远程与线下路径的全流程资源|远程医疗在避免长途交通时常可降低排放，也可能扩大偏远地区服务|低价值复诊、设备更新、网络能耗和后续补做体检会吞噬收益，碳不能替代诊疗适宜性
药品环境与气候足迹|Sustainable Pharmaceuticals|NHS, EMA and life-cycle pharmaceutical initiatives, 2021–2025|药品减排能否兼顾疗效、供应安全和水环境|采购开始询问制造排放、包装和活性成分排放|把药物从研发制造使用到处置纳入生命周期|药品常占医疗供应链排放大头，制造能源、冷链和不必要处方提供减排点|用价格或单一碳因子替代质量会造成短缺，环境毒性和气候指标也不可互换
范围三可持续采购|Scope 3 Sustainable Procurement|NHS Supplier Roadmap and international health procurement standards, 2022–2028|要求供应商碳计划会不会排除小企业和低收入生产者|采购合同逐步加入产品碳与净零要求|以购买力推动药械供应链测量和减排|国家卫生系统可通过招标要求供应商披露排放、设目标并改善包装物流，触及最大排放范围|核算方法和数据能力不一，合规成本可能集中到小供应商且诱发绿色漂洗
气候信息健康预警|Climate-Informed Health Early Warning|WHO-WMO Joint Climate and Health Programme, 2023–2026|气象提前量能否转成卫生系统可执行资源调度|气候服务连接热、媒介病、空气和营养风险|把预报阈值与床位药物人员和公众行动绑定|WHO与WMO合作推动将气候信息转为健康决策，目标是从天气预测走到早期行动|预报有技能不等于部门会行动，错误警报和地方阈值不准会消耗信任
低碳临床路径|Low-Carbon Clinical Pathways|NICE, NHS and specialty society sustainability guidance, 2021–2025|减碳是否可通过减少低价值照护同时提高质量|专科开始为肾病呼吸外科和影像重设计路径|优先避免无效照护再优化必要照护|低碳路径先减少不必要检查住院和并发症，再选择较低影响药械，使质量与碳方向一致|以碳为理由限制必要服务会伤害弱势患者，每项改变必须同时监测临床结局
公正卫生转型|Just Transition in Health Care|WHO ATACH and health equity principles, 2023–2026|净零目标会不会把成本转给患者、工人和能源贫困地区|公平与全民健康覆盖成为低碳路线约束|按历史排放能力和健康需求分配转型责任|公正转型要求高排放系统更快减量并支持低资源系统获得清洁可靠能源和基本照护|平均碳预算若不区分必要扩容与过度医疗，会惩罚最缺服务人群
低碳目标设定指南|Low-Carbon Health Targets|WHO, Target setting for low carbon sustainable health systems (2024)|机构目标能否同时可比、科学且不忽略范围三|指南连接基线、边界、阶段目标和实施监测|把净零愿景压成有年份和责任的可核验目标|WHO资源帮助卫生系统选择核算范围、基线、中期目标和行动路径，并与韧性规划协调|缺数据系统可能先耗时核算而延误可行动措施，目标也需随服务扩容和电网变化重算
""",
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for panel in PANELS:
        data = {k: v for k, v in panel.items() if k != "extra_refs"}
        data["bridges"] = [
            f"第一幕追踪{panel['title']}如何把旧问题变成可执行、可测量的对象；判断标准始终是{panel['thesis']}。",
            f"第二幕转向规模、闭环与责任。最新纪录只有在失败和资源进入分母后，才足以支持“{panel['thesis']}”。",
        ]
        data["items"] = [make_item(r, i, panel) for i, r in enumerate(panel["items"])]
        data["tail"] = make_tail(panel)
        data["refs"] = [r[2] for r in panel["items"]] + panel["extra_refs"]
        path = OUT / f"{panel['no']}-{panel['slug']}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
