#!/usr/bin/env python3
"""第 597 号《AI来了，你的思考升级了吗？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 601 号改写；版式照第 220、302 号。"""
NO = 597
SLUG = 'thinking-upgrade'
TITLE = 'AI来了，你的思考升级了吗？'
SUBTITLE = '人—AI复合主体与思考文明的升级'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'AI Is Here: Has Your Thinking Upgraded?'
EPIGRAPH = '车来了，值得追问的是整个出行怎样改变，而不是双腿能否跑赢车轮。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-625-0'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261106m597'
DATE = '2026-11-06'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261106-m597-unit-v1'
SRC = 'book.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='理论论证与待检验方案，主张层为主，无真跑数据',
            tier_reason='理论解释与待实施检验方案，未经独立实证检验；主张层为主，不含真跑原始数据', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生立题与核心命题，AI 协作执笔、统稿与内部三审）', rights='作者署名出版', tier_judge='未评分',
            tier_date='2026-11-06')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
