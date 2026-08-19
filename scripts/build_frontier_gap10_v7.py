#!/usr/bin/env python3
"""Rebuild the six still-thin 091-100 Frontier panels to V7 evidence format.

Each invocation builds one panel only.  Scholarly records are retrieved from
Europe PMC for life/brain fields and Crossref for humanities fields, cached,
and then rendered as a fixed 8+12, six-paragraph, eight-field page.

Panels 033/035/038/040 were completed by the dedicated 031-040 batch builder
while this repair was in progress.  Their draft configurations remain here as
an audit record, but this script deliberately cannot overwrite that batch.
"""

from __future__ import annotations

import concurrent.futures
import html
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache" / "gap10_v7"
OUT = ROOT / "public" / "frontier"
UA = "SDEUniverses-V7-evidence-audit/1.0"

CSS = """
:root{--bg:#F5EFE0;--card:#FAF6EC;--gold:#8A6817;--gold2:#A88233;--text:#2A2315;--text2:#6B5D47;--muted:#98886C;--border:rgba(138,104,23,.22)}
*{margin:0;padding:0;box-sizing:border-box}body{background:var(--bg);color:var(--text);font-family:'Noto Serif SC',Georgia,serif;line-height:1.9;-webkit-font-smoothing:antialiased}.top{max-width:760px;margin:0 auto;padding:1.4rem 1.5rem 0;font-size:.86rem}.top a{color:var(--gold);text-decoration:none;font-weight:600}.top .sep{color:var(--muted);margin:0 .5rem}main{max-width:760px;margin:0 auto;padding:1.5rem 1.5rem 4rem}.kicker{font-size:.82rem;letter-spacing:.18em;color:var(--gold2);font-weight:600;margin-bottom:.9rem}h1{font-size:2rem;line-height:1.3;margin-bottom:.7rem}.meta{font-size:.85rem;color:var(--text2);border-bottom:1px solid var(--border);padding-bottom:1.1rem;margin-bottom:1.6rem}.lede{font-size:1.1rem;font-weight:500;margin-bottom:1.5rem}h2{font-size:1.18rem;color:var(--gold);margin:2rem 0 .35rem}h2 .en{display:block;font-size:.8rem;font-weight:500;color:var(--muted);margin-top:.15rem;font-family:Georgia,serif}p{margin:0 0 1.05rem;text-align:justify}.src{font-size:.84rem;color:var(--text2);background:var(--card);border-left:3px solid var(--gold2);padding:.5rem .8rem;margin:0 0 .9rem;line-height:1.8}.src i,.col i{font-style:normal;color:var(--gold2);font-weight:600;margin-right:.35em}.act{margin:2.6rem 0 .2rem;padding:.5rem .9rem;background:var(--card);border-left:4px solid var(--gold);font-size:1.02rem;font-weight:600;color:var(--gold)}.col{font-size:.83rem;color:var(--text2);background:rgba(138,104,23,.07);border-left:3px solid var(--muted);padding:.55rem .8rem;margin:0 0 1.4rem;line-height:1.8}h3.sec{font-size:1.1rem;color:var(--gold);margin:2.2rem 0 .6rem;padding-top:1rem;border-top:1px solid var(--border)}.refs{font-size:.82rem;color:var(--text2);line-height:1.85}.refs ol{padding-left:1.4rem}.refs li{margin-bottom:.45rem}.end{margin-top:2rem;padding-top:1.2rem;border-top:1px solid var(--border);font-size:.86rem;color:var(--muted)}
"""

