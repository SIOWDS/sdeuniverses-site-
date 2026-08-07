#!/usr/bin/env python3
"""Create the researched panel dossiers for Frontier 542--550.

The compact records below are editorial inputs, not scraped text.  The shared
builder expands them into the fixed six-paragraph argument form and audits the
published HTML.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "frontier_541_550_data"


def records(blob: str):
    rows = []
    for line in blob.strip().splitlines():
        parts = [x.strip() for x in line.split("|")]
        if len(parts) != 8:
            raise ValueError((len(parts), line))
        rows.append(parts)
    assert len(rows) == 20, len(rows)
    return rows


PANELS = [
    dict(
        no=542, slug="self-driving-labs-automated-scientific-discovery",
        title="自驱动实验室与自动化科学发现", group="科学智能 · 自动化发现",
        description="二十个可核验节点，追踪自驱动实验室如何把假设、实验、失败与复现接成闭环。",
        lede="真正的自驱动实验室不是给仪器装上一条机械臂，而是让选题、执行、异常、阴性结果和下一轮决策共享同一本账。本面板沿着二十个可核验节点追问：闭环在哪一步真的缩短了发现，而又在哪一步把人的判断藏进了代理指标。",
        thesis="闭环只有把失败和人工接管计入分母，才构成自动化科学发现",
        outlook="未来五年的胜负不在无人值守时长，而在跨实验室可迁移的异常语义、开放阴性数据和能接受人工否决的策略层",
        extra_refs=[
            "Häse, Roch & Aspuru-Guzik, Next-Generation Experimentation with Self-Driving Laboratories, Trends in Chemistry 1, 282–291 (2019).",
            "National Academies, Automated Research Workflows for Accelerated Discovery, workshop materials and provenance recommendations.",
            "Nature Communications 15, 2416 (2024), Performance metrics for self-driving laboratories.",
            "Chemical Science 16 (2025), LIRA: a modular framework for laboratory integration and robotic autonomy.",
        ],
        items=records(r"""
Robot Scientist Adam|Robot Scientist Adam|King et al., Science 324, 85–89 (2009), doi:10.1126/science.1165620|酵母功能基因组学能否由机器闭环提出并检验假设|Adam的谱系进入后续机器人科学家与实验知识表示|机器独立提出并验证功能基因假设|系统把候选基因、代谢物与实验步骤编码后自动选择湿实验，留下首个端到端机器科学家证据|适用于定义清楚、仪器稳定的功能筛选；开放世界问题仍需人决定概念和价值
Robot Scientist Eve|Robot Scientist Eve|Williams et al., J. R. Soc. Interface 12, 20141289 (2015), doi:10.1098/rsif.2014.1289|高通量命中是否等于可转化药物发现|抗寄生虫药物再利用继续作为自动假设检验范例|自动筛选与知识驱动优先级合并|Eve把药物筛选、剂量反应和候选排序闭合，并找到与热带病相关的再利用线索|命中率依赖试验体系与阈值，不能从体外活性直接外推临床有效性
AFLOW高通量材料学|AFLOW|Curtarolo et al., Computational Materials Science 58, 218–226 (2012), doi:10.1016/j.commatsci.2012.02.005|计算高通量能否替代实验闭环|AFLOW数据库与标准化工作流持续扩展|可追溯计算配方形成机器候选池|标准化输入、赝势和结构原型使大批量材料计算可比较，候选生成速度首次工程化|计算数据库继承近似泛函和结构先验，实验可合成性不能由低形成能独占
Materials Project|Materials Project|Jain et al., APL Materials 1, 011002 (2013), doi:10.1063/1.4812323|开放计算材料数据的误差能否跨化学空间一致|数据库持续发布版本、API与误差说明|统一数据底座改变候选检索方式|开放材料性质与程序化接口让实验室可从同一候选空间出发并回写验证结果|版本、计算参数和纠错记录若未锁定，同名材料数值不能视作永久真值
模块化有机合成机器|Organic Synthesis Machine|Li et al., Science 347, 1221–1226 (2015), doi:10.1126/science.aaa5414|模块化合成能否覆盖反应条件的长尾|自动合成平台转向更通用的规划和流动化接口|积木式单元把合成路线变成可执行程序|机器以标准化模块完成一组小分子合成，证明合成知识可以部分编译成设备动作|反应类别、纯化兼容性与耗材接口限制覆盖面，成功分子不能代表化学空间
贝叶斯材料搜索|Bayesian Materials Search|Seko et al., Physical Review Letters 115, 205901 (2015), doi:10.1103/PhysRevLett.115.205901|代理模型的不确定度是否校准|主动学习成为自驱动实验室的基础策略|用少量昂贵计算定位低热导材料|贝叶斯优化在大候选空间中迭代选择下一批计算，把搜索预算集中到高价值区域|先验核和初始样本决定探索方向，分布外候选会让置信区间虚假收窄
把失败反应写进数据|Dark Reactions|Raccuglia et al., Nature 533, 73–76 (2016), doi:10.1038/nature17439|阴性实验是否能够抵消文献的成功偏差|失败数据学习成为化学闭环的标准主张|未发表失败提高结晶条件预测|从实验室笔记中恢复成功与失败的水热合成记录后，模型优于只读成功文献的学习|失败记录也受选择过程影响，未尝试区域不能伪装成真正阴性样本
自主碳纳米管合成|Autonomous CNT Synthesis|Nikolaev et al., npj Computational Materials 2, 16031 (2016), doi:10.1038/npjcompumats.2016.31|原位测量能否稳定代表最终材料质量|闭环纳米材料生长推动在线计量与控制融合|算法边做边选碳纳米管生长条件|自动平台以拉曼反馈和搜索算法调整温度与气体条件，展示连续制造参数的闭环优化|传感器漂移和替代指标会把系统推向易测而非真正有用的样品
ChemOS实验操作系统|ChemOS|Roch et al., Science Robotics 3, eaat5559 (2018), doi:10.1126/scirobotics.aat5559|通用调度层能否跨越不同仪器语义|ChemOS成为多类自驱动实验室的软件蓝图|把规划器、机器人和数据库解耦|模块化架构让优化算法通过统一接口安排实验、读取结果和更新策略，降低闭环重写成本|接口统一不等于误差统一，每台仪器的校准和异常仍需领域模型
机器人流动合成规划|Robotic Flow Synthesis|Coley et al., Science 365, eaax1566 (2019), doi:10.1126/science.aax1566|路线规划分数能否预测真实设备可执行性|合成规划与自动执行继续合并|从目标分子到流动设备动作的端到端编译|系统将计算合成路线转化为模块化流动反应并自动执行多个药物分子|可用反应模板和硬件模块构成封闭词表，超出词表的路线仍需人工发明
移动机器人化学家|Mobile Robotic Chemist|Burger et al., Nature 583, 237–241 (2020), doi:10.1038/s41586-020-2442-2|移动性是否真正增加科学自治而非展示效果|移动机器人继续探索共享人类实验室空间|在八天内自主运行688次实验|机器人在普通实验室移动、操作仪器并以贝叶斯搜索找到高活性光催化混合物|688次运行集中在给定配方空间；选什么目标、何谓有用仍由人预先写入
Ada薄膜实验室|Ada Thin-Film SDL|MacLeod et al., Science Advances 6, eaaz8867 (2020), doi:10.1126/sciadv.aaz8867|薄膜表征代理能否跨批次保持可比|模块化薄膜闭环扩展到多目标材料发现|机器人在十轮内逼近性能最优区|Ada把溶液处理、退火、光谱测量和贝叶斯优化连在一起，展示材料加工闭环|环境湿度、喷头状态和基底批次会回写结果，漂移若不建模便会制造虚假进步
CAMEO相图导航|CAMEO|Kusne et al., Nature Communications 11, 5966 (2020), doi:10.1038/s41467-020-19597-w|相边界信息能否比黑箱性能更有效引导实验|物理约束主动学习持续进入材料表征|用知识感知策略自主发现相变材料|系统结合衍射、相图知识和主动学习，减少定位相边界与功能区所需测量|知识先验错误时会系统性避开异常相，需保留随机探索和事后残差图
好奇心驱动配方机器人|Curious Formulation Robot|Grizou et al., Science Advances 6, eaay4237 (2020), doi:10.1126/sciadv.aay4237|无预设目标的好奇心是否仍暗含设计者价值|开放式探索成为目标驱动优化的对照路线|以学习进展选择复杂液滴实验|机器人用预测误差下降而非给定性能作为奖励，找到多样液滴行为区域|好奇心指标偏爱可学习变化，可能忽略难测、稀有却科学上重要的现象
快充电池闭环优化|Closed-Loop Fast Charging|Attia et al., Nature 578, 397–402 (2020), doi:10.1038/s41586-020-1994-5|早期寿命预测能否安全替代完整循环试验|电池自动实验转向寿命、快充和安全的多目标权衡|在224个协议中快速筛选快充策略|闭环系统以早期循环信号淘汰劣势协议，大幅缩短比较充电策略的时间|代理寿命在新化学体系或异常衰退机制下会失准，安全约束不能交给均值优化
A-Lab无机材料合成|A-Lab|Szymanski et al., Nature 624, 86–91 (2023), doi:10.1038/s41586-023-06734-w|计算可合成性与机器人实验之间的落差如何入账|353次实验的完整失败谱成为评价自驱动实验室的关键案例|17天实现57个目标中的36个|A-Lab串起文献提取、配方、固相合成、衍射和主动学习，并公开慢动力学、挥发、非晶化与计算误差四类失败|百分之六十三成功率只属于给定目标和设备；人工接管及平均百分之三点九工位异常必须同列
AlphaFlow多步骤搜索|AlphaFlow|Volk et al., Nature Communications 14, 1403 (2023), doi:10.1038/s41467-023-37139-y|强化学习能否在多步骤化学中给出可解释策略|多阶段流动实验成为高维闭环的重要试验场|最多四十个参数的序列决策|平台以强化学习在多步骤纳米材料合成中平衡探索和利用，优化跨步骤条件组合|策略对奖励定义与设备状态敏感，换平台后必须重新校准而不能照搬动作序列
多性质分子自主发现|Multi-Property Molecular Discovery|Koscher et al., Science 382, eadi1407 (2023), doi:10.1126/science.adi1407|多目标帕累托前沿能否代表真实产品价值|分子设计与合成测试闭环开始共同优化多项性质|闭环同时处理光学与化学性能|系统把候选生成、自动合成和实验表征连接起来，在多目标空间中迭代发现分子|未进入目标函数的毒性、成本与可放大性可能在表面帕累托最优中恶化
Coscientist语言模型代理|Coscientist|Boiko et al., Nature 624, 570–578 (2023), doi:10.1038/s41586-023-06792-0|语言模型规划是否可审计且可安全执行|实验代理的工具权限、化学安全与来源追踪成为核心争议|用公开文档规划并执行多类化学任务|系统让大语言模型检索文档、调用代码和控制液体工作站，完成催化反应规划与执行|网页知识、提示注入和幻觉会进入实体实验，权限分层与人工闸门不能省略
分布式异步自驱动实验室|Distributed Asynchronous SDL|Strieth-Kalthoff et al., Science 384, eadk9227 (2024), doi:10.1126/science.adk9227|跨站点并行是否放大批次差异与队列偏差|多实验室异步闭环成为规模化科学自治的新边界|多个平台共享模型而各自异步实验|分布式系统把不同地点的合成与测试结果回写同一策略，减少等待并扩大可用设备集合|站点校准、网络延迟和数据所有权会改变样本顺序，吞吐提升不等于证据独立
"""),
    ),
    dict(
        no=543, slug="quantum-engineering-quantum-control", title="量子工程与量子控制",
        group="量子科技 · 控制工程",
        description="从GRAPE、DRAG与随机基准到低于阈值逻辑存储，重建量子控制的二十年证据链。",
        lede="量子工程的难点从来不是让一个量子态动一下，而是在漂移、串扰、泄漏和测量回写同时存在时，仍能知道哪一个控制动作造成了结果。本面板把脉冲、校准、基准、纠错和实时解码放进同一条因果链。",
        thesis="量子控制进步的单因不是门数增加，而是把不可见误差压成可诊断、可反馈的综合误差通道",
        outlook="接下来五年要看闭环校准是否追得上大规模漂移，以及逻辑操作、解码延迟和非计算泄漏能否进入同一实时控制预算",
        extra_refs=[
            "Glaser et al., Training Schrödinger's Cat: Quantum Optimal Control, European Physical Journal D 69, 279 (2015).",
            "Terhal, Quantum Error Correction for Quantum Memories, Reviews of Modern Physics 87, 307–346 (2015).",
            "Google Quantum AI, Quantum error correction below the surface code threshold, Nature 638, 920–926 (2025).",
            "Quantum Economic Development Consortium, Application-Oriented Performance Benchmarks for Quantum Systems, technical reports.",
        ],
        items=records(r"""
