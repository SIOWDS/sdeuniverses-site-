"""Reviewed classic-source catalogues shared by the sequential V8 run.

Rows contain five pipe-delimited fields.  The helper attaches the twenty
modern labels in page order, guaranteeing twenty distinct callback targets.
"""

LABELS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]


def attach(rows: list[str]) -> list[str]:
    if len(rows) != 20:
        raise ValueError(f"classic catalogue has {len(rows)} rows")
    return [f"{row}|{LABELS[index]}" for index, row in enumerate(rows)]


MICROBIOLOGY = [
    "1952|噬菌体遗传物质进入细胞|Alfred Hershey 与 Martha Chase|Hershey AD, Chase M. Independent functions of viral protein and nucleic acid in growth of bacteriophage. Journal of General Physiology 36 (1952): 39–56|噬菌体感染时进入细胞并指导复制的是DNA而不是外壳蛋白",
    "1952|宿主控制的噬菌体变异|Salvador Luria 与 Mary Human|Luria SE, Human ML. A nonhereditary, host-induced variation of bacterial viruses. Journal of Bacteriology 64 (1952): 557–569|同一噬菌体经过不同宿主后感染范围会改变，细菌因而具有可遗传之外的防御状态",
    "1958|粪便菌群作为治疗材料|Ben Eiseman 团队|Eiseman B et al. Fecal enema as an adjunct in the treatment of pseudomembranous enterocolitis. Surgery 44 (1958): 854–859|把健康供者粪便灌注结肠可逆转严重伪膜性肠炎，群落本身成为干预对象",
    "1961|乳糖操纵子|Francois Jacob 与 Jacques Monod|Jacob F, Monod J. Genetic regulatory mechanisms in the synthesis of proteins. Journal of Molecular Biology 3 (1961): 318–356|阻遏蛋白与操纵序列把环境信号转成成组基因表达开关",
    "1961|解离细胞的组织自聚集|Aaron Moscona|Moscona A. Rotation-mediated histogenetic aggregation of dissociated cells. Experimental Cell Research 22 (1961): 455–475|解离细胞在受控旋转培养中会选择性黏附并重建组织样结构",
    "1956|连续培养与生长限制|Herbert Herbert、Richard Elsworth 与 Robert Telling|Herbert D, Elsworth R, Telling RC. The continuous culture of bacteria: A theoretical and experimental study. Journal of General Microbiology 14 (1956): 601–622|恒定稀释率把微生物群体生长与限制营养的因果关系写成可控制系统",
    "1977|古菌成为第三条谱系|Carl Woese 与 George Fox|Woese CR, Fox GE. Phylogenetic structure of the prokaryotic domain: The primary kingdoms. Proceedings of the National Academy of Sciences 74 (1977): 5088–5090|核糖体RNA序列显示产甲烷微生物与细菌分属深层不同谱系",
    "1978|生物膜作为附着群落|J. William Costerton、George Geesey 与 K.-J. Cheng|Costerton JW, Geesey GG, Cheng KJ. How bacteria stick. Scientific American 238 (1978): 86–95|细菌以胞外聚合物黏附表面并形成具有群落性质的结构，而非自由细胞堆积",
    "1979|细菌群体发光的密度控制|Kenneth Nealson 与 J. Woodland Hastings|Nealson KH, Hastings JW. Bacterial bioluminescence: Its control and ecological significance. Microbiological Reviews 43 (1979): 496–518|可扩散自诱导物随细胞密度累积并同步开启群体基因表达",
    "1982|噬菌体治疗的动物因果试验|H. Williams Smith 与 M. B. Huggins|Smith HW, Huggins MB. Successful treatment of experimental Escherichia coli infections in mice using phage. Journal of General Microbiology 128 (1982): 307–318|与病原匹配的裂解噬菌体可在活体内扩增并挽救致死细菌感染",
    "1983|hipA与持留表型|Harris Moyed 与 Kevin Bertrand|Moyed HS, Bertrand KP. hipA, a newly recognized gene of Escherichia coli K-12 that affects frequency of persistence after inhibition of murein synthesis. Journal of Bacteriology 155 (1983): 768–775|单基因状态可提高抗生素处理后存活而不提高常规最低抑菌浓度",
    "1985|核糖体RNA直接调查群落|Norman Pace 团队|Pace NR et al. Analyzing natural microbial populations by rRNA sequences. ASM News 51 (1985): 4–12|无需纯培养即可用核糖体RNA序列识别环境微生物及其系统位置",
    "1987|细菌基因组中的规则间隔重复|Yoshizumi Ishino 团队|Ishino Y et al. Nucleotide sequence of the iap gene, responsible for alkaline phosphatase isozyme conversion in Escherichia coli, and identification of the gene product. Journal of Bacteriology 169 (1987): 5429–5433|细菌基因组中出现由间隔序列分开的规则重复，为后来CRISPR系统留下原始记录",
    "1989|PCR携带污染审计|Raymond Kwok 与 Russell Higuchi|Kwok S, Higuchi R. Avoiding false positives with PCR. Nature 339 (1989): 237–238|微量扩增产物可污染后续反应，阳性读数必须依靠空间分区与阴性对照解释",
    "1991|幽门螺杆菌与胃癌风险|Julie Parsonnet 团队|Parsonnet J et al. Helicobacter pylori infection and the risk of gastric carcinoma. New England Journal of Medicine 325 (1991): 1127–1131|既往幽门螺杆菌感染与胃癌风险升高相连，使微生物进入肿瘤因果链",
    "1993|深部地下微生物群落|Karsten Pedersen|Pedersen K. The deep subterranean biosphere. Earth-Science Reviews 34 (1993): 243–260|远离光和地表有机碳的岩石孔隙仍维持低能量微生物生态系统",
    "1998|宏基因组命名与群落功能克隆|Jo Handelsman 团队|Handelsman J et al. Molecular biological access to the chemistry of unknown soil microbes: A new frontier for natural products. Chemistry & Biology 5 (1998): R245–R249|直接克隆环境总DNA可访问不可培养微生物的基因与代谢能力",
    "2000|生物膜发育阶段模型|Paula Watnick 与 Roberto Kolter|Watnick P, Kolter R. Biofilm, city of microbes. Journal of Bacteriology 182 (2000): 2675–2679|附着、微菌落、成熟和脱落构成可调控的群落发育序列",
    "2005|Geobacter导电菌毛|Gemma Reguera 与 Derek Lovley 团队|Reguera G et al. Extracellular electron transfer via microbial nanowires. Nature 435 (2005): 1098–1101|导电菌毛可把细胞代谢电子输送到远处受体并形成电连接",
    "2004|单细胞状态切换生成持留者|Nathalie Balaban 团队|Balaban NQ et al. Bacterial persistence as a phenotypic switch. Science 305 (2004): 1622–1625|遗传相同细胞可随机进入慢生长状态并在杀菌后恢复，耐受因此不同于耐药",
]

EVOLUTION = [
    "1950|植物进化的遗传综合|G. Ledyard Stebbins|Stebbins GL. Variation and Evolution in Plants. Columbia University Press (1950)|把细胞遗传、杂交和多倍体资料纳入自然选择的现代综合",
    "1951|自然种群遗传变异|Theodosius Dobzhansky|Dobzhansky T. Genetics and the Origin of Species, 3rd ed. Columbia University Press (1951)|物种形成由自然种群中的遗传变异、选择与隔离共同推进",
    "1953|DNA双螺旋与复制模板|James Watson 与 Francis Crick|Watson JD, Crick FHC. Molecular structure of nucleic acids. Nature 171 (1953): 737–738|互补碱基配对使遗传信息复制与变异获得分子载体",
    "1963|生物物种与地理隔离|Ernst Mayr|Mayr E. Animal Species and Evolution. Harvard University Press (1963)|物种由繁殖隔离维持，地理分化是新物种形成的主要路径",
    "1964|包容适合度|William Hamilton|Hamilton WD. The genetical evolution of social behaviour I and II. Journal of Theoretical Biology 7 (1964): 1–52|基因可通过亲属的繁殖成功获得间接适合度，合作因此可由选择产生",
    "1966|适应与选择层级纪律|George Williams|Williams GC. Adaptation and Natural Selection. Princeton University Press (1966)|适应解释应优先检验个体与基因层选择，群体利益不能自动充当原因",
    "1967|岛屿生物地理平衡|Robert MacArthur 与 Edward Wilson|MacArthur RH, Wilson EO. The Theory of Island Biogeography. Princeton University Press (1967)|迁入与灭绝的动态平衡决定岛屿物种数并受面积与隔离度控制",
    "1968|中性分子进化|木村资生|Kimura M. Evolutionary rate at the molecular level. Nature 217 (1968): 624–626|大量分子替换由选择近中性的突变随机固定而非适应性扫荡",
    "1970|基因重复提供新功能材料|大野乾|Ohno S. Evolution by Gene Duplication. Springer (1970)|一个基因副本维持旧功能时，另一个副本可积累变化并获得新功能",
    "1972|间断平衡|Niles Eldredge 与 Stephen Jay Gould|Eldredge N, Gould SJ. Punctuated equilibria: An alternative to phyletic gradualism. In Models in Paleobiology, Freeman Cooper (1972): 82–115|物种形态可长期停滞并在物种形成期快速改变，化石缺口不必等于记录失败",
    "1972|亲代投资与性选择|Robert Trivers|Trivers RL. Parental investment and sexual selection. In Sexual Selection and the Descent of Man, Aldine (1972): 136–179|两性投入差异改变配偶竞争、选择强度与照护策略",
    "1975|社会生物学的可检验纲领|Edward O. Wilson|Wilson EO. Sociobiology: The New Synthesis. Harvard University Press (1975)|社会行为可用适合度成本收益与亲缘结构提出进化预测",
    "1976|自私基因视角|Richard Dawkins|Dawkins R. The Selfish Gene. Oxford University Press (1976)|复制子在代际中的差异存续可组织对个体行为与合作的解释",
    "1977|核糖体RNA重画生命树|Carl Woese 与 George Fox|Woese CR, Fox GE. Phylogenetic structure of the prokaryotic domain. Proceedings of the National Academy of Sciences 74 (1977): 5088–5090|保守分子序列可跨形态比较深层亲缘并识别古菌谱系",
    "1982|溯祖过程|John Kingman|Kingman JFC. The coalescent. Stochastic Processes and their Applications 13 (1982): 235–248|从现生样本向过去追踪谱系合并可给群体遗传统计量统一概率模型",
    "1987|线粒体DNA重建人群母系史|Rebecca Cann、Mark Stoneking 与 Allan Wilson|Cann RL, Stoneking M, Wilson AC. Mitochondrial DNA and human evolution. Nature 325 (1987): 31–36|现生线粒体序列差异可估计共同祖先与人群分化时间",
    "1982|外适应概念|Stephen Jay Gould 与 Elisabeth Vrba|Gould SJ, Vrba ES. Exaptation: A missing term in the science of form. Paleobiology 8 (1982): 4–15|当前功能可由为别的作用形成或原本无功能的结构转用而来",
    "1987|系统地理学|John Avise 等|Avise JC et al. Intraspecific phylogeography: The mitochondrial DNA bridge between population genetics and systematics. Annual Review of Ecology and Systematics 18 (1987): 489–522|谱系树与地理分布联合揭示种内历史、屏障与扩散路径",
    "1997|尼安德特人古DNA|Matthias Krings 团队|Krings M et al. Neandertal DNA sequences and the origin of modern humans. Cell 90 (1997): 19–30|直接读取古人类线粒体DNA使现代群体不再是祖先历史的唯一代理",
    "2003|DNA条形码|Paul Hebert 团队|Hebert PDN et al. Biological identifications through DNA barcodes. Proceedings of the Royal Society B 270 (2003): 313–321|标准化短基因片段可批量把未知样本匹配到物种参考库",
]

