#!/usr/bin/env python3
"""Create researched V7 dossiers for Frontier panels 581--592."""
from __future__ import annotations

from pathlib import Path

import make_frontier_563_572_data as base

ROOT = Path(__file__).resolve().parents[1]
base.OUT = ROOT / "tools" / "frontier_581_592_data"
base.PANELS.clear()

# Source roles are selected within each panel's four field-wide references.
# The second index always names a 2024--2026 paper, standard, proceedings set,
# or institutional state report, so the "latest" line is genuinely current.
base.SOURCE_PLAN = {
    581: (0, 1), 582: (0, 1), 583: (0, 1), 584: (0, 1),
    585: (0, 1), 586: (0, 1), 587: (0, 1), 588: (0, 1),
    589: (0, 3), 590: (0, 3), 591: (0, 1), 592: (0, 2),
}

_original_make_item = base.make_item
REVERSE_COUNTS = (11, 14, 17, 9, 20, 12, 15, 18, 10, 19, 13, 16)


def make_item(row, idx, panel):
    """Use the shared renderer, then restore a natural per-panel reversal mix."""
    item = _original_make_item(row, idx, panel)
    key = item["col"]["单因"].removeprefix("只认")
    boundary = row[7].split("，", 1)[0]
    if idx < REVERSE_COUNTS[panel["no"] - 581]:
        item["col"]["失效"] = f"当{boundary}时，{key}越高，系统净效应反而越低"
    else:
        item["col"]["失效"] = f"当{boundary}时，结论只覆盖已观测对象，不能外推到完整分布"
    return item


base.make_item = make_item


def add(no, slug, title, group, description, lede, thesis, outlook, extra_refs, blob):
    base.add(no, slug, title, group, description, lede, thesis, outlook, extra_refs, blob)


add(
    581, "information-coding-theory", "信息论与编码理论", "数理、信息与计算主干 · 信息理论",
    "从压缩感知、Raptor码、有限码长与极化码到DNA存储、私有信息检索、语义通信、量子LDPC和目标导向编码，审计信息的可传、可存与可恢复边界。",
    "信息论的前沿不再只问渐近容量是多少，而是追问有限时延、有限能量、隐私、计算成本和任务语义同时存在时，哪些信息必须保存、哪些冗余可以利用、哪些错误永远无法靠更长码字消除。本面板用二十个转折把‘比特可靠性’推进到‘任务可验证性’。",
    "信息论与编码理论成立的决定性机制，是把可恢复对象、资源预算和失败概率写进同一有限尺度，而不是用无穷码长容量替代现实系统",
    "未来五年要看量子LDPC能否获得可实现译码、语义通信能否给出任务无关基线、DNA存储能否跨越随机访问与写入成本，以及编码学习系统能否报告分布外失败",
    [
        "Polyanskiy & Wu, Information Theory: From Coding to Learning, Cambridge University Press (2024).",
        "IEEE Communications Society, Information Theory and Coding for Future Wireless, ICCC proceedings and tutorial record (2025).",
        "Panteleev & Kalachev, IEEE Transactions on Information Theory 68, 213--229 (2022), doi:10.1109/TIT.2021.3119384.",
        "Jiang et al., IEEE Journal on Selected Areas in Communications 39, 1548--1563 (2021), doi:10.1109/JSAC.2021.3070639.",
    ],
    r"""
Raptor喷泉码|Raptor Codes|Shokrollahi, IEEE Transactions on Information Theory 52, 2551–2567 (2006), doi:10.1109/TIT.2006.874390|近线性译码能否在短块与反馈受限时保持开销|标准化实现继续以有限块长和失包分布校正渐近结论|用预编码加LT码从任意足量符号恢复消息|Raptor码把接收哪一组分组从固定位置改成足量条件，互联网广播和分发因此不必逐包重传|短块、相关丢包与实现图结构会抬高额外符号，任意足量并非零开销
压缩感知|Compressed Sensing|Candès, Romberg & Tao, IEEE Transactions on Information Theory 52, 489–509 (2006), doi:10.1109/TIT.2005.862083|稀疏先验是否真实存在且测量矩阵能否满足恢复条件|结构化测量与模型失配理论持续限定恢复保证|用少于奈奎斯特数量的线性测量恢复稀疏信号|随机测量与凸优化证明稀疏对象可从欠定观测稳定恢复，采样从逐点记录转为结构编码|近似稀疏、相干字典和噪声会破坏保证，测量数少不等于总采集成本低
极化码|Polar Codes|Arıkan, IEEE Transactions on Information Theory 55, 3051–3073 (2009), doi:10.1109/TIT.2009.2021379|渐近容量实现能否在有限长度和低时延译码中兑现|列表译码与5G控制信道实现把有限长度推到工程中心|通过信道极化构造可靠与不可靠比特通道|极化变换首次给出二元离散无记忆信道的显式低复杂度容量达到码，改写了容量证明与构造分离的格局|有限码长下连续消除译码性能弱，冻结位、列表大小和CRC会改变复杂度与误码率
有限码长信息论|Finite-Blocklength Information Theory|Polyanskiy, Poor & Verdú, IEEE Transactions on Information Theory 56, 2307–2359 (2010), doi:10.1109/TIT.2010.2043769|二阶正态近似能否覆盖超短包和非渐近平滑信道|短包通信继续以元 converse 与可达界审计系统时延|把容量改写为码长误差率与速率的三变量边界|研究给出有限码长可达率的非渐近上下界和色散项，使容量不再是现实链路的唯一标尺|极短码、反馈、衰落估计和译码复杂度会让二阶近似失准，码长不能被隐藏
空间耦合LDPC阈值饱和|Spatially Coupled LDPC|Kudekar, Richardson & Urbanke, IEEE Transactions on Information Theory 57, 803–834 (2011), doi:10.1109/TIT.2010.2095072|边界播种带来的阈值提升能否抵消终止损失和译码窗口|窗口译码与标准码设计继续比较延迟和硬件吞吐|用空间耦合让迭代译码阈值逼近MAP阈值|阈值饱和证明局部图耦合可把次优消息传递推到近最优边界，展示结构冗余不是浪费|有限链长度有速率损失，窗口过小或图含短环时性能回落，渐近阈值不能代替芯片测量
DNA数字存储|DNA Data Storage|Goldman et al., Nature 494, 77–80 (2013), doi:10.1038/nature11875|高密度介质能否同时满足写入成本随机访问与长期纠错|自动化合成和喷泉编码继续提高可恢复密度|把数字文件编码为可合成和测序的寡核苷酸|研究以四进制受限编码存储多类文件并完整恢复，使分子序列成为长期冷数据介质|合成错误、PCR偏倚和序列掉落形成非对称信道，密度纪录不等于可用存储系统
编码缓存|Coded Caching|Maddah-Ali & Niesen, IEEE Transactions on Information Theory 60, 2856–2867 (2014), doi:10.1109/TIT.2014.2306938|最坏情形全局增益能否在异质需求与有限子包化下保持|设备到设备与多天线缓存继续处理有限文件和动态用户|在放置阶段制造跨用户可复用的编码多播机会|编码缓存把本地存储与广播负载联动，证明缓存的价值不只在命中率而在创造同时服务|子包化指数增长、需求分布和用户退出会吞掉增益，理论负载不能直接当作时延
局部可修复码|Locally Repairable Codes|Tamo & Barg, IEEE Transactions on Information Theory 60, 4661–4676 (2014), doi:10.1109/TIT.2014.2321280|局部修复是否以全局距离和更新带宽为隐藏代价|分布式存储继续研究可用度和多节点故障|让单个丢失符号只访问少量其他符号即可恢复|最优LRC构造把局部性写进码的代数结构，修复读放大成为与距离并列的设计变量|相关故障、热点和多节点同时失效时局部组会崩溃，最优距离不代表真实恢复时间
DNA喷泉码|DNA Fountain|Erlich & Zielinski, Science 355, 950–954 (2017), doi:10.1126/science.aaj2038|接近容量的密度能否覆盖序列筛选与物理冗余|随机访问、可重写与写入自动化成为DNA存储新瓶颈|用喷泉编码吸收寡核苷酸掉落和无效序列|DNA Fountain把鲁棒索引和喷泉恢复结合，在测序掉落下逼近核苷酸信息密度上限|筛除不适合合成的序列会改变码分布，大规模数据库还需索引和选择性读取
私有信息检索容量|Private Information Retrieval Capacity|Sun & Jafar, IEEE Transactions on Information Theory 63, 4075–4088 (2017), doi:10.1109/TIT.2017.2689028|不泄露查询目标的容量能否在串谋与更新数据中保持|多方计算和编码数据库继续扩展隐私与鲁棒性|以跨副本编码查询隐藏用户索取哪条记录|容量定理把下载代价与副本数数据库数联系起来，使隐私不再只是密码学布尔属性|服务器串谋、异步更新和上传成本会降低容量，复制数据库的存储责任不能外置
5G信道编码分工|5G NR Channel Coding|Richardson & Kudekar, IEEE Communications Magazine 56, 28–34 (2018), doi:10.1109/MCOM.2018.1700665|LDPC与极化码分工是否在短包高可靠场景仍最优|6G研究重新比较短码列表译码和硬件能耗|用LDPC承载数据通道并用极化码承载控制通道|5G标准把两类容量逼近码按业务形态分工，理论码首次在全球蜂窝系统大规模落地|标准码含速率匹配和硬件约束，论文曲线与终端能耗之间仍有距离
编码分布式计算|Coded Distributed Computing|Lee et al., IEEE Transactions on Information Theory 64, 1514–1529 (2018), doi:10.1109/TIT.2017.2736066|冗余任务能否稳定抵消拖尾节点而不增加通信和能耗|梯度编码与多项式码继续处理异质节点和隐私|用编码冗余把最慢工作节点从完成条件中移除|编码计算把纠错思想从通信搬到矩阵运算与机器学习，使作业完成由足量结果而非全部节点决定|拖尾分布随负载变化，冗余会增加总计算和网络拥塞，墙钟时间下降不等于资源下降
深度联合信源信道编码|Deep Joint Source-Channel Coding|Bourtsoulatze, Kurka & Gündüz, IEEE Transactions on Cognitive Communications and Networking 5, 567–579 (2019), doi:10.1109/TCCN.2019.2919300|端到端失真优势能否跨信噪比模型和新图像分布保持|生成式与语义失真继续改变视觉传输评价|用神经编码器直接把图像映射到信道符号|深度JSCC显示在衰落和带宽受限下可以平滑退化，避免传统压缩加信道码的悬崖效应|训练信道失配和感知指标会生成看似合理却错误的细节，像素质量不能替代事实保真
PAC码|Polarization-Adjusted Convolutional Codes|Arıkan, IEEE Communications Letters 23, 2699–2702 (2019), doi:10.1109/LCOMM.2019.2941059|卷积预编码能否在短码下稳定超过极化与LDPC实现|列表和序贯译码继续审计复杂度尾部|在极化变换前加入卷积预编码改善距离谱|PAC码在短块仿真中接近有限码长界，重新打开序贯译码与极化结构结合|译码节点数具有长尾且构造依赖信道，平均复杂度会遮蔽最坏时延
语义通信|Semantic Communication|Jiang et al., IEEE Journal on Selected Areas in Communications 39, 1548–1563 (2021), doi:10.1109/JSAC.2021.3070639|任务语义指标能否避免把模型偏好冒充信息保真|目标导向通信开始要求任务无关基线和失真边界|只传对下游任务有决定作用的表征|深度语义通信把传输目标从逐比特一致改成句义或任务正确率，在受限信道上获得更小负载|语义由训练模型定义且会随任务漂移，接收器高分不代表原始事实被保存
量子LDPC线性距离突破|Quantum LDPC Codes|Panteleev & Kalachev, IEEE Transactions on Information Theory 68, 213–229 (2022), doi:10.1109/TIT.2021.3119384|渐近好码能否获得局域可实现校验和高效译码|量子LDPC研究转向译码阈值、逻辑门和硬件几何|构造常码率且距离近线性增长的量子LDPC码|纤维积构造打破长期障碍，证明稀疏量子校验可以同时保持非零码率与大距离|渐近参数不等于容错计算开销，校验非局域、译码失败与逻辑门实现仍是工程瓶颈
年龄信息|Age of Information|Yates et al., IEEE Journal on Selected Areas in Communications 39, 1183–1210 (2021), doi:10.1109/JSAC.2021.3065072|更新频率能否替代到达信息的新鲜度与价值|状态感知调度继续加入语义价值和能量约束|用接收端最新生成时间而非吞吐量度量状态更新|AoI把队列优化从多传数据改成保持信息新鲜，揭示过高发送率也会因排队让状态变旧|时间戳新不代表内容有用，采样误差和任务价值未进入单一年龄指标
无损压缩机器学习边界|Learned Lossless Compression|Townsend, Bird & Barber, International Conference on Learning Representations (2019)|学习分布能否在分布外数据上保持无损与码长优势|概率模型压缩继续报告校准和解码速度|用可逆熵编码把神经概率预测变成真实比特流|bits-back与神经熵模型让生成模型的似然优势落到实际码长，连接统计学习与编码|模型错误会立即增加码长且解码依赖同版本参数，基准压缩率不含模型传输成本
目标导向编码|Goal-Oriented Coding|Polyanskiy & Wu, Information Theory: From Coding to Learning (2024)|为任务保留的最少信息能否跨任务与决策损失复用|未来无线研究把感知计算和通信放进同一资源预算|以决策风险而非比特误差裁决编码是否成功|目标导向框架要求先写明任务损失和允许风险，再决定哪些观测必须传输，避免默认完整重构|任务变化会使原先丢弃的信息重新关键，模型升级后的不可逆损失必须单独记账
编码系统闭环验收|Coding-System Closed-Loop Acceptance|IEEE Communications Society, Information Theory and Coding for Future Wireless (2025)|理论容量是否能被有限码长能耗时延与失败尾部共同验收|2025未来无线编码讨论把语义量子和短包放进统一工程语境|以端到端可恢复任务和全资源预算验收编码|闭环验收要求公开码长、误差率、译码能耗、最坏时延和分布外任务损失，容量只保留为上界|不同业务的任务损失不可强行合并，统一总分会再次遮蔽关键失败
""",
)


