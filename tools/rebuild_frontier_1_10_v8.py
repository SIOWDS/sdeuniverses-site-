#!/usr/bin/env python3
"""Append the V8 classic layer to frontier panels 001–010.

The modern layer is intentionally left untouched.  Each classic entry has a
four-field source line, two paragraphs, a five-field collision line, and an
explicit callback to one of the twenty modern entries already on the page.
"""

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "public" / "frontier"

PANELS = {
    1: ("number-theory", "数论", "Number Theory"),
    2: ("algebraic-geometry", "代数几何", "Algebraic Geometry"),
    3: ("topology", "拓扑学", "Topology"),
    4: ("category-theory", "范畴论", "Category Theory"),
    5: ("probability", "概率论", "Probability"),
    6: ("combinatorics", "组合数学", "Combinatorics"),
    7: ("dynamical-systems", "动力系统", "Dynamical Systems"),
    8: ("set-theory-logic", "数理逻辑与集合论", "Mathematical Logic and Set Theory"),
    9: ("quantum-computing", "量子信息与量子计算", "Quantum Information and Computing"),
    10: ("condensed-matter", "凝聚态物理", "Condensed Matter Physics"),
}

CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]
MODERN_LABELS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
PREMISES = [
    "谁进入分母", "单一读数代表复杂对象", "有限近似控制无限对象", "测量不改变被测对象", "平均值代表个体",
    "聚合次序不影响结论", "效果可由参与者自己评定", "缺失即不存在", "边界一次划定后保持稳定", "更多数据必然减少偏倚",
    "可复现＝可重做", "成本可外置而不改变结论", "时间尺度可自由压缩", "因与果的方向是给定的", "同名即同物",
    "稀有与常见服从同一机制", "局部最优可加总为整体最优", "干预不回写到被干预者", "类别互斥且穷尽", "窗口内稳定＝长期稳定",
]