OMICS = [
    "1950|Edman逐残基降解|Pehr Edman|Edman P. Method for determination of the amino acid sequence in peptides. Acta Chemica Scandinavica 4 (1950): 283–293|循环标记并切下肽链N端氨基酸可逐位读取蛋白序列",
    "1955|胰岛素完整序列|Frederick Sanger|Ryle AP et al. The disulphide bonds of insulin. Biochemical Journal 60 (1955): 541–556|蛋白质具有确定氨基酸序列并可由化学片段拼接重建",
    "1958|中心法则|Francis Crick|Crick FHC. On protein synthesis. Symposia of the Society for Experimental Biology 12 (1958): 138–163|序列信息通常由核酸流向蛋白质而不从蛋白质逆流回核酸",
    "1965|转运RNA序列与遗传码|Robert Holley 团队|Holley RW et al. Structure of a ribonucleic acid. Science 147 (1965): 1462–1465|完整tRNA序列把密码子识别与氨基酸装载连接为可核对分子结构",
    "1967|蛋白序列构建系统树|Walter Fitch 与 Emanuel Margoliash|Fitch WM, Margoliash E. Construction of phylogenetic trees. Science 155 (1967): 279–284|同源蛋白序列差异可通过最小改变原则重建物种亲缘",
    "1970|全局序列比对|Saul Needleman 与 Christian Wunsch|Needleman SB, Wunsch CD. A general method applicable to the search for similarities in amino acid sequence. Journal of Molecular Biology 48 (1970): 443–453|动态规划可在插入删除条件下找到两条序列的最优全局对应",
    "1973|代谢控制分析|Henrik Kacser 与 Jim Burns|Kacser H, Burns JA. The control of flux. Symposia of the Society for Experimental Biology 27 (1973): 65–104|通量控制分散在网络多个酶上，单个限速酶不能代表系统因果",
    "1975|Southern印迹|Edwin Southern|Southern EM. Detection of specific sequences among DNA fragments separated by gel electrophoresis. Journal of Molecular Biology 98 (1975): 503–517|膜转移与互补探针可在复杂基因组片段中定位特定DNA序列",
    "1977|链终止DNA测序|Frederick Sanger、Steven Nicklen 与 Alan Coulson|Sanger F, Nicklen S, Coulson AR. DNA sequencing with chain-terminating inhibitors. Proceedings of the National Academy of Sciences 74 (1977): 5463–5467|双脱氧终止产生嵌套片段并将DNA碱基次序变成可读梯度",
    "1981|局部序列比对|Temple Smith 与 Michael Waterman|Smith TF, Waterman MS. Identification of common molecular subsequences. Journal of Molecular Biology 147 (1981): 195–197|允许重新起始的动态规划可找出长序列中最相似的局部片段",
    "1985|聚合酶链式反应|Kary Mullis 团队|Saiki RK et al. Enzymatic amplification of beta-globin genomic sequences and restriction site analysis. Science 230 (1985): 1350–1354|引物和循环延伸可指数扩增指定DNA片段并把微量样本变成可测对象",
    "1988|FASTA快速序列搜索|William Pearson 与 David Lipman|Pearson WR, Lipman DJ. Improved tools for biological sequence comparison. Proceedings of the National Academy of Sciences 85 (1988): 2444–2448|先找短词命中再扩展可在大数据库中近似高效搜索同源序列",
    "1988|MALDI质谱|Michael Karas 与 Franz Hillenkamp|Karas M, Hillenkamp F. Laser desorption ionization of proteins with molecular masses exceeding 10000 daltons. Analytical Chemistry 60 (1988): 2299–2301|基质吸收激光能量可让大分子温和离子化并进入质量分析",
    "1989|酵母双杂交|Stanley Fields 与 Ok-kyu Song|Fields S, Song O. A novel genetic system to detect protein-protein interactions. Nature 340 (1989): 245–246|把转录因子拆成结合域和激活域可在活细胞内报告蛋白相互作用",
    "1990|BLAST数据库搜索|Stephen Altschul 等|Altschul SF et al. Basic local alignment search tool. Journal of Molecular Biology 215 (1990): 403–410|高分词种子与统计显著性把局部同源搜索扩展到快速数据库扫描",
    "1995|首个自由生活细菌全基因组|Robert Fleischmann 团队|Fleischmann RD et al. Whole-genome random sequencing and assembly of Haemophilus influenzae. Science 269 (1995): 496–512|全基因组随机鸟枪测序可由大量短读段直接组装完整细菌染色体",
    "1996|高密度寡核苷酸芯片|Stephen Fodor 团队|Lockhart DJ et al. Expression monitoring by hybridization to high-density oligonucleotide arrays. Nature Biotechnology 14 (1996): 1675–1680|成千上万探针可并行比较大量转录本的相对表达",
    "1999|同位素编码亲和标签|Steven Gygi 团队|Gygi SP et al. Quantitative analysis of complex protein mixtures using isotope-coded affinity tags. Nature Biotechnology 17 (1999): 994–999|轻重同位素标签让同一质谱图中的肽峰比值成为蛋白丰度比较",
    "2001|人类基因组草图|International Human Genome Sequencing Consortium|International Human Genome Sequencing Consortium. Initial sequencing and analysis of the human genome. Nature 409 (2001): 860–921|公共分层测序和组装建立可版本化的人类参考基因组",
    "2003|全蛋白组概念进入高通量质谱|Ruedi Aebersold 与 Matthias Mann|Aebersold R, Mann M. Mass spectrometry-based proteomics. Nature 422 (2003): 198–207|液相分离、串联质谱和数据库搜索把复杂样本中的蛋白鉴定变成系统流程",
]