add(
    582, "signal-processing", "信号处理", "数理、信息与计算主干 · 信号处理",
    "从稀疏表示、矩阵补全、稳健主成分、同步挤压与图信号处理到深度展开、可微DSP、自监督声学、事件相机和生成式先验，审计信号表征如何改变。",
    "信号处理已从‘先规定变换再估计参数’转向‘让结构、物理模型和数据共同决定表示’，但学习化并没有取消采样、稳定性与可解释误差。每一个更锐利的恢复结果都必须回答：传感器漏掉了什么，训练分布教会了什么，重建又凭空补了什么。",
    "信号处理成立的决定性机制，是让表示、采样算子和误差边界共同接受可复算检验，而不是让下游模型用漂亮输出替原始信号作证",
    "未来五年要看生成式先验能否给出幻觉上界，图和多模态信号能否跨设备迁移，事件流能否与帧式基准公平比较，以及学习滤波器能否报告最坏稳定性",
    [
        "Monga, Li & Eldar, IEEE Signal Processing Magazine 38, 18--44 (2021), doi:10.1109/MSP.2020.3016905.",
        "IEEE Signal Processing Society, ICASSP 2025 Proceedings (2025).",
        "Shuman et al., IEEE Signal Processing Magazine 30, 83--98 (2013), doi:10.1109/MSP.2012.2235192.",
        "Song et al., International Conference on Learning Representations, Score-Based Generative Modeling (2021).",
    ],
    r"""
稀疏表示与压缩感知|Sparse Representation|Donoho, IEEE Transactions on Information Theory 52, 1289–1306 (2006), doi:10.1109/TIT.2006.871582|稀疏是否属于对象而非选定字典|结构化感知继续用模型失配与相干性限制恢复|以少量线性观测恢复可压缩信号|压缩感知把采样率与稀疏度而非最高频率联系起来，重写传感器设计与重建关系|字典选择、近似稀疏和噪声相关会使理论界变松，少测量不等于少校准
稀疏贝叶斯学习|Sparse Bayesian Learning|Wipf & Rao, IEEE Transactions on Signal Processing 55, 3704–3716 (2007), doi:10.1109/TSP.2007.901154|层级先验给出的稀疏是否依赖超参数与局部极值|自动相关性判定继续与变分推断和阵列处理结合|用证据最大化自动关闭不必要系数|稀疏贝叶斯学习把稀疏度选择写入概率模型，在相关字典下常优于固定凸惩罚|后验近似与初始化会制造不同支持集，概率输出若未校准不能当作置信度
矩阵补全|Matrix Completion|Candès & Recht, Foundations of Computational Mathematics 9, 717–772 (2009), doi:10.1007/s10208-009-9045-5|低秩与随机缺失能否代表真实选择性缺失|非均匀采样和鲁棒补全持续修正可恢复条件|从少量条目恢复低秩矩阵|核范数理论证明满足不相干条件的低秩矩阵可由少量随机观测恢复，推荐与成像共享同一结构|高影响条目往往并非随机缺失，秩估计和冷启动会让漂亮误差只覆盖易观测区域
稳健主成分分析|Robust PCA|Candès et al., Journal of the ACM 58, Article 11 (2011), doi:10.1145/1970392.1970395|低秩背景与稀疏异常能否在结构化运动中唯一分离|在线RPCA继续处理动态背景和缓慢子空间漂移|把矩阵精确拆成低秩与稀疏两部分|主成分追踪把异常从高斯小噪声改成可任意大的稀疏破坏，用于视频背景和故障检测|异常成片或前景长期静止时会进入低秩项，分解名称不保证物理身份正确
同步挤压变换|Synchrosqueezing Transform|Daubechies, Lu & Wu, Applied and Computational Harmonic Analysis 30, 243–261 (2011), doi:10.1016/j.acha.2010.08.002|瞬时频率重排能否在交叉分量与低信噪比下稳定|多变量和二阶同步挤压继续提高调频分辨率|把小波系数沿估计瞬时频率重新集中|同步挤压在保持可逆的同时锐化时频脊线，使非平稳生理和机械信号获得可解释分量|分量靠得过近、幅值过零或频率变化过快时脊线会交换，视觉清晰不等于分解唯一
相位提升|PhaseLift|Candès, Strohmer & Voroninski, Communications on Pure and Applied Mathematics 66, 1241–1274 (2013), doi:10.1002/cpa.21432|升维凸化的可恢复性能否承受真实衍射噪声与计算规模|非凸相位恢复与编码衍射继续降低内存成本|把二次幅值观测提升为秩一矩阵恢复|PhaseLift给出随机测量下相位恢复的凸保证，使缺失相位从启发式迭代进入可证明框架|升维矩阵过大且真实光学测量非独立高斯，理论样本数不能直接换成曝光数
图信号处理|Graph Signal Processing|Shuman et al., IEEE Signal Processing Magazine 30, 83–98 (2013), doi:10.1109/MSP.2012.2235192|图拉普拉斯是否由数据真实机制决定|图学习与几何深度学习继续把图结构本身纳入估计|把傅里叶频率推广到图拉普拉斯谱|图信号处理让传感网络、交通和脑连接上的平滑滤波具有统一谱语言|换一张图就会改变频率和滤波结果，图估计误差常被输出平滑掩盖
变分模态分解|Variational Mode Decomposition|Dragomiretskiy & Zosso, IEEE Transactions on Signal Processing 62, 531–544 (2014), doi:10.1109/TSP.2013.2288675|预设模态数和带宽惩罚是否制造所见分量|自动选模与多变量VMD继续处理参数敏感性|同时估计若干窄带模态及中心频率|VMD把经验模态分解改写为受约束变分优化，减少端点效应和模态混叠|模态数与惩罚参数缺少统一选择，稳定分量可能只是优化偏好
深度展开|Deep Unfolding|Hershey, Le Roux & Weninger, IEEE ICASSP, 1171–1175 (2014), doi:10.1109/ICASSP.2014.6853874|把迭代器层化后是否仍保留算法稳定性|模型驱动深度学习继续加入可解释约束与收敛分析|把每次迭代映射成可训练网络层|深度展开让稀疏推断和源分离用有限层学习步长与阈值，兼顾结构先验和数据适配|训练层数固定且分布外迭代无保证，网络看似像算法不等于具有收敛证书
学习式图像压缩|Learned Image Compression|Ballé, Laparra & Simoncelli, International Conference on Learning Representations (2017)|感知失真与码率优化是否保留事实细节|超先验和生成式压缩继续报告率失真感知三方权衡|共同学习非线性变换和熵模型|学习压缩把变换、量化与概率模型端到端优化，在自然图像基准上超过手工编解码器|训练集和感知损失会偏好常见纹理，重建细节可能不是传感器记录
正则化去噪RED|Regularization by Denoising|Romano, Elad & Milanfar, SIAM Journal on Imaging Sciences 10, 1804–1844 (2017), doi:10.1137/16M1102884|任意去噪器是否对应可解释正则项|即插即用和扩散先验继续研究固定点与收敛条件|用成熟去噪器的残差定义图像先验|RED把强去噪器嵌入反问题而不显式写概率分布，连接工程滤波与优化|去噪器不满足局部齐次或雅可比对称时原正则解释失效，收敛点未必是后验最优
事件相机信号|Event-Based Vision|Gallego et al., IEEE Transactions on Pattern Analysis and Machine Intelligence 44, 154–180 (2022), doi:10.1109/TPAMI.2020.3008413|异步亮度变化能否替代绝对强度和静态纹理|神经形态相机继续扩展高速机器人和HDR任务|只在像素对数亮度越阈值时发送事件|事件相机把固定帧率改成微秒级稀疏变化流，显著提高动态范围并降低运动模糊|静止场景无事件且阈值逐像素漂移，事件多不等于信息多
可微数字信号处理|Differentiable DSP|Engel et al., International Conference on Learning Representations (2020)|可解释振荡器滤波器能否限制神经模型幻觉|可微声学模块继续进入语音音乐与控制|把合成器和滤波器写成可反向传播模块|DDSP让网络预测音高包络和噪声参数，再由已知信号算子生成音频，结构化了端到端学习|参数可解释不保证感知因果，训练音色之外的激励和非线性会导致失真
自监督语音表征|Self-Supervised Speech Representation|Baevski et al., Advances in Neural Information Processing Systems 33, 12449–12460 (2020)|无标签预训练是否跨语言口音和噪声设备保持|多语种语音基础模型继续扩大覆盖并暴露代表性差异|用掩码对比任务学习波形离散表征|wav2vec 2.0显示少量标注配合大规模无标签音频可显著降低语音识别错误|网页和广播语料不代表低资源口音，词错率下降会遮蔽群体差异
分数模型后验采样|Score-Based Inverse Processing|Song et al., International Conference on Learning Representations (2021)|生成先验补全能否区分后验不确定性与幻觉|扩散逆问题研究开始报告覆盖率和多样本稳定性|用噪声尺度上的分数场生成满足观测的候选|分数模型提供从噪声逐步还原信号的生成机制，可与测量一致性结合处理多种退化|先验会拉向训练集常见形状，单个漂亮样本不能证明观测支持
神经音频编解码|Neural Audio Codec|Défossez et al., Transactions on Machine Learning Research (2023)|低码率感知质量能否保留说话人证据和微弱事件|生成式音频令牌继续服务语音模型和实时通信|用残差向量量化压缩宽带波形|神经音频编码在低比特率下保持高主观质量，并把波形转换成可供生成模型处理的离散令牌|感知模型会抹去罕见声学细节，重合成音频不能替代取证原件
图结构联合学习|Joint Graph and Signal Learning|Dong et al., IEEE Transactions on Signal Processing 67, 2148–2160 (2019), doi:10.1109/TSP.2019.2904920|从信号反推的图是否把相关性误写成连接|动态图和因果图学习继续区分结构漂移|同时估计图拉普拉斯与图上平滑信号|联合学习不再把图当作外部真值，而以平滑和稀疏约束从观测恢复网络结构|多个图可解释同一协方差，正则项会选择方便而非真实的边
模型驱动深度学习|Model-Based Deep Learning|Shlezinger et al., Proceedings of the IEEE 111, 465–499 (2023), doi:10.1109/JPROC.2023.3247480|模块化先验能否给出比黑箱更好的分布外保证|通信雷达成像继续以任务模块组合学习|在已知信号模型中只学习不确定组件|模型驱动学习把可知的传播和算子保留，把难建模部分交给网络，降低数据需求|错误物理模块会把偏差固化，少参数不自动等于更可靠
多模态传感对齐|Multimodal Signal Alignment|IEEE Signal Processing Society, ICASSP 2025 Proceedings (2025)|时间空间不同步的模态能否在共享嵌入中保持各自证据|2025信号处理研究集中审计音视雷达和生理模态对齐|以可学习时延和置信权重融合异构传感|多模态处理从简单拼接转向对齐、缺失模态训练和不确定权重，使传感器故障可以被显式处理|共同嵌入会压平模态冲突，缺失数据若只在训练中模拟会低估现场失效
信号恢复闭环验收|Signal-Recovery Closed-Loop Acceptance|Monga, Li & Eldar, IEEE Signal Processing Magazine 38, 18–44 (2021)|重建指标是否能证明输出忠于原始测量而非训练先验|2025基准开始并列任务误差测量一致性与分布外稳定|以观测一致、误差边界和下游证据共同验收恢复|闭环验收要求保存原始测量、算子版本、残差和多候选不确定性，PSNR或主观分数不能独立过关|不可逆预处理和未保存原始流会使后验复核失去对象，任何算法分数都无法补救
""",
)


add(
    583, "computational-science-engineering", "计算科学与工程", "数理、信息与计算主干 · 计算科学",
    "从GPU通用计算、混合精度、任务运行时、随机线性代数与多层蒙特卡洛到百亿亿次计算、原位分析、可复现工作流、性能可移植和可微仿真，审计数值计算的系统转向。",
    "计算科学与工程已经从‘把同一算法跑得更快’转向‘在异构硬件、误差预算、数据移动和可复现责任之间重新设计算法’。浮点运算峰值只是入口，真正的科学产出取决于离散误差、求解器误差、软硬件版本和工作流证据能否沿整条链复算。",
    "计算科学与工程成立的决定性机制，是让算法、精度、硬件和证据链共同服从一个误差与资源预算，而不是把峰值算力或单次加速比当作科学正确性",
    "未来五年要看百亿亿次应用能否稳定复现，混合精度能否给出自适应误差证书，原位压缩能否保留后续新问题所需信息，以及可微仿真能否穿透离散器偏差",
    [
        "National Academies, Reproducibility and Replicability in Science (2019).",
        "Kashi et al., Mixed-Precision Numerics in Scientific Applications: Survey and Perspectives, Journal of Supercomputing (2026), doi:10.1007/s11227-026-08264-4.",
        "US Department of Energy, Exascale Computing Project Final Report (2024).",
        "Halko, Martinsson & Tropp, SIAM Review 53, 217--288 (2011), doi:10.1137/090771806.",
    ],
    r"""
GPU通用科学计算|General-Purpose GPU Computing|Owens et al., Computer Graphics Forum 26, 80–113 (2007), doi:10.1111/j.1467-8659.2007.01012.x|吞吐加速能否覆盖数据搬移和数值差异|性能可移植框架继续比较GPU与多架构执行|把大量规则并行数值核映射到图形处理器|CUDA时代的综述展示GPU可将线性代数、粒子和网格计算推进到高吞吐，异构加速成为科学软件主线|主机设备传输、分支发散和低精度运算会吞掉加速，单核基线选择也会夸大倍数
混合精度迭代改进|Mixed-Precision Iterative Refinement|Buttari et al., International Journal of High Performance Computing Applications 21, 457–466 (2007), doi:10.1177/1094342007084026|低精度求解能否在病态矩阵下恢复高精度答案|自适应精度与张量核心继续扩展到稀疏和非线性问题|用低精度分解配合高精度残差修正|混合精度迭代改进证明大部分计算可在较低精度完成，再以高精度残差恢复准确解，能耗成为数值设计变量|条件数过大或残差停滞时修正失败，速度收益不能替后向误差作证
多层蒙特卡洛|Multilevel Monte Carlo|Giles, Operations Research 56, 607–617 (2008), doi:10.1287/opre.1070.0496|层间耦合的方差衰减能否在复杂离散和不连续收益中保持|自适应与多指标MLMC继续处理概率和密度|用大量粗样本和少量细样本估计期望|MLMC把离散层级差当控制变量，在给定均方误差下显著降低随机仿真成本|层间样本若未强耦合或事件指标不连续，方差不衰减，理论复杂度会失效
MOOSE多物理框架|MOOSE|Gaston et al., Nuclear Engineering and Design 239, 1768–1778 (2009), doi:10.1016/j.nucengdes.2009.05.021|共享非线性求解底座能否避免物理模块耦合误差|模块化多物理继续进入反应堆材料和地学|以雅可比自由牛顿Krylov统一耦合场求解|MOOSE把网格、时间步、非线性求解和并行基础设施集中，让应用专注物理残差与材料模型|模块可编译不等于耦合正确，界面守恒、时间尺度和验证责任仍需逐应用证明
任务图运行时StarPU|Task-Based Runtime|Augonnet et al., Concurrency and Computation: Practice and Experience 23, 187–198 (2011), doi:10.1002/cpe.1631|动态调度能否稳定胜过手工映射且保持结果可重复|PaRSEC、Legion和Kokkos任务模型继续扩展异构机器|把计算和数据依赖写成任务图交给运行时调度|StarPU让CPU与GPU按性能模型动态分派任务，算法从固定设备顺序转向依赖驱动执行|调度开销、性能模型冷启动和非确定执行会改变墙钟与浮点求和顺序
随机数值线性代数|Randomized Numerical Linear Algebra|Halko, Martinsson & Tropp, SIAM Review 53, 217–288 (2011), doi:10.1137/090771806|随机投影误差能否在谱衰减弱和多遍代价高时受控|单遍和通信避免算法继续服务超大矩阵|用随机采样发现低维子空间|随机SVD以少量矩阵乘法逼近主子空间，数据访问次数而非算术次数成为设计中心|谱间隙小或尾部能量大时秩需求上升，概率保证也需报告失败参数
原位可视化|In-Situ Visualization|Childs et al., Computer Graphics and Applications 32, 18–26 (2012), doi:10.1109/MCG.2012.46|仿真期间丢弃原始场是否阻断事后新问题|原位特征检测和可逆压缩继续降低I/O压力|在数据仍驻留内存时完成分析与可视化|原位分析应对超级计算中输出速度落后于模拟速度，把数据选择前移到运行过程|当时没想到的特征若被删掉便无法追回，存储节省会变成认识论锁定
容错算法与检查点|Algorithm-Based Fault Tolerance|Bosilca et al., Journal of Parallel and Distributed Computing 73, 254–273 (2013), doi:10.1016/j.jpdc.2012.09.001|错误检测能否比全局检查点更低成本且覆盖静默错误|弹性运行时继续面向大规模节点故障|利用算法冗余检测并恢复部分计算状态|算法级容错让矩阵运算和迭代器从应用结构恢复故障，而非每次回滚全部状态|冗余只覆盖模型化故障，静默数据破坏和相关节点失效仍可能穿过校验
FAIR科学数据原则|FAIR Principles|Wilkinson et al., Scientific Data 3, 160018 (2016), doi:10.1038/sdata.2016.18|可发现可访问是否等于仿真可复算|工作流封装和可执行论文继续补足环境依赖|让数据与元数据可发现可访问可互操作可复用|FAIR把科学计算输出从文件交付改成带标识语义许可和来源的长期对象|数据FAIR而代码、参数和容器缺失时仍不能重跑，开放元数据不等于开放计算
性能可移植Kokkos|Performance Portability|Edwards, Trott & Sunderland, Journal of Parallel and Distributed Computing 74, 3202–3216 (2014), doi:10.1016/j.jpdc.2014.07.003|单一抽象能否跨架构保持接近最佳性能|Kokkos、RAJA和SYCL继续面向CPU GPU与加速器|把并行模式和数据布局从设备语法分离|Kokkos让同一C++源通过执行与内存空间适配多架构，降低科学软件重写成本|抽象层仍需逐内核调优，能编译不等于性能可移植，后端差异也会改变数值顺序
可复现计算环境|Containerized Scientific Workflows|Boettiger, ACM SIGOPS Operating Systems Review 49, 71–79 (2015), doi:10.1145/2723872.2723882|容器镜像能否保存硬件驱动外部服务和长期安全|Apptainer与工作流语言继续记录环境和来源|以版本化容器封装计算依赖|容器把库、解释器和系统工具固定为可分发环境，缓解论文代码在新机器无法运行|镜像依赖外部数据、CPU指令和GPU驱动，十年后可启动不保证可复算
ECP百亿亿次协同设计|Exascale Computing Project|US Department of Energy, Exascale Computing Project launched 2016|应用软件硬件协同能否避免峰值机器无可用科学程序|ECP于2024总结应用软件栈与共同技术成果|以应用牵引硬件软件数学库共同准备|ECP把科学应用、软件技术和硬件集成并行推进，百亿亿次不再被视为单一机器采购|项目里程碑完成不能代表全部应用稳态生产，迁移与长期维护成本仍在机构账外
SZ有损科学压缩|Error-Bounded Scientific Compression|Tao et al., IEEE Transactions on Parallel and Distributed Systems 30, 1853–1869 (2019), doi:10.1109/TPDS.2018.2886011|逐点误差界能否保留拓扑特征与下游统计|自适应压缩开始用任务误差而非单一绝对误差|以用户给定误差界压缩浮点场|SZ把科学数据压缩从视觉无损改成数值误差有界，显著降低超算I/O与存储|逐点界不保证涡核、临界点或尾概率保持，下游任务必须单独验收
JAX可组合自动微分|JAX|Bradbury et al., JAX: Composable Transformations of Python+NumPy Programs (2018)|自动微分和即时编译能否覆盖不纯函数与数值控制流|可微编程继续进入模拟优化和统计推断|用函数变换统一求导向量化并行和编译|JAX把NumPy风格程序转换为可求导、可批处理和加速器编译函数，模糊数值代码与机器学习边界|随机状态、动态形状和自定义算子需显式处理，梯度存在不代表离散模型可微得正确
AMReX块结构自适应网格|AMReX|Zhang et al., Journal of Open Source Software 4, 1370 (2019), doi:10.21105/joss.01370|局部加密能否在负载平衡通信和守恒间同时成立|AMReX继续支撑百亿亿次多物理应用|以块结构AMR只在需要处提高分辨率|AMReX统一网格层级、并行通信和粒子容器，让爆炸、燃烧和宇宙学在异构机器自适应计算|细网格界面和重网格会引入守恒与负载波动，单元数减少不保证总时间减少
Frontier百亿亿次应用|Frontier Exascale Computing|TOP500 and Oak Ridge Leadership Computing Facility, Frontier sustained exascale in 2022|HPL纪录能否代表真实多物理应用的时间到解|2024 ECP报告以应用成果和软件栈复核百亿亿次兑现|让双精度每秒百亿亿次进入开放科学机器|Frontier首次在HPL持续超过一百亿亿次浮点运算，标志异构GPU超级计算进入新尺度|HPL规则矩阵与稀疏通信应用差别巨大，峰值和功耗不能独立裁决科学产出
工作流来源追踪|Workflow Provenance|Khan et al., Patterns 2, 100290 (2021), doi:10.1016/j.patter.2021.100290|自动工作流是否完整记录人工选择与外部服务|RO-Crate与CWL继续连接数据代码参数和执行|把每一步输入输出软件版本写成机器可读来源|来源追踪使大型计算链的结果能回到原始数据与参数版本，支持增量重跑和责任定位|交互式调参、手工删样本和云服务版本常不进日志，自动记录仍可能留下决定性空白
可微仿真|Differentiable Simulation|Innes et al., arXiv:1907.07587 and Scientific Machine Learning software ecosystem (2019–2024)|离散程序梯度能否代表连续物理灵敏度|伴随与自动微分框架继续进入控制材料和反演|让仿真器输出对参数和设计变量直接求导|可微仿真把PDE求解、优化与学习接成一个梯度链，降低逆设计中有限差分成本|接触、激波和自适应网格会造成不光滑，代码梯度正确不等于连续模型梯度正确
混合精度科学应用总审计|Mixed-Precision Scientific Computing|Kashi et al., Journal of Supercomputing (2026), doi:10.1007/s11227-026-08264-4|精度降低的能耗收益能否以结果误差和失败率共同验收|2026综述并列气候流体深度学习与科学基础设施|按敏感阶段分配不同数值精度|最新综述把迭代改进、自适应精度和软件生态放到同一地图，显示精度本身是一种可调资源|应用跨阶段误差会非线性放大，平均加速比会遮蔽少数灾难性失败
计算科学闭环验收|Computational Science Closed-Loop Acceptance|US Department of Energy, Exascale Computing Project Final Report (2024)|运行成功是否足以证明科学结论可复算|ECP总结强调应用结果软件版本性能与验证共同交付|以误差预算资源预算和来源证据共同验收计算|闭环验收要求保存网格、求解器容差、随机种子、编译环境、硬件和后处理版本，并让另组复算关键读数|专有硬件和退役软件会使完整镜像仍无法重跑，长期保存策略必须进入项目设计
""",
)


