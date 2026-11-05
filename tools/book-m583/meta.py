"""第 583 号《何谓内卷？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 577 号改写；版式照第 220、302 号。"""
NO = 583
SLUG = 'what-is-involution'
TITLE = '何谓内卷？'
SUBTITLE = '普通人都能明白的'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'What Is Involution? In Plain Words'
EPIGRAPH = '东西越交越多，看的人还是那几个。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-606-9'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m583'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m583-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（九处账、母题、虚构人物、待检验的预测）；九篇原文都是理论建构，九个数都没有检验；写作与审校同一底座，无独立评审；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（据王德生、Claude 九篇长文，由 AI 协作重写）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导论、编首语、四十五章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
