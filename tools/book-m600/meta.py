"""第 600 号《AI大模型巴别塔的倒塌》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 552 号工具链复制改写；版式照第 220、302 号。"""
NO = 600
SLUG = 'babel-tower-collapse'
TITLE = 'AI大模型巴别塔的倒塌'
SUBTITLE = '统一性的最大赢家，成了同一性谱系的接生婆'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = ('The Collapse of the AI Babel Tower: '
            'The Biggest Winner of Unity Became the Midwife of Identity Genealogy')
EPIGRAPH = '塔建成之日，就是塔倒之时。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'   # 同系列：545、551 等为 core，543 为 culture
ISBN = '979-8-90690-630-4'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261106b'
DATE = '2026-11-06'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261106-m600-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——命题、判据、三塔三尺、暂定九格读法；陪读场景为构想；无真跑数据；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-06')
AUTHORSHIP = '核心问题、SDE 框架与全书母题由王德生提出；正文由 AI（Claude）协作撰写，经分章质检与统稿；无独立学术评审，无用户试验。'


def body_han(here=None):
    """正文汉字数（前言、导读、序章、十六章、结语与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
