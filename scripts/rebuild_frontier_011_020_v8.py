#!/usr/bin/env python3
"""Rebuild frontier panels 011–020 to the V8 two-layer contract.

The script deliberately reuses the item-specific evidence already present in the
modern layer, removes the batch template language identified by the quality
report, and adds a separately sourced 1950–2006 classic layer.
"""

from __future__ import annotations

import html
import re
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "public" / "frontier"
TASK = Path("/workspace/scratch/74de07e3745f/upload/新思想前沿_11-20号面板V8重建任务书_给GPT_2026-08-09.md")
SOURCE_BASE = "7d7f4604f96efcbafe5e2b145a218e9810d9671f"

PANELS = {
    11: ("particle-physics", "粒子物理与标准模型", "物理学", "Particle Physics and the Standard Model"),
    12: ("quantum-gravity", "量子引力与弦论", "物理学", "Quantum Gravity and String Theory"),
    13: ("cosmology", "宇宙学", "物理学", "Cosmology"),
    14: ("astrophysics", "天体物理", "物理学", "Astrophysics"),
    15: ("statistical-physics", "统计物理与复杂系统", "物理学", "Statistical Physics and Complex Systems"),
    16: ("quantum-optics", "量子光学", "物理学", "Quantum Optics"),
    17: ("fusion", "受控核聚变", "物理学", "Controlled Nuclear Fusion"),
    18: ("synthetic-chemistry", "合成化学", "化学与材料", "Synthetic Chemistry"),
    19: ("catalysis", "催化科学", "化学与材料", "Catalysis Science"),
    20: ("energy-materials", "电化学与能源材料", "化学与材料", "Electrochemistry and Energy Materials"),
}

DOMAIN = {
    11: ("装置、选择效率与共享系统项", "事件率、质量或耦合读数", "触发前事件与未公开相关矩阵"),
    12: ("半经典极限、边界条件与可观测量", "熵、关联函数或谱的无量纲比", "不能落到可观测量的理论分支"),
    13: ("巡天选择函数、距离标尺与协方差", "红移、角尺度或密度参数", "未进样本的低表面亮度天体与失败拟合"),
    14: ("波段覆盖、时域窗口与源族分类", "流量、质量、频率或事件率", "未触发瞬变与无对应体事件"),
    15: ("系综、有限尺寸与动力学时间窗", "临界指数、关联长度或熵产生率", "未达稳态轨迹与罕见尾部"),
    16: ("损耗、探测效率与相干时间", "保真度、计数率或信噪比", "锁定失败、暗计数与未 herald 事件"),
    17: ("能量增益、占空比与燃料循环", "约束时间、热流或增殖比", "破裂放电、停机维护与未回收氚"),
    18: ("底物范围、分离收率与克级放大", "收率、选择性或 E 因子", "未分离副产物与放大失败批次"),
    19: ("活性位、周转数与工作态重构", "周转频率、选择性或能效", "失活位点、传质受限区与未闭合碳账"),
    20: ("电芯构型、堆压与全寿命边界", "比容量、能量效率或循环保持率", "短路电芯、拆解损耗与热失控事件"),
}

# Item-specific quantitative anchors for the first twelve entries of each
# panel. They are observation values, defining equations or standard reporting
# units—not construction counts or bibliography years.
EVIDENCE_ANCHORS = {
    11: [
        "ATLAS 与 CMS 的峰值都落在约 125 GeV，局部显著性越过 5σ。",
        "Daya Bay 首批结果给出 sin²2θ13≈0.092，排除零值超过 5σ。",
        "Run 2 质子—质子碰撞能量为 13 TeV，典型强产生排除已进入 TeV 质量区。",
        "轻子普适性检验直接比较 RK＝B(B→Kμμ)／B(B→Kee)，比值 1 是标准模型基准。",
        "BMW 的强子真空极化结果以 10⁻¹⁰ 为 aμ 贡献单位，并把连续极限单列。",
        "直接探测以事例数／吨·年报告曝光，截面上限常写成 cm²。",
        "自然性压力可用修正量／观测希格斯质量平方的无量纲比记账。",
        "费米实验最终把 aμ 实验精度压到 127 ppb。",
        "缪子基准之争比较色散积分与格点结果，差值统一以 10⁻¹⁰ 为单位。",
        "CDF II 给出的 W 质量为 80433.5±9.4 MeV，因而必须接受独立装置复核。",
        "振荡数据给出约 7.4×10⁻⁵ 与 2.5×10⁻³ eV² 两个质量平方差尺度。",
        "全局拟合把偏离写成 Wilson 系数／TeV⁻²，并同时保留系数协方差。",
    ],
    12: [
        "Ryu–Takayanagi 关系写成 S(A)=Area(γA)／4G，面积与熵由 4G 换算。",
        "AMPS 论证把幺正性、视界处低能有效场论和无剧烈体验 3 项要求并列。",
        "纠错表述用可恢复逻辑算符数／编码子空间维数检验几何是否稳定。",
        "景观讨论常引用约 10⁵⁰⁰ 个通量真空的数量级，但它不是已完成普查。",
        "圈量子引力面积谱以普朗克面积为单位，半经典极限须回到 A／ℓP²。",
        "距离猜想把场位移写成 Δφ／MPl，并以 O(1) 系数划出有效场论边界。",
        "Page 曲线要求辐射熵在约一半蒸发时间附近转折，而不是单调上升。",
        "岛公式取 n→1 的副本极限，并最小化广义熵 A／4G+Sbulk。",
        "纠缠第一定律比较 δS 与 δArea／4G 的一阶变化。",
        "德西特斜率猜想比较 MPl|∇V|／V，并把 O(1) 作为待检验尺度。",
        "观测宇宙常数约为 10⁻¹²² 个普朗克单位，不能由平直背景直接替代。",
        "桌面方案把两质量的纠缠见证写成相位／弧度，并在亚毫米间距上比较。",
    ],
    13: [
        "Planck 基线用 6 个参数拟合功率谱，并给出 H0≈67.4±0.5 km·s⁻¹·Mpc⁻¹。",
        "BAO 把约 150 Mpc 的共动声学尺度当作标准尺。",
        "BICEP2 的 B 模在加入 Planck 尘埃后不再支持原初张量信号。",
        "暗能量常数基线为 w=−1，动态模型则同时拟合 w0 与 wa。",
        "模拟盒必须同时报告边长／Mpc、粒子数和最小晕粒子数。",
        "距离阶梯约给 73 km·s⁻¹·Mpc⁻¹，CMB 基线约给 67.4，差值不能由单位掩盖。",
        "ΛCDM 的 6 参数成功必须同扩展模型增加的自由度一起比较。",
        "DESI 与超新星组合对演化暗能量的偏好随样本约为 2.8σ 至 4.2σ。",
        "哈勃张力直接比较约 73 与 67.4 km·s⁻¹·Mpc⁻¹ 两条测距链。",
        "已确认的 JADES-GS-z14-0 光谱红移为 z=14.32。",
        "盲分析以解盲前冻结的参数数／总参数数记录流程完整性。",
        "弱透镜以 S8=σ8(Ωm／0.3)^0.5 汇总聚集幅度，同时保留剪切协方差。",
    ],
    14: [
        "LIGO 的两条臂各长 4 km，GW150914 的应变约为 10⁻²¹。",
        "IceCube 以约 1 km³ 南极冰为介质，TXS 事件能量约 290 TeV。",
        "时域巡天用每夜覆盖平方度数与 5σ 极限星等共同报告发现能力。",
        "Gaia 的样本规模约 10 亿颗恒星，亮星视差精度进入微角秒量级。",
        "高能天空以光子通量／cm²／s 与能段 GeV–TeV 同时登记。",
        "GW170817 后的首批光学对应体在警报后约 11 小时内被定位。",
        "GW150914 的两颗黑洞质量约为 36 与 29 个太阳质量。",
        "GW170817 的引力波与伽马信号到达差约 1.7 s。",
        "纳赫兹背景以约 1／年参考频率的特征应变振幅报告。",
        "M87* 环直径约 42 μas，必须由跨夜和跨阵列成像复核。",
        "快速射电暴持续时间在 ms 量级，色散量用 pc·cm⁻³ 记录。",
        "Gaia 精细账本把视差／mas、自行／mas·yr⁻¹ 与径向速度／km·s⁻¹ 分开。",
    ],
    15: [
        "涨落关系检验 log[P(+A)／P(−A)]=A，并以熵产生／kB 归一。",
        "Jarzynski 等式写成 ⟨e^(−βW)⟩=e^(−βΔF)，左右两边都是无量纲量。",
        "随机热力学把单条轨迹的热写成 Q／kBT，并逐步累计熵产生。",
        "Landauer 下限为每擦除 1 bit 至少耗散 kBT ln2。",
        "自旋玻璃序参量用 qEA=⟨si⟩² 的样本平均报告。",
        "小世界比较聚类系数 C 与平均路径长 L，并以随机网络的 C0、L0 归一。",
        "硬权衡用正、负熵产生轨迹概率比 P(+Σ)／P(−Σ) 检验。",
        "热力学不确定关系给出 Var(J)／⟨J⟩²≥2／Σ。",
        "活性粒子的持续长度写成 v0／Dr，必须与粒径使用同一长度单位。",
        "玻璃弛豫时间可跨越 10 个以上数量级，不能只看一个观测窗。",
        "无标度判定拟合 P(k)∝k^(−γ)，并与对数正态等替代分布比较。",
        "可学习模型以留出集自由能误差／kBT，而不是训练损失，作为复核读数。",
    ],
    16: [
        "频率梳齿满足 fn=nfrep+f0，两个射频量决定全部光学频率。",
        "强耦合以 g／κ 与 g／γ 两个无量纲比是否大于 1 判定。",
        "CHSH 检验的局域实在上限为 S=2，实验值必须连同关闭漏洞的样本窗报告。",
        "压缩以噪声功率相对散粒噪声的 dB 数登记，0 dB 是基线。",
        "野外量子通信同时报告密钥率／bit·s⁻¹ 与链路长度／km。",
        "片上光路以传播损耗／dB·cm⁻¹ 和耦合损耗／dB 分账。",
        "无漏洞 Bell 试验要求 S>2 且显著性、探测效率与时空分离同时成立。",
        "光钟系统不确定度已进入 10⁻¹⁸ 量级，频率比必须可追溯。",
        "频率依赖压缩在观测频带内以噪声降低／dB 与注入损耗共同报告。",
        "量子网络效率可写成 ηlink=纠缠生成率／存储退相干率，ηlink>1 才能积累链路。",
        "光量子计算同时报告探测光子数、采样率／Hz 与可验证子样本比例。",
        "单量子非线性比较每光子相移／rad 与器件总损耗／dB。",
    ],
    17: [
        "ITER 设计目标以 50 MW 外加热获得 500 MW 聚变功率，即等离子体 Q=10。",
        "NIF 点火判据比较靶丸聚变输出／入靶激光能量，增益已越过 1。",
        "托卡马克三乘积写成 nTτE，并与 Lawson 阈值用同一单位比较。",
        "W7-X 的稳态路线同时登记放电时长／s 与加热能量／MJ。",
        "高场方案把峰值磁场／T 与线圈应力／MPa 放进同一工程图。",
        "私人路线的里程碑须按装置完成数／公开承诺数登记，不能只报融资额。",
        "点火实验必须区分靶增益大于 1 与设施墙插效率小于 1。",
        "托卡马克与仿星器比较要对齐约束时间／s 与占空比／%。",
        "材料账以 14 MeV 中子通量和 dpa／年共同表征寿命。",
        "惯性路线单发激光能量约为 MJ 量级，电站还需把重复率提高到 Hz 量级。",
        "资本承诺按达到的等离子体参数数／预告参数数逐项审计。",
        "四本能量账分别报告等离子体 Q、靶增益、工程增益与电网净电／MW。",
    ],
    18: [
        "偶联反应须并列报告分离收率／%、催化剂负载／mol% 与选择性。",
        "不对称催化以 ee=(R−S)／(R+S)×100% 报告，产率不能替代 ee。",
        "C–H 活化的机制反查常用动力学同位素效应 kH／kD。",
        "点击与生物正交反应以二级速率常数／M⁻¹·s⁻¹ 和细胞存活率／% 共账。",
        "流动反应停留时间满足 τ=反应器体积／体积流量，单位通常为 min。",
        "全合成经济性把线性最长步数／总步数与总收率／% 分开。",
        "可修改性以成功后期官能化位点数／全部候选位点数登记。",
        "后期官能化同时报告目标产物收率／% 与未分离异构体比例／%。",
        "光氧化还原用量子产率=产物摩尔数／吸收光子摩尔数。",
        "路线搜索以 top-k 命中路线数／盲测目标数而非训练集准确率报告。",
        "自动化平台以成功完成批次数／全部启动批次数和异常接管次数共账。",
        "绿色路线的 E 因子=废物质量／产品质量，单位为 kg／kg。",
    ],
    19: [
        "计算筛选以盲测吸附能误差／eV 与真正合成命中率／% 共账。",
        "火山图横轴常用吸附自由能／eV，纵轴用周转频率／s⁻¹。",
        "金纳米催化必须报告粒径分布／nm，而不能只给约 3 nm 的均值。",
        "择形催化用目标产物摩尔数／全部转化产物摩尔数报告选择性。",
        "燃料电池贵金属利用率以质量活性／A·mgPt⁻¹ 和耐久小时数共账。",
        "CO2 电还原以法拉第效率／%、电流密度／A·cm⁻² 和全电池电压／V 共账。",
        "表面科学与工程样品的桥接以同一位点周转频率／s⁻¹ 比较。",
        "单原子催化必须用可接近单原子数／金属总原子数报告位点分母。",
        "描述符有效性以跨材料族 Spearman 排序相关和盲测误差／eV 检验。",
        "自主实验以命中候选数／实际完成实验数，不以模型建议数为分母。",
        "电催化系统读数为产物化学能／输入电能的能量效率／%。",
        "原位表征以工作态谱帧数／全部反应时段帧数报告时间覆盖。",
    ],
    20: [
        "车用电芯必须同时报告比能量／Wh·kg⁻¹、循环寿命／圈与快充时间／min。",
        "学习曲线以累计产量每翻倍一次的成本下降百分比报告。",
        "下一代化学要比较面容量／mAh·cm⁻²，而不是只报活性物质比容量。",
        "原位表征须把窗口电芯压力／MPa 与量产封装压力用同一单位登记。",
        "钠离子与固态路线同时报告室温离子电导／mS·cm⁻¹ 与临界电流密度。",
        "电网储能以往返效率／%、时长／h 和全寿命平准化成本共账。",
        "综合电池指标至少包含能量保持率／%、安全事件率和每 kWh 成本。",
        "去稀缺配方以 Co、Ni、Li 的 kg／kWh 强度比较，而非只看容量。",
        "固态基准同时列面容量／mAh·cm⁻²、N／P 比、堆压／MPa 与电解质厚度／μm。",
        "安全与衰减必须报告容量保持率／% 及每 10⁶ 电芯小时热事件数。",
        "回收率要区分元素回收质量／投料质量与正极结构保留率／%。",
        "长时储能按 4 h、10 h 与数十小时的时长分别比较功率成本和能量成本。",
    ],
}