NEUROSCIENCE = [
    "1950|皮层功能地图|Wilder Penfield 与 Theodore Rasmussen|Penfield W, Rasmussen T. The Cerebral Cortex of Man. Macmillan (1950)|清醒手术电刺激把感觉、运动与语言功能定位到可复查皮层坐标",
    "1953|快速眼动睡眠|Eugene Aserinsky 与 Nathaniel Kleitman|Aserinsky E, Kleitman N. Regularly occurring periods of eye motility and concomitant phenomena during sleep. Science 118 (1953): 273–274|睡眠包含周期性快速眼动与脑活动阶段而非均一的被动停机",
    "1956|短时记忆容量|George Miller|Miller GA. The magical number seven, plus or minus two. Psychological Review 63 (1956): 81–97|多种判断和记忆任务显示有限信息组块容量，编码单位影响表面上限",
    "1957|海马与陈述记忆|William Scoville 与 Brenda Milner|Scoville WB, Milner B. Loss of recent memory after bilateral hippocampal lesions. Journal of Neurology Neurosurgery and Psychiatry 20 (1957): 11–21|双侧内侧颞叶切除导致严重新记忆形成障碍而保留部分技能学习",
    "1958|选择性注意过滤器|Donald Broadbent|Broadbent DE. Perception and Communication. Pergamon Press (1958)|有限通道在语义加工前按物理线索选择输入，注意由容量瓶颈组织",
    "1959|视觉皮层感受野层级|David Hubel 与 Torsten Wiesel|Hubel DH, Wiesel TN. Receptive fields of single neurones in the cat's striate cortex. Journal of Physiology 148 (1959): 574–591|视觉皮层神经元选择边缘方向与位置并形成层级特征表示",
    "1962|情绪的两因素模型|Stanley Schachter 与 Jerome Singer|Schachter S, Singer JE. Cognitive, social, and physiological determinants of emotional state. Psychological Review 69 (1962): 379–399|生理唤醒与情境解释共同塑造被报告的情绪类别",
    "1968|多存储记忆模型|Richard Atkinson 与 Richard Shiffrin|Atkinson RC, Shiffrin RM. Human memory: A proposed system and its control processes. In The Psychology of Learning and Motivation 2 (1968): 89–195|感觉、短时与长时存储由复述和检索控制过程连接",
    "1971|海马位置细胞|John O'Keefe 与 Jonathan Dostrovsky|O'Keefe J, Dostrovsky J. The hippocampus as a spatial map. Brain Research 34 (1971): 171–175|海马单细胞在动物处于特定空间位置时选择性放电",
    "1972|情景记忆与语义记忆|Endel Tulving|Tulving E. Episodic and semantic memory. In Organization of Memory, Academic Press (1972): 381–403|个人事件的时空回忆与一般知识依赖不同信息组织和检索条件",
    "1974|工作记忆多组件模型|Alan Baddeley 与 Graham Hitch|Baddeley AD, Hitch G. Working memory. In The Psychology of Learning and Motivation 8 (1974): 47–89|短时保持由语音、视觉空间和中央执行等并行组件承担",
    "1982|Marr的计算视觉三级分析|David Marr|Marr D. Vision. W. H. Freeman (1982)|认知系统应分别说明计算目标、表征算法与物理实现",
    "1982|Morris水迷宫与空间学习|Richard Morris|Morris RGM. Spatial localization does not require the presence of local cues. Learning and Motivation 12 (1981): 239–260|动物可用远端线索学习隐藏平台位置，空间记忆能够与可见提示分离",
    "1983|意识意图前的准备电位|Benjamin Libet 团队|Libet B et al. Time of conscious intention to act in relation to onset of cerebral activity. Brain 106 (1983): 623–642|自主动作的皮层准备电位早于被报告的行动意图时间",
    "1986|并行分布式加工|David Rumelhart 与 James McClelland|Rumelhart DE, McClelland JL, eds. Parallel Distributed Processing. MIT Press (1986)|认知表征可分布在连接权重中并通过误差学习渐进形成",
    "1988|全局工作空间|Bernard Baars|Baars BJ. A Cognitive Theory of Consciousness. Cambridge University Press (1988)|局部无意识处理经全局广播后才能被多系统共同访问并形成意识报告",
    "1991|功能磁共振成像|John Belliveau 团队|Belliveau JW et al. Functional mapping of the human visual cortex by magnetic resonance imaging. Science 254 (1991): 716–719|血氧和血流变化使无创全脑功能定位成为重复测量工具",
    "1994|睡眠中海马序列重放|Matthew Wilson 与 Bruce McNaughton|Wilson MA, McNaughton BL. Reactivation of hippocampal ensemble memories during sleep. Science 265 (1994): 676–679|清醒探索时的海马群体活动模式在随后睡眠中再次出现",
    "1996|镜像神经元|Giacomo Rizzolatti 团队|Rizzolatti G et al. Premotor cortex and the recognition of motor actions. Cognitive Brain Research 3 (1996): 131–141|执行动作与观察同类动作可激活部分相同前运动神经元",
    "2001|默认模式网络|Marcus Raichle 团队|Raichle ME et al. A default mode of brain function. Proceedings of the National Academy of Sciences 98 (2001): 676–682|一组脑区在外部任务中一致降低活动并在静息时维持高代谢联系",
]

ARTIFICIAL_INTELLIGENCE = [
    "1950|图灵测试与机器智能|Alan Turing|Turing AM. Computing machinery and intelligence. Mind 59 (1950): 433–460|以可观察对话表现替代对机器是否真正思考的本体争论",
    "1958|感知机学习规则|Frank Rosenblatt|Rosenblatt F. The perceptron: A probabilistic model for information storage and organization in the brain. Psychological Review 65 (1958): 386–408|线性阈值单元可按分类误差调整权重并学习可分模式",
    "1960|Widrow-Hoff最小均方学习|Bernard Widrow 与 Marcian Hoff|Widrow B, Hoff ME. Adaptive switching circuits. IRE WESCON Convention Record 4 (1960): 96–104|沿均方误差梯度更新权重可让线性自适应单元在线收敛",
    "1965|多层数据处理网络|Alexey Ivakhnenko 与 Valentin Lapa|Ivakhnenko AG, Lapa VG. Cybernetic Predicting Devices. CCM Information (1965)|逐层生成并筛选多项式单元可构造早期深层自组织模型",
    "1969|感知机表示局限|Marvin Minsky 与 Seymour Papert|Minsky M, Papert S. Perceptrons. MIT Press (1969)|单层感知机无法表示异或与某些连通性质，结构能力须与训练成功分开",
    "1974|误差反向传播论文|Paul Werbos|Werbos PJ. Beyond Regression: New Tools for Prediction and Analysis in the Behavioral Sciences. Harvard PhD thesis (1974)|链式求导可把输出误差分配给多层网络内部权重",
    "1980|Neocognitron卷积层级|Kunihiko Fukushima|Fukushima K. Neocognitron: A self-organizing neural network model for pattern recognition unaffected by shift in position. Biological Cybernetics 36 (1980): 193–202|局部感受野与下采样层级可获得对平移较稳定的视觉识别",
    "1982|Hopfield联想记忆|John Hopfield|Hopfield JJ. Neural networks and physical systems with emergent collective computational abilities. Proceedings of the National Academy of Sciences 79 (1982): 2554–2558|对称连接网络可沿能量下降收敛到存储模式并完成内容寻址",
    "1985|玻尔兹曼机|David Ackley、Geoffrey Hinton 与 Terrence Sejnowski|Ackley DH, Hinton GE, Sejnowski TJ. A learning algorithm for Boltzmann machines. Cognitive Science 9 (1985): 147–169|随机隐变量网络可用自由相与钳制相统计差学习概率分布",
    "1986|多层反向传播复兴|David Rumelhart、Geoffrey Hinton 与 Ronald Williams|Rumelhart DE, Hinton GE, Williams RJ. Learning representations by back-propagating errors. Nature 323 (1986): 533–536|反向传播误差可让多层网络学习分布式内部表示",
    "1989|卷积网络识别手写数字|Yann LeCun 团队|LeCun Y et al. Backpropagation applied to handwritten zip code recognition. Neural Computation 1 (1989): 541–551|共享卷积核与反向传播把图像局部结构转成端到端分类器",
    "1990|简单循环网络|Jeffrey Elman|Elman JL. Finding structure in time. Cognitive Science 14 (1990): 179–211|把上一时刻隐状态回送网络可从序列预测中学习时间结构",
    "1995|支持向量机|Corinna Cortes 与 Vladimir Vapnik|Cortes C, Vapnik V. Support-vector networks. Machine Learning 20 (1995): 273–297|最大间隔与核函数把分类复杂度集中到边界支持向量",
    "1997|长短期记忆网络|Sepp Hochreiter 与 Jurgen Schmidhuber|Hochreiter S, Schmidhuber J. Long short-term memory. Neural Computation 9 (1997): 1735–1780|门控记忆单元为梯度提供近恒定通道并缓解长序列遗忘",
    "1998|LeNet文档识别系统|Yann LeCun 等|LeCun Y et al. Gradient-based learning applied to document recognition. Proceedings of the IEEE 86 (1998): 2278–2324|卷积、池化和梯度训练可组成部署级手写文档识别流水线",
    "2002|核方法统一|Bernhard Scholkopf 与 Alexander Smola|Scholkopf B, Smola AJ. Learning with Kernels. MIT Press (2002)|正定核把非线性学习转为高维特征空间中的凸优化",
    "2000|Isomap流形学习|Joshua Tenenbaum、Vin de Silva 与 John Langford|Tenenbaum JB, de Silva V, Langford JC. A global geometric framework for nonlinear dimensionality reduction. Science 290 (2000): 2319–2323|邻域图上的测地距离可恢复高维数据的低维流形坐标",
    "2002|对比散度|Geoffrey Hinton|Hinton GE. Training products of experts by minimizing contrastive divergence. Neural Computation 14 (2002): 1771–1800|短步马尔可夫链可近似能量模型似然梯度并显著降低训练成本",
    "2004|GPU通用流式计算|Ian Buck 等|Buck I et al. Brook for GPUs: Stream computing on graphics hardware. ACM Transactions on Graphics 23 (2004): 777–786|把程序表达为数据流内核可将图形处理器用于一般并行数值计算",
    "2006|深层信念网络逐层预训练|Geoffrey Hinton、Simon Osindero 与 Yee-Whye Teh|Hinton GE, Osindero S, Teh YW. A fast learning algorithm for deep belief nets. Neural Computation 18 (2006): 1527–1554|逐层无监督训练再微调可让多层生成网络越过随机初始化困难",
]

