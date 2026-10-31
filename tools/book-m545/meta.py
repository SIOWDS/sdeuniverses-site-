"""第 545 号《AI时代什么知识最值钱？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 536 号（tools/book-m536/）改写，承自 532/529 号；版式照第 220、302 号。"""
NO = 545
SLUG = 'which-knowledge-is-worth-most'
TITLE = 'AI时代什么知识最值钱？'
SUBTITLE = '知识经济在 E 的土壤里出生'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'Which Knowledge Is Worth Most in the AI Era? The Knowledge Economy Is Born in the Soil of E'
EPIGRAPH = '人的所有抉择，包括经济抉择，最终都是为了“加厚自己的 E”。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-546-8'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261031a'
DATE = '2026-10-31'
EDITION = '2026年10月第1版'
EDITION_SP = '2026 年 10 月第 1 版'
UNIT_REV = '20261031-m545-unit-v1.0'
SRC = '/home/claude/books/E知识-什么知识最值钱/chapters'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（命题、判错条件、构想案例），无真跑数据', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-10-31')


def body_han(here=None):
    """正文汉字数（序言、导读、二十章与结语；口径见 convert.py），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