GRAPE梯度脉冲工程|GRAPE Optimal Control|Khaneja et al., Journal of Magnetic Resonance 172, 296–305 (2005), doi:10.1016/j.jmr.2004.11.004|数值最优脉冲对模型误差是否鲁棒|GRAPE仍是量子控制软件与自动微分脉冲设计的基础|用传播梯度直接优化控制波形|GRAPE高效计算分段控制的保真度梯度，把原本不可搜索的脉冲空间变成工程优化问题|哈密顿量辨识错误和带宽限制会使仿真最优在实机上失效，须闭环校准
随机基准|Randomized Benchmarking|Knill et al., Physical Review A 77, 012307 (2008), doi:10.1103/PhysRevA.77.012307|平均门误差能否代表相关噪声与泄漏|循环基准和交叉熵基准继续补充其盲区|用随机序列衰减估计平均误差|随机化把态制备与测量误差部分隔离，使跨设备比较不再只依赖单次层析|马尔可夫与门无关假设被破坏时，单一指数会掩盖慢漂移、相干积累和泄漏
Transmon电荷噪声折衷|Transmon Qubit|Koch et al., Physical Review A 76, 042319 (2007), doi:10.1103/PhysRevA.76.042319|降低电荷色散是否以非谐性和控制拥挤为代价|transmon成为超导处理器主流并推动可调耦合器研究|提高约瑟夫森能与充电能之比|设计以较小非谐性换取指数下降的电荷噪声敏感度，改变了超导量子比特工程|更密集能级使强脉冲引发泄漏，器件改善必须与波形选择共同验收
DRAG抑制泄漏|DRAG|Motzoi et al., Physical Review Letters 103, 110501 (2009), doi:10.1103/PhysRevLett.103.110501|解析修正能否抵抗多能级和参数漂移|DRAG变体已嵌入超导量子芯片日常校准|正交导数分量抵消非计算跃迁|在主脉冲上加入导数正交分量，显著压低弱非谐体系的泄漏和相位误差|脉冲畸变、邻近频率与更高能级会改变最佳系数，不能一次校准永久使用
表面码阈值蓝图|Surface-Code Threshold|Fowler et al., Physical Review A 86, 032324 (2012), doi:10.1103/PhysRevA.86.032324|局部门误差阈值能否覆盖相关噪声与解码延迟|距离递增实验已把阈值从蓝图推进到实机|二维近邻稳定子测量给出容错路径|表面码以局部校验和距离扩展把物理误差转成可指数压低的逻辑误差命题|泄漏、串扰和时间相关事件不满足独立噪声假设，会令名义阈值过度乐观
单比特高保真闭环|High-Fidelity Single-Qubit Gates|Barends et al., Nature 508, 500–503 (2014), doi:10.1038/nature13171|平均百分之九十九点九附近是否已足够容错|系统级瓶颈转向双比特门、测量和泄漏|校准反馈把单比特误差压到阈值下|实验以随机基准展示高保真单比特控制，说明脉冲和硬件联合优化可越过表面码要求|平均保真度不能替代最坏情况误差，局部门好并不保证并行层仍好
重复误差检测|Repetitive Error Detection|Kelly et al., Nature 519, 66–69 (2015), doi:10.1038/nature14270|反复测量稳定子是否引入更多回写错误|多轮综合征测量成为逻辑存储的核心操作|九量子比特链重复检测比特翻转|重复校验展示综合征随时间形成可解码轨迹，而非一次末端读数|测量串扰、复位残留和解码模型错误会把检测器本身变成主要噪声源
最优控制的可转移性|Quantum Optimal Control|Glaser et al., European Physical Journal D 69, 279 (2015), doi:10.1140/epjd/e2015-60464-1|开环模型设计与实验闭环学习如何分工|自动微分、强化学习与鲁棒控制不断合流|从核磁方法发展为跨平台控制学|综述统一了可控性、脉冲搜索和鲁棒性语言，使不同量子硬件可共享控制问题|共享数学不等于共享参数，控制器跨设备迁移必须重做系统辨识
变分量子本征求解|VQE|Peruzzo et al., Nature Communications 5, 4213 (2014), doi:10.1038/ncomms5213|浅电路能否抵消测量开销和噪声偏置|误差缓解与问题定制拟设成为近期量子算法主线|经典优化器闭环调节量子电路参数|VQE把量子期望值测量与经典优化接成混合控制环，避开深相位估计|贫瘠高原、抽样成本和优化器对噪声的追逐会令低能量并非正确量子态
QAOA控制视角|QAOA|Farhi, Goldstone & Gutmann, arXiv:1411.4028 (2014)|有限深度参数化控制是否有规模优势|QAOA成为模拟、控制与组合优化的共同试验台|交替问题与混合哈密顿量形成可调协议|参数化交替演化把离散优化写成可实验实现的有限时控制问题|经典预处理、实例结构与采样预算必须计入，近似比不能只报最好一次
超导量子优势实验|Random-Circuit Sampling|Arute et al., Nature 574, 505–510 (2019), doi:10.1038/s41586-019-1666-5|交叉熵保真度是否足以说明可用计算能力|经典模拟进步持续改写任务差距但不抹去控制规模证据|五十三量子比特随机线路采样|实验把并行门校准、串扰管理和随机线路验证推到处理器尺度|专用采样任务与实用算法距离很大，经典基线和保真估计模型变化会改写优势倍数
量子体积|Quantum Volume|Cross et al., Physical Review A 100, 032328 (2019), doi:10.1103/PhysRevA.100.032328|单一综合分数是否会遮蔽任务结构|算法量子比特与应用基准继续拆分综合能力|宽度与深度共同进入可执行阈值|量子体积以重输出概率把门质量、连通性、编译和规模压入同一实测任务|分数随编译器和抽样规则变化，不能代表纠错能力或某一应用的成本
零噪声外推|Zero-Noise Extrapolation|Temme, Bravyi & Gambetta, Physical Review Letters 119, 180509 (2017), doi:10.1103/PhysRevLett.119.180509|可控放大噪声是否保持误差通道形状|误差缓解成为纠错前设备的标准工具箱|多噪声尺度外推无噪声期望值|通过执行多个放大噪声版本并外推，算法在不增加纠错比特时降低偏差|外推方差迅速增大；噪声若随尺度改变类型，截距会给出精确但错误的结果
脉冲级变分控制|Pulse-Level Variational Control|Kandala et al., Nature 549, 242–246 (2017), doi:10.1038/nature23879|硬件高效拟设是否只是把器件偏差写进答案|脉冲级优化逐渐绕过固定门集的编译损耗|短纠缠线路直接适应芯片连通性|硬件高效VQE用浅层旋转和本地纠缠器完成小分子能量估计|表达能力和可训练性互相牵制，化学精度不能从小系统线性外推
逻辑比特实时反馈|Real-Time Quantum Feedback|Andersen et al., Nature Physics 16, 875–880 (2020), doi:10.1038/s41567-020-0920-y|反馈延迟能否低于错误相关时间|低延迟电子学与条件分支成为量子控制栈的一部分|实时校验与纠错延长编码态寿命|控制器在实验过程中读取综合征并条件性反馈，使纠错不再是事后数据处理|读出、传输和判决延迟合计若过长，反馈会纠正已经变化的状态
重复纠错的规模化|Repetition-Code Scaling|Google Quantum AI, Nature 595, 383–387 (2021), doi:10.1038/s41586-021-03588-y|增加量子比特是否真的降低逻辑误差|检测事件图和并行校准成为表面码扩展前提|多距离重复码展示误差随规模压低|实验以多轮比特翻转码观察距离增加带来的逻辑错误下降，并公开时空相关缺陷|它只覆盖一类错误，向全量子表面码迁移还要同时控制相位、泄漏和边界操作
表面码距离递增抑错|Scaling Surface-Code Memory|Google Quantum AI, Nature 614, 676–681 (2023), doi:10.1038/s41586-022-05434-1|距离五是否足以证明可持续指数抑错|逻辑误差随代码距离下降成为硬件容错的转折证据|距离五逻辑比距离三略低|实验在超导芯片上比较两个代码距离，首次让增加物理比特带来净逻辑改善|优势幅度仍小且运行周期有限，稀有相关事件决定更大距离能否延续
中性原子逻辑处理器|Logical Neutral-Atom Processor|Bluvstein et al., Nature 626, 58–65 (2024), doi:10.1038/s41586-023-06927-3|可重构原子阵列的移动与损失是否可被纠错吸收|逻辑量子比特上的纠缠与算法操作成为新比较维度|四十八个逻辑量子比特实现可编程操作|平台用原子重排、横向门和纠错码展示大批逻辑编码单元及逻辑算法|后选择和原子损失处理会改变有效成功分母，持续实时纠错仍需证明
低于阈值的逻辑存储|Below-Threshold Quantum Memory|Google Quantum AI, Nature 638, 920–926 (2025), doi:10.1038/s41586-024-08449-y|短期低于阈值能否转化为长算法容错|距离七一百零一量子比特存储与实时解码给出最新系统锚点|每轮逻辑误差百分之零点一四三|距离七表面码获得二点一四的抑错因子，寿命超越最佳物理比特约二点四倍，实时解码延迟六十三微秒|逻辑门、魔态、长时稀有突发和完整控制栈尚未同等低于阈值
模块化离子阱计算机|Modular Trapped-Ion Computer|Pino et al., Nature 592, 209–213 (2021), doi:10.1038/s41586-021-03318-4|模块搬运能否在扩展时保持低串扰与高占空比|量子电荷耦合器架构继续增加并行区与自动校准|多区离子阱执行容错准备和算法|系统把离子装载、穿梭、门和测量编排成可编程机器，证明控制问题可跨区域模块化|搬运加热、激光稳定与校准吞吐在更大系统会成为新的串行瓶颈
"""),
    ),
    dict(
        no=544, slug="quantum-sensing-metrology", title="量子传感与计量", group="量子科技 · 精密测量",
        description="从量子极限、NV中心与压缩光到网络传感，审计量子传感与计量的二十个证据节点。",
        lede="量子传感真正改变的不是仪表盘多出一个小数位，而是噪声、资源和扰动的定义被重新写过。这里把灵敏度、带宽、动态范围、制备损耗和被测对象回写并列，避免把理想态优势误当成系统优势。",
        thesis="量子传感的单因是可用量子资源对完整估计误差的净压低，而非某一局部灵敏度纪录",
        outlook="未来五年要看压缩、纠缠和量子存储能否在野外损耗、长时间漂移及网络时钟不同步下保留净优势",
        extra_refs=[
            "Degen, Reinhard & Cappellaro, Quantum sensing, Reviews of Modern Physics 89, 035002 (2017).",
            "Ludlow et al., Optical atomic clocks, Reviews of Modern Physics 87, 637–701 (2015).",
            "Giovannetti, Lloyd & Maccone, Advances in quantum metrology, Nature Photonics 5, 222–229 (2011).",
            "National Academies, Quantum Sensors and Measurement Infrastructure, metrology workshop reports.",
        ],
        items=records(r"""