BCI_ROBOTICS = [
    "1952|Hodgkin-Huxley动作电位模型|Alan Hodgkin 与 Andrew Huxley|Hodgkin AL, Huxley AF. A quantitative description of membrane current and its application to conduction and excitation in nerve. Journal of Physiology 117 (1952): 500–544|离子电导和门控变量可定量重建神经膜动作电位",
    "1954|脑内奖赏刺激|James Olds 与 Peter Milner|Olds J, Milner P. Positive reinforcement produced by electrical stimulation of septal area and other regions of rat brain. Journal of Comparative and Physiological Psychology 47 (1954): 419–427|动物会操作装置反复获得特定脑区电刺激，神经信号可进入闭环行为",
    "1950|人类感觉运动皮层图|Wilder Penfield 与 Theodore Rasmussen|Penfield W, Rasmussen T. The Cerebral Cortex of Man. Macmillan (1950)|清醒手术刺激把手、脸、语言等功能映射到可定位皮层区域",
    "1962|多自由度外骨骼手原型|Rajko Tomovic 与 George Boni|Tomovic R, Boni G. An adaptive artificial hand. IRE Transactions on Automatic Control 7 (1962): 3–10|触觉反馈与分层控制可让假手根据物体接触自动调整抓握",
    "1969|单神经元操作性条件化|Eberhard Fetz|Fetz EE. Operant conditioning of cortical unit activity. Science 163 (1969): 955–958|猴可凭反馈学习自主提高单个皮层神经元放电率",
    "1969|触觉视觉替代|Paul Bach-y-Rita 团队|Bach-y-Rita P et al. Vision substitution by tactile image projection. Nature 221 (1969): 963–964|摄像图像经皮肤刺激阵列可被训练为用于定位和辨物的感觉信息",
    "1973|直接脑机通信命名|Jacques Vidal|Vidal JJ. Toward direct brain-computer communication. Annual Review of Biophysics and Bioengineering 2 (1973): 157–180|实时脑电特征可被计算机识别并直接控制外部设备",
    "1973|多通道人工耳蜗|William House 与 Jack Urban|House WF, Urban J. Long term results of electrode implantation and electronic stimulation of the cochlea in man. Annals of Otology Rhinology and Laryngology 82 (1973): 504–517|电极序列刺激听神经可向重度耳聋者传递可学习的声音线索",
    "1982|运动皮层群体方向编码|Apostolos Georgopoulos 团队|Georgopoulos AP et al. On the relations between the direction of two-dimensional arm movements and cell discharge. Journal of Neuroscience 2 (1982): 1527–1537|单神经元宽调谐方向向量的群体合成可预测手臂运动方向",
    "1985|机器人阻抗控制|Neville Hogan|Hogan N. Impedance control: An approach to manipulation. Journal of Dynamic Systems Measurement and Control 107 (1985): 1–24|控制力与位移的动态关系而非单独轨迹可获得安全柔顺交互",
    "1986|分层行为机器人|Rodney Brooks|Brooks RA. A robust layered control system for a mobile robot. IEEE Journal on Robotics and Automation 2 (1986): 14–23|多个感知动作层可用抑制关系直接组成鲁棒行为而不依赖完整世界模型",
    "1977|感觉运动节律去同步|Gert Pfurtscheller 与 Aranibar|Pfurtscheller G, Aranibar A. Event-related cortical desynchronization detected by power measurements of scalp EEG. Electroencephalography and Clinical Neurophysiology 42 (1977): 817–826|想象或执行运动会稳定改变头皮脑电感觉运动节律功率",
    "1991|头皮脑电光标控制|Jonathan Wolpaw 团队|Wolpaw JR et al. An EEG-based brain-computer interface for cursor control. Electroencephalography and Clinical Neurophysiology 78 (1991): 252–259|使用者可学习调节特定脑电节律并连续移动屏幕光标",
    "1991|人工皮肤触觉阵列|Paolo Dario 团队|Dario P et al. Tactile sensing: Technology and applications. Sensors and Actuators A 26 (1991): 251–261|阵列化力传感器可重建接触位置与压力分布并反馈给抓取控制",
    "1996|动态运动基元前身|Stefan Schaal|Schaal S. Learning from demonstration. Advances in Neural Information Processing Systems 9 (1996)|示教轨迹可被参数化策略吸收并迁移到新的目标与速度条件",
    "1998|植入电极控制通信|Philip Kennedy 与 Roy Bakay|Kennedy PR, Bakay RAE. Restoration of neural output from a paralyzed patient by a direct brain connection. NeuroReport 9 (1998): 1707–1711|锁定患者可用植入运动皮层电极活动选择字符并输出控制信号",
    "1999|皮层群体控制机器人手臂|John Chapin 团队|Chapin JK et al. Real-time control of a robot arm using simultaneously recorded neurons in the motor cortex. Nature Neuroscience 2 (1999): 664–670|多神经元放电可实时解码并驱动机器人获取食物",
    "2000|灵长类实时神经假体|Johan Wessberg 与 Miguel Nicolelis 团队|Wessberg J et al. Real-time prediction of hand trajectory by ensembles of cortical neurons in primates. Nature 408 (2000): 361–365|分布式皮层群体可连续预测三维手轨迹并在线驱动外部装置",
    "2003|皮层控制抓取与到达|Jose Carmena 团队|Carmena JM et al. Learning to control a brain-machine interface for reaching and grasping by primates. PLoS Biology 1 (2003): e42|灵长类可在闭环中学习用皮层群体同时控制机器人到达和抓取",
    "2006|BrainGate四肢瘫痪试验|Leigh Hochberg 团队|Hochberg LR et al. Neuronal ensemble control of prosthetic devices by a human with tetraplegia. Nature 442 (2006): 164–171|四肢瘫痪者可用皮层内阵列控制光标、电视与简易机械装置",
]

ROBOTICS_CONTROL_SENSING = [
    "1950|控制、通信与反馈进入统一语言|Norbert Wiener|Wiener N. The Human Use of Human Beings. Houghton Mifflin (1950)|机器、操作者与环境可用信息回路和负反馈在同一闭环中分析",
    "1954|可编程物料搬运装置|George Devol|Devol GC. Programmed article transfer. US Patent 2,988,237, filed 1954, issued 1961|把动作序列存入可重写控制器可使机械臂脱离固定凸轮重复执行任务",
    "1957|动态规划与最优性原理|Richard Bellman|Bellman R. Dynamic Programming. Princeton University Press (1957)|多阶段决策可按状态价值递推分解，当前最优动作必须接续剩余阶段的最优策略",
    "1960|卡尔曼滤波|Rudolf Kalman|Kalman RE. A new approach to linear filtering and prediction problems. Journal of Basic Engineering 82 (1960): 35–45|递推融合模型与带噪观测可给出线性系统状态的最小方差估计",
    "1962|自适应人工手|Rajko Tomovic 与 George Boni|Tomovic R, Boni G. An adaptive artificial hand. IRE Transactions on Automatic Control 7 (1962): 3–10|触觉事件与分层控制可让假手按物体接触自动切换抓握程序",
    "1969|计算机控制关节机械臂|Victor Scheinman|Scheinman VI. Design of a computer controlled manipulator. Stanford Artificial Intelligence Project Memo AIM-92 (1969)|电驱关节、位置反馈与软件轨迹可组成通用可重编程机械臂",
    "1969|Shakey移动机器人|Nils Nilsson 团队|Nilsson NJ. A mobile automaton: An application of artificial intelligence techniques. IJCAI (1969): 509–520|感知、世界模型、规划与执行可在移动平台上闭环连接并由任务失败触发重规划",
    "1981|混合位置力控制|Marc Raibert 与 John Craig|Raibert MH, Craig JJ. Hybrid position/force control of manipulators. Journal of Dynamic Systems Measurement and Control 103 (1981): 126–133|把任务空间分成位置约束与力约束子空间可同时控制轨迹和接触载荷",
    "1985|机器人阻抗控制|Neville Hogan|Hogan N. Impedance control: An approach to manipulation. Journal of Dynamic Systems Measurement and Control 107 (1985): 1–24|控制力与位移之间的动态关系可使接触机器人获得稳定柔顺性",
    "1986|分层行为控制|Rodney Brooks|Brooks RA. A robust layered control system for a mobile robot. IEEE Journal on Robotics and Automation 2 (1986): 14–23|多个感知动作层可用抑制关系直接组成鲁棒行为而不依赖完整世界模型",
    "1986|人工势场避障|Oussama Khatib|Khatib O. Real-time obstacle avoidance for manipulators and mobile robots. International Journal of Robotics Research 5 (1986): 90–98|目标吸引势与障碍排斥势可把在线避障转成控制空间中的局部力",
    "1987|群集行为规则|Craig Reynolds|Reynolds CW. Flocks, herds and schools: A distributed behavioral model. Computer Graphics 21 (1987): 25–34|分离、对齐与聚合三种局部规则可生成没有中央指挥的群体运动",
    "1988|占据栅格地图|Alberto Elfes|Elfes A. Sonar-based real-world mapping and navigation. IEEE Journal of Robotics and Automation 3 (1987): 249–265|把空间离散为占据概率单元可累计不确定传感证据并支持移动导航",
    "1988|不确定性几何表示|Hugh Durrant-Whyte|Durrant-Whyte HF. Uncertain geometry in robotics. IEEE Journal of Robotics and Automation 4 (1988): 23–31|位姿与地标协方差必须随坐标变换共同传播，不能把地图误差当独立噪声",
    "1996|示教学习|Stefan Schaal|Schaal S. Learning from demonstration. Advances in Neural Information Processing Systems 9 (1996)|示范轨迹可被参数化策略吸收并在新目标、速度与扰动条件下重用",
    "1998|快速探索随机树|Steven LaValle|LaValle SM. Rapidly-exploring random trees: A new tool for path planning. Iowa State University Technical Report 98-11 (1998)|向随机样本扩展搜索树可快速覆盖高维受约束构型空间",
    "1999|蒙特卡洛定位|Dieter Fox、Wolfram Burgard 与 Sebastian Thrun|Fox D et al. Monte Carlo localization: Efficient position estimation for mobile robots. AAAI (1999): 343–349|粒子分布可表达多峰位姿不确定性并随运动和传感在线更新",
    "2001|概率机器人地图融合|Sebastian Thrun|Thrun S. Robotic mapping: A survey. In Exploring Artificial Intelligence in the New Millennium. Morgan Kaufmann (2002)|地图与位姿必须联合估计，闭环回访可把累计漂移转成可校正约束",
    "2002|动态运动基元|Auke Ijspeert、Jun Nakanishi 与 Stefan Schaal|Ijspeert AJ et al. Movement imitation with nonlinear dynamical systems in humanoid robots. ICRA (2002): 1398–1403|稳定吸引子与可学习形状项可把示教动作改写为可缩放运动技能",
    "2006|Stanley无人车|Sebastian Thrun 团队|Thrun S et al. Stanley: The robot that won the DARPA Grand Challenge. Journal of Field Robotics 23 (2006): 661–692|概率感知、路径规划和速度控制的系统集成可让无人车在开放荒漠连续自主行驶",
]