add(
    584, "fluid-mechanics", "流体力学", "数理、信息与计算主干 · 流体力学",
    "从惯性微流控、动态模态分解、分辨率分析、主动流体与超疏水减阻到深度强化控制、呼吸气溶胶、高阶激波捕捉和数据驱动湍流，审计流动尺度与证据。",
    "流体力学的二十年不是Navier–Stokes方程被替换，而是可观测尺度、边界条件和控制手段被重新组织。越来越多的流动可被高速成像、直接数值模拟和学习器捕捉，但高分辨率仍不能自动带来跨雷诺数、跨几何和跨实验装置的规律。",
    "流体力学成立的决定性机制，是让尺度、边界条件与守恒误差在同一无量纲体系中闭合，而不是让一幅锐利流场或一个低阻力纪录替代可迁移机制",
    "未来五年要看学习控制能否从二维仿真走进高雷诺实验，粗糙多相和激波湍流能否获得跨装置基准，呼吸气溶胶能否与真实通风干预闭环，以及数据驱动闭合能否守恒",
    [
        "Brunton, Noack & Koumoutsakos, Annual Review of Fluid Mechanics 52, 477--508 (2020), doi:10.1146/annurev-fluid-010719-060214.",
        "De Stefano & Rees, Fluids 10, 137 (2025), doi:10.3390/fluids10050137.",
        "Kim et al., Fluids 9, 216 (2024), doi:10.3390/fluids9090216.",
        "Bourouiba, Annual Review of Fluid Mechanics 53, 473--508 (2021), doi:10.1146/annurev-fluid-060220-113712.",
    ],
    r"""
惯性微流控聚焦|Inertial Microfluidics|Di Carlo, Lab on a Chip 9, 3038–3046 (2009), doi:10.1039/B912547G|微尺度惯性是否在复杂细胞和非牛顿样本中可控|螺旋通道与高通量细胞分选继续校准升力和阻力|利用有限雷诺数升力让颗粒迁移到稳定位置|惯性微流控突破低雷诺数等于无惯性的直觉，在无外场下连续聚焦和分选细胞|粒径形变与浓度改变平衡位置，缓冲液纪录不能直接外推到血液
滴液微流控|Droplet Microfluidics|Teh et al., Lab on a Chip 8, 198–220 (2008), doi:10.1039/B715524G|单分散液滴是否保持化学身份且不受表面活性剂交换|高通量单细胞和数字PCR继续处理串扰与掉滴|用界面张力把反应分隔成可计数微滴|滴液平台让百万级微反应并行运行，每滴成为受控体积和样本单位|分子会跨油相交换，润湿与并滴使名义液滴数大于有效独立反应数
动态模态分解|Dynamic Mode Decomposition|Schmid, Journal of Fluid Mechanics 656, 5–28 (2010), doi:10.1017/S0022112010001217|线性模态能否代表非线性瞬态和采样窗口之外动力学|多分辨率和控制DMD继续处理非平稳流|从时序快照提取最能解释演化的线性模态|DMD把实验与仿真流场分解为带频率和增长率的时空结构，连接数据与动力系统|采样间隔、噪声和窗口选择会改变谱，清晰模态不等于物理本征模态
分辨率分析|Resolvent Analysis|McKeon & Sharma, Journal of Fluid Mechanics 658, 336–382 (2010), doi:10.1017/S002211201000176X|线性放大机制能否在强非线性交互下主导湍流结构|数据辅助分辨率模型继续估计非线性强迫|把平均流周围的线性算子视为输入输出放大器|分辨率分析从Navier–Stokes线性部分预测高增益结构，为壁湍流相干运动提供可计算骨架|平均流误差和未知非线性强迫会改变模式幅值，只见高增益不能证明实际被激发
超疏水表面减阻|Superhydrophobic Drag Reduction|Rothstein, Annual Review of Fluid Mechanics 42, 89–109 (2010), doi:10.1146/annurev-fluid-121108-145558|实验室滑移能否在压力污染和气层耗尽下长期保持|真实粗糙与湍流壁函数继续审计失效|以困气微结构制造有效滑移边界|超疏水纹理显示边界条件本身可设计，微通道压降和船体减阻获得新路径|润湿转变和表面污染会让滑移反号为额外粗糙阻力，短时水槽不等于服役寿命
主动流体湍动|Active Turbulence|Wensink et al., Proceedings of the National Academy of Sciences 109, 14308–14313 (2012), doi:10.1073/pnas.1202032109|自驱颗粒的涡旋能否沿用惯性湍流级联语言|活性向列和细菌流继续区分能量注入尺度|由个体自驱动在低雷诺数产生多尺度涡流|高密度细菌悬浮液出现速度统计和涡旋图样，证明无惯性环境也可形成湍动样集体流|能量由每个个体局部注入，经典Kolmogorov级联和黏性尺度不能直接照搬
超高雷诺数管流|High-Reynolds-Number Pipe Flow|Hultmark et al., Physical Review Letters 108, 094501 (2012), doi:10.1103/PhysRevLett.108.094501|近壁尺度律能否跨超高雷诺数和探针尺寸保持|Superpipe与大气边界层继续比较对数律参数|用纳米尺度热丝测量高雷诺数近壁湍流|新探针降低空间滤波，在普林斯顿Superpipe检验速度方差和尺度律|探针频响和壁面位置误差在高雷诺数被放大，不同设施的压力梯度也会改变常数
柔性推进最优刚度|Flexible Propulsion|Alben, Witt, Baker, Anderson & Lauder, Journal of Fluid Mechanics 614, 355–380 (2008), doi:10.1017/S0022112008004064|最优柔性是否跨振幅速度和三维尾鳍成立|流固耦合实验继续从效率转向机动与鲁棒|用弹性变形协调推力与尾迹|柔性翼实验显示中等刚度可提高推进效率，结构变形成为流动控制的一部分|二维板和稳态游动不能覆盖三维涡脱落与肌肉控制，最优刚度随工况漂移
稀疏动力学辨识|SINDy for Fluid Flows|Brunton, Proctor & Kutz, Proceedings of the National Academy of Sciences 113, 3932–3937 (2016), doi:10.1073/pnas.1517384113|稀疏方程是否由候选函数库预先决定|弱形式和控制SINDy继续处理噪声和偏微分方程|从数据中选择少量支配动力学项|SINDy用稀疏回归从时序数据恢复可解释方程，在尾迹等系统重建低维动力学|函数库缺项时会稳定选出错误方程，测量噪声和求导会制造伪项
极端事件的有限时间结构|Fluid Extreme Events|Farazmand & Sapsis, Science Advances 3, e1701533 (2017), doi:10.1126/sciadv.1701533|短时前兆能否跨流态预测稀有爆发|有限时间相干结构继续用于海浪和湍流预警|用变分指标寻找最易触发能量爆发的状态|研究在湍流模型中识别先于极端耗散出现的局部结构，使稀有事件预测从尾部分布走向动力前兆|极端样本太少且模型低维，前兆命中率在真实流场可能被虚警吞没
深度强化主动流控|Deep Reinforcement Flow Control|Rabault et al., Journal of Fluid Mechanics 865, 281–302 (2019), doi:10.1017/jfm.2019.62|二维仿真学到的控制策略能否迁移到高雷诺实验|多智能体和鲁棒强化学习继续处理传感与执行延迟|通过与流场交互学习抑制涡脱落的吹吸策略|强化学习在圆柱尾迹中发现非直觉控制并降低阻力，控制律不必先写解析模型|训练成本高且策略依赖数值器、传感器和工况，仿真奖励可能利用数值漏洞
呼吸飞沫多相云|Respiratory Multiphase Cloud|Bourouiba, JAMA 323, 1837–1838 (2020), doi:10.1001/jama.2020.4756|孤立弹道飞沫模型能否解释湍流气团中的传播|通风与气溶胶测量继续连接房间流场和感染风险|把呼出物视为携带多尺度液滴的湿暖湍流云|多相云视角解释小滴为何可被气团携带更远，改变固定距离防护的流体假设|感染风险还依赖病毒活性通风和暴露时间，流动范围不能直接等同传播概率
飞沫与气溶胶连续谱|Droplet-Aerosol Continuum|Mittal, Ni & Seo, Journal of Fluid Mechanics 894, F2 (2020), doi:10.1017/jfm.2020.330|五微米二分法是否符合蒸发沉降与室内流动|室内空气标准继续采用连续粒径与通风剂量|用蒸发和气流把飞沫与气溶胶放在连续谱|COVID-19流动物理综述连接产生、蒸发、输运、沉积和吸入，削弱简单粒径二分|口鼻源强与真实活动差异巨大，理想喷流不能替代房间和人群测量
壁模大涡模拟|Wall-Modeled LES|Bose & Park, Annual Review of Fluid Mechanics 50, 535–561 (2018), doi:10.1146/annurev-fluid-122316-045241|近壁模型能否在分离粗糙和压力梯度中保持通用|高雷诺复杂几何继续以基准数据库校准壁模型|不解析最小近壁尺度而建模壁应力|WMLES把工业高雷诺模拟从不可承受DNS降到可计算网格，同时保留大尺度非定常结构|壁模型输入位置和网格各向异性会产生系统偏差，成本下降不保证壁面载荷准确
机器学习湍流闭合|Machine-Learned Turbulence Closure|Duraisamy, Iaccarino & Xiao, Annual Review of Fluid Mechanics 51, 357–377 (2019), doi:10.1146/annurev-fluid-010518-040547|数据校正能否保持Galilean不变性守恒与分布外稳定|不变量网络和不确定性估计继续约束闭合|从高保真数据学习RANS模型结构误差|机器学习把湍流模型校正从调常数推进到学习应力与状态映射，可针对特定流态降低误差|训练流形之外可能给出非物理应力，局部拟合好也会令全局求解器不稳定
空气循环过滤流体学|Indoor Airflow and Filtration|Krishnaprasad et al., Physics of Fluids 35, 013344 (2023), doi:10.1063/5.0133476|名义换气率能否代表污染物实际清除|房间混合与便携过滤继续以位置和短路流复核|把回风过滤效率与流场输运共同建模|研究显示过滤器效率必须与循环流量和空间混合共同计算，单一ACH会遮蔽死区|门窗人流和热羽流改变路径，实验室均匀混合假设会高估脆弱位置清除
高阶激波捕捉不确定性|High-Order Shock Capturing|Yee et al., Fluids 9, 250 (2024), doi:10.3390/fluids9120250|高阶离散是否在强激波湍流中唯一逼近连续解|2025流体综述强调非线性数值不确定性和自适应混合|并列熵守恒动量守恒和耗散控制审计激波计算|高阶方法将数值耗散从固定代价改成可适应设计，并暴露离散非线性解空间可能大于连续系统|网格收敛若落入不同离散分支，阶数更高反而会稳定错误解
粗糙壁标量输运|Rough-Wall Scalar Transport|Hantsis & Piomelli, Fluids 9, review article (2024)|动量相似性能否直接推出热质输运相似性|多类粗糙与孔隙基底继续比较粗糙子层|把标量与动量的粗糙效应分开测量|近期综述显示粗糙子层控制速度压力和标量的耦合，Townsend相似性并非对所有几何自动成立|Prandtl数和几何细节会改变交换，单一等效砂粒高度不足以代表热传
流动控制跨装置基准|Flow-Control Benchmarking|Kim et al., Fluids 9, 216 (2024), doi:10.3390/fluids9090216|学习策略能否在统一传感执行预算下比较|2025研究转向三维高雷诺和仿真到实验迁移|固定观测执行能耗与稳定性报告控制收益|基准化要求控制策略与无控、经典控制和同预算学习器比较，并公开训练与部署成本|不同数值器可给同一策略不同奖励，缺少实验证据时排名会反转
流体力学闭环验收|Fluid-Mechanics Closed-Loop Acceptance|De Stefano & Rees, Fluids 10, 137 (2025), doi:10.3390/fluids10050137|更细网格和更高分辨是否证明机制跨尺度成立|2025前沿综述并列激波湍流机器学习与工程验证|以无量纲参数守恒误差和跨装置复现共同验收|闭环验收要求每项新机制在至少两个雷诺数两个几何和独立装置复算，并报告质量动量能量残差|不可达的极端参数和保密工业几何会留下外推空白，统一基准也不能替全部场景
""",
)