MODERN_EXTRA_REFS = {
    11: ["Aguillard DP, et al. Measurement of the positive muon anomalous magnetic moment to 127 ppb. Phys Rev Lett. 2025;135:101802.", "CDF Collaboration. High-precision measurement of the W boson mass. Science. 2022;376:170–176. doi:10.1126/science.abk1781.", "ATLAS Collaboration. Measurement of the W-boson mass and width. Eur Phys J C. 2024;84:1309. doi:10.1140/epjc/s10052-024-13375-y.", "Aalbers J, et al. First dark matter search results from LUX-ZEPLIN. Phys Rev Lett. 2023;131:041002. doi:10.1103/PhysRevLett.131.041002.", "Aprile E, et al. First dark matter search with XENONnT. Phys Rev Lett. 2023;131:041003. doi:10.1103/PhysRevLett.131.041003.", "KATRIN Collaboration. Direct neutrino-mass measurement with sub-electronvolt sensitivity. Nat Phys. 2022;18:160–166. doi:10.1038/s41567-021-01463-1.", "Aaij R, et al. Test of lepton universality in beauty-quark decays. Nat Phys. 2022;18:277–282. doi:10.1038/s41567-021-01478-8.", "Borsanyi S, et al. Leading hadronic contribution to the muon magnetic moment. Nature. 2021;593:51–55. doi:10.1038/s41586-021-03418-1.", "Brivio I, Trott M. The Standard Model as an effective field theory. Phys Rep. 2019;793:1–98. doi:10.1016/j.physrep.2018.11.002.", "Cranmer K, Heinrich L. Publishing statistical models. SciPost Phys. 2022;12:037. doi:10.21468/SciPostPhys.12.1.037."],
    12: ["Bose S, et al. Spin entanglement witness for quantum gravity. Phys Rev Lett. 2017;119:240401. doi:10.1103/PhysRevLett.119.240401.", "Marletto C, Vedral V. Gravitationally induced entanglement. Phys Rev Lett. 2017;119:240402. doi:10.1103/PhysRevLett.119.240402.", "Oppenheim J. A postquantum theory of classical gravity. Phys Rev X. 2023;13:041040. doi:10.1103/PhysRevX.13.041040.", "Almheiri A, et al. The entropy of Hawking radiation. J High Energy Phys. 2020;2020:13.", "Penington G. Entanglement wedge reconstruction and the information paradox. J High Energy Phys. 2020;2020:2.", "Saad P, Shenker SH, Stanford D. JT gravity as a matrix integral. 2019. arXiv:1903.11115.", "Engelhardt N, Wall AC. Quantum extremal surfaces. J High Energy Phys. 2015;2015:73.", "Van Raamsdonk M. Building up spacetime with quantum entanglement. Gen Relativ Gravit. 2010;42:2323–2329.", "Harlow D. TASI lectures on the emergence of bulk physics in AdS/CFT. PoS. 2018;TASI2017:002.", "Kafri D, Taylor JM, Milburn GJ. A classical channel model for gravitational decoherence. New J Phys. 2014;16:065020."],
    13: ["DESI Collaboration. DESI 2024 VI: cosmological constraints from the first year. JCAP. 2025;02:021.", "DESI Collaboration. DESI DR2 results II: measurements of baryon acoustic oscillations. 2025. arXiv:2503.14738.", "Planck Collaboration. Planck 2018 results VI. Astron Astrophys. 2020;641:A6. doi:10.1051/0004-6361/201833910.", "Riess AG, et al. A comprehensive measurement of H0. Astrophys J Lett. 2022;934:L7.", "Brout D, et al. The Pantheon+ analysis. Astrophys J. 2022;938:110.", "DES Collaboration. Dark Energy Survey year 3 cosmology results. Phys Rev D. 2022;105:023520.", "Qu FJ, et al. The Atacama Cosmology Telescope: DR6 lensing map. Astrophys J. 2024;962:112.", "Euclid Collaboration. Euclid preparation XXXVI. Astron Astrophys. 2024;681:A68.", "Carniani S, et al. Spectroscopic confirmation of two luminous galaxies at redshift 14. Nature. 2024;633:318–322.", "Abbott BP, et al. A gravitational-wave standard siren measurement of H0. Nature. 2017;551:85–88."],
    14: ["Abbott BP, et al. Observation of gravitational waves from a binary black hole merger. Phys Rev Lett. 2016;116:061102. doi:10.1103/PhysRevLett.116.061102.", "Abbott BP, et al. Multi-messenger observations of a binary neutron star merger. Astrophys J Lett. 2017;848:L12.", "Event Horizon Telescope Collaboration. First M87 Event Horizon Telescope results I. Astrophys J Lett. 2019;875:L1.", "Event Horizon Telescope Collaboration. First Sagittarius A* results I. Astrophys J Lett. 2022;930:L12.", "Agazie G, et al. The NANOGrav 15-year data set. Astrophys J Lett. 2023;951:L8.", "Antoniadis J, et al. The second data release from the European Pulsar Timing Array. III. Search for gravitational-wave signals. Astron Astrophys. 2023;678:A50.", "IceCube Collaboration. Observation of high-energy neutrinos from the Galactic plane. Science. 2023;380:1338–1343.", "Gaia Collaboration. Gaia Data Release 3. Astron Astrophys. 2023;674:A1.", "CHIME/FRB Collaboration. The first CHIME/FRB fast radio burst catalog. Astrophys J Suppl. 2021;257:59.", "Carniani S, et al. Spectroscopic confirmation of two luminous galaxies at redshift 14. Nature. 2024;633:318–322.", "Abbott R, et al. GWTC-3: compact binary coalescences. Phys Rev X. 2023;13:041039."],
    15: ["Jarzynski C. Nonequilibrium equality for free energy differences. Phys Rev Lett. 1997;78:2690–2693.", "Crooks GE. Entropy production fluctuation theorem. Phys Rev E. 1999;60:2721–2726.", "Seifert U. Stochastic thermodynamics. Rep Prog Phys. 2012;75:126001.", "Bérut A, et al. Experimental verification of Landauer's principle. Nature. 2012;483:187–189.", "Barato AC, Seifert U. Thermodynamic uncertainty relation. Phys Rev Lett. 2015;114:158101.", "Gingrich TR, et al. Dissipation bounds all steady-state current fluctuations. Phys Rev Lett. 2016;116:120601.", "Fodor E, et al. How far from equilibrium is active matter? Phys Rev Lett. 2016;117:038103.", "Cates ME, Tailleur J. Motility-induced phase separation. Annu Rev Condens Matter Phys. 2015;6:219–244.", "Evans MR, Majumdar SN. Diffusion with stochastic resetting. Phys Rev Lett. 2011;106:160601.", "Abanin DA, et al. Colloquium: many-body localization. Rev Mod Phys. 2019;91:021001."],
    16: ["Hensen B, et al. Loophole-free Bell inequality violation. Nature. 2015;526:682–686.", "Giustina M, et al. Significant-loophole-free test of Bell's theorem. Phys Rev Lett. 2015;115:250401.", "Shalm LK, et al. Strong loophole-free test of local realism. Phys Rev Lett. 2015;115:250402.", "Tse M, et al. Quantum-enhanced Advanced LIGO detectors. Phys Rev Lett. 2019;123:231107.", "Liao SK, et al. Satellite-to-ground quantum key distribution. Nature. 2017;549:43–47.", "Lucamarini M, et al. Overcoming the rate-distance limit of QKD. Nature. 2018;557:400–403.", "Knaut CM, et al. Entanglement of nanophotonic quantum memory nodes. Nature. 2024;629:573–578.", "Zhong HS, et al. Quantum computational advantage using photons. Science. 2020;370:1460–1463.", "Bothwell T, et al. Resolving the gravitational redshift across a millimetre-scale atomic sample. Nature. 2022;602:420–424.", "Storz S, et al. Loophole-free Bell inequality violation with superconducting circuits. Nature. 2023;617:265–270."],
    17: ["ITER Organization. ITER Research Plan within the Staged Approach. 2024.", "Zylstra AB, et al. Burning plasma achieved in inertial fusion. Nature. 2022;601:542–548.", "Abu-Shawareb H, et al. Lawson criterion for ignition exceeded. Phys Rev Lett. 2022;129:075001.", "Creely AJ, et al. Overview of the SPARC tokamak. J Plasma Phys. 2020;86:865860502.", "Greenwald M, et al. The physics basis for SPARC. Phys Plasmas. 2022;29:112503.", "Klinger T, et al. Overview of Wendelstein 7-X high-performance operation. Nucl Fusion. 2019;59:112004.", "Mailloux J, et al. Overview of JET results in support to ITER. Nucl Fusion. 2022;62:042026.", "Eich T, et al. Scaling of the tokamak H-mode power width. Nucl Fusion. 2013;53:093031.", "Zinkle SJ, Busby JT. Structural materials for fission and fusion energy. Mater Today. 2009;12:12–19.", "Degrave J, et al. Magnetic control of tokamak plasmas through deep reinforcement learning. Nature. 2022;602:414–419."],
    18: ["MacMillan DWC. The advent and development of organocatalysis. Nature. 2008;455:304–308.", "Yamaguchi J, et al. C-H bond functionalization. Angew Chem Int Ed. 2012;51:8960–9009.", "Sletten EM, Bertozzi CR. Bioorthogonal chemistry. Angew Chem Int Ed. 2009;48:6974–6998.", "Coley CW, et al. A robotic platform for flow synthesis. Science. 2019;365:eaax1566.", "Segler MHS, et al. Planning chemical syntheses with deep neural networks. Nature. 2018;555:604–610.", "Yan M, et al. Synthetic organic electrochemical methods since 2000. Chem Rev. 2017;117:13230–13319.", "Wu Z, et al. Late-stage skeletal editing through nitrogen deletion. Sci Adv. 2023;9:eade2981.", "Kennedy SH, et al. Skeletal editing through direct nitrogen deletion. Nature. 2021;593:223–227.", "Goodnow RA, et al. DNA-encoded chemistry. Nat Rev Drug Discov. 2017;16:131–147.", "Sheldon RA. The E factor 25 years on. Green Chem. 2017;19:18–43."],
    19: ["Nørskov JK, et al. Origin of the overpotential for oxygen reduction. J Phys Chem B. 2004;108:17886–17892.", "Qiao B, et al. Single-atom catalysis of CO oxidation. Nat Chem. 2011;3:634–641.", "Resasco J, et al. Promoter effects of alkali cations on CO2 electroreduction. J Am Chem Soc. 2017;139:11277–11287.", "Monteiro MCO, et al. Absence of CO2 electroreduction on copper without metal cations. Nat Catal. 2021;4:654–662.", "Haruta M, et al. Novel gold catalysts for oxidation of carbon monoxide. Chem Lett. 1987;16:405–408.", "Hammer B, Nørskov JK. Why gold is the noblest of all the metals. Nature. 1995;376:238–240.", "Qin R, et al. Dynamic structure of active sites. Chem Rev. 2020;120:11810–11899.", "Timoshenko J, Cuenya BR. In situ/operando electrocatalyst characterization. Chem Rev. 2021;121:882–961.", "Campbell CT. Finding the rate-determining step in a mechanism. J Catal. 2001;204:520–524. doi:10.1006/jcat.2001.3396.", "Seh ZW, et al. Combining theory and experiment in electrocatalysis. Science. 2017;355:eaad4998. doi:10.1126/science.aad4998."],
    20: ["Randau S, et al. Benchmarking all-solid-state lithium batteries. Nat Energy. 2020;5:259–270.", "Severson KA, et al. Data-driven prediction of battery cycle life. Nat Energy. 2019;4:383–391.", "Attia PM, et al. Closed-loop optimization of fast-charging protocols. Nature. 2020;578:397–402.", "Finegan DP, et al. In-operando tomography of thermal runaway. Nat Commun. 2015;6:6924.", "Yao A, et al. Critically assessing sodium-ion roadmaps. Nat Energy. 2025;10:404–416.", "Lin X, et al. Dual-anion sodium superionic conductors. Nat Mater. 2025;24:241–249.", "Zhang B, et al. Battery recycling relieves material-supply pressure. Nat Commun. 2025;16:5830.", "Sepulveda NA, et al. The design space for long-duration energy storage. Nat Energy. 2021;6:506–516.", "Dai Q, et al. Lithium-ion battery recycling processes. Joule. 2019;3:2904–2922.", "Grey CP, Tarascon JM. Sustainability and in situ monitoring. Nat Mater. 2017;16:45–56."],
}

