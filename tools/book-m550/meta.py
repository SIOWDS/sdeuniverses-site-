"""第 550 号《听话论：真理的符合论》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 549 号改写；版式照第 220、302 号。"""
NO = 550
SLUG = 'listening-theory-truth-correspondence'
TITLE = '听话论'
SUBTITLE = '真理的符合论'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'The Theory of Obedience: A Genesis Account of the Correspondence Theory of Truth'
EPIGRAPH = '真，是一次发生再来得稳不稳；符合，是照着共同体的“真的发生”做一遍。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-552-9'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261101b'
DATE = '2026-11-01'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261101-m550-unit-v1'
SRC = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（命题、判据、推翻条件、构想场景），无真跑数据；王德生出版令明示三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-01')


def body_han(here=None):
    """正文汉字数（前言、十八章、结语与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
