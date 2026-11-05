"""第 586 号《你没交给企业的那一半》（贝芳 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 582 号改写；版式照第 220、302 号。封面、封底不写指导者（站上口径），"在王德生老师指导下写成"见写在前面。"""
NO = 586
SLUG = 'the-half-you-kept'
TITLE = '你没交给企业的那一半'
SUBTITLE = '人和企业怎样共生，离开时心怀感谢，对新事业充满希望'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Half You Never Handed Over: How People and Companies Coexist, Leave with Gratitude, and Begin with Hope'
EPIGRAPH = '你交给企业的是秩序，没交出去的才是你自己的。'
AUTHOR = '贝芳'
AUTHORS = ['贝芳']
ADVISOR = '王德生'
CATEGORY = 'business'
ISBN = '979-8-90690-610-6'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m586'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m586-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审定稿', tier_set_reason='三审定稿后按出版令裁定',
            tier_reason='主张层为主（秩序归企业、混沌是原料、介生是事业、企业留一块地、离开时交接秩序）；书中涉及他人的场景都是标明的设想，没有访谈或调查；各章“对手与边界”只转述经典公认论点；写作与审校借助 AI 协作，无独立学术评审；作者本人的几处实践经历留待下一版补写；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（贝芳著，王德生指导，AI 协作撰写与三审）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（作者简介、写在前面、导论、五编编首语、十四章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
