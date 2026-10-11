/* sde-intake.js —— 来稿初审引擎  window.SDEIntake
 *
 * 2026-10-11 王德生令：「这是初审的指导书和细节要求，按照这个打造一个来稿初审智能体，输出意见书 WORD，
 * 同样上站 ChatSDE。每个要求都要检查和满足。」
 *
 * 依据：《来稿初审指导书》四章——结构完整性审查／体例审查／内容审查／交互素材与资源审查。
 * 指导书里的每一条要求，都在下面的 CHECK 清单里有一个编号；意见书第二部分逐条给出结论，
 * 一条都不许空着：查得出的由代码查（机检），要读懂的由基底逐单元审读后给结论（审读），
 * 机器看不见的（图片画面、视频画面、地图国界、照片备案、授权文件）明写「提请人工」或「需作者提供」。
 *
 * 三条纪律（改之前先读）：
 * ① 结论只有五种：符合／不符合／需作者确认／提请人工／未检（并写原因）。不许写「符合出版要求」。
 * ② 机检的数（字数、图表编号、图片分辨率、链接、标准年号……）由代码算，不问模型；模型只做要读懂的判断。
 * ③ 意见书是给编辑与作者的，用平常话，不出现任何学派术语。
 *
 * 用法（ChatSDE 的 sendCs 调用）：
 *   var info = SDEIntake.parseInfo(输入框文字, 正文);
 *   var mc   = SDEIntake.machine({ text, meta, others, res, info });   // 机检：立即出结果
 *   SDEIntake.unitPrompt(...) / parseUnit(...) / itemsPrompt(...) / letterPrompt(...)
 *   var blob = SDEIntake.buildDocx(report);                            // 意见书 Word（真表格）
 */