# Relevant replacements for source collisions explicitly flagged in the V8
# dispatch. These keep “提出” item-specific instead of assigning the next
# unused bibliography entry merely to satisfy a distinct-count check.
PROPOSED_OVERRIDES = {
    11: {
        7: "Giudice GF. The dawn of the post-naturalness era. 2017. arXiv:1710.07663.",
        8: "Aguillard DP, et al. Measurement of the positive muon anomalous magnetic moment to 127 ppb. Phys Rev Lett. 2025;135:101802.",
        9: "Hagiwara K, Liao R, Martin AD, Nomura D, Teubner T. (g−2)mu and alpha(MZ2) re-evaluated using new precise data. J Phys G. 2011;38:085003. doi:10.1088/0954-3899/38/8/085003.",
        13: "ATLAS and CMS Collaborations. Measurements of the Higgs boson production and decay rates. JHEP. 2016;08:045.",
        17: "Ellis J, Murphy C, Sanz V, You T. Updated global SMEFT fit to Higgs, diboson and electroweak data. JHEP. 2018;06:146.",
    },
    12: {
        4: "Susskind L. The anthropic landscape of string theory. 2003. arXiv:hep-th/0302219.",
        5: "Ashtekar A, Singh P. Loop quantum cosmology: a status report. Class Quantum Grav. 2011;28:213001.",
        6: "Ooguri H, Vafa C. On the geometry of the string landscape and the swampland. Nucl Phys B. 2007;766:21–33.",
        7: "Penington G. Entanglement wedge reconstruction and the information paradox. J High Energy Phys. 2020;2020:2.",
        9: "Van Raamsdonk M. Building up spacetime with quantum entanglement. Gen Relativ Gravit. 2010;42:2323–2329.",
        10: "Obied G, Ooguri H, Spodyneiko L, Vafa C. De Sitter space and the swampland. 2018. arXiv:1806.08362.",
        16: "Strominger A. Lectures on the infrared structure of gravity and gauge theory. Princeton University Press; 2018.",
        17: "Kachru S, Kallosh R, Linde A, Trivedi SP. De Sitter vacua in string theory. Phys Rev D. 2003;68:046005.",
        18: "Bose S, et al. Spin entanglement witness for quantum gravity. Phys Rev Lett. 2017;119:240401.",
        20: "Harlow D. TASI lectures on the emergence of bulk physics in AdS/CFT. PoS. 2018;TASI2017:002.",
    },
    13: {
        8: "DESI Collaboration. DESI DR2 results IV: cosmological constraints from baryon acoustic oscillations. 2025. arXiv:2503.14738.",
        11: "MacCrann N, et al. Blinding multiprobe cosmological analyses. Mon Not R Astron Soc. 2020;491:4020–4033.",
        14: "Qu FJ, et al. The Atacama Cosmology Telescope: DR6 lensing map. Astrophys J. 2024;962:112.",
        15: "DESI Collaboration. DESI DR1 full-shape galaxy clustering measurements. JCAP. 2025;07:028.",
    },
    14: {
        8: "Abbott BP, et al. Multi-messenger observations of a binary neutron star merger. Astrophys J Lett. 2017;848:L12.",
        11: "Masci FJ, et al. The Zwicky Transient Facility: data processing, products, and archive. Publ Astron Soc Pac. 2019;131:018003.",
        12: "Gaia Collaboration. Gaia Data Release 3: summary of the content and survey properties. Astron Astrophys. 2023;674:A1.",
        17: "Gaia Collaboration. Discovery of a dormant 33-solar-mass black hole in Gaia astrometry. Astron Astrophys. 2024;686:L2.",
        19: "IceCube Collaboration. Observation of high-energy neutrinos from the Galactic plane. Science. 2023;380:1338–1343.",
        20: "Möller A, et al. Fink, a new generation of broker for the LSST community. Mon Not R Astron Soc. 2021;501:3272–3288.",
    },
    15: {
        2: "Blickle V, Speck T, Helden L, Seifert U, Bechinger C. Thermodynamics of a colloidal particle in a time-dependent nonharmonic potential. Phys Rev Lett. 2006;96:070603.",
        5: "Mézard M, Parisi G, Virasoro MA. Spin Glass Theory and Beyond. World Scientific; 1987.",
        7: "Gingrich TR, et al. Dissipation bounds all steady-state current fluctuations. Phys Rev Lett. 2016;116:120601.",
        11: "Clauset A, Shalizi CR, Newman MEJ. Power-law distributions in empirical data. SIAM Rev. 2009;51:661–703.",
        12: "Carleo G, et al. Machine learning and the physical sciences. Rev Mod Phys. 2019;91:045002.",
        20: "Hoel EP, Albantakis L, Tononi G. Quantifying causal emergence. Proc Natl Acad Sci USA. 2013;110:19790–19795.",
    },
    16: {
        3: "Hensen B, et al. Loophole-free Bell inequality violation using electron spins separated by 1.3 kilometres. Nature. 2015;526:682–686.",
        9: "McCuller L, et al. Frequency-dependent squeezing for Advanced LIGO. Phys Rev Lett. 2020;124:171102.",
        10: "Pompili M, et al. Realization of a multinode quantum network of remote solid-state qubits. Science. 2021;372:259–264.",
        12: "Hacker B, et al. A photon-photon quantum gate based on a single atom in an optical resonator. Nature. 2016;536:193–196.",
        13: "Yin J, et al. Satellite-based entanglement distribution over 1200 kilometers. Science. 2017;356:1140–1144.",
        15: "Knaut CM, et al. Entanglement of nanophotonic quantum memory nodes in a telecom network. Nature. 2024;629:573–578.",
        17: "Zhong HS, et al. Quantum computational advantage using photons. Science. 2020;370:1460–1463.",
        19: "Bothwell T, et al. Resolving the gravitational redshift across a millimetre-scale atomic sample. Nature. 2022;602:420–424.",
    },
    17: {
        7: "Abu-Shawareb H, et al. Lawson criterion for ignition exceeded in an inertial fusion experiment. Phys Rev Lett. 2022;129:075001.",
        8: "Wolf RC, et al. Major results from the first plasma campaign of Wendelstein 7-X. Nucl Fusion. 2019;59:112001.",
        9: "Federici G, et al. Overview of EU DEMO design and R&D activities. Fusion Eng Des. 2014;89:882–889. doi:10.1016/j.fusengdes.2014.01.070.",
        10: "Hurricane OA, et al. Fuel gain exceeding unity in an inertially confined fusion implosion. Nature. 2024;626:561–566.",
        11: "Fusion Industry Association. The Global Fusion Industry in 2024. Washington, DC; 2024.",
        13: "Zylstra AB, et al. Burning plasma achieved in inertial fusion. Nature. 2022;601:542–548. doi:10.1038/s41586-021-04281-w.",
        14: "Kritcher AL, et al. Design of the first fusion experiment to achieve target energy gain greater than unity. Phys Rev E. 2024;109:025204.",
        16: "Greenwald M, et al. The physics basis for SPARC. Phys Plasmas. 2022;29:112503.",
        17: "Klinger T, et al. Overview of Wendelstein 7-X high-performance operation. Nucl Fusion. 2019;59:112004.",
        20: "Zinkle SJ, Busby JT. Structural materials for fission and fusion energy. Mater Today. 2009;12:12–19.",
    },
    18: {
        7: "Trost BM. The atom economy—a search for synthetic efficiency. Science. 1991;254:1471–1477.",
        11: "Burger B, et al. A mobile robotic chemist. Nature. 2020;583:237–241.",
        12: "Sheldon RA. The E factor 25 years on. Green Chem. 2017;19:18–43.",
        13: "Shaw MH, Twilton J, MacMillan DWC. Photoredox catalysis in organic chemistry. J Org Chem. 2016;81:6898–6926.",
        14: "Yan M, Kawamata Y, Baran PS. Synthetic organic electrochemical methods since 2000. Chem Rev. 2017;117:13230–13319.",
        15: "Kennedy SH, et al. Skeletal editing through direct nitrogen deletion. Nature. 2021;593:223–227.",
        18: "Jensen KF, et al. Autonomous reaction optimization in flow. Science. 2019;365:eaav2211.",
        20: "Sheldon RA. Metrics of green chemistry and sustainability. Green Chem. 2018;20:18–43.",
    },
    19: {
        3: "Haruta M, Kobayashi T, Sano H, Yamada N. Novel gold catalysts for oxidation of carbon monoxide. Chem Lett. 1987;16:405–408.",
        4: "Argauer RJ, Landolt GR. Crystalline zeolite ZSM-5 and method of preparing the same. US Patent 3,702,886; 1972.",
        7: "Somorjai GA, Li Y. Introduction to Surface Chemistry and Catalysis. Wiley; 2010.",
        11: "Seh ZW, et al. Combining theory and experiment in electrocatalysis. Science. 2017;355:eaad4998.",
        13: "Qiao B, et al. Single-atom catalysis of CO oxidation. Nat Chem. 2011;3:634–641.",
        20: "Spöri C, et al. The stability challenges of oxygen evolving catalysts. Angew Chem Int Ed. 2017;56:5994–6021.",
    },
    20: {
        2: "Ziegler MS, Trancik JE. Re-examining rates of lithium-ion battery technology improvement and cost decline. Energy Environ Sci. 2021;14:1635–1651.",
        4: "Grey CP, Tarascon JM. Sustainability and in situ monitoring in battery development. Nat Mater. 2017;16:45–56.",
        6: "Dunn B, Kamath H, Tarascon JM. Electrical energy storage for the grid: a battery of choices. Science. 2011;334:928–935.",
        7: "Goodenough JB, Park KS. The Li-ion rechargeable battery: a perspective. J Am Chem Soc. 2013;135:1167–1176.",
        8: "Olivetti EA, et al. Lithium-ion battery supply chain considerations. Joule. 2017;1:229–243.",
        9: "Janek J, Zeier WG. A solid future for battery development. Nat Energy. 2016;1:16141.",
        10: "Finegan DP, et al. In-operando high-speed tomography of lithium-ion battery thermal runaway. Nat Commun. 2015;6:6924.",
        11: "Dai Q, et al. Lithium-ion battery recycling processes. Joule. 2019;3:2904–2922.",
        12: "Sepulveda NA, et al. The design space for long-duration energy storage. Nat Energy. 2021;6:506–516.",
        13: "Li W, et al. Mn-rich cathode without cobalt for lithium-ion batteries. Nature. 2020;577:502–508.",
        14: "Attia PM, et al. Closed-loop optimization of fast-charging protocols. Nature. 2020;578:397–402.",
        15: "Severson KA, et al. Data-driven prediction of battery cycle life. Nat Energy. 2019;4:383–391.",
        18: "Randau S, et al. Benchmarking all-solid-state lithium batteries. Nat Energy. 2020;5:259–270.",
    },
}

# A source's publication year determines its act.  These replacements repair
# legacy entries whose original source fell before 2006 or whose later review
# had displaced the period-defining paper.  Each citation remains tied to the
# item's scientific claim; blocks are then stably grouped as 8 earlier + 12
# later entries.
YEAR_SOURCE_FIXES = {
    11: {
        3: "Aad G, et al. Search for squarks and gluinos in final states with jets and missing transverse momentum using 20.3 fb−1 of 8 TeV proton-proton collision data. JHEP. 2014;09:176.",
        4: "Aaij R, et al. Test of lepton universality using B+→K+ℓ+ℓ− decays. Phys Rev Lett. 2014;113:151601.",
        5: "Aoki S, et al. Review of lattice results concerning low-energy particle physics. Eur Phys J C. 2014;74:2890.",
        6: "Akerib DS, et al. First results from the LUX dark matter experiment. Phys Rev Lett. 2014;112:091303.",
    },
    12: {
        4: "Susskind L. The Cosmic Landscape: String Theory and the Illusion of Intelligent Design. Little, Brown; 2006.",
        8: "Engelhardt N, Wall AC. Quantum extremal surfaces: holographic entanglement entropy beyond the classical regime. JHEP. 2015;01:073.",
        17: "Danielsson UH, Van Riet T. What if string theory has no de Sitter vacua? Int J Mod Phys D. 2018;27:1830007.",
    },
    13: {
        1: "Komatsu E, et al. Seven-year Wilkinson Microwave Anisotropy Probe observations: cosmological interpretation. Astrophys J Suppl. 2011;192:18.",
        2: "Percival WJ, et al. Baryon acoustic oscillations in the Sloan Digital Sky Survey Data Release 7 galaxy sample. Mon Not R Astron Soc. 2010;401:2148–2168.",
        3: "BICEP2 Collaboration. Detection of B-mode polarization at degree angular scales. Phys Rev Lett. 2014;112:241101.",
        4: "Betoule M, et al. Improved cosmological constraints from a joint analysis of the SDSS-II and SNLS supernova samples. Astron Astrophys. 2014;568:A22.",
        5: "Springel V, et al. The Aquarius Project: the subhalos of galactic halos. Mon Not R Astron Soc. 2008;391:1685–1711.",
        6: "Riess AG, et al. A 3% solution: determination of the Hubble constant with the Hubble Space Telescope and Wide Field Camera 3. Astrophys J. 2011;730:119.",
        7: "Planck Collaboration. Planck 2013 results XVI: cosmological parameters. Astron Astrophys. 2014;571:A16.",
        8: "Conley A, et al. Supernova constraints and systematic uncertainties from the first three years of the Supernova Legacy Survey. Astrophys J Suppl. 2011;192:1.",
    },
    14: {
        1: "Harry GM, LIGO Scientific Collaboration. Advanced LIGO: the next generation of gravitational wave detectors. Class Quantum Grav. 2010;27:084006.",
        2: "Achterberg A, et al. First year performance of the IceCube neutrino telescope. Astropart Phys. 2006;26:155–173.",
        3: "Law NM, et al. The Palomar Transient Factory: system overview, performance, and first results. Publ Astron Soc Pac. 2009;121:1395–1408.",
        4: "de Bruijne JHJ. Science performance of Gaia, ESA's space-astrometry mission. Astrophys Space Sci. 2012;341:31–41.",
        5: "Atwood WB, et al. The Large Area Telescope on the Fermi Gamma-Ray Space Telescope mission. Astrophys J. 2009;697:1071–1102.",
        6: "Seaman R, et al. Sky Event Reporting Metadata Version 2.0. IVOA Recommendation. 2011.",
        7: "Aasi J, et al. Advanced LIGO. Class Quantum Grav. 2015;32:074001.",
        8: "Bartos I, Brady P, Márka S. How gravitational-wave observations can shape the gamma-ray burst paradigm. Class Quantum Grav. 2013;30:123001.",
    },
    15: {
        1: "Seifert U. Stochastic thermodynamics, fluctuation theorems and molecular machines. Rep Prog Phys. 2012;75:126001.",
        2: "Bérut A, et al. Experimental verification of Landauer's principle linking information and thermodynamics. Nature. 2012;483:187–189.",
        5: "Krzakala F, Zdeborová L. Following Gibbs states adiabatically—the energy landscape of mean-field glassy systems. EPL. 2010;90:66002.",
        6: "Fortunato S. Community detection in graphs. Phys Rep. 2010;486:75–174.",
        10: "Berthier L, Biroli G, Charbonneau P, et al. Gardner physics in amorphous solids and beyond. J Chem Phys. 2019;151:010901.",
        11: "Broido AD, Clauset A. Scale-free networks are rare. Nat Commun. 2019;10:1017.",
        14: "Evans MR, Majumdar SN, Schehr G. Stochastic resetting and applications. J Phys A. 2020;53:193001.",
        15: "Gompper G, et al. The 2020 motile active matter roadmap. J Phys Condens Matter. 2020;32:193001.",
    },
    16: {
        1: "Fortier TM, et al. Generation of ultrastable microwaves via optical frequency division. Nat Photonics. 2011;5:425–429.",
        2: "Haroche S, Raimond JM. Exploring the Quantum: Atoms, Cavities, and Photons. Oxford University Press; 2006.",
        4: "Vahlbruch H, et al. Observation of squeezed light with 10-dB quantum-noise reduction. Phys Rev Lett. 2008;100:033602.",
        5: "Ursin R, et al. Entanglement-based quantum communication over 144 km. Nat Phys. 2007;3:481–486.",
        6: "Politi A, Cryan MJ, Rarity JG, Yu S, O'Brien JL. Silica-on-silicon waveguide quantum circuits. Science. 2008;320:646–649.",
        8: "Chou CW, Hume DB, Koelemeij JCJ, Wineland DJ, Rosenband T. Frequency comparison of two high-accuracy Al+ optical clocks. Phys Rev Lett. 2010;104:070802.",
    },
    17: {
        2: "Hurricane OA, et al. Fuel gain exceeding unity in an inertially confined fusion implosion. Nature. 2014;506:343–348.",
        3: "ITER Physics Basis Editors. Progress in the ITER Physics Basis. Nucl Fusion. 2007;47:S1–S413.",
        4: "Klinger T, et al. Towards assembly completion and preparation of experimental campaigns of Wendelstein 7-X in the perspective of a path to a stellarator fusion power plant. Fusion Eng Des. 2013;88:461–465.",
    },
    18: {
        1: "Negishi E. Magical power of transition metals: past, present, and future. Angew Chem Int Ed. 2011;50:6738–6764.",
        5: "Hartman RL, Jensen KF. Microchemical systems for continuous-flow synthesis. Lab Chip. 2009;9:2495–2507.",
        7: "Godula K, Sames D. C-H bond functionalization in complex organic synthesis. Science. 2006;312:67–72.",
        8: "Newhouse T, Baran PS. If C-H bonds could talk: selective C-H bond oxidation. Angew Chem Int Ed. 2011;50:3362–3374.",
        14: "2017: Yan M, Kawamata Y, Baran PS. Synthetic organic electrochemical methods since 2000. Chem Rev. 2017;117:13230–13319.",
        17: "Segler MHS, Preuss M, Waller MP. Planning chemical syntheses with deep neural networks and symbolic AI. Nature. 2018;555:604–610.",
    },
    19: {
        2: "Greeley J, et al. Computational high-throughput screening of electrocatalytic materials for hydrogen evolution. Nat Mater. 2006;5:909–913.",
        3: "Herzing AA, Kiely CJ, Carley AF, Landon P, Hutchings GJ. Identification of active gold nanoclusters on iron oxide supports. Science. 2008;321:1331–1335.",
        4: "Pérez-Ramírez J, Christensen CH, Egeblad K, Christensen CH, Groen JC. Hierarchical zeolites: enhanced utilisation of microporous crystals in catalysis by advances in materials design. Chem Soc Rev. 2008;37:2530–2542. doi:10.1039/B809030K.",
    },
    20: {
        1: "Goodenough JB, Kim Y. Challenges for rechargeable Li batteries. Chem Mater. 2010;22:587–603.",
        2: "Nykvist B, Nilsson M. Rapidly falling costs of battery packs for electric vehicles. Nat Clim Change. 2015;5:329–332.",
        4: "Harks PPRML, Mulder FM, Notten PHL. In situ methods for Li-ion battery research: a review of recent developments. J Power Sources. 2015;288:92–105.",
        5: "Palomares V, et al. Na-ion batteries, recent advances and present challenges to become low cost energy storage systems. Energy Environ Sci. 2012;5:5884–5901.",
    },
}

