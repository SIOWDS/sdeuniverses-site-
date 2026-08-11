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
