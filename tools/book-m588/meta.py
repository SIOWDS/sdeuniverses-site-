"""第 588 号《孩子没交给学校的那一半》（贝芳 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 586 号改写；版式照第 220、302 号。封面、封底不写指导者（站上口径），"在王德生老师指导下写成"见前言。"""
NO = 588
SLUG = 'the-half-at-home'
TITLE = '孩子没交给学校的那一半'
SUBTITLE = '学校接走秩序，AI加速秩序，家里要为孩子留出混沌与介生'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Half That Never Went to School: Order Goes to School, AI Speeds It Up, and Home Keeps Room for Chaos and Becoming'
EPIGRAPH = 'AI时代，家长—AI与孩子—AI两股洪流都极会把混沌变成秩序；家庭教育的要害，是在两股之间，为孩子留出混沌与介生的地方。'
AUTHOR = '贝芳'
AUTHORS = ['贝芳']
ADVISOR = '王德生'
CATEGORY = 'edu'
ISBN = '979-8-90690-615-1'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m588'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m588-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审稿 v0.3', tier_set_reason='三审稿、作者自述回溯后按出版令裁定',
            tier_reason='主张层为主（学校接走秩序、AI加速秩序、家里留混沌与介生、同源回声是负向发生）；女儿化名小满，只有作者本人文字里的几件事当作纪实，其余场景都标为示例性情境；四周家庭记录只有设计，没有实测；站外经典只转述公认论点并括注；写作与审校借助 AI 协作，无独立学术评审；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（贝芳著，王德生指导，AI 协作撰写与三审）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导论、七编编首语、十八章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
