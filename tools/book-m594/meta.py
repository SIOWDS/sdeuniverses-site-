"""第 594 号《HR的SDE解构入门》（王德生、贝芳 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 594 号改写；版式照第 220、302 号。"""
NO = 594
SLUG = 'hr-sde-deconstruction'
TITLE = 'HR的SDE解构入门'
SUBTITLE = '交账要秩序，接着是介生'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'An Introduction to Deconstructing HR with SDE'
EPIGRAPH = '交账要秩序，接着是介生。'
AUTHOR = '王德生　贝芳'
AUTHORS = ['王德生', '贝芳']
ADVISOR = ''
CATEGORY = 'business'
ISBN = '979-8-90690-622-9'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m594'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m594-unit-v1'
SRC = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='初稿', tier_set_reason='初稿，未评分',
            tier_reason='主张层为主，无真跑数据；〔待核〕标注约 180 处保留；未评分', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生立定义、贝芳访谈＋AI协作成稿）', rights='作者署名出版', tier_judge='未评分',
            tier_date='2026-11-05')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