量子增强测量的资源账|Quantum-Enhanced Measurements|Giovannetti, Lloyd & Maccone, Science 306, 1330–1336 (2004), doi:10.1126/science.1104149|海森堡标度在损耗和有限先验下能否兑现|资源计数转向包括时间、光子、制备和读出|纠缠探针改写估计误差标度|理论把经典散粒噪声与纠缠资源的极限分开，为后续实验提供统一目标|若只数通过样品的光子而不数制备失败和参考束，优势会被高估
芯片原子钟|Chip-Scale Atomic Clock|Knappe et al., Applied Physics Letters 85, 1460–1462 (2004), doi:10.1063/1.1787942|微型化后的功耗与稳定度如何交换|芯片钟进入导航、通信和分布式传感的守时层|微加工蒸气室把原子频标缩到低功耗封装|小型蒸气室与相干布居俘获证明量子频标可进入便携系统|温度、缓冲气体老化和电子本振会主导长期漂移，原子跃迁不是全部系统
单自旋NV磁力计|Single-Spin NV Magnetometry|Maze et al., Nature 455, 644–647 (2008), doi:10.1038/nature07279|单缺陷灵敏度能否在纳米距离和室温同时保持|浅层NV、量子存储与表面工程持续延长相干|单自旋实现纳米尺度磁场读出|金刚石NV中心以光学初始化和微波回波感知局域磁场，打开室温纳米磁成像|表面噪声随探针靠近急增，标称灵敏度必须连同距离、体积和带宽报告
纳米尺度核磁共振|Nanoscale NMR|Staudacher et al., Science 339, 561–563 (2013), doi:10.1126/science.1231675|统计极化信号能否给出化学结构而非存在性|NV核磁向相关谱、单分子与高场路线推进|检测纳米体积中的质子自旋涨落|浅层NV用动态解耦读出表面样品的核自旋噪声，把核磁体积缩至纳米尺度|谱线受扩散、表面和滤波函数共同塑形，存在信号不等于分子结构已解析
压缩光进入LIGO|Squeezed Light in LIGO|Aasi et al., Nature Photonics 7, 613–619 (2013), doi:10.1038/nphoton.2013.177|注入压缩是否在全频段改善而不放大另一正交噪声|频率相关压缩已成为引力波台站升级主线|压缩真空降低高频散粒噪声|实机把压缩态注入公里级干涉仪并获得灵敏度改善，量子光学首次长期进入大科学设施|光损耗和相位噪声吃掉压缩，低频辐射压力还会因反压缩而恶化
量子照明抗背景|Quantum Illumination|Lopaeva et al., Physical Review Letters 110, 153603 (2013), doi:10.1103/PhysRevLett.110.153603|保留相关优势是否必须保持可见纠缠|微波量子照明和实用接收机继续检验系统收益|强背景下量子相关提升目标判别|实验在破坏纠缠的噪声中仍利用源端相关性改善判别，展示资源优势不等于末端纠缠|公平基线、总发射能量和接收器复杂度会显著改变所谓量子优势
未探测光子成像|Imaging with Undetected Photons|Lemos et al., Nature 512, 409–412 (2014), doi:10.1038/nature13586|成像信息来自未探测光子还是诱导相干的整体干涉|中红外和显微成像继续利用分离照明与探测波段|样品光子不被探测器直接接收|两次参量过程的路径不可区分使可见光探测器恢复红外样品信息|源亮度、相位稳定和经典非线性成像基线必须同条件比较
量子网络时钟|Networked Quantum Clocks|Kómár et al., Nature Physics 10, 582–587 (2014), doi:10.1038/nphys3000|分布式纠缠成本能否低于独立时钟平均|光钟链路与网络纠缠形成相邻而不同的路线|跨节点纠缠提升全局时间估计|理论显示共享纠缠可让多个时钟测量共同相位并逼近网络级量子极限|光子损耗、同步和量子存储时间会使远程制备成本超过局部收益
量子金刚石显微镜|Quantum Diamond Microscope|Glenn et al., Nature Methods 12, 736–738 (2015), doi:10.1038/nmeth.3449|宽场像素平均是否保留单缺陷量子灵敏度|NV宽场显微镜进入磁性材料、细胞与芯片诊断|NV层并行成像磁场纹理|大面积NV集合结合相机读出，把量子磁测从扫描点扩展成二维图像|空间分辨率、光功率和温升互相耦合，像素多不等于独立量子通道多
现场量子重力仪|Field Quantum Gravimetry|Freier et al., Journal of Physics: Conference Series 723, 012050 (2016), doi:10.1088/1742-6596/723/1/012050|原子干涉仪在振动环境能否胜过经典重力仪|便携冷原子重力仪进入地下勘测与计量比对|自由落体原子相位测量绝对重力|激光脉冲分束和原子自由落体给出可溯源重力读数，减少机械弹簧漂移|振动隔离、波前像差和科里奥利效应在现场常比量子投影噪声更大
量子传感统一框架|Quantum Sensing Framework|Degen, Reinhard & Cappellaro, Reviews of Modern Physics 89, 035002 (2017), doi:10.1103/RevModPhys.89.035002|灵敏度公式能否跨平台公平比较|动态解耦、辅助量子比特与连续测量继续扩展框架|把初始化、相互作用与读出拆成共同协议|统一语言使自旋、原子、光学和机械传感器的资源与噪声可对照|同一每根号赫兹数字若带宽、空间分辨率和动态范围不同，仍不能排序
引力诱导纠缠见证|Gravity-Induced Entanglement Witness|Bose et al., Physical Review Letters 119, 240401 (2017), doi:10.1103/PhysRevLett.119.240401|观测纠缠能否唯一归因于量子引力媒介|微小质量叠加、屏蔽和非引力耦合成为实验焦点|两质量仅靠引力相互作用产生纠缠|方案把关于引力量子性的宏大问题压成可测纠缠见证|电磁串扰、卡西米尔力和退相干会伪造或抹去信号，零结果解释依赖完整噪声账
量子传感网络极限|Networked Quantum Sensors|Proctor, Knott & Dunningham, Physical Review Letters 120, 080501 (2018), doi:10.1103/PhysRevLett.120.080501|何种纠缠拓扑匹配未知场的空间结构|分布式量子传感转向任务定制的资源分配|全局参数与局部参数需要不同网络态|理论说明网络纠缠是否有利取决于要估计的是平均场、梯度还是独立局部参数|若任务函数事后改变，预先制备的纠缠可能比独立传感器更差
频率相关压缩|Frequency-Dependent Squeezing|Tse et al., Physical Review Letters 123, 231107 (2019), doi:10.1103/PhysRevLett.123.231107|滤波腔能否让压缩角随频率稳定旋转|先进引力波探测器采用频率相关压缩降低宽带量子噪声|兼顾高频散粒噪声与低频辐射压力|滤波腔旋转压缩椭圆，使不同频段分别压低相应量子噪声|光学损耗、模式失配和控制噪声决定注入十余分贝能留下多少
量子增强相位跟踪|Quantum-Enhanced Phase Tracking|Yonezawa et al., Science 337, 1514–1517 (2012), doi:10.1126/science.1221287|非平稳信号下实时反馈是否仍保持优势|连续量子估计成为生物和通信场景的接口|压缩光与自适应测量追踪随机相位|实验将量子态和反馈估计器结合，对随时间变化的相位取得均方误差优势|信号先验与控制带宽若被经典基线不公平限制，优势会被人为放大
量子雷达微波原型|Microwave Quantum Radar Prototype|Barzanjeh et al., Science Advances 6, eabb0451 (2020), doi:10.1126/sciadv.abb0451|低温纠缠源与室温目标之间是否有系统净收益|量子微波探测继续寻找低损接收和公平经典基线|室温强背景中演示相关目标检测|原型用微波光子相关与低温接收展示近距离目标判别提升|制冷、预放大和参考存储成本未进入简单信噪比，离工程雷达仍远
量子增强暗物质搜索|Quantum-Enhanced Axion Search|Backes et al., Nature 590, 238–242 (2021), doi:10.1038/s41586-020-03183-3|压缩是否能扩大扫描带宽而不降低峰值灵敏度|量子放大器进入轴子与隐光子实验|压缩真空把搜索速度提高约一倍|HAYSTAC在微波腔搜索中使用压缩态越过标准量子极限的带宽约束|损耗与标定误差直接决定排除线，搜索速度增益不能替代独立候选复扫
超越标准量子极限的显微术|Quantum-Enhanced Microscopy|Taylor et al., Nature Photonics 7, 229–233 (2013), doi:10.1038/nphoton.2012.346|低光损伤条件下压缩优势能否保持|量子生物成像转向总剂量和样品回写核算|压缩光提高活细胞粒子跟踪信噪比|实验在光敏样品约束下用量子相关改善微粒跟踪精度|额外光学复杂度、探针毒性和后处理必须与最佳经典照明同账比较
集成量子光学相位传感器|Integrated Quantum Optical Phase Sensor|Stokowski et al., Nature Communications 14, 3355 (2023), doi:10.1038/s41467-023-38246-6|片上压缩优势能否跨过耦合、探测与控制损耗|薄膜铌酸锂继续整合量子光源、电光控制与相位测量|二十六点二毫瓦下测得百分之二点七正负零点二压缩|芯片以二阶非线性产生同频压缩态，并用片上电光控制提高相位测量信噪比|激光和探测仍在片外，耦合损耗与锁相资源必须计入可部署系统
高良率定位相干NV中心|Positioned Coherent NV Centers|Kim et al., Nature Communications 16, 9803 (2025), doi:10.1038/s41467-025-64758-4|纳米级定位能否同时保留高良率与自旋相干|缺陷制造从随机植入转向生长掺杂与局域辐照协同|深度约四纳米精度且平均Hahn相干九十八微秒|方法在预制金刚石纳米柱中定位形成单NV中心，并把单自旋灵敏度器件良率提高约三倍|横向精度、器件间分散和表面环境仍限制阵列传感的统一标定
"""),
    ),
    dict(
        no=545, slug="quantum-communication-quantum-networks", title="量子通信与量子网络",
        group="量子科技 · 网络通信",
        description="从诱骗态、测量设备无关QKD和卫星链路到量子存储网络，审计二十年量子通信证据。",
        lede="量子通信最容易被距离纪录诱惑，也最容易在密钥率、占空比、可信节点和设备漏洞上失真。本面板不把单条光纤当作网络，而是追问密钥、纠缠、存储、路由和认证何时共同形成可运营的服务。",
        thesis="量子网络成立的单因是端到端量子关联在完整损耗与信任账下仍可验证，而不是链路名义距离",
        outlook="未来五年要看量子存储与电信波段接口能否在城域网长期运行，以及设备无关安全能否从低速实验走向可维护网络",
        extra_refs=[
            "Wehner, Elkouss & Hanson, Quantum internet: A vision for the road ahead, Science 362, eaam9288 (2018).",
            "Pirandola et al., Advances in quantum cryptography, Advances in Optics and Photonics 12, 1012–1236 (2020).",
            "ETSI, Quantum Key Distribution standards and implementation-security specifications.",
            "ITU-T Y.3800 series, Overview and requirements for networks supporting quantum key distribution.",
        ],
        items=records(r"""
