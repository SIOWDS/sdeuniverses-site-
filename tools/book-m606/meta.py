"""第 606 号《AI时代新教育的三大典范》（王德生 著）排版常量。工具链承自第 605 号。
书号、ISBN、定价只在这里改。上站前须重新拉站上 catalog 复核 606 / 979-8-90690-638-0 未被占用。"""
NO = 606
SLUG = 'three-paradigms-new-education'
TITLE = 'AI时代新教育的三大典范'
TITLE_SHORT = 'AI时代新教育的三大典范'
SUBTITLE = '统一性知识成了水电之后，教什么、怎么教、为什么学'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Three Paradigms of New Education in the AI Era: What to Teach, How to Teach, Why to Learn'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
ISBN = '979-8-90690-638-0'
PRICE_USD = 45.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m606r1'
DATE = '2026-11-07'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
CATEGORY = 'core'
UNIT_REV = '20261107-m606-unit-v1'
TIER = dict(tier='L0', tier_set_at='统稿', tier_reason='Q3 第一刀：公开命题（统一性知识成水电、教学目标转向同一性谱系知识、课例方法）为主，条件层不构成私密底本；沿用作者对自著专著先完整开放上站的做法，待作者确认',
            cite_ok='true', context_layers='判据、结论',
            source='王德生立题、口述三大典范与裁定；Claude 协作执笔与统稿（并行写手与十位统稿核对者）', rights='作者署名出版', tier_judge='Claude（依王德生上站令）',
            tier_date='2026-11-07')
AUTHORSHIP = '王德生立题并口述三大典范，正文由 AI（Claude）协作撰写，经统稿核对；无独立学术评审。'