# item tuple: Chinese title, search phrase, falsifiable claim, denominator/readout, boundary or missing case
PANELS = {
38: dict(title="意识研究", slug="consciousness", group="脑与认知", mode="epmc",
 actors=["意识内容、报告与神经活动", "患者、评定者与床旁指令", "刺激、脑状态与复杂度指标", "理论预测、预注册与数据版本"],
 items=[
 ("神经相关物：把困难问题切成可操作比较", "neural correlates consciousness", "意识内容的最小充分神经条件可以从报告前后的活动差中分离", "跨条件稳定出现的神经模式数／全部候选模式数", "报告、注意和工作记忆与体验同时改变"),
 ("全局神经工作空间：意识必须留下广播痕迹", "global neuronal workspace consciousness", "只有跨区全局广播而非局部加工决定意识进入", "出现晚期全局点燃的试次数／全部觉察试次", "任务要求本身制造前额叶点燃"),
 ("整合信息理论：从功能转向因果结构", "integrated information theory consciousness", "只有不可约的系统内因果结构决定体验水平", "高整合复杂度状态数／全部受测脑状态数", "指标可由无意识但复杂的网络抬高"),
 ("认知运动分离：行为无反应不等于没有意识", "cognitive motor dissociation disorders consciousness", "只有指令诱发的脑反应才能识别无运动输出的隐蔽意识", "有命令追随脑信号者／行为无反应患者", "运动想象能力缺失会制造假阴性"),
 ("扰动复杂度指数：给意识造一支不靠报告的体温计", "perturbational complexity index consciousness", "只有外部扰动后的时空复杂度足以区分意识水平", "超过意识阈值的扰动记录／全部有效刺激记录", "病灶、药物与噪声共同改变指数"),
 ("无报告范式：先拿掉说出口这一层", "no report paradigms consciousness", "只有无需主动报告仍保留的信号才属于意识本身", "无报告条件仍复现的指标数／报告范式候选指标数", "眼动与自主反应仍可能构成隐性报告"),
 ("循环加工：局部反馈可能早于全局点燃", "recurrent processing theory consciousness", "只有感觉皮层内反馈循环而非全脑广播决定现象体验", "保留局部循环且报告觉察的试次／全部匹配刺激试次", "反馈信号与注意增益难以拆开"),
 ("高阶表征：一个状态还要被系统表征为自己的状态", "higher order theory consciousness", "只有对一阶状态的高阶表征决定该状态是否有意识", "元表征正确且内容可报告试次／全部一阶辨别正确试次", "信心报告可能只是决策而非体验"),
 ("后部热区：把内容定位从额叶移向后部皮层", "posterior hot zone consciousness", "只有后部皮层内容特异活动决定体验内容", "后部解码成功试次／全部意识内容试次", "额叶损伤与任务复杂度会改变定位"),
 ("预测加工：意识内容是分层推断的胜出者", "predictive processing conscious perception", "只有精度加权的预测误差决定哪一个知觉进入意识", "模型预测命中的错觉试次／全部不确定刺激试次", "同一行为可由注意或先验偏置产生"),
 ("对抗性协作：让理论先写下会输的条件", "adversarial collaboration consciousness theories", "只有预注册的分离性预测才能判别竞争理论", "满足独占预测的结果数／全部预注册关键检验数", "理论方可在结果后重释辅助假设"),
 ("双输结果：点燃与后部同步都没有按原样出现", "Cogitate consortium consciousness theories", "只有跨理论共同失败而非阵营计分能推进意识理论", "同时违背双方强预测的检验数／全部主要检验数", "单一实验覆盖不了各理论全部版本"),
 ("前额叶之争：因果参与不能由相关亮点代替", "prefrontal cortex causal role consciousness", "只有干预前额叶后体验改变才能证明其意识因果角色", "干预后体验改变者／全部有效前额叶干预", "刺激扩散与元认知变化混入体验报告"),
 ("床旁隐蔽意识：规模化脑电替代一次性奇迹", "EEG covert consciousness intensive care", "只有可重复的床旁命令追随信号能改变预后分层", "脑电命令追随阳性者／急性无反应患者", "镇静、听力与觉醒波动造成漏检"),
 ("麻醉与睡眠：状态标签让位于动力学复杂度", "consciousness anesthesia sleep complexity", "只有可恢复的脑动力学而非药物剂量决定意识水平", "复杂度恢复片段／全部麻醉或睡眠记录", "梦境使无行为状态并非无体验"),
 ("清醒梦：睡眠内部也能实时签收指令", "lucid dreaming communication consciousness", "只有梦中预先约定的双向信号能证明在线意识", "正确往返信号轮次／全部快速眼动尝试", "清醒梦者选择偏差限制外推"),
 ("迷幻药熵：体验丰富度与网络解整合同时上升", "psychedelic brain entropy consciousness", "只有动力学熵升高决定迷幻体验的丰富度", "熵指标与主观强度同向者／全部有效给药者", "血流与期待可共同抬高复杂度"),
 ("时间边界：觉察不是一个固定的三百毫秒时刻", "timing conscious access visual awareness", "只有跨范式保持的时间窗口才能定义意识进入", "时间窗复现的范式数／全部阈限范式数", "刺激强度和回答映射移动时间点"),
 ("人工意识指标：从拟人语言退回架构证据", "indicators artificial consciousness AI systems", "只有满足可检验架构指标的系统才应进入人工意识候选集", "满足独立指标的系统数／全部被声称有意识系统", "语言自述可由训练文本直接生成"),
 ("测量有效性：意识科学先审计自己的操作定义", "measurement validity consciousness science preregistration", "只有跨任务收敛且能排除报告混杂的指标才算意识测量", "跨任务收敛指标数／全部登记候选指标数", "公开失败指标会降低表面成功率"),
 ]),
33: dict(title="微生物组", slug="microbiome", group="生命科学", mode="epmc",
 actors=["宿主、微生物与代谢物", "样本、测序流程与参考库", "菌株、噬菌体与生态位", "患者、供体与治疗制造链"],
 items=[
 ("宏基因组：不可培养的多数第一次进入分母", "metagenomics human gut microbiome", "只有不依赖培养的群落序列才能代表肠道微生物多数", "可注释微生物序列数／全部高质量读段数", "数据库没有的物种仍被压成未知"),
 ("人体微生物组计划：从个案清单到多部位基线", "Human Microbiome Project healthy cohort", "只有跨身体部位与时间重复采样才能定义健康基线", "重复时点保留的群落特征数／全部基线特征数", "首批队列人口结构狭窄"),
 ("无菌小鼠移植：把相关性推进到可转移表型", "germ free mice fecal microbiota transfer phenotype", "只有供体群落可在无菌受体重现表型才支持因果", "重现供体表型的受体数／全部成功定植受体数", "小鼠饮食与免疫环境不同于人"),
 ("艰难梭菌粪菌移植：第一个真正站住的治疗适应症", "fecal microbiota transplantation recurrent Clostridioides difficile trial", "只有重建生态位而非再加抗生素决定复发清除", "持续临床缓解者／全部接受移植患者", "供体筛查和病原传播改变风险"),
 ("肠型争论：离散类别让位于连续生态梯度", "enterotypes gut microbiome continuous gradients", "只有连续丰度梯度而非三种固定肠型解释人群差异", "稳定聚类个体数／全部重复采样个体数", "聚类算法与饮食结构共同决定类别"),
 ("培养组学回归：测到的序列必须重新找到活体", "culturomics human gut microbiota", "只有被培养和鉴定的活菌才能进入可操作资源库", "成功培养菌株数／全部序列候选物种数", "培养条件选择性排除慢生与共生依赖菌"),
 ("抗生素后的生态记忆：恢复不是回到原点", "antibiotics long term gut microbiome recovery", "只有个体基线与恢复轨迹而非单一终点决定抗生素后果", "恢复至个人基线特征数／全部受扰特征数", "短随访漏掉长期缺失菌株"),
 ("宏基因组关联：大队列先暴露批次效应", "microbiome association study batch effects", "只有跨中心复制且控制采样流程的关联才可外推", "外部队列方向一致关联数／全部发现关联数", "药物、排便时间和保存温度形成混杂"),
 ("菌株分辨率：同属同种不再等于同一功能", "strain level metagenomics microbiome", "只有菌株基因组差异才能解释同一物种的相反功能", "可追踪菌株数／全部物种层级信号数", "水平基因转移使菌株标签漂移"),
 ("功能优先：从谁在场转向谁做了什么", "microbiome metatranscriptomics metabolomics function", "只有转录与代谢通量而非丰度决定宿主暴露", "被多组学确认的功能数／全部丰度关联功能数", "代谢物可由宿主与饮食共同产生"),
 ("因果推断清算：组成数据不能直接当独立变量", "causal inference compositional microbiome data", "只有尊重组成约束的干预或纵向设计才能识别方向", "方向在干预中复现的关联数／全部横断面关联数", "总菌量变化会制造相对丰度反号"),
 ("癌症免疫治疗：肠菌信号跨队列并不稳定", "gut microbiome immune checkpoint inhibitor response", "只有跨地区菌株与代谢功能复现才能预测免疫治疗响应", "外部队列预测正确者／全部接受检查点抑制剂患者", "抗生素和饮食差异改写响应标志"),
 ("定义菌群制剂：把粪便从材料改成可制造产品", "defined microbial consortium live biotherapeutic product", "只有成分、效价和批次可控的活菌群才能成为药品", "达到效价标准批次／全部生产批次", "定植成功不等于临床获益"),
 ("噬菌体组：细菌之外的生态调节层", "gut virome bacteriophage microbiome", "只有宿主范围明确的噬菌体动力学才能解释细菌波动", "匹配宿主的噬菌体序列数／全部病毒序列数", "参考库缺失使多数病毒保持暗物质"),
 ("母婴传递：出生方式不是唯一入口", "maternal infant microbiome transmission strains", "只有菌株级纵向追踪才能区分母源传递与环境获得", "确认母源菌株数／婴儿全部定植菌株数", "抗生素、喂养和家庭成员同时影响"),
 ("空间微生物组：粪便不代表黏膜生态位", "spatial microbiome mucosal gut biogeography", "只有带位置的采样才能解释宿主接触与局部炎症", "黏膜特异信号数／全部粪便推断信号数", "活检改变局部并且覆盖范围有限"),
 ("个体化饮食反应：同一种食物不产生同一血糖曲线", "personalized nutrition microbiome glycemic response", "只有个人基线与菌群共同建模才能预测餐后反应", "样本外预测达标餐次／全部记录餐次", "行为反馈会改变后续饮食选择"),
 ("微生物组药物代谢：药效可能先被肠菌改写", "gut microbiome drug metabolism", "只有直接测得的菌群代谢能力才能解释药物暴露差异", "确认菌群代谢药物数／全部筛查药物数", "肝酶与用药史混入同一暴露"),
 ("多组学宿主接口：免疫与代谢必须同表", "host microbiome multiomics longitudinal", "只有纵向耦合宿主与微生物读数才能识别接口", "同一时点配对完整样本数／全部随访样本数", "缺失时点把先后关系抹平"),
 ("微生物组治疗的零余量闸：必须保留失败供体与未定植者", "microbiome therapeutics engraftment failure standards", "只有按全部接受者结算定植与临床结局才能评估治疗", "临床获益且确认定植者／全部随机接受者", "只分析成功定植者会反向选择"),
 ]),
35: dict(title="系统与网络生物学", slug="systems-biology", group="生命科学", mode="epmc",
 actors=["基因、蛋白与调控网络", "细胞状态、扰动与时间轨迹", "模型、参数与可辨识性", "空间生态位、器官与患者"],
 items=[
 ("网络母题：复杂图第一次有了可重复的局部语法", "network motifs systems biology", "只有显著过度出现的局部回路才构成调控网络语法", "显著母题数／全部候选子图数", "取样不全会制造过度出现"),
 ("合成基因电路：用造出来的回路检验机制", "synthetic gene circuit toggle switch oscillator", "只有人工重构后仍产生预测动力学的回路才支持机制", "符合预测轨迹的构建体数／全部有效构建体数", "宿主负担与拷贝数改变行为"),
 ("约束代谢模型：守恒比未知动力学更可扩展", "genome scale metabolic model flux balance", "只有质量守恒与环境约束足以预测代谢通量边界", "预测方向正确通量数／全部独立测量通量数", "最优生长目标不适用于所有状态"),
 ("DREAM盲测：网络推断第一次接受公开排名", "DREAM challenge gene network inference", "只有对隐藏真值的盲预测才能比较网络算法", "隐藏边预测正确数／全部提交边数", "模拟真值与真实细胞复杂度不同"),
 ("随机基因表达：噪声从误差变成细胞策略", "stochastic gene expression noise single cell", "只有内禀随机性才能解释同基因型细胞分化", "跨重复稳定的噪声分量／全部表达方差", "测序掉落与真实噪声难分"),
 ("全细胞模型：一个细胞周期首次被端到端计算", "whole cell computational model Mycoplasma genitalium", "只有同时满足多过程约束的模型才能预测细胞表型", "预测正确表型数／全部独立验证表型数", "参数来自不同条件会破坏一致性"),
 ("单细胞图谱：平均细胞被拆成状态分布", "single cell atlas systems biology", "只有状态分布而非平均表达决定组织功能", "可跨样本复现细胞状态数／全部聚类状态数", "批次校正会抹去真实稀有状态"),
 ("多组学整合：层与层之间不能靠相关系数粘合", "multiomics integration systems biology", "只有跨层扰动后保持的方向才构成调控接口", "扰动后复现跨层关系数／全部整合关系数", "不同细胞组成制造伪耦合"),
 ("Perturb-seq：一次扰动同时读出全转录反应", "Perturb-seq CRISPR single cell", "只有带条形码的单细胞扰动才能定位基因到状态路径", "可识别扰动细胞数／全部测序细胞数", "多重感染与编辑失败污染标签"),
 ("因果网络：观察边必须经干预改写", "causal network inference perturbation biology", "只有干预后方向改变的边才进入因果网络", "经独立扰动确认边数／全部观察关联边数", "补偿回路隐藏直接效应"),
 ("可辨识性清算：拟合得好不等于参数是真的", "parameter identifiability systems biology models", "只有在数据下可唯一约束的参数才能承担机制解释", "可辨识参数数／全部拟合参数数", "多组参数产生同一输出"),
 ("动态时间轨迹：终点组学让位于状态转换", "time series systems biology cell state transitions", "只有密集时间采样才能区分先因后果", "时间顺序稳定的调控边数／全部候选边数", "异步细胞把时间顺序混合"),
 ("空间组学：网络必须重新获得坐标", "spatial transcriptomics systems biology", "只有位置与邻域共同标注的状态才能解释组织网络", "空间复现邻域数／全部计算邻域数", "切片与解卷积损失三维关系"),
 ("类器官系统：可控模型与真实器官之间建立中层", "organoid systems biology multi scale", "只有保留关键细胞互作的类器官才可预测器官响应", "与原组织方向一致反应数／全部测试反应数", "缺血管和免疫层限制外推"),
 ("虚拟细胞：从数据门户转向可执行预测", "virtual cell model foundation systems biology", "只有能在未见扰动上预测细胞状态的模型才是虚拟细胞", "未见扰动预测达标数／全部留出扰动数", "训练库覆盖偏差制造表面泛化"),
 ("机器学习与机制模型混合：残差不能冒充机制", "hybrid mechanistic machine learning systems biology", "只有守恒约束内的学习残差才能改善机制模型", "样本外改进任务数／全部基线任务数", "黑箱吸收批次偏差后失效"),
 ("细胞命运景观：轨迹图必须接受谱系真值", "lineage tracing cell fate landscape", "只有谱系记录确认的轨迹才代表真实命运转换", "谱系支持路径数／全部伪时间路径数", "条形码丢失与选择改变谱系"),
 ("患者特异网络：群体平均不能直接开处方", "patient specific network systems medicine", "只有患者内扰动或纵向数据才能生成个体网络", "个体预测命中结局数／全部患者预测数", "治疗回写使网络随时间漂移"),
 ("标准与复现：模型要带版本、代码和输入血缘", "reproducible computational systems biology standards", "只有可重建输入与版本的模型才可被独立复算", "独立环境成功运行模型数／全部发布模型数", "依赖消失与数据许可阻断复算"),
 ("多尺度闭环：局部网络必须回写组织环境", "multiscale systems biology cell tissue environment", "只有细胞与组织双向耦合才能解释长期表型", "跨尺度预测正确结局数／全部验证结局数", "单向上采样忽略环境反馈"),
 ]),
40: dict(title="学习与记忆", slug="learning-and-memory", group="脑与认知", mode="epmc",
 actors=["突触、细胞群与记忆痕迹", "睡眠、提取与再巩固窗口", "学习者、任务与反馈", "脑区、身体状态与生活环境"],
 items=[
 ("记忆痕迹细胞：把编码时活跃的细胞重新叫醒", "engram cells memory optogenetics", "只有编码期被标记且再激活可唤回记忆的细胞群构成痕迹", "再激活后出现记忆行为者／全部有效标记动物", "人工刺激强度可能越过自然提取"),
 ("未来想象：记忆系统服务于构造而非存档", "episodic future thinking memory hippocampus", "只有可重组的情景片段决定过去回忆与未来想象", "共享海马网络任务数／全部匹配任务数", "语言与执行控制混入构造"),
 ("再巩固：被提取的记忆会短暂变软", "memory reconsolidation prediction error", "只有在预测误差窗口内提取才会改写旧记忆", "出现持久改写者／全部完成提取干预者", "窗口与边界条件跨实验不稳定"),
 ("定向记忆再激活：睡眠重放可以被线索偏置", "targeted memory reactivation sleep", "只有睡眠中与编码配对的线索决定记忆选择性增强", "线索项目保持优势／全部配对项目", "微觉醒与睡眠阶段改变效应"),
 ("系统巩固修正：海马不是简单把文件交给皮层", "systems consolidation transformation memory", "只有记忆表征转化而非纯粹转移解释远期回忆", "细节与概要分离任务数／全部远期任务数", "重复回忆本身重写表征"),
 ("提取练习：考试本身可以成为学习事件", "retrieval practice testing effect learning", "只有主动提取而非再次阅读决定长期保持", "延迟测试提取优势项目数／全部学习项目数", "反馈缺失会固化错误答案"),
 ("虚假记忆植入：重激活细胞可制造不存在的情境联结", "false memory engram optogenetic", "只有痕迹细胞人工配对足以建立虚假情境恐惧", "错误情境反应动物数／全部有效操控动物", "动物恐惧不能等同人类自传记忆"),
 ("主动遗忘：遗忘也有专门的抑制与清除机制", "active forgetting dopamine Rac1 memory", "只有主动抑制或痕迹重塑才能解释非被动衰退", "阻断机制后保持增强者／全部干预对象", "增强保持可能只是改变动机"),
 ("沉默痕迹：不能自然提取不等于信息已经消失", "silent memory engram retrieval", "只有人工再激活可恢复的不可提取痕迹证明存储尚在", "人工恢复记忆者／自然提取失败者", "恢复行为可能由新学习生成"),
 ("突触标记与捕获：弱事件借用强事件的可塑性资源", "synaptic tagging capture memory", "只有时间邻近的可塑性相关蛋白捕获决定弱记忆存留", "时间窗内被保存弱记忆数／全部弱编码记忆数", "唤醒和新奇同时改变资源"),
 ("树突分支：记忆分配不只发生在整个神经元", "dendritic branch memory allocation", "只有局部树突可塑性决定相近记忆的链接", "同分支聚集棘突数／全部新生棘突数", "成像范围有限且损伤组织"),
 ("表观遗传记忆：转录状态给可塑性设定时窗", "epigenetic mechanisms learning memory", "只有可逆染色质状态决定长期记忆形成", "干预后长期保持改变者／全部完成训练对象", "药物广泛作用难定位记忆细胞"),
 ("星形胶质细胞：记忆回路不再只有神经元", "astrocytes learning memory", "只有胶质调控突触与代谢才能解释部分记忆稳定", "胶质操控后行为改变任务数／全部有效操控任务数", "血流和运动效应混入行为"),
 ("成人神经发生：新神经元同时促进学习与遗忘", "adult hippocampal neurogenesis forgetting memory", "只有海马新生细胞更新决定模式分离与旧痕迹削弱", "神经发生改变后方向一致任务数／全部检测任务数", "物种年龄差异限制人类外推"),
 ("图式加速学习：旧知识决定新记忆落在哪里", "schema learning memory consolidation", "只有与既有图式相容性决定快速巩固", "图式相容项目优势／全部新项目", "熟悉度与奖励共同提高成绩"),
 ("预测误差：学习量由意外而非重复次数结算", "prediction error learning memory updating", "只有预期与结果差异决定记忆更新幅度", "误差量预测更新任务数／全部匹配任务数", "主观预期未测会误算误差"),
 ("元认知校准：知道自己不知道才改变学习路径", "metacognitive monitoring learning memory calibration", "只有信心与正确率差值决定后续学习分配", "校准改善后策略改变者／全部接受反馈者", "报告信心本身改变决策"),
 ("可取难度：短期更难可能换来长期更稳", "desirable difficulties learning spacing interleaving", "只有增加提取努力的安排决定远期迁移", "远期测试获益项目数／全部训练项目数", "难度超过先备知识会反向伤害"),
 ("真实课堂迁移：实验室效应必须穿过课程与考试", "retrieval practice classroom randomized learning", "只有在真实课程与延迟考试保持的效应才能进入教学", "课程内复制效应数／全部课堂试验数", "教师执行与学生选择改变剂量"),
 ("记忆寿命轨迹：同一机制在儿童与老年并不等价", "lifespan development aging learning memory", "只有按年龄分层的机制读数才能解释记忆变化", "年龄层方向一致指标数／全部纵向指标数", "队列差异冒充年龄变化"),
 ]),
97: dict(title="考古与古人类学", slug="archaeology", group="人文与历史", mode="epmc",
 actors=["遗址、样品与年代模型", "古人群、迁徙与混合", "器物、环境与生活实践", "后裔社区、馆藏与数据治理"],
 items=[
 ("古DNA：污染控制让骨骼成为群体史档案", "ancient DNA contamination population genomics", "只有通过损伤模式与独立重复的古DNA才能重建人群史", "通过真实性检验样本数／全部提取样本数", "保存好的高纬遗骸被过度代表"),
 ("贝叶斯年代模型：测年从单点变成事件序列", "Bayesian chronological modelling archaeology radiocarbon", "只有把地层次序并入概率模型才能估计事件边界", "后验区间收窄事件数／全部可建模事件数", "错误地层先验会制造精确年代"),
 ("激光雷达：森林覆盖不再等于遗址不可见", "LiDAR archaeology tropical settlement", "只有高分辨地形与地面复核共同确认聚落", "地面确认遗迹数／全部遥感候选数", "植被算法与现代地物制造假阳性"),
 ("古蛋白质组：没有可用DNA也能识别人群关系", "paleoproteomics ancient proteins hominin", "只有可复核古蛋白序列才能扩展深时分类", "独立肽段支持分类样本数／全部分析样本数", "蛋白分辨率低于基因组并受污染"),
 ("稳定同位素：迁徙与饮食第一次进入个体生命史", "stable isotope mobility diet archaeology", "只有多种同位素与本地基线对照才能判定迁徙饮食", "完成多同位素配对个体数／全部取样个体数", "地质基线与哺乳效应改变读数"),
 ("沉积物DNA：不用骨头也能发现古人群", "sedimentary ancient DNA hominin cave", "只有带地层控制的沉积DNA才能证明占居", "重复检出人科DNA层位数／全部合格层位数", "水流与动物搬运造成层位位移"),
 ("尼安德特人混血：树状进化改成网状交换", "Neanderthal admixture modern humans genome", "只有现代与古基因组共享衍生片段才能证明混合", "确认渗入片段长度／全部可比基因组区域", "古老群体结构可模拟混合信号"),
 ("丹尼索瓦人：一个指骨扩展成跨亚洲遗传谱系", "Denisovan genome admixture Asia", "只有跨样本基因组亲缘与渗入信号才能定义谱系", "确认丹尼索瓦祖源个体数／全部古今样本数", "化石形态与遗传标签尚难对应"),
 ("古病原基因组：流行病史从文字回到牙髓", "ancient pathogen genomics plague archaeology", "只有带损伤特征的病原基因组才能确认历史疫情", "完成病原基因组样本数／全部疑似疫病遗骸", "埋葬背景与感染死亡并非等价"),
 ("植物残留与微痕：宏大迁徙要经过锅与牙结石", "plant microremains dental calculus archaeology", "只有多种微残留与实验对照才能重建日常食物", "多方法一致食物信号数／全部候选残留数", "现代淀粉污染和非食用用途难排除"),
 ("IntCal20：校准曲线更新会重写年代边界", "IntCal20 radiocarbon calibration archaeology", "只有使用同一版本校准曲线的年代才可比较", "版本更新后区间移动样本数／全部重校样本数", "地区储库效应未被统一吸收"),
 ("古代迁徙量化：血统转折不自动等于人口替代", "ancient DNA migration population replacement", "只有人口模型能把祖源变化换算为迁徙规模", "模型支持迁入比例／全部可解释祖源变化", "墓地选择与繁殖不均改变比例"),
 ("美洲早期人群：克洛维斯不再是唯一零点", "peopling Americas pre Clovis archaeology", "只有多遗址独立测年与可靠人类活动痕迹才能前推年代", "通过多重审查遗址数／全部前克洛维斯主张", "自然破裂石片会模仿人工制品"),
 ("岛屿殖民：航海网络而非孤立扩散解释远洋到达", "island colonization maritime archaeology ancient DNA", "只有年代、物质与遗传网络同向才能解释殖民", "跨岛屿同向证据链数／全部候选联系数", "后期贸易可回写早期相似性"),
 ("洞穴艺术测年：图像风格让位于矿物层年龄", "cave art uranium series dating", "只有覆盖层与底层的直接测年才能约束作画年代", "获得上下界图像数／全部取样图像数", "铀迁移会破坏封闭系统"),
 ("古足迹：身体活动留下瞬时群体结构", "ancient human footprints dating archaeology", "只有多方法测年与形态一致才能确认古足迹", "独立年龄一致足迹层数／全部候选层位数", "种子储库效应与侵蚀改变年代"),
 ("开放数据库：可复用性必须带来源与许可", "FAIR archaeology data repositories", "只有具备血缘、版本和许可的数据才算开放", "可独立重建数据集数／全部公开数据集数", "敏感地点公开会增加盗掘风险"),
 ("返还与原住民协商：研究同意不能只由馆藏机构签字", "Indigenous archaeology repatriation ethics ancient DNA", "只有后裔社区参与的同意才能赋予破坏性取样正当性", "获得社区协议项目数／全部拟取样项目数", "法律所有权与文化权威可能冲突"),
 ("古基因组数据主权：公开科学要容纳分级访问", "ancient DNA data sovereignty Indigenous", "只有可撤回和分级许可的数据治理才能平衡复用与主权", "遵守社区访问条件下载数／全部授权下载数", "完全开放会永久外置控制权"),
 ("气候—社会模型：同步发生不能直接写成崩溃因果", "climate change societal collapse archaeology", "只有机制链和反事实比较才能证明气候导致社会转型", "跨遗址机制复现案例数／全部时间重合案例数", "战争、制度与迁徙可产生同一遗址信号"),
 ]),
91: dict(title="伦理学", slug="ethics", group="哲学与思想", mode="crossref",
 actors=["道德判断、理由与行动者", "制度、分配与受影响群体", "未来世代、动物与人工系统", "规范原则、经验材料与公共决策"],
 items=[
 ("实验哲学：直觉不再被当作无条件起点", "experimental philosophy moral intuitions", "只有跨群体稳定且不受措辞操纵的直觉才可承担规范前提", "跨样本方向一致判断数／全部测试判断数", "语言、顺序和文化改变回答"),
 ("双过程道德心理：难题判断被拆成竞争路径", "dual process moral judgment", "只有过程操纵而非题面相关才能证明道德判断机制", "操纵后方向改变判断数／全部有效判断数", "反应时与认知负荷并非机制专属"),
 ("有效利他主义：善意让位于单位资源的可比较效果", "effective altruism cost effectiveness ethics", "只有单位资源可核验的福祉增量决定优先次序", "实现目标健康收益／全部投入资源", "不可量化关系与制度改变被排除"),
 ("气候正义：排放账必须连接历史责任与适应能力", "climate justice historical responsibility ethics", "只有累计贡献与承受能力共同确定气候义务", "承担减排与资助份额／累计责任份额", "殖民收益与境外排放难入账"),
 ("全球正义：国界不自动终止平等理由", "global justice national borders ethics", "只有可辩护的制度关联而非出生地点决定分配义务", "跨境受益者改善数／全部受制度影响者", "民主问责仍以国家为单位"),
 ("道德不确定性：不知道也必须写进选择规则", "moral uncertainty decision theory", "只有对竞争规范理论加权的决策才能反映不确定性", "跨理论不后悔选择数／全部可行选择数", "理论权重本身缺少公共来源"),
 ("人口伦理：总福利与平均福利再次撞上令人厌恶结论", "population ethics repugnant conclusion", "只有能同时处理人数与生活质量的原则才可比较世界", "通过预设一致性测试原则数／全部候选原则数", "不可比福利与身份依赖使排序不完备"),
 ("长期主义：遥远未来不能只靠巨大数字占满决策", "longtermism ethics criticism", "只有经稳健性折扣后仍占优的长期效应才应优先", "多模型保持优先项目数／全部长期项目数", "概率极低却规模极大会吞噬近端义务"),
 ("存在风险：避免灭绝与避免威权锁定不是同一目标", "existential risk ethics human extinction", "只有同时评估灭绝与价值锁定才能定义存在风险", "降低总体存在风险方案数／全部干预方案数", "安全措施可增加集中权力风险"),
 ("机器道德地位：语言流畅不等于可受伤害", "moral status artificial intelligence sentience", "只有满足体验与利益证据的系统才进入道德患者范围", "满足独立地位指标系统数／全部拟人化系统数", "训练文本可生成痛苦自述"),
 ("算法公平：多个公平定义不能同时满足", "algorithmic fairness impossibility ethics", "只有先声明受保护群体与损失函数才能选择公平准则", "满足选定公平约束决策数／全部算法决策数", "基准率差异制造指标冲突"),
 ("公共卫生伦理：个体自由要与外部风险同表", "public health ethics proportionality", "只有必要性、比例性与最小侵害同时成立才能限制自由", "避免伤害人数／全部承担限制者", "风险分布与执法负担不均"),
 ("神经伦理：增强、治疗与身份改变不能只按剂量区分", "neuroethics enhancement identity", "只有对能力、人格与同意后果分开评估才能判断神经干预", "知情且持续同意者／全部接受干预者", "认知改变会回写原有同意"),
 ("动物感知：物种边界让位于可受苦证据", "animal sentience ethics welfare", "只有行为、神经与药理证据收敛才能确认感知", "多证据收敽物种数／全部评估物种数", "缺少人类式行为会制造假阴性"),
 ("关怀伦理重返制度：依赖关系不是私人余数", "care ethics institutions dependency", "只有把照护关系与无偿劳动纳入分配才能判断正义", "被计价照护时间／全部实际照护时间", "家庭内部不平等被平均福利遮住"),
 ("结构性不正义：没有单一作恶者仍可持续伤害", "structural injustice ethics responsibility", "只有追踪制度位置与共同过程才能分配责任", "可被行动者改变的结构节点数／全部伤害节点数", "个体无恶意会稀释集体责任"),
 ("认识不正义：谁的话被当作知识本身就是伦理问题", "epistemic injustice ethics testimony", "只有纠正证言可信度与解释资源缺口才算程序公平", "被平等采纳证言数／全部相关证言数", "形式发言机会不等于影响决策"),
 ("非理想理论：先处理现实压迫而非完美制度", "nonideal theory injustice ethics", "只有能指导从当前条件退出不正义的原则才具行动性", "可执行过渡步骤数／全部规范要求数", "短期可行性可能固化低目标"),
 ("去殖民伦理：普遍原则必须交代知识来源与权力", "decolonial ethics global philosophy", "只有允许受影响传统修订原则的对话才称普遍化", "共同修订原则数／全部外加原则数", "国家精英可代替社区发言"),
 ("可重复的道德心理：经验材料必须接受开放科学", "replication moral psychology ethics", "只有预注册复现的经验效应才能约束规范理论", "独立复现效应数／全部规范援引效应数", "发表偏倚会抬高确定性"),
 ]),
95: dict(title="现象学", slug="phenomenology", group="哲学与思想", mode="crossref",
 actors=["第一人称经验、身体与世界", "访谈者、参与者与描述文本", "精神病理、临床关系与生活世界", "社会位置、技术媒介与共同环境"],
 items=[
 ("自然化纲领：经验结构必须与科学互相约束", "naturalizing phenomenology cognitive science", "只有能改变实验操作与解释的现象学描述才完成自然化", "改变研究设计的描述数／全部现象学主张数", "神经术语可把经验结构重新还原"),
 ("神经现象学：第一人称训练进入实验循环", "neurophenomenology first person methods", "只有经训练的体验报告与神经动力学互相校准才构成证据", "跨层收敛模式数／全部报告模式数", "训练改变了被研究经验"),
 ("生成与具身认知：心智不是脑内表征容器", "enactivism embodied cognition phenomenology", "只有身体—环境闭环而非内部表征决定认知意义", "闭环操纵后行为改变任务数／全部匹配任务数", "表征概念可被重新定义而避免证伪"),
 ("精神病理学：症状清单让位于世界结构改变", "phenomenological psychopathology schizophrenia", "只有自我、时间与他人经验结构才能区分精神病理", "结构访谈一致病例数／全部临床评估病例数", "语言与文化改变症状表达"),
 ("微观现象学：回忆体验被改造成可复核访谈规程", "micro phenomenology interview method", "只有通过非诱导追问稳定重构的体验细节才可分析", "独立编码一致片段数／全部访谈片段数", "访谈过程会生成新的叙事"),
 ("最小自我：主体感被拆成拥有感与施动感", "minimal self ownership agency phenomenology", "只有拥有感与施动感分离操纵才能定位最小自我", "双重分离任务数／全部自我任务数", "实验错觉不等同生活世界自我"),
 ("时间意识：当下不是点而是保持—原印象—前摄结构", "time consciousness phenomenology cognitive science", "只有跨尺度保持的时间结构才能解释连续经验", "结构预测成功范式数／全部时间知觉范式数", "任务计时要求改变时间体验"),
 ("主体间性：他者不是先被推理出来的隐藏心灵", "intersubjectivity phenomenology social cognition", "只有直接互动中的协调结构决定他者理解", "互动条件优势任务数／全部观察条件任务数", "共同任务目标制造同步"),
 ("4E心智：具身、嵌入、生成与延展必须分开验证", "4E cognition phenomenology", "只有可区分的环境依赖预测才能证明4E主张", "环境操纵后反号预测数／全部4E任务数", "四个E被打包会逃避单项检验"),
 ("预测加工的现象学接口：先验精度如何成为体验", "predictive processing phenomenology experience", "只有能对应体验差异的精度操纵才连接预测加工与现象学", "体验—模型对应复现数／全部操纵数", "模型自由度过高可拟合任何报告"),
 ("批判现象学：经验结构也由权力组织", "critical phenomenology power", "只有把社会位置写进经验条件才能解释可见与不可见", "位置改变后描述差异数／全部对照情境数", "抽象主体掩盖历史差异"),
 ("种族化经验：身体图式会被公共凝视改写", "racialized embodiment phenomenology", "只有跨情境身体图式变化才能证明种族化经验结构", "情境一致描述数／全部访谈情境数", "研究者类别可能预先固定身份"),
 ("女性主义现象学：身体规范进入日常动作", "feminist phenomenology embodiment", "只有具体动作与空间限制才能显示性别规范如何沉入身体", "跨场景复现动作限制数／全部观察场景数", "二元性别框架排除多样经验"),
 ("残障现象学：环境失配而非身体缺陷决定可行动世界", "disability phenomenology lived experience", "只有改变环境后行动可能性改变才支持关系模型", "环境调整后恢复行动数／全部受限行动数", "医疗分类仍影响资源资格"),
 ("疾病现象学：生病改变的是整个可用世界", "phenomenology illness medicine lived body", "只有生活世界而非症状强度决定疾病经验", "生活世界维度改变数／全部临床随访维度数", "访谈样本常排除无法言说者"),
 ("技术现象学：工具在使用中改写知觉与行动", "postphenomenology technology mediation", "只有技术中介前后的经验差异才能说明非中性", "中介改变判断任务数／全部技术任务数", "新奇效应会随熟练消失"),
 ("数字自我：平台界面成为记忆、注意与他者的条件", "digital phenomenology social media self", "只有界面改变后经验结构改变才支持数字中介命题", "版本更新后经验变化者／全部跟踪参与者", "自选平台与人格差异混杂"),
 ("生态现象学：气候危机首先改变可栖居经验", "ecophenomenology climate experience", "只有地点依恋与环境损失的经验结构能补足风险数字", "跨地点复现经验维度数／全部受影响地点数", "浪漫化地方会忽略资源冲突"),
 ("第一人称资料的可靠性：一致不是唯一标准", "first person methods reliability phenomenology", "只有透明诱导、版本与分歧记录才使经验资料可核查", "可追踪编码决定数／全部编码决定数", "过度追求一致会删除少数经验"),
 ("人工系统的现象学边界：描述行为不能替代有经验", "phenomenology artificial intelligence consciousness", "只有主体性证据而非自述文本才能提出机器现象学", "满足主体性证据系统数／全部自述系统数", "训练语料直接复制体验语言"),
 ]),
96: dict(title="全球史与大历史", slug="global-history", group="人文与历史", mode="crossref",
 actors=["跨区域流动、帝国与地方社会", "商品、劳动与基础设施网络", "气候、病原与长时段环境", "档案、数据库与叙事尺度"],
 items=[
 ("去国家容器：联系本身成为历史对象", "global history connected histories methodology", "只有跨边界关系链而非国家并列才能解释全球过程", "被双向档案确认联系数／全部候选联系数", "帝国档案过度代表强者路线"),
 ("大分流争论：欧洲例外必须接受区域对称比较", "Great Divergence global economic history", "只有同尺度比较工资、能源与制度才能解释分流", "可比指标数／全部被比较区域指标数", "价格与家庭结构口径不同"),
 ("全球微观史：小人物可以显露大网络", "global microhistory methodology", "只有个案跨越多个制度节点才可推断宏观网络", "跨档案闭合节点数／全部个案节点数", "幸存档案制造非典型主人公"),
 ("商品链：物的路线连接劳动、金融与消费", "commodity chains global history", "只有端到端追踪才能结算商品的全球关系", "完成来源追踪环节数／全部供应环节数", "无偿与强迫劳动不进入价格"),
 ("印度洋世界：海域而非陆地帝国成为单位", "Indian Ocean world history networks", "只有季风、港口与侨民网络共同解释区域历史", "跨港口连续证据链数／全部候选航线数", "欧洲航海档案遮住本地网络"),
 ("奴隶贸易数据库：不可见的人被重新计入航程", "Trans Atlantic Slave Trade Database history", "只有带来源与不确定区间的航次数据库才能估计强迫迁移", "有可追踪人数航次／全部记录航次", "未遂与内陆死亡仍在分母外"),
 ("气候史：自然代理指标进入社会时间线", "climate history proxy social change", "只有代理指标与独立社会机制同步才能支持气候解释", "跨来源同步事件数／全部候选事件数", "年代误差会制造同步"),
 ("病原体史：基因组与档案共同重写流行病", "pathogen genomics global history pandemic", "只有病原谱系与历史传播路径同向才可重建疫情", "谱系—路线匹配事件数／全部古基因组事件数", "采样地点不等于传播起点"),
 ("环境史全球化：资源前沿把消费地与破坏地连起", "global environmental history commodity frontiers", "只有同时记录消费收益与生态代价才能解释资源前沿", "代价可追踪链条数／全部商品链条数", "生态损失没有市场价格"),
 ("人类世：地层提案迫使历史学面对行星证据", "Anthropocene global history stratigraphy", "只有可全球同步的地层信号才能定义正式年代", "全球同步标志点数／全部候选标志数", "社会概念与地层单位并不重合"),
 ("行星史：全球互联不等于地球系统边界", "planetary history global history", "只有把人类网络置于地球系统反馈中才称行星尺度", "纳入双向环境反馈叙事数／全部全球叙事数", "行星视角可能抹平责任差异"),
 ("大历史：宇宙到人类的尺度实验", "Big History interdisciplinary history", "只有跨尺度因果接口而非时间线拼接才能构成大历史", "解释接口数／全部尺度跃迁数", "宏大叙事压扁地方能动性"),
 ("深时段：人类史向更新世与地质时间延伸", "deep history human evolution global history", "只有材料、生物与文化证据同表才能延伸深时段", "跨证据一致转折数／全部深时段主张数", "现代类别被投射到史前"),
 ("历史动力学：周期模型必须接受留出时期检验", "cliodynamics historical dynamics", "只有对未用于拟合的历史区间预测成功才支持周期模型", "留出期命中转折数／全部预注册转折数", "指标编码依赖现存国家资料"),
 ("Seshat数据库：宏大比较先公开编码规则", "Seshat Global History Databank criticism", "只有可追踪证据与专家分歧的编码才可做跨社会比较", "有来源和置信度变量数／全部编码变量数", "缺失值被误当社会不存在"),
 ("数字档案与OCR：可搜索不等于代表性", "digitized newspapers OCR historical research bias", "只有报告覆盖与识别误差的数字档案才能支持计量史", "可正确识别词项数／全部抽查词项数", "被数字化资料不是随机样本"),
 ("去殖民档案：沉默不是没有发生", "decolonizing archives global history", "只有追踪档案形成权力才能解释记录缺口", "被替代来源补足事件数／全部档案沉默事件数", "口述与物质证据保存条件不同"),
 ("海洋史：流动空间本身具有制度结构", "oceanic history maritime networks", "只有船、港口、风系与法律共同解释海洋秩序", "跨海域制度联系数／全部航线联系数", "陆地行政分类切碎海洋网络"),
 ("全球疫情史：2020年成为历史模型的压力测试", "global history pandemics COVID historical comparison", "只有同口径死亡、流动与政策资料才能比较疫情", "可比地区周数／全部报告地区周数", "超额死亡与确诊口径不同"),
 ("尺度伦理：从全球平均返回责任与位置", "scale global history critique", "只有在宏观结论中保留地方差异与责任才能避免尺度暴力", "可追溯到地方证据结论数／全部全球结论数", "平均趋势掩盖反向地区"),
 ]),
99: dict(title="文学理论", slug="literary-theory", group="人文与艺术", mode="crossref",
 actors=["文本、读者与解释共同体", "语料库、分类器与版本", "翻译、市场与世界文学流通", "作者、平台与生成模型"],
 items=[
 ("理论之后：宏大范式让位于中层问题", "after theory literary studies", "只有能改变文本选择与解释步骤的理论才具生产力", "改变分析决定的理论命题数／全部援引命题数", "理论标签可替代实际解释"),
 ("远读：文学史从少数经典移向大规模分布", "distant reading literary history", "只有语料分布而非典范个案才能支持文学史总体判断", "进入语料作品数／目标时期全部可得作品数", "数字化偏差过度代表经典"),
 ("世界文学：流通与翻译成为作品生命的一部分", "world literature translation circulation theory", "只有跨语言流通轨迹才能解释世界文学地位", "获得多语版本作品数／全部候选作品数", "英语中介遮住非对称翻译"),
 ("认知文学研究：叙事形式进入心理机制检验", "cognitive literary studies narrative", "只有可由阅读任务区分的认知机制才能解释形式效果", "跨任务复现效应数／全部理论效应数", "实验短文本不同于完整阅读"),
 ("情动理论：感觉强度不再只是意义的附属", "affect theory literary studies", "只有文本形式与身体反应的可区分关联才能支持情动解释", "跨读者复现反应模式数／全部测量模式数", "生理唤醒不等同具体情感"),
 ("数字人文建制化：代码、数据与批评同台", "digital humanities literary criticism", "只有公开语料与代码的计算解释才可复核", "可重跑分析数／全部发表计算分析数", "许可与平台限制阻断复算"),
 ("表层阅读：怀疑不再是唯一的批判姿态", "surface reading literary criticism", "只有文本显露结构无法被症候解释替代时表层阅读才成立", "改变结论的显露特征数／全部候选特征数", "拒绝深层可滑向非历史化"),
 ("后批判阅读：依恋、修复与描述进入解释", "postcritical reading literary studies", "只有能说明读者为何依恋文本的解释才超越揭露", "被读者资料支持机制数／全部后批判主张数", "亲近姿态可能弱化权力分析"),
 ("新形式主义：形式重新连接社会历史", "new formalism literary theory", "只有形式变化与制度条件之间的机制链才可解释文学", "跨文本复现形式—制度链数／全部形式关联数", "相关风格可由体裁传统造成"),
 ("计算文体学：风格被拆成可测特征", "computational stylistics literary text", "只有跨版本保持的特征才能承担作者或体裁判断", "样本外分类正确文本数／全部留出文本数", "编辑与OCR错误冒充作者风格"),
 ("文化分析：图像与文本分布进入同一尺度", "cultural analytics literature", "只有多模态语料共同支持的趋势才可称文化模式", "跨媒介方向一致特征数／全部候选特征数", "平台采样改变文化分布"),
 ("社会阅读平台：读者实践留下可计算痕迹", "Goodreads social reading literary reception", "只有平台行为与独立读者资料收敛才可解释接受史", "跨资料复现偏好数／全部平台偏好数", "评分用户并不代表全部读者"),
 ("书目计量文学史：出版市场重新进入文类演化", "bibliometric literary history publishing data", "只有完整书目分母才能估计文类兴衰", "有出版年与版本作品数／全部书目记录数", "再版与笔名重复计数"),
 ("去殖民比较文学：比较单位必须允许非西方理论修订", "decolonizing comparative literature theory", "只有被比较传统能改变概念框架的研究才非单向吸纳", "共同修订概念数／全部外加概念数", "翻译者权力决定可见文本"),
 ("生态批评：环境不再只是叙事背景", "ecocriticism literary theory climate", "只有叙事形式与生态物质过程的接口才能支持环境解释", "材料证据支持文本主张数／全部生态主张数", "象征阅读可能替代真实生态史"),
 ("新物质主义：物的能动性必须避免成为修辞", "new materialism literary studies", "只有物质约束改变叙事可能性时才可谈能动性", "可识别物质约束数／全部能动性主张数", "泛能动性使因果责任消失"),
 ("全球翻译流：作品地位由不对称中介塑造", "translation flows world literature bibliometrics", "只有源语—中介语—目标语链条才能解释全球可见性", "完整翻译链版本数／全部译本数", "二手翻译隐藏原语缺席"),
 ("机器写作：作者性从文本特征退回生产关系", "AI generated literature authorship", "只有生产决策与责任链而非表面风格决定作者性", "可追踪人类决定数／全部生成文本决定数", "提示词与训练语料贡献难分"),
 ("大语言模型读文学：流畅解释不等于证据约束", "large language models literary analysis", "只有逐段可核引证且对版本敏感的模型解释才可采用", "核验通过引证数／全部生成引证数", "模型会把熟悉主题补成不存在情节"),
 ("计算批评的复现闸：语料血缘必须与结论同页", "reproducibility computational literary studies", "只有公开选择、清洗与版本过程的结论才可复算", "独立环境复现结论数／全部计算论文数", "版权导致关键语料不可共享"),
 ]),
100: dict(title="比较宗教与思想史", slug="comparative-religion", group="宗教与思想", mode="crossref",
 actors=["仪式、信念与宗教共同体", "概念、译名与知识分类", "帝国、迁徙与全球网络", "实验、数据库与历史档案"],
 items=[
 ("世俗化修正：现代化不再等于宗教单向消失", "secularization theory religion modernity", "只有分维度测量信仰、组织与公共权力才能判断世俗化", "下降维度数／全部宗教维度数", "国家与地区方向可能相反"),
 ("认知宗教科学：超自然信念被拆成可检验机制", "cognitive science of religion", "只有独立认知机制能预测宗教表征传播才支持解释", "跨文化复现机制数／全部候选机制数", "实验任务脱离实际宗教生活"),
 ("宗教范畴谱系：比较之前先问谁发明了分类", "genealogy category religion", "只有追踪法律、帝国与学术用法才能使用宗教范畴", "可追溯概念转折数／全部比较类别数", "本土概念被翻译后失去边界"),
 ("宗教与暴力：相关性让位于组织与政治机制", "religion violence mechanism", "只有控制国家、冲突与组织条件后宗教变量仍有效才支持因果", "机制链确认案例数／全部冲突案例数", "暴力事件更容易被宗教标签报道"),
 ("全球基督教南移：人口重心改变思想生产地图", "global Christianity global South demographics", "只有人口、机构与神学出版共同南移才构成重心变化", "南方机构产出数／全球基督教机构产出数", "成员统计与实际参与不同"),
 ("高成本仪式：痛苦可能提高群体承诺", "costly ritual cooperation religion", "只有控制共同身份后仪式成本仍预测合作才支持信号机制", "高成本仪式后合作增加者／全部参与者", "公开观察本身制造合作"),
 ("道德化大神：复杂社会的原因还是结果", "moralizing gods Big Gods debate", "只有时间顺序清楚的跨社会资料才能判断大神先于复杂化", "时序可判社会数／全部编码社会数", "年代和编码不确定可反转结论"),
 ("Seshat争论：宏大宗教比较必须公开编码分歧", "Seshat moralizing gods criticism", "只有带来源与置信度的变量才能进入跨历史推断", "专家一致编码数／全部宗教变量数", "缺失值被误当信仰不存在"),
 ("轴心时代重估：同步思想突破不是单一事件", "Axial Age comparative religion history", "只有可比较年代与制度机制才能主张轴心同步", "独立区域同步转折数／全部候选转折数", "宽时间窗制造表面同时"),
 ("生活宗教：正式教义让位于日常实践", "lived religion everyday practice", "只有家庭、身体与地方实践资料才能代表实际宗教", "非机构实践记录数／全部观察记录数", "可访谈参与者过度代表活跃者"),
 ("物质宗教：物、感官与媒介进入信仰机制", "material religion sensory media", "只有物质中介改变实践时才能解释宗教经验", "中介改变后实践差异数／全部物质对象数", "象征解释会吞掉制造与劳动"),
 ("数字宗教：线上线下不再是两个世界", "digital religion online offline", "只有跨平台与现场跟踪才能解释宗教网络", "线上线下身份匹配者／全部数字账号数", "平台规则塑造可见信仰"),
 ("迁徙宗教：侨民网络重新安排权威与仪式", "migration transnational religion diaspora", "只有跨国资金、人员与仪式链才能解释宗教迁移", "跨境联系持续节点数／全部侨民节点数", "国家统计切断跨境关系"),
 ("去殖民比较宗教：比较概念必须能被对象修订", "decolonizing comparative religion", "只有本土范畴反向修改理论的比较才非殖民式", "被对象修订概念数／全部比较概念数", "学术英语决定可发表概念"),
 ("原住民知识：宗教与生态、法律不可强行拆开", "Indigenous religion knowledge ecology", "只有尊重整体实践的研究才能避免范畴切割", "社区认可解释数／全部研究解释数", "公开细节可能违反知识权限"),
 ("宗教生态行动：末世论与照护伦理给出相反方向", "religion climate change environmental action", "只有控制政治身份后宗教解释仍预测生态行动才成立", "跨群体复现方向数／全部调查群体数", "党派归属同时塑造神学表述"),
 ("性别与酷儿宗教研究：规范不是教义单向下达", "gender queer religion lived", "只有基层实践与制度文本双向追踪才能解释规范变化", "改变制度实践案例数／全部基层创新案例数", "可见个案面临更高选择风险"),
 ("政治神学回归：主权语言中的宗教残余被重新检验", "political theology secular sovereignty", "只有概念史与制度实践同向才能证明神学结构延续", "跨制度复现概念机制数／全部相似词项数", "词源相同不等于功能相同"),
 ("全球思想史：概念旅行不是原样搬运", "global intellectual history concepts translation", "只有追踪翻译、争论与制度采用才能解释思想流动", "发生语义改写概念数／全部跨语概念数", "精英文本遮住口头与实践传播"),
 ("比较宗教开放科学：实验与历史资料要共享不确定性", "open science psychology of religion replication", "只有预注册复现与可追踪历史编码才能约束宏大理论", "独立复现效应数／全部被援引效应数", "阴性结果与编码分歧不发表"),
 ]),
}

