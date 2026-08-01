#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扩充 /kb/placeholders.json：把另外三条真跑（《可预期的尺子》《代签》《没有人拒绝过你》）
敌意拓宽时查出的占位者补进库，并给既有卡加中文人名钩子。

为什么要加中文人名钩子：匹配走中文二元切分，候选是用中文写的 50 字压缩，
别名表里只有 Luhmann / Illich 这类英文名时，中文候选钩不出来。
"""
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "public", "kb", "placeholders.json")

NEW = [
 dict(id="radical-monopoly", p="一种工具或服务的普及，会取消人们自己动手做同一件事的必要性，从而在不禁止任何人的情况下消灭那项能力",
      a=["必要性被更便宜地满足","不经拒绝而消失","工具普及取消自为能力","根本性垄断","伊里奇","无需禁止的剥夺","radical monopoly"],
      o="Tools for Conviviality", au="Illich", y=1973, d="社会批判",
      h="占住「不经过拒绝的消失」：不是压抑也不是剥夺执行条件，而是必要性被替代品接管",
      s="未占：可能性 vs 必要性的区分；拒绝作为指纹唯一来源这一推论", v="核验"),
 dict(id="shifting-baselines", p="每一代人把自己入行时见到的状态当作正常基线，于是长期退化被逐代重述为常态，退化本身不被察觉",
      a=["基线偏移","逐代重设正常值","退化被重述为常态","后来者把区分读成程度差","波利","shifting baseline"],
      o="Anecdotes and the shifting baseline syndrome of fisheries", au="Pauly", y=1995, d="渔业生态学",
      h="占住「遗忘格」：区分消失后，后来者用程度差重述它",
      s="未占：长尾可被制度性场合人为拉长这一修正项", v="核验"),
 dict(id="intermediate-disturbance", p="多样性在中等强度的扰动下最高；扰动过少或过多都会使多样性下降",
      a=["中度干扰假说","扰动过少也有害","断供深度差","康奈尔","intermediate disturbance"],
      o="Diversity in tropical rain forests and coral reefs", au="Connell", y=1978, d="群落生态学",
      h="占住「适度中断有益」这一整族说法的量的版本",
      s="未占：断的是种类而非量这一区分", v="核验"),
 dict(id="disruptive-innovation", p="在位者按现有客户与利润池分配资源，因而系统性地看不见起初性能更差、后来颠覆市场的技术",
      a=["破坏性创新","在位者看不见","资源分配流程的盲区","克里斯坦森","disruptive innovation"],
      o="The Innovator's Dilemma", au="Christensen", y=1997, d="创新管理",
      h="占住「成功者的结构性失察」这一族的市场版本",
      s="未占：失察发生在必要性层而非需求层的情形", v="核验"),
 dict(id="generation-problem", p="社会变化不靠说服在世者完成，而靠新一代带着不同的成形经验进场、旧一代退场",
      a=["代际问题","靠换人不靠说服","成形经验决定视野","曼海姆","problem of generations"],
      o="Das Problem der Generationen", au="Mannheim", y=1928, d="知识社会学",
      h="占住「区分随人退场而消失」的社会学解释",
      s="未占：能力仍在而必要性已无这一格", v="核验"),
 dict(id="care-receiving-responsiveness", p="照料是一个四阶段过程，其最后一阶段是被照料者的回应；缺了这一阶段，照料在伦理上并未完成",
      a=["照料的回应阶段","被照料者的应答","照料未完成","特隆托","care-receiving","responsiveness"],
      o="Moral Boundaries: A Political Argument for an Ethic of Care", au="Tronto", y=1993, d="政治伦理学",
      h="占住「照料需要回音才算结清」这一条",
      s="未占：回音缺席在照料者身上的生理沉淀；由谁签回撤单", v="核验"),
 dict(id="mutual-recognition", p="承认必须是相互的：把对方当作独立主体而非自我的延伸，双方才都能成为主体",
      a=["相互承认","主体间承认","不把对方当延伸","本雅明","mutual recognition","intersubjectivity"],
      o="The Bonds of Love", au="Benjamin", y=1988, d="精神分析",
      h="占住「承认」这条路的全部正面表述",
      s="未占：被承认者被征用去为承认者签凭证这一反向结构", v="核验"),
 dict(id="parentification", p="家庭中子女被置于照料父母的位置，承担了不属于其发展阶段的结算责任，形成隐性的关系账本",
      a=["亲职化","子女被征用为照料者","隐性关系账本","关系伦理","博斯泽门伊-纳吉","parentification","invisible loyalties"],
      o="Invisible Loyalties", au="Boszormenyi-Nagy & Spark", y=1973, d="家庭治疗",
      h="占住「关系里的账与代人受过」这一族",
      s="未占：签单人被撤下后是否在 6–12 个月内出现新签单人", v="核验"),
 dict(id="gift-obligation", p="礼物制造回赠的义务；给予、接受、回报三重义务构成社会纽带的基本形式",
      a=["礼物之债","回赠义务","三重义务","莫斯","the gift","reciprocity"],
      o="Essai sur le don", au="Mauss", y=1925, d="人类学",
      h="占住「给予产生债」这一族的全部经典表述",
      s="未占：债由谁来结、结不掉时沉淀在哪一层", v="核验"),
 dict(id="rules-vs-standards", p="规则事前确定内容、标准事后确定内容；二者的取舍取决于制定成本与被规范者的预判成本如何分配",
      a=["规则与标准","事前确定还是事后确定","可预判性的成本分配","卡普洛","rules versus standards"],
      o="Rules versus Standards: An Economic Analysis", au="Kaplow", y=1992, d="法经济学",
      h="占住「判据在事前还是事后确定」这条轴",
      s="未占：可预期性与粗细/期限相互独立这一分离", v="核验"),
 dict(id="multitask-agency", p="当任务的多个维度中只有一部分可测量时，对可测部分的激励会系统性地把努力从不可测部分抽走",
      a=["多任务代理","可测部分吸走努力","激励扭曲配置","霍姆斯特罗姆","multitask principal-agent"],
      o="Multitask Principal-Agent Analyses", au="Holmström & Milgrom", y=1991, d="契约理论",
      h="占住「可测者挤出不可测者」这一族的形式化版本",
      s="未占：不必等任何一次测量发生即已收敛这一时序主张", v="核验"),
 dict(id="lottery-funding", p="科研资助中引入随机抽签，用以对冲同行评议的保守偏好与评审噪声",
      a=["抽签资助","随机分配经费","对冲评审保守","不可预期的判据","lottery funding","random allocation"],
      o="Ranking games / partial randomisation in research funding（HRC 2013、VW『实验！』2017、FWF、SNSF）",
      au="Osterloh & Frey 一脉·多家资助机构", y=2013, d="科研政策",
      h="占住「让判据不可预期」这一处方本身",
      s="未占：规则完全公开而结果仍不可预期（公开度与可预期性被分开）", v="核验"),
 dict(id="incentives-for-creativity", p="容忍早期失败、给予长期视野的合约，比按短期里程碑考核更能产出突破性研究",
      a=["容错激励","长周期合约出创新","赌人不赌题","曼索","incentives and creativity","tolerance for failure"],
      o="Incentives and Creativity: Evidence from the Academic Life Sciences（NBER w15466）",
      au="Azoulay, Graff Zivin & Manso", y=2011, d="劳动经济学",
      h="占住「期限与容错」这条解释路径",
      s="未占：判据到动作的距离（三个月能学会写申请书，三个月变不成另一个人）", v="核验"),
 dict(id="still-face", p="照料者突然停止面部回应时，婴儿在数十秒内出现试探、抗议与退缩的固定序列",
      a=["静脸实验","停止回应引发退缩","回音撤除的即时效应","特罗尼克","still face paradigm"],
      o="The infant's response to entrapment between contradictory messages in face-to-face interaction",
      au="Tronick et al.", y=1978, d="发展心理学",
      h="占住「回应撤除会立刻改变行为」这一实验范式",
      s="未占：成人版、以及撤除后由谁补签这一问", v="核验"),
 dict(id="ontological-insecurity", p="当一个人的自我感须靠他人的确认来维持时，他人的定义就成为他存在的条件而非描述",
      a=["存在性不安","靠他人确认维持自我","被定义即被安置","莱恩","ontological insecurity"],
      o="The Divided Self / Self and Others", au="Laing", y=1960, d="精神病学",
      h="占住「被说成什么样就成了什么样」这一族",
      s="未占：这份确认是签给照料者而非签给自己", v="核验"),
 dict(id="adaptive-data-analysis", p="对同一份数据反复提问，会使后续结论逐步过拟合；不可预期性随查询次数单调泄露",
      a=["自适应数据分析","反复查询导致泄露","不可预期性会被磨掉","更新率","adaptive data analysis","holdout reuse"],
      o="Preserving Statistical Validity in Adaptive Data Analysis", au="Dwork, Feldman, Hardt, Pitassi, Reingold & Roth", y=2015, d="机器学习",
      h="占住「不可预期性不能一次造好、会随互动泄露」这一条",
      s="未占：把处方从「造不可预期的判据」退成「控制更新率」这一步", v="核验"),
]

# 给既有卡补中文人名钩子（匹配走中文二元切分，纯英文名钩不出中文候选）
ZH = {
 "legibility-destroys-metis": ["斯科特", "可读性摧毁地方性知识"],
 "observer-blind-spot": ["卢曼", "观察者盲点", "划界者不能安置自己"],
 "fragility-revealed-by-stressor": ["塔勒布", "反脆弱"],
 "be-spontaneous-paradox": ["瓦茨拉维克", "我命令你自发"],
 "automation-deskill-mask": ["班布里奇", "自动化的反讽"],
 "control-variance-pathology": ["霍林", "梅菲", "命令与控制的病理"],
 "critical-slowing-down": ["谢弗", "临界慢化", "预警信号"],
 "goodharts-law": ["古德哈特", "坎贝尔", "指标一旦成为目标就不再是好指标"],
 "exit-voice-loyalty": ["赫希曼", "退出与呼吁"],
 "stability-breeds-instability": ["明斯基", "稳定孕育不稳定"],
 "hermeneutical-injustice": ["弗里克", "诠释性不正义"],
 "commons-self-governance": ["奥斯特罗姆", "公共池塘资源自治"],
 "learned-helplessness": ["塞利格曼", "习得性无助"],
 "tacit-knowing": ["波兰尼", "默会知识"],
 "participation-without-power": ["阿恩斯坦", "参与阶梯"],
 "normalization-of-deviance": ["沃恩", "偏差的正常化"],
}

def main():
    j = json.load(open(P, encoding="utf-8"))
    items = j["items"]
    have = {i["id"] for i in items}
    added = 0
    for c in NEW:
        if c["id"] in have:
            print("  跳过已有：", c["id"]); continue
        items.append(c); added += 1
    zh = 0
    for it in items:
        extra = ZH.get(it["id"])
        if not extra: continue
        for x in extra:
            if x not in it["a"]: it["a"].append(x); zh += 1
    j["items"] = items
    j["n"] = len(items)
    j["generated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    json.dump(j, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("新增卡 %d 张 → 共 %d 张；补中文钩子 %d 条" % (added, len(items), zh))

    # 校验：每张卡字段齐、别名非空、无重复 id
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "id 重复"
    for i in items:
        for k in ("id","p","a","o","au","d","h","s","v"):
            assert i.get(k), "字段缺失 %s in %s" % (k, i["id"])
        assert len(i["a"]) >= 3, "别名不足三条：" + i["id"]
    print("校验通过：%d 张卡，字段齐、别名≥3、id 唯一" % len(items))

if __name__ == "__main__":
    main()
