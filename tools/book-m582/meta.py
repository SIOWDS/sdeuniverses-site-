"""第 582 号《以谁为准》（胡敏 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 578 号改写；版式照第 220、302 号。"""
NO = 582
SLUG = 'who-sets-the-standard'
TITLE = '以谁为准'
SUBTITLE = '为什么砍不掉的中间商总会长回来'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'By Whose Measure? Why the Middleman You Cut Out Keeps Growing Back'
EPIGRAPH = '砍掉的是人，没换的是准。'
AUTHOR = '胡敏'
AUTHORS = ['胡敏']
ADVISOR = '王德生'
CATEGORY = 'business'
ISBN = '979-8-90690-605-2'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m582'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m582-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（以它为准、准的五张脸、砍人不换准、越便宜越硬）；九篇原论文的检验都在公开软件仓库上做，场地是代理；第十三章的商业场地清点已预注册、尚未执行；写作与审校同一底座，无独立评审；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（据胡敏中介频道九篇论文，由 AI 协作重写）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（写在前面、序章、编首语、十三章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