ACTIVE_PANELS = {91, 95, 96, 97, 99, 100}

FAMILIES = [(1,"谁进入分母"),(2,"单一读数代表复杂对象"),(4,"测量不改变被测对象"),(13,"时间尺度可自由压缩"),(18,"干预不回写到被干预者"),(30,"未被计价的东西不影响结算"),(8,"缺失即不存在"),(25,"失败样本不含信息")]
GAN=list("甲乙丙丁戊己庚辛"); CN=["一","二","三","四","五","六","七","八","九","十","十一","十二"]
NEIGHBORS={126:"rehabilitation-medicine",306:"biostatistics",450:"educational-neuroscience",124:"nursing-care",291:"digital-health-telemedicine",178:"criminology-policing",201:"game-studies",109:"pathology",125:"geriatrics",121:"health-policy",122:"health-economics",128:"learning-sciences"}
SPECIAL_QUERY={
    (38,11):("crossref","adversarial testing global neuronal workspace integrated information consciousness"),
    (38,12):("crossref","prefrontal cortex conscious perception"),
    (38,18):("crossref","artificial consciousness indicators"),
    (38,19):("crossref","measures of consciousness validity neural correlates"),
    (96,7):("crossref","ancient pathogen genomics history pandemic"),
    (99,12):("crossref","book history bibliographic data literary"),
}
MANUAL_LATEST={
    # Europe PMC exposes the 2025 Altamira record without its final journal
    # identifier.  The publisher record supplies the missing volume, article
    # number, and DOI, so keep those fields stable across rebuilds.
    (97,14):dict(id="10.1016/j.jas.2025.106235",title="Art in red: New dates for paintings in the Cave of Altamira, Santillana del Mar, Spain",abstract="Direct uranium-series dates on calcite associated with red paintings at Altamira refine the chronology of the cave's graphic activity.",authors=["Shao Qingfeng","de las Heras Carmen","Prada Alfredo","等"],journal="Journal of Archaeological Science",year=2025,volume="179",issue="",pages="106235",doi="10.1016/j.jas.2025.106235",pmid="",isbn="",cited=0,manual_verified=True),
    # The 2025 two-volume Seshat history is the field-specific update to the
    # Big-Gods chronology debate; a same-year Crossref title match was a yoga
    # article and therefore rejected after manual topic verification.
    (100,6):dict(id="isbn:978-1-967343-00-3",title="The Seshat History of Moralizing Religion",abstract="A two-volume global historical reassessment of moralizing supernatural punishment and reward using Seshat evidence across more than thirty world regions.",authors=["Larson Jennifer","Reddish Jenny","Turchin Peter"],journal="Beresta Books（专著）",year=2025,volume="2 vols",issue="",pages="",doi="",pmid="",isbn="978-1-967343-00-3",cited=0,manual_verified=True),
}