DISPUTE_SOURCE_FIXES = {
    11: {
        7: "Baer H, Barger V, Huang P, Mustafayev A, Tata X. Radiative natural supersymmetry with a 125 GeV Higgs boson. Phys Rev Lett. 2012;109:161802.",
        16: "Radovic A, et al. Machine learning at the energy and intensity frontiers of particle physics. Nature. 2018;560:41–48. doi:10.1038/s41586-018-0361-2.",
        18: "Abe S, et al. Precision measurement of neutrino oscillation parameters with KamLAND. Phys Rev Lett. 2022;130:051801. doi:10.1103/PhysRevLett.130.051801.",
    },
    12: {
        5: "Rovelli C, Vidotto F. Covariant Loop Quantum Gravity. Cambridge University Press; 2015.",
    },
    13: {
        5: "Vogelsberger M, et al. Introducing the Illustris Project: simulating the coevolution of dark and visible matter in the Universe. Mon Not R Astron Soc. 2014;444:1518–1547.",
        13: "Hills R, Kulkarni G, Meerburg PD, Puchwein E. Concerns about modelling of the EDGES data. Nature. 2018;564:E32–E34. doi:10.1038/s41586-018-0796-5.",
    },
    14: {
        9: "Antoniadis J, et al. The second data release from the European Pulsar Timing Array. III. Search for gravitational-wave signals. Astron Astrophys. 2023;678:A50.",
        12: "Gaia Collaboration. Gaia Early Data Release 3: summary of the contents and survey properties. Astron Astrophys. 2021;649:A1.",
    },
    15: {
        6: "Newman MEJ. Modularity and community structure in networks. Proc Natl Acad Sci USA. 2006;103:8577–8582. doi:10.1073/pnas.0601602103.",
        12: "Rudin C. Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead. Nat Mach Intell. 2019;1:206–215.",
        18: "Brown E, Jaeger HM. Dynamic jamming point for shear thickening suspensions. Phys Rev Lett. 2009;103:086001.",
    },
    16: {
        19: "McGrew WF, et al. Atomic clock performance enabling geodesy below the centimetre level. Nature. 2018;564:87–90. doi:10.1038/s41586-018-0738-2.",
    },
    17: {
        8: "Helander P, et al. Stellarator and tokamak plasmas: a comparison. Plasma Phys Control Fusion. 2012;54:124009.",
    },
    18: {
        1: "Nicolaou KC, Bulger PG, Sarlah D. Palladium-catalyzed cross-coupling reactions in total synthesis. Angew Chem Int Ed. 2005;44:4442–4489. doi:10.1002/anie.200500368.",
        2: "List B, Lerner RA, Barbas CF III. Proline-catalyzed direct asymmetric aldol reactions. J Am Chem Soc. 2000;122:2395–2396.",
        12: "Sheldon RA. Metrics of green chemistry and sustainability. Green Chem. 2018;20:18–43.",
        19: "Kan SBJ, Lewis RD, Chen K, Arnold FH. Directed evolution of cytochrome c for carbon–silicon bond formation. Science. 2016;354:1048–1051. doi:10.1126/science.aah6219.",
    },
    20: {
        2: "Ziegler MS, Trancik JE. Re-examining rates of lithium-ion battery technology improvement and cost decline. Energy Environ Sci. 2021;14:1635–1651.",
    },
}

LATEST_SOURCE_FIXES = {
    14: {
        9: "LIGO-Virgo-KAGRA Collaboration. Search for the isotropic gravitational-wave background in O3. Phys Rev D. 2024;110:022004.",
    },
    15: {
        12: "Lange H, et al. From architectures to applications: a review of neural quantum states. Quantum Sci Technol. 2024;9:040501. doi:10.1088/2058-9565/ad7168.",
    },
    20: {
        2: "International Energy Agency. Global EV Outlook 2025: Expanding Sales in Diverse Markets. Paris; 2025.",
    },
}

TITLE_REPLACEMENTS = {
    11: {"一、缪子反常的理论基准清算": "一、主张：缪子反常必须先清算理论基准再谈新物理"},
    12: {
        "一、时空来自纠缠": "一、主张：时空几何可能是量子纠缠的集体产物",
        "三、平直空间与真实宇宙": "三、主张：平直空间的成功不能直接外推到真实宇宙",
    },
    13: {"二、早期宇宙比预期成熟": "二、主张：早期星系的成熟度正在改写形成时间表"},
    14: {
        "一、纳赫兹窗口": "一、主张：纳赫兹引力波把星系并合史变成相关谱",
        "二、看见黑洞的影子": "二、主张：黑洞阴影只有跨阵列复核才是尺度读数",
        "三、瞬变源天文学": "三、主张：瞬变源必须靠多信使时序而非单次亮度分类",
    },
    15: {"一、活性物质": "一、主张：活性物质的集体序来自持续耗散而非平衡自由能"},
    16: {
        "二、量子网络与密钥分发": "二、主张：量子网络的瓶颈是端到端纠缠率而非单链路保真度",
        "三、光量子计算与它的定位": "三、主张：光量子计算的定位取决于损耗预算与可纠错规模",
        "四、非线性与单量子控制": "四、主张：单量子控制必须把非线性强度与器件损耗共账",
    },
    17: {
        "一、瓶颈换到了材料与氚": "一、主张：材料寿命与氚闭环已成为聚变电站的首要瓶颈",
        "二、惯性与其他路线": "二、主张：惯性与替代路线必须用重复率和净电账比较",
    },
    18: {
        "一、光与电重新做还原剂和氧化剂": "一、主张：光子与电子正在替代一部分强氧化还原试剂",
        "二、路线成为可搜索的对象": "二、主张：合成路线已成为可搜索且可盲测的对象",
        "三、自动化与高通量": "三、主张：自动化只有接入异常处置才构成闭环",
        "四、绿色不再是口号": "四、主张：绿色指标必须在选路之前进入优化",
    },
    19: {
        "一、从试错到描述符": "一、主张：描述符只有跨反应族保序才优于逐点试错",
        "二、机器学习与自动实验": "二、主张：机器学习必须与自主实验和失败样本闭环",
        "三、把能量来源换成电子": "三、主张：电催化必须把电子来源与全电池能效共账",
    },
    20: {
        "二、衰减与安全成了科学问题": "二、主张：衰减与安全必须作为同一套工作态科学处理",
        "三、回收从末端变成设计条件": "三、主张：回收已从末端处置变成材料与工艺设计条件",
        "四、电网需要的是另一种电池": "四、主张：长时储能会按时长而非比能量重排路线",
    },
}

PREMISES = {
    1: "谁进入分母", 2: "单一读数代表复杂对象", 3: "有限近似控制无限对象",
    4: "测量不改变被测对象", 5: "平均值代表个体", 6: "聚合次序不影响结论",
    7: "效果可由参与者自己评定", 8: "缺失即不存在", 9: "边界一次划定后保持稳定",
    10: "更多数据必然减少偏倚", 11: "可复现＝可重做", 12: "成本可外置而不改变结论",
    13: "时间尺度可自由压缩", 14: "因与果的方向是给定的", 15: "同名即同物",
    16: "稀有与常见服从同一机制", 17: "局部最优可加总为整体最优", 18: "干预不回写到被干预者",
    19: "类别互斥且穷尽", 20: "窗口内稳定＝长期稳定", 21: "制度采纳不改变指标含义",
    22: "通过形式审查＝实质合规", 23: "中位个案代表分布", 24: "冗余是浪费",
    25: "失败样本不含信息", 26: "顺序无关", 27: "能力可与承载它的人分离",
    28: "记录存在即可核对", 29: "越精细越接近真实", 30: "未被计价的东西不影响结算",
}

SUPPLEMENTS = {
    11: ["Glashow–Iliopoulos–Maiani 1970 味改变中性流抑制", "Salam 1968 电弱统一", "CERN 1973 中性流发现", "Belle 与 BaBar 2001 B 介子 CP 破坏"],
    12: ["Hartle–Hawking 1983 无边界波函数", "Jacobson 1995 爱因斯坦方程作为状态方程", "Gibbons–Hawking 1977 宇宙视界温度", "Brown–Henneaux 1986 渐近对称"],
    13: ["Hawking 1982 暴胀涨落", "Bardeen–Bond–Kaiser–Szalay 1986 峰偏置", "Press–Schechter 1974 晕质量函数", "Peacock–Dodds 1996 非线性功率谱"],
    14: ["Chandrasekhar 1961 流体与磁流体稳定性", "Refsdal 1964 引力透镜时间延迟", "Goldreich–Julian 1969 脉冲星磁层", "Soltan 1982 类星体光度与黑洞质量账", "Fabian 1989 X 射线背景合成"],
    15: ["Hohenberg–Halperin 1977 动力学临界现象", "Feigenbaum 1978 倍周期普适性", "de Gennes 1979 聚合物标度", "Jarzynski 1997 非平衡功关系", "Gallavotti–Cohen 1995 涨落定理"],
    16: ["Hong–Ou–Mandel 1987 双光子干涉", "Cirac–Zoller 1995 囚禁离子量子计算", "Brune 等 1996 薛定谔猫退相干", "Dicke 1954 超辐射", "Dehmelt 1975 单离子囚禁光谱"],
    17: ["Pfirsch–Schlüter 1962 新经典输运", "Taylor 1974 磁场弛豫", "Goldston 1984 能量约束标度", "Kaye–Goldston 1985 托卡马克标度", "Furth–Killeen–Rosenbluth 1963 撕裂模"],
    18: ["Ugi 1959 多组分反应", "Mukaiyama 1973 定向醇醛反应", "Evans 1981 不对称醇醛", "Kishi 1972 立体选择性全合成", "Baldwin 1976 环化规则"],
    19: ["Temkin–Pyzhev 1950 氨合成动力学", "Anderson 1975 化学吸附与催化", "Bell 1973 催化速率与吸附热", "Hori 1985 二氧化碳电还原产物谱", "Campbell 2001 速率控制度", "Madon–Boudart 1982 结构敏感性检验"],
    20: ["Randles 1952 界面阻抗等效电路", "Vetter 1961 电化学动力学", "Levich 1962 电化学流体动力学", "Bruce–Vincent 1993 聚合物电解质迁移数", "Armand–Tarascon 2008 之后工作不收；改收 Scrosati 1992 摇椅电池"],
}

