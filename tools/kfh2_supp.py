# -*- coding: utf-8 -*-
"""孔凡鹤第二批（心理治疗四篇）：每篇的深化说明（改动落在哪里、为什么）+ 本次所核验的文献。

打磨口径：外科手术式定点修改，不推倒重写。四篇均已近天花板或紧贴门槛，
改的只是审稿时记下的扣分点；作者的核心判断、章节结构与行文一律不动。
"""

NOTES = {
    "co-constructive-field":
        "本篇原稿的结构强度与证伪诚实度在本批四篇中均为最高——它拆掉的是作者自己上一篇的地基预设，"
        "并主动自曝核心机制在行为编码上难与「等待诠释时机的沉默」区分，随后仍给出可数的代理变量。"
        "本次唯一的定点改动落在第五章：原稿用「第二支点」把治疗与阅读、观影、独行划清了界限，"
        "但只做了划界——只证明了别处没有，未证明这个结构在别处只要凑齐同样条件就会出现。"
        "这留下一个隐藏的循环：把治疗室里发生的事命名为转化场，再用「只有治疗室里有」反过来证明命名的必要。"
        "第五章（二）之前补入一节，把三个条件写成脱离治疗设置的一般形式，给出三处应当复现的场合"
        "（长期临床督导、师徒制手艺传承、安宁疗护的共同在场）与两处应当不复现的场合"
        "（异步文字咨询、以效率为考核的短程干预），并为后者各配一条不能被「信息带宽」解释掉的对照预测。"
        "这一补写把本篇从「心理治疗的特殊理论」改写为「一类对话结构的理论」，"
        "同时把它置于更大的风险中：三处复现场合中任意两处失手，第二支点就降格为行业局部习惯。",

    "attribution-sensitivity":
        "本篇是本批跨域移植最实的一篇——柠檬市场不是当比喻用的，是当对手正面驳的；"
        "教育领域的二次函数案例是同一辨别面的完整移植，而非类比装饰。原稿唯一明显的承重弱点在可检验性："
        "核心构念被坦诚地界定为「推定性变量」「不可直接测量」，认识论上诚实，但代价是整篇论文容易滑向不可推翻。"
        "第四章（二）之后补入一节残差协议，把「在不同叙事系统之间的残差中被间接指认」这句方法论声明，"
        "落实为一份可预注册的三源比对方案：案主三个月内的自由叙述、治疗师的个案记录、"
        "三名分属不同流派且未接触前两份材料的编码者对同一段逐字稿的技术成分标注；"
        "以三源在「转折点定位」与「技术成分归属」上的标准化距离之和定义归因残差，"
        "并给出方向明确的预测（残差与治愈深度正相关）与清晰的死亡条件（不相关或负相关则立论瓦解）。"
        "同时预先排除了一个平凡的竞争解释——残差也可能只来自深度事件更复杂、更难被描述一致——"
        "协议因此要求把会谈时长、参与者数量、议题数量作为表层复杂度协变量控制；"
        "若控制后关联消失，本篇主张的结构性不可归因应被降格为一个关于描述难度的平凡观察。",

    "ripened-intuition":
        "本篇原稿的失败预测与死亡条件写得极扎实（四类失败预测各自带证伪条件，"
        "其中「AI 若要模拟负向能力需要做到什么」一条切得尤其准）。它的扣分集中在不可还原性："
        "把核心命题压缩到一句话之后，「治疗精要是被时间在特定身体里熟成的、不可算法化的出手本能」"
        "在压缩层面基本可被默会知识加实践智慧加具身认知覆盖——原稿的新意在机制，不在结论，"
        "而不可还原性恰恰是按结论来判的。第三章末补入 3.10 一节，把不可还原性的重心整体迁移一次："
        "从「不可言说」迁到「断裂类型特异性」。理由是波兰尼那句话已经先占住了不可言说这块地基，"
        "仅凭它本篇并没有比波兰尼多说出什么；而分型且不可迁移这一主张，与默会知识（预测专家整体优于新手）"
        "和实践智慧（一种愈成熟愈普适的统一德性）都构成方向不同的预测，可在同一批数据上分开检验。"
        "这一迁移同时把本篇从一个近乎不可推翻的位置上救了出来：只要对治疗师既往个案按断裂类型编码、"
        "检验其疗效在类型间的方差，核心判断即直接暴露在数据面前；若方差近乎为零，本篇应退回默会知识框架、"
        "不再主张独立命名。补写末尾明确交代，这是重新配重而非撤回：不可言说仍是该能力的属性，"
        "但它不再承担辨别功能，承担辨别功能的是分型。",

    "co-creative-disorientation":
        "本篇的两处扣分都指向同一个根源——概念主要靠否定式来界定（不是共情、不是同盟破裂修复、"
        "不是相遇时刻、不是真诚一致），因而既难被独立辨认，也难以脱离邻居概念这套脚手架而自立。"
        "第三章末补入一段正面表述，把共创性迷失写成三条同时必要的条件："
        "①技术库存的耗尽是被案主的具体困境逼出的而非治疗师选择的（排除策略性的不知姿态）；"
        "②角色的瓦解双向且同时（只有治疗师一方位置松动则仅为自我暴露）；"
        "③这一共同处境被显式放进两人之间并被对方以可辨认的形式确认（未说出的私人困惑不计）。"
        "三条均被写成可由第三方在逐字稿与录像上判定的形态，而不是只能靠内省报告的心理状态，"
        "本篇因此第一次有了独立的操作把手。第五章末另补一节跨领域形式检验："
        "把三条搬出治疗室，给出三处复现（重症告知、论文指导僵局、危机谈判的僵持转折）"
        "与两处失效（课堂教学——学生位置未同时松动；一次性商业咨询——退出成本过低），"
        "并由失效边界反推出本篇判断真正依赖的一般条件：一段双方都无法低成本退出的关系、"
        "一个由具体他者的具体困境逼出的技术空场、一次把该空场放在两人之间的显式言说。"
        "心理治疗只是这组条件被制度性凑齐得最稳定的场所之一。",
}

