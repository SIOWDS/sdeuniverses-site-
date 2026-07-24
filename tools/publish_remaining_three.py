#!/usr/bin/env python3
"""Publish the three remaining 2026-07-24 submissions.

The source texts were already extracted from the submission packages.  This
script deliberately reuses the site's established long-form renderer so the
three-reading-mode contract stays identical to the rest of the site.
"""
from __future__ import annotations

import html
import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "tmp" / "global-iq-20260724"
BASE_PATH = ROOT / "tools" / "publish_global_over145_eleven.py"

spec = importlib.util.spec_from_file_location("over145", BASE_PATH)
base = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(base)
base.SOURCE = SOURCE

PAPERS = [
    dict(
        author="葡萄", student="putao", score=154, source="01",
        slug="gravitational-dialogue",
        kind="对话哲学与关系发生学",
        title="引力的形状：当一场对话不拆壳，只改变引力中心",
        hook="真正改变人的对话，未必靠拆掉旧信念，而可能靠建立一个更可信、更少控制欲的关系重心，使旧壳自行失去环绕价值。",
        evidence="理论建构论文。原始对话被作为机制生成材料，而非受控临床证据；“引力”是关系机制模型，不是物理量。",
    ),
    dict(
        author="葡萄", student="putao", score=152, source="02",
        slug="knowing-leaves-the-body",
        kind="具身认知与精神生活",
        title="当“知道”从身体里退出来：终极确信、速率差与知—身断连",
        hook="问题不总是“知道却不行动”：在高压的终极确信中，意识可能提前完成，身体却被留在原地，由此形成一种不可被意志力直接修复的知—身断连。",
        evidence="概念—解释型论文。诺斯替主义、禅门末流与海子均作比较性思想材料；涉及具体历史与生平的判断须由专门史料继续核验。",
    ),
    dict(
        author="王德生", channel="education", score=150, source="05",
        slug="inscriptive-anxiety",
        kind="AI时代家庭教育与关系本体论",
        title="焦虑的铭写：AI时代家长为何在未来失效后仍无法停止操心",
        hook="当教育行动不再可靠地兑换未来，操心可能从解决问题的手段变成维持亲职正当性的书写动作：不是为了抵达，而是为了证明自己仍在负责。",
        evidence="理论论文。文中家庭场景是基于既有研究构造的分析性类型，不是单一个案实录；“铭写性焦虑”不是临床诊断。",
    ),
]