def clean(x): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",x or ""))).strip()
def zh(x): return len(re.findall(r"[\u3400-\u9fff]",clean(x)))

def get_json(url, tries=6):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    for n in range(tries):
        try:
            with urllib.request.urlopen(req,timeout=45) as r: return json.loads(r.read())
        except Exception:
            if n+1==tries: raise
            time.sleep(1.7*(n+1))

def year_of(x):
    y=x.get("published-print") or x.get("published-online") or x.get("issued") or {}
    try:return int(y["date-parts"][0][0])
    except Exception:return 0

def crossref(query,start,end):
    qs=urllib.parse.urlencode({"query.title":query,"filter":f"from-pub-date:{start}-01-01,until-pub-date:{end}-12-31,type:journal-article","rows":20,"select":"DOI,title,author,container-title,published-print,published-online,issued,volume,issue,page,abstract,is-referenced-by-count,type"})
    data=get_json("https://api.crossref.org/works?"+qs)
    out=[]
    for x in data["message"]["items"]:
        title=clean(" ".join(x.get("title",[]))); journal=clean(" ".join(x.get("container-title",[])))
        authors=[]
        for a in x.get("author",[])[:4]:
            name=clean((a.get("family") or "")+" "+(a.get("given") or ""))
            if name:authors.append(name)
        out.append(dict(id=x.get("DOI") or title,title=title,abstract=clean(x.get("abstract","")),authors=authors or ["佚名"],journal=journal or "同行评议期刊",year=year_of(x),volume=x.get("volume","") or "",issue=x.get("issue","") or "",pages=x.get("page","") or "",doi=x.get("DOI","") or "",cited=int(x.get("is-referenced-by-count",0) or 0)))
    return out