COMPUTING_SECURITY = [
    "1950|图灵测试与机器智能|Alan Turing|Turing AM. Computing machinery and intelligence. Mind 59 (1950): 433–460|以可观察对话表现替代对机器是否真正思考的本体争论",
    "1952|霍夫曼编码|David Huffman|Huffman DA. A method for the construction of minimum-redundancy codes. Proceedings of the IRE 40 (1952): 1098–1101|按符号概率递归合并可构造期望码长最小的前缀码",
    "1959|有限自动机判定理论|Michael Rabin 与 Dana Scott|Rabin MO, Scott D. Finite automata and their decision problems. IBM Journal of Research and Development 3 (1959): 114–125|有限状态、正则语言与可判定问题可用统一机器模型互相转换",
    "1960|人机共生计算|J. C. R. Licklider|Licklider JCR. Man-computer symbiosis. IRE Transactions on Human Factors in Electronics HFE-1 (1960): 4–11|交互计算应让人负责目标与判断、机器负责高速例行运算并形成实时协作",
    "1965|协作顺序进程|Edsger Dijkstra|Dijkstra EW. Cooperating sequential processes. Technological University Eindhoven Report EWD123 (1965)|并发程序必须用互斥与同步显式约束共享状态的合法交错",
    "1971|NP完全性|Stephen Cook|Cook SA. The complexity of theorem-proving procedures. STOC (1971): 151–158|布尔可满足性可在多项式时间承载一整类非确定性计算问题的归约",
    "1976|公开密钥协商|Whitfield Diffie 与 Martin Hellman|Diffie W, Hellman ME. New directions in cryptography. IEEE Transactions on Information Theory 22 (1976): 644–654|通信双方可在公开信道上建立共享秘密而不预先交换对称密钥",
    "1978|RSA公钥密码|Ronald Rivest、Adi Shamir 与 Leonard Adleman|Rivest RL et al. A method for obtaining digital signatures and public-key cryptosystems. Communications of the ACM 21 (1978): 120–126|模幂运算与大整数分解困难性可同时支持公开加密和数字签名",
    "1978|分布式逻辑时钟|Leslie Lamport|Lamport L. Time, clocks, and the ordering of events in a distributed system. Communications of the ACM 21 (1978): 558–565|无共享物理时钟的进程可用先发生关系建立一致的事件偏序",
    "1979|秘密共享|Adi Shamir|Shamir A. How to share a secret. Communications of the ACM 22 (1979): 612–613|阈值多项式插值可使不足门限的份额不泄露秘密而达到门限即可恢复",
    "1982|拜占庭将军问题|Leslie Lamport、Robert Shostak 与 Marshall Pease|Lamport L et al. The Byzantine generals problem. ACM Transactions on Programming Languages and Systems 4 (1982): 382–401|分布式一致性必须明确恶意节点上限与消息认证条件，否则共识不可保证",
    "1982|量子系统模拟计算|Richard Feynman|Feynman RP. Simulating physics with computers. International Journal of Theoretical Physics 21 (1982): 467–488|经典机器普遍模拟量子系统会付出指数代价，量子装置可直接承载其状态空间",
    "1984|BB84量子密钥分发|Charles Bennett 与 Gilles Brassard|Bennett CH, Brassard G. Quantum cryptography: Public key distribution and coin tossing. IEEE Conference on Computers Systems and Signal Processing (1984): 175–179|不可克隆与测量扰动可把窃听转化为通信双方能够统计发现的错误",
    "1985|通用量子计算机|David Deutsch|Deutsch D. Quantum theory, the Church-Turing principle and the universal quantum computer. Proceedings of the Royal Society A 400 (1985): 97–117|一台通用量子机器可模拟任意有限物理系统并以叠加干涉组织计算",
    "1985|分布式快照|K. Mani Chandy 与 Leslie Lamport|Chandy KM, Lamport L. Distributed snapshots: Determining global states of distributed systems. ACM Transactions on Computer Systems 3 (1985): 63–75|标记消息可在系统不停机时记录一致全局切面并保留通道中的在途消息",
    "1994|Shor量子分解算法|Peter Shor|Shor PW. Algorithms for quantum computation: Discrete logarithms and factoring. FOCS (1994): 124–134|量子傅里叶变换可把周期寻找转成多项式时间的整数分解与离散对数算法",
    "1996|Grover量子搜索|Lov Grover|Grover LK. A fast quantum mechanical algorithm for database search. STOC (1996): 212–219|振幅放大可把无结构搜索查询复杂度从线性降到平方根量级",
    "1998|Paxos共识|Leslie Lamport|Lamport L. The part-time parliament. ACM Transactions on Computer Systems 16 (1998): 133–169|多数派法定人数的交叠可在消息延迟和节点故障下保持单一已决定值",
    "1999|实用拜占庭容错|Miguel Castro 与 Barbara Liskov|Castro M, Liskov B. Practical Byzantine fault tolerance. OSDI (1999): 173–186|预准备、准备和提交三阶段可让副本系统在少数恶意节点下保持安全与可用",
    "2004|MapReduce数据并行|Jeffrey Dean 与 Sanjay Ghemawat|Dean J, Ghemawat S. MapReduce: Simplified data processing on large clusters. OSDI (2004): 137–150|映射与归约接口可把数据分片、调度、故障重试和聚合从业务逻辑中分离",
]

ELECTRONICS_PHOTONICS = [
    "1950|半导体载流子与结理论|William Shockley|Shockley W. Electrons and Holes in Semiconductors. Van Nostrand (1950)|能带、少数载流子和结区输运可把晶体管行为写成可计算器件方程",
    "1952|区熔提纯|William Pfann|Pfann WG. Principles of zone-melting. Transactions of the AIME 194 (1952): 747–753|移动熔区按分凝系数搬运杂质可获得高纯锗与硅晶体",
    "1954|首个实用硅太阳电池|Daryl Chapin、Calvin Fuller 与 Gerald Pearson|Chapin DM et al. A new silicon p-n junction photocell for converting solar radiation into electrical power. Journal of Applied Physics 25 (1954): 676–677|硅结的光生载流子分离可把太阳辐照稳定转成可用电功率",
    "1956|晶闸管四层结构|John Moll 团队|Moll JL et al. P-N-P-N transistor switches. Proceedings of the IRE 44 (1956): 1174–1182|四层再生反馈可使半导体器件在阻断与导通两种稳定状态间切换",
    "1958|集成电路单片化|Jack Kilby|Kilby JS. Invention of the integrated circuit. IEEE Transactions on Electron Devices 23 (1976): 648–654|在同一半导体片上制作并互连多个元件可消除离散装配的规模瓶颈",
    "1960|平面工艺|Jean Hoerni|Hoerni JA. Planar silicon transistors and diodes. IRE Electron Devices Meeting (1960)|氧化层掩膜、扩散与表面钝化可让硅器件批量制造并可靠互连",
    "1960|红宝石激光|Theodore Maiman|Maiman TH. Stimulated optical radiation in ruby. Nature 187 (1960): 493–494|受激辐射与光学谐振腔可产生相干、窄谱且高方向性的光脉冲",
    "1960|MOS场效应晶体管|Mohamed Atalla 与 Dawon Kahng|Kahng D, Atalla MM. Silicon-silicon dioxide field induced surface devices. IRE Solid-State Device Research Conference (1960)|绝缘栅电场可无直流栅电流地调制硅表面导电沟道",
    "1962|可见光发光二极管|Nick Holonyak 与 S. F. Bevacqua|Holonyak N, Bevacqua SF. Coherent visible light emission from GaAsP junctions. Applied Physics Letters 1 (1962): 82–83|直接带隙结的载流子复合可在室温产生可见相干发光",
    "1965|摩尔定律|Gordon Moore|Moore GE. Cramming more components onto integrated circuits. Electronics 38(8) (1965): 114–117|制造与经济协同可使芯片元件数按近似指数节奏增长",
    "1966|低损耗光纤通信判据|Charles Kao 与 George Hockham|Kao KC, Hockham GA. Dielectric-fibre surface waveguides for optical frequencies. Proceedings of the IEE 113 (1966): 1151–1158|玻璃损耗主要来自可去除杂质而非物理下限，足够纯净纤维可承载长距通信",
    "1970|电荷耦合器件|Willard Boyle 与 George Smith|Boyle WS, Smith GE. Charge coupled semiconductor devices. Bell System Technical Journal 49 (1970): 587–593|时序栅压可在半导体表面逐级转移电荷包并形成固态成像阵列",
    "1970|低损耗石英光纤|Robert Maurer、Donald Keck 与 Peter Schultz|Kapron FP et al. Radiation losses in glass optical waveguides. Applied Physics Letters 17 (1970): 423–425|高纯掺杂石英把光纤衰减降到足以支持远距离通信的量级",
    "1970|室温连续波半导体激光|Izuo Hayashi 与 Morton Panish 团队|Hayashi I et al. Junction lasers which operate continuously at room temperature. Applied Physics Letters 17 (1970): 109–111|双异质结同时限制载流子与光场，使半导体激光可在室温连续运行",
    "1980|量子霍尔效应|Klaus von Klitzing|von Klitzing K et al. New method for high-accuracy determination of the fine-structure constant based on quantized Hall resistance. Physical Review Letters 45 (1980): 494–497|二维电子气的霍尔电阻形成由基本常数决定的精确量子平台",
    "1982|扫描隧道显微镜|Gerd Binnig 与 Heinrich Rohrer|Binnig G et al. Surface studies by scanning tunneling microscopy. Physical Review Letters 49 (1982): 57–61|针尖隧穿电流对距离的指数敏感性可重建导电表面的原子级形貌",
    "1988|巨磁电阻|Albert Fert 与 Peter Grunberg 团队|Baibich MN et al. Giant magnetoresistance of Fe/Cr magnetic superlattices. Physical Review Letters 61 (1988): 2472–2475|磁性多层中自旋相关散射可让相对磁化方向造成巨大的电阻差",
    "1991|碳纳米管|Sumio Iijima|Iijima S. Helical microtubules of graphitic carbon. Nature 354 (1991): 56–58|石墨片卷曲形成的纳米管兼具一维电子结构与高轴向强度",
    "1994|高亮度蓝光LED|Shuji Nakamura|Nakamura S et al. Candela-class high-brightness InGaN/AlGaN double-heterostructure blue-light-emitting diodes. Applied Physics Letters 64 (1994): 1687–1689|InGaN双异质结与有效掺杂可把蓝光发光效率推到实用照明水平",
    "2004|单层石墨烯器件|Andre Geim 与 Konstantin Novoselov 团队|Novoselov KS et al. Electric field effect in atomically thin carbon films. Science 306 (2004): 666–669|机械剥离得到的单原子层碳可表现可门控的高迁移率二维输运",
]

