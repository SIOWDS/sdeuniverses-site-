"""第 557 号《工具幸福发生学——AI 时代的思考幸福升级》（王德生、胡敏 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 550 号改写；版式照第 220、302 号。"""
NO = 557
SLUG = 'tool-happiness-genesis'
TITLE = '工具幸福发生学'
SUBTITLE = 'AI 时代的思考幸福升级'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Genesis of Tool Happiness: Upgrading the Happiness of Thinking in the AI Era'
EPIGRAPH = '车来了，腿去跑步了；AI 来了，脑子去跑步了。'
AUTHOR = '王德生　胡敏'
AUTHORS = ['王德生', '胡敏']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-565-9'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102m557'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m557-unit-v1'
SRC = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（命题、判据、推翻条件、构想场景），无真跑数据；〔待核〕标注约 95 处保留；王德生出版令明示三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')


def body_han(here=None):
    """正文汉字数（前言、序、二十二章、结语与后记），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
