"""第 537 号《AI接管秩序之后》（阳涌 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 582 号改写；版式照第 220、302 号。"""
NO = 537
SLUG = 'after-ai-takes-over-order'
TITLE = 'AI接管秩序之后'
SUBTITLE = '教育、创造与主体能力的发生学'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'After AI Takes Over Order: The Genesis of Education, Creation and Agency'
EPIGRAPH = '学校只为秩序立了账，未定与承接从无份额；AI接管了秩序，连夹带在笨拙劳动里的那一点未定与承接，也一并端走。'
AUTHOR = '阳涌'
AUTHORS = ['阳涌']
ADVISOR = '王德生'
CATEGORY = 'education'
ISBN = '979-8-90690-988-6'
PRICE_USD = 28.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m537'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m537-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（立账论、无份论、接管论、夹带）；十五篇原论文改写，案例为构造的说明性案例或化名合成个案，无调查数据；写作与审校同一底座，无独立评审；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（据阳涌学员专栏十五篇论文，由 AI 协作重写）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数，由 conv537.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
