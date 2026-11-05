"""第 590 号《每一环都替对了》（胡敏 著，王德生 指导）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 526 号改写；版式照第 220、302 号。本书只做阅读出版（印刷版、阅读版、全文网页、翻页器），不含学习包与智能体。"""
NO = 590
SLUG = 'every-link-done-right'
TITLE = '每一环都替对了'
SUBTITLE = '身体自我照看回路的闲置与归还'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Every Link Done Right: The Idling and Return of the Body’s Self-Care Loop'
EPIGRAPH = '感知、判断、重组三环，各自被正确地代劳了；身体那条只在被走时才存在的回路，便悄然拆除。'
AUTHOR = '胡敏'
AUTHORS = ['胡敏']
ADVISOR = '王德生'
CATEGORY = 'health'
ISBN = '979-8-90690-617-5'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m590'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m590-read-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审统稿后按出版令裁定',
            tier_reason='主张层为主（三环回路、被代劳—萎缩—被锁定、整程归还）；各章与第十章写有可观察的证伪条件，均未经执行；案例一律为临床原型重构；神经与分子机制多为假说；写作与审校同一底座，无独立评审；涉及减药、撤监测处一律限定为医生主导下的研究与设计原则',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（据胡敏学员专栏九篇论文熔铸，由 AI 协作重写）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导论、编序、十章与结论），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