add(
    585, "solid-continuum-mechanics", "固体与连续介质力学", "数理、信息与计算主干 · 固体力学",
    "从周边动力学、相场断裂、等几何分析、软物质失稳与机械超材料到数据驱动计算力学、拓扑逆设计、机器学习本构和神经算子，审计连续体模型如何跨越裂纹与结构。",
    "固体与连续介质力学的核心变化，是把裂纹、界面、微结构、历史依赖和材料不确定性从方程之外的特殊处理带进统一计算框架。与此同时，学习模型开始替代昂贵本构与均匀化，但守恒、客观性和路径依赖不能由训练误差自动保证。",
    "固体与连续介质力学成立的决定性机制，是让力平衡、本构记忆和结构失效在同一边界与能量账中闭合，而不是让网格收敛或代理模型低误差替材料机制作证",
    "未来五年要看数据驱动本构能否在循环载荷和断裂外推，机械超材料能否把样件性质带到制造分布，软组织模型能否获得个体校准，以及神经算子能否保留能量与接触约束",
    [
        "Bock et al., Frontiers in Materials 6, 110 (2019), doi:10.3389/fmats.2019.00110.",
        "Grossi et al., NeuberNet: a Neural Operator Solving Elastic-Plastic PDEs, Communications Engineering (2025).",
        "Kumar et al., npj Computational Materials 6, 73 (2020), doi:10.1038/s41524-020-0341-6.",
        "Mianroodi et al., npj Computational Materials 8, 67 (2022), doi:10.1038/s41524-022-00753-3.",
    ],
    r"""
周边动力学断裂|Peridynamics|Silling & Askari, Computers & Structures 83, 1526–1535 (2005), doi:10.1016/j.compstruc.2004.11.026|非局部积分模型能否同时保持局部弹性极限和裂纹自由生长|对应态与键基模型继续处理多轴材料和边界校准|用有限视界内点对作用替代空间导数|周边动力学让裂纹无需预置路径即可从键断裂出现，跨越经典偏微分方程在不连续面失效的问题|视界尺寸和表面修正会改变刚度与裂纹能，网格细化若不同时缩视界不会收敛到同一模型
相场断裂|Phase-Field Fracture|Miehe, Hofacker & Welschinger, Computer Methods in Applied Mechanics and Engineering 199, 2765–2778 (2010), doi:10.1016/j.cma.2010.04.011|弥散裂纹宽度能否在复杂三维和动力载荷下保持客观|不可逆约束与延性疲劳相场继续统一多种失效|用连续损伤场逼近裂纹面能并自动分叉|相场法把裂纹起裂、扩展、合并和分叉放入变分能量框架，减少显式追踪|长度尺度、张压分裂和网格会改变路径，漂亮裂纹图不等于真实断裂韧度
等几何分析|Isogeometric Analysis|Cottrell, Hughes & Bazilevs, Isogeometric Analysis, Wiley (2009)|CAD基函数能否在局部加密和复杂拓扑下保持优势|THB样条与无缝几何继续服务壳体和流固耦合|用NURBS同一表示承担几何与有限元近似|等几何分析减少CAD到网格的几何误差，以高连续基函数提高壳和高阶PDE效率|局部细化、修剪曲面和装配接口复杂，几何精确不代表材料与边界条件精确
计算均匀化FE²|Computational Homogenization FE²|Geers, Kouznetsova & Brekelmans, Journal of Computational and Applied Mathematics 234, 2175–2182 (2010), doi:10.1016/j.cam.2009.08.077|代表体积单元能否覆盖局部化与尺寸效应|降阶微结构求解和并行FE²继续降低嵌套成本|在每个宏观点求解微结构边值问题返回本构|FE²把微结构响应直接回写宏观积分点，使复合材料不必先拟合固定闭式本构|局部化后代表体积失去尺度分离，边界条件选择和微求解成本会主导结果
软材料表面失稳|Soft-Solid Surface Instability|Hohlfeld & Mahadevan, Physical Review Letters 106, 105702 (2011), doi:10.1103/PhysRevLett.106.105702|尖锐折皱是否能由平滑分叉理论完全描述|软界面研究继续区分皱纹折皱空化与粘附|识别强压缩软固体的亚临界折皱失稳|折皱研究显示软表面可从平滑状态突跳到自接触尖沟，线性皱纹并非唯一前兆|表面能粘弹性与缺陷会移动阈值，理想半空间结果不能直接外推组织和涂层
机械超材料负泊松与编程刚度|Mechanical Metamaterials|Bertoldi et al., Advanced Materials 22, 361–366 (2010), doi:10.1002/adma.200901956|单胞失稳产生的宏观性质能否在制造缺陷下保持|可重构和多稳定超材料继续扩大响应空间|利用结构屈曲而非化学成分设计整体性质|周期孔洞弹性体通过屈曲变换获得负泊松和可调刚度，材料性质成为几何程序|缺陷会选择不同屈曲模态且尺度放大改变边界层，单胞曲线不等于整件响应
数据驱动计算力学|Data-Driven Computational Mechanics|Kirchdoerfer & Ortiz, Computer Methods in Applied Mechanics and Engineering 304, 81–101 (2016), doi:10.1016/j.cma.2016.02.001|绕过本构方程能否在稀疏噪声数据下保持物理一致|局部凸化和不确定数据驱动方法继续完善|在满足平衡相容的状态中直接匹配材料数据库|数据驱动力学不先拟合应力应变公式，而让计算在物理约束与观测数据间找最近状态|数据库覆盖不足会把最近邻冒充材料规律，距离度量和噪声模型决定答案
变分接触与摩擦|Variational Contact Mechanics|Wriggers, Computational Contact Mechanics, second edition (2006)|罚参数和接触离散能否同时避免穿透锁死与能量伪增|无光滑牛顿和黏聚接触继续提高鲁棒性|以约束和互补条件统一接触分离与摩擦|现代接触算法把开闭、粘滑和大变形放入可求解变分不等式，支持复杂装配模拟|网格不匹配与时间步会制造接触颤振，收敛残差小也可能违反能量耗散
拓扑优化制造约束|Manufacturing-Aware Topology Optimization|Lazarov & Sigmund, International Journal for Numerical Methods in Engineering 86, 765–781 (2011), doi:10.1002/nme.3078|滤波与投影能否同时消除网格依赖和保证可制造|增材制造悬垂尺寸与多材料约束继续进入优化|把最小尺度和黑白设计写入密度法|滤波投影让拓扑优化从棋盘格图形走向具备长度尺度的结构设计|制造误差、载荷不确定和疲劳若不入目标，名义最轻结构会在实物中失效
连续体机器人软体建模|Soft Robotics Continuum Mechanics|Rus & Tolley, Nature 521, 467–475 (2015), doi:10.1038/nature14543|低维杆壳模型能否覆盖材料迟滞接触和流固驱动|可微软体仿真和形态控制继续连接设计与学习|利用大变形柔性体把结构同时当执行器|软体机器人使连续变形、材料非线性和环境接触成为功能来源，而非需消除误差|气动迟滞和材料老化难以校准，仿真轨迹在实物上会积累偏差
晶格材料尺寸效应|Architected Lattice Size Effects|Zheng et al., Science 344, 1373–1377 (2014), doi:10.1126/science.1252291|微晶格高比刚度能否在节点缺陷与大尺寸制造中保持|纳米晶格和层级结构继续比较缺陷敏感性|以空心微梁构造超轻高刚度晶格|微晶格显示几何架构可获得极低密度和可恢复压缩，性能不再由块体材料单独决定|节点偏心壁厚分散和尺寸扩大造成最弱链，单位质量纪录不含制造良率
有限元模型验证与确认|Verification and Validation|ASME V&V 10-2006, Guide for Verification and Validation in Computational Solid Mechanics|代码正确与模型真实能否被同一实验区分|数字工程继续要求层级验证不确定性与适用域|分开数值验证、实验确认和预测不确定性|V&V规范把方程求解正确与方程代表现实分开，模型结果不再因网格收敛自动可信|确认数据与校准数据重用会虚高一致性，适用域外预测仍无证据
断裂疲劳相场|Phase-Field Fatigue|Carrara et al., Computer Methods in Applied Mechanics and Engineering 361, 112731 (2020), doi:10.1016/j.cma.2019.112731|循环历史变量能否在多轴载荷下保持材料可识别性|疲劳相场继续向焊缝复合材料与腐蚀耦合|让裂纹面能随累积循环耗散退化|疲劳相场将成核和扩展置于统一历史变量，避免预置Paris裂纹路径|参数常由一类试验反演，多种历史变量可拟合同一S-N曲线而给出不同路径
逆设计spinodoid材料|Inverse-Designed Spinodoids|Kumar et al., npj Computational Materials 6, 73 (2020), doi:10.1038/s41524-020-0341-6|机器学习逆设计能否在训练性质之外满足强度与制造|生成式超材料继续加入多目标和不确定性|从目标各向异性刚度反推非周期微结构|spinodoid方法用随机场和学习器快速生成均匀或梯度微结构，突破周期晶格的性质空间|代理模型只看弹性模量时会忽略屈曲疲劳和打印缺陷，反设计命中不等于实物合格
多尺度机器学习本构|Machine-Learned Constitutive Relations|Mianroodi et al., npj Computational Materials 8, 67 (2022), doi:10.1038/s41524-022-00753-3|无损压缩微结构信息能否跨路径预测应力|图网络和神经算子继续处理材料历史和旋转客观性|学习微结构到本构响应的多尺度映射|深度模型在保持多尺度信息下逼近昂贵微观计算，为实时材料模拟提供新路线|训练应变路径之外会违反耗散或客观性，低平均误差会遮蔽少数不稳定状态
物理约束神经本构|Physics-Constrained Constitutive Learning|Linka et al., Computer Methods in Applied Mechanics and Engineering 393, 114823 (2022)|凸性客观性和耗散约束能否保证真实材料外推|输入凸网络与热力学网络继续编码本构公理|把材料对称与能量约束写进网络结构|物理约束网络减少非物理应力，证明学习器可以继承连续介质公理而非只拟合曲线|约束集合本身可能不完整，满足热力学并不唯一确定材料记忆
4D打印形态编程|4D Printing Mechanics|Gladman et al., Nature Materials 15, 413–418 (2016), doi:10.1038/nmat4544|局部膨胀编码能否在厚度制造和循环湿热中保持目标形状|多材料打印继续推进可逆驱动与负载能力|以各向异性纤维和膨胀差编程后续变形|4D打印让制造后的时间响应成为设计变量，片材可在刺激下自发形成曲面|驱动扩散慢、循环漂移和负载反作用会改变形态，空载演示不等于结构执行
个体化软组织数字模型|Patient-Specific Soft-Tissue Mechanics|Holzapfel & Ogden, Biomechanics: Trends in Modeling and Simulation (2017–2024)|影像几何与群体本构能否产生个体可信应力|反演和不确定性量化继续校准心血管脑与肿瘤组织|用个体影像边界与材料参数求组织应力|个体化模型把临床影像转成连续体边值问题，为手术和破裂风险提供局部分布|多数材料参数来自群体或离体样本，几何个体化不等于力学个体化
弹塑性神经算子|Neural Operator for Elastoplasticity|Grossi et al., Communications Engineering, NeuberNet (2025)|算子代理能否跨几何载荷和塑性路径保持屈服一致|2025研究把神经算子推进弹塑性偏微分方程|学习从边界载荷与材料到全场应力应变的算子|NeuberNet类方法显著加快弹塑性场预测，使多次查询和逆设计获得实时可能|训练网格和载荷族之外会错过局部塑性带，代理速度不能替屈服与平衡残差
固体力学闭环验收|Solid-Mechanics Closed-Loop Acceptance|Bock et al., Frontiers in Materials 6, 110 (2019), doi:10.3389/fmats.2019.00110|代理模型或新材料样件能否以能量失效和制造分布共同验收|2025神经算子与超材料研究开始并列物理残差和外推|以平衡能量路径和实物分布验收预测|闭环验收要求公开本构训练域、网格、边界、耗散、断裂与制造偏差，并用独立载荷路径测试|真实服役组合载荷和长期老化难在实验期覆盖，适用域边界必须保持可见
""",
)


add(
    586, "thermofluid-science", "热流体科学", "数理、信息与计算主干 · 热流体",
    "从微纳尺度传热、沸腾纳米结构、相变储能、超临界二氧化碳循环与被动辐射制冷到热泵、热化学储能、数据驱动沸腾和热管理，审计热与流的系统效率。",
    "热流体科学的变化不只是换热系数越来越高，而是系统边界从局部壁面扩到工质、泵功、天气、储能周期和供热服务。实验室中的临界热流密度、瞬时制冷功率或单次储能密度，必须经受长期循环、污损和全系统能量品位的复核。",
    "热流体科学成立的决定性机制，是让热量、流动功、温差品位和失效周期在同一系统边界守恒，而不是把局部换热增强或材料峰值当作总体效率",
    "未来五年要看高温储热能否跨千次循环，热泵在严寒和高供水温度下能否保持季节性能，辐射制冷能否抵抗污染湿热，以及AI沸腾模型能否跨工质与表面迁移",
    [
        "Cahill et al., Applied Physics Reviews 1, 011305 (2014), doi:10.1063/1.4832615.",
        "International Energy Agency, The Future of Heat Pumps and 2025 Heat Pump Market Update (2025).",
        "Zhao et al., Nature 517, 216--222 (2015), doi:10.1038/nature13883.",
        "De Stefano & Rees, Fluids 10, 137 (2025), doi:10.3390/fluids10050137.",
    ],
    r"""
微纳尺度界面热阻|Nanoscale Interfacial Thermal Transport|Cahill et al., Applied Physics Reviews 1, 011305 (2014), doi:10.1063/1.4832615|体材料热导率能否代表纳米界面和非平衡声子输运|超快测温与第一性原理继续分解界面模态|把界面热阻与尺寸效应纳入热传导主账|微纳传热研究显示当尺度接近声子平均自由程，傅里叶局部平衡和块体参数不再充分|界面粗糙、电子声子耦合和样品制备会改变读数，不同测量法不可直接拼接
纳米结构沸腾表面|Nanostructured Boiling Surfaces|Chen et al., Applied Physics Letters 95, 161909 (2009), doi:10.1063/1.3257697|更多成核点能否同时提高换热和临界热流而不被污损|层级毛细结构继续以长期稳定和制造一致性验收|用微纳结构调控成核补液和汽泡脱离|结构化表面显著改变成核密度和液体回补，让沸腾性能成为可设计边界|纳米涂层老化、污染和局部干斑会使初始增益衰减，短时去离子水纪录不能外推工业工质
相变材料储热|Phase-Change Thermal Storage|Sharma et al., Renewable and Sustainable Energy Reviews 13, 318–345 (2009), doi:10.1016/j.rser.2007.10.005|潜热密度能否抵消低导热过冷和容器成本|复合PCM与封装继续提高功率和循环寿命|以固液相变在近恒温下存取热量|PCM把储热从显热温升改成相变潜热，适合建筑调温和间歇热源|材料标称潜热不含换热器和封装，循环相分离会让系统密度远低于样品
太阳热化学燃料循环|Solar Thermochemical Cycles|Chueh et al., Science 330, 1797–1801 (2010), doi:10.1126/science.1197834|高温氧化还原效率能否覆盖聚光损失和材料循环|铈基与钙钛矿循环继续优化温度摆幅和产率|用非化学计量氧化物分解水和二氧化碳|铈氧化物循环在聚光高温下生成氢和一氧化碳，把太阳热直接储存在化学键|反应产率低且需真空或惰性气，反应器热回收决定系统效率
超临界二氧化碳布雷顿循环|Supercritical CO2 Brayton Cycle|Dostal, Driscoll & Hejzlar, MIT report and cycle development (2004–2006)|紧凑高效率循环能否控制临界点压缩和高温材料|示范机组继续测试透平密封与换热器|利用临界点附近高密度降低压缩功|超临界二氧化碳循环以紧凑透平和回热器连接核能聚光太阳与余热，挑战蒸汽循环体积|临界点环境变化、换热器压降和材料腐蚀会吞掉理论效率，部件纪录不等于净电效率
热二极管与热整流|Thermal Rectification|Chang et al., Science 314, 1121–1124 (2006), doi:10.1126/science.1132898|纳米尺度方向性热流能否放大到可用器件|相变与非线性热器件继续追求高整流比|让同一温差反向时产生不同热流|纳米管质量梯度实验推动热流像电流一样被整流，开启声子器件概念|接触热阻和测量漂移可能制造方向差，器件功率和温区远低于工程换热需求
喷雾冷却高热流|Spray Cooling|Kim, International Journal of Heat and Fluid Flow 28, 753–767 (2007), doi:10.1016/j.ijheatfluidflow.2006.09.003|高热通量是否以泵功液滴损失和不均匀性为代价|电子和航天热管理继续优化喷嘴反馈与工质|用液滴冲击蒸发移除高面热流|喷雾冷却把相变和液滴动量结合，可处理远高于单相冷板的局部热通量|喷嘴堵塞、液体回收和表面干斑使平均热流掩盖热点，系统泵功必须入账
纳米流体导热争议|Nanofluid Heat Transfer|Buongiorno et al., Journal of Applied Physics 106, 094312 (2009), doi:10.1063/1.3245330|异常导热是否超过有效介质与测量误差可解释范围|标准化圆桌测试继续压缩早期夸大效应|用多机构同协议比较纳米流体热导|国际基准显示多数纳米流体增强可由经典有效介质解释，清算了异常倍增叙事|团聚、沉降和黏度增加会让导热上升转成对流和泵功损失
日间被动辐射制冷|Daytime Radiative Cooling|Raman et al., Nature 515, 540–544 (2014), doi:10.1038/nature13883|晴空样片的净制冷能否在云湿污染与建筑负荷下保持|选择发射体与规模化涂层继续进入现场测试|在太阳波段反射并向大气窗口辐射热|光子结构首次在正午实现低于环境温度的无功制冷，天空成为可利用冷源|云量湿度和表面污染关闭大气窗口，单位面积净功率不能直接等同建筑节电
超冷表面凝露传热|Jumping-Droplet Condensation|Boreyko & Chen, Physical Review Letters 103, 184501 (2009), doi:10.1103/PhysRevLett.103.184501|跳滴强化能否在高过冷污染和不凝气体下长期保持|耐久超疏水与润滑表面继续比较凝结寿命|让合并液滴以表面能自行弹离|跳滴凝结减少液膜覆盖并提高传热，展示液滴动力学可代替外部排液|涂层缺陷和霜冻结会迅速钉扎液滴，纯蒸汽小样结果会高估设备收益
热管与蒸汽腔均温|Vapor-Chamber Thermal Management|Faghri, Heat Pipe Science and Technology, second edition (2016)|被动两相均温能否跨姿态和瞬态热点保持毛细回流|超薄蒸汽腔继续服务高功率芯片与电池|以蒸发冷凝和毛细芯无泵搬运热量|蒸汽腔把芯片热点扩散到更大散热面，热管理从材料导热转向两相循环|干涸、非凝气和姿态会使等效热阻反号，稳态额定功率不代表脉冲能力
弹热制冷|Elastocaloric Cooling|Tušek et al., Nature Energy 1, 16134 (2016), doi:10.1038/nenergy.2016.134|材料绝热温变能否转化为高循环系统COP|形状记忆合金再生器继续处理疲劳和换热|用应力诱导相变吸放潜热|弹热原型显示固态制冷可获得大温变并避免高GWP制冷剂|驱动机械功、材料疲劳和热交换速率决定系统性能，单次温变不是COP
界面太阳蒸发|Interfacial Solar Evaporation|Ghasemi et al., Nature Communications 5, 4449 (2014), doi:10.1038/ncomms5449|局域加热高蒸发率能否在盐污和完整能量账下成立|抗盐多级蒸发器继续面向淡化和废水|把太阳吸收和蒸发限制在水气界面|界面蒸发减少加热体相水的损失，以低导热浮层提高太阳到蒸汽效率|环境吸热和暗蒸发基线会夸大效率，盐结晶与冷凝回收决定可用产水
高温颗粒储热|Particle Thermal Energy Storage|US DOE Gen3 CSP particle receiver programmes (2017–2025)|颗粒千度储热能否在磨损粉尘与换热器压降下保持|落幕接收器和颗粒换热器进入放大示范|用廉价固体颗粒直接吸热并储存|高温颗粒把接收与储热介质合一，可向超临界循环供更高品位热|颗粒磨损、吸收率漂移和输运功会降低循环效率，材料吨价不能替系统成本
全天候辐射热管理|All-Weather Radiative Thermal Management|Zhao et al., Nature 517, 216–222 (2015), doi:10.1038/nature13883|透明气凝胶和选择发射是否在风雨机械载荷下耐久|可规模涂层继续从净功率转向年化节能|协同调控太阳吸收红外辐射与对流|辐射热管理把光谱和热流路径共同设计，可无电冷却或选择性保温|实验台光谱随污染老化，风对流和天空温度会重排实际热平衡
工业高温热泵|Industrial Heat Pumps|Arpagaus et al., Energy 152, 985–1010 (2018), doi:10.1016/j.energy.2018.03.166|高供水温度COP能否在真实热源波动和工质限制下保持|天然工质与蒸汽压缩高温机组继续商业化|用电功把低品位余热提升到过程温度|工业热泵把脱碳从燃料替代推进到热级联，回收原本排放的低温热|温升过大和热源中断会降低季节COP，额定点效率不能代表工厂年运行
机器学习沸腾曲线|Machine Learning for Boiling|Ravichandran et al., International Journal of Heat and Mass Transfer 2020–2024 studies|图像与表面数据能否跨工质预测临界热流|多模态沸腾数据库开始记录表面和瞬态|从汽泡图像和工况学习换热与危机前兆|学习器可从高速成像和传感信号识别沸腾状态，提前预警干涸和临界热流|训练表面与相机设置之外会失准，预警分数必须与真实危机时间比较
热化学储能|Thermochemical Energy Storage|Cabeza et al., Renewable and Sustainable Energy Reviews 89, 138–158 (2018), doi:10.1016/j.rser.2018.03.015|高理论密度能否穿过反应速率传质与循环稳定|盐水合物和氧化还原体系继续做百至千次循环|以可逆化学反应长期储存热品位|热化学储能理论上低自放电且密度高，适合季节储热和工业热|副反应、团聚和换热器占比会使样品焓远高于装置可用密度
热泵季节性能验收|Heat-Pump Seasonal Performance|International Energy Agency, The Future of Heat Pumps and 2025 Market Update (2025)|实验室COP能否代表严寒除霜和高温供热的全年表现|2025市场更新强调电网配合安装质量和建筑围护|以季节供热量除以全年用电量验收热泵|季节性能把温度分布、除霜、辅助电加热和部分负荷写进同一比值，纠正额定COP崇拜|安装与建筑差异巨大，市场销量上升不证明每台设备实现减排
热流体闭环验收|Thermofluid Closed-Loop Acceptance|De Stefano & Rees, Fluids 10, 137 (2025), doi:10.3390/fluids10050137|局部换热纪录能否经泵功循环寿命和环境边界复算|2025前沿综述要求把数值不确定与工程验证并列|以净热服务全辅助能耗和寿命保持率共同验收|闭环验收要求公开热流面积温差工质流量泵功环境条件循环数和失效事件，局部系数仅是一项输入|现场污损和维护制度难在短期试验复制，结论必须标注可外推工况
""",
)


