"""第 525 号《先到一步》（张琼 著，王德生 指导）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 582 号改写；版式照第 220、302 号。"""
NO = 525
SLUG = 'one-step-ahead'
TITLE = '先到一步'
SUBTITLE = '清晰、代理与被提前做完的发生'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'One Step Ahead: Clarity, Proxy, and the Experience Done in Advance'
EPIGRAPH = '同样是硬东西，落在亲历之后是骨骼，落在亲历之前是假体。'
AUTHOR = '张琼'
AUTHORS = ['张琼']
ADVISOR = '王德生'
CATEGORY = 'culture'
ISBN = '979-8-90690-611-3'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m525'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m525-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿三审时按出版令裁定',
            tier_reason='主张层为主（抢先的清晰、骨骼与假体、四条判据）；十六篇原论文各有证伪条件，全书三条证伪纲领均未真跑；部分引语、构造场景与统计数字待作者核对；写作与审校同一底座，无独立评审；WDS博士出版令明示排版上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（据张琼学员专栏十六篇论文，由 AI 协作熔铸）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、总论、编首语、十六章与结论），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