诱骗态量子密钥分发|Decoy-State QKD|Lo, Ma & Chen, Physical Review Letters 94, 230504 (2005), doi:10.1103/PhysRevLett.94.230504|弱相干光源的多光子脉冲是否泄露密钥|诱骗态成为实际QKD系统抵抗光子数分裂攻击的标准部件|随机改变光强估计单光子贡献|诱骗强度让发送者从统计上约束单光子产额和错误率，缩小理想单光子源与实际激光器的差距|强度调制侧信道和有限码长会破坏渐近安全率，标称距离不能代替最终密钥率
单向量子中继协议|DLCZ Quantum Repeater|Duan, Lukin, Cirac & Zoller, Nature 414, 413–418 (2001), doi:10.1038/35106500|原子系综存储和光子干涉能否在长链同时稳定|存储复用和纠缠纯化继续沿此架构演化|分段纠缠交换改变距离损耗标度|协议把长距离链路拆成可 herald 的短段并用量子存储等待成功事件|存储效率、相干时间和双光子误差会在多段级联时成倍吞噬速率
测量设备无关QKD|Measurement-Device-Independent QKD|Lo, Curty & Qi, Physical Review Letters 108, 130503 (2012), doi:10.1103/PhysRevLett.108.130503|能否在不信任探测器时维持可用密钥率|双场协议与片上干涉继续降低测量端攻击面|把探测器侧信道移到不可信中继|双方在中继做贝尔测量，安全证明不要求信任探测设备，从原理上关闭一大类黑客攻击|独立激光的频率相位同步和有限密钥统计会显著降低现实吞吐
设备无关QKD界线|Device-Independent QKD|Acín et al., Physical Review Letters 98, 230501 (2007), doi:10.1103/PhysRevLett.98.230501|贝尔违背能否在损耗与有限样本下生成正密钥|无漏洞贝尔实验推动设备无关协议走向小规模实现|安全性只依赖可观测相关而非设备模型|理论把量子非定域性直接转成密钥安全，允许把内部设备视作黑箱|探测效率、空间隔离和极低密钥率使它尚不能替代工程QKD
大陆自由空间纠缠分发|Free-Space Entanglement Distribution|Ursin et al., Nature Physics 3, 481–486 (2007), doi:10.1038/nphys629|大气湍流下纠缠可见度能否长期维持|地面试验成为卫星量子链路的前置证据|一百四十四公里自由空间传送纠缠光子|跨岛实验显示高损耗大气链路仍能保留可验证纠缠并支持远距协议|夜间天气窗口、低占空比和站点对准使演示距离不等于日常网络可用性
量子隐形传态城域链路|Metropolitan Quantum Teleportation|Valivarthi et al., Nature Photonics 10, 676–680 (2016), doi:10.1038/nphoton.2016.180|独立光源和电信光纤能否保持不可区分性|城域隐形传态转向量子存储节点和现场光纤|实际光纤上完成远程量子态传送|实验用独立来源和贝尔测量在城域光纤传递量子态，验证网络协议关键原语|后选择成功率与同步资源必须进入分母，保真度高不代表吞吐足够
卫星量子密钥分发|Satellite QKD|Liao et al., Nature 549, 43–47 (2017), doi:10.1038/nature23655|低轨短时过站能否形成稳定密钥服务|卫星QKD向多站、昼间和更小终端推进|星地链路跨越千公里尺度|墨子号在多个地面站演示星地下行量子密钥，绕开光纤指数损耗|卫星与地面站仍是信任边界，天气、过站和密钥缓存决定业务连续性
星地量子隐形传态|Ground-to-Satellite Teleportation|Ren et al., Nature 549, 70–73 (2017), doi:10.1038/nature23675|后选择传态能否发展为有存储的按需网络|空间量子存储接口成为下一阶段瓶颈|地面光子态传至上行一千四百公里卫星|实验在巨大链路损耗下维持贝尔测量与卫星端态重构，证明空间传态可行|成功事件稀少且没有量子存储缓冲，不能把最大斜距等同于可路由网络
卫星纠缠分发|Satellite Entanglement Distribution|Yin et al., Science 356, 1140–1144 (2017), doi:10.1126/science.aan3211|双下行链路是否能闭合局域性并稳定供对|跨洲纠缠和星座方案继续检验网络覆盖|相隔一千二百公里站点共享纠缠|卫星作为源同时向两个地面站发送纠缠光子，克服同距离地面光纤损耗|双站天气与指向必须同步，检测到的配对率远低于源发射率
双场QKD|Twin-Field QKD|Lucamarini et al., Nature 557, 400–403 (2018), doi:10.1038/s41586-018-0066-6|相位匹配是否能稳定越过无中继速率距离界|多种双场变体不断改进有限密钥安全证明|单光子干涉带来平方根信道标度|双方把弱相干脉冲送到中央站干涉，使密钥率随信道透射率平方根变化|长光纤相位漂移与参考光泄漏会抵消理论标度，安全证明依赖实现细节
量子互联网分阶段路线|Quantum Internet Roadmap|Wehner, Elkouss & Hanson, Science 362, eaam9288 (2018), doi:10.1126/science.aam9288|不同代际能力能否用统一接口逐步升级|网络栈与应用层测试床沿阶段模型展开|从可信节点到纠缠网络划分能力阶段|路线把量子网络按端到端纠缠、存储和纠错能力分级，避免把QKD专网直接称为量子互联网|阶段之间未必平滑升级，硬件接口和信任模型变化可能要求重建网络
存储复用量子中继|Multiplexed Quantum Repeater|Hasegawa et al., Nature Communications 10, 378 (2019), doi:10.1038/s41467-019-08776-9|空间与时间复用能否克服低单模成功率|多模量子存储继续提高可等待通道数|多路并行增加纠缠产生机会|实验展示多模存储与纠缠交换原语，让等待成功不再只占一条模式|模式串扰、读写效率和存储寿命会把名义复用数压成更小有效数
五百公里双场QKD|Long-Distance Twin-Field QKD|Chen et al., Physical Review Letters 124, 070501 (2020), doi:10.1103/PhysRevLett.124.070501|超低密钥率纪录能否抵抗有限统计与系统漂移|相位参考和超低噪声探测推动更长链路|五百零九公里光纤越过无中继界|实验在超长光纤上实现双场协议并报告高于点到点界的安全密钥率|运行时间、参考光和探测器稳定性构成巨大隐藏资源，距离纪录不是网络吞吐
三节点量子网络|Three-Node Quantum Network|Pompili et al., Science 372, 259–264 (2021), doi:10.1126/science.abg1919|存储节点能否按需调度多个链路|多节点量子处理器网络继续增加异构接口|三个远程节点形成可切换纠缠连接|金刚石自旋节点和光子链路在三个节点间建立纠缠，展示从链路到网络的拓扑跃迁|生成率、存储退相干和节点重置使连续服务能力仍有限
五百一十一公里MDI-QKD|511-km MDI-QKD|Chen et al., Nature Photonics 15, 570–575 (2021), doi:10.1038/s41566-021-00828-5|长距离与探测侧安全能否同时成立|现场光纤系统转向稳定自治和有限密钥|五百一十一公里实现测量设备无关密钥|超导探测器、超稳激光和相位控制把MDI型协议推到数百公里|密钥率极低且实验资源昂贵，同等安全服务的总成本仍须比较
四千六百公里综合网络|Integrated Space-to-Ground Quantum Network|Chen et al., Nature 589, 214–219 (2021), doi:10.1038/s41586-020-03093-8|可信节点拼接是否应称为端到端量子网络|卫星与地面QKD继续扩展覆盖同时暴露信任节点治理|地面光纤与卫星链路覆盖四千六百公里|系统连接多地QKD骨干和卫星链路，展示跨区域密钥服务编排|多数路径依赖可信中继，网络被攻破的面随节点数量增长
六百公里现场双场QKD|Field Twin-Field QKD|Pittaluga et al., Nature Photonics 15, 530–535 (2021), doi:10.1038/s41566-021-00811-0|现场环境的相位补偿能否长期维持|双场QKD进入已铺设光纤和运营条件试验|六百公里量级现场链路生成密钥|系统在真实光纤扰动下保持中央干涉，缩小实验室纪录与现场部署差距|长时间平均掩盖停机窗口，服务等级应同时报告可用率与恢复时间
电信波段量子存储节点|Telecom Quantum-Memory Node|Knaut et al., Nature 629, 573–578 (2024), doi:10.1038/s41586-024-07252-z|频率转换能否保持纠缠同时降低网络损耗|固态存储与电信光子接口成为中继节点关键|独立存储节点通过电信光纤纠缠|实验把固态自旋存储器发出的光转换到电信波段并建立远程纠缠|转换噪声、低生成率和存储寿命仍限制多跳扩展
运营商级万公里QKD|Carrier-Grade QKD Network|npj Quantum Information 11 (2025), doi:10.1038/s41534-025-01089-8|万公里覆盖是否依赖过多可信与运维节点|运营级编排、密钥管理和故障恢复成为最新焦点|超过一万公里网络规模运行验证|工程系统把多段光纤、可信中继和统一管理连成大范围密钥基础设施|覆盖长度是各段相加而非单量子链路，安全性取决于每个节点和控制面的治理
量子网络标准栈|Quantum Network Standards Stack|ITU-T Y.3800 series and IETF quantum-network research drafts, updated through 2025|标准接口会不会过早冻结仍快速变化的硬件|QKD密钥管理与纠缠网络架构开始分层标准化|把应用、控制、密钥与量子链路职责拆开|标准工作让跨厂商设备可以讨论服务指标、接口和安全边界|若只标准化QKD而沿用量子互联网名义，会混淆可信密钥网络与端到端纠缠网络
"""),
    ),
    dict(
        no=546, slug="post-quantum-cryptography", title="后量子密码", group="量子科技 · 密码安全",
        description="从LWE、NTRU与哈希签名到NIST三项FIPS和HQC选择，审计后量子密码的迁移证据。",
        lede="后量子密码在2024年越过了“候选算法”门槛，却没有因此完成迁移。真正的前沿已经从数学安全移到实现、协议、库存、互操作和长期密文的时间风险；本面板把标准发布与系统替换严格分开。",
        thesis="后量子安全的单因是可替换的密码敏捷性把已审计算法真正送入端到端协议，而非标准文号本身",
        outlook="未来五年要看混合部署何时退出、硬件侧信道与失败处理能否稳定，以及HQC和FALCON相关标准如何补足算法多样性",
        extra_refs=[
            "NIST, FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (2024).",
            "NIST, FIPS 204: Module-Lattice-Based Digital Signature Standard (2024).",
            "NIST, FIPS 205: Stateless Hash-Based Digital Signature Standard (2024).",
            "NIST, Post-Quantum Cryptography Standardization project and migration guidance, updated 2025–2026.",
        ],
        items=records(r"""
格上的带误差学习|Learning With Errors|Regev, Journal of the ACM 56, 34 (2009); STOC 2005 origin, doi:10.1145/1568318.1568324|最坏情形到平均情形归约能否承受参数与实现变化|LWE成为密钥封装、同态加密和签名的共同安全底座|噪声线性方程连接格困难问题|LWE把可证明困难性与高效代数运算结合，为量子攻击下的公钥密码提供新主干|具体环结构、噪声分布和参数压缩会引入归约未直接覆盖的攻击面
NTRU格密码|NTRU Lattice Cryptography|Hoffstein, Pipher & Silverman, ANTS III, LNCS 1423, 267–288 (1998), doi:10.1007/BFb0054868|长期密码分析能否支持结构化格的效率优势|NTRU类思想继续影响标准候选与部署实现|卷积多项式带来紧凑高效公钥运算|NTRU证明格密码可以在实用速度和密钥尺寸上与传统公钥系统竞争|参数选择和解密失败处理错误可能产生与数学问题无关的现实漏洞
GPV格签名框架|GPV Lattice Signatures|Gentry, Peikert & Vaikuntanathan, STOC 2008, 197–206, doi:10.1145/1374376.1374407|陷门采样的实现能否不泄露秘密基|模格签名的安全证明与实现沿此框架发展|高斯采样连接陷门函数与短签名|GPV建立格上陷门和原像采样的通用签名方法，推动可证明后量子签名|高斯采样与浮点实现会产生侧信道，理论分布必须落实为恒定时间代码
环LWE效率折衷|Ring-LWE|Lyubashevsky, Peikert & Regev, EUROCRYPT 2010, 1–23, doi:10.1007/978-3-642-13190-5_1|代数结构是否给攻击者额外捷径|模格方案以更保守结构在效率与安全间折衷|环结构把密钥和运算压到多项式维度|环LWE保留格困难性框架并显著提升存储与乘法效率，使实际协议可行|结构性子域攻击与参数误配提醒不能把普通LWE安全结论无条件搬用
SPHINCS无状态哈希签名|SPHINCS|Bernstein et al., EUROCRYPT 2015, 368–397, doi:10.1007/978-3-662-46800-5_15|巨大签名和计算成本能否换取保守安全假设|SLH-DSA继承无状态哈希签名路线进入FIPS 205|只依赖哈希函数避免格结构风险|SPHINCS用少量树与一次性签名组合，在无需维护状态时提供量子抗性|签名尺寸和速度限制高吞吐用途，错误的随机化与域分离仍会破坏实现
SIDH同源交换|SIDH|De Feo, Jao & Plût, Journal of Mathematical Cryptology 8, 209–247 (2014), doi:10.1515/jmc-2012-0015|超紧凑密钥能否抵抗利用辅助扭点信息的结构攻击|2022年SIKE被攻破成为标准化反面教材|超奇异同源图提供不同于格的密钥交换|SIDH展示椭圆曲线同源可构成量子抗密钥协商并带来很小公钥|安全依赖的特殊结构后来被直接利用，参数加大无法修复算法根本缺陷
NewHope混合试验|NewHope|Alkim et al., USENIX Security 2016, 327–343|浏览器与服务器能否承受格密钥交换的带宽和实现复杂度|真实协议混合部署成为标准迁移的预演|后量子与传统交换组合进入互联网实验|NewHope把环LWE密钥交换做成可部署实现并在Chrome实验中检验延迟与互操作|混合握手只在组合逻辑正确时继承至少一方安全，降级和解析错误会反转结论
NIST标准化启动|NIST PQC Call|NIST Federal Register call for nominations, December 2016|公开竞赛能否同时评价数学、实现与知识产权|多轮分析最终形成三项FIPS并继续补充算法|统一接口让全球候选接受长期公开攻击|NIST程序把安全、性能、实现和多样性放在多年公开评估中，改变密码标准形成方式|竞赛存活不等于所有参数都安全，标准发布后仍需持续密码分析
CRYSTALS-Kyber|CRYSTALS-Kyber|Bos et al., 2017 NIST submission; IEEE EuroS&P 2018 implementation analyses|模块格效率是否值得接受结构化安全假设|Kyber经修订成为FIPS 203的ML-KEM|模格密钥封装平衡带宽与速度|Kyber在软件和硬件上提供较小握手开销，被选为通用后量子密钥封装基础|实现必须验证密文并恒定时间处理失败，否则反应攻击绕开格问题
CRYSTALS-Dilithium|CRYSTALS-Dilithium|Ducas et al., 2017 NIST submission and TCHES implementation studies|拒绝采样与大签名能否稳定部署|Dilithium经修订成为FIPS 204的ML-DSA|模格签名以简单保守实现取胜|Dilithium避免复杂高斯采样并在安全、速度和实现审计间取得标准化平衡|随机数、拒绝采样时序和密钥编码仍是侧信道与故障攻击入口
FrodoKEM保守格基线|FrodoKEM|Bos et al., ACM CCS 2016, 1006–1018, doi:10.1145/2976749.2978425|无环结构的保守性是否值得巨大的带宽成本|FrodoKEM继续作为结构更少的备选和研究基线|普通LWE降低代数结构依赖|FrodoKEM不用环或模结构，给出与结构化格方案不同的安全多样性|公钥、密文和计算开销较大，使移动端与高并发服务器部署困难
CECPQ互联网混合实验|CECPQ Experiments|Google Security Blog and Cloudflare deployment reports, 2016–2019|实验流量能否暴露实验室基准看不见的中间盒问题|TLS混合PQC已进入浏览器与CDN更广部署|真实互联网握手测量带宽与失败率|CECPQ把后量子交换嵌入TLS并与经典椭圆曲线组合，验证网络可行性|实验算法与最终标准不同，测得的成功不能免除重新迁移和资产盘点
SIKE结构性攻破|SIKE Break|Castryck & Decru, An Efficient Key Recovery Attack on SIDH, 2022 preprint and EUROCRYPT 2023|标准竞赛是否能及时淘汰数学结构缺陷|该攻破持续作为算法多样性与公开分析的核心案例|单核经典计算数小时恢复秘密|攻击利用公开辅助点构造同源信息，彻底击穿SIKE而非仅降低安全位数|它不能推出所有同源密码不安全，却证明小密钥和长期未破不等于稳健证据
2022主算法选择|NIST 2022 Selections|NIST, PQC Standardization Process Announces First Algorithms, 5 July 2022|选择公告是否被市场误读为标准已经可用|后续两年草案、参数和编码继续修改|Kyber、Dilithium、Falcon与SPHINCS+进入标准轨道|NIST明确通用KEM与三条签名路线，给迁移规划稳定方向|在最终FIPS前锁死旧提交版本会造成不兼容，采购必须绑定标准版本
ML-KEM成为FIPS 203|FIPS 203 ML-KEM|NIST FIPS 203, published 13 August 2024|标准参数与既有Kyber实现差异能否安全迁移|NIST持续发布勘误、测试向量与实现验证材料|三个参数集定义通用模格密钥封装|FIPS 203把算法、编码、检查和参数写成可认证规范，跨过候选阶段|仅替换算法库而不改证书、协议消息和密钥生命周期，系统仍不具备后量子安全
ML-DSA成为FIPS 204|FIPS 204 ML-DSA|NIST FIPS 204, published 13 August 2024|签名尺寸、确定性接口和侧信道能否兼容现有PKI|模块格签名测试与硬件实现进入合规阶段|三个安全类别定义主力后量子签名|FIPS 204将Dilithium路线标准化，为软件签名、证书与固件建立共同目标|证书链膨胀和验证峰值会压垮旧设备，数学安全不能补偿资源耗尽
SLH-DSA成为FIPS 205|FIPS 205 SLH-DSA|NIST FIPS 205, published 13 August 2024|保守哈希假设是否值得更大签名和较慢速度|SLH-DSA作为结构多样的备用签名进入部署评估|十二个参数集提供无状态哈希签名|FIPS 205让系统在模格之外保留只依赖哈希安全的标准选择|错误参数集与超大签名会造成带宽和拒绝服务风险，不能当作无成本保险
HQC第五算法选择|HQC Selection|NIST, NIST Selects HQC as Fifth Algorithm for Post-Quantum Encryption, 11 March 2025|码基KEM能否提供足够的实现成熟度和侧信道抵抗|HQC标准草案工作推进，作为ML-KEM备份|码基结构补足密钥封装算法多样性|NIST选择HQC为第二条KEM标准路线，以降低单一模格家族的系统性风险|标准尚在制定，预标准部署可能面对参数、编码和互操作变化
FN-DSA与FIPS 206|FN-DSA / FIPS 206|NIST PQC project status, updated 2026|紧凑签名能否控制浮点采样和实现复杂度|基于FALCON的FN-DSA草案FIPS 206仍在开发|NTRU格签名以小签名换复杂实现|FN-DSA路线为带宽敏感场景提供与ML-DSA不同的签名折衷|采样器和精度实现难审计，标准未定稿前不能把草案接口当作稳定产品
密码敏捷迁移|Cryptographic Agility Migration|NIST draft transition guidance and NSA CNSA 2.0, updated through 2025|资产盘点与协议依赖能否赶在先收集后解密风险之前|迁移时间表转向禁用旧算法、混合期与合规验证|把替换能力本身纳入安全控制|迁移指南要求识别算法库存、数据保密寿命、供应链与互操作依赖，使后量子转型成为系统工程|没有版本回退、遥测和撤销路径的硬切换会制造可用性事故并诱发不安全降级
"""),
    ),
    dict(
        no=547, slug="micro-nano-engineering-mems-nems", title="微纳工程与MEMS/NEMS",
        group="电子工程 · 微纳系统",
        description="从谐振传感、微流控和CMOS融合到柔性与可降解器件，追踪MEMS/NEMS二十年证据。",
        lede="微纳器件常在裸片上创造惊人的灵敏度，却在封装、漂移、读出和批量制造中失去方向。本面板把材料、结构、接口、封装与校准当作一个系统，追问纳米尺度的局部优势何时真正成为可重复工程。",
        thesis="MEMS/NEMS进步的单因是把尺度效应变成可制造且可封装的系统功能，而不是最小线宽或最高裸片灵敏度",
        outlook="未来五年要看异质集成、晶圆级真空封装和软硬材料接口能否把实验室NEMS的收益稳定带入量产与长期现场",
        extra_refs=[
            "Ekinci & Roukes, Nanoelectromechanical systems, Review of Scientific Instruments 76, 061101 (2005).",
            "Stemme, Resonant silicon sensors, Journal of Micromechanics and Microengineering 1, 113–125 (1991), historical context.",
            "Esashi, Wafer level packaging of MEMS, Journal of Micromechanics and Microengineering 18, 073001 (2008).",
            "Microsystems & Nanoengineering, Integrating MEMS and ICs, 1, 15005 (2015).",
        ],
        items=records(r"""