add(
    587, "network-science", "网络科学", "数理、信息与计算主干 · 复杂网络",
    "从社团可探测极限、富人俱乐部、k核、网络可控性与多层网络到高阶相互作用、时序群组、因果重建、图神经网络和韧性干预，审计关系结构如何真正产生系统行为。",
    "网络科学已从静态连边图扩展到有方向、有时间、有层次且包含群组作用的动力系统。中心性、社团和传播阈值仍然有用，但只有在采样机制、时间顺序、干预成本和反事实预测同时受检验时，它们才不是漂亮的结构描述。",
    "网络科学成立的决定性机制，是让观测网络、生成过程、动力传播和可执行干预在同一因果边界内闭合，而不是把相关结构、中心节点或模拟级联当作机制证明",
    "未来五年要看高阶和时序模型能否得到可辨识数据支持，图学习能否跨网络迁移，网络干预能否从仿真走向现场随机或准实验，以及韧性指标能否包含适应与代价",
    [
        "Battiston et al., Physics Reports 874, 1--92 (2020), doi:10.1016/j.physrep.2020.05.004.",
        "Iacopini et al., Nature Communications 15, 7392 (2024), higher-order temporal dynamics.",
        "Malizia et al., Nature Communications 15, 4907 (2024), higher-order network reconstruction.",
        "Runge et al., Nature Communications 10, 2553 (2019), doi:10.1038/s41467-019-10105-3.",
    ],
    r"""
社团探测分辨率极限|Community-Detection Resolution Limit|Fortunato & Barthélemy, Proceedings of the National Academy of Sciences 104, 36–41 (2007), doi:10.1073/pnas.0605965104|模块度最大化能否识别规模差异巨大的真实社团|多分辨率与统计生成模型继续区分结构层级|证明模块度目标会系统合并小社团|分辨率极限说明即使分区得分很高，小而清晰的群体也可能被全局目标吞并，社团不是算法无关的事实|网络规模、度分布和空模型都会改变边界，单一最优分区不能替代稳定性与外部验证
富人俱乐部组织|Rich-Club Organization|Colizza et al., Nature Physics 2, 110–115 (2006), doi:10.1038/nphys209|高度节点彼此密连是否超过度序列自然预期|加权和有方向富人俱乐部继续进入脑网与运输网|用保持度的空模型检验核心互联超额|富人俱乐部系数把枢纽数量与枢纽互连分开，避免把高度节点自然拥有更多边误读为精英核心|空模型若不保持空间成本或权重会夸大显著性，核心连通不自动意味着控制力
k核与影响力|K-Core Influence|Kitsak et al., Nature Physics 6, 888–893 (2010), doi:10.1038/nphys1746|传播影响由度数还是嵌套核心位置决定|多类型和时序k核继续测试跨平台稳健性|递归剥离低度节点定位结构核心|k核研究显示位于深核的节点可比外围高连接节点触发更广传播，局部度数并非唯一影响代理|结论依赖传播模型与全网可见性，平台采样会错估壳层且现实干预会改变网络
网络可控性|Structural Controllability of Networks|Liu, Slotine & Barabási, Nature 473, 167–173 (2011), doi:10.1038/nature10011|最少驱动节点的结构判据能否代表带能量与约束的实际控制|控制能量、非线性和时间变化继续修正结构结论|以最大匹配推导线性系统驱动节点集合|结构可控性把网络拓扑与控制输入配置连接起来，给出大网络最低驱动节点的可计算判据|参数近退化会使理论可控但能量不可承受，非线性饱和和观测限制也不在结构判据内
时序网络|Temporal Networks|Holme & Saramäki, Physics Reports 519, 97–125 (2012), doi:10.1016/j.physrep.2012.03.001|聚合静态图是否保留传播可达性和因果顺序|事件网络与连续时间建模继续连接人类活动数据|保留接触发生时刻而非只累计连边|时序网络揭示同样的聚合结构可因事件顺序产生完全不同的传播、同步和可达性|时间分辨率和缺失事件会改写路径，观察窗口中的活跃周期不能外推长期机制
多层与多重网络|Multilayer Networks|Kivelä et al., Journal of Complex Networks 2, 203–271 (2014), doi:10.1093/comnet/cnu016|把不同关系层叠加是否会掩盖层间依赖和身份耦合|张量表示与跨层社区继续进入交通金融和生物系统|用节点层对和跨层边表达多类关系|多层框架区分同一主体在交通、通信或社会层中的连接，使层间失效和协同可被显式建模|层的定义和耦合权重常由研究者设定，复杂表示不等于数据支持更充分
社团可探测极限|Community Detectability Threshold|Decelle et al., Physical Review E 84, 066106 (2011), doi:10.1103/PhysRevE.84.066106|弱社团何时在信息论上无法从随机波动中恢复|谱算法与贝叶斯推断继续逼近稀疏图阈值|用随机块模型推导结构恢复相变|可探测阈值把算法失败与信息不足分开：阈值以下并不存在可可靠恢复的隐藏标签|真实网络未必来自块模型，度异质和重叠群体会移动阈值，模拟可恢复性不是现实标签真值
相依网络级联|Interdependent-Network Cascades|Buldyrev et al., Nature 464, 1025–1028 (2010), doi:10.1038/nature08932|跨基础设施依赖是否让局部故障产生突变崩溃|部分依赖、空间嵌入和恢复调度继续修正级联模型|把供电通信等层间依赖写入渗流过程|相依网络模型说明单层稳健的系统也可因跨层反馈发生不连续崩溃，韧性必须跨系统评估|一一依赖和随机失效过于理想，真实替代路径与运营响应可缓冲或放大预测
网络几何与导航|Network Geometry|Papadopoulos et al., Nature 489, 537–540 (2012), doi:10.1038/nature11459|隐藏双曲距离能否同时解释层级聚类与高效路由|动态嵌入继续用于互联网和生物网络预测|以流行度和相似度坐标生成并导航网络|双曲几何用低维隐藏空间解释无标度度数、聚类和贪婪路由，使结构预测获得几何语言|嵌入存在非唯一性且会受缺边影响，良好路由不证明节点真的按隐藏坐标形成
多层中心性|Multilayer Centrality|De Domenico et al., Nature Communications 6, 6868 (2015), doi:10.1038/ncomms7868|跨层中心节点是否优于逐层排名的简单组合|可解释中心性继续处理层切换成本和方向性|在多层邻接张量上推广随机游走与中心性|多层中心性让同一节点在不同关系层中的作用被联合计算，可识别单层排名遗漏的跨层桥梁|层间权重会支配结果且常缺独立校准，排名变化不等于实际干预效果
网络神经科学|Network Neuroscience|Bassett & Sporns, Nature Neuroscience 20, 353–364 (2017), doi:10.1038/nn.4502|脑连接图的模块与枢纽能否解释认知而非仅与任务相关|多尺度结构功能耦合继续连接发育疾病和刺激|把解剖与功能连接置于图动力学框架|网络神经科学以模块、富核和可控性描述脑区协同，为跨尺度认知研究提供共同坐标|成像相关连接不等于突触因果，头动、阈值和脑区划分都会改变网络结论
图卷积学习|Graph Convolutional Networks|Kipf & Welling, International Conference on Learning Representations (2017)|邻域聚合能否学习有用表示而不把异质节点过度平滑|异配图、位置编码和可扩展训练继续突破局限|用局部消息传递共享非欧式结构信息|图卷积把拓扑直接纳入端到端学习，推动分子、推荐与知识图任务从人工特征转向表示学习|同质假设和训练图偏差会失效，层数增加造成过平滑且预测解释不等于网络机制
多层传播与认知反馈|Multiplex Epidemics with Awareness|Granell, Gómez & Arenas, Physical Review Letters 111, 128701 (2013), doi:10.1103/PhysRevLett.111.128701|信息传播能否改变疾病阈值和流行规模|行为适应与错误信息继续进入耦合传播模型|在接触层与认知层联立两种扩散过程|多层传播模型显示风险认知可抑制传染并产生元临界点，传播过程会反过来改造网络状态|认知状态和行为响应通常被二元化，参数拟合不足时相变位置只是情景而非预测
高阶网络动力学|Higher-Order Network Dynamics|Battiston et al., Physics Reports 874, 1–92 (2020), doi:10.1016/j.physrep.2020.05.004|成对连边是否足以表示协作、共识和群体传染|超图与单纯复形继续发展可辨识的动力方程|以群组相互作用替代全部二元投影|高阶网络说明三人以上共同作用可改变同步、扩散与稳定性，投影图会丢失群组门槛|高阶项数量爆炸且数据稀疏，同样的投影观测可对应多种不可区分机制
单纯复形传染|Simplicial Contagion|Iacopini et al., Nature Communications 10, 2485 (2019), doi:10.1038/s41467-019-10431-6|群组强化是否会令连续传播阈值转为不连续跃迁|社交强化实验和时序群组数据继续检验预测|允许个体由完整群组而非单邻居共同感染|单纯传染模型显示高阶接触可产生双稳态和突发扩散，为复杂采用行为提供不同于疾病传播的机制|群组率参数难从平台日志识别，观测到突增也可能来自外部冲击或算法推荐
因果网络重建|Causal Network Reconstruction|Runge et al., Nature Communications 10, 2553 (2019), doi:10.1038/s41467-019-10105-3|高维时间序列能否区分直接因果、共同驱动和滞后链|PCMCI等方法继续面向气候生态和神经数据|以条件独立检验筛选时滞因果父节点|因果重建把相关网络推进到有方向的条件依赖，并用控制虚假发现率处理高维候选|未观测混杂、非平稳和采样过慢仍会制造边，算法输出必须接受干预或外部机制验证
时序群组相互作用|Temporal Group Interactions|Iacopini et al., Nature Communications 15, 7392 (2024)|高阶接触的持续时间和顺序是否决定集体动力|2025研究继续比较群组记忆与静态超图近似|同时保留群组构成和事件时间|时序高阶框架显示群组出现顺序与持续性可重排扩散和协调，时间聚合会丢失关键协同路径|群组观测常来自会议或平台代理，时间戳精确不代表互动强度和语义准确
高阶结构重建|Higher-Order Network Reconstruction|Malizia et al., Nature Communications 15, 4907 (2024)|仅凭节点动力学能否识别真实三体及以上作用|稀疏推断继续用受控扰动压缩候选项|从多变量轨迹同时反演二元和高阶耦合|2024方法把高阶网络从描述工具推进为可由动力数据估计的对象，并比较不同阶数证据|轨迹长度、噪声和共线项会造成不可辨识，稀疏解不必等于真实作用阶数
网络韧性干预|Network-Resilience Intervention|Gao, Barzel & Barabási, Nature 530, 307–312 (2016), doi:10.1038/nature16948|一维有效状态能否预测异质网络的临界恢复点|2025研究转向自适应恢复和跨层代价优化|以平均有效动力刻画复杂系统稳定性|韧性降维为生态、基础设施和生物网络提供共同临界指标，使恢复讨论超越单点中心性|平均场会掩盖局部不可逆失效，理论临界点若无现场扰动验证不能直接指导资源配置
网络科学闭环验收|Network-Science Closed-Loop Acceptance|Iacopini et al., Nature Communications 15, 7392 (2024)|结构指标能否经外部预测、反事实和实际干预共同验收|2025高阶时序研究强调数据生成与机制可辨识|以采样审计、留出预测和干预代价验收网络机制|闭环验收要求公开节点边定义、缺失机制、时间分辨率、空模型、参数识别与预注册干预，结构发现必须改善外部结果|许多关键网络无法随机干预且隐私限制原始数据，结论需保留不可识别范围和多模型等价性
""",
)