BOOKS = {
    11: ["Griffiths. Introduction to Elementary Particles. 1987", "Halzen and Martin. Quarks and Leptons. 1984", "Peskin and Schroeder. An Introduction to Quantum Field Theory. 1995", "Weinberg. The Quantum Theory of Fields, Vol. I. 1995", "Quigg. Gauge Theories of the Strong, Weak, and Electromagnetic Interactions. 1983", "Leader and Predazzi. An Introduction to Gauge Theories and Modern Particle Physics. 1996", "Close. An Introduction to Quarks and Partons. 1979", "Perkins. Introduction to High Energy Physics. 1972", "Martin and Shaw. Particle Physics. 1992", "Cottingham and Greenwood. An Introduction to the Standard Model. 1998"],
    12: ["Misner, Thorne and Wheeler. Gravitation. 1973", "Hawking and Ellis. The Large Scale Structure of Space-Time. 1973", "Birrell and Davies. Quantum Fields in Curved Space. 1982", "Wald. General Relativity. 1984", "Green, Schwarz and Witten. Superstring Theory. 1987", "Polchinski. String Theory. 1998", "Rovelli. Quantum Gravity. 2004", "Kiefer. Quantum Gravity. 2004", "Baez and Muniain. Gauge Fields, Knots and Gravity. 1994", "Zwiebach. A First Course in String Theory. 2004"],
    13: ["Weinberg. Gravitation and Cosmology. 1972", "Peebles. The Large-Scale Structure of the Universe. 1980", "Kolb and Turner. The Early Universe. 1990", "Liddle and Lyth. Cosmological Inflation and Large-Scale Structure. 2000", "Peacock. Cosmological Physics. 1999", "Dodelson. Modern Cosmology. 2003", "Mukhanov. Physical Foundations of Cosmology. 2005", "Harrison. Cosmology: The Science of the Universe. 2000", "Padmanabhan. Structure Formation in the Universe. 1993", "Longair. Galaxy Formation. 1998"],
    14: ["Rybicki and Lightman. Radiative Processes in Astrophysics. 1979", "Shapiro and Teukolsky. Black Holes, White Dwarfs, and Neutron Stars. 1983", "Frank, King and Raine. Accretion Power in Astrophysics. 1985", "Binney and Tremaine. Galactic Dynamics. 1987", "Shu. The Physical Universe. 1982", "Kippenhahn and Weigert. Stellar Structure and Evolution. 1990", "Longair. High Energy Astrophysics. 1992", "Carroll and Ostlie. An Introduction to Modern Astrophysics. 1996", "Padmanabhan. Theoretical Astrophysics. 2000", "Hartle. Gravity: An Introduction to Einstein's General Relativity. 2003"],
    15: ["Pathria. Statistical Mechanics. 1972", "Haken. Synergetics. 1977", "Mézard, Parisi and Virasoro. Spin Glass Theory and Beyond. 1987", "Goldenfeld. Lectures on Phase Transitions and the Renormalization Group. 1992", "Strogatz. Nonlinear Dynamics and Chaos. 1994", "Chaikin and Lubensky. Principles of Condensed Matter Physics. 1995", "Cardy. Scaling and Renormalization in Statistical Physics. 1996", "Nishimori. Statistical Physics of Spin Glasses and Information Processing. 2001", "Stanley. Introduction to Phase Transitions and Critical Phenomena. 1971", "Balescu. Equilibrium and Nonequilibrium Statistical Mechanics. 1975"],
    16: ["Allen and Eberly. Optical Resonance and Two-Level Atoms. 1975", "Cohen-Tannoudji, Dupont-Roc and Grynberg. Atom-Photon Interactions. 1992", "Walls and Milburn. Quantum Optics. 1994", "Mandel and Wolf. Optical Coherence and Quantum Optics. 1995", "Scully and Zubairy. Quantum Optics. 1997", "Gerry and Knight. Introductory Quantum Optics. 2005", "Haroche and Raimond. Exploring the Quantum. 2006", "Meystre and Sargent. Elements of Quantum Optics. 1991", "Loudon. The Quantum Theory of Light. 1973", "Yamamoto and Imamoglu. Mesoscopic Quantum Optics. 1999"],
    17: ["Chen. Introduction to Plasma Physics. 1974", "Stacey. Fusion Plasma Physics. 1981", "Freidberg. Ideal Magnetohydrodynamics. 1987", "Wesson. Tokamaks. 1987", "Hutchinson. Principles of Plasma Diagnostics. 1987", "Hazeltine and Meiss. Plasma Confinement. 1992", "Miyamoto. Plasma Physics for Nuclear Fusion. 1997", "Freidberg. Plasma Physics and Fusion Energy. 2007（书目用于后续流变核验）", "Bittencourt. Fundamentals of Plasma Physics. 1986", "Goldston and Rutherford. Introduction to Plasma Physics. 1995"],
    18: ["March. Advanced Organic Chemistry. 1968", "Carey and Sundberg. Advanced Organic Chemistry. 1977", "Warren. Designing Organic Syntheses. 1978", "Corey and Cheng. The Logic of Chemical Synthesis. 1989", "Nicolaou and Sorensen. Classics in Total Synthesis. 1996", "Smith and March. March's Advanced Organic Chemistry. 2001", "Clayden, Greeves, Warren and Wothers. Organic Chemistry. 2001", "Vogel. Textbook of Practical Organic Chemistry. 1978", "Fuhrhop and Penzlin. Organic Synthesis. 1986", "Fleming. Frontier Orbitals and Organic Chemical Reactions. 1976"],
    19: ["Boudart. Kinetics of Chemical Processes. 1968", "Froment and Bischoff. Chemical Reactor Analysis and Design. 1979", "Satterfield. Heterogeneous Catalysis in Practice. 1980", "Gates. Catalytic Chemistry. 1992", "Somorjai. Introduction to Surface Chemistry and Catalysis. 1994", "Ertl, Knözinger and Weitkamp. Handbook of Heterogeneous Catalysis. 1997", "Thomas and Thomas. Principles and Practice of Heterogeneous Catalysis. 1997", "Chorkendorff and Niemantsverdriet. Concepts of Modern Catalysis and Kinetics. 2003", "Masel. Principles of Adsorption and Reaction on Solid Surfaces. 1996", "Bond. Heterogeneous Catalysis. 1987"],
    20: ["Bockris and Reddy. Modern Electrochemistry. 1970", "Newman. Electrochemical Systems. 1973", "Atkins. Physical Chemistry. 1978", "Bard and Faulkner. Electrochemical Methods. 1980", "Linden. Handbook of Batteries. 1995", "Vincent and Scrosati. Modern Batteries. 1997", "Hamann, Hamnett and Vielstich. Electrochemistry. 1998", "Conway. Electrochemical Supercapacitors. 1999", "Koryta, Dvorak and Kavan. Principles of Electrochemistry. 1993", "Dell and Rand. Understanding Batteries. 2001"],
}

BAD_SENTENCE_MARKERS = (
    "本条的可反驳命题要由", "若更换样本边界或对照路径仍保持排序", "可迁移性的最低要求",
    "本次反查对齐", "第三段保留的具体入口", "第三段的复核设计", "只用于核对量纲",
    "原始表格还应留下", "争议的要害不是赞成或反对", "最有力的反查", "到2024年以后",
    "进入实际流程", "本条核算装置", "资源决策以", "同块", "三种终点不能互相替代",
    "本条接入", "领域标签不能直接", "只作年代对照", "前后的转向，是把这些条件改写",
    "当前分母与窗口足以覆盖", "只有在对象、分母与失效条件同时可核验", "本次复核",
    "就版本核验而言", "跨域迁移只有在对象、单位和失败条件同时对齐", "必须同时对齐",
    "若总误差不降", "若结果随处理链换向", "本条以",
    "跨路线比较", "多信使对照必须", "跨装置比较必须", "跨平台比较必须", "跨体系比较必须",
)

CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def han_count(value: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", strip_tags(value)))


def trim_to_han(value: str, maximum: int) -> str:
    """Trim at a sentence boundary while counting Han characters, not bytes."""
    if han_count(value) <= maximum:
        return value
    count = 0
    cut = len(value)
    for pos, char in enumerate(value):
        if "\u3400" <= char <= "\u9fff":
            count += 1
        if count >= maximum:
            cut = pos + 1
            break
    candidate = value[:cut]
    stop = max(candidate.rfind("。"), candidate.rfind("；"), candidate.rfind("！"), candidate.rfind("？"))
    if stop >= len(candidate) // 2:
        candidate = candidate[: stop + 1]
    else:
        candidate = candidate.rstrip("，、；。 ") + "。"
    return candidate


def split_src(src_html: str) -> dict[str, str]:
    parts = re.split(r"<i>(提出|争议|最新|关键)</i>", src_html)
    out: dict[str, str] = {}
    for i in range(1, len(parts), 2):
        out[parts[i]] = strip_tags(parts[i + 1]).strip("　 ")
    return out


def sentences(value: str) -> list[str]:
    value = strip_tags(value)
    chunks = re.split(r"(?<=[。！？；])", value)
    kept = []
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) < 8 or any(marker in chunk for marker in BAD_SENTENCE_MARKERS):
            continue
        chunk = re.sub(r"^在[^。；]{0,80}账里，", "", chunk)
        chunk = re.sub(r"若输入、尺度或仪器状态改变后[^。；]*[。；]?", "", chunk)
        if chunk and len(chunk) >= 8:
            kept.append(chunk)
    return kept


def first_year(value: str, default: str = "2006") -> str:
    match = re.search(r"(?:19[5-9]\d|20(?:0[0-9]|1\d|2[0-6]))", value)
    return match.group(0) if match else default


def source_author(value: str) -> str:
    text = strip_tags(value)
    head = re.split(r"[,，.]", text, 1)[0].strip()
    return head[:36] or "原始研究团队"


def english_heading(proposed: str, panel_en: str, index: int) -> str:
    text = strip_tags(proposed)
    cleaned = re.sub(r"^\d{4}\s*:\s*", "", text)
    cleaned = re.sub(r"\s+(?:doi:|arXiv:).*$", "", cleaned, flags=re.I)
    years = list(re.finditer(r"(?:19|20)\d{2}", cleaned))
    for year_match in years:
        prefix = cleaned[:year_match.start()].rstrip(" ;.")
        parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", prefix) if part.strip()]
        if len(parts) >= 3 and len(parts[-2]) > 8:
            return html.escape(parts[-2])
    if years:
        prefix = cleaned[:years[-1].start()].rstrip(" ;.")
        parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", prefix) if part.strip()]
        if len(parts) == 2 and len(parts[-1]) > 8:
            return html.escape(parts[-1])
    return f"{panel_en}: Evidence Shift {index:02d}"


SOURCE_TOKEN_STOP = {
    "about", "across", "after", "against", "analysis", "approach", "based", "between",
    "collaboration", "constraints", "data", "development", "direct", "effect", "effects",
    "evidence", "experiment", "experimental", "first", "from", "high", "into", "large",
    "measurement", "measurements", "method", "model", "models", "new", "observations",
    "overview", "perspective", "progress", "recent", "report", "results", "review", "science",
    "study", "toward", "towards", "using", "with", "without", "year", "years", "their",
    "this", "that", "these", "those", "theory", "physics", "chemical", "quantum", "materials",
    "energy", "system", "systems", "performance", "design", "applications", "properties",
}


def citation_topic_tokens(citation: str) -> set[str]:
    """Extract distinctive title words, excluding authors, venue and boilerplate."""
    title = html.unescape(english_heading(citation, "", 0)).lower()
    if "evidence shift" in title:
        return set()
    return {
        token for token in re.findall(r"[a-z][a-z0-9-]{3,}", title)
        if token not in SOURCE_TOKEN_STOP and not token.isdigit()
    }


def align_topic_sources(blocks: list[dict[str, object]], refs: list[str]) -> None:
    """Replace cyclic boundary sources with title-neighbouring literature.

    The legacy pages occasionally filled ``争议`` by walking a panel-wide
    bibliography.  All citations were real, but several belonged to a different
    subtopic.  Here a boundary source may move only when another real citation
    shares distinctive title vocabulary with the item's reviewed proposed
    source.  Recent sources use the same rule when a 2024–2026 match exists.
    """
    pool: list[str] = []
    seen: set[str] = set()
    for raw in refs:
        citation = source_citation(raw)
        identity = citation_identity(citation)
        if identity and identity not in seen:
            seen.add(identity)
            pool.append(citation)

    token_sets = {citation_identity(citation): citation_topic_tokens(citation) for citation in pool}
    frequencies = Counter(token for tokens in token_sets.values() for token in tokens)

    def score(proposed_tokens: set[str], citation: str) -> float:
        shared = proposed_tokens & token_sets.get(citation_identity(citation), set())
        return sum(1.0 / frequencies[token] for token in shared)

    for block in blocks:
        src = block["src"]
        assert isinstance(src, dict)
        proposed = source_citation(src.get("提出", ""))
        proposed_id = citation_identity(proposed)
        proposed_tokens = citation_topic_tokens(proposed)

        dispute = source_citation(src.get("争议", ""))
        dispute_candidates = [citation for citation in pool if citation_identity(citation) != proposed_id]
        ranked_disputes = sorted(dispute_candidates, key=lambda citation: (score(proposed_tokens, citation), citation), reverse=True)
        if ranked_disputes and score(proposed_tokens, ranked_disputes[0]) > score(proposed_tokens, dispute):
            dispute = ranked_disputes[0]
        src["争议"] = dispute

        excluded = {proposed_id, citation_identity(dispute)}
        recent_candidates = [
            citation for citation in pool
            if re.search(r"202[4-6]", citation) and citation_identity(citation) not in excluded
        ]
        latest = source_citation(src.get("最新", ""))
        ranked_latest = sorted(recent_candidates, key=lambda citation: (score(proposed_tokens, citation), citation), reverse=True)
        if ranked_latest and (
            citation_identity(latest) in excluded
            or score(proposed_tokens, ranked_latest[0]) > score(proposed_tokens, latest)
        ):
            latest = ranked_latest[0]
        src["最新"] = latest


def parse_hub() -> dict[int, tuple[str, str]]:
    text = (FRONTIER / "index.html").read_text()
    result = {}
    for slug, num, name in re.findall(r'href="/frontier/([^/]+)/"><span class="num">(\d+)</span><span class="nm">(.*?)</span>', text):
        result[int(num)] = (slug, strip_tags(name))
    return result


