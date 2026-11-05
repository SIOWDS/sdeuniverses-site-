"""第 587 号《一个人养不出的清明》（贝芳 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 586 号改写（承自第 582 号）；版式照第 220、302 号。封面、封底不写指导者（站上口径），"在王德生老师指导下写成"见前言。"""
NO = 587
SLUG = 'clarity-no-one-grows-alone'
TITLE = '一个人养不出的清明'
SUBTITLE = '中年少女-AI 的存在性革命'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Clarity No One Grows Alone: The Existential Revolution of the Midlife Girl and Her AI'
EPIGRAPH = '清明长在你身上，却要两个人才养得出来。'
AUTHOR = '贝芳'
AUTHORS = ['贝芳']
ADVISOR = '王德生'
CATEGORY = 'health'
ISBN = '979-8-90690-613-7'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m587'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m587-unit-v1'
SRC = '/home/claude/qingming/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审定稿', tier_set_reason='三审定稿后按出版令裁定',
            tier_reason='面向大众的主张层与生活层为主（一个人养不出清明；换一个主语来活；身体从被保养的对象变成新的自己站立的根基；创造反过来养身体）；医学与健康内容只转述公认常识与权威指南的方向，不给剂量，未经临床医生审读，不构成医疗建议；书中“我”的部分场景为执笔设想、待作者核定，林姐、阿敏、晓雯为化名合成人物；写作与审校借助 AI 协作，无独立评审；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（贝芳著，王德生指导，AI 协作撰写与三审）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导读、四篇编首语、二十一章、各章小账与结语），由 conv587.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