(function (w) {
  "use strict";
  if (w.SDEIntake) return;

  /* ═════════ 一、核对清单：指导书的每一条要求 ═════════
     how: code＝代码机检；model＝审读判断；mix＝代码先查、审读补判；human＝只能人看（给出提请人工及依据） */
  var CH = [
    ["S", "第一章 结构完整性审查"],
    ["T", "第二章 体例审查"],
    ["P", "第三章 内容审查 · 政治性"],
    ["C", "第三章 内容审查 · 版权"],
    ["L", "第三章 内容审查 · 栏目设置"],
    ["Z", "第三章 内容审查 · 思政融入"],
    ["K", "第三章 内容审查 · 知识架构（辅文、准确性、时效性）"],
    ["Y", "第三章 内容审查 · 语言表达与字词标点"],
    ["F", "第三章 内容审查 · 公式、图、表合规性"],
    ["N", "第三章 内容审查 · 版面字数"],
    ["R", "第四章 交互素材与资源审查"]
  ];
  var CHECK = [
    // 第一章
    ["S01", "核心模块：内容提要", "必须有内容提要（对照《数字教材出版通用规范》核对核心模块）", "code"],
    ["S02", "核心模块：前言", "必须有前言（序、序言、编写说明等）", "code"],
    ["S03", "核心模块：目录", "必须有目录", "code"],
    ["S04", "核心模块：正文内容", "正文完整", "code"],
    ["S05", "核心模块：参考文献", "必须有参考文献", "code"],
    ["S06", "拓展模块：引导性栏目", "学习目标、案例引入等，全书各章统一", "code"],
    ["S07", "拓展模块：总结性栏目", "本章小结、任务总结等，全书各章统一", "code"],
    ["S08", "拓展模块：扩展性模块", "知识链接、拓展阅读等，全书各章统一", "code"],
    ["S09", "拓展模块：考核性栏目", "课后练习、任务实训等，全书各章统一", "code"],
    ["S10", "附加模块的正文引用", "正文提及「见附录／见附件」的，附录、附件须实际存在并相互对应", "code"],
    ["S11", "教学链路完整", "覆盖「预习—学习—练习—拓展」全链路，无结构断层", "mix"],
    ["S12", "内容递进", "先易后难、先基础后深入，递进式发展", "model"],
    ["S13", "实训任务单／知识框架图", "实操类建议含「实训任务单」，理论类建议含「知识框架图」", "code"],
    // 第二章
    ["T01", "层级逻辑规则", "章→节→知识点→子知识点（或篇→章→节→…）；属篇章节式、章节式、模块项目任务式、项目任务式或其他形式之一", "code"],
    ["T02", "层级编码全稿统一", "同级标题编号样式一致、序号连续不跳号", "code"],
    ["T03", "上下两级标题不相同", "相邻的上下两级标题文字不得相同", "code"],
    ["T04", "（1）级以下标题接排", "（1）、①、a. 级标题往后都接排正文、不加粗", "code"],
    ["T05", "图表编号规则统一", "全稿统一一种编序：以篇（模块）／章（项目）为单位（图1-1、表1-1），或以篇-章／模块-项目为单位（图1-1-1、表1-1-1）", "code"],
    ["T06", "图表编号唯一、连续", "编号唯一、连续，删图后须重编，无跳号、重号", "code"],
    ["T07", "图有正文引用", "知识性图片须有图号及正文引用（如图X-X所示），图文对应", "code"],
    ["T08", "表有正文引用", "表格须有表号及正文引用，表文对应", "code"],
    ["T09", "无号图片", "知识性图片原则上必须有图号（可无图名）；全稿处理方式统一", "code"],
    ["T10", "知识点排布", "概念定义→原理讲解→案例分析→实践任务，无逻辑倒置", "model"],
    ["T11", "内容占比", "核心知识>60%，拓展知识<40%", "mix"],
    // 第三章 政治性
    ["P01", "涉港澳台内容", "不得将港澳台列为国家、与中国并列，不得以中央、国家名义设机构", "mix"],
    ["P02", "民族宗教、历史虚无主义、错误价值观、地域歧视", "言必有据；尊重民族习俗与宗教信仰；客观介绍不渲染；与官方正史一致", "model"],
    ["P03", "国家主权和形象", "维护领土完整统一；尊重国家象征；区分国际组织性质；外国地名表述规范", "mix"],
    ["P04", "我国制度和意识形态", "制度和理念阐述准确；禁止宣扬错误意识形态；时政表述准确", "model"],
    ["P05", "重大历史事件和人物", "科学评价党史重要事件、会议、人物；留意说法变化", "model"],
    ["P06", "党和国家重要领导人及讲话", "照片履行备案；姓名职务准确；直接引语一字不差", "mix"],
    ["P07", "敏感人物和企业", "认定主流标签，与官方媒体、官方观点一致", "model"],
    ["P08", "社会价值导向", "无低俗、暴力、违法内容；无错误导向的示范（如安全生产案例中的违规操作、客户沟通案例中的不当话术）；禁止宣扬违法违规；反对低俗、庸俗、媚俗；宣传正确人生观、价值观；理性客观分析社会热点", "model"],
    ["P09", "涉密信息", "不得出现涉密内容（如高校科研保密数据）", "mix"],
    ["P10", "地图", "除具有审图号的公益性地图、景区地图、街区地图、公共交通线路图等内容简单的地图，以及法律法规明确应予公开且不涉及国界、边界、历史疆界、行政区域界线的地图外，其他地图均须审核；涉及国界线的尤须重视；古代、近代地图标准统一", "mix"],
    ["P11", "辱华图片、品牌、言论艺术家", "不得使用丑化华人图片、辱华品牌、辱华言论艺术家作品", "mix"],
    ["P12", "劣迹艺人", "不得出现指导书所列劣迹艺人", "code"],
    ["P13", "暴露图片", "无裸体、服装暴露、性暗示图片", "human"],
    ["P14", "国内外领导人图片", "国内外领导人图片须核查", "human"],
    ["P15", "视频的政治性审查", "同文字、图片要求；快速浏览，重点看画面，敏感片段检听音频", "human"],
    // 版权
    ["C01", "原创比例", "原创≥70%，即查重报告重复率<30%；原创比例计算不含行业标准、通用公式等公共知识；外部稿件提供一次免费查重，重复率高须降重，返稿附降重后的查重报告；自组稿件由组稿人员查重、交稿时附报告（可用知网、Turnitin、理工智慧等）", "mix"],
    ["C02", "无大段抄袭", "文字内容避免大段抄袭（如整节照搬其他教材）", "human"],
    ["C03", "校企合作案例、企业技术资料", "须取得合作企业授权", "code"],
    ["C04", "行业标准、技术手册引用", "引用须标注版权方", "code"],
    ["C05", "引用标注来源", "引用部分尽量标注来源", "model"],
    ["C06", "图片版权", "摄影作品、设计作品、人物相片须具有公共版权，或取得版权方授权／肖像权，或符合《中华人民共和国著作权法》第二十四、二十五条规定的适当引用范围", "human"],
    ["C07", "音视频版权", "与作者确认；据片头院校、书名信息初步判断", "human"],
    ["C08", "超链接来源", "可少量引用政府、事业单位、权威学术与行业平台；禁止百度百科、维基百科、个人博客、论坛、商业资讯网站、非官方公众号", "code"],
    ["C09", "标注禁止转载的链接", "标注「未经授权禁止转载」等的网站（如学习强国）未获授权不得引用", "code"],
    // 栏目
    ["L01", "栏目与教学场景适配", "章前学习目标、案例引入帮助预习，章末小结、练习帮助复习；位置正确", "code"],
    ["L02", "栏目与人才培养方案适配", "学习目标覆盖专业核心能力，符合《职业教育专业目录》或《普通高等学校本科专业目录》", "mix"],
    ["L03", "栏目与学情适配", "难度由浅入深、无知识断层、不超纲也不过浅", "model"],
    ["L04", "三维教学目标", "每章／节明确知识目标、能力目标、素养目标", "code"],
    ["L05", "目标可落地", "正文能支撑目标达成，能力目标配套实操或练习", "model"],
    ["L06", "栏目非形式化", "各章栏目内容与本章匹配，不为统一而照抄", "code"],
    // 思政
    ["Z01", "思政有融入", "通过栏目（素养提升）或内容、案例（如大国工匠）融入，无「无思政」「思政缺失」，符合《高校教材管理办法》等政策要求", "mix"],
    ["Z02", "融入自然", "与专业内容有机结合，无两张皮，无空话套话，不刻意设生硬的思政栏目", "model"],
    ["Z03", "思政元素与学科相关", "家国情怀、科学精神、职业操守、法治意识等与学科相关", "model"],
    ["Z04", "国家战略、重大政策表述", "双碳、乡村振兴、新职业教育法等表述与官方口径完全一致；贴合《国家职业教育改革实施方案》，产教融合、校企合作等表述准确", "mix"],
    // 知识架构
    ["K01", "书名、主编与选题一致", "书名、主编信息与选题一致", "mix"],
    ["K02", "内容提要", "介绍主要内容、读者对象（层次与适用专业）、特色；与正文、目录顺序一致；约300字", "mix"],
    ["K03", "前言／序言", "编写背景（政策表述与官方一致）、内容（可简述）、特色、编写分工（名单与版权页一致、分工与章节对应，无作者无内容或内容无作者）、致谢、自谦；他序放在前言之前、标题用「序」", "mix"],
    ["K04", "目录", "目录单独提供；标题与正文一致（不一致须与作者确认，或默认以正文为准）；层级全稿一致；上下两级不同；相近标题形式统一", "code"],
    ["K05", "参考文献著录", "符合 GB/T 7714—2025《信息与文献 参考文献著录规则》", "code"],
    ["K06", "附录", "无政治性、知识性错误与涉密内容；多项按附录A、附录B编排，附录中的图表编号；所列标准、法律、政府文件现行有效；与正文对应统一；内容正确、术语符合标准并与正文统一；图样绘制方法符合国标行标；与主题相关、有补充价值不冗余；数据文献准确完整；排版格式与正文统一", "mix"],
    ["K07", "理论、概念准确", "符合学科主流观点，无过时理论、常识性错误、公式推导漏洞；理论深度够用为度", "model"],
    ["K08", "数据、案例真实", "数据真实、标注权威来源、近3年（行业近1—2年）；案例真实可追溯", "mix"],
    ["K09", "国家／行业标准时效", "已过时废止的必须更新；正在实施但已明确废止日期的强烈要求更新；正在实施的无须更新（到工标网 csres.com 核查）", "mix"],
    ["K10", "法律法规时效", "法律法规现行有效（如《民法典》施行后婚姻法、合同法等九部法律废止）", "code"],
    ["K11", "技术时效与前沿内容", "理论、技术、设备的更新（非必须）；前沿内容占比≥20%", "mix"],
    ["Y01", "专业术语统一规范", "全书统一，无一词多称、无自造术语，符合国标、行规（可查术语在线）", "model"],
    ["Y02", "行业俗称", "用行业俗称须标注规范术语", "model"],
    ["Y03", "术语不得简化", "术语不得简化（如「电子商务」不简作「电商」）", "code"],
    ["Y04", "标准规范简称", "标准、法规可合理简化，首次须写全称并说明「下文简称」", "code"],
    ["Y05", "病句", "主语混乱、搭配不当、成分残缺或多余、语序不当、歧义、句式杂糅、逻辑有误", "model"],
    ["Y06", "口语化", "避免口语化表达", "mix"],
    ["Y07", "表述模糊", "技术操作步骤指令明确，避免「大概」「可能」等模糊表述", "mix"],
    ["Y08", "错字、别字", "无错别字", "mix"],
    ["Y09", "生造词语", "无生造词语", "model"],
    ["Y10", "网络词语", "不泛用网络词语", "code"],
    ["Y11", "中外文混用", "无中外文词语混用", "code"],
    ["Y12", "标点与数字用法", "标点符号与数字用法规范（GB/T 15834、GB/T 15835）", "mix"],
    ["F01", "公式推导完整", "推导步骤完整，无跳越", "model"],
    ["F02", "公式不是图片", "公式须可编辑，不得为图片", "code"],
    ["F03", "无低版本公式编辑器", "不得用 Equation Editor 3.0 等低版本编辑器", "code"],
    ["F04", "图文对应", "图片属正文一部分，图文传达的内容相互对应（建议图片插入正文，便于审核对应性及核算字数）", "mix"],
    ["F05", "实物图清晰度", "不低于1280×720像素，建议1920×1080；放大到1/3屏宽细节清晰", "code"],
    ["F06", "线条图清晰与源文件", "最低要求线条、文字清晰可辨；常规要求同实物图（不低于1280×720）；复杂线条图（待绘线条超过20条，建筑、机械、电气类多属此类）须提供CAD等可编辑源文件", "mix"],
    ["F07", "AI生成图片", "AI生成须标注来源；已标注的须符合生活逻辑与常识；疑似未标注的须与作者确认", "mix"],
    ["F08", "表格可复制", "表格须为可编辑表格，不得为图片", "code"],
    ["F09", "表序号不与图混排", "表格用表序号，不与图序号混排", "code"],
    ["N01", "字数核算", "版面出版字数＝（满版情况下）行数×列数×总面数×折算系数；实际出版字数＝版面出版字数＋气泡、交互习题出版字数；其他素材另行折算", "code"],
    ["N02", "字数要求", "职业教育35万字；本科理工50万字、文管45万字；专著20万字", "code"],
    ["N03", "图片及空白版折算系数", "艺术类实物图（重点看图文对应）0.2；计算机类实物图（含少量参数）0.5；机械、建筑、电气类线条图（含大量参数）0.8", "code"],
    ["N04", "气泡、交互习题折算", "气泡、交互习题统一按100字/个（条）折算", "code"],
    ["N05", "附件字数折算", "Word 附件按正文标准统计；需审校的 PDF 转 Word 后按 Word 统计；PPT 如须在教材中展示按200字/面；Excel 单独提供的按正文版面字数统计；专业图片、图纸按0.2／0.5／0.8折算", "code"],
    ["R01", "气泡", "名词或名人解释，一般50～100字", "code"],
    ["R02", "拓展阅读", "知识链接、知识拓展等可折叠展开", "code"],
    ["R03", "超链接作为辅助", "官方网站、稳定、已授权；不得作为正文重要组成部分", "mix"],
    ["R04", "交互习题答案", "选择、填空、判断、排序、配对题须提供答案（简答题可不提供）", "code"],
    ["R05", "音视频内容", "画面声音清晰；时长合理；书名、院校名称准确；字幕无大量错误", "human"],
    ["R06", "单个音视频大小", "单个控制在100MB以内，超过200MB无法上传", "code"],
    ["R07", "资源总容量", "职业教育5G，本科8G，专著0G", "code"],
    ["R08", "音视频格式", "MP4，编码H.264", "code"],
    ["R09", "其他嵌入文件", "单个≤100MB，格式在支持列表内", "code"],
    ["R10", "资源位置标注", "正文中清晰标注资源位置，与章节知识点强关联", "mix"],
    ["R11", "附件形式", "需三审三校的附件用 Word：数字新稿直接编写在正文对应位置、不单独提供，纸质转数字稿可单独提供；PDF 只放无须审校的标准规范、法律法规条文，需审校的转为 Word；PPT 课件建议单独提供给院校教师，不插入教材；Excel 工单表、习题应与正文一同编写", "code"]
  ];
  var BY = {}; CHECK.forEach(function (c) { BY[c[0]] = { id: c[0], name: c[1], req: c[2], how: c[3] }; });
  var MODEL_IDS = CHECK.filter(function (c) { return c[3] === "model" || c[3] === "mix"; }).map(function (c) { return c[0]; });

  /* ═════════ 二、名单与词表（出自指导书，或通行规范的常见情形）═════════ */
  var BAD_STARS = "范冰冰 郑爽 刘晓庆 翟天临 仝卓 赵薇 张哲瀚 高晓松 吴亦凡 钱枫 霍尊 罗志祥 满文军 房祖名 宁财神 张默 高虎 李代沫 尹相杰 王学兵 张元 傅艺伟 宋冬野 陈羽凡 柯震东 王全安 黄海波 陈赫 李小璐 白百何 陈思诚 张丹峰 吴秀波 文章 陈翔 许志安 姚笛 陈冠希 黄秋生 何韵诗 周子瑜 卢广仲 陈宣裕 蔡依林 高云翔 蒋劲夫 董文华".split(" ");
  var INSULT = ["杜嘉班纳", "Dolce&Gabbana", "Dolce & Gabbana", "D&G", "H&M", "福田繁雄", "龙应台", "吕敬人"];
  var LEADERS = ["习近平", "毛泽东", "邓小平", "江泽民", "胡锦涛", "周恩来", "刘少奇", "朱德", "李强", "赵乐际", "王沪宁", "蔡奇", "丁薛祥", "李希", "李克强", "温家宝"];
  var COUNTRIES = "美国 日本 韩国 朝鲜 英国 法国 德国 意大利 西班牙 俄罗斯 印度 加拿大 澳大利亚 新加坡 马来西亚 泰国 越南 菲律宾 印度尼西亚 巴西 墨西哥 荷兰 瑞士 瑞典".split(" ");
  var OLD_LAWS = ["婚姻法", "继承法", "民法通则", "收养法", "担保法", "合同法", "物权法", "侵权责任法", "民法总则"];
  var ABBR_TERMS = [["电商", "电子商务"]];
  var SLANG = ["yyds", "YYDS", "绝绝子", "躺平", "打call", "打卡圣地", "集美", "小编", "干货满满", "宝藏", "种草", "拔草", "吃瓜", "凡尔赛", "破防", "C位", "神器", "爆款", "刷屏", "秒杀", "666", "给力", "高大上", "接地气", "颜值", "nice", "get到", "割韭菜", "躺赢", "内卷", "佛系", "社死", "emo", "整活"];
  var ORAL = ["咱们", "啥", "咋", "挺好", "蛮好", "搞定", "弄好", "一大堆", "超级", "贼", "老是", "反正", "这么着", "没啥", "差不离", "倍儿", "特别特别"];
  var VAGUE = ["大概", "大约", "可能", "也许", "差不多", "适量", "若干", "一些", "左右", "似乎", "好像"];
  var EN_EVERYDAY = "nice ok okay cool happy easy high low fashion style copy cute very so feel vibe level get out in fine good bad sorry thanks hello hi baby boss man lady party".split(" ");
  var TYPO = [["再接再励", "再接再厉"], ["迫不急待", "迫不及待"], ["一股作气", "一鼓作气"], ["甘败下风", "甘拜下风"], ["按装", "安装"], ["布署", "部署"], ["必竟", "毕竟"], ["既使", "即使"], ["凑和", "凑合"], ["松驰", "松弛"], ["默守成规", "墨守成规"], ["精萃", "精粹"], ["针贬", "针砭"], ["一愁莫展", "一筹莫展"], ["穿流不息", "川流不息"], ["金榜提名", "金榜题名"], ["谈笑风声", "谈笑风生"], ["气慨", "气概"], ["坐阵", "坐镇"], ["九宵", "九霄"], ["重迭", "重叠"], ["磨擦", "摩擦"], ["侯车", "候车"], ["竟赛", "竞赛"], ["发韧", "发轫"], ["脉博", "脉搏"], ["幅射", "辐射"], ["渲泄", "宣泄"], ["暴燥", "暴躁"], ["急燥", "急躁"], ["克苦", "刻苦"], ["家俱", "家具"], ["寒喧", "寒暄"], ["震憾", "震撼"], ["蜇伏", "蛰伏"], ["追朔", "追溯"], ["卑躬屈膝", null], ["相形见拙", "相形见绌"], ["记忆犹心", "记忆犹新"], ["美仑美奂", "美轮美奂"], ["变本加历", "变本加厉"], ["一如继往", "一如既往"], ["名列前矛", "名列前茅"], ["关健", "关键"], ["部份", "部分"], ["计划性", null]].filter(function (x) { return x[1]; });
  // 链接：可少量引用／禁止／须授权
  var URL_OK = /(\.gov\.cn|\.edu\.cn|\.ac\.cn|smartedu\.cn|moe\.gov|stats\.gov|samr\.gov|cnki\.net|people\.com\.cn|xinhuanet\.com|cctv\.com|chinamoocs|icourse163\.org)/i;
  var URL_BAN = /(baike\.baidu|baike\.com|baike\.sogou|wikipedia\.org|wiki\.|blog|bbs\.|tieba\.baidu|zhihu\.com|douban\.com|jianshu\.com|csdn\.net|mp\.weixin\.qq\.com|weixin\.qq\.com|toutiao\.com|sohu\.com|163\.com\/dy|sina\.com|weibo\.com|bilibili\.com|douyin\.com|kuaishou\.com|xiaohongshu\.com|360doc\.com)/i;
  var URL_RESTRICT = /(xuexi\.cn)/i;
  var EMBED_OK = /^(doc|docx|xls|xlsx|ppt|pptx|csv|tsv|dot|xlt|dotx|dotm|xlsm|xltm|xla|xlam|pages|wps|dps|et|wpt|ett|psd|eps|pdf|ofd|rtf|xmind|eml|tif|tiff|vsd|vsdx|glb|stp|step|ifc|dwg|dxf|dwf|dwfx|dwt|dcm)$/i;
  var AV = /^(mp4|m4v|mov|avi|wmv|flv|mkv|webm|mpg|mpeg|mp3|wav|m4a|aac|flac|swf)$/i;

  /* ═════════ 三、小工具 ═════════ */
  var CN = { 零: 0, 〇: 0, 一: 1, 二: 2, 两: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9, 十: 10, 百: 100 };
  function cnNum(s) {
    s = String(s || "").trim();
    if (/^\d+$/.test(s)) return +s;
    var n = 0, cur = 0;
    for (var i = 0; i < s.length; i++) {
      var v = CN[s[i]]; if (v == null) return NaN;
      if (v === 10 || v === 100) { n += (cur || 1) * v; cur = 0; } else cur = v;
    }
    return n + cur;
  }
  function nz(s) { return String(s || "").replace(/[\s　]+/g, ""); }
  function hanCount(s) { var m = String(s || "").match(/[㐀-鿿豈-﫿]/g); return m ? m.length : 0; }
  function charCount(s) { return String(s || "").replace(/\s+/g, "").length; }
  function clip(s, n) { s = String(s || "").replace(/\s+/g, " ").trim(); return s.length > n ? s.slice(0, n) + "…" : s; }
  function uniq(a) { var o = [], seen = {}; a.forEach(function (x) { if (!seen[x]) { seen[x] = 1; o.push(x); } }); return o; }
  function fmtWan(n) { return n >= 10000 ? (n / 10000).toFixed(n >= 100000 ? 1 : 2) + " 万字" : n + " 字"; }
  function mb(n) { return (n / 1048576).toFixed(1) + " MB"; }

  /* 稿件信息：从输入框里认「书名：」「主编：」「类型：」等；认不出的由正文推断，推断的标「推断」 */
  function parseInfo(q, text) {
    q = String(q || ""); text = String(text || "");
    var I = { raw: q.slice(0, 1200) };
    var m = /书\s*名\s*[:：]\s*《?([^》\n]{1,60})》?/.exec(q); if (m) I.title = m[1].trim();
    m = /(主\s*编|作\s*者|编\s*著|著\s*者)\s*[:：]\s*([^\n]{1,80})/.exec(q); if (m) I.editor = m[2].trim();
    m = /选\s*题\s*[:：]\s*([^\n]{1,80})/.exec(q); if (m) I.topic = m[1].trim();
    m = /(?:类\s*型|层\s*次|类\s*别)\s*[:：]\s*([^\n]{1,30})/.exec(q);
    var ty = m ? m[1] : q;
    if (/专著/.test(ty)) I.kind = "mono";
    else if (/职业|职教|高职|中职/.test(ty)) I.kind = "voc";
    else if (/理工/.test(ty)) I.kind = "sci";
    else if (/文管|文科|管理|文史/.test(ty)) I.kind = "art";
    else if (/本科/.test(ty)) I.kind = "ug";
    if (!I.kind) {
      var v = (text.match(/高职|中职|职业院校|职业教育|职业技能|职业本科/g) || []).length, u = (text.match(/本科|普通高等学校|高等院校/g) || []).length;
      if (v >= 3 && v >= u) { I.kind = "voc"; I.kindGuess = 1; } else if (u >= 3) { I.kind = "ug"; I.kindGuess = 1; }
    }
    I.digital = /数字教材|数字新稿|数字化教材|纸质转数字|新形态/.test(q + text.slice(0, 20000));
    m = /(?:每面|每页)\s*字数\s*[:：]?\s*(\d{3,5})/.exec(q); I.perPage = m ? +m[1] : 0;
    m = /(?:图片|图)\s*系数\s*[:：]?\s*(0?\.\d)/.exec(q); I.coef = m ? +m[1] : 0;
    m = /(?:查重|重复率|复制比)[^\d\n]{0,12}(\d{1,2}(?:\.\d+)?)\s*%/.exec(q); if (m) I.dup = +m[1];
    I.resList = [];
    var re = /([^\s，,；;：:\n]{1,80}\.(mp4|m4v|mov|avi|wmv|flv|mkv|mp3|wav|glb|stp|step|ifc|dwg|dxf|ppt|pptx|xls|xlsx|pdf|docx?|psd|xmind|vsdx?))\s*[，,（(：:\s]*\s*(\d+(?:\.\d+)?)\s*(GB|G|MB|M|KB|K)\b/gi, r;
    while ((r = re.exec(q))) {
      var n = +r[3], u2 = r[4].toUpperCase();
      var bytes = n * (u2[0] === "G" ? 1073741824 : u2[0] === "M" ? 1048576 : 1024);
      I.resList.push({ name: r[1], ext: r[2].toLowerCase(), size: bytes, typed: 1 });
    }
    return I;
  }
  var KIND_NAME = { voc: "职业教育教材", sci: "本科教材（理工）", art: "本科教材（文管）", ug: "本科教材（理工／文管未定）", mono: "专著" };
  var KIND_WORDS = { voc: 350000, sci: 500000, art: 450000, mono: 200000 };
  var KIND_CAP = { voc: 5 * 1073741824, sci: 8 * 1073741824, art: 8 * 1073741824, ug: 8 * 1073741824, mono: 0 };

  /* ═════════ 四、机检 ═════════
     输入 o = { text: 正文, meta: Word 结构（可无）, others: [{name,text,note}] 其他文字附件, res: [资源文件], info }
     输出 { rows: {ID: {res, note}}, finds: [{id, pos, src, issue, fix, lvl}], facts: {...}, detail: [md 段] } */
  var LVL_MUST = "必改", LVL_SUG = "建议", LVL_ASK = "需作者确认", LVL_HUM = "提请人工";
  function machine(o) {
    var text = String(o.text || ""), meta = o.meta || null, info = o.info || {}, others = o.others || [], res = (o.res || []).slice();
    (info.resList || []).forEach(function (r) { if (!res.some(function (x) { return x.name === r.name; })) res.push(r); });
    var rows = {}, finds = [], facts = {}, detail = [];
    function row(id, r, note) { rows[id] = { res: r, note: note || "" }; }
    function find(id, pos, src, issue, fix, lvl) { finds.push({ id: id, pos: pos || "", src: clip(src, 60), issue: issue, fix: fix || "", lvl: lvl || LVL_SUG, by: "机检" }); }
    var lines = text.split(/\n+/).map(function (x) { return x.trim(); }).filter(Boolean);
    function isHead(l) { return l.length <= 40 && !/[。；！？]$/.test(l); }

    /* —— 0. 标题、章与位置 —— */
    var H = []; // {i, kind, num, title, lvl}
    var RX = [
      ["篇", /^第\s*([一二三四五六七八九十百零〇两\d]+)\s*篇\s*(.*)$/],
      ["模块", /^模块\s*([一二三四五六七八九十百零〇两\d]+)\s*(.*)$/],
      ["单元", /^(?:第\s*)?([一二三四五六七八九十百零〇两\d]+)?\s*单元\s*([一二三四五六七八九十百零〇两\d]+)?\s*(.*)$/],
      ["章", /^第\s*([一二三四五六七八九十百零〇两\d]+)\s*章\s*(.*)$/],
      ["项目", /^项目\s*([一二三四五六七八九十百零〇两\d]+)\s*(.*)$/],
      ["节", /^第\s*([一二三四五六七八九十百零〇两\d]+)\s*节\s*(.*)$/],
      ["任务", /^任务\s*([一二三四五六七八九十百零〇两\d]+)\s*(.*)$/],
      ["一、", /^([一二三四五六七八九十]+)\s*[、]\s*(.*)$/],
      ["1.1", /^(\d+(?:\.\d+){1,3})\s+(\S.*)$/],
      ["1.", /^(\d+)\s*[.．](?!\d)\s*(.*)$/],
      ["（1）", /^[（(]\s*(\d+)\s*[)）]\s*(.*)$/],
      ["①", /^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*(.*)$/],
      ["a.", /^([a-h])\s*[.．]\s*(.*)$/]
    ];
    var inToc = false, tocLines = [], tocStart = -1, tocLead = 0, tocFirst = "";
    function tocKey(s) { return nz(s).replace(/[.．·…\-—_]{2,}.*$/, "").replace(/\d+$/, ""); }
    lines.forEach(function (l, i) {
      var k = nz(l);
      if (/^目录$|^目次$|^contents$/i.test(k) && tocStart < 0) { inToc = true; tocStart = i; return; }
      if (inToc) {
        var lead = /[.．·…]{3,}\s*\d+\s*$/.test(l);
        // 目录结束：又见到第一条目录的标题（正文开始了）；或目录大多带页码引线而这一行没有
        if (tocLines.length && (tocKey(l) === tocFirst || (tocLead >= 3 && !lead && tocLead >= tocLines.length * 0.6))) inToc = false;
      }
      if (inToc) {
        if (/[.．·…]{3,}\s*\d+\s*$/.test(l)) tocLead++;
        if (inToc && !tocLines.length) tocFirst = tocKey(l);
        if (/[.．·…]{3,}\s*\d+\s*$/.test(l) || (/^(第.{1,4}[篇章节]|模块|项目|任务|单元|[一二三四五六七八九十]+、|\d+(\.\d+)+|前言|参考文献|附录|内容提要)/.test(k) && l.length <= 50)) { tocLines.push(l); return; }
        if (tocLines.length > 3) inToc = false; else if (i - tocStart > 3) inToc = false;
      }
      if (l.length > 60) return;
      for (var j = 0; j < RX.length; j++) {
        var m = RX[j][1].exec(l);
        if (!m) continue;
        var kind = RX[j][0];
        if (kind === "单元") { if (!/单元/.test(l.slice(0, 8))) continue; m = [m[0], m[1] || m[2], m[3]]; if (!m[1]) continue; }
        if ((kind === "1." || kind === "（1）" || kind === "①" || kind === "a." || kind === "一、") && /[。；！？]$/.test(l) && l.length > 25) break;
        H.push({ i: i, kind: kind, raw: m[1], num: kind === "1.1" ? m[1] : cnNum(String(m[1]).replace(/[①-⑳]/, function (c) { return String(c.charCodeAt(0) - 0x245F); })), title: (m[2] || "").trim(), line: l, ar: /\d/.test(m[1]) });
        break;
      }
    });
    var has = {}; H.forEach(function (h) { has[h.kind] = (has[h.kind] || 0) + 1; });
    var form = "其他形式";
    if (has["篇"] && has["章"] && has["节"]) form = "篇章节式";
    else if (has["模块"] && has["项目"] && has["任务"]) form = "模块项目任务式";
    else if (has["章"] && has["节"]) form = "章节式";
    else if (has["项目"] && has["任务"]) form = "项目任务式";
    else if (has["章"]) form = "章式（无节）";
    else if (has["单元"]) form = "单元式";
    var TOP = has["章"] ? "章" : has["项目"] ? "项目" : has["单元"] ? "单元" : has["模块"] ? "模块" : "";
    var MID = has["节"] ? "节" : has["任务"] ? "任务" : "";
    facts.form = form;
    // 章（顶级单元）切分
    var chaps = [];
    var tops = H.filter(function (h) { return h.kind === TOP; });
    tops.forEach(function (h, j) {
      var end = j + 1 < tops.length ? tops[j + 1].i : lines.length;
      chaps.push({ name: h.line, num: h.num, i0: h.i, i1: end, body: lines.slice(h.i, end).join("\n") });
    });
    // 去掉目录里的重复：目录行也会被当成标题。正文章若在目录区内（i 很小且相邻很密），跳过
    if (tocStart >= 0 && tocLines.length) chaps = chaps.filter(function (c) { return c.i0 > tocStart + tocLines.length || c.body.length > 300; });
    // 最后一章止于参考文献、附录（书末辅文不算正文章）
    (function () {
      var back = -1;
      for (var bi = 0; bi < lines.length; bi++) { var bk = nz(lines[bi]); if (bk.length <= 20 && /^(参考文献|主要参考文献|参考书目|附录|后记|致谢)/.test(bk) && chaps.length && bi > chaps[chaps.length - 1].i0) { back = bi; break; } }
      if (back > 0) { var lc = chaps[chaps.length - 1]; lc.i1 = Math.min(lc.i1, back); lc.body = lines.slice(lc.i0, lc.i1).join("\n"); }
    })();
    facts.chapters = chaps.length;
    function chapOf(i) { for (var k = chaps.length - 1; k >= 0; k--) if (i >= chaps[k].i0) return chaps[k]; return null; }
    function posOf(i) { var c = chapOf(i); return (c ? clip(c.name, 18) : "前置部分") + "·第" + (i + 1) + "段"; }

    /* —— 1. 核心模块 —— */
    function headIdx(re) { for (var i = 0; i < lines.length; i++) { var k = nz(lines[i]); if (k.length <= 14 && re.test(k)) return i; } return -1; }
    var iTiyao = headIdx(/^(内容提要|内容简介|提要|本书简介)$/), iQian = headIdx(/^(前言|序言|序|自序|编写说明|出版说明|编者的话|写在前面的话|致读者|引言)$/), iMulu = tocStart >= 0 ? tocStart : headIdx(/^(目录|目次)$/);
    var iRef = headIdx(/^(参考文献|主要参考文献|参考书目|参考资料)$/), iApp = headIdx(/^附录/);
    row("S01", iTiyao >= 0 ? "符合" : "不符合", iTiyao >= 0 ? "已识别「" + lines[iTiyao] + "」" : "稿中未识别到「内容提要」；须补写（约300字）");
    if (iTiyao < 0) find("S01", "前置部分", "", "缺少内容提要", "按要求补写内容提要（主要内容、读者对象与适用专业、写作特点，约300字）", LVL_MUST);
    row("S02", iQian >= 0 ? "符合" : "不符合", iQian >= 0 ? "已识别「" + lines[iQian] + "」" : "稿中未识别到前言／序");
    if (iQian < 0) find("S02", "前置部分", "", "缺少前言", "补写前言（编写背景、特色、编写分工、致谢、自谦等）", LVL_MUST);
    row("S03", iMulu >= 0 ? "符合" : "不符合", iMulu >= 0 ? "已识别目录，" + tocLines.length + " 行" : "稿中未识别到目录；须单独提供目录");
    if (iMulu < 0) find("S03", "前置部分", "", "缺少目录", "提供目录（目录单独提供，便于快速了解稿件内容）", LVL_MUST);
    row("S04", chaps.length >= 1 ? "符合" : "需作者确认", chaps.length ? ("识别出" + TOP + " " + chaps.length + " 个，正文约 " + fmtWan(charCount(text)) ) : "未识别出章／项目级标题，正文结构须人工确认");
    row("S05", iRef >= 0 ? "符合" : "不符合", iRef >= 0 ? "已识别「" + lines[iRef] + "」" : "稿中未识别到参考文献");
    if (iRef < 0) find("S05", "书末", "", "缺少参考文献", "补列参考文献，按 GB/T 7714—2025 著录", LVL_MUST);

    /* —— 2. 栏目矩阵 —— */
    var COL = {
      g: { n: "引导性栏目", re: /^(学习目标|教学目标|知识目标|能力目标|技能目标|素养目标|素质目标|学习导航|案例引入|案例导入|引导案例|导入案例|情境导入|情景导入|任务导入|项目导入|任务描述|项目描述|知识导图|思维导图|知识框架|学习导图|课前预习|预习)/ },
      s: { n: "总结性栏目", re: /^(本章小结|本节小结|项目小结|任务小结|单元小结|模块小结|小结|本章总结|任务总结|项目总结|知识梳理|归纳总结|总结与反思|学习小结)/ },
      x: { n: "扩展性模块", re: /^(知识链接|拓展阅读|知识拓展|延伸阅读|拓展知识|知识延伸|知识窗|小贴士|拓展训练|拓展学习|阅读材料|视野拓展|行业前沿|知识卡片)/ },
      e: { n: "考核性栏目", re: /^(课后练习|思考与练习|习题|练习题|同步练习|巩固练习|任务实训|实训任务|技能训练|技能实训|课后作业|自测题|自我测试|任务评价|考核评价|项目评价|学习评价|思考题|复习思考题|能力训练|实践训练|实训|实践与训练)/ }
    };
    var headSet = {}; H.forEach(function (x) { headSet[x.i] = 1; });
    var mtx = chaps.map(function (c) {
      var r = { name: c.name, g: 0, s: 0, x: 0, e: 0, gPos: 1, sPos: 0, ePos: 0, kn: 0, ab: 0, li: 0, sz: 0, xLen: 0, colTxt: {}, len: c.body.length };
      var cl = lines.slice(c.i0, c.i1), L = cl.length || 1, acc = 0, inX = false, total = c.body.length || 1;
      cl.forEach(function (l, j) {
        var k = nz(l), short = l.length <= 40;
        if (short) {
          for (var key in COL) if (COL[key].re.test(k)) {
            r[key]++;
            var pos = acc / total;
            if (key === "g") r.gPos = Math.min(r.gPos, pos);
            if (key === "s") r.sPos = Math.max(r.sPos, pos);
            if (key === "e") r.ePos = Math.max(r.ePos, pos);
            var nx = cl.slice(j + 1, j + 4).join("").slice(0, 120);
            r.colTxt[k.slice(0, 6)] = nz(nx);
          }
        }
        var isCol = short && (COL.g.re.test(k) || COL.s.re.test(k) || COL.x.re.test(k) || COL.e.re.test(k)), isH = headSet[c.i0 + j];
        if (short && COL.x.re.test(k)) inX = true;
        else if (isCol || isH) inX = false;
        else if (inX) r.xLen += l.length;
        if (/知识目标/.test(k)) r.kn = 1;
        if (/能力目标|技能目标/.test(k)) r.ab = 1;
        if (/素养目标|素质目标|思政目标|育人目标/.test(k)) r.li = 1;
        if (/素养提升|课程思政|思政|大国工匠|工匠精神|家国情怀|职业素养|职业操守|职业道德|社会责任|责任担当|法治意识|科学精神|爱国|劳模|诚信/.test(k)) r.sz = 1;
        acc += l.length + 1;
      });
      return r;
    });
    facts.matrix = mtx;
    ["g", "s", "x", "e"].forEach(function (key, n) {
      var id = ["S06", "S07", "S08", "S09"][n];
      if (!mtx.length) { row(id, "未检", "未识别出章／项目，无法逐章核对"); return; }
      var hasN = mtx.filter(function (r) { return r[key] > 0; }).length;
      var miss = mtx.filter(function (r) { return !r[key]; }).map(function (r) { return clip(r.name, 16); });
      if (hasN === mtx.length) row(id, "符合", "各" + TOP + "均设" + COL[key].n);
      else if (hasN === 0) { row(id, key === "x" ? "需作者确认" : "不符合", "全书未见" + COL[key].n); find(id, "全书", "", "全书未设" + COL[key].n, "按全书统一的体例为各" + TOP + "补设" + COL[key].n, key === "x" ? LVL_ASK : LVL_MUST); }
      else { row(id, "不符合", "设置不统一：" + hasN + "/" + mtx.length + " 个" + TOP + "有；缺：" + miss.slice(0, 8).join("、") + (miss.length > 8 ? "等" : "")); find(id, miss.slice(0, 6).join("、"), "", COL[key].n + "各" + TOP + "设置不统一", "全书统一设置", LVL_MUST); }
    });
    // 附录、附件引用
    var refApp = [], refAtt = [];
    lines.forEach(function (l, i) {
      var m, re = /(?:见|参见|参考|详见)?\s*附录\s*([A-Z一二三四五六七八九十\d]?)/g;
      if (i === iApp) return;
      if (/附录/.test(l) && !(l.length <= 20 && /^附录/.test(nz(l)))) { while ((m = re.exec(l))) refApp.push({ i: i, k: m[1] || "", l: l }); }
      if (/(下载附件|见附件|附件\s*[\d一二三四五六七八九十]|附件「|附件“)/.test(l)) refAtt.push({ i: i, l: l });
    });
    var appHeads = lines.filter(function (l) { return l.length <= 40 && /^附录/.test(nz(l)); }).map(nz);
    var appProblems = [];
    refApp.forEach(function (r) { if (!appHeads.length) appProblems.push(r); else if (r.k && !appHeads.some(function (h) { return h.indexOf("附录" + r.k) === 0; })) appProblems.push(r); });
    var attOk = others.length > 0 || res.length > 0;
    if (!refApp.length && !refAtt.length) row("S10", appHeads.length ? "需作者确认" : "符合", appHeads.length ? "有附录 " + appHeads.length + " 项，但正文未见引用（如「见附录A」），请确认附录与正文的对应" : "正文未提及附录、附件");
    else if (appProblems.length || (refAtt.length && !attOk)) {
      row("S10", "不符合", (appProblems.length ? "正文提及附录而稿中找不到对应附录 " + appProblems.length + " 处；" : "") + (refAtt.length && !attOk ? "正文提及附件 " + refAtt.length + " 处，未随稿提供附件" : ""));
      appProblems.slice(0, 10).forEach(function (r) { find("S10", posOf(r.i), r.l, "正文提及附录" + r.k + "，稿中无对应附录", "补齐附录或改正引用", LVL_MUST); });
      if (refAtt.length && !attOk) find("S10", posOf(refAtt[0].i), refAtt[0].l, "正文提及附件，未随稿提供", "请随稿提供附件文件，并与正文提及处一一对应", LVL_ASK);
    } else row("S10", "符合", "正文提及附录 " + refApp.length + " 处、附件 " + refAtt.length + " 处，均能找到对应");
    // 实训任务单／知识框架图
    var hasTaskSheet = /实训任务单|任务单|工单|任务工单|实训工单|实训报告单/.test(text), hasFrame = /知识框架|思维导图|知识导图|知识结构图|知识图谱|内容框架/.test(text);
    row("S13", hasTaskSheet || hasFrame ? "符合" : "需作者确认", "实训任务单：" + (hasTaskSheet ? "有" : "未见") + "；知识框架图：" + (hasFrame ? "有" : "未见") + "（实操类建议含任务单，理论类建议含框架图）");
    // S11 链路（代码先给证据，审读补判）
    var chain = mtx.length ? ("预习（引导性栏目）" + mtx.filter(function (r) { return r.g; }).length + "/" + mtx.length + "；练习（考核性）" + mtx.filter(function (r) { return r.e; }).length + "/" + mtx.length + "；拓展（扩展性）" + mtx.filter(function (r) { return r.x; }).length + "/" + mtx.length) : "未识别出章";
    facts.chain = chain;
    row("S11", mtx.length && mtx.every(function (r) { return r.g && r.e; }) ? "需作者确认" : "不符合", "栏目链路——" + chain + "（预习与练习环节缺失的" + (TOP || "章") + "即为链路断层）");

    /* —— 3. 层级与编号 —— */
    var probs = [];
    function seqCheck(list, label) {
      var prev = 0;
      list.forEach(function (h) {
        if (isNaN(h.num)) return;
        if (h.num === prev) probs.push({ i: h.i, l: h.line, why: label + "重号" });
        else if (prev && h.num !== prev + 1) probs.push({ i: h.i, l: h.line, why: label + "跳号（" + prev + "→" + h.num + "）" });
        else if (!prev && h.num !== 1) probs.push({ i: h.i, l: h.line, why: label + "不从1起" });
        prev = h.num;
      });
    }
    if (TOP) seqCheck(H.filter(function (h) { return h.kind === TOP && h.i > (tocStart >= 0 ? tocStart + tocLines.length : -1); }), TOP);
    chaps.forEach(function (c) {
      if (MID) seqCheck(H.filter(function (h) { return h.kind === MID && h.i > c.i0 && h.i < c.i1; }), MID);
    });
    // 同级编号样式：章名阿拉伯与汉字混用；知识点级「一、」与「1.1」混用
    var topAr = H.filter(function (h) { return h.kind === TOP; }), mixTop = topAr.some(function (h) { return h.ar; }) && topAr.some(function (h) { return !h.ar; });
    if (mixTop) probs.push({ i: topAr[0].i, l: topAr[0].line, why: TOP + "序号汉字与阿拉伯数字混用" });
    var kpStyle = {};
    chaps.forEach(function (c) {
      var a = H.filter(function (h) { return h.i > c.i0 && h.i < c.i1; });
      var cnN = a.filter(function (h) { return h.kind === "一、"; }).length, decN = a.filter(function (h) { return h.kind === "1.1"; }).length;
      kpStyle[c.name] = cnN && decN ? "混" : cnN ? "一、" : decN ? "1.1" : "";
    });
    var stys = uniq(Object.keys(kpStyle).map(function (k) { return kpStyle[k]; }).filter(Boolean));
    if (stys.length > 1) probs.push({ i: 0, l: "", why: "知识点级标题编号样式不统一（各" + TOP + "分别用了：" + stys.join("／") + "）" });
    row("T01", form !== "其他形式" ? "符合" : "需作者确认", "识别为「" + form + "」：" + Object.keys(has).filter(function (k) { return has[k] && !/^(1\.|（1）|①|a\.)$/.test(k); }).map(function (k) { return k + " " + has[k]; }).join("、"));
    if (probs.length) {
      row("T02", "不符合", "发现 " + probs.length + " 处：" + probs.slice(0, 4).map(function (p) { return p.why; }).join("；") + (probs.length > 4 ? "……" : ""));
      probs.slice(0, 30).forEach(function (p) { find("T02", p.i ? posOf(p.i) : "全书", p.l, p.why, "统一编号样式并按顺序重编", LVL_MUST); });
    } else row("T02", H.length ? "符合" : "未检", H.length ? "同级编号连续、样式一致" : "未识别出编号标题");
    // 上下两级同名
    var same = [];
    for (var hi = 0; hi + 1 < H.length; hi++) {
      var a1 = H[hi], b1 = H[hi + 1];
      if (b1.i === a1.i + 1 && a1.kind !== b1.kind && a1.title && nz(a1.title) === nz(b1.title)) same.push(b1);
    }
    row("T03", same.length ? "不符合" : (H.length ? "符合" : "未检"), same.length ? same.length + " 处上下两级标题相同，如「" + clip(same[0].title, 20) + "」" : "未发现上下两级同名");
    same.slice(0, 10).forEach(function (h) { find("T03", posOf(h.i), h.line, "上下两级标题相同", "改写下一级标题或删去重复层级", LVL_MUST); });
    // （1）级接排
    var notRun = H.filter(function (h) { return (h.kind === "（1）" || h.kind === "①" || h.kind === "a.") && h.line.length <= 25 && !/[。：:；]/.test(h.line) && lines[h.i + 1] && !/^[（(]?\d|^[①-⑳]/.test(lines[h.i + 1]); });
    row("T04", notRun.length > 3 ? "不符合" : notRun.length ? "需作者确认" : "符合", notRun.length ? notRun.length + " 处（1）级以下标题单独成行、未接排正文，如「" + clip(notRun[0].line, 20) + "」；加粗与否须在带格式的稿件上看" : "未见单独成行的（1）级以下标题（是否加粗须在带格式稿件上看）");
    notRun.slice(0, 10).forEach(function (h) { find("T04", posOf(h.i), h.line, "（1）级以下标题未接排", "标题后接排正文：「（1）标题。正文……」，不加粗", LVL_SUG); });
    // 目录与正文
    if (tocLines.length) {
      var bodyHeads = {}; H.forEach(function (h) { if (h.i > tocStart + tocLines.length) bodyHeads[nz(h.line).replace(/[.．·…]+\d*$/, "")] = 1; });
      var heads2 = lines.slice(tocStart + tocLines.length).filter(isHead).map(nz);
      var miss = tocLines.map(function (l) { return nz(l).replace(/[.．·…\-—]{2,}.*$/, "").replace(/\d+$/, ""); }).filter(function (k) { return k && !bodyHeads[k] && heads2.indexOf(k) < 0 && !/^(前言|内容提要|参考文献|附录|目录)/.test(k); });
      var tocTop = tocLines.filter(function (l) { return new RegExp("^(第.{1,4}" + (TOP === "章" ? "章" : TOP === "项目" ? "" : "") + "|" + (TOP || "章") + ")").test(nz(l)); }).length;
      row("K04", miss.length ? "不符合" : "符合", "目录 " + tocLines.length + " 行" + (miss.length ? "；" + miss.length + " 条在正文中找不到同名标题，如「" + clip(miss[0], 20) + "」（默认以正文为准，需与作者确认）" : "，与正文标题一致") + (same.length ? "；另有上下两级同名 " + same.length + " 处" : ""));
      miss.slice(0, 15).forEach(function (k) { find("K04", "目录", k, "目录标题与正文不一致", "核对目录与正文标题，默认以正文为准", LVL_MUST); });
      facts.tocTop = tocTop;
    } else row("K04", iMulu >= 0 ? "需作者确认" : "不符合", iMulu >= 0 ? "有目录标题但未能逐行识别目录条目，请人工核对" : "无目录");

    /* —— 4. 图表编号 —— */
    function capScan(ch) {
      var caps = [], refs = [];
      var reCap = new RegExp("^" + ch + "\\s*(\\d+(?:\\s*[-－—–.．]\\s*\\d+){1,2})\\s*(.*)$");
      var reRef = new RegExp(ch + "\\s*(\\d+(?:\\s*[-－—–.．]\\s*\\d+){1,2})", "g");
      lines.forEach(function (l, i) {
        var m = reCap.exec(l);
        if (m && l.length <= 60 && !/[。，；]/.test(m[2].slice(0, 30))) { caps.push({ i: i, n: m[1].replace(/\s/g, "").replace(/[－—–.．]/g, "-"), name: m[2].trim(), l: l }); return; }
        var r; reRef.lastIndex = 0;
        while ((r = reRef.exec(l))) refs.push({ i: i, n: r[1].replace(/\s/g, "").replace(/[－—–.．]/g, "-") });
      });
      return { caps: caps, refs: refs };
    }
    var FIG = capScan("图"), TAB = capScan("表");
    facts.figCaps = FIG.caps.length; facts.tabCaps = TAB.caps.length;
    function numCheck(S, ch, idSeq, idRef) {
      var segs = uniq(S.caps.map(function (c) { return c.n.split("-").length; }));
      var bad = [];
      if (segs.length > 1) bad.push({ i: S.caps[0].i, l: S.caps[0].l, why: ch + "号编序方式不统一（按章与按篇-章混用）" });
      var by = {}, seen = {};
      S.caps.forEach(function (c) {
        var p = c.n.split("-"), last = +p.pop(), pre = p.join("-");
        if (seen[c.n]) bad.push({ i: c.i, l: c.l, why: ch + c.n + " 重号" }); seen[c.n] = 1;
        (by[pre] = by[pre] || []).push({ last: last, c: c });
        var cp = chapOf(c.i);
        if (cp && segs.length === 1 && segs[0] === 2 && !isNaN(cp.num) && +p[0] !== cp.num) bad.push({ i: c.i, l: c.l, why: ch + c.n + " 与所在" + TOP + "序号（" + cp.num + "）不符" });
      });
      Object.keys(by).forEach(function (pre) {
        var a = by[pre], prev = 0;
        a.forEach(function (x) {
          if (x.last !== prev + 1 && x.last !== prev) bad.push({ i: x.c.i, l: x.c.l, why: ch + x.c.n + " 跳号或顺序错乱（前一个是 " + ch + (pre ? pre + "-" : "") + prev + "）" });
          prev = x.last;
        });
      });
      if (!S.caps.length) row(idSeq, "未检", "稿中未识别到" + ch + "题（" + ch + "X-X）");
      else if (bad.length) { row(idSeq, "不符合", bad.length + " 处：" + bad.slice(0, 3).map(function (b) { return b.why; }).join("；") + (bad.length > 3 ? "……" : "")); bad.slice(0, 30).forEach(function (b) { find(idSeq, posOf(b.i), b.l, b.why, "按「唯一、连续」原则重编" + ch + "号，并同步修改正文引用", LVL_MUST); }); }
      else row(idSeq, "符合", ch + "题 " + S.caps.length + " 个，编号唯一、连续，编序方式统一（" + (segs[0] === 3 ? "按篇-章" : "按章") + "）");
      var refSet = {}; S.refs.forEach(function (r) { refSet[r.n] = 1; });
      var capSet = {}; S.caps.forEach(function (c) { capSet[c.n] = 1; });
      var noRef = S.caps.filter(function (c) { return !refSet[c.n]; }), ghost = uniq(S.refs.filter(function (r) { return !capSet[r.n]; }).map(function (r) { return r.n; }));
      var noName = S.caps.filter(function (c) { return !c.name; }).length;
      if (!S.caps.length && !S.refs.length) row(idRef, "未检", "稿中未见" + ch + "号与" + ch + "的正文引用");
      else if (noRef.length || ghost.length) {
        row(idRef, "不符合", (noRef.length ? noRef.length + " 个" + ch + "号无正文引用（如" + ch + noRef[0].n + "）" : "") + (ghost.length ? (noRef.length ? "；" : "") + "正文引用了不存在的" + ch + "号 " + ghost.length + " 个（如" + ch + ghost[0] + "）" : "") + (noName ? "；无" + ch + "名 " + noName + " 个（可不加" + ch + "名）" : ""));
        noRef.slice(0, 25).forEach(function (c) { find(idRef, posOf(c.i), c.l, ch + c.n + " 无正文引用", "在正文相应位置补「如" + ch + c.n + "所示」，" + ch + "与文相互印证", LVL_MUST); });
        ghost.slice(0, 15).forEach(function (n) { find(idRef, "正文", ch + n, "引用的" + ch + n + " 不存在", "核对" + ch + "号，改正引用或补" + ch, LVL_MUST); });
      } else row(idRef, "符合", ch + "号均有正文引用" + (noName ? "（无" + ch + "名 " + noName + " 个，可不加" + ch + "名）" : ""));
    }
    numCheck(FIG, "图", "T05", "T07");
    var t05 = rows.T05;
    numCheck(TAB, "表", "T06", "T08");
    // T05 是图的编号规则、T06 是表的唯一连续——再合成：T05 规则统一（图＋表），T06 唯一连续（图＋表）
    (function () {
      var figRule = t05, tabSeq = rows.T06;
      var bothSegs = uniq(FIG.caps.concat(TAB.caps).map(function (c) { return c.n.split("-").length; }));
      var ruleBad = bothSegs.length > 1;
      rows.T05 = { res: (!FIG.caps.length && !TAB.caps.length) ? "未检" : ruleBad ? "不符合" : "符合", note: (!FIG.caps.length && !TAB.caps.length) ? "未识别到图题、表题" : ruleBad ? "图、表编序方式不统一（按章与按篇-章混用）" : "图、表统一" + (bothSegs[0] === 3 ? "按篇-章" : "按章") + "编序" };
      var fSeqBad = figRule.res === "不符合", tSeqBad = tabSeq.res === "不符合";
      rows.T06 = { res: (fSeqBad || tSeqBad) ? "不符合" : (FIG.caps.length || TAB.caps.length) ? "符合" : "未检", note: "图：" + figRule.note + "；表：" + tabSeq.note };
      finds.forEach(function (f) { if (f.id === "T05" && /跳号|重号|顺序|不符/.test(f.issue)) f.id = "T06"; });
    })();
    // 无号图片、表格是否为真表格、表题混排
    if (meta) {
      var imgN = meta.drawings || 0;
      facts.images = imgN;
      if (imgN > FIG.caps.length + 2) { row("T09", "不符合", "稿中图片 " + imgN + " 幅，图题只有 " + FIG.caps.length + " 个：约 " + (imgN - FIG.caps.length) + " 幅图无图号（装饰性图片除外），须补图号与正文引用，全稿统一"); find("T09", "全书", "", "约 " + (imgN - FIG.caps.length) + " 幅图片无图号", "知识性图片补图号和正文引用（可不加图名），全稿统一", LVL_MUST); }
      else row("T09", "符合", "图片 " + imgN + " 幅，图题 " + FIG.caps.length + " 个，数量相当");
      var tN = meta.tables || 0;
      if (TAB.caps.length > tN) { row("F08", "不符合", "表题 " + TAB.caps.length + " 个，Word 表格只有 " + tN + " 个：约 " + (TAB.caps.length - tN) + " 个表格疑为图片，不可复制"); find("F08", "全书", "", "约 " + (TAB.caps.length - tN) + " 个表格疑为图片", "改为可编辑的 Word 表格", LVL_MUST); }
      else row("F08", tN ? "符合" : "未检", tN ? "Word 表格 " + tN + " 个，均可复制" : "稿中没有表格");
      var mixed = (meta.tblCaps || []).filter(function (c) { return /^图\s*\d/.test(c.before || "") || /^图\s*\d/.test(c.after || ""); });
      row("F09", mixed.length ? "不符合" : (tN ? "符合" : "未检"), mixed.length ? mixed.length + " 个表格用了图号作题（如「" + clip(mixed[0].before || mixed[0].after, 16) + "」）" : (tN ? "表格均用表序号" : "稿中没有表格"));
      mixed.slice(0, 10).forEach(function (c) { find("F09", "表格处", c.before || c.after, "表格用图号作题，表序号与图序号混排", "表格改用表序号并重编", LVL_MUST); });
    } else {
      row("T09", "未检", "需 .docx 原稿才能数图片（当前为纯文本／PDF／老式 .doc）");
      row("F08", "未检", "需 .docx 原稿才能判断表格是否为图片");
      row("F09", TAB.caps.length && FIG.caps.length ? "需作者确认" : "未检", "需 .docx 原稿才能判断表格题注；请确认表格均用表序号");
    }

    /* —— 5. 内容占比 —— */
    var xLen = mtx.reduce(function (a, r) { return a + r.xLen; }, 0), tot = charCount(text) || 1, ratio = xLen / tot;
    facts.extRatio = ratio;
    row("T11", ratio >= 0.4 ? "不符合" : "符合", "扩展性栏目约 " + fmtWan(xLen) + "，占正文 " + (ratio * 100).toFixed(1) + "%（粗略统计，以栏目标题到下一标题为界）；核心知识约 " + ((1 - ratio) * 100).toFixed(1) + "%");
    if (ratio >= 0.4) find("T11", "全书", "", "拓展知识占比 " + (ratio * 100).toFixed(0) + "%，超过40%", "压缩拓展阅读、知识延伸，核心内容详细展开", LVL_MUST);

    /* —— 6. 政治性：只标位置，提请人工 —— */
    var sents = [];
    lines.forEach(function (l, i) { (l.match(/[^。！？；]+[。！？；]?/g) || []).forEach(function (s) { if (s.trim()) sents.push({ i: i, s: s.trim() }); }); });
    var hk = [];
    sents.forEach(function (x) {
      var s = x.s;
      if (/台湾国|台湾政府|台湾总统|台湾行政院|台湾立法院|中华民国(?!时期|政府时期|\d|年间|成立|建立)|中台(?!风|山)|中港台|港澳台国家|台湾等国|香港等国|澳门等国|香港国家|澳门国家|台湾国家/.test(s)) hk.push(x);
      else if (/(台湾|香港|澳门)/.test(s) && (/(其他)?国家/.test(s) || COUNTRIES.filter(function (c) { return s.indexOf(c) >= 0; }).length >= 2)) hk.push(x);
      else if (/中国(?:和|与|、)(台湾|香港|澳门)|(台湾|香港|澳门)(?:和|与|、)中国(?!内地|大陆)/.test(s)) hk.push(x);
    });
    if (hk.length) { row("P01", "提请人工", hk.length + " 处涉港澳台表述需逐条核查，如：" + clip(hk[0].s, 40)); hk.slice(0, 20).forEach(function (x) { find("P01", posOf(x.i), x.s, "涉港澳台表述，疑似将港澳台列为国家或与中国并列", "核实并改为规范表述（如「中国台湾地区」「国家和地区」）", LVL_HUM); }); }
    else row("P01", "符合", "机检未发现港澳台与国家并列等表述（审读另核）");
    var terr = sents.filter(function (x) { return /南海|钓鱼岛|藏南|阿克赛钦|黄岩岛|南沙|西沙|九段线|十段线|边界|国界|领土|国旗|国徽|国歌|联合国|欧盟|北约|世界贸易组织|WTO/.test(x.s); });
    if (terr.length) { row("P03", "提请人工", "涉及领土、国家象征或国际组织的表述 " + terr.length + " 处，须逐条核对，如：" + clip(terr[0].s, 40)); terr.slice(0, 15).forEach(function (x) { find("P03", posOf(x.i), x.s, "涉及国家主权、国家象征或国际组织的表述", "核对表述是否维护领土完整、尊重国家象征、区分国际组织性质", LVL_HUM); }); }
    else row("P03", "符合", "机检未见涉领土、国家象征、国际组织的表述（外国地名由审读另核）");
    var ld = sents.filter(function (x) { return LEADERS.some(function (n) { return x.s.indexOf(n) >= 0; }); });
    if (ld.length) { row("P06", "提请人工", "提及党和国家领导人 " + ld.length + " 处：姓名、职务须准确，直接引语须对照权威原文一字不差；用照片须履行备案", ""); ld.slice(0, 20).forEach(function (x) { find("P06", posOf(x.i), x.s, "涉及党和国家领导人或其讲话", "对照权威原文核对引语、姓名、职务；如配照片须备案", LVL_HUM); }); }
    else row("P06", "符合", "未提及党和国家重要领导人");
    var sec = sents.filter(function (x) { return /内部资料|内部文件|秘密|机密|绝密|不得外传|涉密|保密数据|未公开数据/.test(x.s); });
    row("P09", sec.length ? "提请人工" : "符合", sec.length ? sec.length + " 处出现「内部资料」「保密」等字样，须确认无涉密内容" : "机检未见涉密字样");
    sec.slice(0, 10).forEach(function (x) { find("P09", posOf(x.i), x.s, "疑似涉密或内部资料", "确认可公开，或删去", LVL_HUM); });
    var maps = sents.filter(function (x) { return /地图|审图号|疆域|版图|行政区划图|示意图.*(国|省)/.test(x.s); });
    row("P10", maps.length ? "提请人工" : (meta && meta.drawings ? "提请人工" : "符合"), maps.length ? "提及地图 " + maps.length + " 处：涉及国界线的地图须送审（有审图号的简单地图除外），古代近代标准统一" : (meta && meta.drawings ? "文字未提及地图；稿中有图片 " + meta.drawings + " 幅，须人工过目是否含地图" : "未提及地图，稿中无图片"));
    maps.slice(0, 10).forEach(function (x) { find("P10", posOf(x.i), x.s, "涉及地图", "核查国界线并取得审图号", LVL_HUM); });
    var ins = sents.filter(function (x) { return INSULT.some(function (n) { return x.s.indexOf(n) >= 0; }); });
    row("P11", ins.length ? "不符合" : "需作者确认", ins.length ? "命中指导书所列辱华品牌／艺术家 " + ins.length + " 处" : "文字未命中指导书名单；图片中的品牌、作品须人工过目");
    ins.slice(0, 10).forEach(function (x) { find("P11", posOf(x.i), x.s, "命中指导书所列辱华品牌或言论艺术家", "删去或替换", LVL_MUST); });
    var stars = [];
    sents.forEach(function (x) { BAD_STARS.forEach(function (n) { if (n.length >= 2 && x.s.indexOf(n) >= 0 && !(n === "文章" && !/演员|艺人|明星/.test(x.s))) stars.push({ i: x.i, s: x.s, n: n }); }); });
    row("P12", stars.length ? "不符合" : "符合", stars.length ? "命中指导书所列劣迹艺人 " + uniq(stars.map(function (x) { return x.n; })).join("、") : "文字未命中劣迹艺人名单（图片、视频须人工过目）");
    stars.slice(0, 10).forEach(function (x) { find("P12", posOf(x.i), x.s, "出现劣迹艺人「" + x.n + "」", "删去或替换", LVL_MUST); });
    var img = meta ? (meta.drawings || 0) : null;
    row("P13", "提请人工", img ? "稿中图片 " + img + " 幅，须人工逐幅过目（裸体、服装暴露、性暗示）" : img === 0 ? "稿中无图片" : "需人工过目图片");
    if (img === 0) rows.P13.res = "符合";
    row("P14", img === 0 ? "符合" : "提请人工", img === 0 ? "稿中无图片" : "须人工过目图片中是否有国内外领导人");
    var vids = res.filter(function (r) { return AV.test(r.ext || ""); });
    row("P15", vids.length ? "提请人工" : "未检", vids.length ? "随稿音视频 " + vids.length + " 个，须快速浏览画面、检听敏感片段" : "未随稿提供音视频");

    /* —— 7. 版权 —— */
    var dupTxt = "";
    others.forEach(function (d) { var m = /(?:总文字复制比|文字复制比|复制比|重复率|相似度|总相似比)[^\d]{0,20}(\d{1,2}(?:\.\d+)?)\s*%/.exec(d.text || ""); if (m && !dupTxt) { dupTxt = d.name; info.dup = info.dup != null ? info.dup : +m[1]; } });
    if (info.dup != null) { row("C01", info.dup < 30 ? "符合" : "不符合", "查重重复率 " + info.dup + "%" + (dupTxt ? "（读自《" + dupTxt + "》）" : "（输入框填写）") + "，要求 <30%"); if (info.dup >= 30) find("C01", "全书", "", "重复率 " + info.dup + "%，超过30%", "作者降重后返稿，并附降重后的查重报告", LVL_MUST); }
    else { row("C01", "需作者确认", "未随稿提供查重报告：外部稿件由出版社提供一次免费查重；自组稿件交稿时须附查重报告（重复率<30%，原创比例计算不含行业标准、通用公式等公共知识）"); find("C01", "全书", "", "未提供查重报告", "提供查重报告（重复率须<30%）", LVL_ASK); }
    row("C02", "提请人工", "以查重报告为准；初审中发现与其他教材雷同的段落另行标出");
    var coop = sents.filter(function (x) { return /校企合作|合作企业|企业提供|企业资料|企业技术资料|由.{1,12}(公司|集团|企业)提供|某(公司|企业|集团)/.test(x.s); });
    row("C03", coop.length ? "需作者确认" : "符合", coop.length ? coop.length + " 处使用校企合作案例或企业资料，须提供企业授权" : "未见校企合作案例、企业技术资料");
    coop.slice(0, 10).forEach(function (x) { find("C03", posOf(x.i), x.s, "校企合作案例或企业资料", "提供合作企业的书面授权", LVL_ASK); });
    // 标准
    var STD = /((?:GB|GB\/T|GB\/Z|GBZ|JB|JB\/T|JGJ|JGJ\/T|CJJ|DL\/T|NB\/T|QB|QB\/T|SJ|SJ\/T|SB\/T|HG|HG\/T|HJ|YY|YY\/T|AQ|WS|WS\/T|JT\/T|TB|TB\/T|MH|MZ\/T|SL|GA|GA\/T|ISO|IEC|DB\d{0,2}(?:\/T)?)\s*\d+(?:\.\d+)?(?:\s*[—–\-－]\s*(\d{4}))?)/g;
    var stds = {}, m7;
    lines.forEach(function (l, i) { STD.lastIndex = 0; while ((m7 = STD.exec(l))) { var k = m7[1].replace(/\s+/g, " "); if (!stds[k]) stds[k] = { k: k, y: m7[2] ? +m7[2] : 0, i: i, l: l }; } });
    var stdList = Object.keys(stds).map(function (k) { return stds[k]; });
    facts.standards = stdList;
    var nowY = new Date().getFullYear();
    var oldStd = stdList.filter(function (s) { return s.y && s.y <= nowY - 12; }), noYear = stdList.filter(function (s) { return !s.y && !/^ISO|^IEC/.test(s.k); });
    if (stdList.length) {
      row("K09", "需作者确认", "引用标准 " + stdList.length + " 项，须逐项到工标网（csres.com）核对现行状态：已废止的必须更新，已明确废止日期的强烈要求更新" + (oldStd.length ? "；其中 " + oldStd.length + " 项发布年份在 " + (nowY - 12) + " 年以前，高度疑似已被代替" : "") + (noYear.length ? "；" + noYear.length + " 项未写年号" : ""));
      oldStd.slice(0, 20).forEach(function (s) { find("K09", posOf(s.i), s.k, "标准年号较早（" + s.y + "），疑已废止或被代替", "到工标网核对，换为现行版本", LVL_ASK); });
      noYear.slice(0, 10).forEach(function (s) { find("K09", posOf(s.i), s.k, "标准未写年号", "补写年号（如 GB/T 7714—2025）", LVL_SUG); });
      var cpr = stdList.length ? sents.filter(function (x) { return /标准|手册/.test(x.s) && /版权|出版|发布单位|归口|起草/.test(x.s); }).length : 0;
      row("C04", cpr ? "符合" : "需作者确认", "引用标准、技术手册 " + stdList.length + " 项；" + (cpr ? "部分已标注发布或版权方" : "未见标注版权方（发布机构），请在引用处或参考文献中注明"));
    } else { row("K09", "符合", "未引用国家／行业标准"); row("C04", "符合", "未引用行业标准、技术手册"); }
    // 法律
    var laws = [];
    sents.forEach(function (x) { OLD_LAWS.forEach(function (n) { var re = new RegExp("《(?:中华人民共和国)?" + n + "》"); if (re.test(x.s) && !/废止|原《|已失效|此前|曾/.test(x.s)) laws.push({ i: x.i, s: x.s, n: n }); }); });
    row("K10", laws.length ? "不符合" : "符合", laws.length ? "引用已废止法律 " + uniq(laws.map(function (x) { return "《" + x.n + "》"; })).join("、") + "（《民法典》2021年1月1日起施行，上述法律同时废止）" : "机检未见已废止的法律（其他法规现行状态审读另核）");
    laws.slice(0, 15).forEach(function (x) { find("K10", posOf(x.i), x.s, "引用已废止的《" + x.n + "》", "改为《中华人民共和国民法典》相应编、条", LVL_MUST); });
    // 链接
    var urls = [];
    lines.forEach(function (l, i) { var re = /https?:\/\/[^\s<>"'，。）)】]+|www\.[^\s<>"'，。）)】]+/g, m; while ((m = re.exec(l))) urls.push({ u: m[0], i: i }); });
    (meta && meta.links || []).forEach(function (u) { if (!urls.some(function (x) { return x.u === u; })) urls.push({ u: u, i: -1 }); });
    var ban = urls.filter(function (x) { return URL_BAN.test(x.u); }), rst = urls.filter(function (x) { return URL_RESTRICT.test(x.u); }), okU = urls.filter(function (x) { return URL_OK.test(x.u); }), other = urls.filter(function (x) { return !URL_BAN.test(x.u) && !URL_RESTRICT.test(x.u) && !URL_OK.test(x.u); });
    facts.urls = { all: urls.length, ok: okU.length, ban: ban.length, rst: rst.length, other: other.length };
    if (!urls.length) { row("C08", "符合", "稿中没有超链接"); row("C09", "符合", "稿中没有超链接"); }
    else {
      row("C08", ban.length ? "不符合" : other.length ? "需作者确认" : "符合", "超链接 " + urls.length + " 个：官方／权威 " + okU.length + "；禁止类（百科、博客、论坛、公众号、商业资讯等）" + ban.length + "；其他 " + other.length + " 个须确认是否官方、稳定");
      ban.slice(0, 20).forEach(function (x) { find("C08", x.i >= 0 ? posOf(x.i) : "超链接", x.u, "禁止引用的链接类型", "删去，或换为政府、事业单位、权威平台的链接", LVL_MUST); });
      other.slice(0, 15).forEach(function (x) { find("C08", x.i >= 0 ? posOf(x.i) : "超链接", x.u, "链接来源待确认", "确认为官方、稳定且未标注禁止转载", LVL_ASK); });
      row("C09", rst.length ? "不符合" : (okU.length ? "需作者确认" : "符合"), rst.length ? "引用学习强国等标注限制转载的平台 " + rst.length + " 处，未获授权不得引用" : (okU.length ? "官方链接 " + okU.length + " 个，须确认页面无「禁止转载」标注" : "未见限制转载类链接"));
      rst.slice(0, 10).forEach(function (x) { find("C09", x.i >= 0 ? posOf(x.i) : "超链接", x.u, "标注限制转载的平台", "取得授权或删去", LVL_MUST); });
    }
    row("C06", meta && meta.drawings === 0 ? "符合" : "提请人工", meta && meta.drawings === 0 ? "稿中无图片" : "须人工核查摄影作品、设计作品、人物相片的来源与授权（公共版权／已授权／合理引用）");
    row("C07", vids.length ? "需作者确认" : "未检", vids.length ? "音视频 " + vids.length + " 个，须与作者确认版权（片头院校、书名信息可作初步判断）" : "未随稿提供音视频");
    if (vids.length) find("C07", "资源", vids.map(function (v) { return v.name; }).slice(0, 3).join("、"), "音视频版权待确认", "作者出具版权说明或授权", LVL_ASK);

    /* —— 8. 栏目位置、三维目标、照抄 —— */
    if (mtx.length) {
      var badPos = mtx.filter(function (r) { return (r.g && r.gPos > 0.25) || (r.s && r.sPos < 0.6) || (r.e && r.ePos < 0.6); });
      row("L01", badPos.length ? "不符合" : "符合", badPos.length ? badPos.length + " 个" + TOP + "栏目位置不当（引导性栏目不在开头、小结或练习不在结尾），如「" + clip(badPos[0].name, 16) + "」" : "引导性栏目在章首、总结与考核栏目在章末");
      badPos.slice(0, 10).forEach(function (r) { find("L01", clip(r.name, 18), "", "栏目位置不当", "「学习目标」前置到章首，「本章小结」「课后练习」后置到章末", LVL_SUG); });
      var full = mtx.filter(function (r) { return r.kn && r.ab && r.li; }).length, part = mtx.filter(function (r) { return (r.kn || r.ab || r.li) && !(r.kn && r.ab && r.li); });
      row("L04", full === mtx.length ? "符合" : "不符合", "三维目标齐全的" + TOP + " " + full + "/" + mtx.length + (part.length ? "；不全的如「" + clip(part[0].name, 16) + "」（缺" + ["知识", "能力", "素养"].filter(function (x, j) { return ![part[0].kn, part[0].ab, part[0].li][j]; }).join("、") + "目标）" : ""));
      mtx.filter(function (r) { return !(r.kn && r.ab && r.li); }).slice(0, 10).forEach(function (r) { find("L04", clip(r.name, 18), "", "三维教学目标不全", "补齐知识目标、能力目标、素养目标", LVL_MUST); });
      var dupCol = [], seenTxt = {};
      mtx.forEach(function (r) { Object.keys(r.colTxt).forEach(function (k) { var v = r.colTxt[k]; if (v.length < 20) return; var key = k + "|" + v.slice(0, 60); if (seenTxt[key]) dupCol.push({ a: seenTxt[key], b: r.name, k: k }); else seenTxt[key] = r.name; }); });
      row("L06", dupCol.length ? "不符合" : "符合", dupCol.length ? dupCol.length + " 处栏目内容在不同" + TOP + "间照抄，如「" + dupCol[0].k + "」在「" + clip(dupCol[0].a, 12) + "」与「" + clip(dupCol[0].b, 12) + "」完全相同" : "未见各" + TOP + "栏目内容照抄");
      dupCol.slice(0, 10).forEach(function (d) { find("L06", clip(d.b, 18), d.k, "栏目内容与「" + clip(d.a, 12) + "」完全相同，形式化", "按本章内容重写", LVL_MUST); });
      var szN = mtx.filter(function (r) { return r.sz; }).length;
      row("Z01", szN ? (szN === mtx.length ? "符合" : "需作者确认") : "不符合", "有思政或素养提升内容的" + TOP + " " + szN + "/" + mtx.length + "（通过内容与案例融入的由审读另判）");
    } else { ["L01", "L04", "L06"].forEach(function (id) { row(id, "未检", "未识别出章／项目，无法逐章核对"); }); row("Z01", /素养|思政|工匠|家国/.test(text) ? "需作者确认" : "不符合", "未识别出章；全书" + (/素养|思政|工匠|家国/.test(text) ? "有" : "未见") + "思政相关内容"); }
    var pol = sents.filter(function (x) { return /双碳|碳达峰|碳中和|乡村振兴|职业教育法|产教融合|校企合作|新质生产力|二十大|二十届|高质量发展|国家职业教育改革实施方案|教育强国/.test(x.s); });
    row("Z04", pol.length ? "提请人工" : "符合", pol.length ? "涉及国家战略、重大政策表述 " + pol.length + " 处，须与官方文件口径逐字核对" : "未涉及国家战略、重大政策的表述");
    pol.slice(0, 15).forEach(function (x) { find("Z04", posOf(x.i), x.s, "国家战略或重大政策表述", "对照官方文件核对，确保口径一致", LVL_HUM); });

    /* —— 9. 辅文 —— */
    if (iTiyao >= 0) {
      var end = lines.length; [iQian, iMulu, chaps[0] ? chaps[0].i0 : -1].forEach(function (x) { if (x > iTiyao && x < end) end = x; });
      var ty = lines.slice(iTiyao + 1, Math.min(end, iTiyao + 12)).join(""), n = charCount(ty);
      var aud = /适用|适合|可作为|可供|读者|专业|院校|学生|人员/.test(ty);
      var okLen = n >= 200 && n <= 450;
      row("K02", okLen && aud ? "符合" : "不符合", "内容提要约 " + n + " 字（要求300字左右）；读者对象与适用专业：" + (aud ? "已写" : "未写") + "；与正文、目录顺序的一致性由审读另核");
      if (!okLen) find("K02", "内容提要", ty, "内容提要约 " + n + " 字，与300字左右的要求不符", "调整到300字左右，重点突出、详略得当", LVL_SUG);
      if (!aud) find("K02", "内容提要", ty, "未写明读者对象与适用专业", "写明读者层次与适用专业", LVL_MUST);
      facts.tiyao = ty;
    } else row("K02", "不符合", "无内容提要");
    if (iQian >= 0) {
      var e2 = lines.length; [iMulu, chaps[0] ? chaps[0].i0 : -1].forEach(function (x) { if (x > iQian && x < e2) e2 = x; });
      var qy = lines.slice(iQian + 1, Math.min(e2, iQian + 60)).join("\n");
      var el = { 背景: /编写|背景|为了|为适应|根据|贯彻|落实|要求/.test(qy), 特色: /特色|特点|亮点/.test(qy), 分工: /编写分工|分工如下|具体分工|负责编写|执笔|编写人员|编写组成员|由.{1,16}(负责|编写|撰写)第|第.{1,6}(章|项目|模块|单元).{0,12}由.{1,16}(编写|撰写|负责)/.test(qy), 自谦: /疏漏|不足之处|批评指正|不妥之处|水平有限|宝贵意见/.test(qy), 政策: /二十大|方案|意见|纲要|职业教育法|办法|通知|精神/.test(qy) };
      row("K03", el.分工 ? "需作者确认" : "不符合", "前言要素——编写背景：" + (el.背景 ? "有" : "无") + "；特色：" + (el.特色 ? "有" : "无") + "；编写分工：" + (el.分工 ? "有（须与版权页名单一致、与章节一一对应）" : "无") + "；自谦：" + (el.自谦 ? "有" : "无") + (el.政策 ? "；含政策性表述，须与官方文件一致" : ""));
      if (!el.分工) find("K03", "前言", "", "前言未写编写分工", "写明编写分工，名单与版权页一致、分工与章节对应", LVL_ASK);
      facts.qianyan = qy.slice(0, 1500);
    } else row("K03", "不符合", "无前言");
    // 书名、主编
    var docTitle = (lines[0] || "").replace(/^《|》$/g, "");
    if (info.title || info.topic) {
      var t1 = nz(info.title || ""), t2 = nz(info.topic || "");
      var hit = t1 && text.slice(0, 3000).indexOf(info.title) >= 0;
      row("K01", t2 && t1 && t1 !== t2 ? "不符合" : hit ? "符合" : "需作者确认", "送审书名《" + (info.title || "—") + "》" + (info.topic ? "；选题《" + info.topic + "》" : "") + (info.editor ? "；主编：" + info.editor : "") + (hit ? "；与稿件首页一致" : "；稿件首页未见同名书名，请核对"));
    } else row("K01", "需作者确认", "输入框未提供书名、主编与选题信息；稿件首行为「" + clip(docTitle, 30) + "」，请与选题单核对");
    // 参考文献
    if (iRef >= 0) {
      var refs = [];
      for (var ri = iRef + 1; ri < lines.length && refs.length < 400; ri++) {
        var l = lines[ri]; if (/^附录/.test(nz(l)) && l.length < 30) break;
        if (/^\s*[\[［【]?\d{1,3}[\]］】.、]/.test(l) || /\[(M|J|N|D|R|S|C|P|Z|A|G|EB\/OL|DB\/OL|CP\/OL|J\/OL|M\/OL)\]/.test(l)) refs.push({ i: ri, l: l });
        else if (refs.length && l.length > 60 && !isHead(l)) break;
      }
      var noType = refs.filter(function (r) { return !/\[(M|J|N|D|R|S|C|P|Z|A|G|EB\/OL|DB\/OL|CP\/OL|J\/OL|M\/OL|N\/OL)\]/.test(r.l); });
      var noYear2 = refs.filter(function (r) { return !/(19|20)\d{2}/.test(r.l); });
      var olNoDate = refs.filter(function (r) { return /\/OL\]/.test(r.l) && !/\[\d{4}-\d{2}-\d{2}\]/.test(r.l); });
      var badSrc = refs.filter(function (r) { return /百度百科|维基百科|百度文库|博客|知乎/.test(r.l); });
      var nums = refs.map(function (r) { var m = /^\s*[\[［【]?(\d{1,3})/.exec(r.l); return m ? +m[1] : null; }).filter(function (x) { return x != null; });
      var seqBad = nums.some(function (n, j) { return j && n !== nums[j - 1] + 1; });
      facts.refs = refs.length;
      var kb = noType.length || noYear2.length || olNoDate.length || seqBad || badSrc.length;
      row("K05", !refs.length ? "需作者确认" : kb ? "不符合" : "符合", !refs.length ? "未能逐条识别参考文献，请人工按 GB/T 7714—2025 核对" : "参考文献 " + refs.length + " 条：缺文献类型标识 " + noType.length + "；缺年份 " + noYear2.length + "；电子资源缺引用日期 " + olNoDate.length + (seqBad ? "；序号不连续" : "") + (badSrc.length ? "；引用百科、文库、博客等非权威来源 " + badSrc.length : ""));
      noType.slice(0, 15).forEach(function (r) { find("K05", "参考文献", r.l, "缺文献类型标识", "按 GB/T 7714—2025 补 [M]、[J] 等标识，如：[8]杨世武.铁路信号电磁兼容技术[M].北京：中国铁道出版社有限公司，2022.", LVL_MUST); });
      olNoDate.slice(0, 10).forEach(function (r) { find("K05", "参考文献", r.l, "电子资源缺引用日期", "补 [引用日期] 与获取路径", LVL_MUST); });
      badSrc.slice(0, 10).forEach(function (r) { find("K05", "参考文献", r.l, "引用非权威来源", "换为权威文献", LVL_MUST); });
    } else row("K05", "不符合", "无参考文献");
    // 附录
    if (appHeads.length) {
      var abForm = appHeads.every(function (h) { return /^附录[A-Z]/.test(h); }) || appHeads.length === 1;
      row("K06", abForm ? "需作者确认" : "不符合", "附录 " + appHeads.length + " 项" + (abForm ? "" : "，多项附录未按「附录A」「附录B」编排") + "；附录中的标准、法规是否现行、术语是否与正文统一由审读另核");
      if (!abForm) find("K06", "附录", appHeads.join("、"), "多项附录未按「附录A」「附录B」编排", "改为附录A、附录B……，附录中的图表编号", LVL_SUG);
    } else row("K06", "符合", "无附录");
    // 数据时效
    var datas = sents.filter(function (x) { var y = /((?:19|20)\d{2})\s*年/.exec(x.s); return y && +y[1] < nowY - 3 && +y[1] > 1990 && /数据|统计|报告|增长|占比|规模|产值|销售额|市场|用户|亿元|万元|万人|亿人|%|％|同比|环比/.test(x.s) && !/成立|创办|提出|发布了?《|颁布|实施|诞生|发明|年代/.test(x.s); });
    facts.oldData = datas.length;
    row("K08", datas.length ? "需作者确认" : "符合", datas.length ? datas.length + " 处数据的年份早于 " + (nowY - 3) + " 年，须更新到近3年（行业数据近1—2年）并标注权威来源" : "机检未见过旧数据；数据来源与案例真实性由审读另核");
    datas.slice(0, 20).forEach(function (x) { find("K08", posOf(x.i), x.s, "数据年份较旧", "更新为近3年数据（行业近1—2年），标注政府网站、核心期刊、行业报告等来源", LVL_ASK); });
    var recent = sents.filter(function (x) { var y = /((?:19|20)\d{2})\s*年/.exec(x.s); return y && +y[1] >= nowY - 3; }).length, front = sents.filter(function (x) { return /人工智能|大模型|生成式|AIGC|AI|智能制造|数字孪生|物联网|5G|6G|区块链|新能源|储能|碳中和|鸿蒙|元宇宙|工业互联网|低空经济|具身智能|机器人|无人机|自动驾驶/.test(x.s); }).length;
    facts.front = { recent: recent, kw: front, ratio: sents.length ? front / sents.length : 0 };

    /* —— 10. 语言 —— */
    var abbr = [];
    sents.forEach(function (x) { ABBR_TERMS.forEach(function (p) { var re = new RegExp(p[0] + "(?!子)"); if (re.test(x.s) && x.s.indexOf(p[1]) < 0) abbr.push({ i: x.i, s: x.s, p: p }); }); });
    row("Y03", abbr.length ? "不符合" : "符合", abbr.length ? "术语简化 " + abbr.length + " 处，如「" + abbr[0].p[0] + "」应写「" + abbr[0].p[1] + "」" : "机检未见术语简化（如电商）");
    abbr.slice(0, 15).forEach(function (x) { find("Y03", posOf(x.i), x.s, "术语简化「" + x.p[0] + "」", "改为「" + x.p[1] + "」", LVL_MUST); });
    var shortLaw = [], seenFull = {};
    sents.forEach(function (x) {
      var re = /《(中华人民共和国)?([^《》]{2,20}?(?:法|条例|规定|办法))》/g, m;
      while ((m = re.exec(x.s))) { var core = m[2]; if (m[1]) { seenFull[core] = 1; continue; } if (/^(中华人民共和国)/.test(core)) continue; if (!seenFull[core] && /法$/.test(core) && !/简称/.test(x.s) && core.length <= 8) { shortLaw.push({ i: x.i, s: x.s, c: core }); seenFull[core] = 1; } }
    });
    row("Y04", shortLaw.length ? "不符合" : "符合", shortLaw.length ? shortLaw.length + " 部法律首次出现即用简称，如《" + shortLaw[0].c + "》" : "法律、标准首次出现均用全称或已说明简称");
    shortLaw.slice(0, 10).forEach(function (x) { find("Y04", posOf(x.i), x.s, "法律首次出现用简称《" + x.c + "》", "首次写全称并注明：《中华人民共和国" + x.c + "》（下文简称《" + x.c + "》）", LVL_SUG); });
    function listScan(id, words, label, fix, lvl) {
      var hits = [];
      sents.forEach(function (x) { words.forEach(function (w2) { if (x.s.indexOf(w2) >= 0) hits.push({ i: x.i, s: x.s, w: w2 }); }); });
      return hits;
    }
    var oral = listScan("Y06", ORAL);
    row("Y06", oral.length > 5 ? "不符合" : oral.length ? "需作者确认" : "符合", oral.length ? "口语化词语 " + oral.length + " 处：" + uniq(oral.map(function (x) { return x.w; })).slice(0, 8).join("、") + "（审读另判）" : "机检未见口语化词语（审读另判）");
    oral.slice(0, 15).forEach(function (x) { find("Y06", posOf(x.i), x.s, "口语化「" + x.w + "」", "改为书面语", LVL_SUG); });
    var stepSents = sents.filter(function (x) { return /^(步骤|第\s*\d+\s*步|\d+[.、．]|[（(]\d+[)）]|①|②|③|④|⑤)/.test(lines[x.i] || "") && /点击|单击|双击|输入|选择|设置|安装|按装|调整|拧|加入|加热|按下|打开|关闭|连接|插入|拆卸|测量|配制|称取|移取|滴加|放置|放在|摆放|搬运|清点|入库|出库|拣选|操作|填写|检查|核对|启动|运行|保存|上传/.test(x.s); });
    var vague = []; stepSents.forEach(function (x) { VAGUE.forEach(function (v) { if (x.s.indexOf(v) >= 0) vague.push({ i: x.i, s: x.s, w: v }); }); });
    row("Y07", vague.length ? "不符合" : "符合", vague.length ? "操作步骤中出现模糊表述 " + vague.length + " 处：" + uniq(vague.map(function (x) { return x.w; })).join("、") : "操作步骤（" + stepSents.length + " 句）中未见「大概」「可能」等模糊表述");
    vague.slice(0, 15).forEach(function (x) { find("Y07", posOf(x.i), x.s, "操作步骤表述模糊「" + x.w + "」", "写明确的数值、条件或判据", LVL_MUST); });
    var typo = []; sents.forEach(function (x) { TYPO.forEach(function (p) { if (x.s.indexOf(p[0]) >= 0) typo.push({ i: x.i, s: x.s, p: p }); }); });
    row("Y08", typo.length ? "不符合" : "符合", typo.length ? "机检常见错别字 " + typo.length + " 处" : "机检常见错别字表未命中（逐单元审读另查）");
    typo.slice(0, 30).forEach(function (x) { find("Y08", posOf(x.i), x.s, "错别字「" + x.p[0] + "」", "改为「" + x.p[1] + "」", LVL_MUST); });
    var sl = listScan("Y10", SLANG);
    row("Y10", sl.length ? "不符合" : "符合", sl.length ? "网络词语 " + sl.length + " 处：" + uniq(sl.map(function (x) { return x.w; })).slice(0, 8).join("、") : "未见网络词语");
    sl.slice(0, 15).forEach(function (x) { find("Y10", posOf(x.i), x.s, "网络词语「" + x.w + "」", "改为规范书面语", LVL_SUG); });
    var mix = [];
    sents.forEach(function (x) { var re = /[一-龥]\s?([a-z]{2,10})\s?[一-龥]/g, m; while ((m = re.exec(x.s))) if (EN_EVERYDAY.indexOf(m[1]) >= 0) mix.push({ i: x.i, s: x.s, w: m[1] }); });
    row("Y11", mix.length ? "不符合" : "符合", mix.length ? "中外文混用 " + mix.length + " 处，如「" + mix[0].w + "」" : "未见中外文词语混用（专业术语、代码、缩略语不在此列）");
    mix.slice(0, 15).forEach(function (x) { find("Y11", posOf(x.i), x.s, "中外文混用「" + x.w + "」", "改用中文表达", LVL_SUG); });
    var punct = [];
    sents.forEach(function (x) {
      var s = x.s;
      if (/[一-龥][,;:?!][一-龥]/.test(s)) punct.push({ i: x.i, s: s, w: "中文里用了半角标点" });
      if (/、等(?![级同效])/.test(s)) punct.push({ i: x.i, s: s, w: "「等」前加了顿号" });
      if (/……等|等……/.test(s)) punct.push({ i: x.i, s: s, w: "省略号与「等」并用" });
      if (/[^.]\.\.\.(?!\.)/.test(s) && /[一-龥]/.test(s) && !/https?:/.test(s)) punct.push({ i: x.i, s: s, w: "中文省略号写成「...」" });
      if (/[一二三四五六七八九十]、[一二三四五六七八九十][个次天年人名种件条项倍]/.test(s)) punct.push({ i: x.i, s: s, w: "相邻数字表概数加了顿号" });
      if (/\d+万\d+千/.test(s)) punct.push({ i: x.i, s: s, w: "数字混写（如3万5千）" });
      if (/(?:^|[^\d.])\.\d/.test(s) && /[一-龥]/.test(s) && !/https?:|www/.test(s)) punct.push({ i: x.i, s: s, w: "纯小数缺前导0" });
      if (/(?:于|在|至|到|是|从)\s*['’]?\d{2}年(?!代|级|来|间|内|以|前|后|度|版|左|多)/.test(s) || /['’]\d{2}年/.test(s)) punct.push({ i: x.i, s: s, w: "年份疑似简写" });
      var lq = (s.match(/[“]/g) || []).length, rq = (s.match(/[”]/g) || []).length; if (lq !== rq) punct.push({ i: x.i, s: s, w: "引号不成对" });
      var lb = (s.match(/[（]/g) || []).length, rb = (s.match(/[）]/g) || []).length; if (lb !== rb) punct.push({ i: x.i, s: s, w: "括号不成对" });
    });
    row("Y12", punct.length > 10 ? "不符合" : punct.length ? "需作者确认" : "符合", punct.length ? "标点与数字用法问题 " + punct.length + " 处：" + uniq(punct.map(function (x) { return x.w; })).join("、") : "机检未见标点、数字用法问题（审读另查）");
    punct.slice(0, 40).forEach(function (x) { find("Y12", posOf(x.i), x.s, x.w, "按 GB/T 15834、GB/T 15835 改正", LVL_SUG); });

    /* —— 11. 公式、图片 —— */
    var fNo = lines.filter(function (l) { return /[（(]\d+[-－.]\d+[)）]\s*$/.test(l) && l.length < 80; }).length + (text.match(/式\s*[（(]\d+[-－.]\d+[)）]/g) || []).length;
    facts.formulaNo = fNo;
    if (meta) {
      var ole = meta.ole || {}, eq3 = 0, mt = 0, others2 = [];
      Object.keys(ole).forEach(function (k) { if (/^Equation\.3$/i.test(k)) eq3 += ole[k]; else if (/DSMT|MathType/i.test(k)) mt += ole[k]; else others2.push(k + "×" + ole[k]); });
      var editable = (meta.omml || 0) + mt;
      row("F03", eq3 ? "不符合" : "符合", eq3 ? eq3 + " 个公式由 Equation Editor 3.0（低版本公式编辑器）创建，无法直接导入排版" : "未见低版本公式编辑器（Word 公式 " + (meta.omml || 0) + " 个" + (mt ? "，MathType " + mt + " 个" : "") + "）");
      if (eq3) find("F03", "全书", "", eq3 + " 个公式为 Equation 3.0", "升级 Word，用新版公式编辑器重新录入", LVL_MUST);
      if (fNo > 0 && editable + eq3 === 0) { row("F02", "不符合", "稿中有公式编号 " + fNo + " 处，却没有一个可编辑公式对象：公式疑为图片"); find("F02", "全书", "", "公式疑为图片", "用 Word 公式编辑器重新录入", LVL_MUST); }
      else if (fNo > editable + eq3 + 2) { row("F02", "需作者确认", "公式编号 " + fNo + " 处，可编辑公式对象 " + (editable + eq3) + " 个：部分公式可能是图片"); find("F02", "全书", "", "部分公式可能是图片", "核对并改为可编辑公式", LVL_ASK); }
      else row("F02", "符合", fNo || editable ? "可编辑公式对象 " + (editable + eq3) + " 个，公式编号 " + fNo + " 处" : "稿中没有公式");
      facts.ole = others2;
      // 图片分辨率
      var ims = (meta.images || []).filter(function (x) { return !x.vec; }), known = ims.filter(function (x) { return x.w && x.h; });
      var low = known.filter(function (x) { var a = Math.max(x.w, x.h), b = Math.min(x.w, x.h); return (a < 1280 || b < 720) && a >= 300; }), tiny = known.filter(function (x) { return Math.max(x.w, x.h) < 300; });
      facts.imgRes = { total: ims.length, known: known.length, low: low.length, tiny: tiny.length, vec: (meta.images || []).length - ims.length };
      if (!ims.length) row("F05", "符合", "稿中无位图图片");
      else row("F05", low.length ? "不符合" : "符合", "位图 " + ims.length + " 幅（读出尺寸 " + known.length + " 幅）：低于1280×720 的 " + low.length + " 幅" + (tiny.length ? "；另有小于300像素的小图 " + tiny.length + " 幅（多为图标，若为知识图片同须替换）" : "") + (meta.images.length - ims.length ? "；矢量图 " + (meta.images.length - ims.length) + " 幅" : ""));
      if (low.length) find("F05", "全书", low.slice(0, 8).map(function (x) { return x.n + "（" + x.w + "×" + x.h + "）"; }).join("、"), low.length + " 幅图片分辨率低于1280×720", "替换为不低于1280×720（建议1920×1080）的原图", LVL_MUST);
      var cad = /机械|建筑|电气|电路|工程制图|CAD|结构图|施工图|装配图|零件图|电路图/.test(text), hasSrc = (meta.embeds || []).some(function (n) { return /dwg|dxf/i.test(n); }) || res.some(function (r) { return /^(dwg|dxf|dwf|dwt)$/i.test(r.ext); });
      row("F06", cad && !hasSrc ? "需作者确认" : (meta.drawings ? "提请人工" : "符合"), cad ? ("稿件涉及机械、建筑、电气类图纸" + (hasSrc ? "，已见 CAD 源文件" : "：复杂线条图（超过20条线）须提供 CAD 等可编辑源文件") + "；位图线条图的分辨率按实物图标准见 F05；线条、文字是否清晰须人工过目") : (meta.drawings ? "线条图是否清晰须人工过目" : "稿中无图片"));
      if (cad && !hasSrc) find("F06", "全书", "", "复杂线条图未见源文件", "提供 CAD 或其他可编辑源文件", LVL_ASK);
      facts.revs = { ins: meta.ins, del: meta.del, comments: meta.comments };
    } else {
      row("F02", fNo ? "需作者确认" : "未检", fNo ? "稿中有公式编号 " + fNo + " 处；需 .docx 原稿才能判断公式是否为图片" : "需 .docx 原稿");
      row("F03", "未检", "需 .docx 原稿才能识别公式编辑器版本");
      row("F05", "未检", "需 .docx 原稿才能读图片分辨率");
      row("F06", "未检", "需 .docx 原稿；复杂线条图须提供 CAD 等源文件");
    }
    var aiMark = sents.filter(function (x) { return /AI\s*生成|AIGC\s*生成|由\s*AI\s*(生成|绘制)|人工智能生成|AI\s*绘图|AI\s*作图/.test(x.s); }).concat(((meta && meta.alt) || []).filter(function (a) { return /AI/.test(a); }).map(function (a) { return { i: -1, s: a }; }));
    row("F07", aiMark.length ? "提请人工" : (meta && meta.drawings === 0 ? "符合" : "提请人工"), aiMark.length ? "标注 AI 生成的图片 " + aiMark.length + " 处：须判断是否符合生活逻辑与常识" : (meta && meta.drawings === 0 ? "稿中无图片" : "未见「AI生成」标注；须人工过目，疑似 AI 生成的与作者确认，属实须标注来源"));
    aiMark.slice(0, 10).forEach(function (x) { find("F07", x.i >= 0 ? posOf(x.i) : "图片说明", x.s, "AI 生成图片", "核查是否符合生活逻辑、常识，并保留来源标注", LVL_HUM); });

    /* —— 12. 字数 —— */
    var kind = info.kind || "", perPage = info.perPage || 1400;
    var coef = info.coef || (/(机械|建筑|电气|电路|工程制图|施工)/.test(text) ? 0.8 : /(计算机|程序|软件|编程|网络|数据库|Python|Java)/.test(text) ? 0.5 : /(艺术|设计|美术|摄影|服装|插画)/.test(text) ? 0.2 : 0.5);
    var chars = charCount(text), han = hanCount(text);
    var imgN2 = meta ? (meta.drawings || 0) : 0, imgEq = Math.round(imgN2 * perPage / 3 * coef);
    var exN = (text.match(/^\s*\d+\s*[.、．]\s*.{2,}[（(]\s*[)）]|[（(]\s*[)）]\s*$|_{3,}/gm) || []).length;
    var bubbles = (text.match(/【气泡】|〔气泡〕|\[气泡\]/g) || []).length;
    var interEq = info.digital ? (exN + bubbles) * 100 : 0;
    var attW = 0, attLines = [];
    others.forEach(function (d) { if (/查重|复制比|检测报告/.test((d.name || "") + (d.text || "").slice(0, 500))) return; var c = charCount(d.text); attW += c; attLines.push((d.name || "附件") + "：" + fmtWan(c) + (/\.pdf$/i.test(d.name || "") ? "（PDF：需审校的应转为 Word）" : "")); });
    res.forEach(function (r) { if (/^pp/.test(r.ext) && r.slides) { attW += r.slides * 200; attLines.push(r.name + "：PPT " + r.slides + " 面 × 200 字＝" + fmtWan(r.slides * 200)); } });
    var total = chars + imgEq + interEq + attW;
    facts.words = { chars: chars, han: han, imgN: imgN2, coef: coef, perPage: perPage, imgEq: imgEq, exN: exN, bubbles: bubbles, interEq: interEq, attW: attW, attLines: attLines, total: total };
    row("N01", "符合", "正文字符（不含空格）" + fmtWan(chars) + "（汉字 " + fmtWan(han) + "）；图片 " + imgN2 + " 幅按每幅约1/3面、每面 " + perPage + " 字、系数 " + coef + " 折算 " + fmtWan(imgEq) + (info.digital ? "；气泡 " + bubbles + "、交互习题约 " + exN + " 条×100字＝" + fmtWan(interEq) : "") + (attW ? "；附件 " + fmtWan(attW) : "") + "；合计约 " + fmtWan(total) + "（估算，以排版后「行数×列数×面数×系数」核算为准）");
    row("N03", info.coef ? "符合" : "需作者确认", "本稿按系数 " + coef + " 折算图片及空白版" + (info.coef ? "（输入框指定）" : "（由正文推断：" + (coef === 0.8 ? "机械、建筑、电气类线条图" : coef === 0.2 ? "艺术类实物图" : "计算机类或一般实物图") + "；请编辑确认，可在输入框写「图片系数：0.2／0.5／0.8」）"));
    row("N04", info.digital ? "符合" : "未检", info.digital ? "气泡 " + bubbles + " 个、交互习题约 " + exN + " 条，按100字/个（条）计 " + fmtWan(interEq) : "非数字教材（输入框未注明「数字教材」），不计气泡与交互习题字数");
    row("N05", attLines.length ? "符合" : "未检", attLines.length ? "附件折算：" + attLines.join("；") : "未随稿提供附件");
    var need = KIND_WORDS[kind];
    if (need) {
      var dev = (total - need) / need;
      row("N02", Math.abs(dev) <= 0.15 ? "符合" : "需作者确认", KIND_NAME[kind] + (info.kindGuess ? "（由正文推断）" : "") + "要求约 " + fmtWan(need) + "，本稿约 " + fmtWan(total) + "（" + (dev >= 0 ? "多" : "少") + " " + Math.abs(dev * 100).toFixed(0) + "%）");
      if (Math.abs(dev) > 0.15) find("N02", "全书", "", "字数与要求相差 " + Math.abs(dev * 100).toFixed(0) + "%", dev < 0 ? "补足核心内容" : "压缩篇幅或与编辑商定", LVL_ASK);
    } else row("N02", "需作者确认", "未确定稿件类型（职业教育35万字；本科理工50万字、文管45万字；专著20万字），本稿约 " + fmtWan(total) + "；请在输入框写明「类型：……」");

    /* —— 13. 交互素材与资源 —— */
    var bubTxt = []; var reB = /【气泡】([^【\n]{1,400})/g, mb2; while ((mb2 = reB.exec(text))) bubTxt.push(mb2[1]);
    var bubBad = bubTxt.filter(function (b) { var n = charCount(b); return n < 50 || n > 100; });
    row("R01", bubTxt.length ? (bubBad.length ? "不符合" : "符合") : "未检", bubTxt.length ? "气泡 " + bubTxt.length + " 个，不在50～100字的 " + bubBad.length + " 个" : "稿中未用「【气泡】」标注气泡（如有气泡请这样标注以便核查）");
    bubBad.slice(0, 10).forEach(function (b) { find("R01", "气泡", b, "气泡字数 " + charCount(b) + "，不在50～100字", "调整到50～100字", LVL_SUG); });
    var xN = mtx.reduce(function (a, r) { return a + r.x; }, 0);
    row("R02", xN ? "符合" : "未检", xN ? "拓展阅读、知识链接等 " + xN + " 处，排版时设为可折叠" : "稿中未见拓展阅读类栏目");
    row("R03", urls.length ? "需作者确认" : "符合", urls.length ? "超链接 " + urls.length + " 个：须稳定、已授权，且不作为正文的重要组成部分（链接失效后不影响正文理解）" : "稿中没有超链接");
    var exTypes = { 选择题: /选择题|单选题|多选题|单项选择|多项选择/, 填空题: /填空题/, 判断题: /判断题/, 排序题: /排序题/, 配对题: /配对题|连线题|匹配题/ };
    var has2 = Object.keys(exTypes).filter(function (k) { return exTypes[k].test(text); });
    var ans = /参考答案|【答案】|答案[:：]|答案与解析|习题答案|答案解析/.test(text) || others.some(function (d) { return /答案/.test(d.name + (d.text || "").slice(0, 2000)); });
    row("R04", !has2.length ? "符合" : ans ? "符合" : "不符合", has2.length ? "稿中有" + has2.join("、") + "；" + (ans ? "已见答案" : "未见答案，须提供") : "稿中没有须附答案的题型（简答题可不提供答案）");
    if (has2.length && !ans) find("R04", "习题", "", has2.join("、") + "未提供答案", "提供选择、填空、判断、排序、配对题的答案", LVL_MUST);
    var avs = res.filter(function (r) { return AV.test(r.ext || ""); });
    var big = avs.filter(function (r) { return r.size > 100 * 1048576; }), huge = avs.filter(function (r) { return r.size > 200 * 1048576; });
    row("R05", avs.length ? "提请人工" : "未检", avs.length ? "音视频 " + avs.length + " 个，须人工看：画面声音清晰、时长合理、书名院校准确、字幕无大量错误" + (avs.some(function (r) { return r.dur > 900; }) ? "；其中时长超过15分钟的 " + avs.filter(function (r) { return r.dur > 900; }).length + " 个，宜拆分" : "") : "未随稿提供音视频");
    row("R06", !avs.length ? "未检" : huge.length ? "不符合" : big.length ? "不符合" : "符合", !avs.length ? "未随稿提供音视频（可在输入框列出「文件名 大小」）" : "单个最大 " + mb(Math.max.apply(null, avs.map(function (r) { return r.size; }))) + "；超过100MB 的 " + big.length + " 个" + (huge.length ? "，其中超过200MB（无法上传）" + huge.length + " 个" : ""));
    big.slice(0, 10).forEach(function (r) { find("R06", "资源", r.name, "视频 " + mb(r.size) + "，超过100MB" + (r.size > 200 * 1048576 ? "（超过200MB无法上传）" : ""), "压缩到100MB以内或拆分", LVL_MUST); });
    var totalRes = res.reduce(function (a, r) { return a + (r.size || 0); }, 0), cap = KIND_CAP[kind];
    if (!res.length) row("R07", "未检", "未随稿提供资源");
    else if (cap == null) row("R07", "需作者确认", "资源合计 " + mb(totalRes) + "；未确定稿件类型（职业教育5G、本科8G、专著0G）");
    else row("R07", totalRes <= cap ? "符合" : "不符合", "资源合计 " + mb(totalRes) + "，" + KIND_NAME[kind] + "上限 " + (cap ? (cap / 1073741824) + "G" : "0G（专著不配音视频资源）"));
    if (cap != null && res.length && totalRes > cap) find("R07", "资源", "", "资源总容量超限", cap ? "压缩或删减资源到 " + (cap / 1073741824) + "G 以内" : "专著不配音视频资源", LVL_MUST);
    var notMp4 = avs.filter(function (r) { return !/^(mp4|m4v)$/.test(r.ext) || (r.codec && r.codec !== "H.264"); });
    row("R08", !avs.length ? "未检" : notMp4.length ? "不符合" : avs.every(function (r) { return r.codec; }) ? "符合" : "需作者确认", !avs.length ? "未随稿提供音视频" : notMp4.length ? notMp4.length + " 个不是 MP4／H.264：" + notMp4.slice(0, 5).map(function (r) { return r.name + "（" + r.ext.toUpperCase() + (r.codec ? "／" + r.codec : "") + "）"; }).join("、") : "均为 MP4" + (avs.every(function (r) { return r.codec; }) ? "／H.264" : "（部分未能读出编码，请确认为 H.264）"));
    notMp4.slice(0, 10).forEach(function (r) { find("R08", "资源", r.name, "格式不是 MP4／H.264", "转为 MP4（H.264 编码）", LVL_MUST); });
    var emb = res.filter(function (r) { return !AV.test(r.ext || ""); }).concat(((meta && meta.embeds) || []).map(function (n) { return { name: n, ext: (n.split(".").pop() || "").toLowerCase(), size: 0, inDoc: 1 }; }));
    var embBad = emb.filter(function (r) { return !EMBED_OK.test(r.ext) && !/^bin$/i.test(r.ext); }), embBig = emb.filter(function (r) { return r.size > 100 * 1048576; });
    row("R09", !emb.length ? "未检" : (embBad.length || embBig.length) ? "不符合" : "符合", !emb.length ? "无其他嵌入文件" : "其他文件 " + emb.length + " 个" + (embBad.length ? "；格式不在支持列表的 " + embBad.length + " 个（" + embBad.slice(0, 4).map(function (r) { return r.name; }).join("、") + "）" : "") + (embBig.length ? "；超过100MB 的 " + embBig.length + " 个" : ""));
    embBad.slice(0, 10).forEach(function (r) { find("R09", "资源", r.name, "格式不在「插入文件嵌入」支持列表", "转为支持的格式（Office、WPS、PDF、OFD、CAD、3D 模型等）", LVL_MUST); });
    var marks = (text.match(/【(?:微课|视频|动画|音频|资源|在线测试|虚拟仿真|3D|三维模型)[^】]{0,20}】|扫码|二维码|扫一扫|▶\s*视频/g) || []).length;
    facts.resMarks = marks;
    row("R10", res.length && !marks ? "不符合" : marks ? "需作者确认" : "未检", res.length && !marks ? "随稿资源 " + res.length + " 个，正文中未见资源位置标注（如【微课】、二维码）" : marks ? "正文资源标注 " + marks + " 处" + (res.length ? "，资源 " + res.length + " 个" : "，未随稿提供资源文件") + "；与知识点的关联由审读另核" : "正文未见资源标注，也未随稿提供资源");
    if (res.length && !marks) find("R10", "全书", "", "正文未标注资源位置", "在相应知识点处标注【微课】【视频】等及资源名", LVL_MUST);
    var attIssues = [];
    others.forEach(function (d) { if (/\.pdf$/i.test(d.name || "") && !/查重|复制比|检测报告/.test((d.name || "") + (d.text || "").slice(0, 500))) attIssues.push(d.name + "：PDF 不可编辑，需审校的请转为 Word；只放无须审校的标准、法规条文"); });
    res.forEach(function (r) { if (/^pp/.test(r.ext)) attIssues.push(r.name + "：PPT 课件建议单独提供给授课教师，不插入教材（如须展示按200字/面计）"); if (/^xls/.test(r.ext)) attIssues.push(r.name + "：Excel 工单、习题应编入正文，不单独提供"); });
    if (info.digital) others.forEach(function (d) { if (/\.docx?$/i.test(d.name || "")) attIssues.push(d.name + "：数字新稿的 Word 附件内容应直接编写在正文对应位置"); });
    row("R11", attIssues.length ? "不符合" : (others.length || res.length ? "符合" : "未检"), attIssues.length ? attIssues.join("；") : (others.length || res.length ? "附件形式符合要求" : "未随稿提供附件"));
    attIssues.forEach(function (s) { find("R11", "附件", s.split("：")[0], s.split("：").slice(1).join("："), "", LVL_SUG); });

    /* —— 14. 修订痕迹、批注（不在指导书条目中，作为送审稿件提示） —— */
    if (meta && (meta.ins || meta.del || meta.comments)) facts.revNote = "稿件中仍有修订痕迹（插入 " + meta.ins + "、删除 " + meta.del + "）与批注 " + meta.comments + " 条，送审稿应接受全部修订、删除批注";

    /* —— 机检明细（附录用） —— */
    detail.push("**标题层级**：" + form + "；" + Object.keys(has).map(function (k) { return k + " " + has[k]; }).join("，"));
    if (meta && meta.headings && meta.headings.length) detail.push("**Word 标题样式**：使用标题样式的段落 " + meta.headings.length + " 个（1级 " + meta.headings.filter(function (h) { return h.lv === 1; }).length + "，2级 " + meta.headings.filter(function (h) { return h.lv === 2; }).length + "，3级 " + meta.headings.filter(function (h) { return h.lv === 3; }).length + "）");
    else if (meta) detail.push("**Word 标题样式**：未使用标题样式（大纲视图无法核查层级），建议各级标题套用 Word 标题样式");
    detail.push("**图表**：图题 " + FIG.caps.length + "，图的正文引用 " + FIG.refs.length + "；表题 " + TAB.caps.length + "，表的正文引用 " + TAB.refs.length + (meta ? "；Word 图片 " + meta.drawings + "、表格 " + meta.tables + "、Word 公式 " + meta.omml : ""));
    if (stdList.length) detail.push("**引用标准**：" + stdList.slice(0, 60).map(function (s) { return s.k; }).join("；"));
    if (urls.length) detail.push("**超链接**：" + urls.slice(0, 60).map(function (u) { return u.u; }).join("；"));
    if (res.length) detail.push("**资源文件**：" + res.map(function (r) { return r.name + "（" + mb(r.size || 0) + (r.codec ? "，" + r.codec : "") + (r.dur ? "，" + Math.floor(r.dur / 60) + "分" + (r.dur % 60) + "秒" : "") + "）"; }).join("；"));
    if (facts.revNote) detail.push("**送审稿提示**：" + facts.revNote);
    return { rows: rows, finds: finds, facts: facts, detail: detail, chaps: chaps, top: TOP };
  }

  /* ═════════ 五、审读（模型）——逐单元 ═════════ */
  var UNIT_ITEMS = ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "C05", "S12", "T10", "L03", "L05", "Z02", "Z03", "Z04", "K07", "K08", "K09", "K10", "K11", "Y01", "Y02", "Y05", "Y06", "Y07", "Y08", "Y09", "Y12", "F01", "F04", "R03", "R10"];
  var UNIT_RULE = [
    "【身份】你是出版社的来稿初审编辑，按《来稿初审指导书》审读一部教材来稿的一个单元。你给的是初审意见：发现问题、说清依据、给出修改建议。政治性、意识形态、事实最终核定归人工，涉及的写「提请人工」，不下定论。不确定就说不确定；不编造标准条款号、数据与出处。",
    "【本单元逐项审读，条目编号必须照写】",
    "P01 港澳台不得列为国家、不得与中国并列，不得以中央、国家名义设机构；P02 民族宗教、历史虚无主义、错误价值观、地域歧视——言必有据、尊重习俗信仰、客观不渲染、与官方正史一致；P03 领土完整、国家象征、国际组织性质、外国地名；P04 我国制度与理念阐述准确、时政表述准确；P05 党史重大事件、会议、人物评价科学；P06 领导人姓名职务准确、直接引语须一字不差（只能提请人工核对原文）；P07 敏感人物和企业按主流标签；P08 无低俗暴力违法，无错误导向的示范（如安全生产案例里的违规操作、客户沟通案例里的不当话术），理性分析社会热点；P09 涉密信息。",
    "C05 引用部分有没有标注来源。S12 本单元是否先易后难、先基础后深入。T10 是否按「概念定义→原理讲解→案例分析→实践任务」排布，有无先讲复杂后补基础的倒置。L03 难度是否由浅入深、有无知识断层（讲复杂内容前有无铺垫）、是否超纲或过浅。L05 学习目标能否由正文支撑，能力目标有无配套实操或练习。",
    "Z02 思政融入是否自然、有无两张皮和空话套话；Z03 思政元素是否与学科相关（家国情怀、科学精神、职业操守、法治意识）；Z04 双碳、乡村振兴、新职业教育法、产教融合等表述是否与官方口径一致（拿不准写提请人工）。",
    "K07 理论、概念是否准确、符合学科主流，有无过时理论、常识性错误、推导漏洞，理论深度是否够用为度；K08 数据是否真实、有权威来源、是否近3年（行业近1—2年），案例是否真实可追溯、贴近行业真实场景；K09 引用的标准是否疑似已废止；K10 引用的法律法规是否现行；K11 有无行业新技术、新设备、新规范。",
    "Y01 同一术语全书是否统一（对照下面的术语台账），有无一词多称、自造术语；Y02 用行业俗称是否标注了规范术语；Y05 病句（主语混乱、搭配不当、成分残缺或多余、语序不当、歧义、句式杂糅、逻辑有误）；Y06 口语化；Y07 操作步骤里的「大概」「可能」等模糊表述；Y08 错别字；Y09 生造词语；Y12 标点与数字用法（GB/T 15834、GB/T 15835）。",
    "F01 公式推导是否完整、有无跳步；F04 图表与正文是否对应（图说的与文说的是否一致）；R03 超链接是否成了正文的重要组成部分；R10 资源标注（【微课】【视频】、二维码）是否与知识点对应。",
    "【写法】平常话。每条问题一行，格式固定：〔条目编号〕位置（小节标题或首句几个字）｜原文片段（照引，不超过40字）｜问题｜修改建议｜级别。级别只用四种：必改／建议／需作者确认／提请人工。同类问题合并为一条并列出全部位置。没有问题就写「无」，不要凑。不要重复机检已经能查的事项（编号连续、栏目有无、链接类型），专心读懂内容。",
    "【输出格式：必须按这三段，用这三个标记开头】",
    "【单元判断】一行一项，各一句、引原文位置作证：知识排布（T10）：…；难度与学情（L03／S12）：…；目标与支撑（L05）：…；思政融入（Z02／Z03）：…；前沿内容（K11）：…；政治性（P01—P09）：…",
    "【问题清单】按上面的行格式逐条写",
    "【术语台账】本单元的核心术语（写法、是否已定义），一行一个，简写"
  ].join("\n");
  function unitPrompt(o) {
    // o = { info, title, i, n, name, body, ledger }
    var I = o.info || {};
    var head = UNIT_RULE + "\n\n【稿件信息】《" + (o.title || "") + "》；类型：" + (KIND_NAME[I.kind] || "未定") + (I.digital ? "；数字教材" : "") + "；当前年份：" + new Date().getFullYear() + "\n\n";
    var body = String(o.body || "").slice(0, 8200);
    var room = 19600 - head.length - body.length - 300;
    var led = room > 200 ? String(o.ledger || "").slice(-Math.min(2000, room)) : "";
    return (head + "【单元】第 " + (o.i + 1) + "/" + o.n + " 单元 · " + o.name + "\n\n【术语台账（前面单元）】\n" + (led || "（无）") + "\n\n【本单元原文】\n" + body).slice(0, 19800);
  }
  function pick(s, tag) {
    s = String(s || ""); var i = s.indexOf(tag); if (i < 0) return "";
    var rest = s.slice(i + tag.length), j = rest.search(/【(?:单元判断|问题清单|术语台账)】/);
    return (j >= 0 ? rest.slice(0, j) : rest).trim();
  }
  // 〔ID〕位置｜原文｜问题｜建议｜级别
  function parseUnit(text, unitName) {
    var out = [], body = pick(text, "【问题清单】") || text;
    body.split("\n").forEach(function (l) {
      var m = /[〔\[【(（]\s*([A-Z]\d{2})\s*[〕\]】)）]\s*(.*)$/.exec(l.replace(/\*\*/g, "").replace(/^\s*[-*·\d.、]+\s*/, ""));
      if (!m || !BY[m[1]]) return;
      var p = m[2].split(/[｜|]/).map(function (x) { return x.trim(); });
      var lv = (p[p.length - 1] || "").replace(/[。.\s*]/g, "");
      if (!/^(必改|建议|需作者确认|提请人工)$/.test(lv)) lv = /必改/.test(m[2]) ? "必改" : /提请人工/.test(m[2]) ? "提请人工" : /作者确认/.test(m[2]) ? "需作者确认" : "建议";
      out.push({ id: m[1], pos: (unitName ? clip(unitName, 14) + "·" : "") + (p[0] || ""), src: clip(p[1] || "", 60), issue: p[2] || "", fix: p[3] || "", lvl: lv, by: "审读" });
    });
    return { judge: pick(text, "【单元判断】"), issues: out, ledger: pick(text, "【术语台账】") };
  }

  /* ═════════ 六、逐项结论（模型）与意见（模型）═════════ */
  function itemsPrompt(o) {
    // o = { mc, units:[{name, judge}], issues:[...], title }
    var ids = MODEL_IDS;
    var cnt = {}; (o.issues || []).forEach(function (f) { (cnt[f.id] = cnt[f.id] || { n: 0, must: 0, ex: [] }).n++; if (f.lvl === "必改") cnt[f.id].must++; if (cnt[f.id].ex.length < 2) cnt[f.id].ex.push(clip(f.pos + "：" + f.issue, 50)); });
    var lst = ids.map(function (id) {
      var b = BY[id], r = o.mc.rows[id], c = cnt[id];
      return "〔" + id + "〕" + b.name + "——要求：" + b.req + (r ? "｜机检：" + r.res + "，" + clip(r.note, 90) : "") + "｜审读发现：" + (c ? c.n + " 条（必改 " + c.must + "）" + c.ex.join("；") : "0 条");
    }).join("\n");
    var judges = (o.units || []).filter(function (u) { return u.judge; }).map(function (u, i) { return "· " + clip(u.name, 16) + "：" + clip(u.judge.replace(/\n+/g, " "), 260); }).join("\n");
    var q = "【任务 · 来稿初审逐项结论】你是出版社初审编辑。下面是需要读懂才能下结论的审查项：每项给出要求、机检结果（如有）和各单元审读发现的问题条数与例子；后面是各单元的审读判断。请逐项给结论，每项一行，格式固定：\n〔编号〕结论｜说明（不超过80字，引单元或问题作证）\n结论只用五种：符合／不符合／需作者确认／提请人工／未检。规则：审读发现「必改」问题的，判不符合；政治性、领导人讲话、国家政策口径类，只要有疑点就判提请人工；机检已判不符合的，不得改判符合；证据不足就写需作者确认，并说明要作者确认什么。每一项都要有一行，不许漏，不许合并。不得说「符合出版要求」。\n\n【审查项】\n" + lst + "\n\n【各单元审读判断】\n" + (judges || "（无）");
    return q.slice(0, 19800);
  }
  function parseItems(text) {
    var out = {};
    String(text || "").split("\n").forEach(function (l) {
      var m = /[〔\[【(（]\s*([A-Z]\d{2})\s*[〕\]】)）]\s*[:：]?\s*(不符合|符合|需作者确认|提请人工|未检)\s*[｜|：:]?\s*(.*)$/.exec(l.replace(/^\s*[-*·]+\s*/, "").replace(/\*\*/g, ""));
      if (m && BY[m[1]]) out[m[1]] = { res: m[2], note: m[3].trim() };
    });
    return out;
  }
  function verdictOf(rows, finds, info) {
    var bad = function (id) { return rows[id] && rows[id].res === "不符合"; };
    var pol = ["P01", "P02", "P03", "P04", "P05", "P07", "P08", "P09", "P11", "P12"].filter(bad);
    var core = ["S01", "S02", "S03", "S05"].filter(bad);
    var must = finds.filter(function (f) { return f.lvl === "必改"; }).length;
    if (pol.length || (info.dup != null && info.dup >= 30) || core.length >= 2) return { v: "退回修改", why: (pol.length ? "政治性审查项不符合（" + pol.join("、") + "）；" : "") + (info.dup != null && info.dup >= 30 ? "重复率 " + info.dup + "% 超过30%；" : "") + (core.length >= 2 ? "核心模块缺失（" + core.join("、") + "）；" : "") };
    if (must) return { v: "修改后复审", why: "有必改问题 " + must + " 条" };
    return { v: "通过初审", why: "无必改问题；需作者确认与提请人工事项须在进入编辑加工前落实" };
  }
  function letterPrompt(o) {
    // o = { title, info, verdict, rows, finds, facts }
    var bySec = {};
    CHECK.forEach(function (c) { var r = o.rows[c[0]]; if (r && r.res === "不符合") (bySec[c[0][0]] = bySec[c[0][0]] || []).push("〔" + c[0] + "〕" + c[1] + "：" + clip(r.note, 100)); });
    var secTxt = CH.map(function (c) { return bySec[c[0]] ? c[1] + "\n" + bySec[c[0]].join("\n") : ""; }).filter(Boolean).join("\n\n");
    var must = o.finds.filter(function (f) { return f.lvl === "必改"; }).slice(0, 40).map(function (f) { return "〔" + f.id + "〕" + clip(f.pos, 20) + "｜" + clip(f.issue, 50); }).join("\n");
    var ask = o.finds.filter(function (f) { return f.lvl === "需作者确认"; }).slice(0, 25).map(function (f) { return "〔" + f.id + "〕" + clip(f.issue, 50); }).join("\n");
    var q = "【任务 · 来稿初审意见】你是出版社初审编辑，为教材来稿《" + o.title + "》写初审意见。初审结论已由规则定为「" + o.verdict.v + "」（依据：" + o.verdict.why + "），只能维持或从严，不得放宽。请写三部分，用这三个标题：\n一、总体评价（约400字：稿件的基本情况与长处；最主要的三到五个问题；为什么是这个结论）\n二、主要问题与修改要求（按「结构完整性／体例／内容／交互素材与资源」四类分条，每条写清问题、位置、怎么改；只写下面材料里有的，不编）\n三、致作者的修改说明（函件口吻，约500字：请作者按意见书第四、五部分逐条修改，补齐第八部分的材料，修改稿附修改说明表；返稿时间写〔待填〕）\n平常话，不用任何学派术语，不得说「符合出版要求」。\n\n【稿件概况】类型：" + (KIND_NAME[o.info.kind] || "未定") + "；体例：" + o.facts.form + "；字数约 " + fmtWan(o.facts.words ? o.facts.words.total : 0) + "\n\n【不符合的审查项】\n" + (secTxt || "（无）") + "\n\n【必改问题（节选）】\n" + (must || "（无）") + "\n\n【需作者确认（节选）】\n" + (ask || "（无）");
    return q.slice(0, 19800);
  }

  /* ═════════ 七、意见书 Word（真表格、宋体黑体、页码）═════════ */
  var D = null;
  function X(s) { return (D && D.esc ? D.esc : function (x) { return String(x).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); })(s); }
  var COLOR = { "符合": "1E7B34", "不符合": "C0392B", "需作者确认": "B9770E", "提请人工": "1F5FA8", "未检": "7F7F7F", "必改": "C0392B", "建议": "555555", "退回修改": "C0392B", "修改后复审": "B9770E", "通过初审": "1E7B34" };
  function run(t, o) {
    o = o || {};
    var rp = '<w:rPr><w:rFonts w:ascii="' + (o.hei ? "SimHei" : "Times New Roman") + '" w:hAnsi="' + (o.hei ? "SimHei" : "Times New Roman") + '" w:eastAsia="' + (o.hei ? "黑体" : "宋体") + '"/>' + (o.b ? "<w:b/>" : "") + (o.color ? '<w:color w:val="' + o.color + '"/>' : "") + '<w:sz w:val="' + (o.sz || 21) + '"/><w:szCs w:val="' + (o.sz || 21) + '"/></w:rPr>';
    return String(t == null ? "" : t).split("\n").map(function (seg, i) { return (i ? "<w:r><w:br/></w:r>" : "") + '<w:r>' + rp + '<w:t xml:space="preserve">' + X(seg) + '</w:t></w:r>'; }).join("");
  }
  function runsMd(t, o) {   // **粗体**
    var parts = String(t || "").split(/\*\*/), s = "";
    parts.forEach(function (p, i) { if (p) s += run(p, Object.assign({}, o, { b: (i % 2 === 1) || (o && o.b) })); });
    return s || run("", o);
  }
  function para(inner, o) {
    o = o || {};
    return '<w:p><w:pPr>' + (o.style ? '<w:pStyle w:val="' + o.style + '"/>' : "") + (o.keep ? "<w:keepNext/>" : "") + '<w:spacing w:before="' + (o.before || 0) + '" w:after="' + (o.after != null ? o.after : 80) + '" w:line="' + (o.line || 340) + '" w:lineRule="auto"/>' + (o.ind ? '<w:ind w:firstLine="420"/>' : "") + (o.left ? '<w:ind w:left="' + o.left + '" w:hanging="' + (o.hang || 0) + '"/>' : "") + (o.jc ? '<w:jc w:val="' + o.jc + '"/>' : "") + '</w:pPr>' + inner + '</w:p>';
  }
  function H1(t) { return para(run(t, { hei: 1, sz: 30, b: 1 }), { style: "Heading1", before: 360, after: 160, keep: 1 }); }
  function H2(t) { return para(run(t, { hei: 1, sz: 26, b: 1 }), { style: "Heading2", before: 240, after: 120, keep: 1 }); }
  function H3(t) { return para(run(t, { hei: 1, sz: 22, b: 1 }), { style: "Heading3", before: 160, after: 80, keep: 1 }); }
  function P(t, o) { return para(runsMd(t, o), { ind: !(o && o.noind), after: 80 }); }
  function LI(t) { return para(run("·  ", {}) + runsMd(t, {}), { left: 420, hang: 210, after: 40 }); }
  function cell(t, w, o) {
    o = o || {};
    return '<w:tc><w:tcPr><w:tcW w:w="' + w + '" w:type="dxa"/>' + (o.fill ? '<w:shd w:val="clear" w:color="auto" w:fill="' + o.fill + '"/>' : "") + '<w:vAlign w:val="center"/></w:tcPr>' + para(runsMd(t, { sz: o.sz || 18, b: o.b, hei: o.hei, color: o.color }), { line: 280, after: 0, jc: o.jc }) + '</w:tc>';
  }
  function table(head, rows2, widths, o) {
    o = o || {};
    var bd = '<w:tblBorders>' + ["top", "left", "bottom", "right", "insideH", "insideV"].map(function (k) { return '<w:' + k + ' w:val="single" w:sz="4" w:space="0" w:color="8C8C8C"/>'; }).join("") + '</w:tblBorders>';
    var s = '<w:tbl><w:tblPr><w:tblW w:w="' + widths.reduce(function (a, b) { return a + b; }, 0) + '" w:type="dxa"/>' + bd + '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>' + widths.map(function (x) { return '<w:gridCol w:w="' + x + '"/>'; }).join("") + '</w:tblGrid>';
    if (head) s += '<w:tr><w:trPr><w:tblHeader/></w:trPr>' + head.map(function (h, i) { return cell(h, widths[i], { fill: "E8E2D0", b: 1, hei: 1, jc: "center" }); }).join("") + '</w:tr>';
    rows2.forEach(function (r) {
      s += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + r.map(function (c, i) {
        var t2 = typeof c === "object" && c ? c.t : c, col = (o.colorCol === i && COLOR[t2]) ? COLOR[t2] : (typeof c === "object" && c && c.color) || "";
        return cell(t2, widths[i], { color: col, b: !!col && o.colorCol === i, jc: (o.center || []).indexOf(i) >= 0 ? "center" : null, fill: typeof c === "object" && c && c.fill });
      }).join("") + '</w:tr>';
    });
    return s + '</w:tbl>' + para("", { after: 60 });
  }
  // 模型写的 Markdown（含表格）→ 段落
  function mdBlocks(md) {
    var out = "", ls = String(md || "").replace(/\r/g, "").split("\n"), i = 0;
    while (i < ls.length) {
      var t = ls[i].trim();
      if (/^\|.*\|\s*$/.test(t) && i + 1 < ls.length && /^\|?\s*:?-{2,}/.test(ls[i + 1].trim())) {
        var hd = t.replace(/^\||\|$/g, "").split("|").map(function (x) { return x.trim(); }); i += 2;
        var rr = [];
        while (i < ls.length && /^\|.*\|\s*$/.test(ls[i].trim())) { rr.push(ls[i].trim().replace(/^\||\|$/g, "").split("|").map(function (x) { return x.trim(); })); i++; }
        var W = 9000, n = hd.length, ws = hd.map(function () { return Math.floor(W / n); });
        out += table(hd, rr.map(function (r) { while (r.length < n) r.push(""); return r.slice(0, n); }), ws);
        continue;
      }
      if (!t || /^-{3,}$/.test(t)) { i++; continue; }
      var m = /^(#{1,4})\s+(.*)$/.exec(t);
      if (m) { out += (m[1].length <= 2 ? H3(m[2].replace(/\*\*/g, "")) : H3(m[2].replace(/\*\*/g, ""))); i++; continue; }
      if (/^[一二三四五六七八九十]+、/.test(t) && t.length < 40) { out += H3(t.replace(/\*\*/g, "")); i++; continue; }
      if (/^[-*·]\s+/.test(t)) { out += LI(t.replace(/^[-*·]\s+/, "")); i++; continue; }
      if (/^>\s?/.test(t)) { out += P(t.replace(/^>\s?/, ""), { noind: 1 }); i++; continue; }
      out += P(t); i++;
    }
    return out;
  }
  // 意见三部分按标题关键词切（不按「一、二、三、」——第二部分里本身就有「一、结构完整性」这类小标题）
  var SEC_KEYS = [/总体评价/, /主要问题与修改要求|主要问题/, /致作者/];
  function secOf(md, n) {
    var ls = String(md || "").replace(/\r/g, "").split("\n"), at = [];
    SEC_KEYS.forEach(function (re, k) {
      for (var i = 0; i < ls.length; i++) { var t = ls[i].replace(/[#*\s]/g, ""); if (t.length <= 24 && re.test(t) && /^([一二三四][、.．])?/.test(t)) { at[k] = i; break; } }
    });
    if (at[n] == null) return n === 0 && at[1] == null && at[2] == null ? String(md || "") : "";
    var end = ls.length; at.forEach(function (x) { if (x != null && x > at[n] && x < end) end = x; });
    return ls.slice(at[n] + 1, end).join("\n").trim();
  }

  function buildDocx(R) {
    // R = { title, info, base, date, mc, rows(final), finds, units:[{name, judge, issues}], letter, verdict, unitsDone, unitsTotal, files }
    D = w.SDEDocx;
    if (!D || !D.zip) throw new Error("Word 组件尚未载入");
    var b = "", I = R.info || {}, F = R.mc.facts || {}, rows = R.rows;
    b += para(run("《" + R.title + "》", { hei: 1, sz: 36, b: 1 }), { jc: "center", before: 200, after: 60 });
    b += para(run("来稿初审意见书", { hei: 1, sz: 32, b: 1 }), { jc: "center", after: 240 });
    var cnt = { 符合: 0, 不符合: 0, 需作者确认: 0, 提请人工: 0, 未检: 0 };
    CHECK.forEach(function (c) { var r = rows[c[0]]; cnt[r ? r.res : "未检"]++; });
    var must = R.finds.filter(function (f) { return f.lvl === "必改"; }), sug = R.finds.filter(function (f) { return f.lvl === "建议"; }), ask = R.finds.filter(function (f) { return f.lvl === "需作者确认"; }), hum = R.finds.filter(function (f) { return f.lvl === "提请人工"; });
    b += table(null, [
      [{ t: "书名", fill: "F3EFE4" }, "《" + R.title + "》", { t: "主编／作者", fill: "F3EFE4" }, I.editor || "〔待填〕"],
      [{ t: "稿件类型", fill: "F3EFE4" }, (KIND_NAME[I.kind] || "〔待填〕") + (I.kindGuess ? "（推断）" : "") + (I.digital ? " · 数字教材" : ""), { t: "体例形式", fill: "F3EFE4" }, F.form || "—"],
      [{ t: "送审材料", fill: "F3EFE4" }, R.files || "—", { t: "字数（估算）", fill: "F3EFE4" }, F.words ? fmtWan(F.words.total) : "—"],
      [{ t: "审读范围", fill: "F3EFE4" }, "逐单元审读 " + R.unitsDone + "/" + R.unitsTotal + "；机检全稿", { t: "初审日期", fill: "F3EFE4" }, R.date],
      [{ t: "初审结论", fill: "F3EFE4" }, { t: R.verdict.v, color: COLOR[R.verdict.v] }, { t: "审查项", fill: "F3EFE4" }, CHECK.length + " 项：符合 " + cnt["符合"] + "，不符合 " + cnt["不符合"] + "，需作者确认 " + cnt["需作者确认"] + "，提请人工 " + cnt["提请人工"] + "，未检 " + cnt["未检"]]
    ], [1300, 3300, 1300, 3100]);
    b += para(run("问题统计：必改 " + must.length + " 条，建议 " + sug.length + " 条，需作者确认 " + ask.length + " 条，提请人工 " + hum.length + " 条。", { sz: 20 }), { after: 120 });

    b += H1("一、初审结论与总体评价");
    b += P("**初审结论：" + R.verdict.v + "。**依据：" + R.verdict.why);
    if (R.unitsDone < R.unitsTotal) b += P("**说明：**本意见书生成时逐单元审读完成 " + R.unitsDone + "/" + R.unitsTotal + "，其余单元只做了机检，结论待全部审读后更新。");
    b += mdBlocks(secOf(R.letter, 0) || "（总体评价待生成：完成审读后点「生成意见书」。）");

    b += H1("二、逐项审查结果");
    b += P("按《来稿初审指导书》逐条核查，共 " + CHECK.length + " 项。结论分五种：符合、不符合、需作者确认、提请人工（机器无法判断，须编辑人工核查）、未检（并注明原因）。「方式」一栏：机检＝程序全稿检查，审读＝逐单元阅读后判断，人工＝须编辑亲自过目。", { noind: 0 });
    CH.forEach(function (c) {
      var items = CHECK.filter(function (x) { return x[0][0] === c[0]; });
      b += H3(c[1]);
      b += table(["编号", "审查项", "要求", "方式", "结论", "说明与位置"], items.map(function (x) {
        var r = rows[x[0]] || { res: "未检", note: "（无结论）" };
        return [x[0], x[1], x[2], { code: "机检", model: "审读", mix: "机检＋审读", human: "人工" }[x[3]], r.res, r.note];
      }), [560, 1450, 2250, 760, 900, 3080], { colorCol: 4, center: [0, 3, 4] });
    });

    b += H1("三、主要问题与修改要求");
    b += mdBlocks(secOf(R.letter, 1) || "（待生成）");

    function ftable(list, cap) {
      if (!list.length) return P("无。");
      var shown = list.slice(0, cap);
      var s = table(["序号", "审查项", "位置", "原文", "问题", "修改建议", "来源"], shown.map(function (f, i) { return [String(i + 1), f.id + " " + (BY[f.id] ? BY[f.id].name : ""), f.pos, f.src, f.issue, f.fix, f.by]; }), [500, 1300, 1250, 1700, 1800, 1850, 600], { center: [0, 6] });
      if (list.length > cap) s += P("（另有 " + (list.length - cap) + " 条同类问题，见附录二逐单元记录。）");
      return s;
    }
    b += H1("四、必改问题清单");
    b += P("下列问题须在返稿前全部修改。");
    b += ftable(must, 400);
    b += H1("五、建议修改清单");
    b += ftable(sug, 300);
    b += H1("六、提请人工复核事项");
    b += P("下列事项涉及政治性、意识形态、图片画面、领导人讲话原文、国家政策口径等，机器无法下结论，须责任编辑逐条核查。");
    b += ftable(hum, 300);

    b += H1("七、字数与资源核算");
    var Wd = F.words || {};
    b += table(["项目", "数量", "折算字数", "说明"], [
      ["正文", fmtWan(Wd.chars || 0), fmtWan(Wd.chars || 0), "不含空格的字符数；其中汉字 " + fmtWan(Wd.han || 0)],
      ["图片", (Wd.imgN || 0) + " 幅", fmtWan(Wd.imgEq || 0), "每幅约1/3面 × 每面 " + (Wd.perPage || 1400) + " 字 × 系数 " + (Wd.coef || 0.5) + "（艺术类0.2、计算机类0.5、机械建筑电气类0.8）"],
      ["气泡、交互习题", (Wd.bubbles || 0) + " 个／约 " + (Wd.exN || 0) + " 条", fmtWan(Wd.interEq || 0), I.digital ? "统一按100字/个（条）" : "非数字教材，不计"],
      ["附件", (Wd.attLines || []).length + " 件", fmtWan(Wd.attW || 0), (Wd.attLines || []).join("；") || "无"],
      [{ t: "合计（估算）", fill: "F3EFE4" }, "", { t: fmtWan(Wd.total || 0), fill: "F3EFE4" }, "以排版后「行数×列数×面数×系数」核算为准；要求：" + (KIND_WORDS[I.kind] ? fmtWan(KIND_WORDS[I.kind]) : "职教35万、本科理工50万、文管45万、专著20万")]
    ], [1600, 1500, 1400, 4500], { center: [1, 2] });
    var resRows = (R.res || []).map(function (r) { return [r.name, r.ext.toUpperCase(), mb(r.size || 0), (r.codec || "—") + (r.w ? " " + r.w + "×" + r.h : ""), r.dur ? Math.floor(r.dur / 60) + "分" + (r.dur % 60) + "秒" : (r.slides ? r.slides + " 页" : "—"), r.typed ? "输入框登记" : "随稿文件"]; });
    if (resRows.length) b += table(["资源文件", "格式", "大小", "编码／画面", "时长／页数", "来源"], resRows, [2800, 800, 1100, 1700, 1300, 1300], { center: [1, 2, 4, 5] });
    else b += P("未随稿提供音视频、课件等资源文件。");

    b += H1("八、需作者补充提交的材料");
    var needs = [];
    if (rows.C01 && rows.C01.res !== "符合") needs.push("查重报告（重复率须低于30%；降重后返稿附新报告）");
    if (rows.C03 && rows.C03.res === "需作者确认") needs.push("校企合作案例、企业技术资料的企业书面授权");
    if (rows.C06 && rows.C06.res !== "符合") needs.push("图片来源与授权说明（摄影作品、设计作品、人物相片；含肖像权）");
    if (rows.C07 && rows.C07.res === "需作者确认") needs.push("音视频版权说明");
    if (rows.F06 && rows.F06.res === "需作者确认") needs.push("复杂线条图的 CAD 等可编辑源文件");
    if (rows.F05 && rows.F05.res === "不符合") needs.push("低分辨率图片的高清原图（不低于1280×720）");
    if (rows.F07 && rows.F07.res !== "符合") needs.push("AI 生成图片的说明与来源标注");
    if (rows.R04 && rows.R04.res === "不符合") needs.push("选择、填空、判断、排序、配对题的答案");
    if (rows.K03 && rows.K03.res !== "符合") needs.push("编写分工名单（与版权页一致、与章节对应）");
    if (rows.K01 && rows.K01.res !== "符合") needs.push("选题信息（书名、主编）以便核对");
    if (rows.S10 && rows.S10.res === "不符合") needs.push("正文提及的附录、附件");
    if (rows.K09 && rows.K09.res === "需作者确认") needs.push("所引标准的现行状态核对结果（工标网）");
    if (rows.K08 && rows.K08.res === "需作者确认") needs.push("旧数据的更新与权威来源");
    if (F.revNote) needs.push("清稿：" + F.revNote);
    needs.push("修改说明表（逐条对应本意见书第四、五部分的修改情况）");
    needs.forEach(function (n) { b += LI(n); });
    if (ask.length) { b += H3("需作者确认的具体事项"); b += ftable(ask, 200); }

    b += H1("九、致作者的修改说明");
    b += mdBlocks(secOf(R.letter, 2) || "（待生成）");

    b += H1("附录一  机检明细");
    (R.mc.detail || []).forEach(function (d) { b += P(d, { noind: 1 }); });
    if (F.matrix && F.matrix.length) {
      b += H3("各" + (R.mc.top || "章") + "栏目设置");
      b += table([R.mc.top || "章", "引导性", "总结性", "扩展性", "考核性", "三维目标", "思政"], F.matrix.map(function (r) { var y = function (v) { return v ? "有" : "—"; }; return [clip(r.name, 22), y(r.g), y(r.s), y(r.x), y(r.e), (r.kn ? "知" : "") + (r.ab ? "能" : "") + (r.li ? "素" : "") || "—", y(r.sz)]; }), [2900, 950, 950, 950, 950, 1150, 1150], { center: [1, 2, 3, 4, 5, 6] });
    }
    b += H1("附录二  逐单元审读记录");
    (R.units || []).forEach(function (u, i) {
      if (!u.judge && !(u.issues && u.issues.length)) return;
      b += H3("第 " + (i + 1) + " 单元 · " + clip(u.name, 30));
      if (u.judge) u.judge.split("\n").filter(Boolean).forEach(function (l) { b += P(l.replace(/^[-*·]\s*/, ""), { noind: 1 }); });
      if (u.issues && u.issues.length) b += table(["审查项", "位置", "原文", "问题", "建议", "级别"], u.issues.map(function (f) { return [f.id, f.pos, f.src, f.issue, f.fix, f.lvl]; }), [700, 1300, 1900, 2200, 2100, 800], { center: [0, 5] });
    });
    b += H1("声明");
    b += P("本意见书由 ChatSDE「来稿初审」智能体依据《来稿初审指导书》生成（基底：" + R.base + "），供出版社初审参考。机检数字由程序计算；审读结论由人工智能基底逐单元阅读得出，可能有漏判、误判。政治性与意识形态把关、图片与音视频画面、事实与引文的最终核定，须由责任编辑和出版单位完成。本意见书不构成「符合出版要求」的结论。");

    var docXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>' + b +
      '<w:sectPr><w:footerReference w:type="default" r:id="rIdF1"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1300" w:right="1200" w:bottom="1300" w:left="1200" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>';
    var styles = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="80" w:line="340" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>' +
      '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>' +
      [1, 2, 3].map(function (n) { return '<w:style w:type="paragraph" w:styleId="Heading' + n + '"><w:name w:val="heading ' + n + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="' + (n - 1) + '"/></w:pPr><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/></w:rPr></w:style>'; }).join("") +
      '<w:style w:type="paragraph" w:styleId="Footer"><w:name w:val="footer"/><w:basedOn w:val="Normal"/></w:style></w:styles>';
    var footer = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="center"/></w:pPr>' + run("《" + R.title + "》来稿初审意见书　第 ", { sz: 18 }) + '<w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>1</w:t></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>' + run(" 页", { sz: 18 }) + '</w:p></w:ftr>';
    var ct = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>';
    var rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>';
    var drels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdS1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rIdF1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>';
    var core = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>' + X("《" + R.title + "》来稿初审意见书") + '</dc:title><dc:creator>ChatSDE · 来稿初审</dc:creator></cp:coreProperties>';
    var enc = new TextEncoder();
    var u8 = D.zip([
      { name: "[Content_Types].xml", data: enc.encode(ct) },
      { name: "_rels/.rels", data: enc.encode(rels) },
      { name: "docProps/core.xml", data: enc.encode(core) },
      { name: "word/document.xml", data: enc.encode(docXml) },
      { name: "word/styles.xml", data: enc.encode(styles) },
      { name: "word/footer1.xml", data: enc.encode(footer) },
      { name: "word/_rels/document.xml.rels", data: enc.encode(drels) }
    ]);
    return new Blob([u8], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
  }

  // 合并：机检行＋审读逐项结论 → 最终逐项结论（机检的「不符合」不许被改判为符合）
  function mergeRows(mcRows, itemRows, finds) {
    var out = {};
    CHECK.forEach(function (c) {
      var id = c[0], m = mcRows[id], it = itemRows && itemRows[id];
      if (c[3] === "model") out[id] = it ? { res: it.res, note: it.note } : { res: "未检", note: "审读尚未给出结论（未完成审读或基底漏答），请人工复核" };
      else if (c[3] === "mix") {
        // 机检与审读取严的那一个（未检最轻：一方查过就以查过的为准）
        var RK = { "未检": -1, "符合": 0, "需作者确认": 1, "提请人工": 2, "不符合": 3 };
        if (!it) out[id] = m || { res: "未检", note: "审读尚未给出结论" };
        else if (!m) out[id] = { res: it.res, note: "审读：" + it.note };
        else out[id] = { res: RK[m.res] >= RK[it.res] ? m.res : it.res, note: m.note + "；审读：" + it.note };
      } else out[id] = m || { res: "未检", note: "（无结论）" };
    });
    // 审读发现的问题反过来约束结论：有「必改」的项不能是符合；有「提请人工」的项不能是符合
    var by = {}; (finds || []).forEach(function (f) { if (f.by !== "审读") return; (by[f.id] = by[f.id] || { m: 0, h: 0, a: 0 }); if (f.lvl === "必改") by[f.id].m++; else if (f.lvl === "提请人工") by[f.id].h++; else if (f.lvl === "需作者确认") by[f.id].a++; });
    Object.keys(by).forEach(function (id) {
      var r = out[id]; if (!r) return; var c = by[id];
      if (c.m && (r.res === "符合" || r.res === "需作者确认" || r.res === "未检")) out[id] = { res: "不符合", note: r.note + "；审读发现必改问题 " + c.m + " 条（见第四部分）" };
      else if (c.h && (r.res === "符合" || r.res === "未检")) out[id] = { res: "提请人工", note: r.note + "；审读提请人工 " + c.h + " 条（见第六部分）" };
      else if (c.a && r.res === "符合") out[id] = { res: "需作者确认", note: r.note + "；审读需作者确认 " + c.a + " 条" };
    });
    return out;
  }

  w.SDEIntake = {
    CHECK: CHECK, CH: CH, BY: BY, MODEL_IDS: MODEL_IDS, KIND_NAME: KIND_NAME,
    parseInfo: parseInfo, machine: machine, unitPrompt: unitPrompt, parseUnit: parseUnit,
    itemsPrompt: itemsPrompt, parseItems: parseItems, mergeRows: mergeRows, verdictOf: verdictOf,
    letterPrompt: letterPrompt, buildDocx: buildDocx, fmtWan: fmtWan, _cnNum: cnNum
  };
})(typeof window !== "undefined" ? window : globalThis);
