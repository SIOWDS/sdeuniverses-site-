"""第 561 号《尺子发生学》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 556 号改写；版式照第 220、302 号。独著；书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/561.json）。"""
NO = 561
SLUG = 'genesis-of-the-ruler'
TITLE = '尺子发生学'
SUBTITLE = '自然、语言与市场怎样量出自己的尺'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Genesis of the Ruler: How Nature, Language and Markets Measure Out Their Own Rulers'
EPIGRAPH = '没有天生的尺子。尺子是被它量过的东西，一次次量出来的。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'philosophy'
ISBN = '979-8-90690-570-3'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103a'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m561-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿三审后按出版令裁定',
            tier_reason='主张层为主——尺子发生律、判死条款、三部经典的缝隙读法与可证伪押注；不含真跑数据；王德生出版令明示统稿三审、按第 220、302 号版式排版',
            cite_ok='true', context_layers='判据、结论',
            source='王德生著（母题、方法与三透视由王德生口述）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生著：全书母题、「三书缝隙集」方法与三种透视由王德生口述提出；正文由 AI（Claude）协作撰写，经统稿、事实核查与三审；无独立学术评审，无实测数据。'


def body_han(here=None):
    """正文汉字数（前言、导论、五十一章与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