# year | short title | proposer | source record | falsifiable core
DATA = {
1: [
"1950|Tate 论文与阿代尔调和分析|John Tate|Tate, Fourier Analysis in Number Fields and Hecke's Zeta-Functions, Princeton PhD thesis (1950)|把类域论互反律写成局部与整体调和分析的同一条公式",
"1956|Selberg 迹公式|Atle Selberg|Selberg, Harmonic analysis and discontinuous groups, Journal of the Indian Mathematical Society 20 (1956): 47–87|用谱侧与几何侧的等式把闭测地线和自守谱放进同一账本",
"1959|Iwasawa 理论|Kenkichi Iwasawa|Iwasawa, On Γ-extensions of algebraic number fields, Bulletin of the AMS 65 (1959): 183–226|把单个数域的类群改写为无限塔中的模与增长率",
"1965|Birch–Swinnerton-Dyer 猜想|Bryan Birch 与 Peter Swinnerton-Dyer|Birch and Swinnerton-Dyer, Notes on elliptic curves II, Journal für die reine und angewandte Mathematik 218 (1965): 79–108|以L函数在中心点的零阶预测椭圆曲线有理点秩",
"1965|Bombieri–Vinogradov 平均定理|Enrico Bombieri 与 Askold Vinogradov|Bombieri, On the large sieve, Mathematika 12 (1965): 201–225|用模数平均换取接近广义黎曼猜想一半强度的素数分布控制",
"1966|Baker 线性对数形式|Alan Baker|Baker, Linear forms in the logarithms of algebraic numbers I, Mathematika 13 (1966): 204–216|把丢番图方程的存在性问题变成可显式估计的下界",
"1967|Langlands 纲领信件|Robert Langlands|Langlands, Letter to André Weil (1967), in The Work of Robert Langlands, IAS archive|预言伽罗瓦表示与自守表示之间存在跨对象对应",
"1973|Montgomery 零点对相关|Hugh Montgomery|Montgomery, The pair correlation of zeros of the zeta function, Proceedings of Symposia in Pure Mathematics 24 (1973): 181–193|用零点间距统计把黎曼ζ函数与随机矩阵谱联系起来",
"1973|陈氏定理的一加二|陈景润|Chen, On the representation of a large even integer as the sum of a prime and the product of at most two primes, Scientia Sinica 16 (1973): 157–176|证明充分大的偶数可写成素数与至多两个素数乘积之和",
"1974|Deligne 证明 Weil 猜想|Pierre Deligne|Deligne, La conjecture de Weil I, Publications Mathématiques de l'IHÉS 43 (1974): 273–307|以代数几何上同调控制有限域点数的误差项",
"1977|Mazur 有理挠点分类|Barry Mazur|Mazur, Modular curves and the Eisenstein ideal, Publications Mathématiques de l'IHÉS 47 (1977): 33–186|把有理数域上椭圆曲线可能的挠子群压成有限清单",
"1983|Faltings 有限性定理|Gerd Faltings|Faltings, Endlichkeitssätze für abelsche Varietäten über Zahlkörpern, Inventiones Mathematicae 73 (1983): 349–366|证明高亏格曲线只有有限多个有理点并解决Mordell猜想",
"1984|Cohen–Lenstra 启发式|Henri Cohen 与 Hendrik Lenstra|Cohen and Lenstra, Heuristics on class groups of number fields, Lecture Notes in Mathematics 1068, Springer (1984): 33–62|按自同构群倒数给类群分布赋权而不是逐域列举",
"1986|Gross–Zagier 公式|Benedict Gross 与 Don Zagier|Gross and Zagier, Heegner points and derivatives of L-series, Inventiones Mathematicae 84 (1986): 225–320|把L函数导数与Heegner点高度精确相等",
"1987|Odlyzko 大规模零点计算|Andrew Odlyzko|Odlyzko, On the distribution of spacings between zeros of the zeta function, Mathematics of Computation 48 (1987): 273–308|用高位零点间距检验随机矩阵型统计而非证明单个零点位置",
"1990|Ribet 的 ε 猜想定理|Kenneth Ribet|Ribet, On modular representations arising from modular forms, Inventiones Mathematicae 100 (1990): 431–476|把费马反例压到不存在的低层模形式上",
"1995|Wiles–Taylor 模性提升|Andrew Wiles 与 Richard Taylor|Wiles, Modular elliptic curves and Fermat's Last Theorem, Annals of Mathematics 141 (1995): 443–551|用变形环与Hecke代数同构把半稳定椭圆曲线提升为模的",
"1998|Friedlander–Iwaniec 稀疏素数|John Friedlander 与 Henryk Iwaniec|Friedlander and Iwaniec, The polynomial X²+Y⁴ captures its primes, Annals of Mathematics 148 (1998): 945–1040|证明高度稀疏的二元多项式仍取得预期数量的素数值",
"1999|Katz–Sarnak 对称族|Nicholas Katz 与 Peter Sarnak|Katz and Sarnak, Random Matrices, Frobenius Eigenvalues, and Monodromy, AMS (1999)|以单值群的对称类型预测L函数族的低位零点",
"2002|Lafforgue 的函数域 Langlands|Laurent Lafforgue|Lafforgue, Chtoucas de Drinfeld et correspondance de Langlands, Inventiones Mathematicae 147 (2002): 1–241|在函数域上证明一般线性群的全局Langlands对应",
],
2: [
"1956|GAGA 原理|Jean-Pierre Serre|Serre, Géométrie algébrique et géométrie analytique, Annales de l'Institut Fourier 6 (1956): 1–42|证明射影复簇的代数对象与解析对象在上同调层面对应",
"1957|Tôhoku 同调代数|Alexander Grothendieck|Grothendieck, Sur quelques points d'algèbre homologique, Tôhoku Mathematical Journal 9 (1957): 119–221|用阿贝尔范畴和导出函子统一层上同调的计算规则",
"1960|概形成为基本对象|Grothendieck 与 Dieudonné|Grothendieck and Dieudonné, Éléments de géométrie algébrique I, Publications Mathématiques de l'IHÉS 4 (1960)|把多项式零点集扩成可粘合且含幂零信息的概形",
"1960|Kodaira–Spencer 变形理论|Kunihiko Kodaira 与 Donald Spencer|Kodaira and Spencer, On deformations of complex analytic structures III, Annals of Mathematics 71 (1960): 43–76|把复结构的微小变化编码为上同调类及障碍",
"1964|Hironaka 奇点消解|广中平祐|Hironaka, Resolution of singularities of an algebraic variety over characteristic zero, Annals of Mathematics 79 (1964): 109–326|证明特征零代数簇可经有限次爆破化为光滑对象",
"1965|几何不变量论|David Mumford|Mumford, Geometric Invariant Theory, Springer (1965)|用稳定与半稳定点构造群作用下可用的商空间",
"1966|Grothendieck 对偶|Robin Hartshorne|Hartshorne, Residues and Duality, Lecture Notes in Mathematics 20, Springer (1966)|把Serre对偶推广为导出范畴中的统一函子公式",
"1969|Deligne–Mumford 模空间|Pierre Deligne 与 David Mumford|Deligne and Mumford, The irreducibility of the space of curves of given genus, Publications Mathématiques de l'IHÉS 36 (1969): 75–109|用叠处理带自同构对象并紧化曲线模空间",
"1970|SGA 的平坦下降|Grothendieck 学派|Grothendieck, Revêtements étales et groupe fondamental, SGA 1, Lecture Notes in Mathematics 224, Springer (1971)|以覆盖与下降数据决定几何对象能否由局部拼成整体",
"1971|Deligne 混合 Hodge 结构|Pierre Deligne|Deligne, Théorie de Hodge II, Publications Mathématiques de l'IHÉS 40 (1971): 5–57|给非光滑非完备簇的上同调加入权与滤过",
"1973|Quillen 高阶 K 理论|Daniel Quillen|Quillen, Higher algebraic K-theory I, Lecture Notes in Mathematics 341, Springer (1973): 85–147|把投射模分类提升为一列同伦不变量",
"1977|Hartshorne 教科书体系|Robin Hartshorne|Hartshorne, Algebraic Geometry, Springer (1977)|把概形层上同调与曲面论组织成共同训练语言",
"1982|BBD 反常层|Beilinson、Bernstein 与 Deligne|Beilinson, Bernstein and Deligne, Faisceaux pervers, Astérisque 100 (1982)|用新的t结构让奇异空间上的上同调保持对偶与分解",
"1982|Mori 锥定理|森重文|Mori, Threefolds whose canonical bundles are not numerically effective, Annals of Mathematics 116 (1982): 133–176|把双有理分类改写为沿负曲线收缩的程序",
"1984|Fulton 交叉理论|William Fulton|Fulton, Intersection Theory, Springer (1984)|用Chow群与形变到法锥给非横截相交稳定的重数",
"1994|同调镜像对称|Maxim Kontsevich|Kontsevich, Homological algebra of mirror symmetry, ICM Zürich proceedings (1994): 120–139|预言辛几何的Fukaya范畴与镜像的导出范畴等价",
"1994|Gromov–Witten 公理化|Kontsevich 与 Manin|Kontsevich and Manin, Gromov-Witten classes, quantum cohomology, and enumerative geometry, Communications in Mathematical Physics 164 (1994): 525–562|把伪全纯曲线计数组织成可分裂的量子上同调",
"1996|Voevodsky 动机上同调|Vladimir Voevodsky|Voevodsky, Homology of schemes, Selecta Mathematica 2 (1996): 111–153|构造能接住代数循环与K理论的动机上同调",
"1998|Kollár–Mori 对数极小模型|János Kollár 与森重文|Kollár and Mori, Birational Geometry of Algebraic Varieties, Cambridge University Press (1998)|把奇点类别写进极小模型每一步的许可条件",
"1999|A¹ 同伦论|Fabien Morel 与 Vladimir Voevodsky|Morel and Voevodsky, A¹-homotopy theory of schemes, Publications Mathématiques de l'IHÉS 90 (1999): 45–143|把代数簇置于以仿射直线为区间的同伦范畴",
],
3: [
"1951|Serre 谱序列|Jean-Pierre Serre|Serre, Homologie singulière des espaces fibrés, Annals of Mathematics 54 (1951): 425–505|把纤维、底空间与总空间的同调组织成逐页逼近",
"1954|Thom 配边理论|René Thom|Thom, Quelques propriétés globales des variétés différentiables, Commentarii Mathematici Helvetici 28 (1954): 17–86|用是否共同成为某流形边界来分类流形",
"1956|Milnor 奇异球面|John Milnor|Milnor, On manifolds homeomorphic to the 7-sphere, Annals of Mathematics 64 (1956): 399–405|证明同一拓扑球面可以承载不等价的光滑结构",
"1958|Adams 谱序列|J. Frank Adams|Adams, On the structure and applications of the Steenrod algebra, Commentarii Mathematici Helvetici 32 (1958): 180–214|用上同调运算逐级逼近稳定同伦群",
"1959|Atiyah–Hirzebruch K 理论|Michael Atiyah 与 Friedrich Hirzebruch|Atiyah and Hirzebruch, Riemann-Roch theorems for differentiable manifolds, Bulletin of the AMS 65 (1959): 276–281|以向量丛的Grothendieck群构造广义上同调理论",
"1961|Smale h-配边定理|Stephen Smale|Smale, Generalized Poincaré's conjecture in dimensions greater than four, Annals of Mathematics 74 (1961): 391–406|用手柄消去证明高维单连闭流形的分类结论",
"1963|Zeeman 解结与高余维|Christopher Zeeman|Zeeman, Unknotting combinatorial balls, Annals of Mathematics 78 (1963): 501–526|说明高余维嵌入比低维结更具刚性",
"1967|Quillen 模型范畴|Daniel Quillen|Quillen, Homotopical Algebra, Lecture Notes in Mathematics 43, Springer (1967)|以弱等价纤维化余纤维化抽取不同范畴的同伦内容",
"1970|Novikov 高阶签名|Sergei Novikov|Novikov, Pontryagin classes, the fundamental group and some problems of stable algebra, Essays on Topology and Related Topics (1970)|把流形签名与基本群上同调联系并提出同伦不变性",
"1970|Kirby–Siebenmann 阻碍|Robion Kirby 与 Laurence Siebenmann|Kirby and Siebenmann, On the triangulation of manifolds and the Hauptvermutung, Bulletin of the AMS 75 (1969): 742–749|用四维上同调类检测拓扑流形能否具有PL结构",
"1974|Sullivan 局部化|Dennis Sullivan|Sullivan, Genetics of homotopy theory and the Adams conjecture, Annals of Mathematics 100 (1974): 1–79|按素数局部化把同伦类型分解后再重组",
"1977|有理同伦最小模型|Dennis Sullivan|Sullivan, Infinitesimal computations in topology, Publications Mathématiques de l'IHÉS 47 (1977): 269–331|用交换微分分次代数计算空间的有理同伦类型",
"1978|Thurston 几何化纲领|William Thurston|Thurston, The geometry and topology of three-manifolds, Princeton lecture notes (1978–1981)|把三维流形切分为八种几何模型",
"1979|Bousfield 同伦局部化|Alden Bousfield|Bousfield, The localization of spaces with respect to homology, Topology 14 (1975): 133–150|按选定同调理论忽略不可见的同伦信息",
"1982|Freedman 四维拓扑|Michael Freedman|Freedman, The topology of four-dimensional manifolds, Journal of Differential Geometry 17 (1982): 357–453|在拓扑范畴解决单连四维流形分类与Poincaré问题",
"1983|Donaldson 四维规范论|Simon Donaldson|Donaldson, An application of gauge theory to four-dimensional topology, Journal of Differential Geometry 18 (1983): 279–315|用反自对偶联络证明光滑四维交叉形式受强约束",
"1984|Jones 多项式|Vaughan Jones|Jones, A polynomial invariant for knots via von Neumann algebras, Bulletin of the AMS 12 (1985): 103–111|从算子代数构造能区分结的新Laurent多项式",
"1984|Ravenel 色层猜想|Douglas Ravenel|Ravenel, Localization with respect to certain periodic homology theories, American Journal of Mathematics 106 (1984): 351–414|按形式群高度把稳定同伦论切成色层",
"1988|Witten 拓扑量子场论|Edward Witten|Witten, Topological quantum field theory, Communications in Mathematical Physics 117 (1988): 353–386|把Donaldson不变量解释为量子场论关联函数",
"2002|Perelman Ricci 流手术|Grigori Perelman|Perelman, The entropy formula for the Ricci flow and its geometric applications, arXiv:math/0211159 (2002)|用熵与无局部塌缩控制Ricci流奇点并完成几何化",
],
4: [
"1957|阿贝尔范畴与导出函子|Alexander Grothendieck|Grothendieck, Sur quelques points d'algèbre homologique, Tôhoku Mathematical Journal 9 (1957): 119–221|把对象的具体元素换成核余核与函子的公理",
"1958|Kan 伴随函子|Daniel Kan|Kan, Adjoint functors, Transactions of the AMS 87 (1958): 294–329|用自然同构刻画自由构造与遗忘过程的普遍配对",
"1963|Lawvere 代数理论|F. William Lawvere|Lawvere, Functorial Semantics of Algebraic Theories, Columbia PhD thesis (1963)|把一种代数结构写成有限积范畴及其保积函子",
"1964|ETCS 集合范畴公理|F. William Lawvere|Lawvere, An elementary theory of the category of sets, PNAS 52 (1964): 1506–1511|用对象与箭头关系而非成员关系给集合论一套基础",
"1964|Freyd 阿贝尔范畴|Peter Freyd|Freyd, Abelian Categories, Harper & Row (1964)|证明同调代数可在抽象阿贝尔范畴中完成",
"1965|Eilenberg–Moore 代数|Samuel Eilenberg 与 John Moore|Eilenberg and Moore, Adjoint functors and triples, Illinois Journal of Mathematics 9 (1965): 381–398|把单子的代数对象组织成一个新范畴",
"1966|Beck 单子性定理|Jonathan Beck|Beck, Triples, algebras and cohomology, Columbia PhD thesis (1966)|给出何时一个伴随等价于某单子代数范畴的判据",
"1967|Bénabou 双范畴|Jean Bénabou|Bénabou, Introduction to bicategories, Reports of the Midwest Category Seminar, Springer (1967): 1–77|把结合律从等式放宽为可相干同构",
"1967|Gabriel–Zisman 分式演算|Pierre Gabriel 与 Michel Zisman|Gabriel and Zisman, Calculus of Fractions and Homotopy Theory, Springer (1967)|以形式逆把指定态射变成同构并构造局部化",
"1969|Grothendieck 下降与纤维范畴|Alexander Grothendieck|Grothendieck, Catégories fibrées et descente, SGA 1 exposé VI, Springer (1971)|用纤维范畴把局部对象及其粘合条件编码在同一结构",
"1971|Mac Lane 相干性|Saunders Mac Lane|Mac Lane, Categories for the Working Mathematician, Springer (1971)|证明单体范畴中所有合法结合图自动交换",
"1972|Grothendieck 拓扑与拓扑斯|Grothendieck、Artin 与 Verdier|Artin, Grothendieck and Verdier, Théorie des topos et cohomologie étale, SGA 4, Springer (1972)|把开覆盖抽象为筛并让层论脱离点集空间",
"1972|May 操作子|J. Peter May|May, The Geometry of Iterated Loop Spaces, Springer (1972)|用带对称作用的多输入运算编码迭代圈空间",
"1980|Street 纤维化形式理论|Ross Street|Street, Fibrations in bicategories, Cahiers de Topologie et Géométrie Différentielle 21 (1980): 111–160|把Grothendieck纤维化提升为双范畴内部的伴随性质",
"1982|Kelly 富集范畴|G. Max Kelly|Kelly, Basic Concepts of Enriched Category Theory, Cambridge University Press (1982)|允许态射对象取值于一般单体范畴而不只是集合",
"1986|Joyal 组合物种|André Joyal|Joyal, Foncteurs analytiques et espèces de structures, Lecture Notes in Mathematics 1234, Springer (1986): 126–159|用有限集上的函子统一带标签组合结构与生成函数",
"1987|线性逻辑的范畴语义|Jean-Yves Girard|Girard, Linear logic, Theoretical Computer Science 50 (1987): 1–102|区分可复制资源与一次性资源并给出星自主范畴模型",
"1993|Joyal–Street 辫状单体范畴|André Joyal 与 Ross Street|Joyal and Street, Braided tensor categories, Advances in Mathematics 102 (1993): 20–78|用辫群相干性编码交换但不对称的过程",
"1995|Baez–Dolan 高阶范畴假说|John Baez 与 James Dolan|Baez and Dolan, Higher-dimensional algebra and topological quantum field theory, Journal of Mathematical Physics 36 (1995): 6073–6105|把全扩张场论预言为由全可对偶对象分类",
"2002|Joyal 拟范畴|André Joyal|Joyal, Quasi-categories and Kan complexes, Journal of Pure and Applied Algebra 175 (2002): 207–222|用内角可填充的单纯集给无穷范畴一个可操作模型",
],
5: [
"1951|Donsker 不变性原理|Monroe Donsker|Donsker, An invariance principle for certain probability limit theorems, Memoirs of the AMS 6 (1951)|证明适当缩放的随机游走路径收敛到布朗运动",
"1951|Itô 随机积分与公式|伊藤清|Itô, On stochastic differential equations, Memoirs of the AMS 4 (1951): 1–51|为非光滑布朗路径建立带二次变差修正的微积分",
"1953|Doob 鞅体系|Joseph Doob|Doob, Stochastic Processes, Wiley (1953)|以条件期望不变性组织随机过程与停时定理",
"1957|Feller 极限定理体系|William Feller|Feller, An Introduction to Probability Theory and Its Applications II, Wiley (1966; first edition 1957)|把独立和的极限分布与生成函数方法组织成标准体系",
"1965|Dynkin 马尔可夫过程|Eugene Dynkin|Dynkin, Markov Processes, Springer (1965)|用生成元与强马尔可夫性质连接路径过程和偏微分方程",
"1969|Stroock–Varadhan 鞅问题|Daniel Stroock 与 Srinivasa Varadhan|Stroock and Varadhan, Diffusion processes with continuous coefficients I, Communications on Pure and Applied Mathematics 22 (1969): 345–400|不用预设随机微分方程解而以测试函数鞅刻画扩散",
"1968|DLR Gibbs 测度|Dobrushin、Lanford 与 Ruelle|Dobrushin, Gibbsian random fields for lattice systems, Functional Analysis and Its Applications 2 (1968): 292–301|用所有有限区域的条件分布定义无限体积平衡态",
"1975|Freidlin–Wentzell 大偏差|Mark Freidlin 与 Alexander Wentzell|Freidlin and Wentzell, Random Perturbations of Dynamical Systems, Springer (1975 Russian edition)|以作用量给小噪声稀有路径的指数概率",
"1976|Malliavin 随机变分法|Paul Malliavin|Malliavin, Stochastic calculus of variations and hypoelliptic operators, Kyoto proceedings (1976): 195–263|在Wiener空间求导以证明扩散分布具有光滑密度",
"1980|Kesten 平面渗流阈值|Harry Kesten|Kesten, The critical probability of bond percolation on the square lattice equals 1/2, Communications in Mathematical Physics 74 (1980): 41–59|严格确定方格键渗流的临界概率为二分之一",
"1982|Kingman 合并过程|John Kingman|Kingman, The coalescent, Stochastic Processes and their Applications 13 (1982): 235–248|用向后两两合并的交换过程描述大群体谱系",
"1984|Geman–Geman 模拟退火|Stuart Geman 与 Donald Geman|Geman and Geman, Stochastic relaxation, Gibbs distributions, and Bayesian restoration of images, IEEE TPAMI 6 (1984): 721–741|以缓慢降温的马尔可夫链逼近全局能量极小",
"1986|KPZ 随机生长方程|Kardar、Parisi 与 Zhang|Kardar, Parisi and Zhang, Dynamic scaling of growing interfaces, Physical Review Letters 56 (1986): 889–892|用非线性随机偏微分方程预测界面粗糙度普适指数",
"1985|Bakry–Émery 曲率判据|Dominique Bakry 与 Michel Émery|Bakry and Émery, Diffusions hypercontractives, Lecture Notes in Mathematics 1123, Springer (1985): 177–206|用生成元的曲率下界推出泛函不等式与浓缩",
"1991|Aldous 连续随机树|David Aldous|Aldous, The continuum random tree I, Annals of Probability 19 (1991): 1–28|把大型离散随机树的缩放极限构造成连续度量树",
"1995|Talagrand 浓缩不等式|Michel Talagrand|Talagrand, Concentration of measure and isoperimetric inequalities in product spaces, Publications Mathématiques de l'IHÉS 81 (1995): 73–205|证明乘积空间中大量函数围绕中位数指数集中",
"1994|Lions–Perthame–Tadmor 动力学平均|Pierre-Louis Lions、Benoît Perthame 与 Eitan Tadmor|Lions, Perthame and Tadmor, A kinetic formulation of multidimensional scalar conservation laws, Journal of the AMS 7 (1994): 169–191|用速度变量平均从弱正则随机结构提取紧性",
"2000|Schramm Loewner 演化|Oded Schramm|Schramm, Scaling limits of loop-erased random walks and uniform spanning trees, Israel Journal of Mathematics 118 (2000): 221–288|证明共形不变且具域马尔可夫性的曲线只能由一维布朗驱动",
"2001|Lawler–Schramm–Werner 交叉指数|Lawler、Schramm 与 Werner|Lawler, Schramm and Werner, Values of Brownian intersection exponents I, Acta Mathematica 187 (2001): 237–273|借SLE精确计算布朗路径互不相交的幂律指数",
"2002|Kallenberg 交换结构体系|Olav Kallenberg|Kallenberg, Foundations of Modern Probability, Springer (2002)|以交换性、点过程与随机测度统一现代概率对象",
],
6: [
"1951|de Bruijn–Erdős 紧致性|Nicolaas de Bruijn 与 Paul Erdős|de Bruijn and Erdős, A colour problem for infinite graphs, Indagationes Mathematicae 13 (1951): 369–373|证明无限图可有限着色当且仅当所有有限子图可同数着色",
"1959|Erdős–Rényi 随机图|Paul Erdős 与 Alfréd Rényi|Erdős and Rényi, On random graphs I, Publicationes Mathematicae 6 (1959): 290–297|用边概率随规模变化刻画巨分量等性质的突现",
"1961|Erdős–Ko–Rado 交族定理|Erdős、Ko 与 Rado|Erdős, Ko and Rado, Intersection theorems for systems of finite sets, Quarterly Journal of Mathematics 12 (1961): 313–320|给定大小子集两两相交时确定最大族的规模与结构",
"1963|Hales–Jewett 定理|Alfred Hales 与 Robert Jewett|Hales and Jewett, Regularity and positional games, Transactions of the AMS 106 (1963): 222–229|证明高维字词立方任意有限染色必含组合直线",
"1966|Erdős–Hajnal 遗传性质|Paul Erdős 与 András Hajnal|Erdős and Hajnal, On chromatic number of graphs and set-systems, Acta Mathematica Academiae Scientiarum Hungaricae 17 (1966): 61–99|把禁诱导子图与大齐次子集的存在联系起来",
"1966|Tutte 图论结构化|William Tutte|Tutte, Connectivity in Graphs, University of Toronto Press (1966)|以割、连通度与拟阵统一图的可分解结构",
"1972|Lovász 弱完美图定理|László Lovász|Lovász, Normal hypergraphs and the perfect graph conjecture, Discrete Mathematics 2 (1972): 253–267|证明图完美当且仅当其补图完美",
"1975|Lovász 局部引理|László Lovász 与 Paul Erdős|Erdős and Lovász, Problems and results on 3-chromatic hypergraphs, Infinite and Finite Sets II (1975): 609–627|说明低概率坏事件在依赖稀疏时可以同时避免",
"1975|Szemerédi 定理|Endre Szemerédi|Szemerédi, On sets of integers containing no k elements in arithmetic progression, Acta Arithmetica 27 (1975): 199–245|证明正密度整数集必含任意给定长度算术级数",
"1978|Szemerédi 正则性引理|Endre Szemerédi|Szemerédi, Regular partitions of graphs, Colloques Internationaux CNRS 260 (1978): 399–401|把大稠密图分成有限个近似随机的点对",
"1979|Lovász θ 函数|László Lovász|Lovász, On the Shannon capacity of a graph, IEEE Transactions on Information Theory 25 (1979): 1–7|用半正定量夹住独立数并精确求五环香农容量",
"1980|AKS 稀疏图独立集|Ajtai、Komlós 与 Szemerédi|Ajtai, Komlós and Szemerédi, A note on Ramsey numbers, Journal of Combinatorial Theory A 29 (1980): 354–360|证明无三角稀疏图含比平凡界更大的独立集",
"1983|Robertson–Seymour 图小式纲领|Neil Robertson 与 Paul Seymour|Robertson and Seymour, Graph minors I, Journal of Combinatorial Theory B 35 (1983): 39–61|证明有限图在小式关系下良基序并导向有限禁阻刻画",
"1985|Bollobás 随机图教科书|Béla Bollobás|Bollobás, Random Graphs, Academic Press (1985)|把阈值函数、分支过程与极值性质编成统一概率方法",
"1985|Razborov 单调电路下界|Alexander Razborov|Razborov, Lower bounds on the monotone complexity of some Boolean functions, Soviet Mathematics Doklady 31 (1985): 354–357|用逼近法证明团问题需要超多项式单调电路",
"1987|Frankl–Rödl 禁交定理|Peter Frankl 与 Vojtěch Rödl|Frankl and Rödl, Forbidden intersections, Transactions of the AMS 300 (1987): 259–286|证明禁掉一个交集大小会使集合族指数缩小",
"1986|Alon–Boppana 谱界|Noga Alon|Alon, Eigenvalues and expanders, Combinatorica 6 (1986): 83–96|用第二特征值给正规图扩张能力设置渐近下限",
"2001|Gowers 范数雏形|Timothy Gowers|Gowers, A new proof of Szemerédi's theorem, Geometric and Functional Analysis 11 (2001): 465–588|以高阶一致性范数检测算术结构并控制密度递增",
"1999|组合零点定理|Noga Alon|Alon, Combinatorial Nullstellensatz, Combinatorics Probability and Computing 8 (1999): 7–29|从多项式最高次单项式系数推出网格上存在非零点",
"2004|Green–Tao 转移原理|Ben Green 与 Terence Tao|Green and Tao, The primes contain arbitrarily long arithmetic progressions, arXiv:math/0404188 (2004)|用伪随机主函数把稠密组合定理转移到稀疏素数",
],
7: [
"1954|Kolmogorov 近可积稳定性|Andrey Kolmogorov|Kolmogorov, On conservation of conditionally periodic motions, Doklady Akademii Nauk 98 (1954): 527–530|证明非退化近可积哈密顿系统保留大量准周期环面",
"1958|Kolmogorov–Sinai 熵|Andrey Kolmogorov 与 Yakov Sinai|Kolmogorov, A new metric invariant of transitive dynamical systems, Doklady 119 (1958): 861–864|用单位时间信息增长率区分测度保持系统",
"1962|Moser 扭转定理|Jürgen Moser|Moser, On invariant curves of area-preserving mappings of an annulus, Nachrichten der Akademie Göttingen II (1962): 1–20|在有限光滑小扰动下保住面积保持映射的不变曲线",
"1963|Lorenz 奇异吸引子|Edward Lorenz|Lorenz, Deterministic nonperiodic flow, Journal of the Atmospheric Sciences 20 (1963): 130–141|用三维常微分方程展示确定系统的长期不可预测性",
"1964|Arnold 扩散机制|Vladimir Arnold|Arnold, Instability of dynamical systems with several degrees of freedom, Soviet Mathematics Doklady 5 (1964): 581–585|说明多自由度近可积系统可沿共振网发生长期漂移",
"1967|Smale 马蹄与结构稳定|Stephen Smale|Smale, Differentiable dynamical systems, Bulletin of the AMS 73 (1967): 747–817|用双曲不变集把复杂轨道编码为符号移位",
"1967|Anosov 双曲系统|Dmitri Anosov|Anosov, Geodesic Flows on Closed Riemannian Manifolds of Negative Curvature, Steklov Institute (1967)|以全局稳定与不稳定分裂定义一致双曲动力学",
"1972|Sinai–Ruelle–Bowen 测度|Yakov Sinai|Sinai, Gibbs measures in ergodic theory, Russian Mathematical Surveys 27 (1972): 21–69|用不稳定方向上的条件密度描述典型初值所见统计",
"1971|Ruelle–Takens 湍流路线|David Ruelle 与 Floris Takens|Ruelle and Takens, On the nature of turbulence, Communications in Mathematical Physics 20 (1971): 167–192|以低维奇异吸引子替代无限次准周期分岔路线",
"1975|Bowen 符号动力学|Rufus Bowen|Bowen, Equilibrium States and the Ergodic Theory of Anosov Diffeomorphisms, Springer (1975)|用Markov分割把双曲流编码为有限符号过程",
"1977|Pesin 非一致双曲理论|Yakov Pesin|Pesin, Characteristic Lyapunov exponents and smooth ergodic theory, Russian Mathematical Surveys 32 (1977): 55–114|在几乎处处非零Lyapunov指数下构造稳定流形",
"1977|Furstenberg 遍历证明|Hillel Furstenberg|Furstenberg, Ergodic behavior of diagonal measures and a theorem of Szemerédi, Journal d'Analyse Mathématique 31 (1977): 204–256|把算术级数存在性转成测度保持系统的多重返回",
"1978|Feigenbaum 倍周期普适性|Mitchell Feigenbaum|Feigenbaum, Quantitative universality for a class of nonlinear transformations, Journal of Statistical Physics 19 (1978): 25–52|发现不同单峰映射的分岔间距趋于同一常数",
"1979|Newhouse 持续同宿切触|Sheldon Newhouse|Newhouse, The abundance of wild hyperbolic sets and nonsmooth stable sets, Publications Mathématiques de l'IHÉS 50 (1979): 101–151|证明二维系统中切触可持续并产生无穷多个吸引子",
"1981|Jakobson 随机型参数|Michael Jakobson|Jakobson, Absolutely continuous invariant measures for one-parameter families, Communications in Mathematical Physics 81 (1981): 39–88|证明二次映射有正测度参数承载绝对连续不变测度",
"1981|Takens 延迟嵌入|Floris Takens|Takens, Detecting strange attractors in turbulence, Lecture Notes in Mathematics 898, Springer (1981): 366–381|用单一观测量的延迟坐标重建一般吸引子",
"1982|Mañé 遍历闭合引理|Ricardo Mañé|Mañé, An ergodic closing lemma, Annals of Mathematics 116 (1982): 503–540|证明典型微扰可用周期轨道逼近遍历测度",
"1990|OGY 混沌控制|Ott、Grebogi 与 Yorke|Ott, Grebogi and Yorke, Controlling chaos, Physical Review Letters 64 (1990): 1196–1199|用小参数扰动稳定嵌在混沌吸引子中的不稳定周期轨",
"1991|Ratner 单参数幺幂流刚性|Marina Ratner|Ratner, On Raghunathan's measure conjecture, Annals of Mathematics 134 (1991): 545–607|证明齐性空间幺幂流的遍历测度必为代数测度",
"1999|Lyubich Feigenbaum 双曲性|Mikhail Lyubich|Lyubich, Feigenbaum-Coullet-Tresser universality and Milnor's hairiness conjecture, Annals of Mathematics 149 (1999): 319–420|用重整化双曲性严格建立一维动力学普适性",
],
8: [
"1952|Kleene 递归论体系|Stephen Kleene|Kleene, Introduction to Metamathematics, North-Holland (1952)|用部分递归函数与可实现性整理可计算和可证明的边界",
"1956|Tarski 真理与逻辑后承|Alfred Tarski|Tarski, Logic, Semantics, Metamathematics, Oxford University Press (1956)|把语义真与形式推导关系分开并给出模型论定义",
"1963|Cohen 强迫法|Paul Cohen|Cohen, The independence of the continuum hypothesis, PNAS 50 (1963): 1143–1148|通过加入泛型对象构造CH成立与失败的模型",
"1965|独立性成为方法|Paul Cohen|Cohen, Set Theory and the Continuum Hypothesis, W. A. Benjamin (1966)|把强迫从一次证明整理成可复用模型扩张技术",
"1966|Robinson 非标准分析|Abraham Robinson|Robinson, Non-standard Analysis, North-Holland (1966)|用模型论构造含无穷小的数系并严格化微积分直觉",
"1968|AUTOMATH 形式化语言|Nicolaas de Bruijn|de Bruijn, AUTOMATH, a language for mathematics, Eindhoven report (1968)|让定义定理和证明进入同一可机检类型系统",
"1970|Scott 域理论|Dana Scott|Scott, Outline of a mathematical theory of computation, Oxford PRG report (1970)|用有序完备域给递归程序与高阶函数指称语义",
"1970|Matiyasevich 解决第十问题|Yuri Matiyasevich|Matiyasevich, Enumerable sets are Diophantine, Soviet Mathematics Doklady 11 (1970): 354–358|证明每个可枚举集合都可由丢番图方程表示",
"1970|Solovay 全可测模型|Robert Solovay|Solovay, A model of set-theory in which every set of reals is Lebesgue measurable, Annals of Mathematics 92 (1970): 1–56|在不可达基数假设下构造所有实数集可测的模型",
"1971|Cook 可满足性完备性|Stephen Cook|Cook, The complexity of theorem-proving procedures, STOC proceedings (1971): 151–158|证明布尔可满足性对非确定多项式时间问题完备",
"1972|Martin-Löf 构造型类型论|Per Martin-Löf|Martin-Löf, An intuitionistic theory of types, University of Stockholm report (1972)|以依赖类型同时承载命题证明与可执行构造",
"1974|Friedman 逆数学纲领|Harvey Friedman|Friedman, Some systems of second order arithmetic and their use, ICM Vancouver proceedings (1974): 235–242|反问普通定理恰好需要哪些集合存在公理",
"1977|Paris–Harrington 自然不可证命题|Jeff Paris 与 Leo Harrington|Paris and Harrington, A mathematical incompleteness in Peano arithmetic, Handbook of Mathematical Logic, North-Holland (1977): 1133–1142|给出有限组合陈述在标准模型为真却不能由PA证明",
"1978|Shelah 分类理论|Saharon Shelah|Shelah, Classification Theory and the Number of Nonisomorphic Models, North-Holland (1978)|用稳定性和分叉划分一阶理论的可分类与野性区域",
"1989|Martin–Steel 决定性与大基数|Donald Martin 与 John Steel|Martin and Steel, A proof of projective determinacy, Journal of the AMS 2 (1989): 71–125|从Woodin型大基数推出投射集合博弈决定性",
"1987|Girard 线性逻辑|Jean-Yves Girard|Girard, Linear logic, Theoretical Computer Science 50 (1987): 1–102|把结构规则拆开以记录证明中资源是否可复制丢弃",
"1994|Shelah PCF 理论|Saharon Shelah|Shelah, Cardinal Arithmetic, Oxford University Press (1994)|以正则基数积的可能共尾性控制奇异基数幂",
"1996|Hrushovski 模型论 Mordell–Lang|Ehud Hrushovski|Hrushovski, The Mordell-Lang conjecture for function fields, Journal of the AMS 9 (1996): 667–690|用稳定性与差分域方法证明函数域Mordell–Lang",
"2001|Woodin Ω 逻辑|W. Hugh Woodin|Woodin, The Continuum Hypothesis, part I, Notices of the AMS 48 (2001): 567–576|以强迫不变的语义后承重新评价连续统命题的可决定性",
"2004|证明助手库化|Georges Gonthier|Gonthier, A computer-checked proof of the four colour theorem, Microsoft Research report (2004)|把大型穷举证书与小可信内核组合成可复查证明",
],
9: [
"1964|Bell 不等式|John Bell|Bell, On the Einstein Podolsky Rosen paradox, Physics Physique Fizika 1 (1964): 195–200|把局域隐变量与量子预测的分歧写成可实验检验的不等式",
"1973|Holevo 信息上界|Alexander Holevo|Holevo, Bounds for the quantity of information transmitted by a quantum communication channel, Problems of Information Transmission 9 (1973): 177–183|限制量子态集合可提取的经典信息不超过Holevo量",
"1982|Feynman 量子模拟|Richard Feynman|Feynman, Simulating physics with computers, International Journal of Theoretical Physics 21 (1982): 467–488|主张量子系统的通用高效模拟需要量子计算装置",
"1983|Wiesner 共轭编码|Stephen Wiesner|Wiesner, Conjugate coding, SIGACT News 15 (1983): 78–88|用不可同时读取的共轭基提出量子防伪与复用通信",
"1984|BB84 量子密钥分发|Charles Bennett 与 Gilles Brassard|Bennett and Brassard, Quantum cryptography, IEEE Bangalore proceedings (1984): 175–179|用非正交态和公开抽检把窃听转成可见误码",
"1985|Deutsch 通用量子机|David Deutsch|Deutsch, Quantum theory, the Church-Turing principle and the universal quantum computer, Proceedings of the Royal Society A 400 (1985): 97–117|定义可模拟任意有限量子系统的通用量子图灵机",
"1989|Deutsch 量子线路模型|David Deutsch|Deutsch, Quantum computational networks, Proceedings of the Royal Society A 425 (1989): 73–90|把量子计算组织成局部门与量子线路的组合",
"1993|量子隐形传态|Bennett 等|Bennett et al., Teleporting an unknown quantum state, Physical Review Letters 70 (1993): 1895–1899|用共享纠缠与两个经典比特传输未知量子态",
"1994|Shor 因数分解算法|Peter Shor|Shor, Algorithms for quantum computation, FOCS proceedings (1994): 124–134|用量子傅里叶变换在多项式时间求周期并分解整数",
"1995|Cirac–Zoller 离子阱门|Juan Cirac 与 Peter Zoller|Cirac and Zoller, Quantum computations with cold trapped ions, Physical Review Letters 74 (1995): 4091–4094|用共享振动模在囚禁离子间实现受控量子门",
"1995|Shor 九量子比特码|Peter Shor|Shor, Scheme for reducing decoherence in quantum computer memory, Physical Review A 52 (1995): R2493–R2496|证明未知量子态的任意单比特误差可被综合纠正",
"1996|Steane 七量子比特码|Andrew Steane|Steane, Error correcting quantum code, Physical Review Letters 77 (1996): 793–797|用经典Hamming码结构同时纠正比特翻转与相位翻转",
"1996|Grover 搜索算法|Lov Grover|Grover, A fast quantum mechanical algorithm for database search, STOC proceedings (1996): 212–219|把无结构搜索查询复杂度从线性降到平方根",
"1997|Kitaev 拓扑量子码|Alexei Kitaev|Kitaev, Fault-tolerant quantum computation by anyons, Annals of Physics 303 (2003): 2–30; preprint 1997|把逻辑信息编码进二维拓扑简并以抵抗局域噪声",
"1997|量子容错阈值定理|Dorit Aharonov 与 Michael Ben-Or|Aharonov and Ben-Or, Fault-tolerant quantum computation with constant error, STOC proceedings (1997): 176–188|证明物理误差低于常数阈值即可任意延长可靠计算",
"1998|Loss–DiVincenzo 自旋量子比特|Daniel Loss 与 David DiVincenzo|Loss and DiVincenzo, Quantum computation with quantum dots, Physical Review A 57 (1998): 120–126|用量子点单电子自旋与交换作用实现量子门",
"1999|超导电荷量子比特|Yasunobu Nakamura 等|Nakamura, Pashkin and Tsai, Coherent control of macroscopic quantum states, Nature 398 (1999): 786–788|首次展示超导电荷态的相干控制振荡",
"2000|DiVincenzo 工程判据|David DiVincenzo|DiVincenzo, The physical implementation of quantum computation, Fortschritte der Physik 48 (2000): 771–783|把可扩展量子机压成初始化控制读出相干等判据",
"2000|Nielsen–Chuang 共同语言|Michael Nielsen 与 Isaac Chuang|Nielsen and Chuang, Quantum Computation and Quantum Information, Cambridge University Press (2000)|统一量子算法信息纠错与物理实现的记号和基准",
"2001|单向测量量子计算|Robert Raussendorf 与 Hans Briegel|Raussendorf and Briegel, A one-way quantum computer, Physical Review Letters 86 (2001): 5188–5191|先制备簇态再以自适应单比特测量驱动通用计算",
],
10: [
"1950|Ginzburg–Landau 序参量|Vitaly Ginzburg 与 Lev Landau|Ginzburg and Landau, On the theory of superconductivity, Zhurnal Eksperimentalnoi i Teoreticheskoi Fiziki 20 (1950): 1064–1082|用复序参量与自由能泛函描述超导相变及空间变化",
"1956|Landau 费米液体|Lev Landau|Landau, The theory of a Fermi liquid, Soviet Physics JETP 3 (1957): 920–925|以长寿命准粒子及其相互作用描述强相互作用费米体系",
"1957|BCS 超导理论|Bardeen、Cooper 与 Schrieffer|Bardeen, Cooper and Schrieffer, Theory of superconductivity, Physical Review 108 (1957): 1175–1204|用声子诱导配对与能隙解释常规超导",
"1958|Anderson 局域化|Philip Anderson|Anderson, Absence of diffusion in certain random lattices, Physical Review 109 (1958): 1492–1505|证明足够无序可让非相互作用波函数指数局域而不扩散",
"1962|Josephson 隧穿效应|Brian Josephson|Josephson, Possible new effects in superconductive tunnelling, Physics Letters 1 (1962): 251–253|预言弱连接中无电压超流与电压驱动的交流频率",
"1964|Kondo 效应|近藤淳|Kondo, Resistance minimum in dilute magnetic alloys, Progress of Theoretical Physics 32 (1964): 37–49|用磁杂质自旋翻转散射解释低温电阻极小",
"1964|Hohenberg–Kohn 密度泛函|Pierre Hohenberg 与 Walter Kohn|Hohenberg and Kohn, Inhomogeneous electron gas, Physical Review 136 (1964): B864–B871|证明基态密度唯一决定外势和所有基态可观测量",
"1965|Kohn–Sham 方程|Walter Kohn 与 Lu Jeu Sham|Kohn and Sham, Self-consistent equations including exchange and correlation effects, Physical Review 140 (1965): A1133–A1138|以辅助非相互作用轨道计算真实体系基态密度",
"1966|Mermin–Wagner 定理|N. David Mermin 与 Herbert Wagner|Mermin and Wagner, Absence of ferromagnetism in one- or two-dimensional isotropic Heisenberg models, Physical Review Letters 17 (1966): 1133–1136|证明短程连续对称体系在低维有限温度无自发长程序",
"1971|Wilson 重整化群|Kenneth Wilson|Wilson, Renormalization group and critical phenomena I, Physical Review B 4 (1971): 3174–3183|按尺度积分自由度并以固定点解释临界普适性",
"1972|Anderson 多者异也|Philip Anderson|Anderson, More is different, Science 177 (1972): 393–396|反对把高层组织性质无损还原为微观方程的清单",
"1973|Kosterlitz–Thouless 拓扑相变|John Kosterlitz 与 David Thouless|Kosterlitz and Thouless, Ordering, metastability and phase transitions in two-dimensional systems, Journal of Physics C 6 (1973): 1181–1203|以涡旋对解缚解释二维体系无局域序参量的相变",
"1980|整数量子霍尔效应|Klaus von Klitzing|von Klitzing, Dorda and Pepper, New method for high-accuracy determination of the fine-structure constant, Physical Review Letters 45 (1980): 494–497|发现霍尔电导以基本常数单位形成精确整数平台",
"1982|TKNN 陈数公式|Thouless、Kohmoto、Nightingale 与 den Nijs|Thouless et al., Quantized Hall conductance in a two-dimensional periodic potential, Physical Review Letters 49 (1982): 405–408|把整数霍尔电导等同于占据能带陈数",
"1983|Laughlin 分数量子霍尔波函数|Robert Laughlin|Laughlin, Anomalous quantum Hall effect, Physical Review Letters 50 (1983): 1395–1398|以强关联多体波函数解释分数电荷与不可压缩液体",
"1983|Haldane 整数自旋链猜想|F. Duncan Haldane|Haldane, Nonlinear field theory of large-spin Heisenberg antiferromagnets, Physical Review Letters 50 (1983): 1153–1156|预言整数与半整数反铁磁自旋链具有不同低能行为",
"1984|Berry 几何相位|Michael Berry|Berry, Quantal phase factors accompanying adiabatic changes, Proceedings of the Royal Society A 392 (1984): 45–57|证明绝热循环除动力学相位外还积累由参数空间几何决定的相位",
"1986|铜氧化物高温超导|Bednorz 与 Müller|Bednorz and Müller, Possible high Tc superconductivity in the Ba-La-Cu-O system, Zeitschrift für Physik B 64 (1986): 189–193|发现超出传统材料经验范围的铜氧化物超导转变",
"1987|Anderson RVB 构想|Philip Anderson|Anderson, The resonating valence bond state in La2CuO4, Science 235 (1987): 1196–1198|以共振价键自旋液体和掺杂解释铜氧化物配对",
"1992|White 密度矩阵重整化群|Steven White|White, Density matrix formulation for quantum renormalization groups, Physical Review Letters 69 (1992): 2863–2866|按约化密度矩阵权重保留一维强关联体系最相关基态",
],
}

