"""第 556 号《不是工业革命》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 555 号改写；版式照第 220、302 号。独著；书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/556.json）。"""
NO = 556
SLUG = 'not-an-industrial-revolution'
TITLE = '不是工业革命'
SUBTITLE = 'AI 革命改变的是「谁」在做'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Not an Industrial Revolution: The AI Revolution Changes Who Is Doing It'
EPIGRAPH = '工业革命改变人能做什么，AI 革命改变的是「谁」在做。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'ai'
ISBN = '979-8-90690-563-5'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102a'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m556-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——原理、判据、条件性论断、构想场景与可证伪清单；不含真跑数据；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='王德生著（核心命题由王德生口述）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')
AUTHORSHIP = '王德生著：全书母题与承重命题由王德生口述提出；正文由 AI（Claude）协作撰写，经三审与统稿；无独立学术评审，无实测数据。'


def body_han(here=None):
    """正文汉字数（前言、导论、五十一章与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