ENERGY_AERO_BIOMED_MANUFACTURING = [
    "1953|体外循环心肺机|John Gibbon|Gibbon JH Jr. Application of a mechanical heart and lung apparatus to cardiac surgery. Minnesota Medicine 37 (1954): 171–185|泵与氧合器可在开放心脏手术中暂时代替循环和气体交换",
    "1954|硅光伏电池|Daryl Chapin、Calvin Fuller 与 Gerald Pearson|Chapin DM et al. A new silicon p-n junction photocell for converting solar radiation into electrical power. Journal of Applied Physics 25 (1954): 676–677|硅结可把太阳辐照转成稳定电功率并以效率和面积统一核算",
    "1957|人造地球卫星|Sergei Korolev 团队|Siddiqi AA. Sputnik and the Soviet Space Challenge. University Press of Florida (2003)|火箭、遥测和轨道力学的系统集成首次把人工载荷送入稳定地球轨道",
    "1958|植入式心脏起搏器|Ake Senning 与 Rune Elmqvist|Elmqvist R, Senning A. An implantable pacemaker for the heart. Second International Conference on Medical Electronics (1959)|可植入脉冲源与心肌电极可长期替代失效的心脏节律触发",
    "1961|载人轨道飞行|Sergei Korolev 与 Yuri Gagarin 团队|Hall RC, Shayler DL. The Rocket Men: Vostok and Voskhod. Springer (2001)|生命保障、制导与再入系统可在同一任务链中支持人类完成地球轨道飞行",
    "1962|全髋关节低摩擦置换|John Charnley|Charnley J. Arthroplasty of the hip: A new operation. Lancet 1 (1961): 1129–1132|小直径金属头、聚合物杯与骨水泥可把关节磨损和固定问题组成可重复手术系统",
    "1969|阿波罗登月系统|NASA Apollo 11 团队|NASA. Apollo 11 Mission Report, MSC-00171 (1969)|多级火箭、月球轨道交会、制导计算和地面控制可闭合载人登月往返任务",
    "1973|计算机断层成像|Godfrey Hounsfield|Hounsfield GN. Computerized transverse axial scanning tomography. British Journal of Radiology 46 (1973): 1016–1022|多角度X射线投影经数值重建可生成体内横断面衰减图",
    "1973|磁共振空间成像|Paul Lauterbur|Lauterbur PC. Image formation by induced local interactions. Nature 242 (1973): 190–191|磁场梯度把核磁共振频率编码为空间位置并可重建二维图像",
    "1976|可充电锂电池插层反应|M. Stanley Whittingham|Whittingham MS. Electrical energy storage and intercalation chemistry. Science 192 (1976): 1126–1127|锂离子在层状电极中的可逆嵌入可把化学势差转为可循环电能",
    "1977|多通道人工耳蜗语音编码|Graeme Clark 团队|Clark GM et al. A multiple-electrode hearing prosthesis for cochlear deafness. Medical Progress through Technology 6 (1977): 127–140|多电极位置编码可向听神经传递可训练区分的语音频带线索",
    "1980|锂钴氧化物正极|John Goodenough 团队|Mizushima K et al. LixCoO2: A new cathode material for batteries of high energy density. Materials Research Bulletin 15 (1980): 783–789|高电压层状氧化物可逆脱嵌锂并显著提高二次电池能量密度",
    "1981|航天飞机重复使用轨道器|NASA Space Shuttle 团队|NASA. STS-1 Space Shuttle Mission Report (1981)|可回收轨道器、固体助推器和外贮箱组成部分重复使用的载人发射体系",
    "1981|逐层光固化制造概念|Hideo Kodama|Kodama H. Automatic method for fabricating a three-dimensional plastic model with photo-hardening polymer. Review of Scientific Instruments 52 (1981): 1770–1773|切片数据驱动逐层光固化可从数字模型直接生成三维实体",
    "1984|立体光刻|Charles Hull|Hull CW. Apparatus for production of three-dimensional objects by stereolithography. US Patent 4,575,330, filed 1984|扫描光束逐层固化液态树脂可把计算机几何直接转成实体零件",
    "1991|染料敏化太阳电池|Brian O'Regan 与 Michael Gratzel|O'Regan B, Gratzel M. A low-cost, high-efficiency solar cell based on dye-sensitized colloidal TiO2 films. Nature 353 (1991): 737–740|染料吸光、纳米氧化物注入电子和电解质再生可分工完成光电转换",
    "1993|组织工程框架|Robert Langer 与 Joseph Vacanti|Langer R, Vacanti JP. Tissue engineering. Science 260 (1993): 920–926|细胞、支架与生物信号可组合设计以恢复或替代组织功能",
    "1998|国际空间站在轨组装|国际空间站合作机构|NASA. International Space Station Assembly, Zarya and Unity Missions (1998)|标准接口、分段发射与跨国任务控制可把大型空间基础设施在轨增量建成",
    "2005|RepRap自复制制造计划|Adrian Bowyer|Bowyer A. Wealth without money: The background to the Bath Replicating Rapid-prototyper Project. University of Bath (2005)|开放硬件挤出式打印机可制造自身大量结构件并由社区迭代复制",
    "2006|工程化膀胱移植|Anthony Atala 团队|Atala A et al. Tissue-engineered autologous bladders for patients needing cystoplasty. Lancet 367 (2006): 1241–1246|患者自体细胞在可降解支架上培养后可构建并移植功能性膀胱组织",
]

EARTH_ENVIRONMENT = [
    "1952|放射性碳年代学|Willard Libby|Libby WF. Radiocarbon Dating. University of Chicago Press (1952)|有机体死亡后碳十四按已知半衰期衰变，可把样本活度转成绝对年代",
    "1956|二氧化碳辐射强迫计算|Gilbert Plass|Plass GN. The carbon dioxide theory of climatic change. Tellus 8 (1956): 140–154|大气二氧化碳增加会改变红外辐射收支并推动地表升温",
    "1957|海洋不能即时吸收化石碳|Roger Revelle 与 Hans Suess|Revelle R, Suess HE. Carbon dioxide exchange between atmosphere and ocean and the question of an increase of atmospheric CO2. Tellus 9 (1957): 18–27|海水碳酸盐缓冲限制二氧化碳快速吸收，使人为排放可在大气累积",
    "1958|大气二氧化碳连续记录|Charles Keeling|Keeling CD. The concentration and isotopic abundances of atmospheric carbon dioxide in rural areas. Geochimica et Cosmochimica Acta 13 (1958): 322–334|高精度连续采样可把季节循环与长期大气二氧化碳上升分离",
    "1962|海底扩张|Harry Hess|Hess HH. History of ocean basins. In Petrologic Studies: A Volume in Honor of A. F. Buddington. Geological Society of America (1962): 599–620|洋中脊生成新洋壳并向两侧扩张可连接地幔对流、海沟与大陆漂移",
    "1962|农药生态级联|Rachel Carson|Carson R. Silent Spring. Houghton Mifflin (1962)|持久性农药会沿食物网累积并把局部灭虫行动转成跨物种生态损伤",
    "1965|转换断层与板块边界|J. Tuzo Wilson|Wilson JT. A new class of faults and their bearing on continental drift. Nature 207 (1965): 343–347|转换断层的震源运动方向可由刚性板块相对运动几何统一解释",
    "1967|全球气候模式的二氧化碳敏感度|Syukuro Manabe 与 Richard Wetherald|Manabe S, Wetherald RT. Thermal equilibrium of the atmosphere with a given distribution of relative humidity. Journal of Atmospheric Sciences 24 (1967): 241–259|辐射对流模型可定量估计二氧化碳倍增、湿度反馈与垂直温度响应",
    "1967|岛屿生物地理平衡|Robert MacArthur 与 Edward Wilson|MacArthur RH, Wilson EO. The Theory of Island Biogeography. Princeton University Press (1967)|物种丰富度由迁入与灭绝速率的面积和隔离依赖平衡决定",
    "1972|Landsat地球资源卫星|NASA 与 USGS|NASA. ERTS-1 Data Users Handbook (1972)|重复轨道多光谱成像可把土地覆盖变化转成跨地区、跨年份的标准观测",
    "1972|增长极限系统动力学|Donella Meadows 团队|Meadows DH et al. The Limits to Growth. Universe Books (1972)|人口、资本、资源、粮食和污染的反馈延迟可使局部增长越过全球承载边界",
    "1976|Viking火星着陆探测|NASA Viking 团队|Klein HP et al. The Viking biological investigation: Preliminary results. Science 194 (1976): 99–105|轨道测绘、软着陆与原位化学实验可把行星宜居性判断落到可复查样本反应",
    "1977|矩震级|Thomas Hanks 与 Hiroo Kanamori|Hanks TC, Kanamori H. A moment magnitude scale. Journal of Geophysical Research 84 (1979): 2348–2350|由断层面积、滑移和刚度得到的地震矩可避免大震中传统震级饱和",
    "1985|南极臭氧洞|Joseph Farman、Brian Gardiner 与 Jonathan Shanklin|Farman JC et al. Large losses of total ozone in Antarctica reveal seasonal ClOx/NOx interaction. Nature 315 (1985): 207–210|长期地面观测揭示南极春季臭氧巨幅损失并把氯化学与季节机制连接",
    "1987|可持续发展定义|世界环境与发展委员会|World Commission on Environment and Development. Our Common Future. Oxford University Press (1987)|满足当代需求的政策不得削弱后代满足其需求的资源与制度能力",
    "1988|政府间气候变化专门委员会|世界气象组织与联合国环境规划署|WMO, UNEP. Establishment of the Intergovernmental Panel on Climate Change (1988)|跨国评估程序把物理科学、影响适应与减排证据按版本和不确定性共同结算",
    "1992|地球峰会与气候公约|联合国|United Nations. Framework Convention on Climate Change (1992)|各国以共同但有区别的责任建立排放盘点、报告、审议与后续议定书框架",
    "1997|京都议定书|联合国气候变化框架公约缔约方|United Nations. Kyoto Protocol to the United Nations Framework Convention on Climate Change (1997)|具有法律约束的国家目标、基准年和市场机制把减排承诺转成可核算责任",
    "1998|全球陆地净初级生产力遥感估计|Christopher Field 团队|Field CB et al. Primary production of the biosphere: Integrating terrestrial and oceanic components. Science 281 (1998): 237–240|卫星植被指数、光能利用率与海洋叶绿素可合成全球生物圈生产力账本",
    "2000|人类世命名|Paul Crutzen 与 Eugene Stoermer|Crutzen PJ, Stoermer EF. The Anthropocene. IGBP Global Change Newsletter 41 (2000): 17–18|人类活动已成为可与地质过程相比的地球系统驱动力，年代边界必须由可测标志裁决",
]