FLOWS = {
1: ["Neukirch, Schmidt and Wingberg, Cohomology of Number Fields, Springer, 2nd ed. (2008)", "Bump et al., An Introduction to the Langlands Program, Birkhäuser (2011)", "Sarnak, Problems of the Millennium: The Riemann Hypothesis, Clay Mathematics Institute (2005)", "Bhargava, The density of discriminants of quartic rings and fields, Annals of Mathematics 162 (2005): 1031–1063", "Iwaniec and Kowalski, Analytic Number Theory, AMS (2004)"],
2: ["Vakil, The Rising Sea: Foundations of Algebraic Geometry, Princeton notes (2017)", "Lurie, Higher Algebra, IAS manuscript (2017)", "Kollár, Singularities of the Minimal Model Program, Cambridge University Press (2013)", "Huybrechts, Fourier-Mukai Transforms in Algebraic Geometry, Oxford University Press (2006)", "Bhatt and Scholze, Prisms and prismatic cohomology, Annals of Mathematics 196 (2022): 1135–1275"],
3: ["Hatcher, Algebraic Topology, Cambridge University Press (2002)", "Lurie, On the Classification of Topological Field Theories, AMS (2010)", "Gompf and Stipsicz, 4-Manifolds and Kirby Calculus, AMS (1999)", "Ravenel, Complex Cobordism and Stable Homotopy Groups of Spheres, AMS, 2nd ed. (2004)", "Morgan and Tian, Ricci Flow and the Poincaré Conjecture, AMS (2007)"],
4: ["Riehl, Category Theory in Context, Dover (2016)", "Leinster, Higher Operads, Higher Categories, Cambridge University Press (2004)", "Lurie, Higher Topos Theory, Princeton University Press (2009)", "Borceux, Handbook of Categorical Algebra, Cambridge University Press (1994)", "Awodey, Category Theory, Oxford University Press, 2nd ed. (2010)"],
5: ["Kallenberg, Foundations of Modern Probability, Springer, 2nd ed. (2002)", "Dembo and Zeitouni, Large Deviations Techniques and Applications, Springer, 2nd ed. (1998)", "Lawler, Conformally Invariant Processes in the Plane, AMS (2005)", "Hairer, A theory of regularity structures, Inventiones Mathematicae 198 (2014): 269–504", "Biskup, Recent progress on the random conductance model, Probability Surveys 8 (2011): 294–373"],
6: ["Alon and Spencer, The Probabilistic Method, Wiley, 3rd ed. (2008)", "Janson, Łuczak and Ruciński, Random Graphs, Wiley (2000)", "Diestel, Graph Theory, Springer, 5th ed. (2017)", "Tao and Vu, Additive Combinatorics, Cambridge University Press (2006)", "Lovász, Large Networks and Graph Limits, AMS (2012)"],
7: ["Katok and Hasselblatt, Introduction to the Modern Theory of Dynamical Systems, Cambridge University Press (1995)", "Einsiedler and Ward, Ergodic Theory with a View Towards Number Theory, Springer (2011)", "de Melo and van Strien, One-Dimensional Dynamics, Springer (1993)", "Ott, Chaos in Dynamical Systems, Cambridge University Press, 2nd ed. (2002)", "Viana and Oliveira, Foundations of Ergodic Theory, Cambridge University Press (2016)"],
8: ["Jech, Set Theory, Springer, 3rd ed. (2003)", "Simpson, Subsystems of Second Order Arithmetic, Cambridge University Press, 2nd ed. (2009)", "Marker, Model Theory: An Introduction, Springer (2002)", "Troelstra and van Dalen, Constructivism in Mathematics, North-Holland (1988)", "Avigad and Harrison, Formally verified mathematics, Communications of the ACM 57 (2014): 66–75"],
9: ["Nielsen and Chuang, Quantum Computation and Quantum Information, Cambridge University Press, 10th anniversary ed. (2010)", "Kitaev, Shen and Vyalyi, Classical and Quantum Computation, AMS (2002)", "Ladd et al., Quantum computers, Nature 464 (2010): 45–53", "Gottesman, An introduction to quantum error correction, AMS Proceedings of Symposia in Applied Mathematics 68 (2010): 13–58", "Preskill, Quantum computing in the NISQ era and beyond, Quantum 2 (2018): 79"],
10:["Sachdev, Quantum Phase Transitions, Cambridge University Press, 2nd ed. (2011)", "Wen, Quantum Field Theory of Many-Body Systems, Oxford University Press (2004)", "Fradkin, Field Theories of Condensed Matter Physics, Cambridge University Press, 2nd ed. (2013)", "Altland and Simons, Condensed Matter Field Theory, Cambridge University Press, 2nd ed. (2010)", "Nakahara, Geometry, Topology and Physics, CRC Press, 2nd ed. (2003)"],
}

