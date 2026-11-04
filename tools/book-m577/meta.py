"""第 577 号《庄子的艺术智慧》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 575 号改写；版式照第 220、302 号。"""
NO = 577
SLUG = 'zhuangzi-art-of-wisdom'
TITLE = '庄子的艺术智慧'
SUBTITLE = '能用，不能常用'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Artful Wisdom of Zhuangzi: Usable, Not for Everyday Use'
EPIGRAPH = '他教的是得鱼忘荃，他靠的是编荃。两千年过去，鱼吃完了，荃还在。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-597-0'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m577'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m577-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（判词、四判据、作品读法、构想场景）；四个读数为写作过程中同一底座自查，不算独立验证；WDS博士出版令明示三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-04')


def body_han(here=None):
    """正文汉字数（前言、导论、四十六章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
