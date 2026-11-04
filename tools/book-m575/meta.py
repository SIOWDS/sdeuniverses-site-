"""第 575 号《好心为什么会作恶？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 549、574 号改写；版式照第 220、302 号。"""
NO = 575
SLUG = 'why-kindness-does-harm'
TITLE = '好心为什么会作恶？'
SUBTITLE = '两条黄金定律怎样从善变成恶'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Why Does Kindness Do Harm? How the Two Golden Rules Turn from Good to Evil'
EPIGRAPH = '善恶是相对于意义的设定的：创造，自由，幸福。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-594-9'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m575'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m575-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（总式、定义域、翻转案例、推翻条件、构想场景），无真跑数据；WDS博士出版令明示三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-04')


def body_han(here=None):
    """正文汉字数（前言、导读、五十二章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
