"""第 538 号《被照顾得很好之后》（陈晓艳 著，王德生 指导）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 526 号改写；版式照第 220、302 号。"""
NO = 538
SLUG = 'after-being-well-cared-for'
TITLE = '被照顾得很好之后'
SUBTITLE = '精准的善意怎样替生命先定了答案'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'After Being Well Cared For: How Precise Kindness Settles Life\'s Answers in Advance'
EPIGRAPH = '精准的善意抢先替生命定下“好”的样子；替得越久，生命越长不出自己的答案。'
AUTHOR = '陈晓艳'
AUTHORS = ['陈晓艳']
ADVISOR = '王德生'
CATEGORY = 'health'
ISBN = '979-8-90690-989-3'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m538'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m538-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='三审统稿时按出版令裁定',
            tier_reason='主张层为主（替定、看不见—抢先替定—长不出三步机制、生迹、残迹、临床海底、发生权代管、健康抵押、致密纠缠、溃散后自组织验、位置性存有）；每章写有证伪条件，均未经执行；书中现场为作者田野观察的匿名合成材料或说明性构造案例，无调查数据；写作与审校同一底座，无独立评审；WDS博士出版令明示上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（据陈晓艳学员专栏九篇论文与一篇实践手册，由 AI 协作重写）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导论、编序、九章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