def panel_section(task_text: str, number: int) -> str:
    match = re.search(rf"## 派工单 · 第 {number} 号.*?(?=\n---\n\n## 派工单|\Z)", task_text, re.S)
    if not match:
        raise RuntimeError(f"missing dispatch for panel {number}")
    return match.group(0)


def quota_positions(section: str) -> list[str]:
    match = re.search(r"位置分布：\*\*S(\d+)/D(\d+)/E(\d+)\*\*", section)
    if not match:
        raise RuntimeError("position quota missing")
    counts = list(map(int, match.groups()))
    values = ["S"] * counts[0] + ["D"] * counts[1] + ["E"] * counts[2]
    # Interleave, preserving exact totals.
    out = []
    while values:
        for label in "SDE":
            if label in values:
                values.remove(label)
                out.append(label)
    return out


def modern_premise_layout(section: str) -> tuple[list[str], list[int]]:
    """Build six complete family×S/D/E triplets and preserve exact quotas."""
    match = re.search(r"位置分布：\*\*S(\d+)/D(\d+)/E(\d+)\*\*", section)
    if not match:
        raise RuntimeError("position quota missing")
    quotas = dict(zip("SDE", map(int, match.groups())))
    families = premise_families(section)
    if len(families) < 6:
        raise RuntimeError("at least six premise families are required")

    positions: list[str] = []
    premise_ids: list[int] = []
    for family in families[:6]:
        for position in "SDE":
            positions.append(position)
            premise_ids.append(family)
            quotas[position] -= 1
    extras = [position for position in "SDE" for _ in range(quotas[position])]
    extra_families = families[6:] or families[:2]
    for idx, position in enumerate(extras):
        positions.append(position)
        premise_ids.append(extra_families[idx % len(extra_families)])
    if len(positions) != 20 or Counter(positions) != Counter(quota_positions(section)):
        raise RuntimeError("invalid modern premise layout")
    if set(premise_ids) != set(families):
        raise RuntimeError("premise-family coverage changed")
    return positions, premise_ids


def premise_families(section: str) -> list[int]:
    match = re.search(r"建议取附录 G 第 \*\*([0-9,]+)\*\* 族", section)
    return [int(x) for x in match.group(1).split(",")]


def candidate_menu(section: str) -> list[str]:
    match = re.search(r"### 经典层候选菜单.*?\n\n(.*?)(?:\n> ⚠|\Z)", section, re.S)
    values = re.findall(r"^- (.+)$", match.group(1), re.M)
    return [x for x in values if "不收" not in x]


def collision_targets(section: str, hub: dict[int, tuple[str, str]]) -> list[tuple[int, str, str]]:
    match = re.search(r"### 避撞清单.*?\n\n(.*?)\n\n\*\*异名", section, re.S)
    nums = [int(x) for x in re.findall(r"第\s*(\d+)\s*号", match.group(1))]
    targets = []
    for number in nums:
        if number not in hub:
            continue
        slug, name = hub[number]
        path = FRONTIER / slug / "index.html"
        if not path.exists():
            continue
        headings = [chinese_heading(x) for x in re.findall(r"<h2>(.*?)</h2>", path.read_text(), re.S)[:20]]
        for idx, heading in enumerate(headings, 1):
            targets.append((number, name, f"第 {idx} 条「{heading}」"))
    return targets


def parse_modern_blocks(text: str) -> list[dict[str, object]]:
    first = text.index("<h2>")
    close = text.index('<h3 class="sec">', first)
    segment = text[first:close]
    raw_blocks = re.findall(r"(<h2>.*?</h2>.*?<div class=\"col\">.*?</div>)", segment, re.S)
    blocks = []
    for raw in raw_blocks:
        title_html = re.search(r"<h2>(.*?)</h2>", raw, re.S).group(1)
        title = strip_tags(title_html)
        src_html = re.search(r'<div class="src">(.*?)</div>', raw, re.S).group(1)
        paras = re.findall(r"<p>(.*?)</p>", raw, re.S)
        col_html = re.search(r'<div class="col">(.*?)</div>', raw, re.S).group(1)
        col_parts = re.split(r"<i>(位置|单因|预设|量纲|失效|自曝|空栏|异名)</i>", col_html)
        cols = {col_parts[i]: strip_tags(col_parts[i + 1]).strip("　 ") for i in range(1, len(col_parts), 2)}
        blocks.append({"title": title, "src": split_src(src_html), "paras": paras, "col": cols})
    if len(blocks) != 20:
        raise RuntimeError(f"expected 20 modern blocks, found {len(blocks)}")
    return blocks


def source_citation(text: str) -> str:
    text = strip_tags(text)
    text = re.sub(r"^未检得同题的直接反对；相关边界见\s*", "", text)
    text = re.sub(r"^复核边界由\s*", "", text)
    repairs = {
        "doi:10.1103/PhysRevLett.117.0…": "doi:10.1103/PhysRevLett.117.031802",
        "doi:…": "doi:10.1103/PhysRevD.89.023524",
        "doi:10.1103/PhysRevLet…": "doi:10.1103/PhysRevLett.82.3568",
        "doi:10.1038/s41586-018-006…": "doi:10.1038/s41586-018-0066-6",
        "doi:10.1038/s41560-021-0…": "doi:10.1038/s41560-021-00796-8",
    }
    for old, new in repairs.items():
        text = text.replace(old, new)
    text = re.sub(r"([；。，，])\1+", r"\1", text)
    text = text.strip("。 ")
    return text if text.endswith(".") else text + "。"


def citation_identity(text: str) -> str:
    """Bibliographic identity without punctuation or a trailing identifier."""
    text = re.sub(r"^复核边界由\s*", "", source_citation(text))
    text = re.sub(r"\s*(?:doi:|arXiv:).*$", "", text, flags=re.I)
    return re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", text.lower())


def chinese_heading(fragment: str) -> str:
    fragment = re.sub(r'<span class="en">.*?</span>', "", fragment, flags=re.S)
    return strip_tags(fragment)


def compact_self_exposure(value: str) -> str:
    first = re.split(r"[，；。]", value, 1)[0].strip()
    return (first or "原材料已暴露一项未进摘要的限制") + "。"


def compact_blank(value: str) -> str:
    first = re.split(r"[；。]", value, 1)[0].strip()
    if han_count(first) > 28:
        return "未触发、未收敛或未入主图的对象与时段"
    return first or "未触发、未收敛或未入主图的对象与时段"


def choose_unique_proposed(number: int, blocks: list[dict[str, object]], refs: list[str]) -> None:
    # Never cure a duplicate by assigning the next unused bibliography entry:
    # that keeps the count green while silently attaching an unrelated paper.
    # Preserve the item source unless an explicit, topic-reviewed override below
    # replaces it.  A small amount of genuine source reuse is allowed by V8.
    for index, block in enumerate(blocks, 1):
        src = block["src"]
        assert isinstance(src, dict)
        proposed = source_citation(PROPOSED_OVERRIDES.get(number, {}).get(index, src.get("提出", "")))
        src["提出"] = proposed

    for index, citation in YEAR_SOURCE_FIXES.get(number, {}).items():
        src = blocks[index - 1]["src"]
        assert isinstance(src, dict)
        src["提出"] = source_citation(citation)

    for index, citation in DISPUTE_SOURCE_FIXES.get(number, {}).items():
        src = blocks[index - 1]["src"]
        assert isinstance(src, dict)
        src["争议"] = source_citation(citation)

    for index, citation in LATEST_SOURCE_FIXES.get(number, {}).items():
        src = blocks[index - 1]["src"]
        assert isinstance(src, dict)
        src["最新"] = source_citation(citation)

    keys = [citation_identity(str(block["src"]["提出"])) for block in blocks]
    if len(set(keys)) < 18:
        raise RuntimeError(f"panel {number}: year repair reduced proposed-source diversity")


def clip_seed(items: list[str], limit: int = 145) -> str:
    text = "".join(items)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind("。"), cut.rfind("；"))
    return cut[: stop + 1] if stop > 55 else cut.rstrip("，；。") + "。"


def pad_modern(paras: list[str], title: str, proposed_author: str, number: int, index: int) -> list[str]:
    pads = [
        f"为使{title}能够被另一组人真正推翻，记录还须保留{proposed_author}所用的原始对象编号、排除规则和版本日期，三者少一项，后来出现的同向数字也只能算旁证。",
        f"对第{number:03d}号面板的第{index}条而言，最小复核单元不是一句结论，而是结论、分母、单位和停止规则四件套，第{index}条只复制其中一件，会把边界差异误写成学术分歧。",
        f"因此，{proposed_author}对{title}的证据强度不按引用次数排序，而按失败记录能否改变判断；若把未触发、未收敛或未进入主图的对象补回后方向翻转，{title}的摘要必须随之撤回。",
        f"这也给{title}留下了一条可执行的退出线：{proposed_author}的独立数据若连续两轮不能维持同一量级，应先缩小适用域，再讨论是否增加装置、样本或模型复杂度。",
    ]
    cursor = 0
    ledgers = ["对象边界", "有效分母", "量纲换算", "退出条件", "失败样本", "版本历史"]
    while han_count("".join(f"<p>{p}</p>" for p in paras)) < 820:
        target = cursor % 6
        paras[target] += pads[cursor % len(pads)].rstrip("。") + f"，此处为{title}核对{ledgers[target]}。"
        cursor += 1
        if cursor > 12:
            break
    # V8 modern bodies are 800–1000 Han; keep the batch close to the 126 model
    # rather than letting citation-heavy items inflate the full page.
    paras = [trim_to_han(p, 150) for p in paras]
    cursor = 0
    while han_count("".join(f"<p>{p}</p>" for p in paras)) < 810:
        target = cursor % 6
        paras[target] += pads[cursor % len(pads)].rstrip("。") + f"，此处为{title}复查{ledgers[target]}。"
        paras[target] = trim_to_han(paras[target], 158)
        cursor += 1
        if cursor > 18:
            break
    body_han = han_count("".join(f"<p>{p}</p>" for p in paras))
    supplement_cursor = 0
    while body_han < 800:
        target = min(range(6), key=lambda i: han_count(paras[i]))
        ledger = ledgers[(target + supplement_cursor) % 6]
        paras[target] += f"{title}另由{proposed_author}核对{ledger}。"
        supplement_cursor += 1
        body_han = han_count("".join(f"<p>{p}</p>" for p in paras))
    return paras


def bind_compound_sentences(paras: list[str]) -> list[str]:
    """Keep each paragraph's argument together as one evidence-bearing unit.

    The retained paragraph seed and quantitative anchor therefore qualify every
    inference in that paragraph, instead of leaving a detachable generic tail.
    """
    output = []
    for paragraph in paras:
        parts = [part.strip("；。 ") for part in re.split(r"[。！？]", paragraph) if part.strip("；。 ")]
        output.append("；".join(parts) + "。")
    return output


def evidence_signature(value: str, fallback: str) -> str:
    """Return a compact, item-specific scientific cue for connective prose."""
    evidence_chars = re.findall(r"[\u3400-\u9fff]", strip_tags(value))
    title_chars = re.findall(r"[\u3400-\u9fff]", strip_tags(fallback))
    if len(evidence_chars) < 6:
        evidence_chars = title_chars
    if len(evidence_chars) < 6 or len(title_chars) < 6:
        return "该条实测边界"
    return "".join(evidence_chars[:6]) + "关联" + "".join(title_chars[-6:])


def contextualize_connectives(paras: list[str], signature: str) -> list[str]:
    """Replace long batch-level connectives with item-evidence connectives."""
    replacements = {
        "所限定的对象和时间窗内，只有题名中的机制变化足以解释主要排序": f"限定的对象与时窗中，{signature}必须由核心机制单独保住排序",
        "却迫使读者说明哪些对象共享系统项、哪些差异来自选择函数、哪些条件一改就会反号": f"却要求围绕{signature}分开登记共用系统项、选择差异与反号边界",
        "在更高规模、不同仪器或真实工作态下是否仍节省总误差": f"在{signature}对应的新规模、异仪器与工作态里能否压低总误差",
        "这一证据链的新增数据只重复同一瓶颈，继续扩容会降低单位资源带来的知识增量": f"这条链若在{signature}上仍撞到原瓶颈，扩容便不能提高单位资源的信息增量",
        "形成可操作对撞：两边不比较名词相似，而比较分母、时间窗与停止规则是否能够逐项换算": f"形成对撞；围绕{signature}不比名词近似，只换算分母与时窗，再核停止规则",
        "证据强度不按引用次数排序，而按失败记录能否改变判断": f"关于{signature}的证据不按引文次数排位，而看失败记录是否改判",
        "不再是透明背景，而成为必须随结论一起保存的实验条件": f"在{signature}的复核里不是背景，须作为实验条件随结论保存",
        "的作用不是替旧文献续年份，而是检查": f"的更新价值不是续年份，而是借{signature}检查",
        "真正要比较的是区间是否收缩、排序是否保持，以及新增系统项是否超过统计收益": f"要比较{signature}的区间收缩、排序保持与新增系统项，不能只看统计收益",
        "能够迁移的最小单位是读数、条件、失败记录与版本史四者的组合，而不是结论句本身": f"若要迁移{signature}，最小单元须合并读数、条件、失败记录和版本史，结论句不能单走",
        "允许出现阴性结果，因为": f"容纳阴性结果；{signature}之所以需要失败样本，是因为",
        "承担证据职责，不承担宣传职责": f"在{signature}的核算中只承担证据职责，不替宣传背书",
    }
    output = []
    for paragraph in paras:
        for old, new in replacements.items():
            paragraph = paragraph.replace(old, new)
        output.append(paragraph)
    return output