EDITORIAL = {
    "gravitational-dialogue": """
<section class="compare"><h2>全球最近邻压力测试：它不是“治疗联盟”的诗意改名</h2>
<p>本稿最接近罗杰斯的治疗性在场、布伯的“我—你”、动机式访谈的非对抗改变，以及心理治疗研究中的治疗联盟。若“引力式对话”只表示温暖、共情或信任，它没有独立创新性。修订稿因此把独立变量收紧为：<strong>对话者不以对方改变来结算自身正确性，同时让一个可共同接触的现实重新取得组织经验的中心地位</strong>。这比“关系好所以有效”多出一个可观察的重心迁移过程。</p>
<h3>四项可观察指标</h3>
<ol><li>结果非依赖：对话者是否需要对方当场认同，才能维持稳定在场；</li><li>现实共指：双方是否转向一个可共同触碰、复查或行动的对象；</li><li>自主保留：接受者能否拒绝、离开或形成第三种答案；</li><li>跨场景持续：改变是否在对话者离场后仍能维持。</li></ol>
<h3>反例与证伪</h3>
<p>魅力型领袖同样能改变他人的“引力中心”，但会把现实共指替换为人格依附。若改变只在领袖在场时存在，或接受者的异议空间持续缩小，这不是引力式对话，而是魅力俘获。若控制“联盟质量”后，上述四项指标不能额外预测自主行动与跨场景持续性，则本模型应被治疗联盟理论吸收。</p></section>
""",
    "knowing-leaves-the-body": """
<section class="compare"><h2>概念硬化：从文学隐喻变成可竞争的机制</h2>
<p>“知—身断连”的全球最近邻包括认知失调、意向—行动缺口、离身认知、灵性逃避与具身认知。修订后的分界不是“想得多、做得少”，而是三项联合条件：<strong>终极确信提前封闭修正、意识完成速度显著快于身体学习、语言调用反过来免除身体核验</strong>。缺少任一条件，都不应使用这一概念。</p>
<h3>竞争性预测</h3>
<p>一般意向—行动缺口可被提醒、计划和环境助推改善；知—身断连则可能因增加教义信息和道德劝告而加重，因为新信息继续喂养已经过快的意识通道。更有效的干预应暂时降低宏大语言的调用频率，改用可感知、可重复、低解释负荷的微动作，让身体重新获得修正“知道”的权利。</p>
<h3>边界与伦理</h3>
<p>本文不把宗教确信、诗性表达或抽象思考本身病理化。只有当终极语言稳定地取消现实核验，并造成持续的行动失能时，断连判断才成立。若身体训练并不比认知干预更能恢复行动，或终极确信程度与断连指标无稳定关系，则“速率差”机制被削弱。</p></section>
""",
    "inscriptive-anxiety": """
<section class="compare"><h2>全球比较后的原创边界：从风险焦虑到“自我留痕”</h2>
<p>本稿与风险社会、密集母职、量化自我、数字育儿和平台黏性研究相邻。已有研究能够解释家长为何担心、为何比较、为何被数据平台持续召回；本文只对一个更窄的机制主张原创性：<strong>当未来不再提供稳定回报时，重复查看、收藏与规划仍可通过留下“我正在负责”的行动痕迹，短暂维持亲职主体感</strong>。焦虑的直接产物因此不是更好的决策，而是可被自己读取的责任证据。</p>
<h3>可检验的区分</h3>
<ol><li>结果保证实验：即使未来结果得到保证，部分家长仍保持刷新行为；</li><li>内容替换：一个教育问题解决后，操作迅速迁移到另一指标；</li><li>观众撤除：在无人评价、无人知晓时，重复操作仍持续；</li><li>关系替代：增加非绩效性的亲子共同活动，比增加确定性信息更能降低刷新频率。</li></ol>
<h3>证据纪律</h3>
<p>“铭写性焦虑”不能替代广泛性焦虑、强迫症或行为成瘾诊断。若刷新行为主要由明确的结果风险解释，或提供可靠信息即可持续终止行为，则风险焦虑模型更简约；若非绩效关系活动不能产生额外缓冲效应，则本文的关系本体论主张不成立。</p></section>
""",
}


def strengthen_page(paper):
    target = (ROOT / "public" / "students" / paper["student"] / paper["slug"]
              if paper.get("student") else ROOT / "public" / paper["channel"] / "ai-era" / paper["slug"])
    path = target / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace(f"{paper['author']} 著 · {base.DATE} ·",
                        f"{paper['author']} 著 · 发表于 {base.DATE} ·", 1)
    insert = EDITORIAL[paper["slug"]]
    text = text.replace("<nav class=\"toc\">", insert + "<nav class=\"toc\">", 1)
    path.write_text(text, encoding="utf-8")


def update_education():
    path = ROOT / "public" / "education" / "ai-era" / "index.html"
    text = path.read_text(encoding="utf-8")
    p = next(x for x in PAPERS if not x.get("student"))
    start = "<!-- REMAINING-THREE:START -->"
    end = "<!-- REMAINING-THREE:END -->"
    url = f'/education/ai-era/{p["slug"]}/'
    block = f"""{start}<div class="block"><div class="block-head"><span class="block-num">新</span><span class="block-title">王德生 · AI时代家庭教育新作</span></div>
<p class="block-desc">经全球最近邻比较、证据等级校正与深度改性的关系本体论论文。</p><div class="art-grid"><a class="art" href="{url}"><span class="k">最新发表 · SDE创新智商 {p['score']} · 三种阅读方式</span>
<h4>{html.escape(p['title'])}</h4><p>{html.escape(p['hook'])}</p><span class="rd">网页长文 · 在线PDF · 下载PDF →</span></a></div></div>{end}"""
    if start in text:
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), block, text, flags=re.S)
    else:
        text = text.replace('<div class="block">', block + '<div class="block">', 1)
    path.write_text(text, encoding="utf-8")


def main():
    base.PAPERS = PAPERS
    for paper in PAPERS:
        base.article_html(paper)
        strengthen_page(paper)
        print("PAGE", paper["author"], paper["score"], paper["slug"])
    base.update_students()
    update_education()
    print("GENERATED", len(PAPERS))


if __name__ == "__main__":
    main()