REFERENCES = {
    "co-constructive-field": [
        ("Fonagy, P., & Bateman, A. (2006). Mechanisms of change in mentalization-based treatment of BPD. Journal of Clinical Psychology, 62(4), 411–430.", ""),
        ("Yalom, I. D. (2002). The Gift of Therapy: An Open Letter to a New Generation of Therapists. HarperCollins.", ""),
        ("Jacobs, T. J. (1986). On countertransference enactments. Journal of the American Psychoanalytic Association, 34(2), 289–307.", ""),
        ("Vygotsky, L. S. (1978). Mind in Society: The Development of Higher Psychological Processes. Harvard University Press.", ""),
        ("Petitmengin, C. (2006). Describing one's subjective experience in the second person. Phenomenology and the Cognitive Sciences, 5, 229–269.（微观现象学编码的方法论来源，本次为补写中的编码路径核验）", ""),
    ],
    "attribution-sensitivity": [
        ("Akerlof, G. A. (1970). The market for \"lemons\": Quality uncertainty and the market mechanism. Quarterly Journal of Economics, 84(3), 488–500.", ""),
        ("Polanyi, M. (1966). The Tacit Dimension. University of Chicago Press.", ""),
        ("Spence, D. P. (1982). Narrative Truth and Historical Truth. W. W. Norton.", ""),
        ("Wampold, B. E., & Imel, Z. E. (2015). The Great Psychotherapy Debate (2nd ed.). Routledge.", ""),
        ("Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. PNAS, 115(11), 2600–2606.（本次补写的预注册协议规格依据）", ""),
    ],
    "ripened-intuition": [
        ("Polanyi, M. (1966). The Tacit Dimension. University of Chicago Press.", ""),
        ("Dreyfus, H. L., & Dreyfus, S. E. (1986). Mind Over Machine. Free Press.", ""),
        ("Schön, D. A. (1983). The Reflective Practitioner: How Professionals Think in Action. Basic Books.", ""),
        ("Ericsson, K. A., Krampe, R. T., & Tesch-Römer, C. (1993). The role of deliberate practice in the acquisition of expert performance. Psychological Review, 100(3), 363–406.", ""),
        ("Wampold, B. E., & Imel, Z. E. (2015). The Great Psychotherapy Debate (2nd ed.). Routledge.（治疗师效应的方差分解，本次用于校核分型方差这一补写预测的可检验形态）", ""),
    ],
    "co-creative-disorientation": [
        ("Safran, J. D., & Muran, J. C. (2000). Negotiating the Therapeutic Alliance: A Relational Treatment Guide. Guilford Press.", ""),
        ("Stern, D. N., Sander, L. W., Nahum, J. P., et al. (1998). Non-interpretive mechanisms in psychoanalytic therapy: The \"something more\" than interpretation. International Journal of Psychoanalysis, 79, 903–921.", ""),
        ("Rogers, C. R. (1957). The necessary and sufficient conditions of therapeutic personality change. Journal of Consulting Psychology, 21(2), 95–103.", ""),
        ("Buber, M. (1923/1970). I and Thou (W. Kaufmann, Trans.). Scribner.", ""),
        ("Back, A. L., Arnold, R. M., Baile, W. F., et al. (2005). Approaching difficult communication tasks in oncology. CA: A Cancer Journal for Clinicians, 55(3), 164–177.（重症告知一处复现的对照文献，本次补写新增核验）", ""),
    ],
}