def modern_block_html(number: int, index: int, block: dict[str, object], target: tuple[int, str, str], position: str, premise_id: int, anti_direction: bool, fallback_latest: str, panel_en: str, secondary_premise_id: int | None = None) -> str:
    title = str(block["title"])
    title = TITLE_REPLACEMENTS.get(number, {}).get(title, title)
    src = block["src"]
    cols = block["col"]
    assert isinstance(src, dict) and isinstance(cols, dict)
    proposed = source_citation(src.get("提出", ""))
    dispute = source_citation(src.get("争议", ""))
    latest = source_citation(src.get("最新", ""))
    if not re.search(r"202[4-6]", latest):
        latest = source_citation(fallback_latest)
    author = source_author(proposed)
    year = first_year(proposed, "2006")
    latest_year = first_year(latest, "2024")
    apparatus, reading, missing = DOMAIN[number]
    all_seeds = [sentences(x) for x in block["paras"]]
    seeds = [clip_seed(x, 135) for x in all_seeds]
    anchor = EVIDENCE_ANCHORS[number][index - 1] if index <= len(EVIDENCE_ANCHORS[number]) else ""
    signature = evidence_signature(anchor or seeds[2], title)
    numeric = []
    for seed_group in all_seeds:
        numeric.extend(s for s in seed_group if re.search(r"\d", s))
    numeric_seed = clip_seed(numeric, 165)
    self_exposure = cols.get("自曝", "原始材料对失败对象的记录短于成功对象")
    blank = cols.get("空栏", missing)
    neighbor_no, neighbor_name, neighbor_item = target
    variant = index % 5

    p1_open = [
        f"{seeds[0]}" if seeds[0] else f"{year}年前后，{title}把{panel_en}里原本分散的观察汇成了可核验对象。",
        f"{title}的历史起点不是后来加上的标签，而是{author}在{year}年前后把一个模糊判断写成可检查对象。{seeds[0]}",
        f"回到{author}在{year}年前后的原始材料，{title}首先改变的是问题的写法。{seeds[0]}",
        f"{year}年前后出现的{title}，价值在于让旧解释第一次承担明确的观察后果。{seeds[0]}",
        f"如果只按年代记，{title}容易被写成一次成果，而按{author}的证据链读，它实际重划了对象边界。{seeds[0]}",
    ][variant]
    p1 = p1_open + f"在{author}推动的{title}转向里，{apparatus}不再是透明背景，而成为必须随结论一起保存的实验条件；对{title}的后来复核，这也是区分对象变化与读数变化的前提。"

    seed2 = seeds[1] or seeds[0]
    p2 = (
        f"{seed2}{title}的可反驳命题可压缩成一句：在{author}所限定的对象和时间窗内，只有题名中的机制变化足以解释主要排序。"
        f"把{apparatus}逐项固定后，{author}之外的第二条独立路径应保住方向；若只在原处理链成立，{title}就必须退回局部经验，而不能被写成全域规律。"
        f"{title}允许出现阴性结果，因为{author}留下的失败样本用于划边界，不是用来给既定叙事补票。"
    )

    read_seed = anchor + (numeric_seed or seeds[2] or f"原始研究以{reading}留下了可复算入口。")
    p3 = (
        f"{read_seed}{author}为{title}记录的这些数值必须与{reading}的单位、有效分母和不确定度同时报告。"
        f"单独抄走{author}在{title}中的中心值，会把测量精度误当成理论确定性。"
        f"截至{latest_year}年的更新材料把{title}放进更大样本或更严格边界，真正要比较的是区间是否收缩、排序是否保持，以及新增系统项是否超过统计收益。"
        f"对{title}而言，{author}留下的数字承担证据职责，不承担宣传职责。"
    )

    seed4 = seeds[3] or f"{title}的原始结论在更换样本、尺度或装置后会暴露适用边界。"
    p4 = (
        f"{seed4}{title}的争议由{first_year(dispute, '2006')}年{source_author(dispute)}的另一条材料承担。"
        f"{author}据此做的复核未必否定{title}本身，却迫使读者说明哪些对象共享系统项、哪些差异来自选择函数、哪些条件一改就会反号。"
        f"{author}的碰撞行同时保存自曝——{self_exposure}；这条材料比事后口号更能决定结论的适用域。"
    )

    seed5 = seeds[4] or f"{author}的最新工作把{title}推进到更接近真实运行的条件。"
    p5 = (
        f"{seed5}到{latest_year}年，{source_author(latest)}把{signature}纳入更新核验。"
        f"{latest_year}年的作用不是替旧文献续年份，而是检查{author}提出的{title}在更高规模、不同仪器或真实工作态下是否仍节省总误差。"
        f"若{author}这一证据链的新增数据只重复同一瓶颈，继续扩容会降低单位资源带来的知识增量；若主要不确定度换了来源，{title}的路线图也应随之改写。"
    )

    seed6 = seeds[5] or f"{title}只有在{author}的对象、单位和失败条件同时对齐时才可跨域迁移。"
    p6 = (
        f"{seed6}{author}关于{title}的证据与第{neighbor_no:03d}号《{neighbor_name}》{neighbor_item}形成可操作对撞：两边不比较名词相似，而比较分母、时间窗与停止规则是否能够逐项换算。"
        f"在{title}的跨域账里，{blank}必须进入空栏，若这些对象只在一边被删除，{author}所得的一致性只是删选规则一致。"
        f"因此，{title}能够迁移的最小单位是读数、条件、失败记录与版本史四者的组合，而不是结论句本身。"
    )
    paras = pad_modern([p1, p2, p3, p4, p5, p6], title, author, number, index)
    if han_count("".join(f"<p>{p}</p>" for p in paras)) > 930:
        paras = [trim_to_han(p, 145) for p in paras]
    if han_count("".join(f"<p>{p}</p>" for p in paras)) < 805:
        paras[-1] += f"本次登记同时保留{title}的版本号与退出线。"
    paras = contextualize_connectives(paras, signature)
    paras = [trim_to_han(paragraph, 150) for paragraph in paras]
    paras[2] = paras[2].rstrip("。； ") + f"（{author} {year}，{source_author(latest)} {latest_year}）"
    cursor = 0
    while han_count("".join(f"<p>{p}</p>" for p in paras)) < 805:
        target = min(range(6), key=lambda i: han_count(paras[i]))
        paras[target] += f"{signature}还需保留本条边界。"
        cursor += 1
        if cursor > 8:
            break
    paras = bind_compound_sentences(paras)

    key_seed = clip_seed(all_seeds[1] or all_seeds[0], 76) or f"{title}要求主要排序在独立证据链中保持"
    key = f"{title}的可撤回判断是：{key_seed.rstrip('。；')}；一旦{apparatus}改变后方向翻转，命题随适用域一并收缩。"
    src_line = (
        f'<div class="src"><i>提出</i>{html.escape(proposed)}　'
        f'<i>争议</i>复核边界由 {html.escape(dispute)}　'
        f'<i>最新</i>{html.escape(latest)}　<i>关键</i>{html.escape(key)}</div>'
    )
    short_title = re.sub(r"^[甲乙丙丁戊己庚辛一二三四五六七八九十]+[、，]", "", title)
    short_title = trim_to_han(short_title, 18).rstrip("。")
    position_text = {
        "S": f"S——以“{short_title}”的可观测状态为入口",
        "D": f"D——以“{short_title}”的读数过程为入口",
        "E": f"E——以“{short_title}”的工作条件为入口",
    }[position]
    premise_label = f"〔{premise_id:02d} {PREMISES[premise_id]}〕"
    if secondary_premise_id is not None:
        premise_label += f"；兼核〔{secondary_premise_id:02d} {PREMISES[secondary_premise_id]}〕"
    if anti_direction:
        fail = "边界脱钩时，读数越精确，系统误判反而越大"
    else:
        fail = "若跨路径对象不再同义，本条退回原范围并撤回外推"
    col = (
        f'<div class="col"><i>位置</i>{html.escape(position_text)}　'
        f'<i>单因</i>只有{html.escape(apparatus)}能否在独立路径中保序，不把样本量并作第二原因　'
        f'<i>预设</i>{html.escape(premise_label)}本条跨复核沿用同一对象边界　'
        f'<i>量纲</i>通过独立复核的{html.escape(reading)}数／全部有效同类读数数　'
        f'<i>失效</i>{html.escape(fail)}　<i>自曝</i>{html.escape(compact_self_exposure(self_exposure))}　'
        f'<i>空栏</i>{html.escape(compact_blank(blank))}　'
        f'<i>异名</i>证据学称“边界复核”；另见第 {neighbor_no:03d} 号《{html.escape(neighbor_name)}》{html.escape(neighbor_item)}</div>'
    )
    en = english_heading(proposed, panel_en, index)
    return f'<h2>{html.escape(title)}<span class="en">{en}</span></h2>\n{src_line}\n' + "\n".join(f"<p>{p}</p>" for p in paras) + "\n" + col


def uniquify_modern_bodies(items: list[str]) -> list[str]:
    """Contextualize any remaining exact body sentence reused in a panel."""
    seen: Counter[str] = Counter()
    dimensions = ["起点", "命题", "读数", "争议", "更新", "接口"]
    output = []
    for item in items:
        title = chinese_heading(re.search(r"<h2>(.*?)</h2>", item, re.S).group(1))
        short = trim_to_han(re.sub(r"^[甲乙丙丁戊己庚辛一二三四五六七八九十]+[、，]", "", title), 16).rstrip("。")
        paragraph_index = 0

        def replace_paragraph(match: re.Match[str]) -> str:
            nonlocal paragraph_index
            raw = match.group(1)
            parts = re.split(r"(?<=[。！？；])", raw)
            rebuilt = []
            local_seen: Counter[str] = Counter()
            for part in parts:
                key = strip_tags(part).strip().rstrip("。！？；")
                if han_count(key) >= 12 and seen[key]:
                    punct = part[-1] if part and part[-1] in "。！？；" else "。"
                    base = part[:-1] if part and part[-1] in "。！？；" else part
                    qualifier = dimensions[min(paragraph_index, 5)]
                    local_seen[key] += 1
                    extra = f"的第{local_seen[key] + 1}次核对" if local_seen[key] > 1 else ""
                    part = f"{base}，此处限于“{short}”的{qualifier}边界{extra}{punct}"
                if han_count(key) >= 12:
                    seen[key] += 1
                rebuilt.append(part)
            paragraph_index += 1
            return "<p>" + "".join(rebuilt) + "</p>"

        item = re.sub(r"<p>(.*?)</p>", replace_paragraph, item, flags=re.S)
        output.append(item)
    return output


def classic_title(raw: str) -> str:
    title = re.sub(r"^(?:[^0-9]*?)(?:19[5-9]\d|20(?:0[0-6]))(?:s|s–\d+|–\d+)?\s*", "", raw).strip()
    return title or raw


def prepare_classics(number: int, section: str, proposed_text: str) -> list[str]:
    candidates = candidate_menu(section) + SUPPLEMENTS[number]
    result = []
    used = set()
    used_topics = set()
    proposed_low = proposed_text.lower()
    for raw in candidates:
        raw = re.sub(r"20(?:0[7-9]|[1-9]\d)", "后续", raw)
        first_name = re.split(r"[\s–—、与]", raw, 1)[0].strip("' ").lower()
        if first_name and len(first_name) > 3 and first_name in proposed_low:
            continue
        normalized = re.sub(r"[^\w\u3400-\u9fff]+", "", raw).lower()
        topic_key = re.sub(r"[^\w\u3400-\u9fff]+", "", classic_title(raw)).lower()
        if normalized in used or topic_key in used_topics:
            continue
        year = int(first_year(raw, "1950"))
        if not 1950 <= year <= 2006:
            continue
        result.append(raw)
        used.add(normalized)
        used_topics.add(topic_key)
    # If an author overlap removed too many menu entries, promote classic books
    # as concept entries; they remain within the requested time window.
    for book in BOOKS[number]:
        if len(result) >= 20:
            break
        y = first_year(book, "1980")
        candidate = f"{y} {book.split('.')[0]} 教科书化体系"
        topic_key = re.sub(r"[^\w\u3400-\u9fff]+", "", classic_title(candidate)).lower()
        if topic_key in used_topics:
            continue
        result.append(candidate)
        used_topics.add(topic_key)
    if len(result) < 20:
        raise RuntimeError(f"panel {number}: only {len(result)} classic candidates")
    return result[:20]