add(
    588, "mathematical-biology", "数学生物学", "数理、信息与计算主干 · 生命系统",
    "从随机基因表达、网络模体、生物节律、肿瘤演化、空间流行病学与形态发生到RNA速度、通用微分方程、数字孪生、扰动单细胞和可辨识个体治疗，审计生命模型的预测边界。",
    "数学生物学已从给平均曲线配方程，转向同时描述细胞异质、空间结构、演化反馈和治疗干预。最危险的捷径是让模型拟合替代机制，让群体参数替代个体校准，或让单细胞快照替代真实谱系与时间。",
    "数学生物学成立的决定性机制，是让生物假设、观测过程、参数可辨识性和干预预测在同一实验闭环中相互约束，而不是用高拟合度或漂亮相图替代可证伪机制",
    "未来五年要看多组学扰动能否识别因果调控，肿瘤和免疫数字孪生能否前瞻预测治疗，空间模型能否连接组织尺度，以及学习微分方程能否保留生物不确定性与可辨识性",
    [
        "Rackauckas et al., arXiv:2001.04385, Universal Differential Equations for Scientific Machine Learning (2020).",
        "Philipps et al., npj Systems Biology and Applications 11 (2025), universal differential equations review.",
        "Lotfollahi et al., Molecular Systems Biology 15, e8746 (2019), doi:10.15252/msb.20188746.",
        "La Manno et al., Nature 560, 494--498 (2018), doi:10.1038/s41586-018-0414-6.",
    ],
    r"""
随机基因表达|Stochastic Gene Expression|Raj & van Oudenaarden, Cell 135, 216–226 (2008), doi:10.1016/j.cell.2008.09.050|细胞间差异是噪声还是被调控的功能变量|单分子与谱系测量继续分解内源外源波动|用随机反应过程描述低拷贝转录翻译|随机基因表达把平均浓度背后的爆发和细胞间分布纳入机制，使噪声可影响命运决定|固定细胞快照无法区分时间波动与稳定亚群，报告基因会改变原有动力学
网络模体与功能|Network Motifs|Alon, Nature Reviews Genetics 8, 450–461 (2007), doi:10.1038/nrg2102|局部拓扑重复是否足以推出动态功能和进化选择|合成生物实验继续检验前馈环和反馈回路|以随机网络为基线寻找过度出现的小子图|网络模体将复杂调控图分解为可分析电路，连接拓扑结构与过滤、脉冲和稳态响应|空模型和网络重建误差会改变富集，结构相同的模体可因参数不同执行相反功能
昼夜节律磷酸化振荡|Post-Translational Circadian Oscillator|Rust et al., Science 318, 809–812 (2007), doi:10.1126/science.1148596|无转录反馈的蛋白修饰能否维持精确二十四小时节律|体外重构继续分解温度补偿和能量消耗|用Kai蛋白磷酸化循环建立最小生物钟|蓝藻体外系统证明少数蛋白与ATP即可重构稳定节律，使生物钟机制不再依赖完整细胞|重构振荡不包含代谢和环境输入，最小机制不能独自解释体内同步与适应
肿瘤演化博弈|Evolutionary Game Theory in Cancer|Gatenby & Vincent, Cancer Research 69, 4894–4903 (2009), doi:10.1158/0008-5472.CAN-08-4354|肿瘤亚克隆相互作用能否预测治疗选择和耐药|适应性治疗试验继续以生态竞争控制敏感细胞|把肿瘤表型视为争夺资源的演化策略|演化博弈将治疗从最大杀伤改写为选择压力管理，解释耐药克隆为何在强治疗下获得优势|支付矩阵难从患者数据识别且随微环境变化，简化策略不能替代克隆谱系和药代动力学
传染病元群体流动|Mobility-Coupled Epidemic Metapopulations|Balcan et al., Proceedings of the National Academy of Sciences 106, 21484–21489 (2009), doi:10.1073/pnas.0906910106|交通流能否从局部传播参数推导全球到达顺序|实时移动数据继续与行为变化和政策响应联动|用城市节点与航空通勤流耦合随机传播|元群体模型把局部感染与跨城迁移连接起来，可预测疫情时空扩散的概率范围|移动数据偏差、政策反馈和病原变异会迅速使固定网络失效，到达时间不是病例规模保证
反应扩散形态发生|Reaction-Diffusion Pattern Formation|Kondo & Miura, Science 329, 1616–1620 (2010), doi:10.1126/science.1179047|图灵机制能否由活体扰动而非相似花纹确认|定量成像和合成系统继续测试抑制激活尺度|以局部激活长程抑制生成空间图案|形态发生研究把斑纹从描述推进到可扰动的反应扩散机制，强调动态恢复比静态外观更有证据力|多种力学和细胞运动机制也能造相似图案，拟合波长不足以唯一识别图灵系统
细胞群体随机命运|Stochastic Cell-Fate Decisions|Balázsi, van Oudenaarden & Collins, Cell 144, 910–925 (2011), doi:10.1016/j.cell.2011.01.030|随机开关能否提高群体在变化环境中的长期适应|谱系追踪继续区分遗传状态和瞬态表型|以双稳态反馈和噪声描述命运转换|随机命运模型解释同基因细胞为何分化出耐受或分工亚群，异质性可成为群体策略|选择与诱导在快照中难区分，培养环境和瓶颈会重塑转换率
稀疏动力学发现生命方程|Sparse Discovery of Biological Dynamics|Brunton, Proctor & Kutz, Proceedings of the National Academy of Sciences 113, 3932–3937 (2016), doi:10.1073/pnas.1517384113|稀疏候选库能否从短噪声生物序列恢复真实机制|弱形式与贝叶斯SINDy继续改善不规则采样|在候选非线性项中稀疏选择微分方程|稀疏识别可把时间序列转成可读动力方程，为调控和种群模型提供数据驱动假设生成器|候选库决定可发现机制且数值微分放大噪声，稀疏性不是生物真实性保证
RNA速度|RNA Velocity|La Manno et al., Nature 560, 494–498 (2018), doi:10.1038/s41586-018-0414-6|剪接与未剪接RNA能否从快照推断细胞未来状态|动力学和代谢标记版本继续修正稳态假设|用转录剪接动力估计单细胞状态导数|RNA速度为单细胞图谱增加局部方向，帮助重建分化轨迹而非只聚类静态状态|基因特异动力与非稳态会反转箭头，低维投影中的流线不是谱系直接观测
单细胞扰动预测|Single-Cell Perturbation Prediction|Lotfollahi et al., Molecular Systems Biology 15, e8746 (2019), doi:10.15252/msb.20188746|潜变量模型能否预测未见细胞类型对药物或基因扰动的响应|大规模Perturb-seq继续建立组合扰动基准|分离细胞状态与扰动方向进行条件生成|单细胞扰动模型把跨细胞类型反应预测变成可验证任务，为实验优先级提供工具|批次和细胞组成偏移会被模型当作扰动，平均表达命中可能遗漏稀有毒性亚群
通用微分方程|Universal Differential Equations|Rackauckas et al., Universal Differential Equations for Scientific Machine Learning (2020), arXiv:2001.04385|未知生物过程能否由神经组件补全而不破坏已知机制|2025综述推进可辨识性、软件和生物案例比较|把可解释微分方程与可学习函数组合|通用微分方程让已知守恒或反应结构保留在模型中，仅用学习器表达未知项，兼顾预测与机制发现|灵活未知项会吸收参数误差和观测偏差，预测准确仍可能对应错误机制分解
器官芯片与多尺度模型|Organ-on-Chip Multiscale Modelling|Low et al., Nature Reviews Drug Discovery 20, 345–361 (2021), doi:10.1038/s41573-020-0079-3|微流控器官模型能否把细胞反应外推到人体剂量与长期病程|器官串联和药代模型继续连接体外与临床|耦合流体、传质、细胞力学与药物反应|器官芯片为数学生物模型提供可控边界和实时观测，使人源组织机制可在动物之外测试|芯片尺度、材料吸附和缺失免疫内分泌会限制外推，结构逼真不等于系统完整
空间转录组反应扩散|Spatial Transcriptomic Modelling|Ståhl et al., Science 353, 78–82 (2016), doi:10.1126/science.aaf2403|空间表达图能否识别细胞交流方向和扩散长度|单细胞分辨空间多组学继续配合配体受体扰动|把基因表达与组织坐标共同建模|空间转录组恢复被解离测序丢失的邻域，使形态、细胞类型和局部信号可在同一坐标分析|捕获点混合、组织切片和配体数据库会制造邻接相关，空间共现不等于信号传递
肿瘤适应性治疗|Adaptive Cancer Therapy|Zhang et al., Nature Communications 8, 1816 (2017), doi:10.1038/s41467-017-01968-5|维持敏感细胞竞争能否延缓耐药并改善患者结局|前瞻试验继续比较个体阈值和标准最大耐受剂量|依据肿瘤负荷反馈开停药而非持续强杀伤|适应性治疗把生态竞争转成临床控制策略，早期研究显示部分患者可延长控制并减少用药|肿瘤标志物未必代表克隆构成，停药阈值和空间异质使简单反馈难以通用
免疫数字孪生|Immune Digital Twins|National Academies and systems-immunology digital-twin roadmaps (2023–2025)|个体免疫模型能否前瞻预测疫苗、感染或免疫治疗响应|2025项目强调多尺度校准和连续更新|以纵向个体数据更新可干预免疫模型|免疫数字孪生把群体知识、机制方程和患者观测合成可更新预测体，目标是比较治疗情景|免疫状态不可完全观测且数据频率低，后验拟合成功不保证下一次干预预测
可辨识性与实用可识别参数|Biological Model Identifiability|Villaverde et al., Bioinformatics 35, 830–838 (2019), doi:10.1093/bioinformatics/bty703|复杂模型参数是否能由现有实验唯一或稳定估计|最优实验设计继续针对结构与实用不可辨识|在拟合前分析参数到观测的可逆性|可辨识性分析把无法由数据区分的参数组合提前暴露，避免用任意最优值叙述生物机制|局部检验会遗漏全局对称且真实噪声破坏理论可辨识，需与轮廓似然和新实验结合
生物基础模型与扰动|Foundation Models for Biology|Theodoris et al., Nature 618, 616–624 (2023), doi:10.1038/s41586-023-06139-9|大规模预训练表达嵌入能否跨组织和疾病预测因果扰动|2025基准转向零样本基因功能与组合干预|从海量单细胞数据学习可迁移状态表示|生物基础模型把分散图谱转成共享表征，可减少特定任务标注并提出候选基因网络|训练语料偏向常见组织且表达相似不等于功能相同，线性探针成绩不能替实验验证
通用微分方程生物评测|UDE Biological Benchmarking|Philipps et al., npj Systems Biology and Applications 11 (2025)|混合机制学习是否比纯机制或纯神经模型更可识别|2025综述系统比较实现、训练和生物用途|用多任务基准比较未知项恢复与外推|最新评测把通用微分方程的价值从单案例拟合推进到结构恢复、数据效率和外推的共同审计|不同求解器与正则会得到近似轨迹却不同未知项，机制结论需要独立干预数据
个体治疗前瞻闭环|Prospective Personalised-Treatment Loop|National Academies, Foundational Research Gaps and Future Directions for Digital Twins (2024)|数字孪生能否在治疗前锁定预测并随新数据校准|2025临床路线强调预注册决策阈值与安全回退|以滚动预测、实际干预和误差更新形成闭环|前瞻闭环要求模型在看见结果前给出治疗排序、置信区间和停机条件，再用真实反应更新个体状态|伦理限制和稀少反事实使模型难与医生选择分离，失败病例必须进入版本审计
数学生物学闭环验收|Mathematical-Biology Closed-Loop Acceptance|Philipps et al., npj Systems Biology and Applications 11 (2025)|生命模型能否经独立扰动、时间外推和机制替代共同验收|2025混合模型综述强调可辨识与实验设计|以留出干预、参数可辨识和预测校准验收模型|闭环验收要求公开观测模型、先验、参数相关、批次校正、替代机制和失败预测，拟合曲线只占证据的一部分|人体实验和长期谱系常不可得，多种机制可能保持等价，结论必须标注哪些参数不可识别
""",
)


add(
    589, "mathematical-finance", "数理金融", "数理、信息与计算主干 · 金融系统",
    "从高频点过程、系统性风险、流动性与最优执行、粗糙波动率、信用估值调整和金融网络到深度对冲、神经随机微分方程、气候压力、分布鲁棒组合与可审计交易控制，审计金融模型的风险边界。",
    "数理金融正在从封闭市场中的无套利定价，走向含交易摩擦、网络反馈、模型不确定性与机器学习策略的动态决策。速度和拟合从来不是最终标准；真正的难题是尾部、制度变化、市场冲击和参与者反应会在模型被部署后改写数据生成过程。",
    "数理金融成立的决定性机制，是让价格过程、交易摩擦、资金约束、模型风险和真实执行损益进入同一资本账，而不是把样本内收益、静态回测或风险中性价格当作可部署证据",
    "未来五年要看学习对冲能否跨制度与成本稳健，粗糙和神经波动模型能否通过尾部外推，气候风险能否进入可验证现金流，以及算法交易能否用真实冲击与失效机制验收",
    [
        "Gatheral, Jaisson & Rosenbaum, Quantitative Finance 18, 933--949 (2018), doi:10.1080/14697688.2017.1393551.",
        "Buehler et al., Quantitative Finance 19, 1271--1291 (2019), doi:10.1080/14697688.2019.1571683.",
        "Angelopoulos & Bates, Foundations and Trends in Machine Learning 16, 494--591 (2023), doi:10.1561/2200000101.",
        "Network for Greening the Financial System, climate scenarios and technical documentation (2024--2025).",
    ],
    r"""
高频交易霍克斯过程|Hawkes Processes in Finance|Bacry, Mastromatteo & Muzy, Market Microstructure and Liquidity 1, 1550005 (2015), doi:10.1142/S2382626615500057|订单事件的自激是否代表策略互动还是共同新闻冲击|非线性和有标记点过程继续分解订单簿反馈|用事件触发核描述交易到达的簇集与互激|霍克斯过程把成交、限价和取消的时间依赖写成可估计强度，可量化市场内生性和冲击衰减|核函数与基线不可唯一分解且时间戳同步会制造激励，拟合事件率不证明因果策略
系统性风险CoVaR|Conditional Value at Risk|Adrian & Brunnermeier, American Economic Review 106, 1705–1741 (2016), doi:10.1257/aer.20120555|机构个体安全是否会掩盖其对系统尾部的边际贡献|网络与宏观压力测试继续校正条件相关的非线性|比较系统在机构困境与正常状态下的尾部风险|CoVaR把风险从单机构损失扩展到条件系统损失，揭示低个体波动机构也可能具有高系统外部性|条件分位差受状态变量和内生杠杆影响，不是可直接相加的资本需求或因果损害
流动性与价格冲击|Market Liquidity and Price Impact|Obizhaeva & Wang, Journal of Financial Markets 16, 1–32 (2013), doi:10.1016/j.finmar.2012.09.001|订单簿韧性是否能预测大额交易的瞬时和永久冲击|瞬态冲击模型继续用高频执行数据校准|以动态供给曲线描述冲击与恢复|动态订单簿模型把执行成本与流动性恢复连接起来，说明切单速度必须随市场韧性优化|线性形状和稳定恢复率在压力期失效，估计冲击会与交易者选择相互内生
信用估值调整XVA|Counterparty Credit Valuation Adjustment|Burgard & Kjaer, Quantitative Finance 11, 1499–1510 (2011), doi:10.1080/14697688.2010.501262|无套利复制能否在融资、违约与抵押不完备时给出唯一调整|资本和保证金调整继续形成统一但机构特定的XVA账|把交易对手与自身违约写入复制组合|XVA框架将衍生品价格从理想无违约值扩展到信用、融资和抵押成本，迫使估值暴露资金边界|融资曲线、净额结算与回收假设因机构而异，同一合约不存在完全制度无关的XVA
金融网络传染|Financial Network Contagion|Acemoglu, Ozdaglar & Tahbaz-Salehi, American Economic Review 105, 564–608 (2015), doi:10.1257/aer.20130456|分散化何时从吸收小冲击转为放大大冲击|多层资产与支付网络继续进入压力测试|在债务网络中推导冲击规模与连接度的非单调关系|金融网络理论显示密集连接可分散小损失却扩散大冲击，系统稳定性不是连接越多越好|真实敞口不透明且处置规则会改变级联，静态网络难覆盖挤兑与共同资产抛售
签名方法与路径依赖|Signature Methods in Finance|Chevyrev & Kormilitzin, arXiv:1603.03788 and Applied Mathematics and Computation 2016|有限路径签名能否稳定表示不规则金融时间序列|深度签名继续服务波动率和执行策略|用迭代积分构造对路径重参数化稳健的特征|路径签名以系统层级编码顺序信息，可统一处理时间序列分类、控制和非马尔可夫依赖|截断阶数与时间通道设计决定表达，统计显著的签名项不自动对应经济机制
随机投资组合理论|Stochastic Portfolio Theory|Fernholz & Karatzas, Handbook of Numerical Analysis 15, 89–167 (2009)|不预测收益率能否仅凭市场权重结构获得相对套利|多样性加权与函数生成组合继续测试交易成本|用市场权重的几何与波动构造相对表现分解|随机投资组合理论把超额收益分成结构变化与交易生成项，不依赖逐资产期望收益预测|理论相对套利常需长时间和理想连续交易，实际换手、集中度和退市偏差会吞掉优势
高频波动率估计|High-Frequency Volatility Estimation|Aït-Sahalia & Jacod, High-Frequency Financial Econometrics, Princeton University Press (2014)|更高采样频率能否克服微观结构噪声和跳跃混淆|预平均与多尺度估计继续适配异步多资产数据|从日内收益分离连续方差、跳跃和噪声|高频计量把实现波动率与跳跃变成可检验对象，使风险模型使用日内信息而非只依赖日收益|报价反弹、异步交易和市场关闭使无限加密采样反而更偏，估计窗口必须匹配用途
粗糙波动率|Rough Volatility|Gatheral, Jaisson & Rosenbaum, Quantitative Finance 18, 933–949 (2018), doi:10.1080/14697688.2017.1393551|波动率短期粗糙性是真实记忆还是测量与聚合产物|粗糙Heston和微观结构极限继续连接期权面|用低Hurst分数过程描述对数波动率|粗糙波动率以少量结构同时拟合短期偏斜和时间序列粗糙性，挑战经典平滑随机波动率|Hurst估计受噪声和有限样本影响，风险中性校准成功不保证真实测度预测
深度对冲|Deep Hedging|Buehler et al., Quantitative Finance 19, 1271–1291 (2019), doi:10.1080/14697688.2019.1571683|神经策略能否在成本、约束和不可复制风险下优于经典对冲|分布外压力与风险偏好校准继续成为基准|直接优化含交易成本的终端损失风险|深度对冲把路径依赖、非线性成本和风险度量纳入策略训练，不再要求闭式复制|模拟器错误会被策略利用，样本内损失下降可能来自隐藏尾部或过度换手，必须真实回放
深度校准与代理定价|Deep Calibration|Horvath, Muguruza & Tomas, Risk and machine-learning calibration studies (2021)|神经代理能否加速模型校准而不平滑掉套利约束和尾部|可微定价器继续加入误差证书与无套利层|学习参数到期权价格面的快速映射|深度校准用离线模拟换取在线速度，使复杂随机模型可在实时风险系统中反复反演|训练参数盒外的市场面会产生无声外推，低均方价差不保证希腊值和尾部稳定
神经随机微分方程|Neural Stochastic Differential Equations|Kidger et al., Advances in Neural Information Processing Systems 34 (2021)|学习漂移扩散能否生成金融路径并保持无套利与统计尾部|可控神经微分方程继续连接不规则市场数据|以神经网络参数化连续时间随机动力|神经随机微分方程可学习灵活路径分布并自然处理不规则采样，为情景生成和衍生品建模提供统一接口|似然与对抗损失可忽略极端事件，连续模型也会掩盖跳跃、交易时段和制度断点
粗糙Heston特征函数|Rough Heston Model|El Euch & Rosenbaum, Mathematical Finance 29, 3–38 (2019), doi:10.1111/mafi.12173|非马尔可夫粗糙模型能否保持可计算期权定价|分数Riccati数值法继续提高稳定与速度|用分数Riccati方程获得粗糙随机波动率变换|粗糙Heston在保留杠杆效应和正方差的同时解释期限结构，建立微观粗糙与定价的可算桥梁|分数核造成长记忆计算成本且校准多峰，参数经济解释仍随市场窗口漂移
分布鲁棒投资组合|Distributionally Robust Portfolio Optimisation|Esfahani & Kuhn, Mathematical Programming 171, 115–166 (2018), doi:10.1007/s10107-017-1172-1|围绕经验分布的最坏情形优化能否减少估计误差而不过度保守|Wasserstein半径数据驱动选择继续进入多期组合|在概率分布邻域内优化最坏损失|分布鲁棒方法把模型不确定性显式转成可调半径，避免把有限样本经验分布当作未来真相|半径决定一切且时间依赖难被静态距离表示，保守收益下降需与真实危机保护比较
加密资产市场微结构|Crypto-Asset Market Microstructure|Makarov & Schoar, Journal of Financial Economics 135, 293–319 (2020), doi:10.1016/j.jfineco.2019.07.001|跨交易所价差是套利机会还是资本和结算摩擦的补偿|链上流、稳定币和永续合约继续进入联合分析|比较分割市场中的同步价格与资金流|加密市场展示无统一结算和资本约束下巨大持续价差，使无套利条件必须包含转账与对手风险|交易所数据质量、存活偏差和监管变化剧烈，历史价差机制难稳定外推
气候金融压力测试|Climate Financial Stress Testing|Network for Greening the Financial System, Climate Scenarios technical documentation (2024)|长期情景能否转化为可验证的短期违约、资产价格和现金流冲击|2025情景继续更新转型路径与物理风险粒度|把温度政策和宏观路径映射到金融敞口|气候压力测试把慢变量与资产负债表连接，迫使机构披露路径依赖与行业集中风险|几十年情景不可用历史频率校准且企业适应内生，损失数值是条件情景而非概率预测
共形风险界限|Conformal Risk Bounds|Angelopoulos & Bates, Foundations and Trends in Machine Learning 16, 494–591 (2023), doi:10.1561/2200000101|有限样本覆盖保证能否在金融非交换序列中保持|在线和加权共形继续处理分布漂移|以校准残差给预测区间有限样本覆盖|共形方法为黑箱风险预测增加分布较弱的覆盖审计，可直接检查区间失配|经典保证依赖交换性，市场聚集波动和制度断点会使名义覆盖失效且不能保证尾部损失大小
强化学习最优执行|Reinforcement Learning for Execution|Nevmyvaka, Feng & Kearns, International Conference on Machine Learning (2006) and 2024 benchmarks|策略能否在自反馈市场中学到低冲击执行而非利用模拟漏洞|离线强化学习和反事实订单簿继续压缩部署风险|以成交成本和未完成风险训练序贯下单|强化学习可随订单簿状态动态调整切单，比固定时间表表达更多状态依赖|历史数据只有行为策略结果且执行改变市场，离线收益存在不可识别反事实和严重选择偏差
跨制度回测审计|Cross-Regime Backtest Audit|Bailey et al., Journal of Computational Finance 20, 39–69 (2016), probability of backtest overfitting|多次试验中的最佳策略是否只是数据挖掘赢家|选择偏差校正继续结合滚动与市场冲击仿真|统计研究者自由度并保留未见制度测试|回测过拟合审计把试过多少版本、参数和样本切分纳入显著性，纠正只展示冠军曲线|未记录的研究尝试无法补算且未来制度仍未知，校正通过不是盈利保证
数理金融闭环验收|Mathematical-Finance Closed-Loop Acceptance|Buehler et al., Quantitative Finance 19, 1271–1291 (2019)|模型能否用预注册成本、资本占用和尾部失效进行实盘影子验收|2025金融AI治理强调版本、数据和人工回退|以样本外损益、风险预算和市场冲击共同验收|闭环验收要求锁定训练截止、费用、滑点、融资、容量、止损与模型变更，再用影子执行和压力期逐笔复核|真实部署会改变市场且极端事件样本稀少，任何通过结果都需保留资本缓冲与停机机制
""",
)


