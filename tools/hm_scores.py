# -*- coding: utf-8 -*-
"""胡敏 69 篇独立作品的创新智商评分（2026-07-27）。

口径：五维加权 S.20 D.25 E.20 I.20 F.15，与胡志英同一把尺。
paper-p48-d01-a01《裂隙：指标复常之后的身体》与 clinical-cognitive-substitution
正文重合 54/59 段，是同一篇的早期版本，只对增补版计分，早期版本标注同篇关系。

这批的共性：几乎每篇都做「撤销一个未经审查的先验 → 命名新概念 → 与 4-6 个
敌意最近邻逐一勘界 → 给可排除竞争解释的证伪设计」，且相当数量的篇目带
「本文禁止什么」自限章节——这个动作在站上其他学员那里少见，是 S 与 I 的稳定加分项。
"""
DUP_EARLY = "paper-p48-d01-a01"          # 早期版本，不计分
DUP_CANON = "clinical-cognitive-substitution"

# slug: (S, D, E, I, F)
SCORES = {
    # ── 身体与慢病
    "felt-sense-sovereignty": (142, 142, 135, 136, 142),
    "body-time-sovereignty": (142, 145, 135, 136, 148),
    "paper-p48-d01-a03": (142, 145, 132, 138, 145),
    "paper-p48-d01-a04": (138, 138, 128, 129, 133),
    "paper-p48-d01-a02": (142, 145, 138, 138, 138),
    "paper-p46-d01-a03": (142, 148, 135, 138, 135),
    "paper-p46-d01-a02": (142, 145, 135, 138, 140),
    "paper-p46-d01-a04": (145, 145, 135, 138, 145),
    "bodily-self-disablement": (147, 148, 145, 145, 143),
    "self-care-paradox": (139, 139, 130, 131, 136),
    "recovery-to-adaptation": (139, 136, 130, 129, 136),
    "clinical-cognitive-substitution": (142, 142, 132, 134, 145),
    # ── 中医与技艺传承
    "paper-p47-d01-a03": (148, 154, 140, 148, 140),
    "paper-p47-d01-a04": (147, 152, 140, 146, 143),
    "paper-p47-d01-a02": (142, 148, 138, 140, 138),
    "resonance-of-pattern-change": (142, 148, 135, 138, 135),
    "experience-bifurcation": (142, 145, 138, 136, 140),
    # ── 抑郁与自我耗竭
    "sensory-narrowing": (142, 142, 135, 136, 138),
    "generative-void": (146, 150, 136, 142, 143),
    "hollowed-existence": (137, 138, 128, 128, 133),
    "psychic-ledger": (138, 140, 130, 130, 133),
    "downside-deprivation": (147, 151, 136, 142, 146),
    "silent-lock": (145, 145, 138, 140, 138),
    "dependency-vortex": (147, 152, 136, 146, 143),
    "recognition-coffin": (139, 141, 130, 132, 133),
    "scrutiny-devouring": (137, 137, 127, 127, 133),
    "genetic-borrowing": (142, 145, 138, 136, 138),
    "returned-fate": (136, 136, 127, 126, 134),
    # ── 婚姻与信仰
    "measurability-exit": (142, 148, 135, 138, 140),
    "preference-adaptation": (142, 142, 135, 134, 142),
    "value-non-accumulation": (148, 154, 140, 145, 138),
    "paradigm-presupposition": (137, 138, 130, 129, 135),
    "reflexive-interval": (142, 145, 135, 136, 138),
    "chastity-marginalization": (142, 145, 135, 136, 138),
    "engineering-shell": (142, 148, 138, 138, 138),
    "irreversible-afterimage": (142, 145, 140, 138, 142),
    "hollowing-steady-state": (137, 137, 130, 128, 135),
    "hollowing-morphology": (142, 148, 135, 136, 138),
    "paper-p41-d01-a01": (147, 151, 133, 144, 136),
    "paper-p41-d01-a04": (148, 155, 138, 148, 144),
    "paper-p41-d01-a02": (147, 152, 136, 144, 141),
    "paper-p41-d01-a03": (147, 153, 136, 144, 143),
    "paper-p39-d01-a04": (142, 145, 132, 136, 135),
    "paper-p39-d01-a01": (145, 145, 135, 140, 140),
    "paper-p39-d01-a03": (142, 145, 132, 136, 138),
    "paper-p39-d01-a02": (148, 156, 138, 148, 142),
    # ── 数字时代与主体性
    "destimulation-window": (142, 145, 135, 136, 142),
    "task-misclassification": (142, 145, 132, 136, 140),
    "niche-dependence": (142, 145, 132, 136, 140),
    "nothing-new-under-sun": (142, 145, 135, 136, 140),
    "substrate-dissipation": (142, 142, 135, 134, 145),
    "paper-p49-d01-a02": (148, 155, 142, 146, 138),
    "paper-p49-d01-a04": (148, 154, 138, 148, 140),
    "paper-p49-d01-a03": (146, 150, 142, 142, 136),
    "paper-p49-d01-a01": (142, 145, 135, 138, 142),
    "self-spectacle": (145, 145, 135, 138, 142),
    # ── 文明与文化
    "neotenic-disqualification": (148, 152, 140, 146, 144),
    "developmental-preoccupation": (142, 148, 135, 138, 140),
    "dual-track-antagonism": (139, 141, 130, 132, 135),
    "internal-inspector": (145, 145, 135, 138, 142),
    "silencing-apparatus": (142, 145, 135, 136, 138),
    "host-migration": (142, 145, 135, 136, 142),
    # ── 发生学方法与蜕变
    "rupture-meaning-genesis": (142, 142, 145, 136, 140),
    "sovereignty-substrate": (147, 150, 139, 142, 141),
    "dissolution-of-time-lag": (145, 148, 138, 140, 138),
    "autophagic-nourishment": (148, 154, 136, 145, 136),
    "directionless-becoming": (147, 153, 133, 144, 138),
    "curiosity-substrate": (148, 152, 138, 145, 144),
    "genesis-of-touch": (136, 134, 128, 124, 128),
}

W = dict(S=0.20, D=0.25, E=0.20, I=0.20, F=0.15)


def total(slug):
    S, D, E, I, F = SCORES[slug]
    return S * W["S"] + D * W["D"] + E * W["E"] + I * W["I"] + F * W["F"]


def rounded(slug):
    return round(total(slug))