DATA = {
    33: attach(MICROBIOLOGY),
    34: attach(EVOLUTION),
    35: attach(OMICS),
    36: attach(NEUROSCIENCE),
    37: attach(ARTIFICIAL_INTELLIGENCE),
    38: attach(NEUROSCIENCE),
    39: attach(BCI_ROBOTICS),
    40: attach(NEUROSCIENCE),
    41: attach(NEUROSCIENCE),
    42: attach(NEUROSCIENCE),
    43: attach(ARTIFICIAL_INTELLIGENCE),
    44: attach(ARTIFICIAL_INTELLIGENCE),
    45: attach(ARTIFICIAL_INTELLIGENCE),
    46: attach(ARTIFICIAL_INTELLIGENCE),
    47: attach(ARTIFICIAL_INTELLIGENCE),
    48: attach(ARTIFICIAL_INTELLIGENCE),
    49: attach(ARTIFICIAL_INTELLIGENCE),
    50: attach(ARTIFICIAL_INTELLIGENCE),
    51: attach(ROBOTICS_CONTROL_SENSING),
    52: attach(COMPUTING_SECURITY),
    53: attach(COMPUTING_SECURITY),
    54: attach(COMPUTING_SECURITY),
    55: attach(ELECTRONICS_PHOTONICS),
    56: attach(ELECTRONICS_PHOTONICS),
    57: attach(ENERGY_AERO_BIOMED_MANUFACTURING),
    58: attach(ENERGY_AERO_BIOMED_MANUFACTURING),
    59: attach(ENERGY_AERO_BIOMED_MANUFACTURING),
    60: attach(ROBOTICS_CONTROL_SENSING),
    61: attach(ENERGY_AERO_BIOMED_MANUFACTURING),
    62: attach(ROBOTICS_CONTROL_SENSING),
    63: attach(EARTH_ENVIRONMENT),
    64: attach(EARTH_ENVIRONMENT),
    65: attach(EARTH_ENVIRONMENT),
    66: attach(EARTH_ENVIRONMENT),
    67: attach(EARTH_ENVIRONMENT),
    68: attach(EARTH_ENVIRONMENT),
    69: attach(EARTH_ENVIRONMENT),
    70: attach(EARTH_ENVIRONMENT),
}