NEMS谐振质量传感|NEMS Resonant Mass Sensing|Yang et al., Nano Letters 6, 583–586 (2006), doi:10.1021/nl052134m|频率漂移能否唯一归因于吸附质量|单分子与大阵列质量谱继续推进|吸附质量改变纳米谐振器本征频率|纳米梁的极小有效质量让微小吸附产生可测频移，打开超灵敏机械质量计量|温度、表面应力和模态形状同样移动频率，裸频移不是无歧义质量
纳米线压力与生物传感|Nanowire Piezoresistive Sensors|He & Yang, Nature Nanotechnology 1, 42–46 (2006), doi:10.1038/nnano.2006.53|巨压阻系数能否在接触电阻和封装应力下保持|纳米线传感转向阵列、表面功能化与低噪读出|尺寸效应放大机械到电学转换|硅纳米线显示显著压阻响应，提供微小力和生物结合事件的电读出路线|掺杂、接触和表面态会随工艺批次变化，单根器件结果难直接量产
晶圆级MEMS封装|Wafer-Level MEMS Packaging|Esashi, Journal of Micromechanics and Microengineering 18, 073001 (2008), doi:10.1088/0960-1317/18/7/073001|封装能否不改变真空、应力和运动间隙|键合、通孔与吸气剂成为惯性和谐振器量产基础|在切割前完成气密保护和电互连|晶圆级封装把逐颗装配变成批量工艺，显著降低微机械器件成本|键合温度、残余气体和封装应力会重写裸片性能，封装不是中性外壳
石墨烯纳米谐振器|Graphene Nanomechanical Resonator|Bunch et al., Science 315, 490–493 (2007), doi:10.1126/science.1136836|原子薄膜高频是否伴随不可控张力和非线性|二维材料谐振器扩展到异质层、应变与量子极限|极低质量与高强度形成可调机械膜|悬空石墨烯膜展示射频机械共振和栅压调谐，建立二维NEMS路线|残胶、边界夹持和热涨落决定品质因数，理想材料常数不能预测器件
微流控大规模集成|Microfluidic Large-Scale Integration|Thorsen, Maerkl & Quake, Science 298, 580–584 (2002), doi:10.1126/science.1076996|阀门数量增加是否带来同等实验可靠性|器官芯片和单细胞自动化继续继承多层软光刻|弹性阀把流体操作编程化|多层软光刻在芯片上集成大量阀与反应室，使复杂生化流程可自动编排|PDMS吸附、蒸发和气体渗透会改变浓度，布局规模不等于化学保真度
CMUT超声阵列|Capacitive Micromachined Ultrasonic Transducers|Haller & Khuri-Yakub, IEEE UFFC 43, 1–8 (1996), doi:10.1109/58.484478|微加工换能器能否在带宽、输出压与可靠性上胜过压电|CMUT进入医学成像、超声指纹与片上电子集成|电容膜阵列实现宽带声电转换|微机械薄膜让超声阵列可用半导体工艺制造并与前端电子靠近|塌陷电压、介质充电和液体封装会压缩长期动态范围
微型能量采集|MEMS Energy Harvesting|Roundy, Wright & Rabaey, Kluwer, Energy Scavenging for Wireless Sensor Networks (2004)|环境振动的窄带与间歇性是否支持自治节点|宽带、非线性和多源采集继续寻找可用功率|机械共振把环境振动转成电能|微机械压电、电磁和静电结构为无电池传感提供局部能源路径|实验室共振峰若不匹配现场频谱，平均采能低于电源管理静态损耗
惯性传感闭环|MEMS Inertial Closed Loop|Yazdi, Ayazi & Najafi, Proceedings of the IEEE 86, 1640–1659 (1998), doi:10.1109/5.704269|闭环力反馈能否抑制非线性而不增加电子噪声|消费级惯性单元推动多轴融合与在线校准|力平衡把位移读出转成反馈量|闭环加速度计和陀螺仪用静电反馈扩大线性范围并提高可控性|偏置漂移、封装应力和温度迟滞决定导航误差，短时噪声密度不足以验收
NEMS单分子质量谱|Single-Molecule NEMS Mass Spectrometry|Naik et al., Nature Nanotechnology 4, 445–450 (2009), doi:10.1038/nnano.2009.152|单次频率跳变能否同时识别质量与落点|多模态反演和阵列吞吐成为核心改进|单个分子吸附事件逐次计量|纳米谐振器解析离散吸附带来的频率阶跃，将质量谱从离子轨迹改为机械称量|吸附位置和分子脱附会混淆质量，低通量难以替代传统质谱
器官芯片机械微环境|Organ-on-Chip Mechanics|Huh et al., Science 328, 1662–1668 (2010), doi:10.1126/science.1188302|微流控仿生是否能代表完整器官免疫与代谢|器官芯片进入多器官耦合与监管验证|周期拉伸与气液界面重建肺泡环境|芯片把流体剪切和呼吸机械应变加入细胞培养，产生静态培养看不到的反应|材料吸附、细胞来源和缺失系统性循环限制外推，仿形不等于生理等价
光机MEMS可调系统|Optomechanical MEMS|Aspelmeyer, Kippenberg & Marquardt, Reviews of Modern Physics 86, 1391–1452 (2014), doi:10.1103/RevModPhys.86.1391|高光机耦合能否承受吸收热和制造失配|腔光机系统连接量子传感、微波转换与片上光学|光压与微结构运动形成双向控制|微纳腔把光场和机械模态强耦合，使位移读出和冷却进入量子极限附近|吸收热、光学损耗和频率失配会使高理论耦合在封装后消失
MEMS与IC异质集成|MEMS-IC Integration|Fischer et al., Microsystems & Nanoengineering 1, 15005 (2015), doi:10.1038/micronano.2015.5|单片与键合集成谁真正降低系统寄生和成本|晶圆键合、硅通孔与先进封装形成多条集成路线|传感结构与读出电子共同设计|综述比较前端、后端和晶圆键合集成，显示系统收益取决于工艺热预算与接口|靠近电子虽降低寄生，却可能牺牲MEMS材料、良率或可替换性
微机械非线性计算|Mechanical Nonlinear Computing|Mahboob & Yamaguchi, Nature Nanotechnology 3, 275–279 (2008), doi:10.1038/nnano.2008.84|利用非线性是否会放大制造差异与初值敏感|机械逻辑、储备计算和内存器件继续探索|非线性模态直接承担信息处理|耦合微机械模态展示可控非线性动力学，使传感器不只输出模拟读数|分岔附近虽高灵敏却低鲁棒，噪声和漂移会把计算状态推过错误吸引子
可溶解瞬态电子系统|Transient Electronics|Hwang et al., Science 337, 1640–1644 (2012), doi:10.1126/science.1226325|可降解时间表能否与功能寿命和毒理相匹配|可吸收传感器进入术后监测和环境设备|材料按设计时间溶解减少取出手术|超薄硅、金属与可溶基底构成在水环境逐步消失的电子系统|降解产物、封装裂纹和个体体液差异会让消失过早或残留过久
柔性表皮电子|Epidermal Electronics|Kim et al., Science 333, 838–843 (2011), doi:10.1126/science.1206157|贴合皮肤是否足以保证长期信号与生物相容|柔性传感发展到无线、无电池和多模态贴片|超薄蛇形互连匹配皮肤力学|器件以低弯曲刚度贴合表皮，获得传统刚性电极难有的舒适信号界面|汗液、运动、粘合剂和重复使用改变接触阻抗，短时演示不能代表长期佩戴
微流控汗液传感|Microfluidic Sweat Sensing|Koh et al., Science Translational Medicine 8, 366ra165 (2016), doi:10.1126/scitranslmed.aaf2593|汗液浓度能否代表血液状态且不受汗率控制|可穿戴化学传感转向采样时间、校准与临床配对|软微流道定时采集并显色多种汗液指标|贴片把采样、储液和比色读出整合，减少开放汗液蒸发污染|汗腺个体差异和滞后会令相关性反号，生物标志物必须做同步血液验证
大规模NEMS质量阵列|Large-Scale Nanomechanical Mass Sensors|Sage et al., Nature Communications 9, 3283 (2018), doi:10.1038/s41467-018-05783-4|阵列并行是否能克服单器件低通量与失配|频率寻址和片上读出继续扩展机械谱仪|多谐振器并行提高颗粒计量吞吐|大阵列与多模反演把NEMS质量传感从单器件推进到统计测量|器件频率分散、坏点和共享读出串扰会让名义阵列规模大于有效通道数
压电MEMS射频滤波|Piezoelectric MEMS RF Filters|Ruby, 2017 IEEE Ultrasonics Symposium tutorials and commercial acoustic-filter literature|高品质因数能否在高功率和温漂下保持|薄膜体声波与铌酸锂器件进入更高频段|机械声学谐振选择无线频带|微纳压电结构以小尺寸高选择性替代部分电磁滤波，成为移动射频前端核心|功率密度、频率温漂和封装寄生在新频段会吞噬实验室品质因数
量子极限机械力传感|Quantum-Limited Mechanical Sensing|Teufel et al., Nature 475, 359–363 (2011), doi:10.1038/nature10261|接近基态是否带来室温或宽带传感净优势|微波光机冷却与反作用规避继续逼近量子极限|机械振子冷却到平均占据数接近零|强微波腔耦合把微机械运动冷却到量子基态附近，使量子反作用成为实测对象|稀释制冷与窄带条件成本很高，不能从基态直接推出实用传感器领先
软体MEMS与液态金属|Soft MEMS and Liquid-Metal Sensors|Dickeya, Advanced Materials 29, 1606425 (2017), doi:10.1002/adma.201606425|极端拉伸是否以迟滞、泄漏和封装寿命为代价|软机器人和可穿戴器件继续发展可修复导体|液态导体随弹性通道形变保持连通|液态金属微通道使大应变传感与可重构电路成为可能|氧化皮、通道疲劳和液态金属泄漏会改变标定并引入安全责任
"""),
    ),
    dict(
        no=548, slug="computer-engineering-hardware-software-codesign", title="计算机工程与软硬件协同设计",
        group="电子工程 · 计算系统",
        description="从CUDA、Roofline和暗硅到TPU、RISC-V、CXL与Chipyard，审计软硬件协同设计二十年。",
        lede="软硬件协同设计不是让软件迁就一颗新芯片，也不是让硬件追逐一个短命模型；它要求算法、编译器、存储层次、互连和可靠性共享一套工作负载证据。本面板用二十个节点追问：专用化何时带来净收益，何时只是把成本移到软件与供应链。",
        thesis="协同设计的单因是跨层暴露并消除真实工作负载的主瓶颈，而不是某一层峰值算力增加",
        outlook="未来五年要看开放指令、芯粒互连和领域编译器能否形成可移植性能，同时把安全、能耗与维护写进共同目标",
        extra_refs=[
            "Hennessy & Patterson, A New Golden Age for Computer Architecture, Communications of the ACM 62, 48–60 (2019).",
            "Sze et al., Efficient Processing of Deep Neural Networks: A Tutorial and Survey, Proceedings of the IEEE 105, 2295–2329 (2017).",
            "Computer Architecture Research Opportunities Task Force, 21st Century Computer Architecture, 2012 report.",
            "MLCommons, MLPerf Inference, Training and Power benchmark rules, current editions.",
        ],
        items=records(r"""