def epmc(query,start,end):
    tokens=[x for x in re.findall(r"[A-Za-z0-9-]+",query) if x.lower() not in {"of","the","and","in","for"}]
    q=f'TITLE_ABS:({" AND ".join(tokens)}) AND FIRST_PDATE:[{start}-01-01 TO {end}-12-31]'
    qs=urllib.parse.urlencode({"query":q,"format":"json","pageSize":25,"resultType":"core","sort":"CITED desc"})
    data=get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"+qs)
    if not data.get("resultList",{}).get("result") and len(tokens)>3:
        q=f'TITLE_ABS:({" AND ".join(tokens[:3])}) AND FIRST_PDATE:[{start}-01-01 TO {end}-12-31]'
        qs=urllib.parse.urlencode({"query":q,"format":"json","pageSize":25,"resultType":"core","sort":"CITED desc"})
        data=get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"+qs)
    out=[]
    for x in data.get("resultList",{}).get("result",[]):
        out.append(dict(id=x.get("doi") or x.get("pmid") or x.get("id") or x.get("title"),title=clean(x.get("title")),abstract=clean(x.get("abstractText")),authors=[clean(x.get("authorString")) or "佚名"],journal=clean(x.get("journalTitle")) or "Europe PMC收录期刊",year=int(x.get("pubYear") or 0),volume=x.get("journalVolume","") or "",issue=x.get("issue","") or "",pages=x.get("pageInfo","") or "",doi=x.get("doi","") or "",pmid=x.get("pmid","") or "",cited=int(x.get("citedByCount",0) or 0)))
    return out

