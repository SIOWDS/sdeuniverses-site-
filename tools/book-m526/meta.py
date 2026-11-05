"""第 526 号《秩序独大》（胡志英 著，王德生 指导）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 582 号改写；版式照第 220、302 号。"""
NO = 526
SLUG = 'order-ascendant'
TITLE = '秩序独大'
SUBTITLE = '差异与关系为何进不来'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Order Ascendant: Why Difference and Relation Cannot Get In'
EPIGRAPH = '伤人的不是失序，是秩序独大：它越尽职，越把差异与关系关在门外，活物因此挨饿。'
AUTHOR = '胡志英'
AUTHORS = ['胡志英']
ADVISOR = '王德生'
CATEGORY = 'culture'
ISBN = '979-8-90690-612-0'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m526'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m526-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='三审统稿时按出版令裁定',
            tier_reason='主张层为主（秩序独大、进入能力、三处断点、承接四条件）；每章写有可观察的证伪条件，均未经执行；书中现场多为构造案例或典型化叙述，法感一章只用两份判决书；写作与审校同一底座，无独立评审；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（据胡志英学员专栏十五篇论文，由 AI 协作重写）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导论、编序、九章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