MapReduce数据局部性|MapReduce|Dean & Ghemawat, OSDI 2004, 137–150|通用批处理抽象是否掩盖网络洗牌与长尾节点|数据流系统继续以调度和容错重写计算位置|把计算移动到数据并自动恢复任务|MapReduce把大规模数据处理压成映射和归约，使运行时可安排局部性、重试与分片|迭代算法和低延迟任务会被反复落盘拖慢，抽象简洁不等于所有工作负载高效
CUDA可编程并行|CUDA Programmability|NVIDIA, CUDA Programming Guide, first public release 2007|专有编程模型的性能收益是否形成长期锁定|GPU编程扩展到统一内存、张量核心与多厂商编译层|大量线程暴露数据并行硬件|CUDA让开发者用接近C的模型调度GPU线程、共享存储与内存层次，改变通用加速计算|高性能代码依赖架构细节和工具链，移植成本必须与加速比同账
Roofline性能模型|Roofline Model|Williams, Waterman & Patterson, Communications of the ACM 52, 65–76 (2009), doi:10.1145/1498765.1498785|算术强度和峰值带宽能否解释不规则系统行为|分层Roofline进入CPU、GPU和性能工具|用算术强度定位计算或内存瓶颈|模型把可达性能限制在峰值计算与带宽两条屋顶下，使优化先找主约束|缓存、延迟、并发和通信会使单一带宽线失真，模型是诊断起点而非预测真值
暗硅约束|Dark Silicon|Esmaeilzadeh et al., ISCA 2011, 365–376, doi:10.1145/2000064.2000108|功率墙是否会让更多晶体管无法同时开启|异构与专用加速成为暗硅时代的主响应|晶体管增加快于可供电面积|分析显示电压缩放放缓后，芯片不能以最高频率同时使用全部晶体管，推翻面积等于性能的默认|模型依赖工艺和冷却假设，但功率密度约束不会由更多核心自动消失
RISC-V开放指令集|RISC-V ISA|Waterman et al., EECS Department, UC Berkeley, Technical Report UCB/EECS-2014-54|开放ISA能否兼顾扩展自由与软件生态稳定|RISC-V已形成基础规范、向量和安全扩展的全球生态|把指令接口从单一厂商授权中解耦|精简稳定的基础加可选扩展让教学、研究和产品共享架构接口，降低定制处理器门槛|碎片化扩展、验证与软件支持会把开放许可优势转成兼容成本
高层综合重新进入主流|High-Level Synthesis|Cong et al., IEEE Transactions on CAD 30, 473–491 (2011), doi:10.1109/TCAD.2011.2110590|从C到电路能否同时保留时序、面积和可预测性|HLS进入FPGA、AI加速与硬件生成器工作流|编译器把循环和数据流变成微结构|高层综合允许设计者用高级语言探索流水线、并行和存储结构，缩短定制硬件迭代|源代码语义不包含完整硬件意图，指令和约束细节仍决定结果质量
近似计算|Approximate Computing|Esmaeilzadeh et al., ASPLOS 2012, 1–12, doi:10.1145/2150976.2150978|应用容错能否安全转换为硬件误差预算|近似路线转向可验证质量、概率硬件与机器学习|允许受控误差交换能耗和吞吐|研究用神经加速和不精确执行说明部分应用不需位精确，可回收过度保守资源|误差会跨流水线累积并伤害少数样本，平均质量不能代替最坏情况责任
Eyeriss数据流|Eyeriss DNN Accelerator|Chen et al., IEEE Journal of Solid-State Circuits 52, 127–138 (2017), doi:10.1109/JSSC.2016.2616357|减少数据移动是否比增加乘加单元更决定能效|空间加速器继续围绕权重、激活和部分和复用设计|行驻留数据流压低存储访问|Eyeriss把卷积映射到处理阵列并复用多类数据，证明访存能耗可主导神经网络加速器|层形状和稀疏模式改变复用收益，单一卷积基准不能代表整网
SCNN稀疏加速|SCNN|Parashar et al., ISCA 2017, 27–40, doi:10.1145/3079856.3080254|压缩稀疏表示的索引成本能否小于跳零收益|结构化稀疏和动态稀疏硬件继续分化|只对非零权重与激活做乘加|SCNN用压缩数据流避开大量零值运算，展示算法稀疏可直接转成硬件效率|不规则索引、负载失衡和小批量会吞噬理论节省，稀疏率不是充分量纲
TPU领域专用架构|Tensor Processing Unit|Jouppi et al., ISCA 2017, 1–12, doi:10.1145/3079856.3080246|生产工作负载优势是否可迁移到模型快速演化之后|TPU世代扩展到训练、稀疏和大型互连|脉动阵列围绕张量运算重排数据|首代TPU针对数据中心推理，以大矩阵单元和片上存储获得显著性能功耗收益|结果依赖谷歌模型与部署栈，硬件固定功能可能在算子变化后形成利用率债务
领域专用黄金时代|Domain-Specific Architectures|Hennessy & Patterson, Communications of the ACM 62, 48–60 (2019), doi:10.1145/3282307|专用化收益能否抵消软件、验证和市场碎片化|芯粒与可生成加速器成为控制专用化成本的路线|摩尔定律放缓后跨层定制重新主导|图灵奖演讲把领域专用架构、开源指令和敏捷硬件列为新黄金时代支柱|没有足够稳定工作负载和工具链，专用芯片可能在摊销前过时
TVM张量编译|TVM|Chen et al., OSDI 2018, 578–594|自动调优能否跨硬件找到稳定而非偶然最优|MLIR、XLA和厂商编译器继续发展多层表示|把算子语义与硬件调度搜索分离|TVM用张量表达、调度和成本模型自动生成多后端内核，降低手写优化依赖|搜索预算、基准噪声和算子融合规则会使结果难复现，编译时间也是系统成本
模拟存内计算|Analog In-Memory Computing|Ambrogio et al., Nature 558, 60–67 (2018), doi:10.1038/s41586-018-0180-5|器件变异与数据转换能否不吃掉阵列级能效|存内计算转向端到端精度、校准和混合数字架构|在存储阵列内完成矩阵向量乘|相变存储交叉阵列用物理电导并行累加，减少权重往返处理器的数据移动|模数转换、写入漂移和校准在系统级占比很高，阵列TOPS每瓦不是应用能效
Spectre跨层安全漏洞|Spectre|Kocher et al., IEEE Symposium on Security and Privacy 2019, 1–19, doi:10.1109/SP.2019.00002|性能推测能否与架构隔离同时成立|缓解措施持续在微码、编译器和操作系统间移动|微架构状态泄露越过软件权限|Spectre证明合法推测执行可通过缓存侧信道泄露被权限保护的数据，打破ISA足够定义安全的预设|修复若只在一层可能被变体绕过，性能代价也会改变原设计优势
高带宽内存|High Bandwidth Memory|JEDEC JESD235 HBM standards, 2013 onward|堆叠带宽是否受容量、热与封装良率反噬|HBM3E与先进封装成为AI系统关键供给约束|硅通孔堆叠扩大每瓦内存带宽|HBM将多层DRAM靠近处理器并用宽接口通信，缓解高并行计算的数据供给|容量价格、热密度和封装瓶颈会让峰值带宽难以持续，供应链也进入架构账
芯粒模块化|Chiplet-Based Systems|AMD EPYC and Intel package disclosures; DARPA CHIPS program, 2017 onward|模块复用能否抵消互连延迟、封装与已知良品管理|UCIe推动封装内互连标准化|把大单片拆成可组合裸片|芯粒允许不同工艺节点和功能在同一封装组合，提高复用并避免最大单片良率风险|裸片测试、协议一致性和热机械耦合会把局部良率优势转成封装复杂度
CXL内存语义互连|Compute Express Link|CXL Consortium, CXL 1.0 Specification (2019) and later revisions|缓存一致性共享能否在延迟、隔离与故障域扩大后保持|CXL 2.0与3.x推进内存池化和交换网络|统一CPU、加速器与扩展内存协议|CXL把缓存、内存和I/O语义整合在PCIe物理层上，支持更灵活的内存组合|协议层统一不消除非一致延迟和多租户安全，池化容量不等于本地内存性能
机密计算|Confidential Computing|AMD SEV, Intel TDX and Confidential Computing Consortium specifications, 2016 onward|可信执行环境能否抵抗侧信道与供应链固件漏洞|云端机密虚拟机进入证明、密钥管理与加速器保护|硬件隔离运行中数据免受宿主读取|内存加密和受保护虚拟机把信任边界从整个云管理栈缩到硬件与小型固件|侧信道、回滚和证明服务仍可能泄露，保密不自动提供完整性与可用性
Chipyard敏捷协同设计|Chipyard|Amid et al., IEEE Micro 40, 10–21 (2020), doi:10.1109/MM.2020.2996616|生成器生态能否让学术原型达到可验证硅实现|开源SoC生成、仿真和FPGA原型继续形成共同平台|从参数化RTL到软件栈共生成|Chipyard组合Rocket、BOOM、加速器和外围，让研究者在统一环境评估软硬件变化|组件版本、物理实现和验证覆盖决定可复现性，生成成功不等于芯片正确
Gemmini可生成矩阵加速器|Gemmini|Genc et al., DAC 2021, 489–494, doi:10.1109/DAC18074.2021.9586216|参数化加速器能否在不同模型与工艺保持帕累托优势|开源加速器与编译器共同成为协同设计试验床|可配置数据流和存储层次贯通软件|Gemmini把矩阵阵列、片上存储、指令和软件接口参数化，支持从工作负载回推硬件|搜索空间巨大且物理实现反馈昂贵，RTL层最优配置可能在布线后反号
"""),
    ),
    dict(
        no=549, slug="integrated-circuit-design-eda", title="集成电路设计与EDA", group="电子工程 · 芯片设计",
        description="从多图形化、FinFET和EUV到OpenROAD、开源PDK、机器学习布局与3D集成，审计EDA二十年。",
        lede="集成电路设计的前沿已经从“画出更多晶体管”转成“在制造、功耗、时序、验证和封装共同约束下收敛”。本面板特别区分工具跑完、规则通过和硅上兑现三种成功，避免把代理代价函数当成真正的芯片质量。",
        thesis="EDA进步的单因是让设计意图在多物理约束和制造反馈中更早收敛，而不是优化器分数单独变好",
        outlook="未来五年要看AI代理能否公开可复算基线，背面供电与3D混合集成能否进入可信设计套件，以及开放工具如何承担签核责任",
        extra_refs=[
            "Kahng, Classical Floorplanning Harm: Is AI Better and Why?, ACM/IEEE design automation analyses (2023–2024).",
            "OpenROAD Project, Toward a self-driving, open-source digital layout implementation tool chain, government and conference reports.",
            "IEEE International Roadmap for Devices and Systems, More Moore and Systems Integration chapters, current edition.",
            "UCIe Consortium, Universal Chiplet Interconnect Express specifications, 2022 onward.",
        ],
        items=records(r"""