add(
    590, "uncertainty-quantification", "不确定性量化", "数理、信息与计算主干 · 可信计算",
    "从随机配置、多层蒙特卡洛、稀疏多项式混沌、贝叶斯反演、主动子空间与整体敏感性到多保真推断、概率数值、深度集成、共形预测、稀有事件和数字孪生校准，审计不确定性如何进入决策。",
    "不确定性量化不是给确定性曲线加一条误差带，而是追问输入、模型结构、数值离散、观测噪声和分布漂移如何分别影响输出与行动。若把所有误差混成单一方差，或只在训练分布校准覆盖率，精致的区间仍可系统失真。",
    "不确定性量化成立的决定性机制，是让不确定来源、传播算法、校准证据和决策损失在同一概率与适用域账中闭合，而不是把更多样本、贝叶斯标签或窄区间当作可信证明",
    "未来五年要看稀有事件能否获得可审计概率，多保真和神经算子能否给出离散与模型误差证书，共形方法能否适应漂移，以及数字孪生能否在连续更新中保持校准",
    [
        "Oates & Sullivan, SIAM Review 61, 756--789 (2019), doi:10.1137/17M1139357.",
        "Peherstorfer, Willcox & Gunzburger, SIAM Review 60, 550--591 (2018), doi:10.1137/15M1046472.",
        "Angelopoulos & Bates, Foundations and Trends in Machine Learning 16, 494--591 (2023), doi:10.1561/2200000101.",
        "SIAM/ASA Journal on Uncertainty Quantification, 2024--2025 benchmark and digital-twin studies.",
    ],
    r"""
随机配置方法|Stochastic Collocation|Nobile, Tempone & Webster, SIAM Journal on Numerical Analysis 46, 2309–2345 (2008), doi:10.1137/060663660|非侵入采样能否在高维随机输入下避免组合爆炸|自适应稀疏网格继续利用各向异性和光滑性|在参数空间插值确定性求解器输出|随机配置无需修改主求解器即可获得响应面和统计量，适合复用成熟仿真软件|维数和非光滑响应会摧毁谱收敛，节点精确不代表输入分布真实
多层蒙特卡洛|Multilevel Monte Carlo|Giles, Operations Research 56, 607–617 (2008), doi:10.1287/opre.1070.0496|粗细模型差值能否以更低成本达到同一均方误差|自适应层级与随机偏微分方程继续扩大适用范围|用大量粗样本和少量细样本估计望远镜和|多层蒙特卡洛把计算预算集中在便宜层级，并用强耦合差值控制离散偏差|层间相关不足或单样本重尾会失去复杂度优势，理论速率需由先导样本验证
贝叶斯反问题|Bayesian Inverse Problems|Stuart, Acta Numerica 19, 451–559 (2010), doi:10.1017/S0962492910000061|无限维先验与似然能否给出网格一致的后验|函数空间MCMC与变分推断继续处理大规模PDE|以概率测度表述参数反演和不适定性|贝叶斯反演把数据噪声与先验知识传播到参数和预测后验，避免只给单个最优解|先验和误差模型会主导弱识别方向，后验窄不等于模型结构正确
稀疏多项式混沌|Sparse Polynomial Chaos|Blatman & Sudret, Journal of Computational Physics 230, 2345–2367 (2011), doi:10.1016/j.jcp.2010.12.021|稀疏回归能否在有限仿真下找到真正重要的高阶交互|压缩感知和自适应基选择继续面向高维模型|从候选正交多项式中稀疏选择响应展开|稀疏混沌显著减少昂贵模型的采样数，并直接给出矩和敏感性指标|非光滑、多峰与相关输入会破坏基正交，交叉验证误差小也可能错估尾部
模型校准与差异项|Calibration with Model Discrepancy|Higdon et al., Journal of the American Statistical Association 103, 570–583 (2008), doi:10.1198/016214507000000888|参数误差与模型结构差异能否由同一观测区分|正交差异和模块化贝叶斯继续缓解不可辨识|在模拟器之外显式加入现实差异过程|差异项承认再好参数也无法让不完备模型等于现实，防止校准参数吸收全部结构错误|灵活差异会与参数混淆，使校准值失去物理意义，需新实验或约束分离
主动子空间|Active Subspaces|Constantine, Active Subspaces, SIAM (2015), doi:10.1137/1.9781611973860|输出是否主要沿少数输入线性组合变化|局部和非线性主动流形继续处理多机制响应|用梯度协方差寻找重要参数方向|主动子空间可将高维参数压缩成少数可解释方向，加速响应面和可视化|特征值间隙可能由采样误差造成，弯曲或分区结构不能被全局线性方向捕获
多项式维度分解|Polynomial Dimensional Decomposition|Rahman, Computer Methods in Applied Mechanics and Engineering 197, 103–127 (2008), doi:10.1016/j.cma.2007.07.026|低阶交互截断能否覆盖非线性高维系统|自适应交互筛选继续与可靠度分析结合|按输入子集逐阶分解响应函数|维度分解把主效应和交互效应层级化，使高维不确定传播可按贡献截断|强高阶协同或不连续失效面会让低阶截断偏乐观，截断误差必须单独估计
整体敏感性Sobol指标|Global Sensitivity Analysis|Saltelli et al., Computer Physics Communications 181, 259–270 (2010), doi:10.1016/j.cpc.2009.09.018|方差贡献能否在相关输入和重尾输出下保持可解释|Shapley效应与目标敏感性继续扩展非独立参数|分解输出方差为单变量与交互贡献|Sobol指标把局部导数提升为全输入域贡献，可指导数据收集和模型简化|方差不是所有决策的损失函数，相关输入下传统分解不唯一且估计成本高
集合卡尔曼反演|Ensemble Kalman Inversion|Iglesias, Law & Stuart, Inverse Problems 29, 045001 (2013), doi:10.1088/0266-5611/29/4/045001|小集合高斯更新能否在非线性多峰反问题中可靠收敛|局部化、退火和约束版本继续进入PDE校准|用集合协方差迭代更新未知参数|集合卡尔曼反演只需前向模型并可并行，成为大规模校准的实用近似|集合张成子空间限制解且会塌缩，多峰后验被单一均值协方差掩盖
多保真蒙特卡洛|Multifidelity Monte Carlo|Peherstorfer, Willcox & Gunzburger, SIAM Review 60, 550–591 (2018), doi:10.1137/15M1046472|便宜低保真模型何时真正减少高保真样本而不引入偏差|在线模型选择继续按相关性与成本分配预算|用控制变量组合多种成本和精度模型|多保真方法把经验模型、降阶和细网格纳入统一估计器，以相关性换计算预算|低保真相关性会随参数区域改变，错误成本模型可让最优分配比单保真更差
概率数值方法|Probabilistic Numerics|Oates & Sullivan, SIAM Review 61, 756–789 (2019), doi:10.1137/17M1139357|把数值误差表示为概率是否提供可校准不确定性而非主观包装|概率积分与概率ODE继续比较频率覆盖和决策收益|对积分、线性代数和微分方程解赋后验|概率数值让有限计算产生的离散误差进入后续推断，可避免把近似解当成精确数据|先验选择和计算预算未必对应真实误差分布，可信区间需与网格加密事实校准
深度集成不确定性|Deep Ensembles|Lakshminarayanan, Pritzel & Blundell, Advances in Neural Information Processing Systems 30 (2017)|多次训练差异能否代表认知不确定而非仅优化随机性|分布外基准继续比较集成与贝叶斯近似|用独立初始化模型的预测分布估计置信|深度集成简单而常具强校准和分布外检测表现，成为神经预测不确定性的实用基线|成员共享数据与架构偏差，彼此一致可能只是共同盲点，集成方差不是完整后验
稀有事件自适应分裂|Adaptive Multilevel Splitting|Cérou & Guyader, Stochastic Analysis and Applications 25, 417–443 (2007), doi:10.1080/07362990601139669|复制接近失效的轨迹能否无偏估计极小概率|反应坐标学习继续用于气候、分子和可靠度|逐层筛选并复制向稀有集合推进的样本|自适应分裂将预算集中到通往失效的路径，比直接蒙特卡洛更高效估计极端概率|反应坐标选错会困在局部通道，方差估计和独立性需专门审计
可靠度子集模拟|Subset Simulation|Au & Beck, Probabilistic Engineering Mechanics 16, 263–277 (2001), doi:10.1016/S0266-8920(01)00019-4|把小概率拆成条件概率链能否稳定覆盖多条失效路径|自适应MCMC和代理边界继续减少昂贵评估|用逐级阈值把罕见失效转成常见条件事件|子集模拟使工程失效概率可由一系列可采样事件估计，兼顾概率与失效样本发现|阈值、马尔可夫相关和多模态边界会偏置结果，单次估计需重复链与路径诊断
共形预测|Conformal Prediction|Angelopoulos & Bates, Foundations and Trends in Machine Learning 16, 494–591 (2023), doi:10.1561/2200000101|分布无关覆盖能否在时空相关与漂移数据中保持|在线、局部和风险控制共形继续扩展非交换场景|用校准集排名把任意预测器包装成区间|共形预测提供有限样本边际覆盖，并把区间是否达标变成直接可验收频率|覆盖是平均而非每子群条件保证，分布漂移和自适应使用会破坏经典结论
多模型结构不确定性|Model-Form Uncertainty|National Research Council, Assessing the Reliability of Complex Models (2012)|多种同样拟合模型如何共同进入预测而非由研究者主观择一|模型集合与贝叶斯模型平均继续纳入结构差异|比较替代方程、边界和闭合方案的预测分散|模型结构审计迫使团队展示方程选择对结果的影响，不把参数区间冒充全部不确定性|候选集合仍可能遗漏共同错误，模型平均权重也依赖历史适用域
神经算子误差证书|Neural-Operator Error Certification|Kovachki et al., Journal of Machine Learning Research 24, 1–97 (2023)|快速算子代理能否同时报告离散、近似和分布外误差|2025研究引入残差界、校准集和自适应回退|用物理残差与高保真抽查约束代理不确定性|误差证书把代理速度与可接受误差阈值连接，使模型可在超界时回退真实求解器|残差小不必推出目标量误差小，边界与系数超训练域时证书常失效
数字孪生连续贝叶斯更新|Digital-Twin Bayesian Updating|National Academies, Foundational Research Gaps and Future Directions for Digital Twins (2024)|连续同化能否在传感漂移和模型老化下保持校准|2025研究强调版本化后验和异常回退|随运行观测滚动更新状态参数与预测区间|贝叶斯数字孪生让不确定性随新证据收缩或扩张，并把维护决策与失效概率连接|重复使用相关数据会过度自信，传感器故障和结构变更需显式变点而非强行更新
决策导向不确定性|Decision-Focused Uncertainty Quantification|Howard, Matheson and modern value-of-information frameworks (2006–2025)|更精确概率是否真的改变行动和期望损失|2025研究把校准、效用和信息价值并列评测|按决策敏感方向分配模拟与实验预算|决策导向方法不追求所有参数同样精确，而优先降低会改变选择的关键不确定性|效用与风险偏好若设错，精确概率也会优化错误目标，公平与安全约束需独立写入
不确定性量化闭环验收|Uncertainty-Quantification Closed-Loop Acceptance|Oates & Sullivan, SIAM Review 61, 756–789 (2019)|区间与失效概率能否经时间外、子群和决策结果共同验收|2025可信计算强调覆盖、尖锐度与回退机制|以来源分解、校准曲线和决策损失验收不确定性|闭环验收要求分别报告输入、模型、离散、数据与漂移不确定性，并在独立时段检查覆盖和错误代价|真正罕见事件没有足够频率验证，尾部结论必须保留先验敏感性与压力情景
""",
)


