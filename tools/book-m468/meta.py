"""第 468 号《一看就不读》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 551 号改写；版式照第 220、302 号。"""
NO = 468
SLUG = 'yi-kan-jiu-bu-du'
TITLE = '一看就不读'
SUBTITLE = 'AI时代，文字里还读得出人吗——人-AI复合主体的三条成立判据'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Not Worth Reading at a Glance: Can We Still Read a Person in Writing in the AI Era? Three Criteria for the Human-AI Composite Subject'
EPIGRAPH = '读者拒绝的从来不是 AI，是文字里读不出人。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-629-8'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261106a'
DATE = '2026-11-06'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261106-m468-unit-v1'
SRC = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（三条判据 D1·S3·E2、九格母题读法、构想场景），无真跑数据；王德生出版令明示三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-06')


def body_han(here=None):
    """正文汉字数（前言、序章、十三章、结语与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