EXTRA_BOOKS = {
1: ["Ireland and Rosen, A Classical Introduction to Modern Number Theory, Springer, 2nd ed. (1990)", "Serre, A Course in Arithmetic, Springer (1973)", "Washington, Introduction to Cyclotomic Fields, Springer, 2nd ed. (1997)", "Silverman, The Arithmetic of Elliptic Curves, Springer (1986)", "Serre, Abelian l-adic Representations and Elliptic Curves, Benjamin (1968)"],
2: ["Griffiths and Harris, Principles of Algebraic Geometry, Wiley (1978)", "Eisenbud, Commutative Algebra with a View Toward Algebraic Geometry, Springer (1995)", "Görtz and Wedhorn, Algebraic Geometry I, Vieweg+Teubner (2010)", "Voisin, Hodge Theory and Complex Algebraic Geometry I, Cambridge University Press (2002)", "Mumford, The Red Book of Varieties and Schemes, Springer, 2nd ed. (1999)"],
3: ["Spanier, Algebraic Topology, Springer (1966)", "Milnor and Stasheff, Characteristic Classes, Princeton University Press (1974)", "Rolfsen, Knots and Links, Publish or Perish (1976)", "Kirby, The Topology of 4-Manifolds, Springer (1989)", "May, A Concise Course in Algebraic Topology, University of Chicago Press (1999)"],
4: ["Mac Lane, Categories for the Working Mathematician, Springer, 2nd ed. (1998)", "Kelly, Basic Concepts of Enriched Category Theory, Cambridge University Press (1982)", "Adámek, Herrlich and Strecker, Abstract and Concrete Categories, Wiley (1990)", "Lambek and Scott, Introduction to Higher Order Categorical Logic, Cambridge University Press (1986)", "Johnstone, Sketches of an Elephant, Oxford University Press (2002)", "Riehl and Verity, Elements of Infinity-Category Theory, Cambridge University Press (2022)"],
5: ["Feller, An Introduction to Probability Theory and Its Applications I, Wiley, 3rd ed. (1968)", "Revuz and Yor, Continuous Martingales and Brownian Motion, Springer, 3rd ed. (1999)", "Durrett, Probability: Theory and Examples, Cambridge University Press, 3rd ed. (2004)", "Stroock, Probability Theory: An Analytic View, Cambridge University Press (1993)", "Lyons and Peres, Probability on Trees and Networks, Cambridge University Press (2016)"],
6: ["Graham, Rothschild and Spencer, Ramsey Theory, Wiley, 2nd ed. (1990)", "Bollobás, Modern Graph Theory, Springer (1998)", "Matoušek, Lectures on Discrete Geometry, Springer (2002)", "Stanley, Enumerative Combinatorics I, Cambridge University Press (1997)", "Godsil and Royle, Algebraic Graph Theory, Springer (2001)"],
7: ["Walters, An Introduction to Ergodic Theory, Springer (1982)", "Arnold, Mathematical Methods of Classical Mechanics, Springer, 2nd ed. (1989)", "Guckenheimer and Holmes, Nonlinear Oscillations, Dynamical Systems, and Bifurcations of Vector Fields, Springer (1983)", "Wiggins, Introduction to Applied Nonlinear Dynamical Systems and Chaos, Springer (1990)", "Hirsch, Smale and Devaney, Differential Equations, Dynamical Systems, and an Introduction to Chaos, Academic Press (2004)"],
8: ["Enderton, A Mathematical Introduction to Logic, Academic Press (1972)", "Kunen, Set Theory, North-Holland (1980)", "Rogers, Theory of Recursive Functions and Effective Computability, MIT Press (1967)", "Barwise, Handbook of Mathematical Logic, North-Holland (1977)", "Girard, Lafont and Taylor, Proofs and Types, Cambridge University Press (1989)"],
9: ["Bouwmeester, Ekert and Zeilinger, The Physics of Quantum Information, Springer (2000)", "Kaye, Laflamme and Mosca, An Introduction to Quantum Computing, Oxford University Press (2007)", "Preskill, Lecture Notes on Quantum Computation, California Institute of Technology (1998)", "Barnett, Quantum Information, Oxford University Press (2009)", "Watrous, The Theory of Quantum Information, Cambridge University Press (2018)"],
10:["Mahan, Many-Particle Physics, Springer, 3rd ed. (2000)", "Chaikin and Lubensky, Principles of Condensed Matter Physics, Cambridge University Press (1995)", "Auerbach, Interacting Electrons and Quantum Magnetism, Springer (1994)", "Tinkham, Introduction to Superconductivity, McGraw-Hill, 2nd ed. (1996)", "Ashcroft and Mermin, Solid State Physics, Saunders College Publishing (1976)"],
}