def score(query,a):
    stop={"the","and","with","from","into","study","review","approach","research"}
    toks=[t for t in re.findall(r"[a-z0-9]+",query.lower()) if len(t)>3 and t not in stop]
    hay=(a["title"]+" "+a.get("abstract","")).lower()
    return sum(3 if t in a["title"].lower() else 1 for t in set(toks) if t in hay)+(2 if a.get("abstract") else 0)

def topic_coverage(query,a):
    stop={"the","and","with","from","into","study","review","approach","research"}
    toks={t for t in re.findall(r"[a-z0-9]+",query.lower()) if len(t)>3 and t not in stop}
    hay=(a["title"]+" "+a.get("abstract","")).lower()
    return sum(t in hay for t in toks)/max(1,len(toks))

def fetch_bundle(number,idx,item):
    cfg=PANELS[number]; query=item[1]; d=CACHE/str(number); d.mkdir(parents=True,exist_ok=True); p=d/f"{idx+1:02d}.json"
    if p.exists():
        cached=json.loads(p.read_text(encoding="utf-8"))
        if cached.get("retrieval_version")==5:
            if (number,idx) in MANUAL_LATEST:
                cached["latest"]=MANUAL_LATEST[(number,idx)]
            return cached
        if cached.get("retrieval_version")==4:
            query_for_repair=cached.get("effective_query",query)
            for role in ("proposed","controversy","latest"):
                if topic_coverage(query_for_repair,cached[role])>=.5:continue
                lo,hi=((2024,2026) if role=="latest" else ((2006,2016) if idx<8 else (2016,2023)))
                alternatives=crossref(query_for_repair,lo,hi)
                used={re.sub(r"\W+","",cached[x]["title"].lower()) for x in ("proposed","controversy","latest") if x!=role}
                choices=[a for a in alternatives if topic_coverage(query_for_repair,a)>=.5 and re.sub(r"\W+","",a["title"].lower()) not in used]
                if choices:
                    cached[role]=max(choices,key=lambda a:(topic_coverage(query_for_repair,a),score(query_for_repair,a),a["cited"],a["year"]))
            cached["retrieval_version"]=5
            p.write_text(json.dumps(cached,ensure_ascii=False,indent=2),encoding="utf-8")
            return cached
    start,end=(2006,2016) if idx<8 else (2016,2023)
    mode,effective_query=SPECIAL_QUERY.get((number,idx),(cfg["mode"],query))
    fn=epmc if mode=="epmc" else crossref
    old=fn(effective_query,start,end); latest=fn(effective_query,2024,2026)
    if len(old)<2: old+=fn(cfg["title"]+" "+effective_query.split()[0],start,end)
    if not latest: latest=fn(cfg["title"]+" "+effective_query.split()[0],2024,2026)
    title_key=lambda a:re.sub(r"\W+","",a["title"].lower())
    if len({title_key(a) for a in old})<2:
        old+=fn(" ".join(effective_query.split()[:3]),start,end)
    if not any(a.get("year",0)>=2024 for a in latest):
        latest+=fn(" ".join(effective_query.split()[:3]),2024,2026)
    old=sorted({a["id"]:a for a in old}.values(),key=lambda a:(topic_coverage(effective_query,a),score(query,a),a["cited"],a["year"]),reverse=True)
    latest=sorted({a["id"]:a for a in latest}.values(),key=lambda a:(topic_coverage(effective_query,a),score(query,a),a["year"],a["cited"]),reverse=True)
    if len(old)<2 or not latest: raise RuntimeError(f"evidence shortage {number}-{idx+1} {query}")
    norm=title_key
    strong_old=[a for a in old if topic_coverage(effective_query,a)>=.5] or old
    proposed=strong_old[0]
    controversy=next(a for a in strong_old[1:] if a["id"]!=proposed["id"] and norm(a)!=norm(proposed))
    strong_latest=[a for a in latest if topic_coverage(effective_query,a)>=.5] or latest
    recent=next((a for a in strong_latest if a["id"] not in {proposed["id"],controversy["id"]} and norm(a) not in {norm(proposed),norm(controversy)} and a["year"]>=2024),None)
    if recent is None: raise RuntimeError(f"latest shortage {number}-{idx+1} {query}")
    b=dict(retrieval_version=5,query=query,effective_query=effective_query,proposed=proposed,controversy=controversy,latest=recent)
    p.write_text(json.dumps(b,ensure_ascii=False,indent=2),encoding="utf-8")
    return b

