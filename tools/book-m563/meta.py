"""第 563 号《开端发生学》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 561 号改写；版式照第 220、302 号。独著；书号与 ISBN 从站里计算。"""
NO = 563
SLUG = 'genesis-of-beginnings'
TITLE = '开端发生学'
SUBTITLE = '几何、礼与王朝的起点是怎样结晶出来的'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Genesis of Beginnings: How the Starting Points of Geometry, Ritual and Dynasty Crystallize'
EPIGRAPH = '每一个开头，都是前面很多次的结尾；只是那些结尾，被忘了。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-580-2'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103m563'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m563-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿三审后按出版令裁定',
            tier_reason='主张层为主——开端发生律、四条判死条款、三部名著的缝隙读法与可证伪押注；不含真跑数据',
            cite_ok='true', context_layers='判据、结论',
            source='王德生著（母题、口径与承重命题由王德生给出并审定）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生著：全书母题、口径与承重命题由王德生给出并审定；正文由 AI（Claude）协作撰写，经统稿、联网事实核查与三审；无独立学术评审。'


def body_han(here=None):
    """正文汉字数（前言、导论、三十四章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