高介电常数金属栅|High-k Metal Gate|Mistry et al., IEEE International Electron Devices Meeting 2007, 247–250|新栅堆叠能否在迁移率、可靠性和工艺整合中保持收益|高介电栅成为先进CMOS后续结构共同基础|降低栅漏同时维持栅控|铪基介质与金属栅替代极薄氧化层，使继续缩放不必接受指数增加的隧穿漏电|阈值控制、界面缺陷和应力会改变器件收益，材料常数不能直接等于产品功耗
双重图形化设计规则|Double Patterning-Aware Design|Chiou et al., DAC 2008 and subsequent decomposition literature|版图着色约束会不会在设计末端才制造不可解冲突|多图形化与自对准工艺推动规则进入布局布线前端|把一个密集层分解到多次曝光|双重图形化延续193纳米光刻的分辨能力，也迫使EDA处理颜色、间距与拼接|分解可行不等于叠加误差可控，修复颜色冲突可能恶化时序和面积
FinFET进入量产设计|FinFET Production Design|Auth et al., IEEE VLSI Technology Symposium 2012; 22-nm tri-gate disclosures|三维栅控收益能否抵消寄生、电阻和模型复杂度|FinFET成为多代先进逻辑节点主结构|多面栅提高静电控制降低短沟道效应|量产三栅器件让晶体管缩放从平面转向三维，改变标准单元与器件模型|离散鳍数限制宽度选择，局部互连和变异会吞噬器件级增益
硅通孔三维集成|TSV 3D Integration|Patti, Proceedings of the IEEE 94, 1214–1224 (2006), doi:10.1109/JPROC.2006.873612|垂直互连缩短是否值得热、应力和测试复杂度|TSV用于HBM和异质集成，同时与混合键合分工|堆叠裸片缩短芯片间数据路径|硅通孔把多层裸片以高密度垂直连接，为内存带宽和异构集成打开新结构|热热点、应力迁移率和已知良品测试会使三维收益在封装后反号
Chisel硬件生成器|Chisel|Bachrach et al., DAC 2012, 1212–1221, doi:10.1145/2228360.2228584|高级生成抽象能否保持RTL可审计和工具兼容|参数化硬件生态扩展到RISC-V和开源SoC|用宿主语言构造可复用硬件族|Chisel让设计者以参数和类型生成RTL，降低复制粘贴并支持架构空间探索|生成链增加调试层次，版本变化和隐式结构可能让签核问题更难定位
计算光刻|Computational Lithography|Cobb et al., SPIE optical proximity correction literature and production OPC, 2000s onward|掩模修正复杂度是否能持续弥补光学分辨率缺口|源掩模协同优化与机器学习光刻继续推进|用逆向计算预失真掩模图形|光学邻近修正把制造成像模型带入版图，延长既有曝光波长寿命|模型误差和掩模复杂度会增加写入、检验和缺陷成本，仿真轮廓不是晶圆真值
形式等价检查|Formal Equivalence Checking|Kuehlmann & Krohm, DAC 1997 and industrial SAT-based equivalence practice|优化后网表能否证明保持设计意图|等价检查成为综合、ECO和低功耗变换的签核闸门|用逻辑证明替代有限测试向量|形式等价让大规模重写和门级优化可在全输入空间核对功能|黑盒、未定义行为和模拟宏单元会把证明范围切碎，工具通过不等于整个芯片被证明
统计时序分析|Statistical Static Timing Analysis|Blaauw et al., IEEE TCAD 27, 589–607 (2008), doi:10.1109/TCAD.2007.907047|相关工艺变异能否被低维分布准确表示|多角多模签核与变化感知优化共同发展|把延迟从固定角落改写为随机变量|统计时序试图用分布与相关性减少过度悲观，直接量化良率与时序风险|分布尾部和空间相关模型错误会给出虚假签核置信，工业流程因而仍依赖角落
EUV进入高量产|EUV High-Volume Manufacturing|ASML and leading-foundry disclosures, 2019 onward; IEEE IEDM process reports|减少多重图形化是否被随机缺陷和掩模成本抵消|高数值孔径EUV把新随机性与设计规则带入路线图|十三点五纳米曝光简化关键层图形化|EUV在先进节点量产，减少部分复杂分解与掩模次数，改变设计制造协同|光子随机性、抗蚀剂粗糙和掩模三维效应要求新的缺陷和良率模型
Design-Technology Co-Optimization|DTCO|IEEE IRDS and imec DTCO publications, 2013 onward|标准单元与工艺共同优化会不会过早锁死架构选择|DTCO扩展到系统技术协同优化|在节点定型前用设计指标约束器件工艺|DTCO让接触、轨高、互连和单元库以芯片功耗性能面积共同裁决，而非只看晶体管|代表性设计若选错，工艺会为局部工作负载优化并牺牲其他产品
OpenROAD自动布局流水线|OpenROAD|Kahng, IEEE Design & Test 36, 8–13 (2019), doi:10.1109/MDAT.2019.2906634|无人干预布局能否达到可签核质量且可复算|OpenROAD持续形成开放RTL到GDS工具链|把数字后端流程变成可脚本化公共基础设施|项目以自主化和开放实现降低先进EDA研究进入门槛，使论文可在共同流程比较|开放工具输出仍依赖商业或代工签核模型，跑到GDS不等于制造责任完成
开源SkyWater 130纳米PDK|Open SkyWater PDK|Google and SkyWater, open-source SKY130 PDK release, 2020|开放规则是否包含足够精度支持可靠流片|开放MPW与教育芯片验证形成真实反馈|首次广泛开放可制造工艺设计套件|SKY130让任何团队查看规则、器件模型与标准单元并用开放工具完成芯片|成熟节点经验不能直接外推先进节点，模型许可开放也不保证所有可靠性角落齐全
机器学习芯片布局|ML for Chip Placement|Mirhoseini et al., Nature 594, 207–212 (2021), doi:10.1038/s41586-021-03544-w|强化学习结果是否优于充分调优的经典基线|复现、数据泄漏与工业使用声明引发持续争议|以图策略快速放置宏单元|方法用强化学习从芯片网表生成宏布局，并报告在若干加速器块上达到或超过人工指标|基线预算、训练芯片相似性和代理代价会改变结论，最终布线与硅后结果才是裁决
门全环绕纳米片|Gate-All-Around Nanosheets|Loubet et al., Symposium on VLSI Technology 2017, T230–T231|可变片宽的电学收益能否抵消制造与寄生复杂度|GAA进入三纳米级量产并向堆叠互补器件推进|栅极完整包围沟道恢复静电控制|水平纳米片提供比FinFET更灵活的有效宽度和更强栅控，开启新一代标准单元|内间隔层、源漏电阻和片间变化会限制器件模型理想收益
UCIe芯粒标准|UCIe|UCIe Consortium, UCIe 1.0 Specification (2022)|标准物理与协议接口能否真正形成多供应商芯粒市场|UCIe 2.0增加管理、可靠性与3D封装支持|封装内互连从厂商私有走向共同规范|UCIe统一电气、协议与封装配置，使芯粒设计可讨论跨厂商互操作|已知良品、信任、热和机械规范仍未因链路标准化而自动解决
背面供电网络|Backside Power Delivery|imec and Intel VLSI/IEDM disclosures, 2019–2024|电源移到晶圆背面能否在通孔、热与良率后保留布线收益|背供电进入量产路线并与背面信号研究相接|电源与正面信号布线分离|背面供电减少正面电源拥塞和压降，为更密标准单元释放信号资源|纳米通孔电阻、对准和故障分析变难，前端收益可能转成制造风险
混合键合三维互连|Hybrid Bonding|IEEE ECTC and leading-foundry hybrid-bonding reports, 2016 onward|微米级连接密度能否在大面积实现足够良率|图像传感、缓存堆叠和逻辑三维集成扩展应用|铜到铜与介质键合缩小垂直互连间距|混合键合绕开传统微凸点尺寸，使更多跨层信号与存储带宽可用|表面颗粒、翘曲和热失配会随面积放大，单连接良率必须换算到整片
模拟版图自动化|Analog Layout Automation|ALIGN open-source project, DAC 2021 and DARPA IDEA program|模拟约束能否被机器表示而不丢失设计师隐性知识|生成式与约束驱动模拟EDA继续推进|把匹配、对称和寄生要求显式编码|ALIGN等项目尝试从网表和约束自动生成模拟版图，缩短人工反复布局|器件环境、寄生耦合和可制造经验难以完全形式化，规则齐全仍可能性能失真
硬件安全验证|Hardware Security Verification|Hicks et al., CHERI and information-flow verification literature, 2010s onward|功能正确是否足以推出无信息泄露|硬件木马、侧信道和权限架构进入EDA检查目标|把安全属性作为设计期可证明约束|信息流和能力架构研究把秘密能否流向未授权端口写成形式属性|微架构时序、模拟效应和第三方IP会超出抽象模型，证明边界必须公开
AI代理式EDA|Agentic AI for EDA|2023–2026 LLM-for-EDA and industrial copilot evaluations|代码生成速度是否能超过新增验证与来源风险|工具调用代理开始覆盖RTL、脚本、调试与设计空间探索|自然语言代理编排多阶段设计工具|代理可生成约束、调用综合、解释报告并迭代候选，降低跨工具操作摩擦|幻觉RTL、训练数据版权和奖励黑客会把节省的编辑时间转成更大验证债务
"""),
    ),
    dict(
        no=550, slug="6g-future-networks", title="6G与未来网络", group="信息工程 · 未来通信",
        description="从SDN、海量MIMO与毫米波到IMT-2030、通感一体和AI原生网络，审计未来网络二十年。",
        lede="6G不是把5G峰值速率再写大一位，而是通信、感知、计算、控制与覆盖开始争夺同一时频能量和责任预算。本面板以ITU IMT‑2030框架为最新锚，逐项分开愿景、候选技术、标准要求和可运营网络。",
        thesis="未来网络的单因是让异构链路、计算和感知在端到端服务约束下可编排，而不是空口峰值单独提高",
        outlook="未来五年要看2027至2029年IMT-2030候选提交能否按二十项最低性能要求、三种评估方法和七类环境统一测试，并处理能耗、覆盖与AI控制责任",
        extra_refs=[
            "ITU-R M.2160-0, Framework and overall objectives of the future development of IMT for 2030 and beyond (2023).",
            "ITU-R, IMT-2030 technical performance requirements and evaluation methodology work programme, 2024–2026.",
            "3GPP, Release 18 and Release 19 work plans for 5G-Advanced, NTN, sensing and AI/ML.",
            "Next G Alliance and Hexa-X-II, 6G system architecture, sustainability and societal requirements reports.",
        ],
        items=records(r"""