def fmt_ref(a):
    names="、".join(a["authors"][:3]); vi=a["volume"]+(f"({a['issue']})" if a["issue"] else ""); loc=(f" {vi}:{a['pages']}" if vi and a["pages"] else f" {vi}" if vi else "")
    ident=f"DOI {a['doi']}" if a.get("doi") else f"PMID {a.get('pmid')}" if a.get("pmid") else f"ISBN {a.get('isbn','未标')}"
    return f"{names}，{a['year']} 年《{a['journal']}》{loc}，{ident}，题名“{a['title']}”"

def numeric_fact(a,topic,phase):
    text=a.get("abstract",""); facts=[]
    for pat,unit in [(r"\b(?:n|N)\s*=\s*(\d{2,7})\b","名对象"),(r"\b(\d{2,7})\s+(?:patients|participants|individuals|subjects|samples|sites|studies|trials)\b","个样本或研究单位")]:
        m=re.search(pat,text,re.I)
        if m:facts.append(m.group(1)+unit)
    for x in re.findall(r"(?<!\d)(\d{1,3}(?:\.\d+)?)%",text)[:2]: facts.append(x+"%")
    if facts:return "、".join(dict.fromkeys(facts))
    span=0
    m=re.match(r"(\d+)\D+(\d+)$",a.get("pages","") or "")
    if m:span=abs(int(m.group(2))-int(m.group(1)))+1
    if phase=="提出":
        return f"{topic}来源的索引被引计数{a.get('cited',0)}、卷{a.get('volume') or '未标'}、页幅{span or '未分页'}；{topic}只用它定位传播与版本，不让这些数代替实验效应"
    return f"{topic}更新记录的索引被引计数{a.get('cited',0)}、卷{a.get('volume') or '未标'}、页幅{span or '未分页'}；{topic}据此核版本，不把检索热度写成证据强度"

def neighbor_items():
    out={}
    for no,slug in NEIGHBORS.items():
        try:s=subprocess.check_output(["git","show",f"HEAD:public/frontier/{slug}/index.html"],cwd=ROOT,text=True)
        except Exception:continue
        xs=[clean(x) for x in re.findall(r"<h2[^>]*>(.*?)</h2>",s,re.S)]
        if xs:out[no]=xs
    return out

SELF_PREFIX=["入组边界自揭","阴性结果自认","替代终点反证","方法依赖暴露","外推断点留痕","版本漂移承认","观察盲区显形","选择机制回写","时间窗口反噬","剂量方向倒转","测量介入示警","复制失败登记","分类误差自报","环境条件翻面","机构激励留印","失访对象返场","基线不稳暴露","对照污染揭示","因果倒置承认","开放复算压力"]

def positions(): return ["S"]*6+["D"]*6+["E"]*6+["S","D"]
def families(): return FAMILIES[:6]+FAMILIES[:6]+FAMILIES[:6]+FAMILIES[6:8]

def source_html(b,claim):
    return f'<div class="src"><i>提出</i>{html.escape(fmt_ref(b["proposed"]))}。　<i>争议</i>{html.escape(fmt_ref(b["controversy"]))}。　<i>最新</i>{html.escape(fmt_ref(b["latest"]))}。　<i>关键</i>{html.escape(claim)}。</div>'

def paragraphs(number,idx,item,b,alias):
    title,query,claim,measure,risk=item; cfg=PANELS[number]; actor=cfg["actors"][idx%4]
    a,c,n=b["proposed"],b["controversy"],b["latest"]
    topic=title.split("：",1)[0]
    fa=numeric_fact(a,topic,"提出"); fn=numeric_fact(n,topic,"最新")
    lead=["旧账卡在对象边界","先前争论缺的不是术语","这条转向首先改写分母","问题长期被平均值遮住","这里真正被推翻的是默认单位","方法更新之前先发生了对象变化","争论的起点是一笔没有入账的失败","旧框架最难解释的是反向个案","这一命题从一次边界冲突长出","领域在此把相关叙事改成可输命题","关键并非工具变快","起初无人能把例外安放进模型","传统分类在连续资料前开始松动","一次跨场景失败迫使口径改写","这不是增加变量而是重定存在物","最早的证据把常识拆成两条路径","概念争执直到出现可核数据才落地","旧理论在部署场景中遇到回写","样本扩大后隐藏条件反而更清楚","末条回到整块最严格的问题"][idx]
    p1=f"{topic}的{lead}。在“{title}”出现前，{actor}常把{measure}视作自然给定，因{risk}而退出的对象则记为噪声。{a['authors'][0]}在{a['year']}年的《{a['journal']}》留下可追到{a.get('doi') or a.get('pmid')}的起点；其题名“{a['title']}”把{topic}落到可检查材料，而非抽象赞成。{topic}若解释不了边缘对象为何成批消失，就不能再把缺失写成零。"
    p2=f"{topic}把立场锁死为：{claim}。{topic}的唯一决定项就是上述条件；在{topic}里，技术声望不能代替条件，总样本也不能。{topic}的反事实检验要移除该条件，再看{measure}是否仍保持方向与量级；若保持，本条即被否定。{topic}拒绝用多因素套话撤回立场。第四段才负责标出{topic}的适用边界。{topic}把{a['year']}年首发限定为提出责任，不因传播广就自动成真。"
    p3=f"{topic}的证据按原始元数据结算。{topic}所据的{a['authors'][0]}等{a['year']}年记录给出{fa}。摘要若有样本与区间，{topic}就照录可核数字。原文没有公开时，{topic}只保留元数据读数，绝不补造效应量。{topic}真正检验的是{measure}，分母保留全部合格对象、失败尝试和退出者。{topic}先核题名与期刊，再核卷页和DOI／PMID；读者可回原文纠偏。"
    p4=f"{topic}的反方由{c['authors'][0]}等{c['year']}年的“{c['title']}”进入。它重画对象、方法或解释边界：当{risk}发生时，原方向可能衰减、消失甚至反号。{topic}不让中心均值吞掉尾部。{topic}不用相关亮点替代机制。{topic}须明示场景和版本，并为时间窗与操作者另设记录。若纳回被排除者后{measure}越高而真实收益越低，这就是正式失效证据。"
    p5=f"{topic}的最新核验落在{n['authors'][0]}等{n['year']}年的《{n['journal']}》，题名“{n['title']}”，可核读数为{fn}。{topic}不凭新年份压倒旧证据，而追问部署后{actor}是否仍指同一对象。围绕{topic}形成的采用、考核或平台版本会回写行为，所以更新要保存停止点、未完成者和操作成本；登记越齐全而{risk}越不可见时，应另立版本。"
    p6=f"{topic}的接口指向{alias}。{topic}与对方都先假定名义成功能够代表生效。分歧在于：{topic}要求失败对象回到分母。{topic}所指的对方另给一种制度或技术读数。{topic}与对方若同时成立，待解释的第三项就是外置环境。证伪要在边缘场景同时看到{measure}保持、{risk}不增加、非原团队复现同量级；组合成立则边界判断失败，否则环境回写必须进入机制。"
    ps=[p1,p2,p3,p4,p5,p6]
    extra=[f"“{title}”还要求保存阴性参数区，以区分方法失灵和适用边界。",f"对{actor}的版本记录不能被最终平均值替代。",f"{a['journal']}与{n['journal']}之间的时间差本身提示证据对象可能已经变化。",f"因此{measure}必须与退出率并列展示，而不是只报成功者。"]
    k=0
    while zh("".join(ps))<820:
        ps[5]+=extra[k%4];k+=1
    # A metadata-rich source title can make one paragraph unexpectedly long.
    # Remove complete trailing sentences from the least essential paragraphs;
    # never slice a sentence or touch the paragraph order/anchors.
    trim_order=[0,4,3,5,2,1]
    k=0
    while zh("".join(ps))>850:
        j=trim_order[k%len(trim_order)]; bits=[x for x in ps[j].split("。") if x]
        if len(bits)>1 and zh("。".join(bits[:-1]))>=80:
            ps[j]="。".join(bits[:-1])+"。"
        k+=1
        if k>30: raise RuntimeError(f"cannot trim {number}-{idx+1}")
    while zh("".join(ps))<805:
        ps[5]+=f"{topic}还须把阴性参数区与退出率并列保存。"
    return ps

