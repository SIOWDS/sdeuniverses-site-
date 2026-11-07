"""第 609 号《抉择需要等待——让半成判断自己去长》（王德生 著）排版常量。工具链承自第 608、569 号。
书号、ISBN、定价只在这里改。上站前须重新拉站上 catalog 复核 609 / 979-8-90690-690-8 未被占用（预留档 .publish/volume-reservations/609.json）。"""
NO = 609
SLUG = 'decisions-need-waiting'
TITLE = '抉择需要等待'
TITLE_SHORT = '抉择需要等待'
SUBTITLE = '让半成判断自己去长'
COVER_SMALL = '半成判断 · 三问 · 把它攥在手里'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Decisions Need Waiting: Letting the Half-Formed Judgment Grow on Its Own'
EPIGRAPH = ''
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
ISBN = '979-8-90690-690-8'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m609r1'
DATE = '2026-11-07'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
CATEGORY = 'core'
UNIT_REV = '20261107-m609-unit-v1'
TIER = dict(tier='L0', tier_set_at='统稿', tier_reason='Q3 第一刀：公开命题（半成判断不是犹豫、不是糊涂；此刻该不该等，用回得了头吗／谁在替我扛／读数赶得上吗三问来问；三个格子至今没有发生）为主，条件层不构成私密底本；不含诊断标准、治疗建议、数值阈值，不含法律或财务建议；沿用站内自著专著完整开放上站的做法，依王德生上站令',
            cite_ok='true', context_layers='判据、结论',
            source='王德生立题并口述母题；Claude 协作执笔（二十位写手）、统稿与三审', rights='作者署名出版', tier_judge='Claude（依王德生上站令）',
            tier_date='2026-11-07')
AUTHORSHIP = '王德生著：王德生立题并口述母题与口径，正文由 AI（Claude）协作撰写，经统稿与三审；未经独立学术评审，未经医学、教育、法律等专业人士审定。'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