OpenFlow与软件定义网络|OpenFlow SDN|McKeown et al., ACM SIGCOMM CCR 38, 69–74 (2008), doi:10.1145/1355734.1355746|控制与转发分离是否制造新的集中故障与攻击面|可编程数据平面和意图网络继续扩展SDN原则|开放接口让控制逻辑脱离专有交换机|OpenFlow把流表控制暴露给外部软件，使网络策略可快速实验和集中编排|控制器延迟、状态一致性和错误策略会跨全网放大，逻辑集中不等于物理单点可接受
海量MIMO|Massive MIMO|Marzetta, IEEE Transactions on Wireless Communications 9, 3590–3600 (2010), doi:10.1109/TWC.2010.092810.091092|无限天线渐近增益能否承受导频污染与硬件误差|大规模阵列已成为5G并继续进入分布式MIMO|许多天线平均小尺度衰落并做空间复用|理论显示基站天线数大增可同时服务多用户并提高频谱与能量效率|导频、校准、互耦和边缘用户会让有限阵列偏离渐近结论
毫米波蜂窝|Millimeter-Wave Cellular|Rappaport et al., IEEE Access 1, 335–349 (2013), doi:10.1109/ACCESS.2013.2260813|巨大带宽能否抵抗遮挡、穿透损耗与波束开销|毫米波已进入5G高频段并为亚太赫兹提供传播经验|定向波束复用高频宽带资源|测量和系统分析证明毫米波可通过高增益阵列支持蜂窝通信，推翻不可用的旧判断|覆盖依赖视距、密集站点和波束追踪，峰值速率会在移动遮挡时反号
网络功能虚拟化|Network Functions Virtualization|ETSI NFV Industry Specification Group white paper, 2012|通用服务器灵活性是否抵消专用设备的确定时延|云原生网络功能与服务网格继续重写电信核心网|把防火墙和核心网功能从专用盒子移到软件|NFV让网络功能可按需部署、扩缩和编排，缩短服务上线周期|抖动、NUMA、虚拟交换和故障级联会伤害电信级可靠性，实例启动不是服务就绪
边缘计算|Edge Computing|Satyanarayanan, Computer 50, 30–39 (2017), doi:10.1109/MC.2017.9|靠近用户是否一定降低端到端时延与能耗|多接入边缘与云边协同成为实时应用基础设施|把计算和数据放到接入侧|边缘节点减少广域往返并支持位置相关服务，把网络拓扑变成应用设计变量|小站资源、缓存未命中和跨边缘迁移可能比中心云更慢更耗能
网络切片|Network Slicing|NGMN Alliance, Description of Network Slicing Concept, 2016; 3GPP system architecture work|逻辑隔离能否在共享无线与传送资源上给出硬保证|切片管理进入5G专网和端到端编排|同一基础设施承载差异化服务目标|切片用虚拟网络实例映射不同可靠性、时延和安全要求，改变按网络整体售卖服务的方式|共享故障域和资源超售会使名义隔离失效，SLA必须穿透无线、传送与核心网
超可靠低时延通信|URLLC|Popovski et al., IEEE Network 32, 16–23 (2018), doi:10.1109/MNET.2018.1700258|极低时延与极高可靠性是否能在有限频谱同时保证|工业控制继续推动短包、冗余和确定性网络融合|用短包和多样性重写平均吞吐目标|URLLC把尾部时延和失败概率置于平均速率之上，使无线进入闭环控制|可靠性小数位若靠仿真外推且不含排队和应用处理，就不能代表端到端安全
无小区海量MIMO|Cell-Free Massive MIMO|Ngo et al., IEEE Transactions on Wireless Communications 16, 1834–1850 (2017), doi:10.1109/TWC.2017.2655515|分布式接入点协同能否承受前传与同步成本|用户中心簇和分布式处理成为6G候选结构|许多接入点共同服务每个用户消除小区边缘|架构用地理分散天线和联合处理平滑传统小区边界的服务差异|前传容量、时钟、功控和计算规模会限制协同范围，理论全局联合难直接部署
可重构智能表面|Reconfigurable Intelligent Surfaces|Di Renzo et al., IEEE Journal on Selected Areas in Communications 38, 2450–2525 (2020), doi:10.1109/JSAC.2020.3007211|被动反射增益能否超过信道估计和控制开销|RIS标准建模与现场测量开始检验规模规律|可编程表面把传播环境变成网络变量|大量可调单元改变反射相位，为遮挡覆盖和能量聚焦提供新自由度|双程路径损耗、离散相位和获取级联信道的成本会使理想平方增益失真
太赫兹通信|Terahertz Communications|Akyildiz, Jornet & Han, Physical Communication 12, 16–32 (2014), doi:10.1016/j.phycom.2014.01.006|超宽带是否被分子吸收、器件功率和极窄波束抵消|亚太赫兹器件和D波段链路进入IMT-2030候选研究|一百GHz以上频谱支持极高近距容量|路线图系统化太赫兹信道、器件与网络问题，打开超高速短距通信研究|链路距离、天气、相位噪声和波束发现决定可用场景，带宽大不等于覆盖广
非地面网络|Non-Terrestrial Networks|3GPP Release 17 NTN specifications, frozen 2022|卫星直连能否在长往返、频移和容量后提供普遍覆盖|Release 18与直连终端继续增强NR-NTN|把卫星和高空平台纳入蜂窝标准|3GPP为透明与再生载荷定义时序、移动性和信道适配，让普通网络栈延伸到天空|波束容量、网关可见性与终端功耗限制公平覆盖，地理可达不等于高质量服务
开放无线接入网|Open RAN|O-RAN Alliance specifications, 2018 onward|接口开放能否在多厂商组合下维持性能与安全|RIC应用、云化基站和一致性测试持续推进|拆分基站并开放控制与管理接口|O-RAN让无线单元、分布单元和控制器可由不同供应商组合，增加可编程性|接口选项、集成责任和供应链攻击面会扩大，厂商数增加不自动带来互操作
通感一体|Integrated Sensing and Communication|Liu et al., IEEE Journal on Selected Areas in Communications 40, 172–191 (2022), doi:10.1109/JSAC.2021.3125390|同一波形能否同时满足通信可靠与感知估计|3GPP和IMT-2030把感知列为未来网络能力|共享频谱、波形与阵列完成通信和环境测量|通感一体把基站从传输管道变成位置、速度和环境传感基础设施|通信数据和感知回波的最优波形不同，隐私与监控责任还会改变可部署性
语义通信|Semantic Communications|Xie et al., IEEE Transactions on Signal Processing 69, 2663–2675 (2021), doi:10.1109/TSP.2021.3071210|任务成功率能否替代比特正确且不造成意义操控|生成式模型推动语义编码同时放大鲁棒与治理争议|传输任务相关表示而非逐比特重建|深度语义系统在特定文本任务和低信噪比下减少传输负担，重开通信目标定义|发送端与接收端模型不一致、分布漂移或攻击会产生流畅但错误的意义
AI原生空口与网络|AI-Native Networks|ITU-T FG-ML5G reports and 3GPP AI/ML studies, 2019 onward|学习控制器能否在分布外事件中保持安全与可解释|IMT-2030把AI相关能力写入框架和性能讨论|学习模型进入信道估计、调度和运维闭环|AI原生路线让数据驱动组件不只辅助运维，也可能共同设计空口和跨域策略|训练数据、在线漂移和奖励黑客会把局部KPI优化转成全网不稳定
网络数字孪生|Network Digital Twin|IETF NMRG and ITU-T network digital twin architecture work, 2021 onward|孪生预测能否在拓扑与流量快速变化时保持校准|闭环验证与意图网络把孪生用于变更前试验|实时模型映射网络状态并模拟策略后果|数字孪生允许在生产变更前测试路由、容量与故障响应，降低直接试错风险|遥测缺失和模型简化会制造虚假安全，孪生通过不等于真实网络不会失效
IMT-2030总体框架|IMT-2030 Framework|ITU-R Recommendation M.2160-0, approved November 2023|愿景能力能否转成可比较且不过度单指标的技术要求|ITU已进入技术性能要求和评估方法阶段|六类使用场景与十五项能力构成全球框架|M.2160把沉浸通信、超可靠低时延、广泛连接、AI通信、通感和普遍连接纳入共同图景|框架是目标而非已部署标准，任何设备不能仅凭符合愿景宣称为6G
可持续未来网络|Sustainable Network Design|EARTH project results and 6G sustainability KPIs, 2010–2025|每比特能效提升能否抵消流量、站点和终端增长|IMT-2030讨论把环境可持续性纳入能力与评价|从设备功耗转向服务与生命周期能耗|网络研究从基站睡眠扩展到碳感知调度、设备寿命和端到端能耗|每比特下降伴随总流量反弹时总能耗仍增，不能只用归一化指标宣布绿色
联合通信计算控制|Joint Communication-Compute-Control|Park et al., IEEE Networked Control and edge-intelligence literature, 2019–2025|无线、计算和控制三个队列能否由同一策略稳定协调|机器人、车联网与数字孪生推动跨层闭环|以任务误差而非链路速率配置网络资源|联合设计让调度器依据推理截止期和控制稳定性决定传输、卸载与计算|模型误差和多主体竞争会使局部最优策略破坏闭环稳定，需端到端安全约束
IMT-2030技术要求与评估|IMT-2030 Requirements and Evaluation|ITU-R Working Party 5D, draft minimum technical performance requirements completed February 2026|二十项最低要求如何避免厂商选择性报告|六月完成三种评估方法与七类测试环境，候选接口将在2027至2029年提交|从愿景进入可度量候选系统门槛|要求覆盖二十项最低性能；评估指南把模拟、分析与检查分配到七类环境，并加入工厂高可靠低时延与通感场景|相关报告仍待2026年十二月由ITU-R第五研究组批准，不能误写成6G已定型上线
"""),
    ),
]


PARA_FORMS = [
    (
        "{title}由{propose}固定为一个可核验节点。它面对的旧问题不是设备不够新，而是{detail}。关键读数是“{key}”，因此历史位置必须连同对象、基线与失败样本一起读。",
        "本面板的单因判断是：{title}真正改变结果的只有“{key}”所指的机制；{detail}。若移除这一机制仍可得到同方向结果，条目就不应被称为思想转折。",
        "证据链以{propose}为提出锚，以“{debate}”为对手，并用“{latest}”检查延续性。量纲不只是一项峰值，还包括样本、周期、误差、对照与未完成运行。",
        "反方最强的问题是：{boundary}。这不是附带限制，而是能让结论反号的失效条件；复核设计应主动把它推到边界之外，再看优势是否存在。",
        "工程上，{title}要求原始指令、版本、校准、人工接管和中止原因可追踪。只有同预算旧方法对照仍显示净收益，才能从演示进入可采购、可维护的系统。",
        "跨域看，{title}与相邻领域共享“可测代理代表真实对象”的前提，却可能在损耗、延迟或责任加入后给出相反结论。由此推出的新问题是如何把代理偏差变成设计变量。",
    ),
    (
        "在{title}之前，领域往往把复杂瓶颈归为规模不足。{propose}给出的新切口是“{key}”；其可见结果来自{detail}，也把原先藏在背景里的系统边界拉到台前。",
        "这里坚持一个可反驳单因：只有“{key}”能解释{title}的方向变化。扩大样本或换更快设备若不能替代该机制，因果才站得住；能替代则应撤回。",
        "提出锚是{propose}，争议锚是“{debate}”，最新锚则是“{latest}”。三条来源分别承担起点、反证与当下状态，不能由同一篇综述代写。",
        "条目的硬边界写成：{boundary}。一旦该条件出现，局部指标越漂亮，整体效用反而可能越差，因此失败谱与极端条件测试比平均值更有信息。",
        "实践中应把{title}的输入、输出、资源和异常放入同一日志，并让外部团队用冻结版本复算。部署门槛是跨批次方向一致，而不是现场演示一次成功。",
        "它与相邻面板的接口不在对象名称，而在共同预设：局部最优能否加总。{title}迫使研究者寻找不能被当前量纲看见、却会回写系统的第三变量。",
    ),
]


def make_item(row, idx, panel):
    title, en, propose, debate, latest, key, detail, boundary = row
    form = PARA_FORMS[idx % len(PARA_FORMS)]
    vals = dict(title=title, propose=propose, debate=debate, latest=latest, key=key, detail=detail, boundary=boundary)
    positions = ("S", "D", "E")
    pos = positions[idx % 3] if idx < 18 else (("D", "E"), ("E", "S"), ("S", "D"))[panel["no"] % 3][idx - 18]
    fail = ("增益在系统核算后反号", "外部复现方向翻转", "极端条件使代理失真")[idx % 3]
    return {
        "title": title, "en": en, "key": key,
        "source": {"propose": propose, "debate": debate, "latest": latest},
        "paras": [x.format(**vals) for x in form],
        "col": {
            "位置": pos,
            "单因": f"只保留“{key}”这一可消融机制",
            "预设": f"〔待归族〕{debate}",
            "量纲": f"以“{key}”为主读数，并列样本、误差、周期和对照",
            "失效": f"⇄{fail}：{boundary}",
            "自曝": f"本条用“{title}—{key}—{fail}”作骨架；弱处是跨平台量纲可能不可换算",
            "空栏": f"尚缺{title}在独立场景的长周期阴性结果",
            "异名": f"若去掉专名，可写成“受约束闭环中的{key}问题”",
        },
    }


def make_tail(panel):
    t, o = panel["thesis"], panel["outlook"]
    return [
        [f"二十个节点连起来，主线不是名词越来越多，而是{t}。早期把对象变得可执行，中期把读数送回决策，近期才开始把异常、资源和责任纳入系统。",
         "这条历史线也显示，局部纪录通常先于完整证据账出现。面板因此保留提出、争议与最新三条来源，避免用今天的术语倒写昨天的因果。"],
        ["第一，自动或量子等标签不自动等于净优势；第二，峰值读数不能替代全流程分母；第三，规模扩大并不会自行消除选择偏差、漂移和外部成本。",
         "三个误解共同源于把代理指标当作对象本身。只要损耗、人工、校准或失败样本被移出账本，任何路线都可能得到过度乐观的结论。"],
        [f"本领域向上连接基础理论，向下连接制造、软件、标准和治理。真正有用的接口是让相邻领域用同一失效条件挑战“{t}”。",
         "接口验收要求对手明确、共同预设明确、相反点明确，并能推出一个原领域尚未提出的新实验，而不是把热门名词并排陈列。"],
        ["支持者强调新的闭环和资源已经把过去不可做的问题变成可运行系统；反方则指出大多数优势仍依赖精心选择的任务、基线和实验环境。",
         "争议的裁决方式不是口号投票，而是冻结版本、同预算对照、跨站点复现与方向反转试验。若失败只被解释成工程细节，理论便失去被反驳的入口。"],
        [o, "应优先观察能否公开完整运行日志、异常分类和阴性结果，以及新一代标准是否要求端到端资源核算。单点纪录仍重要，但不足以单独改变面板判断。"],
        ["可对撞的领域包括控制论、因果推断、计量学、可靠性工程、科学社会学与技术治理。它们分别追问反馈、归因、溯源、长尾失败、奖励结构和责任。",
         "对撞时应保持对象和量纲不变，只替换一个前提；如果结论因此反号，才说明接口带来了新知识。"],
        [
            "建立公开失败谱，并比较只用成功数据与全量数据时结论是否反号。",
            "把人工接管、校准和等待时间加入资源分母，重算相对旧方法的净收益。",
            "在至少两个独立平台冻结版本复现同一方向，而非只复现最好数值。",
            "设计移除关键机制的消融试验，检查单因主张能否被直接推翻。",
            "将平均性能换成最坏分位数，观察路线排序是否改变。",
            "对代理指标施加分布外扰动，寻找它与真实目标解耦的阈值。",
            "记录中止与未完成运行，检验幸存者偏差在多大程度上制造领先。",
            "以同总预算而非同设备时间设置经典或旧技术基线。",
            "把能耗、耗材和退役责任延伸到生命周期，测试局部优化是否转移成本。",
            "预注册一个会令主张失败的结果形态，并在数据到来后按原规则裁决。",
        ],
    ]


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