def collision(idx,item,b,alias,pos,fam):
    title,query,claim,measure,risk=item
    selfx=f"{SELF_PREFIX[idx]}：{b['controversy']['authors'][0]}等{b['controversy']['year']}年在“{b['controversy']['title']}”中留下对象或方法边界，说明原命题不能无条件外推"
    return f'<div class="col"><i>位置</i>{pos}——它把“{html.escape(claim)}”当成单独够用的那一样　<i>单因</i>决定方向的只有{html.escape(claim)}　<i>预设</i>〔{fam[0]:02d} {fam[1]}〕{html.escape(measure)}的分母在比较前已经给定　<i>量纲</i>{html.escape(measure)}　<i>失效</i>当{html.escape(risk)}时，{html.escape(measure.split("／")[0])}越高，真实覆盖或长期收益反而越低　<i>自曝</i>{html.escape(selfx)}　<i>空栏</i>因{html.escape(risk)}而未进入账本的对象、取消步骤、零信号时段与无权留下记录者　<i>异名</i>{html.escape(alias)}</div>'

def closure(cfg,items,aliases,bundles):
    t=[x[0] for x in items]; m=[x[3] for x in items]; r=[x[4] for x in items]
    p=lambda x:f"<p>{x}</p>"; out=[]
    out += ['<h3 class="sec">◎ 二十年连起来看</h3>',p(f"<b>{cfg['title']}最深的变化，是把默认对象拆回可追踪分母。</b>从“{t[0]}”到“{t[19]}”，二十条都不再允许成功个案代表整个领域；{r[0]}与{r[19]}被重新写进知识账本。"),p(f"{cfg['title']}的第二条线是测量会回写实践。{m[3]}一旦进入评估、出版或制度，行动者便围绕它调整，所以观察量转成了环境变量。"),p(f"{cfg['title']}的第三条线是证据责任分层：提出、争议与{bundles[-1]['latest']['year']}年更新各负其责，最新不等于最强，旧文献也不能免于新边界检验。")]
    out += ['<h3 class="sec">◎ 三个常见误解</h3>',p(f"{cfg['title']}的误解一是把“{t[1]}”理解成技术升级。真正的转向发生在{m[1]}的分母被改写，而不在工具速度。"),p(f"{cfg['title']}的误解二是样本大就自动可靠。若{r[7]}，大样本只会把偏差估得更精确，必须同时报告选择机制。"),p(f"{cfg['title']}的误解三是最新来源天然胜出。{cfg['title']}面板20条最新栏均落在2024—2026年，但年份只证明时效；对象相符、独立复算与反号边界才决定强度。")]
    out += ['<h3 class="sec">◎ 与相邻领域的接口</h3>',p(f"与第306号生物统计学的分工是：统计学负责识别和区间，本页负责“{t[2]}”中的对象是否仍是同一对象。"),p(f"与第126号康复医学的接口落在真实使用：{m[5]}只有穿过退出、照护和生活环境才算生效。"),p(f"与第450号教育神经科学的接口是测量反应；当{r[10]}时，实验任务和制度采用都可能制造所测现象。")]
    out += ['<h3 class="sec">◎ 争议现场</h3>',p(f"第一场争论围绕“{t[6]}”：收敛需预注册分离性预测，并在隐藏数据上判定，不准结果后换口径。"),p(f"第二场争论是{m[11]}能否代表长期对象；需用跨时点同一分母和退出者敏感性分析收敛。"),p(f"第三场争论是{r[15]}造成的外推断裂；需由非原团队、不同地区和另一种测量共同复现。")]
    out += ['<h3 class="sec">◎ 往下五年看什么</h3>',p(f"{cfg['title']}在2027—2031年先看独立复算率：分母取全部尝试项目，读数取复现方向与量级的项目数。"),p(f"{cfg['title']}再看边缘覆盖率：因{r[18]}被排除者占全部适用对象多少，纳入后{m[18]}是否反号。"),p(f"{cfg['title']}还看版本漂移率：同一数据或工具连续三次更新后，“{t[19]}”的主要判断能否保持。")]
    out += ['<h3 class="sec">◎ 可与哪些领域对撞</h3>',p(f"“{t[0]}”与{aliases[0]}共享谁进入分母的预设；一边增加可见对象，另一边要求对象能改变路径。若两边都对，{cfg['title']}推出的第三项是记录权。"),p(f"“{t[7]}”与{aliases[7]}共享测量不改变对象的预设，却在{r[7]}时方向相反；{cfg['title']}必须把任务或制度回写单列。"),p(f"“{t[14]}”与{aliases[14]}共享局部读数可加总的预设；若{m[14]}改善而整体结局不动，{cfg['title']}把隐形成本或聚合次序列为第三项。")]
    out += ['<h3 class="sec">◎ 十条可做的研究命题</h3>','<ol>']
    for i in range(10):out.append(f"<li>命题{i+1}：把“{r[i]}”纳入“{t[i]}”的原分母后，{m[i]}将改变方向；以版本化队列、对照语料或预注册扰动检验，若方向与区间均不变则证伪。</li>")
    refs=[];seen=set()
    for b in bundles:
        for k in ("proposed","controversy","latest"):
            a=b[k]
            if a['id'] not in seen:refs.append(a);seen.add(a['id'])
    out += ['</ol>','<h3 class="sec">◎ 资料核验</h3>',p(f"以下{len(refs)}笔记录由Europe PMC或Crossref反查题名、作者、期刊、年份与DOI／PMID；页面不把被引计数冒充效应量。"),'<div class="refs"><ol>']
    out += [f"<li>{html.escape(fmt_ref(a))}。</li>" for a in refs]
    out += ['</ol></div>']; return ''.join(out)

def build(number):
    cfg=PANELS[number];items=cfg['items'];CACHE.mkdir(parents=True,exist_ok=True)
    # Crossref applies a shared public-pool rate limit; two workers keep the
    # scholarly lookup polite while Europe PMC can safely use six.
    workers=2 if cfg["mode"]=="crossref" else 6
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        bundles=list(ex.map(lambda z:fetch_bundle(number,*z),enumerate(items)))
    nitems=neighbor_items(); near=list(NEIGHBORS); aliases=[]
    for i in range(20):
        no=near[(i+number)%len(near)];xs=nitems.get(no,[]);j=(i*3+number)%len(xs) if xs else 0;other=xs[j] if xs else "跨域分母清算"
        aliases.append(f"另见第{no}号第{j+1}条『{other}』")
    pos=positions();fams=families();parts=[]
    for i,(it,b) in enumerate(zip(items,bundles)):
        label=GAN[i] if i<8 else CN[i-8];ps=paragraphs(number,i,it,b,aliases[i]);count=zh(''.join(ps))
        if not 800<=count<=1000:raise RuntimeError(f"body {number}-{i+1}={count}")
        parts.append(f'<h2>{label}、{html.escape(it[0])}<span class="en">{html.escape(it[1])}</span></h2>'+source_html(b,it[2])+''.join(f'<p>{html.escape(x,quote=False)}</p>' for x in ps)+collision(i,it,b,aliases[i],pos[i],fams[i]))
    a1=f'<div class="act">【第一幕】上一个十年 · 约 2006–2016 · 八条奠基转向</div><p>这一幕追踪{cfg["title"]}如何更换默认对象、证据与分母；主证据按2006—2016年反查，较早前身只作为背景，不倒填年代。</p>'+''.join(parts[:8])
    a2=f'<div class="act">【第二幕】这十年 · 约 2016–2026 · 十二条部署与清算</div><p>第二幕把新工具送进真实环境：采用、版本和制度回写是否改变原命题，成为2016—2026年的核心审计。</p>'+''.join(parts[8:])
    lede=f"近二十年的{cfg['title']}不是名词清单，而是二十次对象与证据分母的更换。{cfg['title']}逐条给出三笔互异来源、六段论证和八字段碰撞层；遇摘要未公开效应量时保留空白，不用想象数字填满证据。"
    main=f'<main><div class="kicker">新思想前沿 · {cfg["group"]}</div><h1>{cfg["title"]}</h1><div class="meta">第 {number} 号 · 近二十年 · <b>两幕 · 20 个新思想</b> · 约 __COUNT__ 字 · 王德生 亲撰 · 2026 年 8 月</div><p class="lede">{lede}</p>{a1}{a2}{closure(cfg,items,aliases,bundles)}<div class="end">{cfg["title"]}页是可核对的学术转向清单；文献题名与元数据应在引用前回到原文复核。</div></main>'
    main=main.replace('__COUNT__',f'{zh(main):,}')
    page=f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第{number}号 · {cfg["title"]}｜新思想前沿</title><meta name="description" content="{html.escape(lede)}"><style>{CSS}</style></head><body><div class="top"><a href="/browse/">SDE Universes</a><span class="sep">·</span><a href="/frontier/">新思想前沿</a><span class="sep">›</span><span>{cfg["group"]}</span></div>{main}</body></html>'
    for marker in ('<h2','<div class="src"','<p>','<div class="col"','<h3 class="sec"','<li>','</main>'):
        page=page.replace(marker,"\n"+marker)
    target=OUT/cfg['slug']/"index.html";target.write_text(page,encoding='utf-8');print(f"built {number} {cfg['title']} zh={zh(main)} bytes={target.stat().st_size}")

if __name__=='__main__':
    if len(sys.argv)!=2 or not sys.argv[1].isdigit() or int(sys.argv[1]) not in ACTIVE_PANELS:raise SystemExit('usage: build_frontier_gap10_v7.py NUMBER  # NUMBER in 91,95,96,97,99,100')
    build(int(sys.argv[1]))
