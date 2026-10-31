"""第 547 号《岸上讲，田里耕》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 546、545 号改写，承自 532/529 号；版式照第 220、302 号。"""
NO = 547
SLUG = 'bank-talks-field-ploughs'
TITLE = '岸上讲，田里耕'
SUBTITLE = '你的经验，是AI时代最稀缺的东西'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'Talking on the Bank, Ploughing in the Field: Your Experience Is the Scarcest Thing in the AI Era'
EPIGRAPH = 'AI时代最值钱的，是那一块别人没踩过的、你自己的田。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-549-9'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261101a'
DATE = '2026-11-01'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261101-m547-unit-v1'
SRC = ''
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（命题、判错条件、构想案例），无真跑数据；王德生出版令明示三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-01')


def body_han(here=None):
    """正文汉字数（序章、八章与结语；口径见 convert.py），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