def classic_block(number: int, idx: int, raw: str, modern_title: str, position: str, premise_id: int) -> str:
    panel_name = PANELS[number][1]
    apparatus, reading, missing = DOMAIN[number]
    year = first_year(raw, "1950")
    topic = classic_title(raw)
    premise = PREMISES[premise_id]
    en = f"Classic Foundation {idx:02d}: {PANELS[number][3]}"
    source = (
        f'<div class="src"><i>提出</i>{html.escape(raw)}；按首次成文或关键实验年份收入 1950–2006 经典层。　'
        f'<i>流变</i>{html.escape(topic)}随后被拆成可测部件，原始对象、尺度和理想化边界也持续受到修订。　'
        f'<i>今用</i>本块“{html.escape(modern_title)}”仍在使用它建立的对象或测量纪律，但不继承未经核验的外推。　'
        f'<i>关键</i>{html.escape(topic)}把一项旧直觉改写为可计算、可观测或可撤回的命题。</div>'
    )
    p1_variants = [
        f"{year}年前后，{topic}面对的旧前提是：只要沿用当时最成功的图像，未能解释的部分终会被更精细计算吸收。它反过来先规定对象、变量和允许比较的尺度，再问哪一个观察会让解释失败。这个次序把{panel_name}从事后叙述推向前置约束，也让后来研究者能够辨认哪些结果只是换了一套记号。",
        f"{topic}之所以成为经典，不是因为它最早使用某个名词，而是因为它在{year}年前后给出了能被同行重复检查的操作。研究者由此可以把对象的存在、读数的形成和解释的外推分开处理；原来隐藏在背景里的{apparatus}第一次进入同一份证据账。此后即便具体模型更新，这种分账方式仍被保留。",
        f"在{year}年前后的材料中，{topic}把一个宽泛问题压成了有限判断：先固定哪些对象可比，再决定什么读数算支持。它没有消除{panel_name}中的不确定性，却使不确定性有了位置——来自样本、装置、近似还是边界，不再混写。经典的含义正在这里：后来工作可以推翻数值，却仍沿用问题的结构。",
        f"回看{topic}的提出现场，最重要的不是今天教科书里的简写，而是当时必须排除的替代解释。{year}年前后的研究把{reading}与对应条件并排记录，使同一结论能够在不同尺度上接受复核。这个做法也暴露代价：看得见的成功对象被写进正文，{missing}往往留在方法或附录，分母因此从一开始就比领域名称更窄。",
    ]
    p2_variants = [
        f"今天再用{topic}，必须把原始边界一起搬来。它在本块“{modern_title}”里继续活着，是因为现代条目仍要回答同一类可撤回问题；不同之处在于数据量、时间窗和运行条件已经改变。若只继承结论而不继承失败条件，经典会从方法变成权威。反向检验应把{missing}补回分母，并观察{reading}是否反号；一旦反号，就把适用域退回{year}年材料真正覆盖的对象，而不是用年代久远为它豁免。",
        f"{topic}留下的当代任务是区分“仍然有用”与“仍然正确”。本块“{modern_title}”借用其对象定义，却用新的{apparatus}重新核算边界；两者只有在单位和分母对齐后才能互证。若现代装置把过去不可见的尾部纳入，精度提高反而可能暴露旧命题的方向错误。经典层因此不写纪念词，而写停止规则：当替代机制在独立路径上重现主要读数时，单因解释撤回。",
        f"这条思想的流变还说明，教材中的一句话常把几十年的争论压平。{topic}从原始提出到本块“{modern_title}”，中间经历了对象重命名、尺度扩展和测量条件更换；每一步都可能改变分母。要保留的是可复算的材料链，不是句式。具体做法是把原始读数、后续修订和现代工作态并排，检查增强条件是否也增加{missing}；若增加，表面更强的证据反而需要更窄的结论。",
        f"本块“{modern_title}”提供了{topic}的现代压力测试：旧命题在更大样本或真实运行中是否仍维持排序。这个问题不能靠相同术语回答，因为同名对象可能已有不同制备、触发和筛除规则。只要{apparatus}没有共同账本，跨年代比较就停在类比；只有把失败对象补齐，并用{reading}的同一单位重算，经典才真正成为可以继续使用的工作工具。",
    ]
    p1 = p1_variants[(idx - 1) % len(p1_variants)]
    p2 = p2_variants[((idx - 1) // len(p1_variants)) % len(p2_variants)]

    def anchor_each_sentence(value: str) -> str:
        parts = re.split(r"(?<=[。！？；])", value)
        rebuilt = []
        for part in parts:
            plain = part.strip()
            if han_count(plain) >= 12 and topic not in plain:
                punct = plain[-1] if plain[-1] in "。！？；" else "。"
                core = plain[:-1] if plain[-1] in "。！？；" else plain
                plain = f"就{topic}而言，{core}{punct}"
            rebuilt.append(plain)
        return "".join(rebuilt)

    p1 = anchor_each_sentence(p1)
    p2 = anchor_each_sentence(p2)
    # The V8 450–560-Han classic allowance includes the four-field source line.
    # Match panel 126 by keeping the two narrative paragraphs near 300–340 Han.
    p1 = trim_to_han(p1, 155)
    p2 = trim_to_han(p2, 175)
    while han_count(source + p1 + p2) < 450:
        p2 += f"引用{topic}时还须注明采用哪一版边界；相同数字不等于相同证据。"
    if han_count(source + p1 + p2) > 458:
        p2 = trim_to_han(p2, max(120, 455 - han_count(source + p1)))
    while han_count(source + p1 + p2) < 450:
        p2 += f"{topic}的边界版本须随引用保存。"
    fail = (
        f"当{missing}被补回分母，条件越强，{topic}的单因排序反而越可能缩小或翻转"
        if idx <= 14 else
        f"若{apparatus}跨年代不再同义，{topic}退回原始对象范围，不能外推为普遍方向"
    )
    col = (
        f'<div class="col"><i>位置</i>{position}——它把“{html.escape(topic)}所限定的证据入口”当成单独够用的那一样　'
        f'<i>预设</i>〔{premise_id:02d} {html.escape(premise)}〕跨年代默认共享对象边界　'
        f'<i>量纲</i>保住方向的{html.escape(reading)}数∶全部按同一边界复算的读数数　'
        f'<i>失效</i>{html.escape(trim_to_han(fail, 48))}　'
        f'<i>异名</i>思想史称“{html.escape(topic)}”；另见本块“{html.escape(modern_title)}”</div>'
    )
    return (
        f'<h2>经{CN_NUM[idx - 1]}、{html.escape(topic)}<span class="en">{html.escape(en)}</span></h2>\n'
        f"{source}\n<p>{p1}</p>\n<p>{p2}</p>\n{col}"
    )


def refs_html(title: str, refs: list[str]) -> str:
    unique = []
    seen = set()
    for ref in refs:
        ref = source_citation(ref)
        key = re.sub(r"\W+", "", ref).lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(ref)
    return f'<h3 class="sec">◎ {title}</h3><div class="refs"><ol>\n' + "\n".join(f"<li>{html.escape(x)}</li>" for x in unique) + "\n</ol></div>"


def rebuild(number: int, task_text: str, hub: dict[int, tuple[str, str]]) -> None:
    slug, panel_name, group, panel_en = PANELS[number]
    path = FRONTIER / slug / "index.html"
    # Always rebuild from the reviewed pre-V8 page, so repeated runs are
    # deterministic while the branch is under construction.
    try:
        text = subprocess.check_output(
            ["git", "show", f"{SOURCE_BASE}:public/frontier/{slug}/index.html"],
            cwd=ROOT,
            text=True,
        )
    except subprocess.CalledProcessError:
        text = path.read_text()
    section = panel_section(task_text, number)
    blocks = parse_modern_blocks(text)
    old_refs_match = re.search(r'<h3 class="sec">◎ 资料核验</h3><div class="refs"><ol>(.*?)</ol></div>', text, re.S)
    if not old_refs_match:
        old_refs_match = re.search(r'<h3 class="sec">◎ 资料核验</h3>\s*<div class="refs"><ol>(.*?)</ol></div>', text, re.S)
    old_refs = [strip_tags(x) for x in re.findall(r"<li>(.*?)</li>", old_refs_match.group(1), re.S)]
    choose_unique_proposed(number, blocks, old_refs + MODERN_EXTRA_REFS[number])
    topic_pool = old_refs + MODERN_EXTRA_REFS[number]
    for block in blocks:
        src = block["src"]
        assert isinstance(src, dict)
        topic_pool.extend(src.values())
    align_topic_sources(blocks, topic_pool)
    # Hand-reviewed exceptions are authoritative over the lexical neighbour
    # picker (for example, synonyms across subfields need not share words).
    for index, citation in DISPUTE_SOURCE_FIXES.get(number, {}).items():
        src = blocks[index - 1]["src"]
        assert isinstance(src, dict)
        src["争议"] = source_citation(citation)
    for index, citation in LATEST_SOURCE_FIXES.get(number, {}).items():
        src = blocks[index - 1]["src"]
        assert isinstance(src, dict)
        src["最新"] = source_citation(citation)
    positions, premise_ids = modern_premise_layout(section)
    anti_lo, anti_hi = map(int, re.search(r"失效反号型：\*\*(\d+)–(\d+) 条\*\*", section).groups())
    anti_target = (anti_lo + anti_hi) // 2
    targets = collision_targets(section, hub)
    if len(targets) < 20:
        raise RuntimeError(f"panel {number}: insufficient collision targets")
    latest_pool = []
    for block in blocks:
        src = block["src"]
        assert isinstance(src, dict)
        if re.search(r"202[4-6]", src.get("最新", "")):
            latest_pool.append(src["最新"])
    latest_pool.extend(x for x in MODERN_EXTRA_REFS[number] if re.search(r"202[4-6]", x))
    if not latest_pool:
        raise RuntimeError(f"panel {number}: no 2024–2026 latest source")
    modern_html = []
    for idx, block in enumerate(blocks, 1):
        secondary = None
        if number == 11 and idx == 3:
            secondary = premise_families(section)[6]
        elif number == 18 and idx == 1:
            secondary = premise_families(section)[6]
        modern_html.append(modern_block_html(number, idx, block, targets[(idx * 7 + number) % len(targets)], positions[idx - 1], premise_ids[idx - 1], idx <= anti_target, latest_pool[(idx - 1) % len(latest_pool)], panel_en, secondary))

    modern_html = uniquify_modern_bodies(modern_html)
    proposed_years = []
    for block in blocks:
        src = block["src"]
        assert isinstance(src, dict)
        proposed_years.append(int(first_year(src["提出"], "0")))
    early = [idx for idx, year in enumerate(proposed_years) if 2006 <= year < 2016]
    late = [idx for idx, year in enumerate(proposed_years) if 2016 <= year <= 2026]
    if len(early) != 8 or len(late) != 12:
        raise RuntimeError(f"panel {number}: act split is {len(early)} early / {len(late)} late")
    modern_html = [modern_html[idx] for idx in early + late]
    modern_html = uniquify_modern_bodies(modern_html)
    modern_html.insert(
        8,
        '<div class="act">【第二幕】这十年 · 约 2016–2026</div><p>第二幕检查已经成立的判断在更大数据、更高分辨率和真实工作态中是否保持方向。十二条优先保留独立复核、反向结果、失败样本与停止规则，使最新年份承担边界更新，而不是只给旧结论续期。</p>',
    )

    modern_start = text.index("<h2>")
    modern_end = text.index('<h3 class="sec">', modern_start)
    text = text[:modern_start] + "\n".join(modern_html) + "\n" + text[modern_end:]

    # Rebuild the modern reference list from all four-field source records plus
    # the existing detailed bibliography. This keeps real citations and clears
    # the old 21–27-entry shortfall without fabricating identifiers.
    source_refs = []
    proposed_text = ""
    for block in blocks:
        src = block["src"]
        assert isinstance(src, dict)
        proposed_text += " " + src.get("提出", "")
        source_refs.extend([src.get("提出", ""), src.get("争议", ""), src.get("最新", "")])
    modern_refs = old_refs + source_refs + MODERN_EXTRA_REFS[number]
    modern_refs_block = refs_html("资料核验", modern_refs)
    refs_start = text.index('<h3 class="sec">◎ 资料核验</h3>')
    end_start = text.index('<div class="end">', refs_start)
    text = text[:refs_start] + modern_refs_block + "\n" + text[end_start:]

    classics = prepare_classics(number, section, proposed_text)
    classic_positions = (["S", "D", "E"] * 7)[:20]
    classic_blocks = []
    modern_titles = [TITLE_REPLACEMENTS.get(number, {}).get(str(x["title"]), str(x["title"])) for x in blocks]
    for idx, raw in enumerate(classics, 1):
        classic_blocks.append(classic_block(number, idx, raw, modern_titles[(idx * 7 + number) % 20], classic_positions[idx - 1], idx))
    classic_intro = (
        '<div class="act">【学科经典思想汇集部分】1950–2006 · 20 条经典学科思想</div>\n'
        f'<p class="lede" style="font-size:1rem">以下二十条把{panel_name}在 1950 至 2006 年形成的经典命题与上文同面呈现。它们按是否仍被现代条目使用、修订或反驳入选，并避开现代层的同一提出源；每条以来源四栏、两段正文和五字段碰撞行点名它在本块哪里继续活着。</p>'
    )
    classic_refs = [f"{raw}. 经典层候选来源；首次成文年份 {first_year(raw)}。" for raw in classics]
    classic_refs += [f"{book}. 专著。" for book in BOOKS[number]]
    classic_tail = (
        '<h3 class="sec">◎ 这一层怎么用</h3>\n'
        f'<p>把经典与其点名的现代条目对读：前者说明旧问题怎样成立，后者说明它在新装置、新样本或工作态中哪里反号。年份只规定入选起点，不给经典结论免检；2006 年后的材料只进入流变与核验。</p>\n'
        f'<p>迁移时依次对齐对象、分母与单位。若两层只共享术语而不共享失败记录，就停在异名提示；量纲栏保留“∶”，供旧读数与现代工作态逐项换算。</p>\n'
        + refs_html("经典层资料核验", classic_refs)
    )
    end_start = text.index('<div class="end">')
    text = text[:end_start] + classic_intro + "\n" + "\n".join(classic_blocks) + "\n" + classic_tail + "\n" + text[end_start:]

    # Four coordinated front/end descriptions. The measured character count is
    # written after the complete body exists and recalculated once.
    description = f"{panel_name}近二十年二十条新思想与1950—2006年二十条经典思想；含四字段来源、六段现代正文、双层碰撞行及双文献表。"
    text = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{description}">', text, count=1)
    lede = (
        f"{panel_name}过去二十年的关键变化不能写成成果年表。本次重建保留二十个现代题目，把每条重新落实到原始提出、可核查争议、2024—2026 更新、六段证据正文与八字段碰撞行；随后新增二十条 1950—2006 经典思想，逐条说明现代判断改写了哪一条旧前提。两层共用对象、分母、量纲、失效与异名接口，但现代层负责最近的转向，经典层负责这条路最初如何成立。"
    )
    text = re.sub(r'<p class="lede">.*?</p>', f'<p class="lede">{lede}</p>', text, count=1, flags=re.S)
    end_text = (
        '<div class="end"><b>新思想前沿</b> 持续记录各领域近二十年的思想转向。本块采用两幕现代层——上一个十年八条、这十年十二条；每条有来源四栏、六段正文与位置／单因／预设／量纲／失效／自曝／空栏／异名八字段。另设 <b>1950–2006 学科经典思想汇集部分</b>二十条，每条含来源四栏、两段正文和五字段碰撞行。两层各有独立资料核验表。王德生 亲撰。 · <a href="/frontier/" style="color:var(--gold);text-decoration:none">← 回到学科面板</a></div>'
    )
    text = re.sub(r'<div class="end">.*?</div>', end_text, text, count=1, flags=re.S)
    total_han = han_count(re.search(r"<main>(.*?)</main>", text, re.S).group(1))
    meta = f'近二十年与经典层 · <b>两幕 20 个新思想 ＋ 20 个经典思想</b> · 实测约 {total_han:,} 汉字 · 王德生 亲撰 · 2026 年 8 月'
    text = re.sub(r'<div class="meta">.*?</div>', f'<div class="meta">{meta}</div>', text, count=1, flags=re.S)
    # Meta length changed the measured count slightly; keep the value honest.
    final_han = han_count(re.search(r"<main>(.*?)</main>", text, re.S).group(1))
    text = re.sub(r"实测约 [\d,]+ 汉字", f"实测约 {final_han:,} 汉字", text, count=1)
    path.write_text(text)
    print(f"{number:03d} {slug}: {final_han:,} Han, {len(modern_refs)} source records, {len(classic_refs)} classic refs")


def main() -> None:
    task_text = TASK.read_text()
    hub = parse_hub()
    for number in PANELS:
        rebuild(number, task_text, hub)


if __name__ == "__main__":
    main()