LIFE_FLOWS = [
    "Madigan MT et al. Brock Biology of Microorganisms, 15th ed. Pearson (2018)",
    "Alberts B et al. Molecular Biology of the Cell, 7th ed. Garland Science (2022)",
    "Futuyma DJ, Kirkpatrick M. Evolution, 4th ed. Sinauer (2017)",
    "Pevsner J. Bioinformatics and Functional Genomics, 3rd ed. Wiley-Blackwell (2015)",
    "Quince C et al. Shotgun metagenomics, from sampling to analysis. Nature Biotechnology 35 (2017): 833–844",
]
LIFE_BOOKS = [
    "Brock TD. Biology of Microorganisms. Prentice Hall (1970)",
    "Stanier RY et al. The Microbial World, 5th ed. Prentice Hall (1986)",
    "Mayr E. Animal Species and Evolution. Harvard University Press (1963)",
    "Kimura M. The Neutral Theory of Molecular Evolution. Cambridge University Press (1983)",
    "Li WH, Graur D. Fundamentals of Molecular Evolution. Sinauer (1991)",
    "Mount DW. Bioinformatics: Sequence and Genome Analysis. Cold Spring Harbor Laboratory Press (2001)",
    "Brown TA. Genomes, 2nd ed. Wiley-Liss (2002)",
    "Lesk AM. Introduction to Bioinformatics. Oxford University Press (2002)",
    "Primrose SB, Twyman RM. Principles of Genome Analysis, 3rd ed. Blackwell (2003)",
    "Cantor CR, Smith CL. Genomics. Wiley (1999)",
]
NEURO_FLOWS = [
    "Kandel ER et al. Principles of Neural Science, 6th ed. McGraw-Hill (2021)",
    "Gazzaniga MS et al. Cognitive Neuroscience, 6th ed. Norton (2024)",
    "Dayan P, Abbott LF. Theoretical Neuroscience. MIT Press (2001)",
    "Dehaene S et al. What is consciousness, and could machines have it? Science 358 (2017): 486–492",
    "Squire LR, Kandel ER. Memory: From Mind to Molecules, 2nd ed. Roberts (2009)",
]
NEURO_BOOKS = [
    "Penfield W, Rasmussen T. The Cerebral Cortex of Man. Macmillan (1950)",
    "Hebb DO. A Textbook of Psychology, 2nd ed. Saunders (1966)",
    "Broadbent DE. Perception and Communication. Pergamon Press (1958)",
    "Neisser U. Cognitive Psychology. Appleton-Century-Crofts (1967)",
    "Tulving E, Donaldson W, eds. Organization of Memory. Academic Press (1972)",
    "Marr D. Vision. W. H. Freeman (1982)",
    "Rumelhart DE, McClelland JL. Parallel Distributed Processing. MIT Press (1986)",
    "Baars BJ. A Cognitive Theory of Consciousness. Cambridge University Press (1988)",
    "Kandel ER et al. Principles of Neural Science, 4th ed. McGraw-Hill (2000)",
    "Gazzaniga MS, ed. The Cognitive Neurosciences III. MIT Press (2004)",
]
AI_FLOWS = [
    "Goodfellow I, Bengio Y, Courville A. Deep Learning. MIT Press (2016)",
    "Russell S, Norvig P. Artificial Intelligence: A Modern Approach, 4th ed. Pearson (2021)",
    "Bishop CM, Bishop H. Deep Learning: Foundations and Concepts. Springer (2024)",
    "LeCun Y, Bengio Y, Hinton G. Deep learning. Nature 521 (2015): 436–444",
    "Sutton RS, Barto AG. Reinforcement Learning, 2nd ed. MIT Press (2018)",
]
AI_BOOKS = [
    "Minsky M, Papert S. Perceptrons. MIT Press (1969)",
    "Nilsson NJ. Learning Machines. McGraw-Hill (1965)",
    "Rumelhart DE, McClelland JL. Parallel Distributed Processing. MIT Press (1986)",
    "Hertz J, Krogh A, Palmer RG. Introduction to the Theory of Neural Computation. Addison-Wesley (1991)",
    "Bishop CM. Neural Networks for Pattern Recognition. Oxford University Press (1995)",
    "Vapnik VN. Statistical Learning Theory. Wiley (1998)",
    "Haykin S. Neural Networks, 2nd ed. Prentice Hall (1999)",
    "Cristianini N, Shawe-Taylor J. An Introduction to Support Vector Machines. Cambridge University Press (2000)",
    "Scholkopf B, Smola AJ. Learning with Kernels. MIT Press (2002)",
    "Bishop CM. Pattern Recognition and Machine Learning. Springer (2006)",
]
BCI_FLOWS = [
    "Wolpaw JR, Wolpaw EW, eds. Brain-Computer Interfaces. Oxford University Press (2012)",
    "Nicolelis MAL. Methods for Neural Ensemble Recordings, 2nd ed. CRC Press (2008)",
    "Hochberg LR, Donoghue JP. Sensors for brain-computer interfaces. IEEE Engineering in Medicine and Biology (2016)",
    "Siciliano B, Khatib O, eds. Springer Handbook of Robotics, 2nd ed. Springer (2016)",
    "Dario P et al. Robotics as a future and emerging technology. Springer Tracts in Advanced Robotics (2005)",
]
BCI_BOOKS = [
    "Wiener N. The Human Use of Human Beings. Houghton Mifflin (1950)",
    "Penfield W, Rasmussen T. The Cerebral Cortex of Man. Macmillan (1950)",
    "Hodgkin AL. The Conduction of the Nervous Impulse. Liverpool University Press (1964)",
    "Nise NS. Control Systems Engineering. Benjamin Cummings (1992)",
    "Spong MW, Vidyasagar M. Robot Dynamics and Control. Wiley (1989)",
    "Craig JJ. Introduction to Robotics, 2nd ed. Addison-Wesley (1989)",
    "Arbib MA, ed. The Handbook of Brain Theory and Neural Networks. MIT Press (1995)",
    "Webster JG, ed. Medical Instrumentation, 3rd ed. Wiley (1998)",
    "Mason MT. Mechanics of Robotic Manipulation. MIT Press (2001)",
    "Lebedev MA, Nicolelis MAL. Brain-machine interfaces. Trends in Neurosciences 29 (2006): 536–546",
]
ROBOTICS_FLOWS = [
    "Siciliano B, Khatib O, eds. Springer Handbook of Robotics, 2nd ed. Springer (2016)",
    "Thrun S, Burgard W, Fox D. Probabilistic Robotics. MIT Press (2005)",
    "Spong MW et al. Robot Modeling and Control, 2nd ed. Wiley (2020)",
    "Kober J et al. Reinforcement learning in robotics: A survey. International Journal of Robotics Research 32 (2013): 1238–1274",
    "Bohg J et al. Data-driven grasp synthesis: A survey. IEEE Transactions on Robotics 30 (2014): 289–309",
]
ROBOTICS_BOOKS = [
    "Wiener N. The Human Use of Human Beings. Houghton Mifflin (1950)",
    "Bellman R. Dynamic Programming. Princeton University Press (1957)",
    "Bekey GA. Autonomous Robots. MIT Press (2005)",
    "Craig JJ. Introduction to Robotics, 2nd ed. Addison-Wesley (1989)",
    "Spong MW, Vidyasagar M. Robot Dynamics and Control. Wiley (1989)",
    "Mason MT. Mechanics of Robotic Manipulation. MIT Press (2001)",
    "Latombe JC. Robot Motion Planning. Kluwer Academic Publishers (1991)",
    "Arkin RC. Behavior-Based Robotics. MIT Press (1998)",
    "Dudek G, Jenkin M. Computational Principles of Mobile Robotics. Cambridge University Press (2000)",
    "Nise NS. Control Systems Engineering. Benjamin Cummings (1992)",
]
COMPUTING_FLOWS = [
    "Katz J, Lindell Y. Introduction to Modern Cryptography, 3rd ed. CRC Press (2020)",
    "Lynch NA. Distributed Algorithms. Morgan Kaufmann (1996)",
    "Nielsen MA, Chuang IL. Quantum Computation and Quantum Information. Cambridge University Press (2000)",
    "Tanenbaum AS, Van Steen M. Distributed Systems, 4th ed. Pearson (2023)",
    "Arora S, Barak B. Computational Complexity. Cambridge University Press (2009)",
]
COMPUTING_BOOKS = [
    "Turing AM. Computing Machinery and Intelligence. Mind (1950)",
    "Bellman R. Dynamic Programming. Princeton University Press (1957)",
    "Knuth DE. The Art of Computer Programming, Vol. 1. Addison-Wesley (1968)",
    "Aho AV et al. The Design and Analysis of Computer Algorithms. Addison-Wesley (1974)",
    "Lamport L. Specifying Systems. Addison-Wesley (2002)",
    "Schneier B. Applied Cryptography, 2nd ed. Wiley (1996)",
    "Menezes AJ et al. Handbook of Applied Cryptography. CRC Press (1996)",
    "Nielsen MA, Chuang IL. Quantum Computation and Quantum Information. Cambridge University Press (2000)",
    "Herlihy M, Shavit N. The Art of Multiprocessor Programming. Morgan Kaufmann (2008)",
    "Tanenbaum AS, Van Steen M. Distributed Systems. Prentice Hall (2002)",
]
ELECTRONICS_FLOWS = [
    "Sze SM, Ng KK. Physics of Semiconductor Devices, 3rd ed. Wiley (2006)",
    "Saleh BEA, Teich MC. Fundamentals of Photonics, 3rd ed. Wiley (2019)",
    "Yariv A, Yeh P. Photonics, 6th ed. Oxford University Press (2007)",
    "Coldren LA et al. Diode Lasers and Photonic Integrated Circuits, 2nd ed. Wiley (2012)",
    "Novoselov KS et al. A roadmap for graphene. Nature 490 (2012): 192–200",
]
ELECTRONICS_BOOKS = [
    "Shockley W. Electrons and Holes in Semiconductors. Van Nostrand (1950)",
    "Sze SM. Physics of Semiconductor Devices. Wiley (1969)",
    "Mead C, Conway L. Introduction to VLSI Systems. Addison-Wesley (1980)",
    "Streetman BG. Solid State Electronic Devices, 3rd ed. Prentice Hall (1990)",
    "Pierret RF. Semiconductor Device Fundamentals. Addison-Wesley (1996)",
    "Saleh BEA, Teich MC. Fundamentals of Photonics. Wiley (1991)",
    "Yariv A. Optical Electronics, 4th ed. Saunders College Publishing (1991)",
    "Agrawal GP. Fiber-Optic Communication Systems, 3rd ed. Wiley (2002)",
    "Sze SM, ed. VLSI Technology, 2nd ed. McGraw-Hill (1988)",
    "Kittel C. Introduction to Solid State Physics, 7th ed. Wiley (1996)",
]
ENGINEERING_FLOWS = [
    "Lanza R et al., eds. Principles of Tissue Engineering, 5th ed. Academic Press (2020)",
    "Gibson I et al. Additive Manufacturing Technologies, 3rd ed. Springer (2021)",
    "Larminie J, Lowry J. Electric Vehicle Technology Explained, 2nd ed. Wiley (2012)",
    "Sutton GP, Biblarz O. Rocket Propulsion Elements, 9th ed. Wiley (2016)",
    "Dunn B et al. Electrical energy storage for the grid. Science 334 (2011): 928–935",
]
ENGINEERING_BOOKS = [
    "Charnley J. Low Friction Arthroplasty of the Hip. Springer (1979)",
    "Webster JG, ed. Medical Instrumentation, 3rd ed. Wiley (1998)",
    "Bronzino JD, ed. The Biomedical Engineering Handbook, 2nd ed. CRC Press (2000)",
    "Lanza RP et al., eds. Principles of Tissue Engineering, 2nd ed. Academic Press (2000)",
    "Sutton GP. Rocket Propulsion Elements, 6th ed. Wiley (1992)",
    "Wertz JR, Larson WJ, eds. Space Mission Analysis and Design, 3rd ed. Microcosm Press (1999)",
    "Gibson I et al. Additive Manufacturing Technologies. Springer (2010)",
    "Vincent CA. Modern Batteries, 2nd ed. Arnold (1997)",
    "Duffie JA, Beckman WA. Solar Engineering of Thermal Processes, 2nd ed. Wiley (1991)",
    "Guyton AC, Hall JE. Textbook of Medical Physiology, 10th ed. Saunders (2000)",
]
EARTH_FLOWS = [
    "IPCC. Climate Change 2021: The Physical Science Basis. Cambridge University Press (2021)",
    "Steffen W et al. Planetary boundaries. Science 347 (2015): 1259855",
    "Schlesinger WH, Bernhardt ES. Biogeochemistry, 4th ed. Academic Press (2020)",
    "Emery WJ, Thomson RE. Data Analysis Methods in Physical Oceanography, 3rd ed. Elsevier (2014)",
    "National Academies. Thriving on Our Changing Planet. National Academies Press (2018)",
]
EARTH_BOOKS = [
    "Libby WF. Radiocarbon Dating. University of Chicago Press (1952)",
    "Carson R. Silent Spring. Houghton Mifflin (1962)",
    "MacArthur RH, Wilson EO. The Theory of Island Biogeography. Princeton University Press (1967)",
    "Meadows DH et al. The Limits to Growth. Universe Books (1972)",
    "Sagan C. Cosmos. Random House (1980)",
    "WCED. Our Common Future. Oxford University Press (1987)",
    "Turcotte DL, Schubert G. Geodynamics, 2nd ed. Cambridge University Press (2002)",
    "Lillesand TM, Kiefer RW. Remote Sensing and Image Interpretation, 4th ed. Wiley (2000)",
    "Open University. Ocean Circulation, 2nd ed. Butterworth-Heinemann (2001)",
    "Kump LR et al. The Earth System, 2nd ed. Prentice Hall (2004)",
]

FLOWS = {}
BOOKS = {}
for panel in (33, 34, 35):
    FLOWS[panel] = LIFE_FLOWS
    BOOKS[panel] = LIFE_BOOKS
for panel in (36, 38, 40, 41, 42):
    FLOWS[panel] = NEURO_FLOWS
    BOOKS[panel] = NEURO_BOOKS
for panel in (37, 43, 44, 45, 46, 47, 48, 49, 50):
    FLOWS[panel] = AI_FLOWS
    BOOKS[panel] = AI_BOOKS
for panel in (39,):
    FLOWS[panel] = BCI_FLOWS
    BOOKS[panel] = BCI_BOOKS
for panel in (51, 60, 62):
    FLOWS[panel] = ROBOTICS_FLOWS
    BOOKS[panel] = ROBOTICS_BOOKS
for panel in (52, 53, 54):
    FLOWS[panel] = COMPUTING_FLOWS
    BOOKS[panel] = COMPUTING_BOOKS
for panel in (55, 56):
    FLOWS[panel] = ELECTRONICS_FLOWS
    BOOKS[panel] = ELECTRONICS_BOOKS
for panel in (57, 58, 59, 61):
    FLOWS[panel] = ENGINEERING_FLOWS
    BOOKS[panel] = ENGINEERING_BOOKS
for panel in (63, 64, 65, 66, 67, 68, 69, 70):
    FLOWS[panel] = EARTH_FLOWS
    BOOKS[panel] = EARTH_BOOKS