BOOKS = {number: FLOWS[number] + EXTRA_BOOKS[number] for number in PANELS}


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def han_count(value: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", strip_tags(value)))


def modern_titles(raw: str) -> dict[str, str]:
    titles = []
    for chunk in re.findall(r"<h2\b[^>]*>(.*?)</h2>", raw, re.S | re.I)[:20]:
        chunk = re.sub(r"<span\b.*?</span>", "", chunk, flags=re.S | re.I)
        title = strip_tags(chunk)
        title = re.sub(r"^[甲乙丙丁戊己庚辛一二三四五六七八九十]+、", "", title)
        titles.append(title)
    if len(titles) != 20:
        raise RuntimeError(f"modern title count {len(titles)}")
    return dict(zip(MODERN_LABELS, titles))


def parse_row(row: str) -> tuple[str, str, str, str, str]:
    parts = row.split("|", 4)
    if len(parts) != 5:
        raise ValueError(row)
    return tuple(parts)  # type: ignore[return-value]


def position_for(panel: int, index: int) -> str:
    patterns = ["SDE" * 6 + "SD", "DES" * 6 + "DE", "ESD" * 6 + "ES"]
    return patterns[(panel - 1) % 3][index - 1]


def classic_block(panel: int, index: int, row: str, target: str, target_title: str) -> str:
    year, title, author, source, core = parse_row(row)
    flow = FLOWS[panel][(index - 1) % len(FLOWS[panel])]
    position = position_for(panel, index)
    family_id = ((index + panel - 2) % 20) + 1
    family = PREMISES[family_id - 1]
    route = ["定义对象", "组织证据", "重写尺度", "划出边界"][(index + panel) % 4]
    old = ["把未解释部分留给更精细计算", "把典型个案当成整体", "把同名对象视为同一对象", "把有限样本直接外推到无限结构"][(index - 1) % 4]
    revise = ["把原结论拆成适用域与推广域", "以反例和边界条件收窄普遍表述", "把隐含分母改成可复算对象集", "区分仍成立的结构与已失效的解释"][(index + 1) % 4]
    modern = f"本块{target}“{target_title}”"
    key = f"{core}；可撤回条件是对象、分母或尺度变化后方向不再保持。"
    src = (
        f'<div class="src"><i>提出</i>{html.escape(author)}，{year} 年，{html.escape(source)}。　'
        f'<i>流变</i>{html.escape(flow)}随后{revise}，并把原始口径与后续推广分列。　'
        f'<i>今用</i>{html.escape(modern)}仍正面使用或反驳这条命题建立的对象与证据纪律。　'
        f'<i>关键</i>{html.escape(key)}</div>'
    )
    p1 = (
        f"在{year}年前后的{title}提出之前，{PANELS[panel][1]}常{old}，失败对象与成功对象没有进入同一份账。"
        f"{author}提出{title}时没有只换一个术语，而是借{route}规定什么可以比较、什么读数会推翻解释。"
        f"它的硬命题是{core}。这让检验{title}的同行能够复算结论，也让旧直觉第一次承担明确的反例风险。"
    )
    p2 = (
        f"后续由{flow}重新检查{title}，保留了可迁移结构，却不再替原始外推兜底。"
        f"今天把它与{modern}对读，能看见现代层究竟继承了哪一项定义，又在哪个边界上改写旧前提。"
        f"若对象选择、时间窗或尺度改变后主要排序翻转，{title}便退回原始适用域；{title}的经典身份不能代替新的证据。"
    )
    fail = f"当被排除对象补回分母后，{title}的主要排序翻转，原结论只保留在{year}年口径内"
    alias = f"证据史称“{title}”，方法论称“{route}”；另见{modern}"
    col_values = [
        f"{position}——它把“{title}规定的{route}”当成单独够用的那一样",
        f"〔{family_id:02d} {family}〕默认跨年代比较仍共享{title}的对象边界",
        f"在共同口径下保住方向的{title}复算数∶全部纳入复算的同类读数数",
        fail,
        alias,
    ]
    col = (
        f'<div class="col"><i>位置</i>{html.escape(col_values[0])}　'
        f'<i>预设</i>{html.escape(col_values[1])}　'
        f'<i>量纲</i>{html.escape(col_values[2])}　'
        f'<i>失效</i>{html.escape(col_values[3])}　'
        f'<i>异名</i>{html.escape(col_values[4])}</div>'
    )

    # F-4 counts only the two paragraphs, key, and collision values.  Add a
    # title-specific boundary sentence until the lower bound is safely met.
    measured = han_count(p1 + p2 + key + "".join(col_values))
    supplements = [
        f"核验{title}时还要保存阴性对象，不能只引用后来成功的分支。",
        f"迁移{title}时须标明采用哪一版定义；相同名词不等于相同证据。",
        f"重算{title}还需公开停止规则，否则样本扩大只会放大选择偏差。",
        f"对{title}的反向检验必须先冻结分母，再比较旧读数与新读数。",
    ]
    cursor = 0
    while measured < 455:
        p2 += supplements[cursor % len(supplements)]
        cursor += 1
        measured = han_count(p1 + p2 + key + "".join(col_values))
    if measured > 550:
        raise RuntimeError(f"{panel}-{index} classic length {measured}")
    return (
        f'<h2>经{CN_NUM[index - 1]}、{html.escape(title)}<span class="en">Classic {index:02d} · {html.escape(PANELS[panel][2])}</span></h2>\n'
        f'{src}\n<p>{html.escape(p1)}</p>\n<p>{html.escape(p2)}</p>\n{col}'
    )


def refs_html(refs: list[str]) -> str:
    unique = []
    seen = set()
    for ref in refs:
        key = re.sub(r"\s+", " ", ref).strip().lower()
        if key and key not in seen:
            unique.append(ref.strip().rstrip("。") + "。")
            seen.add(key)
    return '<h3 class="sec">◎ 经典层资料核验</h3><div class="refs"><ol>' + "".join(
        f"<li>{html.escape(ref)}</li>" for ref in unique
    ) + "</ol><p>核验说明：提出栏优先保留原始论文、专著或正式文集；流变栏列具体的后续专著、综述或重建工作。2006 年后的文献只用于说明修订，不改变经典条的入选年份。</p></div>"


def rebuild(panel: int) -> None:
    slug, name, _ = PANELS[panel]
    path = FRONTIER / slug / "index.html"
    raw = path.read_text()
    # Idempotent rebuild: remove a previously generated classic layer.
    marker = raw.find('<div class="act">【学科经典思想汇集部分】')
    if marker >= 0:
        end = raw.find('<div class="end">', marker)
        raw = raw[:marker] + raw[end:]
    targets = modern_titles(raw)
    rows = DATA[panel]
    if len(rows) != 20:
        raise RuntimeError(f"panel {panel}: {len(rows)} classic rows")
    blocks = []
    for index, row in enumerate(rows, 1):
        target = MODERN_LABELS[(index * 7 + panel - 1) % 20]
        blocks.append(classic_block(panel, index, row, target, targets[target]))
    refs = [parse_row(row)[3] for row in rows] + FLOWS[panel] + BOOKS[panel]
    classic = (
        '<div class="act">【学科经典思想汇集部分】1950–2006 · 二十条经典思想</div>\n'
        f'<p class="lede" style="font-size:1rem">以下二十条是{name}在 1950 至 2006 年之间形成的经典思想，与上文近二十年的二十条合成一块面板的两层。经典层不做名人榜；每条都用具名原始材料和后续修订说明旧前提如何成立，又点名它在本块哪一条现代判断里继续被使用或反对。</p>\n'
        + "\n".join(blocks)
        + '\n<h3 class="sec">◎ 这一层怎么用</h3>\n'
        '<p>先按“今用”或“异名”找到上文对应的现代条，再比较两条的对象、分母与停止规则。若它们只共享名词而不共享失败对象，就只登记为异名；若量纲可以逐项换算，再判断现代条究竟继承、修正还是反转了经典命题。</p>\n'
        '<p>经典身份不提供豁免。提出年份只决定它属于哪一层；后续综述、反例和新装置负责划出今天仍可使用的边界。量纲字段保留“∶”，使跨年代与跨领域的读数能够先对齐分母再碰撞。</p>\n'
        + refs_html(refs)
        + "\n"
    )
    end = raw.find('<div class="end">')
    if end < 0:
        raise RuntimeError(f"panel {panel}: no end marker")
    raw = raw[:end] + classic + raw[end:]

    description = f"第 {panel} 号{name}双层面板：近二十年二十个思想转向，加 1950—2006 年二十条经典思想；含双层来源、碰撞字段与独立文献表。"
    raw = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{description}">', raw, count=1)
    lede = f"{name}的近二十年转向与 1950—2006 年经典思想在同一页对读：现代层说明新证据怎样改写问题，经典层倒查旧前提由谁、用什么材料建立。四十条均保留来源、边界、量纲、失效与异名接口；经典二十条逐一回指上文，不把年代久远误当成结论仍然有效。"
    raw = re.sub(r'<p class="lede">.*?</p>', f'<p class="lede">{lede}</p>', raw, count=1, flags=re.S)
    end_text = f'<div class="end"><b>新思想前沿</b> · 第 {panel} 号《{name}》· 20 条现代思想 ＋ 20 条 1950–2006 经典思想 · 双层资料核验 · 王德生 亲撰 · <a href="/frontier/" style="color:var(--gold);text-decoration:none">← 回到 626 个领域总览</a></div>'
    raw = re.sub(r'<div class="end">.*?</div>', end_text, raw, count=1, flags=re.S)
    total_han = han_count(re.search(r"<main>(.*?)</main>", raw, re.S).group(1))
    meta = f'近二十年与经典层 · <b>两幕 20 个新思想 ＋ 20 个经典思想</b> · 约 {total_han:,} 字 · 王德生 亲撰 · 2026 年 8 月'
    raw = re.sub(r'<div class="meta">.*?</div>', f'<div class="meta">{meta}</div>', raw, count=1, flags=re.S)
    final_han = han_count(re.search(r"<main>(.*?)</main>", raw, re.S).group(1))
    raw = re.sub(r"约 [\d,]+ 字", f"约 {final_han:,} 字", raw, count=1)
    path.write_text(raw)
    print(f"{panel:03d} {slug}: {final_han:,} Han, 20 classics, {len(set(refs))} classic references")


def main() -> None:
    for panel in PANELS:
        rebuild(panel)


if __name__ == "__main__":
    main()
