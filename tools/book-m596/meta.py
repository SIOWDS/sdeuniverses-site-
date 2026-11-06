"""第 596 号《AI时代中华智慧的困境和出路》（王德生、胡志英 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 594 号改写；版式照第 220、302 号。2026-11-06 王德生令：完善、打磨、三审，三位一体重做上站（旧版站上杂乱，覆盖重做）。"""
NO = 596
SLUG = 'zhonghua-ai'
TITLE = 'AI时代中华智慧的困境和出路'
SUBTITLE = '从守中开花到持续生成新花种'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Predicament and the Way Out of Chinese Wisdom in the AI Era: From Keeping the Mean in Bloom to Continually Generating New Seeds'
EPIGRAPH = '守中而开花的智慧，如何获得持续生成新花种的能力？'
AUTHOR = '王德生　胡志英'
AUTHORS = ['王德生', '胡志英']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-624-3'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m596'
DATE = '2026-11-07'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261107-m596-unit-v2'
SRC = 'chapters/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='成稿', tier_set_reason='成稿，三审定稿，未评分',
            tier_reason='主张层为主；条件命题与待检验方案；三领域试点尚未实施；未评分', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生立题与口径、胡志英共同作者＋AI协作成稿）', rights='作者署名出版', tier_judge='未评分',
            tier_date='2026-11-07')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
