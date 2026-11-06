#!/usr/bin/env python3
"""第 598 号《持续创造何以可能——知识 原创 价值与成长的主客互动发生学》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 594 号改写；版式照第 220、302 号。"""
NO = 598
SLUG = 'continuous-creation'
TITLE = '持续创造何以可能'
SUBTITLE = '知识 原创 价值与成长的主客互动发生学'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'How Is Continuous Creation Possible?'
EPIGRAPH = '成果，怎样成为下一轮的条件。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-626-7'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261106m598'
DATE = '2026-11-06'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261106-m598-unit-v1'
SRC = 'book.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='理论专著，主张层为主，无真跑数据',
            tier_reason='理论解释与待实施检验方案，未经独立实证检验；主张层为主，不含真跑原始数据', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生十五篇论文为基础，AI 协作统稿）', rights='作者署名出版', tier_judge='未评分',
            tier_date='2026-11-06')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