add(
    591, "inverse-problems-computational-imaging", "反问题与计算成像", "数理、信息与计算主干 · 反演与成像",
    "从压缩感知MRI、相位恢复、叠层衍射、光声成像、单像素相机、冷冻电镜和盲反卷积到即插即用先验、深度图像先验、学习迭代、扩散后验、语义正则和可验证成像，审计不可见对象如何被重建。",
    "反问题与计算成像把硬件、物理传播和算法共同视为测量系统。学习方法显著提升速度和视觉质量，也放大了新的风险：网络可能填入训练语料中常见却未被测量支持的结构，而感知指标与临床、科学任务并不等价。",
    "反问题与计算成像成立的决定性机制，是让测量算子、噪声、先验、算法不稳定与任务真值在同一证据链中闭合，而不是把清晰图像、平均指标或网络置信当作对象真实存在的证明",
    "未来五年要看生成先验能否给出数据一致和幻觉界限，计算显微能否联合校准硬件，临床成像能否用病灶级终点验收，以及反演模型能否在算子漂移时自动回退",
    [
        "Antun et al., Proceedings of the National Academy of Sciences 117, 30088--30095 (2020), doi:10.1073/pnas.1907377117.",
        "Zhang et al., Nature Communications 15 (2024), semantic regularization for inverse problems.",
        "Chung et al., International Conference on Learning Representations (2023), diffusion posterior sampling.",
        "Ongie et al., IEEE Journal on Selected Areas in Information Theory 1, 39--56 (2020), doi:10.1109/JSAIT.2020.2991565.",
    ],
    r"""
压缩感知MRI|Compressed-Sensing MRI|Lustig, Donoho & Pauly, Magnetic Resonance in Medicine 58, 1182–1195 (2007), doi:10.1002/mrm.21391|稀疏先验能否从欠采样频域数据恢复诊断细节|并行成像与学习先验继续在扫描时间和稳健间权衡|用非相干采样和稀疏正则重建图像|压缩感知MRI把扫描加速转成可证明的欠采样反问题，推动随机采样与迭代重建进入临床|真实解剖不严格稀疏且运动会破坏测量模型，平均清晰度可能掩盖小病灶丢失
相位提升|PhaseLift|Candès, Strohmer & Voroninski, Communications on Pure and Applied Mathematics 66, 1241–1274 (2013), doi:10.1002/cpa.21432|丢失相位的二次测量能否通过凸提升唯一恢复信号|非凸梯度法继续降低大规模内存与采样|把二次相位恢复提升为低秩半定规划|PhaseLift给出随机测量下精确恢复保证，使相位恢复从启发式迭代进入凸几何|提升维度过高且实验算子不满足理想随机性，理论唯一性不等于噪声稳健
叠层衍射成像|Ptychographic Imaging|Thibault et al., Science 321, 379–382 (2008), doi:10.1126/science.1158573|重叠扫描能否同时恢复样品复振幅与探针误差|多模态和在线叠层算法继续推进同步辐射成像|利用相邻照明重叠提供相位冗余|叠层成像以扫描重叠补回衍射相位，在无透镜条件下获得高分辨复图像|位置漂移、部分相干和探针变化会产生结构伪影，算法收敛不证明联合校准正确
光声层析成像|Photoacoustic Tomography|Wang & Hu, Science 335, 1458–1462 (2012), doi:10.1126/science.1216210|光吸收产生的声波能否在散射组织中定量反演功能信息|多谱与深层光声继续校正声速和光通量|以光激发声探测结合光学对比和超声深度|光声成像绕过纯光学深层散射，以血红蛋白等吸收对比进行高分辨组织成像|定量浓度受未知光通量和声速影响，多谱解混会把模型误差当作生化变化
冷冻电镜直接探测|Direct-Electron Cryo-EM|Bai et al., eLife 2, e00461 (2013), doi:10.7554/eLife.00461|低剂量噪声投影能否重建连续构象而非单一平均结构|单粒子异质重建继续连接构象动力学|用直接电子探测和运动校正提高低剂量信噪比|直接探测器与算法联合推动近原子分辨冷冻电镜，使无需结晶的蛋白复合体结构成为常规目标|粒子挑选、取向偏好和构象分类会强化先验，分辨率数字不能保证局部结构正确
随机光学重建显微|Stochastic Optical Reconstruction Microscopy|Rust, Bates & Zhuang, Nature Methods 3, 793–795 (2006), doi:10.1038/nmeth929|随机激活定位能否突破衍射极限并保持分子计数|三维多色和活细胞超分辨继续修正闪烁动力|逐批激活荧光分子并以质心定位累积图像|STORM利用时间稀疏把重叠点扩散函数分离，实现远低于衍射极限的定位图|定位精度不等于结构分辨率，标记尺寸、闪烁和漂白会产生缺失或重复分子
单像素压缩相机|Single-Pixel Camera|Duarte et al., IEEE Signal Processing Magazine 25, 83–91 (2008), doi:10.1109/MSP.2007.914730|无阵列探测器能否凭编码测量恢复高维场景|红外高光谱与太赫兹系统继续联合设计掩膜|用空间光调制器获取随机投影并稀疏重建|单像素相机证明传感与压缩可同时完成，在昂贵或不可用阵列波段尤具价值|逐次图案易受场景运动和光通量限制，稀疏模型与校准误差决定真实分辨率
盲反卷积|Blind Deconvolution|Ahmed, Recht & Romberg, IEEE Transactions on Information Theory 60, 1711–1732 (2014), doi:10.1109/TIT.2013.2293772|未知信号与未知模糊核能否在尺度歧义之外稳定分离|结构化非凸和自监督方法继续处理真实退化|将双线性卷积提升为低秩矩阵恢复|盲反卷积理论给出特定子空间与随机条件下的可恢复性，明确何时联合估计不是纯猜测|自然图像与相机核未必满足独立随机条件，先验错误会把纹理吸进模糊核
傅里叶叠层显微|Fourier Ptychographic Microscopy|Zheng, Horstmeyer & Yang, Nature Photonics 7, 739–745 (2013), doi:10.1038/nphoton.2013.187|多角度低分辨图能否合成大视场高数值孔径并联合估计像差|计算照明继续扩展三维和无标记显微|在傅里叶域拼接不同照明角的频谱|傅里叶叠层用廉价LED阵列与相位恢复获得大视场高分辨，把光学设计转成软硬件协同|照明位置、强度和样品厚度偏差会产生重复伪影，薄样品模型限制三维组织
即插即用先验|Plug-and-Play Priors|Venkatakrishnan, Bouman & Wohlberg, IEEE GlobalSIP (2013)|任意去噪器能否作为先验而仍保证迭代收敛和可解释目标|平均算子与共识平衡继续建立理论条件|把成熟去噪器嵌入优化的近端步骤|即插即用方法让图像先验与测量模型模块化，可在不显式写正则函数时复用强去噪器|去噪器未必对应概率先验且可能违反非扩张条件，固定点存在不等于统计正确
深度图像先验|Deep Image Prior|Ulyanov, Vedaldi & Lempitsky, IEEE Conference on Computer Vision and Pattern Recognition (2018)|未训练卷积网络的结构偏好能否充当图像先验|早停与贝叶斯版本继续处理过拟合噪声|直接优化随机输入网络使输出匹配单幅测量|深度图像先验显示网络架构本身偏向自然图像，可无外部数据完成去噪、修补和超分辨|训练过久会拟合噪声且架构偏好并非通用，早停常依赖未知真值或经验
学习原始对偶重建|Learned Primal-Dual Reconstruction|Adler & Öktem, IEEE Transactions on Medical Imaging 37, 1322–1332 (2018), doi:10.1109/TMI.2018.2799231|把迭代更新学出来能否保持测量一致和跨设备稳定|模型展开继续加入算子变化与不确定输出|在原始和对偶空间交替学习重建更新|学习原始对偶保留前向与伴随算子，同时让网络学习优化步骤，兼顾物理结构和数据性能|训练几何固定时会记住设备分布，换扫描协议或病种后细节恢复可能无声失效
开放MRI重建基准|fastMRI Benchmark|Zbontar et al., arXiv:1811.08839 and Radiology: Artificial Intelligence 2, e190007 (2020)|统一数据集能否让重建指标对应放射诊断安全|多线圈原始数据与临床读片继续扩展挑战|公开大规模k空间数据和标准欠采样任务|fastMRI把学习重建从小型私有案例推进到可复核基准，促进模型、速度和采样比较|数据来自有限机构和协议，SSIM排名与病灶检出并不一一对应且挑战会被反复调参
神经辐射场|Neural Radiance Fields|Mildenhall et al., European Conference on Computer Vision (2020), doi:10.1007/978-3-030-58452-8_24|稀疏视角能否恢复连续场景而不生成未观测几何|快速、动态和可编辑NeRF继续扩展计算摄影|用神经场表示空间位置方向到颜色密度映射|NeRF以体渲染和多视图一致训练实现新视角合成，统一了连续三维表示与图像形成|镜面、动态物体和相机位姿误差会形成漂浮伪影，逼真视角不等于度量几何准确
不稳定性与幻觉审计|Instability and Hallucination Audit|Antun et al., Proceedings of the National Academy of Sciences 117, 30088–30095 (2020), doi:10.1073/pnas.1907377117|学习重建能否在微小输入扰动下删除或制造关键结构|对抗、分布外与病灶插入测试继续进入医学基准|用构造扰动系统比较神经与经典重建稳定性|稳定性研究证明若干深度重建可对极小测量变化产生巨大图像差异，并遗漏稀有细节|特定攻击不代表所有临床噪声，但平均测试集成功也不能否定可构造的严重失败
分数扩散后验采样|Diffusion Posterior Sampling|Chung et al., International Conference on Learning Representations (2023)|扩散生成先验能否在强欠定问题中保留数据证据而不想象细节|条件扩散继续加入精确似然和不确定性校准|在逆扩散过程中用测量梯度引导后验样本|扩散后验采样可从复杂自然图像先验产生多种与测量相容的解，把单图重建扩成后验近似|近似引导并非精确后验，样本多样性可能低估结构歧义且生成语义会盖过弱测量
得分模型反问题|Score-Based Inverse Solvers|Song et al., International Conference on Learning Representations (2021)|学习数据分布得分能否跨算子复用并量化多解性|扩散桥和数据一致采样继续减少昂贵迭代|用反向随机微分方程与测量似然联合采样|得分模型把一个无条件生成先验用于去模糊、超分辨和修补等多种算子，提供统一生成式反演|训练分布与科学对象错配时会生成常见外观，噪声日程和似然尺度强烈影响结果
语义正则反问题|Semantic Regularisation for Inverse Problems|Zhang et al., Nature Communications 15 (2024)|高级语义约束能否在低信噪测量中提高任务相关恢复又不注入偏见|2025研究继续比较语义先验与像素数据一致|把预训练表征的语义距离加入反演目标|语义正则可在传统像素先验失效时保留对象级结构，使重建更贴近下游识别需求|预训练标签和文化偏差会进入答案，语义合理不代表测量支持，科学成像尤其需谨慎
计算光刻逆设计|Computational Lithography Inverse Design|Molesky et al., Nature Photonics 12, 659–670 (2018), doi:10.1038/s41566-018-0246-9|像素级光学逆设计能否在制造误差和多波长下稳定实现|2025可微光刻与神经代理继续压缩掩模优化时间|通过伴随梯度反演纳米结构和光场目标|逆设计将纳米光学器件从参数扫描推进到数百万自由度优化，可发现非直觉结构|名义最优对线宽、材料色散和刻蚀偏差敏感，仿真目标命中必须经实物计量
计算成像闭环验收|Computational-Imaging Closed-Loop Acceptance|Antun et al., Proceedings of the National Academy of Sciences 117, 30088–30095 (2020)|重建能否经原始测量、隐藏目标和任务终点共同验收|2025基准强调算子漂移、幻觉和校准不确定性|以数据一致、病灶插入、扰动稳定和盲读验收|闭环验收要求保存原始测量与校准，预注册病灶或科学任务，在未见设备上比较经典基线并标注生成内容|真实对象的完整真值常不可得，任何视觉提升都需保留原始数据回看和失败回退
""",
)


add(
    592, "scientific-machine-learning", "科学机器学习", "数理、信息与计算主干 · 科学智能",
    "从降阶基、动态模态分解、潜在力高斯过程、算子推断和稀疏方程发现到神经常微分方程、物理信息网络、通用微分方程、DeepONet、傅里叶神经算子、天气基础模型与自主科学代理，审计学习如何进入科学计算。",
    "科学机器学习的价值不在于把每个求解器换成神经网络，而在于选择哪些结构必须保留、哪些闭合可由数据学习、哪些误差必须显式报告。跨网格速度纪录很诱人，但若模型不守恒、不能在新边界上稳定或无法察觉分布外输入，快速答案只会更快扩散错误。",
    "科学机器学习成立的决定性机制，是让方程结构、训练数据、离散误差、外推稳定和科学发现的可证伪性在同一验证链中闭合，而不是把训练损失、加速倍数或单基准排名当作科学可信",
    "未来五年要看神经算子能否获得可计算误差界，基础模型能否跨物理域迁移，混合模型能否恢复可辨识机制，科学代理能否留下可复现实验轨迹，以及部署系统能否在超域时自动回退",
    [
        "Karniadakis et al., Nature Reviews Physics 3, 422--440 (2021), doi:10.1038/s42254-021-00314-5.",
        "Kovachki et al., Journal of Machine Learning Research 24, 1--97 (2023).",
        "Rabeh et al., Communications Engineering 4 (2025), scientific machine-learning benchmark.",
        "Moon et al., npj Computational Materials 11 (2025), physics-informed neural operators.",
    ],
    r"""
离散经验插值降阶|Discrete Empirical Interpolation Method|Chaturantabut & Sorensen, SIAM Journal on Scientific Computing 32, 2737–2764 (2010), doi:10.1137/090766498|非线性降阶能否避免仍在全维评估非线性项|超降阶与自适应基继续处理参数化系统|用选定空间点近似非线性项并投影|DEIM使非线性降阶模型的在线成本不再依赖全维网格，为多次查询和控制提供关键加速|选点与训练快照不足会造成不稳定，低状态误差不保证守恒或长期轨迹
动态模态分解|Dynamic Mode Decomposition|Schmid, Journal of Fluid Mechanics 656, 5–28 (2010), doi:10.1017/S0022112010001217|数据模态能否对应真实动力算子而非采样窗口相关模式|多分辨与控制DMD继续分析非平稳系统|从连续快照拟合线性演化特征模态|DMD把高维时空数据分成具有频率和增长率的相干结构，连接流体分析与Koopman观点|噪声、时间步和截断会移动特征值，线性模态解释不等于非线性因果机制
潜在力高斯过程|Latent Force Models|Álvarez, Luengo & Lawrence, IEEE Transactions on Pattern Analysis and Machine Intelligence 35, 2693–2705 (2013), doi:10.1109/TPAMI.2013.86|未知外力能否通过物理响应核从稀疏观测中识别|多输出与非线性潜在力继续连接生理和工程数据|把线性微分方程Green函数嵌入高斯过程核|潜在力模型保留已知动力响应，同时以概率过程表示未知驱动，给出预测与不确定区间|核与物理参数会互相补偿，计算扩展困难且高斯假设会平滑突发事件
降阶基方法|Reduced-Basis Methods|Hesthaven, Rozza & Stamm, Certified Reduced Basis Methods for Parametrized Partial Differential Equations, Springer (2016)|少量快照空间能否覆盖高维参数和移动结构|局部基与误差估计继续处理冲击和几何变化|以离线高保真解构造在线低维近似|认证降阶基把快速查询与残差误差界结合，成为科学机器学习的重要可比较基线|Kolmogorov宽度衰减慢的平移与湍流问题需要大量基，认证常依赖昂贵稳定常数
算子推断|Operator Inference|Peherstorfer & Willcox, Computer Methods in Applied Mechanics and Engineering 306, 196–215 (2016), doi:10.1016/j.cma.2016.03.025|不访问全阶方程能否从状态快照恢复稳定降阶算子|结构保持与正则化算子推断继续扩展非侵入建模|在降阶坐标中回归线性二次动力算子|算子推断从数据重建可解释低阶动力，避免侵入修改遗留求解器并保留方程形式|导数估计和激励不足会使算子不可辨识，训练轨迹外可能出现能量爆炸
稀疏非线性动力发现|Sparse Identification of Nonlinear Dynamics|Brunton, Proctor & Kutz, Proceedings of the National Academy of Sciences 113, 3932–3937 (2016), doi:10.1073/pnas.1517384113|稀疏回归能否从噪声轨迹恢复正确控制方程|弱形式、贝叶斯和控制SINDy继续提高稳健性|在候选函数库中稀疏选择动力项|SINDy把黑箱预测转成可读方程，建立数据驱动发现与经典系统辨识之间的桥梁|候选库和阈值决定答案，相关项会互相替代且数值微分放大噪声
Koopman谱学习|Koopman Operator Learning|Williams, Kevrekidis & Rowley, Journal of Nonlinear Science 25, 1307–1346 (2015), doi:10.1007/s00332-015-9258-5|高维线性观测空间能否有限逼近非线性系统的全局动力|神经可观测与稳定谱约束继续发展|用扩展DMD近似观测函数上的线性算子|Koopman方法让非线性动力可通过线性谱工具分析，并支持预测和控制|有限字典不封闭且特征函数依赖数据覆盖，长期线性预测会积累相位与稳定性误差
方程无关多尺度计算|Equation-Free Computation|Kevrekidis et al., Communications in Mathematical Sciences 1, 715–762 (2003)|只有微观模拟器时能否执行宏观分岔和控制计算|提升限制算子继续与学习闭合耦合|短时微模拟估计未知宏观时间步进器|方程无关框架在没有显式宏观方程时仍执行粗粒度积分、定点和分岔分析，预示混合科学学习|慢变量若选错或尺度不分离，提升与限制会制造不存在的闭合动力
神经常微分方程|Neural Ordinary Differential Equations|Chen et al., Advances in Neural Information Processing Systems 31 (2018)|连续深度模型能否从不规则观测学习稳定动力并可逆传播梯度|稳定积分与事件神经ODE继续扩展时序建模|以神经网络定义连续时间状态导数|神经ODE把网络层深度转成数值积分，允许自适应计算和连续时间潜变量|伴随梯度与前向数值解可能不一致，灵活向量场会拟合插值却在长期外推发散
物理信息神经网络|Physics-Informed Neural Networks|Raissi, Perdikaris & Karniadakis, Journal of Computational Physics 378, 686–707 (2019), doi:10.1016/j.jcp.2018.10.045|偏微分残差训练能否在多尺度刚性与复杂边界上替代网格求解|自适应采样和域分解继续处理训练病态|把方程与边界残差加入神经网络损失|PINN在稀疏数据与方程约束间统一前向和反问题，降低对标注场的依赖|损失尺度和谱偏置会漏掉尖层高频，残差点小不代表全域解误差小
通用微分方程|Universal Differential Equations|Rackauckas et al., arXiv:2001.04385 (2020)|未知闭合能否由可学习组件补全且仍保持参数可辨识|2025系统生物综述继续比较结构恢复与预测|在已知方程中嵌入神经或非参数未知项|UDE把机制方程与通用逼近器组成单一可微模型，使未知物理可从数据中估计|学习项会吸收边界、参数和求解误差，预测命中不保证发现了真实闭合
DeepONet算子学习|Deep Operator Network|Lu et al., Nature Machine Intelligence 3, 218–229 (2021), doi:10.1038/s42256-021-00302-5|有限传感点能否学习函数到函数映射并跨输入实例泛化|多输入与多保真DeepONet继续扩展复杂算子|用分支网络编码输入函数并用主干网络编码坐标|DeepONet将监督学习对象从有限维标签提升为算子，可一次训练后快速求解整族PDE|传感布局和训练函数分布决定泛化，连续算子表述不自动消除离散误差
傅里叶神经算子|Fourier Neural Operator|Li et al., International Conference on Learning Representations (2021)|频域卷积能否跨网格学习PDE解算子|局部高频补偿与球面几何继续提升能力|在傅里叶模态上学习全局核积分|FNO以共享频域核实现跨分辨率场预测，在流体和天气任务获得数量级加速|截断高频会平滑激波和小尺度，跨网格插值不等于跨物理参数外推
物理信息神经算子|Physics-Informed Neural Operator|Li et al., ACM/AAAI and scientific-computing studies (2022)|无成对高保真标签时能否用方程残差训练算子|2025材料研究将守恒和多尺度约束写入算子|在函数空间训练中同时优化数据与PDE残差|PINO结合算子预训练和物理微调，可减少标签并提高特定实例精度|方程残差继承数值离散和参数错误，多目标损失仍可能牺牲关键守恒量
全球天气图学习|GraphCast|Lam et al., Science 382, 1416–1421 (2023), doi:10.1126/science.adi2336|数据驱动全球预报能否在极端与气候漂移下稳定优于数值模式|集合、同化和极端指标继续成为下一轮基准|用多尺度图网络从再分析场预测全球天气|GraphCast展示学习模型可在分钟级生成高质量十日预报，并在多项确定性指标超过业务基线|再分析训练继承数值模式与观测偏差，单次确定性预报不足以给概率风险且极端样本少
三维天气基础模型|Pangu-Weather|Bi et al., Nature 619, 533–538 (2023), doi:10.1038/s41586-023-06185-3|大模型天气预报能否同时保持多层大气一致和长期稳定|基础模型继续连接集合与下游灾害任务|以三维地球特定网络学习多时距预报|Pangu-Weather证明深度模型可快速预测全球多层状态，为业务级科学机器学习树立系统基准|递归误差、资料同化缺失和训练期气候限制仍需混合数值系统补足
科学机器学习统一评测|Scientific Machine-Learning Benchmarking|Rabeh et al., Communications Engineering 4 (2025)|跨论文速度和误差能否在统一硬件、网格和外推任务下比较|2025评测扩展守恒、分布外和端到端成本|固定数据预算、求解容差与硬件比较模型|统一评测把代理、PINN、神经算子和经典求解器置于同一计时与误差口径，减少选择性报告|任何基准只覆盖有限PDE和参数分布，排行榜会诱导针对测试集优化
材料物理信息算子|Physics-Informed Operators for Materials|Moon et al., npj Computational Materials 11 (2025)|神经算子能否在复杂材料边界和多尺度响应中保留物理一致|2025工作并列数据效率、残差和微结构外推|把材料守恒与本构约束嵌入算子训练|材料物理算子展示学习器可加速多次场预测并在少数据时由方程约束稳定训练|微结构拓扑和相变超训练域时会违反本构，平均场误差会遮蔽局部失效热点
自主科学机器学习代理|Agentic Scientific Machine Learning|AgenticSciML and autonomous-science benchmark studies (2026)|代理能否自主提出、运行和修正科学模型且保留可复现证据链|2026研究开始比较工具调用、失败恢复和假设质量|让代理编排数据、求解器、诊断和实验设计|科学代理把模型选择、代码执行和结果解释串成迭代工作流，有望降低跨工具研究成本|代理会放大错误假设和选择性搜索，成功运行代码不等于科学结论，所有轨迹需版本化
科学机器学习闭环验收|Scientific-ML Closed-Loop Acceptance|Karniadakis et al., Nature Reviews Physics 3, 422–440 (2021), doi:10.1038/s42254-021-00314-5|学习模型能否经守恒、网格、外推、基线和科学反事实共同验收|2025至2026评测强调误差证书和自主工作流审计|以隐藏参数域、独立求解器和回退阈值验收|闭环验收要求锁定训练数据与算力，报告经典基线、物理残差、目标量误差、稳定时长和超域检测，并复现实验轨迹|真实科学域无限且极端状态稀少，通过现有基准不能消除共同模型偏差，部署必须保留高保真回退
""",
)


if __name__ == "__main__":
    base.main()
